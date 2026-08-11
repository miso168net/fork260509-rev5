---
id: "0034"
title: contract 測 stub 連線改用 connect_lazy 假連線——research R7-1 的 MockDatabase 方案經實證不可行
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 T007；被翻案的拍板＝research R7-1 決定段（研究文件、非 ADR，故 supersedes 留空）；實證來源＝U-C workflow（wf_5e3bf693-4eb）implementer 之 blocked 升級＋主線於容器內對 sea-orm 1.1.20 原始碼的複驗；user 親決 2026-08-09"
tags: [rust-api, testing, sea-orm, contract-test, decision-reversal]
---

## 背景

research R7-1 為了解一個真問題：contract 測的 stub 連線用 `DatabaseConnection::Disconnected`，
而它在 `Select::all` 呼 `get_database_backend()` 時**直接 panic**（不是回 `DbErr`）。002 沒撞到
是因為當時兩條業務 route 皆 Policy、`enforce_mw` 在 authn 層 early-return、handler 永不觸及；
本刀 9 條 Public route 會**真的進 handler**，其中 `/route/getConstantRoutes` 會查 `sys_menu`。

R7-1 的決定是「改用 sea-orm `mock` feature 的
`MockDatabase::new(DbBackend::Postgres).into_connection()`——產出真 `DatabaseConnection`、
查詢回空集不 panic；沿既有 sea-orm 版本、零新外部 crate」。

**該決定經實作證實不可行**，原因在 sea-orm 自己的原始碼裡（`sea-orm-1.1.20/src/database/db_connection.rs:17-20`）：

> `/// flags. This creates a database pool. This will be `Clone` unless the feature`
> `/// flag `mock` is enabled.`
> `#[cfg_attr(not(feature = "mock"), derive(Clone))]`
> `pub enum DatabaseConnection {`

開 `mock` feature ⇒ `DatabaseConnection` **失去 `Clone`**。而 axum 的 `State` 要求
`AppState: Clone`，於是實測紅在 `state.rs` 的 `E0277: the trait bound DatabaseConnection: Clone
is not satisfied`。把 `mock` 放進 `dev-dependencies` 也救不了——cargo 對整個 test 建置圖做
**feature 聯集**，lib 本體一樣被波及。

要保住 MockDatabase 就得把 `AppState.db` 改型為 `Arc<DatabaseConnection>`，漣漪至 `enforce.rs`
（2 處）與 `handler/system_settings.rs`（3 處）的 `&state.db`，並且**整個 crate 從此永久失去
`DatabaseConnection: Clone`**——為測試便利對 production 型別課的永久稅。

## 決定

**改用 `ConnectOptions::connect_lazy(true)` 建的假連線作為 contract 測 stub，不開 `mock` feature。**

```rust
let mut opt = ConnectOptions::new("postgres://127.0.0.1:1/stub");
opt.connect_lazy(true);
let db = Database::connect(opt).await?;   // 立刻回，不 ping
```

機制已於容器內複驗（`sea-orm-1.1.20/src/driver/sqlx_postgres.rs:114-120`）：`connect_lazy` 為真時
走 sqlx 的 `pool_options.connect_lazy_with(sqlx_opts)`，**不 await、不建立實際連線**，直接回
`Ok(DatabaseConnection::SqlxPostgresPoolConnection(...))`。

四項性質，逐條對應原問題：

1. **不再 panic**：連線是 `SqlxPostgresPoolConnection` 變體，`get_database_backend()` 回
   `Postgres`；panic 只在 `Disconnected` 那一臂。
2. **`Clone` 保留**（沒開 `mock`）⇒ `AppState` 不必改型 ⇒ **零漣漪**。
3. **查詢回 `DbErr` 而非 panic**：實際連線在查詢時才嘗試並失敗，handler 走既有錯誤路徑 →
   `5000` 信封（仍是三欄）→ contract 測的通用斷言 `assert_three_field_envelope` 照過。
4. **零 feature 變動、零新外部 crate**——R7-1 原本追求的兩個性質完整保留。

★**URL MUST 不帶 `user:pass@`**：帶帳密段會命中 betterleaks 的 `rev5-dsn-credential-url` 規則、
被子庫 pre-commit 以 `--exit-code 2` 硬擋（U-B 已實暴同型，見該單元 commit）。

## 後果

- **contract 案的斷言面被明確界定為 wire 形制、不含業務內容**：stub 查詢回 `DbErr` 而非空集，
  故 U-G 的 5 個新 Public route contract case **不得斷言 `code == "0000"` 或空集 data**，只能斷言
  三欄信封與 13 碼矩陣成員。這其實回到 contract 測該有的分工——業務行為歸 integration 測
  （T019 等走真 DB），contract 測只驗 wire 契約。R7-1 的「查詢回空集」曾允許前者，本決定收回。
- **`mock` feature 的其他潛在消費者要另尋出路**：B-050（`sys_user_role::roles_of_user` 次段查詢
  的 DbErr 落地無機器守）的條目自書「需 sea-orm 的 mock feature」。本決定不為它開 feature；
  若日後確需，須連同「整個 crate 失去 `DatabaseConnection: Clone`」的代價一併重估，或改以
  `Arc<DatabaseConnection>` 承接。該條目維持在 BACKLOG、不因本 ADR 關帳。
- **R7-1 的問題陳述完全成立、只有解法被推翻**：`Disconnected` 會 panic、9 條 Public route 會真的
  進 handler，這兩件事仍是 T007 的存在理由。research 文件同批修訂為新解法，問題段一字不動。
- 教訓（值得記進 LESSONS）：**「沿既有版本、零新外部 crate」不等於零成本**——feature flag 可以
  改變既有型別的 trait 實作面。評估 feature 時要看的不只是「多拖哪些依賴」，還有「拿掉了什麼」。
  sea-orm 這處把 `Clone` 綁在 `not(mock)` 上，是在 doc 裡寫明的，屬可事前查證而未查證。
