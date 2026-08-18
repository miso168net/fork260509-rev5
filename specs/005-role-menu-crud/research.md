# Research — 005 role＋menu 管理 CRUD 寫端

> Phase 0 產物。本刀階段 0 已跑兩輪 workflow research（18 支 agent、rev3／rev4 兩樹唯讀偵查、
> 產物在 session scratchpad）＋21 題 user 親決；本檔把其中 **tasks／實作期要反覆查用的結論**
> 凍結進 repo（scratchpad 屬 session 級、會消失）。凡「rev4:」前綴＝唯讀藍本樹
> `../fork260509-rev4/` 內路徑。零 NEEDS CLARIFICATION 殘留。

## R1 rev4 對應碼清單（ADR 0019 要求①；實作單元動工前逐檔先讀）

| # | rev4 檔 | 用處（本刀對應面） |
|---|---|---|
| 1 | rev4:rust-api/server/src/handler/menu.rs（905 行全讀） | menu 7 支 handler 藍本；★reload 呼叫點 :329（updateMenu buttons 變更）/:348（deleteMenu）/:364（batchDeleteMenu）＝FR-016 落地形；addMenu 零 casbin 寫＝不 reload（檔頭 :21） |
| 2 | rev4:rust-api/server/src/model/facade/sys_menu.rs（3405 行、選單域狀態機主藍本） | 治理域／顯示域讀端、樹守門（防環／parent 三態／child-first）、同鍵重建雙封、獨有碼判定（in-memory 全掃 list_governed 形——rev5 沿用、量級 seed 78 可忽略） |
| 3 | rev4:rust-api/server/src/model/facade/sys_casbin_archive.rs | 歸檔寫入面＋reason gate；★:713 逐字「caller 指定：deleteMenu 獨有→menu_soft_delete、updateMenu 絕版→menu_button_removed」＝reason 歸屬權威；:356 不可復原集合；域鎖底座（116 行：i64 常數＋兩支薄 fn＋pg_locks 觀測 helper） |
| 4 | rev4:rust-api/server/src/model/facade/sys_role.rs | 三層守門（SEEDED_ROLE_IDS :136 hardcode 形）、in-use 精修（others=total−operator_is_member、拒因回誠實總掛載）、code 形制驗證 |
| 5 | rev4:rust-api/server/src/handler/role.rs（CRUD 段；★as-built 已被 rev4:010 改寫——enter_menu_domain 域鎖、insert_archived 之 role_id 放寬 Option） | role 6 支 handler 藍本；deleteRole 全函式無 reload（免 reload 論證出處） |
| 6 | rev4:rust-api/server/src/auth/enforce.rs | rebuild_enforcer／reload_enforcer 全套；★硬禁令註解 :69/:76/:94（絕不裸呼 load_policy、casbin 2.20.0 clear-then-load、空 policy＝含 R_SUPER 全 deny）；RELOAD_MAX_ATTEMPTS=3＋50ms 線性退避；SC-013 測試骨架（:400 附近） |
| 7 | specs/rev4:009-role-admin/ 全套（role CRUD／roleHome 段＋FR-016 授權判定面同步） | spec 語意權威；contracts 端點形 |
| 8 | specs/rev4:010-menu-admin/ 全套（32 FR／26 T） | 選單域 spec 語意權威；getMenuList/v2 分頁形（頂層計、size clamp[1,100]＝as-built 常數） |
| 9 | rev4:base-web/src/views/manage/menu/{index.vue,modules/menu-operate-modal.vue,modules/shared.ts} | menu 頁藍本；★modal :5-6 標記＝parentId selector 消費 fetchGetMenuTree；:189 fetchGetAllRoles＝upstream 殘留（rev5 不帶）；toggle 形回收桶 |
| 10 | rev4:base-web/src/views/manage/role/{index.vue,modules/role-operate-drawer.vue,modules/role-search.vue} | role 頁藍本（CRUD 面；兩顆授權 modal 不在本刀） |
| 11 | rev4:docs/arc42/decisions/{0048,0049,0051,0052}.md | 島 G 五條原文／role_id 欄與翻案觸發條款／選單域狀態機理據／島 H 五條原文＋MAJOR 界定字面 |

