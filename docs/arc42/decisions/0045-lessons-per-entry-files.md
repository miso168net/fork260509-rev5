---
id: "0045"
title: LESSONS 由分卷制改分檔制——手寫索引＋一坑一檔＋晉升必答欄 promoted_to
date: 2026-08-17
status: accepted
supersedes: []
superseded_by: []
provenance: "B-090（user 拍板方向 2026-08-17、grilling 六題全決同日）；觸發審計＝004-ip-trust-anchor 收刀後盤點：LESSONS.md 該 session 存取寫:讀＝6:0、真正在行為上生效的教訓全數經晉升面（CLAUDE.md §2 內嵌／quickstart 內嵌／碼註）進場、零次「動手前查前例」"
tags: [docs, lessons, lint, governance]
---

## 背景

LESSONS 原制＝單檔＋滿卷分卷（每卷 token 上限 25000）。收刀後審計實證其失效形：
本 repo 對 LESSONS.md 的存取**寫:讀＝6:0**——每一次開檔都是寫入側，零次「動手前查前例」；
真正在行為上生效的教訓，全數經**晉升面**（CLAUDE.md §2、quickstart、碼註、memory）進場。
凡只住 LESSONS 本體的條目＝寫完即死。結論：LESSONS 實際功能是素材庫＋審計紀錄，不是檢索面。
分卷制的體積壓力形也押錯位置——單卷上限約束的是卷總量，對「單條越寫越長」零約束。

存量＝**47 條**（★2026-08-17 遷移當下凍結量，非活量；其中 L-001～L-003 為裸段形
`L-NNN｜`、RE_ENTRY 容忍變體）。

## 決定

改**分檔制**：手寫索引＋一坑一檔＋晉升必答欄。五個設計決策（D1～D5）＋三件機器防線：

- **D1｜索引行刻意不匹配 `RE_ENTRY`、條目檔正文保留各自原起手形**。索引行取方括號連結形：
  方括號段 `[L-NNN｜坑名]` 緊接圓括號目標 `LESSONS/L-NNN-<slug>.md`、尾綴 `— 防法 hook`
  （本檔刻意拆段示意、不寫成整行真連結——連結形在 ADR 內即觸發 Lint12 目標存在性檢查、
  對佔位目標必紅），`[` 卡形不命中 RE_ENTRY；
  條目檔首行維持 `L-NNN｜` 起手形（含 L-001～L-003 裸段形照舊）。⇒ Lint09 撞號／計數、
  lessons_count、lessons_next 全部零改動，唯一命中面在條目檔。
- **D2｜`lessons_paths()` 是唯一枚舉權威**：主檔（索引、恆 index 0、載 next-id）＋舊分卷
  LESSONS-*.md（過渡期防漏視野）＋ `docs/ops/LESSONS/` 下 sorted 之 L-*.md 條目檔；
  改一處全通（Lint09、計數、語料邊界測試皆走它）。
- **D3｜正文逐位保留（byte-preserving）**：存量 47 條一字不改、只搬家＋加 frontmatter；
  驗收＝機器 byte-diff（串接條目檔正文〔去 frontmatter〕== 原兩檔條目區）。
- **D4｜frontmatter 僅 `promoted_to:` 一欄**（晉升必答：防法晉升到哪個操作面；無處可晉升寫
  「無：<理由>」）。id 不進 frontmatter——檔名＋正文首行已有，第三份抄本違反「每個事實只有
  一個家」。存量「讀到哪填到哪」（Q4）：判不出的填「未盤點」佔位、盤點工項另配號承載。
  值域自由文字、只驗非空（Q5；驗證強化等首次真實失效形實發再校準）。
- **D5｜索引手寫、對賬機器**。漂移防線＝既有 Lint12（索引→檔連結存在）＋新條款 Lint26
  反向三斷言。防法前置＝advisory（Q6；機器強制面由 hook 行雙向對賬承載）。

機器防線三件（同一工作樹內落地，故此處字面引用合法）：

1. **Lint09 head 視野聯集修法**：L 側 head 視野由「現況路徑的 HEAD 版」改為「現況路徑 ∪
   HEAD 自己的 LESSONS 卷集」（git ls-tree 過濾主檔／舊分卷／條目檔三形）——否則遷移
   commit 刪舊分卷即令 L-001～L-028 退出視野、假報 28 筆「舊號回收」。★含主檔 index-0
   修正：head 清單不可用裸 sorted(聯集)——字典序 LESSONS-….md < LESSONS.md（連字號
   0x2D < 句點 0x2E）會把主檔擠出首位，而 head_next 只讀首元素，主檔被擠出＝head_next
   讀不到＝反回收閘整段**靜默失效**；正確形＝[主檔] + sorted(聯集 - {主檔})。
2. **Lint07 單條上限**：條目檔逐檔 token 上限 **WARN 2000／ERROR 3000**（Q1、施壓形；
   遷移當下實測最大 L-045＝1937、中位約 600、零條超線——WARN 線刻意貼近，補記時順手瘦身
   即本制度本意）。token 計全檔（含 frontmatter）。
3. **Lint26 分檔對賬三斷言**（目錄不存在＝零 findings、遷移前照綠）：
   (a) 條目檔名匹配 `L-NNN-<slug>.md`（slug 英文 kebab、Q2）且正文 RE_ENTRY 恰命中一次、
   號碼與檔名相等；(b) 索引↔檔雙向對賬——管反向（檔無索引行）與唯一性（每檔恰一行），
   「索引→檔」存在性由 Lint12 兜底；(c) frontmatter `promoted_to:` 必填非空。
   ★per-machine memory 路徑禁令由既有全 md 掃描條款承載、Lint26 不重複實作。

## 考慮過的替代案

- **生成索引**（掃條目檔自動產索引）：不採。生成物材質歸 docs/generated（機器生成、嚴禁
  手改），而索引的「防法 hook」欄需要人逐條精寫（Q3：機械抽取品質不可控、爛索引比沒索引
  糟）——材質矛盾；且撕裂既有 append 手寫流（MEMORY.md 同形＝手寫索引、慣例已驗證）。
- **防法前置回改存量**（遷移時把 47 條正文重排為防法先行）：不採。破 byte-preserving
  驗證（D3 的機器對賬基礎）、風險不對稱——重排收益小、竄改風險大；前置紀律只約束新條目
  且為 advisory（Q6）。

## 後果

- **單條上限取代單卷 25000 的實質約束面**：分檔制下單卷限只罩索引主檔（自然縮）；
  「條目越寫越長」的結構性壓力由單條 WARN 2000／ERROR 3000 承接。
- **head 視野聯集順帶堵一個現制真漏洞**：「整卷檔被刪＝其號碼靜默退出反回收視野、
  append-only 破壞零訊號」——聯集後任何曾在 HEAD 的卷（含已刪）恆在視野。
- 新條款上線觸發既有紀律的連鎖動作（非本決定新設）：Lint22 名冊三檔範圍字串同 commit
  bump 至新上界、事件帳 append 一筆帶新 lint-roster 名冊的 misc 事件（bootstrap 條款數
  斷言取末筆 lint-roster 事件）。
- 存量 `promoted_to` 盤點是後續工項：佔位「未盤點」條目逐條回填；盤點順便是防法品質
  審查——寫不出晉升面的條目，往往防法本身不可執行。
- 引用一律用 ID（L-NNN）、與檔名無關；檔名只是住址，改 slug 不構成翻案。
