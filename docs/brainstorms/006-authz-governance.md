# 006-authz-governance — 三維授權治理＋結構性封死＋授權回收桶（刀 A2）

> 階段 0 brainstorm **定稿（2026-08-22 全面重寫）**。本檔取代 tmp/006-authz-governance.md
> （2026-08-18 舊草稿、未進版控）——005 實作期間的 spec 重劃與 as-built 補記已使舊草稿多處
> 失真，本次以五 lens 偵查 workflow（005-asbuilt-delta／scope-seed／backlog-triage／
> governance／frontend）逐項機器對賬後重寫；舊草稿仍成立的段落經對賬後沿用。
> 血緣：與 [005-role-menu-crud.md](005-role-menu-crud.md) 為**同一次 brainstorm（2026-08-18）
> 的拆刀產物**（原單刀 tmp/005-role-menu-admin.md「刀 A＝role+menu」沿縫 α 裁開；拆刀由 user 拍板）。
> 基準＝rev5-admin-root @ e682f5e（005 收刀簿記；merge 0125f8c）；pins rust-api=6aed6d5／
> base-web=0af3690f；憲法 v1.7.0（277 行）；ROUTES 38；rust 測試 650；backend i18n 樹三語各 50 鍵。
> ★§10 之 22 題已於 2026-08-22 grilling 輪（AskUserQuestion 逐題、user 親決）**全數拍定**——
> 決議逐題見 §10 各題「➡️ 拍板」行、總表與連動後果見 §11；本檔自此為 speckit-specify 的直接輸入。
> 005 動工前提已成立（005 已收刀、三倉已推）；005 research 已落版控＝
> specs/005-role-menu-crud/research.md（不再引 per-machine scratchpad 路徑）。

## §0 拆刀縫與 005 底座已兌現清單

**縫 α 分水嶺＝「grant/revoke 寫 casbin_rule」——本刀就是 grant 面**：結構性封死（B-024①歸宿）
與 protected-reject（島 G2）皆掛本刀寫端；熱重載基建已隨 005 落地（grilling G1）、本刀純消費
＋島 G 條文隨本刀入憲。**005 底座八件皆已兌現、本刀直接消費**（as-built 形與指針逐項）：

1. **advisory 序列化域**（facade/sys_casbin_archive.rs）：`MENU_DOMAIN_LOCK_KEY=0x7265_7635_6D65_6E75`
   （:49）；兩形薄 fn＝`enter_menu_domain_db`（:61、DbErr 形、facade txn 內接縫）／
   `enter_menu_domain`（:74、AppError 形、handler 接縫）；觀測唯一正解＝`menu_domain_waiter_count`
   （:91；64-bit key 在 pg_locks 拆 classid/objid、bigint 直比撞 OID 界、pg_blocking_pids 對本域
   結構性測不到——呼叫端不得自寫比對 SQL）。固定鎖序（模組 doc:19-21 寫死）＝advisory →
   歸檔表列 → sys_role 列 → sys_menu 列 → casbin_rule。★域鎖 MUST 為 txn 首動作，機器證形＝
   **逐寫端各配一支** pg_locks NOT-granted 等待測（sys_menu.rs:3046 註明理由；現七處同形＝
   sys_menu 五〔create／update／soft_delete／batch／restore〕＋sys_role 二〔delete／batch〕）——
   本刀 updateRoleMenu／updateRoleButton／restorePolicy 選單按鈕分支三支各需一支，
   缺測則刪掉那行 enter_menu_domain_db 全測仍綠。
2. **casbin rebuild-swap 熱重載**（auth/enforce.rs）：`rebuild_enforcer`（:107）／`reload_enforcer`
   （:163、無回傳）；`RELOAD_MAX_ATTEMPTS=3`（:81）＋`RELOAD_RETRY_BACKOFF_MS=50`（:83）；
   keep-last-good＋metrics `casbin_reload_total{ok|retry|exhausted}`（:174/:178/:194）。呼叫端硬紀律
   （:128-136）：**不得持 state.enforcer 讀鎖呼叫**（tokio RwLock 不可重入＝永久互鎖）、正道恆為
   「commit、讀鎖全釋之後才呼叫」——兩道名冊閘對此形結構性無感、唯靠紀律。
   ★**RELOAD_SERIAL**（005 收刀期補、舊草稿零涵蓋）：`static RELOAD_SERIAL: tokio::sync::Mutex<()>`
   包 rebuild＋swap 含重試全程互斥（:150-157 doc＋:166-167）——封「後 commit 先 swap／先 commit
   慢 rebuild 蓋回舊快照＝已歸檔列判定面復活」窗；誠實缺口＝B-105（§8-2）。
   觸發矩陣 as-built＝恰移除面三支、一律 `if archived` 為門（:138-148；:148 釘「恆發生形＝出生
   即誤、勿回帶」）。
3. **archive 寫入面**：`insert_archived(conn, &casbin_rule::Model, reason, archived_by)`
   （sys_casbin_archive.rs:166-196）——★**role_id 由 fn 內收 v0 反查活性角色自動填**（:172-177、
   T014 as-built 拍板），rev4 caller 傳 role_id 形不得帶回；回 `()` 不回歸檔列 id。
   `archive_all_role_policies`（:223）；掃描 helper as-built 形＝sys_menu.rs:755 私有
   `archive_policy_rows_of`（(v1,v2) 雙欄圈定＋跨維誘餌測已建；刪除集以剛歸檔那批 id 圈定、
   不重跑過濾）。
4. **reason gate**：三常數（:113/:117/:121）＋單點 fn `is_non_restorable_reason`（:132、三值集
   `{role_soft_delete, menu_soft_delete, menu_button_removed}`）；集合成員測之負向集已預留本刀
   三個 revoke reason 字面（menu_revoke／button_revoke／endpoint_revoke）；本刀兩消費面
   （getArchivedPolicies 之 restorable 旗標＋restorePolicy 鎖內權威判定）MUST 共用此 fn。
5. **治理域讀端**（facade/sys_menu.rs）：`list_governed`（:162、未刪含停用）／`build_governed_tree`
   （:192；三律＝父不在集合升根、order→id 穩定排序、環整環靜默缺席）／`page_query_governed`
   （:261）／`menu_tree`（:309）；顯示域＝`list_active`（:108、啟用∧未刪）。本刀 menu 維授權
   候選集直接消費治理域（FR-019：治理候選 MUST NOT 誤用顯示域）。
6. **handler 慣例**（handler/role.rs 照抄形）：json_or_default（:236）／tristate（:216）／
   blank_to_none（:369）／map_*_err 四支／audit_operator（:453、上下文缺席拒寫 5000）／
   resolve_operator_names（:496）／MAX_CURRENT（:518）；PageRes 已上移 envelope.rs:104；
   status wire 二值收斂；誠實 null；★稽核詞彙恰五值不擴（audit.rs t005 機器釘）——本刀三維寫端
   用 `update`、restorePolicy 用 `restore`，不得新增 grant/revoke variant。
7. **測試基建**：四守衛家族＋seq 定案值（RoleCleanup setval 3,true／MenuCleanup 78,true／
   CasbinCleanup 163,true＋archive seq 1,false／UserCleanup 雙腿）；contract.rs registry＋coverage
   gate 雙向＋case_key 綁定自證＋授權態矩陣對照凍結 seed 政策列——本刀每支新端點必配全套。
8. **名冊閘與判定收斂閘**（tests/authz_entrypoint_lint.rs）：`RELOAD_CALL_FILES=["handler/menu.rs"]`
   （:353；本刀須擴列）；`ENFORCER_WRITE_FILES=[]`（:584、維持空冊——絕不自取
   `.enforcer.write()`）；`ALLOWED_DECISION_FILES=["auth/enforce.rs"]`（:77）；casbin 版本錨
   2.20.0（:820）不得升版。判定面三規則：判定只呼 `enforce_role_path_method`（pub(crate) ⇒
   端到端判定測內嵌 src/ 的 `#[cfg(test)]`、T032 先例）；枚舉政策走 `MgmtApi::get_filtered_policy`
   （visible_menu_routes／buttons_of_roles 先例）；protected 判定走 DB／entity 面（casbin_rule
   entity 11 欄、adapter 只見 8 基底欄，protected 對 adapter 不可見）。

## §1 背景與觸發

- **指派來源＝NOTES（權威）**：對本刀的四項指派只存在 docs/ops/NOTES.md「★下一刀」段——
  ①射程＝三維授權治理 11 支＋島 G 入憲＋結構性封死（B-024①歸宿）＋policy-archive 頁（B-008
  出列一張）②起手維護批＝B-094＋B-101（2026-08-22 改期落此）③島 G 入憲順捎＝ADR 0052 條款
  入憲法 §III 正文＋B-104 ④brainstorm 自 tmp/ 補入版控、specify 必手動起手。★005 之
  feature_close 事件無任何指派欄——本刀收刀 feature_close 的 notes 欄須寫明承接關係、防同型斷鏈。
- **消化帳目（BACKLOG 現存 45 條、next B-106 全數分流）**：必辦 11＝B-024①（§4-②）、B-008
  出列 policy-archive（餘 system-settings／audit 兩張）、B-094＋B-101（起手維護批）、B-104
  （島 G 入憲時訂正）、B-105（動判定面時）、B-099（按鈕碼授權真管刀＝本刀）、B-102＋B-098
  （本刀動 role handler 與 contract 測家族）、B-091（rider）、B-025（帳面敘述更新、不關帳）；
  拍板 1＝B-083（活書 §6 已 120/120，§10-16）；順捎候選 3＝B-085（自拍納入 U0）、B-088
  （§10-20）、B-075（§10-22）；不入 30（觸發在別刀或前提未成立）。
- rev4 藍本＝rev4:specs/009-role-admin 之 FR-017~FR-026（三維治理狀態機、含支撐讀候選
  FR-025）＋FR-027~FR-032（回收桶、含 FR-032 i18n）＋FR-033~FR-036（拒因鍵與明細通道）；
  FR-037~FR-039（roleHome）已隨 005 交付、不在本刀後端射程（UI 消費者見 §5、§10-10）。
- rev3 有 no-escalation 唯一實作先例（commit 3bfab71）——本刀不採（改結構性封死）、留翻案刀參考。

## §2 射程：11 支端點（ROUTES 38→49；seed 政策列 100% 預埋；零 migration——唯一威脅見 §10-6）

授權角色全 R_SUPER（seed 逐列機器複核）；★＝seed protected=TRUE（11 支中佔 10 列、
僅 getAllPages 為 FALSE）。

