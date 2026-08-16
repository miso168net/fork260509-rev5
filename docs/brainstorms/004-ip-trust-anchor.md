# 004-ip-trust-anchor — IP／信任錨刀 brainstorm（階段 0）

- 日期：2026-08-12｜狀態：四題開場拍板＋設計五節（A～E）逐節過 user 核可；下一步＝**手動**
  `/speckit-specify`（本檔為其 input；不自動觸發——否則 feature-branch pre-hook 不跑、
  spec 落 default branch）。
- 一句話：把「三端備好、中間沒接」的 IP 域接通——rev4 七態信任錨全形＋Tier-1 錨硬化
  （傳輸層背書）入首版＋IP 存取閘＋per-IP 節流啟用＋ip-rule 管理頁前後端全套＋管理員
  解鎖端點＋部署 checklist。
- 交付價值：本域是 repo 內「基建完成度最高、實作完成度為零」的一塊（nginx CF 權威驗證閘
  已完整、`sys_ip_rule` 與 seed 與 casbin 政策全在且零列零碼、`request_context.rs` seam
  已寫死在碼內）；本刀接通中間段，並兌現前代懸了兩代的「信任錨傳輸層背書」安全承諾。
- 權威輸入：**BACKLOG B-019 條目本文**（射程＋六個拍板級前置＋兩項檢查點的權威家）；
  rev4:ADR 0043／0044／0045＋rev4 `trust/`（718 行）`ipgate/`（611 行）`handler/ip_rule.rs`
  （1550 行）`facade`（762 行）約 3,600 行藍本（§I.5＋ADR 0019 紀律：重打字消化、註解
  一律重寫、rev5 拍板差異點不得帶回）；啟動書 K1／K2 對應條（§9 盤點）。

## 1. 開場四題拍板紀錄（user 拍板 2026-08-12）

| 題 | 拍定 | 要點 |
|---|---|---|
| CDN 半邊交付形 | **全形版：搬 rev4 七態全套** | TrustModel TOML＋三層＋兩 overlay＋七態信心整套重打。選項既載效益＝未來多層 CDN/LB 拓樸不重開刀、rev4 藍本完整承襲。連動三筆：①XFF 鏈解析進場 ⇒「PG 把關即足夠」論證重驗（§5.3）②AppState 需 `trust_model`＋`ip_rules` 兩欄（§4.4）③rev4 承重前提隨 Tier-1 位置錨回歸——由下一題硬化拍板處理。棄案＝縮態版（僅信 nginx 傳輸層判定、態縮）與不寫版（prod CF 拓樸下 real_ip 恆 CF 邊緣 IP、per-IP 節流與 IP 規則形同虛設＝B-019 存在理由被掏空）。 |
| Tier-1 錨硬化（rev4:B-080） | **入首版：錨須傳輸層背書才成立** | 錨成立條件新增「最右 CDN 段之右鄰起、直到傳輸層對端（含 peer 本身），全屬受信基建集」，不成立→錨棄用、退 Tier-2。rev4 不硬化的顧慮（誤傷合法多層 CDN/LB 拓樸）在 rev5 不成立——拓樸已枚舉定形（client→CF?→nginx→rust-api、nginx 唯一 ingress），啟動書 K2-04 預判成立。部署 checklist 的「鎖 origin」條目自「安全成立的承重前提」**降級為縱深防禦建議**。攻擊形對照：origin 裸露＋偽造 XFF 注入公開 CDN 邊緣 IP——rev4 舊形得 `cdn_anchored` 可繞 deny／跳節流；硬化後 TCP 對端＝攻擊者自己（不受信）⇒ 錨不成立、real_ip＝攻擊者 peer IP、偽造失敗。 |
| UI 半邊 | **全套入刀：頁＋抽屜＋搜尋** | `manage_ip-rule` 管理頁三檔（rev4 藍本重打）；B-003 之 `wbip_memo` 欄順帶兌現；seed 選單「僅 R_SUPER 可見、點擊 404」已知態解掉一格；驗收走 CDP 三方對照（22080 vs 42080）。連動＝route 鍵 i18n 必然 inline 動 upstream 兩語檔 ⇒ **§III.2 新軌道 Amendment**（B-019 六前置之外的第七個拍板點，§6.2）；B-071 之 §III.1 措辭 PATCH 順帶同批拍。 |
| B-072 兌現形 | **建可繼承防線＋改寫條目、不宣稱關帳** | 事實前提攤開：`x_forwarded_for` 欄只在三張稽核表、`sys_ip_rule` 無此欄、rev4 全前端零渲染（grep 零命中）、真實渲染點屬 B-008 audit 頁（不在本刀射程）。兌現形＝本刀新頁對自由文字欄（`wbip_memo`）一律純文字插值＋「`views/manage/**` 零 `v-html`／`innerHTML`」機器守（附 self-test、ADR 0024 非 vacuous 紀律）；B-072 條目改寫為「防線已備、XFF 渲染點續掛 audit 頁刀」。棄案＝audit 頁一併入刀（雙域大刀、與 B-019 射程定義相抵）。 |

