---
id: "0021"
title: §III ★軌道授權射程釋義——base-web 純新增檔不需軌道、zh-tw.ts 治理錨點孤立檔
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "B12 /speckit-analyze X1（wf_0069f58c-6d0 憲法面 CRITICAL）、user 拍板 2026-08-08（甲案）；背景＝ADR 0018（零修憲）＋ADR 0020（en-us 零改動）＋啟動書 Day-1⑦跨端契約閘"
tags: [governance, constitution, frontend, i18n, scope]
---

## 背景

憲法 §III.1 列三條預設可動軌道（.env*／typings 新檔／service rev5-* 新檔）、§III.2 稱
「★軌道＝base-web inline 的顯式授權邊界」——「純新增檔（不在三軌道射程、亦零 inline）」
落在兩節字面縫隙。B12 治理契約（啟動書 Day-1⑦＋MSG_DICT_LOCALES 常量＋Lint24）自創世
錨定 `base-web/src/locales/langs/zh-tw.ts` 路徑必須存在；但實查 rev5 base-web 的
`App.I18n.Schema`（app.d.ts）無 backend 節、LangType 僅 en-US/zh-CN，rev4 同名檔是靠
★軌道 BASE-WEB-I18N-WIRING 對 app.d.ts 做 inline（加 backend 型節＋LangType 改行）並以
Schema 標註才成立——rev5 零★軌道、照 rev4 藍本落地即撞修憲需求。

## 決定

1. **射程釋義**：§III.2 ★軌道授權射程＝**inline（改動 base-web 既有檔）**；base-web
   純新增檔不觸★軌道，依 §III fork-delta 新增型紀律（檔頭一行 `[rev5-inline …+]` 標記、
   標記註明治理依據）即可落地。§III.1 三軌道表＝常用新增面之預設清單、非新增面之
   窮舉排除。
2. **zh-tw.ts＝治理錨點孤立檔**：裸 object export、**無 `App.I18n.Schema` 標註**、不
   import 進 runtime locale 系統；唯一消費者＝傘狀治理工具文本解析（Lint24 契約閘＋
   gen.msg_dict 謂詞）。
3. **rev5 差異點登記**（ADR 0019 防回歸；research R3 第 13 筆）：rev4 之「標 Schema＋
   app.d.ts inline」不得帶回；runtime 接線（app.d.ts backend 型節＋LangType＋locale
   註冊）與 zh-tw.ts 標型重構，延前端 UI 刀與 view ★軌道同批 Amendment 開齊。

## 後果

- B12 零修憲；app.d.ts 等 upstream 熱檔零 fork-delta（rebase 衝突面不擴）。
- zh-tw.ts 鍵樹在 TS 層無 Schema 保護（打錯鍵名 typecheck 不攔）——機器防線＝Lint24
  （後端實發集⊆字典＋白名單九鍵存在性斷言、缺鍵孤兒鍵皆紅）；vue-tsc 全量 typecheck
  （T011／T031 驗收）兜住語法層。
- 前端 UI 刀開★軌道時，本檔第 2 款之孤立形轉為過渡態、由該刀 Amendment 收編重構。
