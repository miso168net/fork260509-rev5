#!/bin/sh
# SessionStart hook：git 健檢＋ops/NOTES＋generated/STATE（注入預算 ≤5k tokens）
cd "$(dirname "$0")/../.." || exit 0

echo "=== git 健檢 ==="
echo "branch: $(git branch --show-current 2>/dev/null)"
git status --short 2>/dev/null | head -20
git submodule status 2>/dev/null
echo "（判讀：pin≠worktree HEAD→先判方向：worktree 在前＝回外層 bump pin／pin 在前＝worktree 內 merge --ff-only 該 pin〔此時回外層 bump 會抹掉他人 commit〕；兩向皆永不 submodule update；worktree 斷裂/新機→bash tools/bootstrap.sh 重建/體檢）"
echo
echo "=== docs/ops/NOTES.md ==="
cat docs/ops/NOTES.md 2>/dev/null
echo
echo "=== docs/generated/STATE.md ==="
cat docs/generated/STATE.md 2>/dev/null
