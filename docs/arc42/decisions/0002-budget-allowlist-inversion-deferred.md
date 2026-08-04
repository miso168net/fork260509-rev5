---
id: "0002"
title: 預算白名單反轉延後——列創世後首批治理調整（顯式延後立案）
date: 2026-08-04
status: accepted
supersedes: []
superseded_by: []
provenance: "啟動書 §0.3 準則 4／§3.2 條 10（rev4 漏網四件實測為動機）"
tags: [governance, lint]
---

## 背景

啟動書 §0.3 準則 4 要求「預算白名單反轉」：所有 tracked md 與帳本檔**預設受預算管**、豁免顯式登記附理由（動機＝rev4 實測漏網四件：events.jsonl 35,905 tokens／MILESTONES.md 28,883／RUNBOOK.md 23,304／constitution.md 20,114——全數超標或逼近而 lint 全綠）。§3.2 條 10 將其列為創世後首批治理調整＝延後；而準則 1 明訂任何延後須當場立 ADR 記理由與觸發條件——否則 rev5 第一天就以自己禁止的方式（默認延後）延後了自己的成功準則。本 ADR 即該顯式立案。

## 決定

**延後執行白名單反轉**，理由三：

1. rev4 漏網四件在 rev5 已全數入 BUDGETS 名冊（events 帳 token 上限、MILESTONES 分卷改按大小、RUNBOOK ≤900 行、constitution ≤350 行）——已知最大風險面已收。
2. 守衛#8「BUDGETS 名冊內檔案存在性」斷言已上線（B4 丙③、B5 到期拔項實證）——「檔不存在即靜默跳過」的 fail-open 洞已補，現行白名單制本身 fail-closed。
3. 創世期 tracked md 檔集仍在膨脹（B9～B12 陸續進場）——Day 1 反轉會立即製造一批未經拍板的豁免登記項，與「豁免顯式登記附理由」的本意相悖。

**觸發條件（誰先到誰觸發）**：
- ①B12 首刀收刀後的第一個維護批（輕量軌）執行反轉；
- ②任一 tracked md 實測超 15,000 tokens 而不在 BUDGETS——立即提前觸發、不等維護批。

## 後果

反轉前，新增 tracked md **不自動**受預算管——新增檔須人工判斷是否入 BUDGETS（本 ADR 在案期間的已知代價、Compliance 面由 review 輪抽查承接）。
