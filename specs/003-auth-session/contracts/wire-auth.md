# Wire 契約 — auth 面（9 條）

權威＝base-web typings（憲法 §I.3 權威序 1）。信封恆 `{data, code, msg}`、`code` 為 string、
業務錯誤走 **HTTP 200**。路徑不帶 `/api` 前綴（nginx strip）。型別細節見 `../data-model.md`、
不重複。

碼表共用：`0000` 成功／`1000` 登入失敗（`auth.login.failed`）／`2222` 業務驗證（Biz 鍵）／
`3333` access 過期（`auth.token.expired`）／`7777` 被踢（`auth.session.kicked`）／`8888` 會話
失效（`auth.session.reLogin`）／`4040` 路徑或動詞不存在（`system.notFound`、HTTP 404）／
`5000` 內部（HTTP 200）。★除 `4040`→404、`5003`→403 外一律 HTTP 200。

## POST /auth/login（Public）

| 面 | 內容 |
|---|---|
| 授權 | Public（不掛 `enforce_mw`） |
| 請求 | `{userName, password, captchaId?, captchaCode?}`（後二為軟區才驗；非軟區時★完全忽略、不驗不消耗） |
| 成功 | `data: {token, refreshToken}`＝`Api.Auth.LoginToken` |

| 拒因 | code | msg key | 備註 |
|---|---|---|---|
| 帳密錯／帳號不存在／已停用 | `1000` | `auth.login.failed` | ★三態 collapse 同碼（不洩存在性）；落失敗列 |
| userName／password 超限 | `1000` | `auth.login.failed` | 形制閘、零稽核零 argon2 零計數桶 |
| 軟區（失敗 2–4）缺／錯／過期／重放 captcha | `2222` | `biz.auth.captchaRequired` | argon2 前擋、零列零桶；★該題已耗須重取 |
| 鎖定（失敗 ≥5） | `2222` | `biz.auth.locked` | argon2 前擋、零列零桶 |
| `session_idle_timeout` 缺失／commit 失敗 | `5000` | `system.internal` | 不落稽核列 |

## POST /auth/refreshToken（**Public**）

Public 理由：設 Authed 則過期 token 永遠換不了。請求 `{refreshToken}`；成功 `data:
{token, refreshToken}`（新對）。

| 情境 | code | 備註 |
|---|---|---|
| `active`＋idle 未逾時 | `0000` | rotate（舊列→`rotated`、插新 `active`）＋寫 grace 30s |
| `rotated`＋grace 命中（≤30s） | `0000` | ★冪等回**既發的同一對** |
| `rotated`＋grace miss | `8888` | ★唯一觸發 reuse：撤全鏈＋落 `session_event(reuse)` |
| `revoked`＋denylist reason==`kicked` | `7777` | modal「你已在他處登入」 |
| `revoked`＋reason==`revoked` **或鍵缺席** | `8888` | ★靜默、不落事件、不重複撤（status 即權威） |
| `active`＋idle 逾時 | `8888` | 僅首次落 `session_event(idle)`；★不寫 denylist |
| 驗章失敗（過期／垃圾／錯簽）／查無列 | `8888` | ★**絕不 `3333`**——否則前端自動 refresh 死迴圈 |

## POST /auth/logout（**Public**）

Public 理由：設 Authed 則 token 一壞就再也撤不掉那條 session。請求 `{refreshToken}`；
成功 `data: null`。

| 情境 | code | 備註 |
|---|---|---|
| 驗章成功 | `0000` | 該列→`revoked`＋denylist(revoked、refresh 全壽命)＋落 `session_event(logout)` |
| 驗章失敗（垃圾／過期）／查無列 | `0000` | ★冪等 no-op、不落事件——回異碼＝提供 token 有效性 oracle |

## GET /auth/getUserInfo（Authed）

成功 `data`＝`Api.Auth.UserInfo`，四欄皆必填：`userId`（★DB i64 → 序列化為字串）／`userName`
（＝`nick_name` fallback `user_name`；★碼中零帳號字面）／`roles`（DB-fresh）／`buttons`
（Casbin `button` 維度 `get_filtered_policy` 枚舉；★非 `enforce*`、不觸單一判定進入點守恆）。

未認證面：標頭缺席／非 Bearer／簽章不符／已撤銷→`8888`；access 過期→`3333`；被踢→`7777`。

## GET /auth/loginCaptcha（Public）

| 面 | 內容 |
|---|---|
| 請求 | ★**必帶** `?userName=`（challenge 綁帳號的前提） |
| 成功 | `data: {captchaId, captchaImg}`；`captchaImg`＝完整 `data:image/png;base64,…` |
| 存在性 | ★對**任意** userName 一律發題（含不存在帳號）＝零存在性查詢、零洩漏 |

| 拒因 | code | 備註 |
|---|---|---|
| userName 超限 | `1000` | ★與登入端點**同形**閘（零新碼零新 key） |
| 產圖／簽章內部失敗 | `5000` | ★此路是 captcha 字型涵蓋自證的失效出口 |
| 缺 `userName` query | `1000` | Query rejection 亦須成三欄信封 |

## POST /auth/{sendCaptcha,codeLogin,register,resetPwd}（Public × 4）

四端點共用一支 `not_supported_stub()`：一律 `2222`＋`biz.auth.notSupported`、`data: null`、
零副作用（不落任何表、不查 DB）。前端三張表單改打此 stub 以消滅假成功 toast；第四流程
（自助頁手機驗證）整頁未建、不在本刀。

★contract case 注意：四支同形 ⇒ 逐 case 錯配自證（case_key 配到別條 path 須紅）在其上會退化，
tasks 須指定區別手法（如各自斷言 path 專屬的 case_key 對映，而非只比信封）。
