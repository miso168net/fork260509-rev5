---
id: "0054"
title: 結構性封死——治理面受保護端點政策 MUST NOT 授予非 R_SUPER（島 G6 設計全文、掛點恰兩處、非 vacuous 自證、B-024① 歸宿與 no-escalation 翻案觸發條款）
date: 2026-08-23
status: accepted
supersedes: []
superseded_by: []
provenance: "006-authz-governance 之 T003（tasks.md Phase 1 主線任務）；拍板鏈＝docs/brainstorms/006-authz-governance.md §3（B-024① 授權模型深度＝結構性封死、2026-08-18）＋§10 Q1（獨立 G6）／Q2（謂詞不寫列數）／Q8（v2='menu' 四列不擴、列已知態）／Q17（B-024 改記殘餘）／Q22（B-075 不建靜態守恆）（2026-08-22 user 逐題親決）；spec FR-023～FR-027；條文落點＝ADR 0053 款一 G6；承重前提＝ADR 0050 §4（三不變式與翻案觸發條款）；no-escalation seam 形＝ADR 0022 決定 3／4；純 key 受眾邊界＝ADR 0022 決定 2；rev3 唯一先例指針＝rev3:rust-api commit 3bfab71（只給指針、三缺陷三詞見 FR-027）；零 rev4 藍本（rev4 無授予側守門、research R2 #6 從零設計）"
tags: [authz, casbin, governance, constitution-island-g, security]
---

## 背景

rev5 的授權面自 002 起以 seed 政策列之 `protected=TRUE` 標記「治理面端點只有 R_SUPER 可持有」
（B12 之 system-settings 起、005 之 role／menu 寫端、本刀之三維授權與回收桶皆然），而
**授予側**至今零守門：005 的 casbin 寫面只有移除面（連動歸檔），沒有任何 grant 端點；一旦
本刀上 updateRoleEndpoints，R_SUPER 在端點 modal 裡把 `POST /systemManage/updateRoleEndpoints`
勾給 R_ADMIN 就是一次點擊的事——此後 R_ADMIN 可再授自己任何端點＝**授權面的提權鏈**。
rev4 同樣沒有授予側守門（research R2 #6）；rev3 曾做過一次 no-escalation 真邏輯（rev3:rust-api
commit `3bfab71`、唯一先例）但帶三缺陷：①靜默壓縮授權（超出自身權限的項被默默剔除、回應
看似成功）②漏 restorePolicy 路徑③TOCTOU（pre-read 判定、寫入時不重驗）。B-024① 把「授權
模型深度」列為多層管理員前置三件套之一；brainstorm 拍板＝**不做真 no-escalation、做結構性
封死**：規則只有一條、謂詞式、資料庫態鎖內現查，把「受保護端點政策永遠只屬 R_SUPER」從
seed 慣例升為不變式（島 G6 入憲＝ADR 0053 款一）。

## 決定

### 1. 不變式（謂詞式、不寫列數）

集合 **P**＝`{(v1,v2) | ptype='p' ∧ protected=TRUE ∧ v2 ∈ HTTP 動詞}` 之現役政策列
（資料庫態、鎖內現查、單次 SELECT）；任何寫端 MUST NOT 使 `role_code ≠ R_SUPER` 的角色持有
P 中任一 `(v1,v2)`。**不寫列數**：P 隨 seed 演化（刀 B 之 seed 68 `updateUserSessionPolicy`
上線即自動入 P——謂詞式封死下「未上線期間自動受保護」正是 Q19 歸刀 B 的前提）；量測值
以 ADR 0047 (c) 形記於此：2026-08-23 自 seed 定稿數得端點維 protected 列 15（GET 8／POST 7）、
`v2='menu'` protected 列 4、`v2='button'` 0。HTTP 動詞白名單由 `HttpMethod::as_str()` 導出
（與 ROUTES 同源、非手寫第二份）。

### 2. 掛點恰兩處（雙路徑、同一守門 fn）

