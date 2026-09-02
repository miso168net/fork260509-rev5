# Research — 008 稽核中心與系統設定頁（Phase 0）

> 偵查＝三支唯讀並行 workflow（rev5 rust-api 深查／rev5 tools＋base-web／rev4 補遺；
> runId wf_c6edbcad-143、3/3 ok）＋主線 grep 復核（GeoIP 取態、BizData 射程字面）；
> 疊加 brainstorm 期五支盤點（runId wf_b8139ddb-0e8）。行號＝2026-09-01 量測快照、
> 實作期以 grep 現況為準。

## R1. rev4 對應碼清單（ADR 0019 凍結；`../fork260509-rev4/` 絕對唯讀）

**後端藍本**：
| rev4 檔 | 用途 |
|---|---|
| `rust-api/server/src/handler/audit.rs`（1482 行） | 五端點全形：query DTO（Option<String> 寬鬆）、normalize_page、四讀端＋enrich、purge 守門固定序＋單交易自記、mod tests 14 支＋endpoint_tests 5 支（測名清單＝recon 報告 §3） |
| `rust-api/server/src/model/audit_query.rs` | 共用查詢建構（時間 RFC3339 閉開、人員過濾 id 優先／名含軟刪全集、ILIKE 字面化）＋`mask_pii_payload`（:196-212、深度一層、user_phone/user_email 兩鍵）＋三支表驅動測 |
| `rust-api/migration/src/`（rev4:m009 稽核管理批） | pg_trgm 索引＋seed 追加（★rev5 皆已預埋於 m001/m002、僅參照不重做） |

**前端藍本**：
| rev4 檔 | 用途 |
|---|---|
| `base-web/src/views/manage/audit/index.vue`（541 行） | 四分頁主頁：四組 useNaivePaginatedTable、欄定義、快照 dialog、purge 入口 |
| `…/audit/modules/audit-search-{operation,access,login,session}.vue` | 四搜尋卡（label 走分頁樹＋common、placeholder 走 form.*） |
| `…/audit/modules/audit-purge-modal.vue`（96 行） | MIN_DAYS=30、NPopconfirm 二段確認、emit 'submitted'、開啟重置 |
| `…/audit/modules/use-audit-search-date-range.ts`（59 行） | daterange→UTC ISO、reset 快照回填＋emit search |
| `base-web/src/views/manage/system-settings/index.vue`（230 行） | 資料驅動控件、四組分區、labelKeyMap/helpKeyMap 16 鍵、逐項存恆 refetch |
| `base-web/src/{service,typings}/api/rev4-audit.*` | 5 fetcher＋DTO 命名（★rev5 開 `Api.Audit` 獨立、不照抄併入形） |
| i18n：zh-cn.ts:768-844／en-us.ts:772-850（page.manage.audit、57 葉）＋settings 樹＋biz.audit 兩鍵（zh-cn/en-us:102-105）＋throttleNote 逐字 | 兩語重打字來源（rev4 三語、rev5 兩語） |

**rev5 拍板差異點（spec §3 六條＋研究期新增一條）**：
1~6＝spec §3（XFF 渲染／op-log DTO 欄名對齊 rev5 schema／access 空表／i18n 兩語／
`Api.Audit` 獨立／PII 打碼自建）。**7. routes.ts 條目＝生成器兩欄形**（title＋i18nKey；
rev5 先例 ip-rule/policy-archive；rev4 settings 條目之手改 icon/order/roles 不帶回——
dynamic 模式下選單由 seed 下發、零行為差）。

## R2. rev5 起跑線關鍵事實（檔位＝recon 報告；此處只列決策承重項）

- **分頁信封既在**：`envelope::PageRes<T>{current,size,total,records}`（envelope.rs:118-125、
  憲法 §I.3 字面）；007 先例＝`Res<PageRes<Record>>`＋clamp [1,100] 預設 10。
- **facade 缺口**：三日誌 facade 皆零清單讀端（op-log 僅 write_in_txn；login_attempt 僅
  insert＋節流計數；session_event 僅 insert）；**sys_access_log 連 facade 檔都無**。
