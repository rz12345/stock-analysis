import logging

from app.repositories.recent_transcation import TwRecentTranscation
from app.repositories.web_data_sync import TWWebData
from app.services.app_logger import get_logger

logger = get_logger("tw_notify", "tw_notify.log", "tw_chat_id")

if __name__ == "__main__":
    try:
        # Firebase realtime database 同步
        TWWebData().do_process()

        # 發送 Telegram 通知
        RecentTranscation = TwRecentTranscation()
        RecentTranscation.sendNotification()

        logger.info("tw_notify 完成")
    except Exception:
        logger.exception("tw_notify 執行失敗")
        raise SystemExit(1)
    finally:
        logging.shutdown()
