#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/setup-reaper-role.py — reaper role 設密＋LOGIN（ADR 0010 轉換批③、B-037 U2）

等價重寫自 deploy/setup-reaper-role.sh：對 docker 的 argv 序列、餵入 psql 的 stdin payload、
rc 逐分支與 stdout／stderr 分工皆逐位元組對應；唯一實作收斂＝落點解析改用共用庫
deploy/secrets_common.py（同 preflight／decrypt／generate 先例，落點解析兩型失敗的訊息字面
隨之收斂到共用庫版本，rc 與串流不變）。

分工（data-model §5、rev4:research R5、rev4:ADR 0072）：
  rev4:m012 migration＝CREATE ROLE reaper NOLOGIN＋GRANT（零密碼）；本腳本＝ALTER ROLE reaper
  LOGIN PASSWORD（密碼讀自 $SECRETS_DIR/reaper_password.txt；★rev4:019 rev4:US3 起落點由 repo
  根 .env 的 SECRETS_DIR 決定、未設才回退 repo 內 deploy/secrets——解析口徑見共用庫）。
密碼紀律（rev4:FR-013）：SQL 走 psql stdin——密碼零進 host process list、零進版本庫；
  輸出只印狀態不印值。可重跑（ALTER ROLE 冪等）。
前置：stack 已 up（postgres healthy）＋rev4:m012 已套用（role 不存在→psql 非零退出 fail-loud）
  ＋deploy/generate-secrets.py 已產 reaper_password.txt。

用法：python3 deploy/setup-reaper-role.py

子命令：
  （無引數）  設密＋LOGIN 後以 reaper 憑證自驗 SELECT 1。
  test        跑自帶測試（unittest、離線、stdlib-only、不需 docker；一律隔離暫存目錄，
              SECRETS_DIR 與密碼字面一律寫死於測試內、絕不取自環境——防碰真落點）。

退出碼：正常結束 0；落點解析失敗／密碼檔缺席或空／自驗回值非 1 皆 1；用法錯誤 64
        （EX_USAGE；沿 deploy/preflight-secrets.py 家族慣例——舊 .sh 無引數面故無此碼，
        詳見 main() 註解）；docker 不可得 127（＝shell 的 command-not-found 碼）；
        docker 本身非零＝原樣透傳（兩發各自透傳）。

★python 化的主要收益＝**密碼傳遞由 API 形參保證**（B-037 明載）：兩發 docker 調用一律
  `subprocess.run(argv=list, input=bytes)`——argv 是 list 不是字串（零 shell 解析）、密碼只走
  stdin pipe，絕不進 shell 字串拼接／命令列引數／環境變數。bash 版靠「heredoc 與管線寫對」
  這個人為紀律達成同一件事，python 版把它變成呼叫形參的結構性保證：想把密碼放進 argv 得先
  改掉函式簽章，不會是手滑。
