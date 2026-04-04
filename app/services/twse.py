import pandas as pd

class TWSE:
    
    # 取得上市公司與ETF清單
    def getListedCompanies():
        # 台灣證券交易所上市公司
        twse_url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
        twse_df = pd.read_html(twse_url,encoding="big5-hkscs",header=1)[0]

        df = twse_df

        # 變更欄名
        df = df.rename(columns={
            '股票':'code_name',
            '股票.1':'isin_code',
            '股票.2':'start_date',
            '股票.3':'status',
            '股票.4':'category',
            '股票.5':'cfi_code',})

        # Drop 最後一欄 NaN
        df = df.iloc[:,:-1]

        # 調整欄位名稱
        cols_to_move = ['code','name']
        df[cols_to_move] = df['code_name'].str.split('　',expand=True)
        df = df[cols_to_move + [x for x in df.columns if x not in cols_to_move]]
        df = df.drop(['code_name','isin_code','status'],axis=1)
        df = df[~df.name.isna()]

        # 篩選出公司 & ETF
        df = df[df['cfi_code'].str.match('^(CEO|ESV)')]
        
        return df