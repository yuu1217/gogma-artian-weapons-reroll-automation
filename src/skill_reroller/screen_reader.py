import cv2
import numpy as np
import logging
from PIL import ImageGrab
from .config import COORDINATES


class ScreenReader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.skill_area = COORDINATES.get("SKILL_AREA")

        if not self.skill_area:
            self.logger.error("SKILL_AREA not found in configuration.")
            raise ValueError("Configuration error: SKILL_AREA is missing.")

    # 全画面キャプチャを取得
    def capture_screen(self) -> np.ndarray:
        try:
            screenshot = ImageGrab.grab()
            img_np = np.array(screenshot)
            # OpenCV用にBGR変換
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            return img_bgr
        except Exception as e:
            self.logger.error(f"Screen capture failed: {e}")
            raise

    # スキル表示エリアを切り出し
    def get_skill_area_image(self) -> np.ndarray:
        full_screen = self.capture_screen()
        x1, y1, x2, y2 = self.skill_area
        ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)

        h, w = full_screen.shape[:2]
        ix1 = max(0, min(ix1, w))
        ix2 = max(0, min(ix2, w))
        iy1 = max(0, min(iy1, h))
        iy2 = max(0, min(iy2, h))

        cropped = full_screen[iy1:iy2, ix1:ix2]

        if cropped.size == 0:
            self.logger.warning("Cropped image is empty. Check coordinates.")
            return np.zeros((1, 1, 3), dtype=np.uint8)

        return cropped
