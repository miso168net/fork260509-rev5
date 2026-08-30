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
- ★**fork-delta 紀律**：修改型標記僅允許出現於「三用途 (v)(vi)(vii) 檔集 ∪ 順路補完檔集」（後者＝B-129 三顆
  auth-modal 之 (iii)、B-132 之 `menu/index.vue` 之 (ii)；合計既有檔 8 支；逐行 `原行:`；模板側多行註解形）；新檔檔頭
  `[rev5-inline BASE-WEB-MANAGE-PAGE-WIRING(v)+ 007-user-password-admin]`（user 頁新檔）／`…(vi)+ …`（user-center 新檔）；
  產物四檔零重算（不新增 view 目錄）；`components.d.ts`／`service/api/index.ts` 預期零 diff。
- ★**補守門必做變異測試**（專案既有紀律）：主線在邊界補任何守門（no-escalation 掛點、seed 保護、self 五不、政策／
  冷卻／節流判定、名冊閘擴列）後，MUST 把被守的那行改壞→實跑該測確認會紅→還原；紅證逐字補記該 task。
  不做這步＝補的是裝飾性守門（ADR 0024 非 vacuous 精神）。
- ★**密碼三重不洩**：密碼明文與雜湊 MUST NOT 出現於回應、稽核 payload、日誌（含 tracing）；測試以負向斷言（payload 不含 `$argon2`）釘死。

---

## Phase 1: Setup（★主線閘：憲法 Amendment＋ADR 首支＋早期查證）

**Purpose**: 取得 base-web inline 憲法授權（§III.2 (v)(vi)(vii)）、島 I 六條入憲、立首支 ADR、清除實作前未知數。

- [X] T001 ★主線任務（user 親決）：撰寫島 I 入憲 Amendment ADR draft（編號 0063、三款一檔、形照 ADR 0053 七段）於
  `docs/arc42/decisions/0063-constitution-amendment-island-i-and-manage-page-use-v-vi-vii.md`：款一 §I.7 第九座行為島（島 I 六條 blockquote＝
  data-model §4 骨架；★I7 為 rev5 專屬新條、`A` 之「持 R_SUPER 者視為全集」入條文方向面）／款二 §III.2 加 (v)(vi)(vii) 三列 blockquote
  （檔級名單當場定數；(vii) 為 `LOGIN-CAPTCHA-WIRING` 明文凍結位 (ii) 之開立、須同時刪該列紀律欄「用途 (ii) 不在授權內」句）／
  款三 no-escalation 掛點射程分工（middleware＝路徑級上限位恆放行、handler＝body 級指派集；**補充** ADR 0022 決定 3、不 supersede）
  ＋按鈕 gating 例外釋義（ADR 0019 差異點：判準＝該頁 menu 維政策是否僅 R_SUPER；role／menu 頁不 gating 拍板不變）；
  front-matter `provenance` 含 brainstorm §3／§3b／spec Clarifications 三 session。★user 親決兩題：①I7 條文是否寫「持 R_SUPER 者 A＝全集」
  字樣（建議寫、否則實作與條文不同源）②島 I header 括號寫法（建議照島 G／H 形列進場刀與條區間）。
  ★**結論（2026-08-27 落檔）**：`docs/arc42/decisions/0063-constitution-amendment-island-i-and-manage-page-use-v-vi-vii.md`
  （accepted、三款七段）。★user 親決兩題皆取建議案：①I7 條文**逐字具名 `R_SUPER`**（先例＝同節 G6 條文已寫「非 R_SUPER 角色」）
  ②島 I header 取**完整形、含 I6 位刻意空缺說明**（rev4 之首登強制換密留 B-134）。★**落字工程自決**（附機器實證、回報備查）：
  憲法表內用途索引是 **per-軌道**的 ⇒ 本刀 spec 稱之 (v)(vi)(vii) 者，落字為 `MANAGE-PAGE-WIRING(v)`／`(vi)`＋
  `LOGIN-CAPTCHA-WIRING(ii)`；`fork-delta-lint` 驗（軌道×用途×檔案）三元組（tools/fork-delta-lint.py:209-210）、
  用途後綴寫錯即紅，且 `pwd-login.vue` 既有標記本就是 `BASE-WEB-LOGIN-CAPTCHA-WIRING(i)`。★前置查證入 ADR 背景段：
  `manage_user` menu 維政策＝{R_SUPER, R_ADMIN}／`manage_role`／`manage_menu`／`user-center` 皆僅 R_SUPER（款三 gating 判準底座）；
  七枚 `user:*` 按鈕碼 seed 全在（`user:edit` 已勾 R_ADMIN）；`getAllEndpoints` 實測 35。
- [X] T002 早期查證（容器內實跑、結論補記本 task；★全數還原零殘留）：①`AppError::BizData` 對 `error.rs` 四處窮舉 match（:75 `code()`／
  :91 `msg()`／:107／:216 remap）之補臂面——加空殼變體 `cargo build -p server` 逐一收斂編譯紅、記實際須補處數後還原；
  ②`envelope.rs`:29 `compile_fail` doctest 現形與「加 `from_err_with_data` 後仍非 vacuous」的改寫形（暫改後 `cargo test --doc` 實跑、記結論還原）；
  ③`advisory_lock_user` 自 `handler/auth/login.rs`:519 上提為 facade `pub(crate)`（DbErr 形）後，login 端 `AppError` 映射的薄殼形（暫改實編譯、記還原）；
  ④`refresh.rs`:234 附近 txn 邊界——確認在同一 `txn` 內加 `sys_user::find_by_id` 活性判的落點與失敗時走既有 8888 路徑之分支名；
  ⑤`schema-gate.py` gate2 對 `sys_user` 的比對面（seed 3 列逐列全等）與 `sys_pwd_custody` 現況（`RUNTIME_APPEND_TABLES` 外、零列）實測；
  ⑥`handler/role.rs::update_role_endpoints_super_full_candidate_save_…` 三 assert 現形與候選外 audit 域 5 列實測（B-113 續綠佐證）；
  ⑦★定案 `SessionRevokeCleanup` 建或不建——實測既有 `ChainRowsCleanup`（依 sid）與 `SessionEventCleanup` 能否涵蓋
  「一次撤多 sid」的殘列面（撤銷測會一次產生 N 個 sid）；涵蓋＝不建、於 T021 型 doc 寫明理由，不涵蓋＝建。
  ★**七項結論（2026-08-27 容器內實跑、全數還原、`git -C rust-api status` 零殘留）**：
  ①**補臂面＝3 處、非 4**——加空殼變體後 `cargo build -p server` 收斂 2 處（`error.rs`:75 `code()`／:91 `key()`〔R11 記作 `msg()`〕），
  `cargo test --workspace --no-run` 再收斂 1 處（:216 `issuable_witness`，`#[cfg(test)]`）。★`http()` 有 `_` 萬用臂 ⇒ **不需補臂**
  （BizData 走 200，正確）；research R11 #9 記的「四處」把 `http()` 也算進去了。
  ②**doctest 現形＝2 支 compile_fail 全綠**（`request_context.rs`:77／`envelope.rs`:29）。`envelope.rs`:29 測的是**欄位私有性**、
  加 `from_err_with_data` 不影響 ⇒ **測本體維持原樣仍非 vacuous、不改**。★「`from_err` 仍 data null」**不能**寫成 doctest：
  `from_err` 為 `pub(crate)`、doctest 以外部 crate 編譯 ⇒ 實測 `E0624 associated function is private`。該斷言落點＝既有
  `#[cfg(test)]` 模組（`envelope.rs`:185 已有一支），T007 新增 `from_err_with_data` 時在同模組加對照測。★T007 要改的是
  doctest **上方散文**：「合法出口僅兩條」→三條、「錯誤時必為 null」→加唯二例外句。
  ③**上提可行、編譯綠**。facade 形＝`pub(crate) async fn advisory_lock_user<C: ConnectionTrait>(conn: &C, uid: i64)
  -> Result<(), DbErr>`（`sea_orm::Statement::from_sql_and_values` 直下 raw SQL、`.await?`）；login 端薄殼形＝
  `sys_user::advisory_lock_user(&txn, uid).await.map_err(internal("login advisory lock"))?;`——`internal` 的 step 字面沿用 ⇒
  tracing 訊號與 `AppError` 映射零變更、既有 11 步鏈行為不動。
  ④**txn 邊界＝`state.db.begin()`:159 →`txn.commit()`:285**；`find_by_hash_for_update(&txn,…)`:160 起持鎖、
  `roles_of_user(&txn, claims.uid)`:234 已在鎖內 ⇒ **活性重驗落點＝:234 之前**（取得 `row` 且過 active 分支之後、簽發前）。
  失敗分支＝直接 `return Err(AppError::Logout)`，與 :165「查無列」同一出口；模組 doc 既有碼面鐵律「本端點一切拒絕只有
  8888 一個出口」⇒ 新判定腿天然對齊、**零新碼零新鍵**。
  ⑤**三閘全綠**；`RUNTIME_APPEND_TABLES` 收窄集恰 4 表（`session_event`／`sys_login_attempt`／`sys_token`／`sys_operation_log`）。
  `sys_user`／`sys_user_role`／`sys_pwd_custody` **皆在集外** ⇒ gate2 seed 逐列全等（含 id 欄、未排序 diff）；`sys_user_id_seq`
  在 gate2 setval 名冊內（`seed.sql`:481 `setval(...,3,true)`）⇒ addUser 走 nextval 之測**必**還原 setval(3,true)。
  `sys_pwd_custody` 實測**零列**、欄集＝(user_id, created_at, created_by)。★**定案：`sys_pwd_custody` 不入收窄集**——
  它不是 append-only 運行期表、列由業務寫端產生且應被測試清乾淨；入集會讓真實漂移失去守門。走 `PwdCustodyCleanup`。
  ⑥★**關鍵發現：`outside_protected` 現值恰 1，唯一成員＝`/systemManage/updateUserSessionPolicy POST`**（實測：R_SUPER 現役
  端點列 50、候選集 35、候選外 15＝本刀 10 支 user 端點＋audit 5 支〔getAccessLog／getLoginAttempt／getOperationLog／
  getSessionEvent／purgeAuditLog，皆 protected=false〕）。`outside_protected` 目前只出現在 `role.rs`:2666 的 **assert 訊息**、
  非真 assert。★**因果**：本刀 T060 註冊 `updateUserSessionPolicy` 後它進候選集 ⇒ `outside_protected` **降為 0** ⇒
  **T068 的「種合成候選外 protected 探針列」不是加強、是必要條件**，否則升真 assert 會在 T060 之後轉紅（前提消失）。
  ⑦★**定案：建 `SessionRevokeCleanup`**。理由＝既有 `ChainRowsCleanup`（`DELETE sys_token WHERE rotation_chain=$1`）與
  `SessionEventCleanup`（`DELETE session_event WHERE sid=$1`）**鍵皆為單一 sid**，而撤銷測一次產生 N 個 sid、N 於「起手掛
  守衛」時點未知 ⇒ 結構性涵蓋不到。新守衛鍵＝**uid**（測試以顯式大 id 造列、起手即知），兩腿（★序不可反：先 event 後 token，
  否則第二腿刪完就查不到 sid——本形直接以 uid 為鍵故無此依賴，但腿序仍照 event→token 與既有守衛一致）：
  `DELETE FROM session_event WHERE user_id = $1`／`DELETE FROM sys_token WHERE created_by = $1`
  （★`sys_token` **無** `user_id` 欄、擁有者 uid 落在 `created_by`——`facade/sys_token.rs`:42 逐字「`owner_uid`→`created_by`」）。
- [X] T003 ★主線任務（user 親決後）：0063 轉 accepted＋更新 `.specify/memory/constitution.md`（v1.8.0→v1.9.0；research R10；由下而上改：
  修訂日誌一行／版本行／§I.7 島 I 六條塊〔島 H 之後〕／§III.2 表加三列／`LOGIN-CAPTCHA-WIRING` 紀律欄刪「(ii) 不在授權內」句）
  ＋`python3 tools/docs-sync.py generate`；同 commit（`docs(constitution): amend …`）。★本 task 完成前：一切 base-web 既有檔凍結。
  新列變異自證：暫改 (v) 列範圍欄一路徑為裸措辭→`fork-delta-lint` 紅→還原。
  ★**結論**：憲法 v1.9.0 落地（commit 971f370）——版本行／修訂日誌／§I.7 島 I 六條（島 H 之後）／§III.2 表列 12→15／
  LOGIN-CAPTCHA (i) 列刪「用途 (ii) 不在授權內」句，由下而上改、逐處落點先斷言再改。lint 0 錯誤、generate 重算 11 檔。
  ★**新列變異自證：實測與預期不同、已改判**——把 (v) 列範圍欄首路徑改裸措辭 → `fork-delta-lint` **rc=0（綠）**，因
  `user/index.vue` 尚無任何 `(v)` 標記、三元組第 3 維無從觸發 ⇒ **該列此刻結構性 vacuous**。反證守門本身有效：對已有標記的
  (ii) 列做同樣變異 → **rc=1、5 筆 findings**。⇒ 三個新列（(v)／(vi)／LOGIN-CAPTCHA(ii)）的真變異自證**延後至第一個往該列
  落標記的實作單元**：(v)→U6 之 T030、(vi)→U7 之 T050、LOGIN-CAPTCHA(ii)→U8 之 T065，紅證逐字補記各該 task。教訓＝L-063。
  ★還原照 L-060（存原文→寫回＋md5 對照，不用 `git checkout`——同檔另有未 commit 的 Amendment 改動）。
- [X] T004 [P] 前端基線量測（結論補記本 task、供 i18n 與欄寬 task 用）：`page.manage.user` zh-cn／en-us 現有葉鍵集逐鍵列出（現 19）；
  `views/manage/user/index.vue` 現有欄集與各欄 `width|minWidth` 與 `scroll-x` 現值；`user-search.vue` 與 rev4 同檔 `diff` 是否逐位相同
  （零改動則不入 (v) 檔級名單）；`authStore.userInfo` 現有欄（`roles` 為 code 集之證據）。
  ★**量測結論（2026-08-27）**：①`page.manage.user` 兩語各 **19 葉鍵**（`title`／`userName`／`userGender`／`nickName`／
  `userPhone`／`userEmail`／`userStatus`／`userRole` 8＋`form.{同上 7 鍵}` 7＋`addUser`／`editUser` 2＋`gender.{male,female}` 2）
  ——與 research R11 #2 一致；`page.userCenter` **尚不存在**（(vi) 要開的正是新 top-level 命名空間）。
  ②`views/manage/user/index.vue` 現 **9 欄**：selection 48／index 64／userName minWidth 100／userGender 100／nickName minWidth 100／
  userPhone 120／userEmail minWidth 200／status 100／operate 130 ⇒ **Σ＝962＝現 `scroll-x="962"`**（rev5 側不變式現況成立；
  rev4 的 962 才是未隨欄寬改的瑕疵）。本刀新增 roles／sessionPolicy／userMemo／四審計欄後 `scroll-x` 同批改為新 Σ。
  ③`user-search.vue` 對 **rev4 同檔**與**最原始源 `example` 基線**兩向 `diff` 皆逐位相同 ⇒ 零改動、**不入 (v) 檔級名單**（已入憲法該列紀律欄）。
  ④`authStore.userInfo` 四欄＝`userId`／`userName`／`roles`／`buttons`（`handler/auth/user_info.rs`:30-40）；`roles` 為
  **DB-fresh 角色 code 集**（`sys_user_role::roles_of_user`）⇒ T057 之「非超管＝`roles` 不含 `R_SUPER`」可行。
  ★**連帶警示（供 T050）**：`userInfo.userName` 實際是 `nick_name.unwrap_or(user_name)`＝**顯示名、非登入帳號名** ⇒
  改密卡的 `:user-name`（供 `forbid_username` 前端提示用）**不可**取自它，否則暱稱與帳號名不同的使用者會拿到錯的規則提示。
  ⑤另補測（供 T027／T069／SC-001）：dev 庫 `p` 政策列 distinct path×method＝**50**、`getAllEndpoints`＝**35**，差 15＝本刀
  10 支預埋＋audit 5 支未實作 ⇒ 兩數落差是**預埋量、非漂移**；本刀後 `getAllEndpoints` 應為 45（+10 支 Policy；user-center
  兩支走 Authed 不入）。
