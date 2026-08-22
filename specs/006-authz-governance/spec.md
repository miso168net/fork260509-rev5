# Feature Specification: 006 三維授權治理＋結構性封死＋授權回收桶（島 G 入憲）

**Feature Branch**: `006-authz-governance`

**Created**: 2026-08-23

**Status**: Draft

**Input**: User description: "docs/brainstorms/006-authz-governance.md"（階段 0 brainstorm 定稿〔2026-08-22
五 lens 偵查後重寫〕＋§10 二十二題 grilling 輪 user 逐題親決＋§11 決議總表與連動後果；本 spec 之唯一輸入。
與 005-role-menu-crud 為同一次 brainstorm 的拆刀產物——沿縫 α「grant/revoke 寫 casbin_rule」裁開、本刀＝
grant 面全部。射程權威＝brainstorm §2；rev4 對應碼＝實作預設藍本、清單於 plan research 凍結（ADR 0019）；
起手維護批（B-094／B-101／B-085／B-102 收攏與補測）已先於本刀 merge 回 default、本刀自乾淨基線長出）

> 摘要：把 rev5 角色管理的三顆授權 modal（選單／按鈕／端點）與授權回收桶從 upstream demo 殼接成真——
> **三維授權讀寫 6 支＋支撐讀 3 支＋授權回收桶 2 支＝11 支端點**（ROUTES 38→49；seed 政策列 100% 預埋、
> **零 migration、零 seed 變更**），前後端同刀、CDP 三方對照驗收。消費 005 已兌現的三底座（選單序列化域／
> casbin rebuild-swap 判定面同步／授權歸檔寫入面＋reason gate），本刀新拍板三件：**結構性封死**（治理面
> protected 端點 MUST NOT 授予非 R_SUPER——B-024①歸宿、島 G6）、**手動撤銷之選單／按鈕維歸檔列入不可復原集**
> （reason gate 三值→五值、回收桶可復原列只剩端點維、零 migration 保住、島 H2 零破口）、**restorePolicy 固定序
> 五腿復原重驗**。憲法一次 MINOR v1.7.0→v1.8.0：§I.7 第八座行為島（島 G casbin 授權治理、六條）＋§III.2
> `MANAGE-PAGE-WIRING` 加用途 (iii)(iv)＋ADR 0052 生成檔條款入 §III 正文＋島 H 兩處括號回填；ADR 三支
> （0053 島 G 入憲／0054 結構性封死／0055 restorePolicy 五腿＋ADR 0050 §4 復核結論）。連帶修復既有破口：menu
> 管理頁已在呼叫的 getAllPages 現況恆 4040——交付端點即自動修復。

## Clarifications

### Session 2026-08-18（brainstorm 拍板；屬本刀之條目，全紀錄見 brainstorm §3）

- Q: 刀怎麼切？→ A: **刀 A＝role+menu、刀 B＝user+password；刀 A 沿縫 α（grant/revoke 寫 casbin_rule）
  拆 005／本刀**——本刀＝grant 面全部：三維授權治理、結構性封死、授權回收桶、島 G 入憲。
- Q: 授權模型深度（B-024①）？→ A: **結構性封死授出**——治理面 protected 端點 MUST NOT 授予非 R_SUPER；
  updateRoleEndpoints／restorePolicy 鎖內驗、違者顯式拒；no-escalation 真邏輯留翻案刀（rev3 唯一先例
  commit 3bfab71 之三缺陷為參照）。
- Q: 治理拒因明細（B-024③）？→ A: **全降級純 key**（島 G2 條文不綁載體；`protectedRevoke` 明細陣列、
  `BlockedTarget` 型與前端 `protected-revoke-detail.ts` 皆不帶回）。
- Q: updateRoleButton 候選驗證？→ A: **加 orphan skip**（對稱 menu 維；候選集＝未刪選單〔含停用〕之
  buttons 聯集、界外碼靜默略過、回應帶實際生效集合）。
- Q: 歸檔表三自由度（role_id 可空／protected 快照欄／menu_id 同實例欄）？→ A: **全不動**（005 兌現）；
  ADR 0050 §4 翻案觸發條款由本刀復核（見 2026-08-22 輪 Q6）。
- Q: restore 按鈕碼 gating？→ A: **不 gating**（頁級 R_SUPER＋列級 restorable 兩道門）。
- Q: 回收桶 UI 形？→ A: policy-archive＝**獨立管理頁**（rev4 原形；B-008 死項出列一張）。
- Q: static meta 紀律？→ A: **DB 唯一真源**（seed 選單列 10 之 icon＝唯一真源，不寫 static meta）。
- Q: 修憲次數？→ A: 拆刀後各刀一次 MINOR——**本刀落島 G（v1.7.0→v1.8.0）**。
- Q(G1): 熱重載基建歸屬？→ A: 005 建基建、**本刀純消費**（grant 面接線＋島 G1 條文入憲）。
- Q(G2): 新建／復原選單在授權面板進場前無法授予可見性？→ A: 005 已知態③；**本刀 updateRoleMenu 即
  缺席的第二步工具、交付即消滅**。
- Q(G3): 兩顆授權 modal 歸屬？→ A: **屬本刀**（005 零 diff 已機器驗證、與最原始源基線逐位一致起改）。

### Session 2026-08-22（/grilling 二十二題、user 逐題親決；逐題全文見 brainstorm §10、總表與連動後果見 §11）

- Q1 結構性封死條文位置？→ A: **獨立 G6**（照島 F 之 F6～F8 新編號附掛；修訂日誌寫「五條沿 rev4＋G6
  本刀新拍板」）。
- Q2 封死標的集落字？→ A: **條文只寫謂詞、不寫列數**（ADR 0047 活量指節不指數；敘事量「2026-08-22 時
  端點維 15 列」落修訂日誌／活書）。
- Q3 G1 觸發矩陣入憲？→ A: **條文只凍結方向面**（成功 commit 後 MUST 同步／被拒與無作用與標的不存在
  MUST NOT 觸發／keep-last-good／反轉＝MAJOR）、矩陣本體留 ADR＋enforce.rs doc。
- Q4 grant 面空 diff 是否 reload？→ A: **照 rev4：Applied 即觸發、不問 diff**——條文與 doc MUST 明文
  「grant 面刻意例外」、與移除面 `if archived` 並陳。
- Q5 deleteRole 免 reload 論證轉正入島 G？→ A: **不轉正、留 ADR 0050 級**（刀 B 依 B-093 一次 spec 拍板即可閉合）。
- Q6 ADR 0050 §4 翻案觸發條款復核（menu 維同實例）？→ A: **B＝手動撤銷之 menu／button 維歸檔列列入
  不可復原集**（reason gate 三值→五值）——零 migration、H2 零破口；回收桶對 menu／button 維只剩稽核
  閱覽；復核結論由 ADR 承載（0055）。
