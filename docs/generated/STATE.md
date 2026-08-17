<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=bfeb783｜rust-api=bc8d7f3

## constitution
- 版本：1.6.2

## 帳面統計
- ADR：45（accepted 43、superseded 2）
- BACKLOG 待辦：39（next：B-092）｜滯後：1
- LESSONS：47 筆（next：L-048）
- events：27 筆（feature_close 4、misc 23）

## 最近事件（尾 3 筆、新在前）
- 2026-08-17｜misc｜Lint26 LESSONS 分檔對賬閘上線（ADR 0045、B-090 U1 工具面）：檔名↔正文 ID／索引↔檔雙向／promoted_to 必填三斷言＋Lint07 條目檔單條上限（WARN 2000／ERROR 3000）＋Lint09 L 側 head 視野聯集（主檔恆 index 0；堵「整卷刪除＝號碼靜默退出反回收視野」）；名冊三檔範圍字串同 commit bump 至 Lint03～Lint26；本筆即新名冊承載事件
- 2026-08-17｜feature_close｜004-ip-trust-anchor｜IP 信任錨縱切（本代第四刀、B-019 關帳）：真實來源還原八態／IP 存取閘（結構豁免、防自鎖、門鈴熱重載）／IP 規則管理頁與五支端點（含回收桶、sys_operation_log 首個寫入者）／來源維節流（節流自此雙維度）／管理員解鎖端點。ROUTES 16→22 終態、rust 測試 321→512、憲法 1.3.1→1.6.2（島 F 入憲＝第六座行為島＋§III.2 第五條 ★ 軌道）。
- 2026-08-12｜misc｜輕量軌維護批（帳面缺口七件＋B-022 關帳拍板、零碼改動）：B-047 應關未關補記關帳（ADR 0031 明令走收刀事件、003 收刀漏記，而 405→4040 早已實作＝條目描述之現況全反轉）／四筆失效觸發器重定（B-018／B-020／B-021／B-029 皆掛在已走過的刀上）／兩筆帳面孤兒登記（B-072 渲染端轉義、B-073 管理員解鎖端點）／B-008 與 B-024 殘句修文／CLAUDE.md §2 補 resume 分岔／ADR 0038 替代登入維持誠實 stub、ADR 0039 ip_* 三鍵已知態。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
