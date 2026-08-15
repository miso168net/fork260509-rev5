<!-- next: L-038 -->
# LESSONS — 教訓 registry

一教訓一段（`L-NNN｜坑＋防法`）、append-only；配號取檔頭 next-id 後 bump、號碼永不回收。
rev5 自空白起家、只記親歷坑；前代教訓為候選承襲清單（docs/brainstorms/000-doc-architecture.md §5 K3）、撞到對應域時挑選引用、不整批搬入。

L-001｜macOS bash 3.2 全形字黏變數名：`"$VAR全形字"` 在 UTF-8 locale 下會把全形字首位元組黏進變數名，`set -u` 直接炸 unbound variable（首暴＝preflight-secrets.sh 末行、B5b 移植期；且**選擇性觸發**——同檔他處同形卻沒炸，繫於後接字元的位元組值，不能靠「跑過一次沒事」排除）。rev4 全代在 WSL2 bash 5 從未暴露＝跨平台移植必掃。防法：①`$VAR` 後緊接非 ASCII 一律 `${VAR}` 包裹；②機器枚舉全 repo bash 面（regex `(?<!\\)\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])`、排除註解與 `\$` 轉義）逐處處置、絕不只修被咬那行（本次 6 檔 21 處一鍋改）；③新寫告警／訊息分支先空跑一次。

L-002｜watchdog 扁平 grep 抽 journal key 撞巢狀 payload 同名鍵：wf-watchdog 以 `grep -oE '"key":…'` 數不重複 agent key，但 workflow journal 的 result 事件內嵌 agent 回傳 JSON——回傳結構帶同名欄（本例 coverage[].key＝"FR-001"…22 筆）即被一併計入，實證 9 支真 agent 被數成 31 → RUNAWAY 誤報、健康工作流被 TaskStop（001 刀 speckit-analyze 首撞、2026-08-05）。防法：①判準抽取一律**頂層鍵定錨**（逐行 JSON 解析、只取事件物件 top-level 欄），絕不對含任意巢狀 payload 的 jsonl 做扁平 regex 計數；②既有「journal 非空卻抽到 0 key＝fail-loud」健全性檢查保留（頂層定錨後它兼任格式漂移哨）；③workflow 回傳 schema 欄名迴避框架頂層語意名（key/type/agentId）屬縱深防禦、非根治。修復自證＝真 journal 舊法 31/新法 9＋合成巢狀鍵 journal 抽 0 觸發健全性告警。

L-003｜「移植清單照單施工」不等於「已拍板」＋勘誤不逐處＝同病二暴：①啟動書「同機並存錯開清單」第 3 條（DB 身分加 _rev5 後綴）未經 user 逐條拍板即被 b10 照單施工、001 刀再沿引為「compose 既定」擴散至 15 檔——user 發現後裁決回滾（ADR 0008；容器內身分本無衝突面、「必須錯開」言過其實）。②B-009 修復只改被點名三處、漏同檔契約註解 L16/L18，被 review 以 errata 機器枚舉抓出——正是 CLAUDE.md §4 明禁的「只修被點名那一處」。防法：①移植／施工清單中拍板級條目（schema、身分、user 可見行為）施工前逐條確認拍板紀錄在案，查無紀錄＝先問；②勘誤一律 errata 機器枚舉全 repo 同語意命中、逐處處置後才 commit，命中清單附進 report；③承諾「先提修法過目」的事項不得以「後續指示概括放行」自行豁免——過目承諾單獨兌現。

- **L-004**｜移植品的「不一致」可能是前代刻意的防禦性慣例——動叫用形／預設值／樣式前，先查
  前代教訓帳與該處的 rev4 對應寫法，**repo 內部一致性不足以構成修改理由**。
  親歷：RUNBOOK／README 對五支 deploy 腳本混用 `bash deploy/x.sh` 與 `./deploy/x.sh`，我僅憑
  `tools/docs-sync.py` 之 EXEC_BIT_ROSTER 註解稱該五支為「直跑形」，就把 8 處 `bash` 前綴一律
  改成直跑形。user 指出前綴有前代來由後回查：①rev4 是**刻意混用**——其 RUNBOOK 同一張工具表
  內 `./deploy/sops.sh` 與 `bash deploy/decrypt-secrets.sh` 並存；真正的慣例是「docs 面用 `bash`
  前綴／腳本自身用法行與 `deploy/secrets/README.md` 用 `./` 形」②`bash` 前綴的防禦價值有二：
  可在前面掛環境變數（rev4:L-142 的定案指令＝`LC_ALL=C PYTHONUTF8=1 bash tools/bootstrap`，
  macOS bash 3.2 全形字邊界問題所需）、以及 index exec bit 若為 100644 時 `./x.sh` 會
  Permission denied 而 `bash x.sh` 恆可跑（rev4:B-116；drvfs 上 `ls` 恆顯 0777 看不出 index 真值）。
  ★即使 rev5 有 Lint21／EXEC_BIT_ROSTER 保證 100755 使直跑形安全，該慣例仍不該由 agent 以
  一致性為由單方抹平。
  防法：改**移植品**的既有寫法前，先跑「rev4 對應檔怎麼寫」與「教訓帳有無此主題」兩查；
  兩查皆無來由才動，有來由則升級為拍板題問 user。已回退 21 處。

- **L-005**｜以**當時基數**寫死的互動預期（「恰跳 1 次 passphrase 提示」），會在基數變動的
  當天失效——而該工具的失敗訊息指向錯方向，operator 只能誤判成「我的鑰匙壞了」。
  親歷：RUNBOOK §15.2 首次真實加人（recipient 1→2）當日，跨代並存機（本機另存前代 age 私鑰
  於 sops **預設**尋鑰路徑 `keys.txt`）跑 `decrypt-secrets.sh`：wrapper 唯讀掛載**整個**
  `~/.config/sops/age` 目錄 → 容器內兩把 identity → sops 對「每個 recipient × 每把鑰」各索
  一次 passphrase（本例 3 次），而提示與資料同流被暫存檔捕捉、畫面上**一次都看不到**
  （rev4:P1.2／rev4:L-168 之連帶）。operator 只答了第一次、其餘空答，sops 回
  `passphrase can't be empty` 並附一長串「找不到金鑰於 SOPS_AGE_*」——讀起來像鑰匙或加人
  有問題，真因只是「提示不只一次」。腳本檔頭那句「恰跳 1 次（單 recipient 基線）」正是
  誤導的來源：它把一個**隨資料變動的量**寫成了常數，且沒有任何機器會在基數變動時喊它過期。
  防法：①凡「次數／數量」類的互動預期，一律由腳本**自資料現算**後印在預告行，不落字面
  （本次＝自密文數 `recipient:` 行）；②把不可見互動的**面積收斂到最小**——容器內 identity
  收斂成恰一把（單檔掛到預設尋鑰路徑），而非把整個金鑰目錄攤進去，面積即提示次數的乘數；
  ③失敗訊息的**判準**寫進手冊（`Group 0` 的 recipient 清單看加人完沒完、`passphrase can't
  be empty` 看提示有沒有漏答），別讓 operator 從工具的「找不到金鑰」清單反推。
  ★連帶承認：`WARN … didn't match file's recipients` 在多 recipient 下是**正常過程訊息**
  （試到不是你那把的 recipient 時必然出現），單看它會把人帶往錯的方向。

- **L-006**｜世代錯開的殘留掃描，樣式集只列了「連字號後綴形」（`rev4-webhook`／`rev4-obs`），
  **黏斜線路徑段形 `rev4/` 不在集內**——掃描報「零殘留」是真的，但它只證明了「所列樣式零命中」，
  沒證明「該找的形都找了」。
  親歷：B10 stack 移植步首輪殘留掃描抓 6 處連字號形、補輪齊改後複掃零殘留並據此收步；
  2026-08-07 全樹裸編號審計回頭核對才發現，同一批掃描從未涵蓋 `fork260509-rev4/keygen`、
  `~/.cache/fork260509-rev4/secrets` 這類把世代字串當**路徑段**用的形——而世代錯開最要命的
  落點類字面（cache 層、暫存樹、SECRETS_DIR 預設值）恰好全長這樣，漏一處＝兩代共用同一層、
  明文機密互相覆寫。
  防法：①「世代字串」類殘留掃描的樣式集一律**同時列三形**——連字號後綴（`rev4-`）、
  黏斜線路徑段（`rev4/`）、裸詞邊界（`\brev4\b`）；任缺一形即視為未覆蓋，不得宣告零殘留。
  ②「複掃零殘留」只有在**樣式集本身先被審過**之後才算證據——先證集合完備、再證命中為零，
  兩步分別留證。③新增落點型常數（cache／tmp／SECRETS_DIR 之類）時，同刀把該路徑形補進掃描
  樣式集，別讓樣式集停在寫它那天的形狀。

