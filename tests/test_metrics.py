"""
Unit tests and regression checks for dashboard metrics and formatting components.
"""

import math
import typing
import pytest
from dashboard.components.metrics import (
    format_currency,
    format_number,
    format_pct,
    pd_is_nan,
    render_segment_badge,
)
import dashboard.components.metrics as metrics_module


def test_metrics_module_import_and_type_hints():
    """Verify metrics module imports cleanly and type annotations evaluate without NameError."""
    assert metrics_module is not None
    # Evaluating type hints ensures annotations like val: Any are resolved
    hints = typing.get_type_hints(pd_is_nan)
    assert "val" in hints
    assert hints["val"] is typing.Any
    assert hints["return"] is bool


def test_pd_is_nan():
    """Verify NaN detection helper correctly identifies NaN values across types."""
    assert pd_is_nan(float("nan")) is True
    assert pd_is_nan(math.nan) is True
    assert pd_is_nan(100) is False
    assert pd_is_nan(0.0) is False
    assert pd_is_nan(None) is False
    assert pd_is_nan("text") is False


def test_format_currency():
    """Verify currency formatting for regular, compact, zero, None, and NaN inputs."""
    assert format_currency(1234.56) == "£1,234.56"
    assert format_currency(1234.56, compact=True) == "£1.2K"
    assert format_currency(2500000.0, compact=True) == "£2.50M"
    assert format_currency(0) == "£0.00"
    assert format_currency(None) == "£0.00"
    assert format_currency(float("nan")) == "£0.00"


def test_format_number():
    """Verify number formatting with comma separators, zero, None, and NaN inputs."""
    assert format_number(1234567) == "1,234,567"
    assert format_number(42) == "42"
    assert format_number(0) == "0"
    assert format_number(None) == "0"
    assert format_number(float("nan")) == "0"


def test_format_pct():
    """Verify percentage formatting for positive, negative, zero, None, and NaN inputs."""
    assert format_pct(12.34) == "+12.34%"
    assert format_pct(-5.67) == "-5.67%"
    assert format_pct(0) == "0.0%"
    assert format_pct(0.0) == "0.0%"
    assert format_pct(None) == "0.0%"
    assert format_pct(float("nan")) == "0.0%"


def test_render_segment_badge():
    """Verify segment badge HTML generation with proper background colors."""
    badge_champions = render_segment_badge("Champions")
    assert "Champions" in badge_champions
    assert "#2E7D32" in badge_champions

    badge_unknown = render_segment_badge("Unknown Segment")
    assert "Unknown Segment" in badge_unknown
    assert "#546E7A" in badge_unknown
