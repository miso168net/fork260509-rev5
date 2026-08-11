# Research — 003-auth-session

Phase 0 產物。解決 spec 的離線未證項與實作前置未知，並交付 ADR 0019 的兩份硬產物
（R2 rev4 對應碼清單／R3 rev5 拍板差異點）。全程唯讀查證；rev4 碼＝
`origin/rev4-admin-rust-api`／`origin/rev4-admin-base-web`（下同）。

## R1 B-047 處置的 axum API 實證（spec FR-024 的 plan 前置）

**Decision**：`Router::method_not_allowed_fallback` 於 axum 0.8.9 可用；`build()` 的組裝次序
釘死為 **route 註冊 → 各子 router `enforce_mw` layer → merge → `.fallback()` → 
`.method_not_allowed_fallback()` → 最外側 metric layer**。

**Rationale**：spec 要求容器內最小樣本驗，已執行（throwaway crate 置容器 `/tmp`、
`cargo test --offline`、零 repo 污染），三支測試全綠，證出四項行為與兩項次序約束：

| # | 情境 | 實測結果 |
|---|---|---|
| 1 | Public 路由＋動詞不符 | 落 mnaf → 可渲成 4040＋HTTP 404 ✅ |
| 2 | Public 路由＋動詞相符 | 正常放行（fallback 不誤傷） |
| 3 | Authed 路由＋**未認證**＋動詞不符 | **落 mnaf（非 8888）**——mnaf 在 layer 之後掛時，其新設的 default_fallback 不被先前 layer 包住 |
| 4 | Authed 路由＋已認證＋動詞不符 | 落 mnaf |
| 5 | 完全未註冊路徑 | 落既有 `.fallback()`（兩道 fallback 語意分離、並存無衝突） |
| 次序① | mnaf 之後才 `merge` 進來的 route | **不受保護**、回框架預設 405 裸 body（反例測試釘住） |
| 次序② | mnaf 排在 `enforce_mw` layer **之前** | 405 handler 落進 layer 之內 → 未認證動詞不符被攔成 8888，B-047 的 4040 語意在 Authed 路由上失效 |

原始碼三重證據：`routing/mod.rs:374`（API 存在）；`docs/routing/method_not_allowed_fallback.md`
逐字「Sets a fallback on all **previously registered** MethodRouters」；
`path_router.rs:116-127` 實作 `for (_, endpoint) in self.routes.iter_mut()`；
`routing/mod.rs:761-775` `Endpoint::layer` 對 MethodRouter variant 回傳 MethodRouter
（故 layer 後仍掃得到）。

★情境 3 推翻了「405 仍在 layer 之內」的純源碼推論——**這正是 spec 要求實跑的價值**。安全面無
洩漏：未認證的動詞不符與未註冊路徑同回 4040＋HTTP 404，兩者不可區分。

**重現法**（容器內，需 registry 已有 axum 0.8.9；本刀已跑過一次）：建 throwaway crate
依賴 `axum = "0.8.9"`／`tokio`／`tower`(util)／`http-body-util`，以 `tower::ServiceExt::oneshot`
打上表六個情境，`cargo test --offline`。永久資產＝tasks 期把等價斷言寫成 rev5 的 contract
case（SC-008），本探針不入 repo。

**Alternatives considered**：①維持框架預設 405 裸 body（BACKLOG B-047 候選②＝憲法例外集加註
「405 為框架層」）——實證後不需要，故不採 ②`Router::route` 逐條補齊所有動詞回 405 handler——
16 條 route × 5 動詞＝手工枚舉、與「ROUTES 單檔收斂」相斥。

## R2 rev4 對應碼清單（ADR 0019 要求①；實作單元動工前逐檔先讀）