- **L-007**｜機械改檔管線以 `splitlines()`＋`"\n".join()` 重組整檔，會把**字面 U+2028／U+2029**
  （Unicode 行／段分隔符）靜默摺成 `\n`——藏在測試樣本字串裡的該類字元就地斷裂成兩行、
  Python 字串未終結（ast SyntaxError），且字元肉眼不可見、報錯行號指向斷點而非成因。
  親歷：B-004 清償對 tools/docs-sync.py 批量插前綴，U+2028 事件測試樣本（`"前 後"`）被摺斷，
  ast 紅在 6164 行。防法：①整檔機械改動用 `str.replace` 或 `split("\n")`、絕不 `splitlines()`
  （它吃 \x1c\x1d\x1e\x85\u2028\u2029 全家）；②動含編碼樣本的檔前先掃 U+2028／U+2029 存量、
  改後以位置上下文縫回；③改完必 `ast.parse` 自證（本例即由此攔下、453 案測試復綠）。

- **L-008**｜單向書寫的判讀規則在反向情境會導向破壞性操作。親歷：外層 pull 進他機 37 筆後
  rust-api pin 分歧，四處文件（CLAUDE.md §3／SessionStart hook／bootstrap 註解與 warn）皆只寫
  「一律回外層更新 pin」——該句為「worktree 在前」而寫；反向（pin 在前、worktree 落後）照做即把
  pin 倒回舊值、抹掉他人 commit。防法：凡寫「一律 X」的處置規則，先問「反向情境存在嗎」，
  存在就必須雙向寫並給機器判準（此處＝merge-base --is-ancestor 三態）。

- **L-009**｜serde 對 `Option<Option<T>>` 的**預設** Deserialize 不承載三態：欄位值為 JSON `null`
  時，它與「欄位缺席」一樣落外層 `None`，兩者不可辨——三態就地塌成兩態。親歷：002-system-settings
  T021 寫端，ADR 0023 明定三態承載型為 `Option<Option<T>>` ＋ `#[serde(default)]`，照該字面實作後
  TDD 測試紅在「顯式 null 須為 `Some(None)`，實得 `None`」。★諷刺處＝ADR 0023 立案的理由正是
  「前代的 null 語意含混」，而照其條款字面實作仍會得到含混的結果。成因：`#[serde(default)]` 只處理
  「欄位缺席」，欄位存在而值為 null 時走的是 `Option<Option<T>>` 的 Deserialize，外層 Option 會把
  null 吃成 None。防法：①三態欄必須配 `deserialize_with` 自訂函式——欄位出現時先以 `Option<T>` 收
  再包一層 `Some`，缺席才由 default 給 `None`；②照 ADR／設計文件的「型別字面」實作後，必須以
  三形（缺席／null／值）各一案的測試自證，★不可假設型別本身承載了語意；③後續寫端刀照抄承載型時
  必須連該 helper 一起帶，否則同一個坑會逐刀重演。

- **L-010**｜守門機制的判準對被判對象的某類變動**結構性無感**時，閘看起來在保護、實際恆綠；
  已知四種致因＝判準與對象同源／寫死基數／單向包含／兩造無綁定。002-system-settings 一刀內
  四種全數親歷：
  ①**數量等式**——entity_access_lint 掃描面反轉為排除制時，首版完整性斷言寫成「全樹檔數 −
  排除面檔數 ＝ 受掃檔數」：等號兩邊都由同一份排除清單導出，清單一擴大、左邊少掃多少右邊就
  等量減多少，恆等。★實測：把 handler 加進排除面（＝該層整層退出守門）該斷言判**綠**
  （rust-api commit fce6542 載明）。②**寫死的基數下限**——entity_behavior_lint 首版以字面 15
  為 impl 站點下限（當時恰 15 張表）：判頭對某形失效少抓一站，今日 14＜15 尚能紅，增一張表後
  同一失效變成 15≥15 照綠；且在①的情境裡，「檔數下限」對排除面擴大同樣無感——數量門檻能被
  補償性變動填回去。③**單向包含（⊇）而非集合相等（＝）**——動詞閘原形只驗「打宣告動詞→
  非 405」（rev4:contract.rs 即此單向形），對「handler 閉包多掛一個未宣告動詞」完全無感：
  多出來的動詞用宣告動詞的政策放行（寫入吃讀取政策）、閘不紅。④**兩造之間無綁定**——
  contract registry 的 case_key 與 path 之間原無任何強制關聯，把 A 案例的驗證函式配到 B 路徑
  照樣全綠——實際測的是別的東西。防法：(a) 判準的兩邊不得由**同一個會隨違規同步移動的量**
  導出（同一份排除清單、同一個計數）——違規發生時兩邊等量移動、恆等即恆綠；★共變性須**逐
  違規類型**判斷、不可對一個判準整體貼標籤：取自同一掃描面但由互相獨立謂詞導出的等式，常對
  某類違規即紅（違規只動一邊），對另一類仍無感（如整支檔漏掃時兩邊同步各減一），須另配一條
  斷言補上；(b) **結構斷言優先於
  數量斷言**——斷言集合恰等於宣告值、關鍵項逐項指名，不用「數目對不對」代替；
  (c) 每個閘落地時配一次非 vacuous 自證（故意弄壞→須紅且訊息指名是哪裡
  壞→還原→復綠），沒跑過這一輪的閘等同沒裝電池的煙霧偵測器；機器面紀律詳 ADR 0024。
  ★特記：變形①是主線在**已修過五起同型問題、明知這類病灶存在**的情況下，修第六起時親手
  寫出的第七次——「知道有這個坑」不足以避免它，需要機器面的自證程序。
- **L-011**｜workflow 編排 script 把**已完成的工作誤報成失敗**，主線因而多花整輪查證；
  兩種結構性成因、maint-l010 一批內各撞一次：①**狀態欄語意複用**——review agent 沿用
  implementer／fix 的 `{status: 'ok'|'blocked'}` schema，script 依「status≠ok→立即 return
  升級主線」處置；但 agent 把 `blocked` 讀作「我發現了 blocker」（審查結論），script 讀作
  「agent 受阻無法完成」（工作狀態），同一個字兩種語意。實暴＝單元② spec review 回
  `blocked` 帶 1 筆 blocker，script 當場 return，**fix 迴圈整個沒跑**，一筆本可自動修掉的
  finding 直接升級主線。②**迴圈跑滿無確認輪**——fix 迴圈寫成
  `for r in 1..=N { review → 空即 return 收斂 → fix }`，跑滿即 `return {converged:false,
  blockers: prevBlockers}`；但 `prevBlockers` 是**最後一輪 fix 之前**的快照，fix#N 修好了
  卻沒人再看一眼。實暴＝單元① 把兩筆早已被 fix#3 修掉的 blocker 報成 unresolved，主線逐檔
  復核才確認（該兩筆修得比 reviewer 要求的還完整）。防法：(a) **狀態欄不得跨角色複用**——
  「agent 是否受阻」與「審查結論」拆成兩個獨立欄位，script 分開處置；同一份 schema 要給
  不同角色用之前，先逐欄自問「這個欄位對這個角色是什麼意思」；(b) **迴圈收尾必有確認輪**
  ——fix 迴圈跑滿上限後再 review 一次，空 blocker 即判收斂，否則回不收斂並附**確認輪**的
  blockers（不是迴圈內的舊快照）；(c) 共通原則＝**script 回報的狀態必須反映最後一次動作
  之後**，任何「先存快照→再動作→回報快照」的結構都會誤報。機器面紀律已同步進 CLAUDE.md
  §2 防呆六件套之 ④⑤。

- **L-012**｜submodule 內檔案的還原若在**外層** repo 執行，會**靜默失敗**：
  `git checkout -- <子庫>/<路徑>` 只回一行 `error: pathspec '…' did not match any file(s)
  known to git`（外層 git 不認得 submodule 內部路徑），**零檔案被還原**——退出碼雖非零，
  但該行混在大量測試輸出裡極易滑過。親歷（maint-l010 單元② 主線負向自證）：五項探針各自
  「暫改 src/→跑 lint→還原」，四次還原全數靜默失敗、探針逐項累積；第 (d) 項的紅訊息因此
  含兩行（前項殘留＋本項），第 (e) 項更誤紅在**站點數等式**（前項殘留的 impl 讓
  sites=16≠models=15）而非目標的掃描面斷言——★結論失真，但表面上「有紅」看起來像驗證成功。
  防法：(a) submodule 內的任何 git 操作一律 `git -C <子庫> <cmd> -- <子庫內相對路徑>`；
  (b) ★破壞性驗證（ADR 0024 要求③）每一項之間，還原後**立即機器確認**
  `git -C <子庫> status --porcelain` 回到基準態——未確認即進行下一項，則後續全部結論可疑；
  (c) 探針逐項在乾淨狀態**單獨**跑、不與前項疊加：疊加時紅訊息混入他項殘留、指名失真，
  而「有紅」本身會讓人誤以為驗證通過。
