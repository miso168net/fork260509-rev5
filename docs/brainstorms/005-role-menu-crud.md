# 005-role-menu-crud — role＋menu 管理 CRUD 寫端（刀 A1）

> 階段 0 brainstorm 定稿（2026-08-18）。本檔與 [006-authz-governance.md](006-authz-governance.md)
> 為**同一次 brainstorm 的拆刀產物**（原單刀「刀 A＝role+menu」沿縫 α 裁開；拆刀由 user 拍板）。
> 基準＝rev5-admin-root @ f690642（憲法 v1.6.2、ROUTES 22、rust 測試 512）。
> research 原料＝session scratchpad `f005-research/`（C1 690 行＋D1~D6 2128 行＋E1 771 行；
> 兩輪 workflow 共 18 支 agent，rev3／rev4 兩樹唯讀偵查）。

## §0 拆刀縫（why 兩把刀）

**縫 α 分水嶺＝「grant/revoke 寫 casbin_rule」**：本刀（A1）**零 grant 面**——三維授權治理
（grant 面）＋結構性封死＋授權回收桶全歸 006。★熱重載**基建**在本刀（grilling G1 修正原案）：
rev4 的 menu 移除面三支（deleteMenu／batchDeleteMenu／updateMenu 之 buttons 絕版歸檔）依
FR-016 **MUST reload**（rev4:handler/menu.rs:329/348/364 三呼叫點）——reload 基建屬 rev4 009
早段、010 消費，原拆刀誤分到 006；照 rev4 平移 rebuild-swap 於本刀落地（§4-⑤），A1 的
reload 僅由移除面歸檔觸發。deleteRole 免 reload 照 rev4 as-built（in-use 守門保證刪除時
零掛載、記憶體殘留無授權效果）。**已否決的縫 γ**（role|menu 分刀）：域鎖橫跨兩域＋
`getAllButtons` 真源＝`sys_menu.buttons` ⇒ 硬耦合不可拆。

**本刀（A1）產出底座、006 消費**：advisory 序列化域、**casbin rebuild-swap 熱重載**、
archive facade（寫入面）、reason gate、治理域讀端、role／menu handler 檔。

## §1 背景與觸發

- NOTES「最強候選＝後端 role／user 管理寫端」→ user 拍板切法：**A1（本檔）＝role＋menu CRUD**、
  A2＝006 三維授權治理、刀 B＝user＋password（另開；user 已預拍「全納入含 changePassword」）。
- 消化帳目（本刀部分）：B-025 消掉一個預定客戶（deleteRole×deleteMenu 併發窗，經入域消滅）、
  B-087 殘餘②（隨本刀 Amendment 順捎）、B-003 之 role_memo＋menu_memo 兩欄（本刀兌現——grilling G5；餘 sys_user→刀 B）、
  B-091（rider）。B-024／B-008 policy-archive 歸 006。
- rev4 藍本＝specs/009-role-admin（role CRUD 部分）＋010-menu-admin（全套 32 FR／26 T）。

## §2 射程：16 支端點（ROUTES 22→38；seed 政策列 100% 預埋、零 migration）

**role CRUD（6）**：getRoleList(GET, seed 12/13＝SUPER+ADMIN)、getAllRoles(GET, 14/15/16＝三角色)、
addRole(POST, 21)、updateRole(POST, 22)、deleteRole(DELETE, 23)、batchDeleteRole(DELETE, 24)。

**menu CRUD（7）**：getMenuList/v2(GET, 25；★字面帶 `/v2`、逐字對齊 seed)、addMenu(POST, 28)、
updateMenu(POST, 29)、deleteMenu(DELETE, 30)、batchDeleteMenu(DELETE, 31)、
getDeletedMenus(GET, 64★protected)、restoreMenu(POST, 65★protected)。

**roleHome（2）**：getRoleHome(GET, 34)、updateRoleHome(POST, 35)——零 casbin 寫；
讀端兜底 `resolve_home` rev5 已交付（handler/route.rs:173）。

**治理域支撐讀（1；grilling G4 自 006 移入）**：getMenuTree(GET, 27)——治理域（未刪含停用）；
rev4 menu-operate-modal 之父節點選擇器逐字消費 `fetchGetMenuTree`、本刀 menu 頁做真即硬相依。

