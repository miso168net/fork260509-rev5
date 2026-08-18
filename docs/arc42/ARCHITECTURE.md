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
管理員解鎖端點）就位；其餘域隨波次建置。

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
  資料面 `model/facade/` **十支**（session_event／sys_ip_rule／sys_login_attempt／
  sys_menu／sys_operation_log／sys_role／sys_token／sys_user／sys_user_role／
  system_settings）＋src 側測試共用設施 `model::test_db`（守衛**八件**＝`SequenceResetGuard`
  ／`ChainRowsCleanup`／`LoginAttemptCleanup`／`SessionEventCleanup`／`IpRuleCleanup`／
  `OperationLogCleanup`／`SessionIdCleanup`＋列態 fixture `UserStatusFixture`，各支「為何
  非有不可」逐條寫在其型 doc；其中**六支**各配一支核心自證測——`OperationLogCleanup` 依其
  型 doc 的收窄集理由刻意不配、`IpRuleCleanup` 尚無（帳在 B-085）。另有真 app 建構
  `real_app_with`、測試簽章、跨檔共用常數 `REDIS_TTL_SLACK_SECS`）。
- **IP 域模組拓樸**（004 落地）：`trust/`（信任錨純函式核：`resolve_client_ip` 三層判定＋
  兩層覆蓋、`apply_chain_overflow` 鏈長短路、`to_canonical` 折疊、`TrustModel::is_trusted`）／
  `ipgate/`（規則判定純函式 `decide`＋`build_ruleset`＋防自鎖 `would_self_lock`＋讀端
  `load_ruleset`＋門鈴 `reload_and_publish`／`spawn_ipgate_watcher`）／`middleware/`
  （`request_context_mw`＋`ip_gate_mw` 兩支）／`request_context.rs`（`RequestContext` 型＋
  三個建構點 `from_trust`／`from_headers`／`new`——鑑識三欄的唯一產出處）／`config.rs` 的
  `load_trust_model`（啟動時一次載入、唯讀共享）。狀態容器 `AppState` 自本刀起為**七欄**
  （既有五欄＋`trust_model`／`ip_rules`；ADR 0041）。
- **觀測面**：`/metrics` Prometheus exposition；序列一律 boot 時 pre-register 顯式 0
  （防「事件未發生＝序列缺席」使 `rate()` 失去基線——`obs.rs` 檔頭鐵律）。auth 刀新增
  三序列：`denylist_hit_total`（source＝redis／pg 恰二）、`throttle_degraded_total`
  （source 恰十二、值集權威＝`obs::THROTTLE_DEGRADED_SOURCES`；003 立為六源、004 之
  IP 域刀重推為十二源）、`throttle_soft_zone_total`（無 label）；004 之 IP 域刀再新增
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

不變式凍結面住 constitution §I.7（六座行為島＋fail-* 方向）；本節只寫 as-built 執行形
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
  告警；無機器守＝ops/BACKLOG B-075）。
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
  `REASON_REVOKED` 兩常數集中於 `cache/mod.rs`），enforce_mw 讀端映 7777 modal／
  8888 silent；權威關係、TTL 值與缺鍵語意＝constitution §I.7 島 C。
- single-session as-built：政策兩鍵＝`sys_user.session_policy`＋system_settings
  `single_session_default`，`effective_single` 判真後於 `handler/auth/login.rs` ⑨~⑪ 步
  同 txn 撤其他 chain 並落稽核、commit 後才 best-effort 廣播 denylist；兩層解析式與
  踢除義務＝constitution §I.7 島 B。
- idle 逾時 as-built：`session:{sid}:last_activity` 由 enforce_mw 放行後 best-effort 推進、
  事件冪等標記鍵＝`session:idle-emitted:{sid}`；門檻式、事件僅首次落與「不寫 denylist」
  ＝constitution §I.7 島 D。
- 會話終止稽核＝`session_event` append-only 四事件（reuse／kicked／idle／logout）。

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
- ★★**兩維的方向差**（004 U-J／T046 拍板結論，**最容易被日後「順手統一」抹掉**）：
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
  補償等）凍結於 constitution §I.7 島 E；訊號面＝`throttle_degraded_total` source 恰十二。

## §7 部署

（本節尚無內容；compose 拓樸敘事隨 dev stack 刀填入。）

## §8 橫切概念

### fork-delta 接線現況（base-web）

授權面＝constitution §III.2 名冊（授權歸憲法、本節只記 as-built 接線形；**條數以該名冊
為準、本節刻意不複述**——複述即第二份會漂的手抄計數）。003 起實接之 ★ 軌道逐條如下：

- **★BASE-WEB-AUTH-WIRING**：(a) `store/modules/route/index.ts` constant routes **併入**
  static 常量集（seed `constant=TRUE` 現 0 列、取代形會清空五條 builtin）；(b) 三張替代
  登入表單改打 `rev5-auth.ts` 誠實 stub（恆 2222 notSupported）並消滅假成功 toast；
  (c) `hooks/business/captcha.ts` 改打 `/auth/sendCaptcha` stub、假延遲與假成功 toast 移除。
- **★BASE-WEB-LOGIN-CAPTCHA-WIRING**：(i) login 簽名加 captcha 參＋失敗 msg 回傳鏈
  （`store/modules/auth/index.ts`）；`pwd-login.vue` 軟區條件渲染 220×120 驗證碼欄，
  非軟區零行為變更。
