# rev5-admin (fork260509-rev5) Constitution

> **本檔為 rev5 設計凍結權威**：與活書（docs/arc42/ARCHITECTURE.md）、ADR、生成物衝突時以本檔為準。
> v1.0.0 由 rev4 constitution v1.15.0 之可攜段搬入、user 親審 diff 後定版（創世拍板紀錄＝ADR 0001）。
> 改動本檔一律走 Amendment 流程（§V.2）；spec-kit `/speckit-plan` 必須對照本檔跑 Constitution Check（§IV）。

---

## I. Core Principles

### I.1 base-web 為權威（NON-NEGOTIABLE）

**規則**：base-web（`rev5-admin-base-web` 分支實碼、自 upstream soybeanjs example 最新 HEAD 衍生）有的功能，rust-api 都要提供對應 endpoint。設計範圍嚴格、不縮減。

**含義**：
- base-web 的 wire／type／endpoint／route shape，rust-api 必須對齊
- 「v1 從簡」只能是交付排程、不能簡化設計範圍
- 不動 base-web inline（例外見 §III 軌道授權；授權後的變動執行紀律見 §III fork-delta 紀律）
- upstream rebase 友善——不留 upstream 衝突風險高的改動；fork 差異全程 `rev5-inline` 標記可定位

### I.2 menu 權限 Casbin enforce

**規則**：menu 由 Casbin RBAC enforce、有權才顯示。

**含義**：
- 業務 menu 走 `/route/getUserRoutes` → 後端 Casbin enforce 過濾 → 前端顯示
- demo menu 處理：demo view **全部進 `sys_menu` seed、初始僅勾給 `R_SUPER`**——全集完整、可見性由角色勾選層（casbin menu 維度）治理下放；`hideInMenu`／頁面排除等前端隱藏機制**皆不啟用**。例外與釋義（ADR 0005）：①toggle-auth 示範鏈（`function`／`function_toggle-auth`）保留 `R_ADMIN`／`R_USER_COMMON` 初始勾選（恰 4 列、示範「三角色各見不同按鈕」語意所需、承 rev4 終態）；②「不啟用」＝禁止以 hideInMenu 作 demo 可見性治理手段，upstream route meta 自帶之 `hide_in_menu` 值照原樣入 seed、不視為啟用（6 列白名單載 ADR 0005）
- constantRoutes（login／404／403）前端寫死、與 menu 無關、不動；constant route 集合可經 §III.2 授權新增——builtin 三頁不動與 Casbin 豁免語意不變

### I.3 wire 契約權威序與不變式（NON-NEGOTIABLE）

**權威序**（對賬裁決）：
1. **base-web 實碼**（`rev5-admin-base-web` 分支：`typings/api/*.d.ts`＋`service/api/*.ts`＋`.env`＋`views/**`）＝ wire **唯一權威**
2. 官方 docs 站＝解釋性文件，僅紀律性約束引為規範
3. mock 實測＝補充回歸 fixture，**不當 shape oracle**

**鎖定不變式**：
- envelope `{data, code, msg}`（無 `success` bool）；`code`＝string `"0000"` 非 number；business error 走 **HTTP 200** 信封
- **id 序列化＝逐欄位忠實 typings**：typings 宣告 number 的欄位回 JSON number、宣告 string 的欄位（如 `MenuRoute.id`／`UserInfo.userId`）於序列化邊界轉字串；DB 一律 i64 自增；serializer 帶 2^53 fail-loud 守衛；**型別謊言帳本歸零起算**（每筆顯式偏離＝拍板、立 ADR）
- **13 碼矩陣整組凍結**：`0000`/`1000`/`2222`/`3333`/`7777`/`7778`/`8888`/`8889`/`9998`/`9999`/`4040`/`5003`/`5000`；HTTP status 例外僅 `4040`→404、`5003`→403，**內部錯誤 `5000` 一律 HTTP 200 信封**；4 保留碼（`7778`/`8889`/`9998`/`9999` 組內後端從不發出者）僅前端 `.env` 分組認得、contract test 斷言後端從不發出；新需求優先 reuse 既有碼
- `msg` 載穩定 i18n key（後端語言無關、不在地化；前端 `$t` 翻譯、未命中 graceful fallback）——「wire 凍結事實」指錯誤碼本身、`msg` 非人話字串；觀測側可讀性補強候選掛 BACKLOG
- 業務驗證 error code＝`2222`；`5xxx` 段為授權／基建、非業務；refresh 類 critical code 絕不用在業務驗證
- 分頁形 `PageRes<T>`＝`{current, size, total, records}`（camelCase、無 `pages`/`success`、空頁 `records:[]`）
- envelope universal 例外僅 2：`/health`（plain text）與 `/metrics`（Prometheus exposition）
- 預設帳號：`Super / Admin / User`（login req）＋ User → User01 alias（getUserInfo response）
- **契約機器化**：typings 抽 JSON Schema 當 contract test 裁判（唯讀、不動官方檔）＋coverage gate（每條 route 必有 contract case）＋碼表 table-driven case；機制隨 wire 地基刀落地

