---
id: "0071"
title: 測試 helper `metric_value` 多份同形判為 won't-fix——各檔各持一份係取捨、不收攏至 `model::test_db`；份數不入名冊、以枚舉指令為準
date: 2026-08-30
status: accepted
supersedes: []
superseded_by: []
provenance: "B-124①（B-110 oneshot 收攏的續集、維護批 A U2 查定 2026-08-25 立案；原②「`handler/role.rs` 一處手搭 inline oneshot」已於 2026-08-25 帳面更正出列、殘餘射程只剩①）；user 親決 2026-08-30「B-124① 併入本批、立 won't-fix ADR」（零碼改動）；正典 doc＝`rust-api/server/src/handler/menu.rs` endpoint_tests 之 `fn metric_value` rustdoc（本 ADR 為其拍板承載）"
tags: [tests, wont-fix, test-helper, backlog-disposition]
---

## 背景

`fn metric_value(render: &str, series: &str) -> f64`——自 metrics render 文本取指定 series 的值
（找不到＝0）——是一支**單一方法鏈純函式**（`lines → find(starts_with) → rsplit → parse → unwrap_or`），
住在多個檔案各自私有的測試模組裡、彼此看不見。

B-124 是 B-110 的續集：B-110 把同批的 oneshot 打端殼收進 `model::test_db`
（`#[cfg(test)] pub(crate)`），證明**跨檔 test helper 完全取用得到**——「各住私有模組看不見」自此
不再是不收的理由。維護批 A U2（2026-08-25）據此立 B-124，射程兩項：①`metric_value` 多份同形之取捨
②`handler/role.rs` 一處手搭 inline oneshot。②於同日帳面更正出列（該檔早已走 `test_db::oneshot_json`），
殘餘只剩①。

**立案當日快照**（2026-08-30 實跑 `grep -rn "^\s*fn metric_value" --include=*.rs rust-api/server/`）
＝**7 份**：`auth/enforce.rs`／`handler/menu.rs`／`handler/role.rs`／`handler/policy_archive.rs`／
`handler/user.rs`／`model/facade/sys_menu.rs`／`model/facade/sys_role.rs`。★B-124 條文與 menu.rs 正典 doc
皆寫「六份」——`handler/user.rs` 那份是 007-user-password-admin 新增、帳面未跟。這恰是正典 doc 自己
預言的形：份數是跨檔的**衍生事實**，漏同步既不編譯紅也不測試紅 ⇒ 必然腐。**本 ADR 只記立案當日快照，
份數的權威永遠是那句枚舉指令**（行首錨定 `^\s*` 非贅字：正典 doc 自身含該字面舉例一行）。

**決策與帳面不一致**：正典 doc 逐字寫「此處不收係**取捨**：單一方法鏈純函式、零共用狀態、無跨檔
同步面，收攏收益不抵一次跨檔耦合」——這已經是一個 by-design 決定；但 BACKLOG 仍讓 B-124 佔著待辦位
（「日後若改判要收，落點＝`model::test_db`」），而正典 doc 末句「另掛 B-124、不在本刀射程」是**待辦式
引用**——刪列即斷鏈（L-072 之形）。一個已決事項掛成待辦，讓讀 BACKLOG 的人以為還有一件事要做、
讀 doc 的人以為已決，兩人都不會發現對方的存在。本 ADR 把這個決定從 rustdoc 提升為拍板記錄，並關帳。

## 決定

1. **維持各檔各持一份**——won't-fix／by-design。**不收攏**至 `model::test_db`，不建共用 helper。
2. **刻意不記份數與逐檔名冊**（形沿 `model/mod.rs` `REDIS_TTL_SLACK_SECS` 那條 doc）：要枚舉現況
   一律 `grep -rn "^\s*fn metric_value" --include=*.rs server/`，那是唯一不會過期的答案。
3. **正典＝`handler/menu.rs` endpoint_tests 該段 rustdoc 的收攏取捨句**（「此處不收係**取捨**」
   那幾行）；本 ADR 是它的拍板承載，兩處互相指路。★**正典射程僅及收攏取捨**——同段 rustdoc 內
   其餘同族句（例如 `self_heal` 可取用性的那一句）**不在本 ADR 的裁決面**、本 ADR 不為其背書；
   本 ADR 一概不記跨檔的現況考證（理由 4：那是會腐的衍生事實，不該寫進不可變記錄）。
   其他各份的引用形（如 `handler/user.rs`「形沿 handler/role.rs 同名 helper——各檔各持一份係取捨、
   非『收不了』」）維持不動。
4. **零碼行為改動**：本裁決唯一的碼面動作＝正典 doc 末句由「另掛 B-124」改指本 ADR。

## 理由