| 端點（/systemManage/…） | 動詞 | seed | prot | rev5 真源／缺口 |
|---|---|---|---|---|
| getRoleMenu | GET | 32 | ★ | facade/sys_casbin_policy.rs（新檔）＋治理域 menu_tree |
| updateRoleMenu | POST | 33 | ★ | 全量替換 diff；入域；grant 面 reload |
| getRoleButton | GET | 53 | ★ | 同上 facade |
| updateRoleButton | POST | 54 | ★ | ＋orphan skip（候選集＝sys_menu.buttons 治理域聯集）；入域 |
| getRoleEndpoints | GET | 56 | ★ | 同上 facade |
| updateRoleEndpoints | POST | 57 | ★ | ＋結構性封死鎖內守門；不入域 |
| getAllButtons | GET | 52 | ★ | ★rev5 無 public reader——新建 `all_button_codes`（治理域；rev4:facade/sys_menu.rs:306 藍本；現有私有 button_codes_of :694 與絕版判定掃描語意不同、不可複用） |
| getAllEndpoints | GET | 55 | ★ | ROUTES const 濾 Policy（原料全 pub）；★E0391 坑：抽具名 `policy_endpoints() -> Vec<Endpoint>` 斷環（rev4:role.rs:675-687 逐字解說）；回應集 24→35 |
| getAllPages | GET | 26 | — | `list_active` 已 public 零缺口；域選擇＝§10-9；★既有破口自動修復（下） |
| getArchivedPolicies | GET | 70 | ★ | archive 表雙濾＋PageRes；001 索引現成（idx_casbin_archive_role_dim (v0,v2)／archived_at）＝讀端零 migration；baseline 零列⇒契約測自建 fixture |
| restorePolicy | POST | 71 | ★ | rev4:facade/sys_casbin_archive.rs:330 restore 七步藍本；選單／按鈕分支入域 |

- ★**getAllPages 既有破口**（005 未列已知態）：menu 管理頁已在呼叫該路徑（menu/index.vue:10／
  :302-306／:401 → system-manage.ts:42-47），而 ROUTES 38 條無此路徑⇒現況恆 4040、
  menu-operate-modal 消費 allPages 的下拉（page／activeMenu 兩欄共用 pageOptions）**新增模式
  恆空、編輯模式僅剩當前 routeName 一項**（:152-158 unshift 保底）。本刀交付端點即自動修復、
  前端零改動——這是明確交付效果、不是「沒人用的支撐讀」。
- **protected 帳（機器數、與敘事分清）**：seed protected=TRUE 共 **19 列全 R_SUPER**＝
  端點維 **15 列**（32/33/52~57/64~68/70/71）＋menu 維 4 列（10 manage_role／11 manage_menu／
  69 manage_system-settings／72 manage_policy-archive）。端點維已上線 4 支（64/65 隨 005；
  66/67 隨 002）、待本刀 10 支、無主 1 支（68）。「治理面 12 支」＝敘事標籤、非機器謂詞產物
  ——條文落字見 §10-2。
- **鄰接面（本刀不做、留給誰）**：seed 未上線存量恰 26 支＝本刀 11＋audit 5（139/140/141/
  158/159→B-008 audit 頁）＋user 域 9（1+2/17/18/19/20/151/152/154/155→刀 B）＋
  **updateUserSessionPolicy（68、POST、protected=TRUE）無主**（歸屬＝§10-19；謂詞式守門下
  上線即自動納管、不阻塞本刀，但本刀 spec 不得宣稱「治理面 protected 端點集已全數上線」）。
- **本刀交付後殘留已知態**（005 已知態三組①②③全數被本刀消滅；本段取代之）：
  (a) B-008 餘兩張死項 system-settings／audit（側欄零反應＋顯示原始 i18n key）；
  (b) getAllRoles 零 UI 消費者窗（歸刀 B）；(c) roleHome 窗視 §10-10 拍板；
  (d) ★本刀**新造**已知態：updateRoleMenu 可授予「指向不存在 view 的自建選單」⇒側欄可見
  但點擊零反應（B-088 描述形）——必明寫 spec Edge Cases；(e) seed 68 未上線（見上）。

## §3 拍板全紀錄（2026-08-18 拍板；收錄結論與歸屬、as-built 修正一律寫標註欄不動結論字面；關鍵理由欄不重載→見 [005-role-menu-crud.md](005-role-menu-crud.md) §3〔同次 brainstorm 姊妹檔、已進版控〕；「as-built 標註」欄＝005 收刀後成立性）

### user 親決 15 題（2026-08-18）

| # | 題 | 結論 | 歸屬 | 005 as-built 後標註 |
|---|---|---|---|---|
| 1 | 刀怎麼切 | 刀A=role+menu、刀B=user+password；刀 A 沿縫 α 拆 005/006 | 全 | 仍成立。★關鍵理由原文「ADR 0051 序列化域硬耦合」之指涉＝**rev4:ADR 0051**（選單域狀態機總綱）——rev5 ADR 0051 已另有所指（restoreMenu 常量父鏈腿、2026-08-22 accepted），裸號即撞號 |
| 2 | 前端腿 | 前後端同刀 | 全 | 仍成立 |
| 3 | 三維授權治理 | 納入刀 A（拆刀後＝本刀全部射程） | 006 | 仍成立 |
| 4 | （刀 B 預拍）自助改密 | 全納入含 changePassword | 刀 B | 仍成立、與本刀無涉 |
| 5 | 授權模型深度（B-024①） | **結構性封死授出**：治理面 12 支 protected 端點 MUST NOT 授予非 R_SUPER；updateRoleEndpoints／restorePolicy 鎖內驗、違者顯式拒 | 006 | 成立；★標的集數字修正：「12 支」為敘事標籤，DB 謂詞（ptype=p ∧ protected ∧ v2∈HTTP 動詞）實圈 **15 列**（多 66/67/68）——條文落字→§10-2 |
| 6 | casbin 熱重載 | 照搬 rev4 重建-swap | 005 建基建、006 消費 | 已兌現（005 §4-⑤＋ADR 0049）；★收刀期另補 RELOAD_SERIAL 跨端點序列化（§0-2、§4-①） |
| 7 | 治理拒因明細（B-024③） | 全降級純 key；島 G2 條文不綁載體 | 006 | 仍成立；「protected 集靜態（19 列全 R_SUPER）」機器複核成立 |
| 8 | deleteRole 入域 | 拉進序列化域（batch 同） | 005 | 已兌現 |
| 9 | updateRoleButton 候選驗證 | **加 orphan skip**（對稱 menu 維；候選集＝sys_menu.buttons 聯集、界外碼靜默略過、回應帶實際生效集合） | 006 | 仍成立；★帳務框架修正：B-025 已於 2026-08-22 改寫，orphan skip 不消費其客戶——效果＝堵孤兒列**產生面**（§6 帳務） |
| 10 | archive 表三自由度 | 全不動（nullable／不加 protected 快照／不加 menu_id） | 005 | 已兌現；★新增承重前提：ADR 0050 §4 翻案觸發條款已被本刀 updateRoleMenu 之 revoke 面命中（menu_id 同實例欄復核＝§10-6、零 migration 唯一已知威脅） |
| 11 | constant 欄 | 可寫＋父鏈常量性守門 | 005 | 已兌現、本刀無涉 |
| 12 | restore 按鈕碼 gating | 不 gating（頁級＋列級兩道門；policy-archive restore 同） | 005/006 | 仍成立；seed 選單列 10 之 buttons=NULL（零按鈕碼可用）佐證 |
| 13 | 選單回收桶 UI | toggle 形照 rev4（本刀 policy-archive＝獨立頁、即 rev4 原形） | 005 | 仍成立 |
| 14 | static meta 紀律 | DB 唯一真源、不維護 static meta | 全（本刀 policy-archive 新頁進場適用） | 仍成立；seed 列 10 icon=`mdi:recycle`＝唯一真源（rev4 兩處 icon 不一致即前車） |
| 15 | 修憲次數 | 拆刀後各刀一次 MINOR——005 落島 H、006 落島 G（v1.7.0→v1.8.0） | 全 | 005 半已兌現（v1.7.0、2026-08-18）；本刀落 v1.8.0 仍成立 |

### 主線自拍（回報備查；含 as-built 標註）

- 結構性封死拒因＝既有 `2222`＋新 i18n 鍵（零新錯誤碼、不動 13 碼凍結面）｜006｜仍成立。
- 三維 modal 觸發鈕不做 hasAuth gating（照 rev4；門在頁級 R_SUPER）｜006｜仍成立；rev5 已釘
  「rev4 hasAuth gating 屬已推翻行為、不帶回」（menu/index.vue:339-341 逐字）。
- no-escalation 空 seam 恆 Ok 不動——掛點、metrics 位、測試旗標保留給未來翻案刀｜全｜成立；
  ★位置訂正：as-built＝auth/enforce.rs:217 `no_escalation_check`（唯一呼叫點 :248
  `enforce_role_path_method`；測試旗標 :206 `NO_ESCALATION_FORCE_DENY`）——舊草稿之 :92 已漂移。
- 域鎖 key＝`"rev5menu"`（005 建）；PageRes 上移（005 做）｜005｜皆已兌現
  （sys_casbin_archive.rs:49／envelope.rs:104）。

### grilling 輪六題（user 親決 2026-08-18；含 as-built 標註）

| # | 題 | 結論 | as-built 標註 |
|---|---|---|---|
| G1 | 熱重載基建歸屬 | 移入 005、本刀純消費 | 已兌現；rev4 呼叫點行號 :329/:348/:364 機器複核命中。★rev5 對 rev4 的未記載改進：rev4 deleteMenu／batchDeleteMenu 為**無條件** reload（rev4:handler/menu.rs:348/:364）、rev5 三支一律 `if archived` 為門——列入 §9 不得帶回清單 |
| G2 | 選單可見性窗 | 接受＝005 已知態 | 已兌現為 005 已知態③；本刀 updateRoleMenu 即缺席的第二步工具、交付即消滅。★延伸形：v2='menu' 四列 protected 政策不在封死謂詞射程（§10-8） |
| G3 | 前端檔清單 | 兩授權 modal 檔屬本刀（005 一行不動） | 成立；005 零 diff 承諾已機器驗證（兩 modal 與最原始源基線 example tip **逐位一致**、diff 零輸出） |
| G4 | getMenuTree 歸屬 | 移入 005（本刀支撐讀 4→3） | 已兌現（routes.md 在冊、seed 27、sys_menu.rs:309、前端 wrapper rev5-menu-admin.ts:43）——舊草稿 §8-3「歸屬開放點」已消滅、本檔不再列 |
| G5 | memo 欄 | 005 兌現 role_memo＋menu_memo | 已兌現 |
| G6 | 守門兩腿窗 | 接受照建＋spec 註記 | 已兌現（005 spec 註記） |

## §4 核心設計

**① casbin 熱重載消費接線（島 G1）**：基建全套已於 005 交付（§0-2）。本刀三件工作：

- **grant 面接線**：updateRoleMenu／updateRoleButton／updateRoleEndpoints＋restorePolicy 之
  Applied 腿——`txn.commit()` 之後、讀鎖全釋後觸發同一支 `reload_enforcer`；Rejected 走 `?`
  早退＝「被拒不 reload」的結構性保證。★grant 面 outcome **恰兩態** `Applied{revoked,granted}`
  ／`Rejected{blocked}`——**無 NoOp 態**（NoOp 屬 restore 路徑；rev4:model/facade/
  sys_casbin_policy.rs:81-84 明文「本寫端無 NoOp 態」；舊草稿「Rejected／NoOp／NotFound 一律
  skip」為措辭失真、勿據以設計四態 enum）。★**空 diff 是否觸發 reload＝拍板題（§10-4）**：
  rev4 空 diff 仍 Applied 仍 reload（:472 測「刻意不優化」）vs 005 as-built 移除面「零變更
  零觸發」哲學相抵——沉默照抄任一邊都會讓 enforce.rs 觸發矩陣 doc 同時容納互斥兩句。
- **島 G1 條文入憲**：兩半（DB-first 真相唯一＋失敗契約）已分別由 ADR 0050 §3 首條與
  ADR 0049 §2 逐字承載，本刀合成一條轉正；★觸發面落字＝§10-3（勿抄 rev4「Applied 含空 diff
  才觸發」字面——那正是 B-104 要訂正的錯誤形之鏡像）。
