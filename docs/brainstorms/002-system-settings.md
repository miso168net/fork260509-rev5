# 002-system-settings — B12 後端首刀 brainstorm（階段 0）

- 日期：2026-08-08｜狀態：設計九節已過 user 核可；下一步＝**手動** `/speckit-specify`（本檔為其 input；不自動觸發——否則 feature branch pre-hook 不跑、spec 落 default）。
- 一句話：立 `rust-api/server` crate，打通「router→授權→handler→registry→DB→wire→前端接線層」整條管線，功能面＝系統設定**讀＋寫**；view UI 不在本刀。

## 1. 三題拍板紀錄（user 拍板 2026-08-08）

| 題 | 拍定 | 要點 |
|---|---|---|
| 功能域 | **沿用 K1-08＝系統設定** | 連帶沿用 K1-27（登入延 auth 刀、本刀立最小授權骨架）。翻案 auth 案已評估並棄：首刀直接扛 B-017（session 一次完整、不可拆兩段）＋B-020（節流 seam）全套設計、B-022 升必答，量級人週以上、首刀風險過高。 |
| 前端腿 | **typings＋service 接線層；view 延 B-008** | 憲法 §III.1 預設軌道（`src/typings/api/` 新檔＋`src/service/api/rev5-*.ts` 新檔）零修憲；manage_system-settings 選單 404 屬已知態持續；詳 ADR 0018。 |
| 寫端 | **含讀＋寫** | K1-26 registry 有真消費者、寫路徑與驗證失敗路徑一併打樣；B-026 三態約定層與 B-024 授權 seam 隨寫端入刀設計期定形（「第一支寫端落地即隱含定死」——在定死前顯式定形）。 |

## 2. K1 承襲盤點（B-001 要求①：本刀消費之 K1 條目與處置紀錄）

| 條目 | 處置 | 本刀消費點 |
|---|---|---|
| K1-07 後端路由單檔＋三源一致 lint | 沿用 | `router.rs` 之 `ROUTES` const（gen.router 豁免解除謂詞＝該檔存在、routes 真表恢復重算） |
| K1-08 縱切第一刀選最輕系統設定 | 沿用 | 本刀功能域本身 |
| K1-25 wire 契約機器化 | 沿用 | 容器內抽 typings→JSON Schema 快照＋coverage gate cargo test 形（詳設計 §3） |
| K1-26 系統設定值型驗證 registry | 沿用 | `registry.rs`（詳設計 §5） |
| K1-27 最小授權骨架、登入延 auth 刀 | 沿用 | `enforce_mw`＋`require_policy`＋測試態 identity（詳設計 §4） |

B-001 要求②＝`/speckit-plan` 跑完 Constitution Check 後回填「本刀實際消費了哪些 K1／有沒有靠人記得」對照表，據此判承襲盤點機器閘的實需（實作若判要做、留 B12 後維護批）。

## 3. 設計（九節、user 已核可）

### §1 目標與範圍

B12＝rev5 第一把功能刀。範圍外（spec 非目標節照抄）：view UI（B-008）、真登入（auth 刀、K1-27）、稽核 log 寫入（B-016；本刀不寫 sys_operation_log／sys_access_log）、列表排序（B-027）、prod 資產（ADR 0014）。預期**零 migration**（system_settings 表＋16 鍵 seed 已隨 001 基線在庫）；clarify 若冒出 DDL → RUNBOOK §10 三步照走（schema-evolution 啟動斷言七條已完備）。

### §2 架構與單元邊界（server crate 內、各單元一責）

- `router.rs`：路由**單檔** `ROUTES` const（K1-07）。
- `enforce_mw`＋`require_policy`：casbin 最小授權骨架（K1-27）；授權判定收斂**單一純函式進入點**＋空 no-escalation 掛點（B-024 seam、不實作）。登入未到位＝dev-only 測試態 identity 頂替（形式於 spec/plan 定；auth 刀再接真 session）。
- `handler/settings.rs`：薄殼——解析→授權→registry 驗證→facade 落庫→envelope 回包。
- `registry.rs`（K1-26）：每值型一 validator、per-key 宣告範圍、number 正規化落庫、未知型 fail-loud 拒收、驗證失敗不寫入；型別集以現庫 16 鍵定形（int-range／enum-switch 兩型起步、可擴）。
- web 框架選型＝工程自拍、隨 `/speckit-plan` research 確認（傾向沿 rev4 選型）；brainstorm 不定死。

