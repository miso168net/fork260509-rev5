---
id: "0049"
title: 判定面同步進場——翻案「boot 載入即終態」＋rebuild-swap reload 契約（硬禁令＋casbin 版本鎖＋ABBA 三失效條件）
date: 2026-08-18
status: accepted
supersedes: []
superseded_by: []
provenance: "005-role-menu-crud 之 T003-①；grilling G1（熱重載基建自授權治理刀移入本刀、user 親決 2026-08-18）；藍本＝rev4:server/src/auth/enforce.rs（rebuild_enforcer／reload_enforcer 全套＋硬禁令註解 :69-:75）＋rev4:handler/menu.rs:329/348/364（specs/rev4:009-role-admin FR-016 三呼叫點）＋rev4:ADR 0048 島 G1 失敗契約段；被翻案宣告＝002-system-settings research R3-8（enforce.rs 檔頭／main.rs 兩處註解）"
tags: [authz, casbin, state-machine, reversal, concurrency]
---

## 背景

002-system-settings 落 casbin enforce seam 時拍定「boot 一次載入即終態、此後不再重載；
rev4:reload_enforcer 那套重建-swap 一律不搬」，理由子句＝**「B12 沒有治理寫端，政策在運行期
不會變」**（research R3-8）；該宣告以註解凍結於 `enforce.rs` 檔頭與 `main.rs` DB 連線段兩處。

本刀移除面三支寫端（deleteMenu／batchDeleteMenu／updateMenu 之 buttons 絕版歸檔）會在
運行期改變 `casbin_rule` ⇒ 理由子句自本刀起不成立、宣告連帶失效。若不重載：DB 已歸檔而
in-memory 判定面殘留舊政策 ⇒「資料庫已撤、記憶體仍生效」窗（島 H2 之 in-memory 半邊破口）。
依 spec FR-037～FR-040 以本 ADR 翻案，並同批改寫兩處註解（沿 004 對狀態容器五欄封條的
處置形：翻案歸 ADR、註解同 commit 指向本 ADR）。

## 決定

### 1. 翻案標的（T009 同批改寫、註解指向本 ADR）

- `rust-api/server/src/auth/enforce.rs` 檔頭「此後不再重載＝終態……一律不搬」段；
- `rust-api/server/src/main.rs` DB 連線註解「boot 一次載入即終態——rev4:reload_enforcer 不搬」句。

改寫後語意＝「判定面由真相全量導出；移除面寫端 commit 後以 rebuild-swap 同步（ADR 0049）」。

### 2. reload 契約（照 rev4 as-built 平移；rev5 差異＝觸發面僅移除面）

- **rebuild-swap 形**：`rebuild_enforcer(db)` 另建全新 Enforcer——`DefaultModel::from_str(MODEL_CONF)`
  → `SeaOrmAdapter::new(db)` → `Enforcer::new` → 顯式 `load_policy` 四步鏡像 init；
  ★任一步失敗整體 `Err`、不產出實例（全有或全無）；成功才於 `state.enforcer` write 鎖臨界區
  **一行 move-assign** 換值。enforcer 容器＝AppState 既有欄 `Arc<RwLock<Enforcer>>`
  （零新欄、不觸 ADR 0041 七欄封條）。
- **失敗契約 keep-last-good**：`RELOAD_MAX_ATTEMPTS: u32 = 3`＋`RELOAD_RETRY_BACKOFF_MS: u64 = 50`
  線性退避（★寫死常數、絕不取自輸入）；每次失敗結構化告警（`tracing::error!` 帶 cause）＋
  metrics `casbin_reload_total{outcome=ok|retry|exhausted}`；耗盡仍失敗＝維持舊面持續告警、
  服務不中斷（恢復待下次成功同步或維運介入）。**絕不空窗、絕不半載、絕不全 deny**。
