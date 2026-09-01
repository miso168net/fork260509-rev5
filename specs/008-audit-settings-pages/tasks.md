# Tasks: 008 稽核中心與系統設定頁（B-008 收官、audit 五端點）

**Input**: Design documents from `/specs/008-audit-settings-pages/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/（wire-audit.md＋
msg-keys.md）、quickstart.md——全數已備

**Tests**: 必做（spec FR-I01 三層測試＋FR-C04 fault-injection＝硬性要求；workspace TDD 紀律）

**Organization**: 依 user story 分期；執行時由 executing-plans 依相依收攏為執行單元
（CLAUDE.md §2 編排範本）。**次序鐵則**：Phase 1（U0 修憲）先於一切 base-web
route:/page:/views/產物四檔改動與 purge BizData 構造點；rust build/test 一律容器內**全程
serial**——`[P]` 僅表「無相依、可併行編輯」、不表平行跑 cargo。兩段式 commit（子庫→外層
pin bump）與「絕不 push/merge」由 CLAUDE.md 承載、不入本清單。

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

後端＝`rust-api/`（worktree）；前端＝`base-web/`（worktree）；工具與治理＝repo 根
`tools/`、`.specify/`、`docs/`。行號引用＝research.md 量測快照、實作期以 grep 現況為準。

---

## Phase 1: Setup — U0 修憲（blocking GATE；先於一切 WIRING 面）

**Purpose**: plan Constitution Check 之 GATE 條件——§III.2 加用途＋行為島候選親決＋BizData
射程補充 ADR；全在外層 repo、不動子庫。

- [x] T001 起草憲法 Amendment ADR draft `docs/arc42/decisions/00NN-constitution-amendment-manage-page-uses-vii-viii.md`（編號取現況 next；內容＝§III.2 `BASE-WEB-MANAGE-PAGE-WIRING` 加用途 (vii) system-settings 頁進場＋(viii) audit 頁進場之表列逐字〔形照 (i)/(iv)：兩語 locale route:/page: 兩樹＋app.d.ts page 型節新增型圈界；view 新檔不入名冊；產物四檔沿 (i) 列〕）＋稽核域行為島條文草案（audit purge 域：30 天下限／單交易自記／自記豁免／四值白名單／§I.6 變體 B retention 釋義兌現；含「入憲 vs 不入憲」兩案並陳）
- [x] T002 [P] 起草 BizData 射程補充 ADR draft `docs/arc42/decisions/00NN-bizdata-scope-adds-purge-below-floor.md`（補充 ADR 0064 射程清單＋`biz.audit.purgeBelowFloor{minDays}`；provenance＝grilling 拍板③ 2026-09-01 user 親決第三攜參鍵；`rust-api/server/src/error.rs` doc 之「嚴限密碼二鍵」句同批改對計入 T014 涉檔）
- [x] T003 ★user 親決（三停①、主線停手問）：①行為島入不入憲（憲法 §IV 第 9 題；K1-11／K1-57 承襲輸入）②Amendment 表列核可③BizData 射程補充核可
- [x] T004 依親決落字：`.specify/memory/constitution.md` §III.2 表加兩列（＋若拍入島：§I.7 島 J 條文）＋version bump 1.9.1→1.10.0（MINOR）＋U0 三支 ADR 轉 accepted：T001 之 ADR 0077（憲法 Amendment）＋T002 之 ADR 0078（BizData 射程補充）＋★本 task 內補立之 ADR 0079（`AuditOperation` 詞彙第九值 `purge`；T003 附帶親決題第四題取形 (a)＝U0 內補立，原 tasks 無任一支建之＝派工單缺口，依 ADR 0077 後果段於本單元補立）＋獨立 commit `docs(constitution): amend …`＋`python3 tools/docs-sync.py generate`＋★**L-063 防法②之記派**（ADR 0077 後果段承諾之承載；原 tasks 無任一支承載＝派工單缺口，形照 007-user-password-admin 之 T003 記派）：(vii)(viii) 兩新列此刻零標記可比、當場變異結構性 vacuous（改壞新列路徑回 rc=0＝看似有效實則一次未觸發），故**真**變異自證延後至第一個往該列落 `rev5-inline` 標記的實作單元——**(vii)→U4**（①②塊之標記守於 T024、③塊之重算冪等閘於 T025）、**(viii)→U5**（同形：T032／T033），紅綠證逐字補記各該 task；★**變異面取 ADR 0077 後果段列名之兩道實得機器守**（①②塊＝`tools/fork-delta-lint.py` 之 `find_unmarked_additions`「新增型圈界標記須存在」、③塊＝`python3 tools/route-artifact-gate.py check` 之重算冪等閘），★**不取「改壞 §III.2 該列範圍欄反引號路徑」形**——名冊三元組斷言射程僅修改型（`find_rogue_tracks` docstring 逐字「★射程僅修改型——新增型 `NAME+` 不入三元組判定」、self-test Y 釘住），本軌道三塊皆新增型圈界或生成檔 ⇒ 該形對本軌道結構性不適用（ADR 0077 後果段 caveat 已誠實揭露）；還原照 L-060（存原文→寫回＋`md5sum` 對照、不用 `git checkout`）

**Checkpoint**: 憲法 vNext 落地——WIRING (vii)(viii) 授權生效、BizData 第三鍵有 ADR 承載。

---

## Phase 2: Foundational — wire 契約錨（blocks US2／US3 後端）

**Purpose**: `Api.Audit` typings（wire 唯一權威、§III.1 ADAPT 軌零修憲）＋快照重抽，讓
後端三層測試有裁判基準。

- [x] T005 新檔 `base-web/src/typings/api/rev5-audit.d.ts`（`Api.Audit` 全型：四列型＋四 SearchParams＋PurgeAuditTable 四值枚舉＋PurgeAuditLogReq/Res；欄集逐字＝data-model.md §1~§3、契約＝contracts/wire-audit.md；檔頭新增型標記）
- [x] T006 重抽 wire 快照：`python3 tools/wire-schema.py extract` → `rust-api/server/tests/fixtures/wire-schema.json`（definitions 增 Api.Audit 節）＋`rust-api/server/tests/wire_schema.rs` 檔頭 definitions 計數註更新＋容器全量 serial 仍綠（既有 1015 零紅）

**Checkpoint**: 裁判基準就位——後端 story 可開工。

---

## Phase 3: User Story 2 — 超管查詢四源稽核紀錄（Priority: P1）後端讀面

**Goal**: 四支讀端照 rev4 藍本落地（rev5 欄名），三層測試齊。

**Independent Test**: 容器內 `cargo test`——四端點授權矩陣（Super 0000／Admin 5003／未認證
8888）＋DTO wire 形＋寬鬆守門＋enrich＋PII 負向自證全綠；curl 打 22079 四端點回 PageRes。

- [x] T007 [US2] 新檔 `rust-api/server/src/model/audit_query.rs`：共用查詢建構（時間 RFC3339 閉開 [from,to)、畸形＝未設、顛倒＝空頁；人員過濾 id 優先／名→含軟刪同名 IN；ILIKE 萬用字元字面化＋ESCAPE）＋`mask_pii_payload`（深度一層、`userPhone`／`userEmail` 兩鍵、非字串原樣；rev4:audit_query.rs 藍本重打字）（★鍵風格＝rev5 寫端 camelCase——`facade/sys_user::audit_json` 逐字落 `"userPhone"`／`"userEmail"`；rev4: 之 `user_phone`／`user_email` 屬差異點、不帶回〔ADR 0019〕。★照 snake_case 實作則打碼對生產 payload **恆不生效**）＋表驅動測三支（電話全路徑／信箱全路徑／邊界與非打碼鍵原樣）——先紅後綠
- [x] T008 [US2] facade 讀端：`rust-api/server/src/model/facade/{sys_operation_log,sys_login_attempt,session_event}.rs` 各加分頁讀 fn＋新檔 `facade/sys_access_log.rs`（mod.rs 名冊同批）；固定排序 `created_at DESC, id DESC`；分頁走 sea-orm paginate 慣例
- [x] T009 [US2] 新檔 `rust-api/server/src/handler/audit.rs`（四讀端）：query DTO 全 `Option<String>` 寬鬆（rev4:L-090）＋normalize_page（current≥1、size clamp [1,100] 預設 10）＋四 DTO（★rev5 欄名：op-log `realIp` 家族無 operator 前綴＋`region`；session_event 單欄 `sourceIp`）＋enrich 走 `common::resolve_operator_names`＋mask 呼叫恰二處（payloadBefore/After）＋同檔 mod tests：camelCase 收單／分頁欄垃圾不 400／success 嚴格值域／IP 守門／DTO 序列化形（照 rev4 測名族、先紅後綠）
- [x] T010 [US2] `rust-api/server/src/router.rs` 四條 RouteDef（path 逐字＝seed 凍結列、GET、Policy、case_key `get-operation-log` 等）＋`ROUTES_COUNT` 61→65＋逐刀 bump 帳註
- [x] T011 [P] [US2] `rust-api/server/tests/contract.rs` 四 case 登記＋verify fn（照 `verify_get_system_settings` 形：未認證 8888 信封＋HTTP 200）
- [x] T012 [P] [US2] `rust-api/server/tests/wire_schema.rs` 補 `Api.Audit` 讀面 definitions 裁判（四列型＋四 SearchParams；正反例成對、逐格指名；照 Api.IpRule 節形）
- [x] T013 [US2] handler 真 DB 測（同檔 endpoint_tests）：授權矩陣＋casbin seed 端點維五列**存在性**對賬（★五列自 001 恆在、斷言的是 seed 列非 route——本階段 route 僅四條屬預期、第 5 條隨 T016）＋enrich（含軟刪操作者名）＋PII 端到端負向自證（拆 mask 即紅）＋讀端零拒因（畸形分頁／時間顛倒回空頁）；容器全量 serial 綠＋`cargo fmt --all`

**Checkpoint**: US2 後端可獨立驗收（curl＋全測綠）；access 讀空表＝已知態。

---

## Phase 4: User Story 3 — 水平線清理（Priority: P2）後端＋fault-injection

**Goal**: purge 端點＋原子性機器證＋B-125 關帳。

**Independent Test**: 容器內測——四值白名單／30 天下限（BizData {minDays}）／單交易自記
＋purge 豁免／fault-injection 整筆回滾全綠；`_with_db` 薄殼有兩個消費者。

- [x] T014 [US3] `rust-api/server/src/handler/audit.rs` 補 purge：守門固定序（①table 四值白名單→2222 `biz.audit.invalidTable` ②beforeDays≥`PURGE_MIN_DAYS`=30→2222 `biz.audit.purgeBelowFloor`＋`AppError::BizData(json!({"minDays":30}))` ③單交易水平線 DELETE＋同交易 purge 自記、op-log 版 `operation <> 'purge'` 豁免）＋`PurgeAuditLogReq` 寬鬆反序列化（畸形→None 恆不裸 400）＋`error.rs` doc 射程句改對（T002 ADR 承載）＋★前置（開工前提＝ADR 0079 已 accepted、其決定 3 之次序約束）`rust-api/server/src/model/audit.rs` 詞彙第九值三處連動（ADR 0079 決定 2）：①`audit_operation_vocabulary!` 呼叫點**末位**加 `Purge => "purge"`（★小寫、非 rev4 大寫形）②`EXPECTED_LITERALS` 由 `[&str; 8]` 增為 `[&str; 9]`、新字面 `"purge"` 插末位（與 `ALL` 恰等比對含序、插錯位即紅）③測 `t013_user_password_family_adds_three_vocabulary_stays_eight` 之 `ALL.len()` 期望 8→9、**測名與斷言訊息連同改寫**（新定案出處＝ADR 0079）＋同檔 doc 註「八值／八個字面／現八字面／恰八值」假述面以 `grep -n "八" rust-api/server/src/model/audit.rs` 現算逐行判別後同批改對（排除 `ip_confidence` 來源信心八態＝他軸；史述照 L-032 保留），改完以同指令復掃驗收＋stub-DB 守門測（零 DB 副作用、固定序、{minDays} 明細——照 rev4 測 11~14 形、先紅後綠）
- [x] T015 [US3] msg 鍵三檔同 commit（Lint24 孤兒鍵紅約束）：`base-web/src/locales/langs/zh-tw.ts`（`biz.audit` 節插 `biz:` 內字母序 `auth` 前）＋`zh-cn.ts`＋`en-us.ts` backend 樹同鍵（譯文逐字＝contracts/msg-keys.md）＋`base-web/src/typings/app.d.ts` backend 型節補 `audit` 二鍵（I18N-WIRING (ii)(iii) 圈界標記）
- [x] T016 [US3] `rust-api/server/src/router.rs` 第 5 條 RouteDef（POST、case_key `purge-audit-log`）＋`ROUTES_COUNT` 65→66＋`rust-api/server/tests/contract.rs` 第 5 case
- [x] T017 [P] [US3] `rust-api/server/tests/wire_schema.rs` 補 purge definitions 裁判（`PurgeAuditTable` 枚舉集斷言接後端白名單常數＋Req/Res 形）
- [x] T018 [US3] `rust-api/server/src/model/mod.rs` test_db：`real_app_and_state_with` 之 `_with_db` 薄殼（收 db、沿 `test_state`、不新增 AppState 建構字面）＋`LOCKABLE_TABLES` 擴 `"sys_operation_log"`（白名冊常數＋自測同批）
- [x] T019 [US3] purge 原子性 fault-injection 測（照 b056 七步形：`real_db_single_with_lock_timeout`→seed 可刪列→`TableLock::acquire("sys_operation_log")`→打 purge→先釋鎖後斷言→旁證另開連線：標的列仍在＋零自記＋錯誤回傳→前提字面斷言防恆綠；★破壞性驗證還原守衛先行、紅綠證留單元紀錄）＋真 DB purge 測（水平線刪舊留新＋自記 payload／零列照自記 deletedCount=0／併發新寫終態俱在——照 rev4 測 17~19）；容器全量 serial 綠
- [x] T020 [US3] `rust-api/server/src/handler/auth/logout.rs` TTL 同形補測（收尾段 commit 後讀 TTL、經 `_with_db`＋TableLock("system_settings")、照 b056 形）＋B-125 關帳：`docs/ops/BACKLOG.md` 刪列＋L-072 雙向掃（NOTES 等現在式家族）＋`docs/ops/NOTES.md` 同步

**Checkpoint**: 五端點齊、ROUTES_COUNT=66、原子性有機器證、B-125 關。

---

## Phase 5: User Story 4 — 開發者防線 Lint24 第三腿（Priority: P3）

**Goal**: 佔位符漂移即紅（B-139 關帳）；此時三攜參鍵已在、real-repo 自測驗最終態。

**Independent Test**: `python3 tools/docs-sync.py lint` 綠＋自測紅綠樣本；變異（{minDays}
改名→紅→還原綠）附證。

- [x] T021 [US4] `tools/docs-sync.py` Lint24 第三腿：`parse_locale_backend` 留值 dict＋`scan_backend_msg_keys` 擴 BizData 視窗抓 `json!({...})` 頂層字面鍵（非字面形 fail-loud）＋新純判定函式（zh-tw 攜參鍵 `\{(\w+)\}` 佔位符集＝後端頂層鍵集；併驗 zh-cn／en-us 同鍵佔位符集＝zh-tw）＋接線 `lint_i18n_contract`＋`i18n_contract_self_test` 防恆綠＋self-test 紅綠案（真 repo 三鍵綠案）＋docs-sync 自測計數帳更新
- [x] T022 [US4] 變異自證（zh-tw `{minDays}` 改名→Lint24 紅→還原綠；紅綠證留紀錄）＋B-139 關帳：BACKLOG 刪列＋L-072 雙向掃＋NOTES 同步

**Checkpoint**: 條款數維持 **29**（第三腿沿第二腿形掛在 Lint24 底下、不新增條款碼；原寫「30 條款」為規劃期誤記，實作後三處同數〔掃源推導／lint 摘要／events 末筆 lint-roster〕皆 29）、B-139 關。

---

## Phase 6: User Story 1 — 系統設定頁（Priority: P1）前端

**Goal**: settings view 兌現（後端與接線層零改動）；seed-view-gate settings 列摘除。

**Independent Test**: CDP 以 Super 登入 22080——側欄「系統設定」翻譯正常、點擊進頁、四組
16 鍵對照 rev4（42080）、改值即存回讀、非法值拒因可讀；typecheck＋四閘綠。

- [ ] T023 [US1] 新檔 `base-web/src/views/manage/system-settings/index.vue`（單檔；資料驅動控件：二值 enum→NSwitch／number→NInputNumber `:update-value-on-input="false"`／其他→唯讀；四組固定序＋未列鍵排組尾；逐項即改即存、成功失敗皆 refetch、清空不送；labelKeyMap＋helpKeyMap 16 鍵 typed literal＋fallback description；`import { fetchGetSystemSettings, fetchUpdateSystemSetting } from '@/service/api/rev5-settings'` 直接路徑；rev4:system-settings/index.vue 藍本重打字、註解重寫）
- [ ] T024 [US1] i18n＋型節（WIRING (vii) 新增型圈界）：`base-web/src/locales/langs/zh-cn.ts`＋`en-us.ts` 之 route: 樹 `'manage_system-settings'` 鍵＋page.manage.systemSettings 樹（4 titles＋items 16＋help 16；譯文以 rev4 兩語為底重打）＋`base-web/src/typings/app.d.ts` Schema.page.manage 補 systemSettings 型節（插位＝research R2 錨；兩語鍵集相等）＋★**L-063 補做**（本 task ＝用途 (vii) 之第一個落 `rev5-inline` 標記處）：兩道實得機器守之真變異自證——①②塊之圈界標記守於本 task、③塊之重算冪等閘於 T025；變異面／不取之形／還原紀律逐字＝T004 記派段，紅綠證逐字補記本 task
- [ ] T025 [US1] 產物四檔重算（`base-web` dev server 起動或 `pnpm gen-route`；`src/router/elegant/{imports,routes,transform}.ts`＋`src/typings/elegant-router.d.ts` 零手改）＋`python3 tools/route-artifact-gate.py` 冪等綠＋`pnpm typecheck` 綠
- [ ] T026 [US1] `tools/seed-view-gate.py`：EXEMPT 摘 `view.manage_system-settings` 列＋self-test 案 I-a 鍵集釘改（恰餘 audit 一鍵）＋檔頭「恰兩列」敘述改；gate 綠
- [ ] T027 [US1] 單元驗證：`python3 tools/view-render-guard.py` 綠＋`python3 tools/fork-delta-lint.py` 綠＋CDP 快查（側欄進頁煙測反轉＋改一鍵回讀）

**Checkpoint**: US1 可獨立交付（MVP 切片）；豁免表恰餘 audit 一列。

---

## Phase 7: User Story 2＋3 — 稽核中心頁（前端）

**Goal**: audit 頁四源四分頁＋XFF 欄＋purge modal；seed-view-gate 歸零。

**Independent Test**: CDP 對照 rev4 四分頁逐欄（XFF 欄＝唯一例外）；搜尋／分頁／快照
dialog／purge 流程全通；四閘綠。

- [ ] T028 [P] [US2] 新檔 `base-web/src/service/api/rev5-audit.ts`（5 fetcher：四 GET query＋purge POST；不入 barrel、直接路徑 import request）
- [ ] T029 [US2] 新檔 `base-web/src/views/manage/audit/modules/use-audit-search-date-range.ts`（dateRange→UTC ISO、reset 快照回填＋emit search）＋四搜尋卡 `audit-search-{operation,access,login,session}.vue`（NCollapse 預設展開；label 走分頁樹＋common、placeholder 走 form.*；login 之 success NSelect successOption 兩值；rev4 藍本重打字）
- [ ] T030 [US2] 新檔 `base-web/src/views/manage/audit/index.vue`：NTabs 四分頁×四組 `useNaivePaginatedTable`（`api`＋`defaultTransform`＋columns）；欄集逐欄照 rev4＋★XFF 欄三分頁（純文字、`ellipsis: { tooltip: true }`；session 分頁不加；ADR 0076）；scroll-x＝Σ欄寬不變式帳註（multiline 形、B-144 慣例）；op-log 快照 `$dialog.info`＋`<pre>` 純文字 JSON；refresh 鈕不重置頁碼；login 分頁 throttleNote NAlert
- [ ] T031 [US3] 新檔 `base-web/src/views/manage/audit/modules/audit-purge-modal.vue`（MIN_DAYS=30 前端護欄＋NAlert 警語＋NPopconfirm 二段確認＋emit 'submitted'＋開啟重置回 30）＋index.vue 每分頁 purge 入口（單例掛載、target 隨分頁）＋成功 toast 帶 {count} 刷新該分頁
- [ ] T032 [US2] i18n＋型節（WIRING (viii) 新增型圈界）：兩語 route: 樹 `manage_audit` 鍵＋page.manage.audit 樹（57 葉×2、含 tab/common/operation/access/login/session/form/purge；譯文以 rev4 兩語為底重打）＋app.d.ts Schema.page.manage 補 audit 型節；兩語鍵集相等＋★**L-063 補做**（本 task ＝用途 (viii) 之第一個落 `rev5-inline` 標記處）：兩道實得機器守之真變異自證——①②塊之圈界標記守於本 task、③塊之重算冪等閘於 T033；變異面／不取之形／還原紀律逐字＝T004 記派段，紅綠證逐字補記本 task
- [ ] T033 [US2] 產物四檔重算＋`route-artifact-gate` 冪等綠＋`pnpm typecheck` 綠＋`view-render-guard` 綠＋`fork-delta-lint` 綠
- [ ] T034 [US2] `tools/seed-view-gate.py`：EXEMPT 摘 `view.manage_audit` 列（表歸零）＋I-a 釘改＋檔頭改；gate 綠

**Checkpoint**: 兩頁全兌現、豁免表歸零。

---

## Phase 8: Polish — 驗收與關帳

**Purpose**: 端到端驗收（quickstart §3）＋餘四條關帳＋holistic review。

- [ ] T035 CDP 三方對照全套（quickstart.md §3 六步、次序不可反）：baseline snapshot→走查〔煙測反轉兩項／settings 對照／audit 四分頁逐欄對照（XFF 欄例外註記 ADR 0076；access 空表、region/traceId 恆「-」＝已知態驗形不驗值）／★XSS 注入驗證 SC-003（CDP Fetch 注入 `X-Forwarded-For: <script>…</script>` 產列→字面顯示零執行）／purge 29 拒（{minDays} 字樣）＋3650 成功（deletedCount=0＋自記）〕→§9c 清理→`walkthrough-baseline.py diff` rc 0→容器全量 serial 綠→`schema-gate.py check` 三閘綠
- [ ] T036 B-078 確認句復核落帳（grep 證據：讀端 realIp 過濾＝等值 /32、/128、零 LIKE 對 IP 欄）＋關帳三條：`docs/ops/BACKLOG.md` 刪 B-008／B-072／B-078 列＋L-072 雙向掃（現在式家族待辦式引用同批改；反向核家族引用之 B-NNN 仍在兩卷）＋`docs/ops/NOTES.md` 同步
- [ ] T037 final holistic review（spec 逐 FR 對照＋SC 八條逐條驗；findings 三分流：修／轉 B-NNN／won't-fix ADR；以收單 commit 訊息承載＝ADR 0075）

---

## Dependencies

```
T001~T004（U0）──先於──▶ T014（BizData 構造＋詞彙第九值）、T015／T024／T032（WIRING 面）、T025／T033（產物四檔）
T005~T006（契約錨）──▶ T007~T013（US2 後端）──▶ T014~T020（US3 後端；同檔 audit.rs 續建）
T014＋T015──▶ T021（Lint24 第三腿之三鍵終態）
T023~T027（US1 前端）：僅依 T004；與 US2/US3 後端無相依（可提前、惟 rust/前端單元仍序跑）
T028~T034（audit 前端）：依 T004＋T010/T016（端點在）＋T005（typings）
T035~T037：依全部
seed-view-gate 摘列與 view 兌現同單元強耦合（T026↔T023~T025；T034↔T028~T033）——gate
「豁免到期即紅」使反序或跨單元皆擋。
```

**Story 完成序**：US1 獨立（T004 後即可）；US2 後端→US3 後端→US4；audit 前端收 US2/US3
UI 面；US3 的 purge modal（T031）依 audit 頁骨架（T030）。

## Parallel Example

- T011＋T012（contract case×wire_schema 裁判——異檔零相依；cargo 跑仍 serial）。
- T017 與 T016 異檔可併行編輯。
- T028（service 新檔）與 T024~T027（settings 單元）異檔零相依。
- T002 與 T001 異檔並行起草。

## Implementation Strategy

- **MVP 切片**＝Phase 1＋Phase 6（U0＋settings 頁）：最小可交付增量（側欄可進、16 鍵可管；
  seed-view-gate 恰餘一列）。
- 建議執行單元收攏（executing-plans 起手再批判複核）：U0=T001~T004｜U1=T005~T013｜
  U2=T014~T020｜U3=T021~T022｜U4=T023~T027｜U5=T028~T034｜U6=T035~T037。
- 每單元邊界：勾 T（隨做隨記）→子庫 commit→外層 `git add <子庫>`→generate→外層 commit
  （§2 六步序）；破壞性驗證（T019／T022 變異）還原守衛先行。
