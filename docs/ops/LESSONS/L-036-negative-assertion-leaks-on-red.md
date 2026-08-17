---
promoted_to: rust-api/server/src/handler/ip_rule.rs 測試清理註兩處（通則已就地標注）
---
- **L-036**｜**只在「回歸發生時」才漏出 committed 列的測試，平常全綠、紅的那一次順手弄髒共用 dev 庫**：004 U-M 的 `t069_chain_rejection_precedes_password_hashing_with_no_success_side_effect` 以**密碼正確**的帳號發逾窗鏈、斷言仍被拒。正常態下請求在拒絕腿早退 ⇒ 不落 `sys_token`；但**拒絕腿一旦回歸**，該請求就真的登入成功、落一列 committed `sys_token`，而測試拿不到 sid、掛不上 `ChainRowsCleanup` ⇒ **紅的那一次同時汙染共用庫**，後續 `schema-gate` gate2 的 seed 逐列 diff 會在**數個單元之後**才爆，爆點與成因完全對不上（同 L-031 的證據錯位形，但成因相反：L-031 是走查留列毒化測試，本條是測試在紅的那一刻留列毒化閘）。★該測在本單元的 M6 變異測中**實暴**（確實漏出一列），implementer 當場清除並補上守。★**防法**：①凡「斷言某副作用**不該**發生」的測試，其清理 MUST 覆蓋「副作用真的發生了」那條路徑——不能只清自己**預期會建立**的東西；②清理呼叫點擺在**斷言之前**（L-031 已立，本條是它的另一半：L-031 管的是「斷言 panic 時清理跑不到」，本條管的是「清理**不知道有東西要清**」）；③做法上可用「測前記錄基準列數／測後刪除該基準之後的所有列」取代「刪除已知 id」，讓清理不倚賴對副作用的預期。★**識別法**：測試名含 `no_..._side_effect`／`does_not_create`／`precedes_` 者一律套用本條複查。

