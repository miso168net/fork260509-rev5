# ARCHITECTURE — rev5 活書（living as-built）

本書永遠現在式：只寫系統現在的樣子。未來事項住 ops/（NOTES／BACKLOG）、歷史住 git＋events；
決策全文住 decisions/、快變事實住 generated/reference/。空節代表對應子系統尚未建置、隨刀填入。

## §1 簡介與目標

rev5-admin 是一套管理後台系統：前端 fork 自 soybean-admin（Vue3＋TS＋naive-ui）、
後端以 Rust 從零重寫，經歷 rev1~rev4 四代演進後、本代自 rev4 治理終態與乾淨血緣重跑。

**能力級**（以 base-web 為權威——前端有的功能、後端必供對應端點，範圍不縮減）：
使用者／角色／選單管理、casbin RBAC（menu／button 維度）、認證與 session 治理、
系統設定、審計（操作／存取／登入嘗試）、IP 存取控制、觀測層。

**明確不做**：多租戶、對外開放 API、行動端。

**目前建置狀態**：文件地基（創世）＋schema 基線（001）＋系統設定縱切（002）＋auth 會話
縱切（003：真登入／rotation／撤銷矩陣／節流三區／圖形驗證碼／i18n 接線）＋IP 信任錨縱切
（004：真實來源還原**七態**＋轉發鏈逾上界的拒絕腿一態〔＝`ip_confidence` 欄值域共八態，但第八態由三層矩陣**之前**的短路產生、不是矩陣的出口〕／IP 存取閘與門鈴熱重載／IP 規則管理頁與五支端點／來源維節流／
管理員解鎖端點）＋角色與選單 CRUD（005：role／menu 兩域 CRUD、選單序列化域、判定面 rebuild-swap
熱重載、授權歸檔寫入面）＋三維授權治理（006：端點／選單／按鈕三維讀寫、結構性封死、回收桶
與 policy-archive 頁）＋使用者與密碼治理（007：管理面十支＋自助兩支、no-escalation 包含規則、
密碼政策與設密冷卻、改密舊密節流、user 管理頁與個人中心改密卡）＋稽核中心與系統設定頁（008：audit 四源四分頁唯讀報表與水平線清理入口、五支端點、settings 頁 16 鍵管理；purge 單交易原子性與 logout TTL 次序皆有 fault-injection 級機器守）就位；其餘域隨波次建置。

## §2 約束

- **技術棧**：前端＝soybean-admin fork（Vue3／TypeScript／naive-ui／vite／pnpm）；
  後端＝Rust（axum／sea-orm／PostgreSQL／Redis／casbin）；容器化 docker compose；
  工作區工具＝python3 標準庫（tools/ 治理工具鏈）。
- **repo 拓樸**：傘狀 repo（本 repo、default branch `rev5-admin-root`）＋兩個雙身分子體
  （本機 git worktree／外層 submodule gitlink）：`base-web/`（分支 `rev5-admin-base-web`、
  自 upstream example 最新 HEAD 衍生）與 `rust-api/`（分支 `rev5-admin-rust-api`、自源倉
  Initial commit 起全新寫）。fork 源倉以本機 clone 住 repo 根下（gitignored；
  `fork260509-soybean-admin-base/` 與 `fork260509-rev2-anew-rust-api/`）、必須保留——
  worktree 的 `.git` 檔指向它。
- **環境**：macOS（APFS）與 WSL2（drvfs）皆為工作環境——治理工具判定面跨平台單一引擎
  （python re、不依賴平台 grep 方言）；repo 全域 .gitattributes 強制 LF；host 無 rust
  toolchain、build/test 一律容器內——由 compose dev stack（一鍵起，§7）承載。
- **上游關係**：upstream 常態 rebase 為預期事件；fork 差異治理見 constitution §III。

## §3 系統脈絡

（本節尚無內容；ingress 拓樸與外部依賴隨部署刀填入。）

## §4 解法策略

- **從上游重來的 fork 策略**：base-web 取上游最新 HEAD 衍生、rust-api 從零重寫；
  fork 差異以軌道制治理（constitution §III：不動 inline 為預設、★軌道逐用途授權、
  `rev5-inline` 標記紀律）。
- **傘狀雙脊椎**：傘狀 repo 管文件／spec／編排，兩子體各自成倉；兩段式 commit
  （worktree 內 commit→外層 pin bump）保證每個外層 commit 可重現。
- **縱切刀工作流**：功能以縱切刀交付（migration→facade→handler→授權→wire→前端整條打通）；
  橫切慣例為一級公民（事件 kind=horizontal）、每條慣例必附守門機制（§8）。
- **授權模型**：casbin RBAC、DB-first 寫入（寫側只動 DB、寫後全量重載——constitution §I.2
  與行為島進場規則承載細節）。
- **wire 契約機器化**：前端 typings 為裁判、contract test＋coverage gate 守恆
  （constitution §I.3）。
- **機器優先文件觀**：文件為機器與人共讀而設計；每個事實一個人寫的家、鏡像一律機器生成
  （tools/docs-sync.py）、契約 lint 在 commit 當下強制。

## §5 Building blocks

