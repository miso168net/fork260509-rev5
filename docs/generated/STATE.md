<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=b827063｜rust-api=b1ec283

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：71（accepted 69、superseded 2）
- BACKLOG 待辦：34（next：B-155）｜滯後：8
- LESSONS：74 筆（next：L-075）
- events：78 筆（feature_close 7、misc 40、perf 31）

## 最近事件（尾 3 筆、新在前）
- 2026-08-31｜misc｜外層維護批 U4：B-030 子項「機密清單 parity 檢查」出列＝deploy/decrypt-secrets.py 自測層五面 parity 斷言上線（generate 13／preflight 13／compose 12／enc 10／EXPECTED_KEYS 10、差額具名常數、各面仍各寫一份）＋B-023 半件＝deploy/backup-db.py 新增 drill 子命令（非破壞 scratch 演練、只刪 drill 名、真跑逐位元相等）＋RUNBOOK §6 縮編（§6.2 一行命令、新增 §6.5）；B-023 餘排程化、B-030 餘四子項、皆未關帳
- 2026-08-31｜misc｜外層維護批 U3：B-144 關帳＝base-web ip-rule/index.vue 之 scroll-x 註解改為 eslint --fix 產出的 multiline 形（全樹唯一違反 vue/html-comment-content-newline 者、rev5 新增檔零原行；pnpm lint 自此不再改寫允許清單外既有檔）；候選②「pre-commit 加清單外檔斷言」判不可行（允許清單只在 workflow script 常數、子庫 pre-commit 零 python、攔截點錯）；pnpm typecheck 綠、pin 前進一顆
- 2026-08-30｜misc｜外層維護批 U2：B-091 關帳＝LESSONS 11 條 promoted_to 佔位盤完（3 條回填 L-023／L-032／L-043、4 條補句後回填 L-022／L-042／L-052／L-053、4 條「無：候選位不在本單元允許面」L-001／L-012／L-037／L-038、零條改寫防法）＋L-062～L-072 尾巴 11 條標記（已兌現 3、仍待 8）＋CLAUDE.md 兩句（§2 防呆⑥／§4）＋三筆活書補記（RUNBOOK §9 稽核欄複驗、L-062 symlink 句、§16.4 retention 指針列；B-078 縮為指針、B-133／B-016 不關帳）

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-30 9.97s、2026-08-30 12.24s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
