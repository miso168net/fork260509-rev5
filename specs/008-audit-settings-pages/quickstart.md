# Quickstart — 008 驗收動線（Phase 1；驗證指南、非實作清單）

## 前置

- dev stack 起（rev5：22080 UI／22079 API）；rev4 對照 stack 起（42080；
  `../fork260509-rev4/` 根 `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait`）。
- rust 驗證一律容器內、全程 serial；host 瀏覽器帶 `--remote-debugging-port=9229` 供 CDP。

## 1. 後端面（每單元邊界＋收刀）

```bash
# 容器內全量（serial；基線 1015 → 本刀後預期 +N）
docker compose exec rust-api cargo test --workspace -- --test-threads=1
# 容器內 fmt（完工前）
docker compose exec rust-api cargo fmt --all
```

預期：0 failed；新增面含——router 不變式（ROUTES_COUNT 66）、5 contract case、
`Api.Audit.*` wire_schema 裁判、audit handler 真 DB 測（授權矩陣＋seed 對賬）、
purge 原子性 fault-injection（注入自記失敗→整筆回滾；紅綠證留單元紀錄）、
logout TTL 同形測、`mask_pii_payload` 表驅動＋端到端負向自證。

## 2. 治理閘（pre-commit 全跑；手動速查）

```bash
python3 tools/docs-sync.py lint          # 條款數維持 29（第三腿掛 Lint24 底下）；Lint24 第三腿（佔位符）自測綠
python3 tools/fork-delta-lint.py         # WIRING 圈界＋基線斷言
python3 tools/view-render-guard.py       # 新頁自動入射程（7 禁字面）
python3 tools/route-artifact-gate.py     # 產物四檔重算冪等
python3 tools/seed-view-gate.py          # EXEMPT 已摘、零豁免綠
cd base-web && pnpm typecheck            # page 型節／route 鍵全綠
```

變異自證（一次性、附紅綠證）：zh-tw `{minDays}` 改名→Lint24 紅→還原綠；
purge 自記改吞錯→原子性測紅→還原綠（L-063／L-065 紀律：還原守衛先行）。

## 3. CDP 三方對照（真登入走查；RUNBOOK §9c 六步、次序不可反）

1. `python3 tools/walkthrough-baseline.py snapshot tmp/walkthrough-baseline.json`
2. 走查（127.0.0.1、Super／123456；42080 vs 22080 開雙分頁）：
   - **煙測反轉**：側欄「系統設定」「稽核中心」＝翻譯後文字、點擊正常進頁
     （基線已知態＝零反應＋原始 i18n key）。
   - settings 頁：四組 16 鍵逐項對照 rev4；改一鍵→成功 toast→回讀一致；
     非法值→拒因 toast（翻譯後、非裸鍵）→畫面回退。
   - audit 頁：四分頁逐欄對照 rev4——**唯一允許差異＝XFF 欄**（ADR 0076 例外註記）；
     op-log 快照 dialog；login 分頁 throttleNote 告示；access 分頁空列表＝已知態；
     region／traceId 恆「-」＝已知態（驗形不驗值）。
   - **XSS 注入驗證**（SC-003）：以 CDP Fetch 注入帶
     `X-Forwarded-For: <script>alert(1)</script>, 10.0.0.1` 的登入請求產生一列
     login_attempt → audit 頁該列 XFF 欄顯示字面文字、零 alert、零 DOM script 節點。
   - purge：輸入 29 → 拒因帶「30 天」字樣；輸入 3650 送出（二次確認）→
     deletedCount=0 toast＋op-log 多一筆 purge 自記（走查清理面涵蓋）。
3. 清理（§9c 判準形：被寫過的全部表與鍵還原；runtime-append 四表清列＋seq 復位）。
4. `python3 tools/walkthrough-baseline.py diff tmp/walkthrough-baseline.json` → **rc 0**。
5. 容器內全量測試再跑一輪（rc 0）。
6. `python3 tools/schema-gate.py check` 三閘綠。

## 4. 收刀面速查

seed-view-gate EXEMPT 零列；BACKLOG 六條關帳（B-008／B-072／B-078／B-125／B-139＋
豁免表摘列已含）；U0 產物（憲法 vNext＋Amendment ADR〔0077〕＋BizData 射程補充 ADR〔0078〕＋詞彙第九值 ADR〔0079〕）已
accepted；merge --no-ff 前 user 同意（硬禁令）。
