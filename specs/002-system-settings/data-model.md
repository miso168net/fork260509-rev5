# Data Model — 002-system-settings（Phase 1）

轉錄自 spec（Clarify Q1~Q3 已定案）＋research R4/R8；本檔凍結後＝B12 資料面與 wire 型
唯一權威（spec 敘事讓位）。零 migration：system_settings 表＋16 鍵 seed 已隨 001 基線
在庫（`docs/generated/reference/schema.md` system_settings 節＝現況真表）。

## §1 wire DTO — SettingItem（讀端列型）

`#[serde(rename_all = "camelCase")]`；審計欄不上 wire（Model→DTO 映射僅取四欄）。

| wire 欄 | 型 | 語意 |
|---|---|---|
| settingKey | string | PK、不可改 |
| settingValue | string | 值（字串載體；number 型亦字串承載） |
| settingType | string | `"number"`／`"enum:on,off"`（驅動前端 render 與後端驗證） |
| description | string?（缺席＝無） | 用途說明；`None` 不上 wire（`skip_serializing_if`） |

讀端回傳形＝`Res<Vec<SettingItem>>`（非分頁、`ORDER BY setting_key` 升冪穩定序、
`deleted_at IS NULL` filter——R3-6）。★讀端 Model→DTO 映射帶**型別認識集守衛**：
setting_type 非 `number`／`enum:` 前綴→Internal `5000` 整支 fail-loud、不跳列
（§3 不變式「讀寫路徑觸及皆同」之讀端落點）。

## §2 wire DTO — UpdateSystemSettingReq（寫端請求）

`#[serde(rename_all = "camelCase")]`；三態欄依 Clarify Q1（RFC 7386 語意）。

| wire 欄 | 型 | 三態語意 |
|---|---|---|
| settingKey | string（必） | 定位鍵；未知鍵→`2222`（Clarify Q3）；欄缺席／型別非 string→`2222`（handler 層判） |
| settingValue | string（必） | 新值；經 registry 驗證＋正規化；**JSON null＝顯式清空 NOT NULL 欄→`2222`**；欄缺席→`2222`（handler 層判） |
| description | 三態（缺席／null／值） | 缺席＝不動；null＝清空落 NULL；值＝設值（不經 registry；varchar 無長度上限＝庫真表、本刀不設長度界） |

- 三態承載型（實作慣例）：`Option<Option<String>>`＋`#[serde(default)]`——外層 None＝
  缺席、Some(None)＝顯式清空、Some(Some(v))＝設值；settingValue 為偵測「顯式 null」
  亦以三態型承載、Some(None)→`2222`（拒收路徑、非落庫路徑）。
- ★必填欄（settingKey／settingValue）同以寬鬆形承載、缺席由 handler 層判 `2222`——
  **不由 serde 必填拒收**；JSON 反序列化失敗以自訂 rejection 落 `2222` 信封 HTTP 200
  （框架預設 400 裸 body＝違憲法 §I.3、絕不放行）。
- 成功回傳＝`Res<()>`（data:null、code:"0000"）。

## §3 設定值 registry（16 鍵逐鍵凍結；值域承 rev4 終態原值——research R4）

**number 型（10 鍵；含界 [min,max]；canonical＝`trim`→`parse::<i64>`→界內→`to_string()`）**

| setting_key | min | max | 界語意備註 |
|---|---|---|---|
| ip_captcha_after | 1 | 100 | 來源桶軟區門檻 |
| ip_max_fails | 1 | 100 | 來源桶硬鎖門檻 |
| ip_window_minutes | 1 | 1440 | 分鐘；上界一日 |
| login_throttle_captcha_after | 1 | 100 | 登入軟區門檻 |
| login_throttle_max_fails | 1 | 100 | 登入鎖定門檻 |
| login_throttle_window_minutes | 1 | 1440 | 分鐘；上界一日 |
| password_change_min_interval | 0 | 86400 | 秒；下界 0＝停用語意明確放行 |
| password_max_length | 1 | 256 | — |
| password_min_length | 1 | 128 | — |
| session_idle_timeout | 5 | 1440 | 分鐘 |

**enum:on,off 型（6 鍵；值域自含於 setting_type 字面；canonical＝原值）**：
password_forbid_username／password_require_digit／password_require_lowercase／
password_require_special／password_require_uppercase／single_session_default。

**registry 行為不變式**：
- 每鍵必有顯式宣告；宣告集外＝未知鍵→`2222`（含 number 鍵不在範圍表＝fail-loud 拒）。
- ★「含軟刪防禦態」之判定落點＝**facade 查詢層**（find_by_key／find_all 皆帶
  `deleted_at IS NULL` filter、軟刪列視同 miss）——registry 為 const 鍵集、型別上
  無從判 deleted_at。
- 庫中列 setting_type 不在認識集（`number`／`enum:` 前綴之外）→`5000`（R3-2；讀寫路徑
  觸及皆同——讀端落點見 §1 守衛、寫端落點＝validate）。
- 驗證失敗一律零寫入（原值保留）。
- 本表為 rust 端 const 單一來源；16 鍵集合本刀凍結（無新增／刪除鍵端點）。

## §4 route 註冊表（ROUTES const；RouteDef 六欄承 rev4 形——第六欄 handler＝
`fn() -> MethodRouter<AppState>` builder、表略）

