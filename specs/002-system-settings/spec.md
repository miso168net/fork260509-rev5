# Feature Specification: B12 系統設定讀寫——後端首刀縱切管線

**Feature Branch**: `002-system-settings`

**Created**: 2026-08-08

**Status**: Draft

**Input**: User description: "docs/brainstorms/002-system-settings.md"（階段 0 brainstorm、設計九節
user 核可 2026-08-08；本 spec 之唯一輸入。直接輸入含 BACKLOG B-014／B-026／B-024（seam 半條）
＋K1 五條（該檔 §2 表）；rev4 對應碼＝實作預設藍本、清單於 plan research 凍結（ADR 0019））

> 摘要：立 rust-api server 首批程式工件，打通「路由→授權→handler→設定值 registry→DB→wire→
> 前端接線層」整條縱切管線；功能面＝系統設定**讀＋寫**（16 鍵、per-key 型別／範圍驗證）；
> 前端腿＝typings＋service 接線層（ADR 0018、view 延 B-008）；B-026 三態約定層與 B-024 授權
> seam 隨寫端入刀定形；預期零 migration。本刀＝設定值的**治理面**（讀寫），設定值的**行為
> 兌現**（節流／session 等消費側）全數留對應域刀。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 讀端管線全通：R_SUPER 讀取全部系統設定 (Priority: P1)

作為 workspace 維護者（以 R_SUPER 身分操作），我要經 API 一次取得全部 16 鍵系統設定
（鍵／型別／現值／說明），使自後端首批程式工件起，「路由→授權→handler→DB→信封→前端接線層」
七環管線每一環都有真實流量通過並可獨立驗證。

**Why this priority**: 本刀是 rev5 第一把功能刀，讀端是管線存在性的最小證明；沒有讀端全通，
寫端與一切後續功能刀都無地基。

**Independent Test**: 僅實作讀端即可端到端驗證——起容器 stack、以 R_SUPER 身分呼叫讀取端點、
比對回包與 seed 定稿全等；不需寫端即交付「管線可用」價值。

**Acceptance Scenarios**:

1. **Given** seed 基線 16 鍵在庫、服務起得齊，**When** R_SUPER 身分呼叫讀取端點，**Then**
   信封 `{data, code:"0000", msg}`、data 含 16 鍵完整清單（setting_key／setting_type／
   setting_value／description），內容與 seed 定稿全等；僅回未刪列。
2. **Given** 前端接線層新檔（typings＋service），**When** 以其宣告型別消費回包，**Then**
   逐欄位型別對齊、零手工轉換。
3. **Given** R_ADMIN 身分（政策無讀取授權），**When** 呼叫讀取端點，**Then** 授權拒絕
   （碼表對映見 FR-019）、data 不含任何設定內容。

---

### User Story 2 - 寫端合法路徑：單鍵更新落庫 (Priority: P2)

作為 workspace 維護者（R_SUPER），我要更新單一設定鍵的值，值經 per-key 型別／範圍驗證通過後
落庫，回讀即得新值，且審計欄（updated_at／updated_by）成對記錄操作者——使寫路徑與設定值
registry（K1-26）自首刀即有真實消費者。

**Why this priority**: 寫端是 registry 存在的理由；「第一支寫端落地即隱含定死」的三態約定與
授權語意必須在本刀顯式定形（brainstorm 拍板③）。依賴 US1 的管線但可獨立驗收。

**Independent Test**: 合法更新後回讀比對新值＋審計欄成對非空；重放型驗證（同值再寫）不需
其他功能面即閉環。

**Acceptance Scenarios**:

1. **Given** number 型鍵（如 password_min_length、範圍宣告內），**When** R_SUPER 提交合法
   新值，**Then** `0000`、落庫、回讀一致、updated_at 與 updated_by 成對寫入（操作者取自
   請求身分）。
2. **Given** number 型鍵，**When** 提交等價但非正規形的值（如前導零），**Then** 落庫為
   正規形（number 正規化落庫）。
3. **Given** enum:on,off 型鍵（如 single_session_default），**When** 提交值域內另一值，
   **Then** `0000`、落庫、回讀一致。

---

### User Story 3 - 寫端驗證失敗路徑：非法值拒收、不寫入 (Priority: P2)