"""
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 落點解析共用庫（ADR 0010 轉換批①）：五消費者單一實作面。
# ★以 __file__ 推出的絕對路徑載入：不依賴 CWD（本腳本常自 repo 子目錄叫用），也不把
#   deploy/ 塞進 sys.path（避免搜尋路徑遮蔽）。
# ★載入失敗＝印真因後原樣拋（fail-loud）：落點解析錯了就是去別的目錄找密碼檔，靜默降級
#   遠比當場炸危險。
_SECRETS_COMMON_PATH = os.path.join(HERE, "secrets_common.py")
try:
    _spec = importlib.util.spec_from_file_location("secrets_common", _SECRETS_COMMON_PATH)
    _secrets_common = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_secrets_common)
except Exception as _ex:
    print(f"[setup-reaper-role] ERROR 載入共用庫 {_SECRETS_COMMON_PATH} 失敗：{_ex}"
          "——落點解析不得靜默降級（讀錯落點＝拿到別處的舊密碼、ALTER 後認證全掛）",
          file=sys.stderr)
    raise

resolve_secrets_dir = _secrets_common.resolve_secrets_dir

PW_NAME = "reaper_password.txt"

# compose 前綴（逐字沿舊檔 `COMPOSE=(docker compose -f … -f …)`）：兩發共用同一序列。
COMPOSE_ARGV = ("docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")

# 第一發：設密（psql 沿 tools/schema-gate.py 的 `exec -T` 慣例）。★旗標次序即 argv 序列，
# 等價矩陣以假 docker 樁逐位元組比對新舊——重排「看起來比較整齊」＝矩陣當場紅。
PSQL_ARGV_TAIL = ("exec", "-T", "postgres", "psql", "-v", "ON_ERROR_STOP=1",
                  "-U", "soybean", "-d", "soybean_admin_rust",
                  "--quiet", "--no-align", "--tuples-only")

# 第二發：自驗——★必走 -h postgres 容器網段（scram 真驗密）；容器內 127.0.0.1 在 pg_hba 屬
# trust、密碼不參與認證＝驗不到密碼（rev4:L-154）。與 reaper_database_url 同認證路徑
# （host=postgres、scram-sha-256）。密碼經 stdin 管線交給容器內 read→PGPASSWORD env
# （env 只存在於容器內該行程、不進 host process list）。
# ★此字串是**容器內** sh 的腳本文字、不是 host shell 拼接：它以 argv 單一元素傳入，host 側
#   零 shell 解析；密碼不在其中（由 stdin 進 read）。
VERIFY_SH = ('read -r RPW; PGPASSWORD="$RPW" '
             'psql -h postgres -U reaper -d soybean_admin_rust -Atc "SELECT 1"')
VERIFY_ARGV_TAIL = ("exec", "-T", "postgres", "sh", "-c", VERIFY_SH)

# ALTER ROLE 的 SQL 形（逐字紀律）：舊檔 heredoc 本體＝
#   ALTER ROLE reaper LOGIN PASSWORD '${PW}';
# 加結尾換行。★密碼**原樣**嵌在單引號內、不做任何跳脫——這是舊檔行為，照抄不動：
#   ①由來（L-004 先查再動）：密碼由 deploy/generate-secrets.py 以 `openssl rand -hex 24`
#     產生，值域＝[0-9a-f]，單引號／反斜線結構性不可能出現；
#   ②B-037 U2 明載「ALTER ROLE 的 SQL 形一個字元都不能漂」，效果等價由主線真 stack 一輪另驗，
#     此處任何「順手補跳脫」都會讓新舊 stdin payload 分岔、且真 stack 那輪失去可比基準。
#   ★已知極限（等價矩陣情境④實證、非本刀處理面）：手改成含單引號的密碼會產出語法破裂的
#     SQL、psql 非零退出（fail-loud、不是靜默錯設），與舊檔同一行為。要改成 dollar-quoting
#     屬**行為變更**，須走 ADR 拍板、不在等價重寫射程內。
SQL_ALTER_HEAD = b"ALTER ROLE reaper LOGIN PASSWORD '"
SQL_ALTER_TAIL = b"';\n"

# 自驗期望回值（`[ "$RESULT" = "1" ]`）。
VERIFY_EXPECT = b"1"


class SetupAbort(Exception):
    """中止流程並帶出退出碼（等價於 bash 版 `set -e` 與顯式 exit 的合流出口）。"""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def psql_argv():
    """第一發 argv（設密）。"""
    return list(COMPOSE_ARGV) + list(PSQL_ARGV_TAIL)


def verify_argv():
    """第二發 argv（自驗）。"""
    return list(COMPOSE_ARGV) + list(VERIFY_ARGV_TAIL)


def alter_role_sql(pw):
    """設密 SQL payload（位元組）＝舊檔 heredoc 本體逐位元組；pw 原樣嵌入（見上方註解）。"""
    return SQL_ALTER_HEAD + pw + SQL_ALTER_TAIL


def verify_stdin(pw):
    """自驗 stdin payload（位元組）＝舊檔 `printf '%s\\n' "$PW"`。"""
    return pw + b"\n"


def read_password(pw_file):
    """讀密碼位元組；缺席／空檔→None（舊檔 `[ ! -s "$PW_FILE" ]` 判定）。

    ★尾端換行剝**全部**：舊檔 `PW="$(cat "$PW_FILE")"` 是命令替換語意（剝掉所有尾端 LF），
    不是剝一個——密碼檔被編輯器多補一行時，剝一個會把 `\\n` 送進 SQL 字面（等價矩陣情境⑨）。
    """
    try:
        if os.stat(pw_file).st_size <= 0:
            return None
    except OSError:
        return None
    try:
        with open(pw_file, "rb") as fh:
            return fh.read().rstrip(b"\n")
    except OSError as ex:
        # `-s` 對目錄為真（size>0），舊檔會走到 `cat` 失敗、set -e 退 1；此處同碼同串流。
        print(f"錯誤：{pw_file} 讀取失敗（{ex}）", file=sys.stderr)
        raise SetupAbort(1) from ex


def _run(argv, payload, capture, cwd):
    """跑外部命令並自 stdin 餵 payload（★密碼只走這條路：argv 是 list、payload 是 bytes）。

    capture=True 才收 stdout（stderr 一律原樣透傳給呼叫端終端，與舊檔同分工）。
    ★cwd＝repo 根、**必傳**（家族先例＝deploy/decrypt-secrets.py 的 run_sops）：舊檔首行
    `cd "$(dirname "$0")/.."` 有兩個職責——①落點相對值的錨定基準②`docker compose -f
    docker-compose.yml -f docker-compose.dev.yml` 這兩個**相對**路徑的解析基準。②靠的是
    子行程繼承的 CWD，python 這側不傳 cwd 就會繼承呼叫端 CWD、隨叫用位置漂：自 repo 子目錄
    叫用即 `open /docker-compose.yml: no such file or directory`；更壞的情況是呼叫端 CWD 恰有
    另一組同名 compose 檔（服務名含 postgres），reaper 密碼會被 ALTER 到別的 stack 去。
    ★argv 不因此變動一個位元組——等價矩陣比的是 argv 與 stdin payload，比不到子行程 CWD，
    故此處另立測試釘死（test_child_cwd_is_root_regardless_of_caller_cwd）。
    """
    # ★送出前 flush：本行程 stdout 被導向檔案／管線時是塊緩衝，而子行程直接寫 fd 1——
    #   不 flush 則兩者輸出次序會與 bash 版（echo 即時寫出）相反。
    sys.stdout.flush()
    try:
        return subprocess.run(argv, input=payload, cwd=cwd,
                              stdout=subprocess.PIPE if capture else None)
    except OSError as ex:
        print(f"FAIL：無法執行 {argv[0]}（{ex}）——本腳本一律透過 docker compose 進容器"
              "（host 除 docker 外零依賴）", file=sys.stderr)
        raise SetupAbort(127) from ex


def set_password(pw, root):
    """第一發：ALTER ROLE 設密＋LOGIN。非零退出＝原樣透傳 rc（舊檔 set -e）。"""
    r = _run(psql_argv(), alter_role_sql(pw), capture=False, cwd=root)
    if r.returncode != 0:
        raise SetupAbort(r.returncode)
    print("ok: role reaper 已設 LOGIN＋密碼（值不回顯）")


def verify_login(pw, root):
    """第二發：以 reaper 憑證 SELECT 1。回值非 `1`＝指名退 1；docker 非零＝原樣透傳。"""
    r = _run(verify_argv(), verify_stdin(pw), capture=True, cwd=root)
    if r.returncode != 0:
        raise SetupAbort(r.returncode)
    # 舊檔 `RESULT="$(…)"` 是命令替換：剝掉所有尾端 LF 後才比對。
    result = r.stdout.rstrip(b"\n")
    if result == VERIFY_EXPECT:
        print("ok: reaper 憑證連線驗證通過（SELECT 1）")
        return
    # ★回值以位元組原樣寫出（不經 str 轉碼）：psql 回的可能是非 UTF-8 的錯誤片段，
    #   decode 會改字面、也可能自己炸掉——這行是診斷用，形要跟舊檔一模一樣。
    sys.stderr.flush()
    sys.stderr.buffer.write("錯誤：reaper 憑證連線驗證失敗（回值：".encode("utf-8")
                            + result + "）\n".encode("utf-8"))
    sys.stderr.buffer.flush()
    raise SetupAbort(1)


def cmd_setup(root=None, env=None):
    """本體。root／env 皆為測試注入用哨兵——生產面走模組 ROOT 與本行程環境。

    ★root 預設＝ROOT（由 __file__ 推得的 repo 根）而**非 CWD**：舊檔首行 `cd "$(dirname
    "$0")/.."` 就是同一個推導，落點的相對值錨定基準因此與呼叫端 CWD 無關、與 compose 一致。
    ★同一個 root 也是兩發 docker 的子行程 CWD（見 _run 註解）：舊檔那一行 `cd` 一次同時管
    落點錨定與 compose 相對路徑解析，此處以「同源同值」對應——分成兩個來源就會分岔。
    ★env=None 是哨兵、不得寫成 `env or os.environ`：呼叫端明給空 dict＝「該環境確實沒設」，
    改讀本行程環境會讓「未設」與「已匯出為空」兩分支靜默改判（同共用庫註解）。
    """
    root = ROOT if root is None else root
    secrets_dir, err = resolve_secrets_dir(root, env)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1
    pw_file = os.path.join(secrets_dir, PW_NAME)
    try:
        pw = read_password(pw_file)
        if pw is None:
            print(f"錯誤：{pw_file} 缺席或為空（先跑 python3 deploy/decrypt-secrets.py；"
                  "無加密檔情境＝generate-secrets.py）", file=sys.stderr)
            return 1
        set_password(pw, root)
        verify_login(pw, root)
    except SetupAbort as ab:
        return ab.code
    return 0


# ---------------------------------------------------------------------------
# 自測（test 子命令）：離線、stdlib-only、不需 docker，一律隔離暫存目錄
# ---------------------------------------------------------------------------

# 假 docker 樁：把 argv（NUL 分隔、逐位元組）、stdin payload、**子行程 CWD** 與**子行程
# 環境全量**（env.%d；密碼不進環境變數之禁令守衛用）各記一檔，並依
# 呼叫序號決定 rc、stdout 與 stderr——序號化是等價矩陣的地基（同一分支序列 → 同一組檔案 →
# 新舊逐位元組可比）。★CWD 也記：`docker compose -f <相對路徑>` 的解析基準就是它，只比 argv
# 比不到。★stderr（RV5_STUB_ERR_n）是**輸出交錯次序**的探針：docker compose 真跑時會往
#   stderr 印 orphan containers 之類的 warning，兩流併到同一終端時，本行程緩衝的成功訊息
#   有沒有先 flush 出去看得一清二楚（見 test_stdout_order_vs_child_stderr_is_pinned）。
# ★樁一律走 PATH 注入、生產碼零測試接縫：docker 路徑若留成可注入參數，「改用 host psql」
#   就只是換一個預設值的事，「host 除 docker 外零依賴」的姿態當場失守。
DOCKER_STUB = (
    "#!/usr/bin/env python3\n"
    "import os, sys\n"
    "ctr = os.environ['RV5_STUB_CTR']\n"
    "n = (int(open(ctr).read() or '0') if os.path.exists(ctr) else 0) + 1\n"
    "open(ctr, 'w').write(str(n))\n"
    "d = os.environ['RV5_STUB_DIR']\n"
    "with open(os.path.join(d, 'argv.%d' % n), 'wb') as fh:\n"
    "    fh.write(b'\\0'.join(a.encode('utf-8', 'surrogateescape') for a in sys.argv[1:]))\n"
    "with open(os.path.join(d, 'stdin.%d' % n), 'wb') as fh:\n"
    "    fh.write(sys.stdin.buffer.read())\n"
    "with open(os.path.join(d, 'cwd.%d' % n), 'wb') as fh:\n"
    "    fh.write(os.getcwdb())\n"
    "with open(os.path.join(d, 'env.%d' % n), 'wb') as fh:\n"
    "    fh.write(b'\\0'.join(('%s=%s' % kv).encode('utf-8', 'surrogateescape')\n"
    "                         for kv in sorted(os.environ.items())))\n"
    "err = os.environ.get('RV5_STUB_ERR_%d' % n, '')\n"
    "if err:\n"
    "    sys.stderr.buffer.write(err.encode('utf-8'))\n"
    "    sys.stderr.buffer.flush()\n"
    "rc = int(os.environ.get('RV5_STUB_RC_%d' % n, '0'))\n"
    "if rc:\n"
    "    sys.exit(rc)\n"
    "sys.stdout.buffer.write(os.environ.get('RV5_STUB_OUT_%d' % n, '').encode('utf-8'))\n"
    "sys.stdout.buffer.write(bytes.fromhex(os.environ.get('RV5_STUB_OUTHEX_%d' % n, '')))\n"
    "sys.exit(0)\n")

# fixture 密碼字面一律**執行期串接**（同 deploy/generate-secrets.py 慣例）：源碼裡不留成形的
# 密碼字面，憑證掃描面（.githooks pre-commit gitleaks／tools/secret-value-guard.py）零誤報。
_PW_PLAIN = "fixture" + "-" + "reaper" + "-pw"
# 特殊字元組（quoting 等價的關鍵情境）：單引號／反斜線／空白／錢字號／反引號／雙引號全上。
_PW_TRICKY = "a" + "'" + "b" + "\\" + "c d" + "$" + "e" + "`" + 'f"g'


def _install_docker_stub(d):
    """在 d/bin 裝假 docker，回（bin 目錄, 記錄目錄, 計數器路徑）。"""
    bindir = os.path.join(d, "bin")
    logdir = os.path.join(d, "stublog")
    os.makedirs(bindir, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)
    stub = os.path.join(bindir, "docker")
    with open(stub, "w", encoding="utf-8") as fh:
        fh.write(DOCKER_STUB)
    os.chmod(stub, 0o755)
    return bindir, logdir, os.path.join(d, "stub.ctr")


@contextlib.contextmanager
def _stubbed(d, **extra):
    """把假 docker 掛上 PATH 的情境管理器（樁環境變數一併注入）；yield 記錄目錄。"""
    bindir, logdir, ctr = _install_docker_stub(d)
    patch = dict(os.environ, PATH=bindir + os.pathsep + os.environ.get("PATH", ""),
                 RV5_STUB_DIR=logdir, RV5_STUB_CTR=ctr, **extra)
    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(patch)
    try:
        yield logdir
    finally:
        os.environ.clear()
        os.environ.update(old)


@contextlib.contextmanager
def _no_docker(d):
    """PATH 只剩空目錄＝docker 不可得（127 分支）。"""
    bindir = os.path.join(d, "emptybin")
    os.makedirs(bindir, exist_ok=True)
    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(dict(old, PATH=bindir))
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


def _calls(logdir):
    """讀回樁記錄＝[(argv 位元組, stdin 位元組, CWD 位元組), …]（呼叫序）。"""
    out = []
    i = 1
    while os.path.exists(os.path.join(logdir, "argv.%d" % i)):
        with open(os.path.join(logdir, "argv.%d" % i), "rb") as fh:
            argv = fh.read()
        with open(os.path.join(logdir, "stdin.%d" % i), "rb") as fh:
            data = fh.read()
        with open(os.path.join(logdir, "cwd.%d" % i), "rb") as fh:
            cwd = fh.read()
        out.append((argv, data, cwd))
        i += 1
    return out


def _flat(argv_list):
    """argv list → 樁記錄的 NUL 分隔位元組形（比對用）。

    ★丟掉第 0 位：樁記的是 `sys.argv[1:]`，即 docker **收到的引數**（`docker` 這個字由 PATH
    解析掉了）；與舊 .sh 的基準檔同一口徑，兩側才可逐位元組比。
    """
    assert argv_list[0] == "docker", argv_list
    return b"\0".join(a.encode("utf-8") for a in argv_list[1:])


def _seed_pw(secrets_dir, blob):
    """在隔離暫存落點寫入密碼檔。★呼叫端一律傳 tempfile 目錄——指向真落點即覆寫機密。"""
    os.makedirs(secrets_dir, exist_ok=True)
    path = os.path.join(secrets_dir, PW_NAME)
    with open(path, "wb") as fh:
        fh.write(blob)
    return path


class _Cap:
    """捕捉 cmd_setup 的 stdout／stderr（含 stderr.buffer 那條位元組路徑）。"""

    def __init__(self):
        self.out = None
        self.err = None

    def __enter__(self):
        self._o, self._e = sys.stdout, sys.stderr
        self._of = tempfile.TemporaryFile()
        self._ef = tempfile.TemporaryFile()
        sys.stdout = open(self._of.fileno(), "w", encoding="utf-8", closefd=False)
        sys.stderr = open(self._ef.fileno(), "w", encoding="utf-8", closefd=False)
        return self

    def __exit__(self, *exc):
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout, sys.stderr = self._o, self._e
        self._of.seek(0)
        self._ef.seek(0)
        # ★底層以二進位暫存檔收（stderr 診斷行走 buffer 位元組路徑、文字層 StringIO 收不到）；
        #   raw 位元組另存 out_b／err_b（非 UTF-8 診斷案比原始位元組），str 面 decode 用
        #   replace——診斷行可能含非 UTF-8 片段、strict 會在收尾自炸。
        self.out_b = self._of.read()
        self.err_b = self._ef.read()
        self.out = self.out_b.decode("utf-8", "replace")
        self.err = self.err_b.decode("utf-8", "replace")
        self._of.close()
        self._ef.close()
        return False


@contextlib.contextmanager
def _merged_streams(path):
    """把本行程 stdout／stderr **與子行程的** 一起導向同一個檔（＝終端併流的模型）。

    ★與 _Cap 的分工：_Cap 只換掉 sys.stdout／sys.stderr 這兩個 python 物件，收得到本行程的
    輸出，但子行程繼承的是**真的 fd 1／2**（_run 傳 stdout=None），所以兩邊落在不同地方、
    結構上偵測不到交錯。要驗「誰先寫」就必須在 fd 層 dup2 到同一個檔。
    ★sys.stdout 一併重建成**顯式塊緩衝**：直譯器啟動時就依 fd 1 是否為 tty 定死緩衝模式，
    自終端跑測試時是行緩衝、print 完立刻落地，flush 有沒有做看不出差別（測試會假綠）。
    這裡重建包裝把它釘成塊緩衝，任何跑法下「漏 flush」都會被抓到。
    """
    fh = open(path, "wb")
    keep_out, keep_err = os.dup(1), os.dup(2)
    old_out, old_err = sys.stdout, sys.stderr
    try:
        os.dup2(fh.fileno(), 1)
        os.dup2(fh.fileno(), 2)
        sys.stdout = io.TextIOWrapper(io.BufferedWriter(io.FileIO(1, "w", closefd=False)),
                                      encoding="utf-8")
        sys.stderr = io.TextIOWrapper(io.BufferedWriter(io.FileIO(2, "w", closefd=False)),
                                      encoding="utf-8")
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout, sys.stderr = old_out, old_err
        os.dup2(keep_out, 1)
        os.dup2(keep_err, 2)
        os.close(keep_out)
        os.close(keep_err)
        fh.close()


def _run_case(d, pw_blob=None, env=None, stub_env=None, secrets_sub="deploy/secrets"):
    """跑一輪 cmd_setup（假 docker 樁）；回 (rc, calls, stdout 位元組, stderr 位元組)。"""
    root = os.path.join(d, "root")
    os.makedirs(root, exist_ok=True)
    if pw_blob is not None:
        _seed_pw(os.path.join(root, secrets_sub), pw_blob)
    with _stubbed(d, **(stub_env or {})) as logdir:
        with _Cap() as cap:
            rc = cmd_setup(root=root, env={} if env is None else env)
    return rc, _calls(logdir), cap.out, cap.err, root


class TestLiteralsPinned(unittest.TestCase):
    """★介面字面逐字釘死：以被測常數組出期望值＝套套邏輯（常數漂了斷言跟著漂、全綠存活）。

    這四組字面（密碼檔名、compose 前綴、兩發 argv 尾、ALTER ROLE 的 SQL 形）就是 B-037 U2
    明載「一個字元都不能漂」的標的，逐字列出。
    """

    def test_pw_name_is_pinned(self):
        """★跨檔契約字面：deploy/generate-secrets.py 的 SECRETS 名冊產的就是這個名字
        （`("reaper_password", ("-hex", "24"))`＋`.txt`），deploy/secrets/README.md 亦以此為準。

        流程案一律 `_seed_pw(dir, PW_NAME)` 寫檔再以同一常數讀回＝套套邏輯，常數漂了斷言跟著
        漂、全綠存活；而漂掉的後果不是紅，是生產面永遠走「缺席或為空」分支——operator 被指去
        重跑 decrypt 卻永遠補不齊。故此處逐字釘死。
        """
        self.assertEqual(PW_NAME, "reaper_password.txt")

    def test_compose_prefix_is_pinned(self):
        self.assertEqual(COMPOSE_ARGV, ("docker", "compose", "-f", "docker-compose.yml",
                                        "-f", "docker-compose.dev.yml"))

    def test_psql_argv_is_pinned(self):
        self.assertEqual(psql_argv(), [
            "docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml",
            "exec", "-T", "postgres", "psql", "-v", "ON_ERROR_STOP=1",
            "-U", "soybean", "-d", "soybean_admin_rust",
            "--quiet", "--no-align", "--tuples-only"])

    def test_verify_argv_is_pinned(self):
        self.assertEqual(verify_argv(), [
            "docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml",
            "exec", "-T", "postgres", "sh", "-c",
            'read -r RPW; PGPASSWORD="$RPW" '
            'psql -h postgres -U reaper -d soybean_admin_rust -Atc "SELECT 1"'])

    def test_alter_role_sql_shape_is_pinned(self):
        """SQL 形逐位元組：前綴、單引號、分號、結尾換行——舊檔 heredoc 本體的鏡像。"""
        self.assertEqual(alter_role_sql(b"XX"),
                         b"ALTER ROLE reaper LOGIN PASSWORD 'XX';\n")

    def test_password_never_appears_in_any_argv(self):
        """★密碼零進 argv（本刀主要收益的機器化）：兩發 argv 都與密碼無關（純函式、不收 pw）。"""
        pw = _PW_PLAIN.encode("utf-8")
        for argv in (psql_argv(), verify_argv()):
            for token in argv:
                self.assertNotIn(_PW_PLAIN, token, msg=argv)
        self.assertIn(pw, alter_role_sql(pw))      # 密碼只在 payload 裡
        self.assertIn(pw, verify_stdin(pw))


class TestPurePredicates(unittest.TestCase):
    """純函式面：密碼讀取語意與 payload 組裝（不碰檔案系統以外的東西、零 docker）。"""

    def test_alter_role_sql_embeds_password_verbatim(self):
        """★特殊字元原樣嵌入、零跳脫（舊檔行為，照抄不動；等價矩陣情境④的單元面）。"""
        pw = _PW_TRICKY.encode("utf-8")
        self.assertEqual(alter_role_sql(pw),
                         b"ALTER ROLE reaper LOGIN PASSWORD '" + pw + b"';\n")

    def test_verify_stdin_appends_exactly_one_newline(self):
        """`printf '%s\\n'` 語意：恰補一個換行、不多不少。"""
        self.assertEqual(verify_stdin(b"abc"), b"abc\n")
        self.assertEqual(verify_stdin(b""), b"\n")

    def test_read_password_strips_all_trailing_newlines(self):
        """`$(cat)` 剝**全部**尾端換行（剝一個會把 \\n 送進 SQL 字面）。"""
        with tempfile.TemporaryDirectory() as d:
            p = _seed_pw(d, b"multi-nl\n\n\n")
            self.assertEqual(read_password(p), b"multi-nl")

    def test_read_password_keeps_inner_bytes(self):
        """中間的空白／特殊字元不動（只剝尾端 LF）。"""
        with tempfile.TemporaryDirectory() as d:
            p = _seed_pw(d, _PW_TRICKY.encode("utf-8") + b"\n")
            self.assertEqual(read_password(p), _PW_TRICKY.encode("utf-8"))

    def test_read_password_missing_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(read_password(os.path.join(d, PW_NAME)))

    def test_read_password_empty_is_none(self):
        """空檔＝舊檔 `[ ! -s ]` 為真（缺席與空檔同分支、同訊息）。"""
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(read_password(_seed_pw(d, b"")))

    def test_read_password_newline_only_is_empty_bytes(self):
        """★只有換行的檔：size>0 過得了 `-s`，剝完是空字串——舊檔會照送空密碼，此處同行為
        （不擅自升級成錯誤，那是行為變更）。"""
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_password(_seed_pw(d, b"\n\n")), b"")


class TestFlowWithStub(unittest.TestCase):
    """流程面：PATH 注入假 docker，逐分支比對 argv 序列、stdin payload、rc、輸出串流。"""

    def test_happy_path_two_calls_exact(self):
        with tempfile.TemporaryDirectory() as d:
            pw = _PW_PLAIN.encode("utf-8")
            rc, calls, out, err, _root = _run_case(
                d, pw_blob=pw + b"\n", stub_env={"RV5_STUB_OUT_2": "1\n"})
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(len(calls), 2, msg=calls)
            self.assertEqual(calls[0][0], _flat(psql_argv()))
            self.assertEqual(calls[0][1], alter_role_sql(pw))
            self.assertEqual(calls[1][0], _flat(verify_argv()))
            self.assertEqual(calls[1][1], verify_stdin(pw))
            self.assertEqual(out, "ok: role reaper 已設 LOGIN＋密碼（值不回顯）\n"
                                  "ok: reaper 憑證連線驗證通過（SELECT 1）\n")
            self.assertEqual(err, "")

    def test_missing_password_file_no_docker_call(self):
        """②缺 reaper_password.txt：rc 1、零 docker 調用（絕不帶著空密碼去 ALTER）。"""
        with tempfile.TemporaryDirectory() as d:
            rc, calls, out, err, root = _run_case(d, pw_blob=None)
            self.assertEqual(rc, 1)
            self.assertEqual(calls, [])
            self.assertEqual(out, "")
            self.assertIn(os.path.join(root, "deploy/secrets", PW_NAME), err)
            self.assertIn("缺席或為空", err)

    def test_empty_password_file_same_branch(self):
        """③空檔：與缺席同分支、同訊息、同 rc（舊檔 `[ ! -s ]` 一條判定吃兩形）。"""
        with tempfile.TemporaryDirectory() as d:
            rc, calls, out, err, _root = _run_case(d, pw_blob=b"")
            self.assertEqual(rc, 1)
            self.assertEqual(calls, [])
            self.assertIn("缺席或為空", err)

    def test_special_chars_payload_is_byte_verbatim(self):
        """④單引號／反斜線／空白等特殊字元：兩發 payload 逐位元組原樣（quoting 零加工）。"""
        with tempfile.TemporaryDirectory() as d:
            pw = _PW_TRICKY.encode("utf-8")
            rc, calls, _out, err, _root = _run_case(
                d, pw_blob=pw + b"\n", stub_env={"RV5_STUB_OUT_2": "1\n"})
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(calls[0][1],
                             b"ALTER ROLE reaper LOGIN PASSWORD '" + pw + b"';\n")
            self.assertEqual(calls[1][1], pw + b"\n")

    def test_first_docker_nonzero_is_passed_through(self):
        """⑤第一發非零：rc 原樣透傳、第二發不發、成功訊息不印。"""
        with tempfile.TemporaryDirectory() as d:
            rc, calls, out, err, _root = _run_case(
                d, pw_blob=b"x\n", stub_env={"RV5_STUB_RC_1": "42"})
            self.assertEqual(rc, 42)
            self.assertEqual(len(calls), 1, msg=calls)
            self.assertEqual(out, "")
            self.assertEqual(err, "")

    def test_second_docker_nonzero_is_passed_through(self):
        """第二發非零：rc 原樣透傳，而第一發的成功訊息已印（舊檔同序）。"""
        with tempfile.TemporaryDirectory() as d:
            rc, calls, out, err, _root = _run_case(
                d, pw_blob=b"x\n", stub_env={"RV5_STUB_RC_2": "7"})
            self.assertEqual(rc, 7)
            self.assertEqual(len(calls), 2, msg=calls)
            self.assertEqual(out, "ok: role reaper 已設 LOGIN＋密碼（值不回顯）\n")
            self.assertEqual(err, "")

    def test_verify_result_not_one_is_error(self):
        """自驗回值非 `1`：rc 1、回值原樣入 stderr 診斷行。"""
        with tempfile.TemporaryDirectory() as d:
            rc, _calls, out, err, _root = _run_case(
                d, pw_blob=b"x\n", stub_env={"RV5_STUB_OUT_2": "0\n"})
            self.assertEqual(rc, 1)
            self.assertEqual(out, "ok: role reaper 已設 LOGIN＋密碼（值不回顯）\n")
            self.assertEqual(err, "錯誤：reaper 憑證連線驗證失敗（回值：0）\n")

    def test_verify_result_trailing_newlines_stripped(self):
        """`$( )` 剝尾端 LF 後才比對：`1\\n\\n` 一樣算通過。"""
        with tempfile.TemporaryDirectory() as d:
            rc, _calls, _out, err, _root = _run_case(
                d, pw_blob=b"x\n", stub_env={"RV5_STUB_OUT_2": "1\n\n"})
            self.assertEqual(rc, 0, msg=err)

    def test_secrets_dir_empty_string_is_loud_failure(self):
        """⑥落點解析失敗（SECRETS_DIR 已匯出為空字串）：rc 1、零 docker 調用、指名真因。"""
        with tempfile.TemporaryDirectory() as d:
            rc, calls, out, err, _root = _run_case(d, pw_blob=b"x\n", env={"SECRETS_DIR": ""})
            self.assertEqual(rc, 1)
            self.assertEqual(calls, [])
            self.assertEqual(out, "")
            self.assertIn("SECRETS_DIR", err)
            self.assertIn("空字串", err)

    def test_secrets_dir_relative_env_anchors_at_root(self):
        """SECRETS_DIR 相對值＝錨定 repo 根（舊檔 `cd "$(dirname "$0")/.."` 後的 `$PWD`）。"""
        with tempfile.TemporaryDirectory() as d:
            rc, calls, _out, err, _root = _run_case(
                d, pw_blob=b"alt-pw\n", env={"SECRETS_DIR": "alt/sec"},
                stub_env={"RV5_STUB_OUT_2": "1\n"}, secrets_sub="alt/sec")
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(calls[1][1], b"alt-pw\n")

    def test_child_cwd_is_root_regardless_of_caller_cwd(self):
        """★子行程 CWD 釘死＝repo 根、與呼叫端 CWD 無關（舊檔首行 `cd` 的第二個職責）。

        `docker compose -f docker-compose.yml -f docker-compose.dev.yml` 這兩個是**相對**路徑，
        解析基準即子行程 CWD：漂掉的話自 repo 子目錄叫用就是 `open /docker-compose.yml: no
        such file or directory`，而呼叫端 CWD 恰有另一組同名 compose 檔時更糟——reaper 密碼會
        被 ALTER 到別的 stack。此案自「別處」CWD 起跑，釘死兩發皆落在 root。
        ★argv／stdin payload 比不到這件事（樁的 argv 記錄不含 CWD），故單獨立案。
        """
        with tempfile.TemporaryDirectory() as d:
            elsewhere = os.path.join(d, "elsewhere")
            os.makedirs(elsewhere, exist_ok=True)
            keep = os.getcwd()
            os.chdir(elsewhere)
            try:
                rc, calls, _out, err, root = _run_case(
                    d, pw_blob=b"x\n", stub_env={"RV5_STUB_OUT_2": "1\n"})
            finally:
                os.chdir(keep)
            self.assertEqual(rc, 0, msg=err)
            want = os.fsencode(os.path.realpath(root))
            # realpath 比對：暫存根在部分平台是符號連結，子行程 getcwd 回的是解析後的路徑。
            self.assertEqual([c[2] for c in calls], [want, want], msg=calls)

    def test_root_defaults_to_module_root_not_cwd(self):
        """★root 預設值釘死＝模組 ROOT（由 __file__ 推得）、**不是** os.getcwd()。

        其餘流程案一律顯式注入 root，生產面那條預設路徑因此從未被執行過——改成 CWD 也能全綠。
        漂掉的後果就是 cmd_setup／_run 註解點名的最壞情境：呼叫端 CWD 恰有另一組同名 compose
        檔（服務名含 postgres）時，reaper 密碼被 ALTER 到別的 stack 去。
        ★機安：以 SECRETS_DIR 絕對值把落點釘在暫存目錄（env dict 優先於 .env，見共用庫），
        真落點零讀寫；docker 走假樁，真 stack 零接觸。CWD 先切到別處，預設值才有觀測力。
        """
        with tempfile.TemporaryDirectory() as d:
            sec = os.path.join(d, "sec")
            _seed_pw(sec, b"x\n")
            elsewhere = os.path.join(d, "elsewhere")
            os.makedirs(elsewhere, exist_ok=True)
            keep = os.getcwd()
            os.chdir(elsewhere)
            try:
                with _stubbed(d, RV5_STUB_OUT_2="1\n") as logdir:
                    with _Cap() as cap:
                        rc = cmd_setup(root=None, env={"SECRETS_DIR": sec})
            finally:
                os.chdir(keep)
            calls = _calls(logdir)
            self.assertEqual(rc, 0, msg=cap.err)
            want = os.fsencode(os.path.realpath(ROOT))
            self.assertEqual([c[2] for c in calls], [want, want], msg=calls)

    def test_stdout_order_vs_child_stderr_is_pinned(self):
        """★輸出交錯次序釘死（_run 的 sys.stdout.flush() 的守衛）。

        本行程 stdout 被導向檔案／管線時是**塊緩衝**，子行程卻直接寫 fd 2——不先 flush，
        第一發的成功訊息就會被擠到子行程 warning 之後，與 bash 版（echo 即時寫出）相反。
        樁第二發往 stderr 印一行 warning（模擬 docker compose 的 orphan containers 訊息），
        兩流併到同一檔逐行比：訊息次序漂了就紅。
        ★argv／stdin payload 比不到這件事（等價矩陣的兩個比對面都不含時序），故單獨立案——
        缺這一案，「順手清掉看起來多餘的 flush」會全綠通過 pre-commit 與 bootstrap。
        """
        with tempfile.TemporaryDirectory() as d:
            root = os.path.join(d, "root")
            _seed_pw(os.path.join(root, "deploy/secrets"), b"x\n")
            log = os.path.join(d, "merged.log")
            with _stubbed(d, RV5_STUB_OUT_2="1\n",
                          RV5_STUB_ERR_2="WARN: Found orphan containers\n"):
                with _merged_streams(log):
                    rc = cmd_setup(root=root, env={})
            with open(log, "rb") as fh:
                merged = fh.read().decode("utf-8")
            self.assertEqual(rc, 0, msg=merged)
            self.assertEqual(merged,
                             "ok: role reaper 已設 LOGIN＋密碼（值不回顯）\n"
                             "WARN: Found orphan containers\n"
                             "ok: reaper 憑證連線驗證通過（SELECT 1）\n")

    def test_password_never_enters_child_environment(self):
        """★三禁令第三條（密碼不進環境變數）的機器守衛：樁把子行程環境全量落 env.%d，
        斷言兩發環境中零密碼位元組——「改走 -e PGPASSWORD／env= 傳遞」的順手簡化在此紅。
        argv／stdin 矩陣比不到環境面，故單獨立案（同 CWD／交錯次序兩案之理）。"""
        pw = _PW_PLAIN.encode("utf-8")
        with tempfile.TemporaryDirectory() as d:
            root = os.path.join(d, "root")
            _seed_pw(os.path.join(root, "deploy/secrets"), pw + b"\n")
            with _stubbed(d, RV5_STUB_OUT_2="1\n") as logdir:
                with _Cap() as cap:
                    rc = cmd_setup(root=root, env={})
            self.assertEqual(rc, 0, msg=cap.err)
            names = sorted(f for f in os.listdir(logdir) if f.startswith("env."))
            self.assertEqual(names, ["env.1", "env.2"])
            for name in names:
                with open(os.path.join(logdir, name), "rb") as fh:
                    self.assertNotIn(pw, fh.read(), msg=name)

    def test_verify_diag_preserves_non_utf8_bytes(self):
        """★診斷行位元組路徑（verify_login 走 stderr.buffer 不經 str）：psql 可能回非 UTF-8
        片段，decode 會改字面、也可能自己炸——樁令第二發回 b'\\xff\\xfebad'（OUTHEX 探針），
        斷言 stderr 逐位元組＝前綴＋原始位元組＋後綴（改寫成 print(f)＋decode 在此案即紅）。"""
        bad = b"\xff\xfebad"
        with tempfile.TemporaryDirectory() as d:
            root = os.path.join(d, "root")
            _seed_pw(os.path.join(root, "deploy/secrets"), b"x\n")
            with _stubbed(d, RV5_STUB_OUTHEX_2=bad.hex()):
                with _Cap() as cap:
                    rc = cmd_setup(root=root, env={})
            self.assertEqual(rc, 1)
            self.assertEqual(cap.err_b,
                             "錯誤：reaper 憑證連線驗證失敗（回值：".encode("utf-8")
                             + bad + "）\n".encode("utf-8"))

    def test_first_call_stdout_passes_through_to_terminal(self):
        """★第一發 capture=False 的串流分工釘死：舊 .sh 第一發不做命令替換、psql 的 stdout
        直接落使用者終端——樁令第一發印 `ALTER ROLE`，兩流併檔後必須看得到它且次序在
        本行程成功訊息之前；改成 capture=True 即整段被吞（PIPE 收走後無人轉印）、此案紅。"""
        with tempfile.TemporaryDirectory() as d:
            root = os.path.join(d, "root")
            _seed_pw(os.path.join(root, "deploy/secrets"), b"x\n")
            log = os.path.join(d, "merged.log")
            with _stubbed(d, RV5_STUB_OUT_1="ALTER ROLE\n", RV5_STUB_OUT_2="1\n"):
                with _merged_streams(log):
                    rc = cmd_setup(root=root, env={})
            with open(log, "rb") as fh:
                merged = fh.read().decode("utf-8")
            self.assertEqual(rc, 0, msg=merged)
            self.assertEqual(merged,
                             "ALTER ROLE\n"
                             "ok: role reaper 已設 LOGIN＋密碼（值不回顯）\n"
                             "ok: reaper 憑證連線驗證通過（SELECT 1）\n")

    def test_docker_absent_is_127(self):
        """docker 不可得＝127（bash 的 command-not-found 碼；python 側自行指名真因）。"""
        with tempfile.TemporaryDirectory() as d:
            root = os.path.join(d, "root")
            _seed_pw(os.path.join(root, "deploy/secrets"), b"x\n")
            with _no_docker(d):
                with _Cap() as cap:
                    rc = cmd_setup(root=root, env={})
            self.assertEqual(rc, 127)
            self.assertIn("docker", cap.err)


class TestCli(unittest.TestCase):
    """入口分派：test 不收額外參數、未知子命令＝用法錯誤 64。"""

    def test_test_rejects_extra_args(self):
        with _Cap() as cap:
            rc = main(["setup-reaper-role.py", "test", "extra"])
        self.assertEqual(rc, 64)
        self.assertIn("不收額外參數", cap.err)

    def test_unknown_subcommand_is_usage_error(self):
        with _Cap() as cap:
            rc = main(["setup-reaper-role.py", "--force"])
        self.assertEqual(rc, 64)
        self.assertIn("未知子命令", cap.err)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def usage(msg=None):
    """用法錯誤：走 stderr、rc 64（EX_USAGE；沿 deploy/preflight-secrets.py 家族慣例）。"""
    if msg:
        print(msg, file=sys.stderr)
    print("用法：python3 deploy/setup-reaper-role.py（無引數）｜"
          "python3 deploy/setup-reaper-role.py test", file=sys.stderr)
    return 64


def main(argv):
    """★引數面與舊 .sh 的唯一差異，明載於此：舊檔無 case 分派、多餘引數一律**默默忽略**；
    本檔必須分辨 `test` 與真跑，若沿用「忽略」語意，`… tset` 這種手滑就會直接對真 stack
    下 ALTER ROLE。故未知子命令一律 rc 64 吵鬧失敗（同 deploy/preflight-secrets.py 先例）。
    無引數＝真跑，與舊檔逐字等價。
    """
    args = argv[1:]
    if not args:
        return cmd_setup()
    cmd = args[0]
    if cmd == "test":
        if args[1:]:
            return usage(f"test：不收額外參數（見 {' '.join(args[1:])}）")
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