- **L-013**｜`DatabaseConnection::Disconnected` **不是**「一切操作都回 Err」的統一失敗態：
  sea-orm 1.1.20 的 `src/database/db_connection.rs` 對該 variant 共九處分派，八處回
  `Err(conn_err("Disconnected"))`（`execute`／`query_one`／`query_all`／交易等），
  **唯一例外**是 `get_database_backend()`——它 `panic!("Disconnected")`。根因＝該方法回傳
  `DbBackend` 而非 `Result<DbBackend, DbErr>`，**型別上沒有錯誤通道可走**。後果：高階查詢
  API（`Select::all` 等）組 SQL 前必須先取 backend 決定方言，於是**先撞 panic、根本走不到
  DbErr 路徑**——想用 `Disconnected` 當「查庫必失敗」的測試替身，拿到的是 panic 而不是預期的
  5000 信封。rev5 現況（002-system-settings U8b 盤點）：以 `Disconnected` 充免 DB stub 的三處
  （`tests/common` 之 `stub_state`、`router.rs` 的 `mod tests`、`enforce.rs` 測試）都只依賴
  「不觸庫」而非「觸庫得 Err」，故無影響。防法：(a) 需要「查庫必失敗」的替身時**自寫
  `ConnectionTrait` impl**（U8b 的 `FailingConn`：一切查詢回合成 `DbErr`），不要借
  `Disconnected`；(b) 借 `Disconnected` 當 stub 時碼內註明「僅保證**不觸庫**、不保證**觸庫
  得 Err**」——那是兩件事；(c) ★可推廣：判斷一個「失敗態替身」能不能用，要看**被測路徑實際
  會呼叫哪些方法**，不能只看該型別的整體語意；★回傳型別沒有錯誤通道的方法（回 `T` 而非
  `Result<T, E>`）就是 panic 的候選點——掃一遍那些方法即可預判替身會不會炸。
- **L-014**｜啟動書 K 條目裡的**裸 B／L 編號屬 rev4 命名空間**，與 rev5 同號條目語意無關；
  而 `docs/brainstorms/` 整個目錄在 Lint25 掃描面之外，機器不會提醒。親歷（2026-08-09
  維護批 maint-b043 勘查）：`docs/brainstorms/000-doc-architecture.md` 的 K1-70 條目寫
  「後端 log 全環境 JSON 化＋trace_id 進 log＋completion log（<裸 rev4:B-054／rev4:B-045>
  子項配套）」——原檔內那兩個號是**裸形**、此處依紀律補前綴轉述。rev4:B-045 與 rev5 的
  B-045（「main.rs 裸 `Database::connect` 導致逐句 SQL 灌進 Loki」）毫無關係；rev4:B-054
  更是 rev5 尚未配到的號（檔頭 next-id 為 B-053），照字面查會查到空。★本條寫成當下即被
  Lint25 擋下兩筆——證據就在自己身上：rev4:B-054 因超出 rev5 已配區間被抓，rev4:B-045 卻
  因 45 ≤ next-id 而**靜默放行**，兩者在同一個括號裡、命運相反。成因有二：(a) 啟動書是 rev4 承襲盤點的一次性產出，通篇以
  rev4 語境書寫；(b) `LINT25_SKIP_DIRS` 明列 `docs/brainstorms/`，理由是「one-shot 史料、
  過去式不改寫」——**這是刻意的設計、不是漏網**，所以正確處置是「查用時當 rev4 號讀」，
  **不是**回頭去改那個檔（改了反而違反過去式不改寫）。★危險在於啟動書 §5 至今仍是**活的
  查用點**（NOTES 明載「K1 查用點＝各刀階段 0、K2＝BACKLOG 條目本文」），下一刀 brainstorm
  會真的去讀它。防法：(a) 讀啟動書 K 條目時，凡見裸 `B-NNN`／`L-NNN` 一律預設是 rev4 號，
  要對到 rev5 條目必須拿**語意**去比對而非拿號；(b) 號若落在 rev5 已配區間（≤ 檔頭
  next-id）看起來「查得到」才最危險——那正是 ADR 0012 已載的「遮蔽型」已知極限，Lint25
  結構上測不出、只能靠人工；(c) ★通用形：任何「機器掃描面刻意排除」的目錄，其內容一旦
  仍被當作活的查用來源，就會出現「機器綠、內容誤導」的落差——排除掃描面時要同時問一句
  「這個檔還會被誰當真？」
- **L-015**｜**自製彙總腳本本身就是假綠來源，且真 DB 走查等同 runtime 寫入**：以 `cargo test … | grep '^test result' | awk '{p+=$4; f+=$6}'` 彙總得「181 passed／0 failed」，實際 rc=101、8 支紅——`test result: FAILED. 182 passed; 8 failed` 這行的欄位位移與 `ok.` 行不同、awk 取到的欄全錯，且該 suite 一紅即中止、後續 suite 未跑（181 < 250 是「少跑了」非「少了幾支」）。紅的 8 支全是真 DB 測，而弄髒 DB 的不是任何測試，是**主線自己用 CDP 做的 MVP 瀏覽器走查**——三帳號真登入寫 runtime 列進 `sys_token`／`session_event`／`sys_login_attempt` 並不可逆推進三支 sequence；T015 的 `SequenceResetGuard` 只在測試跑時生效，瀏覽器活動不在任何守衛射程內，schema-gate gate2 同時紅。防法：①★測試結論一律看 exit code、不看彙總數字（自製彙總腳本沒被驗證過，跟被它彙總的東西一樣可能出錯；要數字就併看 `grep -c '^test result: FAILED'`）②★任何 runtime 寫入之後都要跑 quickstart §7 收尾、不只收刀時跑（瀏覽器走查、手動 curl 登入、活體 demo 都算；判準＝有無東西寫進那三張表）③走查前確認三表 0 列、走查後立刻收尾，別讓髒 DB 跨越單元邊界（否則紅的會是別人的測試、追因成本翻倍）。★同批揭露：`specs/003-auth-session/quickstart.md` 的 §4 造窗與 §7 收尾兩處 psql 都寫 `-U postgres -d rev5_admin`，實際為 `-U soybean -d soybean_admin_rust`（compose 之 `POSTGRES_USER`／`POSTGRES_DB`），照抄直接 `FATAL: role "postgres" does not exist`——該兩行是 SDD 設計期寫的、從未實跑過；RUNBOOK 的「章內不放未經實跑的命令」自律，spec 的 quickstart 也該適用。
- **L-016**｜**`.ok()` 吞掉的可能是「交易已被毒化」那一腿，而 PG 會把其後的 COMMIT 靜默降級成
  ROLLBACK 卻回 `Ok`**：003-auth-session U-J 的 `handler/auth/refresh.rs` 之 `detect_reuse`
  原本在 txn 內以 `jwt::ttl_from_settings(&txn).await.ok()` 讀 denylist TTL——該函式的 `Err`
  有兩腿，而回傳型別把它們壓成同一個 `AppError::Internal`：①設定列缺失／值不可 parse＝純判斷、
  交易乾淨（`.ok()` 吞它完全正確，正是當時註解寫的那個情境）；②`system_settings::find_by_key`
  查庫失敗＝SQL 已送出且失敗、交易被 PG 推入 aborted 態。吞掉②之後，其後的 `txn.commit()` 會
  被 PG 回以命令標籤 `ROLLBACK`（不是 ErrorResponse），而 sqlx／sea-orm 不檢查命令標籤 ⇒
  `commit()` 回 `Ok(())` ⇒ `revoke_family`（全鏈→revoked）與 `session_event(reuse)` 兩筆一起
  蒸發、denylist 亦未寫，handler 卻照常回 `8888`：**疑似被盜的整條 token 家族原封不動存活、
  可無限重放，稽核面零紀錄**（fail-open，與憲法 §I.7 島 C 相反）。★真正的教訓不是這個機制
  ——`handler/auth/login.rs` 步驟⑩早已用一整段註解把它寫死在案，並據以刻意**不吞**
  `record_attempt` 的錯——而是**那段註解只住在 login.rs、沒有跨檔傳遞**：同一把刀、同一個
  crate、隔四個檔，同一個坑再踩一次，且四輪 code review 才抓到。防法：①凡在 txn 內呼叫
  「回傳型別會把查庫失敗與純判斷失敗壓成同一個錯」的函式，一律**不得 `.ok()`**——要嘛 `?`
  出去 fail-loud，要嘛把該呼叫移到 commit **之後**、走交易外連線（結構性免疫，不靠註解自律）；
  ②寫出這類註解的當下就 append 一條 LESSONS——**檔內註解是給改那個檔的人看的，LESSONS 才是
  給全 repo 看的**；③判準是問「這個 `.ok()` 吞得到的**最壞**那一腿是什麼」，不是「它通常吞到
  什麼」。
