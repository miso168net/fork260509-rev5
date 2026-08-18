# Quickstart — 005 role＋menu 管理 CRUD 寫端（驗證指南）

> Phase 1 產物：可跑的端到端驗證場景（前置→建置→逐面驗證→閘檢查）。細節權威＝
> [data-model.md](data-model.md)＋contracts 三檔（wire-role-admin／wire-menu-admin／msg-keys）；本檔不重複其內容、只給驗證動線。
> 帳密與端口＝CLAUDE.md §7（dev 帳號 Super／Admin、22080/22079；rev4 對照 42080）。

## 0. 前置

- dev stack 起（compose up --wait）；rust build/test 一律容器內、全程 serial。
- 憲法 v1.7.0 已 accepted（U1 硬閘）——`git log` 可見 Amendment commit；
  `docs-sync.py check` 全綠。
- 零 migration 斷言：`ls rust-api/migration/src/` 仍恰 `lib.rs main.rs m001* m002*`。

## 1. 後端契約面（curl；token=Super 登入取得）

逐支對 [wire-role-admin](contracts/wire-role-admin.md)／[wire-menu-admin](contracts/wire-menu-admin.md)：

1. `getRoleList`：分頁回 seed 3 列、`roleMemo` 欄在、`id ASC`。
2. `getAllRoles`：3 項、無 memo 欄。
3. `addRole`：合形制成功；重複 code／壞形制→2222＋對應鍵（msg-keys）。
4. `updateRole`：改名成功；帶 `roleCode` 變更→2222 codeImmutable；停用 R_SUPER→2222
   superCannotDisable；全 None→no-op（時戳不動）。
5. `deleteRole`：seed 角色→seededProtected；自建零掛載角色→成功、歸檔表可查
   `role_soft_delete` 列、★判定面零同步（metrics 不動）。
6. `batchDeleteRole`：含一違規項→整批拒、零變更。
7. `getMenuList/v2`：治理域樹形分頁（含停用列）、`menuMemo` 在。
8. `getMenuTree`：治理域輕量樹。
9. `addMenu`：合法成功（側欄不現＝已知態③）；重複 routeName→routeNameExists；
   常量掛非常量父→constantParent；成環改父→cycleDetected。
10. `updateMenu`：改 routeName→routeNameImmutable；buttons 移除絕版碼→歸檔
    `menu_button_removed`＋`casbin_reload_total{ok}` +1。
11. `deleteMenu`：有未刪子項→hasChildren；protected 列→protectedMenu；成功→
    menu 維跨角色＋獨有碼歸檔（皆 `menu_soft_delete`）＋reload +1。
12. `getDeletedMenus`／`restoreMenu`：toggle 資料源；復原撞活性同鍵→restoreConflict；
    成功→原 status 保留、零回灌（歸檔列仍在、casbin 零新列）。
13. 授權態：Admin token 打任一寫端→5003；打 getRoleList→200。
14. 上下文缺席形（若可構造）→5000 拒寫。

## 2. 判定面同步驗證（US4）

- 測試面為主（cargo test 四支：失敗注入 keep-last-good／裸呼轉紅負向自證／觸發條件特性
  鎖定／移除面端到端 in-memory 雙斷言）。
- 手動 smoke：deleteMenu 前後查 `casbin_reload_total`；kill redis 不影響（同步不涉 redis）；
  注入面僅測試可構造——生產面驗「成功路徑 metrics ok +1」即可。

## 3. 序列化域機器證

- cargo test：兩併發寫端（deleteRole × deleteMenu）→ 後者在 pg_locks 出現 advisory
  NOT-granted 等待列（classid/objid 拆讀斷言）；完成後兩者效果皆完整（無漏歸檔／無孤兒影本）。

## 4. 前端與 CDP 三方對照（22080 vs 42080）

1. role 頁：列表真資料（vs rev4 逐項）／搜尋／新增編輯 drawer（含 memo textarea＋
   placeholder）／刪除批刪確認流。
2. menu 頁：樹表／新增編輯 modal（父選擇器＝getMenuTree、★無 fetchGetAllRoles 呼叫——
   DevTools network 驗證）／buttons 編輯／toggle 回收桶／復原。
3. ★已知態三組逐項驗「現狀形」（煙測判準）：role 頁兩鈕點開＝假資料 modal（非 404）；
   policy-archive 側欄項零反應；新建選單側欄不現、管理列表可見。
4. i18n：兩語切換零 raw key；後端拒因經 $t 呈現人話。

## 5. 收刀閘（全量）

- 容器內 cargo test 全量 serial rc=0（≥512＋本刀淨增）；`docs-sync.py check` 0 錯誤；
  schema-gate 三閘綠（含 gate2 對三表零殘列＋seq setval 核）；wire-schema 快照 diff 符預期；
  fork-delta-lint 綠（修改型僅 plan 所列檔集；兩顆授權 modal 零 diff）；view-render-guard 綠；
  `ROUTES_COUNT=38` 與 reference/routes 真表對齊（generate 後）。
