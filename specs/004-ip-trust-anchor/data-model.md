# Data Model — 004-ip-trust-anchor

> Phase 1 產出。★**本刀零 migration、零 seed 變更**（research R9-1 逐列複核）——本檔描述的是
> **既有結構的消費形**與**非資料庫的記憶體／設定實體**，不含任何 DDL。

## §1 既有資料表的消費面（零結構變更）

### 1.1 `sys_ip_rule`（archetype A 業務全六欄；seed 0 列、本刀首個寫入者）

| 欄 | 型 | 本刀消費 |
|---|---|---|
| `id` | bigint PK | wire 上為 **number**（沿 §I.3 預設＋2^53 守衛） |
| `wbip_cidr` | inet NN | ★寫入前**正規化主機位元**（`203.0.113.7/24`→`203.0.113.0/24`）；讀端以 `IpNetwork::to_string` 上 wire |
| `wbip_type` | varchar NN | 二值封閉 `allow`／`deny`；★讀端對未知值 **skip＋告警**（容忍、不使整份載入失敗） |
| `wbip_memo` | text 可空 | B-003 語意：僅管理列表顯示、對外取用處不帶 |
| `order` | int 可空 | 上 wire、**不參與判定**（規則集為 any-match，無優先序語意） |
| 六審計欄 | — | `created_at`／`created_by`／`updated_at`／`updated_by` 上 wire（操作者以帳號名 enrich、查無→null）；★`deleted_at`／`deleted_by` **不上 wire**，以導出布林 `deleted` 表達回收桶 |

**唯一性**：既有 partial unique `(wbip_cidr, wbip_type) WHERE deleted_at IS NULL`。
⇒ 軟刪後同組合可重建；重複寫入映**業務錯誤**（★MUST NOT 伺服器錯誤）。

**狀態機**（變體 A 軟刪二態）：

| 現態 | 事件 | 次態 | 副作用 |
|---|---|---|---|
| （無） | add | active | 防自鎖檢查 → 落庫 → 操作稽核 → reload＋門鈴 |
| active | update | active | 同上（防自鎖以「變更後規則集」判） |
| active | delete | deleted | 同上（`deleted_at`／`deleted_by` **成對**寫） |
| deleted | restore | active | 同上（`deleted_at`／`deleted_by` 成對清空） |
| deleted | delete | — | 業務錯誤（狀態不符） |
| active | restore | — | 業務錯誤（狀態不符） |

### 1.2 三張稽核表的來源三欄（`ip_confidence` 值域擴張、零 DDL）

| 表 | `peer_ip` | `real_ip` | `ip_confidence` |
|---|---|---|---|
| `sys_login_attempt` | inet 可空｜★**本刀開始填**（此前恆 NULL） | inet NN｜內容改由信任錨推導 | text 可空、**無 CHECK**｜單字面 → **七態** |
| `sys_access_log` | 同上（本刀不寫該表，B-016 域外） | 同上 | 同上 |
| `sys_operation_log` | 本刀新寫入者，見 §1.3 | 同上 | 同上 |

★**既有列不遷移**：憲法 §I.6 變體 B 明定 append-only 表「無 update、不可竄改」⇒ 前一刀寫入的
`nginx_peer` 列**原樣保留為歷史事實**；查詢端須容忍新舊字面並存。

### 1.3 `sys_operation_log`（archetype B append-only；★rev5 首個寫入者）

本刀寫入時機恰五處：IP 規則 add／update／delete／restore＋解鎖。欄值語意：

| 欄 | 值 |
|---|---|
| `operation` | 規則四寫端＝對應動作字面；解鎖＝`unlock` |
| `entity_table` | 規則＝`sys_ip_rule`；解鎖＝`login_throttle`（★非真表名、表示節流子系統） |
| `entity_id` | 規則＝該列 id；解鎖＝`NULL` |
| `payload_before`／`payload_after` | 規則＝變更前後值；解鎖＝`{dimension, userName, target}`（維度為來源時 `target`＝計數桶字面，否則 null） |
| operator 類欄 | 操作者 uid＋來源三欄 |

**落列與生效的次序**（★兩種路徑刻意不同）：

| 路徑 | 次序 | 理由 |
|---|---|---|
| 規則四寫端（純資料庫） | **同一交易**內落列＋改列 | 交易保證原子，無須額外排序 |
| 解鎖（跨資料庫與快取） | ★**先落稽核列、後動快取** | 快取不參與交易；先寫稽核才使「已生效但零稽核列」**構造上不可達**。稽核寫入失敗→中止、快取一概不動 |

### 1.4 `system_settings` 之 `ip_*` 三鍵（零 seed 變更、僅獲得消費者）

