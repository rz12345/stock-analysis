import pandas as pd
import time
from app.repositories.base_trade_record import TaiwanTradeRecord
from app.repositories.tw_dividend_record import DividendRecord
from app.repositories.base_strategy import TwStrategy

if __name__ == "__main__":
    # 初始化
    Strategy = TwStrategy()
    
    # 清除資料表
    Strategy.clear_tables()
    
    # 初始日期
    start_date = '2020-01-01'
    
    focus_stocks = [
        # 市值型ETF:
        '0050', # 元大台灣50
        '00692', # 富邦公司治理 https://www.wantgoo.com/stock/etf/00692/constituent      
        '006208', # 富邦台灣采吉50基金
        '00733', # - 富邦臺灣中小

        # 高股息型ETF:
        '0056', # - 元大高股息
        '00878', # - 國泰永續高股息
        '00915', # - 凱基優選高股息30 https://www.wantgoo.com/stock/etf/00915/constituent
        '00713', # - 元大台灣高息低波
        '00919', # - 群益台灣精選高息
        '00929', # - 復華台灣科技優息
    ]
    for stock_id in focus_stocks:
        print(f'擷取:{stock_id}\t\t起始日:{start_date}')
        
        # 撈個資料
        TradeRecord = TaiwanTradeRecord()
        df_stock = TradeRecord.getTradeRecords(stock_id, start_date)
        df_dividend = DividendRecord.getDividendRecords(stock_id, start_date)
        
        # 合併股息和歷史交易資料
        df_stock = df_stock.merge(df_dividend, how='outer', left_index=True, right_index=True)
        df_stock = df_stock.fillna({'stock_and_cache_dividend': 0})
        df_stock = df_stock.reset_index(names='date')
        df_stock = df_stock.assign(date=pd.to_datetime(df_stock['date']))
        
        # run
        Strategy.bt_strategy(df_stock, 'bt_dividend')
        Strategy.bt_strategy(df_stock, 'bt_signals')
