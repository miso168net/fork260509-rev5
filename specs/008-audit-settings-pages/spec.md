# Feature Specification: 008 稽核中心與系統設定頁（B-008 收官、audit 五端點）

**Feature Branch**: `008-audit-settings-pages`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "docs/brainstorms/008-audit-settings-pages.md"（階段 0 brainstorm 定稿
〔2026-09-01；五支唯讀偵查 workflow＋主線 grep 復核〕＋兩題 AskUserQuestion 親決〔2026-08-31〕＋
grilling 四題親決〔2026-09-01、BACKLOG 兩卷 26 條逐條掃描、frontier 已空〕；本 spec 之唯一輸入。
射程權威＝brainstorm §2；rev4 對應碼＝實作預設藍本、清單於 plan research 凍結（ADR 0019））

> 摘要：把 B-008 餘兩張 rev4 專屬管理頁做成真功能——**manage_system-settings**（後端 002 已備、
> 純前端接線）＋**manage_audit**（四源四分頁唯讀查詢報表＋水平線清理；後端新開 **5 支端點**、
> ROUTES 61→66；**零 migration、零 seed 變更**——path×method 契約由 001 凍結 seed 五列預埋）。
> 本刀拍板兩件 user 可見行為：access 分頁空表＝已知態（寫入面歸 B-016）；**XFF 欄三分頁渲染**
> ＝UI 對照 rev4 唯一例外（ADR 0076、B-072 關單形）。連帶納入：Lint24 擴腿（攜參鍵佔位符機器守、
> B-139）、purge 原子性 fault-injection＋`_with_db` 薄殼（B-125）。修憲一次：§III.2
> `BASE-WEB-MANAGE-PAGE-WIRING` 加用途 (vii)(viii)。收刀關帳六條：B-008／B-072／B-078／B-125／
> B-139＋seed-view-gate 豁免表摘兩列。

## Clarifications

### Session 2026-08-31（brainstorm 兩題 AskUserQuestion 親決；全紀錄見 brainstorm §1）

- Q1 `sys_access_log` 寫入面（`access_log_mw`）納不納？→ A: **不入本刀**（取建議案）——沿 004
  research 既有拍板（不搬、歸 B-016 稽核域射程）；`getAccessLog` 讀端照做但讀空表、access 分頁
  空列表＝已知態；B-016 條目補註已落。
- Q2 audit 頁渲染 `xForwardedFor` 欄？→ A: **渲染**（user 親決、非建議項）——operation／access／
  login 三分頁加該欄（session_event 無此欄不加）；純文字＋ellipsis+tooltip；UI 對照 rev4 唯一
  例外；B-072 以「渲染＋轉義就位」對帳關單；承載＝ADR 0076（已 accepted）。

### Session 2026-09-01（grilling 四題親決＋整體設計核可；全紀錄見 brainstorm §1b／§1c）

- Q3 B-139（佔位符↔data 鍵零機器守）？→ A: **納入**——本刀新增第三個攜參鍵
  `biz.audit.purgeBelowFloor{minDays}`＝觸發器成立；Lint24 擴一腿（zh-tw 譯文 `{ident}` 佔位符集
  × 後端 `BizData` 構造點頂層鍵集比對）；B-139 隨刀關帳。
- Q4 purge 原子性 fault-injection？→ A: **做**——`_with_db` 薄殼（B-125 翻案條件「第二個注入 db
  需求」成立）＋purge 原子性測＋logout TTL 同形補測；B-125 隨刀關帳。
- Q5 B-078（稽核欄複驗殘餘）？→ A: **本刀確認後關帳**——四支讀端零複驗入口、realIp 過濾＝精確
  等值非 LIKE，確認句入本 spec（FR-B08）；紀律本體居 RUNBOOK §9。
- Q6 B-143（user 搜尋卡兩欄）？→ A: **不納**——本刀 Amendment 只加用途 (vii)(viii)、不擴 (v)；
  觸發器保留。
- 自拍工程項（回報備查、brainstorm §1）：四源四分頁照 rev4；wire 命名空間獨立 `Api.Audit`；
  DTO 欄名對齊 rev5 schema；i18n 兩語；peerIp／ipConfidence 不渲染（偏離最小化）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 超管檢視並調整系統設定 (Priority: P1)

