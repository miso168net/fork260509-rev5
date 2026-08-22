---
id: "0055"
title: restorePolicy 鎖內固定序五腿重驗＋restorable 旗標逐腿同判準＋ADR 0050 §4 翻案觸發條款復核結論 B（reason gate 三值→五值、手動撤銷之選單／按鈕維歸檔列不可復原）
date: 2026-08-23
status: accepted
supersedes: []
superseded_by: []
provenance: "006-authz-governance 之 T003（tasks.md Phase 1 主線任務）；拍板鏈＝docs/brainstorms/006-authz-governance.md §3（歸檔表三自由度全不動、2026-08-18）＋§10 Q6（ADR 0050 §4 復核結論 B）／Q7（固定序五腿）／Q15（H1 括號回填）（2026-08-22 user 逐題親決）＋spec Clarifications 2026-08-23（restorable 旗標＝①②③④逐腿同判準）；spec FR-028～FR-033；條文落點＝ADR 0053 款一 G5（方向面＋兩腿名，五腿全文由本檔承載——U1 親決 a）；落字範式＝ADR 0051（判準／落點／機器證／使用者可見前後對照）；藍本＝rev4:server/src/model/facade/sys_casbin_archive.rs 之 restore（鎖序動作形）＋rev4:ADR 0049（role_id 同實例原理）；翻案條款原文＝ADR 0050 §4 末段（rev5 增補句即本次觸發句）"
tags: [authz, casbin, governance, state-machine, constitution-island-g, constitution-island-h]
---

## 背景

005 立歸檔寫入面時 reason gate 三值（`role_soft_delete`／`menu_soft_delete`／`menu_button_removed`、
皆連動歸檔路徑、皆不可復原），並拍「歸檔表三自由度全不動」（ADR 0050 §4）：其第 3 項
「不加 `menu_id` 同實例欄」的論證前提是「menu 維歸檔列結構性無復原路徑」，並附翻案觸發條款
「若引入使 menu 維歸檔列出現**可復原** reason 的寫端，MUST 復核 `menu_id` 同實例欄之必要性」。
本刀的 updateRoleMenu／updateRoleButton 正是那個寫端：手動撤銷會產出 menu／button 維歸檔列，
若其 reason 可復原 ⇒ 同路由鍵重建的新選單可經「復原舊實例授權」繼承（島 H2 零繼承破口）、
而 menu 維沒有同實例錨可判 ⇒ 條款觸發、必須復核。同時 rev4 的 restore 只驗兩腿（reason gate
＋role 同實例）、不驗端點在冊、不驗封死，且 `restorable` 旗標與權威判定不同判準（「顯示可復原、
點了被拒」窗）——本刀一併定形。

## 決定

### 1. ADR 0050 §4 翻案觸發條款復核結論＝B

- **觸發事實**：updateRoleMenu／updateRoleButton 之撤銷產出 menu／button 維歸檔列
  （reason=`menu_revoke`／`button_revoke`）。
- **候選**：A＝加 `menu_id` 同實例欄（migration、復原時驗歸檔 menu_id＝現役同 route_name 活選單 id）；
  **B＝手動撤銷之選單／按鈕維歸檔列列入不可復原集**（reason gate 三值→五值）。
- **結論 B**（Q6 user 親決）：零 migration（FR-056 成立）、島 H2 零破口（menu 維歸檔列仍結構性
  無復原路徑 ⇒ ADR 0050 §4 第 3 項論證**維持成立**、該條款復核完畢不翻案）。
- **代價**：回收桶對選單／按鈕維**只剩稽核閱覽**——選單維授權「撤了想復原」只能回授權面板重勾
  （與 H5「復原不回灌、可見性一律經面板重新下放」同取態）；`restorable` 對該兩維列恆 false、
  列呈停用態。

### 2. reason gate 五值（單點 fn 承載）

