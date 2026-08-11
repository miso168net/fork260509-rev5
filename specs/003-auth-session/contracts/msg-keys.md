# 契約 — msg key 與 i18n 字典（Lint24 面）

後端 `msg` 載**穩定 i18n key**（語言無關、不在地化；憲法 §I.3）；前端經
``$t(`backend.${msg}`, msg)`` 轉譯、未命中回原文 fallback。

## 本刀新增 6 鍵（三語譯文）

| key | 構造形 | zh-TW | zh-CN | en-US |
|---|---|---|---|---|
| `auth.login.failed` | 固定變體（`AppError::LoginFailed`） | 帳號或密碼錯誤 | 用户名或密码错误 | Incorrect username or password |
| `auth.token.expired` | 固定變體（`TokenExpired`） | 登入已逾時，正在重新取得授權 | 登录已过期，正在重新获取授权 | Session expired, refreshing |
| `auth.session.kicked` | 固定變體（`ModalLogout`） | 您的帳號已在其他裝置登入，此工作階段已結束 | 您的账号已在其他设备登录，当前会话已结束 | Your account signed in elsewhere; this session ended |
| `biz.auth.notSupported` | Biz 構造點 | 該功能尚未開放 | 该功能暂未开放 | This feature is not available yet |
| `biz.auth.captchaRequired` | Biz 構造點 | 請完成圖形驗證碼後再試 | 请完成验证码后再试 | Please complete the captcha and try again |
| `biz.auth.locked` | Biz 構造點 | 嘗試次數過多，請稍後再試 | 尝试次数过多，请稍后再试 | Too many attempts; please try again later |

★rev4 對應鍵名為 `auth.login.locked`／`auth.login.captchaRequired`——rev5 **正規化**為
`biz.auth.*`（Biz 構造點鍵一律 `biz.<domain>.<case>`）；前端 captcha 軟區判斷式拿 `msg` 字面
比對區分兩態，**須用新名**（research R3-4）。

## 22 鍵全集與算術自證

插入後三語 backend 樹各 **22 鍵**：

- **後端實發 13**＝002 既有 7（`common.success`／`system.internal`／`system.notFound`／
  `system.forbidden`／`auth.session.reLogin`／`biz.systemSettings.invalidValue`／
  `biz.systemSettings.notFound`）＋本刀 6。
- **前端內部白名單 9**＝`biz.user.passwordViolation.*` 八鍵＋`common.listSeparator`
  （★後端恆不發）。
- ⇒ **13＋9＝22**：零孤兒鍵、零缺譯、白名單 ∩ 實發＝∅ ⇒ Lint24 三向斷言（子集／白名單存在性／
  白名單腐化）恰好成立。

★`auth.session.reLogin`（8888 現行鍵）**已存在、本刀不動但不得漏列**——兩語鍵集閘逐鍵比對，
漏一即紅。

## 機器閘落點

| 閘 | 規則 | 本刀動作 |
|---|---|---|
| Lint24 後端抽取面 | 抽**三面**：①`Biz`／`BizData` 構造點字面 ②名冊常數間接形 ③`error.rs` 之 `fn key()` match 臂 | 三個固定鍵落面③、★三個 Biz 鍵落面①（**原稿誤記為「不在抽取面」**）⇒ Biz 鍵 MUST 以 `Cow::Borrowed("字面")` 構造，**非字面即 fail-loud**（防恆綠洞）；兩語鍵集閘與 contract case 逐鍵為補強、非唯一守 |
| `compute_msg_dict_rows` | `set(zh) != set(en)` → fail-loud | 22=22 通過；六新鍵須**同 commit** 補進 `zh-tw.ts` 與 `en-us.ts` |
| `_locales_have_backend_tree` | 對 `MSG_DICT_LOCALES` 兩支逐支要求存在一行 **fullmatch** `\s*backend:\s*\{` | ★插入行必須是獨佔一行的 `  backend: {`（不可 `backend: { common: {` 同行，否則謂詞不成立、豁免不到期、字典不生成） |
| `DAY1_EXEMPTIONS["gen.msg_dict"]` | 到期即紅 | en-us 一插即謂詞成立 ⇒ **同 commit 拔項**＋跑 `generate`；★拔後成空表，須先驗 `_assert_day1_table`／`DAY1_EXEMPT_SCOPE` 與五處消費點的空表安全 |
| `backend-msg-dict.md` | generate 重算 | 恰 **22 列**（表頭 `| key | zh-TW | en-US |`） |
| `pnpm typecheck` | `app.d.ts` 之 `backend` **必填**型節 | 同時守住 `zh-cn.ts` 結構（兩檔皆標 `App.I18n.Schema`）；★zh-cn 譯文**品質**無機器守＝已知態 |

`MSG_DICT_LOCALES` 維持兩支（zh-TW／en-US）不擴——zh-cn 不在字典鏈射程（B-030 子項），其結構
由必填型節＋typecheck 免費守。
