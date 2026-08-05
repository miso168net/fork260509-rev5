<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0fee6c0｜rust-api=4bbc989

## constitution
- 版本：1.1.0

## 帳面統計
- ADR：8（accepted 8）
- BACKLOG 待辦：14（next：B-016）｜滯後：0
- LESSONS：3 筆（next：L-004）
- events：3 筆（feature_close 1、misc 2）

## 最近事件（尾 3 筆、新在前）
- 2026-08-06｜feature_close｜001-schema-baseline｜波 0 schema 基線刀收刀：m001（15 表 169 欄＋索引 38 約束 101）＋m002（266 列 seed 完全決定性）＝rev4 終態壓平＋user 定稿制；三閘重建＋Day-1 受管演進帳＋fixtures 先驗後凍；entity 15 檔＋refresh 首跑＋拔項＋真表首算＋drift 實跑；ADR 0005~0008（0008＝DB 身分無世代後綴回滾）；quickstart A–E 全跑 SC-001~006 全達成；final holistic review 零 blocker
- 2026-08-05｜misc｜維護批 ports-2xxxx 收單：host 埠 5xxxx→2xxxx 世代錯開（ADR 0004 翻案啟動書 §4.5.9 拍板值；動機＝macOS ephemeral 範圍佔埠致機率性 bind 失敗、世代區隔降位為約束條件）；compose 兩檔＋RUNBOOK §14＋docs-sync 三處裸 0019 指涉同刀跟正；ports 真表重算 12 埠全 2xxxx；殘留掃描零、postgres+redis 實起實聽驗證
- 2026-08-04｜misc｜rev5 創世（波 -1 文件地基）首批 commit：治理工件直搬（sha256 血緣斷言）＋條款裁改 23 條＋骨架六件＋憲法 v1.0.0（user 親審定版）＋機密管線（sops×age）就位；ADR 0001（創世採用）／0002（白名單反轉延後）／0003（佔位字面白名單）同批 accepted

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