超管自側欄進入「系統設定」頁，看到依用途分為四組（密碼策略／工作階段／IP 源登入／帳號登入）的
16 個運行參數；開關型參數以開關呈現、數值型以數字輸入框呈現，每項旁有說明提示。改動任一項即
單獨提交並立刻生效回讀——畫面永遠顯示伺服器的真值。

**Why this priority**: 這是 B-008 兩張頁之一、後端 002 早已備妥只欠 UI；也是 seed-view-gate
豁免表出列的前提。改動即時生效面（節流、逾時、密碼政策）是營運日常。

**Independent Test**: 只實作本 story（settings 頁）即可獨立驗收——側欄進頁、逐鍵改值、回讀
一致、非法值被拒且畫面回退。

**Acceptance Scenarios**:

1. **Given** 以 Super 登入、**When** 側欄點「系統設定」、**Then** 正常進頁，顯示四組共 16 鍵，
   側欄項顯示翻譯後名稱（非原始 i18n key）。
2. **Given** 頁面已載入、**When** 切換某開關型設定、**Then** 立即提交、成功提示出現、值以
   伺服器回讀為準。
3. **Given** 頁面已載入、**When** 在數值欄輸入超出後端界限的值並失焦、**Then** 後端拒絕並顯示
   可讀拒因（i18n 轉譯、非裸鍵），畫面回退為伺服器現值。
4. **Given** 數值欄被清空、**When** 失焦、**Then** 不送出更新、畫面回退為伺服器現值。
5. **Given** 以 Admin（非超管）登入、**When** 檢視側欄、**Then** 「系統設定」不可見；直呼其
   兩支端點得越權拒絕。

---

### User Story 2 - 超管查詢四源稽核紀錄 (Priority: P1)

超管自側欄進入「稽核中心」頁，四個分頁分別對應操作日誌、存取日誌、登入嘗試、會話事件四個
稽核源。每分頁有搜尋卡（欄位過濾＋時間區間）、重新整理鈕與分頁表格；操作日誌可檢視變更前後
快照。三個含 XFF 欄的分頁把該欄以純文字顯示（本刀拍板、rev4 對照唯一例外）。

**Why this priority**: B-008 主體之二；audit 5 支端點與 B-072 渲染義務的兌現點。

**Independent Test**: 只實作本 story（四支讀端＋audit 頁讀面）即可獨立驗收——四分頁查詢、
搜尋、分頁、快照 dialog 全通，與 rev4 頁對照一致（除 XFF 欄）。

**Acceptance Scenarios**:

1. **Given** 以 Super 登入、**When** 側欄點「稽核中心」、**Then** 正常進頁、四分頁可切換，
   各表以固定新→舊排序分頁呈現（每頁預設 10 筆、可調）。
2. **Given** 操作日誌分頁、**When** 以資料表名／操作類型／操作者過濾並設時間區間、**Then**
   結果符合全部條件；操作者顯示名稱（查無名稱時顯示 ID）。
3. **Given** 操作日誌有快照的列、**When** 點「查看」、**Then** 以唯讀對話框顯示變更前／後
   JSON 純文字；無快照的列顯示「（無快照）」。
4. **Given** 登入嘗試分頁、**When** 以成功／失敗與精確 IP 過濾、**Then** 結果正確；分頁上方
   顯示「節流短路遭拒不落表」語意告示。
5. **Given** 某列 `xForwardedFor` 值含 `<script>` 等 HTML 字面、**When** 該列渲染、**Then**
   內容以字面文字顯示、零腳本執行、零 HTML 解析（XSS 驗收；ADR 0076）。
6. **Given** 存取日誌分頁（rev5 現況零寫入者）、**When** 進入、**Then** 顯示空列表空態＝
   已知態、非錯誤（寫入面歸 B-016）。
7. **Given** 以 Admin 登入、**When** 直呼任一 audit 端點、**Then** 越權拒絕；未認證呼叫得
   未認證拒絕。

---

### User Story 3 - 超管水平線清理稽核資料 (Priority: P2)

