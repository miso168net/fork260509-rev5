# Feature Specification: 005 role＋menu 管理 CRUD 寫端（含序列化域與判定面同步基建）

**Feature Branch**: `005-role-menu-crud`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "docs/brainstorms/005-role-menu-crud.md"（階段 0 brainstorm＋/grilling
六題盤問後定稿；本 spec 之唯一輸入。原單刀「刀 A＝role+menu」沿縫 α 拆兩刀之前半；後半＝
authz-governance（brainstorm 已同場定稿、暫存版控外、起手時補入配號）。射程權威＝brainstorm
§2；rev4 對應碼＝實作預設藍本、清單於 plan research 凍結（ADR 0019））

> 摘要：把 rev5 管理面的兩張基石列表頁（角色、選單）從 upstream demo 殼接成真——**role CRUD 6 支
> ＋menu CRUD 7 支＋roleHome 讀寫 2 支＋治理域支撐讀 1 支＝16 支端點**（ROUTES 22→38），前後端
> 同刀、CDP 三方對照驗收。同刀落地三件授權治理刀也要消費的底座：**選單域 advisory 序列化域**（含
> deleteRole 入域——rev5 對 rev4 未論證併發窗的補強）、**casbin rebuild-swap 判定面同步**（rev4
> FR-016 之 menu 移除面 MUST reload；失敗 keep-last-good、絕不裸呼 load_policy）、**授權歸檔寫入
> 面＋reason gate**。憲法開 §I.7 第七座行為島（島 H 選單域生命週期，五條全文入憲）＋§III.2
> `MANAGE-PAGE-WIRING` 加用途 (ii)（MINOR v1.6.2→v1.7.0、B-087 殘餘②補註順捎）。**零 migration、
> 零 seed 變更**——16 支端點政策列（含 getDeletedMenus／restoreMenu 兩列 protected）全數已在 001
> 凍結 seed 內。**零 grant 面**：三維授權治理、結構性封死、授權回收桶讀端全歸授權治理刀。

## Clarifications

### Session 2026-08-18（brainstorm 拍板；屬本刀之條目，全紀錄見 brainstorm §3）

- Q: 刀怎麼切？→ A: **刀 A＝role+menu、刀 B＝user+password；刀 A 再沿縫 α（grant/revoke 寫
  casbin_rule 分水嶺）拆 005／授權治理刀**。理由＝rev4:ADR 0051 把選單樹寫端與選單維／按鈕維授權寫端
  納入同一把 DB 交易級 advisory 序列化域、`getAllButtons` 真源＝`sys_menu.buttons` ⇒ menu 域與
  三維授權治理硬耦合必須同刀群；島 H→005、島 G→授權治理刀、島 I→刀 B。
- Q: 前端腿？→ A: **前後端同刀**——可 CDP 對照驗收；修憲躲不掉（島必入憲），前端多付的只是
  軌道用途擴列。
- Q: `deleteRole`／`batchDeleteRole` 要不要入選單序列化域？→ A: **拉進域**（rev5 新增域成員、
  rev4 沒有）——消滅 rev4 零論證零測試的 deleteRole×deleteMenu 併發窗（兩者寫同一批 casbin_rule
  列、列鎖不相交）；治理 QPS≈0、代價≈0。
- Q: 歸檔表三個 rev5 自由度（role_id NOT NULL／protected 快照欄／menu_id 同實例欄）？→ A:
  **全不動**——保零 migration；誠實退化路徑保留；防的狀態結構性不可達；menu 側零繼承由
  reason gate 一刀封死。rev4:ADR 0049 翻案觸發條款照字面帶進本刀 ADR。
- Q: 選單寫端可寫欄集含不含 `constant`？→ A: **可寫＋父鏈常量性守門**（島 H3 增補一條 rev5
  專屬不變式）——與 rev4 UI 對齊；防 `getConstantRoutes`（Public 免認證＋祖先包含組樹）外洩
  受保護父目錄資訊；現況 seed `constant` TRUE 0 列＝零存量影響。
- Q: 回收桶 restore 動作要不要按鈕碼 gating？→ A: **不 gating**（頁級 R_SUPER＋列級
  restorable 兩道門）——基線 seed 已拍此形（有 `user:restore` 無 `menu:restore`）、照 rev4:010、
  保零 migration。
- Q: 選單回收桶 UI 形？→ A: **toggle 形照 rev4**（「顯示已刪除」開關換資料源、獨立端點
  getDeletedMenus）——CDP 基準對得上、用上預埋 seed 政策列、樹表混排已刪節點的層級語意難定。
- Q: 前端 static meta 與 DB seed 分歧？→ A: **DB 唯一真源、不維護 static meta**（本 spec 記此
  一句紀律、不建閘）——dynamic 路由模式下 static fallback 影響≈0。
- Q: 修憲次數？→ A: 拆刀後各刀一次 MINOR——**005 落島 H（v1.6.2→v1.7.0）**、授權治理刀落島 G。

### Session 2026-08-18（/grilling 六題；全文見 brainstorm §3 grilling 表）