| 鍵 | seed 值 | 本刀消費點 |
|---|---|---|
| `ip_captcha_after` | 10 | 來源維軟門檻 |
| `ip_max_fails` | 50 | 來源維硬門檻 |
| `ip_window_minutes` | 15 | 來源維滑動窗長 |

⇒ 既有「有值、可改、但零行為變化」之已知態自此**解除**。

## §2 記憶體與設定實體（非資料庫）

### 2.1 `TrustModel`（啟動時一次載入、唯讀共享）

| 集合 | 語意 |
|---|---|
| `internal_default` | 內網預設受信集（★dev 設定唯一填的一項＝容器網段） |
| `tunnel{networks, connecting_ip_header}` | 通道來源集與其訪客位址標頭名 |
| `cf_gate_egress` | 掛邊緣驗證閘的我方出口集（覆蓋 B 的前置） |
| `cdn[]{networks, connecting_ip_header}` | CDN 段（Tier-1 位置錨判定面） |
| `my_public[]{networks, dual_role}` | 我方公開出口（`proxy_soft` 觸發①） |
| `bindings[]{public, internal}` | 公開出口×專屬後置內網（`proxy_soft` 觸發②） |

★**單一 helper 導出兩集合**：受信集（層①）與跳過集（層③）＝
`internal_default ∪ tunnel ∪ cf_gate_egress ∪ cdn ∪ my_public ∪ Σbindings.internal`。
兩者**必須同源對稱**——分叉即前代缺陷復發（walk 停在通道 origin 自身、真實來源塌縮為常數）。

**預設**：全空＝全直連（無隱含寬鬆預設）。**載入失敗三層語意**見 spec FR-010。

### 2.2 `RuleSet`（判定面）

`{allow: Vec<IpNetwork>, deny: Vec<IpNetwork>}`；以 `Arc<ArcSwap<RuleSet>>` 存狀態容器、
每請求 `.load()` lock-free、零外部查詢。`Default`＝兩袋皆空（＝全放行）。

**結構性豁免六段**（判定序③、先於兩袋、不可被規則覆蓋）：
`127.0.0.0/8`／`::1/128`／`10.0.0.0/8`／`172.16.0.0/12`／`192.168.0.0/16`／`fc00::/7`。
★只豁免「阻擋」，**不**豁免來源維節流。

### 2.3 `RequestContext`（每請求一次、經 extensions 傳遞）

| 欄 | 本刀後的內容 |
|---|---|
| `real_ip` | 信任錨推導結果之**正規化**字串（此前＝標頭原文） |
| `x_forwarded_for` | 原樣淨化轉錄（零 CR/LF、長度上限）——**不變** |
| `ip_confidence` | 七態字面（此前＝單一字面） |
| `peer_ip`（新增消費） | 傳輸層對端 |

★三欄私有＋取值器簽名不變、編譯期守門（欄位私有之 `compile_fail` doctest）續存。

### 2.4 信心等級（七態，DB／wire 穩定小寫底線字面）

`cdn_verified`／`proxy_clean`／`direct`／`cdn_anchored`／`proxy_soft`／`cdn_mismatch`／
`fallback`。判定矩陣＝research R4；**dev 經反向代理可達二態**＝research R7。

### 2.5 節流鍵與解鎖標記

| 項 | 形 |
|---|---|
| 計數桶身分 | v4 `a.b.c.d/32`；v6 `xxxx::/64`（截斷主機位元）；IPv4-mapped 先折 v4；`unspecified`→**無桶**（該維整層跳過） |
| 快取鍵維度 | 帳號維／來源維並列，鍵形沿既有 `{kind}:{dim}:{value}` |
| 解鎖標記值 | ★**unix 秒的十進位字串**（格式契約；不可解析→視為無標記＝良性方向） |
| 計數下界 | ★**恰兩源**：窗起點＋解鎖標記（`GREATEST` 非 strict，無標記綁 SQL NULL 自然退化為單源；**MUST NOT** 用哨兵值） |

## §3 判定資料流（單一方向、無回環）

```
傳輸層對端 ──┐
             ├─→ trust::resolve_client_ip（純函式）─→ (位址, 信心, 依據)
轉發鏈標頭 ──┘                                              │
CF 兩標頭 ───────→ 兩覆蓋層（只動信心／通道改位址）────────┘
                                    │
                    RequestContext（extensions 注入，每請求一次）
                                    │
        ┌───────────────┬───────────┴───────────┬──────────────┐
        ▼               ▼                       ▼              ▼
   ip_gate_mw      來源維節流              稽核落列        防自鎖檢查
  （decide）    （ip_bucket＋L0 allow）  （三欄如實）  （decide 同源）
```