- **enrich 底座現成**：`sys_user::user_names_by_ids`（不濾軟刪）＋
  `common::resolve_operator_names` 直接複用。
- **session_event rev5 表＝8 欄、與 rev4 同形**（單欄 `source_ip varchar(45)`、有
  created_by）——rev4 SessionEventDto 形可直接對映、enrich 兩欄批查。
- **PII util 無**：全樹零 mask/pii/redact 命中——照 rev4 重寫（D3）。
- **BizData**：`AppError::BizData(Cow, Value)`（error.rs:67）＋`Res::from_err_with_data`；
  現有構造點恰二（user.rs:526/:541、頂層鍵 `violations`／`remainingSeconds`）；
  ★**doc 載射程嚴限密碼二鍵（ADR 0064）**→ 本刀擴一鍵須 ADR 承載（D4）。
- **測試件**：`test_db`（model/mod.rs）之 `test_state`／`real_app_and_state_with`（不收
  db）／`real_db_single_with_lock_timeout`／`TableLock`（★白名冊 `LOCKABLE_TABLES` 現僅
  `["system_settings"]`）；b056 七步形＝`refresh.rs:1586`（單連線池→TableLock→直呼私有
  fn→先釋鎖後斷言→旁證另開連線→降級字面三連斷言）。
- **GeoIP 整包不進場**（middleware/mod.rs:37 檔頭逐字）：`region`／`trace_id` 全稽核面
  恆 NULL——audit 頁該兩欄照 rev4 渲染、值恆「-」＝已知態（驗形不驗值）。
- **Lint24**：兩腿＋34 自測；`parse_locale_backend` 現只取鍵集（第三腿需留值 dict）；
  `scan_backend_msg_keys` 需擴 BizData 視窗抓 `json!({...})` 頂層鍵；en-us backend 樹另由
  msg-dict 兩語鍵集斷言涵蓋（MSG_DICT_LOCALES＝zh-TW＋en-US）。
- **i18n 插入錨**（量測快照）：route: 樹＝zh-cn.ts:410 後／en-us.ts:414 後（`'multi-menu'`
  前）；page.manage 節尾＝zh-cn.ts:942/943 間、en-us.ts:937/938 間、app.d.ts:1106/1107 間；
  zh-tw.ts `biz.audit` 依字母序插 :57/:58 間（`auth` 前）。
- **seed-view-gate**：EXEMPT 摘兩列必同批改 self-test 案 I-a 鍵集釘（:364-369）＋檔頭
  「恰兩列」敘述；I-b/c/d 三根不動。
- **route meta 生成**：`onRouteMetaGen` 只產 title＋i18nKey；產物四檔外掛重算＋
  route-artifact-gate 三道斷言。
- **contract／router 形**：RouteDef 逐字形＋`ROUTES_COUNT=61`（router.rs:740、斷言
  :1013-1018）；ContractCase 登記形（contract.rs:118-121）。

## R3. 決策集（Decision／Rationale／Alternatives）

- **D1 分頁信封**：複用 `envelope::PageRes<T>`、各讀端一個逐欄白名單 Record struct。
  Rationale＝憲法 §I.3 字面＋全樹零例外先例。Alt（Api.Audit 自帶 ListRes）棄——重複發明。
- **D2 讀端佈局**：照 rev4 立 `model/audit_query.rs` 對應物（時間閉開／人員過濾／ILIKE
  字面化共用）＋各表 facade 加分頁讀 fn、`sys_access_log` 新建 facade 檔。Rationale＝
  rev4 驗證過的單一查詢建構點；Alt（handler 內散裝 SQL）棄——違 facade 慣例。
- **D3 PII 打碼**：照 rev4 重寫 `mask_pii_payload`（深度一層、`userPhone`／`userEmail`
  兩鍵、非字串原樣）（★鍵風格＝rev5 寫端 camelCase——`facade/sys_user::audit_json` 逐字落 `"userPhone"`／`"userEmail"`；rev4: 之 `user_phone`／`user_email` 屬差異點、不帶回〔ADR 0019〕。★照 snake_case 實作則打碼對生產 payload **恆不生效**）＋三支表驅動測＋端到端負向自證（拆呼叫即紅）。Alt（不打碼）棄——
  rev4 拍板承襲、op-log payload 含 user 域 PII。