- Q(G1): 熱重載基建歸屬？→ A: **移入 005、授權治理刀變純消費**——rev4 FR-016 逐字「觸及授權變更的
  寫入成功後 MUST 同步授權判定面」，menu 移除面三支（deleteMenu／batchDeleteMenu／updateMenu
  之 buttons 絕版歸檔）皆呼叫 reload（rev4:handler/menu.rs:329/348/364）；基建屬 rev4:009 早段、
  原拆刀誤分授權治理刀。總量不變、島 H2 乾淨入憲（零已知違憲窗）、最高風險件先在本刀被專注驗證。
- Q(G2): 新建／復原選單在授權治理刀授權面板進場前無法授予可見性（含 R_SUPER——MODEL_CONF 無旁路、
  機器驗證）？→ A: **接受、列已知態**——側欄不現、管理列表照常可編；本質＝兩步流第二步工具
  晚一刀、與 rev4「第一步完成第二步未勾」同形。
- Q(G3): 前端修改型檔清單？→ A: **照實拆列**——本刀＝role 3 檔＋menu 2~3 檔；`menu-auth-modal.vue`
  ／`button-auth-modal.vue` 兩檔一行不動留授權治理刀（憲法檔級名單＝硬邊界，多列＝授權未發生的修改）。
- Q(G4): getMenuTree 歸屬？→ A: **移入 005**（16 支／授權治理刀11 支）——rev4 menu-operate-modal 之
  父節點選擇器逐字消費 `fetchGetMenuTree`、本刀 menu 頁做真即硬相依。
- Q(G5): memo 欄？→ A: **本刀兌現 `role_memo`＋`menu_memo` 兩欄、列表顯示不濾受眾**——
  004 wbip_memo 範本照抄；R_ADMIN 經 getRoleList 可見、placeholder 註明；getAllRoles 等被取用處
  不帶；B-003 自此剩 sys_user（→刀 B）。
- Q(G6): deleteRole 之 in-use／self-role 兩腿在刀 B（user 角色指派寫端）落地前生產面結構性
  不可達？→ A: **接受照建＋本 spec 註記**——資料態判定、測試種指派列即真實觸發（零旗標、非
  vacuous）；拆段建＝同域分段長成。

### Session 2026-08-18（/speckit-clarify）

- Q: 絕版判定（button 碼歸檔前提）的聯集範圍＝未刪含停用、還是僅啟用？ → A: **未刪選單
  （含停用）＝治理域聯集**——停用選單持有的碼不算絕版；否則停用中選單的按鈕授權被誤判
  絕版歸檔（不可復原）＝「停用靜默升級為永久撤銷」的 button 維翻版（FR-019 同構）。
  全文「活選單」自此正名為「未刪選單（含停用）」。
- Q: addMenu 撞活性同鍵 `routeName` 的守門形？ → A: **雙層**——域鎖內先驗活性同鍵→顯式拒
  （與 FR-009 role code 同式）；`sys_menu_route_name_active_uniq` 部分唯一索引（基線既有）
  兜底、競態下 23505 收斂為同一業務拒因（與 restoreMenu 兜底慣例一致）。
- Q: getAllRoles 本刀 as-shipped 零前端消費者（menu modal 殘留呼叫不帶、user 頁屬刀 B）
  ——照交付還是出列？ → A: **照交付（16 支不變）、為刀 B 預埋並列已知態**——下拉讀端早到
  ＝功能面零損失；契約一次成套、刀 B 進場零後端改動；seed 政策列（含 R_USER_COMMON）既有。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 超管管理角色全生命週期 (Priority: P1)

超級管理員在角色管理頁看到真實角色列表（分頁＋名稱／代碼模糊搜尋＋狀態等值篩選＋備註欄），
可新增角色（代碼形制受驗、活性代碼唯一）、編輯角色（名稱／描述／狀態／備註；代碼不可變）、
刪除角色（受三層守門保護）、批次刪除（任一違規整批拒）。停用角色即斷其授權（下次請求生效）。

**Why this priority**: 角色是授權模型的軸心實體；沒有真實角色 CRUD，授權治理刀的三維授權治理與
刀 B 的使用者角色指派都沒有操作對象。今日該頁為 demo 殼（讀端打不存在的端點得 404、寫端
假成功 toast）。

**Independent Test**: 以 Super 登入 → 角色頁列表顯示 seed 三角色（含 R_ADMIN 可見的備註欄
placeholder）→ 新增一個角色 → 編輯其名稱與狀態 → 刪除之 → 全程回應與列表刷新一致；
以 Admin 登入可讀列表、寫入操作被後端拒（5003）。

**Acceptance Scenarios**:

1. **Given** seed 基線三角色，**When** 超管開啟角色列表，**Then** 分頁顯示三列、可依名稱／代碼
   模糊與狀態篩選，`role_memo` 欄顯示於列表（seed 值全空）。
2. **Given** 新增抽屜，**When** 提交代碼 `R_OPS`（合形制）與名稱，**Then** 回成功、列表出現新列；
   **When** 提交與活性列重複的代碼或不合形制（含小寫外字元／超長）的代碼，**Then** 顯式拒、
   一因一鍵。
3. **Given** 既有角色，**When** 編輯提交未含 `roleCode` 變更以外的欄位變更，**Then** 依部分更新
   三態語意落庫；**When** 試圖變更 `roleCode`，**Then** 顯式拒（不可變、非靜默忽略）。
