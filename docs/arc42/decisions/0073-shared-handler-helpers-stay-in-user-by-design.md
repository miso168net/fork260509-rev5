---
id: "0073"
title: 四件跨 handler 共用件同住 `handler::user` 判為 by-design——共用件的家取語意層而非技術可行性，`common` 收攏名冊維持八件、兩支 err 不上提
date: 2026-08-31
status: accepted
supersedes: []
superseded_by: []
provenance: "B-141（007 刀 U4 立案：跨 handler 共用件住 handler::user 與 handler/mod.rs 宣告不一致、殘餘待裁＝兩支 err 上提與否；該刀 U4／U5 已以宣告拆兩截消解不一致、例外實為四件）；user 2026-08-30 拍板併入 rust 維護批 R2、三條各走候選①；組裝點釘位之既有拍板＝ADR 0064 決定一；guard_no_escalation 消費者分布＝007 刀 U5 碼品質輪查定"
tags: [by-design, handler, code-structure, backlog-disposition]
---

## 背景

handler 層的「跨 handler 共用件」現有兩個家：

- `handler/common.rs`：**八件收攏名冊**（`audit_operator`／`json_or_default`／
  `resolve_operator_names`／`MAX_CURRENT`／`tristate`／`blank_to_none`／`db_status_to_wire`／
  `wire_two_value_to_db`；B-094 收攏、B-108 續收、B-127 收單）。
- `handler/user.rs`：**as-built 例外恰四件**（`finish_user_write`／`password_policy_err`／
  `pwd_set_too_frequent_err`／`guard_no_escalation`），`handler::user_center` 與
  `handler::throttle` 以 `use crate::handler::user::…` 消費、全樹零同形拷貝。

B-141 立案時所稱「與 `handler/mod.rs` 宣告不一致」已由 007 刀 U4／U5 消解：`mod.rs` 檔頭
把宣告拆成「八件名冊住 common」＋「例外四件住 user、逐件附理由」兩截。殘餘待裁只剩一題：
`password_policy_err`／`pwd_set_too_frequent_err` 是純 `AppError` 組裝（零 entity、零 casbin
觸發），**技術上**搬得進 `common`——要不要上提？

四件的成因各有硬約束：

- `finish_user_write` **結構性搬不動**：它內含觸發 casbin 熱套的那一腿，而
  `handler/common.rs` 檔頭不變式逐字寫著「零 `reload_enforcer`」、
  `tests/authz_entrypoint_lint.rs` 的 `RELOAD_CALL_FILES` 名冊只列 menu／policy_archive／
  role／user 四檔——搬家會同時撞倒那句不變式與那張名冊。
- 兩支 err 的組裝點已由 **ADR 0064 決定一**釘在 `handler/user.rs`（`AppError::BizData`
  射程二鍵的單一組裝點、`pub(crate)` 供三個設密入口共用）。
- `guard_no_escalation` 的九個消費者有**八個就在 `handler/user.rs`**（八支寫端各一次），
  跨檔消費者僅 `throttle` 解鎖帳號維一處。

## 決定

**四件同住 `handler::user`；`common` 收攏名冊維持八件；兩支 err 不上提。**

判準＝**能搬動≠該搬動：共用件的家取語意層、而非技術可行性。**四件同屬「使用者域寫端」
這一層語意（寫端收尾式、設密拒因組裝、寫端守門件），把技術上搬得動的那兩件單獨上提，
「這組東西住哪」就會出現第二份說法——語意上同組的東西分居兩檔，每個新消費者都要重新
考證一次「為什麼這件在這、那件在那」。`common` 的八件名冊語意一致（跨域的形收攏），
兩個家各自成立、以 `handler/mod.rs` 檔頭例外名冊與 `handler/common.rs` 檔頭反向指路句
互為索引。

## 替代案

**A. 兩支 err 上提 `common`（拆兩個家）。** 未採——技術可行但語意破組；且須先動
ADR 0064 決定一的組裝點釘位，為了「名冊看起來大一件」去翻一個零缺陷的拍板不成比例。

**B. 四件全上提、連 `finish_user_write` 一起。** 未採——撞倒 `common` 不變式與
`RELOAD_CALL_FILES` 名冊雙擋；那兩道閘守的是「casbin 熱套觸發面可枚舉」，比收攏對稱性
重要。

## 後果

- 第三個 handler 要消費這四件時：`use crate::handler::user::…` 並直接引用本 ADR，
  **絕不**在自家長出私有拷貝（`FINISH_USER_WRITE_CONSUMER_FILES` 名冊擴列紀律照舊）。
- 日後真要上提兩支 err：須先 supersede **ADR 0064 決定一**（組裝點釘位）**與本 ADR**，
  兩者缺一即為未經拍板的結構漂移。
- B-141 關帳出列；`handler/common.rs` 檔頭補反向指路一句（同批落地）。

## 翻案觸發器

- 四件中任一件出現**使用者域之外**的穩定消費面（語意層判準的前提鬆動）；或
- `common` 的「零 `reload_enforcer`」不變式／`RELOAD_CALL_FILES` 名冊被正式重談——
  屆時 `finish_user_write` 的「搬不動」硬約束才有鬆動空間，四件是否仍同組須重新論證。
