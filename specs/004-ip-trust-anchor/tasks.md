---

description: "Task list for 004-ip-trust-anchor"
---

# Tasks: 004 IP／信任錨——真實來源還原、存取閘、來源維節流、IP 規則管理

**Input**: Design documents from `/specs/004-ip-trust-anchor/`

**Prerequisites**: [plan.md](./plan.md)（必要）、[spec.md](./spec.md)（US 與優先序）、
[research.md](./research.md)（R1~R10；★動工前逐檔先讀 R1 對應碼、R2 十一筆防回歸、R7 dev 可達態）、
[data-model.md](./data-model.md)、contracts 四檔（[wire-ip-rule](./contracts/wire-ip-rule.md)／
[wire-throttle-unlock](./contracts/wire-throttle-unlock.md)／
[trust-model-config](./contracts/trust-model-config.md)／[msg-keys](./contracts/msg-keys.md)）、
[quickstart.md](./quickstart.md)

**Tests**: 含測試任務——CLAUDE.md §2 規定 TDD 實作（紅→綠）。測試層對照：*contract case*＝
`rust-api/server/tests/contract.rs` registry 條目；*integration*＝各模組內 `#[cfg(test)]` 之真
DB／真 redis 測；*unit*＝純函式（信任錨判定、鏈正規化、規則判定、計數桶粒度）。base-web 側
**零測試框架** ⇒ 該側把關＝`pnpm typecheck`＋`fork-delta-lint`＋兩支本刀新建機器守＋人工走查
（★前端執行單元的 TDD 迴圈退化為純 review 迴圈、收斂判定失去客觀依據，編排時須知情）。

**Organization**: 依 user story 分 phase，使每個 story 可獨立實作與驗收。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：檔域不相交、可分派給不同執行單元。★僅指「可分派」——**cargo 執行一律序列**
  （容器內 `--test-threads=1`）。
- **[Story]**：US1~US5（Setup／Foundational／Polish 不掛）。

## 全程紀律（每 task 隱含、不逐條重複）

- ★**實作前先讀** research R1 對應之 rev4 碼：`../fork260509-rev4/rust-api/…`／
  `../fork260509-rev4/base-web/…` 直讀（★**該樹絕不寫入**、亦不得 checkout；派 agent 時唯讀令
  必烤進 prompt）；高度參照、**重打字消化不拷貝**、註解一律 rev5 語境重寫（rev4 出處帶
  `rev4:` 前綴）；**research R2 十一筆差異點不得帶回**（憲法 §I.5＋ADR 0019）。
- ★**Amendment 硬閘**：T002 未 accepted 前，**不得動任何 base-web fork 既有檔**。純新增檔
  （`views/manage/ip-rule/` 三檔、`rev5-ip-rule.ts`、`rev5-ip-rule.d.ts`）依 ADR 0021 款 1
  不受此閘；★但 `zh-tw.ts` 雖屬純新增檔，其編輯受下條 Lint24 同步律約束。
- ★**Lint24 同步律（跨子庫；閘讀「工作樹」、不讀 git index）**：`error.rs`／handler 新增一個
  後端實發 msg key ⇔ 前端**四處**同時補同名鍵——①`base-web/src/locales/langs/zh-tw.ts`
  （治理錨點檔）②`en-us.ts` 之 `backend:` 樹 ③`zh-cn.ts` 之 `backend:` 樹
  ④`base-web/src/typings/app.d.ts` 之 `App.I18n.Schema.backend` 型節（FR-023／FR-036；
  `contracts/msg-keys.md`「三處鍵集」＋Schema 型節）。★**三個機器面各只守一段、缺一即紅**：
  Lint24 本身只掃 ①；② 由 `docs-sync.py generate`／`check` 的 msg-dict 生成器硬斷言
  「zh-tw 與 en-us 鍵集相等」守（單邊落鍵 ⇒ **單元邊界必跑的 generate 整支中止**）；
  ③④ 由 `pnpm typecheck` 守（兩語 runtime locale 標型 `App.I18n.Schema`）。後端側與這四處
  須在**同一次工作樹編輯內**齊備。★孤兒鍵窗**不得跨越任何一次外層 commit**：兩子庫先各自
  commit（次序自由），再以**一顆**外層 commit `git add rust-api base-web` 同時 bump 兩顆 pin。
  ★外層 commit 一律不得 `--no-verify`。
- ★**dev 走查一律帶構造轉發標頭**（quickstart 檔頭）：不帶標頭時真實來源收斂為反向代理位址、
  信心 `fallback`、全站共用單一計數桶 ⇒ 阻擋／計數隔離／防自鎖三者**打不出來**。模擬位址
  MUST 落在結構豁免六段之外（勿用 10/8、172.16/12、192.168/16、127/8）。
