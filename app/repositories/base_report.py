from abc import ABC, abstractmethod
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
import os
import math
from PIL import Image, ImageDraw, ImageFont

class BaseReport(ABC):
    TABLE_STYLE = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    @abstractmethod
    def DB_PATH(self) -> Path:
        pass
    
    def process_data(self, conn: sqlite3.Connection, stock_id: str, method: str) -> None:
        df_transaction = pd.read_sql_query(
            f"SELECT date, date_closed_price, position_size, position_price, position_value, broker_dividend, asset_value FROM transaction_logs WHERE stock_id='{stock_id}' AND method='{method}'", conn)

        df_summary = pd.read_sql_query(
            f"SELECT date, close, position_value, broker_dividend, asset_value, roi, irr FROM bt_summaries WHERE stock_id='{stock_id}' AND method='{method}'", conn)

        chart_img_buffer = __class__.plot_strategy_graph(df_transaction, stock_id, method)

        df_transaction.columns = ['Date','Close','Position\n Size','Position\n Price','Position\n Value','Broker\n Dividend','Asset\n Value']
        df_transaction = df_transaction.applymap(__class__.format_float)
        transaction_table_img_buffer = __class__.plot_table(df_transaction)
        
        df_summary.columns = ['Date','Close','Position\n Value','Broker\n Dividend','Asset\n Value','ROI','IRR']
        df_summary['IRR'] = (df_summary['IRR'] * 100).round(2).astype(str) + '%'
        df_summary['ROI'] = (df_summary['ROI'] * 100).round(2).astype(str) + '%'
        df_summary = df_summary.applymap(__class__.format_float)
        summary_table_img_buffer = __class__.plot_table(df_summary)
        
        #__class__.generate_pdf(stock_id, method, df_transaction, df_summary, img_buffer)        
        __class__.generate_image(stock_id, method, transaction_table_img_buffer, summary_table_img_buffer, chart_img_buffer)

    def plot_strategy_graph(df: pd.DataFrame, stock_id: str, strategy: str) -> BytesIO:
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['position_value'], label='Position Value', color='gray')
        plt.plot(df['date'], df['asset_value'], label='Asset Value', color='darkred')

        last_date = df['date'].iloc[-1]
        last_pv = df['position_value'].iloc[-1]
        last_av = df['asset_value'].iloc[-1]

        va_pv = 'top' if last_av > last_pv else 'bottom'
        va_av = 'bottom' if last_av > last_pv else 'top'

        plt.text(last_date, last_pv, f"{last_pv:.2f}", fontsize=12, ha='center', va=va_pv)
        plt.text(last_date, last_av, f"{last_av:.2f}", fontsize=12, ha='center', va=va_av)

        plt.xlabel('Date', fontsize=16)
        plt.ylabel('Value', fontsize=16)
        plt.title(f'Stock ID: {stock_id}, Strategy: {strategy}', fontsize=20)
        plt.legend(fontsize=16)

        plt.setp(plt.gca().get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

        plt.grid(True)
        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        return img_buffer    
    
    def plot_table(df: pd.DataFrame) -> BytesIO:
        # 創建一個新的圖形，寬度與折線圖相同
        plt.figure(figsize=(12, 1))

        # 隱藏圖形的坐標軸
        plt.axis('off')

        # 創建表格
        data = [df.columns.tolist()] + df.values.tolist()
        table = plt.table(cellText=data, cellLoc='center', loc='center')
        #table.auto_set_column_width(col=list(range(len(df.columns))))
        table.scale(1.25, 2.5)

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        return img_buffer
    

    def set_table_style(table: Table) -> Table:
        table.setStyle(TableStyle(BaseReport.TABLE_STYLE))
        return table

    def generate_pdf(stock_id: str, method: str, df_transaction: pd.DataFrame, df_summary: pd.DataFrame, img_buffer: BytesIO) -> None:
        pdf_filename = os.path.join("output", f"{stock_id}_{method}.pdf")
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

        styles = getSampleStyleSheet()

        elements = []

        title = f"Stock ID: {stock_id}, Strategy: {method}"
        elements.append(Paragraph(title, styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))  # Add space after the title

        elements.append(Paragraph("Line Chart", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))  # Add space after the heading
        elements.append(Image(img_buffer, width=7*inch, height=3.5*inch))
        elements.append(Spacer(1, 0.2*inch))  # Add space after the image

        elements.append(Paragraph("Current Asset Value", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))  # Add space after the heading
        summary_data = [df_summary.columns.tolist()] + df_summary.values.tolist()
        summary_table = Table(summary_data, hAlign='LEFT', colWidths=[doc.width/len(df_summary.columns)]*len(df_summary.columns))
        elements.append(__class__.set_table_style(summary_table))
        elements.append(Spacer(1, 0.2*inch))  # Add space after the table

        elements.append(PageBreak())

        elements.append(Paragraph("Transaction Records", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))  # Add space after the heading
        transaction_data = [df_transaction.columns.tolist()] + df_transaction.values.tolist()
        transaction_table = Table(transaction_data, hAlign='LEFT', colWidths=[doc.width/len(df_transaction.columns)]*len(df_transaction.columns))
        elements.append(__class__.set_table_style(transaction_table))
        elements.append(Spacer(1, 0.2*inch))  # Add space after the table

        doc.build(elements)
        print(f"PDF file '{pdf_filename}' created successfully.")
              

    def generate_image(stock_id: str, method: str, transaction_table_img_buffer: BytesIO, summary_table_img_buffer: BytesIO, chart_img_buffer: BytesIO) -> None:
        img_filename = os.path.join("output", f"{stock_id}_{method}.png")

        # Line Chart
        line_chart = Image.open(chart_img_buffer)
        line_chart_width, line_chart_height = line_chart.size

        # Transaction Records
        transaction_table = Image.open(transaction_table_img_buffer)
        transaction_table_width, transaction_table_height = transaction_table.size

        # Current Asset Value
        summary_table = Image.open(summary_table_img_buffer)
        summary_table_width, summary_table_height = summary_table.size

        # Calculate total image height
        title_font_size = 24
        total_height = line_chart_height + transaction_table_height + summary_table_height + title_font_size*8

        # Create main image
        main_image = Image.new('RGB', (line_chart_width, total_height), color='white')
        draw = ImageDraw.Draw(main_image)
        
        # Add title to main image
        
        title_font = ImageFont.truetype("arial.ttf", title_font_size)
        title_width, title_height = title_font.getsize("Transaction Table")
        draw.text(((line_chart_width - title_width) // 2, line_chart_height + title_font_size), "Transaction Table", font=title_font, fill='black')
        title_width, title_height = title_font.getsize("Summary Table")
        draw.text(((line_chart_width - title_width) // 2, line_chart_height + transaction_table_height + title_font_size*4), "Summary Table", font=title_font, fill='black')

        # Paste subplots onto main image
        main_image.paste(line_chart, (0, 0))
        main_image.paste(transaction_table, (0, line_chart_height + title_font_size*3))
        main_image.paste(summary_table, (0, line_chart_height + transaction_table_height + title_font_size*6))
        
        # Save main image
        main_image.save(img_filename)
        print(f"Image file '{img_filename}' created successfully.")
        
        
    """
    將浮點數格式化為保留兩位小數
    """
    def format_float(value) -> str:
        if isinstance(value, float):
            return '{:.2f}'.format(value)
        return value

    def run(self) -> None:
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                query = 'SELECT DISTINCT stock_id, method FROM transaction_logs'
                unique_combinations = pd.read_sql_query(query, conn)

            for _, row in unique_combinations.iterrows():
                stock_id = row['stock_id']
                method = row['method']
                #if method != 'bt_dividend':
                #    continue
                with sqlite3.connect(self.DB_PATH) as conn:
                    self.process_data(conn, stock_id, method)
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            if conn:
                conn.close()

class USReport(BaseReport):
    DB_PATH = Path('data/us/db.sqlite')

class TWReport(BaseReport):
    DB_PATH = Path('data/tw/db.sqlite')