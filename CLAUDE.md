# CLAUDE.md — rev5 workspace 薄操作手冊

預算 ≤250 行（lint Lint07 強制）。本檔只放規則與程序；快查去處：
查現況→`docs/generated/STATE.md`｜當前意圖→`docs/ops/NOTES.md`｜待辦→`docs/ops/BACKLOG.md`（滯後項另卷→`docs/ops/BACKLOG-DEFERRED.md`）｜
架構→`docs/arc42/ARCHITECTURE.md`｜**文件地圖→README.md**｜坑與防法→`docs/ops/LESSONS.md`｜
決策→`docs/arc42/decisions/`｜操作手冊→`docs/ops/RUNBOOK.md`。
明確不含：reference data（→`docs/generated/reference/`）、進度 marker（→NOTES＋STATE）、
gotcha 長註記（→LESSONS）、repo 目錄樹全景（→README.md）。

## 1. workspace 用途與 repo 拓樸

- 本 repo＝rev5 傘狀 workspace：admin 後台系統的文件、spec、編排中樞；default branch `rev5-admin-root`。
- 程式碼住兩個 submodule 目錄，各有雙身分（本機＝源倉的 git worktree；對外層＝submodule gitlink）：
  - `base-web/`：分支長名 `rev5-admin-base-web`；前端（soybean-admin fork）。
  - `rust-api/`：分支長名 `rev5-admin-rust-api`；後端（rust；全新寫〔§I.5〕、無 fork-delta 最原始源基線）。
- ★應用碼實作高度參照 rev4 為預設藍本：動工前先讀 rev4 對應碼
  （讀法與對照環境→§7、唯讀）；重打字消化、拷貝禁止；★註解一律重寫（rev5 語境、
  rev4 出處帶 rev4: 前綴）；rev5 拍板已推翻的行為不得帶回（憲法 §I.5＋本代 ADR 0019）。
- 短名/長名分工：目錄與口語用短名；git branch／push 一律用長名。
- fork 源倉目錄（repo 根下 `fork260509-soybean-admin-base/` 與 `fork260509-rev2-anew-rust-api/`、
  gitignored）必須保留——worktree 的 `.git` 檔指向它。
- **最原始源**（base-web fork-delta「原行」基線）＝upstream `soybeanjs/soybean-admin` 的 `example`
  分支＝本機源倉 `fork260509-soybean-admin-base/`（恆切在 `example` tip；lint 首步斷言、不在即紅）。
  base-web 修改型 inline（動到基線既有行）標記必含 `原行: <基線該行逐字原文>`；我方新檔／純新增行
  （基線沒有的行）不標原行、走新增型圈界——紀律上位＝constitution §III。機器強制＝
  `tools/fork-delta-lint.py`（每次執行先 self-test 防恆綠；每次 base-web 改動即跑、pre-commit 於
  base-web pin 變動時自動擋，不靠人工 review）。
- 外層只記 gitlink SHA（pin）；worktree 模式下 `git submodule status` 行首「-」永遠出現、屬正常。

## 2. feature 工作流

階段 0 brainstorm → SDD 5 步 → TDD 實作（Workflow 編排）→ finishing → 收刀簿記三步＋perf 第四步。

- **階段 0 brainstorm**（superpowers:brainstorming）：產出存 `docs/brainstorms/<NNN>-<feature-name>.md`
  （此行即覆蓋 skill 預設路徑）。期間拍板→ADR draft。rev4 承襲候選——K1／K2 清單
  （啟動書 docs/brainstorms/000-doc-architecture.md §5）與 BACKLOG 帶 `rev4:` 標註項——是
  brainstorm 的直接輸入：沿用項照已驗證結論施工、翻案項用新設計。
- **SDD 5 步**：`/speckit-specify`（input＝brainstorm 檔）→ `/speckit-clarify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-analyze`；每步後 commit。plan 之 research 必列
  「rev4 對應碼清單＋rev5 拍板差異點」（ADR 0019）。
  specify 必**手動**起手、不排進 brainstorm 流程內自動觸發——否則 feature-branch pre-hook 不會跑、
  spec 會落在 default branch 上。