**錨定註**：本節錨定 `rev5-admin-base-web` 分支實碼；若上游演進使碼表／typings 與本節分叉，於 wire 地基刀對賬現形、走 Amendment 校正。

### I.4 SDD＋TDD 混合工作流（NON-NEGOTIABLE）

- **階段 0 brainstorm**：產出存 `docs/brainstorms/<NNN>-<name>.md`；期間拍板→ADR draft
- **階段 1 SDD 設計鏈**：`/speckit-specify`（**手動起手**）→ `/speckit-clarify` → `/speckit-plan`（對照本 constitution！）→ `/speckit-tasks` → `/speckit-analyze`
- **階段 2 TDD 實作**：superpowers executing-plans（**不是 `/speckit-implement`**）
- **收尾**：finishing-a-development-branch → `git merge --no-ff` 回 `rev5-admin-root`（保留 feature branch 供 audit）
- `git push`／`git merge` 不得出現於 finishing 之前
- 收刀簿記三步：events append＋NOTES＋docs-sync generate（一筆簿記 commit）；拍板全文歸 ADR
- 詳細操作＝CLAUDE.md §2/§3（本檔不重複）

### I.5 rust-api 全新寫、對前代 source 受控參照（RUSTAPI-SOURCE-ISOLATION）

**規則**：rev5 rust-api 整棵樹自源倉 main（Initial commit）起全新寫；設計以 rev4 已驗證結論為輸入（承接經 ADR provenance），**code 不拷貝**。實作以 rev4 對應碼為**預設藍本**——先讀後寫、高度參照（ADR 0019）。

**前代 source 立場（rev4 為主、rev3 溯源，皆唯讀參考庫）**：
- **讀允許**：可 grep／閱讀前代 source 對照驗證（施工參考）
- **拷貝禁止**：實作必須重新打字消化、不可整段複製
- **註解一律重寫**：不拷前代註解；rev5 語境重寫（引 rev5 契約／ADR）、前代出處帶 `rev4:` 前綴（ADR 0019）
- **防回歸條款**：參照前代 code 時，凡 rev5 拍板已推翻的行為**不得帶回**

**例外**：`sea-orm-adapter`／`xdb` 工具性 crate 整檔拷貝（已驗證、工具性質）。

### I.6 業務表審計欄標準（SCHEMA-AUDIT-COLUMNS）

**規則**：業務主表建表（create migration）時 MUST 含 6 審計欄——
`created_at` / `created_by` / `updated_at` / `updated_by` / `deleted_at` / `deleted_by`。

**型與約束**：
- `*_at`：`timestamptz`。`created_at` NOT NULL default `now()`；`updated_at`／`deleted_at` nullable
- `*_by`：operator 的 `user_id`（`bigint` nullable／`Option<i64>`，**非 user_name 字串**）；system seed／migration／未認證情境無 operator → `null`
- **成對**：`deleted_at` 必與 `deleted_by` 同寫；`updated_at`＋`updated_by` 同理

**archetype 四變體**（整組凍結；各表歸屬隨 schema 刀入活書與 generated/reference/schema）：
- **A 業務全 6 欄**（例：使用者／角色／選單／系統設定表）：如上；soft-delete 表配 partial-uniq `WHERE deleted_at IS NULL`（PK 本身總體唯一者除外）
- **B append-only 日誌**（例：三 log 表）：只 `created_at` NN（＋operator 類 domain 欄）；**無 soft-delete、無 update、不可竄改**；MUST NOT 加 `updated_*`/`deleted_*`（retention 水平線刪除不屬「竄改」：時間水平線整段刪除屬 retention、非竄改——權威釋義隨稽核域行為島入憲時載明，在此之前以本句為準）
- **C join／狀態機**（例：user-role join＝零審計硬刪；token 表＝僅 `created_at`＋status 狀態機）；★變體 C upsert 釋義（承 rev4:ADR 0085 釋義）：1:1 已驗證值衛星表之 upsert 刷新＝重驗事件覆寫、`verified_at` 即其時戳、不設 `updated_*`——「成對」條款不因此觸發
- **D 治理變體**（例：casbin 規則表＝`protected`/`created_at`/`created_by` 對 stock adapter 隱形；archive 表＝原 grant 欄＋`archived_at/by`＋`archive_reason`、無 update/delete 欄）

