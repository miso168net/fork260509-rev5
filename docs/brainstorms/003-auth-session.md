# 003-auth-session — auth 域整批 brainstorm（階段 0）

- 日期：2026-08-09｜狀態：五題開場拍板＋三題追加拍板＋設計七節過 user 核可；同日**覆核輪收官**——
  六路唯讀搜證（opus workflow、144 findings）＋grilling 一問一答十三題逐題拍板（§1.2），
  設計各節已依覆核結論就地修訂；下一步＝**手動** `/speckit-specify`（本檔為其 input；
  不自動觸發——否則 feature branch pre-hook 不跑、spec 落 default）。
- 一句話：把 base-web fork 原版 service 已在呼叫的認證／路由端點補齊到終態——真登入、
  DB-stateful rotation、帳號維節流、圖形驗證碼、dynamic 選單、後端 msg 前端轉譯，
  並開憲法 §III.2 的**首批 ★ 軌道**（四條）＋§I.7 首批行為島入憲。
- 交付價值：rev5 第一次端到端可見（瀏覽器真登入 → 側邊欄由後端 casbin 過濾生成、
  錯誤訊息顯人話），且 rust-api release profile 第一次真的跑得動（`dev_identity` 整檔汰換後
  debug／release 行為一致；★base-web 無 prod build target，「release 可跑」不涉前端）。

## 1. 開場五題拍板紀錄（user 拍板 2026-08-09）

| 題 | 拍定 | 要點 |
|---|---|---|
| redis 進場否 | **進場；AppState 兩欄→五欄（覆核修正）** | `cache: Option<SessionCache>`＋`jwt: JwtConfig`＋`captcha_secret: String` 三欄同一 ADR 一次授權——簽 JWT 與驗題秘鑰是本刀硬相依，原「開第三欄」低估翻案幅度；測試 `None`、production 恆 `Some`（boot 建連失敗即 fail-loud panic，不靜默退 None）。翻案 `state.rs`「恰兩欄」拍板須立 ADR、其檔頭拍板註（恰好點名這三個欄名）同批改寫。不進場的代價＝`sys_token` 缺 `last_activity` 欄 → additive DDL → 本刀變「帶 migration 的刀」。 |
| 未認證回哪個碼 | **三分，比 rev4 更精確** | exp 過期→3333（前端自動 refresh、無感續期）／標頭缺席・非 Bearer・簽章不符・已撤銷・refresh 鏈失效→8888／被踢下線→7777（modal）。rev4 把「缺席」也判 3333，未登入者每次白跑一輪注定失敗的 refresh。★前端三碼集合（.env 之 LOGOUT／MODAL_LOGOUT／EXPIRED_TOKEN _CODES）皆 upstream 原生值、零 env 修改即吻合。 |
| B-022 替代登入四流程 | **沿用 rev4:ADR 0029 的誠實 stub** | 三張表單各改 2 行改打後端 stub（恆 `2222 biz.auth.notSupported`），表單與入口原樣保留。★首答為「維持現狀＋立 ADR」，在 captcha 拍定要開 ★ 軌道後改判——原推薦理由（不為拆三顆按鈕開軌道）之前提消失。第四流程（自助頁手機驗證）整頁未建、不在本刀（§2 表 B-022 判半消化）。 |
| B-029 圖形驗證碼 | **進，一次做完** | 含「答對但登入失敗即自動換題」那半條。決定性依據＝001 baseline 已 seed `login_throttle_captcha_after=2`／`ip_captcha_after=10`，節流本就是三區狀態機，不做 captcha 軟區即塌。 |
| B-047 的 405 裸 body | **回 4040 信封＋HTTP 404** | 三候選中**唯一零修憲**——不是新增例外，是消掉一個未入文的例外（修完例外集仍恰 2：/health、/metrics），且 §I.3 自書「新需求優先 reuse 既有碼」。代價＝丟 `allow` 標頭與 405 語意；辯護＝`ROUTES` 以 (path, method) 為一條，該組合在註冊表層確實不存在。★「4040 涵蓋動詞不符」是對既有碼表的新解讀（原註解自書 path fallback 專用）＝立 ADR 記解讀、正面回應 B-047 條目自書的「硬塞 4040 有語意張力」；不順手補條文（會把 405 語意寫進凍結面）。 |

### 1.1 追加拍板三題（同日）

| 題 | 拍定 | 要點 |
|---|---|---|
| 切法 | **一刀到底、不拆** | user 理由＝rev4 藍本齊備、整合風險低於綠地。曾評估拆三刀（認證核心／節流＋captcha／dynamic menu）並棄。 |
| 軌道名機器化 | **放進同一刀** | `tools/fork-delta-lint.py` 現只驗新增型 `[rev5-inline` token 存在與修改型 `原行:` 正規化相符（★修改型甚至不要求 token）——**軌道名寫什麼都過**。實作形經覆核輪細化，見設計 §5。 |
| en-us backend 樹 | **做——經覆核輪擴為甲案 rev4 全形（§1.2 R2）** | 原案「只插 en-us.ts」機械上不可能單獨成立（`App.I18n.Schema` 型別連鎖：en-us.ts→app.d.ts→zh-cn.ts）。解除 `DAY1_EXEMPTIONS["gen.msg_dict"]` 不變，其理由欄明寫「需開第一個 ★ 軌道，本刀不開」——本刀正是那一刀。 |

### 1.2 覆核輪拍板十三題（同日；grilling 一問一答，六路搜證為證據基礎）

