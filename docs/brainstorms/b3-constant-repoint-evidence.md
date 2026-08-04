# B3 常數重指施工紀錄

> 落點＝`docs/brainstorms/`（HISTORICAL_EXEMPT 前綴，與啟動書同區之創世期史料）。
> 依據＝啟動書 §4.5.3（B3 常數重指對照表 46 組）＋§4.5.4（字面釘死落點六處＋四類雙記帳）。
> 紀律＝分執行單元、每單元裁後即驗；驗收信號＝**docs-sync test 紅集合對裁前基線逐案相同**（無新增紅、無意外轉綠）。

## 裁前基線（2026-08-04）

`python3 tools/docs-sync.py test` → 424 tests、**9 failures ＋ 3 errors ＝ 12 紅**。
逐案比對 §4.5.2 二十案清單：九案吻合（roster_all_755／range_green／has_no_empty_set／contract_green／real_corpus_green／age_version／parse_real_routes_ts／parse_real_router_rs／compute_generated_wires_tools_cli）。
★第十案 `test_submodule_fallback_full_tree_when_old_pin_unresolvable`（三 label 變體）**不在 §4.5.2 清單內**——追查後確認為 Lint16 退化面的跨平台破口，非 B3 射程，已拍板丙案並排入 B4（見本檔末）。

## 執行單元與驗收

| # | 單元 | 改動 | 驗收 |
|---|---|---|---|
| 1 | `docs-sync.py` 世代字面 | 檔頭 docstring／`DEFAULT_BRANCH` rev4-admin-root→rev5-admin-root／面板 tags `rev4-admin`→`rev5-admin`（共 3 處） | 紅集合不變 |
| 2 | `secret-value-guard.py` 測試字面 | `/tmp/fork260509-rev4/secrets`×2、`/tmp/rev4-new`×7（共 9 處，皆為 SECRETS_DIR 解析樣本） | 自身 self-test **rc=0** |
| 3 | hooks 檔頭 | `.githooks/pre-commit`、`.githooks/pre-push` 各 1 處世代字樣。★以錨定字串指涉、不用行號（§4.5.1 注意事項 1：這些檔即將被改字、行號當場失效） | 紅集合不變 |
| 4 | `fork-delta-lint.py` 世代 token | `rev4-inline`×19 ＋ 1 處「合法 rev4 標記」docstring（散佈 18 行）→ 零殘留。★判定邏輯與九個 self-test 樣本同字面，必須一次改完 | self-test 通過（卡在基線源倉＝B9 前預期）；**反向突變實證**：只改判定不改樣本 → 立刻翻紅「self-test F」 |
| 5 | `bootstrap.sh` 世代字面 | 檔頭／`RV4_*_SRC_URL`→`RV5_`×4／repo 身分斷言×2／worktree 分支長名×2／`SECRETS_DIR_DEFAULT`×1（共 10 處） | 兩個 clone URL 值**原樣未動**（改了 bootstrap clone 必失敗）；紅集合不變 |
| 6 | `BUDGETS` 新增納管兩筆 | `.specify/memory/constitution.md` (350, None)、`docs/ops/RUNBOOK.md` (900, None)——§3.6 逐字可貼碼 | 實查確認 BUDGETS 無字面釘死自測（與 §4.5.4 六處清單一致）；紅集合不變 |
| 7 | DB 實例錯開（**雙記帳**） | `DB_USER` soybean→`soybean_rev5`、`DB_NAME` soybean_admin_rust→`soybean_admin_rust_rev5`。★`docs-sync.py` 與 `schema-gate.py` 各有獨立宣告、同刀齊改 | 兩檔同值機器斷言通過；紅集合不變 |
| 8 | `wf-watchdog.sh` RUNAWAY 判準（§3.2 條 12） | 行數型 → **數 journal 不重複 agent key**；值 25 不動（改判準非改值）。另加固：抽取樣式容忍鍵值間空白、新增「journal 非空卻抽不到 key」的 fail-loud 檢查 | 三向實證，見下 |