rust-api workspace members＝migration／entity／sea-orm-adapter／server：

- **entity crate**：15 表 sea-orm entity，欄集與 schema 快照逐欄一致
  （`tools/entity-drift-gate.py` 守恆；其中 `casbin_rule` 委派 adapter 建基底、不入比對面，
  故實比對 14 表）；ORM 關聯與行為層紀律見 §8 資料慣例。
- **server crate 管線形**（請求單向流）：`request_context_mw`（信任錨還原＋請求上下文注入，
  最外側業務層；004）→`ip_gate_mw`（IP 存取閘，**先於身分驗證**）→router（`ROUTES` 註冊表
  ＝路徑／method／handler／
  授權態單一來源；動詞不符由 `method_not_allowed_fallback` 收斂為 4040＋HTTP 404，末端
  外殼再剝除 axum 自動附加的 `allow` 標頭——信封與標頭兩面皆與未註冊路徑不可區分＝零
  存在性洩漏，組裝次序載於 ADR 0031、剝除掛點論證見 router.rs 碼註）→enforce_mw（真驗章
  middleware：HS256 access 驗章〔三分碼——缺席・非 Bearer・簽章不符→8888、僅 exp 過期
  →3333、通過即解出 Claims〕→denylist 查〔redis 加速層、`sys_token.status` 為權威；命中
  即拒——被踢→7777 modal、其餘（已撤銷）→8888 silent；redis 故障退 PG
  `has_active_in_chain` fail-closed、PG 亦故障視為無 active 絕不盲放〕→放行後
  best-effort 推進 last_activity；dev-only 查表驗證器已汰換、debug 與 release 同一路）→
  require_policy（逐路由授權層：每請求 DB-fresh 撈角色→casbin 求值）→handler→
  validation registry（設定值型驗證）→model/facade（entity 存取唯一管道、
  `entity_access_lint` 守恆）→DB→envelope（`Res` 三欄信封；/health、/metrics
  為登記在冊信封例外）。
- **auth 域模組拓樸**（003 落地）：`auth/`（`jwt.rs` HS256 簽驗章＋token_hash；`enforce.rs`
  驗章 middleware＋denylist 降級鏈＋casbin 單一判定進入點）／`handler/auth/`（`login.rs`
  十一步登入鏈、`refresh.rs` rotation＋reuse＋idle、`logout.rs` 撤銷、`user_info.rs`、
  `alt_stub.rs` 替代登入誠實 stub 四出口）／`handler/captcha.rs`＋`captcha/`（圖形驗證碼
  簽章題）／`throttle/`（登入失敗節流狀態機——003 起帳號維、004 起雙維）／`cache/`
  （redis session 加速層：denylist／grace／last_activity／throttle L1 與解鎖標記鍵面）；
  資料面 `model/facade/` **13 支**（session_event／sys_casbin_archive／sys_casbin_policy／
  sys_ip_rule／sys_login_attempt／sys_menu／sys_operation_log／sys_pwd_custody／sys_role／
  sys_token／sys_user／sys_user_role／system_settings；`sys_casbin_archive`＝005 授權歸檔寫入面＋
  006 回收桶讀端 list／restore（復原＝鎖內固定序五腿重驗、詳 ADR 0055）——選單域
  advisory 鎖底座 key `0x7265_7635_6D65_6E75`＋`insert_archived` role_id 反查內收＋
  reason gate 五值集（006 擴 menu_revoke／button_revoke）；固定鎖序 advisory→歸檔表列→
  sys_role 列→sys_menu 列→casbin_rule、防環上溯上限 64、routeName 形制上限 100——憲法
  島 H「常數留活書」落點；判定面 rebuild-swap 熱重載機制詳 ADR 0049＋`auth/enforce.rs` doc；
  `sys_casbin_policy`＝006 三維授權寫入面——plan_full_replace／apply_full_replace／
  settle_txn 全量替換核（射程＝候選集、ADR 0056）＋protected_endpoint_set 封死謂詞鎖內
  現查（ADR 0054）＋scope_live_to_candidates 三路同用；自管 txn、選單／按鈕維入選單序列
  化域、端點維與 restore 不入域；handler 消費面＝role.rs 三維六支＋policy_archive.rs 兩支）＋src 側測試共用設施
  `model::test_db`（清理守衛／列態 fixture／真 app 與端殼 helper／PG 層 fault-injection seam
  ／跨檔共用常數之名冊，連同各支「為何非有不可」與 sequence 兩套紀律，全文住該模組 doc 與
  各型 doc——ADR 0062 下放、本書不複述名冊）。
- **IP 域模組拓樸**（004 落地）：`trust/`（信任錨純函式核：`resolve_client_ip` 三層判定＋
  兩層覆蓋、`apply_chain_overflow` 鏈長短路、`to_canonical` 折疊、`TrustModel::is_trusted`）／
  `ipgate/`（規則判定純函式 `decide`＋`build_ruleset`＋防自鎖 `would_self_lock`＋讀端
  `load_ruleset`＋門鈴 `reload_and_publish`／`spawn_ipgate_watcher`）／`middleware/`
  （`request_context_mw`＋`ip_gate_mw` 兩支）／`request_context.rs`（`RequestContext` 型＋
  三個建構點 `from_trust`／`from_headers`／`new`——鑑識三欄的唯一產出處）／`config.rs` 的
  `load_trust_model`（啟動時一次載入、唯讀共享）。狀態容器 `AppState` 自本刀起為**七欄**
  （既有五欄＋`trust_model`／`ip_rules`；ADR 0041）。