超管在任一稽核分頁點「清理」，於對話框輸入保留天數（下限 30 天）、經二次確認後，刪除該源早於
水平線的資料；系統回報刪除筆數，並在操作日誌留下一筆清理自記（含來源表、天數、筆數）。

**Why this priority**: 第 5 支端點；破壞性操作、原子性要求最高，但依賴讀面先在（驗證其效果）。

**Independent Test**: 以既有稽核資料執行清理——低於下限被拒、成功刪除有筆數回報、操作日誌
多一筆自記且自記不被自身清理刪除。

**Acceptance Scenarios**:

1. **Given** 清理對話框、**When** 輸入低於 30 的天數送出、**Then** 拒絕並顯示帶下限值的可讀
   拒因（`{minDays}` 插值）。
2. **Given** 合法天數＋二次確認、**When** 送出、**Then** 該源早於水平線的列被刪除、回報刪除
   筆數、對應分頁刷新；操作日誌多一筆清理自記。
3. **Given** 清理標的＝操作日誌自身、**When** 執行、**Then** 歷史清理自記列不被刪除（自記
   豁免）。
4. **Given** 清理過程中自記寫入失敗（故障注入）、**When** 交易結束、**Then** 整筆回滾——
   零刪除、零自記、回錯誤；絕不出現「回報刪了 N 筆實際零刪除」（B-125 危害形）。
5. **Given** 清理請求 `table` 值域外、**Then** 拒絕並顯示可讀拒因；天數欄畸形值視同缺席、
   同樣被下限擋下（恆不裸 400）。

---

### User Story 4 - 開發者防線：佔位符漂移與靜默回滾不可能發生 (Priority: P3)

開發者改壞攜參鍵的譯文佔位符（或後端 data 鍵名）時，pre-commit lint 當場紅；改壞 purge 同交易
自記的錯誤處理時，測試當場紅。兩道防線皆附負向自證、非裝飾性。

**Why this priority**: 治理面連帶（B-139／B-125 關帳）；不影響終端使用者可見功能、但鎖住本刀
新增暴面的兩種靜默壞法。

**Independent Test**: 變異測試——把 zh-tw 某攜參鍵佔位符改名→lint 紅、還原→綠；把自記失敗
改吞錯→purge 原子性測紅、還原→綠。

**Acceptance Scenarios**:

1. **Given** Lint24 擴腿就位、**When** zh-tw 譯文某攜參鍵的 `{ident}` 與後端 data 頂層鍵不一致、
   **Then** pre-commit 紅、錯誤訊息指名該鍵。
2. **Given** 三個攜參鍵現況全對齊、**Then** lint 綠（正向）；自測含正反例。

---

### Edge Cases

- 時間區間顛倒（from > to）＝回空頁；畸形時間字串＝該過濾視同未設（皆照 rev4 語意）。
- query 參數帶空字串（如 `?operation=`）不得 4xx——寬鬆解析、視同未設。
- 分頁參數越界：current < 1 取 1；size 超上限取上限（100）、低於 1 取 1。
- `xForwardedFor` 值最長 1024 字元（建構點截斷保證）：欄內截尾顯示、懸停看全文；空值顯示
  佔位符「-」。
- session 分頁無 XFF 欄（該源結構性無此欄）——不渲染、不留空欄。
- 操作者名過濾含已軟刪的同名使用者（rev4 語意：名→全集 IN、id 優先於名）。
- 登入嘗試 `success` 過濾僅收 'true'／'false' 兩值、值域外視同未設。
- settings 未知 `settingType`（非二值 enum、非 number）→唯讀呈現原值、不可改（優雅降級）。
- settings 未映射 i18n 鍵的新設定→label 以後端 description 遞補、頁面不壞。
- 快速連續切換開關：逐次提交、最終以伺服器回讀收斂（無防抖、可短暫閃動＝rev4 既有行為）。
- 稽核清理與併發寫入：清理僅刪早於水平線的列，與新寫入零交集；操作日誌自記與刪除同交易。

## Requirements *(mandatory)*

### Functional Requirements

#### A. 端點與契約總則

