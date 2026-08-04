---
id: "0001"
title: rev5 創世採用——治理工件直搬＋憲法 v1.0.0 定版（波 -1 文件地基一鍋 commit）
date: 2026-08-04
status: accepted
supersedes: []
superseded_by: []
provenance: "docs-governance-template@1c1854b4ce64881ad51da0f066accb5321d811ef＋rev4:2b8a101c94abcac4c62e7e77e0bb8796f1f399a8（雙 SHA＝教義源＋工件源）"
tags: [governance, bootstrap]
---

## 背景

rev5 依啟動書（docs/brainstorms/000-doc-architecture.md、§4.2 B0～B12 序列）自 rev4 治理終態重跑。治理樣板教義要求「工件必須機器產出」；rev5 實際採用路徑＝樣板 README 未載的第三條路：**rev4 工件直搬、樣板當教義與裁切清單**——此偏離需立案。

## 決定

1. **採用路徑（偏離立案）**：治理工具鏈、hooks 與根設定檔自 rev4@2b8a101c 直搬，樣板@1c1854b4 僅作教義依據與裁切清單。**緩解**＝逐檔 sha256 血緣斷言（啟動書 §4.5.1 名冊；搬運一律腳本實算 fail-loud，裁製品雙雜湊留證——證據＝brainstorms/b2-transport、b5b-secrets 兩證據檔）。
2. **憲法 v1.0.0 定版**（user 親審 diff、2026-08-04）：自 rev4 constitution v1.15.0 可攜段搬入；§I.7 行為島細目與 §III.2 軌道細目**不預載**、循進場規則隨刀 Amendment 進場，兩節各置承襲指針（候選細目＝啟動書 §5 K1）。裁決全文＝brainstorms/b5-decisions。
3. **schema 拷貝例外承載**（憲法 §I.5 的射程補充；B5 親審裁定歸本 ADR）：**資料形狀是契約不是碼**——schema 與 migration 允許以 rev4 終態為藍本壓平（rev5 `m001` 基線＋`m002` seed；藍本座標與驗證法＝啟動書 §4.5.8；波次歸屬＝波 0 正式刀、brainstorms/b5b-gate-decisions Q2 甲案）。射程以 §4.5.8 藍本座標為界，射程外程式邏輯仍受 §I.5 禁拷貝約束。
4. **創世期結構紅治理**：DAY1_EXEMPTIONS 具名豁免表（四欄制＋機器強制三條——跳過必列明細、到期即紅、拔項翻紅）；pre-commit 的 fork-delta 觸發段加基線源倉缺席具名跳過（B9 前；源倉就位自動恢復實跑，新機空窗由 CLAUDE.md §6 掃描防線禁令＋bootstrap 承接）。
5. **條款名冊 23 條**（Q8 甲案：Lint23 拆除留洞、編號不重用、推導上界 24）＝創世 misc 事件 notes 之 `lint-roster:` 人寫名冊，為 bootstrap 條款數斷言的獨立對賬源。

## 後果

- 首批 commit＝B1～B7 全部產物一鍋（本 ADR、ADR 0002、創世事件同 commit）；此後一切修訂走憲法 §V.2 Amendment 與 ADR 流程。
- 創世決策過程全文＝docs/brainstorms/ 創世期史料（000＝啟動書＋b2-～b7- 證據系列；NNN- 前綴保留給各刀階段 0 產出）；本 ADR 為正式凍結載體。