| path | method | case_key | envelope_exception | protection |
|---|---|---|---|---|
| /health | GET | health | true（plain text "ok"） | Public |
| /metrics | GET | metrics | true（Prometheus exposition） | Public |
| /systemManage/getSystemSettings | GET | get-system-settings | false | Policy |
| /systemManage/updateSystemSetting | POST | update-system-setting | false | Policy |

★**機器契約**：ROUTES 字面形受 `tools/docs-sync.py` parse_router_routes 窄假設約束
（`pub const ROUTES: &[RouteDef] = &[` 精確開頭、block 頂層只認 `RouteDef {` 與 `];`、
每欄一行、handler＝`handler: || get|post|delete(...),` 形、method 限 Get/Post/Delete、
protection 限 Public/Authed/Policy）——任一偏離＝gen.router 重算失敗；寫完先跑
`python3 tools/docs-sync.py generate` 驗。

- Protection 三態承 rev4（Public／Authed／Policy）；B12 無 Authed 成員（型別保留、
  auth 刀啟用）。
- Policy＝enforce_mw（dev 驗證器）＋require_policy(path, method)——casbin act＝method
  字面、與 seed 政策列 66/67 對齊；路徑不帶 `/api` 前綴（front-nginx strip）。
- 覆蓋閘：contract case registry 與本表 case_key 雙向比對（缺 case 紅指名、殭屍 case
  紅指名）。

## §5 AppState 與 dev-only 測試態 identity

- `AppState`（`#[derive(Clone)]`）＝`db: DatabaseConnection`＋
  `enforcer: Arc<tokio::sync::RwLock<Enforcer>>`——恰兩欄（rev4 其餘欄不搬、R3-8）。
- **dev identity 查表**（`#[cfg(debug_assertions)]`、research R8）：

  | token 字面 | uid | 對應 seed 帳號 |
  |---|---|---|
  | dev-super | 1 | Super（R_SUPER） |
  | dev-admin | 2 | Admin（R_ADMIN） |
  | dev-user | 3 | User（R_USER_COMMON） |

  roles 不入表——授權判定恆走 require_policy 的 DB-fresh `roles_of_user`（真政策）。
  ★標頭承載形（權威定義）：`Authorization: Bearer <token>`（沿 rev4 bearer 解析形）——
  剝除 `Bearer ` 前綴、trim 後查表；標頭缺席／非 Bearer 形（含裸 token）／token 不在表
  →`8888`。release 建置＝驗證器缺席、一切請求 `8888`（fail-closed）。
- 注入形：驗證器產 `Identity { uid: i64, user_name: String }`（沿 rev4 Claims 注入位、
  audit updated_by 消費 uid）；auth 刀換 JWT 驗章時本型介面不變。

## §6 錯誤映射（AppError 變體集＝B12 六碼；單一來源住 error.rs）

| 變體 | 碼 | msg key | HTTP |
|---|---|---|---|
| Success | 0000 | common.success | 200 |
| Biz(key) | 2222 | 構造點顯式給定（biz.systemSettings.*） | 200 |
| NotFound | 4040 | system.notFound | 404（router fallback 專用） |
| PermissionDenied | 5003 | system.forbidden | 403 |
| Internal | 5000 | system.internal | 200 |
| Logout | 8888 | auth.session.reLogin | 200 |

- 13 碼常量 mod 全列（憲法 §I.3 矩陣完整）；**1000/3333/7777＋4 保留碼皆無變體**＝
  構造層不可發出（R3-9；contract 斷言消費此保證）。
- 本刀 Biz key 名冊：`biz.systemSettings.invalidValue`（型別／範圍／enum 外／三態非法）、
  `biz.systemSettings.notFound`（未知鍵）——沿 rev4 字面（R3-12）。
- ★zh-tw.ts 起手鍵集＝上表六個 key()／msg 固定鍵之實發五鍵（common.success／
  system.notFound／system.forbidden／system.internal／auth.session.reLogin）∪
  **Lint24 內部鍵白名單九鍵**（I18N_FRONTEND_INTERNAL_KEYS：biz.user.passwordViolation.*
  八鍵＋common.listSeparator——白名單存在性斷言要求九鍵必在字典）；biz.systemSettings.*
  二鍵隨構造點單元增補（Lint24 同步律）。

## §7 資料面補強（B-014；零 DDL）

- sys_user_role 兩條 DB FK（→sys_user.id／→sys_role.id）補 sea-orm `Relation` 枚舉＋
  `Related` impl（機械工；entity-drift 閘比對面＝欄集，不受 Relation 擾動）。
- 兩設計拍板轉錄（brainstorm §5、spec FR-022）：①無 DB FK 之邏輯關聯**不建** Relation
  （需要即手寫 join——單一關聯真相＝DB FK）②ActiveModelBehavior **不承載**六審計欄
  自動化（審計欄由 facade 顯式成對寫；通用化留下一支寫端刀複評）。

## §8 三態約定（B-026 envelope 級定形條文；全 repo 後續寫端消費）

部分更新請求之每一可選欄：**欄位缺席＝不動；欄位值 JSON null＝顯式清空（NOT NULL 欄
→`2222` 拒收、nullable 欄→落 NULL）；欄位有值＝設值**。解析層以三態型別區分「未出現」
與「null」（serde `Option<Option<T>>`＋default 慣例）。逐域欄級三態表由各域刀自定；
本約定僅鎖 envelope 級語意。★本條文隨 T025 轉錄為 ADR（B-026 定形、憲法 §V.1 權威鏈
落點）——accepted 後以該 ADR 為權威、本節轉指引。
