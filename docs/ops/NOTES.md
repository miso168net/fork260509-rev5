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
  ＋rebuild-swap 熱重載＋歸檔寫入面三底座就緒（授權治理刀依賴面全兌現）｜
  **授權治理刀起手維護批**（輕量軌、merge 524d8b9：B-094 收攏＝handler/common.rs 六件＋facade violated_constraint、
  B-101 test_db::test_state 單一字面＋(Router, AppState) 變體、B-085 自證測、B-102 三測、B-098 十二裁判；四筆關帳、測試 650→682）｜
  **006-authz-governance**（merge 307ed51、本代第六刀、B-088 關帳）：三維授權治理 11 端點、ROUTES 49 終態、測試 682→793、憲法 1.8.0（島 G＋(iii)(iv)）、ADR 0053～0056、零 migration；
  封死＋射程＝候選集＋五腿 restore；三 modal 接真＋policy-archive 頁；seed-view-gate；wire 75。
  啟動書 §5 自此為候選清單史料（K1→各刀階段 0、K2→BACKLOG 條目本文；★其內裸 B／L 編號屬 rev4 空間、Lint25 掃描面外＝L-014）｜
  **刀 B 起手維護批**（批次 A、輕量軌、merge 3d72756）：測試設施＋工具鏈九筆關帳（B-121／B-122 守衛面根因、B-109／B-110／B-051 收攏遷位、B-056 seam、B-114／B-118、B-112 rust 格式守門上線）；ADR 0057、L-056、工具名冊 15→16 支、rust 測試 793、零 migration｜
  **刀 B 前置維護批**（輕量軌、merge 53d7a67）：11 筆關帳（B-083 配額＋停損絆線／ADR 0058；B-106 消 N+1／B-108／B-115／B-123；B-111／B-075／B-074 三道守門；B-100／B-116／B-117 前端三件 CDP 實證含反例）；L-057～L-061、rust 測試 829、零 migration。
- 兩筆待補：B-035 雙平台 DoD 之 macOS 側；setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀。帶 migration 的刀沿用 001 紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。

- **★下一刀＝刀 B（user＋password 管理）**：B-089／B-021／B-020 連鎖在彼、scope 已預拍「全納入含
  changePassword」（2026-08-18、記兩檔 §3 表 #4）；★起手必復核 B-093（deleteRole 判定面繼承窗）
  ＋B-113（R_SUPER wire 案前提、seed 未來端點註冊後重審）；seed 68（manage_user view）在彼兌現。
- **其餘在案候選**：B-008 餘兩張 view（＋audit 5 端點；豁免表到期即紅）；B-124／B-125／B-127～B-129／B-131～B-133。★另六條已滯後（查全帳須併看 BACKLOG-DEFERRED.md）；B-057 已裁關帳（ADR 0059＝維持現行、代價與翻案觸發器逐字入該 ADR）。
- ★下一動作＝刀 B **階段 0 brainstorm**（superpowers:brainstorming、產出 docs/brainstorms/<NNN>-<feature-name>.md）；
  specify 手動起手（絕不排自動流程、否則 spec 落 default）→ clarify → plan → tasks → analyze、每步 commit。
  兩批前置維護皆已收（B-111 已立 i64 守衛 lint＝刀 B 新 wire 型漏標即紅）；brainstorm 輸入見 BACKLOG 各條（建議 demo 資產三條併入一次拍）；★硬前置 B-126 已關帳（ADR 0062、merge 5cd4319）：§5 70/90、§8 53/130、配額表整張不動；§9／§11 是指針節非逼近；日後任一節撞頂＝輕量軌下放（下一候選 §5 觀測面清冊→obs.rs）、不再逐次 ADR；附屬文件 FORK-DELTA-WIRING.md 同受活書三閘；★效能：B-130 已關帳（ADR 0061）——全鏈 43.46s→**13.09s**（3.3×）、真 hook 最重情境 24.1s，遠低於 ADR 0044 之 45s 警戒；根因＝drvfs I/O 稅非條款邏輯（L-062、微基準 587×），根治面（遷原生 WSL fs）留 B-133 備案。刀 B 收尾仍依 RUNBOOK §12.1 量測法實測一筆。
