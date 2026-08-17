#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/view-render-guard.py — 管理頁「零原始 HTML 插值」機器守（spec 004 FR-038）

子命令：
  check   （預設，無參數等同之）掃 base-web/src/views/manage/** 之全部前端原始碼，
          命中任一原始 HTML 注入用法即非零退出、逐處指名檔:行:字面
  test    只跑自帶 self-test（離線、毫秒級）

★**為何非有不可**——管理頁的自由文字欄（本刀的 IP 規則備註欄是第一個，稽核管理頁的
轉發鏈欄會是下一個）承載的是**使用者與攻擊者可寫的原文**。Vue 的預設插值（`{{ }}`／JSX
子節點）會逸出標記字元，是安全的；只要有人把某一格改成原始 HTML 注入形（模板指令、DOM
屬性、或 `document` 上的插入 API），那一格就從「顯示字面」變成「執行標記」，而**畫面上
看不出差別**——備註寫純文字時兩者渲染結果一模一樣，要等到有人存進一段帶事件處理器的
標記才會爆，且爆的是別人的瀏覽器。這種缺陷 code review 抓不穩（一行 diff、看起來只是
「改用另一種寫法」），型別檢查與測試也抓不到（型別都是 string、渲染結果在快照裡是等價的）。

★**刪掉它會怎樣**：本目錄下所有原始 HTML 注入用法立刻無人看管；FR-038 的「MUST 建立機器守」
只剩下註解裡的一句話，而註解對下一個改這頁的人沒有強制力。★**改壞被測物會怎樣**：把
`views/manage/` 底下某個自由文字欄改成原始 HTML 注入形，本守門當場紅並指名該行——這正是
下方 self-test 每次執行都重演一遍的情境（植入反例必紅＝ADR 0024 非 vacuous 要求）。

★**掃描刻意「笨」**：逐行比對原文、**不解析註解也不解析語法**。理由有二——①被禁字面若能
藏在註解裡，就能藏在字串常值裡再 `eval`／拼接，解析註解只是把守門的判定面讓給對手；
②實作簡單即無 bug。代價是**連文件與註解都不能寫出被禁字面**（本檔自身不在掃描射程內，
故可寫），這一條已寫進 `views/manage/ip-rule/index.vue` 的檔頭。

★**掃到零檔＝異常**（`EmptyScanError`）：目錄被搬走／改名時，一支只會「找不到違規」的
掃描器會安靜地永遠綠燈——那是恆綠失效的標準形。本守門在該情形下 fail-loud。

落點：`.githooks/pre-commit`（**已接線**——見該檔「管理頁『零原始 HTML 插值』機器守」段）。
觸發條件＝base-web gitlink 變動（pin bump）或本檔自身 staged；純檔案掃描、毫秒級、不碰
docker／node，故可掛進 hook 的秒級預算內。★worktree 未就位（fresh clone、bootstrap 前）時
hook 具名跳過，同 fork-delta／entity-drift 兩處既有 Day-1 模式；跳過條件取 `base-web/src`
而非掃描射程本身，好讓「views/manage 被搬走」照樣走本檔的 fail-loud 路徑。
self-test 每次執行隨 `check` 連帶跑（防恆綠、同 `tools/fork-delta-lint.py` 既有形），故本檔
**不進** pre-commit 的 `for t in …` 自測名冊迴圈——具名豁免＝`tools/docs-sync.py` 之
`HOOK_TEST_LOOP_EXEMPT`（入迴圈＝staged 時緊接 check 再**重複跑一次** test、零新增覆蓋；
迴圈對賬測試期望＝test 名冊（TOOLS_PY 中帶 test 介面者）減豁免集，豁免三道防呆詳該常數處）。
★**治理名冊接線現況**（004 U-I 立本檔時七處全開、逐處 escalation 升級主線；
2026-08-18 治理批〔B-080／B-081〕收官後**七處全關**——
★逐處寫出、不寫「大致補完了」：含糊的那一句就是下一位據以誤判的那一句）：

  ⓪**已關**──`README.md` 的目錄樹已列本檔與 `tools/route-artifact-gate.py`，且該樹自此
    **有機器對賬**＝`docs-sync.py` 之 Lint27（B-081：tools/＋deploy/ 腳本檔集 vs 樹列名
    相等、漏列與幽靈兩向紅、紅只報不改）。
  ①**已關**──`tools/docs-sync.py` 的 `TOOLS_PY` 真表已含本檔（治理批、B-080）。
  ②**已關**──`tools/bootstrap.sh` 的 `run_tool_test` 已含本檔（同批）⇒ 體檢節自此自動
    跑到本檔 `test`（不受迴圈豁免影響——豁免只管 pre-commit 迴圈、bootstrap 體檢照跑；
    route-artifact-gate 同批納冊、其 `test` 同享體檢面）。
  ③**已關**──`docs/ops/RUNBOOK.md` §12 工具表已列本檔與 route-artifact-gate。
  ④**已關**──同檔「**pre-commit 條件觸發**」條目已含本檔（base-web pin bump 或本檔自身
    staged、`base-web/src` 未就位時具名跳過）。
  ⑤**已關**──§12.1 條件觸發段表已為**四支**並含本檔的量測值與單跑上限（0.224s／1s）。
  ⑥**已關**──`tools/docs-sync.py` 的 `TestGateWiring` 已補本檔的接線守：
    `test_dry_run_view_render_guard_trigger_conditions`（兩觸發條件各一次乾跑）與
    `test_dry_run_view_render_guard_day1_skip_when_worktree_absent`（`base-web/src` 缺席
    即具名跳過），另於分支 d2 斷言「本檔非零 ⇒ 立即 exit、其後 fork-delta 與 wire-schema
    全不得跑」。★**兩道變異實測**已跑：把 hook 內本區塊整段刪掉＝紅、把
    `[ -d "$HOOK_DIR/../base-web/src" ]` 條件反轉＝紅。
    ★連帶修好一個 harness 陷阱（值得記住）：該類的 `setUpClass` 原以 `_wfile` 把 `base-web`
    寫成**檔案**佔位 ⇒ `[ -d …/base-web/src ]` 恆假、新區塊一次都沒被乾跑到；現改為
    `_init_sub(d, "base-web")` 建**巢狀 git repo**——單純建目錄仍不行，`git add -- base-web`
    會展開成子路徑、staged 清單裡就沒有 `base-web` 這個字面，`grep -qxF 'base-web'` 落空、
    連 fork-delta 與 wire-schema 兩段也一併停止觸發。
"""
import os
import re
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 掃描射程（FR-038 逐字：「管理頁目錄下」）。
SCAN_REL = os.path.join("base-web", "src", "views", "manage")

# 受掃副檔名（前端原始碼；`.vue` 含模板與 script 兩段，一律當純文字掃）。
SCAN_EXTS = (".vue", ".ts", ".tsx", ".js", ".jsx")

# 禁用字面表：(正則, 說明)。★每條都是「把字串當標記執行」的入口，管理頁一律無正當用途。
FORBIDDEN = (
    (re.compile(r"\bv-html\b"), "Vue 原始 HTML 指令（模板面注入入口）"),
    (re.compile(r"\binnerHTML\b"), "DOM innerHTML 指派（含 Vue JSX 的 innerHTML prop）"),
    # ★獨立一條、不靠上一條兼收：`\binnerHTML\b` 對 `dangerouslySetInnerHTML` **不命中**
    #   ——正則大小寫敏感，而該識別字裡是 `InnerHTML`，且 `SetInnerHTML` 之間無詞界。
    #   合併寫成「上一條也含 React 式」是假述（實測 re.search 回 None）；本刀改為各自一條、
    #   各自配一則反例，維持「反例逐條對照 FORBIDDEN」的不變式。
    (re.compile(r"dangerouslySetInnerHTML"),
     "React 式 dangerouslySetInnerHTML（.tsx／.jsx 亦在掃描射程內）"),
    (re.compile(r"\bouterHTML\b"), "DOM outerHTML 指派"),
    (re.compile(r"\binsertAdjacentHTML\b"), "DOM insertAdjacentHTML 插入"),
    # ★`(?:ln)?` 不可省：`\bdocument\.write\b` 對 `document.writeln` **不命中**（`write` 與
    #   `ln` 之間無詞界，實測 re.search 回 None），而兩者是**同一個**注入面——都把字串當標記
    #   寫進文件流、都會執行內嵌 script 與事件處理器。少收這個變體等於在本表自陳的射程內
    #   留一個可繞道口。這是本表第二次同型失效（見上一條 `dangerouslySetInnerHTML` 註），
    #   故下方 COUNTEREXAMPLES 對本條掛**兩行**反例、由「每行皆須被本條抓到」的斷言逐行守。
    (re.compile(r"\bdocument\.write(?:ln)?\b"), "document.write／writeln 直寫文件流"),
    (re.compile(r"\bdomProps\b"), "Vue 2 風格 domProps（可繞道指派 innerHTML）"),
)


class EmptyScanError(Exception):
    """掃描射程內零檔案——目錄被搬走／改名，守門實質下線（恆綠失效）。"""


def iter_source_files(root):
    """回 root 底下受掃副檔名的檔案相對路徑（排序、確定性）。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if name.endswith(SCAN_EXTS):
                out.append(os.path.relpath(os.path.join(dirpath, name), root))
    return out


def scan_tree(root):
    """掃一棵樹 → (findings, scanned_count)。

    findings＝[(相對路徑, 行號, 說明, 該行去頭尾空白的字面)]；零檔案即 raise EmptyScanError。
    """
    files = iter_source_files(root)
    if not files:
        raise EmptyScanError(f"{root} 底下零個受掃檔案")
    findings = []
    for rel in files:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                for pattern, why in FORBIDDEN:
                    if pattern.search(line):
                        findings.append((rel, lineno, why, line.strip()))
    return findings, len(files)


# ── self-test（離線、毫秒級；每次 check 連帶跑）──────────────────────────────────

CLEAN_VUE = """<script setup lang="ts">
const memo = 'plain';
</script>

<template>
  <span>{{ memo }}</span>
</template>
"""

# 反例對照表：鍵＝`FORBIDDEN` 該條的**正則原文**，值＝植入用的反例片段。
# ★「反例逐條對照 FORBIDDEN」這條不變式是**機器強制**的、不是註解裡的一句話——`self_test()`
#   逐條斷言「鍵集恰等於 FORBIDDEN 的正則集、無重複鍵」且「該反例真的被該條規則抓到」。
#   ★為何非機器強制不可：少了這道，新增一條禁用字面卻忘了配反例時 self-test 仍全綠，那條
#   規則從此再沒被證明會紅（＝本工具自身要防的 vacuous 形，ADR 0024 決定①），而 `cmd_check`
#   的成功訊息卻照樣把它算進「N 條禁用字面」——自報覆蓋面與實證覆蓋面就此分岔且無人看管。
#   ★只斷言「兩表等長」不夠：新規則配一則重複掛在舊規則上的反例即可湊數過關，故取鍵集對賬。
# ★不斷言「該反例**只**命中該條」：`domProps` 那則刻意寫成指派 `innerHTML`（那正是 domProps
#   的唯一危害路徑），必然同時命中 `innerHTML` 條——強求互斥會逼反例失真。
COUNTEREXAMPLES = (
    (r"\bv-html\b", '<template><span v-html="memo"></span></template>\n'),
    (r"\binnerHTML\b", "el.innerHTML = memo;\n"),
    (r"dangerouslySetInnerHTML", "h('span', { dangerouslySetInnerHTML: { __html: memo } });\n"),
    (r"\bouterHTML\b", "el.outerHTML = memo;\n"),
    (r"\binsertAdjacentHTML\b", "el.insertAdjacentHTML('beforeend', memo);\n"),
    # ★兩行＝兩個同族變體，逐行皆須被本條抓到（`document.writeln` 曾因 `\b` 卡在 write／ln
    #   之間而漏收）。單行反例對「規則寫窄了」零偵測力：只留 `write` 那行的話，把正則改回
    #   `\bdocument\.write\b` 仍會全綠。
    (r"\bdocument\.write(?:ln)?\b", "document.write(memo);\ndocument.writeln(memo);\n"),
    (r"\bdomProps\b", "h('span', { domProps: { innerHTML: memo } });\n"),
)


def self_test():
    """紅綠成對：乾淨樹零命中、逐條反例必紅、零檔案 fail-loud。失敗即 AssertionError。"""
    with tempfile.TemporaryDirectory() as tmp:
        # ①零檔案＝fail-loud（不是「沒違規」）
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty)
        try:
            scan_tree(empty)
        except EmptyScanError:
            pass
        else:  # pragma: no cover - 只有守門壞掉才會走到
            raise AssertionError("self-test A：零檔案未 fail-loud＝恆綠失效未被擋")

        # ②乾淨樹零命中（證明本守門不是「見檔就紅」的恆紅品）
        clean = os.path.join(tmp, "clean", "ip-rule")
        os.makedirs(clean)
        with open(os.path.join(clean, "index.vue"), "w", encoding="utf-8") as fh:
            fh.write(CLEAN_VUE)
        found, count = scan_tree(os.path.join(tmp, "clean"))
        assert found == [], f"self-test B：乾淨樹誤報 {found}"
        assert count == 1, f"self-test B：受掃檔數應為 1、實得 {count}"

        # ③-a 反例表與 FORBIDDEN 一一對應（機器強制的不變式；缺這道就會養出「有規則沒反例」
        #     的假覆蓋——見 COUNTEREXAMPLES 上方說明）
        by_source = {pattern.pattern: (pattern, why) for pattern, why in FORBIDDEN}
        assert len(by_source) == len(FORBIDDEN), "self-test C0：FORBIDDEN 有重複的正則原文"
        ce_sources = [source for source, _ in COUNTEREXAMPLES]
        assert len(ce_sources) == len(set(ce_sources)), \
            f"self-test C0：反例表有重複鍵（等於某條規則湊數、另一條無反例）：{ce_sources}"
        assert set(ce_sources) == set(by_source), (
            "self-test C0：反例表與 FORBIDDEN 未一一對應——"
            f"有規則沒反例（該條從未被證明會紅）：{sorted(set(by_source) - set(ce_sources))}；"
            f"有反例沒規則（掛空擋）：{sorted(set(ce_sources) - set(by_source))}")

        # ③-b 逐條植入反例必紅（ADR 0024 非 vacuous：每條規則各自證明過會紅）
        for idx, (source, snippet) in enumerate(COUNTEREXAMPLES):
            pattern, why = by_source[source]
            assert pattern.search(snippet), \
                f"self-test C[{source}]：該反例根本不命中它掛名的那條規則（對照表接錯線）"
            tree = os.path.join(tmp, f"bad{idx}", "ip-rule")
            os.makedirs(tree)
            with open(os.path.join(tree, "index.vue"), "w", encoding="utf-8") as fh:
                fh.write(CLEAN_VUE)
            with open(os.path.join(tree, "evil.vue"), "w", encoding="utf-8") as fh:
                fh.write(snippet)
            found, _ = scan_tree(os.path.join(tmp, f"bad{idx}"))
            hits = [f for f in found if f[0] == "ip-rule/evil.vue"]
            # ★比對 `why`（該條規則專屬）而非「有沒有命中」：只斷言後者的話，反例被另一條
            #   規則順手抓到也算過，掛名那條照樣沒被證明過。
            # ★**逐行**而非 `any(...)`：反例得以多行承載同族變體（`document.write` 之於
            #   `writeln`），而 `any(...)` 只要有一行紅就算過 ⇒ 規則被改窄、漏掉其中一個變體
            #   時 self-test 照樣全綠。那正是本表已兩度發生的失效形（`dangerouslySetInnerHTML`
            #   與 `writeln`），故把「每一行都要被本條抓到」升為機器強制的不變式。
            caught = {f[1] for f in hits if f[2] == why}
            want = [n for n, text in enumerate(snippet.splitlines(), 1) if text.strip()]
            missed = [n for n in want if n not in caught]
            assert not missed, (
                f"self-test C[{source}]：植入反例第 {missed} 行未被**該條**規則抓到"
                f"（同族變體漏收＝該變體可繞道），實得 {hits}")

        # ④副檔名射程：不受掃的副檔名不該被誤掃（避免把 .md 說明文誤判成違規）
        skip = os.path.join(tmp, "skip", "ip-rule")
        os.makedirs(skip)
        with open(os.path.join(skip, "index.vue"), "w", encoding="utf-8") as fh:
            fh.write(CLEAN_VUE)
        with open(os.path.join(skip, "README.md"), "w", encoding="utf-8") as fh:
            fh.write('<span v-html="x"></span>\n')
        found, _ = scan_tree(os.path.join(tmp, "skip"))
        assert found == [], f"self-test D：非受掃副檔名被誤掃 {found}"


def cmd_check():
    """實跑：self-test → 掃 base-web/src/views/manage/**。"""
    self_test()
    root = os.path.join(REPO_ROOT, SCAN_REL)
    if not os.path.isdir(root):
        print(f"[view-render-guard] ✗ 掃描射程不存在：{SCAN_REL}——"
              f"目錄被搬走／改名？守門在該情形下不得靜默放行", file=sys.stderr)
        return 2
    try:
        findings, count = scan_tree(root)
    except EmptyScanError as ex:
        print(f"[view-render-guard] ✗ {ex}——守門實質下線（恆綠失效），"
              f"請確認 {SCAN_REL} 底下的前端原始碼是否被搬移", file=sys.stderr)
        return 2
    if findings:
        print(f"[view-render-guard] ✗ 管理頁出現原始 HTML 插值用法（{len(findings)} 處）"
              f"——FR-038 要求自由文字欄一律純文字插值：", file=sys.stderr)
        for rel, lineno, why, text in findings:
            print(f"  {SCAN_REL}/{rel}:{lineno}  {why}\n      {text}", file=sys.stderr)
        print("  補救：改回預設插值（模板 `{{ }}`／JSX 子節點），"
              "Vue 會把標記字元逸出成字面；確有原始標記需求＝拍板級，走 ADR。", file=sys.stderr)
        return 1
    print(f"[view-render-guard] ✓ {SCAN_REL}/** 零原始 HTML 插值"
          f"（受掃 {count} 檔、{len(FORBIDDEN)} 條禁用字面；self-test 過）")
    return 0


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "test":
        self_test()
        print(f"[view-render-guard] ✓ self-test 過"
              f"（{len(COUNTEREXAMPLES)} 條植入反例皆紅＝FORBIDDEN {len(FORBIDDEN)} 條全數"
              f"〔鍵集機器對賬〕、乾淨樹零誤報、零檔案 fail-loud）")
        return 0
    if cmd != "check":
        print(f"用法：{argv[0]} [check|test]", file=sys.stderr)
        return 64
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
