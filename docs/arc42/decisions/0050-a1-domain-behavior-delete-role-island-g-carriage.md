---
id: "0050"
title: A1 域行為——deleteRole 家族入序列化域＋免 reload 論證＋島 G 行為 ADR 承載（G1/G3/G4/G5）＋archive 三自由度 won't-use 與翻案觸發條款過境
date: 2026-08-18
status: accepted
supersedes: []
superseded_by: []
provenance: "005-role-menu-crud 之 T003-②；拍板鏈＝docs/brainstorms/005-role-menu-crud.md §3（user 親決 #8 deleteRole 入域／#10 archive 三自由度全不動＋grilling G6 守門兩腿窗、2026-08-18）；藍本＝rev4:handler/role.rs（delete_role 全函式零 reload 之 as-built）＋rev4:ADR 0048（島 G 五條原文＋停用雙護欄附帶拍板）＋rev4:ADR 0049（role_id 欄 won't-add 分析＋未來翻案觸發條款原文）"
tags: [authz, governance, role, concurrency, state-machine]
---

## 背景

本刀先於島 G（casbin 授權治理；隨授權治理刀入憲）兌現其四條的**行為**：deleteRole 之
撤銷必歸檔（G3）、三層守門與批次原子（G4）、lock-then-redecide 鎖序（G5）、以及授權變更
DB-first 同交易稽核（G1 前半；reload 失敗契約半邊＝ADR 0049）。判例＝rev4 拒絕把樹結構
塞進島 G（「一台狀態機一島」、rev4:ADR 0052 背景節）；rev5 對偶形＝**島 G 行為先由本 ADR
承載條文、隨授權治理刀入憲時轉正零修憲**——條文早入＝憲法宣告無機器證的 grant 面行為，
條文晚入＝本刀行為無凍結位，ADR 承載是唯一兩全。

另兩筆拍板同場凍結：deleteRole 家族入選單序列化域（rev5 對 rev4 未論證併發窗的補強）、
歸檔表三個 rev5 自由度 won't-use（保零 migration）。

## 決定

### 1. deleteRole／batchDeleteRole 入選單序列化域（rev5 新增域成員）

rev4 的 deleteRole 不入選單域，而 deleteRole 掃 `v0=role_code` 之 casbin_rule 列、
deleteMenu 掃 `v1=route_name` 列——兩者可寫**同一批列**、列鎖不相交、READ COMMITTED 下
互相的 phantom 窗**零論證零測試**（B-025 記錄的預定客戶之一）。rev5 拍板拉進域：治理
QPS≈0、序列化代價≈0，換得「兩寫端互斥＝競態結構性不可達」＋機器證（pg_locks advisory
NOT-granted 斷言、T008）。★域內其餘 role 寫端（addRole／updateRole／roleHome）**不進域**
——零 casbin 面、零選單資料，入域徒增鎖競爭面。

### 2. deleteRole 免 reload 論證（FR-013 後半；spec 之 User Story 4 場景 4）

deleteRole 成功後**不觸發判定面同步**，論證＝in-use 守門保證刪除時零掛載
（`others = total − operator_is_member = 0` 才放行）⇒ 已無任何使用者屬該角色 ⇒ 判定面
殘留的該角色 p 列（至下次 reload 前）**無授權效果**——`g(sub, role)` 對一切現役使用者恆假、
殘留列永不命中；殘留於下次任一移除面 reload 自然消失。rev4 as-built 同形
（rev4:handler/role.rs 之 `delete_role`／`batch_delete_role` 全函式零 reload 呼叫；該檔
唯一 reload 點屬三維授權寫端）。本刀加特性斷言測試（T018 之 deleteRole 零 reload）。

### 3. 島 G 行為承載（條文隨授權治理刀入憲；本刀行為以本節為凍結位）

- **G1 前半（真相唯一、DB-first）**：授權變更（本刀＝移除面歸檔）與其操作稽核 MUST 同一
  交易落地、絕不走判定引擎管理 API 寫面；判定面由真相全量重載導出。失敗契約半邊＝ADR 0049。
- **G3（撤銷必歸檔）**：deleteRole 通過守門後，同交易掃 `v0=role_code` **全三維含
  protected 列**做 archive-move（完整快照＋`role_id`＋reason=`role_soft_delete`）；
  `role_soft_delete` 列 MUST NOT 可手動復原（reason gate 單點 fn 承載、T014）；
  **角色刪除單向**——本刀與授權治理刀皆無 role restore 端點。
