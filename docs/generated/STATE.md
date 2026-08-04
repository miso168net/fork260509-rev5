<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=未定（index 無該 gitlink 條目（純外層 repo 或該 submodule 未登記））｜rust-api=未定（index 無該 gitlink 條目（純外層 repo 或該 submodule 未登記））

## constitution
- 版本：1.0.0

## 帳面統計
- ADR：3（accepted 3）
- BACKLOG 待辦：1（next：B-002）｜滯後：0
- LESSONS：0 筆（next：L-002）
- events：1 筆（misc 1）

## 最近事件（尾 3 筆、新在前）
- 2026-08-04｜misc｜rev5 創世（波 -1 文件地基）首批 commit：治理工件直搬（sha256 血緣斷言）＋條款裁改 23 條＋骨架六件＋憲法 v1.0.0（user 親審定版）＋機密管線（sops×age）就位；ADR 0001（創世採用）／0002（白名單反轉延後）／0003（佔位字面白名單）同批 accepted

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
