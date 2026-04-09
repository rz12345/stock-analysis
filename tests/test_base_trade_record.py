"""
Unit tests for BaseTradeRecord._detect_split()
"""
import pytest
import pandas as pd
import numpy as np

from app.repositories.base_trade_record import BaseTradeRecord


THRESHOLD = BaseTradeRecord.SPLIT_RATIO_THRESHOLD   # 1.9


def _make_price_df(prices: list, col: str = "close") -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(prices), freq="B")
    return pd.DataFrame({"date": dates, col: [float(p) for p in prices]})


# ===========================================================================
# _detect_split
# ===========================================================================

class TestDetectSplit:
    def test_stable_prices_no_split(self):
        """Small daily fluctuations should not trigger split detection."""
        prices = [100.0, 101.0, 99.5, 100.3, 100.0, 98.0, 102.0]
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is False

    def test_price_halves_in_one_day_detected(self):
        """Price dropping by half (ratio 2× reverse) exceeds threshold 1.9."""
        prices = [100.0] * 10 + [50.0] + [50.0] * 5   # halving on day 11
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is True

    def test_price_doubles_in_one_day_detected(self):
        """Price doubling (ratio 2×) exceeds threshold 1.9."""
        prices = [100.0] * 10 + [200.0] + [200.0] * 5
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is True

    def test_ratio_exactly_at_threshold_not_detected(self):
        """A ratio of exactly SPLIT_RATIO_THRESHOLD must NOT trigger (strict >)."""
        # ratio = next / prev = 1.9 → max_ratio = 1.9, not > 1.9
        prices = [100.0, 100.0 * THRESHOLD]
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is False

    def test_ratio_just_above_threshold_detected(self):
        """A ratio of THRESHOLD + ε must trigger split detection."""
        prices = [100.0, 100.0 * (THRESHOLD + 0.01)]
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is True

    def test_three_for_two_split_not_detected(self):
        """A 3-for-2 split (ratio ~1.5) is below threshold and must not trigger."""
        prices = [100.0] * 5 + [66.67] + [66.67] * 5   # forward split 3:2
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is False

    def test_single_row_no_split(self):
        """A single-row DataFrame has no pair to compare; must return False."""
        df = _make_price_df([150.0])
        assert BaseTradeRecord._detect_split(df, "close") is False

    def test_custom_price_column(self):
        """_detect_split must use the supplied column name, not hardcode 'close'."""
        prices = [100.0] * 10 + [50.0]
        df = _make_price_df(prices, col="adjClose")
        assert BaseTradeRecord._detect_split(df, "adjClose") is True

    def test_unsorted_dates_still_detected(self):
        """Detection should work even if the DataFrame is not pre-sorted by date."""
        prices_sorted = [100.0] * 10 + [50.0]
        df = _make_price_df(prices_sorted)
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        # The function sorts internally, so it must still detect
        assert BaseTradeRecord._detect_split(df_shuffled, "close") is True

    def test_monotonically_increasing_prices_no_split(self):
        """Gradual uptrend with max daily gain well below threshold → no split."""
        prices = [100.0 + i * 0.5 for i in range(50)]   # max ratio ≈ 1.005
        df = _make_price_df(prices)
        assert BaseTradeRecord._detect_split(df, "close") is False
