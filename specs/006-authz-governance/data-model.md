# Data Model — 006 三維授權治理＋結構性封死＋授權回收桶

> Phase 1 產物。**零結構變更、零 seed 變更**——本檔全部是「既有基線表獲得 grant／revoke／restore 消費者」；
> 欄集以 `docs/generated/reference/schema.md` 真表為權威（本檔為消費視角快照）。reason gate 五值、五腿、
> 封死謂詞、觸發矩陣皆為 user 親決（brainstorm §10／§11＋clarify 2026-08-23）之轉錄。

## §1 既有資料表的消費面（零 DDL）

### 1.1 `casbin_rule`（archetype D；seed 163 列、全 ptype='p'；本刀 grant／revoke／restore 三寫面）

| 消費欄 | 型 | 本刀語意 |
|---|---|---|
| `ptype` | varchar NOT NULL | 恆 `'p'`（seed 無 `g` 列；角色指派住 `sys_user_role`） |
| `v0` | varchar | 角色代碼（來源角色） |
| `v1` | varchar(125) | 標的：選單維＝`route_name`／按鈕維＝按鈕碼／端點維＝路徑 |
| `v2` | varchar | 維度標記 `'menu'`／`'button'`／或 HTTP 方法 `GET`／`POST`／`DELETE`（端點維以方法白名單辨識、不以排除反推） |
| `v3`～`v5` | varchar NOT NULL | 恆空字串 |
| `protected` | boolean NOT NULL default false | 治理欄（adapter 不可見）；撤銷集觸及＝整批拒；**封死謂詞**之標的集來源；grant 寫死 `false`、restore 回灌**顯式** `Set(false)` |
| `created_at`／`created_by` | timestamptz NOT NULL default now()／bigint | grant 補齊（now＋操作者）；restore 回灌＝now＋復原者（復原＝新 grant 事件、原血緣在歸檔列與 op-log） |
| 唯一索引 `unique_key_sea_orm_adapter`(ptype,v0..v5) | | restorePolicy 7b 撞 23505＝NoOp 競態收斂（`violated_constraint` 比對此名、不用 `UniqueConstraintViolation` 變體） |

- 本刀寫面恰四種：三維 grant（INSERT）、三維 revoke（archive-move＝歸檔後 by-id DELETE）、restore 回灌（INSERT）、歸檔列刪除（restore）。
- seed 靜態量（2026-08-23 機器核、敘事非不變式）：v2 分佈 menu 85／GET 25／button 24／POST 22／DELETE 7；protected=TRUE 19＝端點維 15＋menu 維 4（列 10／11／69／72）。
- 封死謂詞（島 G6）：`ptype='p' ∧ protected=TRUE ∧ v2∈{GET,POST,DELETE}` 之 `(v1,v2)` 集，**鎖內現查**；條文不寫列數。

### 1.2 `sys_casbin_policy_archive`（archetype D；14 欄；seed 0 列；本刀建讀端＋restore）

| 欄 | 本刀語意 |
|---|---|
| `id` | 歸檔列 id＝restorePolicy 請求鍵；`serialize_i64_number_guarded` |
| `role_id` | 來源角色識別（nullable；`insert_archived` 內收反查、grant 面標的角色已鎖且活性⇒恆 Some）；**同實例半**＝`role_id == 現役同代碼活角色 id`、NULL→不可復原（誠實退化） |
| `ptype`／`v0`～`v5` | 政策快照；`v2` 推導 `dimension`（menu／button／endpoint）；`v0` 為 `roleCode` 濾鍵 |
| `archive_reason` varchar(32) | 封閉詞彙六值：不可復原集 `{role_soft_delete, menu_soft_delete, menu_button_removed, menu_revoke, button_revoke}`＋唯一可復原 `endpoint_revoke`（最長 19 字元、在界內） |
| `archived_at`／`archived_by` | 排序鍵 `archived_at DESC, id DESC`；`archivedBy` wire 為 enrich 帳號名（string\|null） |
| `created_at`（nullable）／`created_by` | 原 grant 治理欄快照（restore 不回灌此兩欄、沿 rev4） |
| 索引 `idx_casbin_archive_role_dim`(v0,v2)／`idx_casbin_archive_archived_at` | 雙濾＋排序現成＝讀端零 migration |

