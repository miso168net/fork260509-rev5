#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/rust-fmt-gate.py — rust 格式守門（`cargo fmt --all --check` 之 pre-commit 承載；B-112／ADR 0057）

子命令：
  check   （預設，無參數等同之）容器在跑時於 rust-api 容器內實跑 `cargo fmt --all --check`
          （**唯讀**、絕不寫檔）：未格式化即逐段計數＋摘要＋補救命令、非零退出；docker 不可用
          或容器未在跑＝**具名跳過** rc 0；容器在跑但 cargo-fmt 缺席（舊映像）＝fail-loud rc 2
  test    只跑自帶 self-test（離線、毫秒級；subprocess 全樁、不碰 docker）

★**為何非有不可**——rust-api 自 002 起全部手寫、從未跑過 rustfmt：容器 toolchain 只裝 minimal
profile（無 rustfmt component）、repo 無 rustfmt.toml，「風格一致」沒有任何機器判準（B-112）。
rev5 零 CI（ADR 0014），唯一機器守門面是 pre-commit；而 host 無 rust toolchain，`cargo fmt` 只
跑得動在容器內——本檔即「把容器內的檢查接進 pre-commit，同時不違反『stack 沒起時 hook MUST
可用』」這條既有紀律的承載體（ADR 0057 決定 3）。

★**刪掉它會怎樣**：格式回到「靠人記得在容器裡跑一次」，而 rev5 沒有第二道 fmt 防線
（零 CI）——漏跑零訊號、下一個人的 diff 裡混進大量與其改動無關的重排。
★**改壞被測物會怎樣**：任一 .rs 檔多一個空格／少一個換行 ⇒ 本閘 rc 1 並印出段數與前幾行
diff 摘要（落地當日對現庫實跑即此形：687 段、2.1s——存量尚未格式化，屬**真陽性**而非誤報；
存量一次格式化＝主線單獨一顆 commit、ADR 0057 決定 4）。

════════ 四態與退出碼（★跳過與通過在輸出上必須看得出差別） ════════

  ①docker 不在 PATH／repo 根缺 compose 兩檔          ⇒ ⤳ 具名跳過、rc 0
  ②rust-api 容器未在跑（`ps -q --status running` 空）⇒ ⤳ 具名跳過、rc 0（起 stack 後自動恢復實跑）
  ③容器在跑、`cargo fmt --all --check` rc 0          ⇒ ✓ 綠、rc 0（印耗時）
  ④容器在跑、rc≠0：
      stderr／stdout 含 `not installed`／`no such command` ⇒ ✗ 環境不可用 **rc 2**（附重建映像命令）
      其餘                                                ⇒ ✗ 未格式化 **rc 1**（段數＋摘要＋補救命令）

  ★**②與④的分流不可合併成「出錯就跳過」**：舊映像（未重建、無 rustfmt component）若靜默
  跳過，本閘就進入「守門動作恆不跑」——那正是 ADR 0024 全篇在消滅的失效類，故刻意 fail-loud、
  不設豁免（ADR 0057 決定 3、後果段）。
  ★跳過分支的存在意味著離線 commit 仍可能帶入未格式化碼——下一次 stack 在跑的 pin bump 會擋下，
  屬**延遲一站**而非漏網（ADR 0057 後果段）。
  ★`check` 檢查的是 rust-api **工作樹**內容、非 pin 指向的 commit：worktree 髒時多印一行警示
  （不影響 rc）；正常流程（子庫先 commit、再回外層 bump pin）下兩者一致。★該 git 呼叫必清
  GIT_*——否則 hook 洩漏的 GIT_INDEX_FILE 讓 git 對 worktree 當場 fatal，警示在 hook 路徑上
  成死碼（見 `worktree_dirty` docstring）。
  ★退出碼：0 綠或具名跳過／1 未格式化／2 環境不可用（cargo-fmt 缺席）／64 用法錯。

★**唯讀紀律（機器釘死）**：本檔對容器只下 `cargo fmt --all --check`；`--check` 被拿掉即成
「就地改寫 84 檔」的破壞性動作（存量格式化是主線的單獨一顆 commit、與任何功能改動隔離）。
self-test 案 `…read_only_check_form` 逐字比對實際下達的 argv，拿掉 `--check` 當場紅。

