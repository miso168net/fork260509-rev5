# Contract — 個人中心二支端點（Authed、零 seed）

> 命名空間 `Api.UserCenter`（`base-web/src/typings/api/rev5-user-center.d.ts`；fetcher `service/api/rev5-user-center.ts`）。
> 兩支 `Protection::Authed`（登入即可用、不進 casbin）；標的恆＝`claims.uid`（body 不帶 id）。

## 1. `GET /userCenter/getPasswordPolicy`

- 200 `data: PasswordPolicyView`＝`{ minLength: number, maxLength: number, requireDigit: boolean, requireLowercase: boolean,
  requireUppercase: boolean, requireSpecial: boolean, forbidUsername: boolean }`（七鍵投影；不含 interval；缺鍵 fail-default
  與後端驗證點同源）。
- 前端 `hooks/business/pwd-policy.ts::buildPolicyRules(view)` → naive 表單 rules；取不到靜默降 required。

## 2. `POST /userCenter/changePassword`

- Body：`{ oldPassword: string, newPassword: string, confirmPassword: string }`。
- 步序（任一步拒即零寫入）：帳號存在且活性（`notFound`）→兩次一致（`passwordConfirmMismatch`）→節流 precheck
  （`changePasswordThrottled`，在舊密驗證前）→舊密正確（否則 INCR＋`oldPasswordMismatch`）→新≠舊（`passwordSameAsOld`）→
  政策（`passwordPolicy` 攜參）→冷卻對 (self, self)（`pwdSetTooFrequent` 攜參）→UPDATE＋custody touch＋
  `revoke_others_of_user(keep=claims.sid)`＋事件 `password_changed`＋稽核 `change_password`→commit→清桶。
- 200 `data: null`；其他裝置下一次請求 8888；當前裝置不受影響。
