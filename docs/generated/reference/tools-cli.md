<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/tools-cli — 治理工具命令真表

來源＝治理工具名冊 13 支掃源（python 12 支＝分派表字串比較字面、去重排序；bash 1 支＝存在與檔頭用法行）。消費者＝lint Lint19 命令形條款（語料＝CLAUDE.md／README.md／docs/ops/RUNBOOK.md 三件活手冊）＋人讀。

## tools/docs-sync.py
- 語言：python
- 子命令：`check`｜`errata`｜`generate`｜`lint`｜`refresh`｜`test`

## tools/fork-delta-lint.py
- 語言：python
- 子命令：（無——源碼無分派表、直跑）

## tools/schema-gate.py
- 語言：python
- 子命令：`check`｜`doccheck`｜`test`

## tools/wire-schema.py
- 語言：python
- 子命令：`check`｜`extract`｜`test`

## tools/secret-value-guard.py
- 語言：python
- 子命令：`check`｜`test`

## tools/entity-drift-gate.py
- 語言：python
- 子命令：`check`｜`test`

## tools/wf-watchdog.py
- 語言：python
- 子命令：`test`

## deploy/preflight-secrets.py
- 語言：python
- 子命令：`test`

## deploy/decrypt-secrets.py
- 語言：python
- 子命令：`test`

## deploy/generate-secrets.py
- 語言：python
- 子命令：`test`

## deploy/setup-reaper-role.py
- 語言：python
- 子命令：`test`

## deploy/backup-db.py
- 語言：python
- 子命令：`dump`｜`restore`｜`test`

## tools/bootstrap.sh
- 語言：bash
- 存在：是
- 檔頭用法行：（檔頭前 10 行無「用法」註解行）
