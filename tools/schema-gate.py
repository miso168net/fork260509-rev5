#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/schema-gate.py — 三閘 schema 驗證閘（001 基線；Day-1 受管演進帳）

子命令：
  check [--container 名] [--user U] [--db D]
        三閘全跑（gate1 結構＋gate2 欄序/seed＋audit archetype）；入口無條件先跑合成
        self-test（敗＝rc 2、不讀任何真檔）。預設對 dev stack（compose exec postgres）；
        `--container` 指向一次性 pristine 容器（fixtures 產製／演進帳往返驗證場景）。
  test  跑自帶測試（unittest、離線、零 docker）——含 SC-002 四類 negative 注入
        （結構／欄序／seed 值／sequence 落值）與登記檔壞形自測。
  doccheck  data-model.md 文件面（§2 欄五元組＋§6 索引約束）vs 凍結 fixtures 機器對賬
        （B-010；離線零 docker、不讀庫；★不入 pre-commit 常跑鏈——手動／review 輪跑）。

契約＝specs/001-schema-baseline/contracts/gates.md（行為）＋contracts/schema-evolution.md
（登記檔形＋啟動斷言七條）＋contracts/fixtures.md（凍結面）。零容差語意：一切比對＝全等，
「容差」唯一合法形＝演進帳登記（docs/ops/reference-src/schema-evolution.json）。

三閘：
  gate1 結構——左源＝specs/001-schema-baseline/fixtures/{columns,indexes,constraints}.json
        （凍結面）⊕ 演進帳合成期望；右源＝實庫照相三節（與 tools/docs-sync.py refresh
        同構三查詢、排除 seaql_migrations、確定性排序）；三節逐列全等，未登記差異＝紅
        （指名 section／table／名稱／左右值）、登記超前（登記了實庫沒有）同紅。
  gate2 欄序——左源＝data-model.md §2 逐表欄序（解析「| # | 欄 |」表體）＋演進帳
        add_column 接末位；右源＝實庫 ordinal；14 親排表逐位全等、casbin_rule 豁免。
  gate2 seed——左源＝fixtures/seed.sql ⊕ seed_* 演進合成；右源＝實庫 pg_dump --data-only；
        兩側同一 normalize（COPY 段整列排序＋setval 原位＋剝除 \\restrict／\\unrestrict
        token 行＋seaql_migrations COPY 段）後**未排序逐列 diff**（含 id 欄）；
        ★禁全檔排序後雜湊（會掩蓋 sequence 落值漂移與真差異）。sequence 名冊讀
        seed-decision.json 之 sequences 節（勿手抄名字面）。
  audit archetype——左源＝docs/ops/reference-src/archetype-map.json（15 表歸屬、形契約
        gates.md §3）；對實庫照相逐表驗四變體規則（C／D 子型硬編碼於工具、map note＝
        人讀註記）；created_by 可空性顯式驗（NN 恰四表）；表清單守門（實庫表集≠map
        表集＝紅）。

退出碼：0 全綠／1 漂移（逐項指名）／2 環境或結構異常（fixtures 缺、登記檔壞形、庫不可達、
比對面為空、self-test 敗——附補救提示）／64 用法錯誤（usage 走 stderr）。
只跑唯讀查詢與 pg_dump、絕不寫庫；pg_dump 帶 PGTZ=UTC（閘不依賴 session timezone、
data-model §4 UTC+0 拍板）；輸出不含 deploy 機密值（seed 定稿值〔含 PHC 常數〕本在
版控、gate2 seed diff 可回顯——非洩密面）。

rename map（data-model §3、4 組）僅用於「vs rev4 快照」血緣對賬場景（fixtures 產製之
一次性三驗、T012 scratchpad 腳本 import 消費）——非三閘常態比對面、check 不讀。
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXTURES_DIR = os.path.join("specs", "001-schema-baseline", "fixtures")
DATA_MODEL = os.path.join("specs", "001-schema-baseline", "data-model.md")
SEED_DECISION = os.path.join("specs", "001-schema-baseline", "seed-decision.json")
LEDGER = os.path.join("docs", "ops", "reference-src", "schema-evolution.json")
ARCHETYPE_MAP = os.path.join("docs", "ops", "reference-src", "archetype-map.json")

DB_USER = "soybean"
DB_NAME = "soybean_admin_rust"
COMPOSE_EXEC = ["docker", "compose", "-f", "docker-compose.yml",
                "-f", "docker-compose.dev.yml", "exec", "-T"]

# 三節列鍵集（與 docs-sync refresh 快照同構；fixtures 形斷言用）
COL_KEYS = frozenset({"table", "column", "ordinal", "type", "nullable", "default"})
DEF_KEYS = frozenset({"table", "name", "definition"})

# 登記檔（contracts/schema-evolution.md）：kind 枚舉恰八值；id／knife／date 格式
KINDS = ("add_table", "add_column", "alter_column", "add_index", "add_constraint",
         "seed_add", "seed_update", "seed_delete")
# 斷言⑦（B-006；contracts/schema-evolution.md §2 第 7 條）：kind×detail 必備鍵表——八 kind
# 逐 kind 定形、load_ledger 啟動即驗（原合成期 _need 臨時檢查升格為啟動斷言；_need 留作
# 直呼合成路徑的兜底）。需比對面在場的值域斷言（pk 欄名 ⊆ COPY 欄集、同名 index/
# constraint 重複登記攔）歸合成期驗、同樣 GateError→rc 2。
DETAIL_KEYS = {
    "add_table": ("columns",),
    "add_column": ("column", "type", "nullable"),
    "alter_column": ("column",),
    "add_index": ("name", "definition"),
    "add_constraint": ("name", "definition"),
    "seed_add": ("pk", "values"),
    "seed_update": ("pk", "set"),
    "seed_delete": ("pk",),
}
RE_ENTRY_ID = re.compile(r"^E-\d{3}$")
RE_KNIFE = re.compile(r"^\d{3}-[a-z0-9-]+$")
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# archetype 四變體字串（gates.md §3 label 值域；C 子型明細走 note 人讀）
LABELS = ("A 業務全六欄", "B append-only", "C join·狀態機", "D 治理")
# created_by NN 恰四表（data-model §1「*_by 欄性質判準」：domain 欄、非審計欄）；其餘一律可空
CREATED_BY_NN = ("sys_access_log", "sys_token", "sys_pwd_custody", "sys_user_email_verify")
AUDIT_SIX = ("created_at", "created_by", "updated_at", "updated_by",
             "deleted_at", "deleted_by")
# 變體 B 禁欄判準＝前綴通配（ADR 0016、gates.md §3）：updated_／deleted_ 起首即紅——
# 防變名欄（updated_time／deleted_flag 之類）繞過 append-only 保證（憲法 §I.6）。
AUDIT_B_FORBIDDEN_PREFIXES = ("updated_", "deleted_")
# 具名豁免清單（ADR 0016 正規出口；沿 CREATED_BY_NN 具名慣例）：合法 payload 欄
# （例：日後稽核表 updated_fields jsonb 記變更欄集）加列於此、Day-1 空集。
# 格式＝{(表名, 欄名): "理由"}；加列程序＝隨引入該欄之刀同 commit 加列＋附理由字串
# （誤攔勿就地退回具名判準——等於白拍 ADR 0016），review 輪隨審計欄語意演進複核。
AUDIT_B_EXEMPT = {}
ORDER_EXEMPT = ("casbin_rule",)   # 委派建表、欄序不入親排（data-model §7）

# rename map（data-model §3、4 組、全在 sys_operation_log）：僅供 vs rev4 快照血緣對賬
# 場景（fixtures 產製一次性三驗腳本 import）；rev5 自家比對一律新欄名、check 不消費。
RENAME_MAP = {
    "operator_real_ip": "real_ip",
    "operator_peer_ip": "peer_ip",
    "operator_x_forwarded_for": "x_forwarded_for",
    "operator_ip_confidence": "ip_confidence",
}

# ── 照相三查詢（與 tools/docs-sync.py refresh 同構 SQL；SELECT only）────────────
_JSON_WRAP = "SELECT COALESCE(json_agg(t), '[]'::json) FROM ({}) t"
SQL_COLUMNS = _JSON_WRAP.format(
    'SELECT c.table_name AS "table", c.column_name AS "column",'
    ' c.ordinal_position AS "ordinal", format_type(a.atttypid, a.atttypmod) AS "type",'
    " c.is_nullable = 'YES' AS \"nullable\", c.column_default AS \"default\""
    " FROM information_schema.columns c"
    " JOIN pg_class cl ON cl.relname = c.table_name"
    " JOIN pg_namespace ns ON ns.oid = cl.relnamespace AND ns.nspname = c.table_schema"
    " JOIN pg_attribute a ON a.attrelid = cl.oid AND a.attname = c.column_name"
    " WHERE c.table_schema = 'public' AND c.table_name <> 'seaql_migrations'"
    " ORDER BY c.table_name, c.ordinal_position")
SQL_INDEXES = _JSON_WRAP.format(
    'SELECT tablename AS "table", indexname AS "name", indexdef AS "definition"'
    " FROM pg_indexes WHERE schemaname = 'public' AND tablename <> 'seaql_migrations'"
    " ORDER BY tablename, indexname")
SQL_CONSTRAINTS = _JSON_WRAP.format(
    'SELECT rel.relname AS "table", con.conname AS "name",'
    ' pg_get_constraintdef(con.oid) AS "definition"'
    " FROM pg_constraint con"
    " JOIN pg_class rel ON rel.oid = con.conrelid"
    " JOIN pg_namespace ns ON ns.oid = rel.relnamespace"
    " WHERE ns.nspname = 'public' AND rel.relname <> 'seaql_migrations'"
    " ORDER BY rel.relname, con.conname")


class GateError(Exception):
    """環境／結構異常（fixtures 缺、登記檔壞形、庫不可達、比對面為空）——rc 2 fail-loud。"""


# ---------------------------------------------------------------------------
# DB 存取（helper 單支帶 parse 旗標；--container 指定＝docker exec、預設＝compose exec）
# ---------------------------------------------------------------------------

def _db_base(container):
    if container:
        return ["docker", "exec", "-i", container]
    return list(COMPOSE_EXEC) + ["postgres"]


def _run_docker(cmd, run):
    """docker 子行程統一入口：docker 執行不起來（OSError；不在 PATH／CLI 缺）＝
    環境異常 GateError→rc 2、非漂移——與 docs-sync psql_fetch／wire-schema
    extract_schema 同慣例。"""
    try:
        return run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    except OSError as ex:
        raise GateError(f"無法執行 docker（{ex}）——三閘需 docker 可用；dev stack 啟動："
                        "docker compose -f docker-compose.yml -f docker-compose.dev.yml "
                        "up -d --wait postgres；一次性容器場景→確認 --container 名"
                        ) from None


