import time
import logging
import cv2
import os
import re
import keyboard
from datetime import datetime
from difflib import SequenceMatcher
from .config import (
    COORDINATES,
    DELAYS,
    OUTPUT_DIR,
    TARGET_COMBINATIONS,
    MATCH_THRESHOLD,
    MATCH_THRESHOLD,
    MAX_ATTEMPTS,
    STOP_KEY,
    REPORT_NAME,
)
from .ocr_handler import OCRHandler
from .screen_reader import ScreenReader
from .input_manager import InputManager


class GameLogic:
    def __init__(self, max_attempts: int = MAX_ATTEMPTS, timestamp: str = None):
        self.logger = logging.getLogger(__name__)
        # タイムスタンプが指定されていない場合は新規生成
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.session_dir = os.path.join(OUTPUT_DIR, timestamp)
        os.makedirs(self.session_dir, exist_ok=True)
        self.logger.info(f"Session directory created: {self.session_dir}")

        self.initial_materials = []
        self.history = []
        self.total_points_start = 0

        self.max_attempts = max_attempts
        self.current_attempt = 0
        self.stop_requested = False

        self.ocr = OCRHandler()
        self.screen_reader = ScreenReader()
        self.input_manager = InputManager()

        self.logger.info(
            f"GameLogic initialized. Fallback max attempts: {max_attempts}"
        )

    def run(self):
        self.input_manager.focus_window()
        # 素材数から実行可能回数を計算
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
                    f"Warning: Configured attempts ({self.max_attempts}) exceeds available materials ({available_attempts})."
                )

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

                if TARGET_COMBINATIONS:
                    if is_target:
                        self.logger.info("!!! TARGET COMBINATION FOUND !!!")
                        # ターゲット検出時は接頭辞なしで保存
                        self._save_screenshot(skills, prefix="")
                        self.logger.info(f"Target found: {skills}. Continuing...")
                    else:
                        self.logger.info("Target not matched. Continuing...")
                else:
                    if skills:
                        self._save_screenshot(skills)

                # 次の試行へ (いいえを選択)
                self.logger.info("Discarding result and continuing...")
                self.input_manager.select_no_and_confirm()

            self.logger.info("Loop finished.")

            if not self.stop_requested:
                self.logger.info(
                    "Attempts exhausted. execution return_to_title sequence."
                )
                self.input_manager.return_to_title()
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
            self.logger.error("Failed to calculate points.")
            raise RuntimeError("Could not calculate max attempts from screen.")

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
        if not TARGET_COMBINATIONS:
            return False

        for combination in TARGET_COMBINATIONS:
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

    # 結果のスクリーンショットを保存
    def _save_screenshot(self, skills: list[str], prefix: str = ""):
        safe_skills = (
            "+".join(skills).replace("/", " ").replace("\\", " ").replace(":", " ")
        )
        if len(safe_skills) > 50:
            safe_skills = safe_skills[:50] + "..."

        filename = f"{prefix}{self.current_attempt}回目 {safe_skills}.jpg"
        filepath = os.path.join(self.session_dir, filename)

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
        report_path = os.path.join(self.session_dir, f"{REPORT_NAME}.md")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"# {REPORT_NAME}\n\n")
                f.write(
                    f"- **実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"- **開始時ポイント合計**: {self.total_points_start}\n")
                f.write(f"- **最大試行回数**: {self.max_attempts}\n")
                f.write(f"- **中断キー**: {STOP_KEY}\n")
                f.write(f"- **ターゲットの組み合わせ**:\n")
                if TARGET_COMBINATIONS:
                    for combo in TARGET_COMBINATIONS:
                        f.write(f"  - {combo}\n")
                else:
                    f.write("  - (なし)\n")
                f.write("\n")

                f.write("## 開始時の素材状況\n\n")
                f.write("| 行 | 単価 | 所持数 | 小計 |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for mat in self.initial_materials:
                    f.write(
                        f"| {mat['row']} | {mat['value']} | {mat['count']} | {mat['subtotal']} |\n"
                    )
                if not self.initial_materials:
                    f.write("| - | - | - | - |\n")
                f.write("\n")

                f.write("## リロール履歴\n\n")
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
