---
id: "0053"
title: 憲法 Amendment 1.8.0——§I.7 第八座行為島（島 G casbin 授權治理、含 G6 結構性封死）＋§III.2 MANAGE-PAGE-WIRING 用途 (iii)(iv)（三顆授權 modal 接真＋policy-archive 頁）＋§III 正文納 ADR 0052 生成檔條款＋B-104 觸發矩陣訂正
date: 2026-08-23
status: accepted
supersedes: []
superseded_by: []
provenance: "006-authz-governance 之 T001／T002（tasks.md Phase 1 主線任務）；授權鏈＝plan.md Constitution Check（條件通過、Amendment 先行）＋research R10 治理原料；拍板鏈＝docs/brainstorms/006-authz-governance.md §3（2026-08-18）＋§10 二十二題（2026-08-22 user 逐題親決：Q1 獨立 G6／Q2 謂詞不寫列數／Q3 條文只凍結方向面／Q4 grant 面 Applied 即觸發／Q5 deleteRole 免 reload 不轉正／Q13 §III.2 加兩列／Q15 H1 括號 PATCH 回填／Q18 B-104 併入本 ADR）＋spec Clarifications 2026-08-23（restorable 旗標逐腿同判準）＋U1 兩題 user 親決 2026-08-23（G5 條文層級取 a：方向面＋兩腿名、五腿全文留 ADR 0055；島 G header 不寫總數、照島 F 形列區間）；島 G 條文藍本＝rev4:ADR 0048（五條原文＋MAJOR 界定字面）＋rev5 ADR 0050 §3（005 先行承載之行為、本次轉正、不 supersede）＋ADR 0049（G1 失敗契約與觸發矩陣之 rev5 凍結位）；ADR 0052 條款順捎＝該 ADR 決定 3 之約定兌現；B-104＝BACKLOG 條目承載形（Q18）"
tags: [constitution, governance, behavior-island, authz, casbin, fork-delta]
---

## 背景

006-authz-governance（授權治理刀）撞到**兩個空凍結位**＋兩筆順捎，皆為憲法自身備有的授權
路徑、非違規待辯護：

1. **§I.7 行為島**——本刀落地 casbin 授權治理狀態機（三維授權寫端之 DB-first＋判定面同步、
   protected 整批拒、撤銷必歸檔、復原重驗、結構性封死），依 §I.7 進場規則須以 MINOR Amendment
   入憲。G1～G5 主體沿 rev4 已驗證形（rev4:ADR 0048 五條原文＋MAJOR 界定）；其中 G1 前半／
   G3／G4／G5 之行為已於 005 先由 ADR 0050 §3 承載（該 ADR 後果段明言「條文隨授權治理刀入憲
   時由該刀 Amendment 轉正、本 ADR 不 supersede」）、G1 之判定面同步失敗契約與觸發矩陣之 rev5
   凍結位＝ADR 0049。**G6 結構性封死為本刀新拍板**（brainstorm §10 Q1 獨立成條、Q2 條文只寫
   謂詞不寫列數；設計全文＝ADR 0054）。★字母記法沿 rev4：本島記 **G**（島 H 入憲時即預留此位、
   對偶 H2↔G3、H1/H5↔G5、H3↔G4 固定，對偶引用跨代穩定）；rev5 §I.7 至此為 A～H 八座。
2. **§III.2 ★ 軌道**——兩顆既有授權 modal（`menu-auth-modal.vue`／`button-auth-modal.vue`）
   與 `role-operate-drawer.vue` 之第三鈕接真需動 base-web 既有檔；policy-archive 為新 view
   頁、其 i18n 兩樹與產物四檔同 (i) 之進場形。`BASE-WEB-MANAGE-PAGE-WIRING` 現有用途 (i)
   （IP 規則頁進場）與 (ii)（role／menu 頁 CRUD 接真、且**明文把兩顆授權 modal 排除於名單外**）
   皆涵蓋不到 ⇒ 依「同軌道內的未列用途不自動授權」須 Amendment 加兩用途（Q13）。
3. **ADR 0052 條款順捎**——該 ADR 決定 3 逐字約定「憲法 §III 正文納入本條款＝隨下一次
   Amendment（授權治理刀島 G 入憲時）順捎、不單獨 bump」，本次即是（PATCH 級隨批）。
4. **B-104 訂正順捎**——ADR 0049 §2 觸發矩陣之 deleteMenu／batchDeleteMenu 兩列括號句
   「連動歸檔恆發生」**出生即誤**（as-built 三支一律 `if archived` 為門；spec 005 FR-039、
   tasks、`enforce.rs` doc 三處皆正、ADR 為唯一離群值；L-048 出生即誤形）。ADR body 不可變、
   B-104 條目約定「正式訂正窗＝島 G1 條文入憲時以新 ADR 承載」（Q18）——本次以款四承載**訂正後
   完整矩陣**（含本刀 grant 面三支與回收桶一支）。