- **TDD 實作**：以 superpowers:executing-plans 讀 tasks 起手、批判審查分執行單元；
  **從不使用 spec-kit 的 implement 指令**。編排驅動提示詞範本：

  ```text
★skill 限 superpowers:*
以下提到 <NNN>-<feature-name> 即當前 git branch 名稱。
讀 specs/<NNN>-<feature-name>/tasks.md → act-on-code 接地、依實際相依把 tasks 分執行單元；驗收對照 spec.md。
★編排用 Workflow 工具：每執行單元一支，內部 serial 跑
　implementer(TDD) → spec-compliance review → fix 迴圈 → code-quality review → fix 迴圈。
　★fix 後次輪 review prompt 必附前輪已駁回 findings 清單（file×summary＋駁回理由）、明令勿沿用
　被駁論據重報；同一 finding 再報須附新證據，否則直接計入⑤收斂判定。
　每個 agent prompt 烤進不可違反項：★書面產物（report／blocker／程式碼註解／文件）一律 zh-TW、
　rust 全程 serial、容器內 build/test、★rust 碼完工前容器內 `cargo fmt --all`（ADR 0057）、
　review agent 只讀不寫 repo 檔、★絕不 push/merge、
　★實作先讀 rev4 對應碼（../fork260509-rev4/ 直讀、★該樹絕不寫入）高度參照但重打字消化不拷貝、註解一律重寫
　（rev4 出處帶 rev4: 前綴）、rev5 拍板差異點不得帶回（ADR 0019）。
★workflow script 防呆六件套（缺一不發射）：
　①agent prompt 全數烤進 script 本體模板字串；args 只傳短純量、script 首段逐欄斷言
　　（型別＋非空），不符→零派發即 throw——防 args 以 JSON 字串抵達、屬性讀出 undefined。
　②派發前斷言渲染後 prompt 非空、長度合理、開頭不含字面 "undefined"／"null"、★必含 "zh-TW"
　　字面（語言強制令漏烤→零派發即 throw；另有 PreToolUse hook 機器擋）。
　③一切邊界寫死在 script 常數、絕不取自 args：fix 迴圈用 for 上限 ≤3 輪；
　　單元 agent 總數保險絲 ≤20 支，超限 throw（fail-loud 讓主線立刻收到完成通知）。
　④implementer／fix 一律 schema 回傳 {status, report}；status≠ok→立即 return 升級主線、不進 review。
　　★review agent **不得共用該 status 欄**：「agent 受阻」與「審查有 blocker」是兩件事，
　　共用一欄則 script 把後者當前者、當場 return 而 fix 迴圈整個不跑（L-011 變形①實暴）。
　　★**⑥的升級不得寫成 `blocked`**：「我做不下去了」與「我做完了但有清單外待辦」對 script
　　的正確反應相反（前者立即 return、後者**照常跑完審查**再連同升級項回）。故 status 分
　　`blocked`／`done_with_escalation` 兩值，只有前者觸發立即 return（L-035 實暴：五條全交付
　　的單元因兩行文件失真而整個審查階段零輪次）。徵狀＝完成通知 agent_count=1。
　⑤收斂偵測：review 連兩輪 blocker 集合（file×summary 結構化比較、勿比自由文字）相同、
　　或 fix 連兩輪零改動→return 判不收斂；unresolved 一律帶 findings 回主線。
　　★fix 迴圈跑滿上限後必有**確認輪**（再 review 一次、空 blocker 即判收斂）：直接 return
　　迴圈內的舊 blockers＝把最後一輪 fix 已修好的成果誤報成 unresolved（L-011 變形②實暴）。
　⑥空間邊界：fix agent prompt 烤進允許檔案清單（＝該執行單元 tasks 涉檔＋review findings
　　指涉檔的聯集、寫死 script 常數不取自 args）；清單外檔案需要動→status 回 blocked 附原因
　　升級主線、絕不擅改；次輪清單只縮不擴。
★主線看門狗（非終止型故障不會有完成通知）：★Workflow launch 與 Monitor 看門狗
　**同一回合原子成對**發射、兩 call 間零其他動作——「發射後再掛」＝結構性漏掛（已實證）。
　Monitor command＝`python3 tools/wf-watchdog.py <冒煙token> [wf目錄|runId]`（缺目標＝自動發現最新 wf 目錄、毋需 launch 回傳值故可同回合並發；
　帶目標＝輪詢待其出現後鎖定、resume 沿用原 runId、launch 被擋重發＝TaskStop 舊 Monitor 改帶新 runId 重掛（L-049）；ARMED 首行夾帶冒煙、stall/runaway 保險絲、happy-path 靜默）；
　完成通知＋Monitor 雙訊號全覆蓋、毋需輪詢；完成通知一到→TaskStop 該 Monitor（防誤觸 stall）。
　判死迴圈／卡死→TaskStop→修 script→以 resumeFromRunId 續跑（已完成 agent 走快取不重跑）。
　★resume **只用於故障續跑、不是「讓某支 agent 重跑」的手段**（L-027）：快取判定不逐字比
　prompt（實測改 script 後 resume 仍全數快取回放、tokens=0），且改共用的 fixPrompt 會讓前幾輪
　已完成的 fix 一併重跑、看到自己已修好的檔案而回零改動→誤觸⑤不收斂。需某階段重跑＝**新開
　一支只跑該階段的 workflow**（新 runId、零快取糾纏），CONTEXT 寫清已完成階段結論與勿重報清單。
　hook 兜底：PostToolUse(Workflow) 注入配對提醒、PreToolUse(Workflow) 擋缺 zh-TW 之 script。
主線例行只在單元邊界醒（看門狗告警除外）。★單元收尾**六步序、次序不可反**：
　①復核 agent 回報（逐項自 grep 驗證、不採信）②load-bearing 自驗（容器內看 rc＋三閘）
　★③落帳（＝「隨做隨記」的 TDD 期時點）：本單元發現的衍生工作→BACKLOG append、踩坑→
　　LESSONS append、tasks.md 把該單元涵蓋的 T **全勾**——主動做、不等 user 問
　④子庫 commit ⑤`git add <子庫>`→`docs-sync.py generate`→`git add docs/generated`
　⑥一顆外層 commit → 啟下一支。
　★③必須早於⑤：STATE.md 的帳面統計與 pins 皆由 generate 現讀，反序即產出舊值**且無 diff
　　可察**（同 pin／generate 次序陷阱；成因與危害見 L-018）。
★單元一支接一支連續跑完、**不停下來等 user 首肯**；唯三種情形停：①拍板級問題（§5 判準）
　②到了需要 push/merge 的時點③觸及 §6 硬禁令。
全單元完成 → final holistic review → finishing-a-development-branch（push/merge 需 user 同意）→ 收刀簿記三步（events append＋NOTES＋tools/docs-sync.py generate）→ ★第四步（不在簿記那顆內、易漏）：該簿記 commit 落地後量其牆鐘、append 一筆 close_bookkeeping perf 事件（隨下一顆 commit 入帳；量測法＝RUNBOOK §12.1、承載處＝ADR 0070、出處＝ADR 0044 引信）。
  ```

  ★wf-watchdog 的 runaway 判準＝數**不重複 agent key**（非 journal 行數）——勿以行數直覺判保險絲。
