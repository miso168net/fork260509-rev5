---
id: "0039"
title: ip_* 三個來源節流鍵已 seed 但零執行面消費者＝已知態（解除謂詞＝B-019 落地）
date: 2026-08-12
status: superseded
supersedes: []
superseded_by: [0042]
provenance: "輕量軌維護批（B-047／B-022 批）之帳面補登；成因＝003-auth-session brainstorm 明文承諾「ip_* 三鍵以 ADR 記已知態、解除謂詞＝B-019 落地」，但 ADR 0033 收錄的已知態五項不含此項，該事實最後只落在 003 spec 與 001 data-model（皆非活書）"
tags: [auth, throttle, known-state]
---

## 背景

001 基線壓平時，`system_settings` 隨 rev4 終態一併 seed 了三個來源節流鍵
（`specs/001-schema-baseline/fixtures/seed.sql:388-390`）：

| 鍵 | 值 | 語意（seed 內逐字） |
|---|---|---|
| `ip_captcha_after` | 10 | 來源節流：來源桶滑動窗內失敗達此數即進驗證碼軟區 |
| `ip_max_fails` | 50 | 來源節流：來源桶滑動窗內失敗達此數即硬鎖 |
| `ip_window_minutes` | 15 | 來源節流：來源維滑動窗長（分鐘） |

003-auth-session 交付了節流三區，但**只做 per-user 維**——IP 維明文不做（003 spec 之節流三區段），
理由是語意而非工期：per-IP **鎖定**（不自癒）在 prod CF 拓樸下會把共用出口 IP 的整批使用者
一起鎖，而可信來源 IP 的推導本身屬 B-019。

⇒ 三鍵自此為「**管理面有消費者、執行面零消費者**」：settings CRUD 讀寫得到、值域驗證也在
`validation.rs` 表內，但沒有任何節流邏輯讀它們。

003 brainstorm 當時明文承諾「以 ADR 記已知態、解除謂詞＝B-019 落地」，但 ADR 0033
（該刀的已知態 ADR）收錄五項、**不含此項**——本檔即補上那個家。

## 決定

1. **記為已知態**：`ip_captcha_after`／`ip_max_fails`／`ip_window_minutes` 三鍵於 rev5 現階段
   有值、可經 settings 管理面修改，但**修改不產生任何行為變化**——執行面尚無讀取者。
2. **解除謂詞＝B-019 落地**（IP／信任錨刀交付 per-IP 節流時）。該刀接手時三鍵可直接啟用：
   零 migration、零 seed 變更（值已在庫、範圍驗證已在表內）。
3. **不改行為、不移除鍵**：移除會動 001 凍結面（`schema-gate` gate2 的 seed 比對左源），
   且該刀接手時要重新加回；保留的成本只有本 ADR 這筆帳。

## 後果

- ★**這是一個對操作者可見的落差**：管理員在系統設定頁把 `ip_max_fails` 改成 5，介面會顯示
  成功、值也真的寫進 DB，但**不會有任何 IP 被鎖**。B-019 落地前，此三鍵不得被當作
  「已生效的安全設定」向任何人陳述。
- 同族的 `password_*` 八鍵有相同形（零執行面消費者、待 B-021 的改密端點），該項已由 003
  spec 之 Out of Scope 節記載並綁 B-021，不在本檔重複承載。
- 本檔於 B-019 落地時由該刀的收刀事件解除；解除即刪除本 ADR 的效力（依「翻案立新 ADR」
  紀律，屆時走 `supersedes: ["0039"]` 或於該刀 ADR 內明文解除）。
