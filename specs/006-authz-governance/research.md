# Research — 006 三維授權治理＋結構性封死＋授權回收桶（島 G 入憲）

> Phase 0 產物。本刀階段 0 已有 brainstorm 五 lens 偵查＋22 題 user 親決；plan 期再跑一輪
> research workflow（五支 lens、opus xhigh、唯讀：rev4 後端三維／rev4 回收桶＋reload／前端三 modal
> ＋policy-archive／rev5 後端現況／治理面原料；詳細報告在 session scratchpad、會消失）。本檔把其中
> **tasks／實作期要反覆查用的結論**凍結進 repo。凡「rev4:」前綴＝唯讀藍本樹 `../fork260509-rev4/`
> 內路徑；行號＝2026-08-23 實讀。零 NEEDS CLARIFICATION 殘留。工程選擇一律「主線自拍、回報備查」
> 標示，拍板級者留 U1（user 親決）。

## R1 rev4 對應碼清單（ADR 0019 要求①；實作單元動工前逐檔先讀）

| # | rev4 檔 | 用處（本刀對應面） |
|---|---|---|
| 1 | rev4:rust-api/server/src/model/facade/sys_casbin_policy.rs（912 行全讀） | 三維寫端純資料語意藍本：`ENDPOINT_METHODS`:35／`Dimension`:47／`PolicyOutcome`:85（恰兩態、空 diff 仍 Applied :81-83）／`set_role_dimension`:107／`set_role_endpoints`:129／`apply_full_replace`:160-236（diff→protected-reject→archive-move＋grant；刪除集已是 id 圈定 :203-209）／`live_rows_of_dim`:243／`current_targets`:269／`current_endpoints`:282／`menu_ids_to_route_names`:298（menu orphan skip）／`route_names_to_menu_ids`:311；九支測 :320-912（`empty_diff_still_applied`:475、`protected_reject_zero_change_zero_archive_with_blocked`:511、`current_endpoints_identifies_by_method_whitelist_not_exclusion`:607、`grant_during_delete_serialized_by_role_lock_no_residual`:815） |
| 2 | rev4:rust-api/server/src/handler/role.rs（三維段 :434-700＋endpoint_tests :880-1835） | handler 薄殼形：`begin_and_lock_role`:434（begin→域鎖→FOR UPDATE 角色列→回 (txn, code, id)）／`finish_governed`:461（稽核→commit→**commit 下一行 reload** :487-489）／三維六支 :508-630／`role_code_of`:634／`get_all_pages`:656（顯示域、無序）／`get_all_buttons`:668／★`policy_endpoints`:680＋E0391 斷環解說 :675-687／`get_all_endpoints`:691；端到端測 :1536-1835（整批拒零變更 :1633、集合恰等 :1687／:1707、停用不被升級撤銷 :1786） |
| 3 | rev4:rust-api/server/src/model/facade/sys_casbin_archive.rs（回收桶段 :239-461、測 :1049-1222） | `ArchivedRecord`:248／`dimension_of`:255／`list`:271（雙濾＋`archived_at DESC, id DESC`＋restorable 兩半 :308-318）／`restore`:330（★實碼八動作：begin→**無條件域鎖 :341（rev5 不帶回）**→鎖 archive 列 :344→reason gate :358→鎖活角色列 by v0 :365→同實例 :374→menu orphan :385（rev5 不可達）→7a NoOp :394／7b Applied :413-449（protected 顯式 Set(false)、created_at=now、created_by=復原者、23505 收斂 :428-436）→op-log :442）；測 `list_dual_filter_desc_and_restorable_flags`:1049／`menu_reasons_not_restorable_list_and_restore`:1123（五值成員測與旗標同判準測的直接藍本形）／`restore_during_delete_serialized_by_role_lock_no_residual`:1222 |
| 4 | rev4:rust-api/server/src/handler/policy_archive.rs（709 行全讀） | `ArchivedPolicyQuery`:43（四欄 Option）／`RestorePolicyReq`:53（★無 Default、裸 Json——rev5 必加 Default 走 json_or_default）／`ArchivedPolicy`:68（14 欄）／`serialize_opt_i64_number_guarded`:95／`to_wire`:108（dimension 先借 v2 再 move）／`get_archived_policies`:158（current max(1)、size 預設 10 clamp [1,100]）／`restore_policy`:183（Applied→reload :195／NoOp 不 reload／NotRestorable→`biz.policy.notRestorable`） |
| 5 | rev4:rust-api/server/src/model/facade/sys_role.rs | `active_ids_by_codes`:115（批次 code→id、純 SELECT 不鎖、空集不打 DB）／`find_active_by_id`:96（無鎖整列讀）——rev5 皆不存在、須新建 |
| 6 | rev4:rust-api/server/src/model/facade/sys_menu.rs:306-322 | `all_button_codes`（list_governed 全掃→buttons jsonb→HashSet 首見序去重）＝getAllButtons 藍本 |
| 7 | rev4:rust-api/server/src/auth/enforce.rs | reload 呼叫紀律對照（rev4 無 `RELOAD_SERIAL`、無「不得持讀鎖」明文——rev5 較嚴） |
| 8 | rev4:rust-api/server/src/router.rs:328-445 | 11 條 RouteDef 字面與 case_key（`get-role-menu`／`update-role-menu`／`get-role-button`／`update-role-button`／`get-role-endpoints`／`update-role-endpoints`／`get-all-pages`／`get-all-buttons`／`get-all-endpoints`／`get-archived-policies`／`restore-policy`） |
| 9 | rev4:rust-api/server/tests/contract.rs:154-190／:943-1090 | 十條 contract case（★只做 ROUTES 結構斷言＋無 token→3333；rev5 形不同、不可照抄） |
| 10 | specs/rev4:009-role-admin/（spec.md rev4:FR-017～rev4:FR-036、contracts/role-admin-endpoints.md 之三維／支撐讀／回收桶三節、research.md 之鎖序 R7 節） | spec 語意權威；wire 形 |
| 11 | rev4:base-web/src/views/manage/role/modules/{menu-auth-modal.vue（153 行、6 原行）,button-auth-modal.vue（127 行、21 原行）,endpoint-auth-modal.vue（134 行新檔）,role-operate-drawer.vue（三鈕三 modal :131-139）} | 三 modal 藍本；★`protected-revoke-detail.ts`（36 行）與三處 import／消費（menu :12／:100-102、button :7／:78-80、endpoint :8／:87-89）不帶回 |
| 12 | rev4:base-web/src/views/manage/policy-archive/{index.vue（153 行）,modules/policy-archive-search.vue（92 行）} | 回收桶頁藍本（8 欄、restorable=false 停用態 :85-102、restore→getData() 留當頁 :107-117）；★`scroll-x=1014` vs Σ=1054 為 rev4 內部不一致、rev5 自算 |
| 13 | rev4:base-web/src/service/api/rev4-role-admin.ts（16 支 fetcher）＋rev4:base-web/src/typings/api/rev4-role-admin.d.ts（98 行、併入 Api.SystemManage——rev5 不帶回） | wrapper／typings 形 |
| 14 | rev4:base-web/src/locales/langs/{zh-cn,en-us,zh-tw}.ts 之 `page.manage.policyArchive`（15 葉鍵，zh-cn:745-765）／`page.manage.role.endpointAuth`（zh-cn:734）／`route.manage_policy-archive`（zh-cn:411）／`backend.biz.role.protectedRevoke`（zh-cn:46）／`backend.biz.policy.notRestorable`（zh-cn:107） | i18n 譯文藍本（三語逐鍵表見 contracts/msg-keys.md） |
| 15 | rev4:docs/arc42/decisions/{0048（島 G 五條原文＋MAJOR 界定）,0049（role_id＋翻案觸發條款）,0050（明細通道）,0051（選單域狀態機）,0063（按鈕碼三護欄）} ＋ rev4:.specify/memory/constitution.md §I.7 島 G 段（憲法條文形） | 島 G 落字原料（見 R10） |
| 16 | rev3:rust-api commit `3bfab71`（no-escalation 唯一先例；只給指針、不細讀） | 0054 ADR 參照（三缺陷字面＝spec FR-027①） |

