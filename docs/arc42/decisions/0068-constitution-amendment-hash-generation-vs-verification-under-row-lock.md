---
id: "0068"
title: 憲法 Amendment 1.9.1——§I.7 島 I5 末句澄清：受「持有列鎖期間不得計算」約束者為雜湊之**生成**（hash），**驗證**（verify）作為守門判定依島 I1 於鎖內執行
date: 2026-08-29
status: accepted
supersedes: []
superseded_by: []
provenance: "007-user-password-admin 之 U4（User Story 3 密碼政策與自助改密後端、tasks.md T045／T047）；發現鏈＝該執行單元規格符合性審查第 1 輪 findings①（雜湊落在列鎖內違反島 I5 末句）→ 同輪 fix 將 hash 生成外移至 handler 取鎖前（新增 `password::NewPassword`）→ 該 fix 升級主線之拍板級項（argon2 verify 仍在鎖內、與島 I1 正面相碰）；拍板＝user 親決 2026-08-29（三選項：改條文／立例外 ADR／verify 外移回 rev4 形；選改條文，理由＝承襲條文字面不夠精確而非真衝突）；條文藍本＝rev4 憲法 §I.7 島 I5 末句原文（rev4:ADR 0054 密碼政策）"
tags: [constitution, governance, behavior-island, password, locking]
---

## 背景

007-user-password-admin 的 U4 落地自助改密（`sys_user::change_own_password`）時，
規格符合性審查指出：兩支密碼寫端在**持有 per-user advisory 鎖＋標的列 `FOR UPDATE`**
期間計算 argon2 雜湊，違反憲法 §I.7 島 I5 末句「密碼雜湊 MUST NOT 於持有列鎖期間計算」。

該筆成立，同輪已修：新增 `password::NewPassword`（明文與 PHC 的成對載體、唯一構造路徑
`prepare()`、刻意零 `Debug` impl），兩支寫端改由 handler 於**開交易前**算好再傳入；
facade 本體自此零 argon2 生成，並補源碼掃描守
`password_hash_never_computed_inside_row_lock` 與三發變異紅證。

**但修到第④格就停住了。** 自助改密五步序的第④格是「舊密碼正確」——
`password::verify(&input.old_password, &user.password)`。argon2 verify 同樣是雜湊運算
（其實作以相同參數重算一次再比對），字面上同受島 I5 末句約束；而它**無法外移**：

- 它的比對基準就是**鎖內那一列**的 PHC。要在鎖外驗，就得先讀一次 PHC、驗完再進鎖比對
  「PHC 字串是否仍是同一份」——那正是 rev4 的「鎖外預讀＋鎖內 PHC 重比」形，
  而 `research.md` R2 差異點清單已明文拍板要消掉它。
- 更根本地，它是**守門判定**，而島 I1 寫著「一切守門判定 MUST 鎖內重驗
  （lock-then-redecide、**永不信 pre-read**）」。

於是同一部憲法的兩條島條文在這一行上互相禁止對方：I5 末句說不准在鎖內算，
I1 說守門判定不准在鎖外算。

## 決定

**判定這不是真衝突，而是島 I5 末句承襲 rev4 時字面不夠精確**——修條文，不立例外。

末句所在的段落前三句全部在講「不洩漏」（DTO 除錯輸出遮蔽／稽核 payload 不含／API 回應
不含），第四句「不得於持有列鎖期間計算」講的其實是**另一回事**：鎖窗管理——argon2 刻意
設計得慢，在持鎖期間跑會把序列化域的持有時間拉長。這個關切只對**雜湊生成**成立
（建帳、管理端重設、自助改密的新密碼，皆可在取鎖前算好），對**驗證**不成立
（基準值在鎖內、且它本身就是島 I1 要求鎖內重驗的守門判定）。

條文改法（§I.7 島 I5 末句）：

- 現行：「密碼雜湊 MUST NOT 於持有列鎖期間計算。」
- 改後：「密碼雜湊之**生成**（hash）MUST NOT 於持有列鎖期間計算（三入口一律於取鎖前算好
  再進鎖）；雜湊**驗證**（verify）作為守門判定，依島 I1 於鎖內重驗執行。」

版本 **1.9.0 → 1.9.1**（PATCH／澄清）：不新增禁令、不放寬既有禁令的射程、
不改變任何 as-built 行為，只把一句話裡被混為一談的兩件事分開講。
島 I5 的 ★方向反轉條款（拆單一驗證點／拔遮蔽／把政策掛上登入路徑）不受本次影響。

**碼零改動**：as-built 已符合改後條文——hash 生成在 handler 取鎖前（U4 已修、有源碼掃描守
與變異紅證），verify 在鎖內第④格（本 ADR 追認）。

## 替代案

**A. 憲法不動，另立具名例外 ADR。** 保留末句的絕對形，另記「argon2 verify 於自助改密鎖內
執行」為具名例外。代價：憲法條文自此與 as-built 字面不符，日後讀條文的人看到的是無例外的
MUST NOT，要靠交叉引用才知道有例外；且例外一旦開始累積，條文的可讀性會逐份下降。
**未採**——本案的問題出在條文本身寫得比意圖寬，修條文比在條文外面掛補丁誠實。

**B. verify 外移到鎖外，鎖內只重比 PHC 字串。** 讓 as-built 完全服從末句字面。代價有三：
①這正是 rev4 的形，而 research R2 已明文拍板消掉它②多一次鎖外預讀，島 I1「永不信 pre-read」
的精神被稀釋③五步序第④格要拆成兩半（鎖外驗、鎖內確認），拒因序的推理變複雜。
**未採**——為了服從一句寫得不夠準的話，付出推翻既有拍板與加重推理負擔的代價。

## 後果

- 憲法 §I.7 島 I5 末句自本版起區分 hash 與 verify；`change_own_password` 第④格的鎖內 verify
  自此有明文依據，不再是「與條文字面相抵但沒人提」的狀態。
- 既有機器守不受影響：`password_hash_never_computed_inside_row_lock` 掃的是**生成**呼叫點
  （`password::hash(` 與 `NewPassword::prepare(`），與改後條文的射程恰好對齊。
- ★**留給後人的判準**：日後若有第三種雜湊運算進場（例如 rehash-on-login、或 PHC 參數升級的
  就地重算），先問它是「生成」還是「判定」——生成一律鎖外，判定依島 I1 鎖內；兩者都不是的
  （例如純粹的成本量測）不在本條射程。
- 本次未動島 I1 一字：它對 `verify` 的要求（鎖內重驗、永不信 pre-read）本來就是清楚的，
  失準的一直只有 I5 末句。