- **L-017**｜**「修好一支 flake」與「模組不再 flake」是兩件事；而零餘裕的時間斷言有兩個 ±1 秒級
  來源**：U-J 的碼品質確認輪指出 `t033⑤b`（grace 須先於 commit 落地）是機率性觀測——可觀測窗
  ＝一次 PG commit（0.1~1ms），而單輪只採一個樣本（EXISTS 回真後那一次鎖探針若比 commit 慢就
  收工），12 輪留約 6% 假紅率。修法＝輪數 12→60 ＋單輪內持續重採；★守的單向性不受影響：實作
  若真被搬到 commit 之後，「grace 存在」恆蘊涵「已 commit」＝鎖已釋，重採多少次都不會為真。
  ★關鍵在於修完**沒有就此收工**：連跑 40 次模組，第 34 次仍紅，而且是**另一支**測試 `t033①`
  ——`remaining=3901` 溢出 `<= 3900` 一秒。追出兩個成因：(a)`EXTRACT(EPOCH FROM ts)::bigint`
  在 PG 是**四捨五入不是截斷**（實測 `.6`→+1、`.4`→+0）；(b)斷言兩端取自不同時鐘讀數（PG 欄值
  vs 測試端 `Utc::now()`），WSL2 牆鐘會被時間同步往回踏。原註解還寫著「上界 3900 為緊界而不脆」
  ——那句話是錯的。防法：①★flake 的驗收標準是「模組連跑數十次零紅」而非「那一支不再紅」——
  修完一支就重跑全模組，成本遠低於讓它在別人的單元裡爆且紅訊息會誣指實作退化；②時間／TTL 斷言
  的**上界**一律帶明示餘裕常數，只要餘裕不影響鑑別力就加（該處要分辨 300 vs 3900 的 13 倍差，
  加 10 秒零損失）；下界通常已有大量餘裕、不需動；③`::bigint` 在 PG 是 round 不是 truncate，
  凡拿它做緊界斷言必先算進 ±1；④讀 redis 自己的 TTL 倒數則**無**此暴露面（值不可能超過 SET
  進去的數）——同形斷言要先分清資料來源，別一律加餘裕。
- **L-018**｜**單元收尾只寫 commit message、不落帳本也不勾 tasks.md，等於把知識鎖進 git 史**：
  003-auth-session 連跑九個單元（U-A~U-J）後盤點才發現——(a)每單元發現的衍生工作與踩坑全寫進
  了 commit message，但 `BACKLOG.md`／`LESSONS.md` **零 append**；(b)`tasks.md` 77 條 checkbox
  **全部沒勾**、已完成 38 條卻通篇 `[ ]`，該檔完全不反映實況。兩者都不會被任何機器閘擋下（lint
  不比對 tasks 勾選、帳本形制亦無機器守——後者即 U-N 待斟酌項），所以能一路靜默到收刀。
  ★危害不對稱：commit message 是**寫給讀那顆 commit 的人**看的，帳本才是**查得到**的那一份
  ——下一個接手的人不會去翻九顆 commit 找待辦；tasks.md 不勾則進度只能靠人腦或 session 外的
  task list 維持，換 session／換人即失真。防法：①單元收尾六步序**第③步固定是落帳**——衍生
  工作→BACKLOG append、踩坑→LESSONS append、tasks.md 把該單元涵蓋的 T 全勾；★主動做、不等
  user 問（user 2026-08-10 明令）；②★落帳必須排在 `docs-sync.py generate` **之前**：STATE.md
  的帳面統計現讀 BACKLOG／LESSONS，反序會產出仍帶舊計數的 STATE.md，**而且因為沒有 diff 所以
  不會被察覺**（與 pin／generate 次序陷阱同一形）；③判準——「這件事下一個人要查得到嗎？」要，
  就進帳本；「這條 task 做完了嗎？」做完了，就勾。commit message 照寫，但它是補充、不是替代。
- **L-019**｜**降級腿測不到，常常不是「忘了測」而是「上游同源故障先攔截」——構造壞 X 時，
  所有讀 X 的上游都會先壞**：U-K 的 `handler/auth/refresh.rs` 之 `reject_idle` 對
  `set_nx_ex` 的 `Err`（redis 故障）腿有完整論證與 `degraded` 訊號，卻零測試覆蓋。追因後
  發現不是疏漏：唯一的壞 redis 構造 `test_db::bad_cache()` 會讓**上游**的
  `last_activity_get`（同一條壞連線）先撞 `Err` → 走 fail-open 續跑 rotate，執行流永遠進不了
  `reject_idle` ⇒ 該腿**結構上不可達**。同形風險在後續單元只會更多（U-L 的節流三區、captcha
  標記各有數條 redis／PG 降級腿，且彼此共用同一條連線）。★危害：這類腿改壞了全樹零紅——把
  `Err(_) => false`（跳過落列）改成 `=> true`（「問不到就當第一次、寧可記下來」是很自然的
  直覺），redis 半斷線期間每一枚逾時會話的每次換發都會再插一列 `session_event(idle)`，前端
  refresh-loop 週期性重試 ⇒ append-only 稽核表被同一個 sid 灌爆，而該表無刪除路徑。
  防法：①判準——若某降級腿「經 HTTP 面構造不出來」，先問「是不是上游有同源故障先攔截」，
  是就**直呼私有 fn** 取得覆蓋（`integration_tests` 是模組子模組、`super::` 可達；先例＝
  `super::clamp_source_ip`／`super::is_unique_violation`）；②寫降級腿的論證註解時同步問
  「這條腿有測試嗎、走得到嗎」——有論證無覆蓋＝下一個人有充分理由把它「簡化」掉；
  ③補完守門一律做**變異測試**（本例：`Err(_) => true` 使新測紅 rc=101、還原後 rc=0），
  否則補的是另一個裝飾性守門（ADR 0024）。
- **L-020**｜**守門要挑「判別點附近」的值，不是安全距離外的值——否則測的是別的東西**：
  U-L 的 `captcha::verify_challenge` 以 `validation.leeway = 0;` 關掉寬限秒數（那行承載的是
  captcha「題目一次性」不變式），過期案卻用 `exp = now − 90` 測。而 `jsonwebtoken` 10.4.0 的
  `Validation::default()` 帶 **`leeway: 60`**，過期判定式為 `exp < now − leeway` ⇒ `−90 < −60`
  在 leeway=60 之下**仍然成立** ⇒ 把 `validation.leeway = 0;` 整行刪掉，全樹照樣綠。那行遂是
  一個無守門的賦值，而它一失效就開出真實的重放窗：消耗標記 `captcha:used:{nonce}` 的 TTL 自
  **驗題當下**起算、token 的 `exp` 自**簽發**起算，令寬限為 L，只要「取題到送出」不足 L 秒
  （＝正常操作的絕大多數情形），就有最長 L−1 秒的窗口讓標記已逾期而題仍驗得過 ⇒ 同一張已解出
  的題可再送一次。改用 `exp = now − 5` 後：leeway=0 拒（綠）、leeway=60 接受（紅），判別力精確
  且非 flaky（簽發到解碼之間 now 只前進，要讓 leeway=60 也拒得等 55 秒以上，單元測不可能）。
  防法：①寫「某參數被設成 X」的守門時，取值一律貼著 **X 與預設值之間**那條界線，別取一個
  「兩邊都會拒」的安全值——後者測的是功能存在、不是參數被設成 X；②凡是「把某個預設關掉／調緊」
  的賦值行，先查該函式庫的**預設值是多少**（本例＝讀 vendored 源的 `validation.rs`），再據以
  設計判別值；③補完一律做變異測試——把那行拔掉，指定的測試必須指名紅（本例 rc=101、
  而原 −90 那支照樣綠，正好證明它守不住）。
