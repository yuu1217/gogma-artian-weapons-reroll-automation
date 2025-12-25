import cv2
import sys
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from src.skill_reroller.config import COORDINATES
except ImportError:
    # Use direct import if package import fails
    sys.path.append(str(PROJECT_ROOT / "src"))
    from skill_reroller.config import COORDINATES

SAMPLE_DIR = PROJECT_ROOT / "data" / "dev" / "sample"
OUTPUT_DIR = PROJECT_ROOT / "data" / "dev"


def verify_weapon_info_area():
    # Load sample images (prefer reset_skills.png as it was used for calibration)
    images = list(SAMPLE_DIR.glob("reset_skills.png")) + list(SAMPLE_DIR.glob("*.jpg"))
    if not images:
        print("画像が見つかりません (reset_skills.png or *.jpg in data/sample)")
        return

    img_path = str(images[0])
    img = cv2.imread(img_path)

    if img is None:
        print(f"画像読み込み失敗: {img_path}")
        return

    print(f"Verifying using image: {img_path}")

    # Verify Weapon Name Area
    if "WEAPON_NAME" in COORDINATES:
        nx1, ny1, nx2, ny2 = COORDINATES["WEAPON_NAME"]
        cv2.rectangle(img, (int(nx1), int(ny1)), (int(nx2), int(ny2)), (0, 255, 0), 3)
        cv2.putText(
            img,
            "Weapon Name",
            (int(nx1), int(ny1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )
    else:
        print("WEAPON_NAME coordinate not found in config.")

    # Verify Weapon Element Area
    if "WEAPON_ELEMENT" in COORDINATES:
        ex1, ey1, ex2, ey2 = COORDINATES["WEAPON_ELEMENT"]
        cv2.rectangle(img, (int(ex1), int(ey1)), (int(ex2), int(ey2)), (0, 255, 255), 3)
        cv2.putText(
            img,
            "Element",
            (int(ex1), int(ey1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 255),
            2,
        )
    else:
        print("WEAPON_ELEMENT coordinate not found in config.")

    # Save verification image
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "weapon_info_verification.jpg"
    cv2.imwrite(str(output_path), img)
    print(f"検証画像を保存しました: {output_path}")


if __name__ == "__main__":
    verify_weapon_info_area()