作為 workspace 維護者，我要非法寫入（型別不符／超範圍／enum 外值／未知鍵）被 registry 一律
拒收且**不落庫**，回包帶業務驗證錯誤碼與穩定訊息鍵，使設定值的完整性由機器把關、驗證失敗
路徑與成功路徑同等被契約測試覆蓋。

**Why this priority**: 驗證失敗路徑是 registry 的另一半（brainstorm 拍板③明定「寫路徑與
驗證失敗路徑一併打樣」）；與 US2 同刀落地才構成完整寫端。

**Independent Test**: 逐型別注入非法值、斷言拒收碼與原值保留；registry 每型有紅綠對
（合法過／非法拒），比對器自證。

**Acceptance Scenarios**:

1. **Given** number 型鍵，**When** 提交非數值字面或超出該鍵宣告範圍的值，**Then** 業務驗證
   錯誤（`2222`、HTTP 200 信封）、庫中原值保留、msg 為穩定 i18n key。
2. **Given** enum:on,off 型鍵，**When** 提交值域外的值，**Then** 同上拒收、原值保留。
3. **Given** 請求中 setting_key 不在 registry 宣告集，**When** 提交更新，**Then** 拒收
   （未知鍵、預設 `2222`——plan 期對 rev4 複核，見 Assumptions）、零寫入。
4. **Given** 庫中某列 setting_type 為 registry 不認識的型別字面（資料完整性異常、正常
   營運不可達），**When** 該列被讀寫路徑觸及，**Then** fail-loud 內部錯誤（`5000`、
   HTTP 200 信封）、絕不靜默略過或當作合法。

---

### User Story 4 - 越權寫入拒絕：授權骨架與拒絕語意定形 (Priority: P2)

作為 workspace 維護者，我要「有按鈕權限、無寫端政策」的角色（seed 已保證 R_ADMIN 持
user:edit 鈕而無任何 updateSystemSetting 政策）呼叫寫端時被正確拒絕，且拒絕語意與錯誤明細
粒度以刀內 ADR 定死（B-024 三件套之前置），使最小授權骨架（K1-27）自首刀即以真實組合驗證。

**Why this priority**: 授權面是縱切管線的一環；「第一支寫端落地即隱含定死」拒絕語意，
不在本刀顯式定形＝默拍。

**Independent Test**: 以 R_ADMIN／R_SUPER 兩身分對兩端點打授權矩陣，斷言碼與明細粒度
符合 ADR 定稿；不依賴其他功能面。

**Acceptance Scenarios**:

1. **Given** R_ADMIN 身分（casbin seed 現況：有 user:edit 鈕、無設定域任何政策），
   **When** 呼叫寫端，**Then** 授權拒絕（`5003`、HTTP 403），錯誤明細粒度依刀內 ADR 定稿；
   庫中零寫入。
2. **Given** 授權判定，**When** 任一端點執行授權檢查，**Then** 判定收斂於單一純函式進入點
   （enforce 骨架），且存在空 no-escalation 掛點（B-024 seam、本刀不實作其邏輯）。
3. **Given** 請求未攜任何身分（測試態 identity 缺席），**When** 呼叫任一業務端點，**Then**
   拒絕，碼隨測試態 identity 形式於 clarify 定案（見 Assumptions）。

---

### User Story 5 - 部分更新三態語意：B-026 約定層定形 (Priority: P3)

作為 workspace 維護者，我要部分更新的三態語意（欄位缺席＝不動／顯式清空／設值）在 wire
契約上有通用約定（envelope 級）且於本刀寫端具象驗證：nullable 欄（description）三態俱全、
NOT NULL 欄（setting_value）顯式清空＝非法拒收——使「第一支寫端」不以未定義語意隱含定死
全 repo 的部分更新行為。

**Why this priority**: B-026 明定「wire 契約設計期一次定形」；本刀是第一個寫端＝定形時點。
價值真實但依賴 US2／US3 的寫端先在。

**Independent Test**: 對 description 欄打三態矩陣（缺席／清空／設值）＋對 setting_value
打「顯式清空非法」案，斷言落庫效果與拒收碼；自成閉環。

**Acceptance Scenarios**:

1. **Given** 更新請求中 description 欄缺席，**When** 提交，**Then** 庫中 description
   原值不動、其餘提交欄正常生效。
2. **Given** 更新請求對 description 欄顯式清空（表示法＝clarify 定案），**When** 提交，
   **Then** 庫中 description 落 NULL。