- Q7 restorePolicy 復原重驗腿定形？→ A: **固定序五腿**：①reason gate（五值集）→②role 同實例（歸檔
  role_id＝現役同代碼活角色 id、NULL 不可復原）→③結構性封死→④端點在冊（不在 ROUTES 名冊→拒、免幽靈
  政策）→⑤角色停用不擋（停用≠撤銷）；每腿註對應寫端守門、照 ADR 0051 落字範式。**連動：可復原列自此
  只剩 endpoint 維手動撤銷 ⇒ restorePolicy 不再需進選單序列化域。**
- Q8 v2='menu' 四列 protected 政策納封死？→ A: **不擴、列已知態**（可見性可授、端點仍封；看得到點不動）。
- Q9 getAllPages 域？→ A: **顯示域**（照 rev4）＋spec 明記 menu 頁消費面不對稱（停用選單的 routeName
  不在下拉、拒因由 routeNameExists 誠實承擔）。
- Q10 roleHome UI 隨本刀接上？→ A: **納入**（menu-auth-modal 同檔 +2 fetcher＋2 型＋4 處接線；契約與
  rev4 三處相異不可照抄：query 鍵 `id`／回應 `{home}` 誠實 null／三形同義清空；候選源＝getAllPages）。
- Q11 三維＋回收桶契約的角色鍵？→ A: **八支全部用 `id`**（三維六支＋roleHome 既判二支同式、一次釘死於 contracts）。
- Q12 protected 列 UI 預標載體？→ A: **三支讀端回應多帶 protected 旗標**（後端單一真源；wire-schema 本刀本就重抽）。
- Q13 §III.2 授權形式？→ A: **MANAGE-PAGE-WIRING 加兩列**：(iii) 三顆授權 modal 接真〔含 roleHome UI；
  role-operate-drawer 同檔雙用途明寫；endpoint-auth-modal 新增型新檔另註〕＋(iv) policy-archive 頁（形照 (i)）。
- Q14 policyArchive 之 restore／confirmRestore／restoreSuccess 三鍵收斂？→ A: **不收斂、各頁自有鍵**。
- Q15 島 H H1 終態成員括號回填？→ A: **PATCH 級隨批回填**——如實寫「選單維／按鈕維授權寫端已兌現；回收桶
  復原之選單／按鈕維分支因不可復原集擴列結構性不可達」。
- Q16 B-083 島 G as-built 落節？→ A: **甲案＝落活書 §5＋§8、§6 只 errata 零行增減**（B-083 續掛帳；§8 餘 13 行落筆先算）。
- Q17 B-024 整條關帳？→ A: **改記殘餘、不整條 done**（條目改寫為只剩「no-escalation seam 填入後掛點前移（翻案刀承接）」一句）。
- Q18 B-104 承載形？→ A: **併入島 G 入憲 ADR**（G1 條文長什麼樣＝一決策；承接 ADR 0049 §2 表、寫訂正後
  完整矩陣含 grant 面 Applied 即觸發）。
- Q19 updateUserSessionPolicy（seed 68、protected、未上線）歸哪刀？→ A: **刀 B**（資料面屬 user 域；謂詞式
  封死下未上線期間自動受保護）。
- Q20 B-088 對賬閘順捎？→ A: **順捎＋具名豁免兩列**（seed 列 9 system-settings／77 audit、豁免附 B-008 指針）。
- Q21 B-098 補齊範圍？→ A: **本刀新增命名空間必配裁判**＋起手維護批補 RoleAdmin／MenuAdmin 12 支（已兌現）、
  IpRule 7 支留帳（B-098 不關帳）。
- Q22 B-075 順捎？→ A: **不建靜態守恆、B-075 維持不入**（避免與 runtime 封死守門第二套字面同源）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 超管三維授權治理（選單／按鈕／端點） (Priority: P1)

超級管理員在角色管理頁的抽屜點開「選單權限」「按鈕權限」「端點權限」三顆 modal，看到該角色**現況已授集**
（受保護項預標鎖定）與**候選全集**（與判定面同源），勾選後提交**期望全集**——系統比對現況導出撤銷集與新授集、
同一交易落地並寫操作稽核；撤銷集觸及受保護授權時整批拒、零變更。提交成功即刻影響 API 判定（判定面同步），
前端選單／按鈕顯隱於下次載入更新。

**Why this priority**: 這是本刀的本體，也是 005 已知態③（新建／復原選單無法授予側欄可見性）的第二步工具；
rev5 至今角色授權只能靠 seed，沒有任何運行期授權治理能力。

**Independent Test**: 以 Super 登入→新增一個角色→三顆 modal 各勾一組→提交→以該角色登入（經測試資料
指派）驗側欄、按鈕、端點判定皆依勾選生效；再撤銷其中一項→判定即刻失效；試圖撤銷 R_SUPER 名下任一受保護
項→整批拒、零變更。

**Acceptance Scenarios**:

1. **Given** 角色 R 現有 menu 維授權集 {a,b}、候選集為未刪選單（含停用）全集，**When** 提交期望全集 {b,c}，
   **Then** 撤銷 a（archive-move、reason=`menu_revoke`）、新授 c、b 不動；同交易一列稽核（`update`）；回應
   帶實際生效集合；交易提交後判定面同步一次（即使期望集與現況相同亦同步——刻意例外）。
2. **Given** 期望全集含治理域外的選單識別（已刪或不存在），**When** 提交，**Then** 該項靜默略過不產生孤兒
   授權（orphan skip），回應之生效集合不含它。
3. **Given** 角色 R 名下有一列 protected menu／button／endpoint 政策，**When** 提交之期望全集缺該項（＝撤銷
   集觸及 protected），**Then** 整批拒（`2222`＋`biz.role.protectedRevoke`）、零變更、零稽核、零判定面同步。
4. **Given** 按鈕維候選集＝未刪選單（含停用）buttons 聯集，**When** 提交含不在聯集內之碼，**Then** 界外碼
   靜默略過（orphan skip）、回應帶實際生效集合。
5. **Given** 停用中選單 S 及角色 R 對 S 的既有授權，**When** 以含 S 的期望全集提交，**Then** S 的授權不被
   撤銷（停用≠撤銷、候選集含停用）；**When** 以候選集誤用顯示域（不含 S）的形提交，**Then** 必配負向測試
   證明此形會把停用靜默升級為撤銷＝禁止形。
6. **Given** 端點維，**When** 讀取 R 現況，**Then** 以「路徑×方法」雙鍵呈現、以 HTTP 方法白名單辨識端點維
   （不以排除他維反推）；**When** 提交，**Then** 全量替換語意同上；此維寫端不進選單序列化域。