1. **收攏的收益面極薄。** 單一方法鏈純函式、零共用狀態、無跨檔同步面——**改一處不逼別處跟**。
   多份同形的真正成本是「改一處必須跟著改別處、而漏改會壞」；這支 helper 沒有那個成本：各份是
   獨立的、各自對著自己模組的測試，沒有一個不變式跨在它們之間。
2. **收攏的代價面是實的。** 收攏＝新增一個跨檔耦合點＋`model::test_db` 的可見面再擴一格。L-069 的
   直接形（函式體內有被 token 掃描閘守著的呼叫、放寬可見性即打穿閘的射程）在這支 helper 上**不成立**
   ——它體內沒有任何被守的呼叫；引 L-069 的是它的一般化：**可見面每放寬一次，都得回頭問一次既有
   機器閘還在守什麼**。`test_db` 是本 repo 的共用 test helper 家，裡面每多一支 `pub(crate)`、就多一條
   消費者借道的入口；把一支零收益的 helper 也放進去，是替「家越大越好」立先例，而每一次擴家日後
   都要付那一問。收攏的成本因此不是一次性的。
3. **「看不見」不是理由，「不值得」才是。** B-110 已反證「收不了」；本裁決採的判準是**價值**
   ——收得了與該不該收是兩個問題，前者只證明選項存在。
4. **名冊必腐，已兩度實證。** `REDIS_TTL_SLACK_SECS` 那條為「記次數」付過兩次代價；本次立案時
   「六份」對「七份」的失真，是第三次——而且發生在**正典 doc 自己已經寫明不記名冊**的同一段裡：
   B-124 條文抄了**名冊**、正典 doc 抄了**份數**，**兩份都腐了**（本刀的 rust diff 正是把 doc
   那句「本 helper **六份**的收攏本身」改成「**多份**」）。★教訓不是「不列檔名就安全」——**份數
   一樣是跨檔衍生事實**，這正是決定 §2 把份數與名冊**一併**排除的理由。

## 替代案

**A. 立即收攏至 `model::test_db`（`#[cfg(test)] pub(crate)`）。** 未採，理由 1／2。★**它不是壞選項**
——它可行（B-110 已證）、落點明確，翻案時的落點就是它；只是**現在**收攏付的是實代價、換的是零收益。

**B. 記份數名冊**（BACKLOG 條文或 doc 內逐檔列出）。未採：衍生事實、漏同步既不編譯紅也不測試紅
（理由 4）；本次立案即實證。枚舉指令是不會過期的名冊。

**C. 維持 BACKLOG 佔位、不表態。** 未採：已決事項掛成待辦＝決策與帳面不一致（背景末段）。矛盾不會
自己消失，只會在某次「這個要不要收」的重複討論裡再浪費一輪。

## 後果

- B-124 關帳、自 BACKLOG 刪列；`handler/menu.rs` 正典 doc 末句改指本 ADR；NOTES 在案候選清單去掉
  B-124。**零碼行為改動**（rust diff 只含 `///` 行）。
- ★**誠實記——已知代價**：日後若 series 解析規則變（例如 label 順序、escape 規則、由行首前綴匹配
  改為精確匹配），須**逐份**修改且**無編譯紅／測試紅提醒**；某份漏改的失效形不是紅、而是該檔測試
  在新規則下靜默取到 `0.0`（找不到＝0 的預設值），得靠斷言本身的鑑別力才會浮現。這是接受的面；
  緩解＝枚舉指令一次列全、逐份改。
- ★**翻案觸發器（明確、可檢驗）**——命中任一即立新 ADR `supersedes: ["0071"]`：
  1. 任一次修改 `metric_value` 的**行為**必須同步多份 ⇒「改一處不逼別處跟」不再成立（判準：
     一次 commit 動到枚舉指令命中的兩份以上、且改動同源）。
  2. helper 需要**共用狀態**（例如快取 render 的解析結果、共用 series 常數表），或各份出現
     **行為分岔**（枚舉指令命中的各份函式體不再逐字同形——那時「多份同形」這個前提本身已消失，
     該收的是分岔、不是份數）。
  3. 下一把動 `metric_value` 面的刀**願意承擔收攏成本**、且該刀本來就要動 `test_db`。
  屆時落點＝`model::test_db`（`#[cfg(test)] pub(crate)`），並**同批補消費者名冊閘**（L-069 之形：
  家檔＝定義處、名冊＝跨檔消費者、名冊 doc 寫明擴列要對照什麼），兩處 doc 互相指路。
- ★**留給後人的判準**：多份同形要不要收，先問「**改一處是否逼別處跟**」，不是問「看不看得見」。
  看得見只證明收得了；逼別處跟才證明該收。
