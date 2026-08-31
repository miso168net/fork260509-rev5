---
id: "0076"
title: audit 頁三分頁渲染 x_forwarded_for 欄——UI 對照 rev4 之唯一例外＋B-072 對帳關單形
date: 2026-09-01
status: accepted
supersedes: []
superseded_by: []
provenance: "008-audit-settings-pages brainstorm（docs/brainstorms/008-audit-settings-pages.md）；user 親決 2026-08-31（AskUserQuestion 三選一、取「rev5 加渲染該欄」非建議項）、整體設計核可 2026-09-01；背景帳＝BACKLOG B-072；盤點實測＝rev4 audit 頁不渲染該欄（DTO 有、四表 columns 無、整頁零 v-html）"
tags: [scope, frontend, security, ui-parity, audit]
---

## 背景

B-072 記載：`x_forwarded_for` 為 client 可控之不可信原文（建構點淨化僅「rightmost 判定窗＋
零 CR/LF＋≤1024 字元」、不剝 HTML），渲染端轉義＝XSS 級義務、「帳面隨稽核 UI 刀」；其觸發器
寫「稽核管理列表首次渲染該欄時（B-008 audit 頁）」。但 008 brainstorm 盤點實測：**rev4 的
audit 頁根本不渲染該欄**——B-072 的前提與 rev4 實況不符。而 rev5 既定原則＝UI 須與 rev4 一致
（CDP 對照驗收、CLAUDE.md §7）。兩者不可同時成立，需拍板：照 rev4 不渲染（B-072 觸發器永不
成立）或偏離 rev4 加渲染（對上 B-072 原始期待）。

## 決定

1. **audit 頁 operation／access／login 三分頁渲染 `xForwardedFor` 欄**（`session_event` 無此欄、
   第四分頁不渲染）——B-072 義務射程三表一致兌現。
2. 渲染形＝**純文字插值**（Vue 文字節點；view-render-guard 7 條禁字面＋管理頁純文字慣例雙防線
   常駐）＋ **ellipsis＋tooltip**（欄值最長 1024 字元原文、不撐爆表格）；scroll-x＝Σ欄寬不變式
   隨新欄同批改。
3. 此為 UI 對照 rev4 的**唯一例外**：CDP 三方對照驗收以本 ADR 為例外註記之承載、該欄差異＝
   已知差異非回歸。
4. **偏離最小化**：其餘 DTO 有而 rev4 不渲染的欄（`peerIp`／`ipConfidence`）維持不渲染；
   不隨之新增任何其他欄。
5. **B-072 關單形**＝「渲染＋轉義就位」對帳關單（隨 008 刀收刀）；非 won't-fix。

## 後果

- audit 頁該三分頁與 rev4 畫面不一致（多一欄），對照驗收須引本 ADR 註記；其餘欄集逐欄照 rev4。
- 若日後要回 rev4 形（拿掉該欄）＝翻案新 ADR supersede 本檔，且 B-072 之渲染義務帳隨之重開
  ——不得以普通改碼移除。
- 該欄為不可信原文上畫面之首例：轉義依 Vue 文字節點語意＋view-render-guard 機器守；任何人
  日後把該欄改為原始 HTML 插值即撞 pre-commit 紅。
- access 分頁在 `access_log_mw` 落地（B-016 射程）前為空表，該欄實際首見資料＝operation／
  login 兩分頁。