- 動詞：GET 7／POST 5／DELETE 4——router 打錯動詞即該端點全域 5003。
- 授權態：寫端 seed 全 R_SUPER；getRoleList 下放 R_ADMIN、getAllRoles 下放至 R_USER_COMMON（讀端）。
- ★中間期已知態三組（006 收刀前）：①role 頁「菜單權限／按鈕權限」兩鈕仍 demo stub（寫死
  button1..button10 假資料）②policy-archive 選單項仍死項——與 B-008 既有三死項同形
  ③**addMenu 新建／restoreMenu 復原之選單無法授予可見性（含 R_SUPER——MODEL_CONF 無旁路、
  機器驗證）**：側欄不現、管理列表照常可編（兩步流第二步工具晚一刀、與 rev4 第一步後狀態
  同形；grilling G2）。三組皆入 spec 已知態節與 CDP 對照排除清單。

## §3 拍板全紀錄（與 006 共享全文；「歸屬」欄標各條主要落點）

### user 親決 15 題（2026-08-18）

| # | 題 | 結論 | 歸屬 | 關鍵理由 |
|---|---|---|---|---|
| 1 | 刀怎麼切 | 刀A=role+menu、刀B=user+password；刀 A 再沿縫 α 拆 005/006 | 全 | ADR 0051 序列化域硬耦合（menu×三維授權同域）；島 H→005、島 G→006、島 I→刀 B |
| 2 | 前端腿 | 前後端同刀（各子刀內保持） | 全 | 可 CDP 對照驗收；修憲躲不掉（島必入憲） |
| 3 | 三維授權治理 | 納入刀 A（拆刀後＝006 全部射程） | 006 | 一次做完 rev4 009；熱重載連帶必答 |
| 4 | （刀 B 預拍）自助改密 | 全納入含 changePassword | 刀 B | 五前置中三項本就要建，增量僅四樣 |
| 5 | 授權模型深度（B-024①） | **結構性封死授出**：治理面 12 支 protected 端點 MUST NOT 授予非 R_SUPER；違者顯式拒 | 006 | 唯一非 vacuous（真擋得到、測試零旗標、符 ADR 0024）；直堵 K1-63 的洞 |
| 6 | casbin 熱重載 | **照搬 rev4 重建-swap** | **005 建基建、006 消費**（grilling G1 修正） | 同版 casbin 2.20.0、論證與 SC-013 骨架整套平移；enforcer 為 AppState 既有欄；menu 移除面依 rev4 FR-016 MUST reload |
| 7 | 治理拒因明細（B-024③） | **全降級純 key；島 G2 條文不綁載體** | 全（A1 拒因同純 key） | 守 2026-08-08 親決；protected 集靜態＋super-only ⇒ 自查等價成立；攜參形留擴充＝刀 B 屆時開不算翻案 |
| 8 | deleteRole 入域 | **拉進序列化域**（batch 同） | **005** | 消滅 rev4 零論證的 deleteRole×deleteMenu 併發窗；治理 QPS≈0 代價≈0 |
| 9 | updateRoleButton 候選驗證 | **加 orphan skip**（對稱 menu 維） | 006 | 同一道過濾零新設計；wire 與 rev4 相容；堵孤兒列 |
| 10 | archive 表三自由度 | **全不動**（nullable／不加 protected 快照／不加 menu_id） | **005**（建表消費者） | 保零 migration；誠實退化路徑保留；防的狀態結構性不可達；reason gate 已足 |
| 11 | constant 欄 | **可寫＋父鏈常量性守門**（島 H3 增補） | **005** | 與 rev4 UI 對齊；守門成本低；防 getConstantRoutes（Public）外洩面 |
| 12 | restore 按鈕碼 gating | **不 gating**（頁級 R_SUPER＋列級 restorable） | **005** | 基線 seed 已拍此形（有 user:restore 無 menu:restore）；保零 migration |
| 13 | 選單回收桶 UI | **toggle 形照 rev4**（獨立端點 getDeletedMenus） | **005** | CDP 基準對得上；用上預埋 seed 列 id64；樹表混排層級語意難定 |
| 14 | static meta 紀律 | **DB 唯一真源、不維護 static meta**（spec 一句紀律、不建閘） | 全 | dynamic 模式 fallback 影響≈0 |
| 15 | 修憲次數 | 原拍「一次 MINOR 落兩島」；**拆刀後自然變各刀一次**——005 落島 H（v1.6.2→v1.7.0）、006 落島 G（v1.7.0→v1.8.0） | 全 | 一刀一次 Amendment＝rev5 既有範式 |