## 2. 射程總表與帳面處置

### 2.1 交付物七類

| # | 交付物 | 內容 |
|---|---|---|
| 1 | trust 模組（全形） | 七態信心＋三層（peer-gate→Tier-1 CDN 錨→Tier-2 rightmost-untrusted）＋兩 overlay（tunnel／CF）＋★硬化（錨須傳輸層背書否則退 Tier-2）＋canonical 單點；rev4 四項改善全保留 |
| 2 | ipgate | RuleSet（ArcSwap 判定面）＋decide 純函式（白＞黑＞default-allow）＋結構豁免六段＋`ipgate:invalidate` pub/sub 熱重載（keep-last-good） |
| 3 | middleware 層 | `request_context_mw`（每請求解析一次注入 extensions）＋`ip_gate_mw`（判定短路 5003/403）；RequestContext 之 `real_ip` 推導換為信任錨結果＝B-019 seam 兌現、消費面不動 |
| 4 | per-IP 節流 | 兩段式（軟門檻→captcha、硬門檻→鎖至時窗滑過）、與帳號維並列合成；GREATEST 恆兩源＋禁 reset-on-success（rev4:0045 blocker 級不變式）；ip_* 三鍵啟用＝ADR 0039 解除 |
| 5 | 管理端點 | ip-rule 5 支（list/add/update/delete/restore）＋`would_self_lock` 防自鎖拒寫＋B-073 解鎖端點（寫 user 維＋IP 維兩 marker） |
| 6 | 前端 | `views/manage/ip-rule` 三檔＋typings（ADAPT 軌）＋`rev5-ip-rule.ts` wrapper（WRAPPER 軌）＋route 鍵 i18n inline（§III.2 新軌道）＋`wbip_memo` 欄（B-003）＋B-072 防線 |
| 7 | 治理文件 | §I.7 島 F 入憲（MINOR）／AppState 5→7 欄 ADR／§III.2 新軌道 Amendment／B-071 PATCH／部署 checklist／redis AOF 重評結論／gate2 常數加一行／region 明文排除 |

### 2.2 BACKLOG 帳面處置（收刀時）

| 條目 | 處置 |
|---|---|
| B-019 | **關帳**（核心兌現） |
| B-020 | 條目改寫：per-IP 半邊關、通用化半邊續留（等 B-021 的第二消費者） |
| B-008 | 條目改寫：ip-rule 頁出列、端點卡數 12→7 |
| B-003 | 條目改寫：`wbip_memo` 四分之一關（餘 user／role／menu 三張） |
| B-072 | 條目改寫：防線已備、XFF 渲染點續掛 audit 頁刀（不關帳） |
| B-073 | **關帳**（解鎖端點＋兩維 marker＋user 維「鍵＋讀取＋label」三件落地） |
| B-071 | 隨 §III.2 Amendment 同批拍 PATCH → 關帳 |
| L-026 | 順帶修：throttle 三處上下界共用同一顆具名餘裕常數、註解與失敗訊息對齊 |
| wire 裁判面上限 | 重評結論落帳：`additionalProperties` 維持已知態不動（動快照生成器牽動既有 16 條 route 裁判、屬 wire 地基面）、警示句更新 |

