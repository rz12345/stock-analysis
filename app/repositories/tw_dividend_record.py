from FinMind.data import DataLoader
from pathlib import Path
import pandas as pd
import os
import time

class DividendRecord:
    # 取得配息資料
    # 如果本地 csv 檔案未超過效期，讀取舊檔
    # 如果檔案不存在，或是超過效期，擷取新資料
    def getDividendRecords(stock_id, start_date):
        filename = Path(f'data/tw/{stock_id}-dividend.csv')
        if not os.path.exists(filename):
            df = __class__.fetchDividendRecords(stock_id,start_date)
            if isinstance(df, pd.DataFrame) & (df.shape[0] > 0):
                df.to_csv(filename, encoding='utf_8_sig', index=False)
            else:
                df = pd.DataFrame(columns=['date', 'stock_and_cache_dividend', 'stock_or_cache_dividend'])
            
        # 如果資料超過七天未更新，則更新
        elif __class__.is_file_older_than_7_days(filename):  
            df = __class__.fetchDividendRecords(stock_id,start_date)
            if isinstance(df, pd.DataFrame):
                df.to_csv(filename, encoding='utf_8_sig', index=False)
            
        # 載入舊資料
        else:
            df = pd.read_csv(filename)
            
        df = df[['date', 'stock_and_cache_dividend', 'stock_or_cache_dividend']]
        df = df.assign(date=pd.to_datetime(df['date']))
        df = df.set_index('date')
        return df


    # 擷取新的配息資料
    def fetchDividendRecords(stock_id, start_date):
        # FinMind api 初始化
        api = DataLoader()

        try:
            df = api.taiwan_stock_dividend_result(
                stock_id=stock_id,
                start_date=start_date,
            )

        except Exception as e:
            print(f"Error fetching data for stock {stock_id}: {e}")

        # 配息的 dataframe
        time.sleep(2)
        return df

    # 輔助函式
    def is_file_older_than_7_days(file_path):
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
        days_diff = time_diff / (24 * 60 * 60)

        # 檢查是否超過 7 天
        if days_diff > 7:
            #print(f"檔案 {file_path} 的更新時間超過 7 天")
            return True
        else:
            #print(f"檔案 {file_path} 的更新時間未超過 7 天")
            return False