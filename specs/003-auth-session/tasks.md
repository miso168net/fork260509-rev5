---

description: "Task list for 003-auth-session"
---

# Tasks: 003 auth 域整批——真登入、會話生命週期、節流＋驗證碼、dynamic 選單

**Input**: Design documents from `/specs/003-auth-session/`

**Prerequisites**: [plan.md](./plan.md)（必要）、[spec.md](./spec.md)（US 與優先序）、
[research.md](./research.md)（R1~R9；★動工前逐檔先讀 R2 對應碼、R3 十六筆防回歸）、
[data-model.md](./data-model.md)、contracts 三檔（[wire-auth](./contracts/wire-auth.md)／
[wire-route](./contracts/wire-route.md)／[msg-keys](./contracts/msg-keys.md)）、
[quickstart.md](./quickstart.md)

**Tests**: 含測試任務——CLAUDE.md §2 規定 TDD 實作（紅→綠），且 spec §7 已定驗收面。
測試層對照：*contract case*＝`rust-api/server/tests/contract.rs` 的 registry 條目（wire 形制與
碼表）；*integration*＝各 handler 模組內 `#[cfg(test)]` 之真 DB／真 redis 測；*unit*＝純函式
（TTL 公式、映射、值域）。base-web 側**零測試框架** ⇒ 該側任務的把關＝`pnpm typecheck`＋
`fork-delta-lint`＋人工走查（★前端執行單元的 TDD 迴圈退化成純 review 迴圈、收斂判定失去客觀
依據，編排時須知情）。

**Organization**: 依 user story 分 phase，使每個 story 可獨立實作與驗收。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：檔域不相交、可分派給不同執行單元。★僅指「可分派」——**cargo 執行一律序列**
  （容器內 `--test-threads=1`）。
- **[Story]**：US1~US5（Setup／Foundational／Polish 不掛）。

## 全程紀律（每 task 隱含、不逐條重複）

- ★**實作前先讀** research R2 對應之 rev4 碼：後端
  `git -C rust-api show origin/rev4-admin-rust-api:<path>`／前端
  `git -C base-web show origin/rev4-admin-base-web:<path>`（皆唯讀、絕不 checkout）；高度參照、
  **重打字消化不拷貝**、註解一律 rev5 語境重寫（rev4 出處帶 `rev4:` 前綴）；**research R3 十六筆
  差異點不得帶回**（憲法 §I.5＋ADR 0019）。
- ★**Amendment 硬閘**：T002 未 accepted 前，**不得動任何 base-web fork 既有檔**（`.env*` 亦屬既有
  檔）。純新增檔（`rev5-` 前綴 wrapper／`rev5-auth.d.ts`／`zh-tw.ts`）依 ADR 0021 款 1 不受此閘。
- ★**Lint24 同步律（跨子庫；閘讀「工作樹」、不讀 git index）**：`error.rs` 新增一個 `fn key()`
  match 臂 ⇔ `base-web/src/locales/langs/zh-tw.ts` 補同名鍵，兩邊須在**同一次工作樹編輯內**齊備
  （該閘以 `_read()` 直接開檔讀工作樹，且只在**外層** repo 的 pre-commit 無條件執行；兩子庫自身的
  hook 只跑 betterleaks、**不含 Lint24**）。★孤兒鍵窗的準確界定＝**不得跨越任何一次「外層」
  commit**：兩子庫先各自 commit（次序自由），再以**一顆**外層 commit `git add rust-api base-web`
  **同時 bump 兩顆 pin**。★機器不守的危險態（必須人守）：單側子庫已 commit、另側只在工作樹改好，
  此時外層只 `git add` 一個子庫就落 commit ⇒ Lint24 讀工作樹會**綠**、Lint17 亦不告警，外層歷史
  卻留下「後端有鍵、前端沒鍵」的 pin 組合且收刀時不會補抓。★外層 commit 一律不得 `--no-verify`
  （zh-tw.ts 無 `App.I18n.Schema` 標註、typecheck 不攔鍵名，Lint24 是唯一機器守）。
