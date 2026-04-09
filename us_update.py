import json
import logging
from pathlib import Path

import pandas as pd
from app.repositories.base_strategy import UsStrategy
from app.repositories.base_trade_record import USTradeRecord
from app.services.app_logger import get_logger

logger = get_logger("us_update", "us_update.log", "us_chat_id")

if __name__ == "__main__":
    try:
        # 初始化
        Strategy = UsStrategy()

        # 清除資料表
        Strategy.clear_tables()

        # 初始日期
        start_date = '2020-01-01'

        stocks_config = json.loads(Path('stocks.json').read_text(encoding='utf-8'))
        focus_stocks = stocks_config['us']
        for stock_id in focus_stocks:
            logger.info("擷取:%s  起始日:%s", stock_id, start_date)

            # 撈個資料 (含股息)
            TradeRecord = USTradeRecord()
            df_stock = TradeRecord.getTradeRecords(stock_id, start_date)
            df_stock['stock_id'] = stock_id
            df_stock = df_stock.reset_index(names='date')
            df_stock = df_stock.assign(date=pd.to_datetime(df_stock['date']))

            # run
            Strategy.bt_strategy(df_stock, 'bt_dividend')
            Strategy.bt_strategy(df_stock, 'bt_signals')
            Strategy.bt_strategy(df_stock, 'bt_ma_pullback')
            Strategy.bt_strategy(df_stock, 'bt_monthly_dca')

        logger.info("us_update 完成")
    except Exception:
        logger.exception("us_update 執行失敗")
        raise SystemExit(1)
    finally:
        logging.shutdown()
