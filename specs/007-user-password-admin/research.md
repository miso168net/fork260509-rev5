# Research — 007 使用者＋密碼管理（Phase 0）

> 基準：分支 `007-user-password-admin` @ 85c867b（spec clarify 後）；pins rust-api=5d2d536／base-web=854a72e；
> 憲法 v1.8.0；ROUTES 49；rust 測試 829；wire-schema definitions 75；contract case 50；throttle 降級 source 12。
> rev4 樹 `../fork260509-rev4/`（唯讀、HEAD 2b8a101、三樹乾淨）＝藍本；行號＝2026-08-26 實測凍結量、日後不重算。
> Technical Context 之 NEEDS CLARIFICATION＝零（brainstorm 41＋grilling 18＋clarify 3 題已盡）；本檔各節之
> 「決定」皆為工程自決（CLAUDE.md §5）、回報備查。

## R1 rev4 對應碼清單（ADR 0019 要求①；實作單元動工前逐檔先讀、重打字消化、註解重寫）

| # | rev4 檔（`../fork260509-rev4/` 下） | 用處（本刀對應面） |
|---|---|---|
| 1 | rev4:rust-api/server/src/handler/user.rs | handler 薄殼藍本：`get_user_list`:478／`add_user`:503／`update_user`:544／`delete_user`:582／`batch_delete_user`:600／`kick_user`:621／`reset_user_password`:643／`get_deleted_users`:665／`restore_user`:684／`update_user_session_policy`:703；`broadcast_revocation`:434（commit 後逐 sid 寫 denylist 的 best-effort 形＝R6 藍本）；私有 `map_*_err` 六支 :318-413（facade 錯誤→拒因鍵 remap 形）、`to_user_record`:273、`validate_admin_email`:266。★rev5 改用 `handler/common.rs` 共用件（`audit_operator` 拒寫 5000、`tristate`、`blank_to_none`、`db_status_to_wire`），rev4 之 `audit_meta`:448 fail-open 形不帶回 |
| 2 | rev4:rust-api/server/src/model/facade/sys_user.rs | facade 語意藍本：`find_active_by_id_for_update`:87／`find_deleted_by_id_for_update`:103／`advisory_lock_user_db`:265／`list`:560／`insert`:650／`update`:746（值 diff no-op）／`soft_delete`:979／`batch_soft_delete`:1002／`kick`:1038（doc「無 seeded 守門、未刪即可」）／`reset_password`:1097（冷卻在既有拒因全過後、UPDATE 前）／`set_session_policy`:1186／`list_deleted`:1270／`restore`:1301（鎖已刪列→同名活性→同信箱活性→成對清、零回灌）／`change_own_password`:1436（五步序＋`revoke_others_of_user(keep=sid)`）；稽核 payload 三支 `audit_json_with_roles`:153／`reset_password_audit_json`:165／`kick_audit_json`:172、事件 `make_user_event`:178。★custody 寫入形內嵌於 `reset_password`／`change_own_password`（rev4 **無**獨立 custody facade）；`need_change_pwd`:1730 與 email 家族 :1838-2039 不搬 |
| 3 | rev4:rust-api/server/src/model/password.rs | 密碼政策整套藍本：`hash`:66／`PASSWORD_POLICY_KEYS`:88（7 鍵）／`VIOLATION_*`:102-117（8 值、字面＝rev5 Lint24 白名單尾段）／`PasswordPolicy`:121／`load_policy`:187（單快照、缺鍵 fail-default）／`validate_against_policy`:209（收集全部違規、chars＋bytes、forbid_username 大小寫不敏感）；rev5 現有 `verify`:32／`dummy_verify`:42 同源 |
| 4 | rev4:rust-api/server/src/model/facade/sys_token.rs | `revoke_all_of_user`:160（★rev5 缺、本刀新增薄殼）；`revoke_others_of_user`:143 對照 rev5 :185 |
| 5 | rev4:rust-api/server/src/handler/user_center.rs | `get_password_policy`:350（7 鍵 allowlist 投影）／`change_password`:371＋`ChangePasswordReq`:71＋`map_change_pwd_err`:187；`get_profile`:296／`update_profile`:326／email 四支不搬 |
| 6 | rev4:rust-api/server/src/handler/route.rs | `SELF_SERVICE_ROUTES`:48（碼內常數）＋聯集去重接線 :53（rev5 `handler/route.rs::get_user_routes` 藍本） |
| 7 | rev4:rust-api/server/src/router.rs | 十支 user RouteDef :515-601＋`/userCenter/getPasswordPolicy`:679／`changePassword`:687 之 case_key 字面；profile／email 六支不取 |
| 8 | rev4:rust-api/server/src/middleware/mod.rs（`pwd_gate_mw`） | ★不搬（B-134）；只供辨識「首登判定」碼路徑、避免誤搬 |
| 9 | rev4 specs：`specs/rev4:011-user-admin`（spec Clarifications 五題；rev4:FR-004／FR-007／FR-036／FR-043；contracts）、`specs/rev4:014-user-center`（contracts #3 getPasswordPolicy allowlist、#4 changePassword）、`specs/rev4:015-pwd-custody`（Clarifications「強制態不豁免冷卻」；其餘不搬）、`specs/rev4:007-login-throttle`（unlock 端點語意） | spec 語意權威；wire 形 |
| 10 | rev4 ADR rev4:0006／0053／0054／0055／0065／0067＋rev4:.specify/memory/constitution.md §I.7 島 I 段 | 島 I 落字原料（I1～I5 原文形）；0067 只供辨識不搬 |
| 11 | rev4:base-web/src/views/manage/user/index.vue（469 行）、modules/user-operate-drawer.vue（352）、modules/user-unlock-modal.vue（111）、modules/user-search.vue（118、與 rev5 基線逐位同） | 管理頁全套藍本（`hasAuth(` 9 處七碼、回收桶 toggle、NDropdown 收納、`$dialog` 手輸新密碼；★`scroll-x=962` 未隨欄寬改＝瑕疵不抄） |
| 12 | rev4:base-web/src/views/user-center/index.vue（73）、modules/password-card.vue（190） | 個人中心父層骨架＋改密卡（★`verifyMethod` radio 與 `comingSoon` 假功能不抄）；basic-info／email／phone 三卡不搬 |
| 13 | rev4:base-web/src/components/custom/pwd-gen-modal.vue（156）、hooks/business/pwd-policy.ts（74、`buildPolicyRules`） | 產密浮層與動態 rules hook 藍本 |
| 14 | rev4:base-web/src/service/api/rev4-user-admin.ts（106）、typings/api/rev4-user-admin.d.ts（91、併入 `Api.SystemManage`——不帶回） | wrapper／typings 形（rev5 改獨立命名空間） |
| 15 | rev4:base-web/src/locales/langs/{zh-cn,en-us}.ts 之 `page.manage.user`（45 葉鍵）、`page.userCenter`、`pwdGen`、`backend.biz.user.*`（17 scalar）、`backend.auth.session.*` | i18n 鍵對照（rev5 只取本刀射程內鍵；跨頁借鍵不抄） |
| 16 | rev4 LESSONS rev4:L-121（前端正則擋含連字號密碼零請求）／rev4:L-145（熱套 casbin 後重登）／rev4:L-149（constant route 登出競態） | 坑清單 |
| 17 | 改密舊密節流（B-021） | ★rev4 **零實作**（rev4:B-102 承載未做）——零藍本；形取島 E 之 redis L1 負快取（rev5 `throttle/mod.rs` INCR／EXPIRE 家族）自建 |

