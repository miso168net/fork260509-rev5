#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/walkthrough-baseline.py — CDP 真登入走查前後的全表基準對賬（B-147；L-071 防法①的機制化）

子命令：
  snapshot <檔>   取 rev5 dev stack 實庫＋redis 現況三面、寫成 JSON 基準檔（走查**前**跑）
  diff <檔>       重取現況、與基準檔逐值比對、只列有差者＋末行摘要（走查**後**清理完跑；
                  ★rc 0 才算「環境已還原」——三閘綠不算，L-055／L-071 招牌徵狀＝三閘綠而全量紅）
  test            自帶 self-test（unittest、離線、零 docker；subprocess 全樁）
  選項（snapshot／diff 共用）：`--user U`／`--db D`（預設同 tools/schema-gate.py 常數）。
  `<檔>` 為必填位置引數、無隱含預設落點（契約用法落 tmp/、見 RUNBOOK 走查還原契約節）。

三面（★全部現算、零手抄名冊——清單式防法已被 L-071 證偽：006 的清單擋不住 007 的組合）：
  ①表：public schema **全部**表的列數（表清單自 information_schema.tables 現算、逐表 count(*)
    以單一 UNION ALL 一次撈；含 seaql_migrations——它也是一張表、不豁免）
  ②序列：public schema **全部**序列的 last_value＋is_called（清單自 pg_class relkind='S' 現算）
  ③redis：DBSIZE 總數＋逐前綴鍵數（`--scan` 全鍵**去重後**分組——SCAN 只保證「至少一次」；
    DBSIZE 與去重鍵數互證、不等出提示；前綴＝鍵第一個冒號前段、無冒號者歸「(無前綴)」；
    前綴名冊亦不手抄——rust-api 現行 session:／throttle:／cpwd: 三前綴只是今天的值）
  基準檔另帶 taken_at（UTC ISO）與 schema_version（檔形演進用）；diff 忽略 taken_at。

退出碼：0 全等／1 有差／2 環境或結構異常（docker 不可執行、psql／redis 失敗、基準檔缺席或壞形、
★比對面為空＝零表或零序列——空面的全綠是假綠、同 schema-gate 紀律，snapshot 與 diff 皆然）／
64 用法錯（usage 走 stderr）。

唯讀紀律（self-test 逐字釘住）：pg 只下 SELECT（含目錄視圖）、redis 只下 DBSIZE／--scan；
pg 走 `docker compose … exec -T postgres psql -U … -d … -At -F <分隔>`；redis 走
`exec -T redis sh -c` 以 `$(cat /run/secrets/redis_password)` 取密（同 compose healthcheck 形、
`--no-auth-warning`）——密碼值只在容器內 sh 展開，host argv 與本工具任何輸出皆不含。
★只准指向 rev5 dev stack（compose 專案＝倉庫根）；絕不指向 rev4 對照 stack。

