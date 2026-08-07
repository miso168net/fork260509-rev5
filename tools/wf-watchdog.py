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
  ★冒煙 token 不可取字面 test（會被當自測子命令）。

行為：ARMED 一行（夾帶冒煙：最早 agent transcript＝implementer 首行 byte 數＋冒煙 token
  命中數）→ 靜默迴圈（60s），僅 stall／runaway 告警時輸出並退出。
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
import sys
import tempfile
import time
import unittest
import unittest.mock
from glob import glob

STALL = 780      # 秒；>最長合法 cargo（sub-agent Bash 單命令 600s 上限＋margin）
RUNAWAY = 25     # 不重複 agent key 數；2× 單元理論上限（防呆③ AGENT_FUSE=20 之外部 backstop）
#   ★判準＝數 journal 不重複 agent key、★不數行數（rev5 差分，承 rev4:L-144 同族實證）：
#   行數型 backstop 在 kill/resume 疊代下累積誤報——同一支 agent 每輪 launch 都留新事件列，
#   journal 行數線性成長而實際併發 agent 數不變（實證：三輪 launch 使 journal 達 26 行觸發
#   RUNAWAY 誤報，實際不重複 key＝10≤11 理論上限、保險絲完好）。key 去重後才等價於「派了幾支」。
LOOP_SLEEP = 60            # 秒；靜默迴圈間隔
DISCOVER_SLEEP = 10        # 秒；自動發現模式先讓 launch 建目錄（沿舊 bash 版語意）
TARGET_POLL_INTERVAL = 5   # 秒；目標模式輪詢間隔
TARGET_POLL_TIMEOUT = 180  # 秒；目標模式等待目標目錄出現的上限


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
    """靜默迴圈：60s 一輪；判準失效／RUNAWAY／STALL 告警即輸出並退出（happy-path 靜默）。
    _max_rounds＝測試注入的輪數上限——判準被改壞時測試收「零輸出」紅燈、而非 busy loop
    掛死 pre-commit／bootstrap（兩處裸跑自測無 timeout；2026-08-08 復核）；生產恆 None。"""
    base = os.path.basename(wf_dir.rstrip("/"))
    rounds = 0
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
        if nkeys > RUNAWAY:
            _say(f"看門狗 RUNAWAY：不重複 agent key {nkeys} > {RUNAWAY}"
                 "（防呆③保險絲疑失效）→ /workflows 查→TaskStop wf")
            return 0
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
    _say(f"看門狗 ARMED → {os.path.basename(wf_dir.rstrip('/'))}｜冒煙: "
         f"{smoke_text(wf_dir, token)}（stall>{STALL}s／runaway>{RUNAWAY}key；"
         "完成通知到請 TaskStop 本 Monitor）")
    return watch_loop(wf_dir)


# ---------------------------------------------------------------------------
# 自測（離線、合成 fixtures；一律隔離暫存目錄、絕不讀寫真 projects 目錄）
# ---------------------------------------------------------------------------


class TestConstantsPinned(unittest.TestCase):
    """★常數字面釘死（防靜默漂移）：閾值＝CLAUDE.md §2 契約字面的一部分。"""

    def test_thresholds_match_the_contract(self):
        self.assertEqual(STALL, 780)
        self.assertEqual(RUNAWAY, 25)
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
        journal = "".join('{"key": "agent-%d"}\n' % i for i in range(RUNAWAY + 1))
        out, _rc = self._run_one(journal, newest_offset=1)
        self.assertIn("看門狗 RUNAWAY", out)
        self.assertIn(f"不重複 agent key {RUNAWAY + 1} > {RUNAWAY}", out)

    def test_fail_loud_when_journal_nonempty_but_keyless(self):
        """健全性 fail-loud：journal 非空卻抽不到 key＝判準失效、吵鬧退出（不靜默恆綠）。"""
        out, _rc = self._run_one('{"event": "x"}\n{"event": "y"}\n', newest_offset=1)
        self.assertIn("看門狗 判準失效", out)
        self.assertIn("journal 2行", out)

    def test_unreadable_dir_reports_and_exits(self):
        out, _rc = self._run_one(None, newest_offset=None)
        self.assertIn("看門狗 目錄不可讀", out)


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
