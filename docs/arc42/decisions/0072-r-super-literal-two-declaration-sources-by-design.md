---
id: "0072"
title: R_SUPER 字面兩宣告源並存係 by-design——facade 層 `sys_role::SUPER_ROLE_CODE` 為 model／handler 層唯一宣告源、auth 層 `no_escalation::ROLE_SUPER` 保留憲法同源直書
date: 2026-08-31
status: accepted
supersedes: []
superseded_by: []
provenance: "B-137（007-user-password-admin 收刀留帳、2026-08-30 立案：R_SUPER 在生產面有兩份獨立字面常數——實際盤點為三份、sys_role 側當時帳面漏列）；user 親決 2026-08-30「sys_user 那份收到 sys_role 既有 pub const、auth 側保留直書＋立 by-design ADR」；rust 維護批 R1 落地"
tags: [auth, constants, by-design, backlog-disposition]
---

## 背景

seed 超管角色碼 `R_SUPER` 在生產碼曾有**三份**獨立字面宣告，各因當時執行單元的允許改動面受限而就地重打：

1. `model/facade/sys_role.rs` 之 `pub const SUPER_ROLE_CODE`（005-role-menu-crud T011 最早進場；updateRole 停用護欄用，後被 `sys_casbin_archive`／`sys_casbin_policy` 跨模組消費）——B-137 立案時帳面**漏列**這份，條目只記兩份；
2. `model/facade/sys_user.rs` 之 `pub const SUPER_ROLE_CODE`（007-user-password-admin U2 新增；島 I3「恆禁解除超管指派」判準，消費者＝`handler/user.rs`）——其碼註自陳「全樹第二份同字面」，因 1. 漏列而**失真**（實為第三份）；
3. `auth/no_escalation.rs` 之私有 `const ROLE_SUPER`（同刀 U1 新增；`ActorScope::All` 判定用）——rustdoc 載憲法 §I.7 之 I7 條文**逐字具名** `R_SUPER` 的同源理據。

三份**各有機器釘**（sys_role 側對 seed 首角色列對賬、sys_user 側對活性列與持有者對賬、no_escalation 側字面斷言），任一漂移即紅——問題從來不是假綠面，而是同一個 seed 角色碼有三個宣告源：日後改碼名要靠人記得改三處，任何一處的碼註對「全樹共幾份」的描述都是會腐的衍生事實（sys_user 側已實證失真一次）。

## 決定

1. **收成兩份**：facade 層 `sys_role::SUPER_ROLE_CODE` 為 model／handler 層**唯一宣告源**——sys_user 側宣告刪除，`handler/user.rs` 島 I3 判準兩處與 sys_user 側釘值測（`island_i3_seed_constants_are_pinned_to_the_frozen_seed`）改引 sys_role 側；★釘值測**仍對活性列與持有者對賬**（不是只比字面），鑑別力不折損。
2. **`auth::no_escalation::ROLE_SUPER` 保留直書**、不改 import——by-design。理由：①憲法 §I.7 之 I7 條文逐字具名 `R_SUPER`，auth 側直書字面即與條文同源、不是魔法字串；②本 ADR 立一條層偏好：auth 層與 model 層不共用**常數字面**——既有自陳「零 `entity::`」只管型別面（要角色仍是向 `model::facade` 要、與引用常數不相斥），未涵蓋字面常數，本條是其**補充**而非其推論；③該側自有對 seed 的機器守——功能測 `actor_scope_of_maps_seed_users_to_their_scopes` 以真庫斷言 seed uid 1 之 A 為全集（seed 改名而 `ROLE_SUPER` 未跟即紅）；另有釘值測 `role_super_literal_matches_seed_and_constitution` 釘住常數字面本身（擋「單獨改了常數」）。
3. 三支釘值測**全數保留**——sys_role 側對 seed 首角色列對賬、sys_user 消費面對活性列與持有者對賬、no_escalation 側釘住字面本身，缺一即失「各消費面獨立對賬」的鑑別力。

## 後果

- 改超管角色碼＝改**兩處碼**（`sys_role::SUPER_ROLE_CODE`＋`no_escalation::ROLE_SUPER`）**＋憲法 I7 條文＋seed**。碼與 seed 之間有機器守：漏改 sys_role 側由其 seed 首角色列釘值測擋、漏改 auth 側由 `actor_scope_of_maps_seed_users_to_their_scopes` 真庫斷言擋、單獨動任一常數由各自釘值測擋——碼面「靠人記得」自三處縮為兩處且皆有機器守。★誠實記——已知代價：**憲法 I7 條文那一處零機器守、靠人記得**（全樹無任何條款把條文字面與碼／seed 對賬；碼與 seed 都改好、只漏改條文時全量測試仍綠）。
- sys_user 側自此無宣告：其節首碼註與釘值測 doc 指向唯一宣告源與本 ADR；「全樹第 N 份」一類份數描述不再出現於任何一側碼註（份數是會腐的衍生事實，教訓同 ADR 0071 理由 4）。

## 翻案觸發器

命中任一即立新 ADR `supersedes: ["0072"]`：

1. **憲法 I7 改為不具名**（條文不再逐字寫 `R_SUPER`）——auth 側「與條文同源」的直書理據即消失，屆時應改引 model 層常數、收成一份；
2. **auth 層拍板改為依賴 model 層常數**（放棄本 ADR 所立「不共用常數字面」的層偏好）——同樣收成一份，並同批檢視 `auth/no_escalation.rs` 其餘的層邊界自陳是否連動。
