# NOTES — 當前意圖／下一步

- **已收官**（過去式細節一律查 events＋git，此處只留查用指針）：創世序列 B0～B11｜提前批
  B-035～B-039 與 bash→python 轉換帳｜B12 前維護批（十項＋B-023 第一段）｜B12
  002-system-settings（rust-api server crate 首落地、後端管線縱切全通）｜B12 後衛生維護批
  （merge cdf6eb7：B-049／B-052／B-045／B-011 關帳＋B-042 收②半、ADR 0026）｜帳面更正批
  （merge ea4a470：六條目對齊 rev5 實況＋L-014＋B-043 兩處置候選實證推翻，零關帳）。
  啟動書 §5 自此為候選清單史料（K1 查用點＝各刀階段 0、K2＝BACKLOG 條目本文；
  ★其內裸 B／L 編號屬 rev4 空間、該目錄在 Lint25 掃描面外＝L-014）。
- 兩筆待補：B-035 雙平台 DoD 之 macOS 側（同事機 bootstrap＋test 全套）；setup-reaper
  正向 ALTER ROLE 一輪待建 reaper role 之刀。
- 帶 migration 的刀沿用 001 立的紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。

- **下一步＝auth 域整批**（B-017 會話生命週期一次設計完整／B-020 失敗計數節流通用 seam／
  B-021 改密端點節流／B-022 替代登入四流程做真或砍）。三候選勘查後的排序依據：**只有
  auth 不依賴另外兩者，而另外兩者都依賴它**——B-008 要「頁面看得到」的依賴鏈終點是
  `/auth/login`＋`/route/getUserRoutes`；B-024 的落地對象 role／user 管理寫端在 rev5 後端
  零實作（handler 目錄僅 system_settings.rs），無法單獨成刀。
  - **範圍切法＝零修憲**：後端補齊 base-web fork 原版 service 已在呼叫的 6 支端點
    （`/auth/login`／`/auth/getUserInfo`／`/auth/refreshToken`／`/route/getConstantRoutes`／
    `/route/getUserRoutes`／`/route/isRouteExist`）；base-web 只動 `.env*`（§III.1 ADAPT
    預設軌道：base URL 由 apifox mock 翻 `/api`、加 VITE_PROXY_TARGET、auth route mode
    static→dynamic 以兌現憲法 §II #2）。憲法 §II #1（rust-api 忽略 apifoxToken、base-web
    不動）正是為此準備，故零 base-web inline。
  - **資料面已是終態**：sys_token 9 欄＋rotation partial UNIQUE＋session_event＋
    sys_user.session_policy／session_id＋16 個節流與會話設定鍵全在 001 baseline，
    **B-017 不需要新 migration**——除非拍板棄 redis 改 DB 承載 idle／denylist，那會反過來
    變成 additive DDL。
  - **開場必拍四題（拍板級）**：①redis 進場否（決定 AppState 開幾欄＝state.rs 明文的拍板級
    翻案，也決定會不會變成帶 migration 的刀）②未認證回 8888 還是翻回 3333（002 拍板翻案、
    user 可見行為）③B-022 做真／砍／維持現狀立 ADR（前兩者都動 fork login inline→觸發修憲）
    ④B-029 captcha 進不進（建議不進：rev5 前後端 captcha 皆零，實際是整套首版而非「半條」）。
  - 同刀順手收：B-018（前端首刀觸發）、B-050、B-051、B-047。
- **B-008 排在 auth 之後**：憲法 §III.2 至今零個 ★ 軌道，而新增任一 view 必然 inline 動
  zh-cn.ts／en-us.ts（route 鍵為窮舉型 Record）與 app.d.ts（新 i18n 命名空間＝面級新增），
  該刀第一件事＝修憲（ADR 0018 後果已預告）；四張頁另需 12 支不存在的後端端點。
  ★前一版把它寫成「驗證前端腿分層的最短路徑」，經勘查不成立——elegant routes.ts 連 route
  條目都沒有，且 static 模式下那四項根本不出現在側邊欄。
- ★不論走哪條：開場即階段 0 brainstorm，specify 一律手動起手（否則 feature-branch pre-hook
  不跑、spec 會落在 default branch 上）。