- 派生欄（非 DB）：`restorable`＝①reason 不屬不可復原集 ∧ ②同實例 ∧ ③封死不擋 ∧ ④端點在冊（⑤免算）；`dimension`。
- 不變式（ADR 0050 §4 承重）：protected=TRUE 原值之列**結構上進不了本表**（整批拒先於任何寫）——機器斷言（SC-006）。

### 1.3 `sys_role`／`sys_menu`（消費唯讀＋鎖）

- `sys_role`：三維寫端與 restorePolicy 以 `FOR UPDATE` 鎖標的角色列（活性＝`deleted_at IS NULL`、不含 status）；新批次讀端 `active_ids_by_codes`（純 SELECT）與窄投影 `active_code_of`。
- `sys_menu`：治理域（`list_governed`，未刪含停用）＝選單維候選、id↔route_name 映射、buttons 聯集；顯示域（`list_active`）＝getAllPages／roleHome 候選；皆不鎖。

### 1.4 `sys_operation_log`（append-only；寫端稽核）

- 三維寫端：`operation=update`／`entity_table="sys_role"`／`entity_id=role_id`／`payload_after={dimension, revoked:n, granted:n}`；Rejected 零稽核。
- restorePolicy Applied：`operation=restore`／`entity_table="sys_role"`／`entity_id=role.id`／`payload_after={archive_id, dimension, target, act}`；NoOp／NotRestorable 零稽核。
- 詞彙恰五值不擴（audit.rs t005 釘）；`real_ip` NOT NULL ⇒ 上下文缺席拒寫 5000。

## §2 記憶體實體與常數（非資料庫）

| 實體／常數 | 落點（候選） | 語意 |
|---|---|---|
| `Dimension{Menu, Button}`＋端點維專路 | facade/sys_casbin_policy.rs | 維度→`v2` 字面／→revoke reason |
| `PolicyOutcome::Applied{revoked, granted, effective}`／`Rejected{blocked}` | 同上 | 恰兩態、無 NoOp；`blocked` 永不上 wire |
| 候選集（menu 治理域映射／button 聯集／endpoint Policy 集） | facade 讀治理域；endpoint 候選由 handler `policy_endpoints()` 傳入 | orphan skip 判準；與判定面同源 |
| `ENDPOINT_METHODS` | 自 `router::HttpMethod::as_str()` 導出、由 handler 傳入 | 端點維辨識白名單（單一真源） |
| `REASON_MENU_REVOKE`／`REASON_BUTTON_REVOKE`／`REASON_ENDPOINT_REVOKE` | facade/sys_casbin_archive.rs（照既有三常數形） | 本刀新立；前兩者入 `is_non_restorable_reason` |
| `RestoreOutcome::Applied／NoOp／NotRestorable` | facade/sys_casbin_archive.rs | restorePolicy 三態 |
| 判定面（enforcer） | auth/enforce.rs | 真相導出；觸發矩陣 7 列；`RELOAD_SERIAL`；呼叫者不得持讀鎖 |
| `SUPER_ROLE_CODE`＝`"R_SUPER"` | facade/sys_role.rs:74（既有、有 seed 釘） | 封死「非 R_SUPER」判準 |

## §3 狀態機矩陣（現態 × 事件 → 次態＋副作用）

### 3.1 三維授權寫端（menu／button／endpoint 同形；差異在入域與封死）