- **名冊擴列**：`RELOAD_CALL_FILES` 擴為 `["handler/menu.rs", "handler/policy_archive.rs",
  "handler/role.rs"]`（路徑字典序；主守恆集合恰等、兩向皆紅——不擴列接線當場紅）；
  `ENFORCER_WRITE_FILES` 維持空冊；casbin 釘 2.20.0 不升版。
- 連帶效應：B-093 之判定面繼承窗因 reload 觸發面擴大（3→7+ 支呼叫者）而**時距縮短、但不閉合**
  （閉合仍歸刀 B 的指派寫端）——收刀時 B-093 條文補一行敘述。

**② 結構性封死（B-024①歸宿；條文位置＝§10-1、落字＝§10-2）**：

- 不變式：治理面 protected 端點 MUST NOT 授予非 R_SUPER。標的集＝**謂詞式**
  （`casbin_rule` 中 `ptype='p' ∧ protected=TRUE ∧ v2∈HTTP 動詞` 之 (v1,v2) 集、DB 態鎖內現查
  ——機器數現值 15 列；條文勿寫死列數，防 68 上線或未來刀新標 protected 時改憲）。
- 掛點＝updateRoleEndpoints 與 restorePolicy 的**鎖內**守門（照 rev4 判準「涉 DB 狀態一律
  鎖內」）、違者 `2222`＋新 key。非 vacuous：超管在 UI 真做得出「把治理端點授給 R_ADMIN」、
  守門真擋、測試零旗標；落地必配變異自證（弄壞→紅→還原→綠；L-010／L-019）。
- ★**承重前提明文（舊草稿未點出）**：ADR 0050 §4 ② 三不變式——「可復原列必經 revoke 路徑、
  而 protected-reject 保證含 protected 列的撤銷整批拒 ⇒ revoke 歸檔列原值恆 protected=false、
  protected=true 列結構上進不了 archive」。005 的零 migration（不加 protected 快照欄）**以本刀
  兌現整批拒＋un-protect 永不 UI 化為前提**；本刀任一處鬆綁封死語意＝觸發該 ADR 翻案條款
  ＝該刀必自帶 protected 快照欄 migration。
- 已知態：v2='menu' 的四列 protected 政策（manage_role／manage_menu／manage_system-settings／
  manage_policy-archive）**不在謂詞射程**——超管仍可經 updateRoleMenu 把系統管理目錄可見性
  授予 R_ADMIN；端點層仍 5003、非提權破口（擴不擴＝§10-8）。
- B-024 三件套歸宿：①封死＋翻案觸發條款（真要多層管理員時翻案刀建真 no-escalation；rev3 原形
  〔desired⊆own、handler 層、2222〕與三缺陷〔靜默壓縮授權、漏 restorePolicy、TOCTOU〕留參照）
  ②seeded 護欄三套照 rev4（`SEEDED_ROLE_IDS=[1,2,3]` 已在 sys_role.rs:67、有逐位自證測）
  ③明細受眾邊界隨封死自動保持（重評結論＝維持純 key、入 ADR 0054）。★B-024 條目預查三筆照吃：
  (a) ADR 0022 第 3 款「零簽章變更」在真邏輯需 body 時不成立（no_escalation_check 四參無 body
  通道、require_policy 跑在 body 解析前）——封死正好繞開此坑、spec 須寫明繞開理由
  (b) 熱重載前置已由 005 兌現、自此非前置 (c) ADR 0022 後果末條「填入查庫邏輯後把掛點呼叫移到
  取讀鎖之前」**無任何測試自動抓、tasks 須顯式列一條**——本刀不填 seam ⇒ 該句留殘餘
  （B-024 整關與否＝§10-17）。

**③ 三維授權寫端（島 G2/G5）**：

- 全量替換 diff 形；撤銷集觸及 protected → **整批拒、零變更**（任何寫之前判定）；
  un-protect／re-protect 經一般管理介面**永不提供**（防鎖死 by-design）。
- grant＝INSERT 補齊治理欄（protected=false＋created_at/by）；revoke＝archive-move——
  ★rev5 簽名＝`insert_archived` 內收 v0 反查（§0-3）：本刀 revoke 路徑**不傳 role_id**；
  因標的角色列已 FOR UPDATE 鎖住且活性，role_id 恆 Some(role.id)、同實例判定在該路徑恆成立、
  真正擋的是「刪後同 code 重建」。反查刻意不加鎖（不拉不相干列進鎖足跡）、caller 自鎖標的
  角色列（lock-then-redecide、永不信 pre-read）。revoke reason 字面＝沿用 reason gate 負向測
  已預留三字面 `menu_revoke`／`button_revoke`／`endpoint_revoke`（主線自拍；理由＝改用別的
  字面該測不紅但語意與預留錯開）。
- **入域成員（★rev5 條文終態；舊草稿 §4-④ 沿 rev4 形把 restorePolicy 整支入域——忠實轉述
  rev4 as-built、非「誤」，但與 rev5 H1 終態成員字面不一致）**：updateRoleMenu
  ／updateRoleButton＋**restorePolicy 之選單／按鈕分支**（憲法 §I.7 H1＋rev5
  sys_casbin_archive.rs:14-17 條文終態；updateRoleEndpoints 與 endpoint 維復原**不入域**）。
  ★rev4 as-built＝restorePolicy **無條件**入域，理由與代價逐字在碼註
  （rev4:facade/sys_casbin_archive.rs:338-341：「維度須讀 archive 列 v2 才知、uniform 取鎖比
  條件取簡單且絕對安全」；「代價＝endpoint 維 restore 亦序列化於選單域、可接受」）。
  域鎖 MUST txn 首動作 ⇒ restorePolicy 的
  維度分岔須在 `begin` 之前決定（先讀歸檔列 v2 再定入域與否、或照 rev4 一律入域＋ADR 記
  放寬 H1 字面）——spec 期必須釘死的結構點（§8-3；選項二＝rev4 as-built、分析現成勿重跑）。
  三支入域寫端各配 NOT-granted 等待測（§0-1）。
- updateRoleButton **orphan skip**（候選集＝sys_menu.buttons 治理域聯集、界外碼靜默略過、
  回應帶實際生效集合）；menu 維 orphan skip 照 rev4。
- 掃描面落點照 005 已定形：掃描迴圈落標的 entity 的 facade、只消費公開 primitive
  insert_archived（archive_policy_rows_of 先例）；rev4 之 archive_all_menu_policies／
  archive_button_code_policies 兩支具名 fn 形**不帶回**；撤銷面刪除集一律以剛歸檔那批 id 圈定。
  ★順修：sys_casbin_archive.rs:34-36 模組 doc 失真句（「歸 T024/T025 隨各寫端建、屆時續住
  本檔」——as-built 實落 sys_menu.rs）——本刀動該檔時一併修（B 級帳面）。
- protected 判定走 DB／entity 面（§0-8 三規則）；handler 層零 `entity::`（entity_access_lint）。
- 契約鍵 `roleId` vs `id`＝§10-11；protected UI 預標載體＝§10-12。

**④ 授權回收桶**：

- **getArchivedPolicies**：PageRes 分頁＋雙濾（來源角色 v0／維度 v2）＋archived_at DESC——
  001 基線索引現成＝讀端零 migration；維度由 v2 值推導（rev4:dimension_of :255 形、無維度欄）；
  restorable 旗標**兩半**＝`!is_non_restorable_reason(reason)` ∧ role 側同實例（歸檔列
  `role_id == 現存同 code 活角色 id`；role_id 為 NULL→false——rev4:facade/
  sys_casbin_archive.rs:299-311＋rev4 FR-029 逐字「且現存同代碼活性角色與歸檔列記錄的來源
  角色識別為同一實例」）；非權威預告、但 MUST 與 restore 權威判定同判準（reason 半共用單點
  fn＋同實例半同式；rev4 :357 註「單點 fn 與 list 旗標共用、防漂移」——旗標寫窄成只比 reason
  ＝把 restore 當場會拒的列標成可復原）。
  ★批次料源缺件：旗標同實例半的料源 rev4:`sys_role::active_ids_by_codes`（rev4:facade/
  sys_role.rs:115）在 rev5 **不存在**（公開面僅單列形 find_active_by_id/code_for_update）——
  主線自拍＝自建批次讀端（理由：批次避免逐列查角色；resolve_operator_names
  的 N+1 債已在 B-094 名下、不宜再添一筆）。
- **restorePolicy 七步鎖序**（rev4:facade/sys_casbin_archive.rs:330 restore 藍本）：
  入域（★rev4 原形＝**無條件**取鎖 :338-341；rev5 擬收窄為僅選單／按鈕分支＝§4-③ 待決
  結構點）→鎖 archive 列→鎖角色列→**鎖內重驗**→回灌 casbin_rule→刪 archive 列
  →op-log；outcome 三態 Applied／NoOp／NotRestorable（rev4:handler/policy_archive.rs:10-11）；
  Applied 觸發 reload。鎖內重驗現定四腿：reason gate（MUST 寫 `!is_non_restorable_reason(reason)`
  ——單點 fn 三值集已收斂，不可只比 role_soft_delete）＋role 側同實例（現存同 code 活角色
  `id == 歸檔列 role_id`；NULL→不可復原、誠實退化）＋**menu 維治理域 orphan**（v2=='menu' 時
  標的 route_name 須在 `list_governed` 治理域〔未刪含停用〕、orphan→NotRestorable、非 menu 維
  跳過——rev4 既有腿：rev4:facade/sys_casbin_archive.rs:379-389 第⑥步＋rev4 FR-031
  「不灌無效授權」）＋結構性封死守門（防經回收桶把 protected
  端點政策復原給非 R_SUPER——與 updateRoleEndpoints 同一守門、雙路徑全覆蓋）。
  前三腿沿 rev4、封死腿 rev5 新增。
- ★**復原重驗腿數不足＝本刀最大設計開放點**（§10-6／§10-7）：ADR 0051 取態「復原＝重入治理域
  須全套重驗」同構套用，至少四腿未答——(a) **menu 維同實例**（與既有治理域 orphan 腿不同軸：
  orphan 管標的存在性、同實例管 route_name 重建後的實例身分——orphan 腿對「軟刪後同鍵重建」
  的新實例恰判 governed、擋不住繼承）：ADR 0050 §4 翻案觸發條款已被
  本刀 revoke 面命中（手動撤銷 reason 依定義可復原 ⇒「menu 維歸檔列結構性無復原路徑」前提
  自本刀起不成立；標的選單於歸檔期間被軟刪並同 route_name 重建後復原＝新實例繼承舊實例授權
  ＝直接違反已入憲的島 H2「同鍵重建零繼承」——憲法「回收桶復原」逐字在列）；(b) **button 維
  孤兒**：updateRoleButton 有 orphan skip、restore 路徑沒有——歸檔期間該 code 可能已全域絕版；
  (c) **endpoint 維下線**：歸檔列 (v1,v2) 可能已不在 ROUTES——rev4 **不驗**
  （rev4:facade/sys_casbin_archive.rs:379-389 第⑥步僅 menu 維、逐字「非 menu 維跳過」；鎖內
  重驗至此為止、第⑦步即落地），rev5 要不要補這一腿＝§10-7 腿集拍板；
  (d) **復原到停用角色**：rev4 同實例只驗活不驗 status——停用即斷權沿基線行為、
  無立即危害、as-built 明記已知態。定稿形＝固定序 N 腿表格（照 ADR 0051 落字範式、每腿註明
  對應的現役寫端守門）、由 ADR 0055 承載（§6）。