### 主線自拍（回報備查）

- 域鎖 key＝`0x7265_7635_6D65_6E75`（ASCII `"rev5menu"`；rev4 字面 `"rev4menu"` 照抄即留錯世代名）｜005
- `PageRes<T>` 上移 `envelope.rs`（ip_rule.rs:71 逐字預告「第二個列表端點出現時上移」；
  本刀即來三個分頁端點：getRoleList／getMenuList/v2／getDeletedMenus）｜005
- no-escalation 空 seam（enforce.rs:92）恆 Ok 不動——掛點、metrics 位、測試旗標保留給未來翻案刀｜全
- 結構性封死拒因＝既有 `2222`＋新 i18n 鍵（零新錯誤碼）｜006
- `menu-operate-modal` 的 `fetchGetAllRoles`＝upstream 殘留（template 零消費欄）、不帶｜005
- 三維 modal 觸發鈕不做 hasAuth gating（照 rev4）｜006

### grilling 輪六題（user 親決 2026-08-18、/grilling 盤問 005 定稿後；與 006 共享）

| # | 題 | 結論 | 關鍵理由 |
|---|---|---|---|
| G1 | 熱重載基建歸屬 | **移入 005**、006 變純消費 | rev4 FR-016：menu 移除面三支 MUST reload（handler/menu.rs:329/348/364）；基建屬 rev4 009 早段、原拆刀誤分 006；總量不變、島 H2 乾淨入憲零已知違憲窗、最高風險件先在 005 驗證 |
| G2 | 選單可見性窗 | 接受＝已知態 | MODEL_CONF 無 R_SUPER 旁路（機器驗證）；本質＝兩步流第二步工具晚一刀；替代案（updateRoleMenu 提前）＝破縫 α |
| G3 | 前端檔清單 | 照實拆列：005＝role 3＋menu 2~3、兩授權 modal 一行不動留 006 | 憲法檔級名單＝硬邊界，多列＝授權未發生的修改 |
| G4 | getMenuTree 歸屬 | 移入 005（16 支／006 11 支） | rev4 menu modal 父選擇器逐字消費；治理域讀端同單元順帶、近零成本 |
| G5 | memo 欄 | 005 兌現 role_memo＋menu_memo、列表顯示不濾受眾 | wbip_memo 範本現成；受眾濾為備註欄開新機制不成比例；R_ADMIN 可見寫進 placeholder；getAllRoles 等被取用處不帶 |
| G6 | 守門兩腿窗 | 接受照建＋spec 註記 | in-use／self-role 生產面觸發隨刀 B 進場；資料態可測零旗標＝非 vacuous；拆段建＝同域分段長成 |

## §4 核心設計

**① 序列化域（島 H1；本刀建底座）**：`SELECT pg_advisory_xact_lock($1)` 走 raw Statement
（守 entity_access_lint）、xact 級自動釋放、零逾時零重試零 try_lock（rev4 底座僅 116 行）。
key＝`0x7265_7635_6D65_6E75`。**本刀進域**＝選單 5 寫端（add／update／delete／batchDelete／restore）
＋deleteRole／batchDeleteRole（rev5 新增成員、rev4 沒有）；006 屆時加入 updateRoleMenu／
updateRoleButton／restorePolicy。固定鎖序（rev4 逐字）：`advisory → sys_casbin_policy_archive 列 →
sys_role 列 → sys_menu 列 → casbin_rule`；域鎖必為 txn 首動作、不得下沉 facade fn。
與 per-user advisory 鎖（login.rs:519、uid 為 key）：key 不碰撞（高位 ASCII 常數 vs 個位 bigserial）、
鎖集合零交集 ⇒ 結構性無 ABBA；三個失效條件記入 ADR（role 寫端連動撤 session／刀 B user 寫端／
同 key 重入）。併發機器證兩坑：用 pg_locks 的 advisory NOT-granted 等待者（非 pg_blocking_pids）；
64-bit key 拆 classid（高32）＋objid（低32），bigint 直比恆假。

**② 刪除與歸檔（島 G3/G4 行為、條文隨 006 入憲、本刀以 ADR 承載）**：
- deleteRole：三層守門固定序（seeded hardcode → in-use → self-role；in-use 精修
  `others=total−operator_is_member`、拒因人數回誠實總掛載）→ 同交易掃 `v0=role_code` **全三維
  含 protected 列**做 archive-move（reason=`role_soft_delete`、不可復原）→ 同交易 op-log。
  角色刪除**單向、無 role restore**。批次 no-partial 單 txn、id 升冪。