- **★BASE-WEB-I18N-WIRING**：(i) `service/request/index.ts` 之 `translateBackendMsg`／
  `translateDetailValue`——後端 msg（穩定 i18n key）經 ``$t(`backend.${msg}`, msg)`` 顯人話、
  未命中以原文 graceful fallback；(ii) `en-us.ts`／`zh-cn.ts` 各插 backend 樹（**28 鍵**＝
  003 之 22 鍵＋004 T038 之 `biz.ipRule.*` 五鍵＋004 T054 之 `biz.throttle.*` 一鍵；
  兩語鍵集機器守相等）；(iii) `app.d.ts` 補 backend 必填型節。
- **★BASE-WEB-LOGOUT-UX-WIRING**：(i) `user-avatar.vue` 登出前 best-effort
  `fetchLogout`（失敗不阻斷 `resetStore()`）。
- **★BASE-WEB-MANAGE-PAGE-WIRING**：(i) IP 規則管理頁進場——兩語 locale 之 `route:` 樹加
  `manage_ip-rule`、`page:` 樹加 `manage.ipRule.*`；`app.d.ts` 補 `Schema.page` 型節；
  路由外掛產物**四檔**（`router/elegant/{imports,routes,transform}.ts`＋
  `typings/elegant-router.d.ts`）**由外掛重算產出**、採**產物檔紀律**（禁手改、不逐行標記
  ——標記於下次重算即被抹除、物理上不可維持）。

機器守（`tools/fork-delta-lint.py`、`tools/view-render-guard.py`、
`tools/route-artifact-gate.py`、pre-commit）：修改型標記逐處帶 `原行:`＋軌道名 ∈
授權名冊斷言（名冊掃自 constitution §III.1/§III.2 表格、掃空即 die）；新增型圈界；
「假成功 toast 不得回歸」四檔靜態斷言與「`$t` fallback 不得退化」斷言（B-061／B-062 收單）；
管理頁 `views/manage/**` 零原始 HTML 插值（FR-038）。
★**射程界線**：`fork-delta-lint` 的 `scan()` 對「基線沒有的檔」結構性豁免 ⇒ **rev5 新檔的
檔頭標記不受機器守**（004 U-I 變異實測：拿掉新檔標記，lint 仍全綠），該面屬紀律；受機器
守的是**基線既有檔**的修改型與圈界。★路由外掛產物四檔受 fork-delta **全域豁免**，其唯一
機器守＝`route-artifact-gate` 的產出檔集對賬／重算冪等／零手改三道（★第三道以**上游基線**
為種：以版控為種重算時，外掛的 magicast 增量合併會讓手改過的行原封不動活下來、第二道全綠）。

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
  `specs/001-schema-baseline/data-model.md` §5；UI 兌現由 ops/BACKLOG B-003 承載）。
- **ORM 關聯與行為層紀律**（002 拍板、spec FR-022）：①關聯宣告只映真 DB FK——無 DB FK
  之邏輯關聯不建 Relation、需要即手寫 join（關聯真相單一來源＝DB FK）；
  ②`ActiveModelBehavior` 恆空實作——ORM 行為層不承載六審計欄自動化、審計欄由
  model/facade 顯式成對寫（憲法 §I.6 成對條款）；守門＝`server/tests/entity_behavior_lint.rs`。

### API 慣例

- **部分更新三態**（ADR 0023；射程＝部分更新請求 body 之每一可選欄）：欄位缺席＝不動、
  JSON null＝顯式清空（NOT NULL 欄拒收 2222）、有值＝設值；解析層以 `Option<Option<T>>`
  三態型別區分「未出現」與「null」，★並以自訂 `deserialize_with` 承載——單靠型別，serde
  的預設 Deserialize 會把 JSON null 也落外層 `None`、與缺席不可辨（三態塌兩態；L-009）。

### 授權慣例

- **判定單點與 DB-fresh**：授權判定收斂於單一純函式進入點（server/src/auth/enforce.rs）；
  角色每請求現查 DB、不快取亦不採信 token 附帶——角色一撤、下一請求即生效。
- **拒絕語意**（ADR 0022）：無權＝5003＋HTTP 403、msg＝純 i18n key、不揭露政策明細與
  持有角色；授權面內部故障＝5000、不偽裝成 403。
- **no-escalation seam**（ADR 0022 定形）：空掛點 `no_escalation_check` 單一呼叫點、
  簽章預留 async＋db；現況恆放行、deny 與政策拒絕走同一出口。

## §9 架構決策

決策全文住 docs/arc42/decisions/（一決策一檔）；索引住 docs/generated/DECISIONS-INDEX.md。
本節不承載內容。

## §10 品質要求

（本節尚無內容；fail-open／closed 語意總表隨行為刀填入。）

## §11 風險與技術債

待辦與候選 ☞ ops/BACKLOG；坑與防法 ☞ ops/LESSONS。本節不承載內容。

## §12 名詞表

- **刀**：一個 feature 的完整交付單位（brainstorm→SDD→TDD→收刀）；縱切刀＝功能縱貫、橫切刀＝慣例橫貫。
- **收刀**：feature merge 回 default branch＋簿記三步（events append＋NOTES＋generate）。
- **輕量軌**：維護項不開 SDD 的交付軌（分支＋編排單元＋merge＋misc 事件收單）；判準與程序見 CLAUDE.md §2。
- **島**：具狀態機性質的行為子系統（如 token rotation）；其不變式經 amendment 入 constitution §I.7。
- **軌道**：constitution §III 授權的 base-web 改動邊界類別。
- **短名／長名**：目錄與口語用短名（base-web／rust-api）；git 分支用長名（rev5-admin-*）。
- **pin**：外層 repo 記錄的 submodule commit SHA；單元邊界即時 bump。
- **活書**：本檔——現在式 as-built 敘事，人寫、lint 守約。
- **事件源**：docs/ops/events.jsonl——收刀／review／里程碑的 append 型單一事實源。
- **傘狀 repo**：本 repo；只記文件、spec、gitlink pin，不含子體實碼。
