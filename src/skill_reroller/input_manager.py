import pydirectinput
import time
import logging
import ctypes

from .config import KEYBINDS, DELAYS, WINDOW_TITLE


pydirectinput.FAILSAFE = True


class InputManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def focus_window(self):
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)

            if hwnd:
                self.logger.info(f"Activating window: {WINDOW_TITLE} (HWND: {hwnd})")
                self._force_focus(hwnd)
            else:
                self.logger.warning(
                    f"Window '{WINDOW_TITLE}' not found. Please activate it manually."
                )

        except Exception as e:
            self.logger.error(f"Failed to activate window logic: {e}")

    def _force_focus(self, hwnd):
        """Altキーの空打ちハックを使用してWindowsのフォアグラウンドロックを回避する"""
        self.logger.info("Simulating ALT key press to bypass foreground lock...")
        pydirectinput.press("alt")
        time.sleep(0.1)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        time.sleep(1.0)

    def _press(self, key: str, delay: float = DELAYS["AFTER_CLICK"]):
        try:
            self.logger.debug(f"Pressing key: {key}")
            pydirectinput.press(key)
            time.sleep(delay)
        except Exception as e:
            self.logger.error(f"Key press failed: {e}")

    # 自動選択
    def click_auto_select(self):
        self.logger.info("Actions: Auto Select (G)")
        self._press(KEYBINDS["AUTO_SELECT"])

    # 再付与実行
    def click_reroll(self):
        self.logger.info("Actions: Reroll (Space)")
        self._press(KEYBINDS["CONFIRM"])

    # タイトルに戻るシーケンス
    def return_to_title(self):
        self.logger.info("Executing return to title sequence...")
        # メニューを開く
        for _ in range(5):
            self._press(KEYBINDS["MENU"], delay=DELAYS["RETURN_TO_TITLE"])

        # タブ切り替え
        self._press(KEYBINDS["TAB_LEFT"], delay=DELAYS["RETURN_TO_TITLE"])

        # タイトルに戻るを選択
        for _ in range(2):
            self._press(KEYBINDS["UP"])

        self._press(KEYBINDS["CONFIRM"])

        self._press(KEYBINDS["DOWN"])

        # 決定して遷移待ち
        for _ in range(2):
            self._press(KEYBINDS["CONFIRM"], delay=DELAYS["RETURN_TO_TITLE"])

        self.logger.info("Return to title sequence finished.")

    def confirm_selection(self):
        self.logger.info("Actions: Confirm (Space)")
        self._press(KEYBINDS["CONFIRM"])

    # いいえを選んで進む
    def select_no_and_confirm(self):
        self.logger.info("Actions: Select No (Up -> Space)")
        self._press(KEYBINDS["UP"])
        time.sleep(DELAYS["AFTER_CLICK"])
        self._press(KEYBINDS["CONFIRM"])

    def cancel_selection(self):
        self.logger.info("Actions: Cancel")
        self._press(KEYBINDS["CANCEL"])
