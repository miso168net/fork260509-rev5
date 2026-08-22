# Contract — 授權回收桶兩端點（getArchivedPolicies／restorePolicy）

> 權威序依憲法 §I.3。新頁 policy-archive 之 wire 型落 rev5 新命名空間 `Api.PolicyArchive`（追加於
> `rev5-role-admin.d.ts`；fetcher 追加於 `rev5-role-admin.ts`）。兩條 route 皆 `Protection::Policy`、
> seed R_SUPER（70／71、protected=TRUE）、零新 seed；頁級門＝menu 維政策列 72。分頁形 `PageRes<T>`。

## 共用型

### `ArchivedPolicyDimension`＝`'menu' | 'button' | 'endpoint'`

### `ArchivedPolicy`（列表列；camelCase；恰 15 欄）

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | number | 歸檔列 id（restore 請求鍵；i64→number 2^53 守衛） |
| `ptype` | string | 恆 `'p'` |
| `v0` | string | 來源角色代碼 |
| `v1` | string | 授權標的（route_name／按鈕碼／路徑） |
| `v2` | string | 維度標記或 HTTP 方法 |
| `v3`／`v4`／`v5` | string | 原樣過境（空字串） |
| `archiveReason` | string | 六值封閉詞彙原字面（不映譯） |
| `archivedAt` | string | RFC3339 帶 offset |
| `archivedBy` | string \| null | ★操作者帳號名（批次 enrich、查無→null；rev5 列表慣例，rev4 為 uid number） |
| `roleId` | number \| null | 來源角色識別（`Option<i64>` 守衛序列化；NULL 誠實 null） |
| `restorable` | boolean | 後端派生：①reason ∧ ②同實例 ∧ ③封死不擋 ∧ ④端點在冊（⑤免算）；選單／按鈕維恆 false |
| `dimension` | `ArchivedPolicyDimension` | 由 `v2` 推導 |

### `ArchivedPolicyListQuery`＝`{ current?: number, size?: number, roleCode?: string | null, dimension?: ArchivedPolicyDimension | null }`

### `ArchivedPolicyListRes`＝`PageRes<ArchivedPolicy>`

## 1. `GET /systemManage/getArchivedPolicies`

- Query：分頁（`current` 預設 1、上界 `MAX_CURRENT`；`size` 預設 10、clamp [1,100]）＋`roleCode?`（等值濾 `v0`、空字串忽略）＋`dimension?`（endpoint＝方法白名單；未知值靜默不濾）。
- 200 `data: ArchivedPolicyList`；穩定排序 `archived_at DESC, id DESC`。

## 2. `POST /systemManage/restorePolicy`

- Body：`{ id: number }`（歸檔列 id；DTO 帶 Default、空 body→id 0→NotRestorable）。
- 鎖序（不入選單序列化域）：歸檔列 FOR UPDATE→①reason gate→活角色列 FOR UPDATE（by `v0`）→②同實例→③封死→④端點在冊→⑤停用不擋→回灌／刪歸檔／稽核→commit。
- 三態：Applied→200 `data: null`（判定面同步）；NoOp（標的已在現役）→200 `data: null`（歸檔列仍消費移除、不同步）；NotRestorable→2222 `biz.policy.notRestorable`。
- ★前端不可區分 Applied／NoOp（沿 rev4、已知態）；restorable=false 列 UI 停用、後端為最終防線。

## 授權態矩陣（contract 測）

Super 兩支通（restore 以合成 fixture）；Admin／User 皆 5003。
