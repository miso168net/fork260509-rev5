---
id: "0024"
title: 守門機制必附非 vacuous 生效自證——合成正例＋判準來源獨立＋落地破壞性驗證
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "002-system-settings final holistic review 後 user 拍板 2026-08-08；背景＝該刀六起『守門機制抓不到它存在理由所要抓的東西』（逐條列名於該刀 feature_close 事件 notes）＋主線於 FHR 修訂期自撞同型第七次（rust-api commit fce6542 載明實測）；姊妹教訓＝LESSONS L-010"
tags: [governance, testing, lint, gate]
---

## 背景

002-system-settings 一刀之內，「守門機制抓不到它存在的理由所要抓的東西」共發生六起——
每一起的閘都在、都綠，保護卻不在：

1. **動詞閘驗 ⊇ 而非 ＝**（`rust-api/server/tests/contract.rs`）：原形只驗「打宣告動詞→
   非 405」（rev4:contract.rs 的動詞驗證即此單向形），`handler: || get(list).post(create)`
   多掛一個未宣告動詞時完全無感——多出來的 POST 用 GET 的政策放行（寫入吃讀取政策）。
   終態＝`routes_method_column_matches_handler_dispatch_verb` 逐條裸掛探測、斷言實收動詞集
   **恰等於**宣告值。
2. **entity_access_lint 不遞迴子目錄**（`rust-api/server/tests/entity_access_lint.rs`）：
   平面掃描下受掃層的子目錄檔根本不被讀，漏抓靜默；「層」是子樹不是平面目錄。
3. **entity_behavior_lint 頭部錨定被完全限定路徑繞過**
   （`rust-api/server/tests/entity_behavior_lint.rs`）：判頭只認裸形，
   `impl sea_orm::entity::prelude::ActiveModelBehavior for ActiveModel` 整個站點不入
   sites、主守恆靜默漏抓（U15 review 實測：新增檔＋限定路徑形＝六案全綠）。
4. **contract case_key 與 path 之間毫無綁定**（`rust-api/server/tests/contract.rs`）：
   registry 的 case_key 與驗證函式實打的路徑原無任何強制關聯，鍵與驗證函式錯配照樣全綠
   ——實際測的是別的東西。終態＝驗證函式收 path 參數、由 ROUTES 依 case_key 查出後傳入。
5. **entity_behavior_lint 的字面檔數下限在表增長後失效**：首版以字面 15 為 impl 站點下限
   （當時恰 15 張表）——判頭對某形失效少抓一站，今日 14＜15 尚能紅，增一張表後同一失效
   變成 15≥15、兩道斷言全綠。終態＝站點數恰等於帶 `DeriveEntityModel` 的表 entity 檔數
   （等式由掃描面另一獨立性質導出、非字面常數）。
6. **憲法 §II #1 未知標頭全等斷言只覆蓋未認證腿**：contract.rs 的「帶 apifoxToken 與
   不帶者全等」在 enforce_mw 的 authn 層即 early-return 8888、handler 永不被觸及；而
   base-web 的 request 實例對每個請求都掛 apifoxToken，正式流量走的恰是帶 Bearer 的
   已認證腿——判定鏈後段若長出依賴未知標頭的分支，舊斷言完全無感。終態＝
   `rust-api/server/src/handler/system_settings.rs` 補
   `unknown_header_ignored_on_authenticated_leg_byte_equal`（status／headers／body byte
   三面全等＋釘住基準腿 code=0000 且 data 16 列，防退化為未認證腿重複）。

★第七次＝主線自撞：FHR 修訂期把 entity_access_lint 掃描面反轉為排除制時——亦即**已經
修過上列五起、正在修第六起、明知這類病灶存在**的當下——首版完整性斷言寫成「全樹檔數 −
排除面檔數 ＝ 受掃檔數」的數量等式。等號兩邊都由同一份排除清單導出：「排除面 += handler」
時受掃數減少、排除數等量增加、兩邊同步變動，實測判**綠**（rust-api commit fce6542 載明；
終態＝結構斷言：排除面恰等宣告值＋關鍵層代表檔逐檔指名在面內）。

六起加一次自撞共同指向：閘的「存在」與閘的「生效」是兩件事，且「知道有這類坑」不足以
避免再寫出一個——生效必須有機器面的自證程序。判準面的病理拆解見 LESSONS L-010
（判準對被判對象的變動結構性無感＝恆綠；四種致因＝同源／寫死基數／單向包含／無綁定）。

## 決定

本紀律是 `docs/arc42/ARCHITECTURE.md` §4「每條慣例必附守門機制」規則鏈的下一段：
慣例要有閘，閘本身要有生效自證。

新設守門機制（含修改既有機制的判準、掃描面、覆蓋面）時，必須連帶交付「生效自證」，
三項具體要求：

1. **閘內自帶自動化合成正例**：構造一個應被攔下的違規形，斷言偵測器確實攔得住（且紅訊息
   指名違規處）。此測試進自動化測試面、每次全量測試都跑（rust 側＝容器內 serial cargo
   test；傘狀工具側＝該工具 `test` 子命令自測、pre-commit 於工具本體 staged 時連帶跑；
   rev5 現況零 CI＝ADR 0014，日後 CI 母體立案後自動涵蓋）——閘的偵測能力從此有迴歸保護。
