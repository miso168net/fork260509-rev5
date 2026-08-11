---
id: "0038"
title: 替代登入四流程維持誠實 stub——rev5 不提供自助註冊／驗證碼登入／自助重設密碼
date: 2026-08-12
status: accepted
supersedes: []
superseded_by: []
provenance: "輕量軌維護批（B-047／B-022 批）之 B-022 關帳拍板；user 於 2026-08-12 三選項（維持 stub／砍入口／做真）中親決取「維持 stub＋立 ADR 關帳」；現況實證＝主線逐項 grep（登入頁 module 註冊、四支 stub 端點、自助頁 route 與選單 seed）"
tags: [auth, frontend, scope]
---

## 背景

B-022 自 rev2 起橫跨三代未收，射程＝「替代登入四流程做真或砍」：驗證碼登入／註冊／
重設密碼三張登入頁表單，以及自助頁的手機驗證。

003-auth-session 已把**假成功**這一半消滅（U-M／T063）：三張表單改打 `rev5-auth.ts` 的 stub
wrapper，後端 `POST /auth/{sendCaptcha,codeLogin,register,resetPwd}` 恆回 `2222
biz.auth.notSupported`。此前它們是「validate 通過就彈成功 toast、後端根本不存在」的假象。
⇒ B-022 的殘餘射程只剩**做真或砍的拍板本身**。

as-built 實證（2026-08-12）：

- 三張表單各 70／97／91 行，**有活入口**——`views/_builtin/login/index.vue:10-13` import、
  `:32-35` 註冊為登入頁 module（另有第五個 `bind-wechat.vue`，零 fetch 零 toast 的純 UI 殼、
  射程屬 B-018 不屬本條）
- 自助頁 `user-center`：**route 與選單 seed 都已在庫**（`elegant/routes.ts:695`、
  seed.sql:53 casbin ＋ :244 menu 列），只有 view 是 7 行 `<LookForward />` 空殼

## 決定

**維持誠實 stub、不做真也不砍入口。** B-022 於本批關帳刪列。

理由三條：

1. **產品面**：本系統是 admin 後台，帳號由超管建立、角色由管理員指派。自助註冊在此語境下
   不是缺失而是**不該有的能力**；驗證碼登入與自助重設密碼同理——它們是面向 C 端的形制，
   隨 upstream fork 帶進來而非 rev5 的需求。
2. **砍入口的成本不成比例**：移除 tab 需改 `login/index.vue`（upstream 既有檔、不在任何
   ★ 軌道授權內）⇒ 須先走憲法 §III.2 Amendment 新增用途。付一次修憲換「少三個 tab」，
   而該 tab 目前的行為已是誠實回應而非欺騙。
3. **做真屬另一把刀**：需 mailer 選型（rev5 現零實作）、簡訊通道選型（全新拍板、可能涉付費
   服務）、驗證碼發送與核對狀態機、四支真端點取代 stub、自助頁從零建。這是完整 SDD 刀的
   量級，不在本批射程。

## 後果

- 使用者於登入頁點「註冊」等 tab、填完送出 → 收到 `2222` 之在地化訊息「此功能暫不支援」。
  **這是本 ADR 明文接受的終態**，不再是待辦。
- 四支 stub 端點與三張表單一律**保留原樣**：端點是誠實化的載體（拿掉它們，前端就沒有可打的
  對象、會退回更糟的形），表單是 upstream 檔、刪除反而製造 fork-delta。
- `bind-wechat.vue` 不在本 ADR 射程——它連 stub 都沒有（純靜態殼），去留隨 B-018 一次拍。
- **翻案路徑**：若日後 rev5 要開放自助註冊（例如轉多租戶），走新 ADR supersede 本檔，
  並把 §3 那三項前置（mailer／簡訊通道／狀態機）列為該刀的 research 輸入。