| rev4 | rev5 對應 | 處置 |
|---|---|---|
| `server/src/auth/jwt.rs`（非測試段 1-127） | 同 | 幾近整檔參照重寫：`Claims` 8 欄／`verify`＋`verify_refresh` 金鑰隔離／`verify_with`（leeway=0、set_issuer／set_audience）／`sign`／`token_hash`（SHA256→hex 64）／`TokenTtl`／`access_ttl_secs`／`refresh_ttl_secs`／`ttl_from_settings` 三重 fail-loud |
| `server/src/redis/mod.rs`（1-330） | `server/src/cache/mod.rs` | 承襲連線型別、key builder 六支、GET/SET 原語（含 `set_nx_ex` 回 bool）、R7 nil↔Err 嚴格分流鐵律；**改名** cache（R3-1）＋grace TTL 10→30（R3-2）；不搬 `incr/decr/getdel/expire/ttl/publish/pfadd/pfcount`／HLL／emailverify／ipgate 諸支 |
| `server/src/throttle/mod.rs`（1-738） | 同 | 承襲常數組、`ThrottleSettings`＋`load_settings`（每次載入至多一筆告警）、`lock_ttl_secs`、`precheck` 四步狀態機、`captcha_gate`、`warn_degraded`；**拔** IP 維全組（`load_ip_settings`／`IpThrottleSettings`／`DIM_IP`／`ip_bucket`／⓪L0 白名單／①'②'③'）與 `suppressed_breadcrumb`／`hll_observe`（R3-3）；msg key 改名（R3-4） |
| `server/src/captcha/mod.rs`（1-163） | 同 | 幾近整檔參照：`CaptchaClaims`／`sign`／`verify_challenge`／`answer_mac`／產圖／字元集 34 字／字型涵蓋測試；**去 `ctx` 欄**（R3-5） |
| `server/src/handler/auth.rs` `run_login`（222-377） | `handler/auth/login.rs` | 十一步逐步同構；`advisory_lock_user`／`authenticate`／`sign_pair`／`record_attempt` 一併搬入（拆目錄＝R3-6） |
| 同檔 `run_refresh`（約 500-730） | `handler/auth/refresh.rs` | 五路分流承襲；**revoked 缺 denylist 改靜默 8888**（R3-7）＋denylist TTL 兩 reason 一律 refresh_secs（R3-8） |
| 同檔 `run_logout`（約 729-800） | `handler/auth/logout.rs` | 冪等 no-op 承襲（垃圾／過期 refresh 仍 `Res::ok(())`） |
| 同檔 getUserInfo 段＋`buttons_of_roles`（約 800-830） | `handler/auth/user_info.rs` | 承襲；`buttons` 走 `get_filtered_policy(2, ["button"])`（非 `enforce*`、不觸單一判定進入點守恆） |
| 同檔 alt-login stub 段 | `handler/auth/alt_stub.rs` | 一支共用 stub、四端點恆 2222 |
| `server/src/handler/route.rs`（1-168） | 同 | `get_user_routes`／`get_constant_routes`／`is_route_exist`／`build_user_route_tree`／`resolve_home` 承襲 |
| `server/src/handler/throttle.rs`（loginCaptcha handler、25-58） | `handler/captcha.rs` | 承襲＋正規化到獨立檔（R3-9）；`?userName=` query／超限 1000 同形閘／產圖失敗 5000 |
| `server/src/model/facade/sys_token.rs`（285） | 同 | `insert`／`find_by_hash_for_update`／`rotate`／`revoke_family`／`revoke_others_of_user`／`has_active_in_chain` |
| `server/src/model/facade/session_event.rs`（141） | 同 | `insert`（append-only、八欄；source_ip 為 varchar45） |
| `server/src/model/facade/sys_login_attempt.rs`（76） | 同 | `insert`＋`count_recent_failures`（GREATEST 三源下界 raw SQL 逐字帶入）；**不搬** `count_recent_failures_by_ip`（R3-3） |
| `server/src/model/facade/sys_menu.rs`（1261、部分） | 同 | `list_active`／`visible_menu_routes`／`to_menu_route`（映射見 data-model §5）；不搬選單域寫端（rev4:010-menu-admin 射程） |
| `server/src/model/facade/sys_user.rs`（2099、部分） | 同（新增） | `find_by_user_name`／`find_by_id`／`write_session_id`；不搬使用者域寫端（rev4:011-user-admin 射程） |
| `server/src/model/facade/sys_role.rs`（部分） | 同（新增） | `home_of_roles`（啟用角色依 id 升冪取首個非空 `role_home`、全空→`home`） |
| `server/src/model/password.rs` | 同（新增） | `verify`／`dummy_verify`（時序等化）＋argon2 參數 |
| `server/src/auth/enforce.rs`（954、部分） | 同 | `enforce_mw` 四級降級鏈＋`update_last_activity_best_effort`；rev5 `verify` 由 dev_identity 換真驗章（R3-10） |
| `server/src/middleware/mod.rs`（`RequestContext`／`OptionalCtx`） | `server/src/request_context.rs` | 只取「請求事實原樣轉錄」語意，加 real_ip／x_forwarded_for／ip_confidence 三欄；**不搬**信任判定（屬 B-019、R3-11） |
| `server/src/state.rs` | 同 | 兩欄→五欄（jwt／cache／captcha_secret）；`ip_rules`／`trust_model`／`mailer` 仍不搬 |
| `server/src/error.rs` | 同 | 加三變體（`LoginFailed`／`TokenExpired`／`ModalLogout`）；13 碼矩陣不動 |
| `server/src/router.rs` | 同 | ROUTES 4→16 條、六欄制承襲；**新增** `method_not_allowed_fallback`（R1） |
| `server/src/config.rs` | 同 | 新讀六鍵（`APP_JWT_JWT_SECRET`／`APP_JWT_REFRESH_TOKEN_SECRET`／`APP_JWT_ISS`／`APP_JWT_AUD`／`APP_REDIS_URL`／`APP_CAPTCHA_SECRET`） |
| `server/src/obs.rs` | 同 | pre-register 增三序列（見 R6）；HLL 兩支不搬 |
| base-web `src/store/modules/route/index.ts:163` | 同路徑 | `addConstantRoutes([...staticRoute.constantRoutes, ...data])` 一行（★源倉＝`fork260509-soybean-admin-base`、分支 `origin/rev4-admin-base-web`，下同） |
| base-web `src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue` | 同路徑 | 各 2 行：import stub wrapper＋消滅假成功 toast |
| base-web `src/hooks/business/captcha.ts` | 同路徑 | 4 行：改打 `/auth/sendCaptcha` stub |
| base-web `src/views/_builtin/login/modules/pwd-login.vue`（rev4 11 處） | 同路徑 | captcha 軟區接線（取題走直接路徑 import 避 barrel stale-export、userName debounce 300ms、220×120 條件渲染）；**`formRules` 放寬三處不帶回**（R3-12） |
| base-web `src/store/modules/auth/index.ts`（rev4 7 處） | 同路徑 | login 簽名加 captcha 參＋失敗 msg 回傳鏈（locked／captchaRequired 兩態同碼 2222、僅 msg 相異） |
| base-web `src/layouts/modules/global-header/components/user-avatar.vue`（rev4 3 處） | 同路徑 | 登出前 best-effort `fetchLogout`、失敗不阻斷 |
| base-web `src/service/request/index.ts`（rev4 4 處） | 同路徑 | `translateBackendMsg`＋`translateDetailValue`；modal content 與 toast message 兩行改走轉譯；**不帶回** LOGOUT-UX(ii) reLogin toast（R3-13） |
| base-web `src/typings/app.d.ts`（rev4 27 處中 backend 型節） | 同路徑 | 補 `backend` **必填**型節；LangType 改行不帶回（延前端 UI 刀） |
| base-web `src/locales/langs/{en-us,zh-cn}.ts` | 同路徑 | 插 backend 樹 22 鍵（簡中照 rev4 鏡像重打字消化） |
| base-web `src/service/api/rev4-login-captcha.ts`／`rev4-session-logout.ts` | `rev5-auth.ts`（合一） | wrapper 新檔、`rev5-` 前綴（§III.1 WRAPPER 軌道、免 ★ 軌道） |
| base-web `src/typings/api/rev4-*.d.ts`（captcha 形） | `rev5-auth.d.ts` | 新檔（ADAPT 軌道）；入 wire-schema 快照 |
| base-web `.env`／`.env.test`／`.env.prod` | 同路徑 | 四行改動（見下）；★rev4 的 `VITE_HTTP_PROXY=Y`＋`VITE_PROXY_TARGET`＋DEVPROXY 軌道**方向相反、不可照抄**（R3-14） |

