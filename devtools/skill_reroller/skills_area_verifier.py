import cv2
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from src.skill_reroller.config import COORDINATES
except ImportError:
    from src.skill_reroller.config import COORDINATES

SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"


def verify_area():
    images = list(SAMPLE_DIR.glob("*.png")) + list(SAMPLE_DIR.glob("*.jpg"))
    if not images:
        print("画像が見つかりません")
        return

    img_path = str(images[0])
    img = cv2.imread(img_path)

    if img is None:
        print("画像読み込み失敗")
        return

    area = COORDINATES["SKILL_AREA"]
    x1, y1, x2, y2 = area

    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)

    auto_btn = COORDINATES["AUTO_SELECT_BTN"]
    cv2.circle(img, auto_btn, 20, (255, 0, 0), 3)

    output_path = OUTPUT_DIR / "area_verification.jpg"
    cv2.imwrite(str(output_path), img)
    print(f"検証画像を保存しました: {output_path}")


if __name__ == "__main__":
    verify_area()
