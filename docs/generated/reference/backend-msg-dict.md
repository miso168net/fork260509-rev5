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
| biz.ipRule.conflict | 相同網段與類型的規則已存在 | A rule with the same network and type already exists |
| biz.ipRule.invalidCidr | 網段格式不正確 | Invalid network address format |
| biz.ipRule.invalidRuleType | 規則類型不正確 | Invalid rule type |
| biz.ipRule.notFound | 找不到指定的規則，或其狀態不允許此操作 | The rule was not found, or its state does not allow this action |
| biz.ipRule.selfLock | 此規則會使你目前的連線被阻擋，已拒絕寫入 | This rule would block your current connection; the change was rejected |
| biz.menu.constantParent | 常量選單僅能掛在常量父選單之下 | A constant menu can only be placed under a constant parent menu |
| biz.menu.cycleDetected | 不可將選單移至自身或其子孫之下 | A menu cannot be moved under itself or its descendants |
| biz.menu.hasChildren | 選單下尚有子項，請先處理子項 | This menu still has child items; please handle the child items first |
| biz.menu.menuTypeImmutable | 選單類型建立後不可修改 | Menu type cannot be changed after creation |
| biz.menu.nameRequired | 選單名稱不可為空 | Menu name must not be null |
| biz.menu.notFound | 選單不存在 | Menu not found |
| biz.menu.parentNotFound | 父層選單不存在或已刪除 | Parent menu does not exist or has been deleted |
| biz.menu.protectedMenu | 受保護選單，不可刪除 | Protected menus cannot be deleted |
| biz.menu.restoreConflict | 同名路由已有生效選單，無法復原 | An active menu with the same route name already exists; cannot restore |
| biz.menu.routeNameExists | 路由名稱已存在 | Route name already exists |
| biz.menu.routeNameImmutable | 路由名稱建立後不可修改 | Route name cannot be changed after creation |
| biz.menu.routeNameInvalid | 路由名稱格式不正確（僅允許字母、數字、底線、連字號，最長 100 位） | Invalid route name (letters, digits, underscore and hyphen only, up to 100 characters) |
| biz.role.cannotDeleteSelfRole | 不能刪除目前登入使用者所屬的角色 | You cannot delete a role assigned to your own account |
| biz.role.cannotDisableSelfRole | 不能停用目前登入使用者所屬的角色 | You cannot disable a role assigned to your own account |
| biz.role.codeExists | 角色編碼已存在 | The role code already exists |
| biz.role.codeImmutable | 角色編碼建立後不可修改 | The role code cannot be changed after creation |
| biz.role.codeInvalid | 角色編碼格式不正確（僅允許字母、數字、底線，最長 64 位） | Invalid role code (letters, digits and underscore only, up to 64 characters) |
| biz.role.inUse | 該角色仍掛有使用者，不可刪除 | The role still has users assigned and cannot be deleted |
| biz.role.nameRequired | 角色名稱不可為空 | Role name must not be null |
| biz.role.notFound | 角色不存在 | The role was not found |
| biz.role.protectedRevoke | 存在受保護的授權，無法撤銷 | Protected policies cannot be revoked |
| biz.role.seededProtected | 系統內建角色，不可刪除 | Built-in system roles cannot be deleted |
| biz.role.superCannotDisable | 超級管理員角色不可停用 | The super administrator role cannot be disabled |
| biz.systemSettings.invalidValue | 設定值不合法（型別不符、超出範圍或非允許選項） | Invalid setting value (wrong type, out of range or not an allowed option) |
| biz.systemSettings.notFound | 找不到指定的設定鍵 | The specified setting key was not found |
| biz.throttle.invalidUnlockTarget | 解鎖對象不正確 | Invalid unlock target |
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
