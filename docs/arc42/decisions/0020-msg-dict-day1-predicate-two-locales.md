---
id: "0020"
title: gen.msg_dict Day-1 豁免改謂詞續留——en-us 接線延前端 i18n 刀
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "B12 plan 期 user 拍板（2026-08-08、甲案）；背景＝002-system-settings spec FR-026③「gen.msg_dict 兩表假設對齊釐清」＋B12 偵查（tmp/backlog-recon-before-b12.md §4.1）"
tags: [governance, lint, i18n, scope]
---

## 背景

gen.msg_dict Day-1 豁免的解除謂詞＝「zh-tw.ts 存在」，但字典生成器
（compute_msg_dict_rows）硬讀 MSG_DICT_LOCALES 兩語（zh-tw.ts＋en-us.ts）、缺頂層
`backend:` 樹即 raise、兩語鍵集不等即紅（缺譯即紅）。B12 起手必建 zh-tw.ts（Lint24
硬相依），建檔即謂詞成立、豁免到期下架，而 upstream 原樣 en-us.ts 無 backend 樹
→generate 整支中止——兩表假設不一致、B12 內必收。給 en-us.ts 插 backend 段＝動
upstream 既有檔＝需第一個 ★軌道 Amendment（承 rev4 BASE-WEB-I18N-WIRING）。

## 決定

**甲案——修謂詞續留豁免**：gen.msg_dict 解除謂詞自「zh-tw.ts 存在」改為「MSG_DICT_LOCALES
兩支皆含頂層 `backend:` 樹」（callable 形）；DAY1_EXEMPTIONS 該筆註解同步改寫（解除時點
＝前端 i18n 接線刀）。en-us.ts 零改動、零修憲。Lint24（後端 msg key ⊆ zh-tw.ts 鍵集）
不受影響、B12 照常就位——跨端契約閘不空窗。

## 後果

- B12 期間後端 msg key 僅維護 zh-tw 一處（如 `biz.systemSettings.invalidValue`＝
  「設定值不合法」）；en 譯文缺席——現階段零消費者（無 UI、書面產物全 zh-TW）。
- msg-dict 真表兩產出檔（backend-msg-dict.md＋grafana panel）與兩語鍵集斷言（缺譯即紅）
  延至前端 i18n 接線刀；該刀同批修憲開 BASE-WEB-I18N-WIRING ★軌道（範圍含 en-us.ts
  backend 段插入）更聚合。
- base-web 既有檔 fork-delta 面維持零（upstream rebase 衝突面不擴）。
- 若前端 i18n 刀提前需要 en 譯文，翻案＝該刀 Amendment 一併收、本 ADR 不擋。