不可復原集＝`{role_soft_delete, menu_soft_delete, menu_button_removed, menu_revoke, button_revoke}`；
**唯一可復原 reason＝`endpoint_revoke`**（updateRoleEndpoints 手動撤銷）。字面定案於 spec FR-030
（brainstorm 暫定名不算數）；`is_non_restorable_reason` 擴五臂、既有三值成員測改為五值形
（正向餵獨立字面、負向剩 `endpoint_revoke` 與空串）——T005 首日必改（非回歸、是拍板變更）。

### 3. restorePolicy 鎖內固定序五腿（每腿照 ADR 0051 四段範式）

前置：不入選單序列化域（FR-033——可復原列只剩端點維、端點維依 H1 不屬域）；鎖序＝歸檔表列
`FOR UPDATE`（查無＝假 id／已被消費→NotRestorable）→ sys_role 列 by `v0` `FOR UPDATE`
（活性＝`deleted_at IS NULL`、不含 status；查無→NotRestorable）→ 鎖內五腿 → 回灌 → 刪歸檔列
→ 稽核 `restore` → commit → reload（僅 Applied）。

| 腿 | 判準 | 落點 | 機器證（T021／T022 交付、測名以實作為準） | 使用者可見前後對照 |
|---|---|---|---|---|
| ① reason gate | `is_non_restorable_reason(reason)` 為真→拒 | `sys_casbin_archive.rs::restore` 首腿（鎖歸檔列後） | 五值各餵一列→NotRestorable、歸檔列不消費、零變更；`endpoint_revoke` 列通過本腿 | 前：rev4 menu 維撤銷列可復原；後：選單／按鈕維列 `restorable=false`、復原鈕停用，點 API 回 `2222 biz.policy.notRestorable` |
| ② 同實例 | `archive.role_id == Some(role.id)`（NULL 恆不等）→否則拒 | 鎖活角色列後 | 歸檔 role_id 指舊實例（同 code 重建後）→拒；NULL→拒；同實例→通 | 刪角色再同 code 重建後，舊授權不可經回收桶回到新角色（H2 對偶 G3／G5） |
| ③ 結構性封死 | `role.code ≠ R_SUPER ∧ (v1,v2) ∈ P`→拒（P＝ADR 0054 §1、同一 `protected_endpoint_set` fn） | 同實例後 | 歸檔列標的於歸檔後被標 protected、目標非超管→拒；R_SUPER→通；非 P→通 | 受保護端點政策永不經回收桶流向非超管（雙路徑之第二路） |
| ④ 端點在冊 | `(v1,v2) ∈ ROUTES Policy 候選集`（`policy_endpoints()`、同 getAllEndpoints 候選）→否則拒 | 封死後 | 種一列 `(v1,v2)` 不在 ROUTES 之 `endpoint_revoke` 歸檔列→拒、歸檔列不消費（留作稽核） | 端點已下線的歸檔列 `restorable=false`、不會回灌成幽靈政策 |
| ⑤ 停用不擋 | 角色 `status` 停用→**不擋** | — | 停用角色之歸檔列可復原（Applied）、復原後該角色因停用仍斷權 | 停用≠撤銷（H4 精神）；復原不因停用被拒、也不因復原而解停用 |

三態（FR-032）：7a **NoOp**＝七欄身分鍵已 live（`ptype,v0..v5`）→刪歸檔列、commit、零稽核、
零 reload、回 `0000`；7b **Applied**＝INSERT（`protected` 顯式 false、`created_at=now`、
`created_by=復原者`）＋刪歸檔列＋稽核 `restore`→commit→reload；INSERT 撞 23505（競態）→
NotRestorable（rollback、歸檔列不消費）。五腿任一拒＝**歸檔列不消費、零變更**（歸檔列留作稽核）。

### 4. 腿 ↔ 現役寫端守門對照（縱深＝兩邊同判準）

