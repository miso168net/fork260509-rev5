# Research — 004-ip-trust-anchor

> Phase 0 產出。**R1／R2 即 ADR 0019 要求的兩張表**（rev4 對應碼清單＋rev5 拍板差異點）。
> 全篇 rev4 引用皆為**唯讀勘查**（`../fork260509-rev4/`，該樹絕不寫入）。

## R1 rev4 對應碼清單（ADR 0019 要求①；實作單元動工前逐檔先讀）

| # | rev4 檔／符號 | 行數 | rev5 落點 | 消費單元 |
|---|---|---|---|---|
| 1 | `trust/mod.rs`：`TrustModel`／`TunnelConfig`／`CdnEntry`／`MyPublicEntry`／`Binding` | 22–89 | `trust/mod.rs`（新） | U1 |
| 2 | `trust/mod.rs`：`TrustModel::is_trusted`／`cdn_entry`／`my_public_entry`（★單一 helper） | 90–113 | 同上 | U1 |
| 3 | `trust/mod.rs`：`Confidence` 七態＋`as_str` | 115–148 | 同上 | U1 |
| 4 | `trust/mod.rs`：`SoftReason` 二態／`Evidence` 五變體 | 150–172 | 同上 | U1 |
| 5 | `trust/mod.rs`：`resolve_client_ip` 三層 | 187–245 | 同上（★加硬化，見 R2-1） | U1 |
| 6 | `trust/mod.rs`：`apply_tunnel_fallback` | 252–271 | 同上 | U1 |
| 7 | `trust/mod.rs`：`apply_cf_overlay`（四前置） | 274–299 | 同上 | U1 |
| 8 | `trust/mod.rs`：`normalize_xff`／`parse_xff_token`／`strip_zone_and_parse` | 302–350 | 同上 | U1 |
| 9 | `config.rs`：`load_trust_model`＋`RawTrustModel`＋flat env 退路 | 166–331 | `config.rs`（擴充） | U1 |
| 10 | `ipgate/mod.rs`：`RuleSet`／`Verdict`／`Decision`／`STRUCTURAL_EXEMPT` 六段 | 13–62 | `ipgate/mod.rs`（新） | U2 |
| 11 | `ipgate/mod.rs`：`decide` 判定序 | 63–82 | 同上 | U2 |
| 12 | `ipgate/mod.rs`：`would_self_lock` | 84–96 | 同上 | U2／U5 |
| 13 | `ipgate/mod.rs`：`build_ruleset`（未知型 skip）／`try_load_ruleset`／`load_ruleset` | 98–137 | 同上 | U2 |
| 14 | `ipgate/mod.rs`：`IPGATE_INVALIDATE_CHANNEL`＋`reload_and_publish`（keep-last-good） | 139–193 | 同上 | U3 |
| 15 | `ipgate/mod.rs`：`spawn_ipgate_watcher`＋`subscribe_ipgate`＋`reread_keeping_last_good` | 190–315 | 同上 | U3 |
| 16 | `middleware/mod.rs`：`RequestContext`（extensions 形）＋`request_context_mw`＋`build_request_context` | 56–168／388–436 | `middleware/mod.rs`（新）＋`request_context.rs`（改） | U4 |
| 17 | `middleware/mod.rs`：`ip_gate_mw`（六步短路） | 184–260 | `middleware/mod.rs` | U4 |
| 18 | `middleware/mod.rs`：`CF_VERIFIED_HEADER` 常數 | 28–30 | 同上 | U4 |
| 19 | `throttle/mod.rs`：`DIM_IP`／`ip_bucket`（v4 /32・v6 /64・mapped 折疊・unspecified→None） | 197–228 | `throttle/mod.rs`（擴充） | U6 |
| 20 | `throttle/mod.rs`：`parse_unlock_marker`（unix 秒十進位字串契約） | 246–252 | 同上 | U6／U7 |
| 21 | `throttle/mod.rs`：`precheck` 之 ⓪L0 allow 短路＋IP 維並列判定＋合成 | 300–520 | 同上 | U6 |
| 22 | `model/facade/sys_login_attempt.rs`：`count_recent_failures_by_ip`（`real_ip <<= $1::inet`＋GREATEST 兩源） | 177–213 | rev5 同名 facade（擴充） | U6 |
| 23 | `handler/ip_rule.rs`：`IpRuleListQuery`／`IpRuleRecord`／三個 Req DTO＋五支 handler | 40–107／260–461 | `handler/ip_rule.rs`（新） | U5 |
| 24 | `handler/ip_rule.rs`：`validate_wbip_type`／`normalize_cidr`／`map_mutate_err`／`guard_self_lock` | 115–258 | 同上 | U5 |
| 25 | `handler/throttle.rs`：`unlock_login`＋`resolve_unlock_target`（★稽核先於生效） | 80–196 | `handler/throttle.rs`（新） | U7 |
| 26 | `model/facade/sys_ip_rule.rs`：`load_active`／`list`／`IpRuleWrite`／`IpRuleMutateError`／軟刪復原 | 全檔 762 行 | `model/facade/sys_ip_rule.rs`（新） | U5 |
| 27 | `model/facade/sys_operation_log.rs`＋`model/audit.rs`：`AuditEvent`／`AuditOperation`／`AuditOperator` | — | `model/facade/sys_operation_log.rs`（新）＋`model/audit.rs`（新） | U5 |
| 28 | `base-web/src/views/manage/ip-rule/{index.vue,modules/ip-rule-operate-drawer.vue,modules/ip-rule-search.vue}` | 三檔 | 同路徑（新增型） | U8 |
| 29 | `base-web/src/typings/api/*`：`Api.IpRule` 節 | — | `typings/api/rev5-ip-rule.d.ts`（新、ADAPT 軌） | U8 |
| 30 | `deploy/nginx/nginx.conf`：`geo $cf_edge`／兩 map（**rev5 已完整具備、零改動**） | 41–61 | 不動 | — |