## R2 rev5 拍板差異點清單（ADR 0019 要求②；★防回歸：以下 rev4 行為一律不得帶回）

1. restore 冪等成功 → rev5＝**業務錯誤**（復原現役列＝拒；rev5:handler/ip_rule.rs:23 判例）。
2. 請求上下文缺席放行寫入 → rev5＝**拒寫 5000**（op-log real_ip NOT NULL；憲法 F3① 同向）。
3. `AuditOperation` 大寫 DB 動詞形 → rev5＝**小寫動作名封閉詞彙**（audit.rs 防回歸測既有）。
4. `system_settings::find_by_keys` 批次讀端 → 不搬（單一消費者不開介面；逐鍵讀）。
5. `SELF_SERVICE_ROUTES` 恆附掛白名單 → 不帶回（rev5:handler/route.rs:14 明文）。
6. zh-tw 為 runtime locale → rev5＝治理錨點孤立檔、不上 runtime。
7. 域鎖 key 字面 `"rev4menu"`（0x7265_7634_…） → rev5＝**`"rev5menu"`（0x7265_7635_6D65_6E75）**。
8. rev4 deleteRole 不入域（與 deleteMenu 併發窗零論證） → rev5＝**入域**（grilling 已拍）。
9. rev4 業務錯誤攜參 `BizData` → rev5＝**純 i18n key**（error.rs:37 拍板；島 G2 措辭連動）。
10. rev4 `menu-operate-modal` 開啟打 `fetchGetAllRoles`（template 零消費欄之 upstream 殘留）
    → 不帶。
11. `enforce.rs:8`／`main.rs:56`「不再重載＝終態」 → 本刀 ADR 翻案（理由子句被移除面推翻）。

## R3 依賴釘版（CLAUDE.md §6）

**零新依賴。** casbin 2.20.0（rust-api/Cargo.toml:46 釘版、與 rev4 同版——硬禁令技術根據原封
成立）；axum／sea-orm／sea-orm-adapter 既有；前端零新套件。毋須版本拍板。

## R4 序列化域與鎖序（島 H1 落地細節）

- 載體：`SELECT pg_advisory_xact_lock($1)` 走 raw Statement（守 entity_access_lint）、xact 級
  自動釋放；零逾時、零重試、零 try_lock（rev4 底座 116 行照形）。
- key＝`0x7265_7635_6D65_6E75`（i64 常數、ASCII "rev5menu"；活書級可調）。
- 本刀進域：addMenu／updateMenu／deleteMenu／batchDeleteMenu／restoreMenu＋deleteRole／
  batchDeleteRole。updateRole／addRole／roleHome 寫端不進域（零 casbin 面、零選單資料）。
- 固定鎖序＝`advisory → 歸檔表列 → sys_role 列 → sys_menu 列 → casbin_rule`；域鎖必為
  txn 首動作、不下沉 facade fn（下沉即排到列鎖之後破鎖序——rev4 註解逐字警告）。
- ABBA 分析：per-user advisory 鎖（rev5:handler/auth/login.rs:519、uid 為 key）與域鎖共用
  64-bit key space——①不碰撞（高位 ASCII 常數 vs 個位 bigserial）②鎖集合零交集（login txn
  不取域鎖、域寫端不取 per-user）⇒ 結構性無 ABBA。★三個失效條件記入 ADR：role 寫端連動
  撤 session／刀 B user 寫端進場／同 key 重入。
- 機器證兩坑：①觀測用 pg_locks 的 advisory NOT-granted 等待者（兩寫端鎖不相交列、
  pg_blocking_pids 測不到）②64-bit key 在 pg_locks 拆 `classid`（高 32）＋`objid`（低 32），
  bigint 直比恆假。

## R5 判定面同步（rebuild-swap；grilling G1 基建移入本刀）

