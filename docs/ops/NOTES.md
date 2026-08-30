# NOTES — 當前意圖／下一步

- **已收官**（過去式細節一律查 events＋git，此處只留查用指針；★2026-08-30 依本段自陳紀律壓縮 001～003
  期批次——逐批全文在 `events.jsonl`）：創世序列 B0～B11｜提前批 B-035～B-039｜B12 前維護批｜
  **002-system-settings**（server crate 首落地）｜衛生維護批 cdf6eb7｜帳面更正批 ea4a470｜
  **003-auth-session**（merge 537b021、本代最大一刀：ROUTES 4→16 終態、測試 145→321、憲法 1.3.0、
  DAY1_EXEMPTIONS 自此空表）｜工具面維護批 b5e1be5｜帳面缺口批 988faf9｜
  **004-ip-trust-anchor**（merge 9141e14、B-019 關帳：信任錨還原八態＋IP 存取閘與門鈴熱重載＋
  IP 規則管理頁與五支端點＋來源維節流＋管理員解鎖端點，ROUTES 16→22 終態、rust 測試 321→512、
  憲法 1.3.1→1.6.2＝島 F 入憲＋第五條 ★ 軌道，ADR 0040～0044；新守門工具兩支）｜
  **B-090 LESSONS 分檔制遷移批**（輕量軌、merge ae5c24d：分卷制→分檔制——手寫索引＋
  一坑一檔＋晉升必答欄 promoted_to（實值 35／佔位 12→B-091 承載）、47 條 byte-diff 逐位
  搬運、Lint26＋單條上限＋Lint09 head 視野聯集、ADR 0045、docs-sync 自測 496→517）｜
  **治理工具鏈整併批**（輕量軌、merge d72553b：B-080 納冊（TOOLS_PY 14）＋B-081 Lint27
  README 樹對賬＋B-086 compose anchor 消抄本＋B-092 bootstrap 物理化＋B-087 半關；
  ADR 0046／0047、L-048、lint 條款 26、docs-sync 自測 524）｜
  **005-role-menu-crud**（merge 0125f8c、本代第五刀）：role＋menu CRUD 16 端點、ROUTES 38
  終態、測試 512→650、憲法 1.7.0（島 H＋用途(ii)）、ADR 0048～0052、零 migration；序列化域
  ＋rebuild-swap 熱重載＋歸檔寫入面三底座就緒（授權治理刀依賴面全兌現）｜
  **授權治理刀起手維護批**（輕量軌、merge 524d8b9：B-094 收攏＝handler/common.rs 六件（★該批當時之數；現為八件——B-108 收第七、007 T017 收第八）＋facade violated_constraint、
  B-101 test_db::test_state 單一字面＋(Router, AppState) 變體、B-085 自證測、B-102 三測、B-098 十二裁判；四筆關帳、測試 650→682）｜
  **006-authz-governance**（merge 307ed51、本代第六刀、B-088 關帳）：三維授權治理 11 端點、ROUTES 49 終態、測試 682→793、憲法 1.8.0（島 G＋(iii)(iv)）、ADR 0053～0056、零 migration；
  封死＋射程＝候選集＋五腿 restore；三 modal 接真＋policy-archive 頁；seed-view-gate；wire 75。
  啟動書 §5 自此為候選清單史料（K1→各刀階段 0、K2→BACKLOG 條目本文；★其內裸 B／L 編號屬 rev4 空間、Lint25 掃描面外＝L-014）｜
  **刀 B 起手維護批**（批次 A、輕量軌、merge 3d72756）：測試設施＋工具鏈九筆關帳（B-121／B-122 守衛面根因、B-109／B-110／B-051 收攏遷位、B-056 seam、B-114／B-118、B-112 rust 格式守門上線）；ADR 0057、L-056、工具名冊 15→16 支、rust 測試 793、零 migration｜
  **007-user-password-admin**（merge 5e8b32f、本代第七刀、刀 B）：使用者與密碼治理 12 支端點、
  ROUTES 61 終值／POLICY 45 終態；密碼政策單一驗證點＋設密冷卻＋改密節流＋no-escalation 掛滿八支寫端
  ＋斷權四路與三 reason 不互換＋自助路由白名單；前端 user 管理頁接真＋個人中心改密卡。測試 829→998、
  wire-schema 75→89、憲法 1.8.0→**1.9.1**（島 I 入憲＋I5 澄清）、ADR 0063～0069、零 migration；
  關帳十二條、新教訓 L-063～L-072｜
  **刀 B 前置維護批**（輕量軌、merge 53d7a67）：11 筆關帳（B-083 配額＋停損絆線／ADR 0058；B-106 消 N+1／B-108／B-115／B-123；B-111／B-075／B-074 三道守門；B-100／B-116／B-117 前端三件 CDP 實證含反例）；L-057～L-061、rust 測試 829、零 migration。
- 兩筆待補：B-035 雙平台 DoD 之 macOS 側；setup-reaper 正向 ALTER ROLE 待建 reaper role 之刀。帶 migration 的刀沿用 001 紀律（收刀前 refresh＋演進帳登記＋三閘綠，RUNBOOK §10）。

- **其餘在案候選**：B-008 餘兩張 view（＋audit 5 端點；豁免表到期即紅）；B-124／B-125／B-131～B-133（★B-127／B-128／B-129 已由 007-user-password-admin 關帳）。★另六條已滯後（查全帳須併看 BACKLOG-DEFERRED.md）；B-057 已裁關帳（ADR 0059＝維持現行、代價與翻案觸發器逐字入該 ADR）。
- **★下一動作＝待 user 拍板下一刀**（007 已收官、無預拍者）。候選群：①**B-008 餘兩張 view ＋ audit 五端點**
  （豁免表到期即紅、時間壓力最明確）②**治理工具面三條同族**＝B-146／B-147／B-148（皆「文件／碼註對賬」類新
  lint 條款，同批做最省）③**B-149 急迫**（RUNBOOK 900/900 零餘裕，下一個寫它的人當場被擋；結構解＝新開
  `PERF-DATAPOINTS.md` 附屬文件）④餘 B-124／B-125／B-133。★SDD 五步之 specify **手動**起手；維護項走輕量軌。
- **效能現況**（詳＝RUNBOOK §12.1）：全鏈四型（文件 13.89／基礎鏈中位數 14.617／pin bump 19.41／merge
  4.55s）皆遠低於 45s 警戒、引信未觸發。★**merge commit 不跑 pre-commit**（無 `pre-merge-commit` hook）——「最重情境在 merge 那顆」的舊期待已由 007 實測推翻；真實上界仍是情境 B。