- **L-021**｜**非零 exit code 也要看「是誰回的」——`rc=1`（工具拒絕執行）與 `rc=101`
  （測試真的失敗）意義相反**：U-L 邊界做 flake 檢查時寫成
  `cargo test -p server --lib throttle:: captcha::`，20 輪全部 rc=1，讀起來像「20/20 全紅的
  災難」；實際上 `cargo test` 只吃**一個** TESTNAME 位置參數，第二個直接被 clap 拒絕
  （`error: unexpected argument 'captcha::' found`），**一支測試都沒跑**。識破的線索是同一刻
  全量 `cargo test --workspace` 才剛 rc=0，且 rust 測試失敗的慣例碼是 **101** 而非 1。
  ★這是 L-015「一律看 exit code」的必要補充：看 rc 是對的，但 rc 只說「失敗了」，不說
  「失敗在哪一層」——把工具用法錯誤讀成測試回歸，會讓人去追一個不存在的 bug；反過來把
  rc=101 讀成環境問題則會放掉真回歸。防法：①非零時**先看第一行輸出**再下結論，`error:` 開頭
  ＝工具層、`test ... FAILED`／`panicked at` ＝測試層；②迴圈跑測試時把首行錯誤一併印出來
  （只印 rc 會丟掉這個位元）；③多模組要一起跑就一輪多次呼叫，或直接跑 `--lib` 全組——
  別把兩個 filter 塞進同一次呼叫。
- **L-022**｜**派工單（tasks.md）的「涉檔列」不是授權邊界的真相——要對照「這個 task 需要的
  東西存在嗎」自己補**：003-auth-session 已兩度被同一形咬到。①U-J：`handler/auth/mod.rs`
  不在 U-J 涉檔列，但不補 `pub mod refresh;` 該檔就編譯不進 crate 且**無任何錯誤訊息指向此事**
  （U-K 列有它、只有 U-J 那列漏）。②U-M：T063 寫「import stub wrapper」，而全 tasks.md
  **沒有任何 task 建那個 wrapper**——rev4 藍本是獨立檔 `rev4-auth-stub.ts`、rev5 歸宿是
  `rev5-auth.ts`，U-K／U-L 兩列都有它、唯獨 U-M 那列漏；且憲法 §III.2 (b) 收窄字面是
  「僅改 import 指向 stub wrapper」⇒ 表單直呼 `request` 即違收窄，**沒有合規繞道**，
  implementer 只能回 blocked。★兩次都是「涉檔列漏一個結構上必需的檔」，而編排的允許檔案清單
  若照抄該列，就把缺口一起抄進去。防法：①開單元前對每個 task 問一句「它 import／呼叫／宣告的
  東西**現在存在嗎**」，不存在就往前追是誰該建——沒有任何 task 建＝派工單缺口；②允許清單以
  「該單元真正需要動的檔」為準、涉檔列只當起點；③撞到就**回頭修 tasks.md**（補涉檔列＋在該
  task 加前置說明），不要只修自己的 script——下一個讀派工單的人會撞同一面牆；④★agent 回
  blocked 時先判「是不是我的清單有缺口」，那正是防呆⑥要保護的東西，不是 agent 無能。
- **L-023**｜**`resumeFromRunId` 續跑時，看門狗 ARMED 行的冒煙位元組數是**前一輪**的殘留、
  不可據以判斷「新 prompt 有沒有送達」**：U-M 因允許清單缺口回 blocked，補列後以
  `resumeFromRunId` 續跑；看門狗 ARMED 行印出的「impl首行 10740bytes」與前一輪**完全相同**，
  讀起來像「implementer 走了快取、根本沒重新派」。成因＝resume 沿用同一個 wf 目錄與 runId，
  而看門狗的冒煙欄讀的是 journal 既有的第一筆記錄——那筆是前一輪寫的。同一行的
  `token 命中=1` 仍然有效（它證明鎖對了 run 目錄，不證明本輪 prompt 內容）。
  防法：①續跑時的冒煙查核**改看 agent 檔**——`ls -t <wf目錄>/agent-*.jsonl | head -1` 取最新一支，
  比 mtime 是否為剛剛、並 `grep` 本輪新加的字串（本例＝「本輪為續跑」）確認新 prompt 已送達；
  ②這是**一次性查核不是輪詢**，做完就等完成通知；③★續跑前先想清楚「我改的東西會不會讓
  (prompt, opts) 真的改變」——沒改到 prompt 的 agent 會走快取，那有時正是你要的、有時是災難。
- **L-024**｜**middleware／fallback 的組裝相對次序是行為、不是風格——次序錯不會編譯紅，
  只會把「誰來答 405」整個換人，且每個錯序各有不同的靜默壞法**：003-auth-session 的
  `router.rs::build` 實證三個失效形——①`method_not_allowed_fallback` 排在 merge **之前**
  ＝它只掃「先前已註冊」的 MethodRouter，之後 merge 進來的 route 全數漏保護、動詞不符回
  框架 405 零長度裸 body（13 碼矩陣外的第三種出口）；②排在 enforce_mw layer **之內**＝
  405 fallback 被 authn 包住、未認證動詞不符先吃 8888，於是「換個動詞」就能探測受保護路徑
  存在性（ADR 0031 零洩漏硬條款破功）；③axum 的 `allow` 標頭是 `RouteFuture` 末段才插
  （在所有 endpoint layer 外側），剝除殼從鏈內側掛 `map_response` 剝不掉、且信封三欄仍
  全等＝**靜默**失效。防法：①這類鏈序用「production 組裝函式的行為測」守（走真 `build()`
  的 contract 案），**不要**只用裸掛合成 router 的反例測——後者釘的是框架語意、production
  次序寫錯時它們恆綠（兩類守門的歸屬勿倒記，router.rs 碼註與 contract.rs 節首成對載明）；
  ②改組裝鏈前先讀「次序寫死」碼註並跑該 contract 案，紅了看是哪一個失效形；③凡「掛在鏈上
  的東西」都問一句「它掃的是掛當下的快照、還是之後的終態」——mnaf 屬前者，一切 layer 屬
  逐 endpoint 施加，兩者對次序的敏感方向相反。
- **L-025**｜**「免 DB 契約測」的免 DB 前提對 Public route 結構性破裂——blanket 信封斷言
  一寫 `0000`／空集就是在斷言一個測不到的東西**：contract.rs 的 stub app 用 connect_lazy
  假連線，Authed／Policy route 在 authn 層 early-return 8888、真的免 DB；但 Public route
  （getConstantRoutes 等）沒有 authn 擋路、oneshot 直進 handler、查詢在假連線上落 `DbErr`
  →回 5000——**不是空集也不是 0000**。若對全 route 一體寫「碼須 0000」的 blanket 斷言，
  Public 案必紅；反射性把它改成「碼屬可發集」全體套用，又把 Authed 案的判別力
  （早退形可逐值斷言 8888）一起稀釋掉。防法（ADR 0034 後果段已固化）：①契約案的斷言強度
  **依「該 route 在 stub 下走到哪一層」分級**——免 DB 的確定形（authn early-return、body
  rejection）逐值斷言，會觸 DB 的只斷言三欄信封＋碼屬 13 碼矩陣可發集；②寫新 contract 案
  先問「這條 route 在 stub app 下第一個 DB 觸點在哪」，不要從隔壁案照抄斷言；③blanket
  斷言要收緊前提：它隱含「全部案走同一條路徑到同一層」，Public／Authed 混掃時該前提天然
  不成立。