出處：B-147 候選①；L-071 防法①（走查前取全表基準、後逐值比對——不變式取代清單）＋②（清理面
的定義＝走查期間被寫過的一切、與任何閘的射程無關）；L-055（runtime-append 殘列兩條爆線）。
入冊：docs-sync TOOLS_PY＋pre-commit `for t in …` 自測迴圈（不入 HOOK_TEST_LOOP_EXEMPT）＋
bootstrap run_tool_test＋README 樹＋RUNBOOK §12 表；★不掛 pre-commit 條件觸發（要 dev stack、
且走查收尾才有意義）——走查前後手動跑。stdlib-only（ADR 0010）；連字檔名＝CLI、不可 import。
"""
import contextlib
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DB 身分：與 tools/schema-gate.py 之 DB_USER／DB_NAME **同值**（連字檔名 CLI 不可 import、故自帶；
# 兩處若分歧，本工具會對著不存在的庫報 rc 2、不會靜默比錯庫）。
DB_USER = "soybean"
DB_NAME = "soybean_admin_rust"
# compose 前綴同 schema-gate 形（兩個 -f 缺一即讀不到 dev 覆寫）；`-T` 必帶（非 tty、hook／管道可跑）。
COMPOSE_EXEC = ["docker", "compose", "-f", "docker-compose.yml",
                "-f", "docker-compose.dev.yml", "exec", "-T"]
PG_SERVICE = "postgres"
REDIS_SERVICE = "redis"
REDIS_PASSWORD_FILE = "/run/secrets/redis_password"
# ★密碼只在容器內 sh 展開（同 docker-compose.yml redis healthcheck 形）；host 端只見這行字面。
REDIS_CLI = f'redis-cli -a "$(cat {REDIS_PASSWORD_FILE})" --no-auth-warning'
PSQL_SEP = "\t"          # psql -F 分隔（表名／序列名不含 tab）
SCHEMA_VERSION = 1       # 基準檔形版本；改檔形即 bump、舊檔 diff 走 rc 2 而非誤比
NO_PREFIX = "(無前綴)"
STARTUP_HINT = ("docker compose -f docker-compose.yml -f docker-compose.dev.yml "
                "up -d --wait postgres redis")

RC_OK, RC_DIFF, RC_ENV, RC_USAGE = 0, 1, 2, 64
PROG = "tools/walkthrough-baseline.py"

SQL_TABLES = ("SELECT table_name FROM information_schema.tables "
              "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1")
SQL_SEQUENCES = ("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                 "WHERE c.relkind='S' AND n.nspname='public' ORDER BY 1")


class BaselineError(Exception):
    """環境或結構異常（docker 不可執行、psql／redis 失敗、基準檔缺席或壞形、比對面為空）→ rc 2。"""


def _say(msg, err=False):
    """單一輸出咽喉：每行即時 flush（接管道時塊緩衝會讓輸出錯序；同 rust-fmt-gate 慣例）。"""
    print(msg, file=sys.stderr if err else sys.stdout, flush=True)


# ── 外部呼叫（唯讀）──────────────────────────────────────────────────────────

def _run_docker(argv, run):
    """docker 子行程統一入口：docker 執行不起來（OSError）＝環境異常 rc 2、附啟動命令。"""
    try:
        return run(argv, capture_output=True, text=True, cwd=REPO_ROOT)
    except OSError as ex:
        raise BaselineError(f"無法執行 docker（{ex}）——本工具需 rev5 dev stack 在跑；"
                            f"啟動：{STARTUP_HINT}") from None


def psql_argv(sql, user=DB_USER, db=DB_NAME):
    """psql 唯讀撈取的 argv（`-At` 無表頭純值、`-F` 指定欄分隔、ON_ERROR_STOP 讓 SQL 錯即非零）。"""
    return COMPOSE_EXEC + [PG_SERVICE, "psql", "-U", user, "-d", db, "-At", "-F", PSQL_SEP,
                          "-v", "ON_ERROR_STOP=1", "-c", sql]


def psql_rows(sql, user, db, run):
    """跑一句 SELECT → 列表（每列＝依 PSQL_SEP 切欄的 list）；psql 非零＝rc 2。"""
    r = _run_docker(psql_argv(sql, user, db), run)
    if r.returncode != 0:
        raise BaselineError(f"psql 失敗（rc={r.returncode}）：{(r.stderr or '').strip()[:300]}"
                            f"——補救：dev stack 未起→{STARTUP_HINT}")
    return [ln.split(PSQL_SEP) for ln in (r.stdout or "").splitlines() if ln.strip()]


def redis_argv(command):
    """redis-cli 讀命令的 argv：`exec -T redis sh -c '<REDIS_CLI> <command>'`——密碼由容器內 sh 取。"""
    return COMPOSE_EXEC + [REDIS_SERVICE, "sh", "-c", f"{REDIS_CLI} {command}"]


def redis_out(command, run):
    """跑一個 redis 讀命令 → stdout 原文；非零＝rc 2。"""
    r = _run_docker(redis_argv(command), run)
    if r.returncode != 0:
        raise BaselineError(f"redis-cli 失敗（rc={r.returncode}）："
                            f"{(r.stderr or '').strip()[:300]}——補救：dev stack 未起→{STARTUP_HINT}")
    return r.stdout or ""


def _ident(name):
    """雙引號識別字（表名／序列名來自目錄、仍照規矩引住）。"""
    return '"' + name.replace('"', '""') + '"'


def _literal(name):
    """單引號字串常值（UNION ALL 各列的自帶名欄）。"""
    return "'" + name.replace("'", "''") + "'"


# ── 三面現算 ────────────────────────────────────────────────────────────────

def fetch_tables(user, db, run):
    """①表面：public 全部表 → {表名: 列數}。零表＝比對面為空 → rc 2。"""
    names = [row[0] for row in psql_rows(SQL_TABLES, user, db, run)]
    if not names:
        raise BaselineError("比對面為空：public schema 零表——空面的全等是假綠（庫錯、schema 未建）")
    sql = " UNION ALL ".join(f"SELECT {_literal(n)}, count(*) FROM {_ident(n)}" for n in names)
    rows = psql_rows(sql, user, db, run)
    try:
        got = {row[0]: int(row[1]) for row in rows}
    except (ValueError, IndexError):
        raise BaselineError("表列數輸出不可解（psql -At 每列應為「表名<分隔>列數」）："
                            f"{rows[:3]!r}——輸出被污染或 psql 形改變") from None
    if sorted(got) != sorted(names):
        raise BaselineError(f"表列數撈取不完整：清單 {len(names)} 表、撈得 {len(got)} 表")
    return got


def fetch_sequences(user, db, run):
    """②序列面：public 全部序列 → {序列名: {last_value, is_called}}。零序列 → rc 2。"""
    names = [row[0] for row in psql_rows(SQL_SEQUENCES, user, db, run)]
    if not names:
        raise BaselineError("比對面為空：public schema 零序列——空面的全等是假綠")
    sql = " UNION ALL ".join(
        f"SELECT {_literal(n)}, last_value, is_called FROM {_ident(n)}" for n in names)
    rows = psql_rows(sql, user, db, run)
    try:
        got = {row[0]: {"last_value": int(row[1]), "is_called": row[2] == "t"} for row in rows}
    except (ValueError, IndexError):
        raise BaselineError("序列值輸出不可解（psql -At 每列應為「序列名<分隔>last_value"
                            f"<分隔>is_called」）：{rows[:3]!r}——輸出被污染或 psql 形改變") from None
    if sorted(got) != sorted(names):
        raise BaselineError(f"序列撈取不完整：清單 {len(names)} 序列、撈得 {len(got)} 序列")
    return got


def group_prefixes(keys):
    """redis 鍵 → {前綴: 鍵數}；前綴＝第一個冒號前段、無冒號者歸 NO_PREFIX；空行略。"""
    out = {}
    for k in keys:
        k = k.strip()
        if not k:
            continue
        prefix = k.split(":", 1)[0] if ":" in k else NO_PREFIX
        out[prefix or NO_PREFIX] = out.get(prefix or NO_PREFIX, 0) + 1
    return out


def fetch_redis(run):
    """③redis 面：DBSIZE 總數＋ --scan 全鍵**去重後**逐前綴分組；零鍵是合法狀態、不算空面。

    ★去重不可省：SCAN 契約只保證「全程存在的鍵至少回傳一次」——rehash 期間會重複回傳同一把，
    逐行累加即把一把算成多把；走查前後兩次取樣重複度不同時，diff 報出實際不存在的殘鍵＝假紅。
    ★DBSIZE 另取並與去重鍵數互證（不等即出提示、不改 rc——取樣間有鍵過期或寫入屬正常，
    嚴格相等會偶發不成立；長期偏離＝SCAN 被截斷之徵）。
    """
    raw = redis_out("DBSIZE", run).strip()
    try:
        dbsize = int(raw)
    except ValueError:
        raise BaselineError(f"redis DBSIZE 回非整數：{raw[:80]!r}") from None
    keys = sorted({k.strip() for k in redis_out("--scan", run).splitlines() if k.strip()})
    prefixes = group_prefixes(keys)
    total = sum(prefixes.values())
    if total != dbsize:
        _say(f"[walkthrough-baseline] 提示：--scan 去重後 {total} 鍵、DBSIZE {dbsize}——兩面不等"
             "（取樣間有鍵過期或寫入即屬正常；長期偏離請查 SCAN 是否被截斷）", err=True)
    return {"dbsize": dbsize, "prefixes": prefixes}


def snapshot_live(user=DB_USER, db=DB_NAME, run=subprocess.run, now=None):
    """三面現算 → 基準 dict（含 taken_at UTC ISO＋schema_version）。"""
    taken = now or datetime.datetime.now(datetime.timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION,
        "taken_at": taken.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tables": fetch_tables(user, db, run),
        "sequences": fetch_sequences(user, db, run),
        "redis": fetch_redis(run),
    }


# ── 基準檔 ──────────────────────────────────────────────────────────────────

def validate_snapshot(obj):
    """檔形斷言（fail-loud）：缺鍵／型別錯／版本不符／零表零序列 → BaselineError。"""
    if not isinstance(obj, dict):
        raise BaselineError("基準檔壞形：頂層非 object")
    if obj.get("schema_version") != SCHEMA_VERSION:
        raise BaselineError(f"基準檔壞形：schema_version={obj.get('schema_version')!r}"
                            f"、本工具只認 {SCHEMA_VERSION}（重新 snapshot）")
    tables = obj.get("tables")
    if not isinstance(tables, dict) or not tables \
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in tables.values()):
        raise BaselineError("基準檔壞形：tables 須為非空 {表名: 整數列數}")
    seqs = obj.get("sequences")
    if not isinstance(seqs, dict) or not seqs or not all(
            isinstance(v, dict) and isinstance(v.get("last_value"), int)
            and isinstance(v.get("is_called"), bool) for v in seqs.values()):
        raise BaselineError("基準檔壞形：sequences 須為非空 {序列名: {last_value, is_called}}")
    redis = obj.get("redis")
    if not isinstance(redis, dict) or not isinstance(redis.get("dbsize"), int) \
            or not isinstance(redis.get("prefixes"), dict) \
            or not all(isinstance(v, int) for v in redis["prefixes"].values()):
        raise BaselineError("基準檔壞形：redis 須為 {dbsize: 整數, prefixes: {前綴: 整數}}")
    return obj


def load_snapshot(path):
    """讀基準檔：缺席／非 JSON／壞形 → BaselineError（rc 2）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
    except FileNotFoundError:
        raise BaselineError(f"基準檔缺席：{path}——走查前須先 snapshot") from None
    except (OSError, json.JSONDecodeError) as ex:
        raise BaselineError(f"基準檔讀取或解析失敗：{path}：{ex}") from None
    return validate_snapshot(obj)


