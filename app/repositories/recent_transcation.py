import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from app.services.telegram_notify import TelegramNotify

class RecentTranscation(ABC):
    # 預設的查詢天數
    DAYS = 14

    @property
    @abstractmethod
    def DB_PATH(self):
        pass

    @property
    @abstractmethod
    def CHAT_ID_KEY(self):
        """
        用於從 telegram_notify.json 中獲取對應的 chat_id 的鍵名
        """
        pass

    def getRecords(self):
        """取得近期十四天的交易資料"""
        conn = sqlite3.connect(self.DB_PATH)

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=self.DAYS)).strftime('%Y-%m-%d')

        query = """
            SELECT stock_id, date, date_closed_price, method
            FROM 'transaction_logs'
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, stock_id ASC
        """

        cur = conn.cursor()
        cur.execute(query, (start_date, end_date))
        results = cur.fetchall()
        conn.close()

        return results

    def sendNotification(self):
        """發送 Telegram 通知"""
        try:
            with open('app/configs/telegram_notify.json') as f:
                cred = json.load(f)
                bot_token = cred['bot_token']
                chat_id = cred[self.CHAT_ID_KEY]
        except Exception as e:
            print(f'讀取 Telegram 配置失敗: {e}')
            return

        results = self.getRecords()

        if len(results) > 0:
            message = '最近十四天的交易資料:\n\n'
            for row in results:
                stock_id, date, price, method = row
                message += f'股票代號: {stock_id}, 日期: {date}, 收盤價: {price}, 交易方式: {method}\n'
                print(f'股票代號: {stock_id}, 日期: {date}, 收盤價: {price}, 交易方式: {method}')

            TelegramNotify.sendMessage(bot_token, chat_id, message)
        else:
            print('近期無交易資料')

class UsRecentTranscation(RecentTranscation):
    DB_PATH = Path('data/us/db.sqlite')
    CHAT_ID_KEY = 'us_chat_id'

class TwRecentTranscation(RecentTranscation):
    DB_PATH = Path('data/tw/db.sqlite')
    CHAT_ID_KEY = 'tw_chat_id'