4. **Given** seed 角色（id 1/2/3），**When** 試圖刪除，**Then** 被 seeded 護欄拒；**Given**
   測試種下的「有掛載使用者」角色，**When** 刪除，**Then** 被 in-use 護欄拒且拒因回誠實總掛載
   人數語意（純 key）；**Given** 操作者自身所屬角色（經測試資料構造），**When** 刪除，**Then**
   被 self-role 護欄拒——三層固定序 seeded→in-use→self-role。
5. **Given** 批次刪除集合含任一違規項，**When** 提交，**Then** 整批拒、零變更（單一交易、
   id 升冪逐項驗證）。
6. **Given** 一個無掛載的自建角色且其名下經測試種有三維政策列，**When** 刪除成功，**Then**
   該角色全三維政策列（含 protected）同交易 archive-move（reason=`role_soft_delete`、不可復原）、
   同交易落操作稽核；角色刪除單向、無復原端點。

---

### User Story 2 - 超管管理選單樹 (Priority: P1)

超級管理員在選單管理頁看到真實選單樹（treeTable、分頁以頂層計、備註欄），可新增目錄／選單
（父節點自現有樹選擇、可寫 buttons 與 constant 欄）、編輯（改父受防環與父存在性驗證；
`routeName`／`menuType` 不可變）、刪除（守門＋跨全角色授權連動歸檔＋判定面同步）、批次刪除
（child-first 拓撲序、整批拒）。

**Why this priority**: 選單域是島 H 的本體，也是授權治理刀三維授權治理（menu／button 維）的資料
真源；`getAllButtons` 候選集＝`sys_menu.buttons` 聯集。與 US1 同為本刀 MVP。

**Independent Test**: 以 Super 登入 → 選單頁樹列表顯示 seed 78 列的樹形 → 新增一個子選單
（父選擇器自 getMenuTree 取樹）→ 編輯其 buttons 欄移除一碼 → 刪除之 → 全程守門與歸檔行為
可由稽核與歸檔表查證。

**Acceptance Scenarios**:

1. **Given** seed 選單樹，**When** 開啟選單列表，**Then** 治理域讀端（未刪含停用）以樹形分頁
   呈現（頂層計）、`menu_memo` 欄顯示。
2. **Given** 新增 modal，**When** 父節點選擇器開啟，**Then** 選項樹來自治理域（含停用、不含
   已刪）；**When** 提交 `parentId=0`，**Then** 頂層豁免父驗證；**When** 提交之父不存在或已刪，
   **Then** 顯式拒（停用不擋）；**When** 提交與活性列重複之 `routeName`，**Then** 顯式拒。
3. **Given** 既有選單，**When** 編輯試圖變更 `routeName` 或 `menuType`，**Then** 顯式拒；
   **When** 改父使祖先鏈成環（上溯遇自身），**Then** 顯式拒（上溯上限為常數）。
4. **Given** 選單 X 之 buttons 欄含碼 `x:op` 且該碼不屬其他未刪選單（含停用），**When** 編輯移除該碼，
   **Then** 該碼之 button 維政策同交易絕版歸檔（reason=`menu_button_removed`、不可復原）且
   觸發判定面同步。
5. **Given** 選單 Y 存在未刪子項（不論啟停），**When** 刪除 Y，**Then** 被守門拒；**Given**
   受保護選單，**When** 刪除，**Then** 被守門拒（固定序：受保護→未刪子項）。
6. **Given** 無子項選單 Z 且測試種有跨角色 menu 維政策，**When** 刪除成功，**Then** 掃
   `v1=route_name AND v2='menu'` 跨全角色歸檔＋獨有 button 碼一併歸檔（兩者 reason 皆＝
   `menu_soft_delete`）、同交易稽核、觸發判定面同步。
7. **Given** 批刪集合內含父子，**When** 提交，**Then** child-first 拓撲序逐項驗證、任一違規
   整批拒。
8. **Given** 常量選單（`constant=TRUE`）欲掛於非常量父之下，**When** 提交（新增或改父），
   **Then** 顯式拒（父鏈常量性守門——防 Public 端點外洩受保護父目錄資訊）。

---

### User Story 3 - 選單回收桶與復原 (Priority: P2)

超級管理員在選單頁切「顯示已刪除」開關，列表換源為已刪集合；對可復原列執行復原——復原後
選單回到未刪（原啟停狀態保留），但不回灌任何授權（可見性經授權治理刀的授權面板重勾）。

**Why this priority**: 軟刪而無復原＝變相硬刪；但其價值依附於 US2 的刪除面，故次於 P1。

**Independent Test**: 刪除一個自建選單 → 開 toggle 見其出現於已刪列表 → 復原 → 關 toggle
見其回到樹中、狀態如刪前；歸檔之授權列不隨復原回灌。

**Acceptance Scenarios**:

1. **Given** 已刪選單若干，**When** 開啟 toggle，**Then** 列表換打 getDeletedMenus、操作欄
   整欄換為復原動作（無按鈕碼 gating；門＝頁級授權＋列級可復原性）。
2. **Given** 已刪選單 W 與後建之同 `route_name` 活性選單，**When** 復原 W，**Then** 顯式拒
   （域內鎖列重驗、同鍵活性衝突以唯一索引 23505 兜底收斂為業務拒因）。
3. **Given** 已刪選單其父已刪，**When** 復原，**Then** 顯式拒（父層未刪重驗）。
4. **Given** 復原成功，**Then** 成對清空 `deleted_at`／`deleted_by`、原 `status` 保留、
   零 casbin 寫、零判定面同步；復原後之可見性授權屬授權治理刀（已知態③）。