### 2.3 明確不做

B-021（前置＝改密端點存在，屬 user 中心域）；B-020 通用化半邊；audit 頁＋5 支稽核端點與
policy-archive 2 支（B-008 續留）；region 半邊——GeoIP／xdb 整包不搬（ADR 0014 第 2 款；
rev4:K1-46 排除）；`access_log` middleware（B-016 域外不變）；prod 資產（ADR 0014 持續
有效——部署 checklist 是文件、不是 prod 配置檔）；B-029 殘餘兩件不觸發（本刀不動登入頁
碼與 captcha 產圖）；B-027 排序不觸發（rev4 ip-rule 刀已判後端預設排序足）；B-018 demo
面不動。

## 3. B-019 六前置與兩檢查點處置對照

| 前置／檢查點 | 處置 |
|---|---|
| ①dev 無 CF ⇒ 四態結構性不可驗 | §1 兩題拍定：全形＋硬化。dev 可驗性補償＝純函式全態矩陣＋E2E 可驗態誠實分界（§8.1） |
| ②AppState 第六／七欄 | 新 ADR 承載（§4.4；ADR 0029 封條要求的拍板即此） |
| ③§I.7 第六座行為島入憲 | MINOR Amendment（§7.1；rev4:0044 五條＋硬化條款） |
| ④gate2 對 `sys_operation_log` 收窄 | 常數加一行**排進 tasks**（§7.4；不當 bug 追） |
| ⑤redis 不開 AOF 重評 | 重評結論＝維持不開、論證落已知態 ADR（§7.2） |
| ⑥`region` 半邊排除 | 明文排除（§2.3；ADR 0014 第 2 款過境） |
| 檢查點 1：ADR 0033 load-bearing | 本刀不動 denylist；「status 即權威」與「§I.3 凍結面」零鬆動——13 碼矩陣不動（阻擋 reuse `5003`、自鎖 reuse `2222`）；spec 內明文聲明 |
| 檢查點 2：兩個易漏設計面 | `would_self_lock`（§5.4）與 `ipgate:invalidate` pub/sub 熱重載（§4.2）均入射程 |

## 4. 後端設計：trust／ipgate／middleware／AppState

### 4.1 trust 模組（全形七態＋硬化）

- `Confidence` 七態（DB/wire 小寫 snake：`cdn_verified`／`proxy_clean`／`direct`／
  `cdn_anchored`／`proxy_soft`／`cdn_mismatch`／`fallback`）＋
  `resolve_client_ip(trust_model, peer, xff) -> (IpAddr, Confidence, Evidence)` 純函式三層：
  ①peer-gate（peer∉信任集→直取 peer、忽略 XFF、`direct`）→②Tier-1 CDN 位置錨→
  ③Tier-2 rightmost-untrusted。
- ★硬化落點：Tier-1 錨成立條件新增「錨右鄰起、直到傳輸層對端（含 peer 本身），全屬受信
  基建集」——不成立→錨棄用、退 Tier-2。受信集＝與跳過集同一 helper 導出（rev4 改善①之
  單一來源；硬化檢查不另立集合）。
- 兩 overlay 照搬：tunnel fallback（信心不升）；CF overlay 四前置（peer∈`cf_gate_egress`
  ／`X-CF-Verified=1`／訪客標頭有值／基礎信心∈可升等集）→升 `cdn_verified`、不一致降
  `cdn_mismatch`、只動信心不動位址。
- canonical 單點（IPv4-mapped 折 v4、全下游同拿 canonical 形）、`MAX_XFF_TOKENS=32` 保
  最右（方向不可反）——皆 rev4 原樣。
- 設定源沿 rev4 全套：`TRUST_MODEL_FILE` 指 operator TOML（六集合）、boot 一次載入
  `Arc<TrustModel>`；解析失敗語意三層（永不 panic、皆結構化告警）＝缺檔→flat env
  `TRUSTED_PROXY_CIDRS` 退路／TOML 整體壞→全空 all-direct（★不套 env 退路：設定存在但壞
  不得擴大信任）／單集合含無效 CIDR→該集合整清空（只縮小信任）。**dev 無設定＝全直連**
  （沿 rev4 dev 形）。

