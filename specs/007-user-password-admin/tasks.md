# Tasks: 007 使用者＋密碼管理（島 I 入憲、授權下放＋no-escalation）

**Input**: Design documents from `/specs/007-user-password-admin/`

**Prerequisites**: [plan.md](./plan.md)（必要）、[spec.md](./spec.md)（US1～US6 與 FR-001～FR-050）、
[research.md](./research.md)（R1 rev4 碼清單 17 列／R2 差異點 28 筆／R4 落點表／R5 no-escalation／R6 斷權／R7 密碼面／R8 機器閘 14 條／R9 前端／R10 治理原料／R12 單元骨架）、
[data-model.md](./data-model.md)（狀態機三矩陣／島 I 骨架／錯誤碼／sequence）、
[contracts/](./contracts/wire-user-admin.md)（十支＋二支＋msg-keys）、[quickstart.md](./quickstart.md)（七節驗證動線）

**Tests**: 含測試任務——CLAUDE.md §2 規定 TDD（紅→綠）；spec FR-021／FR-046～FR-050 逐條要求。後端＝cargo 整合測＋
contract case＋lint 型測＋表驅動單元測；前端零測試框架 ⇒ 把關＝`pnpm typecheck`＋`pnpm exec oxlint <file>`（B-128）＋
fork-delta-lint＋view-render-guard＋CDP 走查（quickstart §6）。

**Organization**: 依 user story 分 phase；執行單元映射見「Dependencies」節（編排時每執行單元一支 workflow）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：檔域不相交、可分派給不同執行單元。★僅指「可分派」——**cargo 執行一律序列**（容器內 `--test-threads=1`）。
- **[Story]**：US1～US6（Setup／Foundational／Polish 不掛）。

## 全程紀律（每 task 隱含、不逐條重複）

- ★**實作前先讀** research R1 對應之 rev4 碼（`../fork260509-rev4/` 直讀；★該樹絕不寫入、不 checkout；派 agent 時唯讀令必烤進 prompt）；
  重打字消化不拷貝、註解 rev5 語境重寫（rev4 出處帶 `rev4:` 前綴）；**research R2 二十八筆差異點不得帶回**（憲法 §I.5＋ADR 0019）。
- ★**Amendment 硬閘**：T003 未 accepted 前**不得動任何 base-web fork 既有檔**（`views/manage/user/index.vue`／`modules/user-operate-drawer.vue`／
  `views/user-center/index.vue`／`views/_builtin/login/modules/pwd-login.vue`／`zh-cn.ts`／`en-us.ts` 之 page 樹／`app.d.ts` 之 page 型節）。
  純新增檔（unlock modal／pwd-gen／password-card／pwd-policy hook／`rev5-user-admin.*`／`rev5-user-center.*`）與既有 I18N-WIRING (ii)(iii)
  授權之 backend 樹增鍵不受此閘；純後端單元可先行。
- ★**Lint24 同步律**（跨子庫、閘讀工作樹）：後端新增實發 msg key ⇔ 前端四處（`zh-cn.ts`／`en-us.ts` backend 樹／`zh-tw.ts`／`app.d.ts` backend 型節）
  同一次工作樹編輯內齊備；孤兒鍵窗不得跨越任何一次外層 commit；構造點一律字面 `Cow::Borrowed("…")`；★`biz.user.passwordViolation.*` 八鍵為
  **前端內部詞彙表**（Lint24 白名單）、後端 MUST NOT 作 msg 發出（只作 `data.violations` 陣列成員）。
