---
id: "0023"
title: 部分更新三態約定（B-026 envelope 級定形）——缺席不動／JSON null 清空／有值設值
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "002-system-settings Clarify Q1（user 拍板 2026-08-08）＋spec FR-011／FR-012＋data-model §8＋tasks T025；user 於 U1 執行期間確認本檔為條文轉錄、無新決策空間，並拍定加一句射程釐清；背景＝BACKLOG B-026「部分更新契約的通用顯式 clear 語意於 wire 契約設計期一次定形」"
tags: [wire, convention, api]
---

## 背景

B-026 明定「部分更新的三態（欄位缺席／清空／設值）必須在 wire 契約設計期一次定形」，理由是
前代付過代價：rev4 的 `null` 語意是「整欄跳過」，「清回 NULL」沒有通用語意，只有 user 域以
空字串部分兌現——結果每個寫端各自解釋，前端也各自猜。

002-system-settings 是 rev5 第一支寫端，也就是這個定形的時點。若不在此定死，第一支寫端的
實作方式就會隱含定死全 repo 後續所有寫端的部分更新行為。

本 ADR 的內容係 Clarify Q1 拍板與 data-model §8 條文的**轉錄**，非新決策——立為 ADR 是為了
補齊憲法 §V.1 權威鏈的落點：全 repo 後續寫端要引用的權威應該是 accepted ADR，而不是某一把刀
的 design 產物。

## 決定

部分更新請求的**每一個可選欄**，語意恰為三態（RFC 7386 JSON Merge Patch 語意）：

| 請求中的形 | 語意 |
|---|---|
| 欄位缺席 | 不動——保持庫中原值 |
| 欄位值為 JSON `null` | 顯式清空 |
| 欄位有值 | 設值 |

補充條款：

1. **NOT NULL 欄收到顯式 `null`** → 業務驗證拒收（`2222`、HTTP 200 信封）；
   **nullable 欄收到顯式 `null`** → 落 NULL。
2. **解析層必須以三態型別區分「未出現」與「null」**——serde 的
   `Option<Option<T>>` ＋ `#[serde(default)]` 慣例：外層 `None`＝缺席、`Some(None)`＝顯式
   null、`Some(Some(v))`＝設值。★用單層 `Option<T>` 表達不了三態，那正是前代語意含混的根源。
3. **逐域欄級三態表由各域刀自定**；本約定只鎖 envelope 級語意，不預先枚舉任何域的欄。
4. **★射程釐清**（本 ADR 相對 data-model §8 唯一的新增句、user 2026-08-08 確認）：
   本約定的射程＝**部分更新（partial update）請求的 body**。
   新增（create）請求之缺席欄語意、以及 query 參數的三態語意**不在射程**，由各域刀自定。
   立此句是為了避免後續寫端刀重問同一題；若日後要把 create 語意也一併鎖，那是新拍板、走新 ADR。

## 後果

- 002-system-settings 的寫端即為本約定的第一個具象：`UpdateSystemSettingReq` 的
  `description` 為 nullable 欄、三態俱全；`settingValue` 為 NOT NULL 欄，顯式 `null` 走 `2222`
  拒收路徑（非落庫路徑）——四案各有契約測試（SC-005）。
- wire 契約的機器面：typings 是 wire 唯一權威（憲法 §I.3），三態於其中以「可缺席且可為 null」
  表達；contract 快照能忠實呈現 nullability（抽取管線帶 `--strictNullChecks`），故 rust 側裁判
  可直接以快照斷言三態、毋須手工豁免。
- data-model §8 自本 ADR accepted 起轉為指引，權威以本檔為準。
- 後續每一支寫端刀不必重新討論三態語意，只需宣告自己域內哪些欄是可選、哪些是 NOT NULL。
- 若日後判定某域需要與本約定相異的部分更新語意（例如 PATCH 與 PUT 分流），翻案＝新 ADR
  supersede 本檔，並須說明為何該域不能沿用通用約定。