## R2 rev5 拍板差異點清單（ADR 0019 要求②；★防回歸：以下 rev4 行為一律不得帶回）

1. 拒因攜參明細（`BizData`／`BlockedTarget`／`protected-revoke-detail.ts`／`DETAIL` 對照表）→ rev5 **純 key**（`AppError` 無 `BizData` 變體、error.rs:40-70 十變體）；`PolicyOutcome::Rejected` 內部可帶 blocked 清單供 tracing 與測試斷言、**永不上 wire**。
2. 角色鍵 `roleId`（rev4 wrapper 八處、三支 modal prop、六支 DTO）→ rev5 wire 一律 `id`（FR-003）；★modal **prop 名**保留 `roleId`（基線形、少動基線行）。
3. restorePolicy **無條件入選單序列化域**（rev4:sys_casbin_archive.rs:341）→ rev5 不入域（FR-013／FR-033）；連帶 `sys_casbin_archive.rs:14-16` 域成員 doc 與憲法 H1 括號須改寫（R11）。
4. reason gate 三值、menu／button revoke 可復原（rev4 測 :1072-1073 逐字證）→ rev5 五值；既有測 `is_non_restorable_reason_pins_three_member_set`（sys_casbin_archive.rs:348、:362 負向迴圈）**首日必改**（改名＋擴五值＋`matches!` 五臂）。
5. 復原判定兩腿＋menu orphan 腿、不驗端點在冊、不驗封死 → rev5 固定序五腿；restorable 旗標與①②③④逐腿同判準（rev4 兩半與四腿不同判準＝「顯示可復原、點了被拒」窗，rev5 消滅）。
6. 無授予側守門 → rev5 結構性封死（謂詞式、鎖內現查、掛 updateRoleEndpoints 與 restorePolicy）——**零藍本、從零設計**。
7. `insert_archived(conn, ArchiveSnapshot, Some(role_id), …)` caller 傳 role_id → rev5 內收 `&casbin_rule::Model` 反查（sys_casbin_archive.rs:166-177）；grant 面 revoke 直接把 live row 引用傳入、逐欄複製九行消失；歸檔 MUST 早於任何刪寫。
8. 連動歸檔刪除集重跑過濾 → rev5 以剛歸檔那批 id 圈定（grant 面 rev4 `apply_full_replace` 本就 by-id、可照參；連動歸檔面才是 rev4 不得帶回處）。
9. roleHome wire `roleId`／裸 string／NULL 摺疊空字串 → rev5 `id`／`{home}`／誠實 null（005 契約 wire-role-admin.md §7-8；前端初值 `shallowRef<string|null>(null)`＋NSelect `clearable`）。
10. role 頁三鈕 hasAuth gating（rev4:views/manage/role/index.vue 七處）→ rev5 不 gating、門在頁級；role/index.vue 一行不動。
11. `archive_all_menu_policies`／`archive_button_code_policies` 兩支具名 fn → rev5 私有泛用 `archive_policy_rows_of`（sys_menu.rs:739）；本刀三維 revoke 走新 facade 內部路徑、不建具名包裝。
12. deleteMenu／batchDeleteMenu 無條件 reload → rev5 `if archived`；★grant 面方向相反（Applied 即觸發、不問 diff＝刻意例外），兩者並陳、勿互相污染。
13. 稽核詞彙 8 變體全大寫（`"UPDATE"`／`"RESTORE"`）→ rev5 恰五值小寫；三維寫端 `Update`、restorePolicy `Restore`；`t005_…_stays_five` 不得改。
14. 請求上下文缺席 fail-open（rev4 `audit_meta` 各欄 None 放行）→ rev5 `audit_operator` 拒寫 5000（F3①）。
15. 未認證碼 3333 → rev5 8888＋`auth.session.reLogin`（contract.rs:786-789 釘）。
16. `Api.SystemManage` 併入（rev4 typings）→ rev5 獨立命名空間 `Api.RoleAdmin`／新 `Api.PolicyArchive`。
17. static meta 三欄（`icon: 'carbon:trash-can'`／`order`／`roles`，rev4 routes.ts:295-306 手加）→ rev5 產物條目只有 title＋i18nKey；icon 真源＝seed 列 10 `mdi:recycle`；route-artifact-gate 第③道攔手加。
18. rev4 endpoint-auth-modal `check-strategy="child"` 未寫 `cascade` ＝結構性 inert（naive-ui 2.44.1／treemate 早退分支機器定案，群組點擊對 payload 零貢獻）→ rev5 endpoint modal **顯式加 `cascade`**（FR-040 群組級勾選才成立）。
19. rev4 button-auth-modal 掛載即 `init()`（rev5 現況同）→ rev5 改 `watch(visible)`（rev4 自己已改、理由：切換角色讀舊值）。
20. `scroll-x=1014`（rev4 policy-archive）→ rev5 不變式 Σ(width|minWidth)＝scroll-x、自算。
21. rev4 contract case 把路徑字面寫進斷言 → rev5 由 `ROUTES` 依 case_key 反查（contract.rs:6-14）；case 寫法不可照抄。
22. `domain_lock.rs` 獨立檔 → rev5 已併入 `sys_casbin_archive.rs`（檔級對照勿誤判缺件）。

