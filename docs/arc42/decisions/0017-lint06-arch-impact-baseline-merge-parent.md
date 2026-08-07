---
id: "0017"
title: Lint06 arch_impact 比對基準改 merge^1:BOOK（「本刀影響」語意）
date: 2026-08-07
status: accepted
supersedes: []
superseded_by: []
provenance: "BACKLOG B-015（001 收刀實撞：§8 隨刀內 commit 新設、merge→簿記零 delta、被迫記 arch_impact=none＋notes 載實況）；user 拍板 2026-08-07；前代同題＝啟動書 rev4 K3（操作手冊措辭與閘定義應一次對齊、勿改流程）"
tags: [lint, docs-sync, workflow]
---

## 背景

Lint06 (b) 現比 merge:BOOK vs 簿記態。CLAUDE.md §2 要求活書「就在 feature branch 內改」，
於是刀內 commit 的活書變動在 merge 時已含、merge→簿記零 delta→被判「無實際變動」。
001 實例：§8 資料慣例節隨刀內 commit 新設，收刀事件只能記 arch_impact=none＋notes
解釋——閘定義與操作手冊互相矛盾，rev4 同題已判「對齊兩者、不改流程」為正解。

## 決定

比對基準改 **merge^1:BOOK vs 簿記態**——語意＝「本刀影響」（刀內活書變動∪簿記時
活書變動）。配套：

- 前提＝收刀恆 `merge --no-ff` 單親 merge（本 repo 現行紀律）；此前提**寫死於工具
  註解**——非單親 merge 下 merge^1 語意不定，日後改收刀方式須連動本閘（新 ADR）。
- CLAUDE.md §2「架構影響→活書對應節【就在 feature branch 內改】」維持不動。
- 施工併維護批 docs-sync 群；驗收＝合成 fixture 紅綠測試（001 同型案例判綠、
  無變動案例判定不變），不得以實跑 lint 驗收（現況對 001 已 SKIP、改後仍 SKIP）。

## 後果

- B12 起的 feature_close 可如實記載刀內活書變動，不再被迫記 none。
- 001 那筆歷史事件不回改（events append-only、ADR 0012 決定 5）；其 notes 已載實況、
  以本檔為語意勘正。