### 4.2 ipgate 模組

`RuleSet{allow,deny}` 兩袋、`Arc<ArcSwap<RuleSet>>` 每請求 lock-free 零 DB/Redis；`decide`
純函式判定序＝結構豁免六段（loopback v4/v6＋RFC1918 三段＋ULA）→白→黑→default-allow
（any-match 集合語意、無優先權欄）；boot 初載失敗→空集 fail-open；熱重載＝寫端
`reload_and_publish`（重載＋redis pub `ipgate:invalidate`）＋專用 pub/sub 連線 watcher、
真相暫不可讀→keep-last-good 不清空。

### 4.3 middleware 層（rev5 首次進場）

- `request_context_mw`（ConnectInfo peer＋標頭抽取→trust 純函式→組 RequestContext 注入
  extensions、每請求恰一次）→`ip_gate_mw`（①健康／觀測短路②ctx 缺席放行③Deny→`5003`
  /403 信封＋blocked 結構化告警）。
- **B-019 seam 承諾兌現形**：`RequestContext` 三欄與取值器簽名不動——`real_ip` 內容從
  「X-Real-IP 原樣」換為「信任錨推導之 canonical 字串」、`ip_confidence` 從恆 `nginx_peer`
  換七態、`x_forwarded_for` 原樣淨化轉錄照舊；欄私有＋`compile_fail,E0451` doctest 續存；
  handler 改由 extensions 取（`from_headers` 退為測試建構途徑）。
- 連帶：`nginx_peer` 字面退役、七態表取代（三張稽核表 `ip_confidence` 無 CHECK＝免
  migration）；`sys_login_attempt.peer_ip`（inet 可空、003 恆 NULL）順帶開始填傳輸層對端
  ——鑑識三欄（peer_ip／real_ip／ip_confidence）自此齊活，細節 plan 期對 001 data-model
  定案。

### 4.4 AppState 5→7 欄

`ip_rules: Arc<ArcSwap<RuleSet>>`＋`trust_model: Arc<TrustModel>`，新 ADR 承載（ADR 0029
封條「開欄須拍板」要求的拍板即此；`mailer` 續留域外、封條句改寫保留）。

### 4.5 fail-\* 鏈總覽（島 F 方向）

全鏈 fail-open（trust 壞→all-direct；規則載入敗→空集；門鈴／快取故障→keep-last-good／
放行），**唯一 fail-closed＝寫端自鎖拒寫**（`would_self_lock`）；每次降級必發結構化告警。

## 5. per-IP 節流＋解鎖端點＋稽核寫入面

### 5.1 per-IP 節流（rev4:0045 終態沿用、落點＝003 throttle 模組擴維）

- 兩段式：滑動窗內失敗 ≥`ip_captcha_after`→軟區（captcha）、≥`ip_max_fails`→硬鎖至時窗
  滑過；與帳號維**並列判定、合成**（任一硬鎖→硬鎖、否則任一軟區→軟區、否則放行）。
  三鍵自此有執行面消費者＝**ADR 0039 解除**（零 migration、零 seed 變更）。
- ★GREATEST 恆兩源（時窗起點＋該 IP 解鎖 marker）、**MUST NOT 把 reset-on-success 移植
  進來源維**——rev4 對抗式審查 CONFIRMED blocker 原樣承接，負向自證測試（穿插成功登入
  不重置來源計數）同刀落地。
- 計數鍵粒度：IPv4 `/32`、IPv6 聚合 `/64`、IPv4-mapped 先 canonical 折 v4（防雙棧計數桶
  家族分裂）。
- 負快取沿 003 帳號維不變式（僅短路已鎖、僅 L2 再判路徑寫入、TTL 不長於時窗、命中不
  續期）；marker 讀取故障 fail-closed（島 E 降級⑤對稱擴充）；命中顯式 allow 規則跳來源維
  節流、結構豁免段不跳（F5）。島 E「軟區與鎖定在密碼驗證之前擋下、零稽核列零計數桶」對
  IP 維同樣成立。
