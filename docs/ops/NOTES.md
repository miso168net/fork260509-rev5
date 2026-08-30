# NOTES — 當前意圖／下一步

- **已收官**：查 `docs/generated/MILESTONES.md`（事件表；★perf 型不入該表、另居
  `docs/generated/reference/perf.md`）與 `docs/generated/STATE.md` 尾 3 筆；逐批全文在
  `docs/ops/events.jsonl`——本檔不再鏡像（ADR 0070）。
- **其餘在案候選**：B-008 餘兩張 view（＋audit 5 端點；豁免表到期即紅）；B-125／B-131／B-133；
  兩筆待補：B-035 雙平台 DoD 之 macOS 側、setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀；帶 migration 的刀沿用
  001 紀律（收刀前 refresh＋演進帳登記＋三閘綠，RUNBOOK §10）。★滯後卷另有數條（實數見 STATE.md 帳面統計；查全帳須併看 BACKLOG-DEFERRED.md）；
  B-057 已裁關帳（ADR 0059＝維持現行、代價與翻案觸發器逐字入該 ADR）。
- **★進行中＝下一刀起手維護批**（輕量軌、拍板 2026-08-30、自 default f1c0951 開出）：四條 docs-sync 條款面＋B-124①。
  首條（效能資料點事件源化）已由本批 U1 落地＝ADR 0070（events `perf` 型別＋`reference/perf.md`＋STATE 效能引信、
  RUNBOOK §12.1 瘦身、本檔已收官段刪除）；B-146／B-148 已由本批 U2 落地＝Lint28（活書 §1 建置狀態 ⊇ events feature_close 刀號集）／Lint29（子庫碼面裸 B-／L- 編號超出本代 next-id 即紅）；B-147 已由本批 U3 落地＝tools/walkthrough-baseline.py＋RUNBOOK §9c 走查還原契約；B-124① 已由本批 U4 落地＝ADR 0071（won't-fix／by-design——各檔各持一份係取捨、不收攏至 `model::test_db`，零碼行為改動）。
- **批後＝下一刀本體待拍板**：候選 B-008 餘兩張 view＋audit 五端點（豁免表到期即紅）／B-125／B-133。
  ★SDD 五步之 specify **手動**起手。
- **效能現況**：全序列→`docs/generated/reference/perf.md`、引信判讀→`docs/generated/STATE.md`「效能引信」行（機器判、
  只採 close_bookkeeping）；merge commit 不跑 pre-commit 之事實住 RUNBOOK §12.1。