- rust build／test 一律容器內、全程序列（外層 repo 根）：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace -- --test-threads=1`；
  rust 碼完工前容器內 `cargo fmt --all`（ADR 0057）。
- ★**絕不 push／merge**（本清單零 push／merge 任務）；★`cd 子庫 && git commit` 後外層動作前先 `cd` 回外層。
- **兩段式 commit＋pin bump** 於單元邊界即時做；★單元邊界 commit 恆含 `docs-sync.py generate`→`git add docs/generated`（ROUTES 增列 ⇒ 併 reference/routes）；
  ③落帳（BACKLOG／LESSONS／本檔全勾）早於⑤generate（L-018）。
- ★**測試環境紀律**（data-model §6／research R8-8）：寫 `sys_user`／`sys_user_role` 之測試 MUST 掛 `UserCleanup`（業務鍵腿＋op-log 腿＋
  `setval('sys_user_id_seq',3,true)`）；寫 `sys_pwd_custody` 掛 `PwdCustodyCleanup`；動 seed 三帳號掛 `SeedOpLogCleanup::arm`；
  撤銷列與事件由既有 `ChainRowsCleanup`／`SessionEventCleanup` 管；顯式大 id 優先、只有 addUser 端點測走 nextval；
  清理／釋放先於斷言（持鎖 panic 掛死）；測後 `schema-gate.py check` 三閘綠；真登入 smoke 後全量照 L-050。
- ★**鎖序與 reload 紀律**（research R4／R5／data-model §3.4）：user 域寫端 advisory(uid) 為 txn 首動作（addUser 豁免）；固定鎖序
  advisory→`sys_user` 列→`sys_role` 列升序→`sys_user_role`；批刪依 id 升序逐一取鎖；lock-then-redecide；reload 於 commit 後呼叫、
  **不持 `state.enforcer` 讀鎖**；`RELOAD_CALL_FILES` 與接線同 commit 擴列（實得序以實跑為準）。
- ★**守門固定序**（data-model §3.1）：①活性標的鎖讀（`notFound`）②seed 保護③self 五不④`assert_no_escalation`⑤業務守門；
  任一拒＝零變更零稽核；批次任一違規整批 rollback（no-partial）。
- ★**名冊閘**：`ENFORCER_WRITE_FILES` 維持空冊、`ALLOWED_DECISION_FILES` 維持恰一檔、casbin 版本錨不升版；handler 層零 path-root `entity::`；
  稽核詞彙擴恰八值（新三值 `kick`／`reset_password`／`change_password`）。
- ★**共用件零拷貝**（FR-007）：新 handler 一律引用 `crate::handler::common`（`audit_operator`／`json_or_default`／`tristate`／`blank_to_none`／
  `db_status_to_wire`／`resolve_operator_names`／`MAX_CURRENT`）；facade 側引 `model::facade::violated_constraint`；不得再生私有拷貝。
- ★**fork-delta 紀律**：修改型標記僅允許出現於 spec FR-042 三用途檔集（逐行 `原行:`；模板側多行註解形）；新檔檔頭
  `[rev5-inline BASE-WEB-MANAGE-PAGE-WIRING(v)+ 007-user-password-admin]`（user 頁新檔）／`…(vi)+ …`（user-center 新檔）；
  產物四檔零重算（不新增 view 目錄）；`components.d.ts`／`service/api/index.ts` 預期零 diff。
- ★**密碼三重不洩**：密碼明文與雜湊 MUST NOT 出現於回應、稽核 payload、日誌（含 tracing）；測試以負向斷言（payload 不含 `$argon2`）釘死。

---

## Phase 1: Setup（★主線閘：憲法 Amendment＋ADR 首支＋早期查證）

**Purpose**: 取得 base-web inline 憲法授權（§III.2 (v)(vi)(vii)）、島 I 六條入憲、立首支 ADR、清除實作前未知數。

- [ ] T001 ★主線任務（user 親決）：撰寫島 I 入憲 Amendment ADR draft（編號 0063、三款一檔、形照 ADR 0053 七段）於
  `docs/arc42/decisions/0063-constitution-amendment-island-i-and-manage-page-use-v-vi-vii.md`：款一 §I.7 第九座行為島（島 I 六條 blockquote＝
  data-model §4 骨架；★I7 為 rev5 專屬新條、`A` 之「持 R_SUPER 者視為全集」入條文方向面）／款二 §III.2 加 (v)(vi)(vii) 三列 blockquote
  （檔級名單當場定數；(vii) 為 `LOGIN-CAPTCHA-WIRING` 明文凍結位 (ii) 之開立、須同時刪該列紀律欄「用途 (ii) 不在授權內」句）／
  款三 no-escalation 掛點射程分工（middleware＝路徑級上限位恆放行、handler＝body 級指派集；**補充** ADR 0022 決定 3、不 supersede）
  ＋按鈕 gating 例外釋義（ADR 0019 差異點：判準＝該頁 menu 維政策是否僅 R_SUPER；role／menu 頁不 gating 拍板不變）；
  front-matter `provenance` 含 brainstorm §3／§3b／spec Clarifications 三 session。★user 親決兩題：①I7 條文是否寫「持 R_SUPER 者 A＝全集」
  字樣（建議寫、否則實作與條文不同源）②島 I header 括號寫法（建議照島 G／H 形列進場刀與條區間）。
- [ ] T002 早期查證（容器內實跑、結論補記本 task；★全數還原零殘留）：①`AppError::BizData` 對 `error.rs` 四處窮舉 match（:75 `code()`／
  :91 `msg()`／:107／:216 remap）之補臂面——加空殼變體 `cargo build -p server` 逐一收斂編譯紅、記實際須補處數後還原；
  ②`envelope.rs`:29 `compile_fail` doctest 現形與「加 `from_err_with_data` 後仍非 vacuous」的改寫形（暫改後 `cargo test --doc` 實跑、記結論還原）；
  ③`advisory_lock_user` 自 `handler/auth/login.rs`:519 上提為 facade `pub(crate)`（DbErr 形）後，login 端 `AppError` 映射的薄殼形（暫改實編譯、記還原）；
  ④`refresh.rs`:234 附近 txn 邊界——確認在同一 `txn` 內加 `sys_user::find_by_id` 活性判的落點與失敗時走既有 8888 路徑之分支名；
  ⑤`schema-gate.py` gate2 對 `sys_user` 的比對面（seed 3 列逐列全等）與 `sys_pwd_custody` 現況（`RUNTIME_APPEND_TABLES` 外、零列）實測；
  ⑥`handler/role.rs::update_role_endpoints_super_full_candidate_save_…` 三 assert 現形與候選外 audit 域 5 列實測（B-113 續綠佐證）。
- [ ] T003 ★主線任務（user 親決後）：0063 轉 accepted＋更新 `.specify/memory/constitution.md`（v1.8.0→v1.9.0；research R10；由下而上改：
  修訂日誌一行／版本行／§I.7 島 I 六條塊〔島 H 之後〕／§III.2 表加三列／`LOGIN-CAPTCHA-WIRING` 紀律欄刪「(ii) 不在授權內」句）
  ＋`python3 tools/docs-sync.py generate`；同 commit（`docs(constitution): amend …`）。★本 task 完成前：一切 base-web 既有檔凍結。
  新列變異自證：暫改 (v) 列範圍欄一路徑為裸措辭→`fork-delta-lint` 紅→還原。
- [ ] T004 [P] 前端基線量測（結論補記本 task、供 i18n 與欄寬 task 用）：`page.manage.user` zh-cn／en-us 現有葉鍵集逐鍵列出（現 19）；
  `views/manage/user/index.vue` 現有欄集與各欄 `width|minWidth` 與 `scroll-x` 現值；`user-search.vue` 與 rev4 同檔 `diff` 是否逐位相同
  （零改動則不入 (v) 檔級名單）；`authStore.userInfo` 現有欄（`roles` 為 code 集之證據）。
- [ ] T005 [P] `docs/ops/BACKLOG.md`：B-134 觸發器與本刀關係複核（首登強制改密＝非射程、custody 只時戳）；B-020／B-098 敘述各一行標「刀 B 期間狀態」；
  ★不刪任何條目（關帳集中於 T077）。

**Checkpoint**: 憲法授權到手、未知數清空——後端 Foundational 可開；base-web 既有檔解凍。

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: 密碼政策核心、攜參信封、撤銷原語、事件值集、custody、no-escalation 純函式、觀測與稽核詞彙、facade 讀端與鎖、wire DTO、節流、測試守衛。

**⚠️ 本 phase 未完成前不得開任何 US（T006～T014 [P] 檔域不相交；T015～T021 序列或半序）。**

- [ ] T006 [P] `rust-api/server/src/model/password.rs`：新增 `hash`（argon2id、PHC；與既有 `verify` 同參數集）／`PASSWORD_POLICY_KEYS: [&str; 7]`／
  `VIOLATION_*` 八常數（字面＝Lint24 白名單 `biz.user.passwordViolation.*` 尾段）／`PasswordPolicy` 型／`load_policy`（單快照讀 `system_settings`、
  缺鍵 fail-default）／`validate_against_policy(pw, user_name, &policy) -> Vec<&'static str>`（收集全部違規、chars 計長、bytes ≤
  `throttle::LOGIN_PASSWORD_MAX_BYTES`、`forbid_username` 大小寫不敏感相等）＋表驅動單元測（八違規各一案、多違規全收集、
  chars vs bytes 分界、缺鍵 fail-default、密碼不入 Debug 輸出）；★檔頭「三支不搬」句改寫為 as-built。
