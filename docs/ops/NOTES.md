# NOTES — 當前意圖／下一步

- **已收官**：查 `docs/generated/MILESTONES.md`（事件表；★perf 型不入該表、另居
  `docs/generated/reference/perf.md`）與 `docs/generated/STATE.md` 尾 3 筆；逐批全文在
  `docs/ops/events.jsonl`——本檔不再鏡像（ADR 0070）。
- **其餘在案候選**：B-131／B-133；
  兩筆待補（皆無在案編號、留帳於 events）：雙平台 DoD 之 macOS 側（2026-08-07 B-035 收單時留）、setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀；帶 migration 的刀沿用
  001 紀律（收刀前 refresh＋演進帳登記＋三閘綠，RUNBOOK §10）。★滯後卷另有數條（實數見 STATE.md 帳面統計；查全帳須併看 BACKLOG-DEFERRED.md）；
  B-057 已裁關帳（ADR 0059＝維持現行、代價與翻案觸發器逐字入該 ADR）。
- **★下一動作＝待定**（008-audit-settings-pages 已於 2026-09-02 收官、merge `448b450`；四處遠端
  已同步：外層 default 與 feature branch、兩子庫長名分支）。**B-008 至此關帳**——rev4 專屬管理頁
  在 rev5 base-web 全數兌現，`tools/seed-view-gate.py` 豁免表**歸零**。
- **★下一刀的候選輸入**：BACKLOG 在案 28 條（next B-165；★本刀新增九條 B-156～B-164，其中
  **B-159／B-162 同族**——rev5 新增型新檔的檔頭標記、與 `app.d.ts` 那塊圈界標記，對
  `fork-delta-lint` 皆**零機器守／零鑑別力**，已各附實測紅綠證與處置候選，宜同批處置）；
  滯後卷另計（查全帳須併看 `docs/ops/BACKLOG-DEFERRED.md`）。動工前先跑階段 0 brainstorm
  （產出存 `docs/brainstorms/<NNN>-<feature-name>.md`）、specify 必**手動**起手。
- **效能現況**：全序列→`docs/generated/reference/perf.md`、引信判讀→`docs/generated/STATE.md`「效能引信」行（機器判、
  只採 close_bookkeeping）；merge commit 不跑 pre-commit 之事實住 RUNBOOK §12.1。
