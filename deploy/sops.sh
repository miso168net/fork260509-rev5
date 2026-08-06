#!/usr/bin/env bash
# deploy/sops.sh — sops 官方容器 wrapper（rev4:019-secrets-sops；契約＝contracts/secret-pipeline.md rev4:§P1）
#
# 用法：自 repo 根執行 ./deploy/sops.sh <sops 參數...>
#   例：./deploy/sops.sh -e --filename-override deploy/secrets.dev.enc.yaml tmp/plain.yaml
#       ./deploy/sops.sh -d deploy/secrets.dev.enc.yaml
#
# 契約要點（rev4:P1.1~rev4:P1.7）：
#   rev4:P1.1 映像 digest 釘版（registry 與 digest 成對；tag 可被重推、digest 不可變）
#   rev4:P1.2 互動旗標條件化：stdin 是 tty 才配 -i -t；非互動時 sops 需要互動會自己吵鬧失敗、不 hang
#        （★stdout 重導向＋-t 並存時，容器 pty 會把輸出換行改 CRLF、且 passphrase 提示行與
#          stdout 同流——呼叫端須自行剝 CR 並濾掉非資料行，deploy/decrypt-secrets.sh 的
#          key 行 parser 即此設計；人工呼叫端同受此限＝RUNBOOK §15.7 步驟 1 之正規化片段。
#          ★不需 passphrase 的子命令（-e 等）呼叫端補 `< /dev/null` 即讓本分支不成立、
#          從根上不生 CRLF 與併流——RUNBOOK §15.7 步驟 3 用的就是這一招）
#   rev4:P1.3 不轉發 host EDITOR（映像已內建 EDITOR=vim；host 值多指向容器內不存在的程式）
#   rev4:P1.4 顯式 -e 三變數（docker 未以 -e 列出的環境變數一律被靜默丟棄）
#   rev4:P1.5 必須自 repo 根執行——否則容器內 /work 無 .sops.yaml、sops 自己吵鬧失敗
#        （config file not found＝可接受的失敗訊息、即指引）
#   rev4:P1.6 明文產物一律 host shell 收 stdout＋umask 077；不用 sops 的 --output／-i（in-place）
#        產明文（映像以 root 執行、容器直寫產物＝root:root）——此為呼叫端紀律、wrapper 不產檔
#   rev4:P1.7 exec bit 以 git update-index --chmod=+x 落 index（drvfs 上 chmod 不落 index）
#   ★rev5 增補（**非 P1 契約條款**）：私鑰單檔掛載與選鑰口徑，見下方掛載段註解

set -euo pipefail

# rev4:P1.1 digest 釘版常數（rev4:T002 拍板：ghcr.io v3.13.3-alpine 之 multi-arch index digest）
SOPS_IMAGE="ghcr.io/getsops/sops@sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea"

# rev4:P1.2 互動旗標條件化（stdin 有 tty 才配；B′ passphrase 提示需要容器內 tty）
TTY_FLAGS=()
if [ -t 0 ]; then
    TTY_FLAGS=(-i -t)
fi

# 私鑰唯讀掛載（容器內 HOME=/root → sops 預設尋鑰路徑＝/root/.config/sops/age/keys.txt）
# ★跨代並存機必須讓容器內**恰有一把** identity：掛整個目錄會讓 sops 連同預設路徑的
#   keys.txt（他代的鑰）一併載入，並對「每個 recipient × 每把鑰」各索一次 passphrase；
#   提示與資料同流不可見（rev4:P1.2 註），任一次空答即以 `passphrase can't be empty` 整體
#   失敗、且訊息指向錯方向（實證 2026-08-06 加入第二位 recipient 當日；L-005）。
# 選鑰口徑：RV5_AGE_KEY_FILE（host 絕對路徑）優先，否則取命名紀律預設檔名
#   keys-fork260509-rev5.txt（＝repo 目錄名，同 SECRETS_DIR／keygen 快取之字面慣例）。
AGE_KEY_DIR="${HOME}/.config/sops/age"
if [ -n "${RV5_AGE_KEY_FILE:-}" ]; then
    # ★-v 來源不存在時 docker 自動建**目錄**佔位（同 RUNBOOK §1 第 4 步 nginx 憑證坑），
    #   故先指名退出、不放行到 docker run
    case "$RV5_AGE_KEY_FILE" in /*) ;; *)
        echo "FAIL：RV5_AGE_KEY_FILE 須為 host 端絕對路徑（現值：${RV5_AGE_KEY_FILE}）" >&2; exit 1 ;;
    esac
    [ -f "$RV5_AGE_KEY_FILE" ] \
        || { echo "FAIL：RV5_AGE_KEY_FILE 指向的檔案不存在（${RV5_AGE_KEY_FILE}）" >&2; exit 1; }
fi
RV5_KEY="${RV5_AGE_KEY_FILE:-$AGE_KEY_DIR/keys-fork260509-rev5.txt}"
KEY_MOUNT=()
KEY_ENV=(-e SOPS_AGE_KEY_FILE)
if [ -f "$RV5_KEY" ]; then
    # 單檔掛到容器內預設尋鑰路徑＝容器內恰一把 identity；SOPS_AGE_KEY_FILE 顯式覆寫成該
    # 路徑，使沿用舊命令形（含 shell history）者不因 host 路徑在容器內不存在而失敗
    KEY_MOUNT=(-v "${RV5_KEY}:/root/.config/sops/age/keys.txt:ro")
    KEY_ENV=(-e "SOPS_AGE_KEY_FILE=/root/.config/sops/age/keys.txt")
elif [ -d "$AGE_KEY_DIR" ]; then
    KEY_MOUNT=(-v "${AGE_KEY_DIR}:/root/.config/sops/age:ro")   # 舊行為原樣保留
    echo "提示：未見 ${AGE_KEY_DIR}/keys-fork260509-rev5.txt，改掛整個目錄；本機若同時持有多代 age 私鑰，把 rev5 那把改名為此檔名即可免除多餘的 passphrase 提示（命名紀律＝檔名取 repo 目錄名）。" >&2
fi

# rev4:P1.3／rev4:P1.4：只顯式轉發 SOPS_AGE_* 三變數；EDITOR 一律不轉發
exec docker run --rm \
    "${TTY_FLAGS[@]}" \
    "${KEY_MOUNT[@]}" \
    -e SOPS_AGE_KEY "${KEY_ENV[@]}" -e SOPS_AGE_KEY_CMD \
    -v "${PWD}:/work" -w /work \
    "$SOPS_IMAGE" "$@"
