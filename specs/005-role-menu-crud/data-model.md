# Data Model — 005 role＋menu 管理 CRUD 寫端

> Phase 1 產物。**零結構變更、零 seed 變更**——本檔全部是「既有基線表獲得消費者」；
> 欄集以 `docs/generated/reference/schema.md` 真表為權威（本檔為消費視角快照）。

## §1 既有資料表的消費面（零 DDL）

### 1.1 `sys_role`（archetype A 業務全六欄；seed 3 列受結構護欄）

| 消費欄 | 型 | 本刀語意 |
|---|---|---|
| `role_code` | varchar NOT NULL | 建後不可變；形制 `^[A-Za-z0-9_]{1,64}$`；活性唯一（`sys_role_code_active_uniq` partial WHERE deleted_at IS NULL） |
| `role_name` | varchar NOT NULL | 可編 |
| `role_desc` | varchar NULL | 可編（與 memo 語意各異、兩欄並存——entity 檔頭既有拍板） |
| `role_memo` | text NULL | R_SUPER 備註；管理列表上 wire、getAllRoles 不帶（grilling G5） |
| `role_home` | varchar NULL | roleHome 讀寫端標的；寫端不驗可見樹一致性（讀端兜底既有） |
| `status` | smallint NULL | 1=啟用／2=停用；停用雙護欄（FR-010）；停用即斷權沿基線 |
| 六審計欄＋軟刪 | — | 軟刪＝成對寫 `deleted_at`/`deleted_by`；讀端過濾沿慣例 |

- 寫端全部經 facade、`FOR UPDATE` 鎖內重判（lock-then-redecide）；deleteRole 家族另進序列化域。
- ★`SEEDED_ROLE_IDS: [i64;3]=[1,2,3]`＋`SUPER_ROLE_CODE="R_SUPER"` 常數本刀建（碼內 hardcode
  形照 rev4——零表欄零 migration 的刻意取捨）。

### 1.2 `sys_menu`（archetype A；seed 78 列、樹狀）

| 消費欄 | 型 | 本刀語意 |
|---|---|---|
| `route_name` | varchar NOT NULL | 授權錨（casbin v1）＋i18n 錨；建後不可變；活性唯一（`sys_menu_route_name_active_uniq`）；addMenu 雙層守門（clarify Q2） |
| `menu_type` | smallint | 1=目錄／2=選單；建後不可變 |
| `parent_id` | bigint NULL | 樹關係；防環（上溯上限常數）；parent 三處一致驗證；NULL/0＝頂層 |
| `constant` | boolean NULL | 可寫；常量父鏈守門（島 H3 增補；現況 seed TRUE 0／FALSE 14／NULL 64） |
| `protected` | boolean NOT NULL default false | deleteMenu 守門第一腿（受保護不可刪）；本刀不提供旗標管理 |
| `buttons` | jsonb NULL | 按鈕碼聯集（授權治理刀 getAllButtons 真源）；updateMenu 變更觸發絕版歸檔判定（聯集域＝未刪含停用、clarify Q1） |
| `menu_memo` | text NULL | 同 role_memo 語意（grilling G5） |
| `status` | smallint | 停用＝暫時下架非撤銷（島 H4）；治理域含停用 |
| `order`／`hide_in_menu`／`keep_alive`／`multi_tab`／`icon*`／`i18n_key`／`route_path`／`component`／`href`／`active_menu`／`fixed_index_in_tab`／`query` | — | 一般可編欄（部分更新三態） |

### 1.3 `casbin_rule`（archetype D；163 列 seed；本刀僅移除面）

- 11 欄＝adapter 8 基底（ptype、v0~v5）＋治理 3（`protected`／`created_at`／`created_by`）。
- ★treated 治理欄對 casbin adapter **不可見**（drift-gate 雙向豁免）⇒ protected 判定走自建
  entity/SQL 面（授權治理刀消費；本刀 deleteRole 歸檔「含 protected 列」即直接掃表）。
- 本刀寫面恰三種：deleteRole 全三維掃刪（archive-move）、deleteMenu menu 維跨角色＋獨有碼
  掃刪、updateMenu 絕版碼掃刪。**零 INSERT**（grant 面屬授權治理刀）。
- `unique_key_sea_orm_adapter`（ptype,v0..v5 全欄唯一）＝歸檔回灌之天然屏障（本刀不觸）。

### 1.4 `sys_casbin_policy_archive`（archetype D；本刀建寫入面）

| 欄 | 本刀寫入語意 |
|---|---|
| `ptype`／`v0`~`v5` | 被移除政策列完整快照（v3~v5 空字串預設） |
| `role_id` | 來源角色識別；nullable 照 rev4（`role_code` 查無活角色＝誠實退化 NULL；menu 維跨角色掃描逐列以 v0 反查）|
| `archive_reason` | varchar(32) 封閉詞彙：`role_soft_delete`／`menu_soft_delete`／`menu_button_removed`（★歸屬權威＝rev4:sys_casbin_archive.rs:713：deleteMenu 獨有碼＝menu_soft_delete、updateMenu 絕版＝menu_button_removed） |
| `archived_at`／`archived_by` | now()＋操作者 uid |
| `created_at`／`created_by` | 原政策列之治理欄快照過境 |

