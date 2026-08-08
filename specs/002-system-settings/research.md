# Research — 002-system-settings（Phase 0）

偵查日 2026-08-08;方法＝rev4 源倉唯讀（`git show origin/rev4-admin-rust-api:…`／
`origin/rev4-admin-base-web:…`）＋rev4 傘狀 repo（`../fork260509-rev4/`）＋rev5 現況
grep。★本檔含 ADR 0019 兩份硬產物：R2 rev4 對應碼清單、R3 rev5 拍板差異點清單。

## R1 web 框架與依賴選型

- **Decision**: axum 0.8.9（沿 rev4 已驗證組合）；ORM＝sea-orm 1.1.20（rev5 已在）；
  casbin 2.20.0＋vendored sea-orm-adapter（rev5 已在，001 隨基線 vendored）。
- **Rationale**: rev4 全棧（router 註冊表／enforce middleware／oneshot 測試形）皆以
  axum 為底、B12 高度參照施工面最小；tower `ServiceExt::oneshot` 支撐免 socket 契約
  測試；版本組合經 rev4 20 刀實戰驗證。
- **Alternatives considered**: actix-web／poem——參照面歸零、全部設計重推，無收益。

**B12 依賴子集**（★下表版本欄已於 T003 進場時回填為**實際落地定案值**；原表列為 rev4
workspace 終態，逐筆雙源對照「rev4 lockfile vs crates.io latest stable」後四筆分歧、
user 2026-08-08 拍板全採 latest stable——CLAUDE.md §6）：

| crate | 落地版本 | 用途 | 備註 |
|---|---|---|---|
| axum | 0.8.9 | HTTP 框架 | 新進；兩源同值 |
| serde | 1.0.229 | derive | 新進；★rev4 為 1.0.228、拍板採 latest |
| serde_json | 1.0.151 | 信封／審計 json | 新進；★rev4 為 1.0.150、拍板採 latest |
| tracing | 0.1.44 | 結構化 log | 新進；兩源同值 |
| tracing-subscriber | 0.3.23 | env-filter＋json | 新進；兩源同值 |
| tower | 0.5.3 | dev-dep（oneshot） | 新進；兩源同值 |
| metrics | 0.24.6 | counter 面 | 新進（R6）；兩源同值 |
| metrics-exporter-prometheus | 0.18.3 | recorder＋render、default off | 新進（R6）；兩源同值 |
| axum-prometheus | 0.10.1 | axum_http_* 三序列 | 新進（R6）；★rev4 為 0.10.0、拍板採 latest |
| jsonschema | 0.49.6 | dev-dep、draft-07 裁判 | 新進（R5）；★rev4 為 0.46.9（0.x minor＝可能破相容）、拍板採 latest；★另設 `default-features = false` |
| tokio 1.52.3／sea-orm 1.1.20／casbin 2.20.0／async-trait 0.1.89 | — | — | rev5 已在 |

★兩筆進場期補記（皆 user 拍板 2026-08-08）：

1. **tokio 的相依解析連帶位移**：manifest 維持 `tokio = "1.52.3"`，而 Cargo.lock 實值為
   **1.53.1**——axum-prometheus 0.10.1 要求 tokio `^1.53`，cargo 遂前進之。雙源對照當時只比
   直接依賴、未算相依解析，故此筆是落地後才現形。拍板：**manifest 維持下界不動、實際值以
   Cargo.lock 為權威**（cargo 的 `"1.52.3"` 語意即 `^1.52.3`＝相容下界，非 exact pin；
   改寫下界等於把下界與當前值混為一談，日後再被頂還要再改一次）。
2. **jsonschema 關 default features**（工程判斷、非 user 拍板面）：default 的 `resolve-http`
   會拖進 reqwest／hyper／aws-lc-rs 整條 HTTP client 鏈（實測 Cargo.lock 由 467 降 441 套件、
   並少一條 aws-lc-sys 的 C 建置），而 R5 的契約裁判只對本機快照
   （`rust-api/server/tests/fixtures/wire-schema.json`）的 definitions 建 validator、無遠端
   `$ref`，該 feature 全程用不到；留著會污染 B-028 的編譯時間量測判讀。

**明確不進**（rev4 有、B12 域外）：jsonwebtoken／redis／argon2／captcha／sha2／hex／
lettre／toml／arc-swap／once_cell／futures-util／xdb。

