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
  userGender?: string }`（模糊欄空字串＝未設）。★**過濾面恰此四欄**（`userName`／`nickName`／`status`／`userGender`）——
  搜尋卡上的手機／信箱兩欄不在其內，見 §12 已知態。
  ★本型的 `nickName` **刻意不帶 `| null`**（勿比照 §3／§4 的同名欄「順手補齊」）：它是模糊過濾字串、只有「有值／未設」
  兩態，後端以 `q.nick_name.filter(|v| !v.is_empty())` 把空字串當未設；標上 `| null` 會憑空多出一個沒有語意的態。
- `UserList`＝`PageRes<UserRecord>`（共用分頁信封；現役 `id ASC`）。

> ★**2026-08-28 勘誤（U1 邊界、主線工程自決）**：`nickName` 原寫作非可空 `string`，係落字之誤——本檔 §3 addUser 之 `nickName?`（選填、空字串→NULL）、DB `sys_user.nick_name`（nullable=YES）、rev5 既有同族欄慣例（`Api.RoleAdmin` 之 `roleMemo: string | null`）與 rev4 自身 typing（`nickName?: string | null`）四者一致指向可空，且照原字面落地就得在 handler 端捏一個空字串當值（＝rev4 的空字串摺疊形，research R2 明列不帶回）。故訂正為 `string | null`；碼面 `handler/user.rs` 之 `Option<String>` 為正、無須改。

## 1. `GET /systemManage/getUserList`

- Query：`UserSearchParams`。200 `data: UserList`（現役、含 status 停用者；已刪不含）。

## 2. `GET /systemManage/getDeletedUsers`

- Query：`{ current, size }`。200 `data: UserList`（`deleted_at IS NOT NULL`；`deleted_at DESC, id DESC`；`roles` 恆 `[]`）。

## 3. `POST /systemManage/addUser`

- Body：`{ userName: string, password: string, nickName?: string | null, userGender?: string | null, userPhone?: string | null,
  userEmail?: string | null, status?: UserStatus, roleIds?: number[], userMemo?: string | null }`（空字串→NULL；status 預設 `'1'`；
  roleIds 預設 `[]`）。
- 守門序：形制（`userNameInvalid`）→現役唯一（`userNameExists`／`userEmailExists`，含 23505 兜底）→信箱格式
  （`userEmailInvalid`）→`roleIds` 存在且未軟刪（`roleNotFound`）→N ⊆ A（5003）→政策（`passwordPolicy` 攜參）→
  冷卻對 (新 id, operator) 首寫免判→INSERT＋指派＋custody touch＋稽核 `add`。
- 200 `data: { id: number }`。

## 4. `POST /systemManage/updateUser`

- Body：`{ id: number, nickName?: string | null, userGender?: string | null, userPhone?: string | null, userEmail?: string | null,
  status?: UserStatus, roleIds?: number[], userMemo?: string | null }`（三態：缺席＝不動、null＝清空；`userName` 出現即拒
  `userNameImmutable`；`roleIds`＝期望全集全量替換）。
  > ★**2026-08-29 勘誤（本刀 U6 邊界）**：`nickName` 原寫作 `string`，與同 Body 其餘四個可空欄不一致，且與本節散文自己寫的
  > 「三態：缺席＝不動、**null＝清空**」相抵——後端該欄是 `Option<Option<String>>`（`handler/user.rs` 之 `UpdateReq`），
  > null 這一態本來就收得到。與 §共用型那筆（2026-08-28、U1 邊界）**同一欄同源落字**，此處補齊。
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

- Body：`{ id: number }`。鎖已刪列（查無→`notFound`）→T(∅) ⊆ A→同名活性（`userNameExists`）→
  同信箱活性（`userEmailExists`）→成對清 `deleted_*`；零回灌、status 保留。稽核 `restore`。200 `data: null`。
  ★**次序勘誤（本刀 U5 as-built）**：原文把 `T(∅) ⊆ A` 排在兩格業務守門之後，與八支寫端的通則序
  （①notFound ②seed ③self ④no-escalation ⑤業務）相反。生產態下 `T ≡ ∅`（刪除交易已硬刪全部指派、
  復原零回灌）⇒ ④恆過，兩序在**任何生產可達輸入**下的回應逐位元同形，唯合成態（已刪列仍掛指派）
  才分得出。統一取通則序，以免八支裡留一支需要另記的例外。

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

- Body：`{ dimension: 'user' | 'ip', userName?: string, target?: string }`（既有契約不變）。帳號維：標的存在且 T ⊆ A（5003）；
  IP 維不套。UI＝user 頁頁首 modal（`user:unlock` gating）。
  > ★**2026-08-29 勘誤（本刀 U7 邊界）**：來源維標的欄原寫作 `ip`，係落字之誤——**本節自陳「既有契約不變」，
  > 而既有契約的欄名是 `target`**。三方交叉查證一致：①`specs/004-ip-trust-anchor/contracts/wire-throttle-unlock.md`
  > 請求表三欄逐字為 `dimension`／`userName`／`target`②後端 DTO `handler/throttle.rs` 之 `UnlockLoginReq` 為
  > `target: Option<String>`＋`#[serde(rename_all = "camelCase")]` ⇒ 上 wire 即 `target`③rev4 前端同族型亦為 `target`。
  > ★**照 `ip` 落地會是靜默錯**：請求形制合法、後端只看到「來源維標的缺席」⇒ 恆回 `2222`，畫面上看起來像是
  > 「這個 IP 沒被鎖」而非「你送錯欄名」。本刀 U7 的實作取 `target`（正確側），型 doc 已就地記載本勘誤。

## 12. 已知態（本刀收官時的 as-built 落差，非待辦缺件）

- **搜尋卡的手機／信箱兩欄填了不會濾**：`user-search.vue` 渲染 `userPhone`／`userEmail` 兩個輸入欄（並掛 pattern 驗證），
  但 §1 的過濾面恰四欄、後端對那兩欄沉默忽略。本刀 U6 的接線選擇**逐欄顯式只送四欄**（而非整包散開），
  以免「畫面可填」看起來像「後端會濾」；但欄位本身仍在畫面上。
  ★**這對 rev4 是行為回退**：rev4 前端送整包 `searchParams`、rev4 後端的 `UserSearchParams` 確收
  `user_phone`／`user_email` 兩欄 ⇒ 在 rev4 那兩欄是真的會濾的。rev5 把過濾面收窄成四欄是 rev5 拍板；
  收窄之後留下兩個外觀正常、行為已失效的入口，是接線層的落差。
  ★**本刀結構性無法自修**：`user-search.vue` 不在憲法 §III.2 用途 (v) 的範圍欄內（明文零改動、任何 diff 即紅），
  擅改即破軌道授權邊界 ⇒ 已立 **B-143**。★**T070 的 CDP 三方對照請把本項列入已知態排除清單**，
  免得被當成「rev5 沒做完」重新發現一次。
