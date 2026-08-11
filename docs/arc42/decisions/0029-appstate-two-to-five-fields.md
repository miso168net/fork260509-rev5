---
id: "0029"
title: AppState 兩欄→五欄翻案——加 jwt／cache／captcha_secret，ip_rules／trust_model／mailer 續留域外
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 T003①／T006；被翻案的拍板住在 rust-api/server/src/state.rs 檔頭 doc（002-system-settings T005 落地、其 research R3-8 為由），無 ADR 承載故 supersedes 留空"
tags: [rust-api, state, dependency, decision-reversal]
---

## 背景

`rust-api/server/src/state.rs` 檔頭 doc 有一段自稱拍板級的封條：

> ★★恰兩欄是拍板釘死的邊界：rev4:AppState 上那串 `JwtConfig`／`redis`／`captcha_secret`／
> `ip_rules`／`trust_model`／`mailer` 欄位各自屬於 B12 射程外的功能刀，一欄都不搬。
> **要開第三欄＝拍板級翻案，不得逕加。**

該封條在 002-system-settings 當時完全正確：那把刀沒有認證、沒有快取、沒有驗證碼，六欄一欄都用不到。
但它**只住在碼註裡、沒有 ADR 承載**——這正是它自己要求的「拍板級翻案」找不到可 supersede 的對象的原因。

003-auth-session 需要其中三欄：真驗章要 `JwtConfig`、denylist 與節流要 redis 連線、簽發驗證碼題目要
`captcha_secret`。三者都是 request 路徑上每次都要用、且 boot 期一次建好即不可變的資源，繞過 `AppState`
另建全域單例只會多一套生命週期管理。

## 決定

1. **`AppState` 兩欄 → 五欄**，新增：
   - `jwt: JwtConfig`（access 與 refresh 各自秘鑰、iss／aud）
   - `cache: Option<SessionCache>`
   - `captcha_secret: String`
2. **`cache` 為 `Option` 但語意不是「可有可無」**：測試環境 `None`、**production 恆 `Some`**；
   boot 期建連失敗 MUST **fail-loud panic**，不得靜默退 `None`——否則 denylist 的 fail-closed 方向
   （憲法 §I.7 島 C）會被一個開機期的軟失敗整條旁路掉。
3. **邊界維持、只開三欄**：`ip_rules`／`trust_model`／`mailer` 續留域外，各自屬 IP 存取閘刀與郵件刀。
   封條那句「不得逕加」**不因本 ADR 失效**——它要求的就是「開欄須拍板」，本 ADR 即是該拍板。
4. `state.rs` 檔頭 doc 同批改寫（T004）：陳述改為五欄、**並保留剩餘三欄的邊界說明**，不得整段刪除。

## 後果

- 封條的**強度不變、射程收窄**：從「恰兩欄」變成「恰五欄」，「開欄須拍板」的門檻原樣保留。日後第六欄
  仍須新 ADR。
- `Option<SessionCache>` 的測試 `None` 路徑成為降級鏈的**天然測試面**：`enforce` 的四級降級測試
  （真 redis／壞 redis 退 PG／PG 亦壞／nil 放行）可直接以 `None` 與指向不存在位址的連線構造。
- 代價誠實揭露：`AppState` 每 request clone 一份，五欄的 clone 成本仍只是句柄複製
  （`JwtConfig` 與 `captcha_secret` 為小型不可變值、`SessionCache` 內部是連線管理器），
  clone 得起的理由與兩欄時代相同。
