---
id: "0018"
title: B12 前端腿＝接線層先行（typings＋service 新檔）、view 延 B-008
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "B12 brainstorm（docs/brainstorms/002-system-settings.md、user 拍板 2026-08-08）；背景＝BACKLOG B-008（四張 rev4 專屬管理頁 view 於 rev5 base-web 尚不存在）＋憲法 §III.1 預設軌道三條的設計用途"
tags: [scope, frontend, wire]
---

## 背景

活書對縱切刀的定義含「前端整條打通」，但 manage_system-settings 的 view 在 rev5
base-web 不存在（B-008；R_SUPER 選單點擊 404＝已知態）。wire 契約權威在前端 typings
（憲法 §I.1），後端契約鎖什麼取決於前端腿範圍。憲法 §III.1 三條預設可動軌道
（`.env*`／`src/typings/api/` 新檔／`src/service/api/rev5-*.ts` 新檔）恰可承載
「加 typings 與 service 接線、不動 view」；新增 view 檔則需首個 ★軌道 Amendment
（修憲＋ADR＋版本 bump）＋view 實作本體。

## 決定

B12 前端腿範圍＝**接線層**：`src/typings/api/rev5-settings.d.ts`（wire 權威錨點、
我方新檔走新增型圈界）＋`src/service/api/rev5-settings.ts`（axios 呼叫層）——全在
§III.1 預設軌道內、**零修憲**。view 延 B-008（對應前端刀兌現）；期間
manage_system-settings 選單 404 維持已知態。縱切定義的「前端整條打通」在首刀＝
**接線層打通、UI 顯示延後**——此半條寫入 spec 非目標節。

## 後果

- K1-25 wire 契約機器化自首刀起即有真錨（typings 新檔）；B-008 兌現時直接消費本刀
  契約、無需重談 wire 形。
- ★軌道首例（view 新檔授權）延後至前端首刀，該刀第一件事＝修憲（排程含半日）。
- 404 已知態貫穿 B12 全程：前端煙測腳本須把該 4 項列為已知態、防誤判回歸（B-008
  條目既載）。
- 若日後判定首刀縱切必須含 UI，翻案＝新 ADR supersede 本檔＋提前開 ★軌道。
