import logging

from app.repositories.recent_transcation import UsRecentTranscation
from app.repositories.web_data_sync import USWebData
from app.services.app_logger import get_logger

logger = get_logger("us_notify", "us_notify.log", "us_chat_id")

if __name__ == "__main__":
    try:
        # Firebase realtime database 同步
        USWebData().do_process()

        # 發送 Telegram 通知
        RecentTranscation = UsRecentTranscation()
        RecentTranscation.sendNotification()

        logger.info("us_notify 完成")
    except Exception:
        logger.exception("us_notify 執行失敗")
        raise SystemExit(1)
    finally:
        logging.shutdown()