---

### User Story 4 - 刪除選單後殘留授權即時失效（判定面同步） (Priority: P2)

管理員刪除選單（或自 buttons 欄移除絕版碼）後，被歸檔的授權在**判定面**即時失效——不會出現
「資料庫已歸檔、記憶體殘留政策仍在生效」的窗；同步失敗時系統保留上一份已知良好判定面並告警，
絕不進入全域拒絕狀態。

**Why this priority**: 島 H2「同鍵重建零繼承」的 in-memory 半邊；也是授權治理刀grant 面的共用基建。
失手模式（判定面清空）＝含超管全域鎖死、唯重啟可救——本刀最高風險件。

**Independent Test**: 測試種一列 live menu 維授權 → deleteMenu → 斷言 DB 歸檔**且**判定面
查詢不再命中（in-memory 面斷言）；注入壞連線使重建失敗 → 斷言舊判定面仍在生效（R_SUPER
既有授權續 allow）且結構化告警與 metrics 記錄。

**Acceptance Scenarios**:

1. **Given** 移除面寫端（deleteMenu／batchDeleteMenu／updateMenu-buttons）成功且有連動歸檔，
   **When** 交易 commit 後，**Then** 觸發判定面重建同步；被拒／無作用／無 buttons 變更不觸發。
2. **Given** 重建過程任一步失敗，**Then** 不產出新判定面、保留舊面、結構化告警＋計數；有界
   重試（次數與退避為寫死常數）耗盡仍失敗＝維持舊面持續告警。
3. **Given** 同 `route_name` 刪後重建，**Then** 新選單不經任何路徑（現役殘留、in-memory 殘留、
   回收桶復原）繼承舊實例授權（DB 面＋判定面雙斷言）。
4. **Given** deleteRole 成功，**Then** 不觸發判定面同步（in-use 守門保證刪除時零掛載、殘留
   無授權效果——rev4 as-built 同形；本刀 ADR 記載論證）。

---

### User Story 5 - 角色首頁指定 (Priority: P3)

超級管理員讀取／指定某角色的首頁路由；寫端不驗「首頁是否在該角色可見樹內」的一致性（讀端
兜底既有：不在可見樹→先序第一葉，`resolve_home` 已交付）。

**Why this priority**: 小而獨立；rev4 拍板「寫端不驗一致性＋讀端兜底」照抄。

**Acceptance Scenarios**:

1. **Given** 角色 R，**When** 讀取其首頁設定，**Then** 回現值；**When** 寫入任一路由名，
   **Then** 落庫成功（不驗可見性一致）、同交易稽核。

---

### Edge Cases

- **已知態三組（授權治理刀收刀前；CDP 對照排除清單＋煙測判準）**：①role 頁「菜單權限／按鈕權限」
  兩鈕仍 demo stub（寫死 button1..button10 假資料、點開 modal 顯示假樹）②policy-archive 選單項
  仍死項（側欄零反應＋原始 i18n key，與 B-008 既有死項同形）③新建／復原選單無法授予側欄可見性
  （含 R_SUPER）——管理列表可見可編、側欄不現。
- **getAllRoles 零 UI 消費者窗**：本刀 as-shipped 無前端呼叫點（menu modal 之 upstream 殘留
  呼叫不帶〔FR-045〕、user 頁角色指派屬刀 B）——UI 消費者隨刀 B 進場；契約、授權態與測試
  照常交付（clarify Q3 拍板）。
- **守門兩腿生產面窗（grilling G6 註記）**：deleteRole 之 in-use 與 self-role 兩腿在刀 B
  （user 角色指派寫端）落地前無生產面觸發路徑——新建角色無工具可指派（永零掛載）、seed 角色
  被 seeded 腿先擋；測試以直種 `sys_user_role` 指派列構造觸發（資料態、零測試旗標）。
- **empty body**：POST／DELETE 寫端收空 body ⇒ 授權中介層照常判定（middleware 不觸 body），
  body 解析失敗依既有 wire 慣例回 3333 家族——不得為此把守門前移進 middleware。
- **請求上下文缺席**：寫端稽核列之來源欄不可得 ⇒ 拒寫 5000（rev5 既定、F3① 同向；不帶回
  rev4 的放行形）。
- **restore 冪等**：復原一條現役中（未刪）選單＝業務錯誤（rev5 既定；不帶回 rev4 冪等成功形）。
- **停用選單的授權語意**：停用＝暫時下架非撤銷；治理域讀端含停用列，防「全量替換將停用選單
  diff 掉＝停用靜默升級為永久撤銷」（rev4 血淚、必配測試）；此不變式的主要消費者（三維授權
  寫端）在授權治理刀，本刀交付治理域讀端的正確性測試。
- **幽靈父收縮**：停用／軟刪目錄使其可見子樹整棵收縮（不下發亦不升根）——rev5 既有拍板、
  本刀寫端不得改變此讀端語意。
- **併發**：選單域寫端（含 deleteRole）同時進域＝序列化執行；域鎖等待以 pg_locks 之 advisory
  NOT-granted 等待者觀測（非 pg_blocking_pids；64-bit key 於 pg_locks 拆 classid／objid 兩欄，
  bigint 直比恆假——機器證測試之已知坑）。