- rust build／test **一律容器內、全程序列**：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api cargo test --workspace -- --test-threads=1`；
  容器內**無 rustfmt**（手動排版）。
- ★**絕不 push／merge**（本清單零 push／merge 任務；收尾整合走 finishing 階段、需 user 同意）。
- **兩段式 commit＋pin bump**：子庫內 commit → 立即回外層 `git add rust-api`（或 `base-web`）
  bump pin＋外層 commit；**在單元邊界即時做**、不延到收刀。
- 測試環境紀律：redis 測試鍵一律 uniq 前綴（時戳＋pid；dev 與測試共用 DB 0）；
  `sys_login_attempt.real_ip` 為 INET NOT NULL ⇒ 測試**顯式注入 `X-Real-IP`**；寫入
  `sys_token`／`session_event`／`sys_login_attempt` 的測試須帶 **sequence 重設守衛**
  （data-model §9）。

---

## Phase 1: Setup（★主線閘：憲法 Amendment 與依賴進場）

**Purpose**: 取得 base-web inline 的憲法授權、把六個新依賴帶進場。★本 phase 全數為主線任務
（user 拍板環節，不入 agent 執行單元）。

- [x] T001 ★主線任務（user 親決）：撰寫憲法 Amendment 的 ADR draft 於
  `docs/arc42/decisions/`——四條 ★ 軌道八個用途（`★BASE-WEB-LOGIN-CAPTCHA-WIRING`(i)／
  `★BASE-WEB-AUTH-WIRING`(a)(b)(c)／`★BASE-WEB-I18N-WIRING`(i)(ii)(iii)／
  `★BASE-WEB-LOGOUT-UX-WIRING`(i)）＋§I.7 五座行為島不變式條文＋§III.2 **機器可解表格形**
  （欄位＝`| 軌道 | 用途 | 範圍（檔案） | 紀律 |`、軌道名以 `**★NAME**` 包覆；掃描錨與名冊定義
  見 research R8）；draft 交 user 親決
- [x] T002 ★主線任務（user 親決後）：ADR 轉 accepted＋更新 `.specify/memory/constitution.md`
  （§III.2 新表格四軌道八列＋§I.7 五座島條文）＋bump 1.2.0→1.3.0＋`python3 tools/docs-sync.py
  generate`；獨立 commit `docs(constitution): amend §III.2 ★軌道首開＋§I.7 auth 行為島（ADR
  00NN、1.2.0→1.3.0）`。**DoD：lint 全綠；此 commit 落地即解除 base-web 既有檔硬閘**
- [x] T003 ★主線任務（user 親決）：立五筆連帶 ADR 於 `docs/arc42/decisions/`——①`AppState`
  兩欄→五欄翻案（`state.rs` 恰兩欄封條）②ADR 0021 §3 收窄（`app.d.ts` backend 型節本刀提前、
  LangType／locale 註冊／`zh-tw.ts` 標型重構仍延後）③B-047 的 4040 新解讀（正面回應 BACKLOG
  條目自書的語意張力）④root `Cargo.toml`「不引 argon2」翻案 ⑤已知態集（快速登入鈕暴露 dev
  seed 帳密／redis 無 AOF／alova 第二棧 release 非 dormant／`/auth/error` 失效／`.env*` 在
  fork-delta-lint 射程外）
- [x] T004 六個新依賴釘版：`rust-api/Cargo.toml` workspace.dependencies 加 argon2 0.5.3／
  captcha 1.0.0／hex 0.4.3／jsonwebtoken 10.4.0（★`default-features = false`＋`rust_crypto`
  feature——漏開＝decode 執行期 panic）／redis 1.3.0（`connection-manager`＋`tokio-comp`）／
  sha2 0.10.9；`rust-api/server/Cargo.toml` 加對應依賴並**同批改寫三處舊拍板註解**
  （root 檔頭「不引 argon2」／`server/Cargo.toml` 不進清單移出前六支後六支續留／
  `rust-api/server/src/state.rs:7-9` 恰兩欄封條，改寫時保留「`ip_rules`／`trust_model`／
  `mailer` 仍不搬」邊界說明）。**DoD：容器內 `cargo build` 綠、`Cargo.lock` 成長記入 commit
  message（估 441→約 484 名）**
- [x] T005 `rust-api/server/src/config.rs` 六個新 getter（`APP_JWT_JWT_SECRET`／
  `APP_JWT_REFRESH_TOKEN_SECRET`／`APP_JWT_ISS`／`APP_JWT_AUD`／`APP_REDIS_URL`／
  `APP_CAPTCHA_SECRET`；沿既有 `env_or_file` 四段 panic 條件）＋逐鍵測試。
  **DoD：先紅後綠；`docker compose … up -d --wait` 六業務件仍起得齊（secrets 已備）**

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: 認證基座、快取層、碼表、真驗章、測試設施。**⚠️ 本 phase 未完成前不得開任何 US。**

- [x] T006 `rust-api/server/src/state.rs` 兩欄→五欄（加 `jwt: JwtConfig`／
  `cache: Option<SessionCache>`／`captcha_secret: String`；測試 `None`、production 恆 `Some`、
  boot 建連失敗即 fail-loud panic 不靜默退 None）＋`rust-api/server/src/main.rs` boot 鏈接線。
  **DoD：先紅後綠**
- [x] T007 `rust-api/server/tests/common/mod.rs` 的 `stub_state` 同步五欄，並★**把 stub 連線由
  `DatabaseConnection::Disconnected` 換成 `ConnectOptions::connect_lazy(true)` 的假連線**
  （research R7-1 修訂版／**ADR 0034**：`Disconnected` 在 `Select::all` 呼
  `get_database_backend()` 直接 panic，而本刀 9 條 Public route 會真的進 handler；
  ★原訂之 sea-orm `mock` feature 方案經實證不可行——開 `mock` 會拔掉
  `DatabaseConnection: Clone`、而 axum `State` 要求 `AppState: Clone`）；
  ★URL 不得帶 `user:pass@`（命中 betterleaks DSN 規則）；
  `rust-api/server/src/router.rs` 內的 stub_state 亦同步。
  **DoD：既有 4 case contract 測仍全綠**
- [x] T008 [P] `rust-api/server/src/cache/mod.rs` 新建（★同批於 `rust-api/server/src/lib.rs` 加
  `pub mod cache;`，否則整模組編譯不進 crate）：`SessionCache` 型別別名＋`connect`＋
  六支 key builder（`session:denylist:{sid}`／`session:{sid}:last_activity`／
  `session:rotate-grace:{token_hash}`／`session:idle-emitted:{sid}`／
  `throttle:lock:user:{name}`／`throttle:captcha:used:{nonce}`）＋原語
  （`get_string`／`set_ex`／`set_nx_ex` 回 bool／`del`／denylist／last_activity／grace 讀寫）＋
  常數（★`GRACE_TTL_SECS = 30`＝rev5 差異點 R3-2、`REASON_KICKED`／`REASON_REVOKED`）。
  ★**nil↔Err 嚴格分流**：所有 GET 一律 `Option<T>`（nil→`Ok(None)`＝權威缺席、連線故障→`Err`＝
  caller 退權威源）。★模組名 `cache` 不用 `redis`（R3-1，註解不得帶回 rev4 的消歧理由）。
  **DoD：真 redis（uniq 前綴）＋壞 redis（指不存在位址）雙路測試先紅後綠**
- [x] T009 [P] `rust-api/server/src/auth/jwt.rs` 新建（★同批於 `rust-api/server/src/auth/mod.rs`
  加 `pub mod jwt;`）：`Claims` 八欄（`uid`／`sid`／`jti`／
  `roles` 僅 hint／`iss`／`aud`／`exp`／`iat`）＋`sign`＋`verify`／`verify_refresh`（★access 與
  refresh **各自秘鑰**）＋`verify_with`（HS256、`leeway=0`、`validate_exp`、`set_issuer`／
  `set_audience`）＋`token_hash`（SHA-256 hex 64）＋`TokenTtl`＋`access_ttl_secs`／
  `refresh_ttl_secs`（`min(300, N×60/2)`／`N×60+access`）＋`ttl_from_settings`（★三重 fail-loud：
  查詢失敗／列缺失／不可 parse 一律 `5000`、不猜值）。
  **DoD：TTL 公式邊界 unit 測（N=60→300/3900；N=5→150/450）先紅後綠**
- [x] T010 `rust-api/server/src/error.rs`：`AppError` 加三變體（`LoginFailed` 1000／
  `TokenExpired` 3333／`ModalLogout` 7777）＋`code()`／`key()`／`http()` 三 match 各補三臂
  （★`http()` 現為 `_ => StatusCode::OK` 萬用臂 ⇒ 三碼自動落 HTTP 200、零改動即符 FR-024，僅需
  補斷言）；★**六處逐字改造**（research R7-3）：①函式名 `issuable_six_and_no_variant_seven` 改
  九可發語意 ②計數斷言 6→9 ③期望陣列收成四保留碼 ④`matrix()` 補三列 ⑤`issuable_witness` 窮舉
  match 補三臂（不補＝編譯紅）⑥`witness_aligns_matrix_and_excludes_no_variant_codes` 內**第二份**
  `no_variant` 陣列同步；檔頭 doc「B12 變體集恰六」改寫。★**依全程紀律之 Lint24 同步律**
  （同一次工作樹編輯內齊備、兩子庫各自 commit 後以單顆外層 commit 同時 bump 兩 pin）補
  `base-web/src/locales/langs/zh-tw.ts` 三鍵（`auth.login.failed`／`auth.token.expired`／
  `auth.session.kicked`，譯文見 `contracts/msg-keys.md`）。
  **DoD：先紅後綠；13 碼矩陣測試不動仍綠；`docs-sync lint` 綠**
- [x] T011 [P] `rust-api/server/src/model/facade/sys_token.rs` 新建（先落 `insert`／
  `find_by_hash_for_update`／`has_active_in_chain`；`rotate`／`revoke_family`／
  `revoke_others_of_user` 留 US2／US3）＋`rust-api/server/src/model/facade/mod.rs` 註冊。
  **DoD：真 DB 測（含 sequence 重設守衛）先紅後綠**
- [x] T012 `rust-api/server/src/auth/enforce.rs` 換真驗章：驗 access → denylist 查 → 放行後推進
  `last_activity`；★降級鏈＝redis `Err` 退 PG `has_active_in_chain`（無 active→`8888`
  fail-closed）／**PG 亦故障→視為無 active、絕不盲放**／denylist nil→放行（權威「未撤」）；
  三分碼落地（缺席・非 Bearer・簽章不符・已撤銷→`8888`；exp 過期→`3333`；被踢→`7777`）＝
  R3-10 差異點（rev4 把缺席也判 3333、不得帶回）。`rust-api/server/src/obs.rs` 同批
  pre-register `denylist_hit_total{source=redis|pg}`。
  **DoD：四級降級各一測（真 redis／壞 redis 退 PG／PG 亦壞／nil 放行）先紅後綠**
- [x] T013 汰換 dev-only 驗證器：刪 `rust-api/server/src/auth/dev_identity.rs` 整檔＋
  `rust-api/server/src/auth/mod.rs` 移除 `pub mod dev_identity;`＋★**同批把
  `rust-api/server/tests/authz_entrypoint_lint.rs` 與
  `rust-api/server/tests/entity_access_lint.rs` 兩份 `scan_is_non_empty` must-list 中的
  `auth/dev_identity.rs` 換成本刀新檔**（如 `auth/jwt.rs`／`handler/auth/login.rs`；★維持逐檔
  指名的守門強度、**不是直接刪列**）＋把 002 既有測試由 `Bearer dev-super` 遷到測試 helper 簽
  真 token＋更新 `docs/arc42/ARCHITECTURE.md` 對應節。
  **DoD：兩支 lint 綠、`cargo build --release` 首次可跑（debug／release 行為一致）**
- [x] T014 `rust-api/server/src/router.rs` 掛 **`method_not_allowed_fallback`**（B-047）：
  ★組裝次序寫死為 route 註冊 → 各子 router `enforce_mw` layer → merge → `.fallback()` →
  `.method_not_allowed_fallback()` → 最外側 metric layer（research R1 實證）；把
  `routes_table_matches_data_model_four_rows` 的硬編 4 改為與 `ROUTES` 並置的具名常數
  （各 phase 加 route 時同 commit bump）；★碼註同時釘在
  `rust-api/server/tests/contract.rs` 與 `router.rs`：**動詞探測閘永遠裸掛 router**（改走
  `build()` 共用即恆綠、L-010 形）。
  **DoD：四行為＋兩次序反例測試先紅後綠——Public 動詞不符→4040＋404／Authed 未認證動詞不符
  →4040（不洩存在性）／Authed 已認證動詞不符→4040／未註冊路徑→既有 path fallback；反例①mnaf
  後才 merge 進來的 route 回框架 405 ②mnaf 排在 layer 前則未認證動詞不符變 8888**
- [x] T015 [P] 測試設施：在 `rust-api/server/src/model/mod.rs` 新開
  `#[cfg(test)] pub(crate) mod test_db`（★**不可**放 `rust-api/server/tests/common/mod.rs`——該檔
  自述「crate 內側**拿不到** integration test 的 `tests/common`（取用方向相反）、屬結構性隔離」，
  且其比對面自述「tests/ 各 case 全不觸 DB」；而本刀真 DB／真 redis 測全在 src 側 `#[cfg(test)]`）
  加 ①redis 鍵 uniq 前綴 helper（時戳＋pid）②**三表 sequence 重設守衛**（`sys_token`／
  `session_event`／`sys_login_attempt` 之 `setval(seq, 1, false)`；★刪列救不回 setval——
  schema-gate gate2 原位比對，本刀是 rev5 首撞、002 的還原守衛只 `UPDATE system_settings` 故無
  此面）③`X-Real-IP` 注入 helper。實作範式沿 002 既有三件（`run_restore_stmt`／`SeedRestoreGuard`／
  `RowFixupGuard`＝獨立 OS thread＋一次性 current-thread runtime＋全新連線＋`thread::panicking()`
  二分支，Drop 內不可 await）。★守衛用 raw SQL `Statement`（`setval` 非 entity 存取）故不觸
  `entity_access_lint`。
  **DoD：守衛 Drop 後 `python3 tools/schema-gate.py check` gate2 綠**
