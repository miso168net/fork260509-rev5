---
promoted_to: rust-api/server/src/trust/mod.rs（判定窗與稽核轉錄強制共用同一切分函式、斷言字面引 L-030）
---
- **L-030**｜**射程／職責一搬動，敘述面沒跟著搬＝靜默失效**——同一形在 004 U-D 一輪內撞到兩次，兩次都不是碼錯而是「碼與描述它的那句話分岔」，且兩次的徵狀都是**編譯綠、測試綠、規格看起來也綠**。

**形一（職責搬走、義務沒跟著搬）**：主線指示把 `ipgate::build_ruleset` 的「未知 `wbip_type` 列 skip＋**告警**」中的告警半邊移出純函式（改以回傳值 `RuleSetBuild::skipped` 交出，讓判定核維持零 I/O 而可全態離線測——這個設計是對的），但**沒有同批把發告警的義務指派給任何下游 task**：T025 全文無「未知類型」字樣、T030 的降級類別集又逐字取自 data-model §5 而該矩陣無此列。於是三份規格產物（tasks T011／data-model §1.1／research R5）都還寫著「告警」，實際上全刀不會有任何一處發出它。★危害具體形：營運面把 `wbip_type` 打成 `block`，該列被靜默忽略、日誌與觀測兩面零訊號，管理者以為規則已生效。★**編譯器幫不上忙**——下游只取 `.rules` 而丟棄 `.skipped` 不會有任何警告。抓到它的是規格審查 agent 拿實作去對「三份產物 × 下游每一個 task」交叉查，不是讀碼。

**形二（守門的射程放寬、docstring 沒跟著放寬）**：`server/tests/entity_access_lint.rs` 的實碼掃 `src/` **全樹**、只排除 `model/facade` 一層（`excluded_dirs()`、主守紅訊息字面「src/ 全樹（facade 除外）」），但它自己的檔頭 docstring 仍逐字寫早期的三處列舉「`src/handler/`＋`src/auth/`＋`src/router.rs`」。★危害方向與直覺相反：docstring **比實碼窄**不會讓守門失效，而是讓**讀 docstring 的人**以為 `src/` 底下新開的目錄（本刀的 `src/ipgate/`／`src/trust/`）不在射程、可以自由寫 `entity::`。我自己就是受害者——照該 docstring 把錯的射程寫進了 agent prompt，若不是審查 agent 去讀實碼比對，那句錯敘述會被原樣寫進 commit message 傳下去。

★**防法**：①**搬動職責時，同一次編輯內把接收方的 task／DoD 也改掉**——「移出 A」與「A 的義務落到 B」是**兩件事**，只做前者等於把義務丟掉；規格產物留著舊字面則會讓帳面看起來還在。②**守門碼的射程敘述與其射程常數必須同批改**，並在該敘述旁寫死「MUST 與 `<常數名>` 同步」（本次已就地補進 `entity_access_lint.rs`）。③agent prompt 裡引用機器守的射程時，**引實碼常數而非 docstring**；引錯的成本是把錯敘述放大成全單元的前提。④review prompt 值得長期烤一條：「規格說要有的東西，去查**哪一個 task 負責產出它**；查不到就是 finding」——形一正是這條抓出來的。