## R2 rev5 拍板差異點清單（ADR 0019 要求②；★防回歸：以下 rev4 行為一律不得帶回）

1. 清空語意 `Some("")` → rev5 三態 `Option<Option<T>>`＋`#[serde(default)]`（`handler/common.rs::tristate`）；`blank_to_none` 僅 addUser。
2. userName 等值放行 → rev5 「出現即拒」（沿 `sys_role::update` roleCode 差異①）；前端 update wrapper 剝 `userName`。
3. 拒因 BizData 多鍵攜參 → rev5 純 key；**唯二例外** `biz.user.passwordPolicy{violations}`／`biz.user.pwdSetTooFrequent{remainingSeconds}`（Q19）；5003 恆純 key。
4. no-escalation 零實作 → rev5 於 handler 鎖內以具名純函式實作（Q09／Q28、R5）；`enforce.rs::no_escalation_check`:287 四參掛點續留恆 `Ok`。
5. 稽核詞彙大寫 8 值 → rev5 小寫 macro 五值＋本刀三值 `kick`／`reset_password`／`change_password`（釘值測 `t005_…_vocabulary_stays_five` 本刀必改、R11）。
6. op-log `audit_meta` fail-open → rev5 `audit_operator` 拒寫 5000（F3①）。
7. denylist TTL＝access 窗 → TTL＝refresh 全壽命（`cache::denylist_set` doc）。
8. logout 撤整鏈 → 只撤呈遞列（ADR 0059）；kick／停用撤全 active、不動 rotated（Q13）。
9. `needChangePwd` 第五欄 → 不帶回（B-134）。
10. `SELF_SERVICE_ROUTES` → 本刀帶回（Q22；`handler/route.rs` 檔頭「不帶回」句改寫）。
11. 每鈕 hasAuth gating → role／menu 頁不 gating 拍板不變；user 頁 gating＝例外釋義（Q10；判準寫 spec／ADR）。
12. 角色鍵 `roleId` → `id`。
13. `Api.SystemManage` 併入 → 獨立 `Api.UserAdmin`／`Api.UserCenter` 新檔（`rev5-user-admin.d.ts`／`rev5-user-center.d.ts`）。
14. `createTime／createBy` → `createdAt／createdBy`（帳號名）。
15. 跨頁借鍵（`menu.showDeleted`／`policyArchive.restoreSuccess`）→ `page.manage.user.*` 自備。
16. 未知 setting_type→2222 → 5000 fail-loud（沿 002）。
17. unlock `dimension` 預設帳號維 → 必給、缺席 2222（modal 顯式帶）。
18. 動詞不符→5003 → 4040（ADR 0031；delete 用 DELETE）。
19. `scroll-x=962` 不隨欄寬改 → Σ(width|minWidth)＝scroll-x 不變式、同批改。
20. 授權 modal 換角色殘影 → 先修 B-129 再照抄「請求世代」範式。
21. 新檔標記 `MODAL-WIRING(h)` → `[rev5-inline <軌道>+ 007]` 檔頭。
22. 首登強制換密整包 → 不做（B-134）。
23. 寫端 super-only 不對稱留置 → 本刀下放＋no-escalation（Q09）。
24. **（clarify）** 「超管因角色集最大自然不受限」→ 持 R_SUPER 者之 A 定義為全集（seed Super 只持 R_SUPER）。
25. **（clarify）** 「角色集變更」→ `roleIds` 期望全集全量替換、界外 id 整筆拒（非 orphan skip）。
26. **（clarify）** 觀測面零著墨 → 改密節流 fail-open 進 `throttle_degraded_total` 新 source；5003 只 warn 日誌。
27. rev4 custody「本人自改→全刪經手列」→ 只 upsert（G13）；rev4 冷卻豁免問答之「不豁免」沿用。
28. rev4 改密卡 `verifyMethod` radio 假功能／`deletedAt` 孤兒鍵 → 不抄（Q32／Q35）。