- **FR-A01**: 系統 MUST 新開恰 5 支稽核端點，path×method **逐字等於** 001 凍結 seed 預埋的
  5 列 casbin endpoint 維政策：`/systemManage/getOperationLog`／`getAccessLog`／
  `getLoginAttempt`／`getSessionEvent`（GET）＋`/systemManage/purgeAuditLog`（POST）。
  **零 migration、零 seed 變更、零新政策列**。
- **FR-A02**: 5 支端點 MUST 全部走政策保護（casbin endpoint 維、seed 僅授 R_SUPER）；越權＝
  5003、未認證＝8888（皆統一信封）。settings 兩支端點沿 002 既有、本刀零後端改動。
- **FR-A03**: `ROUTES_COUNT` MUST 61→66 同 commit bump；route 表既有不變式測全綠。
- **FR-A04**: 四支讀端 MUST 回統一分頁信封（current／size／total／records）；分頁參數
  current 預設 1 下界 1、size 預設 10 上界 100；排序固定 `created_at DESC, id DESC`（前端
  零 sorter）。
- **FR-A05**: 讀端 query 參數 MUST 寬鬆解析（全部可缺席；空字串視同未設；絕不因 query 形
  回裸 4xx——承 rev4:L-090）。時間過濾＝RFC3339、閉開 `[from, to)`；畸形＝未設、顛倒＝空頁。
- **FR-A06**: wire 型 MUST 開獨立命名空間 `Api.Audit`（004 起先例；rev4 併入
  Api.SystemManage 之形不帶回）；前端 typings＝wire 契約權威（憲法 §I.1）；DTO 欄名對齊
  **rev5** schema（操作日誌欄不帶 `operator_` 前綴、含 `region`；rev4 DTO 家族形不帶回）。
- **FR-A07**: `Api.Audit.*` 每個 definition MUST 隨刀補 wire_schema 快照裁判（正反例成對、
  值域接後端真源常數；照 `Api.IpRule` 節先例形）＋contract case registry 五 case（未認證
  8888 信封面；query 參數零判別力＝既知限制、B-030 殘項不在本刀）。

#### B. 四支讀端語意（照 rev4 藍本＋§Clarifications 差異）

- **FR-B01**: 操作日誌讀端過濾維＝資料表名（等值）／操作類型（等值）／操作者 id 或名
  （id 優先、名含已軟刪同名全集）／時間區間；列含變更前後快照（JSON、可缺席）。
- **FR-B02**: 操作日誌快照 MUST 經讀出端 PII 打碼後上 wire（rev4 `mask_pii_payload` 對應物；
  rev5 等價物於 plan research 定案——無現成則隨刀落）。
- **FR-B03**: 存取日誌讀端過濾維＝HTTP 方法（等值）／狀態碼（等值）／路徑（模糊含、萬用
  字元字面化）／操作者 id 或名／時間區間。★rev5 現況該表零寫入者：讀端照做、空表＝已知態
  （寫入面 access_log_mw 歸 B-016、004 拍板）。
- **FR-B04**: 登入嘗試讀端過濾維＝嘗試帳名（模糊）／成功旗標（嚴格 'true'|'false'、值域外
  ＝未設）／來源 IP（**精確等值**）／時間區間；該源無操作者維（匿名寫入）。
- **FR-B05**: 會話事件讀端過濾維＝使用者 id 或名／事件型（等值）／原因（等值）／時間區間；
  列含 sid、事件型、原因、操作者、來源 IP。列型逐欄以 rev5 `session_event` 表形為準
  （plan research 凍結）。
- **FR-B06**: 操作者／使用者名稱 MUST 以第二發批次查詢 enrich（不 join、無 N+1）；查無名稱
  時前端顯示 ID、再無則「-」。
- **FR-B07**: 三個含 `xForwardedFor` 欄的源（操作／存取／登入）該欄 MUST 上 wire（原文、
  建構點已保證零 CR/LF＋≤1024 字元）；`peerIp`／`ipConfidence` 同 rev4 上 wire 但前端不渲染。
- **FR-B08**（B-078 確認句）: 讀端 MUST 零稽核欄複驗入口；來源 IP 過濾 MUST 為精確等值
  （IPv4 /32、IPv6 /128）比對、MUST NOT 以 LIKE 字串包含實作（路徑／帳名之模糊搜屬一般
  文字欄、非 IP 欄）。此句＝B-078 觸發臂之確認、收刀關帳依據。