| 事件 | 守門（固定序） | 結果 | 副作用 |
|---|---|---|---|
| 角色不存在／已刪 | 鎖讀查無 | `biz.role.notFound`（2222） | 零變更 |
| 期望集含候選外項 | orphan skip（靜默略過） | 繼續 | 回應 `effective` 不含 |
| 撤銷集含 protected | 任何寫之前 | `Rejected`→`biz.role.protectedRevoke` | rollback、零稽核、零 reload |
| 端點維新授集 ∩ 封死集 ≠ ∅ 且角色非 R_SUPER | protected 整批拒之後、任何寫之前 | `Rejected`→`biz.role.protectedGrant` | 同上 |
| 正常（含空 diff） | — | `Applied{revoked, granted, effective}` | archive-move（reason=`*_revoke`）＋INSERT＋稽核 update（同交易）→commit→**reload（不問 diff）** |

入域：menu／button 維（域鎖首動作）；endpoint 維不入域。鎖序：advisory→sys_role 列→（sys_menu 讀）→casbin_rule。

### 3.2 restorePolicy（五腿固定序）

| 步 | 判定 | 失敗結果 | 對應現役寫端守門 |
|---|---|---|---|
| 鎖歸檔列 | FOR UPDATE、查無（假 id／已被消費） | NotRestorable | — |
| ① reason gate | `is_non_restorable_reason(reason)` | NotRestorable | 連動歸檔三 reason＋手動撤銷 menu／button（單點 fn） |
| 鎖活角色列 | by `v0`、FOR UPDATE、活性（不含 status） | NotRestorable | deleteRole／三維寫端鎖標的角色列 |
| ② 同實例 | `role_id == Some(role.id)`（NULL 恆不等） | NotRestorable | 島 H2 零繼承 |
| ③ 封死 | 角色非 R_SUPER ∧ `(v1,v2)`∈protected 集 | NotRestorable | updateRoleEndpoints 同一守門 |
| ④ 端點在冊 | `(v1,v2)`∈路由註冊表 Policy 候選 | NotRestorable | getAllEndpoints 候選集（免幽靈政策） |
| ⑤ 停用不擋 | — | （不擋） | 停用即斷權基線 |
| 7a | 七欄身分鍵已 live | **NoOp**（0000；刪歸檔列、commit；零稽核、零 reload） | — |
| 7b | INSERT（protected 顯式 false、created_at=now、created_by=復原者）；23505→NotRestorable | **Applied**（刪歸檔列＋稽核 restore→commit→reload） | — |

### 3.3 判定面（擴為 7 觸發者）

| 面 | 寫端 | 觸發 |
|---|---|---|
| 移除面 3 | deleteMenu／batchDeleteMenu／updateMenu | 成功**且有連動歸檔**（`if archived`） |
| grant 面 3 | updateRoleMenu／updateRoleButton／updateRoleEndpoints | **Applied 即觸發、不問 diff**（刻意例外） |
| 回收桶 1 | restorePolicy | Applied；NoOp／NotRestorable 不觸發 |
| 其餘 | deleteRole／batchDeleteRole／addMenu／restoreMenu／addRole／updateRole／roleHome | 零觸發 |

失敗契約沿 005：keep-last-good、有界重試、服務不中斷；`RELOAD_SERIAL` 互斥。

### 3.4 restorable 旗標（列表派生、非權威）

`restorable = ¬non_restorable(reason) ∧ same_instance(role_id, active_id_by_code[v0]) ∧ ¬(role≠R_SUPER ∧ (v1,v2)∈protected_set) ∧ (v1,v2)∈routes_policy_set`
——四腿批次料源：單點 fn／`active_ids_by_codes`／單次 protected 集 SELECT／ROUTES 內建集合；⑤免算。選單／按鈕維列因①恆 false。

## §4 不變式清單（島 G 六條入憲原文骨架；定稿於 U1、user 親決）

- **G1 真相唯一與同步失敗契約**：授權真相＝DB 政策表；授權變更與稽核 MUST 同一交易落地、絕不走判定引擎管理 API 寫面（DB-first）；判定面由真相全量重載導出——
  成功 commit 後 MUST 同步；被拒／無作用／標的不存在 MUST NOT 觸發（早退結構性保證）；grant 面 Applied 即觸發不問 diff＝刻意例外、與移除面「成功且有歸檔才觸發」並陳；
  矩陣本體留 ADR／活書。失敗契約：重建成功才 swap、keep-last-good、結構化告警＋有界重試、耗盡維持舊面持續告警。反轉（同步失敗改清空／全 deny）＝MAJOR。