★**同源約束**：`ip_gate_mw` 與防自鎖消費**同一個** `decide`；來源維節流的 L0 短路
**直讀 allow 袋**而非 `decide`（否則結構豁免段會誤跳節流、違 F5）。

## §4 不變式清單（隨憲法島 F 入憲；反轉＝MAJOR）

| # | 不變式 |
|---|---|
| F1 | 判定序六步固定；規則集 any-match、白＞黑＞預設放行、無優先序欄 |
| F2 | 資料庫為真相、記憶體判定面每請求零外部查詢；真相暫不可讀→**沿用上一份已知良好規則集**、不清空 |
| F3 | 全鏈 fail-open；**唯一 fail-closed＝寫端自鎖拒寫**；每次降級必發結構化告警 |
| F4 | 來源維度一切機制的位址輸入 MUST 為信任錨結果；受信集與跳過集 MUST 同源對稱 |
| F5 | 命中**顯式**放行規則者跳過來源維節流；**結構豁免段 MUST NOT 跳** |
| **F6（本刀新增）** | **Tier-1 位置錨 MUST 附傳輸層背書**——錨右鄰起直到傳輸層對端全屬受信基建，否則錨不成立、退 Tier-2 |

**既有島 E 補充釐清**（已入憲 invariant 細項調整）：帳號維計數下界取三源（含成功即重置）、
**來源維恆兩源且禁成功即重置**——刻意不對稱，防日後被「統一」。

## §5 降級矩陣

| 降級源 | 方向 | 行為 | 觀測 |
|---|---|---|---|
| 信任模型設定檔缺席 | — | 沿用扁平環境變數退路 | 告警 |
| 信任模型整體損壞 | 縮小信任 | 全空＝全直連（★**不**套退路） | 告警 |
| 單一集合含無效網段 | 縮小信任 | 只清空該集合 | 告警 |
| 規則集啟動初載失敗 | fail-open | 空集＝全放行 | 告警 |
| 規則集執行中重載失敗 | fail-open | **keep-last-good**、回錯由呼叫端退避 | 告警 |
| 門鈴 PUBLISH 失敗／通知層缺席 | fail-open | 本機已生效、跨副本待 watcher 補讀 | 告警 |
| watcher 訂閱失敗／斷線 | fail-open | backoff 重連（1s→30s 上限）＋**重連後補一次重讀** | 告警 |
| 快取整體不可用 | fail-open | 沿既有帳號維方向（軟區要求整層停用、密碼錯仍計數） | 既有訊號 |
| 來源節流三鍵設定讀取失敗 | fail-open | 退預設常數（整批失敗→全退；單鍵缺值／不可解析→**該鍵**退，其餘不受波及）；每次載入至多一筆告警 | 告警（★獨立 label、與帳號維同名字面分流） |
| 解鎖標記讀取故障 | **fail-closed** | 視為無標記（該來源可能仍在鎖定中） | 告警 |
| 請求上下文缺席 | fail-open | 閘門放行；來源維整層跳過 | 告警 |
| 寫端自鎖 | **fail-closed** | 拒寫、零落庫、零重載 | 業務錯誤回應 |

## §6 錯誤碼對應（★13 碼矩陣零觸碰、零新變體）

| 情境 | 碼 | 訊息鍵 |
|---|---|---|
| IP 閘阻擋 | `5003`（HTTP 403 例外） | `system.forbidden`（既有） |
| 規則類型非二值 | `2222` | `biz.ipRule.invalidRuleType` |
| 網段字面不可解析 | `2222` | `biz.ipRule.invalidCidr` |
| 唯一性衝突 | `2222` | `biz.ipRule.conflict` |
| 標的不存在／狀態不符 | `2222` | `biz.ipRule.notFound` |
| 寫端自鎖 | `2222` | `biz.ipRule.selfLock` |
| 解鎖參數畸形 | `2222` | `biz.throttle.invalidUnlockTarget` |
| 內部異常 | `5000` | `system.internal`（既有） |

★六個新 `biz.*` 鍵須同步進三處鍵集（兩語 locale 之 `backend:` 樹＋治理錨點檔）——
**屬既有 ★I18N-WIRING 用途 (ii) 授權內**（資料級鍵、不觸 Amendment）；★並須同批擴
`app.d.ts` 之 `App.I18n.Schema.backend.biz` 型節（屬既有用途 (iii)，缺型節即型別檢查紅）。

## §7 sequence 紀律

本刀推進 `sys_ip_rule` 與 `sys_operation_log` 兩支 sequence。前者屬變體 A 業務表、
**不納入** schema 閘的 runtime-append 收窄集 ⇒ 走查後須依既有 quickstart 收尾清理
（TRUNCATE＋setval 重設）；後者納入收窄集後其列內容不再入比對面。
