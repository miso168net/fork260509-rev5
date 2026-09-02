# msg keys — 008（backend 拒因鍵；譯文權威＝本表、I18N-WIRING (ii) 依此落三檔）

> 新增恰兩鍵、皆 `biz.audit.*`；與 rust 構造點**同 commit** 落 zh-tw.ts／zh-cn.ts／
> en-us.ts 三檔 backend 樹（zh-tw＝Lint24 契約錨、zh-cn＝Lint24 第二腿、en-us＝msg-dict
> 兩語斷言）＋app.d.ts backend 型節。zh-tw 插位＝`biz:` 節內字母序（`auth` 前）。
> 攜參鍵佔位符＝Lint24 第三腿（本刀新增）對賬面。

| key | 攜參 | zh-tw | zh-cn | en-us |
|---|---|---|---|---|
| `biz.audit.invalidTable` | — | 清理目標不在允許清單內 | 清理目标不在允许清单内 | The purge target is not in the allowed list |
| `biz.audit.purgeBelowFloor` | `{minDays}`（data 頂層鍵 `minDays`、BizData） | 清理保留天數不可低於 {minDays} 天 | 清理保留天数不可低于 {minDays} 天 | Retention days cannot be below {minDays} days |

註：
- zh-cn／en-us 譯文＝rev4 逐字（zh-cn.ts:102-105／en-us.ts:102-105）；zh-tw＝本刀新譯
  （rev4 zh-tw 未盤、以本表為準）。
- `purgeBelowFloor` 之佔位符 `{minDays}` MUST 逐字＝後端 `json!({ "minDays": … })` 頂層
  鍵（三語一致；Lint24 第三腿機器守）。
- BizData 射程擴列（密碼二鍵＋本鍵）＝U0 補充 ADR 承載（research D4）。