| 掛點 | 位置 | 時序 |
|---|---|---|
| updateRoleEndpoints | `facade/sys_casbin_policy.rs::set_role_endpoints` 鎖內 | 角色列 `FOR UPDATE` 後、protected 整批拒之後、任何寫之前：`role_code ≠ R_SUPER ∧ to_grant ∩ P ≠ ∅` ⇒ `Rejected`（blocked 記封死項、永不上 wire）、rollback、零歸檔、零稽核、零 reload |
| restorePolicy 第③腿 | `facade/sys_casbin_archive.rs::restore` 鎖內 | 鎖歸檔列→①reason gate→鎖活角色列→②同實例→**③封死**（同一 `protected_endpoint_set` fn）→④端點在冊→⑤停用不擋（全文＝ADR 0055） |

★**為何只兩處**：現役授權的「新增」路徑在 rev5 恰兩條（grant 面三維寫端之端點維、回收桶復原）；
選單維／按鈕維寫端的標的 `v2∈{menu,button}` 依定義不在 P（見 §4）；deleteRole／deleteMenu
只做撤銷；roleHome 不寫 casbin。守門 fn 單點（`protected_endpoint_set(conn)`）、兩掛點引同一支
——「漏一路」（rev3 缺陷②）結構上無從發生；日後任何第三條新增路徑進場＝MUST 掛同一 fn、
並更新本表（憲法 G6「掛點恰為…」句隨之 Amendment）。

### 3. 固定序與拒因

端點維寫端守門固定序（spec FR-011／data-model §3.1）：角色查無→`biz.role.notFound`；候選外項
orphan skip（靜默略過、回應 `effective` 不含）；撤銷集含 protected→`biz.role.protectedRevoke`
（G2、整批拒）；**新授集 ∩ P ≠ ∅ 且角色非 R_SUPER→`biz.role.protectedGrant`**（G6、整批拒）；
通過→archive-move＋INSERT＋稽核→commit→reload。兩拒因皆 `2222`＋純 i18n key、零攜參
（blocked 清單只供 tracing 與測試斷言）——**不靜默壓縮授權**（rev3 缺陷①的反面：要嘛全做、
要嘛整批拒且說得出是哪一類原因）。R_SUPER 自授 P 中端點＝通（無人可封死超管）。

### 4. 射程外＝`v2='menu'` 之 protected 列（已知態、Q8）

四列 protected 選單政策（2026-08-23 時）不入 P：可見性可授（R_ADMIN 可被授予看見該選單項）、
端點仍 `5003`（該頁面的 API 全在 P 內）——「看得到、點不動」為已知態、非缺陷；擴射程＝把
選單可見性也綁死在 R_SUPER、與 H4「治理域／顯示域分層」的立意相違。`v2='button'` 現無
protected 列、同理不入。

### 5. 非 vacuous＋變異自證（採 ADR 0024 精神、不主張屬其射程）

守門**非 vacuous**：R_SUPER 在端點 modal 真做得出「把受保護端點勾給 R_ADMIN」（候選集＝
ROUTES Policy 全集、含 P），封死腿是唯一擋它的東西。機器證＝T018 三案（非 R_SUPER 授 P 中端點
→`Rejected` 零變更零歸檔零 reload／R_SUPER 自授通／非 P 端點通）＋固定序（protected 整批拒
先於封死）＋SC-006（歸檔表中 protected=TRUE 原值之列恆零）；★**變異自證**（T019）：拆掉
謂詞守門 → T018 紅 → 還原 → 綠，三次結果寫進 report 與 commit message。★本守門是**業務
不變式的執行點**、不是 ADR 0024 射程內的「守門機制（lint／閘）」——採其精神（落地當下破壞性
驗證一次）但不主張屬其射程、不進該 ADR 的樣板清單。B-075（靜態守恆）不建（Q22）：runtime
謂詞是唯一真源，再建靜態字面集＝第二套同源字面、兩者漂移即假綠。

### 6. 承重前提（FR-026；鬆綁即觸發 ADR 0050 §4 翻案條款）

- 撤銷歸檔列原值恆 `protected=false`：protected 列進不了歸檔表——G2 整批拒擋手動撤銷、seeded
  守門擋連動歸檔路（deleteRole 對 seed 角色）、grant 恆寫 `protected=false`、un-protect 永不
  UI 化。SC-006 機器斷言釘此事實。
