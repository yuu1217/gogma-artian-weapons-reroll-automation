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

    try:
        result = ocr.ocr(img_path)
    except Exception as e:
        print(f"OCR execution failed: {e}")
        return

    output_path = PROJECT_ROOT / "ocr_debug_dump.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Type: {type(result)}\n")
            f.write(f"Raw Result: {result}\n")

            if isinstance(result, list):
                f.write(f"Length: {len(result)}\n")
                if len(result) > 0:
                    f.write(f"Item 0 Type: {type(result[0])}\n")
                    f.write(f"Item 0 Content: {result[0]}\n")
        print(f"OCR結果を {output_path} に出力しました。")
    except Exception as e:
        print(f"Failed to write dump: {e}")


if __name__ == "__main__":
    analyze_sample()
