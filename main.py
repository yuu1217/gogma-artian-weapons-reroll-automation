import logging
import sys
from src.skill_reroller import GameLogic, MAX_ATTEMPTS


# ログ設定
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("reroll_log.txt", encoding="utf-8"),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Artian Weapon Reroll Automation Tool")

    try:
        logger.info(f"Target limit: {MAX_ATTEMPTS} attempts")
        # ゲームロジックの初期化と実行
        game = GameLogic(max_attempts=MAX_ATTEMPTS)
        game.run()

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)

    logger.info("Tool finished.")


if __name__ == "__main__":
    main()