- deleteMenu：守門固定序（受保護 → 存在未刪子項不論啟停）→ 掃 `v1=route_name AND v2='menu'`
  **跨全角色**歸檔＋**獨有 button 碼**一併歸檔（★兩者 reason 皆＝`menu_soft_delete`；
  rev4:sys_casbin_archive.rs:713 逐字「deleteMenu 獨有→menu_soft_delete」——grilling 修正
  原案誤植）。批刪 no-partial＋child-first 拓撲序。
- **updateMenu 之 buttons 變更（grilling 補進、原案漏列）**：自 buttons 欄移除且**絕版**
  （不再屬任何活選單 buttons 聯集）之 button 碼，其 casbin 政策同交易絕版歸檔
  （reason=`menu_button_removed`、不可復原；rev4 同檔 :713 逐字「updateMenu 絕版→
  menu_button_removed」）。
- **reload 契約（grilling G1）**：menu 移除面三支（deleteMenu／batchDeleteMenu／
  updateMenu-buttons）成功且有連動歸檔＝live-affecting ⇒ 照 rev4 FR-016 觸發 reload
  （rebuild-swap、§4-⑤）；被拒／無作用／無 buttons 變更不觸發。deleteRole 免 reload 照
  rev4 as-built（in-use 守門保證零掛載、殘留無授權效果）；addMenu／restoreMenu 零 casbin
  寫＝零 reload。`enforce.rs:8`／`main.rs:56`「不再重載＝終態」本刀以 ADR 翻案
  （理由子句「B12 沒有治理寫端」自本刀移除面起即不成立）。
- archive facade 寫入面＋**reason gate**（不可復原三值集 `{role_soft_delete, menu_soft_delete,
  menu_button_removed}`、單點 fn 供 list 旗標與 restore 權威共用防漂移）本刀建；讀端
  （getArchivedPolicies）與 restorePolicy 歸 006。

**③ 選單域狀態機（島 H 全五條隨本刀入憲）**：同鍵重建零繼承雙封（現役無殘留＋reason gate）；
route_name／menu_type 建後不可變（顯式拒、非靜默忽略）；防環（上溯祖先鏈遇自身拒、上限常數）；
parent 三處一致驗證（新增／改父／復原＝父存在且未刪、停用不擋、parentId=0 頂層豁免）；
治理域（list_governed＝未刪含停用）／顯示域（list_active 既有）分層——★rev4 血淚必配測試：
治理候選讀端誤用顯示域＝「停用靜默升級為永久撤銷」；復原不回灌（restoreMenu 域內鎖列重驗
〔同鍵活性衝突 23505 兜底、父層未刪〕→成對清空 deleted_at/by＋原 status 保留、零 casbin 寫
零 reload）；幽靈父收縮語意不動（改判＝翻案）；**constant 父鏈常量性守門**（rev5 專屬新條：
「選單寫端 MUST 於寫入前驗證常量選單之父鏈常量性；違反顯式拒」——防 getConstantRoutes
Public 端點外洩；現況 seed TRUE 0／FALSE 14／NULL 64＝零存量影響）。

**④ 其餘**：部分更新三態照 ADR 0023；全 None 提前 no-op；role code 形制 `^[A-Za-z0-9_]{1,64}$`
且不可變；停用雙護欄（不可停用自己所屬角色＋R_SUPER 恆禁停用「不因操作者身分而異」）；
停用即斷權已是基線行為（roles_of_user 濾 status=1）；拒因全純 key 一因一鍵；
R_SUPER／SEEDED_ROLE_IDS 常數本刀建（rev5 現缺）；memo 兩欄兌現（grilling G5）＝
`role_memo`／`menu_memo` 上管理列表 wire＋編輯入口，被取用處（getAllRoles 下拉／
getUserRoutes 路由樹）不帶、受眾不濾（R_ADMIN 經 getRoleList 可見、placeholder 註明）。