## R3 依賴釘版（CLAUDE.md §6）

**零新依賴。** casbin 2.20.0（rust-api/Cargo.toml:46、`default-features=false`、版本錨 tests/authz_entrypoint_lint.rs:820 不升版）；
naive-ui 2.44.1（base-web/package.json:73、NTree／NDataTable／NPopconfirm 既有）；typescript-json-schema 0.67.4（tools/wire-schema.py:35、
`--strictNullChecks` 不可省）。毋須版本拍板。

## R4 分層與鎖序（主線自拍、回報備查）

- **分層落點＝候選甲**：rev5 拍板「守門與交易語意全在 facade」（handler/role.rs:11-15 doc）⇒ rev4 的 `begin_and_lock_role`／`finish_governed`
  兩支 handler 薄殼**不帶回**。新 facade `sys_casbin_policy.rs` 之寫端**自管 txn**：`begin`→（menu／button 維）`enter_menu_domain_db` 為首動作
  →`find_active_by_id_for_update` 鎖標的角色列→讀 live→diff→protected 整批拒→（endpoint 維）封死謂詞鎖內現查→archive-move＋INSERT→
  op-log 同交易→commit→回 `PolicyOutcome`；handler 只做 wire 解析→呼叫→`Applied`⇒`reload_enforcer(&state)`／`Rejected`⇒`Err(Biz(key))`
  （與 menu.rs `if archived { reload }` 同構）。reload 留 handler（facade 拿不到 `AppState`）。
- **固定鎖序**（島 G5 條文要寫）：advisory（僅 menu／button 維）→歸檔表列（僅 restorePolicy）→sys_role 列（FOR UPDATE）→sys_menu 列（不鎖、讀治理域映射於同 txn）→casbin_rule。
  endpoint 維寫端與 restorePolicy 不入域、以 sys_role 列鎖序列化（同角色 in-flight 寫端互斥；與 deleteRole 共享列鎖）。
- **commit 後才 reload**＝rev4 `finish_governed` :487-489 同形；rev5 多一條硬紀律：呼叫時**不得持 `state.enforcer` 讀鎖**（enforce.rs:127-136）
  ＋`RELOAD_SERIAL` 互斥（:166-167）。四支新呼叫點（三維寫端＋restorePolicy）逐支必守；兩道名冊閘對「持讀鎖再呼」結構性無感——
  候選新守門（源碼掃描 reload 呼叫點所在 fn 內不得出現 `enforcer.read()`）登 BACKLOG（R8-⑩）。
