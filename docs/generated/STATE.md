<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=7b7cd86｜rust-api=0161d73

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：69（accepted 67、superseded 2）
- BACKLOG 待辦：38（next：B-150）｜滯後：8
- LESSONS：72 筆（next：L-073）
- events：41 筆（feature_close 7、misc 34）

## 最近事件（尾 3 筆、新在前）
- 2026-08-30｜feature_close｜007-user-password-admin｜使用者與密碼治理縱切（本代第七刀、刀 B）：管理面十支＋自助兩支＝12 支端點，ROUTES 49→61 終值、POLICY 35→45 終態。六底座＝密碼政策單一驗證點／設密冷卻／改密舊密節流（第三個節流子系統）／no-escalation 掛滿八支寫端＋unlock 帳號維／斷權四路與三 reason 不互換／自助路由白名單帶回。前端 user 管理頁接真（七碼逐鈕 gating、解鎖 modal 雙維、回收桶）＋個人中心改密卡＋登入表單降必填。測試 829→998、wire-schema 75→89、憲法 1.8.0→1.9.1、ADR 0063～0069、零 migration。
- 2026-08-25｜misc｜B-126 關帳（輕量軌、merge 5cd4319、ADR 0062）：活書 as-built 下放首例——§8 fork-delta 接線段 45 行逐位元搬至附屬文件 FORK-DELTA-WIRING.md、§5 測試設施清冊 18 行下放 test_db 模組 doc；§5 85→70／§8 92→53、配額表整張不動（絆線零改動）；§9／§11 判為指針節、維持 5／3。docs-sync 掃描面擴至附屬文件（BOOK_ANNEXES、自測 529→533）。
- 2026-08-25｜misc｜B-130 關帳（輕量軌、merge a3cd9f8、ADR 0061）：pre-commit 全鏈 43.46s→13.09s（3.3×）。★原列三處置面全數證偽——都假設成本在條款邏輯，實測是 drvfs I/O 稅（lint 的檔案系統原語佔 64%、邏輯僅 7%；fork-delta 的 select.poll 佔 99%）。A＝閘並行派發（機密面序列前導、fail-fast 改 run-all）；B＝_read 作用域快取＋EAFP＋git show 並行預取。守門三調整＋三變異紅證，529 案全綠。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