#### C. 清理（purge）語意

- **FR-C01**: 清理請求＝{來源表, 保留天數} 二欄；來源表 MUST 限四值白名單（operationLog／
  accessLog／loginAttempt／sessionEvent）、值域外＝2222 `biz.audit.invalidTable`。
- **FR-C02**: 保留天數 MUST ≥ 30（`PURGE_MIN_DAYS`、後端權威）；違反＝2222
  `biz.audit.purgeBelowFloor` 攜 `{minDays}` 明細；天數欄寬鬆反序列化（畸形→視同缺席→
  被下限擋、恆不裸 400）。★floor 30＝B-016 逐表門檻設計時必須鏡像的下限（brainstorm §1c）。
- **FR-C03**: 清理 MUST 單交易完成：水平線 DELETE（早於 now − 天數）＋同交易操作日誌自記
  （含來源表、天數、刪除筆數）；操作日誌版 DELETE MUST 豁免歷史清理自記列。回傳刪除筆數。
- **FR-C04**（B-125）: 清理原子性 MUST 有 fault-injection 級測試釘住：注入故障使自記失敗→
  斷言整筆回滾＋錯誤回傳＋零刪除零自記（非 vacuous、附紅綠證）。為此建測試建構腿
  `_with_db` 薄殼（沿用既有 test_state、不新增 AppState 建構字面）；logout TTL 同形補測
  同批落；B-125 隨刀關帳。

#### D. 前端——系統設定頁

- **FR-D01**: settings 頁 MUST 為資料驅動：控件由伺服器回的 `settingType` 決定（二值 enum→
  開關、number→數字輸入、其他→唯讀呈現）；前端不硬編鍵→控件對應。
- **FR-D02**: 四組分區固定序（密碼策略／工作階段／IP 源登入／帳號登入，依鍵前綴歸組）；
  未列序新鍵排組尾保伺服器相對序；空組整卡不渲染。
- **FR-D03**: 逐項即改即存：開關切換即提交；數字欄失焦／Enter 提交、清空不送；提交後
  （成功與失敗皆）MUST 回讀伺服器全列收斂畫面；成功提示、失敗走既有攔截器 i18n 轉譯。
- **FR-D04**: 16 鍵 label＋help 提示 MUST 兩語齊備（zh-cn／en-us；未映射鍵 fallback 後端
  description）；數字欄顯示界照 rev4（UX 護欄；真值約束恆在後端）。
- **FR-D05**: 頁內零按鈕級 gating（門＝menu 維政策僅 R_SUPER＋後端端點政策）；接**既備**
  `rev5-settings` 接線層（002／ADR 0018）、後端與接線層零改動。

#### E. 前端——稽核中心頁

- **FR-E01**: audit 頁 MUST 四源四分頁（操作／存取／登入／會話；照 rev4 7 檔形：主頁＋四支
  搜尋卡＋清理對話框＋共用時間區間邏輯）；「三張表」帳面舊述以四源為準。
- **FR-E02**: 各分頁搜尋卡同構（預設展開、重設清空並觸發搜尋、時間區間以 UTC ISO 上 wire）；
  重新整理鈕不重置頁碼、搜尋回第 1 頁；每頁預設 10 筆可調。
- **FR-E03**（ADR 0076）: 操作／存取／登入三分頁 MUST 渲染 `xForwardedFor` 欄：**純文字**
  插值＋截尾顯示＋懸停全文；session 分頁不渲染（無此欄）；此為 CDP 對照 rev4 的**唯一**
  例外、驗收以 ADR 0076 為例外註記。`peerIp`／`ipConfidence` 維持不渲染。
- **FR-E04**: 表格欄集、欄寬、渲染形（NTag 染色、名稱降級「-」、快照 dialog 純文字 JSON）
  逐欄照 rev4；scroll-x＝Σ欄寬不變式隨 XFF 新欄同批改、註解記帳。
- **FR-E05**: 清理入口每分頁一顆、共用單例對話框（標的隨分頁切換；天數下限 30 前端護欄＋
  警語＋二次確認；成功提示帶刪除筆數並刷新該分頁）。
