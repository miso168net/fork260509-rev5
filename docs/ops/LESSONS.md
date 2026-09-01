<!-- next: L-081 -->
# LESSONS — 教訓索引

一坑一檔住 `LESSONS/L-NNN-<slug>.md`（append-only；配號取檔頭 next-id 後 bump、號碼永不回收；
引用一律用 ID、與檔名無關——檔名只是住址）。本檔＝索引：每條恰一行、形＝
「- ［L-NNN｜坑名］（LESSONS/L-NNN-<slug>.md） — 防法 hook」（此處全形括號示意、實際行用
半形連結形；雙向對賬與唯一性＝Lint26、連結存在＝Lint12）。
條目檔規格：frontmatter **必填 `promoted_to:`**（★晉升必答——防法晉升到哪個操作面：
CLAUDE.md／quickstart／碼註／lint／防呆件套；無處可晉升寫「無：<理由>」。未晉升的教訓
＝寫完即死，2026-08-17 審計實證：真正生效的教訓全數經晉升面進場、零次「動手前查本檔」）；
正文首行維持 L-NNN｜起手形（Lint09 計數面、勿改；L-001~L-003 裸段形照舊）；防法建議**前置**
（advisory——機器強制面由 hook 行雙向對賬承載）。★`promoted_to` 不得指向 per-machine
memory 路徑（repo 硬禁令：repo 文件不引用家目錄 .claude 類路徑）。
rev5 只記親歷坑；前代候選＝啟動書 §5 K3。★**動手前掃一遍本索引**（≈一分鐘）。

