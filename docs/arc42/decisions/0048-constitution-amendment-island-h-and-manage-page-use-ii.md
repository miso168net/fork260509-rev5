---
id: "0048"
title: 憲法 Amendment 1.7.0——§I.7 第七座行為島（島 H 選單域生命週期）＋§III.2 MANAGE-PAGE-WIRING 用途 (ii)（role／menu 管理頁 CRUD 接真）＋B-087 殘餘②補註
date: 2026-08-18
status: accepted
supersedes: []
superseded_by: []
provenance: "005-role-menu-crud 之 T001／T002（tasks.md Phase 1 主線任務）；授權鏈由 plan.md Constitution Check Q2／Q7／Q9 定為『涉及、授權以 Amendment 先行取得』、research R10 定形為 U1 硬閘；拍板鏈＝docs/brainstorms/005-role-menu-crud.md §3（user 親決 15 題之 #10/#11/#15＋grilling G1/G3/G5、2026-08-18）；島 H 條文藍本＝rev4:ADR 0052（五條原文＋MAJOR 界定字面）＋rev4:ADR 0051（設計理據）；B-087 補註＝該條目殘餘②候選處置兌現"
tags: [constitution, governance, behavior-island, menu, fork-delta]
---

## 背景

005-role-menu-crud 撞到**兩個空凍結位**＋一筆順捎，皆為憲法自身備有的授權路徑、非違規待辯護：

1. **§I.7 行為島**——本刀落地選單域生命週期狀態機（樹寫端守門／同鍵重建零繼承／序列化域／
   治理域顯示域分層／復原不回灌），依 §I.7 進場規則須以 MINOR Amendment 入憲。五條主體沿
   rev4 已驗證形（rev4:ADR 0052 之島 H 五條、設計理據 rev4:ADR 0051——含對抗式審查 23
   confirmed 全折入的血統）；**兩處為本刀新拍板**：H1 之 deleteRole 家族入域（brainstorm §3
   #8——消滅 rev4 零論證的 deleteRole×deleteMenu 併發窗）、H3 之常量父鏈句（#11——防
   `getConstantRoutes` Public 端點外洩受保護父目錄資訊）。★字母記法沿 rev4：本島記 **H**、
   G 位保留給授權治理刀之 casbin 授權治理島（兩島對偶關係 H2↔G3、H1/H5↔G5、H3↔G4 固定，
   沿用字母使對偶引用跨代穩定）；rev5 §I.7 至此為 A～F＋H。
2. **§III.2 ★ 軌道**——role／menu 兩張管理頁自 upstream demo 殼接真需動 base-web 既有檔；
   `BASE-WEB-MANAGE-PAGE-WIRING` 現僅用途 (i)（IP 規則管理頁**進場**、i18n 與路由產物面），
   涵蓋不到既有頁的 view 檔接真 ⇒ 依「同軌道內的未列用途不自動授權」須 Amendment 加用途。
3. **B-087 殘餘②補註順捎**（PATCH 級、不另 bump）——該條目逐字約定「下一次真 amendment
   順帶補註」，本次即是。

★**T001 前置半步結論（tasks 明令：名單以定數落、不得帶「視需要」）**：
`views/manage/menu/modules/shared.ts` 對最原始源基線（`fork260509-soybean-admin-base` @
`example` tip）與 rev4 as-built（`../fork260509-rev4/base-web/` 同路徑）兩向 diff **皆逐位零**
——rev4 藍本根本未動此檔 ⇒ 照藍本施工亦零改動 ⇒ **不入名單**；menu 側恰 2 檔。若實作期
發現非動不可（防呆⑥空間邊界會擋下）＝名單擴列＝回本節走 §V.2、非默改。

## 決定

以**一筆 MINOR Amendment**（1.6.2 → 1.7.0）處理三款。依 §V.3，前兩款分級為「行為島隨刀
進場（§I.7 填充）」與「軌道授權邊界擴展（新用途）」＝MINOR；款三屬 PATCH 級隨同批進入、
不另 bump。

### 款一：§I.7 新增第七座行為島（島 H），條文逐字如下