★**T001 前置查證結論**（名單以定數落）：用途 (iii) 之修改型檔恰 3 支（兩 modal＋drawer）、
(iv) 之 base-web 既有檔恰兩語 locale＋`app.d.ts`（與 (i) 同三支）；`role/index.vue` 照 rev5
拍板不做 hasAuth gating（research R2 #10）⇒ 零 diff、不入名單；`endpoint-auth-modal.vue` 與
policy-archive 兩支 view 為 rev5 新增型新檔、承 ADR 0021 款 1 不入名冊。若實作期發現名單外
既有檔非動不可（防呆⑥空間邊界會擋下）＝名單擴列＝回本節走 §V.2、非默改。

## 決定

以**一筆 MINOR Amendment**（1.7.0 → 1.8.0）處理四款。依 §V.3，款一、款二分級為「行為島隨刀
進場（§I.7 填充）」與「軌道授權邊界擴展（新用途）」＝MINOR；款三、款四屬 PATCH 級隨同批進入、
不另 bump。★另兩處 PATCH 級回填隨批：島 H header 括號（G 位已填）與 H1 終態成員括號
（選單維／按鈕維授權寫端已兌現、回收桶復原之選單／按鈕維分支因不可復原集擴列結構性不可達
——Q15 如實形）；表外宣告 2 改寫（「rev5 無 modal 治理需求」自本刀起為假述）。

### 款一：§I.7 新增第八座行為島（島 G），條文逐字如下

> **G. casbin 授權治理**（006-authz-governance 進場；G1～G5 沿 rev4 已驗證形〔rev4:ADR 0048
> 五條原文；其行為於 005 先由 ADR 0050 §3 承載、本次轉正零修憲〕、**G6 結構性封死為本刀新拍板**
> 〔ADR 0054〕；字母沿 rev4 記 G、與島 H 對偶（H2↔G3、H1/H5↔G5、H3↔G4）；判定面同步契約之
> rev5 凍結位＝ADR 0049、觸發矩陣訂正後全表＝ADR 0053 款四）
>
> - **G1 真相唯一與同步失敗契約**：授權真相＝DB 政策表；授權變更與其操作稽核 MUST 同一交易
>   落地、絕不走判定引擎管理 API 寫面（DB-first）；判定面由真相全量重載導出——寫端成功 commit
>   後 MUST 同步、被拒／無作用／標的不存在 MUST NOT 觸發（`?` 早退之結構性保證）；★grant 面
>   （三維授權寫端）Applied 即觸發、不問 diff＝**刻意例外**，與移除面「成功且有連動歸檔才觸發」
>   並陳、勿互相「統一」；觸發矩陣本體留 ADR／活書。★同步失敗契約：重載 MUST 以「**重建成功才
>   swap**」實現、絕不對 live 判定面就地 clear-then-load；失敗→**保留上一份已知良好判定面**
>   （絕不空窗或半載）＋結構化告警＋有界重試，耗盡仍失敗→維持舊面持續告警（恢復待下次成功同步
>   或維運介入）。★方向反轉（同步失敗改為清空／全 deny）＝MAJOR。
> - **G2 受保護拒絕**：撤銷集觸及 protected 政策→整批拒、零變更（任何寫之前判定）；拒絕 MUST
>   使原因可辨識——一因一鍵（明細載體屬活書級、不入條文）；un-protect／re-protect 經一般管理
>   介面永不提供（防鎖死 by-design；保護集變更屬 seed 基線層級決策）。反轉（整批拒改部分成功、
>   開放 un-protect UI）＝MAJOR。
> - **G3 撤銷必歸檔**：revoke＝archive-move（完整快照＋來源角色識別＋reason）、grant＝INSERT
>   補齊治理欄（protected=false＋created_at/by）；刪角色 MUST 同交易全維連動歸檔（含 protected
>   列、reason=`role_soft_delete`）；`role_soft_delete` 列 MUST NOT 可手動復原；角色刪除單向、
>   無 role restore。反轉＝MAJOR。
> - **G4 刪除守門與批次原子**：刪除依固定序三層守門（①seeded ②in-use ③self-role）；批次逐項
>   驗證、任一違規**整批拒**（no-partial）、單一交易。反轉＝MAJOR。
> - **G5 復原同實例與全端點鎖序**：一切向現役授權寫入、或改動角色活性／啟用狀態的寫端（三維
>   寫入、授權復原、刪除、停用）MUST 同交易 `FOR UPDATE` 鎖標的角色列、**鎖內重判前提**後才
>   落寫（lock-then-redecide、永不信 pre-read）；固定鎖序 advisory→歸檔表列→sys_role 列→
>   sys_menu 列→casbin_rule（選單維／按鈕維授權寫端另入島 H1 序列化域、端點維寫端與授權復原
>   不入域）；復原 MUST 鎖內重驗（reason gate＋同實例：歸檔列 role_id＝現役同代碼活角色 `id`、
>   NULL→不可復原、誠實退化）後才回灌，重驗腿之固定序與全文＝ADR 0055。★刀 B 之
>   `sys_user_role` 指派寫端落地時 MUST 同納本鎖序。反轉（拔鎖序、信 pre-read）＝MAJOR。
> - **G6 結構性封死**（rev5 專屬新條）：屬「`ptype=p ∧ protected=TRUE ∧ v2∈HTTP 動詞`」之
>   `(v1,v2)` 集合（謂詞式、資料庫態鎖內現查、不寫列數）MUST NOT 授予非 R_SUPER 角色；掛點
>   恰為端點維授權寫端與回收桶端點維復原（雙路徑、同一守門）；違者整批拒、零變更；`v2='menu'`
>   之 protected 列不在射程（已知態：可見性可授、端點仍拒）；守門 MUST 非 vacuous 並配變異自證。
>   反轉（部分成功、開放 un-protect UI、掛點少一處）＝MAJOR。
> - 常數（reason 字面集、封死集量測值、觸發矩陣列數、候選集來源、重試次數）＝活書／ADR 級、
>   不入條文。