- **隨做隨記**：新拍板→ADR draft→accepted；架構影響→活書對應節【就在 feature branch 內改】；
  踩坑→LESSONS append；衍生工作→BACKLOG append；per-unit pin 即時 bump。
  一次性遷移（改名／搬移／基線前進／拓樸調整）之 brainstorm 或 spec 附 Risk／Guard／Rollback
  三欄表。
- **輕量軌**（維護項不開 SDD）：判準＝維護／小修——單點缺陷修復、文件與設定調整、既有機制的
  小幅完備化；不動 schema、不新增能力面。程序＝開分支 → 編排單元（或直改）→ `merge --no-ff`
  回 default → misc 事件收單（消化 BACKLOG 條目時帶 backlog_done 欄）。
  拿不準走哪軌：涉拍板級（schema／scope／破紀律／user 可見行為）＝開 SDD。
- **收刀**：`merge --no-ff` 回 default（保留 feature branch 不清理）→
  ①`docs/ops/events.jsonl` append feature_close ②NOTES 改下一步 ③`tools/docs-sync.py generate`
  → 一筆簿記 commit、lint 全綠放行。簿記一律排在 merge 之後（merge SHA 與最終 pin 才確定）。
  ④簿記 commit 落地後量該顆牆鐘（量測法＝RUNBOOK §12.1）、append 一筆 `close_bookkeeping` perf
  事件（ADR 0044 引信之每刀例行量測、承載處＝ADR 0070；隨下一顆 commit 入帳）。
- **review 輪**（不定期）：報告存 `docs/reviews/YYYYMMDD-<scope>.md`（front-matter 必含
  `findings_total`）；findings 三分流：修／轉 B-NNN／won't-fix ADR；＋append 一筆 review 事件。

