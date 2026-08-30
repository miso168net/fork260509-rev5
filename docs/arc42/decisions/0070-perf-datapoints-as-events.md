---
id: "0070"
title: pre-commit 效能資料點序列事件源化——events.jsonl 新增 perf 型別（Lint03／Lint18 驗形）、generate 產 reference/perf.md、STATE 效能引信機器判；RUNBOOK §12.1 射程收束為門檻語意／量測法／終態表／指針、ADR 0044 配套段之「記入本節資料點序列」承載處改為 append perf 事件；NOTES 已收官段刪除留指針；收刀程序增第四步
date: 2026-08-30
status: accepted
supersedes: []
superseded_by: []
provenance: "BACKLOG B-149（RUNBOOK 900／900 與 NOTES 40／40 兩檔零餘裕；007-user-password-admin 收刀當場再撞、收刀簿記型 9.97s 這筆因無空間寫不進 §12.1）；user 親決三題 2026-08-30（①事件源化＋立新 ADR＋0044 指涉改指新家 ②NOTES 已收官段整段刪留指針 ③時機＝下一刀起手維護批）、落帳 commit f1c0951；主線自決（欄位形／kind 值集／引信判準／回填法）已回報備查；落地＝下一刀起手維護批（B-146／B-147／B-148／B-149 同批）之 U1；訂正範式＝ADR 0067 對 ADR 0042 之處理形（決定不變、承載處改、以新文件為準）"
tags: [docs, governance, tooling, pre-commit, performance, events]
---

## 背景

`docs/ops/RUNBOOK.md` 於 007-user-password-admin 收刀時達 900／900 行（Lint07 上限）、
`docs/ops/NOTES.md` 同批達 40／40：兩個 ops 文件零餘裕，下一次寫任一份即紅。成長主力
是 RUNBOOK §12.1 的效能資料點序列——ADR 0044 的配套引信逐字要求「收刀簿記型 commit 的
實測值列為每刀例行量測、記入本節資料點序列」，每刀收尾必加一筆，而該序列的每一筆都帶
判讀散文（合成公式、歸因、與前批對照）。

三個事實讓「就地壓縮」不再是出路：

1. **配額壓力已開始吃掉治理機制自己要求的記錄**：007 收刀簿記那顆 commit 實測 9.97s，
   正是 ADR 0044 引信指定要記的那一筆，卻因無空間只能留在 B-149 條目與 commit message 裡。
2. **兩檔已各壓縮一輪**（B-149 候選②：08-08／08-16 兩批史料下放 git；NOTES 已收官段收成
   指針形），仍恰好撞頂——壓縮換到的是一刀的空間，成長形態沒變。
3. **NOTES「已收官」段是機器生成檔的人寫鏡像**：逐批列 merge SHA／ROUTES 終態／測試數，
   與 `docs/generated/MILESTONES.md`（事件表）和 STATE 尾 3 筆同源；CLAUDE.md §4
   「鏡像不是機器生成、就是不存在」明禁；README 對 NOTES 的定義逐字是「幾行」。

RUNBOOK 與活書不同——活書撞頂有「碼 doc」或附屬文件可下放（ADR 0062），RUNBOOK 的資料點
序列沒有天然的碼家；但它有一個更對的家：**它本來就是一條依日期 append 的量測序列**，形狀
與 `events.jsonl` 完全相同。事件帳新增型別屬拍板級（CLAUDE.md §5），故立本 ADR。

## 決定

### ① `events.jsonl` 新增 type `perf`——欄位與驗形

- required：`type`／`date`／`kind`／`wall_s`／`notes`；optional：`commit`／`rc`。
- `date` YYYY-MM-DD；`wall_s` 數值（int／float、非 bool）且 >0；`rc` int ≥0（非 bool）；
  `commit` 40 位 hex 字串；`notes` 非空字串、**不設長度上限、可含換行**（JSON 字串內合法；
  summary 欄的禁換行紀律不套用於 notes——判讀散文整段住此）。
- `kind` 值集＝docs-sync 常數 `PERF_KINDS`（Lint03 驗值域）：
  `close_bookkeeping`（收刀簿記型 commit 實測：events＋NOTES＋generated 那顆、零 gitlink
  零工具本體）／`doc_only`（文件型 commit 實測）／`pin_bump`（pin bump 型 commit 實測）／
  `merge`（merge commit 實測）／`baseline_chain`（情境 A 基礎鏈逐支中位數合計）／
  `full_chain`（情境 B 合計）／`synthetic`（合成推估、非實測——★引信永不採計）／
  `bench`（非本節標準量測法的對比量測：同一支 bench 前後對比、全鏈牆鐘粗判等；不可與序列
  混算）。四種 commit 實測的 kind 依 **staged 內容**分類（hook 自報牆鐘與 perf_counter 包
  整命令都算實測，量法寫進 notes）。
