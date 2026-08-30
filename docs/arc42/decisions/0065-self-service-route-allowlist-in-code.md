---
id: "0065"
title: 自助路由白名單為後端碼內常數、恆併於 Casbin 過濾之後——rev5 缺 rev4 的頁級豁免條文，改以「業務 menu 射程＋hide_in_menu seed 實值」二支柱立論
date: 2026-08-30
status: accepted
supersedes: []
superseded_by: []
provenance: "007-user-password-admin 之 T071（tasks.md Polish 階段主線任務）；承 spec FR-032（過濾後恆併入、只收受眾為本人之自助頁、RBAC 資源頁禁入、seed 政策列保留、兩支單測）＋FR-043③；憲法檢查已於 plan.md Constitution Check 第 3 項過關（PASS，援 brainstorm Q22 之 user 親決）；as-built 落點＝本刀 U4 之 handler/route.rs（T048）；藍本＝rev4:ADR 0065（rev4:014-user-center），★同號屬巧合、rev5 與 rev4 的 ADR 編號無對應制度（ADR 0012 編號命名空間紀律）"
tags: [routing, authz, casbin, self-service, constitution-check]
---

## 背景

`GET /route/getUserRoutes` 是前端路由樹的唯一來源，其內容＝casbin `menu` 維度對操作者現役角色
的枚舉結果。個人中心（`user-center`）在 seed 裡有政策列，但**只勾給 `R_SUPER`**
（`casbin_rule` id 123＝`p|R_SUPER|user-center|menu`）。⇒ 非超管登入後拿不到該路由，
點頭像下拉的「個人中心」會走進 404。

rev4 以 rev4:ADR 0065 解掉這件事：在 casbin 過濾結果之後恆附掛一個寫死的自助路由白名單。
rev5 起初**明文不帶回**——`handler/route.rs` 檔頭舊句逐字寫著白名單不帶回，理由是「前提未成立」：
個人中心兩支端點與改密卡在 rev5 都還不存在，那個頁面是一個 7 行的空殼。本刀把改密卡與
`changePassword`／`getPasswordPolicy` 兩支端點做出來，那個理由自此消失（research R1 第 17 列、
brainstorm Q22 拍板）。

**但 rev5 不能照抄 rev4 的憲法論證。** rev4 的主錨是它自己憲法的 §III.2(g)——該條明文把
user-center 標為「`hideInMenu:true`、經頭像下拉入口、**非 Casbin menu**」，等於在條文層先把這一頁
劃出 Casbin menu 治理域，白名單只是那條豁免在組裝層的實作。**rev5 憲法沒有這一條**：
§I.2 的規則句是無限定的「menu 由 Casbin RBAC enforce、有權才顯示」。照搬 rev4 的說法會引用到
一條不存在的條文。

## 決定

**白名單成立、形制照 rev4（後端碼內常數、casbin 過濾之後恆併入），但憲法立論在 rev5 自行重建。**

`handler/route.rs`：`const SELF_SERVICE_ROUTES: [&str; 1] = ["user-center"];`

### 一、立論二支柱（取代 rev4 的頁級豁免條文）

1. **§I.2 含義第一條的射程是「業務 menu」**——條文逐字：「業務 menu 走 `/route/getUserRoutes`
   → 後端 Casbin enforce 過濾 → 前端顯示」。個人中心不是業務資源頁：它沒有受治理的資料面，
   受眾恆＝**登入者本人**，可達性不隨角色而變。把它交給 RBAC 治理，治理的是一個沒有變數的量。
2. **`hide_in_menu` 的 seed 實值＝`TRUE`**（`sys_menu` id 16，實值查證非推測）⇒ §I.2 規則句的
   「有權才**顯示**」在側欄面對這一頁**結構性不觸發**：它從來不出現在側欄，入口恆是頭像下拉。
   白名單改變的是「這條路由在不在回傳樹裡」（＝點下去會不會 404），不是「側欄多不多一項」。
   ★該 `hide_in_menu` 值是 upstream route meta 自帶、照原樣入 seed，依 §I.2 釋義②
   （ADR 0005 之 6 列白名單）**不視為啟用前端隱藏機制** ⇒ 支柱 2 不與 §I.2「hideInMenu 不啟用」
   相抵。

★兩支柱缺一不可：只有 1 會讓「什麼算業務頁」變成可爭辯的形容詞；只有 2 會讓任何 `hide_in_menu`
的頁面都能進白名單（那正是 rev4 條文想擋的）。

### 二、併入點的次序不可反

白名單 MUST 併在 casbin 過濾**之後**。併在之前（或把白名單塞進 `roles` 集）＝「先加進去再讓
casbin 決定要不要濾掉」——對零 `menu` 政策的角色仍然過不了，白名單整個失效且**不會紅**
（超管測照過，因為超管本來就有那列政策）。

### 三、白名單擴充紀律（承 rev4:ADR 0065 逐字）

僅限「受眾＝任何登入者本人」的自助頁；**任何 RBAC 資源頁禁入**，授權仍走 casbin 唯一路徑。
擴列＝回本 ADR 走第一節二支柱重驗，不是在常數陣列裡多加一個字串。

### 四、seed 政策列保留不動

`p|R_SUPER|user-center|menu` 續留（`HashSet::insert` 天然去重，雙來源命中不生重複節點）。
硬刪屬 seed 移除軌道（B-060 家族），非本刀射程。

## 替代案

**A. 改 seed，把 user-center 的 menu 政策列勾給全部角色。** 未採——三條理由：①**新建的角色仍會
漏配**，而「登入即可達」應該是型別層的事實，不是靠資料維護的約定②casbin 面多出三列純冗餘列要
長期維護③它把一件「與授權無關」的事寫進授權表，日後讀政策表的人會以為個人中心是個受治理資源。

**B. 在 rev5 憲法補一條 user-center 頁級豁免（照 rev4 §III.2(g)）。** 未採——為單一頁面開憲法條文，
而現行條文的射程論證（決定一）已經足夠；且 §I.2 釋義②已經處理過 `hide_in_menu` 在 rev5 的定位，
再開一條會出現兩處講同一件事。★若日後白名單成長到三頁以上、或收進一個不帶 `hide_in_menu` 的頁面，
本替代案應重新評估——屆時支柱 2 失效，靠支柱 1 獨撐會退回形容詞之爭。

**C. 前端把 user-center 寫進 constantRoutes。** 未採——§I.2 明文 constantRoutes 恰 login／404／403
三頁；且前端寫死會讓「後端為路由唯一來源」這條慣例破口，日後查「為什麼這個角色看得到這頁」時
要多查一個地方。

## 後果

- 任何登入角色（含未來新建、含零 `menu` 政策者）恆得 `user-center` 路由；機器守＝本刀 U4 的兩支
  單測（「零 menu 政策角色仍得自助路由」與「白名單外路由不受影響」）。
- `handler/route.rs` 檔頭原本那句「白名單不帶回」已於本刀 U4 改寫為帶回＋理由消失的記載——
  ★**這是本刀推翻碼內舊敘述的一例**（plan.md §II 設計拍板檢查第 6 項已預告），非漏改。
- ★**留給後人的判準**：日後要往白名單加東西，先問「這一頁對不同角色的可達性有沒有差別」——
  沒有差別的才是自助頁；有差別而想用白名單抹平差別的，要的其實是一列 casbin 政策。
- 本 ADR **零碼改動**：as-built 已於本刀 U4（T048）落地。
