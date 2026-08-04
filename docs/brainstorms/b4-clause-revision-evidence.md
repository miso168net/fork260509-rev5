# B4 條款裁改施工紀錄

> 落點＝`docs/brainstorms/`（HISTORICAL_EXEMPT 前綴、創世期史料）。
> 依據＝啟動書 §4.2 B4、§4.5.10 v3、§4.5.5，加上 B4 前拍板閘五題裁決（`b4-decisions.md`）。
> 計畫＝`tmp/B4-PLAN.md`（13 執行單元）。驗收主軸＝**紅集合軌跡預測**，實得須逐步吻合。

## 一、紅集合軌跡（預測 vs 實得）

| 階段 | 預測 | 實得 | 變化來源 |
|---|---|---|---|
| B3 收工基線 | 12 | **12** | 9 案 §4.5.2 結構性紅＋3 案 Lint16 ERE 破口（同案三 label） |
| 單元 1 拆 Lint23 | 11 | **11** | `test_real_corpus_green` 隨條款拆除消失 |
| 單元 2 Lint16 修復 | 8 | **8** | `submodule_fallback` 三 label 全轉綠 |
| 單元 3–4 | 8 | **8** | 改式與建表不觸發行為變化 |
| 單元 5 產出器條件化 | 7 | **7** | `test_compute_generated_wires_tools_cli` 轉綠 |
| 單元 6 skipUnless | ≈2 | **0** | 優於預測——連 `test_live_manuals_are_clean` 的假綠也一併轉為有訊號的 skip |
| 單元 7–13 | 0 | **0** | 恆零 |

## 二、逐單元成果

| # | 單元 | 關鍵實證 |
|---|---|---|
| 1 | 拆 Lint23（甲①） | 移除本體 3,351 bytes＋測試類 4,700 bytes（11 方法）＋六項專屬資產；七識別字零殘留。**Q8 甲案兌現**：`codes={1..22,24}`、count=23、max=24，四處範圍字串一字未動、`bound_pinned` 自動仍綠 |
| 2 | Lint16 退化面跨平台修復 | 改 `ls-tree`＋`cat-file --batch`＋python re；四項契約全保留。補「單一引擎不變式」測試，突變模擬 BSD ERE 後**恰三個含 `\b` 的 label 翻紅、PEM 不受影響**（與 macOS 實測一致） |
| 3 | Lint11 改式＋Lint15 補形（甲②③） | Lint15 三平台形通過。**Lint11 偏離啟動書、user 已認可**（見四） |
| 4 | DAY1_EXEMPTIONS 建表（甲④） | 四欄＋啟動斷言；六筆謂詞**逐筆獨立 tempdir** 驗翻轉；修正 `lint24.day1` 謂詞（`isdir` → 掃描面真的有 `.rs`），補「目錄存在但零 .rs 仍未解除」邊界 |
| 5 | 產出器條件化＋守衛接線（乙①） | **DoD：`generate` rc=0**；產出 4 筆／豁免 7 筆零交集；到期即紅、五筆拔項各自翻紅 |
| 6 | skipUnless（乙②） | 實為 **11 案**（docs-sync 8＋schema-gate 3），逐案帶解除謂詞與所屬 B 步 |
| 7 | Lint24 early-return 分支（乙③） | 判定點在 early-return **匯流處**（非 `check_i18n_contract`）；三向：兩側缺→SKIP／拔項→兩筆 ERROR／單側缺→仍 ERROR |
| 8 | 分卷軸改按大小（丙①） | 120 筆同年→**2 卷**（年軸下恆 1 卷）；**封存卷 append 後逐字不變**；`MILESTONES_VOL_TOKEN_LIMIT=25000` |
| 9 | summary 上限（丙②／Q6） | `SUMMARY_CHAR_LIMIT=300`＋禁換行，併入 Lint03；邊界逐字釘死；突變放寬到 400 被攔 |
| 10 | BUDGETS 存在性斷言（丙③） | Lint20 **七組→八組**、豁免表 **六筆→七筆**；拔項→逐檔 ERROR；名冊少一筆→接線案翻紅 |
| 11 | Q13 雙源對賬 | Lint05 接 `parse_front_matter`；四向紅綠；突變拆接線→3/3 翻紅；**順帶定下報告 front-matter 規格** |
| 12 | 條款數三處同源（丁①） | 見三 |
| 13 | pre-commit 兩級計時（丁②／Q7） | 20s WARN／45s ERROR；五個邊界（3／20／25／45／50 秒）行為全對，含「恰門檻放行」的嚴格大於語意 |

## 三、B4 收工判準（全數通過）