7. **Given** 三支讀端，**Then** 每一授權項帶 `protected` 旗標；**Given** 角色不存在或已刪，**Then** 讀寫皆回
   `biz.role.notFound`（角色鍵一律 `id`）。
8. **Given** 兩個 menu／button 維寫端併發，**Then** 後者於選單序列化域 advisory 等待（pg_locks NOT-granted
   觀測）——入域寫端各配一支機器證。

---

### User Story 2 - 結構性封死：治理面受保護端點不得授予非超管 (Priority: P1)

超級管理員試圖把治理面的受保護端點（如 updateRoleEndpoints 自身、restorePolicy、IP 規則寫端……）授予
R_ADMIN——系統在鎖內以資料庫現況判定「該 (path,method) 是否為受保護政策」，命中即整批拒、零變更。經回收桶
把受保護端點政策復原給非 R_SUPER 亦走同一守門。un-protect／re-protect 在一般管理介面永不提供。

**Why this priority**: 這是 B-024① 的歸宿與零 migration 的承重前提：005 不加 protected 快照欄的前提＝「含
protected 列的撤銷整批拒 ⇒ protected 列結構上進不了歸檔表」，若本刀鬆綁任一處即觸發 ADR 0050 §4 翻案條款。
超管在 UI 真做得出「把治理端點授給 R_ADMIN」——守門非 vacuous。

**Independent Test**: 以 Super 對 R_ADMIN 提交端點維期望全集含 `POST /systemManage/updateRoleEndpoints`
→整批拒（`2222`＋封死拒因鍵）、零變更；同一請求改為非受保護端點→成功；變異自證：拆掉鎖內守門→該測必紅。

**Acceptance Scenarios**:

1. **Given** 非 R_SUPER 角色 X，**When** updateRoleEndpoints 之新授集含任一 (v1,v2) 屬「ptype=p ∧
   protected=TRUE ∧ v2∈HTTP 動詞」之集合（鎖內以資料庫現況判定），**Then** 整批拒、零變更、一因一鍵。
2. **Given** 一列 endpoint 維歸檔列其標的 (v1,v2) 屬上述集合且來源角色非 R_SUPER，**When** restorePolicy，
   **Then** 於鎖內封死腿拒（NotRestorable）——雙路徑全覆蓋。
3. **Given** v2='menu' 之四列 protected 政策（manage_role／manage_menu／manage_system-settings／
   manage_policy-archive），**When** 超管經 updateRoleMenu 授予 R_ADMIN 可見性，**Then** 成功（不在謂詞射程）
   ——端點仍 `5003`、效果＝看得到點不動（已知態、spec 明記）。
4. **Given** 守門實作，**When** 刻意弄壞（拆掉守門或改謂詞），**Then** 對應測試轉紅（變異自證、還原後綠）。

---

### User Story 3 - 授權回收桶：閱覽歸檔列與復原端點維授權 (Priority: P2)

超級管理員在獨立的 policy-archive 頁看到全部歸檔列（歸檔時間新到舊；以來源角色代碼、維度雙條件過濾），
每列帶後端判定的「可復原」旗標；對可復原列執行復原——鎖內五腿重驗後回到現役、歸檔列移除、同交易稽核、
判定面同步。手動撤銷之選單／按鈕維歸檔列與三類連動歸檔列皆不可復原（只剩稽核閱覽價值），唯一可復原的是
端點維手動撤銷。

**Why this priority**: 撤銷而無復原＝變相硬刪；但其價值依附於 US1 的撤銷面、且可復原集已收窄至端點維，
故次於 P1。

**Independent Test**: 以 Super 撤銷 R_ADMIN 一條端點維授權→policy-archive 頁見該列 restorable=true→
復原→R_ADMIN 判定即刻恢復；撤銷一條 menu 維授權→該列 restorable=false、復原動作停用、後端強行呼叫回
NotRestorable。

**Acceptance Scenarios**:

1. **Given** 歸檔表有多維多角色列，**When** 開啟 policy-archive 頁，**Then** 分頁信封、`archivedAt` DESC、
   可依來源角色代碼／維度過濾；維度由歸檔列內容推導（無維度欄）。
2. **Given** 一列 reason=`endpoint_revoke` 且其來源角色 id 等於現役同代碼活角色 id，**Then** restorable=true；
   **Given** reason 屬五值不可復原集、或 role_id 為 NULL、或現役同代碼角色非同一實例，**Then** restorable=false。
3. **Given** restorable=true 之列，**When** 復原，**Then** 鎖內固定序五腿重驗皆過→回灌現役＋刪歸檔列＋稽核
   （`restore`）同交易→判定面同步；**Given** 標的已在現役，**Then** 回成功無作用（NoOp）且歸檔列仍消費移除；
   **Given** 識別不存在或任一腿拒，**Then** `biz.policy.notRestorable`（後端最終防線、不依賴前端隱藏）。
4. **Given** 歸檔列之 (v1,v2) 已不在 ROUTES 名冊（端點下線），**When** 復原，**Then** 第④腿拒（免幽靈政策）。
5. **Given** 來源角色已停用但活性，**When** 復原，**Then** 第⑤腿不擋（停用≠撤銷；已知態）。
6. **Given** policy-archive 頁，**Then** 側欄項經 seed 選單列 10 顯示（component 字面決定 view 目錄）、頁級門
   ＝menu 維政策列 72（R_SUPER）；復原鈕無按鈕碼 gating；restorable=false 列呈停用態。

---

### User Story 4 - 三顆授權 modal 接真＋roleHome 指定＋支撐讀（含既有破口修復） (Priority: P2)

超級管理員在角色抽屜看到三顆授權鈕（rev4 對照錨點；rev5 現況兩顆）；選單權限 modal 顯示真樹、真勾選（不再
是寫死 1..21）與首頁下拉（roleHome 讀寫、候選＝顯示域頁面全集）；按鈕權限 modal 的假資料 button1..button10
消失、候選＝治理域 buttons 聯集；端點權限 modal 以路徑群組呈現端點候選、支援群組級勾選。選單管理頁的
page／activeMenu 下拉因 getAllPages 端點到位而從「恆空／僅當前」變為顯示域全集。

**Why this priority**: 後端三維寫端沒有 UI 就沒有操作者；roleHome 是 005 明文交棒的零消費者窗；getAllPages
是 menu 管理頁已在呼叫的既有 404 破口——交付端點即自動修復，屬明確交付效果。

**Independent Test**: CDP 三方對照（22080 vs 42080、必要時 42089）：抽屜三顆鈕、選單 modal 勾選非連號且
notFound toast 消失、首頁下拉可存可讀（清空三形同義）、按鈕 modal 無假資料、端點 modal 群組勾選；menu
管理頁新增 modal 之 page 下拉非空。

