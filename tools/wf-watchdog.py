#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/wf-watchdog.py — Workflow 看門狗（CLAUDE.md §2、rev4:L-104/rev4:L-112；B-005 轉 python＝ADR 0010）

用法：Monitor 工具 command 欄填 `python3 tools/wf-watchdog.py <冒煙token> [wf目錄|runId]`
  ★必與 Workflow launch 同一回合原子成對發射（兩 call 間零其他動作）。
  無第二參數＝自動發現本專案最新 wf_* transcript 目錄（毋需 launch 回傳值→可同回合並發；
    沿舊 bash 版語意先 sleep 10 讓 launch 建目錄）。
  第二參數＝硬編監看目標（B-005：「最新目錄」自動發現三次實彈鎖錯 run）：
    - wf transcript 目錄路徑（含路徑分隔符即視為路徑）；或
    - 裸 runId（wf_ 開頭、於本專案 slug 的 projects 目錄下解析、跨 session 搜尋）。
    目標模式＝輪詢等待目標目錄出現（5s 間隔、上限 180s）後才 ARMED、不做自動發現——
    「目錄延遲建立、sleep 10 撲空鎖到舊目錄」的坑（2026-08-08 實證）由等待迴圈補上。
  ★resume 場景（resumeFromRunId）：resume 不會建新目錄、沿用原 runId／目錄（2026-08-08
    實證）——第二參數直接給原 runId（或原目錄路徑）即為正解。
    ★續跑時 ARMED 行的冒煙位元組數＝前一輪殘留、不可據以判斷新 prompt 送達；查核改看
    最新 agent-*.jsonl（mtime 是否剛剛＋grep 本輪新字串）、一次性查核不輪詢（L-023）。
  ★冒煙 token 不可取字面 test（會被當自測子命令）。

行為：ARMED 一行（夾帶冒煙：最早 agent transcript＝implementer 首行 byte 數＋冒煙 token
  命中數）→ 靜默迴圈（60s），stall／判準失效告警時輸出並退出；runaway 告警一次後
  ★不退出、續行監看（B-069：run 還活著時退出＝看門狗自我卸除、stall 覆蓋歸零）。
完成通知一到請 TaskStop 本 Monitor（否則正常完成 ~13min 後誤觸 stall）。
自測：python3 tools/wf-watchdog.py test（離線、合成 fixtures、stdlib-only）。

退出碼：0＝正常監看結束（含告警輸出後退出——告警屬正常職責、非故障）；1＝發射失敗
  （自動發現無 wf 目錄／目標逾時未出現）；2＝第二參數無法解析；test＝全綠 0／有紅 1。

★輸出紀律（BACKLOG B-005 陷阱明載）：python 於 pipe 後端預設塊緩衝——ARMED 行是唯一
  冒煙訊號，不即時 flush＝外觀同「發射失敗」。本檔一切輸出走 _say()（print flush=True）、
  自測以檔文釘住「每個 print 都帶 flush=True」。
★存目一句：舊 bash 版的 GNU/BSD find 雙分支（rev4:L-139）與 export LC_ALL=C 補丁
  （rev4:L-142 中文字串 locale 炸點）在 python 下自然消滅——mtime 一律 os.stat。
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import time
import unittest
import unittest.mock
from glob import glob

STALL = 780      # 秒；>最長合法 cargo（sub-agent Bash 單命令 600s 上限＋margin）
RUNAWAY_FLOOR = 25   # 不重複 agent key 數保底（B-069：原 RUNAWAY 字面值、行為不退步）
FUSE_MULTIPLIER = 2  # 有效上限＝max(RUNAWAY_FLOOR, FUSE_MULTIPLIER × script 宣告之 AGENT_FUSE)
#   ★上限自「被監看 script 的 launch 快照」推導、絕不由呼叫端傳入（B-069；CLAUDE.md §9
#   安全邊界不得與呼叫端同源——--fuse／--fanout 兩案依此否決）。取不到快照／無宣告＝
#   顯式退 RUNAWAY_FLOOR，絕不寫成「取不到就不檢查」（＝卸除 backstop）。
#   ★射程限縮（2026-08-11 實測）：持久 json 於 run **結束後**才落地 ⇒ 進行中的 run 恆用
#   floor；推導升級真正生效的形有二：「鎖到已完成的 run」（B-069 原始誤報現場即此形）與
#   「armed-live：run 結束後 json 落地、越界在落地後才被觀測到」——後者＝懶讀重試腿的
#   存在理由。★resume 形不在本 backstop 覆蓋內（fix 第 3 輪誠實限縮）：resume 沿用原
#   runId，讀到的持久 json 直到 resumed run 結束前都是**前一輪**的 script 快照——resume
#   前若動過 AGENT_FUSE（§2「修 script→resume」即典型動機），推得上限即為舊值：調高＝
#   偏窄假警報（噪音、非終止）、調低＝偏寬＝backstop 靜默放寬（CLAUDE.md §9 cap 失格形）。
#   行為面無便宜修法：以「json mtime ≥ watch 啟動時刻」區辨新舊快照，會把「鎖到已完成
#   run」形一併打回 floor＝B-069 原始誤報復活；真修需框架端提供 run 級 script 識別
#   （提案射程外、循 BACKLOG 另立）。ARMED 行印的是當下實際生效值。
#   ★判準＝數 journal 不重複 agent key、★不數行數（rev5 差分，承 rev4:L-144 同族實證）：
#   行數型 backstop 在 kill/resume 疊代下累積誤報——同一支 agent 每輪 launch 都留新事件列，
#   journal 行數線性成長而實際併發 agent 數不變（實證：三輪 launch 使 journal 達 26 行觸發
#   RUNAWAY 誤報，實際不重複 key＝10≤11 理論上限、保險絲完好）。key 去重後才等價於「派了幾支」。
LOOP_SLEEP = 60            # 秒；靜默迴圈間隔
DISCOVER_SLEEP = 10        # 秒；自動發現模式先讓 launch 建目錄（沿舊 bash 版語意）
TARGET_POLL_INTERVAL = 5   # 秒；目標模式輪詢間隔
TARGET_POLL_TIMEOUT = 180  # 秒；目標模式等待目標目錄出現的上限
# ★script 快照內的保險絲「宣告形」＝錨定 const/let/var 關鍵字（B-069 fix 第 2 輪）：
#   裸 `AGENT_FUSE\s*=\s*\d+` 匹配「任何提及」——註解先行（「前一輪 AGENT_FUSE = 20」）
#   會把上限竄窄、前綴變體（MAX_AGENT_FUSE = 999）會把上限竄寬＝backstop 靜默卸除
#   （真實快照已出現一次近失手：宣告行前一行註解恰含歷史值敘述）。
#   ★錨定擋不住兩形（確認輪實暴）：被註解掉的真宣告（`// const AGENT_FUSE = 999`）與
#   模板字串內字面——皆帶 const 關鍵字；取值端故用 findall 取 **min**（search 取首個
#   會使前者推得 1998＝cap 靜默放寬 50 倍）。取不到＝顯式退 RUNAWAY_FLOOR。
#   min＋floor 合起來，「上限只會偏窄、不會偏寬」的方向安全才成立。
FUSE_RE = re.compile(r"\b(?:const|let|var)\s+AGENT_FUSE\s*=\s*(\d+)")