## R3 依賴釘版（CLAUDE.md §6）

零新依賴。既有版本錨（`rust-api/Cargo.toml`）：argon2 0.5.3（`hash` 沿用 `verify` 同 crate、PHC 形）、redis 1.3.0
（改密節流桶 INCR／EXPIRE 沿 `cache/mod.rs` 既有連線管理）、sea-orm 1.1.20、axum 0.8.9、casbin 2.20.0（判定面同步
純消費）；前端零新套件（naive-ui NDrawer／NDropdown／NModal／useNaivePaginatedTable 既有；產密用瀏覽器
`crypto.getRandomValues`）。

## R4 後端落點與分層（主線自拍、回報備查）

| 落點 | 動作 | 內容 |
|---|---|---|
| `model/password.rs` | 擴 | `hash`／`PasswordPolicy`／`load_policy`／`validate_against_policy`＋`PASSWORD_POLICY_KEYS`（7）＋`VIOLATION_*`（8、字面＝Lint24 白名單尾段）；`hash` 於鎖前呼叫 |
| `model/facade/sys_user.rs` | 擴 | `find_active_by_id_for_update`／`find_deleted_by_id_for_update`／`list`（分頁＋濾）／`insert`／`update`（三態＋值 diff）／`soft_delete`／`batch_soft_delete`／`kick`／`reset_password`／`set_session_policy`／`list_deleted`／`restore`／`change_own_password`；`advisory_lock_user` 自 `login.rs`:519 上提為 `pub(crate)`（DbErr 形；login 端薄殼改呼） |
| `model/facade/sys_user_role.rs` | 擴 | `role_codes_all_of_user`（T：不濾 status、join sys_role 取 code）／`replace_roles_of_user`（差集硬刪＋新增、回是否有變更）／`delete_all_of_user`（軟刪用）／`codes_of_role_ids`（N 轉 code、界外 id → Err） |
| `model/facade/sys_token.rs` | 擴 | `revoke_all_of_user(conn, uid) -> Vec<String>`（撤全部 active、回 distinct sid；rotated 不動） |
| `model/facade/session_event.rs` | 擴 | `EVENT_REVOKED`＋`REASON_USER_DISABLED`／`USER_DELETED`／`PASSWORD_RESET`／`PASSWORD_CHANGED`／`ADMIN_KICK`（順手收成 macro 單一宣告源＋值集測） |
| `model/facade/sys_pwd_custody.rs` | 新 | `touch(txn, user_id, created_by) -> DbErr`（upsert `created_at=now()`）／`last_set_at(conn, user_id, created_by) -> Option<DateTime>`；零 EXISTS 語意 |
| `auth/no_escalation.rs` | 新 | 純函式 `assert_no_escalation(actor: &ActorScope, target: &[String], next: &[String]) -> Result<(), Denied>`＋`ActorScope::{All, Codes(HashSet)}`＋`actor_scope_of(conn, uid)`（R_SUPER∈現役→All）；單元測含超管全集、停用角色進 T 不進 A、同級、∅ |
| `handler/user.rs` | 新 | 十支 handler＋`begin_and_lock_user`（begin→advisory(uid)→FOR UPDATE 活性列）＋`finish_user_write`（稽核→commit→斷權 best-effort→reload 條件）＋`map_*_err` |
| `handler/user_center.rs` | 新 | `change_password`／`get_password_policy` |
| `throttle/change_pwd.rs` | 新 | `precheck_change_pwd(cache, uid)`／`record_failure`／`clear`（redis INCR＋EXPIRE 900、閾 5、fail-open＋`throttle_degraded_total{source="redis_change_pwd"}`） |
| `cache/mod.rs` | 擴 | `REASON_ADMIN_KICK="admin_kick"`；改密桶鍵前綴 `cpwd:` |
| `auth/enforce.rs` | 改 | `enforce_mw` denylist reason→碼／鍵：`kicked`→7777 `auth.session.kicked`、`admin_kick`→7777 `auth.session.kickedByAdmin`、`revoked`→8888；`no_escalation_check` 不動 |
| `handler/auth/refresh.rs` | 改 | :234 附近鎖內加使用者活性重驗（`sys_user::find_by_id` status==1 ∧ deleted_at NULL；否則走 8888 路徑）——非方向反轉、ADR 明列 |
| `handler/route.rs` | 改 | `SELF_SERVICE_ROUTES: [&str; 1]=["user-center"]` 聯集去重；檔頭「不帶回」句改寫 |
| `error.rs`／`envelope.rs` | 擴 | `AppError::BizData(Cow<'static,str>, serde_json::Value)`（code 2222、msg=key）＋`Res::from_err_with_data`；`compile_fail` doctest 改寫為「`from_err` 仍 data null；帶資料只經 `from_err_with_data`」 |
| `obs.rs` | 擴 | `THROTTLE_DEGRADED_SOURCES` 12→13（`redis_change_pwd`）＋預註冊 |
| `model/audit.rs` | 擴 | vocabulary 加 `kick`／`reset_password`／`change_password`；釘值測改名擴八 |
| `router.rs` | 擴 | 12 條 RouteDef（case_key：`user-get-list`／`user-add`／`user-update`／`user-delete`／`user-batch-delete`／`user-restore`／`user-kick`／`user-reset-password`／`user-get-deleted`／`user-update-session-policy`／`user-center-change-password`／`user-center-get-password-policy`）；`ROUTES_COUNT` 49→61 |
| `handler/throttle.rs` | 改 | `unlock_login` 帳號維分支鎖內加 `assert_no_escalation`（T 依 R5） |
| `handler/common.rs` | 擴 | `wire_two_value_to_db`（B-127 收攏；role.rs／menu.rs 改 import） |
| `tests/contract.rs` | 擴 | 12 ContractCase（50→62） |
| `tests/authz_entrypoint_lint.rs` | 改 | `RELOAD_CALL_FILES` 加 `handler/user.rs` |
| `model/mod.rs::test_db` | 擴 | `UserCleanup` 補業務鍵腿＋op-log 腿＋`setval('sys_user_id_seq',3,true)`；`PwdCustodyCleanup`（RAII）；`SessionRevokeCleanup`（撤銷列與事件） |

