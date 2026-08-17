---
promoted_to: rust-api/server/src/handler/system_settings.rs 之三態混形矩陣測試（rustdoc 自任 L-009 守門人）
---
- **L-009**｜serde 對 `Option<Option<T>>` 的**預設** Deserialize 不承載三態：欄位值為 JSON `null`
  時，它與「欄位缺席」一樣落外層 `None`，兩者不可辨——三態就地塌成兩態。親歷：002-system-settings
  T021 寫端，ADR 0023 明定三態承載型為 `Option<Option<T>>` ＋ `#[serde(default)]`，照該字面實作後
  TDD 測試紅在「顯式 null 須為 `Some(None)`，實得 `None`」。★諷刺處＝ADR 0023 立案的理由正是
  「前代的 null 語意含混」，而照其條款字面實作仍會得到含混的結果。成因：`#[serde(default)]` 只處理
  「欄位缺席」，欄位存在而值為 null 時走的是 `Option<Option<T>>` 的 Deserialize，外層 Option 會把
  null 吃成 None。防法：①三態欄必須配 `deserialize_with` 自訂函式——欄位出現時先以 `Option<T>` 收
  再包一層 `Some`，缺席才由 default 給 `None`；②照 ADR／設計文件的「型別字面」實作後，必須以
  三形（缺席／null／值）各一案的測試自證，★不可假設型別本身承載了語意；③後續寫端刀照抄承載型時
  必須連該 helper 一起帶，否則同一個坑會逐刀重演。