**⑤ 檔案落點與支撐讀（rev4 對照）**：三維 6＋支撐讀 3（＋roleHome 既有 2 支之 UI 若納入）→
`handler/role.rs`（現 8 支→17 支）；回收桶 2 → **新檔 `handler/policy_archive.rs`**（rev4 獨立檔
709 行；rev5 handler/mod.rs 註冊行依模組名 ASCII 升冪、插 menu 與 role 之間）——舊草稿把回收桶
寫進 role.rs、與藍本不符且令 role.rs 過肥；★順修 handler/mod.rs doc「role（role 管理六端點）」
既有失真（as-built 已 8 支）。facade 新檔＝`sys_casbin_policy.rs`（rev5 現 11 支→12 支；rev4
912 行藍本、公開面九項；★`BlockedTarget`（rev4 :75、protectedRevoke 明細陣列載體）不帶回、
set_role_dimension 回傳形連帶簡化）。支撐讀三支細節見 §2 表。

## §5 前端面

- **三顆授權 modal**（憲法授權形式＝§10-13；掛載點＝`role/modules/role-operate-drawer.vue`
  ——rev4 :132-138／rev5 現況兩鈕 :164-167，**role/index.vue 預期一行不動**、舊草稿「role 頁掛
  三 modal」定位失準）：
  - `menu-auth-modal.vue`（修改型、與基線逐位一致起改；rev4 同檔 6 條 `原行:` 可參）：★現況
    比舊草稿細緻——樹已是**真的**（fetchGetMenuTree 打 005 已交付端點）；假的只有 checks
    （寫死 [1..21]）與 home（寫死 'home'）；fetchGetAllPages 打不存在路徑⇒4040 notFound toast。
    本刀改接 getRoleMenu／updateRoleMenu、改走 rev5 wrapper。CDP 判準連帶修正：不能用
    「假樹 vs 真樹」、改用「勾選是否 1..21 連號」與「notFound toast 消失」。
  - `button-auth-modal.vue`（修改型；★rev4 同檔 **21 條** `原行:`——upstream 寫死的
    button1..button10 假資料逐行都要標，工時照此估、勿與 menu 側齊平）：接 getRoleButton／
    updateRoleButton＋getAllButtons 候選集。
  - `endpoint-auth-modal.vue`（**新增型新檔**、rev4 134 行藍本、零原行不入名冊）：葉鍵
    `${path}|${method}` 合成＋群組鍵＝純 path（結構性不碰撞）；`leafMap` 反查還原 `Endpoint[]`
    ——**不 split '|'**（防 path 內含分隔符誤拆）；`check-strategy="child"`。
  - ★rev4 之 `protected-revoke-detail.ts`（36 行、三 modal 共用明細渲染 helper）**不帶回**
    （rev5 拍板純 key）：錯誤分支收斂為既有形 `if (error) return;`（拒因 toast 全由共用攔截層出）；
    連帶不擴 `service/request/index.ts` 之 DETAIL 對照表、不建 `ProtectedRevokeDetail` 型
    ——rev4 三 modal 各有一行該 import、重打時極易漏審，明記於此。
- **roleHome UI（新射程項；納入與否＝§10-10）**：rev4 的 roleHome UI 家＝menu-auth-modal.vue
  （rev4 :38-53 getHome/updateHome＋:126-129 NSelect），005 spec Edge Cases 已明文交棒本刀；
  rev5 現況零 fetcher 零呼叫點。若納入：rev5-role-admin.ts +2 fetcher＋d.ts +2 型＋同檔 4 處
  接線；候選源＝getAllPages（三者同顆 modal 內閉環）。★**rev4 碼不可照抄**——rev5 契約已判
  三處不同（handler/role.rs:174-203 逐字「rev4 形不帶回」）：query 鍵 `roleId`→`id`、回應
  裸 string→`{home}` 物件、NULL 誠實下發 null（rev4 摺疊空字串；前端初值形連帶改）。
- **policy-archive 新頁**（新增型；B-008 死項出列）：`views/manage/policy-archive/index.vue`
  （rev4 153 行藍本；純列表＋restore、無 create/edit）＋`modules/policy-archive-search.vue`
  （rev4 92 行；roleCode×dimension 雙濾）。seed 選單列 10 逐欄實況：status=1、order=5、
  hide_in_menu=NULL（側欄會現）、protected=TRUE、parent_id=2、component=
  `view.manage_policy-archive`（★字面決定 view 目錄必為 `views/manage/policy-archive/`、
  寫錯即死選單）、icon=`mdi:recycle`（DB 唯一真源、不寫 static meta）、buttons=NULL
  （零按鈕碼＝restore 不 gating 自洽）；menu 維政策列 72（R_SUPER、protected=TRUE）＝頁級門。
  路由外掛產物四檔走產物檔紀律（禁手改＋重算冪等；route-artifact-gate 三道斷言必跑）；
  自由文字欄走純文字插值（view-render-guard 自動涵蓋；archive_reason 為 reason gate 受限
  列舉、非 client 可控原文）。
- **B-099 納入（必辦；隨前端單元順修）**：ip-rule/index.vue 之 default slot 在 hasAuth=false 時
  冒出共用元件自帶寫端鈕——本刀交付 updateRoleButton 後該態**從不可達變可達**（本刀自己造成）。
  修法零設計成本：照抄 menu/index.vue:355-375 已驗證形（外層 div 保底＋v-show＋內層 v-if、
  約 +3 行）；該檔為 rev5 新增型新檔＝零標記成本。★順修 B-099 條文的失準觸發理由
  （「dev 三帳號權限碼齊全」不成立——R_ADMIN 僅 3 碼；真原因＝manage_ip-rule 之 menu 維政策
  僅 R_SUPER 的頁級門）。驗收＝CDP 撤一個按鈕碼→看 ip-rule 頁不冒鈕。
- **i18n（★三條授權鏈分開寫——zh-tw.ts 自成一鏈）**：`backend:` 樹 Lint24 要求**四處**同
  commit，但**授權依據各異**：①`zh-cn.ts`／`en-us.ts` 兩語 backend 樹＋②`app.d.ts` Schema 型節
  走 I18N-WIRING 既有授權（(ii)／(iii)）；③**`zh-tw.ts` 是 rev5 純新增檔、不觸任何 ★軌道**
  ——最原始源基線（upstream example）之 `src/locales/langs/` 只有 en-us／zh-cn 兩檔，該檔全檔
  以檔頭一行 `[rev5-inline BACKEND-MSG-DICT+ …]` 圈界（新增型紀律、ADR 0021）、**零基線既有行
  ⇒ 結構上不會有 `原行:`**；憲法 I18N-WIRING (iii) 紀律欄另明文「`zh-tw.ts` 標型重構不在授權內」
  （本刀只加 backend 鍵、不動標型與 runtime 接線）。`page:`／`route:` 樹走 §III.2 用途授權、
  **三處**（zh-cn／en-us／app.d.ts——★zh-tw.ts 非 runtime locale、只有 backend 樹，勿塞 page 鍵）。
  增量：
  - backend 樹 50→53 鍵：`biz.role.protectedRevoke`（整批拒；rev4 譯文「存在受保護的授權，
    無法撤銷」可單獨站住）＋`biz.policy.notRestorable`（新開 biz.policy 子樹）＋結構性封死
    拒因鍵（rev5 新造、rev4 無對應；命名掛 biz.policy.* 或 biz.role.* 於 contracts/msg-keys.md
    定案）；角色不存在復用既有 `biz.role.notFound` 零新增。構造點照 003 先例一律字面
    `Cow::Borrowed("biz.policy.xxx")`（I18N_CONST_ROSTER 現為空表、常數形會觸發回填門）。
  - `page.manage.policyArchive` 整節 15 鍵（rev4 逐鍵複核＝10 平鍵＋form 2＋dimensionLabel 3；
    restore 三鍵收斂與否＝§10-14）；`page.manage.role.endpointAuth` 1 鍵（三處）；
    `route.manage_policy-archive` 1 鍵；`page.manage.menu.home` 既有零新增。
  - ★機器守強度不對稱：zh-tw＝Lint24 直掃 ERROR；en-us＝msg-dict 兩語鍵集間接守；
    **zh-cn＝零 lint 覆蓋**（僅 vue-tsc typecheck 兜底、不在 pre-commit）——i18n 單元驗收
    顯式跑 typecheck。前後端鍵必同 commit（孤兒鍵雙向 ERROR）。本刀動 zh-cn.ts **不因此**
    擴大 lint 掃描面（維持「前端側僅 zh-tw」紀律）。
- **檔集總表**（詳細性質標註）：修改型 inline 3 檔（兩 modal＋role-operate-drawer 增量）；
  新增型新檔 3 檔（endpoint-auth-modal＋policy-archive 兩支）；修改型檔內新增型圈界 **3 檔**
  （zh-cn.ts／en-us.ts／app.d.ts；塊界若動到基線既有行——如前一鍵補逗號——該行帶 `原行:`）
  ＋★純新增檔增量 1（zh-tw.ts〔僅 backend 3 鍵〕——rev5 自有檔、零基線行、無 `原行:` 面）；產物檔 4（router/elegant 三檔＋elegant-router.d.ts）；rev5 自有
  新增型檔追加 2（rev5-role-admin.ts 6→約 18 支 fetcher＋rev5-role-admin.d.ts——主線自拍：
  全數追加同檔不拆、理由＝三維與回收桶皆以 roleId 為軸、拆檔徒增兩份檔頭紀律）；機器重抽產物 1
  （rust-api 側 wire-schema.json、57 definitions 預估→65~67；★跨子庫：型住 base-web、快照住
  rust-api——兩段式 commit 順序寫進 task 註記）；連帶修 1（ip-rule/index.vue＝B-099）；條件性 1
  （menu/index.vue＝B-100、僅 CDP 實測干擾驗收時順修）。預期零 diff：components.d.ts
  （所需 Naive 元件與 icon 全已註冊；ADR 0052 產物紀律前端面大機率不觸發、但條款入憲仍必辦）、
  service/api/index.ts（barrel 沿先例不動、fetcher 直接路徑 import）；menu 頁之 fetchGetAllPages
  續走 barrel 不切換（其 inline 標記自陳非本刀射程；交付端點即修復 4040）。

## §6 治理面

**憲法 Amendment v1.7.0→v1.8.0 逐處清單（8 處；估 +13 行、落地約 290/350、零預算壓力）**：