**Acceptance Scenarios**:

1. **Given** 角色抽屜，**Then** 三顆授權鈕皆在（不做 hasAuth gating、門在頁級 R_SUPER）；role/index.vue 一行不動。
2. **Given** 選單權限 modal，**When** 開啟，**Then** 樹＝治理域（既有 getMenuTree）、勾選＝getRoleMenu 現況、
   受保護項預標鎖定（依讀端 protected 旗標）、首頁下拉＝getAllPages（顯示域）且現值＝getRoleHome（NULL
   誠實 null）；**When** 提交，**Then** 打 updateRoleMenu（全量）＋首頁變更打 updateRoleHome（三形同義清空）。
3. **Given** 按鈕權限 modal，**Then** 候選＝getAllButtons（治理域聯集）、現況＝getRoleButton；提交打 updateRoleButton。
4. **Given** 端點權限 modal（新增型新檔），**Then** 候選＝getAllEndpoints 依路徑群組呈現、葉鍵以路徑＋方法
   合成且反查不拆字串（路徑可含分隔符）、群組級勾選；提交打 updateRoleEndpoints。
5. **Given** 任一 modal 之撤銷觸及 protected，**Then** 純 key toast 由共用攔截層呈現、無明細表。
6. **Given** menu 管理頁新增／編輯 modal，**Then** page／activeMenu 下拉來自 getAllPages（顯示域）；停用選單的
   routeName 不在下拉、若手輸與停用列同鍵則由 routeNameExists 誠實拒（已知不對稱）。
7. **Given** ip-rule 管理頁以無寫端按鈕碼之帳號開啟（本刀授權面使此態自不可達變可達），**Then** default slot
   不冒出共用元件自帶寫端鈕（B-099 順修；CDP 撤一碼驗收）。

---

### Edge Cases

- **本刀新造已知態（必明記、防煙測誤判回歸）**：超管經 updateRoleMenu 可授予「指向不存在 view 的自建選單」
  ⇒ 側欄可見但點擊零反應（與 B-088 描述形同；B-088 對賬閘本刀順捎、但閘只管 seed 側 view.*）。
- **封死射程外之已知態**：v2='menu' 四列 protected 政策可授予 R_ADMIN 可見性（端點仍 `5003`）；seed 68
  updateUserSessionPolicy（protected、未上線）歸刀 B——本刀 spec MUST NOT 宣稱「治理面 protected 端點集
  已全數上線」（謂詞式守門下上線即自動納管、不阻塞本刀）。
- **回收桶對選單／按鈕維只剩稽核閱覽**：reason 五值不可復原集含 `menu_revoke`／`button_revoke`；選單維
  授權只能重勾不能復原——UI 以 restorable=false 停用態呈現，不另造提示。
- **復原到停用角色**：第⑤腿不擋（停用＝暫時下架、與島 H4 同向）；停用即斷權沿基線行為。
- **端點維下線列**：歸檔列之 (v1,v2) 可能已不在 ROUTES 名冊——rev4 不驗、rev5 第④腿拒（已拍）。
- **role_id NULL 之歷史列**：結構上本刀後新列恆有 role_id（標的角色列已鎖且活性）；NULL→restorable=false
  誠實退化（不補寫、不猜）。
- **grant 面空 diff**：仍 Applied 仍 reload（刻意例外、與移除面「有歸檔才觸發」並陳於條文與 doc）。
- **角色不存在／已刪**：三維讀寫與 restorePolicy 一律 `biz.role.notFound`（純 key）。
- **empty body／body 解析失敗**：沿既有寫端慣例以共用件收斂 `T::default()` 交守門判（全量替換語意下預設空
  集＝「撤銷全部」——**MUST NOT** 把守門前移進 middleware；空集若觸及 protected 即整批拒、不觸及則確為
  全撤）；不得為此新增錯誤碼。
- **請求上下文缺席**：寫端稽核列之來源欄不可得 ⇒ 拒寫 `5000`（rev5 既定、F3① 同向）。
- **menu 維 orphan skip 與停用**：已刪／不存在＝跳過；停用＝合法候選（不跳）；誤用顯示域＝禁止形（負向測試）。
- **併發**：menu／button 維寫端與 005 既有域成員互斥序列化（advisory NOT-granted 觀測、classid／objid 拆讀）；
  endpoint 維寫端與 restorePolicy 不入域、以角色列 FOR UPDATE 鎖序列化（rev4:FR-022 之 lock-then-redecide）。
- **判定面同步交錯**：跨端點 reload 已由 RELOAD_SERIAL 互斥（005 收刀期補）；本刀把 reload 呼叫者自 3 支擴至
  7 支、暴露面放大——交錯時序 seam 形 harness 隨端點維單元自拍（B-105；成本失控則留帳附記）。
- **測試殘列與序列**：casbin_rule 與 sys_casbin_policy_archive 皆不在 schema-gate runtime-append 收窄集 ⇒
  gate2 逐列全等；一切真表測試配清理守衛＋seq 還原（casbin_rule_id_seq (163,true)、archive seq (1,false)）；
  CDP 走查會留列與序列推進 ⇒ **走查排 schema-gate 驗收之後**（或走查後手動還原）；真登入 smoke 後緊接全量
  ＝throttle 家族暫態紅（L-050，rerun 前先存 log 截名單）。
- **三鍵不收斂**：policyArchive 之 restore／confirmRestore／restoreSuccess 為第三份同名鍵（各頁文案不同）。
- **B-008 餘兩張死項**（system-settings／audit）續留：側欄零反應＋原始 i18n key——CDP 排除清單。

## Requirements *(mandatory)*

### Functional Requirements

#### A. 端點與契約總則

- **FR-001**: 本刀 MUST 新增恰 11 支端點且 path×method 逐字對齊 001 凍結 seed 政策列（零新 seed、零
  migration）：三維讀寫 6（getRoleMenu／updateRoleMenu／getRoleButton／updateRoleButton／getRoleEndpoints／
  updateRoleEndpoints）＋支撐讀 3（getAllPages／getAllButtons／getAllEndpoints）＋回收桶 2（getArchivedPolicies
  ／restorePolicy）；動詞分布 GET 7／POST 4；路由註冊表條數常數同 commit 對齊（38→49）。
- **FR-002**: 授權態照 seed：11 支全 R_SUPER；protected=TRUE 10 支（getAllPages 為 FALSE）；不多授不少授。
- **FR-003**: 角色鍵 MUST 一律為 `id`（三維六支與 roleHome 既判二支同式）；rev4 之 `roleId` 鍵不帶回；
  一次釘死於 contracts。
- **FR-004**: 三支三維讀端之每一授權項 MUST 帶 `protected` 旗標（後端單一真源、前端據此預標鎖定；MUST NOT
  以 seed 靜態集於前端判定）。