★**落字與 rev4 原文的差異五處**（research R10；防「照抄 rev4」回帶已翻案語意）：G1 不抄
「Applied 含空 diff 才觸發、Rejected/NoOp/NotFound 不觸發」字面、改寫為方向面＋「grant 面刻意
例外」句（Q3／Q4）；G2 刪「結構化明細」、改「一因一鍵、明細載體活書級」（B-024③ 純 key、
research R2 #1）；G3 不寫欄可空性、不提誰算 role_id（ADR 0050 §4 第 1 項 won't-use 語意不入條文）；
G5 寫固定鎖序、刪 rev4:L-075 類比句、復原重驗層級採 a（U1 親決）、鉤子句指刀 B；G6 全新。
停用雙護欄（ADR 0050 §3 末項）與 deleteRole 免 reload 論證（ADR 0050 §2）**不轉正**、留 ADR 級（Q5）。

### 款二：§III.2 `BASE-WEB-MANAGE-PAGE-WIRING` 加用途 (iii)(iv)，表列逐字如下

> | **★BASE-WEB-MANAGE-PAGE-WIRING** | (iii) 三顆授權 modal 接真（含 roleHome UI） | `src/views/manage/role/modules/menu-auth-modal.vue`／`src/views/manage/role/modules/button-auth-modal.vue`（兩支＝修改型，逐行 `原行:`）／`src/views/manage/role/modules/role-operate-drawer.vue`（修改型；★同檔雙用途——(ii) 之 CRUD 接真與本用途之第三鈕＋endpoint modal 掛載並存、標記各自圈界）／`src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型圈界；僅限 `page:` 樹 `manage.role` 子命名空間之資料級補鍵）／`src/typings/app.d.ts`（1 塊，新增型圈界；僅限 `App.I18n.Schema.page` 之 `manage.role` 對應型節） | 嚴格限三顆 modal 自 demo 殼接真後端（選單維／按鈕維／端點維授權讀寫＋roleHome 讀寫＋protected 鎖定＋端點 modal cascade 群組勾選）；★endpoint-auth-modal 為 rev5 新增型新檔（檔頭標記、不入名冊——承 ADR 0021 款 1）；role 頁三鈕不做 hasAuth gating（門在頁級）、role 頁 index 零 diff；兩語鍵集 MUST 相等；`route:` 樹零新增 |
> | **★BASE-WEB-MANAGE-PAGE-WIRING** | (iv) policy-archive 管理頁進場 | `src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型圈界；僅限 `route:` 與 `page:` 兩樹）／`src/typings/app.d.ts`（1 塊，新增型圈界；僅限 `App.I18n.Schema.page` 型節）；policy-archive 之 view 新檔為新增型、不入名冊；路由外掛產物四檔授權沿 (i) 列（產物檔紀律＋重算冪等檢查）、本列不重複列名 | 形照 (i)：①②塊新增型圈界標記須存在、兩語鍵集 MUST 相等、page 型節必需非「如需」；③塊產物四檔由外掛重算、禁手改；表格 scroll-x＝Σ 欄寬不變式；復原鈕無按鈕碼 gating（門＝頁級 menu 維政策列＋列級 restorable 旗標） |