- **user 域模組拓樸**（007 落地）：`handler/user.rs`（管理面十支端點薄殼＋寫端收尾式
  `finish_user_write`——commit→denylist 廣播→條件式 `reload_enforcer` 的唯一腿，`pub(crate)`
  供自助改密共用，跨 handler 消費者另有名冊閘守）／`handler/user_center.rs`（自助兩支
  changePassword／getPasswordPolicy，皆 `Protection::Authed`、零 casbin seed、不計入 policy
  端點數）／`auth/no_escalation.rs`（島 I7 包含規則 `T ⊆ A ∧ N ⊆ A` 的具名純函式，八支使用者
  寫端＋unlock 帳號維共用；與 `enforce.rs` 的 middleware 四參掛點分屬路徑級與 body 級兩射程）／
  `model/facade/sys_pwd_custody.rs`（設密經手帳；只存時戳、零密碼材料，`touch` 與密碼欄 UPDATE
  同交易）／`throttle/change_pwd.rs`（**第三個**節流子系統：判定鍵 uid、兩態無軟區、fail-open、
  鍵前綴 `cpwd:` 與登入節流分離、降級自成第十三源；ADR 0066）。密碼政策核心住 `model/password.rs`
  ——單一驗證點、**七個設定鍵**單快照讀、缺鍵 fail-default，三個設密入口（addUser／resetUserPassword／
  changePassword）共用；雜湊**生成**恆於取鎖前算好再進鎖、**驗證**依島 I1 於鎖內執行（ADR 0068）。
- **test_db 名冊本刀新立三支**：`SeedUserRestoreCleanup`（seed 帳號被改欄後的還原，本刀的寫端測大量
  改動 seed 三帳號）／`PwdCustodyCleanup`（custody 首寫的 RAII 清理）／`SessionRevokeCleanup`（鍵＝uid
  而非單一 sid——
  撤銷測一次產生 N 個 sid 且 N 於起手時點未知，既有兩守衛結構性涵蓋不到）；另**既有** `UserCleanup`
  本刀補三腿（業務鍵腿＋操作稽核腿＋`sys_user_id_seq` 還原）。逐支「為何非有不可」同前住模組 doc、
  本書不複述（ADR 0062）。
- **觀測面**：`/metrics` Prometheus exposition；序列一律 boot 時 pre-register 顯式 0
  （防「事件未發生＝序列缺席」使 `rate()` 失去基線——`obs.rs` 檔頭鐵律）。auth 刀新增
  三序列：`denylist_hit_total`（source＝redis／pg 恰二）、`throttle_degraded_total`
  （source 恰十三、值集權威＝`obs::THROTTLE_DEGRADED_SOURCES`；003 立為六源、004 之
  IP 域刀重推為十二源、007 之改密節流自成第十三源）、`throttle_soft_zone_total`（無 label）；004 之 IP 域刀再新增
  兩序列：`ip_domain_degraded_total`（kind 恰五、值集權威＝`obs.rs` 的
  `IP_DOMAIN_DEGRADED_KINDS`〔**crate 內私有 const**、非跨 crate API〕，逐字取自該刀
  data-model §5 降級矩陣）、`ipgate_blocked_total`（**無 label**——阻擋**不屬
  降級類**，且網段做 label 等於把序列基數交給營運面輸入；命中網段等結構化欄位改由
  `ip_gate_mw` 的告警承載，理由見 `obs::IPGATE_BLOCKED_TOTAL` 的 doc）；
  另有 002 起的 `casbin_enforce_total`（decision 三值）、005 之 `casbin_reload_total`
  （outcome 三值 ok／retry／exhausted——判定面 rebuild-swap 同步結果，發射點
  `auth/enforce.rs::reload_enforcer`、預註冊 `obs.rs`；ADR 0049）與 axum-prometheus
  HTTP 請求級三序列。
  ★**本清單的複驗法**（現在式清單不會自己跟上新刀，故把量測法寫在此處而非只寫結論）：
  `grep -rn 'metrics::counter!\|metrics::gauge!\|metrics::histogram!' rust-api/server/src/`
  枚舉**全部發射點**，逐條比對本段——序列名一律經 `obs.rs` 的具名常數或
  `pre_register_metrics` 的字面，故枚舉面完整。2026-08-18（005-role-menu-crud 之判定面
  同步單元收尾）實跑結果＝**本段清單與發射點全等、零缺零多**。

## §6 Runtime

不變式凍結面住 constitution §I.7（**十座**行為島 A～J＋fail-* 方向）；本節只寫 as-built 執行形
——模組落點、常數實值、欄與鍵名（§I.7 進場規則明文把這一類留在活書）。凍結條文一律
以「主題＋落點＋指島」形給指針，不複述 MUST 文字（複述＝同一事實兩個人寫的家，
Amendment 改憲法而活書靜默過期）。