- **FR-005**: 一切業務拒因 MUST 為純 i18n key、一因一鍵、無攜參明細；不得新增錯誤碼（13 碼凍結面不動；
  封死拒因＝`2222`＋新 key）。
- **FR-006**: 寫端操作稽核 MUST 與業務寫入同一交易；詞彙恰五值不擴——三維寫端用 `update`、restorePolicy
  用 `restore`；請求上下文缺席 MUST 拒寫 `5000`。
- **FR-007**: 分頁列表（getArchivedPolicies）MUST 採共用分頁信封、穩定排序 `archived_at DESC, id DESC`。
- **FR-008**: 共用 handler 件（audit_operator／json_or_default／resolve_operator_names／MAX_CURRENT／
  tristate／blank_to_none）MUST 引用起手維護批收攏之共用模組、零拷貝；facade 側 violated_constraint 同。

#### B. 三維授權寫端與讀端（島 G2／G3／G5）

- **FR-009**: 三維寫入 MUST 以「期望全集」為輸入，由系統與現況比對導出撤銷集與新授集（全量替換語意）；
  MUST NOT 提供增量式寫入介面。
- **FR-010**: 撤銷集觸及受保護授權時 MUST 整批拒、零變更（於任何寫入發生之前判定；`biz.role.protectedRevoke`）；
  一般管理介面 MUST NOT 提供設定／解除保護旗標的能力（防鎖死 by-design）。
- **FR-011**: 新授 MUST 補齊治理欄（protected=false＋建立時間與操作者）；撤銷 MUST 為 archive-move（完整快照
  ＋來源角色識別由歸檔 primitive 內收反查活性角色自動填入＋reason）；revoke reason 字面＝`menu_revoke`／
  `button_revoke`／`endpoint_revoke`（沿 reason gate 負向測已預留字面）；刪除集以剛歸檔那批 id 圈定。
- **FR-012**: 授權真相唯一（DB-first）：授權變更與稽核同一交易落地；判定面 MUST 由真相導出、MUST NOT 存在
  繞過真相的第二寫入面（島 G1 前半）。
- **FR-013**: 入域成員：updateRoleMenu／updateRoleButton MUST 於選單序列化域內執行（域鎖為交易首動作、
  lock-then-redecide）；updateRoleEndpoints 與 restorePolicy **不入域**（端點維不涉選單資料；復原可復原集
  已收窄至端點維）——憲法 H1 終態成員括號須如實回填（FR-052）。
- **FR-014**: 三維寫端 MUST 鎖標的角色列（FOR UPDATE、活性）→鎖內重驗（角色活性／protected 集／候選集）
  →落寫（lock-then-redecide、永不信 pre-read）；角色不存在或已刪＝`biz.role.notFound`。
- **FR-015**: 選單維 MUST 以介面選單識別收單、以 `route_name` 落授權（治理域映射）；已失效項（不在治理域）
  MUST 跳過（orphan skip、不產生孤兒授權）；讀端 MUST 反向映射回識別。候選集＝治理域（未刪含停用）、
  MUST NOT 誤用顯示域；停用選單之授權 MUST NOT 被全量替換靜默升級為撤銷（島 H4；必配負向測試）。
- **FR-016**: 按鈕維候選集 MUST ＝未刪選單（含停用）之 buttons 聯集（去重）；界外碼 MUST 靜默略過（orphan
  skip、對稱選單維）；回應帶實際生效集合。
- **FR-017**: 端點維粒度 MUST 為「路徑×方法」雙鍵；現況辨識 MUST 以 HTTP 方法白名單判別端點維（不得以排除
  他維反推）；MUST NOT 引入平行的維度標記編碼；候選＝路由註冊表中受政策管制端點全集。
- **FR-018**: grant 面 outcome MUST 恰兩態 Applied{revoked, granted}／Rejected{blocked}（無 NoOp 態）；回應
  帶實際生效集合。

#### C. 判定面同步消費（島 G1；005 基建純消費）

- **FR-019**: 三維寫端之 Applied 與 restorePolicy 之 Applied MUST 於交易提交後、讀鎖全釋後觸發同一支判定面
  同步（rebuild-swap、keep-last-good、有界重試皆既有）；Rejected／標的不存在 MUST NOT 觸發（早退結構性保證）。
- **FR-020**: grant 面 MUST Applied 即觸發、不問 diff（空 diff 仍同步）——MUST 於島 G1 條文與 enforce.rs doc
  明文為「grant 面刻意例外」、與移除面「成功且有歸檔才觸發」並陳。
- **FR-021**: 判定面同步呼叫點名冊閘 MUST 同步擴列（主守恆集合恰等、不擴列接線當場紅）；MUST NOT 自取
  enforcer 寫鎖；casbin 版本錨不升版。
- **FR-022**: 生效語意 MUST 明文：API 判定即時、前端選單／按鈕顯隱於下次載入更新；本刀 MUST NOT 做即時推播。

#### D. 結構性封死（島 G6、B-024①歸宿）

- **FR-023**: 不變式：屬「ptype=p ∧ protected=TRUE ∧ v2∈HTTP 動詞」之 (v1,v2) 集合（謂詞式、資料庫態鎖內現查；
  條文不寫列數——2026-08-22 量測端點維 15 列）MUST NOT 授予非 R_SUPER 角色。
- **FR-024**: 掛點 MUST 恰為 updateRoleEndpoints 與 restorePolicy（端點維復原）之鎖內守門；違者整批拒（`2222`
  ＋封死拒因鍵、零變更）；守門非 vacuous（超管在 UI 真做得出）、MUST 配變異自證（弄壞→紅→還原→綠）。
- **FR-025**: v2='menu' 四列 protected 政策 MUST NOT 納入封死射程（已知態：可見性可授、端點仍 `5003`）。
- **FR-026**: 承重前提 MUST 明文於 ADR：撤銷歸檔列原值恆 protected=false（protected 列結構上進不了歸檔表）；
  005 零 migration 以「整批拒＋un-protect 永不 UI 化」為前提；任一處鬆綁＝觸發 ADR 0050 §4 翻案條款。
- **FR-027**: B-024 三件套：①封死＋翻案觸發條款（真要多層管理員時翻案刀建真 no-escalation；rev3 原形三缺陷
  〔靜默壓縮授權／漏 restorePolicy／TOCTOU〕留參照）②seeded 護欄三套既有 ③明細受眾邊界維持純 key（ADR 0022
  決定 2 不翻案）；no-escalation 空 seam 不填、ADR 0022 後果末條「填 seam 後掛點前移」殘餘由 B-024 改記。

#### E. 授權回收桶（島 G5 復原面）