- **`sys_role_id_seq` × schema-gate**：gate2 對該序列有 setval 期望值 3，而 addRole 寫端會推進
  序列——兩者互動 tasks 早期顯式查證（brainstorm §6 簿記地雷③）；測試一律顯式大 id 避開。
- **測試殘列**：`sys_role`／`sys_menu`／`casbin_rule` 皆不在 schema-gate 收窄集、gate2 逐列
  diff ⇒ 測試必配清理守衛＋守衛自證測（Drop 寫壞＝靜默恆綠之防；B-085 紀律）。

## Requirements *(mandatory)*

### Functional Requirements

#### A. 端點與契約總則

- **FR-001**: 本刀 MUST 新增恰 16 支端點且 path×method 逐字對齊 001 凍結 seed 政策列（零新
  seed、零 migration）：role CRUD 6（getRoleList／getAllRoles／addRole／updateRole／deleteRole
  ／batchDeleteRole）＋menu CRUD 7（getMenuList/v2〔字面含 `/v2`〕／addMenu／updateMenu／
  deleteMenu／batchDeleteMenu／getDeletedMenus／restoreMenu）＋roleHome 2（getRoleHome／
  updateRoleHome）＋getMenuTree；動詞分布 GET 7／POST 5／DELETE 4，路由註冊表條數常數同
  commit 對齊（22→38）。
- **FR-002**: 分頁列表回應 MUST 採共用分頁信封；該信封 MUST 自現寄居處上移至共用層（本刀
  一次帶來三個分頁端點＝其預告之「第二消費者」時點），既有消費者同步改引、契約測試跟隨。
- **FR-003**: 部分更新請求 MUST 遵守既有三態語意（欄位缺席＝不動／null＝清空／有值＝設值；
  ADR 0023）；全 None（無任何有效變更欄）MUST 提前 no-op（不 bump 時戳、不落稽核）。
- **FR-004**: 一切業務拒因 MUST 為純 i18n key、一因一鍵（無攜參明細）；不得新增錯誤碼
  （13 碼矩陣凍結面不動）。
- **FR-005**: 寫端操作稽核 MUST 與業務寫入同一交易落地；稽核操作詞彙沿既有小寫封閉詞彙
  （add／update／delete／restore 直接沿用；標的表由 `entity_table` 區分——T005 定案：
  零新 variant、詞彙集維持恰五值），不得帶回 rev4 大寫 DB 動詞形。
- **FR-006**: 授權態照 seed：寫端全 R_SUPER；getRoleList 另授 R_ADMIN、getAllRoles 另授
  R_ADMIN＋R_USER_COMMON；getMenuTree／getMenuList/v2／getDeletedMenus／restoreMenu 等
  照 seed 政策列逐列對齊，不多授不少授。

#### B. 角色 CRUD

- **FR-007**: getRoleList MUST 提供分頁＋名稱／代碼模糊＋狀態等值篩選；回應逐欄構造白名單
  （絕不序列化 raw model）、含 `roleMemo` 欄；穩定排序 `id ASC`。
- **FR-008**: getAllRoles MUST 僅回活性且啟用之角色（下拉用）且 MUST NOT 帶 memo 欄。
- **FR-009**: addRole MUST 驗 `roleCode` 形制 `^[A-Za-z0-9_]{1,64}$` 與活性代碼唯一；成功後
  該角色零授權（授權經授權治理刀面板；本刀已知態）。
- **FR-010**: updateRole：`roleCode` MUST 不可變（提交變更＝顯式拒、非靜默忽略）；停用 MUST
  過雙護欄——操作者不得停用自己所屬角色、R_SUPER 恆禁停用（不因操作者身分而異）；停用即斷權
  沿基線行為（授權讀端已濾 status）。
- **FR-011**: deleteRole MUST 依固定序三層守門：①seeded（id 常數集，本刀建 `SEEDED_ROLE_IDS`
  ／`SUPER_ROLE_CODE` 常數）②in-use（掛載計數採 `others = total − operator_is_member` 精修、
  拒因語意回誠實總掛載）③self-role（操作者所屬角色不可刪）；通過後同交易掃 `v0=role_code`
  全三維（含 protected 列）archive-move（reason=`role_soft_delete`、不可復原）＋操作稽核。
  角色刪除單向：本刀與授權治理刀皆無 role restore。
- **FR-012**: batchDeleteRole MUST 單一交易、id 升冪逐項全套守門、任一違規整批拒（no-partial）。
- **FR-013**: deleteRole／batchDeleteRole MUST 進選單序列化域（rev5 新增域成員；消滅與
  deleteMenu 寫同批 casbin_rule 列的併發窗）且 MUST NOT 觸發判定面同步（免 reload 論證入 ADR）。
- **FR-014**: roleHome：讀端回現值；寫端落庫不驗可見樹一致性（讀端兜底既有）、同交易稽核。

#### C. 選單域結構不變式（島 H 入憲面）

- **FR-015**: `routeName`／`menuType` 建後 MUST 不可變——寫端顯式拒、MUST NOT 靜默忽略。
- **FR-016**: 改父／新增 MUST 防環（上溯祖先鏈遇自身即拒；上溯上限為寫死常數）。
- **FR-017**: 父驗證 MUST 三處一致（新增／改父／復原）：父存在且未刪；**停用不擋**；
  `parentId=0`（頂層）豁免。