- L-026 順帶修落點在此。

### 5.2 B-073 解鎖端點

POST 管理端點（路徑形 plan 期照 rev4 藍本定），參數至少一維（帳號名／IP），寫對應維
unlock marker——user 維補「鍵＋讀取＋label」三件（003 research R3-17 交棒形、throttle
handler 零改動），IP 維 marker 隨本刀誕生即有寫入者。casbin 政策列新增＝seed 演進一筆
（001 紀律：refresh＋演進帳登記＋三閘綠）。UI 鈕不做——解鎖鈕的家在 user 管理頁（不存
在），本刀 API-only、contract test 驗，「端點已備、鈕待 user 管理刀」記入已知態。

### 5.3 稽核寫入面＋「原樣轉錄」射程界線重驗

- login 三處落列點**零改動**——`real_ip`／`ip_confidence` 內容隨 RequestContext 推導升級
  自動變化（seam 承諾兌現的驗證點）。
- 重驗結論：003 的「real_ip 型內零驗證、合法性外包 PG INET」論證在全形下**不再承重**——
  `resolve_client_ip` 產出 `IpAddr` 型（合法性由型別保證）、canonical 字串落 INET 恆合法；
  XFF walk 的 token 解析（parse 失敗處理＝新驗證面、依 rev4 語意 plan 期定案）獨立於轉錄
  欄——**稽核轉錄軌（原樣淨化）與推導解析軌雙軌並存、互不影響**。
- 邊界案反轉一筆（消費面可見、記入 spec）：real_ip「缺席→空字串→PG fail-loud」路徑消失
  ——peer（ConnectInfo）恆有值，integration 直打 8080 落 `direct` 態；`with_real_ip` 測試
  注入形要重整。
- dev 已知態（沿 rev4 dev 形、記入 spec）：dev 無 TOML＝all-direct ⇒ dev 實跑 `real_ip`
  ＝傳輸層對端（容器位址）、per-IP 計數單桶（rev4 ARCHITECTURE 明載同形已知態）；E2E
  走查勿觸硬鎖、必要時以解鎖端點自癒。
- `clamp_source_ip`：canonical IP 恆 ≤45 字元、行為不變、註解對齊（plan 細節）。

### 5.4 操作稽核首寫＋would_self_lock

ip-rule CRUD 與解鎖動作落 `sys_operation_log`（rev4 藍本有欄語意）＝rev5 首個寫入者；
gate2 常數加一行排 tasks（§3 前置④）。`would_self_lock`：寫端前檢查「此規則生效後發起者
自己的 canonical real_ip 是否被鎖在門外」→會即拒寫（唯一 fail-closed）；錯誤碼 reuse
`2222`＋穩定 msg key（13 碼矩陣不動）。

## 6. 前端＋§III.2 新軌道

### 6.1 頁面與軌道分工

- 頁面三檔（rev4 藍本重打、新檔＝新增型檔頭標記、免 ★ 授權）：`views/manage/ip-rule/
  index.vue`＋`modules/ip-rule-operate-drawer.vue`＋`modules/ip-rule-search.vue`。列表
  （含 `wbip_memo` 欄：多行 text、僅管理列表顯示、對外取用處不帶——語意權威＝001
  data-model）＋新增／編輯抽屜＋搜尋＋回收桶復原；4 顆按鈕權限碼接 seed 既有 `hasAuth`。
  選單鏈零 seed 改動（dynamic mode 下 getUserRoutes 已回 manage_ip-rule 列）。
- typings 新檔（`Api.IpRule`）→ ADAPT 軌；`service/api/rev5-ip-rule.ts` wrapper 5 支 →
  WRAPPER 軌（unlock 端點無 UI 鈕、不建 wrapper）。

### 6.2 §III.2 新軌道 Amendment（提案形、user 屆時親決）