### 信任錨與 IP 存取閘

- **位置**：兩支 middleware 掛在管線最外側業務層（掛載序見 §5「server crate 管線形」）；
  IP 閘**先於身分驗證**——被擋的來源不該有機會走到驗章與政策判定，該序由
  `wired_router_ip_gate_runs_before_identity_enforcement` 釘住。
- **信任錨還原**（`trust::resolve_client_ip`）：鏈＝`normalize(XFF) ++ [傳輸層對端]`——反向
  代理以 `$proxy_add_x_forwarded_for` 在**最右**附加其觀察到的對端，故鏈右端恆為我方基建。
  三層判定序（①對端閘②CDN 位置錨③受信轉發 walk）＋兩層覆蓋（通道回退、邊緣驗證升等），
  凍結面＝constitution §I.7 島 F。對端的權威源＝
  `into_make_service_with_connect_info::<SocketAddr>()`（缺席即退回讀**可偽造**的標頭並發
  告警；機器守＝`server/tests/serve_connect_info_lint.rs`，見 §8 API 慣例）。
- **態語意**：錨還原產出**七態**，而 `ip_confidence` 欄值域為**八態**——第八態
  `chain_rejected` 是三層矩陣**之前**的短路（鏈跳數逾 `trust::MAX_XFF_TOKENS`＝**32**），
  與其餘七態**不同軸**（ADR 0043）。字面的唯一產出點＝`trust::Confidence::as_str`：
  `cdn_verified`（邊緣驗證交叉比對相符，最高）／`proxy_clean`（walk 解出、每跳合預期）／
  `direct`（對端不受信、直取對端，偽造不了）／`cdn_anchored`（位置錨解出、未經交叉比對）／
  `proxy_soft`（walk 經 `dual_role` 出口或綁定右鄰不符）／`cdn_mismatch`（驗證標記為真但
  推導不一致＝異常留痕）／`fallback`（整鏈受信／無可取，退回對端，最低）／`chain_rejected`。
  ★末者 **MUST NOT 讀作「該請求未被服務」**：標記由 `request_context_mw` **全域**施加、
  而**拒絕只在登入端點** ⇒ 同一字面在 `sys_login_attempt` 恆為「被拒」（該表唯一寫入者是
  login）、在 `sys_operation_log` 則是「鏈逾上界但請求**仍被服務**」——**分表判讀**。
- **IP 閘判定序六步**：①健康／觀測端點放行（`middleware::GATE_BYPASS_ENDPOINTS`＝
  `/health`、`/metrics`）②請求上下文缺席放行（fail-open，計
  `ip_domain_degraded_total{kind="request_context_absent"}`）③結構豁免六段（loopback v4／v6、
  RFC1918 三段、ULA `fc00::/7`）④allow 袋 any-match ⑤deny 袋 any-match（阻擋＋
  `ipgate_blocked_total`＋帶命中網段的結構化告警）⑥預設放行。★**白＞黑**由「④寫在⑤之前」
  這個固定序表達、**不是**由任何排序欄位表達 ⇒ 判定與載入順序無關。★③只豁免**阻擋**、
  **不豁免節流**（來源維 L0 短路直讀 allow 袋、不經 `ipgate::decide`）。
- **判定面**：`AppState.ip_rules` 為 `ArcSwap<RuleSet>`（放行袋／阻擋袋），每請求零外部
  查詢；變更時**整份換版**，來源不可讀時沿用上一份良好規則。**門鈴機制**（規則熱重載）：
  四個寫端（新增／編輯／軟刪／復原）於同交易 commit 後呼
  `ipgate::reload_and_publish`——重讀有效列→`ArcSwap` 換版→redis `PUBLISH ipgate:invalidate`
  （頻道名單一權威＝`ipgate::IPGATE_INVALIDATE_CHANNEL`）；各行程的 `spawn_ipgate_watcher`
  訂閱該頻道、收訊即 `reread_keeping_last_good`。★**payload 不帶語意、收訊端只認頻道** ⇒
  繞過端點的 SQL 直改（如走查的 `TRUNCATE`）**不會按門鈴**，須手動 `PUBLISH` 一次。
  ★訂閱連線顯式開 TCP keepalive——建連逾時罩不到訂閱成功**之後**的半開連線（L-034）。
- **dev 可達二態**（誠實分界、不是漏填）：dev 掛的最小信任模型
  （`deploy/trust-model.dev.toml`——只填 `internal_default`、其餘五集合刻意留空）下，經
  反向代理的端到端走查**可達二態**＝`fallback`（不帶構造標頭⇒鏈兩跳皆受信⇒整鏈受信回退）
  與 `proxy_clean`（帶 `X-Forwarded-For: 203.0.113.x`）；其餘五態需宣告 `cdn`／`my_public`／
  `bindings`／`cf_gate_egress` 或需對端不受信 ⇒ dev 結構性不可達，改由整合測試以「直餵
  `TrustModel`＋任意 peer／標頭」覆蓋。★要在 dev 追加態，**是加設定、不是改判定碼**。

### 會話狀態機（sys_token）

