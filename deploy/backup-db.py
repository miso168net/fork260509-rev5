#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/backup-db.py — DB 備份／還原／還原演練（pg_dump 走容器、host 除 docker 外零依賴；
B-023 第一段 dump／restore＋第二段還原演練自動化 drill）

用法：python3 deploy/backup-db.py <dump|restore|drill|test> [選項]

子命令：
  dump [--container 名]   自 dev stack 的 postgres 容器（預設、compose exec）或指定容器
                          （docker exec）pg_dump 整庫（plain SQL）。落點＝
                          $HOME/backups-<repo 目錄名>/，檔名帶 UTC 時戳（帶 --container 時
                          另帶容器名）；★絕不覆寫既有檔、絕不落 repo 內。
  restore <dump 檔> --container 名
                          把 dump 檔經 psql（ON_ERROR_STOP=1）灌進指定容器的目標庫。
                          ★--container 必填、無預設——絕不默灌 dev stack 既有庫；對既有
                          實例的「原地還原」＝破壞性操作，命令形與警語見 RUNBOOK §6。
  drill <dump 檔> [--image 映像] [--keep]
                          還原演練（★非破壞）：起全新 scratch 容器＋卷（名稱恆為
                          rev5-admin-drill-pg／rev5-admin-drill-pg-data；已存在＝FAIL、不覆用
                          不刪、由 operator 自清）→ 等 pg_isready → restore 灌入 → re-dump 落
                          隔離 tempdir（★絕不落 $HOME/backups-*）→ normalize（剝
                          \\restrict／\\unrestrict 行）後逐位元比對：相等＝PASS 0（印 sha256）、
                          不等＝FAIL 1（印首個差異行號）→ 清理**只刪名稱恰為 drill 常數者**
                          （名稱守衛、非 drill 名一律拒刪）；--keep 保留 scratch 供檢視（印清理
                          命令）；tempdir 一律刪。
  test                    跑自帶測試（unittest、離線、stdlib-only、不需 docker；
                          一律隔離暫存目錄、絕不讀寫真落點）

退出碼：成功／PASS 0；本工具自身 FAIL（落點檔已存在／dump 檔缺席或無 pg_dump 標頭／產出無標頭／
drill 名資產已存在／pg_isready 逾時／演練比對不等／名稱守衛拒刪）1；
用法錯 64（EX_USAGE；沿家族慣例）；docker 不可得 127；docker／pg 工具非零＝原樣透傳
（同 deploy/setup-reaper-role.py 分級）。