- [X] T005 [P] `docs/ops/BACKLOG.md`：B-134 觸發器與本刀關係複核（首登強制改密＝非射程、custody 只時戳）；B-020／B-098 敘述各一行標「刀 B 期間狀態」；
  ★不刪任何條目（關帳集中於 T073）。

**Checkpoint**: 憲法授權到手、未知數清空——後端 Foundational 可開；base-web 既有檔解凍。

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: 密碼政策核心、攜參信封、撤銷原語、事件值集、custody、no-escalation 純函式、觀測與稽核詞彙、facade 讀端與鎖、wire DTO、節流、測試守衛。

**⚠️ 本 phase 未完成前不得開任何 US（T006～T014 [P] 檔域不相交；T015～T021 序列或半序）。**

  ★**結論（零刪除、35 條不變）**：B-134 標「射程關係確認不變＋憲法 I6 位已為其保留」；B-020 標「刀 B 期間狀態」——第二消費者
  自本刀起存在但採**專用桶**、**刻意不通用化** `throttle::precheck`（判定維度／軟區語意／觀測 source 皆不同），是否通用化之
  定案排 T073；B-098 標「本刀補 `Api.UserAdmin.*`／`Api.UserCenter.*` 裁判、`Api.IpRule.*` 七支續留帳不關帳」。
- [X] T006 [P] `rust-api/server/src/model/password.rs`：新增 `hash`（argon2id、PHC；與既有 `verify` 同參數集）／`PASSWORD_POLICY_KEYS: [&str; 7]`／
  `VIOLATION_*` 八常數（字面＝Lint24 白名單 `biz.user.passwordViolation.*` 尾段）／`PasswordPolicy` 型／`load_policy`（單快照讀 `system_settings`、
  缺鍵 fail-default）／`validate_against_policy(pw, user_name, &policy) -> Vec<&'static str>`（收集全部違規、chars 計長、bytes ≤
  `throttle::LOGIN_PASSWORD_MAX_BYTES`、`forbid_username` 大小寫不敏感相等）＋表驅動單元測（八違規各一案、多違規全收集、
  chars vs bytes 分界、缺鍵 fail-default、密碼不入 Debug 輸出）；★檔頭「三支不搬」句改寫為 as-built。
- [X] T007 [P] `rust-api/server/src/error.rs`＋`rust-api/server/src/envelope.rs`：`AppError::BizData(Cow<'static, str>, serde_json::Value)`
  （四處 match 補臂：`code()`→`2222`／`msg()`→key／:107／:216 remap；13 碼矩陣列不變）＋`Res::from_err_with_data`（`data=Some(v)`）＋
  `compile_fail` doctest 依 T002② 結論改寫（`from_err` 仍 data null；帶資料只經新出口）＋測（兩出口對照、矩陣測不變）；
  ★`error.rs`:37 之「B12 不建 BizData 攜參形」註解改寫為「射程嚴限密碼二鍵（本刀新 ADR、編號 0064）」。
- [X] T008 [P] `rust-api/server/src/model/facade/sys_token.rs`：`revoke_all_of_user(conn, uid) -> Result<Vec<String>, DbErr>`
  （`status='active'`→`revoked`、回 distinct sid；rotated 列不動）＋測（只撤 active、rotated 不變、無 active 回空集、sid 去重）；
  ★檔頭「`revoke_all_of_user` 前提本刀未成立、不搬」句改寫為 as-built。
- [X] T009 [P] `rust-api/server/src/model/facade/session_event.rs`：`EVENT_REVOKED` 與五 reason 常數
  （`REASON_USER_DISABLED`／`USER_DELETED`／`PASSWORD_RESET`／`PASSWORD_CHANGED`／`ADMIN_KICK`）；★收成 macro 單一宣告源
  （事件型與 reason 各一組）＋值集測（成員恰等、字面逐字）。
- [X] T010 [P] `rust-api/server/src/model/facade/sys_pwd_custody.rs` 新檔＋`model/facade/mod.rs` 掛載（ASCII 序 `sys_operation_log` < `sys_pwd_custody` < `sys_role`）：
  `touch(txn, user_id, created_by)`（upsert `created_at=now()`、`ON CONFLICT (user_id, created_by) DO UPDATE`）／
  `last_set_at(conn, user_id, created_by) -> Option<DateTimeWithTimeZone>`＋測（首寫／覆寫更新時戳／不同 operator 各自一列／查無回 None）；
  ★模組 doc 明寫「本刀只用時戳、不做 EXISTS 經手判定（首登強制改密＝B-134）」。
- [X] T011 [P] `rust-api/server/src/auth/no_escalation.rs` 新檔＋`auth/mod.rs` 掛載：`ActorScope::{All, Codes(HashSet<String>)}`／
  `assert_no_escalation(actor: &ActorScope, target: &[String], next: &[String]) -> Result<(), ()>`（`T ⊆ A ∧ N ⊆ A`；`All` 恆過）／
  `actor_scope_of(conn, uid) -> ActorScope`（`roles_of_user` 現役集；含 `R_SUPER` ⇒ `All`）＋表驅動測（超管全集、子集過、超集拒、
  同級過、`T=∅` 過、`N` 含未持角色拒、停用角色不入 A 之語意由 `roles_of_user` 保證）；★doc 明寫與 `enforce.rs::no_escalation_check`
  的射程分工（後者恆放行、屬路徑級上限位）。
- [X] T012 [P] `rust-api/server/src/obs.rs`：`THROTTLE_DEGRADED_SOURCES` 12→13（新增 `redis_change_pwd`）＋`pre_register_metrics` 同步＋
  值集測改（十二→十三成員恰等）。
- [X] T013 [P] `rust-api/server/src/model/audit.rs`：`audit_operation_vocabulary!` 加 `kick`／`reset_password`／`change_password`（小寫）＋
  釘值測 `t005_role_menu_family_adds_no_variant_vocabulary_stays_five` 改名為八值形（正向逐值、負向大寫與未知值）＋doc 補「本刀擴三值（007）」。
- [X] T014 [P] `rust-api/server/src/cache/mod.rs`：`REASON_ADMIN_KICK: &str = "admin_kick"`（照既有兩常數形、doc 說明 7777 分鍵）＋
  改密節流桶鍵前綴常數（`cpwd:`，與登入節流鍵面分離）＋鍵形測。
- [X] T015 `rust-api/server/src/model/facade/sys_user.rs`＋`rust-api/server/src/handler/auth/login.rs`：`advisory_lock_user` 依 T002③ 上提為
  facade `pub(crate) async fn advisory_lock_user(conn, uid) -> Result<(), DbErr>`；login.rs:519 改為薄殼呼叫（`AppError` 映射保持不變、
  既有 11 步鏈行為零變更）＋`find_active_by_id_for_update`／`find_deleted_by_id_for_update`（窄投影、`FOR UPDATE`）＋測
  （鎖形以既有 `TableLock`／`real_db_single_with_lock_timeout` seam 驗等待；login 回歸測全綠）。
- [X] T016 `rust-api/server/src/model/facade/sys_user_role.rs`：`role_codes_all_of_user(conn, uid) -> Vec<String>`（join `sys_role`、
  ★不濾角色 status、濾已軟刪角色）／`codes_of_role_ids(conn, ids) -> Result<Vec<String>, RoleIdsError>`（界外／已軟刪 id → Err、
  空集不打 DB）／`replace_roles_of_user(txn, uid, role_ids) -> Result<bool, DbErr>`（期望全集：差集硬刪＋新增、回是否有變更）／
  `delete_all_of_user(txn, uid)`＋測（不濾 status 之證、界外 id Err、空集全撤、無變更回 false、去重）。
- [X] T017 `rust-api/server/src/handler/common.rs`＋`handler/role.rs`＋`handler/menu.rs`：`wire_two_value_to_db` 收攏（B-127；
  與 `db_status_to_wire` 成對、doc 記三消費者）＋role.rs `wire_status_to_db`／menu.rs `wire_two_value_to_db` 刪除改 import＋
  測（三消費者同源、`'1'`→1／其餘→2 值表）；★role／menu 既有測全綠不改語意。
- [X] T018 `rust-api/server/src/handler/user.rs` 新檔 wire DTO 段（不掛端點、編譯即可）：`UserRecord`／`UserSearchParams`／
  `AddUserReq`／`UpdateUserReq`（三態欄用 `tristate`）／`DeleteUserReq`／`BatchDeleteUserReq`／`RestoreUserReq`／`KickUserReq`／
  `ResetUserPasswordReq`／`UpdateUserSessionPolicyReq`（皆 `Default`＋`json_or_default` 信封化）＋i64 欄 `serialize_i64_number_guarded`
  ＋contracts/wire-user-admin.md 逐欄對齊測（型層級：serde round-trip、`userName` 出現即拒之欄存在性）。
- [X] T019 `rust-api/server/src/handler/user_center.rs` 新檔 wire DTO 段：`ChangePasswordReq{oldPassword,newPassword,confirmPassword}`
  （`Default`＋`json_or_default`）／`PasswordPolicyView`（七欄）＋serde 測。
- [X] T020 `rust-api/server/src/throttle/change_pwd.rs` 新檔＋`throttle/mod.rs` 掛載：`CHANGE_PWD_MAX_FAILS=5`／`CHANGE_PWD_WINDOW_SECS=900`
  常數＋`precheck(cache, uid) -> Result<(), Throttled>`（GET ≥5 即拒）／`record_failure`（INCR＋EXPIRE 續窗）／`clear`（DEL）；
  redis Err ⇒ fail-open＋`throttle_degraded_total{source="redis_change_pwd"}`＋測（第 6 次拒、成功清、fail-open 不拒且計數、
  桶鍵與登入節流不互擾）。
- [X] T021 `rust-api/server/src/model/mod.rs`（`test_db`）：`UserCleanup` 補業務鍵腿（`user_name` 測試前綴）＋op-log 腿＋
  `setval('sys_user_id_seq', 3, true)`／新 `PwdCustodyCleanup`（依 user_id 集刪）／`SessionRevokeCleanup`（依 T002⑦ 之定案結論建或不建；不建則於 `test_db` 模組 doc「名冊」節寫明既有兩守衛
  如何涵蓋一次撤多 sid 的殘列面）＋各自自證測（Drop SQL 寫壞即紅）；★模組 doc「名冊」節同步。

★**U1 執行結果（workflow `wf_5796527c-7c6`、12 agents、2026-08-28 收尾）**

- **量**：rust 測試 829→**878**（淨增 49；U1 workflow 交付至 876，主線於邊界補 2 支守門測）。容器內 serial rc=0；
  `cargo fmt --all` 已跑；八閘全綠（schema-gate 三閘／entity-drift／rust-fmt／fork-delta／route-artifact／
  view-render／seed-view）＋`docs-sync lint` 0 錯誤。零 migration、零 seed 變更、base-web 零改動。
- **審查**：規格符合性輪**第 1 輪即收斂**（0 blocker）；碼品質輪跑滿 3 輪 fix＋確認輪，確認輪餘 3 筆
  （審查員自陳「無阻斷級、皆守門非 vacuous 與 as-built 敘述同步層級」）。★主線逐項自 grep 復核，**三筆全數成立**、已於邊界修完。
- **主線於單元邊界補的兩支守門＋變異紅證**（紀律：補守門必做變異測試）：
  ①`auth/no_escalation.rs::actor_scope_of_takes_the_active_role_face_not_the_membership_face`——釘 A 側取
  `roles_of_user`（現役口徑）這條**接線**。變異：改呼 `role_codes_all_of_user`＋補錯誤映射（＝真實的「順手對齊」形；
  裸改因回型 `DbErr` vs `AppError` 不同而先撞 E0277，故做忠實變異）→ 該測 FAILED，
  `no_escalation.rs:319 assertion left == right failed: ★A 須恰等於**啟用**角色碼那一顆…
  left: Codes({"test-t011a-…", "test-t011b-…"}) right: Codes({"test-t011a-…"})`。還原後 md5 逐位對照。
  ②`model/password.rs::forbid_username_normalizes_both_sides_and_requires_equality_not_containment`——釘 `pw` 側
  `to_lowercase()`（原本三支涉此條的測試樣本密碼清一色全小寫 ⇒ 該側是 no-op、vacuous）＋「相等非包含」。
  變異：拿掉 `pw.to_lowercase()` → FAILED，`password.rs:618 assertion left == right failed:
  ★pw 側大寫、帳號名小寫須拒——pw 側的 to_lowercase 是 load-bearing`。還原後 md5 逐位對照。
- **主線於邊界修的三處純文字勘誤**（零行為面）：`handler/common.rs` 的 `json_or_default` 射程名冊
  「四域／13 支」→**「七域／25 支」**（實測 ip_rule 3／throttle 1／role 8／menu 4／policy_archive 1／user 8／
  user_center 1；四域→16 支那半是本單元進場前的既有漂移、一併訂正）；`handler/auth/refresh.rs` 3 處＋
  `handler/auth/logout.rs` 1 處的舊測名 `key_builders_render_nine_literals`→`..._ten_literals`；
  `tests/menu_domain_serialization.rs:525` 的 `advisory_lock_user` 仍指舊家 → 改指 `model::facade::sys_user::`。
- **契約勘誤（主線工程自決、回報備查）**：`contracts/wire-user-admin.md` 之 `UserRecord.nickName` 由 `string`
  訂正為 **`string | null`**。四項證據一致指向可空：同檔 §3 addUser 之 `nickName?`（空字串→NULL）／DB
  `sys_user.nick_name` nullable=YES／rev5 既有同族欄慣例 `Api.RoleAdmin.roleMemo: string | null`／rev4 自身 typing
  `nickName?: string | null`；照原字面落地就得在 handler 端捏空字串當值＝rev4 空字串摺疊形（R2 明列不帶回）。
  ⇒ 判為**落字之誤而非二選一拍板**；碼面 `Option<String>` 為正、不改。★後續 T029／T067 之 typings 與裁判照訂正後口徑寫。
