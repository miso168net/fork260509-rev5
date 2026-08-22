---
id: "0051"
title: restoreMenu 復原重驗補常量父鏈腿——閉合軟刪常量後代繞道窗（B-095 處置拍板）
date: 2026-08-22
status: accepted
supersedes: []
superseded_by: []
provenance: "005-role-menu-crud 收刀 final holistic review 查定（run wf_4f12039f、findings 2+3 合併）；user 親決 2026-08-22「merge 前補第四腿」；B-095 立案→改寫→本 ADR 關帳"
tags: [menu, governance, state-machine, constitution-island-h]
---

## 背景

憲法 v1.7.0 島 H3：常量選單 MUST NOT 掛於常量性非真之父下。寫端主防線兩半皆在——
create 守門④（常量標的驗父鏈常量性）與 updateMenu 反面腿（清 constant 時掃常量治理域
後代、有即拒）。final review 查得殘餘可破路徑（五步全正常端點、跨 U10×U12 單元邊界縫）：
把常量子 C 軟刪→清父 P 的 constant（向下掃描走治理域＝未刪含停用、已軟刪的 C 掃不到、
放行）→復原 C（原復原重驗恰三腿：已刪存在／同鍵活性衝突／父未刪，零常量驗）⇒ C（常量）
掛於非常量 P 下＝不變式被破。現況 seed 零常量列＝零存量影響，但憲法宣告存在已知可破
路徑＝宣告強於機器證。

## 決定

1. restoreMenu 復原重驗**補第四腿**（固定序＝已刪存在→同鍵活性衝突→父未刪→★常量父鏈）：
   標的 `constant == TRUE` 時驗其父鏈（治理域內全祖先）常量性，非真即拒——沿 create
   守門④同式同鍵 `biz.menu.constantParent`（零新 i18n、零 wire 變更）；非常量標的零驗、
   頂層常量豁免、鏈斷保守拒。
2. 落點＝`facade/sys_menu.rs::restore_locked` 第④腿；`MenuRestoreError` 增 `ConstantParent`
   變體、handler `map_restore_err` 增臂（值域仍恰十一鍵集）。
3. 機器證＝`restore_constant_target_reverifies_parent_chain_b095` 四腿（繞道正例拒＋零變更
   零稽核／全常量鏈過／非常量零驗／父未刪先序）；變異驗證（第四腿短路）紅→還原綠。

## 後果

- 島 H3 不變式自此在 create／update（雙向）／restore 三寫端面皆有機器守；治理域
  掃描（未刪含停用）與軟刪列的縫由復原時點重驗閉合——「軟刪期間父鏈變動」一律在
  回到活性域的那一刻重審，與「復原＝重入治理域須全套重驗」的既有取態一致。
- 使用者可見行為變更（前後對照）：原本繞道五步後復原 C 會成功並造出違規態；補後同
  操作回 `2222 biz.menu.constantParent` 拒因 toast，需先恢復 P 的 constant（或改掛 C）
  再復原。
- 契約 wire-menu-admin §8 已同步補列第四腿；B-095 關帳。