- [ ] T007 [P] `rust-api/server/src/error.rs`＋`rust-api/server/src/envelope.rs`：`AppError::BizData(Cow<'static, str>, serde_json::Value)`
  （四處 match 補臂：`code()`→`2222`／`msg()`→key／:107／:216 remap；13 碼矩陣列不變）＋`Res::from_err_with_data`（`data=Some(v)`）＋
  `compile_fail` doctest 依 T002② 結論改寫（`from_err` 仍 data null；帶資料只經新出口）＋測（兩出口對照、矩陣測不變）；
  ★`error.rs`:37 之「B12 不建 BizData 攜參形」註解改寫為「射程嚴限密碼二鍵（本刀新 ADR、編號 0064）」。
- [ ] T008 [P] `rust-api/server/src/model/facade/sys_token.rs`：`revoke_all_of_user(conn, uid) -> Result<Vec<String>, DbErr>`
  （`status='active'`→`revoked`、回 distinct sid；rotated 列不動）＋測（只撤 active、rotated 不變、無 active 回空集、sid 去重）；
  ★檔頭「`revoke_all_of_user` 前提本刀未成立、不搬」句改寫為 as-built。
- [ ] T009 [P] `rust-api/server/src/model/facade/session_event.rs`：`EVENT_REVOKED` 與五 reason 常數
  （`REASON_USER_DISABLED`／`USER_DELETED`／`PASSWORD_RESET`／`PASSWORD_CHANGED`／`ADMIN_KICK`）；★收成 macro 單一宣告源
  （事件型與 reason 各一組）＋值集測（成員恰等、字面逐字）。
- [ ] T010 [P] `rust-api/server/src/model/facade/sys_pwd_custody.rs` 新檔＋`model/facade/mod.rs` 掛載（ASCII 序 `sys_operation_log` < `sys_pwd_custody` < `sys_role`）：
  `touch(txn, user_id, created_by)`（upsert `created_at=now()`、`ON CONFLICT (user_id, created_by) DO UPDATE`）／
  `last_set_at(conn, user_id, created_by) -> Option<DateTimeWithTimeZone>`＋測（首寫／覆寫更新時戳／不同 operator 各自一列／查無回 None）；
  ★模組 doc 明寫「本刀只用時戳、不做 EXISTS 經手判定（首登強制改密＝B-134）」。
- [ ] T011 [P] `rust-api/server/src/auth/no_escalation.rs` 新檔＋`auth/mod.rs` 掛載：`ActorScope::{All, Codes(HashSet<String>)}`／
  `assert_no_escalation(actor: &ActorScope, target: &[String], next: &[String]) -> Result<(), ()>`（`T ⊆ A ∧ N ⊆ A`；`All` 恆過）／
  `actor_scope_of(conn, uid) -> ActorScope`（`roles_of_user` 現役集；含 `R_SUPER` ⇒ `All`）＋表驅動測（超管全集、子集過、超集拒、
  同級過、`T=∅` 過、`N` 含未持角色拒、停用角色不入 A 之語意由 `roles_of_user` 保證）；★doc 明寫與 `enforce.rs::no_escalation_check`
  的射程分工（後者恆放行、屬路徑級上限位）。
- [ ] T012 [P] `rust-api/server/src/obs.rs`：`THROTTLE_DEGRADED_SOURCES` 12→13（新增 `redis_change_pwd`）＋`pre_register_metrics` 同步＋
  值集測改（十二→十三成員恰等）。
- [ ] T013 [P] `rust-api/server/src/model/audit.rs`：`audit_operation_vocabulary!` 加 `kick`／`reset_password`／`change_password`（小寫）＋
  釘值測 `t005_role_menu_family_adds_no_variant_vocabulary_stays_five` 改名為八值形（正向逐值、負向大寫與未知值）＋doc 補「本刀擴三值（007）」。
- [ ] T014 [P] `rust-api/server/src/cache/mod.rs`：`REASON_ADMIN_KICK: &str = "admin_kick"`（照既有兩常數形、doc 說明 7777 分鍵）＋
  改密節流桶鍵前綴常數（`cpwd:`，與登入節流鍵面分離）＋鍵形測。
- [ ] T015 `rust-api/server/src/model/facade/sys_user.rs`＋`rust-api/server/src/handler/auth/login.rs`：`advisory_lock_user` 依 T002③ 上提為
  facade `pub(crate) async fn advisory_lock_user(conn, uid) -> Result<(), DbErr>`；login.rs:519 改為薄殼呼叫（`AppError` 映射保持不變、
  既有 11 步鏈行為零變更）＋`find_active_by_id_for_update`／`find_deleted_by_id_for_update`（窄投影、`FOR UPDATE`）＋測
  （鎖形以既有 `TableLock`／`real_db_single_with_lock_timeout` seam 驗等待；login 回歸測全綠）。
- [ ] T016 `rust-api/server/src/model/facade/sys_user_role.rs`：`role_codes_all_of_user(conn, uid) -> Vec<String>`（join `sys_role`、
  ★不濾角色 status、濾已軟刪角色）／`codes_of_role_ids(conn, ids) -> Result<Vec<String>, RoleIdsError>`（界外／已軟刪 id → Err、
  空集不打 DB）／`replace_roles_of_user(txn, uid, role_ids) -> Result<bool, DbErr>`（期望全集：差集硬刪＋新增、回是否有變更）／
  `delete_all_of_user(txn, uid)`＋測（不濾 status 之證、界外 id Err、空集全撤、無變更回 false、去重）。
- [ ] T017 `rust-api/server/src/handler/common.rs`＋`handler/role.rs`＋`handler/menu.rs`：`wire_two_value_to_db` 收攏（B-127；
  與 `db_status_to_wire` 成對、doc 記三消費者）＋role.rs `wire_status_to_db`／menu.rs `wire_two_value_to_db` 刪除改 import＋
  測（三消費者同源、`'1'`→1／其餘→2 值表）；★role／menu 既有測全綠不改語意。
