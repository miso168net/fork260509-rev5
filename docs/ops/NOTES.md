# NOTES — 當前意圖／下一步

- **已收官**（過去式細節一律查 events＋git，此處只留查用指針）：創世序列 B0～B11｜提前批
  B-035～B-039 與 bash→python 轉換帳｜B12 前維護批（十項＋B-023 第一段）｜B12
  002-system-settings（rust-api server crate 首落地、後端管線縱切全通）｜B12 後衛生維護批
  （merge cdf6eb7：B-049／B-052／B-045／B-011 關帳＋B-042 收②半、ADR 0026）｜帳面更正批
  （merge ea4a470：六條目對齊 rev5 實況＋L-014＋B-043 兩處置候選實證推翻，零關帳）｜
  **003-auth-session**（merge 537b021、本代最大一刀：五個 user story 全交付、ROUTES 4→16 終態、
  測試 145→321、憲法 1.2.0→1.3.0、DAY1_EXEMPTIONS 自此空表）｜**工具面維護批**（輕量軌、
  merge b5e1be5：B-042／B-063／B-065／B-067／B-068／B-069 六筆關帳，憲法 1.3.1＋ADR 0035～0037）｜
  **帳面缺口批**（輕量軌、merge 988faf9、零碼改動：B-047 補記關帳＋B-022 拍板關帳，四筆失效
  觸發器重定、兩筆帳面孤兒登記、CLAUDE.md §2 補 resume 分岔；ADR 0038／0039）。
  啟動書 §5 自此為候選清單史料（K1 查用點＝各刀階段 0、K2＝BACKLOG 條目本文；
  ★其內裸 B／L 編號屬 rev4 空間、該目錄在 Lint25 掃描面外＝L-014）。
- 兩筆待補：B-035 雙平台 DoD 之 macOS 側（同事機 bootstrap＋test 全套）；setup-reaper
  正向 ALTER ROLE 一輪待建 reaper role 之刀。
- 帶 migration 的刀沿用 001 立的紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。

- **★下一刀已拍板（user 2026-08-12）＝IP／信任錨刀**，核心＝B-019：本域是 repo 內**基建完成度
  最高、實作完成度為零**的一塊（nginx 側 CF 權威驗證閘已完整、`sys_ip_rule` 與 seed 與 casbin
  政策全在且零列零碼、`request_context.rs` 已把 seam 寫死在碼內、rev4 約 3,600 行藍本）。
  ★**射程、六個拍板級前置與兩項檢查點一律見 B-019 條目本文**（brainstorm 直接輸入）。
- **後續候選**（本刀之後）：後端 role／user 管理寫端（同時解 B-008 的一半與 B-024 全部前置）。
- ★不論走哪條：開場即階段 0 brainstorm，specify 一律手動起手（否則 feature-branch pre-hook
  不跑、spec 會落在 default branch 上）。
