<!-- next: B-006 -->
# BACKLOG — 待辦

條目格式 `- B-NNN｜<一句話>｜<觸發條件或期限（選）>`；配號取檔頭 next-id 後 bump、號碼永不回收；完成即刪列、git 即史。

- B-001｜評估 brainstorm 承襲盤點機器閘（lint 條款或 speckit plan 模板列，強制對照啟動書 §5 K1 清單）｜首刀（B12）跑完 Constitution Check 後檢驗實際需求再定
- B-002｜Lint18「merge SHA 不可解」紅訊息補去處（B8a 裁決員 D2 發現：只給病因無修法，違「紅訊息附去處」慣例；建議文案＝請以真實 merge commit SHA 覆寫該列、事件帳既有列不可改者改以新事件更正）｜首個維護批
- B-003｜memo 欄家族 UI 兌現——sys_user／sys_role／sys_menu／sys_ip_rule 四張管理列表的顯示欄＋編輯入口（語意：R_SUPER 備註用途、text 可多行；顯示於管理列表、不顯示於其它被取用處——下拉／引用／對外 API 不帶；rev4 設計入 schema 但各 UI 刀 brainstorm 均未兌現，語意權威＝001 刀 data-model）｜各對應管理 UI 刀 brainstorm 直接輸入
- B-004｜移植品前代 ADR 指涉清償（全量枚舉＝ports-2xxxx 批 reviewer 實測；枚舉命令 grep -rnoE 'ADR [0-9]{4}'、排除 .git/tmp/子庫/源倉/brainstorms/generated）——分流三路：①前綴化 `rev4:`（本項轄區）＝0072（docker-compose.yml reaper 註解、deploy/setup-reaper-role.sh）、0012（example node 釘版）、0080（deploy/decrypt-secrets.sh、preflight-secrets.sh）、0022（generate-dev-cert.sh、generate-secrets.sh）、0084（deploy/secrets/README.md、generate-age-key.sh）、0037（nginx _locations.inc）、0077（tools/docs-sync.py 五處）；②tools/schema-gate.py 之 0064/0063/0049/0039/0032 多處＝schema 基線刀整組重建轄區、本項不動；③.specify/memory/constitution.md 之 0085/0041＝查實形後另議（憲法修訂＝amendment 程序 ADR＋版本 bump、user 拍板）。＋deploy/secrets/README.md 內 `$HOME/.cache/fork260509-rev4/secrets` 敘述改 rev5（功能面已驗零影響：腳本預設 deploy/secrets、.env 實值為 rev5 路徑）；連帶 LESSONS 入帳：B10 殘留掃描樣式 `rev4[-_]` 抓不到「rev4/」黏斜線形＝掃描樣式集缺口；連帶 README 常見問題表補一列「查埠／帳號／schema／畫面現況→`docs/generated/reference/` 五張正典表」（現行 FAQ 僅進度／歷史／決策三列、reference 只在樹狀圖帶過＝發現性缺口，user 2026-08-05 實際撞到）｜首個維護批
- B-005｜wf-watchdog.sh 加可選第二參數（wf transcript 目錄或 runId）支援硬編監看目標——「最新目錄」自動發現二次實彈鎖錯 run（2026-08-05 ports-2xxxx 批：ARMED 冒煙攔下、應急改掛 inline 復刻迴圈）；加參數後 CLAUDE.md §2 的 Monitor command 範本同步帶目標寫法｜下個維護批