| # | 題 | 拍定 |
|---|---|---|
| R1 | §I.7 行為島入憲 | **同筆 Amendment 納入**：三軌道之外＋五座行為島（rotation／single-session／denylist 撤銷／idle 逾時／登入失敗節流）不變式條文同筆入 §I.7，1.2.0→1.3.0 一次到位——否則 `/speckit-plan` 憲法自查第 9 題當場擋、日後 fail 方向反轉無 MAJOR 閘。 |
| R2 | i18n 姿態 | **甲案 rev4 全形**：★I18N-WIRING 三用途——(i) request 層 `translateBackendMsg` 轉譯 2 處 inline（modal content＋toast，`$t` 帶原文 fallback）／(ii) en-us.ts＋zh-cn.ts 插 backend 樹（22 鍵；簡中照 rev4 鏡像重打）／(iii) app.d.ts backend **必填**型節。zh-tw.ts 補 6 鍵（rev5 新檔免軌道）。zh-cn 結構同步由必填型節＋`pnpm typecheck` 免費守、`MSG_DICT_LOCALES` 維持兩支不擴；zh-cn 翻譯內容品質無機器守＝已知態。★連帶新 ADR 收窄 ADR 0021 §3。 |
| R3 | LOGOUT-UX | **開 (i) 一用途**：user-avatar.vue 3 行 inline（onPositiveClick 改 async＋登出前 `fetchLogout` best-effort、失敗不阻斷）＋wrapper 新檔（免軌道）；(ii) reLogin toast 不開。`/auth/logout` 自此有真 UI 呼叫端、驗收從 UI 走通。 |
| R4 | AUTH-WIRING 粒度 | **沿 rev4 拆 (a)(b)(c) 三用途**（(c)＝hooks/business/captcha.ts 自成一用途）——授權邊界逐用途入憲、不靠讀者推測；成本＝憲法表多一列。 |
| R5 | 軌道名名冊射程 | **斷言只對修改型（帶 `原行:`）生效**；新增型 `NAME+` 檔頭標記不入冊（ADR 0021 款 1：純新增檔不觸 ★ 軌道、無軌道名可掛）。既有 `BACKEND-MSG-DICT+` 天然豁免、零遷就。 |
| R6 | .env 機器守 | **人工紀律＋記帳**：.env 改動手寫 `# [rev5-inline BASE-WEB-ADAPT] …` 標記（沿 rev4 六處 ADAPT 慣例）、ADR 明記「機器不強制、靠 review」；BACKLOG 立「fork-delta-lint 射程擴 .env*＋build/（含 # 註解支援）」新條目延後收。 |
| R7 | revoked 缺 denylist 語意 | **改良案（rev5 對 rev4 差異點）**：`sys_token.status=='revoked'` 本身即權威「被合法撤銷過」——缺 denylist（nil）回靜默 8888、不落事件、不重複撤；reuse 偵測**只保留給 `rotated` 且 grace miss**。denylist 純加速層，redis 狀態（TTL 短／故障／資料遺失）永不污染稽核帳。代價＝redis 丟失時被踢者拿 8888 而非 7777（解釋性降級、非安全降級）。 |
| R8 | redis AOF | **不開、記已知態**：維持 compose RDB 預設。實際暴險受 R7 封頂——revoked 在 PG 為權威、鍵丟失時換發必被擋，復活面＝被踢者既有 access token 直打 API 至自然過期（≤access TTL＝5 分鐘）。prod 化時由 B-019／部署刀重評。 |
| R9 | grace redis-only | **接受 rev4 形**：grace 住 redis（鍵＝`session:rotate-grace:{token_hash}`、值＝新對 JSON；sys_token 只存 hash＝結構上無 PG 退路）；ADR 明記「redis 故障期間多分頁使用者會被全域登出（重登即復原）」為已知降級後果。 |
| R10 | captcha nonce 降級 | **沿 rev4 拒絕不罰**：used 標記 SET NX 寫入失敗→該次登入拒絕（重放窗不存在）、但不消耗計數桶（不推進 ≥5 硬鎖）；列入 §3 降級方向表第四列。 |
| R11 | nginx 其餘 8 條限流 | **記已知態、延 B-019**：四支 stub 幾無成本；getConstantRoutes 有 DB 成本但 B-019 連信任錨一併治。（§4 的 CF 論證同步改寫為「自癒 vs 不自癒」。） |
| R12 | ip_confidence 字面 | **`nginx_peer`**（snake_case 新字面；語意＝nginx 注入的 X-Real-IP、未經信任判定）；B-019 接手時與 rev4 七態（trust/mod.rs）合併治理。 |
| R13 | LOGIN-CAPTCHA 用途 (ii) | **延後、本刀只開 (i)**：seed 密碼明文＝123456 已實證過得了 `REG_PWD`、且本刀零改密／建帳號端點＝(ii) formRules 放寬屬純前瞻授權（★軌道授權應對應實際需求）；日後改密刀 MINOR 加一列即補開。 |

覆核輪同批工程級自拍（回報備查；細節已融入設計各節）：
- **帳面更正**：`password_*` 鍵數實為 **8**（舊文 14／9 皆誤；16＝3 ip＋3 throttle＋8 password＋2 session 才自洽）；rev4 handler/auth.rs 生產段約 860 行；「憲法 §I.3 末條」→「§I.3 鎖定不變式『預設帳號』條」；typings 權威引用「§I.1」→「§I.3 權威序 1（範圍義務見 §I.1）」；rev4 DEVPROXY 全倉實為 5 處（src 內 2）。
- **★axios 側推論補全**（交接稿標最脆那條）：斷點＝`VITE_SERVICE_BASE_URL` 不在 `.env` 而在 `.env.test`／`.env.prod`（dev 實載 `.env.test`），推論鏈其餘各環皆有碼證據，殘餘不確定僅剩真 HTTP 往返一環——.env 改動全清單見設計 §5。
- **seed 密碼明文＝`123456`** 已離線實證（argon2 verify MATCH、＝upstream demo 值、三帳共用同一 PHC）；single-session 驗收前置＝先以 `updateSystemSetting` 翻 `single_session_default=on`（001 凍結 seed 是 schema-gate gate2 比對左源、不可動）。

## 2. K1／K2 承襲盤點（B-001 要求①）

