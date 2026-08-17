<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=bfeb783｜rust-api=bc8d7f3

## constitution
- 版本：1.6.2

## 帳面統計
- ADR：44（accepted 42、superseded 2）
- BACKLOG 待辦：39（next：B-091）｜滯後：1
- LESSONS：47 筆（next：L-048）
- events：26 筆（feature_close 4、misc 22）

## 最近事件（尾 3 筆、新在前）
- 2026-08-17｜feature_close｜004-ip-trust-anchor｜IP 信任錨縱切（本代第四刀、B-019 關帳）：真實來源還原八態／IP 存取閘（結構豁免、防自鎖、門鈴熱重載）／IP 規則管理頁與五支端點（含回收桶、sys_operation_log 首個寫入者）／來源維節流（節流自此雙維度）／管理員解鎖端點。ROUTES 16→22 終態、rust 測試 321→512、憲法 1.3.1→1.6.2（島 F 入憲＝第六座行為島＋§III.2 第五條 ★ 軌道）。
- 2026-08-12｜misc｜輕量軌維護批（帳面缺口七件＋B-022 關帳拍板、零碼改動）：B-047 應關未關補記關帳（ADR 0031 明令走收刀事件、003 收刀漏記，而 405→4040 早已實作＝條目描述之現況全反轉）／四筆失效觸發器重定（B-018／B-020／B-021／B-029 皆掛在已走過的刀上）／兩筆帳面孤兒登記（B-072 渲染端轉義、B-073 管理員解鎖端點）／B-008 與 B-024 殘句修文／CLAUDE.md §2 補 resume 分岔／ADR 0038 替代登入維持誠實 stub、ADR 0039 ip_* 三鍵已知態。
- 2026-08-12｜misc｜工具面維護批（輕量軌）：六筆關帳——wf-watchdog runaway 告警不再自我卸除＋上限自 script 快照推導／fork-delta-lint 掃描面擴 .env* 與 build/、授權判定升（軌道×用途×檔案）三元組／wire_schema 裁判面補 Api.Auth 三型／gate2 seed 對 runtime-append 三表表級收窄／Lint18 認得 erratum 更正事件、紅訊息出口自此可執行。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