def psql(sql, parse=False, container=None, user=DB_USER, db=DB_NAME, run=subprocess.run):
    """docker（compose）exec psql 唯讀撈取；parse=True 時 stdout 以 JSON 解析。
    psql 失敗（含 docker 不可執行）或 JSON 壞形皆屬環境異常（GateError→rc 2）。"""
    cmd = _db_base(container) + ["psql", "-U", user, "-d", db,
                                 "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql]
    r = _run_docker(cmd, run)
    if r.returncode != 0:
        raise GateError(f"psql 失敗（rc={r.returncode}）：{r.stderr.strip()[:300]}"
                        "——補救：dev stack 未起→docker compose -f docker-compose.yml "
                        "-f docker-compose.dev.yml up -d --wait postgres；"
                        "一次性容器場景→確認 --container 名")
    out = r.stdout.strip()
    if not parse:
        return out
    try:
        return json.loads(out or "[]")
    except json.JSONDecodeError as ex:
        raise GateError(f"psql 輸出非合法 JSON：{ex}；前 200 字＝{out[:200]}")


def pg_dump_data(container=None, user=DB_USER, db=DB_NAME, run=subprocess.run):
    """實庫 pg_dump --data-only（右源原文）；PGTZ=UTC＝閘不依賴 session timezone。"""
    base = _db_base(container)
    # -e 必掛 exec 子命令之後（兩形皆然）；插 docker compose 頂層＝unknown shorthand flag
    i = base.index("exec") + 1
    cmd = base[:i] + ["-e", "PGTZ=UTC"] + base[i:] + \
        ["pg_dump", "-U", user, "-d", db, "--data-only"]
    r = _run_docker(cmd, run)
    if r.returncode != 0:
        raise GateError(f"pg_dump 失敗（rc={r.returncode}）：{r.stderr.strip()[:300]}")
    return r.stdout


# ---------------------------------------------------------------------------
# 左源載入（啟動斷言全部 fail-loud；「列缺欄」類壞形前置斷言、勿裸 KeyError）
# ---------------------------------------------------------------------------

def _load_json(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise GateError(f"{what} 缺席（{path}）") from None
    except json.JSONDecodeError as ex:
        raise GateError(f"{what} JSON 壞形：{ex}") from None


def _assert_detail(e):
    """斷言⑦：kind×detail 必備鍵（表＝DETAIL_KEYS）＋逐 kind 值形檢——任一敗＝GateError
    （呼叫端轉 rc 2）；contracts/schema-evolution.md §2 第 7 條。"""
    kind, d, eid = e["kind"], e["detail"], e["id"]
    for k in DETAIL_KEYS[kind]:
        if k not in d:
            raise GateError(f"登記檔啟動斷言⑦敗：{eid}（{kind}）detail 缺必備鍵 {k}"
                            f"（必備鍵表＝{'＋'.join(DETAIL_KEYS[kind])}）")

    def _nonempty_str(key):
        if not isinstance(d[key], str) or not d[key]:
            raise GateError(f"登記檔啟動斷言⑦敗：{eid}（{kind}）detail.{key} 須為非空字串"
                            f"（得 {d[key]!r}）")

    if kind == "add_table":
        cols = d["columns"]
        if not isinstance(cols, list) or not cols:
            raise GateError(f"登記檔啟動斷言⑦敗：{eid} add_table columns 須為全欄非空清單")
        for i, c in enumerate(cols):
            if not isinstance(c, dict) or any(k not in c for k in
                                              ("column", "type", "nullable")):
                raise GateError(f"登記檔啟動斷言⑦敗：{eid} add_table columns[{i}] 須為含"
                                " column＋type＋nullable 之物件")
    elif kind == "add_column":
        _nonempty_str("column")
        _nonempty_str("type")
        if not isinstance(d["nullable"], bool):
            raise GateError(f"登記檔啟動斷言⑦敗：{eid} add_column nullable 須為布林"
                            f"（得 {d['nullable']!r}）")
    elif kind == "alter_column":
        _nonempty_str("column")
        if not any(k in d for k in ("type", "nullable", "default")):
            raise GateError(f"登記檔啟動斷言⑦敗：{eid} alter_column 須帶 type／nullable"
                            "／default 至少一項（零改動項＝空登記、必屬筆誤）")
    elif kind in ("add_index", "add_constraint"):
        _nonempty_str("name")
        _nonempty_str("definition")
    elif kind == "seed_add":
        if not isinstance(d["pk"], list) or not d["pk"] \
                or any(not isinstance(x, str) or not x for x in d["pk"]):
            raise GateError(f"登記檔啟動斷言⑦敗：{eid} seed_add pk 須為主鍵欄名非空清單")
        if not isinstance(d["values"], dict) or not d["values"]:
            raise GateError(f"登記檔啟動斷言⑦敗：{eid} seed_add values 須為物件"
                            "（欄:值 全欄）")
    else:   # seed_update／seed_delete
        if not isinstance(d["pk"], dict) or not d["pk"]:
            raise GateError(f"登記檔啟動斷言⑦敗：{eid}（{kind}）pk 須為非空物件（欄:值）")
        if kind == "seed_update" and (not isinstance(d["set"], dict) or not d["set"]):
            raise GateError(f"登記檔啟動斷言⑦敗：{eid} seed_update set 須為非空物件"
                            "（欄:值）")


def load_ledger(root):
    """演進登記檔＋啟動斷言七條（contracts/schema-evolution.md §2）；任一敗＝GateError。"""
    path = os.path.join(root, LEDGER)
    data = _load_json(path, "演進登記檔 schema-evolution.json")
    # ① 頂層鍵恰集＋型別
    if not isinstance(data, dict) or set(data) != {"next_id", "entries"}:
        raise GateError("登記檔啟動斷言①敗：頂層鍵須恰為 {next_id, entries}"
                        f"（得 {sorted(data) if isinstance(data, dict) else type(data).__name__}）")
    if not isinstance(data["next_id"], int) or isinstance(data["next_id"], bool) \
            or data["next_id"] < 1:
        raise GateError(f"登記檔啟動斷言①敗：next_id 須正整數（得 {data['next_id']!r}）")
    if not isinstance(data["entries"], list):
        raise GateError("登記檔啟動斷言①敗：entries 須為 list")
    nums = []
    for i, e in enumerate(data["entries"]):
        tag = f"entries[{i}]"
        if not isinstance(e, dict):
            raise GateError(f"登記檔啟動斷言②敗：{tag} 非物件")
        # ② 欄位齊全非空
        for k in ("id", "knife", "kind", "table", "detail", "date"):
            if k not in e or e[k] in (None, "", [], {}):
                raise GateError(f"登記檔啟動斷言②敗：{tag} 欄位 {k} 缺席或空"
                                f"（id={e.get('id', '?')}）")
        # ③ id 格式；⑤ kind 枚舉＋date 格式；④ knife 格式；⑥ drop_* 不存在
        if not isinstance(e["id"], str) or not RE_ENTRY_ID.match(e["id"]):
            raise GateError(f"登記檔啟動斷言③敗：{tag} id 格式非 E-NNN（得 {e['id']!r}）")
        if not isinstance(e["knife"], str) or not RE_KNIFE.match(e["knife"]):
            raise GateError(f"登記檔啟動斷言④敗：{e['id']} knife（來源刀編號）格式非 "
                            f"NNN-slug（得 {e['knife']!r}）")
        if isinstance(e["kind"], str) and e["kind"].startswith("drop_"):
            raise GateError(f"登記檔啟動斷言⑥敗：{e['id']} kind={e['kind']}——刪除性演進"
                            "屬拍板級、走新 ADR＋基線翻案，不入登記檔")
        if e["kind"] not in KINDS:
            raise GateError(f"登記檔啟動斷言⑤敗：{e['id']} kind={e['kind']!r} 不在枚舉"
                            f"恰八值 {KINDS}")
        if not isinstance(e["date"], str) or not RE_DATE.match(e["date"]):
            raise GateError(f"登記檔啟動斷言⑤敗：{e['id']} date 格式非 YYYY-MM-DD"
                            f"（得 {e['date']!r}）")
        if not isinstance(e["detail"], dict):
            raise GateError(f"登記檔啟動斷言②敗：{e['id']} detail 須為物件")
        # ⑦ kind×detail 必備鍵表＋值形（B-006）
        _assert_detail(e)
        nums.append(int(e["id"][2:]))
    # ③ 全檔唯一、遞增、永不回收（next_id＝最大號＋1）
    if len(set(nums)) != len(nums):
        raise GateError("登記檔啟動斷言③敗：id 重複")
    if nums != sorted(nums) or any(b <= a for a, b in zip(nums, nums[1:])):
        raise GateError(f"登記檔啟動斷言③敗：id 非遞增（序列 {nums}）")
    if nums and data["next_id"] != nums[-1] + 1:
        raise GateError(f"登記檔啟動斷言③敗：next_id={data['next_id']} ≠ 最大號＋1"
                        f"（={nums[-1] + 1}）")
    return data


def _assert_rows(rows, keys, what):
    if not isinstance(rows, list) or not rows:
        raise GateError(f"{what} 非非空 list——比對面為空、不得靜默判綠")
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or set(r) != keys:
            raise GateError(f"{what} 第 {i} 列形壞：鍵集須恰為 {sorted(keys)}"
                            f"（得 {sorted(r) if isinstance(r, dict) else type(r).__name__}）")
    return rows


def load_fixtures(root):
    """凍結面四件（三 json＋seed.sql）；缺席＝GateError 附補救提示（rc 2）。"""
    remedy = ("——補救：fixtures＝凍結面（specs/001-schema-baseline/fixtures/、"
              "contracts/fixtures.md）；未產製→依 §2 產製程序（pristine 重放＋三驗後照相"
              "落檔）；已凍結卻缺檔＝repo 受損，自 git 還原、絕不重產")
    fx = {}
    for name, keys in (("columns", COL_KEYS), ("indexes", DEF_KEYS),
                       ("constraints", DEF_KEYS)):
        path = os.path.join(root, FIXTURES_DIR, f"{name}.json")
        try:
            rows = _load_json(path, f"fixtures/{name}.json")
        except GateError as ex:
            raise GateError(str(ex) + remedy) from None
        fx[name] = _assert_rows(rows, keys, f"fixtures/{name}.json")
    seed_path = os.path.join(root, FIXTURES_DIR, "seed.sql")
    try:
        with open(seed_path, encoding="utf-8") as fh:
            fx["seed"] = fh.read()
    except FileNotFoundError:
        raise GateError(f"fixtures/seed.sql 缺席（{seed_path}）{remedy}") from None
    if not fx["seed"].strip():
        raise GateError("fixtures/seed.sql 內容為空——比對面為空、不得靜默判綠" + remedy)
    return fx


def load_archetype_map(root):
    """archetype-map 載入＋形斷言（gates.md §3 形契約；缺鍵／表重複／label 值域外＝rc 2）。"""
    data = _load_json(os.path.join(root, ARCHETYPE_MAP), "archetype-map.json")
    if not isinstance(data, dict) or set(data) != {"lineage", "usage", "tables"}:
        raise GateError("archetype-map 形壞：頂層鍵須恰為 {lineage, usage, tables}")
    tables = data["tables"]
    if not isinstance(tables, list) or not tables:
        raise GateError("archetype-map 形壞：tables 非非空 list")
    seen = set()
    for i, row in enumerate(tables):
        if not isinstance(row, dict) or set(row) != {"table", "label",
                                                     "active_unique", "note"}:
            raise GateError(f"archetype-map tables[{i}] 形壞：鍵集須恰為 "
                            "{table, label, active_unique, note}")
        if not isinstance(row["table"], str) or not row["table"]:
            raise GateError(f"archetype-map tables[{i}]：table 必填非空")
        if row["table"] in seen:
            raise GateError(f"archetype-map：表 {row['table']} 重複登記")
        seen.add(row["table"])
        if row["label"] not in LABELS:
            raise GateError(f"archetype-map：{row['table']} label={row['label']!r} "
                            f"值域外（四變體字串＝{LABELS}）")
        au = row["active_unique"]
        if au is not None and (not isinstance(au, list) or not au
                               or any(not isinstance(x, str) or not x for x in au)):
            raise GateError(f"archetype-map：{row['table']} active_unique 須為索引名"
                            "非空清單或 null")
        if not isinstance(row["note"], str):
            raise GateError(f"archetype-map：{row['table']} note 須為字串（人讀註記）")
    return tables


def parse_data_model_order(text):
    """data-model §2 →「表→定稿欄名序」＝parse_data_model_five 的投影（單一解析源：
    §2 版面一變只改一處，防 gate2 欄序面與 doccheck 面各自漂移；自檢同在該支）。"""
    return {t: [r[1] for r in rows]
            for t, rows in parse_data_model_five(text).items()}


def load_data_model_order(root):
    path = os.path.join(root, DATA_MODEL)
    try:
        with open(path, encoding="utf-8") as fh:
            return parse_data_model_order(fh.read())
    except FileNotFoundError:
        raise GateError(f"data-model.md 缺席（{path}）") from None


def load_sequence_roster(root):
    """sequence 名冊＝seed-decision.json 之 sequences 節（唯一源、勿手抄名字面）。"""
    data = _load_json(os.path.join(root, SEED_DECISION), "seed-decision.json")
    seqs = data.get("sequences") if isinstance(data, dict) else None
    if not isinstance(seqs, list) or not seqs:
        raise GateError("seed-decision.json sequences 節空或缺——sequence 名冊無源")
    names = []
    for i, s in enumerate(seqs):
        if not isinstance(s, dict) or not isinstance(s.get("name"), str) or not s["name"]:
            raise GateError(f"seed-decision.json sequences[{i}] 形壞（缺 name）")
        names.append(s["name"])
    if len(set(names)) != len(names):
        raise GateError("seed-decision.json sequences 名冊重複")
    return sorted(names)


# ---------------------------------------------------------------------------
# doccheck（B-010）：data-model 文件面 vs 凍結 fixtures 機器對賬（離線、零 docker）
# ---------------------------------------------------------------------------

RE_DM6_HEAD = re.compile(r"^(索引|約束)（(\d+)）：")
# ★條目正則不錨行尾：§6 條目行可帶尾註（實例＝sys_operation_log_real_ip_not_null 行帶
# 「（★§4 定稿差異新增、rev4 無）」）——嚴格行尾錨會少數一條（B-010 已實證陷阱②）。
RE_DM6_ITEM = re.compile(r"^- `([^`]+)`：`([^`]+)`")


def parse_data_model_five(text):
    """data-model §2 →「表→[(ordinal, column, type, nullable, default)…]」；§2 唯一
    解析源（gate2 欄序面＝parse_data_model_order 投影本支；本支五元組、doccheck 消費）；
    宣告欄數 vs 解析列數逐表自檢（防靜默漏列）。
    ★default 欄「——」＝無 default（None）——取字面比對即全表假紅（B-010 已實證陷阱①）。"""
    m = re.search(r"^## 2\. .*?$(.*?)^## 3\. ", text, re.M | re.S)
    if not m:
        raise GateError("data-model §2 段落定位失敗（## 2. … ## 3. 邊界不在）")
    tables, declared, cur = {}, {}, None
    for line in m.group(1).splitlines():
        h = re.match(r"^### (\w+)（(\d+) 欄", line)
        if h:
            cur = h.group(1)
            declared[cur] = int(h.group(2))
            tables[cur] = []
            continue
        if cur and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 5 and cells[0].isdigit():
                tables[cur].append((int(cells[0]), cells[1], cells[2],
                                    cells[3] != "NN",
                                    None if cells[4] in ("——", "") else cells[4]))
    for t, n in declared.items():
        if len(tables[t]) != n:
            raise GateError(f"data-model §2 解析自檢敗：{t} 宣告 {n} 欄、解析得 "
                            f"{len(tables[t])}")
    if len(tables) != 14:
        raise GateError(f"data-model §2 解析自檢敗：期望 14 親排表、解析得 {len(tables)}")
    return tables


def parse_data_model_defs(text):
    """data-model §6 →（索引 {(表,名):定義}, 約束 {(表,名):定義}）；宣告支數 vs 解析數
    逐表逐節自檢＋總計行自檢（防尾註陷阱之外的任何靜默漏列）。"""
    m = re.search(r"^## 6\. .*?$(.*?)^## 7\. ", text, re.M | re.S)
    if not m:
        raise GateError("data-model §6 段落定位失敗（## 6. … ## 7. 邊界不在）")
    body = m.group(1)
    tm = re.search(r"總計：索引 (\d+) 支、約束 (\d+) 條", body)
    if not tm:
        raise GateError("data-model §6 總計行（索引 N 支、約束 N 條）定位失敗")
    idx, con = {}, {}
    cur, mode, want, seen = None, None, 0, 0

    def _selfcheck():
        if mode is not None and seen != want:
            raise GateError(f"data-model §6 解析自檢敗：{cur} {mode}宣告 {want} 條、"
                            f"解析得 {seen}")

    for ln in body.splitlines():
        h = re.match(r"^### (\w+)\s*$", ln)
        if h:
            _selfcheck()
            cur, mode, want, seen = h.group(1), None, 0, 0
            continue
        hm = RE_DM6_HEAD.match(ln)
        if hm:
            _selfcheck()
            mode, want, seen = hm.group(1), int(hm.group(2)), 0
            continue
        im = RE_DM6_ITEM.match(ln)
        if im:
            if not cur or not mode:
                raise GateError(f"data-model §6 條目行落在表／節之外：{ln[:60]}")
            store = idx if mode == "索引" else con
            key = (cur, im.group(1))
            if key in store:
                raise GateError(f"data-model §6 重複條目：{key}")
            store[key] = im.group(2)
            seen += 1
    _selfcheck()
    if (len(idx), len(con)) != (int(tm.group(1)), int(tm.group(2))):
        raise GateError(f"data-model §6 解析自檢敗：總計宣告索引 {tm.group(1)}／約束 "
                        f"{tm.group(2)}、解析得 {len(idx)}／{len(con)}")
    return idx, con


def doccheck_findings(five, idx_doc, con_doc, fixtures):
    """B-010 對賬核心（純函數）：§2 五元組 vs fixtures/columns（ORDER_EXEMPT 表依
    data-model §7 不在 §2、自 fixtures 面排除——勿誤報）；§6 vs fixtures/{indexes,
    constraints}（全表、含 casbin_rule）。文件單邊被改＝紅、逐項指名。"""
    fnd = []
    fx_five = {}
    for r in fixtures["columns"]:
        if r["table"] in ORDER_EXEMPT:
            continue
        fx_five.setdefault(r["table"], {})[r["column"]] = (
            r["ordinal"], r["type"], r["nullable"], r["default"])
    doc_five = {t: {r[1]: (r[0], r[2], r[3], r[4]) for r in rows}
                for t, rows in five.items()}
    for t in sorted(set(doc_five) - set(fx_five)):
        fnd.append(f"[doccheck·§2] {t}｜文件有、fixtures 無")
    for t in sorted(set(fx_five) - set(doc_five)):
        fnd.append(f"[doccheck·§2] {t}｜fixtures 有、文件無")
    for t in sorted(set(doc_five) & set(fx_five)):
        am, bm = doc_five[t], fx_five[t]
        for c in sorted(set(am) - set(bm)):
            fnd.append(f"[doccheck·§2] {t}.{c}｜文件有、fixtures 無")
        for c in sorted(set(bm) - set(am)):
            fnd.append(f"[doccheck·§2] {t}.{c}｜fixtures 有、文件無")
        for c in sorted(set(am) & set(bm)):
            if am[c] != bm[c]:
                fnd.append(f"[doccheck·§2] {t}.{c}｜(ordinal,type,nullable,default) "
                           f"文件={am[c]}、fixtures={bm[c]}")
    for what, doc in (("indexes", idx_doc), ("constraints", con_doc)):
        fx = {(r["table"], r["name"]): r["definition"] for r in fixtures[what]}
        for k in sorted(set(doc) - set(fx)):
            fnd.append(f"[doccheck·§6] {what}/{k[0]}/{k[1]}｜文件有、fixtures 無")
        for k in sorted(set(fx) - set(doc)):
            fnd.append(f"[doccheck·§6] {what}/{k[0]}/{k[1]}｜fixtures 有、文件無")
        for k in sorted(set(doc) & set(fx)):
            if doc[k] != fx[k]:
                fnd.append(f"[doccheck·§6] {what}/{k[0]}/{k[1]}｜定義異：文件="
                           f"{doc[k]!r}、fixtures={fx[k]!r}")
    return fnd


# ---------------------------------------------------------------------------
# gate1：凍結 ⊕ 演進帳合成 → 三節逐列全等
# ---------------------------------------------------------------------------

def _need(detail, keys, eid):
    for k in keys:
        if k not in detail:
            raise GateError(f"演進帳 {eid} detail 缺鍵 {k}——不足以機器合成期望值")


def synth_expected(fixtures, entries):
    """凍結三節 ⊕ 結構性 entries（seed_* 歸 gate2 seed 面）→ 期望三節（確定性排序）。"""
    cols = [dict(r) for r in fixtures["columns"]]
    idxs = [dict(r) for r in fixtures["indexes"]]
    cons = [dict(r) for r in fixtures["constraints"]]
    for e in entries:
        kind, t, d, eid = e["kind"], e["table"], e["detail"], e["id"]
        if kind == "add_table":
            _need(d, ("columns",), eid)
            if not isinstance(d["columns"], list) or not d["columns"]:
                raise GateError(f"演進帳 {eid} add_table columns 須為全欄非空清單")
            if any(c["table"] == t for c in cols):
                raise GateError(f"演進帳 {eid} add_table：表 {t} 已存在於期望面")
            for i, c in enumerate(d["columns"], 1):
                if not isinstance(c, dict):
                    raise GateError(f"演進帳 {eid} add_table columns[{i - 1}] 非物件")
                _need(c, ("column", "type", "nullable"), eid)
                cols.append({"table": t, "column": c["column"], "ordinal": i,
                             "type": c["type"], "nullable": c["nullable"],
                             "default": c.get("default")})
        elif kind == "add_column":
            _need(d, ("column", "type", "nullable"), eid)
            if d.get("position", "末位") != "末位":
                raise GateError(f"演進帳 {eid} add_column position={d['position']!r} "
                                "未支援——契約＝接末位（gates.md §2）")
            existing = [c for c in cols if c["table"] == t]
            if not existing:
                raise GateError(f"演進帳 {eid} add_column：表 {t} 不在期望面")
            cols.append({"table": t, "column": d["column"],
                         "ordinal": max(c["ordinal"] for c in existing) + 1,
                         "type": d["type"], "nullable": d["nullable"],
                         "default": d.get("default")})
        elif kind == "alter_column":
            _need(d, ("column",), eid)
            hit = [c for c in cols if c["table"] == t and c["column"] == d["column"]]
            if len(hit) != 1:
                raise GateError(f"演進帳 {eid} alter_column：{t}.{d['column']} 在期望面"
                                f"命中 {len(hit)} 筆（須恰 1）")
            for k in ("type", "nullable", "default"):
                if k in d:
                    hit[0][k] = d[k]
        elif kind == "add_index":
            _need(d, ("name", "definition"), eid)
            if any(r["table"] == t and r["name"] == d["name"] for r in idxs):
                raise GateError(f"演進帳 {eid} add_index：{t}/{d['name']} 同名 index 重複"
                                "登記——比對面 (table,name) 鍵合併會吞漂移、不得靜默")
            idxs.append({"table": t, "name": d["name"], "definition": d["definition"]})
        elif kind == "add_constraint":
            _need(d, ("name", "definition"), eid)
            if any(r["table"] == t and r["name"] == d["name"] for r in cons):
                raise GateError(f"演進帳 {eid} add_constraint：{t}/{d['name']} 同名 "
                                "constraint 重複登記——比對面鍵合併會吞漂移、不得靜默")
            cons.append({"table": t, "name": d["name"], "definition": d["definition"]})
        # seed_add／seed_update／seed_delete：gate2 seed 面合成（apply_seed_entries）
    return {
        "columns": sorted(cols, key=lambda r: (r["table"], r["ordinal"])),
        "indexes": sorted(idxs, key=lambda r: (r["table"], r["name"])),
        "constraints": sorted(cons, key=lambda r: (r["table"], r["name"])),
    }


def compare_structure(expected, actual):
    """三節逐列全等；未登記差異／登記超前逐項指名（section＋table＋名稱＋左右值）。"""
    findings = []
    exp_c = {(c["table"], c["column"]):
             (c["ordinal"], c["type"], c["nullable"], c["default"])
             for c in expected["columns"]}
    act_c = {(c["table"], c["column"]):
             (c["ordinal"], c["type"], c["nullable"], c["default"])
             for c in actual["columns"]}
    for k in sorted(set(exp_c) - set(act_c)):
        findings.append(f"[gate1] columns/{k[0]}/{k[1]}｜期望有、實庫無"
                        f"（左={exp_c[k]}、右=∅）——登記超前也是漂移")
    for k in sorted(set(act_c) - set(exp_c)):
        findings.append(f"[gate1] columns/{k[0]}/{k[1]}｜實庫有、期望無"
                        f"（左=∅、右={act_c[k]}）——未登記漂移（合法化唯一路徑＝"
                        "schema-evolution.json 登記）")
    for k in sorted(set(exp_c) & set(act_c)):
        if exp_c[k] != act_c[k]:
            findings.append(f"[gate1] columns/{k[0]}/{k[1]}｜(ordinal,type,nullable,"
                            f"default) 左（期望）={exp_c[k]}、右（實庫）={act_c[k]}")
    for section in ("indexes", "constraints"):
        exp = {(r["table"], r["name"]): r["definition"] for r in expected[section]}
        act = {(r["table"], r["name"]): r["definition"] for r in actual[section]}
        for k in sorted(set(exp) - set(act)):
            findings.append(f"[gate1] {section}/{k[0]}/{k[1]}｜期望有、實庫無"
                            f"（左={exp[k]!r}）")
        for k in sorted(set(act) - set(exp)):
            findings.append(f"[gate1] {section}/{k[0]}/{k[1]}｜實庫有、期望無"
                            f"（右={act[k]!r}）——未登記漂移")
        for k in sorted(set(exp) & set(act)):
            if exp[k] != act[k]:
                findings.append(f"[gate1] {section}/{k[0]}/{k[1]}｜定義異：左（期望）="
                                f"{exp[k]!r}、右（實庫）={act[k]!r}")
    return findings


# ---------------------------------------------------------------------------
# gate2 欄序：data-model §2 ＋ add_column 末位 vs 實庫 ordinal
# ---------------------------------------------------------------------------

def compare_column_order(dm_order, entries, actual_cols):
    """14 親排表逐位全等；casbin_rule 豁免；演進帳 add_column 依 id 序接末位。"""
    findings = []
    expected = {t: list(names) for t, names in dm_order.items()}
    for e in entries:
        if e["kind"] == "add_column" and e["table"] in expected:
            expected[e["table"]].append(e["detail"]["column"])
    by_table = {}
    for c in actual_cols:
        by_table.setdefault(c["table"], []).append(c)
    for t in sorted(expected):
        if t in ORDER_EXEMPT:
            continue
        if t not in by_table:
            findings.append(f"[gate2·欄序] {t}｜表不在實庫")
            continue
        act = [c["column"] for c in sorted(by_table[t], key=lambda c: c["ordinal"])]
        exp = expected[t]
        if act != exp:
            for i in range(max(len(act), len(exp))):
                a = act[i] if i < len(act) else "∅"
                x = exp[i] if i < len(exp) else "∅"
                if a != x:
                    findings.append(f"[gate2·欄序] {t} 第 {i + 1} 位｜期望={x}、實庫={a}")
    return findings


# ---------------------------------------------------------------------------
# gate2 seed：pg_dump normalize（兩側同則）＋ seed_* 合成 ＋ 未排序逐列 diff
# ---------------------------------------------------------------------------

RE_COPY_HDR = re.compile(r"^COPY public\.(\w+) \(([^)]*)\) FROM stdin;$")
# 環境相依噪音兩類（B-011；gates.md §2）
RE_DUMPED = re.compile(r"^-- Dumped (?:from database|by pg_dump) version ")
RE_OWNER = re.compile(r"^(-- .*; Owner: )(.+)$")
OWNER_PLACEHOLDER = "-"


def normalize_seed_dump(text):
    """gates.md §2 normalize 全則。剝除／正規化四類噪音，分兩族：

    **非決定性**（同環境重放即異）——①`\\restrict`／`\\unrestrict` token 行
    （pg_dump 18.4 每次 dump 隨機）②`seaql_migrations` COPY 段（框架帳表、applied_at
    逐次重放異）。
    **環境相依**（同環境穩定、換環境即異；B-011）——③`-- Dumped from database version`
    ／`-- Dumped by pg_dump version` 兩行（postgres 或 pg_dump 升版即變）④`; Owner: X`
    註解行的**值**正規化為 `-`（DB 身分變更即變；ADR 0008 那次即為此連動重產 fixtures）。

    ★③④ 只把噪音移出 **seed 逐列 diff** 的比對面，不等於放棄偵測：DB 身分變更改由
    [`compare_dump_owner`] 以一筆具名 finding 回報（守門強度不減、假紅消除）。
    ★④ 必須正規化「值」而非剝整行——`-- Data for Name: seaql_migrations; …; Owner: x`
    也帶 Owner，剝整行會連帶炸掉本函式賴以認出 seaql stanza 的那一行。

    另：COPY 段內整列排序（消物理列序假紅）；setval 原位。
    冪等：normalize(normalize(x))＝normalize(x)。
    """
    lines = text.splitlines()
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = RE_OWNER.sub(rf"\g<1>{OWNER_PLACEHOLDER}", lines[i])
        if ln.startswith("\\restrict ") or ln.startswith("\\unrestrict "):
            i += 1
            continue
        if RE_DUMPED.match(ln):
            i += 1
            continue
        if ln.startswith("-- Data for Name: seaql_migrations;"):
            if out and out[-1] == "--":
                out.pop()
            i += 1
            if i < n and lines[i] == "--":
                i += 1
            while i < n and lines[i] == "":
                i += 1
            if i < n and lines[i].startswith("COPY public.seaql_migrations "):
                while i < n and lines[i] != "\\.":
                    i += 1
                i += 1                       # 吃掉 \.
            while i < n and lines[i] == "":
                i += 1
            continue
        m = RE_COPY_HDR.match(ln)
        if m:
            out.append(ln)
            i += 1
            block = []
            while i < n and lines[i] != "\\.":
                block.append(lines[i])
                i += 1
            out.extend(sorted(block))        # 整列排序（僅段內；全檔不排序）
            if i < n:
                out.append(lines[i])         # \.
                i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out) + "\n"


def copy_literal(v):
    """python 值 → pg COPY text 格；不支援型別 fail-loud。"""
    if v is None:
        return "\\N"
    if v is True:
        return "t"
    if v is False:
        return "f"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return (v.replace("\\", "\\\\").replace("\t", "\\t")
                .replace("\n", "\\n").replace("\r", "\\r"))
    raise GateError(f"seed 合成不支援的值型別：{type(v).__name__}")


def _copy_blocks(lines):
    """normalize 後文本 → {表: (欄名序, 首列行號, 末列行號後一)}；行號指 COPY 資料列範圍。"""
    blocks = {}
    i = 0
    while i < len(lines):
        m = RE_COPY_HDR.match(lines[i])
        if m:
            cols = [c.strip().strip('"') for c in m.group(2).split(",")]
            start = i + 1
            j = start
            while j < len(lines) and lines[j] != "\\.":
                j += 1
            blocks[m.group(1)] = (cols, start, j)
            i = j
        i += 1
    return blocks


def apply_seed_entries(norm_text, entries):
    """seed 面演進合成到左源（normalize 後施作、段內重排序）。消費四類 entries：
    seed_add＝{pk:[主鍵欄…], values:{欄:值 全欄}}／seed_update＝{pk:{欄:值}, set:{欄:值}}
    ／seed_delete＝{pk:{欄:值}}；★add_column 亦動 seed 面（pg_dump COPY 段首欄清單隨
    結構走）——僅支援 nullable 無 default 形（既有列補 \\N）；其它形與 add_table 之
    seed 面合成未內建＝GateError fail-loud（該刀擴充本閘或走基線翻案；gate1 結構面照常）。"""
    seed_kinds = [e for e in entries
                  if e["kind"].startswith("seed_") or e["kind"] in ("add_column",
                                                                    "add_table")]
    if not seed_kinds:
        return norm_text
    lines = norm_text.splitlines()
    for e in seed_kinds:
        kind, t, d, eid = e["kind"], e["table"], e["detail"], e["id"]
        if kind == "add_table":
            raise GateError(f"演進帳 {eid} add_table：seed 面（pg_dump 新增 COPY 段）"
                            "合成未內建——該刀擴充 tools/schema-gate.py seed 合成或走"
                            "基線翻案（gate1 結構面已承載）")
        blocks = _copy_blocks(lines)
        if t not in blocks:
            raise GateError(f"演進帳 {eid} {kind}：seed 面無表 {t} 之 COPY 段")
        cols, start, end = blocks[t]
        rows = lines[start:end]
        if kind == "add_column":
            _need(d, ("column", "type", "nullable"), eid)
            if not (d["nullable"] is True and d.get("default") is None):
                raise GateError(f"演進帳 {eid} add_column {t}.{d['column']}：seed 面"
                                "列值合成僅支援 nullable 無 default（既有列補 \\N）——"
                                "帶 default／NOT NULL 回填形＝該刀擴充本閘或走基線翻案")
            if not re.match(r"^[a-z_][a-z0-9_]*$", d["column"]):
                raise GateError(f"演進帳 {eid} add_column：欄名 {d['column']!r} 非"
                                "樸素識別字——pg_dump 引號形無法機器合成")
            hdr = lines[start - 1]
            lines[start - 1] = hdr.replace(") FROM stdin;",
                                           f", {d['column']}) FROM stdin;")
            lines[start:end] = sorted(r + "\t\\N" for r in rows)
            continue

        def _match(row, pk_map):
            vals = row.split("\t")
            if len(vals) != len(cols):
                raise GateError(f"演進帳 {eid}：{t} COPY 列欄數 {len(vals)} ≠ 段首欄數 "
                                f"{len(cols)}（凍結面受損？）")
            return all(vals[cols.index(k)] == copy_literal(v)
                       for k, v in pk_map.items())

        # 值域斷言（B-006、斷言⑦同源；直呼合成路徑兜底）：pk/set/values 型別＋pk ⊆ COPY
        # 欄集——前世逸出裸例外（ValueError／AttributeError／TypeError）、今 GateError→rc 2。
        # ★缺鍵情形一併由本塊攔下（seed 三 kind 原 _need 呼點已被完全遮蔽、故移除）。
        if kind == "seed_add":
            if not isinstance(d.get("values"), dict):
                raise GateError(f"演進帳 {eid} seed_add：values 須為物件（欄:值 全欄）")
            if not isinstance(d.get("pk"), list) or not d["pk"]:
                raise GateError(f"演進帳 {eid} seed_add：pk 須為主鍵欄名非空清單")
            bad = sorted(set(d["pk"]) - set(cols))
            if bad:
                raise GateError(f"演進帳 {eid} seed_add：pk 欄 {bad} 不在 {t} COPY 欄集"
                                f"（欄集＝{cols}）")
        else:
            if not isinstance(d.get("pk"), dict) or not d["pk"]:
                raise GateError(f"演進帳 {eid} {kind}：pk 須為非空物件（欄:值）")
            bad = sorted(set(d["pk"]) - set(cols))
            if bad:
                raise GateError(f"演進帳 {eid} {kind}：pk 欄 {bad} 不在 {t} COPY 欄集"
                                f"（欄集＝{cols}）")
            if kind == "seed_update" and (not isinstance(d.get("set"), dict)
                                          or not d["set"]):
                raise GateError(f"演進帳 {eid} seed_update：set 須為非空物件（欄:值）")
        if kind == "seed_add":
            if set(d["values"]) != set(cols):
                raise GateError(f"演進帳 {eid} seed_add：values 欄集 ≠ {t} COPY 欄集"
                                f"（差集 {sorted(set(cols) ^ set(d['values']))}）")
            rows.append("\t".join(copy_literal(d["values"][c]) for c in cols))
        elif kind == "seed_update":
            hits = [i for i, r in enumerate(rows) if _match(r, d["pk"])]
            if len(hits) != 1:
                raise GateError(f"演進帳 {eid} seed_update：{t} pk={d['pk']} 命中 "
                                f"{len(hits)} 列（須恰 1）")
            vals = rows[hits[0]].split("\t")
            for k, v in d["set"].items():
                if k not in cols:
                    raise GateError(f"演進帳 {eid} seed_update：欄 {k} 不在 {t} COPY 段")
                vals[cols.index(k)] = copy_literal(v)
            rows[hits[0]] = "\t".join(vals)
        else:  # seed_delete
            hits = [i for i, r in enumerate(rows) if _match(r, d["pk"])]
            if len(hits) != 1:
                raise GateError(f"演進帳 {eid} seed_delete：{t} pk={d['pk']} 命中 "
                                f"{len(hits)} 列（須恰 1）")
            del rows[hits[0]]
        lines[start:end] = sorted(rows)      # 段內重排序、段外原位
    return "\n".join(lines) + "\n"


RE_SETVAL = re.compile(r"^SELECT pg_catalog\.setval\('public\.(\w+)', \d+, (?:true|false)\);$")


def assert_seed_roster(norm_frozen, roster):
    """凍結 seed.sql 之 setval 名冊必恰等 seed-decision sequences 節（兩者皆凍結面）。"""
    names = sorted(m.group(1) for m in
                   (RE_SETVAL.match(ln) for ln in norm_frozen.splitlines()) if m)
    if names != sorted(roster):
        raise GateError(f"凍結 seed.sql setval 名冊 {names} ≠ seed-decision sequences "
                        f"名冊 {sorted(roster)}——凍結面受損或名冊源壞")


def compare_dump_owner(dump_text, expected):
    """實庫 dump 的 Owner 值一致性（B-011；配 [`normalize_seed_dump`] 第 ④ 類）。

    normalize 把 `; Owner: X` 的值抹成佔位字面後，seed 逐列 diff 對「DB 身分變更」
    從此無感——而那正是 ADR 0008 那次逼 001 凍結 fixtures 重產一次的事實。本檢查把該
    偵測換成一筆具名 finding：噪音消除、守門強度不減。

    ★零 Owner 行必須紅，不得靜默判綠：pg_dump 形變或 dump 為空時比對面即空集合，
    「查空集合恆綠」是本 repo 反覆踩過的形（L-010 同族）。
    ★取原文 dump（normalize 前）為輸入——normalize 後值已被抹掉，餵進來恆綠。
    """
    owners = sorted({m.group(2) for m in
                     (RE_OWNER.match(ln) for ln in dump_text.splitlines()) if m})
    if not owners:
        return ["[gate2·owner] 實庫 dump 零 Owner 註解行——比對面為空、不得靜默判綠"
                "（pg_dump 輸出形變，或本檢查誤收 normalize 後文本）"]
    if owners != [expected]:
        return [f"[gate2·owner] 實庫 dump 的 Owner 值集合＝{owners}、期望恰 [{expected}]"
                "——DB 身分變更（ADR 0008 那次即此形）或 schema 出現多主人；確認為刻意"
                "變更後改連線身分之單一來源（--user／DB_USER），勿改本判準"]
    return []


def compare_seed(expected_text, actual_text, limit=60):
    """normalize 後未排序逐列 diff（含 id 欄）；★禁全檔排序後雜湊比對。"""
    exp, act = expected_text.splitlines(), actual_text.splitlines()
    if exp == act:
        return []
    import difflib
    diff = list(difflib.unified_diff(exp, act, lineterm="",
                                     fromfile="期望（fixtures⊕演進帳）",
                                     tofile="實庫（pg_dump normalize）"))
    body = diff[:limit] + ([f"…（共 {len(diff)} 行 diff、截斷）"]
                           if len(diff) > limit else [])
    return ["[gate2·seed] normalize 後逐列 diff 非零：\n    " + "\n    ".join(body)]


# ---------------------------------------------------------------------------
# audit archetype：15 表歸屬逐表驗（C／D 子型硬編碼；map note＝人讀）
# ---------------------------------------------------------------------------

TS_TZ = "timestamp with time zone"


def _cols_of(actual_cols):
    by = {}
    for c in actual_cols:
        by.setdefault(c["table"], {})[c["column"]] = c
    return by


def _check_col(fnd, t, tcols, name, type_=None, nn=None, default=None):
    c = tcols.get(name)
    if c is None:
        fnd.append(f"[audit] {t}｜欄 {name} 缺席")
        return
    if type_ is not None and c["type"] != type_:
        fnd.append(f"[audit] {t}.{name}｜型別={c['type']}、期望={type_}")
    if nn is not None and c["nullable"] != (not nn):
        fnd.append(f"[audit] {t}.{name}｜可空性={'可空' if c['nullable'] else 'NN'}、"
                   f"期望={'NN' if nn else '可空'}")
    if default is not None and (c["default"] or "") != default:
        fnd.append(f"[audit] {t}.{name}｜default={c['default']!r}、期望={default!r}")


def _pk_def(t, cons_by):
    for (tt, _name), definition in cons_by.items():
        if tt == t and definition.startswith("PRIMARY KEY"):
            return definition
    return None


def audit_archetype(map_rows, actual_cols, actual_idxs, actual_cons):
    """gates.md §3 驗則逐表執行（對實庫照相）；表清單守門；created_by 可空性顯式驗。
    C／D 子型規則不明的表＝GateError（不可驗＝不得靜默放行）。"""
    fnd = []
    cols_by = _cols_of(actual_cols)
    idx_by = {(r["table"], r["name"]): r["definition"] for r in actual_idxs}
    cons_by = {(r["table"], r["name"]): r["definition"] for r in actual_cons}
    map_tables = {r["table"] for r in map_rows}
    actual_tables = set(cols_by)
    for t in sorted(actual_tables - map_tables):
        fnd.append(f"[audit] 表清單守門｜實庫表 {t} 未登記 archetype 歸屬"
                   "（先補 data-model §1、再登記 archetype-map.json）")
    for t in sorted(map_tables - actual_tables):
        fnd.append(f"[audit] 表清單守門｜map 登記表 {t} 不在實庫")
    for row in sorted(map_rows, key=lambda r: r["table"]):
        t, label = row["table"], row["label"]
        if t not in cols_by:
            continue                          # 守門已計
        tc = cols_by[t]
        if label == "A 業務全六欄":
            _check_col(fnd, t, tc, "created_at", TS_TZ, nn=True, default="now()")
            _check_col(fnd, t, tc, "updated_at", TS_TZ, nn=False)
            _check_col(fnd, t, tc, "deleted_at", TS_TZ, nn=False)
            _check_col(fnd, t, tc, "created_by", "bigint")
            _check_col(fnd, t, tc, "updated_by", "bigint", nn=False)
            _check_col(fnd, t, tc, "deleted_by", "bigint", nn=False)
            for iname in (row["active_unique"] or []):
                definition = idx_by.get((t, iname))
                if definition is None:
                    fnd.append(f"[audit] {t}｜活性唯一索引 {iname} 不在實庫")
                elif "deleted_at IS NULL" not in definition:
                    fnd.append(f"[audit] {t}｜索引 {iname} 定義缺 WHERE "
                               f"(deleted_at IS NULL)：{definition!r}")
        elif label == "B append-only":
            # 前綴判準（ADR 0016）：updated_*／deleted_* 起首即紅；豁免走 AUDIT_B_EXEMPT
            for bad in sorted(tc):
                if bad.startswith(AUDIT_B_FORBIDDEN_PREFIXES) \
                        and (t, bad) not in AUDIT_B_EXEMPT:
                    fnd.append(f"[audit] {t}｜變體 B 禁欄 {bad} 在場（前綴判準 "
                               "updated_*／deleted_*、append-only 不可竄改、憲法 §I.6；"
                               "合法 payload 欄走 AUDIT_B_EXEMPT 具名豁免＋理由）")
            _check_col(fnd, t, tc, "created_at", TS_TZ, nn=True, default="now()")
            _check_col(fnd, t, tc, "created_by", "bigint")
        elif label == "C join·狀態機":
            if t == "sys_user_role":
                for bad in AUDIT_SIX:
                    if bad in tc:
                        fnd.append(f"[audit] {t}｜零審計欄 join 卻見 {bad}")
            elif t == "sys_token":
                _check_col(fnd, t, tc, "created_at", TS_TZ, nn=True)
                _check_col(fnd, t, tc, "created_by", "bigint")
                if "status" not in tc:
                    fnd.append(f"[audit] {t}｜狀態機欄 status 缺席")
            elif t == "sys_pwd_custody":
                if set(tc) != {"user_id", "created_at", "created_by"}:
                    fnd.append(f"[audit] {t}｜極簡三欄集不符：{sorted(tc)}")
                pk = _pk_def(t, cons_by)
                if pk != "PRIMARY KEY (user_id, created_by)":
                    fnd.append(f"[audit] {t}｜複合 PK 期望 (user_id, created_by)、"
                               f"實得 {pk!r}")
            elif t == "sys_user_email_verify":
                if len(tc) != 5 or "user_id" not in tc:
                    fnd.append(f"[audit] {t}｜衛星五欄形不符：{sorted(tc)}")
                pk = _pk_def(t, cons_by)
                if pk != "PRIMARY KEY (user_id)":
                    fnd.append(f"[audit] {t}｜PK 期望 (user_id)、實得 {pk!r}")
            else:
                raise GateError(f"audit：表 {t} 標 C 變體但子型規則未硬編碼——"
                                "先補 gates.md §3 驗則與本工具子型分派")
        else:  # D 治理
            if t == "casbin_rule":
                _check_col(fnd, t, tc, "protected", "boolean", nn=True, default="false")
                _check_col(fnd, t, tc, "created_at", TS_TZ, nn=True, default="now()")
                _check_col(fnd, t, tc, "created_by", "bigint")
            elif t == "sys_casbin_policy_archive":
                _check_col(fnd, t, tc, "archived_at", TS_TZ, nn=True, default="now()")
                _check_col(fnd, t, tc, "archive_reason", nn=True)
                _check_col(fnd, t, tc, "created_at", TS_TZ, nn=False)
                _check_col(fnd, t, tc, "created_by", "bigint", nn=False)
            else:
                raise GateError(f"audit：表 {t} 標 D 變體但子型規則未硬編碼——"
                                "先補 gates.md §3 驗則與本工具子型分派")
        # created_by 可空性顯式驗（不靜默；期望＝data-model §1 判準：NN 恰四表）
        if "created_by" in tc:
            want_nn = t in CREATED_BY_NN
            if tc["created_by"]["nullable"] != (not want_nn):
                fnd.append(f"[audit] {t}.created_by｜可空性顯式驗不符："
                           f"{'可空' if tc['created_by']['nullable'] else 'NN'}、期望"
                           f"={'NN' if want_nn else '可空'}（NN 恰四表＝{CREATED_BY_NN}）")
        elif t in CREATED_BY_NN:
            fnd.append(f"[audit] {t}｜created_by 欄缺席（NN 四表之一）")
    return fnd


# ---------------------------------------------------------------------------
# self-test（check 入口無條件合成；敗＝rc 2 不讀真檔——防恆綠假閘）
# ---------------------------------------------------------------------------

def _st_fixtures():
    return {
        "columns": [
            {"table": "t_log", "column": "id", "ordinal": 1, "type": "bigint",
             "nullable": False, "default": "nextval('t_log_id_seq'::regclass)"},
            {"table": "t_log", "column": "created_at", "ordinal": 2, "type": TS_TZ,
             "nullable": False, "default": "now()"},
            {"table": "t_ok", "column": "id", "ordinal": 1, "type": "bigint",
             "nullable": False, "default": None},
            {"table": "t_ok", "column": "name", "ordinal": 2,
             "type": "character varying", "nullable": False, "default": None},
        ],
        "indexes": [{"table": "t_ok", "name": "t_ok_pkey",
                     "definition": "CREATE UNIQUE INDEX t_ok_pkey ON public.t_ok"
                                   " USING btree (id)"}],
        "constraints": [{"table": "t_ok", "name": "t_ok_pkey",
                         "definition": "PRIMARY KEY (id)"}],
    }


_ST_DUMP = ("\\restrict TOKEN123\n"
            "-- Dumped from database version 18.4\n"
            "-- Dumped by pg_dump version 18.4\n"
            "--\n"
            "-- Data for Name: seaql_migrations; Type: TABLE DATA; Schema: public;"
            " Owner: soybean\n"
            "--\n"
            "\n"
            "COPY public.seaql_migrations (version, applied_at) FROM stdin;\n"
            "m001\t123\n"
            "\\.\n"
            "\n"
            "--\n"
            "-- Data for Name: t_ok; Type: TABLE DATA; Schema: public; Owner: soybean\n"
            "--\n"
            "\n"
            "COPY public.t_ok (id, name) FROM stdin;\n"
            "2\tb\n"
            "1\ta\n"
            "\\.\n"
            "\n"
            "SELECT pg_catalog.setval('public.t_ok_id_seq', 2, true);\n"
            "\n"
            "\\unrestrict TOKEN123\n")


def check_self_test():
    """健康對必綠＋注入假漂移必紅（四類：結構／欄序／seed 值／sequence 落值）＋
    normalize 冪等——任一敗＝AssertionError（呼叫端轉 rc 2、不讀真檔）。"""
    fix = _st_fixtures()
    healthy = synth_expected(fix, [])
    # gate1：健康綠
    if compare_structure(synth_expected(fix, []), healthy) != []:
        raise AssertionError("gate1 健康合成對被誤判為漂移")
    # gate1：未登記加欄必紅＋指名
    drifted = json.loads(json.dumps(healthy))
    drifted["columns"].append({"table": "t_ok", "column": "ghost", "ordinal": 3,
                               "type": "text", "nullable": True, "default": None})
    f = compare_structure(synth_expected(fix, []), drifted)
    if not any("columns/t_ok/ghost" in x for x in f):
        raise AssertionError("gate1 未登記加欄假漂移未被攔或未指名")
    # gate1：登記後同欄轉綠；登記超前（實庫沒有）必紅
    entry = {"id": "E-001", "knife": "001-schema-baseline", "kind": "add_column",
             "table": "t_ok", "detail": {"column": "ghost", "type": "text",
                                         "nullable": True, "default": None,
                                         "position": "末位"},
             "date": "2026-08-05"}
    if compare_structure(synth_expected(fix, [entry]), drifted) != []:
        raise AssertionError("gate1 演進帳合成後應綠而未綠")
    if not compare_structure(synth_expected(fix, [entry]), healthy):
        raise AssertionError("gate1 登記超前未被攔")
    # gate1：型別改動必紅
    mutated = json.loads(json.dumps(healthy))
    mutated["columns"][2]["type"] = "integer"
    if not compare_structure(synth_expected(fix, []), mutated):
        raise AssertionError("gate1 型別改動假漂移未被攔")
    # gate2 欄序：健康綠／同表兩欄互換必紅
    dm = {"t_ok": ["id", "name"]}
    if compare_column_order(dm, [], healthy["columns"]) != []:
        raise AssertionError("gate2 欄序健康對被誤判")
    swapped = json.loads(json.dumps(healthy["columns"]))
    for c in swapped:
        if c["table"] == "t_ok":
            c["ordinal"] = 3 - c["ordinal"]
    if not compare_column_order(dm, [], swapped):
        raise AssertionError("gate2 欄序互換假漂移未被攔")
    # gate2 seed：normalize（剝 token 行＋seaql 段＋段內排序）＋冪等＋健康綠
    norm = normalize_seed_dump(_ST_DUMP)
    if "\\restrict" in norm or "seaql_migrations" in norm:
        raise AssertionError("normalize 未剝除 pg_dump 框架噪音")
    # B-011 環境相依噪音兩類：③版本行剝除 ④Owner 值正規化
    if "Dumped from database version" in norm or "Dumped by pg_dump version" in norm:
        raise AssertionError("normalize 未剝除 pg_dump 版本行（環境相依噪音③）")
    if "Owner: soybean" in norm:
        raise AssertionError("normalize 未正規化 Owner 值（環境相依噪音④）")
    # ★正規化「值」而非剝整行：Owner 註解行本身須留下，否則 seaql stanza 認不出來
    if f"-- Data for Name: t_ok; Type: TABLE DATA; Schema: public; " \
       f"Owner: {OWNER_PLACEHOLDER}" not in norm:
        raise AssertionError("normalize 誤剝整行 Owner 註解——應只抹值、保留該行")
    # ★環境相依噪音改變後仍須判綠（B-011 存在的理由：升版／換身分不得紅在純噪音）
    upgraded = (_ST_DUMP.replace("version 18.4", "version 19.1")
                        .replace("Owner: soybean", "Owner: other_role"))
    if compare_seed(norm, normalize_seed_dump(upgraded)) != []:
        raise AssertionError("normalize 後 pg_dump 升版／DB 身分變更仍被判 seed 漂移")
    if norm.index("1\ta") > norm.index("2\tb"):
        raise AssertionError("normalize COPY 段內未整列排序")
    if normalize_seed_dump(norm) != norm:
        raise AssertionError("normalize 非冪等")
    if compare_seed(norm, normalize_seed_dump(_ST_DUMP)) != []:
        raise AssertionError("gate2 seed 健康對被誤判")
    # B-011 owner 一致性檢查＝噪音移出比對面後的補償守門，四格自證
    if compare_dump_owner(_ST_DUMP, DB_USER) != []:
        raise AssertionError("owner 檢查對健康 dump 誤判")
    if not compare_dump_owner(_ST_DUMP.replace("Owner: soybean", "Owner: other_role"),
                              DB_USER):
        raise AssertionError("owner 檢查未攔全庫身分變更（ADR 0008 那次即此形）")
    if not compare_dump_owner(
            _ST_DUMP.replace("Owner: soybean", "Owner: other_role", 1), DB_USER):
        raise AssertionError("owner 檢查未攔多主人 schema（值集合非單元素）")
    if not compare_dump_owner("COPY public.t_ok (id) FROM stdin;\n\\.\n", DB_USER):
        raise AssertionError("owner 檢查對零 Owner 行未紅——查空集合恆綠")
    # ★接錯輸入即恆綠：normalize 後值已成佔位，本檢查必須吃原文 dump
    if not compare_dump_owner(norm, DB_USER):
        raise AssertionError("owner 檢查誤收 normalize 後文本卻判綠——輸入須為原文 dump")
    # seed 值改一格必紅；sequence 落值 ±1 必紅
    if not compare_seed(norm, norm.replace("1\ta", "1\tX")):
        raise AssertionError("gate2 seed 值假漂移未被攔")
    if not compare_seed(norm, norm.replace("', 2, true);", "', 3, true);")):
        raise AssertionError("gate2 sequence 落值假漂移未被攔")
    # add_column 登記之 seed 面合成：COPY 段首欄清單接末位＋既有列補 \N 後轉綠
    drift_dump = (norm.replace("COPY public.t_ok (id, name) FROM stdin;",
                               "COPY public.t_ok (id, name, ghost) FROM stdin;")
                  .replace("1\ta", "1\ta\t\\N").replace("2\tb", "2\tb\t\\N"))
    if compare_seed(norm, drift_dump) == []:
        raise AssertionError("gate2 seed 未攔加欄後的 COPY 段漂移")
    if compare_seed(apply_seed_entries(norm, [entry]), drift_dump) != []:
        raise AssertionError("gate2 seed add_column 合成後應綠而未綠")
    # audit：健康 A／B 合成對綠；B 表注入 updated_at 必紅
    amap = [{"table": "t_biz", "label": "A 業務全六欄",
             "active_unique": ["t_biz_code_active_uniq"], "note": ""},
            {"table": "t_log2", "label": "B append-only",
             "active_unique": None, "note": ""}]
    acols = [
        {"table": "t_biz", "column": "id", "ordinal": 1, "type": "bigint",
         "nullable": False, "default": None},
        {"table": "t_biz", "column": "created_at", "ordinal": 2, "type": TS_TZ,
         "nullable": False, "default": "now()"},
        {"table": "t_biz", "column": "created_by", "ordinal": 3, "type": "bigint",
         "nullable": True, "default": None},
        {"table": "t_biz", "column": "updated_at", "ordinal": 4, "type": TS_TZ,
         "nullable": True, "default": None},
        {"table": "t_biz", "column": "updated_by", "ordinal": 5, "type": "bigint",
         "nullable": True, "default": None},
        {"table": "t_biz", "column": "deleted_at", "ordinal": 6, "type": TS_TZ,
         "nullable": True, "default": None},
        {"table": "t_biz", "column": "deleted_by", "ordinal": 7, "type": "bigint",
         "nullable": True, "default": None},
        {"table": "t_log2", "column": "id", "ordinal": 1, "type": "bigint",
         "nullable": False, "default": None},
        {"table": "t_log2", "column": "created_at", "ordinal": 2, "type": TS_TZ,
         "nullable": False, "default": "now()"},
        {"table": "t_log2", "column": "created_by", "ordinal": 3, "type": "bigint",
         "nullable": True, "default": None},
    ]
    aidx = [{"table": "t_biz", "name": "t_biz_code_active_uniq",
             "definition": "CREATE UNIQUE INDEX t_biz_code_active_uniq ON"
                           " public.t_biz USING btree (code)"
                           " WHERE (deleted_at IS NULL)"}]
    if audit_archetype(amap, acols, aidx, []) != []:
        raise AssertionError("audit 健康合成對被誤判")
    bad = json.loads(json.dumps(acols))
    bad.append({"table": "t_log2", "column": "updated_at", "ordinal": 4,
                "type": TS_TZ, "nullable": True, "default": None})
    if not any("禁欄 updated_at" in x for x in audit_archetype(amap, bad, aidx, [])):
        raise AssertionError("audit 變體 B 禁欄假漂移未被攔")


# ---------------------------------------------------------------------------
# check 子命令
# ---------------------------------------------------------------------------

def cmd_check(root=REPO_ROOT, container=None, user=DB_USER, db=DB_NAME,
              run=subprocess.run):
    # ① self-test（無條件；敗＝rc 2、不讀任何真檔——防恆綠假閘）
    try:
        check_self_test()
    except (AssertionError, GateError) as ex:
        print(f"[check] ✗ self-test 失敗（比對邏輯壞、不讀真檔）：{ex}", file=sys.stderr)
        return 2
    # ② 左源載入（啟動斷言 fail-loud）
    try:
        ledger = load_ledger(root)
        fixtures = load_fixtures(root)
        map_rows = load_archetype_map(root)
        dm_order = load_data_model_order(root)
        roster = load_sequence_roster(root)
    except GateError as ex:
        print(f"[check] ✗ {ex}", file=sys.stderr)
        return 2
    # ③ 右源照相＋dump（唯讀）
    try:
        actual = {
            "columns": sorted(psql(SQL_COLUMNS, parse=True, container=container,
                                   user=user, db=db, run=run),
                              key=lambda r: (r["table"], r["ordinal"])),
            "indexes": sorted(psql(SQL_INDEXES, parse=True, container=container,
                                   user=user, db=db, run=run),
                              key=lambda r: (r["table"], r["name"])),
            "constraints": sorted(psql(SQL_CONSTRAINTS, parse=True, container=container,
                                       user=user, db=db, run=run),
                                  key=lambda r: (r["table"], r["name"])),
        }
        if not actual["columns"]:
            raise GateError("實庫照相 columns 為空——比對面為空（migration 未跑？）")
        dump = pg_dump_data(container=container, user=user, db=db, run=run)
    except GateError as ex:
        print(f"[check] ✗ {ex}", file=sys.stderr)
        return 2
    # ④ 三閘（合成期望；合成不可能＝結構異常 rc 2）
    try:
        expected = synth_expected(fixtures, ledger["entries"])
        frozen_norm = normalize_seed_dump(fixtures["seed"])
        assert_seed_roster(frozen_norm, roster)
        seed_expected = apply_seed_entries(frozen_norm, ledger["entries"])
        findings = compare_structure(expected, actual)
        findings += compare_column_order(dm_order, ledger["entries"], actual["columns"])
        seed_findings = compare_seed(seed_expected, normalize_seed_dump(dump))
        findings += seed_findings
        # ★餵原文 dump（normalize 前）：normalize 已把 Owner 值抹成佔位，餵後者恆綠
        findings += compare_dump_owner(dump, user)
        findings += audit_archetype(map_rows, actual["columns"], actual["indexes"],
                                    actual["constraints"])
    except GateError as ex:
        print(f"[check] ✗ {ex}", file=sys.stderr)
        return 2
    if findings:
        print(f"[check] ✗ {len(findings)} 項漂移（未登記差異一律紅；合法化唯一路徑＝"
              "schema-evolution.json 登記）：", file=sys.stderr)
        for x in findings:
            print(f"    DRIFT {x}", file=sys.stderr)
        return 1
    n_entries = len(ledger["entries"])
    print(f"[check] ✓ gate1 結構：columns {len(actual['columns'])}／indexes "
          f"{len(actual['indexes'])}／constraints {len(actual['constraints'])} 全等"
          f"（演進帳合成 {n_entries} 筆）")
    print(f"[check] ✓ gate2 欄序：{len(dm_order)} 親排表逐位全等"
          f"（{'、'.join(ORDER_EXEMPT)} 豁免）")
    print(f"[check] ✓ gate2 seed：normalize 後 {len(seed_expected.splitlines())} 行"
          f"逐列零差異（setval 名冊 {len(roster)} 支）")
    print(f"[check] ✓ audit archetype：{len(map_rows)}/{len(map_rows)} 綠"
          "（表清單守門通過）")
    return 0


# ---------------------------------------------------------------------------
# doccheck 子命令（B-010；離線、不讀庫；★不入 pre-commit 常跑鏈——護 B-007 效能預算，
# 手動／review 輪跑）
# ---------------------------------------------------------------------------

def cmd_doccheck(root=REPO_ROOT):
    """data-model 文件面 vs 凍結 fixtures 機器對賬；rc：0 全等／1 對賬差異／2 環境或
    結構異常（fixtures 缺、段落定位失敗、解析自檢敗）。"""
    try:
        fixtures = load_fixtures(root)
        path = os.path.join(root, DATA_MODEL)
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            raise GateError(f"data-model.md 缺席（{path}）") from None
        five = parse_data_model_five(text)
        idx_doc, con_doc = parse_data_model_defs(text)
        findings = doccheck_findings(five, idx_doc, con_doc, fixtures)
    except GateError as ex:
        print(f"[doccheck] ✗ {ex}", file=sys.stderr)
        return 2
    if findings:
        print(f"[doccheck] ✗ {len(findings)} 項文件面 vs fixtures 對賬差異（文件單邊"
              "被改＝紅；fixtures 屬凍結面、受損自 git 還原絕不重產）：", file=sys.stderr)
        for x in findings:
            print(f"    DOC-DRIFT {x}", file=sys.stderr)
        return 1
    n_cols = sum(len(v) for v in five.values())
    print(f"[doccheck] ✓ §2 五元組：{len(five)} 親排表 {n_cols} 欄 vs fixtures/columns "
          f"全等（{'、'.join(ORDER_EXEMPT)} 依 §7 豁免）")
    print(f"[doccheck] ✓ §6 索引 {len(idx_doc)} 支／約束 {len(con_doc)} 條 vs "
          "fixtures/{indexes,constraints} 全等")
    return 0


# ---------------------------------------------------------------------------
# 自帶測試（unittest、離線——不觸 docker、不讀實庫）
# ---------------------------------------------------------------------------

_VALID_LEDGER = {"next_id": 1, "entries": []}


def _entry(**kw):
    e = {"id": "E-001", "knife": "001-schema-baseline", "kind": "add_column",
         "table": "sys_user",
         "detail": {"column": "tmp_x", "type": "text", "nullable": True,
                    "default": None, "position": "末位"},
         "date": "2026-08-05"}
    e.update(kw)
    return e


def _write_ledger(d, data):
    path = os.path.join(d, LEDGER)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)


