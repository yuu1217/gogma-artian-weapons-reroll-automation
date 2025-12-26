import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from .config import (
    TABLE_FILE_NAME,
    OUTPUT_DIR,
    CURRENT_CONFIRMED_COUNT,
    WEAPONS,
    ELEMENTS,
)
from .utils import is_fuzzy_match


class TableManager:
    def __init__(self, output_dir: str = OUTPUT_DIR, filename: str = TABLE_FILE_NAME):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.output_dir / filename
        self.logger = logging.getLogger(__name__)
        self.data: Dict[int, Dict[str, str]] = {}
        self.headers: List[str] = ["回数"]
        self.load_table()

    def load_table(self):
        """CSVファイルからデータを読み込む"""
        if not self.filepath.exists():
            self.logger.info(
                f"Existing table not found at {self.filepath}. Starting fresh."
            )
            return

        try:
            with open(self.filepath, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                    self.headers = headers
                except StopIteration:
                    self.logger.warning("Empty CSV file found.")
                    return

                for row in reader:
                    if not row:
                        continue
                    try:
                        count = int(row[0])
                        row_data = {}
                        for i, cell in enumerate(row[1:], start=1):
                            if i < len(headers):
                                column_name = headers[i]
                                row_data[column_name] = cell
                        self.data[count] = row_data
                    except ValueError:
                        self.logger.warning(
                            f"Skipping invalid row (invalid count): {row}"
                        )
                        continue

            self.logger.info(
                f"Loaded table with {len(self.data)} rows and {len(self.headers)-1} data columns."
            )

        except Exception as e:
            self.logger.error(f"Failed to load table: {e}")

    def update_table(
        self,
        weapon: str,
        element: str,
        new_results: List[str],
        confirmed_count: int = CURRENT_CONFIRMED_COUNT,
    ):
        """
        指定された武器・属性の結果でテーブルを更新する
        confirmed_count より後のデータのみを更新・追加する
        """
        column_name = f"{weapon}_{element}"

        if column_name not in self.headers:
            self.headers.append(column_name)
            self.logger.info(f"Added new column: {column_name}")

        starting_count = confirmed_count + 1

        for i, skills in enumerate(new_results):
            current_count = starting_count + i

            if current_count not in self.data:
                self.data[current_count] = {}

            self.data[current_count][column_name] = skills

        self.save_table()

    def save_table(self):
        """内部データをCSVに保存する"""
        try:
            all_counts = sorted(self.data.keys())

            # "回数" 以外のヘッダーを武器順・属性順にソート
            data_headers = [h for h in self.headers if h != "回数"]

            def sort_key(header):
                try:
                    parts = header.split("_")
                    if len(parts) >= 2:
                        weapon = parts[0]
                        element = parts[1]
                        w_idx = WEAPONS.index(weapon) if weapon in WEAPONS else 999
                        e_idx = ELEMENTS.index(element) if element in ELEMENTS else 999
                        return (w_idx, e_idx)
                    return (999, 999)
                except Exception:
                    return (999, 999)

            data_headers.sort(key=sort_key)
            self.headers = ["回数"] + data_headers

            with open(self.filepath, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

                for count in all_counts:
                    row = [str(count)]
                    row_data = self.data[count]

                    for header in self.headers[1:]:
                        row.append(row_data.get(header, ""))

                    writer.writerow(row)

            self.logger.info(f"Table saved to {self.filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save table: {e}")

    def find_target_combinations(
        self, targets: List[List[str]], min_count: int, threshold: float
    ) -> List[Dict]:
        """
        指定されたターゲットスキルの組み合わせを検索する
        min_count (確定済み回数) より後のデータのみを対象とする
        """
        results = []

        for count, row_data in self.data.items():
            if count <= min_count:
                continue

            for weapon_element, skills_str in row_data.items():
                if not skills_str:
                    continue

                detected_skills = skills_str.split("+")

                for combination in targets:
                    # 順不同マッチング
                    all_matched = True
                    for target_skill in combination:
                        found_this_skill = False
                        for detected in detected_skills:
                            if is_fuzzy_match(target_skill, detected, threshold):
                                found_this_skill = True
                                break
                        if not found_this_skill:
                            all_matched = False
                            break

                    if all_matched:
                        results.append(
                            {
                                "count": count,
                                "weapon_element": weapon_element,
                                "matched_combo": combination,
                                "raw_skills": skills_str,
                            }
                        )
                        break

        results.sort(key=lambda x: x["count"])
        return results
