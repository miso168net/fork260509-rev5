#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/preflight-secrets.py — up 前十三機密檔預檢（ADR 0010 轉換批①、B-035）

等價重寫自 deploy/preflight-secrets.sh：判定分支與退出碼逐一對應，唯一實作收斂＝落點解析
改用共用庫 deploy/secrets_common.py。

用法：python3 deploy/preflight-secrets.py

子命令：
  （無參數）  預檢七段依序：落點解析 → 缺檔 → 權限三斷言 → CR 護欄 → LF 護欄 →
              composite↔leaf 一致性 → 佔位字面。前六段任一命中即非零退出並指名；
              佔位字面只 WARN、照設計不阻擋。
  test        跑自帶測試（unittest、離線、stdlib-only；一律隔離暫存目錄、絕不讀寫真落點）

退出碼：全綠（含只有 WARN）0；任一 FAIL 1；用法錯誤 64（EX_USAGE；沿 tools/*.py 家族慣例）。

為何：docker compose secrets 用 `file: …/*.txt` bind；source 檔缺時 compose 不報「缺 X 檔」
而是自動建空目錄 → 容器拿到空／目錄 secret、錯誤訊息誤導（如 DB 連線失敗、boot panic）、
不指向真因。本預檢在 up 前指名缺檔。rev4:019 起本腳本＝落點接線的 fail-loud 承載者
（contracts rev4:P5.4）：缺檔／CR 劣化／composite drift 一律非零退出＋指名，絕不讓服務靜默
啟動失敗。

前代血緣（rev4 考古壓成一句）：rev4:001-compose-stack 立清單雛形，其後 rev4:007 增
captcha_secret、rev4:REVIEW-001-010 rev4:F001-1 補列、rev4:016 增四支（reaper_password／
reaper_database_url／alert_webhook_url／grafana_admin_password）、rev4:019 rev4:T027 增 CR 護欄
與 composite↔leaf 一致性、rev4:B-123 增權限面三斷言、rev4:B-119 增佔位字面 WARN、rev4:020
增 smtp_password／email_verify_secret 兩 leaf。

★輸出串流沿用 bash 版分工、刻意不統一（等價重寫不夾帶行為變更）：落點解析兩型失敗走
stderr（腳本尚未進入檢查本體、屬呼叫端用法錯誤面），其餘 FAIL 與 WARN 與 OK 走 stdout。
"""
import contextlib
import importlib.util
import io
import os
import platform
import pwd
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 落點解析共用庫（ADR 0010 轉換批①）：三消費者單一實作面。
# ★以 __file__ 推出的絕對路徑載入：不依賴 CWD（本檢查常自 repo 子目錄叫用），也不把
#   deploy/ 塞進 sys.path（避免搜尋路徑遮蔽）。
# ★載入失敗＝印真因後原樣拋（fail-loud）：落點解析是本預檢的地基，靜默降級＝查錯落點
#   還回綠（假綠），而本腳本正是 fail-loud 承載者。
_SECRETS_COMMON_PATH = os.path.join(HERE, "secrets_common.py")
try:
    _spec = importlib.util.spec_from_file_location("secrets_common", _SECRETS_COMMON_PATH)
    _secrets_common = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_secrets_common)
except Exception as _ex:
    print(f"[preflight-secrets] ERROR 載入共用庫 {_SECRETS_COMMON_PATH} 失敗：{_ex}"
          "——落點解析不得靜默降級（查錯落點回綠＝假綠）", file=sys.stderr)
    raise

resolve_secrets_dir = _secrets_common.resolve_secrets_dir

# 與 generate-secrets.sh 同一份十三機密清單（grafana_admin_password 僅 grafana
# [profiles:obs,metrics] 消費、但一律生成納入預檢——免 --profile obs 時 compose 對缺檔自動
# 建空目錄、grafana $__file{} 讀到空密碼、admin 登入靜默壞）。
REQUIRED = ("postgres_password", "redis_password", "jwt_secret", "refresh_token_secret",
            "database_url", "redis_url", "captcha_secret", "reaper_password",
            "reaper_database_url", "alert_webhook_url", "grafana_admin_password",
            "smtp_password", "email_verify_secret")

DIR_MODE_OK = "700"
FILE_MODE_OK = "644"

# composite↔leaf 期望值組合式（複用 generate-secrets.sh 之組合式；★兩處各寫一份、
# 不得順手合併——B-037 明載）。欄＝(composite 名, leaf 名, 位元組模板)。
COMPOSITES = (
    ("database_url", "postgres_password",
     b"postgres://soybean:{}@postgres:5432/soybean_admin_rust"),
    ("redis_url", "redis_password", b"redis://:{}@redis:6379"),
    ("reaper_database_url", "reaper_password",
     b"postgres://reaper:{}@postgres:5432/soybean_admin_rust"),
)

# rev4:B-119：已知佔位字面清單（★WARN 不阻擋、rc 不因它非零——佔位期照設計是可過的合法
# 狀態；升級成阻擋屬拍板級）。字面逐字取自 generate-secrets.sh 之 gen_placeholder 呼叫處
# （唯一佔位源頭）；三處同字面記帳見 ADR 0003（此＝提醒未填真值、彼＝不當機密）。
PLACEHOLDER_LITERALS = ("https://CHANGE-ME.invalid/alert-webhook-placeholder",)


def _sec_path(secrets_dir, name):
    return os.path.join(secrets_dir, name + ".txt")


def _mode_of(path):
    """檔／目錄權限位（八進位字串，同 `stat -c '%a'`）。

    ★bash 版寫成 `stat -c … || stat -f …` 雙形是為了同時吃 GNU 與 BSD stat（rev5 B5b
    移植期實測 macOS 必要）；python 的 os.stat 本身跨平台，雙形自然消解——判定不變。
    """
    return oct(os.stat(path).st_mode & 0o7777)[2:]


def _owner_name(uid):
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def _me():
    return _owner_name(os.getuid())


def missing_names(secrets_dir):
    """缺檔判定：缺檔、或為目錄（compose 對缺 bind source 自動建的空目錄）、或空檔＝缺。"""
    out = []
    for name in REQUIRED:
        f = _sec_path(secrets_dir, name)
        if not os.path.isfile(f) or os.path.getsize(f) == 0:
            out.append(name + ".txt")
    return out


def collect_perm_rows(secrets_dir):
    """權限面 IO 採集（缺檔段已放行才叫用）：回（目錄 mode, [(名稱, 路徑, mode, uid)]）。"""
    rows = [(name, _sec_path(secrets_dir, name),
             _mode_of(_sec_path(secrets_dir, name)),
             os.stat(_sec_path(secrets_dir, name)).st_uid) for name in REQUIRED]
    return _mode_of(secrets_dir), rows


def perm_hits(secrets_dir, dir_mode, rows):
    """rev4:B-123 權限面三斷言（純判定）：目錄 mode 700／檔 mode 644／檔 owner 非 root。

    縱深防禦、超出契約 rev4:P5.6 要求面。decrypt-secrets.sh 每次寫出即自證此形
    （rev4:P4.4／rev4:P4.6 目錄 700、rev4:P4.7 檔 644），但落點檔被人手改（chmod 600、
    目錄 777、sudo 建檔）後現檢照樣全綠——而那正是 rev4:P4.5／rev4:P4.7 自陳「只在開
    obs／metrics 軌時才炸」的失敗形。本斷言把它前移到 up 之前指名。
    ★置於 CR／composite 檢查之前：owner=root＋600 之檔會讓後方讀檔直接 Permission denied，
    先斷言權限才能保證後方檢查的錯誤訊息不失真。
    """
    hits = []
    if dir_mode != DIR_MODE_OK:
        hits.append(f"（目錄）{secrets_dir} mode={dir_mode}｜修復：chmod 700 {secrets_dir}")
    for name, path, mode, uid in rows:
        if mode != FILE_MODE_OK:
            hits.append(f"{name}.txt mode={mode}｜修復：chmod 644 {path}")
        if uid == 0:
            hits.append(f"{name}.txt owner={_owner_name(uid)}（不得為 root）"
                        f"｜修復：sudo chown {_me()} {path}")
    return hits


def _is_drvfs(path):
    """落點是否在 /mnt/* 之 drvfs（9p）。★fs 判定限 Linux——BSD stat -f 語意不同、不可直譯。"""
    if platform.system() != "Linux":
        return False
    try:
        r = subprocess.run(["stat", "-f", "-c", "%T", path], capture_output=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return False
    return r.stdout.strip() == "v9fs"


def read_blobs(secrets_dir):
    """十三檔位元組現值（權限段已放行才叫用）。"""
    blobs = {}
    for name in REQUIRED:
        with open(_sec_path(secrets_dir, name), "rb") as fh:
            blobs[name] = fh.read()
    return blobs


def content_hits(blobs):
    """rev4:019 rev4:T027① CR 護欄＋U4 補 LF 護欄（純判定）：回（cr_hit, nl_hit）。

    CR：printf '%s' 管線寫檔應零 CR；任何 CR＝內容已劣化（CRLF 編輯器覆存／pty 流未剝 CR
    直落檔），值進 URL／密碼尾即靜默壞。
    LF：CR 護欄照不到「尾端多一個 LF」，而 composite 一致性檢查在 bash 版是以命令替換取值
    （`$(cat)` 剝尾端換行）對它**結構性失明**——實測 redis_password.txt 尾多一個 LF 時
    preflight 仍回「齊備且健康、可 up」rc=0，而 compose 會把 15 byte 的密碼掛進 redis、把
    內嵌 14 byte 版本的 redis_url 掛進 rust-api，認證必失敗。判準＝檔案零換行字元
    （rev4:P4.1／rev4:P5.7 之 printf '%s' 寫檔形不變式的可機檢投影；bash 版寫成「stat 位元組
    數 ≠ 剝 LF 後位元組數」，與此處的 in 判定逐位元組等價）。
    ★兩者互斥分流（elif）：含 CR 的檔只報 CR，免同一劣化來源報兩次。
    """
    cr, nl = [], []
    for name in REQUIRED:
        data = blobs[name]
        if b"\r" in data:
            cr.append(name + ".txt")
        elif len(data) != len(data.replace(b"\n", b"")):
            nl.append(name + ".txt")
    return cr, nl


def drift_hits(blobs):
    """rev4:019 rev4:T027② composite↔leaf 一致性（純判定）——防「塞入密碼已過期的
    database_url 也回 OK」；只指名檔案、絕不印值。

    ★比對走**位元組**全等（與 decrypt rev4:P4.5 同一形）：bash 的命令替換會剝尾端換行、
    字串相等比較對尾端換行失明，故此處 leaf 取值同樣先剝尾端 LF 再組（上方 LF 護欄已先擋、
    此處為縱深防禦、不靠護欄的執行序）。
    """
    out = []
    for composite, leaf, tmpl in COMPOSITES:
        if tmpl.replace(b"{}", blobs[leaf].rstrip(b"\n")) != blobs[composite]:
            out.append(composite + ".txt")
    return out


def placeholder_hits(blobs):
    """rev4:B-119 佔位字面比對（純判定）：逐字全等、不做前綴／樣式放寬。"""
    lits = tuple(s.encode("utf-8") for s in PLACEHOLDER_LITERALS)
    return [name + ".txt" for name in REQUIRED if blobs[name] in lits]


def cmd_check(root=None, env=None):
    """預檢本體。root／env 皆為測試注入用哨兵——生產面走模組 ROOT 與本行程環境。

    ★root 預設＝ROOT（由 __file__ 推得的 repo 根）而**非 CWD**：compose 以專案目錄（＝repo
    根）解析相對值，本檢查若以 CWD 錨定，自 repo 子目錄執行時看的就與 compose 是不同目錄，
    出現「preflight 全綠、compose 掛空目錄」的假綠（本檢查正是 fail-loud 承載者、假綠最致命）。
    ★env=None 是哨兵、不得寫成 `env or os.environ`：呼叫端明給空 dict＝「該環境確實沒設」，
    改讀本行程環境會讓「未設」與「已匯出為空」兩分支靜默改判（同共用庫註解）。
    """
    root = ROOT if root is None else root
    secrets_dir, err = resolve_secrets_dir(root, env)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1

    missing = missing_names(secrets_dir)
    if missing:
        print(f"FAIL：缺少 {len(missing)} 個 secret 檔（{secrets_dir}）：")
        for m in missing:
            print(f"   - {m}")
        print("")
        print("→ SOPS 管線重建：./deploy/decrypt-secrets.sh（10 支）→ "
              "./deploy/generate-secrets.sh --compose-only（3 composite）。")
        print("  （無加密檔情境仍可 ./deploy/generate-secrets.sh 一鍵生成 dev 亂數、缺的才補。）")
        return 1

    dir_mode, rows = collect_perm_rows(secrets_dir)
    hits = perm_hits(secrets_dir, dir_mode, rows)
    if hits:
        print("FAIL：權限面不符（目錄須 700、檔須 644 且 owner 非 root）——這正是 "
              "rev4:P4.5／rev4:P4.7 自陳")
        print("      「只在開 obs／metrics 軌才炸」的失敗形（grafana uid 472／"
              "postgres-exporter 65534／")
        print("      redis-exporter 59000 讀 /run/secrets/* 全 Permission denied）；"
              "本斷言把它前移到 up 之前：")
        for p in hits:
            print(f"   - {p}")
        if _is_drvfs(secrets_dir):
            print("→ 落點在 /mnt/* 之 drvfs（9p）：chmod 結構性 no-op、mode 恆讀 777，"
                  "本紅字是特性不是誤報——")
            print("  拍板落點應在 ext4（如 $HOME/.cache/fork260509-rev5/secrets；"
                  "承 rev4:ADR 0080／rev4:0084），請遷落點而非改本檢查。")
        return 1

    blobs = read_blobs(secrets_dir)
    cr, nl = content_hits(blobs)
    if cr:
        print("FAIL：下列 secret 檔含 CR 字元（內容劣化、值進連線字串即靜默壞）："
              + " ".join(cr))
        print("→ 重跑 ./deploy/decrypt-secrets.sh（printf 管線寫檔、零 CR）後再驗。")
        return 1
    if nl:
        print("FAIL：下列 secret 檔含換行字元（printf '%s' 寫檔形應零換行；尾端換行會讓 "
              "composite")
        print("      一致性檢查失明、容器拿到與 composite 不符的值）：" + " ".join(nl))
        print("→ 重跑 ./deploy/decrypt-secrets.sh（10 支）＋ "
              "./deploy/generate-secrets.sh --compose-only（3 composite）後再驗。")
        return 1

    drift = drift_hits(blobs)
    if drift:
        print("FAIL：composite 與 leaf 不一致（drift）：" + " ".join(drift))
        print("→ 跑 ./deploy/generate-secrets.sh --compose-only 由 leaf 現值重組 composite。")
        return 1

    ph = placeholder_hits(blobs)
    if ph:
        print("WARN：下列 secret 檔仍為生成腳本的佔位字面（照設計可 up；留佔位的唯一徵狀"
              "＝該功能")
        print("      靜默失效，如告警投遞不出）：" + " ".join(ph))
        print("→ 填真值走 RUNBOOK §7 對應列（alert_webhook_url＝直接編輯檔＋restart grafana）；")
        print("  填完必接 §15.4 re-encrypt 回寫加密檔，否則下次 decrypt 判 DIFF 另存 .new。")

    print(f"OK：{len(REQUIRED)} 個必須 secret 檔齊備且健康（{secrets_dir}；權限 700/644、"
          "CR 零命中、composite 一致）。可 up。")
    return 0


# ---------------------------------------------------------------------------
# 自測（test 子命令）：離線、stdlib-only、一律隔離暫存目錄，絕不讀寫真機密落點
# ---------------------------------------------------------------------------

def _fixture(secrets_dir, overrides=None):
    """在隔離暫存目錄建一份「健康」的十三機密（目錄 700／檔 644／零換行／composite 一致）。

    overrides＝{名稱: 位元組}；值給 None＝刻意不建該檔（缺檔情境）。
    ★呼叫端一律傳 tempfile 目錄——本函式會 chmod 與覆寫，指向真落點即毀機密。
    """
    values = {name: ("val-" + name).encode("utf-8") for name in REQUIRED}
    for composite, leaf, tmpl in COMPOSITES:
        values[composite] = tmpl.replace(b"{}", values[leaf])
    values.update(overrides or {})
    os.makedirs(secrets_dir, exist_ok=True)
    for name in REQUIRED:
        if values[name] is None:
            continue
        path = _sec_path(secrets_dir, name)
        with open(path, "wb") as fh:
            fh.write(values[name])
        os.chmod(path, 0o644)
    os.chmod(secrets_dir, 0o700)
    return values


def _sandbox_holds_modes(d):
    """暫存沙盒能否承載 644（drvfs 上 chmod 結構性 no-op、mode 恆讀 777）。"""
    probe = os.path.join(d, ".mode-probe")
    with open(probe, "w"):
        pass
    os.chmod(probe, 0o644)
    held = _mode_of(probe) == FILE_MODE_OK
    os.remove(probe)
    return held


_DRVFS_SKIP = ("暫存沙盒在 drvfs（chmod 結構性 no-op、mode 恆讀 777）——權限面判定改由 "
               "perm_hits 純判定案覆蓋；把 TMPDIR 指到 ext4 即可跑本案")


class TestRosterPinned(unittest.TestCase):
    """★名冊字面釘死：以被測常數迭代出期望值＝套套邏輯（名冊縮水時斷言跟著縮水、全綠
    存活）。十三機密少一支＝該支缺檔／劣化全面失檢，故字面逐一列出。"""

    def test_required_roster_is_pinned(self):
        self.assertEqual(REQUIRED, (
            "postgres_password", "redis_password", "jwt_secret", "refresh_token_secret",
            "database_url", "redis_url", "captcha_secret", "reaper_password",
            "reaper_database_url", "alert_webhook_url", "grafana_admin_password",
            "smtp_password", "email_verify_secret"))
        self.assertEqual(len(REQUIRED), 13)

    def test_composite_formulas_are_pinned(self):
        """三條組合式字面釘死（與 generate-secrets.sh 各寫一份、單邊改即真 stack 認證失敗）。"""
        self.assertEqual(COMPOSITES, (
            ("database_url", "postgres_password",
             b"postgres://soybean:{}@postgres:5432/soybean_admin_rust"),
            ("redis_url", "redis_password", b"redis://:{}@redis:6379"),
            ("reaper_database_url", "reaper_password",
             b"postgres://reaper:{}@postgres:5432/soybean_admin_rust")))

    def test_placeholder_literal_is_pinned(self):
        """ADR 0003 三處同字面記帳之一：改佔位值必同刀改 generate-secrets 與 guard 白名單。"""
        self.assertEqual(PLACEHOLDER_LITERALS,
                         ("https://CHANGE-ME.invalid/alert-webhook-placeholder",))

    def test_root_is_anchored_on_file_not_cwd(self):
        """★落點錨定基準＝由 __file__ 推得的 repo 根，非 CWD：改吃 CWD 即「自子目錄執行時
        preflight 全綠、compose 掛空目錄」的假綠（bash 版 REPO_ROOT 同義）。"""
        self.assertEqual(ROOT, os.path.dirname(HERE))
        self.assertEqual(os.path.basename(HERE), "deploy")
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        # ★樣本執行期串接構造：字面寫死會讓本斷言自己命中自己（同 secret-value-guard 慣例）
        self.assertNotIn("get" + "cwd", src, msg="落點錨定改吃 CWD＝自子目錄執行時的假綠")


class TestPurePredicates(unittest.TestCase):
    """六段判定的純函式面（零 IO、零 chmod 依賴，drvfs 上照跑）。"""

    def _blobs(self, overrides=None):
        values = {name: ("val-" + name).encode("utf-8") for name in REQUIRED}
        for composite, leaf, tmpl in COMPOSITES:
            values[composite] = tmpl.replace(b"{}", values[leaf])
        values.update(overrides or {})
        return values

    def test_perm_hits_green_when_700_and_644_and_non_root(self):
        rows = [(n, f"/x/{n}.txt", "644", 1000) for n in REQUIRED]
        self.assertEqual(perm_hits("/x", "700", rows), [])

    def test_perm_hits_dir_mode(self):
        rows = [(n, f"/x/{n}.txt", "644", 1000) for n in REQUIRED]
        hits = perm_hits("/x", "777", rows)
        self.assertEqual(len(hits), 1)
        self.assertIn("（目錄）/x mode=777", hits[0])
        self.assertIn("chmod 700", hits[0])

    def test_perm_hits_file_mode(self):
        rows = [(n, f"/x/{n}.txt", "644", 1000) for n in REQUIRED]
        rows[0] = (REQUIRED[0], f"/x/{REQUIRED[0]}.txt", "600", 1000)
        hits = perm_hits("/x", "700", rows)
        self.assertEqual(len(hits), 1)
        self.assertIn(f"{REQUIRED[0]}.txt mode=600", hits[0])

    def test_perm_hits_root_owner(self):
        """★root owner 分支：真 repo 內無法以非 root 造出 root-owned 檔，故走純判定覆蓋
        （bash 版此分支從未被任何自動化驗過）。"""
        rows = [(n, f"/x/{n}.txt", "644", 1000) for n in REQUIRED]
        rows[1] = (REQUIRED[1], f"/x/{REQUIRED[1]}.txt", "644", 0)
        hits = perm_hits("/x", "700", rows)
        self.assertEqual(len(hits), 1)
        self.assertIn("（不得為 root）", hits[0])
        self.assertIn("sudo chown", hits[0])

    def test_content_hits_clean(self):
        self.assertEqual(content_hits(self._blobs()), ([], []))

    def test_content_hits_cr(self):
        cr, nl = content_hits(self._blobs({"jwt_secret": b"abc\rdef"}))
        self.assertEqual((cr, nl), (["jwt_secret.txt"], []))

    def test_content_hits_trailing_lf(self):
        """★尾端多一個 LF：CR 護欄照不到、composite 位元組比對亦剝尾端 LF 後仍相等，
        唯一擋得住的就是本護欄（拿掉即 rc=0 假綠、容器拿到 15 byte 密碼）。"""
        cr, nl = content_hits(self._blobs({"redis_password": b"val-redis_password\n"}))
        self.assertEqual((cr, nl), ([], ["redis_password.txt"]))

    def test_content_hits_crlf_reports_cr_only(self):
        """互斥分流：同一劣化來源（CRLF 覆存）不重複報兩段。"""
        cr, nl = content_hits(self._blobs({"jwt_secret": b"abc\r\n"}))
        self.assertEqual((cr, nl), (["jwt_secret.txt"], []))

    def test_drift_hits_consistent(self):
        self.assertEqual(drift_hits(self._blobs()), [])

    def test_drift_hits_stale_composite(self):
        """leaf 換了新密碼、composite 還內嵌舊密碼＝真 stack 認證必失敗的漂移形。"""
        b = self._blobs({"postgres_password": b"rotated-new"})
        self.assertEqual(drift_hits(b), ["database_url.txt"])

    def test_drift_hits_is_byte_exact(self):
        """位元組全等、不做寬鬆比對：composite 多一個尾端空白即算漂移。"""
        b = self._blobs()
        b["redis_url"] = b["redis_url"] + b" "
        self.assertEqual(drift_hits(b), ["redis_url.txt"])

    def test_placeholder_hits_exact_only(self):
        lit = PLACEHOLDER_LITERALS[0].encode("utf-8")
        self.assertEqual(placeholder_hits(self._blobs({"alert_webhook_url": lit})),
                         ["alert_webhook_url.txt"])
        # 近似形不豁免：多一個字元即不算佔位（防前綴／樣式放寬導致誤判）
        self.assertEqual(placeholder_hits(self._blobs({"alert_webhook_url": lit + b"x"})), [])


class TestCheckPipeline(unittest.TestCase):
    """預檢七段整合（隔離暫存 SECRETS_DIR；SECRETS_DIR 一律明給、絕不落到真落點）。"""

    def _run(self, secrets_dir=None, root=None, env=None):
        out, err = io.StringIO(), io.StringIO()
        if env is None:
            env = {} if secrets_dir is None else {"SECRETS_DIR": secrets_dir}
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cmd_check(root=root or os.path.join(tempfile.gettempdir(), "no-such-root"),
                           env=env)
        return rc, out.getvalue(), err.getvalue()

    def test_healthy_dir_passes(self):
        with tempfile.TemporaryDirectory() as d:
            if not _sandbox_holds_modes(d):
                self.skipTest(_DRVFS_SKIP)
            sd = os.path.join(d, "secrets")
            _fixture(sd)
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertIn("可 up", out)
            self.assertIn("13 個必須 secret 檔", out)

    def test_placeholder_warns_without_blocking(self):
        """★佔位期照設計可 up：WARN 印出但 rc 仍 0（升級成阻擋屬拍板級、本重寫不做）。"""
        with tempfile.TemporaryDirectory() as d:
            if not _sandbox_holds_modes(d):
                self.skipTest(_DRVFS_SKIP)
            sd = os.path.join(d, "secrets")
            _fixture(sd, {"alert_webhook_url": PLACEHOLDER_LITERALS[0].encode("utf-8")})
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertIn("WARN", out)
            self.assertIn("alert_webhook_url.txt", out)
            self.assertIn("可 up", out)

    def test_missing_file_named_and_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "secrets")
            _fixture(sd, {"jwt_secret": None})
            rc, out, _ = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("缺少 1 個 secret 檔", out)
            self.assertIn("jwt_secret.txt", out)

    def test_empty_file_counts_as_missing(self):
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "secrets")
            _fixture(sd, {"jwt_secret": b""})
            rc, out, _ = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("jwt_secret.txt", out)

    def test_directory_in_place_of_file_counts_as_missing(self):
        """compose 對缺 bind source 自動建的空目錄——正是本預檢要指名的那個真因。"""
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "secrets")
            _fixture(sd, {"jwt_secret": None})
            os.makedirs(_sec_path(sd, "jwt_secret"))
            rc, out, _ = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("jwt_secret.txt", out)

    def test_missing_dir_lists_all_thirteen(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out, _ = self._run(os.path.join(d, "nowhere"))
            self.assertEqual(rc, 1)
            self.assertIn("缺少 13 個 secret 檔", out)

    def test_cr_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            if not _sandbox_holds_modes(d):
                self.skipTest(_DRVFS_SKIP)
            sd = os.path.join(d, "secrets")
            _fixture(sd, {"jwt_secret": b"abc\rdef"})
            rc, out, _ = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("含 CR 字元", out)
            self.assertIn("jwt_secret.txt", out)

    def test_trailing_lf_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            if not _sandbox_holds_modes(d):
                self.skipTest(_DRVFS_SKIP)
            sd = os.path.join(d, "secrets")
            _fixture(sd, {"captcha_secret": b"val-captcha_secret\n"})
            rc, out, _ = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("含換行字元", out)
            self.assertIn("captcha_secret.txt", out)

    def test_composite_drift_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            if not _sandbox_holds_modes(d):
                self.skipTest(_DRVFS_SKIP)
            sd = os.path.join(d, "secrets")
            # 合成 DSN 執行期串接構造（防本檔自命中機密樣式掃描；同 secret-value-guard 慣例）
            _fixture(sd, {"database_url": b"postgres" + b"://soybean:" +
                                          b"STALE@postgres:5432/soybean_admin_rust"})
            rc, out, _ = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("drift", out)
            self.assertIn("database_url.txt", out)

    def test_exported_empty_secrets_dir_is_loud_failure(self):
        """★空字串邊界：「已匯出但為空」≠「未設」——compose 對空字串吃預設值回退 repo 內
        舊落點且不讀 .env；當未設而續讀 .env 即「腳本查新落點、compose 掛舊落點」的靜默
        分裂。無合法用途（要走回退請 unset），故吵鬧失敗、走 stderr。"""
        rc, out, err = self._run(env={"SECRETS_DIR": ""})
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", err)
        self.assertEqual(out, "")

    def test_env_file_metachar_value_is_rejected(self):
        """.env 之值含空白／shell 元字元＝拒用（吵鬧失敗、不靜默回退舊落點）。"""
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, ".env"), "w", encoding="utf-8") as fh:
                fh.write("SECRETS_DIR=/tmp/$(id -un)/secrets\n")
            rc, _out, err = self._run(root=d, env={})
            self.assertEqual(rc, 1)
            self.assertIn("元字元", err)

    def test_env_file_relative_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, ".env"), "w", encoding="utf-8") as fh:
                fh.write("SECRETS_DIR=deploy/secrets\n")
            rc, _out, err = self._run(root=d, env={})
            self.assertEqual(rc, 1)
            self.assertIn("絕對路徑", err)

    def test_env_file_absolute_value_is_used(self):
        """.env 的落點確實被採用——以缺檔訊息指名的目錄為證（寬進窄出、不靜默回退）。"""
        with tempfile.TemporaryDirectory() as d:
            target = os.path.join(d, "elsewhere")
            with open(os.path.join(d, ".env"), "w", encoding="utf-8") as fh:
                fh.write(f"export  SECRETS_DIR = {target}\r\n")
            rc, out, _ = self._run(root=d, env={})
            self.assertEqual(rc, 1)
            self.assertIn(target, out)

    def test_default_falls_back_to_repo_deploy_secrets(self):
        """環境與 .env 皆無 → repo 內 deploy/secrets，且錨在傳入的 root（非 CWD）。"""
        with tempfile.TemporaryDirectory() as d:
            rc, out, _ = self._run(root=d, env={})
            self.assertEqual(rc, 1)
            self.assertIn(os.path.join(d, "deploy", "secrets"), out)


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
        return cmd_check()
    cmd = args[0]
    if cmd == "test":
        if args[1:]:
            return usage(f"test：不收額外參數（見 {' '.join(args[1:])}）")
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
