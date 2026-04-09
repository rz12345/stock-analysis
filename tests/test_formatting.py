"""
Unit tests for app/utils/formatting.py
"""
import pytest
from app.utils.formatting import format_float, format_pct


class TestFormatFloat:
    def test_value_less_than_1_uses_4_decimals(self):
        assert format_float(0.1234) == "0.1234"

    def test_value_less_than_1_rounds_to_4_decimals(self):
        assert format_float(0.12345) == "0.1235"   # standard rounding

    def test_value_equal_to_1_uses_2_decimals(self):
        assert format_float(1.0) == "1.00"

    def test_value_greater_than_1_uses_2_decimals(self):
        assert format_float(12345.678) == "12345.68"

    def test_zero_uses_4_decimals(self):
        # 0.0 < 1 → 4 decimal places
        assert format_float(0.0) == "0.0000"

    def test_negative_value_uses_4_decimals(self):
        # All negative floats satisfy `value < 1`, so they get 4 decimal places
        assert format_float(-1.5) == "-1.5000"
        assert format_float(-0.5) == "-0.5000"

    def test_non_float_int_returned_as_is(self):
        result = format_float(42)
        assert result == 42

    def test_non_float_string_returned_as_is(self):
        result = format_float("hello")
        assert result == "hello"

    def test_non_float_none_returned_as_is(self):
        result = format_float(None)
        assert result is None


class TestFormatPct:
    def test_zero_gives_zero_percent(self):
        assert format_pct(0.0) == "0.00%"

    def test_one_gives_100_percent(self):
        assert format_pct(1.0) == "100.00%"

    def test_quarter_gives_25_percent(self):
        assert format_pct(0.25) == "25.00%"

    def test_negative_value(self):
        assert format_pct(-0.1) == "-10.00%"

    def test_rounding(self):
        # 0.12345 * 100 = 12.345 → "12.35%"
        assert format_pct(0.12345) == "12.35%"