- **L-026**｜**redis 的 `TTL` 讀回值會**大於**SET 進去的秒數——L-017④ 那句「讀 redis 自身
  倒數不會超過 SET 值、精確毋需餘裕」是錯的**：U-N 的 T073 全量閘在本機約 3/10 機率紅，紅點
  ＝`t033①` 的 `assert!(ttl > 10 && ttl <= 30)` 讀到 `ttl=31`（`grace_set` 走的是 `EX 30`）。
  成因＝redis 把到期時刻算在**牆鐘**上（`EX n` 存絕對毫秒時刻、`TTL` 回「到期時刻−now」），
  故牆鐘只要在 SET 之後、讀 TTL 之前**向後跳**，讀回值就變大。本機（WSL2）牆鐘正持續後跳：
  量 `CLOCK_REALTIME` 相對 `CLOCK_MONOTONIC` 的偏移，60 秒窗內 4 次離散後跳（−0.782／−1.008／
  −0.825／−1.010，累計 −3.62s、成對出現、兩叢相隔 30 秒），15 分鐘後複量仍在跳。
  ★直證＝在容器內 redis 連續跑 23005 次「`SET … EX 30`→`TTL`」，2 次讀到 **31**——證明不是
  redis 取整語意、就是牆鐘後跳打進 SET 與讀值之間那道窗。★這條把 L-017④ 的分流結論
  （「PG 欄值 vs 測試端時鐘」有暴露、「redis 自身倒數」無暴露）**推翻一半**：兩者其實同一個
  牆鐘，redis 只是把絕對時刻藏在服務端而已。防法：①凡「SET 一個 TTL、隨即讀回斷言」的測，
  **上界與下界各帶同一顆具名餘裕常數**（rev5 落點＝`model::test_db` 的 `REDIS_TTL_SLACK_SECS`
  ＝10 秒、`refresh.rs` 4 處與 `logout.rs` 1 處跨檔沿用同一顆）——★「下界維持零餘裕、鑑別力全在
  下界」是**本條自己一度寫錯的推論**：牆鐘後跳把讀回值往**大**推，對下界是同方向作用，故下界
  貼著「要排除的錯值」W 寫 `> W` 時，實作真被改成 `EX W` 也會因讀回 W+1 而全綠（`> 10` 對 rev4
  grace 10 秒、`> 300` 對 access_secs 誤寫形、`> 3600` 對「拿 idle 門檻當 TTL」三處皆然），
  鑑別力變成**機率性**的。正解＝`ttl > W + 常數 && ttl <= C + 常數`（C＝拍板正解），三組的判別
  間距扣掉常數後仍餘 10／3590／290 秒 ⇒ 仍零鑑別力損失；
  ②餘裕常數的 doc 必須寫明「吸收環境效應、非放寬拍板值」，否則下一個讀的人會以為拍板值鬆綁了；
  ③放寬邊界後要補**變異測試**證明鑑別力沒被稀釋——把 handler 的 `cache::GRACE_TTL_SECS` 改成
  字面 `10` 重跑，該測須指名紅（實測 rc=101、`t033①` FAILED），改回才綠；★★該變異測試在
  「下界零餘裕」版只是**機率性**成立（恰逢一次後跳即讀回 11 > 10 而假綠），下界吃了餘裕之後才
  變成確定性的——**證明防法有效的變異測試自己也會被同一個環境效應蝕空**，這是本條最貴的一半；
  ④間歇性假紅的收工
  標準是「複跑數輪全綠**且期間環境效應仍在發生**」——本次 7 輪全量閘全綠（各 321 支、rc=0）
  之所以算數，是因為同一時段量到牆鐘仍在跳；若不同時證明後者，全綠只能證明環境當下安靜。

- **L-027**｜**Workflow 的 `resumeFromRunId` 不是「讓某一支 agent 重跑」的手段**——它是
  故障續跑用的，拿來當重跑開關會踩兩個坑：①快取判定不是逐字比 prompt。本批 U5 為了讓卡住的
  spec-fix-3 重跑而改 script 的註記內容（且用 `round === MAX_FIX_ROUNDS` 條件確保只有那一支
  的 prompt 變），檔案確認改到、`node --check` 也過，resume 卻回 `subagent_tokens: 0`／
  `tool_uses: 0`／`duration_ms: 10`——**七支全數快取回放**、吐出逐字相同的舊結果，連續三次
  皆然。②就算改對了也可能反噬：若圖省事直接改共用的 `fixPrompt`，前幾輪已完成的 fix agent
  會一併失去快取而重跑，而它們重跑時看到的是**自己已修好**的檔案 ⇒ 回報零改動 ⇒ 恰好觸發
  「fix 連兩輪零改動＝不收斂」把整支 workflow 提早中止。★正解：需要某階段重跑就**新開一支
  只跑該階段的 workflow**（新 runId、零快取糾纏），CONTEXT 內把已完成階段的結論與「勿重報」
  清單寫清楚。本批 U5b 即此形——只跑碼品質、7 支 agent、當場抓出一發存活變異。
- **L-028**｜**「守 A 與守 B 判準必須同尺」這種對稱性論證，兩邊各自需要釘子**——只釘一邊
  而在另一邊的註解寫「對稱釘子＝<那支測試>」，是 vacuous 守門的一種高階變形，比沒寫註解更
  危險（後手照註解判斷會以為已覆蓋）。U5 實暴：`_erratum_view` 的格式跳過守衛註解寫「對稱
  釘子＝`test_erratum_bad_corrected_rejected` 的 `int("1"*40)`」，但該測試走
  `lint_events()`→`_check_event`、**從不呼叫 `_erratum_view`**——視圖那半邊完全裸奔，把
  `isinstance(cor, str) and RE_SHA.fullmatch(cor)` 放寬成 `RE_SHA.fullmatch(str(cor))`
  （＝同檔 feature_close 既有慣例，有人照抄很自然）全套 494 測仍全綠。危害不是 no-op 而是
  **反向**：殘缺值混進視圖後 target 列整列不入 merges，原本該出的 ERROR 被靜默吃掉。
  ★兩個可攜作法：①寫「對稱釘子」註解時，先確認那支測試的**呼叫鏈真的經過本函式**；
  ②挑反例值要挑能**穿透兩把尺差集**的（此處 `3` 無用——`str(3)` 非 40 位 hex、兩把尺都拒；
  只有 `int("1"*40)` 分辨得出來）。

- **L-029**｜**帳面測試數當「零回歸」判準＝跨批次必失真、且會製造假回歸警報**：NOTES／STATE 記的測試數是**收刀當時的快照**（003 收刀＝「測試 145→321」），其後的維護批會把它推走而**沒有任何機制回頭改那句話**——它住在過去式帳裡、本來就不該是活判準。004 的 tasks.md 兩處 DoD（T014／T047）直接引了 `321`，我又把它抄進 U-C 的 agent prompt 當「既有 321 支測試仍全綠」。實測基線是 **server lib 260／全 target 合計 327（另 2 ignored）**，差 6 支。implementer 這次自己查證後在 report 裡校正了（U-C 收尾覆核確認其正確），但同一形也可能反向作用：實作者看到「帳面 321、實測 327」而去找不存在的回歸，或更糟——把自己造成的真回歸當成「帳面本來就對不上」而放過。★防法：①**DoD 與 agent prompt 一律不寫死測試數**，改寫量測法——「動工前先跑一次基線、以**動工前後同一指令逐 target 比對**為準」；②真要引數字時必須同時寫明「量測日期＋量測指令」，讓它自證為快照而非不變式；③帳面數字（NOTES／events）只當史料，反查現況一律回機器面重跑。★同批附帶查證（推翻一則 agent 說法，記此以免下次又被『修正』）：`cargo test -p server <mod>::` **不必**加 `--lib` 也抓得到 lib 內 `#[cfg(test)]`（實測 26 passed／260 filtered out）；會誤判成「抓不到」是因為其餘 target 會各印一行`0 passed; N filtered out`，看起來像過濾器沒命中。

- **L-030**｜**射程／職責一搬動，敘述面沒跟著搬＝靜默失效**——同一形在 004 U-D 一輪內撞到兩次，兩次都不是碼錯而是「碼與描述它的那句話分岔」，且兩次的徵狀都是**編譯綠、測試綠、規格看起來也綠**。

**形一（職責搬走、義務沒跟著搬）**：主線指示把 `ipgate::build_ruleset` 的「未知 `wbip_type` 列 skip＋**告警**」中的告警半邊移出純函式（改以回傳值 `RuleSetBuild::skipped` 交出，讓判定核維持零 I/O 而可全態離線測——這個設計是對的），但**沒有同批把發告警的義務指派給任何下游 task**：T025 全文無「未知類型」字樣、T030 的降級類別集又逐字取自 data-model §5 而該矩陣無此列。於是三份規格產物（tasks T011／data-model §1.1／research R5）都還寫著「告警」，實際上全刀不會有任何一處發出它。★危害具體形：營運面把 `wbip_type` 打成 `block`，該列被靜默忽略、日誌與觀測兩面零訊號，管理者以為規則已生效。★**編譯器幫不上忙**——下游只取 `.rules` 而丟棄 `.skipped` 不會有任何警告。抓到它的是規格審查 agent 拿實作去對「三份產物 × 下游每一個 task」交叉查，不是讀碼。

**形二（守門的射程放寬、docstring 沒跟著放寬）**：`server/tests/entity_access_lint.rs` 的實碼掃 `src/` **全樹**、只排除 `model/facade` 一層（`excluded_dirs()`、主守紅訊息字面「src/ 全樹（facade 除外）」），但它自己的檔頭 docstring 仍逐字寫早期的三處列舉「`src/handler/`＋`src/auth/`＋`src/router.rs`」。★危害方向與直覺相反：docstring **比實碼窄**不會讓守門失效，而是讓**讀 docstring 的人**以為 `src/` 底下新開的目錄（本刀的 `src/ipgate/`／`src/trust/`）不在射程、可以自由寫 `entity::`。我自己就是受害者——照該 docstring 把錯的射程寫進了 agent prompt，若不是審查 agent 去讀實碼比對，那句錯敘述會被原樣寫進 commit message 傳下去。

