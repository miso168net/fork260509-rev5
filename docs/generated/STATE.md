<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0fee6c0｜rust-api=080eefb

## constitution
- 版本：1.1.0

## 帳面統計
- ADR：13（accepted 13）
- BACKLOG 待辦：34（next：B-040）｜滯後：1
- LESSONS：7 筆（next：L-008）
- events：11 筆（feature_close 1、misc 10）

## 最近事件（尾 3 筆、新在前）
- 2026-08-07｜misc｜B-036 decrypt「passphrase 只打一次」收單（輕量軌 maint-b036、merge ebd327a）：自動應答 driver（getpass 一次→pty 偵測提示才餵、邊讀邊數不預測）＋RV5_DECRYPT_MANUAL=1 逐次手打退路＋回顯守衛＋SIGINT／逾時收孤兒；安全姿態拍板＝ADR 0013；舊 decrypt-secrets.sh 退役、轉換窗口 SH_TWIN 收攏（到期即紅守衛首次實走）；真密文人工端到端：自動路徑一次輸入＋退路兩次盲打皆 10 支零 .new、preflight rc=0
- 2026-08-07｜misc｜B-035 bash→python 轉換批①收單（輕量軌 maint-b035、merge 2d22fb6）：共用庫 secrets_common 提出＋guard 併軌→preflight 等價重寫＋自測名冊改單一路徑形（TOOLS_PY 路徑形＋SH_TWIN 到期即紅）→decrypt 等價重寫刪非裸量純量斷言（合成密文 15 情境等價、引號形逐位元組還原）→活手冊 .py 正典＋errata 51 處逐筆處置；真密文人工端到端綠（decrypt 10 支零 .new＋preflight rc=0）
- 2026-08-07｜misc｜B-004 前代裸編號全量清償收單（輕量軌 maint-b004）：Lint25 上線→六批 agent 並行清償（A188/B190/C74+假號段80/D21/EF39/G25）→總審 48 筆殘留逐筆歸因全數收斂（判定收斂＋豁免補齊、漏改 0）→docs-sync 自身 136 處兜底→轉逐筆 ERROR；血緣前綴 rev4:/rev3: 逐 token、grafana uid 與七類 mention 具名豁免；批I 子庫 main.rs 前綴化＋pin bump

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