class TestSelfTest(unittest.TestCase):
    def test_self_test_passes(self):
        check_self_test()   # 不 raise 即綠（健康對＋四類注入內含）


class TestNegativeInjection(unittest.TestCase):
    """SC-002 四類假漂移注入、全數必紅（比對器先自證；test 子命令承載面）。"""

    def setUp(self):
        self.fix = _st_fixtures()
        self.healthy = synth_expected(self.fix, [])
        self.norm = normalize_seed_dump(_ST_DUMP)

    def test_1_structure_add_column_red(self):
        drifted = json.loads(json.dumps(self.healthy))
        drifted["columns"].append({"table": "t_ok", "column": "ghost", "ordinal": 3,
                                   "type": "text", "nullable": True, "default": None})
        f = compare_structure(synth_expected(self.fix, []), drifted)
        self.assertTrue(any("columns/t_ok/ghost" in x and "未登記" in x for x in f))

    def test_1b_structure_type_change_red(self):
        mutated = json.loads(json.dumps(self.healthy))
        mutated["columns"][2]["type"] = "integer"
        f = compare_structure(synth_expected(self.fix, []), mutated)
        self.assertTrue(any("columns/t_ok/id" in x for x in f))

    def test_2_column_order_swap_red(self):
        swapped = json.loads(json.dumps(self.healthy["columns"]))
        for c in swapped:
            if c["table"] == "t_ok":
                c["ordinal"] = 3 - c["ordinal"]
        f = compare_column_order({"t_ok": ["id", "name"]}, [], swapped)
        self.assertTrue(any("[gate2·欄序] t_ok" in x for x in f))

    def test_3_seed_value_red(self):
        f = compare_seed(self.norm, self.norm.replace("1\ta", "1\tX"))
        self.assertTrue(f and "diff 非零" in f[0])

    def test_4_setval_red(self):
        f = compare_seed(self.norm, self.norm.replace("', 2, true);", "', 1, true);"))
        self.assertTrue(f and "setval" in f[0])

    def test_registered_then_green(self):
        """演進帳往返縮影：注入紅→登記綠（SC-005 之離線半）。"""
        drifted = json.loads(json.dumps(self.healthy))
        drifted["columns"].append({"table": "t_ok", "column": "ghost", "ordinal": 3,
                                   "type": "text", "nullable": True, "default": None})
        entry = _entry(table="t_ok",
                       detail={"column": "ghost", "type": "text", "nullable": True,
                               "default": None, "position": "末位"})
        self.assertEqual(compare_structure(synth_expected(self.fix, [entry]),
                                           drifted), [])
        f = compare_column_order({"t_ok": ["id", "name"]}, [entry],
                                 drifted["columns"])
        self.assertEqual(f, [])