`.env` 四行標記逐字（FR-027；標記形＝`# [rev5-inline BASE-WEB-ADAPT] 原行: <現值>`，軌道名
**全稱**不縮寫）：`.env:17 VITE_AUTH_ROUTE_MODE=static`→`dynamic`／`.env:26 VITE_HTTP_PROXY=Y`
→`N`／`.env.test:2` 與 `.env.prod:2` 各一份
`VITE_SERVICE_BASE_URL=https://mock.apifox.cn/m1/3109515-0-default`→`/api`。

rev4:005-auth-login／rev4:006-session-lifecycle／rev4:007-login-throttle 之 SDD 產物與
rev4:ADR 0029／0033／0040 結論已透過 K1 摘要與實碼消化（原文在 rev4 傘狀 repo、本工作區不可達，
引用一律標「經 K1-nn 摘要」）。

## R3 rev5 拍板差異點清單（ADR 0019 要求②；★防回歸：以下 rev4 行為一律不得帶回）

| # | rev4 行為 | rev5 拍板 | 出處 |
|---|---|---|---|
| R3-1 | 模組名 `crate::redis`（與 extern crate 同名、全檔 `::redis::` 消歧） | 模組名 `cache`；消歧包袱消滅，**註解不得帶回消歧理由**。★同型張力於 `captcha` 處**未消滅而是明文規則化**（本刀新引 crate `captcha 1.0.0` ＋模組 `crate::captcha`）：`cache` 之於 `redis` 有語意更準的替代名，`captcha` 沒有 ⇒ 保留模組名、改以「本檔前導 `::`／他處 `crate::`／`lib.rs` 絕不裸寫」三條規則＋檔頭碼註承載（見 tasks T052） | brainstorm §1 工程判斷①；analyze 補 |
| R3-2 | `GRACE_TTL_SECS = 10` | **30 秒**（前端最壞換發間隔 ~11s） | Clarify Q1 |
| R3-3 | IP 維節流（rev4:008-ip-gate）／HLL 廣度（rev4:016 觀測刀）／`suppressed_breadcrumb` | 一律不做；`precheck` 簽名去 real_ip／ip_allow 參數位 | spec FR-015、Out of Scope |
| R3-4 | `auth.login.locked`／`auth.login.captchaRequired` | `biz.auth.locked`／`biz.auth.captchaRequired`（Biz 構造點鍵走 `biz.<domain>.<case>`） | spec FR-025 |
| R3-5 | `CaptchaClaims` 五欄（含 `ctx` 跨語境隔離） | 四欄、單語境不設 `ctx`；未來開第二語境需 additive 加欄並同步簽驗兩端 | spec Assumptions |
| R3-6 | `handler/auth.rs` 單檔約 860 生產行 | 拆 `handler/auth/` 目錄五檔（防呆六件套⑥允許檔案清單需圈界力） | brainstorm §1 工程判斷② |
| R3-7 | refresh 遇 `revoked` 且 denylist 鍵缺席（nil）→落 reuse 分支、撤家族、落 `session_event(reuse)` | `sys_token.status=='revoked'` 即權威 → **靜默 8888、不落事件、不重複撤**；reuse 偵測只保留給 `rotated`＋grace miss | Clarify（覆核輪 R7） |
| R3-8 | denylist TTL：kicked 用 `refresh_secs`，logout／reuse 路徑用 `access_secs` | **兩 reason 一律 `refresh_secs`**（rev4 該不對稱＝final review M2 同族缺陷的換 reason 版） | spec FR-008 |
| R3-9 | loginCaptcha handler 住 `handler/throttle.rs` | 獨立 `handler/captcha.rs` | brainstorm §1 |
| R3-10 | 「標頭缺席」也判 3333 | 三分：exp 過期→3333／缺席・非 Bearer・簽章不符・已撤銷・鏈失效→8888／被踢→7777 | spec Clarifications |
| R3-11 | 信任判定散在 handler／`trust/mod.rs` 七態 | `request_context.rs` 原樣轉錄、零信任判定；`ip_confidence` 單一字面 `nginx_peer` | spec FR-018 |
| R3-12 | `formRules` 放寬（LOGIN-CAPTCHA(ii)、三處 inline） | 本刀不開 (ii)、延改密端點刀；★不得順手放寬 | Clarify（覆核輪 R13） |
| R3-13 | LOGOUT-UX(ii)：request 層 8888 前插「請重新登入」toast | 不開（僅 (i) 登出前呼 API） | spec FR-028 |
| R3-14 | dev proxy：保留 `VITE_HTTP_PROXY=Y`＋新增 `VITE_PROXY_TARGET`＋開 DEVPROXY 軌道改 `proxy.ts`／`utils/service.ts` | 翻 `VITE_HTTP_PROXY=N`、**不開 DEVPROXY 軌道**、由 nginx 前置拓樸取代 | spec FR-027 |
| R3-15 | `app.d.ts` 同批改 LangType＋zh-tw.ts 標型重構 | 只補 `backend` 必填型節；LangType／locale 註冊／zh-tw 標型仍延前端 UI 刀 | ADR 0021 §3 收窄 |
| R3-16 | 首登強制換密（`sys_pwd_custody`）／email-verify／mailer | 全不做（本刀零改密端點） | Out of Scope |
| R3-17 | precheck 讀 redis 鍵 `throttle:unlock:user:{name}` 取 unlock marker（值＝unix 秒字串、TTL＝window_secs），並在 GET Err 時發 `degraded=redis_unlock_marker` | **完全不讀 redis**：`unlock_marker_ts` 恆傳 `None`（本刀無解鎖端點＝無寫入者，讀了恆 nil）；`cache` 六支 key builder 不含該鍵、降級 source 集不含 `redis_unlock_marker`。★SQL 參數位保留（`GREATEST` 非 strict、NULL 自然退化為兩源）⇒ 未來解鎖刀補「鍵＋讀取＋label」三件、handler 零改動 | analyze U4／I5 |

