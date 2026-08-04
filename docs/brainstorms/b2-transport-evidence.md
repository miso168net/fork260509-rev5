# B2 工件搬運血緣證明（sha256 manifest）

> 落點＝`docs/brainstorms/`（HISTORICAL_EXEMPT 前綴，與啟動書同區之創世期史料）；創世 ADR 0001 以 provenance 引用本檔。
> ★不可落 `docs/arc42/decisions/`——`load_adrs()` 以 `endswith('.md')` 掃該目錄，任何非 `NNNN-slug.md` 形的 md 會被當成 ADR 而觸發 Lint08 檔名紅。★本檔由腳本實算產生、非手抄——首版因手動轉錄產生四處錯值與計數不符，經 B2 驗收攔下後改為機器產生。
> 源＝rev4@`2b8a101c94abcac4c62e7e77e0bb8796f1f399a8`（HEAD 凍結）。取件法＝`git -C rev4 show HEAD:<path>` 於 rev5 側落檔，rev4 全程零寫入。
> 斷言法＝落檔位元組的 sha256 逐字等於啟動書 §4.5.1 表值，任一不符即整批中止（fail-loud）。**所有雜湊為完整 64 位十六進位（sha256），非 40 位（那是 commit SHA-1 的長度）。**

## 一、原樣搬運（19 檔，rev5 落地值 ≡ rev4 源值）

| 路徑 | sha256（rev4 源＝rev5 落地，逐位元同） | index mode |
|---|---|---|
| `tools/bootstrap.sh` | `32824cd89a55ebb495a29766182db7a32646113339bf1734fbb56c259a3ed8a4` | 100755 |
| `tools/docs-sync.py` | `5843ea20c12baac7773075405aa8f6d866a608b7454e13fe948338f4e9e206e6` | 100755 |
| `tools/entity-drift-gate.py` | `b3d5a5af31bf11060ad214e0d15e2087fe1bb38535658c0c36897a8e3bdd6f23` | 100755 |
| `tools/fork-delta-lint.py` | `1c84b2ec458a300cb2bcd0c71ad97c54c623d1faf031add9d70bebf210f9ab72` | 100755 |
| `tools/schema-gate.py` | `5b020d9398e5f6b71b2cba6b4fbeda7e76907bb3f8498dc83b481eacf801da71` | 100755 |
| `tools/secret-value-guard.py` | `e169bbc6069a74f891734ceb0fac8f45b45a8ed55bd2f8c7e9b1a4e769845def` | 100755 |
| `tools/wf-watchdog.sh` | `2c8450ae7e4073fd9e84c85a52efbff3eed98c4dd70c56d6b95c6182488829ff` | 100755 |
| `tools/wire-schema.py` | `ad38cb6fe588b0328dc51fe31a4dc2d591ac8e7c44e8bc413d0b904e4dfb943a` | 100755 |
| `.githooks/pre-commit` | `0b215b09e601e006138f45fe64210000cb4c40765099878eeb79bb70f80f1a26` | 100755 |
| `.githooks/pre-push` | `c485a12f316925ebf357f9d3988770fe3f49d3e9894a05d889299cbfbdab1aa7` | 100755 |
| `.githooks/lib/scan-range.sh` | `280f669addf6e11975f04b15e0f785b6febbc8e852277cd699894f1b01a45837` | 100644 |
| `.githooks-submodule/pre-commit` | `a067209c0f67a2a037f743cb32b0a83a01384ebcde1967ef56e2f9d6764c1c2a` | 100755 |
| `.githooks-submodule/pre-push` | `d98cff74f85bd73da25c8447b5789b71b067aaf1b62e3193405dfc0bd5f836f5` | 100755 |
| `.claude/hooks/session-start.sh` | `adfb643d649b5923ad18feacdf6742c6f85082c8efcf9e33342ce9e0c50caf87` | 100644 |
| `.claude/hooks/post-workflow-reminder.py` | `d26bec6489afa9454d550db2ca8f7321aa4b0bbf651af79728934bf161c37a54` | 100755 |
| `.claude/settings.json` | `8ecac690d8c7a981de9bcc18c91ba1ec2240c40b895c3ff2a582acd57f9ca5c5` | 100644 |
| `.sops.yaml` | `bfe0a95029ac20b0ce263cfe0aca95b899d3e4c685ff8e0dcea6299c02ce8c0f` | 100644 |
| `.dockerignore` | `e3afce2333c34c94a20e2178c321ee38ddf14ebb0f1205163f895cef2b18e66f` | 100644 |
| `.graphifyignore` | `ed315be160be1f6fbc6adf78d629dd53f93914972f38dc2c17fedb87d9ed9f40` | 100644 |

## 二、裁製（3 檔，雙雜湊血緣鏈）

