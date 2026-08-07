#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/generate-secrets.py — rev5-admin 十三機密一鍵生成（ADR 0010 轉換批③、B-037）

等價重寫自 deploy/generate-secrets.sh：判定分支、輸出字面、輸出串流與退出碼逐一對應，
唯一實作收斂＝落點解析改用共用庫 deploy/secrets_common.py（同 preflight／decrypt 先例；
落點解析兩型失敗的訊息字面隨之收斂到共用庫版本，rc 與串流不變）。

用法：python3 deploy/generate-secrets.py [--force|--compose-only]

子命令：
  （無旗標）      冪等：已存在跳過（SKIPPED）、缺則補（GENERATED）。
  --force         亂數生成的十二支全重生；alert_webhook_url 屬 user 自填設定值、不在範圍。
  --compose-only  只重組 3 composite；10 支來源檔（9 leaf＋alert_webhook_url）缺任一＝
                  報錯退出、絕不代生成。
  test            跑自帶測試（unittest、離線、stdlib-only、不需 docker；一律隔離暫存目錄，
                  SECRETS_DIR 一律寫死於測試內、絕不取自環境——防在真落點重生亂數）

退出碼：正常結束 0；落點解析／缺來源檔／目錄佔位無法清除 1；用法錯誤 64；
        docker 不可得 127（＝shell 的 command-not-found 碼）；docker 本身非零＝原樣透傳。