- **FR-E06**: 零匯出、零前端排序、零快照內容搜尋（rev4 亦無）；登入分頁帶節流語意告示。
- **FR-E07**: 新增 view 檔 MUST 過 `view-render-guard`（7 條禁字面、含註解）；自由文字欄
  一律純文字插值（管理頁慣例）。

#### F. 進場面（route／i18n／接線）

- **FR-F01**: 兩頁 route 條目經路由外掛重算產出（產物四檔零手改、`route-artifact-gate`
  冪等綠）；兩語 locale `route:` 樹各補兩鍵、`page:` 樹各補兩節、`app.d.ts` page 型節同批
  補（三處鏡像、兩語鍵集相等）；zh-tw.ts 治理錨不動。
- **FR-F02**: 新檔 `rev5-audit.ts`／`rev5-audit.d.ts`（service／typings；不入 barrel、消費端
  直接路徑 import——既有慣例）。
- **FR-F03**: 煙測判準 MUST 反轉：側欄點兩項由「零反應＋顯示原始 i18n key」變「正常進頁」
  （判準走側欄路徑、非直打網址 404——B-008 條目 2026-08-17 更正）。
- **FR-F04**: 選單可見性照 seed（兩頁 menu 維僅 R_SUPER；icon／order 由 seed 下發、dynamic
  route 模式）。

#### G. 治理與簿記

- **FR-G01**: 本刀 U0 MUST 完成憲法 §III.2 `BASE-WEB-MANAGE-PAGE-WIRING` 加用途 (vii)
  system-settings 頁進場＋(viii) audit 頁進場（形照 (i)/(iv) 先例：兩語 locale 兩樹＋
  app.d.ts page 型節新增型圈界；view 新檔不入名冊；產物四檔沿 (i) 列）；不擴用途 (v)
  （B-143 不納、拍板⑥）。
- **FR-G02**: 行為島候選＝audit purge 域（30 天下限／單交易自記／自記豁免／四值白名單）
  MUST 於修憲單元依憲法 §IV 第 9 題判定是否入憲、user 親決。
- **FR-G03**: 收刀 MUST 關帳六條：B-008 刪列；`seed-view-gate` EXEMPT 摘恰兩列（不摘＝
  gate 紅）；B-072 對帳關（ADR 0076）；B-139 關（FR-H01 落地）；B-125 關（FR-C04 落地）；
  B-078 關（FR-B08 確認）。相關現在式文件之待辦式引用同批掃改（L-072 雙向掃）。

#### H. 工具

- **FR-H01**（B-139）: Lint24 MUST 擴一腿：解析 zh-tw 譯文全部攜參鍵的 `{ident}` 佔位符
  集合、與後端 `BizData` 構造點頂層鍵集比對，不一致即紅、訊息指名鍵；自測含正反例
  （非 vacuous）。掃描面以 `BizData` 構造點集為錨（007 已建通道；本刀後攜參鍵恰三）。

#### I. 測試與紀律

- **FR-I01**: 後端測試三層（沿 002／007 先例）：handler 同檔真 DB 測（容器內、分角色授權
  矩陣＋seed 對賬）＋contract case（FR-A07）＋wire_schema 裁判；rust build/test 容器內
  全程 serial。
- **FR-I02**: 實作 MUST 先讀 rev4 對應碼（唯讀）、重打字消化不拷貝、註解重寫帶 `rev4:`
  前綴、rev5 拍板差異點（brainstorm §3 六條）不得帶回（ADR 0019）；rev4 對應碼清單於
  plan research 凍結。
- **FR-I03**: 驗收走 CDP 三方對照（42080 rev4 基準 vs 22080 rev5；XFF 欄唯一例外）＋真登入
  走查前後 `walkthrough-baseline` snapshot／diff 全表對賬（RUNBOOK §9c）。

### Key Entities *(include if feature involves data)*

- **稽核源（四）**: 操作日誌（誰對哪張表做了什麼、含變更前後快照與清理自記）／存取日誌
  （每次 API 請求的方法、路徑、狀態、來源；本刀讀面先行、寫入面 B-016）／登入嘗試（帳名、
  成敗、來源；節流短路遭拒不落表）／會話事件（會話生命週期事件：kicked、idle、logout 等）。
  皆 append-only、僅新→舊讀取、水平線清理。
