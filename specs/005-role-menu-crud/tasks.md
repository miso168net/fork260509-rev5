# Tasks: 005 role＋menu 管理 CRUD 寫端（含序列化域與判定面同步基建）

**Input**: Design documents from `/specs/005-role-menu-crud/`

**Prerequisites**: [plan.md](./plan.md)（必要）、[spec.md](./spec.md)（US 與優先序）、
[research.md](./research.md)（R1 rev4 碼清單／R2 差異點／R10 單元骨架）、
[data-model.md](./data-model.md)（狀態機矩陣／守門固定序）、[contracts/](./contracts/wire-role-admin.md)、
[quickstart.md](./quickstart.md)（驗證動線）

**Tests**: 含測試任務——CLAUDE.md §2 規定 TDD（紅→綠）。後端＝cargo 整合測＋contract case
＋lint 型測；前端零測試框架 ⇒ 把關＝`pnpm typecheck`＋fork-delta-lint＋view-render-guard＋
CDP 走查（quickstart §4）。

**Organization**: 依 user story 分 phase；R10 單元映射見「Dependencies」節（編排時每執行
單元一支 workflow）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：檔域不相交、可分派給不同執行單元。★僅指「可分派」——**cargo 執行一律序列**
  （容器內 `--test-threads=1`）。
- **[Story]**：US1~US5（Setup／Foundational／Polish 不掛）。

## 全程紀律（每 task 隱含、不逐條重複）

- ★**實作前先讀** research R1 對應之 rev4 碼（`../fork260509-rev4/…` 直讀；★該樹絕不寫入、
  不 checkout；派 agent 時唯讀令必烤進 prompt）；重打字消化不拷貝、註解 rev5 語境重寫
  （rev4 出處帶 `rev4:` 前綴）；**research R2 十一筆差異點不得帶回**（憲法 §I.5＋ADR 0019）。
- ★**Amendment 硬閘**：T002 未 accepted 前**不得動任何 base-web fork 既有檔**。純新增檔
  （`rev5-role-admin.ts`／`rev5-menu-admin.ts`＋兩支 d.ts）依 ADR 0021 款 1 不受此閘；
  `zh-tw.ts` 雖屬孤立檔、其編輯受 Lint24 同步律約束。
- ★**Lint24 同步律**（照 004 全文；跨子庫、閘讀工作樹）：後端新增實發 msg key ⇔ 前端四處
  （zh-tw.ts／en-us.ts backend 樹／zh-cn.ts backend 樹／app.d.ts 型節）同一次工作樹編輯內
  齊備；孤兒鍵窗不得跨越任何一次外層 commit。