2. **判準結構化且與被判對象不共變**（詳 L-010 三條防法）：判準的兩邊不得由同一個會隨
   違規**同步移動**的量導出（同一份排除清單、同一個計數——違規發生時兩邊等量移動、
   恆等即恆綠）。★共變性須**逐違規類型**判斷，不可對一個判準整體貼「安全」標籤：
   同一個等式常對某類違規敏感、對另一類無感。實例＝entity_behavior_lint 的
   「impl 站點**總數** ＝ 帶 `DeriveEntityModel` 的表 entity 檔數」——兩邊同掃一棵樹，
   但由互相獨立的謂詞導出，故對「判頭對某種寫法失效而少抓一站」與「某檔漏了該 impl」
   只動站點數一邊、等式即紅；然而對「掃描面漏掃整支檔」，該檔的站點與 `DeriveEntityModel`
   一起消失、兩邊同步各減一，等式照樣成立——**對那一類無感**，須另配一條斷言
   （掃描面結構恰等宣告值／關鍵項逐檔指名）補上，兩者不可互替。
   結構斷言（集合恰等宣告值、關鍵項逐項指名）優先於數量斷言（總數、下限、等式）。
3. **落地當下至少跑一次真檔暫改的破壞性驗證**：暫改真檔造出違規→閘須紅**且訊息指名是哪裡
   壞**→還原→復綠，實跑輸出的關鍵行**寫進 commit message** 留證。此為一次性人工程序、
   不進自動化測試面（合成正例管長期迴歸，真檔暫改管「落地那一刻閘真的接上了實際掃描面」
   ——兩者驗的失效面不同、不可互替）。

## ★射程

**射程＝守門機制**——存在理由是「攔下違規形」而非「驗證業務行為」的那些。判準以本句
**意圖定義**為準；下列僅為落檔當日的非窮舉現況清單，日後新增的機制凡符合意圖定義即
自動入射程、毋須有人記得回來擴列——列舉式射程本身正是本 ADR 所譴責的 allowlist 恆綠形
（`entity_access_lint.rs` 的 `scan_root()` doc 對「allowlist 下新增模組自動落在閘外」
有完整論證，router.rs 當初即因此漏掃）：

- rust 側：`rust-api/server/tests/` 下的 lint 閘（現況＝`*_lint.rs` 兩支）、
  `contract.rs` 的雙向覆蓋閘與 ROUTES 全表不變式、`wire_schema.rs` 的 wire 契約快照
  裁判；以及**住 `src/` 內**、以憲法／契約條文為守恆對象的斷言（如
  `handler/system_settings.rs` 的 `unknown_header_ignored_on_authenticated_leg_byte_equal`
  ——憲法 §II #1 之閘）；
- 傘狀 `tools/` 下的治理 lint 與閘：docs-sync／schema-gate／entity-drift-gate／
  wire-schema／fork-delta-lint；
- pre-commit 與 pre-push 防線。

**不在射程**＝一般業務單元測試與整合測試。那些測的是「程式行為對不對」，不是「守門有沒有
效」；它們照常走 TDD 的紅→綠（先寫失敗測試再實作，本身就含一次「見紅」），不另外要求
破壞性自證。把本紀律攤到全部測試上會讓成本失控且毫無對應收益——本節即為防這種誤用而寫。

## 已符合本 ADR 的 in-repo 樣板

- 要求①之形：`collect_skips_excluded_dirs`（entity_access_lint.rs——合成 keep／drop 兩支
  同構子樹，證排除機制本身真的跳過、非被實作忽略）；
  `contract_case_key_binding_detects_mismatched_verify`（contract.rs——逐 case 把驗證函式
  配到外來 path、須紅，實打自證而非讀碼推論）；
  `raw_request_builder_actually_carries_extra_header`（handler/system_settings.rs——
  釘死「探針真的帶著該標頭」的前提，前提失效時全等斷言比的是空殼卻無從察覺）。
- 要求②之形：`scan_is_non_empty`（entity_access_lint.rs）現行的結構斷言——排除面恰等
  宣告值＋關鍵層代表檔逐檔指名，替換掉被實測擊穿的數量等式。
- 要求③之形：rust-api commit fce6542 的三項負向自證實跑——seed 值改 99999→互鎖案紅並
  指名 session_idle_timeout；build_get_request 的 extra 迴圈短路→前提自證案紅
  （left: None／right: Some("unknown-header-probe")）；排除面 += handler→結構斷言紅並
  印出左右兩清單。
- 傘狀側同精神先例：`tools/fork-delta-lint.py` 每次執行先 self-test 防恆綠；docs-sync
  Lint25 亦內建 self-test registry。既有閘**不要求回補**（見下節），但新改動觸及其判準時
  適用本 ADR。

## 後果與取捨

- **成本（誠實列出）**：每個閘多一至數份自證測試——002 六起補完後（落檔當日實測），
  `entity_access_lint.rs` 主守恆之外帶十個防線測試、約佔五分之二檔幅，
  `entity_behavior_lint.rs` 帶五個、約佔六分之一檔幅；落地多一輪真檔暫改的手動驗證，
  commit message 變長。這是真實的持續性成本，不是一次性的。
- **為何值得**：六起加一次自撞即為代價證明——每一起都是「閘在、保護不在」，其中第七次
  發生在已修五起、病灶形態已完全明知之後。「靠人記得」在此已被實證不可靠，唯機器面程序
  可恃。
- **本 ADR 不保證什麼**：自證只證明閘能抓到**你想到的那個**違規形，抓不到你沒想到的——
  entity_access_lint 那一疊非 vacuous 防線正是逐次被 review 逼出來的，每道各擋一個先前
  沒想到的正交向量。本紀律降低恆綠風險，不消除它。
- **不溯及既往**：已落地的閘不要求專刀回補自證；後續任何刀觸及某閘的判準或掃描面時，
  該次改動適用本 ADR 全部三項要求。
