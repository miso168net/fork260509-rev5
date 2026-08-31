# 008-audit-settings-pages — B-008 餘兩張管理頁＋audit 五端點

> 階段 0 brainstorm **定稿（2026-09-01）**。基準＝rev5-admin-root @ 4b49f15；pins
> base-web=b827063／rust-api=515177e；憲法 1.9.1；ROUTES_COUNT 61；rust 容器測試 1015；
> seed-view-gate 豁免表恰餘兩列（本刀射程）。
> 偵查＝五支唯讀並行 workflow（rev4 audit 前端／rev4 settings 前端／rev4 audit 後端＋casbin seed／
> rev5 rust-api／rev5 base-web），5/5 ok 零 blocked；承載拍板之事實已由主線復核（004 research
> access_log_mw 列、seed 五列、EXEMPT 兩列皆 grep 實證）。
> ★拍板 2 題已以 AskUserQuestion 親決（2026-08-31）：①access 寫入面取建議案（不入本刀）、
> ②XFF 渲染取**非建議項**（rev5 加渲染、偏離 rev4）；整體設計核可 2026-09-01。
> ★grilling 輪（grill-with-docs＋domain-modeling、2026-09-01、AskUserQuestion 逐題）4 題親決、
> 皆取建議案：B-139 納（Lint24 擴腿）／B-125 納（purge fault-injection＋`_with_db` 薄殼）／
> B-078 本刀確認後關帳／B-143 不納——詳 §1b；BACKLOG 全卷掃描紀錄＝§1c；frontier 已空。
> 本檔自此為 speckit-specify 的直接輸入（specify **手動**起手、不入自動流程）。
> 血緣：BACKLOG B-008 條目全文（as-built 以該條為準、非 ADR 0018 字面）＋B-072／B-078＋
> ADR 0018（settings 接線層先行、view 延本刀）＋ADR 0028／憲法 §III.2（軌道既有、走加用途）。

## §0 地基：與本刀決策相關的事實

**契約凍結面（001 seed、本刀零新政策列）**：casbin endpoint 維已預埋恰 5 列＝本刀 5 支新端點的
path×method 凍結契約——`/systemManage/getOperationLog`／`getAccessLog`／`getLoginAttempt`／
`getSessionEvent` 皆 GET、`/systemManage/purgeAuditLog` POST（`m002_baseline_seeds.rs` 列
139/140/141/158/159、全 R_SUPER、protected=FALSE）；menu 維 `manage_audit`（列 142）／
`manage_system-settings`（列 69、protected=TRUE）；**button 維兩頁皆零列**（門在頁級、零按鈕碼
gating）。sys_menu：列 9＝settings（component `view.manage_system-settings`、icon `mdi:cog`、
order 1、protected TRUE）、列 77＝audit（component `view.manage_audit`、
icon `mdi:clipboard-text-search-outline`、order 6）。與 rev4 audit 端點實碼逐字對齊（第一查核點✅：
rev4 router 恰同 5 支、方法一致）。

**rev4 audit 藍本（`../fork260509-rev4/` 唯讀）**：★實為**四源四分頁**（operation／access／login／
**session**）、非帳面舊述「三張表」——第四源 `session_event` 於 rev5 已存在且寫入面活躍
（login／logout／refresh／踢除）。前端 7 檔形（index.vue 541 行 NTabs 四分頁＋4 支搜尋卡＋
purge modal＋daterange composable）；搜尋卡同構（NCollapse 預設展開、reset 清 dateRange 補
emit search、時間 wire＝`timeFrom`/`timeTo` UTC ISO）；op-log 快照走 `$dialog.info`＋`<pre>` 純文字
JSON；零匯出、前端零 sorter（後端固定 `created_at DESC, id DESC`）、pageSize 10。後端 handler
（audit.rs 1482 行）形：分頁 current≥1、size clamp [1,100]；query 參數全 `Option<String>`
（rev4:L-090 防 axum Query 空字串 400）；operator 名 enrich＝第二發批查不 join；時間過濾 RFC3339
閉開 `[from,to)`、畸形＝未設、顛倒＝空頁；op-log 讀出端 `mask_pii_payload` 恰一處；purge 守門固定
序＝table 四值白名單→beforeDays≥30（`PURGE_MIN_DAYS`）→單交易水平線 DELETE（op-log 版帶
`operation <> 'PURGE'` 豁免）＋同交易 PURGE 自記。★rev4 前端**不渲染** `x_forwarded_for`
（DTO 有、四表 columns 無、整頁零 v-html）。

