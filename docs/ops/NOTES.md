# NOTES — 當前意圖／下一步

- **創世序列（B0～B11）全部收官**：B8b 移植驗收後段與 B11 的 K1／K2 處置流水（ADR 0009）
  已收單，創世 DoD 全數關帳；啟動書 §5 自此為候選清單史料（K1 查用點＝各刀階段 0、
  K2 查用點＝BACKLOG 條目本文）。
- 帶 migration 的刀沿用 001 立的紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。
- **提前批（B-035～B-039、bash→python 轉換帳）全數收單**（merge 2d22fb6／ebd327a／
  7a140f4／ab31065／08361f5；ADR 0010 轉換集收攏、ADR 0011 ③類首例落地、ADR 0013
  安全姿態入帳）。兩筆待補：B-035 雙平台 DoD 之 macOS 側（同事機 bootstrap＋test 全套）；
  setup-reaper 正向 ALTER ROLE 一輪待建 reaper role 之刀（rev4:m012 承襲、詳收刀事件）。
- **B12 前四題已拍板（2026-08-07、ADR 0014～0017）**：B-031＝prod 不入 rev5 roadmap
  （各刀留 seam、region 欄 UI 先不做、輪替維持觸發式、多副本假設不成立）；B-032＝前提
  未成立原樣過境（衍生 B-040/B-041）；B-012＝前綴通配＋具名豁免；B-015＝Lint06 基準改
  merge^1。B-031/B-032 收單、B-012/B-015 施工併維護批。
- 下一步＝**B12 前維護批**（輕量軌逐支）：①B-023 第一段（備份＋一次真還原演練）＋
  B-040/B-041＋errata 三筆（README wf-watchdog「刻意 bash」標註 vs ADR 0010 矛盾、
  B-022 條目改 rev5 實況、B-030⑧「單一來源」改 parity 檢查）→②schema-gate 群
  （B-006＋B-013＋B-012 施工）→③docs-sync 群（B-002＋B-015 施工＋B-010）→④B-005→
  ⑤B-007 壓軸定預算表。★中途量測：pre-commit 自測情境（現 27s）超 35s 即拆批。
- 維護批後＝**B12 第一把功能刀**（後端首刀、spec-kit 流程原樣）。brainstorm 第一題＝
  功能域（含是否含 auth／是否含寫端——6 條 BACKLOG 分類繫於此）；直接輸入＝B-014＋
  B-001＋K1 對應域條目；起手 tasks 必含 zh-tw.ts＋兩筆 Day-1 豁免下架（lint24.day1／
  gen.router——server/src 第一支 .rs 落地即紅）＋B-028 起手量測。
