---
id: "0005"
title: 憲法 §I.2 demo menu 條例外與釋義——toggle-auth 示範鏈三角色初始勾選＋hideInMenu 射程
date: 2026-08-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4 終態 seed（casbin_rule 4 列＋sys_menu hide_in_menu 6 列、001 刀 clarify 定稿 user 簽核 2026-08-05）；動機＝001 刀 /speckit-analyze findings D1（CRITICAL）與 D2"
tags: [constitution, casbin, menu, seed]
---

## 背景

§I.2（v1.0.0）凍結「demo view 全部進 `sys_menu` seed、**初始僅勾給 `R_SUPER`**」與
「`hideInMenu`／頁面排除等前端隱藏機制**皆不啟用**」。001-schema-baseline 之 seed 定稿
（rev4 終態壓平、user 全量過目簽核）與此有兩處張力，/speckit-analyze 對抗覆核確認：

1. **D1（CRITICAL）**：casbin_rule 4 列把 demo view 的 menu 政策授予非 R_SUPER 角色——
   `function`→R_ADMIN（id 47）／R_USER_COMMON（id 48）、`function_toggle-auth`→R_ADMIN
   （id 50）／R_USER_COMMON（id 51）。此非疏漏：toggle-auth 頁的存在目的＝示範三種角色
   看到不同按鈕（B_CODE1/2/3），單勾 R_SUPER 即喪失示範語意；rev4 全代即此形。
   惟 seed 過目簽核**不具修憲效力**（§V.2＝ADR＋user 親決＋版本 bump），plan Q3 以簽核
   照收判過＝程序缺口，須以本 Amendment 補正。
2. **D2**：seed 有 6 列 `hide_in_menu=true`（upstream route meta 原樣：detail 頁不進
   選單、hide-child 示範等語意），與「皆不啟用」字面有張力；「值原樣入 seed ≠ 啟用
   隱藏治理」的釋義先前只存在 plan 表格單元格內、未入凍結條文。

## 決定（user 親決 2026-08-05；§V.3 MINOR、v1.0.0→v1.1.0）

§I.2 demo menu 條增「例外與釋義」二款：

1. **toggle-auth 示範鏈例外**：`function`／`function_toggle-auth` 對 `R_ADMIN`／
   `R_USER_COMMON` 之 menu 政策初始勾選**保留**（恰 4 列＝casbin_rule seed id
   47／48／50／51）——示範語意所需、承 rev4 終態。其餘 demo view 維持「初始僅勾給
   R_SUPER」不變。
2. **hideInMenu「不啟用」射程釐清**：禁止的是「以 hideInMenu 作 demo 可見性治理手段」；
   upstream route meta 自帶之 `hide_in_menu` 值照原樣入 seed、不視為啟用隱藏機制。
   白名單恰 6 列（sys_menu seed id｜route_name）：6｜manage_user-detail、16｜user-center、
   22｜function_multi-tab、58｜function_hide-child_one、59｜function_hide-child_three、
   60｜function_hide-child_two。

## 後果

- 憲法 v1.1.0（§I.2 增二款、Amendment log 補記）；本 ADR 與憲法改動同 commit（§V.2-4）。
- 已簽核 seed 定稿（seed-decision.json）**一列不動**；T012 fixtures 凍結可如期進行。
- plan.md Constitution Check Q3 依據回填本 ADR 編號（取代「簽核照收」語）。
- 001 刀原規劃之兩支 ADR 讓號後移：基線定稿制＝0006、閘契約演進帳＝0007
  （tasks/plan 同步改；編號永不回收）。
- 初始勾選集之機器覆蓋毋需新閘：gate2 seed 面對 casbin_rule 全表逐列全等比對、
  4 列例外即在比對面內。