- 005 的「歸檔表不加 `protected` 快照欄」零 migration 拍板（ADR 0050 §4 第 2 項）以上述為前提；
  本 ADR 的封死使 restore 路徑也不可能把 P 中端點回灌給非超管。任一處鬆綁（引入 role restore、
  把 protected 政策掛上非 seeded 角色、un-protect UI 化）＝ADR 0050 §4 翻案條款觸發、該刀
  MUST 自帶 protected 快照欄並復核。

### 7. 翻案觸發條款（真要多層管理員時）

當產品需求出現「R_ADMIN 可把**自己持有的**子集授予下級角色、但不得超出自身」（多層管理員／
委派治理），結構性封死（非超管一律不得持有 P）即不敷用——屆時由翻案刀立新 ADR supersede
本檔、把 ADR 0022 決定 3 之 `no_escalation_check` 空 seam 填入真邏輯（上限檢查＝「授予集 ⊆
操作者現役集」、鎖內重驗、整批拒、含 restorePolicy 路徑——三缺陷逐一反面），並把掛點前移到
取讀鎖之前（ADR 0022 後果末條）。在那之前 seam 維持恆放行、**不填**；本 ADR 與 G6 條文是
該翻案的 MAJOR 閘（G6「反轉＝MAJOR」）。

### 8. B-024 三件套重評

①授權模型深度＝本 ADR（封死＋上述翻案觸發條款）；②seeded 護欄三套既有（SEEDED_ROLE_IDS
／SUPER_ROLE_CODE／R_SUPER 恆禁停用——ADR 0050 §3）、本刀零新增；③業務錯誤明細受眾邊界
＝**維持純 key**（ADR 0022 決定 2 不翻案）：封死拒因 `biz.role.protectedGrant` 不揭露是哪幾條
被擋——向確定無權者描述授權模型等於送權限地圖，且 R_SUPER 自己在 UI 上本就看得到哪些
項帶鎖（三支讀端回應帶 `protected` 旗標、protected 項 disabled——Q12）。B-024 條目改記殘餘
（Q17）：只剩「no-escalation seam 填入後掛點前移（翻案刀承接）」一句。

## 考慮過的替代案與棄用理由

- **真 no-escalation（授予集 ⊆ 操作者現役集）**——棄（brainstorm §3）。rev5 現況只有一層治理者
（R_SUPER）、無委派需求；真邏輯需 body 通道（`require_policy` middleware 跑在 body 解析前、
ADR 0022 第 3 款簽章無 body——B-024 勘查補記①）＝改判定進入點簽章；且 rev3 先例三缺陷證明
這條路易錯。封死一條規則、零簽章變更、零新 i18n 模型。
- **封死條文寫列數（15 列）**——棄（Q2、ADR 0047）。列數是活量。
- **擴射程到 `v2='menu'` 四列**——棄（Q8）。見 §4。
- **靜態守恆（B-075：測試斷言 seed 之 protected 端點集＝常數字面）**——棄（Q22）。runtime
謂詞唯一真源。
- **只掛 updateRoleEndpoints、restorePolicy 靠 reason gate 兜底**——棄。歸檔列 `endpoint_revoke`
可復原、其 `(v1,v2)` 可能於歸檔後被 seed 演進標為 protected（或 restore 目標角色非原角色——
同實例腿已擋，但縱深不靠單腿）；rev3 缺陷②正是漏復原路徑。雙路徑同一 fn 成本≈零。

## 後果

- 島 G6 條文（ADR 0053 款一）之設計全文與掛點表＝本檔；新增第三條現役授權新增路徑＝MUST
  掛同一守門 fn＋更新 §2 表＋憲法 G6 Amendment。
- T015 預留鉤位、T018／T019 落地；`biz.role.protectedGrant` 四處 i18n 同 commit（Lint24）；
  wire 不帶 blocked 明細。
- B-024 改記殘餘（T036 落帳）；B-075 維持不入；ADR 0022 決定 2／3／4 皆不翻案、seam 續空。
- 翻案路徑明確：多層管理員需求出現時 supersede 本檔、填 seam、MAJOR Amendment 翻 G6。