def _say(msg):
    """單一輸出咽喉：每行皆即時 flush（pipe 塊緩衝下 ARMED 不現身＝外觀同發射失敗）。"""
    print(msg, flush=True)


def slugify(path):
    """canonical path → Claude Code projects 目錄 slug（/ 與 _ 全轉 -）。

    呼叫端須先 os.path.realpath：★realpath 解析綁定路徑——primary working dir 可能是
    /home/… 綁定（pwd 給非 canonical、slug 對不上 -mnt-d-… projects 目錄名→找不到 wf；
    rev4:B-070、rev4:006 orchestration 實測）。
    """
    return path.replace("/", "-").replace("_", "-")


def _newest_by_mtime(paths):
    """mtime 最新的一個路徑；空集合／全數消失→None。"""
    best, best_m = None, None
    for p in paths:
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if best_m is None or m > best_m:
            best, best_m = p, m
    return best


def discover_latest_wf(proj_dir):
    """自動發現：最新 session 的 workflows 目錄下最新 wf_*（ls -dt|head -1 等價）；無→None。"""
    root = _newest_by_mtime(glob(os.path.join(proj_dir, "*", "subagents", "workflows")))
    if root is None:
        return None
    return _newest_by_mtime(glob(os.path.join(root, "wf_*")))


def resolve_target(arg):
    """第二參數形制判定：含路徑分隔符＝("dir", arg)；wf_ 起頭＝("runid", arg)；
    其餘無法解析＝(None, arg)。"""
    if "/" in arg or os.sep in arg:
        return ("dir", arg)
    if arg.startswith("wf_"):
        return ("runid", arg)
    return (None, arg)


def find_runid_dir(proj_dir, runid):
    """裸 runId 於 slug projects 目錄下解析：跨 session 搜 subagents/workflows/<runId>；
    多命中取 mtime 最新；無→None。"""
    hits = [p for p in glob(os.path.join(proj_dir, "*", "subagents", "workflows", runid))
            if os.path.isdir(p)]
    return _newest_by_mtime(hits)


def wait_for_target(probe, timeout=TARGET_POLL_TIMEOUT, interval=TARGET_POLL_INTERVAL,
                    _sleep=time.sleep, _clock=time.monotonic):
    """輪詢等待目標出現（B-005 教訓：wf 目錄延遲建立、只 sleep 固定秒數會撲空）。

    probe()→命中路徑或 None；至少探測一次；逾時→None。
    """
    deadline = _clock() + timeout
    while True:
        hit = probe()
        if hit is not None:
            return hit
        if _clock() >= deadline:
            return None
        _sleep(interval)


def oldest_agent_transcript(wf_dir):
    """最早的 agent transcript（＝implementer；ls -t|tail -1 等價）；無→None。"""
    files = [p for p in glob(os.path.join(wf_dir, "agent-*.jsonl"))]
    oldest, oldest_m = None, None
    for p in files:
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if oldest_m is None or m < oldest_m:
            oldest, oldest_m = p, m
    return oldest


def first_line_smoke(first_line, token):
    """冒煙字串（純函式）：first_line＝transcript 首行 bytes（含換行、head -1|wc -c 等價）；
    token 命中＝0/1（grep -c 等價、數命中行非命中次）；token 空＝「-」。"""
    nbytes = len(first_line)
    if token:
        hit = 1 if token in first_line.decode("utf-8", "replace") else 0
    else:
        hit = "-"
    return f"impl首行{nbytes}bytes／token({token or '無'})命中={hit}"


def smoke_text(wf_dir, token):
    """ARMED 行冒煙段：讀最早 transcript 首行；零 transcript＝疑零派發。"""
    path = oldest_agent_transcript(wf_dir)
    if path is None:
        return "尚無 agent transcript（疑零派發 throw 或未啟動）"
    try:
        with open(path, "rb") as fh:
            first = fh.readline()
    except OSError:
        first = b""
    return first_line_smoke(first, token)


