#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/decrypt-secrets.py — 解密管線：deploy/secrets.dev.enc.yaml → $SECRETS_DIR/*.txt
（ADR 0010 轉換批①、B-035）

等價重寫自 deploy/decrypt-secrets.sh：判定分支與退出碼逐一對應，兩處實作收斂＝
①落點解析改用共用庫 deploy/secrets_common.py ②解密改 `sops -d --output-type json`＋
`json.loads`，**整段刪除非裸量純量斷言**（舊檔那 26 行的成因＝bash 逐行拆 key 拿不回引號形
與區塊純量形的原值，只能把它們翻成吵鬧失敗；真 JSON 解析後兩形皆逐位元組正確還原，
人工填值機密不再被解析力反噬——ADR 0010 轉換集①核心收益）。
★但「還原得回來」≠「落點載得動」：落點檔形＝一值一檔零換行（rev4:P4.1／rev4:P5.7），
故刪斷言後另立一道**針對還原後值**的 CR／LF 窄護欄（newline_hits），只擋管線證明載不動的
那一類、零寫入退出；舊斷言誤殺的五形（冒號空白／井號／前後空白／引號字元／星號起首）
一律放行，ADR 0010 的收益全數保住。

用法：自 repo 根、有 tty 的終端執行 `python3 deploy/decrypt-secrets.py`

  B′ 私鑰＝passphrase 加殼 identity → sops 對**每個 recipient** 各索一次 passphrase
  （皆為同一把鑰的同一個 passphrase）。★勿假設「恰跳 1 次」——那是單 recipient 時代的
  舊值，加人當日即失效（L-005）；次數由本腳本自密文現算後印在預告行。
  ★提示行與解密輸出同流被暫存檔捕捉（wrapper -t＝容器 pty、docker 單流輸出）——畫面
  未必顯示提示，故「盲打、次數靠猜」正是 L-005 的病灶。
  ★互動姿態＝**自動應答**（B-036）：passphrase 只自 /dev/tty 收**一次**（不回顯），其後
  由本腳本在 pty 上偵測到提示字樣才代餵、每現一次餵一次——**次數由機器數、絕不預測**，
  L-005 那條「寫死當時基數」的失效路徑從根上消滅；不需 passphrase 的鑰則零提示直通。
  ★退路：RV5_DECRYPT_MANUAL=1 → 回到逐次手打（災難復原路徑不鎖死；本值只認 "1"）。
  ★安全代價：暴露面由「鍵盤→容器直達」變成「經本腳本記憶體」。passphrase 絕不進 argv／
  環境變數／磁碟／log，用畢即零填其位元組緩衝（python 的 str 不可變、CPython 不保證即刻
  回收其緩衝——該層只能盡力而為，本檔如實記載此極限、不宣稱做不到的清零）。另備回顯守衛：
  passphrase 字面一旦現身暫存流，該流整段不倒流給 operator、暫存清空、指名失敗。

子命令：
  （無參數）  解密本體：tty 守衛 → repo 根守衛 → 落點解析 → 落點 0700 自證 →
              暫存落點安全自證 → 預告行 →（自動路徑：getpass 一次 → pty 代餵）
              sops 解密 → 回顯守衛 → JSON 拆 key → key 數／名稱斷言 →
              既有 .txt.new 提醒 → 逐檔寫入（644、無尾端換行、不覆寫 DIFF）
  test        跑自帶測試（unittest、離線、stdlib-only、不需 docker；一律隔離暫存目錄，
              絕不讀寫真機密落點、絕不觸碰真密文）