鎖序（島 G5／H1／ADR 0049 §3②）：advisory(uid)→`sys_user` 列 FOR UPDATE→`sys_role` 列升序（僅需比對 code 時
讀、不鎖）→`sys_user_role` 寫；addUser 無 uid 豁免 advisory、以 `user_name` 活性唯一索引兜底；批刪依 id 升序逐一
取 advisory 再逐列鎖（同 `batch_soft_delete` rev4 升冪形、防死鎖）；`login.rs` 既有 uid 鍵＝同一用途擴消費者
（H1 核過：user 域 key space＝uid、選單域＝高位常數 `0x7265_7635_6D65_6E75`，不碰撞）。

## R5 no-escalation 設計（Q09／Q09-2／Q28／G1／G2／clarify Q1）

- 比對單位＝**role_code**（穩定、可讀）；`A`＝`roles_of_user(txn, claims.uid)`（濾角色軟刪與 status≠1）→ 若含
  `R_SUPER` ⇒ `ActorScope::All`，否則 `Codes(set)`；`T`＝`role_codes_all_of_user(txn, target_id)`（`sys_user_role`
  join `sys_role`、不濾 status；軟刪角色因 in-use 守門結構上無指派列）；`N`＝`codes_of_role_ids(txn, body.roleIds)`
  （界外／已軟刪 id → `biz.user.roleNotFound` 整筆拒）；缺席 roleIds ⇒ N＝T。