- 形：`rebuild_enforcer(db)` 另建全新 Enforcer（model→adapter→new→load_policy 四步鏡像
  init）、任一步失敗整體 Err 不產實例；成功才 write 鎖內一行 move-assign。
- 失敗契約：keep-last-good＋結構化告警＋metrics `casbin_reload_total{ok|retry|exhausted}`；
  `RELOAD_MAX_ATTEMPTS=3`＋`RELOAD_RETRY_BACKOFF_MS=50` 線性退避（寫死常數）；耗盡＝維持
  舊面持續告警、服務不中斷。
- 觸發矩陣：deleteMenu／batchDeleteMenu／updateMenu-buttons 成功且有連動歸檔（commit 後）
  ＝觸發；被拒／無作用／標的不存在／無 buttons 變更＝不觸發（`?` 早退結構性保證）；
  deleteRole＝不觸發（in-use 守門保證零掛載、殘留無授權效果——rev4 as-built 同形、ADR 記載）；
  addMenu／restoreMenu 零 casbin 寫＝不觸發。
- ★硬禁令＋版本鎖：絕不對 live enforcer 裸呼 `load_policy`——casbin 2.20.0 之 clear-then-load
  ＋MODEL_CONF `e = some(where p.eft == allow)` ⇒ 空 policy＝含 R_SUPER 全 deny、唯重啟可救；
  註解帶版本鎖、升版必重核。
- 測試四支：SC-013 形失敗注入（壞 conn⇒舊面續 allow R_SUPER）／「改寫為裸呼」必轉紅負向
  自證／觸發條件特性鎖定／移除面端到端（DB＋in-memory 雙斷言）。
- enforcer＝AppState 既有欄（Arc<RwLock<Enforcer>>）⇒ 零新欄、不觸 ADR 0041 七欄封條。

## R6 選單域狀態機要點（data-model §3 的推導依據）

- 治理域（list_governed＝未刪含停用）新建；顯示域（list_active）既有不動。治理候選誤用
  顯示域＝「停用靜默升級為永久撤銷」（rev4:010 血淚、必配負向測試）。
- 同鍵重建零繼承雙封：現役無殘留（序列化域＋刪除連動歸檔掃盡）＋歸檔不可回灌（reason gate）；
  本刀含判定面同步 ⇒ in-memory 面同受約束（雙斷言）。
- 絕版判定聯集域＝**未刪含停用**（clarify Q1；用顯示域＝button 維的「停用→永久撤銷」翻版）。
- 防環：上溯祖先鏈遇自身拒、上限常數；parent 三處一致（新增／改父／復原：父存在且未刪、
  停用不擋、parentId=0 豁免）；constant 父鏈常量性守門（rev5 專屬；現況 seed TRUE 0 列）。
- 幽靈父收縮語意不動（rev5:facade/sys_menu.rs:119-123 既有拍板）。
- routeName 活性唯一：`sys_menu_route_name_active_uniq` 基線既有（機器核）；addMenu 雙層
  守門（clarify Q2：域鎖內先驗顯式拒＋23505 兜底收斂同一拒因）。

## R7 role CRUD 守門矩陣要點

- deleteRole 三層固定序：seeded（`SEEDED_ROLE_IDS=[1,2,3]`＋`SUPER_ROLE_CODE="R_SUPER"`
  常數本刀建）→ in-use（`others = total − operator_is_member`、拒因語意回誠實總掛載）→
  self-role。★in-use／self-role 兩腿於刀 B 前生產面不可達（G6 註記；測試種 sys_user_role
  指派列構造、零旗標）。
- 停用雙護欄：不可停用自己所屬角色＋R_SUPER 恆禁停用（不因操作者身分而異）。
- code 形制 `^[A-Za-z0-9_]{1,64}$`＋活性唯一（`sys_role_code_active_uniq` 基線既有）＋不可變。
- 部分更新三態照 ADR 0023；全 None 提前 no-op。
- deleteRole 歸檔：掃 `v0=role_code` 全三維含 protected 列、reason=`role_soft_delete`、
  單向無 restore。