> **H. 選單域生命週期**（005-role-menu-crud 進場；五條主體沿 rev4 已驗證形〔rev4:ADR 0052、
> 設計理據 rev4:ADR 0051〕；**H1 之 deleteRole 家族入域與 H3 之常量父鏈句為本刀新拍板**。
> 字母沿 rev4 記 H；G 位保留給授權治理刀之 casbin 授權治理島，兩島對偶（H2↔G3、H1/H5↔G5、
> H3↔G4）——島 G 條文入憲前，其行為之 rev5 凍結位＝ADR 0049〔判定面同步〕與 ADR 0050
> 〔A1 域行為承載〕）
>
> - **H1 序列化域**：選單樹五寫端（新增／編輯／刪除／批次刪除／復原）＋deleteRole 家族
>   （deleteRole／batchDeleteRole；rev5 新增域成員）＋選單維、按鈕維授權寫端與授權回收桶
>   復原之選單／按鈕維分支（授權治理刀屆時兌現——條文寫狀態機**終態成員**、該等端點不存在
>   期間 vacuous 成立、屆時入域零修憲）MUST 於單一 DB 交易級 advisory 序列化域內互斥執行
>   （域鎖為載體、key 值留活書）；每一寫端 MUST 於域內鎖定標的並**重驗全部守門前提後才落寫**
>   （lock-then-redecide、永不信 pre-read）。端點維授權寫入不涉選單域、不屬本域。
>   ★**advisory key space 全域唯一**：per-user 鎖以 uid 為 key、域鎖以高位自描述 ASCII 常數
>   為 key——兩空間 MUST NOT 碰撞、新增 advisory 用途 MUST 先核既有 key space。
>   ★方向反轉（拆散序列化域、改回無域逐列鎖或無鎖 pre-read）＝MAJOR。
> - **H2 同鍵重建零繼承**：選單軟刪 MUST 同交易將其選單維授權（跨全角色）連動歸檔
>   （reason=`menu_soft_delete`）；該選單「獨有」按鈕代碼（刪除後不再屬任何未刪選單〔含停用〕
>   之 buttons 聯集）之按鈕維授權亦同交易歸檔（reason 同 `menu_soft_delete`）；編輯移除按鈕
>   代碼致其**全域絕版**（聯集域同上）時同理（reason=`menu_button_removed`）。此三類 reason
>   之歸檔列 MUST NOT 可手動復原（gate enforce 於復原權威判定）。同路由鍵重建之新選單
>   MUST NOT 經任何路徑（現役殘留、判定面殘留、回收桶復原）繼承舊實例授權——雙封＝現役
>   無殘留（序列化域＋刪除連動歸檔掃盡）＋歸檔不可回灌（reason gate）；判定面同步使
>   in-memory 面同受本條約束。反轉＝MAJOR。
> - **H3 樹結構不變式**：選單樹恆無環（改父 MUST 過防環檢查、上溯上限為常數）；活性子項
>   MUST NOT 掛於已軟刪父層之下——parent 驗證三處一致（新增／改父／復原＝父存在且未刪、
>   **停用不擋**、頂層豁免）；受保護選單 MUST NOT 可刪；存在未刪子項（不論啟停）之選單
>   MUST NOT 可刪；批次刪除逐項驗證、任一違規**整批拒**（no-partial、單一交易、child-first
>   拓撲序）。★**常量父鏈常量性**（rev5 專屬新條）：常量選單 MUST NOT 掛於常量性非真之父下
>   ——寫端 MUST 於寫入前驗證父鏈常量性、違反顯式拒。
> - **H4 不可變錨欄與治理域／顯示域分層**：`route_name`（授權列 v1 錨／i18n 錨）與
>   `menu_type` 建後不可變（寫端 MUST 顯式拒變更、MUST NOT 靜默忽略）；選單讀端分兩域——
>   **治理域**（授權候選與映射、管理列表、父選擇器）以「未軟刪」全集為準（含停用）、
>   **顯示域**（使用者可見性）以「啟用且未軟刪」為準；停用 MUST NOT 被任何全量替換語意
>   升級為撤銷（停用＝暫時下架、非撤銷）。反轉＝MAJOR。
> - **H5 復原不回灌**：選單復原 MUST 於序列化域內鎖定並重驗守門（同路由鍵活性衝突／父層
>   未刪）；復原＝成對清空軟刪欄＋原 status 保留；MUST NOT 回灌任何授權——復原後零授權、
>   可見性一律經授權面板重新勾選下放（與新增選單之兩步流一致）。反轉＝MAJOR。
> - 常數（advisory key 值、防環上溯上限、`route_name` 形制上限）＝活書級可調、不入條文。

### 款二：§III.2 `BASE-WEB-MANAGE-PAGE-WIRING` 加用途 (ii)，表列逐字如下