- 判定序（每支寫端鎖內、寫前）：①活性標的鎖讀（`notFound`）②seed 保護③self 五不④`assert_no_escalation(A,T,N)`
  ⑤業務守門（唯一、政策、冷卻…）；違④→`AppError::Forbidden`（5003、純 key `auth.forbidden` 沿既有）＋
  `tracing::warn!(actor, target, endpoint)`。
- 掛點：addUser（T＝∅、N＝body）／updateUser（T、N）／deleteUser／batchDeleteUser（每筆 T）／restoreUser（T＝∅）／
  kickUser（T）／resetUserPassword（T）／updateUserSessionPolicy（T；super-only 故 vacuous、仍掛保一致）／
  unlockLogin 帳號維（T；IP 維不套）。
- 測試（FR-021）：`no_escalation.rs` 純函式表驅動（All／子集／超集／同級／∅／停用角色進 T）；每支 handler 兩負向
  一正向（測內以 `casbin_rule` 資料列 grant 給 R_ADMIN、`CasbinCleanup` 兜底；正向＝Super 編輯持 {R_ADMIN} 者）。

## R6 斷權接線（Q13／Q14／Q15／G9／G10）

- 交易內：`sys_token::revoke_all_of_user(&txn, uid)` → sids；逐 sid `session_event::insert(EVENT_REVOKED, reason)`；
  稽核列；commit。commit 後 best-effort：逐 sid `cache::denylist_set(sid, reason, ttl.refresh_secs)`（rev4
  `broadcast_revocation` 形；失敗 warn、PG 權威）。
- reason 映射：停用 `user_disabled`／刪除 `user_deleted`／重設 `password_reset`／自改 `password_changed`（皆 denylist
  `revoked`→8888）；kick `admin_kick`（denylist `admin_kick`→7777、新鍵 `auth.session.kickedByAdmin`）。
  `enforce_mw` 分鍵：`REASON_KICKED`→既有鍵、`REASON_ADMIN_KICK`→新鍵、其餘 8888；`kicked`／`revoked` 島 C 語意不變。
