import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from app.repositories.base_report import USReport, TWReport

def format_float(value):
    if isinstance(value, float):
        return '{:.2f}'.format(value)
    return value

def generate_summary_table(df, output_file):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis('off')

    table_data = [df.columns.tolist()] + df.values.tolist()

    table = ax.table(cellText=table_data, cellLoc='right', loc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(16)
    table.scale(1, 4)

    for col in range(len(df.columns)):
        table[0, col].set_text_props(ha='center')

    for row in range(1, len(table_data)):
        table[row, 0].set_text_props(ha='left')

    cell_colors = [['lightgray'] * len(df.columns)] + [['white'] * len(df.columns)] * (len(table_data) - 1)
    for i in range(len(table_data)):
        for j in range(len(df.columns)):
            table[i, j].set_facecolor(cell_colors[i][j])

    for i in range(len(df.columns)):
        table.auto_set_column_width(i)

    plt.savefig(output_file, bbox_inches='tight', dpi=72)
    print(f"Image file '{output_file}' created successfully.")

def generate_summary_tables(reports, methods, output_files):
    for Report, output_file_pair in zip(reports, output_files):
        for method, output_file in zip(methods, output_file_pair):
            with sqlite3.connect(Report.DB_PATH) as conn:
                query = f"SELECT stock_id, date, close, position_value, broker_dividend, asset_value, roi, irr FROM bt_summaries WHERE method = '{method}' ORDER BY roi DESC"
                df = pd.read_sql_query(query, conn)
                df.columns = ['Stock ID','Date','Close','Position\n Value','Broker\n Dividend','Asset\n Value','ROI','IRR']

            df['IRR'] = (df['IRR'] * 100).round(2).astype(str) + '%'
            df['ROI'] = (df['ROI'] * 100).round(2).astype(str) + '%'
            df = df.applymap(format_float)

            generate_summary_table(df, output_file)

if __name__ == "__main__":
    TWReport = TWReport()
    USReport = USReport()
    
    # 生成個股圖表：資產變化折線圖、Transcation Table、Summary Table
    USReport.run()
    TWReport.run()
    
    reports = [USReport, TWReport]
    methods = ['bt_dividend', 'bt_signals']
    output_files = [
        ['output/US_Summary_Dividend.png', 'output/US_Summary_Signals.png'],
        ['output/TW_Summary_Dividend.png', 'output/TW_Summary_Signals.png']
    ]

    # 生成台股、美股彙總表
    generate_summary_tables(reports, methods, output_files)