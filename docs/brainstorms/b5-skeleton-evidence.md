# B5 骨架落地施工紀錄

> 落點＝`docs/brainstorms/`（HISTORICAL_EXEMPT 前綴、創世期史料）。日期＝2026-08-04。
> 依據＝啟動書 §4.2 B5、§4.6（薄手冊骨架＋RUNBOOK 最小四章）、§4.5.6（憲法判定表）、
> §4.7（範本與改字清單）、`b5-decisions.md`（Q5＋追問／Q11／Q12）。計畫＝`tmp/B5-PLAN.md`（7 單元）。

## 一、產物與逐單元實得

| # | 單元 | 產物 | 實得 |
|---|---|---|---|
| 0 | 前置盤點 | 改字工作表 | rev4 as-built 五檔逐字底本（非啟動書轉述）；啟動書己缺口當場解＝rev4 活書標題實形 `## §N 節名`（空格分隔） |
| 1 | 活書 | `docs/arc42/ARCHITECTURE.md` | 95 行；12 節切齊、十二格全在配額內（§9 4/5、§11 3/3 頂格＝設計絆線）；§1/§2/§4 rev5 語境先填、§12 含輕量軌詞條 |
| 2 | 三本帳 | NOTES／BACKLOG／LESSONS | BACKLOG `next: B-002`（B-001＝承襲盤點機器閘評估）；LESSONS `next: L-001` 空白起家、檔頭載 K3 候選去處 |
| 3 | RUNBOOK | `docs/ops/RUNBOOK.md` | 139 行 ≤900；§1/§12/§14/§15 實文＋12 章佔位零命令；範圍字串**半形** `Lint03~Lint24`（rev4 §12 實形、Q8 甲案上界 24 不動）；釘版段 betterleaks **1.7.3**（rev4 為 1.7.1）／sops v3.13.3-alpine digest 沿用／age **v1.3.1** 粗體字面（TestGateWiring 比對面、B5b 落 deploy 後解除 skip）；§14 埠字面 4xxxx→5xxxx |
| 4 | README | `README.md` | 90 行 ≤150；文件地圖含 K1/K2/K3 指路列＋掃描防線禁令提醒 |
| 5 | 薄手冊 | `CLAUDE.md` | 147 行 ≤250；§4.6 骨架六節＋改字清單 10 條＋**Q11 第八條禁令**＋**Q12 輕量軌段**＋wf-watchdog 判準註記；內嵌範本 B 末行改 `tools/docs-sync.py generate`（§4.7 改字 2、Lint19 語料防紅） |
| 6 | 憲法 | `.specify/memory/constitution.md` | **v1.0.0、192 行 ≤350**（Q5 甲案＋承襲指針×2＋§IV Q9 補註）；★**user 親審 diff 通過（2026-08-04）**，對照包＝五類分審（A 不搬 2／B 新增 4／C 改寫 6／D 純改字六類／E 待定 3——E 按建議值收案：§I.5 schema 例外句由 ADR 0001 承載、日期戳 2026-08-04、原樣段全數照搬） |
| 7 | 收工驗收 | 本檔 | 見二 |

## 二、收工判準（全數通過）