## R4 依賴釘版與雙源核對（CLAUDE.md §6）

| crate | 釘版 | 第一源（rev4 Cargo.toml／lock，兩者一致） | 第二源 | features |
|---|---|---|---|---|
| `argon2` | 0.5.3 | ✅ | 本機不可達（見下） | default（含 PHC 解析） |
| `captcha` | 1.0.0 | ✅ | 本機不可達（rev4 註記：rev4:ADR 0037 §G.22 拍板） | `default-features = false`（★關掉唯一可關的 `audio`——其 manifest `default = ["audio"]`、audio 只拖進 `hound` WAV 編碼器；本刀只出圖形題、零音訊面。圖形路徑所需的 `image`／`lodepng`／`base64`／`rand`／`serde_json` 皆非 optional、不隨開關變動） |
| `hex` | 0.4.3 | ✅ | **rev5 `Cargo.lock` 既存同版**（零 lock 圖變動） | default |
| `jsonwebtoken` | 10.4.0 | ✅ | 本機不可達（rev4 註記：user 2026-07-05 拍板） | `default-features = false`＋**`rust_crypto`**（★漏開＝decode 執行期 panic、非編譯錯） |
| `redis` | 1.3.0 | ✅ | 本機不可達（rev4 註記：user 2026-07-06 拍板、當時 crates.io latest stable） | `default-features = false`＋`connection-manager`＋`tokio-comp` |
| `sha2` | 0.10.9 | ✅ | **rev5 `Cargo.lock` 既存同版**（零 lock 圖變動） | default |

