---
findings_total: 27
scope: 005-role-menu-crud final holistic review（三 lens 並行：spec 總符合性／跨單元整合品質／文檔帳面一致性）
run: wf_4f12039f（3 agent、opus xhigh ultrathink、只讀）
date: 2026-08-22
---

# 005 收刀 final holistic review——findings 三分流結果

嚴重度分布：blocker 1／major 11／minor 15。三 lens 總評皆「無收刀阻斷級碼缺陷」；
blocker 為活書計數失真（文檔）。逐筆處置如下（編號＝run 輸出序）。

## 修（15 筆、本輪已落）

| # | 摘要 | 處置 |
|---|---|---|
| 1 | 活書 §5 facade「十支」實 11、守衛「八件」實 12 | §5 改寫：11 支＋sys_casbin_archive 構件句、12 件＋005 四守衛（自證測 7 支機器數） |
| 7 | reload rebuild-swap 跨端點無序列化——併發亂序可令已歸檔 p 列於判定面復活、無自癒 | `enforce.rs` 補 `RELOAD_SERIAL` mutex（rebuild＋swap 含重試全程互斥、鎖序恆 serial→write 無環）＋doc 序列化段＋退化守測 `reload_concurrent_calls_serialize_and_complete`（死鎖即逾時紅）；交錯時序 harness 缺口誠實立 B-105 |
| 4 | 活書 §8 MANAGE-PAGE-WIRING 缺用途 (ii) as-built | 條目補 (ii)（8 檔定數名單＋兩 modal 零 diff 斷言＋殘留移除） |
| 9 | 憲法指名「常數留活書」零落點＋機制 as-built 缺 | 三常數（advisory key／上溯 64／形制 100）＋鎖序＋歸檔面落 §5 構件句；§6 Runtime 擴充留 B-083（滿載、user 拍） |
| 6/18 | spec:235「3333 家族」句失真（B-096 觸發已到） | spec 句改寫 as-built（json_or_default 收斂、零 3333）＋B-096 關帳刪列；errata 複核其餘 42 處＝002/003 正確用法不動 |
| 12(碼註半)/13 | enforce.rs doc 表「連動歸檔恆發生」同誤 | doc 表三列改「成功且有連動歸檔」＋釘「勿回帶」句；ADR 半＝B-104 |
| 14/15 | role.rs「空冊」殘句兩處 | 改「名冊閘（本檔不入冊）」 |
| 16 | role.rs「九鍵」五處未隨第十鍵同步 | 五處改十鍵（歷史敘述句保留） |
| 20 | authz lint doc「現況空集…T026 屆時轉綠」失真 | 改現況恰一檔＋刪已完成預告句 |
| 17/26 | roleHome as-shipped 零 UI 消費者、spec 無已知態專條 | spec Edge Cases 補專條（同構 getAllRoles 形；UI 隨授權治理刀 modal 接真進場） |
| 21 | wire-menu-admin §4「出現變更」措辭鬆於 as-built | 改「出現即拒（值不比對）」對齊 role 側 |
| 22 | wire-menu-admin §6 缺空陣列語意、碼註引用落空 | §6 補空陣列提前 no-op 句 |
| 23 | brainstorm「AuditOperation 擴詞彙」errata 漏網 | 改「詞彙定案〔T005 as-built〕」 |
| 24 | tasks T027 補記 components.d.ts「+1 行」實 +2 | 訂正（L-048 同型誤數） |
| 25 | tasks T012「三件」漏 UserCleanup 第四件 | 補 as-built 記（U7 帶進、雙腿＋兩自證測） |
| 27 | spec FR-041＋clarify「menu 2~3 檔視需要」 | 收窄定數恰 2 檔（Amendment 已判） |

## 轉 B-NNN／帳面處置（5 筆）

| # | 摘要 | 處置 |
|---|---|---|
| 2+3 | B-095 原敘述失真（主路徑已被 T024-fix 關）＋殘餘窗＝軟刪常量後代繞道五步 | B-095 整條改寫（兩 finding 合併）；仍拍板級→finishing 前 user 拍 |
| 5+8 | components.d.ts 改動在憲法用途(ii) 名單外、機器閘結構性失明 | 拍板級→finishing 前 user 拍（追認形式） |
| 10 | B-094/B-101「收刀前維護窗」已到未執行 | 改期至授權治理刀起手維護批（final review 後不開中型重構 diff、主線拍回報備查） |
| 12(ADR 半) | ADR 0049 §2 括號句出生即誤 | B-104 立案（body 不可變、as-built 以 FR-039 為準＝B-008 先例形；訂正窗＝島 G 入憲） |
| 7(harness 半) | 序列化交錯時序無行為證 | B-105 立案（fail-point harness 候選） |

## won't-fix／記錄（1 筆）

| # | 摘要 | 理由 |
|---|---|---|
| 19 | require_policy 讀鎖不變式退化訊號＝掛死非紅 | doc 已逐字自陳＋U10 起三支端到端測實走該路徑（退化＝該三測逾時紅）＝已有間接機器訊號；結構無感面屬 tokio RwLock 本性、無低成本改善 |

## 驗證

- 碼修後容器 serial 全量連兩輪 649 passed／0 failed（首輪 6 failed＝U16 CDP 真登入 redis
  殘態、TTL 自癒——L-050 場景再現、失敗名單再度未截）；schema-gate 三閘綠。
- 文檔修後 docs-sync check 僅餘 STATE 滯後（⑤generate 例行）。
