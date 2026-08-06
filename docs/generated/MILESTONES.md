<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# MILESTONES — 全事件表（最新）

| date | type | 標的 | summary | merge | adrs | arch |
|---|---|---|---|---|---|---|
| 2026-08-04 | misc | — | rev5 創世（波 -1 文件地基）首批 commit：治理工件直搬（sha256 血緣斷言）＋條款裁改 23 條＋骨架六件＋憲法 v1.0.0（user 親審定版）＋機密管線（sops×age）就位；ADR 0001（創世採用）／0002（白名單反轉延後）／0003（佔位字面白名單）同批 accepted | — | — | — |
| 2026-08-05 | misc | — | 維護批 ports-2xxxx 收單：host 埠 5xxxx→2xxxx 世代錯開（ADR 0004 翻案啟動書 §4.5.9 拍板值；動機＝macOS ephemeral 範圍佔埠致機率性 bind 失敗、世代區隔降位為約束條件）；compose 兩檔＋RUNBOOK §14＋docs-sync 三處裸 0019 指涉同刀跟正；ports 真表重算 12 埠全 2xxxx；殘留掃描零、postgres+redis 實起實聽驗證 | — | — | — |
| 2026-08-06 | feature_close | 001-schema-baseline | 波 0 schema 基線刀收刀：m001（15 表 169 欄＋索引 38 約束 101）＋m002（266 列 seed 完全決定性）＝rev4 終態壓平＋user 定稿制；三閘重建＋Day-1 受管演進帳＋fixtures 先驗後凍；entity 15 檔＋refresh 首跑＋拔項＋真表首算＋drift 實跑；ADR 0005~0008（0008＝DB 身分無世代後綴回滾）；quickstart A–E 全跑 SC-001~006 全達成；final holistic review 零 blocker | 6a4696f373c2bf57199c6dccf71afb158708a500 | 0005、0006、0007、0008 | none |
| 2026-08-06 | misc | — | 創世收官（B8b＋B11）：移植驗收後段全過——bootstrap 幂等零改動＋生成檔八檔全刪逐位元重算＋假 feature 以 001 真刀充抵＋router／msg_dict 兩表拔項突變實證；K1／K2 處置流水總帳 ADR 0009 accepted——K1 改隨刀重審機制、K2 二十二筆三分流（15 轉 BACKLOG／2 拍板待答／5 創世期已兌現）＋樣板回灌帳 B-033 開立；創世 DoD 全數關帳 | — | — | — |
| 2026-08-06 | misc | — | sops wrapper 單檔選鑰修正（輕量軌）：加人致 recipient 1→2 後跨代並存機 decrypt 失效——wrapper 掛整個 ~/.config/sops/age 使容器內存在兩把 identity，sops 遂對「每 recipient× 每鑰」各索一次不可見 passphrase、任一次空答即整體失敗且訊息指向錯方向；改為單檔掛到容器內預設尋鑰路徑、容器內恆恰一把 identity。decrypt 預告行改自密文現算 recipient 數、不再寫死「恰 1 次」；RUNBOOK 四節與 generate-age-key.sh 訊息同步；L-005 入帳 | — | — | — |
| 2026-08-06 | misc | — | bash→python 選擇性轉換評估收束：5-agent workflow 逐檔實查全 repo bash 面 24 支 4164 行＋grilling 19 題逐題拍板；定案＝選擇性轉 5 支（10.3~12 人日 vs 全轉 26.8）、stdlib-only與等價驗收兩硬約束、hooks 全組／bootstrap 等 16 支明文不做、age 產鑰改容器化、外部工具版本三分類政策（一次性輔助工具沿 latest）；產出＝ADR 0010/0011＋B-035~B-039＋B-004/B-005 補記 | — | — | — |
| 2026-08-07 | misc | — | 前代裸編號全樹審計收束＋七題拍板：6-agent workflow 逐筆判定 881 筆（機械 740 零缺口＋人工補掃 141）——foreign 621／68 檔、gray 93 歸邊；撞號已實發（nginx 裸 B-037 對撞 rev5 已配號 B-037）、近兩 commit 新引入 7 筆＝防復發必要性實證；拍板＝血緣前綴 rev4:/rev3:/rev2:、裸刀號只加前綴、逐 token 合規、fixture 遷假號段、LESSONS 勘誤級可修／events 不動、已收刀 spec 限前綴化可動、Lint25 與清償同刀；產出＝ADR 0012＋B-004 射程改寫 | — | — | — |
| 2026-08-07 | misc | — | Lint25 跨代裸編號閘上線（ADR 0012 決定 7；B-004 防復發面）：19 族樣式單 pass＋registry 掃源現算＋防恆綠自測＋具名豁免七類；day1 降級 WARN、清償完轉 ERROR；bootstrap 名冊斷言改「末筆 lint-roster 勝」（append-only 帳的條款入冊通道＝append 新事件、絕不改創世列）；本筆即新名冊承載事件 | — | — | — |
| 2026-08-07 | misc | — | B-004 前代裸編號全量清償收單（輕量軌 maint-b004）：Lint25 上線→六批 agent 並行清償（A188/B190/C74+假號段80/D21/EF39/G25）→總審 48 筆殘留逐筆歸因全數收斂（判定收斂＋豁免補齊、漏改 0）→docs-sync 自身 136 處兜底→轉逐筆 ERROR；血緣前綴 rev4:/rev3: 逐 token、grafana uid 與七類 mention 具名豁免；批I 子庫 main.rs 前綴化＋pin bump | — | — | — |