```
login ──insert──▶ active ──rotate（舊列轉 rotated＋used_at → 插新 active）──▶ rotated
                    │                                        │
                    │ logout／被踢／reuse 撤家族              │ grace 窗（30s、redis）內同票再呈遞
                    ▼                                        ▼   ＝冪等回既發同一對（不再轉列）
                 revoked                          grace miss ⇒ 撤整條家族（觸發形＝§I.7 島 A）
```

- 一條會話＝一條 `rotation_chain`（sid）；`active` 唯一性之 DB 護欄 as-built＝m001 建的
  partial UNIQUE index `uq_sys_token_chain_active`（不變式＝constitution §I.7 島 A）。
- TTL as-built：唯一輸入＝`session_idle_timeout`（分鐘、seed 60），公式住 `auth/jwt.rs`
  ——`access = min(300, N×60/2)`／`refresh = N×60 + access`，seed（N=60）下即 300s／3900s；
  ★不可簡寫成 `+ 300`：`session_idle_timeout` 值域下界為 5，N∈[5,10) 時 access＝N×30＜300，
  兩式分岔（N=5 實為 450 而非 600）；且島 D 的門檻＝`refresh − access` 恆等於 N×60 這件事，
  只有在加 access 的形下才讀得通。
  rotate-grace 冪等窗＝`cache::GRACE_TTL_SECS`（30s）。
- 撤銷讀面 as-built：redis 鍵 `session:denylist:{sid}` 存 reason 字面（`REASON_KICKED`／
  `REASON_REVOKED`／`REASON_ADMIN_KICK` **三常數**集中於 `cache/mod.rs`），enforce_mw 讀端
  **三向分派**（見下「使用者域斷權」）；權威關係、TTL 值與缺鍵語意＝constitution §I.7 島 C。
- single-session as-built：政策兩鍵＝`sys_user.session_policy`＋system_settings
  `single_session_default`，`effective_single` 判真後於 `handler/auth/login.rs` ⑨~⑪ 步
  同 txn 撤其他 chain 並落稽核、commit 後才 best-effort 廣播 denylist；兩層解析式與
  踢除義務＝constitution §I.7 島 B。
- idle 逾時 as-built：`session:{sid}:last_activity` 由 enforce_mw 放行後 best-effort 推進、
  事件冪等標記鍵＝`session:idle-emitted:{sid}`；門檻式、事件僅首次落與「不寫 denylist」
  ＝constitution §I.7 島 D。
- 會話終止稽核＝`session_event` append-only **五事件**（reuse／kicked／idle／logout／revoked）。

### 登入失敗節流三區（帳號維＋來源維）

```
帳號維 count（滑動窗、PG sys_login_attempt 權威；鍵＝attempted_user_name 送出原文）
  0 ~ captcha_after(2)-1         ＝ 自由區 → 密碼驗證、失敗落列推計數（1000）
  captcha_after ~ max_fails(5)-1 ＝ 軟區   → 須先過圖形驗證碼（缺／錯／過期＝2222
      captchaRequired），過關才進密碼驗證
  ≥ max_fails(5)                 ＝ 鎖定   → 2222 locked（L1 redis 負快取短路）
來源維 count（滑動窗、同一張表；鍵＝real_ip 經 throttle::ip_bucket 導出的計數桶——
              v4 逐位址 /32、v6 先截主機位元聚合至 /64）
  0 ~ ip_captcha_after(10)-1            ＝ 自由區
  ip_captcha_after ~ ip_max_fails(50)-1 ＝ 軟區
  ≥ ip_max_fails(50)                    ＝ 鎖定（該維自己的 L1 鎖鍵）
合成（spec FR-025 逐字）：任一維硬鎖 → 硬鎖；否則任一維軟區 → 軟區；否則放行。
  ★兩維的拒絕**共用同一組 msg key**——回應不揭露是哪一維觸發的。
  ★來源不可得（real_ip 為 unspecified 哨兵）或命中 allow 袋 ⇒ 來源維整層跳過、帳號維
    照常（前者＝fail-open，後者＝憲法島 F 之 F5 的 L0 短路）。
```

- 門檻**六鍵** as-built（皆住 system_settings）：帳號維＝`login_throttle_captcha_after`／
  `login_throttle_max_fails`／`login_throttle_window_minutes`（seed **2／5／15**）；
  來源維＝`ip_captcha_after`／`ip_max_fails`／`ip_window_minutes`（seed **10／50／15**）。
  判定次序（密碼雜湊驗證之前）與「零稽核列、零計數桶」義務＝constitution §I.7 島 E。
