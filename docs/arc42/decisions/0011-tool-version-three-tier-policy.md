---
id: "0011"
title: 外部工具版本三分類政策（一次性輔助工具沿 latest）
date: 2026-08-06
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:0022（alpine/openssl 沿 latest 浮動 tag 之單點豁免）＝本政策前身、本 ADR 升格為通則；拍板脈絡＝age 產鑰容器化路線選擇（2026-08-06、user 明示「非用於本專案 build 或對外被訪問的程式應使用最新版」後經射程掃描收斂邊界）"
tags: [tooling, supply-chain, governance]
---

## 背景

user 對「工具類程式逐支釘版」的維護瑣事（釘值 bump、重下載、斷言改兩處）提出通則化訴求。
但照字面「非 build、非對外＝latest」全掃會波及 betterleaks（bootstrap die 級釘版斷言）與
sops 容器（digest 釘版＝rev4 P1.1 契約字面）——兩者恰是全 repo 釘版理由最硬的：雙機
（WSL2＋macOS）環境下掃描器版本漂移＝同一 commit 在 A 機過閘、B 機被擋；sops 每次機密
操作經手、tag 可被重推而 digest 不可變是 P1.1 立論本身。故收斂為三分類。

## 決定

### 三分類

| 類 | 判準 | 版本策略 | 現役成員 |
|---|---|---|---|
| ① 專案 build／runtime／對外暴露 | 產物進交付面或被外部訪問 | 釘版（完整數字版；容器 digest 尤佳） | postgres／redis／nginx／node／mailpit／觀測層全部、rust:slim＋watchexec |
| ② 機密管線常駐件 | 每次機密操作或每次 commit 經手、版本＝行為＝閘的跨機一致性 | 釘版＋機器斷言（現狀不動） | sops 容器（digest、P1.1）、betterleaks（bootstrap 斷言） |
| ③ 一次性輔助工具 | 低頻單發、產物格式穩定、工具版本與產物壽命脫鉤 | **latest** | alpine/openssl（dev-cert、承 rev4:0022）、age（產鑰、B-038 起） |

### ③ 類的 latest 語意（防「假 latest」）

Dockerfile 內的 `@latest`／浮動 tag 是 **build 當下**的最新，docker 層快取會把它凍住。
故 ③ 類工具**每次使用時 `docker build --pull --no-cache` 重建**（真最新；秒級～分鐘級、
低頻可承受）；離線或限流時退回本地既有映像並印警示、不得靜默。完整性面：go module 走
sumdb 校驗、apk 走 alpine 官方庫簽章——latest 不等於免驗。

### 分類異動程序

- 新工具入冊時先按判準歸類、歸類寫進引入該工具的 ADR 或 BACKLOG 條目。
- 跨類移動（例：某 ③ 類工具開始每次操作經手）＝拍板級、立新 ADR。
- age 自 RUNBOOK §12 機密工具鏈釘版表（v1.3.1）移出改歸 ③——表列改寫與
  `AGE_VERSION` 釘版斷言拆除由 B-038 承載、非本 ADR 即刻生效面。

## 後果

- 兌現 user 訴求的同時保住兩道最硬的釘版：①②類完全不動、零契約翻案。
- B-038（age 容器化）為 ③ 類新政策首例；generate-dev-cert 免改（rev4:0022 先例即此形）。
- ③ 類工具的版本不再出現在任何釘版斷言中——「最新版是多少」不落字面、不產生同步義務。