- 讀端不取鎖：三支讀端用 `&state.db` 無交易（rev4 `role_code_of` 形）；rev5 無無鎖 by-id 活性讀 ⇒ 新建 `sys_role::active_code_of(id) -> Option<String>`
  （窄投影、照 `home_of_role`:701 範式）。

## R5 三維寫端落地細節（主線自拍逐項）

1. **全量替換 diff**：`current: HashSet<(v1,v2)>` ← live；`to_revoke`＝live∖desired；`to_grant`＝desired∖current（desired 去重、★**排序後再 INSERT**
   ——rev4 迭代 HashSet 落列序非決定性，rev5 為可重現性與 seq 紀律改確定序）。
2. **protected 整批拒**：`to_revoke.iter().any(|r| r.protected)` 於任何寫之前；`Rejected{blocked: Vec<(v1,v2)>}` 內部保留（tracing＋測試）、wire 純 key
   `biz.role.protectedRevoke`。
3. **封死謂詞（endpoint 維寫端）**：`to_grant` 非空且標的角色非 R_SUPER（`SUPER_ROLE_CODE` 常數、繼承其 seed 釘）時，鎖內查 `casbin_rule`
   中 `ptype='p' ∧ protected=TRUE ∧ v2∈HTTP 動詞` 之 `(v1,v2)` 集（單次 SELECT、HashSet 比對）；`to_grant ∩ 集合 ≠ ∅`⇒整批拒 `biz.role.protectedGrant`；
   先判 protected 整批拒、再判封死（兩拒因互斥、固定序）。restorePolicy 第③腿共用同一支 facade fn。
4. **候選集與 orphan skip**：menu 維＝`list_governed` 映射 id↔route_name（鎖內、同 txn）、界外 id 靜默跳過；button 維＝`all_button_codes` 聯集、
   界外碼跳過；endpoint 維＝handler 傳入 `policy_endpoints()` 候選集（`(path,method)`）、界外（含非 GET／POST／DELETE 之 method）靜默跳過
   （rev4 doc 宣稱把關、as-built 零把關——rev5 真做、三維同式；**rev5 新增行為**）。回應帶實際生效集合（orphan skip 後的 desired）。
5. **`ENDPOINT_METHODS`**：自 `router::HttpMethod::as_str()` 導出（單一真源，避免第二份字面）——facade 讀 router 常數屬層級方向問題，
   故由 handler 端把「方法白名單」與候選集一併傳入 facade（facade 保持 router-agnostic）。
6. **grant 治理欄**：`protected=Set(false)`、`created_at=Set(now)`、`created_by=Set(Some(operator.id))`、`v3..v5=""`、`ptype="p"`。
7. **revoke**：逐列 `insert_archived(&txn, row, REASON_*_REVOKE, Some(operator.id))`（role_id 內收反查、標的角色列已鎖且活性⇒恆 Some）→
   `delete_many().filter(Id.is_in(剛歸檔 ids))`。三個 revoke reason 常數新立於 `sys_casbin_archive.rs`（`menu_revoke`／`button_revoke`／`endpoint_revoke`）。
8. **稽核**：`AuditEvent{ operation: Update, entity_table: "sys_role", entity_id: Some(role_id), payload_before: None,
   payload_after: json!({"dimension", "revoked": n, "granted": n}), operator }`（rev4 形＋rev5 六欄 `AuditEvent`；標的表歸 entity_table、動作歸 operation）。
9. **outcome 恰兩態**：`Applied{revoked, granted, effective}`／`Rejected{blocked}`；空 diff＝`Applied{0,0,…}` 仍 reload（FR-020）。
10. **getAllPages 穩定序**：`list_active` 無序（sys_menu.rs:108 doc 逐字）⇒ handler 側 `(order, id)` 排序後回（與組樹同序）；getAllButtons 首見序去重；
    getAllEndpoints 照 ROUTES 宣告序。
11. **E0391 斷環**：`policy_endpoints() -> Vec<Endpoint>` 具名 fn（非 async、具體回型）落 handler/role.rs；實作單元第一件事＝最小編譯探針。

## R6 回收桶落地細節（主線自拍逐項）

1. **list**：`roleCode` 空字串忽略、`dimension` 封閉枚舉 menu／button／endpoint（端點＝`v2.is_in(ENDPOINT_METHODS)`）、未知值沿 rev4 靜默不濾（typings union 已限）；
   `archived_at DESC, id DESC`；size 預設 10、clamp [1,100]（沿 rev5 role 列表形 handler/role.rs:403）、`current` 上界 `MAX_CURRENT`。
2. **restorable 旗標四腿批次料源**：①reason 單點 fn；②`sys_role::active_ids_by_codes(codes)`（新建、純 SELECT 不鎖、空集不打 DB、活性＝`deleted_at IS NULL` 不含 status——
   **不可複用** `all_active_enabled`）；③protected 集單次 SELECT（同 R5-3 謂詞）；④`ROUTES` 內建集合（handler 傳入）；⑤免算。menu／button 維列因①恆 false、②③④短路。
