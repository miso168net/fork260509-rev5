<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=7b7cd86｜rust-api=0161d73

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：70（accepted 68、superseded 2）
- BACKLOG 待辦：35（next：B-151）｜滯後：8
- LESSONS：72 筆（next：L-073）
- events：70 筆（feature_close 7、misc 35、perf 28）

## 最近事件（尾 3 筆、新在前）
- 2026-08-30｜misc｜Lint28／Lint29 上線（B-146、B-148 關帳、維護批 U2）：Lint28＝活書 §1 建置狀態 ⊇ events feature_close 刀號集（單向對賬、缺即 ERROR 指名刀名與收刀日）；Lint29＝兩子庫 pin 指向樹之碼面（rust-api *.rs、base-web src/ *.ts／*.vue）裸 B-／L- 編號超出本代 next-id 即 ERROR（git grep 粗篩＋Lint25 判準複用、skip／warn 沿 Lint17／Lint18）；名冊三檔範圍字串同 commit bump 至 Lint03～Lint29；本筆即新名冊承載事件
- 2026-08-30｜feature_close｜007-user-password-admin｜使用者與密碼治理縱切（本代第七刀、刀 B）：管理面十支＋自助兩支＝12 支端點，ROUTES 49→61 終值、POLICY 35→45 終態。六底座＝密碼政策單一驗證點／設密冷卻／改密舊密節流（第三個節流子系統）／no-escalation 掛滿八支寫端＋unlock 帳號維／斷權四路與三 reason 不互換／自助路由白名單帶回。前端 user 管理頁接真（七碼逐鈕 gating、解鎖 modal 雙維、回收桶）＋個人中心改密卡＋登入表單降必填。測試 829→998、wire-schema 75→89、憲法 1.8.0→1.9.1、ADR 0063～0069、零 migration。
- 2026-08-25｜misc｜B-126 關帳（輕量軌、merge 5cd4319、ADR 0062）：活書 as-built 下放首例——§8 fork-delta 接線段 45 行逐位元搬至附屬文件 FORK-DELTA-WIRING.md、§5 測試設施清冊 18 行下放 test_db 模組 doc；§5 85→70／§8 92→53、配額表整張不動（絆線零改動）；§9／§11 判為指針節、維持 5／3。docs-sync 掃描面擴至附屬文件（BOOK_ANNEXES、自測 529→533）。

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-25 16.68s、2026-08-30 9.97s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