**總量**：rev4 側約 3,600 生產行（trust 718＋ipgate 611＋ip_rule handler 1,550＋facade 762）
＋middleware／throttle／config 的局部段。★全數依 §I.5＋ADR 0019 重打字消化、註解一律 rev5
語境重寫（rev4 出處帶 `rev4:` 前綴）。

## R2 rev5 拍板差異點清單（ADR 0019 要求②；★防回歸：以下 rev4 行為一律不得帶回）

| # | rev4 行為 | rev5 拍板 | 依據 |
|---|---|---|---|
| 1 | Tier-1 錨**盲剝**錨右側（`chain[..anchor_idx]` 只看左側、右側不論內容一律丟棄） | ★錨右側**全部**須屬受信基建集，否則**錨不成立、退 Tier-2** | spec FR-005（brainstorm 題二拍板）；rev4:B-080 硬化案兌現 |
| 2 | 安全保證壓在「部署方 MUST 鎖 origin 僅接受 CDN 邊緣連線」之**承重部署前提** | 降級為**縱深防禦建議**（硬化已入碼） | 同上；spec FR-043 |
| 3 | dev 無任何信任模型設定（compose／`.env`／腳本全查無）⇒ 對端閘恆先觸發、其驗收手冊第 3 節的「構造 XFF 四步走查」**跑不出宣稱結果** | dev **必掛**最小信任模型（僅容器網段入內網預設集） | spec FR-010 後段（Clarify Q1） |
| 4 | 信心字面單一來源＝`Confidence::as_str` 七態 | 同（★rev5 前一刀的 `nginx_peer` 字面**退役**、由七態表取代） | spec FR-007；三張稽核表 `ip_confidence` 無 CHECK ⇒ 零 migration |
| 5 | `region` 欄由 GeoIP（xdb crate 整檔拷貝例外）填值 | **整包不搬**、該欄恆空 | ADR 0014 第 2 款；spec §Out of Scope |
| 6 | 設定源模組名 `crate::redis` | rev5 為 `crate::cache`（前一刀已改名） | rev5 as-built |
| 7 | `sys_operation_log` 的寫入者遍佈各域（含 settings 寫端同 txn 審計鏈） | 本刀**只為新端點**落列；**既有 settings 寫端維持不落列**、不回改 | spec FR-032；002 之 FR-016 刻意決定 |
| 8 | 觀測層 HLL 廣度估計兩支（`hll_observe`／`throttle_hll_key`） | **不搬**（前一刀已判 rev4 HLL 兩支不做、序列面只取真有發射點者） | 003 Clarify 定案之延續 |
| 9 | `access_log_mw`（存取軌跡 middleware） | **不搬**（B-016 稽核域射程） | spec §Out of Scope |
| 10 | 錯誤碼／訊息鍵散在各 handler 自訂 | 復用既有 `2222`／`5003`；**零新 AppError 變體**（`PermissionDenied` 已存在、key＝`system.forbidden`） | spec FR-018／FR-023；§I.3 13 碼矩陣凍結 |
| 11 | rev4 驗收手冊自稱 dev「信心恆 fallback」，與其「dev 無設定」敘述**互相矛盾**（全空設定應得 `direct`） | rev5 以 R7 表明列**dev 實際可達態**，不留矛盾敘述 | 本檔 R7 |