- refresh 鎖內重驗：`refresh.rs` 於 `roles_of_user`（:234）同一 txn 加 `sys_user::find_by_id` 活性判（status==Some(1)
  ∧ deleted_at NULL）；不活 ⇒ 撤該列＋8888（沿既有 revoked 路徑）；Authed 端點與 `getUserInfo` 沿 003 不判。
- ADR 0059 復核：logout 呈遞 rotated 票之 no-op 不受影響（本刀只擴撤銷來源、不改 logout 射程）——結論入新 ADR。
- changePassword：`revoke_others_of_user(keep=claims.sid)`（既有）＋事件 `password_changed`＋稽核 `change_password`。

## R7 密碼面（Q18／Q19／Q20／Q21／Q26／Q30／G12～G14）

- 政策：`load_policy` 單快照 7 鍵（min／max／四 require／forbid_username；缺鍵 fail-default 沿 rev4）；
  `validate_against_policy(pw, user_name, &policy) -> Vec<&'static str>`（chars 計長、bytes ≤`LOGIN_PASSWORD_MAX_BYTES`
  512、forbid_username 大小寫不敏感相等）；三入口共用；登入路徑零呼叫（機器守＝`login.rs` 零 `validate_against_policy`
  引用之 grep 測）。
- 明細通道：`AppError::BizData(key, Value)`；`Res::from_err_with_data(e)`：`data=Some(value)`、`code=2222`、`msg=key`；
  `from_err` 仍 data null。射程二鍵：`biz.user.passwordPolicy` `{violations:[…]}`、`biz.user.pwdSetTooFrequent`
  `{remainingSeconds:n}`；其餘沿 `Biz`。Lint24：`RE_I18N_SITE` 已匹配 `AppError::BizData(`、白名單八鍵不作 msg。
- 冷卻：`password_change_min_interval` 讀自 system_settings（0＝停用）；`sys_pwd_custody::last_set_at(user_id,
  created_by)`；`now-last < interval` ⇒ `BizData(pwdSetTooFrequent, {remainingSeconds})`；通過後寫入 UPDATE＋
  `touch`；addUser 亦 `touch`（G14）；判定位＝既有拒因全過後、UPDATE 前（rev4 序）。
- changePassword 五步序：`find_active_by_id_for_update(claims.uid)`→兩次一致（`biz.user.passwordConfirmMismatch`）→
  舊密 `verify`（失敗→`record_failure`＋`biz.user.oldPasswordMismatch`）→新≠舊（`biz.user.passwordSameAsOld`）→
  政策→hash→UPDATE＋touch＋`revoke_others_of_user`＋事件＋稽核→commit→`clear` 桶。
- 改密節流（零藍本）：`throttle/change_pwd.rs`——鍵 `cpwd:{uid}`；`precheck`：GET≥5 ⇒ `biz.user.changePasswordThrottled`
  （在 `verify` 之前、零稽核）；`record_failure`：INCR＋EXPIRE 900（滑動窗簡化＝固定 TTL 續期；spec「滑動窗」以
  「每次失敗刷新 15 分鐘窗」實作、常數 `CHANGE_PWD_MAX_FAILS=5`／`CHANGE_PWD_WINDOW_SECS=900`）；redis Err ⇒
  fail-open＋`throttle_degraded_total{source="redis_change_pwd"}`；成功 `DEL`。
- `getPasswordPolicy`：Authed；投影七鍵（`minLength／maxLength／requireDigit／requireLowercase／requireUppercase／
  requireSpecial／forbidUsername`）；前端 `hooks/business/pwd-policy.ts::buildPolicyRules`（rev4 形；失敗降 required）。

## R8 測試設施與機器閘衝擊（tasks 硬前置；逐閘）

