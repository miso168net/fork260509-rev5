# B8b 移植驗收・後段 施工紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-06。依據＝啟動書
> `docs/brainstorms/000-doc-architecture.md` §4.2 B8b 三項＋§4.3 DoD＋B8a 裁決員交辦
> （`b8a-acceptance-evidence.md`）＋B6 指紋驗證延期案（`b6-hooks-evidence.md`）。
> 時點＝001 schema 基線刀收刀後（merge `6a4696f`、簿記 `5ac292b`）——子庫與 stack 皆已就位，
> 符合 B8b「結構上要等子庫與 stack」的排序理由。

## 一、三項本體（＝樣板 §8 之④⑤②）

| 項 | 判準 | 實得 |
|---|---|---|
| ①bootstrap 純體檢（樣板 §8 ④幂等） | rc=0、零改動、警告 0 | **rc=0、警告 0 項**；前後三庫（外層／base-web／rust-api）`status --porcelain` 與 `submodule status` **逐行相同**。逐項全綠：origin 身分／`core.hooksPath`／betterleaks 1.7.3 釘版／兩源倉在場／**最原始源基線 example@8be6f9ba**／upstream no_push／兩 worktree／兩源倉 hooksPath／五支工具自測／fork-delta 實掃／entity-drift 實比對／條款數三源同 23／`.env` 形制／SECRETS_DIR 實值檔齊 |
| ②生成檔刪除重算（樣板 §8 ⑤） | 重算後 check 復綠 | 強化形＝**tracked 生成檔 8 檔全刪**（非「任一」）→`generate`：重算 8 檔→`git status --porcelain` **零輸出**＝與 HEAD **逐位元相同**（決定性重算，非僅語意等價）→`check`：一致。兌現 CLAUDE.md §4「機器生成物任何檔案可刪除重算」 |
| ③假 feature 走一刀（樣板 §8 ②） | 分支→改動→merge→簿記三步→commit；feature_close 的 pins 兩鍵有真值 | **以 001 真刀充抵**（工程判斷、見下）：feature branch `001-schema-baseline`→`merge --no-ff` `6a4696f`→簿記三步 `5ac292b`（events append＋NOTES＋generate）；`feature_close` 事件 pins 兩鍵皆**全長真值**（web=0fee6c02…、api=4bbc9898…）、`backlog_add` 9 筆／`backlog_done` 1 筆實用、Lint18 merge SHA 可解 |

**★③充抵的理由與可逆性**：假 feature 的存在目的＝在無真刀時預演事件鏈與 pins 真值；001 是走完
全程的**真**刀（11 個外層 commit、SDD 鏈＋TDD 鏈、真 merge、真簿記），涵蓋面嚴格大於假刀，
再跑一次只會在 git 史留無資訊量的噪音 commit。user 於計畫核可（`task-go`）時未反對本建議、
但亦未逐字裁定——若日後要求補走假刀，成本＝一支分支加三個 commit，隨時可補。

## 二、累積交辦結清

| 交辦 | 出處 | 實得 |
|---|---|---|
| gen.router／gen.screens／gen.msg_dict 三筆 lint 端拔項實證 | B8a 裁決員硬性待辦 | **screens 已於 B9 真解除**（worktree 掛載使謂詞成立→到期即紅→兩表拔項→真表首算 71 行）＝實彈涵蓋。**router／msg_dict 於本步做突變實證**：兩表同刀拔項後 `generate` rc=1 被**來源檔守衛**擋下（contracts G4）、`lint` rc=1 且 **Lint20 逐檔指名缺源**（`rust-api/server/src/router.rs`／`base-web/src/locales/langs/zh-tw.ts`），skip 5→4、紅 0→1；還原後 porcelain 乾淨、lint 復 0 錯誤／0 警告／5 跳過 |
| ★首輪突變只拔單表的實得 | 本步親歷 | 只拔 `DAY1_EXEMPTIONS` 未同拔 `DAY1_EXEMPT_SCOPE` → 撞**啟動斷言**「兩表鍵集不一致」rc=1 而**到不了**下游紅。意義有二：①該斷言本身承重、非裝飾；②「兩表同刀拔項」是紀律也是機器強制，B4 單元 5 建表時的設計在此獲實彈驗證 |
| hooks 指紋以 HEAD 為基準 | B6 明定延至 B8b | 已內建於 bootstrap §3：逐檔 `git hash-object`（走 filter＝`git add` 同口徑）對 `HEAD:<路徑>` 比對——本步實跑印「✓ hooks 標的檔內容＝HEAD 版本（pre-commit／pre-push 指紋一致）」。B-124 型「hooksPath 指標值不變、標的檔被覆寫」之靜默失效面已閉合 |
| SessionStart 注入 ≤5k tokens | §4.3 DoD | 實測 3,432 bytes／2,240 字元（CJK 579）→**保守估 ≈1,110 tokens**（CJK 1.2 tok/字＋ASCII 4 字/tok），餘裕 ≈3,890 |
| pre-commit 全鏈時間基線 | §4.3 DoD／§0.3 準則 5 | 已由 001 收刀實測承載並轉 **B-007**：無 gitlink 無 tools staged＝**1.016s**；staged `docs-sync.py` 觸發 428 案自測＝**27s**（越 20s 警戒、未破 45s 硬擋）。量化門檻與預算分攤明文化屬 B-007 轄區 |

## 三、DoD 對賬（§4.3）

樣板 §8 六項至此**全過**（①②③⑥＝B8a／④⑤＝本步①②／②假 feature＝本步③充抵）；
pre-commit 時間基線與 SessionStart 注入量皆在案。§4.3 殘餘唯一未關項＝
**「K2 全量轉入 BACKLOG；樣板回灌帳 B 號開立」→ B11**。

## 四、刻意留給後續

| 項 | 落點 |
|---|---|
| gen.router／gen.msg_dict／lint24.day1 三筆豁免的**真解除** | B12（後端首刀落 router.rs）與 i18n 地基刀（落 zh-tw.ts）；解除謂詞成立即到期即紅、照紀律兩表拔項 |
| K2 全量轉 BACKLOG＋樣板回灌帳 B 號 | B11（創世 DoD 最後一項） |
| 三閘效能門檻量化、pre-commit 預算分攤明文 | B-007 |
