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
- **B12 brainstorm 已完成**（docs/brainstorms/002-system-settings.md、2026-08-08）：
  功能域＝系統設定（沿用 K1-08＋K1-27、auth 域全數續 defer）；前端腿＝typings＋
  service 接線層（ADR 0018、零修憲、view 延 B-008、選單 404 已知態）；寫端＝含讀＋寫
  （B-026 三態約定層與 B-024 授權 seam 入刀設計期定形）。
- 下一步＝**手動 `/speckit-specify docs/brainstorms/002-system-settings.md`**（不自動
  觸發——feature branch pre-hook 須在 specify 時建 002-system-settings 分支、否則
  spec 落 default）→ SDD 五步照走。起手 tasks 必含 zh-tw.ts＋兩筆 Day-1 豁免下架
  （lint24.day1／gen.router——server/src 第一支 .rs 落地即紅）＋B-028 起手量測
  （第二輪在 server 依賴進場後）；clarify 候選四題已列 brainstorm 檔 §4。
