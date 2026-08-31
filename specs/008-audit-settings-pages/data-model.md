# Data Model — 008 稽核中心與系統設定頁（Phase 1）

**零 migration、零 seed 變更**：四稽核源表、索引（含兩支 pg_trgm GIN）、casbin 政策五列＋
menu 二列、system_settings 16 鍵皆 001/002 既在。本檔只定義**讀模型**（表→wire DTO 對映）
與 purge 請求模型；欄型權威＝`rev5-audit.d.ts`（憲法 §I.1）、後端 schema 權威＝m001。

## 1. 四源讀模型（表欄 → DTO 欄；全 DTO `#[serde(rename_all = "camelCase")]`、id 走 2^53 守衛）

### 1.1 OperationLogDto ← sys_operation_log（14 欄；★rev5 欄名無 operator_ 前綴）

| DTO 欄 | 型（wire） | 來源欄 | 備註 |
|---|---|---|---|
| id | number | id | |
| createTime | string(RFC3339) | created_at | |
| operatorId | number\|null | created_by | |
| operatorName | string\|null | —（enrich） | user_names_by_ids 批查 |
| operation | string | operation | |
| entityTable | string | entity_table | |
| entityId | number\|null | entity_id | |
| payloadBefore / payloadAfter | object\|null | payload_before/after | ★經 mask_pii_payload（D3）後上 wire |
| realIp | string\|null | real_ip | INET→host 字串（rev4 op-log 為 operatorRealIp、不帶回） |
| peerIp | string\|null | peer_ip | wire-only、UI 不渲染 |
| xForwardedFor | string\|null | x_forwarded_for | UI 渲染（ADR 0076） |
| ipConfidence | string\|null | ip_confidence | wire-only |
| region | string\|null | region | wire-only（rev5 值恆 NULL、D10） |
| traceId | string\|null | trace_id | UI 渲染、值恆「-」（D10） |

### 1.2 AccessLogDto ← sys_access_log（12 欄）

id｜createTime｜operatorId(number、created_by **NOT NULL**)｜operatorName(enrich)｜
httpMethod｜httpPath｜httpStatus(number)｜realIp(string NN)｜peerIp\|null｜
xForwardedFor\|null（UI 渲染）｜ipConfidence\|null（wire-only）｜region\|null（UI 渲染、恆「-」）｜
traceId\|null（UI 渲染）。★表現況零寫入者（B-016）＝讀端恆空頁、已知態。

### 1.3 LoginAttemptDto ← sys_login_attempt（11 欄）

id｜createTime｜attemptedUserName｜success(bool)｜realIp(string NN)｜peerIp\|null｜
xForwardedFor\|null（UI 渲染）｜ipConfidence\|null（wire-only）｜region\|null（UI 渲染）｜
traceId\|null（UI 渲染）。★無操作者維（created_by 恆 NULL、不上 wire、無 enrich）。

### 1.4 SessionEventDto ← session_event（8 欄；照 rev4 形）

id｜createTime｜userId(number NN)｜userName(enrich by user_id)｜sid｜eventType｜
reason\|null｜operatorId(number\|null＝created_by)｜operatorName(enrich)｜
sourceIp\|null（★單欄 varchar(45) 字串照回、非信任錨四欄組；無 XFF 欄）。

## 2. 過濾參數模型（query、全 `Option<String>` 寬鬆；共通＝timeFrom/timeTo/current/size）

| 讀端 | 專屬過濾欄（語意） |
|---|---|
| getOperationLog | entityTable（等值）、operation（等值）、operatorId／operatorName（id 優先；名→含軟刪同名 IN） |
| getAccessLog | httpMethod（等值）、httpStatus（等值、trim-parse）、httpPath（ILIKE 含、萬用字元字面化＋ESCAPE、走 trgm）、operatorId／operatorName |
| getLoginAttempt | userName（attempted_user_name ILIKE）、success（嚴格 'true'/'false'、值域外＝未設）、realIp（★精確等值 /32、/128；FR-B08） |
| getSessionEvent | userId／userName（人員過濾）、eventType（等值）、reason（等值） |

正規化：current 預設 1 下界 1；size 預設 10 clamp [1,100]；時間 RFC3339 閉開 [from,to)、
畸形＝未設、顛倒＝空頁；排序恆 `created_at DESC, id DESC`。

## 3. 清理模型

- `PurgeAuditLogReq { table: string, beforeDays: number|數字字串（寬鬆、畸形→缺席） }`
- table 白名單（wire 枚舉四值）：`operationLog`｜`accessLog`｜`loginAttempt`｜`sessionEvent`
- 守門固定序：①白名單（違＝2222 `biz.audit.invalidTable`）→②beforeDays ≥ PURGE_MIN_DAYS=30
  （違＝2222 `biz.audit.purgeBelowFloor`＋BizData `{minDays:30}`）→③單交易：水平線
  DELETE（op-log 版帶 `operation <> 'PURGE'` 豁免）＋同交易 PURGE 自記
  （payload_after=`{table, before_days, deleted_count}`）
- `PurgeAuditLogRes { deletedCount: number }`
- 不變式：零部分成功（自記失敗→整筆回滾、fault-injection 釘住＝FR-C04）；
  PURGE_MIN_DAYS=30＝B-016 逐表門檻下限鏡像。

## 4. SystemSetting（既有模型、純消費）

`Api.SystemManage.SystemSetting { settingKey, settingValue, settingType, description? }`
（16 鍵固定集、settingKey 升冪、非分頁）＋`UpdateSystemSettingReq`（三態 description）——
`rev5-settings.d.ts` 既在、本刀零改動。前端分組鍵前綴：`password_*`→密碼策略、
`login_throttle_*`→帳號登入、`ip_*`→IP 源登入、其餘→工作階段；控件由 settingType 驅動。

## 5. 狀態轉移

無（四源 append-only 唯讀＋水平線刪除；settings 逐鍵覆寫無狀態機）。