def dump_snapshot(snap, path):
    """寫基準檔（indent＋sort_keys＝可讀、可 diff）；寫入失敗 → BaselineError。"""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snap, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
    except OSError as ex:
        raise BaselineError(f"基準檔寫入失敗：{path}：{ex}") from None


# ── 比對（純函式）───────────────────────────────────────────────────────────

def _seq_text(v):
    return f"last_value={v['last_value']},is_called={'t' if v['is_called'] else 'f'}"


def diff_snapshots(base, live):
    """逐值比對 → 差異列（dict：face／name／base／live／delta）；只列有差者、忽略 taken_at。"""
    rows = []
    absent = "（無）"

    def _int_rows(face, bmap, lmap, missing=None):
        """missing=None＝缺席即「（無）」（表不存在≠0 列）；redis 前綴缺席＝0 鍵、傳 0。"""
        for name in sorted(set(bmap) | set(lmap)):
            b, l = bmap.get(name, missing), lmap.get(name, missing)
            if b != l:
                rows.append({"face": face, "name": name,
                             "base": absent if b is None else b,
                             "live": absent if l is None else l,
                             "delta": (l - b) if (b is not None and l is not None) else "—"})

    _int_rows("表", base["tables"], live["tables"])
    for name in sorted(set(base["sequences"]) | set(live["sequences"])):
        b, l = base["sequences"].get(name), live["sequences"].get(name)
        if b != l:
            rows.append({"face": "序列", "name": name,
                         "base": absent if b is None else _seq_text(b),
                         "live": absent if l is None else _seq_text(l),
                         "delta": (l["last_value"] - b["last_value"]) if (b and l) else "—"})
    if base["redis"]["dbsize"] != live["redis"]["dbsize"]:
        rows.append({"face": "redis", "name": "DBSIZE",
                     "base": base["redis"]["dbsize"], "live": live["redis"]["dbsize"],
                     "delta": live["redis"]["dbsize"] - base["redis"]["dbsize"]})
    _int_rows("redis", base["redis"]["prefixes"], live["redis"]["prefixes"], missing=0)
    return rows


