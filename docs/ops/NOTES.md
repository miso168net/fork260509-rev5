# NOTES — 當前意圖／下一步

- **創世序列（B0～B11）全部收官**：B8b 移植驗收後段與 B11 的 K1／K2 處置流水（ADR 0009）
  已收單，創世 DoD 全數關帳；啟動書 §5 自此為候選清單史料（K1 查用點＝各刀階段 0、
  K2 查用點＝BACKLOG 條目本文）。
- 帶 migration 的刀沿用 001 立的紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。
- **提前批（B-035～B-039、bash→python 轉換帳）全數收單**（merge 2d22fb6／ebd327a／
  7a140f4／ab31065／08361f5；ADR 0010 轉換集收攏、ADR 0011 ③類首例落地、ADR 0013
  安全姿態入帳）。兩筆待補：B-035 雙平台 DoD 之 macOS 側（同事機 bootstrap＋test 全套）；
  setup-reaper 正向 ALTER ROLE 一輪待建 reaper role 之刀（rev4:m012 承襲、詳收刀事件）。
- **B12 前維護批全數收單**（輕量軌、merge 4e97031、分支與單元 commit 詳收刀事件；
  ADR 0014～0017 拍板同批落地）：B-002｜B-005｜B-006｜B-007｜B-010｜B-012｜B-013｜
  B-015｜B-040｜B-041 十項關帳＋B-023 第一段（backup-db.py＋非破壞 scratch 還原演練）；
  效能預算入 RUNBOOK §12.1（基礎鏈 7.0s／最壞 staged 26.8s、拆批未觸發）；第三把離線
  復原鑰入列（recipient 2→3）；wf-watchdog 轉 python＋硬編目標參數。衍生 B-042。
- 下一步＝**B12 第一把功能刀**（後端首刀、spec-kit 流程原樣）。brainstorm 第一題＝
  功能域（是否含 auth／是否含寫端——B-017｜B-020｜B-021｜B-022｜B-024｜B-026 併刀
  與否繫於此）；
  直接輸入＝B-014＋B-001＋K1 對應域條目；起手 tasks 必含 zh-tw.ts＋兩筆 Day-1 豁免
  下架（lint24.day1／gen.router——server/src 第一支 .rs 落地即紅）＋B-028 起手量測；
  R_SUPER 選單 4 項 404＝已知態（B-008）。