- **FR-018**: 常量父鏈守門（rev5 專屬、島 H3 增補）：`constant` 欄可寫，但常量選單 MUST NOT
  掛於 `constant` 非 TRUE 之父下——寫端於寫入前驗父鏈常量性、違反顯式拒。
- **FR-019**: 讀端 MUST 分治理域（未刪含停用；管理列表／父選擇器／授權候選之源）與顯示域
  （啟用且未刪；既有 list_active）；治理候選 MUST NOT 誤用顯示域（防停用被全量替換靜默升級
  為永久撤銷——必配負向測試）。
- **FR-020**: 同鍵重建零繼承（島 H2）：同 `routeName` 重建之新選單 MUST NOT 經任何路徑
  （現役殘留、判定面殘留、回收桶復原）繼承舊實例授權——雙封＝現役無殘留（序列化域＋刪除
  連動歸檔掃盡）＋歸檔不可回灌（reason gate）；本刀含判定面同步 ⇒ in-memory 面同受此約束。
- **FR-021**: 幽靈父收縮語意 MUST 維持現狀（停用／軟刪目錄之可見子樹整棵收縮；改判＝翻案
  程序）。

#### D. 選單 CRUD

- **FR-022**: getMenuList/v2 MUST 治理域、樹形、分頁以頂層計（size 上限 clamp 常數與前端
  hook 呼叫形對齊——plan 期釘死）；回應含 `menuMemo` 欄。
- **FR-023**: getMenuTree MUST 治理域輕量樹（父選擇器消費）；與 getMenuList/v2 同源同語意。
- **FR-024**: addMenu MUST 支援目錄／選單兩型、可寫 buttons（jsonb 直傳）與 constant 欄；
  `routeName` MUST 驗活性唯一（域鎖內先驗顯式拒＋基線部分唯一索引 23505 兜底收斂為同一
  業務拒因）；
  零 casbin 寫（兩步流第一步；可見性授權屬授權治理刀）。
- **FR-025**: updateMenu 之 buttons 變更：自欄移除且**絕版**（不再屬任何未刪選單〔含停用〕之 buttons 聯集＝治理域聯集）
  之 button 碼 MUST 同交易絕版歸檔（reason=`menu_button_removed`、不可復原）並觸發判定面
  同步；非絕版移除（他選單仍持有該碼）MUST NOT 歸檔。
- **FR-026**: deleteMenu MUST 依固定序守門（受保護→存在未刪子項〔不論啟停〕）；通過後同交易
  掃 `v1=routeName AND v2='menu'` 跨全角色歸檔＋獨有 button 碼一併歸檔（兩者 reason 皆＝
  `menu_soft_delete`）＋操作稽核＋觸發判定面同步。
- **FR-027**: batchDeleteMenu MUST child-first 拓撲序、逐項全套守門、任一違規整批拒、單一交易。
- **FR-028**: getDeletedMenus MUST 回已刪集合；穩定排序 `deleted_at DESC, id DESC`；
  ★不帶 `restorable` 旗標——選單復原無 reason gate 概念（該概念屬授權歸檔）、復原守門即
  唯一權威（契約 wire-menu-admin §7；analyze I1 修正原誤植）。
- **FR-029**: restoreMenu MUST 域內鎖列重驗（標的已刪存在／同鍵活性衝突〔23505 兜底收斂為
  業務拒因〕／父層未刪）→成對清空 `deleted_at`／`deleted_by`、原 `status` 保留；MUST NOT
  回灌任何授權、零 casbin 寫、零判定面同步；同交易稽核。

#### E. 序列化域與鎖序

- **FR-030**: 選單域 MUST 以單一 DB 交易級 advisory 鎖為載體（key＝`0x7265_7635_6D65_6E75`、
  ASCII `"rev5menu"`；常數留活書可調）；進域寫端＝選單 5 寫端（add／update／delete／batch／
  restore）＋deleteRole／batchDeleteRole；授權治理刀屆時加入其 grant 面寫端（條文寫終態、本刀期間
  該等端點不存在＝vacuous 成立）。
- **FR-031**: 域鎖 MUST 為交易首動作、MUST NOT 下沉至資料存取層內（下沉即破鎖序）；固定鎖序
  ＝`advisory → 歸檔表列 → sys_role 列 → sys_menu 列 → casbin_rule`。
- **FR-032**: 與既有 per-user advisory 鎖（登入／換發用、uid 為 key）MUST 維持結構性無 ABBA
  （key 空間不碰撞＋鎖集合零交集）；三個失效條件（role 寫端連動撤 session／刀 B user 寫端
  進場／同 key 重入）記入 ADR。
- **FR-033**: 序列化有效性 MUST 有機器證：兩寫端併發時後者於 advisory 等待（以 pg_locks 之
  NOT-granted 列斷言；classid／objid 拆讀）。

#### F. 授權歸檔寫入面與 reason gate

- **FR-034**: 歸檔寫入 MUST 完整快照政策列＋來源角色識別（`role_id`，nullable 照 rev4——
  `role_code` 查無活角色時誠實退化寫 NULL）＋reason；歸檔表結構零變更（三自由度全不動、
  rev4:0049 翻案觸發條款過境本刀 ADR）。
- **FR-035**: 不可復原 reason 集合 MUST 為單點函式承載（`{role_soft_delete, menu_soft_delete,
  menu_button_removed}`）、同時供列表旗標（非權威）與復原權威判定（授權治理刀消費）共用——防兩處
  漂移；本刀配集合成員測試。