════════ 落點與接線（★逐處寫出、不寫「大致補完了」） ════════

  ①`.githooks/pre-commit`「rust 格式守門」段：staged 含 `rust-api` gitlink（pin bump）或本檔
    自身時跑 `check`。★跳過邏輯住本檔內、hook 段只做接線（ADR 0057 決定 3）——故 hook 段
    **無** Day-1 條件判斷，「stack 沒起 MUST 可用」由本檔的 ①②兩態承擔。
  ②`tools/docs-sync.py` `TOOLS_PY` 真表納冊（tools-cli 真表自本檔分派表掃源）＋
    `TestGateWiring` 之 `test_dry_run_rust_fmt_gate_trigger_conditions` 乾跑案釘住接線
    （hook 段整段被拆即紅——self-test 對該失效模式零效果，因 self-test 只隨 `test` 跑、
    而 `check` 的唯一觸發點正是被拆掉的那一段）。
  ③`.githooks/pre-commit` 的 `for t in …` 自測迴圈納冊（本檔 self-test **不**隨 `check`
    連帶跑——`check` 要走 docker、多跑一輪離線自測沒有收益，故走迴圈形、不入
    `HOOK_TEST_LOOP_EXEMPT`）。
  ④`tools/bootstrap.sh` `run_tool_test tools/rust-fmt-gate.py`（體檢節無條件全跑；★只接
    `test`——`check` 要 dev stack，而 bootstrap MUST 離線可用，同 route-artifact-gate 既有註）。
  ⑤`README.md` 目錄樹（Lint27 對賬）、`docs/ops/RUNBOOK.md` §12 命令表＋§12.3 rust 格式守門節。

