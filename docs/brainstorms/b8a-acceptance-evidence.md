# B8a 移植驗收・前段施工紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-04。依據＝§4.2 B8a。
> 編排＝Workflow A（10 驗收單元 opus＋裁決 fable、`wf_9c104894-6b7`）＋紅隊兩幕（主線親操）；
> 每次 launch 與看門狗同回合原子成對、ARMED 首行核 run-id（三次武裝三次核靶全中）。

## 一、Workflow A（①殘紅盤點②drift 演練③突變實證）——verdict＝**ok**

10/10 單元 status=ok、零 blocker、零死亡、逐支 root_porcelain=0（本尊零污染自證）；567k tokens／14 分鐘。

| 項 | 判準 | 實得 |
|---|---|---|
| ①殘紅盤點（A1） | 僅具名 SKIP、零 ERROR 零 WARN、逐筆附解除謂詞與 B 步 | 摘要行逐字「lint：0 錯誤／0 警告／10 條款跳過／共 23 條款」；10 案＝Lint16×2＋Lint17×2（→B9）＋gen.compose（→B10）＋gen.snapshots（→B10/schema 刀）＋gen.router（→B12）＋gen.screens（→B9）＋gen.msg_dict（→i18n 刀）＋lint24.day1（→B12） |
| ②drift 演練（D1~D3） | 三類各被擋、紅訊息附去處、還原復綠 | D1 手改生成物→Lint01 紅✓；D2 假 merge SHA→Lint18 rc=1 硬紅✓（★訊息無去處＝真發現，見三）；D3 配號回收→Lint09 紅附去處✓ |
| ③突變實證（M1~M6） | B4 裁改逐條紅綠＋豁免逐筆拔項＋照搬抽一 | M1 單一引擎（BSD 模擬→恰三 label 紅、PEM 綠）✓｜M2 Lint11 混寫中／前綴形放行／rev5 裸碼不誤報＋Lint15 紅綠✓｜M3 豁免六筆逐筆拔項全翻紅✓（紅形見三）｜M4 summary 301 紅／300 綠＋常數放寬 400 被字面自測攔＋BUDGETS 刪檔紅✓｜M5 Q13 拆接線 3 案紅＋名冊 22≠23 die✓｜M6 佔位白名單拔項→命中紅、還原→跳過明細＋照搬抽一（Lint10「待決」紅）✓ |

**裁決（fable）親驗四項**：①本尊唯讀重跑 lint、與 A1 逐字比對（含 10 案明細組成）②自建副本重演 M4(a) 突變（301 字紅行逐字、300 字放行、還原復綠、副本 rm -rf 確認）③本尊 porcelain 開工前後皆 0 ④D2 的 pass:false 回報經源碼複核（docs-sync.py:2857-2859 訊息確無去處、:5073 把「附去處」釘成 Lint10 契約）＝誠實準確。

## 二、紅隊演練（④兩種保險絲第一次實彈——rev4 上線 33 天零實戰紀錄）

**RUNAWAY 幕（`wf_b9f1aee8-1ed`）**：犧牲 script 寫死 30 支（恰超靶值 25、每支 sleep 20 拉長存活窗、haiku 微呼叫）。告警**攔在進行中**（28 key 時、30 支未跑完），原文逐字：
```
看門狗 RUNAWAY：不重複 agent key 28 > 25（防呆③保險絲疑失效）→ /workflows 查→TaskStop wf
```
告警後犧牲 run 旋即自然收完（30/30）、TaskStop 撲空屬預期時序。

**STALL 幕**：
- v1 誠實記載：犧牲 agent 奉命 `sleep 599`×2，實際 **44 秒早退**（`tool_uses=1`）——★**subagent 的 Bash 同樣被 harness 擋前景 sleep**，此為 sandbox 行為發現（與主線相同的封鎖、演練設計時未知）。
- v2 改 until-迴圈（harness 允許形、顯式 timeout 600000）×2 輪（`wf_ef7779ee-b11`、實跑 20.9 分）：
  - ★**門檻校準實證（v2 的意外收穫）**：21 分鐘「長工具忙碌」全程**零誤報**——每次工具結果都寫 journal、idle 時鐘重置；600s 工具上限下「活著的靜默」結構性到不了 780s。STALL 靶值「>最長合法單命令 600s＋margin」的設計語意經實彈反向驗證：**長工具不誤報、觸發域＝零工具活動的真死／收工未收 Monitor**。
  - run 收工後**刻意不 TaskStop**→真靜默成形，告警實彈（原文逐字）：
```
看門狗 STALL：818s 無寫入 > 780s（疑卡死/死迴圈）→ /workflows 查→TaskStop→修 script→resumeFromRunId 續跑
```
  - 此即雙訊號設計中看門狗負責的那一半：「完成通知遺失／Monitor 未收」的兜底，攔截語意成立；告警後看門狗自行退場（exit 0）。

**④判準總結：兩種保險絲皆實彈攔截成立**——RUNAWAY 攔在進行中（28>25）、STALL 攔在真靜默（818>780），且各附一筆校準性副產物（存活窗設計、600s×780s 關係）。

## 三、裁決員交辦與帳面處置（三筆）

1. **D2 真發現→B-002**（已入 BACKLOG）：Lint18「merge SHA 不可解」紅訊息只給病因無修法去處，違「紅訊息附去處」慣例（該慣例被 :5073 測試釘成契約）。非 blocker（閘本體 rc=1 有效）、屬訊息工學；建議文案已附。
2. **M3 紅形帳面改寫（設計預期、非缺陷）**：六筆拔項的具名例外（ComposePortsError 等）不現身——`cmd_generate` 首段守衛（`lint_reference_sources`）先攔、紅形歸一化為「generate：來源檔守衛擋下 N 筆」＋Lint20 ERROR。拔項**確實逐筆翻紅**、只是形不同；日後預期表照此寫。
3. **B8b 硬性待辦**（已入 task）：gen.router／gen.screens／gen.msg_dict 三筆的 **lint 端**拔項實證與子庫 SKIP 重疊、B8a 只驗到 generate 端——子庫就位後（B8b）重跑。

**口徑校準（下游機判必讀）**：①Lint11＝WARN 級、退出碼只看 ERROR——「翻紅」表現為警告條列、rc 仍 0；機判勿寫死「紅＝rc≠0」。②「末行」在本專案語彙＝lint 摘要行；Z>0 時物理末行是跳過明細——機判以「lint：」前綴定位。
**微瑕兩枚（不影響裁決）**：D1 evidence 行文誤數（Lint20×4 應為 ×5）；M4(b) 回傳帶多餘欄位 passx（JSON 雜訊）。

## 四、成本與時序

| 段 | 用量 | 時長 |
|---|---|---|
| Workflow A（11 支） | 567k tokens | 14 分 |
| RUNAWAY 幕（30 支 haiku） | 529k tokens（★高於預估的「忽略不計」——haiku 微呼叫的 per-agent 固定開銷被低估，誠實記載） | 5.5 分 |
| STALL 幕 v1＋v2 | 19k＋19k | 44s＋20.9 分（＋等彈 13.6 分） |

**B8a 收工**：四項判準（①殘紅盤點②三類 drift③突變實證④看門狗紅隊）全數通過；交辦事項已入帳（B-002、B8b 硬性待辦、口徑校準隨本檔）。
