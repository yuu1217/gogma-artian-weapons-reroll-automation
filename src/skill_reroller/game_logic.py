import time
import logging
import cv2
import re
import keyboard
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from .config import (
    COORDINATES,
    DELAYS,
    OUTPUT_DIR,
    TARGET_COMBINATIONS,
    MATCH_THRESHOLD,
    MAX_ATTEMPTS,
    STOP_KEY,
    REPORT_NAME,
)
from .ocr_handler import OCRHandler
from .screen_reader import ScreenReader
from .input_manager import InputManager


class GameLogic:
    def __init__(
        self,
        max_attempts: int = MAX_ATTEMPTS,
        timestamp: str = None,
        target_combination: list = None,
        stop_on_match: bool = True,
        return_to_title: bool = True,
    ):
        self.logger = logging.getLogger(__name__)
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.session_dir = Path(OUTPUT_DIR) / timestamp
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Session directory created: {self.session_dir}")

        # セッション開始時刻を保存（レポート用）
        self.session_timestamp = timestamp

        self.initial_materials = []
        self.history = []
        self.total_points_start = 0
        self.weapon_name = "Unknown"
        self.weapon_element = "Unknown"

        self.max_attempts = max_attempts
        self.current_attempt = 0
        self.stop_requested = False

        self.stop_on_match = stop_on_match
        self.return_to_title_enabled = return_to_title

        # ターゲット組み合わせの設定
        if target_combination:
            self.target_combinations = target_combination
        else:
            self.target_combinations = TARGET_COMBINATIONS

        self.ocr = OCRHandler()
        self.screen_reader = ScreenReader()
        self.input_manager = InputManager()

        self.logger.info(
            f"GameLogic initialized. Fallback max attempts: {max_attempts}, StopOnMatch: {stop_on_match}, Return: {return_to_title}"
        )

    def run(self):
        self.input_manager.focus_window()
        available_attempts = self._calculate_available_attempts()

        if self.max_attempts == 0:
            self.max_attempts = available_attempts
            self.logger.info(
                f"Mode: Auto (0). Max attempts set to {self.max_attempts} based on materials."
            )
        else:
            self.logger.info(
                f"Mode: Manual ({self.max_attempts}). Available materials for: {available_attempts} attempts."
            )
            if self.max_attempts > available_attempts:
                self.logger.warning(
                    f"Warning: Configured attempts ({self.max_attempts}) exceeds available materials ({available_attempts}). Capping to {available_attempts}."
                )
                self.max_attempts = available_attempts

        self.logger.info(
            f"Starting reroll loop. Press '{STOP_KEY}' to stop gracefully."
        )
        self.logger.info("Sequence: G -> Space -> Space -> Wait -> Up -> Space")

        try:
            for i in range(self.max_attempts):
                # 中断キーの確認
                if self._check_stop_key():
                    break

                self.current_attempt = i + 1
                self.logger.info(
                    f"--- Attempt {self.current_attempt} / {self.max_attempts} ---"
                )

                # リロール実行
                self._perform_reroll_action()

                # 演出待機中も中断キーを監視
                if self._sleep_with_check(DELAYS["REROLL_ANIMATION"]):
                    break

                # スキル検出
                skills = self._analyze_result()
                self.logger.info(f"Detected skills: {skills}")

                # ターゲット判定
                is_target = self._check_combination_target(skills)

                self.history.append(
                    {
                        "attempt": self.current_attempt,
                        "skills": skills,
                        "target": is_target,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                )

                if self.target_combinations:
                    if is_target:
                        self.logger.info("!!! TARGET COMBINATION FOUND !!!")
                        # ターゲット検出時は接頭辞なしで保存
                        self._save_screenshot(skills, prefix="")
                        self.logger.info(f"Target found: {skills}.")

                        if self.stop_on_match:
                            self.logger.info(
                                "Stop on Match enabled. Stopping at confirmation screen."
                            )
                            break
                        else:
                            self.logger.info("Stop on Match disabled. Continuing...")
                            # 次の試行へ
                            self.logger.info("Discarding result and continuing...")
                            self.input_manager.select_no_and_confirm()
                    else:
                        self.logger.info("Target not matched. Continuing...")
                        # 次の試行へ
                        self.logger.info("Discarding result and continuing...")
                        self.input_manager.select_no_and_confirm()
                else:
                    if skills:
                        self._save_screenshot(skills)
                    # 次の試行へ
                    self.logger.info("Discarding result and continuing...")
                    self.input_manager.select_no_and_confirm()

            self.logger.info("Loop finished.")

            if not self.stop_requested:
                if self.return_to_title_enabled:
                    self.logger.info(
                        "Attempts exhausted or target found. Executing return_to_title sequence."
                    )
                    self.input_manager.return_to_title()
                else:
                    self.logger.info(
                        "Return to title disabled. Staying on current screen."
                    )
            else:
                self.logger.info("Process interrupted. Skipping return_to_title.")

        except KeyboardInterrupt:
            self.logger.info("Stopped by user (Ctrl+C).")
            self.stop_requested = True
        except Exception as e:
            self.logger.error(f"An error occurred: {e}", exc_info=True)
            self.stop_requested = True
        finally:
            self._finalize()

    def _check_stop_key(self) -> bool:
        if keyboard.is_pressed(STOP_KEY):
            self.logger.info(f"Stop key '{STOP_KEY}' pressed. Stopping...")
            self.stop_requested = True
            return True
        return False

    def _sleep_with_check(self, duration: float, interval: float = 0.1) -> bool:
        end_time = time.time() + duration
        while time.time() < end_time:
            if self._check_stop_key():
                return True
            time.sleep(min(interval, end_time - time.time()))
        return False

    def _calculate_available_attempts(self) -> int:
        self.logger.info("Calculating available attempts from materials...")
        full_img = self.screen_reader.capture_screen()

        # Extract weapon info using the same screenshot
        self._extract_weapon_info(full_img)

        total_points = 0
        self.initial_materials = []

        for i, area in enumerate(COORDINATES["MATERIAL_ROWS"]):
            left, top, right, bottom = area
            cropped = full_img[top:bottom, left:right]
            texts = self.ocr.extract_text(cropped)
            self.logger.info(f"Row {i+1} texts: {texts}")

            numbers = []
            for t in texts:
                nums = re.findall(r"\d+", t)
                for n in nums:
                    numbers.append(int(n))

            if len(numbers) >= 2:
                val = numbers[0]
                count = numbers[1]
                if val not in [250, 500]:
                    self.logger.warning(f"Unexpected point value: {val}.")

                points = val * count
                total_points += points
                self.initial_materials.append(
                    {"row": i + 1, "value": val, "count": count, "subtotal": points}
                )
                self.logger.info(f"Row {i+1}: {val} pts * {count} items = {points} pts")
            else:
                self.logger.warning(
                    f"Could not detect 2 numbers in row {i+1}. Detected: {numbers}"
                )

        if total_points > 0:
            calc = total_points // 1500
            self.logger.info(
                f"Total Points: {total_points}. Calculated Max Attempts: {calc}"
            )
            self.total_points_start = total_points
            return calc
        else:
            self.logger.error("Failed to calculate points using OCR.")
            # デバッグ用画像を保存
            try:
                debug_path = self.session_dir / "debug_failed_calc.jpg"
                cv2.imwrite(str(debug_path), full_img)
                self.logger.error(
                    f"Saved debug screenshot to {debug_path} for investigation."
                )
            except Exception as e:
                self.logger.error(f"Failed to save debug screenshot: {e}")

            raise RuntimeError(
                "Could not calculate max attempts from screen. Check debug image."
            )

    def _extract_weapon_info(self, full_img):
        """Extract weapon name and element from the full screen image."""
        try:
            # Weapon Name
            nx1, ny1, nx2, ny2 = COORDINATES["WEAPON_NAME"]
            name_img = full_img[ny1:ny2, nx1:nx2]
            name_texts = self.ocr.extract_text(name_img)
            if name_texts:
                self.weapon_name = name_texts[0].strip()

            # Weapon Element
            ex1, ey1, ex2, ey2 = COORDINATES["WEAPON_ELEMENT"]
            elem_img = full_img[ey1:ey2, ex1:ex2]
            elem_texts = self.ocr.extract_text(elem_img)

            # OCRが何も検出しなかった、または空のリストの場合
            if not elem_texts:
                self.weapon_element = "無"
            else:
                raw_elem = elem_texts[0].strip()
                # 属性タイプを除去
                clean_elem = raw_elem.replace("属性タイプ", "").strip()

                # 空文字列またはスペースのみの場合
                if not clean_elem:
                    self.weapon_element = "無"
                else:
                    # 有効な属性リスト
                    valid_elements = [
                        "火",
                        "水",
                        "雷",
                        "氷",
                        "龍",
                        "麻痺",
                        "毒",
                        "爆破",
                        "無",
                    ]

                    # マッチする属性を探す
                    matched = None
                    for elem in valid_elements:
                        if elem in clean_elem:
                            matched = elem
                            break

                    if matched:
                        self.weapon_element = matched
                    else:
                        self.weapon_element = "正常に認識できませんでした"

            self.logger.info(f"Weapon Info: {self.weapon_name} ({self.weapon_element})")

        except Exception as e:
            self.logger.error(f"Failed to extract weapon info: {e}")

    def _perform_reroll_action(self):
        self.input_manager.click_auto_select()
        self.input_manager.click_reroll()
        self.input_manager.confirm_selection()

    def _analyze_result(self) -> list[str]:
        cropped_img = self.screen_reader.get_skill_area_image()
        skills = self.ocr.extract_text(cropped_img)
        valid_skills = [s.strip() for s in skills if s.strip()]
        return valid_skills

    def _check_combination_target(self, detected_skills: list[str]) -> bool:
        if not self.target_combinations:
            return False

        for combination in self.target_combinations:
            all_match_in_combo = True
            for target_skill in combination:
                found_this_skill = False
                for detected in detected_skills:
                    if self._is_fuzzy_match(target_skill, detected):
                        found_this_skill = True
                        break
                if not found_this_skill:
                    all_match_in_combo = False
                    break

            if all_match_in_combo:
                self.logger.info(f"Combination Matched: {combination}")
                return True

        return False

    def _is_fuzzy_match(self, target: str, skill: str) -> bool:
        if target in skill:
            return True

        len_t = len(target)
        len_s = len(skill)

        if len_s < len_t:
            ratio = SequenceMatcher(None, target, skill).ratio()
            return ratio >= MATCH_THRESHOLD

        for i in range(len_s - len_t + 1):
            window = skill[i : i + len_t]
            ratio = SequenceMatcher(None, target, window).ratio()
            if ratio >= MATCH_THRESHOLD:
                return True
        return False

    def _save_screenshot(self, skills: list[str], prefix: str = ""):
        safe_skills = (
            "+".join(skills).replace("/", " ").replace("\\", " ").replace(":", " ")
        )
        if len(safe_skills) > 50:
            safe_skills = safe_skills[:50] + "..."

        filename = f"{prefix}{self.current_attempt}回目 {safe_skills}.jpg"
        filepath = self.session_dir / filename

        full_img = self.screen_reader.capture_screen()

        try:
            success, encoded_img = cv2.imencode(".jpg", full_img)
            if success:
                # 日本語ファイル名対応のためバイナリ書き込み
                with open(filepath, "wb") as f:
                    f.write(encoded_img)
                self.logger.info(f"Screenshot saved: {filepath}")
            else:
                self.logger.error(f"Failed to encode image for: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")

    def _finalize(self):
        self.logger.info("Finishing process...")
        self._generate_report()

    def _generate_report(self):
        report_path = self.session_dir / f"{REPORT_NAME}.md"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"# {REPORT_NAME}\n\n")
                f.write(f"- **実行日時**: {self.session_timestamp}\n")
                f.write(f"- **武器名**: {self.weapon_name}\n")
                f.write(f"- **属性**: {self.weapon_element}\n")
                f.write(f"- **開始時ポイント合計**: {self.total_points_start}\n")
                f.write(f"- **スキル再付与を行った回数**: {self.current_attempt}\n")
                f.write(f"- **ターゲットの組み合わせ**:\n")
                if self.target_combinations:
                    for combo in self.target_combinations:
                        f.write(f"  - {combo}\n")
                else:
                    f.write("  - (なし)\n")
                f.write("\n")

                f.write("## 素材の状況\n\n")
                f.write("| 行 | 単価 | 所持数 | 小計 |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for mat in self.initial_materials:
                    f.write(
                        f"| {mat['row']} | {mat['value']} | {mat['count']} | {mat['subtotal']} |\n"
                    )
                if not self.initial_materials:
                    f.write("| - | - | - | - |\n")
                f.write("\n")

                f.write("## 厳選履歴\n\n")
                f.write("| 回数 | 時刻 | 検出スキル | ターゲット一致 |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for entry in self.history:
                    skills_str = (
                        ", ".join(entry["skills"]) if entry["skills"] else "(なし)"
                    )
                    target_mark = "**あり**" if entry["target"] else "-"
                    safe_skills = skills_str.replace("\n", " ")
                    f.write(
                        f"| {entry['attempt']} | {entry['timestamp']} | {safe_skills} | {target_mark} |\n"
                    )
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
