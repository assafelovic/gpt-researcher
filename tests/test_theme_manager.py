from __future__ import annotations

import pytest

from gpt_researcher_desktop.theme import ThemeManager
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor


class TestAdjustColor:
    @staticmethod
    def test_valid_color():
        color = QColor("red")
        adjusted_color: QColor = ThemeManager.adjust_color(color, lightness=50, saturation=150, hue_shift=30)
        assert adjusted_color.isValid()
        assert adjusted_color != color  # Ensure the color has been modified

    @staticmethod
    def test_invalid_color():
        with pytest.raises(ValueError, match="Invalid color provided"):
            ThemeManager.adjust_color("invalid_color")

    @staticmethod
    def test_lightness_adjustment():
        color = QColor("red")
        adjusted_color = ThemeManager.adjust_color(color, lightness=50)
        _, _, original_v, _ = color.getHsv()
        _, _, adjusted_v, _ = adjusted_color.getHsv()
        
        assert adjusted_v < original_v

    @staticmethod
    def test_lightness_extremes():
        color = QColor("red")

        dark_color = ThemeManager.adjust_color(color, lightness=0)
        _, _, dark_v, _ = dark_color.getHsv()
        assert dark_v == 0

        light_color = ThemeManager.adjust_color(color, lightness=200)
        _, _, light_v, _ = light_color.getHsv()
        assert light_v == 255

        # test invalid extremes
        with pytest.raises(AssertionError):  # expecting AssertionError from PyQt's internal checks, as HSL requires 0-255
            ThemeManager.adjust_color(color, lightness=-1)

        with pytest.raises(AssertionError):  # expecting AssertionError from PyQt's internal checks, as HSL requires 0-255
            ThemeManager.adjust_color(color, lightness=256)

    @staticmethod
    def test_saturation_adjustment():
        color = QColor("red")
        adjusted_color = ThemeManager.adjust_color(color, saturation=50)
        _, original_s, _, _ = color.getHsv()
        _, adjusted_s, _, _ = adjusted_color.getHsv()

        assert adjusted_s < original_s

    @staticmethod
    def test_saturation_extremes():
        color = QColor("red")
        desaturated_color = ThemeManager.adjust_color(color, saturation=0)
        _, desaturated_s, _, _ = desaturated_color.getHsv()

        assert desaturated_s == 0

        supersaturated_color = ThemeManager.adjust_color(color, saturation=200)
        _, supersaturated_s, _, _ = supersaturated_color.getHsv()
        assert supersaturated_s == 255

    @staticmethod
    def test_hue_shift():
        color = QColor("red")  # Red is 0 degrees hue
        adjusted_color = ThemeManager.adjust_color(color, hue_shift=30)
        original_h, _, _, _ = color.getHsv()
        adjusted_h, _, _, _ = adjusted_color.getHsv()

        assert (adjusted_h - original_h) % 360 == 30

    @staticmethod
    def test_hue_shift_wraparound():
        color = QColor("red")
        adjusted_color = ThemeManager.adjust_color(color, hue_shift=400)  # Should wrap around
        adjusted_h, _, _, _ = adjusted_color.getHsv()
        assert adjusted_h == 40

        adjusted_color = ThemeManager.adjust_color(color, hue_shift=-400)  # Should wrap around negatively
        adjusted_h, _, _, _ = adjusted_color.getHsv()

        assert adjusted_h == 320  # equivalent to -40, wraparound

    @staticmethod
    def test_qt_global_color():
        adjusted_color = ThemeManager.adjust_color(Qt.GlobalColor.red, lightness=50)
        assert adjusted_color.isValid()

    @staticmethod
    def test_integer_color():
        adjusted_color = ThemeManager.adjust_color(0xFF0000, lightness=50)
        assert adjusted_color.isValid()

    @staticmethod
    def test_color_name():
        adjusted_color = ThemeManager.adjust_color("red", lightness=50)
        assert adjusted_color.isValid()
