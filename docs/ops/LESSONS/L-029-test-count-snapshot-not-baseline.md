---
promoted_to: rust-api/server/tests/wire_schema.rs 之「數字為快照量非不變式」註＋rust-api/server/src/throttle/mod.rs 零回歸判準註＋specs/004-ip-trust-anchor/tasks.md T014／T047 DoD（量測法取代帳面數）
---
- **L-029**｜**帳面測試數當「零回歸」判準＝跨批次必失真、且會製造假回歸警報**：NOTES／STATE 記的測試數是**收刀當時的快照**（003 收刀＝「測試 145→321」），其後的維護批會把它推走而**沒有任何機制回頭改那句話**——它住在過去式帳裡、本來就不該是活判準。004 的 tasks.md 兩處 DoD（T014／T047）直接引了 `321`，我又把它抄進 U-C 的 agent prompt 當「既有 321 支測試仍全綠」。實測基線是 **server lib 260／全 target 合計 327（另 2 ignored）**，差 6 支。implementer 這次自己查證後在 report 裡校正了（U-C 收尾覆核確認其正確），但同一形也可能反向作用：實作者看到「帳面 321、實測 327」而去找不存在的回歸，或更糟——把自己造成的真回歸當成「帳面本來就對不上」而放過。★防法：①**DoD 與 agent prompt 一律不寫死測試數**，改寫量測法——「動工前先跑一次基線、以**動工前後同一指令逐 target 比對**為準」；②真要引數字時必須同時寫明「量測日期＋量測指令」，讓它自證為快照而非不變式；③帳面數字（NOTES／events）只當史料，反查現況一律回機器面重跑。★同批附帶查證（推翻一則 agent 說法，記此以免下次又被『修正』）：`cargo test -p server <mod>::` **不必**加 `--lib` 也抓得到 lib 內 `#[cfg(test)]`（實測 26 passed／260 filtered out）；會誤判成「抓不到」是因為其餘 target 會各印一行`0 passed; N filtered out`，看起來像過濾器沒命中。