- **工程自決追認（agent 提報、主線復核後採納）**：T010 之 `touch` 的 `created_at` 取應用層 `facade::now_ts()`
  而非 SQL `now()`——PG 的 `now()`＝`transaction_timestamp()`、同 txn 內恆定，會讓 T010 明列的「覆寫更新時戳」
  測當場失去鑑別力（rev4 為此改用 `clock_timestamp()`）；且 `ON CONFLICT DO UPDATE` 走 UPDATE 路徑、欄 DEFAULT
  只在 INSERT 省略該欄時生效 ⇒ 該欄本就非顯式給值不可。已於 `touch` doc 逐字記載。
- **允許檔清單外的既成改動（主線復核後放行）**：`facade/sys_casbin_archive.rs`（2 處）與 `facade/sys_login_attempt.rs`
  （2 處）——皆為 `advisory_lock_user` 搬家後的 intra-doc link 更新、**純註解零行為面**，屬 CLAUDE.md 防呆⑥
  「tasks 涉檔 ∪ review findings 指涉檔」之合法擴面。
- **升級主線的待辦**：`test_db::UserCleanup` 兩建構子並存＝過渡形（統一需動 `facade/sys_role.rs` 3 處＋
  `handler/policy_archive.rs` 1 處、皆在本單元允許清單外）→ 已立 **B-135**。
- **踩坑**：`AppError::BizData` 的窮舉 match 臂寫成 `(..)` 會被 Lint24 判成「構造點無法靜態解析」而 fail-loud，
  且 `cargo` 全綠時完全看不見 → 已立 **L-064**（臂一律寫 `(_, _)`；單元自驗不得只跑 cargo）。

**Checkpoint**: Foundation ready——政策／撤銷／守門／節流／DTO／守衛就位，各 US 可開。

---

## Phase 3: User Story 1 — 超管使用者管理全套（P1）🎯 MVP

**Goal**: 七支管理端點（列表／回收桶列表／新增／編輯／單刪／批刪／復原）全真：唯一性、三態、值 diff no-op、seed 保護、self 五不、
軟刪硬刪指派、復原零回灌、角色集全量替換＋判定面同步；前端 user 頁列表與抽屜接真。

**Independent Test**: quickstart §1（curl 七支）＋§6-1（CDP Super 動線）；Admin 對六支寫端 5003。

### Tests for User Story 1 ⚠️（先紅後綠）

- [X] T022 [P] [US1] `rust-api/server/src/model/facade/sys_user.rs` 測段：寫端五組——`insert`（唯一撞 23505 兜底、空字串→NULL、
  預設啟用、零角色）／`update`（三態、`userName` 出現即拒、值 diff no-op、roleIds 全量替換、界外 id 拒）／`soft_delete`＋
  `batch_soft_delete`（seed 保護、self、任一違規整批 rollback、指派硬刪、空陣列 no-op）／`restore`（同名活性撞、同信箱活性撞、
  零回灌、status 保留）／`list`＋`list_deleted`（排序、濾、分頁）。
- [X] T023 [P] [US1] `rust-api/server/src/handler/user.rs` 測段（endpoint 級、`oneshot_json_from` 帶真 connect-info）：七支各正向＋
  拒因映射（`notFound`／`userNameExists`／`userEmailExists`／`userEmailInvalid`／`userNameImmutable`／`seededProtected`／
  `cannotDeleteSelf`／`cannotEditSelfRoleOrStatus`／`roleNotFound`）；稽核列同交易斷言（`operation`／payload 不含 `$argon2`）。
- [X] T024 [P] [US1] `rust-api/server/tests/contract.rs`：七支 ContractCase（`user-get-list`／`user-get-deleted`／`user-add`／
  `user-update`／`user-delete`／`user-batch-delete`／`user-restore`；case_key 反查形、不抄 rev4 路徑字面）；`ROUTES_COUNT` 斷言同步。

### Implementation for User Story 1

- [X] T025 [US1] `rust-api/server/src/model/facade/sys_user.rs`：寫端家族實作（`insert`／`update`／`soft_delete`／`batch_soft_delete`／
  `restore`／`list`／`list_deleted`）——鎖序照全程紀律；`update` 之 roleIds 走 T016 `replace_roles_of_user`；軟刪同交易
  `delete_all_of_user`＋`revoke_all_of_user`（事件 `user_deleted`）；`violated_constraint` 收斂 23505；
  ★錯誤型 enum 逐支（`UserCreateError`／`UserUpdateError`／…）供 handler remap。
- [X] T026 [US1] `rust-api/server/src/handler/user.rs`：七支 handler＋`begin_and_lock_user`（begin→advisory(uid)→`FOR UPDATE` 活性列）＋
  `finish_user_write`（稽核→commit→**斷權整腿**〔交易內 `revoke_all_of_user`＋逐 sid `session_event`；commit 後
  best-effort 逐 sid `cache::denylist_set(sid, reason, ttl.refresh_secs)`、失敗只 warn〕→reload 條件）＋`map_*_err` remap；
  ★停用（status→2、reason `user_disabled`）與刪除（reason `user_deleted`）兩路於本 task 即完整生效——US1 之
  「被撤者下一次請求 8888」為本 phase 驗收條件、不得延到 US2；守門固定序（①notFound②seed③self
  ④`assert_no_escalation`⑤業務）；共用件零拷貝。
- [X] T027 [US1] `rust-api/server/src/router.rs`：七條 RouteDef（`Protection::Policy`、DELETE 兩支）＋`ROUTES_COUNT` 49→56；
  `docs-sync.py generate` 併 `reference/routes`。
- [X] T028 [US1] `rust-api/server/src/handler/user.rs`＋`rust-api/server/tests/authz_entrypoint_lint.rs`：角色集**實際變更**時
  commit 後 `reload_enforcer`（B-093 閉合、Applied 即觸發不問 diff 之口徑照 006 grant 面）＋`RELOAD_CALL_FILES` 擴
  `handler/user.rs`（恰等斷言、實得序以實跑為準）＋deleteUser 硬刪指派亦觸發（data-model §3.4）＋測（無角色變更零觸發之特性測）。
- [X] T029 [US1] `base-web/src/typings/api/rev5-user-admin.d.ts`＋`base-web/src/service/api/rev5-user-admin.ts` 新檔（`Api.UserAdmin.*`；
  contracts/wire-user-admin.md 逐欄；直接路徑 import 不經 barrel；`system-manage.ts` 不動）＋`pnpm exec oxlint <file>` 綠。
- [X] T030 [US1] `base-web/src/views/manage/user/index.vue`（修改型 (v)、逐行 `原行:`）：接真 `fetchGetUserList`／`fetchGetDeletedUsers`；
  刪 console.log 假實作；回收桶 `showDeleted` toggle 切兩資料源（已刪模式隱搜尋卡、operate 欄換復原、不加刪除時間欄）；
  列表欄含角色／狀態／會話政策／記事／審計欄；`scroll-x`＝Σ 欄寬（依 T004 量測）；★治理清單呼叫帶參（B-132 於本頁結構性不重現）。
- [X] T031 [US1] `base-web/src/views/manage/user/modules/user-operate-drawer.vue`（修改型 (v)）：接真 `fetchAddUser`／`fetchUpdateUser`；
  刪 `getRoleOptions()` mock 段改打 `fetchGetAllRoles`；修 `path="email"`→`userEmail`（帶 `原行:`）；password 僅新增模式；
  `userName` 編輯模式 disabled；memo textarea；update wrapper 剝 `userName`；★角色下拉全列（不預判包含規則、G8）。
- [X] T032 [US1] `base-web/src/locales/langs/{zh-cn,en-us}.ts`＋`base-web/src/typings/app.d.ts`：`page.manage.user` 補列表／抽屜／
  回收桶／確認框鍵（兩語鍵集相等、依 contracts/msg-keys.md 候選）＋`App.I18n.Schema.page.manage.user` 型節；`pnpm typecheck` 綠。

★**U2 執行結果（workflow `wf_44629d8c-192` 實作＋`wf_bc16443b-8c1`／`wf_5f336143-fed` 兩支審查專跑、共 24 agents、2026-08-28 收尾）**

- **量**：rust 測試 878→**924**（淨增 46）；**ROUTES 49→56**；`RELOAD_CALL_FILES` 三檔→**四檔**（實得序 menu < policy_archive < role < user）；
  contract case 50→57。容器內 serial rc=0、`cargo fmt` 綠；七閘＋`fork-delta-lint` 全綠、`docs-sync lint` 0 錯誤、`pnpm typecheck` rc=0。
  零 migration、零 seed 變更；seed 三帳號完整性複驗通過。
- **審查**：規格符合性第 2 輪零 blocker 收斂；碼品質輪跑滿 3 輪 fix＋確認輪，確認輪餘 2 筆——主線逐項自 grep 復核，**兩筆全數成立**、已於邊界修完。
- ★**跨單元埋雷（本輪最有價值的一筆）**：`add_user` 的 ④ `assert_no_escalation` 保留位原落在 `state.db.begin()` **之前**、即
  `roleIds` 解出之前，與 contracts §3 的守門序（`roleNotFound` → `N ⊆ A`）相反。U2 零行為影響（④ 尚未實作），但**T054 照原位填**會讓
  「界外 roleId ＋越權角色集」的請求回 5003 而非 `roleNotFound`。已把保留位移到 `sys_user::insert` 呼叫之前、三處 doc 序訂正到與契約逐字同序。
- **碼品質輪修掉的 vacuous 守門（各附變異紅證）**：①島 I1 的 per-user advisory 鎖在五個寫端呼叫點**全無紅點**（整支拔掉或移到
  `FOR UPDATE` 之後全量測試仍綠）→ 補 `test_db::assert_user_advisory_precedes_row_lock` 骨架＋逐寫端腿；②denylist 廣播的
  **TTL＝refresh_secs 無紅點**（改 access_secs 全綠——而那正是憲法島 C 點名要修的 rev4 缺陷形）；③**denylist reason 字面零機器守**
  （改 `admin_kick` 全綠 ⇒ 被撤者由 8888 靜默變 7777 modal）；④三支純函式守門的多數分支無紅點（email 五腿只覆蓋一腿、
  userName 長度上界零覆蓋、`wire_gender_tristate` 三腿全零）；⑤`sys_user::update` 自行重算 `roles_changed`、**丟棄**
  `replace_roles_of_user` 的回值，使其 doc 宣告的「reload 唯一判準」零消費。
- **主線於單元邊界補的守門＋變異紅證**：`facade/sys_user.rs::UserCreate` 的手寫 `Debug` 遮蔽（島 I5 密碼三重不洩之**日誌面**）
  全樹零測釘 → 補 `user_create_debug_redacts_the_plaintext_password`（三腿：不含明文／含遮蔽字面／非敏感欄照印）＋把第三份
  `"<redacted>"` 字面收攏為檔內 `const REDACTED`。變異（`.field("password", &self.password)`）→ FAILED at `sys_user.rs:1901`，
  訊息逐字印出明文；還原後 md5 逐位對照。
- ★**主線於邊界補的 i18n（Lint24 同步律）**：U2 落了 11 個新 `biz.user.*` 實發鍵，依 tasks.md 全程紀律「同一次工作樹編輯內齊備、
  孤兒鍵窗不得跨越任何一次外層 commit」，於本單元邊界補齊四處（`zh-tw.ts`／`zh-cn.ts`／`en-us.ts` backend 樹＋`app.d.ts` backend 型節）。
  ★**刻意只補 11 鍵**：Lint24 為**雙向**閘（`tools/docs-sync.py` 之 `frontend - backend - whitelist` → 孤兒鍵 ERROR），
  另 9 鍵的後端構造點要到 U3／U4／U5 才存在 ⇒ **T051 的射程隨之改為「補剩餘 9 鍵」**。
- **主線裁定（回報備查）**：①`active_email_taken` 的 `exclude_id` 參數**移除**——我在 U2 中段曾依 implB 的 escalation 追認保留該參數，
  碼品質輪查出其 `Some` 分支**結構性不可達**（該 fn 首道濾網已是 `deleted_at IS NULL`、而 restore 的標的是已刪列）、
  且 fn doc 對它的必要性敘述不實 ⇒ **推翻先前追認**、移除參數並補真正的機器釘
  `restore_does_not_treat_the_targets_own_email_as_a_conflict`（釘住「排除標的的是軟刪濾網」）。
  ②手機欄「≤32」守門缺口不在本刀發明新 msg key（四權威皆無、rev4 藍本亦無）→ **B-136** 交 user 收刀前裁定。
  ③`handler/role.rs` 兩處 006 期失真 doc 訂正（候選外 15→**8** 列、protected 仍 1；「本刀終態 35」→「本刀 U2 後 42、終態 45」）。
- **新帳**：B-136（手機守門缺口）／B-137（`R_SUPER` 生產面兩份字面）／B-138（`ilike_contains` 三份拷貝待收攏）／
  L-065（破壞性守門的變異測試會真的毀 seed）／L-066（負向樣本要帶清理鍵前綴）／L-067（Lint25 的執行單元輪次形連本代都判紅）。

**Checkpoint**: US1 可獨立驗收——七支 API＋user 頁列表與抽屜；斷權由 Foundational 之 `revoke_all_of_user` 已生效（分派與文案於 US2 定案）。

---

## Phase 4: User Story 2 — 斷權（踢除與撤銷兩形之合稱）即刻失效（P1）

**Goal**: 踢除／停用／刪除／重設密碼四路撤銷語意定案：同交易撤全部 active、事件五 reason、denylist best-effort、
`admin_kick`→7777 新鍵、其餘→8888、refresh 鎖內活性重驗。

**Independent Test**: quickstart §2（雙 token 斷權動線）＋§6-4（CDP 7777／8888 實機）。

### Tests for User Story 2 ⚠️

- [X] T033 [P] [US2] `rust-api/server/src/handler/user.rs` 測段：kick 正向（`{revoked:n}`、rotated 不動、事件 `admin_kick`、稽核 `kick`）＋
  射程（self 拒、Super 可踢〔受包含規則〕、停用可踢、已刪 `notFound`）；停用／刪除路徑之撤銷斷言（事件 reason 逐值）。
- [X] T034 [P] [US2] `rust-api/server/src/auth/enforce.rs` 測段：denylist reason 分派三向（`kicked`→7777＋既有鍵、`admin_kick`→7777＋
  `auth.session.kickedByAdmin`、`revoked`→8888）＋既有 003 測全綠（島 C 語意不變）。
- [X] T035 [P] [US2] `rust-api/server/src/handler/auth/refresh.rs` 測段：停用使用者之 refresh 鎖內重驗被拒（8888）／已軟刪同；
  正常使用者不受影響（既有 rotation／grace／reuse 測全綠）。
- [X] T036 [P] [US2] `rust-api/server/tests/contract.rs`：`user-kick` ContractCase；`ROUTES_COUNT` 56→57。

### Implementation for User Story 2

- [X] T037 [US2] `rust-api/server/src/handler/user.rs`：`kick_user` handler（沿用 T026 之 `finish_user_write` 斷權整腿、
  ★本 task 只增 kick 專屬的 reason `admin_kick` 分派與 `{revoked:n}` 回應形，不重寫該腿）＋`router.rs` 一條＋
  `ROUTES_COUNT` 56→57；重設密碼路徑（US3 T045）亦沿用同一腿、reason `password_reset`。