| 路徑 | rev4 源 sha256 | rev5 落地 sha256 | 改了什麼 |
|---|---|---|---|
| `.claude/hooks/pre-workflow-gate.py` | `c244270a65ff5dfc807e22c6258e790d5ec86ef3682dafeba84bf7b981c7624c` | `2ae04e2bbcc8ea3ec30f7f3984c7088ccb7d9e4de9697cace3d85f18d96b4437` | 兩處裸 `L-113` → `rev4:L-113`（rev5 自 L-001 空白起家，裸碼即懸空——正是 Lint11 要防的形） |
| `.gitleaks.toml` | `b9ca73bbda835064239b6f55fa019bcc683e2086fa3876f2b4736035feb7afde` | `f61dedac554d0ab07de50ae07f3236782b760da3bb81d5f2d4a6c22ccc7e7085` | 清 rev4 三條 allowlist；寫入 rev5 誤報基線兩條（§3.2 條 9 逐字）；rule id rev4-→rev5-dsn-credential-url；檔頭註解改 rev5 語境 |
| `.env.example` | `eafa5a8d759f97b7fe5305aa4d5d40d8ae18e3a759afe142b43eed5171b3421b` | `5f97946788d9944b036eef40b7b05162ca775f95d584a111a7a7563eb9320efe` | 兩處 `fork260509-rev4` → `fork260509-rev5`（SECRETS_DIR 敘述＋示例行；同長度換字故 bytes 不變） |

**B2 搬運合計＝19＋3＝22 檔**（與啟動書 §4.5.1 manifest 逐檔對賬通過）。

## 三、B1 產物（2 檔，非 B2 搬運、一併留證）

| 路徑 | rev4 源 sha256 | rev5 落地 sha256 | index mode | 說明 |
|---|---|---|---|---|
| `.gitignore` | `9142b428911e0ebcaf45829911f8076ce96012f8ddfe3ffafd9ee1fe55ab6202` | `bbd052100298c96d6430869eb341f094ef6057d55c3141197b2b81dd0c0b3202` | 100644 | 抄 rev4 HEAD 版後四處調整：刪 rev4 docs 源倉行（rev5 無此物）；標頭語境改 rev5；worktree 註解分支長名改 rev5；前代編號補 rev4: 語境 |
| `.gitattributes` | `fc7e7bcc6c543cc7df41cbe3c938c50a21c452e4c6c2e9b5249d834a7034fb11` | `fc7e7bcc6c543cc7df41cbe3c938c50a21c452e4c6c2e9b5249d834a7034fb11`（≡ 源） | 100644 | 依 rev4 內容手寫，事後驗證與 rev4 **逐位元相同** |

## 四、docs 骨架與啟動書移位

六目錄建齊：`docs/arc42/decisions`、`docs/generated/reference`、`docs/ops`、`docs/ops/reference-src`、`docs/reviews`、`docs/brainstorms`。
★git 不版控空目錄——四個創世時仍空的目錄各置 `.gitkeep`（沿 rev4 先例：rev4 亦有 `docs/arc42/decisions/.gitkeep` 與 `docs/reviews/.gitkeep`），否則 B7 後任何 clone 與 B8b 拋棄式副本都拿不到骨架。

啟動書 `INTEGRATION-rev5-arc42.md` → `docs/brainstorms/000-doc-architecture.md`（Lint15 自撞處方，§3.2 條 7）。
移位後身分驗證：**2392 行**、sha256 `f639b29400a46fca9f15ba2dbc7959d64477effdf81f19bc31cb418c00840c4c`——與啟動書自檢第 2／3 條期望值逐字相符。此後自檢改指新路徑。

刻意不搬：`.gitmodules`（B9 手寫）、`README.md`／`CLAUDE.md`（B5 骨架落地）、`deploy/` 全域（B5b，§4.2 B2 ③）、`backend-msg-dict.json`（治外飛地機器生成物，gen.msg_dict 豁免解除後由 generate 重產）。

## 五、掃描實測（B0 後半結案；§3.2 條 9 雙向突變實證）

| # | 掃描 | config | rc | findings | 留證 |
|---|---|---|---|---|---|
| 1 | 全樹盤點 `betterleaks dir .` | rev5 版（基線兩條在） | **0** | 0 | `b2-scan-positive.txt` / `.json` |
| 2 | 突變反證 同上 | 拔第②條之副本 | **2** | 1 | `b2-scan-mutated.txt` / `.json` |
| 3 | staged `betterleaks git --pre-commit --staged`（B7 真閘同形） | rev5 版 | **0** | 0 | `b2-scan-staged.txt` / `.json` |

第 2 筆命中明細（可獨立覆核）：`File=docs/brainstorms/000-doc-architecture.md`、`RuleID=generic-api-key`、`StartLine=335`——命中者即啟動書內嵌的 events 範例列，規則即 `generic-api-key`，與 §3.2 條 9 預期完全一致。

兩 config 的唯一差異即誤報基線第②條那一段；拔除即命中、加回即乾淨 → 該豁免為 **load-bearing 非裝飾**（樣板不變量 5 要求的突變實證，此處已預付）。

★rc 已寫入各 `.txt` 末行（副檔名非 `.log`——`.gitignore` 的 `*.log` 規則會讓實測紀錄無法入版、覆核性落空）、finding 明細寫入各 `.json`，均可離線獨立覆核，不依賴本檔轉述。