- **FR-028**: getArchivedPolicies MUST 分頁＋雙濾（來源角色代碼／維度）＋`archived_at` DESC；維度由歸檔列內容
  推導（選單／按鈕／HTTP 動詞→端點；不新增維度欄）；讀端零 migration（基線索引現成）。
- **FR-029**: 每列 MUST 帶後端判定之 `restorable` 旗標＝「reason 不屬不可復原集」∧「歸檔 role_id 等於現役同
  代碼活角色 id」（NULL→false）；前端 MUST NOT 自行推斷；旗標非權威、MUST 與 restorePolicy 權威判定同判準
  （reason 半共用單點 fn、同實例半同式）；同實例半以批次讀端取活性角色（避免逐列查）。
- **FR-030**: 不可復原 reason 集 MUST 擴為五值 `{role_soft_delete, menu_soft_delete, menu_button_removed,
  menu_revoke, button_revoke}`（單點 fn 承載、集合成員測更新）；唯一可復原 reason＝`endpoint_revoke`。效果：
  回收桶對選單／按鈕維只剩稽核閱覽、選單維授權只能重勾不能復原；島 H2 零破口、零 migration。
- **FR-031**: restorePolicy MUST 鎖內固定序五腿重驗（ADR 承載、照 ADR 0051 落字範式、每腿註對應寫端守門）：
  ①reason gate（五值集）②role 同實例（歸檔 role_id＝現役同代碼活角色 id；NULL 不可復原、誠實退化）③結構性
  封死（protected 端點政策不得復原給非 R_SUPER）④端點在冊（(v1,v2) 不在路由註冊表→拒、免幽靈政策）⑤角色
  停用不擋（停用≠撤銷、島 H4 精神、已知態）。
- **FR-032**: restorePolicy outcome MUST 三態：Applied（回灌現役＋歸檔列移除＋稽核 `restore` 同交易→判定面
  同步）／NoOp（標的已在現役→回成功且歸檔列仍消費移除）／NotRestorable（識別不存在或任一腿拒→
  `biz.policy.notRestorable`）；後端 MUST 為最終防線。
- **FR-033**: restorePolicy MUST NOT 進選單序列化域；鎖序＝歸檔表列→sys_role 列（FOR UPDATE）→鎖內重驗→
  回灌→刪歸檔→稽核；與 updateRoleEndpoints 共用同一封死守門（雙路徑全覆蓋）。
- **FR-034**: policy-archive MUST 以獨立管理頁交付（查詢列 roleCode×dimension＋表格＋分頁）；restorable=false
  列呈停用態；復原無按鈕碼 gating（門＝頁級 menu 維政策列 72＋列級旗標）；view 目錄由 seed 選單列 10 之
  component 字面決定、icon 以 DB 為唯一真源（不寫 static meta）。
- **FR-035**: 回收桶三語／兩語譯文 MUST 隨頁補齊（`page.manage.policyArchive` 整節、`route.manage_policy-archive`
  一鍵）；restore／confirmRestore／restoreSuccess 三鍵各頁自有、不收斂。

#### F. 支撐讀

- **FR-036**: getAllPages MUST 為顯示域（啟用且未刪）頁面全集；spec 明記 menu 管理頁消費面不對稱（停用選單
  之 routeName 不在下拉、拒因由 routeNameExists 誠實承擔）；交付即修復該頁既有 `4040` 破口（已知態）。
- **FR-037**: getAllButtons MUST 為治理域（未刪含停用）buttons 聯集去重（新建公開讀端；與絕版判定之私有掃描
  語意不同、不共用）。
- **FR-038**: getAllEndpoints MUST 為路由註冊表中受政策管制端點全集（路徑×方法；依路徑群組呈現）；回應集隨
  註冊表成長（量測 24→35）。
- **FR-039**: 三面板候選 MUST 與判定面同源：不多列（不受管制者不出現）、不漏列。

#### G. 前端

- **FR-040**: 三顆授權 modal MUST 接真：menu-auth-modal（修改型、接 getRoleMenu／updateRoleMenu、
  fetchGetAllPages 接真、checks 不再寫死）／button-auth-modal（修改型；接 getRoleButton／updateRoleButton＋
  getAllButtons）／endpoint-auth-modal（新增型新檔；葉鍵以路徑與方法合成、群組鍵＝純路徑、反查由映射表
  還原不拆字串、子項勾選策略）；掛載點 role-operate-drawer（同檔雙用途）；role/index.vue MUST 一行不動；
  三鈕不做 hasAuth gating（門在頁級）。
- **FR-041**: 三 modal MUST 依讀端 `protected` 旗標預標鎖定（不可取消勾選）；撤銷含 protected 之整批拒為
  後端最終防線。
- **FR-042**: 拒因 UI MUST 純 key toast（共用攔截層）；不建 ProtectedRevokeDetail 型、不擴 DETAIL 對照表、
  不帶回 protected-revoke-detail.ts。
- **FR-043**: roleHome UI MUST 隨本刀接上（menu-auth-modal 同檔：getRoleHome／updateRoleHome 兩 fetcher＋
  兩型＋四處接線）；契約沿 rev5 既判形（query 鍵 `id`、回應 `{home}` 誠實 null、顯式 null／缺席／空字串
  三形同義清空）；候選源＝getAllPages；閉合 005 零消費者窗。
- **FR-044**: policy-archive 頁兩檔 MUST 新增型新檔；路由外掛產物四檔走產物檔紀律（禁手改＋重算冪等；
  route-artifact-gate 三道斷言）；自由文字欄純文字插值（archive_reason 為受限列舉、非 client 可控）。
- **FR-045**: B-099 MUST 隨前端單元順修：ip-rule 頁 default slot 於 hasAuth=false 不冒寫端鈕（照 menu 頁
  既驗形，約 +3 行、新增型新檔零標記成本）；條文失準觸發理由同步訂正；驗收＝CDP 撤一碼。
- **FR-046**: i18n MUST：backend 樹四處同 commit（zh-cn／en-us／app.d.ts 走既有授權；zh-tw.ts 為 rev5 純
  新增檔、僅 backend 鍵）、page／route 樹三處（zh-tw 不塞 page 鍵）；新 backend 鍵：`biz.role.protectedRevoke`
  ／`biz.policy.notRestorable`／封死拒因鍵（命名於 contracts msg-keys 定案；構造點一律字面形）；
  `page.manage.role.endpointAuth` 一鍵；zh-cn 零 lint 覆蓋 ⇒ 單元驗收顯式跑 typecheck；前後端鍵同 commit。