- [ ] T018 `rust-api/server/src/handler/user.rs` 新檔 wire DTO 段（不掛端點、編譯即可）：`UserRecord`／`UserSearchParams`／
  `AddUserReq`／`UpdateUserReq`（三態欄用 `tristate`）／`DeleteUserReq`／`BatchDeleteUserReq`／`RestoreUserReq`／`KickUserReq`／
  `ResetUserPasswordReq`／`UpdateUserSessionPolicyReq`（皆 `Default`＋`json_or_default` 信封化）＋i64 欄 `serialize_i64_number_guarded`
  ＋contracts/wire-user-admin.md 逐欄對齊測（型層級：serde round-trip、`userName` 出現即拒之欄存在性）。
- [ ] T019 `rust-api/server/src/handler/user_center.rs` 新檔 wire DTO 段：`ChangePasswordReq{oldPassword,newPassword,confirmPassword}`
  （`Default`＋`json_or_default`）／`PasswordPolicyView`（七欄）＋serde 測。
- [ ] T020 `rust-api/server/src/throttle/change_pwd.rs` 新檔＋`throttle/mod.rs` 掛載：`CHANGE_PWD_MAX_FAILS=5`／`CHANGE_PWD_WINDOW_SECS=900`
  常數＋`precheck(cache, uid) -> Result<(), Throttled>`（GET ≥5 即拒）／`record_failure`（INCR＋EXPIRE 續窗）／`clear`（DEL）；
  redis Err ⇒ fail-open＋`throttle_degraded_total{source="redis_change_pwd"}`＋測（第 6 次拒、成功清、fail-open 不拒且計數、
  桶鍵與登入節流不互擾）。
- [ ] T021 `rust-api/server/src/model/mod.rs`（`test_db`）：`UserCleanup` 補業務鍵腿（`user_name` 測試前綴）＋op-log 腿＋
  `setval('sys_user_id_seq', 3, true)`／新 `PwdCustodyCleanup`（依 user_id 集刪）／新 `SessionRevokeCleanup`（撤銷列與事件；
  或說明既有守衛已涵蓋而不建、二擇一並在型 doc 寫明理由）＋各自自證測（Drop SQL 寫壞即紅）；★模組 doc「名冊」節同步。

**Checkpoint**: Foundation ready——政策／撤銷／守門／節流／DTO／守衛就位，各 US 可開。

---

## Phase 3: User Story 1 — 超管使用者管理全套（P1）🎯 MVP

**Goal**: 七支管理端點（列表／回收桶列表／新增／編輯／單刪／批刪／復原）全真：唯一性、三態、值 diff no-op、seed 保護、self 五不、
軟刪硬刪指派、復原零回灌、角色集全量替換＋判定面同步；前端 user 頁列表與抽屜接真。

**Independent Test**: quickstart §1（curl 七支）＋§6-1（CDP Super 動線）；Admin 對六支寫端 5003。

### Tests for User Story 1 ⚠️（先紅後綠）

- [ ] T022 [P] [US1] `rust-api/server/src/model/facade/sys_user.rs` 測段：寫端五組——`insert`（唯一撞 23505 兜底、空字串→NULL、
  預設啟用、零角色）／`update`（三態、`userName` 出現即拒、值 diff no-op、roleIds 全量替換、界外 id 拒）／`soft_delete`＋
  `batch_soft_delete`（seed 保護、self、任一違規整批 rollback、指派硬刪、空陣列 no-op）／`restore`（同名活性撞、同信箱活性撞、
  零回灌、status 保留）／`list`＋`list_deleted`（排序、濾、分頁）。
- [ ] T023 [P] [US1] `rust-api/server/src/handler/user.rs` 測段（endpoint 級、`oneshot_json_from` 帶真 connect-info）：七支各正向＋
  拒因映射（`notFound`／`userNameExists`／`userEmailExists`／`userEmailInvalid`／`userNameImmutable`／`seededProtected`／
  `cannotDeleteSelf`／`cannotEditSelfRoleOrStatus`／`roleNotFound`）；稽核列同交易斷言（`operation`／payload 不含 `$argon2`）。
- [ ] T024 [P] [US1] `rust-api/server/tests/contract.rs`：七支 ContractCase（`user-get-list`／`user-get-deleted`／`user-add`／
  `user-update`／`user-delete`／`user-batch-delete`／`user-restore`；case_key 反查形、不抄 rev4 路徑字面）；`ROUTES_COUNT` 斷言同步。

### Implementation for User Story 1

- [ ] T025 [US1] `rust-api/server/src/model/facade/sys_user.rs`：寫端家族實作（`insert`／`update`／`soft_delete`／`batch_soft_delete`／
  `restore`／`list`／`list_deleted`）——鎖序照全程紀律；`update` 之 roleIds 走 T016 `replace_roles_of_user`；軟刪同交易
  `delete_all_of_user`＋`revoke_all_of_user`（事件 `user_deleted`）；`violated_constraint` 收斂 23505；
  ★錯誤型 enum 逐支（`UserCreateError`／`UserUpdateError`／…）供 handler remap。
- [ ] T026 [US1] `rust-api/server/src/handler/user.rs`：七支 handler＋`begin_and_lock_user`（begin→advisory(uid)→`FOR UPDATE` 活性列）＋
  `finish_user_write`（稽核→commit→斷權 best-effort→reload 條件）＋`map_*_err` remap；守門固定序（①notFound②seed③self
  ④`assert_no_escalation`⑤業務）；共用件零拷貝。
- [ ] T027 [US1] `rust-api/server/src/router.rs`：七條 RouteDef（`Protection::Policy`、DELETE 兩支）＋`ROUTES_COUNT` 49→56；
  `docs-sync.py generate` 併 `reference/routes`。
- [ ] T028 [US1] `rust-api/server/src/handler/user.rs`＋`rust-api/server/tests/authz_entrypoint_lint.rs`：角色集**實際變更**時
  commit 後 `reload_enforcer`（B-093 閉合、Applied 即觸發不問 diff 之口徑照 006 grant 面）＋`RELOAD_CALL_FILES` 擴
  `handler/user.rs`（恰等斷言、實得序以實跑為準）＋deleteUser 硬刪指派亦觸發（data-model §3.4）＋測（無角色變更零觸發之特性測）。
