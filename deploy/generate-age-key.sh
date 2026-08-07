#!/usr/bin/env bash
# deploy/generate-age-key.sh — 產 age 金鑰（B′＝passphrase 加殼 identity）
#
# ＝RUNBOOK §15.2 步驟 1 的**機器化版本**：守衛與自檢內建，消除「手冊裡的可執行片段與實作
#   各寫一份而漂移」那類失效（rev4:L-199）。手冊仍保留同口徑的 inline 形作為本腳本不可用時的退路。
#
# 用法（自 repo 根跑；本腳本不讀寫 repo 內任何檔，故不強制 CWD）：
#   bash deploy/generate-age-key.sh                            # 第一把：產到預設 ~/.config/sops/age/keys.txt
#   bash deploy/generate-age-key.sh keys-fork260509-rev5.txt   # 同機第二把：同目錄**非預設**長檔名
#     （★跨代並存機的正解——該機已有前代 identity 時走這條，見 §15.2 步驟 1 註記）
#
# 何時用：①新機／新成員加入（§15.2 步驟 1）②換機重建 ③撤銷演練需第二把（§15.3 準則 5）
#   ④金鑰或 passphrase 遺失後重新加入（§15.5）。
#
# ★passphrase 只在你腦中：本腳本**不接受、不記錄、不回顯**——由 age 自己向 /dev/tty 索取。
#   遺失＝該 identity 永久失效、其加密的密文不可解（離線備份義務**含 passphrase 本身**、§15.5）。
# ★需真終端（`age -p` 走 /dev/tty）；非互動情境**吵鬧失敗且零副作用**。
# ★同機第二把務必用非預設檔名：金鑰一律落 ~/.config/sops/age。取 keys-fork260509-rev5.txt
#   這個名時 wrapper 會**自動選它**（單檔掛到容器內預設尋鑰路徑、容器內恰一把 identity），
#   解密毋須帶任何環境變數；用其他檔名（如 §15.3 撤銷演練鑰）則以 RV5_AGE_KEY_FILE 給
#   **host 端絕對路徑**覆寫（§15.2 步驟 1 註記）。
# ★檔名取 **repo 目錄名**（`keys-fork260509-rev5.txt`）而非短代號：跨代並存的機器上短代號家族
#   必撞名——此即 rev4:0084 付過代價換來的命名紀律（同源＝SECRETS_DIR 亦以 repo 目錄名為根）。
set -euo pipefail

# ---- 版本釘定（★與 RUNBOOK §12「機密工具鏈釘版」欄同步：改版須同刀改兩處；
#      docs-sync 有斷言釘住兩處相等，單邊改即紅）----
AGE_VERSION=v1.3.1
case "$(uname -s)-$(uname -m)" in                 # ★雙平台（rev5：macOS arm64 與 WSL2 x86-64 皆為工作環境）
  Linux-x86_64)  AGE_ASSET="age-$AGE_VERSION-linux-amd64.tar.gz" ;;
  Darwin-arm64)  AGE_ASSET="age-$AGE_VERSION-darwin-arm64.tar.gz" ;;
  *) echo "FAIL：未支援平台 $(uname -s)-$(uname -m)——請對照官方 release 資產名補 case 分支" >&2; exit 1 ;;
esac   # digest 走 release API 現查資產名對應欄位、隨資產名自動跟隨（勿另立靜態對照常數）

# ★暫存目錄名＝**repo 目錄名**（非 compose project name `rev5-admin`、非刀號）：同一台機器
#   並存 fork260509-rev1~rev5 五代與其他專案（work260730-rev1 等），repo 名才是零撞名的穩定
#   識別。★host 暫存／落點統一為 `~/.cache/fork260509-rev5/` 一棵樹（secrets／
#   decrypt.XXXXXX／merge.XXXXXX／keygen 四層；承 rev4:ADR 0084、rev4:B-125 先例）——
#   本腳本用 keygen 層（age 二進位快取＋公鑰捕捉 pub.txt）。★與 rev4 錯開＝兩代快取不互踩。
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/fork260509-rev5/keygen"
KEYDIR="$HOME/.config/sops/age"
KEYNAME="${1:-keys.txt}"
KEYS="$KEYDIR/$KEYNAME"

