from app.services.twse import TWSE
import datetime
import sqlite3

class ListedCompany:
    DB_PATH = 'data/db.sqlite'
    
    # 更新上市公司清單
    def updateListedCompanies(): 
        conn = sqlite3.connect(__class__.DB_PATH)
        cur = conn.cursor()

        # 清空資料表
        cur.execute("DELETE FROM listed_companies")

        # 新增上市公司資料
        df = TWSE.getListedCompanies()
        data = list(map(tuple, df.values.tolist()))
        cur.executemany("INSERT INTO tw_listed_companies (code, name, start_date, category, cfi_code) VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()

        # 關閉連線
        conn.close()

    # 因為取得股票交易資料，需要起始時間
    # 2020/1/1 之後上市的股票，依照實際上市日期為主
    def getStockFetchStartDate(year = 2008):
        conn = sqlite3.connect(__class__.DB_PATH)
        cur = conn.cursor()

        cur = conn.cursor()
        cur.execute("SELECT code, start_date FROM tw_listed_companies")
        result = [row for row in cur.fetchall()]
        threshold_date = datetime.date(year, 1, 1)
        new_stock_data = [(code, f'{year}/01/01' if datetime.datetime.strptime(date, '%Y/%m/%d').date() < threshold_date else date)
                          for code, date in result]
        return new_stock_data