3. **restore 鎖序**（不入域）：begin→鎖 archive 列（`FOR UPDATE`、查無⇒NotRestorable）→①reason gate→鎖活角色列 by `v0`（`find_active_by_code_for_update`；查無⇒NotRestorable）
   →②同實例（`archived.role_id != Some(role.id)`⇒NotRestorable、NULL 恆不等）→③封死（標的角色非 R_SUPER ∧ `(v1,v2)`∈protected 集⇒NotRestorable）
   →④端點在冊（`(v1,v2)`∉候選集⇒NotRestorable）→⑤不擋→7a NoOp（七欄身分鍵已 live⇒刪歸檔列、commit、零 op-log、不 reload）／7b Applied（INSERT：
   `ptype`／`v0..v5` 快照過境、`protected=Set(false)` **顯式**、`created_at=now`、`created_by=Some(復原者)`——沿 rev4、復原＝新 grant 事件；
   23505 撞 `unique_key_sea_orm_adapter` 以 `violated_constraint` 收窄⇒NotRestorable；刪歸檔列；op-log `Restore`／`entity_table="sys_role"`／
   `payload_after={archive_id, dimension, target, act}`；commit）。handler：Applied⇒reload；NoOp⇒`0000`；NotRestorable⇒`biz.policy.notRestorable`。
4. **wire**：`ArchivedPolicy` 15 欄（rev4 14＋rev5 將 `archivedBy` 改 enrich 帳號名 `string|null`、`roleId: number|null` 走 `Option<i64>` 守衛序列化
   ——新建 `envelope::serialize_opt_i64_number_guarded`（候選 B、單點））；`restorePolicy` body `{id}`（歸檔列 id）、DTO 帶 `Default` 走 `json_or_default`。
5. **NoOp 與 Applied 對前端不可區分**（同 `0000`＋`data:null`）＝沿 rev4、已知態（UI reload 列表即見）。
6. **併發機器證候選**：restore-during-delete 以 `pg_blocking_pids` 形（rev4 :1222；rev5 restorePolicy 不入域、共享 sys_role 列鎖⇒測得到）——spec FR-058 未強制、列為建議測。

## R7 判定面同步接線（島 G1 消費）

- 呼叫者 3→7 支：handler/menu.rs 三處（既有）＋handler/role.rs 三維寫端（Applied）＋handler/policy_archive.rs restorePolicy（Applied）。
- `RELOAD_CALL_FILES`（tests/authz_entrypoint_lint.rs:353）一檔→三檔 `["handler/menu.rs","handler/policy_archive.rs","handler/role.rs"]`；主守恆為**有序 Vec 恰等**
  （:505-510）、實得序由 `scanned_files_excluding_home()` 決定——**實作期實跑確認、勿憑字典序推論**；doc :340-352 同 commit 改寫；擴列時機＝第一個 grant 面
  寫端接上 reload 的同一 commit（早擴／晚擴皆紅）。`ENFORCER_WRITE_FILES` 維持空冊；`ALLOWED_DECISION_FILES` 維持恰一檔。
- enforce.rs 觸發矩陣 doc :138-162 擴為 7 列＋「grant 面刻意例外」句＋`:162`「觸發面僅移除面」句改寫；`:147-148` 釘死句保留。
- 測形：rev5 行為半藍本＝handler/menu.rs:1100 `menu_reload_wiring_matrix_via_endpoints`（`casbin_reload_total{outcome="ok"}` 增量、serial 確定性）
  ——本刀 grant 面特性測（Applied 觸發／Rejected 不觸發／空 diff 觸發／restorePolicy Applied 觸發、NoOp 不觸發）照此形自建（rev4 無端到端藍本）。

## R8 測試設施與機器閘衝擊（tasks 的硬前置；10 道閘逐一）

1. `ROUTES_COUNT` 38→49（router.rs:460；不變式測 :715）＋`docs-sync.py generate` 重算 routes.md（Lint02）；ROUTES 字面形受 `parse_router_routes` 行級窄假設約束（每欄一行、closure 形）。
2. contract coverage gate 雙向（contract.rs:1140／:1156）⇒ **route 與 case 同 commit**；registry 38→49；新共用 verify fn 必配貼界自證（:1083 形）；授權態矩陣（`common::real_seed_app()`＋`hit_as_seed_user`＋`role_path_of`＋`assert_denied_5003`）＝Super 通、Admin／User 對 11 支皆 5003；`hit_as_seed_user` 必植 ConnectInfo。
3. `authz_entrypoint_lint` 三名冊（R7）；新 handler／facade 不得出現 `enforce*` 方法呼叫形；枚舉政策走 `get_filtered_policy`；protected 判定走 entity 面。
4. `entity_access_lint`：新 `handler/policy_archive.rs` 零 path-root `entity::`（endpoint_tests 造列走 raw `Statement`）；新 facade 檔在排除面內。
5. wire-schema：跨子庫兩段式（前端型先 commit base-web→容器內 `tools/wire-schema.py extract`→快照 commit rust-api→外層 pin）；新命名空間 `Api.PolicyArchive.*`＋`Api.RoleAdmin` 新型各配裁判（正向＋反例；回應型以 rust 實例序列化判過；protected 欄為重點）；definitions 57→淨增。
6. schema-gate gate2：`casbin_rule`／`sys_casbin_policy_archive` 皆不在 `RUNTIME_APPEND_TABLES`（schema-gate.py:141）⇒逐列全等；`CasbinCleanup`（seq (163,true)／archive (1,false)）與 `RoleCleanup`／`MenuCleanup` 成對掛；**清理／釋放先於斷言**（持鎖 panic 掛死紀律）；CDP 走查排 gate 之後或走查後還原（`casbin_rule_id_seq` setval 163 true＋archive seq 1 false＋清列）。
7. `view-render-guard`（掃 `views/manage/**`、連註解也不得出現禁字面）與 `route-artifact-gate`（產物四檔三道斷言；施工序＝加 view→外掛重算→四檔同 commit）。
8. `fork-delta-lint`：修改型僅允許出現於 FR-047 檔集；兩 modal 自基線逐位一致起改（sha256 兩側相同、基線 tip `8be6f9b`）；新檔檔頭 `[rev5-inline MANAGE-PAGE-WIRING+ 006-…]`（先例 ip-rule/index.vue:2）。
9. i18n：Lint24 後端實發集（字面 `Cow::Borrowed`、常數形會觸 `I18N_CONST_ROSTER` 空表 fail-loud）vs zh-tw.ts backend 樹雙向；前後端鍵同 commit；zh-cn 零 lint⇒顯式 `pnpm typecheck`；`page:` 型節必補。
10. 守門非 vacuous（FR-059）：封死變異自證（弄壞謂詞／掛點→紅→還原→綠）；五腿各一負向＋逐腿同判準測（旗標 vs 權威）；reason gate 五值成員測（正向餵獨立字面、不引常數）；orphan skip 三維負向；protected 整批拒負向（零變更、零歸檔、零 reload）；grant 面觸發特性測（R7）；兩支入域寫端 NOT-granted 機器證（照 tests/menu_domain_serialization.rs:230 骨架、觀測 helper `menu_domain_waiter_count`）；restore-during-delete 建議測（R6-6）。
    ★候選新守門（登 BACKLOG、非本刀必辦）：「reload 呼叫點所在 fn 內不得出現 `enforcer.read()`」源碼掃描（持讀鎖呼叫 reload 之零機器訊號面）；events summary 無 erratum 出口（L5 發現、另登記）。