檔級名單為硬邊界（§III.2 表外宣告 1）：(iii) 修改型**恰 3 支**、(iii)(iv) 之 base-web 既有檔
（兩語 locale＋`app.d.ts`）逐支以路徑寫出；名單外 base-web 既有檔一律無授權。後端拒因鍵
（`backend.biz.role.protectedRevoke`／`backend.biz.role.protectedGrant`／`backend.biz.policy.notRestorable`）
落於兩語 locale 之 `backend:` 樹與 `app.d.ts` 之 backend 型節——其授權在**既有** ★BASE-WEB-I18N-WIRING
(ii)(iii) 射程內、不隨本款擴列（同 ADR 0040／0048 判法：硬閘按「既有檔」判、與授權來源無關）；
`zh-tw.ts` 為 rev5 純新增治理孤立檔（ADR 0021 款 1）、不涉名冊。★`components.d.ts` 若因新元件
進場被 unplugin 重算＝款三生成檔紀律射程、不入名單。

### 款三：§III 正文納入 ADR 0052 生成檔條款（PATCH 級隨批、不另 bump）

於 §III「跨軌道 fork-delta 執行紀律」四 bullet 後新增第五 bullet（**散文 bullet、絕不寫成
§III.2 表列**——生成檔不入任何用途名單正是該條款本意），逐字如下：

> - **生成檔紀律**（ADR 0052 條款，v1.8.0 納入正文）：判準＝檔頭帶工具 Generated 標記之機器生成檔（unplugin 元件宣告 `src/typings/components.d.ts` 同族）與 §III.2 表內「路由外掛產物四檔」同族——由工具重算產出、**禁手改**、不逐行標記、不入任何用途之檔級名單；其變更隨引入新元件／新頁之單元同 commit 帶入，審查判準＝diff 只允許工具重算形（宣告行增刪）、出現手寫內容即紅；機器承載＝`fork-delta-lint` 之 `is_generated()` 檔頭判準

### 款四：B-104 訂正＋訂正後完整觸發矩陣（PATCH 級隨批）

ADR 0049 §2 表之 deleteMenu／batchDeleteMenu 兩列「成功即觸發（連動歸檔恆發生）」**出生即誤**；
as-built 三支移除面寫端一律以「facade 回傳是否有連動歸檔」為門（零政策列標的＝零觸發），
`enforce.rs` doc 已同批訂正並釘「恆發生形勿回帶」句。本款為島 G1「矩陣本體留 ADR」的**現行
承載處**（ADR 0049 §2 表自此只作史料讀）；訂正後完整矩陣（本刀 as-built 終態、FR-019／FR-020）：

| 面 | 寫端 | 觸發條件 |
|---|---|---|
| 移除面 | deleteMenu | 軟刪成功**且有連動歸檔**才觸發（零政策列標的＝零觸發） |
| 移除面 | batchDeleteMenu | 整批成功**且有連動歸檔**才觸發 |
| 移除面 | updateMenu | buttons 絕版歸檔**實際發生**才觸發（一般欄變更／無 buttons 變更＝零觸發） |
| grant 面 | updateRoleMenu | `Applied` 即觸發、**不問 diff**（空 diff 仍觸發＝刻意例外） |
| grant 面 | updateRoleButton | 同上 |
| grant 面 | updateRoleEndpoints | 同上 |
| 回收桶 | restorePolicy | `Applied` 觸發；`NoOp`／`NotRestorable` 不觸發 |
| 其餘 | deleteRole／batchDeleteRole／addRole／updateRole／roleHome／addMenu／restoreMenu | 零觸發（deleteRole 免 reload 論證＝ADR 0050 §2） |

被拒／標的不存在一律 `?` 早退結構性不觸發；所有觸發點皆於交易 commit 後、不持 `state.enforcer`
讀鎖呼叫同一支 `reload_enforcer`（`RELOAD_SERIAL` 互斥、keep-last-good）；呼叫點名冊閘
（`RELOAD_CALL_FILES`）與接線同 commit 擴列。★「grant 面不問 diff」與「移除面 `if archived`」
方向相反為刻意並陳（Q4）：前者 reload 代價已付、空 diff 多跑一次無害且省掉「diff 判定漏算」
一整類缺陷；後者零歸檔＝判定面零變化、觸發純屬浪費。

## 考慮過的替代案與棄用理由

