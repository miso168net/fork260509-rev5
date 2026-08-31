<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=b827063｜rust-api=3be868e

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：75（accepted 73、superseded 2）
- BACKLOG 待辦：26（next：B-156）｜滯後：7
- LESSONS：74 筆（next：L-075）
- events：89 筆（feature_close 7、misc 48、perf 34）

## 最近事件（尾 3 筆、新在前）
- 2026-08-31｜misc｜docs×tools 維護批 W3（主線直改）：前批 triage 未落帳判讀收割 5 筆補記——B-131 三候選皆非輕量、B-145 needs_sdd、B-028 觸發前提未成立、B-125 精度修正、B-139 三語互比不可替代候選①；滯後卷 B-059 關帳刪列——間歇假紅根因已定位（成功列 txn 時戳 vs 失敗列語句時戳兩種時間基準）並以 DB 端錨定結構性修除、119 輪僅 1 紅且另因 redis TTL
- 2026-08-31｜misc｜docs×tools 維護批 W2：B-152 ①～⑤組全數晉升——14 條 LESSONS 續句落地 CLAUDE.md §2～§5（13 條候選晉升位＋L-003 防法①③、含 L-038 之 §4 勘誤半句）；B-155 拍板落地 ADR 0075——review 報告＋review 事件義務收斂為僅適用不定期獨立 review 輪、feature／維護批收刀 final holistic review 以收單 commit＋findings 三分流承載；B-152／B-155 關帳；CLAUDE.md 212→229 行
- 2026-08-31｜misc｜docs×tools 維護批 W1：Lint29 掃描面存在性守衛補 fail-loud else 腿（B-153 關帳）＋Lint11 禁入詞典加預告三詞（屆時／日後／將由、警告級）＋Lint30 bash 面條款上線（$VAR 後緊接非 ASCII 即紅、掃描面＝外層 tracked *.sh＋shebang 檔）＋errata 補子庫 pin 樹碼面掃描腿（SUBMODULE_ID_SCAN 樣式集、掃描未執行即 fail-loud）＋wf-watchdog 檔頭 resume 段補冒煙殘留註記；lint 條款 28→29

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-31 10.94s、2026-08-31 12.9s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