- `commit` 欄的語意＝**被量測的那顆 commit 本身**（Lint18 據此實證、`reference/perf.md` 以它為
  join 鍵）。「某顆 commit 之後才量的工具鏈」這種**量測時點錨**不掛此欄、只寫進 notes——掛了
  就會被表讀成「該 commit 花了 N 秒」而與事實相反；故 `bench`／`synthetic`／`baseline_chain`／
  `full_chain` 這類非單顆 commit 的量測通常無 commit 欄。
- Lint03 驗格式；Lint18 把 `commit` 欄向**外層** git 實證，形同 merge 那條腿（不可解／
  非 commit＝ERROR 指名行號），共用同一批 cat-file 併發管線。
- 放 `events.jsonl` 而非另開檔：沿用 Lint03／append-only／Lint18 既有機制，零新掃描面。

### ② `docs/generated/reference/perf.md`——全序列生成表

`generate` 自 events 的 perf 事件重算：表欄 `date | kind | wall_s | rc | commit（短 7）| notes`，
依（date，檔內序）排序；notes 的 `|` escape、換行折 `<br>`；空集＝「（尚無 perf 事件）」。
生成檔零預算。登記於 `REFERENCE_TABLES`／`REFERENCE_LIVE`（STATE 對賬行列真來源）。

### ③ STATE.md「效能引信」機器判

`gen_state` 新增獨立小節，機器判 ADR 0044 之「連續兩刀 ≥60s」：只採 `kind == close_bookkeeping`
的事件、依 `date`（同日依檔內序）排序、取**最後兩筆**；兩筆皆 `wall_s ≥ 60`＝「已觸發」，
否則「未觸發」；不足兩筆＝「資料不足（N 筆）」。閾值 60 為具名常數 `PERF_FUSE_SEC`
（出處＝ADR 0044：新警戒 45 與新硬擋 90 的中點）。`synthetic`／`bench` **永不採計**；
`doc_only`／`pin_bump`／`merge`／`baseline_chain`／`full_chain` 亦不採計——引信逐字錨在
收刀簿記型。

### ④ MILESTONES 與 STATE 尾 3 筆濾掉 perf

`gen_milestones` 與 STATE「最近事件」濾掉 perf 型（否則回填的十餘筆把最近事件全部擠掉）；
STATE 的 events 型別統計照算（perf N 筆屬正確帳面）。

### ⑤ RUNBOOK §12.1 射程收束

§12.1 只留：兩級門檻語意／量測法（含可複製命令）／本批終態實測三張表及其註（逐位元不動）
／超上限處置／維護紀律，加一句指針（資料點序列的新家＋引信判讀處）與兩句現行事實（merge
commit 不經 pre-commit、分支最後一顆的綠燈即收刀全部憑據；合成推估對真實值系統性高估、
引信判讀一律以 close_bookkeeping 實測為準）。全部 ★ 資料點 bullet 與「史料批次」「歷史
對照」「一致性核」三段轉 perf 事件（分析結論併入對應日期事件的 notes）、不留 RUNBOOK。

### ⑥ ADR 0044 配套段之承載處訂正

ADR 0044「配套」段逐字：「記入 RUNBOOK §12.1 的資料點序列（該節已備量測法與可複製命令）」。
**決定不變**（每刀例行量測、連續兩刀 ≥60s 強制觸發三處置之一），變的只是承載處：自本 ADR
起該句改讀為「**append 一筆 `close_bookkeeping` perf 事件**（人讀 `docs/generated/reference/perf.md`、
引信機器判＝STATE.md 效能引信行；量測法仍住 RUNBOOK §12.1）」。0044 body 不可變，故以本檔
承載，範式＝ADR 0067 對 ADR 0042 之處理形。`.githooks/pre-commit` 檔頭註解同批改指新家。

★第二處承載處訂正：RUNBOOK §12.1 的警戒錨敘述稱 41.2s 為「收刀簿記型**實測**」，
與 ADR 0044 自己的量測事實表（逐字「**41.2s**（合成推估）」）及 provenance
（「收刀簿記型**推估** 41.2s」）相抵；kind 分類機器化後更與 `reference/perf.md` 的
`synthetic` 直接打架——同一個數字，人寫節說是實測、機器表說是合成推估非實測，且兩者同節
相鄰可見。⇒ §12.1 那句就地訂正為「合成推估」並註明其 kind 與「不入引信採計面」；ADR 0044
body 不動（同本條之形）。連帶：同表記為「收刀簿記型 commit（兩 gitlink＋多檔 staged）」的
38s，依決定①的 kind 定義應為 `pin_bump`（回填的 events 新列已逐字說明）——故「警戒錨＝收刀
簿記型」在新分類下兩筆佐證皆非 `close_bookkeeping`，訂正後的 §12.1 不再作此稱（門檻數值
本身不變：45／90 仍是 ADR 0044 拍板值）。