- [ ] T029 [US1] `base-web/src/typings/api/rev5-user-admin.d.ts`＋`base-web/src/service/api/rev5-user-admin.ts` 新檔（`Api.UserAdmin.*`；
  contracts/wire-user-admin.md 逐欄；直接路徑 import 不經 barrel；`system-manage.ts` 不動）＋`pnpm exec oxlint <file>` 綠。
- [ ] T030 [US1] `base-web/src/views/manage/user/index.vue`（修改型 (v)、逐行 `原行:`）：接真 `fetchGetUserList`／`fetchGetDeletedUsers`；
  刪 console.log 假實作；回收桶 `showDeleted` toggle 切兩資料源（已刪模式隱搜尋卡、operate 欄換復原、不加刪除時間欄）；
  列表欄含角色／狀態／會話政策／記事／審計欄；`scroll-x`＝Σ 欄寬（依 T004 量測）；★治理清單呼叫帶參（B-132 於本頁結構性不重現）。
- [ ] T031 [US1] `base-web/src/views/manage/user/modules/user-operate-drawer.vue`（修改型 (v)）：接真 `fetchAddUser`／`fetchUpdateUser`；
  刪 `getRoleOptions()` mock 段改打 `fetchGetAllRoles`；修 `path="email"`→`userEmail`（帶 `原行:`）；password 僅新增模式；
  `userName` 編輯模式 disabled；memo textarea；update wrapper 剝 `userName`；★角色下拉全列（不預判包含規則、G8）。
- [ ] T032 [US1] `base-web/src/locales/langs/{zh-cn,en-us}.ts`＋`base-web/src/typings/app.d.ts`：`page.manage.user` 補列表／抽屜／
  回收桶／確認框鍵（兩語鍵集相等、依 contracts/msg-keys.md 候選）＋`App.I18n.Schema.page.manage.user` 型節；`pnpm typecheck` 綠。

**Checkpoint**: US1 可獨立驗收——七支 API＋user 頁列表與抽屜；斷權由 Foundational 之 `revoke_all_of_user` 已生效（分派與文案於 US2 定案）。

---

## Phase 4: User Story 2 — 斷權即刻失效（P1）

**Goal**: 踢除／停用／刪除／重設密碼四路撤銷語意定案：同交易撤全部 active、事件五 reason、denylist best-effort、
`admin_kick`→7777 新鍵、其餘→8888、refresh 鎖內活性重驗。

**Independent Test**: quickstart §2（雙 token 斷權動線）＋§6-4（CDP 7777／8888 實機）。

### Tests for User Story 2 ⚠️

- [ ] T033 [P] [US2] `rust-api/server/src/handler/user.rs` 測段：kick 正向（`{revoked:n}`、rotated 不動、事件 `admin_kick`、稽核 `kick`）＋
  射程（self 拒、Super 可踢〔受包含規則〕、停用可踢、已刪 `notFound`）；停用／刪除路徑之撤銷斷言（事件 reason 逐值）。
- [ ] T034 [P] [US2] `rust-api/server/src/auth/enforce.rs` 測段：denylist reason 分派三向（`kicked`→7777＋既有鍵、`admin_kick`→7777＋
  `auth.session.kickedByAdmin`、`revoked`→8888）＋既有 003 測全綠（島 C 語意不變）。
- [ ] T035 [P] [US2] `rust-api/server/src/handler/auth/refresh.rs` 測段：停用使用者之 refresh 鎖內重驗被拒（8888）／已軟刪同；
  正常使用者不受影響（既有 rotation／grace／reuse 測全綠）。
- [ ] T036 [P] [US2] `rust-api/server/tests/contract.rs`：`user-kick` ContractCase；`ROUTES_COUNT` 56→57。

### Implementation for User Story 2

- [ ] T037 [US2] `rust-api/server/src/handler/user.rs`：`kick_user` handler＋`finish_user_write` 之斷權接線（交易內
  `revoke_all_of_user`＋逐 sid `session_event`；commit 後 best-effort 逐 sid `cache::denylist_set(sid, reason, ttl.refresh_secs)`、
  失敗只 warn）＋`router.rs` 一條＋`ROUTES_COUNT` 57；停用（`update` status→2）與刪除路徑共用同一接線。
- [ ] T038 [US2] `rust-api/server/src/auth/enforce.rs`：`enforce_mw` 依 denylist reason 分派碼與鍵（新增 `REASON_ADMIN_KICK` 臂）；
  ★doc 明寫三 reason 不互換（島 C）；`backend.biz`／`auth.session` 新鍵四處同步（Lint24 同步律）。
- [ ] T039 [US2] `rust-api/server/src/handler/auth/refresh.rs`：鎖內使用者活性重驗（依 T002④ 落點；不活→既有 8888 路徑）＋
  doc 記「003 島 C 新增判定腿、非方向反轉」；★`getUserInfo`／`enforce_mw` 不判 status 之 003 拍板不動。

**Checkpoint**: US2 可獨立驗收——四路斷權即時、分鍵正確、refresh 不再是漏洞。

---

## Phase 5: User Story 3 — 密碼政策與自助改密（P1）

**Goal**: 八鍵政策生效於三入口（登入不驗）、違規明細攜參下發、設密冷卻、自助改密五步序、舊密節流；個人中心改密卡與產密浮層。

**Independent Test**: quickstart §3（政策／改密／節流 curl）＋§6-5（CDP 個人中心動線）。

### Tests for User Story 3 ⚠️

- [ ] T040 [P] [US3] `rust-api/server/src/handler/user.rs` 測段：addUser／resetUserPassword 之政策違規（`BizData` 攜 `violations`）、
  冷卻（`remainingSeconds`、interval=0 停用、不同 operator 互不影響、addUser 計入）、self 拒（`cannotResetSelfPassword`）。
- [ ] T041 [P] [US3] `rust-api/server/src/handler/user_center.rs` 測段：changePassword 五步序逐步拒因＋成功後撤他 session 保留當前＋
  事件 `password_changed`＋稽核 `change_password`＋custody touch。