| 腿 | 對應現役寫端守門 | 共用件 |
|---|---|---|
| ① reason gate | 連動歸檔三 reason（deleteRole／deleteMenu／updateMenu buttons 絕版）＋手動撤銷 menu／button 維 | `is_non_restorable_reason` 單點 fn |
| ② 同實例 | deleteRole 連動歸檔寫 `role_id`；島 H2 零繼承 | `role_id` 反查（`insert_archived` 內收 Model 反查、ADR 0050 §4 第 1 項） |
| ③ 封死 | updateRoleEndpoints 鎖內封死腿（ADR 0054 §2） | `protected_endpoint_set(conn)` |
| ④ 端點在冊 | getAllEndpoints 候選集＝ROUTES Policy 全集（三面板候選與判定面同源、FR-039）；updateRoleEndpoints 候選外 orphan skip | `policy_endpoints()`（具名斷環 fn） |
| ⑤ 停用不擋 | 三維寫端對停用角色照常授權（停用即斷權基線、H4 停用不升級為撤銷） | — |

### 5. `restorable` 旗標＝①②③④逐腿同判準（spec clarify 2026-08-23）

列表派生、非權威：`restorable = ¬non_restorable(reason) ∧ same_instance ∧ ¬(role≠R_SUPER ∧ (v1,v2)∈P)
∧ (v1,v2)∈ROUTES Policy 集`；⑤恆不擋故免算。批次料源：單點 fn／`active_ids_by_codes`
（一次查全頁角色 code）／單次 `protected_endpoint_set`／ROUTES 內建集合——避免逐列查。效果
＝UI 不出現「顯示可復原、點了被拒」；配「旗標與權威逐腿同判準」測（①②③④各一）。旗標為
非權威（列表時點）、restorePolicy 鎖內重驗仍是最終防線。

### 6. 計數軸註（防跨代對照誤讀）

rev4 spec 以**鎖序動作**計步（「七步」＝begin→域鎖→鎖歸檔列→reason gate→鎖角色→同實例→
menu orphan→7a／7b）；rev5 以**重驗腿**計數（五腿）、動作序另寫於 §3 前置句——兩者計數軸
不同、數字不可互相對照。rev4 之「無條件入選單域」與「menu orphan 腿」rev5 皆不帶回
（research R2 #3／#5）。

## 考慮過的替代案與棄用理由

- **A＝加 `menu_id` 同實例欄**——棄（Q6）。需 migration（破 FR-056 零 migration）、且 menu 維
  可復原仍得處理「按鈕碼跨選單聯集」的同實例定義問題（按鈕維無單一錨）；B 零欄零 migration、
  H2 以 reason gate 一刀封死。
- **三值維持、menu／button 維手動撤銷列可復原**——棄。即 ADR 0050 §4 第 3 項論證破、H2
  破口實質開啟。
- **restorePolicy 入選單序列化域**（rev4 形）——棄（FR-033）。可復原列只剩端點維、端點維
  不屬域；入域徒增鎖競爭面、且讓 restore 與選單樹寫端互斥毫無對價。
- **旗標只算兩半（reason＋同實例）**——棄（clarify 2026-08-23）。端點已下線／封死列會顯示
  可復原、點了被第③④腿拒。

## 後果

- 憲法 G5 條文只寫方向面＋兩腿名（ADR 0053 款一、U1 親決 a）、本檔為五腿全文唯一承載處；
  增減腿＝改本檔（supersede）、不修憲（除非動到 G5 本句的 reason gate／同實例／鎖序）。
- 島 H1 終態成員括號回填（v1.8.0 PATCH 隨批）：選單維／按鈕維授權寫端已入域；回收桶復原之
  選單／按鈕維分支因不可復原集擴列**結構性不可達**（條文保留終態成員句）。
- ADR 0050 §4 翻案觸發條款本次復核完畢、不翻案；其第 3 項論證維持成立。`sys_casbin_archive.rs`
  檔頭域成員句與既有三值成員測 T005 同批改寫。
- 使用者可見行為變更（前後對照總表）：選單／按鈕維撤銷列在回收桶只能看不能復原；端點維
  手動撤銷列可復原、但端點下線／封死／非同實例三類列旗標 false；復原成功即時生效（reload）、
  NoOp 回成功且列消失。
- B-093（deleteRole 判定面繼承窗）敘述更新一行（reload 觸發面 3→7、窗縮短不閉合；刀 B 復核）。
