<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=b827063｜rust-api=e7181f9

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：74（accepted 72、superseded 2）
- BACKLOG 待辦：28（next：B-155）｜滯後：8
- LESSONS：74 筆（next：L-075）
- events：84 筆（feature_close 7、misc 44、perf 33）

## 最近事件（尾 3 筆、新在前）
- 2026-08-31｜misc｜rust 維護批 R3（輕量軌）：B-135 判 wont-fix、立 ADR 0074——test_db::UserCleanup 兩建構子並存改判刻意終態：new＝顯式 id 單名冊＝with_name_prefixes〔雙名冊〕前綴空集之單行薄殼退化形、行為單源、各有消費面；型 doc「過渡形／統一時機」訂正為 as-built 改指該 ADR、呼叫點數不記死值；現算 grep 命中 81＋10 行（含舉例 2 行）＝真呼叫 89 處散 14 檔（條目 2026-08-28 落帳帳面 12、膨脹全發生於 007 後續單元）；零碼行為改動、rust diff 只含 /// 行
- 2026-08-31｜misc｜rust 維護批 R2（輕量軌）：B-140 Identity 補 sid 欄（enforce_mw 注入帶入、自助改密改讀 identity.sid、刪 current_sid 小抄本、生產面 jwt::verify 2→1）＋B-141 四件共用件同住 handler::user＝ADR 0073＋B-107 缺席腿 target／degraded 補 capture 機器守（變異紅證）＋B-043 守門射程 3→20 檔（handler 全模組含 auth/）配目錄對賬測；全量 serial 測試 998→1000 綠
- 2026-08-31｜misc｜rust 維護批 R1（輕量軌）：B-138 ilike_contains 三份收攏為 model/facade/mod.rs 單一 pub(crate) 共用件（sys_role／sys_user 刪同簽章私有份、sys_ip_rule 窄化變體改傳 CIDR_TEXT_EXPR 首參；三支行為測原地保留）＋B-137 R_SUPER 宣告源三收二（sys_user 側宣告刪除、handler 兩處與釘值測改引 sys_role::SUPER_ROLE_CODE，auth 側直書保留＝by-design ADR 0072；三支釘值測全保留）；容器內全量 serial 測試前後皆 998 綠

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-30 12.24s、2026-08-31 10.94s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
