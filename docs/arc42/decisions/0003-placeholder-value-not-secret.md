---
id: "0003"
title: 值比對層佔位字面白名單——佔位值非機密（secret-value-guard 射程釐清）
date: 2026-08-04
status: accepted
supersedes: []
superseded_by: []
provenance: "rev5 創世 commit 首暴（值比對層攔 generate-secrets.sh／preflight-secrets.sh 之佔位字面）；user 拍板 2026-08-04"
tags: [governance, lint, secrets]
---

## 背景

secret-value-guard（三層掃描之值比對層）以「機密現值逐字比對 staged 新增行」為判定面——唯一擋得住裸高熵值的層。創世 commit 首暴其射程縫隙：`alert_webhook_url` 的現值＝佔位字面 `https://CHANGE-ME.invalid/alert-webhook-placeholder`（設計上的**公開**字面：`.invalid` TLD＋CHANGE-ME 自述；preflight 以 `PLACEHOLDER_LITERALS` 對它發「未填真值」WARN），而同字面必然存在於產生器與 preflight 源碼——「佔位型機密＋其產生器腳本首次入版／被改動」的組合即結構性誤報。rev4 從未暴露（其 webhook 真值已填、真值不在任何源碼中）。

## 決定

guard 加常數 `PLACEHOLDER_VALUES`（frozenset、逐字全等比對、**不做前綴／樣式放寬**）：現值 ∈ 集合 → 該機密跳過比對並印跳過明細「佔位字面（公開、非機密）」；填真值後（真值∉集合）自動納回比對。`check` 與 `--full-tree` 兩消費點同源共用（`comparable_secrets` 單一判定面）。

**三處同字面雙記帳（改佔位值必同刀齊改）**：①本白名單 ②`deploy/preflight-secrets.py` 之 `PLACEHOLDER_LITERALS`（語意＝提醒未填真值）③guard 自測 `TestPlaceholderSkip._PH`（字面手寫釘死、不引用常數——套套邏輯戒律）。

**突變實證**：拔白名單項→佔位跳過測試翻紅＋live check 對兩腳本重新命中；近似形（差一字元）不豁免測試防樣式放寬。

## 後果

- 佔位值期間該機密零值比對防護——可接受：佔位值公開無密可洩，樣式層（betterleaks）照常在场。
- 新增佔位型機密時，佔位值須入本白名單（同刀三處），否則其產生器腳本改動時 pre-commit 誤攔。
