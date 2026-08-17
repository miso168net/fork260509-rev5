---
promoted_to: 未盤點（2026-08-17 分檔遷移前存量；盤點工項＝B-091 承載）
---
- **L-021**｜**非零 exit code 也要看「是誰回的」——`rc=1`（工具拒絕執行）與 `rc=101`
  （測試真的失敗）意義相反**：U-L 邊界做 flake 檢查時寫成
  `cargo test -p server --lib throttle:: captcha::`，20 輪全部 rc=1，讀起來像「20/20 全紅的
  災難」；實際上 `cargo test` 只吃**一個** TESTNAME 位置參數，第二個直接被 clap 拒絕
  （`error: unexpected argument 'captcha::' found`），**一支測試都沒跑**。識破的線索是同一刻
  全量 `cargo test --workspace` 才剛 rc=0，且 rust 測試失敗的慣例碼是 **101** 而非 1。
  ★這是 L-015「一律看 exit code」的必要補充：看 rc 是對的，但 rc 只說「失敗了」，不說
  「失敗在哪一層」——把工具用法錯誤讀成測試回歸，會讓人去追一個不存在的 bug；反過來把
  rc=101 讀成環境問題則會放掉真回歸。防法：①非零時**先看第一行輸出**再下結論，`error:` 開頭
  ＝工具層、`test ... FAILED`／`panicked at` ＝測試層；②迴圈跑測試時把首行錯誤一併印出來
  （只印 rc 會丟掉這個位元）；③多模組要一起跑就一輪多次呼叫，或直接跑 `--lib` 全組——
  別把兩個 filter 塞進同一次呼叫。
