# Contract — role 管理八端點（CRUD 6＋roleHome 2）

> 權威序依憲法 §I.3。role 頁為 upstream 既有 demo 面，但 wire 型別依拍板開 rev5 獨立命名
> 空間（`createdBy` 帳號名 enrich、`deleted` 導出布林——004 慣例）、demo 頁欄定義同批改；
> 契約由本檔凍結。信封一律 `{data, code, msg}`、業務錯誤 HTTP 200（例外僅 4040→404、
> 5003→403）。八條 route 皆政策保護（seed 已在、零新 seed）。

## 共用型

### `RoleRecord`（列表列；camelCase）

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | number | i64→number（2^53 fail-loud 守衛沿 004） |
| `roleCode` | string | 不可變；`^[A-Za-z0-9_]{1,64}$` |
| `roleName` | string | |
| `roleDesc` | string \| null | |
| `roleMemo` | string \| null | ★getRoleList 帶（R_ADMIN 可見）；getAllRoles 不帶 |
| `roleHome` | string \| null | 路由名 |
| `status` | string | `'1'`（啟用）\|`'2'`（停用）——upstream 慣例字串枚舉 |
| `createdAt` | string | RFC3339 帶 offset |
| `updatedAt` | string \| null | |
| `createdBy` | string \| null | 操作者帳號名（批次 enrich、查無→null） |
| `updatedBy` | string \| null | |

★軟刪欄不上 wire（角色刪除單向、無回收桶讀端）。

### `AllRole`（下拉項）

`{ id: number, roleCode: string, roleName: string }`——★無 memo、無審計欄。

## 1. `GET /systemManage/getRoleList`

- Query：`current`／`size`（分頁）＋`roleName?`／`roleCode?`（模糊）＋`status?`（等值）。
- 200 `data: PageRes<RoleRecord>`（`{records, current, size, total}`）；穩定排序 `id ASC`。
- 授權：R_SUPER＋R_ADMIN（seed 12/13）。

## 2. `GET /systemManage/getAllRoles`

- 200 `data: AllRole[]`——僅活性且啟用；`id ASC`。
- 授權：三角色（seed 14/15/16）。★本刀 as-shipped 零 UI 消費者（刀 B 進場；已知態）。

## 3. `POST /systemManage/addRole`

- Body：`{roleCode, roleName, roleDesc?, roleMemo?, roleHome?, status?}`。
- 守門：code 形制→活性唯一。成功 `data: null`；新角色零授權（兩步流）。
- 拒：2222＋`biz.role.*`（形制／重複）。

## 4. `POST /systemManage/updateRole`

- Body：`{id, roleName?, roleDesc?, roleMemo?, roleHome?, status?}`＋★`roleCode` 出現＝顯式拒。
- 三態語意（ADR 0023）；全 None 提前 no-op；停用過雙護欄（自身所屬拒／R_SUPER 恆禁）。

## 5. `DELETE /systemManage/deleteRole`

- Body：`{id}`。三層守門固定序 seeded→in-use→self-role；通過＝軟刪＋全三維歸檔
  （`role_soft_delete`）＋稽核；★零判定面同步。進序列化域。

## 6. `DELETE /systemManage/batchDeleteRole`

- Body：`{ids: number[]}`。id 升冪逐項全套守門、任一違規整批拒（no-partial）、單 txn。
  空陣列＝照 rev4 as-built（plan 期查定：提前 no-op 或形制拒，tasks 單元對 rev4 碼定案）。

## 7. `GET /systemManage/getRoleHome`

- Query：`id`。200 `data: { home: string | null }`。

## 8. `POST /systemManage/updateRoleHome`

- Body：`{id, home}`。落庫不驗可見樹一致性（讀端兜底 `resolve_home` 既有）；稽核。