**Decision**：六支全採 rev4 已驗證組合值。**第二源（crates.io latest stable）於本機不可達**
（沿本 repo 既有先例＝`log = "0.4.33"` 條目自書「第二源於本機不可達（HTTP 403），已揭露後由
user 拍板採 lockfile 值」）——本刀依同一處置：research 明示揭露、不默默釘版。lock 成長**實測
441→484 名**（+43／+10%），`captcha` 為相依成長最大宗；關掉 `audio` 後少一支 `hound`（未關為 485）。

★同批須改寫的三處舊拍板註解（否則 manifest 已改而註解仍宣稱不引、review 必擋）：
root `Cargo.toml:11-12`「★不引 argon2」／`server/Cargo.toml:1-4` 不進清單（移出前六支、後六支
續留）／`state.rs:7-9`「恰兩欄」封條（改寫時保留「`ip_rules`／`trust_model`／`mailer` 仍不搬」
的邊界說明）。

## R5 降級矩陣終形（五座行為島；隨 §I.7 Amendment 入憲）

| 降級源 | 方向 | 行為 | 觀測 |
|---|---|---|---|
| denylist 讀不到（連線 Err） | **fail-closed** | 退 PG `has_active_in_chain`；無 active→8888；PG 亦故障→視為無 active、絕不盲放 | `denylist_hit_total{source=pg}` |
| denylist 鍵缺席（nil） | 權威語意 | nil＝「未撤」→放行；`revoked` 列則由 status 定案（R3-7） | — |
| last_activity 不可讀 | **fail-open** | 不 idle-reject、照常 rotate（token exp 為界） | — |
| grace 不可用 | **fail-secure** | 並發 refresh 觸發 reuse→撤家族（多分頁全域登出、重登復原＝已知態） | — |
| captcha 標記 SET NX 瞬斷（redis 健康） | **fail-closed 不罰** | 拒該次登入、零計數桶 | `throttle_degraded_total{source=redis_captcha}` |
| redis 整體不可用 | **fail-open** | 軟區 captcha 要求**整層停用**、續驗密碼（驗不了題就不該要求；密碼錯仍計數） | `throttle_degraded_total{source=redis_lock}` |
| 節流 L2（PG）查詢失敗 | **fail-open ＋ 補償** | `count:=0` 放行 ＋ `captcha_forced = !redis_down`（否則 DB 抖動會同時關閉節流與 captcha）；★`captcha_forced` **不入**軟區計數 | `throttle_degraded_total{source=db_count}` |
| L1 lock key SET 失敗（redis 健康） | best-effort | 鎖定判定已成立、只是負快取未武裝（下次請求仍由 L2 權威判） | `throttle_degraded_total{source=redis_lock_set}` |
| 節流設定鍵讀不到 | 退活書常數 | 每次載入**至多一筆**告警（缺三鍵不放大成三筆） | `throttle_degraded_total{source=settings_default}` |
| 失敗列寫入失敗 | best-effort | 不改登入回應；★但等於計數斷供（該帳號永不鎖亦永不 captcha）故必須可見 | `throttle_degraded_total{source=db_write}` |
| idle timeout 設定鍵缺失（login 第⑥步） | **fail-loud** | 5000、不猜 TTL 值（與節流方向相反、刻意） | — |
| redis 不開 AOF | 已知態 | RDB 回捲窗內 denylist 鍵可丟；暴險受 R3-7「status 即權威」封頂 | — |

