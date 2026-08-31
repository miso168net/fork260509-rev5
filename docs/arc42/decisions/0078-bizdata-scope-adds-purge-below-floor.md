---
id: "0078"
title: BizData 明細通道射程加第三鍵 biz.audit.purgeBelowFloor{minDays}——補充 ADR 0064 射程表、非翻案
date: 2026-09-01
status: accepted
supersedes: []
superseded_by: []
provenance: "008-audit-settings-pages 之 T002（tasks.md Phase 1 U0、spec FR-G01 之 U0 第三產物）；實質拍板＝docs/brainstorms/008-audit-settings-pages.md §1b grilling 拍板③（2026-09-01 user 親決、第三攜參鍵＋Lint24 擴腿）；形式承載鏈＝plan.md Post-design 複核＋research.md D4；被補充對象＝ADR 0064 決定一射程表；rev4 藍本＝rev4:B-047 攜參形六鍵集之 `biz.audit.purgeBelowFloor` 原形（ADR 0064 決定一對照段已列）；轉 accepted 時點＝T003 親決後之 T004（與 ADR 0077 同批）"
tags: [wire, error, audit, governance]
---

## 背景

ADR 0064 決定一把 `AppError::BizData` 明細通道的射程逐字定為**恰二鍵**（
`biz.user.passwordPolicy` 攜 `{violations}`／`biz.user.pwdSetTooFrequent` 攜
`{remainingSeconds}`、各有唯一組裝點於 `handler/user.rs`），其餘一切拒因恆純 key 零
payload；並於決定二立下受眾邊界判準，逐字：

> 明細所描述的，是**操作者自己剛送出的那份輸入**的評估結果，還是**系統的授權模型**？

前者放行、後者不放行；決定三末句同時預留了擴充協定，逐字：

> 射程若要擴到第三鍵：回本 ADR 走第二節判準，**不是**在某支 handler 裡多寫一顆
> `AppError::BizData`。

本刀（008-audit-settings-pages）的 purge 端點依 rev4 藍本回拒因
`biz.audit.purgeBelowFloor`（保留天數低於下限），其明細＝下限值 `{minDays}`——前端譯文
以 `{minDays}` 插值渲染可讀拒因（spec FR-C02；該刀 spec 之 User Story 3 驗收條 1）。此鍵不攜參即退化為「被拒但
不知道下限是多少」的亂猜重試形（grilling 拍板③已棄之選項＝把 30 寫死譯文，屬雙源字面
漂移形）。故本刀須走 ADR 0064 自留的擴充協定：立本 ADR、正面回答決定二判準。

實質拍板已於 brainstorm grilling 拍板③由 user 親決（2026-09-01、第三攜參鍵成立＋Lint24
擴腿隨刀）；本檔為其**形式承載**（research D4、plan Post-design 複核、spec FR-G01 之
U0 第三產物），T003 一併核可後隨 ADR 0077 同批轉 accepted。

## 決定

### 一、射程表擴一列——第三攜參鍵如下

| 拒因鍵 | payload | 組裝點 | 消費端點 |
|---|---|---|---|
| `biz.audit.purgeBelowFloor` | `{minDays: 30}`（值＝`PURGE_MIN_DAYS`） | `handler/audit.rs` purge 守門（本刀 T014 落地、恰一構造點） | purgeAuditLog |

擴列後射程現況全表＝ADR 0064 決定一之二列 ∪ 本列，**恰三鍵**；其餘一切拒因（含 `5003`、
含 `biz.audit.invalidTable`）恆純 key 零 payload 之原則不變。★同刀之另一拒因
`biz.audit.invalidTable` **刻意不攜參**：值域外的 table 字面是操作者送出的原文回聲、對他
零修正價值（四值白名單成員展示屬前端表單層），照 ADR 0064 原則走純 key。

### 二、判準論證——`purgeBelowFloor{minDays}` 通過 ADR 0064 決定二（本 ADR 論證核心）

**被評估物＝操作者自陳輸入**：明細描述的是「你剛送出的保留天數，低於下限」——被評估的是
操作者自己填的那個數字，不是系統的授權模型。這與 `passwordPolicy{violations}` 同構：
violations 揭露「你的密碼違反了政策哪幾條」（政策規則身分被揭露、ADR 0064 明文放行，理由
＝「不告訴他違反哪條，他只能亂猜重試」）；`minDays` 揭露「你違反的那條規則的門檻值」——
同為設密面／清理面**靜態守門規則**對操作者輸入的評估結果，且是他自行修正輸入（改填 ≥30）
的唯一依據。

**資訊來源歸屬檢核**（ADR 0064 的真判準是來源歸屬、不是「像不像冷卻」）：`minDays` 的值
是碼內常數 `PURGE_MIN_DAYS`——**靜態設定、非系統活狀態**。對照 ADR 0064 對
`changePasswordThrottled` 走純 key 的理由：節流案的剩餘秒數是**桶的當前狀態**、下發即給
猜測者一個可查詢的預言機；`PURGE_MIN_DAYS` 恆為同一值、重複查詢零增量資訊，不構成預言機。
它也不含授權內情：不揭露誰有權、缺哪條政策、政策表任何列。

**混合體檢核**（ADR 0064 後果段：兩者都沾取純 key）：payload 恰一鍵 `minDays`、值恆為
靜態下限——零系統活狀態成分、零授權模型成分，非混合體。

