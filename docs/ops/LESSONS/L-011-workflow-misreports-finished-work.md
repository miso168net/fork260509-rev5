---
promoted_to: CLAUDE.md §2 防呆④⑤（review 不共用 status 欄＋fix 跑滿上限後的確認輪）
---
- **L-011**｜workflow 編排 script 把**已完成的工作誤報成失敗**，主線因而多花整輪查證；
  兩種結構性成因、maint-l010 一批內各撞一次：①**狀態欄語意複用**——review agent 沿用
  implementer／fix 的 `{status: 'ok'|'blocked'}` schema，script 依「status≠ok→立即 return
  升級主線」處置；但 agent 把 `blocked` 讀作「我發現了 blocker」（審查結論），script 讀作
  「agent 受阻無法完成」（工作狀態），同一個字兩種語意。實暴＝單元② spec review 回
  `blocked` 帶 1 筆 blocker，script 當場 return，**fix 迴圈整個沒跑**，一筆本可自動修掉的
  finding 直接升級主線。②**迴圈跑滿無確認輪**——fix 迴圈寫成
  `for r in 1..=N { review → 空即 return 收斂 → fix }`，跑滿即 `return {converged:false,
  blockers: prevBlockers}`；但 `prevBlockers` 是**最後一輪 fix 之前**的快照，fix#N 修好了
  卻沒人再看一眼。實暴＝單元① 把兩筆早已被 fix#3 修掉的 blocker 報成 unresolved，主線逐檔
  復核才確認（該兩筆修得比 reviewer 要求的還完整）。防法：(a) **狀態欄不得跨角色複用**——
  「agent 是否受阻」與「審查結論」拆成兩個獨立欄位，script 分開處置；同一份 schema 要給
  不同角色用之前，先逐欄自問「這個欄位對這個角色是什麼意思」；(b) **迴圈收尾必有確認輪**
  ——fix 迴圈跑滿上限後再 review 一次，空 blocker 即判收斂，否則回不收斂並附**確認輪**的
  blockers（不是迴圈內的舊快照）；(c) 共通原則＝**script 回報的狀態必須反映最後一次動作
  之後**，任何「先存快照→再動作→回報快照」的結構都會誤報。機器面紀律已同步進 CLAUDE.md
  §2 防呆六件套之 ④⑤。