★**防法**：①**搬動職責時，同一次編輯內把接收方的 task／DoD 也改掉**——「移出 A」與「A 的義務落到 B」是**兩件事**，只做前者等於把義務丟掉；規格產物留著舊字面則會讓帳面看起來還在。②**守門碼的射程敘述與其射程常數必須同批改**，並在該敘述旁寫死「MUST 與 `<常數名>` 同步」（本次已就地補進 `entity_access_lint.rs`）。③agent prompt 裡引用機器守的射程時，**引實碼常數而非 docstring**；引錯的成本是把錯敘述放大成全單元的前提。④review prompt 值得長期烤一條：「規格說要有的東西，去查**哪一個 task 負責產出它**；查不到就是 finding」——形一正是這條抓出來的。

- **L-031**｜**走查在共用 dev 庫留下的 committed 列會毒化「下一次」測試，而證據自毀 ⇒ 外觀是 flaky**：004 U-F 的 quickstart §1 走查（兩筆 `Super` 失敗登入）留列後，緊接的 `cargo test --workspace` 之 `handler::auth::login::integration_tests` **五支當場紅**，首發訊息＝`duplicate key value violates unique constraint "sys_login_attempt_pkey" … Key (id)=(1) already exists`。機制：測試起手掛的 `test_db::SequenceResetGuard` 在 Drop 時 `setval('sys_login_attempt_id_seq', 1, false)`，走查留下的列佔住 `id=1` ⇒ 下一支 insert 撞主鍵。★**守衛沒有錯、也不能改**：reset 到 1 是 gate2 逐列 diff 凍結 seed 第 446 行 `setval('public.sys_login_attempt_id_seq', 1, false)` 所要求的，改成 `max(id)` 會讓 gate2 紅；該守衛的 doc 早已寫明「本守衛只管 sequence、不刪列，committed 列的清理歸專責 cleanup、與本守衛**成對掛**」——走查留下的列正是那個**沒有守衛認領**的缺口。 ★**三個讓它極難被發現的性質**：①**證據自毀**——同一次測試執行裡的 `handler::auth::user_info` 掛了 `LoginAttemptCleanup::new(&["Super","Admin","User"])`，而 `user_info` 在字典序上排在 `login` 之後，於是它把走查列清掉 ⇒ **重跑第二次就全綠**；②**三閘接不住**——`sys_login_attempt` 在 schema 閘的 runtime-append 收窄集內，留列時 `schema-gate check` 仍四項全綠（收窄只豁免 **seed 內容比對**這一個面，不等於留列無害）；③**次序決定看不看得到**——把「跑全量」排在走查**之前**（實作者的自然順序，因為走查通常是 DoD 最後一項）就連紅都不會出現，回報的「全量綠」與收尾第②步的 rc 都是**走查前**的快照。 ★**防法**：①**走查即清**——每一節走查的 DoD 直接寫入清列指令，**不要**收斂到收尾章節（004 的 quickstart §7 原本只清 `sys_ip_rule`，而 §7 屬最尾單元 ⇒ 中間每個單元的測試都會被毒到）；②**單元收尾第②步（容器內看 rc）MUST 排在清列之後**——這是 CLAUDE.md §2 六步序的隱含前提，走查型單元要顯式檢查；③**「在收窄集內」不可推論成「留列無害」**——收窄集是**某一個閘**的豁免名冊，其他失敗面（本例是測試套件的 sequence 假設）完全不在它的射程；④agent prompt 若要求走查，就同批要求清列與**清列後**的重跑，否則拿到的綠是走查前的。 ★**與 B-059 的關係**：B-059（`us4_sliding_window_resets_on_success` 間歇性假紅）的兩個嫌疑向量之一正是「dev 共用庫的外部登入流量」。本次實暴**證實該向量真的存在**（外部列確實會影響 login 測），但方向相反（本例是列**多**造成主鍵撞、B-059 是 L2 count 讀**低**），故不足以結案 B-059、僅供其再現時對照。

- **L-032**｜**執行單元的允許檔清單，天然擋住「修正被自己證偽的他處敘述」**——這是防呆⑥（空間邊界）的必然副作用、不是誰的疏失，但它會讓假述無聲累積到收刀。規律很乾淨：**同檔的假述單元自己會修掉；跨檔的不會**。

004 一刀之內撞到四次：①U-D 把 `build_ruleset` 的告警義務移出純函式，但承接它的 `try_load_ruleset` 在**別的 task**（T025／U-G）⇒ 三份規格產物都還寫著「告警」、實際上全刀不會有任何一處發出它（見 [[L-030]] 形一）②U-F 的 `sys_login_attempt` 檔頭「本刀不填」與 `assert!(row.peer_ip.is_none())`（**同檔**、單元內修掉）③U-F 的 `router.rs` mnaf 次序理由與 axum 實況相反（**同檔**、單元內修掉）④U-G 把 `throttle_degraded_total` 值集自六源重推為十二源，而同語意宣稱散在 `throttle/mod.rs` **五處**＋`docs/arc42/ARCHITECTURE.md` **兩處**＋`state.rs` **一處**——★**八處全在 U-G 允許清單外**，fix agent 依防呆⑥零改動 blocked 升級主線（其中 `throttle/mod.rs:358` 更宣告了與 `obs.rs` 現行**相衝的「單一權威」**：一邊說值集權威是research R5 六源、一邊說是 `THROTTLE_DEGRADED_SOURCES` 十二源，兩檔對同一個對外契約〔Grafana label 值集〕各自宣稱不同的權威）。

★**防法**：①**agent prompt 加通則**——「凡你改變了某個**數字／集合大小／方向／名稱／單一權威**，MUST 以 `grep -rn` 枚舉全 repo 同語意命中並**逐處回報**；清單內的自己改，清單外的以 `status=blocked` 升級主線」。★第④次是規格審查 agent **自發**援引 CLAUDE.md §4 的勘誤紀律才抓到的——自發不可依賴，要烤進 prompt。②**主線把「跨檔假述枚舉」列入單元收尾第①步的固定動作**：`grep -rn '<被改變的字面>'` 或`tools/docs-sync.py errata <關鍵詞>`，改完再枚舉一次確認活面零命中。③**判準＝史述保留、現在式改對**：`obs.rs` 的「此前是恰六、004 起重推為十二」是正確史述、不動；`throttle/mod.rs` 那五處是**現在式宣稱**、必改；活書（`docs/arc42/**` 恆現在式，CLAUDE.md §4 時態分離）一律屬後者；已收刀的 specs（002／003）屬史料、不動。★枚舉時務必連**不同語意的同字面**一起看過再排除（本次 `specs/002-.../wire-settings.md` 的「可發碼恰六」講的是錯誤碼、與降級源無關）。

- **L-033**｜**「兩檔各存一份同一字面」的漂移，字面驅動的守門測擋不住——守門必須由『生產端的真實產物』驅動**：004 U-G 一輪內同型撞兩次（`login.rs` 手打 `"request_context_absent"`／`main.rs` 手打 `"unknown_key"` 與 `config.rs:285` 的 `scope` 比對），兩次都是 review 才看見、零機器訊號。機制：生產端寫一份字面、消費端寫一份字面，兩份之間**無共用常數也無型別關係** ⇒ 生產端改名照樣編譯，消費端的 `!=` 恆真／`==` 恆假，行為靜默反轉（本例＝把「TOML 有個鍵名打錯」升格成 `ip_domain_degraded_total{kind="trust_model_load"}` 的**真警報**，正是該處碼註自己宣稱要避免的事）。★**關鍵陷阱在補救那一步**：直覺補的測試是 `assert!(!counts_as_degradation("unknown_key"))`——那**擋不住任何東西**，因為測試自己也握著一份**同樣過時的**字面，它與消費端互相印證、生產端改名時兩邊一起錯、測試全綠。這是循環斷言的變形（同 `obs.rs` 對「測試期望值集不得迭代被測表」的警告，只是這裡循環的是**字面的來源**而非集合）。★**防法＝讓斷言消費生產端**：本例改為呼叫 `config::load_trust_model` 餵一份含未知鍵的真 TOML、對**它實際回傳的** `scope` 做斷言，測試本體零字面 ⇒ 生產端改名時當場紅（兩向都要有：述詞恆 `false` 那向擋的是「整條序列永遠 0」的退化實作，已變異實測 rc=101）。★**歸因陷阱同批記下**：本例做「改 config.rs 生產端字面 → 跑 workspace → rc=101」時，紅的**不只**新測——`config.rs` 自己那支既有測試也硬寫著同一份字面、會一起紅，故 workspace 級的紅**無法單獨歸因於新守門**。要證明新守門有效，必須①單獨跑那一支，或②推導其斷言鏈（本例＝斷言消費 `load_trust_model` 的實際回傳值，故必紅）。更關鍵的是：新測真正獨有的射程是**「生產端與它自己的測試一起改名」**這條路——那條路上 workspace 級變異全綠，只有產物驅動的斷言看得見。★通則：**多支測試各持同一份字面時，變異一次會全紅，rc 不構成任何單支的有效性證據**。★**更根本的一階**＝生產端匯出具名常數讓兩邊消費（`obs.rs` 的 `DEGRADED_KIND_*` 即此形，故 `login.rs` 那條能一行修掉）；做不到時（跨執行單元允許檔清單、或該模組不宜擴 API）才退到產物驅動測試，並在述詞 doc 記下「日後生產端若匯出常數，本處應改為消費之」。★**識別法**：`grep` 某字面若在**生產面**（排除註解與測試）命中 ≥2 個檔案且其中無 `const`／`pub const`，即為本形。