1. `ROUTES_COUNT` 49→61 同 commit；`tests/contract.rs` ContractCase 50→62（case_key 反查形、不抄 rev4 路徑字面）。
2. `authz_entrypoint_lint.rs::RELOAD_CALL_FILES` 加 `handler/user.rs`（恰等斷言）；updateUser 角色集實際變更才 reload。
3. `audit.rs` 釘值測 `t005_role_menu_family_adds_no_variant_vocabulary_stays_five` → 改名擴八值（spec FR-005）。
4. `obs.rs` 十二源測 → 十三；活書 §5 觀測面清單＋複驗法同批。
5. `wire_i64_guard_lint.rs`：新 wire 型 i64 欄（`id`、`createdBy` 若為 id）掛 `serialize_*_guarded`。
6. `wire_schema.rs`：新命名空間 `Api.UserAdmin.*`／`Api.UserCenter.*` 每 definition 正向≥1 反例≥1；快照重抽（需 dev
   stack、單元收尾）；definitions 75→＋N。
7. `entity_access_lint`：handler 零 path-root `entity::`（新 handler 全走 facade）。
8. schema-gate 三閘：零 DDL；`sys_user`／`sys_user_role` 集外 ⇒ gate2 逐列全等 ⇒ `UserCleanup` 補業務鍵腿（`user_name`
   前綴）＋op-log 腿＋`setval('sys_user_id_seq', 3, true)`；`sys_pwd_custody` 首寫 ⇒ `PwdCustodyCleanup`（依
   user_id 集刪）、是否入 `RUNTIME_APPEND_TABLES` 實作期判（傾向不入、走守衛）。
9. `SeedOpLogCleanup::arm` 於動 seed 三帳號之測；`sys_token`／`session_event` 撤銷列由 `ChainRowsCleanup`／
   `SessionEventCleanup` 既有守衛管。
10. Lint24 backend-msg-dict 重算（新 `biz.user.*` 鍵三檔同批＋`auth.session.kickedByAdmin`）。
11. fork-delta-lint：修改型標記只落 (v)(vi)(vii) 檔集；`原行:` 多行註解形；route-artifact-gate 零重算（不新增 view 目錄）。
12. seed-view-gate 豁免表不動；view-render-guard 掃 `views/manage/**`（memo 純文字插值）。
13. docs-sync：活書 §5／§6／§8 增補（餘裕 20／40／77）、附屬文件接線段、§12 六詞；Lint25 rev4 前綴。
14. B-113：`update_role_endpoints_super_full_candidate_save_…` 續綠；種合成候選外 protected 探針列、`outside_protected≥1`
    升真 assert（隨端點註冊單元）。

## R9 前端落地要點（主線自拍）

- 修改型（(v)）：`views/manage/user/index.vue`（接 `fetchGetUserList`／`fetchGetDeletedUsers`；刪 console.log 假實作；
  回收桶 `showDeleted` toggle 切兩資料源、已刪模式隱搜尋卡、operate 欄換復原；NDropdown 收 kick／resetPwd／隨機密碼；
  七碼 `hasAuth` B-099 形；memo 欄純文字；`scroll-x`＝Σ 欄寬）、`modules/user-operate-drawer.vue`（接 `fetchAddUser`／
  `fetchUpdateUser`／`fetchUpdateUserSessionPolicy`；刪 `getRoleOptions()` mock 段改 `fetchGetAllRoles`；修
  `path="email"`→`userEmail`；password 僅 add＋隨機鈕＋hint；sessionPolicy 僅 edit、非超管 disabled＋提示、與現值
  diff 才呼；userName edit disabled；self 之 status／roleIds disabled；memo textarea）；`user-search.vue` 零改動。
- 新增型：`modules/user-unlock-modal.vue`（雙維、`fetchUnlockLogin` 顯式 `dimension`）、`components/custom/pwd-gen-modal.vue`
  （CSPRNG、依政策產合規密碼）、`views/user-center/modules/password-card.vue`、`typings/api/rev5-user-admin.d.ts`＋
  `rev5-user-center.d.ts`、`service/api/rev5-user-admin.ts`＋`rev5-user-center.ts`（直接路徑 import、不經 barrel）。
- (vi)：`views/user-center/index.vue` 修改型（父層骨架＋只掛 password-card）；(vii)：`pwd-login.vue` formRules
  pwd／userName → `createRequiredRule`。
- 順路：B-129（三 modal `getChecks()` 起手清空＋`homeReq` 世代）、B-132（`menu/index.vue` 切模式重置 pageSize）、
  B-128（編排 script .ts 驗證改 `pnpm exec oxlint <file>`＋RUNBOOK 段）。
