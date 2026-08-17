<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=bfeb783｜rust-api=bc8d7f3

## constitution
- 版本：1.6.2

## 帳面統計
- ADR：45（accepted 43、superseded 2）
- BACKLOG 待辦：40（next：B-093）｜滯後：1
- LESSONS：47 筆（next：L-048）
- events：28 筆（feature_close 4、misc 24）

## 最近事件（尾 3 筆、新在前）
- 2026-08-17｜misc｜B-090 LESSONS 分檔制遷移收單（輕量軌 maint-b090、merge ae5c24d）：分卷制→分檔制——47 條 byte-diff 逐位遷入 docs/ops/LESSONS/、主檔改寫手寫索引（47 行逐條精寫 hook）、晉升必答欄 promoted_to 落值（實值 35／佔位 12→B-091 承載）、刪 LESSONS-001-028.md；工具面（U1 commit 8b0cd9e）＝Lint26 分檔對賬＋Lint07 單條上限＋Lint09 head 視野聯集＋ADR 0045、docs-sync 自測 496→517；衍生 B-092
- 2026-08-17｜misc｜Lint26 LESSONS 分檔對賬閘上線（ADR 0045、B-090 U1 工具面）：檔名↔正文 ID／索引↔檔雙向／promoted_to 必填三斷言＋Lint07 條目檔單條上限（WARN 2000／ERROR 3000）＋Lint09 L 側 head 視野聯集（主檔恆 index 0；堵「整卷刪除＝號碼靜默退出反回收視野」）；名冊三檔範圍字串同 commit bump 至 Lint03～Lint26；本筆即新名冊承載事件
- 2026-08-17｜feature_close｜004-ip-trust-anchor｜IP 信任錨縱切（本代第四刀、B-019 關帳）：真實來源還原八態／IP 存取閘（結構豁免、防自鎖、門鈴熱重載）／IP 規則管理頁與五支端點（含回收桶、sys_operation_log 首個寫入者）／來源維節流（節流自此雙維度）／管理員解鎖端點。ROUTES 16→22 終態、rust 測試 321→512、憲法 1.3.1→1.6.2（島 F 入憲＝第六座行為島＋§III.2 第五條 ★ 軌道）。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