- **FR-036**: 歸檔讀端（getArchivedPolicies）與 restorePolicy 不在本刀（授權治理刀射程）。

#### G. 判定面同步（rebuild-swap 基建）

- **FR-037**: 判定面同步 MUST 採重建-swap：另建全新判定面（四步鏡像 init）、任一步失敗整體
  失敗不產出實例、成功才於寫鎖臨界區一步換值；MUST NOT 對現役判定面就地清空重載（裸呼
  load_policy 禁令＋casbin 2.20.0 版本鎖註解——升版必重核 clear-then-load 語意）。
- **FR-038**: 同步失敗 MUST keep-last-good：保留上一份已知良好判定面＋結構化告警＋metrics
  三 outcome（ok／retry／exhausted）；有界重試（`RELOAD_MAX_ATTEMPTS=3`＋線性退避 50ms，
  寫死常數、絕不取自輸入）；耗盡仍失敗＝維持舊面持續告警、服務不中斷。
- **FR-039**: 觸發時機 MUST 恰為：移除面寫端成功且有連動歸檔、於交易 commit 之後；被拒／
  無作用／標的不存在／無 buttons 變更 MUST NOT 觸發（早退結構性保證）。
- **FR-040**: 本刀 MUST 交付四支同步測試：失敗注入（壞連線⇒舊面續 allow R_SUPER）／
  「改寫為裸呼 load_policy 必轉紅」負向自證／觸發條件特性鎖定／移除面端到端（含 in-memory
  面斷言）；`enforce.rs` 之「不再重載＝終態」宣告以 ADR 翻案並更新註解。

#### H. 前端

- **FR-041**: role 頁與 menu 頁 MUST 接真後端（列表／搜尋／新增編輯抽屜或 modal／刪除批刪／
  回收桶 toggle）；修改型檔集恰＝role 3 檔（index.vue／role-operate-drawer.vue／role-search.vue）
  ＋menu 2~3 檔（index.vue／menu-operate-modal.vue／shared.ts 視需要——定數於 Amendment 起草時判定
  〔tasks T001 前置半步〕），逐行 `原行:` 標記；
  `menu-auth-modal.vue`／`button-auth-modal.vue` MUST 一行不動（授權治理刀射程；檔級硬邊界）。
- **FR-042**: 選單回收桶 UI MUST toggle 形（「顯示已刪除」開關換資料源 getDeletedMenus、
  已刪模式操作欄整欄換復原）；復原鈕無按鈕碼 gating（門＝頁級＋列級）。
- **FR-043**: memo 兩欄 MUST 兌現於管理列表與編輯入口（role 列表欄＋drawer textarea、menu
  列表欄＋modal textarea；照 004 wbip_memo 範式：純文字插值、無原始 HTML 插值）；置入
  placeholder 註明「管理員可見」；被取用處（getAllRoles 下拉、路由樹）MUST NOT 帶 memo。
- **FR-044**: API wrapper／typings MUST 新增型新檔（獨立命名空間、`createdBy` enrich 形照
  004 慣例）；demo 頁欄定義隨改；id 序列化逐欄忠實 typings（憲法 §I.3）。
- **FR-045**: `menu-operate-modal` 之 upstream 殘留 `fetchGetAllRoles` 呼叫 MUST NOT 帶入
  （template 零消費欄）；父選擇器改消費 getMenuTree。
- **FR-046**: i18n MUST 三處同補（兩語 locale＋型別樹＋zh-tw 治理字典、跨端契約 lint 過閘）：
  menu 頁補 showDeleted／confirmRestore（自有鍵；與授權治理刀policyArchive 鍵收斂屆時議）＋本刀
  CRUD 面拒因鍵（`backend.biz.role.*`／`biz.menu.*`）；route 鍵三支 upstream 已在、零新增。
- **FR-047**: 前端路由 static meta MUST 以 DB seed 為唯一真源、不維護 static 側同步（一句
  紀律、不建閘）；路由外掛產物四檔本刀零變動（不新增 view 頁）。

#### I. 治理與簿記

- **FR-048**: 憲法 Amendment MUST 一次 MINOR（v1.6.2→v1.7.0）：島 H 五條全文入憲（含
  advisory key space 全域唯一句＋常量父鏈句；MAJOR 界定照 rev4 字面；常數留活書）＋
  `MANAGE-PAGE-WIRING` 加用途 (ii)（本刀實改檔逐支列出）＋B-087 殘餘②補註（逐字形、
  不單獨 bump）；Amendment 為 U1 級前置（先於一切碼變更）。
- **FR-049**: ADR MUST 三支：島 H 入憲／判定面同步翻案（含 reload 契約＋硬禁令與版本鎖＋
  ABBA 三失效條件）／A1 域行為（deleteRole 入域＋免 reload 論證＋島 G1/G3/G4/G5 行為先由
  ADR 承載條文隨授權治理刀入憲＋archive 三自由度 won't-use 與 0049 條款過境）。
- **FR-050**: 測試 MUST 配三表清理守衛＋守衛自證測（造 committed 列→前提自證非零→Drop→
  回零；sequence 還原斷言）；`sys_role_id_seq` × gate2 setval 互動為 tasks 早期顯式查證項；
  seed 78 列寫死之既有測試不得因本刀而動（本刀零 seed 變更）。