### ⑦ NOTES「已收官」段刪除留指針

整段刪、換一行指針（→ `docs/generated/MILESTONES.md` 事件表〔perf 型另居
`docs/generated/reference/perf.md`〕／STATE 尾 3 筆；逐批全文在
`events.jsonl`）。理由＝機器生成檔的人寫鏡像（背景第 3 點）。段內仍現時有效的跨刀指針併入
「其餘在案候選」行。

### ⑧ 收刀程序增第四步

CLAUDE.md §2「收刀」段**增列第四步**：簿記 commit 落地後量該顆牆鐘、append 一筆
`close_bookkeeping` perf 事件（隨下一顆 commit 入帳；量測法＝RUNBOOK §12.1）。

**「簿記三步」一詞維持原義**＝簿記 commit **內**的三步（events append／NOTES／generate）；
第四步必然落在該 commit **之後**（要量的正是那顆的牆鐘、事件隨下一顆 commit 入帳），故不
併入該詞、也不改稱「四步」——改稱四步會反過來謊報簿記那顆的內容。承載面依 CLAUDE.md §4
勘誤紀律全掃（`errata 簿記三步`）、現在式文件家族四處逐處處置：

- CLAUDE.md §2 的**開場流程行**與**編排提示詞範本**內的收刀終點行——**同批補上第四步**。
  範本那段會被整段烤進編排 agent 的 prompt、也是收刀時實際照著跑的清單，只列三項＝第四步
  對讀者等於不存在；而本 ADR「後果」段自己載明不設機器閘，這一步純靠人與範本記得。B-149
  的立案事實（該記的一筆因無承載處而差點掉帳）換個形式復發，就從這裡開始。
- `.specify/memory/constitution.md` §I.4 與活書 §12 名詞表的「簿記三步」——**維持不動**：
  該二處描述的正是簿記 commit 的三步內容、仍屬現時事實（非漏列第四步，而是詞義本就只指
  那顆）；且憲法改動須走 amendment（ADR＋版本 bump）、活書非本刀射程。
- 其餘命中全在 brainstorms／specs／events／生成物——過去式史料或機器重算面，不改。

### ⑨ 既有資料點以原日期回填

RUNBOOK §12.1 現文的每一個資料點（含史料批次、歷史對照、一致性核、2026-08-25 例行量測表
內各支中位數）以**原日期**回填為 perf 事件，notes 忠實承載該筆的判讀散文；加上 B-149 條目
裡的收刀簿記型 9.97s 與同日三顆文件型。回填完整性以機器對賬（瘦身刪除行內所有 `Ns` 數值
逐一在 perf 列出現）自證。

### ⑩ perf 列寫錯的更正形——依「該欄有無機器實證」分兩形

- **非機器驗證欄**（`wall_s`／`kind`／`notes`／`rc`／`date`）：append 一筆新 perf 事件、notes
  註明取代哪一筆；既有列不動。這些欄沒有「事件被它欄引用」的連鎖，一筆新列即足。
- **`commit` 欄**：走 **erratum**（`field: "perf.commit"`、B-042 調閘形）。理由＝`commit`
  受 Lint18 逐列實證，append 新列**不會**讓舊列的紅消失（`lint_events_sha` 逐列掃
  `perf_commits`）；而 erratum 若不收此欄（枚舉外＝Lint03 紅；改填 `merge` 則被「target
  列不存在指定欄」擋）⇒ 壞值一旦以 `--no-verify` 落地、或外層改史讓原本合法的 SHA 失聯，
  `docs-sync lint` 自此恆紅、pre-commit 恆擋，且無任何合規操作能解除。那正是 B-042 開帳要
  消滅的「附了去處卻走不通」形（`_erratum_remedy` docstring 逐字：「照抄 append 即可讓紅消
  ——出口真的走得通」）；不納入即成帳本裡唯一「ERROR 級 SHA 實證＋零出口」的欄。
  ⇒ `ERRATUM_FIELDS` 自此＝**凡受 Lint18 機器 SHA 實證的欄**（`merge`／`perf.commit`／
  `pins.*`）；欄存在性依欄名分派，corrected 自身照硬語意②向外層實證。
  與 **ADR 0037 的關係＝值域擴充、非翻案**（故本檔 `supersedes` 不列 0037）：0037 的調閘形、
  更正視圖與六條硬語意全數沿用不動，變的只是 `field` 值域——0037 寫下 `{merge, pins.*}` 時
  `perf.commit` 這個受實證的欄還不存在（它由本 ADR 決定①才生出來），而 0037 對值域的判準
  本就是「Lint18 的驗證面同一份真值」。連帶：0037 硬語意⑥所稱「三處 ERROR 訊息」隨欄數成為
  **五處**（perf 兩處同批補上、照抄即綠有端到端釘子）。
  替代案：①「不可解降為 WARN」（同 pins 之形）——未採：只赦免一半，「可解但非 commit」
  （抄到 tree／blob 的 SHA）仍是零出口的 ERROR；且 pins 的寬貸是為 upstream rebase 卷史而設，
  外層改史沒有同等常態。②perf 型加「作廢」語意（如 `superseded_by_line`）——未採：要新增
  schema 欄與一套跳過語意，且與決定③取樣窗的互動不明，成本高於復用既有 erratum 機制。
  ③**全部 perf 欄一律 append 新列、不擴 erratum 欄**（＝把非機器驗證欄那半條的作法套用到
  `commit`）——未採：其理由「perf 沒有『被它欄引用』的連鎖」只對不受機器驗證的欄成立，對
  `commit` 欄會留下本條正文所述的零出口恆紅。