**rev4 settings 藍本**：單檔 index.vue（230 行）；控件**資料驅動**（settingType 二值 enum→NSwitch、
number→NInputNumber、其他→唯讀 span）；四組分區固定序（password_*／session／ip_*／
login_throttle_*、未列鍵排組尾）；**逐項即改即存、恆 refetch server 真值**（無整頁儲存、無 dirty
檢查；NInputNumber 清空不送、refetch 回退）；16 鍵；label/help 走 typed literal 映射、未映射
fallback description；零按鈕 gating（R_SUPER only、門在頁級＋後端）。

**rev5 起跑線**：audit 端點零支（`ROUTES_COUNT` 61→66 同 commit bump）；settings 後端兩支＋
`rev5-settings.ts`/`.d.ts` 接線層已備（002／ADR 0018，16 鍵 GET＋三態 POST）——settings 頁純
「view 接上即用」。三稽核表 schema 在（★rev5 `sys_operation_log` 14 欄：欄名**無 `operator_`
前綴**且**多 `region`**，與 rev4 13 欄不同）；`idx_access_log_path_trgm`／
`idx_login_attempt_user_name_trgm` 兩支 pg_trgm GIN rev5 m001 已預埋。★`sys_access_log` 現為
**零寫入空表**（middleware 從未搬入；004 research 已裁 `access_log_mw` 不搬、歸 B-016 射程）；
`sys_login_attempt`／`sys_operation_log`／`session_event` 寫入面皆活躍。XFF 建構點淨化＝
rightmost 判定窗＋零 CR/LF＋≤1024 字元（`request_context.rs`、不剝 HTML）。wire_schema 裁判形＝
`Api.IpRule` 節先例（definition 正反例成對、值域接真源常數）；`seed-view-gate.py` EXEMPT 恰餘
本刀兩列、**view 兌現同刀必摘否則 gate 紅**；`view-render-guard.py`（7 條禁字面、掃
views/manage 全樹含註解、pre-commit）常駐。前端：manage 子樹現有 6 route、兩頁 route 條目與
i18n 鍵**皆不存在**（煙測已知態＝側欄點擊零反應＋顯示原始 i18n key；直打網址才 404——兌現後
反轉為正常進頁）；產物四檔由 elegant-router vite 外掛重算＋route-artifact-gate 三道斷言；
「管理頁進場」先例＝ip-rule 刀（12 檔 +924：兩語 locale＋app.d.ts＋產物四檔＋service/typings
新檔＋views 三檔）；service 慣例＝`rev5-<domain>` 新檔不入 barrel、004 起新 domain 開獨立命名
空間；接真後端零 env 改動（nginx `/api/` 萬用塊已涵蓋）。

## §1 拍板決議

**拍板①（user 親決、取建議案）：`access_log_mw` 不入本刀**——沿 004 research 既有拍板
（不搬、歸 B-016 稽核域射程）。本刀維持「兩張 view＋5 端點」邊界；`getAccessLog` 讀端照做但
讀到空表、audit 頁 access 分頁空列表（NEmpty）＝**已知態寫入 spec**（CDP 對照驗 UI 形、不驗
資料量）；B-016 條目補註「寫入面 access_log_mw 在其射程」已隨本檔同 commit 落地、防帳面斷鏈。

**拍板②（user 親決、取非建議項）：audit 頁渲染 `xForwardedFor` 欄（偏離 rev4 UI）**——
operation／access／login 三分頁加該欄（session_event 無此欄、第四分頁不加）；B-072 以
「渲染＋轉義就位」對帳關單。此為 UI 對照唯一例外、承載＝**ADR 0076**（渲染形、驗收例外註記、
翻案形皆入該 ADR）。

