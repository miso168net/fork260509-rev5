<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=b827063｜rust-api=e02251d

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：72（accepted 70、superseded 2）
- BACKLOG 待辦：32（next：B-155）｜滯後：8
- LESSONS：74 筆（next：L-075）
- events：82 筆（feature_close 7、misc 42、perf 33）

## 最近事件（尾 3 筆、新在前）
- 2026-08-31｜misc｜rust 維護批 R1（輕量軌）：B-138 ilike_contains 三份收攏為 model/facade/mod.rs 單一 pub(crate) 共用件（sys_role／sys_user 刪同簽章私有份、sys_ip_rule 窄化變體改傳 CIDR_TEXT_EXPR 首參；三支行為測原地保留）＋B-137 R_SUPER 宣告源三收二（sys_user 側宣告刪除、handler 兩處與釘值測改引 sys_role::SUPER_ROLE_CODE，auth 側直書保留＝by-design ADR 0072；三支釘值測全保留）；容器內全量 serial 測試前後皆 998 綠
- 2026-08-31｜misc｜外層維護批收單（merge 59db57e）：U1＝B-150 Lint19 佔位續值＋B-151 Lint29 加 rust-api *.toml＋B-030(a) zh-cn 鍵集腿；U2＝B-091 關帳 11 條佔位盤完＋RUNBOOK §9 複驗走重推＋§16.4 retention 列；U3＝B-144 關帳（base-web pin 前進）；U4＝B-030(b) 五面 parity＋B-023 半件 drill（真跑相等）＋§6 縮編；B-120／B-078 改述、L-073／L-074 立帳、B-152～B-154 開立；fhr 13 筆處置畢
- 2026-08-31｜misc｜外層維護批 U4：B-030 子項「機密清單 parity 檢查」出列＝deploy/decrypt-secrets.py 自測層五面 parity 斷言上線（generate 13／preflight 13／compose 12／enc 10／EXPECTED_KEYS 10、差額具名常數、各面仍各寫一份）＋B-023 半件＝deploy/backup-db.py 新增 drill 子命令（非破壞 scratch 演練、只刪 drill 名、真跑逐位元相等）＋RUNBOOK §6 縮編（§6.2 一行命令、新增 §6.5）；B-023 餘排程化、B-030 餘四子項、皆未關帳

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-30 12.24s、2026-08-31 10.94s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