落點紀律（rev4:0084 同款命名、與 SECRETS_DIR 同源）：$HOME 下以 repo 目錄名為根
（`backups-<repo 目錄名>`、跨代並存機不撞名）。★零機密處理：本工具不碰 age 私鑰、不碰
$SECRETS_DIR 明文、dump 內容只含 DB 資料——機密檔與資料卷**不入本工具備份**（明文只是密文
的投影、age 私鑰走人工離線義務、redis 不持久化、obs 卷 opt-in；理由與去處＝RUNBOOK §6）；
備份排程化＝B-023 餘下半件、本工具不含任何刪舊／排程能力（見 docs/ops/BACKLOG.md）。
"""
import argparse
import contextlib
import glob
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DB_NAME = "soybean_admin_rust"
DB_USER = "soybean"

# compose 前綴逐字沿 deploy/setup-reaper-role.py（兩相對 -f 的解析基準＝子行程 CWD＝ROOT）。
COMPOSE_ARGV = ("docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")
# plain pg_dump 產物首段固定標頭：dump 產出與 restore 輸入的雙向防呆錨（灌錯檔／截斷早炸）。
DUMP_MARKER = b"-- PostgreSQL database dump"

# drill scratch 資產（名稱恆定、與 RUNBOOK §6.2 同字面）：既是起動名、也是唯一可刪名——
# 名稱守衛 is_drill_asset 只認這兩個字面，dev stack（rev5-admin-*）與 rev4 對照 stack 永不在射程。
DRILL_CONTAINER = "rev5-admin-drill-pg"
DRILL_VOLUME = "rev5-admin-drill-pg-data"
DRILL_IMAGE = "postgres:18.4-alpine"       # 與 dev stack 同版（dump 標頭「Dumped by」須同版才逐位元相等）
DRILL_PASSWORD = "drill-scratch"           # scratch 專用固定值：容器演練完即刪、不是機密
DRILL_READY_TIMEOUT_S = 60                 # pg_isready 等待上限（逾時＝FAIL 並清理）
DRILL_READY_POLL_S = 1.0
# operator 自清命令（同一形印在：已存在守衛／名稱衝突／清理未跑完整／--keep／探測時 docker 不可得）
SELF_CLEAN_HINT = f"docker rm -f {DRILL_CONTAINER} && docker volume rm {DRILL_VOLUME}"
# docker daemon 對 `docker run --name` 撞名的原話（多年穩定）：
#   Conflict. The container name "/<名>" is already in use by container "<id>". …
_RUN_CONFLICT_MARKER = "is already in use by container"
# normalize 剝除的非決定性 token 行（pg_dump 18 每次隨機；與 RUNBOOK §6.2 舊 grep 形、
# tools/schema-gate.py normalize 同則）：只認「行首 token＋空白」形。
_RESTRICT_PREFIXES = (b"\\restrict ", b"\\unrestrict ")


def backup_dir(env=None):
    """備份落點＝$HOME/backups-<repo 目錄名>。★env=None 是哨兵（家族慣例）：測試明給
    dict、生產走本行程環境；HOME 缺席回 (None, 錯誤訊息)。"""
    env = os.environ if env is None else env
    home = env.get("HOME")
    if not home:
        return None, "HOME 未設——備份落點（$HOME/backups-<repo 目錄名>）無法解析"
    return os.path.join(home, "backups-" + os.path.basename(ROOT)), None


def dump_argv(container=None):
    """dump 的 docker argv：預設走 compose exec -T postgres；--container 走 docker exec。"""
    if container is None:
        return list(COMPOSE_ARGV) + ["exec", "-T", "postgres", "pg_dump",
                                     "--no-password", "-U", DB_USER, DB_NAME]
    return ["docker", "exec", container, "pg_dump",
            "--no-password", "-U", DB_USER, DB_NAME]


def restore_argv(container):
    """restore 的 docker argv：dump 檔自 stdin 餵 psql（-f - 讀 stdin；任一錯即停）。"""
    return ["docker", "exec", "-i", container, "psql", "-q", "--no-password",
            "-v", "ON_ERROR_STOP=1", "-U", DB_USER, "-d", DB_NAME, "-f", "-"]


def _run_docker(argv, root, stdin=None, capture=False, capture_err=False):
    """跑 docker；OSError（docker 不可得）→ None（呼叫端退 127）。cwd＝repo 根**必傳**
    （家族先例：compose 兩相對 -f 的解析基準；自子目錄叫用或呼叫端 CWD 另有同名 compose
    檔時不錨定就會打到別的 stack）。capture_err＝連 stderr 一併截取（drill 的 docker run 用：
    失敗原話要拿來判名稱衝突；呼叫端負責照印、不吞）。"""
    sys.stdout.flush()
    try:
        return subprocess.run(argv, cwd=root, stdin=stdin,
                              stdout=subprocess.PIPE if capture else None,
                              stderr=subprocess.PIPE if capture_err else None)
    except OSError as ex:
        print(f"FAIL：無法執行 {argv[0]}（{ex}）——本工具一律透過 docker 進容器"
              "（host 除 docker 外零依賴）", file=sys.stderr)
        return None


def cmd_dump(container=None, root=None, env=None, now=None, run=None):
    """dump 本體。root／env／now／run 皆為測試注入哨兵——生產面走 ROOT／本行程環境／當下 UTC／
    _run_docker（run＝drill 把 fake runner 一路帶到 pg_dump 的縫、自測零真 docker）。"""
    root = ROOT if root is None else root
    run = _run_docker if run is None else run
    bdir, err = backup_dir(env)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime() if now is None else now)
    suffix = f"-{container}" if container else ""
    final = os.path.join(bdir, f"{DB_NAME}{suffix}-{ts}.sql")
    if os.path.exists(final):
        print(f"FAIL：{final} 已存在——本工具絕不覆寫既有備份檔（同秒重跑請稍候再試）",
              file=sys.stderr)
        return 1
    r = run(dump_argv(container), root, capture=True)
    if r is None:
        return 127
    if r.returncode != 0:
        print(f"FAIL：pg_dump 非零退出（rc={r.returncode}、原樣透傳）——目標容器未起或庫不可用",
              file=sys.stderr)
        return r.returncode
    if DUMP_MARKER not in r.stdout[:512]:
        print("FAIL：產出首段無 pg_dump 標頭（-- PostgreSQL database dump）——疑截斷或非 dump "
              "輸出，不落檔", file=sys.stderr)
        return 1
    os.makedirs(bdir, exist_ok=True)
    # 終值不靠 umask、既存目錄一併補正——dump 含 sys_user 雜湊，目錄 700 即機密邊界
    # （承 SECRETS_DIR 家族 DIR_MODE；檔終值 644 同家族、由目錄承擔保護）。
    os.chmod(bdir, 0o700)
    part = final + ".part"
    with open(part, "wb") as fh:
        fh.write(r.stdout)
    os.replace(part, final)
    print(f"OK：dump 完成 → {final}（{len(r.stdout)} bytes）")
    return 0


def _dump_file_error(dump_path):
    """restore／drill 共用的輸入防呆：缺檔或首段無 pg_dump 標頭→錯誤訊息；合格→None。"""
    if not os.path.isfile(dump_path):
        return f"dump 檔 {dump_path} 不存在"
    with open(dump_path, "rb") as fh:
        if DUMP_MARKER not in fh.read(512):
            return f"{dump_path} 首段無 pg_dump 標頭——疑非 dump 檔，拒灌"
    return None


def cmd_restore(dump_path, container, root=None, run=None):
    """restore 本體：dump 檔逐位元組自 stdin 餵 psql；容器一律由呼叫端顯式指定。
    root／run＝測試注入哨兵（run＝drill 把 fake runner 一路帶到 psql 的縫、自測零真 docker）。"""
    root = ROOT if root is None else root
    run = _run_docker if run is None else run
    err = _dump_file_error(dump_path)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1
    with open(dump_path, "rb") as fh:
        r = run(restore_argv(container), root, stdin=fh)
    if r is None:
        return 127
    if r.returncode != 0:
        print(f"FAIL：psql 非零退出（rc={r.returncode}、原樣透傳）——ON_ERROR_STOP 已停在"
              "首個錯誤（目標庫非空？容器未起？）", file=sys.stderr)
        return r.returncode
    print(f"OK：restore 完成 → 容器 {container} 的 {DB_NAME}"
          f"（{os.path.getsize(dump_path)} bytes 已灌入）")
    return 0


# ---------------------------------------------------------------------------
# drill：還原演練自動化（B-023 第二段；RUNBOOK §6.2 四段手打命令的機器化、同判準）
# ---------------------------------------------------------------------------

def normalize_dump(text):
    """純函式：dump 位元組串 → 剝除 \\restrict／\\unrestrict token 行後的位元組串（其餘逐位元不動；
    text＝位元組、不經解碼——比對語意是「逐位元相等」）。"""
    return b"".join(ln for ln in text.splitlines(keepends=True)
                    if not ln.startswith(_RESTRICT_PREFIXES))


def first_diff_line(a, b):
    """純函式：兩位元組串首個相異行的 1 起行號；全等→None（長度不等時＝較短者行數＋1）。"""
    la, lb = a.splitlines(keepends=True), b.splitlines(keepends=True)
    for n, (x, y) in enumerate(zip(la, lb), start=1):
        if x != y:
            return n
    return None if len(la) == len(lb) else min(len(la), len(lb)) + 1


def is_drill_asset(name):
    """名稱守衛（純函式）：只有名稱**恰等於** drill 常數者可刪——前綴／子字串皆不算。"""
    return name in (DRILL_CONTAINER, DRILL_VOLUME)


def drill_conflicts(ps_names, vol_names):
    """已存在守衛（純函式）：現有容器／卷名冊中命中 drill 常數者（非空＝拒起、由 operator 自清）。"""
    out = []
    if DRILL_CONTAINER in ps_names:
        out.append(f"容器 {DRILL_CONTAINER}")
    if DRILL_VOLUME in vol_names:
        out.append(f"卷 {DRILL_VOLUME}")
    return out


def is_run_name_conflict(stderr_text):
    """純函式：docker run 失敗原話是否為「容器名已被佔用」——此形＝前置守衛之後才被他人建名
    （併行 drill、operator 手動建名、--keep 留下的 scratch），殘留**非本次所建**、不得清理。"""
    return _RUN_CONFLICT_MARKER in stderr_text


def docker_names_argv():
    return ["docker", "ps", "-a", "--format", "{{.Names}}"]


def docker_volumes_argv():
    return ["docker", "volume", "ls", "--format", "{{.Name}}"]


def drill_run_argv(image):
    """scratch 起動 argv（逐字＝RUNBOOK §6.2 舊手打形；卷掛 /var/lib/postgresql＝pg18 映像 VOLUME）。"""
    return ["docker", "run", "-d", "--name", DRILL_CONTAINER,
            "-v", f"{DRILL_VOLUME}:/var/lib/postgresql",
            "-e", f"POSTGRES_USER={DB_USER}", "-e", f"POSTGRES_PASSWORD={DRILL_PASSWORD}",
            "-e", f"POSTGRES_DB={DB_NAME}", image]


def drill_ready_argv():
    """就緒探測：★走 TCP（-h 127.0.0.1）——映像 entrypoint 初始化期先起一個只聽 unix socket 的
    暫時 server，不帶 -h 的 pg_isready 會對它回綠、restore 隨即撞上重啟；TCP 就緒＝最終 server。"""
    return ["docker", "exec", DRILL_CONTAINER, "pg_isready", "-q",
            "-h", "127.0.0.1", "-U", DB_USER, "-d", DB_NAME]


def _lines(stdout):
    return [ln for ln in stdout.decode("utf-8", "replace").splitlines() if ln]


def drill_cleanup(container, volume, root, run):
    """只刪名稱恰為 drill 常數者：任一名不過守衛＝FAIL 1、零 docker 呼叫（守衛在 docker 之前）。
    ★兩條刪除命令**一律跑完**（rm -f 非零不短路 volume rm——否則卷必殘留、訊息卻只提容器）；
    任一非零＝逐條印出＋自清命令、回首個非零 rc（原樣透傳）；docker 不可得→127。"""
    for kind, name in (("容器", container), ("卷", volume)):
        if not is_drill_asset(name):
            print(f"FAIL：名稱守衛拒刪{kind} {name}——只刪名稱恰為 {DRILL_CONTAINER}／"
                  f"{DRILL_VOLUME} 者", file=sys.stderr)
            return 1
    failed = []
    for argv in (["docker", "rm", "-f", container], ["docker", "volume", "rm", volume]):
        r = run(argv, root, capture=True)
        if r is None:
            return 127
        if r.returncode != 0:
            failed.append((argv, r.returncode))
    if failed:
        for argv, rc in failed:
            print(f"FAIL：{' '.join(argv)} 非零退出（rc={rc}、原樣透傳）", file=sys.stderr)
        print("FAIL：清理未跑完整——請以 docker ps -a／docker volume ls 確認殘留後自清："
              f"{SELF_CLEAN_HINT}（零殘留時 volume rm 回 no such volume 亦屬此形）", file=sys.stderr)
        return failed[0][1]
    print(f"OK：清理 → docker rm -f {container}；docker volume rm {volume}")
    return 0


def wait_ready(root, run, timeout_s, poll_s, sleep):
    """輪詢 pg_isready 至就緒；就緒→True、逾時→False、docker 不可得→None。"""
    deadline = time.monotonic() + timeout_s
    while True:
        r = run(drill_ready_argv(), root, capture=True)
        if r is None:
            return None
        if r.returncode == 0:
            return True
        if time.monotonic() >= deadline:
            return False
        sleep(poll_s)


def cmd_drill(dump_path, image=None, keep=False, root=None, run=None,
              ready_timeout_s=None, sleep=None):
    """drill 本體。root／run／ready_timeout_s／sleep 皆為測試注入哨兵——生產面走 ROOT／
    _run_docker／DRILL_READY_TIMEOUT_S／time.sleep。"""
    root = ROOT if root is None else root
    run = _run_docker if run is None else run
    image = DRILL_IMAGE if image is None else image
    ready_timeout_s = DRILL_READY_TIMEOUT_S if ready_timeout_s is None else ready_timeout_s
    sleep = time.sleep if sleep is None else sleep

    err = _dump_file_error(dump_path)
    if err:
        print(f"FAIL：{err}", file=sys.stderr)
        return 1
    # 前置：docker 可得＋drill 名資產不得已存在（存在＝不覆用、不刪、operator 自清）
    rosters = []
    for argv in (docker_names_argv(), docker_volumes_argv()):
        r = run(argv, root, capture=True)
        if r is None:
            return 127
        if r.returncode != 0:
            print(f"FAIL：{' '.join(argv)} 非零退出（rc={r.returncode}、原樣透傳）", file=sys.stderr)
            return r.returncode
        rosters.append(_lines(r.stdout))
    conflicts = drill_conflicts(*rosters)
    if conflicts:
        print("FAIL：drill 名資產已存在：" + "、".join(conflicts)
              + f"——本工具不覆用亦不刪；請 operator 確認後自清：{SELF_CLEAN_HINT}", file=sys.stderr)
        return 1
    def _finish(rc):
        if keep:
            print(f"KEEP：scratch 保留供檢視；看完請自清：{SELF_CLEAN_HINT}")
            return rc
        crc = drill_cleanup(DRILL_CONTAINER, DRILL_VOLUME, root, run)
        return rc if rc != 0 else crc

    # 起 scratch。★docker run 非零也走 _finish：具名卷在 create 階段即建出，「建好但起不來」會
    # 同時留下容器與卷；前置守衛剛證明兩名原本皆不存在，故此刻 drill 名殘留通常為本次所建、
    # 清理安全（零殘留時 docker rm -f 冪等回 0、volume rm 回 no such volume 非零——退出碼仍取
    # docker run 的原 rc、不被清理 rc 蓋掉）。★唯一例外＝**名稱衝突**：守衛與 run 之間被他人
    # 佔名（併行 drill、operator 手動建名、--keep 留下的 scratch）——該殘留非本次所建，依
    # 「不覆用不刪」契約跳過清理、改請 operator 自清；判形取 docker 原話（stderr 截下後照印）。
    r = run(drill_run_argv(image), root, capture=True, capture_err=True)
    if r is None:
        return 127
    run_err = (r.stderr or b"").decode("utf-8", "replace")
    if run_err:
        sys.stderr.write(run_err)          # docker 原話照印（含拉映像進度）、不吞
    if r.returncode != 0:
        if is_run_name_conflict(run_err):
            print(f"FAIL：docker run 非零退出（rc={r.returncode}、原樣透傳）——{DRILL_CONTAINER} 名在"
                  "前置守衛之後被他人佔用、疑為他人資產（併行 drill 或 --keep 留下的 scratch）；"
                  f"本工具不刪，請 operator 確認後自清：{SELF_CLEAN_HINT}", file=sys.stderr)
            return r.returncode
        print(f"FAIL：docker run 非零退出（rc={r.returncode}、原樣透傳）——映像不可得或 docker 異常；"
              "隨即清理本次可能建出的 drill 名殘留", file=sys.stderr)
        return _finish(r.returncode)
    print(f"OK：scratch 起動 → 容器 {DRILL_CONTAINER}／卷 {DRILL_VOLUME}（{image}）")

    t0 = time.monotonic()
    ready = wait_ready(root, run, ready_timeout_s, DRILL_READY_POLL_S, sleep)
    if ready is None:
        print("FAIL：pg_isready 探測時 docker 不可得——scratch 已起、隨即嘗試清理；不成則請 operator "
              f"自清：{SELF_CLEAN_HINT}", file=sys.stderr)
        return _finish(127)
    if not ready:
        print(f"FAIL：pg_isready 逾時（{ready_timeout_s}s）——scratch 未就緒", file=sys.stderr)
        return _finish(1)
    print(f"OK：pg_isready（{time.monotonic() - t0:.1f}s）")
    rc = cmd_restore(dump_path, DRILL_CONTAINER, root, run=run)
    if rc != 0:
        return _finish(rc)
    # re-dump 落隔離 tempdir（走 /tmp 原生 fs；★絕不落 $HOME/backups-*、絕不落 repo 內）
    tmp = tempfile.mkdtemp(prefix="backup-db-drill.")
    try:
        rc = cmd_dump(container=DRILL_CONTAINER, root=root, env={"HOME": tmp}, run=run)
        if rc != 0:
            return _finish(rc)
        produced = glob.glob(os.path.join(tmp, "backups-*", "*.sql"))
        if len(produced) != 1:
            print(f"FAIL：re-dump 落點應恰一檔、實得 {len(produced)}", file=sys.stderr)
            return _finish(1)
        with open(dump_path, "rb") as fh:
            src_norm = normalize_dump(fh.read())
        with open(produced[0], "rb") as fh:
            re_norm = normalize_dump(fh.read())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src_sha, re_sha = (hashlib.sha256(x).hexdigest() for x in (src_norm, re_norm))
    if src_norm != re_norm:
        print(f"FAIL：normalize 後不等——首個差異在第 {first_diff_line(src_norm, re_norm)} 行"
              f"（原 dump sha256 {src_sha}／re-dump sha256 {re_sha}；--keep 可保留 scratch 檢視）——"
              f"首查原 dump 標頭「Dumped by pg_dump version」與 --image 是否同版（不同版＝必然逐位元不等、非備份損壞）；判準與命令形＝RUNBOOK §6.2",
              file=sys.stderr)
        return _finish(1)
    print(f"PASS：normalize 後逐位元相等（sha256 {src_sha}；"
          f"{len(src_norm)} bytes）")
    return _finish(0)


# ---------------------------------------------------------------------------
# 入口（argparse；用法錯一律 64＝EX_USAGE，沿家族慣例、非 argparse 預設 2）
# ---------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print(f"用法錯誤：{message}", file=sys.stderr)
        self.print_usage(sys.stderr)
        sys.exit(64)


def build_parser(prog):
    parser = _Parser(prog=prog, description="DB 備份／還原／還原演練（pg_dump 走容器；B-023）")
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="<dump|restore|drill|test>")
    p_dump = sub.add_parser("dump", help="pg_dump 整庫落 $HOME/backups-<repo 目錄名>/")
    p_dump.add_argument("--container", default=None,
                        help="改自指定容器 dump（預設＝dev stack 的 postgres、走 compose）")
    p_restore = sub.add_parser("restore", help="dump 檔灌進指定容器（--container 必填）")
    p_restore.add_argument("dump_file")
    p_restore.add_argument("--container", required=True,
                           help="目標容器名（無預設——絕不默灌 dev stack 既有庫）")
    p_drill = sub.add_parser("drill", help="還原演練：全新 scratch 容器＋卷 restore→re-dump→"
                                          "normalize 逐位元比對（非破壞、只刪 drill 名）")
    p_drill.add_argument("dump_file")
    p_drill.add_argument("--image", default=DRILL_IMAGE,
                         help=f"scratch 映像（預設 {DRILL_IMAGE}＝與 dev stack 同版）")
    p_drill.add_argument("--keep", action="store_true",
                         help="演練後保留 scratch 容器與卷供檢視（印清理命令）")
    sub.add_parser("test", help="自帶測試（離線、不需 docker）")
    return parser


def main(argv):
    args = build_parser(argv[0]).parse_args(argv[1:])
    if args.cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    if args.cmd == "dump":
        return cmd_dump(container=args.container)
    if args.cmd == "restore":
        return cmd_restore(args.dump_file, args.container)
    if args.cmd == "drill":
        return cmd_drill(args.dump_file, image=args.image, keep=args.keep)
    raise AssertionError(f"未分派子命令：{args.cmd}")   # required=True 下不可達


# ---------------------------------------------------------------------------
# 自測（test 子命令）：離線、stdlib-only、不需 docker，一律隔離暫存目錄
# ---------------------------------------------------------------------------

# 假 docker 樁（走 PATH 注入、生產碼零測試接縫；家族慣例＝setup-reaper-role）：argv＋CWD 記
# 進 BKP_STUB_LOG；pg_dump 形吐 BKP_STUB_OUT（預設含 DUMP_MARKER）、psql 形把 stdin 原樣
# 寫 BKP_STUB_SINK；BKP_STUB_RC＝強制退出碼（透傳分支用）。drill 動詞：`ps -a`／`volume ls`
# 吐 BKP_STUB_PS／BKP_STUB_VOLS（已存在守衛注入面）、`run` 退 BKP_STUB_RUN_RC（預設 0、吐假容器
# id）並把 BKP_STUB_RUN_ERR 原樣寫 stderr（名稱衝突判形注入面）、pg_isready／rm／volume rm 只記錄
# （pg_isready 的重試路徑在 _FakeRunner 層注入 sleep 測、不在樁層——CLI 層等 60s 真逾時不可行）。
DOCKER_STUB = (
    "#!/usr/bin/env python3\n"
    "import os, sys\n"
    "with open(os.environ['BKP_STUB_LOG'], 'ab') as fh:\n"
    "    fh.write(b'\\0'.join(a.encode('utf-8') for a in sys.argv[1:])\n"
    "             + b'\\0CWD=' + os.getcwd().encode('utf-8') + b'\\n')\n"
    "rc = int(os.environ.get('BKP_STUB_RC', '0'))\n"
    "if sys.argv[1:3] == ['ps', '-a']:\n"
    "    sys.stdout.write(os.environ.get('BKP_STUB_PS', ''))\n"
    "elif sys.argv[1:3] == ['volume', 'ls']:\n"
    "    sys.stdout.write(os.environ.get('BKP_STUB_VOLS', ''))\n"
    "elif sys.argv[1:2] == ['run']:\n"
    "    rc = int(os.environ.get('BKP_STUB_RUN_RC', rc))\n"
    "    sys.stderr.write(os.environ.get('BKP_STUB_RUN_ERR', ''))\n"
    "    if rc == 0:\n"
    "        sys.stdout.write('0123456789abcdef\\n')\n"
    "elif 'pg_dump' in sys.argv:\n"
    "    out = os.environ.get('BKP_STUB_OUT', '-- PostgreSQL database dump\\nSELECT 1;\\n')\n"
    "    sys.stdout.buffer.write(out.encode('utf-8'))\n"
    "elif 'psql' in sys.argv:\n"
    "    open(os.environ['BKP_STUB_SINK'], 'wb').write(sys.stdin.buffer.read())\n"
    "sys.exit(rc)\n")

_GOOD_DUMP = b"-- PostgreSQL database dump\nSELECT 1;\n"


class _CliCase(unittest.TestCase):
    """subprocess 端到端跑本檔 CLI（假 docker 樁掛 PATH；HOME 指向隔離暫存目錄）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.home = os.path.join(self.d, "home")
        self.bindir = os.path.join(self.d, "bin")
        os.makedirs(self.home)
        os.makedirs(self.bindir)
        self.log = os.path.join(self.d, "stub.log")
        self.sink = os.path.join(self.d, "stub.sink")
        open(self.log, "wb").close()
        stub = os.path.join(self.bindir, "docker")
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write(DOCKER_STUB)
        os.chmod(stub, 0o755)

    def _cli(self, args, docker=True, rc_force=None, extra_env=None):
        # ★docker=False＝PATH 只剩空目錄（127 分支）：留真 PATH 會找到真 docker、測試
        #   跑去戳真 stack。python 直跑不經 PATH、不受影響。
        empty = os.path.join(self.d, "emptybin")
        os.makedirs(empty, exist_ok=True)
        path = (self.bindir + os.pathsep + os.environ.get("PATH", "")
                if docker else empty)
        env = dict(os.environ, PATH=path, HOME=self.home, BKP_STUB_LOG=self.log,
                   BKP_STUB_SINK=self.sink)
        if rc_force is not None:
            env["BKP_STUB_RC"] = rc_force
        env.update(extra_env or {})
        r = subprocess.run([sys.executable, os.path.abspath(__file__)] + args,
                           capture_output=True, encoding="utf-8", errors="replace",
                           env=env, cwd=self.d)   # 呼叫端 CWD 刻意≠repo 根（錨定另證）
        return r.returncode, r.stdout, r.stderr

    def _calls(self):
        with open(self.log, "rb") as fh:
            lines = fh.read().splitlines()
        out = []
        for ln in lines:
            *argv, cwd = ln.split(b"\0")
            assert cwd.startswith(b"CWD="), ln
            out.append(([a.decode("utf-8") for a in argv], cwd[4:].decode("utf-8")))
        return out

    def _backup_files(self):
        return sorted(glob.glob(os.path.join(self.home, "backups-*", "*")))