退出碼：全綠 0；本腳本自身的斷言不符 1；sops 解密失敗＝原樣沿用 sops 的退出碼；
用法錯誤 64（EX_USAGE；沿 tools/*.py 家族慣例）。

契約要點對照（＝contracts/secret-pipeline.md rev4:§P4，fail-loud：斷言不符＝零寫入＋非零
退出＋指名）：
  rev4:P4.2 tty 守衛：非互動吵鬧失敗、不 hang、不寫壞檔
  rev4:P4.4／rev4:P4.6 自建 0700 子目錄＋權限自證（縱深防禦、與落點無關；rev4:ADR 0080 決策 4）
  rev4:P4.3 key 數與名稱斷言：缺／多 key＝零寫入＋非零退出＋指名（絕不落到 generate 造亂數路徑）
  rev4:P4.1／rev4:P5.7 逐檔無尾端換行寫入；rev4:P4.7 檔 644
  rev4:P4.5 現值 ≠ 解密值 → 另存 <name>.txt.new＋警示、不覆寫；現值＝解密值 → 照寫（冪等）
  rev4:FR-021／rev4:SC-005 明文暫存落點：$XDG_CACHE_HOME（回退 $HOME/.cache）之 0700 暫存目錄、
    非 repo 內 tmp/（/mnt/d＝9p、chmod no-op＝實效 777）；落點性質不符即 fail-loud
  單次 sops -d 收全 YAML 再本地拆 key——B′ 下每次容器呼叫都要輸 passphrase（每 recipient
  一次），絕不逐 key --extract 重呼容器

前代血緣（rev4 考古壓成一句）：rev4:019-secrets-sops 立本管線（rev4:P4.1~rev4:P4.7 七條），
其後 rev4:020 增 smtp_password／email_verify_secret 兩 leaf；rev5 加人日（recipient 1→2）
暴露互動失效（L-005）→ 預告行改自密文現算；本檔＝ADR 0010 轉換批①之等價重寫。

★輸出串流沿用 bash 版分工、刻意不統一（等價重寫不夾帶行為變更）：預告行、逐檔
WRITTEN／DIFF 行、完成行走 stdout；一切 FAIL 與 WARN 走 stderr。
"""
import contextlib
import getpass
import importlib.util
import io
import json
import os
import platform
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import termios
import time
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 落點解析共用庫（ADR 0010 轉換批①）：三消費者單一實作面。
# ★以 __file__ 推出的絕對路徑載入：不依賴 CWD，也不把 deploy/ 塞進 sys.path（避免搜尋路徑
#   遮蔽）。★載入失敗＝印真因後原樣拋（fail-loud）：落點解析錯了就是把 10 支明文寫到別處。
_SECRETS_COMMON_PATH = os.path.join(HERE, "secrets_common.py")
try:
    _spec = importlib.util.spec_from_file_location("secrets_common", _SECRETS_COMMON_PATH)
    _secrets_common = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_secrets_common)
except Exception as _ex:
    print(f"[decrypt-secrets] ERROR 載入共用庫 {_SECRETS_COMMON_PATH} 失敗：{_ex}"
          "——落點解析不得靜默降級（寫錯落點＝10 支明文散落）", file=sys.stderr)
    raise

resolve_secrets_dir = _secrets_common.resolve_secrets_dir

# 10 key 名單（＝deploy/secrets.dev.enc.yaml 全集；9 leaf＋alert_webhook_url；rev4:020 增
# smtp_password／email_verify_secret；composite 三支由 generate-secrets.sh 自 leaf 重生、
# 不進加密檔）。★次序即輸出次序與寫入次序。
EXPECTED_KEYS = ("postgres_password", "redis_password", "jwt_secret", "refresh_token_secret",
                 "captcha_secret", "reaper_password", "grafana_admin_password",
                 "smtp_password", "email_verify_secret", "alert_webhook_url")

ENC_REL = os.path.join("deploy", "secrets.dev.enc.yaml")
SOPS_REL = os.path.join(".", "deploy", "sops.sh")
DIR_MODE_OK = "700"
FILE_MODE = 0o644
TMP_PREFIX = "decrypt."
CACHE_LEAF = "fork260509-rev5"

# 密文內 recipient 行（＝提示次數下界）；同 bash 版 `grep -cE '^[[:space:]]*recipient: age1'`。
RE_RECIPIENT = re.compile(r"^[ \t]*recipient: age1", re.M)
# ANSI CSI 序列（容器 pty 的清行／游標控制）；同 bash 版 sed 的 ESC\[[0-9;]*[A-Za-z]。
RE_ANSI_CSI = re.compile("\x1b\\[[0-9;]*[A-Za-z]")
# JSON 物件起點候選＝行首左大括號（sops --output-type json 頂層物件恆自行首起）。
RE_JSON_START = re.compile(r"^\{", re.M)

# ---- 自動應答 driver 的常數（B-036）----
# sops／age 索 passphrase 的提示字樣。★刻意只取共同前綴、不整句釘死「Enter passphrase for
# identity: 」：識別字愈長愈綁死該版 sops 的措辭尾巴，而本偵測若失配，失效方向是「等不到
# 提示→整體逾時吵鬧失敗」（見 DRIVER_TOTAL_SEC），不是靜默少餵一次。
PROMPT_MARK = "Enter passphrase"
# 手動退路開關（只認 "1"；其他值一律走自動路徑）
MANUAL_ENV = "RV5_DECRYPT_MANUAL"
# ★下列四個時間邊界一律寫死在本檔常數、**絕不取自環境變數或命令列**：安全邊界與不可信
#   輸入同源＝邊界可被外部關掉（"逾時上限取自 env、env 沒設就 None、比較恆為 False" 這條
#   靜默失效路徑）。要調就改本檔並附測試。
DRIVER_SELECT_SEC = 0.5      # 單次 select 等待（＝逾時判定的顆粒度）
DRIVER_TOTAL_SEC = 300.0     # 整體上限（含 docker 拉映像／容器啟動；逾時＝終結子行程）
DRIVER_SETTLE_SEC = 0.05     # 見提示到餵入之間的沉澱（見 run_sops_auto 的回顯競態註）
DRIVER_GRACE_SEC = 3.0       # SIGTERM 後等收屍的寬限，逾時改 SIGKILL


# ---------------------------------------------------------------------------
# 純判定（零 IO；test 子命令的主要覆蓋面）
# ---------------------------------------------------------------------------

def normalize_stream(text):
    """暫存流正規化（失敗診斷與拆 key 兩路共用）。

    暫存流雜訊＝passphrase 提示行＋ANSI 清行序列＋容器 pty 的 CRLF
    （wrapper rev4:P1.2 註／rev4:L-168）：①CR 一律轉行界 ②剝 ANSI CSI 序列。
    ★非 tty 時 sops.sh 不配 -i -t、stdout 乾淨，本函式即恆等變換——但仍無條件套用：
    正規化只在 tty 分支才跑會讓兩條路徑的 parser 不同形，而 tty 分支恰是自動化測不到那條。
    """
    return RE_ANSI_CSI.sub("", text.replace("\r", "\n"))


def extract_payload(text):
    """正規化後的暫存流 → (dict, 錯誤訊息)。

    ★先整段試 `json.loads`（非 tty 乾淨流的常路），失敗才自各個「行首左大括號」重試——
    tty 分支的 passphrase 提示行與資料同流，前置雜訊必須濾掉才 parse（A3 逐字保留的外部
    條件複雜度之一）。用 raw_decode 而非 loads：容器 pty 在 JSON 之後還可能吐控制殘餘，
    「尾端有雜訊」不該被當成解析失敗。
    """
    dec = json.JSONDecoder()
    for pos in [0] + [m.start() for m in RE_JSON_START.finditer(text)]:
        try:
            data, _end = dec.raw_decode(text, pos)
        except ValueError:
            continue
        if not isinstance(data, dict):
            return None, "解密輸出的 JSON 頂層不是物件——密文結構非預期的扁平 key/value"
        return data, None
    return None, "解密輸出無法解析為 JSON（sops --output-type json 的產物被截斷或非 JSON）"


def restore_value(raw):
    """單一 key 的值還原成落點檔內容（str）→ (值, 錯誤訊息)。

    ★這裡就是「刪非裸量純量斷言」之所以成立的地方：JSON 的字串已是**還原後的原值**，
    引號形（值含「冒號空白」／井號／前後空白／引號字元）與區塊純量形（值含換行）在此
    一律逐位元組正確——舊 bash 版逐行拆 key 拿到的是「含引號字元的原樣 token」、無法還原，
    才只能把首字元落 `" ' | >` 四者判成 FAIL（舊檔 :195-220）。
    ★非字串純量（sops 於密文內記型別、解密即還原）以 JSON 字面回填，與 bash 版逐字寫入
    `true`／`123`／`null` 的結果相同；容器／陣列＝結構性非預期，指名失敗不代猜。
    """
    if isinstance(raw, str):
        return raw, None
    if isinstance(raw, (dict, list)):
        return None, "值是 JSON 容器（物件／陣列）——本管線只收扁平純量"
    return json.dumps(raw), None


def collect_values(payload):
    """payload → (values, 型別錯誤清單)。values＝{key: str}（只收 EXPECTED_KEYS 之外亦收，
    多 key 的指名歸 assert_keys）。"""
    values, bad = {}, []
    for key, raw in payload.items():
        val, err = restore_value(raw)
        if err:
            bad.append(f"{key}（{err}）")
        else:
            values[key] = val
    return values, bad


def assert_keys(values):
    """rev4:P4.3 key 數與名稱斷言（純判定）：回 (missing, extra)。

    missing＝缺 key **或值為空字串**（沿 bash 版 `[ -z ]` 判定：空機密無合法用途）；
    extra＝解密結果含 EXPECTED_KEYS 以外的 key。
    """
    missing = [k for k in EXPECTED_KEYS if not values.get(k)]
    extra = sorted(k for k in values if k not in EXPECTED_KEYS)
    return missing, extra


def newline_hits(values):
    """還原後值的 CR／LF 窄護欄（純判定）：回含換行字元的 key 清單。

    ★這**不是**舊檔那道被刪斷言的復辟：舊判準看的是 YAML token 首字元（`" ' | >`），把含
    「冒號空白」／井號／前後空白／引號字元／星號起首的人工填值機密一併打死——那是 bash 解析
    力不足的補丁，正是 ADR 0010 要消滅的東西；本判準看的是**還原後的值本身**有沒有換行字元，
    前述五形一律放行（機器守衛＝TestNewlineGuard 的放行案）。
    ★為何仍須擋：落點檔形＝一值一檔、零換行（rev4:P4.1／rev4:P5.7 之 printf '%s' 寫檔形
    不變式），deploy/preflight-secrets.py 的 content_hits 即該不變式的可機檢投影、見任一
    CR／LF 就判內容劣化 rc=1 擋 up。放行等於讓本腳本印「N 支 key 檔已就緒」rc=0、緊接的
    preflight 卻判劣化，而 preflight 給的處置是「重跑 decrypt」——重跑只會再產同一支壞檔，
    operator 在災難復原路徑上原地打轉、真因（加密檔內那個多行值）永不現形。故在此指名真因、
    零寫入退出（rev4:P4.3 同族：靜默壞值一律翻成吵鬧失敗；舊 bash 版於此形亦為零寫入 rc=1，
    本護欄同時把該情境的新舊等價補回）。
    """
    return [k for k in EXPECTED_KEYS
            if "\n" in values.get(k, "") or "\r" in values.get(k, "")]


def redact_stream(text):
    """失敗路徑的暫存流過濾（純判定）→ (保留行, 濾除行數)。

    ★RAW 同時承載容器 stdout 與 stderr（wrapper -t＝單一 pty 流、rev4:L-168），故「解密失敗
    就不含明文」只是 sops 正常錯誤路徑（MAC 檢查早於 Emit）的性質、不是本腳本的保證：
    已 Emit 才異常結束者（stdout 寫入失敗、passphrase 過關後收 SIGINT）RAW 即含明文。
    註解斷言防不了洩漏——倒出前先濾掉資料行，只留診斷訊息。
    ★JSON 形的判準比 bash 版的逐行 key 樣式更保守：一旦見到行首左大括號就視為進入資料區、
    其後全濾（頂層物件內每一行都可能是機密），另補「行內出現任一已知 key 名」的兜底
    （涵蓋被截斷的部分輸出）。
    """
    kept, redacted, in_data = [], 0, False
    for line in normalize_stream(text).split("\n"):
        if not line.strip():
            continue                       # CRLF 轉行界留下的空殘行（不計數、不解除資料區）
        if line.lstrip().startswith("{"):
            in_data = True
        if in_data or any(k in line for k in EXPECTED_KEYS):
            redacted += 1
            continue
        kept.append(line)
    return kept, redacted


def echo_hit(raw_text, passphrase):
    """回顯守衛純判定（B-036）：passphrase 字面是否現身於暫存流。

    ★為何需要：自動路徑把 passphrase 寫進 pty，line discipline 的本地回顯若沒關（或容器內
    sops 尚未關），這串位元組會原樣回吐到 master 端、落進暫存流——而暫存流在失敗路徑是要
    redact 後倒給 operator 的（redact_stream 濾的是**資料行**，攔不住混在提示行尾的回顯）。
    ★判準對**正規化前後兩形**都看：CR→行界與剝 ANSI CSI 都可能把回顯切斷或接合，只驗一形
    會有一邊漏網。
    ★已知代價（如實記載、不假裝沒有）：若某支機密的值恰等於 passphrase，本判準會把一次
    正常解密判成回顯而擋下。該情形本身即「passphrase 同時是機密值」的異常，指名擋下比放行
    正確；operator 走 RV5_DECRYPT_MANUAL=1 退路即可繼續。
    """
    if not passphrase:
        return False
    return passphrase in raw_text or passphrase in normalize_stream(raw_text)


def recipient_count(enc_text):
    """密文內 recipient 數（＝提示次數）。★自密文現算、不寫死字面——寫死的「恰 1 次」正是
    加人當日誤導 operator 空答的來源（L-005）。"""
    return len(RE_RECIPIENT.findall(enc_text))


def plan_write(existing, value):
    """單檔寫入判定（純判定）：回 "WRITTEN" 或 "DIFF"。

    existing＝落點現有位元組（缺檔傳 None）。現值 ≠ 解密值＝另存 .new 不覆寫
    （rev4:P4.5，decrypt 不得成為靜默覆寫路徑）；缺檔＝新寫、現值＝解密值＝冪等照寫。
    ★比對走**逐位元組**（同 bash 版 `printf '%s' | cmp -s -`）——字串比較會剝尾端換行、
    對「檔尾多一個 LF」結構性失明。
    """
    return "WRITTEN" if existing is None or existing == value else "DIFF"


# ---------------------------------------------------------------------------
# IO 面
# ---------------------------------------------------------------------------

def _mode_of(path):
    """檔／目錄權限位（八進位字串，同 `stat -c '%a'`）。

    ★bash 版寫成 `stat -c … || stat -f …` 雙形是為了同時吃 GNU 與 BSD stat；python 的
    os.stat 本身跨平台，雙形自然消解——判定不變。
    """
    return oct(os.stat(path).st_mode & 0o7777)[2:]


def fs_type(path):
    """檔系統型別字串（同 `stat -f -c '%T'`）。

    ★fs 判定限 Linux——BSD stat -f 語意不同、不可直譯，非 Linux 一律回 "non-linux"
    （與 bash 版同字面，訊息逐字對應）。★ADR 0010 硬約束一允許保留單次 stat -f
    subprocess：v9fs 判定的另一形是讀 /proc/self/mountinfo，但那要自己做最長前綴匹配與
    bind mount 解析，比 subprocess 更大且更易錯；本檔沿 deploy/preflight-secrets.py 同形。
    """
    if platform.system() != "Linux":
        return "non-linux"
    r = subprocess.run(["stat", "-f", "-c", "%T", path], capture_output=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.strip()


def find_stale_new(secrets_dir):
    """落點內既有的 `*.txt.new` → 排序後的檔名清單（無目錄／無命中皆回空）。

    ★**不用 `glob.glob`**：它把**整條落點路徑**當成樣式，落點自身含 `[`／`*`／`?` 時
    （SECRETS_DIR 走環境變數那條無字元白名單——白名單只套 `.env` 那條）比對整批落空、
    「有待決 .new」這道提醒**靜默消失**；bash 版 `for f in "$SECRETS_DIR"/*.txt.new` 的目錄段
    有引號＝逐字字面，只有 `*.txt.new` 是樣式。失效方向是靜默，故改列目錄再逐名過濾。
    ★略過前導點名（bash 的 `*` 同樣不匹配）；不加 isfile 過濾（bash 用 `-e`、目錄同樣算）。
    """
    try:
        names = os.listdir(secrets_dir)
    except OSError:
        return []
    return sorted(n for n in names if n.endswith(".txt.new") and not n.startswith("."))


def write_secrets(secrets_dir, values):
    """逐檔寫入（斷言全過後才叫用）→ (逐檔訊息行, 另存 .new 的 key 清單)。

    rev4:P4.1／rev4:P5.7 無尾端換行；rev4:P4.7 檔 644。
    ★.new 亦為 644（不是 600）：WARN 指示的補救＝`mv .new` 蓋回，mv 於同 fs＝rename、
    mode 原樣保留——.new 若為 600，蓋回後落點檔終值即 600、違反 rev4:P4.7／rev4:FR-022，
    且只在開 obs／metrics 軌時才炸（grafana 472／postgres-exporter 65534／
    redis-exporter 59000 全部 Permission denied）。目錄本身 700，644 不擴大暴露面。
    """
    lines, new_saved = [], []
    for key in EXPECTED_KEYS:
        dst = os.path.join(secrets_dir, key + ".txt")
        payload = values[key].encode("utf-8")
        existing = None
        if os.path.isfile(dst):
            with open(dst, "rb") as fh:
                existing = fh.read()
        if plan_write(existing, payload) == "DIFF":
            with open(dst + ".new", "wb") as fh:
                fh.write(payload)
            os.chmod(dst + ".new", FILE_MODE)
            new_saved.append(key)
            lines.append(f"  {key}.txt DIFF→已另存 {key}.txt.new（原檔不動、請人工比對取捨）")
        else:
            with open(dst, "wb") as fh:
                fh.write(payload)
            os.chmod(dst, FILE_MODE)
            lines.append(f"  {key}.txt WRITTEN")
    return lines, new_saved


def prepare_secrets_dir(secrets_dir):
    """rev4:P4.4／rev4:P4.6 自建 0700 子目錄＋權限自證 → 錯誤訊息清單（空＝放行）。

    drvfs（/mnt/*）：chmod 結構性 no-op、權限恆 777——現行落點已知限制（rev4:US3 遷移消滅），
    只 WARN 不擋（WARN 由呼叫端印，本函式回空清單並以第二個回傳值帶出）。
    """
    os.makedirs(secrets_dir, exist_ok=True)
    os.chmod(secrets_dir, 0o700)
    mode = _mode_of(secrets_dir)
    if mode == DIR_MODE_OK:
        return [], None
    ftype = fs_type(secrets_dir)
    if ftype == "v9fs":
        return [], (f"WARN：{secrets_dir} 權限={mode}"
                    f"（fs={ftype}、chmod 為 no-op；rev4:US3 遷移後消失）")
    return [f"FAIL：{secrets_dir} chmod 700 未生效（實際 {mode}、fs={ftype}）。"], None


def prepare_tmp_dir(env):
    """明文中間產物的暫存落點（rev4:FR-021／rev4:SC-005）→ (路徑, 錯誤訊息清單)。

    ★不得落 repo 內 tmp/：/mnt/d＝9p（v9fs），umask／chmod 皆結構性 no-op——暫存檔會以
    實效 777、Windows 側可見的形式承載 10 支完整明文，正是「/mnt/d 全樹零明文機密檔」要
    消滅的暴露面，且不隨 rev4:US3 落點遷移而消失。
    ★本檔由 host 收 stdout 產生、不進容器（wrapper 只掛載 $PWD 供 sops 讀 enc 檔），故不受
    contracts rev4:§P7「暫存明文必須落 repo 內」限制——該限只適用於要餵回 sops 加密的檔。
    """
    cache = env.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    tmp_root = os.path.join(cache, CACHE_LEAF)
    os.makedirs(tmp_root, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix=TMP_PREFIX, dir=tmp_root)
    ftype, mode = fs_type(tmp_dir), _mode_of(tmp_dir)
    if ftype == "v9fs" or mode != DIR_MODE_OK:
        return tmp_dir, [
            f"FAIL：暫存明文落點 {tmp_dir} 不安全（fs={ftype}、mode={mode}；需非 v9fs 且 700）。",
            "      成因＝$HOME（或 $XDG_CACHE_HOME）落在 /mnt/* 之 9p 上、chmod 為 no-op。",
            "      處置＝將 XDG_CACHE_HOME 指到 ext4 路徑（如 /home/$USER/.cache）後重跑。"]
    return tmp_dir, []


def run_sops(root, raw_path):
    """單次 sops -d 收全密文至暫存（明文中間產物）→ 退出碼。

    ★`--output-type json`＝ADR 0010 轉換批①的核心改法（真 YAML 解析取代逐行拆 key）。
    ★stdin 原樣繼承（passphrase 提示要走真 tty）、stderr 不重導向（同 bash 版；容器 -t 下
    兩流本就在同一個 pty 裡合流，host 端再分也分不開）。
    """
    with open(raw_path, "wb") as fh:
        return subprocess.run([SOPS_REL, "-d", "--output-type", "json", ENC_REL],
                              cwd=root, stdout=fh).returncode


# ---------------------------------------------------------------------------
# 自動應答 driver（B-036：passphrase 只打一次）
# ---------------------------------------------------------------------------

def _reap(pid, block):
    """收屍 → 退出碼；尚未結束（block=False）或已被別處收走一律回 None。

    ★退出碼取 os.waitstatus_to_exitcode：被訊號打死者回負值，與 subprocess.run().returncode
    同形——手動路徑與自動路徑的 rc 語意因此一致（本檔對 sops 的退出碼是原樣沿用）。
    """
    try:
        done, status = os.waitpid(pid, 0 if block else os.WNOHANG)
    except ChildProcessError:
        return None
    if done != pid:
        return None
    return os.waitstatus_to_exitcode(status)


def _terminate_child(pid):
    """終結 pty 子行程並收屍（盡力而為）→ 退出碼（收不到屍回 None）。

    ★為何必須主動終結：pty.fork() 的子行程自成 session（setsid），host 終端的 Ctrl-C
    只送 SIGINT 給**本行程**、不會沿著 pty 傳下去——不收拾就留下孤兒 `docker run`
    （容器還活著，--rm 也不會清）。SIGINT handler 與逾時兩路都走本函式。
    ★sops.sh 以 `exec docker run` 收尾＝子行程 pid 就是 docker run 本身，SIGTERM 打中它
    即由 docker 轉送容器並依 --rm 清掉；SIGTERM 寬限內沒死才升級 SIGKILL。
    """
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            return _reap(pid, False)
        deadline = time.monotonic() + DRIVER_GRACE_SEC
        while time.monotonic() < deadline:
            code = _reap(pid, False)
            if code is not None:
                return code
            time.sleep(0.05)
    return None


def run_sops_auto(root, raw_path, passphrase):
    """自動應答解密：pty 下起 wrapper、偵測到提示才代餵 passphrase → (退出碼, 錯誤訊息)。

    與 run_sops 同一條流：pty 下 wrapper 見 stdin 是 tty → 配 -i -t → 容器 pty 單流輸出，
    故正規化與拆 key 兩段（normalize_stream／extract_payload）原樣沿用、一個字不改。
    ★餵入判準＝**偵測到提示字樣才餵、每現一次餵一次**；提示總數由本迴圈邊讀邊數，
    絕不預先算「該餵幾次」（L-005：寫死當時基數的預期，在基數變動當天靜默失效）。
    ★計數方式＝每收一段就把**累積流**正規化後重數 PROMPT_MARK 出現次數：提示可能被拆成
    好幾次 read 送達（pty 非行緩衝）、也可能夾 CRLF 與 ANSI CSI，只看單段會漏數。
    ★零提示路徑（identity 無 passphrase 殼、sops 根本不索）必須自然通過：本迴圈不等待
    提示、也不因「一次都沒餵」判異常——子行程結束（master 端 EOF／EIO）即收尾。
    ★DRIVER_SETTLE_SEC：sops 是「先印提示、再關回顯」，我們見到提示到寫入之間有一道
    理論競態（真實路徑上還隔著 docker CLI 與容器 pty 兩跳、實務上不會輸）；沉澱一下純屬
    便宜保險，真正的兜底是 echo_hit 回顯守衛。
    """
    pid, master_fd = pty.fork()
    if pid == 0:                                  # ---- 子行程：stdio 皆為 pty slave ----
        try:
            os.chdir(root)
            os.execv(SOPS_REL, [SOPS_REL, "-d", "--output-type", "json", ENC_REL])
        except BaseException:                     # noqa: BLE001（exec 失敗一律以 127 現形）
            pass
        os._exit(127)

    # ★關掉 pty 的本地回顯：line discipline 預設 ECHO on，代餵的位元組會被原樣回吐到
    #   master 端而落進暫存流（實測）。真實路徑上 docker -t 會自行把終端切 raw、容器內
    #   sops 亦以 term.ReadPassword 關回顯，故本行主要防的是「wrapper 不經 docker」之形
    #   與 docker 尚未接手前的空窗。★tcsetattr 打在 master fd 上即作用於該 pty 對的
    #   line discipline（Linux）。拿不到 termios 不該讓解密停擺——回顯守衛是兜底。
    try:
        attrs = termios.tcgetattr(master_fd)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(master_fd, termios.TCSANOW, attrs)
    except (termios.error, OSError):
        pass

    # ★passphrase 只在本函式內以 bytearray 持有（可就地零填）；絕不進 argv／環境變數／
    #   磁碟／log。呼叫端那個 str 的緩衝由 CPython 管、清不掉——A7 的極限在此如實記載。
    pw_buf = bytearray((passphrase + "\n").encode("utf-8"))
    chunks, fed, err, code, aborted = [], 0, None, None, []

    def _on_sigint(_sig, _frm):
        aborted.append(_terminate_child(pid))

    prev_handler = signal.signal(signal.SIGINT, _on_sigint)
    deadline = time.monotonic() + DRIVER_TOTAL_SEC
    try:
        while True:
            if time.monotonic() >= deadline:
                err = (f"pty 驅動逾時（上限 {DRIVER_TOTAL_SEC:.0f} 秒）——已終結子行程"
                       "（不留孤兒 docker run）。常見成因＝docker 拉映像卡住，或提示字樣"
                       f"與本腳本偵測的「{PROMPT_MARK}」不再相符（sops 換版）。")
                code = _terminate_child(pid)
                break
            try:
                ready, _w, _x = select.select([master_fd], [], [], DRIVER_SELECT_SEC)
            except (OSError, ValueError):
                break
            if not ready:
                continue
            try:
                chunk = os.read(master_fd, 65536)
            except OSError:
                chunk = b""            # 子行程結束後 master 端讀出 EIO＝本平台的 EOF 形
            if not chunk:
                break
            chunks.append(chunk)
            hits = normalize_stream(
                b"".join(chunks).decode("utf-8", "replace")).count(PROMPT_MARK)
            while fed < hits:
                time.sleep(DRIVER_SETTLE_SEC)
                try:
                    os.write(master_fd, pw_buf)
                except OSError:
                    break              # 子行程已走＝沒人要餵了，交給 EOF 分支收尾
                fed += 1
    finally:
        for i in range(len(pw_buf)):                 # 就地零填（A7 唯一做得到的那層）
            pw_buf[i] = 0
        signal.signal(signal.SIGINT, prev_handler)
        with open(raw_path, "wb") as fh:             # 暫存流原樣落檔，交給後段正規化拆 key
            fh.write(b"".join(chunks))
        with contextlib.suppress(OSError):
            os.close(master_fd)
        if code is None and aborted:
            code = aborted[0]
            err = err or "已收到 Ctrl-C（SIGINT）——子行程已終結收屍、不留孤兒 docker run。"
        if code is None:
            # EOF 之後子行程通常已結束；仍以寬限內輪詢取代無界 waitpid，避免病態情形掛死。
            wait_until = time.monotonic() + DRIVER_GRACE_SEC
            while code is None and time.monotonic() < wait_until:
                code = _reap(pid, False)
                if code is None:
                    time.sleep(0.05)
            if code is None:
                code = _terminate_child(pid)
    return (1 if code is None else code), err


def _auto_decrypt(root, raw_path):
    """自動路徑外殼：取 passphrase（恰一次）→ driver → 回顯守衛
    → (退出碼, 訊息清單, 暫存流可否倒流)。

    ★passphrase 的生存期壓在本函式內：不回傳、不入 argv／環境變數／磁碟／log，
    用畢即刪參照。★getpass.getpass 自 /dev/tty 讀且不回顯；取不到 tty＝吵鬧失敗零副作用
    （呼叫端已先過 rev4:P4.2 tty 守衛，本層是第二道）。
    """
    try:
        passphrase = getpass.getpass("identity passphrase（不回顯；只需這一次）：")
    except Exception as ex:                          # noqa: BLE001（真因照印、不吞）
        return 1, [f"FAIL：無法自 /dev/tty 取得 passphrase（{ex}）。",
                   f"      處置＝在真實終端執行，或設 {MANUAL_ENV}=1 走逐次手打退路。"], False
    try:
        rc, err = run_sops_auto(root, raw_path, passphrase)
        with open(raw_path, encoding="utf-8", errors="replace") as fh:
            leaked = echo_hit(fh.read(), passphrase)
    finally:
        passphrase = None
        del passphrase
    if leaked:
        with open(raw_path, "wb"):
            pass                                     # 暫存整段清空（不倒流、不留檔）
        return 1, ["FAIL：解密輸出含 passphrase 字面——輸出整段已抑制、暫存已清空"
                   "（本訊息本身絕不含 passphrase）。",
                   "      成因＝pty 回顯未關、或 sops／wrapper 把輸入回吐；此形下任何倒流"
                   "都可能把 passphrase 印上 operator 畫面與 log。",
                   f"      處置＝設 {MANUAL_ENV}=1 走逐次手打退路，並回報本情形。"], False
    return rc, ([f"FAIL：{err}"] if err else []), True


def _announce(count, manual):
    """預告行（B-036：語意隨互動路徑分流；user 可見行為）→ 只印，不回傳。

    ★flush：stdout 非 tty（如 | tee）時 python 是 block-buffered、bash echo 則無條件即寫——
    tty 守衛只看 stdin，stdout 進管線時預告若卡在 buffer，operator 面對空白終端盲等
    passphrase（L-005 那類事故）；sops 起跑前必須先清空本流。
    """
    if manual:
        # 措辭用「每 recipient 一次」而非硬報數：wrapper 走目錄掛載回退分支時容器內可能不只
        # 一把 identity、實際次數更多，現算值僅為正常（單檔掛載）情形之下界。
        if count >= 1:
            print(f"即將解密（{MANUAL_ENV}=1 逐次手打）：sops 會**對每個 recipient 各索一次**"
                  f" identity passphrase（皆為同一個）——本密文有 {count} 個 recipient，"
                  f"故正常會問 {count} 次。")
        else:
            print(f"即將解密（{MANUAL_ENV}=1 逐次手打）：sops 會要求輸入 identity passphrase"
                  "（可能不只一次）。")
        print("★提示可能不顯示於畫面——**每一次**都要輸入後按 Enter；"
              "★任一次空答即以 passphrase can't be empty 整體失敗"
              "（判讀＝RUNBOOK §15.2 失敗訊息判讀）。", flush=True)
        return
    if count >= 1:
        print("即將解密：**只需輸入一次**——腳本會對每個 recipient 提示代餵"
              f"（本密文 {count} 個 recipient）。")
    else:
        print("即將解密：**只需輸入一次**——腳本會對每個 passphrase 提示代餵。")
    print("★次數由腳本邊讀邊數、不預測（L-005）；不需 passphrase 的鑰則零提示直通、"
          f"此時直接按 Enter 即可。★要回到逐次手打請設 {MANUAL_ENV}=1 重跑。", flush=True)


# ---------------------------------------------------------------------------
# 本體
# ---------------------------------------------------------------------------

def cmd_decrypt(root=None, env=None):
    """解密本體。root／env 皆為測試注入用哨兵——生產面走模組 ROOT 與本行程環境。

    ★env=None 是哨兵、不得寫成 `env or os.environ`：呼叫端明給空 dict＝「該環境確實沒設」，
    改讀本行程環境會讓「未設」與「已匯出為空」兩分支靜默改判（同共用庫註解）。
    """
    root = ROOT if root is None else root
    env = os.environ if env is None else env

    # ---- rev4:P4.2 tty 守衛 ----
    if not sys.stdin.isatty():
        print("FAIL：decrypt-secrets.py 需要互動終端（B′ passphrase 解密提示需 tty）。",
              file=sys.stderr)
        print("      命令替換／管線／CI 等非互動情境不支援；請在真實終端執行。", file=sys.stderr)
        return 1

    # ---- 必須自 repo 根執行（wrapper rev4:P1.5 同前提）----
    if not (os.path.isfile(".sops.yaml") and os.path.isfile(ENC_REL)):
        print("FAIL：請自 repo 根執行（當前目錄找不到 .sops.yaml 或 deploy/secrets.dev.enc.yaml）。",
              file=sys.stderr)
        return 1

    # ---- 落點解析三級口徑（rev4:019 rev4:P5.1／rev4:P5.2；共用庫＝三消費者單一實作面）----
    secrets_dir, err = resolve_secrets_dir(root, env)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1

    # ---- rev4:P4.4／rev4:P4.6 自建 0700 子目錄＋權限自證 ----
    os.umask(0o077)
    fails, warn = prepare_secrets_dir(secrets_dir)
    if warn:
        print(warn, file=sys.stderr)
    if fails:
        for line in fails:
            print(line, file=sys.stderr)
        return 1

    # 互動姿態分流（B-036）：只認 "1"，其他值（含未設、空字串、"0"、"true"）一律自動路徑。
    manual = env.get(MANUAL_ENV) == "1"

    tmp_dir, fails = prepare_tmp_dir(env)
    try:
        if fails:
            for line in fails:
                print(line, file=sys.stderr)
            return 1
        return _decrypt_into(root, secrets_dir, tmp_dir, manual)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _decrypt_into(root, secrets_dir, tmp_dir, manual):
    """暫存落點就緒後的後半段（預告→解密→拆 key→斷言→寫入）。

    manual=True＝逐次手打（RV5_DECRYPT_MANUAL=1 退路，＝B-036 之前的行為）；
    False＝自動應答 driver。★分流只在「預告行措辭」與「怎麼把 passphrase 送進 sops」兩點；
    其後每一段（拆 key／斷言／CR-LF 護欄／.new 判定／寫入／redact）兩路完全共用——互動姿態
    換了，落點口徑與各道護欄一個字都不動。
    """
    raw_path = os.path.join(tmp_dir, "raw.out")

    with open(os.path.join(root, ENC_REL), encoding="utf-8", errors="replace") as fh:
        count = recipient_count(fh.read())
    _announce(count, manual)

    if manual:
        rc, fails, raw_usable = run_sops(root, raw_path), [], True
    else:
        rc, fails, raw_usable = _auto_decrypt(root, raw_path)
    for line in fails:
        print(line, file=sys.stderr)
    if not raw_usable:
        return 1                       # 回顯守衛／取不到 tty：暫存整段不倒流、零寫入
    if fails and rc == 0:
        rc = 1                         # driver 層異常但子行程回 0＝仍屬失敗，不得放行

    with open(raw_path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    if rc != 0:
        print(f"FAIL：sops 解密失敗（rc={rc}）——sops 輸出如下（資料行已濾除）：",
              file=sys.stderr)
        kept, redacted = redact_stream(raw)
        for line in kept:
            print(line, file=sys.stderr)
        if redacted:
            print(f"      （另有 {redacted} 行疑似機密資料已濾除、不顯示）", file=sys.stderr)
        return rc

    # ---- 本地拆 key（不重呼容器）----
    payload, err = extract_payload(normalize_stream(raw))
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1
    values, bad = collect_values(payload)

    # ---- rev4:P4.3 key 數與名稱斷言（不符＝零寫入＋非零退出＋指名）----
    missing, extra = assert_keys(values)
    newlines = newline_hits(values)
    if missing or extra or bad or newlines:
        if missing:
            print(f"FAIL：解密結果缺 key（或值為空）：{' '.join(missing)}", file=sys.stderr)
        if extra:
            print(f"FAIL：解密結果含非預期 key：{' '.join(extra)}", file=sys.stderr)
        if bad:
            print(f"FAIL：下列 key 的值不是純量：{' '.join(bad)}", file=sys.stderr)
        if newlines:
            print("FAIL：下列 key 的值含換行字元（CR／LF），落點檔形＝一值一檔零換行："
                  f"{' '.join(newlines)}", file=sys.stderr)
            print("      成因＝加密檔內該值是多行（YAML 區塊純量）或含 CR。", file=sys.stderr)
            print("      後果＝照寫後 deploy/preflight-secrets.py 的 CR／LF 護欄"
                  "（rev4:P4.1／rev4:P5.7 寫檔形不變式）會判內容劣化擋 up，而它指的處置"
                  "是「重跑 decrypt」＝再產同一支壞檔。", file=sys.stderr)
            print("      處置＝./deploy/sops.sh edit deploy/secrets.dev.enc.yaml "
                  "把該值改成單行後重跑。", file=sys.stderr)
        print("FAIL：key 斷言不符＝零寫入退出。修復加密檔後重跑；絕不落到 generate 造亂數路徑。",
              file=sys.stderr)
        return 1

    # ---- 既有 .txt.new 偵測（rev4:019 rev4:U3 遺留 advisory 三）：值重新一致後，先前 DIFF
    #      產下的舊 .new 不會再被觸碰＝長存落點；此處只提醒、★不自動刪（避免吃掉人工待決資料）
    stale = find_stale_new(secrets_dir)
    if stale:
        print(f"WARN：落點已有先前遺留的待決 .txt.new：{' '.join(stale)}"
              "——請人工比對處置（本腳本不自動刪）。", file=sys.stderr)

    # ---- 寫入（斷言全過後才進入；rev4:P4.1／rev4:P4.5／rev4:P4.7）----
    lines, new_saved = write_secrets(secrets_dir, values)
    for line in lines:
        print(line)

    print("")
    if new_saved:
        print("WARN：下列機密現值與加密檔不一致、已另存 .txt.new（原檔未覆寫）："
              f"{' '.join(new_saved)}", file=sys.stderr)
        print("      人工比對後：採加密檔值＝mv .new 蓋回；保留現值＝刪 .new 並依 RUNBOOK "
              "輪替程序回寫加密檔。", file=sys.stderr)
    print(f"完成：{secrets_dir} 之 {len(EXPECTED_KEYS)} 支 key 檔已就緒"
          "（composite 另跑 ./deploy/generate-secrets.sh 重組）。")
    return 0


# ---------------------------------------------------------------------------
# 自測（test 子命令）：離線、stdlib-only、不需 docker，一律隔離暫存目錄
# ---------------------------------------------------------------------------

# ★合成 JSON 樣本一律執行期串接構造（防本檔自命中機密樣式掃描；同 tools/secret-value-guard.py
#   與 deploy/preflight-secrets.py 慣例——U2 已實證字面寫死會被 pre-commit 硬擋）。
def _payload_json(values, indent="\t", eol="\n"):
    body = ("," + eol + indent).join(
        json.dumps(k) + ": " + json.dumps(v) for k, v in values.items())
    return "{" + eol + indent + body + eol + "}" + eol


def _plain_values():
    return {k: "FAKE-" + k + "-value" for k in EXPECTED_KEYS}


# 假 passphrase（同上，執行期串接）與樁要印的提示行——提示字面刻意由 PROMPT_MARK 接出
# 真實尾巴，讓「偵測樣式改短／改長」與「樁印的東西」保持同一個來源。
_TEST_PASSPHRASE = "FAKE-" + "b036-" + "passphrase"
_STUB_PROMPT = PROMPT_MARK + " for identity: "


def _stub_source(body):
    """假 sops 樁原始碼（落 <root>/deploy/sops.sh＝driver 實際叫用的相對路徑）。"""
    return "\n".join(["#!/usr/bin/env python3",
                      "# -*- coding: utf-8 -*-",
                      "import json, os, select, sys, time"] + body) + "\n"


def _stub_prompt_loop(root, prompts, echo_back=False, timed=False):
    """N 次提示 →（可選：把收到的東西回吐）→ 合成 JSON；收到什麼只記次數。

    timed=True＝提示後以 0.6 秒為限等 stdin（手動路徑沒有代餵者，無界 readline 會掛死
    測試；本形讓「沒人餵」成為有界的可觀測結果）。
    ★收完 passphrase 後樁補印 `ESC[2K` 加換行——這是**實測過的真流形**（同 TestExtractPayload
    的 noisy 案，出自 sops／age 讀完密語後的清行），不是為了好過。少了它，JSON 的左大括號
    會黏在提示行尾、extract_payload 的行首判準吃不到——樁必須把這個真條件也帶進來。
    """
    return _stub_source([
        "MARK = " + json.dumps(_STUB_PROMPT),
        "PW = " + json.dumps(_TEST_PASSPHRASE),
        "REC = " + json.dumps(os.path.join(root, "stub-record.json")),
        "N, ECHO, TIMED = " + f"{prompts}, {bool(echo_back)!r}, {bool(timed)!r}",
        "got = []",
        "for _ in range(N):",
        "    sys.stdout.write(MARK)",
        "    sys.stdout.flush()",
        "    if TIMED and not select.select([sys.stdin], [], [], 0.6)[0]:",
        "        got.append('')",
        "    else:",
        "        got.append(sys.stdin.readline().rstrip('\\r\\n'))",
        "    sys.stdout.write('\\x1b[2K\\n')",
        "    if ECHO:",
        "        sys.stdout.write('debug echo: ' + got[-1] + '\\n')",
        "    sys.stdout.flush()",
        "with open(REC, 'w') as _fh:",
        "    json.dump({'prompts': N, 'match': sum(1 for g in got if g == PW),",
        "               'nonempty': sum(1 for g in got if g)}, _fh)",
        "sys.stdout.write(" + json.dumps(_payload_json(_plain_values())) + ")",
        "sys.stdout.flush()",
    ])


def _stub_hang(root):
    """吐一行雜訊後長睡不退、且**永不印提示**的樁（逾時與孤兒收拾用）。"""
    return _stub_source([
        "with open(" + json.dumps(os.path.join(root, "stub.pid")) + ", 'w') as _fh:",
        "    _fh.write(str(os.getpid()))",
        "sys.stdout.write('stub-alive-no-prompt\\n')",
        "sys.stdout.flush()",
        "time.sleep(600)",
    ])


class TestRosterPinned(unittest.TestCase):
    """★名冊字面釘死：以被測常數迭代出期望值＝套套邏輯（名冊縮水時斷言跟著縮水、全綠
    存活）。10 支少一支＝該支靜默不寫出、preflight 到 up 前才炸，故字面逐一列出。"""

    def test_expected_keys_pinned(self):
        self.assertEqual(EXPECTED_KEYS, (
            "postgres_password", "redis_password", "jwt_secret", "refresh_token_secret",
            "captcha_secret", "reaper_password", "grafana_admin_password",
            "smtp_password", "email_verify_secret", "alert_webhook_url"))
        self.assertEqual(len(EXPECTED_KEYS), 10)

    def test_root_is_anchored_on_file_not_cwd(self):
        """★落點錨定基準＝由 __file__ 推得的 repo 根，非 CWD（bash 版 _ANCHOR_ROOT 同義）：
        本檔雖已斷言 CWD＝repo 根，但拿 CWD 當基準等於把正確性續押在該斷言上。"""
        self.assertEqual(ROOT, os.path.dirname(HERE))
        self.assertEqual(os.path.basename(HERE), "deploy")
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        # ★樣本執行期串接構造：字面寫死會讓本斷言自己命中自己
        self.assertNotIn("get" + "cwd", src, msg="落點錨定改吃 CWD＝呼叫端一漂落點就變")

    def test_non_plain_scalar_assertion_is_gone(self):
        """★ADR 0010 轉換批①核心：非裸量純量斷言整段刪除（舊檔 :195-220）。字面殘留＝
        改法沒真的落地（真 JSON 解析後該斷言只會誤殺人工填值機密）。
        ★刪的是「YAML token 首字元判形」那道；另立的 CR／LF 窄護欄（newline_hits）判準
        不同、放行面不同，見 TestNewlineGuard。"""
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        # ★樣本執行期串接構造：字面寫死會讓本斷言自己命中自己（同上方 CWD 案）
        self.assertNotIn("NON" + "PLAIN", src)
        self.assertIn("--output-type", src)


class TestNormalizeStream(unittest.TestCase):
    """pty 單流正規化（A3 逐字保留的外部條件複雜度之一）。"""

    def test_cr_becomes_line_break(self):
        self.assertEqual(normalize_stream("a\r\nb\rc"), "a\n\nb\nc")

    def test_ansi_csi_stripped(self):
        self.assertEqual(normalize_stream("\x1b[2Kabc\x1b[0m"), "abc")

    def test_clean_stream_is_identity(self):
        """非 tty 乾淨流＝恆等變換（正規化無條件套用、不分岔兩個 parser）。"""
        text = _payload_json(_plain_values())
        self.assertEqual(normalize_stream(text), text)


class TestExtractPayload(unittest.TestCase):
    """JSON 拆 key：乾淨流／pty 併流／雜訊在前／壞流。"""

    def test_clean_json(self):
        vals = _plain_values()
        data, err = extract_payload(normalize_stream(_payload_json(vals)))
        self.assertIsNone(err)
        self.assertEqual(data, vals)

    def test_crlf_stream_from_container_pty(self):
        """容器 pty 把換行改 CRLF（wrapper rev4:P1.2 註）——正規化後照樣 parse。"""
        vals = _plain_values()
        data, err = extract_payload(normalize_stream(_payload_json(vals, eol="\r\n")))
        self.assertIsNone(err)
        self.assertEqual(data, vals)

    def test_passphrase_prompt_lines_before_data_are_skipped(self):
        """★提示行與資料同流（單一 pty）：前置雜訊必須濾掉才 parse，否則整段解析失敗＝
        真 tty 情境全滅（自動化測不到那條路，故此案是它唯一的機器守衛）。"""
        vals = _plain_values()
        noisy = ("Enter passphrase for identity: \x1b[2K\n"
                 "Enter passphrase for identity: \n" + _payload_json(vals))
        data, err = extract_payload(normalize_stream(noisy))
        self.assertIsNone(err)
        self.assertEqual(data, vals)

    def test_trailing_control_residue_tolerated(self):
        """raw_decode 而非 loads：JSON 之後的殘餘不該被當成解析失敗。"""
        data, err = extract_payload(normalize_stream(_payload_json(_plain_values()) + "\n\n"))
        self.assertIsNone(err)
        self.assertEqual(len(data), 10)

    def test_garbage_is_loud_failure(self):
        data, err = extract_payload("not json at all\n")
        self.assertIsNone(data)
        self.assertIn("無法解析為 JSON", err)

    def test_top_level_array_is_loud_failure(self):
        data, err = extract_payload('["a"]')
        self.assertIsNone(data)
        self.assertIn("頂層不是物件", err)


class TestRestoreValue(unittest.TestCase):
    """★A2 還原面（本刀刪斷言的正當性證據）：舊 bash 版對這些值一律 FAIL 指名「無法還原
    原值」（首字元落 `" ' | >` 四者）或逐字寫入含引號的壞值；真 JSON 解析後逐位元組正確。

    ★本層只驗**還原**：區塊純量（含換行）在此同樣逐位元組還原成功，它之所以仍不進落點是
    落點檔形載不動（newline_hits／TestNewlineGuard），兩件事分層、不要混為一談。"""

    def test_quoted_forms_restore_byte_exact(self):
        cases = {
            "含冒號空白": "FAKE-pg: colon-space",
            "含井號": "FAKE-redis #hash-inside",
            "前後帶空白": " FAKE-jwt-leading-and-trailing ",
            "含雙引號": 'FAKE-refresh-with-"double-quote"',
            "含單引號": "FAKE-smtp-single'quote",
            "星號起首": "*FAKE-reaper-star-start",
            "at 起首": "@FAKE-emailverify-at-start",
            "區塊純量（含換行）": "FAKE-captcha-line-one\nFAKE-captcha-line-two",
        }
        for label, value in cases.items():
            with self.subTest(label=label):
                text = _payload_json({"jwt_secret": value})
                data, err = extract_payload(normalize_stream(text))
                self.assertIsNone(err)
                got, err2 = restore_value(data["jwt_secret"])
                self.assertIsNone(err2)
                self.assertEqual(got, value)
                self.assertEqual(got.encode("utf-8"), value.encode("utf-8"))

    def test_old_bash_predicate_would_have_rejected_these(self):
        """★對照案：舊版判準（值首字元落 `" ' | >`）套在 sops 的 YAML 輸出上會把這些值
        整批打成 FAIL——證明本刀刪的是「解析力不足的補丁」而非一道真防線。
        （判準逐字重建於此，僅供對照、不參與生產路徑。）"""
        yaml_tokens = ["'FAKE-pg: colon-space'", "'FAKE-redis #hash-inside'",
                       "' FAKE-jwt-leading-and-trailing '", "|-"]
        self.assertTrue(all(tok[:1] in ('"', "'", "|", ">") for tok in yaml_tokens))

    def test_non_string_scalars_render_as_json_literals(self):
        """sops 於密文內記型別、解密即還原；bash 版逐字寫入 `true`／`123`／`null`，同形。"""
        self.assertEqual(restore_value(True), ("true", None))
        self.assertEqual(restore_value(123), ("123", None))
        self.assertEqual(restore_value(None), ("null", None))

    def test_containers_are_loud_failure(self):
        for raw in ({"a": 1}, ["a"]):
            val, err = restore_value(raw)
            self.assertIsNone(val)
            self.assertIn("JSON 容器", err)


class TestAssertKeys(unittest.TestCase):
    """rev4:P4.3 key 數與名稱斷言。"""

    def test_full_roster_passes(self):
        self.assertEqual(assert_keys(_plain_values()), ([], []))

    def test_missing_key_named(self):
        vals = _plain_values()
        del vals["email_verify_secret"]
        self.assertEqual(assert_keys(vals), (["email_verify_secret"], []))

    def test_empty_value_counts_as_missing(self):
        """★沿 bash 版 `[ -z ]` 判定：空機密無合法用途，值為空即缺。
        （舊版此案其實被非裸量純量斷言先攔下——sops 對空值吐 2 字元的 `\"\"`；
        斷言刪除後由本判定接手，指名的真因反而更準。）"""
        vals = _plain_values()
        vals["jwt_secret"] = ""
        self.assertEqual(assert_keys(vals), (["jwt_secret"], []))

    def test_extra_key_named(self):
        vals = _plain_values()
        vals["unexpected_extra_key"] = "x"
        self.assertEqual(assert_keys(vals), ([], ["unexpected_extra_key"]))

    def test_collect_values_reports_bad_types(self):
        payload = dict(_plain_values())
        payload["jwt_secret"] = {"nested": 1}
        values, bad = collect_values(payload)
        self.assertNotIn("jwt_secret", values)
        self.assertEqual(len(bad), 1)
        self.assertIn("jwt_secret", bad[0])


class TestRedactStream(unittest.TestCase):
    """失敗路徑：先濾疑似機密行才把暫存流倒給 operator。"""

    def test_json_body_fully_redacted_diagnostics_kept(self):
        text = "sops error: MAC mismatch\n" + _payload_json(_plain_values())
        kept, redacted = redact_stream(text)
        self.assertEqual(kept, ["sops error: MAC mismatch"])
        self.assertGreaterEqual(redacted, 10)
        self.assertFalse(any("FAKE-" in line for line in kept))

    def test_key_named_line_redacted_even_without_json_start(self):
        """輸出被截斷、沒有行首左大括號時的兜底（行內出現任一已知 key 名即濾）。"""
        kept, redacted = redact_stream('  "jwt_secret": "FAKE-leak"\ndiag line\n')
        self.assertEqual(kept, ["diag line"])
        self.assertEqual(redacted, 1)

    def test_blank_residue_lines_not_counted(self):
        """CRLF 轉行界留下的空殘行不計數、也不解除資料區。"""
        kept, redacted = redact_stream("diag\r\n\r\n")
        self.assertEqual((kept, redacted), (["diag"], 0))


class TestRecipientCount(unittest.TestCase):
    """預告行的次數＝自密文現算（L-005：寫死「恰 1 次」是加人日誤導 operator 空答的來源）。"""

    def test_counts_recipient_lines(self):
        # 形制逐字取自真密文（`- enc: |` 區塊之後、同縮排的 recipient 行）
        enc = ("sops:\n    age:\n        - enc: |\n            BLOB\n"
               "          recipient: age1aaa\n        - enc: |\n            BLOB\n"
               "          recipient: age1bbb\n")
        self.assertEqual(recipient_count(enc), 2)

    def test_zero_when_absent(self):
        self.assertEqual(recipient_count("sops:\n    kms: []\n"), 0)


class TestWriteSecrets(unittest.TestCase):
    """寫入面（隔離暫存目錄；rev4:P4.1／rev4:P4.5／rev4:P4.7）。"""

    def _dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def test_fresh_write_has_no_trailing_newline_and_mode_644(self):
        d = self._dir()
        vals = _plain_values()
        lines, new_saved = write_secrets(d, vals)
        self.assertEqual(new_saved, [])
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(line.endswith("WRITTEN") for line in lines))
        for key in EXPECTED_KEYS:
            with open(os.path.join(d, key + ".txt"), "rb") as fh:
                data = fh.read()
            self.assertEqual(data, vals[key].encode("utf-8"))
            self.assertNotIn(b"\n", data)
            self.assertNotIn(b"\r", data)
            if _sandbox_holds_modes(d):
                self.assertEqual(_mode_of(os.path.join(d, key + ".txt")), "644")

    def test_identical_value_is_idempotent_rewrite(self):
        d = self._dir()
        vals = _plain_values()
        write_secrets(d, vals)
        lines, new_saved = write_secrets(d, vals)
        self.assertEqual(new_saved, [])
        self.assertTrue(all("WRITTEN" in line for line in lines))

    def test_differing_value_saves_new_without_overwriting(self):
        """rev4:P4.5：decrypt 不得成為靜默覆寫路徑——原檔一個 byte 都不動。"""
        d = self._dir()
        base = _plain_values()
        write_secrets(d, base)
        rotated = dict(base, jwt_secret="FAKE-jwt-rotated")
        lines, new_saved = write_secrets(d, rotated)
        self.assertEqual(new_saved, ["jwt_secret"])
        with open(os.path.join(d, "jwt_secret.txt"), "rb") as fh:
            self.assertEqual(fh.read(), base["jwt_secret"].encode("utf-8"))
        with open(os.path.join(d, "jwt_secret.txt.new"), "rb") as fh:
            self.assertEqual(fh.read(), b"FAKE-jwt-rotated")
        self.assertTrue(any("DIFF→已另存" in line for line in lines))
        if _sandbox_holds_modes(d):
            self.assertEqual(_mode_of(os.path.join(d, "jwt_secret.txt.new")), "644")

    def test_plan_write_is_byte_exact(self):
        """★逐位元組比對：字串比較會剝尾端換行、對「檔尾多一個 LF」結構性失明。"""
        self.assertEqual(plan_write(None, b"v"), "WRITTEN")
        self.assertEqual(plan_write(b"v", b"v"), "WRITTEN")
        self.assertEqual(plan_write(b"v\n", b"v"), "DIFF")

    def test_quoted_form_values_round_trip_to_disk(self):
        """★A2 端到端（離線段）：引號形值自 JSON 還原後寫檔，逐位元組等於原值。

        ★選值一律**不含換行**：含換行的值根本進不到寫入面（newline_hits 先零寫入退出），
        在此塞一個多行值等於把「decrypt 寫出 preflight 會拒收的檔」釘成期望行為。
        """
        d = self._dir()
        vals = dict(_plain_values(),
                    postgres_password="FAKE-pg: colon-space",
                    captcha_secret="FAKE-captcha #hash-and-'quote'",
                    jwt_secret=" FAKE-jwt-leading-and-trailing ")
        payload, err = extract_payload(normalize_stream(_payload_json(vals)))
        self.assertIsNone(err)
        restored, bad = collect_values(payload)
        self.assertEqual(bad, [])
        self.assertEqual(newline_hits(restored), [])
        write_secrets(d, restored)
        for key in ("postgres_password", "captcha_secret", "jwt_secret"):
            with open(os.path.join(d, key + ".txt"), "rb") as fh:
                self.assertEqual(fh.read(), vals[key].encode("utf-8"))


class TestNewlineGuard(unittest.TestCase):
    """還原後值的 CR／LF 窄護欄：擋住落點載不動的那一類，其餘引號形全放行。

    ★本護欄的存在理由是**跨檔一致**：decrypt 宣告「已就緒 rc=0」的產物，緊接的
    deploy/preflight-secrets.py 不得判它劣化。兩支判準一漂開，管線就回到自相矛盾。
    """

    def test_plain_roster_has_no_hits(self):
        self.assertEqual(newline_hits(_plain_values()), [])

    def test_quoted_forms_without_newline_all_pass(self):
        """★ADR 0010 的收益面不得被本護欄吃掉：舊斷言誤殺的五形一律放行。"""
        vals = dict(_plain_values(),
                    postgres_password="FAKE-pg: colon-space",
                    redis_password="FAKE-redis #hash-inside",
                    jwt_secret=" FAKE-jwt-leading-and-trailing ",
                    refresh_token_secret='FAKE-refresh-with-"double-quote"',
                    smtp_password="FAKE-smtp-single'quote",
                    reaper_password="*FAKE-reaper-star-start",
                    email_verify_secret="@FAKE-emailverify-at-start")
        self.assertEqual(newline_hits(vals), [])

    def test_lf_and_cr_values_are_named_in_roster_order(self):
        vals = dict(_plain_values(),
                    jwt_secret="FAKE-jwt-with-cr\rtail",
                    captcha_secret="FAKE-captcha-line-one\nFAKE-captcha-line-two")
        self.assertEqual(newline_hits(vals), ["jwt_secret", "captcha_secret"])

    def test_trailing_newline_value_is_named(self):
        """尾端多一個 LF 同樣命中——preflight 的 LF 護欄正是為此形而立（該形會讓
        composite 一致性檢查失明、容器拿到與 composite 不符的值）。"""
        self.assertEqual(
            newline_hits(dict(_plain_values(), redis_password="FAKE-redis-tail-lf\n")),
            ["redis_password"])

    def test_predicate_matches_preflight_content_guard(self):
        """★跨檔一致性機器守衛：同一批探針值，本護欄的命中與否必與
        deploy/preflight-secrets.py 的 content_hits 完全一致（CR 與 LF 在彼處走互斥
        分流，故以「有無命中」而非分類比對）。任一邊日後放寬／收緊即紅。"""
        spec = importlib.util.spec_from_file_location(
            "preflight_secrets_probe", os.path.join(HERE, "preflight-secrets.py"))
        preflight = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preflight)
        probes = {
            "乾淨裸量": "FAKE-clean-value",
            "冒號空白": "FAKE-a: b",
            "井號": "FAKE-a #b",
            "前後空白": " FAKE-a ",
            "雙引號": 'FAKE-"a"',
            "單引號": "FAKE-'a'",
            "星號起首": "*FAKE-a",
            "內嵌 LF": "FAKE-a\nFAKE-b",
            "尾端 LF": "FAKE-a\n",
            "內嵌 CR": "FAKE-a\rFAKE-b",
            "CRLF": "FAKE-a\r\nFAKE-b",
        }
        for label, value in probes.items():
            with self.subTest(label=label):
                blobs = {n: b"FAKE-clean-value" for n in preflight.REQUIRED}
                blobs["jwt_secret"] = value.encode("utf-8")
                cr, nl = preflight.content_hits(blobs)
                self.assertEqual(bool(cr or nl), bool(newline_hits({"jwt_secret": value})))


class TestFindStaleNew(unittest.TestCase):
    """既有 .txt.new 提醒（rev4:019 rev4:U3 遺留 advisory 三）：只提醒、不自動刪。"""

    def _dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def _touch(self, d, *names):
        for name in names:
            with open(os.path.join(d, name), "w"):
                pass

    def test_lists_sorted_basenames_only(self):
        d = self._dir()
        self._touch(d, "redis_password.txt.new", "jwt_secret.txt.new", "jwt_secret.txt")
        self.assertEqual(find_stale_new(d), ["jwt_secret.txt.new", "redis_password.txt.new"])

    def test_glob_metachars_in_dir_do_not_hide_the_warning(self):
        """★落點含 glob 元字元時仍須找到：SECRETS_DIR 走環境變數那條沒有字元白名單
        （白名單只套 .env 那條），而 glob.glob 會把整條路徑當樣式、回空集合＝這道人工待決
        提醒靜默消失；bash 版目錄段有引號、不受影響。"""
        d = os.path.join(self._dir(), "we[i]rd*dir?x")
        os.makedirs(d)
        self._touch(d, "redis_password.txt.new")
        self.assertEqual(find_stale_new(d), ["redis_password.txt.new"])

    def test_missing_dir_is_empty(self):
        self.assertEqual(find_stale_new(os.path.join(self._dir(), "nope")), [])

    def test_leading_dot_names_skipped_like_bash_glob(self):
        d = self._dir()
        self._touch(d, ".hidden.txt.new")
        self.assertEqual(find_stale_new(d), [])


def _sandbox_holds_modes(d):
    """暫存沙盒能否承載 644（drvfs 上 chmod 結構性 no-op、mode 恆讀 777）。

    ★探針兩端一律用**字面** 0o644／"644"、絕不取受測常數 FILE_MODE：拿 FILE_MODE 設探針
    等於讓「沙盒能力偵測」與「斷言標的」同源——FILE_MODE 一旦被改壞（如 0o600），探針讀回
    600 ≠ "644" 使本函式回 False，644 斷言整批靜默 skip、rc 仍 0，落點檔悄悄變成 600
    （違反 rev4:P4.7，且只在開 obs／metrics 軌時才炸：grafana 472／postgres-exporter 65534／
    redis-exporter 59000 全部 Permission denied）。
    """
    probe = os.path.join(d, ".mode-probe")
    with open(probe, "w"):
        pass
    os.chmod(probe, 0o644)
    held = _mode_of(probe) == "644"
    os.remove(probe)
    return held


_DRVFS_SKIP = ("暫存沙盒在 drvfs（chmod 結構性 no-op、mode 恆讀 777）——權限面判定改由 "
               "mock 注入的兩支 mode 不符案覆蓋；把 TMPDIR 指到 ext4 即可跑本案")


class _StubStdin:
    """sys.stdin 替身：cmd_decrypt 的 rev4:P4.2 守衛只用到 isatty。

    ★有了替身，tty 兩分支都成為**確定性**案——原本「stdin 恰是 tty 就 skipTest」的寫法
    在互動終端下跑 test 會靜默放掉守衛案（沙盒探針同一個病）。
    """

    def __init__(self, tty):
        self._tty = tty

    def isatty(self):
        return self._tty


class TestPrepareDirs(unittest.TestCase):
    """兩支安全自證函式（隔離暫存；絕不觸真落點、絕不觸真密文）。

    ★這兩支是本刀的安全核心、必須有常駐回歸網：prepare_tmp_dir 條件寫壞＝10 支完整明文
    落到 9p（chmod no-op＝實效 777、Windows 側可見，rev4:FR-021／rev4:SC-005）；
    prepare_secrets_dir 條件寫壞＝落點權限失守（rev4:P4.4／rev4:P4.6）。
    ★mode 不符兩分支以 mock 注入 _mode_of／fs_type：真 no-op fs 造不出來，靠沙盒碰運氣＝
    在 ext4 上永遠測不到那兩條。
    """

    def _dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    # ---- prepare_secrets_dir ----

    def test_secrets_dir_is_created_and_self_certified_700(self):
        parent = self._dir()
        sd = os.path.join(parent, "secrets")
        fails, warn = prepare_secrets_dir(sd)
        self.assertTrue(os.path.isdir(sd))
        if not _sandbox_holds_modes(parent):
            self.skipTest(_DRVFS_SKIP)
        self.assertEqual((fails, warn), ([], None))
        self.assertEqual(_mode_of(sd), "700")   # 字面、不取 DIR_MODE_OK（套套邏輯）

    def test_secrets_dir_on_v9fs_warns_but_passes(self):
        """drvfs 落點：chmod 結構性 no-op＝現行已知限制（rev4:US3 遷移消滅），只 WARN 不擋。"""
        sd = os.path.join(self._dir(), "secrets")
        with unittest.mock.patch(f"{__name__}._mode_of", return_value="777"), \
             unittest.mock.patch(f"{__name__}.fs_type", return_value="v9fs"):
            fails, warn = prepare_secrets_dir(sd)
        self.assertEqual(fails, [])
        self.assertIn("no-op", warn)
        self.assertIn("777", warn)

    def test_secrets_dir_mode_mismatch_off_v9fs_is_loud_failure(self):
        """非 no-op fs 上 chmod 700 沒生效＝真異常（權限失守），fail-loud 帶實際 mode 與 fs。"""
        sd = os.path.join(self._dir(), "secrets")
        with unittest.mock.patch(f"{__name__}._mode_of", return_value="755"), \
             unittest.mock.patch(f"{__name__}.fs_type", return_value="ext4"):
            fails, warn = prepare_secrets_dir(sd)
        self.assertIsNone(warn)
        self.assertEqual(len(fails), 1)
        self.assertIn("chmod 700 未生效", fails[0])
        self.assertIn("755", fails[0])

    # ---- prepare_tmp_dir ----

    def test_tmp_dir_lands_under_xdg_cache_and_is_700(self):
        cache = self._dir()
        tmp_dir, fails = prepare_tmp_dir({"XDG_CACHE_HOME": cache})
        self.addCleanup(shutil.rmtree, tmp_dir, True)
        # 字面釘死路徑形（不取 CACHE_LEAF／TMP_PREFIX，否則常數改壞時斷言跟著改）
        self.assertEqual(os.path.dirname(tmp_dir), os.path.join(cache, "fork260509-rev5"))
        self.assertTrue(os.path.basename(tmp_dir).startswith("decrypt."))
        if not _sandbox_holds_modes(cache):
            self.skipTest(_DRVFS_SKIP)
        self.assertEqual(fails, [])
        self.assertEqual(_mode_of(tmp_dir), "700")

    def test_tmp_dir_falls_back_to_home_cache(self):
        """$XDG_CACHE_HOME 未設 → $HOME/.cache（同 bash 版 `${XDG_CACHE_HOME:-$HOME/.cache}`）。
        ★expanduser 以 mock 改道隔離暫存：本案絕不在真 $HOME 留痕。"""
        home = self._dir()
        with unittest.mock.patch("os.path.expanduser", return_value=home):
            tmp_dir, _fails = prepare_tmp_dir({})
        self.addCleanup(shutil.rmtree, tmp_dir, True)
        self.assertEqual(os.path.dirname(tmp_dir),
                         os.path.join(home, ".cache", "fork260509-rev5"))

    def test_tmp_dir_on_v9fs_is_loud_failure(self):
        """★暫存明文落點落在 9p＝10 支完整明文以實效 777、Windows 側可見的形式躺著——
        必須 fail-loud 並指路 XDG_CACHE_HOME，絕不降級續跑（rev4:FR-021／rev4:SC-005）。"""
        cache = self._dir()
        with unittest.mock.patch(f"{__name__}.fs_type", return_value="v9fs"):
            tmp_dir, fails = prepare_tmp_dir({"XDG_CACHE_HOME": cache})
        self.addCleanup(shutil.rmtree, tmp_dir, True)
        self.assertTrue(fails)
        self.assertIn("不安全", fails[0])
        self.assertIn("v9fs", fails[0])
        self.assertTrue(any("XDG_CACHE_HOME" in line for line in fails))

    def test_tmp_dir_mode_mismatch_is_loud_failure(self):
        cache = self._dir()
        with unittest.mock.patch(f"{__name__}.fs_type", return_value="ext4"), \
             unittest.mock.patch(f"{__name__}._mode_of", return_value="755"):
            tmp_dir, fails = prepare_tmp_dir({"XDG_CACHE_HOME": cache})
        self.addCleanup(shutil.rmtree, tmp_dir, True)
        self.assertTrue(fails)
        self.assertIn("mode=755", fails[0])


class TestGuards(unittest.TestCase):
    """前段守衛（不需 docker 的那幾條）：tty → repo 根 → 落點解析 → 暫存落點，逐條驗
    「零寫入＋rc 1」。★一律明給 root／env／SECRETS_DIR，絕不落到真落點、絕不觸真密文。"""

    def _dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def _fake_repo(self):
        """假 repo 根：只需 repo 根守衛看的那兩個檔存在（內容不參與本層判定）。"""
        d = self._dir()
        os.makedirs(os.path.join(d, "deploy"))
        for rel in (".sops.yaml", ENC_REL):
            with open(os.path.join(d, rel), "w", encoding="utf-8") as fh:
                fh.write("# fixture\n")
        return d

    def _run(self, root, env, tty=True, cwd=None):
        """cmd_decrypt 一次執行 → (rc, stdout, stderr)。

        ★repo 根守衛看的是 **CWD**（同 bash 版），故情境以 chdir 造；返回原處走
        **開著的目錄 fd＋fchdir**（Linux 前提，同 fs_type 一致）——不用路徑字串回頭，
        本檔的錨定紀律案正是以「原始碼不得出現取 CWD 的呼叫」為判準。
        ★umask 亦還原：cmd_decrypt 會設 0o077，測試不該把它漏給後續案。
        """
        out, err = io.StringIO(), io.StringIO()
        prev_umask = os.umask(0o022)
        os.umask(prev_umask)
        prev_cwd_fd = os.open(".", os.O_RDONLY)
        try:
            if cwd:
                os.chdir(cwd)
            with unittest.mock.patch("sys.stdin", _StubStdin(tty)), \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = cmd_decrypt(root=root, env=env)
        finally:
            os.fchdir(prev_cwd_fd)
            os.close(prev_cwd_fd)
            os.umask(prev_umask)
        return rc, out.getvalue(), err.getvalue()

    def test_non_tty_is_refused(self):
        """rev4:P4.2 tty 守衛：非互動吵鬧失敗、不 hang、不寫壞檔。"""
        rc, out, err = self._run(root=self._dir(), env={}, tty=False)
        self.assertEqual(rc, 1)
        self.assertIn("需要互動終端", err)
        self.assertEqual(out, "")

    def test_non_repo_root_is_refused(self):
        """CWD 非 repo 根＝零寫入退出（wrapper rev4:P1.5 同前提）。"""
        d = self._dir()
        rc, out, err = self._run(root=d, env={}, cwd=d)
        self.assertEqual(rc, 1)
        self.assertIn("請自 repo 根執行", err)
        self.assertEqual(out, "")

    def test_resolve_secrets_dir_error_maps_to_rc1(self):
        """落點解析錯誤 → rc 1、走 stderr、stdout 全空（共用庫的各分支判定另有 preflight／
        secret-value-guard 的案；此處驗的是**映射**：解析一錯就零寫入退出，不靜默回退）。"""
        d = self._fake_repo()
        rc, out, err = self._run(root=d, env={"SECRETS_DIR": ""}, cwd=d)
        self.assertEqual(rc, 1)
        self.assertIn("已匯出為空字串", err)
        self.assertEqual(out, "")

    def test_unsafe_tmp_dir_blocks_before_any_write(self):
        """★端到端：暫存落點不安全時在**呼叫 sops 之前**退出，落點一支 .txt 都不留。"""
        d = self._fake_repo()
        sd, cache = os.path.join(d, "sec"), self._dir()
        with unittest.mock.patch(f"{__name__}.fs_type", return_value="v9fs"):
            rc, _out, err = self._run(root=d, cwd=d,
                                      env={"SECRETS_DIR": sd, "XDG_CACHE_HOME": cache})
        self.assertEqual(rc, 1)
        self.assertIn("暫存明文落點", err)
        self.assertEqual([n for n in os.listdir(sd) if n.endswith(".txt")], [])

    def test_fs_type_non_linux_is_pinned(self):
        """★fs 判定限 Linux（BSD stat -f 語意不同、不可直譯）——字面與 bash 版逐字對應。"""
        if platform.system() == "Linux":
            self.assertNotEqual(fs_type(tempfile.gettempdir()), "non-linux")
        else:
            self.assertEqual(fs_type(tempfile.gettempdir()), "non-linux")


class TestDecryptIntoWiring(unittest.TestCase):
    """解密後半段（拆 key→斷言→寫入）的接線面，以假 sops 離線覆蓋。

    ★為何需要這層：上面各案驗的都是**純判定函式**，判定寫對了但沒接進 `_decrypt_into` 的
    fail 條件式一樣是零防線（實測：把 `newlines` 自條件式拿掉，純判定案全數照綠）。本類把
    「判定 → rc → 落點實際產出」串成一條，斷言一律看**落點檔**而非訊息字串。
    ★離線：run_sops 以 mock 換成「把合成 JSON 寫進 raw_path」，不需 docker、不觸真密文。
    ★本類固定走 manual=True（＝run_sops 那條）：驗的是**後半段共用管線**，與互動姿態無關；
    自動路徑的同一條管線另由 TestAutoDriver 以真 pty ＋假 sops 樁覆蓋。
    """

    def _dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def _run(self, values):
        """假 sops 產 values 的 JSON → 跑 _decrypt_into → (rc, 落點 .txt 檔名集合)。"""
        root, secrets_dir, tmp_dir = self._dir(), self._dir(), self._dir()
        os.makedirs(os.path.join(root, "deploy"))
        with open(os.path.join(root, ENC_REL), "w", encoding="utf-8") as fh:
            fh.write("          recipient: age1fixture\n")

        def fake_sops(_root, raw_path):
            with open(raw_path, "w", encoding="utf-8") as fh:
                fh.write(_payload_json(values))
            return 0

        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch(f"{__name__}.run_sops", side_effect=fake_sops), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = _decrypt_into(root, secrets_dir, tmp_dir, manual=True)
        return rc, sorted(n for n in os.listdir(secrets_dir) if n.endswith(".txt")), err.getvalue()

    def test_healthy_payload_writes_full_roster(self):
        rc, names, _err = self._run(_plain_values())
        self.assertEqual(rc, 0)
        self.assertEqual(names, sorted(k + ".txt" for k in EXPECTED_KEYS))

    def test_newline_value_is_zero_write_rc1(self):
        """★第 2 輪 finding：含換行值照寫＝decrypt 回「已就緒 rc=0」、緊接的 preflight 判
        內容劣化擋 up，且它指的處置是「重跑 decrypt」＝再產同一支壞檔。故必須零寫入退出。"""
        rc, names, err = self._run(
            dict(_plain_values(), captcha_secret="FAKE-captcha-line-one\nFAKE-captcha-line-two"))
        self.assertEqual(rc, 1)
        self.assertEqual(names, [])
        self.assertIn("captcha_secret", err)
        self.assertIn("sops.sh edit", err)

    def test_missing_key_is_zero_write_rc1(self):
        vals = _plain_values()
        del vals["smtp_password"]
        rc, names, err = self._run(vals)
        self.assertEqual(rc, 1)
        self.assertEqual(names, [])
        self.assertIn("smtp_password", err)


class TestEchoHit(unittest.TestCase):
    """回顯守衛純判定（B-036）。"""

    def test_plain_hit(self):
        self.assertTrue(echo_hit("noise " + _TEST_PASSPHRASE + " tail", _TEST_PASSPHRASE))

    def test_hit_survives_ansi_normalization(self):
        """容器 pty 的清行序列可能插進回顯中段——只驗原文一形會漏網，故兩形都看。"""
        chopped = _TEST_PASSPHRASE[:4] + "\x1b[2K" + _TEST_PASSPHRASE[4:]
        self.assertFalse(_TEST_PASSPHRASE in chopped)     # 原文形確實不命中
        self.assertTrue(echo_hit(chopped, _TEST_PASSPHRASE))

    def test_clean_stream_is_not_a_hit(self):
        self.assertFalse(echo_hit(_payload_json(_plain_values()), _TEST_PASSPHRASE))

    def test_empty_passphrase_never_hits(self):
        """★空 passphrase 不得讓守衛恆真（空字串是任何字串的子串）——那會把零提示直通路徑
        （identity 無 passphrase 殼、operator 直接按 Enter）整條靜默打死。"""
        self.assertFalse(echo_hit("anything at all", ""))


class TestAnnounce(unittest.TestCase):
    """預告行分流（B-036；★user 可見行為，措辭即契約）。"""

    def _say(self, count, manual):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            _announce(count, manual)
        return out.getvalue()

    def test_auto_says_single_entry_with_live_recipient_count(self):
        text = self._say(3, manual=False)
        self.assertIn("只需輸入一次", text)
        self.assertIn("3 個 recipient", text)          # 現算、不寫死（L-005）
        self.assertNotIn("**每一次**都要輸入", text)

    def test_auto_zero_recipient_form_omits_the_count(self):
        text = self._say(0, manual=False)
        self.assertIn("只需輸入一次", text)
        self.assertNotIn("0 個 recipient", text)

    def test_manual_keeps_the_per_prompt_wording(self):
        """退路的預告必須保留「每一次都要輸入」——手動路徑真的會逐次問。"""
        text = self._say(2, manual=True)
        self.assertIn("**每一次**都要輸入", text)
        self.assertIn("會問 2 次", text)
        self.assertNotIn("只需輸入一次", text)


class TestTerminateChild(unittest.TestCase):
    """孤兒收拾（B-036）：pty 子行程自成 session、host 的 Ctrl-C 不會傳下去，故必須主動終結。

    ★以樁驗證（真 docker run 不進自測射程）：pty.fork 起一支長睡子行程，_terminate_child
    後該 pid 必須既不存在、也沒留成殭屍（收屍成功＝waitpid 已取走）。
    """

    def test_long_running_child_is_killed_and_reaped(self):
        pid, master_fd = pty.fork()
        if pid == 0:
            try:
                os.execv(sys.executable, [sys.executable, "-c", "import time; time.sleep(600)"])
            except BaseException:                        # noqa: BLE001
                pass
            os._exit(127)
        try:
            code = _terminate_child(pid)
        finally:
            with contextlib.suppress(OSError):
                os.close(master_fd)
        self.assertIsNotNone(code)                       # 收不到屍才回 None
        with self.assertRaises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)                  # 已無此子行程＝沒留殭屍


class TestManualEnvDispatch(unittest.TestCase):
    """RV5_DECRYPT_MANUAL 判讀（B-036）：只認 "1"，其餘一律自動路徑。

    ★只驗分流參數、不起 sops：把 _decrypt_into 換成錄音機，讓「哪個值走哪條」成為確定性
    斷言；兩支安全自證也一併換掉——本案要量的是判讀，不該摻進落點／暫存的 fs 性質。
    """

    def _seen(self, env_value):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "deploy"))
        for rel in (".sops.yaml", ENC_REL):
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("# fixture\n")
        env = {"SECRETS_DIR": os.path.join(root, "sec")}
        if env_value is not None:
            env[MANUAL_ENV] = env_value
        seen = []

        def recorder(_root, _secrets_dir, _tmp_dir, manual):
            seen.append(manual)
            return 0

        def fake_tmp(_env):
            d = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, d, True)
            return d, []

        prev_umask = os.umask(0o022)
        os.umask(prev_umask)
        prev_cwd_fd = os.open(".", os.O_RDONLY)
        try:
            os.chdir(root)
            with unittest.mock.patch(f"{__name__}._decrypt_into", side_effect=recorder), \
                 unittest.mock.patch(f"{__name__}.prepare_secrets_dir", return_value=([], None)), \
                 unittest.mock.patch(f"{__name__}.prepare_tmp_dir", side_effect=fake_tmp), \
                 unittest.mock.patch("sys.stdin", _StubStdin(True)), \
                 contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                cmd_decrypt(root=root, env=env)
        finally:
            os.fchdir(prev_cwd_fd)
            os.close(prev_cwd_fd)
            os.umask(prev_umask)
        return seen

    def test_literal_one_selects_the_manual_path(self):
        self.assertEqual(self._seen("1"), [True])

    def test_every_other_value_falls_back_to_auto(self):
        """★只認 "1"：真值化判讀（"0"／"false" 也算開）會讓退路在打錯字時被誤啟用，
        而退路正是「盲打次數」那條已知會誤導 operator 的路（L-005）。"""
        for value in (None, "", "0", "01", "1 ", "true", "yes", "TRUE"):
            self.assertEqual(self._seen(value), [False], msg=repr(value))


class TestAutoDriver(unittest.TestCase):
    """自動應答 driver（B-036）：真 pty ＋假 sops 樁，離線、不需 docker、不觸真密文。

    ★樁落在 <root>/deploy/sops.sh——driver 叫用的就是這個相對路徑，故「wrapper 怎麼被起」
    也在射程內，且不必另開注入面（不開 CLI／環境變數面是本刀的硬約束）。
    ★getpass 一律 mock 成固定假字串；真 /dev/tty 面不強求自動化。
    ★樁只把**次數**寫進記錄檔（prompts／match／nonempty），連假 passphrase 都不落磁碟。
    """

    def _dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def _root(self, recipients=1):
        root = self._dir()
        os.makedirs(os.path.join(root, "deploy"))
        with open(os.path.join(root, ENC_REL), "w", encoding="utf-8") as fh:
            fh.write("          recipient: age1fixture\n" * recipients)
        return root

    def _install(self, root, src):
        path = os.path.join(root, "deploy", "sops.sh")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
        os.chmod(path, 0o755)

    def _record(self, root):
        with open(os.path.join(root, "stub-record.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def _run(self, root, manual=False):
        secrets_dir, tmp_dir = self._dir(), self._dir()
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch("getpass.getpass",
                                 return_value=_TEST_PASSPHRASE) as getpass_mock, \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = _decrypt_into(root, secrets_dir, tmp_dir, manual=manual)
        return {"rc": rc, "out": out.getvalue(), "err": err.getvalue(),
                "getpass_calls": getpass_mock.call_count, "tmp_dir": tmp_dir,
                "names": sorted(n for n in os.listdir(secrets_dir) if n.endswith(".txt"))}

    def test_two_prompts_are_fed_from_one_getpass(self):
        root = self._root(recipients=2)
        self._install(root, _stub_prompt_loop(root, 2))
        r = self._run(root)
        self.assertEqual(r["getpass_calls"], 1)          # ★user 端恰一次
        self.assertEqual(self._record(root), {"prompts": 2, "match": 2, "nonempty": 2})
        self.assertEqual(r["rc"], 0)
        self.assertEqual(r["names"], sorted(k + ".txt" for k in EXPECTED_KEYS))
        # ★預告行的**接線**也要驗：_announce 兩形都寫對了，但 _decrypt_into 把旗標傳反，
        #   operator 看到的仍是「每一次都要輸入」——純函式案對這條結構性失明。
        self.assertIn("只需輸入一次", r["out"])

    def test_zero_prompt_stream_passes_straight_through(self):
        """★identity 無 passphrase 殼＝sops 根本不索：driver 不得因「等不到提示」誤判，
        子行程正常結束即收尾（合成密文機器驗收走的就是這條主幹）。"""
        root = self._root()
        self._install(root, _stub_prompt_loop(root, 0))
        r = self._run(root)
        self.assertEqual(self._record(root), {"prompts": 0, "match": 0, "nonempty": 0})
        self.assertEqual(r["rc"], 0)
        self.assertEqual(r["names"], sorted(k + ".txt" for k in EXPECTED_KEYS))

    def test_feed_count_tracks_prompts_and_is_never_predicted(self):
        """★L-005 防復發：餵幾次由**流裡數到幾次提示**決定，與密文 recipient 現算數無關。
        故意讓兩者不一致（recipient 1、提示 3）——任何「照 recipient 數預餵」的實作在此即紅。"""
        root = self._root(recipients=1)
        self._install(root, _stub_prompt_loop(root, 3))
        r = self._run(root)
        self.assertEqual(self._record(root), {"prompts": 3, "match": 3, "nonempty": 3})
        self.assertEqual(r["rc"], 0)

    def test_silent_child_hits_the_timeout_and_leaves_no_orphan(self):
        """提示永不出現且子行程不退出 → 逾時觸發、子行程被終結收屍（不留孤兒 docker run）。
        ★上限常數以測試層 mock 縮短：生產面寫死本檔常數，不開環境變數／args 面。"""
        root = self._root()
        self._install(root, _stub_hang(root))
        with unittest.mock.patch(f"{__name__}.DRIVER_TOTAL_SEC", 1.5):
            r = self._run(root)
        self.assertNotEqual(r["rc"], 0)
        self.assertIn("逾時", r["err"])
        self.assertEqual(r["names"], [])
        with open(os.path.join(root, "stub.pid"), encoding="utf-8") as fh:
            child_pid = int(fh.read())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)

    def test_echoed_passphrase_suppresses_the_stream_and_fails_loud(self):
        """樁把收到的 passphrase 回吐進輸出流 → 回顯守衛觸發：整段不倒流、暫存清空、
        零寫入退出，且**訊息本身不含 passphrase**。"""
        root = self._root()
        self._install(root, _stub_prompt_loop(root, 1, echo_back=True))
        r = self._run(root)
        self.assertEqual(r["rc"], 1)
        self.assertEqual(r["names"], [])
        self.assertIn("已抑制", r["err"])
        self.assertNotIn(_TEST_PASSPHRASE, r["err"])
        self.assertNotIn(_TEST_PASSPHRASE, r["out"])
        self.assertEqual(os.path.getsize(os.path.join(r["tmp_dir"], "raw.out")), 0)

    def test_manual_path_never_feeds_but_auto_does(self):
        """RV5_DECRYPT_MANUAL=1 的退路：同一支樁在手動路徑收不到代餵、也不取 passphrase
        進記憶體。★對照組（同樁走自動路徑即收到）是必要的——沒有它，match=0 也可能只是
        樁壞了。"""
        manual_root = self._root()
        self._install(manual_root, _stub_prompt_loop(manual_root, 1, timed=True))
        manual = self._run(manual_root, manual=True)
        self.assertEqual(manual["getpass_calls"], 0)
        self.assertEqual(self._record(manual_root)["match"], 0)
        self.assertIn("**每一次**都要輸入", manual["out"])

        auto_root = self._root()
        self._install(auto_root, _stub_prompt_loop(auto_root, 1, timed=True))
        auto = self._run(auto_root)
        self.assertEqual(auto["getpass_calls"], 1)
        self.assertEqual(self._record(auto_root)["match"], 1)
        self.assertEqual(auto["rc"], 0)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def usage(msg=None):
    """用法錯誤：usage 走 stderr、exit 64（EX_USAGE；沿 tools/*.py 家族慣例）。"""
    if msg:
        print(msg, file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 64


def main(argv):
    args = argv[1:]
    if not args:
        return cmd_decrypt()
    cmd = args[0]
    if cmd == "test":
        if args[1:]:
            return usage(f"test：不收額外參數（見 {' '.join(args[1:])}）")
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
