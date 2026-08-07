---
id: "0016"
title: audit 變體 B 禁欄判準＝前綴通配＋具名豁免出口
date: 2026-08-07
status: accepted
supersedes: []
superseded_by: []
provenance: "BACKLOG B-012（001 收刀 triage 判拍板級、不宜順手拍）；user 拍板 2026-08-07；提前拍因＝維護批 B-006/B-013 動 tools/schema-gate.py、觸發條件「下一支動 schema-gate 的刀」在維護批即成立"
tags: [schema-gate, audit, lint]
---

## 背景

契約與實作現分歧：specs/001-schema-baseline/contracts/gates.md §3 字面為前綴通配
（`updated_*`／`deleted_*` 在場即紅）、tools/schema-gate.py 實作為具名四欄
（updated_at／updated_by／deleted_at／deleted_by）。四張 B 變體表現有欄名零個命中
前綴，兩判準今日判定結果完全相同、分歧純屬前瞻；但不拍＝默認具名現況，並讓
「契約寫前綴、工具驗具名」的不一致（gates.md 作為重建依據的失真）再延一輪。

## 決定

採**前綴通配＋具名豁免清單出口**：

- 判準＝任何 `updated_`／`deleted_` 起首欄名於 B 變體表在場即紅（憲法 §I.6
  append-only 保證不因變名欄——updated_time／deleted_flag 之類——被繞過而閘全綠）。
- 合法 payload 欄（例：日後為稽核表加 `updated_fields` jsonb 記變更欄集）走
  **具名豁免清單**正規出口，沿用 repo 既有具名豁免慣例形，每筆豁免附理由。
- 同刀把 tools/schema-gate.py 實作與 gates.md §3 對齊為同一語意、成對紅綠測試。
- 施工併維護批 schema-gate 群（與 B-006／B-013 同刀）。

## 後果

- 守門強度優先、誤攔有正規出口——避免日後合法欄被攔時就地退回具名案（等於白拍）。
- 豁免清單成為新的人工維護面：每筆豁免須帶理由、隨審計欄語意演進複核。
