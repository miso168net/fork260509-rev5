# NOTES — 當前意圖／下一步

- **已收官**：查 `docs/generated/MILESTONES.md`（事件表；★perf 型不入該表、另居
  `docs/generated/reference/perf.md`）與 `docs/generated/STATE.md` 尾 3 筆；逐批全文在
  `docs/ops/events.jsonl`——本檔不再鏡像（ADR 0070）。
- **其餘在案候選**：B-131／B-133；
  兩筆待補（皆無在案編號、留帳於 events）：雙平台 DoD 之 macOS 側（2026-08-07 B-035 收單時留）、setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀；帶 migration 的刀沿用
  001 紀律（收刀前 refresh＋演進帳登記＋三閘綠，RUNBOOK §10）。★滯後卷另有數條（實數見 STATE.md 帳面統計；查全帳須併看 BACKLOG-DEFERRED.md）；
  B-057 已裁關帳（ADR 0059＝維持現行、代價與翻案觸發器逐字入該 ADR）。
- **★進行中＝`008-audit-settings-pages` 之 TDD 實作**（SDD 五步已全數完成；編排照 CLAUDE.md §2 範本、
  一支 workflow 一個執行單元）。已落地單元：U0（修憲 1.10.0＋島 J 入憲＋ADR 0077／0078／0079）／
  U1（`Api.Audit` 契約錨）／U2（讀面全鏈）／U3（讀面兩層裁判）／U4＋U4b（purge 端點全鏈）／
  **本刀 U5**（`_with_db` 薄殼＋`LOCKABLE_TABLES` 擴列＋purge 原子性 fault-injection＋水平線三測＋
  logout TTL 同形補測——**B-125 關帳**）／**本刀 U6**（Lint24 第三腿＝佔位符 × 後端 `json!` 頂層鍵
  對賬＋三語併驗——**B-139 關帳**）／**本刀 U7**（system-settings 頁進場：view 單檔＋兩語 i18n
  ＋型節＋產物四檔＋seed-view-gate 摘一列＋用途 (vii) 之 L-063 變異自證；**B-008 settings 半邊
  出列**、CDP 走查證已知態反轉）／**本刀 U8**（audit 頁進場：service 5 fetcher＋view 七檔
  ＋兩語 58 葉＋型節＋產物四檔＋**seed-view-gate 豁免表歸零**＋用途 (viii) 之 L-063 變異自證
  〔11 輪、揭出 `app.d.ts` 型節標記零鑑別力＝B-162〕；**B-008 兩張 view 全數兌現**）。
  ／**本刀 U9**（主線做：CDP 三方對照六步全過〔欄集逐欄對照 rev4、唯一差異＝XFF 欄；XSS 注入 SC-003
  字面顯示零執行；purge 29 拒／3650 成功＋自記〕＋**關帳三條**〔B-008／B-072／B-078〕＋final
  holistic review〔SC 八條逐條驗、findings 三分流：修 0／轉 B-164 一條／won't-fix 0〕）。
  ⇒ **tasks 37/37 全勾、實作全數完成**。**下一步＝收刀**：finishing-a-development-branch →
  ★**push／merge 需 user 同意** → 簿記三步（events append＋NOTES＋generate）→ ★第四步（易漏）：
  簿記 commit 落地後量其牆鐘、append 一筆 `close_bookkeeping` perf 事件。brainstorm＝`docs/brainstorms/008-audit-settings-pages.md`。
- **效能現況**：全序列→`docs/generated/reference/perf.md`、引信判讀→`docs/generated/STATE.md`「效能引信」行（機器判、
  只採 close_bookkeeping）；merge commit 不跑 pre-commit 之事實住 RUNBOOK §12.1。