- **FR-047**: fork-delta 檔集 MUST 恰為：修改型 inline 3（兩 modal＋role-operate-drawer）；新增型新檔 3
  （endpoint-auth-modal＋policy-archive 兩支）；修改型檔內新增型圈界 3（zh-cn／en-us／app.d.ts）；純新增檔
  增量 1（zh-tw.ts）；產物檔 4；rev5 自有 wrapper／typings 同檔追加；連帶修 1（ip-rule/index.vue）；條件性 1
  （menu/index.vue、僅 CDP 實測干擾驗收時）；預期零 diff＝components.d.ts／service/api/index.ts；修改型標記
  逐行 `原行:`。
- **FR-048**: 憲法 §III.2 MUST 加兩列：(iii) 三顆授權 modal 接真〔含 roleHome UI；role-operate-drawer 同檔雙
  用途明寫；endpoint-auth-modal 新增型新檔另註〕＋(iv) policy-archive 頁（形照 (i)；產物四檔授權沿 (i) 列、
  不重複列名）；表列 10→12；新列首欄不留空；表外宣告第 2 條改寫（「rev5 無 modal 治理需求」自本刀起為假述）。
- **FR-049**: B-088 對賬閘 MUST 順捎（seed 之 view.* ⊆ 前端 view 集）＋具名豁免兩列（seed 列 9
  system-settings／77 audit，豁免附 B-008 條目編號為觸發、兌現時自然縮小）。
- **FR-050**: CDP 對照判準 MUST 改用：選單 modal 勾選非 1..21 連號／notFound toast 消失；按鈕 modal 假資料
  消失；抽屜三顆 vs 兩顆錨點；policy-archive 頁側欄有項且可操作；已知態排除清單（B-008 餘兩張、本刀新造
  已知態）。

#### H. 治理與簿記

- **FR-051**: 憲法 Amendment MUST 一次 MINOR（v1.7.0→v1.8.0）、為前置單元、user 親決；逐處＝①§I.7 新增
  島 G 六條（G1 DB-first＋判定面同步方向面與失敗契約／G2 protected 整批拒、拒因可辨一因一鍵、明細載體活書級
  ／G3 deleteRole 與 grant/revoke 連動歸檔／G4 選單維錨與候選同源／G5 固定鎖序「advisory→歸檔表列→sys_role
  列→sys_menu 列→casbin_rule」＋復原同實例判定＋跨刀鉤子句指刀 B／G6 結構性封死謂詞）②島 H header 括號
  回填（G 位已填）③H1 終態成員括號回填（如實寫「選單維／按鈕維授權寫端已兌現；回收桶復原之選單／按鈕維
  分支因不可復原集擴列結構性不可達」）④§III 正文加 ADR 0052 生成檔條款 bullet（MUST 為散文 bullet、絕不可
  寫成 §III.2 表格列）⑤§III.2 兩列（FR-048）⑥表外宣告第 2 條改寫 ⑦§IV 九題與 §II 不動 ⑧Amendment log
  一行＋版本行；落字差異五處（觸發面不抄「Applied 含空 diff 才觸發」字面、G2 明細載體不入條文、rev4:L-075
  類比句刪除、G5 寫固定鎖序、G3 不寫欄可空性）；停用雙護欄不入條文；deleteRole 免 reload 不轉正。
- **FR-052**: ADR MUST 三支（編號 0053／0054／0055 自本刀起立檔、ADR 0050 不 supersede 而以 provenance 引用）：
  島 G 入憲（含 G6＋B-104 觸發矩陣訂正〔ADR 0049 §2 括號句出生即誤；訂正後完整矩陣＝移除面三支成功且有
  歸檔／grant 面三支 Applied 即觸發／restorePolicy Applied／其餘零觸發〕＋ADR 0052 條款順捎）／結構性封死
  （FR-023～FR-027 全文＋rev3 原形三缺陷參照＋B-024③ 重評結論）／restorePolicy 五腿定形＋ADR 0050 §4 翻案
  觸發條款復核結論 B；第四支（封死落 §II）不需。
- **FR-053**: 島 G as-built MUST 落活書 §5＋§8（§6 只 errata 零行增減；B-083 續掛帳）；收刀 errata「六座」→
  「八座」（現在式唯一處）；arch_impact MUST 列 §6（雙向相等）；§8 餘行落筆先算。
- **FR-054**: 帳務 MUST：關帳 B-104／B-099；B-024 改記殘餘；B-098 不關帳（新增命名空間必配裁判）；B-088
  順捎；B-075 不入；B-105 隨端點維單元自拍 seam harness（成本失控則留帳附記）；B-106 於自建批次讀端時順捎
  評估；敘述更新各一行＝B-025（產生面已封、殘餘只剩缺陷／手改 DB 漂移）／B-093（reload 觸發面擴大、窗縮
  短不閉合）／B-016／B-018／B-091（rider：每單元收尾順盤 promoted_to 佔位）；B-008 條文「餘 5 支＝audit 5、
  死項 2」。
- **FR-055**: feature_close notes MUST 寫明承接關係（005 事件無指派欄、防同型斷鏈）；seed 68 歸刀 B 記鄰接面。
- **FR-056**: 本刀零 migration、零 seed 變更 MUST 成立（唯一已知威脅＝ADR 0050 §4 翻案條款，已由 Q6 取 B
  化解）；收刀毋須跑 schema refresh 三步。

#### I. 測試與紀律

- **FR-057**: 每支新端點 MUST 配 contract case＋coverage gate 雙向＋case_key 綁定自證＋授權態矩陣對照凍結
  seed 政策列；判定只呼單一進入點、枚舉政策走既有讀面、protected 判定走資料面；handler 層零 path-root
  entity token；名冊閘（判定面／寫鎖／reload 呼叫點）全綠。
- **FR-058**: 兩支入域寫端（updateRoleMenu／updateRoleButton）MUST 各配一支 advisory NOT-granted 等待機器證
  （pg_locks classid／objid 拆讀；缺測則刪掉入域那行全測仍綠＝禁止形）。
- **FR-059**: 守門非 vacuous 自證 MUST：結構性封死變異自證；五腿各配負向測；protected 整批拒負向測；reason gate
  五值集合成員測；restorable 旗標與權威判定同判準測；orphan skip 兩維負向測；grant 面觸發矩陣特性鎖定測
  （Applied 觸發、Rejected 不觸發、空 diff 觸發）。
- **FR-060**: 測試環境紀律 MUST：真表測試配清理守衛（CasbinCleanup seq (163,true)＋archive seq (1,false)、
  RoleCleanup、MenuCleanup）＋顯式大 id 或走真寫端後 setval 還原；測後 schema-gate 三閘綠；CDP 走查排
  schema-gate 之後；真登入 smoke 後全量照 L-050 處置。