- rust build／test 一律容器內、全程序列：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api cargo test --workspace -- --test-threads=1`。
- ★**絕不 push／merge**（本清單零 push／merge 任務）。
- **兩段式 commit＋pin bump** 於單元邊界即時做；★單元邊界 commit 恆含 `docs-sync.py generate`
  → `git add docs/generated`（ROUTES 增列 ⇒ 併 reference/routes）。
- ★**測試環境紀律**（data-model §6／research R8）：寫 `sys_role`／`sys_menu`／`casbin_rule`／
  歸檔表之測試一律走本刀清理守衛（T012）＋顯式大 id＋sequence 還原斷言；redis 不涉本刀。
- ★**序列化域紀律**：域鎖必為 txn 首動作、絕不下沉 facade fn；固定鎖序＝
  `advisory → 歸檔表列 → sys_role 列 → sys_menu 列 → casbin_rule`（research R4）。

---

## Phase 1: Setup（★主線閘：憲法 Amendment＋ADR＋早期查證）

**Purpose**: 取得 base-web inline 憲法授權、立三支 ADR、清除 gate2 互動未知數、
搬 PageRes 與稽核詞彙底座。

- [ ] T001 ★主線任務（user 親決）：撰寫憲法 Amendment 之 ADR draft 於
  `docs/arc42/decisions/`——島 H 五條全文（data-model §4 骨架；H1 含終態成員與 advisory
  key space 句、H3 含常量父鏈句；MAJOR 界定照 rev4:0052 字面；常數留活書）＋§III.2
  `MANAGE-PAGE-WIRING` 加用途 (ii)（檔級名單＝role 3 檔＋menu 2~3 檔逐支列出、兩顆授權
  modal 明文不入）＋B-087 殘餘②補註（目標句逐字形、不單獨 bump）。
  ★前置半步：先 diff `rev4:base-web/.../manage/menu/modules/shared.ts` 對 upstream 判定其
  入單與否——名單以**定數**落、不得帶「視需要」（檔級硬邊界；grilling G3）。
- [ ] T002 ★主線任務（user 親決後）：ADR 轉 accepted＋更新 `.specify/memory/constitution.md`
  （v1.6.2→v1.7.0、修訂日誌行）＋`tools/docs-sync.py generate`。★本 task 完成前：一切
  base-web 既有檔凍結。
- [ ] T003 ★主線任務（user 親決）：兩支連帶 ADR——①判定面同步翻案（翻 `enforce.rs:8`／
  `main.rs:56`「不再重載＝終態」；含 reload 觸發矩陣、rebuild-swap 失敗契約、裸呼硬禁令＋
  casbin 2.20.0 版本鎖、ABBA 三失效條件）②A1 域行為（deleteRole 入域＋deleteRole 免 reload
  論證＋島 G1/G3/G4/G5 行為先由本 ADR 承載條文隨授權治理刀入憲＋archive 三自由度
  won't-use 與 rev4:0049 翻案觸發條款過境）。
- [ ] T004 早期查證項（research R8-2）：容器內實測 `sys_role_id_seq`／`sys_menu_id_seq`／
  `sys_casbin_policy_archive_id_seq`（data-model §6 一併覆核）推進
  × `tools/schema-gate.py check` 之 setval 互動——以顯式大 id INSERT＋seq 推進＋還原三種形
  各跑一輪 gate2，把「寫端推進後 gate 判定」結論以補記寫回本檔本 task 與 data-model §6；
  若需 gate 規則調整＝停手升級 user。
- [ ] T005 [P] `rust-api/server/src/model/audit.rs`：`AuditOperation` 小寫封閉詞彙擴充
  （role／menu 家族 add/update/delete/restore；含 batch 形的落列語意照 rev4 as-built——
  逐標的一列）＋既有防回歸測擴充；詞彙字面同步 `contracts/` 若有出入以本 task 定案。
- [ ] T006 [P] `PageRes<T>` 上移：`rust-api/server/src/envelope.rs` 落戶（自
  `handler/ip_rule.rs:71` 搬移、字面不變）＋ip_rule.rs 改引＋既有 contract 測改引零行為差。

**Checkpoint**: 憲法授權到手、三支 ADR accepted、gate2 互動已知、共用底座就緒。

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: 序列化域、判定面同步、鎖讀 helper、清理守衛、治理域讀端、歸檔寫入面。
**⚠️ 本 phase 未完成前不得開任何 US。**

- [ ] T007 `rust-api/server/src/model/facade/sys_casbin_archive.rs` 新建（★同批 mod.rs 掛載）：
  域鎖底座——`MENU_DOMAIN_LOCK_KEY: i64 = 0x7265_7635_6D65_6E75`（★rev5 字面、勿抄 rev4）＋
  `enter_menu_domain`（DbErr 形／AppError 形兩支薄 fn、raw Statement
  `SELECT pg_advisory_xact_lock($1)`）＋pg_locks 觀測 helper（classid／objid 拆讀）；
  照 rev4 底座 116 行形重打。
- [ ] T008 序列化域 ABBA／互斥機器證（`rust-api/server/tests/` 新測檔）：兩併發寫端
  （模擬 deleteRole × deleteMenu 形）後者於 advisory NOT-granted 等待之斷言＋完成後零漏
  歸檔；★坑烤入：pg_blocking_pids 測不到（鎖不相交列）、64-bit key 拆兩 oid 欄 bigint
  直比恆假（research R4）。
- [ ] T009 `rust-api/server/src/auth/enforce.rs`：`rebuild_enforcer`（四步鏡像 init、任一步
  失敗整體 Err）＋`reload_enforcer`（write 鎖內一行 move-assign、RELOAD_MAX_ATTEMPTS=3＋
  50ms 線性退避、keep-last-good、告警＋`casbin_reload_total{ok|retry|exhausted}`）＋
  ★硬禁令與版本鎖註解＋檔頭 `:8` 與 `main.rs:56` 註解翻案改寫（T003-① ADR 引）。
- [ ] T010 判定面同步測三支（第四支端到端在 T033）：SC-013 形失敗注入（壞 conn ⇒ 舊面續
  allow R_SUPER＋metrics retry/exhausted）／「改寫為裸呼 load_policy」必轉紅負向自證
  （明文步驟註解）／觸發條件特性鎖定（Rejected／NoOp／NotFound／無 buttons 變更零觸發）。
- [ ] T011 [P] 鎖讀 helper＋常數：`rust-api/server/src/model/facade/sys_role.rs`
  （`SEEDED_ROLE_IDS=[1,2,3]`＋`SUPER_ROLE_CODE="R_SUPER"`＋`find_active_by_id_for_update`
  家族）；`sys_menu.rs` 同形 helper。零寫端（寫端在各 US）。
- [ ] T012 [P] 清理守衛家族（`test_db`）：RoleCleanup／MenuCleanup／CasbinCleanup（casbin_rule
  ＋歸檔表）三件 RAII Drop 守衛＋★守衛自證測各一（造 committed 列→前提自證非零→Drop→
  回零＋sequence 還原斷言照 004 `sequence_reset_guard` 形；B-085 紀律——Drop 寫壞＝恆綠之防）。
- [ ] T013 `rust-api/server/src/model/facade/sys_menu.rs`：治理域讀端 `list_governed`（未刪
  含停用）＋樹組裝＋★「治理候選誤用顯示域＝停用被 diff 掉」負向測（rev4:010 血淚；
  data-model §3.1）；顯示域 `list_active` 零改動斷言。
- [ ] T014 `sys_casbin_archive.rs`：歸檔寫入面 `insert_archived`（完整快照＋role_id nullable
  誠實退化＋archive_reason）＋reason gate 單點 fn `is_non_restorable_reason`（三值集）＋
  集合成員測＋「role_id 查無活角色寫 NULL」測。

**Checkpoint**: 域鎖／同步／守衛／讀端／歸檔五底座就緒＋機器證全綠；可開 US。

---

## Phase 3: User Story 1 — 超管管理角色全生命週期（P1）🎯 MVP

**Goal**: 角色列表／新增／編輯／刪除／批刪全真；三層守門固定序；停用雙護欄；memo 欄。

**Independent Test**: quickstart §1 步 1~6＋§4-1（Super 全流程、Admin 讀通寫拒）。

### Tests for User Story 1 ⚠️（先紅後綠）

- [ ] T015 [US1] `rust-api/server/tests/contract.rs`：role 六端點 contract case（動詞×路徑×
  授權態矩陣：Super 通／Admin 寫端 5003 讀端通／R_USER_COMMON getAllRoles 通其餘 5003）——
  ★先紅（端點未建）；ROUTES 逐欄對齊 seed 政策列。

### Implementation for User Story 1

- [ ] T016 [US1] `sys_role.rs` 讀端：`page_query`（分頁＋roleName/roleCode 模糊＋status 等值
  ＋`id ASC`＋逐欄構造含 role_memo）＋`all_active_enabled`（★無 memo；僅活性啟用）＋
  createdBy/updatedBy 批次 enrich（004 範式）＋測。
- [ ] T017 [US1] `sys_role.rs` 寫端一：`create`（code 形制 `^[A-Za-z0-9_]{1,64}$`→活性唯一
  先驗＋23505 兜底同鍵）＋`update`（roleCode 不可變顯式拒／三態 ADR 0023／全 None 提前
  no-op／停用雙護欄：自身所屬拒＋R_SUPER 恆禁「不因操作者身分而異」）＋逐守門測。
- [ ] T018 [US1] `sys_role.rs` 寫端二：`delete_one_locked`（★域鎖 txn 首動作→三層守門固定序
  seeded→in-use〔others=total−operator_is_member、拒因回總掛載語意〕→self-role→全三維
  含 protected 歸檔 `role_soft_delete`→同交易 op-log）＋`batch_delete`（id 升冪逐項全套、
  任一違規整批拒、單 txn；空陣列語意照 rev4 as-built 定案並測）＋★in-use／self-role 以
  測試種 `sys_user_role` 指派列構造（G6：資料態零旗標）＋★deleteRole 零 reload 特性斷言。
- [ ] T019 [US1] `rust-api/server/src/handler/role.rs` 六支 handler＋`router.rs` +6 條
  （`ROUTES_COUNT` 22→28 同 commit bump）＋T015 轉綠＋wire-schema 快照更新。
- [ ] T020 [US1] 前端（★T002 後）：`service/api/rev5-role-admin.ts`＋`typings/rev5-role-admin.d.ts`
  （新增型）＋`views/manage/role/{index.vue,modules/role-operate-drawer.vue,modules/role-search.vue}`
  接真（列表含 roleMemo 欄／drawer memo textarea＋「管理員可見」placeholder／刪除批刪確認流；
  修改型逐行 `原行:`）＋i18n：`biz.role.*` 九鍵四處同步（msg-keys 候選字面）＋role 頁欄位鍵
  ＋`pnpm typecheck` 綠。

**Checkpoint**: US1 可獨立驗收（quickstart §1-1~6；兩顆授權 modal 一行未動）。

---

## Phase 4: User Story 2 — 超管管理選單樹（P1）

**Goal**: 選單樹 CRUD 全真；樹守門（防環／parent 三處／constant 父鏈／不可變錨欄）；
buttons 絕版歸檔＋判定面同步。

**Independent Test**: quickstart §1 步 7~11＋§2＋§4-2。

### Tests for User Story 2 ⚠️

- [ ] T021 [US2] `tests/contract.rs`：menu 六端點（getMenuList/v2★字面／getMenuTree／add／
  update／delete／batchDelete）contract case＋授權態——先紅。

### Implementation for User Story 2

- [ ] T022 [US2] `sys_menu.rs` 讀端：`page_query_governed`（樹形、分頁頂層計、size clamp
  常數★與 rev5 前端 hook 無參呼叫形對齊——本 task 先 grep `useNaivePaginatedTable` 預設
  定值再定常數）＋`menu_tree`（輕量樹）＋menuMemo 欄＋測。
- [ ] T023 [US2] `sys_menu.rs` 寫端一：`create`（守門序＝parent 三態〔存在未刪／停用不擋／
  頂層豁免〕→防環〔上溯上限常數〕→routeName 活性唯一雙層→constant 父鏈→形制；
  零 casbin 寫）＋逐守門測（含 constant 父鏈正反例）。
- [ ] T024 [US2] `sys_menu.rs` 寫端二：`update`（routeName／menuType 不可變顯式拒／改父
  防環＋★constant 父鏈重驗〔改父／改 constant 兩觸發點；FR-018、analyze C1 補〕／三態）＋
  ★buttons 絕版判定（聯集域＝未刪含停用、clarify Q1）＋絕版碼歸檔 `menu_button_removed`
  ＋非絕版移除零歸檔測。
- [ ] T025 [US2] `sys_menu.rs` 寫端三：`delete_one_locked`（守門固定序 protected→未刪子項
  不論啟停→menu 維跨角色＋獨有碼歸檔皆 `menu_soft_delete`→op-log）＋`batch_delete`
  （child-first 拓撲序、整批拒、單 txn）＋逐守門測。
- [ ] T026 [US2] `handler/menu.rs` 六支＋router +6 條（`ROUTES_COUNT` 28→34）＋★reload 接線
  （deleteMenu／batchDeleteMenu／updateMenu-buttons 成功且有歸檔 ⇒ commit 後 reload；
  觸發矩陣特性測 T010 擴充轉綠）＋T021 轉綠＋wire-schema 快照。
- [ ] T027 [US2] 前端（★T002 後）：`rev5-menu-admin.ts`＋d.ts（新增型）＋
  `views/manage/menu/{index.vue,modules/menu-operate-modal.vue}`（＋shared.ts 視需要）接真
  （樹表含 menuMemo／modal 父選擇器＝getMenuTree★移除 fetchGetAllRoles 殘留／buttons 編輯／
  constant 開關；修改型逐行標記）＋i18n：`biz.menu.*` 九鍵四處＋menu 頁欄位鍵＋typecheck 綠。

**Checkpoint**: US2 可獨立驗收；已知態③（新建選單側欄不現）照 quickstart §4-3 驗現狀形。

---

## Phase 5: User Story 3 — 選單回收桶與復原（P2）

**Goal**: toggle 顯示已刪；復原重驗（同鍵衝突／父未刪）；原 status 保留；零回灌。

**Independent Test**: quickstart §1 步 12＋§4-2。

### Tests for User Story 3 ⚠️

- [ ] T028 [US3] `tests/contract.rs`：getDeletedMenus／restoreMenu contract case——先紅。

### Implementation for User Story 3

- [ ] T029 [US3] `sys_menu.rs`：`list_deleted`（`deleted_at DESC, id DESC`、★無 restorable
  旗標——契約定案）＋`restore_locked`（域內鎖列→已刪存在→同鍵活性衝突 23505 兜底→父未刪
  →成對清空＋原 status 保留；零回灌零 reload）＋逐重驗測（含「復原現役列＝業務錯誤」
  R2-1 防回歸）。
- [ ] T030 [US3] `handler/menu.rs` 兩支＋router +2 條（`ROUTES_COUNT` 34→36）＋T028 轉綠。
- [ ] T031 [US3] 前端：menu index.vue toggle（「顯示已刪除」NSwitch 換資料源、已刪模式操作欄
  整欄換復原、confirmRestore 確認）＋i18n showDeleted/confirmRestore/restoreConflict 等。

**Checkpoint**: US3 可獨立驗收（刪→toggle 見→復原→原態回樹）。

---

## Phase 6: User Story 4 — 刪除後殘留授權即時失效（P2）

**Goal**: 零繼承鏈端到端閉環（DB＋in-memory 雙斷言）；同步失敗服務不中斷已由 T010 釘住。

**Independent Test**: quickstart §2＋§3。

- [ ] T032 [US4] 零繼承鏈端到端測（`tests/`）：★防恆綠前提自證——先種 live menu 維授權列
  ＋斷言非零→deleteMenu→DB 歸檔斷言＋★in-memory 判定面不再命中斷言→同 routeName 重建
  →零繼承雙斷言（DB＋判定面）；updateMenu 絕版路徑同構一組。
- [ ] T033 [US4] metrics 落點驗證測（`casbin_reload_total` 三 outcome 逐一可觸發）＋
  quickstart §2 手動 smoke 補記（本 task 收尾把實測輸出貼進 quickstart 對應節）。

**Checkpoint**: US4 可獨立驗收——島 H2 之 in-memory 半邊自此有機器證。

---

## Phase 7: User Story 5 — 角色首頁指定（P3）

**Goal**: roleHome 讀寫；寫端不驗一致性（讀端兜底既有）。

**Independent Test**: quickstart §1 對應步。

- [ ] T034 [US5] `sys_role.rs` home 讀寫 facade＋`handler/role.rs` 兩支＋router +2 條
  （`ROUTES_COUNT` 36→38 終態）＋contract case（先紅後綠）＋同交易稽核。

**Checkpoint**: 16 支端點全上、`ROUTES_COUNT=38` 終態。

---

## Phase 8: Polish & Cross-Cutting（DoD 收攏）

- [ ] T035 全量閘：容器 serial 全量 `cargo test` rc=0＋`docs-sync.py check` 0 錯誤＋
  `schema-gate.py check` 三閘綠（gate2 對三表零殘列＋seq setval 核——T004 結論複驗）＋
  wire-schema 快照 diff 符預期＋fork-delta-lint 綠（修改型僅 plan 檔集；★兩顆授權 modal
  `git diff` 零輸出斷言）＋view-render-guard 綠＋`pnpm typecheck` 綠。
- [ ] T036 CDP 三方對照（quickstart §4 全動線）：role 頁／menu 頁 vs rev4 42080 逐項；
  ★已知態三組驗「現狀形」（兩鈕假資料 modal／policy-archive 死項零反應／新建選單側欄不現
  管理列表可見）；發現差異＝逐項判定（rev5 拍板差異 or 缺陷）記錄於本 task 補記。
- [ ] T037 ★主線任務：`docs/ops/RUNBOOK.md` 增補（若有新操作面：域鎖觀測法／reload 告警
  查法——僅指針不展開）＋`docs/ops/BACKLOG.md` 帳面處置：B-025 敘述更新（deleteRole 窗
  客戶消滅）／B-003 改寫（role_memo＋menu_memo 兌現、剩 sys_user→刀 B）／B-091 rider
  順盤數條／★wf-watchdog journal 無心跳盲點落 LESSONS 新條（brainstorm §6 移交）。
  ★活書 as-built 不在本 task（收刀簿記；★注意 B-083：§6 已滿 120/120，as-built 落點
  屆時依該條三候選請 user 拍）。

---

## Dependencies & Execution Order

- **Phase 序**：Setup（T001~T006）→ Foundational（T007~T014）→ US1（T015~T020）→
  US2（T021~T027）→ US3（T028~T031）→ US4（T032~T033）→ US5（T034）→ Polish（T035~T037）。
- **硬閘**：T002 accepted 前凍結一切 base-web 既有檔（T020／T027／T031 之修改型段）。
- **US 依賴**：US2 依賴 US1 之 T019 router 段先落（ROUTES 遞增鏈）；US3 依賴 US2 facade；
  US4 依賴 US2/US3 寫端齊；US5 僅依賴 Foundational（可與 US3/US4 並行分派）。
- **R10 單元映射**（編排每單元一支 workflow）：U1=T001~T003｜U2=T004~T006｜U3=T007~T008｜
  U4=T009~T010｜U5=T011~T012｜U6=T013~T014｜U7=T015~T018｜U8=T019~T020｜U9=T021~T023｜
  U10=T024~T026｜U11=T027｜U12=T028~T031｜U13=T032~T033｜U14=T034｜U15=T035｜U16=T036｜
  U17=T037＋收刀簿記。
- **共享檔序列鏈（同檔不 [P]）**：`facade/sys_menu.rs`（T013→T022~T025→T029）、
  `facade/sys_role.rs`（T011→T016~T018→T034）、`facade/sys_casbin_archive.rs`（T007→T014）、
  `handler/role.rs`（T019→T034）、`handler/menu.rs`（T026→T030）、`router.rs`＋
  `tests/contract.rs`（T015→T019→T021→T026→T028→T030→T034 遞增鏈）、
  `views/manage/menu/index.vue`（T027→T031）。

## Parallel Example: Foundational

T007→T008（同域鎖面、序列）；T009→T010（同步面、序列）；此兩鏈與 T011、T012 四路可
並行分派（檔域不相交）；T013、T014 待 T007 落（sys_casbin_archive.rs 檔既存）後併入。

## Implementation Strategy

- **MVP＝US1**（role CRUD 全鏈＋前端 role 頁）——第一個可 CDP 對照的穩定點。
- 逐 US 增量：每 US 收尾＝contract case 綠＋單元邊界 commit（兩段式＋generate）；
  US2 起每單元附前輪 findings 清單（防呆六件套⑤收斂紀律）。
- 編排慣例：implementer=fable 1m xhigh、review=opus 1m xhigh、防呆六件套＋看門狗原子成對
  （CLAUDE.md §2；記憶 workflow-unit-orchestration-shape）。

## Notes

- 本檔零 push／merge 任務；finishing 由收刀程序（CLAUDE.md §2）承接。
- ROUTES_COUNT 遞增鏈 22→28→34→36→38；每段同 commit bump＋contract case 同步。
