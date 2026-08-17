---
promoted_to: docs/arc42/decisions/0034-contract-stub-connect-lazy.md 後果段（斷言強度分級紀律）
---
- **L-025**｜**「免 DB 契約測」的免 DB 前提對 Public route 結構性破裂——blanket 信封斷言
  一寫 `0000`／空集就是在斷言一個測不到的東西**：contract.rs 的 stub app 用 connect_lazy
  假連線，Authed／Policy route 在 authn 層 early-return 8888、真的免 DB；但 Public route
  （getConstantRoutes 等）沒有 authn 擋路、oneshot 直進 handler、查詢在假連線上落 `DbErr`
  →回 5000——**不是空集也不是 0000**。若對全 route 一體寫「碼須 0000」的 blanket 斷言，
  Public 案必紅；反射性把它改成「碼屬可發集」全體套用，又把 Authed 案的判別力
  （早退形可逐值斷言 8888）一起稀釋掉。防法（ADR 0034 後果段已固化）：①契約案的斷言強度
  **依「該 route 在 stub 下走到哪一層」分級**——免 DB 的確定形（authn early-return、body
  rejection）逐值斷言，會觸 DB 的只斷言三欄信封＋碼屬 13 碼矩陣可發集；②寫新 contract 案
  先問「這條 route 在 stub app 下第一個 DB 觸點在哪」，不要從隔壁案照抄斷言；③blanket
  斷言要收緊前提：它隱含「全部案走同一條路徑到同一層」，Public／Authed 混掃時該前提天然
  不成立。
