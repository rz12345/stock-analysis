import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from app.services.line_notify import LineNotify

class RecentTranscation(ABC):
    # 預設的查詢天數
    DAYS = 14
    
    @abstractmethod
    def DB_PATH(self):
        pass

    """
    取得近期七天的交易資料
    """
    def getRecords(self):
        # 建立資料庫連線
        conn = sqlite3.connect(self.DB_PATH)

        # 計算最近七天的日期範圍
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=self.DAYS)).strftime('%Y-%m-%d')

        # 查詢最近七天的交易資料
        query = f"""
            SELECT stock_id, date, date_closed_price, method
            FROM 'transaction_logs'
            WHERE date BETWEEN ? AND ?
        """

        cur = conn.cursor()
        cur.execute(query, (start_date, end_date))
        results = cur.fetchall()

        # 關閉資料庫連線
        conn.close()

        return results
    
    """
    發送 LINE Notify 訊息
    """
    def sendNotification(self):
        with open('app/configs/line_notify.json') as f:
            cred = json.load(f)
            token = cred['token']
        
        results = self.getRecords()

        # 發送 LINE 通知
        if len(results) > 0:
            # 組合 LINE 通知訊息
            message = "最近七天的交易資料:\n\n"
            for row in results:
                stock_id, date, price, method = row
                message += f"股票代號: {stock_id}, 日期: {date}, 收盤價: {price}, 交易方式: {method}\n"
                print(f"股票代號: {stock_id}, 日期: {date}, 收盤價: {price}, 交易方式: {method}\n")
                
            LineNotify.sendMessage(token, message)
        else:
            print('近期無交易資料')

class UsRecentTranscation(RecentTranscation):
    DB_PATH = Path('data/us/db.sqlite')

class TwRecentTranscation(RecentTranscation):
    DB_PATH = Path('data/tw/db.sqlite')