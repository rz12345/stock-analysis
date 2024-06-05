from abc import ABC, abstractmethod
import pandas as pd
import os
import time
import requests
import json
from pathlib import Path
from datetime import date
from datetime import datetime
from datetime import timedelta
from FinMind.data import DataLoader

class BaseTradeRecord(ABC):
    def getTradeRecords(self, stock_id, start_date):
        filename = Path(self.get_filename(stock_id))
        if not os.path.exists(filename):
            df = self.fetchTradeData(stock_id, start_date)
            df.to_csv(filename, encoding='utf_8_sig', index=False)
        
        # 如果資料超過一天未更新，則更新
        elif self.is_file_older_than_1_day(filename):            
            df = pd.read_csv(filename, dtype={'stock_id': str})
            df = pd.concat([df, self.fetchTradeData(stock_id, start_date)], axis=0)
            df['date'] = pd.to_datetime(df['date'])  # 將 'date' 轉換為日期型別
            df = df.sort_values(by='date')  # 依照 'date' 欄位排序(由小至大)
            df = df.drop_duplicates(subset=['date'], keep='last')  # 根據 'date' 欄位去除重複資料，保留最新的
            df.to_csv(filename, encoding='utf_8_sig', index=False)
        
        # 載入舊資料
        else:
            df = pd.read_csv(filename, dtype={'stock_id': str})
            
        df = df.assign(date=pd.to_datetime(df['date']))
        df = df.set_index('date')
        return df    
    
    @abstractmethod
    def fetchTradeData(self, stock_id, start_date):
        pass

    @abstractmethod
    def get_filename(self, stock_id):
        pass

    @staticmethod
    def is_file_older_than_1_day(file_path):
        # 檢查檔案是否存在
        if not os.path.exists(file_path):
            print(f"檔案 {file_path} 不存在")
            return False

        # 取得檔案的最後修改時間
        file_mtime = os.path.getmtime(file_path)

        # 取得當前時間
        current_time = time.time()

        # 計算檔案最後修改時間與當前時間的差異（以秒為單位）
        time_diff = current_time - file_mtime

        # 將時間差異轉換為天數
        days_diff = time_diff / (23 * 60 * 60)

        # 檢查是否超過 1 天
        if days_diff > 1:
            return True
        else:
            return False

class TaiwanTradeRecord(BaseTradeRecord):
    def fetchTradeData(self, stock_id, start_date):
        api = DataLoader()
        df = api.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date,
        )
        
        time.sleep(2)
        
        return df

    def get_filename(self, stock_id):
        return f'data/tw/{stock_id}.csv'

class USTradeRecord(BaseTradeRecord):
    def fetchTradeData(self, stock_id, start_date):
        with open('app/configs/tiingo.json') as f:
            cred = json.load(f)
            token = cred['token']
            
        url = "https://api.tiingo.com/tiingo/daily/"+stock_id+"/prices"
        params = {
            'startDate':start_date,
            'token':token
        }
        r = requests.get(url, params=params)
        df = pd.DataFrame(r.json())
        
        # 將 'date' 欄位轉換為指定的日期格式
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        time.sleep(2)
        return df

    def get_filename(self, stock_id):
        return f'data/us/{stock_id}.csv'