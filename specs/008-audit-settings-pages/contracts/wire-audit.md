# Wire 契約 — Api.Audit（008；權威＝base-web `src/typings/api/rev5-audit.d.ts`）

> path×method 由 001 凍結 seed 五列預埋（零新政策列）；全走 `Protection::Policy`
> （seed 僅授 R_SUPER）；`envelope_exception: false`；信封＝`{data, code, msg}`、
> business error HTTP 200。命名空間＝`Api.Audit`（獨立、declaration merging 新檔；
> 004 起先例）。DTO 欄表＝[data-model.md](../data-model.md) §1～§3、此處不重複。

## 1. 端點

| # | method | path | req | res |
|---|---|---|---|---|
| 1 | GET | `/systemManage/getOperationLog` | `OperationLogSearchParams`（query） | `PageRes<OperationLog>` |
| 2 | GET | `/systemManage/getAccessLog` | `AccessLogSearchParams` | `PageRes<AccessLog>` |
| 3 | GET | `/systemManage/getLoginAttempt` | `LoginAttemptSearchParams` | `PageRes<LoginAttempt>` |
| 4 | GET | `/systemManage/getSessionEvent` | `SessionEventSearchParams` | `PageRes<SessionEvent>` |
| 5 | POST | `/systemManage/purgeAuditLog` | `PurgeAuditLogReq`（json body） | `PurgeAuditLogRes` |

分頁形＝`Common.PaginatingQueryRecord`／`PageRes<T>`＝`{current, size, total, records}`
（camelCase；空頁 `records: []`）。SearchParams 共通欄＝`current`／`size`／`timeFrom`／
`timeTo`（UTC RFC3339 字串、閉開 `[from,to)`）；全欄可缺席、空字串視同未設、
畸形不 4xx（寬鬆解析）。

## 2. 型別要點（typings 撰寫時之硬點）

- `LoginAttemptSearchParams.success`：`'true' | 'false'` 字串收斂（值域外＝未設）。
- `PurgeAuditTable`：`'operationLog' | 'accessLog' | 'loginAttempt' | 'sessionEvent'`。
- `PurgeAuditLogReq`：`{ table: PurgeAuditTable; beforeDays: number }`（≥30）；
  `PurgeAuditLogRes`：`{ deletedCount: number }`。
- id／entityId／operatorId／userId／httpStatus＝number（i64、2^53 fail-loud 守衛）；
  `success`＝boolean；payload 快照＝object|null（後端已打碼）。
- `OperationLog` 之 IP 欄組＝`realIp`／`peerIp`／`xForwardedFor`／`ipConfidence`（rev5
  欄名、無 operator 前綴——rev4 形不帶回）；`SessionEvent` 僅 `sourceIp: string | null`。

## 3. 錯誤碼（全數復用、零新碼）

| 碼 | 情境 | msg（i18n key） | data |
|---|---|---|---|
| `2222` | purge table 值域外 | `biz.audit.invalidTable` | null |
| `2222` | purge beforeDays < 30／缺席／畸形 | `biz.audit.purgeBelowFloor` | `{ "minDays": 30 }`（BizData；射程擴列 ADR＝U0） |
| `5003` | 非 R_SUPER 呼叫 | （既有授權拒因） | null |
| `8888` | 未認證 | （既有） | null |
| `0000` | 讀端恆成功（畸形過濾＝未設、顛倒＝空頁、零拒因） | — | PageRes |

## 4. 測試承載（coverage gate：每 route 必有 case）

- `tests/contract.rs`：五 case（`get-operation-log`／`get-access-log`／`get-login-attempt`／
  `get-session-event`／`purge-audit-log`）照 `get-system-settings` 形（免 DB oneshot、
  未認證→8888 信封＋HTTP 200）；query 參數零判別力＝既知限制（B-030 殘項、照記不擴）。
- `tests/wire_schema.rs`：`Api.Audit.*` 每 definition 正反例成對裁判（照 `Api.IpRule` 節
  形）；`PurgeAuditTable` 枚舉集斷言接後端白名單常數。
- handler 同檔真 DB 測：授權矩陣＋seed 五列對賬＋rev4 19 測形參照（research §R1）。
