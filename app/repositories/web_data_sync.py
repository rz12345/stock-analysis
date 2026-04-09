import sqlite3
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from app.services.firebase import Firebase as DB
from datetime import datetime, timedelta
import pandas as pd
from app.utils.formatting import format_float

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF = 2  # seconds; doubles on each attempt


def _sync_with_retry(node_ref: str, data) -> None:
    """Call DB.updateNodeByDict with exponential-backoff retry."""
    delay = _RETRY_BACKOFF
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            DB.updateNodeByDict(node_ref, data)
            return
        except Exception:
            if attempt == _RETRY_ATTEMPTS:
                logger.error("Firebase 同步失敗（已重試 %d 次）：%s", _RETRY_ATTEMPTS, node_ref, exc_info=True)
                raise
            logger.warning("Firebase 同步失敗，%d 秒後重試（第 %d/%d 次）：%s", delay, attempt, _RETRY_ATTEMPTS, node_ref)
            time.sleep(delay)
            delay *= 2

class WebDataSync(ABC):
    # 預設的查詢天數
    DAYS = 30
    PREFIX_URI = None

    @property
    def DB_PATH(self):
        if self.PREFIX_URI is None:
            raise NotImplementedError("PREFIX_URI must be defined in the subclass.")
        return Path(f'data/{self.PREFIX_URI}/db.sqlite')

    def get_transaction_logs(self, row):
        stock_id = row['stock_id']
        method = row['method']

        query = f'''
            SELECT * FROM transaction_logs
            WHERE stock_id = '{stock_id}' AND method = '{method}'
            ORDER BY date
        '''

        with sqlite3.connect(self.DB_PATH) as conn:
            logs_df = pd.read_sql_query(query, conn)

        return logs_df

    def do_process(self):
        """
        查詢近期交易紀錄
        """
        with sqlite3.connect(self.DB_PATH) as conn:
            # 計算最近七天的日期範圍
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=self.DAYS)).strftime('%Y-%m-%d')

            # 查詢最近七天的交易資料
            query = f"""
                SELECT stock_id, date, date_closed_price, method
                FROM 'transaction_logs'
                WHERE date BETWEEN '{start_date}' AND '{end_date}'
            """
            df_recent = pd.read_sql_query(query, conn)
                    
        _sync_with_retry(f'{self.PREFIX_URI}/recent_transaction_logs', df_recent.to_dict('records'))
        
        # 查詢所有的 method
        with sqlite3.connect(self.DB_PATH) as conn:
            query = "SELECT DISTINCT method FROM bt_summaries"
            methods = pd.read_sql_query(query, conn)['method'].tolist()

        for method in methods:
            # 查詢每個 method 的最新資料
            with sqlite3.connect(self.DB_PATH) as conn:
                query = f'''
                    SELECT bs.*
                    FROM bt_summaries bs
                    INNER JOIN (
                        SELECT stock_id, MAX(date) AS latest_date
                        FROM bt_summaries
                        WHERE method = '{method}'
                        GROUP BY stock_id
                    ) latest ON bs.stock_id = latest.stock_id AND bs.date = latest.latest_date
                    WHERE bs.method = '{method}'
                    ORDER BY bs.stock_id
                '''
                df_method = pd.read_sql_query(query, conn)
                df_method = df_method.map(format_float)

            # 將 query 結果轉存至 firebase realtime database
            data_method_summaries = df_method.to_dict('records')
            data_method_transaction_logs = {}

            for index, row in df_method.iterrows():
                s = self.get_transaction_logs(row)
                s = s.map(format_float)
                stock_id = s.stock_id.values[0]
                data_method_transaction_logs[stock_id] = s.to_dict('records')

            _sync_with_retry(f'{self.PREFIX_URI}/{method}/summaries', data_method_summaries)
            _sync_with_retry(f'{self.PREFIX_URI}/{method}/transaction_logs', data_method_transaction_logs)

class USWebData(WebDataSync):
    PREFIX_URI = 'us'

class TWWebData(WebDataSync):
    PREFIX_URI = 'tw'