- **G4（刪除守門與批次原子）**：固定序三層守門①seeded（`SEEDED_ROLE_IDS=[1,2,3]`＋
  `SUPER_ROLE_CODE="R_SUPER"` 常數本刀建、碼內 hardcode 形照 rev4——零表欄零 migration 的
  刻意取捨）②in-use（精修 `others = total − operator_is_member`；拒因語意回**誠實總掛載**、
  純 i18n key 零攜參）③self-role（操作者所屬角色不可刪）；批次 id 升冪逐項全套守門、
  任一違規**整批拒**（no-partial）、單一交易。
- **G5（lock-then-redecide）**：一切向現役授權寫入、或改動角色活性／啟用狀態的寫端 MUST
  同交易 `FOR UPDATE` 鎖標的列、鎖內重判前提後才落寫、永不信 pre-read；deleteRole 家族
  另進序列化域＝rev5 對此範式的加強（advisory 先於列鎖、固定鎖序
  `advisory → 歸檔表列 → sys_role 列 → sys_menu 列 → casbin_rule`）。
- **停用雙護欄**（rev4:ADR 0048 後果之附帶拍板同形過境）：操作者不得停用自己所屬角色＋
  R_SUPER 恆禁停用（**不因操作者身分而異**）；停用即斷權沿基線行為（授權讀端濾 status）。

★**grilling G6 註記**：in-use／self-role 兩腿於刀 B（user 角色指派寫端）落地前生產面
**結構性不可達**——新建角色無工具可指派（永零掛載）、seed 角色被 seeded 腿先擋；測試以
直種 `sys_user_role` 指派列構造真實觸發（資料態判定、零測試旗標、非 vacuous——ADR 0024
精神）。拆段建＝同域分段長成、非裝飾性守門。

### 4. archive 三自由度 won't-use（brainstorm #10；保零 migration）

歸檔表 `sys_casbin_policy_archive` 對照 rev5 需求的三個潛在結構變更**全不動**：

1. **`role_id` 維持 nullable**——`role_code` 查無活角色時誠實退化寫 NULL（menu 維跨角色
   掃描逐列以 v0 反查）；NOT NULL 化需 migration 且抹掉「歷史列未知」的誠實語意。
2. **不加 `protected` 快照欄**——rev4:ADR 0049 三不變式 rev5 原封成立：①可復原列必經
   revoke 路徑而 protected-reject 保證含 protected 列的撤銷整批拒 ⇒ revoke 歸檔列原值恆
   `protected=false`②protected=true 列結構上進不了 archive（seeded 守門擋死連動歸檔路、
   grant 恆寫 false、un-protect 永不 UI 化）③對現行 restore 零收益。
3. **不加 `menu_id` 同實例欄**——menu 側零繼承由 reason gate 一刀封死：menu 維歸檔僅三
   reason（`role_soft_delete`／`menu_soft_delete`／`menu_button_removed`）且**三者全屬
   不可復原集** ⇒ menu 維歸檔列結構性無復原路徑 ⇒ 同實例判定（rev4 以 `role_id` 對 role
   維所做的）在 menu 維**無判定時點**、加欄零消費者。

★**翻案觸發條款**（rev4:ADR 0049 原文照字面過境＋rev5 語境增補一句）：任何後續刀若引入
role restore、把 protected 政策掛上非 seeded 角色、或將 un-protect UI 化——上列不變式即破、
缺欄變成靜默降權破口（restore 後 protected true→false）；**屆時該刀 MUST 自帶 protected
快照欄（NULL=unknown 誠實退化）並復核本 ADR**。rev5 增補：若引入使 menu 維歸檔列出現
**可復原** reason 的寫端，同理 MUST 復核 `menu_id` 同實例欄之必要性。

## 後果

- T016～T018（role facade）依本 ADR §3 施工；T007（域鎖底座）之域成員清單含 deleteRole 家族。
- 島 G 條文隨授權治理刀入憲時，本 ADR §3 行為承載段由該刀 Amendment 轉正——本 ADR 不
  supersede（行為記載與 won't-use 分析仍有效）、該刀 ADR 引用本檔為 provenance。
- B-025 之 deleteRole×deleteMenu 併發窗客戶消滅（T037 帳面處置：敘述更新、不關帳）。
- 空陣列 batchDeleteRole 語意照 rev4 as-built（U7 實作單元對 rev4 碼定案並測、契約補記）。
