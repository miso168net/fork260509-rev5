---
id: "0046"
title: dev compose 信任模型路徑改 YAML anchor 同源＋long-form volume——消抄本、分岔物理上不可能
date: 2026-08-18
status: accepted
supersedes: []
superseded_by: []
provenance: "B-086（004 收刀後盤點立案）；治理工具鏈整併批 grilling Q1／Q5 拍板（2026-08-17）；修法落地＝治理工具鏈整併批之 U2（批分支名＝maint- 前綴串接五條 B 編號、字面不入本檔——子串會被 Lint25 誤讀為跨代刀名形）"
tags: [compose, dev-stack, trust-model, governance]
---

## 背景

`docker-compose.dev.yml` 的 rust-api service 有兩處必須逐字一致的同一字面：
environment 之 `APP_TRUST_MODEL_PATH` 的值，與 dev 信任模型 volume 的容器內掛載目標
（`/etc/rev5/trust-model.toml`）。改法前它們是**兩份獨立抄本**，一致性只靠掛載行上方
一行註解（「路徑與上方 APP_TRUST_MODEL_PATH 必須一致」）＋人眼。

★失效表徵是**軟降級、不是紅**：兩處一旦分岔，`config.rs` 讀不到檔即走「無法讀取信任模型檔
…：退扁平環境變數」那條退路——不擋啟動、不影響健康檢查，dev stack 照樣起得來、照樣服務，
只是信任模型整份不生效；訊號只有 boot 時的結構化 WARN（`main.rs` 對每筆降級 warning 落
「信任模型設定降級」）與一次 `ip_domain_degraded_total{kind="trust_model_load"}` 計數，
quickstart 走查未必抓得到（走查發的鏈多半在兩種設定下同判）。

## 決定

**用 YAML anchor 讓兩處引同一個值**：env 行定義 `&trust_target`（anchor 定義先於引用、
現行 service 內序已滿足），volume 改 long-form（`type: bind`／`source:`／
`target: *trust_target`／`read_only: true`）引用之——短形 `host:container:ro` 是單一
字串字面、塞不進 anchor 引用，long-form 是能讓 target 獨立成節點的唯一寫法。
自此兩處同源，分岔**物理上不可能**（YAML 解析層保證，不靠任何對賬工具）。

★**風格特例、刻意為之**：這是全檔唯一的 long-form volume（其餘皆短形）。不一致是
代價，換的是「抄本消滅」這個更高階的一致性；且形制差異本身就是標記——讀者見 long-form
即知此處有 anchor 引用、有本 ADR。

## 考慮過的替代案

- **docs-sync 對賬條款**（「compose 內 `APP_TRUST_MODEL_PATH` 的值 == 同 service 某
  volume 的掛載目標」、B-086 原候選①）：不採。兩個家加一道對賬，比不上一個家——對賬
  只把「分岔」從靜默變成紅，anchor 讓分岔根本寫不出來；且新條款有 Lint22 名冊範圍
  字串連鎖與永久維護成本，為一對字面開一條條款不成比例。

## 後果

- 該對字面自此單一來源：改掛載路徑只動 env 行一處，volume target 隨 anchor 自動跟進。
- compose 掛載行註解改指本 ADR（原「必須一致」人眼提醒句功成身退）。
- 日後 prod compose 掛載信任模型時，**須沿同形**（anchor 同源），勿退回兩份抄本。