def _face_counts(snap):
    return (len(snap["tables"]), len(snap["sequences"]), snap["redis"]["dbsize"],
            len(snap["redis"]["prefixes"]))


def render_diff(rows, live):
    """差異列 → 輸出行；空差異＝一行「全等」（附三面規模，證明比對面非空）。"""
    t, s, k, p = _face_counts(live)
    if not rows:
        return [f"[walkthrough-baseline] ✓ 全等（表 {t}／序列 {s}／redis {k} 鍵、{p} 前綴）"]
    lines = ["[walkthrough-baseline] ✗ 與基準有差——面｜名｜基準值｜現值｜差"]
    lines += [f"  {r['face']}｜{r['name']}｜{r['base']}｜{r['live']}｜{r['delta']}" for r in rows]
    n = {face: sum(1 for r in rows if r["face"] == face) for face in ("表", "序列", "redis")}
    lines.append(f"[walkthrough-baseline] 摘要：表 {n['表']} 項差／序列 {n['序列']} 項差／"
                 f"redis {n['redis']} 項差（比對面：表 {t}／序列 {s}／redis {k} 鍵、{p} 前綴）")
    return lines


# ── 子命令 ──────────────────────────────────────────────────────────────────

def cmd_snapshot(path, user, db, run=subprocess.run):
    snap = snapshot_live(user, db, run)
    dump_snapshot(snap, path)
    t, s, k, p = _face_counts(snap)
    _say(f"[walkthrough-baseline] ✓ 基準已寫：{path}（表 {t}／序列 {s}／redis {k} 鍵、{p} 前綴；"
         f"taken_at {snap['taken_at']}）")
    return RC_OK


def cmd_diff(path, user, db, run=subprocess.run):
    base = load_snapshot(path)
    # 現況**不**再過 validate_snapshot：它檢查的每一項在這條路徑上都是恆真（schema_version 由
    # snapshot_live 自己塞、零表零序列已由 fetch_* fail-loud、值型別由 int()／建構過程保證），
    # 沒有任何輸入能讓它拒絕——讀起來像第二道防線、實際是空轉（變異測試殺不死）。真正的守門
    # 在 fetch_tables／fetch_sequences／fetch_redis 各自的 fail-loud，放寬那裡就是真的沒有兜底。
    live = snapshot_live(user, db, run)
    rows = diff_snapshots(base, live)
    for ln in render_diff(rows, live):
        _say(ln, err=bool(rows))
    return RC_DIFF if rows else RC_OK


def usage(msg=None):
    if msg:
        _say(f"[walkthrough-baseline] 用法錯：{msg}", err=True)
    _say(f"用法：python3 {PROG} snapshot <檔> [--user U] [--db D]\n"
         f"      python3 {PROG} diff <檔> [--user U] [--db D]\n"
         f"      python3 {PROG} test\n"
         f"  snapshot＝走查前取三面基準寫 JSON；diff＝走查後重取現況逐值比對（rc 0 才算環境已還原）；"
         f"退出碼 0 全等／1 有差／2 環境或結構異常／64 用法錯", err=True)
    return RC_USAGE


def _parse_opts(args):
    """`--user U`／`--db D` 手寫解析（沿 schema-gate 形）；回 (user, db) 或 usage 錯誤訊息。"""
    user, db = DB_USER, DB_NAME
    i = 0
    while i < len(args):
        flag = args[i]
        if flag not in ("--user", "--db"):
            return None, f"未知旗標或多餘引數：{flag}"
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            return None, f"旗標 {flag} 缺值"
        if flag == "--user":
            user = args[i + 1]
        else:
            db = args[i + 1]
        i += 2
    return (user, db), None


def main(argv, run=subprocess.run):
    if len(argv) < 2:
        return usage()
    cmd = argv[1]
    if cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        if result.wasSuccessful():
            _say(f"[walkthrough-baseline] ✓ self-test 過（{result.testsRun} 案：diff 純函式六形、"
                 "前綴分組與 SCAN 去重、DBSIZE 互證、JSON 往返、基準檔缺席／壞形（含型別）、"
                 "空面與撈取截斷 rc 2、"
                 "psql 輸出不可解 rc 2、退出碼四態＋字面契約、用法、psql／redis 命令構造與唯讀、"
                 "目錄 SQL 與 count 腿抗窄化、密碼不出 argv、print 全 flush）")
            return RC_OK
        return RC_DIFF
    if cmd in ("snapshot", "diff"):
        if len(argv) < 3 or argv[2].startswith("--"):
            return usage(f"{cmd} 需要 <檔> 位置引數（無隱含預設落點）")
        opts, err = _parse_opts(argv[3:])
        if err:
            return usage(err)
        user, db = opts
        try:
            if cmd == "snapshot":
                return cmd_snapshot(argv[2], user, db, run)
            return cmd_diff(argv[2], user, db, run)
        except BaselineError as ex:
            _say(f"[walkthrough-baseline] ✗ 環境或結構異常：{ex}", err=True)
            return RC_ENV
    return usage(f"未知子命令：{cmd}")


# ── self-test（離線、subprocess 全樁、零 docker）──────────────────────────────

FAKE_TABLES = {"sys_user": 3, "sys_token": 0, "seaql_migrations": 7}
FAKE_SEQS = {"sys_user_id_seq": (3, "t"), "sys_token_id_seq": (1, "f")}
FAKE_KEYS = ["session:sid-a:last_activity", "session:denylist:sid-b", "throttle:lock:user:x",
             "plainkey"]