**無 retrofit 條款（含範圍釋義）**：本標準自第一條 migration 即生效——建表即帶 archetype 全欄，**不允許「建表漏審計欄、事後補」**。釋義：本條款標的**僅限 archetype 審計欄**；既有表因功能需要加業務／鑑識欄的**刻意、規劃、可逆**演進不在此限——前提是 archetype 欄規則不變（如變體 B 永不加 `updated_*`/`deleted_*`、不可竄改性維持），且非「忘帶事後補」的意外債。

### I.7 行為島 invariants（隨刀進場）

**本節為行為島狀態機不變式的凍結位，隨刀填充。**

**進場規則**：每台狀態機（如 token rotation／policy governance／single-session）隨其刀的 brainstorm 拍板後，以 **MINOR Amendment** 將不變式條文入本節；rev4 已驗證狀態機之不變式為對應刀 brainstorm 的直接輸入（出處經 ADR provenance 溯源）。入本節後，動任一條不變式走 Amendment；方向性反轉（fail-OPEN/closed 方向、DB-first、踢人雙通道分離等）＝MAJOR。常數值與欄級細節留活書（非凍結面）。

**已入憲行為島**（首批五座由 ADR 0028 於 v1.3.0 隨 003-auth-session 進場）：

**A. token rotation**
- 同一鏈（family）至多一條 `active`；DB partial UNIQUE 為護欄而非唯一防線。
- rotate 次序 MUST 為「舊列轉 `rotated` 並寫 `used_at` → 插新 `active`」，**次序不可反**。
- grace 窗內同票二度換發 MUST 冪等回**既發的同一對**；grace 窗 MUST 大於前端最壞重試間隔。
- reuse 偵測的**唯一觸發形**＝列為 `rotated` 且 grace miss；命中即撤整條家族。
- fail-* 方向：grace 不可用＝**fail-secure**（並發換發觸發 reuse、撤家族；重登復原）。

**B. single-session**
- 政策解析為**兩層**：`effective_single = session_policy=='single' || (session_policy=='inherit' && single_session_default=='on')`。
- 踢除 MUST 落 `session_event(kicked)` 並寫 denylist；被踢者在 `(access, refresh)` 窗內換發仍得 `7777`。
- fail-* 方向：`single_session_default` 讀不到＝**off 語意**（刻意與 D、E 方向不同）。

**C. denylist 撤銷**
- `sys_token.status` 為**權威**、denylist 為加速層；兩者不一致時以 status 定案。
- 鍵缺席（nil）＝「未撤」語意 ⇒ 放行；`revoked` 列缺 denylist MUST 靜默 `8888`、**不得落假 reuse**。
- denylist TTL MUST ＝ refresh 全壽命，`kicked` 與 `revoked` 兩 reason 皆同。
- fail-* 方向：讀不到（連線 Err）＝**fail-closed**——退 PG 查該鏈是否仍有 active，無 active→`8888`；**PG 亦故障 MUST 視為無 active、絕不盲放**。

**D. idle 逾時**
- 門檻＝`refresh_secs − access_secs`；`session_event(idle)` MUST 僅首次落（SET NX 守門）。
- 不等式 `access_TTL ≤ N×30 < N×60` ⇒ idle 命中 **MUST NOT** 寫 denylist。
- fail-* 方向：`last_activity` 不可讀＝**fail-open**（不 idle-reject，以 token exp 為界）。

**E. 登入失敗節流**
- 三區（自由／需驗證碼／鎖定）；滑動窗（PG）為**權威**、redis L1 為負快取。
- 軟區與鎖定 MUST 在密碼雜湊驗證**之前**擋下，且**零稽核列、零計數桶**（拒絕不得消耗受害者的額度）。
- fail-* 方向：redis 整體不可用＝**fail-open**（軟區 captcha 要求整層停用、續驗密碼，密碼錯仍計數）；L2（PG）查詢失敗＝**fail-open ＋ 補償**（計數歸零放行並置 `captcha_forced`）；captcha 標記 SET NX 瞬斷（redis 健康）＝**fail-closed 不罰**（拒該次、零計數桶）。
- **來源維釐清**（004 補）：滑動窗計數的**下界來源數兩維蓄意不對稱**——帳號維**三源**（窗起點＋解鎖標記＋窗內最近成功登入）、來源維**恆兩源**（窗起點＋解鎖標記，**禁**「成功即重置」）。來源維若採成功即重置，攻擊者只需在同一來源穿插一次自有帳號的成功登入即可清零計數 ⇒ 整套來源維防護可被繞過。**MUST NOT 日後被「統一」**。
- fail-* 方向補記（004 補）：**解鎖標記讀取故障＝fail-closed**（視為無標記＝該標的可能仍在鎖定中；良性方向＝至多少解鎖、不誤放行），與本島既有的「captcha 標記 SET NX 瞬斷＝fail-closed 不罰」同族。★解鎖標記為**帳號維與來源維共用**機制（同一格式契約、兩維各自的讀取端），故其方向記於本島而非島 F。

