---
id: "0006"
title: schema 基線＝rev4 終態壓平＋user 定稿制（波 0、m001／m002 兩支基線遷移）
date: 2026-08-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:0014（schema 基線壓平先例）＋rev4:0021（定稿制方法論）；rev4 終態快照＝rev4@2b8a101 docs/ops/reference-src/schema-snapshot.json；brainstorm 001 §0／§5 拍板＋clarify seed 定稿 user 總簽核 2026-08-05"
tags: [schema, migration, baseline, finalize]
---

## 背景

rev5 為 rev4 治理終態之重跑（ADR 0001），資料庫面臨同一選擇：逐支搬 rev4 的十五支
migration（含其全部歷史 delta），或以終態壓平為新基線。rev4 自身即以「壓平＋定稿制」
起家（rev4:0014＋rev4:0021）且全代驗證良好；憲法 §I.5 拷貝例外（ADR 0001 決定 3）已
承載「資料形狀是契約不是碼」——schema 與 migration 允許以 rev4 終態為藍本壓平。
brainstorm 001 三題拍板＋欄序親排工作坊（user 逐表親排、2026-08-05 總確認）與 clarify
seed 全量過目（user 總簽核 2026-08-05）完成了定稿制的全部輸入。

## 決定

1. **基線＝rev4 終態壓平為兩支**：`m001_baseline_schema`（15 表結構＋索引 38／約束 101
   ＋pg_trgm＋casbin_rule 委派建表）＋`m002_baseline_seeds`（266 列 seed、完全決定性）。
   rev4 的 rev4:m003～rev4:m015 為其後續刀 delta、淨效果已含於終態——不搬；rev5 第一支後續 delta
   自 m003 起編（短編號紀律承 K1-13）。
2. **定稿制（「定稿即基線」）**：欄序 user 逐表親排＋更名開放（rename map 4 組、全在
   sys_operation_log 去 operator_ 前綴）＋seed 全量過目（零未過目列進基線）。定稿權威
   鏈＝brainstorm 001 §5 → 轉錄 `specs/001-schema-baseline/data-model.md` 凍結後以
   data-model 為唯一權威、brainstorm 轉史料。
3. **授權偏離集**（對 rev4 終態的全部偏離＝data-model §4，此外零支）：rename map 4 組
   ＋sys_operation_log.region 新增＋trace_id 改 text＋real_ip 全庫一律 NN＋帶時戳預設
   統一 `now()`（DB 以 UTC+0 運行）。血緣核對（vs rev4 快照）逐項 normalize 後全等。
4. **seed 完全決定性**（clarify Q1 甲案）：明示 id／明示定稿時戳
   `2026-08-05T00:00:00+00:00`／password＝argon2 PHC 定稿常數（無 runtime 雜湊、
   不引 argon2）／protected 逐列明示／收尾 setval 對齊 sequence 落值；內容唯一來源＝
   `seed-decision.json`（機器轉錄、禁手抄）。

## 後果

- 後續一切功能刀建立在單一權威 schema 起點；pristine 重放與凍結 fixtures 逐列全等
  （SC-001）、比對器零豁免洞。
- rev4 已推翻之形不得帶回（data-model §4＋§10 防回歸：operator_ 前綴、trace_id
  varchar(64)、seed 簡體原值、runtime 隨機雜湊〔§10〕；CURRENT_TIMESTAMP 預設〔§4
  追補拍板、統一 now()〕）。
- reaper DB role＋GRANTs（rev4:m012／rev4:m013）不入基線——屬 observability 域運維工件、
  隨該域刀重進場（research R4）。
- 基線翻案＝新刀新 ADR（supersedes 本檔）；fixtures 凍結後永不改寫。
