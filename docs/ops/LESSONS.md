<!-- next: L-010 -->
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