- ★★**兩維的方向差**（004 U-J／T046 拍板結論，**最容易被後續維護「順手統一」抹掉**）：
  - **計數窗下界**：帳號維取 `GREATEST` **三源**（窗起點／窗內最近一次成功登入／解鎖標記）
    ⇒ reset-on-success 由查詢形免費兌現；來源維**恆兩源**（窗起點／解鎖標記）、
    **禁 reset-on-success**——第三源移植過來即反轉為破口：攻擊者持任一有效帳號在同一來源
    穿插一次成功登入就能清零該來源計數，恰好繞過本維所針對的輪換帳號名攻擊。
  - **`chain_rejected` 列的計入**：帳號維**必須排除**（`ip_confidence IS DISTINCT FROM
    'chain_rejected'`）、來源維**刻意不排除**（FR-050／ADR 0043）。理由＝**鍵不對稱**：
    帳號維鍵是 `attempted_user_name`＝**受害者**且由攻擊者在 body 內自選，納入即等於
    「攻擊者可指定誰被鎖」；來源維鍵是 `real_ip`＝**攻擊者自身**且由信任錨錨定（塞標頭
    改不動它），納入不會誤傷第三方、還讓拒絕列消耗他自己的來源額度。
    ★**勿寫成「封成長」**——那個舊理由已於 2026-08-16 實測**證偽**並隨憲法 v1.6.1 勘誤：
    拒絕腿在 `throttle::precheck` **之前**就 return，敵意鏈請求從不進入來源維判定，
    加不加過濾都封不住該腿自身的落列速率（速率上界在反向代理層的 `limit_req`）。
- 圖形驗證碼＝無狀態簽章題（HS256、leeway=0、nonce 消耗標記 SET NX＝一次性）；
  發題對任意 userName 一律發（零存在性洩漏）、題綁發題帳號。
- 降級腿方向（redis 失聯＝軟區停用續驗密碼、PG 查詢失敗＝歸零放行＋`captcha_forced`
  補償等）凍結於 constitution §I.7 島 E；訊號面＝`throttle_degraded_total` source 恰十三（第十三源＝007 之改密節流、自成一格）。

### 使用者域斷權與密碼三入口（007 落地）

- **denylist 三 reason 的分派**（島 I2「三 reason 不互換」的 as-built）：`REASON_REVOKED`
  →8888 silent，涵蓋**四路**（停用／刪除／重設密碼／自助改密）；`REASON_ADMIN_KICK`→7777 modal
  ＋文案 `auth.session.kickedByAdmin`，恰一路＝管理員踢除；`REASON_KICKED`→7777 modal＋既有文案，
  恰一路＝single-session 頂替。★未知字面落 8888 側。★字面互換在 PG 面、稽核面與回應信封上
  **全部看不出來**，故逐呼叫點各有一顆掛真 redis 的紅點守著（名冊住 `finish_user_write` doc）。
- **兩套詞彙不共用**：`session_event`（PG 稽核）與 denylist（redis 快取）字面偶有重疊
  （`admin_kick`）純屬對照方便。`session_event.event_type` 恰五、`reason` 恰七（003 之
  `single_session`／`idle_timeout` ＋007 之 `user_disabled`／`user_deleted`／`password_reset`／
  `password_changed`／`admin_kick`）——五個新 reason 配 `revoked` 事件分辨撤銷來源。
- **撤銷的交易邊界**：撤票與逐 sid 事件由 facade 於**同一交易**落定（PG-first）；handler 的
  `finish_user_write` 只做 commit 後的 best-effort denylist 廣播＋條件式判定面同步。denylist
  TTL＝`refresh_secs`（取 access_secs 會讓被撤者於 (access, refresh) 窗內換發時讀得 nil
  ＝「未撤」而放行）。判定面同步的觸發矩陣＝ADR 0067 款二。
- **密碼三入口共用單一政策驗證點**（`model/password.rs`）；守門序 as-built：
  - `addUser`：形制→現役唯一→信箱格式→roleIds 存在→N ⊆ A→**政策**→冷卻**免判**（新 id 無
    前次可比）但 custody **照落**（初始密碼計入冷卻帳，否則「建帳後立刻重設」白得一次免費機會）。
  - `resetUserPassword`：notFound→self→T ⊆ A→**政策**→**冷卻**→UPDATE＋custody touch＋撤全 active。
  - `changePassword`：**節流**（uid 維、5 次／900 秒，落在 argon2 verify **之前**、拒絕路徑零計數
    推進）→帳號存在→兩次一致→**舊密驗證**→新≠舊→**政策**→**冷卻**→UPDATE＋custody touch＋
    撤其他 active（**保留當前 sid**）。
  ★**政策恆排在冷卻之前**：兩者同時成立時，先讓使用者知道密碼哪裡不合格，比先叫他等幾十秒有用。
  ★門檻的家不同：政策**七鍵**與冷卻 interval 住 `system_settings`（★權威＝`password::PASSWORD_POLICY_KEYS`；
  「八」是**違規碼**數、其中 `maxBytes` 是碼內常數不是設定鍵——兩者不可互推），改密節流門檻是碼內常數
  （判準＝ADR 0066 決定三）。
  ★**登入路徑 MUST NOT 驗政策**（島 I5 明文）：seed 帳號密碼短於政策下限，驗了即結構性自鎖；
  有源碼掃描守。

## §7 部署

（本節尚無內容；compose 拓樸敘事隨 dev stack 刀填入。）

## §8 橫切概念

### fork-delta 接線現況（base-web）

★ 軌道逐條 as-built 接線形、機器守清單與射程界線 ☞ `docs/arc42/FORK-DELTA-WIRING.md`
（本書附屬文件、同受 Lint07／Lint10／Lint11；自本節下放＝ADR 0062）。授權面仍＝constitution
§III.2 名冊；本節不承載內容。

