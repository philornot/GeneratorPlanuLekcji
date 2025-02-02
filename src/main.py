# src/main.py

from utils.logger import setup_logger
from gui.app import SchedulerGUI


def main():
    logger = setup_logger('school_scheduler')
    logger.info("Starting school scheduler application")

    try:
        app = SchedulerGUI()
        app.mainloop()

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
