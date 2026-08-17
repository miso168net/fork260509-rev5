---
promoted_to: tools/schema-gate.py 兩處紀律註（降級腿有論證必有紅綠載體）
---
- **L-019**｜**降級腿測不到，常常不是「忘了測」而是「上游同源故障先攔截」——構造壞 X 時，
  所有讀 X 的上游都會先壞**：U-K 的 `handler/auth/refresh.rs` 之 `reject_idle` 對
  `set_nx_ex` 的 `Err`（redis 故障）腿有完整論證與 `degraded` 訊號，卻零測試覆蓋。追因後
  發現不是疏漏：唯一的壞 redis 構造 `test_db::bad_cache()` 會讓**上游**的
  `last_activity_get`（同一條壞連線）先撞 `Err` → 走 fail-open 續跑 rotate，執行流永遠進不了
  `reject_idle` ⇒ 該腿**結構上不可達**。同形風險在後續單元只會更多（U-L 的節流三區、captcha
  標記各有數條 redis／PG 降級腿，且彼此共用同一條連線）。★危害：這類腿改壞了全樹零紅——把
  `Err(_) => false`（跳過落列）改成 `=> true`（「問不到就當第一次、寧可記下來」是很自然的
  直覺），redis 半斷線期間每一枚逾時會話的每次換發都會再插一列 `session_event(idle)`，前端
  refresh-loop 週期性重試 ⇒ append-only 稽核表被同一個 sid 灌爆，而該表無刪除路徑。
  防法：①判準——若某降級腿「經 HTTP 面構造不出來」，先問「是不是上游有同源故障先攔截」，
  是就**直呼私有 fn** 取得覆蓋（`integration_tests` 是模組子模組、`super::` 可達；先例＝
  `super::clamp_source_ip`／`super::is_unique_violation`）；②寫降級腿的論證註解時同步問
  「這條腿有測試嗎、走得到嗎」——有論證無覆蓋＝下一個人有充分理由把它「簡化」掉；
  ③補完守門一律做**變異測試**（本例：`Err(_) => true` 使新測紅 rc=101、還原後 rc=0），
  否則補的是另一個裝飾性守門（ADR 0024）。
