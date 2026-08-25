---
id: "0060"
title: menu 治理清單的分頁列改「凍結」而非抽除或接真——UI 位置不動、頁碼 1／每頁 0／整列上鎖，itemCount 必須讓位給 pageCount
date: 2026-08-25
status: accepted
supersedes: []
superseded_by: []
provenance: "B-097（005-role-menu-crud U11 碼品質審查輪查定、與 B-030 首項同一事兩處記帳）；2026-08-25 主線 CDP 實測後提題、user 親決同日（選「凍結」形並逐項給定規格）；落地＝維護批 maint-b097"
tags: [frontend, ux, pagination, backlog-disposition]
---

## 背景

menu 管理頁的**治理清單**模式走 `fetchGetMenuList()` **無參** ⇒ 後端 `size` 預設 100
（`handler/menu.rs` 逐字：「rev4 as-built 無參形＝一次取全樹——treeTable 前端無參呼叫」），
而 `useNaivePaginatedTable` 的 `onFetched` 又把回應的 `pageSize` 寫回分頁狀態
（`hooks/common/table.ts`：`pagination.pageSize = data.pageSize`）。

**2026-08-25 CDP 實測**（頂層 11 列、seed 基線）：

| | 改前 治理清單 | 改前 回收桶 |
|---|---|---|
| 每頁下拉顯示 | **100**（不在 `pageSizes [10,15,20,25,30]` 內） | 100（同一殘留值） |
| 改每頁筆數 | **被回彈、零效果** | 生效 |

★條目原標題稱「頂層列數 >100 才成真缺陷」**不準確**：「換頁不換資料」確實要 >100 列才碰得到
（11 列時只有 1 頁、前後鍵 disabled），但「下拉顯示一個不在選項內的值、且改了完全沒反應」
**今天就可見**。同頁的回收桶模式已於 005 接真分頁 ⇒ 同一頁兩種模式行為不一致。

## 決定

治理清單模式**凍結**分頁列，不抽除、不接真（user 親決 2026-08-25 並逐項給定規格）：
**UI 位置不動**（三段俱在）、**頁碼顯示 1**、**每頁數量顯示 0**、**整列 `disabled`**；
prefix 續顯真實筆數。回收桶模式**一行不動**（保持已接真的可操作分頁）。

實測驗收：治理清單渲染 `共 11 条 ⎢ 1 ⎢ 0`，分頁器與每頁選擇器皆 disabled、點下拉零選項，
11 列照常全渲染；回收桶模式仍可操作。

## 理由

1. **不接真分頁**：切頁會打斷樹的完整性（後端 `paginate_top_level` 切的是頂層節點、子樹整棵
   跟著父節點走 ⇒ 第 2 頁只剩幾個孤立頂層節點），且「治理清單維持無參一次取全樹形」是 005
   期的既有拍板（`menu/index.vue` 碼註逐字），翻它需要理由而非順手。
2. **不抽除**：抽掉分頁列會讓版面在兩種模式間跳動；凍結保住版面穩定，且「灰掉的分頁列」本身
   就是「此清單不分頁」的可見訊號。
3. **★`itemCount` 必須讓位給 `pageCount`（技術硬約束、非風格選擇）**：naive-ui 的
   `mergedPageCountRef` 讓 `itemCount` 優先（`Pagination.mjs` 註解逐字「item count has high
   priority, for it can affect prefix slot rendering」）⇒ 保留 `itemCount` 而設 `pageSize: 0`
   會算出 `pageCount = Math.ceil(11 / 0) = Infinity`，而 `createPageItemsInfo` 的 `rightSplit`
   分支據此呼叫 `createRange(8, Infinity)`＝`for (i=8; i<=Infinity; ++i)`（`showQuickJumpDropdown`
   預設 `true`）。**2026-08-25 實證：POC 頁面當場卡死、CDP 腳本逾時零輸出** ⇒ 那不是凍結分頁列、
   是凍死瀏覽器。故實作走 `itemCount: undefined` ＋ `pageCount: 1` ＋自備 `prefix`。
   ★連帶：`itemCount` 與 `pageSize` **至多一個能是 0**（`0/0 = NaN` 同樣越出安全區）。

## 後果

- B-097 關帳；**B-030 首項「未刪選單列表分頁」同步出列**（兩處記帳同一事，本刀一併清）。
- 授權面：`views/manage/menu/index.vue` 在憲法 §III.2 用途 (ii) 的**檔級名單**內（硬邊界），
  本次屬該用途「列表」接真的**補完**（B-097 正是 005 接真時回收桶接真、治理清單維持無參所留的
  殘餘），非新能力 ⇒ 不需 Amendment。修改型兩處皆帶 `原行:`，模板側沿既有 multiline 註解紀律
  （singleline 形會被 eslint `vue/html-comment-content-newline` 的 fix 併行、令行尾錨定失真）。
- ★**殘餘一（本 ADR 射程外、另立 B-131）**：頂層若真的長到 >100 列，後端 clamp 會截斷，而凍結後
  使用者看到「共 N 条」卻只有 100 列且**無從翻頁**。★改前同樣不可達（api 無參、換頁不重取），
  凍結只是把「假裝可翻」變成「明示不可翻」——**未使之惡化，但也未解決**。
- ★**殘餘二（既有、另立 B-132）**：`onFetched` 寫回的 100 會經 `onPaginationParamsChange` 洩漏進
  `deletedSearchParams` ⇒ 回收桶初始顯示每頁 100。改前兩模式同顯 100 而不可見，改後落差外顯。
- ★翻案觸發器：頂層列數逼近 100，或決定改走真分頁 ⇒ 立新 ADR `supersedes: ["0060"]`。
