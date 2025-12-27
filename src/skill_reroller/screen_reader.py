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

    # 指定された相対座標エリアを切り出し
    def crop_from_rect(self, image: np.ndarray, relative_rect: tuple) -> np.ndarray:
        if image is None or image.size == 0:
            return np.zeros((1, 1, 3), dtype=np.uint8)

        h, w = image.shape[:2]

        if len(relative_rect) == 4:
            rx1, ry1, rx2, ry2 = relative_rect
            ix1 = int(rx1 * w)
            iy1 = int(ry1 * h)
            ix2 = int(rx2 * w)
            iy2 = int(ry2 * h)

            # 範囲チェック
            ix1 = max(0, min(ix1, w))
            iy1 = max(0, min(iy1, h))
            ix2 = max(0, min(ix2, w))
            iy2 = max(0, min(iy2, h))

            return image[iy1:iy2, ix1:ix2]

        return np.zeros((1, 1, 3), dtype=np.uint8)

    # スキル表示エリアを切り出し
    def get_skill_area_image(self) -> np.ndarray:
        full_screen = self.capture_screen()
        cropped = self.crop_from_rect(full_screen, self.skill_area)

        if cropped.size == 0:
            self.logger.warning("Cropped image is empty. Check coordinates.")
            return np.zeros((1, 1, 3), dtype=np.uint8)

        return cropped
