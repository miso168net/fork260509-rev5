<!-- next: B-042 -->
# BACKLOG — 待辦

條目格式 `- B-NNN｜<一句話>｜<觸發條件或期限（選）>`；配號取檔頭 next-id 後 bump、號碼永不回收；完成即刪列、git 即史。

- B-001｜評估 brainstorm 承襲盤點機器閘（lint 條款或 speckit plan 模板列，強制對照啟動書 §5 K1 清單）｜首刀（B12）跑完 Constitution Check 後檢驗實際需求再定
- B-002｜Lint18「merge SHA 不可解」紅訊息補去處（B8a 裁決員 D2 發現：只給病因無修法，違「紅訊息附去處」慣例；建議文案＝請以真實 merge commit SHA 覆寫該列、事件帳既有列不可改者改以新事件更正）｜首個維護批
- B-003｜memo 欄家族 UI 兌現——sys_user／sys_role／sys_menu／sys_ip_rule 四張管理列表的顯示欄＋編輯入口（語意：R_SUPER 備註用途、text 可多行；顯示於管理列表、不顯示於其它被取用處——下拉／引用／對外 API 不帶；rev4 設計入 schema 但各 UI 刀 brainstorm 均未兌現，語意權威＝001 刀 data-model）｜各對應管理 UI 刀 brainstorm 直接輸入
- B-005｜wf-watchdog.sh 加可選第二參數（wf transcript 目錄或 runId）支援硬編監看目標——「最新目錄」自動發現二次實彈鎖錯 run（2026-08-05 ports-2xxxx 批：ARMED 冒煙攔下、應急改掛 inline 復刻迴圈）；加參數後 CLAUDE.md §2 的 Monitor command 範本同步帶目標寫法。★併刀項（ADR 0010 轉換集、2026-08-06 拍板）：同刀將本檔轉 python（估 1.1 人日、轉後淨減行數＋刪 rev4:L-142 補丁＋os.stat 消滅 GNU/BSD 雙分支）——連帶＝docs-sync TOOLS_SH 名冊先改否則 Lint19 擋 commit、CLAUDE.md §2 Monitor command 契約字面、post-workflow-reminder hook 注入字面、README 樹狀圖、tools-cli 真表 regenerate；★陷阱＝python 於 pipe 後端預設塊緩衝，ARMED 行必 print(flush=True) 否則外觀同「發射失敗」｜下個維護批
- B-006｜schema-evolution.json 之 kind×detail 必備鍵表＋逐 kind 啟動斷言（analyze B2：現契約 detail 只驗非空、alter_column 零定形，壞形 entry 可滲入 gate1 合成；補「kind × detail 必備鍵」表升為斷言第 7 條＋八 kind 各一筆合法／缺鍵樣本自測；001 收刀擴充：detail 值域斷言一併入——pk 欄名 ⊆ COPY 欄集、pk/set 型別檢、同名 index/constraint 重複登記攔——四種壞形現逸出裸例外收 rc 1、應歸 rc 2）｜首筆真登記（E-001 之後、下一支帶 migration 的刀）前完備
- B-007｜三閘與治理工具效能門檻量化（analyze B5：「秒級」無量化、無 SC 承載；pre-commit 全鏈 20s 警戒／45s 硬擋之預算分攤明文化——新閘單跑上限與量測法入 contracts 或 RUNBOOK；001 收刀實測基準：無 gitlink 無 tools staged＝1.016s、staged docs-sync.py 觸發 428 案自測＝27s 越警戒未破硬擋——量測分兩情境各留值）｜001 刀收刀後首個維護批
- B-008｜四張 rev4 專屬管理頁 view 於 base-web 兌現——manage_system-settings／manage_policy-archive／manage_audit／manage_ip-rule（analyze D6：seed 選單與 casbin 政策隨 001 基線先行、`component` 指向之 view 於 rev5 base-web 尚不存在；期間該 4 項僅 R_SUPER 可見、點擊 404 屬已知態）｜各對應管理 UI 刀 brainstorm 直接輸入
- B-010｜data-model §2/§6 文件面 vs 凍結 fixtures 機器對賬（001 收刀 holistic：§2 型別/NULL/default 三欄與 §6 索引約束定義從未進機器比對面——gate2 欄序只解析欄名、型別面錨 fixtures；文件單邊被改不會被抓；三輪 review 各自寫過一次性 parser 證明可落地）｜首個維護批評估
- B-011｜gate2 seed normalize 擴充剝除 pg_dump 版本行與 Owner 註解行（001 收刀：比對面現含「Dumped from/by version 18.4」與 Owner 行——postgres 升版或 DB 身分再變即紅在純噪音、ADR 0008 那次即為 Owner 行連動重產 fixtures；契約級變更、gates.md §2＋fixtures 重產一次，宜與升版維護批同刀）｜postgres 升版前必做
- B-012｜audit 變體 B 禁欄判準施工——已拍板（ADR 0016）：前綴通配（updated_*/deleted_*）＋具名豁免清單出口；同刀把工具具名四欄實作與 gates.md §3 對齊＋成對紅綠測試｜首個維護批 schema-gate 群（與 B-006/B-013 同刀）
- B-013｜schema-gate 測試覆蓋兩缺口：cmd_check 綠路徑離線測試（fake run 分派 fixtures 三節）＋照相三查詢與 docs-sync 逐字重複之「同構」機器斷言（讀源碼比對三常數位元相等）｜首個維護批
- B-014｜entity 對應層後端首刀前補強：15 檔 Relation 空 enum（data-model §6 兩條 FK 未映射）＋ActiveModel 慣例面——本刀驗收（build 綠＋drift 綠）不需要、server 刀消費時變真風險｜後端首刀（B12）brainstorm 直接輸入
- B-015｜Lint06 arch_impact 基準施工——已拍板（ADR 0017）：改 merge^1:BOOK vs 簿記態（「本刀影響」語意）；恆 --no-ff 單親前提寫死工具註解＋合成 fixture 紅綠測試（不得以實跑 lint 驗收）；CLAUDE.md §2 流程不動｜首個維護批 docs-sync 群
- B-016｜稽核資料生命週期一次入設計：retention 水平線語意＋清理動作同交易自記稽核＋自動排程＋逐表門檻，不走「先手動清理、後補自動化」（前代同域四次拍板／一次正式翻案／一次違憲重拍；rev5 稽核表結構已隨 001 基線壓平落地、政策面尚未設計；詳＝啟動書 §5.2 K2-01、承 rev4:ADR 0058／rev4:0075／rev4:0076＋specs/rev4:017-audit-retention）｜稽核功能刀
- B-017｜會話生命週期一次設計完整、直接以 DB-stateful rotation 終態起手（rotation＋reuse 偵測＋denylist 即時撤銷＋single-session＋精確 idle），不走「無狀態先行、下一刀翻案」兩段式（前代付兩次完整拍板＋一次破前刀交付契約；詳＝啟動書 §5.2 K2-02、承 rev4:ADR 0030→rev4:0033）｜auth 刀 brainstorm 直接輸入
- B-018｜前端 demo 資產去留一次拍：alova 第二請求棧、替代登入表單殼（seed 側 demo 選單與授權已由憲法 §I.2＋ADR 0005 收；前代全量保留衍生兩支 won't-fix 決策＋清理需 seed 移除白名單；詳＝啟動書 §5.2 K2-03、承 rev4:ADR 0029／rev4:0035／rev4:0036）｜前端首刀 brainstorm 直接輸入
- B-019｜信任錨傳輸層背書入首版評估＋部署 checklist 與錨同刀交付（前代安全保證整個壓在「部署方須鎖 origin 僅接受 CDN 邊緣連線」的文件約束上、硬化案至今未做；詳＝啟動書 §5.2 K2-04、承 rev4:ADR 0043）｜ingress／IP 閘刀 brainstorm 直接輸入
- B-020｜失敗計數節流做成可掛任意敏感端點的通用 seam（per-user／per-IP），不綁死登入流程（前代改密端點無法直掛成獨立缺口、軟區永不被第一層快取短路；輕量範本＝原子先佔 SET NX→INCR→超限拒→best-effort 回補；詳＝啟動書 §5.2 K2-05、承 rev4:ADR 0037／rev4:0038→rev4:0045）｜節流刀 brainstorm 直接輸入
- B-021｜改密端點舊密暴力試節流（掛點在 argon2 之前、成功改密清計數、需新業務碼；殘餘拍板點＝redis 故障 fail-open 或 fail-closed、門檻走設定鍵或常數；詳＝啟動書 §5.2 K2-08、承 rev4:B-102＋specs/rev4:014-user-center／rev4:015-pwd-custody）｜auth 設計期內建、或列第一批補完
- B-022｜替代登入四流程做真或砍表單一次拍：驗證碼登入／註冊／重設密碼三張表單後端仍 stub、自助頁手機驗證為佔位控件（信箱半邊資產可平移、簡訊通道選型屬新拍板；已橫跨三代未收；詳＝啟動書 §5.2 K2-09、承 rev4:ADR 0029／rev4:0085／rev4:0086）｜沿用同款登入頁時開場即拍
- B-023｜備份自動化：排程 pg_dump＋卷快照＋還原演練＋機密檔與資料卷的配對備份（前代零工具致 RUNBOOK 破壞性驗證被迫跳過＝備份缺席在限制驗證能力；rev5 事件帳與稽核表自 Day 1 累積價值；詳＝啟動書 §5.2 K2-11、承 rev4:B-107）｜早期治理批（不宜留到 prod 前夕）
- B-024｜寫端授權下放非超管前置三件套：no-escalation 上限檢查、seeded 受保護護欄與「超管恆禁停用」結構護欄複評、業務錯誤明細通道受眾邊界重評（詳＝啟動書 §5.2 K2-12、承 rev4:B-083＋specs/rev4:009-role-admin）｜role／user 管理刀（目標含多層管理員即入首版）
- B-025｜軟刪×授權歸檔一致性通用掃描（選單／角色／使用者各軟刪路徑下 casbin 碼與選單按鈕欄聯集），宜與背景 job 底座同刀首發（詳＝啟動書 §5.2 K2-13、承 rev4:B-100）｜背景 job 底座刀
- B-026｜部分更新契約的通用顯式 clear 語意——三態（欄位缺席／清空／設值）於 wire 契約設計期一次定形（前代 null＝整欄跳過、「清回 NULL」無通用語意，僅 user 域以空字串部分兌現；詳＝啟動書 §5.2 K2-14、承 rev4:B-026）｜wire 契約設計期
- B-027｜列表欄位排序能力＋排序欄白名單三端單一來源（或 parity 檢查）＋per-column 索引評估（前代全數後端預設排序、白名單分散三端靠人工同步；詳＝啟動書 §5.2 K2-15、承 rev4:B-036）｜首個排序需求刀
- B-028｜後端開發體驗兩缺口：容器內 cargo build 時間基線量測（雙機冷編＋單檔增量，作為 dev profile debuginfo 裁剪的數據前提）＋sea-orm additive DDL 草稿生成輔助（entity 漂移閘已隨治理套件搬運兌現；詳＝啟動書 §5.2 K2-17、承 rev4:B-109／rev4:B-110）｜第一把 rust 功能刀起手順跑量測
- B-029｜captcha 強化包：「答對但登入失敗即自動換題」收進首版前端行為；產圖對抗性（干擾強度、字型多樣）續留觸發制（詳＝啟動書 §5.2 K2-21、承 rev4:B-075）｜captcha 沿用刀首版收 UX 半條
- B-030｜低位殘項群逐項內建 checklist：未刪選單列表分頁、契約測試對 query 零判別力、zh-cn 鍵集不在掃描面、320px 窄屏頁首溢出、自助頁雙卡同構重複、單一超管軟鎖自解的雞蛋相依、告警僅 webhook 單通道、機密清單三處人工同步（可考慮單一來源生成）（詳＝啟動書 §5.2 K2-22）｜重寫對應模組時逐項
- B-033｜樣板回灌帳（§3.2 條 16／Q14）：集中登記 docs-governance-template 的樣板缺陷與搬遷摩擦，rev5 收刀後一次批次回灌。已知內容＝①樣板 export 腳本未落致 rev5 手工搬運、樣板失去第一個真實檢驗機會 ②樣板 H 層把 Lint20 具名豁免表當既有設施而源碼實無（rev5 補建）③治理硬化四項顯式延後之邊界清單（lint 差分分級／ctags 符號漂移偵測／基線 freshness 提示／clean-tag 建置閘）應記其存在、防第三代重新發明（詳＝啟動書 §5.2 K2-18／K2-19）｜rev5 收刀後批次回灌
- B-040｜RUNBOOK §15.5 補「成員離開／持鑰人失聯」情境列（指向 §15.3 撤銷準則——只 re-key 不換值＝形式撤銷、必連帶輪替機密值本身——與 §15.6 輪替表；ADR 0015 子題二）｜首個維護批第一支
- B-041｜產第三把離線保管復原鑰（不綁任何開發機；B-038 產鑰工具→私鑰與 passphrase 離線保管→入 .sops.yaml recipients→updatekeys 回寫→解回驗收；封掉雙持鑰人同失 passphrase＝密文永久不可解之死路；ADR 0015 子題三）｜首個維護批第一支