- ★三 reason 全屬**不可復原集合**——單點 fn `is_non_restorable_reason` 本刀建，同時供
  列表旗標（非權威）與復原權威判定（授權治理刀 restorePolicy 消費）；配集合成員測試。
- 讀端（getArchivedPolicies）本刀不建。

### 1.5 `sys_operation_log`（append-only；寫端稽核）

- 每寫端同交易恰一列；`AuditOperation`＝小寫封閉詞彙**恰五值、role／menu 家族零新
  variant**（★T005 定案 2026-08-18，推翻本節初稿「× role／menu 家族擴充」形：operation
  軸只載**動作名**——add／update／delete／restore 直接沿用；標的表歸
  `AuditEvent::entity_table`＝`"sys_role"`／`"sys_menu"`；batch 刪＝逐標的一列、每列
  operation 皆 `delete`。定案理由與 rev4 as-built 佐證詳 audit.rs 詞彙 doc 與 tasks.md
  T005 補記；機器釘＝audit.rs tests T005 案）；`real_ip` NOT NULL ⇒ 上下文缺席拒寫
  5000（rev5 既定）。

## §2 記憶體實體與常數（非資料庫）

| 實體/常數 | 落點 | 語意 |
|---|---|---|
| 判定面 `Arc<RwLock<Enforcer>>` | AppState 既有欄 | rebuild-swap 換值；讀端短讀鎖既有三處不變 |
| `MENU_DOMAIN_LOCK_KEY: i64 = 0x7265_7635_6D65_6E75` | archive facade（域鎖底座） | "rev5menu"；活書級可調 |
| `RELOAD_MAX_ATTEMPTS=3`／`RELOAD_RETRY_BACKOFF_MS=50` | enforce.rs | 寫死常數、絕不取自輸入 |
| `SEEDED_ROLE_IDS=[1,2,3]`／`SUPER_ROLE_CODE="R_SUPER"` | sys_role facade | seeded 守門腿＋停用護欄 |
| 防環上溯上限（常數） | sys_menu facade | 值照 rev4 as-built、活書級 |
| reason gate 三值集 | archive facade | §1.4；單點 fn |
| `casbin_reload_total{ok\|retry\|exhausted}` | obs | 同步三 outcome 計數 |

## §3 狀態機矩陣（現態 × 事件 → 次態＋副作用）

### 3.1 選單

| 現態 | 事件 | 守門（固定序） | 次態 | 副作用 |
|---|---|---|---|---|
| 不存在 | addMenu | parent 驗證→防環→routeName 活性唯一（雙層）→constant 父鏈→形制 | 活性（原 status） | 零 casbin 寫、零 reload；稽核 |
| 活性/停用 | updateMenu（一般欄） | 不可變欄拒（routeName/menuType）→parent/防環（若改父）→constant 父鏈 | 同態 | 稽核；無 buttons 變更＝零 reload |
| 活性/停用 | updateMenu（buttons 移除且絕版） | 同上＋絕版判定（未刪含停用聯集） | 同態 | 絕版碼歸檔（menu_button_removed）＋reload＋稽核 |
| 活性/停用 | deleteMenu | protected→未刪子項（不論啟停） | 已刪 | menu 維跨角色＋獨有碼歸檔（皆 menu_soft_delete）＋reload＋稽核 |
| 已刪 | restoreMenu | 域內鎖列→同鍵活性衝突（23505 兜底）→父未刪 | 活性/停用（原 status） | 零回灌、零 casbin 寫、零 reload；稽核 |
| 已刪 | deleteMenu/updateMenu | 標的不存在形拒 | — | 零副作用 |

批刪＝child-first 拓撲序逐項全套守門、任一違規整批拒、單 txn。全部寫端：域鎖首動作。

### 3.2 角色

| 現態 | 事件 | 守門（固定序） | 次態 | 副作用 |
|---|---|---|---|---|
| 不存在 | addRole | code 形制→活性唯一 | 活性 | 零授權（兩步流）；稽核 |
| 活性 | updateRole（一般欄） | code 不可變拒→全 None no-op | 活性 | 稽核 |
| 活性 | updateRole（停用） | 自身所屬拒→R_SUPER 恆禁 | 停用 | 停用即斷權（授權讀端濾 status、次請求生效）；稽核 |
| 停用 | updateRole（啟用） | — | 活性 | 稽核 |
| 活性/停用 | deleteRole | seeded→in-use（others 精修）→self-role | 已刪 | 全三維含 protected 歸檔（role_soft_delete）＋**零 reload**＋稽核；單向無 restore |

### 3.3 判定面

