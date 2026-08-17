---
promoted_to: rust-api/server/tests/common/mod.rs（stub 連線 rustdoc＋釘 backend＝Postgres 防倒退回 Disconnected 測）
---
- **L-013**｜`DatabaseConnection::Disconnected` **不是**「一切操作都回 Err」的統一失敗態：
  sea-orm 1.1.20 的 `src/database/db_connection.rs` 對該 variant 共九處分派，八處回
  `Err(conn_err("Disconnected"))`（`execute`／`query_one`／`query_all`／交易等），
  **唯一例外**是 `get_database_backend()`——它 `panic!("Disconnected")`。根因＝該方法回傳
  `DbBackend` 而非 `Result<DbBackend, DbErr>`，**型別上沒有錯誤通道可走**。後果：高階查詢
  API（`Select::all` 等）組 SQL 前必須先取 backend 決定方言，於是**先撞 panic、根本走不到
  DbErr 路徑**——想用 `Disconnected` 當「查庫必失敗」的測試替身，拿到的是 panic 而不是預期的
  5000 信封。rev5 現況（002-system-settings U8b 盤點）：以 `Disconnected` 充免 DB stub 的三處
  （`tests/common` 之 `stub_state`、`router.rs` 的 `mod tests`、`enforce.rs` 測試）都只依賴
  「不觸庫」而非「觸庫得 Err」，故無影響。防法：(a) 需要「查庫必失敗」的替身時**自寫
  `ConnectionTrait` impl**（U8b 的 `FailingConn`：一切查詢回合成 `DbErr`），不要借
  `Disconnected`；(b) 借 `Disconnected` 當 stub 時碼內註明「僅保證**不觸庫**、不保證**觸庫
  得 Err**」——那是兩件事；(c) ★可推廣：判斷一個「失敗態替身」能不能用，要看**被測路徑實際
  會呼叫哪些方法**，不能只看該型別的整體語意；★回傳型別沒有錯誤通道的方法（回 `T` 而非
  `Result<T, E>`）就是 panic 的候選點——掃一遍那些方法即可預判替身會不會炸。