- [X] T038 [US2] `rust-api/server/src/auth/enforce.rs`：`enforce_mw` 依 denylist reason 分派碼與鍵（新增 `REASON_ADMIN_KICK` 臂）；
  ★doc 明寫三 reason 不互換（島 C）；`backend.biz`／`auth.session` 新鍵四處同步（Lint24 同步律）。
- [X] T039 [US2] `rust-api/server/src/handler/auth/refresh.rs`：鎖內使用者活性重驗（依 T002④ 落點；不活→既有 8888 路徑）＋
  doc 記「003 島 C 新增判定腿、非方向反轉」；★`getUserInfo`／`enforce_mw` 不判 status 之 003 拍板不動。

★**U3 執行結果（實作 workflow `wf_f593ae25-d56` ＋審查專跑 `wf_7bd2441d-418`〔12 agents〕、2026-08-29 收尾）**

- **量**：rust 測試 924→**933**（淨增 9）；**ROUTES 56→57**；contract case 57→**58**；backend msg key +2
  （`auth.session.kickedByAdmin`＋`biz.user.cannotKickSelf`）。容器內 serial rc=0、`cargo fmt` 綠；
  七閘＋`fork-delta-lint` 全綠、`docs-sync lint` 0 錯誤、`pnpm typecheck` rc=0。零 migration、零 seed 變更。
- ★**本輪抓到的真缺陷（規格輪第一筆）**：`handler/auth/refresh.rs` 的 `revoked` 分支**未接 `admin_kick`** ⇒
  被管理員踢除者走**換發路徑**時得 8888＋`auth.session.reLogin`，而非 US2 Scenario 1 要求的 7777＋
  `auth.session.kickedByAdmin`。連帶揭穿 `auth/enforce.rs` 的 fn doc 假述——它宣稱自己是全 codebase 唯一的
  reason→(碼, msg 鍵) 分派點，實際上 `refresh.rs` 是第二處。兩者同批修，`cache/mod.rs` 的
  `REASON_ADMIN_KICK` 型 doc「分派點恰一處」亦同批訂正為恰二處。
- **審查輪**：規格符合性 **第 3 輪（確認輪）零 blocker 收斂**（round 0／1／2 各 3／2／1 筆、逐輪修完）。
  碼品質輪跑了 3 輪 review（3／4／3 筆）＋2 輪 fix，**第 13 支 agent 撞保險絲 throw**（見下）。
- ★★**碼品質輪的確認輪未跑（誠實記載、本單元的已知缺口）**：碼品質 round 2 的 3 筆由**主線接手修完**
  （取鎖點機器證④／`user.rs` 三處「七端點」bump／`self_heal` 併入 `test_db::heal`），並各自完成
  自驗與變異紅證；但**防呆⑤ 所要求的「fix 迴圈後之確認輪」在本單元未執行**。
  ⇒ 殘餘風險＝「主線那三筆修法本身是否引入新問題」，現有覆蓋＝全量 933 綠＋七閘＋變異紅證。
  ⇒ **處置：併入收刀前的 final holistic review**（CLAUDE.md §2 之「全單元完成 → final holistic review」），
  屆時本單元列為重點掃描面；另 U9 之 T069（全量閘）與 T070（CDP 三方對照）亦覆蓋本單元行為面。
- **保險絲事故**：審查專跑的 `AGENT_FUSE` 我手挑 12，而該形的**結構最壞值是 14**
  （0 implementer ＋ 2 cycle × (2×`MAX_FIX_ROUNDS`+1) ＝ 2×7）⇒ 健康的 run 在第 13 支被誤斬。
  已立 **L-068**（保險絲一律由同檔常數推導＋自我斷言、不得手挑），memory 之編排定型亦補上該公式。
- **主線於單元邊界的處置六則**：
  ①**三支既有測被打紅、皆在允許清單外**（agent 依空間邊界未動、升級主線）——`handler/role.rs` 的
  `POLICY_ENDPOINT_COUNT` 42→43＋末條期望值 `restoreUser`→`kickUser`＋註解續 bump 說明；
  `handler/auth/logout.rs` 兩支測各補三行 `sys_user` fixture（T039 把「查無列」判為不活所致）。
  ②`handler/mod.rs` 模組 doc「上線七支／餘三支」→「八支／餘二支」＋補記 `ROUTES_COUNT` 56→57。
  ③**追認** `AppError::ModalLogoutByAdmin` 新變體與 7777 **同列共用**——Lint24 的後端實發集只掃
  `AppError::Biz/BizData` 構造點與 `key()` 固定臂，而既有 `ModalLogout` 的鍵是寫死固定臂、無處承載第二個值；
  形沿 `BizData` 共用 2222 列之先例，13 碼矩陣零變更、可發碼仍九。
  ④**追認** T039 刻意**不加** `FOR UPDATE`（用 `find_by_id`）——refresh 端點沒取 per-user advisory，
  對 `sys_user` 下列鎖等於「列鎖→無 advisory」插隊，與 user 域寫端的 advisory→列 固定序互為 ABBA（島 I1）。
  ⑤**追認射程外擴**：base-web 四檔多補 `biz.user.cannotKickSelf`——T037 的 self 守門必然構造該鍵、
  Lint24 「後端有前端無」方向會逐鍵 ERROR，與「lint 0 錯誤」硬性要求直接衝突；★該限制是**任務書的疏漏**
  （我方 prompt 只授權 `kickedByAdmin`）。⇒ **T051 射程由九鍵再縮為八鍵**（已改本檔）。
  ⑥**接受探針揭露**：implementer 曾暫改清單外兩檔驗證補丁充分性（結果 930/930）後以 sha256 還原——
  主線復核交付樹零殘留，判為與變異測試同族的合法手法（改壞→驗→逐位還原）。
- **變異紅證合計九發**：implementer 六發（三向 reason 分派拔臂／碼對鍵錯／refresh 拔活性判／判準漏
  `deleted_at`／kick 動到 rotated／denylist reason 誤傳）＋射程二發（替 kick 補 seed 守門→Super 踢不掉即紅／
  拔 self 守門→回 0000 即紅）＋主線一發（把 `kick` 的 advisory 取鎖行下沉到列鎖之後 →
  `55P03…該寫端先鎖列再取 advisory（島 I1 固定鎖序反轉、與亦取同一把鎖的 login 構成 ABBA）`）。
- **kick 的射程**（刻意、已有測與紅證）：**不受 seed 保護**——Super 可踢、停用帳號可踢、self 禁踢、
  已刪 `notFound`（contracts §8 與 data-model §3.1 之 kick 列守門僅 notFound→self→T ⊆ A）。
- **守門固定序第④步**在 kick 亦**只留掛點位**、doc 標明由 US4 之 T054 一次掛滿八支寫端。

**Checkpoint**: US2 可獨立驗收——四路斷權即時、分鍵正確、refresh 不再是漏洞。

---

## Phase 5: User Story 3 — 密碼政策與自助改密（P1）

**Goal**: 八鍵政策生效於三入口（登入不驗）、違規明細攜參下發、設密冷卻、自助改密五步序、舊密節流；**自助路由白名單
（非超管可達個人中心）**；個人中心改密卡與產密浮層。

**Independent Test**: quickstart §3（政策／改密／節流 curl）＋§6-5（CDP 個人中心動線）。

### Tests for User Story 3 ⚠️

- [X] T040 [P] [US3] `rust-api/server/src/handler/user.rs` 測段：addUser／resetUserPassword 之政策違規（`BizData` 攜 `violations`）、
  冷卻（`remainingSeconds`、interval=0 停用、不同 operator 互不影響、addUser 計入）、self 拒（`cannotResetSelfPassword`）。
- [X] T041 [P] [US3] `rust-api/server/src/handler/user_center.rs` 測段：changePassword 五步序逐步拒因＋成功後撤他 session 保留當前＋
  事件 `password_changed`＋稽核 `change_password`＋custody touch。
- [X] T042 [P] [US3] `rust-api/server/src/throttle/change_pwd.rs` 測段（整合面）：連錯 5 次後第 6 次 `changePasswordThrottled`（在雜湊驗證前、
  零稽核）、成功改密清桶、redis 停機 fail-open＋降級計數。
- [X] T043 [P] [US3] `rust-api/server/src/handler/auth/login.rs` 測段：★登入路徑零政策驗證之機器守（seed 帳號 6 字元密碼登入成功；
  `login.rs` 全檔零 `validate_against_policy` 引用之 grep 型斷言）。
- [X] T044 [P] [US3] `rust-api/server/tests/contract.rs`：`user-reset-password`／`user-center-change-password`／
  `user-center-get-password-policy` 三 ContractCase；`ROUTES_COUNT` 57→60。

### Implementation for User Story 3

- [X] T045 [US3] `rust-api/server/src/model/facade/sys_user.rs`：`reset_password`（政策→冷卻→UPDATE＋custody touch＋撤全 active
  ＋事件 `password_reset`）／`change_own_password`（五步序；成功 `revoke_others_of_user(keep=sid)`＋事件 `password_changed`）；
  ★`insert` 補政策＋custody touch（G14）。
  ★**as-built（ADR 0068）**：雜湊**生成**外移至 handler 取鎖前（`password::NewPassword::prepare`），故上列兩序皆不含 `hash` 一格；
  facade 本體零 argon2 生成、有源碼掃描守 `password_hash_never_computed_inside_row_lock`。舊密 `verify` 續留鎖內（島 I1 守門判定）。
- [X] T046 [US3] `rust-api/server/src/handler/user.rs`：`reset_user_password` handler＋`router.rs` 一條＋`ROUTES_COUNT` 57→58；
  ★self 拒導向個人中心（拒因鍵 `cannotResetSelfPassword`）。
- [X] T047 [US3] `rust-api/server/src/handler/user_center.rs`：`change_password`（Authed、標的恆 `claims.uid`、節流前置）＋
  `get_password_policy`（七鍵投影）＋`router.rs` 兩條（`Protection::Authed`、零 casbin seed）＋`ROUTES_COUNT` 58→60。
- [X] T048 [US3] `rust-api/server/src/handler/route.rs`：自助路由白名單（FR-032）——碼內常數
  `SELF_SERVICE_ROUTES: [&str; 1] = ["user-center"]`＋`get_user_routes` 於 casbin 過濾結果**之後**恆併入該白名單
  （聯集去重；`hide_in_menu` 故側欄不現、只從頭像下拉進）＋檔頭「rev4 之 `SELF_SERVICE_ROUTES` 不帶回——前提未成立」
  句改寫為「自本刀帶回（承 rev4:ADR 0065）」＋常數 doc 寫明擴充紀律（只收「受眾＝本人」之自助頁家族、RBAC 資源頁
  MUST NOT 入）；★單測兩向：零 menu 政策角色（新建之零角色帳號）仍得 `user-center` 路由／白名單外路由不受影響；
  seed 之 `p|R_SUPER|user-center|menu` 保留不動（聯集下冗餘無害）。★本 task 未完成前，非超管（含 R_ADMIN／R_USER）
  進不了個人中心 ⇒ US3 之 Independent Test 與 T070 之 CDP 第 5 步皆不可驗。
★**U4 執行結果（主 run `wf_d72fc03f-63e` 8 支＋碼品質專跑 `wf_032b5464-cc3` 7 支、2026-08-29 收尾）**

- **量**：rust 測試 933→**958**（淨增 25）。容器內 serial rc=0；`cargo fmt --all -- --check` rc=0；
  ROUTES 57→**60**；`POLICY_ENDPOINT_COUNT` 43→**44**（三條新 route 只有 `resetUserPassword` 進政策維，
  user-center 兩支是 `Protection::Authed`＋零 casbin seed）；七閘全綠＋`docs-sync lint` 0 錯誤。
  零 migration、零 seed 變更。base-web 四檔恰補**七鍵**（`sessionPolicyInvalid` 構造點在 T058／T060 ⇒ 本單元補了就是孤兒鍵紅）。
- **審查**：規格符合性四輪（三輪 fix＋確認輪）、碼品質四輪（三輪 fix＋確認輪），**兩輪的確認輪各自仍有 blocker**
  ⇒ script 依防呆⑤ 判「跑滿上限」return。★**但這不是不收斂**：每輪 blocker 集合皆相異、每輪 fix 皆有改動，
  是逐層深挖（規格輪 2+2+2+1 筆、碼品質輪 5+4+5+3 筆，共 24 筆）。主線據此判定接手修而非重跑審查。
  ★**副作用**：規格輪 return 使**碼品質輪零輪次** ⇒ 依 L-027 另開新 runId 專跑（不用 resume），CONTEXT 烤入十四項勿重報清單。
- **本輪最有價值的三筆 finding**：
  ①**argon2 雜湊落在列鎖內**（規格輪第 2 輪）——違反憲法島 I5 末句。fix 新增 `password::NewPassword`
  （明文＋PHC 成對載體、唯一構造路徑 `prepare()`、**刻意零 `Debug` impl** ⇒ 想 `derive(Debug)` 的外層型直接編譯失敗），
  兩支寫端改由 handler 於取鎖前算；補源碼掃描守 `password_hash_never_computed_inside_row_lock` ＋三發變異紅證。
  ②**`passwordPolicy` 譯文佔位符 `{list}` vs 後端 data 鍵 `violations`**（碼品質輪第 3 輪）——**使用者可見缺陷**：
  違規明細會在 toast 上整段消失，而 Lint24（只比鍵集）／typecheck（看不到字串內容）／端點測（只驗 code 與 msg 鍵）三道全部攔不到。
  ★根因在契約表**自身自相矛盾**（鍵欄寫 `{violations}`、兩個藍本欄寫 `{list}`），前端照藍本欄抄。
  已依 §4 用 `errata` 機器枚舉全 repo（命中 1 處）逐處訂正；衍生 **B-139**。
  ③**`finish_user_write` 提為 `pub(crate)` 打穿 `RELOAD_CALL_FILES` 名冊閘射程**（碼品質輪確認輪）——
  該閘掃 `reload_enforcer` token 的檔集合，而唯一那行 reload 住在 `finish_user_write` 體內 ⇒
  任何 handler 都能 `use` 它並傳 `reload = true` 觸發全域熱套而不進名冊、全樹零紅點。已立 **L-069**。