- [ ] T042 [P] [US3] `rust-api/server/src/throttle/change_pwd.rs` 測段（整合面）：連錯 5 次後第 6 次 `changePasswordThrottled`（在雜湊驗證前、
  零稽核）、成功改密清桶、redis 停機 fail-open＋降級計數。
- [ ] T043 [P] [US3] `rust-api/server/src/handler/auth/login.rs` 測段：★登入路徑零政策驗證之機器守（seed 帳號 6 字元密碼登入成功；
  `login.rs` 全檔零 `validate_against_policy` 引用之 grep 型斷言）。
- [ ] T044 [P] [US3] `rust-api/server/tests/contract.rs`：`user-reset-password`／`user-center-change-password`／
  `user-center-get-password-policy` 三 ContractCase；`ROUTES_COUNT` 57→60。

### Implementation for User Story 3

- [ ] T045 [US3] `rust-api/server/src/model/facade/sys_user.rs`：`reset_password`（政策→冷卻→hash→UPDATE＋custody touch＋撤全 active
  ＋事件 `password_reset`）／`change_own_password`（五步序；成功 `revoke_others_of_user(keep=sid)`＋事件 `password_changed`）；
  ★`insert` 補政策＋custody touch（G14）。
- [ ] T046 [US3] `rust-api/server/src/handler/user.rs`：`reset_user_password` handler＋`router.rs` 一條；
  ★self 拒導向個人中心（拒因鍵 `cannotResetSelfPassword`）。
- [ ] T047 [US3] `rust-api/server/src/handler/user_center.rs`：`change_password`（Authed、標的恆 `claims.uid`、節流前置）＋
  `get_password_policy`（七鍵投影）＋`router.rs` 兩條（`Protection::Authed`、零 casbin seed）＋`ROUTES_COUNT` 60。
- [ ] T048 [US3] `base-web/src/typings/api/rev5-user-center.d.ts`＋`base-web/src/service/api/rev5-user-center.ts` 新檔＋
  `base-web/src/hooks/business/pwd-policy.ts` 新檔（`buildPolicyRules`；取不到靜默降 required）＋
  `base-web/src/components/custom/pwd-gen-modal.vue` 新檔（`crypto.getRandomValues`、依政策產合規密碼）。
- [ ] T049 [US3] `base-web/src/views/user-center/modules/password-card.vue` 新檔（只舊密碼一路、無 radio、規則來自 hook、
  `:user-name` 不用 `authStore.userInfo.userName`）＋`base-web/src/views/user-center/index.vue`（修改型 (vi)：父層骨架、
  只掛改密卡、三卡位留白）。
- [ ] T050 [US3] `base-web/src/locales/langs/{zh-cn,en-us}.ts`＋`zh-tw.ts`＋`app.d.ts`：`page.userCenter.*` 新 top-level 命名空間＋
  `backend.biz.user.*` 二十一鍵＋`auth.session.kickedByAdmin`（四處同步、Lint24）＋`page.manage.user.pwdGen.*`；`pnpm typecheck` 綠。

**Checkpoint**: US3 可獨立驗收——政策三入口、明細可讀、冷卻與節流、個人中心可自助改密。

---

## Phase 6: User Story 4 — 授權下放＋no-escalation（P2）

**Goal**: 九處掛點全上、規則對所有角色一體適用（超管 A＝全集）、5003 warn 日誌；前端七碼 gating 與會話政策欄 disabled。

**Independent Test**: quickstart §4（下放後 Admin 動線）＋§6-2／§6-3（CDP 預設態與下放後對照）。

### Tests for User Story 4 ⚠️

- [ ] T051 [P] [US4] `rust-api/server/src/handler/user.rs` 測段（每支寫端 ≥2 負向＋1 正向、FR-021）：被授權 R_ADMIN 對持 R_SUPER 標的 5003／
  指派超出自身角色集 5003／Super（僅持 R_SUPER）對持其未持角色之標的成功（A＝全集非 vacuous）；測內以 `casbin_rule` 資料列 grant、
  `CasbinCleanup` 兜底；★停用角色仍計入 T 之案。
- [ ] T052 [P] [US4] `rust-api/server/src/handler/throttle.rs` 測段：unlockLogin 帳號維套規則（R_ADMIN 解鎖持 R_SUPER 帳號 5003）／
  IP 維不套（既有行為不變）。

### Implementation for User Story 4

- [ ] T053 [US4] `rust-api/server/src/handler/user.rs`：`assert_no_escalation` 掛八支寫端（守門序④；`actor_scope_of`＋
  `role_codes_all_of_user`＋`codes_of_role_ids` 取三元）＋違者 5003 純 key＋`tracing::warn!(actor, target, endpoint)`
  （★不含角色差集）。
- [ ] T054 [US4] `rust-api/server/src/handler/throttle.rs`：`unlock_login` 帳號維分支鎖內加 `assert_no_escalation`（T 取標的全部指派列）；
  IP 維不套；doc 記射程。
- [ ] T055 [US4] `base-web/src/views/manage/user/index.vue`（修改型 (v)）：七枚按鈕碼逐鈕 `hasAuth` gating（B-099 形：外層 div 保底＋
  `v-show`＋內層 `v-if`）；★自己那列操作下拉不列「重設密碼」（self 五不）。
- [ ] T056 [US4] `base-web/src/views/manage/user/modules/user-operate-drawer.vue`（修改型 (v)）：`sessionPolicy` 欄對非超管
  （`authStore.userInfo.roles` 不含 `R_SUPER`）顯示現值但 disabled＋提示鍵；★不發出必敗的第二支呼叫（G7）；
  self 之 `status`／`roleIds` 控制項 disabled。

**Checkpoint**: US4 可獨立驗收——下放可開關、規則一體適用、UI 誠實。

---

## Phase 7: User Story 5 — 解鎖登入、會話政策、記事欄（P2）

**Goal**: seed 已錨定的三項能力取得消費者：`updateUserSessionPolicy` 端點＋抽屜三值、`user:unlock` 頁首 modal（雙維）、
`user_memo` 兩面（B-003 關帳）。

**Independent Test**: quickstart §1 尾三 curl＋§6-1（CDP 解鎖 modal 與會話政策）。

### Tests for User Story 5 ⚠️

- [ ] T057 [P] [US5] `rust-api/server/src/handler/user.rs` 測段：`update_user_session_policy` 三值收斂＋值域外 2222＋與現值相同 no-op＋
  已刪 `notFound`＋改 single 不即時踢（既有 session 仍在之斷言）。
