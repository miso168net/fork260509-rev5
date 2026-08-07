---
id: "0019"
title: 應用碼施工紀律——高度參照 rev4 為預設藍本（重打字消化形）、註解一律重寫
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "user 拍板 2026-08-08 兩題：條文層級＝ADR＋CLAUDE.md＋憲法三層全落；參照強度＝維持憲法 §I.5 重打字消化、不放寬拷貝禁止。背景＝rev5 重修動機（治理前置化，如 sops/age 自 rev4:019 提前到創世）不含重新發明應用碼"
tags: [workflow, constitution-amendment, source-reference]
---

## 背景

rev5＝rev4 的重修版：動機是把治理拉到專案初期（機密管線、掃描防線、文件系統——已隨
創世與維護批收官）與腳本整理重構，**不是**重寫應用碼——base-web／rust-api 的應用邏輯
經 rev4 二十刀實戰驗證。惟此意圖先前僅存對話：CLAUDE.md §1「全新寫」字面反而把新
session 推向從零發明；憲法 §I.5 有受控參照條款、但「高度參照＝預設施工法」與「註解
一律重寫」未顯式。參照面實查：兩源倉皆有 rev4 分支（origin/rev4-admin-rust-api／
origin/rev4-admin-base-web、唯讀查閱即可）；本機另有 ../fork260509-rev4 傘狀 repo
（rev4 specs 與 ADR 全文，可自其 origin clone、非 rev5 版控面）。

## 決定

1. **高度參照＝預設施工法**：每個實作單元動工前**必先讀 rev4 對應碼**（源倉 rev4
   分支唯讀），結構／邏輯／命名以 rev4 為藍本；不重新發明已驗證的形。
2. **參照強度＝維持 §I.5 拷貝禁止**（user 顯式重申）：重新打字消化、不可整段複製；
   防回歸條款照舊——rev5 拍板已推翻的行為不得帶回。執行面＝各刀 plan 之 research
   必列「rev4 對應碼清單＋rev5 拍板差異點」（K1 翻案項／K3 教訓／rev5 spec 牴觸處，
   例：K1-26 已棄 rev4 全域 1..=1024 捷徑），實作與 review 逐單元對照。
3. **★註解一律重寫**：不拷 rev4 註解；rev5 語境重寫（引 rev5 契約／ADR）；rev4 出處
   依 ADR 0012 帶 `rev4:` 前綴。
4. **base-web 側機制不變**：inline 改動仍走憲法 §III 軌道授權（rev4 六 ★ 軌道＝日後
   Amendment 直接輸入、§III.2 指針既載）；fork-delta「原行」標記依 **rev5 基線**重打、
   不得沿用 rev4 的原行值。
5. **憲法 Amendment**（隨本 ADR、MINOR 1.1.0→1.2.0）：§I.5 規則句補「實作以 rev4
   對應碼為預設藍本（先讀後寫、高度參照）」＋前代 source 立場清單補「註解一律重寫」款。
6. **操作條文入 CLAUDE.md**：§1 拓樸句釐清、§2 SDD plan research 動作、§2 編排範本
   不可違反項（烤進每支 implementer／fix／review agent prompt）。

## 後果

- 每刀 research 多一份 rev4 對應碼清單（002-system-settings 起適用）；review 判準含
  「註解非 rev4 拷貝、差異點已對照」。
- 重打字消化＝實作較慢，換得每行經手的防回歸執行面（user 權衡後選定；放寬為逐段移植
  之替代案已評估並棄）。
- 日後若改判逐段移植＝翻案本 ADR＋§I.5 該半條（新 ADR supersede）。
