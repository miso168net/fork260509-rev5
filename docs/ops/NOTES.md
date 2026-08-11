# NOTES — 當前意圖／下一步

- **已收官**（過去式細節一律查 events＋git，此處只留查用指針）：創世序列 B0～B11｜提前批
  B-035～B-039 與 bash→python 轉換帳｜B12 前維護批（十項＋B-023 第一段）｜B12
  002-system-settings（rust-api server crate 首落地、後端管線縱切全通）｜B12 後衛生維護批
  （merge cdf6eb7：B-049／B-052／B-045／B-011 關帳＋B-042 收②半、ADR 0026）｜帳面更正批
  （merge ea4a470：六條目對齊 rev5 實況＋L-014＋B-043 兩處置候選實證推翻，零關帳）｜
  **003-auth-session**（merge 537b021、本代最大一刀：五個 user story 全交付、ROUTES 4→16 終態、
  測試 145→321、憲法 1.2.0→1.3.0、DAY1_EXEMPTIONS 自此空表）。
  啟動書 §5 自此為候選清單史料（K1 查用點＝各刀階段 0、K2＝BACKLOG 條目本文；
  ★其內裸 B／L 編號屬 rev4 空間、該目錄在 Lint25 掃描面外＝L-014）。
- 兩筆待補：B-035 雙平台 DoD 之 macOS 側（同事機 bootstrap＋test 全套）；setup-reaper
  正向 ALTER ROLE 一輪待建 reaper role 之刀。
- 帶 migration 的刀沿用 001 立的紀律：收刀前必跑 refresh＋演進帳登記＋三閘綠（RUNBOOK §10）。

- **下一步＝兩條軌並存，先拍哪條走**：

  **(甲) 工具面維護批（輕量軌；自足、不依賴任何 feature）**——003 收刀新登記的七筆全在 `tools/`
  與 hooks，彼此獨立、規模小：B-063（fork-delta-lint 射程擴 `.env*`＋`build/`）／B-065（gate2 對
  append-only 稽核表的 seed 比對面收窄，★拍板級）／B-067（wire_schema 裁判面補三型）／
  B-068（fork-delta-lint 授權判定升成軌道×用途×檔案三元組）／B-069（wf-watchdog runaway 門檻對
  扇出型 workflow 必穿）。★B-068 與 B-063 同檔宜同批；★B-068 需先解 §III.2「型別」欄與 as-built
  的既有分歧，否則新判定會誤報。

  **(乙) 下一個 feature**——三個候選的現況**已被 003 改寫**，排序依據隨之變動：
  - **B-008 四張管理頁 view**：前置條件**真的解鎖了**——`.env` 已翻 dynamic ⇒「僅 R_SUPER 可見、
    點擊 404」自此成立；且 §III.2 名冊已存在 ⇒ 該刀不再是「開第一個 ★ 軌道」而是「在既有名冊上
    加用途」。但仍卡 **12 支不存在的後端端點**（audit 5／ip-rule 5／policy-archive 2）。
  - **B-024 寫端授權下放非超管**：落地對象 role／user 管理寫端在 rev5 後端**仍為零實作**
    （handler 目錄現有 auth/ 五支＋captcha＋route＋system_settings，無 role／user）。
  - **B-022 替代登入四流程做真或砍**：U-M 已把三表單誠實化（恆 `2222 notSupported`），
    ★**殘餘射程只剩拍板本身**——stub 是誠實化、不是實作；連帶 B-029 的圖形 captcha 首版亦已完成、
    只剩兩件小項。這條**最接近可以只靠一次對話拍完、不佔一把刀**。
  ⇒ (乙) 的前兩條指向同一件事：**下一刀是後端的 role／user 管理寫端**——它同時解 B-008 的一半
    與 B-024 的全部前置。B-022 可獨立先拍。
- ★不論走哪條：開場即階段 0 brainstorm，specify 一律手動起手（否則 feature-branch pre-hook
  不跑、spec 會落在 default branch 上）。
