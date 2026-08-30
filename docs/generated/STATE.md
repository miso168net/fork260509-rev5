<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=7b7cd86｜rust-api=b1ec283

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：71（accepted 69、superseded 2）
- BACKLOG 待辦：33（next：B-153）｜滯後：8
- LESSONS：73 筆（next：L-074）
- events：76 筆（feature_close 7、misc 38、perf 31）

## 最近事件（尾 3 筆、新在前）
- 2026-08-30｜misc｜外層維護批 U2：B-091 關帳＝LESSONS 11 條 promoted_to 佔位盤完（3 條回填 L-023／L-032／L-043、4 條補句後回填 L-022／L-042／L-052／L-053、4 條「無：候選位不在本單元允許面」L-001／L-012／L-037／L-038、零條改寫防法）＋L-062～L-072 尾巴 11 條標記（已兌現 3、仍待 8）＋CLAUDE.md 兩句（§2 防呆⑥／§4）＋三筆活書補記（RUNBOOK §9 稽核欄複驗、L-062 symlink 句、§16.4 retention 指針列；B-078 縮為指針、B-133／B-016 不關帳）
- 2026-08-30｜misc｜外層維護批 U1（輕量軌、docs-sync 條款面小修）：Lint19 跨段續值文法容許 `<…>` 佔位 token（B-150；RUNBOOK §12 表列 diff／test 與 CLAUDE.md §7 diff 三 token 進判定）／Lint29 掃描面 rust-api 加 *.toml＋docstring 登記排除理由（B-151；現況四筆命中皆合規）／Lint24 第二腿 zh-cn backend 鍵集＝zh-tw 鍵集上線（B-030 出列該子項、面數四→五）／B-120 觸發器改述；B-150／B-151 關帳、條款數仍 28
- 2026-08-30｜misc｜下一刀起手維護批收單（輕量軌、merge f8da2e4）：B-149 效能資料點事件源化（ADR 0070；RUNBOOK 900→806、NOTES 40→16）／B-146＋B-148＝Lint28／Lint29 上線（條款 26→28）／B-147＝tools/walkthrough-baseline.py＋RUNBOOK §9c 走查還原契約／B-124①＝won't-fix ADR 0071；docs-sync 自測 533→599、TOOLS_PY 16→17、perf 事件回填 28；final holistic 13 筆全處置、B-150／B-151 開立

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-30 9.97s、2026-08-30 12.24s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
