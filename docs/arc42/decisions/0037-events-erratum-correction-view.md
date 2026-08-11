---
id: "0037"
title: events 帳本新增 erratum 事件型與 Lint18 更正視圖
date: 2026-08-11
status: accepted
supersedes: []
superseded_by: []
provenance: "工具面維護批（輕量軌）U5、BACKLOG B-042 殘半；user 拍板取「調閘：Lint18 認得更正事件」形、否「歷史錯列具名豁免表」候選（2026-08-11）；六條硬語意逐條由主線擬定並烤入該單元規格"
tags: [governance, tooling, docs-sync]
---

## 背景

Lint18 對「已進 git 史的壞 merge／pins SHA」的 ERROR 訊息自己指示補救路徑＝「依 ADR 0012
決定 5 append 新事件更正（既有列絕不編輯）」，但 Lint18 不認得任何更正事件——照指示做完
ERROR 依然在、pre-commit 依然卡死。這是「紅訊息附去處、但出口不可執行」（B-042 開帳、
B-033④ 教訓形）：唯一能清紅的做法是編輯既有列，而那正是 ADR 0012 決定 5 明禁的。

非 live 紅：現有 events.jsonl 全部 SHA 可解、Lint18 全綠。本案是把一條寫在訊息裡但走不通
的路修成走得通，不是修復當前紅。

## 決定

### 1. 採「調閘」形——events.jsonl 新增第四事件型 `erratum`

形制：`{date, type:"erratum", target_line, field, corrected, reason}`，
`field ∈ {merge, pins.web, pins.api}`（自 `PIN_KEYS` 導出、不落第二份字面名冊）。
Lint18 驗證前先掃全帳建**更正視圖**，以 corrected 值覆蓋 target 列的指定欄後才做逐列
SHA 實證。六條硬語意：

1. **更正視圖重驗**：覆蓋後實證通過 ⇒ 該壞列 ERROR 消。
2. **corrected 自驗、零豁免**：每筆 erratum 的 corrected 都須向 `field` 對應的 repo 實證
   可解且為 commit（merge→外層、pins.web→base-web、pins.api→rust-api），否則該 erratum
   列 ERROR。★pins 面「不可解＝WARN」的寬貸（upstream rebase 卷史合法失聯）**不適用於
   更正值**——更正是新寫的、沒有卷史藉口。
3. **脫靶 fail-loud**：`target_line` 超界／指向非事件列／`field` 指定欄不存在於 target 列
   ＝ERROR，絕不靜默 no-op。
4. **同 target×欄多筆＝後者勝**（append 序），但每筆各自過第 2 條自驗。
5. **erratum 不得指向 erratum 列**＝ERROR；更正的更正＝再 append 一筆指向**原始列**。
6. **三處 ERROR 訊息**（merge 不可解／merge 非 commit／pins 非 commit）的「已進史」補救支
   一律改為具體可執行的 erratum 形——欄名逐字、`target_line` 代入該列真實行號。

### 2. 否決「歷史錯列具名豁免表」候選

三條理由：①違「到期即紅」原則——現有 `DAY1_EXEMPTIONS` 是為「判定來源尚不存在」設計的
到期型豁免（五個消費點且不含 Lint18），新設一個永不到期的豁免類別等於開後門；②同一事實
記兩處（豁免表＋事件流）必然漂移；③豁免值本身無人再驗，而 erratum 形的 corrected 是被
機器驗過的。

### 3. 射程邊界＝更正視圖只套 Lint18

**更正視圖**（以 corrected 覆蓋 target 欄）只作用於 Lint18 的 SHA 實證面，其他消費點
一律不套——它們消費的是事件語意而非 SHA。其餘消費點依其既有性質分兩類，本案皆不改：

- **型篩選類**（Lint04／Lint05／Lint06、`backlog_done` 彙總）：只認 `feature_close`／
  `misc` 等特定型，erratum 天然落在篩選之外＝零誤傷。一筆更正不會被計成一次刀。
- **全事件呈現類**（STATE 的 events 型統計與尾列、MILESTONES 表格化）：**照全事件逐筆
  呈現**，erratum 會如實現身（型統計多一個 `erratum N` 項、MILESTONES 多一列、
  刀專屬欄位為空）。這是刻意保留：erratum 是真發生過的事件，機器鏡像須與帳本一一對應，
  濾掉它反而讓「生成物＝events 的忠實鏡像」這條性質破裂。

## 後果

- Lint18 訊息教的補救路徑自此真的走得通；ADR 0012 決定 5（既有列絕不編輯）不必為此開例外。
- 事件型自三型（feature_close／review／misc）增為四型；新型**不被計成一把刀**（型篩選類
  消費點跳過），但**照常出現在全事件呈現面**（STATE 型統計與尾列、MILESTONES）。
- `tools/docs-sync.py` 自測 471→489；真帳本零 erratum ⇒ 視圖空 ⇒ 現況行為零變。
- B-042 由此關帳（該條目「一次覆蓋三處」之明令隨本案兌現）。
