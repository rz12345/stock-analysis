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
    SPLIT_RATIO_THRESHOLD = 1.9
    SPLIT_DETECTION_COLUMN = 'close'

    def getTradeRecords(self, stock_id, start_date):
        filename = Path(self.get_filename(stock_id))

        if not os.path.exists(filename):
            df = self.fetchTradeData(stock_id, start_date)
            df.to_csv(filename, encoding='utf_8_sig', index=False)

        elif self.is_file_older_than_1_day(filename):
            cached_df = pd.read_csv(filename, dtype={'stock_id': str})
            cached_df = cached_df.assign(date=pd.to_datetime(cached_df['date']))

            if self._detect_split(cached_df, self.SPLIT_DETECTION_COLUMN):
                # 快取已含分割前後混合資料，重新擷取完整調整股價
                print(f'[WARNING] {stock_id}: 偵測到股票分割（快取），重新擷取調整股價')
                df = self.fetchTradeData(stock_id, start_date)
            else:
                new_df = self.fetchTradeData(stock_id, start_date)
                merged = pd.concat([cached_df, new_df], axis=0)
                merged = merged.assign(date=pd.to_datetime(merged['date']))
                merged = merged.sort_values(by='date')
                merged = merged.drop_duplicates(subset=['date'], keep='last')

                if self._detect_split(merged, self.SPLIT_DETECTION_COLUMN):
                    # 合併後才出現分割跡象，重新擷取完整調整股價
                    print(f'[WARNING] {stock_id}: 偵測到股票分割（合併後），重新擷取調整股價')
                    df = self.fetchTradeData(stock_id, start_date)
                else:
                    df = merged

            df.to_csv(filename, encoding='utf_8_sig', index=False)

        else:
            cached_df = pd.read_csv(filename, dtype={'stock_id': str})
            cached_df = cached_df.assign(date=pd.to_datetime(cached_df['date']))

            if self._detect_split(cached_df, self.SPLIT_DETECTION_COLUMN):
                # 快取污染但檔案尚未過期，仍需重新擷取
                print(f'[WARNING] {stock_id}: 偵測到股票分割（快取未過期），重新擷取調整股價')
                df = self.fetchTradeData(stock_id, start_date)
                df.to_csv(filename, encoding='utf_8_sig', index=False)
            else:
                df = cached_df

        df = df.assign(date=pd.to_datetime(df['date']))
        df = df.set_index('date')
        return df

    @staticmethod
    def _detect_split(df: pd.DataFrame, price_column: str) -> bool:
        """相鄰交易日價格比值超過閾值，視為股票分割/反分割事件"""
        sorted_price = df.sort_values('date')[price_column]
        ratios = sorted_price / sorted_price.shift(1)
        reverse_ratios = sorted_price.shift(1) / sorted_price
        max_ratio = max(ratios.max(), reverse_ratios.max())
        return max_ratio > BaseTradeRecord.SPLIT_RATIO_THRESHOLD

    @abstractmethod
    def fetchTradeData(self, stock_id, start_date):
        pass

    @abstractmethod
    def get_filename(self, stock_id):
        pass

    @staticmethod
    def is_file_older_than_1_day(file_path):
        if not os.path.exists(file_path):
            print(f"檔案 {file_path} 不存在")
            return False

        file_mtime = os.path.getmtime(file_path)
        current_time = time.time()
        time_diff = current_time - file_mtime
        days_diff = time_diff / (23 * 60 * 60)

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

        df = TaiwanTradeRecord._apply_split_adjustments(df, stock_id, start_date)
        return df

    @staticmethod
    def _apply_split_adjustments(df: pd.DataFrame, stock_id: str, start_date: str) -> pd.DataFrame:
        """
        依據 FinMind 的分割資料，對歷史股價做前複權調整。
        對每個分割事件，將該日期之前的所有 OHLC 乘以 (after_price / before_price)。
        """
        try:
            api = DataLoader()
            splits_df = api.taiwan_stock_split_price(start_date=start_date)
            time.sleep(1)
        except Exception as e:
            print(f'[WARNING] {stock_id}: 無法取得分割資料，略過調整: {e}')
            return df

        stock_splits = splits_df[splits_df['stock_id'] == stock_id].copy()
        if stock_splits.empty:
            return df

        stock_splits = stock_splits.assign(date=pd.to_datetime(stock_splits['date']))
        stock_splits = stock_splits.sort_values('date')

        price_cols = [c for c in ['open', 'max', 'min', 'close'] if c in df.columns]
        result = df.copy()
        result = result.assign(date=pd.to_datetime(result['date']))

        for _, split_row in stock_splits.iterrows():
            split_date = split_row['date']
            factor = split_row['after_price'] / split_row['before_price']
            mask = result['date'] < split_date
            result = result.assign(**{
                col: result[col].where(~mask, result[col] * factor)
                for col in price_cols
            })
            print(f'[INFO] {stock_id}: 套用分割調整 {split_date.date()} factor={factor:.4f}')

        return result

    def get_filename(self, stock_id):
        return f'data/tw/{stock_id}.csv'

class USTradeRecord(BaseTradeRecord):
    SPLIT_DETECTION_COLUMN = 'adjClose'

    def fetchTradeData(self, stock_id, start_date):
        with open('app/configs/tiingo.json') as f:
            cred = json.load(f)
            token = cred['token']

        url = "https://api.tiingo.com/tiingo/daily/" + stock_id + "/prices"
        params = {
            'startDate': start_date,
            'token': token
        }
        r = requests.get(url, params=params)
        df = pd.DataFrame(r.json())

        # 將 'date' 欄位轉換為指定的日期格式
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        time.sleep(2)
        return df

    def get_filename(self, stock_id):
        return f'data/us/{stock_id}.csv'