- [ ] T058 [P] [US5] `rust-api/server/tests/contract.rs`：`user-update-session-policy` ContractCase；`ROUTES_COUNT` 60→61（終值）。

### Implementation for User Story 5

- [ ] T059 [US5] `rust-api/server/src/handler/user.rs`＋`rust-api/server/src/model/facade/sys_user.rs`：`update_user_session_policy` handler＋
  `set_session_policy` facade＋`router.rs` 一條（protected 端點、super-only 結構性）＋`ROUTES_COUNT` 61。
- [ ] T060 [US5] `base-web/src/views/manage/user/modules/user-unlock-modal.vue` 新檔（雙維下拉＋條件輸入、顯式帶 `dimension`、
  打既有 `fetchUnlockLogin`）＋`index.vue` 頁首鈕接線（`user:unlock` gating）。
- [ ] T061 [US5] `base-web/src/views/manage/user/{index.vue,modules/user-operate-drawer.vue}`：`userMemo` 列表純文字欄
  （零原始 HTML 插值、`view-render-guard` 綠）＋抽屜 textarea（B-003 最後一張表）；i18n 鍵同批。

**Checkpoint**: US5 可獨立驗收——七枚按鈕碼與 seed 68 全數取得消費者。

---

## Phase 8: User Story 6 — 登入頁規則放寬與順路修復（P3）

**Goal**: B-089 結案（登入頁降 required-only）＋順路三條（B-129／B-132／B-128 ①②）。

**Independent Test**: quickstart §3 末（含特殊字元密碼登入）＋§6-5；role 頁換角色 modal 無殘影；menu 頁回收桶每頁 10。

- [ ] T062 [P] [US6] `base-web/src/views/manage/role/modules/{menu-auth-modal.vue,button-auth-modal.vue,endpoint-auth-modal.vue}`
  （(iii) 補完、免 bump）：`getChecks()` 起手清 `rawChecks`／`protectedIds`＋`getHome()` 請求世代（B-129）；★排在 US1 抽屜照抄範式之前
  （實際執行序見 Dependencies）。
- [ ] T063 [P] [US6] `base-web/src/views/manage/menu/index.vue`（(ii) 補完、帶 `原行:`）：切回收桶模式時重置 `pagination.pageSize`
  （B-132 修法①；★只動 menu 頁、不動 `hooks/common/table.ts`）。
- [ ] T064 [US6] `base-web/src/views/_builtin/login/modules/pwd-login.vue`（修改型 (vii)、逐行 `原行:`）：`formRules` 之 pwd／userName
  改 `createRequiredRule`；★不動 `src/constants/reg.ts`；register／reset-pwd stub 不動。
- [ ] T065 [P] [US6] `docs/ops/RUNBOOK.md`：前端驗證指令分工一段（.vue 走 `pnpm lint`／`.ts` 走 `pnpm exec oxlint <file>`；
  ★`eslint` 對 `src/**/*.ts` 零覆蓋、`--max-warnings=0` 之 rc=1 為假紅）＋本刀編排 script 前端驗證段照此（B-128 ①②）。

**Checkpoint**: US6 可獨立驗收——設得進的密碼登得進；三條順路缺陷關帳。

---

## Phase 9: Polish & Cross-Cutting（DoD 收攏）

- [ ] T066 `rust-api/server/tests/wire_schema.rs`＋`rust-api/server/tests/fixtures/wire-schema.json`：跨子庫兩段式重抽
  （base-web 型 commit→容器內 `python3 tools/wire-schema.py extract`→fixtures commit→外層 pin）＋`Api.UserAdmin.*`／
  `Api.UserCenter.*` 每 definition 裁判（正向≥1／反例≥1；`status` 二值、`roles` 陣列、可空欄 null 形為重點）＋
  `python3 tools/wire-schema.py check` 綠；definitions 自 75 淨增（補記實數）；★`Api.IpRule.*` 七支不補（B-098 留帳句不動）。
- [ ] T067 `rust-api/server/src/handler/role.rs`：B-113 處置——種合成候選外 protected 探針列（非 seed、`CasbinCleanup` 兜底）、
  把 `outside_protected≥1` 自 assert 訊息升為真 assert；★該測續綠非轉紅（T002⑥ 佐證）；BACKLOG 條文更正隨 T077。
- [ ] T068 全量閘：容器 serial 全量 `cargo test` rc=0（基線 829、淨增補記實數）＋`docs-sync.py lint` 0 錯誤＋`schema-gate.py check` 三閘綠
  ＋`entity-drift-gate.py check`＋`fork-delta-lint.py`（修改型僅三用途檔集；`components.d.ts`／`service/api/index.ts` `git diff` 零輸出斷言）
  ＋`route-artifact-gate.py check`（零重算）＋`view-render-guard.py check`＋`seed-view-gate.py check`＋`rust-fmt-gate.py check`
  ＋`pnpm typecheck` 綠＋三名冊閘綠（`RELOAD_CALL_FILES` 實得序）。
- [ ] T069 CDP 三方對照（quickstart §6 全動線八步；★排 schema-gate 之後）：Super 全套／Admin 預設態（只見編輯鈕）／下放後（六鈕出現、
  同級成功、對 Super 5003）／踢除 7777 新文案／停用 8888／個人中心改密卡動態規則／登入頁特殊字元密碼直送／rev4 42080 逐項對照；
  已知態排除清單逐項驗現狀形；走查後清殘列＋`sys_user_id_seq` 還原＋三閘複驗；差異逐項判定（rev5 拍板差異 or 缺陷）補記本 task。
- [ ] T070 ★主線任務：ADR ②～⑤ draft→accepted——`0064`（BizData 明細通道：射程二鍵、澄清 ADR 0022 §2② 之誤、結 B-024③ 受眾邊界）／
  `0065`（`SELF_SERVICE_ROUTES` 碼內白名單，承 rev4:ADR 0065、紀律嚴限自助頁家族）／`0066`（設密冷卻＋改密節流：custody 只時戳、
  fail-open 同島 E、常數門檻、觀測 source）／`0067`（ADR 0042 第 2 項措辭訂正＝解鎖入口為使用者管理頁，走 v1.6.1 對 0043 範式；
  ＋ADR 0053 觸發矩陣補一列＝user 指派寫端）；各 `provenance` 指向 brainstorm／spec 條號；`docs-sync.py generate`。