## 3. git／submodule 操作手冊

- **兩段式 commit**：①worktree 內 commit → ②立即回外層 `git add base-web`（或 `rust-api`）
  bump pin＋外層 commit。pin bump 在單元邊界即時做、不延到收刀。
- **session 健檢判讀**（SessionStart hook 自動注入）：pin 與 worktree HEAD 分歧**先判方向**——
  兩向處置相反、照錯邊會抹掉真 commit。①**worktree 在前**（本機剛在子庫 commit、pin 落後）→
  回外層 `git add <子庫>` bump pin。②**pin 在前**（他機推了子庫 commit、外層 pull 帶進新 pin）→
  在 **worktree 內**顯式前進：`git -C <子庫> fetch origin <長名>` →
  `git -C <子庫> merge --ff-only <pin>`；★此時回外層 bump pin＝把 pin 倒回舊值、抹掉他人 commit。
  機判：`git -C <子庫> merge-base --is-ancestor <worktree HEAD> <pin>` 成立＝②、反向成立＝①、
  兩者皆不成立＝真分叉、停手問 user；pin object 不在本地（bad object）＝先 fetch 再判。
  ★兩向皆**永不 `submodule update`**（會 reset worktree）。
- **初始化／新機器**：clone 外層後跑 **`bash tools/bootstrap.sh`**（一鍵幂等：源倉 clone＋worktree
  重建＋hooks＋基線/pin 斷言＋fork-delta-lint＋secrets 體檢；舊機重跑＝純體檢、worktree 斷裂給
  自癒指引）。`git submodule update --init` 僅限唯讀快速看碼捷徑（fresh clone；worktree 模式下
  誤跑撞 gitlink）——該模式**無源倉＝無基線**、不可做 base-web 開發。
- **upstream rebase**（base-web）：fetch 前 `git remote -v` 確認 upstream push URL 已設 no_push；
  rebase＋force-with-lease push 後**立即**回外層 bump pin；並同步前進最原始源基線
  （`fork260509-soybean-admin-base` fetch upstream 至 `example` 新 tip；各機自行向 upstream
  pull 同步、基線不 push）＋`原行:` 註解更新為 upstream 現行版（憲法 §III rebase 同步紀律）
  ——基線不前進＝fork-delta-lint 比對失真。
- worktree 內 push 一律顯式 `git push origin <長名>`。
- 故障排除→查 `docs/ops/LESSONS.md`（rev5 空白起家；前代候選＝啟動書 §5 K3）。

## 4. 文件系統規則

- **三材質**：人寫（對話產出、Claude 執筆、user 拍板審 diff）／事件源（`docs/ops/events.jsonl`、
  半自動 append）／機器生成（`docs/generated/`、嚴禁手改、任何檔案可刪除重算）。
  每個事實只有一個人寫的家；鏡像不是機器生成、就是不存在。
- **時態分離**：活書永遠現在式；未來式住 ops/（NOTES／BACKLOG）；過去式住 git＋events。
- **完成即刪、git 即史**：BACKLOG 做完刪列、決策翻案立新 ADR；沒有歸檔搬運手續。
- **ADR**：一決策一檔 `docs/arc42/decisions/NNNN-<slug>.md`；accepted 後 body 不可變
  （typo 級修正：commit message 帶 `[adr-amend]`＋設 `DOCS_SYNC_ADR_AMEND=1` 過 lint）；
  翻案＝新檔 `supersedes: [舊號]`、
  `superseded_by` 由工具回填人不填；won't-fix／by-design 也立 ADR；as-built 不回灌 ADR
  （拍板歸 ADR、實作結果歸收刀事件、實作推翻拍板＝新 ADR）。
- **lint 運作模式**：pre-commit 一次跑完、秒級；被擋的是 Claude、同回合修復（錯誤訊息附去處）；
  純碼 commit 幾乎全 skip。user 僅介入：lint 抓到真決策、或 lint 調規拍板。
- **勘誤**：`tools/docs-sync.py errata <關鍵詞>` 機器枚舉全 repo 同語意命中、逐處處置後才 commit——
  禁止只修被點名那一處。
- **ID 配號**（B-NNN／L-NNN）：取檔頭 next-id 後 bump；號碼永不回收；ADR 編號＝檔名、永不重用。
- **constitution**：`.specify/memory/constitution.md` 唯一權威、不設鏡像快查表；
  amendment＝ADR＋版本 bump。