## R3 依賴釘版與三源核對（CLAUDE.md §6；★crates.io 本輪可達，非沿用「第二源不可達」先例）

| crate | 釘版 | rev4 釘版 | rev5 `Cargo.lock` 現值 | crates.io latest stable | 處置 |
|---|---|---|---|---|---|
| `arc-swap` | **1.9.2** | 1.9.2 | 1.9.2（transitive） | 1.9.2 | ★三源一致 → 採用、報備（零 lock 圖變動、僅由間接轉直接） |
| `futures-util` | **0.3.34** | 0.3.32 | 0.3.33（transitive） | 0.3.34 | 三源分歧 → **user 拍板取 latest stable**；連帶把 lock 內 0.3.33 推升至 0.3.34（影響所有間接消費者、屬本刀順帶的依賴變動，已揭露） |
| `toml` | **1.1.4** | 1.1.2 | 不在 lock | 1.1.4（完整字串 `1.1.4+spec-1.1.0`，`+` 後為建置註記、Cargo 不參與比對） | 分歧 → **user 拍板取 latest stable**（全新 lock 條目、無「沿現值零變動」可講；與 rev4 同為 1.1.x） |

- 三支皆進 `[workspace.dependencies]`＋`server/Cargo.toml`（沿既有兩層釘版形制）。
- **零新 redis feature flag**：`redis` 的 pub/sub 訂閱在既有 `connection-manager`＋
  `tokio-comp` 下即可用（rev4 同組合）。三支新依賴的 features 亦沿 rev4 形：`arc-swap`／
  `toml` 取 default；★`futures-util` 取 `default-features = false`——default 的
  `async-await-macro` 會多拉一條 `futures-macro` lock 條目，而本刀唯一使用點
  `StreamExt::next()`（見下一條）用不到它。
- `futures-util` 的**唯一**使用點＝門鈴 watcher 的 `StreamExt::next()`（一行）。已評估「手寫
  `poll_fn`＋`Pin::new(..).poll_next(cx)` 以省依賴」並棄——該段位於規則熱重載路徑，寫錯的
  後果是「規則改了不生效且不易審出」，不值得為省一支已在 lock 圖內的 crate 換十行難審樣板。
- `ipnetwork` 0.20.0 **已在 lock**（`sea-orm` 帶進），經 `sea_orm::prelude::IpNetwork` 取用
  ⇒ 不列直接依賴（沿 rev4 形）。

## R4 信任錨判定矩陣（七態 × 三層 × 兩覆蓋 × 硬化）

**鏈的組成**：`chain = normalize(xff) ++ [peer]`——傳輸層對端接在**最右**（＝最可信一跳）。
反向代理以 `$proxy_add_x_forwarded_for` 附加其觀察到的對端，故鏈右端恆為我方基建。

