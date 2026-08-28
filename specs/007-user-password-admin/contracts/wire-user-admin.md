# Contract — 使用者管理十支端點（＋unlockLogin UI 接線）

> 權威序依憲法 §I.3。wire 型落 rev5 獨立命名空間 `Api.UserAdmin`（`base-web/src/typings/api/rev5-user-admin.d.ts`；
> fetcher `base-web/src/service/api/rev5-user-admin.ts`、不入 barrel）。信封 `{data, code, msg}`、業務錯誤 HTTP 200
> （例外 4040→404、5003→403）。十支皆 `Protection::Policy`、seed 全 R_SUPER（getUserList 另 R_ADMIN）、零新 seed；
> 使用者鍵一律 `id`；拒因純 key（例外＝密碼二鍵攜參、見 wire-user-center.md／msg-keys.md）。

## 共用型

- `UserStatus`＝`'1' | '2'`（啟用／停用；DB `Some(1)`／其餘）。
- `SessionPolicy`＝`'inherit' | 'single' | 'multi'`。
- `UserRecord`＝`{ id: number, userName: string, nickName: string | null, userGender: string | null, userPhone: string | null,
  userEmail: string | null, status: UserStatus, sessionPolicy: SessionPolicy, userMemo: string | null, roles: string[],
  createdAt: string, createdBy: string | null, updatedAt: string | null, updatedBy: string | null }`（`roles`＝現役角色 code；
  `createdBy／updatedBy`＝帳號名經 `resolve_operator_names`；id 欄走 `serialize_i64_number_guarded`）。
- `UserSearchParams`＝`{ current: number, size: number, userName?: string, nickName?: string, status?: UserStatus,
  userGender?: string }`（模糊欄空字串＝未設）。
- `UserList`＝`PageRes<UserRecord>`（共用分頁信封；現役 `id ASC`）。

> ★**2026-08-28 勘誤（U1 邊界、主線工程自決）**：`nickName` 原寫作非可空 `string`，係落字之誤——本檔 §3 addUser 之 `nickName?`（選填、空字串→NULL）、DB `sys_user.nick_name`（nullable=YES）、rev5 既有同族欄慣例（`Api.RoleAdmin` 之 `roleMemo: string | null`）與 rev4 自身 typing（`nickName?: string | null`）四者一致指向可空，且照原字面落地就得在 handler 端捏一個空字串當值（＝rev4 的空字串摺疊形，research R2 明列不帶回）。故訂正為 `string | null`；碼面 `handler/user.rs` 之 `Option<String>` 為正、無須改。

## 1. `GET /systemManage/getUserList`

- Query：`UserSearchParams`。200 `data: UserList`（現役、含 status 停用者；已刪不含）。

## 2. `GET /systemManage/getDeletedUsers`

- Query：`{ current, size }`。200 `data: UserList`（`deleted_at IS NOT NULL`；`deleted_at DESC, id DESC`；`roles` 恆 `[]`）。

## 3. `POST /systemManage/addUser`

- Body：`{ userName: string, password: string, nickName?: string, userGender?: string | null, userPhone?: string | null,
  userEmail?: string | null, status?: UserStatus, roleIds?: number[], userMemo?: string | null }`（空字串→NULL；status 預設 `'1'`；
  roleIds 預設 `[]`）。
- 守門序：形制（`userNameInvalid`）→現役唯一（`userNameExists`／`userEmailExists`，含 23505 兜底）→信箱格式
  （`userEmailInvalid`）→`roleIds` 存在且未軟刪（`roleNotFound`）→N ⊆ A（5003）→政策（`passwordPolicy` 攜參）→
  冷卻對 (新 id, operator) 首寫免判→INSERT＋指派＋custody touch＋稽核 `add`。
- 200 `data: { id: number }`。

## 4. `POST /systemManage/updateUser`

- Body：`{ id: number, nickName?: string, userGender?: string | null, userPhone?: string | null, userEmail?: string | null,
  status?: UserStatus, roleIds?: number[], userMemo?: string | null }`（三態：缺席＝不動、null＝清空；`userName` 出現即拒
  `userNameImmutable`；`roleIds`＝期望全集全量替換）。
- 守門序：notFound→seed（id 1 且 status→'2'：`superCannotDisable`；id 1 且 roleIds 缺 R_SUPER：`seededProtected`）→self
  （`status`／`roleIds` 出現：`cannotEditSelfRoleOrStatus`）→T ⊆ A ∧ N ⊆ A（5003）→唯一／格式→值 diff（全缺席早退＋
  無變更＝no-op 0000 零寫入）。
- 副作用：status→'2' ⇒ 撤全 active（`user_disabled`）；roleIds 實際變更 ⇒ reload。
- 200 `data: null`。

## 5. `DELETE /systemManage/deleteUser`

- Body：`{ id: number }`。守門：notFound→seed（`seededProtected`）→self（`cannotDeleteSelf`）→T ⊆ A。
- 副作用：軟刪＋硬刪指派＋撤全 active（`user_deleted`）＋稽核 `delete`＋reload。200 `data: null`。

## 6. `DELETE /systemManage/batchDeleteUser`

- Body：`{ ids: number[] }`（去重；空陣列＝提前 no-op 0000）。id 升序取鎖；任一違規整批 rollback、拒因＝該筆之純 key
  （不帶 id）。稽核逐列 `delete`。200 `data: null`。

## 7. `POST /systemManage/restoreUser`

- Body：`{ id: number }`。鎖已刪列（查無→`notFound`）→同名活性（`userNameExists`）→同信箱活性（`userEmailExists`）→
  T(∅) ⊆ A→成對清 `deleted_*`；零回灌、status 保留。稽核 `restore`。200 `data: null`。

## 8. `POST /systemManage/kickUser`

- Body：`{ id: number }`。notFound→self（`cannotKickSelf`）→T ⊆ A。撤全 active、rotated 不動；事件 `admin_kick`；denylist
  `admin_kick`（7777）；稽核 `kick`。停用帳號可踢。200 `data: { revoked: number }`。

## 9. `POST /systemManage/resetUserPassword`

- Body：`{ id: number, password: string }`（管理員手輸或前端產密；後端不回傳密碼）。notFound→self
  （`cannotResetSelfPassword`）→T ⊆ A→政策（攜參）→冷卻（攜參）→UPDATE＋custody touch＋撤全 active
  （`password_reset`）＋稽核 `reset_password`。200 `data: null`。

## 10. `POST /systemManage/updateUserSessionPolicy`

- Body：`{ id: number, sessionPolicy: SessionPolicy }`（值域外→`sessionPolicyInvalid`）。notFound→T ⊆ A→與現值相同＝no-op。
  改 single 不即時踢。稽核 `update`。200 `data: null`。protected 端點（super-only、結構性）。

## 既有 `POST /systemManage/unlockLogin`（004；本刀接 UI＋帳號維套規則）

- Body：`{ dimension: 'user' | 'ip', userName?: string, ip?: string }`（既有契約不變）。帳號維：標的存在且 T ⊆ A（5003）；
  IP 維不套。UI＝user 頁頁首 modal（`user:unlock` gating）。