1. **§I.7 新增島 G 條文**（落點＝島 F 塊後、島 H header 前，維持字母序）。五條承載狀態逐條：
   G1 兩半已由 ADR 0050 §3 首條（DB-first＋同交易＋判定面全量重載導出）與 ADR 0049 §2
   （失敗契約：rebuild 成功才 swap、keep-last-good、有界重試、耗盡維持舊面）逐字承載→本刀
   合成＋訂正觸發面；**G2 零承載**＝本刀全新兌現；G3 之 deleteRole 半已兌現（ADR 0050 §3-G3）、
   **grant/revoke 半零承載**＝本刀兌現；G4 全承載＝純轉正零新行為；G5 現役寫入半已承載
   （rev5 加強＝固定鎖序句寫進條文、rev4 無）、**復原同實例判定＋跨刀鉤子句零承載**＝本刀兌現
   （鉤子句改指刀 B 之 sys_user_role 指派寫端）。★落字差異五處（照抄 rev4 即出錯）：
   ①觸發面勿抄「Applied 含空 diff 才觸發」（B-104 錯字面之鏡像；建議只凍結「拒絕／無作用／
   標的不存在 MUST NOT 觸發同步」方向面、矩陣本體留 ADR／活書級＝§10-3）②G2 明細載體改寫
   「拒絕 MUST 使原因可辨識、一因一鍵；明細載體屬活書級、不入條文」③rev4 條文內嵌之
   rev4:L-075 類比句刪除（rev5 語境無指涉對象；★.specify/ 在 Lint25 SKIP_DIRS＝零機器守、
   純人審）④G5 寫入固定鎖序「advisory → 歸檔表列 → sys_role 列 → sys_menu 列 → casbin_rule」
   ⑤G3 不寫欄可空性（schema 屬活書級）、G5 保留「NULL→不可復原、誠實退化」。
   停用雙護欄照 rev4 明文**不入**條文（ADR 0050 已同形過境；欲升格＝另行 Amendment）。
   deleteRole 免 reload 論證**不轉正**（§10-5）。
2. **§I.7 島 H header 括號回填**（G 位既填、「保留」「入憲前」兩句失效）——PATCH 級隨批；
   不改則憲法自陳「G 位保留」而 G 已在表上。
3. **§I.7 島 H H1 終態成員括號回填**（「該等端點不存在期間 vacuous 成立」句）——§10-15。
4. **§III 正文加第五 bullet＝ADR 0052 生成檔條款**（判準＝檔頭 Generated 標記；路由外掛四檔＋
   unplugin components.d.ts 同族；禁手改、不逐行標記、不入用途檔級名單；機器承載＝
   fork-delta-lint is_generated()）。★硬約束：**必須是 §III 正文散文 bullet、絕不可寫成 §III.2
   表格列**——load_roster 逐列解讀行首 `|` 資料列、寫成表列會污染★軌道名冊並可能 die。
   PATCH 級隨批、不單獨 bump（ADR 0052 決定 3 自陳）。
5. **§III.2 加用途列**（§10-13 拍板；建議兩列：(iii) role 頁三顆授權 modal 接真〔含 roleHome UI
   進場、閉合 005 的零消費者窗；★role-operate-drawer.vue 已在用途 (ii) 名單內、本刀同檔雙用途
   ——Amendment 文字明寫〕＋(iv) policy-archive 頁進場〔形照 (i)〕）。表列數 10→12。
   ★機器面三約束：(a) 新增列**首欄不得留空**（load_roster 對省略重複欄值的續列即 die）
   (b) **路由外掛產物四檔路徑 MUST 留在 (i) 列範圍欄**——route-artifact-gate 以
   （軌道名×用途 (i)）定位、搬列即 G_c 空集當場紅；(iv) 列改在紀律欄寫「產物四檔授權沿 (i) 列、
   不重複列名」(c) endpoint-auth-modal 與 policy-archive 兩~三支 view 皆新增型新檔、依
   ADR 0021 款 1 不入名冊。★誠實揭露：fork-delta-lint 三元組判定不讀紀律欄語意——技術上沿用
   (ii) 標記改兩顆 modal 機器全綠、但違 v1.7.0「（ii）明文排除兩 modal、出現任何 diff＝紅」
   之人審紀律，實作期不得偷懶。「定數恰 8 檔」句射程只綁 (ii)、新用途不受其限。
6. **§III.2 表外宣告第 2 條改寫**——「rev5 無 modal 治理需求」自本刀起為假述，不改即留一句
   與 as-built 矛盾的憲法正文。
7. **§IV 九題不動**（Q9「觸及 §I.7 已入憲行為島」自動涵蓋島 G；先例＝島 H 入憲亦未增題）；
   **§II 不動**（封死落島條文；若 user 反拍才落 §II 加列）。
8. **Amendment log 一行＋版本行 1.8.0**。log 落字守 ADR 0047 引量三形：凍結量引前先數
   （「島 G N 條」「§III.2 表列數 10→12」）、活量指節不指數（勿寫 backend 鍵數，指向
   reference/backend-msg-dict）；載明分級自證——兩款 MINOR（行為島填充＋軌道授權邊界擴展）、
   ADR 0052 條款與 B-104 訂正 PATCH 級隨批；非 MAJOR 自證（§V.3 四款皆不中：未改 §I 鐵紀律、
   未反轉已入憲 invariant、未撤回 §II 拍板、未撤銷軌道授權）＋user 親決日期＋rev4 藍本出處
   （一律帶 rev4: 前綴）。

**ADR 配置（編號自 0053 起；★ADR 0050 交棒形已寫死＝不 supersede、以 provenance 引用
〔ADR 0050:93-94 逐字〕；Lint08：supersedes 空、accepted 後 body 不可變）**：

- **0053｜憲法 Amendment v1.8.0**（四款一檔、形照 ADR 0048：島 G 條文＋§III.2 用途列＋
  ADR 0052 條款順捎＋**B-104 訂正**〔建議併入＝§10-18：它是 G1 落字的直接前置，訂正句逐字
  「ADR 0049 §2 該括號句出生即誤，as-built 權威＝spec 005 FR-039＋enforce.rs doc 表」〕）。
- **0054｜結構性封死**（B-024①歸宿＋謂詞式標的集＋掛點＋非 vacuous 自證＋翻案觸發條款＋
  rev3 原形三缺陷參照＋★B-024③重評結論「維持純 key（ADR 0022 決定 2 不翻案）」明文——
  無此句 B-024③ 無結論可關）。
- **0055｜restorePolicy 復原重驗腿定形＋ADR 0050 §4 翻案觸發條款復核結論**（舊草稿無此支；
  復核結論不論走哪案皆拍板級、可能觸 migration ⇒ 獨立承載；同檔定固定序 N 腿、範式照
  ADR 0051）。
- 0056（條件性）｜僅當 user 反拍「封死落 §II 不入島條文」時立釋義 ADR；走 G6 案則不需。

**帳務（feature_close 十欄；backlog_done 須同步自 BACKLOG 刪列＝Lint04）**：

- 必關：B-104。起手維護批關：B-094＋B-101。隨前端修妥關：B-099（含條文失準理由順修）。
  隨維護批關：B-102（修法取低成本案＝facade 層收斂點補單元測，不動 contract 節零副作用紀律）。
- §10 已拍（決議見各題 ➡️ 與 §11）：B-024（§10-17＝改記殘餘不整關）、B-098（§10-21＝新增必配＋維護批補 12 支）、B-088（§10-20＝順捎＋豁免兩列）、
  B-083（§10-16）。B-085＝主線自拍納入 U0（IpRuleCleanup 為守衛家族 10 支中唯一非刻意
  自證缺口〔另一支 OperationLogCleanup 屬刻意〕；維護批本就開 model/mod.rs、照抄
  role_cleanup 自證形邊際成本近零；不納則本刀 MUST 不動 sys_ip_rule 測試面）。
- 部分／不進 backlog_done：B-008（出列 policy-archive；收刀時條文更新「餘 7 支」→「餘 5 支
  ＝audit 5」、死項 3→2）；B-105（主線自拍傾向隨 U4 補 seam 形 harness——理由＝本刀把 reload
  呼叫者 3→7+ 支、暴露面放大且 BACKLOG 明訂本刀為處置窗；補成即關、成本失控則留帳附記）。
- 敘述更新各一行（收刀時做；防 L-030 射程搬動敘述不跟）：**B-025**（★不得記為「消掉 button
  孤兒客戶」——該條 2026-08-22 已改寫、殘餘僅①sys_user 軟刪〔刀 B〕②事後對賬；本刀 orphan
  skip＝堵孤兒列**產生面**、既非①也非②，補記「產生面已封、②殘餘只剩缺陷／手改 DB 漂移」）；
  B-093（reload 觸發面擴大、窗縮短不閉合）；B-016（sys_casbin_archive 自本刀成為持續成長
  可見表、retention 逐表門檻屆時涵蓋）；B-018（demo fetcher 失去消費者之新事實）；B-091
  （rider：每單元收尾③順盤 1~2 條 promoted_to 佔位——餘 9 條中 L-022/L-037/L-042/L-043
  四條正是本刀 §8 引用對象、零額外成本）。

**簿記地雷（進 tasks）**：①單元收尾③落帳必早於⑤generate（L-018）②收刀時
`docs-sync.py errata 六座`——14 處命中、唯一現在式＝活書 §6「六座行為島」→改「八座」、
過去式 13 處維持原字；★只改一個詞 §6 也進 Lint06 changed set ⇒ **arch_impact 必列 §6**
（雙向相等、列了沒改也 ERROR）③casbin_rule 與 sys_casbin_policy_archive 皆**不在**
RUNTIME_APPEND_TABLES ⇒ gate2 逐列全等：測試殘列清乾淨＋`casbin_rule_id_seq` setval(163,true)
＋archive seq setval(1,false) 還原（CasbinCleanup 已覆蓋 nextval 路徑、有自證測）；
★CDP 走查會留列與序列推進 ⇒ **走查排 schema-gate 驗收之後**（或走查後手動還原）④wire-schema
跨子庫兩段式 commit 順序寫進 task 註記⑤Lint25 受掃面＝specs/006-*/ 全套 ERROR 級、
**逐 token 前綴**（「rev4:ADR 0080／0084」第二個號不合規；brainstorm／.specify 在 SKIP_DIRS
＝零機器守純人審、本檔自律）⑥Lint11：活書勿寫端點計數字面（指向 reference/routes）
⑦活書 §8 只餘 13 行（77/90）——本刀要加兩用途 as-built＋授權慣例條目、落筆先算行（§10-16
連動）⑧新頁 view 檔必落 `views/manage/policy-archive/`（component 字面推導、寫錯即死選單）。

## §7 執行單元草案（14 支；tasks 期定稿）

- **U0 起手維護批**（NOTES 指派；排在一切端點單元之前）：B-094 收攏——★允許檔清單**顯式**列
  handler/menu.rs（機器查證：rev4 三維＋支撐讀＋roleHome 全住 role.rs、回收桶住獨立
  policy_archive.rs ⇒ 本刀授權面不會自然打開 menu.rs；★失準句出處＝BACKLOG B-094 改期段
  「該刀必動 handler/menu.rs 授權面」——以此為準、收刀關帳時順修該半句；NOTES 僅記
  「起手維護批＝B-094＋B-101 收攏」、無此失準句）；
  緊迫理由＝本刀新檔 policy_archive.rs 會生出 audit_operator **第五份**拷貝（現況機器數：
  audit_operator 4 份、json_or_default 3、resolve_operator_names 3、violated_constraint 3、
  MAX_CURRENT 3、tristate 3、blank_to_none 2）。B-101——★動工前先分類：AppState 字面建構點
  生產 1＋測試側 **10 處**（BACKLOG「第四份」低估）；可收攏（menu.rs:1827／contract.rs:1608／
  tests/common/mod.rs:78／enforce.rs:495 之一部）vs 須保留自訂形（stub_state_with_rules／
  stub_state(tm)／real_app_with_rules／state_with 四處）；real_app_with 長 (Router, AppState)
  變體。＋B-102（facade 層收斂點單元測）＋B-085（IpRuleCleanup 自證測、自拍納入）＋B-098
  既有命名空間補齊（範圍＝§10-21）。