| 判準 | 實得 |
|---|---|
| 五支工具 self-test 零紅 | 全 OK；**docs-sync skipped 8→6**（CMD_FORM_CORPUS 案＋RANGE_ROSTER 案隨三活手冊落地解除、426 tests）、schema-gate skipped=3 不動——與計畫預測逐案相同 |
| DAY1_EXEMPTIONS | **7→6 筆**——★`lint07.budget_roster` 豁免「到期即紅」**實彈觸發**（CLAUDE.md 落地使八檔齊、lint 轉 ERROR 要求下架）→依紀律拔項，Lint07 恢復八檔全檢。B4 建的機制首次真實運轉 |
| Lint07 八檔實跑 | 全綠：README 90/150｜CLAUDE 147/250｜NOTES/BACKLOG 預算內｜活書 95/700｜憲法 192/350｜RUNBOOK 139/900｜STATE token 內 |
| `generate` | rc=0、重算 4 檔 |
| 實 repo lint 紅軌跡 | **13 → 11 → 9 → 8 → 7**（單元 1 起點→單元 2→3→4→拔項後），殘 7 全數具名：Lint20×2（ADR 檔集空／events 空→**B7 解**）＋Lint21×5（deploy 五支不在 index→**B5b 解**）；0 WARN、10 條款跳過、共 23 條款 |
| 突變實證（抽驗三項） | ①RUNBOOK 範圍字串 24→25：**Lint22 兩處逐行翻紅**（:68/:97 各附實得/應為），還原後 0 紅｜②活書 §12 灌至 36/30：**Lint07 WARN 放行**，還原 95 行｜③CLAUDE.md 灌至 257/250：**Lint07 ERROR 硬擋**，還原 147 行｜三項後基線復位（7 錯誤/0 警告/10 跳過） |
| staged 憑證掃描（B7 真閘同形） | `betterleaks git --config .gitleaks.toml --pre-commit --staged --redact --verbose --exit-code 2`→**rc=0**、no leaks（1.68MB／161ms） |
| rev4 唯讀紀律 | `porcelain` 0 行、HEAD 仍 `2b8a101c` |
| index | 98→**106 檔**（＋7 件手冊帳＋005 裁決紀錄；106 檔全 A＝B7 首批 commit 前無 HEAD 的正常態）；B5 不 commit（B7 一鍋） |

## 三、工程自拍（回報備查）

1. **RUNBOOK §12 條款速覽縮編**：rev4 有 55 行逐條款詳述，rev5 縮為三分義＋摘要形＋指路（工具源碼與 test 自測）——逐條詳述是與 docs-sync 源碼的雙記帳面，rev5 Day 1 不再複製；三個機器閘吃的①叫用形②範圍字串③AGE_VERSION 全數保留。
2. **rev4 追蹤碼處置**：功能敘述保留、rev4 專屬追蹤碼（B-NNN／ADR 號／刀號）刪除或改 `rev4:L-NNN` provenance 形（編號降級規則②④）；rev4 RUNBOOK §16 章名的刀號亦除。
3. **§1 五步含 B5b 資產命令**：deploy 腳本 B5b 才落，但 B1～B6 產物同進 B7 一鍋 commit——commit 內自洽，故照 rev4 as-built 全寫；macOS 憑證信任程序**未實跑不落命令**、註記隨 dev stack 刀補。
4. **憲法 C 類改寫 6 處**（詳 `tmp/B5-CONSTITUTION-DIFF.md`，已隨親審過目）：檔頭來歷句、§I.2 刪 (k)、§I.6 J3 自足化、§I.6 變體 C provenance 形、§III 例句軌道代號泛化、§II 排程例示刪。

**收工後修正一筆（同日）**：README 目錄樹原把 compose 三檔寫成無條件存在，實則 B10 才移植（晚於 B7 創世 commit）——已改「（dev stack 就位時出現）」標記形，比照 `specs/` 先例；lint 基線不變。

## 四、啟動書偏差（實查修正，2 筆）

1. **§III.2 軌道數**：啟動書 §4.5.6 稱「五個」★ 軌道，rev4 憲法實檔為**六個**（MODAL／I18N／AUTH／LOGOUT-UX／LOGIN-CAPTCHA／DEVPROXY）——憲法承襲指針與 Amendment log 均按六寫。
2. **檔尾形制**：啟動書範本用全形「｜」與「（Q12）」字樣；rev4 實檔為半形 `|`、粗體欄名——從實檔；「（Q12）」改「（創世拍板）」防與 rev5 13 題編號混淆。

## 五、刻意留給後續步驟

| 項 | 落點 |
|---|---|
| Lint21 deploy 五支紅＋RUNBOOK §7/§15 補全＋AGE gate wiring skip 解除 | B5b |
| Lint20 ADR 檔集空／events 空兩紅＋ADR 0001（含 §I.5 schema 例外承載）＋創世 misc 事件（`lint-roster:` 名冊） | B7 |
| RUNBOOK 佔位 12 章實文 | 各對應刀 |
| macOS 憑證信任命令實測補記 | dev stack 刀（B10） |
| B-001 承襲盤點機器閘評估 | 首刀（B12）後 |
