---
id: "0059"
title: logout 呈遞 rotated 票維持 0000 靜默 no-op——sys_token 狀態機矩陣缺格之裁決（撤銷射程恆為單列、不擴 revoke_family）
date: 2026-08-25
status: accepted
supersedes: []
superseded_by: []
provenance: "B-057（003-auth-session 收刀時列為已知態待裁、觸發器寫「下一支動 data-model §1 狀態機矩陣的刀，或 user 主動裁決時」）；user 親決 2026-08-25 選候選 (a)；落地＝本維護批"
tags: [auth, session, state-machine, backlog-disposition]
---

## 背景

`specs/003-auth-session/data-model.md` §1 的狀態機矩陣，logout 事件只有兩列：現態 `active`
（驗章成功）→ 該列轉 `revoked`；以及「（任意／無）＋驗章**失敗**／垃圾票」→ 不變、回 `0000`。

呈遞 **rotated** 票的形**兩列皆落不進**：該票驗章是**成功**的（未過期、簽章正確、查得到列），
只是現態非 `active` ⇒ 第一列的現態條件不符、第二列的驗章條件不符。這是矩陣缺格。

現行實作歸「冪等 no-op 家」——`0000`、`data:null`、零 DB 寫、不落事件，與已撤票同軌；
由 `rust-api/server/src/handler/auth/logout.rs` 之
`t040_2b_logout_with_rotated_stale_ticket_is_silent_noop` 機器釘住，改動任一方向都會紅。

## 決定

**維持現行**（B-057 候選 (a)）：rotated × logout ＝ `0000` 靜默 no-op，撤銷射程**恆為單列**、
不擴為 `revoke_family`。

★**寫明的落點＝本 ADR，不是 data-model §1**：B-057 條目原寫「在 data-model §1 補一列」，
那是 003 收刀**當時**的候選；該刀收刀後 `specs/` 樹已成史料、**不可改**（ADR 0058 決定 3 逐字，
理由＝把現在式 as-built 放進過去式的家是死路）。本 ADR 即該缺格的裁決記錄。

## 理由

1. **回異碼＝token 有效性 oracle**：wire-auth §logout 的既定紀律是 logout 一律回 `0000`
   （logout.rs 檔頭逐字：「回異碼＝提供 token 有效性 oracle」）。若對 rotated 回不同碼，
   等於對外洩漏「這張票曾經有效」，與該紀律相抵。
2. **候選 (b) 會污染稽核語意**：`revoke_family` 在生產面的觸發點是 `refresh` 的 grace miss
   （`detect_reuse`），而該路徑與 `session_event(reuse)` 綁定——reuse 是**系統事件／攻擊訊號**
   （`created_by` NULL、`reason` NULL）。把使用者**主動**登出併進同一路徑，會使 reuse 事件
   不再等於「偵測到重放」。要避開這點就得另建「撤全鏈但落 logout 事件」的第三條路徑，
   那已不是條目所寫「與 reuse 路徑一致」的簡單改法。
3. **現行射程已有機器守**：logout.rs 既有測斷言「★鏈上 rotated 前置列須**維持 rotated**——
   轉 revoked＝撤銷範圍被擴成 `revoke_family`」；(b) 須連同該守一併推翻。

★**已知代價（不粉飾）**：多分頁 rotate 競態下，分頁 A 完成 refresh 後，分頁 B 手上的票已是
rotated；使用者在 B 按登出得 `0000`，但**同鏈的 active 後繼未被撤** ⇒ 分頁 A 的會話續活。
B 自身因前端清本地票並導回登入頁而「看起來已登出」，未被撤的是**其他分頁**。若使用者對
「登出」的心智模型是「結束整個會話」而非「結束本分頁」，此形即與預期不符——本決定接受此代價。

## 後果

- 現行行為續由 `t040_2b` 釘住；B-057 關帳、自 BACKLOG 刪列。
- logout.rs 檔頭既有的誠實記載補指向本 ADR ⇒ 日後要改該行為者，循碼註即見裁決與代價。
- ★**翻案觸發器**：收到真實回報「在一個分頁登出後其他分頁仍活著」，或 single-session 語意
  調整時 ⇒ 立新 ADR `supersedes: ["0059"]`，並反轉 `t040_2b`（該測 doc 已載此意）。
