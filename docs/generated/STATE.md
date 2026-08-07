<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0fee6c0｜rust-api=080eefb

## constitution
- 版本：1.1.0

## 帳面統計
- ADR：17（accepted 17）
- BACKLOG 待辦：31（next：B-042）｜滯後：1
- LESSONS：8 筆（next：L-009）
- events：15 筆（feature_close 1、misc 14）

## 最近事件（尾 3 筆、新在前）
- 2026-08-07｜misc｜B12 前拍板批四題收單（ADR 0014～0017）：B-031 prod 不入 rev5 roadmap（各刀留 seam；region 欄 UI 先不做；輪替維持觸發式；多副本假設不成立）；B-032 前提未成立原樣過境（多人成立但第二位持鑰人＝工程師）＋衍生 B-040（§15.5 補成員離開列）/B-041（第三把離線復原鑰）；B-012 前綴通配＋具名豁免（施工併維護批 schema-gate 群）；B-015 Lint06 基準改 merge^1:BOOK（施工併 docs-sync 群）
- 2026-08-07｜misc｜B-039 pre-push 防線測試矩陣收單（輕量軌 maint-b039、merge 08361f5）：docs-sync 新增 TestPrePushMatrix（455→463 測）——合成 stdin 四情境×betterleaks rc 三值（實查 0 乾淨／2 命中／其餘工具錯誤）12 格×兩支 pre-push 真檔文乾跑＋九補案；三處怪行為釘為改寫基準（空字串 oid 當全零／末行缺尾換行不掃／force push 不區分）；突變兩組紅（直譯反向＋fail-open 化）；未揭露防線真缺陷
- 2026-08-07｜misc｜B-038 age 產鑰容器化收單（輕量軌 maint-b038、merge ab31065；ADR 0011 ③類首例）：Dockerfile.age 多階段（golang @latest builder＋alpine、零版本字面）＋generate-age-key.sh 重寫——下載膠水／digest 現查／雙平台 case／行內 python 全蒸發、每次 build --pull --no-cache、離線退回帶警示、pty 併流正規化；docs-sync AGE_VERSION 釘版斷言拆除；端到端全機器化（殼鑰→解回→重推公鑰相等＋sops 實吃 armored identity）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