3. **Given** 更新請求對 setting_value（NOT NULL 欄）顯式清空，**When** 提交，**Then**
   業務驗證拒收（`2222`）、零寫入。

---

### Edge Cases

- **併發同鍵更新**：兩請求同時更新同鍵 → 單鍵更新原子、last-write-wins、審計欄記最後
  寫入者；不設樂觀鎖（沿 rev4 預設，plan 期複核）。
- **軟刪列觸及**：16 鍵 seed 皆未刪、本刀無刪除端點，deleted_at 非 NULL 態正常營運不可達；
  防禦性處置＝讀端不回、寫端視同未知鍵拒收（不為不可達態新增碼面）。
- **未知型 fail-loud**：庫中 setting_type 字面不在 registry 認識集 → `5000`（US3 場景 4）；
  registry 絕不「跳過不認識的型」。
- **msg 訊息鍵未命中前端字典**：前端 graceful fallback（憲法 §I.3 既定），本刀 msg 一律
  穩定 i18n key、不回人話字串。
- **不認識的 header**：一律忽略（憲法 §II #1），契約測試不因多餘 header 改變行為。
- **值長度上限**：值域宣告涵蓋長度面（varchar 落庫），超長屬範圍驗證拒收、非截斷。
- **4 保留碼**：`7778`／`8889`／`9998`／`9999` 後端從不發出（憲法 §I.3），契約測試斷言
  本刀零發出。

## Requirements *(mandatory)*

### Functional Requirements

**管線與服務啟動**

- **FR-001**: rust-api server 首批程式工件 MUST 使六業務件 `up -d --wait` 起得齊（migrate
  啟動閘之後 server 常駐、容器健康判定可過）；RUNBOOK §1 步 5 的「B12 之前跑不完」已知態
  註記 MUST 同刀撤除。
- **FR-002**: 路由 MUST 收斂單檔 ROUTES 常量（K1-07）；本刀業務 route 恰兩條＝
  `GET /systemManage/getSystemSettings`＋`POST /systemManage/updateSystemSetting`
  （路徑與方法由 casbin seed 政策列 66／67 錨定；本刀 MUST NOT 動 casbin seed）；
  信封例外端點（/health plain text，憲法 §I.3 例外集）隨 server 就位供健康判定；
  gen.router Day-1 豁免 MUST 依到期即紅下架、routes 參考真表恢復重算。

**讀端**

- **FR-003**: 讀取端點 MUST 一次回傳全部 16 鍵（setting_key／setting_type／setting_value／
  description），僅未刪列；回傳形＝非分頁清單（16 鍵固定集、PageRes 不適用）；信封與逐欄位
  型別忠實 typings 權威（憲法 §I.3）。
- **FR-004**: 讀端授權 MUST 依 casbin seed 現況＝僅 R_SUPER；其餘角色→授權拒絕（FR-019
  碼表）。

**寫端與設定值 registry（K1-26）**

- **FR-005**: 寫端 MUST 為單鍵更新：以 setting_key 定位、提交新值；成功→`0000`、落庫、
  回讀一致。可更新欄集＝setting_value（必）＋description（三態，FR-011）；setting_key／
  setting_type 不可經寫端變更；無新增鍵／刪除鍵端點（16 鍵集合凍結）。
- **FR-006**: registry MUST 為每鍵顯式宣告型別與值域：型別集以現庫 16 鍵定形（int-range／
  enum-switch 兩型起步、可擴）；每 number 鍵 MUST 有顯式範圍宣告（逐鍵值域數字＝plan／
  data-model 凍結）；registry 未宣告之鍵＝未知鍵拒收。
- **FR-007**: 驗證失敗 MUST 不寫入：型別不符／超範圍／enum 外值／未知鍵→`2222`＋穩定
  i18n key 明細、庫中原值保留；每一拒收形 MUST 有契約測試案。
- **FR-008**: number 型值 MUST 正規化落庫（等價非正規字面→單一正規形；正規形定義隨 plan
  凍結）。
- **FR-009**: 庫中 setting_type 未知型 MUST fail-loud（`5000` 內部錯誤、HTTP 200 信封）；
  MUST NOT 靜默跳過或降級為警告。