def _completed(argv, rc, stdout="", stderr=""):
    return subprocess.CompletedProcess(argv, rc, stdout, stderr)


class _StubRun:
    """樁 subprocess.run：依 argv 分流 psql（依 SQL 內容）／redis（依命令）；記錄每次 argv。"""

    def __init__(self, tables=None, seqs=None, keys=None, dbsize=None, fail=None, garble=None,
                 truncate=None):
        self.tables = FAKE_TABLES if tables is None else tables
        self.seqs = FAKE_SEQS if seqs is None else seqs
        self.keys = FAKE_KEYS if keys is None else keys
        self.dbsize = len(self.keys) if dbsize is None else dbsize
        self.fail = fail            # "psql"／"redis"＝該支非零退出
        self.garble = garble        # "tables"／"seqs"＝該面回不可解輸出（缺欄／非整數）
        self.truncate = truncate    # "tables"／"seqs"＝該面值腿少回一列（輸出被截斷／撈取不完整）
        self.log = []

    def __call__(self, argv, **_kw):
        self.log.append(list(argv))
        if "psql" in argv:
            if self.fail == "psql":
                return _completed(argv, 2, "", "psql: error: connection refused")
            sql = argv[-1]
            if sql == SQL_TABLES:
                out = "\n".join(sorted(self.tables))
            elif sql == SQL_SEQUENCES:
                out = "\n".join(sorted(self.seqs))
            elif "count(*)" in sql:
                if self.garble == "tables":
                    return _completed(argv, 0, "sys_user\n", "")           # 缺列數欄
                items = sorted(self.tables.items())
                out = "\n".join(f"{n}{PSQL_SEP}{c}"
                                for n, c in (items[:-1] if self.truncate == "tables" else items))
            else:
                if self.garble == "seqs":
                    return _completed(argv, 0, f"sys_user_id_seq{PSQL_SEP}?{PSQL_SEP}t\n", "")
                items = sorted(self.seqs.items())
                out = "\n".join(f"{n}{PSQL_SEP}{v[0]}{PSQL_SEP}{v[1]}"
                                for n, v in (items[:-1] if self.truncate == "seqs" else items))
            return _completed(argv, 0, out + "\n", "")
        if self.fail == "redis":
            return _completed(argv, 1, "", "NOAUTH Authentication required.")
        cmd = argv[-1]
        if cmd.endswith(" DBSIZE"):
            return _completed(argv, 0, f"{self.dbsize}\n", "")
        return _completed(argv, 0, "".join(k + "\n" for k in self.keys), "")


def _snap(**over):
    """合成基準 dict（可覆寫任一面）。"""
    base = {"schema_version": SCHEMA_VERSION, "taken_at": "2026-08-30T00:00:00Z",
            "tables": {"sys_user": 3, "sys_token": 0},
            "sequences": {"sys_user_id_seq": {"last_value": 3, "is_called": True}},
            "redis": {"dbsize": 2, "prefixes": {"session": 2}}}
    base.update(over)
    return base


class TestDiffPure(unittest.TestCase):
    """diff 純函式六形：全等／列數差／表多／表少／序列差／redis 前綴差（＋taken_at 忽略）。"""

    def test_equal_snapshots_yield_no_rows_and_ignore_taken_at(self):
        a, b = _snap(), _snap(taken_at="2026-08-30T23:59:59Z")
        self.assertEqual(diff_snapshots(a, b), [])

    def test_row_count_drift(self):
        rows = diff_snapshots(_snap(), _snap(tables={"sys_user": 3, "sys_token": 2}))
        self.assertEqual(rows, [{"face": "表", "name": "sys_token", "base": 0, "live": 2,
                                 "delta": 2}])

    def test_extra_table_in_live(self):
        rows = diff_snapshots(_snap(), _snap(tables={"sys_user": 3, "sys_token": 0, "tmp_x": 1}))
        self.assertEqual([(r["name"], r["base"], r["live"], r["delta"]) for r in rows],
                         [("tmp_x", "（無）", 1, "—")])

    def test_missing_table_in_live(self):
        rows = diff_snapshots(_snap(), _snap(tables={"sys_user": 3}))
        self.assertEqual([(r["face"], r["name"], r["base"], r["live"]) for r in rows],
                         [("表", "sys_token", 0, "（無）")])

    def test_sequence_drift_last_value_and_is_called(self):
        live = _snap(sequences={"sys_user_id_seq": {"last_value": 4, "is_called": True}})
        rows = diff_snapshots(_snap(), live)
        self.assertEqual(rows, [{"face": "序列", "name": "sys_user_id_seq",
                                 "base": "last_value=3,is_called=t",
                                 "live": "last_value=4,is_called=t", "delta": 1}])
        live = _snap(sequences={"sys_user_id_seq": {"last_value": 3, "is_called": False}})
        self.assertEqual(len(diff_snapshots(_snap(), live)), 1)   # 只差 is_called 也算差

    def test_redis_prefix_and_dbsize_drift(self):
        live = _snap(redis={"dbsize": 3, "prefixes": {"session": 2, "cpwd": 1}})
        rows = diff_snapshots(_snap(), live)
        self.assertEqual([(r["face"], r["name"], r["base"], r["live"], r["delta"]) for r in rows],
                         [("redis", "DBSIZE", 2, 3, 1), ("redis", "cpwd", 0, 1, 1)])

    def test_render_lists_only_diffs_with_summary_line(self):
        live = _snap(tables={"sys_user": 4, "sys_token": 0},
                     redis={"dbsize": 3, "prefixes": {"session": 3}})
        lines = render_diff(diff_snapshots(_snap(), live), live)
        self.assertIn("  表｜sys_user｜3｜4｜1", lines)
        self.assertNotIn("sys_token", "\n".join(lines))
        self.assertTrue(lines[-1].startswith("[walkthrough-baseline] 摘要：表 1 項差／序列 0 項差／"
                                              "redis 2 項差"), msg=lines[-1])
        self.assertIn("✓ 全等（表 2／序列 1／redis 2 鍵、1 前綴）", render_diff([], _snap())[0])


