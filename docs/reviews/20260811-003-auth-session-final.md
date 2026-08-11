---
date: 2026-08-11
scope: 003-auth-session final holistic review
findings_total: 26
confirmed: 11
refuted: 15
distinct_issues: 8
---

# 003-auth-session — final holistic review

feature branch 完成 T001~T077 全 77 個 task 之後、finishing 之前的整體審查。
逐單元的 spec-compliance 與 code-quality 已各跑過 3~4 輪，故本輪明令**不重報單元內部已審過的東西**，
只找站在全刀高度才看得見的問題。

## 方法

五個維度各一支 reviewer（只讀不寫），**每筆 finding 再派一支駁斥者**——預設立場是「這條不成立」，
只有駁不倒才確認；不確定一律駁回。特別檢查三種常見假 finding：證據行號已被後續單元修掉／
失效鏈其實被別處的守擋住／它其實是刻意設計且碼註或 ADR 已寫明。

| 維度 | findings |
|---|---|
| 跨單元一致性 | 5 |
| 驗收標準兌現度 | 4 |
| 憲法／ADR 自洽性 | 4 |
| 機器守對抗性盤點 | 5 |
| 文件與實況分岔 | 8 |
| **合計** | **26** |

**結果：確認 11 筆、駁回 15 筆（駁回率 58%）。**

★確認的 11 筆去重後是 **8 個相異問題**——活書 TTL 公式那條被**四個維度各自獨立報出**
（1 blocker ＋ 3 minor），交叉印證強，但同一個修法。兩個駁斥者對它的嚴重度給了不同判定
（doc-truth 判 blocker、cross-unit 收窄為 minor 並附論證），因它是一行文件修正，不另裁。

## 三分流

### 修（6 項，本輪已落地）

| # | 問題 | 處置 |
|---|---|---|
| 1 | 活書 TTL 公式寫死 `refresh = N×60 + 300`，與實碼／spec／data-model 三方的 `+ access` 分岔。`session_idle_timeout` 下界為 5，N∈[5,10) 時兩式不等（N=5 實為 450 而非 600）；且島 D 的門檻＝`refresh − access` 恆等於 N×60 只有在加 access 的形下才讀得通 | `ARCHITECTURE.md` 改為 `+ access`＋補「不可簡寫」理由 |
| 2 | ★`cache::denylist_set` 的 doc 註寫「TTL 覆蓋 access 存活窗即可」，與憲法 §I.7 島 C「MUST ＝ refresh 全壽命」**直接矛盾**——那正是 FR-008 點名要修的 rev4 缺陷形 | 改寫該註並寫明失效鏈；三個呼叫端實查皆傳 refresh 全壽命，註解現在名副其實 |
| 3 | ★「constant routes MUST 為併入而非取代」零機器承載。實測回退成 upstream 形後 fork-delta-lint 三個判定全綠、五道閘皆看不見，而後果是 **login／403／404／500／iframe-page 五條 builtin 常量路由被清空、登入頁本身不可達** | fork-delta-lint 新增 `REQUIRED_LITERALS` 交付面必存字面守 |
| 4 | 同上組：登出的 `await fetchLogout(...)` best-effort「失敗不得阻斷 `resetStore()`」（憲法 §III.2 (i) 逐字收窄）同樣零機器承載 | 併入同一組守 |
| 5 | ★T069⑤「三重非 vacuous 斷言」**只覆蓋 §III.2 半邊**；§III.1 三軌道可靜默自名冊掉線而 lint 全綠。實測把 `### III.1` 改成 `### III-1` 或刪列 ⇒ 名冊由 7 名縮成 4 名、輸出仍宣稱「軌道名皆在名冊」 | `load_roster()` 補 `s1_rows != 3` 斷言；tasks T069 的 DoD 字面同步收窄 |
| 6 | `B-008` 的 2026-08-09 勘誤兩處現況斷言已被本刀反轉（`.env` 已翻 dynamic；「首個 ★ 軌道 Amendment」已不成立）；`B-057` 的裁決觸發器指向已關閉且不含 data-model 收斂的 T077 | 兩條帳本更新 |