- **G2 受保護拒絕**：撤銷集觸及 protected→整批拒、零變更（任何寫之前判定）；拒絕 MUST 使原因可辨識、一因一鍵（明細載體屬活書級、不入條文）；un-protect／re-protect 經一般管理介面永不提供。
- **G3 撤銷必歸檔**：revoke＝archive-move（完整快照＋來源角色識別＋reason）、grant＝INSERT 補齊治理欄（protected=false＋created_at/by）；刪角色同交易全維連動歸檔（含 protected 列、reason=`role_soft_delete`）；`role_soft_delete` 列 MUST NOT 可手動復原；角色刪除單向。
- **G4 刪除守門與批次原子**：固定序三層守門（seeded→in-use→self-role）；批次逐項驗證、任一違規整批拒、單一交易。（純轉正）
- **G5 復原同實例與全端點鎖序**：一切向現役授權寫入或改動角色活性／啟用的寫端 MUST 同交易 FOR UPDATE 鎖標的角色列、鎖內重判前提後才落寫（lock-then-redecide、永不信 pre-read）；
  固定鎖序 advisory→歸檔表列→sys_role 列→sys_menu 列→casbin_rule；復原 MUST 鎖內重驗（reason gate＋同實例；NULL→不可復原、誠實退化；五腿全文留 ADR——條文層級＝U1 親決）；
  刀 B 之 `sys_user_role` 指派寫端落地時 MUST 同納本鎖序。
- **G6 結構性封死（本刀新拍板）**：屬「`ptype=p ∧ protected=TRUE ∧ v2∈HTTP 動詞`」之 `(v1,v2)` 集合（謂詞式、鎖內現查、不寫列數）MUST NOT 授予非 R_SUPER；
  掛點恰為端點維授權寫端與回收桶端點維復原（雙路徑）；違者整批拒零變更；menu 維 protected 不在射程（已知態）；守門非 vacuous＋變異自證；反轉（部分成功／開放 un-protect UI）＝MAJOR。
- 常數（reason 字面集、封死集量測值、觸發矩陣列數、候選集來源）＝活書／ADR 級、不入條文。

## §5 錯誤碼對應（13 碼矩陣零觸碰、零新變體）

| 情境 | code | msg key |
|---|---|---|
| 角色不存在／已刪（三維讀寫、restore 鎖角色查無走 NotRestorable） | 2222 | `biz.role.notFound` |
| 撤銷集觸及 protected | 2222 | `biz.role.protectedRevoke`（新） |
| 端點維授予封死集給非 R_SUPER | 2222 | `biz.role.protectedGrant`（新、命名定於 contracts/msg-keys.md） |
| restorePolicy 識別不存在／任一腿拒／23505 競態 | 2222 | `biz.policy.notRestorable`（新、新開 `biz.policy` 子樹） |
| 非 R_SUPER 打 11 支任一 | 5003 | （既有） |
| 請求上下文缺席（寫端） | 5000 | （既有） |
| body 取用失敗／空 body | → 預設形（角色鍵 0）→`biz.role.notFound` | 零新碼 |

## §6 sequence 紀律

- `casbin_rule_id_seq`：grant／restore 回灌走 nextval ⇒ 測試必配 `CasbinCleanup`（`setval(163,true)`）；`sys_casbin_policy_archive_id_seq`：revoke 歸檔走 nextval ⇒ `setval(1,false)`（is_called 位不可錯）。
- gate2 對兩表逐列全等（不在 runtime-append 收窄集）；CDP 走查後還原（清列＋兩 setval）再跑 schema-gate。
- `sys_role`／`sys_menu` 測試列一律顯式大 id（RoleCleanup／MenuCleanup 還原 (3,true)／(78,true)）。