class TestLedgerAssertions(unittest.TestCase):
    """登記檔啟動斷言七條（contracts/schema-evolution.md §2）＝rc 2 fail-loud。"""

    def _load(self, data):
        with tempfile.TemporaryDirectory() as d:
            _write_ledger(d, data)
            return load_ledger(d)

    def test_baseline_form_green(self):
        self.assertEqual(self._load(_VALID_LEDGER)["entries"], [])
        got = self._load({"next_id": 2, "entries": [_entry()]})
        self.assertEqual(got["entries"][0]["id"], "E-001")

    def test_knife_format_bad(self):
        with self.assertRaisesRegex(GateError, "斷言④.*knife"):
            self._load({"next_id": 2, "entries": [_entry(knife="902_bad_slug")]})

    def test_kind_not_in_enum(self):
        with self.assertRaisesRegex(GateError, "斷言⑤.*kind"):
            self._load({"next_id": 2, "entries": [_entry(kind="rename_column")]})

    def test_drop_kind_named(self):
        with self.assertRaisesRegex(GateError, "斷言⑥.*基線翻案"):
            self._load({"next_id": 2, "entries": [_entry(kind="drop_column")]})

    def test_id_not_ascending(self):
        with self.assertRaisesRegex(GateError, "斷言③.*遞增"):
            self._load({"next_id": 904, "entries": [
                _entry(id="E-903"),
                _entry(id="E-902", kind="add_index", table="sys_role",
                       detail={"name": "x", "definition": "y"})]})

    def test_missing_date_field(self):
        e = _entry()
        del e["date"]
        with self.assertRaisesRegex(GateError, "斷言②.*date"):
            self._load({"next_id": 2, "entries": [e]})

    def test_top_level_keys_exact(self):
        with self.assertRaisesRegex(GateError, "斷言①"):
            self._load({"next_id": 1, "entries": [], "extra": 1})

    def test_next_id_mismatch(self):
        with self.assertRaisesRegex(GateError, "斷言③.*next_id"):
            self._load({"next_id": 9, "entries": [_entry()]})

    def test_json_malformed_caught(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, LEDGER)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{broken")
            with self.assertRaisesRegex(GateError, "JSON 壞形"):
                load_ledger(d)


# 斷言⑦測試樣本：八 kind 各一筆合法 detail（缺鍵樣本＝逐 kind 刪首個必備鍵派生）。
_LEGAL_DETAIL = {
    "add_table": {"columns": [{"column": "id", "type": "bigint", "nullable": False,
                               "default": None}]},
    "add_column": {"column": "x", "type": "text", "nullable": True, "default": None,
                   "position": "末位"},
    "alter_column": {"column": "x", "nullable": False},
    "add_index": {"name": "i_x", "definition": "CREATE INDEX i_x ON public.t (x)"},
    "add_constraint": {"name": "c_x", "definition": "CHECK (x > 0)"},
    "seed_add": {"pk": ["id"], "values": {"id": 1}},
    "seed_update": {"pk": {"id": 1}, "set": {"name": "v"}},
    "seed_delete": {"pk": {"id": 1}},
}


class TestDetailKeyTable(unittest.TestCase):
    """斷言⑦（kind×detail 必備鍵表、B-006）：八 kind 各一筆合法／缺鍵樣本＝16 案
    （方法由下方 setattr 迴圈逐 kind 生成）。"""

    def _load(self, kind, detail):
        with tempfile.TemporaryDirectory() as d:
            _write_ledger(d, {"next_id": 2,
                              "entries": [_entry(kind=kind, detail=detail)]})
            return load_ledger(d)


def _mk_legal(kind):
    def test(self):
        got = self._load(kind, json.loads(json.dumps(_LEGAL_DETAIL[kind])))
        self.assertEqual(got["entries"][0]["kind"], kind)
    test.__doc__ = f"斷言⑦：{kind} 合法樣本必過。"
    return test


def _mk_missing(kind):
    key = DETAIL_KEYS[kind][0]

    def test(self):
        detail = json.loads(json.dumps(_LEGAL_DETAIL[kind]))
        del detail[key]
        if not detail:                    # 空 detail 會先撞斷言②——補墊鍵讓⑦說話
            detail = {"pad": 1}
        with self.assertRaisesRegex(GateError, "斷言⑦.*" + key):
            self._load(kind, detail)
    test.__doc__ = f"斷言⑦：{kind} 缺必備鍵 {key} 必紅。"
    return test


for _k in KINDS:
    setattr(TestDetailKeyTable, f"test_legal_{_k}", _mk_legal(_k))
    setattr(TestDetailKeyTable, f"test_missing_{_k}", _mk_missing(_k))


class TestDetailBadForms(unittest.TestCase):
    """B-006 四壞形改判 rc 2：前世逸出裸例外（ValueError／AttributeError／TypeError→
    解譯器崩潰、殼層收 rc 1）——契約 gates.md §0 rc 語意＝1 漂移／2 環境或結構異常，
    壞形屬後者。紅綠方向：改判前本組全紅（裸例外非 GateError）、改判後全綠。
    ★壞形①另帶 seed_add 姊妹案：契約「`pk`／`set`／`values` 欄名 ⊆ COPY 欄集」括號只
    豁免 `values` 的「恰等」強度、未豁免 `pk`——seed_add 分支同須驗，否則契約過度宣稱。"""

    def setUp(self):
        self.norm = normalize_seed_dump(_ST_DUMP)

    def test_bad1_pk_col_not_in_copy_set(self):
        """壞形①：pk 欄名 ∉ COPY 欄集（前世 cols.index 拋 ValueError）。"""
        e = _entry(kind="seed_update", table="t_ok",
                   detail={"pk": {"ghost": 1}, "set": {"name": "z"}})
        with self.assertRaisesRegex(GateError, "不在 t_ok COPY 欄集"):
            apply_seed_entries(self.norm, [e])

    def test_bad1b_seed_add_pk_col_not_in_copy_set(self):
        """壞形①姊妹案：seed_add 之 pk 欄名 ∉ COPY 欄集（values 欄集合法亦須紅）——
        補檢前靜默通過（契約寫 A、工具驗 B），補檢後 GateError→rc 2。"""
        e = _entry(kind="seed_add", table="t_ok",
                   detail={"pk": ["ghost_col"], "values": {"id": 9, "name": "z"}})
        with self.assertRaisesRegex(GateError, "不在 t_ok COPY 欄集"):
            apply_seed_entries(self.norm, [e])

    def test_bad1c_seed_add_pk_not_list(self):
        """壞形①旁支：seed_add pk 非清單（直呼合成路徑兜底——否則 set() 逐字元拆解、
        錯誤訊息失真）。"""
        e = _entry(kind="seed_add", table="t_ok",
                   detail={"pk": "id", "values": {"id": 9, "name": "z"}})
        with self.assertRaisesRegex(GateError, "pk 須為主鍵欄名非空清單"):
            apply_seed_entries(self.norm, [e])

    def test_bad2_pk_not_object(self):
        """壞形②：pk 非物件（前世 pk_map.items() 拋 AttributeError）；load 斷言⑦同攔。"""
        e = _entry(kind="seed_update", table="t_ok",
                   detail={"pk": [{"id": 1}], "set": {"name": "z"}})
        with self.assertRaisesRegex(GateError, "pk 須為非空物件"):
            apply_seed_entries(self.norm, [e])
        with tempfile.TemporaryDirectory() as d:
            _write_ledger(d, {"next_id": 2, "entries": [e]})
            with self.assertRaisesRegex(GateError, "斷言⑦"):
                load_ledger(d)

    def test_bad3_set_not_object(self):
        """壞形③：set 非物件（前世 d["set"].items() 拋 AttributeError）。"""
        e = _entry(kind="seed_update", table="t_ok",
                   detail={"pk": {"id": 1}, "set": ["name"]})
        with self.assertRaisesRegex(GateError, "set 須為非空物件"):
            apply_seed_entries(self.norm, [e])

    def test_bad4_values_not_object(self):
        """壞形④：seed_add values 非物件（前世 set(d["values"]) 拋 TypeError）。"""
        e = _entry(kind="seed_add", table="t_ok",
                   detail={"pk": ["id"], "values": 7})
        with self.assertRaisesRegex(GateError, "values 須為物件"):
            apply_seed_entries(self.norm, [e])


class TestDuplicateRegistration(unittest.TestCase):
    """B-006 值域斷言：同名 index/constraint 重複登記攔——前世 synth 靜默附掛、compare
    面 (table,name) 字典鍵合併＝重複被吞、閘照綠。"""

    def test_add_index_duplicate(self):
        e = _entry(kind="add_index", table="t_ok",
                   detail={"name": "t_ok_pkey", "definition": "CREATE INDEX x"})
        with self.assertRaisesRegex(GateError, "重複登記"):
            synth_expected(_st_fixtures(), [e])

    def test_add_constraint_duplicate(self):
        e = _entry(kind="add_constraint", table="t_ok",
                   detail={"name": "t_ok_pkey", "definition": "PRIMARY KEY (id)"})
        with self.assertRaisesRegex(GateError, "重複登記"):
            synth_expected(_st_fixtures(), [e])


class TestFixturesMissing(unittest.TestCase):
    def test_check_rc2_with_remedy(self):
        """fixtures 缺席＝check rc 2 附補救提示（T011 驗收面；self-test＋登記檔綠後即攔、
        零 docker）。"""
        with tempfile.TemporaryDirectory() as d:
            _write_ledger(d, _VALID_LEDGER)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("fixtures/columns.json 缺席", err.getvalue())
            self.assertIn("補救", err.getvalue())


class TestSeedSynthesis(unittest.TestCase):
    def setUp(self):
        self.norm = normalize_seed_dump(_ST_DUMP)

    def test_seed_add(self):
        e = _entry(kind="seed_add", table="t_ok",
                   detail={"pk": ["id"], "values": {"id": 3, "name": "c"}})
        out = apply_seed_entries(self.norm, [e])
        self.assertIn("3\tc", out)
        self.assertEqual(compare_seed(out, normalize_seed_dump(out)), [])

    def test_seed_update(self):
        e = _entry(kind="seed_update", table="t_ok",
                   detail={"pk": {"id": 1}, "set": {"name": "z"}})
        out = apply_seed_entries(self.norm, [e])
        self.assertIn("1\tz", out)
        self.assertNotIn("1\ta", out)

    def test_seed_delete(self):
        e = _entry(kind="seed_delete", table="t_ok", detail={"pk": {"id": 2}})
        out = apply_seed_entries(self.norm, [e])
        self.assertNotIn("2\tb", out)

    def test_seed_update_pk_miss_fail_loud(self):
        e = _entry(kind="seed_update", table="t_ok",
                   detail={"pk": {"id": 99}, "set": {"name": "z"}})
        with self.assertRaisesRegex(GateError, "命中 0 列"):
            apply_seed_entries(self.norm, [e])

    def test_null_literal(self):
        self.assertEqual(copy_literal(None), "\\N")
        self.assertEqual(copy_literal(True), "t")
        self.assertEqual(copy_literal("a\tb"), "a\\tb")

    def test_roster_assert(self):
        assert_seed_roster(self.norm, ["t_ok_id_seq"])
        with self.assertRaisesRegex(GateError, "setval 名冊"):
            assert_seed_roster(self.norm, ["t_ok_id_seq", "missing_seq"])

    def test_add_column_header_and_fill(self):
        out = apply_seed_entries(self.norm, [_entry(table="t_ok")])
        self.assertIn("COPY public.t_ok (id, name, tmp_x) FROM stdin;", out)
        self.assertIn("1\ta\t\\N", out)

    def test_add_column_with_default_fail_loud(self):
        e = _entry(table="t_ok",
                   detail={"column": "x", "type": "text", "nullable": True,
                           "default": "'v'::text", "position": "末位"})
        with self.assertRaisesRegex(GateError, "僅支援 nullable 無 default"):
            apply_seed_entries(self.norm, [e])

    def test_add_table_seed_face_fail_loud(self):
        e = _entry(kind="add_table", table="t_new",
                   detail={"columns": [{"column": "id", "type": "bigint",
                                        "nullable": False}]})
        with self.assertRaisesRegex(GateError, "add_table.*seed 面"):
            apply_seed_entries(self.norm, [e])


class TestPgDumpArgv(unittest.TestCase):
    """pg_dump 旗標渲染回歸：-e PGTZ=UTC 必掛 exec 子命令之後（兩形皆然）。
    曾有缺陷：compose 形把 -e 插在 docker compose 頂層 → `unknown shorthand flag: 'e'`
    rc 1 → check 對 dev stack 永遠 rc 2（quickstart §B／RUNBOOK §10 裸 check 不可用）。"""

    class _R:
        returncode, stdout, stderr = 0, "x", ""

    def _rendered(self, container):
        seen = {}

        def fake_run(cmd, **kw):
            seen["cmd"] = cmd
            return self._R()

        pg_dump_data(container=container, run=fake_run)
        return seen["cmd"]

    def test_compose_form_env_after_exec(self):
        cmd = self._rendered(None)
        i = cmd.index("exec")
        self.assertEqual(cmd[i + 1:i + 3], ["-e", "PGTZ=UTC"])
        self.assertNotIn("-e", cmd[:i])      # docker compose 頂層絕無 -e

    def test_container_form_env_after_exec(self):
        self.assertEqual(self._rendered("pristine-pg")[:6],
                         ["docker", "exec", "-e", "PGTZ=UTC", "-i", "pristine-pg"])


class TestCmdCheckGreenPath(unittest.TestCase):
    """B-013 缺口①：cmd_check 綠路徑離線全程（照相→合成→三閘→四行摘要→rc 0）。樁沿
    TestPgDumpArgv fake_run 法：按 SQL 常數分派 fixtures 三節 JSON、pg_dump 回凍結
    seed.sql。★驗 SQL 分派正確＋四行摘要格式計數＋rc 0；比對器邏輯歸 check_self_test
    承載、此處刻意不重驗（分工）。凍結基線複製入暫存 root＋空演進帳＝真登記檔日後長
    entries 也不影響本測（凍結面永不改寫、字面計數可釘）。"""

    _COPY = ("specs/001-schema-baseline/fixtures/columns.json",
             "specs/001-schema-baseline/fixtures/indexes.json",
             "specs/001-schema-baseline/fixtures/constraints.json",
             "specs/001-schema-baseline/fixtures/seed.sql",
             "specs/001-schema-baseline/data-model.md",
             "specs/001-schema-baseline/seed-decision.json",
             "docs/ops/reference-src/archetype-map.json")

    def test_green_path_sql_dispatch_summary_rc0(self):
        fx = load_fixtures(REPO_ROOT)
        dispatch = {SQL_COLUMNS: fx["columns"], SQL_INDEXES: fx["indexes"],
                    SQL_CONSTRAINTS: fx["constraints"]}
        calls = []

        class _R:
            returncode, stderr = 0, ""

            def __init__(self, out):
                self.stdout = out

        def fake_run(cmd, **kw):
            if "pg_dump" in cmd:
                calls.append("pg_dump")
                return _R(fx["seed"])
            sql = cmd[-1]
            if sql not in dispatch:
                raise AssertionError(f"樁收到未知 SQL（分派錯）：{sql[:80]}")
            calls.append(sql)
            return _R(json.dumps(dispatch[sql]))

        with tempfile.TemporaryDirectory() as d:
            for rel in self._COPY:
                dst = os.path.join(d, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(os.path.join(REPO_ROOT, rel), dst)
            _write_ledger(d, _VALID_LEDGER)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cmd_check(root=d, run=fake_run)
        self.assertEqual(rc, 0)
        # SQL 分派：三查詢恰各一次、序＝columns→indexes→constraints，殿後 pg_dump
        self.assertEqual(calls, [SQL_COLUMNS, SQL_INDEXES, SQL_CONSTRAINTS, "pg_dump"])
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(ln.startswith("[check] ✓") for ln in lines), msg=lines)
        self.assertIn("gate1 結構：columns 169／indexes 38／constraints 101 全等",
                      lines[0])
        self.assertIn("演進帳合成 0 筆", lines[0])
        self.assertIn("gate2 欄序：14 親排表逐位全等", lines[1])
        self.assertIn("casbin_rule 豁免", lines[1])
        n = len(normalize_seed_dump(fx["seed"]).splitlines())
        self.assertIn(f"gate2 seed：normalize 後 {n} 行逐列零差異（setval 名冊 11 支）",
                      lines[2])
        self.assertIn("audit archetype：15/15 綠", lines[3])


class TestSnapshotIsomorphism(unittest.TestCase):
    """B-013 缺口②：gate1 照相三 SQL 常數 vs tools/docs-sync.py refresh 三常數位元相等
    ——兩工具刻意重複、「同構」宣稱的唯一機器載體（importlib 實載模組取常數值、
    非讀源碼文字比對）。"""

    def test_three_sql_constants_bit_identical(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "docs_sync_isomorphism_probe",
            os.path.join(REPO_ROOT, "tools", "docs-sync.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in ("SQL_COLUMNS", "SQL_INDEXES", "SQL_CONSTRAINTS"):
            self.assertEqual(globals()[name], getattr(mod, name),
                             msg=f"{name} 兩工具位元不相等——gate1 照相與 refresh 快照"
                                 "不再同構（單邊改動）")


class TestDockerUnavailable(unittest.TestCase):
    """docker 不可執行（OSError；不在 PATH／CLI 缺）＝環境異常 GateError→rc 2——
    非 rc 1 漂移、非裸 traceback（契約 gates.md §0；RUNBOOK §12 依碼判讀之根據）。
    注意與 daemon 停擺區分：後者 docker 有跑、回非零、走既有 rc≠0 分支。"""

    @staticmethod
    def _no_docker(cmd, **kw):
        raise FileNotFoundError(2, "No such file or directory", "docker")

    def test_psql_oserror_to_gateerror(self):
        with self.assertRaisesRegex(GateError, "無法執行 docker"):
            psql("SELECT 1", parse=True, run=self._no_docker)

    def test_pg_dump_oserror_to_gateerror(self):
        with self.assertRaisesRegex(GateError, "無法執行 docker"):
            pg_dump_data(run=self._no_docker)

    def test_cmd_check_rc2_with_remedy(self):
        """cmd_check 層：左源全綠後右源照相撞 OSError → rc 2 附補救、絕不判漂移。"""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cmd_check(run=self._no_docker), 2)
        self.assertIn("無法執行 docker", err.getvalue())
        self.assertIn("--container", err.getvalue())


class TestDataModelParse(unittest.TestCase):
    DM = ("## 2. 逐表欄序定稿\n\n### t_a（2 欄；變體 A）\n\n"
          "| # | 欄 | 型別 | NULL | default | 註 |\n|---|---|---|---|---|---|\n"
          "| 1 | id | bigint | NN | —— |  |\n| 2 | name | text | 可空 | —— |  |\n\n"
          + "".join(f"### t_{c}（1 欄）\n\n| # | 欄 | 型別 | NULL | default | 註 |\n"
                    "|---|---|---|---|---|---|\n| 1 | id | bigint | NN | —— |  |\n\n"
                    for c in "bcdefghijklmn")
          + "## 3. rename map\n")

    def test_parse_and_self_check(self):
        got = parse_data_model_order(self.DM)
        self.assertEqual(got["t_a"], ["id", "name"])
        self.assertEqual(len(got), 14)

    def test_declared_count_mismatch_fail_loud(self):
        with self.assertRaisesRegex(GateError, "解析自檢敗"):
            parse_data_model_order(self.DM.replace("t_a（2 欄", "t_a（3 欄"))

    def test_real_data_model_parses(self):
        """對現庫 data-model 實解析：14 親排表、總欄 158（凍結定稿字面）。"""
        got = load_data_model_order(REPO_ROOT)
        self.assertEqual(len(got), 14)
        self.assertEqual(sum(len(v) for v in got.values()), 158)
        self.assertEqual(len(got["sys_user"]), 17)


class TestAuditEngine(unittest.TestCase):
    def test_unknown_c_subtype_fail_loud(self):
        amap = [{"table": "t_mystery", "label": "C join·狀態機",
                 "active_unique": None, "note": ""}]
        cols = [{"table": "t_mystery", "column": "id", "ordinal": 1,
                 "type": "bigint", "nullable": False, "default": None}]
        with self.assertRaisesRegex(GateError, "子型規則未硬編碼"):
            audit_archetype(amap, cols, [], [])

    def test_table_guard_both_ways(self):
        amap = [{"table": "t_biz", "label": "A 業務全六欄",
                 "active_unique": None, "note": ""}]
        cols = [{"table": "t_other", "column": "id", "ordinal": 1,
                 "type": "bigint", "nullable": False, "default": None}]
        f = audit_archetype(amap, cols, [], [])
        self.assertTrue(any("t_other 未登記" in x for x in f))
        self.assertTrue(any("t_biz 不在實庫" in x for x in f))

    def test_created_by_nn_roster_enforced(self):
        """created_by 可空性顯式驗：非 NN 四表卻 NN＝紅。"""
        amap = [{"table": "t_log2", "label": "B append-only",
                 "active_unique": None, "note": ""}]
        cols = [
            {"table": "t_log2", "column": "created_at", "ordinal": 1, "type": TS_TZ,
             "nullable": False, "default": "now()"},
            {"table": "t_log2", "column": "created_by", "ordinal": 2,
             "type": "bigint", "nullable": False, "default": None},
        ]
        f = audit_archetype(amap, cols, [], [])
        self.assertTrue(any("created_by｜可空性顯式驗不符" in x for x in f))


class TestAuditBForbiddenPrefix(unittest.TestCase):
    """B-012（ADR 0016）變體 B 禁欄三向紅綠：①前綴新欄（updated_fields）紅——具名四欄
    時代的漏網形；②具名豁免清單加列後綠——正規出口；③具名四欄仍紅——前綴判準涵蓋原
    判準、守門不縮水。"""

    A_MAP = [{"table": "t_log2", "label": "B append-only",
              "active_unique": None, "note": ""}]

    def _cols(self, extra):
        return [
            {"table": "t_log2", "column": "id", "ordinal": 1, "type": "bigint",
             "nullable": False, "default": None},
            {"table": "t_log2", "column": "created_at", "ordinal": 2, "type": TS_TZ,
             "nullable": False, "default": "now()"},
            {"table": "t_log2", "column": "created_by", "ordinal": 3, "type": "bigint",
             "nullable": True, "default": None},
            {"table": "t_log2", "column": extra, "ordinal": 4, "type": "jsonb",
             "nullable": True, "default": None},
        ]

    def test_1_prefix_new_column_red(self):
        for col in ("updated_fields", "deleted_flag"):
            f = audit_archetype(self.A_MAP, self._cols(col), [], [])
            self.assertTrue(any(f"禁欄 {col}" in x for x in f), msg=(col, f))

    def test_2_exempt_listed_then_green(self):
        key = ("t_log2", "updated_fields")
        AUDIT_B_EXEMPT[key] = "測試豁免：payload 欄（jsonb 記變更欄集）——非審計欄"
        try:
            f = audit_archetype(self.A_MAP, self._cols("updated_fields"), [], [])
            self.assertEqual([x for x in f if "禁欄" in x], [])
        finally:
            del AUDIT_B_EXEMPT[key]

    def test_3_named_four_still_red(self):
        for col in ("updated_at", "updated_by", "deleted_at", "deleted_by"):
            f = audit_archetype(self.A_MAP, self._cols(col), [], [])
            self.assertTrue(any(f"禁欄 {col}" in x for x in f), msg=(col, f))


class TestMapAssertions(unittest.TestCase):
    def _map(self, tables):
        return {"lineage": "x", "usage": "y", "tables": tables}

    def _load(self, data):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, ARCHETYPE_MAP)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
            return load_archetype_map(d)

    def test_label_out_of_domain(self):
        with self.assertRaisesRegex(GateError, "值域外"):
            self._load(self._map([{"table": "t", "label": "E 神秘",
                                   "active_unique": None, "note": ""}]))

    def test_duplicate_table(self):
        row = {"table": "t", "label": "D 治理", "active_unique": None, "note": ""}
        with self.assertRaisesRegex(GateError, "重複登記"):
            self._load(self._map([row, dict(row)]))

    def test_missing_key(self):
        with self.assertRaisesRegex(GateError, "鍵集須恰為"):
            self._load(self._map([{"table": "t", "label": "D 治理"}]))

    def test_real_map_day1_form(self):
        """現庫 archetype-map 實載：恰 15 筆（gates.md §3 Day-1 形）＋load 斷言全過。"""
        rows = load_archetype_map(REPO_ROOT)
        self.assertEqual(len(rows), 15)
        self.assertEqual(sorted(r["table"] for r in rows if r["label"] == LABELS[0]),
                         ["sys_ip_rule", "sys_menu", "sys_role", "sys_user",
                          "system_settings"])


class TestDocCheck(unittest.TestCase):
    """B-010：data-model 文件面（§2 五元組／§6 索引約束）vs 凍結 fixtures 機器對賬——
    兩個已實證解析陷阱之負向測試＋比對器非恆綠自證＋今日真 repo 基線全綠。"""

    DM2 = ("## 2. 逐表欄序定稿\n\n### t_a（2 欄）\n\n"
           "| # | 欄 | 型別 | NULL | default | 註 |\n|---|---|---|---|---|---|\n"
           "| 1 | id | bigint | NN | nextval('s'::regclass) |  |\n"
           "| 2 | memo | text | 可空 | —— |  |\n\n"
           + "".join(f"### t_{c}（1 欄）\n\n| # | 欄 | 型別 | NULL | default | 註 |\n"
                     "|---|---|---|---|---|---|\n| 1 | id | bigint | NN | —— |  |\n\n"
                     for c in "bcdefghijklmn")
           + "## 3. rename map\n")

    DM6 = ("## 6. 索引與約束\n\n總計：索引 1 支、約束 2 條（含 NOT NULL 逐欄形）。\n\n"
           "### t_a\n\n索引（1）：\n\n"
           "- `t_a_pkey`：`CREATE UNIQUE INDEX t_a_pkey ON public.t_a USING btree (id)`\n"
           "\n約束（2）：\n\n"
           "- `t_a_pkey`：`PRIMARY KEY (id)`\n"
           "- `t_a_real_ip_not_null`：`NOT NULL real_ip`（★§4 定稿差異新增、rev4 無）\n\n"
           "## 7. casbin_rule\n")

    def _fx(self):
        cols = [{"table": "t_a", "column": "id", "ordinal": 1, "type": "bigint",
                 "nullable": False, "default": "nextval('s'::regclass)"},
                {"table": "t_a", "column": "memo", "ordinal": 2, "type": "text",
                 "nullable": True, "default": None}]
        for c in "bcdefghijklmn":
            cols.append({"table": f"t_{c}", "column": "id", "ordinal": 1,
                         "type": "bigint", "nullable": False, "default": None})
        return {"columns": cols,
                "indexes": [{"table": "t_a", "name": "t_a_pkey",
                             "definition": "CREATE UNIQUE INDEX t_a_pkey ON public.t_a"
                                           " USING btree (id)"}],
                "constraints": [{"table": "t_a", "name": "t_a_pkey",
                                 "definition": "PRIMARY KEY (id)"},
                                {"table": "t_a", "name": "t_a_real_ip_not_null",
                                 "definition": "NOT NULL real_ip"}]}

    def test_missing_fixtures_root_is_rc2(self):
        """負向：fixtures 缺席＝環境／結構異常 rc 2（GateError 路徑、非裸例外）。"""
        with tempfile.TemporaryDirectory() as td, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cmd_doccheck(root=td), 2)

    def test_trap1_dash_default_is_none(self):
        """陷阱①：§2 default 欄「——」＝無 default（None）——取字面比對即全表假紅。"""
        five = parse_data_model_five(self.DM2)
        self.assertEqual(five["t_a"][1], (2, "memo", "text", True, None))
        self.assertEqual(five["t_a"][0],
                         (1, "id", "bigint", False, "nextval('s'::regclass)"))

    def test_trap2_trailing_note_parsed(self):
        """陷阱②：§6 條目行可帶尾註（實例＝sys_operation_log_real_ip_not_null 行帶
        「（★§4 定稿差異新增、rev4 無）」）——嚴格行尾錨會少數一條、宣告支數自檢連帶炸。"""
        idx, con = parse_data_model_defs(self.DM6)
        self.assertEqual(len(idx), 1)
        self.assertEqual(con[("t_a", "t_a_real_ip_not_null")], "NOT NULL real_ip")

    def test_declared_count_mismatch_fail_loud(self):
        with self.assertRaisesRegex(GateError, "自檢敗"):
            parse_data_model_defs(self.DM6.replace("約束（2）", "約束（3）"))

    def test_comparator_red_on_single_field(self):
        """比對器非恆綠自證：單格改動即紅、逐項指名（§2 型別格＋§6 定義文字各一）。"""
        five = parse_data_model_five(self.DM2)
        idx, con = parse_data_model_defs(self.DM6)
        fx = self._fx()
        self.assertEqual(doccheck_findings(five, idx, con, fx), [])   # 健康對綠
        fx["columns"][0]["type"] = "integer"
        f = doccheck_findings(five, idx, con, fx)
        self.assertTrue(any("[doccheck·§2] t_a.id" in x for x in f), msg=f)
        fx2 = self._fx()
        fx2["constraints"][0]["definition"] = "PRIMARY KEY (memo)"
        f2 = doccheck_findings(five, idx, con, fx2)
        self.assertTrue(any("[doccheck·§6] constraints/t_a/t_a_pkey" in x
                            for x in f2), msg=f2)

    def test_order_exempt_not_false_reported(self):
        """casbin_rule 依 §7／ORDER_EXEMPT 本就不在 §2——fixtures 面豁免、勿誤報。"""
        five = parse_data_model_five(self.DM2)
        idx, con = parse_data_model_defs(self.DM6)
        fx = self._fx()
        fx["columns"].append({"table": "casbin_rule", "column": "id", "ordinal": 1,
                              "type": "bigint", "nullable": False, "default": None})
        self.assertEqual([x for x in doccheck_findings(five, idx, con, fx)
                          if "§2" in x], [])

    def test_real_repo_green_rc0(self):
        """今日基線必須全綠（偵查離線實證：§2 14 表 158 欄、§6 索引 38／約束 101 全等）。"""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cmd_doccheck(REPO_ROOT), 0)
        self.assertIn("§2 五元組：14 親排表 158 欄", out.getvalue())
        self.assertIn("§6 索引 38 支／約束 101 條", out.getvalue())


