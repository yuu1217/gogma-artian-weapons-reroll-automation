import cv2
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.skill_reroller.config import COORDINATES


def verify_materials_area():
    img_path = os.path.join("data", "sample", "reset_skills.png")
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        return

    img = cv2.imread(img_path)

    for area in COORDINATES["MATERIAL_ROWS"]:
        x1, y1, x2, y2 = area
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    output_path = os.path.join("data", "output", "materials_area_verification.jpg")
    cv2.imwrite(output_path, img)
    print(f"Verified image saved to {output_path}")


if __name__ == "__main__":
    verify_materials_area()
