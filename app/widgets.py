"""Custom-painted KEYGEN widgets."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QPoint,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import animations
from app.icons import brand_pixmap, paint_icon
from app.theme import Palette, mix, strength_color


def _mono() -> QFont:
    f = QFont("Cascadia Mono")
    if f.exactMatch() is False:
        f = QFont("Consolas")
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


class HoverMixin:
    def _init_hover(self) -> None:
        self._hover = 0.0
        self._press = 0.0
        self._h_anim = None
        self.setMouseTracking(True)

    def enterEvent(self, e) -> None:
        self._h_anim = animations.hover_anim(self, self._hover, 1.0, 130, self._set_h)
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._h_anim = animations.hover_anim(self, self._hover, 0.0, 160, self._set_h)
        super().leaveEvent(e)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = 1.0
            self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._press = 0.0
        self.update()
        super().mouseReleaseEvent(e)

    def _set_h(self, v) -> None:
        self._hover = float(v)
        self.update()


class IconLabel(QWidget):
    def __init__(self, name: str, size: int = 18, parent=None) -> None:
        super().__init__(parent)
        self.name = name
        self.sz = size
        self.color = QColor("#8E98A7")
        self.rotation = 0.0
        self.setFixedSize(size, size)

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        paint_icon(p, self.name, QRectF(self.rect()), self.color, rotation=self.rotation)


class IconButton(HoverMixin, QWidget):
    clicked = Signal()

    def __init__(self, name: str, tooltip: str = "", size: int = 34, parent=None) -> None:
        super().__init__(parent)
        self._init_hover()
        self.name = name
        self.pal: Palette | None = None
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = mix(QColor(0, 0, 0, 0), pal.hover, self._hover)
        if self._press:
            bg = mix(bg, pal.border, 0.4)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 8, 8)
        paint_icon(p, self.name, QRectF(self.rect()).adjusted(7, 7, -7, -7), pal.secondary)


class PillButton(HoverMixin, QWidget):
    clicked = Signal()

    def __init__(self, text: str, icon: str = "", primary: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._init_hover()
        self.text = text
        self.icon = icon
        self.primary = primary
        self.success = False
        self.selected = False
        self.pal: Palette | None = None
        self._rot = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.setMinimumWidth(132)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def get_rot(self) -> float:
        return self._rot

    def set_rot(self, v: float) -> None:
        self._rot = v
        self.update()

    rotation = Property(float, get_rot, set_rot)

    def sizeHint(self) -> QSize:
        return QSize(160, 42)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self.success:
            bg, fg, border = pal.success, QColor("#06281C"), pal.success
        elif self.selected:
            bg, fg, border = pal.accent, QColor("#1A0A04"), pal.accent
        elif self.primary:
            bg = mix(pal.accent, QColor("#FF8A4A"), self._hover * 0.35)
            if self._press:
                bg = mix(bg, QColor("#C73A10"), 0.25)
            fg = QColor("#1A0A04")
            border = bg
        else:
            bg = mix(pal.elevated, pal.hover, self._hover)
            fg = pal.text
            border = mix(pal.border, pal.accent, self._hover * 0.4)
        p.setPen(border)
        p.setBrush(bg)
        p.drawRoundedRect(r, 12, 12)
        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        tw = p.fontMetrics().horizontalAdvance(self.text)
        icon_w = 18 if self.icon else 0
        gap = 8 if self.icon else 0
        total = icon_w + gap + tw
        x = (self.width() - total) / 2
        if self.icon:
            paint_icon(
                p,
                self.icon,
                QRectF(x, (self.height() - 18) / 2, 18, 18),
                fg if not self.primary else QColor("#2A0E06"),
                rotation=self._rot,
            )
            x += icon_w + gap
        p.setPen(fg)
        p.drawText(QRect(int(x), 0, tw + 4, self.height()), Qt.AlignmentFlag.AlignVCenter, self.text)


class Segmented(HoverMixin, QWidget):
    changed = Signal(str)

    def __init__(self, items: list[tuple[str, str, str]], parent=None) -> None:
        super().__init__(parent)
        self._init_hover()
        self.items = items
        self.current = items[0][0]
        self.pal: Palette | None = None
        self.setFixedHeight(44)
        self.setMinimumWidth(420)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        if e.button() != Qt.MouseButton.LeftButton:
            return
        w = self.width() / len(self.items)
        i = int(e.position().x() / w)
        if 0 <= i < len(self.items):
            key = self.items[i][0]
            if key != self.current:
                self.current = key
                self.changed.emit(key)
                self.update()

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(pal.border)
        p.setBrush(pal.panel)
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)
        n = len(self.items)
        slot = r.width() / n
        for i, (key, label, icon) in enumerate(self.items):
            cell = QRectF(r.x() + i * slot + 4, r.y() + 4, slot - 8, r.height() - 8)
            active = key == self.current
            if active:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(pal.accent)
                p.drawRoundedRect(cell, 10, 10)
                col = QColor("#1A0A04")
            else:
                col = pal.secondary
            font = QFont("Segoe UI", 10)
            font.setWeight(QFont.Weight.DemiBold)
            p.setFont(font)
            tw = p.fontMetrics().horizontalAdvance(label)
            total = 18 + 8 + tw
            x = cell.x() + (cell.width() - total) / 2
            paint_icon(p, icon, QRectF(x, cell.y() + 8, 18, 18), col)
            p.setPen(col)
            p.drawText(QRect(int(x + 26), int(cell.y()), tw + 8, int(cell.height())), Qt.AlignmentFlag.AlignVCenter, label)



class CompactToggle(HoverMixin, QWidget):
    changed = Signal(bool)

    def __init__(self, title: str, checked: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._init_hover()
        self.title = title
        self.checked = checked
        self.pal: Palette | None = None
        self._knob = 1.0 if checked else 0.0
        self.setFixedHeight(28)
        self.setMinimumWidth(168)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAutoFillBackground(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def get_knob(self) -> float:
        return self._knob

    def set_knob(self, v: float) -> None:
        self._knob = float(v)
        self.update()

    knob = Property(float, get_knob, set_knob)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.checked = not self.checked
            animations.tween(self, b"knob", self._knob, 1.0 if self.checked else 0.0, 160)
            self.changed.emit(self.checked)

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        tw, th = 36, 20
        track = QRectF(0, (self.height() - th) / 2, tw, th)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix(pal.track, pal.accent, self._knob))
        p.drawRoundedRect(track, 10, 10)
        kx = 2 + (tw - 18 - 2) * self._knob
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(kx, track.y() + 2, 16, 16))
        p.setPen(pal.text)
        f = QFont("Segoe UI", 9)
        f.setWeight(QFont.Weight.Medium)
        p.setFont(f)
        p.drawText(
            QRect(int(tw + 10), 0, self.width() - int(tw) - 10, self.height()),
            Qt.AlignmentFlag.AlignVCenter,
            self.title,
        )


class Toggle(HoverMixin, QWidget):
    changed = Signal(bool)

    def __init__(self, title: str, subtitle: str, checked: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._init_hover()
        self.title = title
        self.subtitle = subtitle
        self.checked = checked
        self.pal: Palette | None = None
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.checked = not self.checked
            self.changed.emit(self.checked)
            self.update()

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        bg = mix(pal.elevated, pal.hover, self._hover * 0.7)
        p.setPen(pal.border)
        p.setBrush(bg)
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)
        p.setPen(pal.text)
        f = QFont("Segoe UI", 10)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.drawText(QRect(16, 8, self.width() - 80, 22), Qt.AlignmentFlag.AlignVCenter, self.title)
        p.setPen(pal.muted)
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRect(16, 28, self.width() - 80, 18), Qt.AlignmentFlag.AlignVCenter, self.subtitle)
        # switch
        tw, th = 40, 22
        tx, ty = self.width() - tw - 16, (self.height() - th) / 2
        track = QRectF(tx, ty, tw, th)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.accent if self.checked else pal.track)
        p.drawRoundedRect(track, 11, 11)
        knob_x = tx + (tw - 18 - 3) if self.checked else tx + 3
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(knob_x, ty + 2, 18, 18))


class LengthSlider(QWidget):
    changed = Signal(int)

    def __init__(self, lo=4, hi=64, value=16, parent=None) -> None:
        super().__init__(parent)
        self.lo, self.hi, self.value = lo, hi, value
        self.pal: Palette | None = None
        self._drag = False
        self.ticks = (8, 12, 16, 20, 24, 32, 64)
        self.setFixedHeight(44)
        self.setMinimumWidth(220)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _pos_to_val(self, x: float) -> int:
        m = 10
        t = max(0.0, min(1.0, (x - m) / max(1, self.width() - 2 * m)))
        return int(round(self.lo + t * (self.hi - self.lo)))

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self._drag = True
        self._apply(e.position().x())

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag:
            self._apply(e.position().x())

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._drag = False

    def _apply(self, x: float) -> None:
        v = self._pos_to_val(x)
        if v != self.value:
            self.value = v
            self.changed.emit(v)
            self.update()

    def set_value(self, v: int) -> None:
        self.value = max(self.lo, min(self.hi, v))
        self.update()

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 10
        y = 12
        w = self.width() - 2 * m
        t = (self.value - self.lo) / (self.hi - self.lo)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.track)
        p.drawRoundedRect(QRectF(m, y - 3, w, 6), 3, 3)
        p.setBrush(pal.accent)
        p.drawRoundedRect(QRectF(m, y - 3, w * t, 6), 3, 3)
        p.setBrush(QColor("#FFFFFF"))
        p.setPen(pal.accent)
        p.drawEllipse(QPoint(int(m + w * t), int(y)), 8, 8)
        p.setPen(pal.muted)
        p.setFont(QFont("Segoe UI", 8))
        for tick in self.ticks:
            tx = m + w * (tick - self.lo) / (self.hi - self.lo)
            col = pal.accent if tick == self.value else pal.muted
            p.setPen(col)
            p.drawText(QRect(int(tx - 14), 20, 28, 18), Qt.AlignmentFlag.AlignCenter, str(tick))


class Chip(QWidget):
    def __init__(self, count: str = "0", suffix: str = "Upper", parent=None) -> None:
        super().__init__(parent)
        self.count = count
        self.suffix = suffix
        self.pal: Palette | None = None
        self.setFixedHeight(30)
        self.setMinimumWidth(88)

    def sizeHint(self) -> QSize:
        return QSize(96, 30)

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(pal.border)
        p.setBrush(pal.chip)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)
        f = QFont("Segoe UI", 9)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        txt = f"{self.count}  {self.suffix}"
        # draw count in accent
        cw = p.fontMetrics().horizontalAdvance(self.count)
        rest = f"  {self.suffix}"
        total = p.fontMetrics().horizontalAdvance(txt)
        x = (self.width() - total) / 2
        p.setPen(pal.accent)
        p.drawText(int(x), 0, cw + 2, self.height(), Qt.AlignmentFlag.AlignVCenter, self.count)
        p.setPen(pal.secondary)
        p.drawText(int(x + cw), 0, total, self.height(), Qt.AlignmentFlag.AlignVCenter, rest)


class NavItem(HoverMixin, QWidget):
    clicked = Signal()

    def __init__(self, icon: str, label: str, parent=None) -> None:
        super().__init__(parent)
        self._init_hover()
        self.icon = icon
        self.label = label
        self.active = False
        self.pal: Palette | None = None
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(8, 2, -8, -2)
        if self.active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal.accent_soft)
            p.drawRoundedRect(r, 10, 10)
            col = pal.accent
        else:
            if self._hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(mix(QColor(0, 0, 0, 0), pal.hover, self._hover))
                p.drawRoundedRect(r, 10, 10)
            col = pal.secondary
        paint_icon(p, self.icon, QRectF(r.x() + 10, r.y() + 8, 18, 18), col)
        f = QFont("Segoe UI", 10)
        f.setWeight(QFont.Weight.DemiBold if self.active else QFont.Weight.Medium)
        p.setFont(f)
        p.setPen(pal.text if self.active else pal.secondary)
        p.drawText(r.adjusted(36, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, self.label)


class StrengthBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.level = "MODERATE"
        self.bits = 0.0
        self.pal: Palette | None = None
        self.setFixedHeight(8)

    def paintEvent(self, _) -> None:
        pal = self.pal
        if not pal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        segs, gap = 5, 4
        fill = min(5, max(0, int(round(self.bits / 22.0)))) if self.bits else 0
        colors = [pal.accent, QColor("#FF8A1F"), pal.warning, QColor("#84CC16"), pal.success]
        sw = (self.width() - gap * (segs - 1)) / max(1, segs)
        for i in range(segs):
            p.setBrush(colors[i] if i < fill else pal.track)
            p.drawRoundedRect(QRectF(i * (sw + gap), 0, sw, self.height()), 4, 4)


class ToastHost(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._items: list[QWidget] = []

    def show_toast(self, text: str, pal: Palette) -> None:
        t = QLabel(text, self)
        t.setStyleSheet(
            f"background:{pal.elevated.name()}; color:{pal.text.name()};"
            f"border:1px solid {pal.border.name()}; border-radius:10px; padding:10px 16px;"
            f"font: 600 12px 'Segoe UI';"
        )
        t.adjustSize()
        fx = QGraphicsOpacityEffect(t)
        t.setGraphicsEffect(fx)
        fx.setOpacity(0)
        self._items.append(t)
        self._layout()
        t.show()
        animations.tween(fx, b"opacity", 0.0, 1.0, 180)

        def hide():
            animations.tween(fx, b"opacity", 1.0, 0.0, 220, finished=lambda: self._drop(t))

        animations.later(1800, hide)

    def _drop(self, t: QWidget) -> None:
        if t in self._items:
            self._items.remove(t)
        t.deleteLater()
        self._layout()

    def _layout(self) -> None:
        y = 16
        for item in self._items:
            item.move((self.width() - item.width()) // 2, y)
            y += item.height() + 8

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._layout()


class StyledLine(QLineEdit):
    def apply(self, pal: Palette, mono: bool = False) -> None:
        f = _mono() if mono else QFont("Segoe UI", 10)
        if mono:
            f.setPointSize(11)
        self.setFont(f)
        self.setStyleSheet(
            f"""
            QLineEdit {{
                background: {pal.input.name()};
                color: {pal.text.name()};
                border: 1px solid {pal.border.name()};
                border-radius: 10px;
                padding: 10px 12px;
                selection-background-color: {pal.accent.name()};
            }}
            QLineEdit:focus {{
                border: 1px solid {pal.accent.name()};
            }}
            """
        )


class BrandMark(QWidget):
    def __init__(self, size: int = 56, parent=None) -> None:
        super().__init__(parent)
        self.sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.drawPixmap(0, 0, brand_pixmap(self.sz, self.devicePixelRatioF()))
