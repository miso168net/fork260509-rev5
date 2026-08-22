# Contract — menu 管理八端點（CRUD 7＋getMenuTree）

> 同 wire-role-admin 權威序與信封慣例。★`getMenuList/v2` 字面帶 `/v2`（逐字對齊 seed 25）。
> 全部治理域語意（未刪含停用）；顯示域（getUserRoutes 家族）不在本刀。

## 共用型

### `MenuRecord`（樹列；camelCase）

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | number | |
| `parentId` | number | 頂層＝0（DB NULL↔wire 0 映射照 rev4） |
| `menuType` | string | `'1'` 目錄／`'2'` 選單；不可變 |
| `menuName` | string | |
| `routeName` | string | 不可變；活性唯一 |
| `routePath` | string \| null | |
| `component` | string \| null | |
| `status` | string | `'1'`/`'2'` |
| `hideInMenu` | boolean \| null | |
| `keepAlive` | boolean \| null | |
| `multiTab` | boolean \| null | ★2026-08-19 補漏列（user 拍板：可寫、照 rev4 as-built——data-model §1.2 本列於「一般可編欄」、本表原缺席屬 SDD 期缺漏、實作期查獲） |
| `constant` | boolean \| null | 可寫；父鏈常量性守門 |
| `protected` | boolean | 受保護（刪除守門第一腿；本刀唯讀呈現） |
| `order` | number \| null | |
| `icon`／`iconType`／`i18nKey`／`href`／`activeMenu`／`fixedIndexInTab` | 各原型 | 一般可編欄 |
| `query` | object[] \| null | jsonb 直傳 |
| `buttons` | `{code,desc}[]` \| null | jsonb 直傳；變更觸發絕版歸檔判定 |
| `menuMemo` | string \| null | 列表帶 |
| `deleted` | boolean | `deleted_at.is_some()` 導出（回收桶辨識） |
| `createdAt`／`updatedAt`／`createdBy`／`updatedBy` | 同 RoleRecord | enrich 形 |
| `children` | MenuRecord[] \| 缺席 | 樹形組裝（getMenuList/v2） |

### `MenuTree`（父選擇器輕量樹）

`{ id: number, label: string, pId: number, children?: MenuTree[] }`（照 rev4 形；treeSelect 消費）。

## 1. `GET /systemManage/getMenuList/v2`

- Query：`current`／`size`（★分頁以頂層計；size clamp 常數＝rev4 as-built [1,100]、與前端
  hook 無參呼叫形對齊——tasks 期釘死）。
- 200 `data: PageRes<MenuRecord>`（records＝頂層列＋全深子樹）。治理域。

## 2. `GET /systemManage/getMenuTree`

- 200 `data: MenuTree[]`——治理域全樹（未刪含停用、不含已刪）。父選擇器消費。

## 3. `POST /systemManage/addMenu`

- Body：MenuRecord 可寫欄集（無 id／deleted／審計欄）。
- 守門序：parent 驗證（存在未刪、停用不擋、頂層豁免）→防環→routeName 活性唯一（雙層）→
  constant 父鏈→形制。零 casbin 寫。

## 4. `POST /systemManage/updateMenu`

- Body：`{id, ...三態欄}`；`routeName`／`menuType` ★**出現即拒**（值不比對、等值亦拒——
  與 wire-role-admin §4 roleCode 同式；as-built 措辭訂正 2026-08-22）。
- buttons 移除且絕版（未刪含停用聯集）⇒ 絕版歸檔（`menu_button_removed`）＋判定面同步。

## 5. `DELETE /systemManage/deleteMenu`

- Body：`{id}`。守門固定序：protected→存在未刪子項（不論啟停）。通過＝軟刪＋menu 維跨角色
  ＋獨有碼歸檔（皆 `menu_soft_delete`）＋判定面同步＋稽核。

## 6. `DELETE /systemManage/batchDeleteMenu`

- Body：`{ids}`。child-first 拓撲序、逐項全套守門、整批拒、單 txn＋一次收尾同步。
- ★空陣列＝提前 no-op 成功（零副作用、零稽核、不取域鎖——照 wire-role-admin §6 之
  rev4 as-built 查定、兩域同式；原表漏載 2026-08-22 補）。

## 7. `GET /systemManage/getDeletedMenus`

- Query：分頁。200 `data: PageRes<MenuRecord>`（已刪集合；穩定排序 `deleted_at DESC, id DESC`）。
  ★不帶 `restorable` 旗標——選單復原無 reason gate 概念（那屬授權歸檔）、恆可嘗試復原，
  復原守門（同鍵衝突／父未刪）即唯一權威；照 rev4 toggle 形。

## 8. `POST /systemManage/restoreMenu`

- Body：`{id}`。域內鎖列重驗（已刪存在→同鍵活性衝突〔23505 兜底同一拒因〕→父未刪→
  ★常量父鏈〔標的是常量時驗全祖先常量性、違即 `constantParent`——B-095 補刀、user 拍板
  2026-08-22：閉合軟刪常量後代繞道窗；非常量標的零驗〕）→
  成對清空軟刪欄＋原 status 保留；零回灌、零同步；稽核。