十三機密（$SECRETS_DIR/*.txt；落點解析見共用庫、未設回退 deploy/secrets）：
  leaf      postgres_password（hex 24、URL-safe）／redis_password（hex 24、URL-safe）
  leaf      jwt_secret（base64 48）／refresh_token_secret（base64 48）
  leaf      captcha_secret（base64 48；rev4:007-login-throttle challenge HS256）
  leaf      reaper_password（hex 24、URL-safe；rev4:016 reaper 最小權限 DB 身分）
  leaf      grafana_admin_password（base64 24；rev4:016 grafana GF $__file{} 檔注入、非 URL）
  leaf      smtp_password（base64 24；rev4:020 SMTP 密碼——dev 亂數 leaf 未消費、prod 真值＝
            Gmail app password 依 RUNBOOK §15.4 回寫；★亂數非 CHANGE-ME——config 對佔位值 panic）
  leaf      email_verify_secret（base64 48；rev4:020 驗證憑據 HS256 獨立金鑰、仿 captcha_secret 形）
  composite database_url／redis_url／reaper_database_url（由 leaf 檔案內容組合、絕不獨立亂數）
  佔位      alert_webhook_url（顯眼佔位 URL；真值 user 自填、--force 不重置——重置法＝刪檔重跑）

設計（三條逐字紀律，B-037 明載、違者即行為變更）：
  - 亂數一律走 docker alpine/openssl rand（host 除 docker 外零依賴）——**絕不**改用 python
    的亂數模組：那是行為變更＋host 依賴姿態變。輔助映像沿 latest 浮動 tag＝拍板豁免
    rev4:ADR 0022、勿改釘數字版。
  - alert_webhook_url 佔位字面與 deploy/preflight-secrets.py／ADR 0003 三處共享同一字面，
    逐字保住（本檔＝唯一佔位源頭）。
  - composite 組合式在 generate 與 preflight **各寫一份、不得順手合併**（B-037 明載）：
    dual-write 由本檔自持實作，驗證面靠等價矩陣、不靠共用。

前代血緣（rev4 考古壓成一句）：rev4:001-compose-stack 立十三機密雛形，其後 rev4:007 增
captcha_secret、rev4:016 增四支（reaper_password／reaper_database_url／alert_webhook_url／
grafana_admin_password）、rev4:019 rev4:P5.5 增 --compose-only 與落點三級口徑、rev4:P4.7 定權限
終值（目錄 700／檔 644）、rev4:020 增 smtp_password／email_verify_secret 兩 leaf。
"""
import contextlib
import glob as globmod
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 落點解析共用庫（ADR 0010 轉換批①）：四消費者單一實作面。
# ★以 __file__ 推出的絕對路徑載入：不依賴 CWD（本腳本常自 repo 子目錄叫用），也不把
#   deploy/ 塞進 sys.path（避免搜尋路徑遮蔽）。
# ★載入失敗＝印真因後原樣拋（fail-loud）：落點解析錯了就是把明文機密寫到別處，靜默降級
#   遠比當場炸危險。
_SECRETS_COMMON_PATH = os.path.join(HERE, "secrets_common.py")
try:
    _spec = importlib.util.spec_from_file_location("secrets_common", _SECRETS_COMMON_PATH)
    _secrets_common = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_secrets_common)
except Exception as _ex:
    print(f"[generate-secrets] ERROR 載入共用庫 {_SECRETS_COMMON_PATH} 失敗：{_ex}"
          "——落點解析不得靜默降級（寫錯落點＝明文機密落在非預期目錄）", file=sys.stderr)
    raise

resolve_secrets_dir = _secrets_common.resolve_secrets_dir

# 亂數來源（逐字紀律一）：映像沿 latest 浮動 tag（rev4:ADR 0022 拍板豁免、勿改釘數字版）。
OPENSSL_IMG = "alpine/openssl:latest"

# leaf 名冊＝(名稱, openssl rand 引數)；★次序即 docker 調用次序，等價矩陣以 argv 序列比對。
# jwt／refresh／captcha／email_verify 用 base64（不進 URL）；postgres／redis／reaper 用 hex
# （URL-safe，嵌入連線字串不被 + / = 破壞）；grafana／smtp 僅檔注入、非 URL → base64 安全。
LEAF_SPECS = (
    ("postgres_password", ("-hex", "24")),
    ("redis_password", ("-hex", "24")),
    ("jwt_secret", ("-base64", "48")),
    ("refresh_token_secret", ("-base64", "48")),
    ("captcha_secret", ("-base64", "48")),
    ("reaper_password", ("-hex", "24")),
    ("grafana_admin_password", ("-base64", "24")),
    ("smtp_password", ("-base64", "24")),
    ("email_verify_secret", ("-base64", "48")),
)
LEAF_NAMES = tuple(name for name, _args in LEAF_SPECS)

# composite 組合式（逐字紀律三）：與 deploy/preflight-secrets.py 的 COMPOSITES **各寫一份**，
# 不得順手合併——單邊改即真 stack 認證失敗，兩側各自的釘死斷言就是那道對賬。
# 欄＝(composite 名, leaf 名, 位元組模板)。
COMPOSITES = (
    ("database_url", "postgres_password",
     b"postgres://soybean:{}@postgres:5432/soybean_admin_rust"),
    ("redis_url", "redis_password", b"redis://:{}@redis:6379"),
    ("reaper_database_url", "reaper_password",
     b"postgres://reaper:{}@postgres:5432/soybean_admin_rust"),
)

# 佔位機密（逐字紀律二）：本檔＝唯一佔位源頭；.invalid 為保留域、必不可達。
# 三處同字面記帳見 ADR 0003（此＝提醒未填真值、preflight＝WARN 不阻擋、guard＝白名單不當機密）。
PLACEHOLDER_NAME = "alert_webhook_url"
PLACEHOLDER_VALUE = "https://CHANGE-ME.invalid/alert-webhook-placeholder"

# --compose-only 的來源檔集合（9 leaf＋佔位；composite 不在其中——它們正是要重組的標的）。
COMPOSE_ONLY_SOURCES = LEAF_NAMES + (PLACEHOLDER_NAME,)

# 摘要列印次序（逐字沿舊檔 Step 5 迴圈）：9 leaf → 3 composite → 佔位。
SUMMARY_ORDER = LEAF_NAMES + tuple(name for name, _l, _t in COMPOSITES) + (PLACEHOLDER_NAME,)

DIR_MODE = 0o700          # rev4:019 rev4:P4.7 權限終值：目錄 700
FILE_MODE = 0o644         # 同上：檔 644（grafana 472／postgres-exporter 65534／redis-exporter
                          # 59000 三個非 root service 要讀 /run/secrets；暴露面由目錄 700 承載）
BIRTH_UMASK = 0o077       # 機密檔出生即 600（原生 Linux 檔系統生效）；終值於 Step 4 收斂


class GenerateAbort(Exception):
    """中止流程並帶出退出碼（等價於 bash 版 `set -e` 與顯式 exit 的合流出口）。"""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _sec_path(secrets_dir, name):
    return os.path.join(secrets_dir, name + ".txt")


def docker_rand_argv(rand_args):
    """亂數調用 argv（逐字紀律一）：沿舊檔 `docker run --rm "$OPENSSL_IMG" rand "$@"`。

    ★形制由本函式單點決定，等價矩陣以假 docker 樁收 argv 序列逐位元組比對新舊。
    """
    return ["docker", "run", "--rm", OPENSSL_IMG, "rand"] + list(rand_args)


def _run(argv, capture):
    """跑外部命令。capture=True 才收 stdout（stderr 一律原樣透傳給呼叫端終端）。

    ★docker 不可得＝回 127：bash 版靠 shell 的 command-not-found 語意退出 127，python 這側
    要自己指名真因，否則使用者看到的是 traceback 而不是「請先裝 docker」。
    """
    try:
        return subprocess.run(argv, stdout=subprocess.PIPE if capture else None)
    except OSError as ex:
        print(f"FAIL：無法執行 {argv[0]}（{ex}）——亂數一律走 docker "
              f"{OPENSSL_IMG} 容器（host 除 docker 外零依賴）", file=sys.stderr)
        raise GenerateAbort(127) from ex


def ensure_image():
    """離線／限流時 image 已 cache 則免 pull（`docker pull` 在 set -e 下會 abort、即使本機已有）。

    逐字沿舊檔：`docker image inspect IMG >/dev/null 2>&1 || docker pull -q IMG >/dev/null`。
    ★本步在 --compose-only 也照跑（舊檔 line 118 無條件執行）——等價矩陣的 argv 序列比對會
      看到這一發，別「順手」把它挪進非 compose-only 分支。
    """
    try:
        with open(os.devnull, "wb") as null:
            probe = subprocess.run(["docker", "image", "inspect", OPENSSL_IMG],
                                   stdout=null, stderr=null)
        if probe.returncode == 0:
            return
    except OSError:
        # ★inspect 這一發的 `2>&1` 導向 /dev/null＝連「命令不存在」也被吞掉（舊檔逐字行為）；
        #   真因由下方 pull 那一發吐出，rc 與訊息落點（stderr）因此與 bash 側一致。
        pass
    r = _run(["docker", "pull", "-q", OPENSSL_IMG], capture=True)
    if r.returncode != 0:
        raise GenerateAbort(r.returncode)


def gen_rand(rand_args):
    """回隨機值位元組（去尾端換行＝bash 命令替換語意）。非零退出＝原樣透傳 rc（set -e）。"""
    r = _run(docker_rand_argv(rand_args), capture=True)
    if r.returncode != 0:
        raise GenerateAbort(r.returncode)
    return r.stdout.rstrip(b"\n")


def clear_dir_placeholder(path):
    """機密檔缺席時 docker 可能於該路徑自動建出「目錄」佔位（缺檔直接 up 的殘骸）——
    空目錄自動清除、非空指名退出，讓 preflight→generate 的恢復路徑自足。"""
    if not os.path.isdir(path):
        return
    try:
        os.rmdir(path)
    except OSError:
        print(f"FAIL：{path} 是非空目錄（無法自動清除）——請手動移除後重跑", file=sys.stderr)
        raise GenerateAbort(1)
    print(f"  {os.path.basename(path)} 為目錄佔位（缺檔曾直接 up 的殘骸）→ 已清除")


def _write(path, data):
    """寫值（`printf '%s'`：零尾端換行）。既有檔以截斷寫入、mode 不動；新檔吃 umask 077。"""
    with open(path, "wb") as fh:
        fh.write(data)


def compose_expected(leaf_blob, tmpl):
    """composite 期望值（純函式）：leaf 現值先剝尾端 LF（bash `$(cat)` 語意）再套模板。"""
    return tmpl.replace(b"{}", leaf_blob.rstrip(b"\n"))


def gen_leaf(secrets_dir, name, rand_args, force, status):
    """leaf：檔缺或 --force → 取亂數重寫（GENERATED）；否則不動（SKIPPED）。"""
    path = _sec_path(secrets_dir, name)
    clear_dir_placeholder(path)
    if not os.path.isfile(path) or force:
        _write(path, gen_rand(rand_args))
        status[name] = "GENERATED"
    else:
        status[name] = "SKIPPED"


def gen_composite(secrets_dir, name, value, force, status):
    """composite：檔缺、--force、或現值 ≠ 期望值（leaf 重生／單獨改動＝drift）→ 重寫。

    ★內容比對取代「本次是否重生」旗標——連 leaf 在腳本之外被改動的 drift 也修復。
    ★比對走**位元組**全等（與 decrypt rev4:P4.5、preflight rev4:T027② 同一形）：bash 的
      `$(cat)` 會剝掉尾端換行，字串相等比較對「檔尾多一個 LF」結構性失明——實測
      redis_url.txt 尾多一個 LF 時判為相等、印 SKIPPED、rc=0，劣化未修復（rev4:P5.7 之
      byte-identical 不變式失效）。
    """
    path = _sec_path(secrets_dir, name)
    clear_dir_placeholder(path)
    exists = os.path.isfile(path)
    if exists and not force:
        with open(path, "rb") as fh:
            if fh.read() == value:
                status[name] = "SKIPPED"
                return
        print(f"  {name}.txt 與依賴 leaf 不一致（dual-write drift）→ 連動重寫")
    _write(path, value)
    status[name] = "GENERATED"


def gen_placeholder(secrets_dir, name, value, status):
    """佔位：僅缺檔才寫入（既有檔含 user 已填真值一律不動——--force 也不重置）。"""
    path = _sec_path(secrets_dir, name)
    clear_dir_placeholder(path)
    if os.path.isfile(path):
        status[name] = "SKIPPED"
    else:
        _write(path, value.encode("utf-8"))
        status[name] = "GENERATED"


def _read_leaf(secrets_dir, name):
    """Step 2 取 leaf 現值（bash `PG_PASS="$(cat …)"`；讀不到＝吵鬧失敗 rc 1）。"""
    path = _sec_path(secrets_dir, name)
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as ex:
        print(f"FAIL：讀不到 {path}（{ex}）——composite 無法由 leaf 組合", file=sys.stderr)
        raise GenerateAbort(1) from ex


def _compose_only_missing(secrets_dir):
    """--compose-only 前置斷言（rev4:019 rev4:P5.5）：10 支來源檔在位且非空（`[ -s ]` 語意）。"""
    out = []
    for name in COMPOSE_ONLY_SOURCES:
        path = _sec_path(secrets_dir, name)
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            out.append(name + ".txt")
    return out


def cmd_generate(force=0, compose_only=0, root=None, env=None):
    """生成本體。root／env 皆為測試注入用哨兵——生產面走模組 ROOT 與本行程環境。

    ★root 預設＝ROOT（由 __file__ 推得的 repo 根）而**非 CWD**：compose 以專案目錄（＝repo
    根）解析相對值，本腳本若以 CWD 錨定，自 repo 子目錄執行就與 compose 指向不同目錄，且
    雙方各自 rc=0＝靜默分裂（明文會寫進 CWD 相對目錄、落回 repo 樹內而 guard 掃不到）。
    ★env=None 是哨兵、不得寫成 `env or os.environ`：呼叫端明給空 dict＝「該環境確實沒設」，
    改讀本行程環境會讓「未設」與「已匯出為空」兩分支靜默改判（同共用庫註解）。
    """
    root = ROOT if root is None else root
    secrets_dir, err = resolve_secrets_dir(root, env)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1
    old_umask = os.umask(BIRTH_UMASK)
    try:
        return _generate_body(secrets_dir, force, compose_only)
    except GenerateAbort as ab:
        return ab.code
    finally:
        os.umask(old_umask)


def _generate_body(secrets_dir, force, compose_only):
    """Step 1~5 本體（落點已解析、umask 已就位）。"""
    os.makedirs(secrets_dir, exist_ok=True)

    if compose_only:
        missing = _compose_only_missing(secrets_dir)
        if missing:
            print("FAIL：--compose-only 缺來源檔（不生成、防靜默造新亂數）："
                  + " ".join(missing), file=sys.stderr)
            print("      → 先跑 python3 deploy/decrypt-secrets.py 重建 10 支"
                  "（9 leaf＋alert_webhook_url）後重試。", file=sys.stderr)
            return 1

    ensure_image()
    status = {}

    # ── Step 1: leaf secret ×9 ──────────────────────────────────────────────
    print("=== Step 1: 生成 leaf secret ===")
    if not compose_only:
        for name, rand_args in LEAF_SPECS:
            gen_leaf(secrets_dir, name, rand_args, force, status)
    else:
        # --compose-only：前置斷言已證 9 leaf 在位非空、此處只記狀態（不生成、不改動）
        for name in LEAF_NAMES:
            status[name] = "PRESENT"

    # ── Step 2: composite secret ×3（由 leaf 組合、dual-write 連動）─────────
    print("=== Step 2: 生成 composite secret（dual-write 由 leaf 組合）===")
    leaf_blobs = {leaf: _read_leaf(secrets_dir, leaf) for _c, leaf, _t in COMPOSITES}
    for name, leaf, tmpl in COMPOSITES:
        gen_composite(secrets_dir, name, compose_expected(leaf_blobs[leaf], tmpl),
                      force, status)

    # ── Step 3: 佔位 secret ×1（user 自填、--force 不重置）───────────────────
    print("=== Step 3: 佔位 secret（真值 user 自填）===")
    if not compose_only:
        gen_placeholder(secrets_dir, PLACEHOLDER_NAME, PLACEHOLDER_VALUE, status)
    else:
        # --compose-only：前置斷言已證在位非空（值多為 user 已填真值、絕不動）
        status[PLACEHOLDER_NAME] = "PRESENT"

    # ── Step 4: 權限收斂（rev4:019 rev4:T026／rev4:P4.7）─────────────────────
    # WSL2 drvfs（/mnt/*）上 chmod 為 no-op、仍照做（原生 Linux 檔系統正確生效）。
    os.chmod(secrets_dir, DIR_MODE)
    for path in globmod.glob(os.path.join(secrets_dir, "*.txt")):
        os.chmod(path, FILE_MODE)

    # ── Step 5: 摘要（只印檔名＋狀態、絕不印值）──────────────────────────────
    print("")
    print("=== Secret 生成摘要 ===")
    for name in SUMMARY_ORDER:
        print(f"  {name + '.txt':<26} {status[name]}")
    print("")
    print(f"完成。{secrets_dir}/*.txt 已就緒（明文不進版本庫）。")
    return 0


# ---------------------------------------------------------------------------
# 自測（test 子命令）：離線、stdlib-only、不需 docker，一律隔離暫存目錄
# ---------------------------------------------------------------------------

# 假 docker 樁：把 argv 記進 RV5_STUB_LOG，並以呼叫序號產出確定性「亂數」——確定性是等價
# 矩陣的地基（真亂數不可重現，只能拆層比對；同一分支序列 → 同一值序列 → 全目錄逐位元組可比）。
# ★樁一律走 PATH 注入、生產碼零測試接縫：亂數來源若留成可注入參數，「改用 python 亂數」
#   就只是換一個預設值的事，逐字紀律一當場失守。
DOCKER_STUB = (
    "#!/usr/bin/env python3\n"
    "import os, sys\n"
    "argv = sys.argv[1:]\n"
    "log = os.environ.get('RV5_STUB_LOG')\n"
    "if log:\n"
    "    open(log, 'a', encoding='utf-8').write(' '.join(argv) + '\\n')\n"
    "if argv[:2] == ['image', 'inspect']:\n"
    "    sys.exit(0 if os.environ.get('RV5_STUB_CACHED', '1') == '1' else 1)\n"
    "if argv[:1] == ['pull']:\n"
    "    sys.exit(int(os.environ.get('RV5_STUB_PULL_RC', '0')))\n"
    "if argv[:1] == ['run']:\n"
    "    rc = int(os.environ.get('RV5_STUB_RUN_RC', '0'))\n"
    "    if rc:\n"
    "        sys.exit(rc)\n"
    "    ctr = os.environ['RV5_STUB_CTR']\n"
    "    n = (int(open(ctr).read() or '0') if os.path.exists(ctr) else 0) + 1\n"
    "    open(ctr, 'w').write(str(n))\n"
    "    print('%s%s-%04d' % (argv[-2].lstrip('-'), argv[-1], n))\n"
    "    sys.exit(0)\n"
    "sys.exit(2)\n")


def _install_docker_stub(d):
    """在 d/bin 裝假 docker 並回（bin 目錄, log 路徑, 計數器路徑）。"""
    bindir = os.path.join(d, "bin")
    os.makedirs(bindir, exist_ok=True)
    stub = os.path.join(bindir, "docker")
    with open(stub, "w", encoding="utf-8") as fh:
        fh.write(DOCKER_STUB)
    os.chmod(stub, 0o755)
    return bindir, os.path.join(d, "docker.log"), os.path.join(d, "docker.ctr")


@contextlib.contextmanager
def _stubbed(d, **extra):
    """把假 docker 掛上 PATH 的情境管理器（樁環境變數一併注入）。"""
    bindir, log, ctr = _install_docker_stub(d)
    patch = dict(os.environ, PATH=bindir + os.pathsep + os.environ.get("PATH", ""),
                 RV5_STUB_LOG=log, RV5_STUB_CTR=ctr, **extra)
    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(patch)
    try:
        yield log
    finally:
        os.environ.clear()
        os.environ.update(old)


def _sandbox_holds_modes(d):
    """暫存沙盒能否承載 644（drvfs 上 chmod 結構性 no-op、mode 恆讀 777）。"""
    probe = os.path.join(d, ".mode-probe")
    with open(probe, "w"):
        pass
    os.chmod(probe, 0o644)
    held = (os.stat(probe).st_mode & 0o777) == FILE_MODE
    os.remove(probe)
    return held


_DRVFS_SKIP = ("暫存沙盒在 drvfs（chmod 結構性 no-op、mode 恆讀 777）——權限終值改由原生 fs "
               "上的等價矩陣覆蓋；把 TMPDIR 指到 ext4 即可跑本案")


def _seed(secrets_dir, names=None, overrides=None):
    """在隔離暫存目錄預置一份一致的十三機密（固定值＝決定性面可逐位元組比對）。

    names＝要建的名稱集（None＝十三支全建）；overrides＝{名稱: 位元組}。
    ★呼叫端一律傳 tempfile 目錄——本函式會覆寫，指向真落點即毀機密。
    """
    values = {name: ("seed-" + name).encode("utf-8") for name in LEAF_NAMES}
    values[PLACEHOLDER_NAME] = PLACEHOLDER_VALUE.encode("utf-8")
    for name, leaf, tmpl in COMPOSITES:
        values[name] = tmpl.replace(b"{}", values[leaf])
    values.update(overrides or {})
    os.makedirs(secrets_dir, exist_ok=True)
    for name in (SUMMARY_ORDER if names is None else names):
        with open(_sec_path(secrets_dir, name), "wb") as fh:
            fh.write(values[name])
    return values


def _blob(secrets_dir, name):
    with open(_sec_path(secrets_dir, name), "rb") as fh:
        return fh.read()


def _statuses(out):
    """摘要段解析：回 {名稱: 狀態}（只認 `  <名>.txt<空白><狀態>` 那 13 列）。"""
    got = {}
    known = {name + ".txt": name for name in SUMMARY_ORDER}
    for line in out.splitlines():
        parts = line.split()
        # ★收窄到「兩欄且首欄是名冊檔名」：只判尾綴 `.txt` 會把收尾那行
        #   「完成。<落點>/*.txt 已就緒…」也吃進來（實測多出第 14 筆假狀態）
        if len(parts) == 2 and parts[0] in known and line.startswith("  "):
            got[known[parts[0]]] = parts[1]
    return got


class TestRosterPinned(unittest.TestCase):
    """★名冊與三條逐字紀律的字面釘死：以被測常數迭代出期望值＝套套邏輯（常數縮水時斷言
    跟著縮水、全綠存活）。這三條是 B-037 明載「違者即 blocker」的項目，逐字列出。"""

    def test_leaf_roster_and_rand_args_are_pinned(self):
        """★次序即 docker 調用次序：改序＝等價矩陣的 argv 序列比對當場失真。"""
        self.assertEqual(LEAF_SPECS, (
            ("postgres_password", ("-hex", "24")),
            ("redis_password", ("-hex", "24")),
            ("jwt_secret", ("-base64", "48")),
            ("refresh_token_secret", ("-base64", "48")),
            ("captcha_secret", ("-base64", "48")),
            ("reaper_password", ("-hex", "24")),
            ("grafana_admin_password", ("-base64", "24")),
            ("smtp_password", ("-base64", "24")),
            ("email_verify_secret", ("-base64", "48"))))
        self.assertEqual(len(LEAF_SPECS), 9)

    def test_summary_roster_is_pinned(self):
        """十三機密與摘要列印次序逐字釘死（少一支＝該支永不生成也永不出現在摘要）。"""
        self.assertEqual(SUMMARY_ORDER, (
            "postgres_password", "redis_password", "jwt_secret", "refresh_token_secret",
            "captcha_secret", "reaper_password", "grafana_admin_password", "smtp_password",
            "email_verify_secret", "database_url", "redis_url", "reaper_database_url",
            "alert_webhook_url"))
        self.assertEqual(len(SUMMARY_ORDER), 13)

    def test_composite_formulas_are_pinned(self):
        """逐字紀律三：三條組合式在本檔自持一份（與 preflight 各寫一份、不得順手合併）。"""
        self.assertEqual(COMPOSITES, (
            ("database_url", "postgres_password",
             b"postgres://soybean:{}@postgres:5432/soybean_admin_rust"),
            ("redis_url", "redis_password", b"redis://:{}@redis:6379"),
            ("reaper_database_url", "reaper_password",
             b"postgres://reaper:{}@postgres:5432/soybean_admin_rust")))

    def test_placeholder_literal_is_pinned(self):
        """逐字紀律二（ADR 0003 三處同字面記帳之一）：改佔位值必同刀改 preflight 的
        PLACEHOLDER_LITERALS 與 secret-value-guard 的 PLACEHOLDER_VALUES 白名單。

        ★期望值執行期串接構造：完整字面在本檔已出現於生產常數一次（本檔＝唯一佔位源頭），
        測試再抄一次會讓「值比對層掃描」與「勘誤枚舉」多一個必須同步的點。
        """
        self.assertEqual(PLACEHOLDER_NAME, "alert_webhook_url")
        self.assertEqual(PLACEHOLDER_VALUE,
                         "https://CHANGE-ME" + ".invalid/alert-webhook-placeholder")

    def test_random_source_is_docker_openssl_verbatim(self):
        """逐字紀律一：亂數＝docker alpine/openssl rand，調用形沿舊檔逐字。"""
        self.assertEqual(OPENSSL_IMG, "alpine/openssl" + ":latest")
        self.assertEqual(docker_rand_argv(("-hex", "24")),
                         ["docker", "run", "--rm", "alpine/openssl:latest", "rand",
                          "-hex", "24"])
        self.assertEqual(docker_rand_argv(("-base64", "48"))[-2:], ["-base64", "48"])

    def test_no_python_random_module_is_imported(self):
        """★逐字紀律一的反向鎖：改用 python 亂數模組＝行為變更＋host 依賴姿態變，絕不做。

        ★樣式執行期串接構造：字面寫死會讓本斷言自己命中自己（同 preflight 慣例）。
        """
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        for mod in ("secrets", "random"):
            self.assertNotIn("\nimport " + mod + "\n", src, msg=f"亂數來源不得改 {mod} 模組")
        self.assertNotIn("urand" + "om(", src, msg="亂數來源不得改 os.urandom")

    def test_root_is_anchored_on_file_not_cwd(self):
        """★落點錨定基準＝由 __file__ 推得的 repo 根，非 CWD：改吃 CWD 即「自子目錄執行時
        把明文機密寫進 CWD 相對目錄」（bash 版 REPO_ROOT 同義）。"""
        self.assertEqual(ROOT, os.path.dirname(HERE))
        self.assertEqual(os.path.basename(HERE), "deploy")
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("get" + "cwd", src, msg="落點錨定改吃 CWD＝寫錯落點的靜默分裂")


class TestPurePredicates(unittest.TestCase):
    """純判定面（零 IO、零 docker）。"""

    def test_compose_expected_strips_trailing_lf_only(self):
        """bash `$(cat)` 剝的是尾端換行（可多個）——前導與中段一律不動。

        ★期望值一律執行期串接：完整 DSN 字面會被機密樣式掃描判成憑證 URL（實測 betterleaks
        規則 rev5-dsn-credential-url 命中、pre-commit 硬擋）；模板常數帶 `{}` 故不自命中。
        """
        self.assertEqual(compose_expected(b"pw\n\n", COMPOSITES[1][2]),
                         b"redis" + b"://:pw@redis:6379")
        self.assertEqual(compose_expected(b" pw ", COMPOSITES[1][2]),
                         b"redis" + b"://: pw @redis:6379")

    def test_compose_only_sources_exclude_composites(self):
        """--compose-only 的來源集＝9 leaf＋佔位；composite 不在其中（它們是重組標的）。"""
        self.assertEqual(COMPOSE_ONLY_SOURCES, LEAF_NAMES + ("alert_webhook_url",))
        self.assertEqual(len(COMPOSE_ONLY_SOURCES), 10)
        for name, _leaf, _tmpl in COMPOSITES:
            self.assertNotIn(name, COMPOSE_ONLY_SOURCES)


class TestGeneratePipeline(unittest.TestCase):
    """決策矩陣整合（假 docker 樁、隔離暫存 SECRETS_DIR）。

    ★SECRETS_DIR 一律由本測試寫死並明給——絕不取自環境（B-037 明載）：--force 若落到真
    落點就是把 dev stack 的十二支機密當場重生，preflight 之後才會發現。
    """

    def _run(self, secrets_dir, force=0, compose_only=0):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cmd_generate(force=force, compose_only=compose_only,
                              root=os.path.join(tempfile.gettempdir(), "no-such-root"),
                              env={"SECRETS_DIR": secrets_dir})
        return rc, out.getvalue(), err.getvalue()

    def test_all_missing_generates_thirteen(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            st = _statuses(out)
            self.assertEqual(len(st), 13)
            self.assertEqual(set(st.values()), {"GENERATED"})
            self.assertEqual(_blob(sd, PLACEHOLDER_NAME),
                             PLACEHOLDER_VALUE.encode("utf-8"))

    def test_second_run_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            self._run(sd)
            before = {n: _blob(sd, n) for n in SUMMARY_ORDER}
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertEqual(set(_statuses(out).values()), {"SKIPPED"})
            self.assertEqual({n: _blob(sd, n) for n in SUMMARY_ORDER}, before)

    def test_missing_single_leaf_regenerates_and_rewrites_composite(self):
        """★dual-write 連動：leaf 重生 → 內嵌它的 composite 必連動重寫，絕不留兩處不一致。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd)
            os.remove(_sec_path(sd, "postgres_password"))
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            st = _statuses(out)
            self.assertEqual(st["postgres_password"], "GENERATED")
            self.assertEqual(st["database_url"], "GENERATED")
            self.assertEqual(st["redis_url"], "SKIPPED")
            self.assertEqual(_blob(sd, "database_url"),
                             compose_expected(_blob(sd, "postgres_password"),
                                              COMPOSITES[0][2]))

    def test_missing_single_composite_is_recomposed_from_leaf(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d) as log:
            sd = os.path.join(d, "secrets")
            _seed(sd)
            os.remove(_sec_path(sd, "redis_url"))
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            st = _statuses(out)
            self.assertEqual(st["redis_url"], "GENERATED")
            self.assertEqual(st["redis_password"], "SKIPPED")
            self.assertEqual(_blob(sd, "redis_url"),
                             b"redis" + b"://:seed-redis_password@redis:6379")
            # composite 由 leaf 組合、絕不獨立亂數生成：本情境零 `docker run`
            with open(log, encoding="utf-8") as fh:
                self.assertEqual([ln for ln in fh.read().splitlines()
                                  if ln.startswith("run ")], [])

    def test_leaf_drift_triggers_composite_rewrite_with_named_message(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd, overrides={"postgres_password": b"rotated-out-of-band"})
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertIn("database_url.txt 與依賴 leaf 不一致（dual-write drift）", out)
            self.assertEqual(_statuses(out)["database_url"], "GENERATED")
            self.assertEqual(_blob(sd, "database_url"),
                             b"postgres" + b"://soybean:rotated-out-of-band"
                             b"@postgres:5432/soybean_admin_rust")

    def test_trailing_lf_on_composite_is_byte_level_drift(self):
        """★尾端多一個 LF：字串相等比較對它失明（rev4:P5.7 不變式失效）——位元組比對才擋得住。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd)
            with open(_sec_path(sd, "redis_url"), "ab") as fh:
                fh.write(b"\n")
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertEqual(_statuses(out)["redis_url"], "GENERATED")
            self.assertEqual(_blob(sd, "redis_url"),
                             b"redis" + b"://:seed-redis_password@redis:6379")

    def test_force_regenerates_twelve_but_never_the_placeholder(self):
        """★--force 專測（SECRETS_DIR 寫死於本測試、絕不取自環境）：亂數十二支全重生，
        alert_webhook_url 屬 user 自填設定值、不在範圍（重生佔位無輪替價值、反毀真值）。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd, overrides={PLACEHOLDER_NAME: b"https://real.example/hook"})
            before = {n: _blob(sd, n) for n in SUMMARY_ORDER}
            rc, out, err = self._run(sd, force=1)
            self.assertEqual(rc, 0, msg=out + err)
            st = _statuses(out)
            self.assertEqual(st[PLACEHOLDER_NAME], "SKIPPED")
            self.assertEqual(_blob(sd, PLACEHOLDER_NAME), b"https://real.example/hook")
            for name in SUMMARY_ORDER:
                if name == PLACEHOLDER_NAME:
                    continue
                self.assertEqual(st[name], "GENERATED", msg=name)
                self.assertNotEqual(_blob(sd, name), before[name], msg=name)

    def test_compose_only_recomposes_without_touching_leaves(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd, overrides={"redis_password": b"rotated-leaf"})
            leaves = {n: _blob(sd, n) for n in COMPOSE_ONLY_SOURCES}
            rc, out, err = self._run(sd, compose_only=1)
            self.assertEqual(rc, 0, msg=out + err)
            st = _statuses(out)
            self.assertEqual([st[n] for n in COMPOSE_ONLY_SOURCES], ["PRESENT"] * 10)
            self.assertEqual(st["redis_url"], "GENERATED")
            self.assertEqual(st["database_url"], "SKIPPED")
            self.assertEqual({n: _blob(sd, n) for n in COMPOSE_ONLY_SOURCES}, leaves)

    def test_compose_only_missing_leaf_fails_and_generates_nothing(self):
        """★缺來源檔一律報錯退出、絕不代生成——防靜默造新亂數（每台機器各拿到不同值、
        與加密檔脫鉤）。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d) as log:
            sd = os.path.join(d, "secrets")
            _seed(sd)
            os.remove(_sec_path(sd, "jwt_secret"))
            rc, out, err = self._run(sd, compose_only=1)
            self.assertEqual(rc, 1)
            self.assertIn("--compose-only 缺來源檔", err)
            self.assertIn("jwt_secret.txt", err)
            self.assertEqual(out, "")
            self.assertFalse(os.path.exists(_sec_path(sd, "jwt_secret")))
            self.assertFalse(os.path.exists(log))   # 連 image inspect 都還沒發

    def test_compose_only_missing_placeholder_also_fails(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd)
            os.remove(_sec_path(sd, PLACEHOLDER_NAME))
            rc, _out, err = self._run(sd, compose_only=1)
            self.assertEqual(rc, 1)
            self.assertIn("alert_webhook_url.txt", err)

    def test_compose_only_empty_source_counts_as_missing(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd, overrides={"captcha_secret": b""})
            rc, _out, err = self._run(sd, compose_only=1)
            self.assertEqual(rc, 1)
            self.assertIn("captcha_secret.txt", err)

    def test_dir_placeholder_is_cleared_then_regenerated(self):
        """compose 對缺 bind source 自動建的空目錄殘骸：自動清除、續生成（恢復路徑自足）。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd)
            os.remove(_sec_path(sd, "jwt_secret"))
            os.makedirs(_sec_path(sd, "jwt_secret"))
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertIn("jwt_secret.txt 為目錄佔位", out)
            self.assertEqual(_statuses(out)["jwt_secret"], "GENERATED")
            self.assertTrue(os.path.isfile(_sec_path(sd, "jwt_secret")))

    def test_nonempty_dir_placeholder_is_named_and_blocks(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            _seed(sd)
            os.remove(_sec_path(sd, "jwt_secret"))
            os.makedirs(os.path.join(_sec_path(sd, "jwt_secret"), "sub"))
            rc, _out, err = self._run(sd)
            self.assertEqual(rc, 1)
            self.assertIn("是非空目錄（無法自動清除）", err)

    def test_permission_convergence_dir_700_files_644(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            if not _sandbox_holds_modes(d):
                self.skipTest(_DRVFS_SKIP)
            sd = os.path.join(d, "secrets")
            rc, out, err = self._run(sd)
            self.assertEqual(rc, 0, msg=out + err)
            self.assertEqual(os.stat(sd).st_mode & 0o777, DIR_MODE)
            for name in SUMMARY_ORDER:
                self.assertEqual(os.stat(_sec_path(sd, name)).st_mode & 0o777, FILE_MODE,
                                 msg=name)

    def test_values_carry_no_newline(self):
        """`printf '%s'` 寫檔形＝零換行（尾端一個 LF 就會讓容器拿到與 composite 不符的值）。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d):
            sd = os.path.join(d, "secrets")
            self._run(sd)
            for name in SUMMARY_ORDER:
                self.assertNotIn(b"\n", _blob(sd, name), msg=name)

    def test_docker_argv_sequence_is_image_probe_then_nine_rands(self):
        """★亂數調用 argv 序列（逐字紀律一的機器投影）：image inspect 一發＋九發 rand。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d) as log:
            sd = os.path.join(d, "secrets")
            self._run(sd)
            with open(log, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            self.assertEqual(lines[0], f"image inspect {OPENSSL_IMG}")
            self.assertEqual(lines[1:], [
                "run --rm " + OPENSSL_IMG + " rand " + " ".join(a)
                for _n, a in LEAF_SPECS])

    def test_image_pull_only_when_not_cached(self):
        """離線／限流時 image 已 cache 則免 pull（`docker pull` 在 set -e 下會 abort）。"""
        with tempfile.TemporaryDirectory() as d, _stubbed(d, RV5_STUB_CACHED="0") as log:
            self._run(os.path.join(d, "secrets"))
            with open(log, encoding="utf-8") as fh:
                self.assertIn(f"pull -q {OPENSSL_IMG}", fh.read())

    def test_pull_failure_propagates_exit_code(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d, RV5_STUB_CACHED="0",
                                                          RV5_STUB_PULL_RC="7"):
            rc, _out, _err = self._run(os.path.join(d, "secrets"))
            self.assertEqual(rc, 7)

    def test_rand_failure_propagates_exit_code(self):
        with tempfile.TemporaryDirectory() as d, _stubbed(d, RV5_STUB_RUN_RC="3"):
            rc, _out, _err = self._run(os.path.join(d, "secrets"))
            self.assertEqual(rc, 3)

    def test_missing_docker_is_named_and_exits_127(self):
        """docker 不可得＝指名真因、rc 127（bash 側由 shell 的 command-not-found 給同一碼）。"""
        with tempfile.TemporaryDirectory() as d:
            old = dict(os.environ)
            os.environ["PATH"] = os.path.join(d, "empty-bin")
            try:
                rc, _out, err = self._run(os.path.join(d, "secrets"))
            finally:
                os.environ.clear()
                os.environ.update(old)
            self.assertEqual(rc, 127)
            self.assertIn("docker", err)

    def test_exported_empty_secrets_dir_is_loud_failure(self):
        """★空字串邊界：「已匯出但為空」≠「未設」——compose 對空字串吃預設值回退 repo 內
        舊落點且不讀 .env；當未設而續讀 .env 即「腳本寫新落點、compose 掛舊落點」的靜默分裂。"""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cmd_generate(root=os.path.join(tempfile.gettempdir(), "no-such-root"),
                              env={"SECRETS_DIR": ""})
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", err.getvalue())
        self.assertEqual(out.getvalue(), "")

    def test_env_file_relative_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, ".env"), "w", encoding="utf-8") as fh:
                fh.write("SECRETS_DIR=deploy/secrets\n")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = cmd_generate(root=d, env={})
            self.assertEqual(rc, 1)
            self.assertIn("絕對路徑", err.getvalue())
            self.assertFalse(os.path.isdir(os.path.join(d, "deploy", "secrets")))


class TestCli(unittest.TestCase):
    """旗標解析（逐字沿舊檔 `case "${1:-}"`）。"""

    def test_flags(self):
        self.assertEqual(parse_flag([]), (0, 0, None))
        self.assertEqual(parse_flag(["--force"]), (1, 0, None))
        self.assertEqual(parse_flag(["--compose-only"]), (0, 1, None))

    def test_unknown_flag_is_usage_error(self):
        self.assertEqual(parse_flag(["--nope"])[2], "--nope")

    def test_only_first_arg_is_inspected(self):
        """★逐字保留 bash 版行為：`case "${1:-}"` 只看 $1，其後多帶引數一律忽略、不報錯。"""
        self.assertEqual(parse_flag(["--force", "extra"]), (1, 0, None))

    def test_main_rejects_unknown_flag_with_64(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = main(["deploy/generate-secrets.py", "--nope"])
        self.assertEqual(rc, 64)
        self.assertIn("[--force|--compose-only]", err.getvalue())


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def parse_flag(args):
    """回 (force, compose_only, 用法錯誤的引數字面 or None)——逐字沿舊檔 `case "${1:-}"`。"""
    first = args[0] if args else ""
    if first == "--force":
        return 1, 0, None
    if first == "--compose-only":
        return 0, 1, None
    if first == "":
        return 0, 0, None
    return 0, 0, first


def usage(argv0, msg=None):
    """用法錯誤：走 stderr、rc 64（EX_USAGE；bash 版 `exit 64` 同碼）。"""
    if msg:
        print(msg, file=sys.stderr)
    print(f"用法：{argv0} [--force|--compose-only]", file=sys.stderr)
    return 64


def main(argv):
    args = argv[1:]
    cmd = args[0] if args else ""
    if cmd == "test":
        if args[1:]:
            return usage(argv[0], f"test：不收額外參數（見 {' '.join(args[1:])}）")
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    force, compose_only, bad = parse_flag(args)
    if bad is not None:
        return usage(argv[0])
    return cmd_generate(force=force, compose_only=compose_only)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