- **系統設定（KV）**: 16 個運行參數（鍵、字串值載體、型別描述、說明）；型別描述驅動 UI
  控件；真值約束在後端驗證登記表。
- **清理請求**: {來源表（四值）, 保留天數（≥30）}→刪除筆數；每次清理在操作日誌留自記。
- **稽核列 DTO 家族（`Api.Audit`）**: 四源列型＋各自過濾參數型＋分頁信封＋清理請求／回應型；
  欄名對齊 rev5 表形。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 以超管身分自側欄可在 3 次點擊內抵達兩張新頁；兩項側欄文字皆為翻譯後名稱、
  點擊即進頁（煙測判準由「零反應＋原始 key」反轉為「正常進頁」）。
- **SC-002**: 四個稽核分頁的查詢、搜尋、時間區間、分頁與快照檢視行為與 rev4 對照頁逐項一致
  （CDP 三方對照；唯一允許差異＝XFF 欄、依 ADR 0076 註記）。
- **SC-003**: 對含 HTML／script 字面的 `xForwardedFor` 資料列，頁面渲染為字面文字、零腳本
  執行（注入驗證至少一例、CDP 實測）。
- **SC-004**: 系統設定 16 鍵 100% 可視可讀；可改鍵改動後 1 次回讀內畫面與伺服器一致；非法
  值 100% 被拒且拒因可讀（非裸 i18n 鍵）。
- **SC-005**: 清理操作：低於 30 天 100% 被拒（拒因含下限值）；成功清理回報筆數與實刪一致；
  操作日誌清理自記留存率 100%（自記豁免）；故障注入下零部分成功（fault-injection 紅綠證）。
- **SC-006**: 佔位符漂移防線：任一攜參鍵佔位符改名→pre-commit 100% 攔下（變異自證）；
  現況三鍵全綠。
- **SC-007**: 全閘綠：rust 容器全量 serial（0 failed）、三閘、`seed-view-gate`（EXEMPT 已摘）、
  `view-render-guard`、`route-artifact-gate` 冪等、fork-delta-lint、`pnpm typecheck`。
- **SC-008**: 收刀時 BACKLOG 六條關帳全數落地（B-008／B-072／B-078／B-125／B-139＋豁免表
  摘列）、走查前後全表基準 diff rc 0。

## Assumptions

- 5 支端點 path×method 契約由 001 凍結 seed 預埋列決定（brainstorm 第一查核點已逐字核實）；
  本刀零 migration、零 seed 變更。
- `sys_access_log` 空表＝已知態：讀端與 UI 照做、資料自 B-016（access_log_mw）落地後才累積；
  CDP 對照該分頁驗 UI 形不驗資料量。
- rev4 對照 stack（42080）可用且其 audit／settings 頁為驗收基準；rev4 樹唯讀。
- `session_event` rev5 表逐欄形與 op-log PII 打碼等價物於 plan research 凍結（brainstorm §5
  開放項；不影響本 spec 射程）。
- `PURGE_MIN_DAYS=30` 同時是 B-016 retention 逐表門檻的下限鏡像（rev4 先例形）；B-016 設計
  時以本刀落的常數為準。
- settings 16 鍵 seed×驗證登記表互鎖 002 既備；本刀後端與接線層零改動、view 純消費。
- i18n 兩語（zh-cn／en-us）；zh-tw.ts＝治理錨孤立檔、僅 `backend` 樹隨拒因鍵新增而動
  （Lint24 射程）、route:/page: 樹不動。

### Out of Scope

- `access_log_mw`（存取日誌寫入面）與 retention／reaper 自動清理——皆 B-016（拍板①）。
- 匯出、前端排序、快照內容搜尋（rev4 亦無；B-027 排序另有其刀）。
- B-143（user 搜尋卡兩欄）——觸發器保留（拍板⑥）；用途 (v) 名單不擴。
- 稽核欄複驗實作（本刀僅做 FR-B08 確認；B-078 關帳後紀律居 RUNBOOK §9）。
- `sys_casbin_policy_archive` 歸檔表 retention（B-016 射程）。
- 首登強制改密（B-134）、demo 資產去留（B-018）等他刀條目。
