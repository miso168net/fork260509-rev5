---
id: "0036"
title: gate2 seed 對 runtime-append 表的表級收窄
date: 2026-08-11
status: accepted
supersedes: []
superseded_by: []
provenance: "工具面維護批（輕量軌）U4、BACKLOG B-065；user 拍板取「表級收窄寫死工具內」形、否 runtime-tolerant 呼叫旗標案（2026-08-11）；收窄集三表判定＝主線 archetype 實查後之工程拍板（回報備查）"
tags: [tooling, schema-gate, governance]
---

## 背景

gate2 seed＝兩側 normalize 後未排序逐列 diff（001 凍結面）。append-only 稽核表的 seed
期望是 0 列，任何 runtime 寫入（登入走查一次即寫 sys_token／session_event／
sys_login_attempt）即紅，強迫每次走查後跑 quickstart 收尾（TRUNCATE＋setval 重設）——
003-auth-session 一刀為此付出三次收尾成本、L-015 實暴一次髒庫連鎖。0 列期望本身無資訊量，
逐列 diff 對它是零收益全成本。屬 001 凍結面調整、拍板級。

## 決定

1. **表級收窄寫死工具內**：`tools/schema-gate.py` 立常數（恰三表＝`session_event`／
   `sys_login_attempt`／`sys_token`），此三表兩側 normalize 後剝 COPY 資料列（段首欄名行
   照留照比＝結構漂移仍紅）、其 sequence 之 setval **值**原位正規化為佔位（行消失＝紅、
   per-sequence 身分保留）。
2. **新斷言「seed 側此類表必 0 列」**：於剝列之前驗左源（凍結 seed ⊕ 演進合成），非 0＝
   具名 finding 紅——有人往 seed 塞稽核列照樣被抓。
3. **呼叫端零旗標**：清單寫死工具、絕不取自呼叫端。另一候選 runtime-tolerant 呼叫旗標
   被否——旗標＝呼叫端控制安全邊界（與 B-069 否決 --fuse 同紀律），且 pre-commit 跑的是
   無旗標形、痛點根本沒解。
4. **收窄集射程＝恰三張 003 實痛表**：★`sys_user_role` 雖屬 archetype 變體 C 但有 seed 列
   （種子使用者角色掛載），明令排除——收窄它＝弱化真 seed 面。其餘變體 B/C 零 seed 表
   （sys_operation_log／sys_access_log／sys_pwd_custody／sys_user_email_verify）未實暴
   runtime 寫入、不預先收窄；擴充＝常數加一行，「seed 必空」斷言對新成員自動生效。

## 後果

- 走查後毋須先跑收尾即可過 gate2（對三表）；三表**實庫列內容**自此不在 gate2 射程。
- 結構面（欄序／COPY 段首／setval 行存在）與其餘表的逐列 diff 強度不變；
  凍結 seed.sql 與 specs/ 零改動（收窄語意權威＝本 ADR＋工具 docstring）。
- 自測 88→99（六臂反例＋常數釘死＋確認輪 M16 補釘）；變異自證 20 支全殺。
- quickstart 對此三表的清理步驟自此屬衛生選做、非 gate 前置（該文件屬已收刀 spec、
  不回改；後續刀如需引用以本 ADR 為準）。