## R6 觀測面與 i18n 契約的算術自證

**觀測面（FR-034）**：`obs.rs` 的 `pre_register_metrics` 增三序列（該檔自書「後續刀之新序列各自
帶 pre-register」）：`throttle_degraded_total`（label `source`＝**R5 表列之六源逐字**，即
`settings_default`／`redis_lock`／`redis_lock_set`／`redis_captcha`／`db_count`／`db_write`；
★rev4 user 維為七源，rev5 少 `redis_unlock_marker`——本刀不讀 unlock marker，見 R3-17）／
`denylist_hit_total`（label `source`＝`redis`｜`pg`）／`throttle_soft_zone_total`（無 label）。
★`captcha_forced` 屬 DB 降級旗標、**不計入** `throttle_soft_zone_total`（降級能見度歸
`throttle_degraded_total`）。降級 warn 一律結構化（`target: "security.throttle"`＋`degraded`
欄），守門走計數器 render 文本比對（沿 `obs.rs` 現有測試形）；不新建 log 捕捉層設施。
rev4 的 `throttle_hll_*` 兩支不做。

**i18n（FR-026）算術自證**：插入後三語 backend 樹各 22 鍵。等式＝**後端實發 13＋前端內部白名單
9 ＝ 22**（實發 13＝002 既有 7〔`common.success`／`system.internal`／`system.notFound`／
`system.forbidden`／`auth.session.reLogin`／`biz.systemSettings.invalidValue`／
`biz.systemSettings.notFound`〕＋本刀 6；白名單 9＝`biz.user.passwordViolation.*` 八鍵＋
`common.listSeparator`，後端恆不發）⇒ 零孤兒鍵、零缺譯、白名單∩實發＝∅，Lint24 三向斷言恰好
成立。`MSG_DICT_LOCALES` 維持兩支；zh-cn 結構由 `app.d.ts` 必填型節＋`pnpm typecheck` 守。
★`_locales_have_backend_tree` 為整行 fullmatch `\s*backend:\s*\{`——插入行必須是獨佔一行的
`  backend: {`，同 commit 拔 `DAY1_EXEMPTIONS["gen.msg_dict"]` 並跑 generate（該表拔後成空表、
需先驗 `_assert_day1_table`／`DAY1_EXEMPT_SCOPE` 與五處消費點的空表安全）。

## R7 測試設施與機器閘衝擊（tasks 的硬前置）

