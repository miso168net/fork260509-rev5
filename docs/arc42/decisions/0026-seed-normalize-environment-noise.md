---
id: "0026"
title: gate2 seed normalize 擴入「環境相依噪音」族——版本行剝除＋Owner 值正規化，配 owner 一致性補償守門
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "BACKLOG B-011（001 收刀留帳、條目自陳「契約級變更」）；輕量軌維護批（B-049／B-052／B-045／B-042②／B-011 五項）單元② 施工；先例＝ADR 0016（同刀把 tools/schema-gate.py 實作與 contracts/gates.md 條文對齊為同一語意）；補償守門之非 vacuous 要求＝ADR 0024"
tags: [schema-gate, seed, gate, normalize]
---

## 背景

gate2 seed 面的比對法是「凍結 `fixtures/seed.sql`（左源）與實庫 `pg_dump --data-only`
（右源）經**同一支** normalize 後未排序逐列 diff」。原 normalize 只處理**非決定性**噪音
兩類（`\restrict`／`\unrestrict` 隨機 token 行、`seaql_migrations` COPY 段），其契約條文
（`specs/001-schema-baseline/contracts/gates.md` §2）並附 2026-08-05 兩座 pristine 獨立
重放的位元 diff 實證，結論是「非決定性恰此兩處」。

該結論在其射程內正確，但比對面裡還躺著另一族噪音：**同環境穩定、換環境即異**。

- `-- Dumped from database version 18.4`／`-- Dumped by pg_dump version 18.4` 兩行
  ——postgres 或 pg_dump 一升版就變。
- `-- Data for Name: X; Type: TABLE DATA; Schema: public; Owner: soybean` 共 26 行的
  `Owner:` 值——DB 身分一變就全部變。**ADR 0008 那次即為此形**：DB 身分自
  `soybean_rev5` 回滾為 `soybean`，schema 與 seed 資料內容位元零變，卻逼 001 凍結
  fixtures 重產一次（該 ADR「後果」末條載明）。

兩者都不是「資料漂移」，卻會讓 gate2 整面紅在純噪音上。B-011 的觸發條件寫「postgres
升版前必做」——升版當天閘會紅，而紅的是 28 行毫無意義的差異，屆時最省事的處置是重產
fixtures，等於用「重產凍結面」換「看不懂的紅」，正是凍結面該避免的行為。

## 決定

1. **normalize 噪音類別由二類擴為四類、分兩族成文**：
   - 非決定性族（原有）：①`\restrict`／`\unrestrict` token 行 ②`seaql_migrations` COPY 段。
   - 環境相依族（本 ADR 新增）：③pg_dump 兩行版本註解**整行剝除** ④`; Owner: X` 的
     **值**正規化為固定佔位 `-`。
2. **④ 只剝值、不剝整行**：`-- Data for Name: seaql_migrations; …; Owner: x` 亦帶
   `Owner:`，剝整行會連帶炸掉 ② 賴以認出該 stanza 的判頭。此為實作硬約束、寫入條文。
3. **新增 owner 一致性檢查作為補償守門**（`compare_dump_owner`）：對實庫 dump **原文**
   （normalize 前）取 `Owner:` 值集合，須恰為單元素且等於連線身分（`--user`／`DB_USER`
   單一來源）；不符＝一筆具名 DRIFT finding。**零命中亦紅**——比對面為空不得靜默判綠。
4. **③④ 不觸發 fixtures 重產**：左右兩源走同一支 normalize，凍結面無須改動。
5. 條文（gates.md §2）與實作同刀對齊為同一語意（沿 ADR 0016 先例）。

## 後果

- 「守門面縮減」被明確換成「守門面轉形」：DB 身分變更從 26 行 diff 噪音，變成一行寫明
  病因與處置的 finding；pg_dump／postgres 升版不再紅在版本行。
- **實證（真 fixture、同一輸入）**：模擬 postgres 18.4→19.1 升版 ＋ DB 身分
  soybean→newrole ——舊 normalize 判紅、差異 28 行（2 版本行＋26 Owner 行）；新 normalize
  判綠、差異 0 行。gate2 seed 比對面自 488 行降為 486 行。
- **補償守門的非 vacuous 自證**（ADR 0024 三要求）：自測含健康綠／全庫身分變更紅／
  多主人 schema（值集合非單元素）紅／零 Owner 行紅／★誤收 normalize 後文本必紅（接錯
  輸入即恆綠的形，明文釘住）；落地破壞性驗證＝對實庫暫改期望身分跑 `check`，rc 1 並輸出
  指名 finding。
- owner 值的期望來源綁在連線身分上：日後若出現「刻意的多主人 schema」（如 reaper role
  持有部分表），本判準會紅——屆時應擴為「值集合 ⊆ 已授權身分集合」而非就地放寬為不檢查。
- B-011 條目所寫的「fixtures 重產一次」經實證為誤記（兩源同 normalize），收單時勘誤。