**⑤ casbin rebuild-swap 熱重載基建（grilling G1 自 006 移入）**：照 rev4 全套——
`rebuild_enforcer(db)` 另建全新 Enforcer（model→adapter→new→load_policy 四步鏡像 init）、
任一步失敗整體 Err 不產實例、成功才 write 鎖內一行 move-assign；`RELOAD_MAX_ATTEMPTS=3`＋
`RELOAD_RETRY_BACKOFF_MS=50` 線性退避（★常數寫死、絕不取自輸入）；keep-last-good＋結構化
告警＋metrics `casbin_reload_total{ok|retry|exhausted}`；耗盡仍失敗＝維持舊面持續告警。
★硬禁令＋版本鎖：**絕不對 live enforcer 裸呼 `load_policy`**——casbin 2.20.0（rev5 同版、
Cargo.toml:46 釘版）之 `load_policy`＝clear-then-load，空 policy 在 MODEL_CONF 下＝含
R_SUPER 全 deny、唯重啟可救；註解帶版本鎖、升版必重核。測試四支照 rev4：SC-013 壞 conn
注入（斷言舊面續 allow R_SUPER）／裸呼必轉紅負向自證／特性鎖定／端到端。★島 G1 條文
（失敗契約全文）照舊隨 006 入憲；本刀 reload 行為由本刀 ADR 承載（同 G3/G4/G5 模式）；
006 屆時純消費（grant 面 Applied 觸發同一支 reload）。

## §5 前端面

- 改 5~6 支 upstream 基線檔（修改型、逐行 `原行:`；grilling G3 照實拆列）：`views/manage/role/`
  3 檔（index.vue／role-operate-drawer.vue／role-search.vue）＋`views/manage/menu/` 2~3 檔
  （index.vue／menu-operate-modal.vue／shared.ts 視需要）。★menu-auth-modal.vue／
  button-auth-modal.vue 兩檔一行不動、留 006；role 頁兩鈕與 policy-archive 死項＝已知態（§2）。
- wrapper／typings（新增型）：`service/api/rev5-role-admin.ts`＋`rev5-menu-admin.ts`＋對應 d.ts；
  wire 型別照 004 開獨立命名空間（createdBy enrich 形）、demo 頁欄定義跟改；
  id 序列化逐欄忠實 typings（憲法 §I.3）。
- 回收桶 toggle 形（menu 頁「顯示已刪除」NSwitch 換資料源 getDeletedMenus）。
- memo 兩欄 UI（grilling G5）：role 列表欄＋drawer textarea、menu 列表欄＋modal textarea
  （照 004 wbip_memo 範本、純文字插值、view-render-guard 自動涵蓋；i18n 補對應欄位鍵）。
- i18n：menu 補 2 鍵（showDeleted／confirmRestore；★rev4 復原鈕文字復用 policyArchive.restore——
  該節屬 006，本刀 confirmRestore 先以自有鍵落、006 進場時再議收斂）；`backend.biz.role.*`／
  `biz.menu.*` 之 **CRUD 面拒因鍵**（三維／回收桶鍵隨 006）——兩語 locale＋app.d.ts 型節＋
  zh-tw.ts 治理字典三處同補、過 Lint24。
- static meta 不維護（DB 唯一真源、spec 記一句）；view-render-guard 自動涵蓋（零加接線）。

## §6 治理面

- **憲法一次 MINOR v1.6.2→v1.7.0**：島 H 五條全文入憲（H1 含 006 才兌現的授權寫端成員——
  條文寫狀態機終態、A1 期間該等端點不存在＝vacuous 成立、006 兌現零修憲；H1 另含
  advisory key space 全域唯一句；H3 含常量父鏈句；MAJOR 界定照 rev4 字面：拆散序列化域／
  部分成功／route_name·menu_type 可變／拔連動歸檔／回灌復原授權皆 MAJOR；常數留活書）＋
  §III.2 `MANAGE-PAGE-WIRING` 加用途 (ii)（role/menu 八檔逐支列出）＋**B-087 殘餘②補註順捎**。
- **ADR 草案配置**（U1 期定支數）：島 H 入憲一支；熱重載翻案一支（grilling G1 自 006 移入
  ——翻 enforce.rs:8／main.rs:56、含 reload 契約＋硬禁令與版本鎖＋ABBA 三失效條件）；
  A1 域行為一支（deleteRole 入域＋deleteRole 免 reload 論證＋島 G1/G3/G4/G5 行為先由
  ADR 承載、條文隨 006 入憲＋archive 三自由度 won't-use 及 rev4 0049 翻案觸發條款過境）。