class TestDumpCli(_CliCase):

    def test_dump_default_writes_file_via_compose_argv(self):
        rc, out, _ = self._cli(["dump"])
        self.assertEqual(rc, 0, msg=out)
        files = self._backup_files()
        self.assertEqual(len(files), 1, msg=str(files))
        base = os.path.basename(files[0])
        self.assertRegex(base, rf"^{DB_NAME}-\d{{8}}T\d{{6}}Z\.sql$")
        self.assertIn("backups-" + os.path.basename(ROOT), files[0])
        with open(files[0], "rb") as fh:
            self.assertEqual(fh.read(), _GOOD_DUMP)
        calls = self._calls()
        self.assertEqual(len(calls), 1)
        argv, cwd = calls[0]
        self.assertEqual(["docker"] + argv, dump_argv(None))
        self.assertEqual(cwd, ROOT)          # compose 相對 -f 錨定 repo 根、與呼叫端 CWD 無關
        self.assertNotIn(".part", "".join(self._backup_files()))

    def test_dump_backup_dir_mode_is_0700(self):
        """落點目錄權限終值 0700（dump 含 sys_user 雜湊；承 SECRETS_DIR 家族 DIR_MODE）。"""
        rc, out, _ = self._cli(["dump"])
        self.assertEqual(rc, 0, msg=out)
        bdir = os.path.dirname(self._backup_files()[0])
        self.assertEqual(os.stat(bdir).st_mode & 0o777, 0o700)

    def test_dump_container_variant_argv_and_filename(self):
        rc, _, _ = self._cli(["dump", "--container", "x-drill-pg"])
        self.assertEqual(rc, 0)
        files = self._backup_files()
        self.assertEqual(len(files), 1)
        self.assertIn(f"{DB_NAME}-x-drill-pg-", os.path.basename(files[0]))
        argv, _cwd = self._calls()[0]
        self.assertEqual(["docker"] + argv, dump_argv("x-drill-pg"))

    def test_dump_without_marker_fails_loud_and_leaves_no_file(self):
        """負向：產出無 pg_dump 標頭＝FAIL 1、零落檔（含 .part）。"""
        path = self.bindir + os.pathsep + os.environ.get("PATH", "")
        env = dict(os.environ, PATH=path, HOME=self.home, BKP_STUB_LOG=self.log,
                   BKP_STUB_SINK=self.sink, BKP_STUB_OUT="garbage\n")
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "dump"],
                           capture_output=True, encoding="utf-8", errors="replace", env=env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("標頭", r.stderr)
        self.assertEqual(self._backup_files(), [])

    def test_dump_docker_unavailable_is_127(self):
        """負向：docker 不可得＝127（家族分級）、零落檔。"""
        rc, _, err = self._cli(["dump"], docker=False)
        self.assertEqual(rc, 127)
        self.assertIn("FAIL", err)
        self.assertEqual(self._backup_files(), [])

    def test_dump_nonzero_rc_is_passed_through(self):
        """負向：pg_dump 非零＝原樣透傳、零落檔。"""
        rc, _, err = self._cli(["dump"], rc_force="3")
        self.assertEqual(rc, 3)
        self.assertIn("rc=3", err)
        self.assertEqual(self._backup_files(), [])

    def test_dump_refuses_to_overwrite_existing_target(self):
        """負向：同名落點檔已存在＝FAIL 1、不覆寫、不叫 docker（now 哨兵固定時戳）。"""
        fixed = time.gmtime(0)
        bdir, err = backup_dir({"HOME": self.home})
        self.assertIsNone(err)
        os.makedirs(bdir)
        target = os.path.join(bdir, f"{DB_NAME}-19700101T000000Z.sql")
        with open(target, "wb") as fh:
            fh.write(b"sentinel")
        with unittest.mock.patch.object(subprocess, "run",
                                        side_effect=AssertionError("不得叫 docker")):
            rc = cmd_dump(root=self.d, env={"HOME": self.home}, now=fixed)
        self.assertEqual(rc, 1)
        with open(target, "rb") as fh:
            self.assertEqual(fh.read(), b"sentinel")   # 既有檔一位元組未動

    def test_dump_home_unset_is_fail_1(self):
        """負向：HOME 缺席＝落點無法解析、FAIL 1（不叫 docker）。"""
        with unittest.mock.patch.object(subprocess, "run",
                                        side_effect=AssertionError("不得叫 docker")):
            rc = cmd_dump(root=self.d, env={})
        self.assertEqual(rc, 1)


