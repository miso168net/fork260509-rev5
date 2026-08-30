# Contract — 本刀新增 i18n 鍵（候選權威；逐字面於 i18n 單元定稿、Lint24 對賬）

> backend 樹：純 key 家族走 `AppError::Biz`；唯二攜參鍵走 `AppError::BizData`（前端以 `translateBackendMsg` 顯 msg、
> 明細由頁面依 `data` 渲染；違規碼經前端內部詞彙表 `biz.user.passwordViolation.*` 八鍵〔既有、Lint24 白名單〕轉人話）。
> 四處同 commit：zh-cn／en-us `backend:` 樹（既有授權 (ii)）＋`app.d.ts` backend 型節（(iii)）＋`zh-tw.ts`（backend 鍵）。
> page 樹三處（zh-cn／en-us／app.d.ts；zh-tw 不塞）。

## `backend.biz.user.*`（新開子樹）

| 鍵 | 觸發 | zh-cn 藍本 | en-us 藍本 |
|---|---|---|---|
| `notFound` | 標的不存在或已軟刪 | 用户不存在 | User not found |
| `userNameExists` | 現役同名 | 用户名已存在 | Username already exists |
| `userNameInvalid` | 形制不符 | 用户名格式不正确 | Invalid username format |
| `userNameImmutable` | updateUser 帶 userName | 用户名不可修改 | Username cannot be changed |
| `userEmailExists` | 現役同信箱（不分大小寫） | 邮箱已被使用 | Email already in use |
| `userEmailInvalid` | 信箱格式 | 邮箱格式不正确 | Invalid email format |
| `seededProtected` | 三帳號不可刪／id 1 解超管指派 | 内置账号受保护 | Built-in account is protected |
| `superCannotDisable` | id 1 停用 | 超级管理员不可停用 | Super administrator cannot be disabled |
| `cannotDeleteSelf` | self 刪 | 不能删除自己 | Cannot delete yourself |
| `cannotKickSelf` | self 踢 | 不能踢除自己 | Cannot kick yourself |
| `cannotEditSelfRoleOrStatus` | self 帶 status／roleIds（★self「不得停用自己」由本鍵承載——`status` 出現即拒故無獨立停用鍵） | 不能修改自己的角色或状态 | Cannot change your own roles or status |
| `cannotResetSelfPassword` | self 用管理頁重設 | 请到个人中心修改自己的密码 | Change your own password in the user center |
| `roleNotFound` | roleIds 含不存在／已刪角色 | 角色不存在 | Role not found |
| `sessionPolicyInvalid` | 三值外 | 会话策略无效 | Invalid session policy |
| `passwordConfirmMismatch` | 兩次不一致 | 两次输入的密码不一致 | Passwords do not match |
| `oldPasswordMismatch` | 舊密錯 | 旧密码不正确 | Old password is incorrect |
| `passwordSameAsOld` | 新＝舊 | 新密码不能与旧密码相同 | New password must differ from the old one |
| `changePasswordThrottled` | 舊密猜測超限 | 尝试次数过多，请稍后再试 | Too many attempts, please try again later |
| `passwordPolicy`（攜參 `{violations}`） | 政策違規 | 密码不符合安全策略：{violations} | Password does not meet the policy: {violations} |
| `pwdSetTooFrequent`（攜參 `{remainingSeconds}`） | 冷卻未滿 | 密码设置过于频繁，请 {remainingSeconds} 秒后再试 | Password was set too recently, retry in {remainingSeconds}s |

## `backend.auth.session.*`（既有子樹＋1）

| 鍵 | 觸發 | zh-cn | en-us |
|---|---|---|---|
| `kickedByAdmin` | denylist reason `admin_kick`→7777 | 此会话已被管理员结束，请重新登录 | This session was ended by an administrator, please sign in again |

`auth.session.kicked`（單一會話）文案不動。

## 前端 `page.manage.user.*`（既有 **19** 葉鍵＋補至射程；兩語同位、zh-tw 不塞）

> ★**2026-08-30 勘誤（本刀收刀前 final holistic）**：原寫「既有 21 葉鍵」係落字之誤——同刀的 research R11
> 與 tasks T004 之前端基線量測已機器複核為**兩語各 19**（U0 量測基準表逐字），本處未被同批掃到。

新增候選：`userMemo`／`sessionPolicy`＋`sessionPolicyOption.{inherit,single,multi}`／`sessionPolicyHint`（僅超管可改）／
`roles`／`showDeleted`／`restore`／`confirmRestore`／`restoreHint`（復原後需重新指派角色）／`restoreSuccess`／`kick`／
`confirmKick`／`kickSuccess`／`resetPwd`／`resetPwdTitle`／`newPassword`／`resetPwdSuccess`／`randomPassword`／
`unlockLogin`／`unlock.{dimension,user,ip,userName,ipAddress,success}`／`passwordHint`／`deleteSuccess`／
`pwdGen.{title,length,generate,copy,copied,apply}`。實數於 i18n 單元定稿、`app.d.ts` `App.I18n.Schema.page.manage.user` 型節同步。

## 前端 `page.userCenter.*`（新 top-level 命名空間；Amendment (vi) 具名）

`title`／`password.{title,oldPassword,newPassword,confirmPassword,submit,success,hint}`。

> ★**as-built 註（本刀 U7）**：其中 `title`（頁標題）**未設**——個人中心的頁標題已由既有 `route['user-center']`
> 承載（兩語皆在），另立同義鍵即多一枚零消費者的鍵與第二份說法。餘七鍵照列落地。
> ★另註：`page.manage.user.passwordHint` 落在 `page.manage.user.*` 的**直屬層**（非 `pwdGen.*` 子樹）——
> 依本檔列序，它是 `pwdGen.{...}` 的同級兄弟。

## 前端內部詞彙表（既有、零新增）

`biz.user.passwordViolation.{minLength,maxLength,maxBytes,requireDigit,requireLowercase,requireUppercase,requireSpecial,forbidUsername}`＋
`common.listSeparator`——由前端把 `violations[]` 轉人話清單（Lint24 白名單九鍵、後端不得作 msg 發出）。