**自拍工程項（回報備查）**：四源四分頁照 rev4（三張表說法＝帳面舊述）；purge 端點照做（seed
凍結；B-016 之 reaper 自動面不併）；wire 命名空間開獨立 `Api.Audit`（004 起先例、不併
Api.SystemManage——rev4 係併入、rev5 拍板差異）；DTO 欄名對齊 rev5 schema；XFF 欄顯示採
ellipsis＋tooltip 純文字形、scroll-x 不變式隨欄寬總和同批改；其餘 DTO 有而 rev4 不渲染的欄
（peerIp／ipConfidence）維持不渲染、偏離最小化；i18n 兩語（zh-cn／en-us；zh-tw.ts 孤立治理錨
不動、rev4 三語不帶回）；B-078 處置＝拍板⑤（§1b；grilling 輪推翻初稿「續掛」案）。

### §1b grilling 輪拍板（2026-09-01、AskUserQuestion 逐題親決、皆取建議案）

**拍板③：B-139 納入本刀**——本刀照 rev4 藍本新增 `biz.audit.purgeBelowFloor` 攜 `{minDays}`
＝**第三個攜參鍵**、B-139 觸發器字面成立；處置取條目候選①＝Lint24 擴一腿（解析 zh-tw 譯文
`{ident}` 佔位符集、與後端 `BizData` 構造點 `json!({...})` 頂層鍵集比對，住
`tools/docs-sync.py`、自測正反例）；B-139 隨本刀關帳。

**拍板④：B-125 納入本刀**——purge＝破壞性 DELETE＋同交易自記，原子性做 fault-injection 級測
（TableLock＋單連線 lock_timeout 池注入故障→斷言整筆回滾＋錯誤回傳＋零刪除零自記、非
vacuous）；為此建 `real_app_and_state_with` 之 `_with_db` 薄殼（沿用 test_state、不新增
AppState 建構字面）＝B-125 自訂翻案條件「第二個注入 db 的測試需求」成立；logout TTL 同形補測
同批落；B-125 隨本刀關帳。

**拍板⑤：B-078 本刀確認後關帳**——本刀四支讀端零複驗入口、realIp 搜尋＝精確等值
（/32、/128）比對非 LIKE 字串包含（httpPath／userName 之 ILIKE 為一般文字欄模糊搜、非對 IP
欄），確認句入 spec 驗收面；紀律本體已居 RUNBOOK §9 永久家、收刀即刪列。

**拍板⑥：B-143 不納**——本刀 Amendment 只加用途 (vii)(viii)、不擴用途 (v) 名單；B-143 觸發器
字面未命中（本刀非「擴 (v)」亦非「動 user 搜尋面」），且其三處置候選自身是未決 UI／契約拍板
題、非順帶量級；觸發器保留。

### §1c BACKLOG 全卷掃描紀錄（grilling 輪、兩卷 26 條逐條）

命中納入＝B-139／B-125；命中關帳＝B-078；邊界不納＝B-143（以上 §1b）。近距離不納各一句：
B-082＝本刀 realIp 讀端走**等值**比對、吃既有 btree `idx_login_attempt_ip_time`，`<<=` 無索引
問題屬節流計數路徑、本刀不碰；B-030 之「契約測試對 query 零判別力」＝本刀 4 支 GET contract
case 同受此限、spec 註記為既知限制（非「重寫對應模組」不觸發）；B-145＝triage 已判
needs_sdd、獨立刀之 brainstorm 輸入；B-016 射程已由拍板①界定；B-018／B-027／B-131 等餘條
皆不觸發（demo 面／排序需求／menu 域）。domain-modeling 兩筆接地：`PURGE_MIN_DAYS=30`＝
B-016 逐表門檻設計時必須鏡像的下限（rev4 reaper `AUDIT_RETENTION_*` floor 30 即鏡像 purge
floor 的先例形）；術語固定＝「四源四分頁；XFF 渲染義務射程恰三表（session_event 無此欄）」。

## §2 範圍

**In**：
- 後端：5 支 audit 端點（照 rev4 藍本＋§3 差異點）；`Api.Audit.*` wire_schema 裁判＋contract
  case registry＋ROUTES_COUNT bump；purge 之 `PURGE_MIN_DAYS=30` 與 i18n 拒因鍵
  （`biz.audit.invalidTable`／`purgeBelowFloor` 攜 `{minDays}`）；purge 原子性 fault-injection
  測＋`_with_db` 薄殼＋logout TTL 同形補測（拍板④）。