軌道名暫擬 `★BASE-WEB-MANAGE-VIEW-WIRING`、用途 (i)「manage 域新 view 接線」，範圍三塊：
①兩語 locale 檔 route 鍵＋`page.manage` 新子樹（inline；灰帶不玩、明文入用途範圍）
②`app.d.ts` 對應型節（如需）③`src/router/elegant/` 三生成檔——由 elegant-router 插件
重算產出、逐行標記會被下次重算抹掉，授權紀律擬「僅由插件重算產出、禁手改、重算冪等驗收」
（fork-delta-lint 對此範圍的處置 plan 期實測工具行為後定案）。兩語鍵集相等紀律沿
I18N-WIRING。MINOR bump；B-071 之 §III.1 措辭 PATCH 同批拍。

★**校正（2026-08-12 跨產物檢查；拍板語意不變、僅更正事實）**：上段②「`app.d.ts` 對應型節
（如需）」實為**必需**——`page:` 是顯式型樹，`page.manage.ipRule.*` 不補型即型別檢查紅；
③「三生成檔」實為**四支**——`src/router/elegant/{imports,routes,transform}.ts` ＋
`src/typings/elegant-router.d.ts`（四支檔頭皆帶 `Generated by elegant-router`）。
軌道範圍以 spec FR-041 的逐支清單為準（共七支檔）。

### 6.3 B-072 可繼承防線

自由文字欄一律純文字插值（Vue 預設轉義）；機器守＝「`views/manage/**` 零 `v-html`／
`innerHTML`」lint 斷言，掛 pre-commit、附 self-test（塞 v-html 樣本必紅＝非 vacuous、
ADR 0024 紀律）；落點在 tools/ 既有 lint 家族或 fork-delta-lint 內加規則（plan 定）。

## 7. 治理文件面

### 7.1 憲法 Amendment（一次 ADR、一次 MINOR bump、user 親決；沿 ADR 0028 多塊合拍慣例）

- §I.7 島 F 入憲：rev4:0044 五條原樣（F1 判定序／F2 真相分層 keep-last-good／F3 fail-open
  ＋唯一 fail-closed＝寫端自鎖、降級必告警／F4 信任錨唯一輸入＋同源對稱／F5 顯式放行跳
  節流、結構豁免不跳）＋**新增硬化條款**（Tier-1 錨須傳輸層背書否則不成立——入憲後反轉
  ＝MAJOR）。
- 島 E 補一句來源維釐清：帳號維三源（含 reset-on-success）vs 來源維恆兩源（禁
  reset-on-success）——刻意不對稱入憲、防日後被「統一」（同跨島註手法）。
- §III.2 新軌道（§6.2）＋B-071 之 §III.1 措辭 PATCH 同批。

### 7.2 ADR 群（本刀預計新立）

AppState 5→7（§4.4）／憲法 Amendment ADR（§7.1）／本刀已知態 ADR——含 redis AOF 重評
結論＝**維持不開**（論證：IP 維 redis 態丟失後果被「PG 為權威」封頂——L1 僅加速、marker
丟＝可再解鎖自癒、ipgate 判定面不依賴 redis；與 ADR 0033② 同構）、「解鎖端點無 UI 鈕」
已知態、dev all-direct 已知態（§5.3）／ADR 0039 明文解除（隨已知態 ADR 或 supersedes 形）。

### 7.3 部署 checklist（落 RUNBOOK 新節）

CF 網段 geo 清單填法＋定期更新程序／鎖 origin（降級為縱深建議、標明硬化已入碼）／
`TRUST_MODEL_FILE` TOML 樣例／B-064 拆快速登入鈕（prod 前置引用）／其餘 K2-10 項留指針
指 ADR 0014、不展開。

### 7.4 機器面兩筆（排進 tasks）

gate2 常數加一行（`sys_operation_log` 入 runtime-append 收窄集、ADR 0036 擴充機制）；
unlock casbin 政策列＝seed 演進一筆（refresh＋演進帳＋三閘綠、RUNBOOK §10 紀律）。

## 8. 測試策略與驗收

### 8.1 可驗性分界（誠實記入 spec）

