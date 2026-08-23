#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/seed-view-gate.py — seed `sys_menu.component` 之 `view.*` 集 ⊆ 前端 view 集對賬閘（B-088／spec 006 FR-049／T025）

子命令：
  check   （預設，無參數等同之）解析 rust-api seed 的 `SEED_SYS_MENU` 字串內全部 `view.*` 字面
          → 依 elegant-router 規則自 base-web/src/views/** 導出 view 鍵集 → 兩者對賬；缺漏即非零
          退出、逐鍵指名（含 seed 檔行號與 sys_menu 列 id）
  test    只跑自帶 self-test（離線、毫秒級、合成 fixtures 於 tempfile）

★**為何非有不可**——後端 seed 的 `sys_menu.component`（`view.manage_user` 這形）是側欄選單項與
前端頁面之間**唯一**的綁定，而它只是一個字串：seed 加一列指向不存在的 view、或前端搬走／改名一支
view 而忘了動 seed，兩向都**零紅**——側欄照樣長出該項、點下去零反應（URL 不變、無 404 頁、無
console error、無 toast；B-008 之 2026-08-17 CDP 實測），連未翻譯的 i18n 原始鍵都直接上畫面。
B-088 立案時 seed 列 9／10／77 三支即屬此態、三張頁全在 base-web 缺席而全套閘綠。

★**刪掉它會怎樣**：上述兩向失配回到「靠人記得」；`BASE-WEB-MANAGE-PAGE-WIRING` 軌道會頻繁動到
view 檔（新增／搬移／改名），每一次都是一個無訊號的斷裂點。★**改壞被測物會怎樣**：把
`base-web/src/views/manage/policy-archive/` 整個搬走（或在 seed 補一列指向 `view.nope`）→ 本閘當場紅並
指名 `view.manage_policy-archive`（或 `view.nope`）與 seed 檔行號——那正是下方 self-test 每次執行都
重演一遍的合成情境、亦是落地當日真檔暫改實跑過的情境（ADR 0024 決定①③）。

════════ 判準兩端獨立＋結構自證（ADR 0024 決定②） ════════

  seed 集 ＝ `rust-api/migration/src/m002_baseline_seeds.rs` 之 `const SEED_SYS_MENU` 字串**塊內**
            全部 `\\bview\\.[A-Za-z0-9_-]+` 字面（去重；`layout.base$view.home` 那形亦收；塊外的
            `view.*` 不收——`UNSEED_SYS_MENU`／註解／其他 seed 都不是選單綁定）
  views 集＝ `base-web/src/views/**` 依 elegant-router 0.3.8 **預設**規則導出（`build/plugins/router.ts`
            未覆寫 pageDir／pagePatterns／pageExcludePatterns、已逐字讀過）：
              頁檔＝`**/index.vue` 與 `**/[param].vue`；`**/components/**` 排除；
              鍵＝目錄段以 `_` 連、以 `_` 起首的目錄段不入鍵（`_builtin` 為現行唯一實例）、
              全小寫；`[param].vue` 之鍵＝所在目錄（參數只進 path 不進鍵）；`modules/*.vue`、
              `*.ts` 非頁檔、天然不產鍵。
  兩集來自兩棵互不相干的樹（rust seed 檔 vs 前端檔案系統），違規時只動一邊、不共變。
  ★**結構自證**：導出集 MUST 恰等於 `base-web/src/router/elegant/imports.ts` 之 `views` 匯入鍵集
  （外掛真跑過的產物；兩向差集即紅、訊息「推導失真或產物未重算」）——證本檔的導出規則對得上
  外掛實跑結果、同時攔「加了 view 卻沒讓外掛重算／沒 commit 產物」；imports.ts 缺席＝fail-loud。
  ★方向是**單向包含**（seed ⊆ views）、不是相等：`hide_in_menu` 頁、尚未 seed 的 view（login）都是
  合法的不對稱（B-088 原文）。

════════ 具名豁免與到期語意（B-088 拍板／FR-049） ════════

  `EXEMPT` 常數表恰兩列＝B-008 餘兩張尚未兌現的 view（seed 列 9 `view.manage_system-settings`、
  列 77 `view.manage_audit`）、各附 B-008 指針。★**到期即紅**：被豁免鍵的 view 一旦存在（導出集
  命中）即紅、逼人摘掉該列——豁免只能縮、不能養；★**幽靈亦紅**：豁免鍵已不在 seed 集＝掛空擋、
  同樣逼摘。★「恰兩列＋各附 B-008 指針」與「表不得取自輸入（args／env／讀檔）」這兩條不變式是
  **機器強制**的、不是註解裡的一句話——self-test 案 I 四根釘死：I-a 斷言 `EXEMPT` 鍵集恰為那兩鍵、
  且每個值含「B-008 餘兩張 view」字面；I-b 斷言 `cmd_check` 內 `run_gate` 的第四實參逐字＝`EXEMPT`
  （呼叫點先併一份外來表再傳＝當場紅）；I-c 斷言判定路徑諸函式源碼零 env／argv／json／stdin 取值
  形，且四支判定函式另零 `open(` 字面（`run_gate` 內讀檔擴充豁免＝當場紅；`cmd_check` 正當讀兩支
  真檔、故不入此列）；I-d 斷言 `cmd_check` 全文只出現一次 `EXEMPT` 字面（＝I-b 那個實參），封鎖
  「`self_test()` 之後就地 `EXEMPT.update(…)`」——該形佈線沒動、常數快照也已照過，I-a／I-b 皆管不到。
  ★四根互不覆蓋、缺一即留一條繞道：I-a 殺不掉「呼叫點合併一份拷貝」（常數本身沒動）、I-b 殺不掉
  「常數表養第三列」（佈線本身沒動）、I-c／I-d 各封一條讀檔擴充路（前者在判定函式內、後者在呼叫端
  就地——兩形皆曾以 rc=0 實測漏網、補釘後轉紅）。★射程自陳（不誇大）：I-c／I-d 封的是**字面取值
  形**＝「摘紅燈最省事的那幾條路」；刻意繞開字面（getattr 拼字串、以 os.listdir 拼表）仍須靠 I-b 的
  原封佈線＋人審，不是形式證明。self-test 注入合成表只為驗「豁免機制本身」會紅會綠，CLI 無任何旗標可改表。

★**掃到空集＝異常**（`EmptyScanError`、rc 2）：seed 塊內零 `view.*`、views 目錄零頁檔、imports.ts
缺席或零鍵——一支只會「找不到缺漏」的對賬器在任一邊空掉時會安靜地永遠綠燈，那是恆綠失效的
標準形；本閘在該情形下 fail-loud。worktree 未就位（seed 檔／views 目錄整個缺席）亦 rc 2。

退出碼：0 綠／1 紅（缺漏鍵、豁免到期或幽靈、導出≠imports——訊息逐鍵列出）／2 結構故障／64 用法錯。

落點與接線（T025；★逐處寫出、不寫「大致補完了」）：
  ①`.githooks/pre-commit` 條件觸發段：staged 含 `base-web` 或 `rust-api` gitlink（pin bump）或本檔
    自身時跑 `check`；`base-web/src` 或 `rust-api/migration` 缺席＝具名跳過（Day-1 模式、同
    view-render-guard 段）。self-test 每次隨 `check` 連帶跑（防恆綠），故本檔**不進** pre-commit 的
    `for t in …` 自測迴圈＝`tools/docs-sync.py` 之 `HOOK_TEST_LOOP_EXEMPT` 具名豁免（同
    view-render-guard；入迴圈＝staged 時緊接 check 再重複跑一次 test、零新增覆蓋）。
  ②`tools/docs-sync.py` `TOOLS_PY` 真表已納冊（tools-cli 真表自本檔頭子命令段與分派表掃源）。
  ③`tools/bootstrap.sh` `run_tool_test tools/seed-view-gate.py`（體檢節無條件全跑、離線毫秒級）。
  ④`README.md` tools 目錄樹已列本檔（Lint27 對賬）。
  ⑤**未接（T025 允許清單外、已升級主線）**：`docs/ops/RUNBOOK.md` §12 工具表與 §12.1 條件觸發段表
    （含「具名豁免 1 支」字樣）、`docs-sync.py` `TestGateWiring` 之本檔觸發條件乾跑案（沙盒的
    `rust-api` 佔位現為檔案、本段在沙盒永遠走跳過分支）。
"""
import inspect
import os
import re
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEED_REL = os.path.join("rust-api", "migration", "src", "m002_baseline_seeds.rs")
VIEWS_REL = os.path.join("base-web", "src", "views")
IMPORTS_REL = os.path.join("base-web", "src", "router", "elegant", "imports.ts")

# seed 字串塊的起訖（rust raw string；塊外一律不掃）。
SEED_BLOCK_HEAD = 'const SEED_SYS_MENU: &str = r#"'
SEED_BLOCK_TAIL = '"#;'
RE_VIEW_TOKEN = re.compile(r"\bview\.([A-Za-z0-9_-]+)")
RE_SEED_ROW_ID = re.compile(r"^\((\d+),")

# elegant-router 預設（0.3.8；router.ts 未覆寫）：頁檔形＋排除目錄＋隱藏層前綴。
RE_PAGE_PARAM = re.compile(r"^\[\w+\]\.vue$")
PAGE_INDEX = "index.vue"
EXCLUDE_DIRS = ("components",)
HIDDEN_DIR_PREFIX = "_"

# imports.ts 的 `views` 匯入鍵（裸鍵或雙引號鍵）：`  manage_menu: () => import(`／`  "manage_ip-rule": () => import(`。
RE_IMPORT_KEY = re.compile(r'^\s+(?:"([^"]+)"|([A-Za-z0-9_$-]+)):\s*\(\)\s*=>\s*import\(', re.M)

# 具名豁免（B-088 拍板、spec 006 FR-049）：鍵＝seed component 字面；值＝指針（為何暫容、何時摘）。
# ★到期即紅／幽靈亦紅／不得取自輸入——語意見檔頭「具名豁免與到期語意」段。
# ★本表內容（恰兩列、各附 B-008 指針）由 self-test 案 I-a 機器釘死：養第三列＝self-test 當場紅，
#   要養就得連同改一行斷言、在 diff 裡現形（＝拍板級可見）——豁免只能縮、不能養不是勸告。
EXEMPT = {
    "view.manage_system-settings": "B-008 餘兩張 view（seed 列 9 manage_system-settings；頁面兌現後摘列）",
    "view.manage_audit": "B-008 餘兩張 view（seed 列 77 manage_audit；頁面兌現後摘列）",
}


class EmptyScanError(Exception):
    """掃描面空集或結構缺席——對賬實質下線（恆綠失效），fail-loud。"""


def parse_seed_views(seed_text):
    """seed 檔全文 → {`view.x`: [(行號, 列 id|None), …]}（只掃 SEED_SYS_MENU 塊內；零 token 即 raise）。"""
    found = {}
    in_block = False
    for lineno, line in enumerate(seed_text.splitlines(), 1):
        if not in_block:
            if not line.startswith(SEED_BLOCK_HEAD):
                continue
            in_block = True
        m = RE_SEED_ROW_ID.match(line)
        row_id = int(m.group(1)) if m else None
        for key in RE_VIEW_TOKEN.findall(line):
            found.setdefault("view." + key, []).append((lineno, row_id))
        if SEED_BLOCK_TAIL in line:
            break
    if not in_block:
        raise EmptyScanError(f"seed 檔內找不到 `{SEED_BLOCK_HEAD}` 塊")
    if not found:
        raise EmptyScanError("SEED_SYS_MENU 塊內零個 view.* 字面")
    return found


def derive_view_keys(views_root):
    """base-web/src/views 樹 → {鍵: 相對頁檔路徑}（elegant-router 預設規則；零頁檔即 raise）。"""
    out = {}
    for dirpath, dirnames, filenames in os.walk(views_root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        rel_dir = os.path.relpath(dirpath, views_root)
        parts = [] if rel_dir == os.curdir else rel_dir.split(os.sep)
        for name in sorted(filenames):
            if name != PAGE_INDEX and not RE_PAGE_PARAM.match(name):
                continue
            key = "_".join(p for p in parts if not p.startswith(HIDDEN_DIR_PREFIX)).lower()
            out[key] = "/".join(parts + [name])
    if not out:
        raise EmptyScanError(f"{views_root} 底下零個頁檔（index.vue／[param].vue）")
    return out


def parse_imports_keys(imports_text):
    """imports.ts 全文 → `views` 匯入鍵集（零鍵即 raise）。"""
    keys = {a or b for a, b in RE_IMPORT_KEY.findall(imports_text)}
    if not keys:
        raise EmptyScanError("imports.ts 內零個 `() => import(` 匯入鍵——產物檔空殼或形制已變")
    return keys


def run_gate(seed_text, views_root, imports_text, exempt):
    """純判定：→ (rc, 訊息行列)；rc 0 綠／1 紅。EmptyScanError 往上拋（呼叫端轉 rc 2）。"""
    seed = parse_seed_views(seed_text)
    views = derive_view_keys(views_root)
    imports_keys = parse_imports_keys(imports_text)
    view_tokens = {"view." + k for k in views}
    lines = []

    # ③ 結構自證：導出集恰等 imports.ts 鍵集（兩向）。
    only_derived = sorted(set(views) - imports_keys)
    only_imports = sorted(imports_keys - set(views))
    if only_derived or only_imports:
        lines.append(f"[seed-view-gate] ✗ views 導出集 ≠ {IMPORTS_REL} 鍵集——推導失真或產物未重算：")
        for k in only_derived:
            lines.append(f"  導出有、imports.ts 無：{k}（{views[k]}）——外掛未重算／產物未 commit？")
        for k in only_imports:
            lines.append(f"  imports.ts 有、導出無：{k}——頁檔已搬走／改名，或本檔導出規則與外掛脫節？")

    # ④ 對賬：seed ∖ views ∖ 豁免 ＝ 空即綠。
    missing = sorted(k for k in seed if k not in view_tokens and k not in exempt)
    if missing:
        lines.append(f"[seed-view-gate] ✗ seed view.* 有 {len(missing)} 鍵無對應 view"
                     f"（{VIEWS_REL}/** 導出集缺；B-088）：")
        for k in missing:
            where = "、".join(f"{SEED_REL}:{ln}（列 {rid}）" if rid is not None else f"{SEED_REL}:{ln}"
                              for ln, rid in seed[k])
            lines.append(f"  {k}  ←  {where}")
        lines.append("  補救：補上該 view（外掛重算產物同 commit）、或自 seed 摘該列；暫容＝拍板級、"
                     "走 BACKLOG 指針進本檔 EXEMPT。")

    # ⑤ 豁免到期守：被豁免鍵的 view 已存在＝到期；已不在 seed＝幽靈；兩者皆紅、逼摘。
    expired = sorted(k for k in exempt if k in view_tokens)
    ghosts = sorted(k for k in exempt if k not in seed)
    for k in expired:
        lines.append(f"[seed-view-gate] ✗ 豁免到期：{k} 的 view 已存在，請自 EXEMPT 摘列（{exempt[k]}）")
    for k in ghosts:
        lines.append(f"[seed-view-gate] ✗ 幽靈豁免：{k} 已不在 seed view.* 集，請自 EXEMPT 摘列（{exempt[k]}）")

    if lines:
        return 1, lines
    active = sorted(k for k in exempt if k in seed)
    lines.append(f"[seed-view-gate] ✓ seed view.* {len(seed)} 鍵皆有 view"
                 f"（豁免 {len(active)}：{'、'.join(active) or '無'}；導出 {len(views)} 鍵＝imports.ts 鍵集；"
                 f"self-test 過）")
    return 0, lines


# ── self-test（離線、毫秒級；每次 check 連帶跑）──────────────────────────────────

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _fx_views(tmp, name, pages):
    """合成 views 樹：pages＝相對頁檔路徑清單；回樹根。"""
    root = os.path.join(tmp, name, "views")
    os.makedirs(root, exist_ok=True)
    for rel in pages:
        _write(os.path.join(root, rel), "<template><div /></template>\n")
    return root


def _fx_imports(keys):
    """合成 imports.ts（形照外掛產物：裸鍵／需引號鍵混用、另有 layouts 區塊作雜訊）。"""
    lines = ["// Generated by elegant-router", "export const layouts = {", "  base: BaseLayout,", "};",
             "export const views = {"]
    for k in sorted(keys):
        lit = k if re.fullmatch(r"[A-Za-z0-9_$]+", k) else f'"{k}"'
        lines.append(f'  {lit}: () => import("@/views/{k}/index.vue"),')
    lines.append("};")
    return "\n".join(lines) + "\n"


def _fx_seed(rows, extra_before="", extra_after=""):
    """合成 seed 檔：rows＝[(列 id, component 欄字面)]；塊外可夾雜訊（證塊外不收）。"""
    body = [SEED_BLOCK_HEAD + 'INSERT INTO "sys_menu" ("id", "component") VALUES']
    for rid, comp in rows:
        body.append(f"({rid}, '2026-01-01', '{comp}', 'route.x'),")
    body[-1] = body[-1][:-1] + ";" + SEED_BLOCK_TAIL
    return extra_before + "\n".join(body) + "\n" + extra_after


def self_test():
    """紅綠成對；失敗即 AssertionError。案名見各段首行註解（A~H 合成 fixtures；I 對的是本檔自身；兩向差集案拆 D1／D2 各自單向）。"""
    with tempfile.TemporaryDirectory() as tmp:
        # A 正例：seed 有鍵、views 缺 ⇒ 紅且指名該鍵＋行號＋列 id；在場的鍵不得被點名。
        seed = _fx_seed([(3, "view.a_b"), (5, "view.c_d")])
        views = _fx_views(tmp, "A", ["a/b/index.vue"])
        rc, lines = run_gate(seed, views, _fx_imports(["a_b"]), {})
        text = "\n".join(lines)
        assert rc == 1, f"self-test A：缺 view 未紅（rc={rc}）\n{text}"
        assert "view.c_d" in text and "列 5" in text and ":3" in text, \
            f"self-test A：紅訊息未指名缺漏鍵／seed 行號／列 id\n{text}"
        assert "view.a_b" not in text, f"self-test A：在場鍵被誤點名\n{text}"

        # B 負例：全在 ⇒ 綠（證不是見檔就紅的恆紅品）。
        seed = _fx_seed([(3, "view.a_b"), (4, "layout.base$view.c_d")])
        views = _fx_views(tmp, "B", ["a/b/index.vue", "c/d/index.vue"])
        rc, lines = run_gate(seed, views, _fx_imports(["a_b", "c_d"]), {})
        assert rc == 0 and "2 鍵皆有 view" in "\n".join(lines), f"self-test B：全在卻非綠\n{lines}"

        # C1 豁免生效：缺的那鍵在豁免表 ⇒ 綠且訊息列出豁免。
        seed = _fx_seed([(3, "view.a_b"), (9, "view.c_d")])
        views = _fx_views(tmp, "C1", ["a/b/index.vue"])
        rc, lines = run_gate(seed, views, _fx_imports(["a_b"]), {"view.c_d": "B-xxx 指針"})
        text = "\n".join(lines)
        assert rc == 0 and "豁免 1" in text and "view.c_d" in text, f"self-test C1：豁免未生效\n{text}"

        # C2 豁免到期：被豁免鍵的 view 已存在 ⇒ 紅並指名（逼摘）。
        views = _fx_views(tmp, "C2", ["a/b/index.vue", "c/d/index.vue"])
        rc, lines = run_gate(seed, views, _fx_imports(["a_b", "c_d"]), {"view.c_d": "B-xxx 指針"})
        text = "\n".join(lines)
        assert rc == 1 and "到期" in text and "view.c_d" in text, f"self-test C2：豁免到期未紅\n{text}"

        # C3 幽靈豁免：豁免鍵已不在 seed ⇒ 紅並指名。
        views = _fx_views(tmp, "C3", ["a/b/index.vue"])
        rc, lines = run_gate(_fx_seed([(3, "view.a_b")]), views, _fx_imports(["a_b"]),
                             {"view.zz": "B-xxx 指針"})
        text = "\n".join(lines)
        assert rc == 1 and "幽靈" in text and "view.zz" in text, f"self-test C3：幽靈豁免未紅\n{text}"

        # D1／D2 結構自證：導出集 ≠ imports.ts 鍵集 ⇒ 紅、且**該向**自己被指名。
        # ★兩向必須是**兩組各自單向的 fixture**、絕不可併成一組雙向 fixture：併成一組時，判定式
        #   `if only_derived or only_imports:` 一旦退化成任一單向（`if only_derived:` 或
        #   `if only_imports:`）都仍能全綠存活——實測兩個變異體跑 `test` 皆 rc=0，而檔頭自陳的主要
        #   用途「攔產物未重算」（only_derived 那向）就此變成靜默綠燈，等於 ADR 0024①「每條規則
        #   各自證明會紅」只證了一半。同型失效形 tools/view-render-guard.py 的 COUNTEREXAMPLES
        #   上方註解已兩度記載（多個變體綁在一個 any(...) → 規則改窄仍全綠），此處循同一紀律。
        # D1 導出多出向（＝加了 view 卻沒讓外掛重算／產物未 commit）：only_derived 非空、only_imports 空。
        views = _fx_views(tmp, "D1", ["a/b/index.vue", "c/d/index.vue"])
        rc, lines = run_gate(_fx_seed([(3, "view.a_b")]), views, _fx_imports(["a_b"]), {})
        text = "\n".join(lines)
        assert rc == 1 and "推導失真或產物未重算" in text and "導出有、imports.ts 無：c_d" in text, \
            f"self-test D1：導出多出（產物未重算）未紅或未指名該向\n{text}"
        assert "imports.ts 有、導出無" not in text, \
            f"self-test D1：只有導出多出、卻報了反向差集\n{text}"

        # D2 imports 多出向（＝頁檔已搬走／改名，或導出規則與外掛脫節）：only_imports 非空、only_derived 空。
        views = _fx_views(tmp, "D2", ["a/b/index.vue"])
        rc, lines = run_gate(_fx_seed([(3, "view.a_b")]), views, _fx_imports(["a_b", "e_f"]), {})
        text = "\n".join(lines)
        assert rc == 1 and "推導失真或產物未重算" in text and "imports.ts 有、導出無：e_f" in text, \
            f"self-test D2：imports 多出（頁檔已搬走／規則脫節）未紅或未指名該向\n{text}"
        assert "導出有、imports.ts 無" not in text, \
            f"self-test D2：只有 imports 多出、卻報了反向差集\n{text}"

        # E 空集 fail-loud（三面各一）：seed 零 view.*／views 零頁檔／imports 零鍵。
        for label, args in (
                ("seed 零 view.*", (_fx_seed([(1, "layout.base")]), _fx_views(tmp, "E1", ["a/b/index.vue"]),
                                  _fx_imports(["a_b"]), {})),
                ("views 零頁檔", (_fx_seed([(1, "view.a_b")]), _fx_views(tmp, "E2", ["a/b/modules/x.vue"]),
                                 _fx_imports(["a_b"]), {})),
                ("imports 零鍵", (_fx_seed([(1, "view.a_b")]), _fx_views(tmp, "E3", ["a/b/index.vue"]),
                                 "export const views = {\n};\n", {}))):
            try:
                run_gate(*args)
            except EmptyScanError:
                pass
            else:  # pragma: no cover - 只有守門壞掉才會走到
                raise AssertionError(f"self-test E：{label} 未 fail-loud＝恆綠失效未被擋")

        # F 導出規則逐形釘死（外掛預設：_ 起首層剝除／[param]／components 排除／非頁檔／小寫／保留 - 與 _）。
        views = _fx_views(tmp, "F", [
            "_builtin/403/index.vue", "_builtin/iframe-page/[url].vue", "manage/ip-rule/index.vue",
            "manage/user-detail/[id].vue", "multi-menu/first_child/index.vue", "Plugin/Map/index.vue",
            "plugin/map/components/index.vue", "manage/role/modules/role-search.vue",
            "manage/menu/modules/shared.ts", "home/index.vue"])
        got = derive_view_keys(views)
        want = {"403": "_builtin/403/index.vue", "iframe-page": "_builtin/iframe-page/[url].vue",
                "manage_ip-rule": "manage/ip-rule/index.vue",
                "manage_user-detail": "manage/user-detail/[id].vue",
                "multi-menu_first_child": "multi-menu/first_child/index.vue",
                "plugin_map": "Plugin/Map/index.vue", "home": "home/index.vue"}
        assert got == want, f"self-test F：導出規則失真\n實得 {got}\n應得 {want}"

        # G seed 解析：塊外 token 不收、同鍵多列去重並各記行號、列 id 解析。
        seed = _fx_seed([(10, "view.p_q"), (12, "view.p_q"), (13, "layout.base$view.r")],
                        extra_before="/// 註解裡的 view.outside 不算\n",
                        extra_after='const OTHER: &str = r#"view.other"#;\n')
        got = parse_seed_views(seed)
        assert set(got) == {"view.p_q", "view.r"}, f"self-test G：seed 集失真 {sorted(got)}"
        assert [rid for _, rid in got["view.p_q"]] == [10, 12], f"self-test G：列 id／去重失真 {got}"
        assert all(ln > 1 for ln, _ in got["view.p_q"]), f"self-test G：行號未以檔為基準 {got}"

        # H imports 鍵解析：裸鍵／引號鍵／數字鍵全收，layouts 區塊不收。
        keys = parse_imports_keys(_fx_imports(["403", "manage_menu", "manage_ip-rule"]))
        assert keys == {"403", "manage_menu", "manage_ip-rule"}, f"self-test H：imports 鍵集失真 {keys}"

    # I 具名豁免的兩條不變式（★機器強制，非註解裡的一句話）——不進 tempdir、對的是本檔自身。
    # ★為何非有不可：A~H 全案的 `exempt` 一律由測試自己餵合成表，模組級 `EXEMPT` 常數與「cmd_check
    #   只准把該常數原封傳進 run_gate」這條佈線**從未被任何一案碰到**（機器數：self-test 帶內
    #   `grep -c EXEMPT` 曾為 0）。於是摘紅燈有四條零反應的繞道：①養第三列豁免蓋掉真缺頁
    #   ②在呼叫點先併一份 env／argv 來的表再傳 ③在 run_gate 內就地讀檔擴充傳進來的表
    #   ④在 cmd_check 的 self_test() 之後就地 EXEMPT.update(讀檔結果)。★四條互不覆蓋——I-a 殺不掉
    #   ②③④（常數沒動／快照已照過）、I-b 殺不掉①③（佈線沒動）——故各釘一根，缺一即留門。
    # I-a 常數表釘死：鍵集恰兩列（B-088 拍板／FR-049）、每列各附 B-008 指針。
    assert set(EXEMPT) == {"view.manage_system-settings", "view.manage_audit"}, (
        "self-test I-a：EXEMPT 鍵集非 B-088 拍板的恰兩列——養豁免是拍板級（須連同改本行斷言），"
        f"實得 {sorted(EXEMPT)}")
    for _k, _why in sorted(EXEMPT.items()):
        assert "B-008 餘兩張 view" in _why, \
            f"self-test I-a：豁免 {_k} 的值缺 B-008 指針字面（沒指針＝沒人知道何時能摘）：{_why!r}"

    # I-b 呼叫點佈線：cmd_check 內恰一處 run_gate 呼叫、第四實參逐字＝模組級常數 EXEMPT。
    _calls = [" ".join(a.split()) for a in re.findall(r"run_gate\(([^)]*)\)", inspect.getsource(cmd_check))]
    assert _calls == ["seed_text, views_root, imports_text, EXEMPT"], (
        "self-test I-b：cmd_check 未把 EXEMPT 原封傳進 run_gate（先併一份外來表再傳＝繞道口），"
        f"實得 {_calls}")

    # I-c 取值形封鎖：判定路徑諸函式源碼零 env／argv／json／stdin 取值形（self_test 本身除外——
    #     它注入合成表是測試自身職責，且必然含下列字面）；四支判定函式另封 `open(`——它們的輸入
    #     一律由 cmd_check 讀好餵進來，自己開檔即繞道口（實測漏網形：run_gate 內
    #     `exempt = dict(exempt); exempt.update({… for l in open(_p)})`，無 env／json 字面故舊版全綠）。
    #     `cmd_check` 正當讀 seed／imports 兩支真檔，故它不入 `open(` 那列、改由 I-d 各別釘死。
    for _fn in (parse_seed_views, derive_view_keys, parse_imports_keys, run_gate, cmd_check):
        _src = inspect.getsource(_fn)
        _toks = ("environ", "getenv", "argv", "json", "input(")
        if _fn is not cmd_check:
            _toks += ("open(",)
        for _tok in _toks:
            assert _tok not in _src, \
                f"self-test I-c：{_fn.__name__}() 出現取值形 {_tok!r}——判定與豁免表不得取自輸入"

    # I-d 就地改表封鎖：cmd_check 全文只准出現一次 `EXEMPT` 字面（＝I-b 那個第四實參）。第二次出現
    #     ＝在呼叫前就地改常數表（實測漏網形：`self_test()` 之後 `EXEMPT.update({… for l in open(_p)})`
    #     ——佈線逐字沒動騙過 I-b、常數快照在 self_test 當下已照過騙過 I-a）。
    _exempt_hits = len(re.findall(r"\bEXEMPT\b", inspect.getsource(cmd_check)))
    assert _exempt_hits == 1, (
        "self-test I-d：cmd_check 內 `EXEMPT` 字面出現 "
        f"{_exempt_hits} 次（應恰 1＝傳進 run_gate 的第四實參）——多出的那次＝呼叫前就地改豁免表，"
        "豁免只能縮、不能養")

    # ★I-c／I-d 射程自陳：封的是字面取值形，非形式證明；繞開字面者靠 I-b 原封佈線＋人審。


def cmd_check():
    """實跑：self-test → 讀真檔 → 對賬。"""
    self_test()
    seed_path = os.path.join(REPO_ROOT, SEED_REL)
    views_root = os.path.join(REPO_ROOT, VIEWS_REL)
    imports_path = os.path.join(REPO_ROOT, IMPORTS_REL)
    for rel, path, kind in ((SEED_REL, seed_path, os.path.isfile), (VIEWS_REL, views_root, os.path.isdir),
                            (IMPORTS_REL, imports_path, os.path.isfile)):
        if not kind(path):
            print(f"[seed-view-gate] ✗ {rel} 缺席——worktree 未就位或被搬移；對賬在該情形下不得靜默放行"
                  f"（rc 2）", file=sys.stderr)
            return 2
    with open(seed_path, encoding="utf-8") as fh:
        seed_text = fh.read()
    with open(imports_path, encoding="utf-8") as fh:
        imports_text = fh.read()
    try:
        rc, lines = run_gate(seed_text, views_root, imports_text, EXEMPT)
    except EmptyScanError as ex:
        print(f"[seed-view-gate] ✗ {ex}——對賬實質下線（恆綠失效），請確認兩側掃描面是否被搬移／改名"
              f"（rc 2）", file=sys.stderr)
        return 2
    print("\n".join(lines), file=sys.stderr if rc else sys.stdout)
    return rc


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "test":
        self_test()
        print("[seed-view-gate] ✓ self-test 過（A 缺 view 紅＋指名／B 全在綠／C1 豁免生效綠／C2 豁免到期紅／"
              "C3 幽靈豁免紅／D1 導出多出紅／D2 imports 多出紅／E 三面空集 fail-loud／F 導出規則逐形／"
              "G seed 塊內解析／"
              "H imports 鍵解析／I 豁免常數表恰兩列＋呼叫點原封佈線＋取值形封鎖＋就地改表封鎖）")
        return 0
    if cmd != "check":
        print(f"用法：{argv[0]} [check|test]", file=sys.stderr)
        return 64
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