- **G5 條文寫「固定序五腿」＋五腿名入憲**（U1 題①選項 b）——棄（user 親決取 a）。五腿數與序
  入憲＝增減任一腿皆 MINOR Amendment；先例＝島 H5 只列兩腿名、ADR 0051 補第四腿零修憲；且
  ③封死腿已由 G6「掛點恰兩處」凍結、①②由 G5 本句凍結，只剩④端點在冊／⑤停用不擋屬 ADR 級
  可調——與 Q3「條文只凍結方向面」同形。
- **島 G header 寫「六條」總數**（U1 題②）——棄。照島 F 形列區間（G1～G5／G6），日後照 F7／F8
  前例追加 G7 時 header 零改字；ADR 0047 三形下兩者皆合規、差在多一處漂移點。
- **島 G 隨 005 一併入憲**——已於 ADR 0048 棄（一刀一次 Amendment；grant 面零實作時條文先入＝
  憲法宣告無機器證行為）；本刀即其「屆時」。
- **G6 不獨立、併入 G2**——棄（Q1）。G2 是撤銷側（revoke 觸及 protected→整批拒），G6 是授予側
  （grant protected 給非超管→整批拒）、方向相反、掛點不同；併寫會讓「反轉＝MAJOR」的射程
  含混。照島 F 之 F6～F8 形新編號附掛。
- **封死條文寫列數（「15 列」）**——棄（Q2）。列數隨 seed 演化（刀 B 之 seed 68 上線即變），
  條文寫謂詞；量測值以 ADR 0047 (c) 形落 ADR 0054 與活書。
- **B-104 以 PATCH 單獨 bump 憲法或改 ADR 0049 body**——棄。ADR body 不可變（翻案＝新檔）；為
  一句括號訂正 bump 憲法不成比例；B-104 條目自陳「正式訂正窗＝島 G1 入憲時」，本款即是。
- **ADR 0052 條款寫成 §III.2 表列**——棄。生成檔紀律的本意是「不入任何用途之檔級名單」，
  寫成表列＝自相矛盾、且 `fork-delta-lint` 之 `load_roster` 會把它當授權檔集載入。

## 後果

- **硬閘解除點**：本 ADR accepted 且憲法 bump 落地後，「T002 accepted 前不得動任何 base-web
  既有檔」之硬閘解除（T029～T031 修改型段、T024／T031 之 zh-cn／en-us／app.d.ts page 樹自此
  有授權前提；純新增 wrapper／typings／新檔依 ADR 0021 款 1 本就不受閘）。
- **島 G 方向性面凍結**（MAJOR 界定照 rev4:ADR 0048 字面＋G6 新增）：後續刀改「整批拒」為部分
  成功、改 keep-last-good 為清空／全 deny、拔鎖序或信 pre-read、拔連動歸檔、開放 un-protect UI、
  封死掛點少一處——皆 MAJOR；常數（reason 字面集、封死集量測值、觸發矩陣列數、候選集來源、
  重試次數）留活書／ADR 可調。
- **FR-022 生效語意**（本刀明文落點）：API 判定於 grant 面 `Applied` commit 後之 reload 完成時
  **即時生效**；前端選單／按鈕顯隱於**下次載入**（重新登入或重整取路由）更新；本刀 MUST NOT
  做即時推播——活書 §8 授權慣例條目同句。
- **§III.2 表列數 10 → 12**；新列變異自證照 ADR 0040 後果之形（暫改 (iii) 列範圍欄任一路徑為
  裸措辭 → `fork-delta-lint` 須當場紅 → 還原），於本 Amendment 落地 commit 前主線親跑、關鍵行
  寫進 commit message。
- **ADR 0049 §2 表自此為史料**：觸發矩陣現行承載＝本 ADR 款四＋`enforce.rs` doc；日後再見
  「連動歸檔恆發生」句＝文檔漂移，以本款為準。**B-104 關帳**（隨 T036 落帳刪列）。
- **ADR 0052 後果兌現**：§III 正文自此為生成檔紀律之憲法級承載，ADR 0052 由「唯一權威」降為
  provenance。
- **ADR 0050 §3 行為承載段完成轉正**（該 ADR 不 supersede：§1 域成員／§2 免 reload 論證／§4
  won't-use 與翻案觸發條款仍現行有效）；ADR 0050 §4 翻案觸發條款之本刀復核結論＝ADR 0055。
- 本檔為 §V.2 之提案；user 親決兩題後轉 accepted，憲法改動與本檔同一 commit、緊接
  `python3 tools/docs-sync.py generate`；連帶 ADR 0054／0055 同批 accepted（照 005 先例
  bdc7ba4 一顆 commit）。
