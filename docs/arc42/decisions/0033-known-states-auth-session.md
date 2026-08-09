---
id: "0033"
title: 003-auth-session 已知態集五項（by-design／排程錨，非缺陷）
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 T003⑤；素材＝research R5 降級矩陣末三列、spec Assumptions 與 §7、BACKLOG B-053；立 ADR 之依據＝CLAUDE.md §4「won't-fix／by-design 也立 ADR」"
tags: [known-state, by-design, security, scheduling]
---

## 背景

本刀交付面上有五項「知道、刻意不處理、且不處理是有理由的」狀態。它們既不是缺陷（不進 LESSONS）、
也不是待辦（其中三項另有 BACKLOG 條目承載排程），而是**需要被指名記錄的已知態**——否則下一輪 review
會把它們當新發現重報一次，或更糟：有人「順手修掉」而不知道為什麼當初留著。

## 決定

以下五項記為 by-design／排程錨，本刀不處置：

**① 快速登入鈕暴露 dev seed 帳密**
upstream `pwd-login.vue` 內建三顆快速登入鈕，按下即以明文帳密登入。dev 便利性高（quickstart §1
的三帳號走查直接用它），但**轉 prod 前必須拆除**。射程：僅 dev。本刀 Phase 8 於 BACKLOG 登記並綁
prod 硬化刀。

**② redis 不開 AOF**
RDB 回捲窗內 denylist 鍵可丟。**暴險受憲法 §I.7 島 C「`sys_token.status` 即權威」封頂**：最壞後果是
已撤 token 在回捲窗內短暫仍被快取判為未撤，而下一次退 PG 的查詢即定案。開 AOF 的寫入放大成本，
與這個已被封頂的暴險不成比例。

**③ alova 第二棧在 release build 非 dormant**
base-web fork 原版帶 alova demo 頁，release build 不會把該棧 tree-shake 掉。屬 upstream 既有面、
不在本刀射程；本刀既不擴大也不縮小它。

**④ `/auth/error` demo 端點失效**
本刀 16 條 ROUTES 不含該端點，兩張 demo 頁（`views/function/request/index.vue`／
`views/alova/request/index.vue`）的按鈕會得 `4040`＋`system.notFound`。依憲法 §I.1「v1 從簡只能是
交付排程、不能簡化設計範圍」走排程錨。★**兌現有前置衝突、不是工期問題**：該端點契約是回吐 client
任意 `code` 與 `msg`，而 demo 字面含保留碼 `9999`（「後端從不發出」由三處錨釘死）、`msg` 又是已在地化
人話（違 §I.3「msg 載穩定 i18n key」、並破 msg-dict 的 13＋9＝22 算術）⇒ 須先走 §I.3 Amendment
決「保留碼是否開特例」與「msg 是否開 echo 通道」。已登 B-053。

**⑤ `.env*` 在 fork-delta-lint 射程外**
該工具只掃 `src/*.{ts,vue}`，且 `#` 註解形不被認。故本刀對 `.env`／`.env.test`／`.env.prod` 的四行
ADAPT 改動，其 `原行:` 標記是**人工紀律＋review 把關、無機器守**。這是本刀唯一一處「有標記紀律但
機器不強制」的面，明文揭露而非假裝有守。本刀 Phase 8 於 BACKLOG 登記「lint 射程擴 `.env*`＋`build/`
（含 `#` 註解前綴支援）」。

## 後果

- 五項自此有指名出處。下一輪 review 若重報，回指本 ADR 即可；要翻案（例如決定開 AOF、或決定本刀就
  把快速登入鈕拆掉）則立新 ADR，不默改。
- ②與④的**風險封頂論證是 load-bearing 的**：②靠「status 即權威」、④靠「§I.3 凍結面未被繞過」。
  若日後任一前提鬆動（例如有人讓 denylist 成為唯一權威、或 `/auth/error` 被以其他形式兌現），
  對應的已知態就不再成立、須重新評估——這正是把論證寫進 ADR 而非只寫「已知態」三個字的原因。
- ⑤是本刀機器守覆蓋率的**誠實缺口**，不是疏漏：`fork-delta-lint` 的軌道名名冊斷言（FR-030）覆蓋
  `src/` 下的修改型標記，`.env*` 不在其中。收刀時該缺口仍在，靠 BACKLOG 承載而非靠遺忘。