11. 測試基準＝**682**（2026-08-23 容器內 `cargo test --workspace -- --test-threads=1` 實跑、含 doctest 與 `tests/common/mod.rs` 五 crate 重複編譯）；
    源碼面 grep 674 為靜態估值、勿當基準。
12. B-088 對賬閘落點（主線自拍）：新 `tools/seed-view-gate.py`（seed `sys_menu.component` 之 `view.*` 集 ⊆ `base-web/src/views/**` 目錄導出集；具名豁免常數兩列
    `manage_system-settings`／`manage_audit`（seed 9／77）各附 B-008 指針、到期即紅形）；self-test 防恆綠；ADR 0024 三項自證（合成正例／非共變判準／真檔暫改破壞性驗證寫進
    commit message）；接線＝`.githooks/pre-commit` 迴圈（base-web pin 或 seed 檔 staged 時）＋`tools/bootstrap.sh` 體檢；納冊 `TOOLS_PY`（docs-sync.py:2152）＋README 工具樹（Lint27 對賬）＋`reference/tools-cli.md` 重算。

## R9 前端落地要點（主線自拍逐項）

1. **NTree 語意定案**（naive-ui 2.44.1／treemate 0.3.11 原始碼）：`cascade` 未寫＝false⇒checkedKeys 恰等於逐一點過的鍵集、indeterminate 恆不出現、`check-strategy` 不生效。
   ⇒ endpoint modal **加 `cascade`**＋`check-strategy="child"`（群組級勾選真成立、checkedKeys 只回葉鍵）；menu modal **不加 cascade**（沿 rev4／upstream 形＝CDP 基準；
   勾子不補父、顯示樹幽靈父收縮⇒只勾子選單側欄不現——已知態、操作者須一併勾父目錄，與 rev4 同形）；button modal 扁平無父層、無此題。
2. **protected 預標鎖定載體**（rev4 零藍本）：三支讀端回 `{…, protected}[]`；前端由 protected 集注入 TreeOption `disabled: true`（視覺＋不可點、勾選保留；treemate cascade 跳過 disabled）
   ＋受控 `checked-keys`／`on-update:checked-keys` 攔截把 protected 鍵強制補回（雙保險）；後端整批拒為最終防線。`getMenuTree` wire 不動（四欄）。
3. **roleHome**：`home = shallowRef<string|null>(null)`＋NSelect `clearable`；候選＝getAllPages；`:value` 單向、選了即打 updateRoleHome（沿 rev4 同一 modal 兩種提交時機）；
   fetcher 走 rev5 wrapper（`fetchGetRoleHome(id)`／`fetchUpdateRoleHome({id, home})`）。
4. **menu-auth-modal 之 `fetchGetAllPages`／`fetchGetMenuTree`** 續走 barrel（一行不動、少一條 `原行:`）；其餘改引 rev5 wrapper。**button-auth-modal `init()` 改 `watch(visible)`**（R2-19）；
   `ButtonConfig.id` 復用為 code（rev4 :32-37 形、模板 `key-field="id"` 一行不動）。
