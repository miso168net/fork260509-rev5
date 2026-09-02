---
id: "0079"
title: AuditOperation 封閉詞彙集加第九值 purge（小寫動作名）——推翻「恰八值」定案、purge 自記列之詞彙前提
date: 2026-09-01
status: accepted
supersedes: []
superseded_by: []
provenance: "008-audit-settings-pages 之 U0（T003 附帶親決題〔第四題〕：user 親決 2026-09-01 取形 (a)＝U0 內補立專屬 ADR、編號 0079）；缺口揭露鏈＝ADR 0077 款二「詞彙前置條件」——tasks.md 無任何一條任務建本 ADR＝派工單缺口、由主線補立；被推翻之定案＝007-user-password-admin 期之「詞彙集恰八值」（rust-api/server/src/model/audit.rs 測 t013_user_password_family_adds_three_vocabulary_stays_eight 釘死、其訊息自陳變動須新 ADR 連同本測改寫——本檔即該新 ADR）；rev4 藍本＝rev4 憲法 §I.7 島 J3 之 PURGE 自記形（僅語意承襲；其大寫字面依 ADR 0019 不得帶回）；同批拍板＝ADR 0077（島 J 入憲）／ADR 0078（BizData 第三鍵）"
tags: [audit, model, vocabulary, governance]
---

## 背景

本刀（008-audit-settings-pages）的 purge 端點依 spec FR-C03 於單一交易水平線 DELETE 後
同交易自落一筆操作日誌自記列，該列的 `operation` 欄值必須是
`rust-api/server/src/model/audit.rs` 之 `AuditOperation` enum 成員（`AuditEvent.operation`
的欄型即該 enum、DB 存值＝`as_str` 字面）。而該 enum 由 `audit_operation_vocabulary!`
單一宣告源展開，現為**恰八值、全小寫**（add／update／delete／restore／unlock／kick／
reset_password／change_password）、**無 purge** ⇒ purge 自記列在型別上根本寫不出來，
除非先加第九值。

「恰八值」是 007-user-password-admin 期的**定案**，有測釘死：同檔測
`t013_user_password_family_adds_three_vocabulary_stays_eight` 斷言
`AuditOperation::ALL.len() == 8`，訊息逐字「定案：詞彙集恰八值……變動＝推翻定案、須新 ADR
連同本測改寫」——依定案自陳，加第九值必以新 ADR 承載；本檔即該新 ADR。

★另據實記載：本刀 SDD 包起草時沿用了 rev4 的**大寫** `PURGE` 字面（起草時快照＝四行三檔：
`quickstart.md`／`tasks.md`／`data-model.md`），而 rev5 詞彙紀律為**小寫動作名**——同檔判準
fn `closed_vocabulary_violation` 對大寫值直接以 `WHY_UPPERCASE` 判違規（常數逐字「大寫形——
rev5 詞彙軸為小寫動作名，rev4 大寫 DB 動詞形不得帶回」）。該字面改對已於本單元（U0b）
同批完成（見後果段）。

## 決定

1. **第九值＝`Purge => "purge"`**（**小寫**、沿 rev5 小寫動作名紀律；**非** rev4 之大寫
   `PURGE` 形）。宣告位＝`audit_operation_vocabulary!` macro 呼叫點**末位**（宣告序＝
   進場刀時序、`change_password` 之後）；語意＝歷史清理（retention 水平線刪除）之自記動作，
   詞彙「隨消費刀進場才加」的既有紀律不變——本值的消費刀即本刀。
2. **實作面三處連動改動＋同檔 doc 註假述面同批改對**（逐條寫明；★本 ADR 只拍板、**不動碼**，實作歸本刀 **T014**——單元收攏由 executing-plans 現場批判複核、非定值，故只記 T 編號）：
   ① macro 呼叫點加 `Purge => "purge"` variant（enum／`as_str`／受檢面 `ALL` 同一次展開
   自動跟進）；
   ② `EXPECTED_LITERALS` 由 `[&str; 8]` 增為 `[&str; 9]`、新字面 `"purge"` 插於與宣告序
   相同之位（末位）——手寫期望清單與 `ALL` **恰等比對**（含序）的紀律不變，故插錯位即紅；
   ③ 測 `t013_user_password_family_adds_three_vocabulary_stays_eight` 之 `ALL.len()` 期望值
   8→9，**測名與斷言訊息連同改寫**（改寫後訊息以本檔為新定案出處）。
   ★**①②③恰對應同檔自陳之三處同步清單**（`closed_vocabulary_violation` doc 逐字「macro
   呼叫點（受檢面）＋`EXPECTED_LITERALS`＋主測的恰值常數」），但**不等於本次改動的全部**：
   第九值一落地，同檔多處 doc 註之「八值」「八個字面」「現八字面」「恰八值」即成假述，
   MUST 與①②③**同批**改對（L-032——凡改變某數字／集合即枚舉全面命中逐處改對）。
   ★待改對面**以掃源現算、不落第二份字面名冊**（形照後果段對 `PURGE` 的處置）：
   `grep -n "八" rust-api/server/src/model/audit.rs` 逐行判別，兩類排除——`ip_confidence`
   之「來源信心八態」屬他軸、不在射程；「005 T005 立、007 T013 改為八值形」一類**史述**
   （過去式敘事）照 L-032 保留。改完以同一指令復掃驗收。
3. **次序約束**：本 ADR MUST 早於 T014 開工——T014 開工前提＝本檔已 accepted（形照
   ADR 0077／ADR 0078 對 purge BizData 構造點之同型次序約束、spec FR-G01）。

## 後果

- 詞彙集自此**恰九值**；字面契約釘子（`EXPECTED_LITERALS` 與 `ALL` 恰等比對、測
  `audit_operation_literals_are_the_db_contract`）之受檢面同步擴一。
- ★島 J 已隨本刀同批入憲（ADR 0077 甲案、憲法 1.10.0），其 J3 之「操作日誌源之水平線
  DELETE MUST 固定豁免歷史清理自記列」的唯一實作依據即自記列的本值（rev5 字面＝
  `operation <> 'purge'`、小寫）——條文與本 ADR 互為前提：本 ADR 未 accepted 前該 MUST
  無法履行。
- SDD 包沿用之 rev4 大寫字面已於本單元同批改對（詞彙值類全改小寫；常數名 `PURGE_MIN_DAYS`
  大寫正確、不在射程）；驗收判準＝`grep -rn "PURGE" specs/008-audit-settings-pages/` 逐行
  剝除 `PURGE_MIN_DAYS` token 後零詞彙值命中（★逐行剝 token 而非整行過濾——同一行可同時
  含常數名與詞彙值）。
- 日後第十值＝同一路徑：新 ADR 承載＋macro 呼叫點與 `EXPECTED_LITERALS` 與恰值測同批改；
  「只在某處多寫一個字串字面」仍為違約形（封閉詞彙紀律不變）。