1. **★contract 測 stub 連線形須換**：`all_registered_contract_cases_pass` 對每條非信封例外
   route 另發一次請求斷言三欄信封。現況兩條業務 route 皆 Policy、`enforce_mw` 在 authn 層
   early-return，handler 永不觸及故免 DB；本刀 9 條 Public 會**真的進 handler**，其中
   `/route/getConstantRoutes` 查 sys_menu，而 stub 的 `DatabaseConnection::Disconnected` 在
   `Select::all` 呼 `get_database_backend()` 時**直接 panic**（非回 DbErr）。
   **Decision（★2026-08-09 修訂，ADR 0034）**：改用 `ConnectOptions::connect_lazy(true)` 建的
   假連線（`Database::connect` 走 sqlx `connect_lazy_with`、不 await 不連線，直接回真
   `DatabaseConnection`；`get_database_backend()` 回 `Postgres` 故不 panic，查詢時才失敗成
   `DbErr`）。★URL MUST 不帶 `user:pass@`（會命中 betterleaks 的 DSN 規則、被子庫 pre-commit
   硬擋）。**原案（sea-orm `mock` feature 的 `MockDatabase`）經實證不可行**：
   `sea-orm-1.1.20/src/database/db_connection.rs:19` 為
   `#[cfg_attr(not(feature = "mock"), derive(Clone))]`——開 `mock` 即拔掉
   `DatabaseConnection: Clone`，而 axum `State` 要求 `AppState: Clone`（實測 `E0277`），
   且 cargo 對整個 test 建置圖做 feature 聯集、放 dev-dependencies 亦無效。
   ★連帶約束：stub 查詢回 `DbErr` 而非空集 ⇒ **contract case 只能斷言三欄信封與 13 碼矩陣成員、
   不得斷言 `code == "0000"` 或空集 data**（業務內容歸 integration 測）。
   七條 POST route 各需自訂 rejection→信封（沿 002 `from_request` 形）；
   `/auth/loginCaptcha` 的 Query rejection 亦須成三欄信封（FR-003 的 1000 同形閘）。
2. **★`dev_identity.rs` 汰換會弄紅兩支 lint**：該檔被硬編進 `authz_entrypoint_lint.rs:207-223`
   與 `entity_access_lint.rs:217-231` 的 `scan_is_non_empty` must-list。刪檔單元必須同批把該列
   換成本刀新檔（維持逐檔指名的守門強度，**不是直接刪列**），並同批更新
   `docs/arc42/ARCHITECTURE.md` 該節與 `auth/mod.rs` 的 `pub mod` 行。
3. **★`error.rs` 實為六處逐字改動**（spec FR-023 的「四處」低估兩處）：①函式名
   `issuable_six_and_no_variant_seven` 語意改名 ②計數斷言 6→9 ③期望陣列收成四保留碼
   ④`matrix()` 補三列（code／key／http／sample）⑤`issuable_witness` 窮舉 match 補三臂（不補＝
   非窮舉、編譯紅）⑥`witness_aligns_matrix_and_excludes_no_variant_codes` 內**第二份**
   `no_variant` 陣列同步。★`http()` 現為 `_ => StatusCode::OK` 萬用臂 ⇒ 1000／3333／7777 自動
   落 HTTP 200，FR-024 零改動即成立、只需補斷言。
4. **★schema-gate gate2 × runtime 寫入**：凍結 seed 對 `sys_token`／`session_event`／
   `sys_login_attempt` 各有 0 列 COPY 段＋`setval(seq, 1, false)`，normalize 原位保留 setval
   逐列 diff。本刀會插入這三張表並**不可逆推進三支 sequence**——刪列救不回 setval。002 的
   `SeedRestoreGuard` 只 `UPDATE system_settings`（無 sequence）故未撞到，本刀是首撞。
   **紀律**：真 DB 測試守衛除還原列外，**須顯式 `setval(seq, 1, false)` 重設三支 sequence**；
   single-session 前置把 `single_session_default` 翻 `on` 後**驗收完須翻回 `off`**（連帶
   `updated_at`／`updated_by` 欄），否則 gate2 seed 自本刀起永久紅。
5. **redis 鍵空間隔離**：dev 與測試共用 DB 0（連線字串無 DB index）。測試鍵一律加 uniq 前綴
   （時戳＋pid，沿 rev4 `redis/mod.rs` 測試 helper 形），否則測試會踢掉開發者自己的 session；
   `--test-threads=1` 只解 PG 列爭用、不解 redis 鍵爭用。
6. **`parse_router_routes` 兩個地雷**：16 條 route 必守「每欄一行」窄形制（rustfmt 不得折行）；
   `handler:` 正則 `^handler:\s*\|\|\s*(?:get|post|delete)\(.+\),$` 對 `|| get(h).post(h)` 鏈式
   多動詞**靜默 fullmatch 通過** ⇒ 16 條不得出現鏈式，另加「generate 後 `routes.md` 恰 16 列」
   機器核對。