5. **錯誤分支**＝`if (error) return;`（role-operate-drawer.vue:119-121 形）；三處 import／消費不帶回。
6. **endpoint-auth-modal**：葉鍵 `` `${path}|${method}` ``、群組鍵純 path、`leafMap` 反查不 split、`key` 欄（非 key-field="id"）。
7. **policy-archive 頁**：`<script setup lang="tsx">`、`useNaivePaginatedTable`＋`defaultTransform`（不用 `useTableOperate`）；8 欄（index／v0／dimension NTag／v1／archiveReason 原字面／archivedAt／archivedBy／operate）；
   restorable=false⇒同鍵 `restore` 鈕 `disabled` 無 Popconfirm；restore→`fetchRestorePolicy(id)`→`if (error) return;`→success toast→`getData()`（留當頁）；表頭只 refresh 鈕（無 default slot 覆寫⇒不觸 B-099 形）；
   `scroll-x` 自算＝Σ；`dimensionRecord` 照 rev4 兩處各寫（不抽新檔、不動新檔計數）；search 模組照 ip-rule-search.vue 範式、reset 補 `emit('search')`。
8. **i18n 插入點**：`page.manage.policyArchive` 整節插 `role` 之後（zh-cn/en-us 同位）；`page.manage.role.endpointAuth` 插 `buttonAuth` 後（zh-cn:687／en-us:691／app.d.ts:870 後）；
   `route['manage_policy-archive']` 照 `manage_ip-rule` 圈界塊形（zh-cn:372-376）；`archiveReason` 不映譯（沿 rev4、CDP 基準）。
9. **wrapper／typings**：`rev5-role-admin.ts` 6→18 支（+三維六支＋getAllButtons／getAllEndpoints＋roleHome 兩支＋回收桶兩支；`fetchGetAllPages` 不新建）；
   `rev5-role-admin.d.ts` 加型（契約見 contracts/）。
10. **B-099**：ip-rule/index.vue:245-255 照 menu/index.vue:355-375 形（外層 `<div v-show>` 保底＋內層 `v-if`）、條件用 `hasAuth('ipRule:add')` 不照抄 menu 的 `!showDeleted`。
11. **components.d.ts／service/api/index.ts 零 diff**（所需元件與 icon 全已註冊；wrapper 不入 barrel）。

## R10 治理面原料（U1 主線親做；插入點＝改前行號、由下而上改）

- 憲法 277 行／上限 350；預估 +11～12 行。插入點：①島 G 塊插 L138 後／L139 島 H header 前（+7：header＋G1～G6，rev5 形 `**G. …**`＋`- **G1 …**：`、勿用 rev4 二層縮排）
  ②L139 島 H header 括號回填（G 位保留句、入憲前句）③L140 H1 終態成員括號回填（第三態：「選單維／按鈕維授權寫端已兌現、v1.8.0 起非 vacuous；回收桶復原之選單／按鈕維分支因不可復原集擴列〔reason gate 五值〕結構性不可達」）
  ④§III 正文第五 bullet 插 L173 後（ADR 0052 四要素：判準檔頭 Generated／族＝產物四檔＋components.d.ts／禁手改不逐行標記不入用途名單／機器承載 `is_generated()`；**散文 bullet、絕不寫成表列**）
  ⑤§III.2 兩列插 L207 後（首欄不留空；產物四檔路徑留 (i) 列；(iv) 紀律欄寫「產物四檔授權沿 (i) 列」；(iii) 明寫 role-operate-drawer 同檔雙用途、endpoint-auth-modal 新增型不入名冊、三鈕不做 hasAuth gating）
  ⑥L211 表外宣告 2 改寫（「modal 治理需求自 v1.8.0 起由 MANAGE-PAGE-WIRING (iii) 承載、不另開 rev4 同名軌道」）⑦L263 版本行 1.8.0＋Last Amended ⑧L265 後插 1.8.0 log 一行（照 1.7.0 條目形；ADR 0047 引量三形；分級自證兩款 MINOR＋PATCH 隨批＋非 MAJOR 四款）。
- 島 G 六條落字差異（條文層）：G1 只凍結方向面＋「grant 面刻意例外」句；G2 刪「結構化明細」改「一因一鍵、明細載體活書級」；G3 不寫欄可空性、不提誰算 role_id；G4 純轉正；
  G5 寫固定鎖序、刪 rev4:L-075 類比句、鉤子句指刀 B、復原判定層級＝**U1 親決題①**（a 條文只寫「鎖內重驗＋reason gate＋同實例 NULL 誠實退化」、五腿留 ADR／b 寫「固定序五腿」字樣）；
  G6 候選措辭（謂詞式、鎖內現查、不寫列數、掛點恰兩處雙路徑、menu 維四列不在射程、非 vacuous＋變異自證、反轉＝MAJOR）。
  島 G header 括號形＝照島 F（列區間不列總數：「G1～G5 沿 rev4 已驗證形〔rev4:ADR 0048〕、G6 本刀新拍板；對偶 H2↔G3、H1/H5↔G5、H3↔G4」）＝**U1 親決題②**（寫不寫「六條」）。
- ADR 三支骨架：0053＝Amendment 四款一檔（照 ADR 0048 七段：款一島 G 六條 blockquote／款二 §III.2 兩列／款三 ADR 0052 條款順捎／款四 B-104 訂正＋訂正後完整 7 列矩陣）、
  front-matter `provenance` 含 ADR 0050（不 supersede）；0054＝封死（不變式／掛點恰兩處／射程外四列／非 vacuous 自證——明寫採 ADR 0024 精神但不主張屬其射程／翻案觸發條款／
  B-024③ 重評＝維持純 key／rev3 `3bfab71` 三缺陷三詞＋指針／後果＝B-024 改記殘餘）；0055＝五腿（照 ADR 0051 四段範式逐腿：判準／落點／機器證／使用者可見前後對照；
  腿↔寫端守門對照表）＋ADR 0050 §4 復核結論 B（觸發事實、結論、代價）＋「rev4 七步（鎖序動作軸）vs rev5 五腿（重驗腿軸）計數軸不同」註＋字面定案於 spec（`menu_revoke`／`button_revoke`、勿抄 brainstorm 暫定名）。