### 資料慣例

- **schema 基線現況**：PostgreSQL（表清單／欄型正典＝`docs/generated/reference/schema.md`
  真表）；對 pristine 重放 m001（結構）＋m002（seed、
  完全決定性）兩支 migration 即得全庫（ADR 0006）。每表歸屬 constitution §I.6 archetype
  四變體（A 業務全六欄／B append-only／C join·狀態機·衛星／D 治理）之一，歸屬帳＝
  `docs/ops/reference-src/archetype-map.json`（新表先登記後進場、audit 閘表清單守門）。
  漂移防線＝三閘（`tools/schema-gate.py`：gate1 結構／gate2 欄序與 seed／audit archetype）
  ＋受管演進帳（`docs/ops/reference-src/schema-evolution.json`）——凍結面
  （`specs/001-schema-baseline/fixtures/`、永不改寫）⊕演進登記合成期望值、與實庫全等
  比對；合法演進唯一出口＝登記檔一筆、未登記漂移即紅（ADR 0007）。
- **memo 欄家族**：user_memo／role_memo／menu_memo／wbip_memo（text 可空、可多行）＝
  R_SUPER 備註——顯示於管理列表、不顯示於其它被取用處（下拉／引用／對外 API 一律不帶）；
  role_desc（使用者可見「角色描述」）與 role_memo 職責不同、並存不合併（語意權威＝
  `specs/001-schema-baseline/data-model.md` §5；四張管理列表的 UI 兌現**已於 007-user-password-admin 收齊**
  ——`sys_user` 是最後一張，該刀同批關帳）。
- **ORM 關聯與行為層紀律**（002 拍板、spec FR-022）：①關聯宣告只映真 DB FK——無 DB FK
  之邏輯關聯不建 Relation、需要即手寫 join（關聯真相單一來源＝DB FK）；
  ②`ActiveModelBehavior` 恆空實作——ORM 行為層不承載六審計欄自動化、審計欄由
  model/facade 顯式成對寫（憲法 §I.6 成對條款）；守門＝`server/tests/entity_behavior_lint.rs`。

### API 慣例

- **部分更新三態**（ADR 0023；射程＝部分更新請求 body 之每一可選欄）：欄位缺席＝不動、
  JSON null＝顯式清空（NOT NULL 欄拒收 2222）、有值＝設值；解析層以 `Option<Option<T>>`
  三態型別區分「未出現」與「null」，★並以自訂 `deserialize_with` 承載——單靠型別，serde
  的預設 Deserialize 會把 JSON null 也落外層 `None`、與缺席不可辨（三態塌兩態；L-009）。
- **序列化與傳輸層守門**：`Serialize` 型 i64 欄逐欄過 envelope 2^53 守衛（typings 宣告 string
  者走 `serialize_i64_as_string`）＝`server/tests/wire_i64_guard_lint.rs`；serve 的 `ConnectInfo`
  備線＝`server/tests/serve_connect_info_lint.rs`；信任模型 IPv4-mapped 網段字面＝告警＋清空該集合。

### 授權慣例

- **判定單點與 DB-fresh**：授權判定收斂於單一純函式進入點（server/src/auth/enforce.rs）；
  角色每請求現查 DB、不快取亦不採信 token 附帶——角色一撤、下一請求即生效。
- **拒絕語意**（ADR 0022）：無權＝5003＋HTTP 403、msg＝純 i18n key、不揭露政策明細與
  持有角色；授權面內部故障＝5000、不偽裝成 403。
- **no-escalation 兩射程**（形＝ADR 0022 定形、真邏輯＝007）：middleware 掛點
  `no_escalation_check`（單一呼叫點、簽章預留 async＋db）**恆放行**＝路徑級上限位；真判定住
  handler 鎖內的具名純函式（`auth/no_escalation.rs`）＝body 級指派集。★中介層取不到 body、
  亦取不到鎖內的 T ⇒ 兩位置不是「暫時的」與「正式的」，是**不同射程**。deny 與政策拒絕同出口。
- **三維授權治理**（006）：期望全集全量替換（diff 由系統導出）、射程＝候選集（候選外既得
  原封、界外靜默略過；ADR 0056）；protected 撤銷整批拒 `protectedRevoke`；結構性封死＝謂詞
  式（ptype=p ∧ protected ∧ v2∈動詞）鎖內現查、掛 updateRoleEndpoints＋restore 第③腿、拒因
  `protectedGrant`（ADR 0054）。回收桶：撤銷＝archive-move 完整快照、復原＝鎖內固定序五腿
  重驗（ADR 0055）、restorable 派生旗標與①～④腿同判準。觸發面：grant 面 Applied 即判定面
  同步不問 diff（刻意例外、與移除面 if-archived 並陳）、呼叫點名冊機器守（007 起**四檔**）；生效語意＝
  API 判定即時、前端選單／按鈕面下次載入生效（FR-022）。