**受眾旁證**（非判準本體、僅降風險佐證）：`purgeAuditLog` 為 casbin endpoint 維
**seed 預設**僅授 `R_SUPER` 之端點，無權者在進到守門前即得 `5003` 純 key——故 **seed 預設下**
收到本明細者為超管。★但該政策列之 `protected` 欄為 **FALSE**
（`rust-api/migration/src/m002_baseline_seeds.rs` 之 `/systemManage/purgeAuditLog` 列），
不落憲法島 G6「`ptype=p ∧
protected=TRUE ∧ v2∈HTTP 動詞` MUST NOT 授予非 R_SUPER」之結構性封死射程 ⇒ 超管 MAY 於運行期
把本端點下放給其他角色（006-authz-governance 已交付的正常產品操作），屆時受託角色亦可收到本
明細。**本旁證因此只降低風險、不構成受眾封閉性保證**（同批之 ADR 0077 款二子選項 A-1 對五支
audit 端點 `protected=FALSE` 的論證與本段同一事實基礎）。即便不計此點，上述來源歸屬論證已
獨立成立。

### 三、為何是「補充」而非「翻案」（supersedes 留空之論證）

ADR 0064 決定一的形式是枚舉（「恰二」），加一列是否推翻它？認定＝**不推翻**，三筆：

1. **枚舉自帶擴充協定**：決定三末句（背景已逐字引）明文預留「擴到第三鍵＝回本 ADR 走
   判準」——一個自我宣告修訂路徑的枚舉是**登記表**、不是凍結判決；本 ADR 正是循它自己
   指定的路徑走，何來推翻。
2. **被翻案的實體不存在**：ADR 0064 的三個規範性決定——受眾邊界判準（決定二）、`5003`
   純 key 終局（後果一）、機器面守法（`from_err` 出口分離＋單一組裝點、決定三）——本 ADR
   一條不改、全數沿用且以判準為論證骨架。「恰二」是決定一寫定當時的**射程快照**（其自陳
   「只是把收窄後恰剩哪兩個寫定、不是新的收窄動作」），快照隨受控擴列前進≠原則被翻。
3. **先例**：ADR 0063 款三補充 ADR 0022 決定 3、ADR 0064 自身補充 ADR 0022 決定 2——
   本工作區對「原決定續行有效、新事實受控疊加」一貫走補充形，supersede 保留給「舊決定
   不再成立」。

**誠實對價**（不硬凹）：走補充形的實質代價＝射程枚舉自此分居兩檔（ADR 0064 二列＋本檔
一列），單點閱讀性弱於 supersede 重立三列全表。緩解＝本檔決定一已載現況全表鏡像（規範性
權威仍為兩檔聯集），且碼側 `error.rs` doc（T014 改對後）與 Lint24 第三腿（B-139、T021）
各為單點對賬面。若 user 於 T003 判定「恰二」字面應以 supersede 收束，改形屬形式選擇、
不影響決定二判準與本鍵論證。

### 四、機器面連動（本 ADR 不新增機制、只記看守人變化）

- **單一組裝點紀律沿用**：第三鍵構造點恰一、落 `handler/audit.rs` purge 守門（T014）；
  `Res::from_err` 對 `BizData` 仍回 `data: null`、攜明細恆走 `IntoResponse` 顯式出口
  （ADR 0064 決定三，零改動）。
- **本鍵之機器守隨本刀同批落地，但晚於構造點**：ADR 0064 決定三曾明載鍵名與前端佔位符分岔時
  三道現有守門（Lint24 舊腿只比鍵集／typecheck／端點測只驗碼與 msg 鍵）全攔不到（其 U4 實暴、
  B-139）；本刀 Lint24 擴第三腿（zh-tw 譯文 `{ident}` 佔位符集×後端 `BizData` 構造點頂層鍵集
  比對、併驗兩語 runtime locale；spec FR-H01、T021）——擴腿後對賬面即為**三攜參鍵全集**，前二
  鍵一併納入看守。★**誠實揭露裸奔時窗**：tasks.md 相依序逐字＝「T014＋T015──▶ T021（Lint24
  第三腿之三鍵終態）」，故守門（T021）晚於本鍵構造點（T014）——該時窗內本鍵與前二鍵同屬 ADR
  0064 所述之零機器守態，收官時才由第三腿一併納守。故本條**不宣稱本鍵生而有守**，只宣稱守門
  與本鍵同刀落地。

## 後果

- `rust-api/server/src/error.rs` 現於兩處 doc（enum 檔頭 doc 與 `BizData` 變體 doc）逐字
  載「射程**嚴限密碼二鍵**」——本 ADR accepted 且第三構造點落地後該述成假述；**改對歸本刀 T014／U4**（計入
  其涉檔），本 ADR 僅留此指針、不動該檔。
- 次序約束（spec FR-G01）：本 ADR MUST 先於 purge BizData 構造點落地——T014 開工前提＝
  本檔已於 T004 轉 accepted。
- Lint24 第三腿（B-139、T021）以三攜參鍵為對賬面；B-139 隨本刀關帳。
- 日後第四鍵＝同一路徑：回 ADR 0064 決定二判準、立新 ADR 補充；「在某支 handler 裡多寫
  一顆 `AppError::BizData`」仍為違約形。
- ADR 0064 全部規範性決定續行有效；其決定一之「恰二」自此讀作歷史快照、現況射程以
  「ADR 0064 二列＋本檔一列」聯集為準。
