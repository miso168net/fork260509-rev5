---
id: "0075"
title: review 報告與 review 事件義務收斂為僅適用不定期獨立 review 輪——feature／維護批收刀之 final holistic review 以收單 commit＋findings 三分流承載
date: 2026-08-31
status: accepted
supersedes: []
superseded_by: []
provenance: "B-155（rust 維護批 final holistic review 之文件透鏡查定 2026-08-31 立帳：CLAUDE.md §2 review 輪規則與 as-built 長期分岔）；user 親決 2026-08-31 選項②「改述規則」"
tags: [docs, process, review, backlog-disposition]
---

## 背景

CLAUDE.md §2 的 review 輪條目規定：報告存 `docs/reviews/YYYYMMDD-<scope>.md`（front-matter
必含 `findings_total`）＋append 一筆 review 事件。但規則與 as-built 長期分岔（B-155 立帳時
查定、本 ADR 定稿前複核並訂正計數）：本 ADR 落帳前 events 87 筆中 review 型別 **0 筆**——事件義務自始
零執行；final holistic review 歷來共**十次**（001～007 七刀＋下一刀起手／外層／rust 三維護批），報告義務
僅 003／005 兩次執行（`docs/reviews/` 現存兩檔即此二者、皆為收刀 fhr 報告，005 之後全停），
其餘**八次**皆走「findings 直入收刀 commit＋三分流（修／轉 B-NNN／won't-fix ADR）」——
零報告檔、零 review 事件。逐次覆核（近四次由 rust 維護批收單時以文件透鏡查定、餘依 events
收刀筆複核）：十次的 findings 全數有落點、**零資訊遺失**——修＝修復 commit、轉待辦＝
B-NNN 列、不修＝won't-fix ADR，三個去向各有帳面；003／005 兩份報告的 findings 亦全數在
收刀 commit 有落點、不構成增量資訊。

同一條規則於是有兩種讀法並存：照條文讀＝每次 fhr 都欠一份報告＋一筆事件；照 005 之後的
as-built 讀＝義務早已不及 fhr。每次 fhr 都要重付一次「要不要寫報告」的討論成本。

## 決定

1. **報告檔＋review 事件二義務收斂為僅適用「不定期獨立 review 輪」**——自成一輪、
   不附掛在任何刀或批的收刀程序內的 review。
2. **feature／維護批收刀之 final holistic review 不落報告檔、不落 review 事件**；其
   findings 一律三分流（修／轉 B-NNN／won't-fix ADR），以該批**收單 commit**（commit
   訊息＋隨批帳面）承載。
3. CLAUDE.md §2 review 輪條目同批改述、標注本 ADR；三分流句保留原語意。
4. 既有 `docs/reviews/` 兩檔維持不動；**不補記**歷史 review 事件（過去式歸 git＋events
   既有帳，as-built 不回灌）。

## 理由

1. **規則與 as-built 長期分岔＝每輪重付討論成本**——判準同 ADR 0071 替代案 C：決策與帳面
   不一致不會自己消失，只會在每次 fhr 的「要不要寫報告」裡重複收費。零報告的八次 as-built
   已是行之有年的既成形（報告腿 005 之後全停、事件腿自始零執行），且無一次因缺報告而
   漏掉 finding。
2. **收單 commit＋三分流已是有效的 durable 承載**：修復有 commit、待辦有 B-NNN 兩卷、
   翻案／不修有 ADR——三個去向各有機器閘（Lint04 backlog_done 對賬、Lint08 ADR schema）
   與 git 史，報告檔在此場景是第四份鏡像、違反「每個事實只有一個人寫的家」。
3. **獨立 review 輪的義務保留**：該場景無「收單 commit」這個天然承載物（獨立輪不必然
   產生 commit），報告檔＋review 事件是其唯一 durable 落點；且獨立輪 findings 量大、
   須有 `findings_total` 供對賬。收斂的是適用面、不是義務本身。

## 替代案

**A（B-155 選項①）：恢復執行**——自下次 fhr 起產出報告＋review 事件、並補記歷次無帳成因。
未採：十次實證顯示報告檔在 fhr 場景零增量資訊——八次零報告的 findings 已全數三分流落帳，
003／005 兩次雖有報告、其 findings 亦全數在收刀 commit 有落點（報告未攔到任何原會漏掉的
finding）；恢復執行＝每批多寫一份鏡像、還要補考古歷史，成本實付而收益空。

**B：維持條文不動、繼續各讀各的。** 未採：判準同 ADR 0071 替代案 C——矛盾持續收費。

## 後果

- B-155 關帳、自 BACKLOG 刪列；CLAUDE.md §2 review 輪條目改述（僅適用獨立輪＋fhr
  承載形、標注本 ADR）。
- ★**誠實記——已知代價**：fhr 的 findings 自此**無單檔彙整視圖**——要回答「歷來 fhr
  共抓過哪些 findings、各怎麼處置」得走逐顆收單 commit 訊息與 events 收單筆
  （feature_close／misc）考古，而非開一個目錄逐檔讀。緩解＝三分流去向本身可查
  （修復 commit、B-NNN 兩卷、ADR 目錄），且收單 commit 訊息紀律上逐項列 findings 處置。
- ★**翻案觸發器**（命中任一即立新 ADR `supersedes: ["0075"]`）：
  1. 出現「需跨批彙整 fhr findings」的真實需求——例如某次盤點須逐批比對 findings
     趨勢，且 git 考古成本已實付並明顯高於維護一份報告檔；
  2. 保留下來的獨立輪義務確認為空殼——★拍板日帳面即零次獨立輪、review 事件 0 筆，故以
     正向門檻計：自本 ADR 起首次獨立 review 輪出現時未落報告檔＋review 事件，或累計五個
     收刀批（刀或維護批）後仍零次獨立輪——須重新拍板收斂或恢復；
  3. 某次 fhr 的 findings 出現三分流無家可歸的第四類（不修、不值得立 B-NNN、也非
     won't-fix ADR）——承載形本身不敷用。
