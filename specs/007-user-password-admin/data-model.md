# Data Model — 007 使用者＋密碼管理

> 零 DDL、零 seed 變更（spec FR-001／SC-004）。全表欄集以 `docs/generated/reference/schema.md` 為真表；本檔只列
> 本刀消費面與新增語意。狀態機以「現態 × 事件 → 次態＋副作用」鏡頭寫（憲法 §IV 第 9 題）。

## §1 既有資料表的消費面（零 DDL）

### 1.1 `sys_user`（archetype A、十七欄；本刀首個寫端家族）

- 識別：`id`（bigserial、`sys_user_id_seq`）、`user_name`（現役唯一：`sys_user_user_name_active_uniq WHERE deleted_at IS NULL`；
  建後不可變、形制 `^[A-Za-z0-9_-]{1,64}$`）。
- 憑證：`password`（argon2id PHC；三重不洩）。
- 個資：`nick_name`／`user_gender`／`user_phone`（≤32、選填）／`user_email`（選填；現役唯一不分大小寫：
  `sys_user_user_email_active_uniq (lower(user_email)) WHERE deleted_at IS NULL AND user_email IS NOT NULL`；簡式格式守門）／
  `user_memo`（text、列表純文字顯示、抽屜編輯）。
- 狀態：`status smallint` 可空零 CHECK——碼層二值收斂「`Some(1)`＝啟用、其餘＝停用」（wire `'1'|'2'`、共用映射
  `wire_two_value_to_db`／`db_status_to_wire`）；`session_policy varchar(20) NOT NULL DEFAULT 'inherit'`（三值
  inherit／single／multi、碼層收斂、值域外 2222）；`session_id`（login 寫、本刀唯讀）。
- 審計六欄（§I.6）：`created_at／created_by／updated_at／updated_by／deleted_at／deleted_by`；軟刪＝成對寫、復原＝成對清。
- 寫端：insert／update／soft_delete／batch_soft_delete／restore／kick（不改欄、只撤票）／reset_password／set_session_policy／
  change_own_password；鎖形 `SELECT … WHERE id=$1 AND deleted_at IS NULL FOR UPDATE`（restore 用 `deleted_at IS NOT NULL`）。
- seed：id 1 Super（R_SUPER）／2 Admin（R_ADMIN）／3 User（R_USER），密碼 `123456`（6 字元＜min 8 ⇒ 登入路徑不驗政策）。

### 1.2 `sys_user_role`（join；PK (user_id, role_id)；無審計欄、無 seq）

- 讀：`roles_of_user`（現役角色 code、濾角色軟刪＋status=1）＝操作者 A 來源；`role_ids_of_user`／新 `role_codes_all_of_user`
  （不濾角色 status）＝標的 T 來源；`count_by_role`（不濾）＝角色 in-use 守門（島 G4）。
- 寫（本刀首建）：`replace_roles_of_user`（期望全集：差集硬刪＋新增、同交易）／`delete_all_of_user`（軟刪使用者時）。
  復原零回灌（不寫）。

### 1.3 `sys_pwd_custody`（archetype C join·狀態機；PK (user_id, created_by)；零 FK；本刀首寫）

- 語意（本刀限縮）：`created_at`＝「(標的, 操作者) 對上次設密時間」；只 upsert、不刪他列、不做 EXISTS 判定
  （首登經手判定歸 B-134）。
- 寫端：addUser（初始密碼）／resetUserPassword／changePassword（operator＝target）皆 `touch`。
- 測試：`PwdCustodyCleanup`（依 user_id 集刪）；是否入 schema-gate `RUNTIME_APPEND_TABLES` 實作期判（傾向不入）。

### 1.4 `sys_token`／`session_event`（島 A／B／C 既有；本刀擴撤銷來源）

- `sys_token`：新讀寫 `revoke_all_of_user(uid)`（`status='active'`→`revoked`、回 distinct sid；rotated 不動）；
  `revoke_others_of_user(keep=sid)` 既有（changePassword）。
- `session_event`：新事件型 `revoked`；reason 新五值 `user_disabled／user_deleted／password_reset／password_changed／admin_kick`
  （varchar、零 migration）；既有 `kicked／single_session` 不動。

### 1.5 `sys_operation_log`（append-only；`real_ip inet NOT NULL`）

- 每寫端同交易一列；`operation` 新三值 `kick／reset_password／change_password`；payload `{id,user_name}`（＋update 之欄變更
  摘要、不含密碼）；`entity_table='sys_user'`；unlock 沿既有 `login_throttle`。

### 1.6 `casbin_rule`／`sys_role`（唯讀）

- `sys_role`：code 查表（T／N 轉 code、界外／已軟刪 id → 拒）；`status` 只影響 A 不影響 T。
- `casbin_rule`：本刀零寫入；運行期下放由 006 授權 modal 寫（測內以資料列 grant＋`CasbinCleanup`）。