**F. IP 存取閘＋信任錨＋來源維節流**（004-ip-trust-anchor 進場；F1～F5 沿前代已驗證形、F6 為本刀新拍板）
- ★**本島射程**＝**位址的真相面**（信任錨）與**存取判定面**（規則集）。來源維節流的**狀態機本體**（三區、滑動窗、L1／L2 分層、計數下界、解鎖標記）屬**島 E**；本島只約束其**位址輸入**（F4）與**跳過條件**（F5）。
- **F1 判定序與集合語意**：存取判定序**六步固定**——①健康／觀測端點放行 ②請求上下文缺席放行 ③結構豁免段放行 ④allow any-match 放行 ⑤deny any-match 拒絕 ⑥預設放行。規則集為 **any-match 集合語意**：白＞黑＞預設放行、**無優先序欄**、判定結果與載入順序無關。
- **F2 真相分層**：資料庫為真相、記憶體判定面**每請求零外部查詢**；**執行中**真相暫不可讀 MUST **沿用上一份已知良好規則集、不清空**（啟動初載無「上一份」可沿用 ⇒ 空集＝全放行，方向同為 fail-open）。
- **F3 fail-* 方向**：全鏈 **fail-open**；**唯一 fail-closed ＝寫端自鎖拒寫**（會把操作者自己鎖在門外的規則 MUST 拒寫、零落庫、零重載）。每次降級 MUST 發**結構化告警**。
- **F4 信任錨為唯一位址輸入**：來源維度一切機制（存取閘、來源維節流、稽核落列、防自鎖）的位址輸入 MUST 為信任錨結果；**受信集與跳過集 MUST 由同一 helper 導出、內容對稱**——兩集合分叉即真實來源塌縮為常數（前代實暴缺陷）。
- **F5 放行與節流的分界**：命中**顯式** allow 規則者跳過來源維節流；**結構豁免段 MUST NOT 跳**——結構豁免只豁免「阻擋」、不豁免「節流」。
- **F6 Tier-1 錨須傳輸層背書**（本刀新增）：Tier-1 位置錨成立 MUST 附傳輸層背書——**錨右鄰起、直到傳輸層對端，全屬受信基建**；不成立即**棄錨、退 Tier-2**。受信判定 MUST 用 F4 的同一 helper，不得為此另立第三個集合。（無此背書時，攻擊者繞過 CDN 直打來源站並自帶「偽造位址, CDN 邊緣」轉發鏈即可讓錨成立、把任意位址寫成真實來源；前代把該風險壓在「部署方 MUST 鎖 origin 僅接受 CDN 邊緣連線」的**承重部署前提**上，本條入碼後該前提降級為**縱深防禦建議**。）

**跨島註（方向刻意不一致，記於此以免日後被「統一」）**：登入流程讀 `session_idle_timeout` 設定鍵缺失＝**fail-loud**（`5000`、不猜 TTL 值），與 E 的節流設定鍵缺失走 fail-open 退常數方向相反——前者猜錯會靜默改變所有人的會話壽命，後者猜錯只影響阻力強度。

**承襲指針**：rev4 曾入憲十座行為島 A～J（single-session／token rotation／denylist 即時撤銷／閒置 sliding refresh／登入失敗節流／IP 存取閘／casbin 授權治理／選單域生命週期／使用者域治理／稽核域 reporting 與 retention），候選細目＝啟動書（docs/brainstorms/000-doc-architecture.md）§5 K1 承襲清單——對應域動刀時為 brainstorm 直接輸入、依本節進場規則隨刀重新入憲。

---

## II. 設計拍板凍結

隨 §I 未承載的獨立小拍板（拍板現況機器索引＝docs/generated/DECISIONS-INDEX.md）：

| # | 主題 | 拍板凍結 |
|---|---|---|
| #1 | unknown header | rust-api 忽略不認識的 header（如 apifoxToken）；base-web 不動 |
| #2 | auth route mode | dynamic（後端控 menu；`.env` `VITE_AUTH_ROUTE_MODE=dynamic`、ADAPT 軌道） |
| #3 | prod 路徑前綴 | `/api/*` 主流（front-nginx strip 轉發、`/api/metrics` 擋塊） |

**排程性拍板註記**：排程性結論（何時做／先做哪個）**不預載於本檔**——入波排程時逐筆重審立 ADR；重議既有排程性拍板仍走 §V.2 Amendment、**不得默改**。

---

## III. 軌道授權邊界

