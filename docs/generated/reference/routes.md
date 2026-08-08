<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/routes — 全量正典表

來源＝rust-api/server/src/router.rs 的 ROUTES const（generate 重算；handler 閉包不入表）。

| path | method | protection | case_key | envelope 例外 |
|---|---|---|---|---|
| /health | GET | Public | health | 是 |
| /metrics | GET | Public | metrics | 是 |