def journal_key_stats(text):
    """journal 全文 →（raw 行數, 不重複 top-level "key" 數）（純函式）。

    ★頂層鍵定錨（L-002）：逐行 JSON 解析、只取事件物件 top-level 的 "key"——扁平 grep
    會把 result payload 巢狀同名鍵（如 coverage[].key＝"FR-001"）一併計入，實證 9 支
    真 agent 被數成 31 → RUNAWAY 誤報。壞行跳過（擋壞行非本工具職責）。
    ★另設判準健全性檢查（消費端）：journal 非空卻抽不到任何 key＝抽取與實際格式脫節，
    此時保險絲恆 0＝永不觸發＝靜默失效，故 fail-loud。
    """
    keys = set()
    # 行數＝wc -l 等價（僅計完整換行行）：尾端無換行殘行＝寫入中途、不計不解析——
    # 否則首筆寫入中途恰逢巡檢會偽觸發「判準失效」（2026-08-08 復核、對齊舊 bash 版語意）。
    raw = text.count("\n")
    for line in (text.split("\n")[:raw] if raw else []):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if isinstance(e, dict):
            k = e.get("key")
            if isinstance(k, str):
                keys.add(k)
    return raw, len(keys)


def read_journal(wf_dir):
    """journal.jsonl 全文；缺檔／不可讀→空字串（兩判準同時歸零、與舊版行為等價）。"""
    try:
        with open(os.path.join(wf_dir, "journal.jsonl"), encoding="utf-8",
                  errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def wf_persist_json_path(wf_dir):
    """wf transcript 目錄 → 同 run 持久檔路徑（B-069；2026-08-11 實地驗證之佈局）：
    <session>/subagents/workflows/wf_<runId>/ → <session>/workflows/wf_<runId>.json
    （自 wf 目錄向上三層再進 workflows/、同名 .json）。"""
    d = wf_dir.rstrip("/")
    session = os.path.dirname(os.path.dirname(os.path.dirname(d)))
    return os.path.join(session, "workflows", os.path.basename(d) + ".json")


def derive_runaway_ceiling(wf_dir):
    """RUNAWAY 有效上限自被監看產物推導（B-069）→ (ceiling, final)。

    來源＝持久檔 "script" 欄＝launch 當下實際執行的 script 快照；★絕不改讀 json 之
    scriptPath 指向的 scratchpad 現檔——現檔可被事後覆寫、快照才是實際執行的內容
    （安全邊界的來源紀律）。
    ★懶讀契約與射程限縮（2026-08-11 實測：持久 json 於 run 進行中不存在、run 結束後
    才落地）：final=True＝定案、呼叫端可快取不再讀；final=False＝json 尚不存在／尚不可
    解析（含寫入中途壞檔），本輪先用 floor、★不快取——下輪重試。⇒ 進行中的 run 恆退
    floor；推導升級真正生效的形有二：「鎖到已完成的 run」與「armed-live：run 結束後
    json 落地、越界在落地後才被觀測到」——後者正是重試腿（final=False 不快取）的存在
    理由，run 進行中仍由 floor 把關。★resume 形不覆蓋：resume 沿用原 runId，本函式讀
    到的必是**前一輪**的 script 快照——resume 前若動過 AGENT_FUSE，推得上限即舊值
    （調高＝偏窄假警報、調低＝偏寬＝backstop 弱化）；成因與「無便宜修法」論證詳常數區註解。
    ★「取不到 json／無 script 欄／無 AGENT_FUSE 宣告／讀檔或解析失敗」一律顯式退
    RUNAWAY_FLOOR——絕不「取不到就不檢查」（＝卸除 backstop）；例外不外洩 crash。
    """
    try:
        with open(wf_persist_json_path(wf_dir), encoding="utf-8",
                  errors="replace") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return (RUNAWAY_FLOOR, False)   # 尚不存在／壞檔（寫入中途）：floor、下輪再試
    script = data.get("script") if isinstance(data, dict) else None
    if not isinstance(script, str):
        return (RUNAWAY_FLOOR, True)    # 快照在但無 script 欄＝定案 floor
    vals = [int(x) for x in FUSE_RE.findall(script)]
    if not vals:
        return (RUNAWAY_FLOOR, True)    # 無 AGENT_FUSE 宣告＝定案 floor
    # ★多重匹配＝無從分辨哪個宣告實際生效（被註解掉的舊宣告／模板字串內字面皆帶 const、
    #   錨定擋不住）——取 min＝最保守值：偏窄＝假警報（噪音、且已非終止型），偏寬＝
    #   backstop 靜默卸除，兩者代價不對稱。JS 同 scope const 不可重複宣告，正常單一
    #   宣告 script 完全不受影響（確認輪實暴：search 取首個使被註解掉的 999 推得 1998）。
    return (max(RUNAWAY_FLOOR, FUSE_MULTIPLIER * min(vals)), True)


def newest_mtime_under(root):
    """目錄樹最新檔案 mtime（os.stat 一支打天下）；無檔案／目錄消失→None。"""
    newest = None
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            try:
                m = os.stat(os.path.join(dirpath, name)).st_mtime
            except OSError:
                continue
            if newest is None or m > newest:
                newest = m
    return newest


def watch_loop(wf_dir, _sleep=time.sleep, _now=time.time, _newest=newest_mtime_under,
               _max_rounds=None):
    """靜默迴圈：60s 一輪；判準失效／STALL 告警即輸出並退出；RUNAWAY 只告警一次且
    ★不退出（B-069：run 還活著時 return＝看門狗自我卸除、stall 覆蓋歸零）。
    _max_rounds＝測試注入的輪數上限——判準被改壞時測試收「零輸出」紅燈、而非 busy loop
    掛死 pre-commit／bootstrap（兩處裸跑自測無 timeout；2026-08-08 復核）；生產恆 None。"""
    base = os.path.basename(wf_dir.rstrip("/"))
    rounds = 0
    ceiling = None        # None＝上限尚未定案 → 每輪懶讀（持久 json 於 run 結束後才落地）
    # ★runaway_said＝一個 watch 生命週期只叫一次（否則每 60s 洗版一則）、且上限升級後
    # 亦不重新武裝——刻意取捨（提案 §5 只釘「只叫一次」；重新武裝＝規格外行為變更）。
    # 代價（明認）：floor 告警後 ceiling 升級且 nkeys 破新上限（更強的失效訊號）不再出
    # 聲，唯一一則印的是首次越界當下的 nkeys。可接受之因：升級時點必在 run 結束後，其
    # 後 key 續增僅發生於 resume，而 resume＝新 launch 必原子成對掛新 Monitor
    # （CLAUDE.md §2）＝新 watch 生命週期重新武裝可再叫；舊 watch 的後續覆蓋交給
    # stall 偵測與完成通知接手。
    runaway_said = False
    while _max_rounds is None or rounds < _max_rounds:
        rounds += 1
        _sleep(LOOP_SLEEP)
        now = _now()
        newest = _newest(wf_dir)
        if newest is None:
            _say(f"看門狗 目錄不可讀：{base}——疑被清或發射失敗")
            return 0
        idle = int(now) - int(newest)
        raw, nkeys = journal_key_stats(read_journal(wf_dir))
        if raw > 0 and nkeys == 0:
            _say(f"看門狗 判準失效：journal {raw}行 但抽不到任何 agent key——"
                 "RUNAWAY 保險絲已恆 0、形同卸除→立即人工查 journal 格式")
            return 0
        if ceiling is None:
            derived, final = derive_runaway_ceiling(wf_dir)
            if final:
                ceiling = derived
        else:
            derived = ceiling
        if nkeys > derived and not runaway_said:
            runaway_said = True
            _say(f"看門狗 RUNAWAY：不重複 agent key {nkeys} > {derived}"
                 "——★先判形態：扇出型 workflow（review／多維度／pipeline 扇出）正當總量"
                 "本就可能超過門檻，屬預期、不要 TaskStop；編排型（單元 implementer＋"
                 "review 迴圈）超過才是防呆③保險絲疑失效→/workflows 查→TaskStop wf。"
                 "看門狗續行監看。")
            # ★不 return（B-069）：stall 偵測繼續有效直到 run 真的結束
        if idle > STALL:
            _say(f"看門狗 STALL：{idle}s 無寫入 > {STALL}s（疑卡死/死迴圈）→ "
                 "/workflows 查→TaskStop→修 script→resumeFromRunId 續跑")
            return 0
    return 0


def main(argv):
    args = argv[1:]
    cmd = args[0] if args else ""
    if cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    token = args[0] if args else ""
    target = args[1] if len(args) > 1 else ""
    slug = slugify(os.path.realpath(os.getcwd()))
    proj_dir = os.path.join(os.path.expanduser("~"), ".claude", "projects", slug)
    if target:
        kind, val = resolve_target(target)
        if kind == "dir":
            def probe():
                return val if os.path.isdir(val) else None
        elif kind == "runid":
            def probe():
                return find_runid_dir(proj_dir, val)
        else:
            _say(f"看門狗 參數無法解析：{val}——第二參數須為 wf 目錄路徑或 wf_ 開頭"
                 "的 runId（見檔頭用法）")
            return 2
        wf_dir = wait_for_target(probe)
        if wf_dir is None:
            _say(f"看門狗 發射失敗？目標 {val} 等 {TARGET_POLL_TIMEOUT}s 未出現"
                 f"（slug={slug}）——確認 runId／路徑正確且 Workflow 已 launch")
            return 1
    else:
        time.sleep(DISCOVER_SLEEP)   # 沿舊 bash 版語意：讓 launch 先把 wf 目錄建出來
        wf_dir = discover_latest_wf(proj_dir)
        if wf_dir is None:
            _say(f"看門狗 發射失敗？找不到 wf transcript 目錄（slug={slug}）"
                 "——確認 Workflow 已 launch")
            return 1
    # ★ARMED 印當下實際生效門檻（B-069 射程限縮揭露）：持久 json 於 run 結束後才落地，
    # live run 此刻必然取不到快照＝floor 生效；印公式會謊報一個當下不成立的門檻。
    derived, final = derive_runaway_ceiling(wf_dir)
    if final:
        runaway_txt = f"runaway>{derived}key（自 script 快照定案）"
    else:
        runaway_txt = (f"runaway>{RUNAWAY_FLOOR}key（快照未落地之保底；json 於 run 結束後"
                       f"才落地→進行中恆此值、落地後次輪懶讀升 "
                       f"max({RUNAWAY_FLOOR},{FUSE_MULTIPLIER}×AGENT_FUSE)）")
    _say(f"看門狗 ARMED → {os.path.basename(wf_dir.rstrip('/'))}｜冒煙: "
         f"{smoke_text(wf_dir, token)}（stall>{STALL}s／{runaway_txt}；"
         "完成通知到請 TaskStop 本 Monitor）")
    return watch_loop(wf_dir)


# ---------------------------------------------------------------------------
# 自測（離線、合成 fixtures；一律隔離暫存目錄、絕不讀寫真 projects 目錄）
# ---------------------------------------------------------------------------


class TestConstantsPinned(unittest.TestCase):
    """★常數字面釘死（防靜默漂移）：閾值＝CLAUDE.md §2 契約字面的一部分。"""

    def test_thresholds_match_the_contract(self):
        self.assertEqual(STALL, 780)
        self.assertEqual(RUNAWAY_FLOOR, 25)
        self.assertEqual(FUSE_MULTIPLIER, 2)
        self.assertEqual(LOOP_SLEEP, 60)
        self.assertEqual(DISCOVER_SLEEP, 10)
        self.assertEqual(TARGET_POLL_INTERVAL, 5)
        self.assertEqual(TARGET_POLL_TIMEOUT, 180)


class TestSlug(unittest.TestCase):
    def test_slash_and_underscore_both_become_dash(self):
        """rev4:B-070：/ 與 _ 全轉 -（漏 _ 即 slug 對不上 projects 目錄名）。"""
        self.assertEqual(slugify("/mnt/d/A_Spaces/x_Proj"), "-mnt-d-A-Spaces-x-Proj")


class TestJournalKeyStats(unittest.TestCase):
    def test_dedup_counts_distinct_top_level_keys(self):
        """同一 agent 多輪事件列去重——kill/resume 疊代下行數成長、key 數不動（rev4:L-144）。"""
        text = ('{"key": "impl-1"}\n{"key": "impl-1"}\n{"key": "review-1"}\n')
        self.assertEqual(journal_key_stats(text), (3, 2))

    def test_nested_same_name_keys_are_not_counted(self):
        """★L-002：result payload 巢狀同名鍵不得計入（扁平 grep 把 9 支數成 31 誤報）。"""
        text = ('{"key": "impl-1", "result": {"coverage": '
                '[{"key": "FR-001"}, {"key": "FR-002"}]}}\n')
        self.assertEqual(journal_key_stats(text), (1, 1))

    def test_bad_lines_and_non_dict_lines_are_skipped_but_counted_raw(self):
        text = 'not-json\n[1, 2]\n"scalar"\n{"key": "impl-1"}\n'
        self.assertEqual(journal_key_stats(text), (4, 1))

    def test_keyless_journal_yields_zero_keys_for_fail_loud(self):
        """健全性 fail-loud 的資料面：非空 journal 抽不到 key＝(raw>0, 0)。"""
        raw, nkeys = journal_key_stats('{"event": "x"}\n{"event": "y"}\n')
        self.assertEqual((raw > 0, nkeys), (True, 0))

    def test_empty_or_missing_journal_is_all_zero(self):
        self.assertEqual(journal_key_stats(""), (0, 0))
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_journal(d), "")   # 缺檔→空字串、兩判準同時歸零