class TestRestoreCli(_CliCase):

    def _dump_file(self, body=_GOOD_DUMP):
        p = os.path.join(self.d, "in.sql")
        with open(p, "wb") as fh:
            fh.write(body)
        return p

    def test_restore_feeds_file_bytes_to_psql_stdin(self):
        p = self._dump_file()
        rc, out, _ = self._cli(["restore", p, "--container", "y-drill-pg"])
        self.assertEqual(rc, 0, msg=out)
        with open(self.sink, "rb") as fh:
            self.assertEqual(fh.read(), _GOOD_DUMP)   # 逐位元組原樣抵達 psql stdin
        argv, cwd = self._calls()[0]
        self.assertEqual(["docker"] + argv, restore_argv("y-drill-pg"))
        self.assertEqual(cwd, ROOT)

    def test_restore_missing_container_flag_is_usage_64(self):
        """負向：--container 必填（絕不默灌既有庫）＝用法錯 64、不叫 docker。"""
        rc, _, err = self._cli(["restore", self._dump_file()])
        self.assertEqual(rc, 64)
        self.assertIn("用法錯誤", err)
        self.assertEqual(self._calls(), [])

    def test_restore_missing_file_is_fail_1(self):
        """負向：dump 檔不存在＝FAIL 1、不叫 docker。"""
        rc, _, err = self._cli(["restore", os.path.join(self.d, "no.sql"),
                                "--container", "z"])
        self.assertEqual(rc, 1)
        self.assertIn("不存在", err)
        self.assertEqual(self._calls(), [])

    def test_restore_rejects_file_without_marker(self):
        """負向：無 pg_dump 標頭＝拒灌 FAIL 1（灌錯檔防呆）、不叫 docker。"""
        rc, _, err = self._cli(["restore", self._dump_file(b"not a dump\n"),
                                "--container", "z"])
        self.assertEqual(rc, 1)
        self.assertIn("拒灌", err)
        self.assertEqual(self._calls(), [])

    def test_restore_nonzero_rc_is_passed_through(self):
        """負向：psql 非零＝原樣透傳。"""
        rc, _, err = self._cli(["restore", self._dump_file(), "--container", "z"],
                               rc_force="7")
        self.assertEqual(rc, 7)
        self.assertIn("rc=7", err)