| 層／覆蓋 | 條件 | 產出位址 | 信心 | Evidence |
|---|---|---|---|---|
| ①對端閘 | `peer ∉ is_trusted` | peer | `direct` | `PeerGate` |
| ②Tier-1 錨 | 鏈中有 CDN 段 ∧ **錨右側全受信**（★硬化）∧ 錨左有非 CDN 段 | 錨左鄰第一個非 CDN | `cdn_anchored` | `CdnAnchor{anchor}` |
| ②→回退 | 有 CDN 段 ∧ 錨右側全受信 ∧ 錨左**無**非 CDN 段 | peer | `fallback` | `AllTrustedFallback` |
| ②→★退層③ | 有 CDN 段 ∧ **錨右側含不受信跳** | 交層③ | 交層③ | 交層③ |
| ③Tier-2 | 由右往左跳過受信集，第一個不屬者 | 該跳 | 無 soft→`proxy_clean`／有→`proxy_soft` | `RightmostUntrusted{skipped,soft}` |
| ③→回退 | 整鏈皆受信 | peer | `fallback` | `AllTrustedFallback` |
| 覆蓋 A 通道 | 基礎＝`fallback` ∧ `peer ∈ tunnel.networks` ∧ 通道訪客標頭有值 | 訪客位址 | **維持 `fallback`**（不升） | `TunnelVisitor` |
| 覆蓋 B CF | 四前置全中（`peer ∈ cf_gate_egress` ∧ 驗證標記真 ∧ 訪客標頭有值 ∧ 基礎信心∈{`cdn_anchored`,`proxy_clean`,`proxy_soft`}） | **不動位址** | 訪客＝推導值→`cdn_verified`；不等→`cdn_mismatch` | 不動 |

**`proxy_soft` 兩觸發**：①walk 經過 `dual_role=true` 的我方公開出口 ②公開出口宣告了專屬後置
內網、而其鏈中右鄰不屬該內網集。

**★硬化的形式化**：`chain[anchor_idx+1..].iter().all(|hop| tm.is_trusted(hop))`。
- 合法 CDN 路徑：`chain = [client, cf_edge, nginx]`、錨在 idx 1、右側＝`[nginx]`（受信）⇒ **通過**，
  結論與硬化前**逐位元相同** ⇒ 零誤傷（SC-002 後半）。
- 偽造路徑（繞 CDN 直連來源站）：攻擊者送 `XFF: 8.8.8.8, <CDN 邊緣>`，反向代理附加攻擊者位址
  ⇒ `chain = [8.8.8.8, cdn_edge, attacker, nginx]`、錨在 idx 1、右側含 `attacker`（不受信）
  ⇒ **錨不成立**、退層③ → 右往左：nginx 跳過、`attacker` 不受信 ⇒ **real_ip＝attacker**、
  信心 `proxy_clean`。偽造的 `8.8.8.8` 永遠走不到。
  ★**信心是 `proxy_clean` 而非 `direct`**——spec 原措辭已於本輪校正（見 R9-3）。
- `peer` 恆屬受信集（否則層①早已短路），故硬化實質只檢查「錨右側的轉發鏈段」。

## R5 ipgate 機制與門鈴

- **判定面**：`Arc<ArcSwap<RuleSet>>`、`.load()` lock-free、每請求零資料庫零快取查詢。
- **`decide` 判定序**（純函式、單一權威）：③結構豁免六段（`127.0.0.0/8`／`::1/128`／
  `10.0.0.0/8`／`172.16.0.0/12`／`192.168.0.0/16`／`fc00::/7`）→④allow any-match →
  ⑤deny any-match →⑥default-allow。①健康／觀測放行與②上下文缺席放行屬 middleware 前置。