class TestSmoke(unittest.TestCase):
    def test_token_hit_and_byte_count(self):
        """token 命中計數：首行含 token＝1、不含＝0；byte 數含換行（head -1|wc -c 等價）。"""
        line = "hello TOKEN123 world\n".encode()
        self.assertEqual(first_line_smoke(line, "TOKEN123"),
                         f"impl首行{len(line)}bytes／token(TOKEN123)命中=1")
        self.assertEqual(first_line_smoke(line, "absent-tok"),
                         f"impl首行{len(line)}bytes／token(absent-tok)命中=0")

    def test_empty_token_renders_dash(self):
        self.assertEqual(first_line_smoke(b"x\n", ""), "impl首行2bytes／token(無)命中=-")

    def test_smoke_text_reads_oldest_transcript_first_line_only(self):
        with tempfile.TemporaryDirectory() as d:
            new = os.path.join(d, "agent-b.jsonl")
            old = os.path.join(d, "agent-a.jsonl")
            with open(new, "w", encoding="utf-8") as fh:
                fh.write("newer TOK\nrest\n")
            with open(old, "w", encoding="utf-8") as fh:
                fh.write("older TOK line\nTOK again\n")
            os.utime(old, (1000, 1000))
            os.utime(new, (2000, 2000))
            got = smoke_text(d, "TOK")
            self.assertIn(f"impl首行{len('older TOK line') + 1}bytes", got)
            self.assertIn("命中=1", got)

    def test_smoke_text_without_transcripts_flags_zero_dispatch(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(smoke_text(d, "TOK"),
                             "尚無 agent transcript（疑零派發 throw 或未啟動）")


class TestTargetResolution(unittest.TestCase):
    def test_dir_form_runid_form_and_garbage(self):
        """目標參數解析：目錄形（含分隔符）／runId 形（wf_ 起頭）／其餘無法解析。"""
        self.assertEqual(resolve_target("/a/b/wf_x"), ("dir", "/a/b/wf_x"))
        self.assertEqual(resolve_target("sub/wf_x"), ("dir", "sub/wf_x"))
        self.assertEqual(resolve_target("wf_abc-123"), ("runid", "wf_abc-123"))
        self.assertEqual(resolve_target("bogus")[0], None)

    def test_find_runid_dir_searches_across_sessions(self):
        with tempfile.TemporaryDirectory() as d:
            hit = os.path.join(d, "sess-2", "subagents", "workflows", "wf_abc")
            os.makedirs(os.path.join(d, "sess-1", "subagents", "workflows"))
            os.makedirs(hit)
            self.assertEqual(find_runid_dir(d, "wf_abc"), hit)
            self.assertIsNone(find_runid_dir(d, "wf_missing"))

    def test_wait_for_target_polls_until_found(self):
        seen = []

        def probe():
            seen.append(1)
            return "/hit" if len(seen) >= 3 else None

        got = wait_for_target(probe, timeout=180, interval=5,
                              _sleep=lambda s: None, _clock=lambda: 0)
        self.assertEqual(got, "/hit")
        self.assertEqual(len(seen), 3)

    def test_wait_for_target_times_out_when_target_never_appears(self):
        """不存在逾時形：假時鐘推進、逾時回 None；探測次數＝timeout/interval＋首probe。"""
        clock = {"t": 0.0}
        sleeps = []

        def fake_sleep(s):
            sleeps.append(s)
            clock["t"] += s

        got = wait_for_target(lambda: None, timeout=180, interval=5,
                              _sleep=fake_sleep, _clock=lambda: clock["t"])
        self.assertIsNone(got)
        self.assertEqual(sleeps, [5] * 36)   # 180/5＝36 次輪詢後放棄


class TestStallAndLoopVerdicts(unittest.TestCase):
    def _run_one(self, journal, newest_offset, now=1_000_000.0):
        """跑一輪 watch_loop（sleep 注入 no-op、mtime 函式級注入）→（輸出, 回傳值）。"""
        with tempfile.TemporaryDirectory() as d:
            if journal is not None:
                with open(os.path.join(d, "journal.jsonl"), "w",
                          encoding="utf-8") as fh:
                    fh.write(journal)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = watch_loop(
                    d, _sleep=lambda s: None, _now=lambda: now,
                    _newest=(lambda _d: None if newest_offset is None
                             else now - newest_offset),
                    _max_rounds=3)   # 判準改壞＝三輪零輸出紅燈、非掛死
            return buf.getvalue(), rc

    def test_newest_mtime_under_picks_max_and_none_when_empty(self):
        """stall 判定的 mtime 來源：整樹取最大；無檔案／目錄消失→None。"""
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "sub"))
            a = os.path.join(d, "a.txt")
            b = os.path.join(d, "sub", "b.txt")
            for p in (a, b):
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write("x")
            os.utime(a, (1000, 1000))
            os.utime(b, (2000, 2000))
            self.assertEqual(int(newest_mtime_under(d)), 2000)
            self.assertIsNone(newest_mtime_under(os.path.join(d, "ghost")))
            os.remove(a)
            os.remove(b)
            self.assertIsNone(newest_mtime_under(d))   # 有目錄無檔案＝None

    def test_stall_fires_only_past_threshold(self):
        out, rc = self._run_one('{"key": "impl-1"}\n', newest_offset=STALL + 1)
        self.assertIn("看門狗 STALL", out)
        self.assertIn(f"{STALL + 1}s 無寫入 > {STALL}s", out)
        self.assertEqual(rc, 0)

    def test_runaway_fires_on_distinct_key_overflow(self):
        """無持久 json 的 wf 目錄＝fallback floor 真的在管（backstop 未被卸除）；
        ★等號側同釘（L-020 同形）：恰 RUNAWAY_FLOOR 個 key 靜默——「等於門檻不叫」
        是契約的一部分、`>` 被無聲改 `>=` 即此臂紅（門檻常數釘死了、比較運算子也要釘）。"""
        at_floor = "".join('{"key": "agent-%d"}\n' % i
                           for i in range(RUNAWAY_FLOOR))
        out, rc = self._run_one(at_floor, newest_offset=1)
        self.assertEqual(out, "")            # 恰等於門檻：靜默
        self.assertEqual(rc, 0)
        journal = "".join('{"key": "agent-%d"}\n' % i
                          for i in range(RUNAWAY_FLOOR + 1))
        out, rc = self._run_one(journal, newest_offset=1)
        self.assertIn("看門狗 RUNAWAY", out)
        self.assertIn(f"不重複 agent key {RUNAWAY_FLOOR + 1} > {RUNAWAY_FLOOR}", out)
        self.assertEqual(rc, 0)

    def test_fail_loud_when_journal_nonempty_but_keyless(self):
        """健全性 fail-loud：journal 非空卻抽不到 key＝判準失效、吵鬧退出（不靜默恆綠）。"""
        out, _rc = self._run_one('{"event": "x"}\n{"event": "y"}\n', newest_offset=1)
        self.assertIn("看門狗 判準失效", out)
        self.assertIn("journal 2行", out)

    def test_unreadable_dir_reports_and_exits(self):
        out, _rc = self._run_one(None, newest_offset=None)
        self.assertIn("看門狗 目錄不可讀", out)