- **FR-010**: 審計欄 MUST 由寫入口顯式成對寫（updated_at＋updated_by 同寫、操作者取自請求
  身分）；MUST NOT 由 ORM 行為層自動承載（brainstorm §5 拍板②；通用化留下一支寫端刀複評）。

**三態約定層（B-026、envelope 級）**

- **FR-011**: 部分更新 MUST 具三態語意：欄位缺席＝不動／顯式清空／設值；顯式清空表示法＝
  clarify 定案（候選見 Assumptions）；本刀定形射程＝envelope 級通用約定＋本刀寫端具象，
  逐域欄級表 MUST NOT 入本刀（留各域刀）。
- **FR-012**: NOT NULL 欄顯式清空 MUST 拒收（`2222`）；nullable 欄（description）顯式清空
  MUST 落 NULL；兩形 MUST 各有契約測試案。

**授權面（K1-27＋B-024 seam）**

- **FR-013**: 授權判定 MUST 收斂單一純函式進入點（enforce 骨架消費 casbin 政策）；MUST 留
  空 no-escalation 掛點（B-024 seam、本刀不實作邏輯）；auth 刀接真 session 時判定進入點
  介面不變。
- **FR-014**: 「R_ADMIN 有 user:edit 鈕、無寫端政策」組合（seed 已保證必發生）之拒絕語意
  與錯誤明細粒度 MUST 以刀內 ADR 定死（B-024 三件套前置；draft→accepted 於本刀完成）。
- **FR-015**: 登入未到位期間 MUST 以 dev-only 測試態 identity 頂替（形式＝clarify／plan
  定案）；測試態 identity MUST NOT 存在於非 dev 建置形。
- **FR-016**: request_context MUST 只留介面位（信任判定不寫死 handler；B-019 seam）；本刀
  MUST NOT 寫入 sys_operation_log／sys_access_log（B-016 射程、real_ip seam 不觸發）。

**wire 契約（K1-25＋憲法 §I.3）**

- **FR-017**: wire 權威＝base-web typings 新檔（rev5- 前綴、新增型圈界）；後端序列化 MUST
  逐欄位忠實 typings 宣告。
- **FR-018**: 契約機器化 MUST 就位：容器內自 typings 抽 JSON Schema 快照（落
  rust-api 測試 fixtures）、契約測試離線消費快照；coverage gate＝cargo test 形——每條
  業務 route 必有契約測試案、缺即紅。
- **FR-019**: 錯誤碼 MUST 全數 reuse 13 碼矩陣既有碼、零新增碼面；本刀逐碼對表：

  | 路徑 | 碼 | HTTP |
  |---|---|---|
  | 成功（讀／寫） | `0000` | 200 |
  | 型別不符／超範圍／enum 外值 | `2222` | 200 |
  | 未知鍵（含軟刪防禦態） | `2222`（預設、plan 期 rev4 複核） | 200 |
  | NOT NULL 欄顯式清空 | `2222` | 200 |
  | 授權拒絕（政策無授） | `5003` | 403 |
  | 庫中未知 setting_type（fail-loud） | `5000` | 200 |
  | 未認證（identity 缺席） | 隨測試態 identity 形式 clarify 定案 | — |

  4 保留碼 MUST 斷言本刀零發出；msg MUST 為穩定 i18n key。
- **FR-020**: i18n 字典兩側源 MUST 就位：base-web zh-tw 語言檔建檔＋接字典生成器（FR-026
  起手項）；本刀新增之 msg key MUST 進兩側源。

**資料面（B-014）**

- **FR-021**: sys_user_role 兩條 DB FK 之 ORM 關聯宣告 MUST 補齊（機械工、不擾動
  entity-drift 閘既有綠態）。
- **FR-022**: 兩設計拍板 MUST 依 brainstorm §5 落實並入 as-built 紀錄：①無 DB FK 之邏輯
  關聯不建 ORM 關聯宣告（需要即手寫 join、避免第二套關聯真相）②ORM 行為層不承載六審計欄
  自動化（FR-010 之資料面對應）。
- **FR-023**: 本刀預期零 migration（16 鍵＋表結構已隨 001 基線在庫）；clarify／plan 若冒出
  DDL → MUST 走 RUNBOOK §10 三步（照相＋演進帳登記＋三閘綠）。

**前端接線層（ADR 0018）**