### 1.7 `system_settings`（唯讀；八鍵 `password_*`）

- 七鍵入 `PasswordPolicy`（單快照、缺鍵 fail-default）；`password_change_min_interval` 供冷卻（0＝停用、界 [0,86400]）。

## §2 記憶體實體與常數（非資料庫）

| 名 | 落點 | 語意 |
|---|---|---|
| `ActorScope::{All, Codes(HashSet<String>)}` | `auth/no_escalation.rs` | 操作者 A；含 R_SUPER ⇒ All |
| `assert_no_escalation(A, T, N)` | 同上 | `T ⊆ A ∧ N ⊆ A`；All 恆過 |
| `USER_SEED_IDS={1,2,3}`／`SUPER_USER_ID=1` | `model/facade/sys_user.rs` | seed 帳號結構保護 |
| `SELF_SERVICE_ROUTES=["user-center"]` | `handler/route.rs` | 自助路由白名單 |
| `CHANGE_PWD_MAX_FAILS=5`／`CHANGE_PWD_WINDOW_SECS=900` | `throttle/change_pwd.rs` | 改密舊密節流（碼內常數） |
| `REASON_ADMIN_KICK="admin_kick"` | `cache/mod.rs` | denylist reason 第三值（7777 分鍵） |
| `EVENT_REVOKED`＋五 reason | `facade/session_event.rs` | 見 §1.4 |
| `VIOLATION_*`（8） | `model/password.rs` | 違規碼＝Lint24 白名單尾段 |
| `THROTTLE_DEGRADED_SOURCES` +`redis_change_pwd` | `obs.rs` | 觀測 source 13 |
| `PasswordPolicy`（7 欄） | `model/password.rs` | 單快照 |

## §3 狀態機矩陣

### 3.1 使用者列（現態 × 事件 → 次態＋副作用）

| 現態 | 事件 | 守門（固定序） | 次態 | 副作用 |
|---|---|---|---|---|
| — | addUser | 形制／唯一（name、email）／政策／冷卻對（首寫）／N ⊆ A | 啟用（或抽屜指定停用）、角色＝N | hash 鎖前；custody touch；稽核 `add` |
| 啟用／停用 | updateUser（非 status／roles） | notFound→seed／self→T ⊆ A→三態 diff | 同態 | 值 diff 才寫；稽核 `update` |
| 啟用 | updateUser status→2 | ＋Super 恆禁、self 禁 | 停用 | 同交易撤全 active＋事件 `user_disabled`＋commit 後 denylist `revoked` |
| 停用 | updateUser status→1 | 同上 | 啟用 | 無撤銷 |
| 啟用／停用 | updateUser roleIds | ＋N ⊆ A、界外 id 拒 | 角色＝N | 差集硬刪＋新增；實際變更 ⇒ commit 後 reload_enforcer |
| 啟用／停用 | deleteUser／batch | notFound→seed 三帳號→self→T ⊆ A；batch 任一違規整批 rollback | 軟刪 | 硬刪指派＋撤全 active＋事件 `user_deleted`＋稽核 `delete`（batch 逐列） |
| 軟刪 | restoreUser | 鎖已刪列→T(∅) ⊆ A→同名活性→同信箱活性（撞→2222）〔本刀 U5 as-built：④依通則序排在⑤業務守門之前；生產態 T ≡ ∅ 故兩序逐位同形，詳 contracts §7 該節勘誤〕 | 刪除前 status、零角色 | 稽核 `restore`；零 reload |
| 軟刪 | 其他寫端 | — | — | `biz.user.notFound` |
| 啟用／停用 | kickUser | notFound→self 禁→T ⊆ A | 同態 | 撤全 active＋事件 `admin_kick`＋denylist `admin_kick`（7777）＋稽核 `kick` |
| 啟用／停用 | resetUserPassword | notFound→self 禁（→個人中心）→T ⊆ A→政策→冷卻 | 同態（新雜湊） | custody touch；撤全 active＋事件 `password_reset`＋稽核 `reset_password` |
| 啟用／停用 | updateUserSessionPolicy | notFound→T ⊆ A（super-only 故 vacuous）→三值 | 同態 | 稽核 `update`；改 single 不即時踢 |
| 啟用（本人） | changePassword | 存在→兩次一致→節流 precheck→舊密→新≠舊→政策→（冷卻對＝self） | 同態（新雜湊） | custody touch；撤他 session 保留當前＋事件 `password_changed`＋稽核 `change_password`；成功清桶 |

seed 保護（先於一切）：id∈{1,2,3} 不可刪；id 1 不可停用、不可解除 R_SUPER 指派。self 五不：刪／停用／踢／改自身指派／
resetUserPassword 對 self；self 可改非角色欄與 sessionPolicy。

### 3.2 斷權（被撤者所見）