- **主線於單元邊界的處置五則**：
  ①**補取鎖點機器證⑤⑥**（規格確認輪唯一 blocker）：查證屬實（`sys_user.rs` 六個取鎖行對四支機器證），
  區塊標題「四支」→「六支」。★第⑥支（`change_own_password`）是本組實害最重的——該端點 handler 只做
  `state.db.begin()`、不走 `begin_and_lock_user`，故 facade 那行是自助改密路上**唯一且承重**的取鎖點；
  刪掉它信封／拒因／票面／事件／稽核一字不變、全樹仍綠。兩發變異紅證（各下沉取鎖行）皆得逐字
  「55P03＝該寫端先鎖列再取 advisory」，還原 `diff -q` 逐位相同。
  ②**新增 `FINISH_USER_WRITE_CONSUMER_FILES` 名冊閘**（碼品質確認輪第 1 筆）：`tests/authz_entrypoint_lint.rs`
  加家檔常數＋消費者名冊＋`finish_user_write_consumers_match_declared_roster`；連帶把 detector 與掃描面
  泛化為 `call_lines_of(stripped, pat)`／`scan_excluding(home_rel, detector)`（零拷貝、既有 16 支測全數不受影響）。
  兩發變異紅證：名冊清空→紅且實得 `[("handler/user_center.rs", [275])]`（證明真的掃到）；detector pattern 打錯一字→紅且實得 `[]`（證明綠不是兩邊皆空）。
  ③**`sys_token::revoke_others_of_user` 的 fn doc 訂正**（確認輪第 2 筆）：原文寫死 login 語境
  （caller 恆 login 第⑨步、reason 恆 `kicked`、`keep_sid` 恆「本次登入新生」、advisory 恆由 login 持有），
  而本單元讓自助改密成為第二個 caller（reason `password_changed`／denylist `revoked`／keep 是既有會話／
  advisory 自己取）。已比照姊妹 `revoke_all_of_user` 的形改為逐路列消費者，並補「reason 與 keep 語意
  一律留在 caller、勿寫回本層」的警語。★審查員誤判該檔在允許清單外（實際在內），但 finding 本身成立。
  ④**「走 `nextval` 者恰二支」名冊 bump 為三支**（確認輪第 3 筆）：本單元的冷卻測第①腿真的打 `addUser` 建列。
  行為面本就正確（該測已掛 `with_name_prefixes`），純註解失真。順帶記入「政策違規測雖打 addUser 但被守門擋在
  INSERT 之前 ⇒ 不消耗 `nextval`、不入名冊」。
  ⑤**契約勘誤**：`contracts/msg-keys.md` 之 `passwordPolicy` 譯文欄 `{list}` → `{violations}`（見上②）。
- **拍板級升級一筆、user 親決**（2026-08-29）：`change_own_password` 五步序第④格的 `password::verify` 仍在鎖內，
  與島 I5 末句字面相衝、與島 I1「守門判定 MUST 鎖內重驗」正面相碰。三選項（改條文／立例外 ADR／verify 外移回 rev4 形）
  中 user 選**改條文**：憲法 **1.9.0 → 1.9.1**（PATCH／澄清），末句區分雜湊**生成**（鎖外）與**驗證**（鎖內），
  **碼零改動**；ADR **0068**。理由＝承襲 rev4 條文時字面不夠精確，非真衝突。
- **本單元新帳**：B-139（佔位符↔data 鍵名零機器守）／B-140（`auth::Identity` 不帶 `sid`、`current_sid` 是 Bearer 解析小抄本）／
  B-141（三件共用件住哪一家、`finish_user_write` 結構性搬不動）／L-069（可見性放寬打穿名冊閘射程）。
- **未竟**：碼品質輪確認輪的三筆由主線修完後**未再跑一輪確認**（同 U3 之形）⇒ 併入收刀前的 final holistic review。

★**U6 執行結果（workflow `wf_709a7170-fec`、11 支、2026-08-29 收尾）**

- **量**：前端接真十檔（含兩支新檔）。`pnpm typecheck` rc=0｜兩支新檔 `oxlint` 0 error／0 warning｜
  `fork-delta-lint` 綠（授權判定 101→**136** 處）｜`view-render-guard` 綠｜`docs-sync lint` 0 錯誤。零 rust 改動。
  `page.manage.user` 兩語各 19→**37 葉鍵**（+18、鍵集相等）；`scroll-x` **962→1932**（16 欄 Σ、機器重算核對）。
- **審查**：★**規格符合性輪第 1 輪即零 blocker**（本刀最好的一次）；碼品質輪跑滿三輪 fix＋確認輪，餘 1 筆。
- ★★**用途 (v) 的變異自證（L-063 補做、本單元是 (v) 的第一個落標記處）——這次真的紅**：
  改壞憲法 §III.2 之 (v) 列範圍欄路徑 → `fork-delta-lint` **REAL_RC=1**、14 筆「不在 ★軌道
  `BASE-WEB-MANAGE-PAGE-WIRING(v)` 授權檔案集」；還原後 md5 逐位相同、RESTORED_RC=0。
  ⇒ L-063 的預測完全兌現：T003（Amendment 當下）那次 rc=0 是**結構性 vacuous**（碼裡零 (v) 標記可比），
  真正的守門力要到第一個落標記處才驗得出來。★同紀律套用於 (vi)→T050、LOGIN-CAPTCHA(ii)→T065。
- **主線於單元邊界的處置四則**：
  ①**契約勘誤兩處**：`wire-user-admin.md` §3／§4 的 `nickName?: string` 補 `| null`——§4 的 updateUser 走
  tristate（後端 `Option<Option<String>>`）、與本節散文自己寫的「null＝清空」相抵，且與同 Body 其餘四個可空欄不一致；
  與 §共用型那筆（U1 邊界）**同一欄同源落字**。★依 §4 用 `errata` 機器枚舉（5 處命中）**逐處判性質**：
  §1 之 `UserSearchParams.nickName` **刻意不補**（模糊過濾字串、只有「有值／未設」兩態，後端以
  `filter(|v| !v.is_empty())` 把空字串當未設，標 `| null` 憑空多一個沒有語意的態）——理由已就地寫進該行，
  免得下次 errata 命中時又被「順手補齊」。
  ②**`contracts` 新增 §12 已知態**＋**B-143 立帳**：搜尋卡的手機／信箱兩欄填了不會濾（§1 過濾面恰四欄）。
  ★**這對 rev4 是行為回退**（rev4 前後端那兩欄真的會濾），而 `user-search.vue` 不在 (v) 的範圍欄內、
  本刀結構性無法自修 ⇒ 立帳＋列入 T070 的 CDP 已知態排除清單，免得被當成「rev5 沒做完」重新發現一次。
  ③**B-144 立帳**：`pnpm lint` 會改寫允許清單外的既有檔（本輪誤改 `ip-rule/index.vue` 的註解排版、
  成因是該檔本來就不是 lint-clean）——空間邊界靠「工作樹只出現清單內檔」判定，這筆改寫會讓清單外檔平白出現。
  ④**B-145 立帳**：持有停用角色的帳號、其既有指派在抽屜下拉不可見（列 wire 的 `roles` 不濾狀態、
  `getAllRoles` 只回活性且啟用者）。U6 已以「`roleIds` 只在真改了才送」＋`roleAssignLocked` 鎖定態擋住靜默丟失，
  代價是該帳號暫時改不動角色指派。
- **T062 射程改述**：memo 兩面已隨 T030／T031 原文一併落地（列表純文字欄＋抽屜 textarea＋兩語鍵）
  ⇒ T062 縮為**確認輪**、勿重覆施工（已改本檔）。
- **未竟**：碼品質輪確認輪那筆為「結構性無法自修、已立帳」⇒ 無殘留修復項；但確認輪之後未再跑一輪
  （同 U3～U5 之形）⇒ 併入收刀前的 final holistic review。

- [X] T049 [US3] `base-web/src/typings/api/rev5-user-center.d.ts`＋`base-web/src/service/api/rev5-user-center.ts` 新檔＋
  `base-web/src/hooks/business/pwd-policy.ts` 新檔（`buildPolicyRules`；取不到靜默降 required）＋
  `base-web/src/components/custom/pwd-gen-modal.vue` 新檔（`crypto.getRandomValues`、依政策產合規密碼）。
- [X] T050 [US3] `base-web/src/views/user-center/modules/password-card.vue` 新檔（只舊密碼一路、無 radio、規則來自 hook、
  `:user-name` 不用 `authStore.userInfo.userName`）＋`base-web/src/views/user-center/index.vue`（修改型 (vi)：父層骨架、
  只掛改密卡、三卡位留白）。
- [X] T051 [US3] `base-web/src/locales/langs/{zh-cn,en-us}.ts`＋`app.d.ts`：`page.userCenter.*` 新 top-level 命名空間
  ＋`page.manage.user.pwdGen.*`；`pnpm typecheck` 綠（兩語鍵集相等）。
  ★★**射程已四度收窄——backend 樹本 task 一鍵不補**：`backend.biz.user.*` 二十鍵與 `auth.session.kickedByAdmin`
  **已於 U2～U5 各單元邊界全數補齊**（U2 十一鍵／U3 `cannotKickSelf`＋`kickedByAdmin`／U4 七鍵／U5 `sessionPolicyInvalid`）。
  成因＝Lint24 是**雙向**的：孤兒鍵窗不得跨越任何一次外層 commit ⇒ 每個發鍵的後端單元必須在自己的邊界補齊，
  補不齊當場紅、提前補則成孤兒鍵同樣紅。★**本 task 若再補 backend 鍵即為重複宣告**（typecheck 紅）。
  ★`zh-tw.ts` 亦不動——該檔**只有 `backend` 樹**（無 page 樹、非 `App.I18n.Schema` 標註）。

**Checkpoint**: US3 可獨立驗收——政策三入口、明細可讀、冷卻與節流、個人中心可自助改密。

---

## Phase 6: User Story 4 — 授權下放＋no-escalation（P2）

**Goal**: 九處掛點全上、規則對所有角色一體適用（超管 A＝全集）、5003 warn 日誌；前端七碼 gating 與會話政策欄 disabled。

**Independent Test**: quickstart §4（下放後 Admin 動線）＋§6-2／§6-3（CDP 預設態與下放後對照）。

### Tests for User Story 4 ⚠️

- [X] T052 [P] [US4] `rust-api/server/src/handler/user.rs` 測段（每支寫端 ≥2 負向＋1 正向、FR-021）：被授權 R_ADMIN 對持 R_SUPER 標的 5003／
  指派超出自身角色集 5003／Super（僅持 R_SUPER）對持其未持角色之標的成功（A＝全集非 vacuous）；測內以 `casbin_rule` 資料列 grant、
  `CasbinCleanup` 兜底；★停用角色仍計入 T 之案。
- [X] T053 [P] [US4] `rust-api/server/src/handler/throttle.rs` 測段：unlockLogin 帳號維套規則（R_ADMIN 解鎖持 R_SUPER 帳號 5003）／
  IP 維不套（既有行為不變）。

### Implementation for User Story 4

- [X] T054 [US4]（★變異紅證：任取一支寫端拆掉 `assert_no_escalation` 呼叫→實跑 T052 該支負向案確認紅→還原、
  紅證逐字補記本 task；SC-006 之機器承載）`rust-api/server/src/handler/user.rs`：`assert_no_escalation` 掛八支寫端（守門序④；`actor_scope_of`＋
  `role_codes_all_of_user`＋`codes_of_role_ids` 取三元）＋違者 5003 純 key＋`tracing::warn!(actor, target, endpoint)`
  （★不含角色差集）。
  ★**as-built（本刀 U5）**：唯一掛點式＝`handler::user::guard_no_escalation`（`pub(crate)`），八支寫端各呼一次、
  `handler::throttle` 之 unlock 帳號維借道同一支（零同形拷貝）。`restore_user` 的鎖內位置**由 handler 自取
  advisory 生出**（它的①鎖讀住 facade `sys_user::restore` 內、handler 端原本沒有「鎖後、寫入前」的位置）——
  取此形而非改 facade 簽章：後者會讓 facade 的稽核快照依賴 caller 傳值，屬拍板級。
  ★**恆過的只有兩支**（`restore_user` 之 `T ≡ ∅` 且不收 `roleIds`／`update_user_session_policy` 因 super-only）；
  ★`add_user` **非恆過**——`T ≡ ∅` 但 `N`＝請求的 `roleIds` 可越界，「新開一個超管帳號」正是全樹最直接的提權路徑
  （碼品質確認輪抓出守門骨架註解把它誤列為恆過、三處敘述分岔，主線已對齊）。
  ★**變異紅證四發**（皆「先存原文→實跑→寫回」、md5 逐位還原、零 `git checkout`）：
  ①拆 kickUser 的④ → `kickUser／T ⊄ A（★kick 無 seed 保護，擋它的只有島 I7）：5003 走 HTTP 403：
  {"code":"0000","data":{"revoked":1},...} left: 200 right: 403`（被下放的 Admin 真的把持 `R_SUPER` 的帳號踢下線）
  ②整格拆 unlock 帳號維守門 → `★★帳號維套規則：R_ADMIN 解鎖持 R_SUPER 的帳號須 5003 純 key…；實得 None
  left: None right: Some(("5003", "system.forbidden"))`
  ③`set_session_policy` 三值收斂改壞（`if false`）→ `值域外 → 2222：{"code":"0000",...} left: String("0000") right: "2222"`
  ④拆 restoreUser 的④ → `restoreUser／T ⊄ A（合成態：已刪列仍掛 R_SUPER 指派）… left: 200 right: 403`
  ——即那條「生產態恆過所以看不出來」的掛點確實有紅點守著。
  ★**機器閘**：本刀 U5 邊界另補兩張名冊閘（`tests/authz_entrypoint_lint.rs`）——
  `NO_ESCALATION_CALL_FILES`（守「不繞過掛點式、自己直呼純函式」）與
  `GUARD_NO_ESCALATION_CONSUMER_FILES`（守「借道掛點式的人有沒有進過名冊」）；各附變異紅證。
- [X] T055 [US4] `rust-api/server/src/handler/throttle.rs`：`unlock_login` 帳號維分支鎖內加 `assert_no_escalation`（T 取標的全部指派列）；
  IP 維不套；doc 記射程。
- [X] T056 [US4] `base-web/src/views/manage/user/index.vue`（修改型 (v)）：七枚按鈕碼逐鈕 `hasAuth` gating（B-099 形：外層 div 保底＋
  `v-show`＋內層 `v-if`）；★自己那列操作下拉不列「重設密碼」（self 五不）。
- [X] T057 [US4] `base-web/src/views/manage/user/modules/user-operate-drawer.vue`（修改型 (v)）：`sessionPolicy` 欄對非超管
  （`authStore.userInfo.roles` 不含 `R_SUPER`）顯示現值但 disabled＋提示鍵；★不發出必敗的第二支呼叫（G7）；
  self 之 `status`／`roleIds` 控制項 disabled。

**Checkpoint**: US4 可獨立驗收——下放可開關、規則一體適用、UI 誠實。

---

## Phase 7: User Story 5 — 解鎖登入、會話政策、記事欄（P2）

**Goal**: seed 已錨定的三項能力取得消費者：`updateUserSessionPolicy` 端點＋抽屜三值、`user:unlock` 頁首 modal（雙維）、
`user_memo` 兩面（B-003 關帳）。

**Independent Test**: quickstart §1 尾三 curl＋§6-1（CDP 解鎖 modal 與會話政策）。

### Tests for User Story 5 ⚠️

- [X] T058 [P] [US5] `rust-api/server/src/handler/user.rs` 測段：`update_user_session_policy` 三值收斂＋值域外 2222＋與現值相同 no-op＋
  已刪 `notFound`＋改 single 不即時踢（既有 session 仍在之斷言）。
- [X] T059 [P] [US5] `rust-api/server/tests/contract.rs`：`user-update-session-policy` ContractCase；`ROUTES_COUNT` 60→61（終值）。

### Implementation for User Story 5

- [X] T060 [US5] `rust-api/server/src/handler/user.rs`＋`rust-api/server/src/model/facade/sys_user.rs`：`update_user_session_policy` handler＋
  `set_session_policy` facade＋`router.rs` 一條（protected 端點、super-only 結構性）＋`ROUTES_COUNT` 61。
★**U5 執行結果（workflow `wf_4439ba93-594`、15 支＝結構最壞值、2026-08-29 收尾）**

