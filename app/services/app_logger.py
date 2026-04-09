import json
import logging
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.services.telegram_notify import TelegramNotify

LOG_DIR = Path("logs")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
TELEGRAM_CONFIG_PATH = Path("app/configs/telegram_notify.json")


@dataclass(frozen=True)
class _TelegramConfig:
    bot_token: str
    chat_id: str


def _load_telegram_config(chat_id_key: str) -> "_TelegramConfig | None":
    try:
        with open(TELEGRAM_CONFIG_PATH) as f:
            raw = json.load(f)
        return _TelegramConfig(bot_token=raw["bot_token"], chat_id=raw[chat_id_key])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return None


class TelegramHandler(logging.Handler):
    def __init__(self, config: _TelegramConfig) -> None:
        super().__init__(level=logging.ERROR)
        self._config = config

    def emit(self, record: logging.LogRecord) -> None:
        try:
            lines = [
                f"[{record.levelname}] {record.name}",
                f"Time   : {datetime.fromtimestamp(record.created).strftime(DATE_FORMAT)}",
                f"Message: {record.getMessage()}",
            ]
            if record.exc_info:
                tb = "".join(traceback.format_exception(*record.exc_info))
                lines.append(f"\nTraceback:\n{tb}")
            TelegramNotify.sendMessage(self._config.bot_token, self._config.chat_id, "\n".join(lines))
        except Exception:
            self.handleError(record)


def get_logger(name: str, log_file: str, chat_id_key: str) -> logging.Logger:
    """
    建立並回傳 logger。

    - 所有層級寫入 logs/<log_file>（RotatingFileHandler，5MB × 3 份備份）
    - INFO 以上輸出至 stdout
    - ERROR 以上傳送 Telegram（config key 不存在時降級為 WARNING 並繼續執行）

    Args:
        name:        Logger 名稱（通常為腳本名稱，如 "tw_update"）
        log_file:    Log 檔案名稱（如 "tw_update.log"），存於 logs/ 目錄
        chat_id_key: telegram_notify.json 中的 chat_id 欄位名稱
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    LOG_DIR.mkdir(exist_ok=True)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    fh = RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    tg_config = _load_telegram_config(chat_id_key)
    if tg_config is not None:
        th = TelegramHandler(tg_config)
        logger.addHandler(th)
    else:
        logger.warning("Telegram config key '%s' 不存在，錯誤通知停用", chat_id_key)

    return logger