- **U1 憲法 Amendment（v1.8.0）＋ADR 0053~0055**（主線親做；§6 逐處清單＋B-083 落節拍板
  〔§10-16〕＋§8 行數預算先算）。
- **U2 menu 維**（getRoleMenu／updateRoleMenu）：facade/sys_casbin_policy.rs TDD→handler＋
  入域＋NOT-granted 等待測＋grant 面 reload 接線＋RELOAD_CALL_FILES 擴列。
- **U3 button 維**（getRoleButton／updateRoleButton＋orphan skip）：入域＋NOT-granted 測。
- **U4 endpoint 維＋結構性封死**（getRoleEndpoints／updateRoleEndpoints、不入域）：鎖內守門＋
  守門變異自證（L-019）＋B-105 seam 形 harness（自拍隨此單元）。
- **U5 支撐讀三支**（getAllPages／getAllButtons〔新建 all_button_codes〕／getAllEndpoints
  〔policy_endpoints 斷環〕）。
- **U6 回收桶讀端**（getArchivedPolicies＋批次讀端 active_ids_by_codes 自建＋restorable 旗標）。
- **U7 restorePolicy**（七步鎖序＋復原重驗 N 腿照 ADR 0055 定形＋封死涵蓋＋維度分岔
  〔begin 前決定〕＋選單／按鈕分支入域＋NOT-granted 測）。
- **U8 i18n 四處＋Lint24＋vue-tsc typecheck**（zh-cn 零 lint 覆蓋、顯式驗）。
- **U9 前端三 modal**＋roleHome 接真（§10-10 已拍納入）＋B-099 順修。
- **U10 policy-archive 頁**＋產物四檔重算冪等＋B-088 對賬閘＋具名豁免兩列（§10-20 已拍順捎）。
- **U11 wire-schema 重抽＋契約快照＋全量閘**（容器內；跨子庫 commit 順序）。
- **U12 CDP 三方對照**（22080 vs 42080 vs 42089；dev 帳號 Super／Admin／User＋123456；
  ★判準修正：menu-auth 樹已是真樹——改用勾選 1..21 連號／notFound toast 消失；button-auth
  假資料 button1..10；rev4 抽屜三顆授權鈕 vs rev5 現況兩顆＝天然錨點；★走查排 schema-gate
  之後；L-050：真登入 smoke 後緊接全量＝throttle 家族暫態紅）。
- **U13 收刀簿記**（errata 六座＋arch_impact 含 §6＋帳務清單＋feature_close notes 寫承接關係）。

編排慣例：implementer=fable 1m xhigh、review=opus 1m xhigh、防呆六件套（CLAUDE.md §2）。
高風險共享檔序列鏈：facade/sys_casbin_policy.rs（新）、facade/sys_casbin_archive.rs（本刀增
讀端與 restore）、facade/sys_menu.rs（all_button_codes）、handler/role.rs（8→17 支）、
handler/policy_archive.rs（新檔）、router.rs、tests/contract.rs、tests/authz_entrypoint_lint.rs
（RELOAD_CALL_FILES 擴列）。

## §8 風險與誠實界線

1. ★**ADR 0050 §4 翻案觸發條款已被本刀命中**＝零 migration 前提的唯一已知威脅（§10-6）：
   走「不可復原集擴列」案即保零 migration；走「加 menu_id 欄」案＝ALTER TABLE＋schema-gate
   演進帳三閘＋收刀事件與 SC 全改。
2. **B-105**：RELOAD_SERIAL 交錯時序無行為 harness（拿掉 mutex 全測仍綠、退化守僅死鎖逾時紅）；
   本刀 reload 呼叫者 3→7+ 支、暴露面放大——自拍隨 U4 補 seam 形 harness、成本失控則降級留帳。
3. **restorePolicy 維度分岔 vs 域鎖 txn 首動作**的結構點（begin 前讀 v2 決定入域、或照 rev4
   一律入域＋ADR 記放寬）——spec 期必須釘死。★rev4 已答此題（無條件取鎖）且理由／代價逐字
   在碼註（rev4:facade/sys_casbin_archive.rs:338-341）；真正的張力＝rev5 憲法 H1 與 facade
   模組 doc（sys_casbin_archive.rs:14-17）把終態成員寫成僅選單／按鈕分支——舊草稿沿 rev4 形、
   非未意識到（§4-③）。
4. protected UI 預標契約細節（§10-12）與三維讀端 wire——spec 期定。
5. wire-schema 被動存放命名空間現已三個 19 支零裁判（RoleAdmin 6／MenuAdmin 6／IpRule 7；
   B-098 條文只點名前兩者）——本刀若不按 §10-21 補齊、缺口擴至第四個命名空間
   （Api.PolicyArchive.*），且 protected 欄若上 wire 正是「序列化形漂移不紅」高風險欄。
6. 本刀新造已知態（§2-(d)）：授予指向不存在 view 的自建選單⇒側欄可見點擊零反應——
   明寫 spec Edge Cases，防煙測誤判回歸。
7. endpoint 維下線列的復原重驗——rev4 **不驗**（restore 全邏輯住 facade、handler 為薄殼
   〔rev4:handler/policy_archive.rs:9-11 doc＋:183〕；鎖內重驗至第⑥步止且逐字「非 menu 維
   跳過」〔rev4:facade/sys_casbin_archive.rs:379-389〕）——rev5 要不要補這一腿＝§10-7 腿集
   拍板、spec 期釘死。
8. B-059（throttle 間歇假紅）已降級已知態——再現時照條文傾印自證屬外部干擾、不當本刀回歸；
   驗收序照 L-050。
9. **LESSONS 指針（風險面對應）**：守門非 vacuous＝L-010／L-019／L-020／L-028；負向斷言與
   併發清理＝L-036／L-031／L-050／L-017；兩處字面同源＝L-033（protected 前端靜態集若採即中
   此形——§10-12 的反對理由）；文件計數與預告＝L-048／L-043／L-037／L-039；編排面＝L-011／
   L-035／L-027／L-049／L-051／L-042／L-022。
10. 本檔性質自律：brainstorm 在 Lint25 SKIP_DIRS（零機器守）——rev4 編號前綴、行號快照
    （寫作當下實測值）純人審；下游 specs/006-*/ 全套為 ERROR 級受掃面。

## §9 rev4 參照清單（plan research 前置素材，ADR 0019；行號＝2026-08-22 實測）

- **spec**：rev4:specs/009-role-admin 之 FR-017~026（三維治理狀態機、US2 段 :191 起）／
  FR-027~032（回收桶 :204 起）／FR-033~036（拒因與明細 :213 起）；FR-037~039（roleHome）
  已隨 005 交付、不列。
- **facade/sys_casbin_policy.rs（912 行）**：Dimension:48／★BlockedTarget:75（不帶回）／
  PolicyOutcome:85／set_role_dimension:107／set_role_endpoints:129／current_targets:269／
  current_endpoints:282／menu_ids_to_route_names:298／route_names_to_menu_ids:311。
- **facade/sys_casbin_archive.rs（1336 行；與上檔合 2248 行）**：ArchiveSnapshot:57／
  insert_archived:78（★rev5 已改內收形）／archive_all_role_policies:111／
  archive_all_menu_policies:205＋archive_button_code_policies:217（★rev5 改私有泛用 helper、
  兩支具名形不帶回）／RestoreOutcome:239／ArchivedRecord:248／dimension_of:255／list:271／
  **restore:330（七步鎖序本體）**。★rev4 另有 facade/domain_lock.rs——rev5 已併入
  sys_casbin_archive.rs、檔級對照勿誤判缺件。
- **handler/role.rs（2034 行）**：共用 query 型:105／UpdateRoleMenuReq:116／
  UpdateRoleButtonReq:124／UpdateRoleEndpointsReq:132／Endpoint wire 型:179-181／
  begin_and_lock_role:434／finish_governed:461／get_role_menu:508／update_role_menu:524／
  get_role_button:554／update_role_button:567／get_role_endpoints:596／update_role_endpoints:611
  ／get_all_pages:656／get_all_buttons:668／**policy_endpoints:680（E0391 解說 :675-687）**／
  get_all_endpoints:691／role_code_of:634。
- **handler/policy_archive.rs（709 行、獨立檔）**：ArchivedPolicyQuery:43／RestorePolicyReq:53／
  ArchivedPolicy:68／serialize_opt_i64_number_guarded:95／to_wire:108／audit_meta:131／
  get_archived_policies:158／restore_policy:183。
- **auth/enforce.rs（954 行）**：MODEL_CONF:31／init_enforcer:49／有界重試常數:57／
  硬禁令段:69-73／rebuild_enforcer:76／reload skip 條件:93／reload_enforcer:94／
  enforce_role_path_method:229／require_policy:256。
- **handler/menu.rs**：reload 三呼叫點 :329／:348／:364（G1 表原始出處）。
- **router.rs**：三維六條 :329/:337/:345/:353/:361/:369；支撐讀 :385/:393/:401；
  回收桶 :431/:439（:428 註「〔70,71〕、零新 seed」）。
- **前端**：views/manage/role/modules/ 之 menu-auth-modal.vue（153 行、6 條原行）／
  button-auth-modal.vue（127 行、21 條原行）／endpoint-auth-modal.vue（134 行、新檔）／
  ★protected-revoke-detail.ts（36 行、不帶回）；views/manage/policy-archive/index.vue（153 行）
  ＋modules/policy-archive-search.vue（92 行）；locale 之 page.manage.policyArchive 15 鍵。
- **ADR**：rev4:ADR 0048（島 G 全文）／rev4:ADR 0049（role_id＋翻案條款）／rev4:ADR 0050
  （明細通道＋受眾邊界重評條款）／rev4:ADR 0051（選單域狀態機總綱——拍板 #1 引用之本尊）／
  rev4:ADR 0063（按鈕碼三護欄＋「無機器強制」自承）。
- **rev3**（翻案刀參考、本刀不採）：handler/system_manage.rs 之 grantExceedsOwn 三段＋
  commit 3bfab71。
- **rev5 差異點（不得帶回；舊草稿三條＋本次偵查新增）**：BizData 攜參形（→純 key）／
  rev4 protectedRevoke 明細陣列與 BlockedTarget 型與 protected-revoke-detail.ts（→純 key）／
  「B12 不重載」宣告（→ADR 0049 已翻案）／★deleteMenu／batchDeleteMenu 之無條件 reload
  （→rev5 三支一律 `if archived` 為門）／★insert_archived 之 caller 傳 role_id
  （→內收 v0 反查；連帶「歸檔掃描 MUST 早於軟刪 UPDATE」次序鐵律、rev4 藍本恰反序）／
  ★刪除集重跑過濾（→以剛歸檔那批 id 圈定）／rev4 roleHome wire 形（roleId query 鍵／裸
  string 回應／NULL 摺疊空字串→rev5 已判 id／{home}／誠實 null）／rev4 role 頁 hasAuth
  gating（→rev5 已推翻、不 gating）／rev4 archive_all_menu_policies 兩具名 fn 形
  （→私有泛用 helper）。

## §10 待 user 拍板開放題（每題：背景→選項〔含代價〕→建議）

### 甲、憲法與條文面

