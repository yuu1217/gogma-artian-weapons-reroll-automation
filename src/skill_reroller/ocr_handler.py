from paddleocr import PaddleOCR
import logging
import numpy as np
from typing import List
from .config import OCR_LANG


class OCRHandler:
    def __init__(self, lang: str = OCR_LANG):
        self.logger = logging.getLogger(__name__)
        try:
            self.ocr = PaddleOCR(lang=lang)
            self.logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def extract_text(self, image: np.ndarray) -> List[str]:
        if image is None or image.size == 0:
            self.logger.warning("Empty image provided to extract_text.")
            return []

        try:
            result = self.ocr.ocr(image)
            extracted_texts = []

            if not result:
                return []

            page_result = result[0]
            if not page_result:
                return []

            # 辞書形式のレスポンス (新しいPaddleOCR)
            if isinstance(page_result, dict):
                if "rec_texts" in page_result:
                    return page_result["rec_texts"]

            # リスト形式のレスポンス
            if isinstance(page_result, list):
                for line in page_result:
                    if len(line) >= 2 and isinstance(line[1], (list, tuple)):
                        text_info = line[1]
                        if len(text_info) > 0:
                            text = text_info[0]
                            extracted_texts.append(text)

            return extracted_texts

        except Exception as e:
            self.logger.error(f"OCR execution failed: {e}")
            return []