- **D4 BizData 射程擴一鍵＝ADR 承載**：`biz.audit.purgeBelowFloor{minDays}` 入 BizData
  射程——實質已由 grilling 拍板③親決（第三攜參鍵）；形式＝**U0 立補充 ADR**（補充
  ADR 0064 射程清單、不 supersede；error.rs doc 同批改對）。Alt（minDays 寫死譯文）已於
  grilling Q3 選項③棄——雙源字面漂移形。
- **D5 fault-injection 面**：`_with_db` 薄殼（收 db 的 `real_app_and_state_with` 變體、
  沿用 test_state、不新增 AppState 建構字面）＋`LOCKABLE_TABLES` 擴 `sys_operation_log`
  （鎖自記表使 INSERT 逾時→斷言整筆回滾＋錯誤＋零刪除零自記）；測形照 b056 七步
  （優先直呼 handler fn、extractor 不可構造才走 app 打端）；logout TTL 同形補測同批。
  Rationale＝B-125 拍板④＋b056 已驗證形。
- **D6 Lint24 第三腿**：新純判定函式（仿 check_locale_key_parity）＋接線於
  lint_i18n_contract＋self-test 紅綠樣本；資料面＝`parse_locale_backend` 留值 dict、
  佔位符掃 `\{(\w+)\}`、後端側 `scan_backend_msg_keys` 擴 BizData 視窗抓 json! 頂層字面
  鍵（非字面形 fail-loud）；同腿併驗 zh-cn／en-us 佔位符集＝zh-tw（spec FR-H01）。
- **D7 routes.ts meta**：生成器兩欄形、零手改（差異點 7）。
- **D8 i18n 規模**：page.manage.audit 兩語各 57 葉＋page.manage.systemSettings 兩語各
  36 葉（4 titles＋16 items＋16 help）＋route: 兩鍵×兩語＋app.d.ts 兩型節；backend
  `biz.audit` 兩鍵×三檔（zh-tw／zh-cn／en-us）**與 rust 構造點同 commit**（否則 Lint24
  孤兒鍵紅）。
- **D9 DTO 對映**：session_event 照 rev4 形（單欄 sourceIp）；op-log 對齊 rev5 欄名
  （`realIp`／`peerIp`／`xForwardedFor`／`ipConfidence`；`region` wire-only）；三表 XFF
  上 wire、UI 三分頁渲染（ADR 0076）。
- **D10 已知態三筆**：access 分頁空表（B-016）；`region`／`traceId` 值恆「-」（GeoIP／
  trace 中介層不進場、寫入面既定取態）；login 分頁節流短路不落表（throttleNote 告示）。
  CDP 對照皆驗形不驗值。
- **D11 seed-view-gate 摘列連動**：EXEMPT 兩列＋I-a 釘＋檔頭敘述三處同批（R2 所列）。
- **D12 contract cases**：5 支照 `get-system-settings` 形（Policy 未認證 8888 免 DB
  oneshot）；coverage gate 自動要求（每 route 必有 case）。

## R4. spec §5 開放項歸零

| 開放項 | 歸零 |
|---|---|
| session_event rev5 表形 | R2＝8 欄與 rev4 同形；DTO 照 rev4（D9） |
| PII mask 等價物 | 無→自建（D3） |
| audit handler 測試形 | rev4 19 測名清單（R1）＋rev5 三層先例＋b056 七步（D5） |
| settings 16 鍵互鎖 | SEED_EXPECTED 16 鍵逐字核實＝rev4 同鍵集；registry 界值表在；零後端改動確認 |
| purgeBelowFloor BizData 形 | 構造點形＋射程 ADR 事項（D4）；Lint24 錨＝構造點集（D6） |
| contract query 零判別力 | 既知限制照記（spec FR-A07）；B-030 殘項不擴 |