## R2 rev4 對應碼清單（ADR 0019 要求①；實作單元動工前逐檔先讀）

| rev4（origin/rev4-admin-rust-api） | rev5 對應 | 處置 |
|---|---|---|
| `server/src/main.rs`＋`lib.rs` | 同路徑 | 參照重寫；boot 鏈縮（無 redis／ipgate／mailer／captcha） |
| `server/src/router.rs` | 同 | RouteDef 六欄＋Protection 三態承襲；B12 恰 4 條 route |
| `server/src/state.rs` | 同 | AppState 縮＝db＋enforcer（Arc\<RwLock\>）；JwtConfig 不搬 |
| `server/src/envelope.rs` | 同 | Res 三欄宣告序＋2^53 守衛＋serialize_i64_as_string 承襲；PageRes 不搬（R3-10） |
| `server/src/error.rs` | 同 | 13 碼常量 mod 全列；AppError 變體縮至 B12 六碼（R3-9） |
| `server/src/auth/enforce.rs` | 同 | MODEL_CONF／init_enforcer／enforce_role_path_method／require_policy 承襲；bearer→dev 驗證器（R3-3/4）；denylist／reload 不搬 |
| `server/src/auth/jwt.rs` | 不搬 | auth 刀射程；Claims 欄形（uid 注入）參照 |
| `server/src/handler/system_settings.rs` | 同 | SettingItem／UpdateReq／兩 handler＋mod tests（真 DB oneshot 形）承襲；差異 R3-1/2/5/7 |
| `server/src/model/facade/system_settings.rs` | 同 | find_all／find_by_key／update_by_key／build_update_active_model 純測 seam 承襲；差異 R3-5/6 |
| `server/src/model/facade/sys_user_role.rs` | 同 | roles_of_user（require_policy DB-fresh 消費） |
| `server/src/validation.rs` | 同 | validate＋NUMBER_RANGES（10 鍵全承襲）＋canonical 規則；其他域守門（role_code 等）不搬；未知型改 5000（R3-2） |
| `server/src/config.rs` | 同 | 縮：APP_DATABASE_URL_FILE 讀取；其餘 compose 環境鍵「接而不讀」維持 |
| `server/src/obs.rs` | 同 | recorder＋render＋axum-prometheus layer（R6） |
| `server/tests/health.rs`／`contract.rs`／`wire_schema.rs` | 同 | oneshot 契約形＋case registry 覆蓋閘雙向＋快照裁判承襲縮編 |
| `server/tests/entity_access_lint.rs` | 同 | handler 零 `entity::` 機器強制承襲（工程自拍：防線值高、成本低） |
| rev4 傘狀 `tools/wire-schema.py`（640 行） | rev5 傘狀 `tools/wire-schema.py` | ★rev5 已在版（創世 c5b4d7c 入版、rev5 座標、pre-commit 已接 `--staged-gate`）——本刀僅複核適用性、勿重寫 |
| base-web `src/typings/api/rev4-system-settings.d.ts` | `rev5-settings.d.ts` | 承襲；UpdateReq 加 description 三態（R3-1）。★源倉＝fork260509-soybean-admin-base、分支 origin/rev4-admin-base-web（下同） |
| base-web `src/service/api/rev4-system-settings.ts` | `rev5-settings.ts` | 承襲（直接路徑 import、不經 barrel） |

rev4:004-system-settings 之 SDD 產物（rev4 傘狀 repo specs/ 下）＝設計語境參考；
rev4:ADR 0026（registry）／rev4:ADR 0027（enforce seam）結論已透過實碼消化。

## R3 rev5 拍板差異點清單（ADR 0019 要求②；防回歸條款執行面——參照 rev4 時**不得帶回**下列已推翻行為）

1. **UpdateReq 含 description 三態欄**（Clarify Q1；rev4 僅 `{settingKey, settingValue}`）
   ——B-026 三態約定層具象欄。
2. **庫中未知 setting_type→`5000`**（spec FR-009；rev4 回 2222 invalidValue——把資料完整
   性異常誤報為 user 輸入錯，rev5 拍板改判內部錯誤）。
3. **未認證（無 `Authorization` 標頭）→`8888`**（Clarify Q2；rev4 bearer 缺/壞→3333——
   3333 觸發前端 refresh 重試，B12 無 refresh 機制；auth 刀接真 session 時再對齊 rev4
   3333/8888 語意分工）。
