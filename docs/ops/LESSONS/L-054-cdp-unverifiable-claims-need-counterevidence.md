---
promoted_to: 無：CDP 走查屬編排期活動，防法已烤進 U11 型 workflow script 的 verify review prompt（「blocker＝步驟漏驗（verdict 未驗卻無理由）」＋redo 迴圈）；下一刀沿用該 script 模板即帶防法，無穩定 repo 操作面可晉升
---
- **L-054**｜**CDP 走查回報中「無可觀察實例」與「契約豁免」兩類理由，必須附機器可查的反證（psql／grep 實查零命中）或被引契約的原文行號，否則等同未驗**：006-authz-governance U11（2026-08-24）實暴——CDP agent 首輪對已知態 8a-③ 稱「零孤兒端點鍵、無可觀察實例」（實測後坐實其推論方向錯誤：R_SUPER 端點 modal 原樣 Save 實得 0000／revoked 0／granted 0／effective 35＝ADR 0056 射程句，而非其推論的 protectedRevoke 拒）、對「自建選單指向不存在 view」步驟稱「契約明列不必實做」（該引用不存在）。兩者皆由驗證審查輪抓出、redo 輪以真操作＋psql 反證重做並改寫結論。防法：verify review 對此兩類理由一律要求證據、缺即 blocker 令 redo；CDP agent prompt 端亦應明令「已知態步驟＝實際操作觀察、不得以推論代替」。盲點＝「已知態」三字讓 agent 誤以為只需複述文件、不需現場證據。