| 條目 | 處置 | 本刀消費點 |
|---|---|---|
| K1-07 後端路由單檔＋三源一致 lint | 沿用 | `ROUTES` 4→16 條；動詞探測閘 table-driven、新 route 自動落入 |
| K1-27 登入未到位前先立最小授權骨架 | **解除** | 本刀接真 session，`auth/dev_identity.rs` 整檔汰換（該檔檔頭自述此路徑；enforce.rs 接點僅一處 cfg verify、汰換面極小，連帶清 `Bearer dev-super` 測試面） |
| K1-29 替代登入端點包＝後端 stub | 沿用 | 一支 `not_supported_stub()`、四端點共用、恆 2222 |
| K1-30 閒置逾時無狀態 sliding refresh | **不走**（已被 rev4:0033 翻案） | 直接上 stateful 終態，中繼態不重走；其「先打通最小形＋預埋 seam」分段手法教訓＝知情捨棄（§1.1 一刀到底拍板取代） |
| K1-31 auth 刀前端接線軌道 | 沿用 | 開 `★BASE-WEB-AUTH-WIRING`（三用途、沿 rev4 終態＝R4） |
| K1-33 會話生命週期 DB-stateful rotation 終態 | 沿用 | 設計 §3 全節 |
| K1-35 前端跨棧共用 refresh 承諾判不做 | 沿用（won't-fix） | alova 棧對真 auth 流 **dev 下** dormant；★release build 非 dormant（mockAdapter 僅 DEV、tokenRefresher 真打 refreshToken）→後端 grace 冪等是必需非保險 |
| K1-37 登入失敗節流合成終態 | **重審** | rev5 只做帳號維；來源維全景重述隨 B-019、非本刀漏做 |
| K1-38 節流負快取層終態 | 沿用 | `sys_login_attempt` 滑動窗為權威、redis 為 L1 負快取 |
| K1-40 登入表單圖形驗證碼接線軌道 | 沿用 | rev4:ADR 0040 開立時嚴限一用途，後由 rev4:011-user-admin 擴為二（憲法 §III.2 承襲指針記終態「二用途」）；rev5 本刀只開 (i)（R13），(ii) 延改密刀補開 |
| K1-42 dev／prod 同形 `/api` | 沿用（覆核輪補列） | .env 三檔拆 apifox mock 改 `/api`＋`VITE_HTTP_PROXY=N`（設計 §5 ADAPT 段） |
| K1-45 來源維度節流與計數下界不變式 | **不消費** | K1 初判為沿用；本刀知情降級（IP 維延 B-019），B-019 落地時終態整組照抄 |
| K1-53 使用者域狀態機與登入鎖內重驗 | 沿用 | login 第 5 步 lock-then-redecide |
| K1-65 自助頁路由恆附掛白名單 | **不消費** | rev5 自助頁整頁未建（`user-center/index.vue` 僅 7 行 `<LookForward />`） |
| K2-02（B-017） | 消化 | 設計 §3 |
| K2-05（B-020） | **半消化** | 帳號維節流落地（本刀唯一消費者＝login、老實記「login 專用實作」不宣稱通用 seam——閘存在≠生效，通用化與第二消費者隨 B-021）；per-IP 維延 B-019、條目續留 |
| K2-08（B-021） | **不消費** | rev5 無改密端點（自助頁未建），條目續留 |
| K2-09（B-022） | **半消化** | 三張表單＋captcha hook 誠實 stub 化（見 §1）；第四流程（自助頁手機驗證從零建頁）不在本刀、條目續留並記已收半 |
| K2-21（B-029） | 消化 | captcha 整套首版＋UX 半條 |
| K2-03（B-018） | **半消化** | 替代登入表單殼半條隨 B-022 收；alova 第二棧半條不動（憲法 §I.2 已治理 demo menu 可見性），條目續留 |

B-001 要求②＝`/speckit-plan` 跑完 Constitution Check 後回填實際消費對照表。
rev5 原生順手收：B-050＋B-051（NOTES 已列；同一組測試件、見設計 §1）。

## 3. 設計（七節、user 核可＋覆核輪修訂）

### §1 模組拓樸與 AppState

新增：`auth/jwt.rs`、`cache/mod.rs`、`throttle/mod.rs`、`captcha/mod.rs`、
`handler/auth/{login,refresh,logout,user_info,alt_stub}.rs`、`handler/route.rs`、`handler/captcha.rs`、
`model/facade/{sys_token,session_event,sys_login_attempt,sys_menu,sys_user,sys_role}.rs`、
`model/password.rs`（覆核補：login 路徑對 sys_user／sys_role facade 與 password 驗證硬相依）。
變更：`auth/enforce.rs`、`state.rs`（兩欄→五欄）、`error.rs`、`router.rs`、`config.rs`、
`model/facade/mod.rs`、`model/mod.rs`、`request_context.rs`（加 real_ip／x_forwarded_for／
ip_confidence **原樣轉錄**欄、零信任判定——該檔自述之收斂落點，handler 絕不自讀轉發標頭；
B-019 接手只換 real_ip 推導）。刪除：`auth/dev_identity.rs` 整檔。
前端新增檔（免軌道）：`src/typings/api/rev5-auth.d.ts`＋`src/service/api/rev5-auth.ts`
（loginCaptcha 不在 fork 原版 service 內、無現成 typings 權威）、`fetchLogout` wrapper（R3）。

★新 crate 六支全需釘版（原稿只提產圖 crate）：argon2 0.5.3／captcha 1.0.0／hex 0.4.3／
jsonwebtoken 10.4.0（★必帶 `rust_crypto` feature——漏了是執行期 panic 非編譯錯）／
redis 1.3.0（connection-manager＋tokio-comp）／sha2 0.10.9（版本沿 rev4 釘版、spec 期雙源核對）；
root Cargo.toml「★不引 argon2」舊拍板（001 clarify Q1）一併翻案記入 ADR。config.rs 新讀六鍵
（APP_JWT_JWT_SECRET［注意雙 JWT 鍵名］／REFRESH_TOKEN_SECRET／ISS／AUD／REDIS_URL／
CAPTCHA_SECRET，compose 皆已接）——現僅一支 getter，六新 getter＋測試宜獨立執行單元。

兩個工程判斷（自拍、回報備查）：①模組名 `cache` 不用 `redis`——rev4 的 `crate::redis` 與
extern crate 同名、全檔靠 `::redis::` 消歧（其檔頭自述此摩擦、且已擴散至 captcha 模組）
②`handler/auth` 拆目錄不用單檔（rev4 單檔約 860 生產行）——CLAUDE.md §2 防呆六件套⑥的
「允許檔案清單」需要圈界力，單檔等於整個 auth 域都在清單裡。