- rust build／test **一律容器內、全程序列**：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api cargo test --workspace -- --test-threads=1`；
  容器內**無 rustfmt**（手動排版）。
- ★**絕不 push／merge**（本清單零 push／merge 任務）。
- **兩段式 commit＋pin bump**：子庫內 commit → 立即回外層 `git add rust-api`（或 `base-web`）
  bump pin＋外層 commit；**在單元邊界即時做**。
- ★**單元邊界 commit 恆含機器生成物**：`docs-sync.py generate` → `git add docs/generated` →
  與 pin 同一顆外層 commit。對照面＝pin bump ⇒ `STATE.md`；ROUTES 增列 ⇒ 併
  `reference/routes.md`；ADR／BACKLOG／LESSONS 增列 ⇒ 併 `STATE.md`＋`DECISIONS-INDEX.md`。
- 測試環境紀律：redis 測試鍵一律 uniq 前綴（時戳＋pid）；★寫入 `sys_ip_rule`／
  `sys_operation_log` 的測試須帶 **sequence 重設守衛**（data-model §7、沿 003 之 `test_db` 三件
  範式）；`sys_login_attempt.real_ip` 為 INET NOT NULL。

---

## Phase 1: Setup（★主線閘：憲法 Amendment、依賴進場、信任模型設定）

**Purpose**: 取得 base-web inline 的憲法授權、把三個新依賴帶進場、讓信任模型在 dev 真的生效。
★T001~T003 為主線任務（user 拍板環節，不入 agent 執行單元）。

- [ ] T001 ★主線任務（user 親決）：撰寫憲法 Amendment 的 ADR draft 於
  `docs/arc42/decisions/`——①**§I.7 島 F 進場**（六條：F1 判定序與集合語意／F2 真相分層
  keep-last-good／F3 fail-open 且唯一 fail-closed＝寫端自鎖、降級必告警／F4 信任錨為唯一位址
  輸入且兩集合同源對稱／F5 顯式放行跳節流而結構豁免不跳／★**F6 本刀新增：Tier-1 錨須傳輸層
  背書**，條文與理由見 data-model §4）②**既有登入節流島補來源維釐清**（帳號維三源 vs 來源維
  恆兩源、刻意不對稱、防日後被「統一」）③**§III.2 第五條 ★ 軌道**（管理域新頁接線）——
  ★**檔級名單為硬邊界（§III.2 表外宣告 1）：下列三塊共七支檔 MUST 逐支以路徑寫進條文範圍欄，
  任一塊都不得出現無路徑的概稱**（本刀的 C1 缺陷正是「用『三檔』概稱掩蓋實際檔集」，同型錯誤
  不得在條文內復發）：〔一〕`base-web/src/locales/langs/{en-us,zh-cn}.ts` 之 `route:`／`page:`
  兩樹（各 1 塊、新增型）〔二〕`base-web/src/typings/app.d.ts` 之 `App.I18n.Schema.page` 型節
  （1 塊、新增型圈界；★**必需非「如需」**——`page:` 為顯式型樹，`page.manage.ipRule.*` 不補型
  即 typecheck 紅；既有 (iii) 只授權 `backend` 型節、涵蓋不到）〔三〕**路由外掛產物四檔**
  ＝`src/router/elegant/{imports,routes,transform}.ts`＋`src/typings/elegant-router.d.ts`；
  ★條文 MUST 明載本軌道之機器守實況（生成檔＝重算冪等檢查為唯一守／新增型兩塊＝僅「圈界標記
  須存在」，名冊斷言只掃修改型、對本軌道不適用），不以含糊措辭掩蓋覆蓋缺口；★產物檔紀律
  ＝「僅由外掛重算產出、禁止手改」＋**明文寫入「不要求逐行原文標記」及其理由**〔標記於下次
  重算即被抹除、物理上不可維持〕＋驗收採**重算冪等檢查**）④**B-071 之 §III.1 紀律欄措辭 PATCH**；
  draft 交 user 親決
- [ ] T002 ★主線任務（user 親決後）：ADR 轉 accepted＋更新 `.specify/memory/constitution.md`
  （§I.7 島 F 六條＋島 E 釐清句＋§III.2 表格加第五條軌道一列＋§III.1 紀律欄措辭）＋bump
  1.3.1→1.4.0＋`python3 tools/docs-sync.py generate`；獨立 commit
  `docs(constitution): amend §I.7 島 F＋§III.2 第五條軌道（ADR 00NN、1.3.1→1.4.0）`。
  **DoD：lint 全綠；★新軌道那一列的變異自證通過——暫把該列範圍欄任一反引號路徑改成不含 `/`
  的裸措辭（或拿掉用途識別符 `(x)`）→ `fork-delta-lint` 當場紅，驗畢還原；此證明該列真的被名冊
  載入器讀進來（SC-011）。★射程提醒：這證的是「該列被讀進來」，不是「名冊斷言會擋本軌道的越界
  改動」——本軌道三塊皆新增型或生成檔，在名冊斷言（僅掃帶 `原行:` 的修改型）射程外。此 commit
  落地即解除 base-web 既有檔硬閘**
- [ ] T003 ★主線任務（user 親決）：立連帶 ADR 於 `docs/arc42/decisions/`——①`AppState`
  五欄→七欄翻案（`state.rs` 恰五欄封條；★改寫時**保留** `mailer` 續留域外的邊界說明）
  ②本刀已知態集：**持久化設定重評結論＝維持不開**（論證＝IP 維暴險受「權威源即真相」封頂：
  判定面不依賴快取、解鎖標記遺失可再解鎖自癒；★此重評觸發器由前一刀明文掛在本條目上）／
  「解鎖端點無 UI 按鈕」／「dev 經反向代理可達二態」（research R7）／「稽核覆蓋不對稱」
  （既有設定寫端不落操作稽核列、本刀新端點落列）③**明文解除**「三個來源節流鍵零消費者」之
  既有已知態紀錄（走 `supersedes` 或於本刀已知態 ADR 內明文解除）
- [ ] T004 三個新依賴釘版（research R3 三源核對表）：`rust-api/Cargo.toml` 的
  `[workspace.dependencies]` 加 **arc-swap 1.9.2**（三源一致）／**futures-util 0.3.34**
  （★user 拍板取 latest stable；連帶把 lock 內既有的 0.3.33 推升）／**toml 1.1.4**
  （★user 拍板取 latest stable；全新 lock 條目）；`rust-api/server/Cargo.toml` 加對應三支
  （★features 沿 rev4 形：`server/Cargo.toml` 三支一律 `{ workspace = true }`、features 單一
  來源＝workspace root——`arc-swap`／`toml` 取 default、**`futures-util` 於 root 帶
  `default-features = false`**（rev4 同形；default 的 `async-await-macro` 會多拉一條
  `futures-macro` lock 條目，而本刀唯一使用點 `StreamExt::next()` 用不到它）。★`redis` 的
  pub/sub 在既有 `connection-manager`＋`tokio-comp` 下即可用＝**本刀零新 redis feature
  flag**）。**DoD：容器內 `cargo build` 綠；`Cargo.lock` 成長（★關掉 default 之下不應出現
  `futures-macro` 新條目）與 futures-util 升版逐筆記入 commit message**
- [ ] T005 `rust-api/server/src/config.rs` 加信任模型載入：`load_trust_model(path, lookup)`
  ＋`RawTrustModel`（TOML 六集合、欄名見 `contracts/trust-model-config.md`）＋
  `trust_model_path` getter；★**三層失敗語意**——缺路徑／讀檔失敗→扁平環境變數退路
  （逗號分隔 CIDR 充 `internal_default`）／TOML 整體解析失敗→**全空**（★**不**套退路：設定
  存在但壞掉不得擴大信任）／單一集合含無效 CIDR→**只清空該集合**；三者皆**永不 panic**、
  皆發結構化告警。**DoD：四類輸入（完整／部分／整體壞／單集合壞）unit 測先紅後綠**
- [ ] T006 dev 信任模型設定就位：新建 `deploy/trust-model.dev.toml`（★內容見
  `contracts/trust-model-config.md` 之 dev 交付形——**僅** `internal_default` 填容器網段、
  其餘集合刻意留空，且註解須寫明「本檔存在的理由」與「只填這一項的後果＝可達二態」）＋
  `docker-compose.dev.yml` 掛載該檔並設環境變數指向。**DoD：`docker compose … up -d --wait`
  後 `docker compose logs rust-api | grep -i trust` 見載入成功、**無**缺席／解析失敗告警**

**Checkpoint**: 憲法授權到手、依賴進場、信任模型在 dev 真的生效——可開 Foundational。

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: 信任錨純函式全形、規則判定純函式、狀態容器擴欄、測試設施。
**⚠️ 本 phase 未完成前不得開任何 US。**

- [ ] T007 [P] `rust-api/server/src/trust/mod.rs` 新建型別群（★同批於
  `rust-api/server/src/lib.rs` 加 `pub mod trust;`，否則整模組編譯不進 crate）：`TrustModel`
  六集合＋`TunnelConfig`／`CdnEntry`／`MyPublicEntry`／`Binding`＋`Confidence` **七態**與其
  `as_str`（DB／wire 小寫底線字面）＋`SoftReason` 二態＋`Evidence` 五變體；★**`is_trusted`
  單一 helper**——受信集（層①）與跳過集（層③）**由同一函式導出、內容對稱**
  （`internal_default ∪ tunnel ∪ cf_gate_egress ∪ cdn ∪ my_public ∪ Σbindings.internal`；
  ★**必含 tunnel＋cf_gate_egress**，兩集合分叉即前代缺陷復發、real_ip 塌縮為常數）。
  **DoD：七態字面 unit 測＋`is_trusted` 六集合各一命中案，先紅後綠**
- [ ] T008 [P] `rust-api/server/src/trust/mod.rs` 鏈正規化：`normalize_xff`（★**先取右端視窗**
  再逐欄解析——把解析成本上界鎖死、洪泛不放大成本；方向不可反）＋`parse_xff_token`
  （剝連接埠／剝 IPv6 區域識別／剝方括號包裹）＋常數 `MAX_XFF_TOKENS`。
  ★**不可解析者丟棄**（＝該跳不存在、鏈的相對次序不變）。
  **DoD：先紅後綠，且必含**三語意區辨性測試**——同一輸入（含垃圾欄位）在「丟棄」得 A、在
  「遇垃圾即中止整條鏈」得 B、在「保留為佔位跳」得 C，三者結論相異（spec FR-009：若三者
  結論相同則該測試無鑑別力、等於沒守）；另含右端視窗方向反例（左端洪泛不得把真實來源擠出）**
- [ ] T009 `rust-api/server/src/trust/mod.rs` 之 `resolve_client_ip` 三層＋★**F6 硬化**：
  鏈組成＝`normalize(xff) ++ [peer]`（對端接最右）；①對端閘（peer ∉ 受信集→直取 peer、
  轉發鏈整條忽略、`direct`）②Tier-1 位置錨（最右 CDN 段為錨；★**硬化：錨右鄰起直到傳輸層
  對端全屬受信基建，否則錨不成立、退層③**；受信判定 MUST 用 T007 的同一 helper、**不得**
  為硬化另立第三個集合）→取錨左鄰第一個非 CDN 為真實來源、`cdn_anchored`；錨左無非 CDN→回退
  ③Tier-2 最右非受信 walk（含 `proxy_soft` 兩觸發：`dual_role` 出口／綁定右鄰不符）
  ④回退（整鏈受信→peer、`fallback`）。
  **DoD：先紅後綠，且必含**硬化的兩個對照案**——(a) 攻擊形：鏈＝`[偽造位址, CDN 邊緣, 攻擊者,
  反向代理]` ⇒ 硬化前得 `cdn_anchored`＋**偽造位址**、硬化後**錨不成立退層③**得**攻擊者位址**
  ＋`proxy_clean`；(b) 合法形：鏈＝`[使用者, CDN 邊緣, 反向代理]` ⇒ 硬化前後**位址與信心皆
  逐位元相同**（零誤傷、SC-002 後半）**
- [ ] T010 `rust-api/server/src/trust/mod.rs` 兩覆蓋層：`apply_tunnel_fallback`（基礎＝回退
  ∧ peer ∈ 通道集 ∧ 訪客標頭有值 → 採信訪客位址、★**信心維持回退不升**）＋
  `apply_cf_overlay`（★**四前置全中**才比對：peer ∈ `cf_gate_egress` ∧ 驗證標記真 ∧ 訪客標頭
  有值 ∧ 基礎信心 ∈ **恰** {`cdn_anchored`,`proxy_clean`,`proxy_soft`}；相符→`cdn_verified`、
  不符→`cdn_mismatch`；★**只動信心、絕不動位址**）＋`to_canonical` 折疊單點。
  **DoD：先紅後綠——四前置各缺一皆透傳（含「peer 不在驗證閘出口集但自帶驗證標記」之負向案，
  即防直連形態騙升）／不可升等三態（`direct`／`fallback`／`cdn_mismatch`）無作用／
  IPv4-mapped 折疊**
- [ ] T011 [P] `rust-api/server/src/ipgate/mod.rs` 新建純函式核（★同批於 `lib.rs` 加
  `pub mod ipgate;`）：`RuleSet{allow, deny}`＋`Verdict` 三值＋`Decision{verdict, matched_cidr}`
  ＋`STRUCTURAL_EXEMPT` **六段**（`127.0.0.0/8`／`::1/128`／`10.0.0.0/8`／`172.16.0.0/12`／
  `192.168.0.0/16`／`fc00::/7`）＋`decide`（判定序＝③豁免→④allow any-match→⑤deny any-match
  →⑥預設放行；★**集合語意、無優先序欄、與載入順序無關**）＋`build_ruleset`（★未知類型列
  **skip＋告警**、不使整份載入失敗）＋`would_self_lock`（＝`decide(rs_after, ip).verdict ==
  Deny`；★**消費同一個 `decide`**、零內聯重複）。
  **DoD：先紅後綠——白＞黑（同網段兩類並存）／豁免段建 deny 仍放行／兩袋皆空→放行／
  未知類型 skip 而其餘規則照常／`would_self_lock` 對 allow 規則恆 false**
- [ ] T012 [P] `rust-api/server/src/model/facade/sys_ip_rule.rs` 新建**讀端**
  （`load_active` 回 `Vec<(IpNetwork, String)>`；寫端留 US3）＋`facade/mod.rs` 註冊
  （★終態十行須**嚴格 ASCII 升冪**：`sys_ip_rule` 在 `sys_login_attempt` **之前**〔`i` < `l`〕、
  `sys_operation_log` 在 `sys_menu` **之後** `sys_role` **之前**）。
  **DoD：真 DB 測（含 sequence 重設守衛）先紅後綠**
- [ ] T013 `rust-api/server/src/state.rs` 五欄→七欄（加 `trust_model: Arc<TrustModel>`＋
  `ip_rules: Arc<ArcSwap<RuleSet>>`）＋★**檔頭封條註解改寫**（「恰五欄」→「恰七欄」，
  **保留** `mailer` 續留域外之邊界說明、不得整段刪除）＋`rust-api/server/src/main.rs` boot
  接線（載信任模型；★**規則集初載與 watcher 起動留 US2**、本 task 先以空規則集建欄）。
  **DoD：先紅後綠；`cargo build --release` 仍可跑**
- [ ] T014 `AppState` **窮舉式 struct literal 五處**同步七欄（★清單來源＝
  `grep -rn "AppState {" rust-api/server/` 的實測結果，排除 `state.rs` 的 struct 定義本體與三處
  `-> AppState {` 函式簽名；六處 literal 中 `main.rs` 的 boot 建構已由 T013 涵蓋、其餘五處在此）：
  ①`rust-api/server/tests/common/mod.rs` 之 `stub_state`
  ②`rust-api/server/src/router.rs` 之 `mod tests::stub_state`
  ③`rust-api/server/src/auth/enforce.rs` 之 `mod tests::state_with`
  ④`rust-api/server/src/model/mod.rs` 之 `test_db::real_app_with`
  ⑤`rust-api/server/src/throttle/mod.rs` 之 `mod tests::throttle_app`。
  ★五處皆**無 `..Default`**、加欄即編譯不過，漏一處＝implementer 一開工就撞編譯錯。
  ★`rust-api/server/src/handler/system_settings.rs` 之 `real_app()` **不在此列**——B-054 收攏後
  已是零建構薄轉呼（其本體＝`crate::model::test_db::real_app_with(None).await`），改它是空操作。
  **DoD：既有 16 case contract 測與既有 321 支測試仍全綠**
- [ ] T015 [P] ★**research R8 未定項實測**：在容器內跑
  `rust-api/server/tests/authz_entrypoint_lint.rs` 與 `entity_access_lint.rs`，確認
  `ipgate::decide` 與 `would_self_lock`（＝**IP 閘判定**，非 casbin 授權判定）是否被
  `ALLOWED_DECISION_FILES` 的偵測面誤攔。**若誤攔**→擴 must-list 並在該 lint 內以註解記明
  「casbin 授權判定 vs IP 閘判定」的語意分工（★不得直接放寬偵測樣式而使守門失效）；
  **若未誤攔**→在本 task 的 report 中明載「實測未觸發、零改動」作為後續 review 的擋箭牌。
  **DoD：兩支 lint 綠，且結論（改動或零改動）有明文記錄**

**Checkpoint**: 信任錨與規則判定兩組純函式就緒、狀態容器七欄、測試設施齊備；可開 US。

---

## Phase 3: User Story 1 — 稽核紀錄記下真實來源與其可信度（P1）🎯 MVP

**Goal**: 稽核列記下的是**真實使用者位址**與其**可信度**，而非最近一跳代理的位址；
攻擊者偽造轉發標頭無法讓系統記錯來源。

**Independent Test**: 直打後端注入各種「對端×轉發鏈×信任設定」組合，斷言還原結果逐案正確；
並實際登入後查稽核列的鑑識三欄（對端位址／真實位址／信心）如實落庫。

### Tests for User Story 1 ⚠️

- [ ] T016 [P] [US1] `rust-api/server/src/middleware/mod.rs` 之 `#[cfg(test)]`：
  **七態逐態**整合測（直餵 `TrustModel`＋任意對端與標頭；★對照 research R7——七態全數在此層
  覆蓋，**不得**寫成需經反向代理的形）＋上下文缺席 fail-open 案。**先確認紅**
- [ ] T017 [P] [US1] `rust-api/server/src/request_context.rs` 之 `#[cfg(test)]`：seam 換血後
  的既有不變式仍成立（轉發鏈欄仍原樣淨化、欄位私有之編譯期守門仍在）＋★**邊界案反轉**測
  （「來源位址缺席→空字串→由資料庫擋下」路徑**消失**，對端恆有值）。**先確認紅**

### Implementation for User Story 1

- [ ] T018 [US1] `rust-api/server/src/middleware/mod.rs` 新建（★同批於 `lib.rs` 加
  `pub mod middleware;`）：`request_context_mw`——自 `ConnectInfo` 取傳輸層對端、抽取轉發鏈與
  兩個邊緣標頭（★`CF_VERIFIED_HEADER` 常數落此檔）→呼叫 `trust` 純函式三層＋兩覆蓋→組
  `RequestContext` 注入 request extensions（**每請求恰一次**）；★**本層零政策邏輯**
  （判定全在 `trust` 純函式、middleware 純消費，違反即 F4 破功）。
  **DoD：T016 由紅轉綠**
- [ ] T019 [US1] `rust-api/server/src/request_context.rs` **seam 換血**：三欄與取值器**簽名
  一律不動**——`real_ip` 內容改為信任錨結果之正規化字串、`ip_confidence` 由單一字面改為七態、
  轉發鏈欄原樣淨化轉錄不變；★`IP_CONFIDENCE_NGINX_PEER` 常數**退役**（由 `Confidence::as_str`
  取代）；`from_headers` 退為**測試建構途徑**、請求路徑改由 extensions 取；★欄位私有與
  `compile_fail` doctest **續存不得刪**。
  **DoD：T017 由紅轉綠；★既有 login 三處落列點零改動仍編譯通過（seam 承諾的驗證點）**
- [ ] T020 [P] [US1] `rust-api/server/src/model/facade/sys_login_attempt.rs`：insert 擴充
  **`peer_ip` 落欄**（此前恆 NULL）——鑑識三欄（對端／真實／信心）自此齊活。
  **DoD：真 DB 測斷言三欄皆有值、且信心為七態之一，先紅後綠**
- [ ] T021 [US1] `rust-api/server/src/router.rs` 掛 `request_context_mw` layer（★層序：
  須在 `enforce_mw` 與所有 handler **之前**——否則下游取不到上下文；與既有動詞探測 fallback
  的組裝次序不得互換）。**DoD：既有 16 case 全綠；新增一支層序反例測（mw 掛在 handler 之後
  則上下文缺席、下游走 fail-open）先紅後綠**
- [ ] T022 [US1] 走查 quickstart §1：帶／不帶構造轉發標頭各發一次失敗登入，查
  `sys_login_attempt` 尾二列。**DoD：帶標頭那筆＝`proxy_clean`＋模擬公網位址；不帶那筆＝
  `fallback`；★兩列 `peer_ip` 皆有值**

**Checkpoint**: 稽核來源三欄如實——US1 可獨立驗收（rev5 第一次「稽核紀錄可當證據」）。

---

## Phase 4: User Story 2 — 超管以 IP 規則阻擋或放行特定來源（P2）

**Goal**: 規則一存檔即生效（免重啟）；白優先於黑；基礎設施網段永不被鎖在門外；
規則來源暫時讀不到時沿用上一份已知良好規則。

**Independent Test**: 以 facade 直接寫入規則列後以該來源請求斷言被拒／放行；對本機位址建
阻擋規則斷言仍放行；令規則來源不可讀斷言沿用前一份。★本 phase 的「超管操作即生效」以
**呼叫重載機制**驗證；經端點的完整鏈路於 US3 之 **T043** 再驗（quickstart §2）。

### Tests for User Story 2 ⚠️

- [ ] T023 [P] [US2] `rust-api/server/src/ipgate/mod.rs` 之 `#[cfg(test)]`：`reload_and_publish`
  三分支（重載成功→換版＋發門鈴／★重載失敗→**keep-last-good 不清空**＋回錯／通知層缺席或
  發送失敗→告警但回成功）＋`load_ruleset` 啟動初載失敗→空集放行。**先確認紅**
- [ ] T024 [P] [US2] `rust-api/server/src/middleware/mod.rs` 之 `#[cfg(test)]`：`ip_gate_mw`
  **六步判定序**逐步各一案（①健康／觀測放行 ②上下文缺席放行 ③豁免段放行 ④allow 放行
  ⑤deny 拒絕 ⑥預設放行）。**先確認紅**

### Implementation for User Story 2

- [ ] T025 [US2] `rust-api/server/src/ipgate/mod.rs` 補動態面：`try_load_ruleset`／
  `load_ruleset`（啟動初載失敗→空集 fail-open）＋`IPGATE_INVALIDATE_CHANNEL` 常數＋
  `reload_and_publish`（★re-read **成功才** store＋發門鈴；失敗→keep-last-good＋回錯由呼叫端
  退避；發送失敗／通知層缺席→告警但回成功，本機已生效）。**DoD：T023 由紅轉綠**
- [ ] T026 [US2] `rust-api/server/src/cache/mod.rs` 加 `publish` 原語（沿既有 nil↔Err 分流
  慣例）。**DoD：真 redis 測先紅後綠**
- [ ] T027 [US2] `rust-api/server/src/ipgate/mod.rs` 之 watcher：`spawn_ipgate_watcher`＋
  `subscribe_ipgate`＋`reread_keeping_last_good`。★三個易漏點必須全中——(a) **專用 pub/sub
  連線**：既有多工連線句柄**不可**用於訂閱，須由 `config::redis_url()` 另開 client
  (b) 訂閱建連帶 **5 秒 timeout**：無 timeout 時對端黑洞會使 watcher 永久 hang 而**不 backoff**
  (c) **重連（含首次訂閱成功）後補一次重讀**：否則 backoff 窗內錯過的門鈴永不收斂。
  斷線 backoff 1s 指數上限 30s、訂閱成功重置。
  **DoD：先紅後綠——訂閱失敗→backoff 不脫鉤／重連後補讀生效／重讀失敗→keep-last-good**
- [ ] T028 [US2] `rust-api/server/src/middleware/mod.rs` 加 `ip_gate_mw`：六步判定序＋
  阻擋回應（★復用既有 `PermissionDenied`／`5003`／HTTP 403、**零新錯誤變體**）＋阻擋時發
  帶結構化欄位的告警（含命中網段）。**DoD：T024 由紅轉綠**
- [ ] T029 [US2] `rust-api/server/src/main.rs` boot 補規則集初載＋起 watcher；
  `rust-api/server/src/router.rs` 掛 `ip_gate_mw` layer（★層序：在 `request_context_mw`
  **之後**〔需上下文〕、在 `enforce_mw` **之前**〔IP 閘先於身分驗證〕）。
  **DoD：既有測試全綠；新增層序反例測先紅後綠**
- [ ] T030 [US2] `rust-api/server/src/obs.rs`（★U-G 以外的單元動不到此檔 ⇒ 本 task 是本刀
  obs.rs 的**唯一**落點）：①**降級五類**各 pre-register 一支計數器，類別集合逐字取自
  **data-model §5 降級矩陣**（信任模型載入失敗〔涵蓋設定檔缺席／整體損壞／單一集合無效三列〕
  ／規則集載入失敗〔初載＋執行中重載〕／門鈴與 watcher 故障〔PUBLISH 失敗、通知層缺席、
  訂閱斷線〕／**請求上下文缺席**〔發射點＝T028 之 `ip_gate_mw` 判定序②〕／**解鎖標記讀取
  故障**〔發射點在 T047／T053、屬他單元；★序列先於發射點註冊正是 pre-register 本義〕）
  ②**IP 閘阻擋計數**（★**不屬降級類**——歸 FR-018 之可觀測紀錄，結構化欄位由 T028 發射）。
  ★**啟動即註冊 0**（不因「事件尚未發生」而整條訊號缺席）。★data-model §5 之「快取整體
  不可用」**不新增序列**——沿用既有帳號維訊號（`throttle_degraded_total` 之 `redis_lock`／
  `redis_lock_set`／`redis_captcha` 三源已在）。
  ★**同批重推 `throttle_degraded_total` 的 source 值集與其兩道上界守**：obs.rs 現有
  `!text.contains("redis_unlock_marker")` 與「樣本行**恰六**」兩句斷言，其理據（R3-17「rev5
  不讀 unlock marker」、R3-3「IP 維全組不得回歸」）**已被本刀整條推翻**——本刀真的讀解鎖
  標記（T047／T053）且真的有來源維節流。值集 MUST 重推為「本刀實際發射點逐字」並同步改寫
  該註解與失敗訊息；IP 維發射點沿 rev4 先例採**獨立 label**（與帳號維同名字面分開、免觀測
  混流；例：`settings_default_ip`〔T047 三鍵讀取端〕／`redis_unlock_marker`）。
  ★**上界守形式不得拆除**（只改期望值集，不得改成「至少 N 源」）；★該守門**不會**因他單元
  新增發射點而自動轉紅（其測試用 local recorder、只跑 `pre_register_metrics`）⇒ 值集漂移
  無機器可察，本 task 是唯一防線。
  **DoD：計數器 render 文本比對測先紅後綠；★降級五類逐類斷言顯式 0；★上界守仍為等值斷言
  ——植入一個多餘 label 即紅**

**Checkpoint**: IP 閘生效且熱重載成立——US2 可獨立驗收。

---

## Phase 5: User Story 3 — 超管在管理頁維護 IP 規則（P2）

**Goal**: 超管從側邊欄進「IP 規則管理」完成列表／搜尋／新增／編輯／軟刪／回收桶復原；
會把自己鎖在門外的規則**當場拒絕**。

**Independent Test**: 瀏覽器完成六步全程並與前代同頁對照；另以「建立涵蓋自身來源的阻擋規則」
驗證當場被拒且零寫入。

### Tests for User Story 3 ⚠️

- [ ] T031 [P] [US3] `rust-api/server/tests/contract.rs` 加**五個 case**
  （`get-ip-rule-list`／`add-ip-rule`／`update-ip-rule`／`delete-ip-rule`／`restore-ip-rule`；
  斷言重點見 `contracts/wire-ip-rule.md` 末表）。**先確認紅**
- [ ] T032 [P] [US3] `rust-api/server/src/handler/ip_rule.rs` 之 `#[cfg(test)]`：守門與防自鎖
  ——類型非二值／網段不可解析**皆寫前拒零寫入**、唯一性衝突映**業務碼非伺服器錯誤**、
  ★**防自鎖四寫端各一案**（含「刪 allow 規則亦須過自鎖」與「復原後與現有列衝突」）。
  **先確認紅**

### Implementation for User Story 3

- [ ] T033 [P] [US3] `rust-api/server/src/model/audit.rs` 新建（`AuditEvent`／`AuditOperation`／
  `AuditOperator`；★同批於 `model/mod.rs` 加 `pub mod audit;`）＋
  `rust-api/server/src/model/facade/sys_operation_log.rs` 新建（★**rev5 首個寫入者**）
  ＋`facade/mod.rs` 註冊（ASCII 升冪位置見 T012）。
  **DoD：真 DB 測（含 sequence 重設守衛）先紅後綠**
- [ ] T034 [US3] `rust-api/server/src/model/facade/sys_ip_rule.rs` 補**寫端**：
  `list`（分頁＋三 filter：網段模糊／類型等值／刪除狀態三態）＋四寫端（新增／更新／軟刪
  〔`deleted_at`＋`deleted_by` **成對**寫〕／復原〔成對清空〕）＋`IpRuleMutateError`
  （唯一性衝突獨立變體，供 handler 映業務碼）；★寫端與操作稽核列**同一交易**。
  **DoD：真 DB 測先紅後綠——軟刪後同組合可重建、唯一性只約束有效列**
- [ ] T035 [US3] `rust-api/server/src/handler/ip_rule.rs` 新建（★同批於 `handler/mod.rs` 加
  `pub mod ip_rule;`）：五支 handler＋DTO（camelCase，見 `contracts/wire-ip-rule.md`；★識別碼
  上 wire 為 number＋2^53 守衛、`deleted` 由 `deleted_at.is_some()` 導出、
  **刪除時間與刪除者不上 wire**）＋`validate_wbip_type`（二值封閉）＋`normalize_cidr`
  （★**主機位元 mask**——防同網段不同寫法繞過唯一性）＋`map_mutate_err`＋`guard_self_lock`
  （★組「變更後規則集」交 `ipgate::would_self_lock`，**與請求判定同源**；四寫端各自的
  「變更後集合」語意見 `contracts/wire-ip-rule.md`）；寫成功後呼 `reload_and_publish`。
  ★handler **零 path-root `entity::`**（資料存取全走 facade）。
  **DoD：T032 由紅轉綠**
- [ ] T036 [US3] `rust-api/server/src/router.rs` 加**五條 ROUTES**（路徑與動詞逐字對齊 001
  凍結 seed 之政策列：`getIpRuleList` GET／`addIpRule` POST／`updateIpRule` POST／
  `deleteIpRule` **DELETE**／`restoreIpRule` POST；★五條皆 `Protection::Policy`）＋bump 條數
  常數。★**零新 casbin 政策列**（seed 143–147 已在）。**DoD：T031 由紅轉綠；契約覆蓋閘無缺
  case 無殭屍 case**
- [ ] T037 [US3] `tools/schema-gate.py`：runtime-append 收窄集**常數加一行**納入
  `sys_operation_log`（★這是 spec FR-042 明列的**排程工作項、不得當 bug 追**）；
  ★`sys_ip_rule` **MUST NOT** 納入（變體 A 業務表、列內容即真 seed 面）。
  **DoD：該工具自測擴充後全綠；★變異測試——把 `sys_ip_rule` 誤加進收窄集時自測必紅；
  ★端到端證據（SC-011 指名）——往 `sys_ip_rule` 塞一列後 `schema-gate check` 轉紅、清列後
  轉綠，證明該表未被順手收窄**
- [ ] T038 [US3] 後端 msg key 五鍵落地（`biz.ipRule.{invalidRuleType,invalidCidr,conflict,
  notFound,selfLock}`）＋★**依 Lint24 同步律**在**同一次工作樹編輯內**把五鍵補進**四處**
  （譯文語意見 `contracts/msg-keys.md`；FR-023／FR-036）：①`base-web/src/locales/langs/zh-tw.ts`
  ②`base-web/src/locales/langs/en-us.ts` 之 `backend:` 樹 ③`base-web/src/locales/langs/zh-cn.ts`
  之 `backend:` 樹 ④`base-web/src/typings/app.d.ts` 之 `App.I18n.Schema.backend.biz` 加
  `ipRule` 型節（五鍵皆 `string`）。★②③④ 為 base-web **既有檔**，三處皆補在既有
  `[rev5-inline BASE-WEB-I18N-WIRING(ii)/(iii)+ …]` 圈界塊**內部**（憲法 §III.2 (ii)(iii) 授權
  射程內、不需新 Amendment，亦**不新開**圈界標記）。★失敗形：漏 ② ⇒ 單元邊界必跑的
  `docs-sync.py generate` 在 msg-dict 生成器「兩語 backend 鍵集不相等」處整支中止；漏 ③④ ⇒
  `pnpm typecheck` 紅。
  **DoD：`python3 tools/docs-sync.py lint` 綠；`python3 tools/docs-sync.py generate` 跑得完
  （不拋 `BackendDictError`）；`pnpm typecheck` 綠；`fork-delta-lint` 綠**
- [ ] T039 [P] [US3] `base-web/src/typings/api/rev5-ip-rule.d.ts` 新建（`Api.IpRule` 節；
  ADAPT 軌、新檔）＋`base-web/src/service/api/rev5-ip-rule.ts` 新建（五支 wrapper；WRAPPER 軌、
  新檔）。**DoD：`pnpm typecheck` 綠；wire-schema 快照納入該新檔**
- [ ] T040 [US3] `base-web/src/views/manage/ip-rule/` 三檔新建（`index.vue`＋
  `modules/ip-rule-operate-drawer.vue`＋`modules/ip-rule-search.vue`；新增型、檔頭一行標記
  圈界）：列表（含備註欄）＋搜尋＋新增／編輯抽屜＋回收桶復原＋四顆按鈕接既有權限碼機制。
  ★**自由文字欄一律純文字插值**、禁 `v-html`／`innerHTML`。
  **DoD：`pnpm typecheck` 綠**
- [ ] T041 [US3] ★**新軌道射程內的既有檔改動**（★T002 未 accepted 前不得動）：
  `base-web/src/locales/langs/{en-us,zh-cn}.ts` 之 `route:` 樹加 `manage_ip-rule`、`page:` 樹加
  `manage.ipRule.*`（★兩語鍵集 MUST 相等）＋`base-web/src/typings/app.d.ts` 型節（★**必需**
  ——`page:` 為顯式型樹，`page.manage.ipRule.*` 不補型則 typecheck 紅；`route:` 才是自動導出）
  ＋`base-web/src/router/elegant/{imports,routes,transform}.ts` 與
  `base-web/src/typings/elegant-router.d.ts`（★路由外掛產物**四檔**）**由外掛重算產出**
  （★**禁手改**；★該 `.d.ts` 是 `RouteKey`／`RouteMap` 的產出處——locale `route:` 樹型為
  `Record<I18nRouteKey, string>`，它未重算出 `manage_ip-rule` 鍵則 typecheck 必紅）。
  每處依 fork-delta 紀律標記（★產物四檔**除外**——依 T002 條文不要求逐行標記）。
  **DoD：`pnpm typecheck` 綠；`fork-delta-lint` 綠——★此處驗的是新增型「圈界標記須存在」，
  不是名冊斷言：本軌道三塊皆新增型或生成檔，在名冊斷言（僅掃帶 `原行:` 的修改型）射程外
  〔憲法 §III.2 表外宣告 3〕；四支生成檔由 T042② 的冪等檢查守**
- [ ] T042 [US3] 本刀兩支新機器守（★各附 self-test、植入反例必紅——ADR 0024 非 vacuous）：
  ①`views/manage/**` 零 `v-html`／`innerHTML` 斷言（掛 pre-commit）②路由產物**四檔**
  （`src/router/elegant/{imports,routes,transform}.ts`＋`src/typings/elegant-router.d.ts`）之
  **重算冪等檢查**（重跑外掛後與版控內容零差異）。★②並 MUST 併斷言「§III.2 第五條軌道該列
  所列生成檔集＝外掛實際產出檔集（檔頭帶 `Generated by elegant-router` 者）」——生成檔受
  fork-delta 檢查全域豁免，冪等檢查是它們唯一的機器守，憲法清單漏列一支即該支完全無守。
  落點沿既有 lint 家族。
  **DoD：兩支綠；★兩支的 self-test 各自證明「拿掉守門即紅」；★②另證兩道變異——「把憲法該列
  的生成檔集少列一支→檢查轉紅」與「手改任一支生成檔的一行→檢查轉紅」**
- [ ] T043 [US3] 走查 quickstart §2＋§3＋§6（★依 quickstart 原序跑；§2 用的 `addIpRule`
  端點本 phase 才存在 ⇒ US2「Independent Test」明文遞延的「經端點的完整鏈路」由本 task 承接）：
  ①**§2 IP 存取閘端到端**——對 SIM_B 建阻擋規則→該來源得 **403**／信封碼 `5003`、SIM_A
  同時仍得 200（SC-013 ②）；★**全程未重啟服務**（＝SC-004「寫入後未重啟即生效」的端到端
  半邊）；白＞黑（同位址再加 allow→改得 200）；結構豁免段建 deny 後其位址仍得 200
  ②**§3 防自鎖**——拒寫且**零寫入**
  ③**§6 管理頁**——CDP 三方對照（22080 vs 42080），六步全程＋主機位元正規化＋衝突提示＋
  備註欄標記字元顯示為字面。
  **DoD：①四項狀態碼逐項符（403／200／200／200）且期間零服務重啟；②`SELECT count(*)` 證明
  自鎖案零寫入；③六步全通**

**Checkpoint**: 規則管理前後端閉環、防自鎖成立——US3 可獨立驗收。

---

## Phase 6: User Story 4 — 來源維登入節流真正生效（P3）

**Goal**: 同一來源輪換帳號名的暴力嘗試會被擋；三個來源節流設定鍵自此**真的改變行為**。

**Independent Test**: 同一來源輪換帳號名連續失敗，斷言軟門檻要求驗證碼、硬門檻鎖定；
並斷言穿插一次成功登入**不重置**來源計數。

### Tests for User Story 4 ⚠️

- [ ] T044 [P] [US4] `rust-api/server/src/model/facade/sys_login_attempt.rs` 之 `#[cfg(test)]`：
  ★**GREATEST 兩源負向自證**——「穿插成功登入不重置來源計數」（★若誤加第三源「窗內最近成功
  登入」，本測必紅；該形是可繞過整套來源維防護的破口）＋`/64` 聚合＋解鎖標記進下界。
  **先確認紅**
- [ ] T045 [P] [US4] `rust-api/server/src/throttle/mod.rs` 之 `#[cfg(test)]`：計數桶粒度
  （v4 `/32`／v6 `/64`／IPv4-mapped 折疊／`unspecified`→無桶）＋雙維合成四組合＋
  ★L0 短路兩案（顯式 allow 規則→跳節流；**結構豁免段→不跳**）＋★**三鍵真消費自證**——把
  `ip_captcha_after`／`ip_max_fails`／`ip_window_minutes` 改成與 seed 不同的值，斷言來源維
  軟／硬門檻**隨之改變**（★這是 FR-024「三鍵具備執行面消費者」的唯一機器證據：少了它，
  以硬編常數實作的來源維一樣全綠）＋讀取端三態降級（DbErr→整批退預設／缺列或值不可解析→
  **該鍵**退預設、其餘不受波及／每次載入**至多一筆**告警）。**先確認紅**

### Implementation for User Story 4

- [ ] T046 [US4] `rust-api/server/src/model/facade/sys_login_attempt.rs` 加
  `count_recent_failures_by_ip`（★`real_ip <<= $1::inet` 使兩種粒度自然對 inet 欄生效；
  ★**GREATEST 恰兩源**＝窗起點＋解鎖標記，無標記綁 SQL **NULL**〔`GREATEST` 非 strict、
  自然退化〕、**MUST NOT** 用哨兵值；★子查詢必帶窗下界防全歷史回掃）。
  **DoD：T044 由紅轉綠**
- [ ] T047 [US4] `rust-api/server/src/throttle/mod.rs` 擴來源維：`DIM_IP` 常數＋`ip_bucket`
  粒度導出＋★**三鍵讀取端**（`IpThrottleSettings{max_fails, window_minutes, captcha_after}`
  ＋`load_ip_settings`＋鍵名常數三顆 `ip_max_fails`／`ip_window_minutes`／`ip_captcha_after`
  ＋退路常數三顆 `DEFAULT_IP_*`＝seed 同值 **50／15／10**；★**形沿 rev5 帳號維 `load_settings`**
  ——`system_settings::find_by_key` 逐鍵三呼〔rev5 facade **無** `find_by_keys`，勿照搬 rev4 的
  單查詢形〕；★**降級方向＝退預設常數**——DbErr→整批退預設、缺列／值不可解析→**該鍵**退預設
  〔其餘鍵不受波及〕，兩者皆永不 panic、每次載入**至多一筆**告警〔缺三鍵不放大成三筆〕；
  ★桶為 `None` 時**不載入**設定〔沿 rev4 於 `Some(bucket)` 臂內才呼的形、零多餘查詢〕）
  ＋`parse_unlock_marker`（★格式契約＝**unix 秒十進位字串**；不可解析→視為無標記）
  ＋`precheck` 加 `real_ip: IpAddr` 與 `ip_allow: &[IpNetwork]` 兩參＋★**⓪L0 allow 短路**
  （**直讀 allow 袋**、★**絕不經 `decide`**——`decide` 對結構豁免六段亦回放行，經其判定會使
  未登記 allow 的私網來源誤跳節流、違 F5）＋雙維並列合成（任一硬鎖→硬鎖；否則任一軟區→軟區；
  否則放行）＋解鎖標記讀取故障 **fail-closed** ★並**發降級告警**（data-model §5 該列觀測欄
  ＝告警；序列由 T030 pre-register，此處為其**發射點**——缺此則該序列恆 0、等於沒守）。
  ★同批修 **L-026**：三處上下界共用同一顆具名餘裕常數、註解與失敗訊息對齊碼。
  **DoD：T045 由紅轉綠（★含三鍵真消費自證一案）；★既有帳號維 321 支測試零回歸；★T003③
  「三個來源節流鍵零消費者」已知態自此為真解除——無讀取端即帳面不實**
- [ ] T048 [US4] `rust-api/server/src/handler/auth/login.rs` 接線：由 extensions 取上下文，
  把真實來源與 allow 袋餵進 `precheck`。★軟區與鎖定仍 MUST 在密碼雜湊驗證**之前**擋下、
  且拒絕分支**零稽核列零計數桶**。**DoD：先紅後綠——拒絕後解鎖再登入仍可（證明不消耗桶）**
- [ ] T049 [US4] 走查 quickstart §4：同一來源輪換帳號名至軟門檻→要求驗證碼；另一來源不受
  影響；★穿插成功登入後**仍**要求驗證碼。**DoD：三項皆符**

**Checkpoint**: 來源維節流生效、三鍵有消費者——US4 可獨立驗收。

---

## Phase 7: User Story 5 — 超管手動解鎖被鎖的帳號或來源（P3）

**Goal**: 超管可立即解除帳號或來源的鎖定，且**稽核先於生效**。

**Independent Test**: 把某帳號與某來源各鎖到硬門檻，呼叫解鎖後斷言立即可再嘗試；
畸形參數零稽核零狀態；稽核寫入失敗則不解鎖。

### Tests for User Story 5 ⚠️

- [ ] T050 [P] [US5] `rust-api/server/tests/contract.rs` 加 `unlock-login` case。**先確認紅**
- [ ] T051 [P] [US5] `rust-api/server/src/handler/throttle.rs` 之 `#[cfg(test)]`：兩維各一案
  解鎖生效／畸形參數→業務碼且**零稽核零狀態**／★**稽核寫入失敗即中止且快取一概不動**
  （「已生效但零稽核列」構造不可達）／未鎖標的冪等成功。**先確認紅**

### Implementation for User Story 5

- [ ] T052 [US5] `rust-api/server/src/handler/throttle.rs` 新建（★同批於 `handler/mod.rs` 加
  `pub mod throttle;`）：`unlock_login`＋`resolve_unlock_target`；★**動作序寫死**＝①維度解析
  與標的導出（畸形即回、**先於**任何稽核與狀態變更）→②**先寫操作稽核列**（失敗→內部錯誤
  中止、快取不動）→③寫解鎖標記＋清該維鎖定鍵。★標記值格式＝**unix 秒十進位字串**
  （與 T047 讀端同一契約）。**DoD：T051 由紅轉綠**
- [ ] T053 [US5] 帳號維**三件補齊**（★既有節流查詢函式本體**零改動**——前一刀交棒時已預留
  參數位）：解鎖標記鍵（帳號維鍵形）＋讀取端（把標記值餵進計數下界）＋計數標籤。
  **DoD：帳號維解鎖生效之真 redis＋真 DB 測先紅後綠**
- [ ] T054 [US5] 後端 msg key 一鍵（`biz.throttle.invalidUnlockTarget`）＋★依 Lint24 同步律
  同批補**四處**：`zh-tw.ts`／`en-us.ts` 之 `backend:` 樹／`zh-cn.ts` 之 `backend:` 樹／
  `base-web/src/typings/app.d.ts` 之 `App.I18n.Schema.backend.biz` **新增 `throttle` 型節**
  （★該子節此前不存在、需整節新增；後三處為 base-web 既有檔，補在既有
  `[rev5-inline BASE-WEB-I18N-WIRING(ii)/(iii)+ …]` 圈界塊內，授權射程與失敗形同 T038）；
  `rust-api/server/src/router.rs` 加**第六條 ROUTES**
  （`/systemManage/unlockLogin` POST、`Protection::Policy`）＋bump 條數常數至 **22**。
  ★**零新 casbin 政策列**（seed 148 已在）。**DoD：T050 由紅轉綠；`docs-sync lint` 綠；
  `docs-sync generate` 跑得完（不拋 `BackendDictError`）；`pnpm typecheck` 綠；
  `fork-delta-lint` 綠**
- [ ] T055 [US5] 走查 quickstart §5：兩維各解鎖一次、畸形參數零稽核。**DoD：三項皆符**

**Checkpoint**: 解鎖端點與兩維標記到位——US5 可獨立驗收。

---

## Phase 8: Polish & Cross-Cutting Concerns（DoD 收攏）

- [ ] T056 [P] `docs/ops/RUNBOOK.md` 新節：**部署 checklist**——CDN 邊緣網段清單填法與更新
  節奏／信任模型設定檔樣例（★**以 dev 實際掛載的那份為基底**，樣例 MUST 是跑過的形）／
  ★**一致性義務**：CDN 網段在反向代理的 `geo` 區塊與信任模型檔**各存一份、必須同步更新**
  （只改一邊的表徵＝信心大量落 `cdn_mismatch`）／鎖 origin（★**標明已由 F6 硬化入碼、此處為
  縱深防禦建議**）／登入頁快速登入鈕之 prod 前拆除指引（引用既有條目）／其餘 prod 遞延項留
  指針不展開
- [ ] T057 [P] `docs/arc42/ARCHITECTURE.md` 對應節 as-built（信任錨與 IP 閘的位置、
  七態語意、門鈴機制、dev 可達二態）
- [ ] T058 [P] `docs/ops/BACKLOG.md` 帳面處置（spec §2.2）：**B-019 關帳**／**B-073 關帳**／
  **B-071 關帳**（隨 T002 之 PATCH）／B-020 改寫（per-IP 半邊關、通用化半邊續留）／B-008 改寫
  （ip-rule 頁出列、端點卡數 12→7）／B-003 改寫（備註欄四分之一關）／B-072 改寫
  （★防線已備、真實渲染點續掛稽核頁刀——**不宣稱關帳**）
- [ ] T059 [P] `docs/ops/LESSONS.md` append：本刀踩坑（★候選＝rev4 驗收手冊與其 dev 設定
  互相矛盾一事——「驗收程序寫了，但使其成立的設定從未存在」屬**可跨代復發**的形）
- [ ] T060 [P] ★**wire 裁判面重評落帳**：`additionalProperties` 維持已知態不動（動快照生成器
  會牽動既有全部路由的裁判行為、屬 wire 地基面），僅更新該面的警示句——★落點＝
  `rust-api/server/tests/wire_schema.rs` 之「★裁判面界線（誠實記載……）」區塊註記：把
  「38 definitions 內出現次數＝0」的計數改為 **T039 快照重抽後的實測值**（新增
  `Api.IpRule` 系列 definition 後 38 已失準），並補記本刀重評結論＝維持不設
  `additionalProperties: false`（理由同上）。★**只改註解、零斷言改動、零快照改動**。
  **DoD：容器內 `cargo test --test wire_schema -- --test-threads=1` 全綠；該檔 `git diff` 僅含
  註解行（無 `assert`／`const`／`fn` 行變動）**
- [ ] T061 走查 quickstart §7 收尾：★`TRUNCATE sys_ip_rule RESTART IDENTITY`（該表**刻意不在**
  收窄集內、留列必使 gate2 紅）；操作稽核表已納入收窄集免清理。
  ★**本 task MUST 早於 T062**——走查（§2 三次新增、§6 管理頁新增／軟刪〔軟刪不移列〕）會在
  `sys_ip_rule` 留下實列，而 T062 的全量閘含 `schema-gate check`；次序倒置則該閘必紅、且紅得
  「看起來像真缺陷」。**DoD：三閘綠**
- [ ] T062 全量閘（容器內、serial）：`cargo test --workspace -- --test-threads=1`
  ＋`cargo build --release`＋`pnpm typecheck`＋`fork-delta-lint`＋`docs-sync check`
  ＋`schema-gate check`＋本刀兩支新機器守。**前置＝T061 已清走查列。DoD：全綠**
- [ ] T063 `python3 tools/docs-sync.py generate`＋`git add docs/generated`
  （★`reference/routes.md` 應反映 **22 條**、`STATE.md` 反映新 pins 與 ADR／BACKLOG 統計、
  ★`reference/screens.md` 應含 `manage_ip-rule` 一列——該表由 `router/elegant/routes.ts` 的
  `generatedRoutes` 重算，新頁必令其變動，漏跑 generate 即 **Lint02** 當場擋〔訊息指名
  `routes.ts` 來源側〕；同段 `routes.md` 亦同屬 Lint02——Lint01 只在生成檔缺席／多出時
  觸發，勿誤引）

---

## Dependencies & Execution Order

### Phase 依賴

- **Phase 1（Setup）**：`T001→T002` 為**硬閘**（★Amendment accepted 前不得動 base-web 既有檔
  ⇒ 阻塞 **T038／T041／T054**——凡動 base-web 既有檔者皆受管，非僅 T041）；T003 可與
  T004／T005 平行；`T004→T005→T006`。
- **Phase 2（Foundational）**：依賴 Phase 1（T004 依賴、T005/T006 設定）→ **阻塞全部 US**。
  `{T007、T011、T012 平行}→T008→T009→T010`；`T013` 依賴 T007＋T011（型別）；`T013→T014`；
  `T015` 全程可平行（純實測）。
- **Phase 3~7（US1~US5）**：皆依賴 Phase 2。實作序建議照優先序 US1→US2→US3→US4→US5。
- **Phase 8（Polish）**：依賴全部 US；T063 須在 T036／T054（ROUTES 增列）與 T058／T059
  （BACKLOG／LESSONS 增列）之後；★**T061→T062 為硬序**（走查清列先於全量閘，理由見 T061）。

### User Story 依賴

- **US1（P1）**：Phase 2 後即可開，零 US 依賴 → **MVP**。
- **US2（P2）**：依賴 US1（需 `request_context_mw` 注入的上下文；`ip_gate_mw` 掛在其後）。
- **US3（P2）**：依賴 US2（`decide`／`would_self_lock`／`reload_and_publish` 皆為其消費面）。
- **US4（P3）**：依賴 US1（真實來源）＋US2（allow 袋供 L0 短路）。
- **US5（P3）**：依賴 US4（解鎖標記的讀端在其中）。
- ★**單元序不可並發的四組共用檔**：①`router.rs`——T021／T029／T036／T054 皆改它，且 T036／T054
  同 bump **同一個條數常數**，並行必衝且**不會被編譯擋**、只會在最後由條數核對才發現
  ②`contract.rs`——T031／T050 改**同一個 registry vec** ③`middleware/mod.rs`——T018（US1）與
  T028（US2）同檔遞進 ④**i18n 共用檔**——T038（U-H）與 T054（U-K）補 `backend:`
  鍵於 `locales/langs/{zh-tw,en-us,zh-cn}.ts`＋`app.d.ts`；T041（U-I）補 `route:`／`page:` 鍵於
  `locales/langs/{en-us,zh-cn}.ts`＋`app.d.ts`（★`zh-tw.ts` **不在** T041 射程——該檔只有
  `backend:` 樹，契約 msg-keys 軌道歸屬表明文「路由／頁面鍵不進治理錨點檔」）。三者交集＝
  `en-us.ts`／`zh-cn.ts`／`app.d.ts`，同檔不同區塊，並行必衝且**只會在最後 `pnpm typecheck`
  才發現**。⇒ US 的「獨立可驗收」成立於**交付面**，不成立於**單元併發面**。

### Within Each User Story

- 測試先寫、**先確認紅**（各 phase 的 Tests 段在 Implementation 段之前）。
- facade（model）→ handler（service）→ router 註冊 → 前端接線 → quickstart 走查。
- ★`router.rs` 與 `contract.rs` 於**各自的 US phase** 加自己的列（沿 003 的刻意修正）——
  收斂到尾端會使該 US 在自己的 phase 內無法端到端驗收；代價是該二檔出現在多個單元的允許檔
  清單內（防呆⑥的「清單只縮不擴」是單元內規則，跨單元重複出現不違反）。

### Parallel Opportunities

- Phase 2：T007／T011／T012 三支**主體檔**不相交、可分派；★但 T007／T011 共用 `lib.rs`、
  T012 共用 `facade/mod.rs` 之**註冊行**——★**每一條註冊行只由單一單元追加**（不跨單元同時
  改同一行）；逐行分派見 Implementation Strategy 之分批說明。
- US1：T016／T017 兩支測試可分派；T020 與 T018／T019 檔域不相交。
- US2：T023／T024 可分派；T026 與 T025／T027 檔域不相交。
- US3：T031／T032 可分派；T033／T039 可分派；★T040 與 T041 **不可**併行（T041 的產物四檔由
  T040 新建的 view 觸發重算、有生成相依）。
- US4：T044／T045 可分派。
- US5：T050／T051 可分派。
- Phase 8：T056／T057／T058／T059／T060 五支可分派。
- ★**cargo 執行一律序列**——[P] 僅指可分派給不同執行單元。

---

## Parallel Example: Foundational

```text
# 三支主體檔併行分派（★共用的模組註冊行每條只由單一單元追加、見分批說明）
Task: "T007 trust 型別群＋is_trusted 單一 helper in rust-api/server/src/trust/mod.rs"
Task: "T011 ipgate 純函式核（decide／六段豁免／would_self_lock）in rust-api/server/src/ipgate/mod.rs"
Task: "T012 sys_ip_rule facade 讀端 in rust-api/server/src/model/facade/sys_ip_rule.rs"
```

---

## Implementation Strategy

### 執行單元切分（T 號區間；★編排消費面）

以 T 號區間界定單元邊界（沿 001／003 前例）。每單元一支 Workflow（內部 serial：
implementer(TDD) → spec-compliance review → fix 迴圈 → code-quality review → fix 迴圈），
依 CLAUDE.md §2 防呆六件套與看門狗紀律（★Workflow launch 與 Monitor 看門狗**同一回合原子
成對**發射）。

| 單元 | T 區間 | 允許檔案清單（起始） |
|---|---|---|
| U-A ★主線 | T001~T003 | `docs/arc42/decisions/`、`.specify/memory/constitution.md` |
| U-B | T004~T006 | 兩份 `Cargo.toml`、★`rust-api/Cargo.lock`（由 `cargo build` 機器重算、禁手改）、`config.rs`、`deploy/trust-model.dev.toml`、`docker-compose.dev.yml` |
| U-C | T007~T010 | `trust/mod.rs`、★`lib.rs` |
| U-D | T011~T012 | `ipgate/mod.rs`、★`lib.rs`、`facade/{sys_ip_rule,mod}.rs` |
| U-E | T013~T015 | `state.rs`、`main.rs`、`tests/common/mod.rs`、★`router.rs`（僅其 `mod tests` 的 stub_state）、★`auth/enforce.rs`（僅其 `mod tests` 的 `state_with`）、★`model/mod.rs`（僅其 `test_db::real_app_with`）、★`throttle/mod.rs`（僅其 `mod tests` 的 `throttle_app`）、兩支 lint |
| U-F | T016~T022 | `middleware/mod.rs`、★`lib.rs`、`request_context.rs`、`facade/sys_login_attempt.rs`、`router.rs` |
| U-G | T023~T030 | `ipgate/mod.rs`、`middleware/mod.rs`、`cache/mod.rs`、`main.rs`、`router.rs`、`obs.rs` |
| U-H | T031~T038 | `contract.rs`、`router.rs`、`model/{audit,mod}.rs`、`facade/{sys_ip_rule,sys_operation_log,mod}.rs`、★`handler/{mod,ip_rule}.rs`、`tools/schema-gate.py`、★**i18n 四處**＝`locales/langs/{zh-tw,en-us,zh-cn}.ts`＋`typings/app.d.ts`（後三者為既有檔，僅其 `backend:`／`Schema.backend` 節） |
| U-I | T039~T043 | `rev5-ip-rule.{ts,d.ts}`、`views/manage/ip-rule/` 三檔、兩語 locale、`app.d.ts`、`router/elegant/` 三檔＋`typings/elegant-router.d.ts`（★路由外掛產物四檔）、`tools/`（兩支新守）、★`rust-api/server/tests/fixtures/wire-schema.json`（T039 之 DoD「快照納入新檔」的實體、由生成器重抽） |
| U-J | T044~T049 | `facade/sys_login_attempt.rs`、`throttle/mod.rs`、`handler/auth/login.rs` |
| U-K | T050~T055 | `contract.rs`、`router.rs`、★`handler/{mod,throttle}.rs`、`throttle/mod.rs`、`cache/mod.rs`、★**i18n 四處**＝`locales/langs/{zh-tw,en-us,zh-cn}.ts`＋`typings/app.d.ts`（後三者為既有檔，僅其 `backend:`／`Schema.backend` 節） |
| U-L | T056~T063 | `RUNBOOK.md`、`ARCHITECTURE.md`、`BACKLOG.md`、`LESSONS.md`、★`rust-api/server/tests/wire_schema.rs`（僅其「裁判面界線」註記、T060）、★`docs/generated/**`（★T063 由 `docs-sync.py generate` **機器重算**產出、**禁手改**——agent 只得跑該指令後 `git add`） |

★清單以「★」標出者為**模組註冊檔與散布點**（`lib.rs`／`handler/mod.rs`／`facade/mod.rs`／
`AppState` 的四處**散布** struct literal〔`tests/common/mod.rs` 為 T014 主體檔、不另標星；
五處完整枚舉見 T014〕／i18n 四處落點〔見 T038／T054〕）——漏列即 fix
agent 撞清單外檔而 blocked（防呆⑥「清單只縮不擴」）。

★**`lib.rs` 的三個新註冊行分批追加**：U-C 加 `trust`／U-D 加 `ipgate`／U-F 加 `middleware`；
`facade/mod.rs` 由 U-D 加 `sys_ip_rule`、U-H 加 `sys_operation_log`；`handler/mod.rs` 由 U-H
加 `ip_rule`、U-K 加 `throttle`。**終態皆須嚴格 ASCII 升冪**。

★**U-I 對 U-A 是硬序**（憲法授權在前、動 base-web 既有檔在後）；★**U-H／U-K 亦對 U-A 硬序**
——兩單元的 msg key 落點含 base-web **既有檔**（`en-us.ts`／`zh-cn.ts`／`app.d.ts`），同受
「T002 accepted 前不得動 base-web 既有檔」硬閘管（該三處的**授權**本身已在憲法 §III.2
(ii)(iii) 射程內、不需新軌道，但硬閘按「既有檔」判、與授權來源無關）。U-C~U-G、U-J 為純
後端、不受該閘阻擋。

★**編排注意**（B-070 已知態）：改動 Workflow script 後以 resume 續跑會使看門狗上限推導沿用
**舊快照**；需某階段重跑一律**新開單階段 workflow**（新 runId、零快取糾纏），不用 resume。

### MVP First

1. Phase 1（★Amendment 需 user 親決）→ 2. Phase 2 → 3. Phase 3（US1）→
**STOP & VALIDATE**：quickstart §1 走通＝稽核列記下的是真實來源與其可信度（此前記的是最近
一跳代理位址、且信心恆為單一字面）。

### Incremental Delivery

US1（來源真實性）→ US2（存取閘）→ US3（規則管理前後端）→ US4（來源維節流）→ US5（解鎖）→
Phase 8 DoD。每個 US 完成即可獨立驗收、不破壞前面的 US。

### 收尾（★不在本清單內）

全單元完成 → final holistic review → `superpowers:finishing-a-development-branch`
（★push／merge 需 user 同意）→ 收刀簿記三步（events append＋NOTES 改下一步＋
`docs-sync generate`）。★動 `docs/ops/NOTES.md` 前先確認其行數預算（Lint07）；
events `summary` ≤300 字、細節走 `notes` 欄。

---

## Notes

- [P]＝檔域不相交可分派；★cargo 執行一律序列（容器內 `--test-threads=1`）。
- 測試先確認紅再實作；每個 task 或邏輯群組後 commit（子庫 commit → 外層 bump pin）。
- 任一 checkpoint 皆可停下獨立驗收該 US。
- 避免：跨 US 破壞獨立性、同檔並行、在 Amendment accepted 前動 base-web 既有檔、
  以 resume 讓某階段重跑、走查時忘了帶構造轉發標頭。
