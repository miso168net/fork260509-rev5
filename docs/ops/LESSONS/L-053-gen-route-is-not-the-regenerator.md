---
promoted_to: （佔位：候選晉升位＝tools/route-artifact-gate.py 檔頭「重算者」段或 docs/ops/RUNBOOK.md 前端段——待有人再撞到第二次再晉升）
---
- **L-053**｜**`pnpm gen-route`（soybean CLI `sa gen-route`）不是 elegant-router 產物四檔的重算指令**：它是互動式 route 腳手架（容器內 `-T` 跑即印 `please enter route name`、stdin EOF 後 rc=0 零寫檔——看起來像成功、實則什麼都沒做）。真正的重算者＝dev server 內的 elegant-router vite 外掛（新 view 目錄落地即自動重算、容器 log 有 `[elegant-router] … regenerated successfully`）＋`tools/route-artifact-gate.py check` 的沙盒重跑（重算冪等閘）。防法：新增 view 頁的施工序寫成「建目錄→核 `git -C base-web status` 四檔變動（dev server 須在跑）→route-artifact-gate check」，勿寫「跑 gen-route」。實暴＝006-authz-governance U7a（2026-08-23）implementer 照 prompt 跑 gen-route、發現零寫檔後改核 dev server log 才對上。盲點＝package.json scripts 名「gen-route」直觀上像重算指令。