順手收 B-050＋B-051（同一組測試件）：B-051（`test_kit` 遷 `facade/mod.rs`）門檻「第三個消費者
出現時」★須真消費才成立——至少一支新 facade 測試真用 `test_kit::FailingConn` 驗 DbErr 落地，
寫成任務非順手重構；B-050（`roles_of_user` 次段查詢 DbErr 無獨立機器守）條文明點觸發＝
「下一支動 auth／授權面的刀」＝本刀，與 B-051 併收成本最低。

### §2 端點清單（4 → 16 條）

路徑與 Protection 逐條對齊 rev4 實表（已逐字核實含三個 Public）；回傳型以前端 typings 為權威
（憲法 §I.3 權威序 1；範圍義務見 §I.1）。新增 12 條：`/auth/login`（POST/Public）、
`/auth/refreshToken`（POST/**Public**）、`/auth/logout`（POST/**Public**）、
`/auth/getUserInfo`（GET/Authed）、`/auth/loginCaptcha`（GET/Public）、
`/auth/{sendCaptcha,codeLogin,register,resetPwd}`（POST/Public）、
`/route/getConstantRoutes`（GET/**Public**）、`/route/getUserRoutes`（GET/Authed）、
`/route/isRouteExist`（GET/Authed）。

三個 Public 各有非做不可的理由：refreshToken 設 Authed 則過期 token 永遠換不了；logout 設
Authed 則 token 一壞就再也撤不掉那條 session；getConstantRoutes 要在登入前拿得到。
★loginCaptcha 形制（覆核補、沿 rev4）：必帶 `?userName=` query（challenge 綁帳號的前提；
對任意 userName 一律發題＝零存在性洩漏）、userName 超限走與登入端點**同形**的 1000 閘
（零新碼零新 key）、產圖／簽章內部失敗→5000（此路是 captcha 字型涵蓋自證的失效出口）。

**零 Policy → 零新 casbin seed 列 → 維持零 migration**（163 條政策一列不動；★seed 已含
kickUser／getSessionEvent／user:kick 等後續刀政策列＝本刀不消費、spec 明寫防 review 質疑）。
deploy/nginx 已預先宣告四個 auth location 並掛 `limit_req`，路徑逐字對上（`/api` 前綴由
nginx strip、後端 route 不帶前綴）；其餘 8 條新端點落無限流的通用塊＝已知態（R11）。

wire 細節（覆核擴充）：`UserInfo` 四欄皆必填——`userId` typings 宣告 string、DB i64 →
既有 `serialize_i64_as_string`（`MenuRoute.id` 同樣處置）；`userName` ＝ `nick_name` fallback
`user_name`（★憲法 §I.3 鎖定不變式「預設帳號」條之「User → User01 alias」以 **seed 資料**兌現、
碼中零帳號字面（rev4 亦然）；該不變式仍凍結對外可見結果——日後改 getUserInfo 回值仍須
Amendment）；`buttons` ＝ casbin button 政策枚舉（沿 rev4 handler 形 `get_filtered_policy`、
非 `enforce*`＝不觸單一判定進入點守恆）；`UserRoute.home` ＝ `sys_role.role_home` 經
`resolve_home` 兜底（驗 home 屬可見樹可導航葉、不屬→先序第一可導航頁——否則「登入落 404」
復活；★home 型別是 elegant-router 字面聯集，回非法值＝前端靜默不改 redirect、極難查）。
contract case 補一條「帶 apifoxToken 標頭的 /auth/login 正常成功」釘住憲法 §II #1。

### §3 會話生命週期（B-017）

Claims `{uid, sid, jti, roles, iss, aud, exp, iat}`；`sid` ＝ `rotation_chain` ＝會話身分；
`roles` 僅 hint，授權恆 DB-fresh。

**login 十一步**（rev4 逐步同構已核實，run_login 222–363 可直接當 FR 骨架）：①輸入形制閘
（超限 1000、零稽核零 argon2 不消耗桶）②節流狀態機③`authenticate`（三態 collapse 同一 1000）
④txn＋`pg_advisory_xact_lock(uid)`⑤**鎖內重驗**（status／deleted_at／password 字面；
★不重跑 argon2）⑥讀 `session_idle_timeout` 套 TTL（缺失→5000、不猜值）⑦新 sid＋簽對
⑧`sys_token::insert`⑨single-session 判定＋逐 sid `session_event(kicked)`＋寫 `session_id`
⑩稽核成功列同 txn⑪commit 後 best-effort 進 denylist＋last_activity 起點。
★第⑨步（覆核補）＝**兩層政策解析**：`effective_single = policy=='single' ||
(policy=='inherit' && global_on)`；`sys_user.session_policy` 值域＝{single, multi, inherit}
（零文件零 CHECK——碼層收斂＋一支值域測試守、不加 CHECK 保零 migration）；
`single_session_default` 缺鍵→false（off 語意；與第⑥步 fail-loud 方向相反、刻意）。

★第⑪步 denylist 的 TTL 必須是 **refresh 全壽命**（非 access）——否則被踢者在
`(access_secs, refresh_secs)` 窗內換發時 denylist 已過期，掉進 reuse 分支回 8888 並落假
`session_event(reuse)`（rev4 final review M2 抓到、其 kicked 路徑碼註逐字核實）。
★★覆核擴充（rev5 差異點）：**兩 reason（kicked／revoked）一律 refresh_secs**——rev4 僅
kicked 用 refresh_secs，logout／reuse 路徑仍 access_secs＝同 M2 缺陷換 reason 版，rev5 修正。

**refresh**：驗章失敗一律 8888（★絕不 3333，fork 註解自書的死迴圈硬約束；★rev4 實證陷阱＝
jwt 底層恆吐 3333、refresh handler 漏 map_err 即死迴圈——tasks 排紅→綠測釘住）；
`FOR UPDATE` 鎖呈遞列後分流——`active`→idle 檢查→rotate（舊 `rotated`+`used_at`、插新
`active`，次序不可反、partial UNIQUE 護欄）→寫 grace（★commit 前、仍持鎖時）；
`rotated` 且 grace 窗內→冪等回既發後繼；`rotated` 且 grace miss→**reuse 偵測（唯一觸發形，R7）**
→`revoke_family`＋`session_event(reuse)`→8888；`revoked`→denylist reason==kicked→7777／
其餘（reason==revoked **或鍵缺席**）→★靜默 8888、不落事件、不重複撤（R7 改良案：status 即
權威、denylist 純加速層——登出後重放／redis 回捲永不落假 reuse 稽核）；查無列→8888。
★idle（覆核補、沿 rev4）：門檻＝`refresh_secs − access_secs`＝N×60、僅 last_activity 可讀時
判；命中→SET NX `idle-emitted:{sid}` 冪等守門、僅首次落 `session_event(idle)`→8888；
★idle 不寫 denylist（不變式 `access_TTL ≤ N×30 < N×60` ⇒ idle 觸發時 access 必已過期——
此不等式是降級方向表自洽的算式基礎）。

**enforce_mw**：驗 access → denylist 查 → 放行後推進 last_activity。redis 故障退 PG
`has_active_in_chain`，無 active→8888 fail-closed；★PG 亦故障→視為無 active，絕不盲放。
Public 路由不掛本 middleware＝「Public 不查 denylist／refresh 不推進 idle-clock」天然成立。

**降級方向**（user 核可；覆核輪擴為四列＋兩筆已知態，隨 R1 入憲 §I.7）：
denylist fail-closed（寧可誤踢）／idle fail-open（寧可晚踢、退 token exp 為界；redis 掉線＝
無 idle 判定）／grace fail-secure（寧可誤撤良性並發——R9：redis 故障期間多分頁使用者被全域
登出、重登即復原，ADR 記已知態）／captcha-used fail-closed 不罰（R10）。
★R8 已知態：redis 不開 AOF——RDB 回捲窗內 denylist 鍵可丟，暴險受 R7 封頂（換發被 PG 擋），
復活面＝被踢者既有 access 直打 API 至過期（≤5 分）；prod 化由 B-019／部署刀重評。
工程註：session_event.source_ip 為 varchar(45) 非 INET（與 sys_login_attempt.real_ip 型別
不同、寫入不共 helper）；event_type／reason 字面沿 rev4（kicked／reuse／idle／logout；
reason=single_session／idle_timeout 等）。

### §4 節流 ＋ captcha

**IP 維本刀不做**。`request_context.rs` 現為空 struct，信任判定明文屬 B-019；硬做會出事——
★覆核改寫論證：per-IP **鎖定**（15 分鐘、不自癒）在 prod CF 拓樸下 `X-Real-IP` 是 CF 邊緣
出口 IP，一桶 50 次失敗即鎖掉該邊緣後面所有人；nginx `limit_req`（5r/s per peer、burst=40
nodelay）的 key 同為 TCP peer、拓樸缺陷相同，但**速率限制持續自癒**、爆桶只在攻擊持續期間
拒絕——容量防護與懲罰性鎖定是兩回事，前者可先行、後者必須等 B-019 信任錨。`ip_*` 三鍵本刀
無消費者，以 ADR 記已知態、解除謂詞＝B-019 落地。

`sys_login_attempt.real_ip` 為 `INET NOT NULL`：填 nginx 注入的 `X-Real-IP`（client 自帶會被
`proxy_set_header` 覆寫）、`ip_confidence` 標 `'nginx_peer'`（R12：snake_case；B-019 接手時與
rev4 七態合併治理）、`x_forwarded_for` **截斷至 1024 字元＋剝 CR/LF 後**存（覆核補儲存面：
text 無界＋header 上限 8KB＋未認證可寫；★該欄為不可信原文、任何渲染端必須轉義——帳面隨
稽核 UI 刀）。★記錄事實 ≠ 據以做安全判定；B-019 接手只換 real_ip 推導，欄與寫入點不動。
★integration 測試直打 8080 無 nginx＝X-Real-IP 缺席：測試一律顯式注入該標頭（沿 rev4
post_login(peer) 形），不為缺席開回填值。

**帳號維三區**：失敗 <2 自由／2–4 需驗證碼（2222 `biz.auth.captchaRequired`）／≥5 鎖定
（2222 `biz.auth.locked`），後兩者皆在 argon2 之前擋下、不落稽核列、不消耗計數桶（構造上
零 record_attempt——落列則鎖可被週期性探測無限延長）。`sys_login_attempt` 滑動窗為權威
（★GREATEST 三源下界：窗起點／窗內最近成功／unlock marker——reset-on-success 由查詢形免費
兌現，最易被實作簡化掉、spec 逐字帶入）、redis 為 L1 負快取（命中不續期；lock key 唯一寫入
點＝同一次新鮮 L2 讀）；設定鍵讀不到→退活書常數＋一筆 `degraded=settings_default` 告警
（★每次載入至多一筆）。

**captcha**：無狀態簽題 `CaptchaClaims{nonce, user_name, exp, ans_mac}`、HS256、第三把秘鑰
`APP_CAPTCHA_SECRET`（compose 已接）；`ans_mac = hex(SHA256(secret ‖ nonce ‖ lower(answer)))`
——★秘鑰參與雜湊故答案不可離線還原；challenge 綁 user_name；驗題成功即在 redis 標記 nonce
used（SET NX、提交即消耗＝寫入先於答案比對；★寫入失敗→拒絕不罰＝R10）。字元集 34 字
（小寫 a-z 去 `o`＋數字去 `0`）、4 字＝34⁴≥10⁶——★這不是美觀選擇：crate 內嵌字型排除混淆字
且 `add_char` 對無 glyph 字元**靜默跳過**，字集含 `0`/`o` 會產出約 20% 廢題。產圖 crate＝
`captcha 1.0.0`（rev4 釘版；全域版本紀律、spec 期雙源核對）。★rev4 CaptchaClaims 有第五欄
`ctx`（多語境隔離）；rev5 單語境不設——未來開第二語境需 additive 加欄並同步簽驗兩端。

### §5 憲法 Amendment（★ 軌道首開＋§I.7 首批行為島，1.2.0 → 1.3.0）

**四條軌道**（R2／R3／R4／R13）：
- `★BASE-WEB-LOGIN-CAPTCHA-WIRING`：本刀僅開 **(i)** captcha 軟區接線＝`pwd-login.vue`＋
  `store/modules/auth/index.ts`（rev4 已驗證細節隨 tasks：取題 API 走直接路徑 import 避
  barrel stale-export、userName 輸入 debounce 300ms 首發即帶）。(ii) formRules 放寬延改密刀
  （R13）——屆時論據已備：`REG_PWD=/^\w{6,18}$/` 排除全部特殊字元，`password_require_special=on`
  下任何合規密碼被前端擋在送出前；放寬只動 pwd-login.vue 的 rules computed（修改型），
  ★不可改共用 `hooks/common/form.ts`（會連帶鬆掉 register／reset-pwd、逸出射程）。
- `★BASE-WEB-AUTH-WIRING` 三用途（R4）：**(a)** constant routes 合併＝`store/modules/route/
  index.ts` 1 行（實測＝initConstantRoute else 分支一行、Map 按 name 收斂天然支援合併且後端
  同名可覆寫；被清空面＝5 條 constant 路由：403/404/500/iframe-page/login）／**(b)** 替代登入
  誠實 stub＝三張表單各 2 行（import＋消滅假成功行）／**(c)** captcha hook stub＝
  `hooks/business/captcha.ts` 4 行（★影響 code-login＋register 兩表單；reset-pwd 的 code 欄
  無送碼入口＝已知 UX 態記 ADR）。
- `★BASE-WEB-I18N-WIRING` 三用途（R2 甲案）：**(i)** request 層轉譯 2 處＝modal content＋
  showErrorMsg 鏈改走 `translateBackendMsg`（`$t(\`backend.${msg}\`, msg)` 原文 fallback、
  detail 值連帶轉譯）／**(ii)** locale 樹＝en-us.ts＋zh-cn.ts 插 backend 樹（22 鍵＝既有 16＋
  本刀 6；簡中照 rev4 鏡像重打字消化）／**(iii)** app.d.ts backend **必填**型節。
  ★連帶新 ADR 收窄 ADR 0021 §3：該款延後項中 app.d.ts backend 型節本刀提前（LangType／
  locale 註冊／zh-tw.ts 標型重構仍延前端 UI 刀）；ADR 0020 後果末條活口（「前端 i18n 刀提前
  需要 en 譯文，翻案＝該刀 Amendment 一併收」）正是本形。
- `★BASE-WEB-LOGOUT-UX-WIRING`：僅 **(i)**＝`user-avatar.vue` 3 行（登出前 `fetchLogout`
  best-effort、失敗不阻斷；wrapper 住免軌道新檔）；(ii) reLogin toast 不開。

用途 (a) 是**必需非選配**：rev5 seed 的 78 列 `sys_menu` 中 `constant=TRUE` 為 **0 列**
（NULL 64／FALSE 14——★後端 getConstantRoutes 過濾謂詞必寫 `constant = TRUE`、勿寫
IS NOT FALSE），取代語意會清空登入頁等內建常量路由；憲法 §I.2 末句「constant route 集合可經
§III.2 授權新增——builtin 三頁不動與 Casbin 豁免語意不變」＝授權正當性＋紀律邊界（合併＝在
builtin 之上新增、語意不牴觸，ADR 一句說明）。

**§I.7 五座行為島同筆入憲**（R1）：token rotation／single-session／denylist 撤銷／idle 逾時／
登入失敗節流之不變式與 fail-* 方向（§3／§4 降級表四列＋R8 已知態）以 MINOR 同筆入 §I.7；
方向性反轉自此有 MAJOR 閘。憲法現 195 行／預算 350，放得下。

**不開**：`★MODAL-WIRING`／管理頁面；`★BASE-WEB-DEVPROXY-WIRING`——rev5 nginx 前置拓樸
不需要：`VITE_HTTP_PROXY=N` 後 vite proxy（proxy.ts）與 `/proxy-default` 皆無消費者＝零 src
inline（rev4 全倉 5 處 DEVPROXY 屬 vite proxy 拓樸）。

**ADAPT 預設軌道（.env 三檔、零修憲；§III.1 射程含 `.env*`、§II #2 明寫「ADAPT 軌道」）**：
①`.env`：`VITE_HTTP_PROXY=Y→N`；②`.env.test`（★dev 實載此檔：package.json dev＝
`--mode test`）：`VITE_SERVICE_BASE_URL` apifox mock→`/api`；`.env.prod` 同步拆 mock
（沿 rev4 K1-42、dev/prod 同形——不同步＝留一個指向 apifox 的死設定）；③`.env`：
`VITE_AUTH_ROUTE_MODE=static→dynamic` 兌現憲法 §II #2——★不翻則 route store 三處硬閘
（initConstantRoute／initAuthRoute／getIsAuthRouteExist）全走 static 分支，`/route/*` 三端點
前端永不呼叫、用途 (a) 所在 else 分支永不執行、交付價值空轉。★機器守＝R6 人工紀律：.env 在
fork-delta-lint 射程外（只掃 src/*.{ts,vue}、`#` 註解不被認），手寫 `# [rev5-inline
BASE-WEB-ADAPT] 原行: …` 標記＋review 把關、ADR 記已知態；BACKLOG 立「lint 射程擴
`.env*`＋`build/`」條目。★翻 N 後 22081 直連＝vite 無 proxy、`/api` 必 404——唯一入口
http://127.0.0.1:22080（curl 與瀏覽器鎖同一 origin）、記 quickstart。

**同批補機器強制**（fork-delta-lint「軌道名 ∈ 授權名冊」斷言；覆核輪細化）：
- 名冊源＝Amendment 於 §III.2 新建的**機器可解表格**（★順序相依：該表現在不存在——§III.2
  明文「尚未授權任何 ★ 軌道」、§III 唯一表格是 §III.1 三列；Amendment 先定表格形，lint 斷言
  後落）。掃描錨＝表格列（`^\|` 起、跳標題／分隔列、剝 `**`）；名冊＝§III.2 ★軌道 ∪ §III.1
  三軌道。★誤授權陷阱：§III.2 承襲指針**散文**列著六個 rev4 軌道名（含三條本刀明說不開的）
  ——非 vacuous 自證必含「承襲指針六名不在名冊」反例。
- 射程＝R5：僅修改型（帶 `原行:`）標記；並順手強制修改型同行必含 `[rev5-inline` token
  （★現況修改型連 token 都不要求——`find_missing` 對任意含 `原行:` 之行即豁免、比對是去尾
  標點正規化非逐字）。新增型 `NAME+` 不入冊（ADR 0021 款 1；既有 `BACKEND-MSG-DICT+`
  天然豁免）。
- 正規化規則（spec 寫死）：★ 必帶、全名不得縮寫（rev4 實碼三種寫法並存＝反例）、用途後綴
  `(x)` 必帶且 ∈ 該軌道已授權用途集。
- fail-loud：該 lint 首次跨界讀 `.specify/memory/constitution.md`——檔缺席／名冊掃空＝die、
  絕不退空名冊全放行；self-test 加成對樣本（名冊內過／名冊外攔）＋「名冊非空」斷言；既有
  self-test 樣本用名冊外合成名（UI／DEP）須同批改造，否則加斷言即全紅。
- ★結構性 vacuous 護欄：base-web 現況 vs 基線僅三個新增檔＝lint 今日實掃修改型對象為零；
  本刀動到七個既有檔後才有實對象——自證須含「真 repo 至少一個修改型對象被檢查」。
- 動機（維持）：rev4 實測破口——367 個 inline 標記中 **49 個連軌道名都沒寫**（`(k)`20／
  `(g)`14／`(d)`13／`(j)`2；`(j)` 用途 100% 裸字母零正名）。

### §6 錯誤處理與 wire 契約

`AppError` 6→9 變體（加 `LoginFailed` 1000／`TokenExpired` 3333／`ModalLogout` 7777；
`Biz(Cow)` 已存在故三個新 Biz 構造點不需新變體）。碼表終形＝**9 可發＋4 保留＝13**（保留碼
字面＝7778/8889/9998/9999），且無變體碼恰等於四個保留碼——`error.rs` 的
`issuable_six_and_no_variant_seven` 改斷言此對應（★四處同批：函式名／matrix() 三列 sample／
`issuable_witness` 窮舉臂／no_variant 陣列——漏一處即編譯紅或恆綠）。★新變體 HTTP 映射必落
`_ => StatusCode::OK` 臂：fork 的 validateStatus 只放 2xx＋304，非 2xx 信封整個被吞
（onBackendFail 不跑）——3333 配 401 則自動 refresh 靜默全失效；4040/5003 前端顯 axios 英文
原句屬既有已知態。router 面：build() 已有 path fallback（:166），本刀**新增第二道**
`method_not_allowed_fallback`（兩道並存＋與 metric layer 的掛載次序須明寫）；
★該 API 於 axum 0.8.9 之存在性離線未證——**plan 第一步容器內最小樣本驗**（含「只對已註冊
路由生效」次序約束），證偽則回 BACKLOG 候選②重拍；「動詞探測閘永遠裸掛 router」碼註解同時
釘 contract.rs 與 router.rs 兩處（改走 build() 共用即恆綠、L-010 形）；B12「無 Authed 成員」
註解同批更新。

msg key：固定變體鍵依語意分組（`auth.login.failed`／`auth.token.expired`／
`auth.session.kicked`，沿 rev4；既有 `auth.session.reLogin`＝8888 現行鍵不動、★勿漏——兩語
鍵集閘逐鍵比對）；Biz 構造點鍵走 `biz.<domain>.<case>`——`biz.auth.notSupported`／
`biz.auth.captchaRequired`／`biz.auth.locked`。★後兩者為 rev5 對 rev4 的**命名正規化**
（rev4 寫 `auth.login.*`），而 pwd-login.vue 的 captcha 軟區判斷式（本刀新寫、拿 msg 字面
比對區分兩態）須用新名。★Biz 三新鍵不在 Lint24 抽取面（只抽 fn key() match 臂）——機器守＝
msg-dict 兩語鍵集閘＋contract case 逐鍵斷言（列入非 vacuous 自證）。
本刀新增 6 鍵（上列三固定＋三 Biz）落點＝zh-tw.ts＋en-us.ts 各 22 鍵全集（zh-cn.ts 同步、R2）。

B-047：`build()` 掛 `Router::method_not_allowed_fallback` 回 `AppError::NotFound`；ADR 記
4040 新解讀（見 §1 表末列）。

en-us backend 樹一插，`_locales_have_backend_tree` 謂詞成立 → **同一 commit 必須連帶**拔掉
`DAY1_EXEMPTIONS["gen.msg_dict"]`（到期即紅）＋跑 generate 讓 `backend-msg-dict.md` 與
Grafana panel 首次生成。★兩個工程細節：插入行形必須是整行 `backend: {`（謂詞 fullmatch、
一行式寫法不成立）；拔項後 DAY1_EXEMPTIONS 成**空表**——`_assert_day1_table`／
`DAY1_EXEMPT_SCOPE`／五處消費點的空表安全先驗。

★澄清：16 個設定鍵本刀只活 5 個（2 session＋3 login_throttle 含 window_minutes——滑動窗
權威需讀它）；3 個 `ip_*` 卡 B-019，**8 個** `password_*` 卡「沒有改密／建帳號端點」。
`biz.user.passwordViolation.*` 八白名單鍵維持「後端不發」。
★alova 第二棧已知態：release build 非 dormant（見 §2 表 K1-35）；`/auth/error` 不在 16 條
——翻 `/api` 後兩個 demo 頁四顆按鈕失效顯英文原句（user 可見、ADR 記已知態）。

### §7 測試與 DoD

contract case 4→16（純新增；雙向覆蓋閘逐鍵指名缺 case／殭屍 case；★四支 alt-stub 同形恆
2222——逐 case 錯配自證在其上退化，tasks 指定區別手法）；wire-schema fixture：
LoginToken／UserInfo／MenuRoute／UserRoute／ElegantConstRoute **已在 002 快照內**
（TYPINGS_GLOB 全 api 目錄、覆核修正「重抽五形」舊述）——真正新增＝captcha 形，靠新檔
`rev5-auth.d.ts` 入快照；動詞探測閘與 entity_access_lint 零額外工作（table-driven／自動受管；
★parse_router_routes 每欄一行窄假設＝rustfmt 不得折行，另加「generate 後 routes.md 恰 16 列」
機器核對）。

四件難測的事的解法：redis 降級＝`real_redis()`＋`bad_redis()`（lazy ConnectionManager 指不
存在位址）；rotation 並發＝同票兩並發、斷言一 rotate 一走 grace 回同一對且不觸 reuse
（★同鏈至多一 active 由 partial UNIQUE 硬保證——並發失敗模式＝唯一鍵衝突 DbErr，須辨識並轉
grace 冪等分支、不得籠統 5000）；idle＝★不需注入時鐘（`last_activity_set` 收明確時戳、直接
寫舊值）；single-session＝同帳號二次登入、斷言前一條下個請求得 7777（★前置＝先
updateSystemSetting 翻 `single_session_default=on`——預設 off＋全帳號 inherit 下第⑨步永不
執行）。★第五件（覆核補）：redis 鍵空間隔離——dev 與測試共用 DB 0，測試鍵一律 uniq 前綴
（時戳＋pid、沿 rev4），否則測試踢掉開發者自己的 session；`--test-threads=1` 只解 PG 列爭用。

非 vacuous 自證（ADR 0024）逐項：軌道名名冊（＋名冊空集 fail-loud＋承襲指針六名反例＋真
repo 至少一修改型對象）／captcha 字型涵蓋（＋產圖失敗 5000 出口）／msg-dict 兩語鍵集（含
Biz 三新鍵）／denylist fail-closed／★denylist TTL 兩 reason 皆==refresh_secs／reuse 偵測
（僅 rotated＋grace miss 觸發、revoked 缺 denylist 不觸發＝R7）／節流三區／★3333與7777→
HTTP 200／★refresh 驗章失敗→8888 紅綠測。

base-web 側**零測試框架**：把關＝`pnpm typecheck`（★R2 (iii) 必填型節後兼守 zh-cn 結構）＋
`fork-delta-lint`＋手動端到端。★tasks 須明講前端執行單元的 TDD 迴圈會退化成純 review 迴圈、
收斂判定失去客觀依據。

手動端到端驗收（★三帳號密碼皆 `123456`——已離線實證＝upstream demo 值；★錯誤訊息經 R2 甲案
顯人話，zh-CN 顯簡中／en-US 顯英文）：三帳號登入看側邊欄差異／失敗 2 次出驗證碼／答錯自動
換題／失敗 5 次鎖定／【前置：`updateSystemSetting` 翻 `single_session_default=on`】同帳號
二次登入使前一條得 7777／access 過期自動 refresh 無感／登出（UI、R3 接線後）舊 token 立即
失效。★入口一律 http://127.0.0.1:22080（22081 直連 `/api` 必 404）。

★已知假紅：`cargo test --workspace` **必須**帶 `--test-threads=1`（載
`specs/002-system-settings/quickstart.md`）；本刀新增的 auth integration 測共用 `sys_token`／
`session_event`／`sys_login_attempt` 列，平行跑必撞、面比 002 大得多。★real_ip INET NOT
NULL：integration 直打 8080 無 nginx＝標頭缺席，測試一律顯式注入 X-Real-IP。

## 4. 給 /speckit-specify 的輸入摘要

- feature 名＝`003-auth-session`；user 故事核心＝使用者以帳密登入取得可續期的會話，受節流與
  圖形驗證碼保護；登入後側邊欄依其角色由後端生成；會話可被撤銷、逾時、或因他處登入而被踢除；
  錯誤訊息以使用者語言呈現。
- 直接輸入：本檔＋BACKLOG B-017／B-020／B-022／B-029／B-047／B-050／B-051＋K1 十四條與 K2
  六條（§2 表）＋rev4 對應碼（`origin/rev4-admin-rust-api`、`origin/rev4-admin-base-web`，
  唯讀高度參照）。
- 預期**零 migration**（sys_token 9 欄＋rotation partial UNIQUE＋session_event＋
  sys_user.session_policy／session_id＋16 鍵 seed 全在 001 基線；零新 casbin 政策列）。
- clarify 候選（覆核輪已代答大半）：**已定**——TTL 公式沿 rev4（`access=min(300, N×60/2)`／
  `refresh=N×60+access`；N＝session_idle_timeout 分鐘）；logout 對任何 refresh token 一律
  0000 冪等 no-op、不落事件（回異碼＝token 有效性 oracle）；`ip_confidence='nginx_peer'`
  （R12）；captcha crate＝`captcha 1.0.0`；`sys_menu` 樹轉 `MenuRoute` 映射＝rev4
  `to_menu_route` 逐欄＋前端 `router.d.ts` RouteMeta 17 欄為權威（icon_type 拆 icon／
  localIcon、title 恆存、i18nKey 為生成鍵字面聯集、dynamic 模式 roles 不下發）。**仍待
  clarify**——grace 窗長度：rev4=10s 與前端最壞換發間隔 ~11s（1s promise 快取＋10s timeout）
  矛盾，建議 15–30s 帶數字拍；home 多角色收斂律（rev4 `resolve_home` 兜底之上的選擇規則，
  建議 sys_role.id 最小者＋合成多角色測試守）。
- ★開刀第一件事＝憲法 Amendment（§5）走 §V.2 流程：ADR draft → user 親決 → accepted＋憲法段
  ＋bump 1.3.0，獨立 commit 沿先例格式
  `docs(constitution): amend §III.2 ★軌道首開＋§I.7 auth 行為島（ADR 00NN、1.2.0→1.3.0）`
  ＋`docs-sync generate`。軌道未開之前不得動任何 base-web fork 既有檔。
- 程序前置（覆核輪記入）：動 `docs/ops/NOTES.md` 前先壓縮「已收官」段（現 40/40 卡 Lint07）；
  收刀 events summary ≤300 字（本刀極易超限、細節走 notes 欄）；同批 ADR 面＝★軌道＋§I.7
  Amendment ADR、AppState 五欄翻案、ADR 0021 §3 收窄、B-047 4040 解讀、R7～R11 已知態集。
