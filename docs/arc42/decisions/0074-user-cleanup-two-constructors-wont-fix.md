---
id: "0074"
title: 測試守衛 `test_db::UserCleanup` 兩建構子並存判為 won't-fix——`new`＝顯式 id 單名冊、`with_name_prefixes`＝雙名冊係刻意終態、不收成單一建構子
date: 2026-08-31
status: accepted
supersedes: []
superseded_by: []
provenance: "B-135（007-user-password-admin T021 補業務鍵前綴腿時留下過渡形自陳、`facade/sys_role.rs`／`handler/policy_archive.rs` 在該單元允許檔清單外故未當場統一；2026-08-28 落帳〔外層 commit 0803e10、api pin 7575379〕）；user 親決 2026-08-30「wont-fix、併入 rust 維護批、立 ADR」；正典 doc＝`rust-api/server/src/model/mod.rs` `test_db::UserCleanup` 型 doc 末條（本 ADR 為其拍板承載）"
tags: [tests, wont-fix, test-helper, backlog-disposition]
---

## 背景

`test_db::UserCleanup`（user 測試清理守衛）有兩個建構子：`new(ids)`＝顯式大 id 單名冊，
係 `with_name_prefixes` 的單行薄殼；`with_name_prefixes(ids, name_prefixes)`＝顯式 id＋
`user_name` 前綴雙名冊（007-user-password-admin T021 為業務鍵腿新增——真寫端走 `nextval`、
id 事前不可知，等值清理鍵圈不住，故收前綴）。當時型 doc 與 B-135 條文皆自陳**過渡形**：
終態應照同檔 `RoleCleanup`／`MenuCleanup` 收成單一雙名冊建構子，統一時機＝下一把動得到
`facade/sys_role.rs`／`handler/policy_archive.rs` 的刀，並記「既有 12 個呼叫點」。

**拍板日快照**（2026-08-31 實跑 `git -C rust-api grep -c`）：`UserCleanup::new(` 命中
**81 行**、`UserCleanup::with_name_prefixes(` 命中 **10 行**——各含型 doc「用法」舉例 1 行、
非呼叫點，**真呼叫點＝89 處**；含 `UserCleanup::` 字面之檔共 **14 檔**（`git grep -l`）——
距條目落帳（2026-08-28、外層 commit 0803e10：當日 pin 實測 `new(` 14 行／
`with_name_prefixes(` 3 行／7 檔）帳面「12 個呼叫點」已膨脹約 7 倍，且膨脹全數發生在
落帳後的同一刀內（007 之 U2～U10；2026-08-30 feature_close pin 已達與拍板日相同之
81／10／14）：後續單元（user 管理面端點測等）大量沿用 `new(ids)` 起手形，正是「名冊必腐」
（ADR 0071 理由 4）在呼叫點數上的再次實證。★本 ADR 只記快照，數量的權威永遠是正典 doc
那句枚舉 grep（`[(]` 錨定形把無括號散文提及排除在帳外、命中帳同上）。

★B-135 條文自帶的統一時機（「下一把動得到 `facade/sys_role.rs`／`handler/policy_archive.rs`
的刀」）已於本維護批 R1（rust-api commit e02251d 實動 `facade/sys_role.rs`）**兌現**，
判不順帶做並**退役**該觸發器（形制同 BACKLOG B-125 之「觸發器兌現但判不順帶做＋觸發器
改述」）：立案時射程僅 2 檔、命中＝罕見訊號；現呼叫點已散 14 檔、幾乎每把 rust 刀都會
命中，該觸發器已無鑑別力——成本天平的真正接手者＝後果段翻案觸發器 4。

## 決定

1. **兩建構子並存判為刻意終態**——won't-fix。不把 `new` 併進 `with_name_prefixes`、
   不做 89 處呼叫點的機械改寫、不對齊 `RoleCleanup`／`MenuCleanup` 的單建構子形。
2. **分工屬慣例、非能力邊界**：`new(ids)`＝只圈事前已知合成大 id 的測試；
   `with_name_prefixes(ids, name_prefixes)`＝另需收「id 事前不可知的真寫端」殘列的測試。
   `new` 係後者「前綴名冊＝空集」的單行薄殼退化形——行為 100% 被涵蓋、僅**呼叫端形**
   不重疊，兩支各自有消費面；保留 `new` 換到的是大宗呼叫點免寫 `&[]` 樣板，
   薄殼保證行為單源。
3. **正典 doc＝型 doc 末條**（本 ADR 落地時同步訂正為 as-built）：挑用哪一支由該處
   一句話承擔；呼叫點數不記死值、以枚舉 grep 現算為準。
4. **零碼行為改動**：本裁決唯一碼面動作＝型 doc「過渡形／統一時機」敘述改指本 ADR
   （rust diff 只含 `///` 行）。

## 理由

1. **成本已非立案時的成本。** 立案帳面 12 處；現算 89 處散 14 檔，統一簽名＝89 處呼叫點
   機械改寫（多為測試起手行；型 doc 兩行舉例同須跟改、共 91 行）、呼叫點面約 ×7
   （12→89）、觸檔面 ×2（7→14），且動到多個守門測所在檔。
2. **收益只有名冊形一致。** B-135 條文自承：危害＝低、兩支語意不重疊、無假綠面；89 處改寫
   換到的只有「與 `RoleCleanup`／`MenuCleanup` 同形」的觀感一致性——推測性工作、不做。
3. **薄殼不是債。** `new` 是 `with_name_prefixes` 的單行薄殼、行為單源：改任一條清理腿
   只動一處、不逼 80 個 `new` 呼叫點跟。「改一處不逼別處跟」（ADR 0071 留給後人的判準）
   在此不成立為收攏理由——並存的成本只剩「新測要分辨用哪一支」，那由型 doc 一句話承擔。

## 後果

- B-135 關帳、自 BACKLOG 刪列；型 doc 過渡形敘述刪除、改指本 ADR；呼叫點數自此不記死值。
- ★**誠實記——已知代價**：日後新增 user 相關測試要先分辨該用哪一支；緩解＝型 doc 末條
  挑法一句話（會生出 id 事前不可知的業務列＝掛 `with_name_prefixes` 收前綴腿；
  只圈顯式大 id＝掛 `new`）。
- ★**翻案觸發器**（命中任一即立新 ADR `supersedes: ["0074"]`）：
  1. 呼叫點數量級下降至可一次掃完統一（判準：枚舉 grep 命中降回立案帳面的量級、
     一顆 commit 改得完）；
  2. 第三個建構子出現——並存形開始發散，該收的是發散、不是份數；
  3. `RoleCleanup`／`MenuCleanup` 的雙名冊形制本身改版——屆時 `UserCleanup` 同批對齊；
  4. 下一把**因其他理由本來就要重寫這批測試起手行**的刀（判準：一顆 commit 已動到枚舉
     grep 命中的**過半檔案**）——屆時統一簽名的邊際成本趨近零、理由 1 的成本前提即不
     成立，該刀願意承擔者同批收攏（承 ADR 0071 觸發器 3 之形）。