- **觸發矩陣**（恰移除面三支、於交易 commit 之後）：

  | 寫端 | 觸發條件 |
  |---|---|
  | deleteMenu | 軟刪成功（連動歸檔恆發生）＝觸發 |
  | batchDeleteMenu | 整批成功＝觸發 |
  | updateMenu | **buttons 絕版歸檔實際發生**才觸發（facade 回傳歸檔與否；一般欄變更／無 buttons 變更＝零觸發） |

  被拒／無作用／標的不存在＝`?` 早退**結構性不觸發**（無需額外守衛）；deleteRole／
  batchDeleteRole 零觸發（免 reload 論證＝ADR 0050）；addMenu／restoreMenu 零 casbin 寫
  ＝零觸發。
- **★硬禁令＋版本鎖**：**絕不對 live 共享 Enforcer 裸呼 `load_policy`**。casbin 2.20.0
  （`rust-api/Cargo.toml:46` 釘版、與 rev4 同版）之 `Enforcer::load_policy` 為
  **clear-then-load**（casbin `src/enforcer.rs:765-767`）——先清空 in-memory policy 再向
  adapter 載入，載入失敗即 `?` 早退、留下空 policy；MODEL_CONF
  `e = some(where p.eft == allow)` 下空 policy＝**含 R_SUPER 全 deny、唯重啟可救**。
  故 reload 一律「另建新實例、成功才 swap」。☆版本鎖：本禁令釘 casbin 2.20.0 語意；
  升版 MUST 重核 `load_policy` 是否仍 clear-then-load（縱使改為 append 語意、重建-swap
  仍安全，惟註記需同步更新）；實作留特性鎖定測試。

### 3. ABBA 結構性無死鎖論證與三失效條件（FR-032）

選單域 advisory 鎖與既有 per-user advisory 鎖（`handler/auth/login.rs`、uid 為 key）共用
PostgreSQL 64-bit advisory key space，結構性無 ABBA 的論證＝兩條同時成立：
①**key space 不碰撞**（域鎖＝高位自描述 ASCII 常數、per-user＝個位數 bigserial uid）；
②**鎖集合零交集**（login txn 不取域鎖、選單域寫端不取 per-user 鎖 ⇒ 無任何交易同時持兩類鎖）。

★**三失效條件**（任一出現＝上述論證失效、該刀 MUST 重核鎖序並復核本 ADR）：

1. **role 寫端連動撤 session**——若未來 deleteRole／停用角色改為同交易撤銷該角色使用者的
   session（觸 per-user 鎖域），②即破；
2. **刀 B user 寫端進場**——user 域寫端若須進選單序列化域（或反向：選單域寫端須鎖 user 列
   之 per-user advisory），②即破；
3. **同 key 重入**——`pg_advisory_xact_lock` 同交易內重入為 no-op，但若出現「域內 fn 再開
   新交易並重取域鎖」的嵌套形（跨 txn 自等待）＝單獨即死鎖，與 ABBA 無關但同屬鎖序破口。

### 4. 測試面（FR-040 四支；本刀交付）

失敗注入（壞 conn ⇒ 舊面續 allow R_SUPER＋metrics retry/exhausted）／「改寫為裸呼
load_policy」必轉紅負向自證（明文步驟註解）／觸發條件特性鎖定（Rejected／NoOp／NotFound／
無 buttons 變更零觸發）／移除面端到端（DB＋in-memory 雙斷言、T032）。

## 後果

- T009／T010 授權前提成立；`enforce.rs` 檔頭與 `main.rs` 註解同批翻寫。
- 島 G1 之失敗契約條文全文隨授權治理刀入憲；本刀期間 reload 行為之凍結位＝本 ADR
  （授權治理刀 grant 面屆時**純消費**同一支 `reload_enforcer`、零新機制）。
- 島 H2「判定面殘留」路徑自此有機器閘（同鍵重建零繼承之 in-memory 半邊）；SC-006 之
  失敗注入服務不中斷承諾由 keep-last-good 承載。
- 日後任何人再看到「不再重載＝終態」的殘句＝文檔漂移，以本 ADR 為準。
