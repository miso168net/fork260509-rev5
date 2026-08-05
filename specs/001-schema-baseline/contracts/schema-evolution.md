# contracts/schema-evolution.md — 演進登記檔契約

> 檔＝`docs/ops/reference-src/schema-evolution.json`（單一登記檔、與快照同家——specs/
> 下屬凍結史料、放彼處違時態語意）。消費者＝tools/schema-gate.py（gate1／gate2 合成）。
> lineage：spec FR-009、brainstorm §3、ADR 待立②。

## 1. 形（schema）

```json
{
  "next_id": 1,
  "entries": [
    {
      "id": "E-001",
      "knife": "005-example-feature",
      "kind": "add_column",
      "table": "sys_user",
      "detail": {"column": "new_col", "type": "text", "nullable": true,
                 "default": null, "position": "末位"},
      "date": "2026-09-01"
    }
  ]
}
```

- `kind` 枚舉（恰八值）：`add_table`／`add_column`／`alter_column`／`add_index`／
  `add_constraint`／`seed_add`／`seed_update`／`seed_delete`。
- `detail` 形依 kind 而異，MUST 足以讓 gate 機器合成期望值（add_table＝全欄清單；
  add_index／add_constraint＝name＋definition；seed_*＝table＋pk＋逐欄值）。
- **基線初始態**＝`{"next_id": 1, "entries": []}`（001 刀落地即此形；凍結面即全部期望）。

## 2. 啟動斷言（gate 每跑必驗；任一敗＝rc 2 fail-loud、絕不靜默放行）

1. 頂層鍵恰集 `{next_id, entries}`；`next_id` 正整數；`entries` 為 list。
2. 逐筆欄位齊全非空：`id`／`knife`／`kind`／`table`／`detail`／`date`。
3. `id` 格式 `^E-\d{3}$`、全檔唯一、遞增、**永不回收**（`next_id` ＝ 最大號＋1）。
4. `knife` 格式 `^\d{3}-[a-z0-9-]+$`（來源刀編號＝feature branch 名）。
5. `kind` 入枚舉；`date` 格式 `YYYY-MM-DD`。
6. `kind=drop_*` 不存在——刪除性演進＝拍板級、走新 ADR＋基線翻案，不入登記檔。

## 3. 生命週期

- **append-only**：每筆一經合成生效即不可改（改帳＝漂移歷史）；寫錯＝新 entry 修正並於
  detail 註明 supersedes。
- 登記時點＝該刀 migration 落地同刀（Day-1 紀律、contracts/gates.md §5）；
  「migration 已跑、登記缺席」＝gate1 紅之常態語意（未登記漂移）。
- 基線翻案（重壓平）＝新刀立新 fixtures＋清空 entries＋新 ADR supersedes——不回改本檔形。