class _FakeRunner:
    """直呼 cmd_drill 用的假 runner（形同 _run_docker：argv／root／stdin／capture／capture_err →
    CompletedProcess 或 None）；只記錄 argv、不碰 subprocess。ps／vols＝`docker ps -a`／`docker volume ls`
    注入輸出；ready_rc／run_rc／rm_rc＝pg_isready／docker run／docker rm -f 退出碼；ready_fails＝前 N 次
    pg_isready 一律回非零（第 N+1 次起回 ready_rc；重試路徑注入面）；run_err＝docker run 的 stderr 原話
    （名稱衝突判形注入面）；pg_dump 形吐 _GOOD_DUMP（PASS 路徑走得完）。"""

    def __init__(self, ps="", vols="", ready_rc=0, run_rc=0, ready_fails=0, run_err=b"", rm_rc=0):
        self.calls, self.ps, self.vols = [], ps, vols
        self.ready_rc, self.run_rc, self.rm_rc = ready_rc, run_rc, rm_rc
        self.ready_fails, self.run_err, self.ready_seen = ready_fails, run_err, 0

    def __call__(self, argv, root, stdin=None, capture=False, capture_err=False):
        self.calls.append(list(argv))
        rc, out, err = 0, b"", b""
        if "pg_isready" in argv:
            self.ready_seen += 1
            rc = 1 if self.ready_seen <= self.ready_fails else self.ready_rc
        elif argv[1:3] == ["ps", "-a"]:
            out = self.ps.encode("utf-8")
        elif argv[1:3] == ["volume", "ls"]:
            out = self.vols.encode("utf-8")
        elif argv[1:2] == ["run"]:
            rc, err = self.run_rc, self.run_err
        elif argv[1:3] == ["rm", "-f"]:
            rc = self.rm_rc
        elif "pg_dump" in argv:
            out = _GOOD_DUMP
        return subprocess.CompletedProcess(argv, rc, stdout=out,
                                           stderr=err if capture_err else None)


