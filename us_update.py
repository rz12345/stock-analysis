import pandas as pd
import time
from app.repositories.base_trade_record import USTradeRecord
from app.repositories.base_strategy import UsStrategy

if __name__ == "__main__":
    # 初始化
    Strategy = UsStrategy()
    
    # 清除資料表
    Strategy.clear_tables()
    
    # 初始日期
    start_date = '2020-01-01'
    
    focus_stocks = [
        'VOO', 
        'QQQ', 
        'VT', 
        'VTI',
        'XLF',
        'XLP',
        'XLV',        
        'IJH',
        'IJR',
        'IWM',
        'NVDA',
    ]
    for stock_id in focus_stocks:
        print(f'擷取:{stock_id}\t\t起始日:{start_date}')
        
        # 撈個資料 (含股息)
        TradeRecord = USTradeRecord()
        df_stock = TradeRecord.getTradeRecords(stock_id, start_date)
        df_stock['stock_id'] = stock_id
        df_stock = df_stock.reset_index(names='date')
        df_stock = df_stock.assign(date=pd.to_datetime(df_stock['date']))
        
        # run        
        Strategy.bt_strategy(df_stock, 'bt_dividend')
        Strategy.bt_strategy(df_stock, 'bt_signals')
        