- **FR-024**: 前端腿 MUST 恰為兩新檔：typings 型別宣告檔＋service 接線檔（皆 rev5- 前綴、
  §III.1 預設軌道、零 inline 改動、零修憲）；view 不入本刀（B-008）、manage_system-settings
  選單點擊 404 已知態持續。
- **FR-025**: 接線層 MUST 完整可消費：兩端點各有型別完備的呼叫函式，未來 view 刀接上即用、
  不需回頭補型別。

**治理起手與收刀 DoD**

- **FR-026**: 起手 tasks MUST 含（先於 server 首支 .rs 之 commit）：①建 base-web zh-tw
  語言檔＋接字典生成器 ②下架 lint24.day1 與 gen.router 兩筆到期豁免 ③gen.msg_dict 豁免
  與 lint24 謂詞的兩表假設不一致一併釐清（處置＝下架或修謂詞、依釐清結果）。
- **FR-027**: B-028 量測 MUST 跑兩輪：第一輪起手態（動工前、容器內冷編＋單檔增量）、
  第二輪 server 依賴進場後；數據落帳依 RUNBOOK §12.1 形制；收刀時 B-028 條目改寫留
  DDL 半條、勿整列刪。
- **FR-028**: K1 承襲盤點（brainstorm §2 表＝B-001 要求①）MUST 於 plan Constitution Check
  後回填「實際消費對照表」（B-001 要求②）；據此評估承襲盤點機器閘實需、結論留帳（實作
  若判要做＝B12 後維護批、不入本刀）。
- **FR-029**: 收刀 DoD MUST 全綠：契約測試（per route＋registry 紅綠矩陣＋三態案＋授權
  拒絕案）＋entity-drift＋schema-gate 三閘＋lint 全量；US1～US5 驗收場景全數對應至少
  一測試案。

### Key Entities

- **系統設定（system_settings、16 鍵）**: 鍵值型設定表（PK＝setting_key、setting_type／
  setting_value NOT NULL、description nullable、六審計欄 archetype A）；現庫 16 鍵＝
  number 型 10 鍵（節流窗／密碼長度／逾時等）＋enum:on,off 型 6 鍵（密碼複雜度開關／
  single_session_default 等）；鍵集合本刀凍結、僅值可變。
- **設定值 registry**: per-key 型別與值域宣告表（int-range／enum-switch 兩型起步、可擴）；
  驗證的唯一權威、未宣告鍵拒收；逐鍵值域數字隨 plan 凍結。
- **wire 契約物**: typings 新檔（權威）＋自其抽出之 JSON Schema 快照＋契約測試 fixtures；
  信封與 13 碼矩陣照憲法 §I.3 凍結面消費。
- **casbin 政策（seed 現況、本刀不動）**: 設定域三列皆僅 R_SUPER（讀 66／寫 67／menu 69、
  皆 protected）；R_ADMIN 之 user:edit 鈕（44）構成「有鈕無政策」驗證組合。
- **測試態 identity（dev-only）**: 登入未到位期間的請求身分頂替；形式 clarify 定案、
  auth 刀接真 session 時汰換。
- **三態約定（envelope 級）**: 部分更新之通用語意約定（缺席／清空／設值）；本刀定形、
  全 repo 後續寫端消費。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 讀端端到端：R_SUPER 讀回 16 鍵、與 seed 定稿逐鍵全等（key／type／value／
  description 四欄）；R_ADMIN 讀被拒且 data 零內容。
- **SC-002**: 寫端往返：合法更新（number 與 enum 各至少 1 例）後回讀＝新值、audit 欄成對
  非空；number 非正規字面落庫為正規形。
- **SC-003**: registry 紅綠矩陣全數正確：兩型各有合法過／非法拒對、未知鍵拒、未知型
  fail-loud——非法案庫中原值保留（零寫入以回讀證明）。
- **SC-004**: 授權矩陣全數正確：R_SUPER 讀寫皆 `0000`；R_ADMIN 讀寫皆 `5003`（HTTP 403）
  且明細粒度符合刀內 ADR 定稿；identity 缺席案符合 clarify 定案碼。
- **SC-005**: 三態矩陣全數正確：description 缺席不動／清空落 NULL／設值生效；
  setting_value 顯式清空拒收——四案各有契約測試。
- **SC-006**: 契約覆蓋自證：兩業務 route 皆有契約測試案，抽掉任一 route 之案 coverage
  gate 即紅（negative 自證）；4 保留碼零發出斷言在案。