- [x] T016 [P] `rust-api/server/src/request_context.rs` 加 `real_ip`／`x_forwarded_for`／
  `ip_confidence` 三個**原樣轉錄**欄（★零信任判定；handler 一律經此型取請求事實、絕不自讀轉發
  標頭——B-019 接手只換 `real_ip` 推導、欄與寫入點不動）；`x_forwarded_for` 入庫前**截斷 1024＋
  剝 CR/LF**、`ip_confidence` 恆 `nginx_peer`（R3-11）。
  **DoD：截斷與剝控制字元 unit 測先紅後綠**
- [x] T017 [P] `rust-api/server/src/model/password.rs` 新建：`verify`／`dummy_verify`
  （時序等化）＋argon2 參數（對齊 seed PHC `m=19456,t=2,p=1`）。
  **DoD：以 seed hash 驗 `123456` 成功／錯誤密碼失敗／`dummy_verify` 耗時同量級，先紅後綠**

**Checkpoint**: 基座就緒——真驗章上線、release 可跑、碼表九可發、測試設施齊備；可開 US。

---

## Phase 3: User Story 1 — 真帳密登入取得會話、側邊欄由後端生成（P1）🎯 MVP

**Goal**: 瀏覽器以三個 seed 帳號登入，側邊欄呈現後端 Casbin 過濾後的角色化選單。

**Independent Test**: quickstart §1——三帳號登入看側邊欄差異；`getUserInfo` 四欄型別對齊
typings；`getConstantRoutes` 未認證可取且前端合併不清空 builtin 五條常量路由。

### Tests for User Story 1 ⚠️（先寫、先確認紅）

- [x] T018 [P] [US1] contract case ×5 加入 `rust-api/server/tests/contract.rs` registry：
  `/auth/login`／`/auth/getUserInfo`／`/route/getUserRoutes`／`/route/getConstantRoutes`／
  `/route/isRouteExist`（案 key 與 wire 形制依 `contracts/wire-auth.md`／`wire-route.md`；
  ★每 case 的 verify 須能在配到別條 path 時紅＝逐 case 錯配自證）
- [x] T019 [P] [US1] integration 測骨架：三帳號登入→取 token→`getUserInfo` 四欄斷言
  （`userId` 為**字串**、`userName`＝nick_name〔User→`User01`〕、`roles` DB-fresh、`buttons`
  非空）＋`getUserRoutes` 樹依角色差異＋`home` 為可導航葉頁，置
  `rust-api/server/src/handler/auth/user_info.rs` 與 `handler/route.rs` 之 `#[cfg(test)]`。
  ★同批補**四條失敗路徑**（否則 FR-004 的 ③⑤ 兩分支零測試）：①帳號不存在 ②密碼錯——兩者零
  fixture 即可驗同碼同 msg（`1000`＋`auth.login.failed`）③已停用（fixture＝`UPDATE sys_user
  SET status=2 WHERE id=3`）④鎖內重驗失敗（fixture＝植**第三個 status 值** `0` ⇒ ③過、⑤擋）。
  ★fixture 一律用 **UPDATE 而非 INSERT**（`sys_user` 有 sequence、INSERT 會不可逆推進），並以
  RAII 守衛還原且**顯式把 `updated_at`／`updated_by` 歸 `NULL`**（否則 gate2 seed 逐列紅）。
  ★③與⑤的判別器＝`sys_login_attempt` 恰一列且 `created_by`：③ uid 可為 `None`、⑤ uid 必有值
  （測試綠不代表⑤被走到，須併驗此欄）

### Implementation for User Story 1

- [x] T020 [P] [US1] `rust-api/server/src/model/facade/sys_user.rs` 新建：
  `find_by_user_name`／`find_by_id`／`write_session_id`
- [x] T021 [P] [US1] `rust-api/server/src/model/facade/sys_role.rs` 新建：`home_of_roles`
  （★收斂律＝啟用角色 `status=1` 依 role id 升冪取首個**非空** `role_home`、全空→`home`；
  ★三 seed 角色同值故機器測不出分歧 ⇒ 碼註釘住規則＋一支**合成多角色**測試守）
- [x] T022 [P] [US1] `rust-api/server/src/model/facade/sys_menu.rs` 新建：`list_active`／
  `visible_menu_routes`（Casbin `menu` 維度 `get_filtered_policy`）／`to_menu_route`
  （★欄位映射逐欄依 data-model §5：`id`→字串、`meta.title` 恆存、`icon_type` 拆
  `icon`／`localIcon` 且本身不外洩、`meta.roles` 類欄**不下發**）
- [x] T023 [P] [US1] `rust-api/server/src/model/facade/sys_login_attempt.rs` 新建（本 phase 只落
  `insert`；滑動窗 `count_recent_failures` 留 US4）
- [x] T024 [US1] `rust-api/server/src/handler/auth/login.rs` 新建（★同批**新建**
  `rust-api/server/src/handler/auth/mod.rs`＝五個子模組的 `pub mod` 宣告，並於
  `rust-api/server/src/handler/mod.rs` 加 `pub mod auth;`；漏建即整個 handler/auth 目錄
  編譯不進 crate）——十一步之
  ③`authenticate`（帳號不存在／密碼錯／已停用**三態 collapse 同一 `1000`**、不洩存在性）
  ④txn＋`pg_advisory_xact_lock(uid)` ⑤**鎖內重驗**（status／deleted_at／password 字面比對、
  ★不重跑 argon2）⑥讀 `session_idle_timeout` 套 TTL（缺失→`5000`）⑦生新 sid＋簽對
  ⑧`sys_token::insert` ⑩稽核成功列同 txn ⑪commit 後 best-effort 進 denylist＋`last_activity`
  起點。★**失敗列寫入點恰三處**（research R7-7）：Denied（外層 conn）／鎖內重驗失敗
  （先 `txn.rollback()` 再落列於**外層 conn**）／成功（落 txn 內）。步驟①②留 T054、⑨留 T041
- [x] T025 [P] [US1] `rust-api/server/src/handler/auth/user_info.rs` 新建：四欄回包；
  `buttons` 走 Casbin `button` 維度 `get_filtered_policy` 枚舉（★非 `enforce*` ⇒ 不觸單一判定
  進入點守恆）；`userId` 用既有 `serialize_i64_as_string`