★**已知副作用（限 append 新列形）：更正列會佔用決定③的取樣窗**。`close_bookkeeping` 型若依
該形更正，該刀在帳上就留下**兩筆**同型列，而引信取的是「最後兩筆」⇒ 窗內變成同一刀的〔錯值, 更正值〕，而非
ADR 0044 逐字要求的「連續**兩刀** ≥60s」。方向是**假陰性**：前一刀 62s、本刀誤記 9.9s 後補
記 70s ⇒ 正確判讀為已觸發（兩刀皆 ≥60），機器實得〔9.9, 70〕而印「未觸發」；引信無機器閘、
STATE 那一行就是唯一出口，印錯不會有第二道接住。
取態＝**判準不變、以已知態承載**，不加機器去重：去重只能靠 `commit` 欄相同才成立，而該欄
選填、跨機重測亦可能同 commit，機器去重收掉的是一半情形卻會讓判準看起來已經可靠。⇒ 更正
`close_bookkeeping` 列時**必須人工複核** STATE 效能引信行，並在更正列的 notes 寫明正確的
兩刀判讀；`perf_fuse` 的 docstring 同載此已知態，讀碼面不會漏掉。

## 考慮過的替代案

- **候選①：新開附屬文件 `docs/ops/PERF-DATAPOINTS.md`**（形照活書附屬文件、入 BOOK_ANNEXES
  家族、同受 Lint07）：未採——只是把同一條會無限成長的序列換個檔繼續長，仍需配額、仍會撞頂；
  且資料點是「依日期 append 的量測」，事件帳才是它的正確材質。
- **候選②：就地壓縮史料段**：已於 2026-08-30 收刀執行過一輪，換到零餘裕——證明是止痛不治本。
- **候選③：提高配額**：須走 ADR 0058 停損絆線程序、且與「撞頂即下放」既定取態相抵；末選、未採。
- **perf 另開 `perf.jsonl`**：未採——要複製一整套 Lint03／Lint18／append-only 機制；放同一帳
  只多一個 type 分支。
- **引信採計全部實測型（含 pin_bump／doc_only）**：未採——ADR 0044 引信逐字錨在收刀簿記型；
  混入其他型會讓 pin bump 型（條件段全中、天然較慢）先觸發、失去「同型比同型」的判讀力。

## 後果

- RUNBOOK §12.1 釋出百餘行、NOTES 回到「幾行」；兩檔重獲餘裕，且資料點序列自此零預算。
- 引信判讀自此由機器做：STATE 一行、每次 generate 現算，不再靠人讀散文推算。
- 多一個事件型別要維護（Lint03 分支、perf.md 生成器、STATE 小節）；docs-sync 自測案數隨之增加。
- 每刀收尾多一步（量牆鐘、append perf 事件）；漏做的偵測面＝STATE 引信行的最新日期落後於最新
  feature_close——本 ADR 不設機器閘（同 ADR 0044「不設機器守」取態；成長壓力已由事件帳吸收）。
- 改動面＝`tools/docs-sync.py`（schema／Lint18／三個生成器／自測）、`events.jsonl` append 回填、
  RUNBOOK §12.1、NOTES、README 地圖、CLAUDE.md §2、pre-commit 檔頭註解、BACKLOG 刪 B-149、活書 §12 名詞表「事件源」一行（補 perf 型；§12 配額餘裕充足）。