- **SC-007**: DoD 鏈全綠：六業務件 `up -d --wait` 起得齊＋RUNBOOK §1 已知態註記撤除＋
  三筆 Day-1 豁免處置完畢（lint24.day1／gen.router 下架、gen.msg_dict 依釐清結果）後
  全量 lint 零紅＋entity-drift 綠＋schema-gate 三閘綠。
- **SC-008**: B-028 兩輪量測數據落帳（RUNBOOK §12.1 形制）；K1 實際消費對照表回填在案
  （B-001 要求②）。

## Assumptions

- **wire 形＝POST 單鍵更新**：casbin seed 政策列 67 已錨定 `updateSystemSetting POST`
  （政策 obj＝路徑、act＝方法；brainstorm 拍板「不動 casbin seed」→ 改用 PUT／PATCH 須動
  seed＝拍板級翻案）。brainstorm §4 clarify 候選第三題以此為既定事實、clarify 僅確認。
- **未知鍵拒收碼＝`2222` 預設**：植基「registry 宣告集之外＝業務驗證失敗」語意；rev4 對應
  碼於 plan research 複核，若 rev4 採 `4040` 則屆時對表更新（誤差射程僅此一格）。
- **測試態 identity 形式＝clarify 定案**（brainstorm §4 候選第一題）：候選形＝dev-only
  請求標頭注入／固定測試 token／建置期旗標；連動「未認證回哪個碼」同題定案。
- **顯式清空表示法＝clarify 定案**（brainstorm §4 候選第二題）：候選形＝JSON null 承載
  清空（缺席與 null 區分於解析層）／專用 clear 欄位表；B-026 前代教訓（null＝整欄跳過、
  清空無語意）為反面輸入。
- **registry 逐鍵值域數字＝plan／data-model 凍結**（brainstorm §4 候選第四題之處置）：
  spec 僅凍結「每鍵必有顯式宣告」紀律，16 鍵逐鍵範圍值屬設計期資料、隨 plan 定稿。
- **寫端可更新欄含 description**：三態約定需真實 nullable 欄具象；rev4 對應 req 形於 plan
  research 複核，若 rev4 無此欄＝rev5 拍板差異點記明（ADR 0019 差異清單）。
- **併發語意**：單鍵更新原子、last-write-wins、無樂觀鎖（16 鍵低頻治理面；沿 rev4 預設、
  plan 複核）。
- **零 migration**：表結構＋16 鍵 seed 已隨 001 基線在庫（複核 2026-08-08：fixtures 與
  reference 真表 16 鍵在案）；DDL 冒出時走 FR-023。
- **實作紀律引用**（非本 spec 新拍板）：rev4 對應碼先讀後寫、重打字消化、註解一律重寫
  （憲法 §I.5＋ADR 0019）；容器內 build／test 全程 serial；web 框架選型＝plan research
  工程自拍（傾向沿 rev4 選型）。
- **upstream rebase 風險低**：前端腿皆 rev5- 前綴新檔（brainstorm §9）。

### Out of Scope

- **view UI**（B-008）：manage_system-settings 頁面不入本刀、選單 404 已知態持續。
- **真登入／session**（auth 刀、K1-27 defer 面）：本刀僅測試態 identity 頂替＋授權骨架。
- **稽核 log 寫入**（B-016）：sys_operation_log／sys_access_log 零寫入；real_ip 信任鏈
  （B-019）僅留 request_context 介面位。
- **列表排序**（B-027）：16 鍵清單無排序參數；觸發＝B-027。
- **prod 資產**（ADR 0014）：各面僅留 seam。
- **新增／刪除設定鍵端點**：16 鍵集合凍結、僅值可變；無對應 casbin 政策＝無對應 route。
- **三態逐域欄級表**：本刀僅 envelope 級約定＋本刀寫端具象；各域欄級表留各域刀。
- **no-escalation 邏輯實作**（B-024 本體）：本刀僅空掛點＋拒絕語意 ADR。
- **設定值的行為兌現**：16 鍵之消費側（登入節流／session 逾時／密碼原則 enforce 等）
  全數留對應域刀；本刀讀寫治理面不含任何值語意生效驗證。
- **承襲盤點機器閘實作**（B-001）：本刀僅評估與結論留帳。