- **`would_self_lock`** ＝ `decide(rs_after, client_ip).verdict == Deny`（★與請求判定同源、
  零內聯重複）。語意推論：allow 規則永不自鎖；★**結構豁免段不算自鎖**（`decide` 對其回 Allow）
  ——此即 spec Edge Cases 所問的行為，答案由 `decide` 同源性直接導出、無須另立規則。
- **未知 `wbip_type` 列**：skip＋告警，不使整份載入失敗。
- **門鈴**：頻道 `ipgate:invalidate`；寫端 `reload_and_publish`（re-read 成功才 store＋PUBLISH；
  reload 失敗→keep-last-good＋回 `Err` 由呼叫端退避；PUBLISH 失敗／Redis 缺席→告警但回 `Ok`，
  單副本 in-process 已生效）。
- **watcher**：★**專用 pub/sub 連線**——`SessionCache` 是多工 `ConnectionManager`、**不可**用於
  SUBSCRIBE，須由 `config::redis_url()` 另開 `redis::Client`（rev5 已有該 getter，零新設定鍵）。
  韌性：`get_async_pubsub` 帶 **5 秒 timeout**（無 timeout 時 SYN 黑洞會使 watcher 永久 hang
  而不 backoff）、斷線 backoff 1s 指數上限 30s、訂閱成功重置；★**reconnect（含首次訂閱成功）
  後補一次 re-read**——否則 backoff 窗內錯過的門鈴永不收斂。

## R6 來源維節流的擴維落點

- **鍵粒度** `ip_bucket`：`to_canonical()` 折 IPv4-mapped → v4 出 `a.b.c.d/32`、v6 出
  `xxxx::/64`（`.network()` 截斷主機位元）；★`unspecified`（`0.0.0.0`／`::`）→ `None`＝
  IP 維整層跳過（與上下文缺席 fail-open 同源），不對 sentinel 建桶。
- **L2 計數 SQL**：`WHERE real_ip <<= $1::inet AND success = false AND created_at > GREATEST(
  now() - make_interval(mins => $2::int), $3)`——`<<=`（含於或等於）使 /32 與 /64 兩種粒度
  自然對 `inet` 欄生效；★**GREATEST 恰兩源**（窗起點＋解鎖標記），帳號維的第三源
  「窗內最近成功登入」**蓄意拔除**、MUST NOT 加回。
- **解鎖標記值格式契約**＝**unix 秒的十進位字串**；不可解析→視為無標記（良性方向：至多少
  解鎖、不誤放行）。解鎖端點（U7）寫端須照此格式。
- **L0 allow 短路**（★易錯點）：判斷是否跳過 IP 維節流時 MUST **直讀 allow 袋**
  （`IpNetwork::contains`），**絕不經 `decide`**——`decide` 對結構豁免六段亦回 Allow，經其判定
  會使「未登記 allow 的私網來源」誤跳節流，違反 F5（結構豁免只豁免阻擋、不豁免節流）。
  短路時桶置 `None`（L1／L2／軟區全跳、不讀不寫任何 IP 維快取鍵）；帳號維照常獨立並列。
- **rev5 現況銜接**：`throttle::precheck` 現簽名為
  `(conn, cache, captcha_secret, user_name, captcha_id, captcha_code)`，本刀加
  `real_ip: IpAddr`＋`ip_allow: &[IpNetwork]` 兩參（rev4 同形）。
- **L-026 順帶修**：三處上下界的具名餘裕常數（現註解與碼不符）於本單元一併對齊。

## R7 dev 可達信心態（★誠實分界；quickstart 與 SC-013 的前提）

dev 掛最小信任模型（**僅**容器網段入 `internal_default`、其餘集合留空）後：

