---
id: "0067"
title: ADR 0042 第 2 項之解鎖入口歸屬預測訂正（實落使用者管理頁、可見落差同批解除）＋ADR 0053 款四判定面同步觸發矩陣擴入 user 域三支寫端（含訂正後完整矩陣）
date: 2026-08-30
status: accepted
supersedes: []
superseded_by: []
provenance: "007-user-password-admin 之 T071（tasks.md Polish 階段主線任務）；承 spec FR-033（觸發源恰二、reload 呼叫者名冊擴一檔、矩陣補列）＋FR-043⑤；訂正範式＝憲法 v1.6.1 對 ADR 0043 理由段之處理形（決定不變、以新文件為準、同一假述逐處同批改對）；款一之 as-built＝本刀 U7 之 user-unlock-modal.vue（T061）＋U5 之 unlock_login 掛點（T055）；款二之 as-built＝本刀 U2／U3 之 finish_user_write 實參（T026）與 U5 之名冊閘（T054）；B-093 之閉合候選①即本款二"
tags: [adr-correction, authz, casbin, reload, unlock, known-state]
---

## 背景

004-ip-trust-anchor 收刀時，ADR 0042 把兩件與本刀正面相關的事寫進了已知態集，而本刀的
as-built 讓其中一件的**理由**失準、另一件（ADR 0053 款四的觸發矩陣）需要擴列。兩者都不是翻案：
決定不變，變的是措辭與涵蓋面。ADR body 不可變，故以本檔承載，範式取憲法 v1.6.1 對 ADR 0043
理由段的處理形（決定不變、以新文件為準、同一假述逐處同批改對）。

## 決定

### 款一：ADR 0042 第 2 項——「解鎖入口自然歸屬稽核／登入紀錄管理頁」之歸屬預測訂正

ADR 0042 第 2 項逐字：

> **解鎖端點無 UI 按鈕**。……理由是解鎖的操作入口自然歸屬「稽核／登入紀錄管理頁」，
> 該頁不在本刀射程。★可見落差：超管在 UI 上找不到解鎖入口，須由呼叫端（腳本／走查）直打端點。

**「不建 UI」這個決定在 004 是對的**（該刀確實沒有合適的宿主頁），訂正的只是那句歸屬預測：
as-built 的入口落在**使用者管理頁**——頁首「解鎖登入」鈕（`user:unlock` gating）＋
`modules/user-unlock-modal.vue` 的雙維浮層，不是稽核／登入紀錄管理頁。

★**為什麼實際歸屬與預測不同**：解鎖是一個**即時處置**動作，操作者手上握的事實是「某個人登不進來」，
他要找的是**那個人**——而找人的地方是使用者管理頁。稽核／登入紀錄頁的受眾是**事後查閱**：
它回答「發生過什麼」，不回答「現在把誰放出來」。把處置鈕放在查閱頁，等於要求操作者先學會
從紀錄反查標的。★判準留給後人：**入口歸屬看的是「操作者動手時手上有什麼」，不是「這個動作的
紀錄事後會出現在哪裡」。**

★**ADR 0042 第 2 項的「可見落差」同批解除**：超管自本刀起在 UI 上找得到解鎖入口。該已知態的
續存部分只剩「IP 維解鎖的標的粒度換算由後端做」這一形制事實，不再有落差。

### 款二：ADR 0053 款四觸發矩陣擴入 user 域——訂正後完整矩陣

★**本款為判定面同步觸發矩陣的現行承載處**；ADR 0053 款四表自此只作史料讀（同該款對 ADR 0049 §2
的處理）。訂正後完整矩陣（006 八列 ∪ 本刀三列）：

| 面 | 寫端 | 觸發條件 |
|---|---|---|
| 移除面 | deleteMenu | 軟刪成功**且有連動歸檔**才觸發（零政策列標的＝零觸發） |
| 移除面 | batchDeleteMenu | 整批成功**且有連動歸檔**才觸發 |
| 移除面 | updateMenu | buttons 絕版歸檔**實際發生**才觸發 |
| grant 面 | updateRoleMenu | `Applied` 即觸發、**不問 diff**（空 diff 仍觸發＝刻意例外） |
| grant 面 | updateRoleButton | 同上 |
| grant 面 | updateRoleEndpoints | 同上 |
| 回收桶 | restorePolicy | `Applied` 觸發；`NoOp`／`NotRestorable` 不觸發 |
| **指派面（007 新增）** | **updateUser** | **角色集實際變更（差集非空）才觸發**——★與 grant 面三支方向相反，理由見下 |
| **指派面（007 新增）** | **deleteUser／batchDeleteUser** | **標的原本有指派列才觸發**（`had_roles`；零指派＝零觸發） |
| 其餘 | addUser／restoreUser／kickUser／resetUserPassword／updateUserSessionPolicy／deleteRole／batchDeleteRole／addRole／updateRole／roleHome／addMenu／restoreMenu | 零觸發 |

