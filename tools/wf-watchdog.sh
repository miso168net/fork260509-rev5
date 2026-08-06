#!/usr/bin/env bash
# tools/wf-watchdog.sh — Workflow 看門狗（CLAUDE.md §2、rev4:L-104/rev4:L-112）
#
# 用法：Monitor 工具 command 欄填 `bash tools/wf-watchdog.sh [冒煙token]`
#   ★必與 Workflow launch 同一回合原子成對發射（兩 call 間零其他動作）。
#   自動發現本專案最新 wf_* transcript 目錄（毋需 launch 回傳值→可同回合並發）。
# 行為：sleep 10 讓 launch 建目錄 → ARMED 一行（夾帶冒煙：implementer transcript
#   首行 byte 數＋冒煙 token 命中數）→ 靜默迴圈，僅 stall／runaway 告警時輸出並退出。
# 完成通知一到請 TaskStop 本 Monitor（否則正常完成 ~13min 後誤觸 stall）。
set -u
# ★rev4:L-142：本檔含中文字串——mac（實證 mac2、bash 5.3）部分 locale 下 bash 解析
#   「$smoke（」類「變數名＋全形字」邊界會黏成未綁定變數名而炸；byte-wise 解析免疫。
export LC_ALL=C
TOKEN="${1:-}"
STALL=780      # 秒；>最長合法 cargo（sub-agent Bash 單命令 600s 上限＋margin）
RUNAWAY=25     # 不重複 agent key 數；2× 單元理論上限（防呆③ AGENT_FUSE=20 之外部 backstop）
#   ★判準＝數 journal 不重複 agent key、★不數行數（rev5 差分，承 rev4:L-144 同族實證）：
#   行數型 backstop 在 kill/resume 疊代下累積誤報——同一支 agent 每輪 launch 都留新事件列，
#   journal 行數線性成長而實際併發 agent 數不變（實證：三輪 launch 使 journal 達 26 行觸發
#   RUNAWAY 誤報，實際不重複 key＝10≤11 理論上限、保險絲完好）。key 去重後才等價於「派了幾支」。

# 專案 slug＝canonical path 之 / 與 _ 全轉 -（Claude Code projects 目錄命名規則）。
# ★realpath 解析綁定路徑：primary working dir 可能是 /home/… 綁定（pwd 給非 canonical、
#  slug 對不上 -mnt-d-… projects 目錄名→找不到 wf；rev4:B-070、rev4:006 orchestration 實測）。
CANON=$(realpath "$PWD" 2>/dev/null || pwd)
SLUG=$(printf '%s' "$CANON" | sed 's|[/_]|-|g')
sleep 10
ROOT=$(ls -dt "$HOME/.claude/projects/$SLUG"/*/subagents/workflows 2>/dev/null | head -1)
DIR=$(ls -dt "${ROOT:-/nonexistent}"/wf_* 2>/dev/null | head -1)
if [ -z "${DIR:-}" ]; then
  echo "看門狗 發射失敗？找不到 wf transcript 目錄（slug=${SLUG}）——確認 Workflow 已 launch"
  exit 1
fi

# 冒煙：最早的 agent transcript（＝implementer）首行完整性
f=$(ls -t "$DIR"/agent-*.jsonl 2>/dev/null | tail -1)
smoke="尚無 agent transcript（疑零派發 throw 或未啟動）"
if [ -n "${f:-}" ]; then
  bytes=$(head -1 "$f" | wc -c)
  hit="-"
  [ -n "$TOKEN" ] && hit=$(head -1 "$f" | grep -c -- "$TOKEN" || true)
  smoke="impl首行${bytes}bytes／token(${TOKEN:-無})命中=${hit}"
fi
echo "看門狗 ARMED → $(basename "$DIR")｜冒煙: ${smoke}（stall>${STALL}s／runaway>${RUNAWAY}key；完成通知到請 TaskStop 本 Monitor）"

while true; do
  sleep 60
  now=$(date +%s)
  # 最新 mtime（epoch）：GNU find -printf 先試（Linux）；macOS BSD find 無 -printf→
  # 落空時以 BSD stat -f '%m' 兜底（rev4:L-139：勿反序——GNU stat -f 是檔案系統狀態、%m=掛載點）
  newest=$(find "$DIR" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1); newest=${newest%.*}
  if [ -z "${newest:-}" ]; then
    newest=$(find "$DIR" -type f -exec stat -f '%m' {} + 2>/dev/null | sort -n | tail -1)
  fi
  if [ -z "${newest:-}" ]; then
    echo "看門狗 目錄不可讀：$(basename "$DIR")——疑被清或發射失敗"
    break
  fi
  idle=$(( now - newest ))
  # ★頂層鍵定錨（L-002）：逐行 JSON 解析、只取事件物件 top-level 的 "key"——扁平 grep
  #   會把 result payload 巢狀同名鍵（如 coverage[].key＝"FR-001"）一併計入，實證 9 支
  #   真 agent 被數成 31 → RUNAWAY 誤報。壞行跳過（擋壞行非本工具職責）。
  #   ★另設判準健全性檢查：journal 非空卻抽不到任何 key＝抽取與實際格式脫節，此時
  #   保險絲恆 0＝永不觸發＝靜默失效，故 fail-loud。
  jl=$(python3 -c '
import json, sys
ks = set()
try:
    for line in open(sys.argv[1]):
        try:
            e = json.loads(line)
        except Exception:
            continue
        k = e.get("key") if isinstance(e, dict) else None
        if isinstance(k, str):
            ks.add(k)
except OSError:
    pass
print(len(ks))
' "$DIR/journal.jsonl" 2>/dev/null || echo 0)
  jraw=$(wc -l < "$DIR/journal.jsonl" 2>/dev/null || echo 0)
  if [ "${jraw:-0}" -gt 0 ] && [ "${jl:-0}" -eq 0 ]; then
    echo "看門狗 判準失效：journal ${jraw}行 但抽不到任何 agent key——RUNAWAY 保險絲已恆 0、形同卸除→立即人工查 journal 格式"
    break
  fi
  if [ "${jl:-0}" -gt "$RUNAWAY" ]; then
    echo "看門狗 RUNAWAY：不重複 agent key ${jl} > ${RUNAWAY}（防呆③保險絲疑失效）→ /workflows 查→TaskStop wf"
    break
  fi
  if [ "$idle" -gt "$STALL" ]; then
    echo "看門狗 STALL：${idle}s 無寫入 > ${STALL}s（疑卡死/死迴圈）→ /workflows 查→TaskStop→修 script→resumeFromRunId 續跑"
    break
  fi
done
