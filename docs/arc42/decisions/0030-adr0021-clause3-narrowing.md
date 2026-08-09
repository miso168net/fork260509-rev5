---
id: "0030"
title: ADR 0021 §3 射程收窄——app.d.ts backend 型節本刀提前，LangType／locale 註冊／zh-tw.ts 標型重構仍延後
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 T003②；收窄對象＝ADR 0021 決定 §3；授權面＝ADR 0028 開立之 ★BASE-WEB-I18N-WIRING (iii)；先例＝ADR 0025（釋義型 ADR、不走 supersedes）"
tags: [base-web, i18n, adr-narrowing, fork-delta]
---

## 背景

ADR 0021 決定 §3 把三項 runtime 接線**打包**延後：

> rev4 之「標 Schema＋app.d.ts inline」不得帶回；runtime 接線（app.d.ts backend 型節＋LangType＋
> locale 註冊）與 zh-tw.ts 標型重構，延前端 UI 刀與 view ★軌道同批 Amendment 開齊。

003-auth-session 的 R2 甲案要求後端 msg 在前端顯人話（而非裸 key）。其機器面契約是硬的：
`docs-sync` 的 `gen.msg_dict` 謂詞要求兩語鍵集相等，而 `App.I18n.Schema` 若不補 `backend` **必填**
型節，`pnpm typecheck` 就攔不住「某一語系少一鍵」——三檔任缺一鍵都靜默通過。三項打包裡，**只有
`app.d.ts` 這一項是本刀交付的機器守所必需**，另外兩項（LangType 擴充、locale 註冊）純屬前端 UI 面。

## 決定

1. **只提前一項**：`src/typings/app.d.ts` 的 `App.I18n.Schema` 補 `backend` 必填型節，走 ADR 0028
   開立的 `★BASE-WEB-I18N-WIRING (iii)` 軌道用途。
2. **兩項仍延後、一字不動**：LangType 擴充與 locale 註冊，仍依 ADR 0021 §3 原文延前端 UI 刀。
3. **zh-tw.ts 標型重構仍延後**：ADR 0021 §2「zh-tw.ts＝治理錨點孤立檔（裸 object export、無
   `App.I18n.Schema` 標註、不 import 進 runtime locale 系統）」**全效不動**。本刀對 zh-tw.ts 的動作
   僅止於補鍵（Lint24 同步律要求），不加型標註、不接進 runtime。
4. **本 ADR 不使用 `supersedes`**，理由見後果第一項。

## 後果

- **為何不走 `supersedes`**：ADR 0021 的 §1（★軌道射程＝inline、純新增檔不觸軌道）與 §2（zh-tw.ts
  治理錨點孤立檔）**全效不動**，被收窄的只有 §3 三項中的一項。而 `docs-sync` 的 Lint08 對非空
  `supersedes` 會強制被指向的 ADR 轉 `superseded` 狀態——那會讓 §1§2 在索引上讀起來像一併失效，
  是不實陳述。故以射程收窄 ADR 承載（沿 ADR 0025 之釋義型先例；本 repo 至今零真翻案）。
- ADR 0021 §3 自此**讀作**：「三項中 `app.d.ts` backend 型節已於 ADR 0030 提前，其餘兩項與
  zh-tw.ts 標型重構仍延後」。前端 UI 刀開齊剩餘面時再立新 ADR。
- **代價已知並入帳**：`app.d.ts` 是基線近 12 月最熱的檔之一（15 個 commit），本刀提前吃下該 rebase
  衝突面，正是 ADR 0021 當初顧慮的事。處置＝rebase 時先比對 upstream 是否已自行改動 `Schema` 結構，
  若是則改為**對齊而非疊加**（ADR 0028 後果段同款）。
- 三項打包被拆開這件事本身是教訓：**延後決策若把技術相依不同的項目綁成一包，後續刀就得為了其中一項
  付整包的拍板成本**。日後寫延後條款宜逐項列，不宜打包。