1. **結構性封死條文位置**。背景：G2 管撤銷側（revoke 觸 protected 整批拒）、封死管授予側
   （不得 grant 給非 R_SUPER），方向相反、觸發端點集不同、血統不同（G2＝rev4 過境、封死＝
   rev5 新拍板）。選項：**A（建議）獨立 G6**——併寫會讓「反轉＝MAJOR」射程無法判；先例＝
   島 F 之 F6~F8 新編號附掛；代價＝島 G 六條、log 寫「五條沿 rev4＋G6 本刀新拍板」。
   B 併入 G2 尾段——省一條編號、犧牲上述三點區辨。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 獨立 G6（照島 F 之 F6~F8 新編號附掛；修訂日誌寫「五條沿 rev4＋G6 本刀新拍板」）
2. **封死標的集落字**。背景：機器謂詞（ptype=p ∧ protected ∧ v2∈HTTP 動詞）在真 seed 圈出
   15 列、「治理面 12 支」是敘事標籤、「19 列」是含 menu 維總數——三個量並存、硬列數字＝
   製造下一個 B-104。選項：**A（建議）條文只寫謂詞、不寫列數**（ADR 0047 活量指節不指數；
   68 上線或未來刀新標 protected 自動納管）、敘事段註「2026-08-22 時為 15 支、其中 12 支屬
   治理面」。B 謂詞＋硬列 15 支——每次增列改憲。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 條文只寫謂詞、不寫列數（ADR 0047 活量指節不指數；敘事量「2026-08-22 時端點維 15 列」落修訂日誌／活書）
3. **G1 觸發面要不要把觸發矩陣寫進條文**。背景：照抄 rev4「Applied 含空 diff 才觸發」＝把
   B-104 剛訂正的錯誤形之鏡像寫進憲法；rev5 as-built 移除面更窄（if archived 為門）。選項：
   **A（建議）條文只凍結「拒絕／無作用／標的不存在 MUST NOT 觸發同步」方向面**、矩陣本體留
   ADR／活書級（同島 H「常數留活書」範式）。B 矩陣入條文——本刀 §10-4 拍完就固化、日後調整
   觸發面＝修憲。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 條文只凍結方向面（成功 commit 後 MUST 同步／被拒與無作用與標的不存在 MUST NOT 觸發／keep-last-good／反轉＝MAJOR）、矩陣本體留 ADR 0053＋enforce.rs doc
4. **grant 面空 diff 是否觸發 reload**。背景：rev4 空 diff 仍 Applied 仍 reload（「刻意不優化」
   有測釘）；005 as-built 移除面立了相反哲學「零變更零觸發」；沉默照抄任一邊＝enforce.rs
   觸發矩陣 doc 同時容納互斥兩句。選項：**A（建議）照 rev4 空 diff 仍 reload**——reload 冪等
   全量重建、成本可忽略；判斷「有無實際變更」在全量替換 diff 形下要多算一次集合比較＝多一個
   可錯面；MUST 在島 G1 條文與 enforce.rs doc 明文寫成刻意例外。B 對齊 005「零變更零觸發」
   ——哲學統一、但 grant 面要新增變更偵測邏輯與其測試。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 照 rev4：grant 面 Applied 即觸發、不問 diff——★島 G1 條文與 enforce.rs doc MUST 明文寫成「grant 面刻意例外」、與移除面 if archived 並陳
5. **ADR 0050 §2「deleteRole 免 reload」論證要不要轉正入島 G**。背景：轉正會把刀 B 閉合
   B-093 的候選②（deleteRole 改觸發同步）從「一次 spec 拍板」升級為「修憲」。選項：
   **A（建議）不轉正、留 ADR 級**。B 轉正——條文更完整、代價＝刀 B 手腳被綁。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 不轉正、留 ADR 0050 級（刀 B 依 B-093 三候選一次 spec 拍板即可閉合）
6. **ADR 0050 §4 翻案觸發條款復核：menu 維同實例欄**。背景：本刀 updateRoleMenu 的 revoke 面
   產生**可復原** reason 的 menu 維歸檔列，「menu 維歸檔列結構性無復原路徑」前提自本刀起
   不成立；同 route_name 重建後復原＝新實例繼承舊授權＝違已入憲島 H2（「回收桶復原」逐字
   在列）。選項：A 加 menu_id 同實例欄——判定最精確、代價＝ALTER TABLE 破零 migration。
   **B（建議）把手動撤銷的 menu／button 維歸檔列也列入不可復原集**（menu 維授權只能重勾
   不能復原）——零 migration、與島 H5「復原不回灌」精神一致；代價＝回收桶對 menu/button 維
   只剩稽核閱覽價值。C 以現存同 route_name 活選單判同實例——route_name 可重建⇒判不出實例、
   等於沒判、繞回 H2 破口（不建議）。復核結論由 ADR 0055 承載。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：B 手動撤銷之 menu／button 維歸檔列列入不可復原集（reason gate 三值→五值：＋menu_manual_revoke／button_manual_revoke 類 reason、字面 spec 期定）——零 migration、H2 零破口；回收桶對 menu/button 維只剩稽核閱覽；復核結論由 ADR 0055 承載
7. **restorePolicy 復原重驗腿定形**。背景：舊草稿只有兩腿（reason gate＋role 側同實例），
   ADR 0051 取態「復原＝重入治理域須全套重驗」下至少四腿未答（§4-④：menu 維同實例／button
   維孤兒／endpoint 維下線／停用角色語意）。選項：**A（建議）固定序 N 腿表格定稿**（照
   ADR 0051 落字範式、每腿註對應現役寫端守門；腿集依 §10-6 結論收斂）。B 維持 §4-④ 現定
   四腿、未答腿只記已知態——工少、但把 rev4 沒答的洞原樣帶進 rev5。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 固定序五腿定稿：①reason gate（五值集）→②role 同實例（歸檔 role_id＝現役同 code 活角色 id、NULL 不可復原）→③封死（protected 端點政策不得復原給非 R_SUPER）→④端點在冊（不在 ROUTES 名冊→拒、免幽靈政策）→⑤角色停用不擋（停用≠撤銷、島 H4 精神）；每腿註對應寫端守門、照 ADR 0051 落字範式、ADR 0055 承載。★連動：可復原列自此只剩 endpoint 維手動撤銷
8. **v2='menu' 四列 protected 政策要不要納入封死**。背景：四列（manage_role／manage_menu／
   manage_system-settings／manage_policy-archive）不在端點維謂詞射程——超管可經 updateRoleMenu
   把系統管理目錄可見性授予 R_ADMIN；端點層仍 5003、非提權破口。選項：**A（建議）不擴、
   列已知態**（可見性非授權；擴了 UI 出現「勾不動的樹節點」）。B 擴及 menu 維 protected 列
   ——封死語意更完整、代價＝menu-auth 樹要做 protected 節點鎖定 UI。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 不擴、列已知態（spec 明記「可見性可授、端點仍封；效果＝看得到點不動」）

### 乙、契約與 UI 面

9. **getAllPages 域選擇**。背景：兩個消費面需求相反——roleHome 首頁候選宜顯示域（停用頁
   不該被指為首頁）、menu 頁 routeName 下拉宜治理域（否則挑不到與停用選單同名的 routeName、
   被活性唯一守門拒時語意不直觀）；rev5 spec 005 FR-019 又立了「治理候選 MUST NOT 誤用顯示域」。
   選項：**A（建議）照 rev4 走顯示域**（list_active）＋spec 明文記載 menu 頁消費面的已知
   不對稱（拒因由 routeNameExists 誠實承擔）——避免同一端點兩種語意。B 治理域——與 FR-019
   一致、代價＝停用頁可被指為 roleHome。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 顯示域（list_active、照 rev4）＋spec 明記 menu 頁消費面不對稱（停用選單的 routeName 不在下拉、拒因由 routeNameExists 誠實承擔）
10. **roleHome UI 是否隨本刀接上**。背景：rev4 的 roleHome UI 家＝menu-auth-modal（本刀必動
    的檔）；005 spec 已明文交棒；不接則 005 兩支端點的零消費者窗續留（刀 B 射程無自然落點）、
    CDP 三方對照該區塊永遠對不齊。選項：**A（建議）納入**——邊際成本＝+2 fetcher＋2 型＋
    同檔 4 處接線（契約差異三處見 §5、rev4 碼不可照抄）。B 不納入——省工、窗續留。
    ★附註：「不做 roleHome 則 getAllPages 一併移出射程」的選項**不成立**——menu 管理頁
    已是 getAllPages 的既有消費者（現況恆 4040、§2）、端點無論如何要交付。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 納入本刀（+2 fetcher＋2 型＋menu-auth-modal 同檔 4 處接線；契約與 rev4 三處相異不可照抄：query 鍵 id／回應 {home} 誠實 null／三形同義清空；候選源＝getAllPages）
11. **三維＋回收桶契約的角色鍵：`roleId`（rev4 全用）vs `id`（rev5 roleHome 已判形）**。
    背景：rev5 已在 roleHome 契約逐字凍結「rev4 之 query 鍵 roleId 形不帶回」；混用＝同一
    handler 檔兩套鍵名慣例。選項：**A（建議）全部用 `id`**——與 rev5 既判形一致、一次釘死於
    contracts。B 全部用 `roleId` 照 rev4——前端照抄省事、但與 roleHome 既有契約打架。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 八支全部用 id（與 roleHome 既判形一致、一次釘死於 contracts）
12. **protected 列 UI 預標載體**。背景：三維 modal 要預標 protected 列（拍板 #7 的 UI 緩解）。
    選項：**A（建議）三支讀端回應多帶 protected 旗標**——資料取得面現成（entity 11 欄）、
    代價＝wire 變更＋wire-schema 重抽（本刀本就要抽）。B 前端以 seed 靜態集判——零 wire
    變更、代價＝兩處字面同源（L-033 形）、seed 變動時靜默失準。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 三支讀端回應多帶 protected 旗標（後端單一真源；wire-schema 本刀本就重抽）
13. **§III.2 授權形式**。背景：兩顆 modal 被 v1.7.0 明文排除於用途 (ii)（「本刀出現任何 diff
    ＝紅」）、policy-archive 是新頁——四條「補完」判準全不中、必走 Amendment。選項：
    **A（建議）MANAGE-PAGE-WIRING 加兩列**——(iii) 三 modal 接真（含 roleHome UI；
    role-operate-drawer 同檔雙用途明寫）＋(iv) policy-archive 頁（形照 (i)）；混列會讓紀律欄
    同時描述兩種驗收形、失去可審性；代價＝表列 10→12。B 只加一列混寫——省一列、犧牲可審性。
    C 開 rev4 同名 BASE-WEB-MODAL-WIRING 新軌道——語意最貼、代價＝新軌道機器面全套＋
    表外宣告連動改更多。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A MANAGE-PAGE-WIRING 加兩列：(iii) 三顆授權 modal 接真〔含 roleHome UI；role-operate-drawer 同檔雙用途明寫；endpoint-auth-modal 新增型新檔另註〕＋(iv) policy-archive 頁（形照 (i)）
14. **policyArchive 之 restore／confirmRestore／restoreSuccess 三鍵收斂**（005 遺留「屆時議」）。
    背景：rev5 已有兩份同名三鍵（ipRule〔004〕＋menu〔005〕）、本節進場＝第三份。選項：
    **A（建議）不收斂、照 rev4 各頁自有鍵**——三頁確認文案本就不同（「確定恢復此規則／
    此菜單／此授權？」）、共用鍵無合法的家（common.* 屬 upstream 凍結面）、收斂只省兩個
    泛用鍵卻要動 004/005 既有檔。B 收斂共用命名空間——省鍵、文案退化成無主詞形＋動既有檔。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 不收斂、照 rev4 各頁自有鍵（page.manage.policyArchive.{restore,confirmRestore,restoreSuccess}；三頁文案本就不同）