# ---- 參數自檢：檔名不得帶路徑（防穿越、也防誤把金鑰產到容器讀不到的地方）----
case "$KEYNAME" in
  */*|"")
    echo "FAIL：參數是**檔名**、不是路徑（例：keys-fork260509-rev5.txt）——金鑰一律落 $KEYDIR" >&2
    exit 1 ;;
esac

# ---- 取得 age（一次性工具、不常駐）：PATH → 本機 cache → 自官方 release 下載＋digest 驗證 ----
if command -v age >/dev/null 2>&1 && command -v age-keygen >/dev/null 2>&1; then
  AGE_BIN=$(command -v age); AGE_KEYGEN=$(command -v age-keygen)
  echo "age 來源＝PATH（$("$AGE_BIN" --version)）"
elif [ -x "$CACHE/age/age" ] && [ -x "$CACHE/age/age-keygen" ]; then
  AGE_BIN="$CACHE/age/age"; AGE_KEYGEN="$CACHE/age/age-keygen"
  echo "age 來源＝$CACHE/age（$("$AGE_BIN" --version)）"
else
  echo "age 不在 PATH 也不在 $CACHE ——自官方 release 取得 $AGE_VERSION 並驗 digest…"
  mkdir -p "$CACHE"
  ( cd "$CACHE"
    curl -sfL "https://api.github.com/repos/FiloSottile/age/releases/tags/$AGE_VERSION" -o api.json
    curl -sfLO "https://github.com/FiloSottile/age/releases/download/$AGE_VERSION/$AGE_ASSET"
    # ★age **無 checksums 檔**：完整性以 release API 的 digest 欄位**現查值**比對（勿沿用任何舊記值）
    python3 - "$AGE_ASSET" <<'PY'
import hashlib, json, sys
asset = sys.argv[1]
meta = json.load(open("api.json"))
want = next((a.get("digest", "") for a in meta["assets"] if a["name"] == asset), "")
want = want.replace("sha256:", "")
got = hashlib.sha256(open(asset, "rb").read()).hexdigest()
print(f"digest 現查＝{want[:16]}…｜實得＝{got[:16]}…｜相符＝{got == want and bool(want)}")
sys.exit(0 if (want and got == want) else 1)
PY
    tar xzf "$AGE_ASSET" )
  AGE_BIN="$CACHE/age/age"; AGE_KEYGEN="$CACHE/age/age-keygen"
  echo "age 已取得（$("$AGE_BIN" --version)）"
fi

# ---- 覆蓋前最後一道閘（★RUNBOOK §15.2：覆蓋＝永久銷毀既有私鑰、其密文即刻不可解）----
mkdir -p "$KEYDIR"
chmod 700 "$KEYDIR"
if [ -e "$KEYS" ]; then
  echo "FAIL：$KEYS 已存在——覆蓋＝永久銷毀該私鑰、版控內以它加密的密文即刻不可解；停手。" >&2
  echo "      跨代並存機（該機已有前代 identity）＝保留舊鑰、另產第二把，檔名取 repo 目錄名：" >&2
  echo "        bash deploy/generate-age-key.sh keys-fork260509-rev5.txt" >&2
  echo "      該檔名會被 wrapper 自動選用（單檔掛載），之後解密照常跑、毋須帶環境變數：" >&2
  echo "        python3 deploy/decrypt-secrets.py" >&2
  echo "      全文＝RUNBOOK §15.2 步驟 1 註記。" >&2
  exit 1
fi

echo
echo "即將產生金鑰到 $KEYS ——age 會要求輸入 passphrase 兩次（設定＋確認）。"
echo "★該 passphrase 只存在你腦中；★絕不要貼進任何對話或訊息。"
echo

# ---- 產鑰（★先寫 .new 再 mv：絕不簡寫成 `age-keygen | age -p > "$KEYS"`——shell 會在 age
#      起跑「之前」就截斷目標檔，passphrase 打錯／Ctrl-C／取不到 tty 時檔案已成 0 byte，
#      在已持鑰的機器上照打即不可逆銷毀唯一私鑰）----
PUB="$CACHE/pub.txt"
mkdir -p "$CACHE"
if ( set -o pipefail; umask 077; "$AGE_KEYGEN" 2>"$PUB" | "$AGE_BIN" -p > "$KEYS.new" ); then
  mv "$KEYS.new" "$KEYS"
  chmod 600 "$KEYS"
else
  rm -f "$KEYS.new"
  echo "FAIL：產鑰未完成（passphrase 中斷／取不到 tty）——既有檔一 byte 未動、殘檔已清" >&2
  exit 1
fi

# ---- 產物自檢（★布林形、只印 True/False 與 byte 數，絕不印內容 byte；rev4:L-193）----
python3 - "$KEYS" "$PUB" <<'PY'
import sys
keys, pub = sys.argv[1], sys.argv[2]
b = open(keys, "rb").read()
armored = b.startswith(b"age-encryption.org/v1")
# 明文私鑰前綴以**執行期串接**構造，避免本檔自身命中機密掃描規則（同 secret-value-guard 慣例）
plaintext = b.startswith(b"AGE-SECRET-" + b"KEY-")
print(f"自檢｜passphrase 加殼＝{armored}｜明文私鑰形＝{plaintext}"
      f"｜尾端無 CR＝{b[-1:] != b'\\r'}｜bytes={len(b)}")
if plaintext or not armored:
    print("FAIL：產物不是 passphrase 加殼形（應以 age-encryption.org/v1 開頭）"
          "——passphrase 那步沒生效；刪檔重做", file=sys.stderr)
    sys.exit(1)
has_pub = any(l.startswith("Public key:") for l in open(pub, encoding="utf-8"))
print(f"自檢｜公鑰行已捕捉＝{has_pub}")
sys.exit(0 if has_pub else 1)
PY

echo "權限｜檔 mode=$(stat -c '%a' "$KEYS" 2>/dev/null || stat -f '%A' "$KEYS")（應 600）｜目錄 mode=$(stat -c '%a' "$KEYDIR" 2>/dev/null || stat -f '%A' "$KEYDIR")（應 700）"
echo
echo "===== 完成。下面這一行是你的**公鑰**（非機密、可貼訊息交付管理者） ====="
cat "$PUB"
echo "======================================================================"
echo
echo "接著（§15.2 步驟 3~4）：管理者把該公鑰加進 .sops.yaml 的 age: 清單 →"
echo "  ./deploy/sops.sh updatekeys -y deploy/secrets.dev.enc.yaml → commit 密文 →"
echo "  你 git pull → bash tools/bootstrap.sh → python3 deploy/decrypt-secrets.py"
echo "★少了步驟 3，你的私鑰不在 recipient 清單裡＝拉到的密文一律解不開（§15.2 末條）。"