4. **dev-only 測試態 identity（固定 token 查表）取代 JWT 驗章**（Clarify Q2）；uid 注入
   介面沿 rev4 Claims 形、驗證器內部整換。
5. **update 不寫 op-log**（B-016 域外；rev4 `mutate_in_txn` 同 txn 審計不搬）；facade 仍
   顯式成對寫 `updated_at`／`updated_by`（憲法 §I.6）。
6. **讀端 `deleted_at IS NULL` filter**（spec FR-003 防禦性；rev4 find_all 無 filter）。
7. **熱套用 stub 不搬**（rev5 無設定值消費側；行為兌現留對應域刀）。
8. **reload_enforcer／denylist／redis 不搬**（無治理寫端、auth 域外；enforcer boot 一次
   載入即終態）。
9. **AppError 變體集＝B12 六碼**（0000/2222/4040/5003/5000/8888）；1000/3333/7777 與 4
   保留碼**皆無變體**＝構造層不可發出（比 rev4 更強的「本刀零發出」保證；auth 刀進場
   時加變體）。
10. **PageRes 不搬**（B12 無列表分頁端點；留首個列表刀）。
11. **i18n 僅 zh-tw 側**（user 拍板甲案 2026-08-08、ADR 0020：gen.msg_dict 豁免改謂詞
    續留、en-us.ts 零改動；BASE-WEB-I18N-WIRING ★軌道延前端 i18n 接線刀）。
12. **msg key 沿 rev4 既有字面**：`biz.systemSettings.invalidValue`／`biz.systemSettings.notFound`／
    `system.internal`／`system.forbidden`／`system.notFound`／`auth.session.reLogin`／
    `common.success`——zh-tw.ts 起手鍵集＝後端實發集∪Lint24 白名單九鍵（Lint24 閉環、
    data-model §6）。
13. **zh-tw.ts＝無 Schema 標註孤立檔**（釋義 ADR 0021、user 拍板 2026-08-08）：rev4 靠
    ★軌道對 app.d.ts inline（backend 型節＋LangType）並以 `App.I18n.Schema` 標註——
    rev5 **不得帶回**；zh-tw.ts 裸 object export、不接 runtime；標型重構與 runtime
    接線延前端 UI 刀★軌道。

## R4 registry 值域（→data-model §3 凍結）

NUMBER_RANGES 10 鍵逐鍵界＝rev4 終態原值承襲（rev4 經 rev4:004→rev4:015 五刀漸進定界、已驗證）；
enum:on,off 6 鍵值域自含於 setting_type 字面。canonical 規則承襲：number＝`trim`→
`parse::<i64>`→界內→`to_string()`（棄空白／前導零／正號）；enum＝精確成員、原值即 canonical。

## R5 契約機器化管線（K1-25）

- **Decision**: 沿 rev4 三件形——①傘狀 `tools/wire-schema.py`（★已隨 rev5 創世入版、
  本刀僅複核；extract＝base-web 容器內
  npx 抽 typings→draft-07 快照、原子替換寫 `rust-api/server/tests/fixtures/wire-schema.json`；
  check＝重抽 byte 比對 drift 閘＋`--staged-gate` pre-commit 收窄；test＝自帶 unittest）
  ②`server/tests/wire_schema.rs`（jsonschema 0.46.9 dev-dep 對快照 definitions 建
  validator、驗 DTO 序列化輸出）③`server/tests/contract.rs` case registry＋覆蓋閘
  （雙向：ROUTES.case_key vs registered keys，缺 case 紅指名、殭屍 case 紅指名）。
- **Rationale**: 「容器內抽」語意經 rev4 實證＝npx 一次性、不碰 base-web 工作樹、輸出
  確定性 byte 一致；覆蓋閘＝cargo test 形（spec FR-018）。
- **Alternatives considered**: host 直跑 tsc——host 無 node 工具鏈假設不成立（node 住
  base-web 容器）、棄。

## R6 metrics 三件（工程自拍、回報備查）