class TestPrefixGrouping(unittest.TestCase):
    def test_prefix_is_segment_before_first_colon_and_colonless_goes_to_no_prefix(self):
        got = group_prefixes(["session:a:b", "session:c", "throttle:lock:user:x", "plain",
                              "", "  ", "cpwd:7"])
        self.assertEqual(got, {"session": 2, "throttle": 1, "cpwd": 1, NO_PREFIX: 1})
        self.assertEqual(group_prefixes([]), {})

    def test_scan_duplicates_are_deduped_before_counting(self):
        """★SCAN 契約只保證「至少一次」（rehash 期間重複回傳同一把鍵）——逐行累加會把一把
        算成多把；走查前後兩次取樣重複度不同時，diff 即報出實際不存在的殘鍵＝假紅，
        而 §9c 步驟 4 的操作者會照著去找一把不存在的殘鍵。"""
        stub = _StubRun(keys=["session:a", "session:a", "session:b", "session:a"], dbsize=2)
        self.assertEqual(snapshot_live(run=stub)["redis"], {"dbsize": 2, "prefixes": {"session": 2}})

    def test_dbsize_is_cross_checked_against_deduped_scan_key_count(self):
        """「DBSIZE 另取以互證」須真的發生（B-147 條目原話）：不等即出提示——但**不改 rc**
        （取樣間有鍵 TTL 到期屬正常，嚴格相等會偶發不成立、rc 2 即假紅）。"""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            snap = snapshot_live(run=_StubRun(keys=["session:a", "session:b"], dbsize=5))
        self.assertIn("--scan 去重後 2 鍵、DBSIZE 5", err.getvalue())
        self.assertEqual(snap["redis"], {"dbsize": 5, "prefixes": {"session": 2}})
        quiet = io.StringIO()
        with contextlib.redirect_stderr(quiet):
            snapshot_live(run=_StubRun())                    # 相等即靜默
        self.assertEqual(quiet.getvalue(), "")


class TestSnapshotFileAndForm(unittest.TestCase):
    """JSON 往返、基準檔缺席／壞形（`{}`、非 JSON、版本不符、空表面）＝rc 2。"""

    def test_json_round_trip_diffs_empty(self):
        snap = snapshot_live(run=_StubRun(), now=datetime.datetime(2026, 8, 30, 1, 2, 3,
                                                                   tzinfo=datetime.timezone.utc))
        self.assertEqual(snap["taken_at"], "2026-08-30T01:02:03Z")
        self.assertEqual(snap["schema_version"], SCHEMA_VERSION)
        self.assertEqual(snap["tables"], FAKE_TABLES)
        self.assertEqual(snap["sequences"]["sys_token_id_seq"], {"last_value": 1, "is_called": False})
        self.assertEqual(snap["redis"], {"dbsize": 4, "prefixes": {"session": 2, "throttle": 1,
                                                                    NO_PREFIX: 1}})
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "b.json")
            dump_snapshot(snap, path)
            self.assertEqual(diff_snapshots(load_snapshot(path), snap), [])

    def test_missing_and_malformed_baseline_are_env_errors(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(BaselineError):
                load_snapshot(os.path.join(d, "nope.json"))
            for body in ("{}", "not json", "[]", json.dumps(_snap(schema_version=99)),
                         json.dumps(_snap(tables={})), json.dumps(_snap(sequences={})),
                         json.dumps(_snap(tables={"t": "3"})),
                         json.dumps(_snap(redis={"dbsize": 0})),
                         json.dumps(_snap(redis={"dbsize": "5", "prefixes": {}})),
                         json.dumps(_snap(redis={"dbsize": 0, "prefixes": {"session": "2"}})),
                         json.dumps(_snap(sequences={"s": {"last_value": "3",
                                                           "is_called": True}})),
                         json.dumps(_snap(sequences={"s": {"last_value": 3,
                                                           "is_called": "t"}}))):
                path = os.path.join(d, "bad.json")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(body)
                with self.assertRaises(BaselineError, msg=body):
                    load_snapshot(path)

    def test_incomplete_fetch_is_env_error_not_a_silently_short_baseline(self):
        """★撈取完整性守門（清單 N 個、值腿只回 N-1 列＝psql 輸出被截斷）：不 fail-loud 的話，
        少掉的那張表／那條序列會靜默不進基準檔，走查後 diff 對它恆「全等」＝假綠——與「比對面
        為空」同一家族（空面是全部漏、截斷是部分漏）。兩面各自釘訊息，只拆掉一道也照樣紅。"""
        for face, word in (("tables", "表列數撈取不完整"), ("seqs", "序列撈取不完整")):
            with self.assertRaises(BaselineError, msg=face) as ctx:
                snapshot_live(run=_StubRun(truncate=face))
            self.assertIn(word, str(ctx.exception))

    def test_empty_comparison_face_is_env_error_not_green(self):
        """★零表或零序列＝rc 2（空面的全綠是假綠）——snapshot 與 diff 兩路皆然。"""
        with self.assertRaises(BaselineError):
            snapshot_live(run=_StubRun(tables={}))
        with self.assertRaises(BaselineError):
            snapshot_live(run=_StubRun(seqs={}))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "b.json")
            dump_snapshot(snapshot_live(run=_StubRun()), path)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = main([PROG, "diff", path], run=_StubRun(tables={}))
            self.assertEqual(rc, RC_ENV)
            self.assertIn("比對面為空", err.getvalue())
        # 零 redis 鍵是合法狀態、不是空面
        self.assertEqual(snapshot_live(run=_StubRun(keys=[]))["redis"],
                         {"dbsize": 0, "prefixes": {}})

    def test_unparsable_psql_output_is_env_error_not_a_bare_traceback(self):
        """★psql -At 輸出不可解（缺欄 IndexError／非整數 ValueError）＝結構異常 rc 2。
        裸 traceback 會讓行程落在 **1＝契約中的「有差」**：走查收尾照 §9c 步驟 4 判 rc 的人
        會把「工具沒讀懂輸出」讀成「環境沒還原」（或反過來把 traceback 當雜訊忽略）
        ——兩種誤讀都在 L-055／L-071 的錯誤家族裡。"""
        for garble in ("tables", "seqs"):
            with self.assertRaises(BaselineError, msg=garble):
                snapshot_live(run=_StubRun(garble=garble))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "b.json")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(main([PROG, "snapshot", path], run=_StubRun(garble="tables")),
                                 RC_ENV)
            self.assertIn("不可解", err.getvalue())
            self.assertFalse(os.path.exists(path))


