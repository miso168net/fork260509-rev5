<!-- next: B-034 -->
# BACKLOG — 待辦

條目格式 `- B-NNN｜<一句話>｜<觸發條件或期限（選）>`；配號取檔頭 next-id 後 bump、號碼永不回收；完成即刪列、git 即史。

- B-001｜評估 brainstorm 承襲盤點機器閘（lint 條款或 speckit plan 模板列，強制對照啟動書 §5 K1 清單）｜首刀（B12）跑完 Constitution Check 後檢驗實際需求再定
- B-002｜Lint18「merge SHA 不可解」紅訊息補去處（B8a 裁決員 D2 發現：只給病因無修法，違「紅訊息附去處」慣例；建議文案＝請以真實 merge commit SHA 覆寫該列、事件帳既有列不可改者改以新事件更正）｜首個維護批
- B-003｜memo 欄家族 UI 兌現——sys_user／sys_role／sys_menu／sys_ip_rule 四張管理列表的顯示欄＋編輯入口（語意：R_SUPER 備註用途、text 可多行；顯示於管理列表、不顯示於其它被取用處——下拉／引用／對外 API 不帶；rev4 設計入 schema 但各 UI 刀 brainstorm 均未兌現，語意權威＝001 刀 data-model）｜各對應管理 UI 刀 brainstorm 直接輸入
- B-004｜移植品前代 ADR 指涉清償（全量枚舉＝ports-2xxxx 批 reviewer 實測；枚舉命令 grep -rnoE 'ADR [0-9]{4}'、排除 .git/tmp/子庫/源倉/brainstorms/generated）——分流三路：①前綴化 `rev4:`（本項轄區）＝0072（docker-compose.yml reaper 註解、deploy/setup-reaper-role.sh）、0012（example node 釘版）、0080（deploy/decrypt-secrets.sh、preflight-secrets.sh）、0022（generate-dev-cert.sh、generate-secrets.sh）、0084（deploy/secrets/README.md、generate-age-key.sh）、0037（nginx _locations.inc）、0077（tools/docs-sync.py 五處）；②tools/schema-gate.py 之 0064/0063/0049/0039/0032 多處＝schema 基線刀整組重建轄區、本項不動；③.specify/memory/constitution.md 之 0085/0041＝查實形後另議（憲法修訂＝amendment 程序 ADR＋版本 bump、user 拍板）。①轄區補列（001 收刀 holistic 枚舉）：tools/entity-drift-gate.py 之 0015×6＋0021×1、.githooks/pre-commit 之 0015/0021、tools/docs-sync.py L1677 specs/002-schema-baseline 座標、rust-api main.rs 等 7 處「001-compose-stack env-secrets 契約」指涉（rev5 無此 spec 目錄、實為 rev4 側 019）。＋deploy/secrets/README.md 內 `$HOME/.cache/fork260509-rev4/secrets` 敘述改 rev5（功能面已驗零影響：腳本預設 deploy/secrets、.env 實值為 rev5 路徑）；連帶 LESSONS 入帳：B10 殘留掃描樣式 `rev4[-_]` 抓不到「rev4/」黏斜線形＝掃描樣式集缺口；連帶 README 常見問題表補一列「查埠／帳號／schema／畫面現況→`docs/generated/reference/` 五張正典表」（現行 FAQ 僅進度／歷史／決策三列、reference 只在樹狀圖帶過＝發現性缺口，user 2026-08-05 實際撞到）｜首個維護批
- B-005｜wf-watchdog.sh 加可選第二參數（wf transcript 目錄或 runId）支援硬編監看目標——「最新目錄」自動發現二次實彈鎖錯 run（2026-08-05 ports-2xxxx 批：ARMED 冒煙攔下、應急改掛 inline 復刻迴圈）；加參數後 CLAUDE.md §2 的 Monitor command 範本同步帶目標寫法｜下個維護批
- B-006｜schema-evolution.json 之 kind×detail 必備鍵表＋逐 kind 啟動斷言（analyze B2：現契約 detail 只驗非空、alter_column 零定形，壞形 entry 可滲入 gate1 合成；補「kind × detail 必備鍵」表升為斷言第 7 條＋八 kind 各一筆合法／缺鍵樣本自測；001 收刀擴充：detail 值域斷言一併入——pk 欄名 ⊆ COPY 欄集、pk/set 型別檢、同名 index/constraint 重複登記攔——四種壞形現逸出裸例外收 rc 1、應歸 rc 2）｜首筆真登記（E-001 之後、下一支帶 migration 的刀）前完備
- B-007｜三閘與治理工具效能門檻量化（analyze B5：「秒級」無量化、無 SC 承載；pre-commit 全鏈 20s 警戒／45s 硬擋之預算分攤明文化——新閘單跑上限與量測法入 contracts 或 RUNBOOK；001 收刀實測基準：無 gitlink 無 tools staged＝1.016s、staged docs-sync.py 觸發 428 案自測＝27s 越警戒未破硬擋——量測分兩情境各留值）｜001 刀收刀後首個維護批
- B-008｜四張 rev4 專屬管理頁 view 於 base-web 兌現——manage_system-settings／manage_policy-archive／manage_audit／manage_ip-rule（analyze D6：seed 選單與 casbin 政策隨 001 基線先行、`component` 指向之 view 於 rev5 base-web 尚不存在；期間該 4 項僅 R_SUPER 可見、點擊 404 屬已知態）｜各對應管理 UI 刀 brainstorm 直接輸入
- B-010｜data-model §2/§6 文件面 vs 凍結 fixtures 機器對賬（001 收刀 holistic：§2 型別/NULL/default 三欄與 §6 索引約束定義從未進機器比對面——gate2 欄序只解析欄名、型別面錨 fixtures；文件單邊被改不會被抓；三輪 review 各自寫過一次性 parser 證明可落地）｜首個維護批評估
- B-011｜gate2 seed normalize 擴充剝除 pg_dump 版本行與 Owner 註解行（001 收刀：比對面現含「Dumped from/by version 18.4」與 Owner 行——postgres 升版或 DB 身分再變即紅在純噪音、ADR 0008 那次即為 Owner 行連動重產 fixtures；契約級變更、gates.md §2＋fixtures 重產一次，宜與升版維護批同刀）｜postgres 升版前必做
- B-012｜audit 變體 B 禁欄判準拍板：前綴通配（gates.md §3 字面 updated_*/deleted_*）vs 具名四欄（工具 L750 現況）——前綴守門強但可能誤攔未來合法欄名；二擇一屬拍板級（001 收刀 triage 判定不宜順手拍）｜下一支動 schema-gate 的刀
- B-013｜schema-gate 測試覆蓋兩缺口：cmd_check 綠路徑離線測試（fake run 分派 fixtures 三節）＋照相三查詢與 docs-sync 逐字重複之「同構」機器斷言（讀源碼比對三常數位元相等）｜首個維護批
- B-014｜entity 對應層後端首刀前補強：15 檔 Relation 空 enum（data-model §6 兩條 FK 未映射）＋ActiveModel 慣例面——本刀驗收（build 綠＋drift 綠）不需要、server 刀消費時變真風險｜後端首刀（B12）brainstorm 直接輸入
- B-015｜Lint06 arch_impact 雙向比對基準疑與「活書隨刀改」流程矛盾（001 收刀實撞：§8 隨刀內 commit 新設、merge 時已含→merge→簿記零 delta→宣稱 §8 反被判「無實際變動」；工具比 merge:BOOK vs 簿記態、若語意為「本刀影響」應比 merge^1:BOOK——屬 lint 調規拍板；本次事件以 arch_impact=none＋notes 載實況通行）｜首個維護批
- B-016｜稽核資料生命週期一次入設計：retention 水平線語意＋清理動作同交易自記稽核＋自動排程＋逐表門檻，不走「先手動清理、後補自動化」（前代同域四次拍板／一次正式翻案／一次違憲重拍；rev5 稽核表結構已隨 001 基線壓平落地、政策面尚未設計；詳＝啟動書 §5.2 K2-01、承 rev4:ADR 0058／0075／0076＋specs/017-audit-retention）｜稽核功能刀
- B-017｜會話生命週期一次設計完整、直接以 DB-stateful rotation 終態起手（rotation＋reuse 偵測＋denylist 即時撤銷＋single-session＋精確 idle），不走「無狀態先行、下一刀翻案」兩段式（前代付兩次完整拍板＋一次破前刀交付契約；詳＝啟動書 §5.2 K2-02、承 rev4:ADR 0030→0033）｜auth 刀 brainstorm 直接輸入
- B-018｜前端 demo 資產去留一次拍：alova 第二請求棧、替代登入表單殼（seed 側 demo 選單與授權已由憲法 §I.2＋ADR 0005 收；前代全量保留衍生兩支 won't-fix 決策＋清理需 seed 移除白名單；詳＝啟動書 §5.2 K2-03、承 rev4:ADR 0029／0035／0036）｜前端首刀 brainstorm 直接輸入
- B-019｜信任錨傳輸層背書入首版評估＋部署 checklist 與錨同刀交付（前代安全保證整個壓在「部署方須鎖 origin 僅接受 CDN 邊緣連線」的文件約束上、硬化案至今未做；詳＝啟動書 §5.2 K2-04、承 rev4:ADR 0043）｜ingress／IP 閘刀 brainstorm 直接輸入
- B-020｜失敗計數節流做成可掛任意敏感端點的通用 seam（per-user／per-IP），不綁死登入流程（前代改密端點無法直掛成獨立缺口、軟區永不被第一層快取短路；輕量範本＝原子先佔 SET NX→INCR→超限拒→best-effort 回補；詳＝啟動書 §5.2 K2-05、承 rev4:ADR 0037／0038→0045）｜節流刀 brainstorm 直接輸入
- B-021｜改密端點舊密暴力試節流（掛點在 argon2 之前、成功改密清計數、需新業務碼；殘餘拍板點＝redis 故障 fail-open 或 fail-closed、門檻走設定鍵或常數；詳＝啟動書 §5.2 K2-08、承 rev4:B-102＋specs/014-user-center／015-pwd-custody）｜auth 設計期內建、或列第一批補完
- B-022｜替代登入四流程做真或砍表單一次拍：驗證碼登入／註冊／重設密碼三張表單後端仍 stub、自助頁手機驗證為佔位控件（信箱半邊資產可平移、簡訊通道選型屬新拍板；已橫跨三代未收；詳＝啟動書 §5.2 K2-09、承 rev4:ADR 0029／0085／0086）｜沿用同款登入頁時開場即拍
- B-023｜備份自動化：排程 pg_dump＋卷快照＋還原演練＋機密檔與資料卷的配對備份（前代零工具致 RUNBOOK 破壞性驗證被迫跳過＝備份缺席在限制驗證能力；rev5 事件帳與稽核表自 Day 1 累積價值；詳＝啟動書 §5.2 K2-11、承 rev4:B-107）｜早期治理批（不宜留到 prod 前夕）
- B-024｜寫端授權下放非超管前置三件套：no-escalation 上限檢查、seeded 受保護護欄與「超管恆禁停用」結構護欄複評、業務錯誤明細通道受眾邊界重評（詳＝啟動書 §5.2 K2-12、承 rev4:B-083＋specs/009-role-admin）｜role／user 管理刀（目標含多層管理員即入首版）
- B-025｜軟刪×授權歸檔一致性通用掃描（選單／角色／使用者各軟刪路徑下 casbin 碼與選單按鈕欄聯集），宜與背景 job 底座同刀首發（詳＝啟動書 §5.2 K2-13、承 rev4:B-100）｜背景 job 底座刀
- B-026｜部分更新契約的通用顯式 clear 語意——三態（欄位缺席／清空／設值）於 wire 契約設計期一次定形（前代 null＝整欄跳過、「清回 NULL」無通用語意，僅 user 域以空字串部分兌現；詳＝啟動書 §5.2 K2-14、承 rev4:B-026）｜wire 契約設計期
- B-027｜列表欄位排序能力＋排序欄白名單三端單一來源（或 parity 檢查）＋per-column 索引評估（前代全數後端預設排序、白名單分散三端靠人工同步；詳＝啟動書 §5.2 K2-15、承 rev4:B-036）｜首個排序需求刀
- B-028｜後端開發體驗兩缺口：容器內 cargo build 時間基線量測（雙機冷編＋單檔增量，作為 dev profile debuginfo 裁剪的數據前提）＋sea-orm additive DDL 草稿生成輔助（entity 漂移閘已隨治理套件搬運兌現；詳＝啟動書 §5.2 K2-17、承 rev4:B-109／B-110）｜第一把 rust 功能刀起手順跑量測
- B-029｜captcha 強化包：「答對但登入失敗即自動換題」收進首版前端行為；產圖對抗性（干擾強度、字型多樣）續留觸發制（詳＝啟動書 §5.2 K2-21、承 rev4:B-075）｜captcha 沿用刀首版收 UX 半條
- B-030｜低位殘項群逐項內建 checklist：未刪選單列表分頁、契約測試對 query 零判別力、zh-cn 鍵集不在掃描面、320px 窄屏頁首溢出、自助頁雙卡同構重複、單一超管軟鎖自解的雞蛋相依、告警僅 webhook 單通道、機密清單三處人工同步（可考慮單一來源生成）（詳＝啟動書 §5.2 K2-22）｜重寫對應模組時逐項
- B-031｜★拍板待答：prod 是否入 rev5 roadmap——若入，prod 部署包（部署 checklist＋CDN origin 防火牆鎖定、prod CSP 收緊、GeoIP 資料檔 COPY、加密檔分層與至少兩把 recipients、多副本 LB 拓樸）升格為正式刀與自動化驗收，而非散裝待辦（前代二十刀內零落地＝無 prod 資產與 CI 母體、結構性不可測；詳＝啟動書 §5.2 K2-10）｜user 拍板（B12 前後擇期）
- B-032｜★拍板待答：團隊組成前提是否已變（「將來可能有非工程師」）——成立即重啟機密選型（工程師層維持 SOPS 密文入版控／非工程師層另設不持金鑰的 GUI 取用面，兩層間橋接角色是新的信任集中點須連同設計），明文「觸發即重啟選型、不是在現有方案上補 GUI」；個人密碼管理器四反轉條件原樣過境（詳＝啟動書 §5.2 K2-20、承 rev4:ADR 0083）｜user 拍板
- B-033｜樣板回灌帳（§3.2 條 16／Q14）：集中登記 docs-governance-template 的樣板缺陷與搬遷摩擦，rev5 收刀後一次批次回灌。已知內容＝①樣板 export 腳本未落致 rev5 手工搬運、樣板失去第一個真實檢驗機會 ②樣板 H 層把 Lint20 具名豁免表當既有設施而源碼實無（rev5 補建）③治理硬化四項顯式延後之邊界清單（lint 差分分級／ctags 符號漂移偵測／基線 freshness 提示／clean-tag 建置閘）應記其存在、防第三代重新發明（詳＝啟動書 §5.2 K2-18／K2-19）｜rev5 收刀後批次回灌