- [L-001｜bash 3.2 下 $VAR 後緊接全形字＝黏進變數名](LESSONS/L-001-bash-fullwidth-glues-varname.md) — `$VAR` 後緊接非 ASCII 一律 `${VAR}` 包裹；機器枚舉全 repo bash 面逐處處置、不靠「跑過一次沒事」
- [L-002｜扁平 grep 抽 jsonl key 撞巢狀 payload 同名鍵](LESSONS/L-002-flat-grep-hits-nested-payload-keys.md) — 判準抽取一律頂層鍵定錨（逐行 JSON 解析、只取事件物件 top-level 欄）、絕不對含巢狀 payload 的 jsonl 扁平 regex 計數
- [L-003｜「移植清單照單施工」≠已拍板；勘誤只修被點名處＝同病二暴](LESSONS/L-003-checklist-is-not-approval.md) — 拍板級條目施工前先查拍板紀錄、查無＝先問；勘誤一律 errata 機器枚舉全 repo 逐處處置
- [L-004｜移植品的「不一致」可能是前代刻意的防禦性慣例](LESSONS/L-004-inconsistency-may-be-deliberate.md) — 改移植品既有寫法前先兩查（rev4 對應檔怎麼寫＋教訓帳有無此主題）；repo 內部一致性不構成修改理由
- [L-005｜以當時基數寫死的互動預期（「恰跳 1 次提示」）在基數變動日失效](LESSONS/L-005-interaction-count-hardcoded-at-baseline.md) — 次數類互動預期由腳本自資料現算後印預告行、不落字面；不可見互動的面積收斂到最小
- [L-006｜殘留掃描「零命中」只證所列樣式零命中、不證該找的形都找了](LESSONS/L-006-residue-scan-pattern-set-incomplete.md) — 世代字串掃描必同列三形（連字號後綴／黏斜線路徑段／裸詞邊界）；先證樣式集完備、再證命中為零
- [L-007｜splitlines() 重組整檔把 U+2028／U+2029 靜默摺成換行](LESSONS/L-007-splitlines-eats-unicode-separators.md) — 整檔機械改動用 str.replace 或 split("\n")；改完必 ast.parse 自證
- [L-008｜單向書寫的判讀規則在反向情境導向破壞性操作](LESSONS/L-008-one-way-rule-reversed-is-destructive.md) — 凡寫「一律 X」先問反向情境存在嗎；存在就雙向寫並給機器判準（merge-base --is-ancestor 三態）
- [L-009｜serde 預設 Deserialize 下 Option<Option<T>> 三態塌兩態](LESSONS/L-009-serde-double-option-collapses-tristate.md) — 三態欄必配 deserialize_with 自訂函式；照型別字面實作後以缺席／null／值三形測試自證
- [L-010｜守門判準對某類變動結構性無感＝閘恆綠（四種致因）](LESSONS/L-010-gate-structurally-blind-stays-green.md) — 結構斷言優先於數量斷言；每個閘落地配一次非 vacuous 自證（弄壞→紅→還原→綠）
- [L-011｜編排 script 把已完成的工作誤報成失敗](LESSONS/L-011-workflow-misreports-finished-work.md) — 狀態欄不得跨角色複用；fix 迴圈跑滿必有確認輪——回報必須反映最後一次動作之後
- [L-012｜submodule 內檔案在外層 repo 還原＝靜默零還原](LESSONS/L-012-submodule-restore-needs-git-c.md) — 子庫 git 操作一律 git -C <子庫>；破壞性驗證每項還原後立即 status --porcelain 機器確認、單獨跑不疊加
- [L-013｜DatabaseConnection::Disconnected 在 get_database_backend() 是 panic 不是 Err](LESSONS/L-013-disconnected-panics-not-errs.md) — 「查庫必失敗」替身自寫 ConnectionTrait impl（FailingConn）；判斷替身看被測路徑實際呼叫哪些方法
- [L-014｜啟動書 K 條目的裸 B／L 編號屬 rev4 命名空間](LESSONS/L-014-bare-ids-in-kickoff-are-rev4.md) — 讀啟動書凡見裸編號預設 rev4 號、拿語意比對不拿號；落在 rev5 已配區間「查得到」才最危險
- [L-015｜自製彙總腳本本身是假綠來源；真 DB 走查等同 runtime 寫入](LESSONS/L-015-homemade-tally-fakes-green.md) — 測試結論一律看 exit code、不看彙總數字；任何 runtime 寫入後立刻收尾清列、不跨單元邊界
- [L-016｜.ok() 吞掉「交易已毒化」腿、COMMIT 被 PG 靜默降級成 ROLLBACK 卻回 Ok](LESSONS/L-016-ok-swallows-poisoned-txn.md) — txn 內呼叫「查庫失敗與純判斷失敗壓成同一錯」的函式不得 .ok()——要嘛 ? 出去、要嘛移到 commit 後交易外讀；問「吞得到的最壞腿是什麼」
- [L-017｜「修好一支 flake」≠「模組不再 flake」；零餘裕時間斷言有兩個 ±1 秒級來源](LESSONS/L-017-fixed-one-flake-not-zero-flakes.md) — flake 驗收＝模組連跑數十次零紅；時間斷言上界帶明示餘裕常數；PG ::bigint 是 round 不是 truncate
- [L-018｜收尾只寫 commit message、不落帳不勾 tasks＝知識鎖進 git 史](LESSONS/L-018-ledgerless-closeout-locks-knowledge.md) — 單元收尾第③步固定落帳（BACKLOG／LESSONS append＋tasks 全勾）且必早於 generate；判準＝「下一個人查得到嗎」
- [L-019｜降級腿測不到＝上游同源故障先攔截（構造壞 X 時所有讀 X 的上游先壞）](LESSONS/L-019-upstream-intercepts-degraded-leg.md) — 經 HTTP 面構造不出的降級腿直呼私有 fn 取覆蓋；有論證必有紅綠載體；補守門必做變異測試
- [L-020｜守門取「安全距離外」的值＝測的是功能存在、不是參數被設成 X](LESSONS/L-020-probe-the-discriminating-boundary.md) — 取值貼著 X 與函式庫預設值之間那條界線；先查預設值再設計判別值；補完做變異測試
- [L-021｜rc=1（工具拒跑）與 rc=101（測試真失敗）意義相反](LESSONS/L-021-exit-code-layer-matters.md) — 非零先看第一行輸出——error: 開頭＝工具層、FAILED／panicked＝測試層；迴圈跑測試連首行錯誤一併印
- [L-022｜tasks.md 涉檔列會漏結構上必需的檔、照抄＝把缺口抄進允許清單](LESSONS/L-022-task-file-list-is-not-the-truth.md) — 開單元前對每個 task 問「它 import／呼叫／宣告的東西現在存在嗎」；agent 回 blocked 先判清單缺口；撞到就回頭修 tasks.md
- [L-023｜resumeFromRunId 續跑時看門狗 ARMED 行的冒煙位元組數是前一輪殘留](LESSONS/L-023-resume-smoke-bytes-are-stale.md) — 續跑冒煙改看最新 agent 檔（mtime＋grep 本輪新字串）；先想清楚改動會不會讓 (prompt, opts) 真的改變
- [L-024｜middleware／fallback 組裝次序是行為不是風格——次序錯不編譯紅](LESSONS/L-024-middleware-order-is-behavior.md) — 鏈序用走真 build() 的 contract 行為測守、不用裸掛合成 router 反例；問「掃的是掛當下快照還是終態」
- [L-025｜免 DB 契約測的前提對 Public route 結構性破裂](LESSONS/L-025-no-db-premise-breaks-on-public-routes.md) — 契約案斷言強度依「該 route 在 stub 下走到哪一層」分級；寫新案先問第一個 DB 觸點在哪、勿照抄隔壁案
- [L-026｜redis TTL 讀回值會大於 SET 秒數（牆鐘後跳）](LESSONS/L-026-redis-ttl-reads-above-set-value.md) — SET 後讀 TTL 的斷言上下界各帶同一顆具名餘裕常數；複跑全綠須同時證明環境效應仍在發生
- [L-027｜resumeFromRunId 是故障續跑用、不是「讓某支 agent 重跑」的手段](LESSONS/L-027-resume-is-not-a-rerun-switch.md) — 需某階段重跑＝新開一支只跑該階段的 workflow（新 runId）、CONTEXT 寫清已完成結論與勿重報清單
- [L-028｜「對稱釘子＝那支測試」的註解若該測不經本函式＝vacuous 高階變形](LESSONS/L-028-symmetry-pin-off-the-call-chain.md) — 寫對稱釘子註解先確認該測試的呼叫鏈真經過本函式；反例值挑能穿透兩把尺差集的
- [L-029｜帳面測試數是收刀當時快照、當「零回歸」判準跨批次必失真](LESSONS/L-029-test-count-snapshot-not-baseline.md) — DoD 與 agent prompt 不寫死測試數、改寫量測法（動工前後同一指令逐 target 比對）；引數字必附量測日期＋指令
- [L-030｜射程／職責一搬動、敘述面沒跟著搬＝靜默失效](LESSONS/L-030-moved-duty-stale-narrative.md) — 搬動職責同一次編輯把接收方 task／DoD 也改掉；守門射程敘述與射程常數同批改；prompt 引實碼常數不引 docstring
- [L-031｜走查在共用 dev 庫留下的 committed 列毒化下一次測試、證據自毀](LESSONS/L-031-walkthrough-rows-poison-tests.md) — 走查即清（每節 DoD 寫入清列指令）；收尾看 rc 必排在清列之後；「在收窄集內」不可推論成「留列無害」
- [L-032｜執行單元允許檔清單天然擋住「修正被自己證偽的他處敘述」](LESSONS/L-032-file-boundary-blocks-cross-file-errata.md) — 凡改變數字／集合／方向／權威＝grep 枚舉全 repo 逐處回報，清單外依④分值升級；史述保留、現在式改對
- [L-033｜兩檔各存同一字面＝生產端改名靜默反轉行為、字面驅動守門擋不住](LESSONS/L-033-duplicated-literal-drift.md) — 一階＝生產端匯出具名常數兩邊消費；否則斷言消費生產端實際產物、測試本體零字面
- [L-034｜建連逾時罩不到連線之後——半開連線讓長生串流零告警永遠掛著](LESSONS/L-034-connect-timeout-misses-half-open.md) — 長生訂閱／串流另開 TCP keepalive 或應用層心跳；「有逾時」與「有存活期偵測」分開問
- [L-035｜blocked 語意重載＝交付完整的單元整個審查階段零輪次](LESSONS/L-035-blocked-overload-skips-review.md) — status 分 blocked／done_with_escalation 兩值、只有前者立即 return；徵狀＝完成通知 agent_count=1
- [L-036｜「斷言副作用不發生」的測試平常全綠、紅的那一次弄髒共用庫](LESSONS/L-036-negative-assertion-leaks-on-red.md) — 清理 MUST 覆蓋「副作用真的發生了」那條路徑；測試名含 no_side_effect／does_not_create／precedes_ 一律複查
- [L-037｜用某論據駁倒替代案後、沒回頭檢查所選方案是否中同一刀](LESSONS/L-037-rejection-argument-hits-the-chosen-too.md) — 棄案論證寫完 MUST 對所選方案跑同一個反例；寫「結構性保證」前先找一條讓它不成立的輸入
- [L-038｜更正只附加不改原句＝同段自相矛盾；勘誤關鍵詞取自更正文必漏同義複本](LESSONS/L-038-append-only-correction-misses-synonyms.md) — 更正一律就地改寫；勘誤枚舉取概念的同義集、同批掃 src/**（碼側 rustdoc 是定義權威位）
- [L-039｜決策對、記下的理由是未查證推測——錯誤理由會被拿來推翻正確決策](LESSONS/L-039-wrong-reason-invites-reversal.md) — 碼註寫「不這樣做會 X」則 X 必是查證過的事實、查不動就寫「推測、未驗」；覆核時理由和結論分開驗
- [L-040｜守門住 shell／設定面時、工具 self-test 擋不住「根本沒被跑」](LESSONS/L-040-self-test-cannot-see-unwired-hook.md) — 接線守必須住別處（TestGateWiring 乾跑真 hook）；驗收必兩道變異——拆段紅＋Day-1 條件反轉紅
- [L-041｜走查殘留不只在 DB——redis 節流計數（TTL 自毀）與還開著的登入分頁](LESSONS/L-041-walkthrough-residue-beyond-db.md) — 跑全量前先關走查分頁、必要時清 redis 節流鍵；「重跑就綠」永遠先當殘留、不當 flaky
- [L-042｜允許檔清單從 task 文字建就一定會漏——task 寫「做什麼」、清單要答「碰得到什麼」](LESSONS/L-042-file-list-from-prose-always-leaks.md) — 動工前三問對實碼查——值域容得下嗎／新欄位有 Default 嗎（建構點全 grep）／新事實有誰消費；寧可多列
- [L-043｜文件裡的「預告」是會過期的斷言——寫下當時是對的才難察覺](LESSONS/L-043-doc-forecasts-expire.md) — 預告必標成預告＋附回填義務、該刀 tasks 同批加回填條；覆核把「屆時／日後／將由」當同義集掃
- [L-044｜驗收程序寫好了、使它成立的設定從未存在——兩邊各自看起來都沒問題](LESSONS/L-044-acceptance-without-its-premise.md) — 驗收程序與環境前提成對交付且前提實跑過；fail-safe 模組「已載入」須有正向訊號；每步問「需要哪個設定、在哪個檔」
- [L-045｜清理義務被私有 fixture 就地解掉＝全域性被藏起來](LESSONS/L-045-cleanup-duty-hidden-by-private-fixture.md) — 名冊 MUST 由 grep 產生；複合判準分開枚舉取聯集；義務屬路徑就上移共用設施
- [L-046｜「已知態」記成單一症狀＝煙測驗一條沒人走的路](LESSONS/L-046-known-state-needs-observation-path.md) — 記已知態必寫觀察路徑；煙測判準路徑＝使用者路徑
- [L-047｜前端表單擋下＝零請求零 toast、與後端掛了同形](LESSONS/L-047-form-validation-mimics-dead-backend.md) — 排查後端行為前先證明請求發出去了（Network.requestWillBeSent）
- [L-048｜引用的計數「出生時就錯」比「後來漂了」更難抓（碰巧對＝最毒的形）](LESSONS/L-048-quoted-counts-need-machine-recount.md) — 引量前先機器數且數對物件（表邊界）；歷史時點用 git show 重數；他人寫的計數一律當主張不當事實
- [L-049｜Workflow launch 被擋後，無目標看門狗鎖上一支舊 wf 目錄](LESSONS/L-049-watchdog-locks-stale-wf-dir.md) — launch 失敗即 TaskStop 已 armed 的看門狗、重發後帶明確 runId 重掛；ARMED 行冒煙命中=0＋run id 不對＝鎖錯標的
- [L-050｜dev stack 真登入 smoke 後緊接全量測試＝throttle 家族暫態紅](LESSONS/L-050-login-smoke-residue-flakes-full-suite.md) — 手動 smoke 排在全量之後（或先等窗期/清 redis 鍵）；暫態紅當輪立刻截獲失敗名單、rerun 前先存 log
- [L-051｜wf-watchdog 的 stall 判定源（journal）沒有心跳、只在 agent 邊界寫入](LESSONS/L-051-wf-watchdog-journal-no-heartbeat.md) — 完成通知一到立即 TaskStop（run 後 journal 永不再動＝必誤報）；stall 閾值語意＝agent 邊界間隔上限、非無活動時間
- [L-052｜編排單元允許檔案清單漏列「連動釘值測」所在檔＝implementer 正確 blocked、多跑一輪審查 run](LESSONS/L-052-allowed-list-misses-pinned-count-tests.md) — 寫 ALLOWED 前先 grep 本單元會改動的計數／常數在全樹的釘值測檔、一併納入（限釘值段）
- [L-053｜`pnpm gen-route` 不是 elegant-router 產物四檔的重算指令（互動腳手架、零寫檔）](LESSONS/L-053-gen-route-is-not-the-regenerator.md) — 重算＝dev server 外掛自動（核 git status 四檔變動）＋route-artifact-gate check
- [L-054｜CDP 走查回報的「無可觀察實例」與「契約豁免」兩類理由不附機器反證＝等同未驗](LESSONS/L-054-cdp-unverifiable-claims-need-counterevidence.md) — 驗證審查對此類步驟必令 redo：附 psql／grep 反證或原文行號，否則不得記已知態
- [L-055｜CDP／手動真登入殘列 × AUTH_SEQUENCES setval(1,false)＝下一輪全量 23505；schema-gate 複驗綠≠環境已還原](LESSONS/L-055-runtime-append-residue-blows-next-full-suite.md) — 走查後 DELETE sys_token／session_event／sys_login_attempt＋三 seq 復位（quickstart §4 已晉升）
- [L-056｜清理守衛的 setval 還原把 create 形測試的 nextval id 釘成跨執行定值＝走查造得出同 id 的孤兒稽核列](LESSONS/L-056-seq-restore-pins-nextval-id-to-a-constant.md) — 稽核斷言窗形判準改寫：不是「鍵是不是 seed id」而是「這個 id 走查造不造得出」（nextval id 造得出、顯式大 id 段造不出）
- [L-057｜派生「只跑某階段」的續跑 script 時，冒煙 token 隨 IMPL_PROMPT 一起蒸發（ARMED 照出、命中=0）](LESSONS/L-057-derived-stage-script-drops-the-smoke-token.md) — 冒煙 token 提到所有 prompt 共用段、渲染斷言比照 zh-TW 一併檢查
- [L-058｜以手擬 grep 代替 errata 驗「零殘留」，樣式比實際措辭窄就漏改，留下同檔自相矛盾兩句](LESSONS/L-058-hand-grep-is-not-errata.md) — 勘誤一律跑 tools/docs-sync.py errata <關鍵詞>；要自擬也只能取最短公共子串
- [L-059｜兩視圖守門 lint 須逐 byte 對齊；「rustfmt 保證一欄一行」因本 repo 的 use_small_heuristics=Max 而不成立](LESSONS/L-059-two-view-lint-must-share-byte-coordinates.md) — 常值逐 byte 換白的結構視圖＋按精確 (起,迄) 圈界取屬性字面，另配視圖對齊的前提自證測
- [L-060｜暫改真檔驗紅後，用 git checkout 還原＝連同該檔其它未 commit 改動一起丟](LESSONS/L-060-restore-temp-mutation-without-git-checkout.md) — 存原文→寫回，還原後以 git diff --name-only 證零殘留；禁令要連替代作法一起寫
- [L-061｜base-web 的 pnpm install 會覆寫外層 .githooks-submodule，機密掃描整段消失且失效是靜默的](LESSONS/L-061-pnpm-install-overwrites-outer-githooks.md) — 跑過 pnpm install／typecheck 的單元，收尾第一件事是 bootstrap 體檢或六步 hooks 複驗
- [L-062｜drvfs 上治理工具的耗時是 I/O 稅不是邏輯（587×、9p 並發有效 6.33×）——憑直覺列的優化清單會全數落空](LESSONS/L-062-drvfs-io-tax-dominates-hook-time.md) — 優化治理工具前先 cProfile 分 I/O 稅 vs 邏輯（手法＝並行派發／作用域快取／EAFP）；symlink 到 drvfs 的路徑不是原生副本、當 performance-sensitive path 零收益
- [L-063｜開新 ★軌道用途時當場做的「新列變異自證」結構性 vacuous（尚無標記可比、回綠像有效）](LESSONS/L-063-new-track-purpose-mutation-test-is-vacuous-before-markers.md) — Amendment 只宣稱「機制已驗（拿已有標記的既有列反證）」，新列真自證排進第一個落標記的實作單元；通則＝變異前先確認被守面已有實例
- [L-064｜AppError::Biz/BizData 的 match 臂寫成 `(..)` 會被 Lint24 判成無法靜態解析的構造點，而 cargo 全綠時看不見](LESSONS/L-064-lint24-bizdata-match-arm-must-be-two-underscores.md) — 臂一律寫 `(_, _)`；rust 單元收尾的自驗必須含 `docs-sync.py lint`，cargo 綠與 lint 綠是兩件事
- [L-065｜對破壞性守門做變異測試會真的破壞 seed 列，而刪除式清理守衛結構上救不了](LESSONS/L-065-destructive-guard-mutation-really-destroys-seed.md) — mutate 型測試改掛快照還原式守衛（SeedUserRestoreCleanup）；判別問句＝這支測失敗時庫裡是多出東西還是變掉東西
- [L-066｜「應該被拒」的負向樣本也要帶清理鍵前綴，否則守門被改壞那一發的殘列圈不到](LESSONS/L-066-negative-samples-need-cleanup-key-prefixes.md) — 用「帶前綴但仍違規」的構造（uniq_key 加違規尾綴）；判別問句＝這個樣本沒被拒會在庫裡留下什麼
- [L-067｜Lint25 的「執行單元輪次」形連本代的刀號＋輪次寫法都判紅，而改寫成刀名全形會踩另一個形](LESSONS/L-067-lint25-unit-round-shape-traps-current-generation-too.md) — ops 帳本一律寫「本刀 U2」；判準是「長得像不像那幾個 regex」而非「是不是跨代引用」
- [L-068｜agent 保險絲低於 script 的結構最壞值時會在健康的 run 上開火，且必定開在最後一支](LESSONS/L-068-agent-fuse-below-structural-worst-case-fires-on-healthy-runs.md) — 由同檔常數推導＋自我斷言（WORST = 實作支數 + cycle 數 × (2·MAX_FIX_ROUNDS+1)）、不得手挑；通則＝安全邊界要從它所守的東西推導
- [L-069｜可見性放寬把既有名冊閘的射程打穿、全樹零紅點](LESSONS/L-069-visibility-widening-punches-through-a-roster-gate.md) — 改可見性前先 grep 函式體內有無被 token 掃描閘守著的呼叫；有就同批補一道消費者名冊閘、兩閘 doc 互相指路
- [L-070｜shell cwd 跨呼叫持久化，在傘狀 repo 裡把路徑錯誤偽裝成「檔案不見了」](LESSONS/L-070-shell-cwd-persists-across-calls-in-an-umbrella-repo.md) — 子庫一律 `git -C`、非 git 指令用絕對路徑；路徑類錯誤先 `pwd` 自證位置再談對象
- [L-071｜教訓晉升到下一刀的一次性文件＝半衰期只有一刀（L-055 六天後原樣復發）](LESSONS/L-071-a-lesson-promoted-into-the-next-one-shot-doc-has-a-one-blade-half-life.md) — 走查前取全表基準、後逐值比對（不變式取代清單）；清理面與閘的射程無關；寫 promoted_to 先問「這位置的讀者是不是下一個踩坑的人」
- [L-072｜刪 BACKLOG 條目沒掃引用，當場造出指涉斷鏈](LESSONS/L-072-deleting-a-backlog-entry-without-sweeping-its-references.md) — 刪列後雙向掃現在式文件家族；判準＝「這句在說曾經，還是在說現在還沒做」（歷史記述正當、待辦式引用才是斷鏈）
- [L-073｜變異探針從 repo 外載入 mutant，現況驗收案整批靜默 skip](LESSONS/L-073-mutation-probe-loaded-outside-repo-skips-live-cases.md) — 就地變異或改寫 ROOT；紅證必印 skipped=0
- [L-074｜pg_isready 不帶 -h 對初始化期只聽 unix socket 的暫時 server 回綠，restore 撞上重啟](LESSONS/L-074-pg-isready-without-host-flag-greens-on-init-temp-server.md) — 就緒探測一律 `-h 127.0.0.1`（TCP 就緒＝最終 server）；手寫 postgres 等待迴圈前 grep 本 ID
- [L-075｜允許清單裡的「限定式項」被越界時 agent 不觸發分值升級——它判「檔在清單內」就是沒越界](LESSONS/L-075-scoped-allowlist-entry-overrun-skips-escalation.md) — 限定式清單項附一句「本檔之限定外改動＝清單外、走 done_with_escalation」；主線復核看 `git diff` 實際改動面、不看 `escalations` 欄下結論
- [L-076｜枚舉同語意命中時用 `grep -v` 過濾整行，會漏掉同行雙 token 的那筆，且漏掉的看起來像不存在](LESSONS/L-076-line-level-grep-filter-misses-dual-token-lines.md) — 逐行剝 token 再判、不整行過濾；枚舉筆數要有第二來源對賬
- [L-077｜「逐欄對賬 schema 真源」只驗欄名與存在性、漏驗可空性，型別失真整條穿過復核](LESSONS/L-077-column-parity-check-that-skips-nullability.md) — 對賬腳本化（真源與文件各拉 {欄名:可空性} dict 比對）；可空性一律以 migration／entity 為準；同檔同型欄寫法不一致本身就是失真訊號
- [L-078｜fix 因「finding 在允許清單外」而正確零改動，被零改動偵測判成不收斂](LESSONS/L-078-zero-change-detector-misreads-correct-escalation.md) — cycle() 對 `done_with_escalation`＋零改動當場 return 升級，置於零改動偵測之前；零改動偵測只服務 status:ok 的真空轉
- [L-079｜驗「呼叫處恰 N 處」只 grep `name(` 會漏掉函式指標形，0 命中被誤判成「根本沒呼叫」](LESSONS/L-079-counting-call-sites-misses-function-pointer-form.md) — 三形取聯集，或改名讓編譯器列出真實使用點；處數型驗收長期該由測試釘不由人 grep
- [L-080｜連動面盤點只找數字釘，漏掉手抄檔案名冊——新增一個檔本身就是一次集合改變](LESSONS/L-080-adding-a-file-is-itself-a-set-change.md) — 數字釘與名冊釘兩路並行盤點；新增檔的單元把全量測試排在實作早期