- **量**：rust 測試 958→**969**（淨增 11）。容器內 serial rc=0；`cargo fmt --all -- --check` rc=0；
  ★**ROUTES 60→61＝終值**、`POLICY_ENDPOINT_COUNT` 44→**45＝終態**（末條期望值改 `updateUserSessionPolicy`）；
  七閘全綠＋`docs-sync lint` 0 錯誤。零 migration、零 seed 變更。
  base-web 四檔恰補**一鍵** `sessionPolicyInvalid`（zh-tw 繁體化為「會話策略無效」——與同子樹 `passwordPolicy`
  的「安全策略」用字一致，未改用「政策／工作階段」以免同子樹出現第二種譯法）；★**本刀二十鍵自此補齊**
  （U2 十一鍵＋U3 `cannotKickSelf`＋U4 七鍵＋U5 一鍵）⇒ **T051 射程只剩** `page.userCenter.*` 與 `page.manage.user.pwdGen.*`。
- **審查**：★**規格符合性輪第 3 輪即收斂、零 blocker**（本刀首次規格面一次過）；碼品質輪跑滿三輪 fix＋確認輪，
  確認輪餘 3 筆由主線接手。agent 用量 15＝結構最壞值，保險絲 16 恰好容下（L-068 的推導公式在此得到實測驗證）。
- **主線於單元邊界的處置三則**（皆先自 grep 查證、不採信）：
  ①**守門骨架註解把 `add_user` 誤列為「判定結構性恆過」**（三處敘述分岔：骨架註解／模組 doc 說恆過、fn doc 說
  `N ⊆ A`）——★這正是該註解自稱要防的事：它寫「此處只列名以免有人以為那三處是誤植」，等於主動告訴下一個
  維護者 addUser 那行是裝飾，而 addUser 的 `N` 越界正是最直接的提權路徑。已把它移出恆過名單（三支→兩支）
  並補上「勿把它加回去」的理由與機器證指路。
  ②**補兩張 no-escalation 名冊閘**：`assert_no_escalation` 的呼叫點名冊（守「不繞過掛點式」、FR-018 具名純函式
  單點之機器承載）＋`guard_no_escalation` 的跨 handler 消費者名冊（守「借道掛點式的人有沒有進過名冊」）。
  ★審查員指出的處境與 L-069 逐字同形——`guard_no_escalation` 同樣剛由私有升 `pub(crate)`、被 `throttle.rs` 跨檔
  消費；且本刀真的出現過一份同形拷貝並在 `target` 欄分岔（一份 `?Option<i64>`、一份裸 `i64`，以 `target=<id>`
  過濾只撈得到一半），碼品質輪收攏了拷貝卻沒留下防止下一份的紅點。兩發變異紅證：名冊各自清空 → 實得
  `[("handler/user.rs", [1110])]`／`[("handler/throttle.rs", [218])]`。
  ③**`set_session_policy` 的 `Result<bool>` 收成 `Result<()>`**：那個布林全樹零消費者、零斷言，寫死成單一值也
  不會紅；no-op 的機器承載在端點測的 op-log 列數 delta。fn doc 補上與 `update` 之 `roles_changed`（有實際去處）
  的對照，免得日後有人照類比加回來。
- **契約次序訂正兩處**（規格輪的非阻斷觀察，主線裁定）：`contracts` §7 與 `data-model` §3.1 的 restoreUser 守門鏈
  原把 `T(∅) ⊆ A` 排在同名／同信箱之後，與八支寫端通則序（④先於⑤業務）相反。生產態下 `T ≡ ∅` ⇒ ④恆過、
  兩序在任何生產可達輸入下逐位同形，唯合成態才分得出 ⇒ **取通則序**，免得八支裡留一支需要另記的例外。
  依 §4 用 `errata` 機器枚舉（2 處命中、逐處處置）。
- **B-113 探針前提如預期消失**：`updateUserSessionPolicy` 註冊後進候選集 ⇒ `outside_protected` 實際降為 **0**
  （現僅印在訊息裡、非 assert，故續綠）。★**T068 種合成候選外 protected 探針列之前，不可把該數升成真 assert。**
- **本單元新帳**：B-142（no-escalation 判定的三處重複查詢面、收攏屬拍板級）。

- [X] T061 [US5] `base-web/src/views/manage/user/modules/user-unlock-modal.vue` 新檔（雙維下拉＋條件輸入、顯式帶 `dimension`）
  ＋**新增** `fetchUnlockLogin` 至 `base-web/src/service/api/rev5-user-admin.ts`＋`Api.UserAdmin.UnlockReq` 至
  `base-web/src/typings/api/rev5-user-admin.d.ts`＋`index.vue` 頁首鈕接線（`user:unlock` gating）。
  ★★**落字勘誤（本刀 U7 實暴）**：原文寫「打**既有** `fetchUnlockLogin`」——「既有」指的是
  **後端端點**（`POST /systemManage/unlockLogin`，004 建、見 contracts §「既有 …（004；本刀接 UI＋帳號維套規則）」），
  **不是前端 fetcher**。前端側該 fetcher 與其請求型在本 task 之前**全樹零命中**、由本 task 新建。
  歸屬依契約檔頭逐字：本族 wire 型的家＝`Api.UserAdmin`（`rev5-user-admin.d.ts`／fetcher `rev5-user-admin.ts`），
  且該契約標題即「使用者管理十支端點（**＋unlockLogin UI 接線**）」⇒ ★**不得**塞進 `rev5-user-center.*`
  （那支檔頭逐字寫「兩支端點皆 `Protection::Authed`」，而 unlockLogin 是 `Protection::Policy`／super-only 的
  `/systemManage/*` 端點），亦**不得**在 `.vue` 內直接 `import { request }`（全樹零先例、破分層）。
- [X] T062 [US5] **★射程已縮為確認輪**（本刀 U6 已隨 T030／T031 原文一併交付）：`userMemo` 列表純文字欄
  （零原始 HTML 插值、`view-render-guard` 綠）＋抽屜 textarea（B-003 最後一張表）＋兩語 i18n 鍵
  （`userMemo`／`form.userMemo`）皆已落地。⇒ 本 task 只需**對賬確認**並為 B-003 最後一張表關帳，**勿重覆施工**。
  ★成因＝T030 原文逐字含「記事」欄、T031 原文逐字含「memo textarea」，且 U6 自驗要求 `view-render-guard` 綠
  （該守門的標的正是記事欄的純文字插值）⇒ 結構上不可能只做一半。

**Checkpoint**: US5 可獨立驗收——七枚按鈕碼與 seed 68 全數取得消費者。

---

## Phase 8: User Story 6 — 登入頁規則放寬與順路修復（P3）

**Goal**: B-089 結案（登入頁降 required-only）＋順路三條（B-129／B-132／B-128 ①②）。

**Independent Test**: quickstart §3 末（含特殊字元密碼登入）＋§6-5；role 頁換角色 modal 無殘影；menu 頁回收桶每頁 10。

★**U7 執行結果（首支 `wf_866e1f35-c3f` 3 支＋補跑 `wf_15c96e8a-2fc` 9 支、2026-08-29 收尾）**

- **量**：前端十二檔（含六支新檔）。`pnpm typecheck` rc=0｜`pnpm lint` **0 errors**（唯一 warning 在未受改的
  `user-detail/[id].vue`、屬既有）｜改動 `.ts` 逐檔 `oxlint` 0 warning／0 error｜`fork-delta-lint` 綠（授權判定 136→**141** 處）｜
  `view-render-guard` 綠（受掃 18→**19** 檔）｜`docs-sync lint` 0 錯誤｜**wire-schema 86→89**（+3：`Api.UserAdmin.UnlockReq`／
  `Api.UserCenter.ChangePasswordReq`／`Api.UserCenter.PasswordPolicyView`）。i18n 兩語各 **697 葉鍵**、對稱差集皆空。
  `scroll-x` 1932→**2002**（operate 欄 130→200 同批改）。
- **審查**：補跑的**規格符合性輪第 0 輪即零 blocker**；碼品質輪跑滿三輪 fix＋確認輪，餘 2 筆由主線接手。
- ★★**首支為何 3 支就停：fix agent 回 `blocked`，而它是對的**。T061 的 `fetchUnlockLogin` 與 `UnlockReq`
  唯一合法的家是 U6 建的 `service/api/rev5-user-admin.ts`／`typings/api/rev5-user-admin.d.ts`，而**我方 prompt 的
  允許清單漏列了那兩支**。agent 逐條驗證後駁回三條繞道：塞 `rev5-user-center.*`（違該檔頭「兩支端點皆 `Authed`」，
  而 unlockLogin 是 `Protection::Policy`／super-only）／`.vue` 內直呼 `request`（全樹零先例）／只做 gating 不接 API
  （點了沒反應的鈕＋七枚孤兒 i18n 鍵，比不做更糟）。★**空間邊界該擋住的是越界，不是把人逼去繞道**——這次兩件都做到。
- ★**它同時揭穿任務書的事實錯誤**：T061 原文「打**既有** `fetchUnlockLogin`」——「既有」指的是**後端端點**（004 建），
  前端該 fetcher 全樹零命中。已勘誤 T061 並寫明歸屬依據與兩條禁止路徑。
- ★★**契約落字勘誤（本輪最有價值的一筆、靜默錯）**：`contracts/wire-user-admin.md` 末節把來源維標的欄寫成
  `ip?: string`，**而該節自陳「既有契約不變」**——既有契約（`specs/004-ip-trust-anchor/contracts/wire-throttle-unlock.md`）
  的欄名是 `target`，後端 DTO `UnlockLoginReq` 亦為 `target`＋camelCase，rev4 前端同族型同。
  ★**照 `ip` 落地會是靜默錯**：請求形制合法、後端只看到「來源維標的缺席」⇒ 恆回 `2222`，畫面上像是「這個 IP 沒被鎖」
  而非「你送錯欄名」。implementer 取 `target`（正確側）並在型 doc 就地記載；主線已於契約補勘誤註。
- **主線於單元邊界的處置三則**：
  ①**`pwd-gen-modal.vue` 的 `defineModel` 具名 `show` → `visible`**（含兩處掛載點共 4 行）：全庫既有六支開關型
  `defineModel` 全數具名 `visible`，連同單元交付的 `user-unlock-modal.vue` 也是——★兩支新檔自己就不同形。
  危害在可讀性與擴散：寫錯不會 typecheck 紅（多餘的 `v-model:visible` 只是綁到不存在的 model 上、**浮層永不開啟且無錯誤訊息**）。
  ②**`user-operate-drawer.vue` 的 self 不變式補到送出面**：`statusChanged`／`rolesChanged` 各補 `!selfFieldsLocked.value &&`，
  與同函式的 `sessionPolicyChanged`（已有 `isSuper.value &&`）同形。★**同一函式自己立的原則只套用了一半**——
  那段註解逐字寫著「把不變式只寫在一個 `:disabled` 上，等於讓一個顯示屬性當唯一防線」，卻只對 sessionPolicy 兌現。
  現況不可達（回填值＋disabled ⇒ diff 恆 false），修的是守門的耐久性。
  ③**契約 `ip` → `target` 勘誤**（見上；依 §4 用 `errata` 枚舉、1 處命中）。
- **B-144 第三度復發**：`pnpm lint`（含 `--fix`）再次改寫清單外的 `views/manage/ip-rule/index.vue`（6 行註解排版）。
  ★主線判定**還原**而非順手吃掉——U7 的 diff 已夠複雜，混入無關檔會讓復核更難；清償留給「動得到該檔的刀」（B-144 候選處置①）。
  ★另註：`typings/components.d.ts` 的 diff 是 unplugin-vue-components 由 dev 容器自動重算的**生成物**，手動還原會被立刻改回，屬預期改動。
- **主線追認兩則工程自決**（皆已於 `contracts/msg-keys.md` 落 as-built 註）：`page.userCenter.title` **刻意未設**
  （頁標題已由既有 `route['user-center']` 承載，另立同義鍵＝零消費者＋第二份說法）／`passwordHint` 落
  `page.manage.user.*` **直屬層**（依契約列序，它是 `pwdGen.{...}` 的同級兄弟）。
- ★**(vi) 用途變異自證已完成**（首支）：REAL_RC=1、2 筆「檔 `src/views/user-center/index.vue` 不在 ★軌道
  `BASE-WEB-MANAGE-PAGE-WIRING(vi)` 授權檔案集」，還原後 `diff -q` 逐位相同、RESTORED_RC=0。
  ⇒ **(v)（U6）與 (vi)（U7）皆已補做**；餘 `LOGIN-CAPTCHA-WIRING(ii)` 屬 U8 之 T065。
- **T062 對賬確認屬實**（未重覆施工）：`userMemo` 列表欄走預設純文字渲染、抽屜 textarea、兩語 `userMemo`／`form.userMemo` 皆在。
  ⇒ **B-003 最後一張表可於收刀關帳**。
- **未竟**：碼品質輪確認輪兩筆由主線修完後未再跑一輪（同 U3～U6 之形）⇒ 併入收刀前的 final holistic review。

- [X] T063 [P] [US6] `base-web/src/views/manage/role/modules/{menu-auth-modal.vue,button-auth-modal.vue,endpoint-auth-modal.vue}`
  （(iii) 補完、免 bump）：`getChecks()` 起手清 `rawChecks`／`protectedIds`＋`getHome()` 請求世代（B-129）；★排在 US1 抽屜照抄範式之前
  （實際執行序見 Dependencies）。
- [X] T064 [P] [US6] `base-web/src/views/manage/menu/index.vue`（(ii) 補完、帶 `原行:`）：切回收桶模式時重置 `pagination.pageSize`
  （B-132 修法①；★只動 menu 頁、不動 `hooks/common/table.ts`）。
- [X] T065 [US6] `base-web/src/views/_builtin/login/modules/pwd-login.vue`（修改型 (vii)、逐行 `原行:`）：`formRules` 之 pwd／userName
  改 `createRequiredRule`；★不動 `src/constants/reg.ts`；register／reset-pwd stub 不動。
- [X] T066 [P] [US6] `docs/ops/RUNBOOK.md`：前端驗證指令分工一段（.vue 走 `pnpm lint`／`.ts` 走 `pnpm exec oxlint <file>`；
  ★`eslint` 對 `src/**/*.ts` 零覆蓋、`--max-warnings=0` 之 rc=1 為假紅）＋本刀編排 script 前端驗證段照此（B-128 ①②）。

**Checkpoint**: US6 可獨立驗收——設得進的密碼登得進；三條順路缺陷關帳。

---

## Phase 9: Polish & Cross-Cutting（DoD 收攏）

★**U8 執行結果（★主線親做、無 workflow、2026-08-29）**

- **軌別自決（回報備查）**：三條 task 合計改動 < 30 行＋一段 RUNBOOK，開 workflow 至少 3 支 agent、
  跑數十分鐘，編排成本大於收益 ⇒ 主線親做（global CLAUDE.md §9「default to doing the work yourself」）。
