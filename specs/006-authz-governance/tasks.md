# Tasks: 006 三維授權治理＋結構性封死＋授權回收桶（島 G 入憲）

**Input**: Design documents from `/specs/006-authz-governance/`

**Prerequisites**: [plan.md](./plan.md)（必要）、[spec.md](./spec.md)（US 與優先序、FR-001～FR-062）、
[research.md](./research.md)（R1 rev4 碼清單／R2 差異點 22 筆／R4～R9 落地細節／R10 治理原料／R12 單元骨架）、
[data-model.md](./data-model.md)（狀態機矩陣／五腿／觸發矩陣／島 G 骨架）、
[contracts/](./contracts/wire-authz-governance.md)（三維九支／回收桶兩支／msg-keys）、[quickstart.md](./quickstart.md)（驗證動線）

**Tests**: 含測試任務——CLAUDE.md §2 規定 TDD（紅→綠）；spec FR-057～FR-062 逐條要求。後端＝cargo 整合測＋
contract case＋lint 型測＋機器證；前端零測試框架 ⇒ 把關＝`pnpm typecheck`＋fork-delta-lint＋view-render-guard
＋route-artifact-gate＋CDP 走查（quickstart §4）。

**Organization**: 依 user story 分 phase；R12 單元映射見「Dependencies」節（編排時每執行單元一支 workflow、
implementer=fable xhigh／review=opus xhigh）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：檔域不相交、可分派給不同執行單元。★僅指「可分派」——**cargo 執行一律序列**（容器內 `--test-threads=1`）。
- **[Story]**：US1～US4（Setup／Foundational／Polish 不掛）。

## 全程紀律（每 task 隱含、不逐條重複）

- ★**實作前先讀** research R1 對應之 rev4 碼（`../fork260509-rev4/` 直讀；★該樹絕不寫入、不 checkout；派 agent 時唯讀令必烤進 prompt）；
  重打字消化不拷貝、註解 rev5 語境重寫（rev4 出處帶 `rev4:` 前綴）；**research R2 二十二筆差異點不得帶回**（憲法 §I.5＋ADR 0019）。
- ★**Amendment 硬閘**：T002 未 accepted 前**不得動任何 base-web fork 既有檔**（`menu-auth-modal.vue`／`button-auth-modal.vue`／
  `role-operate-drawer.vue`／`zh-cn.ts`／`en-us.ts`／`app.d.ts` 之 page 樹）。純新增檔（`endpoint-auth-modal.vue`、policy-archive 兩檔、
  `rev5-role-admin.ts`／`.d.ts` 追加、`zh-tw.ts` backend 鍵）與既有 I18N-WIRING (ii)(iii) 授權之 backend 樹增鍵不受此閘；純後端單元可先行。
- ★**Lint24 同步律**（跨子庫、閘讀工作樹）：後端新增實發 msg key ⇔ 前端四處（zh-tw.ts／en-us.ts backend 樹／zh-cn.ts backend 樹／app.d.ts 型節）
  同一次工作樹編輯內齊備；孤兒鍵窗不得跨越任何一次外層 commit；構造點一律字面 `Cow::Borrowed("…")`。
