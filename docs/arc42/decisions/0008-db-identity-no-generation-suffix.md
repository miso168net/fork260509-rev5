---
id: "0008"
title: DB 身分不帶世代後綴（soybean／soybean_admin_rust；世代錯開射程＝host 共享面）
date: 2026-08-06
status: accepted
supersedes: []
superseded_by: []
provenance: "user 裁決 2026-08-06（001-schema-baseline 單元④ 期間）；推翻啟動書 docs/brainstorms/000-doc-architecture.md「rev5 同機並存必須錯開的項目」清單第 3 條（該條未經逐條拍板即由 b10 96e76c7 施工落地）"
tags: [db, identity, secrets, compose, generation]
---

## 背景

b10 compose 移植批（`96e76c7`）依啟動書「rev5 同機並存必須錯開的項目」清單施工，其中
第 3 條把 DB 身分改為 `soybean_rev5`／`soybean_admin_rust_rev5`。該條 user 並未逐條
拍板；且 rev3→rev4 世代升級時亦無此慣例（rev4 沿用無後綴身分）。001 刀 SDD 與
deploy secrets 修復（B-009）沿引為既定、擴散至 15 檔後，user 於 2026-08-06 發現並裁決。

技術事實：compose project name 改 `rev5-admin` 後 named volume 已全隔離，DB 帳號／庫名
在**容器內**、與 rev4 stack 零衝突面——「必須錯開」不成立；世代錯開的正當射程僅限
**host 宿主機共享面**（project name／host ports／volume 前綴／network 名）。secrets
需要分代的是**存放目錄**（SECRETS_DIR＝`~/.cache/fork260509-rev5/secrets`、`.env` 既定），
不是容器內連線身分。

## 決定

1. **DB 身分無世代後綴**：`POSTGRES_USER=soybean`／`POSTGRES_DB=soybean_admin_rust`，
   DSN composite 同形；對齊 rev3→rev4 慣例。
2. **世代錯開射程界定**：host 共享面（project name／ports／volume／network）＝必須錯開；
   容器內身分（DB user／DB name）＝不錯開；secrets 世代隔離＝SECRETS_DIR 目錄承載。
3. 啟動書該條之後引用以本 ADR 為準（brainstorm 屬史料、不回改）。

## 後果

- 字面回滾 ×15 檔面：compose 三檔、deploy 四檔（generate-secrets／preflight-secrets／
  secrets README／setup-reaper-role）＋grafana alerting datname、tools 兩支（schema-gate
  ／docs-sync 連線常數）、SDD 件勘誤（plan／research）。
- dev stack postgres volume 以新身分重建重放（m001＋m002）；composite 由 leaf 重組。
- 001 刀凍結 fixtures 重產一次（seed.sql 之 pg_dump `Owner:` 註解行連動；schema／seed
  資料內容位元零變）——重產授權＝本 ADR、provenance.md 載明原因。
- 程序教訓：勘誤必逐處處置（errata 機器枚舉）；「移植清單照單施工」不等於「已拍板」——
  拍板級條目（schema／身分／user 可見行為）施工前應逐條確認。
