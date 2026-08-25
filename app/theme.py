"""Coherent dark / light theme palettes."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor


def _c(hex_color: str) -> QColor:
    return QColor(hex_color)


def mix(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


@dataclass(frozen=True)
class Palette:
    name: str
    bg: QColor
    panel: QColor
    elevated: QColor
    border: QColor
    text: QColor
    secondary: QColor
    muted: QColor
    accent: QColor
    accent_soft: QColor
    success: QColor
    warning: QColor
    error: QColor
    track: QColor
    sidebar: QColor
    input: QColor
    chip: QColor
    hover: QColor
    shadow: QColor


DARK = Palette(
    name="dark",
    bg=_c("#0B0D10"),
    panel=_c("#111419"),
    elevated=_c("#171B21"),
    border=_c("#242A32"),
    text=_c("#F4F6F8"),
    secondary=_c("#8E98A7"),
    muted=_c("#626B78"),
    accent=_c("#FF5A1F"),
    accent_soft=QColor(255, 90, 31, 36),
    success=_c("#10B981"),
    warning=_c("#F59E0B"),
    error=_c("#EF4444"),
    track=_c("#1C222A"),
    sidebar=_c("#0E1115"),
    input=_c("#14181E"),
    chip=_c("#1A1F26"),
    hover=_c("#1E242C"),
    shadow=QColor(0, 0, 0, 90),
)

LIGHT = Palette(
    name="light",
    bg=_c("#F4F2EE"),
    panel=_c("#FFFFFF"),
    elevated=_c("#FFFFFF"),
    border=_c("#E2DED6"),
    text=_c("#16181D"),
    secondary=_c("#5C6570"),
    muted=_c("#8A919A"),
    accent=_c("#E04A12"),
    accent_soft=QColor(224, 74, 18, 28),
    success=_c("#059669"),
    warning=_c("#D97706"),
    error=_c("#DC2626"),
    track=_c("#E8E4DC"),
    sidebar=_c("#EDEAE4"),
    input=_c("#F7F5F1"),
    chip=_c("#EFEBE4"),
    hover=_c("#E8E3DA"),
    shadow=QColor(20, 16, 10, 28),
)


def strength_color(level: str, pal: Palette) -> QColor:
    return {
        "WEAK": pal.error,
        "FAIR": pal.warning,
        "MODERATE": QColor("#3B82F6"),
        "STRONG": pal.success,
        "VERY STRONG": pal.success,
    }.get(level, pal.muted)