7. **登入失敗列寫入點**（spec 無顯式 FR、由 FR-014「滑動窗為權威」隱含，tasks 須顯式排入）：
   rev4 `record_attempt` 產線呼叫恰三處——①`authenticate` Denied（外層 conn，uid 可為 None）
   ②鎖內重驗失敗（★先 `txn.rollback()` 再落列於外層 conn，否則隨 txn 回滾）③成功（落 txn 內、
   與建會話原子）。**不落列**四類路徑：形制閘超限／節流三個拒絕分支（`?` 早退、構造上零
   `record_attempt`）／5000 配置與內部異常。

## R8 憲法 Amendment 形制（FR-028／FR-029；ADR draft 的直接輸入）

**§III.2 機器可解表格形**（順序相依：Amendment 先定表格，FR-030 的 lint 斷言後落）：沿 §III.1
的 markdown 表格慣例、**逐軌道逐用途一列**，欄位＝`| 軌道 | 用途 | 範圍（檔案） | 紀律 |`；軌道名
以 `**★NAME**` 包覆（掃描端剝 `**` 與 `★`）。掃描錨＝該表標題列之後、以 `^\|` 起的資料列，跳
分隔列。**名冊＝§III.2 ★ 軌道 ∪ §III.1 三軌道**。

★兩條非空斷言（單一條不足）：「名冊整體非空」＋「§III.2 ★ 段貢獻列數 ≥ 4」——因 §III.2 表格
若被刪或掃描錨打錯，§III.1 三名仍在、名冊仍非空，斷言照跑卻整段失守（半 vacuous）。另保留
「承襲指針散文中**本刀不開的兩名**（`MODAL-WIRING`／`BASE-WEB-DEVPROXY-WIRING`）不在名冊」作為
掃描錨正確性的反向自證——★不可寫「六名」：Amendment 後六名中四名正式在冊，該斷言必然不成立。

**§I.7 五座行為島條文骨架**（MINOR、不抬版號）：token rotation（同鏈至多一 active＋rotate 次序
不可反＋grace 冪等窗）／single-session（兩層政策解析＋踢除落事件）／denylist 撤銷（status 為
權威、快取為加速層、fail-closed）／idle 逾時（fail-open、不寫 denylist、`access_TTL ≤ N×30 <
N×60` 不等式）／登入失敗節流（三區＋滑動窗為權威＋argon2 前擋零列零桶）。方向性反轉自此為
MAJOR。

**同批 ADR 面**：★軌道四條＋§I.7 五島（主 Amendment ADR）／AppState 兩欄→五欄翻案／
ADR 0021 §3 收窄（app.d.ts backend 型節提前）／B-047 之 4040 解讀／root Cargo.toml「不引
argon2」翻案／R5 已知態集（含快速登入鈕暴露 dev 帳密、redis 無 AOF、alova 第二棧 release 非
dormant、`/auth/error` 失效）。

## R9 執行單元切分（tasks 的 phase 骨架建議）

沿 001 前例以 **T 號區間**表達單元邊界（002 不標 U 編號；啟動書與 Lint25 `uround` 族禁止把 U
編號當長壽指涉錨）。建議 14 個單元、45~60 個 T：

1. ★主線：憲法 Amendment（ADR draft→user 親決→accepted＋§III.2 表格＋§I.7＋bump 1.3.0＋
   generate）——**硬閘：未 accepted 前不得動任何 base-web 既有檔**
2. 依賴進場（六 crate 釘版＋三處舊拍板註解改寫＋`config.rs` 六鍵）
3. 基座（`state.rs` 五欄＋`cache/mod.rs`＋`auth/jwt.rs`＋contract stub 連線改 mock）
4. `error.rs` 三變體＋六處斷言改造
5. facade 四支（sys_token／session_event／sys_login_attempt／sys_role）＋B-050／B-051
6. facade sys_menu＋`to_menu_route`
7. `model/password.rs`＋`throttle/mod.rs`（帳號維三區）
8. `captcha/mod.rs`＋`handler/captcha.rs`
9. `handler/auth/login.rs`（十一步）
10. `handler/auth/{refresh,logout}.rs`
11. `handler/auth/{user_info,alt_stub}.rs`＋`handler/route.rs`
12. ★獨佔單元：`router.rs` ROUTES 16 條＋`contract.rs` 16 case＋mnaf＋`dev_identity` 汰換與兩支
    lint must-list（此二檔幾乎出現在每個單元的允許檔清單，收斂成獨佔單元避免反覆撞牆）
13. base-web：`.env` 四行＋七檔 ★ 軌道接線＋兩支新檔
14. i18n 三語 22 鍵＋`app.d.ts` 型節＋拔豁免＋generate；DoD 收攏
