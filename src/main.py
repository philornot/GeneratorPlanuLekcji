# src/main.py

from gui.app import SchedulerGUI
from src.utils.logger import GPLLogger


def main():
    logger = GPLLogger(__name__)
    logger.info("Starting school scheduler application")

    try:
        app = SchedulerGUI()
        app.mainloop()

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
