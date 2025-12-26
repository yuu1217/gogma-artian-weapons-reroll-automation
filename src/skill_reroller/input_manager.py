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

    def _press(self, key: str, delay: float = 0.0):
        try:
            self.logger.debug(f"Pressing key: {key}")
            pydirectinput.press(key)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            self.logger.error(f"Key press failed: {e}")

    def execute_reroll_sequence(self):
        self.logger.info("Executing reroll sequence (G -> Space -> Space)...")
        self._press(KEYBINDS["AUTO_SELECT"], delay=DELAYS["AFTER_CLICK"])
        self._press(KEYBINDS["CONFIRM"], delay=DELAYS["AFTER_CLICK"])
        self._press(KEYBINDS["CONFIRM"])
        self.logger.info("Reroll sequence initiated.")

    def return_to_title(self):
        self.logger.info("Executing return to title sequence...")
        for _ in range(5):
            self._press(KEYBINDS["MENU"], delay=DELAYS["RETURN_TO_TITLE"])

        self._press(KEYBINDS["TAB_LEFT"], delay=DELAYS["RETURN_TO_TITLE"])

        for _ in range(2):
            self._press(KEYBINDS["UP"], delay=DELAYS["AFTER_CLICK"])

        self._press(KEYBINDS["CONFIRM"], delay=DELAYS["AFTER_CLICK"])
        self._press(KEYBINDS["DOWN"], delay=DELAYS["AFTER_CLICK"])

        for _ in range(2):
            self._press(KEYBINDS["CONFIRM"], delay=DELAYS["RETURN_TO_TITLE"])

        self.logger.info("Return to title sequence finished.")

    def select_no_and_confirm(self):
        self.logger.info("Actions: Select No (Up -> Space)")
        self._press(KEYBINDS["UP"])
        time.sleep(DELAYS["AFTER_CLICK"])
        self._press(KEYBINDS["CONFIRM"])

    def cancel_selection(self):
        self.logger.info("Actions: Cancel")
        self._press(KEYBINDS["CANCEL"])
