---
id: "0004"
title: host 埠配號 2xxxx 世代制——翻案啟動書 5xxxx 錯開表（避開 macOS ephemeral 範圍）
date: 2026-08-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:0019（前代配號制母版：世代首碼＋well-known 尾碼）；翻案對象＝啟動書 docs/brainstorms/000-doc-architecture.md §4.5.9 錯開表之 5xxxx 拍板值（B10 已落地）"
tags: [deploy, ports]
---

## 背景

host 埠配號沿世代慣例：rev3＝3xxxx→rev4＝4xxxx（rev4:0019 定制：世代首碼＋well-known 尾碼）。rev5 啟動書 §4.5.9 錯開表拍板 5xxxx 並已於 B10 落地 compose 三檔。落地後暴露一問題，為翻案唯一動機；另附一配套確認條件：

1. **翻案動機——macOS ephemeral port 衝突**：5xxxx 全數落 macOS ephemeral port 範圍 **49152–65535**——OS 隨機分配瞬態出向連線埠於此段，任一瞬態連線恰佔我方配號埠即致 `docker compose up` 機率性 bind 失敗，且故障不可重現、難以歸因。
2. **配套確認條件（非動機）——世代區隔維持**：rev4（4xxxx）與 rev5 stack 須在同機並行比對；三代互不重疊此一需求 5xxxx 本已滿足，改配號時新段位仍須維持與 rev3（3xxxx）、rev4（4xxxx）互不重疊——此為新值的選擇約束，不構成翻案理由。

## 決定

**host 埠首碼 5→2、尾碼一律不動**（20 值對照＝舊 5xxxx 同尾碼形逐一映射至：22078～22089、22443、23000、23100、25432、26379、28025、29090、29091；舊值即各新值首碼改回 5，不在本文重列——殘留掃描零字面）。理由二：

- (a) rev4＋rev5 stack 並行比對之世代區隔（配套確認條件、非翻案動機）：rev5＝2xxxx，與 rev4（4xxxx）、rev3（3xxxx）三代互不重疊。
- (b) 2xxxx 完全避開 macOS ephemeral port 範圍 49152–65535，根除瞬態出向連線佔埠致機率性 bind 失敗。

配套紀律（承 rev4:0019 制、於 rev5 續行）：

- **尾碼不動**：尾碼＝服務 well-known 語意（80/443/5432/6379/8025/9090/9091/3000/3100…映射位），首碼純世代碼。
- **容器內側 port 照官方預設**：配號只動 host 側，容器內側一律官方預設值。
- **ports 真表**＝`docs/generated/reference/ports.md`（機器生成、generate 自 compose 三檔重算），本 ADR 不做鏡像表。
- **後續動埠照 errata 紀律**（`python3 tools/docs-sync.py errata <埠>`）機器枚舉全 repo 同語意命中、逐處處置。

## 後果

- compose 兩檔（dev／example）、RUNBOOK §14 字面埠、tools/docs-sync.py 之配號紀律指涉同刀跟正；`generate` 重算 ports.md 為 2xxxx。
- rev5 無 0019 號 ADR——編號不過境：前代判例一律以 `rev4:0019` 前綴形引用，裸「ADR 0019」在 rev5 repo 內＝違規指涉。
- 啟動書 §4.5.9 之 5xxxx 拍板值自此作廢；啟動書屬創世史料不回改，翻案以本 ADR 為正式載體。
