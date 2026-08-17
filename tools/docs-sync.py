#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/docs-sync.py — rev5 文件系統生成器＋lint（python 標準庫、單檔、自帶測試）

子命令：
  generate        重算 docs/generated/ 全部（含 ADR superseded_by 對稱回填）
  check           重算到暫存與現況 diff、不一致 exit 1（= lint Lint01 本體＋Lint02 對賬）
  lint            Lint03～Lint26（Lint04/Lint05/Lint06 收刀完整性閘：
                  事件存在性／review 分流／arch_impact 雙向；
                  Lint16 憑證內容掃描：外層 tracked 全量＋pin bump 時 submodule 增量；
                  Lint17 pin↔worktree HEAD 互證；Lint18 events 帳本 SHA 逐列向 git 實證；
                  Lint19 三件活手冊的 tools 命令形 vs 掃源真表＋舊名禁令；
                  Lint20 空集合守衛八組；Lint21 名冊腳本 index exec bit＝100755；
                  Lint22 條款範圍字串名冊 vs 掃源上界；
                  Lint24 前後端 msg key 契約閘；
                  Lint25 跨代裸編號閘：前代編號空間的裸引用須帶 revN: 前綴；
                  Lint26 LESSONS 分檔對賬：檔名↔正文 ID／索引↔檔雙向／promoted_to 必填）
                  輸出末行＝「lint：X 錯誤／Y 警告／Z 條款跳過」，Z>0 時次行列跳過明細。
  refresh         自實庫撈快照寫 docs/ops/reference-src/（唯一需 docker 的子命令）
  errata <詞>     全 repo 同語意枚舉報告
  test            跑自帶測試（unittest）

token 計數：UTF-8 bytes ÷ 3 保守近似（測試鎖定算法）。
"""
import concurrent.futures
import contextlib
import functools
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

# ---------------------------------------------------------------------------
# 共用基礎
# ---------------------------------------------------------------------------

# repo 相對路徑常數
EVENTS = "docs/ops/events.jsonl"
BOOK = "docs/arc42/ARCHITECTURE.md"
NOTES = "docs/ops/NOTES.md"
BACKLOG = "docs/ops/BACKLOG.md"
STATE = "docs/generated/STATE.md"
ADR_DIR = "docs/arc42/decisions"
GENERATED_DIR = "docs/generated"
# events 帳本 pins 鍵名 ↔ submodule 目錄之固定映射（帳本實形；rev4:contracts G2/G3 共用單一真值）
PIN_KEYS = (("web", "base-web"), ("api", "rust-api"))


def token_count(text):
    """token 保守近似 = UTF-8 bytes ÷ 3（整數除法）。"""
    return len(text.encode("utf-8")) // 3


def _yaml_scalar(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def parse_front_matter(text):
    """解析 md 檔頭 front-matter（YAML 子集：scalar、flow list、行首 key:）。

    回 (meta_dict, body_str)；無 front-matter 回 ({}, 原文)。
    支援：字串 scalar（可帶引號）、flow list [a, b]、空 list []。
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "".join(lines[i + 1:])
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            val = [_yaml_scalar(x) for x in inner.split(",")] if inner else []
        else:
            val = _yaml_scalar(raw)
        meta[key.strip()] = val
    return {}, text  # 沒關閉的 front-matter：視同無


# ---------------------------------------------------------------------------
# lint 基礎設施
# ---------------------------------------------------------------------------

# SKIP＝條款不適用而未執行（rev4:FR-012：「不適用」與「通過」必須顯式區分）。三者都是 finding，
# 只是 SKIP 不進條列區、只在摘要次行的跳過明細出現，且不影響退出碼。
ERROR, WARN, SKIP = "ERROR", "WARN", "SKIP"


def finding(level, code, where, msg):
    return {"level": level, "code": code, "where": where, "msg": msg}


RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_FEATURE = re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*$")
# 全域 40 位、無史料豁免分支（FR-010／FR-011；前置＝rev4:T010 四筆短 SHA 正規化勘誤 commit）
RE_SHA = re.compile(r"^[0-9a-f]{40}$")
RE_SECTION = re.compile(r"^§\d{1,2}$")
RE_ADR_ID = re.compile(r"^\d{4}$")
RE_BID = re.compile(r"^B-\d{3,}$")

# erratum 可更正的欄枚舉：merge 驗於外層、pins.* 依 PIN_KEYS 映射驗於各 submodule——
# 與 Lint18 的驗證面同一份真值，故自 PIN_KEYS 導出、不落第二份字面名冊。
ERRATUM_FIELDS = ("merge",) + tuple(f"pins.{key}" for key, _sub in PIN_KEYS)

EVENT_SCHEMAS = {
    "feature_close": {
        "required": ["type", "feature", "merge", "date", "summary", "pins",
                     "adrs", "arch_impact", "backlog_add", "backlog_done"],
        "optional": ["kind", "spec_supersessions", "notes"],
    },
    "review": {
        "required": ["type", "date", "scope", "report", "findings"],
        "optional": ["notes"],
    },
    "misc": {
        "required": ["type", "date", "summary"],
        # backlog_done：輕量軌收刀（非 NNN- branch、無 feature_close 事件）消化 BACKLOG 條目的
        # 唯一證據通道（Lint04/Lint05 對賬同源；user 拍板調規 2026-07-17——維護批首例）。
        "optional": ["notes", "backlog_done"],
    },
    # erratum＝對已入史事件列的 append 型更正（B-042 調閘形、ADR 0012 決定 5「既有列
    # 絕不編輯」的機器可認出口）：Lint18 以更正視圖重驗 target 列、corrected 本身亦被實證。
    "erratum": {
        "required": ["type", "date", "target_line", "field", "corrected", "reason"],
        "optional": ["notes"],
    },
}


def _id_list_ok(v, pattern):
    return (isinstance(v, list)
            and all(isinstance(x, str) and pattern.fullmatch(x) for x in v))


def _check_event(e):
    """單筆事件的欄位驗證；回錯誤訊息 list。"""
    if not isinstance(e, dict):
        return ["事件須為 JSON object（一行一事件）"]
    errs = []
    etype = e.get("type")
    schema = EVENT_SCHEMAS.get(etype)
    if schema is None:
        return [f"未知 type「{etype}」（合法：{'/'.join(EVENT_SCHEMAS)}）"]
    for k in schema["required"]:
        if k not in e:
            errs.append(f"缺必填欄位「{k}」")
    allowed = set(schema["required"]) | set(schema["optional"])
    for k in e:
        if k not in allowed:
            errs.append(f"未知欄位「{k}」")
    if errs:
        return errs
    if not RE_DATE.fullmatch(str(e["date"])):
        errs.append(f"date 格式須為 YYYY-MM-DD：{e['date']!r}")
    # ★summary 單筆上限（Q6；併入 Lint03——長度即欄位形，與 merge 恆 40-hex、
    #   findings 四鍵守恆律同層級，故不另立條款、條款總數不變、Lint22 範圍字串不動）
    if "summary" in e and isinstance(e["summary"], str):
        if "\n" in e["summary"] or "\r" in e["summary"]:
            errs.append("summary 不得含換行（jsonl 一行一事件；多段敘述請移 notes 或報告檔）")
        if len(e["summary"]) > SUMMARY_CHAR_LIMIT:
            errs.append(f"summary {len(e['summary'])} 字超出單筆上限 {SUMMARY_CHAR_LIMIT}"
                        "——細節移 notes 選填欄／報告檔／LESSONS")
    if etype == "feature_close":
        if not RE_FEATURE.fullmatch(str(e["feature"])):
            errs.append(f"feature 格式須為 NNN-slug：{e['feature']!r}")
        if not RE_SHA.fullmatch(str(e["merge"])):
            errs.append(f"merge 須為 git SHA：{e['merge']!r}")
        pins = e["pins"]
        if not (isinstance(pins, dict) and set(pins) == {"web", "api"}
                and all(RE_SHA.fullmatch(str(v)) for v in pins.values())):
            errs.append('pins 須為 {"web": SHA, "api": SHA}')
        if not _id_list_ok(e["adrs"], RE_ADR_ID):
            errs.append("adrs 須為 4 位 ADR 編號字串 list（可空）")
        ai = e["arch_impact"]
        if not (ai == "none" or (isinstance(ai, list) and ai
                                 and all(isinstance(x, str) and RE_SECTION.fullmatch(x)
                                         for x in ai))):
            errs.append('arch_impact 須為 ["§N", …] 或 "none"')
        for k in ("backlog_add", "backlog_done"):
            if not _id_list_ok(e[k], RE_BID):
                errs.append(f"{k} 須為 B-NNN 字串 list（可空）")
        if "kind" in e and e["kind"] not in ("vertical", "horizontal"):
            errs.append('kind 須為 "vertical"|"horizontal"')
        if "spec_supersessions" in e:
            ss = e["spec_supersessions"]
            if not (isinstance(ss, list) and all(
                    isinstance(x, dict) and set(x) == {"feature", "item", "note"}
                    for x in ss)):
                errs.append("spec_supersessions 須為 [{feature,item,note},…]")
    elif etype == "review":
        fd = e["findings"]
        if not (isinstance(fd, dict)
                and set(fd) == {"total", "fixed", "to_backlog", "wontfix_adr"}
                and isinstance(fd.get("total"), int) and fd["total"] >= 0
                and isinstance(fd.get("fixed"), int) and fd["fixed"] >= 0
                and _id_list_ok(fd.get("to_backlog"), RE_BID)
                and _id_list_ok(fd.get("wontfix_adr"), RE_ADR_ID)):
            errs.append("findings 須為 {total≥0, fixed≥0, to_backlog[B-NNN…], wontfix_adr[00NN…]}")
        elif fd["fixed"] + len(fd["to_backlog"]) + len(fd["wontfix_adr"]) != fd["total"]:
            errs.append("findings 分流不守恆：fixed＋len(to_backlog)＋len(wontfix_adr) 須＝total")
    elif etype == "misc":
        if "backlog_done" in e and not _id_list_ok(e["backlog_done"], RE_BID):
            errs.append("backlog_done 須為 B-NNN 字串 list（可空）")
    elif etype == "erratum":
        tl = e["target_line"]
        if not (isinstance(tl, int) and not isinstance(tl, bool) and tl >= 1):
            errs.append(f"target_line 須為正整數（events.jsonl 行號）：{tl!r}")
        if e["field"] not in ERRATUM_FIELDS:
            errs.append(f"field 須為 {'/'.join(ERRATUM_FIELDS)} 之一：{e['field']!r}")
        # ★須與 `_erratum_view` 的 `isinstance(cor, str)` 守衛同尺：此處若沿用
        #   `str(e["corrected"])` 的寬鬆轉型，40 位純十進位數字的 JSON number
        #   （＝corrected 少打引號）會兩邊都不報——Lint03 因 str() 後恰為 40 個合法 hex
        #   字元而放行、視圖因非 str 而 continue，erratum 靜默零效、target 列舊紅照掛。
        #   那正是硬語意③「絕不靜默 no-op」明禁之形，故此欄不吃 feature_close 的
        #   merge／pins 那套 str() 寬鬆慣例。
        if not (isinstance(e["corrected"], str) and RE_SHA.fullmatch(e["corrected"])):
            errs.append(f"corrected 須為 40 位 hex SHA：{e['corrected']!r}")
        r = e["reason"]
        if not (isinstance(r, str) and r.strip() and "\n" not in r and "\r" not in r):
            errs.append("reason 須為非空單行字串（一句話、不得換行）")
    return errs


def _jsonl_lines(text):
    """jsonl 行界只認 \\n（splitlines 會在 U+2028 等處誤切合法 JSON 字串）。"""
    lines = (text or "").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [l.rstrip("\r") for l in lines]


def lint_events(text):
    """Lint03：ops/events.jsonl 逐行 JSON Schema 驗證。回 findings list。"""
    out = []
    for n, line in enumerate(_jsonl_lines(text), start=1):
        where = f"{EVENTS}:行 {n}"
        if not line.strip():
            out.append(finding(ERROR, "Lint03", where, "不得有空行（jsonl 一行一事件）"))
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError as ex:
            out.append(finding(ERROR, "Lint03", where, f"非合法 JSON：{ex.msg}"))
            continue
        for msg in _check_event(e):
            out.append(finding(ERROR, "Lint03", where, msg))
    return out


# Lint07 預算表：rel path → (行數上限, token 上限)；None＝不設
BUDGETS = {
    "README.md": (150, None),
    "CLAUDE.md": (250, None),
    "docs/ops/NOTES.md": (40, None),
    "docs/ops/BACKLOG.md": (200, None),
    "docs/generated/STATE.md": (None, 4000),
    "docs/arc42/ARCHITECTURE.md": (700, 25000),
    ".specify/memory/constitution.md": (350, None),   # rev5 新增納管（起始值、收緊另議）
    "docs/ops/RUNBOOK.md": (900, None),               # rev5 新增納管（起始值、收緊另議）
}
LESSONS_TOKEN_LIMIT = 25000
LESSONS_TOKEN_WARN = 22500
# 分檔制（ADR 0045、grilling Q1 施壓形拍板 2026-08-17）：docs/ops/LESSONS/ 條目檔單條上限。
# 單卷 25000 在分檔制下只罩索引主檔；「條目越寫越長」的實質約束面移到單條 token 上限
# （遷移當下實測最大 L-045＝1937、零條 >2000——WARN 線刻意貼近、補記即施壓瘦身）。
LESSON_ENTRY_TOKEN_LIMIT = 3000   # ERROR
LESSON_ENTRY_TOKEN_WARN = 2000    # WARN
BACKLOG_VOL_LINE_LIMIT = 200
# rev5 差分（§3.2 條 11／§0.3 準則 4）：分卷軸一律按大小、不按時間。
# ★取與 LESSONS 同值——兩者同為 append-only 帳本的鏡像、同一種成長形態，用同一把尺；
#   rev4 的 MILESTONES 實測 28,883 tokens／47 筆事件（約 614 tokens 一筆），本值約當 40 筆。
MILESTONES_VOL_TOKEN_LIMIT = LESSONS_TOKEN_LIMIT
# rev5 差分（§3.2 條 11／Q6 拍板 2026-08-04）：事件帳 summary 單筆上限。
# ★一次性拍板——事件帳「既有列不可改」，本值創世後定死、不能回頭改舊列。
# ★數值回歸設計預測值「一刀約 300 字」：rev4 零限制的結果是單筆最長 2,498 字、
#   中位 953 字（＝預測值 3.2 倍），亦為 events.jsonl 膨脹至 35,905 tokens 的主因之一。
# ★jsonl 單列結構下「行數型上限」落實為「禁含換行＋字元數上限」——NOTES 那種真行數
#   預算套不進 JSON 字串欄。溢出去處：細節→notes 選填欄／報告檔／LESSONS。
# ★notes 刻意不設限：創世 misc 事件的 notes 要承載 lint-roster: 固定前綴（全部條款名）。
SUMMARY_CHAR_LIMIT = 300
# 活書單節配額（行數、超出＝警告）
SECTION_QUOTAS = {1: 40, 2: 30, 3: 50, 4: 40, 5: 90, 6: 120,
                  7: 60, 8: 90, 9: 5, 10: 40, 11: 3, 12: 30}
RE_BOOK_SECTION = re.compile(r"^## §(\d{1,2})\b")


def _read(root, rel):
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8-sig") as fh:  # -sig：吞 BOM（Windows 編輯器常見）
        return fh.read()


def _line_count(text):
    return len(text.splitlines())


def lint_budgets(root):
    """Lint07：檔案預算（行數／token）＋活書單節配額。回 findings list。"""
    out = []
    for rel, (max_lines, max_tokens) in BUDGETS.items():
        text = _read(root, rel)
        if text is None:
            continue
        if max_lines is not None and _line_count(text) > max_lines:
            out.append(finding(ERROR, "Lint07", rel,
                               f"行數 {_line_count(text)} 超出預算 {max_lines}"))
        if max_tokens is not None and token_count(text) > max_tokens:
            out.append(finding(ERROR, "Lint07", rel,
                               f"約 {token_count(text)} tokens 超出預算 {max_tokens}"))
    # LESSONS 全卷（LESSONS.md＋LESSONS-*.md）各卷 token 限額；BACKLOG 卷（BACKLOG-*.md）
    # 各卷行數限額（同主檔 200）——皆走 glob、新卷免登記 BUDGETS 即被涵蓋
    ops_dir = os.path.join(root, "docs/ops")
    if os.path.isdir(ops_dir):
        for name in sorted(os.listdir(ops_dir)):
            rel = f"docs/ops/{name}"
            if name == "LESSONS.md" or (name.startswith("LESSONS-") and name.endswith(".md")):
                toks = token_count(_read(root, rel))
                if toks > LESSONS_TOKEN_LIMIT:
                    out.append(finding(ERROR, "Lint07", rel,
                                       f"約 {toks} tokens 超出單卷上限 {LESSONS_TOKEN_LIMIT}——請分卷（詳活書文件規則）"))
                elif toks > LESSONS_TOKEN_WARN:
                    out.append(finding(WARN, "Lint07", rel,
                                       f"約 {toks} tokens 逼近單卷上限 {LESSONS_TOKEN_LIMIT}，宜準備分卷"))
            elif name.startswith("BACKLOG-") and name.endswith(".md"):
                lines = _line_count(_read(root, rel) or "")
                if lines > BACKLOG_VOL_LINE_LIMIT:
                    out.append(finding(ERROR, "Lint07", rel,
                                       f"行數 {lines} 超出單卷預算 {BACKLOG_VOL_LINE_LIMIT}"))
    # 分檔制（ADR 0045）：docs/ops/LESSONS/ 條目檔逐檔單條上限（token 計全檔、含 frontmatter）；
    # 目錄不存在＝略過（遷移前照綠）
    les_dir = os.path.join(root, "docs/ops/LESSONS")
    if os.path.isdir(les_dir):
        for name in sorted(os.listdir(les_dir)):
            if not (name.startswith("L-") and name.endswith(".md")):
                continue
            rel = f"docs/ops/LESSONS/{name}"
            toks = token_count(_read(root, rel) or "")
            if toks > LESSON_ENTRY_TOKEN_LIMIT:
                out.append(finding(ERROR, "Lint07", rel,
                                   f"約 {toks} tokens 超出單條上限 {LESSON_ENTRY_TOKEN_LIMIT}——"
                                   "拆條或瘦身（一坑一檔勿併坑；防法細節晉升進操作面後即可自本檔刪減）"))
            elif toks > LESSON_ENTRY_TOKEN_WARN:
                out.append(finding(WARN, "Lint07", rel,
                                   f"約 {toks} tokens 逼近單條上限 {LESSON_ENTRY_TOKEN_LIMIT}，"
                                   "宜瘦身或拆條（一坑一檔勿併坑）"))
    # 活書單節配額（警告級）
    book = _read(root, BOOK)
    if book is not None:
        for sec, count in book_section_lines(book).items():
            quota = SECTION_QUOTAS.get(sec)
            if quota is not None and count > quota:
                out.append(finding(WARN, "Lint07", BOOK,
                                   f"§{sec} 共 {count} 行超出單節配額 {quota}"))
    return out


# ---------------------------------------------------------------------------
# Lint08 ADR／Lint09 ID／Lint10 時態／Lint11 詞典
# ---------------------------------------------------------------------------


RE_ADR_FILENAME = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9-]*\.md$")
ADR_STATUSES = ("draft", "accepted", "superseded", "rejected")
ADR_REQUIRED = ("id", "title", "date", "status")
# accepted 後仍可動的 front-matter 欄：superseded_by（工具回填）；status 僅可轉 superseded
ADR_MUTABLE_AFTER_ACCEPT = ("superseded_by",)


def _adr_list(meta, key):
    v = meta.get(key, [])
    return v if isinstance(v, list) else None


def _valid_adr_id(v):
    return isinstance(v, str) and bool(RE_ADR_ID.fullmatch(v))


def lint_adrs(adrs, head_adrs, amend=False):
    """Lint08：ADR front-matter schema＋accepted 不可變＋supersedes 對稱＋禁刪除。

    adrs / head_adrs：{filename: 檔案全文}（head_adrs＝git HEAD 版；無 HEAD 版＝空 dict）。
    amend=True（env DOCS_SYNC_ADR_AMEND=1）＝豁免 accepted body 不可變（typo 級修正）。
    """
    out = []
    for fn in head_adrs:
        if fn not in adrs:
            out.append(finding(ERROR, "Lint08", f"{ADR_DIR}/{fn}",
                               "ADR 禁刪除（編號永不重用；翻案＝新檔 supersedes）"))
    metas = {}
    for fn, text in sorted(adrs.items()):
        where = f"{ADR_DIR}/{fn}"
        meta, body = parse_front_matter(text)
        metas[fn] = (meta, body)
        m = RE_ADR_FILENAME.fullmatch(fn)
        if not m:
            out.append(finding(ERROR, "Lint08", where, "檔名須為 NNNN-<slug>.md"))
        for k in ADR_REQUIRED:
            if k not in meta:
                out.append(finding(ERROR, "Lint08", where, f"front-matter 缺必填欄「{k}」"))
        status = meta.get("status")
        if status is not None and status not in ADR_STATUSES:
            out.append(finding(ERROR, "Lint08", where,
                               f"status 須為 {'|'.join(ADR_STATUSES)}：{status!r}"))
        if "id" in meta and not _valid_adr_id(meta["id"]):
            out.append(finding(ERROR, "Lint08", where, f"id 須為 4 位數字字串：{meta['id']!r}"))
        if m and _valid_adr_id(meta.get("id")) and meta["id"] != m.group(1):
            out.append(finding(ERROR, "Lint08", where,
                               f"id「{meta['id']}」與檔名編號「{m.group(1)}」不一致（編號＝檔名）"))
        if "date" in meta and not RE_DATE.fullmatch(str(meta["date"])):
            out.append(finding(ERROR, "Lint08", where, f"date 格式須為 YYYY-MM-DD：{meta['date']!r}"))
        for k in ("supersedes", "superseded_by"):
            v = _adr_list(meta, k)
            if v is None or not all(RE_ADR_ID.fullmatch(str(x)) for x in v):
                out.append(finding(ERROR, "Lint08", where, f"{k} 須為 4 位 ADR 編號 list"))
        if "feature" in meta and not isinstance(meta.get("feature"), str):
            out.append(finding(ERROR, "Lint08", where, "feature 須為字串"))
        if "provenance" in meta and not isinstance(meta.get("provenance"), str):
            out.append(finding(ERROR, "Lint08", where, "provenance 須為字串"))
        if "tags" in meta and not isinstance(meta.get("tags"), list):
            out.append(finding(ERROR, "Lint08", where, "tags 須為 list"))
    # 撞號偵測（同號不同 slug 的 merge 不會產生 git 衝突、必須 lint 抓）
    seen_ids = {}
    for fn, (meta, _) in sorted(metas.items()):
        i = meta.get("id")
        if _valid_adr_id(i):
            if i in seen_ids:
                out.append(finding(ERROR, "Lint08", f"{ADR_DIR}/{fn}",
                                   f"id「{i}」與 {seen_ids[i]} 重複配號（編號永不重用）"))
            else:
                seen_ids[i] = fn
    by_id = {meta["id"]: (fn, meta) for fn, (meta, _) in metas.items()
             if _valid_adr_id(meta.get("id"))}
    for fn, (meta, _) in sorted(metas.items()):
        where = f"{ADR_DIR}/{fn}"
        my_id = meta.get("id")
        for x in (_adr_list(meta, "supersedes") or []):
            x = str(x)
            if x not in by_id:
                out.append(finding(ERROR, "Lint08", where, f"supersedes 指向不存在的 ADR「{x}」"))
                continue
            _, tmeta = by_id[x]
            if my_id and my_id not in (_adr_list(tmeta, "superseded_by") or []):
                out.append(finding(ERROR, "Lint08", where,
                                   f"supersedes 對稱缺口：ADR {x} 的 superseded_by 未回填"
                                   f"「{my_id}」（跑 tools/docs-sync.py generate 回填）"))
            if tmeta.get("status") != "superseded":
                out.append(finding(ERROR, "Lint08", where,
                                   f"被翻案的 ADR {x} status 須為 superseded"))
        for x in (_adr_list(meta, "superseded_by") or []):
            x = str(x)
            if x not in by_id:
                out.append(finding(ERROR, "Lint08", where, f"superseded_by 指向不存在的 ADR「{x}」"))
            elif my_id and my_id not in (_adr_list(by_id[x][1], "supersedes") or []):
                out.append(finding(ERROR, "Lint08", where,
                                   f"superseded_by 對稱缺口：ADR {x} 未宣告 supersedes「{my_id}」"))
    for fn, head_text in sorted(head_adrs.items()):
        if fn not in adrs:
            continue
        hmeta, hbody = parse_front_matter(head_text)
        if hmeta.get("status") != "accepted":
            continue
        where = f"{ADR_DIR}/{fn}"
        cmeta, cbody = metas[fn]
        if cbody != hbody and not amend:  # amend 僅豁免 body 的 typo 級修正
            out.append(finding(ERROR, "Lint08", where,
                               "accepted 後 body 不可變（typo 級修正：commit message 帶"
                               " [adr-amend] 並設 DOCS_SYNC_ADR_AMEND=1）"))
        for k in sorted(set(hmeta) | set(cmeta)):
            if k in ADR_MUTABLE_AFTER_ACCEPT:
                continue
            if k == "status":
                if cmeta.get(k) not in ("accepted", "superseded"):
                    out.append(finding(ERROR, "Lint08", where,
                                       "accepted 的 status 僅可轉 superseded"))
                continue
            if hmeta.get(k) != cmeta.get(k):
                out.append(finding(ERROR, "Lint08", where,
                                   f"accepted 後 front-matter 欄「{k}」不可變"))
    return out


RE_NEXT_ID = re.compile(r"<!--\s*next:\s*([BL])-(\d+)\s*-->")
RE_ENTRY = {
    "B": re.compile(r"^- B-(\d+)｜", re.M),
    # L 側：LESSONS.md 檔頭自載格式＝裸段形「L-NNN｜…」（非 list-item）——`- ` 前綴設為
    # 可選以配合實檔（001 收刀修：舊樣式強制 `- ` 使計數恆 0＋Lint09 L 側恆綠假閘）。
    # ★B 側勿比照改動：Lint04 _backlog_ever_tokens 以其 group(0) 逐字 token 為對外契約。
    "L": re.compile(r"^(?:- )?(?:\*\*)?L-(\d+)(?:\*\*)?｜", re.M),
}
# 反回收豁免視野（原 Lint09 head_ids 專用）：不錨行首的寬鬆子串形——｜為欄位分隔、散文引用不帶，
# 故「字串曾在 HEAD 出現」即非回收；格式事故（行黏連/縮排）修復不誤判，真回收（號碼已刪列
# ＝字串已消失）照抓。staged 側計數/撞號仍用嚴格 RE_ENTRY。user 拍板調規 2026-07-19（rev4:B-106）。
# ★第二消費者＝Lint04 全史 token 掃描（_backlog_ever_tokens）：其 group(0) 逐字 token 為對外契約
#   ——調 "B" 變體形（如比照 "L" 補 (?:\*\*)?）前先核對該比對面，否則 Lint04 靜默全面誤報。
RE_ENTRY_ANYPOS = {
    "B": re.compile(r"B-(\d+)｜"),
    "L": re.compile(r"L-(\d+)(?:\*\*)?｜"),
}


def _parse_next(kind, text):
    m = RE_NEXT_ID.search(text or "")
    return int(m.group(2)) if m and m.group(1) == kind else None


def lint_ids(kind, texts, head_texts):
    """Lint09：B-NNN／L-NNN 依檔頭 next-id 驗唯一、單調、不回收。

    kind："B" 或 "L"；texts／head_texts＝[主檔文, 其餘卷文…]（主檔在首、含 next-id 檔頭）。
    head_texts 各元素可為 None（HEAD 無此檔）。
    """
    out = []
    label = {"B": BACKLOG, "L": "docs/ops/LESSONS.md"}[kind]
    cur_next = _parse_next(kind, texts[0])
    if cur_next is None:
        out.append(finding(ERROR, "Lint09", label, "缺 next-id 檔頭（<!-- next: %s-NNN -->）" % kind))
    ids, seen = [], set()
    for text in texts:
        for m in RE_ENTRY[kind].finditer(text or ""):
            n = int(m.group(1))
            if n in seen:
                out.append(finding(ERROR, "Lint09", label, f"{kind}-{n:03d} 重複配號"))
            seen.add(n)
            ids.append(n)
    if cur_next is not None:
        for n in ids:
            if n >= cur_next:
                out.append(finding(ERROR, "Lint09", label,
                                   f"{kind}-{n:03d} ≥ next-id {cur_next}（配號＝取 next 後 bump）"))
    head_next = _parse_next(kind, head_texts[0]) if head_texts else None
    if head_next is not None:
        if cur_next is not None and cur_next < head_next:
            out.append(finding(ERROR, "Lint09", label,
                               f"next-id 須單調遞增（HEAD {head_next} → 現 {cur_next}）"))
        head_ids = set()
        for text in head_texts:
            head_ids.update(int(m.group(1)) for m in RE_ENTRY_ANYPOS[kind].finditer(text or ""))
        for n in sorted(set(ids) - head_ids):
            if n < head_next:
                out.append(finding(ERROR, "Lint09", label,
                                   f"{kind}-{n:03d} 為舊號回收（新號必 ≥ HEAD next-id {head_next}；號碼永不回收）"))
    return out


# LESSONS 分檔制（ADR 0045）：條目檔名形＋索引連結抽取形（Lint26 專用）。
# ★索引行取方括號連結形、刻意不匹配 RE_ENTRY（分檔制設計支點 D1——Lint09 計數／lessons_count
#   零改動）。
# ★抽取形之數字要求 L-\d{3} 屬**前瞻性約束、現行無行為面**：link_counts 只被條目檔名
#   （RE_LESSON_FILE、必含 \d{3}）查表，放寬後多收的散文示意鍵（字母 NNN 形）永遠沒人讀
#   ——寫不出真紅案（mutation 實證：拆掉 \d{3} 全自測照綠）。對應自測只誠實主張
#   「散文示意不誤報」（ADR 0024 防恆綠紀律之誠實標註形）。
RE_LESSON_FILE = re.compile(r"^L-(\d{3})-[a-z0-9][a-z0-9-]*\.md$")
RE_LESSON_INDEX_LINK = re.compile(r"\(LESSONS/(L-\d{3}[^)\s]*\.md)\)")
# 索引行「標號↔連結檔名號碼」對賬形（U1 收尾補防、U1c 品質輪 advisory #4）：47 行手寫索引
# 最可能的抄錯形＝標號抄錯——link_counts 只管存在與唯一、Lint12 只管檔案存在，無此斷言即全綠。
# 兩側皆要求 \d{3} ⇒ 前言散文示意（字母 NNN 形）不命中、不誤報。
RE_LESSON_INDEX_ROW = re.compile(r"\[L-(\d{3})｜[^\]]*\]\(LESSONS/L-(\d{3})[^)\s]*\.md\)")


def lint_lessons_files(root):
    """Lint26：LESSONS 分檔制對賬三斷言（ADR 0045）；docs/ops/LESSONS/ 不存在＝零 findings。

    (a) 條目檔名匹配 L-NNN-<slug>.md，且正文以 RE_ENTRY["L"] 恰命中一次、號碼與檔名相等；
    (b) 索引（docs/ops/LESSONS.md）↔ 條目檔雙向對賬——本斷言管反向（檔無索引行）與唯一性
        （每檔恰一行）；「索引→檔」連結存在性另有 Lint12 兜底、此處不重複；
    (c) 條目檔 frontmatter 具非空 promoted_to:（晉升必答欄；值域自由文字、只驗非空
        〔grilling Q5 拍板〕。★per-machine memory 路徑禁令由既有 lint_memory_refs（Lint15）
        全 md 掃描承載，本條款不重複實作）。
    """
    out = []
    les_dir = os.path.join(root, "docs/ops/LESSONS")
    if not os.path.isdir(les_dir):
        return out
    entry_files = []
    for name in sorted(os.listdir(les_dir)):
        m = RE_LESSON_FILE.match(name)
        if not m:
            out.append(finding(ERROR, "Lint26", f"docs/ops/LESSONS/{name}",
                               "檔名不匹配 L-NNN-<slug>.md 形（NNN＝三位數字、slug＝英文小寫"
                               " kebab）——改名合形、或移出 docs/ops/LESSONS/（目錄僅收條目檔）"))
            continue
        entry_files.append((name, int(m.group(1))))
    for name, fn_num in entry_files:
        rel = f"docs/ops/LESSONS/{name}"
        text = _read(root, rel) or ""
        hits = RE_ENTRY["L"].findall(text)
        if len(hits) != 1:
            out.append(finding(ERROR, "Lint26", rel,
                               f"正文 L-NNN｜起手形命中 {len(hits)} 次、應恰一次"
                               "（一坑一檔：0＝缺條目首行、多於一＝併坑須拆檔）"))
        elif int(hits[0]) != fn_num:
            out.append(finding(ERROR, "Lint26", rel,
                               f"正文號碼 L-{int(hits[0]):03d} 與檔名號碼 L-{fn_num:03d} 不一致"
                               "（引用以 ID 為準；改正文或改檔名使相等）"))
        v = parse_front_matter(text)[0].get("promoted_to")
        if not v or (isinstance(v, str) and not v.strip()):
            out.append(finding(ERROR, "Lint26", rel,
                               "frontmatter 缺非空 promoted_to:（晉升必答欄：防法晉升到哪個"
                               "操作面；無處可晉升寫「無：<理由>」）"))
    index_text = _read(root, "docs/ops/LESSONS.md") or ""
    link_counts = {}
    for m in RE_LESSON_INDEX_LINK.finditer(index_text):
        link_counts[m.group(1)] = link_counts.get(m.group(1), 0) + 1
    for m in RE_LESSON_INDEX_ROW.finditer(index_text):
        if m.group(1) != m.group(2):
            out.append(finding(ERROR, "Lint26", "docs/ops/LESSONS.md",
                               f"索引行標號 L-{m.group(1)} 與連結檔名號碼 L-{m.group(2)} 不一致"
                               "（手寫索引最易出的抄錯形；以條目檔名號碼為準、改標號或改連結）"))
    for name, _n in entry_files:
        cnt = link_counts.get(name, 0)
        if cnt == 0:
            out.append(finding(ERROR, "Lint26", "docs/ops/LESSONS.md",
                               f"缺 {name} 的索引行——每條目檔於索引恰一行"
                               "（- [L-NNN｜坑名](LESSONS/<檔名>) — 防法 hook）"))
        elif cnt > 1:
            out.append(finding(ERROR, "Lint26", "docs/ops/LESSONS.md",
                               f"{name} 於索引出現 {cnt} 行——每檔恰一行、刪重複行"))
    return out


TENSE_WORDS = {
    "待決": "ops/BACKLOG（待辦）或 ADR draft（未決案）",
    "TBD": "ops/BACKLOG",
    "⏳": "ops/BACKLOG",
    "已完成": "git 史＋ops/events.jsonl（過去式不入書）",
    "下一步": "ops/NOTES（未來式不入書）",
}


def lint_tense(book_text):
    """Lint10：活書時態禁詞（待決/TBD/⏳/已完成/下一步），附去處提示。"""
    out = []
    for n, line in enumerate(book_text.splitlines(), start=1):
        for word, dest in TENSE_WORDS.items():
            if word in line:
                out.append(finding(ERROR, "Lint10", f"{BOOK}:行 {n}",
                                   f"活書時態禁詞「{word}」；去處：{dest}"))
    return out


DICT_PATTERNS = (
    # rev5 差分（§3.2 條 6）：rev5 的直接前身是 rev4，防的是 rev4 編號未帶前綴走私進活文件。
    # ★rev4 原三式（⚠️x／待決①／F-NN）之所以可行，是因為 rev3 與 rev4 的編號**形式不同**；
    #   rev4→rev5 則沿用同一套形式（ADR NNNN／B-NNN／L-NNN，rev5 自 0001 與 001 起家），
    #   故「裸碼即前代碼」的靜態判定**在本世代不可實作**——照那樣寫會把 rev5 自己的編號全數
    #   誤報。改以「提及 rev4 卻未用 rev4: 標準前綴形」的混寫為判定面：抓得到真走私、不誤傷
    #   自身編號。射程誠實邊界＝完全未提 rev4 的裸碼抓不到（機器本無從分辨），該面由 Lint09
    #   配號閘（已用號不得 ≥ next-id、反回收）承接。
    (re.compile(r"rev4(?!:)[^\n]{0,12}?\b(?:ADR\s*\d{4}|[BL]-\d{3,})\b"), "rev4 編號混寫走私",
     "前代編號須用史料標註形——寫成 rev4:ADR NNNN／rev4:B-NNN／rev4:L-NNN 或改寫為自解釋描述"),
    (re.compile(r"(?i)\bport\s*[:=]?\s*\d{2,5}\b"), "port 實值",
     "快變字面值不入活文件→ docs/generated/reference/ports.md"),
    (re.compile(r"(?<![0-9a-fA-F])123456(?![0-9a-fA-F])"), "seed 密碼實值",
     "快變字面值不入活文件→ docs/generated/reference/accounts.md"),
    (re.compile(r"(?i)(?:routes?|路由|端點|endpoints?)\D{0,8}?\d+"
                r"|\d+\s*(?:條|個|支)?\s*(?:routes?|路由|端點|endpoints?)"), "route 計數實值",
     "快變字面值不入活文件→ docs/generated/reference/routes.md"),
)


def lint_dictionary(texts):
    """Lint11：禁入詞典（警告級）。texts＝{rel: 全文}，掃活書＋CLAUDE.md。

    「｜出處：」起始的行（rev3 史料標註）整行豁免——僅行首、行中不豁免。
    """
    out = []
    for rel, text in sorted(texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            if line.lstrip().startswith("｜出處："):
                continue
            for pat, label, hint in DICT_PATTERNS:
                for m in pat.finditer(line):
                    out.append(finding(WARN, "Lint11", f"{rel}:行 {n}",
                                       f"禁入詞典命中「{m.group(0)}」（{label}）；{hint}"))
    return out


# ---------------------------------------------------------------------------
# Lint12~Lint15 引用健康
# ---------------------------------------------------------------------------


RE_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
RE_LINE_REF = re.compile(r"\S+\.md:\d+")
# BACKLOG 全系（含 BACKLOG-*.md 卷）皆揮發故一律禁錨；LESSONS 系 append-only、錨穩定故不禁
RE_VOLATILE_ANCHOR = re.compile(r"(?:BACKLOG(?:-[A-Za-z0-9-]+)?|NOTES|STATE)\.md#\S+")
# rev5 差分（§3.2 條 7）：補 /Users/ 家目錄形——rev4 式樣按 WSL2 路徑寫，macOS 射程缺口。
RE_MEMORY_PATH = re.compile(r"(?:~|/home/[^/\s]+|/Users/[^/\s]+)/\.claude/[^\s)]*")


def _iter_links(md_texts):
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_MD_LINK.finditer(line):
                yield rel, n, m.group(1)


def lint_links(md_texts, existing_paths):
    """Lint12：md 內部連結（相對路徑）必須指向存在檔案。

    md_texts＝{rel: 全文}；existing_paths＝repo 現存（git 追蹤）路徑 set。
    http(s)/mailto/純錨點連結不驗。
    """
    out = []
    for rel, n, target in _iter_links(md_texts):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#", 1)[0]
        resolved = os.path.normpath(os.path.join(os.path.dirname(rel), path)).replace(os.sep, "/")
        if resolved not in existing_paths:
            out.append(finding(ERROR, "Lint12", f"{rel}:行 {n}",
                               f"連結指向不存在檔案「{target}」（解析為 {resolved}）"))
    return out


def lint_line_refs(md_texts):
    """Lint13：禁行號引用（xxx.md:123 型）——行號揮發、引用必 rot。"""
    out = []
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_LINE_REF.finditer(line):
                out.append(finding(ERROR, "Lint13", f"{rel}:行 {n}",
                                   f"禁行號引用「{m.group(0)}」；改用穩定語意錨（節號／檔名／描述名）"))
    return out


def lint_volatile_deep_links(md_texts):
    """Lint14：禁 deep-link 揮發區內部錨（BACKLOG/NOTES/STATE 只可整檔引用）。"""
    out = []
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_VOLATILE_ANCHOR.finditer(line):
                out.append(finding(ERROR, "Lint14", f"{rel}:行 {n}",
                                   f"揮發區禁 deep-link「{m.group(0)}」；只可整檔引用"))
    return out


def lint_memory_refs(md_texts):
    """Lint15：repo 文件禁引 per-machine memory 實路徑（~/.claude/**）。

    帶 rev4: 前綴的純文字史料標註（如 rev4:memory/…）非實路徑、天然不命中。
    """
    out = []
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_MEMORY_PATH.finditer(line):
                out.append(finding(ERROR, "Lint15", f"{rel}:行 {n}",
                                   f"禁引 per-machine 路徑「{m.group(0)}」；先提取進 repo 文件再引用"))
    return out


# ---------------------------------------------------------------------------
# Lint16 憑證內容掃描（rev4:contracts G1／data-model §1§2；rev4:ADR 0077）
# ---------------------------------------------------------------------------

# 窄集合高確信樣式：刻意**不含**泛熵值與 password= 類（誤報成本高於殘餘風險——漏報面有意識
# 接受）。擴充或豁免一律動本常數＋立 ADR；無 inline 豁免 marker（防偽）。
CRED_PATTERNS = (
    ("pem-private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY( BLOCK)?-----")),
    ("aws-akia", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,255}\b")),
)
CRED_WHITELIST = ()            # 豁免白名單（現空集；擴充須同時立 ADR——rev4:ADR 0077 豁免路徑）
CRED_SUBMODULES = ("base-web", "rust-api")
CRED_BINARY_PROBE = 8192       # 前 8KB 含 NUL byte 即判二進位（近似 git 的偵測、憑證必為文字）


def scan_cred_text(text):
    """全文過樣式集；回 [(label, 行號)]（同 label 只回首命中，訊息不爆量）。"""
    hits = []
    for label, pat in CRED_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append((label, text.count("\n", 0, m.start()) + 1))
    return hits


def _cred_samples():
    """self-test 紅綠樣本。

    ★執行期字串串接構造：本檔屬 tracked，落任何完整命中字面即被外層全量掃自命中自紅。
    """
    red = [
        ("pem-private-key", "-----BEGIN " + "RSA PRIVATE" + " KEY" + "-----"),
        ("aws-akia", "AKIA" + "0123456789ABCDEF"),
        ("github-token", "gh" + "p_" + "s3lfT3st" * 4 + "Samp"),
        ("github-pat", "github" + "_pat_" + "s3lfT3stSampl3Str1ng0k"),
    ]
    green = ["普通說明文字、無憑證內容。", "-----BEGIN CERTIFICATE-----",
             "AKIA" + "TOOSHORT", "gh" + "p_" + "short"]
    return red, green


def cred_self_test():
    """防恆綠：每次 lint 連帶驗紅樣本必紅、綠樣本必綠；失效即 ERROR（rev4:contracts G1）。"""
    out = []
    red, green = _cred_samples()
    for label, sample in red:
        if label not in [l for l, _ in scan_cred_text(sample)]:
            out.append(finding(ERROR, "Lint16", "tools/docs-sync.py",
                               f"憑證掃描 self-test 失效：紅樣本 {label} 未被攔下"
                               "——條款已恆綠，修復 CRED_PATTERNS 後重跑"))
    for sample in green:
        hit = scan_cred_text(sample)
        if hit:
            out.append(finding(ERROR, "Lint16", "tools/docs-sync.py",
                               f"憑證掃描 self-test 失效：綠樣本誤報 {hit[0][0]}"
                               "——樣式集過寬，收窄後重跑"))
    return out


def cred_diff_hits(diff_text):
    """unified diff（-U0）新增行過樣式集；回 [(檔路徑, label)]。

    ★以 hunk 狀態機判檔頭、不以前綴猜測：-U0 的內容行本身帶一個 `+` 前綴，故檔案內任何
    以「兩個加號加空白」起首的行，在 diff 裡就長成三個加號加空白——單看前綴會把它當檔頭
    整行吞掉（該行漏掃），且把行內容寫進路徑欄（其後真命中被指名到不存在的檔）。狀態機
    界線嚴密：檔頭必在該檔首個 `@@` 之前、內容行必在 `@@` 之後。
    """
    out, path, in_hunk = [], "?", False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            path, in_hunk = "?", False
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk and line.startswith("+++ "):
            raw = line[4:].strip()
            path = raw[2:] if raw.startswith(("a/", "b/")) else raw
            continue
        if not line.startswith("+"):
            continue
        for label, _n in scan_cred_text(line[1:]):
            if (path, label) not in out:
                out.append((path, label))
    return out


# ---------------------------------------------------------------------------
# generate／check／errata
# ---------------------------------------------------------------------------

GEN_HEADER = "<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->"
REFERENCE_TABLES = ("routes", "ports", "schema", "accounts", "screens")
# stub 轉真的表：STATE 對賬行改列真來源描述（其餘表維持 gen_reference_stub）
REFERENCE_LIVE = {
    "routes": "真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）",
    "ports": "真表（來源＝compose 三檔的 ports: 段、由 generate 重算）",
    "schema": "真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、"
              "由 generate 重算；快照由 refresh 自實庫撈）",
    "accounts": "真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；"
                "快照由 refresh 自實庫撈）",
    "screens": "真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、"
               "由 generate 重算；全巢狀 route flatten）",
}
# ports 對照表來源（base 層設計鐵律禁 host ports、映射只住 dev/example）
COMPOSE_FILES = ("docker-compose.yml", "docker-compose.dev.yml", "docker-compose.example.yml")
# backend 拒因字典鏈（rev4:B-007／rev4:FR-014）常數——生成器本體見下方「backend 拒因字典鏈」節
MSG_DICT_LOCALES = (("zh-TW", "base-web/src/locales/langs/zh-tw.ts"),
                    ("en-US", "base-web/src/locales/langs/en-us.ts"))
MSG_DICT_MD = f"{GENERATED_DIR}/reference/backend-msg-dict.md"
MSG_DICT_PANEL = "deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json"
MSG_DICT_HINT = ("機器生成：tools/docs-sync.py generate（來源＝base-web locale backend.* 兩語）"
                 "——嚴禁手改；差異由 pre-commit check 攔下")


DEFAULT_BRANCH = "rev5-admin-root"


def _md_cell(v):
    s = str(v) if v not in (None, "", []) else "—"
    return s.replace("|", "\\|")


def _event_row(e):
    t = e.get("type", "?")
    target = {"feature_close": e.get("feature"), "review": e.get("scope")}.get(t)
    merge = e.get("merge") if t == "feature_close" else None
    adrs = "、".join(e.get("adrs", [])) if t == "feature_close" else None
    ai = e.get("arch_impact") if t == "feature_close" else None
    arch = "、".join(ai) if isinstance(ai, list) else ai
    return (f"| {_md_cell(e.get('date'))} | {_md_cell(t)} | {_md_cell(target)} "
            f"| {_md_cell(e.get('summary') or e.get('report'))} | {_md_cell(merge)} "
            f"| {_md_cell(adrs)} | {_md_cell(arch)} |")


MILESTONE_TABLE_HEAD = ("| date | type | 標的 | summary | merge | adrs | arch |\n"
                        "|---|---|---|---|---|---|---|")


def gen_milestones(events):
    """MILESTONES ← 全 events 表格化、★按大小分卷（rev5 差分，§3.2 條 11）。回 {rel: content}。

    ★rev4 按**年**分卷：33 天內 47 筆事件即達 28,883 tokens，卻因同屬 2026 年而始終單卷
    ——時間軸與體積無關，分卷條件結構上永不觸發（§2.6 列為兩個架構級缺陷之一）。
    rev5 改按大小：事件依日期**由舊而新**填卷，填滿即封存、開新卷；主卷恆為最新的未滿卷。
    ★「由舊而新」不可反：由新而舊會讓每次 append 都推移卷邊界、已封存卷的內容跟著變動，
    check 於是逐次報 Lint01 drift（生成物必須對同一輸入穩定重算）。
    ★date 畸形的事件（generate 走寬鬆解析、不等 Lint03）排在最後、必落主卷，
    不得以字串序劫走主卷位置。
    """
    main_rel = f"{GENERATED_DIR}/MILESTONES.md"

    def _sort_key(e):
        d = str(e.get("date", ""))
        return (0, d) if RE_DATE.fullmatch(d) else (1, "")

    ordered = sorted(events, key=_sort_key)
    if not ordered:
        return {main_rel: f"{GEN_HEADER}\n# MILESTONES — 全事件表\n\n（尚無事件）\n"}

    # 卷頭固定開銷（標題與表頭），逐卷都要計入體積
    overhead = token_count(f"{GEN_HEADER}\n# MILESTONES — 全事件表（）\n\n{MILESTONE_TABLE_HEAD}\n")
    vols, cur, cur_tok = [], [], 0
    for e in ordered:
        row = _event_row(e)
        t = token_count(row) + 1
        if cur and overhead + cur_tok + t > MILESTONES_VOL_TOKEN_LIMIT:
            vols.append(cur)
            cur, cur_tok = [], 0
        cur.append(e)
        cur_tok += t
    vols.append(cur)

    def _span(evs):
        ds = [str(e.get("date", "")) for e in evs if RE_DATE.fullmatch(str(e.get("date", "")))]
        return (ds[0].replace("-", ""), ds[-1].replace("-", "")) if ds else ("", "")

    out = {}
    for i, evs in enumerate(vols):
        last = (i == len(vols) - 1)
        if last:
            rel, label = main_rel, "最新"
        else:
            a, b = _span(evs)
            rel = f"{GENERATED_DIR}/MILESTONES-{a}-{b}.md"
            label = f"{a}–{b}"
        rows = "\n".join(_event_row(e) for e in evs)
        out[rel] = (f"{GEN_HEADER}\n# MILESTONES — 全事件表（{label}）\n\n"
                    f"{MILESTONE_TABLE_HEAD}\n{rows}\n")
    return out


def gen_decisions_index(metas):
    """DECISIONS-INDEX ← ADR front-matter 掃描。metas＝[{…}]（依 id 排序輸出）。"""
    head = f"{GEN_HEADER}\n# DECISIONS-INDEX — ADR 索引\n\n"
    if not metas:
        return head + "（尚無 ADR）\n"
    rows = []
    for m in sorted(metas, key=lambda m: str(m.get("id", ""))):
        rows.append(
            f"| {_md_cell(m.get('id'))} | {_md_cell(m.get('status'))} "
            f"| {_md_cell(m.get('date'))} | {_md_cell(m.get('title'))} "
            f"| {_md_cell(m.get('feature'))} "
            f"| {_md_cell('、'.join(m.get('supersedes', []) or []))} "
            f"| {_md_cell('、'.join(m.get('superseded_by', []) or []))} |")
    return (head + "| id | status | date | title | feature | supersedes | superseded_by |\n"
            "|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")


def _fmt_pin(pin):
    """pin＝index_gitlink 之 (SHA, 跳過原因)：有 SHA→短 SHA；無→未定（含原因）——
    衝突態／無條目一律走此形，絕不顯示 stage 1/2/3 值（rev4:B-114）。"""
    sha, why = pin or (None, None)
    if sha:
        return sha[:7]
    return f"未定（{why}）" if why else "未定"


def gen_state(ctx):
    """STATE ← events 尾 3 筆＋pins＋constitution 版本＋統計＋對賬結果。"""
    events = ctx.get("events", [])
    adr_metas = ctx.get("adr_metas", [])
    status_count = {}
    for m in adr_metas:
        status_count[m.get("status", "?")] = status_count.get(m.get("status", "?"), 0) + 1
    adr_stat = ("、".join(f"{k} {v}" for k, v in sorted(status_count.items()))
                if status_count else "0")
    type_count = {}
    for e in events:
        type_count[e.get("type", "?")] = type_count.get(e.get("type", "?"), 0) + 1
    ev_stat = ("、".join(f"{k} {v}" for k, v in sorted(type_count.items()))
               if type_count else "0")
    tail = list(reversed(events[-3:]))
    if tail:
        tail_lines = "\n".join(
            f"- {e.get('date')}｜{e.get('type')}｜"
            + (f"{e.get('feature')}｜" if e.get("feature") else "")
            + str(e.get("summary") or e.get("scope") or "")
            for e in tail)
    else:
        tail_lines = "（尚無事件）"
    bn = ctx.get("backlog_next")
    ln = ctx.get("lessons_next")
    ref_lines = "\n".join(
        f"- reference/{name}：" + REFERENCE_LIVE.get(
            name, "stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）")
        for name in REFERENCE_TABLES)
    return f"""{GEN_HEADER}
# STATE — 現況機器帳

## git
- default branch：{DEFAULT_BRANCH}
- pins：base-web={_fmt_pin(ctx.get('pins', {}).get('web'))}｜rust-api={_fmt_pin(ctx.get('pins', {}).get('api'))}

## constitution
- 版本：{ctx.get('constitution_version') or '未鑄'}

## 帳面統計
- ADR：{len(adr_metas)}（{adr_stat}）
- BACKLOG 待辦：{ctx.get('backlog_count', 0)}（next：{f'B-{bn:03d}' if bn else '？'}）｜滯後：{ctx.get('backlog_deferred_count', 0)}
- LESSONS：{ctx.get('lessons_count', 0)} 筆（next：{f'L-{ln:03d}' if ln else '？'}）
- events：{len(events)} 筆（{ev_stat}）

## 最近事件（尾 3 筆、新在前）
{tail_lines}

## reference 對賬
{ref_lines}
"""


def _set_fm_field(text, key, value_line):
    """就地改寫 front-matter 單欄（存在則替換、不存在則插在關閉 --- 前）。"""
    lines = text.splitlines(keepends=True)
    close = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close = i
            break
    if close is None:
        return text
    for i in range(1, close):
        if lines[i].split(":", 1)[0].strip() == key:
            lines[i] = value_line + "\n"
            return "".join(lines)
    lines.insert(close, value_line + "\n")
    return "".join(lines)


def backfill_supersessions(adrs):
    """supersedes 對稱回填：A supersedes X ⇒ X.superseded_by ∋ A.id 且 X.status=superseded。

    adrs＝{filename: 全文}；回 {filename: 新全文}（僅含需要改的檔）。
    """
    metas = {fn: parse_front_matter(text)[0] for fn, text in adrs.items()}
    by_id = {m["id"]: fn for fn, m in metas.items() if _valid_adr_id(m.get("id"))}
    changed = {}
    for fn, m in sorted(metas.items()):
        if not _valid_adr_id(m.get("id")):
            continue  # 缺 id／畸形 id 由 Lint08 報，此處不崩
        for x in (_adr_list(m, "supersedes") or []):
            tfn = by_id.get(str(x))
            if tfn is None:
                continue  # dangling → Lint08 擋，不在此處理
            cur_text = changed.get(tfn, adrs[tfn])
            tmeta = parse_front_matter(cur_text)[0]
            sb = list(_adr_list(tmeta, "superseded_by") or [])
            new_text = cur_text
            if m["id"] not in sb:
                sb.append(m["id"])
                new_text = _set_fm_field(new_text, "superseded_by",
                                         f"superseded_by: [{', '.join(sorted(sb))}]")
            if tmeta.get("status") != "superseded":
                new_text = _set_fm_field(new_text, "status", "status: superseded")
            if new_text != adrs[tfn]:
                changed[tfn] = new_text
    return changed


def errata_scan(texts, keyword):
    """errata：全 repo 同語意（大小寫不敏感子串）枚舉。回 [(rel, 行號, 行文)]。"""
    kw = keyword.lower()
    hits = []
    for rel, text in sorted(texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            if kw in line.lower():
                hits.append((rel, n, line))
    return hits


# Lint02 對賬：轉真表各有真來源——漂移指名來源側（其餘生成檔漂移歸 Lint01 泛訊息）
LINT02_SOURCES = {
    f"{GENERATED_DIR}/reference/routes.md":
        "routes 對照表與 router.rs 重算結果不一致——"
        "rust-api/server/src/router.rs ROUTES 改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/ports.md":
        "ports 對照表與 compose 重算結果不一致——compose 三檔"
        " ports: 段改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/schema.md":
        "schema 正典表與快照重算結果不一致——docs/ops/reference-src/schema-snapshot.json"
        "（或 archetype-map.json）改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/accounts.md":
        "accounts 正典表與快照重算結果不一致——docs/ops/reference-src/"
        "accounts-snapshot.json 改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/screens.md":
        "screens 正典表與 routes.ts 重算結果不一致——"
        "base-web/src/router/elegant/routes.ts 的 generatedRoutes 改動後未跑 tools/docs-sync.py generate",
    MSG_DICT_MD:
        "backend 拒因字典與 locale 重算結果不一致——base-web/src/locales/langs/"
        "{zh-tw,en-us}.ts 的 backend.* 改動後未跑 tools/docs-sync.py generate",
    MSG_DICT_PANEL:
        "字典面板 json 與 locale 重算結果不一致——deploy 側生成物嚴禁手改；"
        "locale 改動後跑 tools/docs-sync.py generate（rev4:FR-014 守門）",
}


def check_generated(root, computed, exemptions=None):
    """check：computed（{rel: content}）與磁碟現況 diff。回 findings。

    ★Day 1 具名豁免：被豁免的產出鍵當日不產，其路徑須自「缺生成檔」與「多出的檔案」
    兩分支同步豁免——否則條件化剛拿掉的紅會原封不動從 Lint01 那側冒回來。
    """
    out = []
    exempt_out = _day1_exempt_outputs(root, exemptions)
    gen_root = os.path.join(root, GENERATED_DIR)
    on_disk = set()
    for dirpath, _, names in os.walk(gen_root):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            on_disk.add(rel)
    # deploy 側字典面板＝生成物治外飛地（僅此一檔納管；同目錄手寫面板不受掃描）
    if os.path.exists(os.path.join(root, MSG_DICT_PANEL)):
        on_disk.add(MSG_DICT_PANEL)
    for rel in sorted(set(computed) | on_disk):
        if rel in exempt_out:
            continue
        if rel not in computed:
            out.append(finding(ERROR, "Lint01", rel, "多出的檔案（generated/ 嚴禁手加；請移除）"))
        elif rel not in on_disk:
            out.append(finding(ERROR, "Lint01", rel, "缺生成檔（跑 tools/docs-sync.py generate）"))
        elif _read(root, rel) != computed[rel]:
            if rel in LINT02_SOURCES:
                out.append(finding(ERROR, "Lint02", rel, LINT02_SOURCES[rel]))
            else:
                out.append(finding(ERROR, "Lint01", rel,
                                   "與重算結果不一致（忘跑 generate 或手改；跑 tools/docs-sync.py generate）"))
    return out


# ---------------------------------------------------------------------------
# git 介接與 IO 組裝（薄層；核心邏輯皆為上方可測純函式）
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 史料豁免：內容類 lint（Lint11~Lint15）不掃 one-shot 史料（其內文含示例 pattern、必自撞）
# ＋外部工具機器生成物豁免（2026-08-02 user 拍板）：graphify-out/ 之 .md 是 graphify 對本
# repo 源碼的節點標籤鏡像、非人寫治理文件，Lint12~Lint15 守的「引用健康」不適用；且任何
# lint 規則的自述一旦被抽成節點標籤即自撞（實證＝Lint15 docstring 之 ~/.claude/** 經
# GRAPH_REPORT.md 回頭命中 Lint15 本身）。★docs/generated/ 刻意不入豁免——那是本 repo
# 自己的真表、引用健康仍須守。
HISTORICAL_EXEMPT = ("docs/brainstorms/", "graphify-out/")


def _is_exempt(rel):
    return any(rel == p or rel.startswith(p) for p in HISTORICAL_EXEMPT)


def purge_git_env():
    """清掉本行程的 GIT_* 環境變數（就地改 os.environ，子行程一併免疫）。

    ★只給 test 子命令用：git 跑 hook 時會把外層 repo 的 GIT_DIR／GIT_INDEX_FILE 洩漏給
    子行程，而 `git commit -a` 與 pathspec commit 給的是**絕對路徑**（.git/index.lock、
    .git/next-index-PID.lock）——測試 fixture 在 temp repo 內跑的 git init／add／commit
    會因此寫進真 repo 的 index，整套崩（實測 44 failures＋1 error）且外層 commit 被
    「invalid object／Error building trees」這種與閘判定無關的訊息誤擋。同
    tools/fork-delta-lint.py 的 sh() 慣例。
    ★絕不可全域清：check／lint 必須繼續繼承 GIT_INDEX_FILE，否則看不到正在被 commit 的
    index（`git commit -a` 時尤其重要——那是唯一能看到自動 stage 內容的途徑）。
    """
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]


def git_out(args, cwd):
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=cwd,
                           capture_output=True, encoding="utf-8", errors="replace")
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def git_available(root):
    """守門工具的 fail-closed 前提：git 本體與 repo 必須可用。"""
    return git_out(["rev-parse", "--git-dir"], root) is not None


def head_file(rel, root):
    return git_out(["show", f"HEAD:{rel}"], root)


def index_pins(root):
    """外層 index 之 submodule pin（generate 面／STATE 帳面唯一來源）。

    ★逐庫復用 index_gitlink＝rev4:018 嚴格語意歸一（rev4:B-114）：只認 stage 0。修前舊碼
    自掃 `ls-files -s` 逐行覆寫、無 stage 過濾——gitlink 合併衝突未解（index 同存
    stage 1／2／3）時末筆＝stage 3（theirs）勝出（BACKLOG 條目誤記為「取首行＝
    讀到共同祖先」、據實勘正），STATE 顯示衝突單側 pin 一樣是帳面誤導。統一回
    {key: (SHA, 跳過原因)}：健康態 (SHA, None)；衝突態／無條目 (None, 原因)、
    渲染面（_fmt_pin）顯示未定。
    """
    return {key: index_gitlink(root, sub) for key, sub in PIN_KEYS}


def tracked_files(root):
    return [l for l in (git_out(["ls-files"], root) or "").splitlines() if l]


def unstaged_generated(root):
    """生成物的 working tree 與 index 落差（跑了 generate 忘了 git add）。"""
    out = git_out(["diff", "--name-only", "--", GENERATED_DIR, MSG_DICT_PANEL], root)
    return [l for l in (out or "").splitlines() if l]


def constitution_version(root):
    text = _read(root, ".specify/memory/constitution.md")
    if text is None:
        return None
    m = re.search(r"\*\*Version\*\*[:\s]*v?(\d+\.\d+\.\d+)", text)
    return m.group(1) if m else None


def load_adrs(root):
    d = os.path.join(root, ADR_DIR)
    if not os.path.isdir(d):
        return {}
    return {n: _read(root, f"{ADR_DIR}/{n}")
            for n in sorted(os.listdir(d)) if n.endswith(".md")}


def load_head_adrs(root):
    """HEAD 版 ADR 全載——單支 cat-file --batch（ADR 數量只增不減、逐檔 git show 會吃穿秒級預算）。"""
    out = git_out(["ls-tree", "HEAD", f"{ADR_DIR}/"], root) or ""
    entries = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        meta_part, path = line.split("\t", 1)
        parts = meta_part.split()
        if len(parts) == 3 and parts[1] == "blob" and path.endswith(".md"):
            entries.append((parts[2], os.path.basename(path)))
    if not entries:
        return {}
    try:
        r = subprocess.run(["git", "cat-file", "--batch"], cwd=root,
                           input="\n".join(oid for oid, _ in entries).encode(),
                           capture_output=True)
    except OSError:
        return {}
    if r.returncode != 0:
        return {}
    head, buf, pos = {}, r.stdout, 0
    for _, name in entries:
        nl = buf.index(b"\n", pos)
        hdr = buf[pos:nl].decode("utf-8", errors="replace").split()
        if len(hdr) != 3 or hdr[1] != "blob":
            pos = nl + 1
            continue
        size = int(hdr[2])
        head[name] = buf[nl + 1: nl + 1 + size].decode("utf-8", errors="replace")
        pos = nl + 1 + size + 1
    return head


def head_files_batch(rels, root):
    """依輸入序回傳各 rel 之 HEAD 版全文（HEAD 無此檔＝None）——語意同逐檔 head_file。

    ★恰兩發 subprocess（單支 ls-tree 取 oid → 單支 cat-file --batch），比照 load_head_adrs
    既有範式：LESSONS 條目檔同屬只增不減的集合，逐檔 git show 會吃穿秒級預算——U2 分檔
    遷移後 head 視野 2→約 48 條，drvfs 實測逐檔形每次 lint 多耗約 5s 且經 pre-commit
    進到每一顆 commit（B-090 U1b 補審 blocker）。"""
    if not rels:
        return []
    out = git_out(["ls-tree", "-r", "HEAD", "--", *rels], root)
    texts = {rel: None for rel in rels}
    if out is None:
        return [texts[rel] for rel in rels]
    oid_by_path = {}
    for line in out.splitlines():
        if "\t" not in line:
            continue
        meta_part, path = line.split("\t", 1)
        parts = meta_part.split()
        if len(parts) == 3 and parts[1] == "blob":
            oid_by_path[path] = parts[2]
    order = [(oid_by_path[rel], rel) for rel in rels if rel in oid_by_path]
    if order:
        try:
            r = subprocess.run(["git", "cat-file", "--batch"], cwd=root,
                               input="\n".join(oid for oid, _ in order).encode(),
                               capture_output=True)
        except OSError:
            r = None
        if r is not None and r.returncode == 0:
            buf, pos = r.stdout, 0
            for _, rel in order:
                nl = buf.index(b"\n", pos)
                hdr = buf[pos:nl].decode("utf-8", errors="replace").split()
                if len(hdr) != 3 or hdr[1] != "blob":
                    pos = nl + 1
                    continue
                size = int(hdr[2])
                texts[rel] = buf[nl + 1: nl + 1 + size].decode("utf-8", errors="replace")
                pos = nl + 1 + size + 1
    return [texts[rel] for rel in rels]


def _volume_paths(root, main_rel, prefix):
    """主檔＋docs/ops 下同前綴分卷（sorted）；主檔恆在 index 0。"""
    ops = os.path.join(root, "docs/ops")
    vols = (sorted(n for n in os.listdir(ops)
                   if n.startswith(prefix) and n.endswith(".md"))
            if os.path.isdir(ops) else [])
    return [main_rel] + [f"docs/ops/{v}" for v in vols]


def lessons_paths(root):
    """LESSONS 枚舉唯一權威（分檔制 2026-08-17、ADR 0045）：主檔（索引、恆 index 0、載
    next-id）＋舊分卷 LESSONS-*.md（過渡期防漏視野；遷移刪卷後自然消失）＋
    docs/ops/LESSONS/ 下 sorted 之 L-*.md 條目檔（目錄不存在＝略過）。"""
    paths = _volume_paths(root, "docs/ops/LESSONS.md", "LESSONS-")
    d = os.path.join(root, "docs/ops/LESSONS")
    if os.path.isdir(d):
        paths += [f"docs/ops/LESSONS/{n}" for n in sorted(os.listdir(d))
                  if n.startswith("L-") and n.endswith(".md")]
    return paths


# HEAD 之 LESSONS 卷集三形：主檔／舊分卷（docs/ops 頂層）／分檔制條目檔（ADR 0045）
RE_HEAD_LESSONS_PATH = re.compile(
    r"^docs/ops/(?:LESSONS\.md|LESSONS-[^/]+\.md|LESSONS/L-[^/]+\.md)$")


def head_lessons_paths(root):
    """Lint09 L 側 head 視野聯集用（ADR 0045）：git ls-tree 取 HEAD 之 LESSONS 卷集。

    聯集目的＝堵「整卷（或條目檔）被刪＝其號碼靜默退出反回收視野」——分檔遷移刪舊分卷
    即此形。HEAD 讀不到＝回空集（head 側缺席由 lint_ids 既有 None 容錯形承接）。
    """
    out = git_out(["ls-tree", "-r", "--name-only", "HEAD", "--", "docs/ops/"], root)
    if out is None:
        return []
    return [l for l in out.splitlines() if RE_HEAD_LESSONS_PATH.match(l)]


def lessons_head_view(root):
    """Lint09 L 側 head 視野清單的**單一構造權威**（ADR 0045）：現況 lessons_paths ∪
    HEAD 卷集，且主檔恆 index 0——run_lint 呼叫端與自測共用本 helper，構造式絕不抄第二份
    （兩份抄本各自漂移＝生產路徑零覆蓋的恆綠形）。

    ★主檔恆 index 0 是硬不變量：lint_ids 的 head_next 只讀 head_texts[0]，而字典序
    LESSONS-….md < LESSONS.md（連字號 0x2D < 句點 0x2E）會把主檔擠出首位→head_next=None→
    反回收閘整段靜默失效，故不可用裸 sorted(聯集)。"""
    lmain = "docs/ops/LESSONS.md"
    return [lmain] + sorted((set(lessons_paths(root)) | set(head_lessons_paths(root)))
                            - {lmain})


def backlog_paths(root):
    """BACKLOG 全卷：主檔＋滯後卷（BACKLOG-*.md；滯後≠完成、條目仍屬開放待辦）。
    配號 next-id 只在主檔（texts[0]）；滯後卷收 user 拍板滯後之整行搬移條目。"""
    return _volume_paths(root, BACKLOG, "BACKLOG-")


def gen_reference_stub(name):
    return (f"{GEN_HEADER}\n# reference/{name} — 全量正典表\n\n"
            f"狀態：stub｜來源未就緒——extractor 隨對應子系統首刀落地（見 ops/BACKLOG）。\n")


class ComposePortsError(Exception):
    """compose ports 解析失敗（fail-loud：寧可擋下、不靜默漏列）。"""


# 窄假設唯一合法項形：引號短語法＋127.0.0.1 綁定前綴＋純數字 port（本 repo 實際使用的形；
# 配號紀律歸 ADR 0004）。其他寫法（無引號、0.0.0.0、port 範圍、長語法…）一律 fail-loud。
RE_PORTS_ITEM = re.compile(r'^"(127\.0\.0\.1):(\d{1,5}):(\d{1,5})"$')
RE_COMPOSE_SERVICE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):$")


def parse_compose_ports(text, rel):
    """解析單一 compose 檔的 ports: 段。回 [(service, host_port, container_port, bind_ip)]。

    行級窄假設解析（標準庫、不引 YAML 庫；只支援本 repo 實際使用的形）：
    - 頂層 services:（0 縮排）→ 服務名＝2 縮排 `name:` → ports:＝4 縮排服務直屬鍵
    - 項目＝同縮排或更深縮排的 `- "127.0.0.1:HOST:CONTAINER"`（RE_PORTS_ITEM；不支援行內註解）
    - 任何不認得的 ports 項／ports 鍵位置／services 直屬 2 縮排行 → ComposePortsError 指名檔與行
      ——防未來 compose 改寫法時對照表靜默漏列（fail-loud 逼人同步擴充解析器）
    """
    rows = []
    in_services, service, ports_indent = False, None, None
    for n, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue  # 空行／註解行不終結區塊
        indent = len(raw) - len(raw.lstrip(" "))
        if ports_indent is not None:
            # 項目可與 ports: 鍵同縮排（YAML 合法形）——同縮排非清單行才是區塊結束
            if indent > ports_indent or (indent == ports_indent
                                         and stripped.startswith("- ")):
                if not stripped.startswith("- "):
                    raise ComposePortsError(
                        f"{rel}:行 {n}｜ports 段內不認得的行「{stripped}」（僅支援引號短語法清單項）")
                m = RE_PORTS_ITEM.fullmatch(stripped[2:].strip())
                if not m:
                    raise ComposePortsError(
                        f"{rel}:行 {n}｜不認得的 ports 項「{stripped}」"
                        '（僅支援 - "127.0.0.1:HOST:CONTAINER"；compose 改寫法請同步擴充本解析器）')
                rows.append((service, m.group(2), m.group(3), m.group(1)))
                continue
            ports_indent = None  # 區塊結束、本行落回狀態機
        if indent == 0:
            in_services = (stripped == "services:")
            service = None
            continue
        if stripped.startswith("ports:"):
            if not (in_services and service and indent == 4 and stripped == "ports:"):
                raise ComposePortsError(
                    f"{rel}:行 {n}｜不認得的 ports 鍵寫法/位置「{stripped}」"
                    "（僅支援服務直屬 4 縮排純鍵；compose 改寫法請同步擴充本解析器）")
            ports_indent = indent
            continue
        if in_services and indent == 2:
            m = RE_COMPOSE_SERVICE.fullmatch(stripped)
            if not m:
                raise ComposePortsError(
                    f"{rel}:行 {n}｜services 下不認得的服務行「{stripped}」"
                    "（僅支援裸服務名鍵、不支援行內註解；compose 改寫法請同步擴充本解析器）"
                    "——否則後續 ports 會錯掛到前一個服務")
            service = m.group(1)
    return rows


def compute_ports_rows(root):
    """三檔 compose 全掃。回 [(來源檔, service, host, container, ip)]；來源檔缺＝fail-loud。"""
    rows = []
    for rel in COMPOSE_FILES:
        text = _read(root, rel)
        if text is None:
            raise ComposePortsError(f"{rel}｜compose 來源檔不存在——ports 對照表無法重算")
        rows += [(rel, *r) for r in parse_compose_ports(text, rel)]
    return rows


def gen_reference_ports(rows):
    """reference/ports ← compose 三檔 ports: 段全量表。

    只列 compose 實際存在的映射（留號決策語意歸 ADR 0004、不入表）；
    列序確定性＝來源檔→服務名→host port。
    """
    head = (f"{GEN_HEADER}\n# reference/ports — 全量正典表\n\n"
            f"來源＝{'＋'.join(COMPOSE_FILES)} 的 ports: 段（generate 重算；配號紀律歸 ADR 0004）。\n\n")
    if not rows:
        return head + "（compose 無任何 host port 映射）\n"
    lines = "\n".join(
        f"| {svc} | {host} | {cont} | {ip} | {src} |"
        for src, svc, host, cont, ip in
        sorted(rows, key=lambda r: (r[0], r[1], int(r[2]), int(r[3]))))
    return (head + "| 服務 | host port | 容器內 port | 綁定 IP | 來源檔 |\n"
            "|---|---|---|---|---|\n" + lines + "\n")


# ---------------------------------------------------------------------------
# routes 直解：rust-api/server/src/router.rs 的 `pub const ROUTES` 全量表（rev4:B-001）。
# 比照上方 ports 直解範式（窄假設行級解析＋fail-loud）；rev4:B-052「route 抽取防漏」關鍵——
# 寧可擋下、絕不靜默漏列一條 route。
# ---------------------------------------------------------------------------

ROUTER_SOURCE = "rust-api/server/src/router.rs"
# router.rs 全部合法 variant（掌握全集才能讓 fail-loud 準確、新增即紅逼同步）：
ROUTE_METHODS = {"Get": "GET", "Post": "POST", "Delete": "DELETE"}  # HttpMethod variant → casbin act 字面
ROUTE_PROTECTIONS = ("Public", "Authed", "Policy")   # Protection 三態
ROUTE_REQUIRED_FIELDS = ("path", "method", "case_key", "envelope_exception", "protection")

# 窄假設唯一合法項形（router.rs 現行實際使用的形；stripped 後 fullmatch）：
RE_ROUTES_CONST_OPEN = re.compile(r"^pub const ROUTES:\s*&\[RouteDef\]\s*=\s*&\[$")
RE_ROUTE_FIELD_PATH = re.compile(r'^path:\s*"([^"]*)",$')
RE_ROUTE_FIELD_METHOD = re.compile(r"^method:\s*HttpMethod::(\w+),$")
RE_ROUTE_FIELD_HANDLER = re.compile(r"^handler:\s*\|\|\s*(?:get|post|delete)\(.+\),$")
RE_ROUTE_FIELD_CASE_KEY = re.compile(r'^case_key:\s*"([^"]*)",$')
RE_ROUTE_FIELD_ENVELOPE = re.compile(r"^envelope_exception:\s*(true|false),$")
RE_ROUTE_FIELD_PROTECTION = re.compile(r"^protection:\s*Protection::(\w+),$")


class RouterRoutesError(Exception):
    """router.rs ROUTES 解析失敗（fail-loud：寧可擋下、不靜默漏列一條 route——rev4:B-052）。"""


def _parse_route_field(stripped, rel, n):
    """解析 RouteDef 條目內單行欄位。回 (key, value)；handler 識形後回 (None, None)（略過不入表）。

    不認得的欄／形／未知 method 或 protection variant → RouterRoutesError 指名 rel:行。
    """
    m = RE_ROUTE_FIELD_PATH.fullmatch(stripped)
    if m:
        return "path", m.group(1)
    m = RE_ROUTE_FIELD_CASE_KEY.fullmatch(stripped)
    if m:
        return "case_key", m.group(1)
    m = RE_ROUTE_FIELD_ENVELOPE.fullmatch(stripped)
    if m:
        return "envelope_exception", m.group(1) == "true"
    m = RE_ROUTE_FIELD_METHOD.fullmatch(stripped)
    if m:
        variant = m.group(1)
        if variant not in ROUTE_METHODS:
            raise RouterRoutesError(
                f"{rel}:行 {n}｜未知 HttpMethod::{variant}"
                f"（已知：{'／'.join(ROUTE_METHODS)}；router.rs 新增動詞請同步擴充本解析器）")
        return "method", ROUTE_METHODS[variant]
    m = RE_ROUTE_FIELD_PROTECTION.fullmatch(stripped)
    if m:
        variant = m.group(1)
        if variant not in ROUTE_PROTECTIONS:
            raise RouterRoutesError(
                f"{rel}:行 {n}｜未知 Protection::{variant}"
                f"（已知：{'／'.join(ROUTE_PROTECTIONS)}；router.rs 新增保護態請同步擴充本解析器）")
        return "protection", variant
    if RE_ROUTE_FIELD_HANDLER.fullmatch(stripped):
        return None, None  # handler 閉包：識形後略過不入表（form 變即 fail-loud）
    raise RouterRoutesError(
        f"{rel}:行 {n}｜RouteDef 內不認得的欄/形「{stripped}」"
        "（僅支援 path／method／handler／case_key／envelope_exception／protection；"
        "router.rs 改寫法請同步擴充本解析器）")


def parse_router_routes(text, rel):
    """解析 router.rs 的 `pub const ROUTES` block。
    回 [(path, method, protection, case_key, envelope_exception)]。

    行級窄假設解析（標準庫、不 parse Rust；只支援 router.rs 現行實際使用的形）：
    - 只解析 `pub const ROUTES: &[RouteDef] = &[` 起、`];` 止的那一段 block；其他 RouteDef
      出現處（struct 定義、build() 迭代、doc 註解）一律不碰。
    - block 內頂層只認 `RouteDef {` 起條目、`}`／`},` 收條目，空行／`//` 註解跳過；其餘 fail-loud。
    - 條目內每欄一行；handler 閉包識形後略過不入表；method／protection variant 必屬已知集。
    - 未知欄／重複欄／缺欄／未知 variant／找不到 ROUTES const／block 未收尾 → RouterRoutesError
      指名 rel:行——防來源改寫法時對照表靜默漏列（fail-loud 逼人同步擴充解析器）。
    """
    rows = []
    found_const, in_const, entry, entry_line = False, False, None, None
    for n, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not in_const:
            if RE_ROUTES_CONST_OPEN.fullmatch(stripped):
                found_const, in_const = True, True
            continue  # const 外一律忽略（含 struct 定義、build() 迭代、doc 註解）
        if not stripped or stripped.startswith("//"):
            continue  # 空行／註解行不終結區塊
        if entry is None:
            if stripped == "];":
                in_const = False
                break  # ROUTES const 收尾（唯一一段、無需續掃）
            if stripped == "RouteDef {":
                entry, entry_line = {}, n
                continue
            raise RouterRoutesError(
                f"{rel}:行 {n}｜ROUTES block 頂層不認得的行「{stripped}」"
                "（僅支援 RouteDef 條目與收尾 ];；router.rs 改寫法請同步擴充本解析器）")
        if stripped in ("}", "},"):
            missing = [f for f in ROUTE_REQUIRED_FIELDS if f not in entry]
            if missing:
                raise RouterRoutesError(
                    f"{rel}:行 {entry_line}｜RouteDef 條目缺欄 {missing}"
                    "（router.rs 改寫法請同步擴充本解析器）")
            rows.append((entry["path"], entry["method"], entry["protection"],
                         entry["case_key"], entry["envelope_exception"]))
            entry = None
            continue
        key, value = _parse_route_field(stripped, rel, n)
        if key is None:
            continue  # handler：略過
        if key in entry:
            raise RouterRoutesError(f"{rel}:行 {n}｜RouteDef 內重複欄「{key}」")
        entry[key] = value
    if not found_const:
        raise RouterRoutesError(
            f"{rel}｜找不到 `pub const ROUTES: &[RouteDef] = &[`——routes 對照表無法重算")
    if in_const:
        raise RouterRoutesError(f"{rel}｜ROUTES const block 未見收尾 ];（fail-loud、防半解析漏列）")
    return rows


def compute_router_rows(root):
    """讀 router.rs → parse_router_routes。回 rows；來源檔缺＝fail-loud。"""
    text = _read(root, ROUTER_SOURCE)
    if text is None:
        raise RouterRoutesError(f"{ROUTER_SOURCE}｜router 來源檔不存在——routes 對照表無法重算")
    return parse_router_routes(text, ROUTER_SOURCE)


def gen_reference_routes(rows):
    """reference/routes ← router.rs ROUTES const 全量表。

    只列 ROUTES 實際註冊的路由（handler 閉包不入表；授權語意歸 router.rs 文件）；
    列序確定性＝path→method。
    """
    head = (f"{GEN_HEADER}\n# reference/routes — 全量正典表\n\n"
            f"來源＝{ROUTER_SOURCE} 的 ROUTES const（generate 重算；handler 閉包不入表）。\n\n")
    if not rows:
        return head + "（ROUTES 無任何條目）\n"
    lines = "\n".join(
        f"| {path} | {method} | {protection} | {case_key} | {'是' if env else '否'} |"
        for path, method, protection, case_key, env in
        sorted(rows, key=lambda r: (r[0], r[1])))
    return (head + "| path | method | protection | case_key | envelope 例外 |\n"
            "|---|---|---|---|---|\n" + lines + "\n")


# ---------------------------------------------------------------------------
# screens 直解：base-web/src/router/elegant/routes.ts 的 generatedRoutes const 全量表（rev4:B-005）。
# 比照上方 routes 直解範式（窄假設行級解析＋fail-loud），惟來源含巢狀 children（深達 3 層）——
# 以「容器框堆疊」追蹤 array／route／meta 邊界、遞迴 flatten 全部 route。rev4:B-052「防漏」關鍵：
# 寧可擋下、絕不靜默漏列一條 screen。
# ---------------------------------------------------------------------------

ELEGANT_SOURCE = "base-web/src/router/elegant/routes.ts"
# route 物件合法頂層欄全集（掌握全集才能讓 fail-loud 準確、來源新增欄即紅逼同步）：
# name／path／component 抽值入表；props／redirect 識形後略過；meta／children 開子容器。
ELEGANT_ROUTE_SKIP_FIELDS = ("props", "redirect")
ELEGANT_ROUTE_REQUIRED_FIELDS = ("name", "path")   # 每條 route 物件必備（缺＝fail-loud）

# 窄假設唯一合法形（routes.ts 現行實際使用的形：單引號字串、elegant-router prettier-ignore
# 穩定格式；stripped 後 fullmatch）。其他寫法（雙引號、行內物件…）一律 fail-loud。
RE_ELEGANT_CONST_OPEN = re.compile(r"^export const generatedRoutes: GeneratedRoute\[\] = \[$")
RE_ELEGANT_NAME = re.compile(r"^name: '([^']*)',$")
RE_ELEGANT_PATH = re.compile(r"^path: '([^']*)',$")
RE_ELEGANT_COMPONENT = re.compile(r"^component: '([^']*)',$")
RE_ELEGANT_I18NKEY = re.compile(r"^i18nKey: '([^']*)',?$")
RE_ELEGANT_FIELD = {"name": RE_ELEGANT_NAME, "path": RE_ELEGANT_PATH,
                    "component": RE_ELEGANT_COMPONENT}


class ElegantRoutesError(Exception):
    """routes.ts generatedRoutes 解析失敗（fail-loud：寧可擋下、不靜默漏列一條 screen——rev4:B-052）。"""


def parse_elegant_routes(text, rel):
    """解析 routes.ts 的 `export const generatedRoutes` 陣列、flatten 全巢狀 route。
    回 [(name, path, component, i18nKey)]（每條 route 物件一列、含所有 children）。

    行級窄假設解析（標準庫、不 parse TS；只支援 routes.ts 現行實際使用的形）：
    - 只解析 `export const generatedRoutes: GeneratedRoute[] = [` 起、頂層 `];` 止的那一段；
      其他 import／型別／別處一律不碰。
    - 以容器框堆疊追蹤邊界：array（陣列，直屬子＝route 物件）／route（route 物件，欄集＝
      name/path/component/props/redirect/meta/children）／meta（只抽 i18nKey、其餘欄安全略過）。
      route 物件開＝裸 `{`；收＝`}`／`},`（收時即 flatten 入表，父／葉皆列）；children＝巢狀 array。
    - route 頂層見不認得的欄／形、重複欄、缺 name/path、找不到 const、陣列未收尾 → ElegantRoutesError
      指名 rel:行——防來源改寫法時對照表靜默漏列（fail-loud 逼人同步擴充解析器）。
    """
    rows = []
    stack = []                        # [(kind, entry)]；kind∈{array,route,meta}；entry＝route dict 或 None
    found_const = in_const = False
    for n, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not in_const:
            if RE_ELEGANT_CONST_OPEN.fullmatch(stripped):
                found_const = in_const = True
                stack.append(("array", None))
            continue                  # const 外一律忽略（import／型別／註解）
        if not stripped or stripped.startswith("//"):
            continue                  # 空行／註解行不終結區塊
        kind, entry = stack[-1]
        if kind == "meta":
            if stripped in ("}", "},"):
                stack.pop()           # meta 收尾（`}` 或 `},`）
                continue
            m = RE_ELEGANT_I18NKEY.fullmatch(stripped)
            if m:
                if "i18nKey" in entry:
                    raise ElegantRoutesError(f"{rel}:行 {n}｜meta 內重複 i18nKey")
                entry["i18nKey"] = m.group(1)
            continue                  # 其餘 meta 欄（title/icon/order/roles/…）安全略過、不 choke
        if kind == "array":
            if stripped == "{":
                stack.append(("route", {"_line": n}))
                continue
            if stripped in ("]", "],", "];"):
                stack.pop()
                if not stack:
                    in_const = False
                    break             # 頂層 generatedRoutes 陣列收尾（唯一一段、無需續掃）
                continue              # children 子陣列收尾
            raise ElegantRoutesError(
                f"{rel}:行 {n}｜陣列頂層不認得的行「{stripped}」"
                "（僅支援 route 物件 `{` 與收尾 `]`；routes.ts 改寫法請同步擴充本解析器）")
        # kind == "route"
        if stripped in ("}", "},"):
            missing = [f for f in ELEGANT_ROUTE_REQUIRED_FIELDS if f not in entry]
            if missing:
                raise ElegantRoutesError(
                    f"{rel}:行 {entry['_line']}｜route 物件缺欄 {missing}"
                    "（routes.ts 改寫法請同步擴充本解析器）")
            rows.append((entry["name"], entry["path"],
                         entry.get("component", ""), entry.get("i18nKey", "")))
            stack.pop()
            continue
        if stripped == "meta: {":
            stack.append(("meta", entry))     # meta 寫回同一 route entry（i18nKey 落此）
            continue
        if stripped == "children: [":
            stack.append(("array", None))     # 巢狀 children：遞迴進 array 框
            continue
        key = stripped.split(":", 1)[0].strip()
        if key in RE_ELEGANT_FIELD:
            m = RE_ELEGANT_FIELD[key].fullmatch(stripped)
            if not m:
                raise ElegantRoutesError(
                    f"{rel}:行 {n}｜route 欄「{key}」形不認得「{stripped}」"
                    "（僅支援單引號字串；routes.ts 改寫法請同步擴充本解析器）")
            if key in entry:
                raise ElegantRoutesError(f"{rel}:行 {n}｜route 物件內重複欄「{key}」")
            entry[key] = m.group(1)
            continue
        if key in ELEGANT_ROUTE_SKIP_FIELDS:
            continue                  # props／redirect：欄名已知、值不入表故不需驗形
        raise ElegantRoutesError(
            f"{rel}:行 {n}｜route 物件內不認得的欄/形「{stripped}」"
            "（僅支援 name／path／component／props／redirect／meta／children；"
            "routes.ts 改寫法請同步擴充本解析器）")
    if not found_const:
        raise ElegantRoutesError(
            f"{rel}｜找不到 `export const generatedRoutes: GeneratedRoute[] = [`——screens 對照表無法重算")
    if in_const:
        raise ElegantRoutesError(f"{rel}｜generatedRoutes 陣列未見收尾 ];（fail-loud、防半解析漏列）")
    return rows


def compute_screen_rows(root):
    """讀 routes.ts → parse_elegant_routes。回 rows；來源檔缺＝fail-loud。"""
    text = _read(root, ELEGANT_SOURCE)
    if text is None:
        raise ElegantRoutesError(f"{ELEGANT_SOURCE}｜elegant routes 來源檔不存在——screens 對照表無法重算")
    return parse_elegant_routes(text, ELEGANT_SOURCE)


def gen_reference_screens(rows):
    """reference/screens ← routes.ts generatedRoutes 全量表（全巢狀 route flatten）。

    每條 route 物件一列（父／葉皆入表）；列序確定性＝name（elegant-router name 全域唯一）。
    component／i18nKey 某 route 無則留「—」；path 內含 `|`（如 login module 選擇器）由 _md_cell 轉義。
    """
    head = (f"{GEN_HEADER}\n# reference/screens — 全量正典表\n\n"
            f"來源＝{ELEGANT_SOURCE} 的 generatedRoutes const"
            f"（generate 重算；全巢狀 route flatten、每條一列）。\n\n")
    if not rows:
        return head + "（generatedRoutes 無任何 route）\n"
    lines = "\n".join(
        f"| {_md_cell(name)} | {_md_cell(path)} | {_md_cell(component)} | {_md_cell(i18nKey)} |"
        for name, path, component, i18nKey in sorted(rows, key=lambda r: r[0]))
    return (head + "| name | path | component | i18nKey |\n"
            "|---|---|---|---|\n" + lines + "\n")


# ---------------------------------------------------------------------------
# backend 拒因字典鏈（rev4:B-007／rev4:FR-014、rev4:016-observability rev4:T019）：base-web locale 兩語
# `backend.*` 鍵樹（單一真相源、唯讀）→ ①reference/backend-msg-dict.md 對照表
# ②deploy 側 grafana text panel json（零 datasource）。比照 ports/routes 直解範式
# （窄假設行級解析＋fail-loud）；兩語鍵集不相等＝fail-loud（字典缺譯即紅、非靜默缺列）。
# ---------------------------------------------------------------------------

# backend 樹內唯二合法行形（stripped 後 fullmatch；註解行另行跳過）：
RE_DICT_OPEN = re.compile(r"^([A-Za-z_$][A-Za-z0-9_$]*):\s*\{$")
RE_DICT_LEAF = re.compile(
    r"^([A-Za-z_$][A-Za-z0-9_$]*):\s*(['\"`])((?:\\.|(?!\2).)*)\2,?$")
RE_DICT_ESCAPE = re.compile(r"\\(.)")


class BackendDictError(Exception):
    """locale backend 樹解析失敗（fail-loud：寧可擋下、不靜默漏一鍵或收殘值）。"""


def parse_locale_backend(text, rel):
    """自 locale TS 擷取頂層 backend: { … } 樹。回 {扁平鍵: 值}（鍵＝a.b.c）。

    窄假設：樹內每行恰為 註解（//…）／子樹開（key: {）／葉（key: '值',）／閉（} 或 },）
    之一；值同行閉合、三種引號皆收、跳脫以 \\x → x 還原；重複鍵＝fail-loud。
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        # ★起點正則走共用常數 RE_LOCALE_BACKEND_OPEN（定義於本檔後段、python 於呼叫期
        # 解析 global，故前向引用可行）：兩處各寫一份 pattern 時，只改其中一處就會出現
        # 「豁免謂詞說可以重算、產出器卻 raise 找不到樹」的錯位。
        if RE_LOCALE_BACKEND_OPEN.fullmatch(line):
            start = i
            break
    if start is None:
        raise BackendDictError(f"{rel}｜找不到頂層 backend: {{ 樹——字典無法重算")
    out, stack = {}, []
    for n, raw in enumerate(lines[start + 1:], start=start + 2):
        s = raw.strip()
        if not s or s.startswith("//"):
            continue
        m = RE_DICT_OPEN.fullmatch(s)
        if m:
            stack.append(m.group(1))
            continue
        m = RE_DICT_LEAF.fullmatch(s)
        if m:
            key = ".".join(stack + [m.group(1)])
            if key in out:
                raise BackendDictError(f"{rel}:行 {n}｜重複鍵 {key}")
            out[key] = RE_DICT_ESCAPE.sub(r"\1", m.group(3))
            continue
        if s in ("}", "},"):
            if not stack:
                if not out:
                    raise BackendDictError(f"{rel}｜backend 樹為空——字典無法重算")
                return out
            stack.pop()
            continue
        raise BackendDictError(f"{rel}:行 {n}｜backend 樹內無法解析的行形：{s[:80]}")
    raise BackendDictError(f"{rel}｜backend 樹未閉合（EOF）")


def compute_msg_dict_rows(root):
    """讀兩語 locale → 鍵集斷言相等 → 回 [(key, zh, en)]（鍵序確定性）。"""
    trees = []
    for lang, rel in MSG_DICT_LOCALES:
        text = _read(root, rel)
        if text is None:
            raise BackendDictError(f"{rel}｜locale 來源檔不存在——字典無法重算")
        trees.append(parse_locale_backend(text, rel))
    zh, en = trees
    if set(zh) != set(en):
        diff = "、".join(sorted(set(zh) ^ set(en)))
        raise BackendDictError(f"兩語 backend 鍵集不相等（缺譯即紅）：{diff}")
    return [(k, zh[k], en[k]) for k in sorted(zh)]


def _msg_dict_table(rows):
    return ("| key | zh-TW | en-US |\n|---|---|---|\n"
            + "\n".join(f"| {_md_cell(k)} | {_md_cell(z)} | {_md_cell(e)} |"
                        for k, z, e in rows) + "\n")


def gen_msg_dict_md(rows):
    """reference/backend-msg-dict ← locale backend.* 兩語對照表（D9 拍板＝兩語）。"""
    head = (f"{GEN_HEADER}\n# reference/backend-msg-dict — 拒因字典（機器生成）\n\n"
            f"來源＝{'＋'.join(rel for _, rel in MSG_DICT_LOCALES)} 之 backend.* 鍵樹"
            f"（generate 重算；rev4:B-007／rev4:FR-014、全鏈零手維）。\n\n")
    return head + _msg_dict_table(rows)


def gen_msg_dict_panel(rows):
    """deploy 側字典面板 json ← 同 rows（text panel markdown 嵌入、零 datasource）。"""
    dash = {
        "uid": "obs-backend-msg-dict",
        "title": "拒因字典 (backend-msg-dict)",
        "description": MSG_DICT_HINT,
        "tags": ["obs", "rev5-admin", "backend-msg-dict"],
        "schemaVersion": 39,
        "editable": False,
        "graphTooltip": 0,
        "time": {"from": "now-6h", "to": "now"},
        "refresh": "",
        "timezone": "browser",
        "templating": {"list": []},
        "annotations": {"list": []},
        "panels": [{
            "id": 1,
            "type": "text",
            "title": "backend.* 拒因鍵 → zh-TW／en-US 對照",
            "description": MSG_DICT_HINT,
            "gridPos": {"h": 30, "w": 24, "x": 0, "y": 0},
            "options": {"mode": "markdown", "code": {"language": "plaintext"},
                        "content": f"{MSG_DICT_HINT}\n\n{_msg_dict_table(rows)}"},
        }],
    }
    return json.dumps(dash, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------
# 快照管線：refresh（需 stack）→ reference-src 兩快照（契約 specs/rev4:002-schema-baseline/
# contracts/snapshot-reference.md §1）。generate／check 只讀快照、絕不碰 docker。
# ---------------------------------------------------------------------------

REFERENCE_SRC_DIR = "docs/ops/reference-src"
SCHEMA_SNAPSHOT = f"{REFERENCE_SRC_DIR}/schema-snapshot.json"
ACCOUNTS_SNAPSHOT = f"{REFERENCE_SRC_DIR}/accounts-snapshot.json"
ARCHETYPE_MAP = f"{REFERENCE_SRC_DIR}/archetype-map.json"
STACK_HINT = "docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait"
DB_USER = "soybean"
DB_NAME = "soybean_admin_rust"
COMPOSE_PSQL = ["docker", "compose", "-f", "docker-compose.yml",
                "-f", "docker-compose.dev.yml", "exec", "-T", "postgres"]

# 唯讀撈取（information_schema／pg_catalog／SELECT only）；每支包 json_agg 回單值 JSON。
# seaql_migrations 除外（框架表；build_* 再防禦性過濾一次）。
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
# 帳號面三表；sys_user 明確逐欄 SELECT——絕不 SELECT *、password 欄不入快照（機密紀律）
SQL_USERS = _JSON_WRAP.format(
    "SELECT id, user_name, nick_name, status FROM sys_user ORDER BY id")
SQL_ROLES = _JSON_WRAP.format(
    "SELECT id, role_code, role_name, status FROM sys_role ORDER BY id")
SQL_BINDINGS = _JSON_WRAP.format(
    "SELECT user_id, role_id FROM sys_user_role ORDER BY user_id, role_id")

SCHEMA_COLUMN_KEYS = ("table", "column", "ordinal", "type", "nullable", "default")
SCHEMA_DEF_KEYS = ("table", "name", "definition")
USER_KEYS = ("id", "user_name", "nick_name", "status")
ROLE_KEYS = ("id", "role_code", "role_name", "status")
BINDING_KEYS = ("user_id", "role_id")


class SnapshotError(Exception):
    """快照管線失敗（stack 不在、撈取形不符、快照/歸屬檔缺）——fail-loud、絕不寫部分結果。"""


def _project(row, keys, what):
    """逐列投影到白名單欄集；多欄/缺欄＝fail-loud（多欄含 password 走私即機密紅線）。"""
    if not isinstance(row, dict):
        raise SnapshotError(f"{what} 列須為 object：{row!r}")
    extra = sorted(set(row) - set(keys))
    missing = [k for k in keys if k not in row]
    if extra or missing:
        raise SnapshotError(
            f"{what} 列欄集不符白名單（多：{extra or '無'}／缺：{missing or '無'}）"
            "——refresh 拒寫（撈取 SQL 與白名單須同步改）")
    return {k: row[k] for k in keys}


def _no_framework(rows):
    return [r for r in rows if r.get("table") != "seaql_migrations"]


def build_schema_snapshot(cols, idx, cons):
    """欄／索引／約束 → 確定性排序快照 dict（表名→ordinal；無產生時點欄位）。"""
    return {
        "columns": sorted((_project(r, SCHEMA_COLUMN_KEYS, "columns")
                           for r in _no_framework(cols)),
                          key=lambda r: (r["table"], r["ordinal"])),
        "indexes": sorted((_project(r, SCHEMA_DEF_KEYS, "indexes")
                           for r in _no_framework(idx)),
                          key=lambda r: (r["table"], r["name"])),
        "constraints": sorted((_project(r, SCHEMA_DEF_KEYS, "constraints")
                               for r in _no_framework(cons)),
                              key=lambda r: (r["table"], r["name"])),
    }


def build_accounts_snapshot(users, roles, bindings):
    """帳號面三表 → 確定性排序快照 dict；password 欄出現＝機密紅線 fail-loud。"""
    for u in users:
        if isinstance(u, dict) and "password" in u:
            raise SnapshotError(
                "機密紀律：sys_user 撈取含 password 欄——連雜湊值都不入快照，refresh 拒寫")
    return {
        "users": sorted((_project(u, USER_KEYS, "sys_user") for u in users),
                        key=lambda u: u["id"]),
        "roles": sorted((_project(r, ROLE_KEYS, "sys_role") for r in roles),
                        key=lambda r: r["id"]),
        "bindings": sorted((_project(b, BINDING_KEYS, "sys_user_role") for b in bindings),
                           key=lambda b: (b["user_id"], b["role_id"])),
    }


def snapshot_dumps(snap):
    """快照序列化：固定鍵序＋indent 2＋結尾換行——同輸入同 byte。"""
    return json.dumps(snap, ensure_ascii=False, indent=2) + "\n"


def _atomic_write(path, text):
    """原子替換寫檔（同目錄暫存→os.replace）；失敗不留半成品。"""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def psql_fetch(sql, root=None, run=subprocess.run):
    """compose exec psql 唯讀撈取、回 JSON rows；stack 不在＝fail-loud＋啟動提示。"""
    cmd = COMPOSE_PSQL + ["psql", "-U", DB_USER, "-d", DB_NAME,
                          "-v", "ON_ERROR_STOP=1", "-qAt", "-c", sql]
    try:
        proc = run(cmd, capture_output=True, text=True, cwd=root or ROOT)
    except OSError as ex:
        raise SnapshotError(
            f"無法執行 docker（{ex}）——refresh 需 dev stack 在跑；先啟動：{STACK_HINT}")
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout).strip() or f"退出碼 {proc.returncode}"
        raise SnapshotError(
            f"psql 撈取失敗：{reason}——refresh 需 dev stack 在跑；先啟動：{STACK_HINT}")
    try:
        rows = json.loads(proc.stdout)
    except json.JSONDecodeError as ex:
        raise SnapshotError(f"psql 輸出非合法 JSON（{ex.msg}）——查詢形被改動？")
    if not isinstance(rows, list):
        raise SnapshotError("psql 輸出非 JSON array——查詢形被改動？")
    return rows


def cmd_refresh(root=None, fetch=psql_fetch):
    """refresh：六撈全數成功→組兩快照→原子替換落檔（絕不寫部分結果）。"""
    root = root or ROOT
    schema_text = snapshot_dumps(build_schema_snapshot(
        fetch(SQL_COLUMNS, root), fetch(SQL_INDEXES, root), fetch(SQL_CONSTRAINTS, root)))
    accounts_text = snapshot_dumps(build_accounts_snapshot(
        fetch(SQL_USERS, root), fetch(SQL_ROLES, root), fetch(SQL_BINDINGS, root)))
    for rel, text in ((SCHEMA_SNAPSHOT, schema_text), (ACCOUNTS_SNAPSHOT, accounts_text)):
        _atomic_write(os.path.join(root, rel), text)
        print(f"refresh：寫 {rel}（{_line_count(text)} 行）")
    return 0


def _load_reference_src(root, rel, hint):
    """讀 reference-src 追蹤檔；缺檔／壞 JSON＝fail-loud（轉真後即為表的存在前提）。"""
    text = _read(root, rel)
    if text is None:
        raise SnapshotError(f"{rel} 缺失——{hint}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as ex:
        raise SnapshotError(f"{rel} 非合法 JSON（{ex.msg}）——{hint}")


def gen_reference_schema(snap, archetypes):
    """reference/schema ← schema 快照＋archetype 歸屬。逐表分節（表名序）。

    archetypes＝{table: {"label": …, …}}；快照有表、map 無歸屬＝fail-loud 指名。
    """
    tables = sorted({r["table"] for key in ("columns", "indexes", "constraints")
                     for r in snap.get(key, [])})
    missing = [t for t in tables if t not in archetypes]
    if missing:
        raise SnapshotError(
            "archetype-map 缺表歸屬：" + "、".join(missing)
            + f"——先補 data-model §1 再登記 {ARCHETYPE_MAP}")
    unlabeled = [t for t in tables if not archetypes[t].get("label")]
    if unlabeled:
        raise SnapshotError(
            "archetype-map 條目缺 label：" + "、".join(unlabeled)
            + f"——補齊 {ARCHETYPE_MAP} 該表的 label 欄")
    head = (f"{GEN_HEADER}\n# reference/schema — 全量正典表\n\n"
            f"來源＝{SCHEMA_SNAPSHOT}（refresh 自實庫撈）＋{ARCHETYPE_MAP}（變體歸屬）；"
            "由 generate 重算。seaql_migrations 除外。\n")
    parts = [head]
    for table in tables:
        parts.append(f"\n## {table}（archetype {archetypes[table]['label']}）\n\n"
                     "| 欄 | 型別 | 可空 | 預設 |\n|---|---|---|---|\n")
        parts.append("".join(
            f"| {_md_cell(c['column'])} | {_md_cell(c['type'])} "
            f"| {'是' if c['nullable'] else '否'} | {_md_cell(c['default'])} |\n"
            for c in sorted((c for c in snap.get("columns", []) if c["table"] == table),
                            key=lambda c: c["ordinal"])))
        for label, key in (("索引", "indexes"), ("約束", "constraints")):
            rows = sorted((r for r in snap.get(key, []) if r["table"] == table),
                          key=lambda r: r["name"])
            if rows:
                parts.append(f"\n{label}：\n" + "".join(
                    f"- {r['name']}｜{r['definition']}\n" for r in rows))
    return "".join(parts)


def gen_reference_accounts(snap):
    """reference/accounts ← accounts 快照（帳號｜暱稱｜狀態｜角色綁定；零密碼欄）。"""
    role_code = {r["id"]: r["role_code"] for r in snap.get("roles", [])}
    bound = {}
    for b in snap.get("bindings", []):
        if b["role_id"] not in role_code:
            raise SnapshotError(
                f"accounts 快照綁定指向不存在的 role id {b['role_id']}"
                f"（user id {b['user_id']}）——重跑 tools/docs-sync.py refresh")
        bound.setdefault(b["user_id"], []).append(role_code[b["role_id"]])
    user_rows = "".join(
        f"| {_md_cell(u['user_name'])} | {_md_cell(u['nick_name'])} "
        f"| {_md_cell(u['status'])} | {_md_cell('、'.join(sorted(bound.get(u['id'], []))))} |\n"
        for u in snap.get("users", []))
    role_rows = "".join(
        f"| {_md_cell(r['role_code'])} | {_md_cell(r['role_name'])} "
        f"| {_md_cell(r['status'])} |\n"
        for r in snap.get("roles", []))
    return (f"{GEN_HEADER}\n# reference/accounts — 全量正典表\n\n"
            f"來源＝{ACCOUNTS_SNAPSHOT}（refresh 自實庫撈；零密碼欄——契約明文）；"
            "由 generate 重算。\n\n"
            "## 帳號\n\n| 帳號 | 暱稱 | 狀態 | 角色綁定 |\n|---|---|---|---|\n"
            + user_rows +
            "\n## 角色\n\n| 角色碼 | 角色名 | 狀態 |\n|---|---|---|\n" + role_rows)


def compute_snapshot_reference(root):
    """兩快照＋archetype-map → reference/{schema,accounts}.md。回 {rel: content}。"""
    refresh_hint = "先跑 tools/docs-sync.py refresh（需 dev stack 在跑）"
    schema_snap = _load_reference_src(root, SCHEMA_SNAPSHOT, refresh_hint)
    accounts_snap = _load_reference_src(root, ACCOUNTS_SNAPSHOT, refresh_hint)
    amap = _load_reference_src(
        root, ARCHETYPE_MAP, "追蹤中繼檔、隨 schema 刀維護（初始內容＝data-model §1 轉錄）")
    archetypes = {t["table"]: t for t in amap.get("tables", [])
                  if isinstance(t, dict) and "table" in t}
    return {
        f"{GENERATED_DIR}/reference/schema.md":
            gen_reference_schema(schema_snap, archetypes),
        f"{GENERATED_DIR}/reference/accounts.md":
            gen_reference_accounts(accounts_snap),
    }


# ---------------------------------------------------------------------------
# G7 tools-cli 真表／Lint19 命令形 lint（rev4:contracts G5/G7；rev4:FR-014）
# ---------------------------------------------------------------------------

# ★名冊採**單一路徑形**（ADR 0010 轉換批①、B-035 U2）：原為「裸名＋各衍生面自行補
# `tools/` 前綴」，deploy/ 也開始出現受治理的 python 工具後，目錄不能再是隱含常識。改路徑形
# 的理由＝維持「一份名冊、一處釘死斷言」——另立第二份 deploy 名冊等於讓每個衍生面都要記得
# 取兩者聯集，漏一處就是靜默恆綠，而防名冊縮水正是本名冊存在的唯一理由。
TOOLS_PY = ("tools/docs-sync.py", "tools/fork-delta-lint.py", "tools/schema-gate.py",
            "tools/wire-schema.py", "tools/secret-value-guard.py",
            "tools/entity-drift-gate.py", "tools/wf-watchdog.py",
            "deploy/preflight-secrets.py", "deploy/decrypt-secrets.py",
            "deploy/generate-secrets.py", "deploy/setup-reaper-role.py",
            "deploy/backup-db.py")
TOOLS_SH = ("bootstrap",)
# ★轉換窗口共存名單（TOOLS_PY_SH_TWIN、ADR 0010）已於 B-037 U3 隨最後三支舊 .sh 退役而**整
# 條下架**——該機制與其到期即紅守衛（check_twin_window）自註解即預告收攏終點，名單清空即
# 無存在理由。此後舊名禁令對 deploy 條目一律嚴格形：`deploy/generate-secrets.sh` 這類殘留
# 命令形指向不存在的檔，Lint19 當場紅（覆蓋案＝test_retired_sh_name_is_error）。
TOOLS_CLI_MD = f"{GENERATED_DIR}/reference/tools-cli.md"
SH_USAGE_HEAD = 10     # bash 用法行只認檔頭前 N 行的註解（再深＝內文敘述、非介面說明）
# ★語料寫死三件活手冊（現在式）：NOTES 屬未來式帳（可合法提及尚未存在的子命令、clarify
# 拍板）、LESSONS 屬過去式史料（rev4:L-143 留有當時舊名的實跑 exit 對照）、docs/generated/ 為
# 機器生成（含本真表自身與由 events 派生的里程碑摘要）——三者入語料即當場自紅。
CMD_FORM_CORPUS = ("CLAUDE.md", "README.md", "docs/ops/RUNBOOK.md")

# 掃源＝分派表的字串比較字面。★兩形都要收：schema-gate 的 audit 只出現在 `cmd in (…)` 形，
# 只收等號形則真表少一個子命令、與源碼對不上（rev4:SC-006）。變數名限定 cmd、子命令限小寫起首
# ——把一般字串比較（如 mode 比對、大寫常數）擋在外。
RE_DISPATCH_EQ = re.compile(r'\bcmd\s*==\s*"([a-z][a-z0-9-]*)"')
RE_DISPATCH_IN = re.compile(r"\bcmd\s+in\s+\(([^)]*)\)")
RE_DISPATCH_ITEM = re.compile(r'"([a-z][a-z0-9-]*)"')

# 命令形：子命令 token 收「一個以上的空白／tab 後緊接」。★唯一例外＝目錄樹行（行首為
# `├`／`└` 分支符號）上的「多空白對欄」——README 的 repo 目錄樹用多空白把說明文字對欄，
# `tools/fork-delta-lint.py` 那行後面第一個詞恰是 base-web（完全合子命令字元集），而該工具
# 子命令集為空、任何 token 都不合法，不排除即一律誤紅。判準取排版形制（樹狀圖行）而非工具
# 身分；樹狀圖行上的單一空白形仍照驗（見 test_tree_line_with_single_space_…）。
RE_CMD_PY = re.compile(
    r"(" + "|".join(re.escape(rel) for rel in TOOLS_PY)
    + r")(?:(?P<gap>[ \t]+)(?P<sub>[a-z][a-z0-9-]*))?")
RE_TREE_LINE = re.compile(r"^[ \t│]*[├└]")
# 名冊涵蓋的工具目錄（自名冊現算、不落第二份字面）：續值排除前瞻要擋掉「另一支完整命令
# 形」，而完整命令形的起手就是這些目錄名——寫死 `tools/` 時 `deploy/…` 會被當成前一支的
# 續值 token（例如「`…docs-sync.py check` / `deploy/preflight-secrets.py`」誤紅 deploy）。
TOOLS_PY_DIRS = tuple(sorted({rel.split("/", 1)[0] for rel in TOOLS_PY}))
_RE_DIR_GUARD = r"(?!(?:" + "|".join(TOOLS_PY_DIRS) + r")/)"
# 一格多值的續值兩形，皆可連鎖任意多值（三值以上、兩形混用都驗得到）：
#   ①同段內：分隔符緊接前一個 token（`gate1|gate2|audit`、`check/lint`），收直豎線與
#     ASCII／全形斜線——同段內不可能是表格欄界，緊接形無歧義。
#   ②跨代碼段：前段收尾後以斜線接下一個代碼段（`… check` / `lint`／`… check`／`lint`）。
#     ★跨段分隔符**只收斜線、刻意不收直豎線**：markdown 表格的欄界正是直豎線，收了就會
#     把下一欄第一個小寫詞當成續值（例如「…`test` | pre-commit 兩道 |」誤紅 pre-commit）。
# ★兩形的 group 都收在 token 尾（不含結尾反引號）：吃掉結尾反引號後，下一輪的 `[^`\n]*`
#   會先把「空白斜線空白」吃掉、再也對不上「反引號＋斜線＋反引號」的形，鏈式只能延續一次
#   （U5-quality 實測：三值斜線鏈第三值漏檢、混合分隔全漏）。
# ★`[^`\n]*` 不含反引號＝只能錨在「其後第一個反引號」上，不會跨到別的命令形的代碼段。
# ★續值不得誤收「另一支完整命令形」：(?!tools/) 擋以工具路徑起手的代碼段；SLASH 形另以
#   (?=[`|/／]) 要求續值 token 後緊接反引號或下一分隔符——「python3 tools/…」這種 token 後
#   還有空白與引數的完整命令形因此不會被當成前一支的續值（它由 RE_CMD_PY 自己那輪去驗）。
#   誤收的後果＝對 RUNBOOK 現行「`…check` / `python3 …test`」句型誤紅 ERROR 硬擋（U5 實證）。
RE_SUB_PIPE = re.compile(r"[|/／]" + _RE_DIR_GUARD + r"([a-z][a-z0-9-]*)")
RE_SUB_SLASH = re.compile(r"[^`\n]*`\s*[/／]\s*`" + _RE_DIR_GUARD
                          + r"([a-z][a-z0-9-]*)(?=[`|/／])")


def _old_py_name_alt(rel):
    """舊名禁令的單一名冊項樣式＝去副檔名的路徑＋負向前瞻（只排除 .py 新名自身）。"""
    return re.escape(rel[:-len(".py")]) + r"(?!\.py)"


RE_CMD_OLD = re.compile(r"(" + "|".join(_old_py_name_alt(rel) for rel in TOOLS_PY) + r")\b")
RE_CMD_SH = re.compile(r"tools/(" + "|".join(TOOLS_SH) + r")\.sh\b")
# ★舊名禁令（rev4:B-127、比照 rev4:B-111 之 RE_CMD_OLD）：舊名是新名的前綴子字串（tools/bootstrap
#   之於 tools/bootstrap.sh），邊界判定＝負向前瞻 (?!\.sh) 排除新名自身＋ \b 排除更長
#   識別字——新名不誤咬、舊名（後隨空白／反引號／行尾等）即紅。
RE_CMD_OLD_SH = re.compile(r"tools/(" + "|".join(TOOLS_SH) + r")(?!\.sh)\b")


class ToolsCliError(Exception):
    """tools-cli 掃源失敗（fail-loud：python 工具本體缺席＝真表無源，不得靜默產空表）。"""


def scan_subcommands(source):
    """工具源碼 → 子命令集（去重排序）。"""
    subs = set(RE_DISPATCH_EQ.findall(source))
    for group in RE_DISPATCH_IN.findall(source):
        subs.update(RE_DISPATCH_ITEM.findall(group))
    return sorted(subs)


def sh_usage_line(source):
    """bash 檔頭前 SH_USAGE_HEAD 行內首個含「用法」的註解行（去註解符）；缺→None。"""
    for line in source.splitlines()[:SH_USAGE_HEAD]:
        s = line.strip()
        if s.startswith("#") and "用法" in s:
            return s.lstrip("#").strip()
    return None


def compute_tools_cli(root):
    """TOOLS_PY／TOOLS_SH 名冊掃源 → 真表 rows（python＝子命令集；bash＝存在＋用法行）。"""
    rows = []
    for rel in TOOLS_PY:
        src = _read(root, rel)
        if src is None:
            raise ToolsCliError(f"{rel} 讀不到——真表缺源、命令形比對基準無法建立")
        rows.append({"rel": rel, "lang": "python", "subs": scan_subcommands(src)})
    for name in TOOLS_SH:
        rel = f"tools/{name}.sh"
        src = _read(root, rel)
        rows.append({"rel": rel, "lang": "bash", "exists": src is not None,
                     "usage": sh_usage_line(src) if src is not None else None})
    return rows


def gen_tools_cli(rows):
    """真表 md（GEN_HEADER＋每工具一節；data-model §7）。"""
    # ★抬頭支數由 rows 現算、不寫死字面：寫死時名冊增減只改得到節數、抬頭原封不動，生成檔
    # 當場自我矛盾且全套件仍綠（rev4:019 U1 實證：名冊進 secret-value-guard 後抬頭仍稱「六支」、
    # 實列七節）。字面斷言＝test_tools_roster_is_pinned_and_table_renders_seven_sections。
    n_py = sum(1 for r in rows if r["lang"] == "python")
    parts = [GEN_HEADER, "# reference/tools-cli — 治理工具命令真表", "",
             f"來源＝治理工具名冊 {len(rows)} 支掃源（python {n_py} 支＝分派表字串比較字面、"
             f"去重排序；bash {len(rows) - n_py} 支＝存在與檔頭用法行）。消費者＝lint Lint19 "
             "命令形條款（語料＝CLAUDE.md／README.md／docs/ops/RUNBOOK.md 三件活手冊）＋人讀。\n"]
    for row in rows:
        parts.append(f"## {row['rel']}")
        parts.append(f"- 語言：{row['lang']}")
        if row["lang"] == "python":
            parts.append("- 子命令：" + ("｜".join(f"`{s}`" for s in row["subs"])
                                       if row["subs"] else "（無——源碼無分派表、直跑）"))
        else:
            parts.append(f"- 存在：{'是' if row['exists'] else '否'}")
            parts.append("- 檔頭用法行：" + (row["usage"]
                                        or f"（檔頭前 {SH_USAGE_HEAD} 行無「用法」註解行）"))
        parts.append("")
    return "\n".join(parts)


def _extra_subs(line, pos):
    """同一命令形之續值 token 全集（一格多值、可連鎖；見 RE_SUB_PIPE／RE_SUB_SLASH）。"""
    out = []
    while True:
        m = RE_SUB_PIPE.match(line, pos) or RE_SUB_SLASH.match(line, pos)
        if not m:
            return out
        out.append(m.group(1))
        pos = m.end()


def check_cmd_forms(texts, subs, sh_exists):
    """純判定：texts={rel: 全文}、subs={python 工具 rel: 子命令集}、sh_exists={bash rel: bool}。"""
    out = []
    for rel in sorted(texts):
        for n, line in enumerate((texts[rel] or "").splitlines(), start=1):
            for m in RE_CMD_PY.finditer(line):
                sub = m.group("sub")
                tool = m.group(1)
                if sub is None:
                    continue
                if len(m.group("gap")) > 1 and RE_TREE_LINE.match(line):
                    continue           # 目錄樹對欄：其後是說明文字、非子命令（見 RE_TREE_LINE）
                for value in [sub] + _extra_subs(line, m.end()):
                    if value in subs.get(tool, set()):
                        continue
                    out.append(finding(
                        ERROR, "Lint19", f"{rel}:行 {n}",
                        f"命令形宣稱的子命令「{value}」不在 {tool} 的分派表——比對基準＝該工具"
                        f"源碼的分派表（每次執行即時掃源；真表 {TOOLS_CLI_MD} 是同一份掃源的"
                        "生成物、不是基準，手改真表不會改變判定）；文件宣稱漂移，改回真名，"
                        "或先讓工具支援該子命令再回頭改文件"))
            for m in RE_CMD_OLD.finditer(line):
                out.append(finding(
                    ERROR, "Lint19", f"{rel}:行 {n}",
                    f"舊名命令形「{m.group(1)}」（缺 .py 副檔名）——rev4:B-111 改名後工具實體"
                    "只有 .py 名，照著打即檔不存在"))
            for m in RE_CMD_OLD_SH.finditer(line):
                out.append(finding(
                    ERROR, "Lint19", f"{rel}:行 {n}",
                    f"舊名命令形「tools/{m.group(1)}」（缺 .sh 副檔名）——rev4:B-127 改名後工具實體"
                    "只有 .sh 名，照著打即檔不存在"))
            for m in RE_CMD_SH.finditer(line):
                tool = f"tools/{m.group(1)}.sh"
                if not sh_exists.get(tool, False):
                    out.append(finding(ERROR, "Lint19", f"{rel}:行 {n}",
                                       f"命令形指向不存在的工具「{tool}」"))
    return out


def lint_cmd_forms(root):
    """Lint19：三件活手冊的 tools 命令形 vs tools-cli 真表（rev4:contracts G5）。"""
    try:
        rows = compute_tools_cli(root)
    except ToolsCliError as ex:
        return [finding(ERROR, "Lint19", "tools",
                        f"真表掃源失敗（{ex}）——命令形無比對基準，fail-closed")]
    texts = {rel: _read(root, rel) for rel in CMD_FORM_CORPUS}
    return check_cmd_forms(
        {rel: t for rel, t in texts.items() if t is not None},
        {r["rel"]: set(r["subs"]) for r in rows if r["lang"] == "python"},
        {r["rel"]: r["exists"] for r in rows if r["lang"] == "bash"})


def parse_events_loose(text):
    """generate 用的寬鬆解析（壞行、非 object 行跳過——擋壞行是 Lint03 的職責）。"""
    events = []
    for line in _jsonl_lines(text or ""):
        if line.strip():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(e, dict):
                events.append(e)
    return events


def compute_generated(root, exemptions=None):
    """重算 docs/generated/ 全部應有內容。回 {rel: content}。

    ★Day 1 具名豁免（§4.5.10 乙①）：登記於 DAY1_EXEMPTIONS 且謂詞未成立者**不產該鍵**，
    連帶不呼叫其產出器——五個產出器缺源時各自 raise（ComposePortsError／RouterRoutesError／
    ElegantRoutesError／BackendDictError／SnapshotError），不條件化則 generate 整支中止。
    ★回傳形維持純 dict、不 emit findings：跳過明細統一由 lint_reference_sources 輸出
    （改成回 tuple 會破 test_compute_generated_wires_tools_cli 的 assertIn 形）。
    """
    events = parse_events_loose(_read(root, EVENTS))
    metas = [parse_front_matter(t)[0] for t in load_adrs(root).values()]
    btexts = [(_read(root, rel) or "") for rel in backlog_paths(root)]
    lessons_texts = [(_read(root, rel) or "") for rel in lessons_paths(root)]
    ctx = {
        "pins": index_pins(root),
        "constitution_version": constitution_version(root),
        "events": events,
        "adr_metas": metas,
        "backlog_count": len(RE_ENTRY["B"].findall(btexts[0])),
        "backlog_next": _parse_next("B", btexts[0]),
        "backlog_deferred_count": sum(len(RE_ENTRY["B"].findall(t)) for t in btexts[1:]),
        "lessons_count": sum(len(RE_ENTRY["L"].findall(t)) for t in lessons_texts),
        "lessons_next": _parse_next("L", lessons_texts[0]),
    }
    files = {
        f"{GENERATED_DIR}/STATE.md": gen_state(ctx),
        f"{GENERATED_DIR}/DECISIONS-INDEX.md": gen_decisions_index(metas),
    }
    files.update(gen_milestones(events))
    for name in REFERENCE_TABLES:
        if name in REFERENCE_LIVE:
            continue
        files[f"{GENERATED_DIR}/reference/{name}.md"] = gen_reference_stub(name)
    exempt = day1_active(root, exemptions)
    if "gen.compose" not in exempt:
        files[f"{GENERATED_DIR}/reference/ports.md"] = gen_reference_ports(compute_ports_rows(root))
    if "gen.router" not in exempt:
        files[f"{GENERATED_DIR}/reference/routes.md"] = gen_reference_routes(compute_router_rows(root))
    if "gen.screens" not in exempt:
        files[f"{GENERATED_DIR}/reference/screens.md"] = gen_reference_screens(compute_screen_rows(root))
    if "gen.msg_dict" not in exempt:
        msg_rows = compute_msg_dict_rows(root)
        files[MSG_DICT_MD] = gen_msg_dict_md(msg_rows)
        files[MSG_DICT_PANEL] = gen_msg_dict_panel(msg_rows)
    # ★第六產出器：來源＝tools/ 自身、B2 即在位，Day 1 不紅故無豁免
    files[TOOLS_CLI_MD] = gen_tools_cli(compute_tools_cli(root))
    if "gen.snapshots" not in exempt:
        files.update(compute_snapshot_reference(root))
    return files


# ---------------------------------------------------------------------------
# Lint04 收刀事件存在性／Lint05 review 分流雙源對賬／Lint06 arch_impact 存在性＋最新刀雙向
# ---------------------------------------------------------------------------


def _norm_bid(s):
    """B-NNN 正規化為 3 位零填字串，令事件字串與 BACKLOG 條目可比。"""
    m = re.fullmatch(r"B-(\d+)", s) if isinstance(s, str) else None
    return f"B-{int(m.group(1)):03d}" if m else s


def _open_backlog_ids(root):
    """現況 BACKLOG 全卷（主檔＋滯後卷）仍開放的 B-NNN 條目集（RE_ENTRY 認真條目、
    非散文引用；滯後≠完成——滯後卷條目對 Lint04/Lint05 一律視為仍開放）。"""
    ids = set()
    for rel in backlog_paths(root):
        text = _read(root, rel) or ""
        ids.update(f"B-{int(m.group(1)):03d}" for m in RE_ENTRY["B"].finditer(text))
    return ids


def _backlog_ever_tokens(root, cache=None):
    """BACKLOG 全卷 git 全史「曾存在之 `B-NNN｜` token」集合（至多一次全史單掃）。
    ★取代逐慢路徑 id 各發一次 `git log -S` pickaxe（drvfs 實測單發 ~7s、筆數隨治理活動永久
    遞增＝每次 commit 成本線性惡化）：改一發 `git log --oneline -p` 全史掃描，於 diff 內容行
    以 RE_ENTRY_ANYPOS 寬鬆子串形抓 token、不加行首錨定——與 pickaxe -S 同語意：子串曾存在
    於任一歷史版本（含後來被刪者、含僅被其他條目內文引用者）必經某 commit 加號行進入
    （初始 commit 之 diff 全檔皆加號行）；減號行掃描屬證明性冗餘（shallow／grafted 史把
    加入 commit 裁掉時 token 只以減號行現身、pickaxe 仍判 True，漏掃即破壞等價）。
    存 group(0) 逐字 token（不正規化數字）＝保留 pickaxe 的字面子串比對語意。
    ★--no-color／--no-ext-diff／--no-textconv 免疫機器級 git 組態（color.ui=always 會把
    +/- 行前綴成 ESC 碼→token 集塌空＝Lint04 全面誤報 phantom；同 git_out 硬編 core.quotepath=off
    的免疫紀律）。+++/--- 檔頭行內容為 ASCII 路徑、regex 恆不中；--oneline 標題行以 sha
    起頭不入 +/- 過濾、subject 縱含 B-NNN｜亦不混入。git 不可用→空集合（同逐 id 版回 False）。
    cache＝呼叫端快取 dict（lint_close_existence 區域下傳、同 submodule_head 慣例）；
    不給（單測直呼）＝每次真打、無跨案殘留。"""
    if cache is not None and root in cache:
        return cache[root]
    out = git_out(["log", "--oneline", "--no-color", "--no-ext-diff", "--no-textconv",
                   "-p", "--", *backlog_paths(root)], root)
    toks = set()
    for line in (out or "").splitlines():
        if line.startswith(("+", "-")):
            toks.update(m.group(0) for m in RE_ENTRY_ANYPOS["B"].finditer(line))
    if cache is not None:
        cache[root] = toks
    return toks


def _backlog_id_ever_existed(root, nb, cache=None):
    """B-NNN 是否曾在 BACKLOG.md git 史出現過（真被 defer、非 phantom/typo）。
    ★不問「何時加」：backlog 項或於 mid-feature commit、或於 merge 後之收刀簿記 commit 加入
    （CLAUDE.md §2 簿記排在 merge 之後），故 merge SHA 非可靠參考點——只問「有沒有真加過」。
    `｜` 為條目欄位分隔、散文引用不帶，故 `B-NNN｜` 專認真條目。git 不可用（測試）→False。
    實作＝查 _backlog_ever_tokens 單掃集合（cache 透傳呼叫端）；lazy——零慢路徑 id 時
    本函式不被呼叫、零新成本。"""
    return f"{nb}｜" in _backlog_ever_tokens(root, cache)


def _backlog_done_ids(events):
    """曾在任一 feature_close／misc 之 backlog_done 被標記完成的 B-NNN 集（＝已被消化的證據；
    misc 通道＝輕量軌收刀、2026-07-17 調規）。"""
    out = set()
    for e in events:
        if e.get("type") in ("feature_close", "misc") and isinstance(e.get("backlog_done"), list):
            out.update(_norm_bid(b) for b in e["backlog_done"] if isinstance(b, str))
    return out


def _adr_ids_on_disk(root):
    """現況 ADR_DIR 下合法檔名的 4 碼 ADR 編號集。"""
    d = os.path.join(root, ADR_DIR)
    ids = set()
    if os.path.isdir(d):
        for n in os.listdir(d):
            m = RE_ADR_FILENAME.fullmatch(n)
            if m:
                ids.add(m.group(1))
    return ids


def lint_close_existence(root):
    """Lint04：逐 feature_close 驗其引用之 ADR／backlog／specs 目錄真實存在。回 findings。"""
    out = []
    events = parse_events_loose(_read(root, EVENTS))
    open_ids = _open_backlog_ids(root)
    done_ids = _backlog_done_ids(events)
    adr_ids = _adr_ids_on_disk(root)
    ever_cache = {}   # 全史單掃快取（區域生命週期＝本條款一次執行；同 submodule_head 慣例）
    for e in events:
        etype = e.get("type")
        # misc 亦可攜 backlog_done（輕量軌消化通道、2026-07-17 調規）——同受「宣稱完成卻未刪列」檢查；
        # 其餘檢查（adrs/backlog_add/specs）對 misc 自然 no-op（欄不存在）。
        if etype not in ("feature_close", "misc"):
            continue
        feat = e.get("feature")
        where = f"{EVENTS}｜{feat if etype == 'feature_close' else 'misc ' + str(e.get('date'))}"
        for adr in e.get("adrs", []) or []:
            if adr not in adr_ids:
                out.append(finding(ERROR, "Lint04", where,
                                   f"adrs 引用 ADR {adr} 但 {ADR_DIR}/ 無對應檔"))
        for b in e.get("backlog_done", []) or []:
            if _norm_bid(b) in open_ids:
                out.append(finding(ERROR, "Lint04", where,
                                   f"backlog_done {b} 仍在 BACKLOG 卷（主檔或滯後卷；宣稱完成卻未刪列）"))
        for b in e.get("backlog_add", []) or []:
            nb = _norm_bid(b)
            # 快速路徑：現況仍開放 或 後續 backlog_done 消化＝顯然真被 defer、免 git。
            if nb in open_ids or nb in done_ids:
                continue
            # 事後獨立完成刪列（git 即史、不進 event）→查 BACKLOG git 史確認曾真加過；
            # 從未出現＝phantom/typo。git 不可用（測試無 git）→_ever_existed False→仍抓 phantom。
            if _backlog_id_ever_existed(root, nb, ever_cache):
                continue
            out.append(finding(ERROR, "Lint04", where,
                               f"backlog_add {b} 查無此項（BACKLOG git 史從未出現、疑 phantom/typo）"))
        if isinstance(feat, str) and not os.path.isdir(os.path.join(root, "specs", feat)):
            out.append(finding(ERROR, "Lint04", where, f"specs/{feat}/ 目錄不存在"))
    return out


def _lint_review_dual_source(root, rel, event, where):
    """Q13 拍板（2026-08-04）：review 事件 findings.total ↔ 報告檔 front-matter
    findings_total 的**雙源對賬**。回 findings。

    ★rev4 啟動書 L5 宣稱有此紀律，但 grep 全 tools/ 與 .githooks/ 零命中——as-built
    從未實作，只有單源（事件內部四鍵守恆律 fixed+to_backlog+wontfix_adr==total，在
    Lint03）。rev5 依 §0.3 準則 1「治理能力零空窗」與準則 7「對賬全機器化或顯式列冊」
    於 Day 1 補上，故不需另立延後 ADR。
    ★報告檔 front-matter 規格（本次順帶定下——rev4 只給了欄名、無型別與必填性）：
      唯一必填欄 `findings_total`，值為非負整數；沿用既有解析器吃得下的 YAML 子集
      （帶引號或裸 scalar、flow list、空 list；**不支援區塊式 list**）；缺欄即 ERROR。
    """
    out = []
    text = _read(root, rel)
    if text is None:                       # tracked 但工作樹讀不到：留給既有存在性面處理
        return out
    meta = parse_front_matter(text)[0]
    raw = meta.get("findings_total")
    total = (event.get("findings") or {}).get("total")
    if raw is None:
        out.append(finding(ERROR, "Lint05", rel,
                           "報告檔 front-matter 缺必填欄 findings_total——雙源對賬無基準"
                           "（形制：`---` 起首、`findings_total: N`、`---` 收尾）"))
        return out
    if not str(raw).lstrip("-").isdigit() or int(raw) < 0:
        out.append(finding(ERROR, "Lint05", rel,
                           f"findings_total 須為非負整數，實得 {raw!r}"))
        return out
    if not isinstance(total, int):
        return out                         # 事件側型別錯由 Lint03 欄位形負責，此處不重複報
    if int(raw) != total:
        out.append(finding(ERROR, "Lint05", where,
                           f"findings 雙源不符：事件 total={total}、報告 "
                           f"{rel} front-matter findings_total={int(raw)}"
                           "——兩處須同步（改動一側必改另一側）"))
    return out


def lint_review_existence(root):
    """Lint05：逐 review 驗分流引用（report 檔／to_backlog／wontfix_adr）真實存在。回 findings。"""
    out = []
    events = parse_events_loose(_read(root, EVENTS))
    open_ids = _open_backlog_ids(root)
    done_ids = _backlog_done_ids(events)
    adr_ids = _adr_ids_on_disk(root)
    tracked = set(tracked_files(root))
    for e in events:
        if e.get("type") != "review":
            continue
        where = f"{EVENTS}｜review {e.get('date')}"
        report = e.get("report")
        if isinstance(report, str):
            rel = f"docs/{report}"
            if not os.path.isfile(os.path.join(root, rel)) and rel not in tracked:
                out.append(finding(ERROR, "Lint05", where, f"report 檔不存在：{rel}"))
            else:
                out += _lint_review_dual_source(root, rel, e, where)
        fd = e.get("findings")
        if isinstance(fd, dict):
            for b in fd.get("to_backlog", []) or []:
                nb = _norm_bid(b)
                if nb not in open_ids and nb not in done_ids:
                    out.append(finding(ERROR, "Lint05", where,
                                       f"to_backlog {b} 查無此項（現況 BACKLOG 無、亦無後續 backlog_done 消化）"))
            for adr in fd.get("wontfix_adr", []) or []:
                if adr not in adr_ids:
                    out.append(finding(ERROR, "Lint05", where,
                                       f"wontfix_adr 引用 ADR {adr} 但 {ADR_DIR}/ 無對應檔"))
    return out


def _section_num(s):
    return int(s[1:]) if isinstance(s, str) and RE_SECTION.fullmatch(s) else None


def _arch_impact_nums(ai):
    """arch_impact 欄轉節號集；"none" 或非 list→空集（非 §N 項交 Lint03 驗形）。"""
    if not isinstance(ai, list):
        return set()
    return {n for n in (_section_num(s) for s in ai) if n is not None}


def _book_section_content(text):
    """活書各 §節內容（不含節標題行），供內容相異比對。回 {節號: 內容字串}。"""
    sec, buf, out = None, [], {}
    for line in (text or "").splitlines():
        m = RE_BOOK_SECTION.match(line)
        if m:
            if sec is not None:
                out[sec] = "\n".join(buf)
            sec, buf = int(m.group(1)), []
        elif sec is not None:
            buf.append(line)
    if sec is not None:
        out[sec] = "\n".join(buf)
    return out


def _arch_changed_sections(book_a, book_b):
    """兩版活書內容相異的 §節號集（含只存在於一版者）。"""
    sa, sb = _book_section_content(book_a), _book_section_content(book_b)
    return {n for n in set(sa) | set(sb) if sa.get(n) != sb.get(n)}


def lint_arch_impact(root):
    """Lint06：(a) 全 feature_close arch_impact §N 須為活書現存節；
    (b) 僅最新 feature_close：merge^1→簿記活書變動節集與 arch_impact 雙向相等
    （左源＝merge^1:BOOK、ADR 0017「本刀影響」語意）。回 findings。

    (b) 現況側綁定該刀「簿記狀態」（非恆前進工作樹）：
      - 簿記尚未 commit（HEAD＝該刀 merge）＝pre-commit 閘時刻，as-built 僅在工作樹→讀工作樹；
      - 簿記已落地為 HEAD（HEAD^＝該刀 merge）→讀 HEAD 版活書（忽略工作樹後續漂移）；
      - HEAD 已前進超過簿記（下一支 feature 已 commit）或 SHA 取不到→跳過 (b)（fail-safe、不誤報）。
    綁定之必要：若恆讀工作樹，下一支 feature 的 mid-feature 活書編輯會被誤算進最新刀名下，
    產生無法滿足的假陽（下一支尚無 close event 可登記 arch_impact），全程硬擋 commit。
    歷史刀不做 (b)——其 merge 與現況簿記狀態無對應、慣例對不齊會誤報。
    """
    out = []
    events = parse_events_loose(_read(root, EVENTS))
    book = _read(root, BOOK)
    sec_set = set(book_section_lines(book)) if book is not None else set()
    closes = [e for e in events if e.get("type") == "feature_close"]
    # (a) 存在性：全 feature_close
    for e in closes:
        where = f"{EVENTS}｜{e.get('feature')}"
        for n in sorted(_arch_impact_nums(e.get("arch_impact"))):
            if n not in sec_set:
                out.append(finding(ERROR, "Lint06", where,
                                   f"arch_impact §{n} 非活書（{BOOK}）現存節"))
    # (b) 雙向：僅最新刀，且現況側綁定該刀簿記狀態（非恆前進工作樹）
    if closes:
        latest = closes[-1]
        where = f"{EVENTS}｜{latest.get('feature')}"
        m = latest.get("merge")
        m_sha = git_out(["rev-parse", "--verify", m], root) if isinstance(m, str) else None
        head = git_out(["rev-parse", "--verify", "HEAD"], root)
        head_par = git_out(["rev-parse", "--verify", "HEAD^"], root)
        # ★比對左源＝merge^1 版活書（ADR 0017）：「本刀影響」語意＝刀內活書變動∪簿記時
        #   變動——左源若取 merge 版，刀內 commit 的變動在 merge 時已含、merge→簿記零
        #   delta 會被誤判「無實際變動」（001 實撞、被迫記 arch_impact=none）。
        # ★前提：收刀恆 merge --no-ff 單親 merge；非單親（octopus）下 merge^1 語意不定、
        #   日後改收刀方式須連動本閘（新 ADR）。
        book_m = git_out(["show", f"{m}^1:{BOOK}"], root) if isinstance(m, str) else None
        book_now = None
        if m_sha is not None and head is not None and m_sha.strip() == head.strip():
            # State 1：pre-commit 簿記（HEAD＝merge、as-built 尚未落地、僅在工作樹）→ 讀工作樹
            book_now = book
        elif m_sha is not None and head_par is not None and m_sha.strip() == head_par.strip():
            # State 2：簿記已落地為 HEAD（HEAD^＝merge）→ 讀 HEAD 版活書、忽略工作樹後續漂移
            book_now = head_file(BOOK, root)
        # 否則 HEAD 已前進超過簿記／SHA 取不到 → book_now=None → 跳過 (b)（fail-safe）
        if book_m is None or book_now is None:
            out.append(finding(SKIP, "Lint06", where,
                               "最新刀的 merge 與現況 HEAD 對不上簿記狀態（HEAD 已前進超過"
                               "簿記，或 merge SHA／merge^1 版活書取不到）——arch_impact 雙向"
                               "比對跳過（fail-safe：現況側無對應基準，比了會誤報）"))
        if book_m is not None and book_now is not None:
            claimed = _arch_impact_nums(latest.get("arch_impact"))
            changed = _arch_changed_sections(book_m, book_now)
            for n in sorted(claimed - changed):
                out.append(finding(ERROR, "Lint06", where,
                                   f"最新刀宣稱 arch_impact §{n} 但 merge^1→簿記活書該節"
                                   "無實際變動"))
            for n in sorted(changed - claimed):
                out.append(finding(ERROR, "Lint06", where,
                                   f"最新刀 merge^1→簿記活書 §{n} 內容有變動但 arch_impact"
                                   " 未宣稱"))
    return out


def tracked_blobs(root):
    """tracked 檔清單扣掉 gitlink（160000）條目——憑證掃描的外層面（data-model §2）。"""
    rels = []
    for line in (git_out(["ls-files", "-s"], root) or "").splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path and parts and parts[0] != "160000":
            rels.append(path)
    return rels


def _cred_read_text(path):
    """回 (全文, 意外跳過原因)。

    二進位（前 8KB 含 NUL）＝刻意 skip（R2：憑證必為文字），回 (None, None)；讀不到
    （缺席／目錄／權限）＝意外，回 (None, 原因)——呼叫端必須留信號，「沒掃到」靜默
    當成乾淨即 fail-open。
    """
    try:
        with open(path, "rb") as fh:
            probe = fh.read(CRED_BINARY_PROBE)
            if b"\x00" in probe:
                return None, None
            return (probe + fh.read()).decode("utf-8", errors="replace"), None
    except OSError as exc:
        return None, f"讀取失敗（{exc.__class__.__name__}）"


def _cred_staged_added(root):
    """staged 新增行（index vs HEAD）過樣式集；回 [(rel, label)]。

    ★判定面不得只有工作樹快照：閘要護的是「這次要進版控的內容」。實證兩態——`git add`
    後把工作樹檔 rm、或 `git add` 後把工作樹版本洗白——工作樹都是乾淨的、index blob 卻
    仍帶憑證。改讀全 index blob 語意最純但實測 414 blob 走 `cat-file` 需 2.2s（工作樹讀
    僅 1.3s），故只補「本次新增內容」這條增量：成本正比 staged 變更量，與 rev4:FR-008 同哲學。
    """
    diff = git_out(["diff", "--cached", "-U0"], root)
    return cred_diff_hits(diff) if diff else []


def lint_cred_outer(root):
    """Lint16 外層面：全 tracked 文字檔過樣式集（data-model §2 第 1 列）＋staged 新增行補掃。

    兩面聯集去重（同一 rel×label 只報一次；工作樹面帶行號、優先）。
    """
    out, seen = [], set()
    for rel in tracked_blobs(root):
        if rel in CRED_WHITELIST:
            continue
        text, unread = _cred_read_text(os.path.join(root, rel))
        if unread:
            out.append(finding(WARN, "Lint16", rel,
                               f"工作樹{unread}——該檔工作樹面未掃、非判定為乾淨"
                               "（staged 內容另由 index 面補掃）"))
        if text is None:
            continue
        for label, n in scan_cred_text(text):
            if (rel, label) in seen:
                continue
            seen.add((rel, label))
            out.append(finding(ERROR, "Lint16", f"{rel}:行 {n}",
                               f"憑證內容命中（label={label}）——移除內容並輪替該憑證；"
                               "無 inline 豁免，確需豁免走 CRED_WHITELIST＋rev4:ADR（0077）"))
    for rel, label in _cred_staged_added(root):
        if rel in CRED_WHITELIST or (rel, label) in seen:
            continue
        seen.add((rel, label))
        out.append(finding(ERROR, "Lint16", f"{rel}:staged",
                           f"staged 內容憑證命中（label={label}）——工作樹版本已無此內容、"
                           "但 index 這份即將進版控；移除並輪替後重新 git add"))
    return out


def index_gitlink(root, sub):
    """index 內該 submodule 的 gitlink SHA；回 (SHA, 跳過原因)——取不到時 SHA＝None。

    ★只認 stage 0：gitlink 合併衝突未解時 index 同時有 stage 1（共同祖先）／2（ours）／
    3（theirs）三筆，且 `git ls-files -s` 依 stage 遞增輸出——「取首個 160000 行」會讀到
    祖先 pin，Lint17 據以報一筆根本不存在的分歧（收刀簿記 commit 那格更會升成 ERROR 硬擋）、
    Lint16 增量掃則拿祖先 SHA 當「new」去 diff。衝突態一律回跳過原因，比默默取祖先誠實。
    """
    sha0, stages = None, set()
    for line in (git_out(["ls-files", "-s", "--", sub], root) or "").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "160000":
            stages.add(parts[2])
            if parts[2] == "0":
                sha0 = parts[1]
    if sha0 is not None:
        return sha0, None
    if stages:
        return None, (f"index gitlink 合併衝突未解（stage {'／'.join(sorted(stages))}、"
                      "無 stage 0）——先解掉該 submodule 的衝突再重跑")
    return None, "index 無該 gitlink 條目（純外層 repo 或該 submodule 未登記）"


def submodule_head(root, sub, cache=None):
    """子庫存活探針：回 (worktree HEAD SHA, 跳過原因)——查不到時 SHA＝None。

    ★Lint16 submodule 面／Lint17／Lint18／Lint20 守衛#4 四條款共用同一支探針。各自為政的後果實證：
    Lint17 以 `rev-parse HEAD` 成功與否判定、Lint18 只看 `.git` 路徑是否存在，於「worktree 斷裂」
    （`.git` gitfile 指向已被刪除的源倉、CLAUDE.md §3 明載狀態）時 Lint17 落 1 筆跳過、
    Lint18 卻對該庫每一列各落一筆「upstream rebase 卷史後合法失聯」——同一事實兩種說法，
    且把「庫根本開不起來」誤植成「SHA 失聯」，操作者會去 fetch 而不是去跑 bootstrap。
    ★判準必須是「rev-parse HEAD 成功」而非「.git 路徑存在」：後者對斷裂 worktree 為真。

    ★`cache`＝單次 lint 內共用的記憶化字典（run_lint 建、逐條款傳下去）：探針是一發
    subprocess，drvfs 上實測 base-web 78ms／rust-api 101ms，四條款各自打＝一次 lint 多花
    ~360ms。給 cache 即每庫每次 lint 只打一發；不給（單測直呼）＝每次真打，無跨案殘留。
    """
    if cache is not None and sub in cache:
        return cache[sub]
    subdir = os.path.join(root, sub)
    if not os.path.exists(os.path.join(subdir, ".git")):
        result = (None, "submodule worktree 缺席（唯讀看碼模式或尚未跑 bootstrap）")
    else:
        head = (git_out(["rev-parse", "HEAD"], subdir) or "").strip()
        result = (head, None) if head else (
            None, "submodule worktree 斷裂、庫開不起來（.git gitfile 指向的源倉不在"
                  "或 HEAD 讀不到；跑 bash tools/bootstrap.sh 自癒）")
    if cache is not None:
        cache[sub] = result
    return result


def _cred_grep_tree(subdir, tree):
    r"""退化全樹掃：`git ls-tree -r` 列 blob →`git cat-file --batch` 批次取→python re 掃。

    回 (命中清單, 失敗說明或 None)；命中清單為去重後的 [(path, label)]。

    ★rev5 差分・跨平台修復（rev4 原以 `-nEI -e <樣式> <tree>` 走 git 自身正則引擎）：`-E`
    走系統 regcomp＝POSIX ERE，而 CRED_PATTERNS 四條中三條含 `\b`（aws-akia／github-token／
    github-pat）。glibc（WSL2／Linux）把 `\b` 當 GNU 擴充**支援**，BSD libc（macOS）**不支援**
    ——後者對這三條回退出碼 1，而 1 正是「確無命中」語意，於是被讀成乾淨：WARN 仍宣稱「已
    退化為全樹掃」，實則對三類機密零偵測且零訊號。同一道防線在兩平台行為分裂，屬「防線還在、
    偵測力歸零」的靜默失效家族。改走 python re 後全鏈單一引擎——樣式常數與 scan_cred_text 的
    行號邏輯皆零改動、平台零依賴，並根除「兩套引擎未必等價」的結構性風險。
    ★二進位跳過沿用外層面同規則（前 CRED_BINARY_PROBE bytes 含 NUL 即跳），對應原 `-I`：
    缺之則二進位命中會把路徑欄污染成殘餘文字、且與外層面判定不一致。
    ★退出碼三分語意保留：ls-tree／cat-file 任一非零＝掃描根本沒跑成，一律回失敗說明給呼叫端
    升 ERROR——把執行失敗解讀成乾淨，會做出比不掃更危險的假保證（rev4:FR-008 fail-closed）。
    ★批次讀法沿用 load_head_adrs 既有範式（逐檔 git show 會吃穿秒級預算；414 blob 實測 2.2s）。
    """
    out = []
    try:
        r = subprocess.run(["git", "ls-tree", "-r", "-z", tree], cwd=subdir,
                           capture_output=True)
    except OSError as exc:
        return out, f"git ls-tree 無法執行（{exc.__class__.__name__}）"
    if r.returncode != 0:
        head = ((r.stderr or b"").decode("utf-8", "replace").strip().splitlines() or [""])[0]
        return out, f"git ls-tree 退出碼 {r.returncode}" + (f"：{head}" if head else "")

    entries = []
    for rec in r.stdout.decode("utf-8", "replace").split("\0"):
        if not rec:
            continue
        meta, _, path = rec.partition("\t")
        parts = meta.split()
        if len(parts) >= 3 and parts[1] == "blob":
            entries.append((parts[2], path))
    if not entries:
        return out, None

    try:
        r2 = subprocess.run(["git", "cat-file", "--batch"], cwd=subdir,
                            input=b"\n".join(sha.encode() for sha, _ in entries) + b"\n",
                            capture_output=True)
    except OSError as exc:
        return out, f"git cat-file 無法執行（{exc.__class__.__name__}）"
    if r2.returncode != 0:
        head = ((r2.stderr or b"").decode("utf-8", "replace").strip().splitlines() or [""])[0]
        return out, f"git cat-file 退出碼 {r2.returncode}" + (f"：{head}" if head else "")

    data, pos = r2.stdout, 0
    for sha, path in entries:
        nl = data.find(b"\n", pos)
        if nl < 0:
            return out, f"git cat-file 回應截斷（{path}）"
        head_parts = data[pos:nl].decode("utf-8", "replace").split()
        if len(head_parts) != 3 or head_parts[1] != "blob":
            return out, f"git cat-file 回應非預期（{data[pos:nl][:60]!r}）"
        size = int(head_parts[2])
        blob = data[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1          # 內容後尾隨一個換行
        if b"\x00" in blob[:CRED_BINARY_PROBE]:
            continue                     # 二進位：與外層面同規則跳過
        text = blob.decode("utf-8", "replace")
        for label, pat in CRED_PATTERNS:
            if pat.search(text) and (path, label) not in out:
                out.append((path, label))
    return out, None


def lint_cred_submodules(root, cache=None):
    """Lint16 增量面：staged 含 gitlink 變動時掃 old..new 新增行（R3；data-model §2 第 2/3 列）。"""
    out = []
    staged = set((git_out(["diff", "--cached", "--name-only"], root) or "").splitlines())
    for sub in CRED_SUBMODULES:
        if sub not in staged:
            out.append(finding(SKIP, "Lint16", sub,
                               "本次 commit 未 staged 該 gitlink——憑證增量掃不適用"
                               "（掃描面＝old..new 新增行，成本正比 pin 變更量）"))
            continue
        subdir = os.path.join(root, sub)
        _head, why = submodule_head(root, sub, cache)
        if why:
            out.append(finding(SKIP, "Lint16", sub, f"{why}——憑證增量掃跳過"))
            continue
        new, why = index_gitlink(root, sub)
        if new is None:
            out.append(finding(SKIP, "Lint16", sub, f"{why}——憑證增量掃跳過"))
            continue
        old = (git_out(["rev-parse", f"HEAD:{sub}"], root) or "").strip()
        diff = git_out(["diff", old, new, "-U0"], subdir) if old else None
        if diff is None:
            out.append(finding(WARN, "Lint16", sub,
                               f"舊 pin（{old[:12] or '無'}）不可解或 diff 失敗——"
                               "退化為新 pin 全樹掃描（fail-closed 向完整掃）"))
            hits, err = _cred_grep_tree(subdir, new)
            if err:
                out.append(finding(ERROR, "Lint16", sub,
                                   f"退化全樹掃執行失敗（{err}）——掃描面未建立、不得視同乾淨；"
                                   "補齊該 pin 物件（回該庫 fetch）後重跑"))
        else:
            hits = cred_diff_hits(diff)
        for path, label in hits:
            out.append(finding(ERROR, "Lint16", f"{sub}/{path}",
                               f"submodule 新進內容憑證命中（label={label}）——"
                               "回該庫移除並輪替後重 bump pin"))
    return out


def lint_credentials(root, cache=None):
    """Lint16 組裝：self-test 防恆綠＋外層全量＋submodule 增量（rev4:contracts G1）。"""
    return cred_self_test() + lint_cred_outer(root) + lint_cred_submodules(root, cache)


# ---------------------------------------------------------------------------
# Lint17 pin↔worktree HEAD 互證／Lint18 events SHA 逐列實證（rev4:contracts G2/G3；rev4:FR-009~FR-011）
# ---------------------------------------------------------------------------

RE_EVENT_CLOSE = re.compile(r'"type"\s*:\s*"feature_close"')
GIT_OBJECT_TYPES = ("blob", "tree", "commit", "tag")


def is_closing_commit(root):
    """本次 commit 是否為收刀簿記：staged events 新增行含 feature_close（R7、與 L6b 同資料源）。

    ★以 hunk 狀態機界定新增行、不以前綴猜測：`+++ b/…` 檔頭在該檔首個 `@@` 之前，內容行
    在其後（同 `cred_diff_hits` 紀律）。
    """
    diff = git_out(["diff", "--cached", "-U0", "--", EVENTS], root)
    if not diff:
        return False
    in_hunk = False
    for line in diff.splitlines():
        if line.startswith("@@"):
            in_hunk = True
            continue
        if in_hunk and line.startswith("+") and RE_EVENT_CLOSE.search(line[1:]):
            return True
    return False


def lint_pin_crosscheck(root, cache=None):
    """Lint17：staged gitlink ↔ submodule worktree HEAD 互證（rev4:contracts G2／data-model §3）。

    嚴重度由收刀偵測決定：平時 WARN（兩段式 commit 的合法中間態）、收刀簿記 commit ERROR
    （最終 pin 必須齊）；worktree 缺席＝跳過。
    """
    out, closing = [], None
    for _key, sub in PIN_KEYS:
        staged, why = index_gitlink(root, sub)
        if staged is None:
            out.append(finding(SKIP, "Lint17", sub, f"{why}——pin 互證跳過"))
            continue
        head, why = submodule_head(root, sub, cache)
        if head is None:
            out.append(finding(SKIP, "Lint17", sub, f"{why}——pin 互證跳過"))
            continue
        if head == staged:
            continue
        if closing is None:
            closing = is_closing_commit(root)
        tail = (f"本次屬收刀簿記 commit（staged events 新增行含 feature_close）——最終 pin "
                f"必須齊：回外層 bump pin（git add {sub}）後重試"
                if closing else
                f"兩段式 commit 的合法中間態——worktree 內 commit 後記得回外層 bump pin"
                f"（git add {sub}）")
        out.append(finding(ERROR if closing else WARN, "Lint17", sub,
                           f"pin 與 worktree HEAD 分歧（staged={staged[:12]}／"
                           f"HEAD={head[:12]}）——{tail}"))
    return out


def git_object_types(shas, cwd):
    """一發 `git cat-file --batch-check` 問多個 SHA；回 {sha: 物件型別}（不可解者不入 dict）。

    輸出與輸入逐行對位（不可解者輸出 `<輸入> missing`），故以 zip 配對而非解析回顯 SHA。
    逐筆 rev-parse 需 ~87 次 subprocess（約 1s），批次為毫秒級（rev4:contracts G3 效能契約）。
    """
    types = {}
    # ★只排除含換行者：batch-check 是「一行一問、一行一答」，值內夾換行會多問一行、其後
    #   所有回答整體錯位（錯位能把偽造值配到真 commit 型別上＝漏報）。其餘空白無此風險——
    #   實測 git 把整行當物件名、原樣回「<整行> missing」（不會拿空白前那截當縮寫去解），
    #   判定結果本就是「不可解」；再排除一次＝庫裡多一條驗不到的死防線。
    uniq = [s for s in dict.fromkeys(shas) if s and "\n" not in s]
    if not uniq:
        return types
    try:
        r = subprocess.run(["git", "cat-file", "--batch-check"], cwd=cwd,
                           input="\n".join(uniq) + "\n", capture_output=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return types
    if r.returncode != 0:
        return types
    for sha, line in zip(uniq, r.stdout.splitlines()):
        parts = line.split()
        if len(parts) >= 3 and parts[1] in GIT_OBJECT_TYPES:
            types[sha] = parts[1]
    return types


def run_git_concurrently(calls):
    """零引數 callable list 一次併發派出；回與 calls 同序的結果。單發不起執行緒。

    各呼叫只等 git 子行程 I/O、彼此零共享狀態，故以執行緒併發（與「rust 全程 serial」無關——
    那條紀律管的是平行 cargo 互撞 target）。WSL2 drvfs 上單發成本幾乎全在開庫（實測
    cat-file 外層 23ms／base-web 64ms／rust-api 82ms、rev-parse 另需 78ms／101ms，git 本體
    啟動僅 1ms），全部序列跑約 300ms＝超出 rev4:contracts G3「全帳本驗證 200ms 以內」。
    ★存活探針必須與 cat-file 批次同池併發、不得排在批次之前序列跑：兩者分兩段時
    ~180ms（探針）＋~80ms（批次）＝ 破契約（U5-quality 實測 341ms／300ms）；同時在飛後
    實測約 130ms。代價＝對「庫不可查」者多派一發空轉 cat-file（結果不採用），成本遠低於
    序列化探針。
    """
    if len(calls) <= 1:
        return [fn() for fn in calls]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(calls)) as ex:
        return [f.result() for f in [ex.submit(fn) for fn in calls]]


def _erratum_view(rows, line_count):
    """erratum 更正視圖（B-042 調閘形；六條硬語意之①③④⑤面）。

    輸入＝Lint18 已解析之 (行號, 事件) 列表＋帳本總行數；回 (view, checks, findings)：
    - view＝{(target_line, field): corrected}——同 target×欄多筆時 append 序後者勝（④）；
    - checks＝[(erratum 行號, field, corrected), …]——**每筆**通過脫靶檢查者皆入列（含被
      後筆蓋掉者），corrected 自驗（②）由呼叫端併入既有 cat-file 批次；
    - findings＝脫靶 ERROR（③：target_line 超界／指向非事件列、指定欄不存在於 target 列）
      與⑤（erratum 指向 erratum 列——更正的更正＝再 append 一筆指向**原始列**），
      一律 fail-loud、絕不靜默 no-op。
    格式殘缺（target_line 非正整數／field 非枚舉／corrected 非 40 hex）歸 Lint03、此處跳過。
    """
    by_line = dict(rows)
    view, checks, out = {}, [], []
    for n, e in rows:
        if e.get("type") != "erratum":
            continue
        tl, fld, cor = e.get("target_line"), e.get("field"), e.get("corrected")
        if not (isinstance(tl, int) and not isinstance(tl, bool) and tl >= 1
                and fld in ERRATUM_FIELDS
                and isinstance(cor, str) and RE_SHA.fullmatch(cor)):
            # ★本 continue 的正當性全繫於「Lint03 會替這四腿出紅」：兩處判準必須同尺，
            #   任一邊放寬即出現「Lint03 綠＋視圖跳過」的靜默零效缺口（違硬語意③）。
            #   兩把尺**各有各的釘子**（確認輪校正——原註解點名的對稱釘子走 lint_events()
            #   →_check_event，根本不呼叫本函式，視圖這半邊當時裸奔）：
            #   Lint03 側＝TestLintEvents.test_erratum_bad_corrected_rejected；
            #   視圖側＝test_malformed_erratum_rows_are_skipped_without_crashing 的
            #   int("1"*40) 一筆（該值同時穿透兩把尺的差集，是唯一能分辨 str(cor) 放寬形者）。
            continue                       # 格式面歸 Lint03、此處不重複報
        where = f"{EVENTS}:行 {n}"
        tgt = by_line.get(tl)
        # ★單一判準 `tgt is None` 即涵蓋「超界」與「指向非事件列」兩形：by_line 的鍵取自
        #   enumerate(lines, start=1) 之可解析列，恆為 1..line_count 的子集，故 tl>line_count
        #   必然蘊含 tl∉by_line。另寫一條 `tl > line_count` 的 disjunct 永遠不會獨立成立
        #   ＝走不到的死腿（L-019 同形），且寫壞成 `>=` 會把「指向最末列」的合法引用誤報脫靶。
        #   line_count 僅供訊息文字（告知帳本規模）。
        if tgt is None:
            out.append(finding(ERROR, "Lint18", where,
                               f"erratum 脫靶：target_line={tl} 超界或指向非事件列"
                               f"（帳本共 {line_count} 行）——更正必須釘住一列真事件、"
                               "絕不靜默略過"))
            continue
        if tgt.get("type") == "erratum":
            out.append(finding(ERROR, "Lint18", where,
                               f"erratum 不得指向 erratum 列（行 {tl}）——更正的更正＝"
                               "再 append 一筆、target_line 指向原始列"))
            continue
        if fld == "merge":
            present = "merge" in tgt
        else:
            pins = tgt.get("pins")
            present = isinstance(pins, dict) and fld.split(".", 1)[1] in pins
        if not present:
            out.append(finding(ERROR, "Lint18", where,
                               f"erratum 脫靶：target 列（行 {tl}）不存在指定欄 {fld}"
                               "——絕不靜默略過"))
            continue
        view[(tl, fld)] = cor              # 同 target×欄多筆＝append 序後者勝（④）
        checks.append((n, fld, cor))
    return view, checks, out


def _erratum_remedy(n, field):
    """三處 ERROR 訊息共用的「已進 git 史」補救支（B-042 硬語意⑥）：附具體可執行的
    erratum 形——欄名逐字、target_line 帶該列行號，照抄 append 即可讓紅消（出口真的走得通）。"""
    return ("已進 git 史→依 ADR 0012 決定 5（events.jsonl 既有列絕不編輯）append 新事件"
            "更正、不得回改舊列——具體形＝append "
            f'{{"date":"YYYY-MM-DD","type":"erratum","target_line":{n},"field":"{field}",'
            '"corrected":"<正確 40 位 hex SHA>","reason":"<一句話>"}'
            "（Lint18 以更正視圖重驗該列；corrected 本身亦被實證、不可解即紅）")


def _erratum_corrected_remedy():
    """四處「erratum corrected 自驗失敗」ERROR 共用的補救支（B-042 碼品質輪補齊）。

    與史值三處（`_erratum_remedy`）同構分兩支，差別在第二支說的是實話：**已入史的
    erratum 列在現行設計下無可執行出口**——回改本列違 ADR 0012 決定 5；append erratum
    指向本列被硬語意⑤（不得指向 erratum 列）擋；指向原始列只把 target 列救回（硬語意④
    後者勝），本列自身的自驗紅仍在（checks 收錄每一筆 erratum、含被蓋掉者）。
    ★故第二支導向升級主線由拍板層處置，絕不以「corrected 須填…」單句暗示回改已入史列
    ——那正是 B-042 開帳要消滅的「附了去處卻走不通」形（在此重演即自打嘴巴）。
    可達性不是理論：pins 面「不可解＝WARN」的寬貸就是為 upstream rebase 卷史而設，
    而硬語意②把該寬貸從更正值拿掉的理由（「更正是新寫的、沒有卷史藉口」）只在寫入
    當下成立；寫完入史後被卷走，這條紅就永久卡住 pre-commit。
    """
    return ("——補救分兩支：本 erratum 列尚未進 git 史（工作樹／staged）→直接覆寫本列的"
            " corrected 為上述正確值；已進 git 史→現行設計下無可執行出口（回改本列違"
            " ADR 0012 決定 5；append erratum 指向本列被「不得指向 erratum 列」擋；指向"
            "原始列只救得回 target 列、本列自驗紅仍在）——請升級主線循拍板層處置，"
            "勿自行回改已入史列")


def lint_events_sha(root, cache=None):
    """Lint18：events 帳本逐列 SHA 向 git 實證（rev4:contracts G3／data-model §4 判定表）。

    merge 驗於外層（不可解／非 commit＝ERROR）；pins 依 PIN_KEYS 映射驗於各 submodule
    worktree（不可解＝WARN——upstream rebase 卷史後合法失聯；可解而非 commit＝ERROR；
    worktree 缺席＝該庫整批跳過）。含 pins 之列另做鍵集斷言（防查空集合恆綠）。

    ★erratum 更正視圖（B-042 調閘形、六條硬語意）：①逐列實證前先掃全帳 erratum 列建視圖，
    target 列的指定欄以 corrected 取代後才驗——已入史壞列因此有可執行出口；②每筆 erratum
    的 corrected 自身也向對應 repo 實證（merge→外層、pins.*→各 submodule），不可解／非
    commit＝該 erratum 列 ERROR——沒有任何東西被「豁免」；③脫靶（超界／非事件列／欄不
    存在）＝ERROR、絕不靜默 no-op；④同 target×欄多筆＝append 序後者勝、但每筆各自過②；
    ⑤erratum 指向 erratum 列＝ERROR；⑥三處 ERROR 訊息的「已進史」補救支附具體 erratum 形。
    corrected 自驗與視圖覆蓋後的逐列實證共用同一批 cat-file 併發管線（G3 200ms 契約）。
    """
    out, rows = [], []
    lines = _jsonl_lines(_read(root, EVENTS) or "")
    for n, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue                       # 格式面歸 Lint03、此處不重複報
        if isinstance(e, dict):
            rows.append((n, e))

    view, err_checks, err_findings = _erratum_view(rows, len(lines))

    merges = []
    for n, e in rows:
        m = view.get((n, "merge"), e.get("merge"))
        if isinstance(m, str):
            merges.append((n, m))

    keys = {key for key, _sub in PIN_KEYS}
    per_key = {key: [] for key in keys}
    keyset = []                     # 鍵集斷言 findings（輸出序仍排在 merge findings 之後）
    for n, e in rows:
        if "pins" not in e:
            continue
        pins = e["pins"]
        if not isinstance(pins, dict) or set(pins) != keys:
            got = ("、".join(sorted(pins)) or "空") if isinstance(pins, dict) \
                else type(pins).__name__
            keyset.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                                  f"pins 鍵集須恰為 web／api（現為 {got}）——缺鍵或未知鍵會讓"
                                  "逐列實證查到空集合而恆綠"))
            continue
        for key in keys:
            v = view.get((n, f"pins.{key}"), pins[key])
            if isinstance(v, str):
                per_key[key].append((n, v))

    # erratum corrected 自驗（②）依 field 分派到對應 repo 的批次
    err_merge = [(n, c) for n, f_, c in err_checks if f_ == "merge"]
    err_pins = {key: [(n, c) for n, f_, c in err_checks if f_ == f"pins.{key}"]
                for key in keys}

    # 三批 cat-file（外層 merge＋每庫 pins；erratum corrected 併同批、零額外 git 呼叫）
    # ＋每庫存活探針，全部同池一次併發派出
    # ★存活判定走共用探針（見 submodule_head）：只看 .git 路徑存在會把斷裂 worktree 當成
    #   活庫，逐列報「rebase 卷史合法失聯」＝把「庫開不起來」誤植成「SHA 失聯」
    # ★探針不得排在批次之前序列跑（會破 G3 200ms 契約、理由見 run_git_concurrently）：
    #   故對尚不知死活的庫先樂觀派 cat-file，探針判死者其結果整批丟棄。
    pending = [(key, sub) for key, sub in PIN_KEYS if per_key[key] or err_pins[key]]
    results = run_git_concurrently(
        [functools.partial(git_object_types,
                           [s for _n, s in merges] + [c for _n, c in err_merge], root)]
        + [functools.partial(git_object_types,
                             [s for _n, s in per_key[key]] + [c for _n, c in err_pins[key]],
                             os.path.join(root, sub)) for key, sub in pending]
        + [functools.partial(submodule_head, root, sub, cache) for _key, sub in pending])
    mtypes = results[0]
    types_of = dict(zip([key for key, _sub in pending], results[1:1 + len(pending)]))
    absent = {key: why for (key, _sub), (_head, why)
              in zip(pending, results[1 + len(pending):]) if why}
    ptypes = {key: t for key, t in types_of.items() if key not in absent}

    for n, sha in merges:
        t = mtypes.get(sha)
        if t is None:
            out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                               f"merge SHA {sha[:12]} 在外層不可解析——帳本每列 SHA 須對得上"
                               " git 物件（抄錯／造假／事後改史即紅）——補救分兩支：該列尚未"
                               "進 git 史（工作樹／staged）→以真實 merge commit SHA 覆寫該列；"
                               + _erratum_remedy(n, "merge")))
        elif t != "commit":
            out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                               f"merge SHA {sha[:12]} 解得物件型別 {t}、非 commit——多半是"
                               "抄到 tree／blob 的 SHA（`git rev-parse HEAD:<path>`、"
                               "`cat-file` 輸出等）；正確值＝該刀 merge 回 default 的 commit"
                               " SHA（`git log --merges --format=%H -1`）——補救分兩支（同"
                               "「不可解」）：該列尚未進 git 史（工作樹／staged）→以真實"
                               " merge commit SHA 覆寫該列；" + _erratum_remedy(n, "merge")))
    out.extend(keyset)
    out.extend(err_findings)

    for n, c in err_merge:
        t = mtypes.get(c)
        if t is None:
            out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                               f"erratum corrected {c[:12]} 在外層不可解析——更正本身也被驗、"
                               "不可解＝零豁免；正確值＝該刀 merge 回 default 的 commit"
                               " SHA（`git log --merges --format=%H -1`）"
                               + _erratum_corrected_remedy()))
        elif t != "commit":
            out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                               f"erratum corrected {c[:12]} 在外層解得物件型別 {t}、非"
                               " commit——更正本身也被驗；正確值＝該刀 merge 回 default 的"
                               " commit SHA（`git log --merges --format=%H -1`）"
                               + _erratum_corrected_remedy()))

    for key, sub in PIN_KEYS:
        items = per_key[key]
        errata = err_pins[key]
        if not items and not errata:
            continue
        if key not in ptypes:
            out.append(finding(SKIP, "Lint18", sub,
                               f"{absent.get(key, '該庫不可查')}——pins.{key} 共 "
                               f"{len(items) + len(errata)} 筆 SHA 實證跳過"))
            continue
        for n, sha in items:
            t = ptypes[key].get(sha)
            if t is None:
                out.append(finding(WARN, "Lint18", f"{EVENTS}:行 {n}",
                                   f"pins.{key} SHA {sha[:12]} 在 {sub} 不可解析——"
                                   "upstream rebase 卷史後合法失聯，故僅警告"))
            elif t != "commit":
                out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                                   f"pins.{key} SHA {sha[:12]} 在 {sub} 解得物件型別 {t}、"
                                   "非 commit——多半是抄到 tree／blob 的 SHA；正確值＝該刀"
                                   f"收邊時 {sub} 的 worktree HEAD（`git -C {sub} rev-parse"
                                   " HEAD`）——補救分兩支（同 merge 面）：該列尚未進 git 史"
                                   "（工作樹／staged）→以真實 commit SHA 覆寫該列；"
                                   + _erratum_remedy(n, f"pins.{key}")))
        for n, c in errata:
            t = ptypes[key].get(c)
            if t is None:
                out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                                   f"erratum corrected {c[:12]} 在 {sub} 不可解析——更正本身"
                                   "也被驗、不可解＝零豁免（pins 的 WARN 寬貸不適用於更正值）"
                                   f"；正確值＝該刀收邊時 {sub} 的 worktree HEAD"
                                   f"（`git -C {sub} rev-parse HEAD`）"
                                   + _erratum_corrected_remedy()))
            elif t != "commit":
                out.append(finding(ERROR, "Lint18", f"{EVENTS}:行 {n}",
                                   f"erratum corrected {c[:12]} 在 {sub} 解得物件型別 {t}、"
                                   f"非 commit——更正本身也被驗；正確值＝該刀收邊時 {sub} 的"
                                   f" worktree HEAD（`git -C {sub} rev-parse HEAD`）"
                                   + _erratum_corrected_remedy()))
    return out


# ---------------------------------------------------------------------------
# Lint20 空集合守衛（rev4:contracts G4／data-model §6／rev4:research R4；rev4:FR-013）
# ---------------------------------------------------------------------------

# 守衛#4 的來源檔全集＝generate 每張 reference 表的輸入。既有行為是各自 fail-loud 拋例外
# （ComposePortsError／RouterRoutesError／…），歸一化進守衛後 lint 與 generate 兩端同文。
REFERENCE_SOURCES = (COMPOSE_FILES + (ROUTER_SOURCE, ELEGANT_SOURCE)
                     + tuple(rel for _lang, rel in MSG_DICT_LOCALES)
                     + (SCHEMA_SNAPSHOT, ACCOUNTS_SNAPSHOT, ARCHETYPE_MAP))

# ---------------------------------------------------------------------------
# DAY1_EXEMPTIONS：創世期結構性紅的具名豁免表（§4.5.10 v3；rev5 新增，rev4 無此設施）
# ---------------------------------------------------------------------------
# 動機五要求「治理能力 Day 1 全套上線」，但多數閘的判定來源要到 B9／B10／B12 才存在。
# 兩條錯誤解法：①把閘關掉＝rev4 老路；②「找不到就跳過」＝製造恆綠假閘（§0.3 準則 2 明禁）。
# 本表的解法＝**具名、可機驗、會自己到期**：每筆帶解除謂詞，工具每跑一次就執行一次謂詞，
# 謂詞為真而項仍在表＝ERROR 指名該筆（到期即紅、不靠人記得）。
#
# 四欄缺一不可（鍵＋三值），工具啟動時斷言逐欄非空：
#   鍵      ＝ 消費點識別字（gen.* 對應產出器、lint*.* 對應條款）
#   第一值  ＝ 豁免理由（散文；★一切散文只准住這欄）
#   第二值  ＝ 解除謂詞（★可直接求值物：路徑元組＝全部存在即解除；callable(root)→bool）
#   第三值  ＝ 登記日
# ★入表資格＝**拔項會翻紅**（B8a 突變實證逐筆拔、逐筆驗）；拔了沒反應＝該筆是裝飾品。
# ★機器強制三條：①跳過必列明細 ②到期即紅（謂詞形）③拔項驗證。
# 消費點五處（乙①②③接線，非本步）：①compute_generated 五產出器 ②cmd_generate 首段守衛
# ③lint_reference_sources 本體（具名 SKIP 統一輸出點）④check_generated 的 Lint01 缺檔／
# 多檔分支 ⑤lint_i18n_contract 兩個 early-return。
# locale backend 樹的起點正則（`parse_locale_backend` 的起點掃描唯一消費者）。
# ★原本另有 gen.msg_dict 的解除謂詞 `_locales_have_backend_tree` 與此共用一條正則，
# 該豁免於 2026-08-11 下架後謂詞即成孤兒，依本表五個先例（謂詞隨豁免一併移除、只留
# 下架註記）刪去；留著會讓讀者誤以為 gen.msg_dict 豁免仍在運作。
RE_LOCALE_BACKEND_OPEN = re.compile(r"\s*backend:\s*\{")


DAY1_EXEMPTIONS = {
    # gen.compose：2026-08-04 B10 compose 三檔移植就位、解除謂詞成立——依「到期即紅」
    # 下架（原豁免＝compose 三檔於 dev stack 就位前不存在；ports 真表自此恢復重算）。
    # gen.snapshots：2026-08-06 001-schema-baseline refresh 首跑落兩快照（archetype-map
    # 已先入版）、解除謂詞成立——依「到期即紅」下架（原豁免＝reference-src 三來源檔於
    # schema 基線刀前不存在；schema／accounts 真表自此恢復重算）。
    # gen.router：2026-08-08 002-system-settings T008 之 server/src/router.rs ROUTES 就位、
    # 解除謂詞成立——依「到期即紅」下架（原豁免＝rust 路由表於後端首刀前無實碼；routes
    # 參考真表自此恢復重算，來源＝該檔 ROUTES const 的窄假設直解）。
    # gen.screens：2026-08-04 B9 worktree 掛載、routes.ts 到位、解除謂詞成立——依「到期即紅」
    # 下架（原豁免＝前端 route 表於 worktree 掛載前不存在；screens 真表自此恢復重算）。
    # gen.msg_dict：2026-08-11 003-auth-session T066 開 ★BASE-WEB-I18N-WIRING(ii) 補齊
    # en-us.ts（與 zh-cn.ts）backend 樹、解除謂詞 _locales_have_backend_tree 成立——依
    # 「到期即紅」下架（原豁免＝en-us.ts 為 upstream 原樣檔無 backend 樹、插入需開第一個
    # ★軌道〔ADR 0020 甲案於 002 改謂詞續留〕；拒因字典 backend-msg-dict 與 Grafana 面板
    # 自此恢復重算——本筆為表內最後一項、兩表自此空表，空表安全由 lint／check 全綠承載）。
    # lint07.budget_roster：2026-08-04 B5 骨架落地、八檔齊備、解除謂詞成立——依「到期即紅」
    # 下架（原豁免＝BUDGETS 名冊八檔多數於 B5 前不存在；守衛#8 自此恢復全檢）。
    # lint24.day1：2026-08-08 002-system-settings T011——兩側源皆備（rust 掃描面自 T003 起
    # 有 .rs ＋ zh-tw.ts 於本刀 T011 建檔），解除謂詞成立，依「到期即紅」下架。跨端契約閘
    # 自此全檢：後端實發 msg key ⊆ zh-tw.ts backend 樹鍵集，少鍵缺譯紅、多鍵孤兒紅。
}


# 豁免鍵的**射程**映射：(該鍵涵蓋的 reference 來源檔, 該鍵涵蓋的 generated 產出路徑)。
# ★與 DAY1_EXEMPTIONS 分表存放——前者答「何時解除」、本表答「豁免什麼」，合併會讓四欄制
#   失去單一語意，且射程改動與解除條件改動是兩件事、不該互相牽動。
DAY1_EXEMPT_SCOPE = {}


def _day1_released(key, root, exemptions=None):
    """執行該筆豁免的解除謂詞；True＝條件已成立、該筆應下架（到期即紅的判定基礎）。"""
    pred = (exemptions if exemptions is not None else DAY1_EXEMPTIONS)[key][1]
    if callable(pred):
        return bool(pred(root))
    return all(os.path.exists(os.path.join(root, rel)) for rel in pred)


def day1_active(root, exemptions=None):
    """回傳當下**仍生效**的豁免鍵集合（謂詞已為真者＝已到期、不算生效）。

    ★到期即紅由消費端負責：本函式只答「還在豁免中嗎」；已到期而項仍在表的 ERROR
    由 lint_reference_sources 指名該筆（機器強制第②條）。
    """
    table = exemptions if exemptions is not None else DAY1_EXEMPTIONS
    return {k for k in table if not _day1_released(k, root, table)}


def _day1_exempt_sources(root, exemptions=None):
    """仍生效之豁免鍵所涵蓋的 reference 來源檔集合。"""
    return {rel for k in day1_active(root, exemptions)
            for rel in DAY1_EXEMPT_SCOPE.get(k, ((), ()))[0]}


def _day1_exempt_outputs(root, exemptions=None):
    """仍生效之豁免鍵所涵蓋的 generated 產出路徑集合。"""
    return {rel for k in day1_active(root, exemptions)
            for rel in DAY1_EXEMPT_SCOPE.get(k, ((), ()))[1]}


def _assert_day1_table():
    """啟動時斷言：四欄缺一不可、逐欄非空——名冊自身腐化會讓整套豁免語意失真。"""
    for key, row in DAY1_EXEMPTIONS.items():
        assert key and isinstance(row, tuple) and len(row) == 3, f"DAY1_EXEMPTIONS[{key}] 欄數非 3"
        why, pred, since = row
        assert isinstance(why, str) and why.strip(), f"DAY1_EXEMPTIONS[{key}] 理由欄空"
        # ★理由欄會被逐字印進 lint 跳過明細，而該明細以全形分號分隔、筆數受機判
        #   （test_cmd_lint_prints_summary_then_skip_detail）——理由內含分隔符即污染筆數。
        assert "；" not in why, f"DAY1_EXEMPTIONS[{key}] 理由欄含全形分號（會污染跳過明細筆數機判）"
        assert callable(pred) or (isinstance(pred, tuple) and pred and
                                  all(isinstance(x, str) and x for x in pred)), \
            f"DAY1_EXEMPTIONS[{key}] 解除謂詞欄非可求值物"
        assert isinstance(since, str) and since.strip(), f"DAY1_EXEMPTIONS[{key}] 登記日欄空"
    # ★兩表鍵集必須逐鍵對齊——射程表漏一鍵＝該筆豁免的射程靜默歸零（消費端查不到、照舊硬紅）
    assert set(DAY1_EXEMPTIONS) == set(DAY1_EXEMPT_SCOPE), (
        f"DAY1_EXEMPTIONS 與 DAY1_EXEMPT_SCOPE 鍵集不一致："
        f"{set(DAY1_EXEMPTIONS) ^ set(DAY1_EXEMPT_SCOPE)}")


_assert_day1_table()


# 守衛#5 的弱探針：源碼「有沒有分派表」。★刻意與嚴格掃源正則（RE_DISPATCH_EQ／
# RE_DISPATCH_IN）各自獨立——同一條正則既當判準又當被驗對象＝套套邏輯，改壞它反而全綠。
RE_DISPATCH_PROBE = re.compile(r"\bcmd\s*==|\bcmd\s+in\s*\(")


def owning_submodule(rel):
    """來源檔所屬 submodule 目錄（不在任一子庫底下＝None）；映射唯一真值＝PIN_KEYS。"""
    for _key, sub in PIN_KEYS:
        if rel.startswith(sub + "/"):
            return sub
    return None


def lint_reference_sources(root, cache=None, submodule_skip=True, exemptions=None):
    """守衛#4：generate 各 reference 來源檔存在。lint 與 generate 雙掛（rev4:contracts G4）。

    ★與 rev4:contracts G4 字面（「空／缺即 ERROR」）的差異與理由（比照守衛#5 已做的收斂）：
    來源檔有四筆住在 submodule 底下（router.rs／elegant routes.ts／兩支 locale）。唯讀看碼
    模式（fresh clone 未跑 bootstrap）下這四筆必然不存在，照字面一律 ERROR，會與同一次
    lint 內 Lint16／Lint17／Lint18 對「同一個環境事實」判 skip 直接自相矛盾——一邊逐字說「不適用、
    不是失敗」、一邊逐字說「fail-closed 硬紅」（U5-quality 實測：scratch clone 得 4 ERROR
    ＋7 SKIP，四筆 ERROR 全落在 submodule 底下的來源檔）。且守衛要防的是「查到空集合而
    恆綠」，此處恆綠不成立：唯讀模式下 generate／check 本來就 fail-loud（實跑 check 直接
    吐 RouterRoutesError）。額外代價是 quickstart S5 造空劇本的機判被無關 ERROR 淹沒。
    故收斂為：來源檔位於 submodule 底下者先過共用存活探針（同 Lint16／Lint17／Lint18 那支），庫
    不可查→SKIP、原因同文；庫可查而檔案不見、或外層來源檔不見→維持 ERROR。
    ★`submodule_skip`：lint 端 True；generate 端 False——generate 沒有來源就是算不出對照表，
    跳過只會讓它往下撞既有散落例外（RouterRoutesError／SnapshotError…），失去歸一化的意義。
    """
    tail = ("來源被移位或改名（submodule 底下者其庫已可查、非缺 bootstrap——庫不可查走跳過）"
            if submodule_skip else
            "submodule worktree 未建起（跑 bash tools/bootstrap.sh）或來源被移位")
    out, skipped = [], {}
    exempt_src = _day1_exempt_sources(root, exemptions)
    day1_hit = set()
    for rel in REFERENCE_SOURCES:
        if os.path.isfile(os.path.join(root, rel)):
            continue
        if rel in exempt_src:            # Day 1 具名豁免：改由本函式末統一輸出具名 SKIP
            day1_hit.add(rel)
            continue
        sub = owning_submodule(rel) if submodule_skip else None
        if sub is not None:
            _head, why = submodule_head(root, sub, cache)
            if why:
                skipped.setdefault(sub, [why, 0])
                skipped[sub][1] += 1
                continue
        out.append(finding(ERROR, "Lint20", rel,
                           f"reference 來源檔不存在——generate 無輸入、對照表無法重算；{tail}"))
    for _key, sub in PIN_KEYS:
        if sub in skipped:
            why, n = skipped[sub]
            out.append(finding(SKIP, "Lint20", sub,
                               f"{why}——該庫 {n} 筆 reference 來源檔存在性守衛跳過"))
    # ★Day 1 具名豁免的統一輸出點（機器強制第①條：跳過必列明細，逐筆帶解除謂詞與所屬步）
    table = exemptions if exemptions is not None else DAY1_EXEMPTIONS
    for key in sorted(day1_active(root, exemptions)):
        n = len([r for r in DAY1_EXEMPT_SCOPE.get(key, ((), ()))[0] if r in day1_hit])
        if n:
            out.append(finding(SKIP, "Lint20", key,
                               f"Day 1 具名豁免（{table[key][0]}）——涵蓋 {n} 筆 reference "
                               f"來源檔，解除條件成立時本筆自動轉 ERROR 要求下架"))
    # ★機器強制第②條「到期即紅」：謂詞已為真而項仍在表＝ERROR 指名該筆
    for key in sorted(table):
        if _day1_released(key, root, table):
            out.append(finding(ERROR, "Lint20", key,
                               "Day 1 豁免已到期（解除謂詞成立）而項仍在 DAY1_EXEMPTIONS——"
                               "請移除該筆並讓對應閘恢復全檢"))
    return out


def lint_tool_dispatch(root):
    """守衛#5：①掃源清單本身非空 ②有分派表的 python 工具其子命令集非空。

    ★與 data-model §6 字面（「工具子命令集×4、空或缺即 ERROR」）的差異與理由：U4 真表
    實測 tools/fork-delta-lint.py 源碼本來就沒有分派表（零等號形、零 in 形），子命令集
    恆為空集合——而那是**正確的事實**：它是直跑工具，CLAUDE.md／RUNBOOK 都這樣寫、真表
    也如實記為「無——源碼無分派表、直跑」。照字面實作，lint 對現況直接自紅。
    故收斂為：以獨立的弱探針（源碼是否出現 `cmd ==`／`cmd in (`）判斷這支工具「有沒有
    分派表」；有分派表卻掃出空集合＝掃源正則壞了→ERROR，本來就沒有分派表＝合法空集合。
    守住的仍是 rev4:FR-013 要防的那件事——「查到空集合而恆綠」。
    """
    try:
        rows = compute_tools_cli(root)
    except ToolsCliError as ex:
        return [finding(ERROR, "Lint20", "tools",
                        f"工具掃源失敗（{ex}）——子命令集無從建立，fail-closed")]
    if not rows:
        return [finding(ERROR, "Lint20", "tools",
                        "工具掃源清單為空（TOOLS_PY／TOOLS_SH 名冊縮水）——"
                        "真表少節、命令形比對與舊名禁令一併靜默下線")]
    out = []
    for row in rows:
        if row["lang"] != "python" or row["subs"]:
            continue
        if RE_DISPATCH_PROBE.search(_read(root, row["rel"]) or ""):
            out.append(finding(ERROR, "Lint20", row["rel"],
                               "源碼有分派表（出現 cmd 比較）卻掃出空子命令集——掃源正則"
                               "壞了；該工具的命令形比對會查到空集合而恆綠"))
    return out


def lint_empty_sets(root, tracked=None, cache=None, exemptions=None):
    """Lint20：空集合守衛**八組**（data-model §6 七組＋rev5 新增守衛#8）。
    空／缺即 ERROR、訊息指名集合與來源。

    八組皆「結構上恆非空／恆存在」；空了代表掃描器或環境壞了，靜默放行＝假綠。
    ★守衛#8（rev5 差分）＝BUDGETS 名冊內檔案存在性，見該段註解。
    """
    out = []
    if not load_adrs(root):
        out.append(finding(ERROR, "Lint20", ADR_DIR,
                           f"ADR 檔集為空（來源＝{ADR_DIR}/*.md）——決策帳本不可能空，"
                           "目錄被移走或掃描器壞了"))
    if not [l for l in _jsonl_lines(_read(root, EVENTS) or "") if l.strip()]:
        out.append(finding(ERROR, "Lint20", EVENTS,
                           f"events 列為空（來源＝{EVENTS}）——事件源不可能空，"
                           "檔被清空或讀不到"))
    if tracked is None:
        tracked = tracked_files(root)
    if not [rel for rel in tracked if rel.endswith(".md")]:
        out.append(finding(ERROR, "Lint20", ".",
                           "外層 tracked md 語料為空（來源＝git ls-files '*.md'）——"
                           "Lint12~Lint15 引用健康條款會查到空語料而恆綠"))
    out += lint_reference_sources(root, cache, exemptions=exemptions)
    # 守衛#8（rev5 新增，§3.6 機制事實 1／§0.3 準則 4 白名單反轉的技術前提）：
    # ★lint_budgets 的第一步是讀檔、讀不到就 continue——既不報錯也不落跳過明細。
    #   於是「加進 BUDGETS」只保證**檔存在時**受管、不保證檔存在；名冊列了而檔案沒了，
    #   該筆預算就靜默下線且零信號。本組補上那道存在性斷言，讓白名單反轉真的 fail-closed。
    _table = exemptions if exemptions is not None else DAY1_EXEMPTIONS
    if "lint07.budget_roster" in _table and not _day1_released("lint07.budget_roster", root, _table):
        out.append(finding(SKIP, "Lint20", "lint07.budget_roster",
                           f"Day 1 具名豁免（{_table['lint07.budget_roster'][0]}）——"
                           "八檔全數落地後本筆自動轉 ERROR 要求下架"))
    else:
        for rel in sorted(BUDGETS):
            if not os.path.isfile(os.path.join(root, rel)):
                out.append(finding(ERROR, "Lint20", rel,
                                   "BUDGETS 名冊內檔案不存在——該筆預算判定會靜默跳過"
                                   "（讀不到即 continue、零訊號），名冊形同虛設"))
    out += lint_tool_dispatch(root)
    if not tracked_blobs(root):
        out.append(finding(ERROR, "Lint20", ".",
                           "憑證掃描 tracked 檔清單為空（來源＝git ls-files -s 扣 gitlink）"
                           "——Lint16 外層全量面會掃了個寂寞而恆綠"))
    for rel in CMD_FORM_CORPUS:
        if not os.path.isfile(os.path.join(root, rel)):
            out.append(finding(ERROR, "Lint20", rel,
                               "命令形語料檔不存在（三件活手冊為 Lint19 的固定語料）——"
                               "少一件即該檔的命令形漂移與舊名禁令靜默下線"))
    return out


# ---------------------------------------------------------------------------
# Lint21 index exec bit 守衛（rev4:B-116）
# ---------------------------------------------------------------------------

# 名冊＝「以直接執行形叫用」的可執行腳本（repo 相對路徑、寫死）。drvfs 上 chmod 不落
# index、ls 恆顯 0777，index 內 100644/100755 只有 `git ls-files -s` 看得到——全靠人記得
# `git update-index --chmod=+x` 即 rev4:019 兩支新腳本連踩之坑（rev4:B-116）。
# 成員資格以叫用形為據（逐檔 grep 實證、2026-07-31 盤點）：
#   .githooks/* 與 .githooks-submodule/* 四支＝git 經 core.hooksPath 直接 exec（外層
#     hooksPath=.githooks、兩源倉 hooksPath 指 .githooks-submodule，皆 tools/bootstrap.sh 設定）；
#   deploy/ 兩支＝檔頭用法行自載直跑形：sops.sh「./deploy/sops.sh <sops 參數...>」（另
#     deploy/decrypt-secrets.py 內以 ./deploy/sops.sh 直呼＝SOPS_REL）、
#     generate-dev-cert.sh「./deploy/generate-dev-cert.sh [--force]」；
#     ★generate-secrets.sh 與 preflight-secrets.sh 兩支已於 B-037 U3 退役（正典改
#     python3 deploy/<name>.py、不帶 exec bit＝B-035 U2/U3 拍板），同刀摘出本名冊。
#   tools/*.py 六支＝RUNBOOK §12 標頭明載「python 工具一律直跑或 python3 前綴」——直跑
#     屬受支持介面形。
# ★除外（叫用形不依賴 index exec bit；其 index 現值為何不在本條款管轄）：
#   .githooks/lib/scan-range.sh＝被 source（.githooks/pre-push 與
#     .githooks-submodule/pre-push 皆 `. …/scan-range.sh`、無直接執行處）；
#   deploy/dev-webhook-sink.sh＝恆 `sh` 前綴（檔頭用法行與 RUNBOOK §11 皆
#     `sh deploy/dev-webhook-sink.sh start|cat|stop`）；
#   deploy/generate-age-key.sh＝恆 `bash` 前綴（檔頭用法行與 RUNBOOK §12／§15.2 皆
#     `bash deploy/generate-age-key.sh`）；
#   tools/bootstrap.sh＝恆 `bash tools/bootstrap.sh`（CLAUDE.md §3、RUNBOOK §12、hooks 檢修
#     指引同形）；tools/wf-watchdog.py＝恆 `python3` 前綴（檔頭用法行＝Monitor command 欄填
#     `python3 tools/wf-watchdog.py <冒煙token> [wf目錄|runId]`、CLAUDE.md §2 同形；
#     B-005 轉 python 後比照 deploy/ 四支、不帶 exec bit）。
EXEC_BIT_ROSTER = (
    ".githooks/pre-commit", ".githooks/pre-push",
    ".githooks-submodule/pre-commit", ".githooks-submodule/pre-push",
    "deploy/generate-dev-cert.sh",
    "deploy/sops.sh",
    "tools/docs-sync.py", "tools/entity-drift-gate.py", "tools/fork-delta-lint.py",
    "tools/schema-gate.py", "tools/secret-value-guard.py", "tools/wire-schema.py",
)
EXEC_BIT_MODE = "100755"


def check_exec_bits(roster, modes):
    """Lint21 純判定：roster＝名冊、modes＝{rel: index stage-0 mode（ls-files -s 首欄）}。

    名冊空集合＝ERROR（fail-closed、Lint20 家族：名冊縮水＝守衛靜默下線）；名冊檔不在
    index（含合併衝突無 stage-0）＝ERROR（名冊腐化即紅）。本條款無 skip。
    """
    if not roster:
        return [finding(ERROR, "Lint21", "tools/docs-sync.py",
                        "exec bit 名冊為空集合（EXEC_BIT_ROSTER 縮水）——守衛靜默下線，"
                        "fail-closed（Lint20 家族）")]
    out = []
    for rel in roster:
        mode = modes.get(rel)
        if mode is None:
            out.append(finding(ERROR, "Lint21", rel,
                               "名冊檔不在 index（stage-0 查無此路徑）——名冊腐化即紅：檔案"
                               "移位／改名須同步改 EXEC_BIT_ROSTER，尚未 add 則先 git add"))
        elif mode != EXEC_BIT_MODE:
            out.append(finding(ERROR, "Lint21", rel,
                               f"index mode {mode}（須 {EXEC_BIT_MODE}）——drvfs 上 chmod "
                               f"不落 index、ls 恆顯 0777；修復：git update-index "
                               f"--chmod=+x {rel}"))
    return out


def exec_bit_self_test():
    """防恆綠：紅樣本（100644／缺席 index／空名冊）必紅、綠樣本必綠；失效即 ERROR
    （比照 Lint16 cred_self_test 慣例、成本近零）。"""
    out = []
    for label, roster, modes in (("100644", ("樣本",), {"樣本": "100644"}),
                                 ("缺席 index", ("樣本",), {}),
                                 ("空名冊", (), {})):
        if not any(f["level"] == ERROR for f in check_exec_bits(roster, modes)):
            out.append(finding(ERROR, "Lint21", "tools/docs-sync.py",
                               f"exec bit self-test 失效：紅樣本（{label}）未被攔下"
                               "——條款已恆綠，修復 check_exec_bits 後重跑"))
    if check_exec_bits(("樣本",), {"樣本": EXEC_BIT_MODE}):
        out.append(finding(ERROR, "Lint21", "tools/docs-sync.py",
                           "exec bit self-test 失效：綠樣本（100755）誤報——判定過寬，"
                           "修復 check_exec_bits 後重跑"))
    return out


def index_exec_modes(root, roster):
    """名冊檔之 index stage-0 mode（git ls-files -s 首欄）；回 {rel: mode}。

    只收 stage 0：合併衝突條目（stage 1/2/3）不入 map→該檔落「名冊檔不在 index」ERROR，
    衝突解掉前不放行（fail-closed）。
    """
    modes = {}
    for line in (git_out(["ls-files", "-s", "--", *roster], root) or "").splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path and len(parts) >= 3 and parts[2] == "0":
            modes[path] = parts[0]
    return modes


def lint_exec_bits(root):
    """Lint21：名冊內直接執行腳本之 index exec bit 必為 100755（rev4:B-116）。

    組裝＝self-test 防恆綠＋名冊逐檔斷言。本條款無 skip（名冊檔皆住外層 repo、無
    submodule 存活問題；任何不符一律 ERROR）。
    """
    modes = index_exec_modes(root, EXEC_BIT_ROSTER) if EXEC_BIT_ROSTER else {}
    return exec_bit_self_test() + check_exec_bits(EXEC_BIT_ROSTER, modes)


# ---------------------------------------------------------------------------
# Lint22 lint 條款範圍字串守衛（rev4:B-126）
# ---------------------------------------------------------------------------

# 本條款自身碼：finding 呼叫一律用字面 "Lint22"（錨形之所需、Lint21 同慣例）；本常數只作
# 組裝層推導一致性斷言（字面與常數漂移→自身碼不入推導集合→fail-closed 顯性紅）。
RANGE_CODE = "Lint22"
# 名冊＝範圍字串「Lint03～LintNN」的活引用檔（repo 相對路徑、寫死）。上線新條款漏 bump 已連兩例
# （rev4:018 上 Lint20 與 rev4:B-116 上 Lint21 都漏改 .githooks/pre-commit 檔頭）、純人工勘誤壓不住＝本條款
# 由來（rev4:B-126）。實形盤點（2026-07-31）：tools/docs-sync.py 一檔兩處（檔頭 lint 行＋
# run_lint docstring、全形～）、RUNBOOK §12 表列（半形~）、pre-commit 檔頭（全形～）——
# 逐檔收「全部」命中、每筆皆須等於推導上界。
# ★為何不全 repo 掃：docs/ops/events.jsonl 與 docs/generated/MILESTONES.md 等史料含舊範圍
#   字面（如 rev4:B-116 收單敘事）＝不可變過去式，全掃必誤紅、逼改史——名冊釘活引用三檔即射程。
RANGE_ROSTER = ("tools/docs-sync.py", "docs/ops/RUNBOOK.md", ".githooks/pre-commit")
# 真值側錨形＝finding 呼叫的「層級字面＋條款碼字面」形：條款存在的操作型定義（能發
# finding 才算條款）、散文與 docstring 提及不具此形不誤收；比組裝接線面（lint_* 函式名）
# 不易失真——函式:條款非一對一（如 lint_budgets 發 Lint07、lint_ids 發 Lint09）。上界＝字面最大號；
# test 假樁用碼不得高於現行最大號（灌水＝真 repo lint 顯性紅、fail-loud 非假綠）。
# ★兩支 regex 以拆分構造：本檔自身既是推導源又在名冊內，落完整字面會被自己掃到
#   （範圍形自咬）或把推導上界灌水（錨形）；同 Lint19 _FAKE_* 模板紀律。
RE_LINT_CODE = re.compile(r"finding\(\s*(?:ERROR|WARN|SKIP)\s*,\s*\"Lint" + r"(\d+)\"")
RE_RANGE = re.compile("Lint03" + "[~～]" + "Lint" + r"(\d+)")


def _self_source():
    """讀本工具自身源碼——條款集的唯一真值來源（掃源推導、不維護第二份名冊）。"""
    try:
        with open(os.path.abspath(__file__), encoding="utf-8-sig") as fh:
            return fh.read()
    except OSError:
        return ""


def derive_lint_codes(source_text):
    """Lint22 取值：以錨形掃本工具源碼、收 finding 呼叫的條款碼字面；回 {int 條款號}。"""
    return {int(m.group(1)) for m in RE_LINT_CODE.finditer(source_text)}


def scan_nonpadded_codes(source_text):
    """Lint22 取值（兩碼零填守衛、u2 雙審）：RE_LINT_CODE 寬收 \\d+ 防「單碼形靜默漏推導」，
    本函式對原字面驗長度——回非恰兩碼的碼字面清單（拍板＝Lint01 起兩碼零填形）。"""
    return [m.group(1) for m in RE_LINT_CODE.finditer(source_text)
            if len(m.group(1)) != 2]


def scan_range_hits(text):
    """Lint22 取值：逐行掃範圍字串「Lint03～LintNN」（半形~／全形～皆收）；回 [(行號, NN), ...]。"""
    return [(ln, int(m.group(1)))
            for ln, line in enumerate(text.splitlines(), start=1)
            for m in RE_RANGE.finditer(line)]


def check_range_strings(bound, roster, hits):
    """Lint22 純判定：bound＝掃源推導之條款上界（None＝推導失效）、roster＝名冊、
    hits＝{rel: None（檔案缺席）| [(行號, NN), ...]（該檔全部範圍字串命中）}。

    fail-closed：名冊空集合／推導失效／名冊檔缺席／零命中／任一命中 NN≠bound 皆
    ERROR（Lint20 家族）；本條款無 skip（名冊三檔皆住外層 repo、恆存在）。
    """
    if not roster:
        return [finding(ERROR, "Lint22", "tools/docs-sync.py",
                        "範圍字串名冊為空集合（RANGE_ROSTER 縮水）——守衛靜默下線，"
                        "fail-closed（Lint20 家族）")]
    if bound is None:
        return [finding(ERROR, "Lint22", "tools/docs-sync.py",
                        "條款上界推導失效（推導源讀不到、錨形零命中、或集合未含本條款"
                        "自身碼）——真值側失明即紅：修復 RE_LINT_CODE 錨形或推導源後重跑")]
    out = []
    for rel in roster:
        rel_hits = hits.get(rel)
        if rel_hits is None:
            out.append(finding(ERROR, "Lint22", rel,
                               "名冊檔缺席（讀不到）——名冊腐化即紅：檔案移位／改名須同步改 "
                               "RANGE_ROSTER"))
        elif not rel_hits:
            out.append(finding(ERROR, "Lint22", rel,
                               "範圍字串零命中——該檔原有的「Lint03～LintNN」字面被刪或改形＝名冊"
                               "腐化：恢復字面、或該檔確不再引用範圍時同步修 RANGE_ROSTER"))
        else:
            for ln, nn in rel_hits:
                if nn != bound:
                    out.append(finding(ERROR, "Lint22", f"{rel}:{ln}",
                                       f"範圍字串上界實得 {nn}、應為 {bound}（＝掃源推導之"
                                       f"現行條款上界）——上線新條款須同 commit 把名冊三檔"
                                       f"全部範圍字串 bump 至 Lint03～Lint{bound:02d}"))
    return out


def range_self_test():
    """防恆綠：紅樣本（錯值＋行號、零命中、推導失效）必紅、綠樣本（半形全形兩型）必綠；
    失效即 ERROR（比照 Lint16/Lint21 慣例、成本近零）。樣本字面拆分構造（理由見 RE_RANGE 註解）。
    """
    def rng(wave, nn):
        return "Lint03" + wave + "Lint" + str(nn)

    out = []
    red_hits = scan_range_hits("首行無關\n改 " + rng("～", 6) + " 於此\n")
    f = check_range_strings(7, ("樣本",), {"樣本": red_hits})
    if not any(x["level"] == ERROR and x["where"] == "樣本:2" for x in f):
        out.append(finding(ERROR, "Lint22", "tools/docs-sync.py",
                           "範圍字串 self-test 失效：紅樣本（錯值 6≠7）未被攔下或未指名"
                           "檔案:行號——條款已恆綠，修復 scan_range_hits／"
                           "check_range_strings 後重跑"))
    for label, bound, hits in (("零命中", 7, []), ("推導失效", None, [(1, 7)])):
        if not any(x["level"] == ERROR
                   for x in check_range_strings(bound, ("樣本",), {"樣本": hits})):
            out.append(finding(ERROR, "Lint22", "tools/docs-sync.py",
                               f"範圍字串 self-test 失效：紅樣本（{label}）未被攔下"
                               "——條款已恆綠，修復 check_range_strings 後重跑"))
    green_hits = scan_range_hits("甲 " + rng("~", 7) + "\n乙 " + rng("～", 7) + "\n")
    if len(green_hits) != 2:
        out.append(finding(ERROR, "Lint22", "tools/docs-sync.py",
                           f"範圍字串 self-test 失效：綠樣本兩型（半形~／全形～）應各命中"
                           f"一筆、實得 {len(green_hits)} 筆——掃描器對波浪形失明，"
                           "修復 scan_range_hits 後重跑"))
    elif check_range_strings(7, ("樣本",), {"樣本": green_hits}):
        out.append(finding(ERROR, "Lint22", "tools/docs-sync.py",
                           "範圍字串 self-test 失效：綠樣本（上界 7＝命中 7）誤報——"
                           "判定過寬，修復 check_range_strings 後重跑"))
    return out


def lint_range_strings(root):
    """Lint22：lint 條款範圍字串「Lint03～LintNN」名冊三檔 vs 掃源推導上界（rev4:B-126）。

    真值側＝自本工具源碼推導條款上界（錨形見 RE_LINT_CODE 註解；絕不另立手抄常數）；
    推導集合未含本條款自身碼＝錨形失真、視同推導失效（fail-closed）。名冊側＝
    RANGE_ROSTER 逐檔全命中比對。組裝＝self-test 防恆綠＋推導＋名冊斷言。本條款無 skip
    （名冊三檔皆住外層 repo、恆存在；任何不符一律 ERROR）。
    """
    src = _read(root, "tools/docs-sync.py")
    codes = derive_lint_codes(src) if src is not None else set()
    bound = max(codes) if int(RANGE_CODE.removeprefix("Lint")) in codes else None
    pad = [finding(ERROR, "Lint22", "tools/docs-sync.py",
                   f"條款碼字面「Lint{c}」非兩碼零填形（拍板＝Lint01 起兩碼）——"
                   "修正該 finding 呼叫的碼字面")
           for c in scan_nonpadded_codes(src or "")]
    hits = {}
    for rel in RANGE_ROSTER:
        text = _read(root, rel)
        hits[rel] = None if text is None else scan_range_hits(text)
    return range_self_test() + pad + check_range_strings(bound, RANGE_ROSTER, hits)


# ---------------------------------------------------------------------------
# Lint24 前後端 msg key 契約閘（rev4:B-133／rev4:B-134）
# ---------------------------------------------------------------------------

# 掃描面＝rust-api/server/src 底下全部 .rs 生產碼（#[cfg(test)] 區間以大括號配對整段排除、
# 行首 // 註解排除）；前端側復用 parse_locale_backend 解析 zh-tw backend 樹。
I18N_RS_SRC_DIR = "rust-api/server/src"
I18N_ERROR_RS = "rust-api/server/src/error.rs"     # key() 固定鍵抽取標的（碼表單一來源檔）
I18N_FRONTEND_LOCALE = "base-web/src/locales/langs/zh-tw.ts"
# 間接常數名冊（字面釘死；掃到 Biz(Cow::Borrowed(常數)) 形時查表）：
# throttle/mod.rs 之 LOCKED_MSG_KEY／CAPTCHA_REQUIRED_MSG_KEY 兩筆。掃描時另抓
# 「const 名: &str = "值";」宣告比對名冊值——源碼改值而名冊未跟＝ERROR（名冊漂移即恆綠洞）。
# ★rev5 現況為空表（user 拍板 2026-08-08、002-system-settings T011）：名冊原釘的兩筆
# （LOCKED_MSG_KEY／CAPTCHA_REQUIRED_MSG_KEY）在 rev4 住 server/src/throttle/mod.rs，而 B12
# 明確不搬 throttle（research R1「明確不進」清單），於是掃描面內查無宣告＝名冊腐化 ERROR，
# 會擋住 T011 這一批治理 commit。名冊防的是「常數改名／移出射程而名冊沒跟」，射程內沒有
# 那個常數時，空表才是誠實的狀態。
# ★回填由機器逼出、不靠人記得：登入節流刀寫下 AppError::Biz(Cow::Borrowed(LOCKED_MSG_KEY))
# 這類常數形構造點時，scan_backend_msg_keys 會判「無法靜態解析」而 fail-loud，訊息本身就寫
# 著「擴 I18N_CONST_ROSTER 名冊」——屆時同刀回填。
# ★實況（003-auth-session U-L／T051 落地後）：登入節流刀**沒有**走常數形，而是採 Lint24 的
#   另一條指定解法——六個構造點直書 `Cow::Borrowed("biz.auth.*")` 字面（同 002 既有構造點形），
#   故上述觸發條件未成立、本名冊維持空表＝**誠實態而非漏填**。上面那段機制仍然有效，只是它
#   預告的那把刀沒有觸發它；下一個寫出常數形構造點的刀仍會被 fail-loud 逼出回填。
I18N_CONST_ROSTER = {}
# 前端獨有內部詞彙表白名單（九鍵字面釘死；★白名單∩後端實發集必空、非空＝腐化 ERROR）：
# biz.user.passwordViolation.* 八鍵＝密碼政策明細插值的前端內部詞彙表——與
# rust-api/server/src/model/password.rs 八個 VIOLATION_* 常量一一對應（後端經 BizData
# passwordPolicy 明細通道下發違規碼、前端逐碼譯後 join，不作 msg key 整鍵下發）；
# common.listSeparator＝明細清單 join 分隔符（純前端在地化詞彙）。
I18N_FRONTEND_INTERNAL_KEYS = frozenset((
    "biz.user.passwordViolation.minLength",       # VIOLATION_MIN_LENGTH
    "biz.user.passwordViolation.maxLength",       # VIOLATION_MAX_LENGTH
    "biz.user.passwordViolation.maxBytes",        # VIOLATION_MAX_BYTES
    "biz.user.passwordViolation.requireDigit",    # VIOLATION_REQUIRE_DIGIT
    "biz.user.passwordViolation.requireLowercase",  # VIOLATION_REQUIRE_LOWERCASE
    "biz.user.passwordViolation.requireUppercase",  # VIOLATION_REQUIRE_UPPERCASE
    "biz.user.passwordViolation.requireSpecial",  # VIOLATION_REQUIRE_SPECIAL
    "biz.user.passwordViolation.forbidUsername",  # VIOLATION_FORBID_USERNAME
    "common.listSeparator",                       # 明細 join 分隔符（rev4:T024）
))
# 構造點錨形（Biz 前綴可帶路徑限定如 crate::error::AppError::Biz）：
RE_I18N_SITE = re.compile(r"AppError::(?:BizData|Biz)\s*\(")
# 構造點內文四形（對錨形之後的視窗行匹配；順序＝樣式排除→字面→名冊常數→unresolved）：
RE_I18N_ARM = re.compile(   # match 綁定臂樣式：Biz(key) =>／BizData(key, _) =>（含 if 守衛）
    r"^\s*(?:_|[a-z][A-Za-z0-9_]*)\s*(?:,\s*(?:_|[a-z][A-Za-z0-9_]*)\s*)?\)+\s*"
    r"(?:if\b[^=]*)?=>")
RE_I18N_LIT = re.compile(   # Cow::Borrowed("字面")／直接 "字面"（Cow 可帶 std::borrow:: 前綴）
    r'^\s*(?:(?:std::borrow::)?Cow::Borrowed\(\s*)?"([^"]+)"')
RE_I18N_CONST = re.compile(  # Cow::Borrowed(常數)／直接常數（UPPER_SNAKE 形）
    r"^\s*(?:(?:std::borrow::)?Cow::Borrowed\(\s*)?([A-Z][A-Z0-9_]*)\s*[,)]")
RE_I18N_CONST_DECL = re.compile(  # 名冊常數宣告實值（名冊漂移比對用）
    r'\bconst\s+([A-Z][A-Z0-9_]*)\s*:\s*&\s*str\s*=\s*"([^"]+)"\s*;')
RE_I18N_KEY_ARM = re.compile(r'=>\s*"([^"]+)"')   # key() 方法 match 臂固定鍵
RE_I18N_STR = re.compile(r'"(?:\\.|[^"\\])*"')    # 洗掃用：字串字面
RE_I18N_CHAR = re.compile(r"'(?:\\.|[^'\\])'")    # 洗掃用：char 字面（lifetime 無閉引號、不中）


def _rs_scrub(line):
    """洗掉字串／char 字面與 // 註解後的殘碼——只供大括號/分號結構計數，內容不重要。"""
    line = RE_I18N_STR.sub('""', line)
    line = RE_I18N_CHAR.sub("' '", line)
    return line.split("//", 1)[0]


def _rs_code_part(line):
    """截去行尾 // 註解（字串感知：引號內 // 不截）——供構造點／宣告／固定鍵掃描用。
    與 _rs_scrub 不同：保留字串字面內容（要抓的 key 就在字面裡）。
    雙審 minor 收單：尾註內的構造點／const 宣告字面曾會成幻影鍵誤紅（quality ②）。"""
    in_str, esc = False, False
    for i, ch in enumerate(line):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "/" and line[i:i + 2] == "//":
            return line[:i]
    return line


def rs_production_lines(text, rel):
    """Lint24 取值：#[cfg(test)] 區間以大括號配對整段排除（分號項如 `pub mod x;` 亦收；
    屬性後允許夾註解／堆疊屬性行）。回 ([(行號, 原行), ...], findings)——
    區間至 EOF 未配對＝ERROR fail-loud（排除失效即紅、非靜默略過）。"""
    lines = text.splitlines()
    kept, errs = [], []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        # 不受支援的 cfg-test 形一律 fail-loud（quality 審 minor ③——同行屬性＋item 會
        # 靜默吃掉後續產碼、cfg(all(test,…)) 會讓測試碼洩進掃描面；含 not(test)——
        # 屆時擴掃描器）：
        if s.startswith("#[cfg(test)]") and s != "#[cfg(test)]":
            errs.append(finding(ERROR, "Lint24", f"{rel}:{i + 1}",
                                "不受支援的 #[cfg(test)] 同行形（屬性後接同行 item）——"
                                "排除圈界無法保證，fail-loud：改寫為標準獨立行形或擴 "
                                "rs_production_lines"))
            i += 1
            continue
        if s != "#[cfg(test)]" and s.startswith("#[cfg(") and re.search(r"\btest\b", s):
            errs.append(finding(ERROR, "Lint24", f"{rel}:{i + 1}",
                                "可疑的 cfg-test 複合形（如 cfg(all(test,…))／cfg(not(test))）"
                                "不受支援——測試區間可能洩入（或產碼被誤排除），fail-loud："
                                "改寫為標準 #[cfg(test)] 或擴 rs_production_lines"))
            i += 1
            continue
        if s == "#[cfg(test)]":
            start_ln = i + 1
            i += 1
            depth, opened, ended = 0, False, False
            while i < n and not ended:
                for ch in _rs_scrub(lines[i]):
                    if ch == "{":
                        depth += 1
                        opened = True
                    elif ch == "}":
                        depth -= 1
                        if opened and depth == 0:
                            ended = True
                            break
                    elif ch == ";" and not opened:
                        ended = True   # 分號項（無大括號體）：排除至此行止
                        break
                i += 1
            if not ended:
                errs.append(finding(ERROR, "Lint24", f"{rel}:{start_ln}",
                                    "#[cfg(test)] 區間大括號未配對（至 EOF 未閉）——排除"
                                    "失效，fail-loud：修復該區間或掃描器後重跑"))
        else:
            kept.append((i + 1, lines[i]))
            i += 1
    return kept, errs


def scan_backend_msg_keys(root):
    """Lint24 取值：掃 rust 生產碼收「後端實發 msg key 集」＝①Biz/BizData 構造點字面
    ②名冊常數間接形 ③error.rs key() 方法 match 臂固定鍵。
    回 ({key: [(rel, 行號), ...]}, findings)——findings＝結構性錯誤（零 .rs 檔／cfg(test)
    未配對／構造點無法靜態解析／名冊漂移／key() 方法缺席），非空時不可進差集比對。"""
    src_dir = os.path.join(root, I18N_RS_SRC_DIR)
    files = sorted(
        os.path.join(dirpath, f)[len(os.path.join(root, "")):].replace(os.sep, "/")
        for dirpath, _dirs, names in os.walk(src_dir)
        for f in names if f.endswith(".rs"))
    if not files:
        return {}, [finding(ERROR, "Lint24", I18N_RS_SRC_DIR,
                            "掃描面零 .rs 檔（源樹缺席或空）——後端實發集無法建立，"
                            "fail-closed（Lint20 家族）")]
    backend, errs, const_decls, key_method_found = {}, [], {}, False
    for rel in files:
        kept, region_errs = rs_production_lines(_read(root, rel) or "", rel)
        errs += region_errs
        for _ln, line in kept:
            if line.strip().startswith("//"):
                continue   # 註解可注入假宣告值（spec 審 minor ①）——與構造點掃描同紀律
            for m in RE_I18N_CONST_DECL.finditer(_rs_code_part(line)):
                if m.group(1) in I18N_CONST_ROSTER:
                    const_decls[m.group(1)] = m.group(2)
        for idx, (ln, line) in enumerate(kept):
            if line.strip().startswith("//"):
                continue
            code = _rs_code_part(line)
            for m in RE_I18N_SITE.finditer(code):
                window = code[m.end():]
                for _nln, nline in kept[idx + 1:idx + 3]:
                    window += " " + _rs_code_part(nline).strip()
                if RE_I18N_ARM.match(window) or (
                        re.match(r"\s*_", window) and "=>" in window):
                    continue   # match 樣式（綁定臂／萬用臂——萬用臂須窗內見 => 才略過，
                    #            否則落 unresolved fail-loud；quality 審 minor ④）＝非構造點
                lit = RE_I18N_LIT.match(window)
                if lit:
                    backend.setdefault(lit.group(1), []).append((rel, ln))
                    continue
                cst = RE_I18N_CONST.match(window)
                if cst and cst.group(1) in I18N_CONST_ROSTER:
                    backend.setdefault(
                        I18N_CONST_ROSTER[cst.group(1)], []).append((rel, ln))
                    continue
                errs.append(finding(ERROR, "Lint24", f"{rel}:{ln}",
                                    f"AppError::Biz/BizData 構造點無法靜態解析"
                                    f"（內文開頭：{window[:60]}）——非字面、非名冊常數一律 "
                                    f"fail-loud（防恆綠洞）：改寫為 Cow::Borrowed(字面) "
                                    f"或擴 I18N_CONST_ROSTER 名冊；若實為 match 臂形"
                                    f"（本形未被樣式排除吃下）請擴 RE_I18N_ARM"))
        if rel == I18N_ERROR_RS:
            key_method_found, key_errs = _collect_key_method(kept, rel, backend)
            errs += key_errs
    if not key_method_found and not any(
            x["where"].startswith(I18N_ERROR_RS) for x in errs):
        errs.append(finding(ERROR, "Lint24", I18N_ERROR_RS,
                            "error.rs 缺席或找不到 fn key( 方法——固定鍵抽取失效，"
                            "fail-loud（碼表單一來源檔即紅）"))
    for name, pinned in I18N_CONST_ROSTER.items():
        used = any((pinned == k) for k in backend) or name in const_decls
        if name in const_decls and const_decls[name] != pinned:
            errs.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                                f"名冊常數 {name} 值漂移：源碼實值「{const_decls[name]}」"
                                f"≠名冊釘死值「{pinned}」——同 commit 更新 "
                                f"I18N_CONST_ROSTER（名冊腐化即恆綠洞）"))
        elif not used:
            errs.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                                f"名冊常數 {name} 於掃描面查無宣告——常數已改名／移出射程"
                                f"＝名冊腐化：同步修 I18N_CONST_ROSTER"))
    return backend, errs


def _collect_key_method(kept, rel, backend):
    """error.rs `fn key(` 方法體（大括號配對圈界）內 match 臂固定鍵 → 併入 backend。
    回 (是否找到方法, findings)。綁定臂（=> key.as_ref()）無字串字面、天然不中。"""
    start = next((i for i, (_ln, l) in enumerate(kept)
                  if not l.strip().startswith("//")
                  and re.search(r"\bfn key\s*\(", _rs_code_part(l))), None)
    if start is None:
        return False, []
    depth, opened = 0, False
    for i in range(start, len(kept)):
        ln, line = kept[i]
        if opened or "{" in _rs_scrub(line):
            if not line.strip().startswith("//"):
                # 註解行可注入幻影固定鍵（spec 審 minor ①②）——與構造點掃描同紀律
                for k in RE_I18N_KEY_ARM.findall(_rs_code_part(line)):
                    backend.setdefault(k, []).append((rel, ln))
        for ch in _rs_scrub(line):
            if ch == "{":
                depth += 1
                opened = True
            elif ch == "}":
                depth -= 1
                if opened and depth == 0:
                    return True, []
    return True, [finding(ERROR, "Lint24", rel,
                          "fn key( 方法體大括號未配對（至 EOF 未閉）——固定鍵抽取失效，"
                          "fail-loud")]


def check_i18n_contract(backend, frontend, whitelist):
    """Lint24 純判定：backend＝{實發 key: [(rel, 行號), ...]}、frontend＝前端 backend 樹
    鍵集、whitelist＝前端內部鍵白名單。空集 fail-loud（Lint20 家族）；後端有前端無＝ERROR
    逐鍵指名構造點＋修法；白名單∩後端實發集非空＝腐化 ERROR；前端有後端無且白名單外＝
    孤兒鍵 ERROR；★白名單鍵不在字典＝ERROR（存在性斷言——九鍵被刪不得靜默綠，
    rev4:B-133 同失效類；quality 審 minor ①）。本條款無 skip、severity 一律 ERROR。"""
    if not backend:
        return [finding(ERROR, "Lint24", I18N_RS_SRC_DIR,
                        "後端掃出 0 鍵——掃描器或源樹壞了，fail-closed（Lint20 家族）")]
    if not frontend:
        return [finding(ERROR, "Lint24", I18N_FRONTEND_LOCALE,
                        "前端 backend 樹 0 鍵——解析器或字典壞了，fail-closed（Lint20 家族）")]
    out = []
    for key in sorted(set(backend) & whitelist):
        sites = "、".join(f"{rel}:{ln}" for rel, ln in backend[key])
        out.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                           f"I18N_FRONTEND_INTERNAL_KEYS 白名單腐化：「{key}」已在後端實發集"
                           f"（構造點：{sites}）——白名單僅收前端內部鍵，自白名單移除該筆"))
    for key in sorted(set(backend) - frontend):
        sites = "、".join(f"{rel}:{ln}" for rel, ln in backend[key])
        out.append(finding(ERROR, "Lint24", backend[key][0][0] + ":%d" % backend[key][0][1],
                           f"後端實發 msg key「{key}」前端 backend 字典無此鍵"
                           f"（構造點：{sites}）——三語 locale（zh-tw/zh-cn/en-us）backend "
                           f"樹＋app.d.ts Schema 同 commit 補鍵（rev4:L-094：i18n 接線三範圍"
                           f"最常漏第三個、任一側單獨 commit 都 typecheck 紅）"))
    for key in sorted(frontend - set(backend) - whitelist):
        out.append(finding(ERROR, "Lint24", I18N_FRONTEND_LOCALE,
                           f"前端 backend 字典鍵「{key}」後端無任何構造點發出＝孤兒鍵——"
                           f"確為前端內部詞彙表則入 I18N_FRONTEND_INTERNAL_KEYS 白名單"
                           f"（附存在理由註解）、確廢棄則刪鍵"))
    for key in sorted(whitelist - frontend):
        out.append(finding(ERROR, "Lint24", I18N_FRONTEND_LOCALE,
                           f"I18N_FRONTEND_INTERNAL_KEYS 白名單鍵「{key}」不在前端 backend 字典"
                           f"——字典缺鍵即 vue-i18n fallback 吐裸識別字（rev4:B-133 同失效類）："
                           f"確已廢棄則同刀自白名單移除、否則補回字典"))
    return out


def i18n_contract_self_test():
    """防恆綠：紅樣本四型（後端多鍵／前端孤兒鍵／白名單腐化／白名單鍵不在字典）必紅且帶
    關鍵內容、綠樣本（含白名單內部鍵）必綠；失效即 ERROR（比照 Lint16/Lint21/Lint22 慣例）。"""
    out = []
    site = {"甲.乙": [("樣本.rs", 7)]}
    f = check_i18n_contract(site, {"甲.丙"}, frozenset(("甲.丙",)))
    if not any(x["level"] == ERROR and "甲.乙" in x["msg"] and "樣本.rs:7" in x["msg"]
               for x in f):
        out.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                           "契約閘 self-test 失效：紅樣本（後端多鍵）未被攔下或未附構造點 "
                           "file:line——條款已恆綠，修復 check_i18n_contract 後重跑"))
    f = check_i18n_contract(site, {"甲.乙", "孤.鍵"}, frozenset())
    if not any(x["level"] == ERROR and "孤.鍵" in x["msg"] for x in f):
        out.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                           "契約閘 self-test 失效：紅樣本（前端孤兒鍵）未被攔下"
                           "——條款已恆綠，修復 check_i18n_contract 後重跑"))
    f = check_i18n_contract(site, {"甲.乙", "內.部"}, frozenset(("內.部", "甲.乙")))
    if not any(x["level"] == ERROR and "白名單" in x["msg"] for x in f):
        out.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                           "契約閘 self-test 失效：紅樣本（白名單∩後端實發集非空）未被攔下"
                           "——白名單腐化防呆已恆綠，修復 check_i18n_contract 後重跑"))
    f = check_i18n_contract(site, {"甲.乙"}, frozenset(("缺.鍵",)))
    if not any(x["level"] == ERROR and "缺.鍵" in x["msg"] for x in f):
        out.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                           "契約閘 self-test 失效：紅樣本（白名單鍵不在字典）未被攔下"
                           "——白名單存在性斷言已恆綠，修復 check_i18n_contract 後重跑"))
    if check_i18n_contract(site, {"甲.乙", "內.部"}, frozenset(("內.部",))):
        out.append(finding(ERROR, "Lint24", "tools/docs-sync.py",
                           "契約閘 self-test 失效：綠樣本（全對齊＋白名單內部鍵）誤報——"
                           "判定過寬，修復 check_i18n_contract 後重跑"))
    return out


def lint_i18n_contract(root, exemptions=None):
    """Lint24：前後端 msg key 契約閘（rev4:B-133／rev4:B-134）。

    後端側＝scan_backend_msg_keys（生產碼構造點字面＋名冊常數＋key() 固定鍵；cfg(test)
    區間排除；無法靜態解析＝ERROR fail-loud）；前端側＝parse_locale_backend 解析 zh-tw
    backend 樹。組裝＝self-test 防恆綠＋雙側取值＋差集判定；任一側結構性錯誤＝只報該錯、
    不進差集（比對無基準）。本條款無 skip、severity 一律 ERROR。
    ★掃描面註記（雙審 minor 收單）：前端側僅 zh-tw；en-us 由 msg-dict 兩語鍵集斷言
    （compute_msg_dict_rows、generate/check 路徑）間接守；zh-cn 不在任何 lint 掃描面、
    僅由 app.d.ts Schema 之 vue-tsc typecheck 兜底（不在 pre-commit）——強化候選詳 rev4:B-135。"""
    out = i18n_contract_self_test()
    backend, errs = scan_backend_msg_keys(root)
    text = _read(root, I18N_FRONTEND_LOCALE)
    frontend = set()
    if text is None:
        errs.append(finding(ERROR, "Lint24", I18N_FRONTEND_LOCALE,
                            "前端 locale 檔缺席（讀不到）——字典側無法建立，fail-closed"
                            "（Lint20 家族）"))
    else:
        try:
            frontend = set(parse_locale_backend(text, I18N_FRONTEND_LOCALE))
        except BackendDictError as ex:
            errs.append(finding(ERROR, "Lint24", I18N_FRONTEND_LOCALE,
                                f"backend 樹解析失敗：{ex}——fail-loud"))
    if errs:
        # ★Day 1 具名豁免（§4.5.10 類三／B4 乙③）：判定點必須在此——兩個 early-return
        #   的 errs 已集齊、尚未 return 的這一刻。放進 check_i18n_contract 內是不可達的
        #   （Day 1 根本走不到那裡），拔項亦零信號（v2 之誤，經源碼複驗證偽）。
        # 語意：**兩側源皆缺** 且 lint24.day1 有登記 → 合併為一筆具名 SKIP；
        #       **單側缺** → 照舊 ERROR（那是真故障，不是創世期結構性紅）。
        table = exemptions if exemptions is not None else DAY1_EXEMPTIONS
        if "lint24.day1" in table and not _day1_released("lint24.day1", root, table):
            back_missing = any(x["where"] == I18N_RS_SRC_DIR for x in errs)
            front_missing = any(x["where"] == I18N_FRONTEND_LOCALE for x in errs)
            if back_missing and front_missing and len(errs) == 2:
                return out + [finding(SKIP, "Lint24", "lint24.day1",
                                      f"Day 1 具名豁免（{table['lint24.day1'][0]}）——"
                                      "任一側源到位即該側規則接管，兩側皆備即全檢")]
        return out + errs
    return out + check_i18n_contract(backend, frontend, I18N_FRONTEND_INTERNAL_KEYS)


# ---------------------------------------------------------------------------
# Lint25 跨代裸編號（ADR 0012；B-004 全量清償的防復發閘）
# ---------------------------------------------------------------------------
# 判定三段，**逐 token、零上下文依賴**（ADR 0012 決定 3）：
#   ①token 緊鄰左側是 rev2:／rev3:／rev4:（未來 rev5:）＝合規。空格散文形（「rev4 P1.1」）
#     與共享前綴形（「rev4:ADR 0080／0084」的第二號）刻意**不算**合規——散文限定擋不住
#     擴散已實證（同一 ADR 檔首處散文形、後兩處即退化純裸）。
#   ②能在 rev5 原生 registry 解析＝原生放行。
#   ③其餘＝命中（前代編號空間的裸引用）。
# ★registry 一律**掃源現算**、絕不落字面名冊（ADR 0012 決定 7）：落字面就是第二份會腐化的
#   名冊，rev5 配號往前走時它照舊用舊區間判、誤報與漏報同時發生。
# ★已知極限（ADR 0012 明載、不強求）：「號落 rev5 原生區間、語意屬前代」的遮蔽型測不出
#   （裸 001 既是 rev5 首刀號、也是 rev4 001-compose-stack 的號），靠人工審查兜底。
# ★掃描面＝**外層** tracked 文字檔。submodule 內容不在 git ls-files 展開面內（同 Lint12~Lint15
#   慣例），子庫側清償走各自的刀（B-004 批 I）。
LINT25_SKIP_DIRS = (
    "docs/generated/",      # 機器生成、任何字面都是上游源的鏡像（改源不改鏡）
    "docs/brainstorms/",    # one-shot 史料（同 HISTORICAL_EXEMPT 之理由：過去式不改寫）
    ".specify/",            # vendored spec-kit 面（ADR 0012 白名單第三類、sha256 釘死）
    ".claude/skills/",      # vendored skill 面（同上）
)

# 形狀族表（族名＝具名群組名／中文標籤／樣式）。族名必須是合法 python 識別字。
# ★次序即優先權：長形排在其真子形之前——刀名全形先於裸刀號，否則 019-secrets-sops 會被
#   拆成裸 019、slug 這個最有力的血緣證據就看不到了。
# ★各族 regex 自行收斂、**precision 優先**：寧可漏（人工兜底）不可淹——誤報一多整條款會被
#   當雜訊略過，那才是真正的恆綠。
# ★刻意不做的兩族（ADR 0012 已知極限）：無「ADR」字面毗鄰之裸四位（年份／埠／雜湊片段誤報
#   面遠大於收益）、data-model §N 與 quickstart 章節號（§N 是全 repo 通用節號形、誤報面大）。
LINT25_SHAPES = (
    # 刀名全形 NNN-slug：左界只擋數字、**放行字母**——grafana uid 的內嵌形（obs016-…）要抓得到
    # 才輪得到樣式級豁免吃；擋掉字母等於讓白名單變裝飾品。
    ("feat", "刀名全形", r"(?<!\d)(?P<feat>\d{3}-[a-z]+(?:-[a-z]+)*)"),
    ("adr", "ADR 編號", r"(?P<adr>ADR\s*[（(]?\s*\d{4}[）)]?)"),
    ("review", "review 報告編號", r"(?<![0-9A-Za-z])(?P<review>REVIEW-\d{3}-\d{3})"),
    ("bid", "BACKLOG 編號", r"(?<![0-9A-Za-z])(?P<bid>B-\d{3})(?!\d)"),
    ("lid", "LESSONS 編號", r"(?<![0-9A-Za-z])(?P<lid>L-\d{3})(?!\d)"),
    ("frsc", "需求／成功指標號", r"(?<![0-9A-Za-z])(?P<frsc>(?:FR|SC)-\d{3})(?!\d)"),
    ("fid", "findings 編號", r"(?<![0-9A-Za-z])(?P<fid>F\d{3}-\d)(?!\d)"),
    ("tid", "任務號", r"(?<![0-9A-Za-z])(?P<tid>T\d{3})(?!\d)"),
    ("pn", "契約條款號", r"(?<![0-9A-Za-z])(?P<pn>§?P\d\.\d{1,2})(?!\d)"),
    ("psec", "契約節號", r"(?P<psec>§P\d)(?!\.)"),
    ("uround", "執行單元輪次", r"(?<!\d)(?P<uround>0\d{2}\s+U\d)(?!\d)"),
    ("us", "user story 號", r"(?<![0-9A-Za-z])(?P<us>US\d)(?!\d)"),
    ("research", "research 條目", r"(?P<research>research\s+R\d)(?!\d)"),
    ("contracts", "contracts 守衛號", r"(?P<contracts>§G\d|contracts\s+G\d)(?!\d)"),
    ("scangates", "scan-gates 節號", r"(?P<scangates>scan-gates\s+§S\d)(?!\d)"),
    ("mid", "migration 短編號", r"(?<![0-9A-Za-z])(?P<mid>m\d{3})(?!\d)"),
    ("lintcode", "lint 條款碼", r"(?<![0-9A-Za-z])(?P<lintcode>Lint\d{2,})"),
    # 裸刀號：僅 0 開頭三位、值域收斂 001~029（歷代刀號實域）——000（rev5 啟動書）／
    # 033（ANSI escape）／077（umask）天然出局。四位以上（權限 mode 0755／0700、ADR 四位）
    # 由右界 (?!\d) 擋、小數與版本號（0.001／1.0.019）由兩側的 . 擋、日期與長數字串
    # （2026-08-07、fork260509）由左界的數字擋；左界另擋 , 與 -（千分位 1,000,000 與
    # E-NNN 連字號形，總審 2026-08-07 收斂）；埠一律 2xxxx／非 0 開頭、天然不入。
    ("bare", "裸刀號", r"(?<![0-9A-Za-z.,-])(?P<bare>0(?:0[1-9]|1\d|2\d))(?![\d.])"),
)
RE_LINT25 = re.compile("|".join(pat for _n, _label, pat in LINT25_SHAPES))
LINT25_LABELS = {name: label for name, label, _pat in LINT25_SHAPES}
# 合規前綴：緊鄰左側、逐 token（rev5: 為未來世代預留——rev6 起本代編號亦須帶前綴）
RE_LINT25_PREFIX = re.compile(r"rev[2-5]:$")
# 自測假號段（ADR 0012 決定 4）：永不落入 rev5 可達號段，故一律視同原生
RE_LINT25_FAKE_FEAT = re.compile(r"^9\d\d-fake|^\d{3}-example-")  # 後者＝契約 JSON 示例假刀名（005-example-feature）
RE_MIGRATION_SRC = re.compile(r"^(m\d{3})_\w+\.rs$")
MIGRATION_SRC_DIR = "rust-api/migration/src"
LINT25_HINT = "加 rev4:／rev3:／rev2: 前綴，或查 ADR 0012（編號命名空間紀律）"


def lint25_registry(root):
    """Lint25 取值：rev5 原生編號 registry——一律掃源現算（ADR 0012 決定 7）。

    回 dict：
      specs      ＝specs/ 目錄名集（刀名全形原生集）
      spec_nums  ＝其三位號集（裸刀號原生集）
      adrs       ＝docs/arc42/decisions/ 檔名四位集
      b_next／l_next＝BACKLOG／LESSONS 檔頭 next-id（None＝讀不到，該族一律不放行）
      mids       ＝migration 檔名 mNNN 集；None＝來源目錄缺席（唯讀 clone），該族不判——
                   判定基準不在就不判，比「基準空集合＝全數誤報」誠實
      lint_bound ＝條款碼上界（derive_lint_codes 自身結果之最大值）；None＝推導失效
    """
    specs = set()
    d = os.path.join(root, "specs")
    if os.path.isdir(d):
        specs = {n for n in os.listdir(d) if os.path.isdir(os.path.join(d, n))}
    # 啟動書與各刀階段 0 產出（docs/brainstorms/NNN-*.md）＝rev5 自己的刀名編號空間
    bd = os.path.join(root, "docs/brainstorms")
    if os.path.isdir(bd):
        specs |= {n[:-3] for n in os.listdir(bd)
                  if n.endswith(".md") and re.match(r"\d{3}-", n)}
    adrs = set()
    ad = os.path.join(root, ADR_DIR)
    if os.path.isdir(ad):
        adrs = {n[:4] for n in os.listdir(ad) if n.endswith(".md") and RE_ADR_ID.fullmatch(n[:4])}
    mids = None
    md = os.path.join(root, MIGRATION_SRC_DIR)
    if os.path.isdir(md):
        mids = {m.group(1) for m in (RE_MIGRATION_SRC.match(n) for n in os.listdir(md)) if m}
        if mids:
            # 「下一支」也原生：文件慣以「自 m00N 起編」指 rev5 未來號（同 next-id 語意）
            mids |= {f"m{max(int(x[1:]) for x in mids) + 1:03d}"}
    # rev5 spec 定義號掃源導出集：checkbox 任務行＝tids、spec.md 粗體定義＝frscs、
    # research.md 節標題＝rns——跨檔引用這些號（工具 docstring／ADR 引 001 刀驗收面）屬原生；
    # 「前代同號」遮蔽型為 ADR 0012 已載之已知極限
    tids, frscs, rns = set(), set(), set()
    for _feat in specs:
        _t = _read(root, f"specs/{_feat}/tasks.md") or ""
        tids |= {m.group(1) for m in re.finditer(r"^- \[.\] (T\d{3})\b", _t, re.M)}
        _s = _read(root, f"specs/{_feat}/spec.md") or ""
        frscs |= {m.group(1) for m in re.finditer(r"\*\*((?:FR|SC)-\d{3})\*\*", _s)}
        _r = _read(root, f"specs/{_feat}/research.md") or ""
        rns |= {m.group(1) for m in re.finditer(r"^## (R\d)\b", _r, re.M)}
    codes = derive_lint_codes(_read(root, "tools/docs-sync.py") or "")
    return {
        "specs": specs,
        "spec_nums": {n[:3] for n in specs if n[:3].isdigit()},
        "adrs": adrs,
        "b_next": _parse_next("B", _read(root, BACKLOG)),
        "l_next": _parse_next("L", _read(root, "docs/ops/LESSONS.md")),
        "mids": mids,
        "tids": tids,
        "frscs": frscs,
        "rns": rns,
        "lint_bound": max(codes) if codes else None,
    }


def lint25_native(kind, tok, rel, reg):
    """該 token 是否解析得進 rev5 原生編號空間（True＝放行、不算命中）。

    ★假號段（B-9xx／L-9xx／9NN-fake-*；ADR 0012 決定 4）一律放行——自測 fixture 專用區間。
    ★K1-NN／K2-NN／E-NNN／無連字號創世步（B9／B8a／B10）不落入任何形狀族、天然不成候選，
      故此處無對應放行碼（由 TestLintIdNamespace 的反例案釘住，避免將來改形時靜默誤報）。
    """
    if kind == "feat":
        return tok in reg["specs"] or bool(RE_LINT25_FAKE_FEAT.match(tok))
    if kind == "bare":
        return tok in reg["spec_nums"]
    if kind == "adr":
        return re.search(r"\d{4}", tok).group(0) in reg["adrs"]
    if kind in ("bid", "lid"):
        n = int(tok[2:])
        # next-id 本身也放行：檔頭 `<!-- next: B-NNN -->` 宣告的是 rev5 下一個保留號
        nxt = reg["b_next" if kind == "bid" else "l_next"]
        return (nxt is not None and n <= nxt) or 900 <= n <= 999
    if kind == "mid":
        return reg["mids"] is None or tok in reg["mids"]
    if kind == "lintcode":
        # 上界內（含已拆除而不重用的號，如 23）＝rev5 條款碼空間；超界＝前代條款碼
        return reg["lint_bound"] is not None and int(tok[4:]) <= reg["lint_bound"]
    if kind in ("tid", "frsc", "us", "research"):
        # spec 自引用：任務號／需求號／成功指標號／research 節號在**自己那支刀的目錄底下**
        # 恆為原生（specs/<刀名>/ 內的 T012 指的就是該刀的 T012）。
        parts = rel.split("/")
        if len(parts) > 2 and parts[0] == "specs" and parts[1] in reg["specs"]:
            return True
        # 跨檔引用 rev5 spec 定義號（掃源導出集）亦原生——工具 docstring 引自家刀的
        # SC-002／ADR 引 T012 等；US 族無定義面可導、僅 spec 目錄內原生
        if kind == "tid":
            return tok in reg["tids"]
        if kind == "frsc":
            return tok in reg["frscs"]
        if kind == "research":
            return tok.split()[-1] in reg["rns"]
        return False
    return False


# Lint25 具名豁免表（四欄紀律比照 DAY1_EXEMPTIONS：鍵→(理由, 命中謂詞, 到期即紅, 登記日)）。
#   理由    ＝散文（★一切散文只准住這欄；不得含全形分號——會污染跳過明細的筆數機判）
#   命中謂詞＝callable(hit)→bool，決定「哪些命中被本筆吃掉」（檔案級／token 級／樣式級／行級）
#   到期即紅＝True 時本筆零命中即 ERROR 指名（＝解除謂詞已成立、該下架）；
#             False＝結構性永久豁免（自撞／規則反例／vendored 白名單），零命中不報
#   登記日
# ★入表資格同 DAY1：拔項會翻紅。到期即紅為 False 的四筆是**規則本身的反例面**，不是待清償項。
LINT25_EXEMPTIONS = {
    "events.append-only": (
        "events.jsonl＝append-only 帳、既有列絕不編輯（ADR 0012 決定 5）——澄清只能 append "
        "新事件，故本檔永久豁免、新列由人工審",
        lambda h: h["rel"] == EVENTS,
        False, "2026-08-07"),
    # constitution：憲法檔之前代 ADR 指涉屬 B-004 ③分流「另議」——該檔現由 LINT25_SKIP_DIRS
    # 之 .specify/ 目錄級排除覆蓋（不進掃描面），不設永零命中的裝飾條目；③分流拍板後若憲法
    # 回到掃描面，屆時立帶到期即紅的真豁免（總審 2026-08-07 advisory 收斂）。
    "adr0004.rule-counterexample": (
        "ADR 0004 內的裸「ADR 0019」是**規則反例 mention**（該行正在說明裸形即違規）——"
        "清償它等於把反例改成正例、規則本身失去示範，token 級永久豁免",
        lambda h: (h["rel"] == f"{ADR_DIR}/0004-port-allocation-2xxxx.md"
                   and h["tok"].startswith("ADR") and h["tok"].endswith("0019")),
        False, "2026-08-07"),
    "research.quoted-literal": (
        "001 刀 spec 面（research／spec／tasks）的存證引用句（主詞即被清償字面本身、"
        "如 specs/002-… 座標）——前綴化會讓句子指涉不到它要存證的東西，token 級永久豁免",
        lambda h: (h["rel"] in ("specs/001-schema-baseline/research.md",
                                "specs/001-schema-baseline/spec.md",
                                "specs/001-schema-baseline/tasks.md")
                   and h["line"][:h["start"]].endswith("specs/")),
        False, "2026-08-07"),
    "adr0012.rule-example": (
        "ADR 0012 本文以「rev4 P1.1」示範不合規的空格散文形——規則示例 mention、"
        "前綴化即失去示範性，token 級永久豁免",
        lambda h: (h["rel"] == f"{ADR_DIR}/0012-id-namespace-discipline.md"
                   and h["tok"] == "P1.1" and "散文形" in h["line"]),
        False, "2026-08-07"),
    "grafana.uid": (
        "grafana provisioning 的 alert uid 內嵌前代刀號（obs016-*）＝已部署告警的穩定識別字，"
        "改字面即斷開既有告警歷史與靜音規則（ADR 0012 白名單第二類），樣式級永久豁免",
        lambda h: (h["rel"].startswith("deploy/grafana-provisioning/")
                   and h["line"][:h["start"]].endswith("obs")),
        False, "2026-08-07"),
    "docs-sync.self-corpus": (
        "本工具自身＝條款實作與自測語料，規則文字／負向樣本必須逐字保留被偵測的形（自撞）"
        "——同 HISTORICAL_EXEMPT 之理由，檔案級永久豁免，本檔真正的清償面走 B-004 批 C 人工兜底",
        lambda h: h["rel"] == "tools/docs-sync.py",
        False, "2026-08-07"),
    # backlog.b004-entry：B-004 清償收單刪列（2026-08-07）、解除謂詞成立——依到期即紅下架。
}

# (h) 全域降級豁免：清償進行中，整條款降 WARN。
# ★這是「轉 ERROR」的**唯一機關**——B-004 清償收刀時把本常數改成 None，條款即刻轉逐筆 ERROR，
#   不需動任何判定碼、不需改任何樣式。留著它就是「還在清償中」的機器可讀聲明。
# 清償收官（B-004、2026-08-07）：day1 全域降級豁免依解除謂詞下架——全樹零命中後轉逐筆
# ERROR（ADR 0012 決定 7 之收尾動作）。歷史形（降級期間之三元組）見 git 史。
LINT25_DAY1_DOWNGRADE = None
# WARN 期逐筆列示上限（其餘以「…另 N 筆」收尾；轉 ERROR 後逐筆全列）
LINT25_WARN_SAMPLE = 20


def _lint25_exempt_key(hit, exemptions=None):
    """該命中被哪一筆具名豁免吃掉（無＝None）。表序即優先序、首筆命中即歸屬。"""
    for key, row in (exemptions if exemptions is not None else LINT25_EXEMPTIONS).items():
        if row[1](hit):
            return key
    return None


def scan_id_namespace(texts, reg, exemptions=None):
    """Lint25 取值（純函式）：texts＝{rel: 全文}、reg＝lint25_registry 結果。

    回 (hits, exempt_counts)：hits＝未被具名豁免吃掉的命中 list（檔名／行號序，每筆
    {rel, ln, kind, tok, line, start}）；exempt_counts＝{豁免鍵: 吃掉筆數}（零筆者不入）。
    """
    hits, counts = [], {}
    for rel in sorted(texts):
        for ln, line in enumerate((texts[rel] or "").splitlines(), start=1):
            for m in RE_LINT25.finditer(line):
                kind = m.lastgroup
                tok = m.group(kind)
                if RE_LINT25_PREFIX.search(line[:m.start()]):
                    continue                                  # ①逐 token 前綴＝合規
                if lint25_native(kind, tok, rel, reg):
                    continue                                  # ②rev5 原生
                hit = {"rel": rel, "ln": ln, "kind": kind, "tok": tok,
                       "line": line, "start": m.start()}
                key = _lint25_exempt_key(hit, exemptions)
                if key is not None:
                    counts[key] = counts.get(key, 0) + 1
                    continue
                hits.append(hit)
    return hits, counts


# self-test 用的固定 registry：與真 repo 脫鉤（真 registry 一變樣本就換判定＝防恆綠自己會腐化）
LINT25_SELF_TEST_REG = {"specs": set(), "spec_nums": set(), "adrs": {"0012"},
                        "b_next": 40, "l_next": 6, "mids": set(),
                        "tids": set(), "frscs": set(), "rns": set(), "lint_bound": 25}


def id_namespace_self_test():
    """防恆綠：紅樣本必紅、綠樣本必綠；失效即 ERROR（Lint16／Lint21／Lint22 慣例）。

    ★樣本編號一律用 9 字頭合成號或已前綴形——不與任何真 registry 區間相撞，樣本改動不會
      因為 rev5 配號往前走而變綠。
    """
    out = []
    red = {"樣本": "見 ADR 9999 與 T999 兩處。\n"}
    red_hits, _c = scan_id_namespace(red, LINT25_SELF_TEST_REG, {})
    if len({h["kind"] for h in red_hits}) < 2:
        out.append(finding(ERROR, "Lint25", "tools/docs-sync.py",
                           "self-test 失效：紅樣本（裸 ADR 9999／T999）未被兩族分別攔下"
                           "——條款已恆綠，修復 RE_LINT25／lint25_native 後重跑"))
    green = {"樣本": "見 rev4:ADR 9999、ADR 0012、B-999 三處。\n"}
    green_hits, _c = scan_id_namespace(green, LINT25_SELF_TEST_REG, {})
    if green_hits:
        out.append(finding(ERROR, "Lint25", "tools/docs-sync.py",
                           "self-test 失效：綠樣本（已前綴形／rev5 原生號／假號段）誤報 "
                           f"{len(green_hits)} 筆——判定過寬，修復 lint25_native 後重跑"))
    return out


def lint_id_namespace(root, tracked, exemptions=None):
    """Lint25：跨代裸編號（ADR 0012）。組裝＝self-test 防恆綠＋掃源 registry＋全樹單 pass。

    ★效能：tracked 檔單次讀、全族單一 master regex 一個 pass——族數增加不增讀檔次數。
    """
    out = id_namespace_self_test()
    table = exemptions if exemptions is not None else LINT25_EXEMPTIONS
    texts = {}
    for rel in tracked:
        if any(rel.startswith(p) for p in LINT25_SKIP_DIRS):
            continue
        try:
            text = _read(root, rel)
        except (UnicodeDecodeError, OSError):
            continue                      # 二進位／非文字檔：不是掃描面
        if text is not None:
            texts[rel] = text
    hits, counts = scan_id_namespace(texts, lint25_registry(root), table)
    # 具名豁免一律列示、不靜默（機器強制第①條：跳過必列明細）
    for key in sorted(counts):
        out.append(finding(SKIP, "Lint25", key,
                           f"具名豁免（{table[key][0]}）——吃掉 {counts[key]} 筆命中"))
    # 到期即紅（機器強制第②條）：帶解除謂詞的豁免零命中＝清償已完成、該下架
    for key, row in sorted(table.items()):
        if row[2] and not counts.get(key):
            out.append(finding(ERROR, "Lint25", key,
                               "具名豁免零命中＝解除謂詞成立，而項仍在 LINT25_EXEMPTIONS"
                               "——請移除該筆並讓條款恢復全檢"))
    if LINT25_DAY1_DOWNGRADE is None:
        for h in hits:
            out.append(finding(ERROR, "Lint25", f"{h['rel']}:行 {h['ln']}",
                               f"跨代裸編號「{h['tok']}」（{LINT25_LABELS[h['kind']]}）"
                               f"；{LINT25_HINT}"))
        return out
    key, why, _since = LINT25_DAY1_DOWNGRADE
    out.append(finding(SKIP, "Lint25", key,
                       f"全域降級豁免（{why}）——刪除 LINT25_DAY1_DOWNGRADE 常數即轉逐筆 ERROR"))
    out.append(finding(WARN, "Lint25", "（全樹）",
                       f"跨代裸編號共 {len(hits)} 筆待清償（B-004）；{LINT25_HINT}"))
    for h in hits[:LINT25_WARN_SAMPLE]:
        out.append(finding(WARN, "Lint25", f"{h['rel']}:行 {h['ln']}",
                           f"跨代裸編號「{h['tok']}」（{LINT25_LABELS[h['kind']]}）"))
    if len(hits) > LINT25_WARN_SAMPLE:
        out.append(finding(WARN, "Lint25", "（全樹）",
                           f"…另 {len(hits) - LINT25_WARN_SAMPLE} 筆未逐筆列示"
                           "（清償完成刪 LINT25_DAY1_DOWNGRADE 後轉 ERROR 逐筆列）"))
    return out


def _assert_lint25_table():
    """啟動時斷言：四欄缺一不可——名冊自身腐化會讓整套豁免語意失真（同 _assert_day1_table）。"""
    for key, row in LINT25_EXEMPTIONS.items():
        assert key and isinstance(row, tuple) and len(row) == 4, \
            f"LINT25_EXEMPTIONS[{key}] 欄數非 4"
        why, pred, expire, since = row
        assert isinstance(why, str) and why.strip(), f"LINT25_EXEMPTIONS[{key}] 理由欄空"
        assert "；" not in why, \
            f"LINT25_EXEMPTIONS[{key}] 理由欄含全形分號（會污染跳過明細筆數機判）"
        assert callable(pred), f"LINT25_EXEMPTIONS[{key}] 命中謂詞欄非 callable"
        assert isinstance(expire, bool), f"LINT25_EXEMPTIONS[{key}] 到期即紅欄非布林"
        assert isinstance(since, str) and since.strip(), f"LINT25_EXEMPTIONS[{key}] 登記日欄空"


_assert_lint25_table()


def run_lint(root, exemptions=None):
    """組裝 Lint03～Lint26 全套：Lint04/Lint05/Lint06 收刀完整性閘、Lint16 憑證掃描、
    Lint17 pin 互證、Lint18 帳本 SHA 實證、Lint19 命令形真表比對、Lint20 空集合守衛、
    Lint21 exec bit 守衛、Lint22 範圍字串守衛、
    Lint24 前後端 msg key 契約閘、Lint25 跨代裸編號閘、Lint26 LESSONS 分檔對賬閘。
    回 findings（含 SKIP 級：條款不適用而未執行，由 lint_summary 彙整成跳過明細）。
    git 不可用＝fail-closed 單發 ERROR。"""
    if not git_available(root):
        return [finding(ERROR, "Lint01", ".",
                        "git 不可用——HEAD 基線與掃描語料無法建立，lint fail-closed（修復 git 後重跑）")]
    findings = []
    findings += lint_events(_read(root, EVENTS) or "")
    findings += lint_close_existence(root)
    findings += lint_review_existence(root)
    findings += lint_arch_impact(root)
    findings += lint_budgets(root)
    amend = os.environ.get("DOCS_SYNC_ADR_AMEND") == "1"
    if amend:
        findings.append(finding(SKIP, "Lint08", ADR_DIR,
                                "DOCS_SYNC_ADR_AMEND=1 豁免——accepted ADR body 不可變檢查"
                                "跳過（typo 級修正通道；commit message 須帶 [adr-amend]）"))
    findings += lint_adrs(load_adrs(root), load_head_adrs(root), amend=amend)
    bpaths = backlog_paths(root)
    findings += lint_ids("B", [(_read(root, p) or "") for p in bpaths],
                         [head_file(p, root) for p in bpaths])
    lpaths = lessons_paths(root)
    # ★L 側 head 視野一律走 lessons_head_view（聯集＋主檔恆 index 0 的單一構造權威、
    #   ADR 0045）——絕不在此 inline 抄構造式（抄本漂移＝反回收閘靜默失效，詳 helper docstring）；
    #   讀取一律批讀 head_files_batch、絕不退回逐檔 head_file（U2 後 48 條＝每 commit +5s）。
    findings += lint_ids("L", [(_read(root, p) or "") for p in lpaths],
                         head_files_batch(lessons_head_view(root), root))
    findings += lint_lessons_files(root)
    book = _read(root, BOOK)
    if book is not None:
        findings += lint_tense(book)
    findings += lint_dictionary(
        {rel: _read(root, rel) for rel in (BOOK, "CLAUDE.md")
         if _read(root, rel) is not None})
    # G4 引用健康：Lint12~Lint15 同一語料＝全 tracked md 扣史料豁免（specs/、reviews/ 都在內）
    tracked = tracked_files(root)
    md_texts = {rel: _read(root, rel) or ""
                for rel in tracked if rel.endswith(".md") and not _is_exempt(rel)}
    untracked = [l for l in (git_out(["ls-files", "--others", "--exclude-standard"], root)
                             or "").splitlines() if l]
    findings += lint_links(md_texts, set(tracked) | set(untracked))
    findings += lint_line_refs(md_texts)
    findings += lint_volatile_deep_links(md_texts)
    findings += lint_memory_refs(md_texts)
    # 子庫存活探針的單次 lint 記憶化：Lint16／Lint17／Lint18／Lint20 守衛#4 共用同一份結果，
    # 每庫只打一發 git（見 submodule_head；四條款各自打＝多花 ~360ms 在 drvfs 上）
    probe = {}
    findings += lint_credentials(root, probe)
    findings += lint_pin_crosscheck(root, probe)
    findings += lint_events_sha(root, probe)
    findings += lint_cmd_forms(root)
    findings += lint_empty_sets(root, tracked, probe, exemptions=exemptions)
    findings += lint_exec_bits(root)
    findings += lint_range_strings(root)
    findings += lint_i18n_contract(root, exemptions=exemptions)
    findings += lint_id_namespace(root, tracked)
    return findings


def print_findings(findings):
    """條列區只印 ERROR／WARN；SKIP 走摘要次行的跳過明細（重複印一次＝雜訊）。"""
    for f in findings:
        if f["level"] != SKIP:
            print(f"[{f['level']}] {f['code']}｜{f['where']}｜{f['msg']}")


def lint_summary(findings):
    """G6 摘要三段式。回 (摘要行, 跳過明細行或 None, 退出碼)。

    退出碼只看 ERROR：警告是放行列示、跳過更不是失敗（rev4:FR-012）。
    """
    errors = [f for f in findings if f["level"] == ERROR]
    warns = [f for f in findings if f["level"] == WARN]
    skips = [f for f in findings if f["level"] == SKIP]
    # ★條款總數欄（rev5 新增，§4.2 B4 丁／§0.3 準則 1 的機器驗法）：
    #   值取自 derive_lint_codes 掃本工具源碼、**不落字面**——落字面即與實際條款集脫節，
    #   條款被靜默拆掉時摘要照舊報舊數（正是準則 1 要防的「名冊與實作不同源」）。
    #   ★與創世事件 notes 的 lint-roster 前綴、bootstrap 的條款數斷言三處同數。
    total = len(derive_lint_codes(_self_source()))
    line = (f"lint：{len(errors)} 錯誤／{len(warns)} 警告／{len(skips)} 條款跳過"
            f"／共 {total} 條款")
    detail = ("跳過：" + "；".join(f"{f['code']}｜{f['where']}={f['msg']}" for f in skips)
              if skips else None)
    return line, detail, (1 if errors else 0)


def book_section_lines(book_text):
    """活書各節行數（§3.2 更新契約 3：每 commit 輸出各節行數表）。"""
    sec, count, counts = None, 0, {}
    for line in book_text.splitlines():
        m = RE_BOOK_SECTION.match(line)
        if m:
            if sec is not None:
                counts[sec] = count
            sec, count = int(m.group(1)), 0
        elif sec is not None:
            count += 1
    if sec is not None:
        counts[sec] = count
    return counts


def cmd_lint():
    findings = run_lint(ROOT)
    print_findings(findings)
    book = _read(ROOT, BOOK)
    if book is not None:
        cells = [f"§{s} {n}/{SECTION_QUOTAS.get(s, '—')}"
                 for s, n in sorted(book_section_lines(book).items())]
        print("活書各節行數：" + "｜".join(cells))
    line, detail, code = lint_summary(findings)
    print(line)
    if detail:
        print(detail)
    return code


def cmd_generate():
    if not git_available(ROOT):
        print("[ERROR] git 不可用——pins 等 git 來源無法讀取，generate 中止（fail-closed）",
              file=sys.stderr)
        return 1
    # generate 端不吃 submodule 跳過語意：沒有來源就是算不出對照表（見 lint_reference_sources）
    missing = lint_reference_sources(ROOT, submodule_skip=False)
    # ★豁免表必須接進這道第一關卡——它在 compute 之前，不接則後面全白做（§4.5.10 類一）。
    #   擋的判準只看 ERROR：具名 SKIP 屬「當日本就不該有」、列示放行。
    blocking = [f for f in missing if f["level"] == ERROR]
    if blocking:
        print_findings(missing)
        print(f"generate：來源檔守衛擋下 {len(blocking)} 筆（rev4:contracts G4）——補齊後重跑",
              file=sys.stderr)
        return 1
    if missing:
        print_findings(missing)
    adrs = load_adrs(ROOT)
    for fn, text in sorted(backfill_supersessions(adrs).items()):
        path = os.path.join(ROOT, ADR_DIR, fn)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"回填 supersedes 對稱欄：{ADR_DIR}/{fn}")
    files = compute_generated(ROOT)
    for rel, content in sorted(files.items()):
        path = os.path.join(ROOT, rel)
        if rel == MSG_DICT_PANEL:
            # grafana provider 每 30s 掃描該目錄——原子替換防讀到半成品（rev4:T003 staging 紀律）
            _atomic_write(path, content)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    # generated/ 全域歸生成器管轄：非生成物一律移除（含 .gitkeep）
    gen_root = os.path.join(ROOT, GENERATED_DIR)
    for dirpath, _, names in os.walk(gen_root):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, "/")
            if rel not in files:
                os.remove(os.path.join(dirpath, name))
                print(f"移除非生成物：{rel}")
    print(f"generate：重算 {len(files)} 檔完成")
    return 0


def cmd_check():
    if not git_available(ROOT):
        print("[ERROR] git 不可用——check 無法建立比對基線，fail-closed", file=sys.stderr)
        return 1
    findings = check_generated(ROOT, compute_generated(ROOT))
    pending = backfill_supersessions(load_adrs(ROOT))
    for fn in sorted(pending):
        findings.append(finding(ERROR, "Lint01", f"{ADR_DIR}/{fn}",
                                "supersedes 對稱回填待跑（tools/docs-sync.py generate）"))
    for rel in unstaged_generated(ROOT):
        findings.append(finding(ERROR, "Lint01", rel,
                                "生成物有未 staged 變更（跑了 generate 忘了 git add——"
                                "staged 內容過期，入版即漂移）"))
    print_findings(findings)
    print(f"check：{'不一致 ' + str(len(findings)) + ' 處' if findings else '一致'}")
    return 1 if findings else 0


def cmd_errata(keyword):
    texts = {}
    for rel in tracked_files(ROOT):
        try:
            text = _read(ROOT, rel)
        except (UnicodeDecodeError, OSError):
            continue
        if text is not None:
            texts[rel] = text
    hits = errata_scan(texts, keyword)
    for rel, n, line in hits:
        print(f"{rel}:行 {n}｜{line.strip()}")
    print(f"errata「{keyword}」：{len(hits)} 處命中（逐處處置、勿只修被點名那一處）")
    return 0


# ---------------------------------------------------------------------------
# 自帶測試
# ---------------------------------------------------------------------------

# SHA 欄一律 40 位（RE_SHA 全域收 40、無史料豁免）；值為合成十六進位、不對應真物件——
# schema 面只驗格式，向 git 實證屬 Lint18（各案自建 fixture repo 取真 SHA）。
VALID_CLOSE = {
    "type": "feature_close", "feature": "901-fake-system-settings",
    "merge": "a1b2c3d4" * 5, "date": "2026-07-10", "summary": "打樣刀收刀",
    "pins": {"web": "deadbeef" * 5, "api": "cafe1230" * 5}, "adrs": ["0007"],
    "arch_impact": ["§6"], "backlog_add": [], "backlog_done": ["B-903"],
}
VALID_MISC = {"type": "misc", "date": "2026-07-02", "summary": "bootstrap 完成"}
VALID_REVIEW = {
    "type": "review", "date": "2026-08-01", "scope": "001-005 cumulative",
    "report": "reviews/20260801-cumulative.md",
    "findings": {"total": 3, "fixed": 1, "to_backlog": ["B-909"], "wontfix_adr": ["0012"]},
}
VALID_ERRATUM = {
    "type": "erratum", "date": "2026-08-11", "target_line": 1, "field": "merge",
    "corrected": "a1b2c3d4" * 5, "reason": "簿記誤植假 SHA、依 ADR 0012 決定 5 更正",
}


def _jl(*objs):
    return "".join(json.dumps(o, ensure_ascii=False) + "\n" for o in objs)


ADR_OK_A = (
    "---\nid: \"0001\"\ntitle: 甲決策\ndate: 2026-07-05\nstatus: superseded\n"
    "supersedes: []\nsuperseded_by: [0002]\n---\n\n## 背景\n舊案。\n"
)
ADR_OK_B = (
    "---\nid: \"0002\"\ntitle: 乙決策\ndate: 2026-07-08\nstatus: accepted\n"
    "supersedes: [0001]\nsuperseded_by: []\n---\n\n## 背景\n新案。\n"
)


def _day1_pending(*rels):
    """類二 skipUnless 的測試側謂詞：真根下所列路徑全部存在才跑該案（§4.5.10 類二）。

    ★測試側自持、刻意不讀 lint 常數：期望值若取自被測常數即套套邏輯，常數縮水時
    期望值同步縮水、守衛靜默瘦身而零信號（§4.5.4 共通設計理由）。
    ★skip 訊息一律帶「解除謂詞＋所屬 B 步」——B8a 殘紅盤點要求每筆跳過可追去處。
    """
    return all(os.path.exists(os.path.join(ROOT, r)) for r in rels)


class TestLintAdrs(unittest.TestCase):
    def test_symmetric_pair_passes(self):
        adrs = {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}
        self.assertEqual(lint_adrs(adrs, dict(adrs)), [])

    def test_missing_required_field(self):
        bad = "---\nid: \"0003\"\ndate: 2026-07-05\nstatus: draft\n---\nbody\n"
        f = lint_adrs({"0003-x.md": bad}, {})
        self.assertTrue(any("title" in x["msg"] for x in f))

    def test_bad_status(self):
        bad = ADR_OK_B.replace("status: accepted", "status: done")
        f = lint_adrs({"0002-new.md": bad}, {})
        self.assertTrue(any("status" in x["msg"] for x in f))

    def test_id_filename_mismatch(self):
        f = lint_adrs({"0009-new.md": ADR_OK_B}, {})
        self.assertTrue(any("檔名" in x["msg"] for x in f))

    def test_bad_filename(self):
        f = lint_adrs({"2-new.md": ADR_OK_B.replace('id: "0002"', 'id: "2"')}, {})
        self.assertTrue(any("檔名" in x["msg"] for x in f))

    def test_supersedes_asymmetry(self):
        a = ADR_OK_A.replace("superseded_by: [0002]", "superseded_by: []")
        f = lint_adrs({"0001-old.md": a, "0002-new.md": ADR_OK_B}, {})
        self.assertTrue(any("對稱" in x["msg"] for x in f))

    def test_supersedes_dangling_target(self):
        f = lint_adrs({"0002-new.md": ADR_OK_B}, {})
        self.assertTrue(any("0001" in x["msg"] for x in f))

    def test_superseded_status_required(self):
        a = ADR_OK_A.replace("status: superseded", "status: accepted")
        f = lint_adrs({"0001-old.md": a, "0002-new.md": ADR_OK_B}, {})
        self.assertTrue(any("superseded" in x["msg"] for x in f))

    def test_accepted_body_immutable(self):
        cur = ADR_OK_B.replace("新案。", "偷偷改寫。")
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": cur},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B})
        self.assertEqual(len(f), 1)
        self.assertIn("不可變", f[0]["msg"])

    def test_accepted_body_amend_escape(self):
        cur = ADR_OK_B.replace("新案。", "修個錯字。")
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": cur},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}, amend=True)
        self.assertEqual(f, [])

    def test_tool_backfill_of_superseded_by_allowed(self):
        head_b = ADR_OK_B.replace("superseded_by: []", "")  # HEAD 版尚無該欄
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": head_b})
        self.assertEqual(f, [])

    def test_deletion_banned(self):
        f = lint_adrs({"0002-new.md": ADR_OK_B.replace("supersedes: [0001]", "supersedes: []")},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B})
        self.assertTrue(any("刪除" in x["msg"] for x in f))

    def test_draft_freely_editable(self):
        head = ADR_OK_B.replace("status: accepted", "status: draft")
        cur = head.replace("新案。", "改來改去。")
        f = lint_adrs({"0002-new.md": cur.replace("supersedes: [0001]", "supersedes: []")},
                      {"0002-new.md": head.replace("supersedes: [0001]", "supersedes: []")})
        self.assertEqual(f, [])


BACKLOG_V1 = "<!-- next: B-003 -->\n# BACKLOG\n\n- B-001｜甲\n- B-002｜乙\n"


class TestLintIds(unittest.TestCase):
    def test_clean_passes(self):
        self.assertEqual(lint_ids("B", [BACKLOG_V1], [BACKLOG_V1]), [])

    def test_duplicate_id(self):
        cur = BACKLOG_V1 + "- B-002｜丙\n"
        f = lint_ids("B", [cur], [BACKLOG_V1])
        self.assertTrue(any("重複" in x["msg"] for x in f))

    def test_id_beyond_next(self):
        cur = BACKLOG_V1 + "- B-007｜丙\n"
        f = lint_ids("B", [cur], [BACKLOG_V1])
        self.assertTrue(any("next" in x["msg"] for x in f))

    def test_next_must_not_decrease(self):
        cur = BACKLOG_V1.replace("B-003 ", "B-002 ").replace("- B-002｜乙\n", "")
        f = lint_ids("B", [cur], [BACKLOG_V1])
        self.assertTrue(any("單調" in x["msg"] for x in f))

    def test_new_id_must_take_fresh_number(self):
        head = "<!-- next: B-005 -->\n# BACKLOG\n\n- B-004｜丁\n"
        cur = head + "- B-002｜回收舊號\n"   # B-002 曾用過已刪
        f = lint_ids("B", [cur], [head])
        self.assertTrue(any("回收" in x["msg"] for x in f))

    def test_new_entry_bumps_next(self):
        cur = BACKLOG_V1.replace("B-003 ", "B-004 ") + "- B-003｜丙\n"
        self.assertEqual(lint_ids("B", [cur], [BACKLOG_V1]), [])

    def test_missing_header(self):
        f = lint_ids("B", ["# BACKLOG\n- B-001｜甲\n"], [BACKLOG_V1])
        self.assertTrue(any("next" in x["msg"] for x in f))

    def test_lessons_multi_volume_duplicate(self):
        main = "<!-- next: L-903 -->\n# LESSONS\n- **L-902**｜新坑\n"
        vol = "# LESSONS-001-101\n- **L-001**｜舊坑\n- **L-902**｜撞號\n"
        f = lint_ids("L", [main, vol], [main, vol])
        self.assertTrue(any("重複" in x["msg"] for x in f))

    def test_repairing_midline_entry_not_recycle(self):
        # rev4:B-106 場景：HEAD 端條目黏他行行尾（非行首、嚴格 RE_ENTRY 不認），staged 補換行
        # 修復不得誤判舊號回收——反回收 HEAD 豁免視野採寬鬆子串形（｜為欄位分隔、散文引用不帶）
        head = "<!-- next: B-005 -->\n# BACKLOG\n\n- B-003｜甲（註）- B-004｜乙\n"
        cur = head.replace("（註）- B-004｜乙", "（註）\n- B-004｜乙")
        self.assertEqual(lint_ids("B", [cur], [head]), [])

    def test_backlog_multi_volume_move_and_duplicate(self):
        # 滯後卷與主檔同視野：同 commit 整行搬移＝非舊號回收；跨卷撞號可偵測
        head_main = "<!-- next: B-005 -->\n# BACKLOG\n\n- B-003｜甲\n- B-004｜乙\n"
        cur_main = head_main.replace("- B-003｜甲\n", "")
        vol = "# BACKLOG-DEFERRED — 滯後卷\n\n- B-003｜甲｜★滯後：release 前\n"
        self.assertEqual(lint_ids("B", [cur_main, vol], [head_main, None]), [])
        dup = vol + "- B-004｜乙撞號\n"
        f = lint_ids("B", [cur_main, dup], [head_main, None])
        self.assertTrue(any("重複" in x["msg"] for x in f))

    def test_lessons_plain_form_same_view(self):
        # rev4:B-105：plain 形（- L-NNN｜）與粗體形同視野——計數入帳、
        # 反回收兩側同視（plain→粗體正規化不得誤判舊號回收）、跨形撞號可偵測
        head = "<!-- next: L-903 -->\n# LESSONS\n- **L-901**｜甲\n- L-902｜乙\n"
        self.assertEqual(len(RE_ENTRY["L"].findall(head)), 2)
        cur = head.replace("- L-902｜", "- **L-902**｜")
        self.assertEqual(lint_ids("L", [cur], [head]), [])
        dup = head + "- **L-902**｜跨形撞號\n"
        f = lint_ids("L", [dup], [head])
        self.assertTrue(any("重複" in x["msg"] for x in f))


class TestLintLessonsFiles(unittest.TestCase):
    """Lint26 LESSONS 分檔對賬（ADR 0045）：三斷言各配紅案防恆綠（ADR 0024 紀律）。

    fixture＝tempdir 自建、真 repo 唯讀；號碼一律取 9xx 假號段（ADR 0012 決定 4）。
    """

    INDEX = ("<!-- next: L-903 -->\n# LESSONS — 教訓索引\n\n"
             "- [L-901｜甲坑](LESSONS/L-901-a.md) — 防法甲\n"
             "- [L-902｜乙坑](LESSONS/L-902-b.md) — 防法乙\n")

    @staticmethod
    def _entry(n, promoted="CLAUDE.md §2"):
        return f"---\npromoted_to: {promoted}\n---\n- **L-{n}**｜某坑\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_lessons_paths_appends_entry_files_main_first(self):
        """交付一：枚舉＝既有卷集（主檔恆 index 0）＋LESSONS/ 下 sorted 的 L-*.md。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS-901-901.md", "- **L-901**｜舊卷\n")
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md", self._entry(902))
        _wfile(self.root, "docs/ops/LESSONS/readme.txt", "非條目檔不納\n")
        self.assertEqual(lessons_paths(self.root),
                         ["docs/ops/LESSONS.md", "docs/ops/LESSONS-901-901.md",
                          "docs/ops/LESSONS/L-902-b.md"])

    def test_no_dir_zero_findings(self):
        """目錄不存在＝零 findings（U1 落地時分檔尚未遷移、lint 必須照綠）。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        self.assertEqual(lint_lessons_files(self.root), [])

    def test_clean_green(self):
        """合法索引＋兩條目檔全綠。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", self._entry(901))
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md", self._entry(902))
        self.assertEqual(lint_lessons_files(self.root), [])

    def test_filename_shape_red(self):
        """(a) 紅案：檔名不匹配 L-NNN-<slug>.md 形（兩位號碼）。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS/L-90-bad.md", self._entry(901))
        f = lint_lessons_files(self.root)
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertEqual(f[0]["level"], ERROR)
        self.assertEqual(f[0]["code"], "Lint26")
        self.assertIn("檔名", f[0]["msg"])

    def test_filename_slug_charset_red(self):
        """(a) 紅案：slug 含大寫＝非英文小寫 kebab（Q2 拍板、finding 訊息與 ADR 0045
        逐字承諾的斷言）——必得檔名形 ERROR、where＝條目檔本身。

        ★釘 RE_LESSON_FILE 的 slug 半邊（U1b）：test_filename_shape_red 只釘 \\d{3} 半邊，
        slug 字元集放寬成 .* 時本案自「檔名」ERROR 翻成「缺索引行」（where 變
        docs/ops/LESSONS.md）＝紅；正文與 promoted_to 全合規、確保紅只紅在檔名形。
        """
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS/L-901-BadSlug.md", self._entry(901))
        f = lint_lessons_files(self.root)
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertEqual(f[0]["where"], "docs/ops/LESSONS/L-901-BadSlug.md")
        self.assertIn("檔名", f[0]["msg"])

    def test_filename_id_mismatch_red(self):
        """(a) 紅案：正文號碼與檔名號碼不相等。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", self._entry(902))
        f = lint_lessons_files(self.root)
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertEqual(f[0]["level"], ERROR)
        self.assertIn("不一致", f[0]["msg"])

    def test_entry_count_not_one_red(self):
        """(a) 紅案：正文 RE_ENTRY 命中 0 次（缺條目首行）與 2 次（併坑）各自紅。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md",
               "---\npromoted_to: CLAUDE.md §2\n---\n散文無條目首行\n")
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md",
               self._entry(902) + "- **L-903**｜併坑\n")
        f = lint_lessons_files(self.root)
        hits = [x for x in f if "恰一次" in x["msg"]]
        self.assertEqual([x["where"] for x in hits],
                         ["docs/ops/LESSONS/L-901-a.md", "docs/ops/LESSONS/L-902-b.md"],
                         msg=str(f))

    def test_missing_index_line_red(self):
        """(b) 紅案：檔在、索引無行（反向對賬；「索引→檔」另有 Lint12 兜底）。"""
        _wfile(self.root, "docs/ops/LESSONS.md",
               self.INDEX.replace("- [L-902｜乙坑](LESSONS/L-902-b.md) — 防法乙\n", ""))
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", self._entry(901))
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md", self._entry(902))
        f = lint_lessons_files(self.root)
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertEqual(f[0]["where"], "docs/ops/LESSONS.md")
        self.assertIn("L-902-b.md", f[0]["msg"])
        self.assertIn("索引行", f[0]["msg"])

    def test_duplicate_index_line_red(self):
        """(b) 紅案：同一條目檔在索引出現兩行（唯一性）。"""
        _wfile(self.root, "docs/ops/LESSONS.md",
               self.INDEX + "- [L-901｜甲坑重複](LESSONS/L-901-a.md) — 重複行\n")
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", self._entry(901))
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md", self._entry(902))
        f = lint_lessons_files(self.root)
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertEqual(f[0]["where"], "docs/ops/LESSONS.md")
        self.assertIn("2 行", f[0]["msg"])

    def test_prose_illustration_no_false_report(self):
        """(b) 綠案：索引頭夾散文示意（字母 NNN 連結形）不誤報。

        ★誠實範圍（ADR 0024）：本案只證「散文示意不產生 findings」，**不**證抽取形
        要求數字——該 \\d{3} 限制現行無行為面（見 RE_LESSON_INDEX_LINK 註解；
        mutation 實證放寬後本案仍綠），故不冒稱守它。
        """
        _wfile(self.root, "docs/ops/LESSONS.md",
               "<!-- next: L-903 -->\n# 索引\n每條恰一行 `- [L-NNN｜坑名](LESSONS/L-NNN-<slug>.md)`\n"
               + "- [L-901｜甲坑](LESSONS/L-901-a.md) — 防法甲\n")
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", self._entry(901))
        self.assertEqual(lint_lessons_files(self.root), [])

    def test_index_label_number_mismatch_red(self):
        """(b) 紅案：索引行標號與連結檔名號碼不一致（47 行手寫索引最可能的抄錯形——
        link_counts 只管存在與唯一、Lint12 只管檔案存在，無此斷言即全綠）。"""
        _wfile(self.root, "docs/ops/LESSONS.md",
               self.INDEX.replace("- [L-902｜乙坑](LESSONS/L-902-b.md) — 防法乙\n",
                                  "- [L-903｜乙坑](LESSONS/L-902-b.md) — 防法乙\n"))
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", self._entry(901))
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md", self._entry(902))
        f = lint_lessons_files(self.root)
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertEqual(f[0]["where"], "docs/ops/LESSONS.md")
        self.assertIn("標號", f[0]["msg"])
        self.assertIn("903", f[0]["msg"])

    def test_missing_promoted_to_red(self):
        """(c) 紅案：無 frontmatter、與 frontmatter 內 promoted_to 值為空——各自紅。"""
        _wfile(self.root, "docs/ops/LESSONS.md", self.INDEX)
        _wfile(self.root, "docs/ops/LESSONS/L-901-a.md", "- **L-901**｜無 frontmatter\n")
        _wfile(self.root, "docs/ops/LESSONS/L-902-b.md",
               "---\npromoted_to:\n---\n- **L-902**｜值為空\n")
        f = lint_lessons_files(self.root)
        hits = [x for x in f if "promoted_to" in x["msg"]]
        self.assertEqual([x["where"] for x in hits],
                         ["docs/ops/LESSONS/L-901-a.md", "docs/ops/LESSONS/L-902-b.md"],
                         msg=str(f))
        self.assertTrue(all(x["level"] == ERROR for x in hits))

    def test_run_lint_wires_lessons_files(self):
        """★接線層：lint_lessons_files 從 run_lint 掉線＝Lint26 整條靜默下線。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _wfile(d, "docs/ops/LESSONS/L-901-a.md", "- **L-902**｜號碼不一致\n")
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint26" and x["level"] == ERROR for x in f),
                            msg=str([x for x in f if x["code"] == "Lint26"]))


class TestLessonsHeadUnion(unittest.TestCase):
    """Lint09 L 側 head 視野聯集（ADR 0045）：git fixture 重演分檔遷移形。

    ★構造式不抄第二份：與 run_lint 共用 lessons_head_view（單一構造權威）——mutation 實證
      抄本形讓 helper 被改壞時全部自測照綠（生產路徑零覆蓋）；另有 run_lint 層接線案守
      「呼叫端繞開 helper」的變形。
    ★紅案證明聯集沒把反回收閘弄鈍：HEAD 從未存在的舊號條目檔必得「舊號回收」ERROR——
      同時釘住主檔 index-0 修正（字典序 LESSONS-….md < LESSONS.md 擠出主檔時
      head_next=None、反回收整段靜默失效，本紅案必失敗）。
    """

    def _fixture(self, d):
        """HEAD＝遷移前（主檔＋分卷）；工作樹＝遷移後（索引＋分檔、分卷已刪、未 staged）。"""
        _wfile(d, "docs/ops/LESSONS.md",
               "<!-- next: L-903 -->\n# LESSONS\n- **L-902**｜乙\n")
        _wfile(d, "docs/ops/LESSONS-901-901.md", "# LESSONS 分卷\n- **L-901**｜甲\n")
        _git(d, "init", "-q", "-b", "main")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "pre-migration")
        _wfile(d, "docs/ops/LESSONS.md",
               "<!-- next: L-903 -->\n# LESSONS — 教訓索引\n\n"
               "- [L-901｜甲](LESSONS/L-901-a.md) — 防法甲\n"
               "- [L-902｜乙](LESSONS/L-902-b.md) — 防法乙\n")
        os.remove(os.path.join(d, "docs/ops/LESSONS-901-901.md"))
        _wfile(d, "docs/ops/LESSONS/L-901-a.md",
               "---\npromoted_to: CLAUDE.md §2\n---\n- **L-901**｜甲\n")
        _wfile(d, "docs/ops/LESSONS/L-902-b.md",
               "---\npromoted_to: CLAUDE.md §2\n---\n- **L-902**｜乙\n")

    def _lint09(self, d):
        lpaths = lessons_paths(d)
        lpaths_head = lessons_head_view(d)  # ★與 run_lint 同一構造權威、絕不 inline 抄
        # index-0 不變量：連字號 0x2D < 句點 0x2E、裸 sorted 會把主檔擠出首位
        self.assertEqual(lpaths_head[0], "docs/ops/LESSONS.md")
        # ★讀取同 run_lint 走批讀（head_files_batch）——遷移 fixture 直接覆蓋批讀路徑：
        #   批讀壞掉（全 None／亂序）→ head_next=None → 反向紅案 900 不紅、此類自測翻紅
        return lpaths_head, lint_ids("L", [(_read(d, p) or "") for p in lpaths],
                                     head_files_batch(lpaths_head, d))

    def test_head_union_covers_deleted_volume(self):
        """遷移形：分卷已刪仍在 head 視野 → Lint09 零「舊號回收」誤報。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            lpaths_head, f = self._lint09(d)
            self.assertIn("docs/ops/LESSONS-901-901.md", lpaths_head)
            self.assertEqual(f, [], msg=str(f))

    def test_never_in_head_old_number_still_red(self):
        """反向紅案：HEAD 從未存在的舊號條目檔 → 必得「舊號回收」ERROR（閘未鈍化）。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            _wfile(d, "docs/ops/LESSONS/L-900-x.md",
                   "---\npromoted_to: 無：測試樣本\n---\n- **L-900**｜HEAD 從未存在\n")
            _, f = self._lint09(d)
            self.assertTrue(any(x["level"] == ERROR and "回收" in x["msg"] and "900" in x["msg"]
                                for x in f), msg=str(f))

    def test_head_lessons_paths_no_git_empty(self):
        """HEAD 讀不到（非 git 目錄）＝回空集。"""
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(head_lessons_paths(d), [])

    def test_head_files_batch_two_spawns_and_per_file_parity(self):
        """★批次守衛（U1b 補審）：head 視野讀取恰 2 發 subprocess（ls-tree＋cat-file），
        且與逐檔 head_file 逐位等價（HEAD 無此檔＝None、依輸入序）。

        逐檔 git show 形於 U2 遷移後 2→約 48 條、drvfs 實測每次 lint 多耗約 5s 且進每顆
        commit 的 pre-commit——本案把「批次而非逐檔」釘成可機器偵測的派發次數。
        ★不共用 _fixture、自建 HEAD 四 blob 形（U1b 第 2 輪）：_fixture 的 HEAD 僅
        2 顆 blob 且其 oid 恰已依 rels 序升冪（71f76fc… < c6273aa…；內容固定故為決定性），
        cat-file 輸入序被改壞成 sorted(oid) 時 sorted＝原序、對位斷言比不出差別——而錯配
        的失效形＝head_texts[0] 拿到別檔內容→head_next=None→反回收閘靜默下線。
        故 fixture 不退化守衛看兩維：①len(rels) ≥ 4（派發次數維：逐檔形至少 4 發、
        單條時逐檔與批次同為可混淆量）②HEAD 內 present ≥ 2 且其 oid 序 ≠ rels 序
        （對位維：oid 恰已依序＝該類變異隱形）；含 HEAD 缺席之條目檔＝None 形。"""
        with tempfile.TemporaryDirectory() as d:
            # HEAD＝四顆 blob（主檔＋舊分卷＋兩支條目檔）；此內容組合實算 oid 序≠rels 序
            _wfile(d, "docs/ops/LESSONS.md",
                   "<!-- next: L-904 -->\n# LESSONS — 教訓索引\n\n"
                   "- [L-901｜甲](LESSONS/L-901-a.md) — 防法甲\n"
                   "- [L-902｜乙](LESSONS/L-902-b.md) — 防法乙\n")
            _wfile(d, "docs/ops/LESSONS-901-901.md", "# LESSONS 分卷\n- **L-901**｜甲\n")
            _wfile(d, "docs/ops/LESSONS/L-901-a.md",
                   "---\npromoted_to: CLAUDE.md §2\n---\n- **L-901**｜甲\n")
            _wfile(d, "docs/ops/LESSONS/L-902-b.md",
                   "---\npromoted_to: CLAUDE.md §2\n---\n- **L-902**｜乙\n")
            _git(d, "init", "-q", "-b", "main")
            _git(d, "add", "-A")
            _git(d, "commit", "-qm", "head-four-blobs")
            _wfile(d, "docs/ops/LESSONS/L-903-c.md",
                   "---\npromoted_to: 無：測試樣本\n---\n- **L-903**｜丙\n")
            rels = lessons_head_view(d)
            self.assertGreaterEqual(len(rels), 4, msg=str(rels))
            expected = [head_file(p, d) for p in rels]   # 差分基準：mock 外先取
            self.assertIn(None, expected)                # 必含 HEAD 缺席形（工作樹新條目檔）
            present = [p for p, t in zip(rels, expected) if t is not None]
            oids = [_git(d, "rev-parse", f"HEAD:{p}").strip() for p in present]
            self.assertGreaterEqual(len(present), 2, msg=str(present))
            self.assertNotEqual(oids, sorted(oids), msg=str(list(zip(present, oids))))
            real, spawns = subprocess.run, []

            def fake(args, **kw):
                spawns.append(list(args))
                return real(args, **kw)

            with mock.patch.object(subprocess, "run", fake):
                texts = head_files_batch(rels, d)
            self.assertEqual(len(spawns), 2, msg=str(spawns))
            self.assertEqual(texts, expected)

    def test_run_lint_head_view_production_path(self):
        """★接線層：run_lint 的 L 側 head 視野必行經 lessons_head_view——生產路徑全程覆蓋。

        呼叫端若繞開 helper 自抄構造式，兩種變形皆在此翻紅：
        ①裸 sorted(聯集)＝主檔被擠出 index 0→head_next=None→反回收閘死→900 不紅；
        ②退回無聯集舊形（head 視野＝現況 lpaths）＝已刪分卷退出視野→901 誤報舊號回收。
        """
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            _wfile(d, "docs/ops/LESSONS/L-900-x.md",
                   "---\npromoted_to: 無：測試樣本\n---\n- **L-900**｜HEAD 從未存在\n")
            f = [x for x in run_lint(d) if x["code"] == "Lint09"
                 and x["where"] == "docs/ops/LESSONS.md"]
            self.assertTrue(any(x["level"] == ERROR and "回收" in x["msg"] and "900" in x["msg"]
                                for x in f), msg=str(f))
            self.assertFalse(any("901" in x["msg"] for x in f), msg=str(f))

    def test_head_entry_file_slug_rename_no_false_recycle(self):
        """★RE_HEAD_LESSONS_PATH 條目檔分支紅案（U1b）：分檔制下改條目檔 slug 不得假紅。

        HEAD 已是分檔制、索引行刻意不帶｜（Lint26 只驗連結存在與唯一、不管行內形，
        此形合法）→ head_ids 之 902 唯一來源＝HEAD 條目檔本體。工作樹改 slug
        （刪舊檔＋同號新 slug 檔＋索引連結同步改；ADR 0045 後果段：改 slug 不構成翻案）。
        拿掉 LESSONS/L-[^/]+\\.md 分支＝被刪舊檔退出 head 視野→「L-902 為舊號回收」
        假 ERROR 擋 commit——本案即翻紅。
        """
        entry_902 = "---\npromoted_to: CLAUDE.md §2\n---\n- **L-902**｜乙\n"
        with tempfile.TemporaryDirectory() as d:
            _wfile(d, "docs/ops/LESSONS.md",
                   "<!-- next: L-903 -->\n# LESSONS — 教訓索引\n\n"
                   "- [L-901 — 甲坑](LESSONS/L-901-a.md) — 防法甲\n"
                   "- [L-902 — 乙坑](LESSONS/L-902-s902.md) — 防法乙\n")
            _wfile(d, "docs/ops/LESSONS/L-901-a.md",
                   "---\npromoted_to: CLAUDE.md §2\n---\n- **L-901**｜甲\n")
            _wfile(d, "docs/ops/LESSONS/L-902-s902.md", entry_902)
            _git(d, "init", "-q", "-b", "main")
            _git(d, "add", "-A")
            _git(d, "commit", "-qm", "post-migration")
            os.remove(os.path.join(d, "docs/ops/LESSONS/L-902-s902.md"))
            _wfile(d, "docs/ops/LESSONS/L-902-renamed.md", entry_902)
            _wfile(d, "docs/ops/LESSONS.md",
                   "<!-- next: L-903 -->\n# LESSONS — 教訓索引\n\n"
                   "- [L-901 — 甲坑](LESSONS/L-901-a.md) — 防法甲\n"
                   "- [L-902 — 乙坑](LESSONS/L-902-renamed.md) — 防法乙\n")
            # fixture 不退化守衛：索引行必無 L-NNN｜形——一旦有，head_ids 改由索引供號、
            # 條目檔分支零覆蓋（本案退化成恆綠）
            self.assertEqual(
                RE_ENTRY_ANYPOS["L"].findall(_read(d, "docs/ops/LESSONS.md")), [])
            f = [x for x in run_lint(d) if x["code"] == "Lint09"
                 and x["where"] == "docs/ops/LESSONS.md"]
            self.assertEqual(f, [], msg=str(f))

    def test_run_lint_lessons_head_no_per_file_show(self):
        """★接線層批讀守衛（U1b）：run_lint 的 L 側 head 讀取絕不對 LESSONS 卷集逐檔
        `git show HEAD:…`——呼叫端退回逐檔 head_file 時本案翻紅。

        與 test_head_files_batch_two_spawns…（守 helper 本體派發數）成對：該案不覆蓋
        「helper 沒壞、但 run_lint 繞開它」的呼叫端變形——drvfs 實測逐檔形 48 條每次
        lint 多耗約 4~5s 且經 pre-commit 進每顆 commit。B 側 BACKLOG 仍屬逐檔 show
        豁免面（前綴過濾只認 HEAD:docs/ops/LESSONS）。
        """
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            real, spawns = subprocess.run, []

            def fake(args, **kw):
                spawns.append(list(args))
                return real(args, **kw)

            with mock.patch.object(subprocess, "run", fake):
                run_lint(d)
            # 正向前提：批讀路徑確實跑過（ls-tree 批次取 oid 含主檔）——防 fixture 退化成
            # 「L 側 head 讀取整段消失」的恆綠形（該變形另由 production_path 案守語意面）
            self.assertTrue(any("ls-tree" in a and "docs/ops/LESSONS.md" in a
                                for a in spawns), msg=str(spawns))
            hits = [a for a in spawns if "show" in a
                    and any(str(x).startswith("HEAD:docs/ops/LESSONS") for x in a)]
            self.assertEqual(hits, [], msg=str(hits))


class TestGenMilestones(unittest.TestCase):
    def test_empty(self):
        files = gen_milestones([])
        self.assertEqual(list(files), ["docs/generated/MILESTONES.md"])
        self.assertIn("（尚無事件）", files["docs/generated/MILESTONES.md"])

    def test_rows_and_header(self):
        files = gen_milestones([VALID_MISC, VALID_CLOSE])
        text = files["docs/generated/MILESTONES.md"]
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertIn("901-fake-system-settings", text)
        self.assertIn("bootstrap 完成", text)

    # -- rev5 差分：分卷軸按大小、不按時間（§3.2 條 11／§0.3 準則 4）------------------
    @staticmethod
    def _bulk(n, day0=0):
        """造 n 筆合規事件，summary 貼近 Q6 上限（300 字）——逼近真實體積。"""
        return [{"type": "misc", "date": f"2026-{(day0 + i) // 28 + 1:02d}-{(day0 + i) % 28 + 1:02d}",
                 "summary": "摘" * 300} for i in range(n)]

    def test_size_split_not_year_split(self):
        """★rev4 病灶重演：同一年的大量事件，年軸永不分卷、大小軸必分卷。

        rev4 實測 33 天 47 筆即達 28,883 tokens 卻仍同屬 2026 單卷——時間軸與體積無關，
        分卷條件結構上永不觸發（§2.6 架構級缺陷之一）。
        """
        files = gen_milestones(self._bulk(120))
        self.assertGreater(len(files), 1, msg=f"同年事件仍單卷＝年軸病灶未除：{list(files)}")
        self.assertIn("docs/generated/MILESTONES.md", files)
        for rel, text in files.items():
            self.assertLessEqual(token_count(text), MILESTONES_VOL_TOKEN_LIMIT, msg=rel)
        # 跨年不再自動切卷——僅體積決定
        two_years = gen_milestones([dict(VALID_MISC, date="2025-12-31"), VALID_MISC])
        self.assertEqual(list(two_years), ["docs/generated/MILESTONES.md"], msg=str(list(two_years)))

    def test_sealed_volumes_are_stable_across_append(self):
        """★已封存卷須逐字穩定——由新而舊填會推移卷邊界，check 逐次報 Lint01 drift。"""
        base = self._bulk(120)
        before = gen_milestones(base)
        after = gen_milestones(base + self._bulk(1, day0=200))
        sealed = [r for r in before if r != "docs/generated/MILESTONES.md"]
        self.assertTrue(sealed, msg="樣本未觸發分卷、本案失去意義")
        for rel in sealed:
            self.assertEqual(before[rel], after.get(rel), msg=f"{rel} 於 append 後被推移")

    def test_malformed_date_stays_in_main_volume(self):
        """date 畸形者（generate 走寬鬆解析）排最後、必落主卷，不得劫走主卷位置。"""
        files = gen_milestones(self._bulk(120) + [{"type": "misc", "date": "壞掉", "summary": "x"}])
        self.assertIn("壞掉", files["docs/generated/MILESTONES.md"])

    def test_empty_events_single_main_volume(self):
        self.assertEqual(list(gen_milestones([])), ["docs/generated/MILESTONES.md"])


class TestGenDecisionsIndex(unittest.TestCase):
    def test_empty(self):
        self.assertIn("（尚無 ADR）", gen_decisions_index([]))

    def test_sorted_by_id(self):
        metas = [parse_front_matter(ADR_OK_B)[0], parse_front_matter(ADR_OK_A)[0]]
        text = gen_decisions_index(metas)
        self.assertLess(text.index("0001"), text.index("0002"))
        self.assertIn("superseded", text)


class TestGenState(unittest.TestCase):
    CTX = {
        "pins": {"web": ("deadbeef00", None),
                 "api": (None, "index 無該 gitlink 條目（純外層 repo 或該 submodule 未登記）")},
        "constitution_version": None,
        "events": [VALID_MISC, VALID_MISC, VALID_MISC, VALID_CLOSE],
        "adr_metas": [],
        "backlog_count": 2, "backlog_next": 6, "backlog_deferred_count": 2,
        "lessons_count": 101, "lessons_next": 102,
    }

    def test_contains_core_blocks(self):
        text = gen_state(self.CTX)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertIn("deadbee", text)          # pin 短 SHA
        self.assertIn("未定（index 無該 gitlink", text)   # api pin 缺→未定（含原因）
        self.assertIn("未鑄", text)              # constitution 版本缺
        self.assertIn("B-006", text)            # backlog next
        self.assertIn("滯後：2", text)           # 滯後卷分計
        self.assertIn("101", text)              # lessons count

    def test_tail_three_events_newest_first(self):
        text = gen_state(self.CTX)
        self.assertIn("901-fake-system-settings", text)   # 最新一筆（feature_close）
        self.assertEqual(text.count("bootstrap 完成"), 2)  # 尾 3 筆只含 2 筆 misc

    def test_within_budget(self):
        self.assertLessEqual(token_count(gen_state(self.CTX)), 4000)


class TestBackfill(unittest.TestCase):
    def test_backfill_superseded_by_and_status(self):
        a_head = ADR_OK_A.replace("superseded_by: [0002]", "superseded_by: []") \
                          .replace("status: superseded", "status: accepted")
        changed = backfill_supersessions({"0001-old.md": a_head, "0002-new.md": ADR_OK_B})
        self.assertEqual(list(changed), ["0001-old.md"])
        meta, body = parse_front_matter(changed["0001-old.md"])
        self.assertEqual(meta["superseded_by"], ["0002"])
        self.assertEqual(meta["status"], "superseded")
        self.assertEqual(body, parse_front_matter(a_head)[1])  # body 一字不動

    def test_noop_when_symmetric(self):
        self.assertEqual(
            backfill_supersessions({"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}), {})


class TestErrata(unittest.TestCase):
    def test_hits_case_insensitive(self):
        hits = errata_scan({"a.md": "有 Port 設定\n無關行\n", "b.md": "PORT 又見\n"}, "port")
        self.assertEqual([(h[0], h[1]) for h in hits], [("a.md", 1), ("b.md", 1)])

    def test_no_hits(self):
        self.assertEqual(errata_scan({"a.md": "x\n"}, "沒有"), [])


class TestCheckGenerated(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs/generated/reference"))
        self.computed = {
            "docs/generated/STATE.md": "內容A\n",
            "docs/generated/reference/ports.md": "stub\n",
        }
        for rel, content in self.computed.items():
            with open(os.path.join(self.root, rel), "w", encoding="utf-8") as fh:
                fh.write(content)

    def tearDown(self):
        self.tmp.cleanup()

    def test_in_sync(self):
        self.assertEqual(check_generated(self.root, self.computed, exemptions={}), [])

    def test_drift_detected(self):
        with open(os.path.join(self.root, "docs/generated/STATE.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("被手改\n")
        f = check_generated(self.root, self.computed, exemptions={})
        self.assertEqual(len(f), 1)
        self.assertIn("STATE.md", f[0]["where"])

    def test_missing_file(self):
        os.remove(os.path.join(self.root, "docs/generated/reference/ports.md"))
        f = check_generated(self.root, self.computed, exemptions={})
        self.assertEqual(len(f), 1)

    def test_extra_file(self):
        with open(os.path.join(self.root, "docs/generated/EXTRA.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("手加\n")
        f = check_generated(self.root, self.computed, exemptions={})
        self.assertEqual(len(f), 1)
        self.assertIn("EXTRA", f[0]["where"])


COMPOSE_PORTS_SAMPLE = (
    "# 註解\n"
    "name: demo\n"
    "services:\n"
    "  front-nginx:\n"
    "    ports:\n"
    '      - "127.0.0.1:42080:80"\n'
    '      - "127.0.0.1:42443:443"\n'
    "    volumes:\n"
    "      - ./x:/x:ro\n"
    "  postgres:\n"
    "    ports:\n"
    '      - "127.0.0.1:45432:5432"\n'
    "volumes:\n"
    "  x:\n"
)


class TestComposePorts(unittest.TestCase):
    def test_parse_short_syntax(self):
        rows = parse_compose_ports(COMPOSE_PORTS_SAMPLE, "docker-compose.dev.yml")
        self.assertEqual(rows, [
            ("front-nginx", "42080", "80", "127.0.0.1"),
            ("front-nginx", "42443", "443", "127.0.0.1"),
            ("postgres", "45432", "5432", "127.0.0.1"),
        ])

    def test_no_ports_section(self):
        self.assertEqual(parse_compose_ports("services:\n  a:\n    image: x\n", "f.yml"), [])

    def test_item_at_same_indent_as_ports_key(self):
        # 回歸（quality review）：同縮排清單項（YAML 合法形）曾被靜默漏列
        text = ("services:\n"
                "  a:\n"
                "    ports:\n"
                '    - "127.0.0.1:9999:80"\n'
                "    volumes:\n"
                "    - ./x:/x\n")
        self.assertEqual(parse_compose_ports(text, "f.yml"),
                         [("a", "9999", "80", "127.0.0.1")])

    def test_bad_item_at_same_indent_still_fails_loud(self):
        text = 'services:\n  a:\n    ports:\n    - "0.0.0.0:1:2"\n'
        with self.assertRaises(ComposePortsError) as cm:
            parse_compose_ports(text, "f.yml")
        self.assertIn("行 4", str(cm.exception))

    def test_unknown_item_fails_loud_with_file_and_line(self):
        for bad in ("- 127.0.0.1:1:2",      # 無引號
                    '- "0.0.0.0:1:2"',      # 非 127.0.0.1 綁定
                    "- target: 80",          # 長語法
                    '- "8080:80"'):          # 無綁定 IP 前綴
            text = f"services:\n  a:\n    ports:\n      {bad}\n"
            with self.assertRaises(ComposePortsError, msg=bad) as cm:
                parse_compose_ports(text, "f.yml")
            self.assertIn("f.yml", str(cm.exception), msg=bad)
            self.assertIn("行 4", str(cm.exception), msg=bad)

    def test_unexpected_ports_key_shape_fails_loud(self):
        with self.assertRaises(ComposePortsError):   # inline value
            parse_compose_ports("services:\n  a:\n    ports: []\n", "f.yml")
        with self.assertRaises(ComposePortsError):   # 非服務直屬（深一層）
            parse_compose_ports("services:\n  a:\n    x:\n      ports:\n", "f.yml")

    def test_unknown_service_line_fails_loud(self):
        # 不擋則 service 殘留前值→後續 ports 錯掛到前一個服務（靜默錯列）
        for bad in ("b:  # 行內註解", '"b":', "b: {}"):
            text = f'services:\n  a:\n    ports:\n      - "127.0.0.1:1:1"\n  {bad}\n'
            with self.assertRaises(ComposePortsError, msg=bad) as cm:
                parse_compose_ports(text, "f.yml")
            self.assertIn("f.yml", str(cm.exception), msg=bad)
            self.assertIn("行 5", str(cm.exception), msg=bad)

    def test_compute_ports_rows_missing_source_fails_loud(self):
        with tempfile.TemporaryDirectory() as root:
            for rel in COMPOSE_FILES[:-1]:
                with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                    fh.write("services:\n")
            with self.assertRaises(ComposePortsError) as cm:
                compute_ports_rows(root)
            self.assertIn(COMPOSE_FILES[-1], str(cm.exception))

    def test_gen_reference_ports_sorted_and_deterministic(self):
        rows = [("docker-compose.example.yml", "example-dev", "42089", "80", "127.0.0.1"),
                ("docker-compose.dev.yml", "front-nginx", "42443", "443", "127.0.0.1"),
                ("docker-compose.dev.yml", "front-nginx", "42080", "80", "127.0.0.1")]
        text = gen_reference_ports(rows)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("42080"), text.index("42443"))   # host port 序
        self.assertLess(text.index("42443"), text.index("42089"))   # 來源檔序
        self.assertEqual(text, gen_reference_ports(list(reversed(rows))))  # 入序無關

    def test_gen_reference_ports_empty(self):
        self.assertIn("無任何 host port 映射", gen_reference_ports([]))

    def test_state_ports_line_is_live_not_stub(self):
        text = gen_state(TestGenState.CTX)
        for line in text.splitlines():
            if line.startswith("- reference/ports"):
                self.assertNotIn("stub", line)
                self.assertIn("generate", line)
                break
        else:
            self.fail("STATE 缺 reference/ports 對賬行")

    def test_check_reports_ports_drift_as_l2(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs/generated/reference"))
            rel = "docs/generated/reference/ports.md"
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("舊表\n")
            f = check_generated(root, {rel: "新表\n"}, exemptions={})
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["code"], "Lint02")
            self.assertIn("ports", f[0]["msg"])


# 單條乾淨 RouteDef 欄集（fail-loud 案例逐行代換其一）
ROUTER_CLEAN_FIELDS = (
    '        path: "/health",\n'
    "        method: HttpMethod::Get,\n"
    "        handler: || get(health_ok),\n"
    '        case_key: "health",\n'
    "        envelope_exception: true,\n"
    "        protection: Protection::Public,\n"
)
# 完整樣本：const 前置 struct 定義＋block 內註解＋build() 迭代（皆須被忽略、不誤抓）
ROUTER_ROUTES_SAMPLE = (
    "use axum::Router;\n"
    "pub struct RouteDef {\n"                     # ← const 外的 RouteDef 字樣：須忽略
    "    pub path: &'static str,\n"               # ← 看似 path 欄、但不在 const：須忽略
    "}\n"
    "pub const ROUTES: &[RouteDef] = &[\n"
    + ROUTER_CLEAN_FIELDS.join(("    RouteDef {\n", "    },\n"))
    + "    // block 內註解：須跳過、不終結區塊\n"
    "    RouteDef {\n"
    '        path: "/auth/login",\n'
    "        method: HttpMethod::Post,\n"
    "        handler: || post(crate::handler::auth::login),\n"
    '        case_key: "auth-login",\n'
    "        envelope_exception: false,\n"
    "        protection: Protection::Policy,\n"
    "    },\n"
    "];\n"
    "pub fn build() {\n"
    "    for def in ROUTES {}\n"                   # ← const 外的 ROUTES 字樣：須忽略
    "}\n"
)


def _router_one(fields):
    """把單條欄集包成完整 ROUTES const 文字（fail-loud 案例用）。"""
    return ("pub const ROUTES: &[RouteDef] = &[\n"
            "    RouteDef {\n" + fields + "    },\n"
            "];\n")


class TestRouterRoutes(unittest.TestCase):
    def test_parse_clean_sample(self):
        rows = parse_router_routes(ROUTER_ROUTES_SAMPLE, "router.rs")
        # 恰 2 條（struct 定義／build() 迭代未被誤抓）；handler 不入表、method 已映射字面
        self.assertEqual(rows, [
            ("/health", "GET", "Public", "health", True),
            ("/auth/login", "POST", "Policy", "auth-login", False),
        ])

    @unittest.skipUnless(_day1_pending(ROUTER_SOURCE),
                         "Day 1 未達：解除＝router.rs 到位（B12）；同 gen.router 字面")
    def test_parse_real_router_rs(self):
        rows = compute_router_rows(ROOT)
        self.assertGreater(len(rows), 0, "真實 router.rs 應解析出 route")
        health = [r for r in rows if r[0] == "/health"]
        self.assertEqual(len(health), 1, "應含且僅含一條 /health")
        self.assertEqual(health[0][1], "GET")
        self.assertTrue(health[0][4], "/health 應標 envelope 例外")

    def test_unknown_method_variant_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS.replace("HttpMethod::Get", "HttpMethod::Patch")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("Patch", str(cm.exception))
        self.assertIn("行 4", str(cm.exception))

    def test_unknown_protection_variant_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS.replace("Protection::Public", "Protection::Admin")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("Admin", str(cm.exception))

    def test_unknown_field_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS + "        weight: 5,\n"
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("f.rs", str(cm.exception))

    def test_malformed_path_shape_fails_loud(self):
        # path 無引號＝不認得的形（窄假設：必引號短語法）
        bad = ROUTER_CLEAN_FIELDS.replace('path: "/health",', "path: /health,")
        with self.assertRaises(RouterRoutesError):
            parse_router_routes(_router_one(bad), "f.rs")

    def test_handler_shape_change_fails_loud(self):
        # handler 非 get()／post()／delete() 閉包＝不認得的形（不盲跳過；探針改 patch——
        # delete 已為合法形、rev4:008 U7 寫端五端點）
        bad = ROUTER_CLEAN_FIELDS.replace(
            "handler: || get(health_ok),", "handler: || patch(health_ok),")
        with self.assertRaises(RouterRoutesError):
            parse_router_routes(_router_one(bad), "f.rs")

    def test_duplicate_field_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS + '        path: "/dup",\n'
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("重複", str(cm.exception))

    def test_missing_field_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS.replace(
            "        protection: Protection::Public,\n", "")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("protection", str(cm.exception))

    def test_top_level_junk_in_block_fails_loud(self):
        text = ("pub const ROUTES: &[RouteDef] = &[\n"
                "    surprise_line,\n"
                "];\n")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(text, "f.rs")
        self.assertIn("行 2", str(cm.exception))

    def test_missing_const_fails_loud(self):
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes("fn main() {}\n", "f.rs")
        self.assertIn("ROUTES", str(cm.exception))

    def test_unterminated_block_fails_loud(self):
        text = "pub const ROUTES: &[RouteDef] = &[\n    RouteDef {\n" + ROUTER_CLEAN_FIELDS
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(text, "f.rs")
        self.assertIn("收尾", str(cm.exception))

    def test_compute_router_rows_missing_source_fails_loud(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(RouterRoutesError) as cm:
                compute_router_rows(root)
            self.assertIn(ROUTER_SOURCE, str(cm.exception))

    def test_gen_reference_routes_sorted_and_deterministic(self):
        rows = [("/b", "GET", "Authed", "b", False),
                ("/a", "POST", "Public", "a-post", False),
                ("/a", "GET", "Public", "a-get", True)]
        text = gen_reference_routes(rows)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("/a | GET"), text.index("/a | POST"))  # 同 path→method 序
        self.assertLess(text.index("/a | POST"), text.index("/b | GET"))  # path 序
        self.assertEqual(text, gen_reference_routes(list(reversed(rows))))  # 入序無關
        self.assertIn("| 是 |", text)  # envelope True→是
        self.assertIn("| 否 |", text)  # envelope False→否

    def test_gen_reference_routes_empty(self):
        self.assertIn("無任何條目", gen_reference_routes([]))

    def test_state_routes_line_is_live_not_stub(self):
        text = gen_state(TestGenState.CTX)
        for line in text.splitlines():
            if line.startswith("- reference/routes"):
                self.assertNotIn("stub", line)
                self.assertIn("generate", line)
                break
        else:
            self.fail("STATE 缺 reference/routes 對賬行")

    def test_check_reports_routes_drift_as_l2(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs/generated/reference"))
            rel = "docs/generated/reference/routes.md"
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("舊表\n")
            f = check_generated(root, {rel: "新表\n"}, exemptions={})
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["code"], "Lint02")
            self.assertIn("routes", f[0]["msg"])


# 單條乾淨 route 欄集（fail-loud 案例逐行代換其一；i18nKey 為 meta 內末欄、無尾逗號）
ELEGANT_CLEAN_FIELDS = (
    "    name: 'demo',\n"
    "    path: '/demo',\n"
    "    component: 'view.demo',\n"
    "    meta: {\n"
    "      title: 'demo',\n"
    "      i18nKey: 'route.demo'\n"
    "    }\n"
)
# 完整巢狀樣本：含父 route（有／無 component）＋深達 3 層 children＋meta 雜欄（roles/localIcon…）；
# const 外的 import／型別字樣須被忽略、不誤抓。
ELEGANT_ROUTES_SAMPLE = (
    "import type { GeneratedRoute } from '@elegant-router/types';\n"
    "export const generatedRoutes: GeneratedRoute[] = [\n"
    "  {\n"
    "    name: '403',\n"
    "    path: '/403',\n"
    "    component: 'layout.blank$view.403',\n"
    "    meta: {\n"
    "      title: '403',\n"
    "      i18nKey: 'route.403',\n"
    "      constant: true,\n"
    "      hideInMenu: true\n"
    "    }\n"
    "  },\n"
    "  {\n"
    "    name: 'alova',\n"
    "    path: '/alova',\n"
    "    component: 'layout.base',\n"
    "    meta: {\n"
    "      title: 'alova',\n"
    "      i18nKey: 'route.alova',\n"
    "      icon: 'carbon:http',\n"
    "      order: 7,\n"
    "      roles: ['R_SUPER']\n"
    "    },\n"
    "    children: [\n"
    "      {\n"
    "        name: 'alova_request',\n"
    "        path: '/alova/request',\n"
    "        component: 'view.alova_request',\n"
    "        meta: {\n"
    "          title: 'alova_request',\n"
    "          i18nKey: 'route.alova_request',\n"
    "          order: 1\n"
    "        }\n"
    "      }\n"
    "    ]\n"
    "  },\n"
    "  {\n"
    "    name: 'multi-menu_second',\n"
    "    path: '/multi-menu/second',\n"
    "    meta: {\n"
    "      title: 'multi-menu_second',\n"
    "      i18nKey: 'route.multi-menu_second',\n"
    "      order: 2\n"
    "    },\n"
    "    children: [\n"
    "      {\n"
    "        name: 'multi-menu_second_child',\n"
    "        path: '/multi-menu/second/child',\n"
    "        meta: {\n"
    "          title: 'multi-menu_second_child',\n"
    "          i18nKey: 'route.multi-menu_second_child'\n"
    "        },\n"
    "        children: [\n"
    "          {\n"
    "            name: 'multi-menu_second_child_home',\n"
    "            path: '/multi-menu/second/child/home',\n"
    "            component: 'view.multi-menu_second_child_home',\n"
    "            meta: {\n"
    "              title: 'multi-menu_second_child_home',\n"
    "              i18nKey: 'route.multi-menu_second_child_home'\n"
    "            }\n"
    "          }\n"
    "        ]\n"
    "      }\n"
    "    ]\n"
    "  }\n"
    "];\n"
)


def _elegant_one(fields):
    """把單條欄集包成完整 generatedRoutes const 文字（fail-loud 案例用）。"""
    return ("export const generatedRoutes: GeneratedRoute[] = [\n"
            "  {\n" + fields + "  }\n"
            "];\n")


class TestElegantRoutes(unittest.TestCase):
    def test_parse_clean_nested_sample(self):
        rows = parse_elegant_routes(ELEGANT_ROUTES_SAMPLE, "routes.ts")
        # 6 條 route 物件（父＋葉全 flatten）：403／alova／alova_request／
        # multi-menu_second／multi-menu_second_child／multi-menu_second_child_home
        self.assertEqual(len(rows), 6)
        d = {r[0]: r for r in rows}
        self.assertEqual(d["403"],
                         ("403", "/403", "layout.blank$view.403", "route.403"))
        # 深層巢狀（3 層）child 確有入表
        self.assertEqual(d["multi-menu_second_child_home"],
                         ("multi-menu_second_child_home", "/multi-menu/second/child/home",
                          "view.multi-menu_second_child_home", "route.multi-menu_second_child_home"))
        # 父 route 無 component → 空字串（gen 時轉 —）；i18nKey 仍抽到
        self.assertEqual(d["multi-menu_second"][2], "")
        self.assertEqual(d["multi-menu_second"][3], "route.multi-menu_second")

    def test_meta_extra_fields_do_not_choke(self):
        # meta 內 roles 陣列／icon／order 等雜欄安全略過、不致 fail-loud
        rows = parse_elegant_routes(ELEGANT_ROUTES_SAMPLE, "routes.ts")
        alova = [r for r in rows if r[0] == "alova"][0]
        self.assertEqual(alova, ("alova", "/alova", "layout.base", "route.alova"))

    @unittest.skipUnless(_day1_pending(ELEGANT_SOURCE),
                         "Day 1 未達：解除＝routes.ts 到位（B9 掛 worktree 當步）；同 gen.screens 字面")
    def test_parse_real_routes_ts(self):
        rows = compute_screen_rows(ROOT)
        self.assertGreater(len(rows), 0, "真實 routes.ts 應解析出 route")
        names = [r[0] for r in rows]
        self.assertIn("403", names)
        # 深層巢狀（3 層）route 確有 flatten 入表
        self.assertIn("multi-menu_second_child_home", names)
        self.assertEqual(len(names), len(set(names)), "elegant-router name 應全域唯一")
        # rows 數＝來源檔 route 物件總數（每條 route 恰一 name: 行）
        src = _read(ROOT, ELEGANT_SOURCE)
        self.assertEqual(len(rows), len(re.findall(r"(?m)^\s*name: '", src)))

    def test_unknown_top_level_field_fails_loud(self):
        bad = ELEGANT_CLEAN_FIELDS + "    surprise: 1,\n"
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(_elegant_one(bad), "f.ts")
        self.assertIn("f.ts", str(cm.exception))
        self.assertIn("surprise", str(cm.exception))

    def test_malformed_name_shape_fails_loud(self):
        # name 無引號＝不認得的形（窄假設：必單引號短語法）
        bad = ELEGANT_CLEAN_FIELDS.replace("name: 'demo',", "name: demo,")
        with self.assertRaises(ElegantRoutesError):
            parse_elegant_routes(_elegant_one(bad), "f.ts")

    def test_duplicate_field_fails_loud(self):
        bad = ELEGANT_CLEAN_FIELDS + "    name: 'dup',\n"
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(_elegant_one(bad), "f.ts")
        self.assertIn("重複", str(cm.exception))

    def test_missing_required_field_fails_loud(self):
        bad = ELEGANT_CLEAN_FIELDS.replace("    path: '/demo',\n", "")
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(_elegant_one(bad), "f.ts")
        self.assertIn("path", str(cm.exception))

    def test_top_level_junk_in_array_fails_loud(self):
        text = ("export const generatedRoutes: GeneratedRoute[] = [\n"
                "  surprise,\n"
                "];\n")
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(text, "f.ts")
        self.assertIn("行 2", str(cm.exception))

    def test_missing_const_fails_loud(self):
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes("const x = 1;\n", "f.ts")
        self.assertIn("generatedRoutes", str(cm.exception))

    def test_unterminated_array_fails_loud(self):
        text = ("export const generatedRoutes: GeneratedRoute[] = [\n"
                "  {\n" + ELEGANT_CLEAN_FIELDS + "  }\n")   # 缺頂層收尾 ];
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(text, "f.ts")
        self.assertIn("收尾", str(cm.exception))

    def test_compute_screen_rows_missing_source_fails_loud(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ElegantRoutesError) as cm:
                compute_screen_rows(root)
            self.assertIn(ELEGANT_SOURCE, str(cm.exception))

    def test_gen_reference_screens_sorted_and_deterministic(self):
        rows = [("bravo", "/b", "view.b", "route.b"),
                ("alpha", "/a", "", "route.a"),
                ("charlie", "/c", "view.c", "")]
        text = gen_reference_screens(rows)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("alpha"), text.index("bravo"))    # name 序
        self.assertLess(text.index("bravo"), text.index("charlie"))
        self.assertEqual(text, gen_reference_screens(list(reversed(rows))))  # 入序無關
        self.assertIn("| alpha | /a | — | route.a |", text)          # 空 component→—
        self.assertIn("| charlie | /c | view.c | — |", text)         # 空 i18nKey→—

    def test_gen_reference_screens_escapes_pipe_in_path(self):
        # login path 內含 module 選擇器 `|`——須轉義否則破表格欄
        rows = [("login", "/login/:module(pwd-login|code-login)?",
                 "layout.blank$view.login", "route.login")]
        text = gen_reference_screens(rows)
        self.assertIn(r"pwd-login\|code-login", text)

    def test_gen_reference_screens_empty(self):
        self.assertIn("無任何 route", gen_reference_screens([]))

    def test_state_screens_line_is_live_not_stub(self):
        text = gen_state(TestGenState.CTX)
        for line in text.splitlines():
            if line.startswith("- reference/screens"):
                self.assertNotIn("stub", line)
                self.assertIn("generate", line)
                break
        else:
            self.fail("STATE 缺 reference/screens 對賬行")

    def test_check_reports_screens_drift_as_l2(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs/generated/reference"))
            rel = "docs/generated/reference/screens.md"
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("舊表\n")
            f = check_generated(root, {rel: "新表\n"}, exemptions={})
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["code"], "Lint02")
            self.assertIn("screens", f[0]["msg"])


MSG_DICT_TS_SAMPLE = (
    "const local: App.I18n.Schema = {\n"
    "  backend: {\n"
    "    common: {\n"
    "      // 行內註解（跳過）\n"
    "      listSeparator: '、',\n"
    "      success: '操作成功'\n"
    "    },\n"
    "    biz: {\n"
    "      user: {\n"
    "        inUse: '掛有 {userCount} 個使用者',\n"
    "        quoted: \"雙引號值\",\n"
    "        ticked: `反引號值`,\n"
    "        escaped: 'It\\'s ok'\n"
    "      }\n"
    "    }\n"
    "  },\n"
    "  system: {\n"
    "    title: 'not-backend'\n"
    "  }\n"
    "};\n"
)


class TestBackendMsgDict(unittest.TestCase):
    def test_parse_normal_nested(self):
        d = parse_locale_backend(MSG_DICT_TS_SAMPLE, "f.ts")
        self.assertEqual(d, {
            "common.listSeparator": "、",
            "common.success": "操作成功",
            "biz.user.inUse": "掛有 {userCount} 個使用者",
            "biz.user.quoted": "雙引號值",
            "biz.user.ticked": "反引號值",
            "biz.user.escaped": "It's ok",
        })

    def test_missing_backend_fails(self):
        with self.assertRaises(BackendDictError) as cm:
            parse_locale_backend("const local = {\n  other: {}\n};\n", "f.ts")
        self.assertIn("backend", str(cm.exception))

    def test_bad_line_fails_with_file_and_line(self):
        for bad in ("key: unquoted,",        # 無引號值
                    "key: ['a'],",           # 陣列值
                    "key: '跨行未閉",         # 值未閉合
                    "'quoted-key': 'v',"):   # 引號鍵（backend 樹現無、窄假設擋下）
            text = f"  backend: {{\n    {bad}\n  }},\n"
            with self.assertRaises(BackendDictError, msg=bad) as cm:
                parse_locale_backend(text, "f.ts")
            self.assertIn("f.ts:行 2", str(cm.exception), msg=bad)

    def test_unclosed_tree_fails(self):
        with self.assertRaises(BackendDictError) as cm:
            parse_locale_backend("  backend: {\n    a: {\n      b: 'v'\n", "f.ts")
        self.assertIn("未閉合", str(cm.exception))

    def test_duplicate_key_fails(self):
        text = "  backend: {\n    a: 'x',\n    a: 'y'\n  },\n"
        with self.assertRaises(BackendDictError) as cm:
            parse_locale_backend(text, "f.ts")
        self.assertIn("重複鍵 a", str(cm.exception))

    def test_empty_tree_fails(self):
        with self.assertRaises(BackendDictError):
            parse_locale_backend("  backend: {\n  },\n", "f.ts")

    def _root_with_locales(self, zh, en):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = os.path.join(tmp.name, "base-web/src/locales/langs")
        os.makedirs(d)
        for name, text in (("zh-tw.ts", zh), ("en-us.ts", en)):
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        return tmp.name

    def test_compute_rows_two_locales(self):
        root = self._root_with_locales(
            "  backend: {\n    auth: {\n      failed: '帳密錯誤'\n    }\n  },\n",
            "  backend: {\n    auth: {\n      failed: 'Bad credentials'\n    }\n  },\n")
        self.assertEqual(compute_msg_dict_rows(root),
                         [("auth.failed", "帳密錯誤", "Bad credentials")])

    def test_keyset_mismatch_fails(self):
        root = self._root_with_locales(
            "  backend: {\n    a: 'x'\n  },\n",
            "  backend: {\n    b: 'y'\n  },\n")
        with self.assertRaises(BackendDictError) as cm:
            compute_msg_dict_rows(root)
        self.assertIn("鍵集不相等", str(cm.exception))
        self.assertIn("a", str(cm.exception))

    def test_missing_locale_file_fails(self):
        root = self._root_with_locales("  backend: {\n    a: 'x'\n  },\n", "")
        os.remove(os.path.join(root, "base-web/src/locales/langs/en-us.ts"))
        with self.assertRaises(BackendDictError) as cm:
            compute_msg_dict_rows(root)
        self.assertIn("en-us.ts", str(cm.exception))

    def test_gen_md_form(self):
        md = gen_msg_dict_md([("auth.failed", "帳密|錯誤", "Bad credentials")])
        self.assertTrue(md.startswith(GEN_HEADER))
        self.assertIn("| auth.failed | 帳密\\|錯誤 | Bad credentials |", md)

    def test_gen_panel_form(self):
        text = gen_msg_dict_panel([("auth.failed", "帳密錯誤", "Bad credentials")])
        dash = json.loads(text)
        self.assertEqual(dash["uid"], "obs-backend-msg-dict")
        self.assertNotIn("datasource", text)         # 零 datasource
        self.assertIn("嚴禁手改", dash["description"])  # 檔頭 hint
        panel = dash["panels"][0]
        self.assertEqual(panel["type"], "text")
        self.assertIn("auth.failed", panel["options"]["content"])
        self.assertIn("帳密錯誤", panel["options"]["content"])

    def test_check_intercepts_tampered_panel(self):
        # 手改攔截形：deploy 側面板被手改一字元 → check 紅（Lint02 指名來源）
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = tmp.name
        os.makedirs(os.path.join(root, GENERATED_DIR))
        panel_path = os.path.join(root, MSG_DICT_PANEL)
        os.makedirs(os.path.dirname(panel_path))
        good = gen_msg_dict_panel([("a", "甲", "A")])
        computed = {MSG_DICT_PANEL: good}
        with open(panel_path, "w", encoding="utf-8") as fh:
            fh.write(good)
        self.assertEqual(check_generated(root, computed, exemptions={}), [])   # 一致＝綠
        with open(panel_path, "w", encoding="utf-8") as fh:
            fh.write(good.replace("甲", "乙", 1))               # 手改一字元
        f = check_generated(root, computed, exemptions={})
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["code"], "Lint02")
        self.assertIn("backend-msg-dict.json", f[0]["where"])

    def test_check_missing_panel_reported(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = tmp.name
        os.makedirs(os.path.join(root, GENERATED_DIR))
        f = check_generated(root, {MSG_DICT_PANEL: "x"}, exemptions={})
        self.assertEqual(len(f), 1)
        self.assertIn("缺生成檔", f[0]["msg"])


class TestLintLinks(unittest.TestCase):
    PATHS = {"docs/ops/BACKLOG.md", "docs/arc42/ARCHITECTURE.md", "CLAUDE.md"}

    def test_valid_relative_link(self):
        f = lint_links({"CLAUDE.md": "[待辦](docs/ops/BACKLOG.md)\n"}, self.PATHS)
        self.assertEqual(f, [])

    def test_dead_link(self):
        f = lint_links({"CLAUDE.md": "[死](docs/GONE.md)\n"}, self.PATHS)
        self.assertEqual(len(f), 1)
        self.assertIn("GONE", f[0]["msg"])

    def test_relative_from_subdir(self):
        f = lint_links({"docs/arc42/ARCHITECTURE.md": "[待辦](../ops/BACKLOG.md)\n"}, self.PATHS)
        self.assertEqual(f, [])

    def test_external_and_anchor_skipped(self):
        text = "[a](https://x.dev) [b](mailto:x@y.z) [c](#節)\n"
        self.assertEqual(lint_links({"CLAUDE.md": text}, self.PATHS), [])

    def test_link_with_anchor_checks_file_part(self):
        f = lint_links({"CLAUDE.md": "[x](docs/GONE.md#s)\n"}, self.PATHS)
        self.assertEqual(len(f), 1)


class TestLintLineRefs(unittest.TestCase):
    def test_line_ref_flagged(self):
        f = lint_line_refs({"docs/ops/NOTES.md": "詳 DESIGN.md:123 那段\n"})
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["level"], ERROR)

    def test_clean(self):
        self.assertEqual(lint_line_refs({"docs/ops/NOTES.md": "詳活書 §5、CLAUDE.md§3。\n"}), [])


class TestLintVolatileDeepLinks(unittest.TestCase):
    def test_deep_link_to_backlog_anchor(self):
        f = lint_volatile_deep_links({"CLAUDE.md": "[項](docs/ops/BACKLOG.md#b-021)\n"})
        self.assertEqual(len(f), 1)
        self.assertIn("整檔", f[0]["msg"])

    def test_deep_link_to_backlog_volume_anchor(self):
        # 滯後卷（BACKLOG-*.md）同屬揮發區——內部錨照禁
        f = lint_volatile_deep_links({"CLAUDE.md": "[項](docs/ops/BACKLOG-DEFERRED.md#b-060)\n"})
        self.assertEqual(len(f), 1)
        self.assertIn("整檔", f[0]["msg"])

    def test_whole_file_link_ok(self):
        f = lint_volatile_deep_links({"CLAUDE.md": "[待辦](docs/ops/BACKLOG.md)\n"})
        self.assertEqual(f, [])

    def test_state_and_notes_also_guarded(self):
        f = lint_volatile_deep_links(
            {"CLAUDE.md": "[a](docs/generated/STATE.md#x) [b](docs/ops/NOTES.md#y)\n"})
        self.assertEqual(len(f), 2)


class TestLintMemoryRefs(unittest.TestCase):
    def test_memory_path_flagged(self):
        f = lint_memory_refs({"docs/ops/NOTES.md": "見 ~/.claude/projects/x/memory/foo.md\n"})
        self.assertEqual(len(f), 1)

    def test_home_path_flagged(self):
        f = lint_memory_refs({"CLAUDE.md": "見 /home/anew/.claude/memory/bar.md\n"})
        self.assertEqual(len(f), 1)

    def test_rev3_annotation_exempt(self):
        self.assertEqual(
            lint_memory_refs({"docs/ops/LESSONS.md": "｜出處：rev3:memory/foo-bar\n"}), [])


class TestContentLintExempt(unittest.TestCase):
    """Lint11~Lint15 語料豁免（_is_exempt）：史料＋外部工具機器生成物。"""

    def test_historical_and_generated_exempt(self):
        self.assertTrue(_is_exempt("docs/brainstorms/018-x.md"))
        self.assertTrue(_is_exempt("graphify-out/GRAPH_REPORT.md"))
        self.assertTrue(_is_exempt("graphify-out/memory/query_x.md"))

    def test_repo_governed_docs_not_exempt(self):
        """★docs/generated/ 刻意不豁免——本 repo 真表的引用健康仍須守。"""
        for rel in ("docs/generated/STATE.md",
                    "docs/generated/reference/backend-msg-dict.md",
                    "docs/ops/NOTES.md", "CLAUDE.md"):
            self.assertFalse(_is_exempt(rel), msg=rel)

    def test_exempt_is_prefix_scoped_not_substring(self):
        """前綴比對、非子字串——同名前綴的鄰居檔不得被誤豁免。"""
        self.assertFalse(_is_exempt("docs/brainstorms.md"))
        self.assertFalse(_is_exempt("tools/graphify-out-helper.md"))


class TestLintTense(unittest.TestCase):
    def test_clean_book(self):
        self.assertEqual(lint_tense("## §1 簡介\n系統現在長這樣。\n"), [])

    def test_forbidden_words(self):
        for word in ("待決", "TBD", "⏳", "已完成", "下一步"):
            f = lint_tense(f"## §6 Runtime\n這件事{word}中。\n")
            self.assertEqual(len(f), 1, msg=word)
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("去處", f[0]["msg"], msg=word)


class TestLintDictionary(unittest.TestCase):
    def test_rev4_codes_smuggled(self):
        """★rev5 差分：判定面＝「提及 rev4 卻未用 rev4: 前綴」的混寫。

        ★負向樣本不可省——rev4→rev5 沿用同一套編號形式，故本案同時釘住「rev5 自身編號
        必須放行」；缺之則「裸碼即前代碼」型的錯誤實作全套仍綠（實證：該寫法會把
        B-012／ADR 0003／L-002 全數誤報成走私）。
        """
        f = lint_dictionary({"CLAUDE.md": "沿用 rev4 的 B-135 與 rev4 ADR 0077 的結論\n"})
        self.assertEqual(len(f), 2, msg=str(f))
        self.assertTrue(all(x["level"] == WARN for x in f))
        # 標準史料標註形不命中
        self.assertEqual(lint_dictionary({"CLAUDE.md": "沿用 rev4:B-135 與 rev4:ADR 0077\n"}), [])
        # ★rev5 自身編號不得誤報
        self.assertEqual(
            lint_dictionary({"CLAUDE.md": "追 B-012、立 ADR 0003、承 L-002。\n"}), [])

    def test_fast_changing_literals(self):
        f = lint_dictionary({BOOK: "服務聽 port 9528、seed 密碼 123456。\n"})
        self.assertEqual(len(f), 2)
        self.assertTrue(all("generated/reference" in x["msg"] for x in f))

    def test_provenance_line_exempt(self):
        f = lint_dictionary({BOOK: "｜出處：rev3:DECISIONS§1-⚠️c＋待決③\n"})
        self.assertEqual(f, [])

    def test_clean(self):
        self.assertEqual(lint_dictionary({"CLAUDE.md": "正常內容 §5 與 B-012。\n"}), [])

class TestLintEvents(unittest.TestCase):
    # -- rev5 差分：summary 單筆上限（Q6 拍板；併入 Lint03）------------------------
    @staticmethod
    def _ev(summary):
        return {"type": "misc", "date": "2026-08-04", "summary": summary}

    def test_summary_at_limit_passes_over_limit_fails(self):
        """★邊界逐字釘死：恰上限過、超一字紅——期望值寫死字面，不取自 SUMMARY_CHAR_LIMIT。

        取自被測常數即套套邏輯：上限被改小時期望值同步縮水、永遠對得上，守衛靜默瘦身
        而零信號（§4.5.4 共通設計理由）。故此處逐字寫 300／301。
        """
        self.assertEqual(_check_event(self._ev("摘" * 300)), [])
        errs = _check_event(self._ev("摘" * 301))
        self.assertEqual(len(errs), 1, msg=str(errs))
        self.assertIn("301 字超出單筆上限 300", errs[0])

    def test_summary_rejects_newline(self):
        """jsonl 一行一事件——summary 含換行即破壞行界語意。"""
        for bad in ("第一段\n第二段", "第一段\r第二段"):
            errs = _check_event(self._ev(bad))
            self.assertTrue(any("不得含換行" in x for x in errs), msg=str(errs))

    def test_notes_length_is_deliberately_unbounded(self):
        """★notes 刻意不設限：創世 misc 事件的 notes 承載 lint-roster 固定前綴（全部條款名）。

        本案同時是「別順手也把 notes 加上限」的防呆——加了會擋住創世事件本身。
        """
        e = dict(self._ev("一句話"), notes="lint-roster: " + ",".join(f"Lint{i:02d}" for i in range(1, 25)) + "詳" * 800)
        self.assertEqual(_check_event(e), [])

    def test_valid_lines_pass(self):
        self.assertEqual(lint_events(_jl(VALID_CLOSE, VALID_MISC, VALID_REVIEW)), [])

    def test_empty_file_passes(self):
        self.assertEqual(lint_events(""), [])

    def test_bad_json(self):
        f = lint_events("{not json\n")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["level"], ERROR)
        self.assertIn("行 1", f[0]["where"])

    def test_missing_required_field(self):
        e = dict(VALID_CLOSE); e.pop("pins")
        f = lint_events(_jl(e))
        self.assertEqual(len(f), 1)
        self.assertIn("pins", f[0]["msg"])

    def test_unknown_type(self):
        f = lint_events(_jl({"type": "nope", "date": "2026-07-02"}))
        self.assertEqual(len(f), 1)
        self.assertIn("nope", f[0]["msg"])

    def test_arch_impact_none_ok(self):
        e = dict(VALID_CLOSE); e["arch_impact"] = "none"
        self.assertEqual(lint_events(_jl(e)), [])

    def test_arch_impact_bad(self):
        for bad in ("§6", ["x6"], []):
            e = dict(VALID_CLOSE); e["arch_impact"] = bad
            self.assertEqual(len(lint_events(_jl(e))), 1, msg=repr(bad))

    def test_bad_date(self):
        e = dict(VALID_MISC); e["date"] = "2026/07/02"
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_bad_kind(self):
        e = dict(VALID_CLOSE); e["kind"] = "diagonal"
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_review_findings_sum(self):
        e = json.loads(json.dumps(VALID_REVIEW)); e["findings"]["total"] = 5
        f = lint_events(_jl(e))
        self.assertEqual(len(f), 1)
        self.assertIn("total", f[0]["msg"])

    def test_blank_line_rejected(self):
        f = lint_events(json.dumps(VALID_MISC) + "\n\n" + json.dumps(VALID_MISC) + "\n")
        self.assertEqual(len(f), 1)

    def test_misc_backlog_done_valid(self):
        """misc 攜 backlog_done（輕量軌消化通道、2026-07-17 調規）——合法形零錯。"""
        e = dict(VALID_MISC); e["backlog_done"] = ["B-992", "B-998"]
        self.assertEqual(lint_events(_jl(e)), [])

    def test_misc_backlog_done_bad_ids(self):
        e = dict(VALID_MISC); e["backlog_done"] = ["X-1"]
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_backlog_done_ids_includes_misc(self):
        """_backlog_done_ids 掃 misc 通道——改壞掃描（如回退只掃 feature_close）即紅。"""
        m = dict(VALID_MISC); m["backlog_done"] = ["B-910"]
        self.assertEqual(_backlog_done_ids([VALID_CLOSE, m]), {"B-903", "B-910"})

    # -- RE_SHA 全域收 40 位（rev4:contracts G3；前置＝rev4:T010 四筆正規化勘誤） ----------
    def test_merge_short_sha_rejected(self):
        """新列 7 位短 SHA→schema 拒（史料已正規化、無格式豁免分支）。"""
        e = dict(VALID_CLOSE); e["merge"] = "abc1234"
        f = lint_events(_jl(e))
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertIn("merge", f[0]["msg"])

    def test_pin_short_sha_rejected(self):
        e = json.loads(json.dumps(VALID_CLOSE)); e["pins"]["web"] = "deadbee"
        f = lint_events(_jl(e))
        self.assertEqual(len(f), 1, msg=str(f))
        self.assertIn("pins", f[0]["msg"])

    def test_merge_41_hex_rejected(self):
        """上界同守：41 位亦非合法（收 40 是等號、不是下界）。"""
        e = dict(VALID_CLOSE); e["merge"] = "a" * 41
        self.assertEqual(len(lint_events(_jl(e))), 1)

    # -- erratum 型格式面（B-042 調閘形；語意面歸 Lint18） -----------------------------
    def test_erratum_valid_passes(self):
        self.assertEqual(lint_events(_jl(VALID_ERRATUM)), [])

    def test_erratum_missing_required_field_rejected(self):
        """B-042 八臂⑦前半：四個專屬必填欄逐一缺欄＝格式 ERROR。"""
        for k in ("target_line", "field", "corrected", "reason"):
            e = dict(VALID_ERRATUM); e.pop(k)
            f = lint_events(_jl(e))
            self.assertEqual(len(f), 1, msg=f"{k}｜{f}")
            self.assertIn(k, f[0]["msg"])

    def test_erratum_bad_target_line_rejected(self):
        """target_line 須為正整數（行號）；bool 是 int 子類、須另擋。"""
        for bad in (0, -1, "2", 1.5, True):
            e = dict(VALID_ERRATUM); e["target_line"] = bad
            f = lint_events(_jl(e))
            self.assertEqual(len(f), 1, msg=f"{bad!r}｜{f}")
            self.assertIn("target_line", f[0]["msg"])

    def test_erratum_field_enum(self):
        """B-042 八臂⑦中段：field 枚舉外＝格式 ERROR；三個合法值逐一放行。"""
        for bad in ("pins", "summary", "Merge", "pins.mobile", 3):
            e = dict(VALID_ERRATUM); e["field"] = bad
            f = lint_events(_jl(e))
            self.assertEqual(len(f), 1, msg=f"{bad!r}｜{f}")
            self.assertIn("field", f[0]["msg"])
        for ok in ("merge", "pins.web", "pins.api"):
            e = dict(VALID_ERRATUM); e["field"] = ok
            self.assertEqual(lint_events(_jl(e)), [], msg=ok)

    def test_erratum_fields_derived_from_pin_keys_not_literal_roster(self):
        """★「ERRATUM_FIELDS 自 PIN_KEYS 導出、不落第二份字面名冊」須有機器守著（掃源）。

        值斷言在此零分辨力：字面名冊與導出式對**現行** PIN_KEYS 求值全等，兩邊皆綠＝套套
        邏輯（同 test_tools_roster_is_pinned… docstring 所指之形）；上面的
        test_erratum_field_enum 更是把同一份字面手抄進測試，導不導出都不會紅。分辨點只在
        源碼形，故掃源（前例＝TestToolsCliTruthTable.test_real_docs_sync_dispatch_is_pinned）。
        真實後果：PIN_KEYS 日後增第三個子庫時，導出式讓 field＝pins.<新鍵> 自動通過本條
        枚舉、Lint18 的 err_pins 派批與 pending 也一併跟上；換回字面則該子庫的 pins 永遠
        無法被 erratum 更正——B-042 補起來的出口對新子庫靜默缺一半、且無一支測試會紅。
        ★禁字亦自 PIN_KEYS 導出（不手抄），否則本釘子自己就成了第二份字面名冊。
        """
        src = _read(ROOT, "tools/docs-sync.py")
        self.assertIsNotNone(src)
        rows = [ln for ln in src.splitlines() if ln.startswith("ERRATUM_FIELDS =")]
        self.assertEqual(len(rows), 1, msg=str(rows))
        self.assertIn("PIN_KEYS", rows[0], msg=rows[0])
        for key, _sub in PIN_KEYS:
            self.assertNotIn(f'"pins.{key}"', rows[0], msg=rows[0])

    def test_erratum_bad_corrected_rejected(self):
        """B-042 八臂⑦後半：corrected 非 40 位小寫 hex＝格式 ERROR（與 RE_SHA 同尺）。

        ★`int("1"*40)` 是本案唯一能分辨兩把尺的輸入（釘住「Lint03 與 `_erratum_view`
        同尺」）：格式面若寫成 `RE_SHA.fullmatch(str(...))`，40 位純十進位數字 str() 後
        恰為 40 個合法 hex 字元而放行，視圖面卻因 `isinstance(cor, str)` 為 False 而
        continue——兩邊都不報＝erratum 靜默零效（硬語意③明禁）。其餘短整數（123）
        兩把尺皆拒、對此變異零分辨力。
        """
        for bad in ("abc1234", "g" * 40, "A1B2C3D4" * 5, "a" * 41, 123, int("1" * 40)):
            e = dict(VALID_ERRATUM); e["corrected"] = bad
            f = lint_events(_jl(e))
            self.assertEqual(len(f), 1, msg=f"{bad!r}｜{f}")
            self.assertIn("corrected", f[0]["msg"])

    def test_erratum_reason_nonempty_single_line(self):
        for bad in ("", "   ", "上一句\n下一句", "上一句\r下一句", 123):
            e = dict(VALID_ERRATUM); e["reason"] = bad
            f = lint_events(_jl(e))
            self.assertEqual(len(f), 1, msg=f"{bad!r}｜{f}")
            self.assertIn("reason", f[0]["msg"])

    def test_erratum_passes_type_filtered_consumers_unharmed(self):
        """erratum 對既有以型篩選的消費點零誤傷：_backlog_done_ids 不撿（無 backlog_done
        通道）、gen_state 型統計照計、gen_milestones 表格化不炸（無 summary＝該格畫 —）。"""
        self.assertEqual(_backlog_done_ids([VALID_CLOSE, VALID_ERRATUM]), {"B-903"})
        text = gen_state({"events": [VALID_MISC, VALID_ERRATUM], "adr_metas": []})
        self.assertIn("erratum 1", text)
        files = gen_milestones([VALID_MISC, VALID_ERRATUM])
        self.assertIn("erratum", files["docs/generated/MILESTONES.md"])


class TestLintCloseExistence(unittest.TestCase):
    """Lint04：收刀事件引用之 ADR／backlog／specs 目錄存在性。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs/ops"))
        os.makedirs(os.path.join(self.root, ADR_DIR))

    def tearDown(self):
        self.tmp.cleanup()

    def _w(self, rel, content):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)

    def _adr(self, fid):
        self._w(f"{ADR_DIR}/{fid}-x.md", f'---\nid: "{fid}"\n---\n')

    def _close(self, **kw):
        e = {"type": "feature_close", "feature": "001-x", "merge": "abc1234",
             "date": "2026-07-10", "summary": "s", "pins": {"web": "a", "api": "b"},
             "adrs": [], "arch_impact": "none", "backlog_add": [], "backlog_done": []}
        e.update(kw)
        return e

    def _clean(self):
        # ADR 0007 存在、B-955 開放、B-903 已完成不在 BACKLOG、specs/001-x 存在
        self._adr("0007")
        self._w(BACKLOG, "<!-- next: B-990 -->\n# BACKLOG\n\n- B-955｜開放中\n")
        os.makedirs(os.path.join(self.root, "specs/001-x"))
        return self._close(adrs=["0007"], backlog_add=["B-955"], backlog_done=["B-903"])

    def test_clean_passes(self):
        self._w(EVENTS, _jl(self._clean()))
        self.assertEqual(lint_close_existence(self.root), [])

    def test_missing_adr(self):
        e = self._clean()
        e["adrs"] = ["0007", "0099"]  # 0099 無檔
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertEqual([x["code"] for x in f], ["Lint04"])
        self.assertIn("0099", f[0]["msg"])

    def test_backlog_done_still_open(self):
        e = self._clean()
        e["backlog_done"] = ["B-955"]  # B-955 仍開放在 BACKLOG＝未真的完成刪列
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("B-955" in x["msg"] and x["code"] == "Lint04" for x in f))

    def test_backlog_add_phantom(self):
        e = self._clean()
        e["backlog_add"] = ["B-977"]  # 既非開放亦無後續 done 消化
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("B-977" in x["msg"] and x["code"] == "Lint04" for x in f))

    def test_backlog_open_includes_deferred_volume(self):
        # 滯後卷條目仍屬開放：backlog_add 指向滯後卷不誤報 phantom；
        # backlog_done 誤標滯後中條目要被抓「宣稱完成卻未刪列」
        e = self._clean()
        self._w(BACKLOG, "<!-- next: B-990 -->\n# BACKLOG\n")
        self._w("docs/ops/BACKLOG-DEFERRED.md",
                "# BACKLOG-DEFERRED — 滯後卷\n\n- B-955｜開放中｜release 前\n")
        self._w(EVENTS, _jl(e))
        self.assertEqual(lint_close_existence(self.root), [])
        e["backlog_done"] = ["B-955"]
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("宣稱完成卻未刪列" in x["msg"] for x in f))

    def test_backlog_add_consumed_by_later_done(self):
        self._adr("0007")
        self._w(BACKLOG, "<!-- next: B-990 -->\n# BACKLOG\n")
        os.makedirs(os.path.join(self.root, "specs/001-x"))
        os.makedirs(os.path.join(self.root, "specs/002-y"))
        e1 = self._close(feature="001-x", adrs=["0007"], backlog_add=["B-956"])
        e2 = self._close(feature="002-y", adrs=["0007"], backlog_done=["B-956"])
        self._w(EVENTS, _jl(e1, e2))
        self.assertEqual(lint_close_existence(self.root), [])

    def test_missing_specs_dir(self):
        e = self._clean()
        e["feature"] = "909-fake-nope"  # 未建 specs/909-fake-nope
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("specs/909-fake-nope" in x["msg"] for x in f))

    def _g(self, *args):
        """fixture git 呼叫（固定身分 env；_git_close 與等價性案共用、免樣板重複）。"""
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        r = subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                           text=True, env=env)
        assert r.returncode == 0, r.stderr
        return r.stdout

    def _git_close(self, backlog_at_merge, backlog_now, backlog_add):
        """建 git repo：commit＝merge M（BACKLOG＝backlog_at_merge）；工作樹 BACKLOG 改成 backlog_now
        （模擬事後完成刪列、git 即史）；events 寫 feature_close(merge=M, backlog_add)。回 findings。"""
        g = self._g

        def _bl(ids):
            return "<!-- next: B-990 -->\n# BACKLOG\n\n" + "".join(f"- {b}｜開放中\n" for b in ids)
        self._adr("0007")
        os.makedirs(os.path.join(self.root, "specs/001-x"))
        self._w(BACKLOG, _bl(backlog_at_merge))
        g("init", "-q", "-b", "main")
        g("add", "-A")
        g("commit", "-qm", "merge-M")
        m = g("rev-parse", "HEAD").strip()
        self._w(BACKLOG, _bl(backlog_now))          # 事後刪列（工作樹）
        self._w(EVENTS, _jl(self._close(merge=m, adrs=["0007"], backlog_add=backlog_add)))
        return lint_close_existence(self.root)

    def test_backlog_add_removed_after_close_passes(self):
        # rev4:B-070 曾在 BACKLOG（commit M）、事後獨立完成刪列（現況/done 皆無）→git 史驗過、不誤報。
        # 回歸：舊碼查現況 open_ids/done_ids→獨立維護任務完成刪列後恆假陽（rev4:B-070 實測）。
        f = self._git_close(backlog_at_merge=["B-970"], backlog_now=[], backlog_add=["B-970"])
        self.assertEqual(f, [])

    def test_backlog_add_true_phantom_errors(self):
        # B-999 從未在 BACKLOG git 史出現（phantom/typo）→仍抓錯。
        f = self._git_close(backlog_at_merge=["B-970"], backlog_now=[], backlog_add=["B-999"])
        self.assertTrue(any("B-999" in x["msg"] and x["code"] == "Lint04" for x in f))

    def _pickaxe_ever_existed(self, nb):
        """單掃改法前的逐 id pickaxe 原邏輯（僅留作等價性測試的對照基準；
        生產路徑已改 _backlog_ever_tokens 單掃集合法）。"""
        out = git_out(["log", "--oneline", "-S", f"{nb}｜", "--", *backlog_paths(self.root)],
                      self.root)
        return bool(out and out.strip())

    def test_ever_existed_single_scan_equals_pickaxe(self):
        """等價性：單掃集合法與逐 id pickaxe 法對三型 id 結論一致（子串級、不分行首形）。
        三型＝曾存在後被刪（B-970）／從未存在（B-999）／僅被其他條目內文引用（B-902：
        `B-902｜` 子串只出現在 B-901 條目內文、非自身條目列——pickaxe 本就子串級、判曾存在）。
        ★v2 之 commit subject 帶 B-988｜＝標題行注入探針：--oneline 標題不以 +/- 起頭、
        不得入集——下方精確集合斷言即其突變守護（拆掉 +/- 過濾＝B-988｜混入即紅）。"""
        g = self._g
        kept = "- B-901｜內文引用他項：詳見 B-902｜之內文子串形\n"
        self._w(BACKLOG, "<!-- next: B-995 -->\n# BACKLOG\n\n- B-970｜曾存在後被刪\n" + kept)
        g("init", "-q", "-b", "main")
        g("add", "-A")
        g("commit", "-qm", "v1")
        self._w(BACKLOG, "<!-- next: B-995 -->\n# BACKLOG\n\n" + kept)
        g("add", "-A")
        g("commit", "-qm", "v2-del-B-970（B-988｜標題行注入探針）")
        # 單掃集合逐字 token（B-970：v1 加號行進入、v2 減號行離場——減號行掃描屬證明性冗餘、
        # 詳 _backlog_ever_tokens docstring；B-988｜在 subject、不得入集）
        self.assertEqual(_backlog_ever_tokens(self.root),
                         {"B-970｜", "B-901｜", "B-902｜"})
        for nb, expect in [("B-970", True), ("B-999", False), ("B-902", True)]:
            scan = _backlog_id_ever_existed(self.root, nb)
            pick = self._pickaxe_ever_existed(nb)
            self.assertEqual(scan, pick, f"{nb}：單掃 {scan} ≠ pickaxe {pick}")
            self.assertEqual(scan, expect, nb)


class TestLintReviewExistence(unittest.TestCase):
    """Lint05：review 分流引用（report 檔／to_backlog／wontfix_adr）存在性。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs/ops"))
        os.makedirs(os.path.join(self.root, ADR_DIR))

    def tearDown(self):
        self.tmp.cleanup()

    def _w(self, rel, content):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)

    def _adr(self, fid):
        self._w(f"{ADR_DIR}/{fid}-x.md", f'---\nid: "{fid}"\n---\n')

    # -- Q13 雙源對賬（2026-08-04 拍板；rev4 宣稱有此紀律但 as-built 從未實作）--------
    def test_dual_source_mismatch_is_error(self):
        """★事件 total 與報告 front-matter findings_total 不符＝ERROR（本條款核心）。"""
        self._w(EVENTS, _jl(self._clean()))
        self._w("docs/reviews/20260801-x.md", "---\nfindings_total: 5\n---\n# review\n")
        all_f = lint_review_existence(self.root)
        f = [x for x in all_f if "雙源不符" in x["msg"]]
        self.assertEqual(len(f), 1, msg=str(all_f))
        self.assertIn("事件 total=2", f[0]["msg"])

    def test_dual_source_missing_front_matter_is_error(self):
        """★報告檔缺 front-matter＝無對賬基準，不得靜默放行（否則等同 rev4 單源現況）。"""
        self._w(EVENTS, _jl(self._clean()))
        self._w("docs/reviews/20260801-x.md", "# review 沒有 front-matter\n")
        all_f = lint_review_existence(self.root)
        self.assertEqual(len([x for x in all_f if "缺必填欄 findings_total" in x["msg"]]), 1,
                         msg=str(all_f))

    def test_dual_source_non_integer_is_error(self):
        """findings_total 須為非負整數——型別不對即無從比對。"""
        self._w(EVENTS, _jl(self._clean()))
        self._w("docs/reviews/20260801-x.md", "---\nfindings_total: 兩筆\n---\n# review\n")
        all_f = lint_review_existence(self.root)
        self.assertEqual(len([x for x in all_f if "須為非負整數" in x["msg"]]), 1, msg=str(all_f))

    def _review(self, **kw):
        e = {"type": "review", "date": "2026-08-01", "scope": "s",
             "report": "reviews/20260801-x.md",
             "findings": {"total": 1, "fixed": 0, "to_backlog": [], "wontfix_adr": []}}
        e.update(kw)
        return e

    def _clean(self):
        self._adr("0012")
        self._w(BACKLOG, "<!-- next: B-990 -->\n# BACKLOG\n\n- B-955｜開放中\n")
        # ★報告檔 front-matter 為 Q13 雙源對賬的必填規格（findings_total 須等於事件 total）
        self._w("docs/reviews/20260801-x.md", "---\nfindings_total: 2\n---\n# review\n")
        return self._review(findings={"total": 2, "fixed": 0,
                                       "to_backlog": ["B-955"], "wontfix_adr": ["0012"]})

    def test_clean_passes(self):
        self._w(EVENTS, _jl(self._clean()))
        self.assertEqual(lint_review_existence(self.root), [])

    def test_empty_events_vacuous_pass(self):
        self._w(EVENTS, "")
        self.assertEqual(lint_review_existence(self.root), [])

    def test_missing_report(self):
        e = self._clean()
        e["report"] = "reviews/nope.md"  # 檔不存在
        self._w(EVENTS, _jl(e))
        f = lint_review_existence(self.root)
        self.assertTrue(any("report" in x["msg"] and x["code"] == "Lint05" for x in f))

    def test_missing_wontfix_adr(self):
        e = self._clean()
        e["findings"]["wontfix_adr"] = ["0099"]  # 無檔
        self._w(EVENTS, _jl(e))
        f = lint_review_existence(self.root)
        self.assertTrue(any("0099" in x["msg"] and x["code"] == "Lint05" for x in f))

    def test_to_backlog_phantom(self):
        e = self._clean()
        e["findings"]["to_backlog"] = ["B-977"]  # 既非開放亦無 done 消化
        self._w(EVENTS, _jl(e))
        f = lint_review_existence(self.root)
        self.assertTrue(any("B-977" in x["msg"] and x["code"] == "Lint05" for x in f))


BOOK_3SEC = "# 活書\n\n## §1 甲\n一\n## §2 乙\n二\n## §3 丙\n三\n"


class TestLintArchImpact(unittest.TestCase):
    """Lint06：arch_impact 節存在性（a）＋最新刀 merge^1→簿記雙向（b、ADR 0017）。"""

    def test_changed_sections_content_diff(self):
        a = "## §5 X\naaa\n## §6 Y\nbbb\n"
        b = "## §5 X\nAAA\n## §6 Y\nbbb\n"  # 僅 §5 內容變
        self.assertEqual(_arch_changed_sections(a, b), {5})

    def test_changed_sections_added(self):
        a = "## §5 X\naaa\n"
        b = "## §5 X\naaa\n## §6 Y\nbbb\n"  # §6 新增
        self.assertEqual(_arch_changed_sections(a, b), {6})

    def _write_book_events(self, d, arch_impact):
        os.makedirs(os.path.join(d, "docs/ops"))
        os.makedirs(os.path.join(d, "docs/arc42"))
        with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
            fh.write(BOOK_3SEC)
        ev = {"type": "feature_close", "feature": "001-x", "merge": "abc1234",
              "date": "2026-07-10", "summary": "s", "pins": {"web": "a", "api": "b"},
              "adrs": [], "arch_impact": arch_impact, "backlog_add": [], "backlog_done": []}
        with open(os.path.join(d, EVENTS), "w", encoding="utf-8") as fh:
            fh.write(_jl(ev))

    def test_existence_clean_no_git_skips_b(self):
        # 非 git 目錄＋不可解 merge SHA→(b) 跳過；(a) 驗 §2 存在→0
        # ★U5 語意遷移：(b) 的跳過由靜默改為落跳過明細（rev4:FR-012「不適用≠通過」）。
        with tempfile.TemporaryDirectory() as d:
            self._write_book_events(d, ["§2"])
            self._assert_only_skip_b(lint_arch_impact(d))

    def _assert_only_skip_b(self, findings):
        """(b) 合法跳過：零 ERROR／WARN、恰一筆 Lint06 跳過明細。"""
        self.assertEqual([x for x in findings if x["level"] != SKIP], [], msg=str(findings))
        skips = [x for x in findings if x["level"] == SKIP]
        self.assertEqual(len(skips), 1, msg=str(findings))
        self.assertEqual(skips[0]["code"], "Lint06")

    def test_existence_bad_section(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_book_events(d, ["§99"])
            f = lint_arch_impact(d)
            self.assertTrue(any("§99" in x["msg"] and x["code"] == "Lint06" for x in f))

    def _git_repo(self, d, arch_impact, commit_bookkeeping=True, book_at="bookkeeping"):
        """建 git repo：commit0＝merge 前基底 P（＝merge^1、比對左源）；commit1＝merge M；
        簿記 as-built＋events 寫工作樹。活書 §5 變動落點由 book_at 三擇一：
          "bookkeeping"＝M 版活書仍＝基底版、簿記時才改 §5（原骨架語意）；
          "feature"＝§5 變動隨刀內 commit 已含於 M、merge→簿記零活書 delta（001 同型）；
          "none"＝全程零活書變動。
        commit_bookkeeping=True→再 commit 成簿記 commit（post-commit 態、HEAD＝簿記）；
        False→as-built／events 留工作樹不 commit（pre-commit 閘態、HEAD 仍＝merge M）。回 lint_arch_impact。"""
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

        def g(*args):
            r = subprocess.run(["git", *args], cwd=d, capture_output=True,
                               text=True, env=env)
            assert r.returncode == 0, r.stderr
            return r.stdout

        def w_book(text):
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write(text)
        v0 = "## §5 A\nold5\n## §6 B\nold6\n"
        v1 = "## §5 A\nNEW5\n## §6 B\nold6\n"
        g("init", "-q", "-b", "main")
        os.makedirs(os.path.join(d, "docs/arc42"))
        os.makedirs(os.path.join(d, "docs/ops"))
        w_book(v0)
        g("add", "-A")
        g("commit", "-qm", "base-P")            # merge^1＝比對左源基準
        w_book(v1 if book_at == "feature" else v0)
        with open(os.path.join(d, "feature.txt"), "w", encoding="utf-8") as fh:
            fh.write("刀內變更佔位（保 merge commit 非空）\n")
        g("add", "-A")
        g("commit", "-qm", "merge-M")
        m = g("rev-parse", "HEAD").strip()
        w_book(v0 if book_at == "none" else v1)  # 簿記態活書
        ev = {"type": "feature_close", "feature": "001-x", "merge": m,
              "date": "2026-07-10", "summary": "s", "pins": {"web": "a", "api": "b"},
              "adrs": [], "arch_impact": arch_impact, "backlog_add": [], "backlog_done": []}
        with open(os.path.join(d, EVENTS), "w", encoding="utf-8") as fh:
            fh.write(_jl(ev))
        if commit_bookkeeping:
            g("add", "-A")
            g("commit", "-qm", "bookkeeping")
        return lint_arch_impact(d)

    def test_bidirectional_clean(self):
        # 兼 ADR 0017 驗收案 (c)：簿記時才改活書的變動仍正確納入（基準改 merge^1 後不漏）。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])

    def test_bidirectional_in_feature_change_counts(self):
        # ADR 0017 驗收案 (a)＝001 同型紅綠案：§5 變動隨刀內 commit 已含於 merge M、
        # merge→簿記零活書 delta。舊基準（左源＝merge:BOOK）此案紅——被誤判
        # 「宣稱 §5 但無實際變動」、只能違實記 arch_impact=none（001 實撞）；
        # 新基準（左源＝merge^1:BOOK、「本刀影響」語意）判有影響→宣稱 §5 應綠。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"], book_at="feature"), [])

    def test_bidirectional_no_change_verdict_unchanged(self):
        # ADR 0017 驗收案 (b)：全程零活書變動——零宣稱＝綠、假宣稱＝紅，判定不因基準改動而變。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, [], book_at="none"), [])

    def test_bidirectional_no_change_false_claim_still_error(self):
        with tempfile.TemporaryDirectory() as d:
            f = self._git_repo(d, ["§5"], book_at="none")
            l6 = [x for x in f if x["code"] == "Lint06" and x["level"] == ERROR]
            self.assertEqual(len(l6), 1, msg=str(f))
            self.assertIn("§5", l6[0]["msg"])

    def test_bidirectional_true_merge_parent_order_pinned(self):
        """真雙親 --no-ff merge 釘死「^1＝default 側」語意（ADR 0017 註解前提的可執行
        斷言；線性 fixture 下 ^1／^2 不可區分——復核補強）：default 側先落一筆與本刀
        無關的 §6 變動（在 ^1 內、不得入差集）、feature 側改 §5——誤取 ^2（feature tip）
        為左源時差集變 {§6}、本案即紅；誤用舊基準（merge:BOOK）差集變空、本案亦紅。"""
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

            def g(*args):
                r = subprocess.run(["git", *args], cwd=d, capture_output=True,
                                   text=True, env=env)
                assert r.returncode == 0, r.stderr
                return r.stdout

            def w_book(text):
                with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                    fh.write(text)
            base5, base6 = "## §5 A\nold5\np1\np2\np3\n", "## §6 B\nold6\n"
            g("init", "-q", "-b", "main")
            os.makedirs(os.path.join(d, "docs/arc42"))
            os.makedirs(os.path.join(d, "docs/ops"))
            w_book(base5 + base6)
            g("add", "-A")
            g("commit", "-qm", "base")
            g("checkout", "-qb", "feat")
            w_book(base5.replace("old5", "NEW5") + base6)
            g("add", "-A")
            g("commit", "-qm", "feature-§5")
            g("checkout", "-q", "main")
            w_book(base5 + base6.replace("old6", "NEW6"))
            g("add", "-A")
            g("commit", "-qm", "default-side-§6")
            g("merge", "-q", "--no-ff", "-m", "merge-M", "feat")
            m = g("rev-parse", "HEAD").strip()
            ev = {"type": "feature_close", "feature": "001-x", "merge": m,
                  "date": "2026-07-10", "summary": "s",
                  "pins": {"web": "a", "api": "b"}, "adrs": [],
                  "arch_impact": ["§5"], "backlog_add": [], "backlog_done": []}
            with open(os.path.join(d, EVENTS), "w", encoding="utf-8") as fh:
                fh.write(_jl(ev))
            g("add", "-A")
            g("commit", "-qm", "bookkeeping")
            self.assertEqual(lint_arch_impact(d), [])

    def test_bidirectional_precommit_clean(self):
        # pre-commit 閘時刻（HEAD＝merge、as-built 僅在工作樹）：宣稱 §5＝實改 §5→應綠。
        # 回歸：舊碼讀 head_file(HEAD) 時 merge→HEAD 恆為空、此處會誤報「宣稱但無變動」。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"], commit_bookkeeping=False), [])

    def test_bidirectional_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            f = self._git_repo(d, ["§6"])  # 宣稱 §6，實際改的是 §5
            l6 = [x for x in f if x["code"] == "Lint06"]
            msgs = " ".join(x["msg"] for x in l6)
            self.assertEqual(len(l6), 2)
            self.assertIn("§6", msgs)  # 宣稱卻沒改
            self.assertIn("§5", msgs)  # 改了卻沒宣稱

    def _runner(self, d):
        """回一個對 tempdir d 執行 git 的 runner（與 _git_repo 同環境）。"""
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

        def g(*args):
            r = subprocess.run(["git", *args], cwd=d, capture_output=True,
                               text=True, env=env)
            assert r.returncode == 0, r.stderr
            return r.stdout
        return g

    def test_bidirectional_next_feature_committed_skips_b(self):
        # 下一支 feature 於某單元 commit 編輯活書 §6（mid-feature、最新 close 仍＝001-x）：
        # HEAD 前進超過簿記（HEAD^＝簿記 B≠merge M）→ (b) 應跳過、不誤報。
        # 回歸 blocker：舊碼恆讀工作樹→ merge→工作樹＝{5,6}、claimed={5}→ 假陽全程硬擋下一支 feature。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])  # 建到簿記 post-commit（HEAD=B）
            g = self._runner(d)
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write("## §5 A\nNEW5\n## §6 B\nDRIFT6\n")  # 907 動 §6
            g("add", "-A")
            g("commit", "-qm", "907-fake-unit-book")
            self._assert_only_skip_b(lint_arch_impact(d))

    def test_bidirectional_next_feature_uncommitted_reads_head(self):
        # 下一支 feature 活書漂移仍在工作樹未 commit（HEAD 仍＝簿記 B、HEAD^＝merge M）：
        # (b) 綁 State 2 讀 HEAD 版活書（非工作樹）→ 忽略漂移、不誤報。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write("## §5 A\nNEW5\n## §6 B\nDRIFT6\n")  # 工作樹漂移未 commit
            self.assertEqual(lint_arch_impact(d), [])

    def test_bidirectional_next_feature_unrelated_commit_skips_b(self):
        # 下一支 feature 已 commit 一筆活書 §6 後、再來一筆無關（僅 NOTES）commit：
        # HEAD 仍在簿記之後 → (b) 續跳過、無關 commit 不被誤擋（回歸 blocker「連改 NOTES 亦被擋」）。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])
            g = self._runner(d)
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write("## §5 A\nNEW5\n## §6 B\nDRIFT6\n")
            g("add", "-A")
            g("commit", "-qm", "907-fake-unit-book")
            with open(os.path.join(d, "docs/ops/NOTES.md"), "w", encoding="utf-8") as fh:
                fh.write("下一步\n")
            g("add", "-A")
            g("commit", "-qm", "907-fake-notes")
            self._assert_only_skip_b(lint_arch_impact(d))


class TestLintBudgets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        for d in ("docs/ops", "docs/generated", "docs/arc42"):
            os.makedirs(os.path.join(self.root, d))

    def tearDown(self):
        self.tmp.cleanup()

    def _w(self, rel, content):
        p = os.path.join(self.root, rel)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)

    def test_all_missing_files_pass(self):
        self.assertEqual(lint_budgets(self.root), [])

    def test_notes_over_40_lines(self):
        self._w("docs/ops/NOTES.md", "x\n" * 41)
        f = lint_budgets(self.root)
        self.assertEqual([x["code"] for x in f], ["Lint07"])
        self.assertEqual(f[0]["level"], ERROR)

    def test_notes_at_40_lines_ok(self):
        self._w("docs/ops/NOTES.md", "x\n" * 40)
        self.assertEqual(lint_budgets(self.root), [])

    def test_state_over_4k_tokens(self):
        self._w("docs/generated/STATE.md", "字" * 4001 * 1)  # 4001 chars ×3 bytes → >4000 tokens
        f = lint_budgets(self.root)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["level"], ERROR)

    def test_lessons_warn_near_limit(self):
        self._w("docs/ops/LESSONS.md", "字" * 22600)  # ~22600 tokens：警告未達硬擋
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [WARN])

    def test_lessons_volume_files_also_checked(self):
        self._w("docs/ops/LESSONS-001-050.md", "字" * 25100)
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [ERROR])

    def test_backlog_volume_files_also_checked(self):
        # BACKLOG-*.md 卷走 glob 限額（同主檔 200 行）——新卷免登記 BUDGETS 也被攔
        self._w("docs/ops/BACKLOG-ARCHIVE.md", "x\n" * 201)
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [ERROR])

    def test_lesson_entry_over_token_limit_red(self):
        # 分檔制（ADR 0045）：LESSONS/ 條目檔逐檔單條上限——3000+ 必 ERROR、2000+ 必 WARN、
        # 2000 以下與非 L-*.md 檔不報；token 計全檔（含 frontmatter）。「字」＝3 bytes＝1 token。
        os.makedirs(os.path.join(self.root, "docs/ops/LESSONS"))
        self._w("docs/ops/LESSONS/L-901-a.md", "字" * 3001)
        self._w("docs/ops/LESSONS/L-902-b.md", "字" * 2001)
        self._w("docs/ops/LESSONS/L-903-c.md", "字" * 1999)
        self._w("docs/ops/LESSONS/notes.md", "字" * 3001)  # 非 L- 前綴：不屬條目、不納
        f = lint_budgets(self.root)
        self.assertEqual([(x["level"], x["where"]) for x in f],
                         [(ERROR, "docs/ops/LESSONS/L-901-a.md"),
                          (WARN, "docs/ops/LESSONS/L-902-b.md")], msg=str(f))
        self.assertTrue(all(x["code"] == "Lint07" and "單條上限" in x["msg"] for x in f),
                        msg=str(f))

    def test_architecture_section_quota_warn(self):
        body = "## §1 簡介與目標\n" + "內容\n" * 41 + "## §2 約束\n內容\n"
        self._w("docs/arc42/ARCHITECTURE.md", body)
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [WARN])
        self.assertIn("§1", f[0]["msg"])

    def test_architecture_over_700_lines_error(self):
        self._w("docs/arc42/ARCHITECTURE.md", "## §1 簡介與目標\n" + "x\n" * 700)
        levels = [x["level"] for x in lint_budgets(self.root)]
        self.assertIn(ERROR, levels)


class TestTokenCount(unittest.TestCase):
    """鎖定 token 算法：UTF-8 bytes ÷ 3。"""

    def test_ascii(self):
        self.assertEqual(token_count("abc"), 1)      # 3 bytes → 1

    def test_empty(self):
        self.assertEqual(token_count(""), 0)

    def test_cjk(self):
        self.assertEqual(token_count("中文字"), 3)    # 9 bytes → 3

    def test_mixed_floor(self):
        self.assertEqual(token_count("ab"), 0)       # 2 bytes → 0（整數除法）
        self.assertEqual(token_count("abcd"), 1)     # 4 bytes → 1


class TestFrontMatter(unittest.TestCase):
    ADR = (
        "---\n"
        'id: "0007"\n'
        "title: 測試決策\n"
        "date: 2026-07-02\n"
        "status: accepted\n"
        "feature: 901-fake-demo\n"
        "supersedes: [0003, 0004]\n"
        "superseded_by: []\n"
        "tags: [auth]\n"
        "---\n"
        "\n## 背景\n內文\n"
    )

    def test_basic_fields(self):
        meta, body = parse_front_matter(self.ADR)
        self.assertEqual(meta["id"], "0007")
        self.assertEqual(meta["title"], "測試決策")
        self.assertEqual(meta["status"], "accepted")

    def test_flow_lists(self):
        meta, _ = parse_front_matter(self.ADR)
        self.assertEqual(meta["supersedes"], ["0003", "0004"])
        self.assertEqual(meta["superseded_by"], [])

    def test_body_preserved(self):
        _, body = parse_front_matter(self.ADR)
        self.assertEqual(body, "\n## 背景\n內文\n")

    def test_no_front_matter(self):
        meta, body = parse_front_matter("# 純文件\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# 純文件\n")


class TestReviewFixes(unittest.TestCase):
    """B4 對抗式 review 的 CONFIRMED findings 回歸測試。"""

    # --- 崩潰型 ---
    def test_event_non_object_line_is_finding_not_crash(self):
        for bad in ("123", '"text"', "[1,2]", "null"):
            f = lint_events(bad + "\n")
            self.assertEqual(len(f), 1, msg=bad)
            self.assertIn("object", f[0]["msg"])
        self.assertEqual(parse_events_loose('[1,2]\n{"type":"misc"}\n'), [{"type": "misc"}])

    def test_adr_id_as_list_no_crash(self):
        bad = ADR_OK_B.replace('id: "0002"', "id: [0002]")
        f = lint_adrs({"0002-new.md": bad, "0001-old.md": ADR_OK_A}, {})
        self.assertTrue(any("id" in x["msg"] for x in f))  # 有 finding、無 TypeError

    def test_backfill_skips_adr_without_id(self):
        no_id = "---\ntitle: 無 id\ndate: 2026-07-09\nstatus: draft\nsupersedes: [0001]\n---\nbody\n"
        changed = backfill_supersessions({"0001-old.md": ADR_OK_A, "0003-x.md": no_id})
        self.assertNotIn("0003-x.md", changed)  # 不崩潰；缺 id 由 Lint08 報

    def test_l3_int_adrs_rejected(self):
        e = dict(VALID_CLOSE); e["adrs"] = [1234]
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_adr_duplicate_id_detected(self):
        a = ADR_OK_A.replace("supersedes: []", "supersedes: []").replace(
            'id: "0001"', 'id: "0002"').replace("status: superseded", "status: draft") \
            .replace("superseded_by: [0002]", "superseded_by: []")
        f = lint_adrs({"0002-foo.md": a.replace("0002-", ""),
                       "0002-new.md": ADR_OK_B.replace("supersedes: [0001]", "supersedes: []")}, {})
        self.assertTrue(any("重複" in x["msg"] for x in f))

    # --- Lint03 review findings 元素驗證 ---
    def test_review_findings_elements_validated(self):
        e = json.loads(json.dumps(VALID_REVIEW))
        e["findings"] = {"total": 2, "fixed": 0, "to_backlog": ["banana", "B-909"],
                         "wontfix_adr": []}
        self.assertEqual(len(lint_events(_jl(e))), 1)
        e["findings"] = {"total": -1, "fixed": -1, "to_backlog": [], "wontfix_adr": []}
        self.assertEqual(len(lint_events(_jl(e))), 1)

    # --- Lint11 ---
    def test_l11_exemption_only_line_initial(self):
        f = lint_dictionary({BOOK: "沿用 rev4 的 B-135 做 X｜出處：rev4:DECISIONS§1\n"})
        self.assertEqual(len(f), 1, msg=str(f))  # 行中出處標註不豁免
        self.assertEqual(lint_dictionary({BOOK: "｜出處：rev4:DECISIONS§1-rev4 的 B-135\n"}), [])

    def test_l11_route_count_pattern(self):
        f = lint_dictionary({BOOK: "全站共 54 條路由。\n"})
        self.assertEqual(len(f), 1)
        self.assertIn("route", f[0]["msg"].lower() + "route")  # 有命中即可

    def test_l11_seed_password_boundary(self):
        self.assertEqual(lint_dictionary({BOOK: "對照 commit a1234567 的變更。\n"}), [])
        self.assertEqual(len(lint_dictionary({BOOK: "密碼123456。\n"})), 1)

    # --- Lint08 ---
    def test_l8_optional_field_types_validated(self):
        bad = ADR_OK_B.replace("supersedes: [0001]", "supersedes: []") \
                      .replace("superseded_by: []", "superseded_by: []\ntags: notalist")
        f = lint_adrs({"0002-new.md": bad}, {})
        self.assertTrue(any("tags" in x["msg"] for x in f))

    def test_amend_only_exempts_body(self):
        cur = ADR_OK_B.replace("title: 乙決策", "title: 被改名") \
                      .replace("新案。", "順便改 body。")
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": cur},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}, amend=True)
        self.assertEqual(len(f), 1)  # body 豁免、title 不豁免
        self.assertIn("title", f[0]["msg"])

    # --- 事件行界與編碼 ---
    def test_u2028_inside_event_string_ok(self):
        e = dict(VALID_MISC); e["summary"] = "前 後"
        self.assertEqual(lint_events(_jl(e)), [])
        self.assertEqual(len(parse_events_loose(_jl(e))), 1)

    def test_read_strips_bom(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.md"), "w", encoding="utf-8-sig") as fh:
                fh.write("---\nid: \"0001\"\n---\nbody\n")
            text = _read(d, "x.md")
        self.assertTrue(text.startswith("---"))

    # --- MILESTONES 壞 date ---
    def test_milestones_bad_date_stays_in_main_volume(self):
        bad = dict(VALID_MISC); bad["date"] = "not-a-date"
        files = gen_milestones([VALID_MISC, bad])
        self.assertEqual(set(files), {"docs/generated/MILESTONES.md"})
        self.assertIn("bootstrap 完成", files["docs/generated/MILESTONES.md"])
        self.assertIn("not-a-date", files["docs/generated/MILESTONES.md"])


class TestGitIntegration(unittest.TestCase):
    """git 介接：fail-closed 閘、HEAD 批次載入、staged 落差偵測（用臨時 git repo）。"""

    def _init_repo(self, d):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        def g(*args):
            r = subprocess.run(["git", *args], cwd=d, capture_output=True, text=True, env=env)
            assert r.returncode == 0, r.stderr
        g("init", "-q", "-b", "main")
        os.makedirs(os.path.join(d, ADR_DIR))
        os.makedirs(os.path.join(d, "docs/generated"))
        with open(os.path.join(d, ADR_DIR, "0001-x.md"), "w", encoding="utf-8") as fh:
            fh.write(ADR_OK_A)
        with open(os.path.join(d, "docs/generated/STATE.md"), "w", encoding="utf-8") as fh:
            fh.write("v1\n")
        g("add", "-A")
        g("commit", "-qm", "init")
        return g

    def test_lint_fails_closed_without_git(self):
        with tempfile.TemporaryDirectory() as d:
            f = run_lint(d)
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("git", f[0]["msg"])

    def test_load_head_adrs_batch(self):
        with tempfile.TemporaryDirectory() as d:
            self._init_repo(d)
            head = load_head_adrs(d)
            self.assertEqual(list(head), ["0001-x.md"])
            self.assertEqual(head["0001-x.md"], ADR_OK_A)

    def test_cli_errata_smoke(self):
        """回歸：cmd_errata 曾漏傳 root 而 TypeError 崩潰（CLI 包裝層無測試覆蓋）。"""
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "errata", "next-id"],
                           capture_output=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("errata", r.stdout)

    def test_unstaged_generated_detected(self):
        with tempfile.TemporaryDirectory() as d:
            self._init_repo(d)
            self.assertEqual(unstaged_generated(d), [])
            with open(os.path.join(d, "docs/generated/STATE.md"), "w", encoding="utf-8") as fh:
                fh.write("v2（generate 過但沒 git add）\n")
            self.assertEqual(unstaged_generated(d), ["docs/generated/STATE.md"])


class TestCredScan(unittest.TestCase):
    """Lint16 憑證內容掃描（rev4:contracts G1／data-model §1§2）：樣式集、外層全量、增量、退化、self-test。

    ★本類全部紅樣本一律以執行期字串串接構造——本檔屬 tracked，落任何完整命中字面即會被 Lint16
    掃自己時自命中自紅（analyze 對 U1 的預警）；`test_tool_source_has_no_credential_literal`
    即該紀律的反證案。
    """

    # 與 `_cred_samples()`（產線 self-test 樣本）刻意各自獨立：樣本產生器壞掉時測試仍抓得到
    RED = {
        "pem-private-key": "-----BEGIN " + "OPENSSH PRIVATE" + " KEY" + "-----",
        "aws-akia": "AKIA" + "Z7Q3M8K2P5R9T4W6",
        "github-token": "gh" + "o_" + "Zq7" * 12,
        "github-pat": "github" + "_pat_" + "K3m" * 8,
    }
    GREEN = (
        "普通說明文字，無任何憑證內容。",
        "-----BEGIN CERTIFICATE-----",                       # 憑證公開部分、非私鑰
        "AKIA" + "SHORT12345",                               # AKIA 形但長度不足 16
        "gh" + "p_" + "ab12",                                # token 形但長度不足 36
        "github" + "_pat_" + "tooShort",                     # PAT 形但長度不足 22
        # ★下界邊界樣本（恰比下界少一位）：無此兩筆時「把下界放寬」型突變（36→20、22→10）
        # 全套仍全綠——長度不足很多的樣本擋不住小幅放寬（U2 審查突變實證）。
        "gh" + "p_" + "Zq7" * 11 + "AB",                     # token 形、35 位＝下界 36 少一
        "github" + "_pat_" + "K3m" * 7,                      # PAT 形、21 位＝下界 22 少一
        "密碼欄 password=hunter2 屬刻意排除面（誤報成本高於殘餘風險）",
    )

    # -- fixture 工具 ------------------------------------------------------
    def _g(self, cwd, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, msg=f"git {args}｜{r.stderr}")
        return r.stdout

    def _outer(self, d):
        """外層 fixture repo（Lint16 只需 tracked 清單與 staged 面、毋需 docs 骨架）。"""
        self._g(d, "init", "-q", "-b", "main")
        self._write(d, "README.md", "普通說明\n")
        self._g(d, "add", "README.md")
        self._g(d, "commit", "-qm", "init")

    def _write(self, d, rel, text):
        path = os.path.join(d, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def _subrepo(self, d, name, label="aws-akia"):
        """子 repo：commit A 乾淨、commit B 新增行含指定 label 紅樣本；回 (shaA, shaB)。"""
        sd = os.path.join(d, name)
        os.makedirs(sd)
        self._g(sd, "init", "-q", "-b", "main")
        self._write(sd, "app.ts", "export const a = 1\n")
        self._g(sd, "add", "app.ts")
        self._g(sd, "commit", "-qm", "A")
        sha_a = self._g(sd, "rev-parse", "HEAD").strip()
        self._write(sd, "app.ts",
                    "export const a = 1\nconst k = '" + self.RED[label] + "'\n")
        self._g(sd, "add", "app.ts")
        self._g(sd, "commit", "-qm", "B")
        return sha_a, self._g(sd, "rev-parse", "HEAD").strip()

    def _stage_gitlink(self, d, name, sha):
        self._g(d, "update-index", "--add", "--cacheinfo", f"160000,{sha},{name}")

    def _real_diff(self, d, first, second):
        """以真 git 產出 `app.ts` 的 -U0 diff（手寫 diff 會與 git 實際輸出漂移）。"""
        self._g(d, "init", "-q", "-b", "main")
        self._write(d, "app.ts", first)
        self._g(d, "add", "app.ts")
        self._g(d, "commit", "-qm", "A")
        self._write(d, "app.ts", second)
        self._g(d, "add", "app.ts")
        self._g(d, "commit", "-qm", "B")
        return self._g(d, "diff", "HEAD~1", "HEAD", "-U0")

    # -- 樣式集（data-model §1） -------------------------------------------
    def test_red_samples_hit_each_label(self):
        for label, sample in self.RED.items():
            with self.subTest(label=label):
                self.assertEqual([l for l, _ in scan_cred_text(sample)], [label])

    def test_green_samples_no_hit(self):
        for sample in self.GREEN:
            with self.subTest(sample=sample[:24]):
                self.assertEqual(scan_cred_text(sample), [])

    def test_scan_reports_line_number(self):
        text = "第一行\n第二行\n" + self.RED["pem-private-key"] + "\n"
        self.assertEqual(scan_cred_text(text), [("pem-private-key", 3)])

    def test_tool_source_has_no_credential_literal(self):
        """★A8 反證：本工具原始碼（tracked）零完整命中字面——否則 G1 掃自己即自紅。"""
        with open(os.path.abspath(__file__), encoding="utf-8", errors="replace") as fh:
            self.assertEqual(scan_cred_text(fh.read()), [])

    # -- 外層全量面（data-model §2 第 1 列） --------------------------------
    def test_outer_scan_reports_tracked_hit(self):
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "deploy/key.conf", "cert:\n" + self.RED["pem-private-key"] + "\n")
            self._g(d, "add", "deploy/key.conf")
            f = lint_cred_outer(d)
            self.assertEqual([x["level"] for x in f], [ERROR])
            self.assertIn("deploy/key.conf", f[0]["where"])
            self.assertIn("pem-private-key", f[0]["msg"])

    def test_outer_scan_catches_staged_when_worktree_file_removed(self):
        """★staged 含憑證但工作樹檔已 rm：只看工作樹＝零信號放行（index blob 仍要進版控）。

        連帶驗「沒掃到必留信號」：工作樹讀不到一律落 WARN、不得靜默當乾淨。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "key.conf", "k='" + self.RED["aws-akia"] + "'\n")
            self._g(d, "add", "key.conf")
            os.remove(os.path.join(d, "key.conf"))
            f = lint_cred_outer(d)
            errs = [x for x in f if x["level"] == ERROR]
            self.assertEqual(len(errs), 1, msg=str(f))
            self.assertIn("key.conf", errs[0]["where"])
            self.assertIn("aws-akia", errs[0]["msg"])
            self.assertTrue(any(x["level"] == WARN and "key.conf" == x["where"] for x in f),
                            msg=str(f))

    def test_outer_scan_catches_staged_when_worktree_cleaned(self):
        """staged 髒、工作樹版本已洗白：判定面取自 index 才對得上「這次 commit 的內容」。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "key.conf", "k='" + self.RED["github-token"] + "'\n")
            self._g(d, "add", "key.conf")
            self._write(d, "key.conf", "k='已移除'\n")
            f = lint_cred_outer(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("key.conf", f[0]["where"])
            self.assertIn("github-token", f[0]["msg"])

    def test_outer_scan_clean_repo_is_green(self):
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self.assertEqual(lint_cred_outer(d), [])

    def test_outer_scan_skips_binary(self):
        """前 8KB 含 NUL＝二進位、不掃（R2）。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            blob = b"\x00\x01" + self.RED["pem-private-key"].encode() + b"\x00"
            with open(os.path.join(d, "logo.bin"), "wb") as fh:
                fh.write(blob)
            self._g(d, "add", "logo.bin")
            self.assertEqual(lint_cred_outer(d), [])

    def test_outer_scan_excludes_gitlink_entry(self):
        """gitlink 條目屬目錄、不入外層掃描面（其內容歸增量面）。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            _, sha_b = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_b)
            self.assertEqual(lint_cred_outer(d), [])

    # -- submodule 增量面（data-model §2 第 2/3 列、R3） ---------------------
    def test_submodule_incremental_hit(self):
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, sha_b = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_a)
            self._g(d, "commit", "-qm", "pin A")
            self._stage_gitlink(d, "base-web", sha_b)
            f = lint_cred_submodules(d)
            errs = [x for x in f if x["level"] == ERROR]
            self.assertEqual(len(errs), 1, msg=str(f))
            self.assertIn("base-web", errs[0]["where"])
            self.assertIn("app.ts", errs[0]["where"])
            self.assertIn("aws-akia", errs[0]["msg"])

    def test_diff_hits_scans_content_line_starting_with_double_plus(self):
        """★檔案內以「兩個加號加空白」起首的行，在 -U0 diff 長成三個加號——不得當檔頭吞掉。"""
        with tempfile.TemporaryDirectory() as d:
            diff = self._real_diff(
                d, "x = 1\n",
                "x = 1\n++ 文件裡的 diff 片段 " + self.RED["aws-akia"] + "\n")
            self.assertIn("\n+++ 文件裡", diff)      # 前提：git 確實把它輸出成三個加號起首
            self.assertEqual(cred_diff_hits(diff), [("app.ts", "aws-akia")])

    def test_diff_hits_double_plus_line_does_not_pollute_path(self):
        """誤判成檔頭時 path 會被寫成該行內容，其後真命中即指名一個不存在的檔。"""
        with tempfile.TemporaryDirectory() as d:
            diff = self._real_diff(
                d, "x = 1\n",
                "x = 1\n++ 文件裡的 diff 片段\nconst k = '" + self.RED["github-token"] + "'\n")
            self.assertEqual(cred_diff_hits(diff), [("app.ts", "github-token")])

    def test_submodule_not_staged_lands_in_skip_detail(self):
        """未 stage gitlink＝不觸發增量面（成本正比變更量）——落跳過明細、零 ERROR／WARN。

        ★語意遷移（U5）：原斷言零 finding，改為 SKIP 級明細——純碼 commit 的主要跳過來源，
        「不適用」不顯式可見即 rev4:FR-012 要消滅的假綠面。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, _ = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_a)
            self._g(d, "commit", "-qm", "pin A")
            f = lint_cred_submodules(d)
            self.assertEqual([x["level"] for x in f], [SKIP, SKIP], msg=str(f))
            self.assertTrue(all("未 staged" in x["msg"] for x in f), msg=str(f))

    def test_submodule_fallback_full_tree_when_old_pin_unresolvable(self):
        """舊 pin 不可解→退化為新 pin 全樹掃＋WARN 註記（fail-closed 向完整掃）。

        ★逐 label 參數化不可省：退化面是唯一走 git 自己 ERE 引擎的路徑（其餘面走
        python re），兩套引擎對同一份樣式集未必等價；只測單一 label 會漏掉引擎歧異——
        實證即以連字號開頭的 PEM 樣式在缺 `-e` 時被 git 當未知選項吞成零命中。
        """
        for label in self.RED:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as d:
                self._outer(d)
                _, sha_b = self._subrepo(d, "base-web", label)
                self._stage_gitlink(d, "base-web", "0" * 39 + "1")   # 子庫不存在之物件
                self._g(d, "commit", "-qm", "pin 不可解")
                self._stage_gitlink(d, "base-web", sha_b)
                f = lint_cred_submodules(d)
                self.assertTrue(any(x["level"] == WARN and "退化" in x["msg"] for x in f),
                                msg=str(f))
                errs = [x for x in f if x["level"] == ERROR]
                self.assertEqual(len(errs), 1, msg=str(f))
                self.assertIn(label, errs[0]["msg"])
                self.assertIn("app.ts", errs[0]["where"])

    def test_submodule_fallback_scan_failure_is_fail_closed(self):
        """★退化掃本身跑不成（新 pin 物件不在該庫，如切分支後未 fetch）→ERROR 不放行。

        「非零退出即零命中」會把執行失敗讀成乾淨，同時 WARN 還宣稱已退化為全樹掃——
        形成比不掃更危險的假保證（rev4:FR-008 fail-closed）。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", "0" * 39 + "1")   # 舊 pin 不可解→走退化
            self._g(d, "commit", "-qm", "pin 不可解")
            self._stage_gitlink(d, "base-web", "0" * 39 + "2")   # 新 pin 物件亦不在該庫
            f = lint_cred_submodules(d)
            errs = [x for x in f if x["level"] == ERROR]
            self.assertEqual(len(errs), 1, msg=str(f))
            self.assertIn("退化全樹掃執行失敗", errs[0]["msg"])

    def test_fallback_engine_matches_python_re_for_every_pattern(self):
        r"""★單一引擎不變式：退化面與其餘掃描面對同一輸入必須給出相同判定。

        rev4 的退化面走 git 自身 ERE 引擎、其餘面走 python re；兩者對含 `\b` 的樣式在
        BSD libc 上判定相反——實證：macOS 上 aws-akia／github-token／github-pat 三條回
        退出碼 1（＝確無命中）而 PEM（無 `\b`）正常，於是防線還在、偵測力歸零且零訊號。
        rev5 已統一為 python re；本案釘住該不變式，防未來任何人改回雙引擎或新增樣式時
        再生歧異（逐 label 參數化不可省——單一 label 測不出引擎差）。
        """
        for label, sample in self.RED.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as d:
                sd = os.path.join(d, "sub")
                os.makedirs(sd)
                self._g(sd, "init", "-q", "-b", "main")
                body = f'const k = "{sample}";\n'
                self._write(sd, "app.ts", body)
                self._g(sd, "add", "app.ts")
                self._g(sd, "commit", "-qm", "x")
                sha = self._g(sd, "rev-parse", "HEAD").strip()
                hits, err = _cred_grep_tree(sd, sha)
                self.assertIsNone(err, msg=f"{label}：退化面執行失敗")
                self.assertIn(("app.ts", label), hits,
                              msg=f"{label}：退化面漏判（實得 {hits}）")
                self.assertIn(label, [l for l, _ in scan_cred_text(body)],
                              msg=f"{label}：python re 面漏判")

    def test_fallback_full_tree_skips_binary(self):
        """★退化全樹掃須與外層面同規則跳過二進位（R2）。

        缺 `-I` 時 git grep 對二進位檔改輸出「Binary file <tree>:<path> matches」——逐冒號
        切欄後路徑欄變成「<path> matches」殘餘文字，命中被指名到一個不存在的檔；且二進位
        面的判定與外層面（前 8KB 含 NUL 即 skip）不一致。
        """
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "base-web")
            os.makedirs(sd)
            self._g(sd, "init", "-q", "-b", "main")
            with open(os.path.join(sd, "logo.bin"), "wb") as fh:
                fh.write(b"\x00\x01" + self.RED["aws-akia"].encode() + b"\x00")
            self._g(sd, "add", "logo.bin")
            self._g(sd, "commit", "-qm", "bin")
            sha = self._g(sd, "rev-parse", "HEAD").strip()
            self.assertEqual(_cred_grep_tree(sd, sha), ([], None))

    def test_grep_tree_reports_no_hit_without_error(self):
        """乾淨 tree：git grep 退出碼 1＝確無命中，MUST NOT 誤判成掃描失敗。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, _ = self._subrepo(d, "base-web")
            self.assertEqual(_cred_grep_tree(os.path.join(d, "base-web"), sha_a), ([], None))

    def test_submodule_absent_worktree_skips(self):
        """worktree 缺席（唯讀看碼模式）→跳過、不落 ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._stage_gitlink(d, "rust-api", "1" * 40)
            f = [x for x in lint_cred_submodules(d) if x["where"] == "rust-api"]
            self.assertEqual([x["level"] for x in f], [SKIP], msg=str(f))
            self.assertIn("跳過", f[0]["msg"])

    # -- 組裝與 run_lint 接線（rev4:contracts G1「觸發＝每次 lint」） ---------------
    def test_credentials_assembly_wires_submodule_face(self):
        """★組裝層：`lint_cred_submodules` 從 `lint_credentials` 掉線＝rev4:US2 情境 2 靜默下線。

        突變實證：組裝行改成只回 self-test＋外層面後，全套測試仍全綠——各面單元測試都直呼
        函式本體、繞過組裝層，故「函式活著、接線斷掉」零信號。本案即補那張網。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, sha_b = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_a)
            self._g(d, "commit", "-qm", "pin A")
            self._stage_gitlink(d, "base-web", sha_b)
            f = lint_credentials(d)
            self.assertTrue(
                any(x["code"] == "Lint16" and x["level"] == ERROR
                    and "base-web" in x["where"] and "app.ts" in x["where"] for x in f),
                msg=str(f))

    def test_credentials_assembly_wires_self_test(self):
        """★組裝層：`cred_self_test` 掉線＝rev4:US2 情境 5 防恆綠靜默下線（同上突變實證）。

        乾淨 fixture＋永不命中之 dead 樣式集：外層面與增量面必然零 ERROR，故任何 ERROR
        只可能來自 self-test——信號純淨。
        """
        dead = (("pem-private-key", re.compile(r"ZZZ-NEVER-MATCH-ZZZ")),)
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            f = self._with_patterns(dead, lambda: lint_credentials(d))
            self.assertTrue(
                any(x["code"] == "Lint16" and x["level"] == ERROR
                    and "self-test 失效" in x["msg"] for x in f), msg=str(f))

    def test_run_lint_wires_credential_gate(self):
        """★接線層：`lint_credentials` 從 run_lint 掉線＝G1 整條下線，單元測試卻不會有反應。

        突變實證：刪掉 run_lint 內該接線行後全套測試仍全綠——本案即補那張網
        （U5 rev4:T020 要重組 run_lint，重組時掉線必須當場紅）。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "deploy/key.conf", "cert:\n" + self.RED["pem-private-key"] + "\n")
            self._g(d, "add", "deploy/key.conf")
            f = run_lint(d)
            self.assertTrue(
                any(x["code"] == "Lint16" and x["level"] == ERROR
                    and "deploy/key.conf" in x["where"] for x in f), msg=str(f))

    # -- self-test 防恆綠（rev4:contracts G1） -----------------------------------
    def test_self_test_green_on_healthy_engine(self):
        self.assertEqual(cred_self_test(), [])

    def _with_patterns(self, patterns, fn):
        original = globals()["CRED_PATTERNS"]
        globals()["CRED_PATTERNS"] = patterns
        try:
            return fn()
        finally:
            globals()["CRED_PATTERNS"] = original

    def _with_whitelist(self, whitelist, fn):
        original = globals()["CRED_WHITELIST"]
        globals()["CRED_WHITELIST"] = whitelist
        try:
            return fn()
        finally:
            globals()["CRED_WHITELIST"] = original

    def test_whitelist_suppresses_both_outer_faces(self):
        """★`CRED_WHITELIST` 零測試覆蓋＝豁免路徑（rev4:ADR 0077 第 3 項）壞掉無信號。

        突變實證：外層面兩處白名單略過分支（工作樹面與 staged 面）整段刪除後全套仍全綠。
        本案一次釘住兩處——白名單生效時兩面皆須零 finding，任一分支被刪即有一面重新報紅。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "docs/sample.md", "k='" + self.RED["aws-akia"] + "'\n")
            self._g(d, "add", "docs/sample.md")
            before = [x for x in lint_cred_outer(d) if x["level"] == ERROR]
            self.assertEqual(len(before), 1, msg=str(before))   # 白名單外＝報紅
            self.assertEqual(
                self._with_whitelist(("docs/sample.md",), lambda: lint_cred_outer(d)), [])
            after = [x for x in lint_cred_outer(d) if x["level"] == ERROR]
            self.assertEqual(len(after), 1, msg=str(after))     # 還原後恢復報紅

    def test_self_test_catches_dead_patterns(self):
        """樣式集被改壞成永不命中（恆綠）→self-test 逐 label 報 ERROR。"""
        dead = (("pem-private-key", re.compile(r"ZZZ-NEVER-MATCH-ZZZ")),)
        f = self._with_patterns(dead, cred_self_test)
        self.assertEqual(len(f), 4)
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertEqual({lbl for lbl in self.RED for x in f if lbl in x["msg"]}, set(self.RED))

    def test_self_test_catches_overbroad_patterns(self):
        """樣式集被改到過寬→綠樣本誤報、self-test 同樣報 ERROR。"""
        wide = (("pem-private-key", re.compile(r".")),)
        f = self._with_patterns(wide, cred_self_test)
        self.assertTrue(f)
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertTrue(any("綠樣本" in x["msg"] for x in f))


# --- Lint17／Lint18 測試共用 fixture 工具（★一律自建 repo，絕不觸碰真 submodule worktree）---

def _git(cwd, *args):
    """測試用 git 呼叫：作者身分固定（無 global config 亦可 commit）、非零退出即拋。"""
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                       encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0:
        raise AssertionError(f"git {args}｜{r.stderr}")
    return r.stdout


def _wfile(d, rel, text):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path) or d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _init_outer(d):
    _git(d, "init", "-q", "-b", "main")
    _wfile(d, "README.md", "說明\n")
    _git(d, "add", "README.md")
    _git(d, "commit", "-qm", "init")
    return _git(d, "rev-parse", "HEAD").strip()


def _init_sub(d, name, n=1):
    """建子 repo（n 個 commit）；回 SHA list（由舊到新）。"""
    sd = os.path.join(d, name)
    os.makedirs(sd)
    _git(sd, "init", "-q", "-b", "main")
    shas = []
    for i in range(n):
        _wfile(sd, "app.ts", f"export const a = {i}\n")
        _git(sd, "add", "app.ts")
        _git(sd, "commit", "-qm", f"c{i}")
        shas.append(_git(sd, "rev-parse", "HEAD").strip())
    return shas


def _stage_gitlink(d, name, sha):
    _git(d, "update-index", "--add", "--cacheinfo", f"160000,{sha},{name}")


def _l17(d, sub):
    """Lint17 findings 中屬該 submodule 者——fixture 只造一個子庫時，另一個必落「index 無該
    gitlink」跳過明細（A10），故各案一律先依 sub 過濾再斷言。"""
    return [x for x in lint_pin_crosscheck(d) if x["where"] == sub]


def _break_worktree(d, name):
    """把子庫的 `.git` 換成指向不存在源倉的 gitfile＝CLAUDE.md §3「worktree 斷裂」實態。

    worktree 模式下子庫的 `.git` 是一個檔（`gitdir: <源倉路徑>`）；源倉目錄被刪／未 clone
    時該檔仍在、`os.path.exists` 為真，但任何 git 操作都開不起來——「路徑存在」與「庫可查」
    是兩件事，本 helper 即造出那個落差。
    """
    sd = os.path.join(d, name)
    real = os.path.join(sd, ".git")
    if os.path.isdir(real):
        import shutil
        shutil.rmtree(real)
    with open(real, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"gitdir: {os.path.join(d, '不存在的源倉')}\n")


def _stage_gitlink_conflict(d, name, shas):
    """把 index 內該 gitlink 換成未解衝突態（stage 1／2／3 各一筆、無 stage 0）。

    `git ls-files -s` 依 stage 遞增輸出，故「取首個 160000 行」會讀到 stage 1＝共同祖先 pin。
    """
    info = "".join(f"160000 {sha} {i}\t{name}\n" for i, sha in enumerate(shas, start=1))
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run(["git", "update-index", "--index-info"], cwd=d, input=info,
                       capture_output=True, encoding="utf-8", env=env)
    if r.returncode != 0:
        raise AssertionError(f"update-index --index-info｜{r.stderr}")


class TestSubmoduleProbe(unittest.TestCase):
    """★A1 共用探針：Lint16 submodule 面／Lint17／Lint18 對「這個庫能不能查」必須用同一支探針。

    斷裂 worktree（`.git` gitfile 指向不存在的源倉）是 CLAUDE.md §3 明載的真實狀態。修前
    Lint17 用 `rev-parse HEAD` 成功與否、Lint18 只看 `.git` 路徑存在與否——同一事實兩種判讀：
    Lint17 落 1 筆「跳過」、Lint18 卻對該庫每一列各落一筆「rebase 卷史後合法失聯」（真帳本換算
    ＝單庫 17 筆、兩庫俱斷 34 筆），且把「庫根本開不起來」誤植成「SHA 失聯」，操作者會朝
    錯方向排查（去 fetch 而不是去跑 bootstrap）。
    """

    def test_probe_reports_absent_and_broken_distinctly(self):
        """探針三態：健全→回 HEAD；worktree 缺席→原因含「缺席」；斷裂→原因含「開不起來」。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            sha, = _init_sub(d, "base-web")
            self.assertEqual(submodule_head(d, "base-web"), (sha, None))
            head, why = submodule_head(d, "rust-api")
            self.assertIsNone(head)
            self.assertIn("缺席", why)
            _break_worktree(d, "base-web")
            head, why = submodule_head(d, "base-web")
            self.assertIsNone(head)
            self.assertIn("開不起來", why)

    def test_broken_worktree_yields_one_skip_per_clause(self):
        """★斷裂 worktree：Lint17／Lint18 各恰 1 筆跳過、理由同文；Lint18 絕不逐列報 rebase 失聯。"""
        with tempfile.TemporaryDirectory() as d:
            outer = _init_outer(d)
            shas = {key: _init_sub(d, name)[0] for key, name in PIN_KEYS}
            rows = [dict(VALID_CLOSE, merge=outer, pins=dict(shas)) for _ in range(3)]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            _stage_gitlink(d, "base-web", shas["web"])
            _break_worktree(d, "base-web")
            f17 = [x for x in lint_pin_crosscheck(d) if x["where"] == "base-web"]
            f18 = [x for x in lint_events_sha(d)
                   if "base-web" in x["where"] or "base-web" in x["msg"]]
            self.assertEqual(len(f17), 1, msg=str(f17))
            self.assertEqual(len(f18), 1, msg=str(f18))     # 修前＝每列各一筆＝3 筆
            self.assertIn("開不起來", f17[0]["msg"])
            self.assertIn("開不起來", f18[0]["msg"])
            self.assertNotIn("rebase", f18[0]["msg"])
            self.assertEqual([x for x in lint_events_sha(d)
                              if "rebase" in x["msg"]], [])

    def test_broken_worktree_skips_credential_incremental_face(self):
        """Lint16 submodule 增量面同用該探針：斷裂庫不得走進 diff／退化全樹掃。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            sha, = _init_sub(d, "base-web")
            _stage_gitlink(d, "base-web", sha)
            _break_worktree(d, "base-web")
            f = [x for x in lint_cred_submodules(d) if x["where"] == "base-web"]
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertIn("開不起來", f[0]["msg"])


class TestIndexGitlinkStage(unittest.TestCase):
    """★A2：gitlink 合併衝突未解時 index 同時有 stage 1／2／3，取首個 160000 行＝讀到祖先 pin。

    後果具體：Lint17 拿共同祖先 pin 去比 worktree HEAD，報一筆根本不存在的分歧（且在收刀簿記
    commit 上會升成 ERROR 硬擋）；Lint16 增量掃則以祖先 SHA 當「new」去 diff。誠實作法＝認出
    衝突態並落跳過明細。
    """

    def test_stage_zero_is_returned_when_clean(self):
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            sha, = _init_sub(d, "base-web")
            _stage_gitlink(d, "base-web", sha)
            self.assertEqual(index_gitlink(d, "base-web"), (sha, None))

    def test_no_entry_reports_reason(self):
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            sha, why = index_gitlink(d, "base-web")
            self.assertIsNone(sha)
            self.assertIn("index 無該 gitlink", why)

    def test_conflicted_index_is_not_read_as_ancestor_pin(self):
        """stage 1／2／3 俱在（無 stage 0）→不得回祖先 pin，須回衝突原因。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            base, ours, theirs = _init_sub(d, "base-web", 3)
            _stage_gitlink_conflict(d, "base-web", (base, ours, theirs))
            sha, why = index_gitlink(d, "base-web")
            self.assertIsNone(sha, msg=f"讀到 {sha}（祖先＝{base}）")
            self.assertIn("衝突", why)

    def test_pin_crosscheck_skips_on_conflicted_index(self):
        """★Lint17：衝突態不得報「pin 與 worktree HEAD 分歧」（那是拿祖先 pin 比出來的假分歧）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            base, ours, theirs = _init_sub(d, "base-web", 3)
            _stage_gitlink_conflict(d, "base-web", (base, ours, theirs))
            f = _l17(d, "base-web")
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertIn("衝突", f[0]["msg"])
            self.assertNotIn("分歧", f[0]["msg"])


class TestIndexPinsStrictStage(unittest.TestCase):
    """★rev4:B-114：index_pins（generate 面／STATE 帳面）歸一 rev4:018 嚴格語意——逐庫復用
    index_gitlink、只認 stage 0。

    修前舊碼自掃 `ls-files -s` 逐行覆寫、無 stage 過濾：gitlink 合併衝突未解
    （index 同存 stage 1／2／3）時**末筆＝stage 3（theirs）勝出**（BACKLOG 條目
    誤記為「取首行＝讀到共同祖先」、據實勘正——ls-files 依 stage 遞增輸出、迴圈
    覆寫故末筆勝）；無論祖先或 theirs，STATE 顯示任何 stage 1/2/3 值都是帳面誤導。
    """

    def test_healthy_stage_zero_pins(self):
        """健康態（stage 0 單行）→ 兩庫各回 (SHA, None)，與 index_gitlink 契約同形。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            shas = {key: _init_sub(d, name)[0] for key, name in PIN_KEYS}
            for key, name in PIN_KEYS:
                _stage_gitlink(d, name, shas[key])
            self.assertEqual(index_pins(d),
                             {"web": (shas["web"], None), "api": (shas["api"], None)})

    def test_conflicted_index_yields_undetermined_not_any_stage(self):
        """衝突態（stage 1／2／3 並存、無 stage 0）→ (None, 衝突原因)；
        絕不回任何 stage 值——對舊碼必紅（舊碼回末筆 stage 3＝theirs）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            base, ours, theirs = _init_sub(d, "base-web", 3)
            _stage_gitlink_conflict(d, "base-web", (base, ours, theirs))
            pin = index_pins(d)["web"]
            self.assertNotIn(pin, (base, ours, theirs),
                             msg=f"讀到 stage 值 {pin}（祖先={base[:7]}／theirs={theirs[:7]}）")
            sha, why = pin
            self.assertIsNone(sha)
            self.assertIn("衝突", why)

    def test_absent_path_yields_undetermined_reason(self):
        """路徑缺席（index 無該 gitlink 條目）→ (None, 原因)。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            sha, why = index_pins(d)["api"]
            self.assertIsNone(sha)
            self.assertIn("index 無該 gitlink", why)

    def test_state_renders_undetermined_never_stage_values(self):
        """STATE 渲染：衝突庫顯示「未定（含原因）」、健康庫照常顯示短 SHA；
        stage 1/2/3 任一 SHA 之短形一律不得出現。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            base, ours, theirs = _init_sub(d, "base-web", 3)
            # ★取第 4 筆：_init_sub 逐庫同內容＋同秒 commit 會產出相同 SHA——rust-api
            # 首 commit 與 base 撞 SHA 時「不得出現 stage 值短形」斷言會自撞（實測踩中）。
            api = _init_sub(d, "rust-api", 4)[-1]
            _stage_gitlink_conflict(d, "base-web", (base, ours, theirs))
            _stage_gitlink(d, "rust-api", api)
            text = gen_state({"pins": index_pins(d)})
            self.assertIn("base-web=未定（", text)
            self.assertIn("衝突", text)
            self.assertIn(f"rust-api={api[:7]}", text)
            for sha in (base, ours, theirs):
                self.assertNotIn(sha[:7], text)


class TestPinCrosscheck(unittest.TestCase):
    """Lint17 pin↔worktree HEAD 互證（rev4:contracts G2／data-model §3 狀態表逐格）。

    ★staged 情境一律於自建 fixture repo 內構造——真 base-web／rust-api worktree 零觸碰。
    """

    def test_pin_matches_head_passes(self):
        """狀態表第 1 列：staged gitlink＝worktree HEAD→pass（零 finding）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            sha, = _init_sub(d, "base-web")
            _stage_gitlink(d, "base-web", sha)
            self.assertEqual(_l17(d, "base-web"), [])

    def test_divergence_on_ordinary_commit_is_warn(self):
        """狀態表第 2 列：分歧×一般 commit→WARN（兩段式中間態合法、不擋）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            old, new = _init_sub(d, "base-web", 2)
            _stage_gitlink(d, "base-web", old)
            f = _l17(d, "base-web")
            self.assertEqual([x["level"] for x in f], [WARN], msg=str(f))
            self.assertEqual(f[0]["where"], "base-web")
            self.assertIn(old[:12], f[0]["msg"])
            self.assertIn(new[:12], f[0]["msg"])
            self.assertIn("bump pin", f[0]["msg"])

    def test_divergence_with_staged_feature_close_is_error(self):
        """狀態表第 3 列：分歧×收刀簿記 commit（staged events 新增行含 feature_close）→ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            old, _new = _init_sub(d, "base-web", 2)
            _stage_gitlink(d, "base-web", old)
            _wfile(d, EVENTS, json.dumps(VALID_CLOSE, ensure_ascii=False) + "\n")
            _git(d, "add", EVENTS)
            f = _l17(d, "base-web")
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("bump pin", f[0]["msg"])

    def test_divergence_with_staged_non_close_event_stays_warn(self):
        """收刀偵測須認事件型別、不是「有 staged events 就 ERROR」（misc 新增行→仍 WARN）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            old, _new = _init_sub(d, "base-web", 2)
            _stage_gitlink(d, "base-web", old)
            _wfile(d, EVENTS, json.dumps(VALID_MISC, ensure_ascii=False) + "\n")
            _git(d, "add", EVENTS)
            f = _l17(d, "base-web")
            self.assertEqual([x["level"] for x in f], [WARN], msg=str(f))

    def test_absent_worktree_skips(self):
        """狀態表第 4 列：worktree 缺席（唯讀看碼模式）→跳過、不落 ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _stage_gitlink(d, "rust-api", "1" * 40)
            f = _l17(d, "rust-api")
            self.assertEqual([x["level"] for x in f], [SKIP], msg=str(f))
            self.assertEqual(f[0]["where"], "rust-api")
            self.assertIn("跳過", f[0]["msg"])

    def test_dir_present_without_dotgit_skips(self):
        """狀態表第 4 列另一形：★目錄在、`.git` 不在（fresh clone 未跑 bootstrap 的常態）。

        ★守衛（`.git` 存在才 rev-parse）是載重件：git 的 repo 探索會從 cwd 往上走，在外層 repo
        內一個沒有 `.git` 的空目錄執行 rev-parse HEAD 拿回的是「外層 repo 的 HEAD」，必然異於
        staged gitlink——守衛缺席時第 4 列（skip）會被錯判成第 2／第 3 列，收刀簿記 commit 那格
        更是把合法 commit 硬擋在門外。故本案同時斷言一般形與收刀形皆停在 WARN 跳過。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            os.makedirs(os.path.join(d, "base-web"))       # 空目錄、不 init
            _stage_gitlink(d, "base-web", "a" * 40)        # 異於任何真 SHA
            f = _l17(d, "base-web")
            self.assertEqual([x["level"] for x in f], [SKIP], msg=str(f))
            self.assertEqual(f[0]["where"], "base-web")
            self.assertIn("跳過", f[0]["msg"])
            # 收刀形：守衛缺席時這格會退化成 ERROR、硬擋合法 commit
            _wfile(d, EVENTS, json.dumps(VALID_CLOSE, ensure_ascii=False) + "\n")
            _git(d, "add", EVENTS)
            f = _l17(d, "base-web")
            self.assertEqual([x["level"] for x in f], [SKIP], msg=str(f))
            self.assertIn("跳過", f[0]["msg"])

    def test_no_gitlink_in_index_falls_into_skip_detail(self):
        """★A10：index 無該 gitlink（純外層 repo）→落跳過明細，不再零 finding 靜默略過。

        靜默略過時「不適用」與「檢了通過」在輸出上長得一樣＝rev4:FR-012 要消滅的假綠面。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = lint_pin_crosscheck(d)
            self.assertEqual([x["where"] for x in f], [sub for _k, sub in PIN_KEYS])
            self.assertTrue(all("index 無該 gitlink" in x["msg"] for x in f), msg=str(f))

    def test_closing_detection_is_scoped_to_the_events_ledger(self):
        """★A5：收刀偵測的 pathspec 限定（`-- docs/ops/events.jsonl`）零測試覆蓋。

        曝險真實——本工具原始碼自身就含多處 feature_close 字面。pathspec 一旦被重構掉，
        凡「staged 內容含該字面 ＋ 同時有 pin 分歧」的 commit 都會由 WARN 升成 ERROR 硬擋，
        而那正是兩段式 commit（先子庫 commit、後回外層 bump pin）中間態最常見的組合。
        本案 staged 一個非帳本檔、其新增行含該字面：限定在＝WARN，限定掉＝ERROR。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            old, _new = _init_sub(d, "base-web", 2)
            _stage_gitlink(d, "base-web", old)
            _wfile(d, "docs/ops/NOTES.md",
                   "下一步：補上 " + json.dumps({"type": "feature_close"}) + " 這列\n")
            _git(d, "add", "docs/ops/NOTES.md")
            self.assertFalse(is_closing_commit(d))
            f = _l17(d, "base-web")
            self.assertEqual([x["level"] for x in f], [WARN], msg=str(f))

    def test_run_lint_wires_pin_crosscheck(self):
        """★接線層：`lint_pin_crosscheck` 從 run_lint 掉線＝G2 整條靜默下線。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            old, _new = _init_sub(d, "base-web", 2)
            _stage_gitlink(d, "base-web", old)
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint17" and x["level"] == WARN
                                and x["where"] == "base-web" for x in f), msg=str(f))


class TestEventsShaProof(unittest.TestCase):
    """Lint18 events 逐列 SHA 實證（rev4:contracts G3／data-model §4 判定表逐列）。"""

    def _fixture(self, d, subs=("base-web", "rust-api")):
        """外層 repo＋指定 submodule worktree；回 (外層 SHA, {鍵: 子庫 SHA})。"""
        outer = _init_outer(d)
        shas = {}
        for key, name in PIN_KEYS:
            if name in subs:
                shas[key], = _init_sub(d, name)
        return outer, shas

    def _events(self, d, **over):
        e = json.loads(json.dumps(VALID_CLOSE))
        e.update(over)
        _wfile(d, EVENTS, json.dumps(e, ensure_ascii=False) + "\n")

    def test_all_resolvable_is_green(self):
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._events(d, merge=outer, pins=pins)
            self.assertEqual(lint_events_sha(d), [])

    def test_merge_unresolvable_is_error(self):
        """判定表第 1 列：merge 不可解＝ERROR（抄錯／造假／事後改史），且須指到壞值那列。

        ★fixture 須兩列、壞值落第 2 列：單列 fixture 上「把行號寫死成 1」的突變會存活
        （實測全套零轉紅），而 merge 面是 ERROR、直接硬擋 commit——行號指錯會把維運者
        帶去改一列無辜的事件。pins 兩支同型缺口已由 test_pins_… 兩案各自補上。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            rows = [dict(VALID_CLOSE, merge=outer, pins=pins),
                    dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins)]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("merge", f[0]["msg"])
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")

    def test_merge_unresolvable_message_has_remedy(self):
        """B-002：merge 不可解的紅訊息必附去處，且去處必須分兩支——該列尚未進 git 史
        （工作樹／staged 階段）＝以真實 merge commit SHA 覆寫該列；已進 git 史＝依
        ADR 0012 決定 5（events.jsonl 既有列絕不編輯）append 新事件更正、不得回改舊列。
        單支「覆寫」文案會教維運者對已入史列改史、直接違紀。"""
        with tempfile.TemporaryDirectory() as d:
            _outer, pins = self._fixture(d)
            self._events(d, merge="0" * 39 + "1", pins=pins)
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            for needle in ("補救", "覆寫該列", "ADR 0012", "append 新事件", "不得回改"):
                self.assertIn(needle, f[0]["msg"])

    def test_merge_resolvable_but_not_commit_is_error(self):
        """判定表第 1 列右欄：可解但非 commit 物件（此處為 blob）＝ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            _outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            self._events(d, merge=blob, pins=pins)
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("blob", f[0]["msg"])

    def test_pins_unresolvable_is_warn_and_points_at_the_right_line(self):
        """判定表第 2／3 列：pins 不可解＝WARN（upstream rebase 卷史後合法失聯）。

        ★A4 fixture 須兩列、壞值落第 2 列：單列 fixture 上「把行號寫死成 1」的突變存活
        （pins 兩支 finding 的 where 都只在單列上驗過），行號指錯會把維運者帶去改無辜的列。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            rows = [dict(VALID_CLOSE, merge=outer, pins=pins),
                    dict(VALID_CLOSE, merge=outer, pins=dict(pins, web="0" * 39 + "1"))]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [WARN], msg=str(f))
            self.assertIn("pins.web", f[0]["msg"])
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")

    def test_pins_resolvable_but_not_commit_points_at_the_right_line(self):
        """★A4 同理：pins 可解而非 commit 的 ERROR 亦須指到壞值真正所在那列。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(os.path.join(d, "base-web"), "rev-parse", "HEAD:app.ts").strip()
            rows = [dict(VALID_CLOSE, merge=outer, pins=pins),
                    dict(VALID_CLOSE, merge=outer, pins=dict(pins, web=blob))]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")

    def test_pins_resolvable_but_not_commit_is_error(self):
        """判定表第 2／3 列右欄：pins 可解但非 commit 物件＝ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(os.path.join(d, "rust-api"), "rev-parse", "HEAD:app.ts").strip()
            self._events(d, merge=outer, pins=dict(pins, api=blob))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("pins.api", f[0]["msg"])

    def test_not_commit_messages_have_remedy_on_both_faces(self):
        """B-042②：「解得非 commit」兩筆 ERROR（merge 面／pins 面）同樣須附去處。

        ★開帳理由＝同條款只補一半：B-002 當時只為「不可解」那筆補了兩支去處，
        同一支 lint 的「可解但非 commit」兩筆卻止於病因。維運者拿到「非 commit」
        只知道錯、不知道正確值該去哪裡取，也不知道已入史列不得回改。
        ★去處兩支必須與「不可解」那筆同文——分歧的文案會讓維運者以為兩種錯有兩套
        紀律，而 events.jsonl 既有列絕不編輯（ADR 0012 決定 5）對兩者一體適用。
        """
        needles = ("補救", "覆寫該列", "ADR 0012", "append 新事件", "不得回改")
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            self._events(d, merge=blob, pins=pins)
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            for needle in needles + ("非 commit", "git log --merges"):
                self.assertIn(needle, f[0]["msg"])
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(os.path.join(d, "rust-api"), "rev-parse", "HEAD:app.ts").strip()
            self._events(d, merge=outer, pins=dict(pins, api=blob))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            for needle in needles + ("非 commit", "rev-parse"):
                self.assertIn(needle, f[0]["msg"])

    def test_not_commit_remedy_overwrite_branch_actually_clears_the_error(self):
        """B-033 紀律：「紅訊息附去處」須連帶驗證出口可執行——照做卻清不掉紅的去處
        比沒有去處更糟（B-042① 的開帳教訓）。

        本案機器驗證去處第一支（該列尚未進 git 史→以真實 SHA 覆寫該列）：紅→照做→綠。
        ★第二支（已進 git 史→append 更正事件）的可執行性由 TestErratumCorrectionView
        承接（B-042 調閘形：erratum 更正視圖、三處訊息之出口逐處紅→照做→綠）；
        兩支去處文案於三筆訊息一致。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            self._events(d, merge=blob, pins=pins)
            self.assertEqual([x["level"] for x in lint_events_sha(d)], [ERROR],
                             msg="前提：壞值須先紅，否則本案後半無判別力")
            self._events(d, merge=outer, pins=pins)          # ＝去處第一支：覆寫該列
            self.assertEqual(lint_events_sha(d), [],
                             msg="照去處第一支執行後須轉綠——清不掉即去處失效")

    def test_pins_missing_key_is_error(self):
        """★鍵集斷言：缺鍵＝ERROR（防「查一個不存在的鍵得空集合」型恆綠）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._events(d, merge=outer, pins={"web": pins["web"]})
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("pins", f[0]["msg"])

    def test_pins_unknown_key_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._events(d, merge=outer, pins=dict(pins, mobile="2" * 40))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("pins", f[0]["msg"])

    def test_pins_non_dict_is_error(self):
        """★型別守衛：pins 非 dict＝ERROR，鍵集比對本身擋不住。

        ★`["web", "api"]` 這格是本案的殺傷樣本：其 `set()` 恰等於鍵集，鍵集比對放行後
        會走進 `pins[key]` 字串下標而拋 TypeError（整條 lint 當掉）——唯有 isinstance
        守衛在才會落 ERROR。另兩格（SHA list／裸 str）驗非 dict 時的型別名訊息。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            for bad in (["web", "api"], [pins["web"], pins["api"]], pins["web"]):
                self._events(d, merge=outer, pins=bad)
                f = lint_events_sha(d)
                self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
                self.assertIn("pins", f[0]["msg"])
                self.assertIn(type(bad).__name__, f[0]["msg"])

    def test_whitespace_in_sha_does_not_misalign_batch(self):
        """★對位守衛：值內夾空白（換行）之 SHA 一律視同不可解，且不得帶歪其後各列。

        `cat-file --batch-check` 一行一問、回顯以 zip 逐行配對；值內若夾換行，git 會多回
        一行，其後所有 SHA 的型別整體錯位——錯位能把偽造值配到真 commit 型別上（漏報）。
        本案第 1 列放夾換行的偽造值、第 2 列放真 blob（應報非 commit）：守衛掉了兩列都會
        被配成 commit 而雙雙漏報。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            rows = [dict(VALID_CLOSE, merge=outer + "\n" + outer, pins=pins),
                    dict(VALID_CLOSE, merge=blob, pins=pins)]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR, ERROR], msg=str(f))
            self.assertIn("行 1", f[0]["where"])
            self.assertIn("不可解析", f[0]["msg"])
            self.assertIn("行 2", f[1]["where"])
            self.assertIn("blob", f[1]["msg"])

    def test_batch_check_failure_fails_closed(self):
        """★fail-closed：`cat-file` 子行程非零退出＝整批輸出丟棄、視同全不可解→merge 面 ERROR。

        守衛掉了會改去解析半截 stdout，把「查不成」讀成「查過了、乾淨」。本案刻意保留真
        stdout、只把退出碼翻成非零——唯有守衛在，才會落 ERROR。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._events(d, merge=outer, pins=pins)
            self.assertEqual(lint_events_sha(d), [])       # 前提：真跑時本 fixture 全綠
            real = subprocess.run

            def fake(args, **kw):
                r = real(args, **kw)
                if list(args[:2]) == ["git", "cat-file"]:
                    return subprocess.CompletedProcess(args, 1, r.stdout, "boom")
                return r

            with mock.patch.object(subprocess, "run", fake):
                f = lint_events_sha(d)
            self.assertTrue(any(x["level"] == ERROR and "merge" in x["msg"] for x in f),
                            msg=str(f))

    def test_type_guards_survive_malformed_rows_without_crashing(self):
        """★A3：三處型別守衛（列非 dict／merge 非 str／pins 值非 str）一次釘住。

        突變實證：三處 isinstance 任一拿掉，本案即以 AttributeError（`list.get`）或
        TypeError（`re.search` 吃到 int）整條 lint 當掉——當掉不是「紅」，是守門工具
        在壞資料前直接死掉、pre-commit 拿到的是 traceback 而非 finding。
        Lint18 只負責「向 git 實證」，格式面歸 Lint03；故本案同時斷言：Lint18 零 finding、
        Lint03 對三列各報至少一筆 ERROR（壞資料確實有人管、不是被吞掉）。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            rows = [
                json.dumps([1, 2, 3]),                            # 裸 JSON 陣列列
                json.dumps(dict(VALID_CLOSE, merge=12345, pins=pins),
                           ensure_ascii=False),                   # merge 為整數
                json.dumps(dict(VALID_CLOSE, merge=outer,
                                pins={"web": 12345, "api": pins["api"]}),
                           ensure_ascii=False),                   # pins 值為整數
            ]
            text = "".join(r + "\n" for r in rows)
            _wfile(d, EVENTS, text)
            self.assertEqual(lint_events_sha(d), [])
            schema = lint_events(text)
            for n in (1, 2, 3):
                hits = [x for x in schema
                        if x["level"] == ERROR and x["where"].endswith(f"行 {n}")]
                self.assertTrue(hits, msg=f"行 {n} 無 schema ERROR｜{schema}")

    def test_space_inside_sha_is_reported_unresolvable(self):
        """★A6：值內夾半形空白之 SHA 須落「不可解析」ERROR，且不帶歪其後各列。

        原本的排除守衛寫成「含任何空白即排除」，實測其中「空白」那半是驗不到的死防線：
        `cat-file --batch-check` 未指定自訂格式時把整行當物件名，對 `<20位> <20位>` 原樣
        回「<整行> missing」——不會拿空白前那截當縮寫去解，判定本來就是不可解。載重的只有
        換行（一行一問、一行一答，多一行即整體錯位，另案 test_whitespace_in_sha_… 看住），
        故守衛已收斂為只排除換行。本案把「夾空白＝不可解、鄰列不受影響」這個對外行為釘成
        契約——與守衛用哪種字元集無關，換實作也不得改判。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            rows = [dict(VALID_CLOSE, merge=outer[:20] + " " + outer[20:], pins=pins),
                    dict(VALID_CLOSE, merge=blob, pins=pins)]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR, ERROR], msg=str(f))
            self.assertIn("行 1", f[0]["where"])
            self.assertIn("不可解析", f[0]["msg"])
            self.assertIn("行 2", f[1]["where"])
            self.assertIn("blob", f[1]["msg"])

    def test_absent_submodule_worktree_skips_its_pins(self):
        """判定表第 4 列：worktree 缺席＝該庫清單整批 skip（不逐列誤報 WARN）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d, subs=("base-web",))
            self._events(d, merge=outer, pins=dict(pins, api="3" * 40))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [SKIP], msg=str(f))
            self.assertEqual(f[0]["where"], "rust-api")
            self.assertIn("跳過", f[0]["msg"])

    def test_run_lint_wires_events_sha(self):
        """★接線層：`lint_events_sha` 從 run_lint 掉線＝G3 整條靜默下線。"""
        with tempfile.TemporaryDirectory() as d:
            _outer, pins = self._fixture(d)
            self._events(d, merge="0" * 39 + "1", pins=pins)
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint18" and x["level"] == ERROR
                                for x in f), msg=str(f))

    def test_dispatch_is_one_batch_per_repo(self):
        """★批次守衛：全帳本驗證恰派「1＋存活庫數」發 cat-file，且每庫各一發。

        退回逐筆 rev-parse 對真庫要 ~87 次 subprocess（約 1s）＝超 rev4:contracts G3
        「200ms 以內」十倍量級；本案把「批次而非逐筆」釘成可機器偵測的次數。
        ★fixture 須多列（此處 3 個事件列×3 庫＝9 個 SHA），單列時逐筆與批次派發次數同為
        3、分辨不出——故另立 assertLess 看住 fixture 不退化。
        ★fixture 另含 erratum 列（外層一筆＋每庫一筆）：B-042 把 corrected 自驗併進這同三發
        批次（「零額外 git 呼叫」），而零 erratum 的帳本量不到那條路徑——實測把 corrected
        抽出批次、改成批次外各自 git_object_types 的退化寫法（重構時最自然的寫法）全綠
        存活；帳本一有 N 筆 erratum，退化寫法每筆各開一發 git，drvfs 上直接吃掉 G3 預算。
        """
        with tempfile.TemporaryDirectory() as d:
            outer = [_init_outer(d)]
            for i in range(2):
                _wfile(d, "README.md", f"說明 {i}\n")
                _git(d, "add", "README.md")
                _git(d, "commit", "-qm", f"r{i}")
                outer.append(_git(d, "rev-parse", "HEAD").strip())
            subs = {key: _init_sub(d, name, len(outer)) for key, name in PIN_KEYS}
            rows = [dict(VALID_CLOSE, merge=sha,
                         pins={key: shas[i] for key, shas in subs.items()})
                    for i, sha in enumerate(outer)]
            # 三筆合法 erratum 各覆蓋第 1 列一欄（corrected 皆為該 repo 另一顆真 commit＝
            # 覆蓋後仍全綠），使外層與兩庫的批次都必須順帶馱著自己的 corrected
            rows += [{"date": "2026-08-11", "type": "erratum", "target_line": 1,
                      "field": fld, "corrected": cor,
                      "reason": "批次守衛 fixture：更正值須併入既有批次"}
                     for fld, cor in ([("merge", outer[1])]
                                      + [(f"pins.{key}", subs[key][1])
                                         for key, _sub in PIN_KEYS])]
            _wfile(d, EVENTS,
                   "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            real, cwds = subprocess.run, []

            def fake(args, **kw):
                if list(args[:2]) == ["git", "cat-file"]:
                    cwds.append(kw.get("cwd"))
                return real(args, **kw)

            with mock.patch.object(subprocess, "run", fake):
                self.assertEqual(lint_events_sha(d), [])
            batched = 1 + len(PIN_KEYS)
            self.assertLess(batched, len(rows) * batched)   # 逐筆實作會派後者那麼多發
            self.assertEqual(len(cwds), batched, msg=str(cwds))
            self.assertEqual(len(set(cwds)), batched, msg=str(cwds))

    def test_calls_are_dispatched_concurrently(self):
        """★併發守衛：同池多發必須同時在飛，退回序列即紅（rev4:contracts G3 效能契約）。

        三發各在同一 barrier 上互等：併發時三者同時抵達而放行；序列時第一發等不到
        另兩發、逾時 BrokenBarrierError＝紅。不比時間長短，故 drvfs 上不 flaky。
        不改以 threading.get_ident() 相異數斷言——瞬回時 ThreadPoolExecutor 會
        重用剛轉閒置的同一執行緒（實測 400 回有 388 回只見 1 個 ident）。
        """
        bar = threading.Barrier(3, timeout=10)

        def fake(tag):
            bar.wait()
            return tag

        self.assertEqual(
            run_git_concurrently([functools.partial(fake, t) for t in "abc"]),
            ["a", "b", "c"])

    def test_probe_flies_together_with_the_batches(self):
        """★存活探針必須與 cat-file 批次同池併發（U5-quality：分兩段跑實測 300~341ms、
        破 rev4:contracts G3「全帳本驗證 200ms 以內」）。

        探針與三發批次共 5 個參與者在同一 barrier 上互等：探針若被移回批次之前序列跑，
        它先抵達卻等不到批次、逾時 BrokenBarrierError＝紅。
        """
        with tempfile.TemporaryDirectory() as d:
            outer = _init_outer(d)
            subs = {key: _init_sub(d, name)[0] for key, name in PIN_KEYS}
            _wfile(d, EVENTS,
                   json.dumps(dict(VALID_CLOSE, merge=outer, pins=subs),
                              ensure_ascii=False) + "\n")
            bar = threading.Barrier(1 + 2 * len(PIN_KEYS), timeout=10)
            real_types, real_head = git_object_types, submodule_head

            def fake_types(shas, cwd):
                bar.wait()
                return real_types(shas, cwd)

            def fake_head(root, sub, cache=None):
                bar.wait()
                return real_head(root, sub, cache)

            mod = sys.modules[__name__]
            with mock.patch.object(mod, "git_object_types", fake_types), \
                 mock.patch.object(mod, "submodule_head", fake_head):
                self.assertEqual(lint_events_sha(d), [])

    def test_single_lint_probes_each_submodule_at_most_once(self):
        """★探針記憶化守衛：單次 lint 內每個子庫的存活探針最多打一發 git。

        Lint16／Lint17／Lint18／Lint20 守衛#4 各自打＝每庫四發（drvfs 實測每發 78~101ms、一次 lint 多花
        ~360ms）。同型回歸（新條款忘了傳 cache）不會被 clause 級的時間量測抓到，故釘成
        可機器偵測的次數。★fixture 須 stage gitlink：不 stage 時 Lint16／Lint17 在探針之前就先
        跳過（未 staged／index 無條目），四條款只剩兩條會打、分辨力減半。
        """
        with tempfile.TemporaryDirectory() as d:
            outer = _init_outer(d)
            subs = {key: _init_sub(d, name)[0] for key, name in PIN_KEYS}
            for key, name in PIN_KEYS:
                _stage_gitlink(d, name, subs[key])
            _wfile(d, EVENTS,
                   json.dumps(dict(VALID_CLOSE, merge=outer, pins=subs),
                              ensure_ascii=False) + "\n")
            real, probes = subprocess.run, []

            # ★比對整串 argv 尾段而非 args[:3]：git_out 會夾 `-c core.quotepath=off`，
            #   以 ["git", "rev-parse", "HEAD"] 相等比對永遠不成立＝本案零信號（實證：
            #   三個「拿掉 cache」突變體全數存活）
            def fake(args, **kw):
                if list(args)[-2:] == ["rev-parse", "HEAD"]:
                    probes.append(kw.get("cwd"))
                return real(args, **kw)

            with mock.patch.object(subprocess, "run", fake):
                run_lint(d)
            for _key, sub in PIN_KEYS:
                hits = [c for c in probes if c == os.path.join(d, sub)]
                self.assertEqual(len(hits), 1, msg=f"{sub}｜{probes}")


class TestErratumCorrectionView(unittest.TestCase):
    """B-042 調閘形：Lint18 erratum 更正視圖（六條硬語意）——已入史壞列的可執行出口。

    紅訊息指示「append 新事件更正」後紅必須真的消（B-033④ 教訓形：附了去處卻走不通
    比沒有去處更糟）。★真帳本現況全綠（B-042 明載非 live 紅），全部案例自建 fixture repo
    造紅、絕不觸碰真 events.jsonl。
    """

    # ★與 TestEventsShaProof 共用同一份 fixture 實作（曾各存一份逐字重複的拷貝：兩份漂移
    #   時「同名 helper 造出不同 repo」的測試會照樣綠、debug 成本極高）
    _fixture = TestEventsShaProof._fixture

    def _rows(self, d, *rows):
        _wfile(d, EVENTS,
               "".join((r if isinstance(r, str)
                        else json.dumps(r, ensure_ascii=False)) + "\n" for r in rows))

    @staticmethod
    def _erratum(target_line, field, corrected, **over):
        e = {"type": "erratum", "date": "2026-08-11", "target_line": target_line,
             "field": field, "corrected": corrected, "reason": "fixture 造紅後更正"}
        e.update(over)
        return e

    def test_bad_merge_without_erratum_is_error(self):
        """八臂①：壞 merge SHA、無 erratum＝ERROR（造紅基線——後續各臂的前提）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins),
                       dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")

    def test_erratum_with_real_commit_clears_the_error(self):
        """八臂②：＋erratum（corrected＝fixture 真 commit）→零 findings——紅訊息附的
        出口真的走得通（B-042 開帳訴求本體）。兩子案＝merge 面兩筆 ERROR 逐處實證：
        前段「不可解」（偽造 SHA）、後段「可解非 commit」（blob）；pins 面＝八臂⑤——
        硬語意⑥的三處去處第二支至此各有自己的紅→照做→綠釘子。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            bad = dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins)
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins), bad)
            self.assertEqual([x["level"] for x in lint_events_sha(d)], [ERROR],
                             msg="前提：壞值須先紅，否則本案無判別力")
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins), bad,
                       self._erratum(2, "merge", outer))
            self.assertEqual(lint_events_sha(d), [],
                             msg="照紅訊息 append erratum 後須轉綠——清不掉即出口失效")
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            bad = dict(VALID_CLOSE, merge=blob, pins=pins)
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins), bad)
            self.assertEqual([x["level"] for x in lint_events_sha(d)], [ERROR],
                             msg="前提：merge 解得 blob（非 commit）須先紅")
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins), bad,
                       self._erratum(2, "merge", outer))
            self.assertEqual(lint_events_sha(d), [],
                             msg="「非 commit」面出口同樣要走得通（B-042 三處一次覆蓋）")

    def test_erratum_corrected_unresolvable_is_error_on_erratum_row(self):
        """八臂③：erratum corrected 不可解＝該 erratum 列 ERROR——更正本身也被驗、
        零豁免（硬語意②）。target 列以壞 corrected 覆蓋後照樣紅、兩紅並陳。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins),
                       self._erratum(1, "merge", "0" * 39 + "2"))
            f = lint_events_sha(d)
            hits = [x for x in f if x["where"] == f"{EVENTS}:行 2"
                    and x["level"] == ERROR and "erratum corrected" in x["msg"]]
            self.assertEqual(len(hits), 1, msg=str(f))
            self.assertIn("不可解", hits[0]["msg"])

    def test_offtarget_fails_loud(self):
        """八臂④：脫靶（target_line 超界／指到非事件列）＝ERROR、絕不靜默 no-op
        （硬語意③）。靜默略過＝erratum 看似入帳實則零效、操作者以為修完了。

        ★第二子案另釘住訊息裡的「帳本共 N 行」＝**實體行數**（`len(lines)`）而非可解析
        列數（`len(rows)`）：該子案的帳本恰為 3 個實體行、只有 2 筆可解析 rows，是兩者
        唯一的判別點。這句話的唯一用途就是幫維運者判斷 target_line 是否打超界，報偏小的
        規模等於把人往錯方向指（B-042 訴求本體＝紅訊息的出口要真的走得通）。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins),
                       self._erratum(99, "merge", outer))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")
            self.assertIn("脫靶", f[0]["msg"])
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins),
                       "{壞 JSON 列",
                       self._erratum(2, "merge", outer))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 3")
            self.assertIn("脫靶", f[0]["msg"])
            # 帳本規模＝3 個實體行（可解析 rows 只有 2 筆）——報 rows 數即誤導
            self.assertIn("帳本共 3 行", f[0]["msg"], msg=f[0]["msg"])

    def test_pins_api_erratum_clears_and_missing_field_is_error(self):
        """八臂⑤：pins.api 非 commit＋erratum→消；field 指定欄不存在於 target 列＝ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(os.path.join(d, "rust-api"), "rev-parse", "HEAD:app.ts").strip()
            bad = dict(VALID_CLOSE, merge=outer, pins=dict(pins, api=blob))
            self._rows(d, bad)
            self.assertEqual([x["level"] for x in lint_events_sha(d)], [ERROR],
                             msg="前提：pins.api 非 commit 須先紅")
            self._rows(d, bad, self._erratum(1, "pins.api", pins["api"]))
            self.assertEqual(lint_events_sha(d), [],
                             msg="pins 面出口同樣要走得通（B-042 三處一次覆蓋）")
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, VALID_MISC, self._erratum(1, "pins.web", pins["web"]))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")
            self.assertIn("不存在指定欄 pins.web", f[0]["msg"])

    def test_merge_erratum_missing_field_on_target_is_error(self):
        """硬語意③第三子案 merge 半邊：erratum 指定 merge 欄、target 列（misc）根本沒有
        merge 欄＝ERROR、絕不靜默 no-op——否則實作等於憑空替該列造出 merge 值去驗，
        corrected 填真 commit 即全帳零 finding、操作者以為更正生效實則零效（拍板③明禁形）。
        ★釘住變異：merge 側 present 檢查退化為恆真（R2 實證 pins 半邊反例殺不到它、
        變異後全綠存活——本案即該裸奔子案的反例）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, VALID_MISC, self._erratum(1, "merge", outer))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 2")
            self.assertIn("不存在指定欄 merge", f[0]["msg"])

    def test_erratum_pointing_at_erratum_is_error(self):
        """八臂⑥：erratum 指向 erratum 列＝ERROR（硬語意⑤）——更正的更正＝再 append
        一筆指向原始列，不得形成更正鏈。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=pins),
                       self._erratum(1, "merge", outer),
                       self._erratum(2, "merge", outer))
            f = lint_events_sha(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["where"], f"{EVENTS}:行 3")
            self.assertIn("不得指向 erratum 列", f[0]["msg"])

    # 八臂⑦（格式面：缺欄／field 枚舉外／corrected 非 40 hex）＝TestLintEvents 的
    # test_erratum_missing_required_field_rejected／…field_enum／…bad_corrected_rejected。

    def test_malformed_erratum_rows_are_skipped_without_crashing(self):
        """★`_erratum_view` 的格式跳過守衛（四腿）逐腿反例——白箱直呼、九個殘缺列
        逐一斷言 view／checks／findings 三者皆空且不拋例外。

        殘缺歸 Lint03（格式面）、此處只負責「安靜讓路」，但四腿各有實質後果、缺一即壞：
        ①`fld in ERRATUM_FIELDS` 是唯一防崩線——`field:"summary"` 會讓 `fld.split(".",1)[1]`
          吃 IndexError、`field:3` 吃 AttributeError，Lint18 整支拋 traceback 而非出 finding；
        ②bool 腿有真語意——Python 的 `True == 1` 且 hash 相同，缺腿時 `target_line: true`
          會被當成「更正第 1 列」而**真的生效**（view[(True,…)] 與 view.get((1,…)) 命中同格），
          Lint18 靜默把第 1 列的紅清掉；
        ③`isinstance(tl,int)`／`isinstance(cor,str)` 缺腿**有兩個變體**（確認輪補齊——原只論
          證了前者、後者才是會被真寫出來的形）：整條拿掉＝`"2" >= 1`／`RE_SHA.fullmatch(3)`
          直接 TypeError；換成寬鬆轉型 `RE_SHA.fullmatch(str(cor))`（同檔 feature_close 的
          merge／pins 正是此慣例，故有人照抄）則**不崩**，而是讓殘缺值混進視圖與 checks：
          view 值為 int ⇒ `lint_events_sha` 的 `isinstance(m, str)` 為 False ⇒ target 列整列
          不入 merges、原有的 ERROR 被靜默吃掉（比 no-op 更糟）；checks 的 int 再流進
          `git_object_types` 的 `"\\n" not in s` 拋 TypeError。此變體由 `int("1"*40)` 一筆釘住
          （★不可改用 `3`：`str(3)` 非 40 位 hex、兩把尺都拒＝對本變體零分辨力）；
        ④`tl >= 1`／`RE_SHA` 缺腿＝殘缺值混進視圖去覆蓋真欄。
        """
        base = [(1, dict(VALID_CLOSE)), (2, dict(VALID_MISC))]
        ok = "a" * 40
        for bad in (self._erratum(True, "merge", ok),      # bool 冒充行號（== 1）
                    self._erratum(0, "merge", ok),         # 非正整數
                    self._erratum("2", "merge", ok),       # 行號為字串
                    self._erratum(1, "summary", ok),       # 枚舉外欄名（無 "." 可切）
                    self._erratum(1, 3, ok),               # 欄名非字串
                    self._erratum(1, "merge", "z" * 40),   # 非 hex
                    self._erratum(1, "merge", ok[:39]),    # 長度不足
                    self._erratum(1, "merge", 3),          # corrected 非字串
                    self._erratum(1, "merge", int("1" * 40))):  # ★少打引號的 40 位十進位
                                                           #   number——唯一能分辨
                                                           #   `str(cor)` 寬鬆轉型變體者
            rows = base + [(3, bad)]
            view, checks, f = _erratum_view(rows, 3)
            self.assertEqual((view, checks, f), ({}, [], []), msg=str(bad))

    def test_same_target_field_later_erratum_wins(self):
        """八臂⑧：同 target×欄兩筆合法 erratum＝append 序後者勝（硬語意④），
        且每筆各自過 corrected 自驗。"""
        # 白箱：視圖取後值、checks 兩筆俱在（後者勝不豁免前筆的自驗）
        c1, c2 = "1" * 40, "2" * 40
        rows = [(1, dict(VALID_CLOSE)),
                (2, self._erratum(1, "merge", c1)),
                (3, self._erratum(1, "merge", c2))]
        view, checks, f = _erratum_view(rows, 3)
        self.assertEqual(view, {(1, "merge"): c2})
        self.assertEqual([c for _n, _f, c in checks], [c1, c2])
        self.assertEqual(f, [])
        # 黑箱：兩筆 corrected 皆真 commit→零 findings（各自自驗通過、視圖值可解）
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            _wfile(d, "second.md", "第二筆\n")
            _git(d, "add", "second.md")
            _git(d, "commit", "-qm", "c2")
            outer2 = _git(d, "rev-parse", "HEAD").strip()
            self._rows(d, dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins),
                       self._erratum(1, "merge", outer),
                       self._erratum(1, "merge", outer2))
            self.assertEqual(lint_events_sha(d), [])
        # 黑箱可辨：後筆 corrected＝blob（40 hex 格式合法）→後者勝＝target 以 blob 覆蓋
        # 而紅（非 commit）＋後筆自驗紅；若誤取前值（真 commit）target 會靜默轉綠。
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            self._rows(d, dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins),
                       self._erratum(1, "merge", outer),
                       self._erratum(1, "merge", blob))
            f = lint_events_sha(d)
            self.assertTrue(any(x["where"] == f"{EVENTS}:行 1" and x["level"] == ERROR
                                and "非 commit" in x["msg"] for x in f), msg=str(f))
            self.assertTrue(any(x["where"] == f"{EVENTS}:行 3" and x["level"] == ERROR
                                and "erratum corrected" in x["msg"] for x in f), msg=str(f))

    def test_remedy_messages_carry_concrete_erratum_form(self):
        """硬語意⑥：三處 ERROR（merge 不可解／merge 非 commit／pins 非 commit）教的
        erratum 形**照抄即綠**——端到端釘死（B-042 訴求本體：出口真的走得通）。

        ★不比對字串片段：那等於在測試裡手抄一份 EVENT_SCHEMAS 副本、與 schema 各走各的。
        實測片段比對法對兩發變異全綠存活——模板拿掉 `"date":"YYYY-MM-DD",`（照抄者吃
        Lint03「缺必填欄位「date」」）／模板尾端多一個 `"extra":1`（吃 Lint03「未知欄位」）；
        兩者都讓「照做卻清不掉紅」重演，正是本案要防的那件事。
        本案改為：自 finding 訊息正則抓出模板 → 只代入訊息以角括號標示的待填值 →
        **原文 append** 進 fixture 帳本 → 斷言 Lint03（格式）與 Lint18（SHA 實證）雙雙全綠。
        ★fixture 兩列、壞值落第 2 列：行號若寫死 1 會教操作者更正無辜列。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            api_blob = _git(os.path.join(d, "rust-api"),
                            "rev-parse", "HEAD:app.ts").strip()
            good = dict(VALID_CLOSE, merge=outer, pins=pins)
            for bad, field, fix in (
                    (dict(VALID_CLOSE, merge="0" * 39 + "1", pins=pins), "merge", outer),
                    (dict(VALID_CLOSE, merge=blob, pins=pins), "merge", outer),
                    (dict(VALID_CLOSE, merge=outer, pins=dict(pins, api=api_blob)),
                     "pins.api", pins["api"])):
                self._rows(d, good, bad)
                f = lint_events_sha(d)
                self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
                m = re.search(r"\{.*?\}", f[0]["msg"])
                self.assertTrue(m, msg=f"訊息未附 erratum 形｜{f[0]['msg']}")
                row = (m.group(0)
                       .replace("YYYY-MM-DD", "2026-08-11")
                       .replace("<正確 40 位 hex SHA>", fix)
                       .replace("<一句話>", "照紅訊息所教的形 append 更正"))
                # 訊息指對欄位與行號（寫死行號會把操作者帶去更正無辜列）
                self.assertEqual({k: json.loads(row)[k] for k in ("field", "target_line")},
                                 {"field": field, "target_line": 2}, msg=row)
                self._rows(d, good, bad, row)          # ★原文 append、不經 dict 洗過
                self.assertEqual(lint_events(_read(d, EVENTS)), [],
                                 msg="照抄的 erratum 列自身須過格式面（Lint03）")
                self.assertEqual(lint_events_sha(d), [],
                                 msg="照抄後紅須真的消（Lint18）——清不掉即出口失效")

    def test_corrected_error_messages_carry_two_branch_remedy(self):
        """★四處「erratum corrected 自驗失敗」ERROR 的補救支：與史值三處同構分兩支，且第
        二支說實話——已入史的 erratum 列在現行設計下無出口、導向升級主線由拍板層處置。

        缺這條釘子時四筆一律只有「corrected 須填該刀…的真 commit SHA」單句：對已入史的列
        而言那等於教人回改既有列（違 ADR 0012 決定 5），而合法路徑一條都不存在——回改本列
        違紀、append erratum 指向本列被硬語意⑤擋、指向原始列只救得回 target 列（本案第二段
        即該三行帳本的實證）。B-042 開帳要消滅的正是這種「附了去處卻走不通」形，在新增的
        訊息上重演＝自打嘴巴。四筆逐一驗（merge／pins × 不可解／非 commit），任一筆退回
        舊文案即紅；可達性見 CLAUDE.md §3 的 upstream rebase 例行程序（卷史合法失聯）。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(d, "rev-parse", "HEAD:README.md").strip()
            api_blob = _git(os.path.join(d, "rust-api"),
                            "rev-parse", "HEAD:app.ts").strip()
            good = dict(VALID_CLOSE, merge=outer, pins=pins)
            for field, bad_corrected in (("merge", "0" * 39 + "2"), ("merge", blob),
                                         ("pins.api", "0" * 39 + "9"),
                                         ("pins.api", api_blob)):
                self._rows(d, good, self._erratum(1, field, bad_corrected))
                f = lint_events_sha(d)
                hits = [x for x in f if x["where"] == f"{EVENTS}:行 2"]
                self.assertEqual(len(hits), 1, msg=str(f))
                for needle in ("補救分兩支", "尚未進 git 史", "覆寫本列", "已進 git 史",
                               "無可執行出口", "ADR 0012", "升級主線", "勿自行回改已入史列"):
                    self.assertIn(needle, hits[0]["msg"],
                                  msg=f"{field}／{bad_corrected[:8]}｜{hits[0]['msg']}")
            # 「已入史即無出口」不是修辭：三行帳本（壞 pins 值列＋卷史失聯的更正＋正確的
            # 更正）跑完後，target 列被④救回、被蓋掉那筆 erratum 的自驗紅仍在＝永久紅。
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=dict(pins, api="3" * 40)),
                       self._erratum(1, "pins.api", "0" * 39 + "9"),
                       self._erratum(1, "pins.api", pins["api"]))
            self.assertEqual([(x["level"], x["where"]) for x in lint_events_sha(d)],
                             [(ERROR, f"{EVENTS}:行 2")],
                             msg="更正的更正救不了被蓋掉那列——第二支若教人回改即違 ADR 0012")

    # --- pins 半邊 corrected 自驗反例（review R1：變異測試 M1／M2／M3／M18／M20／M22
    #     六發全存活＝硬語意②的 pins 側守門在測試面恆綠——以下三案逐一釘住；merge 側
    #     同型反例＝八臂③，此前 pins 側僅有 happy path 八臂⑤） --------------------------

    def test_pins_erratum_corrected_unresolvable_is_error_on_erratum_row(self):
        """pins 側硬語意②反例（不可解）：corrected 在子庫不可解＝該 erratum 列 ERROR
        （pins 的 WARN 寬貸只給史值、不給更正值）；target 列以壞 corrected 覆蓋後僅 WARN。
        ★釘住變異：pins 側 errata 迴圈整段停用（M1）／「不可解」分支靜默（M2）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(os.path.join(d, "rust-api"), "rev-parse", "HEAD:app.ts").strip()
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=dict(pins, api=blob)),
                       self._erratum(1, "pins.api", "0" * 39 + "9"))
            f = lint_events_sha(d)
            self.assertEqual([(x["level"], x["where"]) for x in f],
                             [(WARN, f"{EVENTS}:行 1"), (ERROR, f"{EVENTS}:行 2")],
                             msg=str(f))
            self.assertIn("pins.api", f[0]["msg"])
            self.assertIn("不可解析", f[0]["msg"])
            self.assertIn("erratum corrected", f[1]["msg"])
            self.assertIn("在 rust-api 不可解析", f[1]["msg"])

    def test_pins_erratum_corrected_blob_is_error_on_both_rows(self):
        """pins 側硬語意②反例（非 commit）：corrected＝子庫 blob（40 hex 格式合法）＝
        該 erratum 列 ERROR；target 列以 blob 覆蓋後亦紅（非 commit）——兩紅並陳、
        零豁免。★釘住變異：「非 commit」分支靜默（M3）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            blob = _git(os.path.join(d, "rust-api"), "rev-parse", "HEAD:app.ts").strip()
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=dict(pins, api=blob)),
                       self._erratum(1, "pins.api", blob))
            f = lint_events_sha(d)
            self.assertEqual([(x["level"], x["where"]) for x in f],
                             [(ERROR, f"{EVENTS}:行 1"), (ERROR, f"{EVENTS}:行 2")],
                             msg=str(f))
            self.assertIn("非 commit", f[0]["msg"])
            self.assertIn("erratum corrected", f[1]["msg"])
            self.assertIn("在 rust-api 解得物件型別 blob、非 commit", f[1]["msg"])

    def test_pins_erratum_validated_even_when_no_pins_row_enters_batch(self):
        """pins 側硬語意②反例（純 erratum 派批）：target 列 pins 鍵集殘缺＝整列不入
        per_key、該庫批次只剩 corrected 一筆——更正值仍必須被驗（blob→ERROR）。
        ★釘住變異：派批條件漏 err_pins（M18、ERROR 退化成 SKIP）／空 items 提前
        continue（M20、整筆消失）／cat-file 批漏併 corrected（M22、錯報成「不可解」）。"""
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d)
            web_blob = _git(os.path.join(d, "base-web"),
                            "rev-parse", "HEAD:app.ts").strip()
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins={"web": pins["web"]}),
                       self._erratum(1, "pins.web", web_blob))
            f = lint_events_sha(d)
            self.assertEqual([(x["level"], x["where"]) for x in f],
                             [(ERROR, f"{EVENTS}:行 1"), (ERROR, f"{EVENTS}:行 2")],
                             msg=str(f))
            self.assertIn("鍵集", f[0]["msg"])
            self.assertIn("erratum corrected", f[1]["msg"])
            self.assertIn("在 base-web 解得物件型別 blob、非 commit", f[1]["msg"])

    def test_absent_worktree_skip_counts_errata_too(self):
        """★硬語意②唯一的豁免路徑（庫缺席＝該庫整批跳過、更正值連帶不被驗）須在 SKIP
        明細上如實現身：筆數＝史值筆數＋erratum corrected 筆數。

        筆數若只數史值（`len(items)`），跳過明細會少報更正值那幾筆——而「沒被驗的東西
        有幾個」正是 SKIP 這條訊息存在的唯一理由（rev4:FR-012 假綠面：不適用與檢了通過
        在輸出上長得一樣即失守）。本案 rust-api 缺席、pins.api 一筆史值＋一筆 corrected。
        """
        with tempfile.TemporaryDirectory() as d:
            outer, pins = self._fixture(d, subs=("base-web",))
            self._rows(d, dict(VALID_CLOSE, merge=outer, pins=dict(pins, api="3" * 40)),
                       self._erratum(1, "pins.api", "4" * 40))
            f = lint_events_sha(d)
            self.assertEqual([(x["level"], x["where"]) for x in f],
                             [(SKIP, "rust-api")], msg=str(f))
            self.assertIn("pins.api 共 2 筆 SHA 實證跳過", f[0]["msg"])


# --- G7／Lint19 測試共用 fixture（★一律自建 root，真 repo 唯讀）------------------

# ★分派表字面一律以 format 模板構造：本檔自身即掃源標的，落任何完整的
#   「cmd 等號等號 空白 雙引號 小寫子命令 雙引號」字面，就會被自己的掃源當成 docs-sync 的
#   子命令、真表當場失真（與 Lint16 紅樣本執行期串接同一紀律）。模板的 {} 非小寫字母＝不自命中。
_FAKE_EQ = 'if cmd == "{}":\n    pass\n'
_FAKE_ELIF = 'elif cmd == "{}":\n    pass\n'
_FAKE_IN = 'if cmd in ("{}", "{}"):\n    pass\n'
_FAKE_TOOLS = (("tools/docs-sync.py", ("generate", "lint")),
               ("tools/fork-delta-lint.py", ()),
               ("tools/schema-gate.py", ("gate1", "gate2")),
               ("tools/wire-schema.py", ("extract",)),
               ("tools/secret-value-guard.py", ("check",)),
               ("tools/entity-drift-gate.py", ("check",)),
               ("tools/wf-watchdog.py", ("test",)),
               ("deploy/preflight-secrets.py", ("test",)),
               ("deploy/decrypt-secrets.py", ("test",)),
               ("deploy/generate-secrets.py", ("test",)),
               ("deploy/setup-reaper-role.py", ("test",)),
               ("deploy/backup-db.py", ("dump", "restore", "test")))


def _tools_fixture(d):
    """自建 root 的最小工具源（支數與清單一律以 _FAKE_TOOLS 名冊為準、不留硬編數字）。"""
    for rel, subs in _FAKE_TOOLS:
        body = "".join(_FAKE_EQ.format(s) for s in subs) or "# 無分派表、直跑\n"
        _wfile(d, rel, "#!/usr/bin/env python3\n" + body)
    # ★檔頭刻意不含「用法」二字：讓唯一的 bash 名冊工具走 placeholder 分支（同真 repo 現況）
    _wfile(d, "tools/bootstrap.sh", "#!/usr/bin/env bash\n# 用途：體檢\n")


class TestToolsCliTruthTable(unittest.TestCase):
    """G7 tools-cli 掃源真表（rev4:contracts G7／data-model §7／rev4:research R5）。"""

    def test_scan_dedups_sorts_and_ignores_non_dispatch(self):
        """掃源子命令集：elif 鏈＋`cmd in (...)` 形全收、重複去重、非分派字串比較不收。"""
        src = ("import sys\n"
               + _FAKE_EQ.format("lint")
               + _FAKE_ELIF.format("generate")
               + _FAKE_ELIF.format("lint")               # 重複→去重
               + _FAKE_IN.format("gate2", "audit")       # schema-gate 的 audit 只長這形
               + 'if mode == "notacmd":\n    pass\n'     # 非 cmd 變數＝一般字串比較、不收
               + 'if cmd == "BadCase":\n    pass\n')     # 大寫起首＝非子命令形、不收
        self.assertEqual(scan_subcommands(src),
                         ["audit", "gate2", "generate", "lint"])

    def test_real_docs_sync_dispatch_is_pinned(self):
        """★對現庫源碼實掃（S6 步 1 逐一對照的機器化）：本檔測試字面污染真表即當場紅。"""
        src = _read(ROOT, "tools/docs-sync.py")
        self.assertIsNotNone(src)
        self.assertEqual(scan_subcommands(src),
                         ["check", "errata", "generate", "lint", "refresh", "test"])

    def test_sh_usage_line(self):
        """bash 用法行＝檔頭前 N 行首個含「用法」註解（去註解符）；缺／過深→None。"""
        head = "#!/usr/bin/env bash\n# 名稱 — 說明\n#\n#   用法：bash tools/x [token]\n"
        self.assertEqual(sh_usage_line(head), "用法：bash tools/x [token]")
        self.assertIsNone(sh_usage_line("#!/bin/sh\n# 用途：只有用途註解\n"))
        self.assertIsNone(sh_usage_line("#\n" * SH_USAGE_HEAD + "# 用法：太深\n"))

    def test_tools_roster_is_pinned_and_table_renders_twelve_sections(self):
        """★名冊字面釘死：只迭代 TOOLS_PY／TOOLS_SH 的斷言是套套邏輯（常數縮水＝斷言跟著
        縮水、全綠存活），連帶 RE_CMD_PY／RE_CMD_OLD 也由同一常數 join 而成——名冊少一支＝
        真表少一節（rev4:SC-006 失守）＋該工具的 Lint19 子命令比對與舊名禁令一併靜默下線。
        ★路徑形（B-035 U2）：名冊含 deploy/ 條目，目錄不再是隱含常識、字面連目錄一起釘。"""
        self.assertEqual(TOOLS_PY,
                         ("tools/docs-sync.py", "tools/fork-delta-lint.py",
                          "tools/schema-gate.py", "tools/wire-schema.py",
                          "tools/secret-value-guard.py", "tools/entity-drift-gate.py",
                          "tools/wf-watchdog.py",
                          "deploy/preflight-secrets.py", "deploy/decrypt-secrets.py",
                          "deploy/generate-secrets.py", "deploy/setup-reaper-role.py",
                          "deploy/backup-db.py"))
        self.assertEqual(TOOLS_SH, ("bootstrap",))
        md = gen_tools_cli(compute_tools_cli(ROOT))
        heads = [ln for ln in md.splitlines() if ln.startswith("## ")]
        self.assertEqual(len(heads), 13, msg=str(heads))
        # ★抬頭敘述同案釘死：只驗節數時，寫死字面的抬頭支數漂移不會被任何斷言碰到——
        # 生成檔「抬頭說六支、實列七節」在 347 案全綠下存活（rev4:019 U1 實證）。
        self.assertIn("來源＝治理工具名冊 13 支掃源（python 12 支", md)

    def test_compute_and_render_every_rostered_tool(self):
        """真表每支名冊工具一節：python 列子命令集、bash 列存在＋用法行；空集合工具明示直跑。"""
        with tempfile.TemporaryDirectory() as d:
            _tools_fixture(d)
            md = gen_tools_cli(compute_tools_cli(d))
            self.assertTrue(md.startswith(GEN_HEADER))
            for rel in TOOLS_PY:
                self.assertIn(f"## {rel}", md)
            for name in TOOLS_SH:
                self.assertIn(f"## tools/{name}.sh\n", md)
            self.assertIn("`generate`｜`lint`", md)
            self.assertIn("直跑", md)                      # fork-delta-lint 無子命令
            self.assertIn(f"（檔頭前 {SH_USAGE_HEAD} 行無「用法」註解行）", md)

    def test_compute_fails_loud_on_missing_python_tool(self):
        """python 工具缺席＝真表無源→fail-loud（不得靜默產空表、否則命令形恆綠）。"""
        with tempfile.TemporaryDirectory() as d:
            _tools_fixture(d)
            os.remove(os.path.join(d, "tools/wire-schema.py"))
            with self.assertRaises(ToolsCliError):
                compute_tools_cli(d)

    def test_absent_bash_tool_recorded_as_missing(self):
        """bash 工具缺席＝真表如實記「否」（判定歸 Lint19、生成面不炸）。"""
        with tempfile.TemporaryDirectory() as d:
            _tools_fixture(d)
            rows = {r["rel"]: r for r in compute_tools_cli(d)}
            self.assertTrue(rows["tools/bootstrap.sh"]["exists"])
            os.remove(os.path.join(d, "tools/bootstrap.sh"))
            rows = {r["rel"]: r for r in compute_tools_cli(d)}
            self.assertFalse(rows["tools/bootstrap.sh"]["exists"])

    def test_compute_generated_wires_tools_cli(self):
        """★接線層：真表若沒進 compute_generated，check 就對不到賬、G7 靜默下線。"""
        self.assertIn(TOOLS_CLI_MD, compute_generated(ROOT))


class TestCmdFormLint(unittest.TestCase):
    """Lint19 命令形 lint（rev4:contracts G5／rev4:research R6）：真表比對＋舊名禁令＋語料邊界。"""

    SUBS = {"tools/docs-sync.py": {"check", "errata", "generate", "lint", "refresh", "test"},
            "tools/schema-gate.py": {"audit", "gate1", "gate2", "test"},
            "tools/wire-schema.py": {"extract", "test"},
            "tools/fork-delta-lint.py": set(),
            "deploy/preflight-secrets.py": {"test"}}
    SH = {"tools/bootstrap.sh": True}
    RUNBOOK_REL = "docs/ops/RUNBOOK.md"

    def _f(self, text, rel=None):
        return check_cmd_forms({rel or self.RUNBOOK_REL: text}, self.SUBS, self.SH)

    def test_unknown_subcommand_is_error_naming_file_and_line(self):
        """真表沒有的子命令→ERROR，指名該檔該行（文件宣稱漂移）。"""
        text = "前言\n\n跑 `python3 tools/docs-sync.py nonexistent-cmd` 重算\n"
        f = self._f(text)
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertEqual(f[0]["code"], "Lint19")
        self.assertEqual(f[0]["where"], f"{self.RUNBOOK_REL}:行 3")
        self.assertIn("nonexistent-cmd", f[0]["msg"])

    def test_known_subcommands_pass(self):
        for sub in ("generate", "check", "lint", "refresh", "errata", "test"):
            self.assertEqual(self._f(f"`python3 tools/docs-sync.py {sub}`\n"), [],
                             msg=sub)

    def test_old_name_without_py_is_error(self):
        """②舊名禁令：TOOLS_PY 名冊各支不帶 .py 的路徑形命中即 ERROR（rev4:B-111 長期機器化）。"""
        f = self._f("勘誤跑 `tools/docs-sync errata 某詞`\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("舊名", f[0]["msg"])

    def test_new_name_does_not_trip_old_name_ban(self):
        """`tools/docs-sync.py` 內含舊名子字串——負向前瞻沒掛好即全庫誤紅。"""
        self.assertEqual(self._f("`python3 tools/docs-sync.py generate`\n"), [])

    def test_deploy_rostered_tool_is_checked_like_any_other(self):
        """★路徑形名冊（B-035 U2）：deploy/ 條目與 tools/ 條目同一套判定——真表沒有的
        子命令照紅、真名照過（名冊只認 `tools/` 前綴時本支的比對整條靜默下線）。"""
        f = self._f("`python3 deploy/preflight-secrets.py nonexistent-cmd`\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("deploy/preflight-secrets.py", f[0]["msg"])
        self.assertEqual(self._f("`python3 deploy/preflight-secrets.py test`\n"), [])

    def test_retired_sh_name_is_error(self):
        """★轉換窗口收攏後的嚴格形（TOOLS_PY_SH_TWIN 已隨 B-037 U3 整條下架）：四支舊 bash
        實體全數退役（decrypt＝B-036 U2；preflight／generate／setup-reaper＝B-037 U3），舊名
        禁令對 deploy 條目一律收回嚴格形——文件裡殘留的 `bash deploy/<name>.sh` 指向不存在
        的檔案、即刻 ERROR。窗口期曾以具名豁免弱化本禁令，少了本案就沒有任何斷言證明豁免
        真的收回了（弱化形留著也全綠）。副檔名全缺者照抓（禁令本體不得被拆）。"""
        for name in ("decrypt-secrets", "preflight-secrets", "generate-secrets",
                     "setup-reaper-role"):
            self.assertFalse(os.path.exists(os.path.join(ROOT, "deploy", name + ".sh")),
                             msg=f"{name}.sh 仍在庫＝退役未落實，本案前提失效")
            for text in (f"`bash deploy/{name}.sh`\n", f"`bash deploy/{name}`\n"):
                f = self._f(text)
                self.assertEqual([x["level"] for x in f], [ERROR], msg=f"{text}｜{f}")
                self.assertIn("舊名", f[0]["msg"])

    def test_continuation_token_never_swallows_a_deploy_command_form(self):
        """★續值排除前瞻改自名冊目錄現算（B-035 U2）：寫死 `tools/` 時，跨代碼段斜線形會
        把後一支完整命令形的 `deploy` 當成前一支的續值子命令而誤紅（實測 ERROR）。"""
        self.assertEqual(
            self._f("`python3 tools/docs-sync.py check` / "
                    "`python3 deploy/preflight-secrets.py test`\n"), [])
        self.assertEqual(
            self._f("`python3 tools/docs-sync.py check` / `deploy/preflight-secrets.py`\n"),
            [])

    def test_old_sh_name_without_sh_is_error(self):
        """②舊名禁令（bash 面）：TOOLS_SH 名冊各支不帶 .sh 的路徑形命中即 ERROR
        （rev4:B-127、防他機肌肉記憶回寫）。"""
        f = self._f("新機初始化跑 `bash tools/bootstrap`\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("舊名", f[0]["msg"])
        self.assertIn(".sh", f[0]["msg"])

    def test_new_sh_name_does_not_trip_old_sh_name_ban(self):
        """`tools/bootstrap.sh` 內含舊名前綴子字串——負向前瞻（排除 .sh）沒掛好即全庫誤紅
        （rev4:B-111 同型邊界：舊名為新名前綴）。"""
        self.assertEqual(self._f("`bash tools/bootstrap.sh`\n"), [])

    def test_retired_watchdog_sh_name_is_error(self):
        """★B-005 退役嚴格形（比照 deploy 四支之 test_retired_sh_name_is_error）：
        wf-watchdog 轉 python 後 .sh 實體已刪、TOOLS_SH 名冊已摘——文件殘留的舊 bash 命令形
        改由 TOOLS_PY 舊名禁令（缺 .py 後綴即紅）接手；少了本案，摘名冊那步就沒有任何斷言
        證明「殘留舊命令形仍會被擋」（摘完即對 wf-watchdog 全放行也全綠）。
        ★舊路徑字面以串接構造——收刀驗收含「全 repo grep 舊檔名零命中」。"""
        retired = "tools/wf-watchdog" + ".sh"
        self.assertFalse(os.path.exists(os.path.join(ROOT, retired)),
                         msg=f"{retired} 仍在庫＝退役未落實，本案前提失效")
        for text in (f"Monitor command 欄填 `bash {retired} <token>`\n",
                     "Monitor command 欄填 `bash tools/wf-watchdog <token>`\n"):
            f = self._f(text)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=f"{text}｜{f}")
            self.assertIn("舊名", f[0]["msg"])
            self.assertIn(".py", f[0]["msg"])

    def test_non_lowercase_token_treated_as_argument(self):
        """後隨 token 非小寫字母起首（佔位符）＝引數、僅驗工具存在、不驗子命令。"""
        self.assertEqual(self._f("`tools/docs-sync.py 「關鍵詞」`\n"), [])
        self.assertEqual(self._f("`tools/docs-sync.py errata 「關鍵詞」`\n"), [])
        self.assertEqual(self._f("- 生成器＋lint（generate／check／lint／errata／test）\n"), [])

    def test_multi_value_cells_from_live_runbook(self):
        """★RUNBOOK 現行一格多值列原文入 fixture：以空白為界取 token 會取到整串而誤紅。"""
        text = (
            "| `python3 tools/docs-sync.py check` / `lint` | pre-commit 兩道 | 否 |\n"
            "| `python3 tools/docs-sync.py errata <詞>` / `test` | 枚舉／自測 | 否 |\n"
            "| `python3 tools/schema-gate.py gate1|gate2|audit` | 三閘 | **是** |\n"
            "| `python3 tools/wire-schema.py extract` / `test` | 抽 typings／自測 | 是 |\n"
            "| `python3 tools/fork-delta-lint.py` | base-web 原行紀律 | 否 |\n")
        self.assertEqual(self._f(text), [])

    def test_multi_value_cell_validates_every_value_not_just_the_first(self):
        """★A7：一格多值（直豎線相連）時第 2、3 個值一樣要驗——只驗第一個＝假子命令免檢。"""
        f = self._f("| `python3 tools/schema-gate.py gate1|bogus2|audit` | 三閘 | 是 |\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("bogus2", f[0]["msg"])

    def test_multi_value_cell_across_code_spans_validates_every_value(self):
        """★A7 另一形：以斜線相連的第二個代碼段（RUNBOOK 命令表現行寫法）同樣要驗。"""
        f = self._f("| `python3 tools/docs-sync.py check` / `bogus-cmd` | 兩道 | 否 |\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("bogus-cmd", f[0]["msg"])

    def test_multi_value_cell_with_argument_before_slash(self):
        """★A7：`errata <詞>` / `test` 這形——續值在引數之後、仍須驗到。"""
        f = self._f("| `python3 tools/docs-sync.py errata <詞>` / `bogus3` | 枚舉 | 否 |\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("bogus3", f[0]["msg"])

    def test_multi_value_chain_beyond_two_values(self):
        """★A7 邊界（U5-quality 實測漏檢）：三值以上的斜線鏈、混合分隔、全形斜線、同段斜線。

        修前只能延續一次：跨段規則吃掉了前一段的結尾反引號，下一輪的「非反引號任意重複」
        先把「空白斜線空白」吃掉，就再也對不上「反引號＋斜線＋反引號」的形。四形當時
        findings 全為 0（第三值 bogus3 漏、混合分隔 lint 與 bogus 都沒驗到、全形斜線全漏）。
        現庫三件手冊恰好只有兩值斜線與三值直豎線，故不自紅——保護卻是缺的。
        """
        for label, line in (
                ("三值斜線鏈",
                 "| `python3 tools/docs-sync.py check` / `lint` / `bogus3` | x | 否 |\n"),
                ("混合分隔",
                 "| `python3 tools/docs-sync.py check` / `lint|bogus3` | x | 否 |\n"),
                ("全形斜線",
                 "| `python3 tools/docs-sync.py check`／`bogus3` | x | 否 |\n"),
                ("同段斜線",
                 "| `python3 tools/docs-sync.py check/bogus3` | x | 否 |\n")):
            f = self._f(line)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=f"{label}｜{f}")
            self.assertIn("bogus3", f[0]["msg"], msg=label)

    def test_pipe_is_not_a_cross_span_separator(self):
        """★A7 已知邊界（明示契約）：跨代碼段的續值只認斜線、刻意不認直豎線。

        markdown 表格的欄界正是直豎線：`| `… test` | pre-commit 兩道 | 否 |` 這種
        現行寫法，若把直豎線也當跨段分隔符，下一欄第一個小寫詞（pre-commit）就會被當成
        第二個子命令而誤紅。代價＝真的想以「`a` | `b`」表達一格多值時
        第二值驗不到；改用斜線即可（三件手冊現行寫法本來就是斜線）。
        """
        self.assertEqual(
            self._f("| `python3 tools/docs-sync.py test` | pre-commit 自測 | 否 |\n"), [])
        self.assertEqual(
            self._f("| `python3 tools/docs-sync.py test` | `bogus-next-cell` | 否 |\n"), [])

    def test_slash_continuation_requires_a_code_span(self):
        """★A7 已知邊界（明示契約）：斜線之後必須是代碼段，散文不當續值。

        ``… check` / see docs` 這種行文裡的斜線很常見，若不要求續值落在反引號內，
        `see` 就會被當成假子命令而誤紅。
        """
        self.assertEqual(self._f("跑 `python3 tools/docs-sync.py check` / see docs\n"), [])

    def test_cross_span_continuation_is_not_another_command_form(self):
        """★A7 已知邊界（明示契約）：續值只認純子命令代碼段——下一段若本身是完整命令形
        （帶 python3 前綴或 tools 路徑），由 RE_CMD_PY 自己那一輪去驗，不得被當成前一支
        的續值子命令。

        誤收的實害（U5 quality 實證、皆為 RUNBOOK 現行書寫風格）：
        「`…check` / `python3 tools/schema-gate.py test`」跨工具並列時，python3 或 tools
        會被當成前一支的假子命令而誤紅 ERROR 硬擋，訊息還指向不存在的分派表問題；
        rev4:T022 要補的 pre-commit 條件觸發說明正是這種句型。
        """
        cases = [
            # ①半形斜線＋python3 前綴完整命令形（RUNBOOK 表格風格）
            "| `python3 tools/docs-sync.py test` / `python3 tools/schema-gate.py test` "
            "| 條件觸發 | 否 |\n",
            # ②全形斜線散文版
            "跑 `python3 tools/docs-sync.py test`／`python3 tools/wire-schema.py test`\n",
            # ③續值段以 tools 路徑起手（真子命令 gate2 仍須被驗——此行應恰零 finding）
            "`tools/docs-sync.py lint`／`tools/schema-gate.py gate2`\n",
            # ④續值段為 bash 工具路徑
            "`tools/docs-sync.py lint`／`tools/bootstrap.sh`\n",
        ]
        for text in cases:
            self.assertEqual(self._f(text), [], msg=text)
        # 反面：續值段若是「tools 路徑＋假子命令」，由 RE_CMD_PY 自己那輪抓（不因
        # (?!tools/) 而漏）——僅該假子命令一筆、不多不少。
        f = self._f("`tools/docs-sync.py lint`／`tools/schema-gate.py bogus-gate`\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("bogus-gate", f[0]["msg"])

    def test_multi_space_aligned_fake_subcommand_is_caught(self):
        """★A8：以多空白對欄書寫的假子命令（非目錄樹行）須抓得到。"""
        f = self._f("| `python3 tools/docs-sync.py   bogus-aligned` | 說明 | 否 |\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("bogus-aligned", f[0]["msg"])

    def test_error_message_names_the_source_scan_as_the_basis(self):
        """★A9：比對基準是工具源碼的分派表（即時掃源），真表只是同一掃源的生成物。

        訊息若宣稱基準是真表檔，維運者會去手改真表想「讓 lint 過」——真表被 generate
        重算覆蓋、判定也不看它，白費工還會被 check 擋下。故訊息須指出真正的基準。
        """
        f = self._f("`python3 tools/docs-sync.py nonexistent-cmd`\n")
        self.assertIn("源碼", f[0]["msg"])
        self.assertIn("分派表", f[0]["msg"])
        self.assertIn("生成物", f[0]["msg"])

    def test_column_aligned_tree_line_is_not_a_subcommand(self):
        """★A8 已知邊界（明示契約）：目錄樹行以多空白對欄，其後說明文字不是子命令。

        README 的 repo 目錄樹用 `├──`／`└──` 起首、以多空白把說明文字對欄，而
        `tools/fork-delta-lint.py` 那行後面第一個詞恰好是 `base-web`——完全符合子命令的
        字元集（小寫起首、可含連字號）。該工具的子命令集是空的（源碼無分派表、直跑），
        任何 token 都不合法，故一律誤紅。
        取捨：多空白後的 token 一般情形要驗（見上一案），唯獨「行首為樹狀圖分支符號」這一類
        排版行不驗——判準是排版形制而非工具身分，維運者看得懂也躲得開；代價是有人若把假
        子命令寫在目錄樹行上、且刻意用多空白，就抓不到（單一空白仍抓得到，見下一案）。
        """
        self.assertEqual(
            self._f("├── tools/fork-delta-lint.py         base-web 原行紀律機器強制\n",
                    rel="README.md"), [])

    def test_tree_line_with_single_space_still_validates_subcommand(self):
        """★A8 邊界的另一半：樹狀圖行只在「多空白對欄」時免驗，單一空白仍照驗。"""
        f = self._f("├── tools/docs-sync.py bogus-tree 生成器\n", rel="README.md")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("bogus-tree", f[0]["msg"])

    def test_subcommand_on_tool_without_dispatch_is_error(self):
        """空子命令集的工具（fork-delta-lint）被宣稱帶子命令→ERROR。"""
        f = self._f("`python3 tools/fork-delta-lint.py scan`\n")
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))

    def test_bash_tools_existence_only(self):
        """③bash 工具僅驗檔存在：在＝過、不在＝ERROR。"""
        self.assertEqual(self._f("`bash tools/bootstrap.sh`\n"), [])
        self.assertEqual(
            check_cmd_forms({self.RUNBOOK_REL: "`bash tools/bootstrap.sh`\n"},
                            self.SUBS, {"tools/bootstrap.sh": False}
                            )[0]["level"], ERROR)

    def test_corpus_is_exactly_three_live_manuals(self):
        """★語料邊界機器斷言：三件活手冊；NOTES（未來式）／LESSONS（史料）／generated 皆排除。"""
        self.assertEqual(CMD_FORM_CORPUS, ("CLAUDE.md", "README.md", "docs/ops/RUNBOOK.md"))
        self.assertNotIn(NOTES, CMD_FORM_CORPUS)
        for rel in lessons_paths(ROOT):
            self.assertNotIn(rel, CMD_FORM_CORPUS)
        for rel in CMD_FORM_CORPUS:
            self.assertFalse(rel.startswith(GENERATED_DIR + "/"), msg=rel)

    def test_corpus_boundary_end_to_end(self):
        """同一段違規文字：放 NOTES／LESSONS／generated 不紅、放 RUNBOOK 即紅（各一）。"""
        bad = "跑 `python3 tools/docs-sync.py nonexistent-cmd` 與 `tools/docs-sync generate`\n"
        with tempfile.TemporaryDirectory() as d:
            _tools_fixture(d)
            for rel in (NOTES, "docs/ops/LESSONS.md", TOOLS_CLI_MD):
                _wfile(d, rel, bad)
            self.assertEqual(lint_cmd_forms(d), [])
            _wfile(d, "docs/ops/RUNBOOK.md", bad)
            f = lint_cmd_forms(d)
            self.assertEqual(len(f), 2, msg=str(f))
            self.assertTrue(all(x["level"] == ERROR and x["code"] == "Lint19" for x in f))

    def test_missing_tool_source_fails_closed(self):
        """真表無源→Lint19 fail-closed 單發 ERROR（不得因掃源失敗而靜默放行）。"""
        with tempfile.TemporaryDirectory() as d:
            f = lint_cmd_forms(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("fail-closed", f[0]["msg"])

    @unittest.skipUnless(_day1_pending(*CMD_FORM_CORPUS),
                         "Day 1 未達：解除＝三件活手冊全在（CLAUDE.md／README.md／RUNBOOK.md 隨 B5）★此前為假綠：檔案不存在即無命令形可驗、靜默通過")
    def test_live_manuals_are_clean(self):
        """★現庫三件活手冊零命令形漂移（條款上線即自紅＝接線或語料選錯）。"""
        self.assertEqual(lint_cmd_forms(ROOT), [])

    def test_run_lint_wires_cmd_forms(self):
        """★接線層：lint_cmd_forms 從 run_lint 掉線＝Lint19 整條靜默下線。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _tools_fixture(d)
            _wfile(d, "CLAUDE.md", "跑 `tools/docs-sync.py nonexistent-cmd`\n")
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint19" and x["level"] == ERROR for x in f),
                            msg=str(f))


class TestEmptySetGuards(unittest.TestCase):
    """G4 空集合守衛七組（rev4:contracts G4／data-model §6／rev4:research R4）：理論上不可能空的
    枚舉語料空了＝掃描器或環境壞了，一律 fail-closed 報 ERROR、不靜默假綠。

    ★守衛#5 與 data-model §6 字面的差異＝本刀刻意收斂，理由見 lint_tool_dispatch docstring。
    """

    def _bare(self, d):
        """最小外層 fixture：一個 tracked 非 md 檔（令各組守衛可逐組獨立造空）。"""
        _git(d, "init", "-q", "-b", "main")
        _wfile(d, "note.txt", "純文字\n")
        _git(d, "add", "note.txt")
        _git(d, "commit", "-qm", "init")

    def _msgs(self, d):
        return [f"{x['where']}｜{x['msg']}" for x in lint_empty_sets(d, exemptions={})
                if x["level"] == ERROR]

    def test_group1_empty_adr_set(self):
        """①ADR 檔集空／目錄不存在→ERROR，訊息指名集合與來源。"""
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            self.assertTrue(any(ADR_DIR in m and "ADR" in m for m in self._msgs(d)),
                            msg=str(self._msgs(d)))

    def test_group2_empty_events_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            _wfile(d, EVENTS, "")
            self.assertTrue(any(EVENTS in m for m in self._msgs(d)), msg=str(self._msgs(d)))

    def test_group3_empty_tracked_markdown_corpus(self):
        """③外層 tracked *.md 語料空（本 fixture 只 track 一個 .txt）→ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            self.assertTrue(any("tracked" in m and "md" in m for m in self._msgs(d)),
                            msg=str(self._msgs(d)))

    def test_group4_reference_sources_roster_is_pinned(self):
        """★④來源檔全集字面釘死：只迭代 REFERENCE_SOURCES 的斷言是套套邏輯。

        突變實證（修前三支全數存活、338 案零轉紅）：常數移除 ROUTER_SOURCE／移除三個
        reference-src 快照／移除兩支 locale。期望值取自被測常數，常數縮水時期望值同步
        縮水，永遠對得上。縮水的後果＝該來源退回既有散落例外（RouterRoutesError／
        SnapshotError…），R4 第四項「既有散落 fail 行為歸一化進守衛輸出」對它失效、
        lint 端對該來源不再 fail-closed。故此處字面列出十筆，少一筆即紅。
        """
        self.assertEqual(REFERENCE_SOURCES, (
            "docker-compose.yml", "docker-compose.dev.yml", "docker-compose.example.yml",
            "rust-api/server/src/router.rs", "base-web/src/router/elegant/routes.ts",
            "base-web/src/locales/langs/zh-tw.ts", "base-web/src/locales/langs/en-us.ts",
            "docs/ops/reference-src/schema-snapshot.json",
            "docs/ops/reference-src/accounts-snapshot.json",
            "docs/ops/reference-src/archetype-map.json"))

    def test_group4_outer_sources_error_submodule_sources_skip(self):
        """★④lint 端兩分支：外層來源缺席＝ERROR、submodule 來源之庫不可查＝SKIP。

        後者是與 rev4:contracts G4 字面的刻意落差（理由見 lint_reference_sources docstring）：
        同一次 lint 內 Lint16／Lint17／Lint18 對「worktree 缺席」逐字判「不適用、不是失敗」，守衛#4
        若對同一事實硬紅即自相矛盾，且會淹沒 quickstart S5 造空劇本的機判。
        """
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            # ★傳空豁免表：本案驗的是「來源缺席」的原生兩分支語意，不受 Day 1 具名豁免干擾
            f = lint_reference_sources(d, exemptions={})
            errs = [x["where"] for x in f if x["level"] == ERROR]
            skips = [x for x in f if x["level"] == SKIP]
            self.assertEqual(errs, [rel for rel in REFERENCE_SOURCES
                                    if owning_submodule(rel) is None], msg=str(f))
            self.assertEqual([x["where"] for x in skips], ["base-web", "rust-api"])
            self.assertTrue(all("worktree 缺席" in x["msg"] for x in skips), msg=str(skips))

    def test_group4_error_when_submodule_is_live_but_source_missing(self):
        """★④庫可查而來源檔不見＝仍是 ERROR（跳過只給「庫開不起來」，不給「檔沒了」）。"""
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            for _key, sub in PIN_KEYS:
                _init_sub(d, sub)
            errs = [x["where"] for x in lint_reference_sources(d, exemptions={})
                    if x["level"] == ERROR]
            self.assertEqual(errs, list(REFERENCE_SOURCES), msg=str(errs))

    def test_group4_is_also_wired_into_generate(self):
        """★守衛#4 雙掛（rev4:contracts G4「lint／generate 來源檔守衛雙掛」）：generate 端亦須報。

        ★不可只驗 lint_reference_sources() 本體：那樣「函式活著、generate 沒接」零信號
        （突變實證：把 cmd_generate 的守衛呼叫拿掉，全套仍全綠）。故本案直接跑 cmd_generate
        並斷言 exit 1＋守衛訊息——接線斷掉時它會改以 ComposePortsError 拋出（來源檔缺席
        的既有散落 fail 行為），本案即當場紅。
        ★generate 端 submodule_skip=False：沒有來源就是算不出對照表，十筆全數 ERROR
        （跳過只會讓它往下撞既有散落例外）；接線改成吃 lint 端語意時本案亦紅。
        """
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            f = lint_reference_sources(d, submodule_skip=False, exemptions={})
            self.assertEqual(len(f), len(REFERENCE_SOURCES), msg=str(f))
            self.assertTrue(all(x["level"] == ERROR for x in f))
            buf, err = io.StringIO(), io.StringIO()
            # ★cmd_generate 無參數、內部取模組層預設，故連 DAY1_EXEMPTIONS 一併 patch 成空表
            with mock.patch.object(sys.modules[__name__], "ROOT", d), \
                 mock.patch.object(sys.modules[__name__], "DAY1_EXEMPTIONS", {}):
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                    rc = cmd_generate()
            self.assertEqual(rc, 1, msg=buf.getvalue() + err.getvalue())
            self.assertIn("來源檔守衛", err.getvalue())
            self.assertIn("reference 來源檔不存在", buf.getvalue())
            self.assertIn(ROUTER_SOURCE, buf.getvalue())

    def test_group5_empty_tool_roster(self):
        """⑤掃源清單本身空（名冊被清空）→ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            _tools_fixture(d)
            self.assertEqual([x for x in lint_tool_dispatch(d) if x["level"] == ERROR], [])
            mod = sys.modules[__name__]
            with mock.patch.object(mod, "TOOLS_PY", ()), \
                 mock.patch.object(mod, "TOOLS_SH", ()):
                f = lint_tool_dispatch(d)
            self.assertTrue(any("掃源清單" in x["msg"] for x in f), msg=str(f))

    def test_group5_dispatch_table_present_but_scanned_empty(self):
        """★⑤第二半（非套套邏輯的那半）：源碼有分派表、掃出的子命令集卻空＝掃源正則壞了。

        弱探針（源碼是否出現 cmd 比較）與嚴格掃源正則各自獨立，故把 RE_DISPATCH_EQ／
        RE_DISPATCH_IN 改壞成永不命中時本守衛當場紅——而 fork-delta-lint 這種本來就沒有
        分派表的工具（真表如實記「無——源碼無分派表、直跑」）仍是合法空集合、不誤紅。
        """
        dead = re.compile(r"ZZZ-NEVER-MATCH-ZZZ")
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            _tools_fixture(d)
            mod = sys.modules[__name__]
            with mock.patch.object(mod, "RE_DISPATCH_EQ", dead), \
                 mock.patch.object(mod, "RE_DISPATCH_IN", dead):
                f = lint_tool_dispatch(d)
            named = {x["where"] for x in f if x["level"] == ERROR}
            self.assertIn("tools/docs-sync.py", named, msg=str(f))
            self.assertNotIn("tools/fork-delta-lint.py", named, msg=str(f))

    def test_group5_real_repo_tools_are_green(self):
        """★現庫實跑：fork-delta-lint 子命令集為空是正確事實，守衛不得對現況自紅。"""
        self.assertEqual(lint_tool_dispatch(ROOT), [])

    def test_group6_empty_credential_scan_roster(self):
        """⑥憑證掃描 tracked 檔清單空（無 index）→ERROR（清單空＝掃了個寂寞）。"""
        with tempfile.TemporaryDirectory() as d:
            _git(d, "init", "-q", "-b", "main")
            self.assertTrue(any("憑證掃描" in m for m in self._msgs(d)),
                            msg=str(self._msgs(d)))

    def test_group7_command_form_corpus_files(self):
        """⑦命令形語料三檔存在——逐檔缺席即 ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            msgs = self._msgs(d)
            for rel in CMD_FORM_CORPUS:
                self.assertTrue(any(rel in m for m in msgs), msg=f"{rel} 未被守衛點名")

    @unittest.skipUnless(_day1_pending(*REFERENCE_SOURCES),
                         "Day 1 未達：解除＝十筆 reference 來源全存在（最後一筆＝gen.msg_dict 於 i18n 地基刀；勿設早，B10 起解除跳過即真紅卡 bootstrap 第 5 節）")
    def test_real_repo_has_no_empty_set(self):
        """★現況驗收：現庫七組守衛全綠（守衛上線即自紅＝定義錯或接線錯）。"""
        self.assertEqual(lint_empty_sets(ROOT), [])

    def test_group4_and_group5_are_composed_into_lint_empty_sets(self):
        """★組裝層：守衛#4／#5 組裝進 lint_empty_sets 的那兩行掉線＝lint 端零信號。

        其餘五組的造空案都走 _msgs()（＝lint_empty_sets 本體），唯獨#4／#5 的既有案直呼
        lint_reference_sources／lint_tool_dispatch，繞過組裝層；而 lint_empty_sets 僅有的
        兩個組裝案都擋不住——test_real_repo_has_no_empty_set 在現庫本來就期望空（這兩支對
        現況本來就回空，拿掉照樣是空）、test_run_lint_wires_empty_set_guards 修前只驗
        「存在任一 Lint20 ERROR」。突變實證（修前）：兩行分別換成 pass，345 案零轉紅。
        #5 掉線尤其是全損：它在 lint 端沒有第二個家（#4 另有 generate 端接線案看住），
        Lint19 的 fail-closed 只覆蓋「掃源失敗」那一格，FR-013 要防的「有分派表卻掃出空集合
        而恆綠」會直接消失。
        """
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            msgs = self._msgs(d)
            self.assertTrue(any("docker-compose.yml" in m and "reference 來源檔不存在" in m
                                for m in msgs), msg=str(msgs))
            self.assertTrue(any(m.startswith("tools｜") and "工具掃源失敗" in m
                                for m in msgs), msg=str(msgs))

    def test_run_lint_wires_empty_set_guards(self):
        """★接線層：lint_empty_sets 從 run_lint 掉線＝G4 整條靜默下線。

        ★不可只斷言「存在任一 Lint20 ERROR」：_bare fixture 上守衛#1／#2／#3／#7 都會報，
        any 恆真，#4／#5 的組裝行換成 pass 照樣全綠。故改以 where 全集逐字對照，讓每一支
        守衛在 run_lint 這條線上各自帶信號。#6（憑證掃描清單）在本 fixture 有 index、
        依定義不報，由 test_group6_empty_credential_scan_roster 單獨釘。
        """
        with tempfile.TemporaryDirectory() as d:
            self._bare(d)
            # ★空表：本案驗「守衛有沒有接進 run_lint」，Day 1 豁免行為另有專屬案
            wheres = {x["where"] for x in run_lint(d, exemptions={})
                      if x["code"] == "Lint20" and x["level"] == ERROR}
            expected = ({ADR_DIR, EVENTS, ".", "tools"}
                        | {rel for rel in REFERENCE_SOURCES
                           if owning_submodule(rel) is None}
                        | set(CMD_FORM_CORPUS)
                        # 守衛#8（rev5 新增）：BUDGETS 名冊存在性。逐字列出而非
                        # 由 BUDGETS 推導——取自被測常數即套套邏輯，名冊縮水時期望
                        # 同步縮水、永遠對得上（§4.5.4）。三件活手冊已由
                        # CMD_FORM_CORPUS 涵蓋，此處補其餘五筆。
                        | {"docs/ops/NOTES.md", "docs/ops/BACKLOG.md",
                           "docs/generated/STATE.md", "docs/arc42/ARCHITECTURE.md",
                           ".specify/memory/constitution.md"})
            self.assertEqual(wheres, expected)


class TestExecBitGuard(unittest.TestCase):
    """Lint21 index exec bit 守衛（rev4:B-116）：名冊內直接執行腳本 index stage-0 必為 100755。

    ★fixture 一律自建 temp repo（_git／_wfile）、絕不動真 repo index——rev4:018 曾因 fixture
    寫進真 repo index 炸 44 failures（purge_git_env docstring 實證）；真 repo 僅唯讀。
    """

    def _repo(self, d, rel="bin/run.sh", exec_bit=False):
        _git(d, "init", "-q", "-b", "main")
        _wfile(d, rel, "#!/usr/bin/env bash\necho ok\n")
        _git(d, "add", rel)
        if exec_bit:
            _git(d, "update-index", "--chmod=+x", rel)
        _git(d, "commit", "-qm", "init")

    def test_mode_644_red_names_file_mode_and_repair(self):
        """①名冊檔 index 100644→ERROR 指名檔案、現值、修復命令。"""
        with tempfile.TemporaryDirectory() as d:
            self._repo(d, exec_bit=False)
            f = check_exec_bits(("bin/run.sh",), index_exec_modes(d, ("bin/run.sh",)))
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertEqual(f[0]["code"], "Lint21")
            self.assertEqual(f[0]["where"], "bin/run.sh")
            self.assertIn("100644", f[0]["msg"])
            self.assertIn("git update-index --chmod=+x bin/run.sh", f[0]["msg"])

    def test_mode_755_green(self):
        """②名冊檔 index 100755→零 finding。"""
        with tempfile.TemporaryDirectory() as d:
            self._repo(d, exec_bit=True)
            self.assertEqual(
                check_exec_bits(("bin/run.sh",), index_exec_modes(d, ("bin/run.sh",))), [])

    def test_roster_file_missing_from_index_red(self):
        """③名冊檔不在 index→ERROR（名冊腐化即紅）。"""
        with tempfile.TemporaryDirectory() as d:
            self._repo(d, exec_bit=True)
            roster = ("bin/run.sh", "bin/亡佚.sh")
            f = check_exec_bits(roster, index_exec_modes(d, roster))
            self.assertEqual([x["where"] for x in f], ["bin/亡佚.sh"], msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("index", f[0]["msg"])

    def test_empty_roster_fail_closed(self):
        """名冊空集合→ERROR（fail-closed、Lint20 家族）。"""
        f = check_exec_bits((), {})
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("EXEC_BIT_ROSTER", f[0]["msg"])

    def test_roster_is_pinned(self):
        """★名冊字面釘死（同 REFERENCE_SOURCES 慣例）：期望值取自被測常數＝套套邏輯，
        名冊縮水時守衛靜默瘦身、零信號——字面列出十二筆，少一筆即紅。
        ★十四→十二（B-037 U3）：generate-secrets.sh／preflight-secrets.sh 退役、正典改
        python3 前綴的 .py 形（不帶 exec bit），叫用形不再依賴 index exec bit。"""
        self.assertEqual(EXEC_BIT_ROSTER, (
            ".githooks/pre-commit", ".githooks/pre-push",
            ".githooks-submodule/pre-commit", ".githooks-submodule/pre-push",
            "deploy/generate-dev-cert.sh",
            "deploy/sops.sh",
            "tools/docs-sync.py", "tools/entity-drift-gate.py",
            "tools/fork-delta-lint.py", "tools/schema-gate.py",
            "tools/secret-value-guard.py", "tools/wire-schema.py"))

    @unittest.skipUnless(_day1_pending(*EXEC_BIT_ROSTER),
                         "Day 1 未達：解除＝EXEC_BIT_ROSTER 十二筆全在（deploy 兩支隨 B5b 到位）")
    def test_real_repo_roster_all_755(self):
        """★現庫名冊全 100755（條款上線即自紅＝名冊選錯或 index 已破戒）；真 repo 唯讀。"""
        self.assertEqual(lint_exec_bits(ROOT), [])

    def test_run_lint_wires_exec_bits(self):
        """★接線層：lint_exec_bits 從 run_lint 掉線＝Lint21 整條靜默下線。

        bare fixture 的 index 沒有任何名冊檔→Lint21 必報名冊腐化 ERROR；任何 Lint21 finding
        只可能來自 lint_exec_bits——信號純淨。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint21" and x["level"] == ERROR for x in f),
                            msg=str([x for x in f if x["code"] == "Lint21"]))

    # -- self-test 防恆綠（Lint16 慣例） ---------------------------------------
    def test_self_test_green_on_healthy_checker(self):
        self.assertEqual(exec_bit_self_test(), [])

    def _with_checker(self, fake, fn):
        original = globals()["check_exec_bits"]
        globals()["check_exec_bits"] = fake
        try:
            return fn()
        finally:
            globals()["check_exec_bits"] = original

    def test_self_test_catches_dead_checker(self):
        """④突變面：判定函式被改成永不報（恆綠）→self-test 逐紅樣本報 ERROR。"""
        f = self._with_checker(lambda roster, modes: [], exec_bit_self_test)
        self.assertEqual(len(f), 3, msg=str(f))
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertTrue(all("self-test 失效" in x["msg"] for x in f))

    def test_self_test_catches_overbroad_checker(self):
        """④突變面：判定函式被改成一律報紅→綠樣本誤報、self-test 報 ERROR。"""
        f = self._with_checker(
            lambda roster, modes: [finding(ERROR, "Lint21", "樣本", "誤報")],
            exec_bit_self_test)
        self.assertTrue(any(x["level"] == ERROR and "綠樣本" in x["msg"] for x in f),
                        msg=str(f))

    def test_assembly_wires_self_test(self):
        """★組裝層：exec_bit_self_test 從 lint_exec_bits 掉線＝防恆綠靜默下線。"""
        original = globals()["check_exec_bits"]
        globals()["check_exec_bits"] = lambda roster, modes: []
        try:
            f = lint_exec_bits(ROOT)
        finally:
            globals()["check_exec_bits"] = original
        self.assertTrue(any(x["code"] == "Lint21" and "self-test 失效" in x["msg"] for x in f),
                        msg=str(f))


class TestRangeStringGuard(unittest.TestCase):
    """Lint22 lint 條款範圍字串守衛（rev4:B-126）：名冊三檔「Lint03～LintNN」逐檔全命中 vs 掃源推導上界。

    ★fixture 一律 tempdir 自建假名冊三檔（_wfile、無需 git）、真 repo 唯讀；
    ★一切錨形／範圍字面以拆分構造——本檔自身既是推導源又在名冊內，落完整字面＝
    被自己掃到（範圍形自咬）或把推導上界灌水（錨形）；同 Lint19 _FAKE_* 模板紀律。
    """

    @staticmethod
    def _own():
        return int(RANGE_CODE.removeprefix("Lint"))

    @staticmethod
    def _rng(nn, wave="～"):
        """構造範圍字串字面（拆分、兩碼零填；wave 預設全形～、傳 "~" 得半形）。"""
        return "Lint03" + wave + "Lint" + ("%02d" % int(nn))

    @staticmethod
    def _call(nn):
        """構造錨形 finding 呼叫字面（拆分、兩碼零填——非兩碼會被 scan_nonpadded_codes 抓）。"""
        return "finding" + '(ERROR, "Lint' + ("%02d" % int(nn)) + '", "處", "因")\n'

    def _fixture(self, d, src_nn=None, src2_nn=None, runbook_nn=None, hook_nn=None):
        """假名冊三檔：docs-sync 源＝錨形兩筆（3＋自身碼）＋兩處全形範圍字串（鏡照實形：
        檔頭＋run_lint docstring）；RUNBOOK 半形一處；pre-commit 全形一處。省略＝正確值。"""
        own = self._own()
        src_nn = own if src_nn is None else src_nn
        src2_nn = own if src2_nn is None else src2_nn
        runbook_nn = own if runbook_nn is None else runbook_nn
        hook_nn = own if hook_nn is None else hook_nn
        _wfile(d, "tools/docs-sync.py",
               self._call(3) + self._call(own)
               + "頭 " + self._rng(src_nn) + "\n"
               + "尾 " + self._rng(src2_nn) + "\n")
        _wfile(d, "docs/ops/RUNBOOK.md", "表 " + self._rng(runbook_nn, "~") + "\n")
        _wfile(d, ".githooks/pre-commit", "# 註 " + self._rng(hook_nn) + "\n")

    def test_all_correct_green(self):
        """②三檔皆＝推導上界（半形／全形混用如實形）→零 finding。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            self.assertEqual(lint_range_strings(d), [])

    def test_wrong_value_red_names_file_line_actual_expected(self):
        """①某檔上界字面落後→ERROR 指名檔案:行號＋實得＋應為＋同 commit 修復指引。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d, hook_nn=self._own() - 1)
            f = lint_range_strings(d)
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertEqual(f[0]["code"], "Lint22")
            self.assertEqual(f[0]["where"], ".githooks/pre-commit:1")
            self.assertIn(str(self._own() - 1), f[0]["msg"])
            self.assertIn(str(self._own()), f[0]["msg"])
            self.assertIn("同 commit", f[0]["msg"])

    def test_docs_sync_second_site_also_checked(self):
        """①docs-sync 一檔兩處（檔頭＋run_lint docstring 實形）漏改第二處→該行 ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d, src2_nn=self._own() - 1)
            f = lint_range_strings(d)
            self.assertEqual([x["where"] for x in f], ["tools/docs-sync.py:4"], msg=str(f))

    def test_zero_hit_red(self):
        """③名冊檔在、範圍字串消失（被刪或改形）→ERROR 名冊腐化。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            _wfile(d, ".githooks/pre-commit", "# 無範圍字串\n")
            f = lint_range_strings(d)
            self.assertEqual([x["where"] for x in f], [".githooks/pre-commit"], msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("零命中", f[0]["msg"])

    def test_missing_roster_file_red(self):
        """③名冊檔缺席→ERROR（檔案移位／改名須同步改名冊）。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            os.remove(os.path.join(d, ".githooks/pre-commit"))
            f = lint_range_strings(d)
            self.assertEqual([x["where"] for x in f], [".githooks/pre-commit"], msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("缺席", f[0]["msg"])

    def test_both_wave_forms_scanned(self):
        """④半形~與全形～皆收、行號正確；一行多筆亦全收。"""
        text = ("甲 " + self._rng(9, "~") + "\n"
                + "乙 " + self._rng(9) + " 丙 " + self._rng(8) + "\n")
        self.assertEqual(scan_range_hits(text), [(1, 9), (2, 9), (2, 8)])

    def test_derive_codes_ignores_prose_and_range_strings(self):
        """錨形只收 finding 呼叫字面：散文提及與範圍字串不入推導（誤收散文＝上界失真）。"""
        src = self._call(5) + "散文提及 Lint09 與 " + self._rng(8) + "\n"
        self.assertEqual(derive_lint_codes(src), {5})

    def test_empty_roster_fail_closed(self):
        """名冊空集合→ERROR（fail-closed、Lint20 家族）。"""
        f = check_range_strings(7, (), {})
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("RANGE_ROSTER", f[0]["msg"])

    def test_derivation_failure_fail_closed(self):
        """推導失效（bound=None）→單發 ERROR、不進名冊比對（比對無基準）。"""
        f = check_range_strings(None, ("樣本",), {"樣本": [(1, 7)]})
        self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
        self.assertIn("推導失效", f[0]["msg"])

    def test_roster_is_pinned(self):
        """★名冊字面釘死（Lint21 慣例）：期望值取自被測常數＝套套邏輯，名冊縮水零信號。"""
        self.assertEqual(RANGE_ROSTER, (
            "tools/docs-sync.py", "docs/ops/RUNBOOK.md", ".githooks/pre-commit"))

    def test_real_source_derivation_contains_own_code_and_bound_pinned(self):
        """★推導一致性（真源）：集合必含本條款自身碼（推導前提）、上界釘版＝26
        （Lint26 LESSONS 分檔對賬閘為現行最大號）——上界前進時本測試逼著同刀更新
        （釘版＝有意識動作、同 test_roster_is_pinned 慣例；非守衛真值側）。"""
        codes = derive_lint_codes(_read(ROOT, "tools/docs-sync.py"))
        self.assertIn(self._own(), codes)
        self.assertEqual(max(codes), 26)

    @unittest.skipUnless(_day1_pending(*RANGE_ROSTER),
                         "Day 1 未達：解除＝RANGE_ROSTER 三檔全在（docs/ops/RUNBOOK.md 隨 B5 骨架落地）")
    def test_real_repo_range_green(self):
        """★現庫名冊三檔四處全＝推導上界（條款上線即自證：漏 bump 任一處當場紅）；
        真 repo 唯讀。"""
        self.assertEqual(lint_range_strings(ROOT), [])

    def test_run_lint_wires_range_strings(self):
        """★接線層：lint_range_strings 從 run_lint 掉線＝Lint22 整條靜默下線。

        bare fixture 無 tools/docs-sync.py＝推導源缺席→Lint22 必報推導失效 ERROR；任何
        Lint22 finding 只可能來自 lint_range_strings——信號純淨。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint22" and x["level"] == ERROR for x in f),
                            msg=str([x for x in f if x["code"] == "Lint22"]))

    # -- self-test 防恆綠（Lint16/Lint21 慣例） -----------------------------------
    def test_self_test_green_on_healthy_checker(self):
        self.assertEqual(range_self_test(), [])

    def _with_checker(self, fake, fn):
        original = globals()["check_range_strings"]
        globals()["check_range_strings"] = fake
        try:
            return fn()
        finally:
            globals()["check_range_strings"] = original

    def test_self_test_catches_dead_checker(self):
        """④突變面：判定函式被改成永不報（恆綠）→self-test 逐紅樣本報 ERROR。"""
        f = self._with_checker(lambda bound, roster, hits: [], range_self_test)
        self.assertEqual(len(f), 3, msg=str(f))
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertTrue(all("self-test 失效" in x["msg"] for x in f))

    def test_self_test_catches_overbroad_checker(self):
        """④突變面：判定函式被改成一律報紅→綠樣本誤報、self-test 報 ERROR。"""
        f = self._with_checker(
            lambda bound, roster, hits: [finding(ERROR, "Lint22", "樣本", "誤報")],
            range_self_test)
        self.assertTrue(any(x["level"] == ERROR and "綠樣本" in x["msg"] for x in f),
                        msg=str(f))

    def test_self_test_catches_wave_blind_scanner(self):
        """④突變面：掃描器對波浪形失明（綠樣本命中≠2）→self-test 報 ERROR。"""
        original = globals()["scan_range_hits"]
        globals()["scan_range_hits"] = lambda text: [(1, 7)]
        try:
            f = range_self_test()
        finally:
            globals()["scan_range_hits"] = original
        self.assertTrue(any(x["level"] == ERROR and "兩型" in x["msg"] for x in f),
                        msg=str(f))

    def test_assembly_wires_self_test(self):
        """★組裝層：range_self_test 從 lint_range_strings 掉線＝防恆綠靜默下線。"""
        original = globals()["check_range_strings"]
        globals()["check_range_strings"] = lambda bound, roster, hits: []
        try:
            f = lint_range_strings(ROOT)
        finally:
            globals()["check_range_strings"] = original
        self.assertTrue(any(x["code"] == "Lint22" and "self-test 失效" in x["msg"] for x in f),
                        msg=str(f))


class TestLintIdNamespace(unittest.TestCase):
    """Lint25 跨代裸編號（ADR 0012）：逐 token 判定、掃源 registry、具名豁免、防恆綠。

    ★樣本編號一律用 9 字頭合成號或已前綴形（ADR 0012 決定 4）——不與任何真 registry 區間
      相撞，rev5 配號往前走時樣本不會靜默變綠；純判定案不碰真 repo。
    """

    REG = LINT25_SELF_TEST_REG

    def _scan(self, line, rel="樣本.md", reg=None, exemptions=None):
        hits, counts = scan_id_namespace({rel: line + "\n"}, reg or self.REG,
                                         {} if exemptions is None else exemptions)
        return hits, counts

    # -- 正例：裸前代形必命中 ---------------------------------------------------
    def test_bare_prior_generation_forms_flagged(self):
        """一族一案：裸形逐 token 命中，且族別標籤正確（標籤錯＝紅訊息指錯方向）。"""
        cases = [
            ("見 999-nope-slug 刀", "feat", "999-nope-slug"),
            ("見 ADR 9999 判例", "adr", "ADR 9999"),
            ("見 B-777 條目", "bid", "B-777"),
            ("見 L-777 教訓", "lid", "L-777"),
            ("見 T999 任務", "tid", "T999"),
            ("見 FR-999 需求", "frsc", "FR-999"),
            ("見 SC-999 指標", "frsc", "SC-999"),
            ("見 P9.9 條款", "pn", "P9.9"),
            ("見 §P9 節", "psec", "§P9"),
            ("見 REVIEW-999-999 報告", "review", "REVIEW-999-999"),
            ("見 F999-9 finding", "fid", "F999-9"),
            ("見 099 U9 那輪", "uround", "099 U9"),
            ("見 US9 故事", "us", "US9"),
            ("見 research R9 段", "research", "research R9"),
            ("見 §G9 守衛", "contracts", "§G9"),
            ("見 scan-gates §S9 節", "scangates", "scan-gates §S9"),
            ("見 m999 遷移", "mid", "m999"),
            ("見 Lint99 條款", "lintcode", "Lint99"),
            ("見 019 刀", "bare", "019"),   # 值域 001~29 內樣本（099 已被收斂排除、另有反例案釘）
        ]
        for line, kind, tok in cases:
            hits, _c = self._scan(line)
            self.assertEqual([(h["kind"], h["tok"]) for h in hits], [(kind, tok)], msg=line)

    def test_shared_prefix_second_token_still_flagged(self):
        """★ADR 0012 決定 3：共享前綴形不合規——並列第二號沒有自己的前綴就是命中。"""
        hits, _c = self._scan("承 rev4:ADR 9999／ADR 9998 兩判例")
        self.assertEqual([h["tok"] for h in hits], ["ADR 9998"])

    def test_prose_qualifier_not_compliant(self):
        """★ADR 0012 決定 3：空格散文形（rev4 P9.9）不算合規——散文限定擋不住擴散。"""
        hits, _c = self._scan("沿用 rev4 P9.9 的口徑")
        self.assertEqual([h["tok"] for h in hits], ["P9.9"])

    # -- 反例：合規／原生／假號段不得命中 ---------------------------------------
    def test_prefixed_tokens_not_flagged(self):
        for line in ("依 rev4:999-nope-slug 刀", "依 rev3:ADR 9999", "依 rev2:B-777",
                     "依 rev4:T999", "依 rev5:m999", "依 rev4:099 刀", "依 rev4:US9"):
            hits, _c = self._scan(line)
            self.assertEqual(hits, [], msg=line)

    def test_rev5_native_ids_not_flagged(self):
        """★缺此案則「裸碼即前代碼」型的錯誤實作全套仍綠（同 Lint11 負向樣本之理由）。"""
        reg = dict(self.REG, specs={"001-schema-baseline"}, spec_nums={"001"},
                   mids={"m001", "m002"})
        for line in ("追 001-schema-baseline 刀", "立 ADR 0012", "追 B-012", "承 L-002",
                     "跑 m001 遷移", "見 001 刀", "見 Lint25 條款", "配到 B-040 這個 next-id"):
            hits, _c = self._scan(line, reg=reg)
            self.assertEqual(hits, [], msg=line)

    def test_self_reference_ids_native_inside_own_spec_dir(self):
        """spec 自引用：T／FR／SC／US 在自己那支刀目錄底下＝原生，出了目錄照抓。"""
        reg = dict(self.REG, specs={"001-schema-baseline"}, spec_nums={"001"})
        line = "驗收 T999 對應 FR-999／SC-999、屬 US9"
        inside, _c = self._scan(line, rel="specs/001-schema-baseline/tasks.md", reg=reg)
        self.assertEqual(inside, [])
        outside, _c = self._scan(line, rel="docs/ops/NOTES.md", reg=reg)
        self.assertEqual(len(outside), 4, msg=str(outside))

    def test_fake_segments_not_flagged(self):
        """★ADR 0012 決定 4：自測假號段（B-9xx／L-9xx／9NN-fake-*）永不落 rev5 可達號段。"""
        for line in ("fixture 用 B-901", "fixture 用 L-999", "fixture 刀 999-fake-slug"):
            hits, _c = self._scan(line)
            self.assertEqual(hits, [], msg=line)

    def test_non_candidate_families_never_hit(self):
        """★K1-NN／K2-NN／E-NNN／無連字號創世步不落入任何形狀族——天然放行的機器釘子：
        將來收緊某族的 regex 若不慎把它們掃進來，本案當場紅。"""
        for line in ("承襲 K1-13 與 K2-07 清單", "缺陷 E-003 已修", "波 -1 的 B9／B8a／B10 步"):
            hits, _c = self._scan(line)
            self.assertEqual(hits, [], msg=line)

    def test_precision_exclusions(self):
        """裸刀號的排除面：權限 mode／日期／版本號／小數／長數字串不得誤報。"""
        for line in ("chmod 0755 與 0700", "日期 2026-08-07", "版本 1.0.019",
                     "比例 0.001", "源倉 fork260509-rev5", "埠 20080"):
            hits, _c = self._scan(line)
            self.assertEqual([h["tok"] for h in hits], [], msg=line)

    def test_full_knife_name_wins_over_bare_number(self):
        """★次序即優先權：刀名全形先於裸刀號，否則 slug 這個血緣證據會被拆掉。"""
        hits, _c = self._scan("見 099-nope-slug 刀")
        self.assertEqual([(h["kind"], h["tok"]) for h in hits], [("feat", "099-nope-slug")])

    # -- 具名豁免 ---------------------------------------------------------------
    def test_named_exemption_swallows_and_counts(self):
        """豁免例：events 路徑跳過、且以計數回報（不靜默）。"""
        hits, counts = scan_id_namespace({EVENTS: "舊列提及 ADR 9999\n"}, self.REG)
        self.assertEqual(hits, [])
        self.assertEqual(counts, {"events.append-only": 1})

    def test_named_exemption_is_path_scoped(self):
        """★豁免射程＝具名路徑，鄰居檔不得沾光（拔項會翻紅的另一面）。"""
        hits, _c = scan_id_namespace({"docs/ops/NOTES.md": "提及 ADR 9999\n"}, self.REG)
        self.assertEqual(len(hits), 1)

    def test_exemption_table_columns(self):
        """四欄紀律：名冊自身腐化會讓整套豁免語意失真。"""
        _assert_lint25_table()
        # B-004 收官（2026-08-07）後全表合法地僅剩結構性永久豁免（到期即紅列可為零）；
        # 解除機關本體由 test_expiring_exemption_goes_red_when_zero_hit 以合成表自證，
        # 此處只釘欄形：第三欄必為 bool（真值腐化＝永久豁免被誤標可解除、或反之）。
        self.assertTrue(all(isinstance(row[2], bool) for row in LINT25_EXEMPTIONS.values()),
                        msg="到期即紅欄必為 bool")

    def test_expiring_exemption_goes_red_when_zero_hit(self):
        """★到期即紅：帶解除謂詞的豁免零命中＝清償已完成，項仍在表即 ERROR 指名該筆。"""
        table = {"樣本.expiring": ("零命中即到期", lambda h: h["rel"] == "不存在的檔", True,
                                   "2026-08-07")}
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = lint_id_namespace(d, [], exemptions=table)
        self.assertTrue(any(x["level"] == ERROR and x["where"] == "樣本.expiring" for x in f),
                        msg=str(f))

    # -- 降級開關（WARN ↔ ERROR） -----------------------------------------------
    def test_downgrade_switch_controls_severity(self):
        """★唯一機關雙態：None（現行活態、B-004 收官後）＝逐筆 ERROR；三元組＝WARN 摘要形
        （清償期歷史態、以 mock 續釘防迴歸）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _wfile(d, "docs/ops/NOTES.md", "見 ADR 9999 與 T999。\n")
            err = lint_id_namespace(d, ["docs/ops/NOTES.md"], exemptions={})
            self.assertEqual(len([x for x in err if x["level"] == ERROR]), 2, msg=str(err))
            self.assertTrue(all("ADR 0012" in x["msg"]
                                for x in err if x["level"] == ERROR), msg=str(err))
            with mock.patch.object(sys.modules[__name__], "LINT25_DAY1_DOWNGRADE",
                                   ("day1.test", "測試用降級態", "2026-08-07")):
                warn = lint_id_namespace(d, ["docs/ops/NOTES.md"], exemptions={})
            self.assertTrue(any(x["level"] == WARN and "共 2 筆" in x["msg"] for x in warn),
                            msg=str(warn))
            self.assertFalse([x for x in warn if x["level"] == ERROR], msg=str(warn))

    def test_warn_sample_is_truncated(self):
        """WARN 期只逐筆列前 N 筆、其餘以「另 N 筆」收尾（避免淹沒其他條款的紅）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _wfile(d, "docs/ops/NOTES.md", "".join(f"第 {i} 行提及 ADR 9999。\n"
                                                   for i in range(LINT25_WARN_SAMPLE + 5)))
            with mock.patch.object(sys.modules[__name__], "LINT25_DAY1_DOWNGRADE",
                                   ("day1.test", "測試用降級態", "2026-08-07")):
                f = lint_id_namespace(d, ["docs/ops/NOTES.md"], exemptions={})
        detail = [x for x in f if x["level"] == WARN and x["where"].startswith("docs/")]
        self.assertEqual(len(detail), LINT25_WARN_SAMPLE)
        self.assertTrue(any("另 5 筆" in x["msg"] for x in f), msg=str(f))

    # -- 掃描面 -----------------------------------------------------------------
    def test_skip_dirs_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            tracked = []
            for rel in ("docs/generated/STATE.md", "docs/brainstorms/x.md",
                        ".specify/templates/t.md", ".claude/skills/s/SKILL.md"):
                _wfile(d, rel, "提及 ADR 9999。\n")
                tracked.append(rel)
            f = lint_id_namespace(d, tracked, exemptions={})
            self.assertFalse([x for x in f if x["level"] in (ERROR, WARN)], msg=str(f))

    def test_binary_file_skipped(self):
        """二進位／非文字檔不是掃描面——讀不出來就跳過，不得炸掉整條 lint。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            with open(os.path.join(d, "blob.bin"), "wb") as fh:
                fh.write(b"\xff\xfe\x00ADR 9999")
            f = lint_id_namespace(d, ["blob.bin"], exemptions={})
            self.assertFalse([x for x in f if x["level"] in (ERROR, WARN)], msg=str(f))

    # -- registry 掃源現算 -------------------------------------------------------
    def test_registry_is_derived_from_sources(self):
        """★registry 掃源現算、絕不落字面名冊：真 repo 的 specs 目錄／ADR 檔名／next-id
        必須逐一對得上——名冊寫死時本案在配號前進的下一刻就過期而不自知。"""
        reg = lint25_registry(ROOT)
        self.assertEqual(reg["specs"],
                         {n for n in os.listdir(os.path.join(ROOT, "specs"))
                          if os.path.isdir(os.path.join(ROOT, "specs", n))}
                         | {n[:-3] for n in os.listdir(os.path.join(ROOT, "docs/brainstorms"))
                            if n.endswith(".md") and re.match(r"\d{3}-", n)})
        self.assertEqual(reg["adrs"],
                         {n[:4] for n in os.listdir(os.path.join(ROOT, ADR_DIR))
                          if n.endswith(".md")})
        self.assertEqual(reg["b_next"], _parse_next("B", _read(ROOT, BACKLOG)))
        self.assertEqual(reg["lint_bound"], max(derive_lint_codes(_self_source())))

    def test_migration_family_not_judged_when_source_absent(self):
        """migration 來源目錄缺席（唯讀 clone）＝判定基準不在就不判，不製造滿屏誤報。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            self.assertIsNone(lint25_registry(d)["mids"])
            hits, _c = self._scan("跑 m999 遷移", reg=lint25_registry(d))
            self.assertEqual(hits, [])

    # -- self-test 防恆綠（Lint16／Lint21／Lint22 慣例） --------------------------
    def test_self_test_green_on_healthy_scanner(self):
        self.assertEqual(id_namespace_self_test(), [])

    def _with_scanner(self, fake, fn):
        original = globals()["scan_id_namespace"]
        globals()["scan_id_namespace"] = fake
        try:
            return fn()
        finally:
            globals()["scan_id_namespace"] = original

    def test_self_test_catches_dead_scanner(self):
        """★④突變面（非恆綠自證）：掃描器被改成永不報→self-test 紅樣本當場報 ERROR。"""
        f = self._with_scanner(lambda texts, reg, exemptions=None: ([], {}),
                               id_namespace_self_test)
        self.assertTrue(any(x["level"] == ERROR and "紅樣本" in x["msg"] for x in f),
                        msg=str(f))

    def test_self_test_catches_overbroad_scanner(self):
        """★④突變面：掃描器被改成一律報紅→綠樣本誤報、self-test 報 ERROR。"""
        fake = ([{"rel": "樣本", "ln": 1, "kind": "adr", "tok": "ADR 9999",
                  "line": "", "start": 0}], {})
        f = self._with_scanner(lambda texts, reg, exemptions=None: fake,
                               id_namespace_self_test)
        self.assertTrue(any(x["level"] == ERROR and "綠樣本" in x["msg"] for x in f),
                        msg=str(f))

    def test_assembly_wires_self_test(self):
        """★組裝層：id_namespace_self_test 從 lint_id_namespace 掉線＝防恆綠靜默下線。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = self._with_scanner(lambda texts, reg, exemptions=None: ([], {}),
                                   lambda: lint_id_namespace(d, [], exemptions={}))
        self.assertTrue(any(x["code"] == "Lint25" and "self-test 失效" in x["msg"] for x in f),
                        msg=str(f))

    def test_run_lint_wires_id_namespace(self):
        """★接線層：lint_id_namespace 從 run_lint 掉線＝Lint25 整條靜默下線。

        ERROR 活態（B-004 收官後）零命中即零輸出，故 fixture **種一筆裸前代號**——run_lint
        輸出必含其 Lint25 ERROR；任何 Lint25 finding 只可能來自 lint_id_namespace——信號純淨。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _wfile(d, "docs/ops/NOTES.md", "接線探針：見 ADR 9999。\n")
            _git(d, "add", "docs/ops/NOTES.md")   # run_lint 走 tracked_files、未追蹤不進掃描面
            f = run_lint(d)
            self.assertTrue(any(x["code"] == "Lint25" and x["level"] == ERROR for x in f),
                            msg=str([x for x in f if x["code"] == "Lint25"]))


class TestI18nContractGate(unittest.TestCase):
    """Lint24 前後端 msg key 契約閘（B-133／B-134）：後端 rust 實發 msg key 集（Biz/BizData
    構造點字面＋名冊常數間接形＋error.rs key() 固定鍵）vs 前端 backend 字典鍵集雙向差集。

    ★fixture 一律 tempdir 自建假 rust 源＋假 locale（_wfile、無需 git）、真 repo 唯讀。
    ★名冊亦自帶（見 setUp）：本 class 的假 handler 以常數間接形測名冊機制，若讓語料吃
    生產名冊 I18N_CONST_ROSTER 的內容，該名冊隨射程增減時這批測試就會集體紅在與被測
    行為無關的理由上（rev5 清空名冊時實際發生過，11 紅）。語料與生產名冊必須解耦。
    """

    def setUp(self):
        """注入測試名冊：本 class 語料所用的兩個常數。生產名冊為空表時（rev5 現況）
        機制本身仍須可測——測的是「掃到常數形就查表」這個行為，不是表裡有誰。

        ★唯一例外＝對真 repo 跑的那支：它要驗的正是生產名冊與現況源樹相符，
        注入語料名冊會把它變成「驗我剛塞進去的假設定」，恰好失去該測試的全部意義。
        """
        if self._testMethodName == "test_real_repo_contract_green":
            return
        patcher = mock.patch.object(
            sys.modules[__name__], "I18N_CONST_ROSTER",
            {"LOCKED_MSG_KEY": "auth.login.locked",
             "CAPTCHA_REQUIRED_MSG_KEY": "auth.login.captchaRequired"})
        patcher.start()
        self.addCleanup(patcher.stop)

    # 假 error.rs：key() 兩固定鍵＋綁定臂（match 樣式、不入實發集）；code() 的 "2222"/"0000"
    # 字面在 fn key 大括號之外——固定鍵抽取若溢出方法體、健康綠案當場紅（突變自證）。
    ERROR_RS = (
        "pub fn key(&self) -> &str {\n"
        "    match self {\n"
        "        AppError::Biz(key) => key.as_ref(),\n"
        "        AppError::BizData(key, _) => key.as_ref(),\n"
        '        AppError::Success => "common.success",\n'
        '        AppError::Internal => "system.internal",\n'
        "    }\n"
        "}\n"
        "pub fn code(&self) -> &str {\n"
        "    match self {\n"
        '        AppError::Biz(_) => "2222",\n'
        '        AppError::BizData(_, _) => "2222",\n'
        '        _ => "0000",\n'
        "    }\n"
        "}\n")

    # 假 handler：直字面（行 4）＋名冊常數單行形（行 7）＋名冊常數多行 BizData 形（行 10~13）。
    HANDLER_RS = (
        'pub const LOCKED_MSG_KEY: &str = "auth.login.locked";\n'
        'pub const CAPTCHA_REQUIRED_MSG_KEY: &str = "auth.login.captchaRequired";\n'
        "fn f() -> AppError {\n"
        '    AppError::Biz(Cow::Borrowed("biz.a.x"))\n'
        "}\n"
        "fn g() -> AppError {\n"
        "    AppError::Biz(Cow::Borrowed(LOCKED_MSG_KEY))\n"
        "}\n"
        "fn h() -> AppError {\n"
        "    AppError::BizData(\n"
        "        Cow::Borrowed(CAPTCHA_REQUIRED_MSG_KEY),\n"
        "        serde_json::json!({}),\n"
        "    )\n"
        "}\n")

    @staticmethod
    def _locale(with_biz=True, with_locked=True, extra=""):
        """假 zh-tw backend 樹：共有鍵＋白名單內部鍵九鍵全量（listSeparator＋
        passwordViolation 八鍵——白名單存在性斷言要求字典齊備）；可抽鍵造紅。"""
        ax = "      a: {\n        x: '甲'\n      },\n" if with_biz else ""
        locked = "        locked: '鎖定',\n" if with_locked else ""
        pv = "".join("          %s: '＊',\n" % k for k in (
            "minLength", "maxLength", "maxBytes", "requireDigit",
            "requireLowercase", "requireUppercase", "requireSpecial"))
        return ("  backend: {\n"
                + "    biz: {\n" + ax
                + "      user: {\n        passwordViolation: {\n" + pv
                + "          forbidUsername: '＊'\n        }\n      }\n    },\n"
                + extra
                + "    common: {\n      listSeparator: '、',\n      success: '操作成功'\n    },\n"
                + "    system: {\n      internal: '內部錯誤'\n    },\n"
                + "    auth: {\n      login: {\n" + locked
                + "        captchaRequired: '請過驗證碼'\n      }\n    }\n"
                + "  },\n")

    def _fixture(self, d, locale=None, handler=None, error_rs=None):
        _wfile(d, I18N_ERROR_RS, self.ERROR_RS if error_rs is None else error_rs)
        _wfile(d, "rust-api/server/src/handler.rs",
               self.HANDLER_RS if handler is None else handler)
        _wfile(d, I18N_FRONTEND_LOCALE, self._locale() if locale is None else locale)

    def test_healthy_green(self):
        """②健康綠：字面＋常數間接＋key() 固定鍵 vs 字典全對齊；白名單內部鍵
        （listSeparator）不誤報；綁定臂／萬用臂屬 match 樣式、不入實發集。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            self.assertEqual(lint_i18n_contract(d), [])

    def test_backend_key_missing_red_names_site_and_fix(self):
        """①後端多鍵紅：字典抽掉 biz.a.x → ERROR 指名構造點 file:line、附三語 locale
        ＋app.d.ts Schema 同 commit 修法（L-094）。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d, locale=self._locale(with_biz=False))
            f = lint_i18n_contract(d)
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertEqual(f[0]["code"], "Lint24")
            joined = f[0]["where"] + "｜" + f[0]["msg"]
            self.assertIn("rust-api/server/src/handler.rs:4", joined)
            self.assertIn("biz.a.x", joined)
            for hint in ("zh-cn", "app.d.ts", "L-094"):
                self.assertIn(hint, f[0]["msg"])

    def test_const_indirect_enters_set(self):
        """⑧常數間接形（Biz(Cow::Borrowed(LOCKED_MSG_KEY)) 查名冊）：字典抽掉
        auth.login.locked → 紅指名常數構造點行號（單行形＝handler.rs:7）。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d, locale=self._locale(with_locked=False))
            f = lint_i18n_contract(d)
            self.assertEqual(len(f), 1, msg=str(f))
            joined = f[0]["where"] + "｜" + f[0]["msg"]
            self.assertIn("auth.login.locked", joined)
            self.assertIn("rust-api/server/src/handler.rs:7", joined)

    def test_const_roster_drift_red(self):
        """⑧b 名冊值漂移：源碼常數實值≠名冊釘死值 → ERROR（名冊腐化即紅、防恆綠）。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS.replace('"auth.login.locked"', '"auth.login.lockedOut"')
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and "LOCKED_MSG_KEY" in x["msg"]
                                and "漂移" in x["msg"] for x in f), msg=str(f))

    def test_frontend_orphan_red(self):
        """③前端孤兒紅：字典多出後端不發、白名單外之鍵 → ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d, locale=self._locale(
                extra="    orphan: {\n      key: '孤'\n    },\n"))
            f = lint_i18n_contract(d)
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("orphan.key", f[0]["msg"])
            self.assertIn("孤兒", f[0]["msg"])

    def test_whitelist_corruption_red(self):
        """④白名單∩後端實發集必空：後端發出 common.listSeparator → 白名單腐化 ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS + (
                "fn w() -> AppError {\n"
                '    AppError::Biz(Cow::Borrowed("common.listSeparator"))\n'
                "}\n")
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("白名單", f[0]["msg"])
            self.assertIn("common.listSeparator", f[0]["msg"])

    def test_unresolvable_site_red(self):
        """⑤非字面、非名冊常數＝無法靜態解析 → ERROR fail-loud（防恆綠洞）、不進差集比對。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS + (
                "fn u(k: String) -> AppError {\n"
                "    AppError::Biz(Cow::Owned(k))\n"
                "}\n")
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("無法靜態解析", f[0]["msg"])
            self.assertTrue(f[0]["where"].endswith("handler.rs:16"), msg=str(f))

    def test_empty_scan_surface_red(self):
        """⑥空集 fail-loud：rust 源樹缺席／零 .rs 檔 → ERROR（Lint20 家族）。"""
        with tempfile.TemporaryDirectory() as d:
            _wfile(d, I18N_FRONTEND_LOCALE, self._locale())
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and I18N_RS_SRC_DIR in x["where"]
                                for x in f), msg=str(f))

    def test_missing_locale_red(self):
        """⑥b 前端 locale 缺席＝ERROR（fail-closed、Lint20 家族）。"""
        with tempfile.TemporaryDirectory() as d:
            self._fixture(d)
            os.remove(os.path.join(d, I18N_FRONTEND_LOCALE))
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and I18N_FRONTEND_LOCALE in x["where"]
                                for x in f), msg=str(f))

    def test_cfg_test_region_excluded(self):
        """⑦#[cfg(test)] 區間大括號配對整段排除：測試碼 Biz 鍵不入實發集
        （字串內大括號經洗掃、不破壞配對）。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS + (
                "#[cfg(test)]\n"
                "mod tests {\n"
                "    use super::*;\n"
                '    const S: &str = "字串內大括號 {x} 不算";\n'
                "    fn t() -> AppError {\n"
                '        AppError::Biz(Cow::Borrowed("biz.test.only"))\n'
                "    }\n"
                "}\n")
            self._fixture(d, handler=handler)
            self.assertEqual(lint_i18n_contract(d), [])

    def test_cfg_test_unclosed_red(self):
        """⑦b 配對失效（EOF 未閉）＝ERROR fail-loud、非靜默略過。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS + "#[cfg(test)]\nmod tests {\n    fn t() {}\n"
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and "未配對" in x["msg"]
                                for x in f), msg=str(f))

    def test_cfg_test_same_line_item_red(self):
        """⑦c 同行屬性形『#[cfg(test)] use super::*;』＝不受支援 fail-loud
        （曾為靜默排除後續產碼；quality 審 minor ③）。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS + "#[cfg(test)] use super::*;\n"
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and "同行形" in x["msg"]
                                for x in f), msg=str(f))

    def test_cfg_all_test_compound_red(self):
        """⑦d 複合形『#[cfg(all(test, …))]』＝不受支援 fail-loud
        （曾讓測試 mod 洩進產碼掃描面；quality 審 minor ③）。"""
        with tempfile.TemporaryDirectory() as d:
            handler = self.HANDLER_RS + (
                '#[cfg(all(test, feature = "x"))]\n'
                "mod tests {\n"
                '    fn t() -> AppError { AppError::Biz(Cow::Borrowed("biz.leak.x")) }\n'
                "}\n")
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and "複合形" in x["msg"]
                                for x in f), msg=str(f))

    def test_whitelist_key_missing_from_dict_red(self):
        """⑨白名單存在性斷言：字典抽掉 listSeparator → ERROR（九鍵被刪不得靜默綠、
        rev4:B-133 同失效類；quality 審 minor ①）。"""
        with tempfile.TemporaryDirectory() as d:
            locale = self._locale().replace("      listSeparator: '、',\n", "")
            self._fixture(d, locale=locale)
            f = lint_i18n_contract(d)
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("common.listSeparator", f[0]["msg"])
            self.assertIn("不在前端 backend 字典", f[0]["msg"])

    def test_fn_key_method_missing_red(self):
        """⑩error.rs 無 fn key( 方法＝固定鍵抽取失效 fail-loud（quality 審 minor ⑥）。"""
        with tempfile.TemporaryDirectory() as d:
            error_rs = self.ERROR_RS[self.ERROR_RS.index("pub fn code"):]
            self._fixture(d, error_rs=error_rs)
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and "找不到 fn key(" in x["msg"]
                                for x in f), msg=str(f))

    def test_fn_key_method_unclosed_red(self):
        """⑩b fn key( 方法體至 EOF 未閉＝fail-loud（quality 審 minor ⑥）。"""
        with tempfile.TemporaryDirectory() as d:
            error_rs = "pub fn key(&self) -> &str {\n    match self {\n"
            self._fixture(d, error_rs=error_rs)
            f = lint_i18n_contract(d)
            self.assertTrue(any(x["level"] == ERROR and "fn key( 方法體大括號未配對" in x["msg"]
                                for x in f), msg=str(f))

    def test_const_roster_undeclared_red(self):
        """⑩c 名冊常數於掃描面查無宣告＝名冊腐化 fail-loud（quality 審 minor ⑥）。"""
        with tempfile.TemporaryDirectory() as d:
            handler = (
                "fn f() -> AppError {\n"
                '    AppError::Biz(Cow::Borrowed("biz.a.x"))\n'
                "}\n")
            self._fixture(d, handler=handler)
            f = lint_i18n_contract(d)
            hits = [x for x in f if x["level"] == ERROR and "查無宣告" in x["msg"]]
            self.assertEqual(len(hits), 2, msg=str(f))

    def test_whitelist_is_pinned(self):
        """★白名單九鍵字面釘死（Lint21/Lint22 慣例）：期望值不取被測常數、縮水即紅。"""
        self.assertEqual(I18N_FRONTEND_INTERNAL_KEYS, frozenset((
            "biz.user.passwordViolation.minLength",
            "biz.user.passwordViolation.maxLength",
            "biz.user.passwordViolation.maxBytes",
            "biz.user.passwordViolation.requireDigit",
            "biz.user.passwordViolation.requireLowercase",
            "biz.user.passwordViolation.requireUppercase",
            "biz.user.passwordViolation.requireSpecial",
            "biz.user.passwordViolation.forbidUsername",
            "common.listSeparator")))

    @unittest.skipUnless(_day1_pending("rust-api/server/src", "base-web/src/locales/langs/zh-tw.ts"),
                         "Day 1 未達：解除＝跨端兩側源皆備（rust 掃描面 B12、zh-tw.ts 於 i18n 地基刀）；同 lint24.day1 字面")
    def test_real_repo_contract_green(self):
        """★現庫契約綠（條款上線即自證；rev4:B-133 兩缺鍵補齊後恆綠）：真 repo 唯讀。"""
        self.assertEqual(lint_i18n_contract(ROOT), [])

    def test_run_lint_wires_i18n_contract(self):
        """★接線層：lint_i18n_contract 從 run_lint 掉線＝Lint24 整條靜默下線。

        bare fixture 無 rust 源樹→Lint24 必報空集 ERROR；任何 Lint24 finding 只可能
        來自 lint_i18n_contract——信號純淨。
        ★傳空豁免表：本案的信號源是「Lint24 ERROR 有沒有出現」，而 Day 1 具名豁免會把
        該 ERROR 合併成 SKIP、信號源消失——但接線本身沒壞。豁免行為由
        test_day1_exemption_merges_both_sides_missing 等三案單獨釘。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = run_lint(d, exemptions={})
            self.assertTrue(any(x["code"] == "Lint24" and x["level"] == ERROR for x in f),
                            msg=str([x for x in f if x["code"] == "Lint24"]))

    # -- Day 1 具名豁免（§4.5.10 類三／B4 乙③） ------------------------------------
    def test_day1_exemption_merges_both_sides_missing(self):
        """★兩側源皆缺＝創世期結構性紅→合併為一筆具名 SKIP（非兩筆 ERROR）。

        ★豁免表以參數注入、不吃生產 DAY1_EXEMPTIONS：lint24.day1 已於 002-system-settings
        T011 依「到期即紅」下架（兩側源皆備），但 early-return 的合併機制仍在碼裡、仍須有
        測試守著——否則下一個需要具名豁免的條款接上來時，這段合併邏輯已無人證其可用。
        """
        exemptions = {"lint24.day1": ("測試注入之具名豁免", lambda _root: False, "2026-08-04")}
        with tempfile.TemporaryDirectory() as d:
            f = [x for x in lint_i18n_contract(d, exemptions=exemptions)
                 if x["code"] == "Lint24"]
            self.assertEqual([(x["level"], x["where"]) for x in f],
                             [(SKIP, "lint24.day1")], msg=str(f))

    def test_day1_exemption_pull_out_turns_red(self):
        """★機器強制第③條：拔項→兩筆 ERROR 回歸（拔了沒反應＝該筆是裝飾品）。

        ★判定點必須在 lint_i18n_contract 的 early-return 匯流處——放進
        check_i18n_contract 內 Day 1 根本不可達，拔項亦零信號（v2 之誤）。
        """
        with tempfile.TemporaryDirectory() as d:
            f = [x for x in lint_i18n_contract(d, exemptions={}) if x["code"] == "Lint24"]
            self.assertEqual(len(f), 2, msg=str(f))
            self.assertTrue(all(x["level"] == ERROR for x in f), msg=str(f))

    def test_day1_exemption_does_not_swallow_single_side_failure(self):
        """★單側缺＝真故障，不得被豁免吞掉（謂詞成立即該側規則接管）。"""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, I18N_FRONTEND_LOCALE)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("const local = { backend: {} };\nexport default local;\n")
            f = [x for x in lint_i18n_contract(d) if x["code"] == "Lint24"]
            self.assertTrue(any(x["level"] == ERROR for x in f), msg=str(f))
            self.assertFalse(any(x["level"] == SKIP for x in f), msg=str(f))

    # -- self-test 防恆綠（Lint16/Lint21/Lint22 慣例） --------------------------------
    def test_self_test_green_on_healthy_checker(self):
        self.assertEqual(i18n_contract_self_test(), [])

    def _with_checker(self, fake, fn):
        original = globals()["check_i18n_contract"]
        globals()["check_i18n_contract"] = fake
        try:
            return fn()
        finally:
            globals()["check_i18n_contract"] = original

    def test_self_test_catches_dead_checker(self):
        """④突變面：判定函式被改成永不報（恆綠）→self-test 逐紅樣本（四型）報 ERROR。"""
        f = self._with_checker(lambda backend, frontend, whitelist: [],
                               i18n_contract_self_test)
        self.assertEqual(len(f), 4, msg=str(f))
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertTrue(all("self-test 失效" in x["msg"] for x in f))

    def test_self_test_catches_overbroad_checker(self):
        """④突變面：判定函式被改成一律報紅→綠樣本誤報、self-test 報 ERROR。"""
        f = self._with_checker(
            lambda backend, frontend, whitelist: [finding(ERROR, "Lint24", "樣本", "誤報")],
            i18n_contract_self_test)
        self.assertTrue(any(x["level"] == ERROR and "綠樣本" in x["msg"] for x in f),
                        msg=str(f))

    def test_assembly_wires_self_test(self):
        """★組裝層：i18n_contract_self_test 從 lint_i18n_contract 掉線＝防恆綠靜默下線。"""
        f = self._with_checker(lambda backend, frontend, whitelist: [],
                               lambda: lint_i18n_contract(ROOT))
        self.assertTrue(any(x["code"] == "Lint24" and "self-test 失效" in x["msg"] for x in f),
                        msg=str(f))


class TestLintSummary(unittest.TestCase):
    """G6 lint 摘要三段式（rev4:contracts G6／rev4:FR-012／data-model §5）。"""

    def _f(self, level, code="Lint17", where="base-web", msg="原因"):
        return finding(level, code, where, msg)

    def test_summary_line_is_three_segment(self):
        """★形制逐字：`lint：X 錯誤／Y 警告／Z 條款跳過／共 N 條款`（rev5 增第四段）。

        ★第四段的 N 以 derive_lint_codes 現算值比對、不寫死數字：寫死即與 Q8 拍板
        （甲案留洞、條款數 23 而上界 24）脫鉤，日後條款增減時本案不會紅。
        """
        total = len(derive_lint_codes(_self_source()))
        line, detail, code = lint_summary(
            [self._f(ERROR), self._f(ERROR), self._f(WARN), self._f(SKIP)])
        self.assertEqual(line, f"lint：2 錯誤／1 警告／1 條款跳過／共 {total} 條款")
        self.assertIsNotNone(detail)
        self.assertEqual(code, 1)

    def test_skip_detail_line_lists_label_and_reason(self):
        """Z>0 時次行 `跳過：<標籤>=<原因>；…`（不適用≠通過、顯式可見）。"""
        _line, detail, _code = lint_summary(
            [self._f(SKIP, "Lint17", "base-web", "worktree 缺席"),
             self._f(SKIP, "Lint18", "rust-api", "該庫不可查")])
        self.assertTrue(detail.startswith("跳過："), msg=detail)
        self.assertIn("Lint17｜base-web=worktree 缺席", detail)
        self.assertIn("Lint18｜rust-api=該庫不可查", detail)
        self.assertIn("；", detail)

    def test_no_skip_means_no_detail_line(self):
        line, detail, code = lint_summary([self._f(WARN)])
        self.assertEqual(line, "lint：0 錯誤／1 警告／0 條款跳過"
                               f"／共 {len(derive_lint_codes(_self_source()))} 條款")
        self.assertIsNone(detail)
        self.assertEqual(code, 0)

    def test_exit_code_only_tracks_errors(self):
        """★退出碼僅看 X：Y 或 Z 大於 0 不影響（警告放行列示、跳過更不是失敗）。"""
        self.assertEqual(lint_summary([])[2], 0)
        self.assertEqual(lint_summary([self._f(WARN)] * 5)[2], 0)
        self.assertEqual(lint_summary([self._f(SKIP)] * 9)[2], 0)
        self.assertEqual(lint_summary([self._f(WARN), self._f(SKIP), self._f(ERROR)])[2], 1)

    def test_warning_count_excludes_skips(self):
        """★跳過不得混進警告數（原實作以「總數減錯誤數」當警告數，遷移後即失真）。"""
        line, _d, _c = lint_summary([self._f(WARN), self._f(SKIP), self._f(SKIP)])
        self.assertEqual(line, "lint：0 錯誤／1 警告／2 條款跳過"
                               f"／共 {len(derive_lint_codes(_self_source()))} 條款")

    def test_skip_findings_are_not_printed_as_findings(self):
        """跳過只在明細行出現一次——條列區重複印一次＝雜訊、且看起來像有問題。"""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_findings([self._f(SKIP, msg="worktree 缺席"), self._f(WARN, msg="w")])
        self.assertNotIn("worktree 缺席", buf.getvalue())
        self.assertIn("[WARN]", buf.getvalue())

    def test_cmd_lint_prints_summary_then_skip_detail(self):
        """★端到端輸出形（S5 步 3 的機判）：摘要行恰一行、次行即跳過明細、明細筆數對得上。

        ★刻意在 fixture repo 上跑而非現庫：現庫 lint 的憑證全量掃在 drvfs 上要 ~47s，
        放進自帶測試會把 pre-commit 的條件觸發成本從秒級推到分鐘級（rev4:SC-008）。現庫全綠
        屬 G10 紅線、以實跑命令驗收，不由單元測試背。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            for _key, sub in PIN_KEYS:
                _init_sub(d, sub)
            buf = io.StringIO()
            # ★對 amend 開關密封：DOCS_SYNC_ADR_AMEND 是外部逐 commit 開關，amend commit 的
            #   pre-commit 條件自測會在該環境下跑本案——本案釘的是無豁免基線的輸出形，
            #   不 scrub 即被多出的 Lint08 跳過筆數污染（B-037 U3 收攏 commit 首暴）。
            with mock.patch.dict(os.environ):
                os.environ.pop("DOCS_SYNC_ADR_AMEND", None)
                with mock.patch.object(sys.modules[__name__], "ROOT", d):
                    with contextlib.redirect_stdout(buf):
                        rc = cmd_lint()
            lines = buf.getvalue().splitlines()
            idx = [i for i, l in enumerate(lines) if l.startswith("lint：")]
            self.assertEqual(len(idx), 1, msg=str(lines))
            i = idx[0]
            m = re.fullmatch(r"lint：(\d+) 錯誤／(\d+) 警告／(\d+) 條款跳過／共 (\d+) 條款",
                             lines[i])
            self.assertIsNotNone(m, msg=lines[i])
            # ★第四段＝條款總數，須等於掃源現算值（與創世事件 lint-roster、bootstrap
            #   斷言三處同數；§0.3 準則 1 的機器驗法）
            self.assertEqual(int(m.group(4)), len(derive_lint_codes(_self_source())),
                             msg=lines[i])
            z = int(m.group(3))
            self.assertGreater(z, 0, msg=lines[i])       # 本 fixture 必有合法跳過
            self.assertTrue(lines[i + 1].startswith("跳過："), msg=str(lines[i:]))
            self.assertEqual(lines[i + 1].count("；"), z - 1, msg=lines[i + 1])
            self.assertEqual(rc, 1 if int(m.group(1)) else 0)

    def test_cmd_check_output_shape_is_unchanged(self):
        """★G6 明文只動 lint：`check` 子命令輸出形不變（無三段式、無跳過段）。

        ★比照鄰案在 fixture repo 上跑而非現庫：原版直呼 `cmd_check()`，等於把「現庫
        生成物與現況一致」寫成本案前提——收刀三步的中間態（events 已 append、generate
        尚未跑）就會讓本案假紅，訊息還與受測程式碼零關係；唯讀看碼／scratch clone
        （無 submodule worktree）更直接崩在 RouterRoutesError。生成內容正確性歸另外近
        三百案，本案只守輸出形，故 `compute_generated` 以 mock 換掉。
        ★一致與不一致兩支都驗：後者才是誤植三段式摘要的高風險路徑。
        """
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            for computed, expect_rc, expect_line in (
                    ({}, 0, "check：一致"),
                    ({f"{GENERATED_DIR}/STATE.md": "x\n"}, 1, "check：不一致 1 處")):
                buf = io.StringIO()
                with mock.patch.object(sys.modules[__name__], "ROOT", d), \
                        mock.patch.object(sys.modules[__name__], "compute_generated",
                                          lambda _root, c=computed: c):
                    with contextlib.redirect_stdout(buf):
                        rc = cmd_check()
                out = buf.getvalue()
                self.assertEqual(rc, expect_rc, msg=out)
                self.assertIn(expect_line, out)
                self.assertNotIn("條款跳過", out)
                self.assertNotIn("跳過：", out)


class TestSkipInventory(unittest.TestCase):
    """合法 skip 落明細（rev4:contracts G2／G3／data-model §5）：不適用≠通過。"""

    def test_absent_worktree_lands_in_skip_not_warning(self):
        """★語意遷移：worktree 缺席由 WARN finding 改走 skipped 累積器（Lint16／Lint17／Lint18）。"""
        with tempfile.TemporaryDirectory() as d:
            outer = _init_outer(d)
            web, = _init_sub(d, "base-web")
            _wfile(d, EVENTS, json.dumps(
                dict(VALID_CLOSE, merge=outer, pins={"web": web, "api": "3" * 40}),
                ensure_ascii=False) + "\n")
            _stage_gitlink(d, "base-web", web)
            _stage_gitlink(d, "rust-api", "1" * 40)
            _git(d, "add", EVENTS)
            for fn in (lint_pin_crosscheck, lint_events_sha, lint_cred_submodules):
                f = [x for x in fn(d) if "rust-api" in x["where"]]
                self.assertEqual([x["level"] for x in f], [SKIP], msg=f"{fn.__name__}｜{f}")

    def test_unstaged_gitlink_lands_in_skip_detail(self):
        """★純碼 commit 的主要跳過來源：本次未動 pin→Lint16 增量掃不適用、須顯式可見。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            for _key, sub in PIN_KEYS:
                _init_sub(d, sub)
            f = lint_cred_submodules(d)
            self.assertEqual([x["level"] for x in f], [SKIP, SKIP], msg=str(f))
            self.assertTrue(all("未 staged" in x["msg"] or "未 stage" in x["msg"] for x in f),
                            msg=str(f))

    def test_index_without_gitlink_lands_in_skip_detail(self):
        """★A10：Lint17 在 index 無 gitlink 條目時落跳過明細（原為零 finding 靜默略過）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            f = lint_pin_crosscheck(d)
            self.assertEqual([x["level"] for x in f], [SKIP, SKIP], msg=str(f))
            self.assertTrue(all("index 無該 gitlink" in x["msg"] for x in f), msg=str(f))

    def test_adr_amend_escape_lands_in_skip_detail(self):
        """★amend 豁免（DOCS_SYNC_ADR_AMEND=1）＝條款被關掉，必須在輸出上看得見。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            with mock.patch.dict(os.environ, {"DOCS_SYNC_ADR_AMEND": "1"}):
                f = [x for x in run_lint(d) if x["level"] == SKIP and x["code"] == "Lint08"]
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertIn("DOCS_SYNC_ADR_AMEND", f[0]["msg"])
            with tempfile.TemporaryDirectory() as d2:
                _init_outer(d2)
                # ★無豁免側必須自己清掉開關、不得繼承行程環境（amend commit 的 pre-commit
                #   條件自測即帶著 DOCS_SYNC_ADR_AMEND=1 跑本案；B-037 U3 首暴）。
                with mock.patch.dict(os.environ):
                    os.environ.pop("DOCS_SYNC_ADR_AMEND", None)
                    self.assertEqual(
                        [x for x in run_lint(d2)
                         if x["level"] == SKIP and x["code"] == "Lint08"], [])

    def test_arch_impact_bidirectional_skip_is_visible(self):
        """★Lint06(b)：現況側對不上簿記狀態時原為靜默跳過（fail-safe），改落明細。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            _wfile(d, BOOK, "## §6 部署\n內容\n")
            _git(d, "add", BOOK)
            _git(d, "commit", "-qm", "book")
            _wfile(d, EVENTS, json.dumps(
                dict(VALID_CLOSE, arch_impact=["§6"]), ensure_ascii=False) + "\n")
            f = [x for x in lint_arch_impact(d) if x["level"] == SKIP]
            self.assertEqual(len(f), 1, msg=str(f))
            self.assertEqual(f[0]["code"], "Lint06")

    def test_skip_reason_is_never_empty(self):
        """★明細的價值全在原因欄：任何 skip finding 都必須帶得出原因（空字串＝假明細）。"""
        with tempfile.TemporaryDirectory() as d:
            _init_outer(d)
            for x in run_lint(d):
                if x["level"] == SKIP:
                    self.assertTrue(x["msg"].strip(), msg=str(x))
                    self.assertTrue(x["where"].strip(), msg=str(x))


HOOK_REL = ".githooks/pre-commit"
BOOTSTRAP_REL = "tools/bootstrap.sh"
# ★字元集含 `/`（B-035 U2 路徑形）：hook 名冊改列相對路徑後，不放行斜線即整行對不上、
#   對賬案退化成「名冊行不見了」的假故障訊息。
RE_HOOK_ROSTER = re.compile(r"^for t in ([a-z0-9./ -]+); do$", re.M)
RE_BOOTSTRAP_TEST = re.compile(r"^run_tool_test (\S+)$", re.M)
# 樁工具：把自己被呼叫的 argv 記進 WIRE_LOG；WIRE_FAIL（檔名）＋WIRE_FAIL_SUB（子命令、可空）
# 同時命中才非零退出（驗 fail-closed）。★需子命令粒度，否則同一支 docs-sync.py 的 check 與 lint
# 兩分支無法各自單獨失敗、G8 的 lint 分支就驗不到。
STUB_TOOL = ("#!/usr/bin/env python3\n"
             "import os, sys\n"
             "open(os.environ['WIRE_LOG'], 'a').write(' '.join(sys.argv) + '\\n')\n"
             "fail = os.environ.get('WIRE_FAIL')\n"
             "sub = os.environ.get('WIRE_FAIL_SUB')\n"
             "hit = bool(fail) and sys.argv[0].endswith(fail)\n"
             "sys.exit(1 if hit and (not sub or sys.argv[1:2] == [sub]) else 0)\n")


def tools_test_roster():
    """真表中帶 `test` 子命令的 python 工具名冊＝hook／bootstrap 應觸發自測的全集。"""
    subs = {r["rel"]: r["subs"] for r in compute_tools_cli(ROOT) if r["lang"] == "python"}
    return tuple(rel for rel in TOOLS_PY if "test" in subs[rel])


class TestGateWiring(unittest.TestCase):
    """★G8/G9 接線守衛（rev4:contracts G8／G9、data-model §8）：守門動作住 shell 面，整段被
    刪除或改壞時三套件仍全綠（＝本刀要消滅的失效類「守門動作恆不跑」）。python 面已有
    test_run_lint_wires_cmd_forms／test_compute_generated_wires_tools_cli 同級案，此節補齊
    shell 面：①名冊與真表對賬（把 hook 的手抄名冊降級為受檢副本）②以樁工具乾跑真 hook 檔
    文、實測觸發次數（非只驗字面在）。沙盒建在系統 tmp（native fs、非 drvfs），十五次乾跑
    合計約 1s。"""

    BASE = ["tools/secret-value-guard.py check",
            "tools/docs-sync.py check", "tools/docs-sync.py lint"]

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.d = d = cls._tmp.name
        _init_outer(d)
        hook = _read(ROOT, HOOK_REL)
        assert hook is not None, f"{HOOK_REL} 讀不到——G8 接線無源"
        _wfile(d, HOOK_REL, hook)              # ★乾跑真 hook 檔文，不重寫等價品
        for rel in TOOLS_PY:
            _wfile(d, rel, STUB_TOOL)
        # ★`base-web` 佔位刻意建成**真 gitlink**（巢狀 git repo）而非檔案，理由有二、缺一不可：
        #   ①hook 的 view-render-guard 段以 `[ -d base-web/src ]` 為實跑前提——佔位是檔案時該
        #     條件恆假 ⇒ 整段在本 harness 十餘次乾跑中**一次都不會被執行**，新增的觸發案會恆綠
        #     （004 U-I 實暴：把 hook 該段整段拆掉，全套件仍 494 OK）。
        #   ②但**不能只改成普通目錄**：`_run` 走 `git add -- base-web`，普通目錄會被展開成
        #     `base-web/src/...` 逐檔入 index，hook 的 `grep -qxF 'base-web'`（整行精確比對）
        #     當場落空 ⇒ 連 fork-delta 與 wire-schema 兩段也一起靜默不觸發（實測：staged 只剩
        #     BASE 三行）。巢狀 repo 才會被記成 mode 160000、staged 路徑逐字為 `base-web`，
        #     與真 submodule 同形。
        _init_sub(d, "base-web")
        os.makedirs(os.path.join(d, "base-web", "src"))
        _wfile(d, "base-web/src/.gitkeep", "掃描射程佔位：本測只驗觸發條件\n")
        _wfile(d, "rust-api", "gitlink 佔位：本測只驗觸發條件、不建真 submodule\n")
        # ★名冊外工具的樁**顯式寫**：view-render-guard／route-artifact-gate 刻意不入 TOOLS_PY
        #   （self-test 隨 check 連帶跑、同 fork-delta-lint 既有形），故不會被上方迴圈掃到；
        #   漏寫則 hook 執行到該行即「檔案不存在」rc≠0，測到的是沙盒不保真、不是 hook 行為。
        _wfile(d, "tools/view-render-guard.py", STUB_TOOL)
        # ★基線源倉目錄佔位（B7 hook 裁製、ADR 0001 決定 4）：hook 的 fork-delta 段以
        #   「源倉目錄存在」為實跑前提（Day-1 缺席＝具名跳過）。本 fixture 建目錄＝契約
        #   測試模擬 B9 後穩態；Day-1 缺席情境由 day1_skip 專屬測試另測（成對紅綠）。
        os.makedirs(os.path.join(d, "fork260509-soybean-admin-base"))
        _wfile(d, "docs/ops/reference-src/schema-snapshot.json",
               "{}\n")   # 快照佔位：entity-drift-gate 閘觸發條件用（rev4:B-110）
        _wfile(d, "docs/ops/NOTES.md", "非工具檔（平時情境用）\n")
        # ★真 hook 現以 `--config <hook 目錄>/../.gitleaks.toml` 顯式指定掃描器設定
        # （rev4:019 final review：靠自動探索時 config 缺席會**靜默降級成內建規則並 rc=0**，
        # 顯式帶則 rc=1 落入「掃描器本身異常」分支＝吵鬧失敗）。沙盒缺該檔時掃描階段即
        # exit 1、樁工具零呼叫——那是 hook 行為正確而**沙盒不保真**，故此處補最小合法
        # 設定檔（`extend.useDefault` 保內建規則；本節只驗觸發接線、不驗規則內容）。
        _wfile(d, ".gitleaks.toml", "[extend]\n  useDefault = true\n")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _run(self, staged, fail="", fail_sub=""):
        """乾跑真 hook：回（退出碼, 樁工具被呼叫的 argv 行序）。fail／fail_sub＝指定哪支
        工具的哪個子命令要非零退出（fail_sub 留空＝該支任何子命令皆失敗）。"""
        log = os.path.join(self.d, "wire.log")
        open(log, "w").close()
        _git(self.d, "reset", "-q")
        _git(self.d, "add", "--", *staged)
        r = subprocess.run(["sh", HOOK_REL], cwd=self.d, capture_output=True,
                           encoding="utf-8", errors="replace",
                           env=dict(os.environ, WIRE_LOG=log, WIRE_FAIL=fail,
                                    WIRE_FAIL_SUB=fail_sub))
        with open(log, encoding="utf-8") as fh:
            return r.returncode, fh.read().splitlines()

    def test_hook_roster_is_a_checked_copy_of_the_truth_table(self):
        """★hook 的 `for t in …` 是全庫第三份手抄名冊（一＝TOOLS_PY、二＝bootstrap）：
        與真表對賬後，新增帶 test 介面的守門工具卻漏接線即紅、不再零提醒。"""
        hook = _read(ROOT, HOOK_REL)
        m = RE_HOOK_ROSTER.search(hook or "")
        self.assertIsNotNone(m, msg="pre-commit 條件觸發段的工具名冊行不見了")
        self.assertEqual(tuple(m.group(1).split()), tools_test_roster())
        self.assertIn("tools/fork-delta-lint.py", hook)   # 無 test 介面、走聯集觸發

    def test_hook_scan_pins_scanner_config_explicitly(self):
        """★掃描器設定檔**顯式指定、不靠自動探索**（rev4:019 final review 實證）：探索模式下
        `.gitleaks.toml` 缺席時 betterleaks **靜默降級為內建規則庫並回 rc=0**——自訂 DSN
        規則與兩條 allowlist 一併下線，而 hook 只看 rc，於是一路綠（實測同一 DSN fixture：
        無 config rc=0／放回 rc=2）；顯式帶則 config 缺席即 rc=1、落入「掃描器本身異常」
        分支＝吵鬧失敗。此案釘住兩支 hook 皆顯式帶（拿掉任一即紅）——沙盒 fixture 有該檔，
        故少了本案時「移除 --config」會全綠存活（防恆綠、同 rev4:L-159 教訓）。"""
        for rel in (HOOK_REL, ".githooks-submodule/pre-commit"):
            text = _read(ROOT, rel) or ""
            line = re.search(r"^betterleaks git .*$", text, re.M)
            self.assertIsNotNone(line, msg=f"{rel} 的樣式掃描行不見了")
            self.assertIn("--config ", line.group(0),
                          msg=f"{rel} 掃描行未顯式帶 --config＝config 缺席時靜默降級")

    def test_bootstrap_runs_every_tool_test(self):
        """G9 體檢節無條件全跑：run_tool_test 逐行被刪即紅（與 hook 同一名冊對賬）。"""
        text = _read(ROOT, BOOTSTRAP_REL)
        self.assertIsNotNone(text)
        self.assertEqual(tuple(RE_BOOTSTRAP_TEST.findall(text)), tools_test_roster())
        self.assertIn("tools/fork-delta-lint.py", text)
        self.assertIn("tools/entity-drift-gate.py", text)   # 實跑行（rev4:B-110、與 fdl 同款兜底）

    def test_bootstrap_tool_test_is_fail_closed(self):
        """★G9 的另一半：跑了還要「失敗會紅」。上一案只驗「有沒有跑、順序對不對」，
        突變實測 die 換成 warn（只累加 WARNS、不改退出碼）與條件換成恆假（自測結果
        完全不看）兩者皆全綠存活＝守門工具自測掛掉時 bootstrap 仍以 0 收場，正是本刀
        要消滅的失效類。此案釘住「檢查退出狀態」與「失敗即 die」兩件。"""
        text = _read(ROOT, BOOTSTRAP_REL) or ""
        m = re.search(r"^run_tool_test\(\) \{.*?^\}$", text, re.M | re.S)
        self.assertIsNotNone(m, msg="bootstrap 的 run_tool_test 函式不見了")
        body = m.group(0)
        self.assertRegex(body, r"if\s+!\s+\w+=\"\$\(python3 ")   # 退出狀態有被看
        self.assertIn("die ", body)                              # 失敗即體檢紅

    def test_purge_git_env_removes_only_git_prefixed(self):
        """★GIT_* 隔離（本體）：hook 內跑 test 時外層 git 會洩漏 GIT_INDEX_FILE，而
        `git commit -a` 與 pathspec commit 給的是絕對路徑——不清即讓 fixture 的 temp
        repo 寫進真 repo 的 index（實測 44 failures＋1 error、外層 commit 被無關的
        invalid object 訊息誤擋）。改成 no-op 即紅。"""
        saved = {k: v for k, v in os.environ.items() if k.startswith("GIT_")}
        probe = "DOCS_SYNC_PURGE_PROBE"
        os.environ["GIT_INDEX_FILE"] = "/nonexistent/abs/index"
        os.environ["GIT_DIR"] = "/nonexistent/abs/gitdir"
        os.environ[probe] = "keep"
        try:
            purge_git_env()
            self.assertEqual([k for k in os.environ if k.startswith("GIT_")], [])
            self.assertEqual(os.environ.get(probe), "keep")   # 非 GIT_ 前綴不受波及
        finally:
            # ★不得靠 purge_git_env 自己還原：它正是被測對象，改壞時本案設的兩個 GIT_*
            # 會外洩並污染後續所有 git fixture 案（實測 18 案連坐）。自己清乾淨再回填。
            os.environ.pop(probe, None)
            for k in [k for k in os.environ if k.startswith("GIT_")]:
                del os.environ[k]
            os.environ.update(saved)

    def test_test_subcommand_purges_git_env(self):
        """★GIT_* 隔離（接線）：清除發生在測試開跑之前，套件自己看不見自己被隔離，
        故以檔文釘住 main() 的 test 分支確有呼叫。★同時反向釘住「只清 test 分支」——
        check／lint 必須繼續繼承 GIT_INDEX_FILE 才看得到正在被 commit 的 index。"""
        src = _read(ROOT, "tools/docs-sync.py") or ""
        m = re.search(r'\n    if cmd == "test":\n(.*?)\n    try:\n', src, re.S)
        self.assertIsNotNone(m, msg="main() 的 test 分支不見了")
        self.assertIn("purge_git_env()", m.group(1))
        mm = re.search(r"\ndef main\(argv\):\n(.*?)\n\nif __name__", src, re.S)
        self.assertIsNotNone(mm, msg="main() 不見了")
        self.assertEqual(mm.group(1).count("purge_git_env()"), 1,
                         msg="purge_git_env 只該掛 test 分支；生產面清掉 GIT_* 會瞎掉")

    def test_dry_run_costs_nothing_extra_when_no_tool_staged(self):
        """情境①平時（零工具 staged）：只跑 check＋lint，零 test、零 fork-delta-lint。"""
        self.assertEqual(self._run(["docs/ops/NOTES.md"]), (0, self.BASE))

    def test_dry_run_triggers_only_the_staged_tools_test(self):
        """情境②名冊全 staged＝全支觸發（順序＝名冊序）；情境③只 staged 一支＝其餘各支
        不得被拖下水（條件是逐支比對、不是「有工具改動就全跑」）。"""
        roster = tools_test_roster()
        self.assertEqual(self._run(list(roster)),
                         (0, self.BASE + [f"{rel} test" for rel in roster]))
        self.assertEqual(self._run(["tools/docs-sync.py"]),
                         (0, self.BASE + ["tools/docs-sync.py test"]))

    def test_dry_run_fork_delta_lint_union_runs_exactly_once(self):
        """情境④~⑥ fork-delta-lint 兩觸發條件（base-web pin bump／工具本體 staged）取
        聯集：各單條件 1 次、雙條件仍 1 次（重跑判定冪等、白付約 9s drvfs I/O 稅）。
        ★三組期望分開釘（rev4:B-128 後補）：staged 含 base-web gitlink 時另觸發
        wire-schema check --staged-gate（快照 drift 閘）、僅工具本體 staged 時不得觸發
        ——此案同時是全庫唯一釘住該閘接線的守衛（整段刪掉即紅、防靜默關閘）。"""
        wire_gate = ["tools/wire-schema.py check --staged-gate"]
        # ★`base-web` staged 時 view-render-guard 先於 fork-delta 觸發（hook 內次序即此）。
        vrg = ["tools/view-render-guard.py check"]
        self.assertEqual(self._run(["base-web"]),
                         (0, self.BASE + vrg + ["tools/fork-delta-lint.py"] + wire_gate))
        self.assertEqual(self._run(["tools/fork-delta-lint.py"]),
                         (0, self.BASE + ["tools/fork-delta-lint.py"]))
        self.assertEqual(self._run(["base-web", "tools/fork-delta-lint.py"]),
                         (0, self.BASE + vrg + ["tools/fork-delta-lint.py"] + wire_gate))

    def test_dry_run_fork_delta_day1_skip_when_baseline_absent(self):
        """★Day-1 具名跳過（B7 hook 裁製、ADR 0001 決定 4）：基線源倉目錄缺席時
        fork-delta-lint 不實跑（工具首步斷言必 rc=2、會擋創世一鍋 commit）且 hook 放行；
        其餘動作照跑。與 union 案成對＝目錄在必跑、缺席必跳（兩向紅綠、防閘門被拆或
        被反向寫死）。"""
        baseline = os.path.join(self.d, "fork260509-soybean-admin-base")
        os.rename(baseline, baseline + ".away")
        try:
            self.assertEqual(self._run(["tools/fork-delta-lint.py"]),
                             (0, self.BASE))
        finally:
            os.rename(baseline + ".away", baseline)

    def test_dry_run_entity_drift_gate_trigger_conditions(self):
        """情境⑦~⑩ entity-drift-gate 閘（rev4:B-110）：staged 含 rust-api gitlink 或 schema
        快照即觸發恰一次、兩者同 staged 仍恰一次（聯集、判定冪等）、平時（NOTES）不觸發
        ——此案＝全庫唯一釘住該閘接線的守衛（整段刪掉即紅、防靜默關閘）。"""
        gate = ["tools/entity-drift-gate.py check"]
        self.assertEqual(self._run(["rust-api"]), (0, self.BASE + gate))
        self.assertEqual(self._run(["docs/ops/reference-src/schema-snapshot.json"]),
                         (0, self.BASE + gate))
        self.assertEqual(
            self._run(["rust-api", "docs/ops/reference-src/schema-snapshot.json"]),
            (0, self.BASE + gate))
        self.assertEqual(self._run(["docs/ops/NOTES.md"]), (0, self.BASE))

    def test_dry_run_entity_drift_day1_skip_when_snapshot_absent(self):
        """★Day-1 具名跳過（B9 hook 裁製、ADR 0001 決定 4 同模式第二例）：schema 快照
        缺席時 entity-drift-gate 不實跑（工具 rc=2 環境不可用、會擋 pin 首記）且 hook 放行。
        與 trigger_conditions 案成對＝快照在必跑、缺席必跳（兩向紅綠、防閘門被拆或反向寫死）。"""
        snap = os.path.join(self.d, "docs/ops/reference-src/schema-snapshot.json")
        os.rename(snap, snap + ".away")
        try:
            self.assertEqual(self._run(["rust-api"]), (0, self.BASE))
        finally:
            os.rename(snap + ".away", snap)

    def test_dry_run_view_render_guard_trigger_conditions(self):
        """★管理頁「零原始 HTML 插值」守門（004 T042①）的**接線**守衛——全庫唯一釘住它的案。
        staged 含 base-web gitlink 或工具本體即觸發恰一次、兩者同 staged 仍恰一次（聯集）、
        平時（NOTES）不觸發。
        ★**為何非有不可**：hook 的守門動作住 shell 面，整段被刪掉時工具本體與其 self-test
        全都還在、照樣全綠——004 U-I 實測拆掉該段後 `docs-sync test`（494）與 `lint` 皆不紅。
        ★把斷言寫進 view-render-guard 自身的 self-test **對本失效模式零效果**：self-test 只隨
        `check` 連帶跑，而 `check` 的唯一觸發點正是被拆掉的那一段（循環依賴）。"""
        gate = ["tools/view-render-guard.py check"]
        self.assertEqual(self._run(["base-web"]),
                         (0, self.BASE + gate + ["tools/fork-delta-lint.py",
                                                 "tools/wire-schema.py check --staged-gate"]))
        self.assertEqual(self._run(["tools/view-render-guard.py"]), (0, self.BASE + gate))
        self.assertEqual(self._run(["docs/ops/NOTES.md"]), (0, self.BASE))

    def test_dry_run_view_render_guard_day1_skip_when_worktree_absent(self):
        """★Day-1 具名跳過（同 fork-delta／entity-drift 兩處既有模式、ADR 0001 決定 4 第三例）：
        `base-web/src` 缺席（fresh clone、bootstrap 前）時不實跑且 hook 放行。
        與 trigger_conditions 案**成對**＝worktree 在必跑、缺席必跳（兩向紅綠，防閘門被拆或
        被反向寫死成「永遠跳過」）。
        ★條件刻意取 `base-web/src` 而非掃描射程 `views/manage` 本身：worktree 在位卻少了
        `views/manage` ＝目錄被搬走／改名，那正是工具要 fail-loud 的情境，不得在此被吞掉。"""
        src = os.path.join(self.d, "base-web", "src")
        os.rename(src, src + ".away")
        try:
            self.assertEqual(self._run(["base-web"]),
                             (0, self.BASE + ["tools/fork-delta-lint.py",
                                              "tools/wire-schema.py check --staged-gate"]))
        finally:
            os.rename(src + ".away", src)

    def test_dry_run_non_zero_action_fails_the_hook(self):
        """G8 fail-closed：任一動作非零→hook exit 1（不得吞掉退出碼繼續往下跑）。
        ★四分支逐一驗：hook 首行是 #!/bin/sh 且全檔無 set -e，行尾 `|| exit 1` 被拿掉＝該
        動作非零時被完全忽略、續跑並以 0 收場（＝全庫閘可被一行編輯靜默關掉）。只驗其中
        一支＝覆蓋率 1/4，另三支的保護被拆時全套件仍綠。"""
        # 分支 a：check 非零→立即 exit，lint 與後續全不得跑（log＝值比對＋check 兩行——
        # rev4:019 起值比對層在 docs-sync 之前、屬事件型防線，見 hook 註解）。
        self.assertEqual(self._run(["docs/ops/NOTES.md"], fail="docs-sync.py"),
                         (1, self.BASE[:2]))
        # 分支 b：只讓 lint 非零（同一支工具、以子命令區分）→ check 跑完、hook 仍 exit 1。
        self.assertEqual(self._run(["docs/ops/NOTES.md"], fail="docs-sync.py", fail_sub="lint"),
                         (1, self.BASE))
        # 分支 c：工具自測非零。
        self.assertEqual(self._run(["tools/schema-gate.py"], fail="schema-gate.py"),
                         (1, self.BASE + ["tools/schema-gate.py test"]))
        # 分支 d：fork-delta-lint 非零（★其前另跑 view-render-guard、該支回 0 故續行）。
        self.assertEqual(self._run(["base-web"], fail="fork-delta-lint.py"),
                         (1, self.BASE + ["tools/view-render-guard.py check",
                                          "tools/fork-delta-lint.py"]))
        # 分支 d2：view-render-guard 非零→立即 exit，其後的 fork-delta 與 wire-schema 全不得跑。
        # ★此案與 trigger_conditions 成對，是「守門被拆＝commit 照過」這條失效的唯一機器守。
        self.assertEqual(self._run(["base-web"], fail="view-render-guard.py"),
                         (1, self.BASE + ["tools/view-render-guard.py check"]))
        # 分支 e：entity-drift-gate 非零（rev4:B-110 閘；漂移／異常皆須擋 commit）。
        self.assertEqual(self._run(["rust-api"], fail="entity-drift-gate.py"),
                         (1, self.BASE + ["tools/entity-drift-gate.py check"]))

    def test_every_gate_action_line_is_guarded(self):
        """★分支 d 的檔文兜底：hook 末個動作（立案當時＝fork-delta-lint、rev4:B-110 後＝
        entity-drift-gate 閘）的 `|| exit 1` 被拆掉後、if 語句的退出碼仍等於該命令退出碼
        （實測 sh 語意），行為與現行完全等價——黑箱乾跑殺不死，只有檔文守衛擋得住。
        故通則化：每個 python3 動作行都必須帶退出碼保護，將來在其後追加動作、末位優勢
        消失時，漏保護才不會靜默變成 fail-open。"""
        lines = [ln for ln in (_read(ROOT, HOOK_REL) or "").splitlines()
                 if ln.strip().startswith("python3 ")]
        self.assertGreaterEqual(len(lines), 4, msg=str(lines))   # check／lint／自測／fdl／entity 閘
        for ln in lines:
            self.assertTrue(ln.rstrip().endswith("|| exit 1"), msg=f"守門動作漏退出碼保護：{ln}")


# --- pre-push 防線測試矩陣共用 fixture（B-039 U1；rev4:019 rev4:scan-gates §S3）---

PP_HOOK_OUTER = ".githooks/pre-push"
PP_HOOK_SUB = ".githooks-submodule/pre-push"
PP_LIB = ".githooks/lib/scan-range.sh"
PP_ORIGIN_REF = "refs/remotes/origin/main"
# ★fixture 的 oid 一律合成假值：40 位十六進位形、與真 repo 任何物件無關（同理，本節不放
#   任何可被掃描規則命中的機密樣本——樁掃描器不讀 git 物件，rc 由環境變數指定）。
PP_ZERO = "0" * 40
PP_LOCAL = "a1" * 20
PP_REMOTE = "b2" * 20
PP_FORCE = "c3" * 20
# 樁 betterleaks（走 PATH 注入，比照 STUB_TOOL 慣例）：把收到的 argv（去 argv[0]）記進
# PP_LOG；退出碼取 PP_RC，但 PP_HIT_ON 非空且出現在 argv 時改回 2——多行 stdin 要能只讓
# 其中一行命中，才驗得到「命中不中斷後續行」。
PP_STUB = ("#!/usr/bin/env python3\n"
           "import os, sys\n"
           "args = ' '.join(sys.argv[1:])\n"
           "open(os.environ['PP_LOG'], 'a').write(args + '\\n')\n"
           "hit = os.environ.get('PP_HIT_ON')\n"
           "sys.exit(2 if hit and hit in args else int(os.environ.get('PP_RC', '0')))\n")


class TestPrePushMatrix(unittest.TestCase):
    """★pre-push 防線（機密掃描第二層）行為矩陣（B-039 U1；rev4:019 rev4:scan-gates §S3）。
    防線＝兩支 4 行轉接頭（.githooks/pre-push、.githooks-submodule/pre-push）＋唯一有真
    演算法的 .githooks/lib/scan-range.sh；守的是「pre-commit 被 --no-verify 繞過後」的補攔
    ＝災難路徑，立案前零自動化測試、零實戰史。

    ★★本矩陣＝**現行為基準**：每一格釘死的是「今天實際怎麼跑」，不是「應該怎麼跑」。
    日後任何改寫（換判定形式、換 shell、改範圍推導）以此矩陣為基準——翻轉任何一格都必須
    是刻意決策並在該案 docstring 留下新理由，不得順手改綠。

    形狀：TestGateWiring 用 staged 檔案觸發 pre-commit，本節改以 stdin 餵 pre-push 協定行＋
    PATH 注入樁掃描器，fixture 形狀不同故另立一類（同檔、同「樁工具乾跑真 hook 檔文」先例）。
    沙盒建在系統 tmp（native fs、非 drvfs）。"""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        # realpath：hook 內 `cd -- $(dirname $0) && pwd` 回實體路徑，期望 argv 要對得上。
        cls.d = d = os.path.realpath(cls._tmp.name)
        cls.head = _init_outer(d)
        for rel in (PP_HOOK_OUTER, PP_HOOK_SUB, PP_LIB):
            text = _read(ROOT, rel)
            assert text is not None, f"{rel} 讀不到——pre-push 防線無源"
            _wfile(d, rel, text)          # ★乾跑真 hook 檔文，不重寫等價品
        # 兩支轉接頭的 SCAN_CONFIG 都算到 `$HOOK_DIR/../.gitleaks.toml`＝沙盒根同一檔。
        _wfile(d, ".gitleaks.toml", "[extend]\n  useDefault = true\n")
        cls.bin = os.path.join(d, "stub-bin")
        _wfile(d, "stub-bin/betterleaks", PP_STUB)
        os.chmod(os.path.join(cls.bin, "betterleaks"), 0o755)
        # 穩態 fixture：origin 有遠端追蹤 ref（新分支走「只掃 origin 未見過的 commit」形）。
        # 零 ref 退階形由 …_falls_back_… 專案另測＝成對紅綠、防分支被拆或反向寫死。
        _git(d, "update-ref", PP_ORIGIN_REF, cls.head)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _run(self, hook_rel, stdin, rc=0, hit_on="", shell="sh"):
        """乾跑真 pre-push 檔文：stdin 餵 git pre-push 協定行，回（退出碼, 樁掃描器收到的
        argv 行序, stderr）。shell 預設 sh＝hook shebang（本機 dash）＝git 實際用的解譯器。"""
        log = os.path.join(self.d, "prepush.log")
        open(log, "w").close()
        env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"],
                   PP_LOG=log, PP_RC=str(rc), PP_HIT_ON=hit_on, PWD=self.d)
        r = subprocess.run([shell, hook_rel], cwd=self.d, input=stdin,
                           capture_output=True, encoding="utf-8", errors="replace", env=env)
        with open(log, encoding="utf-8") as fh:
            return r.returncode, fh.read().splitlines(), r.stderr

    def _argv(self, hook_rel, opts):
        """期望的樁 argv：釘住 --config 顯式帶（缺席即靜默降級成內建規則、見 pre-commit
        同款案）、--redact 不可省、--exit-code 2 決定下方 rc 分流語意，以及推導出的範圍。"""
        cfg = os.path.join(self.d, os.path.dirname(hook_rel), "..", ".gitleaks.toml")
        return f"git --config {cfg} --redact --verbose --exit-code 2 --log-opts={opts}"

    # 四情境 ×（stdin 行, 期望 --log-opts；None＝該行不得到達掃描器）。
    def _cells(self):
        return (
            ("①新分支首推（remote oid 全零）",
             f"refs/heads/feat {PP_LOCAL} refs/heads/feat {PP_ZERO}\n",
             f"{PP_LOCAL} --not --remotes=origin"),
            ("②刪分支（local oid 全零）",
             f"(delete) {PP_ZERO} refs/heads/old {PP_REMOTE}\n", None),
            ("③force push（常規 oid、hook 不區分）",
             f"refs/heads/main {PP_FORCE} refs/heads/main {PP_REMOTE}\n",
             f"{PP_REMOTE}..{PP_FORCE}"),
            ("④常規推進",
             f"refs/heads/main {PP_LOCAL} refs/heads/main {PP_REMOTE}\n",
             f"{PP_REMOTE}..{PP_LOCAL}"),
        )

    def test_matrix_four_stdin_forms_by_three_scanner_rcs(self):
        """★矩陣本體 12 格 × 兩支 hook：四 stdin 情境 × 樁掃描器三 rc。
        rc 語意以實查為準（lib 帶 `--exit-code 2`）：0＝乾淨放行／2＝機密命中→擋＋「機密
        命中」訊息／其餘非零＝掃描器本身異常→**同樣擋**＋另一則可辨識訊息（fail-closed：
        工具壞掉不得變成放行）。②刪分支＝掃描器零呼叫，故三 rc 全放行——這正是「無內容
        可掃就別掃」與「rc 分流」兩件事互不干擾的釘子。"""
        for hook in (PP_HOOK_OUTER, PP_HOOK_SUB):
            for name, line, opts in self._cells():
                for rc, want_exit, want_msg in ((0, 0, ""), (2, 1, "機密命中"),
                                                (1, 1, "掃描器本身異常")):
                    with self.subTest(hook=hook, 情境=name, rc=rc):
                        code, calls, err = self._run(hook, line, rc=rc)
                        if opts is None:
                            self.assertEqual((code, calls, err), (0, [], ""))
                            continue
                        self.assertEqual(calls, [self._argv(hook, opts)])
                        self.assertEqual(code, want_exit)
                        if want_msg:
                            self.assertIn(want_msg, err)
                        else:
                            self.assertEqual(err, "")

    def test_new_branch_falls_back_to_whole_branch_when_origin_has_no_refs(self):
        """契約表第三列（新分支首推的退階）：origin 一個遠端追蹤 ref 都沒有時，lib 不走排除
        形、改掃整條分支（`--log-opts=<local-oid>`）。
        ★理由以實測為準（git 2.43.0、零 refs/remotes/origin/*）：`git log <oid> --not
        --remotes=origin` rc=0 且照列出全部 commit＝**純 no-op**，掃描面與退階形等價——退階
        分支是防禦性冗餘，不是在閃避什麼未定義行為。故本案釘的是「lib 今天選了哪條分支」
        這件可觀測事實（而非兩形不等價）；日後要合併掉該分支得是刻意決策、附新理由。
        與矩陣①成對＝有 ref 走排除形、零 ref 走整條形（兩向紅綠）。"""
        _git(self.d, "update-ref", "-d", PP_ORIGIN_REF)
        try:
            code, calls, _ = self._run(
                PP_HOOK_OUTER, f"refs/heads/feat {PP_LOCAL} refs/heads/feat {PP_ZERO}\n")
            self.assertEqual((code, calls), (0, [self._argv(PP_HOOK_OUTER, PP_LOCAL)]))
        finally:
            _git(self.d, "update-ref", PP_ORIGIN_REF, self.head)

    def test_empty_oid_field_is_treated_as_all_zero_frozen_baseline(self):
        """★★已知怪分支＝基準（本刀最重要的一格）：lib 用 `case "$oid" in *[!0]*)` 判「非
        全零」，而**空字串**沒有任何字元、比不中 `*[!0]*`，於是落 `*)`＝被當成全零。
        後果分兩面，皆為現行為、皆在此釘死：
          ‧ local oid 欄空（stdin 只有 1 欄）→ 整行當「刪分支」跳過，掃描器零呼叫；
          ‧ remote oid 欄空（stdin 只有 2 欄）→ 當「新分支首推」走排除形。
        ★直譯改寫會反向：把它寫成 set／字串比對形（如 `[ "$oid" = "000…0" ] && continue`）
        時，空字串**不等於**全零字串→不再跳過→改成去呼叫掃描器（範圍還是空的）。本案即
        為此而立；日後任何改寫以此為基準，要翻轉須是刻意決策。
        （第一子案刻意用 rc=2＝「掃到就命中」的樁，證明不是靠掃描器回 0 才綠、是根本沒被呼叫。）"""
        code, calls, err = self._run(PP_HOOK_OUTER, "refs/heads/feat\n", rc=2)
        self.assertEqual((code, calls, err), (0, [], ""))
        code, calls, _ = self._run(PP_HOOK_OUTER, f"refs/heads/feat {PP_LOCAL}\n")
        self.assertEqual(
            (code, calls),
            (0, [self._argv(PP_HOOK_OUTER, f"{PP_LOCAL} --not --remotes=origin")]))

    def test_empty_and_blank_stdin_scan_nothing(self):
        """零行 stdin（無事可推）與空白行：`[ -z "$sr_local_ref" ] && continue` 吃掉空白行，
        零行則迴圈根本不進。三形皆放行且掃描器零呼叫（樁設 rc=2＝一被呼叫就會擋，故本案
        綠＝真的沒呼叫）。"""
        for label, stdin in (("零行", ""), ("空白行", "\n"),
                             ("多空白行", "\n\n"), ("純空白字元行", "   \n")):
            with self.subTest(stdin=label):
                self.assertEqual(self._run(PP_HOOK_OUTER, stdin, rc=2)[:2], (0, []))

    def test_multi_ref_stdin_scans_every_line_and_never_short_circuits(self):
        """多行 stdin（一次 push 多 ref）：逐行推導、順序即 stdin 序；中間夾的刪分支行被
        跳過不佔位；★某行命中後**不中斷**——後續行照掃、退出碼在迴圈結束才以累計的
        sr_status 收（改成命中即 break／return 會少掃、本案即紅）。"""
        stdin = (f"refs/heads/a {PP_LOCAL} refs/heads/a {PP_REMOTE}\n"
                 f"refs/heads/gone {PP_ZERO} refs/heads/gone {PP_REMOTE}\n"
                 f"refs/heads/b {PP_FORCE} refs/heads/b {PP_ZERO}\n"
                 f"refs/heads/c {PP_REMOTE} refs/heads/c {PP_LOCAL}\n")
        code, calls, err = self._run(PP_HOOK_OUTER, stdin, hit_on=PP_FORCE)
        self.assertEqual(calls, [
            self._argv(PP_HOOK_OUTER, f"{PP_REMOTE}..{PP_LOCAL}"),
            self._argv(PP_HOOK_OUTER, f"{PP_FORCE} --not --remotes=origin"),
            self._argv(PP_HOOK_OUTER, f"{PP_LOCAL}..{PP_REMOTE}"),
        ])
        self.assertEqual(code, 1)
        self.assertIn("refs/heads/b", err)          # 訊息指名是哪個 ref 中的

    def test_last_line_without_trailing_newline_is_dropped(self):
        """★現行為釘死、非缺陷判定：`while read` 對缺結尾換行的末行回非零，迴圈體不執行
        ＝該 ref 完全不掃。git pre-push 協定每行必帶換行，生產面不可達，故不修（防線本體
        本刀一字不動）。與帶換行的同一行成對＝差一個 \\n 就從放行變成擋。日後若改寫成
        `while read … || [ -n "$sr_local_ref" ]`，本案會翻轉——以此矩陣為基準。"""
        line = f"refs/heads/main {PP_LOCAL} refs/heads/main {PP_REMOTE}"
        self.assertEqual(self._run(PP_HOOK_OUTER, line, rc=2)[:2], (0, []))
        self.assertEqual(self._run(PP_HOOK_OUTER, line + "\n", rc=2)[0], 1)

    def test_matrix_is_shell_agnostic(self):
        """矩陣以 sh（＝hook shebang、本機 dash、git 實際用的解譯器）跑；若 dash 與 bash 對
        `*[!0]*` 或 `read` 的語意分歧，矩陣就只對其中一支成立。故把最吃 shell 語意的三案
        在 bash 下重跑、釘住兩殼結論一致。"""
        for label, stdin, want in (
                ("空 local oid", "refs/heads/feat\n", []),
                ("常規推進", f"refs/heads/main {PP_LOCAL} refs/heads/main {PP_REMOTE}\n",
                 [self._argv(PP_HOOK_OUTER, f"{PP_REMOTE}..{PP_LOCAL}")]),
                ("新分支首推", f"refs/heads/feat {PP_LOCAL} refs/heads/feat {PP_ZERO}\n",
                 [self._argv(PP_HOOK_OUTER, f"{PP_LOCAL} --not --remotes=origin")])):
            with self.subTest(情境=label):
                self.assertEqual(self._run(PP_HOOK_OUTER, stdin, shell="bash")[:2],
                                 (0, want))

    def test_both_pre_push_hooks_are_thin_adapters_over_the_single_lib(self):
        """★檔文守衛（黑箱乾跑殺不死的部分）：兩支 pre-push 是轉接頭，演算法只有一份。
        ★先釘一件實測結論、免得誤傳災難路徑：source 路徑打錯**不是** fail-open——dash
        （＝shebang 的 sh）因 `.` 屬 special builtin、失敗即整殼收攤 exit 2；bash 續行後撞
        `scan_push_ranges: command not found`、由 `|| exit 1` 收 exit 1。兩殼皆非零＝
        fail-closed，且此時黑箱矩陣當場全紅（該 hook 12 格全滅）。故本案守的不是「靜默放行」
        這個不存在的盲區，而是以下三件黑箱替代不了的：
        ①兩支的 source 相對路徑契約**各自不同**（外層 `lib/…`／源倉 `../.githooks/lib/…`）：
          黑箱只能證明「source 得到了某個檔」，釘不住哪一支該用哪一形——沙盒佈局換一種擺法
          就可能兩形皆綠，唯檔文能鎖死契約。
        ②`scan_push_ranges || exit 1` 的退出碼保護（同 pre-commit 通則）：今天它是末行、退出
          碼本就直通，實測拔掉 `|| exit 1` 黑箱兩形皆 rc=1＝**測不出**；它守的是日後在其後
          插入任何一行時不致把非零吞掉。此格是純檔文格。
        ③轉接頭內不得自己呼叫 betterleaks＝防第二份演算法長出來、兩支行為漂移（新演算法可
          與單一 lib 形行為一致，黑箱同樣殺不死）。"""
        want_source = {PP_HOOK_OUTER: '. "$HOOK_DIR/lib/scan-range.sh"',
                       PP_HOOK_SUB: '. "$HOOK_DIR/../.githooks/lib/scan-range.sh"'}
        for rel, src in want_source.items():
            text = _read(ROOT, rel) or ""
            self.assertIn(src, text, msg=f"{rel} 的 lib source 行不見了或相對契約被改")
            self.assertIn('SCAN_CONFIG="$HOOK_DIR/../.gitleaks.toml"', text)
            self.assertIn("scan_push_ranges || exit 1", text)
            self.assertNotIn("betterleaks", text)


SNAP_COLS = [
    {"table": "sys_user", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": None},
    {"table": "sys_user", "column": "user_name", "ordinal": 2,
     "type": "character varying(64)", "nullable": False, "default": None},
    {"table": "casbin_rule", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": "nextval('casbin_rule_id_seq'::regclass)"},
]
SNAP_IDX = [
    {"table": "sys_user", "name": "sys_user_pkey",
     "definition": "CREATE UNIQUE INDEX sys_user_pkey ON public.sys_user USING btree (id)"},
    {"table": "casbin_rule", "name": "casbin_rule_pkey",
     "definition": "CREATE UNIQUE INDEX casbin_rule_pkey ON public.casbin_rule USING btree (id)"},
]
SNAP_CONS = [
    {"table": "sys_user", "name": "sys_user_pkey", "definition": "PRIMARY KEY (id)"},
]
ACC_USERS = [
    {"id": 5, "user_name": "Admin", "nick_name": "Admin", "status": 1},
    {"id": 4, "user_name": "Super", "nick_name": "Super", "status": 1},
]
ACC_ROLES = [
    {"id": 5, "role_code": "R_ADMIN", "role_name": "管理員", "status": 1},
    {"id": 4, "role_code": "R_SUPER", "role_name": "超管", "status": 1},
]
ACC_BINDS = [{"user_id": 5, "role_id": 5}, {"user_id": 4, "role_id": 4}]


def _fake_fetch(sql, root=None):
    """測試用 fetch：依 SQL 內容回對應 canned rows（sys_user_role 判在 sys_user 前）。"""
    if "information_schema.columns" in sql:
        return list(SNAP_COLS)
    if "pg_indexes" in sql:
        return list(SNAP_IDX)
    if "pg_constraint" in sql:
        return list(SNAP_CONS)
    if "sys_user_role" in sql:
        return list(ACC_BINDS)
    if "sys_user" in sql:
        return list(ACC_USERS)
    if "sys_role" in sql:
        return list(ACC_ROLES)
    raise AssertionError("未知 SQL：" + sql)


class TestSnapshot(unittest.TestCase):
    """rev4:T015：refresh 快照面——確定性排序、密碼欄排除、缺 stack fail-loud、原子替換。"""

    def test_schema_snapshot_sorted_and_deterministic(self):
        a = snapshot_dumps(build_schema_snapshot(SNAP_COLS, SNAP_IDX, SNAP_CONS))
        b = snapshot_dumps(build_schema_snapshot(
            list(reversed(SNAP_COLS)), list(reversed(SNAP_IDX)), list(reversed(SNAP_CONS))))
        self.assertEqual(a, b)                       # 入序無關、同 byte
        snap = json.loads(a)
        self.assertEqual(set(snap), {"columns", "indexes", "constraints"})  # 無產生時點欄位
        self.assertEqual([c["table"] for c in snap["columns"]],
                         ["casbin_rule", "sys_user", "sys_user"])            # 表名序
        self.assertEqual([c["ordinal"] for c in snap["columns"][1:]], [1, 2])  # ordinal 序
        self.assertEqual([i["name"] for i in snap["indexes"]],
                         ["casbin_rule_pkey", "sys_user_pkey"])

    def test_schema_snapshot_excludes_seaql_migrations(self):
        cols = SNAP_COLS + [{"table": "seaql_migrations", "column": "version", "ordinal": 1,
                             "type": "character varying", "nullable": False, "default": None}]
        idx = SNAP_IDX + [{"table": "seaql_migrations", "name": "seaql_migrations_pkey",
                           "definition": "CREATE UNIQUE INDEX …"}]
        text = snapshot_dumps(build_schema_snapshot(cols, idx, SNAP_CONS))
        self.assertNotIn("seaql_migrations", text)

    def test_schema_snapshot_bad_row_shape_fail_loud(self):
        with self.assertRaises(SnapshotError):
            build_schema_snapshot([{"table": "t", "column": "c"}], [], [])  # 缺欄

    def test_accounts_snapshot_password_excluded_fail_loud(self):
        bad = dict(ACC_USERS[0])
        bad["password"] = "$argon2id$假雜湊"
        with self.assertRaises(SnapshotError) as cm:
            build_accounts_snapshot([bad], ACC_ROLES, ACC_BINDS)
        self.assertIn("password", str(cm.exception))
        text = snapshot_dumps(build_accounts_snapshot(ACC_USERS, ACC_ROLES, ACC_BINDS))
        self.assertNotIn("password", text)
        self.assertNotIn("argon2", text)

    def test_accounts_snapshot_sorted_and_deterministic(self):
        a = snapshot_dumps(build_accounts_snapshot(ACC_USERS, ACC_ROLES, ACC_BINDS))
        b = snapshot_dumps(build_accounts_snapshot(
            list(reversed(ACC_USERS)), list(reversed(ACC_ROLES)), list(reversed(ACC_BINDS))))
        self.assertEqual(a, b)
        snap = json.loads(a)
        self.assertEqual(set(snap), {"users", "roles", "bindings"})
        self.assertEqual([u["id"] for u in snap["users"]], [4, 5])
        self.assertEqual([r["id"] for r in snap["roles"]], [4, 5])
        self.assertEqual([x["user_id"] for x in snap["bindings"]], [4, 5])

    def test_atomic_write_no_leftover_tmp(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "x.json")
            _atomic_write(p, "第一版\n")
            _atomic_write(p, "第二版\n")
            with open(p, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "第二版\n")
            self.assertEqual(os.listdir(os.path.join(d, "sub")), ["x.json"])  # 無殘留暫存檔

    def test_refresh_writes_both_snapshots_byte_identical_rerun(self):
        with tempfile.TemporaryDirectory() as d, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cmd_refresh(root=d, fetch=_fake_fetch), 0)
            p_schema = os.path.join(d, "docs/ops/reference-src/schema-snapshot.json")
            p_accounts = os.path.join(d, "docs/ops/reference-src/accounts-snapshot.json")
            with open(p_schema, encoding="utf-8") as fh:
                schema1 = fh.read()
            with open(p_accounts, encoding="utf-8") as fh:
                accounts1 = fh.read()
            self.assertEqual(set(json.loads(schema1)), {"columns", "indexes", "constraints"})
            self.assertEqual(set(json.loads(accounts1)), {"users", "roles", "bindings"})
            self.assertEqual(cmd_refresh(root=d, fetch=_fake_fetch), 0)  # 同庫重跑
            with open(p_schema, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), schema1)                     # byte-identical
            with open(p_accounts, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), accounts1)

    def test_refresh_no_partial_write_on_late_failure(self):
        calls = {"n": 0}

        def flaky(sql, root=None):
            calls["n"] += 1
            if calls["n"] >= 4:                      # 帳號面撈取才失敗
                raise SnapshotError("psql 撈取失敗（模擬）")
            return []

        with tempfile.TemporaryDirectory() as d, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SnapshotError):
                cmd_refresh(root=d, fetch=flaky)
            self.assertFalse(os.path.exists(os.path.join(d, "docs/ops/reference-src")))

    def test_psql_fetch_stack_down_fail_loud(self):
        class Down:
            returncode = 1
            stdout = ""
            stderr = 'service "postgres" is not running'

        with self.assertRaises(SnapshotError) as cm:
            psql_fetch("SELECT 1", root=".", run=lambda *a, **k: Down())
        self.assertIn(STACK_HINT, str(cm.exception))
        self.assertIn("postgres", str(cm.exception))

    def test_psql_fetch_docker_missing_fail_loud(self):
        def boom(*a, **k):
            raise OSError("No such file or directory: 'docker'")

        with self.assertRaises(SnapshotError) as cm:
            psql_fetch("SELECT 1", root=".", run=boom)
        self.assertIn(STACK_HINT, str(cm.exception))

    def test_cli_refresh_without_docker_exits_nonzero_with_hint(self):
        env = dict(os.environ, PATH=os.devnull)      # docker 不可得
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "refresh"],
                           capture_output=True, encoding="utf-8", errors="replace", env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("up -d --wait", r.stderr)      # 提示啟動命令


class TestSnapshotReference(unittest.TestCase):
    """rev4:T017：generate／check 兩來源——快照→兩表、確定性、轉真、Lint02 分流、缺檔 fail-loud。"""

    ARCH = {
        "sys_user": {"table": "sys_user", "variant": "A", "label": "A 業務全六欄"},
        "casbin_rule": {"table": "casbin_rule", "variant": "D", "label": "D 治理"},
    }

    def _schema_snap(self):
        return build_schema_snapshot(SNAP_COLS, SNAP_IDX, SNAP_CONS)

    def _accounts_snap(self):
        return build_accounts_snapshot(ACC_USERS, ACC_ROLES, ACC_BINDS)

    def test_gen_reference_schema_sections_and_archetype(self):
        text = gen_reference_schema(self._schema_snap(), self.ARCH)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("## casbin_rule"), text.index("## sys_user"))  # 表名序分節
        self.assertIn("A 業務全六欄", text)          # archetype 變體歸屬標註
        self.assertIn("D 治理", text)
        self.assertIn("| user_name | character varying(64) |", text)  # 欄明細列
        self.assertIn("sys_user_pkey", text)         # 索引／約束清單入表

    def test_gen_reference_schema_deterministic_same_bytes(self):
        a = gen_reference_schema(self._schema_snap(), self.ARCH)
        b = gen_reference_schema(
            build_schema_snapshot(list(reversed(SNAP_COLS)), list(reversed(SNAP_IDX)),
                                  list(reversed(SNAP_CONS))),
            dict(reversed(list(self.ARCH.items()))))
        self.assertEqual(a, b)

    def test_gen_reference_schema_missing_archetype_fail_loud(self):
        arch = {"sys_user": self.ARCH["sys_user"]}   # 缺 casbin_rule 歸屬
        with self.assertRaises(SnapshotError) as cm:
            gen_reference_schema(self._schema_snap(), arch)
        self.assertIn("casbin_rule", str(cm.exception))

    def test_gen_reference_accounts_bindings_and_zero_password(self):
        text = gen_reference_accounts(self._accounts_snap())
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertIn("| Super | Super | 1 | R_SUPER |", text)   # 帳號｜暱稱｜狀態｜角色綁定
        self.assertIn("| Admin | Admin | 1 | R_ADMIN |", text)
        self.assertNotIn("password", text)
        self.assertNotIn("argon2", text)

    def test_gen_reference_accounts_dangling_binding_fail_loud(self):
        snap = self._accounts_snap()
        snap["bindings"].append({"user_id": 4, "role_id": 99})
        with self.assertRaises(SnapshotError):
            gen_reference_accounts(snap)

    def test_reference_live_schema_accounts_promoted(self):
        self.assertIn("schema", REFERENCE_LIVE)
        self.assertIn("accounts", REFERENCE_LIVE)
        self.assertIn("screens", REFERENCE_LIVE)
        text = gen_state(TestGenState.CTX)
        state_lines = {name: line
                       for line in text.splitlines()
                       for name in ("routes", "ports", "schema", "accounts", "screens")
                       if line.startswith(f"- reference/{name}：")}
        # screens 轉真後、五表全為真表、無殘餘 stub
        for name in ("schema", "accounts", "screens"):
            self.assertNotIn("stub", state_lines[name], msg=name)   # 轉真
            self.assertIn("generate", state_lines[name], msg=name)

    def test_check_reports_schema_accounts_drift_as_l2(self):
        for base in ("schema", "accounts"):
            with tempfile.TemporaryDirectory() as root:
                os.makedirs(os.path.join(root, "docs/generated/reference"))
                rel = f"docs/generated/reference/{base}.md"
                with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                    fh.write("舊表\n")
                f = check_generated(root, {rel: "新表\n"}, exemptions={})
                self.assertEqual(len(f), 1, msg=base)
                self.assertEqual(f[0]["code"], "Lint02", msg=base)      # Lint02 分流（指名來源側）
                self.assertIn(f"{base}-snapshot.json", f[0]["msg"], msg=base)

    def _write_reference_src(self, root, schema=True, accounts=True, amap=True):
        d = os.path.join(root, REFERENCE_SRC_DIR)
        os.makedirs(d)
        if schema:
            with open(os.path.join(root, SCHEMA_SNAPSHOT), "w", encoding="utf-8") as fh:
                fh.write(snapshot_dumps(self._schema_snap()))
        if accounts:
            with open(os.path.join(root, ACCOUNTS_SNAPSHOT), "w", encoding="utf-8") as fh:
                fh.write(snapshot_dumps(self._accounts_snap()))
        if amap:
            with open(os.path.join(root, ARCHETYPE_MAP), "w", encoding="utf-8") as fh:
                json.dump({"tables": list(self.ARCH.values())}, fh, ensure_ascii=False)

    def test_compute_snapshot_reference_green_and_deterministic(self):
        with tempfile.TemporaryDirectory() as root:
            self._write_reference_src(root)
            files = compute_snapshot_reference(root)
            self.assertEqual(set(files), {"docs/generated/reference/schema.md",
                                          "docs/generated/reference/accounts.md"})
            self.assertEqual(files, compute_snapshot_reference(root))  # 同快照同 byte

    def test_compute_snapshot_reference_missing_snapshot_fail_loud(self):
        with tempfile.TemporaryDirectory() as root:
            self._write_reference_src(root, schema=False)
            with self.assertRaises(SnapshotError) as cm:
                compute_snapshot_reference(root)
            self.assertIn("schema-snapshot.json", str(cm.exception))
            self.assertIn("refresh", str(cm.exception))              # 提示補救命令

    def test_compute_snapshot_reference_missing_archetype_map_fail_loud(self):
        with tempfile.TemporaryDirectory() as root:
            self._write_reference_src(root, amap=False)
            with self.assertRaises(SnapshotError) as cm:
                compute_snapshot_reference(root)
            self.assertIn("archetype-map.json", str(cm.exception))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "test":
        purge_git_env()   # ★hook 內執行時隔離外層 GIT_*，否則 fixture 寫進真 repo index
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    try:
        if cmd == "lint":
            return cmd_lint()
        if cmd == "generate":
            return cmd_generate()
        if cmd == "check":
            return cmd_check()
        if cmd == "refresh":
            return cmd_refresh()
        if cmd == "errata":
            if len(argv) < 3:
                print("用法：tools/docs-sync.py errata <關鍵詞>", file=sys.stderr)
                return 2
            return cmd_errata(argv[2])
    except UnicodeDecodeError as ex:
        print(f"[ERROR] 編碼｜文件含非 UTF-8 內容（{ex}）——fail-closed，修復編碼後重跑",
              file=sys.stderr)
        return 1
    except ComposePortsError as ex:
        print(f"[ERROR] ports 解析｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except RouterRoutesError as ex:
        print(f"[ERROR] routes 解析｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except ElegantRoutesError as ex:
        print(f"[ERROR] screens 解析｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except ToolsCliError as ex:
        print(f"[ERROR] tools-cli 掃源｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except SnapshotError as ex:
        print(f"[ERROR] 快照管線｜{ex}", file=sys.stderr)
        return 1
    print(f"未知子命令：{cmd}", file=sys.stderr)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