- 工具：Lint24 擴腿＝zh-tw 譯文佔位符集 × 後端 `BizData` 頂層鍵集比對（拍板③）。
- 前端：settings 頁（單檔、資料驅動、四組、逐項存；接既備接線層、後端零改動）；audit 頁
  （四源四分頁 7 檔形＋XFF 欄）；新檔 `rev5-audit.ts`／`rev5-audit.d.ts`；兩語 locale
  route:/page: 樹＋app.d.ts page 型節＋產物四檔重算。
- 修憲（本刀 U0）：§III.2 `BASE-WEB-MANAGE-PAGE-WIRING` 加用途 (vii)(viii)（兩頁進場、形照
  (i)/(iv) 先例）；行為島候選＝audit purge 域（30 天下限／單交易自記／PURGE 豁免／四值白名單）
  ——是否入憲屆時依憲法 §IV 判、user 親決。
- 關帳（六條）：B-008 關；seed-view-gate EXEMPT 摘兩列；B-072 對帳關（ADR 0076）；B-139 關
  （Lint24 擴腿落地）；B-125 關（薄殼＋兩支測落地）；B-078 關（確認句入 spec 驗收面）。

**Out**：`access_log_mw` 寫入面與 retention／reaper 自動面（皆 B-016）；匯出／前端排序／快照
內容搜尋（rev4 亦無）；B-143（觸發器保留、拍板⑥）；B-016 歸檔表 retention。

## §3 rev5 拍板差異點（ADR 0019：plan research 必列、此為起點）

1. XFF 三分頁渲染（rev4 不渲染）——ADR 0076。
2. DTO 欄名對齊 rev5 schema：op-log 欄無 `operator_` 前綴＋多 `region`（rev4 DTO 之
   `operatorRealIp` 家族形不帶回）。
3. access 分頁空表＝已知態（rev4 有資料；寫入面 B-016）。
4. i18n 兩語（rev4 三語；zh-tw.ts 不動）。
5. wire 命名空間 `Api.Audit` 獨立（rev4 併入 `Api.SystemManage`）。
6. op-log 讀出端 PII 打碼：rev4 `mask_pii_payload`——rev5 等價物待 spec research 確認
   （見 §5）。

## §4 驗收判準

- CDP 三方對照（42080 rev4 vs 22080 rev5；XFF 欄＝唯一例外註記、依 ADR 0076）；真登入走查
  前後各跑 `walkthrough-baseline.py snapshot`／`diff`（RUNBOOK §9c 六步）。
- 煙測判準反轉：側欄點兩項由「零反應＋原始 i18n key」變「正常進頁」（★判準用側欄路徑、
  非直打網址之 404——B-008 條目 2026-08-17 更正）。
- B-078 確認句：四支讀端零複驗入口、realIp 過濾＝精確等值非 LIKE（拍板⑤、入 spec 驗收面）。
- 容器全量 serial 綠＋三閘＋`seed-view-gate` 綠（EXEMPT 已摘）＋`view-render-guard` 綠＋
  `route-artifact-gate` 冪等綠＋fork-delta-lint 綠。

## §5 開放項（spec research 去解、不擋本檔定稿）

- `session_event` rev5 表逐欄 schema（讀端 DTO 對齊；rev4 SessionEventDto 有 `sourceIp` 單欄，
  rev5 表形待核）。
- rev5 有無現成 PII mask util（rev4 `mask_pii_payload` 對應物；無則隨刀重打）。
- audit handler 測試形：沿 002／007 三層先例（handler 內真 DB 測＋contract case＋wire_schema
  裁判）之具體案面。
- settings 16 鍵 seed×validation registry 互鎖 002 既備、view 只消費——spec 確認零後端改動
  即可收。
- `purgeBelowFloor` 之 `BizData` 變體承載形（007 已建通道、樣例＝`passwordPolicy{violations}`）
  ——spec research 確認構造點形；Lint24 擴腿（拍板③）的掃描面即以該構造點集為錨。
- 本刀 4 支 GET contract case 對 query 參數零判別力＝既知限制（B-030 殘項）、spec 註記。