`rules.yml` ①a `rustapi-down`＝`up{job="rust-api"}` **noDataState: Alerting**——server
起而 `/metrics` 缺＝scrape fail＝告警恆紅，故 `/metrics` 必本刀掛。拍板：recorder＋
render（metrics-exporter-prometheus、default off、/metrics 由 axum route 吐）＋
axum-prometheus layer（axum_http_* 三序列——5xx 比率告警與 rust-api dashboard 即接資料；
成本＝一 layer＋已驗證版本組）。`/health`＝plain text "ok"（★消費面實查更正：
front-nginx healthcheck 打的是 nginx **自答塊**（`_locations.inc` return 200 "ok"、
不轉發）、rust-api 自身 healthcheck＝dev override TCP 探針——/health 端點在本 stack
無 healthcheck 消費者、屬信封例外契約端點，驗收＝dev 直連埠 22079 直打）。

## R11 併發語意複核（spec Assumptions 指派項）

rev4 `update_by_key`＝單鍵原子 UPDATE、無樂觀鎖、last-write-wins（updated_at 非版本欄、
僅審計時戳）；rev5 沿用（16 鍵低頻治理面、單管理者情境）。本刀不驗併發；結論落此、
T031 DoD 記帳。

## R7 測試分層（沿 rev4 實形）

1. **純函式單元測**（免 DB）：validation registry 紅綠矩陣、error 碼映射、
   build_update_active_model 欄映射（now 注入純測 seam）、三態 deserialize。
2. **oneshot 契約測**（免 DB、tests/ crate）：case registry 全 route（未認證 8888 形、
   信封例外形）＋快照裁判＋覆蓋閘＋entity_access_lint。
3. **真 DB integration**（沿 rev4 handler `mod tests` 形）：`Database::connect(db_url)`
   ＋real_app oneshot——授權矩陣（uid 1/2 兩身分×兩端點）、寫端往返、驗證失敗零寫入、
   三態落庫效果。全程容器內 serial（CLAUDE.md 硬禁令）。

## R8 dev-only 測試態 identity 形

- **Decision**: 固定 token 查表 `dev-super`→uid 1／`dev-admin`→uid 2／`dev-user`→uid 3
  （seed 帳號 Super/Admin/User 實 id）；roles **不入表**——沿 require_policy DB-fresh
  `roles_of_user`（授權判定恆走真政策）。驗證器整體掛 `#[cfg(debug_assertions)]`：dev
  容器（cargo run dev profile）＝有效；release 建置＝驗證器缺席、一切請求 8888
  fail-closed（「MUST NOT 存在於非 dev 建置形」的編譯期承載）。
- **Rationale**: 查表零密碼學、auth 刀僅換驗證器內部；debug_assertions＝零新 feature
  flag、機器可證。
- **Alternatives considered**: cargo feature flag——需 compose build args 配合、面大；
  env 開關——runtime 可誤開、非編譯期保證。

## R9 gen.msg_dict 豁免謂詞修改設計（user 拍板甲案、ADR 0020）

解除謂詞自「zh-tw.ts 存在」改為 callable＝「MSG_DICT_LOCALES 兩支皆含頂層 `backend: {`
樹」；DAY1_EXEMPTIONS 該筆註解同步改寫（射程說明＋解除＝前端 i18n 接線刀）；docs-sync
自測隨治理檔變動照跑。Lint24（後端 key⊆zh-tw）不受影響、B12 照常就位。

## R10 K1 承襲盤點對照表（B-001 要求②回填；plan Constitution Check 後）

| K1 | 本刀實際消費 | 機器強制點（「靠人記得」檢核） |
|---|---|---|
| K1-07 路由單檔 | ROUTES const＋build 迭代 | 覆蓋閘迭代 ROUTES＋gen.router 真表重算（豁免下架後 lint 錨定） |
| K1-08 最輕縱切＝系統設定 | 本刀功能域 | —（一次性選型、無殘留紀律） |
| K1-25 wire 契約機器化 | R5 三件 | wire-schema check drift 閘＋coverage gate cargo test＋pre-commit staged-gate |
| K1-26 值型驗證 registry | validation.rs | registry 紅綠矩陣測試＋未宣告鍵 fail-loud |
| K1-27 最小授權骨架 | enforce_mw＋require_policy | contract case（8888／5003 形）＋授權矩陣 integration |

**結論**：五條全消費、四條有機器強制錨（K1-08 屬一次性選型無需錨）——「靠人記得」
面＝零。承襲盤點機器閘（B-001）實需評估＝**低**：K1 用點天然被 lint／測試錨定，建議
B-001 收刀留帳「暫不建閘、維持 brainstorm §2 表人工盤點＋plan 回填」，實作不排。
