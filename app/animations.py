"""Event-driven Qt animations. No sleep()."""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QTimer,
    QVariantAnimation,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

OUT = QEasingCurve.Type.OutCubic


def tween(target: QObject, prop: bytes, start, end, ms: int = 180, finished=None) -> QPropertyAnimation:
    anim = QPropertyAnimation(target, prop, target)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setDuration(ms)
    anim.setEasingCurve(OUT)
    if finished:
        anim.finished.connect(finished)
    anim.start()
    return anim


def fade_widget(widget: QWidget, show: bool, ms: int = 200) -> QPropertyAnimation:
    fx = widget.graphicsEffect()
    if not isinstance(fx, QGraphicsOpacityEffect):
        fx = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(fx)
    start, end = (0.0, 1.0) if show else (fx.opacity(), 0.0)
    if show:
        widget.show()
    anim = tween(fx, b"opacity", start, end, ms)
    if not show:
        anim.finished.connect(widget.hide)
    return anim


def hover_anim(owner: QObject, start: float, end: float, ms: int = 140, on_value=None) -> QVariantAnimation:
    anim = QVariantAnimation(owner)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setDuration(ms)
    anim.setEasingCurve(OUT)
    if on_value:
        anim.valueChanged.connect(on_value)
    anim.start()
    return anim


def later(ms: int, fn) -> None:
    QTimer.singleShot(ms, fn)


def shake(widget: QWidget) -> None:
    """Horizontal error shake using geometry animation."""
    geo = widget.geometry()
    anim = QVariantAnimation(widget)
    anim.setDuration(320)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    offsets = (0, -10, 10, -7, 7, -3, 0)

    def step(v):
        t = float(v)
        i = min(int(t * (len(offsets) - 1)), len(offsets) - 2)
        frac = t * (len(offsets) - 1) - i
        dx = offsets[i] + (offsets[i + 1] - offsets[i]) * frac
        widget.move(geo.x() + int(dx), geo.y())

    anim.valueChanged.connect(step)
    anim.finished.connect(lambda: widget.setGeometry(geo))
    anim.start()
