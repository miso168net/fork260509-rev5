---
id: "0014"
title: prod 不入 rev5 roadmap——各刀留 seam、不交付 prod 資產
date: 2026-08-07
status: accepted
supersedes: []
superseded_by: []
provenance: "BACKLOG B-031（啟動書 §5.2 K2-10、ADR 0009 乙組顯式待答）；user 拍板 2026-08-07；拍板素材＝B12 開刀前 BACKLOG 全項唯讀偵查（4 agent 接地、詳同日 misc 事件）"
tags: [scope, roadmap, deployment]
---

## 背景

rev5 現況零 prod 資產：compose 僅 dev 一套（docker-compose.yml 檔頭明文「prod override
歸部署刀」而該刀不存在）；nginx 僅 dev.conf、全 deploy/ 零 CSP；CF 邊緣網段清單空集
（信任錨 CDN 半邊 dev 恆不生效）；GeoIP 資料檔不存在（sys_operation_log.region／
sys_login_attempt.region 恆空）；.sops.yaml 兩把 recipients 皆開發機公鑰（prod 分層
要求「不含開發機公鑰」）；零 CI——rev4 判「結構性不可測」的前提原樣仍在。RUNBOOK §15.6
並把「機密定期輪替節奏未拍板」明文懸掛在本題。

## 決定

prod 部署**不入 rev5 roadmap**：本代交付到 dev／驗證完備；各刀為 prod **留 seam、
不交付 prod 資產**。連帶四項一併拍定：

1. 本代不得宣稱「prod 機密已納管」（rev4 決策檔原話過境）。
2. region 欄前端 UI 本代先不做（欄值恆空、不做永遠沒資料的功能；對應管理 UI 刀
   brainstorm 引用本條）。
3. 機密定期輪替節奏＝維持觸發式（RUNBOOK §15.6 懸置就此解除）。
4. 多副本 LB 假設不成立——auth／節流等狀態面按單副本 dev 前提設計，留 seam 即可
   （denylist／計數不強制全 redis）。

## 後果

- 五件散裝（部署 checklist＋CDN origin 鎖定、prod CSP、GeoIP COPY、加密檔分層、
  多副本拓樸）維持待辦形、不升格正式刀；B-019 的部署 checklist 改明文併入 ingress
  刀交付物（防止再度散裝化）。
- 日後要上線＝新 ADR supersede 本檔＋prod 部署刀立案＋CI 母體另案立案（自動化驗收
  的前置）。
- 旁接：prod DB owner 若異於 dev（soybean），B-011 的 Owner 行噪音會提早引爆——
  該題觸發時一併看。