# docker daemon 撞名原話（逐字形；名稱衝突判形的正向樣本）
_RUN_CONFLICT_ERR = (b'docker: Error response from daemon: Conflict. The container name '
                     b'"/rev5-admin-drill-pg" is already in use by container "0123456789abcdef". '
                     b'You have to remove (or rename) that container to be able to reuse that name.\n')


_RESTRICT_DUMP = (b"-- PostgreSQL database dump\n"
                  b"\\restrict TOKEN123\n"
                  b"SELECT 1;\n"
                  b"\\unrestrict TOKEN123\n")


class TestNormalizeDump(unittest.TestCase):
    """normalize 純函式：只剝 `\\restrict `／`\\unrestrict ` 起首行（與 RUNBOOK §6.2 舊 grep 形、
    schema-gate normalize 同則）；其餘位元組原樣。"""

    def test_strips_restrict_lines_in_middle(self):
        self.assertEqual(normalize_dump(_RESTRICT_DUMP), _GOOD_DUMP)

    def test_strips_restrict_line_at_start(self):
        self.assertEqual(normalize_dump(b"\\restrict X\n" + _GOOD_DUMP), _GOOD_DUMP)

    def test_empty_and_untouched_inputs_are_identity(self):
        self.assertEqual(normalize_dump(b""), b"")
        self.assertEqual(normalize_dump(_GOOD_DUMP), _GOOD_DUMP)

    def test_only_exact_token_lines_are_stripped(self):
        """`\\restricted …`（無空白分隔）不是 token 行、不剝；行中出現的 `\\restrict` 亦不剝。"""
        body = b"\\restricted keep\nSELECT '\\restrict x';\n"
        self.assertEqual(normalize_dump(body), body)

    def test_first_diff_line_is_one_based_and_none_when_equal(self):
        self.assertIsNone(first_diff_line(_GOOD_DUMP, _GOOD_DUMP))
        self.assertEqual(first_diff_line(_GOOD_DUMP, b"-- PostgreSQL database dump\nSELECT 2;\n"), 2)
        self.assertEqual(first_diff_line(_GOOD_DUMP, _GOOD_DUMP + b"tail\n"), 3)