### §3 wire 契約

權威＝base-web typings **新檔**（`src/typings/api/rev5-settings.d.ts`；我方新檔＝新增型圈界、不標原行）＋`src/service/api/rev5-settings.ts` 接線。envelope＋13 碼矩陣照憲法 §I.3 凍結面消費、不新增碼面。**B-026 三態約定層本刀定形**（envelope 級：欄位缺席＝不動／顯式清空表示法／設值；清空非法回哪個碼對 13 碼矩陣定）；逐域欄級表留各域刀。K1-25 機器化：容器內抽 typings→`rust-api/server/tests/fixtures/wire-schema.json` 快照、contract test 離線消費、coverage gate＝cargo test 形（每條 route 必有 case、缺即紅）。

### §4 授權面

seed 已保證 R_ADMIN「有鈕（user:edit）無寫端政策」組合必發生——本刀以 **ADR 定死拒絕語意與錯誤明細粒度**（B-024 三件套前置、刀內立）。設定寫端政策僅授 R_SUPER（沿 seed 現況、不動 casbin seed）。

### §5 資料面（B-014 一併收）

sys_user_role 兩條 FK 的 Relation＋Related impl（機械工、不擾動 entity-drift 閘）。兩設計題本刀拍定：①無 DB FK 之邏輯關聯**不建** sea-orm Relation（避免第二套關聯真相；server 端需要即手寫 join）②ActiveModelBehavior **不承載**六審計欄自動化（首刀寫端只碰 system_settings、審計欄由 facade 顯式寫；通用化留下一支寫端刀複評）。

### §6 錯誤處理

registry 拒收／三態非法／授權拒絕各對映 13 碼矩陣既有碼（spec 期逐碼對表）；錯誤路徑一律有 contract case。不寫 log 表（B-019 的 real_ip seam 不觸發）；request_context 只留介面位、信任判定不寫死 handler。

### §7 測試與 DoD

TDD。契約測試 per route＋registry 紅綠（每型別合法／非法／未知型）＋三態語意案＋授權拒絕案；entity-drift 綠、schema-gate 三閘綠；**六業務件 `up -d --wait` 起得齊**＋RUNBOOK §1 已知態註記撤除；三筆 Day-1 豁免拔項（gen.router／lint24.day1／gen.msg_dict 兩表假設對齊一併釐清）。

### §8 起手固定 tasks

①建 `base-web/src/locales/langs/zh-tw.ts`＋接字典生成器＋下架到期豁免（否則 server/src 首支 .rs 的 commit 被 pre-commit 擋）②B-028 量測第一輪（起手態容器內冷編＋單檔增量；server 依賴進場後第二輪；收刀時 B-028 條目改寫留 DDL 半條、勿整列刪）③本檔 K1 盤點節＝B-001 要求①；plan 後回填對照表。

### §9 風險

上游 rebase 撞 typings 新檔機率低（皆 rev5- 前綴新檔）；容器冷編時長未知（B-028 第一輪即答）；三態約定層 YAGNI 邊界＝只定 envelope 級。

## 4. 給 /speckit-specify 的輸入摘要

- feature 名＝`002-system-settings`；user 故事核心＝R_SUPER 經 API 讀取全部系統設定、更新單鍵且值受型別／範圍驗證，非法值與越權寫入被正確拒絕。
- 直接輸入：本檔＋BACKLOG B-014／B-026（三態）／B-024（seam 半條）＋K1 五條（§2 表）。
- 待 clarify 候選：測試態 identity 形式、三態「顯式清空」表示法、單鍵更新 wire 形（PUT／PATCH／POST 擇一）、registry 兩型的 per-key 範圍值域。