被拒／標的不存在一律 `?` 早退結構性不觸發；所有觸發點皆於交易 commit 後、不持 `state.enforcer`
讀鎖呼叫同一支 `reload_enforcer`。呼叫點名冊 `RELOAD_CALL_FILES` 於本刀擴入 `handler/user.rs`
（漏擴即紅）；★本刀 U4 另補 `FINISH_USER_WRITE_CONSUMER_FILES` 名冊——`finish_user_write` 由私有
提升為 `pub(crate)` 後，`handler/user.rs` 唯一那行 `reload_enforcer` 就住在它體內，任何 handler
都能借道觸發而該檔不出現 `reload_enforcer` token（可見性放寬把上一道閘的射程打穿，L-069）。

#### 為什麼 updateUser 不照 grant 面的「不問 diff」

ADR 0053 對 grant 面三支的「不問 diff」有一條前提：**呼叫這支端點本身就意味著授權可能變了**。
那三支是專用授權端點，空 diff 是罕見情形，多跑一次 reload 無害且省掉「diff 判定漏算」一整類缺陷。

**updateUser 不滿足那條前提**：它是通用更新端點，`roleIds` 只是八個欄位之一，絕大多數呼叫
（改暱稱、改備註、改狀態）根本不動角色。照「Applied 即觸發」的話，**每一次改暱稱都會引發一次
全量 casbin 重建**。且 `roles_changed` 不是為了 reload 特地加的判定——全量替換本來就要算差集
才知道 INSERT／DELETE 哪些列，故「漏算」的風險面在此顯著低於那三支。★該布林恆 `true` 的退化形
有測試釘住（`sys_user_role` 之差集測 doc 逐字記載該劇本）。

#### ★這三列的觸發理由不是「指派列在判定面裡」

誠實記，因為這一點極易誤讀：enforcer 只載 `casbin_rule` 的 `p` 列，**`g` 列在 seed 中為零**
（實測 `grep -c` 得 0），角色一律向 `model::facade::sys_user_role` 要 **DB-fresh**。⇒ 指派列
本身不在判定面。三列的真正理由各不相同：

- **updateUser 那列＝B-093 繼承窗的閉合點**（spec 該節標題逐字「B-093 閉合」）。窗的形狀是：
  `deleteRole` 歸檔該 code 的 p 列但**免 reload** ⇒ in-memory 留著陳舊 p 列；同 code 重建角色後，
  **指派**是那條鏈的最後一步——在那裡 reload，窗就關了。B-093 明列的三個候選中，本款採①
  「指派寫端自帶 reload」（零既有拍板變更）。
- **deleteUser／batchDeleteUser 那列在判定面上是冗餘的**：角色 DB-fresh、被刪者已被撤票無 session。
  保留它是為了與 006 移除面「有變更才觸發」的口徑一致。★**這是全表唯一一列的觸發理由是「口徑
  一致」而非「判定面需要」**——日後若 reload 成本隨政策列規模上升，這是第一個可以拿掉的列，
  拿掉時不需要新的行為論證，只需要記一筆口徑分岔。

## 替代案

**款一：ADR 0042 第 2 項不訂正，僅在本刀已知態記一句「入口實落使用者管理頁」。** 未採——
0042 那句是**預測**，而它預測錯了；留著不動會讓下一個規劃稽核頁的人以為解鎖入口該搬過去。

**款二 A：updateUser 照 grant 面不問 diff。** 未採——理由見上（每次改暱稱全量重建）。

**款二 B：deleteUser／batchDeleteUser 零觸發。** 未採——會讓移除面出現「menu 有變更才觸發、
user 一律不觸發」的口徑分岔，而分岔的收益只是省下一次幾乎不發生的重建（刪使用者是低頻操作）。
★但其必要性弱於另一列，已於上文誠實記。

**款二 C：把 B-093 的窗改由 `deleteRole` 觸發同步關掉。** 未採——推翻 spec 005 FR-013 後半、
需拍板；且 B-093 條目自己就把「指派寫端自帶 reload」列為最可能解。

## 後果

- **B-093 關帳**（deleteRole 免 reload 的判定面繼承窗，由款二①閉合）；ADR 0050 §2 之免 reload
  論證**不受影響、不 supersede**——它論證的是 `deleteRole` 那一端，本款補的是鏈尾那一端。
- ADR 0042 第 2 項自此只有形制事實續存，其歸屬預測與可見落差兩部分由本檔款一取代。
- 觸發矩陣的查找點自此為本檔款二一處（ADR 0049 §2 與 ADR 0053 款四兩表皆只作史料讀）。
- ★**留給後人的判準**：新寫端要不要 reload，先問「呼叫這支端點本身是否意味著授權可能變了」——
  是（專用授權端點）→ 不問 diff；否（通用寫端，授權只是欄位之一）→ 有變更才觸發。
- 本 ADR **零碼改動**：兩款所述皆為 as-built（款一 U5／U7、款二 U2／U3／U5）。
