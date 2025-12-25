import logging
import sys
import os
from datetime import datetime
from src.skill_reroller import GameLogic, MAX_ATTEMPTS


# ログ設定
def setup_logging(timestamp: str):
    log_dir = os.path.join("data", "logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(log_dir, f"{timestamp}.txt"), encoding="utf-8"
            ),
        ],
    )


def main():
    # セッションのタイムスタンプを生成
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    setup_logging(timestamp)
    logger = logging.getLogger(__name__)

    logger.info("Starting Artian Weapon Reroll Automation Tool")

    try:
        logger.info(f"Target limit: {MAX_ATTEMPTS} attempts")
        # ゲームロジックの初期化と実行
        game = GameLogic(max_attempts=MAX_ATTEMPTS, timestamp=timestamp)
        game.run()

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)

    logger.info("Tool finished.")


if __name__ == "__main__":
    main()