- **FR-051**: 本刀零 migration、零 seed 變更 MUST 成立（migration 目錄維持恰兩支）；收刀
  毋須跑 schema refresh 三步。

### Key Entities *(include if feature involves data)*

- **sys_role（角色）**: 授權模型軸心；代碼（不可變、形制受驗、活性唯一）、名稱、描述、狀態
  （啟用／停用）、備註（`role_memo`、R_SUPER 書寫、管理列表可見）、軟刪欄；seed 三列受結構
  護欄；停用即斷權。
- **sys_menu（選單）**: 樹狀實體（`parent_id`、防環）；路由鍵 `route_name`（授權錨、不可變）、
  型別 `menu_type`（不可變）、`buttons`（按鈕碼聯集、jsonb）、`constant`（常量選單旗標、
  父鏈常量性受守）、`menu_memo`、啟停、軟刪欄；治理域／顯示域雙讀面。
- **casbin_rule（授權政策）**: 授權真相（DB-first）；本刀僅移除面觸及（刪除／絕版連動歸檔）；
  protected 治理欄對 adapter 不可見、判定走自建面。
- **sys_casbin_policy_archive（授權歸檔）**: revoke＝archive-move 之落點；完整快照＋
  `role_id`（nullable）＋reason；不可復原三 reason 由單點 fn 承載；本刀建寫入面、讀端歸授權治理刀。
- **選單序列化域（概念實體）**: 單一 advisory 鎖承載的互斥執行域；成員＝選單 5 寫端＋
  deleteRole 家族（＋授權治理刀grant 面）；固定鎖序之首動作。
- **判定面（enforcer）**: casbin in-memory 判定實體；由真相全量導出；重建-swap 同步、
  keep-last-good、絕不就地清空。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 路由註冊表恰 38 條且與 seed 政策列 path×method 逐字對齊（機器對賬零漂移）；
  16 支新端點以 dev 帳號實測全通（授權態照 seed：Admin 對寫端得拒、對 getRoleList 得通）。
- **SC-002**: rust 測試總數自 512 淨增且全綠（容器內 serial 全量、rc=0）；其中含四支判定面
  同步測試、序列化域機器證、三層守門固定序、同鍵重建零繼承端到端（DB＋in-memory 雙斷言）、
  守衛自證測——負向自證（拆掉正解必轉紅）逐項可示範。
- **SC-003**: CDP 三方對照（22080 vs 42080）role 頁與 menu 頁主流程逐項一致（列表／新增／
  編輯／刪除／批刪／回收桶 toggle／memo 欄）；已知態三組列排除清單且逐項驗證其現狀（兩鈕
  假資料、死項零反應、新建選單側欄不現）。
- **SC-004**: 零 migration 兌現：migration 目錄維持兩支、schema-gate 三閘照常綠、
  `list_active_reads_seed_78_rows` 等 seed 寫死測試零改動。
- **SC-005**: 憲法 v1.7.0（島 H 五條＋軌道用途 (ii)＋B-087 補註）；lint 全綠（0 錯誤）；
  fork-delta：修改型標記僅出現於 FR-041 所列檔集，兩顆授權 modal 零 diff。
- **SC-006**: 判定面失敗注入下服務不中斷：R_SUPER 既有授權續 allow、告警與 metrics 落點
  可查、耗盡後行為＝維持舊面（無任何全域拒絕窗）。

## Assumptions

- rev4 樹（`../fork260509-rev4/`）為唯讀活體藍本：spec 對應＝specs/rev4:009-role-admin
  （role CRUD／roleHome 段）＋specs/rev4:010-menu-admin 全套；as-built 碼清單於 plan research
  凍結（ADR 0019）；rev5 已明文推翻之行為不得帶回（brainstorm §9 差異點清單）。
- authz-governance 依賴本刀底座（序列化域／判定面同步／歸檔寫入面／reason gate／治理域
  讀端）；本刀「條文寫終態、行為先 ADR 承載」之島 G 各條由授權治理刀轉正。
- 單副本部署前提（ADR 0014）；判定面同步不需跨副本廣播。
- seed 政策列與選單列凍結不動；dev 環境（容器內 build/test、serial）；CDP 對照環境照
  CLAUDE.md §7。
- 刀 B（user＋password）另開；其 scope 已預拍（全納入含 changePassword）、B-089／B-021／
  B-020 連鎖在彼。

### Out of Scope

- 三維授權治理（getRoleMenu／updateRoleMenu／getRoleButton／updateRoleButton／
  getRoleEndpoints／updateRoleEndpoints）＋支撐讀（getAllButtons／getAllEndpoints／
  getAllPages）＋授權回收桶（getArchivedPolicies／restorePolicy）——授權治理刀。
- 結構性封死（治理面 protected 端點不得授予非 R_SUPER）與 orphan skip——授權治理刀。
- 島 G 條文入憲、policy-archive 新頁、兩顆授權 modal 做真——授權治理刀。
- no-escalation 真邏輯（空 seam 恆 Ok 不動、留翻案刀）。
- user 域一切（含 sys_user memo 欄、角色指派、密碼面）——刀 B。
- 列表排序能力（B-027 續掛）、`real_ip` gist 索引（B-082 續掛）、審計列表頁（B-008 餘兩張）。