> | **★BASE-WEB-MANAGE-PAGE-WIRING** | (ii) role／menu 管理頁 CRUD 接真 | `src/views/manage/role/index.vue`／`src/views/manage/role/modules/role-operate-drawer.vue`／`src/views/manage/role/modules/role-search.vue`／`src/views/manage/menu/index.vue`／`src/views/manage/menu/modules/menu-operate-modal.vue`（五支＝修改型，逐行 `原行:`）／`src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型圈界；僅限 `page:` 樹既有 `manage` 子命名空間之資料級補鍵）／`src/typings/app.d.ts`（1 塊，新增型圈界；僅限 `App.I18n.Schema.page` 之 `manage` 對應型節） | 嚴格限 demo 殼接真後端（列表／搜尋／新增編輯 drawer·modal／刪除批刪／回收桶 toggle／memo 欄）；★同目錄 `role/modules/` 之 `menu-auth-modal.vue`／`button-auth-modal.vue` **明文不入名單**（授權治理刀射程；本刀出現任何 diff＝紅、T035 有 `git diff` 零輸出斷言）；`menu/modules/shared.ts` 經基線兩向 diff 判定零改動、不入名單；兩語鍵集 MUST 相等；`route:` 樹零新增（role／menu 頁 route 鍵 upstream 既在）；路由外掛產物四檔本用途零變動（不新增 view 頁） |

檔級名單為硬邊界（§III.2 表外宣告 1）：上列**恰 8 支**、逐支以路徑寫出；名單外 base-web
既有檔一律無授權。後端拒因鍵（`backend.biz.role.*`／`biz.menu.*`）落於兩語 locale 之
`backend:` 樹與 `app.d.ts` 之 backend 型節——其授權在**既有** ★BASE-WEB-I18N-WIRING
(ii)(iii) 射程內、不隨本款擴列（同 ADR 0040 後果節之判法：硬閘按「既有檔」判、與授權來源
無關）；`zh-tw.ts` 為 rev5 純新增治理孤立檔（ADR 0021 款 1）、不涉名冊。

### 款三：B-087 殘餘②補註（PATCH 級隨批、不另 bump）

於憲法 Amendment log 之 **1.5.0 條目**「data-model §5 那十三列」句後，以 B-087 約定之
**逐字形**補註：

> （本句計數與寫入當時的矩陣列數不符，現況以 data-model §5 該節為準）

## 考慮過的替代案與棄用理由

- **shared.ts 以「視需要」帶入名單**——棄。tasks T001 明令定數；「視需要」＝把授權判定
  推遲到實作期＝授權未發生的修改窗。兩向 diff 已證 rev4 藍本零改動，列入即虛列。
- **locale／app.d.ts 三支不入名單、掛「零新 key」釋義**——棄。該釋義（§III.2）射程是
  **既有授權頁**之資料級 label key；role／menu 頁的授權正是本款才發生，且 `page:` 為顯式
  型樹、`app.d.ts` 型節非補不可 ⇒ 依 ADR 0040 款三先例（page 型節「必需非如需」）逐支明列。
- **島 G 條文隨本刀一併入憲**——棄（brainstorm #15）。一刀一次 Amendment＝rev5 既有範式；
  島 G 的 grant 面本刀零實作、條文先入＝憲法宣告無機器證的行為。行為承載走 ADR 0050。

## 後果

- **硬閘解除點**：本 ADR 轉 accepted 且憲法 bump 落地後，「T002 accepted 前不得動任何
  base-web 既有檔」之硬閘解除（T020／T027／T031 修改型段自此有授權前提；純新增 wrapper／
  typings 依 ADR 0021 款 1 本就不受閘）。
- **島 H 方向性面凍結**（MAJOR 界定照 rev4:ADR 0052 字面）：後續刀拆散序列化域、改「整批拒」
  為部分成功、開放 `route_name`／`menu_type` 可變、拔連動歸檔、回灌復原授權——皆 MAJOR；
  常數（advisory key、上溯上限、形制上限）留活書可調。
- **§III.2 表列數 9 → 10**；新列變異自證照 ADR 0040 後果之形（暫改範圍欄任一路徑為裸措辭
  → fork-delta-lint 須當場紅→還原），於首個動 base-web 的單元順做。
- **B-087 關帳**：款三落地即殘餘②兌現，BACKLOG 刪列（隨 T002 落帳）。
- 本檔為 §V.2 之提案；user 親決後轉 accepted，憲法改動與本檔同一 commit、緊接
  `python3 tools/docs-sync.py generate`。