- rust build／test 一律容器內、全程序列（外層 repo 根）：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace -- --test-threads=1`。
- ★**絕不 push／merge**（本清單零 push／merge 任務）；★`cd 子庫 && git commit` 後外層動作前先 `cd` 回外層。
- **兩段式 commit＋pin bump** 於單元邊界即時做；★單元邊界 commit 恆含 `docs-sync.py generate`→`git add docs/generated`（ROUTES 增列 ⇒ 併 reference/routes）；
  ③落帳（BACKLOG／LESSONS／本檔全勾）早於⑤generate（L-018）。
- ★**測試環境紀律**（data-model §6／research R8-6）：寫 `casbin_rule`／歸檔表之測試 MUST 掛 `CasbinCleanup`（seq (163,true)／(1,false)）並與
  `RoleCleanup`／`MenuCleanup` 成對；顯式大 id 或真寫端後還原；清理／釋放先於斷言（持鎖 panic 掛死）；測後 `schema-gate.py check` 三閘綠；
  真登入 smoke 後全量照 L-050。
- ★**鎖序與 reload 紀律**（research R4／R7）：menu／button 維寫端域鎖為 txn 首動作、endpoint 維與 restorePolicy 不入域；固定鎖序
  advisory→歸檔表列→sys_role 列→sys_menu 列→casbin_rule；reload 於 commit 後且**不持 `state.enforcer` 讀鎖**呼叫；`RELOAD_CALL_FILES` 與接線同 commit 擴列（實得序以實跑為準）。
- ★**名冊閘**：`ENFORCER_WRITE_FILES` 維持空冊、`ALLOWED_DECISION_FILES` 維持恰一檔、casbin 版本錨不升版；handler 層零 path-root `entity::`；
  稽核詞彙恰五值（三維寫端 `Update`、restorePolicy `Restore`）。
- ★**共用件零拷貝**（FR-008）：新 handler 一律引用 `crate::handler::common`（audit_operator／json_or_default／MAX_CURRENT／resolve_operator_names 等）、facade 側引
  `model::facade::violated_constraint`；不得再生私有拷貝（B-094 收攏批之後的硬紀律）。
- ★**fork-delta 紀律**：修改型標記僅允許出現於 spec FR-047 檔集（逐行 `原行:`）；新檔檔頭 `[rev5-inline BASE-WEB-MANAGE-PAGE-WIRING(iii)+ 006-authz-governance]`（endpoint-auth-modal）／`…(iv)+ 006-authz-governance`（policy-archive 兩檔；as-built 定形、與憲法軌道名一致）；
  產物四檔只由外掛重算、不手改；`components.d.ts`／`service/api/index.ts` 預期零 diff。

---

## Phase 1: Setup（★主線閘：憲法 Amendment＋ADR 三支＋早期查證）

**Purpose**: 取得 base-web inline 憲法授權（§III.2 (iii)(iv)）、島 G 六條入憲、立三支 ADR、清除實作前未知數。

- [x] T001 ★主線任務（user 親決）：撰寫島 G 入憲 Amendment ADR draft（編號 0053、四款一檔、形照 ADR 0048 七段）於
  `docs/arc42/decisions/0053-constitution-amendment-island-g-and-manage-page-use-iii-iv.md`：款一 §I.7 第八座行為島（島 G 六條 blockquote＝data-model §4
  骨架＋research R10 落字差異五處）／款二 §III.2 加 (iii)(iv) 兩列 blockquote（首欄不留空、產物四檔路徑留 (i) 列、role-operate-drawer 同檔雙用途、
  endpoint-auth-modal 新增型不入名冊、三鈕不做 hasAuth gating）／款三 ADR 0052 生成檔條款入 §III 正文散文 bullet／款四 B-104 訂正＋訂正後完整 7 列觸發矩陣；
  front-matter `provenance` 含 ADR 0050（不 supersede）；後果段明列 FR-022 生效語意（API 判定即時／前端顯隱下次載入／不即時推播）。★user 親決兩題：①G5 條文層級（a 只寫「鎖內重驗＋reason gate＋同實例 NULL 誠實退化」、五腿留 0055／b 寫「固定序五腿」字樣）
  ②島 G header 括號寫不寫「六條」（建議照島 F 形列區間不列總數）。
- [x] T002 ★主線任務（user 親決後）：0053 轉 accepted＋更新 `.specify/memory/constitution.md`（v1.7.0→v1.8.0；research R10 八處、由下而上改：log 一行／版本行／
  表外宣告 2／§III.2 兩列／§III 第五 bullet／H1 括號回填〔第三態措辭〕／島 H header 括號回填／島 G 六條塊）＋`python3 tools/docs-sync.py generate`；同 commit
  （`docs(constitution): amend …`）。★本 task 完成前：一切 base-web 既有檔凍結。新列變異自證：暫改 (iii) 列範圍欄一路徑為裸措辭→fork-delta-lint 紅→還原。
- [x] T003 ★主線任務（user 親決）：兩支連帶 ADR draft→accepted——`docs/arc42/decisions/0054-structural-grant-lockout-protected-endpoints.md`
  （不變式謂詞／掛點恰兩處／射程外 menu 維四列已知態／非 vacuous 自證〔採 ADR 0024 精神、不主張屬其射程〕／翻案觸發條款／B-024③ 維持純 key／
  rev3 `3bfab71` 三缺陷三詞＋指針／後果＝B-024 改記殘餘）＋`docs/arc42/decisions/0055-restore-policy-five-leg-reverify-and-adr0050-recheck.md`
  （五腿照 ADR 0051 四段範式逐腿＋腿↔寫端守門對照表＋restorable 旗標①②③④同判準＋ADR 0050 §4 復核結論 B＋「rev4 七步／rev5 五腿計數軸不同」註＋
  字面定案於 spec〔`menu_revoke`／`button_revoke`〕）；`provenance` 含 ADR 0050；generate。
- [x] T004 早期查證（容器內、結論補記本 task）：①E0391 探針——在 `rust-api/server/src/handler/role.rs` 加最小 handler（本體直讀 `crate::router::ROUTES`）
  並**暫時註冊進 `router.rs` ROUTES**（`ROUTES_COUNT` 暫 +1）→`cargo build` 確認是否觸環→改為經具名 `policy_endpoints() -> Vec<Endpoint>`（具體回型、非 async）
  再編譯確認斷環→記結論→**全數還原、零殘留**（ROUTES／ROUTES_COUNT／探針碼）；②`RELOAD_CALL_FILES` 擴為三檔後 `scanned_files_excluding_home()` 實得序（暫改常數實跑
  `rust-api/server/tests/authz_entrypoint_lint.rs` 主守恆、記實得序後還原）；③核 `sys_casbin_archive.rs` 之 `is_non_restorable_reason_pins_three_member_set`
  負向臂是否真含三個 revoke 字面；④`grep -rn "AppState {" --include=*.rs rust-api/server/ | grep -v "pub struct\|-> "` 基線 7 命中複核。
  結論（2026-08-23 容器內實跑、U2 補記）：①E0391——第一形（handler 本體直讀 `crate::router::ROUTES`、暫註冊 ROUTES 39 條）`cargo build -p server` 觸
  `error[E0391]: cycle detected when computing type of opaque handler::role::probe_routes_len::{opaque#0}`（環＝borrow-checking handler→promoting constants
  in MIR→const checking `router::ROUTES`→type-checking `router::ROUTES`→回到 opaque 型）；第二形（具名非 async `fn probe_policy_paths() -> Vec<String>` 讀 ROUTES、
  handler 只呼它）`Finished dev`＝斷環成立 ⇒ T010 採具名 `policy_endpoints() -> Vec<Endpoint>`；探針全數還原（`git -C rust-api diff -- server/src/router.rs` 零輸出＝該檔長期可複核）；
  `server/src/handler/role.rs` 側之「diff 零輸出」屬**時點限定證據**〔T010 動工前實測，該檔隨後即承載 T010 交付物、diff 恆非零〕，
  後續單元複核改引長期形：`grep -rnE "probe_routes_len|probe_policy_paths" rust-api/server/` 全樹零命中（rc=1）。②`scanned_files_excluding_home()` 之 handler/ 實得序（暫加測 `--nocapture` 印出）＝…`handler/menu.rs` < `handler/mod.rs` <
  `handler/role.rs`…（menu<role 實證）；依 PathBuf 字典序 `handler/policy_archive.rs` 落於 mod.rs 與 role.rs 之間 ⇒ 三檔序假說 `["handler/menu.rs",
  "handler/policy_archive.rs","handler/role.rs"]` 成立；★最終由 U3（role.rs 接線）與 U6（policy_archive.rs 接線）時該主守恆測轉綠證實；探針已還原（該檔 diff 零輸出）。
  ③`is_non_restorable_reason_pins_three_member_set` 負向臂 `:362` 迴圈確含 `"menu_revoke"`／`"button_revoke"`／`"endpoint_revoke"`／`""` 四值（grep 複核）⇒ T005 改五值形、
  負向只剩 `endpoint_revoke` 與空串。④`AppState {` 基線命中恰 7（main.rs／router.rs／handler/ip_rule.rs／middleware/mod.rs／model/mod.rs／throttle/mod.rs／
  tests/common/mod.rs）＝與 test_db::test_state doc 名冊一致、本單元零新增。

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: reason gate 五值、批次讀端、聯集讀端、Option<i64> 守衛、三維 facade 骨架與讀端、wire DTO 與斷環 fn。
**⚠️ 本 phase 未完成前不得開任何 US（T005～T008 [P] 檔域不相交；T009～T010 序列）。**

- [x] T005 [P] `rust-api/server/src/model/facade/sys_casbin_archive.rs`：新立三常數 `REASON_MENU_REVOKE`／`REASON_BUTTON_REVOKE`／`REASON_ENDPOINT_REVOKE`
  （照既有三常數形）＋`is_non_restorable_reason` 擴五臂＋既有測 `is_non_restorable_reason_pins_three_member_set` 改名為五值形（正向餵獨立字面、負向剩
  `endpoint_revoke` 與空串）＋doc 改寫；★同檔 doc 順修：`:12-17` 域成員句改為「updateRoleMenu／updateRoleButton 入域；updateRoleEndpoints 與 restorePolicy 不入域」、
  `:34-36` 失真句改為如實（掃描面＝`archive_all_role_policies`＋`sys_menu.rs` 私有 `archive_policy_rows_of`）。
- [x] T006 [P] `rust-api/server/src/model/facade/sys_role.rs`：`active_ids_by_codes(conn, codes) -> HashMap<String,i64>`（純 SELECT、活性＝`deleted_at IS NULL` 不含 status、
  空集不打 DB、不取鎖）＋`active_code_of(conn, id) -> Option<String>`（窄投影、照 `home_of_role` 範式）＋測（停用角色仍回、已刪不回、空集零查詢）。
- [x] T007 [P] `rust-api/server/src/model/facade/sys_menu.rs`：`pub async fn all_button_codes(conn) -> Vec<String>`（`list_governed`→逐列 `button_codes_of`→HashSet 首見序去重；
  與 `obsolete_codes` 不共用）＋測（含停用選單碼、排除已刪、oracle 獨立重算對賬）。
- [x] T008 [P] `rust-api/server/src/envelope.rs`：`pub fn serialize_opt_i64_number_guarded`（None→null、Some→2^53 守衛）＋測（兩臂＋界外 fail-loud）。
- [x] T009 `rust-api/server/src/model/facade/sys_casbin_policy.rs` 新檔＋`model/facade/mod.rs` 掛載（ASCII 序 `sys_casbin_archive` < `sys_casbin_policy` < `sys_ip_rule`）：
  `Dimension{Menu,Button}`（`act()`／`revoke_reason()`）／`PolicyOutcome::{Applied{revoked,granted,effective}, Rejected{blocked}}`（blocked 永不上 wire）／
  `live_rows_of_dim`／`live_endpoint_rows`（方法白名單由 caller 傳入）／`current_targets`／`current_endpoints`（回帶 protected）／`menu_ids_to_route_names`＋
  `route_names_to_menu_ids`（治理域、orphan skip）＋單元測（白名單非反推：種 PATCH 列不得被納；映射 orphan skip 雙向；停用選單 route_name 反查得 id）。
- [x] T010 `rust-api/server/src/handler/role.rs` wire 段（不掛端點、編譯即可）：`Endpoint{path,method}`／`RoleMenuItem`／`RoleButtonItem`／`RoleEndpointItem`（帶 protected）／
  `GrantResult<T>`／`UpdateRoleMenuReq{id,menuIds}`／`UpdateRoleButtonReq{id,buttons}`／`UpdateRoleEndpointsReq{id,endpoints}`（皆 `Default`＋`json_or_default` 信封化）／
  `RoleIdQuery{id}`（`FromRequestParts` 收斂）＋`policy_endpoints() -> Vec<Endpoint>` 具名斷環 fn（依 T004 結論）＋`ENDPOINT_METHODS` 自 `HttpMethod::as_str()` 導出。

**Checkpoint**: Foundation ready——facade 讀端可測、DTO 就位。

---

## Phase 3: User Story 1 — 超管三維授權治理（選單／按鈕／端點）（P1）🎯 MVP

**Goal**: 三維讀寫六支全真：全量替換、protected 整批拒、orphan skip 三維、archive-move＋reason、grant 治理欄、入域兩支、Applied 即 reload（含空 diff）、判定即時生效。

**Independent Test**: quickstart §1（三維讀寫 curl）＋§2（判定面同步）＋§3（NOT-granted）；Admin 六支 5003。

### Tests for User Story 1 ⚠️（先紅後綠）

- [x] T011 [US1]（★單元移轉：原 U3→U4b 落地——contract coverage gate 雙向、case 無 route 即紅，與 T016 同單元紅→綠）`rust-api/server/tests/contract.rs`：三維六支 contract case（registry＋共用 verify fn 三段式＋貼界自證一支）＋授權態矩陣
  （Super 六支通〔空 body 收斂形期望碼逐支寫死〕／Admin、R_USER_COMMON 六支 5003；`hit_as_seed_user` 植 ConnectInfo）——先紅（端點未建）。
- [x] T012 [US1]（★選單／按鈕維案於 U3 落地 11 支；端點維案於 U4a 落地 10 支）`rust-api/server/src/model/facade/sys_casbin_policy.rs` tests（真 DB、`CasbinCleanup`＋`RoleCleanup`＋`MenuCleanup` 成對）：diff 正確（desired 含重複＋順序顛倒、同維隔離）
  ／空 diff `Applied{0,0}` 零歸檔現役不動／protected 整批拒（零變更、零歸檔、`Rejected.blocked` 命中）／orphan skip 三維（menu 失效 id、button 界外碼、endpoint 界外與非白名單 method）
  ／停用選單授權不被撤銷＋負向（誤用顯示域形必撤＝禁止形）／grant 治理欄（protected=false、created_at/by）／archive-move reason 三字面＋role_id 恆 Some／
  INSERT 排序確定性／角色列 FOR UPDATE（grant-during-delete 以 `pg_blocking_pids` 形、零殘留）。
- [x] T013 [US1] `rust-api/server/tests/menu_domain_serialization.rs`：updateRoleMenu／updateRoleButton 兩支入域寫端 NOT-granted 等待機器證（照既有骨架：基線零等待→txn1 入域
  →spawn txn2→觀測 `menu_domain_waiter_count`→釋鎖→斷言；結果存變數、清理先於斷言）——先紅。

### Implementation for User Story 1

- [x] T014 [US1] `sys_casbin_policy.rs`：`set_role_dimension(db, role_id, dim, desired, operator) -> Result<PolicyOutcome, RoleDimensionError>`（自管 txn：`enter_menu_domain_db` 首動作→
  `find_active_by_id_for_update`〔查無→NotFound〕→鎖內治理域映射 orphan skip→live 讀→diff→protected 整批拒（rollback、Rejected）→archive-move（`insert_archived` 逐列＋by-id DELETE）
  →INSERT（排序）→op-log `Update`／`sys_role`／`{dimension,revoked,granted}`→commit→Applied）；T012 menu／button 案轉綠、T013 轉綠。
- [x] T015 [US1]（as-built 多一參 `methods: &[&str]`——白名單由 caller 傳入、research R5-5；封死鉤位預留於 apply_endpoints_locked、U5 T019 接）`sys_casbin_policy.rs`：`set_role_endpoints(db, role_id, desired, candidates:&HashSet<(String,String)>, operator)`（不入域；候選集 orphan skip；同核心；★預留封死鉤位由 T018 接）；
  T012 endpoint 案轉綠。
- [x] T016 [US1] `rust-api/server/src/handler/role.rs` 六支 handler（讀端 `active_code_of`→`current_*`；寫端→facade→`Applied`⇒`reload_enforcer(&state)`／`Rejected`⇒
  `Err(Biz("biz.role.protectedRevoke"))`／NotFound⇒`biz.role.notFound`）＋`rust-api/server/src/router.rs` +6 條（`ROUTES_COUNT` 38→44、doc 沿革一行）＋
  `rust-api/server/tests/authz_entrypoint_lint.rs` `RELOAD_CALL_FILES` 加 `handler/role.rs`（實得序依 T004）＋doc 改寫＋`rust-api/server/src/auth/enforce.rs:138-162` 觸發矩陣 doc
  擴 7 列＋「grant 面刻意例外：Applied 即觸發、不問 diff」句＋`:162` 改寫（釘死句保留）＋`biz.role.protectedRevoke` 四處 i18n（`base-web/src/locales/langs/zh-tw.ts`／
  `zh-cn.ts`／`en-us.ts` backend 樹＋`base-web/src/typings/app.d.ts` backend 型節）＋T011 轉綠＋generate routes。
- [x] T017 [US1] 端到端（`rust-api/server/src/handler/role.rs` endpoint_tests、`test_db::real_app_and_state_with` 同一顆 enforcer）：grant 面觸發特性測（Applied 觸發／Rejected 不觸發／
  空 diff 觸發；`casbin_reload_total{outcome="ok"}` 增量形照 `handler/menu.rs` 既有矩陣測）＋判定即時生效雙斷言（新授→`enforce_role_path_method` allow、撤銷→deny）＋三讀端
  protected 旗標回讀；全量綠＋schema-gate 綠。

- [x] T037 [US1]（★實作期新增、user 親決 2026-08-23、ADR 0056；as-built：濾點＝單一 helper scope_live_to_candidates 三路同用；R_SUPER wire 案以「候選內現役全集 Save→0000／revoked 0／granted 0／reload +1、候選外 seed 列原封」承載——R_SUPER 已持有候選集全部 30 端點、granted 1 在零 seed 變更下結構上不可達，真豁免由 facade savepoint 測承載）全量替換射程＝候選集：`sys_casbin_policy.rs` 三路於鎖內 live 讀後、diff 前以候選集濾 live
  （選單維＝治理域 route_name 集、按鈕維＝治理域 buttons 聯集、端點維＝候選集 ∩ 白名單）；候選外現役列不撤不授不入 effective；doc 同步；
  三維各一支「候選外現役列不動」測（端點維含 protected 候選外列；既有期望「候選外列被撤」之測逐案改）＋`handler/role.rs` endpoint_tests
  「R_SUPER 自授 P 中端點→0000」wire 案（U5 升級①所述結構性打不出者自此可打）；全量綠＋schema-gate 綠。

**Checkpoint**: US1 可獨立驗收（quickstart §1 三維段＋§2＋§3；前端仍 demo 殼）。

---

## Phase 4: User Story 2 — 結構性封死（P1）

**Goal**: 治理面受保護端點政策 MUST NOT 授予非 R_SUPER（謂詞式、鎖內現查）；掛 updateRoleEndpoints（restorePolicy 第③腿由 US3 共用）；非 vacuous＋變異自證。

**Independent Test**: quickstart §1 封死 curl（R_ADMIN 授 `POST /systemManage/updateRoleEndpoints`→2222 `biz.role.protectedGrant` 零變更；非受保護→通；R_SUPER 自授→通）＋§3 變異自證。

### Tests for User Story 2 ⚠️

- [x] T018 [US2] `sys_casbin_policy.rs` tests＋`handler/role.rs` endpoint_tests：封死三案（非 R_SUPER 授 protected 端點→Rejected 零變更零歸檔零 reload／R_SUPER 自授通／
  非 protected 端點通）＋固定序（protected 整批拒先於封死）＋歸檔表中 protected=TRUE 原值之列恆零（SC-006 機器斷言）——先紅。

### Implementation for User Story 2

- [x] T019 [US2] `sys_casbin_policy.rs`：`protected_endpoint_set(conn) -> HashSet<(String,String)>`（謂詞 `ptype='p' ∧ protected=TRUE ∧ v2∈方法白名單`、單次 SELECT、鎖內現查）＋
  `set_role_endpoints` 接封死腿（角色 `role_code != SUPER_ROLE_CODE` ∧ to_grant ∩ 集≠∅⇒`Rejected`〔blocked 記封死項〕；拒因鍵 `biz.role.protectedGrant`）＋handler 映射＋
  四處 i18n＋doc 承重前提（ADR 0050 §4；un-protect 永不 UI 化）＋★變異自證（拆掉謂詞守門→T018 紅→還原→綠；report 附三次結果）；T018 轉綠。
- [x] T020 [US2]（結論：harness 已建成＝`auth/enforce.rs` tests `reload_serial_holds_second_reload_until_first_swaps_then_last_rebuild_wins`、seam＝`#[cfg(test)] mod reload_seam`＋臨界區內 cfg(test) pause 點、生產零變更；B-105 關帳）B-105 seam harness 自拍（跨切項：屬 G1 判定面同步、隨 U5 單元施工；`rust-api/server/src/auth/enforce.rs` tests）：`RELOAD_SERIAL` 交錯時序 seam 形 harness（後 commit 先 swap／先 commit 慢 rebuild 蓋回）
  ——可證即補；成本失控＝BACKLOG B-105 留帳附記「006 已把 reload 呼叫者 3→7、harness 仍未建」（本 task 補記結論）。

**Checkpoint**: US2 可獨立驗收（US1 端點維寫端上的封死；restorePolicy 路徑待 US3）。

---

## Phase 5: User Story 3 — 授權回收桶（P2）

**Goal**: getArchivedPolicies（雙濾、DESC、restorable 四腿批次旗標）＋restorePolicy（五腿固定序、三態、不入域）＋policy-archive 獨立頁＋B-088 對賬閘。

**Independent Test**: quickstart §1 回收桶 curl（endpoint 維手動撤銷列 restorable=true 可復原；menu／button 維列 false）＋§4-5 頁面。

### Tests for User Story 3 ⚠️

- [x] T021 [US3] `rust-api/server/tests/contract.rs`：回收桶兩支 contract case＋授權態（Super 通、Admin／User 5003）＋貼界自證（與 US1 POST 對）——先紅；
  `sys_casbin_archive.rs` tests：list 雙濾／DESC／分頁 total／旗標逐腿（reason 五值、同實例、NULL、封死、端點在冊；menu 維列恆 false；對照組 endpoint_revoke true）
  ＋restore 五腿各負向（歸檔列不消費、零變更）＋NoOp（歸檔列消費、零 op-log、零 reload）＋Applied（回灌欄值：protected=false、created_at 新、created_by 復原者；歸檔列刪；op-log `Restore`）
  ＋23505 競態→NotRestorable＋restore-during-delete（`pg_blocking_pids` 形、零殘留）——先紅。
- [x] T022 [US3] `sys_casbin_archive.rs`：`ArchivedRecord`／`dimension_of`／`list(conn, filter, page, size) -> (Vec<ArchivedRecord>, total)`（restorable 批次料源：單點 fn＋
  `active_ids_by_codes`＋`protected_endpoint_set`＋候選集參數）＋`restore(db, archive_id, candidates, operator) -> RestoreOutcome`（鎖歸檔列→①→鎖活角色 by v0→②→③（共用 T019 fn）→④→⑤→7a／7b）；
  T021 facade 案轉綠。
- [x] T023 [US3] `rust-api/server/src/handler/policy_archive.rs` 新檔（`ArchivedPolicyQuery` 四欄 Option＋`RestorePolicyReq{id}` Default＋`ArchivedPolicy` 14 欄〔`archivedBy` enrich
  帳號名——走 `common::resolve_operator_names`、既有 B-106 範圍、去重後個位數；`roleId` 用 T008 守衛〕＋`to_wire`＋兩支 handler：Applied⇒reload／NoOp⇒ok／NotRestorable⇒`biz.policy.notRestorable`）＋`handler/mod.rs` 註冊（menu 與 role 之間、doc 同步）
  ＋`router.rs` +2（44→46）＋`RELOAD_CALL_FILES` 加 `handler/policy_archive.rs`＋`biz.policy.notRestorable` 四處 i18n（新開 `biz.policy` 子樹）＋T021 contract 轉綠＋generate。
- [x] T024 [US3] 前端 policy-archive 頁（★T002 後）：`base-web/src/views/manage/policy-archive/index.vue`（tsx、`useNaivePaginatedTable`＋`defaultTransform`、8 欄、NTag dimension、
  archiveReason 原字面、restorable=false 停用鈕、restore→`fetchRestorePolicy`→`if (error) return;`→toast→`getData()`、scroll-x 自算＝Σ、表頭僅 refresh）＋
  `modules/policy-archive-search.vue`（照 ip-rule-search 範式、reset 補 emit）＋`base-web/src/service/api/rev5-role-admin.ts` 追加 `fetchGetArchivedPolicies`／`fetchRestorePolicy`＋
  `base-web/src/typings/api/rev5-role-admin.d.ts` 新 `Api.PolicyArchive` 命名空間（`ArchivedPolicyDimension`／`ArchivedPolicy`／`ArchivedPolicyListQuery`／`ArchivedPolicyListRes`）＋
  i18n `page.manage.policyArchive` 15 鍵（zh-cn／en-us 插 `role` 後、app.d.ts page 型節）＋`route['manage_policy-archive']`（圈界塊形）＋路由外掛重算產物四檔＋
  `tools/route-artifact-gate.py check`＋`tools/view-render-guard.py check`＋`pnpm typecheck`。
- [x] T025 [US3]（as-built：pre-commit 觸發＝base-web／rust-api gitlink 或工具本體 staged——seed 檔住 rust-api worktree、其變動以 rust-api pin bump 顯現；另加結構自證「導出集恰等 `router/elegant/imports.ts` 鍵集」、幽靈豁免亦紅；量測 seed view.* 51／views 導出 50／imports 50、豁免 2；docs-sync 乾跑案缺→B-114）`tools/seed-view-gate.py` 新建（B-088：seed `sys_menu.component` 之 `view.*` 集 ⊆ `base-web/src/views/**` 導出集；具名豁免常數兩列 `manage_system-settings`／
  `manage_audit` 各附 B-008 指針、到期即紅形；self-test 防恆綠；ADR 0024 三項自證〔合成正例／非共變判準／真檔暫改破壞性驗證且關鍵行寫進 commit message〕）＋接線：
  `.githooks/pre-commit` 迴圈（base-web pin 或 seed 檔 staged 時）＋`tools/bootstrap.sh` 體檢＋`tools/docs-sync.py` `TOOLS_PY` 納冊＋README 工具樹（Lint27）＋`generate` 重算 tools-cli。

**Checkpoint**: US3 可獨立驗收（quickstart §1 回收桶＋§4-5）。

---

## Phase 6: User Story 4 — 三顆授權 modal 接真＋roleHome＋支撐讀（含既有破口修復）（P2）

**Goal**: 支撐讀三支（getAllPages 修復 menu 頁 404）、wrapper／typings 追加、三 modal 接真（protected 鎖定、cascade、roleHome）、B-099 順修。

**Independent Test**: quickstart §4 步 1～4、6、7（CDP 三方對照）。

### Tests for User Story 4 ⚠️

- [x] T026 [US4]（as-built：先紅後綠；router t027 對齊測＋contract 矩陣＋endpoint_tests 三支 oracle 獨立重算〔ROUTES 反查／raw SQL jsonb／raw SQL COALESCE 序〕；fixture id 段 9_800_100 全樹首用）`rust-api/server/tests/contract.rs`：支撐讀三支 contract case＋授權態（Admin／User 5003；getAllPages 為 protected=FALSE 但仍 R_SUPER 政策）；
  `handler/role.rs` endpoint_tests：getAllEndpoints 回應集＝ROUTES Policy 全集恰等（不多不漏）／getAllButtons＝治理域聯集（oracle 獨立重算、含停用選單碼）／
  getAllPages＝顯示域（停用選單不現、`(order,id)` 穩定序）——先紅。

### Implementation for User Story 4

- [x] T027 [US4]（as-built：ROUTES 49／Policy 35 終態、POLICY_ENDPOINT_COUNT 32→35；全量 760→765；handler/common.rs 檔頭預告句同步改現在式；getAllButtons 候選序沿 list_governed 無 ORDER BY→B-115）`handler/role.rs` 三支支撐讀 handler（getAllPages 經 `list_active` 排序、getAllButtons 經 T007、getAllEndpoints 經 `policy_endpoints()`）＋`router.rs` +3
  （46→49、最終值）＋T026 轉綠＋generate routes＋`handler/mod.rs` doc（role 八端點→十七支）與 `handler/common.rs` 檔頭預告句同步；menu 管理頁 page 下拉 404 破口自動修復（CDP 於 T035 驗）。
- [ ] T028 [US4]（★待 T024 後：同檔追加、不與 US3 前端並行）`base-web/src/service/api/rev5-role-admin.ts`（6→18：+`fetchGetRoleMenu(id)`／`fetchUpdateRoleMenu`／`fetchGetRoleButton`／`fetchUpdateRoleButton`／
  `fetchGetRoleEndpoints`／`fetchUpdateRoleEndpoints`／`fetchGetAllButtons`／`fetchGetAllEndpoints`／`fetchGetRoleHome`／`fetchUpdateRoleHome`；`fetchGetAllPages` 不新建）＋
  `base-web/src/typings/api/rev5-role-admin.d.ts`（`Api.RoleAdmin`：`Endpoint`／`RoleMenuItem`／`RoleButtonItem`／`RoleEndpointItem`／`GrantResult`／三 Req／`RoleHomeRes`／`UpdateRoleHomeReq`）
  ＋`pnpm typecheck`（新增型、不受硬閘）。
- [ ] T029 [US4] `base-web/src/views/manage/role/modules/menu-auth-modal.vue`（★T002 後；修改型逐行 `原行:`）：接 `fetchGetRoleMenu`／`fetchUpdateRoleMenu`（checks 不再寫死、
  提交期望全集含 protected 項）＋protected 鎖定（TreeOption `disabled`＋受控 `checked-keys` 攔截補回）＋roleHome（`home: shallowRef<string|null>(null)`、NSelect `clearable`、
  `fetchGetRoleHome(id)`／`fetchUpdateRoleHome({id, home})`、候選＝`fetchGetAllPages` 走 barrel 一行不動）＋`fetchGetMenuTree` barrel 不動＋不加 cascade＋錯誤分支 `if (error) return;`。
- [ ] T030 [US4] `base-web/src/views/manage/role/modules/button-auth-modal.vue`（修改型、21 條原行）：假資料 button1..10 移除、候選＝`fetchGetAllButtons`（`ButtonConfig.id` 復用為 code、
  模板 `key-field="id"` 不動）＋`fetchGetRoleButton`／`fetchUpdateRoleButton`＋protected 鎖定＋`init()` 改 `watch(visible)`。
- [ ] T031 [US4] `base-web/src/views/manage/role/modules/endpoint-auth-modal.vue` 新檔（新增型、檔頭標記；`cascade`＋`check-strategy="child"`、葉鍵 `path|method`、群組鍵純 path、
  `leafMap` 反查不 split、protected 鎖定、`fetchGetAllEndpoints`／`fetchGetRoleEndpoints`／`fetchUpdateRoleEndpoints`）＋`role-operate-drawer.vue` 第三鈕＋掛載
  （純新增行、新增型圈界；同檔雙用途）＋`page.manage.role.endpointAuth` 三處（zh-cn／en-us／app.d.ts）＋typecheck；role/index.vue 一行不動。
- [ ] T032 [US4] `base-web/src/views/manage/ip-rule/index.vue` B-099 順修（default slot 外層 `<div v-show="hasAuth('ipRule:add')">` 保底＋內層 `v-if`；照 menu/index.vue 既驗形、條件不照抄）
  ＋`docs/ops/BACKLOG.md` B-099 條文失準觸發理由訂正（關帳於 T036）。

**Checkpoint**: US4 可獨立驗收（quickstart §4 全動線）。

---

## Phase 7: Polish & Cross-Cutting（DoD 收攏）

- [ ] T033 wire-schema 重抽（跨子庫兩段式：base-web 型 commit→容器內 `python3 tools/wire-schema.py extract`→`rust-api/server/tests/fixtures/wire-schema.json` commit→外層 pin）＋
  `rust-api/server/tests/wire_schema.rs` 新命名空間裁判（`Api.RoleAdmin` 新型＋`Api.PolicyArchive.*` 各正向＋反例；protected 欄、`roleId` null 形為重點；檔頭 doc 受審面補節、
  IpRule 七支留帳句不動）＋`python3 tools/wire-schema.py check` 綠；definitions 自 57 淨增（補記實數）。
- [ ] T034 全量閘：容器 serial 全量 `cargo test` rc=0（基線 682、淨增補記實數）＋`docs-sync.py lint` 0 錯誤＋`schema-gate.py check` 三閘綠＋`fork-delta-lint` 綠
  （修改型僅 FR-047 檔集；`components.d.ts`／`service/api/index.ts` `git diff` 零輸出斷言）＋`route-artifact-gate.py check`＋`view-render-guard.py check`＋`seed-view-gate.py check`
  ＋`pnpm typecheck` 綠＋三名冊閘綠（`RELOAD_CALL_FILES` 三檔實得序）。
- [ ] T035 CDP 三方對照（quickstart §4 全動線：三鈕錨點／選單 modal 真勾選＋鎖定＋首頁下拉／按鈕 modal 無假資料／端點 modal 群組連動／policy-archive 頁濾與復原／
  menu 頁 page 下拉非空／ip-rule 頁不冒鈕／已知態排除清單逐項驗現狀形）；★排 schema-gate 之後；走查後 psql 清殘列＋兩 seq 還原＋三閘複驗；差異逐項判定（rev5 拍板差異 or 缺陷）補記本 task。
- [ ] T036 ★主線任務：活書 `docs/arc42/ARCHITECTURE.md` §5（facade 11→12、reason gate 三值→五值、新增兩檔一句）＋§8（(iii)(iv) as-built、backend 樹 50 鍵改指節形、授權慣例子節
  加三維治理／封死／回收桶／觸發面條目〔含 FR-022 生效語意一句〕——落筆先算餘 13 行）＋§6 errata `docs-sync.py errata 六座`（唯一現在式「六座」→「八座」；一次補兩代）＋`docs/ops/BACKLOG.md` 帳務
  （刪 B-104／B-099；B-024 改記殘餘一句；B-098 註 IpRule 留帳；B-088 閘已建餘豁免兩列；B-083 甲案續掛；B-093／B-025／B-016／B-018／B-091／B-008／B-105／B-106 敘述各一行；
  新登「reload 呼叫點不得持讀鎖之源碼掃描守門候選」與「events summary 無 erratum 出口」兩條）＋LESSONS 新條（若有踩坑）＋`docs/ops/RUNBOOK.md` 指針（回收桶復原／封死拒因查法，
  僅指針）；收刀簿記（events feature_close notes 寫承接關係＋seed 68 歸刀 B、NOTES、generate）由收刀程序承接、不列 push／merge。

---

## Dependencies & Execution Order

- **Phase 序**：Setup（T001～T004）→ Foundational（T005～T010）→ US1（T011～T017）→ US2（T018～T020）→ US3（T021～T025）→ US4（T026～T032）→ Polish（T033～T036）。
- **硬閘**：T002 accepted 前凍結一切 base-web 既有檔（T029～T031 修改型段、T024／T031 之 zh-cn／en-us／app.d.ts page 樹；backend 樹增鍵與新檔不受此閘）。
- **US 依賴**：US2 依賴 US1 之 T015（endpoint 維 facade）與 T016（handler）；US3 之 restore 第③腿依賴 US2 T019；US4 之 T027 依賴 T010／T007；T028 可在 T002 前先行。
- **ROUTES_COUNT 遞增鏈**：38→44（T016）→46（T023）→49（T027）；每段同 commit bump＋contract case＋generate routes。
- **R12 單元映射**（編排每單元一支 workflow）：U1=T001～T003（主線）｜U2=T004～T010｜U3=T011～T014｜U4=T015～T017｜U5=T018～T020｜U6=T021～T023｜U7=T024～T025｜
  U8=T026～T027｜U9=T028～T032｜U10=T033｜U11=T034～T035｜U12=T036＋收刀簿記。
- **共享檔序列鏈（同檔不 [P]）**：`facade/sys_casbin_policy.rs`（T009→T012→T014→T015→T019）、`facade/sys_casbin_archive.rs`（T005→T021→T022）、`facade/sys_role.rs`（T006→T022 引用）、
  `handler/role.rs`（T010→T016→T017→T018→T019→T027）、`router.rs`＋`tests/contract.rs`（T011→T016→T021→T023→T026→T027 遞增鏈）、`tests/authz_entrypoint_lint.rs`（T016→T023）、
  `auth/enforce.rs`（T016 doc→T020）、`rev5-role-admin.ts`／`.d.ts`（T024→T028）、locales 三檔＋`app.d.ts`（T016→T019→T023→T024→T031）、`role-operate-drawer.vue`（T031）。

## Parallel Example: Foundational

T005／T006／T007／T008 四路可並行分派（檔域不相交）；T009 待 T005（reason 常數）後、T010 待 T009（型引用）後序列。US4 之 T028 可與 US1～US3 後端單元並行（新增型檔、不受硬閘）。

## Implementation Strategy

- **MVP＝US1**（三維讀寫六支＋入域＋reload 接線）——第一個可 API 驗收的穩定點；US2 緊接（封死在同一 facade）。
- 逐 US 增量：每 US 收尾＝contract case 綠＋單元邊界 commit（兩段式＋generate）；次輪 review prompt 附前輪已駁回 findings（防呆六件套⑤）。
- 編排慣例：implementer=fable 1m xhigh、review=opus 1m xhigh（ultrathink）、防呆六件套＋看門狗原子成對（CLAUDE.md §2）；U1 主線親做、user 親決兩題。

## Notes

- 本檔零 push／merge 任務；finishing 由收刀程序承接。
- 零 migration、零 seed 變更；任何單元冒出 DDL／seed 需求＝停手升級 user。
- 測試基準 682＝容器內實跑值；淨增數於 T034 補記。