class TestRunawayCeilingDerivation(unittest.TestCase):
    """B-069：上限自 script 快照推導＋runaway 告警後生命週期（缺一＝新行為無守）。"""

    @staticmethod
    def _mk_wf(session, run="wf_t", persist=None):
        """自造暫存 session 佈局（絕不碰真 projects 目錄）：wf 目錄＋（可選）持久 json。"""
        wf = os.path.join(session, "subagents", "workflows", run)
        os.makedirs(wf)
        if persist is not None:
            os.makedirs(os.path.join(session, "workflows"), exist_ok=True)
            with open(os.path.join(session, "workflows", run + ".json"), "w",
                      encoding="utf-8") as fh:
                fh.write(persist)
        return wf

    def test_runaway_alert_keeps_loop_alive_and_says_once(self):
        """①告警後迴圈仍在（不 return、stall 覆蓋未歸零）②只 say 一次不洗版——
        B-069 前完全無此測、正是缺陷 (ii)（告警即自我卸除）長期潛伏的原因。"""
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess)   # 無持久 json → floor 25
            journal = "".join('{"key": "agent-%d"}\n' % i
                              for i in range(RUNAWAY_FLOOR + 1))
            with open(os.path.join(wf, "journal.jsonl"), "w",
                      encoding="utf-8") as fh:
                fh.write(journal)
            now = 1_000_000.0
            calls = {"n": 0}

            def newest(_d):
                calls["n"] += 1
                # 前兩輪新鮮（第 1 輪觸 runaway、第 2 輪驗只叫一次）、第 3 輪起 stall
                return now - (STALL + 1 if calls["n"] >= 3 else 1)

            sleeps = []
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = watch_loop(wf, _sleep=lambda s: sleeps.append(s),
                                _now=lambda: now, _newest=newest, _max_rounds=5)
            out = buf.getvalue()
            self.assertEqual(out.count("看門狗 RUNAWAY"), 1)   # 只叫一次
            self.assertIn("看門狗續行監看", out)               # 告警文字收尾句
            self.assertIn("先判形態", out)                     # 處置前先判扇出／編排
            self.assertIn("看門狗 STALL", out)   # 告警後迴圈仍在、stall 偵測仍有效
            self.assertEqual(len(sleeps), 3)     # 第 3 輪 stall 退出、runaway 未提前 return
            self.assertEqual(rc, 0)

    def test_ceiling_from_snapshot_fuse_and_path_layout(self):
        """②快照宣告 AGENT_FUSE=80 → 上限 160＝max(25, 2×80)、定案可快取；
        佈局＝wf 目錄向上三層 workflows/ 同名 .json（2026-08-11 實地驗證）。"""
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "const AGENT_FUSE = 80;\nlaunch();"}))
            self.assertEqual(derive_runaway_ceiling(wf), (160, True))

    def test_fanout_within_derived_ceiling_stays_silent(self):
        """②B-069 實暴反例：宣告 80→上限 160，50 key（原誤報現場）不再假警報；
        ★邊界兩臂（L-020 同形、等號側釘死）：恰 160 key（＝推導上限）靜默、
        161 key 才告警——`>` 被無聲改 `>=` 即 160 臂紅。"""
        def run(nkeys):
            with tempfile.TemporaryDirectory() as sess:
                wf = self._mk_wf(sess, persist=json.dumps(
                    {"script": "const AGENT_FUSE = 80;"}))
                journal = "".join('{"key": "agent-%d"}\n' % i
                                  for i in range(nkeys))
                with open(os.path.join(wf, "journal.jsonl"), "w",
                          encoding="utf-8") as fh:
                    fh.write(journal)
                now = 1_000_000.0
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = watch_loop(wf, _sleep=lambda s: None, _now=lambda: now,
                                    _newest=lambda _d: now - 1, _max_rounds=2)
                return buf.getvalue(), rc

        self.assertEqual(run(50), ("", 0))    # 原誤報現場：happy-path 靜默
        self.assertEqual(run(160), ("", 0))   # 恰等於推導上限：靜默
        out, rc = run(161)                    # 越過推導上限：告警（backstop 仍在）
        self.assertIn("不重複 agent key 161 > 160", out)
        self.assertEqual(rc, 0)

    def test_lazy_retry_upgrades_ceiling_after_json_lands(self):
        """④armed-live 第三形（懶讀重試腿唯一生效路徑、`final` 旗標存在理由）：
        第 1 輪 run 進行中無 json（floor、final=False ★不快取）→ 第 2 輪 json 落地
        （AGENT_FUSE=80→上限 160）＋key 增至 31——現行碼靜默；把 `if final:` 改成
        無條件快取＝floor 被永久釘死、31 > 25 假警報（＝B-069 要消滅的那一則）。
        ★實作坑：狀態切換必掛 _sleep（每輪起點）——掛 _newest 會在第 1 輪 journal
        讀取前生效、兩版皆靜默＝恆綠測。"""
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess)   # 第 1 輪：無持久 json（run 進行中形）

            def write_journal(n):
                with open(os.path.join(wf, "journal.jsonl"), "w",
                          encoding="utf-8") as fh:
                    fh.write("".join('{"key": "agent-%d"}\n' % i
                                     for i in range(n)))

            write_journal(5)
            calls = {"n": 0}

            def sleep_hook(_s):
                calls["n"] += 1
                if calls["n"] == 2:   # 第 2 輪起點：run 結束、json 落地＋key 續增
                    os.makedirs(os.path.join(sess, "workflows"), exist_ok=True)
                    with open(os.path.join(sess, "workflows", "wf_t.json"), "w",
                              encoding="utf-8") as fh:
                        fh.write(json.dumps({"script": "const AGENT_FUSE = 80;"}))
                    write_journal(RUNAWAY_FLOOR + 6)   # 31：> floor、< 160

            now = 1_000_000.0
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = watch_loop(wf, _sleep=sleep_hook, _now=lambda: now,
                                _newest=lambda _d: now - 1, _max_rounds=2)
            self.assertEqual(buf.getvalue(), "")   # 第 2 輪升 160、31 key 靜默＝重試腿有效
            self.assertEqual(rc, 0)
            self.assertEqual(calls["n"], 2)        # 確跑滿兩輪、非提前退出

    def test_missing_json_or_missing_declaration_falls_back_to_floor(self):
        """③顯式 fallback 分支逐一走到：無 json＝(25, False) 下輪再試；有 json 無
        script 欄／無宣告＝(25, True) 定案；壞 json（寫入中途）＝(25, False)；
        ★max() 保底之守護取交界兩側貼線判別值（L-020 同形、fix 第 3 輪；交界在
        fuse=12/13）：fuse=12（2×12=24＜floor）＝(25, True) 保底不收窄、fuse=13
        （2×13=26）＝(26, True) 升推導——判別值離界（舊臂 fuse=8）時「max(floor,X)
        改分段常數」類變異兩側皆綠＝交界逃逸；貼線後誤刪 max() 或界線挪動即紅
        （提案 §5「＝現行值、行為不退步」）。絕非「取不到就不檢查」（＝卸除 backstop）。"""
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess)                                # 無持久 json
            self.assertEqual(derive_runaway_ceiling(wf), (RUNAWAY_FLOOR, False))
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist='{"scriptPath": "/x"}')  # 無 script 欄
            self.assertEqual(derive_runaway_ceiling(wf), (RUNAWAY_FLOOR, True))
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "console.log('無保險絲宣告');"}))        # 無 AGENT_FUSE
            self.assertEqual(derive_runaway_ceiling(wf), (RUNAWAY_FLOOR, True))
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist='{"script": "AGENT_')   # 壞檔＝寫入中途
            self.assertEqual(derive_runaway_ceiling(wf), (RUNAWAY_FLOOR, False))
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "const AGENT_FUSE = 12;"}))  # 2×12=24＜floor：貼線內側、保底不收窄
            self.assertEqual(derive_runaway_ceiling(wf), (RUNAWAY_FLOOR, True))
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "const AGENT_FUSE = 13;"}))  # 2×13=26＞floor：貼線外側、升推導值
            self.assertEqual(derive_runaway_ceiling(wf), (26, True))

    def test_non_declaration_mentions_never_alter_the_ceiling(self):
        """★宣告 vs 提及的區分能力（fix 第 2 輪；此前五支測試全餵單一乾淨宣告＝零覆蓋）：
        ①註解先行——「前一輪 AGENT_FUSE = 20」在真宣告 80 之前，裸 pattern search()
        取最先出現的 20＝上限被竄窄（真實快照已近失手一次）；②前綴變體——
        MAX_AGENT_FUSE = 999 無真宣告，裸 pattern 取 999＝上限 1998＝backstop 靜默
        卸除（CLAUDE.md §9「a cap … silently stops being a cap」）。錨定式：①取真
        宣告 80→(160, True)；②取不到→顯式退 floor。③④＝錨定擋不住的兩形（被註解
        掉的真宣告／模板字串內字面、皆帶 const 關鍵字）——由 findall 取 min 擋
        （確認輪實暴：search 取首個使③推得 1998＝cap 放寬 50 倍）。"""
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "// 前一輪 AGENT_FUSE = 20\nconst AGENT_FUSE = 80"}))
            self.assertEqual(derive_runaway_ceiling(wf), (160, True))
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "const MAX_AGENT_FUSE = 999"}))
            self.assertEqual(derive_runaway_ceiling(wf), (RUNAWAY_FLOOR, True))
        # ③被註解掉的較大真宣告在前（帶 const、錨定不參與過濾）：min 後維持真宣告
        #   20→(40, True)；search 取首個會推得 1998。
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "// const AGENT_FUSE = 999  // 舊扇出版\nconst AGENT_FUSE = 20"}))
            self.assertEqual(derive_runaway_ceiling(wf), (40, True))
        # ④模板字串內較大字面在前（防呆①把六件套原文烤進 prompt 的制度化形）：同③。
        with tempfile.TemporaryDirectory() as sess:
            wf = self._mk_wf(sess, persist=json.dumps(
                {"script": "const P = `範本：const AGENT_FUSE = 400`\nconst AGENT_FUSE = 20"}))
            self.assertEqual(derive_runaway_ceiling(wf), (40, True))