- **FR-061**: wire-schema 快照 MUST 重抽（型住 base-web、快照住 rust-api——跨子庫兩段式 commit 次序寫進 task
  註記）；本刀新增命名空間（policy-archive 與三維型）MUST 各配裁判（正向＋反例；protected 欄為重點）；
  IpRule 七支留帳。
- **FR-062**: CDP 三方對照 MUST 覆蓋三 modal＋roleHome＋policy-archive 頁＋menu 頁 getAllPages 修復＋B-099；
  dev 帳號 Super／Admin／User；一律 127.0.0.1。

### Key Entities *(include if feature involves data)*

- **casbin_rule（三維授權政策）**: 授權真相（DB-first）；`v0`＝角色代碼、`v1`＝標的（route_name／按鈕碼／
  路徑）、`v2`＝維度標記或 HTTP 方法；治理欄 `protected`／建立時間與操作者對 adapter 不可見；本刀 grant／
  revoke 寫入面＋結構性封死謂詞之標的集來源。
- **sys_casbin_policy_archive（授權歸檔）**: archive-move 落點；完整快照＋`role_id`（可空、誠實退化）＋
  `archive_reason`（五值不可復原集＋`endpoint_revoke`）；維度由列內容推導；`restorable` 為派生旗標（非欄）。
- **三維候選集**: 選單維＝治理域選單樹（未刪含停用）；按鈕維＝治理域 buttons 聯集去重；端點維＝路由註冊表
  中受政策管制端點全集（路徑×方法）——皆與判定面同源。
- **結構性封死標的集（概念實體）**: 謂詞「ptype=p ∧ protected=TRUE ∧ v2∈HTTP 動詞」之 (v1,v2) 集合，鎖內
  資料庫現查；不寫死列數。
- **選單序列化域（終態成員）**: 005 既有成員＋本刀 updateRoleMenu／updateRoleButton；updateRoleEndpoints 與
  restorePolicy 不入域。
- **判定面（enforcer）**: 由真相全量導出；grant 面 Applied 即同步（刻意例外）、移除面有歸檔才同步；keep-last-good。
- **policy-archive 管理頁**: 獨立頁（seed 選單列 10）、查詢列 roleCode×dimension、restore 動作（列級 restorable 門）。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 路由註冊表恰 49 條且與 seed 政策列 path×method 逐字對齊（機器對賬零漂移）；11 支新端點以 dev
  帳號實測全通（Super 通、Admin 對 11 支皆 `5003`）。
- **SC-002**: rust 測試總數自 682 淨增且全綠（容器內 serial 全量、rc=0）；含：兩支 NOT-granted 機器證、封死
  變異自證、五腿各一負向、protected 整批拒負向、grant 面觸發矩陣特性測、reason gate 五值成員測、restorable
  同判準測、orphan skip 兩維負向——負向自證逐項可示範。
- **SC-003**: CDP 三方對照（22080 vs 42080）：抽屜三顆授權鈕、選單 modal 真勾選＋首頁下拉、按鈕 modal 無假
  資料、端點 modal 群組勾選、policy-archive 頁可濾可復原、menu 頁 page 下拉非空、ip-rule 頁不冒鈕——逐項
  一致；已知態（B-008 餘兩張、本刀新造已知態、menu 維 protected 可授可見性）列排除清單且逐項驗證其現狀。
- **SC-004**: 零 migration 兌現：migration 目錄維持兩支、schema-gate 三閘照常綠；reason gate 擴列為純碼變更。
- **SC-005**: 憲法 v1.8.0（島 G 六條＋§III.2 表列 10→12＋ADR 0052 條款入 §III 正文＋島 H 兩處括號回填）；
  ADR 三支 accepted；lint 全綠（0 錯誤）；fork-delta：修改型標記僅出現於 FR-047 所列檔集。
- **SC-006**: 結構性封死非 vacuous：超管以 UI 可達路徑試授 protected 端點給 R_ADMIN 必拒；拆掉守門測試必紅；
  歸檔表中 protected=TRUE 原值之列恆零（機器斷言）。
- **SC-007**: wire-schema 快照重抽後 definitions 自 57 淨增、新增命名空間全數有裁判（正向＋反例）；前端
  typecheck 綠。
- **SC-008**: 判定面同步失敗注入下服務不中斷（既有 keep-last-good 基建沿用）；grant 面成功後 API 判定即時
  生效（測試以單一進入點探測雙斷言）。

## Assumptions

- rev4 樹（`../fork260509-rev4/`）為唯讀活體藍本：spec 對應＝specs/rev4:009-role-admin 之 rev4:FR-017～
  rev4:FR-036（三維治理狀態機／回收桶／拒因鍵）；as-built 碼清單於 plan research 凍結（ADR 0019）；rev5 已
  明文推翻之行為不得帶回（brainstorm §9 差異點清單：BizData 攜參形、明細陣列與 BlockedTarget、無條件
  reload、caller 傳 role_id、刪除集重跑過濾、roleHome wire 形、hasAuth gating、兩支具名歸檔 fn 形）。
- 005 三底座已全兌現（序列化域兩形薄 fn／rebuild-swap＋RELOAD_SERIAL／insert_archived 內收反查＋reason gate
  單點 fn／治理域讀端／測試基建四守衛家族＋contract registry／名冊閘）；本刀純消費、不改基建語意。
- 起手維護批已 merge（handler/common.rs 六件＋facade violated_constraint；test_db::test_state 單一字面＋
  (Router, AppState) 變體；wire-schema RoleAdmin／MenuAdmin 裁判）——本刀新 handler 引用 common、零拷貝。
- 單副本部署前提（ADR 0014）；判定面同步不需跨副本廣播。
- seed 政策列與選單列凍結不動；dev 環境（容器內 build/test、serial）；CDP 對照環境照 CLAUDE.md §7。
- 刀 B（user＋password）另開：seed 68 updateUserSessionPolicy、getAllRoles 零 UI 消費者窗、B-093 復核、
  跨刀鉤子句（sys_user_role 指派寫端）皆歸彼。

### Out of Scope

- no-escalation 真邏輯（空 seam 恆 Ok 不動、留翻案刀；B-024 殘餘一句）。
- 選單維 protected 四列之封死（已知態）；靜態守恆「治理面 Policy 端點 seed v0 恆 R_SUPER」（B-075 不入）。
- Api.IpRule.* 七支 wire 裁判（B-098 留帳）；ip_rule.rs／throttle/mod.rs 殘餘兩處 AppState 薄殼化（B-109）。
- user 域一切（含 updateUserSessionPolicy、角色指派、密碼面）——刀 B；B-008 餘兩張 view（system-settings／
  audit＋audit 5 支端點）。
- 即時推播刷新前端授權顯隱；增量式授權寫入介面；un-protect／re-protect 管理介面。
- 列表排序能力（B-027 續掛）、`real_ip` gist 索引（B-082 續掛）。