- [ ] T071 ★主線任務：活書 `docs/arc42/ARCHITECTURE.md` §5（facade 新兩檔與寫端家族、test_db 名冊三守衛——落筆先算餘裕 20 行）＋
  §6（斷權四路與 reason 分派、密碼三入口與冷卻節流序——餘裕 40）＋§8（授權慣例加 no-escalation 包含規則與掛點分工、
  按鈕 gating 判準——餘裕 77）＋§12 詞彙六條（停用／軟刪／踢除／撤銷／鎖定／重設 vs 修改密碼）＋
  `docs/arc42/FORK-DELTA-WIRING.md`（(v)(vi)(vii) 三用途接線 as-built）；撞頂即依 ADR 0062 輕量軌下放（不再逐次 ADR）。
- [ ] T072 ★主線任務：`docs/ops/BACKLOG.md` 關帳與勘誤——刪 B-003／B-021／B-024／B-089／B-093／B-113／B-127／B-129／B-128／B-132
  （B-020 視通用 seam 是否做、B-025 只結①留②、B-098 續留）＋`docs/ops/LESSONS.md`（若有踩坑）＋勘誤四處：
  `docs/ops/NOTES.md`「seed 68（manage_user view）」→「seed 68（updateUserSessionPolicy 端點）」、
  `handler/common.rs` 檔頭與 NOTES「六件」→七件、B-113 條文「由綠轉紅」→續綠、ADR 0022 §2② 由編號 0064 之新 ADR 一句澄清；
  ★`docs-sync.py errata <關鍵詞>` 逐處處置（禁只修被點名處）。
- [ ] T073 `docs/ops/RUNBOOK.md` §12.1 量測法實測 pre-commit 一筆（低於 ADR 0044 之 45s 警戒；hook 自報值與逐支中位數法不可混用）＋
  結論補記本 task；收刀簿記（events `feature_close`＋NOTES＋generate）由收刀程序承接、不列 push／merge。

---

## Dependencies & Execution Order

- **Phase 序**：Setup（T001～T005）→ Foundational（T006～T021）→ US1（T022～T032）→ US2（T033～T039）→ US3（T040～T050）→
  US4（T051～T056）→ US5（T057～T061）→ US6（T062～T065）→ Polish（T066～T073）。
- **硬閘**：T003 accepted 前凍結一切 base-web 既有檔（T030／T031／T032／T049 之 `user-center/index.vue`／T054／T055／T056／
  T061／T063／T064；backend 樹增鍵與純新增檔不受此閘）。
- **US 依賴**：US2 之 T037 依賴 US1 之 T026（`finish_user_write` 骨架）；US3 之 T045 依賴 T025（facade 寫端）與 T006／T010；
  US4 之 T053 依賴 T011（純函式）與 T026（掛點位）；US5 之 T059 依賴 T025；US6 之 T062 **建議排在 T031 之前**（先修再照抄範式、
  Q36）——實際執行序＝T062 提前至 US1 前端單元之首。
- **ROUTES_COUNT 遞增鏈**：49→56（T027）→57（T037）→60（T047）→61（T059）；每段同 commit bump＋contract case＋generate routes。
- **執行單元映射**（編排每單元一支 workflow；research R12 定稿）：U0＝T001～T005（主線、user 親決）｜U1＝T006～T021（後端底座）｜
  U2＝T022～T028（US1 後端）｜U3＝T033～T039（US2）｜U4＝T040～T047（US3 後端）｜U5＝T051～T054＋T057～T059（US4／US5 後端）｜
  U6＝T062＋T029～T032（US1 前端、B-129 先修）｜U7＝T048～T050＋T055／T056／T060／T061（US3／US4／US5 前端）｜
  U8＝T063～T065（US6）｜U9＝T066～T069（重抽與全量閘與 CDP）｜U10＝T070～T073（治理收尾）。
- **共享檔序列鏈（同檔不 [P]）**：`facade/sys_user.rs`（T015→T022→T025→T045→T059）、`facade/sys_user_role.rs`（T016→T025）、
  `handler/user.rs`（T018→T023→T026→T028→T033→T037→T040→T046→T051→T053→T057→T059）、
  `router.rs`＋`tests/contract.rs`（T024→T027→T036→T037→T044→T047→T058→T059 遞增鏈）、
  `auth/enforce.rs`（T034→T038）、`error.rs`／`envelope.rs`（T007→T040）、`views/manage/user/index.vue`（T030→T054→T060→T061）、
  `modules/user-operate-drawer.vue`（T031→T056→T061）、locales 三檔＋`app.d.ts`（T032→T050→T061）。

## Parallel Example: Foundational

T006／T007／T008／T009／T010／T011／T012／T013／T014 九路可並行分派（檔域不相交）；T015～T021 半序（T015 與 T016 可並行、
T017 獨立、T018／T019 待型定案、T020 獨立、T021 最後）。US 內之 Tests 段各 [P] 任務同理可並行分派、cargo 執行仍序列。

## Implementation Strategy

- **MVP＝US1**（七支管理端點＋user 頁列表與抽屜）——第一個可 API 與 UI 同時驗收的穩定點；US2 緊接（斷權語意定案）。
- 逐 US 增量：每 US 收尾＝contract case 綠＋單元邊界 commit（兩段式＋generate）＋六步序（復核 agent 回報→自驗三閘→落帳→
  子庫 commit→`git add` 子庫＋generate→外層 commit）；次輪 review prompt 附前輪已駁回 findings（防呆六件套⑤）。
- 編排慣例：每執行單元一支 workflow（防呆六件套＋看門狗原子成對、CLAUDE.md §2）；U0 與 T070～T073 主線親做、user 親決兩題（T001）。

## Notes

- 本檔零 push／merge 任務；finishing 由收刀程序承接。
- 零 migration、零 seed 變更；任何單元冒出 DDL／seed 需求＝停手升級 user。
- 測試基準 829＝容器內實跑值；淨增數於 T068 補記。
- 前端零測試框架：US 前端 task 之驗收＝`pnpm typecheck`＋`pnpm exec oxlint <file>`＋fork-delta-lint＋view-render-guard＋CDP（T069）。
