---
id: "0007"
title: schema 閘契約＝Day-1 受管演進帳（凍結面＋演進登記合成全等比對）
date: 2026-08-05
status: accepted
supersedes: []
superseded_by: []
provenance: "K1-32／K1-39 重審（rev4 凍結模型三段鑿洞 0032→0039→0064 教訓）；brainstorm 001 §3 拍板甲；契約細節＝specs/001-schema-baseline/contracts/gates.md＋contracts/schema-evolution.md"
tags: [schema, gate, evolution, governance]
---

## 背景

rev4 的 schema 驗證閘採「凍結 fixtures 純全等」模型，落地後三度被以白名單鑿洞放行漂移
（rev4:0032→0039→0064）——凍結模型缺演進出口，每次合法演進都只能開洞，洞一開即成
常設後門。K1-32／K1-39 重審結論：凍結模型必須自 Day-1 配受管演進帳，否則鑿洞重演。
本刀（001-schema-baseline）為 rev5 閘的初建點，契約在此定死。

## 決定

1. **閘契約＝凍結面＋演進面合成期望值、與實庫全等比對**：
   - 凍結面＝`specs/001-schema-baseline/fixtures/*`（定稿產物、永不改寫、provenance 保存）。
   - 演進面＝`docs/ops/reference-src/schema-evolution.json`（單一登記檔、跨刀更新）；
     每筆演進帶來源刀編號（`NNN-slug`）、kind 入枚舉恰八值（add_table／add_column／
     alter_column／add_index／add_constraint／seed_add／seed_update／seed_delete）；
     刪除性演進（drop_*）不入登記檔——屬拍板級、走新 ADR 基線翻案。
   - 合成後與實庫**全等**比對——非容差剝除；未登記漂移一律紅。
2. **登記檔啟動斷言 fail-loud**：頂層鍵恰集＋逐筆欄位齊全非空＋knife 格式
   `^\d{3}-[a-z0-9-]+$`＋kind 入枚舉＋id 遞增不回收；壞形＝rc 2 指名、不得靜默放行。
3. **白名單模型整組移除**：rev4 三段鑿洞之白名單介面（rev4:ADR 0032/rev4:0039/rev4:0064 殘留）不留
   任何形式；閘工具（tools/schema-gate.py）整組重建為 rev5 座標，check 入口無條件
   合成 self-test（健康對必綠＋注入假漂移必紅、self-test 敗＝rc 2 不讀真檔）。
4. **Day-1 常設紀律**：每支帶 migration 的刀收刀前必跑 refresh 照相＋schema-evolution
   登記＋三閘綠（入 RUNBOOK；rev4 係紅燈裸奔兩刀後才補此紀律——K1-39）。

## 後果

- 基線自落地起有保鮮機制：漂移在 commit 前即現形、演進有唯一合法出口（登記檔）。
- 合法演進成本＝一筆登記；非法漂移零通道——「開洞」不再是可選項。
- 登記檔累積即 schema 演進史帳（過去式歸 git＋登記檔、現在式歸快照與真表）。
- 閘契約翻案＝新 ADR supersedes 本檔。
