from paddleocr import PaddleOCR
import cv2
import os
import sys
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def analyze_materials():
    img_path = os.path.join("data", "sample", "reset_skills.png")
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        return

    ocr = PaddleOCR(lang="japan")

    img = cv2.imread(img_path)
    h, w, _ = img.shape

    print("Analyzing full image...")
    result = ocr.ocr(img)

    if not result:
        print("No result.")
        return

    first_res = result[0]
    if not first_res:
        print("Empty first result page.")
        return

    boxes = []
    texts = []
    scores = []

    if isinstance(first_res, dict) and "dt_polys" in first_res:
        boxes = first_res["dt_polys"]
        texts = first_res["rec_texts"]
        scores = first_res["rec_scores"]
    elif isinstance(first_res, list):
        for line in first_res:
            if len(line) >= 2:
                boxes.append(line[0])
                texts.append(line[1][0])
                scores.append(line[1][1])

    with open("materials_result_final.txt", "w", encoding="utf-8") as f:
        for i, text in enumerate(texts):
            box = boxes[i]
            score = scores[i]

            if isinstance(box, np.ndarray):
                box = box.tolist()

            cx = sum([p[0] for p in box]) / 4
            cy = sum([p[1] for p in box]) / 4

            f.write(f"Text: {text}, Center: ({cx:.1f}, {cy:.1f}), Score: {score:.2f}\n")
    print("Done. Saved to materials_result_final.txt")


if __name__ == "__main__":
    analyze_materials()