## 5. 提問／決策紀律

- 純工程「怎麼做」（優化手法、模組拆法、DTO 映射、命名、測試策略）自己拍、回報備查。
- 拍板級才問：動 schema／加 migration、feature scope 邊界、破紀律例外、user 可見行為變更。
- 問法：大白話、每選項串回 user 核心目標；trade-off 主張先 grep 實證；
  行為類拍板附具體渲染範例（前後對照）；正交維度拆開列選項、granular 攤開不打包。

## 6. 不要做的事（精選硬禁令）

- ★絕不在 finishing 收尾階段之前 push/merge；push 前需 user 明確同意；tasks 清單不得排入 push/merge。
- ★絕不在掃描防線就位前落任何 commit（含子庫與新機器；`bash tools/bootstrap.sh` 驗證通過＝就位）。
- 絕不 `git submodule update`（會 reset worktree）；絕不 `git submodule add`（與 worktree 衝突；
  submodule 設定手寫 `.gitmodules`）。
- 絕不直接編輯 fork 源倉；前後端改動一律走 `base-web/`、`rust-api/` worktree。
- 絕不寫入 `../fork260509-rev4/`（含其子庫與兩份源倉）——活體對照基準；亦絕不對 rev4
  stack 做 schema／seed／設定變更或 `down -v`（操作面詳 §7）。
- 絕不手改 `docs/generated/**`；絕不用 spec-kit implement 指令；specify 不進 brainstorm 自動流程。
- rust build/test 一律容器內跑且全程 serial（host 無 toolchain；平行 cargo 互撞 target）。
- review agent 只讀不寫 repo 檔，findings 只放回傳訊息。
- NOTES／任何帳本不記「已push/未push」揮發狀態，只記 SHA；repo 文件不引用 per-machine memory
  路徑；跨檔引用不用行號、不 deep-link BACKLOG/NOTES/STATE 的內部錨（只可整檔引用）。

## 7. rev4 參照與對照環境（讀碼＋活體 UI 基準）

- rev4＝已收官的上一代：既是應用碼藍本（§1 紀律），也是 UI 對照基準——rev5 做出來的
  UI 須與其一致、以 CDP 對照驗收。
- **讀碼**：`../fork260509-rev4/` 之 `base-web/` 與 `rust-api/`＝切在 `rev4-admin-*` 的真
  worktree，與 rev5 源倉同名分支 tip 同版（2026-08-12 實測逐位一致）。直接 Read／Grep／
  Glob，勝過 `git show` 逐檔撈。★它是可寫的真工作樹、無物理唯讀保護：絕不寫入（§6 硬
  禁令）；派 agent 讀 rev4 時唯讀令必烤進 prompt。rev4 已收官不應再動——發現其 worktree
  不乾淨、或其 HEAD 與 rev5 源倉 rev4 分支 tip 不一致＝有人動過、停手問 user。
- **對照 stack**：於 `../fork260509-rev4/` 根跑
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait`；例行只
  up／stop／ps，拆除、機密、故障排除→rev4 自家 `docs/ops/RUNBOOK.md`（不在本檔重複）。
  ★絕不 `down -v`（刪卷＝毀掉最終版對照資料、不可逆）；runtime 使用（登入、瀏覽、寫其
  稽核表）屬正常，但絕不動其 schema／seed／設定；rev5 的 psql／schema-gate 絕不指向 rev4 庫。
- **端口**（皆 127.0.0.1）：42080＝rev4 UI（對照基準）｜42089＝soybean example 原版基線
  （apifox mock、`docker-compose.example.yml`）｜42079＝rev4 API 直連｜45432／46379／
  48025＝pg／redis／mailpit。rev5 側 22080（UI）／22079（API）——4xxxx 對 2xxxx 不衝突、
  兩 stack 併行是預期形。
- **UI 對照流程**：host 瀏覽器以 `--remote-debugging-port=9229` 起，CDP 接
  `127.0.0.1:9229`（Node 24 內建 WebSocket、勿裝 ws 套件），開分頁對照 42080（rev4）vs
  22080（rev5）、必要時加 42089（原版基線）三方比。★一律用 127.0.0.1、不用 localhost
  （兩者 origin 不同、token 不共享）；dev 帳號 Super／Admin／User、密碼 123456。