- **使用者域授權**（007）：**包含規則** `T ⊆ A ∧ N ⊆ A`（A＝操作者現役角色集、持 `R_SUPER`
  者之 A 視為**全集**；T＝標的全部指派列、不濾角色狀態；N＝寫後角色集）——凍結面＝島 I7。
  掛滿**八支使用者寫端＋unlock 帳號維**，判定序排在 seed 保護與 self 諸不**之後**、業務守門
  **之前**；來源維解鎖不套（標的是位址、無角色可比）。同級互管**允許**（`A ⊆ A` 成立）。
  ★`addUser` 不因「T 恆空」而結構性恆過——`N`＝請求 roleIds 可越界，「新開一個超管帳號」是最
  直接的提權路徑，故它進名單。
- **前端不預判包含規則**（FR-020）：角色下拉全列、列級鈕只依按鈕碼顯隱，後端為唯一裁判。
  預判會讓前端多一份必須與後端同步的規則副本，而兩份規則分岔時使用者看到的是「按鈕不見了」
  而非「被拒絕了」——後者可診斷，前者只能猜。
- **按鈕 gating 的判準**（釋義＝ADR 0063 款三）：**該頁 menu 維政策是否僅 `R_SUPER`**。
  僅 `R_SUPER` ⇒ 門已在頁級（進不來就談不上按鈕），頁內不做逐鈕 gating（`manage_role`／
  `manage_menu` 屬此）；含非超管角色 ⇒ 逐鈕 gating（`manage_user`＝{R_SUPER, R_ADMIN}，
  故七枚按鈕碼逐鈕判）。★判準是**政策實況**、不是頁面的重要性。
- **名冊閘的射程紀律**（007 擴三張）：`reload_enforcer` 呼叫點名冊之外，另有
  `finish_user_write` 跨 handler 消費者、`no_escalation` 判定呼叫點、`guard_no_escalation`
  掛點消費者三張。★**新增名冊的觸發條件＝可見性放寬**：把一支內含受管呼叫的函式由私有提升為
  `pub(crate)`，借道者就能觸發該行為而自身檔案不出現受掃 token ⇒ 上一道名冊閘的射程被打穿
  （L-069）。凡提升這類函式的可見性，同批補一張消費者名冊。

## §9 架構決策

決策全文住 docs/arc42/decisions/（一決策一檔）；索引住 docs/generated/DECISIONS-INDEX.md。
本節不承載內容。

## §10 品質要求

（本節尚無內容；fail-open／closed 語意總表隨行為刀填入。）

## §11 風險與技術債

待辦與候選 ☞ ops/BACKLOG；坑與防法 ☞ ops/LESSONS。本節不承載內容。

## §12 名詞表

- **刀**：一個 feature 的完整交付單位（brainstorm→SDD→TDD→收刀）；縱切刀＝功能縱貫、橫切刀＝慣例橫貫。
- **收刀**：feature merge 回 default branch＋簿記三步（events append＋NOTES＋generate）＋perf 第四步（簿記 commit 落地後量其牆鐘、append `close_bookkeeping` perf 事件；ADR 0070）。
- **輕量軌**：維護項不開 SDD 的交付軌（分支＋編排單元＋merge＋misc 事件收單）；判準與程序見 CLAUDE.md §2。
- **島**：具狀態機性質的行為子系統（如 token rotation）；其不變式經 amendment 入 constitution §I.7。
- **軌道**：constitution §III 授權的 base-web 改動邊界類別。
- **短名／長名**：目錄與口語用短名（base-web／rust-api）；git 分支用長名（rev5-admin-*）。
- **pin**：外層 repo 記錄的 submodule commit SHA；單元邊界即時 bump。
- **活書**：本檔——現在式 as-built 敘事，人寫、lint 守約。
- **事件源**：docs/ops/events.jsonl——收刀／review／里程碑／勘誤／效能資料點（perf）的 append 型單一事實源；perf 型不入 MILESTONES、人讀 reference/perf。
- **傘狀 repo**：本 repo；只記文件、spec、gitlink pin，不含子體實碼。
- **停用／軟刪**：停用＝`status` 轉 `'2'`（列仍在、可再啟用）；軟刪＝`deleted_at` 落值（自現役面
  消失、可經回收桶復原、status 保留零回灌）。兩者皆撤標的全部 active 票。
- **踢除／撤銷**：踢除＝管理員的**顯式**斷線（denylist `admin_kick`→7777 modal）；撤銷＝停用／
  刪除／重設密碼／自助改密**連帶**發生的失效（`revoked`→8888 silent）。★DB 面同為 token 轉非
  active，差別只在 reason 字面與使用者看到的碼；互換即體驗錯位而無斷言會紅（島 I2）。
- **鎖定**（登入節流域）：計數逾門檻後**新的登入嘗試**被拒；不動 token、不寫 denylist，解除靠
  `unlockLogin` 或等窗過。★已持未過期 token 的人**既有 session 照常**——鎖的是門，不是屋內的人。
- **重設密碼／修改密碼**：重設＝管理員對**他人**（`resetUserPassword`、無需舊密、撤標的全部
  active 票）；修改＝本人對**自己**（`changePassword`、需舊密、撤其他 active 票但**保留當前**）。
  ★共用同一政策驗證點與同一冷卻帳；self 是兩者相反的禁區——管理端禁對自己重設、自助端只能對自己。