- **L-034**｜**建連逾時罩不到「連線之後」——長生串流的死亡偵測要另一套機制，而它失效時是零告警零計數的完全靜默**：004 U-G 的門鈴 watcher 依 research R5 逐字實作了「建連 5 秒逾時」（`SUBSCRIBE_TIMEOUT`），看起來連線面已有守；實則該逾時只罩**建連＋訂閱那兩步**，訂閱成功之後的存活期完全沒罩。中間設備靜默丟棄連線（NAT／LB idle 回收、對端主機掉電）⇒ 我方得到**半開連線**：`on_message` 串流永不回 `None`、`.await` 永遠掛著 ⇒ 外層的 backoff 重連迴圈**永不觸發** ⇒ 規則改了但本副本永不生效，且**不會有任何一則告警或計數**（那些訊號全掛在「串流斷線」與「訂閱失敗」上，而這兩件事都沒發生）。★徵狀在營運面極難歸因：「後台改了 IP 規則，A 機生效、B 機沒生效」，而 B 機的 log 乾淨、metrics 正常。★防法：①長生訂閱／串流一律另開 **TCP keepalive**（本例＝`ConnectionInfo::set_tcp_settings(TcpSettings::default().set_keepalive(..))`；★`redis::Client::open(url)` 走的是 `TcpSettings::default()`＝`keepalive: None`，**不顯式覆蓋就沒有第二個地方會補**）②或加應用層心跳／`.await` 上的 idle 逾時。③**審查時把「有逾時」與「有存活期偵測」當兩件事分開問**——前者存在會讓後者的缺席看起來像已覆蓋，這正是本條被拖到第三輪才發現的原因。★**連帶記下未關的口**：補上的守門測 `pubsub_client_enables_tcp_keepalive_on_the_doorbell_connection` 釘住的是**建構點**（`open_pubsub_client` 的產物確實帶 keepalive），**不是呼叫點**——把 watcher 那行換回 `redis::Client::open` 則全樹仍綠、上述失效被靜默還原。要真關掉只有「型別上讓訂閱端只吃該建構函式的產物」或「另立掃原始碼的 lint 測」兩條路，皆已超出本刀範圍、逐字記在該測 doc 內（同形警示：**守門測釘住建構點不等於釘住呼叫點**，寫 doc 時不得含糊成「已守」）。

- **L-035**｜**防呆④（status≠ok 立即 return）與防呆⑥（清單外→回 blocked）相撞，會讓一個交付完整的單元整個審查階段一輪都不跑**：004 U-M 實暴——implementer 把 T067~T070／T072 五條全數落地、容器內 rc=0、三閘全綠、走查跑完且四表零殘留、六項變異測實跑，**唯一**回 `blocked` 的原因是跨檔假述枚舉掃出**兩處清單外**的一行級文件失真（`refresh.rs` 的一句 doc、`msg-keys.md` 的一格表欄），依⑥不擅改而升級主線。而 script 依④「`status !== 'ok'` → 立即 return」當場收工 ⇒ **規格審查與品質審查一輪都沒跑**，主線收到的是一個「未經任何審查但其實做完了」的單元。★**兩條規則各自都對、相撞在語意重載**：`blocked` 同時承載「我做不下去了」與「我做完了但有事要你在清單外做」，而這兩者對 script 的正確反應相反——前者該立即升級、後者該**照常跑完審查**再連同升級項一起回。★**防法**（擇一，本刀採①）：①**分兩個 status 值**——`blocked`（真受阻、立即 return）與 `done_with_escalation`（工作完成、附清單外待辦，**照常進審查**）；②退一步的權宜法＝主線收到 `blocked` 時**先判它是哪一種**（看 `changed_files` 非空且 `report` 自稱完成即屬後者），再另開一支只跑審查的 workflow（★不是 resume——L-027：resume 會全數快取回放）。★**識別徵狀**：workflow 完成通知裡 `agent_count=1`、`outcome` 卻是 implementer 的 status——一支 workflow 只跑了一個 agent 就結束，就是撞上這一形。

- **L-036**｜**只在「回歸發生時」才漏出 committed 列的測試，平常全綠、紅的那一次順手弄髒共用 dev 庫**：004 U-M 的 `t069_chain_rejection_precedes_password_hashing_with_no_success_side_effect` 以**密碼正確**的帳號發逾窗鏈、斷言仍被拒。正常態下請求在拒絕腿早退 ⇒ 不落 `sys_token`；但**拒絕腿一旦回歸**，該請求就真的登入成功、落一列 committed `sys_token`，而測試拿不到 sid、掛不上 `ChainRowsCleanup` ⇒ **紅的那一次同時汙染共用庫**，後續 `schema-gate` gate2 的 seed 逐列 diff 會在**數個單元之後**才爆，爆點與成因完全對不上（同 L-031 的證據錯位形，但成因相反：L-031 是走查留列毒化測試，本條是測試在紅的那一刻留列毒化閘）。★該測在本單元的 M6 變異測中**實暴**（確實漏出一列），implementer 當場清除並補上守。★**防法**：①凡「斷言某副作用**不該**發生」的測試，其清理 MUST 覆蓋「副作用真的發生了」那條路徑——不能只清自己**預期會建立**的東西；②清理呼叫點擺在**斷言之前**（L-031 已立，本條是它的另一半：L-031 管的是「斷言 panic 時清理跑不到」，本條管的是「清理**不知道有東西要清**」）；③做法上可用「測前記錄基準列數／測後刪除該基準之後的所有列」取代「刪除已知 id」，讓清理不倚賴對副作用的預期。★**識別法**：測試名含 `no_..._side_effect`／`does_not_create`／`precedes_` 者一律套用本條複查。

- **L-037**｜**用某個論據駁倒替代案之後，沒回頭檢查所選方案是否也中同一刀**——最隱蔽的一種設計缺陷，因為證據就寫在自己的文件裡、只差沒往回讀一次：004 的 FR-046 選了「稽核轉錄改保留判定窗」，其**棄案論證**逐字寫著「棄案＝只把方向反過來（保留最右 1024 字元）：32 個長 IPv6 token 可達約 1440 字元 > 1024，真實來源仍可能落在欄外，是『大多數情況包得住』而非結構性保證」。★該論據**同樣適用於所選方案**——所選方案是「先取最右 32 欄、**再以字元上限兜底**」，那個字元兜底在窗本身逾 1024 字元時照樣切掉最左欄。於是同一份 FR 裡，上半宣告「結構性保證：真實來源必定出現在該欄中」，下半自己寫出了推翻它的機制。★**憲法 F8 據此宣稱寫成無條件保證、隨 v1.5.0 入憲**，直到 U-M 規格審查以逐位元反例證偽（`"203.0.113.50, " + "X"×1100 + ", 10.0.0.5"` 僅 **3 欄** ⇒ 不溢出、請求照常被服務、稽核列照落；判定軌丟棄不可解析欄後 `real_ip` 是最左那個，而窗長 1124 > 1024 ⇒ 字元兜底把它整段切掉），v1.5.1 收窄。★**為何 review 前沒人發現**：①棄案段落在心理上已「結案」，寫完就不再當成活的約束讀 ②所選方案多了一道「先取窗」，直覺上會覺得「有了欄數上限，字元上限只是保險」——但兩道上限**各自獨立**，欄數達標不蘊含字元數達標 ③反例需要「欄數少但單欄極長」這種不直覺的形，而測試通常造「欄數很多」的鏈。★**防法**：①**棄案論證寫完後 MUST 回頭對所選方案跑一次同一個反例**——這一步寫進 spec 撰寫紀律，成本極低（就是把剛寫的那句話當輸入再讀一次）②凡「A 和 B 兩道獨立上限先後套用」的設計，MUST 明確寫出「只滿足其一時會怎樣」③「結構性保證」四個字是強宣稱，寫下它之前先問「有沒有一條輸入能讓它不成立」——答不出來才寫，答得出來就改寫成帶條件的宣稱。★**同批教訓**：`rightmost_window_str` 的 doc 裡有該假述的**第二份複本**，只修被 review 點名的那一處＝L-032／L-033 的原型復發；枚舉通則要對**自己剛寫的宣稱**也跑一次。