| 態 | dev 經反向代理可達？ | 達法／不可達原因 |
|---|---|---|
| `fallback` | ✅（**預設瀏覽行為**） | 瀏覽器不帶轉發標頭 ⇒ 鏈兩跳皆受信 ⇒ 整鏈受信回退；real_ip＝反向代理位址 |
| `proxy_clean` | ✅（**構造標頭**） | 帶 `X-Forwarded-For: 203.0.113.x` ⇒ 層③解出該公網位址 |
| `proxy_soft` | ❌ | 需宣告 `my_public`（`dual_role`）或 `bindings`——dev 設定留空 |
| `cdn_anchored` | ❌ | 需宣告 `cdn` 網段——dev 設定留空 |
| `cdn_verified`／`cdn_mismatch` | ❌ | 另需 `cf_gate_egress` 宣告＋`X-CF-Verified` 標頭，而 dev 的 `geo $cf_edge` 恆 0 ⇒ 反向代理**主動移除**該標頭（client 自帶不倖存） |
| `direct` | ❌ | 需對端 ∉ 受信集，而容器網段已入受信集 |

⇒ **經反向代理的端到端走查可達二態**（`fallback`／`proxy_clean`）；其餘五態由整合測試以
「直餵 TrustModel＋任意 peer／標頭」覆蓋（純函式與直打後端埠皆可注）。SC-001 的「七態逐態
至少一案」落在整合層、SC-013 的四項落在端到端層——兩者射程不同，tasks 不得混寫。

★**這正是 dev 掛設定的價值**：不掛設定時 `proxy_clean` 亦不可達（層①恆短路），阻擋／計數
隔離／防自鎖三項端到端全滅（R2-3）。

## R8 測試設施與機器閘衝擊（tasks 的硬前置）

| 面 | 衝擊 | 處置 |
|---|---|---|
| `schema-gate` gate2 | IP 規則 CRUD 與解鎖落 `sys_operation_log` ⇒ 走查後該表有列、seed 側 0 列 ⇒ 紅 | 常數加一行納入 runtime-append 收窄集（spec FR-042）。★`sys_ip_rule` **不**納入 |
| `schema-gate` gate2（`sys_ip_rule`） | 走查建立的規則列使該表有列 ⇒ 紅 | **刻意不收窄**（變體 A 業務表、列內容即真 seed 面）；走查後以 quickstart 收尾清理 |
| contract 覆蓋閘 | 每條 route 必有 case ⇒ 新增 6 條即需 6 個 case | tasks 顯式列；`case_key` 沿 rev4 命名（`get-ip-rule-list` 等） |
| `wire_schema` 裁判面 | 新 DTO 須入快照（`TYPINGS_GLOB` 掃 api 目錄）⇒ 靠新檔 `rev5-ip-rule.d.ts` 入面 | 同 003 之 `rev5-auth.d.ts` 先例 |
| `authz_entrypoint_lint` | `ALLOWED_DECISION_FILES = ["auth/enforce.rs"]`——★`ipgate::decide` 與 `would_self_lock` 是**授權判定以外**的判定（IP 閘非 casbin），須確認該 lint 的偵測面是否誤攔 | plan→tasks 第一步實測；若誤攔則擴 must-list 並在該 lint 內記明兩者語意分工 |
| `entity_access_lint` | handler 零 path-root `entity::`、資料存取全走 facade | 沿既有紀律（rev4 同形，其 `handler/ip_rule.rs` 檔頭已自述） |
| `docs-sync` Lint24（msg key 跨端契約） | 新增 `biz.ipRule.*` 等後端實發鍵 ⇒ 三處鍵集須同步（兩語 locale 之 `backend:` 樹＋治理錨點檔 `zh-tw.ts`） | spec FR-023；★`zh-tw.ts` 只放後端訊息鍵、**不**放路由／頁面鍵 |
| `fork-delta-lint` | ★名冊斷言（`find_rogue_tracks`）**只掃帶 `原行:` 的修改型標記**〔憲法 §III.2 表外宣告 3〕；本軌道三塊皆新增型（兩語 locale `route:`／`page:` 樹、`app.d.ts` 型節——後者沿 v1.3.1 之 I18N-WIRING (iii)「新增型圈界」先例）或生成檔（`is_generated` 於 `scan()` 全域豁免）⇒ 名冊斷言對本軌道**結構性不適用**、不可當驗收 | spec FR-041／SC-011；實得機器守＝`find_unmarked_additions` 的「圈界標記須存在」（不比對軌道名與用途）＋T042② 冪等檢查；該列「真被載入」以 `load_roster` 表列形守變異證（落 T002）。★`s2_rows < 4` 只是表錨／列形 tripwire、非名冊斷言本體——現表 8 列、Amendment 後 9 列，門檻推到 5 仍偵測不到刪一列，故**不採**該路徑 |
| 新增機器守（本刀自建） | ①管理頁零 `v-html`／`innerHTML` ②路由產物**四檔**（`router/elegant/{imports,routes,transform}.ts`＋`typings/elegant-router.d.ts`）**重算冪等**＋「憲法該列生成檔集＝實產出檔集」斷言 | 兩者皆須附 self-test（植入反例必紅、ADR 0024） |
| `reference/routes` 真表 | `ROUTES` 16→22 ⇒ `docs-sync generate` 重算 | 收刀簿記既有步驟 |