- **帳務**：B-025 消掉 deleteRole 窗客戶（不關帳）；B-003 本刀兌現 role_memo＋menu_memo 兩欄（剩 sys_user→刀 B）；
  B-091 rider；wf-watchdog journal 無心跳盲點（本 session stall 假警報實暴）收刀落 LESSONS。
- **簿記地雷三顆（進 tasks）**：①sys_role／sys_menu／casbin_rule 測試清理守衛＋守衛自證測
  （B-085 紀律；三表皆不在 RUNTIME_APPEND_TABLES、gate2 逐列 diff）②`list_active_reads_seed_78_rows`
  寫死 78（本刀不動 seed ⇒ 不紅）③`sys_role_id_seq` setval 期望 3 × addRole 推進 seq 的 gate2
  互動——**tasks 早期顯式查證項**。

## §7 執行單元草案（~17 支；tasks 期定稿）

U1 憲法 Amendment（島 H）＋三支 ADR（主線親做）→ U2 Setup（handler 骨架／AuditOperation
擴詞彙／PageRes 上移）→ U3 域鎖底座＋ABBA 機器證 → U4 rebuild-swap 熱重載（SC-013 四測；
grilling G1 移入）→ U5 鎖讀 helper＋清理守衛＋自證測 → U6 治理域讀端（list_governed／
getMenuList/v2／getDeletedMenus／getMenuTree 讀面）→ U7~U8 role CRUD（facade TDD→
handler+router）→ U9~U11 menu CRUD 寫端＋回收桶＋constant 守門＋reload 接線 → U12 零繼承鏈
端到端（deleteMenu／updateMenu 歸檔＋同鍵重建＋reload 後 in-memory 面斷言；★防恆綠：先種
live 授權再測）→ U13 i18n 三處＋Lint24 → U14~U15 前端（role 頁＋memo／menu 頁＋toggle＋memo）→
U16 全量閘＋CDP 三方對照（22080 vs 42080；已知態三組排除）→ U17 收刀簿記。
編排慣例：implementer=fable 1m xhigh、review=opus 1m xhigh、防呆六件套。
高風險共享檔序列鏈：facade/sys_menu.rs、facade/sys_role.rs、facade/sys_casbin_archive.rs、
handler/role.rs、router.rs、tests/contract.rs。

## §8 風險與誠實界線

1. `sys_role_id_seq` × gate2 setval 互動未查證（tasks 早期顯式查證項）。
2. rev4 handler/role.rs 已被 010 改寫、未逐一 git blame——實作以 as-built 終態為藍本。
3. `getMenuList/v2` 分頁形（頂層計、size clamp[1,100]）是 rev4 as-built 常數非契約凍結值——
   spec 期與 rev5 前端 hook 無參呼叫形對齊。
4. 中間期已知態三組（§2）＋守門兩腿之生產面觸發隨刀 B 註記（grilling G6）——皆須寫入
   spec 的 Edge Cases／已知態節，防煙測誤判回歸。（原開放點「getMenuTree 歸屬」已由
   grilling G4 解決＝移入本刀。）

## §9 rev4 參照清單（plan research 前置素材，ADR 0019）

- spec：rev4:specs/009-role-admin（role CRUD／roleHome 部分）＋rev4:specs/010-menu-admin 全套。
- 碼：rev4 handler/role.rs（CRUD 段）／handler/menu.rs（905 行全；★reload 呼叫點
  :329/:348/:364＝FR-016 落地形）／facade/sys_menu.rs（3405 行、選單域狀態機主藍本）／
  facade/sys_role.rs／facade/sys_casbin_archive.rs（寫入面＋reason gate＋:713 之 reason
  歸屬逐字）／auth/enforce.rs（rebuild_enforcer／reload_enforcer 全套＋硬禁令註解 :69/:76/:94）。
- ADR：rev4:0049（role_id＋翻案條款）／0051（選單域狀態機）／0052（島 H）／0061（回收桶軌道判例）／
  0064（seed 覆寫白名單→rev5 等價物＝ADR 0007 演進帳）。
- 前端：rev4 views/manage/menu/ 三檔＋views/manage/role/（CRUD 面）。
- rev5 差異點（不得帶回）：restore 冪等成功（→業務錯誤）／上下文缺席放行（→拒寫5000）／
  AuditOperation 大寫形（→小寫封閉詞彙）／find_by_keys 批次讀端／`"rev4menu"` 域鎖字面
  （→`"rev5menu"`）／SELF_SERVICE_ROUTES／zh-tw runtime locale。