| 來源 | session_event | denylist reason | 被撤者 |
|---|---|---|---|
| 管理員踢除 | `revoked`／`admin_kick` | `admin_kick` | 7777＋`auth.session.kickedByAdmin` |
| 單一會話頂替（既有） | `kicked`／`single_session` | `kicked` | 7777＋`auth.session.kicked` |
| 停用／刪除／重設／自改 | `revoked`／對應 reason | `revoked` | 8888；再登入 1000 |

refresh：鎖內重驗 `status==Some(1) ∧ deleted_at IS NULL`，不活 ⇒ 8888 路徑；PG 權威、denylist best-effort（redis 故障
下 access 票活到期＝已知降級、島 C 方向不變）。

### 3.3 密碼面

- 政策：`validate_against_policy` 收集全部違規 → `BizData(passwordPolicy,{violations})`；登入路徑零呼叫。
- 冷卻：`now − last_set_at(target, operator) < interval` ⇒ `BizData(pwdSetTooFrequent,{remainingSeconds})`；interval=0 停用；
  addUser 計入。
- 改密節流：`cpwd:{uid}` 計數 ≥5 ⇒ `changePasswordThrottled`（純 key、在 verify 前、零稽核）；失敗 INCR＋EXPIRE 900；
  成功 DEL；redis Err ⇒ fail-open＋`throttle_degraded_total{source=redis_change_pwd}`。

### 3.4 判定面同步

updateUser 之角色集**實際變更**（差集非空）commit 後 `reload_enforcer`；其餘寫端零觸發（restore 零回灌、delete 硬刪指派
但被撤者已無 session——照 006 移除面「有變更才觸發」口徑，deleteUser 硬刪指派列亦觸發 reload 以清判定面殘留）。
`RELOAD_CALL_FILES` 加 `handler/user.rs`。

## §4 島 I 不變式骨架（Amendment 原文於 U0 定稿、user 親決）

- **I1 寫端鎖序**：使用者域一切寫端 MUST 於 per-user advisory 鎖內 lock-then-redecide；固定鎖序 advisory(uid)→sys_user 列→
  sys_role 列升序→sys_user_role；新增豁免。
- **I2 斷權即時性**：停用／刪除／重設密碼 MUST 同交易撤銷標的全部 active 票並落事件；denylist best-effort、PG 為權威；
  refresh MUST 鎖內重驗活性；MUST NOT 每請求活性判定；`kicked`／`admin_kick`／`revoked` 三 reason 不互換。
- **I3 seed 帳號與自身結構保護**：seed 三帳號不可刪；Super 恆禁停用、恆禁解除超管指派；self 五不；碼內常數。
- **I4 軟刪硬刪指派＋復原零回灌**：軟刪 MUST 同交易硬刪全部指派；復原 MUST NOT 回灌、status 保留。
- **I5 密碼政策單一驗證點**：三入口共用；違規全部收集；密碼三重不洩；登入路徑 MUST NOT 驗政策。
- **I7 no-escalation 包含規則**：寫端授權可下放；下放後 MUST 以 `T ⊆ A ∧ N ⊆ A` 守門（A＝操作者現役、持 R_SUPER 者為全集；
  T＝標的全部指派列）；違者 fail-closed 純 key；反轉＝MAJOR。

## §5 錯誤碼對應（13 碼矩陣零觸碰）

| 碼 | 用法 | 鍵 |
|---|---|---|
| 0000 | 成功 | — |
| 2222 `Biz` | 純 key 拒因 | `biz.user.notFound／userNameExists／userNameInvalid／userEmailExists／userEmailInvalid／seededProtected／superCannotDisable／cannotDeleteSelf／cannotDisableSelf／cannotKickSelf／cannotEditSelfRoleOrStatus／cannotResetSelfPassword／roleNotFound／sessionPolicyInvalid／passwordConfirmMismatch／oldPasswordMismatch／passwordSameAsOld／changePasswordThrottled` |
| 2222 `BizData` | 攜參（唯二） | `biz.user.passwordPolicy{violations[]}`／`biz.user.pwdSetTooFrequent{remainingSeconds}` |
| 5003 | no-escalation 拒（純 key、既有 forbidden 鍵） | 沿既有 |
| 5000 | request context 缺席拒寫 | 沿既有 |
| 4040 | 動詞不符 | 沿 ADR 0031 |
| 7777／8888 | 斷權 | `auth.session.kicked`（既有）／`auth.session.kickedByAdmin`（新）／`auth.session.reLogin`（既有） |

## §6 sequence 紀律

- `sys_user_id_seq`：集外表 ⇒ addUser 走 nextval 之測後 MUST `setval('sys_user_id_seq', 3, true)`（`UserCleanup` 補腿）；
  測試造列優先顯式大 id、只有 addUser 端點測走 nextval。
- `sys_user_role`：複合 PK 無 seq；清理走 user_id 集。
- `sys_pwd_custody`：複合 PK 無 seq；`PwdCustodyCleanup`。
- `sys_token`／`session_event`／`sys_operation_log`：收窄集內、seq 不重設；殘列由既有守衛管。