| 現態 | 事件 | 次態 | 副作用 |
|---|---|---|---|
| 舊面 | 移除面 commit 成功（有歸檔） | 新面（重建成功 swap） | metrics ok |
| 舊面 | 重建失敗 ×≤3 | 舊面（keep-last-good） | 告警＋metrics retry |
| 舊面 | 重試耗盡 | 舊面 | 持續告警＋metrics exhausted；服務不中斷 |
| 任何 | 寫端被拒/無作用/deleteRole/addMenu/restoreMenu | 不變 | 零觸發（早退結構性保證） |

## §4 不變式清單（島 H 五條入憲原文骨架；G 行為由 A1 域行為 ADR 承載）

- **H1 序列化域**：選單樹五寫端＋deleteRole 家族＋（授權治理刀之選單維／按鈕維授權寫端與
  restorePolicy——終態成員、屆時兌現）MUST 於單一 advisory 域內互斥執行；域內
  lock-then-redecide、永不信 pre-read；advisory key space 全域唯一（per-user 鎖用 uid、
  域鎖用高位自描述常數）。反轉（拆域／無鎖 pre-read）＝MAJOR。
- **H2 同鍵重建零繼承**：同 routeName 重建 MUST NOT 經任何路徑（現役殘留、判定面殘留、
  回收桶復原）繼承舊實例授權；雙封＝掃盡歸檔＋reason gate；判定面同步使 in-memory 面同受
  約束。反轉＝MAJOR。
- **H3 樹結構**：防環（上限常數）；parent 三處一致（停用不擋、頂層豁免）；deleteMenu 固定序
  守門；批刪 no-partial＋child-first；★常量父鏈常量性（rev5 專屬新條）。
- **H4 不可變錨欄＋兩域分層**：routeName／menuType 建後不可變（顯式拒）；治理域（未刪含停用）
  ／顯示域（啟用未刪）分讀；停用 MUST NOT 被任何全量替換語意升級為撤銷。反轉＝MAJOR。
- **H5 復原不回灌**：restoreMenu 域內重驗→成對清空軟刪欄＋原 status 保留；零授權回灌。
  反轉＝MAJOR。
- 常數（advisory key、上溯上限、routeName 形制上限）＝活書級可調、不入條文。

## §5 錯誤碼對應（13 碼矩陣零觸碰、零新變體）

| 情境 | 碼 | i18n 鍵（新增、三處同補） |
|---|---|---|
| 守門拒（seeded／in-use／self-role／停用護欄×2） | 2222 | `biz.role.*` 家族（tasks 定逐字） |
| code／routeName 不可變、活性重複、形制 | 2222 | 同上／`biz.menu.*` |
| menu 守門（protected／未刪子項／防環／parent／constant 父鏈／同鍵衝突／不可復原） | 2222 | `biz.menu.*` 家族 |
| 授權拒（非 R_SUPER 打寫端） | 5003 | 既有 |
| 標的不存在 | 既有 not-found 慣例碼 | 既有 |
| 上下文缺席拒寫 | 5000 | 既有 |

## §6 sequence 紀律

- `sys_role_id_seq`（gate2 setval 期望 3）／`sys_menu_id_seq`：寫端推進 seq 與 gate2 的互動
  ＝tasks 早期顯式查證項（U 早段跑 `schema-gate check` 實測後定測試紀律）；測試造列一律
  顯式大 id＋清理守衛 sequence 還原斷言（比照 004 `sequence_reset_guard` 形）。
- `sys_casbin_policy_archive_id_seq`：append 推進、無非零 setval 期望值（歸檔表非 seed
  凍結面）——tasks 查證項一併覆核。
- ★T004 實測定案（2026-08-18；容器內三形各一輪 gate、詳 tasks.md T004 補記；第四支
  `casbin_rule_id_seq` 為 quality-fix 輪同法補測、同結論）：
  ①顯式大 id INSERT 不動 seq；殘列＝gate2 seed 逐列 diff 紅（sys_role／sys_menu／
  casbin_rule／歸檔表四表皆在逐列比對面——casbin_rule 亦不在 `RUNTIME_APPEND_TABLES`
  收窄集），DELETE 殘列即綠、毋須 setval。②nextval 推進
  （addRole／addMenu 寫端形、casbin adapter `add_policy`、歸檔表 default id append）
  ＝四條 seq 之 setval 行逐字比對紅——★sys_casbin_policy_archive_id_seq 雖無非零期望值，
  其 setval 行仍受比對，僅 is_called 翻位（`1, false`→`1, true`）即紅。③setval 還原即綠。
  ⇒ 本刀測試與清理守衛 MUST setval 還原且 **is_called 位正確**：
  `sys_role_id_seq=(3,true)`／`sys_menu_id_seq=(78,true)`／`casbin_rule_id_seq=(163,true)`／
  `sys_casbin_policy_archive_id_seq=(1,false)`；gate 規則零調整。★casbin_rule 之測試造列
  走真 Enforcer `add_policy`＝nextval 取 id，「顯式大 id 免 setval」免除路徑在此不成立。
