# Contract — 三維授權治理九端點（三維讀寫 6＋支撐讀 3）

> 權威序依憲法 §I.3。三顆授權 modal 為 upstream 既有 demo 面，wire 型依拍板落 rev5 獨立命名空間
> `Api.RoleAdmin`（追加於 `base-web/src/typings/api/rev5-role-admin.d.ts`；fetcher 追加於
> `base-web/src/service/api/rev5-role-admin.ts`、不入 barrel）。信封一律 `{data, code, msg}`、業務錯誤
> HTTP 200（例外僅 4040→404、5003→403）。九條 route 皆 `Protection::Policy`、seed 全 R_SUPER（32／33／
> 52～57／26）、零新 seed。角色鍵一律 `id`（rev4 `roleId` 不帶回）；拒因純 key（無明細）。

## 共用型

### `Endpoint`＝`{ path: string, method: string }`（端點維雙鍵；讀端項再加 `protected`）

### 三維讀端項（每項帶 `protected: boolean`＝受保護、前端預標鎖定）

- `RoleMenuItem`＝`{ id: number, protected: boolean }`（`id`＝選單 id，治理域映射自 `route_name`）
- `RoleButtonItem`＝`{ code: string, protected: boolean }`
- `RoleEndpointItem`＝`{ path: string, method: string, protected: boolean }`

### 三維寫端回應 `GrantResult<T>`＝`{ revoked: number, granted: number, effective: T[] }`

`effective`＝orphan skip 後實際生效之期望全集（menu→`number[]`／button→`string[]`／endpoint→`Endpoint[]`）。

## 1. `GET /systemManage/getRoleMenu`

- Query：`id`（角色 id）。
- 200 `data: RoleMenuItem[]`（現況選單維授權；治理域反向映射、歷史孤兒 route_name 不反射）；角色不存在／已刪→2222 `biz.role.notFound`。

## 2. `POST /systemManage/updateRoleMenu`

- Body：`{ id: number, menuIds: number[] }`（期望全集；含 protected 項須原樣帶回）。
- 全量替換；候選＝治理域（未刪含停用）；界外 id 靜默略過。撤銷集觸及 protected→2222 `biz.role.protectedRevoke`、零變更。
- 200 `data: GrantResult<number>`；Applied 即判定面同步（含空 diff）。入選單序列化域。

## 3. `GET /systemManage/getRoleButton`

- Query：`id`。200 `data: RoleButtonItem[]`。

## 4. `POST /systemManage/updateRoleButton`

- Body：`{ id: number, buttons: string[] }`。候選＝治理域 buttons 聯集；界外碼靜默略過。protected 同上。
- 200 `data: GrantResult<string>`。入選單序列化域。

## 5. `GET /systemManage/getRoleEndpoints`

- Query：`id`。200 `data: RoleEndpointItem[]`（以 HTTP 方法白名單辨識端點維列）。

## 6. `POST /systemManage/updateRoleEndpoints`

- Body：`{ id: number, endpoints: Endpoint[] }`。候選＝路由註冊表受政策管制端點全集（路徑×方法）；界外（含非 GET／POST／DELETE）靜默略過。
- 守門固定序：protected 整批拒（`biz.role.protectedRevoke`）→★結構性封死：標的角色非 R_SUPER 且新授集含 protected 端點政策→2222 `biz.role.protectedGrant`、零變更。
- 200 `data: GrantResult<Endpoint>`。**不入**選單序列化域（以角色列鎖序列化）。

## 7. `GET /systemManage/getAllPages`

- 200 `data: string[]`（顯示域 route_name 全集；穩定序 `(order, id)`）。★protected=FALSE 之唯一一支（seed 26）；menu 管理頁 page／activeMenu 下拉與 roleHome 候選共用。

## 8. `GET /systemManage/getAllButtons`

- 200 `data: string[]`（治理域 buttons 聯集、去重、首見序）。

## 9. `GET /systemManage/getAllEndpoints`

- 200 `data: Endpoint[]`（路由註冊表 `Protection::Policy` 全集；照註冊序；回應集量隨註冊表成長——2026-08-23 量測 24→本刀後 35）。

## 授權態矩陣（contract 測）

Super 九支全通；Admin／User 九支皆 5003（seed 全 R_SUPER）。三支寫端空 body→預設形→`biz.role.notFound`（2222）。
