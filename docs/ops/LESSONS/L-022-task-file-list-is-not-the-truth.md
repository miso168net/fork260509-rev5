---
promoted_to: 未盤點（2026-08-17 分檔遷移前存量；盤點工項＝B-091 承載）
---
- **L-022**｜**派工單（tasks.md）的「涉檔列」不是授權邊界的真相——要對照「這個 task 需要的
  東西存在嗎」自己補**：003-auth-session 已兩度被同一形咬到。①U-J：`handler/auth/mod.rs`
  不在 U-J 涉檔列，但不補 `pub mod refresh;` 該檔就編譯不進 crate 且**無任何錯誤訊息指向此事**
  （U-K 列有它、只有 U-J 那列漏）。②U-M：T063 寫「import stub wrapper」，而全 tasks.md
  **沒有任何 task 建那個 wrapper**——rev4 藍本是獨立檔 `rev4-auth-stub.ts`、rev5 歸宿是
  `rev5-auth.ts`，U-K／U-L 兩列都有它、唯獨 U-M 那列漏；且憲法 §III.2 (b) 收窄字面是
  「僅改 import 指向 stub wrapper」⇒ 表單直呼 `request` 即違收窄，**沒有合規繞道**，
  implementer 只能回 blocked。★兩次都是「涉檔列漏一個結構上必需的檔」，而編排的允許檔案清單
  若照抄該列，就把缺口一起抄進去。防法：①開單元前對每個 task 問一句「它 import／呼叫／宣告的
  東西**現在存在嗎**」，不存在就往前追是誰該建——沒有任何 task 建＝派工單缺口；②允許清單以
  「該單元真正需要動的檔」為準、涉檔列只當起點；③撞到就**回頭修 tasks.md**（補涉檔列＋在該
  task 加前置說明），不要只修自己的 script——下一個讀派工單的人會撞同一面牆；④★agent 回
  blocked 時先判「是不是我的清單有缺口」，那正是防呆⑥要保護的東西，不是 agent 無能。