class TestDrillGuards(unittest.TestCase):
    """名稱守衛（只刪名稱恰為 drill 常數者）與已存在守衛（純函式、fake runner）。"""

    def test_drill_names_are_pinned(self):
        self.assertEqual(DRILL_CONTAINER, "rev5-admin-drill-pg")
        self.assertEqual(DRILL_VOLUME, "rev5-admin-drill-pg-data")
        self.assertEqual(DRILL_IMAGE, "postgres:18.4-alpine")

    def test_drill_image_matches_compose_postgres_image(self):
        """★B-154 第六面 parity（外層批 fhr 碼透鏡立案、2026-08-31 收單）：DRILL_IMAGE 與
        docker-compose.yml 之 postgres `image:` 字面機器對賬——此前唯一釘子（上一支測）把
        常數釘回自身字面＝只擋誤改常數、對 compose 面零覆蓋，兩面單獨改版彼此無感。
        stdlib 正則取 `image: postgres:*`（compose 恰一處、恰一斷言防多 postgres 服務混入）、
        斷言＝DRILL_IMAGE；自此任一面單獨改版即紅。"""
        with open(os.path.join(ROOT, "docker-compose.yml"), encoding="utf-8") as fh:
            text = fh.read()
        imgs = re.findall(r"^\s*image:\s*(postgres:\S+)\s*$", text, flags=re.M)
        self.assertEqual(len(imgs), 1, msg=str(imgs))
        self.assertEqual(imgs[0], DRILL_IMAGE)

    def test_is_drill_asset_only_exact_names(self):
        self.assertTrue(is_drill_asset(DRILL_CONTAINER))
        self.assertTrue(is_drill_asset(DRILL_VOLUME))
        for name in ("rev5-admin-postgres-1", "rev5-admin_postgres_data", "rev5-admin-drill-pg-x",
                     "rev4-admin-postgres-1", "", "drill"):
            self.assertFalse(is_drill_asset(name), msg=name)

    def test_cleanup_refuses_non_drill_container_without_calling_docker(self):
        """★紅案：非 drill 名一律拒刪並 FAIL 1、零 docker 呼叫（守衛在 docker 之前）。"""
        fake = _FakeRunner()
        rc = drill_cleanup("rev5-admin-postgres-1", DRILL_VOLUME, "/r", fake)
        self.assertEqual(rc, 1)
        self.assertEqual(fake.calls, [])
        fake = _FakeRunner()
        rc = drill_cleanup(DRILL_CONTAINER, "rev5-admin_postgres_data", "/r", fake)
        self.assertEqual(rc, 1)
        self.assertEqual(fake.calls, [])

    def test_cleanup_removes_exactly_drill_assets(self):
        fake = _FakeRunner()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(drill_cleanup(DRILL_CONTAINER, DRILL_VOLUME, "/r", fake), 0)
        self.assertEqual(fake.calls, [["docker", "rm", "-f", DRILL_CONTAINER],
                                      ["docker", "volume", "rm", DRILL_VOLUME]])

    def test_conflicts_names_existing_drill_assets_only(self):
        self.assertEqual(drill_conflicts(["a", "rev5-admin-postgres-1"], ["rev5-admin_postgres_data"]), [])
        self.assertEqual(drill_conflicts([DRILL_CONTAINER, "x"], ["y", DRILL_VOLUME]),
                         [f"容器 {DRILL_CONTAINER}", f"卷 {DRILL_VOLUME}"])

    def test_existing_asset_from_injected_ps_output_is_fail_1_before_run(self):
        """★紅案：fake runner 注入 `docker ps -a` 輸出含 drill 名＝FAIL 1、不起 scratch、不刪。"""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _FakeRunner(ps="rev5-admin-postgres-1\nrev5-admin-drill-pg\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = cmd_drill(p, root=d, run=fake)
            self.assertEqual(rc, 1)
            self.assertIn(DRILL_CONTAINER, err.getvalue())
            verbs = [c[1] for c in fake.calls]
            self.assertEqual(verbs, ["ps", "volume"])          # 只看名冊、其餘零呼叫

    def test_ready_timeout_is_fail_1_and_cleans_up(self):
        """pg_isready 逾時＝FAIL 1、scratch 清理、不進 restore。"""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _FakeRunner(ready_rc=1)
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_drill(p, root=d, run=fake, ready_timeout_s=0, sleep=lambda _s: None)
            self.assertEqual(rc, 1)
            self.assertIn("pg_isready", err.getvalue())
            verbs = [c[1:3] for c in fake.calls]
            self.assertIn(["rm", "-f"], verbs)
            self.assertIn(["volume", "rm"], verbs)
            self.assertFalse(any("psql" in c for c in fake.calls))

    def test_full_sequence_stays_inside_injected_runner(self):
        """★隔離守門：fake runner 經 cmd_restore／cmd_dump 的 run 縫一路帶到 psql／pg_dump——
        八步 argv 全數落在 fake.calls＝零真 docker；縫斷掉即少 psql／pg_dump 兩筆（且戳真 daemon）而紅。"""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _FakeRunner()
            with contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_drill(p, root=d, run=fake)
            self.assertEqual(rc, 0)
            self.assertEqual(fake.calls, [
                docker_names_argv(), docker_volumes_argv(), drill_run_argv(DRILL_IMAGE),
                drill_ready_argv(), restore_argv(DRILL_CONTAINER), dump_argv(DRILL_CONTAINER),
                ["docker", "rm", "-f", DRILL_CONTAINER], ["docker", "volume", "rm", DRILL_VOLUME]])

    def test_ready_retry_path_sleeps_poll_interval_until_green(self):
        """★重試路徑（L-074 修法承載處、真跑 5.6s 全靠它）：前 3 探非零、第 4 探回 0——sleep 恰 3 次
        且每次引數＝DRILL_READY_POLL_S、pg_isready 恰 4 次、之後照常進 restore、rc=0
        （把迴圈的 sleep 換成 raise、或提早 return True 即紅）。"""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _FakeRunner(ready_fails=3)
            sleeps = []
            with contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_drill(p, root=d, run=fake, sleep=sleeps.append)
            self.assertEqual(rc, 0)
            self.assertEqual(sleeps, [DRILL_READY_POLL_S] * 3)
            self.assertEqual(sum("pg_isready" in c for c in fake.calls), 4)
            self.assertTrue(any("psql" in c for c in fake.calls))

    def test_ready_probe_docker_gone_is_127_with_cleanup_attempt_and_hint(self):
        """pg_isready 探測時 docker 不可得（runner 回 None）＝127、**仍嘗試清理**並印自清命令
        （裸 return 127 會把已起的 scratch 留下且零提示）。"""
        class _Gone(_FakeRunner):
            def __call__(self, argv, root, stdin=None, capture=False, capture_err=False):
                if "pg_isready" in argv:
                    self.calls.append(list(argv))
                    return None
                return super().__call__(argv, root, stdin, capture, capture_err)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _Gone()
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_drill(p, root=d, run=fake)
            self.assertEqual(rc, 127)
            verbs = [c[1:3] for c in fake.calls]
            self.assertIn(["rm", "-f"], verbs)
            self.assertIn(["volume", "rm"], verbs)
            self.assertIn(SELF_CLEAN_HINT, err.getvalue())

    def test_cleanup_runs_volume_rm_even_when_rm_f_fails(self):
        """★紅案：docker rm -f 非零**不短路**——volume rm 仍跑；回首個非零 rc、兩條命令與自清提示皆印。"""
        fake = _FakeRunner(rm_rc=3)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = drill_cleanup(DRILL_CONTAINER, DRILL_VOLUME, "/r", fake)
        self.assertEqual(rc, 3)
        self.assertEqual(fake.calls, [["docker", "rm", "-f", DRILL_CONTAINER],
                                      ["docker", "volume", "rm", DRILL_VOLUME]])
        self.assertIn("rc=3", err.getvalue())
        self.assertIn(SELF_CLEAN_HINT, err.getvalue())

    def test_is_run_name_conflict_only_matches_daemon_phrase(self):
        self.assertTrue(is_run_name_conflict(_RUN_CONFLICT_ERR.decode("utf-8")))
        self.assertFalse(is_run_name_conflict("docker: Error response from daemon: No such image: postgres:x\n"))
        self.assertFalse(is_run_name_conflict(""))

    def test_docker_run_name_conflict_skips_cleanup_and_points_operator(self):
        """★紅案（非破壞契約）：docker run 因 drill 名在守衛之後被他人佔用而失敗（daemon 原話
        「is already in use by container」）＝原 rc 透傳、**零 rm／volume rm**（該殘留非本次所建）、
        印自清命令；--keep 與否無涉。"""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _FakeRunner(run_rc=125, run_err=_RUN_CONFLICT_ERR)
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_drill(p, root=d, run=fake)
            self.assertEqual(rc, 125)
            verbs = [c[1:3] for c in fake.calls]
            self.assertNotIn(["rm", "-f"], verbs)
            self.assertNotIn(["volume", "rm"], verbs)
            self.assertIn("他人資產", err.getvalue())
            self.assertIn(SELF_CLEAN_HINT, err.getvalue())
            self.assertIn("is already in use by container", err.getvalue())   # docker 原話照印

    def test_docker_run_failure_passes_rc_through_and_cleans_up(self):
        """★紅案：docker run 非零且**非名稱衝突**（映像不可得等）＝原 rc 透傳、隨即清理
        （「建好但起不來」會留下容器＋卷）、不進 pg_isready。"""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.sql")
            with open(p, "wb") as fh:
                fh.write(_GOOD_DUMP)
            fake = _FakeRunner(run_rc=125)
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_drill(p, root=d, run=fake)
            self.assertEqual(rc, 125)
            self.assertIn("docker run", err.getvalue())
            verbs = [c[1:3] for c in fake.calls]
            self.assertIn(["rm", "-f"], verbs)
            self.assertIn(["volume", "rm"], verbs)
            self.assertFalse(any("pg_isready" in c for c in fake.calls))


class TestDrillCli(_CliCase):
    """drill 端到端（假 docker 樁）：PASS／diff FAIL／rc 分級／--keep／argparse。"""

    def _dump_file(self, body):
        p = os.path.join(self.d, "in.sql")
        with open(p, "wb") as fh:
            fh.write(body)
        return p

    def test_drill_pass_path_full_sequence_and_no_home_landing(self):
        """輸入含 \\restrict 行、樁 re-dump 不含：normalize 後相等＝PASS 0；序列逐字釘死；
        re-dump 絕不落 $HOME/backups-*。"""
        rc, out, err = self._cli(["drill", self._dump_file(_RESTRICT_DUMP)])
        self.assertEqual(rc, 0, msg=out + err)
        self.assertIn("PASS", out)
        self.assertIn(hashlib.sha256(_GOOD_DUMP).hexdigest(), out)
        with open(self.sink, "rb") as fh:
            self.assertEqual(fh.read(), _RESTRICT_DUMP)      # restore 餵的是原檔位元組
        calls = self._calls()
        self.assertEqual([["docker"] + a for a, _c in calls], [
            docker_names_argv(), docker_volumes_argv(), drill_run_argv(DRILL_IMAGE),
            drill_ready_argv(), restore_argv(DRILL_CONTAINER), dump_argv(DRILL_CONTAINER),
            ["docker", "rm", "-f", DRILL_CONTAINER], ["docker", "volume", "rm", DRILL_VOLUME]])
        self.assertTrue(all(c == ROOT for _a, c in calls))
        self.assertEqual(self._backup_files(), [])

    def test_drill_keep_skips_cleanup_and_prints_command(self):
        rc, out, _ = self._cli(["drill", self._dump_file(_GOOD_DUMP), "--keep"])
        self.assertEqual(rc, 0, msg=out)
        verbs = [a[0] for a, _c in self._calls()]
        self.assertNotIn("rm", verbs)
        self.assertNotIn("volume rm", [" ".join(a[:2]) for a, _c in self._calls()])
        self.assertIn(f"docker rm -f {DRILL_CONTAINER}", out)
        self.assertIn(f"docker volume rm {DRILL_VOLUME}", out)

    def test_drill_image_flag_replaces_image_in_run_argv(self):
        rc, _, _ = self._cli(["drill", self._dump_file(_GOOD_DUMP), "--image", "postgres:x"])
        self.assertEqual(rc, 0)
        run_calls = [a for a, _c in self._calls() if a[0] == "run"]
        self.assertEqual(["docker"] + run_calls[0], drill_run_argv("postgres:x"))

    def test_drill_diff_is_fail_1_with_first_line_and_still_cleans_up(self):
        """★紅案：normalize 後不等＝FAIL 1、印首個差異行號；scratch 仍清理。"""
        rc, _, err = self._cli(["drill", self._dump_file(b"-- PostgreSQL database dump\nSELECT 2;\n")])
        self.assertEqual(rc, 1)
        self.assertIn("第 2 行", err)
        verbs = [" ".join(a[:2]) for a, _c in self._calls()]
        self.assertIn("rm -f", verbs)
        self.assertIn("volume rm", verbs)

    def test_drill_existing_container_via_stub_ps_is_fail_1(self):
        rc, _, err = self._cli(["drill", self._dump_file(_GOOD_DUMP)],
                               extra_env={"BKP_STUB_PS": "rev5-admin-drill-pg\n"})
        self.assertEqual(rc, 1)
        self.assertIn("已存在", err)
        self.assertNotIn("run", [a[0] for a, _c in self._calls()])

    def test_drill_existing_volume_via_stub_vols_is_fail_1(self):
        rc, _, err = self._cli(["drill", self._dump_file(_GOOD_DUMP)],
                               extra_env={"BKP_STUB_VOLS": "rev5-admin-drill-pg-data\n"})
        self.assertEqual(rc, 1)
        self.assertIn(DRILL_VOLUME, err)
        self.assertNotIn("run", [a[0] for a, _c in self._calls()])

    def test_drill_run_name_conflict_via_stub_stderr_skips_cleanup(self):
        """端到端：真 _run_docker 截 docker run 的 stderr → 判名稱衝突＝rc 透傳、零 rm、原話照印。"""
        rc, _, err = self._cli(["drill", self._dump_file(_GOOD_DUMP)],
                               extra_env={"BKP_STUB_RUN_RC": "125",
                                          "BKP_STUB_RUN_ERR": _RUN_CONFLICT_ERR.decode("utf-8")})
        self.assertEqual(rc, 125)
        self.assertIn("is already in use by container", err)
        self.assertIn(SELF_CLEAN_HINT, err)
        verbs = [" ".join(a[:2]) for a, _c in self._calls()]
        self.assertNotIn("rm -f", verbs)
        self.assertNotIn("volume rm", verbs)

    def test_drill_run_plain_failure_via_stub_cleans_up(self):
        """端到端：docker run 非零、stderr 非衝突原話＝rc 透傳、照常清理兩資產。"""
        rc, _, err = self._cli(["drill", self._dump_file(_GOOD_DUMP)],
                               extra_env={"BKP_STUB_RUN_RC": "125",
                                          "BKP_STUB_RUN_ERR": "docker: Error response from daemon: No such image\n"})
        self.assertEqual(rc, 125)
        self.assertIn("No such image", err)
        verbs = [" ".join(a[:2]) for a, _c in self._calls()]
        self.assertIn("rm -f", verbs)
        self.assertIn("volume rm", verbs)

    def test_drill_docker_unavailable_is_127(self):
        rc, _, err = self._cli(["drill", self._dump_file(_GOOD_DUMP)], docker=False)
        self.assertEqual(rc, 127)
        self.assertIn("FAIL", err)

    def test_drill_nonzero_docker_rc_is_passed_through(self):
        rc, _, err = self._cli(["drill", self._dump_file(_GOOD_DUMP)], rc_force="5")
        self.assertEqual(rc, 5)
        self.assertIn("rc=5", err)

    def test_drill_missing_dump_file_is_fail_1_without_docker(self):
        rc, _, err = self._cli(["drill", os.path.join(self.d, "no.sql")])
        self.assertEqual(rc, 1)
        self.assertIn("不存在", err)
        self.assertEqual(self._calls(), [])

    def test_drill_rejects_file_without_marker(self):
        rc, _, err = self._cli(["drill", self._dump_file(b"garbage\n")])
        self.assertEqual(rc, 1)
        self.assertIn("拒灌", err)
        self.assertEqual(self._calls(), [])

    def test_drill_without_dump_arg_is_usage_64(self):
        rc, _, err = self._cli(["drill"])
        self.assertEqual(rc, 64)
        self.assertIn("用法錯誤", err)
        self.assertEqual(self._calls(), [])


class TestEntryAndUnits(_CliCase):

    def test_unknown_subcommand_is_usage_64(self):
        rc, _, err = self._cli(["frobnicate"])
        self.assertEqual(rc, 64)
        self.assertIn("用法錯誤", err)

    def test_no_subcommand_is_usage_64(self):
        rc, _, _ = self._cli([])
        self.assertEqual(rc, 64)

    def test_backup_dir_embeds_repo_dirname_under_home(self):
        """落點紀律：$HOME 直下、根目錄名嵌完整 repo 目錄名（rev4:0084 防跨代撞名）。"""
        bdir, err = backup_dir({"HOME": "/x"})
        self.assertIsNone(err)
        self.assertEqual(os.path.dirname(bdir), "/x")
        base = os.path.basename(bdir)
        self.assertTrue(base.startswith("backups-"))
        self.assertIn(os.path.basename(ROOT), base)
        self.assertNotEqual(base, "backups")           # 短代號家族必撞名、嵌名不可省

    def test_argv_literals_are_pinned(self):
        """argv 逐位釘死（等價矩陣護欄：重排「看起來比較整齊」即紅）。"""
        self.assertEqual(dump_argv(None),
                         ["docker", "compose", "-f", "docker-compose.yml",
                          "-f", "docker-compose.dev.yml", "exec", "-T", "postgres",
                          "pg_dump", "--no-password", "-U", "soybean",
                          "soybean_admin_rust"])
        self.assertEqual(restore_argv("c1"),
                         ["docker", "exec", "-i", "c1", "psql", "-q", "--no-password",
                          "-v", "ON_ERROR_STOP=1", "-U", "soybean",
                          "-d", "soybean_admin_rust", "-f", "-"])
        self.assertEqual(drill_run_argv("img:1"),
                         ["docker", "run", "-d", "--name", "rev5-admin-drill-pg",
                          "-v", "rev5-admin-drill-pg-data:/var/lib/postgresql",
                          "-e", "POSTGRES_USER=soybean", "-e", "POSTGRES_PASSWORD=drill-scratch",
                          "-e", "POSTGRES_DB=soybean_admin_rust", "img:1"])
        self.assertEqual(drill_ready_argv(),
                         ["docker", "exec", "rev5-admin-drill-pg", "pg_isready", "-q",
                          "-h", "127.0.0.1", "-U", "soybean", "-d", "soybean_admin_rust"])
        self.assertEqual(docker_names_argv(), ["docker", "ps", "-a", "--format", "{{.Names}}"])
        self.assertEqual(docker_volumes_argv(), ["docker", "volume", "ls", "--format", "{{.Name}}"])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