| 判準 | 實得 |
|---|---|
| 五支工具 self-test 零紅 | 全 `OK`（docs-sync skipped=8、schema-gate skipped=3） |
| `generate` 可跑通、產出鍵集＝當日應有集 | **rc=0**、重算 4 檔 |
| 條款數三處同數 | 掃源推導 **23**／lint 摘要 **23**／bootstrap 斷言 **23**（上界仍 24，Q8 甲案下刻意不同） |
| 七筆豁免逐筆拔項翻紅 | `ComposePortsError`／`BackendDictError`／`RouterRoutesError`／`ElegantRoutesError`／`SnapshotError`／6 筆 ERROR／2 筆 ERROR |
| staged 憑證掃描 | rc=0 |
| rev4 唯讀紀律 | `porcelain` 0 行、HEAD 仍 `2b8a101` |

**殘紅口徑**（B8a 第①項）：零 ERROR；殘餘僅 `DAY1_EXEMPTIONS` 具名 SKIP 與類二 skip 明細共 11 案，**每筆附解除謂詞與所屬 B 步**。

## 四、啟動書偏離與盤點缺口

### 偏離一處（user 已認可）

**Lint11 改式**（§3.2 條 6／§4.5.3 條 10）。書上要求「三條前代碼樣式改成 rev4 裸碼偵測」，但那在本世代**不可實作**：rev3→rev4 之所以可行，是因為編號**形式不同**（`⚠️c`／`待決③`／`F-12` vs `ADR NNNN`／`B-NNN`／`L-NNN`）；rev4→rev5 沿用**同一套形式**（rev5 自 0001／001 起家），靜態樣式無從分辨。實證：照字面寫成 `(?<!rev4:)\bB-\d{3,}\b` 後，`test_clean` 立刻翻紅——它把 rev5 自己的 `B-012` 誤報成走私。

**處置**：三式併一式，判定面改為「提及 rev4 卻未用 `rev4:` 前綴」的混寫。八個正負樣本全過（rev4 混寫必中、`rev4:` 形放行、**rev5 自身 `B-012`／`ADR 0003`／`L-002` 必放行**）。同刀改字面自測並內建 rev5 自身編號負向樣本——缺之則錯誤實作全套仍綠。
**誠實射程**：完全未提 rev4 的裸碼抓不到（機器本無從分辨），該面由 Lint09 配號閘（已用號不得 ≥ next-id、反回收）承接。

### 盤點缺口三處（均已處置）

1. **§4.5.10 只盤點了 `lint_reference_sources` 側的三個 fixture 案要傳空表**，漏掉 `check_generated` 側——實際共 **12 處**呼叫需傳空表。
2. **§4.5.2 稱 schema-gate 兩案**，實為**三案**（多 `test_map_matches_datamodel_s1`）。
3. **§4.5.2 未標記 `test_live_manuals_are_clean` 是假綠**——三件活手冊皆不存在時「無命令形可驗」而靜默通過。加 skipUnless 後才成為有訊號的 skip。

## 五、施工中我寫出、被機制抓到的三個真 bug

這三件都不是啟動書的問題，是我的實作缺陷；記載於此供 B8a 與日後考古。

1. **豁免訊息含全形分號**，污染 lint 跳過明細的筆數機判（明細以「；」分隔、筆數靠數分隔符），被 `test_cmd_lint_prints_summary_then_skip_detail` 抓到（`14 != 8`）。已把該約束**機器化**成啟動斷言「理由欄禁含全形分號」，附原因。
2. **條款數斷言犯套套邏輯**：第一版比對「掃源推導」與「lint 摘要」，而兩者**同源**——條款被靜默拆掉時雙雙縮水、永遠對得上（突變實證 rc=0 通過、只是報 22 條）。真正的獨立源是 §3.4 補記載明的**創世事件 `notes` 之 `lint-roster:` 人寫名冊**。改對後四向全過：Day 1 warn／相符 ok／名冊少一條 die／實作縮水 die。
3. **驗證腳本自身的三次 bug**（共用 tempdir 污染謂詞、突變設計未真正模擬失效、測試漏餵 events）。其中兩次反而揭出被驗對象的真問題——`lint24.day1` 謂詞不精確、`RUNAWAY` 判準對格式變異脆弱。

★共同教訓：**突變實證要能信，前提是好版本自己得先綠**。第 3 項曾出現「突變後 3/3 翻紅」看似正常，實則好版本在那三案上也是紅的，數字對得上但意義是假的。

## 六、刻意留給後續步驟

| 項 | 落點 |
|---|---|
| `BETTERLEAKS_VER` 1.7.1→1.7.3、資產名 `linux_x64`→`darwin_arm64` | B6（平台移植，§4.2 B6 明文分派） |
| `TSJS_VERSION` 釘版重查 | B6 |
| `EXEC_BIT_ROSTER` deploy 五支 | Q4 拍板後／B5b |
| I18N 三路徑＋兩名冊 | B12／i18n 地基刀 |
| schema-gate 基線白名單整組（含三行史料註解） | schema 基線刀 |
| 附錄 A L2316 與 §3.2 條 5 的「預設乙案」敘述改甲案、名冊註「23 號已拆除、不重用」 | 本步已完成條款側；文件側敘述隨 B5 骨架落地時一併修 |