**跨軌道 fork-delta 執行紀律**（upstream 常態更新，本紀律使 fork 差異在 rebase 時可快速定位）：
- **修改型**（既有行語意被改變）：**原行註解保留**、緊鄰新行之上，含標記（如 `// [rev5-inline <軌道代號>] 原行: ...`）——rebase 衝突塊自含對照基準
- **新增型**（純插入新行／區塊／檔）：插入區塊以 `[rev5-inline ...+]` 標記圈界；新檔僅檔頭一行標記
- **標記統一含 `rev5-inline` token**：全 repo grep 即得完整 fork patch set（upstream 大重構時的災難重建索引）
- **rebase 同步紀律**：解衝突時，註解內「原行」同步更新為 upstream 現行版（防對照基準過時）

### III.1 預設可動軌道（無需額外授權）

| 軌道 | 範圍 | 紀律 |
|---|---|---|
| **BASE-WEB-ADAPT** | `.env*`＋`src/typings/api/` 新檔 | 新增為主；**inline 修改限根層 `.env*` 接管面**（§III.2 表外宣告 2 指定之 devproxy 涵蓋路徑）；禁止刪除既有 type／field |
| **BASE-WEB-WRAPPER** | `src/service/api/rev5-*.ts` 新檔 | 一律新檔（`rev5-` 前綴）；不改既有 service 檔 |
| **RUSTAPI-SOURCE-ISOLATION** | rust-api 整棵樹 | 全新寫；前代受控參照不拷貝（§I.5） |

### III.2 ★ 需 constitution 顯式授權軌道

**本節為 ★ 軌道的凍結位**——每條軌道與其**每一個用途**皆須經 §V.2 Amendment 明文開立；未列於下表者一律無授權（同軌道內的未列用途，不因該軌道已開而自動授權）。首批四條軌道八用途由 ADR 0028 於 v1.3.0 開立（003-auth-session）。

**機制骨架**（一切 ★ 軌道的共同紀律）：
- ★ 軌道＝base-web inline 的顯式授權邊界：嚴格限本檔已授權之用途／範圍，新用途一律走 §V.2 Amendment
- **補完 vs 新能力判準**：既有授權頁內「單頁、純加、復用既有 wrapper、零新 key/元件/路由」四條件全中的 dispatcher 補完＝**用途補完、不 bump 本檔**；跨多頁新能力＝**須 Amendment**
  - **「零新 key」釋義**（承 rev4:ADR 0041）：指**新 i18n 命名空間／新元件／新路由等「面」級新增**；**不含**既有授權頁、既有子命名空間之下的**資料級 label key**。新增 top-level i18n 命名空間、新元件／路由、跨頁能力仍須 Amendment；判準其餘三條件仍須全中
- 每改一處在 spec 內紀錄（位置＋改動內容＋upstream 衝突風險評估）
- 共用元件改動 MUST 用附加 prop＋安全預設（不變既有呼叫端行為）

**已授權軌道與用途**（機器可解表格；掃描錨＝本表標題列之後、以 `|` 起的資料列，跳分隔列；軌道名以 `**★NAME**` 包覆、掃描端剝 `**` 與 `★`。**授權名冊＝本表 ★ 軌道 ∪ §III.1 三軌道**）：