class TestMainWiring(unittest.TestCase):
    def test_target_mode_wires_probe_token_and_watch(self):
        """main 接線釘死（復核補強：token/target 參數對調、或目標模式整支死掉＝本案紅）：
        目標模式下 token 取 argv[1]、目標目錄真的成為監看對象、ARMED 帶目標 basename。"""
        with tempfile.TemporaryDirectory() as d:
            wf = os.path.join(d, "wf_wire")
            os.makedirs(wf)
            seen = {}
            mod = sys.modules[__name__]

            def fake_watch(wf_dir, **_kw):
                seen["watched"] = wf_dir
                return 0

            def fake_smoke(wf_dir, token):
                seen["token"] = token
                return "冒煙樁"
            buf = io.StringIO()
            with unittest.mock.patch.object(mod, "watch_loop", fake_watch), \
                    unittest.mock.patch.object(mod, "smoke_text", fake_smoke), \
                    contextlib.redirect_stdout(buf):
                rc = main(["wf-watchdog.py", "tokX", wf])
            self.assertEqual(rc, 0)
            self.assertEqual(seen["watched"], wf)
            self.assertEqual(seen["token"], "tokX")
            self.assertIn("ARMED → wf_wire", buf.getvalue())

    def test_armed_line_reports_effective_runaway_ceiling(self):
        """★B-069 射程限縮揭露釘死：ARMED 行印「當下實際生效值」而非公式——
        持久 json 於 run 結束後才落地，live run 發射當下必然取不到快照，
        印 max(25,2×AGENT_FUSE) 即謊報一個當下不成立的門檻（2026-08-11 review 實暴）。
        ①無快照（＝live run 形）＝floor 實值＋升級條件揭露；
        ②快照已落地（＝鎖到已完成／resume 之 run）＝推導值定案。"""
        mod = sys.modules[__name__]

        def _armed_out(wf):
            buf = io.StringIO()
            with unittest.mock.patch.object(mod, "watch_loop",
                                            lambda *_a, **_k: 0), \
                    unittest.mock.patch.object(mod, "smoke_text",
                                               lambda *_a: "冒煙樁"), \
                    contextlib.redirect_stdout(buf):
                main(["wf-watchdog.py", "tok", wf])
            return buf.getvalue()

        with tempfile.TemporaryDirectory() as sess:
            wf = os.path.join(sess, "subagents", "workflows", "wf_live")
            os.makedirs(wf)                       # 無持久 json＝live run 形
            out = _armed_out(wf)
            self.assertIn(f"runaway>{RUNAWAY_FLOOR}key", out)   # 印 floor 實值
            self.assertIn("run 結束後", out)                     # 升級條件（射程）揭露
        with tempfile.TemporaryDirectory() as sess:
            wf = os.path.join(sess, "subagents", "workflows", "wf_done")
            os.makedirs(wf)
            os.makedirs(os.path.join(sess, "workflows"))
            with open(os.path.join(sess, "workflows", "wf_done.json"), "w",
                      encoding="utf-8") as fh:
                fh.write(json.dumps({"script": "const AGENT_FUSE = 80;"}))
            self.assertIn("runaway>160key", _armed_out(wf))     # 已落地＝推導定案值

    def test_journal_partial_last_line_not_counted(self):
        """wc -l 等價釘死：尾端無換行殘行（寫入中途）不計 raw、不觸發偽「判準失效」。"""
        self.assertEqual(journal_key_stats('{"event": "x"}'), (0, 0))
        self.assertEqual(journal_key_stats('{"key": "a"}\n{"event"'), (1, 1))


class TestOutputDiscipline(unittest.TestCase):
    def test_every_print_flushes(self):
        """★B-005 陷阱檔文釘死：本檔每個 print 呼叫皆帶 flush=True（pipe 塊緩衝下
        ARMED 不現身＝外觀同發射失敗、且該行是唯一冒煙訊號）。"""
        with open(__file__, encoding="utf-8") as fh:
            src = fh.read()
        offenders = [ln for ln in src.splitlines()
                     if "print(" in ln and "flush=True" not in ln]
        self.assertEqual(offenders, [], msg=str(offenders))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
