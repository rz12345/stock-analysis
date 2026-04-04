import pandas as pd
import matplotlib.pyplot as plt

class BacktestPlot:

    def plot_strategy_graph(df, stock_id, strategy):
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['position_value'], label='Position Value')
        plt.plot(df['date'], df['broker_dividend'], label='Broker Dividend')
        plt.plot(df['date'], df['asset_value'], label='Asset Value')

        # 在每個點標示 Y 值,並調整 Position Value 和 Asset Value 的標示位置
        for x, pv, av in zip(df['date'], df['position_value'], df['asset_value']):
            if av > pv:
                plt.text(x, pv, f'{pv:.2f}', fontsize=8, ha='center', va='top')
                plt.text(x, av, f'{av:.2f}', fontsize=8, ha='center', va='bottom')
            else:
                plt.text(x, pv, f'{pv:.2f}', fontsize=8, ha='center', va='bottom')
                plt.text(x, av, f'{av:.2f}', fontsize=8, ha='center', va='top')
        for x, y in zip(df['date'], df['broker_dividend']):
            plt.text(x, y, f'{y:.2f}', fontsize=8, ha='center', va='center')

        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title(f'Stock ID: {stock_id}, Strategy: {strategy}')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

