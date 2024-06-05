import sqlite3
from pathlib import Path
from abc import ABC, abstractmethod
from app.services.firebase import Firebase as DB
from datetime import datetime, timedelta
import pandas as pd

class WebDataSync(ABC):
    # 預設的查詢天數
    DAYS = 14
    PREFIX_URI = None

    @property
    def DB_PATH(self):
        if self.PREFIX_URI is None:
            raise NotImplementedError("PREFIX_URI must be defined in the subclass.")
        return Path(f'data/{self.PREFIX_URI}/db.sqlite')

    def format_float(value):
        if isinstance(value, float):
            if value < 1:
                return '{:.4f}'.format(value)
            else:
                return '{:.2f}'.format(value)
        return value

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
                    
        DB.updateNodeByDict(f'{self.PREFIX_URI}/recent_transaction_logs', df_recent.to_dict('records'))
        
        
        """
        每一個 stock_id 有不同的 metod
        查詢每一個 stoick_id 的 asset_value 較高的結果
        """
        with sqlite3.connect(self.DB_PATH) as conn:
            query = '''
                SELECT bs.stock_id,
                       bs.date,
                       bs.method,
                       bs.close,
                       bs.position_value,
                       bs.broker_dividend,
                       bs.asset_value,
                       bs.roi,
                       bs.irr
                FROM bt_summaries bs
                INNER JOIN (
                    SELECT stock_id, MAX(asset_value) AS max_asset_value
                    FROM bt_summaries
                    GROUP BY stock_id
                ) max_bs ON bs.stock_id = max_bs.stock_id AND bs.asset_value = max_bs.max_asset_value
                ORDER BY bs.stock_id
            '''
            df_best = pd.read_sql_query(query, conn)
            df_best = df_best.applymap(__class__.format_float)        
            
        # 將 query 結果轉存至 firebase realtime database
        data_best_bt_summaries = df_best.to_dict('records')
        data_best_transaction_logs = {}
        for index, row in df_best.iterrows():
            s = __class__.get_transaction_logs(self, row)
            s = s.applymap(__class__.format_float)
            stock_id = s.stock_id.values[0]
            data_best_transaction_logs[stock_id] = s.to_dict('records')
            #data_best_transaction_logs.append({stock_id:s.to_dict('records')})

        DB.updateNodeByDict(f'{self.PREFIX_URI}/best_bt_summaries',data_best_bt_summaries)
        DB.updateNodeByDict(f'{self.PREFIX_URI}/best_transaction_logs',data_best_transaction_logs)
        

class USWebData(WebDataSync):
    PREFIX_URI = 'us'

class TWWebData(WebDataSync):
    PREFIX_URI = 'tw'
    
#USWebData().do_process()
#TWWebData().do_process()