★#3~#5 三組新守**皆配變異測試**（ADR 0024）：
- 併入形回退 → rc=1 且指名該檔並說明「登入頁不可達」；還原 rc=0
- 拿掉登出 catch → rc=1 且指名「使用者登不出去」；還原 rc=0
- §III.1 表錨壞掉／刪列 → die rc=2（修補前這兩形都是**靜默 rc=0**）；基準未變異時 7 名不 die

### 轉 BACKLOG（3 項）

- **B-067**｜`wire_schema.rs` 的裁判面仍停在 002 的兩個 definition，003 新增五個 wire DTO 無一被快照裁判消費。
  失效鏈＝upstream 對 `Api.Auth.UserInfo` 加必填欄 → `wire-schema check` 紅 → 重抽快照 → 轉綠 →
  **全樹零測試變紅**。★當下兌現度不受影響（SC-001 由 `user_info.rs` 的 t019 四欄斷言承接）。
- **B-068**｜fork-delta-lint 的授權判定只到**軌道裸名**層級，而憲法的授權單位是（軌道 × 用途 × 檔案）三元組。
  ★需先解決 §III.2 表格「型別」欄與 as-built 的既有分歧，否則新判定會誤報。
- **B-069**｜`wf-watchdog.py` 的 runaway 門檻寫死 25 支，對**扇出型** workflow 必穿。
  ★危害不只噪音：告警文字寫「TaskStop wf」而正確處置是不要 TaskStop，且它觸發後 Monitor 即結束
  ＝在 run 未完成時自己拆掉看門狗（本輪實暴）。

### won't-fix（0 項）

無。

## 駁回的 15 筆裡值得記的

駁斥者不是橡皮圖章。幾個被實地駁倒的例子：

- 「`single_session_default` 的 fail-* 方向實作只做了 `Ok(None)` 那一腿」——實查兩腿確實分開（L-016 已落實）。
- 「三區不變式在權威 DB 值上零守門」——**這條在第一輪被確認、第二輪被同一批駁斥者推翻**：
  第一輪的駁斥者查完四條路徑全部落空而確認，第二輪重跑時另一支駁斥者找到了不同的反證。
  ★同一 finding 兩輪不同結論本身值得記——駁斥結論會隨查證深度改變，單輪確認不等於定論。
- 「用途後綴未驗」（兩個維度各報一次）——皆被駁回，但**同根因的另一個角度**（授權單位維度落差）
  被確認 ⇒ 已收 B-068。

## 本輪暴露的兩個編排缺陷（皆已處置）

**① `AGENT_FUSE` 設成了預算而不是後盾。** 我把它設 24，而 5 維度 × N 筆 findings 的理論上限遠不止 24
⇒ 直接切掉 doc-truth 的 7 筆複核。保險絲的用途是**失控後盾**，必須設在理論最大值之上。已改 80。

**② review agent 的「唯讀」不含 DB。** prompt 寫「跑唯讀指令皆可」，但駁斥者為了查證跑了 `cargo test`
與 psql，三張稽核表各殘 1 列、`sys_token_id_seq` 被消耗、`single_session_default` 被翻——
審查結束後 schema-gate gate2 當場紅。這是 L-015 的同形（★任何 runtime 寫入之後都要跑 quickstart §7 收尾），
只是這次寫入者是 review agent。收尾後三閘全綠。
★下次的 review prompt 應明寫「若你跑了任何寫入 DB 的指令，回報中須註明」。

## 驗證（本輪處置後）

| 項目 | 值 |
|---|---|
| `cargo test --workspace -- --test-threads=1` | rc=0、**321 passed／0 failed**、零 FAILED 行 |
| `fork-delta-lint.py` | rc=0（三守綠：假 toast／`$t` fallback／交付面必存字面） |
| `schema-gate.py check` | 三閘四行全綠、gate2 seed 486 行逐列零差異 |
| `docs-sync` lint／自測 | 0 錯誤 0 警告／471 tests OK |
