# NOTES — 當前意圖／下一步

- **已收官**：查 `docs/generated/MILESTONES.md`（事件表；★perf 型不入該表、另居
  `docs/generated/reference/perf.md`）與 `docs/generated/STATE.md` 尾 3 筆；逐批全文在
  `docs/ops/events.jsonl`——本檔不再鏡像（ADR 0070）。
- **其餘在案候選**：B-125／B-131／B-133；
  兩筆待補（皆無在案編號、留帳於 events）：雙平台 DoD 之 macOS 側（2026-08-07 B-035 收單時留）、setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀；帶 migration 的刀沿用
  001 紀律（收刀前 refresh＋演進帳登記＋三閘綠，RUNBOOK §10）。★滯後卷另有數條（實數見 STATE.md 帳面統計；查全帳須併看 BACKLOG-DEFERRED.md）；
  B-057 已裁關帳（ADR 0059＝維持現行、代價與翻案觸發器逐字入該 ADR）。
- **★下一動作＝008-audit-settings-pages 之 TDD 實作起手**（branch `008-audit-settings-pages`、
  SDD 五步已全數完成：specify→clarify（零提問）→plan（憲法九題通過）→tasks（37 支、覆蓋
  100%）→analyze（零 CRITICAL、微補已落帳）——起手＝superpowers:executing-plans 讀
  `specs/008-audit-settings-pages/tasks.md`、批判複核分執行單元（建議收攏 U0~U6＝tasks.md
  Implementation Strategy）、Workflow 編排照 CLAUDE.md §2 範本。★次序鐵則：U0 修憲
  （用途 (vii)(viii)＋行為島候選 user 親決＋BizData 射程補充 ADR）先於一切 base-web
  WIRING 面與 purge BizData 構造點。brainstorm＝`docs/brainstorms/008-audit-settings-pages.md`；
  拍板②承載＝ADR 0076。
- **效能現況**：全序列→`docs/generated/reference/perf.md`、引信判讀→`docs/generated/STATE.md`「效能引信」行（機器判、
  只採 close_bookkeeping）；merge commit 不跑 pre-commit 之事實住 RUNBOOK §12.1。