class TestConstantsPinned(unittest.TestCase):
    """治理常數字面釘死（慣例承 entity-drift-gate TestWhitelist）：常數縮水＝斷言跟縮
    的套套邏輯在此擋。"""

    def test_kinds_exactly_eight(self):
        self.assertEqual(KINDS, ("add_table", "add_column", "alter_column",
                                 "add_index", "add_constraint",
                                 "seed_add", "seed_update", "seed_delete"))

    def test_labels_four(self):
        self.assertEqual(LABELS, ("A 業務全六欄", "B append-only",
                                  "C join·狀態機", "D 治理"))

    def test_created_by_nn_four(self):
        self.assertEqual(CREATED_BY_NN, ("sys_access_log", "sys_token",
                                         "sys_pwd_custody", "sys_user_email_verify"))

    def test_rename_map_four_pairs(self):
        self.assertEqual(RENAME_MAP, {
            "operator_real_ip": "real_ip", "operator_peer_ip": "peer_ip",
            "operator_x_forwarded_for": "x_forwarded_for",
            "operator_ip_confidence": "ip_confidence"})

    def test_detail_keys_and_audit_b_pinned(self):
        """B-006／B-012 治理常數逐字釘死——TestDetailKeyTable 樣本與豁免出口皆由其派生，
        縮水即套套邏輯（實證：DETAIL_KEYS 縮鍵後 _assert_detail 逸出裸 KeyError 回 rc 1
        形而 85 案全綠）；AUDIT_B_EXEMPT 每筆形制機器強制（(表,欄) tuple＋非空理由）。"""
        self.assertEqual(DETAIL_KEYS, {
            "add_table": ("columns",),
            "add_column": ("column", "type", "nullable"),
            "alter_column": ("column",),
            "add_index": ("name", "definition"),
            "add_constraint": ("name", "definition"),
            "seed_add": ("pk", "values"),
            "seed_update": ("pk", "set"),
            "seed_delete": ("pk",),
        })
        self.assertEqual(AUDIT_B_FORBIDDEN_PREFIXES, ("updated_", "deleted_"))
        self.assertEqual(AUDIT_B_EXEMPT, {})   # Day-1 空集；加列＝同 commit 改本案＋附理由
        for key, reason in AUDIT_B_EXEMPT.items():
            self.assertIsInstance(key, tuple)
            self.assertEqual(len(key), 2)
            self.assertTrue(all(isinstance(x, str) and x for x in key))
            self.assertTrue(isinstance(reason, str) and reason.strip())

    def test_paths_are_001_coordinates(self):
        """rev4 世代座標（specs/rev4:002）整組清償：路徑常數一律 001。"""
        for p in (FIXTURES_DIR, DATA_MODEL, SEED_DECISION):
            self.assertIn("001-schema-baseline", p)