| 軌道 | 用途 | 範圍（檔案） | 紀律 |
|---|---|---|---|
| **★BASE-WEB-AUTH-WIRING** | (a) constant routes 合併 | `src/store/modules/route/index.ts`（1 處，修改型） | 僅限 `initConstantRoute` 之 else 分支；MUST 為**併入** static 常量集而非取代（seed `constant=TRUE` 為 0 列，取代會清空 login／403／404／500／iframe-page 五條 builtin）；不得擴及 route store 其他分支 |
| **★BASE-WEB-AUTH-WIRING** | (b) 三表單 stub 化 | `src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue`（各 2 處，修改型） | 僅改 import 指向 stub wrapper＋消滅假成功 toast；不動表單欄位、驗證規則與版面 |
| **★BASE-WEB-AUTH-WIRING** | (c) captcha hook 改打 stub | `src/hooks/business/captcha.ts`（4 處，修改型） | 僅改請求目標為 `/auth/sendCaptcha`＋移除假延遲與假成功 toast；hook 對外簽名不變 |
| **★BASE-WEB-LOGIN-CAPTCHA-WIRING** | (i) 登入頁 captcha 軟區 | `src/store/modules/auth/index.ts`（修改型）／`src/views/_builtin/login/modules/pwd-login.vue`（修改型＋新增型） | login 簽名加 captcha 參並串通失敗 msg 回傳鏈；軟區為條件渲染、**非軟區時零行為變更**。用途 (ii)（`formRules` 放寬）不在授權內 |
| **★BASE-WEB-I18N-WIRING** | (i) 後端 msg 轉譯 | `src/service/request/index.ts`（2 處修改型＋1 塊新增型） | `translateBackendMsg`／`translateDetailValue` 走 `$t` 並以原文 fallback；未命中 MUST graceful fallback，不得吞錯亦不得顯裸 key |
| **★BASE-WEB-I18N-WIRING** | (ii) locale backend 樹 | `src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型） | 插入錨為**獨佔一行**的 `  backend: {`；兩語鍵集 MUST 相等；譯文以該刀 contracts 之 msg-keys 為權威 |
| **★BASE-WEB-I18N-WIRING** | (iii) Schema backend 型節 | `src/typings/app.d.ts`（1 塊，新增型圈界） | 僅補 `App.I18n.Schema` 之 `backend` **必填**型節。LangType 擴充／locale 註冊／`zh-tw.ts` 標型重構不在授權內 |
| **★BASE-WEB-LOGOUT-UX-WIRING** | (i) 登出前撤銷接線 | `src/layouts/modules/global-header/components/user-avatar.vue`（1 處修改型＋2 處新增型） | `onPositiveClick` 改 async、登出前 best-effort `await fetchLogout(...)`，**失敗不得阻斷** `resetStore()`。用途 (ii)（reLogin toast）不在授權內 |
| **★BASE-WEB-MANAGE-PAGE-WIRING** | (i) IP 規則管理頁進場 | `src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型圈界；僅限 `route:` 與 `page:` 兩樹）／`src/typings/app.d.ts`（1 塊，新增型圈界；僅限 `App.I18n.Schema.page` 型節）／`src/router/elegant/{imports,routes,transform}.ts`／`src/typings/elegant-router.d.ts`（後四支＝路由外掛產物、不標記） | **①②塊**（兩語 locale 之 route:／page: 兩樹、app.d.ts 之 Schema.page 型節）：新增型圈界標記須存在；兩語鍵集 MUST 相等；page 型節為**必需非「如需」**——page: 為顯式型樹，不補型即型別檢查紅（route: 因型為 Record<I18nRouteKey, string> 才自動導出）。**③塊（產物四檔）＝產物檔紀律**：僅由路由外掛重算產出、**禁止手改**；**不要求逐行原文標記**——理由是標記於下一次重算即被抹除、物理上不可維持，寫進紀律等於立一條保證會被違反的規則；驗收改採**重算冪等檢查**（重跑外掛後與版控內容零差異），其強度高於逐行標記：標記僅是註解、無強制力，冪等檢查連單行手改都抓得到。★**本軌道機器守實況**（誠實揭露、不以含糊措辭掩蓋覆蓋缺口）：名冊斷言僅掃帶 `原行:` 的**修改型**標記〔表外宣告 3〕，本軌道三塊皆新增型或生成檔 ⇒ 名冊斷言對本軌道**結構性不適用**、MUST NOT 當驗收；①②塊實得機器守＝「圈界標記須存在」（不比對軌道名與用途）；③塊受 fork-delta 檢查全域豁免，**重算冪等檢查是其唯一機器守**，故該檢查 MUST 併斷言「本列所列生成檔集＝外掛實際產出檔集」——本列漏列一支即該支完全無守 |

**表外三項適用宣告**：
1. 範圍欄的**處數為估值**，實作期以 `rev5-inline` 標記實數為準；**檔級名單則是硬邊界**——名單外的 base-web 既有檔一律無授權，需要動即回本節走 §V.2。
2. 承襲指針散文提及的 `MODAL-WIRING` 與 `BASE-WEB-DEVPROXY-WIRING` **不在名冊**（rev5 無 modal 治理需求；devproxy 由 §III.1 的 `BASE-WEB-ADAPT` 軌道以 `.env*` 涵蓋）。
3. 新增型 `NAME+` 標記**不入名冊**（承 ADR 0021 款 1）——名冊斷言的射程僅修改型（帶 `原行:`）。

**承襲指針**：rev4 曾授權六個 ★ 軌道（MODAL-WIRING 十一用途／BASE-WEB-I18N-WIRING 四範圍／BASE-WEB-AUTH-WIRING 三接線／BASE-WEB-LOGOUT-UX-WIRING 二用途／BASE-WEB-LOGIN-CAPTCHA-WIRING 二用途／BASE-WEB-DEVPROXY-WIRING 三處），候選細目＝啟動書 §5 K1 承襲清單——對應接線需求出現時為 Amendment 提案的直接輸入。

---

## IV. Compliance Check（spec-kit `/speckit-plan` 用）

`/speckit-plan` 必須對照本 constitution 逐項 yes/no：

1. **此 plan 是否違反 §I.1 base-web 為權威紀律？** rust-api 是否未提供 base-web 用到的對應 endpoint？
2. **此 plan 是否動到 base-web inline？** 若是、屬 §III.2 哪個用途／範圍？授權邊界內？是否依 fork-delta 紀律（修改型原行註解／新增型圈界、`rev5-inline` token）？
3. **此 plan 涉及 menu 顯示是否走 Casbin enforce？**（§I.2；demo menu 是否進 seed 而非隱藏？）
4. **此 plan 的 wire 設計是否對齊 §I.3 權威序與不變式？**（envelope／逐欄位 id 型／13 碼矩陣／msg=key；mock 僅補充 fixture）
5. **此 plan 是否從前代 source 拷貝 code？** 若是、屬 §I.5 例外清單嗎？參照處是否觸發防回歸條款？
6. **此 plan 是否抵觸 §II 拍板？** 任一拍板需改變、必先走 Amendment
7. **此 plan 是否觸及 §III ★ 軌道？** 若是、在授權邊界內？屬「補完」還是「新能力」（§III.2 判準）？
8. **此 plan 是否新建業務表（create migration）？** 若是，是否含 §I.6 六審計欄（建表即帶、無 retrofit）？append-only／join 表是否依變體處理？
9. **此 plan 是否觸及 §I.7 已入憲的行為島？** 若是、各 invariants 是否保持？是否用 state-machine 鏡頭設計（非 CRUD 格子）？若屬「該入憲而未入憲」的新行為島、是否隨本刀排入 Amendment（候選來源＝啟動書 §5 K1 承襲清單）？

任一檢查不通過 → plan 須回 brainstorm 或申請 Amendment（§V.2）。

註：本題組承接 rev4 九題制；「不增列 push/merge 自查題」為已封案事項、日後不再議（該紀律由 CLAUDE.md 硬禁令＋agent prompt 烤入承載）。

---

## V. Governance

### V.1 凍結權威性

本 constitution 為 rev5 的**凍結權威**；與其他文件衝突時**以本檔為準**。文件權威鏈：

> constitution（凍結權威）＞ ADR accepted（拍板全文；索引＝docs/generated/DECISIONS-INDEX.md）＞ 活書 docs/arc42/ARCHITECTURE.md（as-built 敘事）＞ docs/generated/（機器鏡像）

本檔與 accepted ADR 不一致＝Amendment 未同步的程序錯誤，以本檔為準並立即補同步。

### V.2 Amendment 流程

1. **提案**：立 ADR draft（背景／決定／後果；註明改本檔哪一節）
2. **討論**：user 親決（本檔內容皆為 user 拍板項，Claude 不主動 amend）
3. **凍結**：ADR 轉 accepted＋更新本檔對應段＋bump version（§V.3）
4. **commit**：獨立 commit `docs(constitution): amend <條目>`（憲法改動＋ADR 同 commit）＋`docs-sync generate`

### V.3 Version 規則

- **MAJOR**（2.0.0）：鐵紀律（§I 原則）改變、§I.7 方向性不變式反轉、§II 拍板撤回、★ 軌道授權撤銷
- **MINOR**（1.1.0）：新拍板固化（§II 加項）、軌道授權邊界擴展（新用途／新範圍）、新增 ★ 軌道、**行為島隨刀進場（§I.7 填充）**、已入憲 invariant 細項調整
- **PATCH**（1.0.1）：文字校正、釐清、reference 更新、Compliance Check 增補

---

**Version**: 1.4.0 | **Ratified**: 2026-08-04 | **Last Amended**: 2026-08-15

**Amendment log**:
- 1.4.0（2026-08-15）：**§I.7 第六座行為島入憲**（島 F：IP 存取閘＋信任錨＋來源維節流）——射程分界句＋F1 判定序與集合語意／F2 真相分層 keep-last-good／F3 fail-open 且唯一 fail-closed＝寫端自鎖／F4 信任錨為唯一位址輸入且兩集合同源對稱／F5 顯式放行跳節流而結構豁免不跳（五條沿前代已驗證形）＋★**F6「Tier-1 錨須傳輸層背書」為本刀新拍板**（兌現懸兩代的硬化案，錨右鄰起至傳輸層對端全屬受信基建否則棄錨退 Tier-2；反轉＝MAJOR，連帶把「鎖 origin 僅接受 CDN 邊緣連線」由承重部署前提降為縱深防禦建議）。**島 E 補兩句**：來源維計數下界恆兩源之刻意不對稱（禁「成功即重置」、防日後被統一）／解鎖標記讀取故障＝fail-closed（★該標記為帳號維與來源維**共用**機制，故方向記於島 E 而非島 F——記進島 F 只會落得「島 F 越界管轄帳號維」或「帳號維那半無家」二擇一）。**§III.2 開第五條 ★ 軌道** `BASE-WEB-MANAGE-PAGE-WIRING` (i) IP 規則管理頁進場，範圍**七支檔逐支寫出**（兩語 locale 之 `route:`／`page:` 兩樹＋`app.d.ts` 之 `Schema.page` 型節＋路由外掛產物四檔）——第三塊採**產物檔紀律**（禁手改＋重算冪等檢查，明文載「不要求逐行原文標記」及其理由＝標記於下次重算即被抹除、物理上不可維持），並明載本軌道機器守實況與覆蓋缺口（名冊斷言只掃修改型、對本軌道結構性不適用）。**§III.1 BASE-WEB-ADAPT 紀律欄措辭收斂**（B-071：「不改 inline」→「inline 修改限根層 `.env*` 接管面」；授權邊界零變動，僅使人讀憲法與 fork-delta-lint 既有寬鬆解一致）。ADR 0040；MINOR（§V.3 之「新增 ★ 軌道」「行為島隨刀進場」「已入憲 invariant 細項調整」三款）——動機＝004-ip-trust-anchor 同時撞到三個空凍結位（行為島／★ 軌道／島 E 的一處刻意不對稱），三者皆走憲法自備的授權路徑、非違規。三處拍板點 user 親決 2026-08-15（fail-closed 歸島／射程分界句要不要補／軌道命名），替代案與棄用理由逐項記於 ADR 0040。
- 1.1.0（2026-08-05）：§I.2 demo menu 條增「例外與釋義」二款（ADR 0005；MINOR）——①toggle-auth 示範鏈（function／function_toggle-auth）對 R_ADMIN／R_USER_COMMON 之初始勾選例外（4 列、承 rev4 終態）②hideInMenu「不啟用」射程釐清（upstream route meta 原樣值非隱藏治理、6 列白名單）。動機＝001 刀 /speckit-analyze D1（CRITICAL：seed 定稿與字面衝突、過目簽核不具修憲效力）與 D2；user 親決。
- 1.2.0（2026-08-08）：§I.5 增「實作以 rev4 對應碼為預設藍本（先讀後寫、高度參照）」句＋前代 source 立場清單增「註解一律重寫」款（ADR 0019；MINOR）——動機＝應用碼施工意圖先前僅存對話、「全新寫」字面誤導新 session 從零發明；user 親決維持拷貝禁止強度（重打字消化）、放寬為逐段移植之替代案評估後棄。
- 1.3.0（2026-08-09）：§III.2 首開四條 ★ 軌道八用途（BASE-WEB-AUTH-WIRING (a)(b)(c)／BASE-WEB-LOGIN-CAPTCHA-WIRING (i)／BASE-WEB-I18N-WIRING (i)(ii)(iii)／BASE-WEB-LOGOUT-UX-WIRING (i)）並改為機器可解表格形（fork-delta-lint 名冊斷言之來源）＋表外三項適用宣告；§I.7 首批五座行為島入憲（token rotation／single-session／denylist 撤銷／idle 逾時／登入失敗節流，含各自 fail-* 方向與跨島刻意不一致註）。ADR 0028；MINOR（§V.3 之「新增 ★ 軌道」與「行為島隨刀進場」兩款）——動機＝003-auth-session 為第一把同時撞到兩個空凍結位的刀：後端補齊六支端點後 base-web 必須接線（12 處分屬四條尚未存在的軌道），且五台狀態機的 fail-* 方向不入憲則日後反轉無 MAJOR 閘。授權逐用途收窄，rev4 更寬用途集中的三項 `(ii)` 類明文不授權。user 親決。
- 1.3.1（2026-08-11）：§III.2 名冊兩處範圍欄註記對齊 as-built（ADR 0035；PATCH「文字校正、釐清」）——app.d.ts「1 處，修改型」→「1 塊，新增型圈界」；user-avatar.vue「3 處，修改型」→「1 處修改型＋2 處新增型」。授權邊界零變動（檔級名單／用途集／紀律欄一字不動）；動機＝B-068 將以名冊欄位為（軌道×用途×檔案）三元組判準，「型別」欄不準則新判定上線即誤報。user 核批工具面維護批（輕量軌；B-042 等六筆同批）組成時併同核可。
- 1.0.0（2026-08-04）：創世初版——自 rev4 constitution v1.15.0 之可攜段搬入（§I.1～§I.6 改字可攜、§I.7 僅搬進場規則、§II 三筆拍板、§III fork-delta 紀律與 §III.1 三軌道、§III.2 僅機制骨架與補完判準、§IV 九題、§V 全段；rev4 專屬之十座已入憲行為島細目與六個 ★ 軌道細目一律不預載、循 §I.7 進場規則與 §III.2 Amendment 條款隨刀進場，兩處承襲指針句與 §IV 第 9 題候選來源括註為本次新增）；全域改字＝世代代號、兩子庫長分支名、fork 標記 token、service wrapper 前綴、前代參照世代整組前移一代。user 親審 diff 後定版（創世拍板）。ADR 0001（創世採用）同 commit 轉 accepted。
