# -*- coding: utf-8 -*-
"""deploy/secrets_common.py — 機密落點解析共用庫（ADR 0010 轉換批①、B-035）。

實作自 tools/secret-value-guard.py 既有已測版本原樣提出，判定邏輯零變更：移植品的
「怪寫法」（寬進窄出、空字串吵鬧失敗）是前代刻意防禦，動它之前先查由來（L-004）。

★消費者限五支（ADR 0010；批③ B-037 增 generate-secrets 與 setup-reaper-role）：
deploy/generate-secrets、deploy/setup-reaper-role、
deploy/preflight-secrets、deploy/decrypt-secrets、
tools/secret-value-guard。tools/bootstrap.sh 的落點解析刻意窄（只讀 .env）——驗證器
不與被驗證者共用底座，**永不併庫**（ADR 0010 後果欄）。

本模組零第三方 import（ADR 0010 硬約束一）、不配 CLI、不配 test 子命令；
既有測試留在 tools/secret-value-guard.py 的 test 子命令內（經 import 測本實作）。
"""
import os
import re

DEFAULT_SECRETS_DIR = os.path.join("deploy", "secrets")

# .env 行形偵測＝**寬樣式**（rev4:019 U4）：compose 的 .env 解析器接受 UTF-8 BOM／行首空白／
# export 前綴／等號兩側空白／CRLF 行尾；行首錨定 `SECRETS_DIR=` 的窄樣式對這些形一律漏認並
# 靜默回退 repo 內舊落點＝假綠（rev4:L-174）。
RE_ENV_SECRETS_DIR = re.compile(
    r"^[ \t]*(?:export[ \t]+)?SECRETS_DIR[ \t]*=[ \t]*(.*?)[ \t]*$")
# .env 值字元白名單：與 deploy 四腳本 case 樣式 `*[!A-Za-z0-9_/.-]*` 逐字同集合。
RE_ENV_VALUE_OK = re.compile(r"^[A-Za-z0-9_/.-]+$")


def resolve_secrets_dir(root, env=None):
    """機密落點三級口徑（與 deploy 四腳本同口徑；rev4:019 契約 rev4:P5.1／rev4:P5.2）。

    環境變數優先（與 compose 口徑一致）→ repo 根 `.env` 只嚴格解析 `SECRETS_DIR` 一行
    → 皆缺回退 repo 內 `deploy/secrets`。
    ★不整檔 source／不引 dotenv：compose 的 `.env` 允許不加引號的含空白值、井號語意亦與
    shell 不同。★`.env` 有該鍵但值非法＝**吵鬧失敗**（回錯誤訊息）而非靜默回退——靜默回退
    會讓消費者改讀 repo 內舊落點、明明沒在守卻回綠（假綠）。
    ★**行形偵測寬、值校驗窄**（rev4:019 U4）：偵測面必須涵蓋 compose 會讀到的每一種行形
    （BOM／縮排／export 前綴／等號兩側空白／CRLF），否則漏認即靜默回退＝同一個假綠。
    ★**空字串邊界**（rev4:019 U4）：「已匯出但為空」≠「未設」——compose 的
    `${SECRETS_DIR:-./deploy/secrets}` 對空字串直接吃預設值、回退舊落點且**不讀 `.env`**；
    把空字串當未設而續讀 `.env` 即「消費者讀新落點、compose 掛舊落點」的靜默分裂。
    空字串無合法用途（要走回退請 unset），故吵鬧失敗指名真因。
    ★`env=None`＝哨兵、不得寫成 `env or os.environ`：呼叫端明給空 dict＝「該環境確實沒設」，
    改讀本行程環境會讓「未設」與「已匯出為空」兩分支靜默改判。
    回 `(絕對路徑, None)` 或 `(None, 錯誤訊息)`。
    """
    env = os.environ if env is None else env
    val = env.get("SECRETS_DIR")
    if val == "":
        return None, ("SECRETS_DIR 已匯出為空字串——compose 會忽略 .env 並回退 repo 內 "
                      "./deploy/secrets；要用 .env 的值請先 unset SECRETS_DIR")
    if val:
        return (val if os.path.isabs(val) else os.path.join(root, val)), None
    envfile = os.path.join(root, ".env")
    if os.path.isfile(envfile):
        raw_val = None
        # utf-8-sig＝剝首行 UTF-8 BOM（compose 同口徑；Windows 側編輯器覆存常見）
        with open(envfile, encoding="utf-8-sig", errors="replace") as fh:
            for raw in fh:
                m = RE_ENV_SECRETS_DIR.match(raw.rstrip("\r\n"))
                if m:
                    raw_val = m.group(1)   # 取最後一筆（同腳本 `grep … | tail -n 1`）
        if raw_val is not None:
            if not RE_ENV_VALUE_OK.match(raw_val):
                return None, (".env 之 SECRETS_DIR 為空或含空白／shell 元字元"
                              "——拒用（產檔約束見 .env.example）")
            if not raw_val.startswith("/"):
                return None, (".env 之 SECRETS_DIR 必須為絕對路徑字面"
                              "（compose 不做 shell 展開）——見 .env.example")
            return raw_val, None
    return os.path.join(root, DEFAULT_SECRETS_DIR), None