### 單元 8 的三向實證

| 場景 | 資料 | 結果 |
|---|---|---|
| A・誤報場景（條 12 記載） | 三輪 launch、journal 26 行、不重複 key 10 | 舊判準 26>25 **誤報**；新判準 10≤25 **不誤報** ✓ |
| B・真失控 | 30 支不同 agent | key=30>25 **正確觸發** ✓ |
| C・格式變異 | 鍵值間帶空白的 JSON | 加固後仍抽得到 key=10（未加固則為 0＝保險絲恆不觸發、**靜默卸除**）✓ |

★場景 C 是施工中意外發現的：首次驗證腳本用 `json.dumps` 預設格式（帶空白）產生測試資料，抽取結果為 0——測試資料的 bug 反而暴露了判準本身的脆弱性。真實 journal 無空白故當下有效，但格式一變即靜默失效。與同日發現的 Lint16 ERE 破口屬同一失效家族（**防線還在、偵測力歸零、零訊號**），故一併加固並補 fail-loud。

## 完工判準

**非 `rev4:` 前綴形的 rev4 字面：裁前 41 行 → 裁後 3 行。**

殘留三行全在 `tools/schema-gate.py`，**刻意保留**：

```
L121  # ---- 閘 1 結構面：post-baseline rev4 新增結構白名單（ADR 0039）----
L156  # ---- 閘 2 seed 面：post-baseline rev4 新增 seed 白名單（ADR 0032）----
L900  # B-055 長度面（ADR 0039）：…（左恆＝rev4 實庫）
```

理由：三行皆為**史料性描述**——它們正確陳述「這批白名單是 rev4 的」，改成 rev5 會失真。且 §4.5.3（三）第 11 條明訂該整組基線白名單因 Q9「schema 壓平成 rev5 m001」而語意消失、須**整組重建或整支延後**，屆時連同註解一併處置。B3 不動。

## 刻意留給後續步驟（非 B3 遺漏）

| 項 | 落點 | 理由 |
|---|---|---|
| `BETTERLEAKS_VER` 1.7.1→1.7.3、資產名 `linux_x64`→`darwin_arm64` | **B6** | §4.2 B6 明文分派；屬平台移植而非常數重指（與 §4.5.11 的 `AGE_ASSET` 同類） |
| `SECTION_QUOTAS` §9=5／§11=3 | **Q10 拍板後** | §3.3 稱十二格零漂移可照搬、§4.5.3 常數 8 稱應重議，§6 已登記待裁 |
| `RANGE_ROSTER` 範圍字串 | **Q8 拍板後** | 留洞（上界仍 24、四處不動）或遞補（全部 bump）取決於拍板 |
| `DICT_PATTERNS` 三條前代碼樣式 | **B4 甲** | 屬 Lint11 改式（防 `rev4:` 裸碼），是條款裁改非常數重指 |
| `EXEC_BIT_ROSTER` deploy 五支 | **Q4 拍板後** | 搬不搬 deploy 決定名冊要不要同刀改 |
| I18N 三路徑＋兩名冊 | **B12／i18n 地基刀** | rust 全新寫，Day 1 該九鍵與兩常數皆不存在 |
| schema-gate 基線白名單整組 | **schema 基線刀** | Q9 壓平後語意消失，整組重建 |
| `TSJS_VERSION` 0.67.4 | **B6／版本重查** | §4.5.3（四）明寫「依 §6 版本紀律重新確認後再定」 |

## 終驗

- 五支工具 self-test：`wire-schema`／`secret-value-guard`／`entity-drift-gate` **rc=0**；`docs-sync`／`schema-gate` rc=1（Day 1 結構性紅，明細見 §4.5.2）
- docs-sync 紅集合對裁前基線 **逐案相同**——無新增紅、無意外轉綠
- staged 憑證掃描 **rc=0**
- rev4 唯讀哨兵全程 **零改動**（`status --porcelain` 持續 0 行、HEAD 凍結未動）
