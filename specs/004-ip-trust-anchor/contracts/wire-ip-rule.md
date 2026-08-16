# Contract — IP 規則管理五端點

> 權威序依憲法 §I.3：base-web 實碼 ＞ 官方 docs ＞ mock。本刀為 rev5 **新建**面，
> 無 upstream 既有呼叫端 ⇒ 契約以 rev4 已驗證形為藍本、由本檔凍結。
> 信封一律 `{data, code, msg}`、業務錯誤走 HTTP 200（例外僅 `4040`→404、`5003`→403）。
> 五條 route 皆為**政策保護**（casbin 政策列已在 001 凍結 seed，零新 seed）。

## 共用型

### `IpRuleRecord`（清單列；camelCase）

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | number | DB i64 → JSON number（沿 §I.3 預設＋2^53 fail-loud 守衛） |
| `wbipCidr` | string | 正規化後網段字面（主機位元已 mask） |
| `wbipType` | string | `allow`｜`deny` |
| `wbipMemo` | string \| null | 備註（★渲染端純文字插值，FR-038） |
| `order` | number \| null | 排序值；**不參與判定** |
| `deleted` | boolean | 由 `deleted_at.is_some()` 導出（回收桶辨識） |
| `createdAt` | string | RFC3339 帶 offset |
| `updatedAt` | string \| null | DB nullable |
| `createdBy` | string \| null | 操作者**帳號名**（批次 enrich、查無→null） |
| `updatedBy` | string \| null | 同上 |

★`deletedAt`／`deletedBy` **不上 wire**（`deleted` 布林已足辨識）。

---

## 1. `GET /systemManage/getIpRuleList`

**Query**（camelCase，全部可空）

| 參數 | 型 | 語意 |
|---|---|---|
| `current` | number | 頁碼；預設 1、下界 1 |
| `size` | number | 每頁筆數；預設 10、clamp `[1, 100]` |
| `wbipCidr` | string | **模糊**比對 |
| `wbipType` | string | 等值（`allow`｜`deny`） |
| `deleted` | string | 三態 `active`｜`deleted`｜`all`；**缺省＝`all`** |

**200**：`{ code: "0000", msg: "common.success", data: PageRes<IpRuleRecord> }`
（`PageRes` ＝ `{current, size, total, records}`，沿 §I.3 分頁形）

**錯誤**：`5003`（非超管）／`5000`（內部）

---

## 2. `POST /systemManage/addIpRule`

**Req**：`{ wbipCidr: string, wbipType: string, wbipMemo?: string, order?: number }`

**處理序**（★次序即契約）

1. 類型二值守門 → 不符 `2222 biz.ipRule.invalidRuleType`（**寫前拒、零寫入**）
2. 網段解析＋主機位元正規化 → 失敗 `2222 biz.ipRule.invalidCidr`（**寫前拒、零寫入**）
3. **防自鎖**：以「變更後規則集」對操作者當下真實來源跑同一判定純函式 → 判 Deny 即
   `2222 biz.ipRule.selfLock`（**零落庫、零重載**）
4. 落庫（與操作稽核列同一交易）→ 唯一性衝突（partial unique）映 `2222 biz.ipRule.conflict`
   （★MUST NOT 為伺服器錯誤）
5. 成功後 → 重載判定面＋發門鈴

**200**：`{ code: "0000", msg: "common.success", data: null }`

---

## 3. `POST /systemManage/updateIpRule`

**Req**：`{ id: number, wbipCidr: string, wbipType: string, wbipMemo?: string, order?: number }`

處理序同 `addIpRule`，差異：防自鎖的「變更後規則集」＝**移除舊值＋加入新值**後的集合；
標的不存在或已軟刪 → `2222 biz.ipRule.notFound`。

---

## 4. `DELETE /systemManage/deleteIpRule`

**Req**：`{ id: number }`

軟刪（`deleted_at`／`deleted_by` **成對**寫）。防自鎖的「變更後規則集」＝**移除該列**後的集合
（★刪 allow 規則可能使操作者失去放行 ⇒ 刪除同樣要過自鎖檢查）。
標的不存在或已在回收桶 → `2222 biz.ipRule.notFound`。成功後重載＋門鈴。

---

## 5. `POST /systemManage/restoreIpRule`

**Req**：`{ id: number }`

復原（`deleted_at`／`deleted_by` 成對清空）。防自鎖的「變更後規則集」＝**加入該列**後的集合。
標的不存在或非回收桶狀態 → `2222 biz.ipRule.notFound`；復原後與現有有效列衝突 →
`2222 biz.ipRule.conflict`。成功後重載＋門鈴。

---

## 契約測試 case（覆蓋閘要求每條 route 至少一案）

| case_key | 斷言重點 |
|---|---|
| `get-ip-rule-list` | 分頁形＋三 filter＋審計欄上 wire＋`deleted` 導出 |
| `add-ip-rule` | 正規化落庫＋衝突映業務碼＋自鎖拒寫 |
| `update-ip-rule` | 標的不存在＋自鎖以「移除舊＋加入新」判 |
| `delete-ip-rule` | 軟刪成對寫＋刪 allow 亦過自鎖 |
| `restore-ip-rule` | 復原成對清空＋復原衝突 |
