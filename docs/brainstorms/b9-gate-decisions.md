# B9 前拍板閘・裁決紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-04。裁決者＝user。
> 本閘四件：Q9／clone 來源／upstream remote 補步驟／push 同意——實測後僅一件需拍板。

## 實測（唯讀 ls-remote 四路、零寫入）

| 路 | 實得 |
|---|---|
| upstream `soybeanjs/soybean-admin` example tip | `8be6f9ba68c2e0878a1fd3ebacb5dd4f8d06dae5`＝拍板起點逐字相同、**未前進** |
| fork 前端源倉 | example 同 SHA；rev1~rev4 歷代分支俱在；`rev5-admin-base-web` 尚無（B9 建） |
| 後端源倉 | `main` tip＝`32c52542…9787`＝Initial commit 本身、起點零歧義 |
| rev4 本機源倉 | example 同 SHA——本地與 GitHub 兩來源內容等價 |

## 裁決

1. **Q9＝前提不成立、自然消解**：題目是「tip 若已前進——跟進或釘舊」；實測未前進，B9 建分支照 `8be6f9ba`、零歧義。日後 upstream 前進的跟進紀律由 CLAUDE.md §3（rebase 程序）承載，非一次性拍板。
2. **clone 來源＝甲・GitHub 直 clone**（user 拍板）：兩倉都直接 `git clone https://github.com/miso168net/…`。理由：§4.5.7 明文形；origin 天生正確**免 remote 重指**（乙缺口的「set-url 全篇無本體」風險面直接消失）；血緣最乾淨。代價＝一次性全量下載、可接受。rev4 本地 clone 先例的動機（省流量）非紀律、偏離記本檔即可。`--reference` 案因 alternates 對 rev4 目錄的隱形耐久耦合遭否（與兩代錯開取向相悖）。
3. **upstream remote 補步驟＝工程自拍（回報備查）**：前端源倉 clone 後補 `git remote add upstream https://github.com/soybeanjs/soybean-admin.git`＋push URL 設 no_push 鎖——CLAUDE.md §3 rebase 程序預設其存在（丙缺口），由既有條文推導、非新拍板。後端無 upstream（全新寫）、不加。
4. **push 同意**：依絕對禁令「當回合明確同意」——B9 執行到「push 兩分支上 remote」該步時停下問，本閘不預授。