dev 預設 all-direct ⇒ E2E 實跑僅 `direct` 態；其餘六態由**含 TOML 之純函式／integration
矩陣**覆蓋（七態×三層×兩 overlay×硬化成立／不成立×canonical×token 上限——直打 8080 可注
任意標頭與 TrustModel、全態可驗）；「真 CF 流量過真 nginx geo」一段屬 prod 專屬、nginx 側
承 rev4 已驗證形＋部署 checklist 承載。

### 8.2 測試面

- ipgate：decide 矩陣＋豁免六段＋keep-last-good＋門鈴熱重載 integration；`would_self_lock`
  拒寫 integration。
- throttle：GREATEST 兩源負向自證（穿插成功不重置）＋並列合成矩陣＋粒度（/64、mapped
  折疊）＋marker fail-closed；B-059 已知態測區（診斷面已烤入、再現時據傾印定案）。
- contract：ROUTES 16→22（5 CRUD＋unlock），coverage gate 自動強制每條 route 有 case。
- rust 容器內全程 serial；前端驗收＝CDP 三方對照（22080 vs 42080）＋v-html lint 機器守。
- 收刀前：三閘綠＋refresh＋演進帳（§7.4）。

### 8.3 編排注意

TDD 期以 Workflow 編排（CLAUDE.md §2 防呆六件套）；B-070 已知態＝改 script 後 resume 的
watchdog 上限推導用舊快照——需某階段重跑一律新開單階段 workflow、不用 resume。

## 9. K1／K2 承襲盤點（B-001 要求①）

| 條目 | 處置 | 本刀消費點 |
|---|---|---|
| K1-38 節流負快取終態＋來源維規則 | 沿用 | GREATEST 兩源、禁 reset-on-success、負向自證守門（§5.1） |
| K1-43 信任錨終態（四改善＋承重前提重估指示） | 沿用＋兌現 | 四改善全保留（§4.1）；承重前提由硬化拍板解除（§1 題二） |
| K1-44 島 F 入憲 | 沿用 | 五條原樣＋硬化條款新增（§7.1） |
| K1-17 IP 閘原案 | 已決·重審 | 還原節已被 rev4:0043 翻案，以終態為輸入、不重走原案 |
| K1-46 region GeoIP | 排除 | ADR 0014 第 2 款；xdb 整包不搬（§2.3） |
| K1-62 讀端契約最小誠實形演進 | 沿用 | `IpRuleRecord` 審計欄上 wire＋filter（plan 期對 rev4 契約定形） |
| K1-63 按鈕碼 seed 前置鏈 | 沿用 | seed 已在、`hasAuth` 接線（§6.1）；授權下放前置歸 B-024 域不動 |
| K1-61 回收桶復原 MODAL-WIRING | 不適用 | rev5 無 modal 軌道；復原走自建頁 UI（新增型、§6.1） |
| K2-04 錨傳輸層背書 | **兌現** | 硬化入首版（§1 題二）——本刀核心 |
| K2-05 節流通用 seam | 半邊消費 | per-IP 半邊兌現；通用化半邊續留 B-020（§2.2） |

## 10. 工程自決報備彙整

- TrustModel 設定源沿 rev4 TOML 全套（含 `TRUSTED_PROXY_CIDRS` 退路與三層失敗語意；
  dev 不設檔）。
- `nginx_peer` 字面退役、七態表取代（免 migration）；`peer_ip` 欄開始填。
- 解鎖端點 API-only、UI 鈕待 user 管理刀（已知態）；unlock wrapper 不建（YAGNI）。
- 部署 checklist 落 RUNBOOK 新節；v-html 機器守落 tools/ lint 家族（plan 定、附 self-test）。
- wire 裁判面重評結論：`additionalProperties` 維持已知態、落帳更新警示句、不動機器。
- `clamp_source_ip` 行為不變、註解對齊；阻擋碼 reuse `5003`、自鎖碼 reuse `2222`（13 碼
  矩陣零觸碰）。

## 11. 下一步

**手動** `/speckit-specify`（本檔為 input）→ spec 落 `specs/004-ip-trust-anchor/`；
`/speckit-plan` 之 research 必列「rev4 對應碼清單＋rev5 拍板差異點」（ADR 0019）；
Workflow 模型分派依當下 user 指示、不預載。