class TestExitCodes(unittest.TestCase):
    """退出碼四態：0 全等／1 有差／2 環境（docker 不可執行、psql／redis 失敗）／64 用法。"""

    def _baseline(self, d):
        path = os.path.join(d, "b.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main([PROG, "snapshot", path], run=_StubRun()), RC_OK)
        self.assertIn("基準已寫", out.getvalue())
        return path

    def test_equal_is_0_and_drift_is_1(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._baseline(d)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(main([PROG, "diff", path], run=_StubRun()), RC_OK)
            self.assertIn("✓ 全等", out.getvalue())
            drift = _StubRun(keys=FAKE_KEYS + ["walkthrough-baseline-selftest:probe"])
            with contextlib.redirect_stderr(err):
                self.assertEqual(main([PROG, "diff", path], run=drift), RC_DIFF)
            text = err.getvalue()
            self.assertIn("redis｜DBSIZE｜4｜5｜1", text)
            self.assertIn("redis｜walkthrough-baseline-selftest｜0｜1｜1", text)   # 前綴缺席＝0 鍵
            self.assertIn("摘要：表 0 項差／序列 0 項差／redis 2 項差", text)

    def test_env_failures_are_2_with_startup_hint(self):
        def no_docker(argv, **_kw):
            raise OSError("[Errno 2] No such file or directory: 'docker'")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "b.json")
            for run in (no_docker, _StubRun(fail="psql"), _StubRun(fail="redis")):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    self.assertEqual(main([PROG, "snapshot", path], run=run), RC_ENV)
                self.assertIn(STARTUP_HINT, err.getvalue())
                self.assertFalse(os.path.exists(path))   # 環境異常不得留下半成品基準檔
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(main([PROG, "diff", path], run=_StubRun()), RC_ENV)
            self.assertIn("基準檔缺席", err.getvalue())

    def test_exit_code_numerals_are_the_published_contract(self):
        """★本類其餘各案一律拿常數與自己比（assertEqual(main(...), RC_*)），只驗分流路徑、
        不驗契約數值——RC_ENV 由 2 改 3、RC_USAGE 由 64 改 2 皆全綠，而 RUNBOOK §12 退出碼段
        仍逐碼寫 2／64＝手冊與工具各說各話。退出碼是本工具唯一的對外契約（§9c 步驟 4
        「rc 0 為準」），故照 rust-fmt-gate 慣例釘字面。"""
        self.assertEqual((RC_OK, RC_DIFF, RC_ENV, RC_USAGE), (0, 1, 2, 64))

    def test_usage_is_64_on_stderr(self):
        for argv in ([PROG], [PROG, "nope"], [PROG, "snapshot"], [PROG, "diff", "--user", "x"],
                     [PROG, "diff", "f.json", "--bogus"], [PROG, "diff", "f.json", "--user"]):
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv, run=_StubRun()), RC_USAGE, msg=str(argv))
            self.assertIn("用法：", err.getvalue(), msg=str(argv))