## R8 測試設施與機器閘衝擊（tasks 的硬前置）

1. **清理守衛**：`sys_role`／`sys_menu`／`casbin_rule`（＋歸檔表）皆不在 schema-gate
   `RUNTIME_APPEND_TABLES` 收窄集 ⇒ gate2 逐列 diff、測試殘列必紅。比照 004 守衛家族建
   RAII Drop 守衛＋**守衛自證測**（造 committed 列→前提自證非零→Drop→回零＋sequence 還原
   斷言；B-085 紀律——Drop 寫壞＝影響 0 列零錯誤恆綠）。
2. **sequence**：`sys_role_id_seq`／`sys_menu_id_seq` 有 gate2 setval 期望值（sys_role=3）；
   addRole／addMenu 推進 seq 與 gate 的互動＝**tasks 早期顯式查證項**；測試一律顯式大 id。
3. **seed 寫死測**：`list_active_reads_seed_78_rows` 等——本刀零 seed 變更 ⇒ 不紅；任何
   單元若動 seed 即為射程違規訊號。
4. **router 三源 lint／contract case**：+16 條 ROUTES ⇒ `ROUTES_COUNT` 22→38 同 commit bump、
   contract.rs 逐端點 case（含授權態矩陣：Admin 對寫端 5003、對 getRoleList 通）。
5. **wire-schema 快照**：新回應型入快照；`PageRes` 上移＝既有快照字面不變、引用路徑變。
6. **fork-delta-lint**：修改型標記僅允許出現於 plan「Source Code」所列 base-web 檔集；
   兩顆授權 modal 出現任何 diff＝紅。
7. **view-render-guard**：memo 欄純文字插值自動在掃描面（零加接線）。

## R9 本輪查證對既有敘述的三筆校正（grilling 產物、已回寫 brainstorm）

1. 「deleteRole／deleteMenu 免 reload」→ **只對 deleteRole 成立**；menu 移除面三支 rev4
   MUST reload（FR-016）⇒ 熱重載基建移入本刀。
2. deleteMenu 獨有 button 碼歸檔 reason ＝ `menu_soft_delete`（**非** `menu_button_removed`
   ——後者專屬 updateMenu buttons 變更路徑；rev4:sys_casbin_archive.rs:713 逐字）。
3. updateMenu 之 buttons 絕版歸檔路徑為獨立寫端行為（原單刀案漏列）——已入 spec FR-025。

## R10 執行單元切分（tasks 的 phase 骨架建議；~17 支）

U1 憲法 Amendment（島 H）＋三支 ADR（★主線親做、硬閘：accepted 前不得動 base-web 既有檔）→
U2 Setup（handler 骨架／AuditOperation 擴詞彙／PageRes 上移）→ U3 域鎖底座＋ABBA 機器證 →
U4 rebuild-swap 判定面同步（四測）→ U5 鎖讀 helper＋清理守衛＋自證測 → U6 治理域讀端
（list_governed／getMenuList/v2／getDeletedMenus／getMenuTree）→ U7~U8 role CRUD
（facade TDD→handler+router）→ U9~U11 menu CRUD 寫端＋回收桶＋constant 守門＋reload 接線 →
U12 零繼承鏈端到端（★防恆綠：先種 live 授權再測）→ U13 i18n 三處＋Lint24 → U14~U15 前端
（role 頁＋memo／menu 頁＋toggle＋memo）→ U16 全量閘＋CDP 三方對照 → U17 收刀簿記。
- 高風險共享檔序列鏈（同檔任務不標 [P]）：facade/sys_menu.rs（U6/U9~U11）、facade/sys_role.rs
  （U5/U7）、facade/sys_casbin_archive.rs（U3/U5/U9）、handler/role.rs（U7~U8）、router.rs
  （U8/U11）、tests/contract.rs（U8/U11）、envelope.rs＋handler/ip_rule.rs（U2）。
- 編排慣例：implementer=fable 1m xhigh、review=opus 1m xhigh、防呆六件套
  （workflow-unit-orchestration-shape）。
