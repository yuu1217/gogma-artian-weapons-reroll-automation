import os

OCR_LANG = "japan"

# 座標定義 (解像度2560x1440基準)
COORDINATES = {
    "AUTO_SELECT_BTN": (248, 1417),
    "REROLL_BTN": (460, 773),
    # スキル表示エリア
    "SKILL_AREA": (2150, 710, 2560, 800),
    "BACK_BTN": (40, 1419),
    # 素材数読み取りエリア
    "MATERIAL_ROWS": [
        (680, 340, 920, 390),
        (680, 460, 920, 510),
        (680, 580, 920, 630),
    ],
}

KEYBINDS = {
    "AUTO_SELECT": "g",
    "CONFIRM": "space",
    "CANCEL": "esc",
    "UP": "up",
    "DOWN": "down",
    "MENU": "esc",
    "TAB_LEFT": "q",
}

DELAYS = {
    # 基本操作の待機時間
    "AFTER_CLICK": 0.15,
    "REROLL_ANIMATION": 5.0,
    # タイトルに戻る操作は一度しか行われないので安全性重視で長めの遅延を設ける
    "RETURN_TO_TITLE": 0.3,
}

# ターゲットスキルの組み合わせ
TARGET_COMBINATIONS = [["闘獣の力", "甲虫の知らせ"]]

# 近似一致の閾値
MATCH_THRESHOLD = 0.65

REPORT_NAME = "report"

OUTPUT_DIR = os.path.join("data", "output", "skill_reroller")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# 最大試行回数 (0は素材数から自動計算)
MAX_ATTEMPTS = 0

WINDOW_TITLE = "Monster Hunter Wilds"

# 中断キー
STOP_KEY = "alt+q"