- 活書：§6 120/120 只 errata `:131`「六座」→「八座」（★一次補兩代：005 漏做；島 G 入憲 ADR（編號 0053）後果段註明）；§5 70/90 改 facade 11→12、reason gate 三值→五值、新增兩檔一句（+3～5 行）；
  §8 77/90 餘 13：`:276-283` 加 (iii)(iv) as-built、`:270-273` backend 樹「50 鍵」改指節形、「授權慣例」子節加三維治理／封死／回收桶／觸發面條目（併 no-escalation seam 條目以壓行）——落筆先算；
  arch_impact＝`["§5","§6","§8"]`（Lint06 雙向相等）。errata「六座」git 面 17 處、實改恰 1 處（其餘過去式／生成物／不可變 body）。

## R11 本輪查證對既有敘述的校正

1. brainstorm §0-1「三支 NOT-granted 測」早於 Q7 ⇒ **以 spec FR-058 兩支為準**（已同步 brainstorm 該句）。
2. brainstorm §2「`button_codes_of :694`」實為 `:678`；§9 行號為 2026-08-22 值、以本檔 R1 為準。
3. `sys_casbin_archive.rs:34-36` 失真句（承諾兩支具名 fn、從未存在）⇒ 甲案 doc-only 改寫（掃描面現況＝`archive_all_role_policies`＋`sys_menu.rs` 私有 `archive_policy_rows_of`）；
   `:12-17` 終態成員句之「restorePolicy 之選單／按鈕分支」⇒ 改寫為「updateRoleMenu／updateRoleButton 入域；updateRoleEndpoints 與 restorePolicy 不入域」（與憲法 H1 回填同語意、errata 紀律同批）。
4. 既有測 `is_non_restorable_reason_pins_three_member_set`（:348／:362）與 FR-030 衝突＝實作首日必改（非回歸）。
5. 測試基準 682 為實跑值（R8-11）；brainstorm §6「六座 14 處命中」已過時（現 17）。
6. spec FR-029 restorable 旗標已由 clarify 定為①②③④逐腿同判準（取代 brainstorm §4-④「兩半」）。

## R12 執行單元切分（tasks 的 phase 骨架建議；~13 支）

U1 憲法 Amendment v1.8.0＋ADR 三支（編號 0053～0055；★主線親做、user 親決兩題；硬閘：accepted 前不得動 base-web 既有檔）→
U2 menu 維（facade sys_casbin_policy.rs 新檔 TDD：diff／protected 整批拒／orphan skip／archive-move／入域＋NOT-granted／grant 面 reload 接線＋`RELOAD_CALL_FILES` 擴列＋enforce.rs doc 矩陣擴列；handler getRoleMenu／updateRoleMenu＋router＋contract）→
U3 button 維（all_button_codes＋orphan skip＋NOT-granted）→U4 endpoint 維＋結構性封死（policy_endpoints 斷環、候選把關、封死鎖內守門＋變異自證、B-105 seam harness 自拍）→
U5 支撐讀三支（getAllPages 顯示域穩定序／getAllButtons／getAllEndpoints）→U6 回收桶讀端（active_ids_by_codes＋protected 集＋ROUTES 四腿旗標、PageRes、enrich archivedBy、Option<i64> 守衛）→
U7 restorePolicy（五腿＋三態＋23505 收斂＋封死共用＋reload＋restore-during-delete 測＋reason gate 五值與既有測改）→U8 i18n 四處＋Lint24＋typecheck＋msg-keys 定稿→
U9 前端三 modal＋roleHome＋B-099（wrapper／typings 追加、cascade、protected 載體）→U10 policy-archive 頁＋產物四檔重算＋seed-view-gate（B-088）＋具名豁免→
U11 wire-schema 重抽＋新裁判＋全量閘（跨子庫兩段式）→U12 CDP 三方對照（排 schema-gate 後；L-050）→U13 收刀簿記（errata 六座→八座、活書 §5/§8、帳務、feature_close notes 承接關係）。
- 高風險共享檔序列鏈（同檔任務不標 [P]）：facade/sys_casbin_policy.rs（U2/U3/U4）、facade/sys_casbin_archive.rs（U2 reason 常數／U6／U7）、facade/sys_menu.rs（U3）、facade/sys_role.rs（U4 active_code_of／U6 批次）、
  handler/role.rs（U2～U5）、handler/policy_archive.rs（U6/U7）、router.rs＋tests/contract.rs（U2～U7 每支）、tests/authz_entrypoint_lint.rs（U2 擴列、U7 若名冊序變）、auth/enforce.rs doc（U2）、
  rev5-role-admin.ts／.d.ts（U9/U10）、locales 三檔（U8/U10）。
- 編排慣例：implementer=fable 1m xhigh、review=opus 1m xhigh（prompt 帶 ultrathink）、防呆六件套；Workflow＋Monitor 原子成對。