class TestUsage(unittest.TestCase):
    def test_no_args_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["schema-gate.py"]), 64)

    def test_unknown_subcommand_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["schema-gate.py", "gate1"]), 64)

    def test_check_unknown_flag_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["schema-gate.py", "check", "--bogus"]), 64)

    def test_check_flag_missing_value_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["schema-gate.py", "check", "--container"]), 64)

    def test_doccheck_extra_arg_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["schema-gate.py", "doccheck", "x"]), 64)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def usage(msg=None):
    if msg:
        print(msg, file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 64


def main(argv):
    if len(argv) < 2:
        return usage()
    cmd = argv[1]
    if cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    if cmd == "doccheck":
        if len(argv) > 2:
            return usage(f"doccheck 不收引數（得 {argv[2:]}）")
        return cmd_doccheck()
    if cmd == "check":
        container, user, db = None, DB_USER, DB_NAME
        args = argv[2:]
        i = 0
        while i < len(args):
            flag = args[i]
            if flag not in ("--container", "--user", "--db"):
                return usage(f"未知旗標：{flag}")
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                return usage(f"旗標 {flag} 缺值")
            val = args[i + 1]
            if flag == "--container":
                container = val
            elif flag == "--user":
                user = val
            else:
                db = val
            i += 2
        return cmd_check(container=container, user=user, db=db)
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
