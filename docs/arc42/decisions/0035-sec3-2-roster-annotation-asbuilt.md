---
id: "0035"
title: §III.2 名冊兩處範圍欄註記對齊 as-built（PATCH 校正）
date: 2026-08-11
status: accepted
supersedes: []
superseded_by: []
provenance: "工具面維護批（輕量軌；B-042／B-063／B-065／B-067／B-068／B-069 六筆同批）之 B-068 前置；分歧＝003-auth-session final holistic review 分流時發現（BACKLOG B-068 條目★注）；user 核批批組成時併同核可（2026-08-11）"
tags: [constitution, fork-delta, governance]
---

## 背景

§III.2 名冊（v1.3.0 由 ADR 0028 開立）範圍欄的處數與型別為開立當時的**估值**
（表外宣告 1 明言「處數為估值，實作期以 `rev5-inline` 標記實數為準」）。003-auth-session
實作落地後，兩列註記與 as-built 分歧（grep 實證 2026-08-11）：

1. **`src/typings/app.d.ts`**（I18N-WIRING (iii)）：名冊記「1 處，修改型」；實作為**一對
   START/END 新增型圈界**（`app.d.ts:314`／`:368`、標記帶 `+` 尾綴），檔內零 `原行:` 錨
   ——基線既有行逐字未動。
2. **`src/layouts/modules/global-header/components/user-avatar.vue`**（LOGOUT-UX-WIRING
   (i)）：名冊記「3 處，修改型」；實作為 **1 處修改型**（`:64`、帶 `原行:`）＋
   **2 處新增型**（`:7` import 圈界、`:72` 說明註記，皆明文自述不記修改型錨）。

名冊消費停在軌道裸名層級（現行 fork-delta-lint 僅抽表格首欄）時此分歧無害；B-068 將把
授權判定升為（軌道×用途×檔案）三元組、名冊欄位成為機器判準——「型別」欄不準＝新判定
上線即誤報。故於同批先行校正。

## 決定

1. §III.2 表 I18N-WIRING (iii) 列範圍欄：「（1 處，修改型）」→「（1 塊，新增型圈界）」。
2. §III.2 表 LOGOUT-UX-WIRING (i) 列範圍欄：「（3 處，修改型）」→
   「（1 處修改型＋2 處新增型）」。
3. 授權邊界零變動：檔級名單、用途集、紀律欄一字不動。分級＝PATCH
   （§V.3「文字校正、釐清」）、1.3.0→1.3.1。

## 後果

- B-068 三元組判定可直接以校正後名冊為判準、不誤報。
- 表外宣告 1（處數為估值）與宣告 3（新增型 `NAME+` 不入名冊斷言射程）語意不變：
  app.d.ts 一列自此描述的是新增型標記，其授權承載仍是**檔級名單硬邊界**（宣告 1 後半）
  ——既有檔內純新增行仍須在冊才可動，非修改型斷言射程的事。
- 名冊註記自此以 as-built 為準；日後實數再漂移（新刀動同檔）循同款 PATCH 校正。
