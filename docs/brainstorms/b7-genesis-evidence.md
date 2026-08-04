# B7 創世儀式施工紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-04。依據＝§4.2 B7。
> **創世 commit＝`cb2ced604eb9a1fdd55728976f434771125cf5ec`**（單一 commit、B1～B7 全產物一鍋）。

## 一、三工件

| 工件 | 內容 |
|---|---|
| ADR 0001 創世採用 | accepted 起家；provenance 雙 SHA（樣板@1c1854b4＋rev4@2b8a101c）；「工件必須機器產出」偏離立案＋sha256 manifest 緩解；憲法 v1.0.0 定版紀錄；★§I.5 schema 拷貝例外承載（B5 親審裁定）；創世結構紅治理（DAY1_EXEMPTIONS＋fork-delta Day-1 跳過）在案 |
| ADR 0002 白名單反轉延後 | §0.3 準則 1 要求的顯式延後立案：理由三條（四漏網已入 BUDGETS／守衛#8 已 fail-closed／創世期檔集仍膨脹）＋雙觸發條件（B12 後首維護批；或任一 tracked md 超 15k tokens 提前觸發） |
| 創世 misc 事件 | summary 140 字（≤300、無換行）；notes 攜 `lint-roster:` 23 條人寫名冊（★名冊尾接 ASCII 空白——regex 吃到空白為止，全形標點會黏進 token） |

5b 條款數斷言單跑：**掃源推導＝創世名冊＝23** ✓（三源對賬成立）。

## 二、★真閘第一天、兩次實彈攔截（都是真問題）

**第一攔・值比對層佔位命中**：secret-value-guard 攔 `generate-secrets.sh`／`preflight-secrets.sh`——`alert_webhook_url` 現值＝佔位字面 `https://CHANGE-ME.invalid/…`（設計上的公開字面）逐字存在於兩腳本源碼。射程縫隙：「佔位型機密＋其產生器首次入版」的組合 rev4 從未暴露（真值已填）。**user 拍板甲案**→guard 加 `PLACEHOLDER_VALUES` 白名單（逐字全等、check 與 --full-tree 同源共用 `comparable_secrets`）＋跳過明細＋三測試（佔位跳過／真值照抓／近似形不豁免——字面手寫釘死防套套邏輯）＋**ADR 0003**；突變實證＝拔白名單項→live check 恰 2 命中回歸。三處同字面雙記帳（guard 白名單／preflight PLACEHOLDER_LITERALS／測試字面）載明於 ADR。

**第二攔・hook 接線契約測試**：pre-commit 裁製（fork-delta 段加基線源倉缺席 Day-1 具名跳過——工具首步斷言 rc=2 會擋創世）後，TestGateWiring 兩案翻紅——**契約測試在 fixture 沙盒乾跑真 hook，抓到接線行為被改**。同刀修法＝fixture 建源倉目錄佔位（契約測 B9 後穩態）＋新增 `day1_skip` 專屬契約測試（缺席→不跑＋rc0；與 union 案成對＝兩向紅綠）。427 tests OK。

★共同意義：改閘門的人（我）被閘門的閘門攔住——「同刀改對應自測」紀律不是儀式，是這兩攔的直接受益者。

## 三、收工判準（全數通過）

| 判準 | 實得 |
|---|---|
| 創世 commit 過全套真閘 | betterleaks staged（1.79MB no leaks）→ guard（佔位跳過明細＋零命中）→ check 一致 → lint 0 錯誤 → 五支工具 test 全跑（427/426+ OK）→ fork-delta Day-1 具名跳過行印出 → 計時閘未攔（≤45s 硬上限） |
| commit 後狀態 | `git log` 恰一筆＝cb2ced60；porcelain 0 行；check 一致；lint 0／0／10／共 23 |
| Lint20 兩殘紅自解 | ADR 檔集非空＋events 非空——lint **首次全綠**於 commit 前達成 |
| rev4 紀律 | porcelain 0、HEAD 2b8a101 凍結（哨兵 4 小時保險絲期滿全綠、已重掛） |

## 四、刻意留給後續

| 項 | 落點 |
|---|---|
| fork-delta Day-1 跳過解除 | B9（bootstrap 建源倉後自動恢復實跑；契約測試已釘兩向） |
| alert_webhook_url 真值＋回寫密文 | B10 前（RUNBOOK §7＋§15；填後 guard 自動納回比對） |
| hooks 指紋斷言（B-124 形、對 HEAD） | B8b（HEAD 已存在、可實跑） |
| B7 後一切改動照常單獨 commit | B8a 起（一鍋紀律僅限創世） |