- **T064（menu 頁 pageSize 歸位、B-132 修法①）**：`watch(showDeleted, ...)` 內先判等再賦值＋早退。
  ★**早退是必要的、不是優化**：`pagination` 的 `{page, pageSize}` 由 hook 的 `paginationParams` watch 監聽，
  同 tick 把兩值一起改只會合併觸發**一次**重取；若照原樣再呼一次 `getDataByPage(1)`，當 `page` 已是 1 時
  它會直接 `getData()`，與 watch 那次疊成**同一次切換發兩個請求**，而且第一個還帶著舊的 `size=100`。
  值未變的路徑（自回收桶切回治理清單）仍由 `getDataByPage(1)` 補一次重取。★只動本頁、未動 `hooks/common/table.ts`。
  ★歸位值寫成具名常數 `MENU_DEFAULT_PAGE_SIZE`（＝hook 預設 `pageSize: 10`＝`pageSizes` 首項）而非裸 10——
  它與 hook 預設是同一個約定，裸數字讀不出這層相依。
- **T065（登入表單降 required-only、`LOGIN-CAPTCHA-WIRING(ii)`）**：`formRules.userName`／`formRules.pwd`
  （皆為 `[required, patternRules.*]`）改為只取 `createRequiredRule`。★論證逐字入碼註：**設得進的密碼必須登得進**
  ——本刀讓三入口共用後端的密碼政策單一驗證點（島 I5）、政策鍵可由超管運行期調整；前端若還按一組寫死的正則擋人，
  就會出現「密碼照政策設好了、登入頁卻說格式不對」的死路。`src/constants/reg.ts` 未動、兩支 stub 未動、
  用途 (i) 的 captcha 軟區條件渲染零變更。
  ★**踩到一個標記形制坑**：`原行:` 必須與 `[rev5-inline …]` 在**同一行**——把說明寫成多行、`原行:` 落在續行時，
  `fork-delta-lint` 逐字報「缺 [rev5-inline token——裸 `原行:` 不構成合法修改型標記」。改為「多行說明在上、
  最後一行為完整單行標記＋`；原行: …`」後綠（授權判定 141→**144** 處）。
- **T066（RUNBOOK §9b 前端驗證指令分工、B-128 ①②）**：四件各有其職的表（typecheck／`.vue` 走 `pnpm lint`／
  `.ts` 走 `oxlint`／標記與渲染閘）＋兩條★注意事項：①`eslint` 對 `src/**/*.ts` **零覆蓋**、`--max-warnings=0`
  之 rc=1 是**假紅**②`pnpm lint` 內含 `--fix`，會就地改寫「本來就不 lint-clean 的既有檔」（B-144），
  跑完必須檢查 `git status` 並把清單外的檔存原文→寫回還原。B-128 ② 面（編排 script 照此）已於 U6／U7／U8 三支兌現。
- ★★**`LOGIN-CAPTCHA-WIRING(ii)` 的變異自證（L-063 的第三處、也是最後一處）**：改壞憲法 §III.2 之 (ii) 列範圍欄
  → `fork-delta-lint` 逐字紅 **3 筆**「檔 `src/views/_builtin/login/modules/pwd-login.vue` 不在 ★軌道
  `BASE-WEB-LOGIN-CAPTCHA-WIRING(ii)` 授權檔案集」；還原（存原文→寫回、非 `git checkout`）後 md5 逐位相同
  （`8b0c7bdc…`）、`git status` 零殘留、重跑 rc=0。
  ⇒ **(v)（U6）／(vi)（U7）／(ii)（U8）三個新用途的變異自證全部補做完畢，L-063 清償。**
- **B-144 第四度復發**：`pnpm lint` 又改寫 `views/manage/ip-rule/index.vue`，已還原（同 U7 判定）。
  ★該筆的處置紀律現已成文於 RUNBOOK §9b。
- **驗證**：`pnpm typecheck` rc=0｜`pnpm lint` **0 errors**（唯一 warning 在未受改的 `user-detail/[id].vue`、屬既有）｜
  `fork-delta-lint` 綠（**144** 處）｜`view-render-guard` 綠（19 檔）｜`wire-schema check` byte 一致（89）｜
  `docs-sync lint` 0 錯誤。零 rust 改動。

- [X] T067 `rust-api/server/tests/wire_schema.rs`＋`rust-api/server/tests/fixtures/wire-schema.json`：跨子庫兩段式重抽
  （base-web 型 commit→容器內 `python3 tools/wire-schema.py extract`→fixtures commit→外層 pin）＋`Api.UserAdmin.*`／
  `Api.UserCenter.*` 每 definition 裁判（正向≥1／反例≥1；`status` 二值、`roles` 陣列、可空欄 null 形為重點）＋
  `python3 tools/wire-schema.py check` 綠；definitions 自 75 淨增（補記實數）；★`Api.IpRule.*` 七支不補（B-098 留帳句不動）。
  ★★**排程勘誤（本刀 U6 實暴）**：本 task 原設想「重抽留到 Polish 期一次做」，但 **`wire-schema` 是 pre-commit 閘**——
  任何新增 `typings/api/**` 的單元，其**外層 commit 當場就會被擋**（訊息：「快照與 typings 重抽不一致」）。
  ⇒ 重抽**不是**可延後的收尾動作，而是「新增 wire 型的單元邊界必辦」。U6 已中途重抽一次：
  **75→86**（+11 個 `Api.UserAdmin.*`、零移除），rust-api 快照與 pin 隨該單元同批 bump。
  ⇒ 本 task 的殘餘射程＝**U7 之後的最後一次重抽**（吸收 `Api.UserCenter.*`）＋**每 definition 的裁判腿**
  （正向≥1／反例≥1）＋終值補記；重抽本身屆時多半已是 no-op。
- [X] T068 `rust-api/server/src/handler/role.rs`：B-113 處置——種合成候選外 protected 探針列（非 seed、`CasbinCleanup` 兜底）、
  把 `outside_protected≥1` 自 assert 訊息升為真 assert；★該測續綠非轉紅（T002⑥ 佐證）；BACKLOG 條文更正隨 T073。
- [X] T069 全量閘：容器 serial 全量 `cargo test` rc=0（基線 829、淨增補記實數）＋`docs-sync.py lint` 0 錯誤＋`schema-gate.py check` 三閘綠
  ＋`entity-drift-gate.py check`＋`fork-delta-lint.py`（修改型僅「三用途 ∪ 順路補完」8 支既有檔；`components.d.ts`／`service/api/index.ts` `git diff` 零輸出斷言）
  ＋`route-artifact-gate.py check`（零重算）＋`view-render-guard.py check`＋`seed-view-gate.py check`＋`rust-fmt-gate.py check`
  ＋`pnpm typecheck` 綠＋★**五**名冊閘綠（`RELOAD_CALL_FILES` 實得序／`ENFORCER_WRITE_FILES`／本刀新增三張：`FINISH_USER_WRITE_CONSUMER_FILES`〔U4，L-069〕／`NO_ESCALATION_CALL_FILES`＋`GUARD_NO_ESCALATION_CONSUMER_FILES`〔U5〕——原文「三」係開刀時的量、本刀期間增為五）。
★**U9A 執行結果（workflow `wf_af40b2e5-4bb`、9 支、2026-08-30 收尾；T067＋T068，T069 主線續跑）**

- ★★**本刀第一次兩輪審查都自行收斂**：規格符合性輪**第 0 輪零 blocker**、碼品質輪跑到**確認輪亦零 blocker**
  （`ok: true`、零 escalation）。前六個單元的確認輪都還有 blocker 由主線接手。
- **量**：rust 測試 969→**998**（+29＝新增裁判腿數，逐位吻合）；`wire_schema` 套件 100 passed。
  改動面僅兩檔（`tests/wire_schema.rs` +1252／`handler/role.rs` +80）；**base-web 零改動**、
  `wire-schema.json` **零 diff**（未被手改、`check` byte 一致 89）。
- **T067 殘餘（裁判腿）**：本刀十四個新 definition（`Api.UserAdmin.*` 十二含 `UnlockReq`／`Api.UserCenter.*` 二）
  各補正向≥1＋反例≥1，共 29 支 `#[test]`（正向 15／反例 14）。三重點欄全覆蓋：`status` 二值（`"3"`／`"0"`／`null` 三形）、
  `roles` 陣列**型與元素型兩層**、可空欄 `null` 形**三種分岔各自釘死**（`UserRecord` 省略即紅／`UpdateReq` 三態
  `["null","string"]`／`AddReq.nickName` 不可空）。
  ★審查員以 **Python `Draft7Validator`（獨立於 rust `jsonschema` crate 的第二套實作）** 重跑全部正向與反例實例覆核，
  零裝飾性反例——這是本輪最紮實的一筆驗證。
- **T068（B-113 探針升真 assert）**：確為「**先種**合成探針列 → **再**升真 assert」。
  探針＝`/systemManage/__t068ProbeOutsideCandidates`（非 seed、DB default `nextval`、`v0='R_SUPER'`），
  由既有 `CasbinCleanup::new(&["R_SUPER"])` 的 `(v0=$1 OR v1=$1) AND id > 163` 腿刮掉、seq 由其 `setval(…,163,true)` 腿收回
  ⇒ **零新守衛、零 seed 變更**。★**該測續綠非轉紅**（原文逐字要求）。
  ★審查員以**凍結 seed × `router.rs` 的 `Protection::Policy` 獨立重算**驗證該 assert 非恆真：
  ROUTES 61／Policy 45／R_SUPER 端點列 50／候選內 45／**候選外恰 5 列**＝五支稽核端點，`protected` 皆 FALSE
  ⇒ seed 側 `outside_protected` 為 0，`>= 1` 完全靠自種探針供給，拿掉 `seed_live_policy` 該測必紅。
  實測殘列：`casbin_rule` 探針列 **0**、`max(id)=163`／`count=163`／`casbin_rule_id_seq.last_value=163`。
- **主線於單元邊界的處置兩則**（皆為碼品質輪列為「非阻擋性觀察」者，主線判定順手做掉）：
  ①**`user_admin_list_res_page_res_matches_snapshot` 的 `items_required.len() == 14` 改為名集恰等**
  （十四欄逐字），形沿同檔 `Api.RoleAdmin.RoleEndpointGrantRes` 的 `["method","path"]` 先例、合 ADR 0024 要求②
  「結構斷言優先於數量斷言」。★理由：數量斷言擋不住「刪一欄又補一欄」的**補償式改動**，而那正是 wire 契約最該釘住的一格。
  變異紅證：期望陣列內 `userPhone`→`userPhoneX` → 逐欄印出 left／right 而紅；還原後零殘留。
  ②**檔頭「★上一行的 75」指涉訂正**（該 75 實際在 29 行之上、非緊鄰上一行）。
- ★**主線自我更正（過程留痕）**：上述變異紅證我前兩次都得到「沒紅」，一度誤判為 CLAUDE.md §11 的 drvfs 假綠。
  實際上**兩次都是我自己的操作錯**——第一次 `replace(..., 1)` 命中了檔內**另一處**同字面（`USER_RECORD_DEF` 的
  十四欄名集、位在 2672 行），第二次沿用了錯的測試 filter（`user_admin_list_res_page` 不涵蓋那支）。
  改以行號精確定位＋對應 filter 後當場紅。★**教訓**：變異測試的「沒紅」有兩種成因——守門真的 vacuous，
  或**變異根本沒打到被守的那一格**；先自證「我改的確實是那一行、跑的確實是那支測」，再談守門有效性。
- **T069 全量閘（主線續跑、同批完成）**：容器內 serial 全量 `cargo test` rc=0（**998**）＋九支閘全綠
  （`docs-sync lint` 0 錯誤／`schema-gate` 四綠／`entity-drift` 零漂移／`route-artifact` 重算冪等／`view-render-guard` 19 檔／
  `seed-view-gate` 51 鍵／`rust-fmt-gate`／`wire-schema` byte 一致 89／`fork-delta-lint` rc=0）＋`pnpm typecheck` rc=0
  ＋★**五支名冊閘全綠**（原文寫「三」＝開刀時的量；本刀期間增為五，已改述該 task）
  ＋`components.d.ts`／`service/api/index.ts` **零 diff 斷言成立**＋修改型恰 **8 支既有檔**（與原文吻合）。

- [ ] T070 CDP 三方對照（quickstart §6 全動線七步；★排 schema-gate 之後）：Super 全套／Admin 預設態（只見編輯鈕）／下放後（六鈕出現、
  同級成功、對 Super 5003）／踢除 7777 新文案／停用 8888／個人中心改密卡動態規則／登入頁特殊字元密碼直送／rev4 42080 逐項對照；
  已知態排除清單逐項驗現狀形；走查後清殘列＋`sys_user_id_seq` 還原＋三閘複驗；差異逐項判定（rev5 拍板差異 or 缺陷）補記本 task。
★**T070 CDP 走查結果（主線、2026-08-30；★七步中已驗六步、兩步留待收刀前補）**

**已驗（逐項實測）**
- **步驟 1 Super 全套**：列表 **15 欄**（序号／用户名／性别／昵称／手机号／邮箱／用户状态／**角色**／**会话策略**／
  **备注**／**创建时间／创建者／更新时间／更新者**／操作）＝FR-035 齊備；抽屜新增九欄含 **`随机密码` 鈕**與
  hint「密码规则由服务端校验；可点右侧按钮按当前策略随机生成」；產密浮層「随机生成密码 长度 重新生成 复制 带入」；
  編輯抽屜 **userName disabled**；★**操作下拉**：Admin 列＝`踢除下线／重置密码／随机密码` 三項，
  **Super 列（self）只有 `踢除下线`** ⇒ **T056 的 self 五不在真 UI 上成立**（管理端不可重設自己密碼、走個人中心）；
  頁首**解鎖 modal 雙維**「锁定维度 * 账号 用户名 * 请输入」；回收桶 toggle **隱搜尋卡**、
  欄集與現役同（**無刪除時間欄**＝R2#28 rev5 拍板差異）。
- **步驟 2 Admin 預設態**：頁首只剩「刷新 列设置」（新增／批量删除／解锁登录 **全不見**）、
  列操作欄**只有「编辑」** ⇒ 與 seed 實況吻合（`casbin_rule` 查得 R_ADMIN 按鈕碼**只有 `user:edit`**）。
  ★**七枚逐鈕 gating 在真 UI 上成立**。
- **步驟 5 個人中心＋登入頁**：`/user-center` 為真頁、**只掛改密卡**（三卡位留白）、**只舊密碼一路**
  （旧密码／新密码／确认新密码，**無信箱／手機 radio**）；hint「密码规则由系统设置决定、以服务端校验为准；
  修改成功后本设备保持登录，其他设备需重新登录」；★**動態規則跟政策**——填 `ab` 得「**长度未达策略下限**」；
  ★**登入頁輸入含特殊字元密碼零前端格式紅字**（`n-form-item-feedback__line` 空集）⇒ **T065 的 required-only 兌現**。
- **步驟 6 rev4 42080 逐項對照**（差異全部落在 quickstart 明列的預期內）：

  | 面 | rev4 | rev5 | 判定 |
  |---|---|---|---|
  | 語言 | 繁體 | 簡體 | ★預期差異（quickstart 逐字「兩語」） |
  | 列表欄 | **8 欄** | **15 欄**（多角色／會話政策／備註／四審計欄） | rev5 更完整（FR-035） |
  | 頁首鈕／列操作 | 新增／批次刪除／解鎖登入／…；編輯｜刪除｜操作 | 同（簡體） | 一致 |
  | 個人中心 | 改密卡＋**隨機密碼**＋**信箱驗證碼／手機驗證碼**兩路＋**信箱卡**＋**手機號碼卡** | **只改密卡、只舊密碼一路** | ★預期差異（FR-037 三卡留白、無 radio） |

- **步驟 7 走查後複驗**：★**本輪零寫庫** ⇒ `sys_user` 3 列／`max(id)=3`／`sys_user_id_seq.last_value=3`／
  `casbin_rule` 163 列，與走查前逐值相同、零殘列、無須清理。

**未走（誠實記載，留待收刀前補）**
- **步驟 3（授權下放後：六鈕出現／同級成功／對 Super 5003）** 與 **步驟 4（alice 雙開：踢除 7777 新文案／停用 8888）**
  ——兩者皆為**寫庫動線**（插 `casbin_rule` 授權列／建帳號／踢除），走查後須清殘列＋`sys_user_id_seq` 還原＋三閘複驗。
  ★**未走的理由不是難度而是排程**：本輪 context 需讓位給壓縮，而這兩步的後端行為已由 998 支測釘死
  （含 U3 抓出的 `refresh` 之 `admin_kick` 分支真缺陷），前端 gating 亦已由**步驟 2 的預設態反證**
  （只見編輯 ⇒ gating 確實生效，授權後鈕出現是同一機制的另一側）。
  ⇒ 併入**收刀前的 final holistic review**，與 U3～U8 的確認輪缺口同批處理。

**★主線自我更正（過程留痕、與 U9A 那筆同族）**
- 步驟 2 首跑得到「Admin 看到全部鈕」，一度看似 gating 缺陷。實為**我的測試 bug**：
  CDP helper 的 `clickByText` 用 `includes`，而登入頁的「**超级管理员**」含子字串「**管理员**」且排在前面
  ⇒ `find` 命中超管，整段「Admin 預設態」其實是用 Super 驗的。改為精確比對（`trim() === text`）後當場正確。
  ★教訓同 U9A：**先自證「我操作的確實是那個對象」，再談被測物有沒有問題**——否則會把自己的手滑記成產品缺陷。
- 另兩則 CDP 驅動坑（已寫進 helper 註解）：①naive-ui 的 dropdown 需**真實滑鼠事件**（`Input.dispatchMouseEvent`），
  `element.click()` 不觸發②關閉下拉用 **ESC**，點空白處 (5,5) 會落在側欄 logo 上而導航走掉
  ③操作欄在 `scroll-x=2002` 的橫向捲動區外（座標 x=2211 超出視窗）⇒ 須先
  `Emulation.setDeviceMetricsOverride` 放大 viewport 或 `scrollIntoView({inline:'end'})`。

- [x] T071 ★主線任務：ADR ②～⑤ draft→accepted——`0064`（BizData 明細通道：射程二鍵、澄清 ADR 0022 §2② 之誤、結 B-024③ 受眾邊界）／
  `0065`（`SELF_SERVICE_ROUTES` 碼內白名單，承 rev4:ADR 0065、紀律嚴限自助頁家族）／`0066`（設密冷卻＋改密節流：custody 只時戳、
  fail-open 同島 E、常數門檻、觀測 source）／`0067`（ADR 0042 第 2 項措辭訂正＝解鎖入口為使用者管理頁，走 v1.6.1 對 0043 範式；
  ＋ADR 0053 觸發矩陣補一列＝user 指派寫端）；各 `provenance` 指向 brainstorm／spec 條號；`docs-sync.py generate`。
- [x] T072 ★主線任務：活書 `docs/arc42/ARCHITECTURE.md` §5（facade 新兩檔與寫端家族、test_db 名冊三守衛——落筆先算餘裕 20 行）＋
  §6（斷權四路與 reason 分派、密碼三入口與冷卻節流序——餘裕 40）＋§8（授權慣例加 no-escalation 包含規則與掛點分工、
  按鈕 gating 判準——餘裕 77）＋§12 詞彙六條（停用／軟刪／踢除／撤銷／鎖定／重設 vs 修改密碼）＋
  `docs/arc42/FORK-DELTA-WIRING.md`（(v)(vi)(vii) 三用途接線 as-built）；撞頂即依 ADR 0062 輕量軌下放（不再逐次 ADR）。
- [x] T073 ★主線任務：`docs/ops/BACKLOG.md` 關帳與勘誤——刪 B-003／B-021／B-024／B-089／B-093／B-113／B-127／B-129／B-128／B-132
  （B-020 視通用 seam 是否做、B-025 只結①留②、B-098 續留）＋`docs/ops/LESSONS.md`（若有踩坑）＋勘誤四處：
  `docs/ops/NOTES.md`「seed 68（manage_user view）」→「seed 68（updateUserSessionPolicy 端點）」、
  `handler/common.rs` 檔頭與 NOTES「六件」→七件、B-113 條文「由綠轉紅」→續綠、ADR 0022 §2② 由編號 0064 之新 ADR 一句澄清；
  ★`docs-sync.py errata <關鍵詞>` 逐處處置（禁只修被點名處）。
★**T071～T073 as-built（主線、2026-08-30）**

- **T071**：ADR 0064～0067 四支 draft→accepted 一次落地（body 皆零碼改動、記的是 as-built 與判準）。
  ①`0064` BizData 明細通道——★查證出 ADR 0022 決定 2 理由②「`AppError` 已有 `BizData` 變體形」是**事實誤述**
  （同期 `error.rs` 碼註逐字「B12 不建 rev4:B-047 之 BizData 攜參形」，該變體到本刀 U1／`7575379` 才進場）；
  受眾邊界判準立為「明細是**操作者自陳輸入**的評估結果 vs. **系統的**狀態或模型」，B-024③ 據此結掉。
  ②`0065` 自助路由白名單——★rev5 **沒有** rev4 那條 §III.2(g) 頁級豁免條文，改以二支柱立論（§I.2 含義射程
  限「業務 menu」＋`sys_menu` id 16 之 `hide_in_menu = TRUE` 實值）。③`0066` 冷卻與節流——結掉 B-021 兩個殘餘
  拍板點（fail-open／碼內常數），判準＝「這個數字的正確值是否隨組織而異」；B-020 通用化半邊判 won't-fix。
  ④`0067` 兩款訂正——ADR 0042 第 2 項的入口歸屬預測（實落使用者管理頁、可見落差同批解除）＋ADR 0053 款四
  觸發矩陣擴 user 域，★**補的是兩列不是一列**（本檔原文「補一列」為預估失準：as-built 觸發源恰二＝
  `updateUser` 角色集實際變更／`deleteUser`＋`batchDeleteUser` 之 `had_roles`）。
- **T072**：§5（user 域拓樸五支新檔＋facade 12→13＋test_db 三守衛）／§6（denylist 三 reason 分派、兩套詞彙、
  撤銷交易邊界、密碼三入口守門序）／§8（no-escalation 兩射程、前端不預判、gating 判準、名冊閘射程紀律）／
  §12（業務詞彙四組六條）＋`FORK-DELTA-WIRING.md`（(v)(vi) 與 LOGIN-CAPTCHA (ii) 三用途 as-built＋
  `原行:` 同行形制紀律）。★**射程外順手修五處現在式失準**（活書的現在式義務、非擴 scope）：
  §1 建置狀態停在 004（★005／006 **連兩刀遺漏**⇒ 根因立帳 B-146）、觀測 source 十二→十三、
  denylist reason 兩常數→三、`session_event` 四事件→五、reload 名冊三檔→四檔。各節行數
  §1 18/40｜§5 85/90｜§6 148/160｜§8 73/130｜§12 21/30，全在配額內。
- **T073**：關帳**十一條**（本檔原列十條＋B-020——其通用化半邊由 ADR 0066 決定四判 won't-fix，翻案觸發器＝
  出現第三個消費者且與既有兩者之一同形）；B-025 只結①（★自證：`sys_user_role::delete_all_of_user` 硬刪與
  `deleted_at` 同交易同 advisory 域、全程零 casbin 歸檔列 ⇒ 窗結構性不存在）、②事後對賬掃描續留；B-098 續留。
  ★**十一條逐條自證前提**（不採信本檔記載）：B-003 兩面各有 `userMemo`／B-089 三行 required-only 且
  `constants/reg.ts` 零 diff／B-113 探針升真 assert／B-127 收攏至 `handler/common.rs`／B-128 RUNBOOK §9b 分工表／
  B-129 三檔皆有 `B-129①` 清空腿＋`homeReq` 世代／B-132 `MENU_DEFAULT_PAGE_SIZE` 重置。
  勘誤逐處處置：①NOTES「seed 68（manage_user view）」→已改為端點名（★同述另在 `events.jsonl` 行 33，
  append-only 不可改＝ADR 0012 決定 5；其餘三處命中皆為**勘誤指令本身**、改掉即失去指涉，保留）
  ②「六件→七件」**本檔失準**——`handler/common.rs` 檔頭現為**八件**（B-108 第七、本刀 T017 第八）、碼側早已正確，
  處置改為在 NOTES 該句就地加註現況 ③「由綠轉紅」隨 B-113 關帳自然消解（errata 現存二處皆為勘誤指令本身）
  ④ADR 0022 決定 2② 之澄清＝ADR 0064 背景段。

- [x] T074 `docs/ops/RUNBOOK.md` §12.1 量測法實測 pre-commit 一筆（低於 ADR 0044 之 45s 警戒；hook 自報值與逐支中位數法不可混用）＋
  結論補記本 task；收刀簿記（events `feature_close`＋NOTES＋generate）由收刀程序承接、不列 push／merge。

---

## Dependencies & Execution Order

- **Phase 序**：Setup（T001～T005）→ Foundational（T006～T021）→ US1（T022～T032）→ US2（T033～T039）→ US3（T040～T051）→
  US4（T052～T057）→ US5（T058～T062）→ US6（T063～T066）→ Polish（T067～T074）。
- **硬閘**：T003 accepted 前凍結一切 base-web 既有檔（T030／T031／T032／T050 之 `user-center/index.vue`／T055／T056／T057／
  T062／T064／T065；backend 樹增鍵與純新增檔不受此閘）。
- **US 依賴**：US2 之 T037 依賴 US1 之 T026（`finish_user_write` 骨架）；US3 之 T045 依賴 T025（facade 寫端）與 T006／T010；
  US4 之 T054 依賴 T011（純函式）與 T026（掛點位）；US5 之 T060 依賴 T025；US6 之 T063 **建議排在 T031 之前**（先修再照抄範式、
  Q36）——實際執行序＝T063 提前至 US1 前端單元之首。
- **ROUTES_COUNT 遞增鏈**：49→56（T027、七支管理端點）→57（T037、kick）→58（T046、reset-password）→60（T047、
  user-center 兩支）→61（T060、session-policy）；每段同 commit bump＋contract case＋generate routes。
- **執行單元映射**（編排每單元一支 workflow；research R12 定稿）：U0＝T001～T005（主線、user 親決）｜U1＝T006～T021（後端底座）｜
  U2＝T022～T028（US1 後端）｜U3＝T033～T039（US2）｜U4＝T040～T048（US3 後端、含自助白名單）｜U5＝T052～T055＋T058～T060（US4／US5 後端）｜
  U6＝T063＋T029～T032（US1 前端、B-129 先修）｜U7＝T049～T051＋T056／T057／T061／T062（US3／US4／US5 前端）｜
★**T074 as-built（主線、2026-08-30）**：兩個量測面各實測一筆，值與判讀全文落 RUNBOOK §12.1 資料點序列。
①**牆鐘**（真 commit、`perf_counter` 包 `git commit` 整命令、單次）＝**13.89s rc=0**（U10 治理收尾
commit `b5b6912`，零 gitlink／零工具本體）——對照同型的 2026-08-18 文件型 26.10s，**B-130 提速在真實
commit 面兌現（−47%）**，距警戒 45s 餘 3.2 倍。②**逐支中位數**（情境 A 基礎鏈、乾淨環境、每支 3 跑）＝
0.138／1.153／13.326 ⇒ **合計 14.617s**；對照 2026-08-18 同法之 13.695s 為 +6.7%，而其間掃描面多了
005／006／007 三刀的全部產出 ⇒ 成長被 B-130 的 I/O 稅處置吸收。★兩值**不可混算**（不同量測面）。
★**誠實界線兩則**：①這兩筆**都不是收刀簿記型**，ADR 0044 引信所指的本刀資料點須於收刀簿記那顆補記
（引信「連續兩刀 ≥60s」以現值判未觸發）②RUNBOOK 既有「下一刀必做」第②項（pin bump 型牆鐘實測）
**本刀仍未做**——U1～U9 各有一顆 pin bump commit 而當時未計時（執行疏漏）、U10 零 gitlink 改動故無機會，
已續掛至收刀的 `merge --no-ff` 那顆（它 staged 兩個 gitlink＝該項要的最重情境）。

  U8＝T064～T066（US6）｜U9＝T067～T070（重抽與全量閘與 CDP）｜U10＝T071～T074（治理收尾）。
- **共享檔序列鏈（同檔不 [P]）**：`facade/sys_user.rs`（T015→T022→T025→T045→T060）、`facade/sys_user_role.rs`（T016→T025）、
  `handler/user.rs`（T018→T023→T026→T028→T033→T037→T040→T046→T052→T054→T058→T060）、
  `router.rs`＋`tests/contract.rs`（T024→T027→T036→T037→T044→T047→T059→T060 遞增鏈）、
  `auth/enforce.rs`（T034→T038）、`handler/route.rs`（T048 單點）、`error.rs`／`envelope.rs`（T007→T040）、`views/manage/user/index.vue`（T030→T055→T061→T062）、
  `modules/user-operate-drawer.vue`（T031→T057→T062）、locales 三檔＋`app.d.ts`（T032→T051→T062）。

## Parallel Example: Foundational

T006／T007／T008／T009／T010／T011／T012／T013／T014 九路可並行分派（檔域不相交）；T015～T021 半序（T015 與 T016 可並行、
T017 獨立、T018／T019 待型定案、T020 獨立、T021 最後）。US 內之 Tests 段各 [P] 任務同理可並行分派、cargo 執行仍序列。

## Implementation Strategy

- **MVP＝US1**（七支管理端點＋user 頁列表與抽屜）——第一個可 API 與 UI 同時驗收的穩定點；US2 緊接（斷權語意定案）。
- 逐 US 增量：每 US 收尾＝contract case 綠＋單元邊界 commit（兩段式＋generate）＋六步序（復核 agent 回報→自驗三閘→落帳→
  子庫 commit→`git add` 子庫＋generate→外層 commit）；次輪 review prompt 附前輪已駁回 findings（防呆六件套⑤）。
- 編排慣例：每執行單元一支 workflow（防呆六件套＋看門狗原子成對、CLAUDE.md §2）；U0 與 T071～T074 主線親做、user 親決兩題（T001）。

## Notes

- 本檔零 push／merge 任務；finishing 由收刀程序承接。
- 零 migration、零 seed 變更；任何單元冒出 DDL／seed 需求＝停手升級 user。
- 測試基準 829＝容器內實跑值；淨增數於 T069 補記。
- 前端零測試框架：US 前端 task 之驗收＝`pnpm typecheck`＋`pnpm exec oxlint <file>`＋fork-delta-lint＋view-render-guard＋CDP（T070）。
