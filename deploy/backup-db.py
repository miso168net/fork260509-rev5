#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/backup-db.py — DB 備份／還原（pg_dump 走容器、host 除 docker 外零依賴；B-023 第一段）

用法：python3 deploy/backup-db.py <dump|restore|test> [選項]

子命令：
  dump [--container 名]   自 dev stack 的 postgres 容器（預設、compose exec）或指定容器
                          （docker exec）pg_dump 整庫（plain SQL）。落點＝
                          $HOME/backups-<repo 目錄名>/，檔名帶 UTC 時戳（帶 --container 時
                          另帶容器名）；★絕不覆寫既有檔、絕不落 repo 內。
  restore <dump 檔> --container 名
                          把 dump 檔經 psql（ON_ERROR_STOP=1）灌進指定容器的目標庫。
                          ★--container 必填、無預設——絕不默灌 dev stack 既有庫；對既有
                          實例的「原地還原」＝破壞性操作，命令形與警語見 RUNBOOK §6。
  test                    跑自帶測試（unittest、離線、stdlib-only、不需 docker；
                          一律隔離暫存目錄、絕不讀寫真落點）

退出碼：成功 0；本工具自身 FAIL（落點檔已存在／dump 檔缺席或無 pg_dump 標頭／產出無標頭）1；
用法錯 64（EX_USAGE；沿家族慣例）；docker 不可得 127；docker／pg 工具非零＝原樣透傳
（同 deploy/setup-reaper-role.py 分級）。

落點紀律（rev4:0084 同款命名、與 SECRETS_DIR 同源）：$HOME 下以 repo 目錄名為根
（`backups-<repo 目錄名>`、跨代並存機不撞名）。★零機密處理：本工具不碰 age 私鑰、不碰
$SECRETS_DIR 明文、dump 內容只含 DB 資料——機密檔與資料卷的配對備份＝B-023 第二段、
明確不在本工具（見 docs/ops/BACKLOG.md）。
"""
import argparse
import glob
import os
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


def _run_docker(argv, root, stdin=None, capture=False):
    """跑 docker；OSError（docker 不可得）→ None（呼叫端退 127）。cwd＝repo 根**必傳**
    （家族先例：compose 兩相對 -f 的解析基準；自子目錄叫用或呼叫端 CWD 另有同名 compose
    檔時不錨定就會打到別的 stack）。"""
    sys.stdout.flush()
    try:
        return subprocess.run(argv, cwd=root, stdin=stdin,
                              stdout=subprocess.PIPE if capture else None)
    except OSError as ex:
        print(f"FAIL：無法執行 {argv[0]}（{ex}）——本工具一律透過 docker 進容器"
              "（host 除 docker 外零依賴）", file=sys.stderr)
        return None


def cmd_dump(container=None, root=None, env=None, now=None):
    """dump 本體。root／env／now 皆為測試注試哨兵——生產面走 ROOT／本行程環境／當下 UTC。"""
    root = ROOT if root is None else root
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
    r = _run_docker(dump_argv(container), root, capture=True)
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


def cmd_restore(dump_path, container, root=None):
    """restore 本體：dump 檔逐位元組自 stdin 餵 psql；容器一律由呼叫端顯式指定。"""
    root = ROOT if root is None else root
    if not os.path.isfile(dump_path):
        print(f"FAIL：dump 檔 {dump_path} 不存在", file=sys.stderr)
        return 1
    with open(dump_path, "rb") as fh:
        if DUMP_MARKER not in fh.read(512):
            print(f"FAIL：{dump_path} 首段無 pg_dump 標頭——疑非 dump 檔，拒灌", file=sys.stderr)
            return 1
    with open(dump_path, "rb") as fh:
        r = _run_docker(restore_argv(container), root, stdin=fh)
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
# 入口（argparse；用法錯一律 64＝EX_USAGE，沿家族慣例、非 argparse 預設 2）
# ---------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print(f"用法錯誤：{message}", file=sys.stderr)
        self.print_usage(sys.stderr)
        sys.exit(64)


def build_parser(prog):
    parser = _Parser(prog=prog, description="DB 備份／還原（pg_dump 走容器；B-023 第一段）")
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="<dump|restore|test>")
    p_dump = sub.add_parser("dump", help="pg_dump 整庫落 $HOME/backups-<repo 目錄名>/")
    p_dump.add_argument("--container", default=None,
                        help="改自指定容器 dump（預設＝dev stack 的 postgres、走 compose）")
    p_restore = sub.add_parser("restore", help="dump 檔灌進指定容器（--container 必填）")
    p_restore.add_argument("dump_file")
    p_restore.add_argument("--container", required=True,
                           help="目標容器名（無預設——絕不默灌 dev stack 既有庫）")
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
    raise AssertionError(f"未分派子命令：{args.cmd}")   # required=True 下不可達


# ---------------------------------------------------------------------------
# 自測（test 子命令）：離線、stdlib-only、不需 docker，一律隔離暫存目錄
# ---------------------------------------------------------------------------

# 假 docker 樁（走 PATH 注入、生產碼零測試接縫；家族慣例＝setup-reaper-role）：argv＋CWD 記
# 進 BKP_STUB_LOG；pg_dump 形吐 BKP_STUB_OUT（預設含 DUMP_MARKER）、psql 形把 stdin 原樣
# 寫 BKP_STUB_SINK；BKP_STUB_RC＝強制退出碼（透傳分支用）。
DOCKER_STUB = (
    "#!/usr/bin/env python3\n"
    "import os, sys\n"
    "with open(os.environ['BKP_STUB_LOG'], 'ab') as fh:\n"
    "    fh.write(b'\\0'.join(a.encode('utf-8') for a in sys.argv[1:])\n"
    "             + b'\\0CWD=' + os.getcwd().encode('utf-8') + b'\\n')\n"
    "rc = int(os.environ.get('BKP_STUB_RC', '0'))\n"
    "if 'pg_dump' in sys.argv:\n"
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

    def _cli(self, args, docker=True, rc_force=None):
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


if __name__ == "__main__":
    sys.exit(main(sys.argv))
