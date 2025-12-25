import cv2
from paddleocr import PaddleOCR
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"

ocr = PaddleOCR(lang="japan")


def analyze_sample():
    images = list(SAMPLE_DIR.glob("*.png")) + list(SAMPLE_DIR.glob("*.jpg"))
    if not images:
        print("エラー: data/sample に画像が見つかりません。")
        return

    img_path = str(images[0])
    print(f"解析対象画像: {img_path}")

    img = cv2.imread(img_path)
    if img is None:
        print("画像の読み込みに失敗しました。")
        return

    h, w, _ = img.shape
    print(f"解像度: {w}x{h}")

    result = ocr.ocr(img_path)

    if not isinstance(result, list) or len(result) == 0:
        print("文字が検出されませんでした。")
        return

    first_res = result[0]

    try:
        if isinstance(first_res, dict) or hasattr(first_res, "__getitem__"):
            boxes = first_res["dt_polys"]
            texts = first_res["rec_texts"]
            scores = first_res["rec_scores"]
        elif isinstance(first_res, list):
            print(f"警告: リスト形式のレスポンスです。")
            return
        else:
            print(f"警告: 未知のデータ型 {type(first_res)} です。")
            return

        output_file = PROJECT_ROOT / "layout_result.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("--- 検出結果 ---\n")
            for i, text in enumerate(texts):
                if i >= len(boxes) or i >= len(scores):
                    break

                box = boxes[i]
                score = scores[i]

                x1 = float(box[0][0])
                y1 = float(box[0][1])
                x2 = float(box[2][0])
                y2 = float(box[2][1])

                per_x1 = x1 / w
                per_y1 = y1 / h
                per_x2 = x2 / w
                per_y2 = y2 / h

                f.write(f"Text: '{text}' ({score:.3f})\n")
                f.write(f"  Rect: ({x1:.1f}, {y1:.1f}) - ({x2:.1f}, {y2:.1f})\n")
                f.write(
                    f"  Perc: ({per_x1:.4f}, {per_y1:.4f}, {per_x2:.4f}, {per_y2:.4f})\n"
                )
                f.write("-" * 20 + "\n")

        print(f"解析完了: 結果を {output_file} に保存しました。")

    except Exception as e:
        print(f"解析エラー: {e}")


if __name__ == "__main__":
    analyze_sample()
