<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# DECISIONS-INDEX — ADR 索引

| id | status | date | title | feature | supersedes | superseded_by |
|---|---|---|---|---|---|---|
| 0001 | accepted | 2026-08-04 | rev5 創世採用——治理工件直搬＋憲法 v1.0.0 定版（波 -1 文件地基一鍋 commit） | — | — | — |
| 0002 | accepted | 2026-08-04 | 預算白名單反轉延後——列創世後首批治理調整（顯式延後立案） | — | — | — |
| 0003 | accepted | 2026-08-04 | 值比對層佔位字面白名單——佔位值非機密（secret-value-guard 射程釐清） | — | — | — |
| 0004 | accepted | 2026-08-05 | host 埠配號 2xxxx 世代制——翻案啟動書 5xxxx 錯開表（避開 macOS ephemeral 範圍） | — | — | — |
| 0005 | accepted | 2026-08-05 | 憲法 §I.2 demo menu 條例外與釋義——toggle-auth 示範鏈三角色初始勾選＋hideInMenu 射程 | — | — | — |
| 0006 | accepted | 2026-08-05 | schema 基線＝rev4 終態壓平＋user 定稿制（波 0、m001／m002 兩支基線遷移） | — | — | — |
| 0007 | accepted | 2026-08-05 | schema 閘契約＝Day-1 受管演進帳（凍結面＋演進登記合成全等比對） | — | — | — |
| 0008 | accepted | 2026-08-06 | DB 身分不帶世代後綴（soybean／soybean_admin_rust；世代錯開射程＝host 共享面） | — | — | — |
| 0009 | accepted | 2026-08-06 | K1／K2 前代知識處置流水總帳（K1 隨刀重審機制＋K2 二十二筆三分流） | — | — | — |
| 0010 | accepted | 2026-08-06 | bash→python 選擇性轉換範圍總帳（轉換集 5 支＋不做集 16 支＋兩硬約束） | — | — | — |
| 0011 | accepted | 2026-08-06 | 外部工具版本三分類政策（一次性輔助工具沿 latest） | — | — | — |
| 0012 | accepted | 2026-08-07 | 編號命名空間紀律（跨代裸編號的前綴口徑與防復發閘） | — | — | — |
| 0013 | accepted | 2026-08-07 | decrypt passphrase 自動應答（只打一次）之安全姿態 | — | — | — |
| 0014 | accepted | 2026-08-07 | prod 不入 rev5 roadmap——各刀留 seam、不交付 prod 資產 | — | — | — |
| 0015 | accepted | 2026-08-07 | 機密選型前提複核未觸發——四反轉條件過境＋雙持鑰復原兩補強 | — | — | — |
| 0016 | accepted | 2026-08-07 | audit 變體 B 禁欄判準＝前綴通配＋具名豁免出口 | — | — | — |
| 0017 | accepted | 2026-08-07 | Lint06 arch_impact 比對基準改 merge^1:BOOK（「本刀影響」語意） | — | — | — |
| 0018 | accepted | 2026-08-08 | B12 前端腿＝接線層先行（typings＋service 新檔）、view 延 B-008 | — | — | — |
| 0019 | accepted | 2026-08-08 | 應用碼施工紀律——高度參照 rev4 為預設藍本（重打字消化形）、註解一律重寫 | — | — | — |
| 0020 | accepted | 2026-08-08 | gen.msg_dict Day-1 豁免改謂詞續留——en-us 接線延前端 i18n 刀 | — | — | — |
| 0021 | accepted | 2026-08-08 | §III ★軌道授權射程釋義——base-web 純新增檔不需軌道、zh-tw.ts 治理錨點孤立檔 | — | — | — |
| 0022 | accepted | 2026-08-08 | 授權拒絕語意與 no-escalation seam 定形——5003＋純 i18n key 起步、掛點簽章預留 async 與 db | — | — | — |
| 0023 | accepted | 2026-08-08 | 部分更新三態約定（B-026 envelope 級定形）——缺席不動／JSON null 清空／有值設值 | — | — | — |
| 0024 | accepted | 2026-08-08 | 守門機制必附非 vacuous 生效自證——合成正例＋判準來源獨立＋落地破壞性驗證 | — | — | — |
| 0025 | accepted | 2026-08-08 | 憲法 §I.5「註解一律重寫」射程釋義——執行期診斷字串是碼不是註解、逐字同 rev4 不違憲 | — | — | — |
| 0026 | accepted | 2026-08-09 | gate2 seed normalize 擴入「環境相依噪音」族——版本行剝除＋Owner 值正規化，配 owner 一致性補償守門 | — | — | — |
| 0027 | accepted | 2026-08-09 | dev 驗收入口統一為 http://127.0.0.1:22080——curl 與瀏覽器全程鎖同一 origin | — | — | — |
| 0028 | accepted | 2026-08-09 | 憲法 Amendment 1.2.0→1.3.0——§III.2 首批四條 ★ 軌道八用途授權＋§I.7 首批五座行為島入憲 | — | — | — |
| 0029 | superseded | 2026-08-09 | AppState 兩欄→五欄翻案——加 jwt／cache／captcha_secret，ip_rules／trust_model／mailer 續留域外 | — | — | 0041 |
| 0030 | accepted | 2026-08-09 | ADR 0021 §3 射程收窄——app.d.ts backend 型節本刀提前，LangType／locale 註冊／zh-tw.ts 標型重構仍延後 | — | — | — |
| 0031 | accepted | 2026-08-09 | 動詞不符回 4040＋HTTP 404——B-047 兩候選取①，正面處置「13 碼矩陣無動詞不符語意」的張力 | — | — | — |
| 0032 | accepted | 2026-08-09 | root Cargo.toml「不引 argon2」翻案——引入六支 auth 依賴，後六支續留域外 | — | — | — |
| 0033 | accepted | 2026-08-09 | 003-auth-session 已知態集五項（by-design／排程錨，非缺陷） | — | — | — |
| 0034 | accepted | 2026-08-09 | contract 測 stub 連線改用 connect_lazy 假連線——research R7-1 的 MockDatabase 方案經實證不可行 | — | — | — |
| 0035 | accepted | 2026-08-11 | §III.2 名冊兩處範圍欄註記對齊 as-built（PATCH 校正） | — | — | — |
| 0036 | accepted | 2026-08-11 | gate2 seed 對 runtime-append 表的表級收窄 | — | — | — |
| 0037 | accepted | 2026-08-11 | events 帳本新增 erratum 事件型與 Lint18 更正視圖 | — | — | — |
| 0038 | accepted | 2026-08-12 | 替代登入四流程維持誠實 stub——rev5 不提供自助註冊／驗證碼登入／自助重設密碼 | — | — | — |
| 0039 | superseded | 2026-08-12 | ip_* 三個來源節流鍵已 seed 但零執行面消費者＝已知態（解除謂詞＝B-019 落地） | — | — | 0042 |
| 0040 | accepted | 2026-08-15 | 憲法 Amendment 1.4.0——§I.7 第六座行為島（島 F）＋§III.2 第五條 ★ 軌道（管理域新頁接線）＋島 E 來源維釐清＋§III.1 ADAPT 紀律欄措辭收斂 | — | — | — |
| 0041 | accepted | 2026-08-15 | AppState 由恰五欄擴為恰七欄（信任模型＋規則判定面）——翻案 ADR 0029 之五欄封條 | — | 0029 | — |
| 0042 | accepted | 2026-08-15 | 004-ip-trust-anchor 已知態集（四項續存＋一項重評不動）＋明文解除「ip_* 三鍵零消費者」 | — | 0039 | — |
| 0043 | accepted | 2026-08-15 | 轉發鏈跳數逾上界即拒絕（fail-closed 第二腿）＋稽核轉錄保留判定窗＋計數維度分流 | — | — | — |
| 0044 | accepted | 2026-08-17 | pre-commit 全鏈時間門檻改為雙錨（警戒 45s／硬擋 90s），並把「收刀簿記型實測」列為每刀例行量測 | — | — | — |
| 0045 | accepted | 2026-08-17 | LESSONS 由分卷制改分檔制——手寫索引＋一坑一檔＋晉升必答欄 promoted_to | — | — | — |
| 0046 | accepted | 2026-08-18 | dev compose 信任模型路徑改 YAML anchor 同源＋long-form volume——消抄本、分岔物理上不可能 | — | — | — |
| 0047 | accepted | 2026-08-18 | 憲法修訂日誌引量紀律——凍結量／指節不指數／時點自證三形擇一，人審不設 lint | — | — | — |
| 0048 | accepted | 2026-08-18 | 憲法 Amendment 1.7.0——§I.7 第七座行為島（島 H 選單域生命週期）＋§III.2 MANAGE-PAGE-WIRING 用途 (ii)（role／menu 管理頁 CRUD 接真）＋B-087 殘餘②補註 | — | — | — |
| 0049 | accepted | 2026-08-18 | 判定面同步進場——翻案「boot 載入即終態」＋rebuild-swap reload 契約（硬禁令＋casbin 版本鎖＋ABBA 三失效條件） | — | — | — |
| 0050 | accepted | 2026-08-18 | A1 域行為——deleteRole 家族入序列化域＋免 reload 論證＋島 G 行為 ADR 承載（G1/G3/G4/G5）＋archive 三自由度 won't-use 與翻案觸發條款過境 | — | — | — |
| 0051 | accepted | 2026-08-22 | restoreMenu 復原重驗補常量父鏈腿——閉合軟刪常量後代繞道窗（B-095 處置拍板） | — | — | — |
| 0052 | accepted | 2026-08-22 | unplugin 元件宣告生成檔併入產物檔紀律——components.d.ts 同族不入憲法用途名單 | — | — | — |
| 0053 | accepted | 2026-08-23 | 憲法 Amendment 1.8.0——§I.7 第八座行為島（島 G casbin 授權治理、含 G6 結構性封死）＋§III.2 MANAGE-PAGE-WIRING 用途 (iii)(iv)（三顆授權 modal 接真＋policy-archive 頁）＋§III 正文納 ADR 0052 生成檔條款＋B-104 觸發矩陣訂正 | — | — | — |
| 0054 | accepted | 2026-08-23 | 結構性封死——治理面受保護端點政策 MUST NOT 授予非 R_SUPER（島 G6 設計全文、掛點恰兩處、非 vacuous 自證、B-024① 歸宿與 no-escalation 翻案觸發條款） | — | — | — |
| 0055 | accepted | 2026-08-23 | restorePolicy 鎖內固定序五腿重驗＋restorable 旗標逐腿同判準＋ADR 0050 §4 翻案觸發條款復核結論 B（reason gate 三值→五值、手動撤銷之選單／按鈕維歸檔列不可復原） | — | — | — |
| 0056 | accepted | 2026-08-23 | 三維授權全量替換之射程＝候選集——候選外現役列不撤不授不入 effective（rev5 路由註冊表遞增 vs seed 完整之實況拍板） | — | — | — |
| 0057 | accepted | 2026-08-24 | rust 格式守門——rustfmt 設定釘 max_width=100＋use_small_heuristics=Max（存量 diff 實測最小）、閘以納冊工具承載並於 pre-commit 條件式呼叫容器（stack 在跑才實跑、不在跑具名跳過） | — | — | — |
| 0058 | accepted | 2026-08-25 | 活書 §6／§8 單節配額一次性放寬（120→160、90→130）＋停損條款——再撞頂改走 as-built 下放、停損之機器承載＝釘值測絆線 | — | — | — |
| 0059 | accepted | 2026-08-25 | logout 呈遞 rotated 票維持 0000 靜默 no-op——sys_token 狀態機矩陣缺格之裁決（撤銷射程恆為單列、不擴 revoke_family） | — | — | — |
