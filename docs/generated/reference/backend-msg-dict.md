<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/backend-msg-dict — 拒因字典（機器生成）

來源＝base-web/src/locales/langs/zh-tw.ts＋base-web/src/locales/langs/en-us.ts 之 backend.* 鍵樹（generate 重算；rev4:B-007／rev4:FR-014、全鏈零手維）。

| key | zh-TW | en-US |
|---|---|---|
| auth.login.failed | 帳號或密碼錯誤 | Incorrect username or password |
| auth.session.kicked | 您的帳號已在其他裝置登入，此工作階段已結束 | Your account signed in elsewhere; this session ended |
| auth.session.reLogin | 請重新登入 | Please log in again |
| auth.token.expired | 登入已逾時，正在重新取得授權 | Session expired, refreshing |
| biz.auth.captchaRequired | 請完成圖形驗證碼後再試 | Please complete the captcha and try again |
| biz.auth.locked | 嘗試次數過多，請稍後再試 | Too many attempts; please try again later |
| biz.auth.notSupported | 該功能尚未開放 | This feature is not available yet |
| biz.systemSettings.invalidValue | 設定值不合法（型別不符、超出範圍或非允許選項） | Invalid setting value (wrong type, out of range or not an allowed option) |
| biz.systemSettings.notFound | 找不到指定的設定鍵 | The specified setting key was not found |
| biz.user.passwordViolation.forbidUsername | 不可與使用者名稱相同 | must not be identical to the user name |
| biz.user.passwordViolation.maxBytes | 位元組數超過上限 | byte length exceeds the limit |
| biz.user.passwordViolation.maxLength | 長度超過政策上限 | length exceeds the policy maximum |
| biz.user.passwordViolation.minLength | 長度未達政策下限 | length below the policy minimum |
| biz.user.passwordViolation.requireDigit | 須包含數字 | must contain a digit |
| biz.user.passwordViolation.requireLowercase | 須包含小寫字母 | must contain a lowercase letter |
| biz.user.passwordViolation.requireSpecial | 須包含特殊符號 | must contain a special character |
| biz.user.passwordViolation.requireUppercase | 須包含大寫字母 | must contain an uppercase letter |
| common.listSeparator | 、 | ,  |
| common.success | 操作成功 | Operation successful |
| system.forbidden | 沒有權限執行此操作 | You do not have permission to perform this action |
| system.internal | 系統發生內部錯誤，請稍後再試 | An internal error occurred. Please try again later |
| system.notFound | 找不到請求的資源 | The requested resource was not found |
