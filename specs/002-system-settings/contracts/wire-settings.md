# Wire 契約 — 002-system-settings

消費面＝憲法 §I.3 凍結信封＋13 碼矩陣（零新增碼面）；型權威＝base-web
`src/typings/api/rev5-settings.d.ts`（本刀新檔）；機器裁判＝wire-schema 快照
（`rust-api/server/tests/fixtures/wire-schema.json`、draft-07）。DTO 欄型詳
data-model §1/§2（本檔不重複）。

## §1 讀端 `GET /systemManage/getSystemSettings`

- 授權：Policy（R_SUPER only；casbin seed 政策列 66）。
- 請求：無 body、無 query（不認識的 header 一律忽略——憲法 §II #1）。
- 成功：HTTP 200、`{data: SettingItem[16], code:"0000", msg:"common.success"}`；
  `settingKey` 升冪穩定序；僅未刪列。
- 錯誤：見 §3 矩陣（未認證 8888／越權 5003）。

## §2 寫端 `POST /systemManage/updateSystemSetting`

- 授權：Policy（R_SUPER only；casbin seed 政策列 67；act＝POST）。
- 請求：`UpdateSystemSettingReq`（camelCase JSON body；三態語意＝data-model §8）。
- 成功：HTTP 200、`{data:null, code:"0000", msg:"common.success"}`；落庫效果＝
  settingValue canonical 形＋updated_at/updated_by 成對＋description 依三態。
- 錯誤矩陣（全部零寫入）：

| 情境 | 碼 | msg key | HTTP |
|---|---|---|---|
| settingValue 型別不符／超範圍／enum 外值 | 2222 | biz.systemSettings.invalidValue | 200 |
| settingValue 顯式 null（NOT NULL 欄清空） | 2222 | biz.systemSettings.invalidValue | 200 |
| settingKey 不在 registry 宣告集（含軟刪防禦態——判定落點＝facade filter） | 2222 | biz.systemSettings.notFound | 200 |
| settingKey 或 settingValue 欄缺席／型別非 string／JSON 反序列化失敗 | 2222 | biz.systemSettings.invalidValue | 200 |
| 越權（政策無授，R_ADMIN 組合） | 5003 | system.forbidden | 403 |
| 未認證（無 `Authorization` 標頭／非 Bearer 形／token 不在 dev 表） | 8888 | auth.session.reLogin | 200 |
| 庫中 setting_type 未知型 | 5000 | system.internal | 200 |

## §3 碼面斷言（contract test 消費）

1. 本刀可發碼恰六：0000／2222／4040（router fallback）／5003／5000／8888。
2. 1000／3333／7777＋4 保留碼（7778/8889/9998/9999）＝AppError 無變體、構造層不可
   發出（cargo 型別層保證＋contract 斷言雙錨）。
3. 信封三欄宣告序 `data→code→msg`；code 恆 string；錯誤 `data:null` 不省略；
   business error 一律 HTTP 200（例外僅 4040→404、5003→403）。
4. msg 恆穩定 i18n key（後端不在地化）；本刀 key 名冊＝data-model §6（Lint24 閉環：
   後端掃描面 keys ⊆ zh-tw.ts `backend.*` 鍵集）。
5. 信封例外恰二：`/health`（plain text "ok"）、`/metrics`（Prometheus exposition）。

## §4 快照與覆蓋閘契約（K1-25）

- 快照產製：`python3 tools/wire-schema.py extract`（base-web 容器內 npx 抽 typings、
  原子替換寫入；需 stack 在跑）；drift 閘＝`check`（重抽 byte 比對；pre-commit
  `--staged-gate` 收窄：staged base-web gitlink 區間零 typings 變動即跳過）。
- 受審 definitions（本刀新增）：`Api.SystemManage.SystemSetting`（SettingItem 序列化
  輸出必過）＋`Api.SystemManage.UpdateSystemSettingReq`（service 送出形錨定）。
- 覆蓋閘：`server/tests/contract.rs` registry 與 `router::ROUTES` 之 case_key **雙向**
  比對——每條 route 必有 case（缺即紅指名）、每個 case 必對 route（殭屍即紅指名）。
  B12 case 集恰四：health／metrics／get-system-settings／update-system-setting。

## §5 前端接線層契約（ADR 0018）

- `rev5-settings.d.ts`：declaration merging 併入 `Api.SystemManage`（不改既有
  system-manage.d.ts）；新檔＝fork-delta 新增型、檔頭一行 `[rev5-inline …+]` 標記。
- `rev5-settings.ts`：直接路徑 import request 實例（不經 barrel index.ts）；
  `fetchGetSystemSettings()`＋`fetchUpdateSystemSetting(req)` 兩函式、型別完備
  （未來 view 刀接上即用）。