## R9 本輪查證對既有文件的三筆校正

1. **spec FR-002 之「零 seed 變更」經逐列複核成立**：001 凍結 seed 第 143–148 列（五支 IP 規則
   端點＋`unlockLogin`）、149 列（`manage_ip-rule` menu 維）、157 列（`user:unlock`）、
   160–163 列（四顆 `ipRule:*`）、選單列 78 全在。⇒ 校正 brainstorm §5.2／§7.4 的
   「unlock 政策列＝seed 演進一筆」（不成立）。
2. **零新 `AppError` 變體**：`PermissionDenied`（`5003`／`system.forbidden`）與
   `Biz(Cow)`（`2222`）已足夠承載阻擋與四類規則錯誤 ⇒ 13 碼矩陣零觸碰（spec FR-045 成立）。
3. **spec US1 場景 3 與 SC-002 的技術措辭已於本輪校正**：硬化生效後攻擊路徑的結論是
   「退 Tier-2 解出攻擊者位址、信心 `proxy_clean`」，原文誤寫為「退化為傳輸層對端位址／直連」
   ——傳輸層對端從後端視角看是反向代理，攻擊者位址是**反向代理附加進轉發鏈**的那一段。
   位址結論不變（偽造失敗），但信心態與取得路徑不同，攸關測試怎麼斷言。

## R10 執行單元切分（tasks 的 phase 骨架建議）

| 單元 | 內容 | 相依 |
|---|---|---|
| **U0** | 憲法 Amendment（島 F＋★軌道＋B-071 PATCH）＋AppState 擴欄 ADR｜★**硬閘**：未 accepted 前不得動任何 base-web 既有檔 | — |
| U1 | `trust/` 純函式全形＋硬化＋`config::load_trust_model`＋dev 設定檔與 compose 掛載 | U0（僅 ADR 面） |
| U2 | `ipgate/` 規則集＋`decide`＋結構豁免＋`would_self_lock`＋facade `load_active` | U1 |
| U3 | 門鈴（`reload_and_publish`＋watcher＋專用連線）＋AppState 兩欄接線 | U2 |
| U4 | middleware 兩支＋`RequestContext` seam 換血＋`peer_ip` 落欄 | U1／U3 |
| U5 | ip-rule 五支端點＋facade＋防自鎖＋操作稽核首寫＋gate2 常數 | U2／U4 |
| U6 | per-IP 節流擴維＋GREATEST 兩源負向自證＋L0 allow 短路＋L-026 | U4 |
| U7 | 解鎖端點＋兩維 marker＋帳號維三件＋稽核先於生效 | U6 |
| U8 | 前端三檔＋typings／wrapper＋i18n 三樹＋按鈕碼＋v-html 機器守＋路由產物冪等檢查 | U0（Amendment accepted）／U5 |
| U9 | 部署 checklist＋已知態 ADR 群＋帳面處置 | 全部 |

★U8 對 U0 的相依是**硬序**（憲法授權在前、動 base-web 既有檔在後）；U1～U7 為純後端、
不受該閘阻擋，可先行。