15. **島 H H1 終態成員括號要不要就地回填**。背景：ADR 0048 承諾「屆時入域零修憲」⇒不動
    完全合法；但不動則憲法讀來像那些寫端仍不存在。選項：**A（建議）PATCH 級隨批改為
    「授權治理刀已兌現、v1.8.0 起非 vacuous」**。B 不動——零成本、留一句過時描述。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A PATCH 級隨 v1.8.0 批改為「授權治理刀已兌現、v1.8.0 起非 vacuous」、不另 bump（★連動 §10-6/7：H1 之「授權回收桶復原之選單／按鈕維分支」因可復原集收窄而結構性 vacuous——回填句須如實寫「選單維／按鈕維授權寫端已兌現；回收桶復原之選單／按鈕維分支因不可復原集擴列結構性不可達」）

### 丙、帳務與排程面

16. **B-083：島 G as-built 落活書哪一節**。背景：§6=120/120 滿載（Lint07 警告級不擋 commit、
    但「lint 全綠」判準會漂）；§5 餘 20 行、§8 餘 13 行；005（CRUD 性格）走 §5+9/§8+4 避開
    §6，004（runtime 性格）§6+66；本刀兼具兩性格（新 facade/handler 屬 §5、七步鎖序與觸發序
    與 §6 現有「IP 閘判定序」同構）。選項：**A（建議）甲案＝落 §5＋§8、§6 只做 errata 字詞
    修正（零行增減）**——零 lint 動作、沿 005 先例；代價＝島 G as-built 與島 E/F 不同節、
    體例不全齊；★§8 餘 13 行、落筆前先算行。B 調高 §6 配額常數（動 docs-sync＋自測、要論證
    §6 為何更寬）。C 拆 §6 子節（動 arc42 節號骨架＋牽連 Lint06 歷史 arch_impact 存在性斷言
    ——成本最高、明確不建議）。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 甲案＝島 G as-built 落 §5＋§8、§6 只 errata 零行增減；B-083 本體續掛帳；§8 餘 13 行落筆先算
17. **B-024 能否整條關帳**。背景：①封死＋②護欄複評隨 ADR 0054 關、③受眾重評以「維持純 key」
    為結論關；但 ADR 0022 後果末條交棒的「填 seam 後把掛點呼叫移到取讀鎖之前」本刀不填 seam
    ＝仍未辦。選項：**A（建議）改記殘餘、不整條 done**（不進 backlog_done；殘餘句改寫為只剩
    該交棒項、由翻案刀承接）。B 整條關＋殘餘句搬 ADR 0054 後果段——帳面乾淨、代價＝交棒項
    脫離 BACKLOG 追蹤面。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 改記殘餘、不整條 done（B-024 條目改寫為只剩「no-escalation seam 填入後掛點前移（翻案刀承接）」一句）
18. **B-104 承載形**。背景：BACKLOG 只說「一併以新 ADR 承載」未指定形。選項：**A（建議）併入
    ADR 0053**——它是 G1 條文落字的直接前置（不訂正就把錯字面寫進憲法）、「一決策」＝
    「G1 條文長什麼樣」。B 獨立一支 ADR——編號多一支、兩檔互引。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 併入 ADR 0053（G1 條文長什麼樣＝一決策；0053 承接 ADR 0049 §2 表、寫訂正後完整矩陣含 grant 面 Applied 即觸發）
19. **updateUserSessionPolicy（seed 68、protected、未上線）歸哪一刀**。背景：26 支存量中唯一
    無主；資料面 sys_user.session_policy 欄（per-user session 政策）、保護等級與治理面同級、
    與 system-settings 頁全站設定成對。選項：**A（建議）刀 B**——資料面屬 user 域、與 sys_user
    寫端同刀；謂詞式守門下未上線期間自動受保護、本刀零風險。B B-008 之 system-settings 頁
    （與 66/67 同頁同批）。C 本刀（protected 身分與封死同刀交付免留窗）——射程膨脹、且其
    UI 家（user 管理面）本刀不做。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 刀 B（資料面屬 user 域、UI 家在 user 管理面；謂詞式封死下未上線期間自動受保護）
20. **B-088 對賬閘（seed 之 view.* ⊆ 前端 view 集）順捎與否**。背景：NOTES 標「宜同批做」；
    但本刀交付後仍餘兩死項（seed 列 9 system-settings／77 audit）⇒閘一建就紅、必配具名豁免
    清單（豁免附 B-008 指針、兌現時自然縮小，否則 L-010 恆綠形）。選項：**A（建議）順捎＋
    具名豁免兩列**——掃源兩端現成、本刀正是產物四檔變動時刻、新頁是第一個真陽性樣本；
    代價＝多一份豁免設計。B 等 B-008 三張全兌現再建——閘出生即綠、拖到最後。C 本刀只更新
    B-088 條文（死項 3→2＋豁免設計新發現）、建閘留下一刀——最省。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 順捎＋具名豁免兩列（seed 列 9 system-settings／77 audit，豁免附 B-008 指針、兌現時自然縮小；防豁免變永久＝豁免列附 B-008 條目編號為觸發）
21. **B-098 補齊範圍**。背景：wire-schema 裁判測現僅 5 支 definitions，被動存放三個命名空間
    19 支（RoleAdmin 6／MenuAdmin 6／IpRule 7；條文只點名前兩者）；本刀新增 Api.PolicyArchive.*
    與三維型＝若沿現形即第四個。選項：**A（建議）本刀新增命名空間必配裁判＋維護批補齊
    RoleAdmin＋MenuAdmin 12 支、IpRule 7 支留帳並於條文註明**。B 三個全補、B-098 當場關帳
    ——多 7 支工作量。C 只補本刀新增、既有 19 支原樣留帳——最省、缺口不縮。
    ★誠實註記：lens 間對「觸發成立與否」讀法有分歧（一說本刀不動 wire-schema 工具面故不
    觸發）——但條文觸發欄含「或 contract 測家族」半句、本刀確動 tests/contract.rs，故按
    觸發成立處理。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 本刀新增命名空間必配裁判＋起手維護批補 RoleAdmin／MenuAdmin 12 支、IpRule 7 支留帳並於 B-098 條文註明（B-098 不關帳）
22. **B-075 順捎與否**。背景：僅當本刀真開 lint 家族檔才順捎（十幾行字串斷言）；封死守門是
    runtime 鎖內重判、非文字掃描形——除非決定額外加「治理面 Policy 端點 seed 政策列 v0 恆
    R_SUPER」靜態守恆。選項：**A（建議）不建靜態守恆、B-075 維持不入**（避免與 runtime 守門
    第二套字面同源；觸發器不變）。B 建靜態守恆＋順捎 B-075——多一道防線、代價＝兩套判準
    要同步維護。
   ➡️ **拍板（2026-08-22 grilling 輪、user 親決）**：A 不建靜態守恆、B-075 維持不入（避免與 runtime 封死守門第二套字面同源）

## §11 拍板決議總表與連動後果（2026-08-22 grilling 輪；22 題＝21 題取建議、§10-6 取 B）

| # | 題 | 決議 | 連動段落 |
|---|---|---|---|
| 1 | 封死條文位置 | 獨立 G6 | §6 Amendment 清單、ADR 0053 |
| 2 | 封死標的集落字 | 謂詞、不寫列數 | §4-②、ADR 0053/0054 |
| 3 | G1 矩陣入憲 | 方向面入條文、矩陣留 ADR/活書 | §4-①、ADR 0053 |
| 4 | grant 面空 diff reload | 照 rev4 仍 reload（刻意例外明文） | §4-①、enforce.rs doc、ADR 0053 |
| 5 | deleteRole 免 reload 轉正 | 不轉正 | §6 |
| 6 | menu 維同實例 | **B**：手動撤銷 menu/button 維入不可復原集（gate 五值） | §4-②④、§2 restorePolicy 列、ADR 0055 |
| 7 | 復原重驗腿 | 固定序五腿（gate→同實例→封死→端點在冊→停用不擋） | §4-④、§7 U7、ADR 0055 |
| 8 | menu 維 protected 納封死 | 不擴、已知態 | §4-②、spec 已知態 |
| 9 | getAllPages 域 | 顯示域＋spec 記不對稱 | §2 表、§5 |
| 10 | roleHome UI | 納入 | §5、§7 U9、§III.2 (iii) |
| 11 | 角色鍵名 | 全用 id | contracts、§5 wrapper |
| 12 | protected 預標載體 | 讀端帶旗標 | 三維讀端契約、wire-schema |
| 13 | §III.2 授權形式 | 加 (iii)＋(iv) 兩列 | §6 Amendment 清單 |
| 14 | 三鍵收斂 | 不收斂 | §5 i18n |
| 15 | H1 括號回填 | PATCH 隨批回填（含 §10-6/7 連動措辭） | §6 Amendment 清單 |
| 16 | B-083 落節 | §5＋§8、§6 零增減 | §6 as-built、U13 |
| 17 | B-024 關帳 | 改記殘餘 | §6 帳務 |
| 18 | B-104 承載 | 併 ADR 0053 | §6 ADR 配置 |
| 19 | seed 68 歸屬 | 刀 B | §2 鄰接面 |
| 20 | B-088 順捎 | 順捎＋豁免兩列 | §7 U10 |
| 21 | B-098 範圍 | 新增必配＋維護批補 12 支、IpRule 留帳 | §7 U0／U11 |
| 22 | B-075 順捎 | 不入 | §6 帳務 |
| — | push | 拍板落帳只 commit 暫不推 | — |

**連動後果（spec 期必承接）**：
- **可復原集收窄**：§10-6＝B ⇒ 歸檔 reason 集三值→五值、回收桶可復原列**只剩 endpoint 維手動
  撤銷**；restorePolicy 因此**不再需要進選單序列化域**（選單／按鈕維分支結構性不可達、gate 首腿
  即拒）——§2 表 restorePolicy 列之「選單／按鈕分支入域」與 §4-④ 七步鎖序之入域步隨之收斂為
  「不入域」（與 updateRoleEndpoints 同口徑：不涉選單資料）；island H1 終態成員之「授權回收桶
  復原之選單／按鈕維分支」回填句（§10-15）須如實寫為結構性不可達。
- **reload 觸發矩陣終態**（ADR 0053 承載、B-104 同批訂正）：移除面三支＝成功且有歸檔才觸發；
  grant 面三支＝Applied 即觸發不問 diff（刻意例外）；restorePolicy 成功＝Applied 觸發；其餘零觸發。
- **封死謂詞**（G6＋ADR 0054）：casbin_rule ptype=p ∧ protected=TRUE ∧ v2∈HTTP 動詞之 (v1,v2)
  集——掛 updateRoleEndpoints 與 restorePolicy 鎖內；menu 維 4 列 protected 不在射程＝已知態。
- **ADR 配置定形**：0053 島 G 入憲（含 G6＋B-104 矩陣訂正＋ADR 0052 條款順捎）／0054 結構性
  封死（B-024①＋翻案觸發條款＋rev3 原形參照）／0055 restorePolicy 五腿＋ADR 0050 §4 復核結論（B）。