- i18n：`page.manage.user` 現 21 葉鍵 → 補至射程所需（列表欄／抽屜欄／操作／確認框／解鎖 modal／`pwdGen.*`）；
  `page.userCenter.*` 新 top-level；`backend.biz.user.*`＋`auth.session.kickedByAdmin` 三檔；`app.d.ts` 型節。
- CDP：起手清 localStorage；三角色反覆切（B-064 三顆鈕）；下放情境先用 006 modal（或 curl updateRoleEndpoints／
  updateRoleButton）授 R_ADMIN；走查排 schema-gate 之後。

## R10 治理面原料（U0 主線親做、user 親審）

- 憲法 Amendment v1.9.0：§I.7 於島 H 之後加**島 I 使用者域治理**六條（I1 寫端鎖序／I2 斷權即時性與分碼不互換／I3 seed
  帳號與自身結構保護／I4 軟刪硬刪指派＋復原零回灌／I5 密碼政策單一驗證點＋登入不驗／I7 no-escalation 包含規則
  〔A 之超管全集定義入條文方向面〕；常數留活書）；§III.2 表加三列 (v)(vi)(vii)（檔級名單定數）；修訂日誌一列。
- ADR 五支（實作期落檔、accepted）：①島 I＋掛點分工＋gating 例外釋義；②BizData 二鍵＋0022 §2② 澄清＋B-024③；
  ③SELF_SERVICE_ROUTES；④冷卻＋改密節流（含觀測 source）；⑤ADR 0042 措辭訂正＋0053 矩陣補列。
- U0 硬閘：Amendment accepted 前不得動 base-web 既有檔、不得落憲法接觸面碼；純後端單元可先行。

## R11 本輪查證對既有敘述的校正（回報備查）

1. wire-schema definitions 現 **75**（006 SC 寫「自 57 淨增」為當時基線；本刀基線以 75 計）。
2. `page.manage.user` zh-cn 現 **約 21** 葉鍵（brainstorm 記 19；以實作期 grep 為準）。
3. 稽核詞彙釘值測 `t005_…_vocabulary_stays_five`（`audit.rs`:259）——006 R2 曾記「不得改」，係指 006 射程；本刀依
   spec FR-005 擴三值、測改名。
4. 受政策管制端點計數「35」無具名常數（僅 `ROUTES_COUNT`）；spec 之「35→45」以 `getAllEndpoints` 候選集實測為驗收錨。
5. rev4 **無**獨立 custody facade（寫入形內嵌 `sys_user.rs`）；rev5 新立 `sys_pwd_custody.rs` 為刻意分層（只時戳）。
6. rev4 改密舊密節流零實作（B-021 承 rev4:B-102 未做）——spec「rev4 對應」欄無此項；零藍本自建。
7. `no_escalation_check` 為 `pub(crate) async fn`（`enforce.rs`:287）、非同步簽章；本刀不動。
8. `unlockLogin` 稽核 `entity_table='login_throttle'` 既有已知態沿用。

## R12 執行單元切分（tasks 期定稿；~10 支）

U0 憲法 Amendment＋ADR ①（島 I）草稿（user 親審、硬閘）→ U1 後端底座（password 三支＋BizData／envelope＋
`revoke_all_of_user`＋session_event 值集＋custody facade＋`advisory_lock_user` 上提＋`no_escalation.rs`＋obs source＋
audit 三值）→ U2 user facade 寫端＋handler 十支＋ROUTES 61＋contract 12＋seed 保護＋self 五不＋B-127＋B-113 探針
→ U3 changePassword＋getPasswordPolicy＋改密節流＋SELF_SERVICE_ROUTES → U4 refresh 重驗＋enforce 分鍵＋新 msg 鍵
→ U5 前端 user 頁（(v)、含 B-129／B-132 先修、typings＋wrapper＋裁判）→ U6 user-center 改密卡＋pwd-login required-only
（(vi)(vii)）＋i18n 兩語 → U7 wire-schema 重抽＋CDP 三角色走查＋RUNBOOK §12.1 量測 → U8 收尾（活書 as-built、ADR
②～⑤ accepted、BACKLOG 關帳、B-128 ①②、勘誤四處）。rust 全程 serial 容器內；每單元 pin bump。
