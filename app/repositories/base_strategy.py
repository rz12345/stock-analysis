from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import date
import pandas as pd
import math
import sqlite3
import time
import sys

class BaseStrategy(ABC):
    TRANSACTION_LOGS_TABLE = 'transaction_logs' 
    BT_SUMMARIES_TABLE = 'bt_summaries'
    
    # 持股量
    POSITION_SIZE = 0
    
    # 持股成本
    POSITION_VALUE = 0
    
    # 持股單價
    POSITION_PRICE = 0
    
    # 配息
    BROKER_DIVIDEND = 0
    
    # 起始年
    START_YEAR = 2000
    
    @abstractmethod
    def DB_PATH(self):
        pass
    
    @abstractmethod
    def BROKER_YEAR_CASH(self):
        pass
    
    @abstractmethod
    def DIVIDEND_COLUMN(self):
        pass
    
    @abstractmethod
    def CLOSED_PRICE_COLUMN(self):
        pass
    
    """
    計算年化報酬率
    
    :param initial_value: 初始值
    :param final_value: 最終值
    :param num_years: 年數
    :return: 年化報酬率
    """
    @staticmethod
    def calculate_annualized_return(initial_value: float, final_value: float, num_years: float) -> float:
        if initial_value == 0:
            raise ValueError("Initial value cannot be zero")
        total_return = final_value / initial_value
        annualized_return = math.pow(total_return, 1 / num_years) - 1
        return annualized_return

    """
    交易策略
    bt_dividend(每次配息後買入)
    bt_signals(MACD負轉正，且RSI低於50)
    
    :param stock_data: 股票數據
    :param method_name: 策略名稱
    :return: 回測結果字典
    """
    def bt_strategy(self, stock_data: pd.DataFrame, method_name: str) -> Dict[str, float]:
        if stock_data.empty:
            raise ValueError("Stock data is empty")

        # 初始化參數
        position_size = self.POSITION_SIZE
        position_value = self.POSITION_VALUE
        position_price = self.POSITION_PRICE
        broker_dividend = self.BROKER_DIVIDEND
        year_avl_cash = self.BROKER_YEAR_CASH
        current_year = self.START_YEAR

        # 執行回測日期
        bt_date = date.today().strftime('%Y-%m-%d')

        # 定義買入訊號 `buy_signal`
        if method_name == 'bt_dividend':
            stock_data['buy_signal'] = (stock_data[self.DIVIDEND_COLUMN] != 0).astype(int)
        elif method_name == 'bt_signals':
            stock_data = self.calculate_macd_and_rsi(stock_data)
            stock_data['buy_signal'] = stock_data['MACD_signal'] & stock_data['RSI_signal']

        if stock_data[stock_data['buy_signal'] == 1]['buy_signal'].count() == 0: 
            return None

        data = []
        total_investment = 0
        last_div_date = None
        for _, row in stock_data.iterrows():
            
            # 檢查當前年份是否與數據中的年份不同。如果不同,則更新 `current_year` 變數。
            if int(current_year) != int(row['date'].year):
                current_year = row['date'].year

            # 接下來,它檢查當前數據行的買入信號 `buy_signal` 是否為1,表示需要進行買入操作。
            if row['buy_signal'] == 1:
                # 如果需要買入,並且目前持有股票(即 `position_size` 大於0),則檢查上次買入後是否有配息:
                if position_size > 0:
                    # 如果 `last_div_date` 為 None,則找當前日期之前所有的配息數據。
                    if last_div_date == None:
                        div_data = stock_data.loc[(stock_data[self.DIVIDEND_COLUMN] > 0) & (stock_data['date'] < row['date']), 
                                                  ['date',self.DIVIDEND_COLUMN]]
                    # 如果 `last_div_date` 不為 None,則找上次配息日期和當前日期之間的配息數據。
                    else:
                        div_data = stock_data.loc[(stock_data[self.DIVIDEND_COLUMN] > 0) & (stock_data['date'] < row['date']) & (stock_data['date'] > last_div_date), 
                                                  ['date',self.DIVIDEND_COLUMN]]

                    # 如果找到配息數據,則根據持股量計算配息金額,並更新 `broker_dividend` 和 `last_div_date`。    
                    if not div_data.empty:
                        broker_dividend += round(position_size * div_data[self.DIVIDEND_COLUMN].values[-1], 2)
                        last_div_date = div_data['date'].values[-1]  # 更新上次配息日期

                # 定期定額：依照 per_trade_cash 每次交易金額  與 close 收盤價
                # 計算當前年份的買入次數 `buy_times` ,並計算每次交易的金額 `per_trade_cash` 和股數 `per_trade_amount`
                buy_times = stock_data.loc[(stock_data['date'].dt.year == current_year) & (stock_data['buy_signal'] == 1)].shape[0]
                per_trade_cash = year_avl_cash / buy_times
                per_trade_amount = round(per_trade_cash / row[self.CLOSED_PRICE_COLUMN], 0)

                # 更新持股單價 `position_price`, 公式: (持股價 * 持股量 + 收盤價 * 本次交易量) / (持股量 + 本次交易量)。
                # 如果分母為0,則將持股單價設為0。
                denominator = position_size + per_trade_amount
                if denominator != 0:
                    position_price = round((position_price * position_size + row[self.CLOSED_PRICE_COLUMN] * per_trade_amount) / denominator, 2)
                else:
                    position_price = 0

                # 更新持股量 `position_size` 和持股成本 `position_value`。
                position_size = position_size + per_trade_amount
                position_value = round(position_price * position_size, 2)

                # 計算當日的資產價值 `asset_value`,包括股票市值和配息金額。
                date_closed_price = round(row[self.CLOSED_PRICE_COLUMN], 2)
                asset_value = round(position_size * date_closed_price + broker_dividend, 2)

                # 將當前交易的數據添加到 `data` 列表中,包括股票代碼、日期、策略名稱、持股量、持股單價、持股成本、當日收盤價、配息額和資產價值。
                row_data = [row['stock_id'],
                            row['date'].strftime('%Y-%m-%d'),
                            method_name,  # 函式名稱
                            position_size,  # 持股量 
                            position_price,  # 持股單價
                            position_value,  # 持股成本值              
                            date_closed_price,  # 當日收盤價
                            broker_dividend,  # 配息額
                            asset_value,  # 資產價值(收盤價)
                            ]
                data.append(row_data)

                # 將每次交易的金額累加到總投資金額 `total_investment`中。
                total_investment += per_trade_cash
            # 如果當前數據行的買入信號為0,則將本次交易量(`per_trade_amount`)設為0。
            else:
                per_trade_amount = 0


        # 更新交易資料
        self.update_transaction_logs(data)

        # 資產價值：持股量*最後一天收盤價 + 配息
        last_closed_price = stock_data[self.CLOSED_PRICE_COLUMN].values[-1]
        asset_value, roi = self.calculate_asset_value_and_ratio(position_size, last_closed_price, broker_dividend, total_investment)

        # 計算 irr
        first_date = stock_data[stock_data['buy_signal'] == 1].iloc[0]['date']
        last_date = stock_data.iloc[-1]['date']
        years = (last_date - first_date).days / 365

        if years > 0:
            irr = round(__class__.calculate_annualized_return(total_investment, asset_value, years), 4)

            # 更新交易策略 summary 資料
            summary = [
                stock_data['stock_id'].iloc[0],
                bt_date,  # 回測日期
                method_name,  # 函式名稱
                last_closed_price, # 最後一天收盤價
                position_value,  # 持股成本
                broker_dividend,  # 總配息
                asset_value,  # 資產價值
                roi,  # 投報率
                irr,  # 年化報酬率
            ]
            self.update_bt_summary(summary)

    """
    計算資產淨值 asset_value，與投資報酬率 roi
    
    :param position_size: 持股量
    :param last_closed_price: 最後一天收盤價
    :param broker_dividend: 總配息
    :param total_investment: 總投資金額
    :return: 資產淨值和投資報酬率
    """
    def calculate_asset_value_and_ratio(self, position_size: float, last_closed_price: float, broker_dividend: float, total_investment: float) -> Tuple[float, float]:
        asset_value = round(position_size * last_closed_price + broker_dividend, 2)
        if total_investment != 0:
            roi = round(((asset_value - total_investment) / total_investment), 4)
        else:
            roi = 0
        return asset_value, roi
    
    """
    計算歷史股價資料的 MACD 與 RSI
    
    :param stock_data: 股票數據
    :return: 包含 MACD 和 RSI 的股票數據
    """
    def calculate_macd_and_rsi(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        stock_data['MACD'] = stock_data[self.CLOSED_PRICE_COLUMN].ewm(span=12, adjust=False).mean() - stock_data[self.CLOSED_PRICE_COLUMN].ewm(span=26, adjust=False).mean()
        stock_data['Signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
        stock_data['MACD_diff'] = stock_data['MACD'] - stock_data['Signal']
        stock_data['MACD_diff_prev'] = stock_data['MACD_diff'].shift(1)
        stock_data['MACD_signal'] = (stock_data['MACD_diff'] > 0) & (stock_data['MACD_diff_prev'] <= 0)
        delta = stock_data[self.CLOSED_PRICE_COLUMN].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        stock_data['RSI'] = 100 - (100 / (1 + rs))
        stock_data['RSI_signal'] = stock_data['RSI'] <= 50
        return stock_data
    
    """
    紀錄回測的交易紀錄
    
    :param data: 交易紀錄數據
    """
    def update_transaction_logs(self, data: List[Tuple]) -> None:
        with sqlite3.connect(self.DB_PATH) as conn:
            try:
                cur = conn.cursor()
                cur.executemany(f"INSERT INTO {self.TRANSACTION_LOGS_TABLE} \
                    (stock_id, date, method, position_size, position_price, position_value, date_closed_price, broker_dividend, asset_value) \
                    VALUES \
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error inserting transaction logs: {e}")

    """
    紀錄回測 summary
    
    :param data: 回測摘要數據
    """
    def update_bt_summary(self, data: List[Tuple]) -> None:
        with sqlite3.connect(self.DB_PATH) as conn:
            try:
                cur = conn.cursor()            
                cur.execute(f"INSERT INTO {self.BT_SUMMARIES_TABLE} \
                    (stock_id, date, method, close, position_value, broker_dividend, asset_value, roi, irr) \
                    VALUES \
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error inserting backtest summary: {e}")

    """
    清除資料表
    """
    def clear_tables(self) -> None:
        with sqlite3.connect(self.DB_PATH) as conn:
            try:
                cur = conn.cursor()
                cur.execute("BEGIN TRANSACTION")
                cur.execute(f"DELETE FROM {self.BT_SUMMARIES_TABLE}")
                cur.execute(f"DELETE FROM {self.TRANSACTION_LOGS_TABLE}")
                cur.execute("COMMIT")
            except sqlite3.Error as e:
                print(f"Error clearing tables: {e}")
                conn.rollback()

class TwStrategy(BaseStrategy):
    DB_PATH = Path('data/tw/db.sqlite')
    BROKER_YEAR_CASH = 100000
    DIVIDEND_COLUMN = 'stock_and_cache_dividend'
    CLOSED_PRICE_COLUMN = 'close'

class UsStrategy(BaseStrategy):
    DB_PATH = Path('data/us/db.sqlite')  
    BROKER_YEAR_CASH = 3500
    DIVIDEND_COLUMN = 'divCash'
    CLOSED_PRICE_COLUMN = 'adjClose'