★輸出紀律（同 tools/wf-watchdog.py）：一切輸出走 `_say()`（`print(..., flush=True)`）——
pre-commit 把 hook 輸出接管道時 python 預設塊緩衝，不 flush 的行會與後續閘的輸出錯序。
self-test 以檔文釘住「每個 print 皆帶 flush=True」。
"""
import contextlib
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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COMPOSE_FILES = ("docker-compose.yml", "docker-compose.dev.yml")
SERVICE = "rust-api"
SUB_DIR = "rust-api"
# `cargo fmt --check` 的每段 diff 以 `Diff in <路徑>:<行>:` 起頭——段數＝規模指標。
RE_DIFF_HUNK = re.compile(r"^Diff in ", re.M)
# 舊映像（無 rustfmt component）的兩種實際訊息：rustup 的 `… is not installed for the
# toolchain` 與 cargo 的 `no such command: fmt`。
NOT_INSTALLED_MARKERS = ("not installed", "no such command")
SUMMARY_HEAD = 12       # 紅訊息只印前 N 行 diff 摘要（全文動輒數千行、灌爆 hook 輸出）
_COMPOSE = "docker compose -f docker-compose.yml -f docker-compose.dev.yml"
REBUILD_CMD = f"{_COMPOSE} build rust-api && {_COMPOSE} up -d rust-api"
FIX_CMD = f"{_COMPOSE} exec -T rust-api cargo fmt --all"


def _say(msg, err=False):
    """單一輸出咽喉：每行即時 flush（hook 接管道時塊緩衝會讓輸出與其他閘錯序）。"""
    print(msg, file=sys.stderr if err else sys.stdout, flush=True)


def compose_argv(*args):
    """compose 呼叫的固定前綴＋子命令（★兩個 -f 缺一即讀不到 dev 覆寫、容器名對不上）。"""
    return ["docker", "compose", "-f", COMPOSE_FILES[0], "-f", COMPOSE_FILES[1], *args]


def _clean_git_env(environ):
    """濾掉 GIT_* 的環境副本（★只給對 rust-api 的 git 呼叫用、docker 那幾支不需要）。

    同 tools/wire-schema.py `_clean_git_env`／tools/fork-delta-lint.py `sh()` 既有慣例。
    """
    return {k: v for k, v in environ.items() if not k.startswith("GIT_")}


def _sh(argv, root, env=None):
    """外部呼叫單一咽喉（self-test 一律樁掉本函式的 subprocess.run）。

    `env=None`＝繼承本行程環境（docker compose 各呼叫走此形）。
    """
    return subprocess.run(argv, cwd=root, capture_output=True, encoding="utf-8",
                          errors="replace", env=env)


def docker_skip_reason(root):
    """①態判定：docker 不可用的具名理由（可用＝回 None）。"""
    if shutil.which("docker") is None:
        return "docker 不在 PATH"
    missing = [n for n in COMPOSE_FILES if not os.path.isfile(os.path.join(root, n))]
    if missing:
        return "repo 根缺 " + "、".join(missing)
    return None


def container_is_running(root):
    """②態判定：`ps -q --status running rust-api` 有輸出即在跑。

    ★ps 本身非零（daemon 未起、compose 檔解析失敗）一律歸「未在跑」——輸出為空，補救動作
    同樣是「把 stack 起起來」，不另立第五態。
    """
    r = _sh(compose_argv("ps", "-q", "--status", "running", SERVICE), root)
    return bool((r.stdout or "").strip())


def worktree_dirty(root):
    """rust-api worktree 是否有未 commit 變動（純警示用、不影響 rc）。

    ★git 呼叫**必清 GIT_***：本工具的主要呼叫點是 pre-commit，而 git 跑 hook 時一定把外層
    repo 的 GIT_INDEX_FILE 洩漏給子行程（一般 commit＝相對 `.git/index`；`git commit -a`／
    pathspec commit＝絕對 `.git/index.lock`／`.git/next-index-<PID>.lock`）。該變數優先權高於
    `-C`，而 rust-api 是 worktree（`.git` 為檔非目錄）⇒ 兩種形式都讓 git 當場 fatal（實測
    rc 128、stdout 空：相對形報 `.git/index: Not a directory`、絕對形報 `unable to load
    config blob object`）⇒ 本函式恆回 False、④附加的髒警示在**唯一的主要呼叫點**成死碼
    （只有人工 CLI 直跑才看得到）。rc 語意不受影響——四態分流與 `--check` 實跑照常。
    """
    r = _sh(["git", "-C", os.path.join(root, SUB_DIR), "status", "--porcelain"], root,
            env=_clean_git_env(os.environ))
    return bool((r.stdout or "").strip())


def fmt_verdict(rc, stdout, stderr, elapsed):
    """純判定：`cargo fmt --all --check` 的 (rc, stdout, stderr) → (本閘 rc, 訊息行列)。"""
    if rc == 0:
        return 0, [f"[rust-fmt-gate] ✓ rustfmt 全綠（{elapsed:.1f}s）"]
    blob = (stderr + stdout).lower()
    if any(m in blob for m in NOT_INSTALLED_MARKERS):
        return 2, [f"[rust-fmt-gate] ✗ 容器內 cargo-fmt 缺席（映像未含 rustfmt component、"
                   f"{elapsed:.1f}s）——環境不可用，**刻意 fail-loud、不靜默跳過**"
                   f"（靜默跳過＝守門動作恆不跑；ADR 0057 決定 3）",
                   f"  重建映像：{REBUILD_CMD}"]
    hunks = len(RE_DIFF_HUNK.findall(stdout))
    body = (stdout if hunks else (stdout + stderr)).splitlines()[:SUMMARY_HEAD]
    note = "" if hunks else "（未見 `Diff in` 段——可能非格式差異而是解析失敗，見摘要）"
    lines = [f"[rust-fmt-gate] ✗ rustfmt 未通過：{hunks} 段 diff"
             f"（cargo rc {rc}、{elapsed:.1f}s）{note}——前 {len(body)} 行摘要："]
    lines += [f"  {ln}" for ln in body]
    lines.append(f"  補救：容器內跑 `{FIX_CMD}` 後重新 stage"
                 f"（設定＝rust-api/rustfmt.toml；B-112／ADR 0057）")
    return 1, lines


def run_check(root):
    """四態判定的組裝：→ (rc, 訊息行列)。純回傳、不自己印（self-test 逐態比對行文）。"""
    reason = docker_skip_reason(root)
    if reason:
        return 0, [f"[rust-fmt-gate] ⤳ 跳過：docker 不可用（{reason}）"
                   f"——docker 與 compose 檔就位後自動恢復實跑"]
    if not container_is_running(root):
        return 0, [f"[rust-fmt-gate] ⤳ 跳過：rust-api 容器未在跑"
                   f"——起 stack 後自動恢復實跑；自律補救＝容器內 cargo fmt --all（{FIX_CMD}）"]
    lines = []
    if worktree_dirty(root):
        lines.append("[rust-fmt-gate] ⚠ rust-api worktree 有未 commit 變動"
                     "——檢查的是工作樹、非 pin 之 commit（正常流程下兩者一致）")
    t0 = time.perf_counter()
    r = _sh(compose_argv("exec", "-T", SERVICE, "cargo", "fmt", "--all", "--check"), root)
    rc, verdict = fmt_verdict(r.returncode, r.stdout or "", r.stderr or "",
                              time.perf_counter() - t0)
    return rc, lines + verdict


def cmd_check():
    """實跑：四態判定 → 逐行輸出（紅走 stderr、綠與跳過走 stdout）。"""
    rc, lines = run_check(REPO_ROOT)
    for ln in lines:
        _say(ln, err=bool(rc))
    return rc


# ── self-test（離線、毫秒級；subprocess 全樁、不碰 docker）────────────────────

PROG = "tools/rust-fmt-gate.py"
FAKE_DOCKER = "/usr/bin/docker"          # shutil.which 的樁回值（離線自測不得依賴真 docker）
FMT_DIRTY_OUT = ("Diff in /app/server/src/a.rs:1:\n"
                 "-use x::{b, a};\n"
                 "+use x::{a, b};\n"
                 "Diff in /app/server/src/b.rs:9:\n"
                 "-fn f() ->i32 { 1 }\n"
                 "+fn f() -> i32 { 1 }\n")
FMT_NOT_INSTALLED_ERR = ("error: 'cargo-fmt' is not installed for the toolchain '1.96.1-x86_64"
                         "-unknown-linux-gnu'\n")
# hook 洩漏 GIT_INDEX_FILE 時真 git 對 worktree 的實測收場（rc 128、stdout 空）。
GIT_LEAK_FATAL_ERR = "fatal: .git/index: index file open failed: Not a directory\n"
# ★只有「指路」的這三個會讓 git 對 worktree 當場 fatal——GIT_EDITOR 之類無害者不列，
# 否則樁比真 git 嚴，測試結果會隨呼叫者的環境飄（生產面仍照慣例清掉全部 GIT_*）。
GIT_LEAK_FATAL_VARS = ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE")


def _completed(argv, rc, stdout="", stderr=""):
    return subprocess.CompletedProcess(argv, rc, stdout, stderr)


def _stub_run(running=True, fmt_rc=0, fmt_out="", fmt_err="", dirty="", log=None):
    """樁 subprocess.run：依 argv 分流（compose ps／git status／compose exec cargo fmt）。"""
    def run(argv, **kw):
        if log is not None:
            log.append(list(argv))
        if argv[0] == "git":
            # ★忠實模擬真 git：環境裡還帶著 hook 洩漏的 GIT_INDEX_FILE／GIT_DIR／
            # GIT_WORK_TREE 時，對 worktree（`.git` 為檔）跑 git 即 fatal——rc 128、
            # stdout 空。樁成「恆回乾淨輸出」等於把本失效模式從自測視野裡刪掉
            # （原樁 `**_kw` 全吞即此形）。
            env = kw.get("env")
            seen = os.environ if env is None else env
            if any(k in seen for k in GIT_LEAK_FATAL_VARS):
                return _completed(argv, 128, "", GIT_LEAK_FATAL_ERR)
            return _completed(argv, 0, dirty, "")
        if "ps" in argv:
            return _completed(argv, 0, "c0ffee\n" if running else "", "")
        return _completed(argv, fmt_rc, fmt_out, fmt_err)
    return run


class _FakeRoot:
    """合成 repo 根：預設含 compose 兩檔（`with` 內回路徑）。"""

    def __init__(self, compose=True):
        self._compose = compose
        self._tmp = None

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        if self._compose:
            for name in COMPOSE_FILES:
                with open(os.path.join(self._tmp.name, name), "w", encoding="utf-8") as fh:
                    fh.write("services: {}\n")
        return self._tmp.name

    def __exit__(self, *_exc):
        self._tmp.cleanup()


class TestSkipStates(unittest.TestCase):
    """①②具名跳過兩態：rc 0，且訊息**指名跳過原因**（跳過與通過在輸出上必須不同——
    「不適用」與「檢了通過」長一樣即失守，rev4:FR-012 假綠面）。"""

    def test_skip_when_docker_missing_from_path(self):
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=None), \
                unittest.mock.patch("subprocess.run", side_effect=AssertionError("不得呼叫")):
            rc, lines = run_check(root)
        self.assertEqual(rc, 0, msg=str(lines))
        self.assertIn("跳過：docker 不可用", "\n".join(lines))

    def test_skip_when_compose_files_absent(self):
        """★與上一案分開釘（判準兩端獨立）：`docker` 在 PATH、但 repo 根沒有 compose 檔
        （fresh clone／被搬移）——併成一案時任一半的條件被拆掉都仍全綠。"""
        with _FakeRoot(compose=False) as root, \
                unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run", side_effect=AssertionError("不得呼叫")):
            rc, lines = run_check(root)
        self.assertEqual(rc, 0, msg=str(lines))
        text = "\n".join(lines)
        self.assertIn("跳過：docker 不可用", text)
        self.assertIn(COMPOSE_FILES[0], text)

    def test_skip_when_container_not_running(self):
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run", side_effect=_stub_run(running=False)):
            rc, lines = run_check(root)
        self.assertEqual(rc, 0, msg=str(lines))
        text = "\n".join(lines)
        self.assertIn("rust-api 容器未在跑", text)
        self.assertIn("起 stack 後自動恢復實跑", text)


class TestRunningStates(unittest.TestCase):
    """③④容器在跑三態：綠／未格式化 rc 1／cargo-fmt 缺席 rc 2。"""

    def test_green_when_formatted(self):
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run", side_effect=_stub_run(fmt_rc=0)):
            rc, lines = run_check(root)
        self.assertEqual(rc, 0, msg=str(lines))
        self.assertIn("rustfmt 全綠", "\n".join(lines))

    def test_red_with_hunk_count_when_unformatted(self):
        """rc 1＋段數（fixture 恰兩段）＋摘要行＋補救命令——四者缺一即紅訊息沒有可操作性。"""
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run",
                                    side_effect=_stub_run(fmt_rc=1, fmt_out=FMT_DIRTY_OUT)):
            rc, lines = run_check(root)
        text = "\n".join(lines)
        self.assertEqual(rc, 1, msg=text)
        self.assertIn("2 段 diff", text)
        self.assertIn("Diff in /app/server/src/a.rs:1:", text)
        self.assertIn("cargo fmt --all", text)

    def test_fail_loud_when_cargo_fmt_absent(self):
        """★rc 2、**不是**靜默跳過：舊映像若被當成「跳過」，本閘即進入守門恆不跑
        （ADR 0024 全篇要消滅的失效類；ADR 0057 決定 3 明令不設豁免）。"""
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run",
                                    side_effect=_stub_run(fmt_rc=101,
                                                          fmt_err=FMT_NOT_INSTALLED_ERR)):
            rc, lines = run_check(root)
        text = "\n".join(lines)
        self.assertEqual(rc, 2, msg=text)
        self.assertIn("cargo-fmt 缺席", text)
        self.assertIn("build rust-api", text)

    def test_dirty_worktree_warns_without_changing_rc(self):
        """④附加：worktree 髒＝多印一行警示（檢的是工作樹、非 pin 之 commit），rc 不變。"""
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run",
                                    side_effect=_stub_run(fmt_rc=0, dirty=" M server/src/a.rs\n")):
            rc, lines = run_check(root)
        text = "\n".join(lines)
        self.assertEqual(rc, 0, msg=text)
        self.assertIn("非 pin 之 commit", text)
        # 反向成對：乾淨時**不得**出現該警示（恆印＝訊息失去鑑別力）。
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run", side_effect=_stub_run(fmt_rc=0, dirty="")):
            _rc, clean_lines = run_check(root)
        self.assertNotIn("非 pin 之 commit", "\n".join(clean_lines))

    def test_dirty_warning_survives_hook_leaked_git_index_file(self):
        """★pre-commit 真實路徑釘死（本工具的主要呼叫點正是 hook）：git 跑 hook 時必洩漏
        GIT_INDEX_FILE 給子行程，其優先權高於 `-C`，而 rust-api 是 worktree（`.git` 為檔）
        ⇒ 真 git rc 128、stdout 空。不清 GIT_* 則 worktree_dirty() 恆 False、④附加警示在
        hook 路徑上成死碼（ADR 0057 後果段明記的行為當場失效），而人工 CLI 直跑仍看得到
        ⇒ 徵狀極難歸因。把 env 傳回 None（或 `_clean_git_env` 改成 identity）即紅。"""
        saved = os.environ.get("GIT_INDEX_FILE")
        os.environ["GIT_INDEX_FILE"] = ".git/index"     # 一般 commit 之 hook 實測值
        try:
            with _FakeRoot() as root, \
                    unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                    unittest.mock.patch("subprocess.run",
                                        side_effect=_stub_run(fmt_rc=0,
                                                              dirty=" M server/src/a.rs\n")):
                rc, lines = run_check(root)
        finally:
            if saved is None:
                os.environ.pop("GIT_INDEX_FILE", None)
            else:
                os.environ["GIT_INDEX_FILE"] = saved
        text = "\n".join(lines)
        self.assertEqual(rc, 0, msg=text)
        self.assertIn("非 pin 之 commit", text)

    def test_exec_argv_is_read_only_check_form(self):
        """★唯讀紀律機器釘死：下給容器的 argv 逐字比對——`--check` 被拿掉即成「就地改寫
        84 檔」的破壞性動作（存量格式化屬主線單獨一顆 commit、ADR 0057 決定 4），而黑箱
        rc 比對對此完全無感（改寫成功時 rc 也是 0）。"""
        log = []
        with _FakeRoot() as root, unittest.mock.patch("shutil.which", return_value=FAKE_DOCKER), \
                unittest.mock.patch("subprocess.run", side_effect=_stub_run(fmt_rc=0, log=log)):
            run_check(root)
        self.assertIn(["docker", "compose", "-f", "docker-compose.yml", "-f",
                       "docker-compose.dev.yml", "exec", "-T", "rust-api",
                       "cargo", "fmt", "--all", "--check"], log, msg=str(log))


class TestUsageAndOutput(unittest.TestCase):
    def test_usage_guard_rejects_unknown_subcommand(self):
        """用法守衛（形同 view-render-guard／seed-view-gate／route-artifact-gate）：未知子命令
        ⇒ 印用法、rc 64（★全庫四支既有納冊工具一致；RUNBOOK 退出碼段亦以 64 記「用法錯」）。"""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = main([PROG, "nope"])
        self.assertEqual(rc, 64)
        self.assertIn("用法：", err.getvalue())

    def test_every_print_flushes(self):
        """★輸出紀律檔文釘死（同 wf-watchdog）：本檔每個 print 呼叫皆帶 flush=True。"""
        with open(__file__, encoding="utf-8") as fh:
            src = fh.read()
        offenders = [ln for ln in src.splitlines()
                     if "print(" in ln and "flush=True" not in ln]
        self.assertEqual(offenders, [], msg=str(offenders))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        if result.wasSuccessful():
            _say("[rust-fmt-gate] ✓ self-test 過（①docker 缺席／compose 檔缺席兩跳過態、"
                 "②容器未跑跳過、③綠、④未格式化 rc1＋段數、⑤cargo-fmt 缺席 rc2 fail-loud、"
                 "⑥worktree 髒警示成對＋GIT_* 洩漏免疫、⑦唯讀 argv 逐字、⑧用法守衛、"
                 "⑨print 全 flush）")
            return 0
        return 1
    if cmd != "check":
        _say(f"用法：{argv[0]} [check|test]", err=True)
        return 64
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
