# B5b 前拍板閘・三題裁決紀錄（連動組）

> 落點＝`docs/brainstorms/`（HISTORICAL_EXEMPT 前綴、創世期史料）。日期＝2026-08-04。
> 裁決者＝user，依賴序 Q2→Q3→Q4 逐題分問（決策紀律 §8）；Q3 應 user 要求先釐清
> 「refresh 首跑」機制後重列選項再裁。本檔是 B5b／B10／波 0 刀邊界的直接依據。

---

## Q2・schema 壓平：bootstrap 波 -1 還是波 0 正式刀

**裁決：甲案——降為波 0 的第一把正式刀（沿 rev4 先例）。**

- **內容**：rev4 十五支 migration 終態 → rev5 `m001_baseline_schema`＋`m002_baseline_seeds`，走完整刀流程（brainstorm→SDD 5 步→TDD→收刀簿記）。藍本座標與驗證法（pristine 重放**未排序逐列 diff**＋negative test）＝啟動書 §4.5.8。
- **為何這樣拍**：①治理鏈（feature-branch pre-hook、SDD 逐步 commit、Lint06 收刀聲明制、簿記三步）在功能刀前的首次實戰演練——用驗證法已定、範圍清楚的工作載提早暴露流程 bug；②schema 是最承重工件、spec＋ADR 史料值得；③rev4 先例（002-schema-baseline、rev4:ADR 0014／0021）零翻案。
- **連動面**：B12「第一把功能刀」實質成為第二把刀；Q1（欄序親排＋seed 過目）關卡**嵌在刀的 clarify／plan 內**、不再獨立拍板閘；B10 邊界縮小（見 Q3）。

## Q3・B10 剩餘兩件事的歸屬

**裁決：甲案——compose 移植留 B10 工程步；refresh 首跑作刀的 DoD。**

- **先釐清的機制事實（user 追問後查源碼）**：`refresh`＝對運行中實庫下六道 SQL、六撈全成才原子落檔兩快照（schema-snapshot 50KB 逐欄含欄序／accounts-snapshot＝seed 淨效果）；下游＝generate 真表（schema.md／accounts.md）＋entity-drift-gate＋schema-gate＋`gen.snapshots` 豁免解除。**refresh 是實庫的照相機——壓平前庫是空的**，首跑必然排壓平之後，留在刀前的 B10 會時序倒置、不是選項。
- **裁定邊界**：B10＝純移植工程步（compose 三檔＋掛載相依自 rev4 藍本、§4.5.9 九條錯開逐項驗收、驗 postgres／redis 可起、`gen.compose` 豁免解除→ports 真表重算）；刀＝migration crate 骨架＋m001/m002＋pristine 逐列 diff＋Q1 親排＋**收尾 refresh 首跑與真表產出（DoD）**——起 postgres 為刀內前置。
- **為何**：已拍板的機械移植不塔 SDD（同 B2～B6 先例）；真表產出就是壓平完工的機器驗收面，刀內一氣呵成、零時序縫隙。
- **既知邊界事實**：Day 1 六件 stack 起不齊——rust-api server 實碼 B12 後才有；B10 驗的是 config 解析＋錯開＋postgres/redis 可起，非全 stack。

## Q4・deploy 資產搬運範圍

**裁決：乙案——機密管線最小集在 B5b，其餘隨 B10 與 compose 同步。**

- **B5b 搬**：EXEC_BIT_ROSTER 五支（sops／decrypt-secrets／generate-secrets／preflight-secrets／generate-dev-cert）＋`generate-age-key.sh`（bash 前綴叫用、不在名冊但產鑰必用）＋secrets 範本 14 檔（13 `*.txt.example`＋README——缺之 bootstrap 第 7 節迴圈零圈假綠）＋`dev-certs/.gitkeep`＋`.sops.yaml` 改 recipient（檔已 tracked）＋密文 `secrets.dev.enc.yaml` 產出入版。
- **隨 B10 搬**：nginx 三檔＋observability 設定＋grafana-provisioning 整棵（實搬 12、扣治外飛地 `backend-msg-dict.json`）＋`Dockerfile.rust-api`。
- **為何**：搬運與消費同步——這批資產唯一消費者是 compose 掛載（Q3 拍在 B10），甲案下它們在 B5b～B10 間無任何機器閘看管（Lint21 只管五支、Lint20 不引用）＝搬壞了要到 B10 才暴露；且與 §4.2 B10 原文一致。機器硬需求（Lint21 五紅、bootstrap 755 案、age 釘版案、secrets 體檢）最小集全數涵蓋、B6 前就位不受影響。
- **連動面**：§4.5.11 步驟 1 照本案改寫（搬運清單縮）；`dev-webhook-sink.sh` 依原文刻意不搬；B7 創世 commit 更聚焦治理面。

---

## 邊界改寫總覽（三題合併後的 B10～B12 時序）

```
B5b（機密管線八步、最小集）→ B6 → B7 創世 commit → B8a → 拍板閘（B9 前）→ B9
→ B10（compose 移植＋錯開，工程步）→ 波 0 schema 基線刀（正式刀；Q1 嵌 clarify；
   DoD 含 refresh 首跑＋真表）→ B8b → B11 → B12（第一把功能刀＝實質第二把刀）
```