class TestCommandForms(unittest.TestCase):
    """psql／redis 命令構造與唯讀紀律逐字釘死；密碼不出現在 host argv。"""

    def test_psql_argv_form_and_user_db_options(self):
        argv = psql_argv("SELECT 1", "u1", "d1")
        self.assertEqual(argv[:8], ["docker", "compose", "-f", "docker-compose.yml",
                                    "-f", "docker-compose.dev.yml", "exec", "-T"])
        self.assertEqual(argv[8:10], ["postgres", "psql"])
        for tok in ("-U", "u1", "-d", "d1", "-At", "-F", PSQL_SEP, "ON_ERROR_STOP=1"):
            self.assertIn(tok, argv)
        self.assertEqual(argv[-1], "SELECT 1")
        stub = _StubRun()
        with tempfile.TemporaryDirectory() as d:
            with contextlib.redirect_stdout(io.StringIO()):
                main([PROG, "snapshot", os.path.join(d, "b.json"), "--user", "u9", "--db", "d9"],
                     run=stub)
        psqls = [a for a in stub.log if "psql" in a]
        self.assertTrue(psqls and all(a[a.index("-U") + 1] == "u9" and a[a.index("-d") + 1] == "d9"
                                      for a in psqls))

    def test_every_pg_statement_is_select_and_every_redis_command_is_read(self):
        stub = _StubRun()
        snapshot_live(run=stub)
        sqls = [a[-1] for a in stub.log if "psql" in a]
        self.assertEqual(len(sqls), 4)                   # 表清單／表列數／序列清單／序列值
        self.assertTrue(all(s.startswith("SELECT ") for s in sqls), msg=sqls)
        self.assertFalse(any(w in s.upper() for s in sqls
                             for w in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "SETVAL", "ALTER")))
        redis_cmds = [a[-1] for a in stub.log if "sh" in a]
        self.assertEqual(len(redis_cmds), 2)
        self.assertTrue(all(c.endswith(" DBSIZE") or c.endswith(" --scan") for c in redis_cmds),
                        msg=redis_cmds)
        # 表名照規矩雙引號、名欄單引號（UNION ALL 一次撈）
        self.assertIn('SELECT \'sys_user\', count(*) FROM "sys_user"', sqls[1])
        self.assertIn(" UNION ALL ", sqls[1])
        self.assertIn('SELECT \'sys_user_id_seq\', last_value, is_called FROM "sys_user_id_seq"',
                      sqls[3])

    def test_catalog_sql_and_count_legs_are_pinned_against_narrowing(self):
        """★「零手抄名冊」不變式的唯一機器載體（同 schema-gate 三 SQL 常數位元釘死之形）：
        樁 _StubRun 以**常數同一性**分流（`sql == SQL_TABLES`）、回傳的假資料與 SQL 文字無關，
        故目錄 SQL 被窄化時其餘各案照樣全綠——本工具存在的理由（清單式防法已被 L-071 證偽）
        可被靜默拆掉。四種實測窄化：①排除 seaql_migrations（檔頭明文承諾不豁免）
        ②改掃 pg_catalog ③序列面 LIKE 'sys_token%'（退化成手抄四表）④count 腿 WHERE false
        （整個表面恆讀 0＝走查後 diff 永遠全等的假綠機器）。逐字全等＋結構不變式雙釘。"""
        self.assertEqual(SQL_TABLES,
                         "SELECT table_name FROM information_schema.tables "
                         "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1")
        self.assertEqual(SQL_SEQUENCES,
                         "SELECT c.relname FROM pg_class c "
                         "JOIN pg_namespace n ON n.oid=c.relnamespace "
                         "WHERE c.relkind='S' AND n.nspname='public' ORDER BY 1")
        for sql in (SQL_TABLES, SQL_SEQUENCES):
            # 結構不變式（連同期望字面一起被改寫時仍成立）：只准一個 AND、不得有名冊式篩選
            self.assertEqual(sql.upper().count(" AND "), 1, msg=sql)
            for banned in (" LIKE ", "<>", "!=", " NOT IN ", " IN ("):
                self.assertNotIn(banned, sql.upper(), msg=sql)
        stub = _StubRun()
        snapshot_live(run=stub)
        sqls = [a[-1] for a in stub.log if "psql" in a]
        self.assertEqual(sqls[0], SQL_TABLES)
        self.assertEqual(sqls[2], SQL_SEQUENCES)
        # count／序列腿：**全等**比對（非 assertIn）＋腿數＝清單長度、且不得帶 WHERE
        self.assertEqual(sqls[1], " UNION ALL ".join(
            f'SELECT \'{n}\', count(*) FROM "{n}"' for n in sorted(FAKE_TABLES)))
        self.assertEqual(sqls[3], " UNION ALL ".join(
            f'SELECT \'{n}\', last_value, is_called FROM "{n}"' for n in sorted(FAKE_SEQS)))
        for leg_sql, names in ((sqls[1], FAKE_TABLES), (sqls[3], FAKE_SEQS)):
            self.assertEqual(leg_sql.count(" UNION ALL "), len(names) - 1, msg=leg_sql)
            self.assertNotIn("WHERE", leg_sql.upper(), msg=leg_sql)

    def test_redis_argv_takes_password_inside_container_shell_only(self):
        argv = redis_argv("DBSIZE")
        self.assertEqual(argv[:8], COMPOSE_EXEC)
        self.assertEqual(argv[8:11], ["redis", "sh", "-c"])
        script = argv[-1]
        self.assertIn(f'-a "$(cat {REDIS_PASSWORD_FILE})"', script)
        self.assertIn("--no-auth-warning", script)
        self.assertTrue(script.endswith(" DBSIZE"))
        # host argv 只出現「$(cat …)」字面：除 sh -c 的 script 外沒有任何元素提到密碼檔，
        # 且 script 內密碼檔只以命令替換形出現（沒有任何已展開的值可洩）。
        self.assertEqual([a for a in argv if "redis_password" in a], [script])
        self.assertEqual(script.count("redis_password"), script.count("$(cat /run/secrets/redis_password)"))

    def test_every_print_flushes(self):
        """輸出紀律檔文釘死（同 rust-fmt-gate／wf-watchdog）：每個 print 皆帶 flush=True。"""
        with open(__file__, encoding="utf-8") as fh:
            src = fh.read()
        offenders = [ln for ln in src.splitlines() if "print(" in ln and "flush=True" not in ln]
        self.assertEqual(offenders, [], msg=str(offenders))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
