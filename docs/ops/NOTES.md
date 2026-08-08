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
- **B12（002-system-settings）已收刀**：rust-api server crate 首次落地、後端管線縱切
  全通（router→enforce_mw→require_policy→handler→validation→facade→envelope）；
  三筆 Day-1 豁免處置完畢、ADR 0020~0023 拍板、活書 §5 §8 回填 as-built；
  B-014 與 B-026 一併關帳。實作細節、教訓與 review 攔截面詳收刀事件。
- **下一步＝尚未拍板**。候選（依 BACKLOG 條目的觸發條件）：①**auth 域整批**
  （B-017 會話生命週期一次設計完整／B-020 失敗計數節流通用 seam／B-021 改密端點節流／
  B-022 替代登入四流程做真或砍）——四條彼此高度相依、宜同一 brainstorm 一次拍範圍，
  且 B-017／B-022 都帶「前代兩段式翻案」的明確反面教材；②**B-008 四張 rev4 專屬管理頁
  view**——其中 manage_system-settings 可直接消費本刀已通的讀寫端點，是驗證前端腿
  分層（typings／service 已備、僅缺 view）的最短路徑；③**B-024 寫端授權下放三件套**
  ——no-escalation 掛點已於本刀備妥（ADR 0022 定形、現況恆放行、簽章已預留 async＋db）。
  ★不論走哪條：開場即階段 0 brainstorm，specify 一律手動起手（否則 feature-branch
  pre-hook 不跑、spec 會落在 default branch 上）。