- [x] T026 [P] [US1] `rust-api/server/src/handler/route.rs` 新建：`get_user_routes`
  （DB-fresh roles→過濾→祖先包含→同層 `order`→`id` 升冪；`home` 經 `resolve_home` 兜底＝驗屬
  可見樹可導航葉、不屬→先序第一可導航頁）／`get_constant_routes`（★過濾謂詞必寫
  `constant = TRUE`、**勿寫 `IS NOT FALSE`**——NULL 佔 64 列；現回 `[]`）／`is_route_exist`
- [x] T027 [US1] `rust-api/server/src/router.rs` 加 5 條 ROUTES（`/auth/login` POST/Public／
  `/auth/getUserInfo` GET/Authed／`/route/getConstantRoutes` GET/**Public**／
  `/route/getUserRoutes` GET/Authed／`/route/isRouteExist` GET/Authed）＋bump 條數常數。
  ★每欄一行的窄形制（`parse_router_routes` 要求；rustfmt 不得折行、**不得出現鏈式多動詞
  handler**——會靜默 fullmatch 通過）
- [x] T028 [US1] base-web `.env` 兩行 ADAPT 改動＋標記：`VITE_AUTH_ROUTE_MODE=static`→
  `dynamic`（兌現憲法 §II #2；不翻則三個 `/route/*` 端點前端永不呼叫）／`VITE_HTTP_PROXY=Y`→`N`；
  標記形＝`# [rev5-inline BASE-WEB-ADAPT] 原行: <現值>`（★軌道名**全稱不縮寫**）
- [x] T029 [P] [US1] base-web `.env.test` 與 `.env.prod` 各一行 ADAPT：
  `VITE_SERVICE_BASE_URL` 由 apifox mock→`/api`（★dev 實載 `.env.test`；`.env.prod` 同步拆
  mock＝dev/prod 同形，不同步則留一個指向 apifox 的死設定）＋同形標記
- [x] T030 [US1] base-web `src/store/modules/route/index.ts` 的 `★BASE-WEB-AUTH-WIRING(a)`：
  `initConstantRoute` 之 else 分支一行改為
  `addConstantRoutes([...staticRoute.constantRoutes, ...data])`（★**合併**而非取代——seed
  `constant=TRUE` 為 0 列，取代會清空 403／404／500／iframe-page／login 五條 builtin 常量路由）；
  修改型 inline 須帶 `原行:` 註解。**DoD：`pnpm typecheck` 綠＋瀏覽器登入頁仍可達**
- [x] T031 [US1] 走查 quickstart §1（三帳號登入＋側邊欄差異＋`getConstantRoutes` 未認證可取），
  並在 `rust-api` worktree commit＋外層 bump pin

**Checkpoint**: US1 完成——**MVP 達成**：rev5 第一次端到端可見（瀏覽器真登入→角色化側邊欄）。

---

## Phase 4: User Story 2 — access 過期無感續期（token rotation）（P2）

**Goal**: access 過期時以 refresh token 自動換發，並發換發不誤判盜用。

**Independent Test**: quickstart §2——同票二度換發於 30 秒 grace 窗內回**同一對**；同票兩並發
一 rotate 一走 grace；驗章失敗一律 8888。

### Tests for User Story 2 ⚠️

- [x] T032 [P] [US2] contract case ×1（`/auth/refreshToken` POST/**Public**）加入
  `rust-api/server/tests/contract.rs`
- [x] T033 [P] [US2] integration 測：①`active`→rotate 回新對 ②同票二度→grace 命中冪等回同一對
  ③grace 窗外同票→reuse＋撤家族＋落 `session_event(reuse)`＋8888 ④驗章失敗／查無列→8888
  ⑤**同票兩並發**→一 rotate 一走 grace、不觸 reuse（★partial UNIQUE 衝突 DbErr 須辨識並轉
  grace 冪等分支、**不得籠統 5000**），置 `handler/auth/refresh.rs` 之 `#[cfg(test)]`

### Implementation for User Story 2

- [x] T034 [P] [US2] `rust-api/server/src/model/facade/sys_token.rs` 補 `rotate`（★舊列→
  `rotated`＋`used_at`、插新 `active` 同鏈；**次序不可反**、partial UNIQUE 為護欄）與
  `revoke_family`
- [x] T035 [P] [US2] `rust-api/server/src/model/facade/session_event.rs` 新建：`insert`
  （append-only 八欄；★`source_ip` 為 `varchar(45)` 非 INET ⇒ 與 `sys_login_attempt.real_ip`
  寫入**不共 helper**）
- [x] T036 [US2] `rust-api/server/src/handler/auth/refresh.rs` 新建：驗章失敗**一律 8888**
  （★絕不 3333——jwt 層恆吐 3333、漏 `map_err` 即前端死迴圈）；`FOR UPDATE` 鎖列後分流——
  `active`→rotate→**寫 grace（TTL 30 秒、★commit 前仍持鎖時）**／`rotated`＋grace 命中→冪等回
  既發後繼／`rotated`＋grace miss→**reuse 偵測（唯一觸發形，R3-7）**→`revoke_family`＋
  `session_event(reuse)`＋denylist(revoked、★TTL＝refresh 全壽命 R3-8)→8888／查無列→8888。
  `revoked` 三分支留 T042
- [x] T037 [US2] `rust-api/server/src/router.rs` 加 `/auth/refreshToken`（POST/**Public**——設
  Authed 則過期 token 永遠換不了）＋bump 條數常數
- [x] T038 [US2] 走查 quickstart §2＋worktree commit＋外層 bump pin

**Checkpoint**: US1＋US2 皆獨立可用——會話可續期。

---

## Phase 5: User Story 3 — 會話撤銷與單一會話治理（logout／被踢／閒置）（P2）

**Goal**: 登出即撤、他處登入即踢（modal）、閒置逾時失效。

**Independent Test**: quickstart §3——logout 後舊 access 得 8888、垃圾票 logout 仍 0000；
single-session 前置翻 on 後同帳號二次登入使前一條得 7777；idle 直接寫舊 `last_activity` 值觸發。

### Tests for User Story 3 ⚠️

- [x] T039 [P] [US3] contract case ×1（`/auth/logout` POST/**Public**）加入
  `rust-api/server/tests/contract.rs`
- [x] T040 [P] [US3] integration 測：①logout 後舊 access→8888 ②logout 對垃圾／已撤票→**0000
  冪等 no-op、不落事件**（回異碼＝token 有效性 oracle）③single-session 二次登入→前一條 7777＋
  落 `session_event(kicked, reason=single_session)` ④idle 逾時→8888＋**僅首次**落
  `session_event(idle)`（SET NX 冪等守門）⑤★被踢者於 `(access, refresh)` 窗內換發**仍得 7777**
  （denylist TTL＝refresh 全壽命）⑥★`revoked` 列缺 denylist→**靜默 8888、不落假 reuse**（R3-7）

### Implementation for User Story 3

- [x] T041 [US3] `rust-api/server/src/handler/auth/login.rs` 補步驟⑨：**兩層政策解析**
  （`effective_single = session_policy=='single' || (session_policy=='inherit' &&
  single_session_default=='on')`；`session_policy` 值域 `single|multi|inherit` 碼層收斂＋值域
  測試守〔★不加 CHECK、保零 migration〕；`single_session_default` 讀不到→**off 語意**，與第⑥步
  fail-loud 方向相反、刻意）＋`sys_token::revoke_others_of_user`＋逐 sid
  `session_event(kicked)`＋denylist(kicked、TTL＝refresh 全壽命)＋寫 `sys_user.session_id`
- [x] T042 [US3] `rust-api/server/src/handler/auth/refresh.rs` 補 `revoked` 三分支與 idle：
  reason==`kicked`→**7777**／reason==`revoked` **或鍵缺席**→★靜默 8888、不落事件、不重複撤
  （status 即權威、denylist 純加速層）；idle 門檻＝`refresh_secs − access_secs`（＝N×60）、僅
  `last_activity` 可讀時判（不可讀＝**fail-open** 不 idle-reject）、命中→SET NX
  `idle-emitted:{sid}` 守門→僅首次落 `session_event(idle)`→8888，★**idle 不寫 denylist**
  （不變式 `access_TTL ≤ N×30 < N×60`）
- [x] T043 [P] [US3] `rust-api/server/src/handler/auth/logout.rs` 新建：驗章成功→該列→`revoked`＋
  denylist(revoked、★TTL＝refresh 全壽命 R3-8)＋落 `session_event(logout, created_by=本人)`→0000；
  驗章失敗→**0000 冪等 no-op、不落事件**
- [x] T044 [US3] `rust-api/server/src/router.rs` 加 `/auth/logout`（POST/**Public**——設 Authed
  則 token 一壞就再也撤不掉那條 session）＋bump 條數常數
- [x] T045 [P] [US3] base-web `src/service/api/rev5-auth.ts` 新建（★`rev5-` 前綴＝§III.1
  WRAPPER 軌道、免 ★ 軌道）：`fetchLogout(refreshToken)` wrapper
- [x] T046 [US3] base-web `src/layouts/modules/global-header/components/user-avatar.vue` 的
  `★BASE-WEB-LOGOUT-UX-WIRING(i)`：`onPositiveClick` 改 async、登出前 best-effort
  `await fetchLogout(...)`（失敗不阻斷）後才 `resetStore()`；三行修改型 inline 帶 `原行:` 註解。
  ★(ii) reLogin toast **不開**（R3-13 不得帶回）。**DoD：`pnpm typecheck` 綠＋UI 登出可走通**
- [x] T047 [US3] 走查 quickstart §3＋worktree commit＋外層 bump pin

**Checkpoint**: US1~US3 皆獨立可用——會話全生命週期到位。

---

## Phase 6: User Story 4 — 登入失敗節流三區＋圖形驗證碼（P3）

**Goal**: 同帳號連續失敗施以三區節流（自由／需驗證碼／鎖定），答對但登入失敗自動換題。

**Independent Test**: quickstart §4——失敗 <2 回 1000；2–4 回 `2222 biz.auth.captchaRequired`；
≥5 回 `2222 biz.auth.locked`；任意 userName（含不存在）皆發題。

### Tests for User Story 4 ⚠️

- [x] T048 [P] [US4] contract case ×1（`/auth/loginCaptcha` GET/Public）加入
  `rust-api/server/tests/contract.rs`（★含缺 `userName` query 的 rejection 亦須成三欄信封）
- [x] T049 [P] [US4] integration 測：①三區轉換 ②★軟區與鎖定皆 argon2 **之前**擋下、
  **零稽核列零計數桶**（以「拒絕後成功登入仍可」證明不消耗桶）③滑動窗 reset-on-success
  ④captcha nonce 重放第二次拒 ⑤答錯不推進鎖定但該題已耗 ⑥**兩層降級**：redis 整體不可用→軟區
  要求**整層停用**且密碼錯仍計數／單次 SET NX 瞬斷→**拒但零計數不罰** ⑦L2 DbErr→`count:=0`
  fail-open ＋ `captcha_forced = !redis_down` 補償 ⑧設定鍵讀不到→退常數＋**每次載入至多一筆**告警

### Implementation for User Story 4

- [x] T050 [P] [US4] `rust-api/server/src/model/facade/sys_login_attempt.rs` 補
  `count_recent_failures`：★raw SQL 之 `GREATEST` **三源下界**（窗起點／窗內最近成功的
  `MAX(created_at)`／`unlock_marker`）逐字帶入**不得簡化**；★子查詢必帶窗下界（防全歷史回掃）；
  ★`unlock_marker` 本刀**無寫入者**（後續刀補）——無 marker 綁 SQL NULL、`GREATEST` 非 strict
  自然退化為兩源，保留參數位、**不得用 sentinel 值**；碼註記「該源恆 NULL＝已知態、不得宣稱
  三源皆已驗」
- [x] T051 [P] [US4] `rust-api/server/src/throttle/mod.rs` 新建（★同批於
  `rust-api/server/src/lib.rs` 加 `pub mod throttle;`）：常數組（`THROTTLE_LOCK_TTL_SECS`
  900／`CAPTCHA_TTL_SECS` 300／`CAPTCHA_ANSWER_LEN` 4／`CAPTCHA_CHARSET` 34 字／三個 DEFAULT／
  `LOGIN_USER_NAME_MAX`／`LOGIN_PASSWORD_MAX_BYTES`）＋`ThrottleSettings`＋`load_settings`＋
  `lock_ttl_secs`＋`precheck` 四步（①L1 GET lock key〔★命中**不續期**〕②unlock marker＋
  `load_settings`＋新鮮 L2 讀 ③`count ≥ max_fails`→SET L1〔★user 維 lock key 的**唯一寫入點**、
  恆衍生自同一次新鮮 L2 讀〕→2222 locked ④captcha gate）＋`captcha_gate`＋`warn_degraded`
  （結構化 `target: "security.throttle"`＋`degraded` 欄＋counter）。★msg key 用 rev5 新名
  `biz.auth.locked`／`biz.auth.captchaRequired`（R3-4）；★**拔** IP 維全組與
  `suppressed_breadcrumb`／HLL，`precheck` 簽名不留 real_ip／ip_allow 參數位（R3-3）
- [x] T052 [P] [US4] `rust-api/server/src/captcha/mod.rs` 新建（★同批於
  `rust-api/server/src/lib.rs` 加 `pub mod captcha;`）：`CaptchaClaims` **四欄**
  （`nonce`／`user_name`／`exp`／`ans_mac`；★不設 rev4 的 `ctx` 欄＝R3-5）＋`sign`／
  `verify_challenge`＋`answer_mac`＝`hex(SHA256(secret ‖ nonce ‖ lower(answer)))`（★秘鑰參與
  雜湊⇒答案不可離線還原）＋產圖（`captcha 1.0.0`）＋★字元集 34 字（小寫 a-z 去 `o`＋數字去 `0`）
  ＋**字型涵蓋測試**（★字集含 `0`/`o` 會因內嵌字型無 glyph 靜默跳過、產約 20% 廢題）。
  ★★**撞名消歧規則（下筆前必讀）**：本模組名 `captcha` 與**外部 crate** `captcha 1.0.0` 同名、
  共用第一路徑段，寫錯會拿到「另一個 captcha」或撞 E0659：①本檔內取外部 crate 一律**前導 `::`**
  （`use ::captcha::{Captcha, Difficulty};`），不得寫裸 `use captcha::…` ②他處取本模組一律
  `crate::captcha::` ③`lib.rs` 內**絕不**寫裸 `captcha::` 路徑（crate 根同時存在同名模組與 extern
  crate，是唯一必然 ambiguous 之處）④檔頭加碼註釘住此規則：「裸 `captcha::` 在兩處指向相反」
- [x] T053 [P] [US4] `rust-api/server/src/handler/captcha.rs` 新建（★同批於
  `rust-api/server/src/handler/mod.rs` 加 `pub mod captcha;`）：`/auth/loginCaptcha`——
  ★本檔取產圖／簽題模組一律 `crate::captcha::`（裸 `captcha::` 會解析到外部 crate——見 T052 之
  撞名消歧規則）。★必帶 `?userName=`；對**任意** userName 一律發題（含不存在帳號＝零洩漏）；
  userName 超限走與登入端點**同形**的 `1000` 閘（零新碼零新 key）；產圖／簽章內部失敗→`5000`
- [x] T054 [US4] `rust-api/server/src/handler/auth/login.rs` 補步驟①②：①輸入形制閘
  （超限→`1000`、★零稽核列零 argon2 不消耗計數桶）②`throttle::precheck`（★以 `?` 早退＝構造上
  零 `record_attempt`）；★**依 Lint24 同步律**（見全程紀律）補
  `base-web/src/locales/langs/zh-tw.ts` 兩鍵（`biz.auth.captchaRequired`／`biz.auth.locked`）
- [x] T055 [US4] `rust-api/server/src/obs.rs` pre-register 兩序列：`throttle_degraded_total`
  （label `source`＝**research R5 表列之六源逐字**：`settings_default`／`redis_lock`／
  `redis_lock_set`／`redis_captcha`／`db_count`／`db_write`；★rev4 user 維為七源，rev5 少
  `redis_unlock_marker`——本刀不讀 unlock marker，見 R3-17。★label 值集以 R5 表為單一權威、
  本處為引用，勿各自維護）＋`throttle_soft_zone_total`（無 label；★`captcha_forced` 屬 DB 降級
  旗標、**不入**軟區計數）。**DoD：boot 後首次 scrape 即含全部 label 組合顯式 0（render 文本
  比對測），先紅後綠**
- [x] T056 [US4] `rust-api/server/src/router.rs` 加 `/auth/loginCaptcha`（GET/Public）＋bump
  條數常數
- [x] T057 [US4] base-web 前端 captcha 軟區接線（`★BASE-WEB-LOGIN-CAPTCHA-WIRING(i)`）：
  `src/typings/api/rev5-auth.d.ts` 新建（captcha 形、ADAPT 軌道）＋`src/service/api/rev5-auth.ts`
  補 `fetchLoginCaptcha`（★直接路徑 import、避 barrel stale-export）＋
  `src/store/modules/auth/index.ts` login 簽名加 captcha 參與失敗 msg 回傳鏈（locked／
  captchaRequired 兩態同碼 2222、僅 msg 相異）＋`src/views/_builtin/login/modules/pwd-login.vue`
  軟區條件渲染（220×120 圖＋輸入欄）＋`refreshCaptcha`＋watch userName **debounce 300ms**。
  ★**(ii) `formRules` 放寬不做**（R3-12 不得帶回、延改密端點刀）。
  **DoD：`pnpm typecheck` 綠＋瀏覽器軟區出圖、答對密碼錯自動換題**
- [x] T058 [US4] 走查 quickstart §4＋worktree commit＋外層 bump pin

**Checkpoint**: US1~US4 皆獨立可用——暴力破解阻力到位。

---

## Phase 7: User Story 5 — 替代登入誠實 stub ＋ 錯誤訊息顯人話（P3）

**Goal**: 未開放流程回明確提示（非假成功）；所有後端 msg 經 `$t` 轉譯為使用者語言。

**Independent Test**: quickstart §5——四支 stub 皆 `2222 biz.auth.notSupported`；切換語系
（zh-CN／en-US）同一後端 key 顯示對應語言譯文；7777 modal 顯人話非裸鍵。

### Tests for User Story 5 ⚠️

- [x] T059 [P] [US5] contract case ×4（`/auth/sendCaptcha`／`codeLogin`／`register`／`resetPwd`）
  加入 `rust-api/server/tests/contract.rs`。★四支同形恆 2222 ⇒ 逐 case 錯配自證會退化，
  **須指定區別手法**（各自斷言 path 專屬的 case_key 對映，而非只比信封）
- [x] T060 [P] [US5] i18n 機器面測：`python3 tools/docs-sync.py generate` 後
  `docs/generated/reference/backend-msg-dict.md` 恰 **22 列**；兩語鍵集相等；
  `DAY1_EXEMPTIONS` 拔項後 `docs-sync check` 綠（空表安全）

### Implementation for User Story 5

- [x] T061 [P] [US5] `rust-api/server/src/handler/auth/alt_stub.rs` 新建：一支
  `not_supported_stub()` 四端點共用、恆 `2222 biz.auth.notSupported`、`data: null`、零副作用
  （不落任何表、不查 DB）；★**依 Lint24 同步律**（見全程紀律）補
  `base-web/src/locales/langs/zh-tw.ts` 之 `biz.auth.notSupported`
- [x] T062 [US5] `rust-api/server/src/router.rs` 加四條（`/auth/{sendCaptcha,codeLogin,register,
  resetPwd}` POST/Public）＋bump 條數常數至 **16**
- [x] T063 [P] [US5] base-web 三張表單 stub 化（`★BASE-WEB-AUTH-WIRING(b)`、各 2 行）：
  `src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue`——import stub wrapper＋
  **消滅假成功 toast**；修改型 inline 帶 `原行:` 註解。
  ★**前置（原稿缺）**：所 import 的 stub wrapper 在 rev5 不存在——rev4 藍本為獨立檔
  `rev4-auth-stub.ts`，rev5 歸宿＝`src/service/api/rev5-auth.ts`（§III.1 WRAPPER 軌道、
  `rev5-` 前綴自有檔、免 ★ 軌道授權）。四支 stub fetch（`sendCaptcha`／`codeLogin`／
  `register`／`resetPwd`）於該檔補齊後 T063／T064 才有合規 import 對象；憲法 §III.2 (b)
  收窄字面為「僅改 import 指向 stub wrapper」，表單直呼 `request` 即違收窄
- [x] T064 [P] [US5] base-web `src/hooks/business/captcha.ts` 的 `★BASE-WEB-AUTH-WIRING(c)`
  （4 行）：`getCaptcha` 改打 `/auth/sendCaptcha` stub、移除 500ms 假延遲與假成功 toast。
  ★影響 code-login 與 register 兩表單；reset-pwd 的 code 欄無送碼入口＝已知 UX 態（ADR 記）
- [x] T065 [US5] base-web `src/typings/app.d.ts` 的 `★BASE-WEB-I18N-WIRING(iii)`：`App.I18n.Schema`
  補 `backend` **必填**型節（逐鍵鏡像 locale 結構）。★LangType／locale 註冊／`zh-tw.ts` 標型
  重構**不做**（R3-15、仍延前端 UI 刀）。**DoD：`pnpm typecheck` 紅→補完 en-us／zh-cn 後綠**
- [x] T066 [US5] base-web locale 三語 22 鍵（`★BASE-WEB-I18N-WIRING(ii)`）：
  `src/locales/langs/en-us.ts` 與 `zh-cn.ts` 插 backend 樹（★插入行必須是**獨佔一行**的
  `  backend: {`——`_locales_have_backend_tree` 為整行 fullmatch；譯文見 `contracts/msg-keys.md`、
  簡中照 rev4 鏡像重打字消化）＋`zh-tw.ts` 補齊至 22 鍵；★**同一次工作樹編輯內**（跨子庫，比照
  Lint24 同步律）拔 `tools/docs-sync.py` 的 `DAY1_EXEMPTIONS["gen.msg_dict"]`（到期即紅）＋跑
  `generate` 讓 `backend-msg-dict.md` 與 Grafana panel 首次生成——★三者（base-web locale／外層
  工具／外層生成物）須在**同一顆外層 commit** 落地，否則謂詞成立而豁免仍在＝到期即紅當場擋
- [x] T067 [US5] base-web `src/service/request/index.ts` 的 `★BASE-WEB-I18N-WIRING(i)`（2 處）：
  新增 `translateBackendMsg`／`translateDetailValue`（``$t(`backend.${msg}`, msg)`` 原文
  fallback）＋modal `content` 與 `showErrorMsg` 鏈改走轉譯；修改型 inline 帶 `原行:` 註解。
  ★**`★BASE-WEB-LOGOUT-UX-WIRING(ii)`**（reLogin toast）**不做**——注意此 (ii) 屬 LOGOUT-UX 軌道，
  與 T066 正在做的 `★BASE-WEB-I18N-WIRING(ii)` 是**不同軌道的同字母用途**，勿混。
  **DoD：`pnpm typecheck` 綠＋瀏覽器錯誤提示顯人話**
- [x] T068 [US5] 走查 quickstart §5＋worktree commit＋外層 bump pin

**Checkpoint**: 全部 US 獨立可用——本刀功能面完成。

---

## Phase 8: Polish & Cross-Cutting Concerns（DoD 收攏）

- [x] T069 [P] `tools/fork-delta-lint.py` 加「軌道名 ∈ 授權名冊」斷言（FR-030／031）五子步：
  ①名冊載入器（讀 `.specify/memory/constitution.md`、掃 §III.2 表格列 `^\|` 起、跳標題／分隔列、
  剝 `**` 與 `★`；名冊＝§III.2 ★軌道 ∪ §III.1 三軌道；★檔缺席／掃空＝**die**）②新增軌道名抽取
  正則（現行 `MARKER` 只捕 `原行:` 之後、捕不到軌道名）③判定接進 `find_missing`／`scan()` 第三類
  錯誤，並**同時**強制「修改型同行必含 `[rev5-inline` token」（現行漏洞：任何含 `原行:` 的行都
  算已記錄）④改造既有 self-test 四條樣本（B／I／L／R——皆修改型且軌道名不在名冊）＋補成對樣本
  （名冊內過／名冊外攔）⑤★**兩條**非空斷言（名冊整體非空 ＋ §III.2 ★段貢獻列數 ≥ 4）＋
  「承襲指針散文中**本刀不開的兩名**（`MODAL-WIRING`／`BASE-WEB-DEVPROXY-WIRING`）不在名冊」反例
  （★不可寫「六名」——Amendment 後六名中四名正式在冊、該斷言必然不成立）＋「真 repo 至少一個
  修改型對象被檢查」結構性自證。
  **DoD：self-test 全綠＋抽掉任一合法軌道名即紅指名**
- [x] T070 [P] ROUTES 終態機器核對：`python3 tools/docs-sync.py generate` 後
  `docs/generated/reference/routes.md` 恰 **16 列**（表頭外）；★確認 16 條皆為「每欄一行」形制、
  **零鏈式多動詞 handler**（`parse_router_routes` 對鏈式會靜默 fullmatch 通過＝漏報地雷）
- [x] T071 [P] B-050／B-051 順手收：`test_kit`（capture＋FailingConn）由
  `rust-api/server/src/model/facade/system_settings.rs` 遷至
  `rust-api/server/src/model/facade/mod.rs`（★門檻「第三個消費者」須**真消費**才成立——至少一支
  本刀**六支**新 facade 之一的測試實際使用 `test_kit::FailingConn` 驗 DbErr 落地；★T015 的
  `test_db` 是**另一支**、本刀專用、不與 `test_kit` 合併，故 B-051 的門檻語意不被稀釋成無門檻
  重構）＋為
  `sys_user_role::roles_of_user` 次段查詢的 DbErr 落地補獨立機器守
- [x] T072 非 vacuous 自證收攏（ADR 0024）逐項確認在案：軌道名名冊（三重）／captcha 字型涵蓋
  ＋產圖失敗 5000 出口／msg-dict 兩語鍵集（含 Biz 三新鍵走 contract case 逐鍵斷言）／
  denylist fail-closed／★denylist TTL 兩 reason 皆 `refresh_secs`／reuse 僅 `rotated`＋grace
  miss 觸發（`revoked` 缺 denylist **不**觸發）／節流三區／★3333 與 7777 → HTTP 200／
  ★refresh 驗章失敗→8888
- [x] T073 全量閘綠：容器內 `cargo test --workspace -- --test-threads=1`＋
  `cargo build --release`＋`pnpm typecheck`＋`python3 tools/fork-delta-lint.py`＋
  `python3 tools/docs-sync.py generate && … check`。★`schema-gate.py check`（三閘）**不在本任務**
  ——它須排在 T074 的 §7 收尾**之後**（runtime 寫入已推進三支 sequence，未收尾前 gate2 必紅）
- [x] T074 走查 quickstart 全場景（§0~§7）＋★**執行 §7 收尾**（一次 psql 批次：
  `single_session_default` 還原 `off` **並把 `updated_at`／`updated_by` 歸 NULL**〔★不可走
  updateSystemSetting API——該 API 必寫這兩欄、走 API 還原值仍留痕跡使 gate2 逐列紅〕＋清三表
  runtime 列＋`setval(seq,1,false)` 重設三支 sequence＋`sys_user.session_id` 歸 NULL；另清 §4
  造窗殘留的 L1 lock 鍵）→**收尾後才跑** `python3 tools/schema-gate.py check`。
  **DoD：gate2 seed 逐列綠（含 `system_settings` 該列審計兩欄為 NULL）**
- [x] T075 [P] 活書更新：`docs/arc42/ARCHITECTURE.md` as-built 敘事（auth 域模組拓樸、會話狀態
  機、節流三區、四條 ★ 軌道、觀測三序列）；★不回灌 ADR（拍板歸 ADR、實作結果歸收刀事件）
- [x] T076 [P] `docs/ops/BACKLOG.md` append 三筆新條目：①`fork-delta-lint` 射程擴 `.env*`＋
  `build/`（含 `#` 註解前綴支援）②快速登入鈕暴露 dev seed 帳密——轉 prod 前必須拆除（綁 prod
  硬化刀）③schema-gate gate2 對 append-only 稽核表的 seed 比對面收窄
- [x] T077 `docs/ops/LESSONS.md` append 本刀踩坑（候選：`method_not_allowed_fallback` 與 layer
  的相對次序決定 405 歸屬／contract blanket 信封斷言對 Public route 破裂免 DB 前提／gate2 seed
  對 runtime sequence 的不可逆敏感性）

---

## Dependencies & Execution Order

### Phase 依賴

- **Phase 1（Setup）**：T001→T002 為硬閘（★Amendment accepted 前不得動 base-web 既有檔）；
  T003 可與 T004／T005 平行；T004→T005。
- **Phase 2（Foundational）**：依賴 Phase 1 完成 → **阻塞全部 US**。
  `T006→T007→{T008、T009 平行}→{T011、T015、T016、T017 平行}→T010→T012→T013→T014`。
  ★該鏈與 T 號區間切出的單元邊界**不同序**（U-C＝T006~T009／U-D＝T010／U-E＝T011~T014／
  U-F＝T015~T017）：技術相依上 T010（error.rs 九可發）不需等 U-E，而 U-F 的測試設施是 T011 的
  DoD 前提。**執行單元的實際派發序＝U-C→U-F→U-D→U-E**（依相依而非依編號），單元表的字母序僅為
  命名、不代表派發序。
- **Phase 3~7（US1~US5）**：皆依賴 Phase 2；★但實作序建議照優先序 US1→US2→US3→US4→US5
  （US3 補 login 步驟⑨、US4 補步驟①②，同檔遞進；並行會撞 `login.rs`）。
- **Phase 8（Polish）**：依賴全部 US 完成；T069 另依賴 T002（名冊源＝Amendment 的 §III.2 表格）。

### User Story 依賴

- **US1（P1）**：Phase 2 後即可開，零 US 依賴 → **MVP**。
- **US2（P2）**：依賴 US1（需 login 發出的會話）；獨立驗收面＝rotation 往返。
- **US3（P2）**：依賴 US1（步驟⑨補在 `login.rs`）與 US2（`revoked` 三分支補在 `refresh.rs`）。
- **US4（P3）**：依賴 US1（步驟①②補在 `login.rs`）；throttle／captcha 模組的**檔案主體**可先行
  撰寫，★但**單元序 U-G→U-J→U-K→U-L→U-M 不可並發**（見下）。
- **US5（P3）**：依賴 Phase 2（碼表）；i18n 面依賴 T002（★I18N-WIRING 授權）；同受單元序約束。
- ★**單元序不可並發的兩個共用檔**（原稿「可平行」失真）：①`router.rs`——T027／T037／T044／T056／
  T062 五處都加 ROUTES 列並 bump **同一個遞增條數常數**，並行必衝且**不會被編譯擋**，只會由 T070
  的「恰 16 列」核對在最後才發現 ②`contract.rs`——五處都改**同一個 registry vec**。另 T041／T054
  同改 `login.rs`（步驟⑨／①②遞進）。⇒ US 的「獨立可驗收」成立於**交付面**，不成立於**單元併發面**。

### Within Each User Story

- 測試先寫、**先確認紅**（Phase 3~7 每 phase 的 Tests 段在 Implementation 段之前）。
- facade（model）→ handler（service）→ router 註冊 → 前端接線 → quickstart 走查。
- ★`router.rs` 與 `contract.rs` 於**每個 US phase 各加自己的列**（而非收斂到尾端獨佔單元）——
  這是對 research R9 單元 12 的**刻意修正**：收斂到尾端會使任何 US 在自己的 phase 內無法端到端
  驗收，違反 spec-kit 獨立可測性與 TDD 紅綠；代價是該二檔出現在五個 phase 的允許檔清單內
  （防呆⑥的「清單只縮不擴」是單元內的規則，跨單元重複出現不違反）。

### Parallel Opportunities

- Phase 2：T008／T009／T011／T015／T016／T017 六支**主體檔**不相交、可分派；★但 T008／T009 共用
  `lib.rs`／`auth/mod.rs`、T011 共用 `facade/mod.rs` 之**註冊行**——註冊行須序列化收攏於單一單元內
  （「檔域不相交」僅對主體檔成立）。
- US1：T020～T023 四支 facade **主體檔**可分派，★四支共用 `facade/mod.rs` 註冊行；T025／T026 兩
  handler 可分派，★共用 `handler/mod.rs`／`handler/auth/mod.rs` 註冊行（同上處置）。
- US4：T050／T051／T052／T053 四支可分派。
- US5：T063／T064 可分派；★T061 **不可**與 i18n 組併行（它也改 `zh-tw.ts`、與 T066 同檔）；
  i18n 三檔（T065→T066→T067）★必須序列（typecheck 相依）。
- Phase 8：T069／T070／T071／T075／T076 可分派。
- ★**cargo 執行一律序列**——[P] 僅指可分派給不同執行單元，不代表可並行跑 build／test。

---

## Parallel Example: User Story 1

```text
# facade 四支併行分派（檔域不相交）
Task: "T020 sys_user facade in rust-api/server/src/model/facade/sys_user.rs"
Task: "T021 sys_role facade（home_of_roles 收斂律）in rust-api/server/src/model/facade/sys_role.rs"
Task: "T022 sys_menu facade（to_menu_route 映射）in rust-api/server/src/model/facade/sys_menu.rs"
Task: "T023 sys_login_attempt facade（insert）in rust-api/server/src/model/facade/sys_login_attempt.rs"

# 兩 handler 併行分派（login.rs 由單一單元獨佔、不併行）
Task: "T025 user_info handler in rust-api/server/src/handler/auth/user_info.rs"
Task: "T026 route handler in rust-api/server/src/handler/route.rs"
```

---

## Implementation Strategy

### 執行單元切分（T 號區間；★編排消費面）

以 T 號區間界定單元邊界（沿 001 前例；★不用 U 編號——啟動書與 Lint25 `uround` 族禁止把 U 編號
當長壽指涉錨）。每單元一支 Workflow（內部 serial：implementer(TDD) → spec-compliance review →
fix 迴圈 → code-quality review → fix 迴圈），依 CLAUDE.md §2 防呆六件套與看門狗紀律：

| 單元 | T 區間 | 允許檔案清單（起始） |
|---|---|---|
| U-A ★主線 | T001~T003 | `docs/arc42/decisions/`、`.specify/memory/constitution.md` |
| U-B | T004~T005 | 兩份 `Cargo.toml`、`config.rs`、`state.rs`（僅註解） |
| U-C | T006~T009 | `state.rs`、`main.rs`、★`lib.rs`、★`auth/mod.rs`、`tests/common/mod.rs`、`cache/mod.rs`、`auth/jwt.rs`、★`router.rs`（僅其 `mod tests` 的第二份 stub_state）、★`handler/system_settings.rs`（僅其 `real_app()` 的第 4 個 `AppState` 建構點） |
| U-D | T010 | `error.rs`、`zh-tw.ts` |
| U-E | T011~T014 | `facade/{sys_token,mod}.rs`、`auth/{enforce,mod}.rs`、`dev_identity.rs`(刪)、兩支 lint、`router.rs`、`contract.rs`、`obs.rs`、`ARCHITECTURE.md`、★`handler/system_settings.rs`（dev-super 遷移的唯一散布點、51 處） |
| U-F | T015~T017 | `request_context.rs`、`model/{password,mod}.rs`（★`test_db` 落 `model/mod.rs`、非 `tests/common`） |
| U-G | T018~T027 | `contract.rs`、`router.rs`、`facade/{sys_user,sys_role,sys_menu,sys_login_attempt,mod}.rs`、★`handler/{mod,route}.rs`、★`handler/auth/{mod,login,user_info}.rs`（★C5：case 與其 ROUTES 列必須同單元收邊，否則 `all_registered_contract_cases_pass` 直接 panic、單元邊界無綠基線） |
| U-I | T028~T031 | `base-web/{.env,.env.test,.env.prod}`、`store/modules/route/index.ts` |
| U-J | T032~T038 | `contract.rs`、`router.rs`、`facade/{sys_token,session_event,`★`mod}.rs`、`handler/auth/refresh.rs` |
| U-K | T039~T047 | `contract.rs`、`router.rs`、`handler/auth/{login,refresh,logout,`★`mod}.rs`、`facade/sys_token.rs`、`rev5-auth.ts`、`user-avatar.vue` |
| U-L | T048~T058 | `contract.rs`、`router.rs`、★`lib.rs`、★`handler/mod.rs`、`facade/sys_login_attempt.rs`、`throttle/mod.rs`、`captcha/mod.rs`、`handler/{captcha,auth/login}.rs`、`obs.rs`、`rev5-auth.{ts,d.ts}`、`store/modules/auth/index.ts`、`pwd-login.vue`、`zh-tw.ts` |
| U-M | T059~T068 | `contract.rs`、`router.rs`、`handler/auth/{alt_stub,`★`mod}.rs`、三張表單、`captcha.ts`、`app.d.ts`、三語 locale、`docs-sync.py`、`service/request/index.ts`、★`rev5-auth.ts`（T063／T064 所 import 的 stub wrapper 落點——原稿漏列，U-M 實作期補） |
| U-N | T069~T077 | `fork-delta-lint.py`、`facade/{mod,system_settings,sys_user_role}.rs`、`ARCHITECTURE.md`、`BACKLOG.md`、`LESSONS.md` |

★清單以「★」標出的項為 analyze 補洞（模組註冊檔 `lib.rs`／`auth/mod.rs`／`handler/mod.rs`／
`handler/auth/mod.rs`、`facade/mod.rs`、dev-super 散布點）——漏列即 fix agent 撞清單外檔而 blocked
（防呆⑥「清單只縮不擴」）。單元數 14→**13**（U-G 併吞原 U-H）。

★**`facade/mod.rs` 的註冊行由六支新 facade 分批追加**（不是四支）：U-E 加 `sys_token`／U-G 加
`sys_login_attempt`、`sys_menu`、`sys_role`、`sys_user` 四行／U-J 加 `session_event`；終態八行須
**嚴格 ASCII 升冪**（★`sys_user_role` 在 `system_settings` **之前**，因 `_`(0x5f) < `t`(0x74)）。
同批改寫該檔檔頭 doc 之「本刀只開兩支」（002 開兩支＋003 補六支＝八支、一張表配一支模組不變）。

★**單元邊界 commit 恆含機器生成物**（主線動作、不入 agent 允許檔清單）：外層 pre-commit 無條件跑
`docs-sync.py check`，而 `STATE.md` 的 pins 行由**外層 index 的 submodule gitlink** 重算、
`routes.md` 由 `ROUTES` const 重算 ⇒ **每次 pin bump 都讓 STATE.md 過期、每次加 route 都讓
routes.md 過期**，漏帶即 Lint01 當場擋（實例：本刀 Batch 1 的 BACKLOG 新增即當場觸發）。故單元
邊界一律：`docs-sync.py generate` → `git add` 生成物 → 與 pin 同一顆外層 commit。對照面＝
pin bump ⇒ `docs/generated/STATE.md`；ROUTES 增列 ⇒ 併 `docs/generated/reference/routes.md`；
BACKLOG／LESSONS／ADR 增列 ⇒ 併 `STATE.md`＋`docs/generated/DECISIONS-INDEX.md`。

主線例行只在單元邊界醒：復核 → load-bearing 自驗 → generate＋git add 生成物 → bump submodule
pin → 啟下一支。

### MVP First

1. Phase 1（★Amendment 需 user 親決）→ 2. Phase 2 → 3. Phase 3（US1）→
**STOP & VALIDATE**：quickstart §1 走通＝瀏覽器真登入看見角色化側邊欄（rev5 第一次端到端可見）。

### Incremental Delivery

US1（MVP）→ US2（續期）→ US3（撤銷）→ US4（節流＋captcha）→ US5（stub＋i18n）→ Phase 8 DoD。
每個 US 完成即可獨立驗收、不破壞前面的 US。

### 收尾（★不在本清單內）

全單元完成 → final holistic review → `superpowers:finishing-a-development-branch`（★push／merge
需 user 同意）→ 收刀簿記三步（events append＋NOTES 改下一步＋`docs-sync generate`）。
★動 `docs/ops/NOTES.md` 前須先壓縮「已收官」段（現 40/40 卡 Lint07）；events `summary` ≤300 字、
細節走 `notes` 欄。

---

## Notes

- [P]＝檔域不相交可分派；★cargo 執行一律序列（容器內 `--test-threads=1`）。
- 測試先確認紅再實作；每個 task 或邏輯群組後 commit（子庫 commit → 外層 bump pin）。
- 任一 checkpoint 皆可停下獨立驗收該 US。
- 避免：跨 US 破壞獨立性、同檔並行、在 Amendment accepted 前動 base-web 既有檔。
