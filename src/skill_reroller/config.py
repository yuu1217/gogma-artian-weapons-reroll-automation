import tomllib
from pathlib import Path

# 設定ファイルパス
CONFIG_FILE = Path(__file__).parent / "config.toml"

# 設定を読み込み
with open(CONFIG_FILE, "rb") as f:
    _config = tomllib.load(f)

# ゲーム設定
WINDOW_TITLE = _config["game"]["window_title"]

# OCR設定
OCR_LANG = _config["ocr"]["lang"]

# 座標設定
COORDINATES = {
    "AUTO_SELECT_BTN": tuple(_config["coordinates"]["auto_select_btn"]),
    "REROLL_BTN": tuple(_config["coordinates"]["reroll_btn"]),
    "SKILL_AREA": tuple(_config["coordinates"]["skill_area"]),
    "BACK_BTN": tuple(_config["coordinates"]["back_btn"]),
    "MATERIAL_ROWS": [tuple(row) for row in _config["coordinates"]["material_rows"]],
    "WEAPON_NAME": tuple(_config["coordinates"]["weapon_name"]),
    "WEAPON_ELEMENT": tuple(_config["coordinates"]["weapon_element"]),
}

# キーバインド設定
KEYBINDS = {
    "AUTO_SELECT": _config["keybinds"]["auto_select_key"],
    "CONFIRM": _config["keybinds"]["confirm_key"],
    "CANCEL": _config["keybinds"]["cancel_key"],
    "UP": _config["keybinds"]["up_key"],
    "DOWN": _config["keybinds"]["down_key"],
    "MENU": _config["keybinds"]["menu_key"],
    "TAB_LEFT": _config["keybinds"]["tab_left_key"],
}
STOP_KEY = _config["keybinds"]["stop_key"]

# 遅延設定
DELAYS = {
    "AFTER_CLICK": _config["delays"]["after_click"],
    "REROLL_ANIMATION": _config["delays"]["reroll_animation"],
    "RETURN_TO_TITLE": _config["delays"]["return_to_title"],
}

# 出力設定
OUTPUT_DIR = _config["output"]["dir"]
REPORT_NAME = _config["output"]["report_name"]

# リロール設定
MAX_ATTEMPTS = _config["reroll"]["max_attempts"]
MATCH_THRESHOLD = _config["reroll"]["match_threshold"]
STOP_ON_MATCH = _config["reroll"]["stop_on_match"]
RETURN_TO_TITLE = _config["reroll"]["return_to_title"]
TARGET_COMBINATIONS = _config["reroll"]["target_combinations"]

# スキル一覧
SERIES_SKILLS = _config["skills"]["series"]
GROUP_SKILLS = _config["skills"]["group"]
