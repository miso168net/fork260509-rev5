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
  觸發器重定、兩筆帳面孤兒登記、CLAUDE.md §2 補 resume 分岔；ADR 0038／0039）｜
  **004-ip-trust-anchor**（merge 9141e14、B-019 關帳：信任錨還原八態＋IP 存取閘與門鈴熱重載＋
  IP 規則管理頁與五支端點＋來源維節流＋管理員解鎖端點，ROUTES 16→22 終態、rust 測試 321→512、
  憲法 1.3.1→1.6.2＝島 F 入憲＋第五條 ★ 軌道，ADR 0040～0044；新守門工具兩支）｜
  **B-090 LESSONS 分檔制遷移批**（輕量軌、merge ae5c24d：分卷制→分檔制——手寫索引＋
  一坑一檔＋晉升必答欄 promoted_to（實值 35／佔位 12→B-091 承載）、47 條 byte-diff 逐位
  搬運、Lint26＋單條上限＋Lint09 head 視野聯集、ADR 0045、docs-sync 自測 496→517）｜
  **治理工具鏈整併批**（輕量軌、merge d72553b：B-080 納冊（TOOLS_PY 14）＋B-081 Lint27
  README 樹對賬＋B-086 compose anchor 消抄本＋B-092 bootstrap 物理化＋B-087 半關；
  ADR 0046／0047、L-048、lint 條款 26、docs-sync 自測 524）｜
  **005-role-menu-crud**（merge 0125f8c、本代第五刀）：role＋menu CRUD 16 端點、ROUTES 38
  終態、測試 512→650、憲法 1.7.0（島 H＋用途(ii)）、ADR 0048～0052、零 migration；序列化域
  ＋rebuild-swap 熱重載＋歸檔寫入面三底座就緒（授權治理刀依賴面全兌現）。
  啟動書 §5 自此為候選清單史料（K1 查用點＝各刀階段 0、K2＝BACKLOG 條目本文；
  ★其內裸 B／L 編號屬 rev4 空間、該目錄在 Lint25 掃描面外＝L-014）。
- 兩筆待補：B-035 雙平台 DoD 之 macOS 側；setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀。
- 帶 migration 的刀沿用 001 立的紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。

- **★下一刀＝授權治理刀**（brainstorm 已於 005 階段 0 同場定稿、★暫存版控外〔tmp/ 備份〕、
  起手時補入版控、檔名配號接續 005）：三維授權治理 11 支＋島 G 入憲＋結構性封死〔B-024①歸宿〕＋
  policy-archive 頁〔B-008 出列一張〕；依賴之 005 底座（序列化域／熱重載／歸檔寫入面）已全兌現。
  ★起手維護批（改期落此、2026-08-22）＝B-094＋B-101 收攏；島 G 入憲順捎＝ADR 0052 條款入
  §III 正文＋B-104（ADR 0049 括號句訂正）。
  刀 B（user＋password）＝再之後：B-089／B-021／B-020 連鎖在彼、scope 已預拍「全納入含
  changePassword」（2026-08-18、記兩檔 §3 表 #4）；★刀 B 必復核 B-093（deleteRole 判定面繼承窗）。
- **其餘在案候選**：B-008 餘兩張 view（manage_system-settings／audit＋audit 5 支端點；policy-archive 由授權治理刀承接、★連帶 B-088 對賬閘宜同批）。
- ★下一動作＝授權治理刀起手：①階段 0 **已定稿**＝docs/brainstorms/006-authz-governance.md
  （2026-08-22 五 lens 偵查後重寫、取代 tmp/ 舊草稿）②**待 user 拍該檔 §10 之 22 題**
  ③起手維護批（B-094＋B-101）④手動起 /speckit-specify（絕不排自動流程、否則 spec 落 default）。
