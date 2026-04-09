"""
Unit tests for BaseStrategy calculation methods:
- calculate_monthly_dca()
- calculate_ma_pullback()
- calculate_macd_and_rsi()
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from app.repositories.base_strategy import TwStrategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STRATEGY = TwStrategy()
CLOSE_COL = TwStrategy.CLOSED_PRICE_COLUMN       # 'close'
DIVIDEND_COL = TwStrategy.DIVIDEND_COLUMN         # 'stock_and_cache_dividend'


def _make_df(dates, closes, dividends=None, stock_id="0050"):
    """Build a minimal TwStrategy-compatible DataFrame."""
    if dividends is None:
        dividends = [0.0] * len(dates)
    return pd.DataFrame({
        "stock_id": stock_id,
        "date": pd.to_datetime(dates),
        CLOSE_COL: [float(c) for c in closes],
        DIVIDEND_COL: [float(d) for d in dividends],
    })


def _trading_days(start: str, n: int) -> list:
    """Return n weekday dates starting from start."""
    result = []
    d = pd.Timestamp(start)
    while len(result) < n:
        if d.weekday() < 5:   # Mon–Fri
            result.append(d)
        d += pd.Timedelta(days=1)
    return result


# ===========================================================================
# calculate_monthly_dca
# ===========================================================================

class TestCalculateMonthlyDca:
    def test_first_trading_day_of_each_month_gets_signal(self):
        """The first trading day of each month must have signal=True."""
        # Build 3 months of daily data (Jan–Mar 2024)
        dates = _trading_days("2024-01-01", 63)  # ~3 months
        closes = [100.0] * len(dates)
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_monthly_dca(df)

        # Group by month; signal must be True only on the minimum date per month
        for period, group in result.groupby(result["date"].dt.to_period("M")):
            first_day = group["date"].min()
            for _, row in group.iterrows():
                expected = row["date"] == first_day
                assert bool(row["monthly_dca_signal"]) == expected, (
                    f"period={period}, date={row['date'].date()}: "
                    f"expected signal={expected}, got {row['monthly_dca_signal']}"
                )

    def test_non_first_days_have_no_signal(self):
        """Days that are not the first trading day of their month must be False."""
        # Use exactly 21 trading days (all within March 2024) to stay in one month
        dates = _trading_days("2024-03-01", 21)
        closes = [50.0] * len(dates)
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_monthly_dca(df)
        first_day = result["date"].min()
        non_first = result[result["date"] != first_day]

        assert non_first["monthly_dca_signal"].sum() == 0

    def test_single_row_is_first_day(self):
        """A single-row DataFrame is trivially its own first trading day."""
        df = _make_df(["2024-06-03"], [200.0])
        result = STRATEGY.calculate_monthly_dca(df)

        assert result["monthly_dca_signal"].iloc[0] is True or \
               result["monthly_dca_signal"].iloc[0] == True  # noqa: E712

    def test_exactly_one_signal_per_month(self):
        """Each month should produce exactly one buy signal."""
        dates = _trading_days("2024-01-01", 63)
        closes = [100.0] * len(dates)
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_monthly_dca(df)
        signals_per_month = result[result["monthly_dca_signal"]].groupby(
            result.loc[result["monthly_dca_signal"], "date"].dt.to_period("M")
        ).size()

        assert (signals_per_month == 1).all(), "Each month must have exactly one signal"

    def test_original_df_not_mutated(self):
        """The function must return a new object and leave the input untouched."""
        dates = _trading_days("2024-01-01", 10)
        closes = [100.0] * len(dates)
        df = _make_df(dates, closes)
        cols_before = set(df.columns)

        STRATEGY.calculate_monthly_dca(df)

        assert set(df.columns) == cols_before, "Input DataFrame was mutated"


# ===========================================================================
# calculate_ma_pullback
# ===========================================================================

class TestCalculateMaPullback:
    def test_insufficient_data_produces_no_signal(self):
        """Fewer than window rows → MA is all NaN → no signals."""
        dates = _trading_days("2024-01-01", 50)  # well below 120
        closes = [100.0] * len(dates)
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_ma_pullback(df, window=120)

        assert result["MA_pullback_signal"].sum() == 0

    def test_price_always_above_ma_produces_no_signal(self):
        """If price never dips below MA there is no crossing-back signal."""
        dates = _trading_days("2020-01-01", 150)
        closes = [100.0] * len(dates)  # flat → price == MA always
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_ma_pullback(df, window=120)

        assert result["MA_pullback_signal"].sum() == 0

    def test_pullback_crossing_generates_signal_on_correct_day(self):
        """
        After 130 days at 100, drop to 50 on day 131, then rise to 150 on day 132.
        Day 131: price(50) < MA(~100) → below_ma True
        Day 132: price(150) >= MA(~100) & prev_below_ma True → signal
        """
        dates = _trading_days("2020-01-01", 132)
        closes = [100.0] * 130 + [50.0, 150.0]
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_ma_pullback(df, window=120)

        signal_rows = result[result["MA_pullback_signal"]]
        assert len(signal_rows) == 1
        assert signal_rows.iloc[0]["date"] == dates[131]

    def test_multiple_crossings_each_generate_signal(self):
        """Two distinct pullback-crossings should each produce one signal."""
        # 130 flat days → drop → cross → flat → drop again → cross
        base = [100.0] * 130
        bounce1 = [50.0, 150.0]       # crossing 1
        flat = [150.0] * 10
        bounce2 = [80.0, 160.0]       # crossing 2 (relative to new MA)
        closes = base + bounce1 + flat + bounce2
        dates = _trading_days("2020-01-01", len(closes))
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_ma_pullback(df, window=120)

        assert result["MA_pullback_signal"].sum() >= 2

    def test_custom_window_respected(self):
        """With window=5, signals can appear much earlier than with window=120."""
        dates = _trading_days("2024-01-01", 20)
        # 8 days at 100, day 9 drops to 50, day 10 rises to 150
        closes = [100.0] * 8 + [50.0, 150.0] + [150.0] * 10
        df = _make_df(dates, closes)

        result = STRATEGY.calculate_ma_pullback(df, window=5)

        # With window=5 the MA becomes valid from row index 4 onward
        assert result["MA_pullback_signal"].sum() >= 1

    def test_original_df_not_mutated(self):
        """The function must not modify the input DataFrame in-place."""
        dates = _trading_days("2020-01-01", 10)
        closes = [100.0] * 10
        df = _make_df(dates, closes)
        cols_before = set(df.columns)

        STRATEGY.calculate_ma_pullback(df, window=5)

        assert set(df.columns) == cols_before


# ===========================================================================
# calculate_macd_and_rsi
# ===========================================================================

class TestCalculateMacdAndRsi:
    def _make_long_df(self, n=100, prices=None):
        dates = _trading_days("2020-01-01", n)
        if prices is None:
            # Slightly trending series with noise to make RSI & MACD meaningful
            prices = [100.0 + i * 0.1 + (i % 7) * 0.5 for i in range(n)]
        return _make_df(dates, prices)

    def test_required_columns_added(self):
        """All expected columns must be present in the result."""
        df = self._make_long_df()
        result = STRATEGY.calculate_macd_and_rsi(df)
        for col in ("MACD", "Signal", "MACD_diff", "MACD_diff_prev",
                    "MACD_signal", "RSI", "RSI_signal"):
            assert col in result.columns, f"Missing column: {col}"

    def test_rsi_bounded_between_0_and_100(self):
        """RSI values (excluding initial NaN rows) must be in [0, 100]."""
        df = self._make_long_df(n=60)
        result = STRATEGY.calculate_macd_and_rsi(df)
        valid_rsi = result["RSI"].dropna()

        assert (valid_rsi >= 0).all(), "RSI below 0 found"
        assert (valid_rsi <= 100).all(), "RSI above 100 found"

    def test_rsi_signal_true_when_rsi_le_50(self):
        """RSI_signal must be True exactly where RSI <= 50."""
        df = self._make_long_df()
        result = STRATEGY.calculate_macd_and_rsi(df)
        valid = result.dropna(subset=["RSI"])

        expected = valid["RSI"] <= 50
        pd.testing.assert_series_equal(
            valid["RSI_signal"].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False,
        )

    def test_macd_signal_detects_zero_crossover(self):
        """
        MACD_signal must be True on the first day MACD_diff turns positive
        after being non-positive.
        """
        df = self._make_long_df()
        result = STRATEGY.calculate_macd_and_rsi(df)
        signal_rows = result[result["MACD_signal"]]

        for _, row in signal_rows.iterrows():
            assert row["MACD_diff"] > 0, "MACD_signal True but MACD_diff not positive"
            assert row["MACD_diff_prev"] <= 0, "MACD_signal True but previous diff not <= 0"

    def test_macd_signal_false_when_already_positive(self):
        """If MACD_diff was already positive on the previous bar, no crossover signal."""
        df = self._make_long_df()
        result = STRATEGY.calculate_macd_and_rsi(df)
        # Both current and prev positive → no crossover
        both_positive = result[(result["MACD_diff"] > 0) & (result["MACD_diff_prev"] > 0)]
        assert both_positive["MACD_signal"].sum() == 0

    def test_declining_prices_push_rsi_below_50(self):
        """A steadily declining price series should produce RSI < 50 for most of the period."""
        prices = [200.0 - i * 1.5 for i in range(60)]  # strong downtrend
        df = self._make_long_df(n=60, prices=prices)
        result = STRATEGY.calculate_macd_and_rsi(df)
        valid = result["RSI"].dropna()

        # At least half of non-NaN RSI values should be below 50
        below_50 = (valid < 50).sum()
        assert below_50 > len(valid) / 2


# ===========================================================================
# calculate_annualized_return (pure arithmetic — no DB needed)
# ===========================================================================

class TestCalculateAnnualizedReturn:
    def test_flat_return(self):
        """Same initial and final value over any period gives 0% annualized."""
        result = TwStrategy.calculate_annualized_return(1000.0, 1000.0, 1.0)
        assert result == pytest.approx(0.0)

    def test_double_in_one_year(self):
        """Doubling in 1 year gives 100% annualized return."""
        result = TwStrategy.calculate_annualized_return(1000.0, 2000.0, 1.0)
        assert result == pytest.approx(1.0)

    def test_double_in_two_years(self):
        """Doubling in 2 years gives ~41.4% annualized (√2 - 1)."""
        result = TwStrategy.calculate_annualized_return(1000.0, 2000.0, 2.0)
        assert result == pytest.approx(2 ** 0.5 - 1, rel=1e-6)

    def test_zero_initial_raises(self):
        """Zero initial value must raise ValueError."""
        with pytest.raises(ValueError):
            TwStrategy.calculate_annualized_return(0.0, 1000.0, 1.0)


# ===========================================================================
# calculate_asset_value_and_ratio
# ===========================================================================

class TestCalculateAssetValueAndRatio:
    def test_basic_calculation(self):
        asset, roi = STRATEGY.calculate_asset_value_and_ratio(
            position_size=10.0,
            last_closed_price=110.0,
            broker_dividend=50.0,
            total_investment=1000.0,
        )
        # asset = 10 * 110 + 50 = 1150
        assert asset == pytest.approx(1150.0)
        # roi = (1150 - 1000) / 1000 = 0.15
        assert roi == pytest.approx(0.15)

    def test_zero_investment_gives_zero_roi(self):
        _, roi = STRATEGY.calculate_asset_value_and_ratio(0.0, 100.0, 0.0, 0.0)
        assert roi == 0.0

    def test_loss_gives_negative_roi(self):
        asset, roi = STRATEGY.calculate_asset_value_and_ratio(
            position_size=10.0,
            last_closed_price=80.0,
            broker_dividend=0.0,
            total_investment=1000.0,
        )
        assert asset == pytest.approx(800.0)
        assert roi < 0.0
