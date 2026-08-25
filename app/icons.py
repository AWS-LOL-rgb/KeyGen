"""Programmatic 24×24 line icons (QPainter). No SVG / icon fonts."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

SIZE = 24.0


def _pen(color: QColor, width: float = 1.8) -> QPen:
    p = QPen(color, width)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def _star(cx: float, cy: float, r_out: float, r_in: float, n: int = 4) -> QPainterPath:
    path = QPainterPath()
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / n
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    return path


def draw_shield(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(12, 3)
    path.cubicTo(16, 3.5, 19.5, 4.5, 20, 6)
    path.lineTo(20, 12)
    path.cubicTo(20, 17.5, 16.5, 20.5, 12, 21.5)
    path.cubicTo(7.5, 20.5, 4, 17.5, 4, 12)
    path.lineTo(4, 6)
    path.cubicTo(4.5, 4.5, 8, 3.5, 12, 3)
    p.drawPath(path)


def draw_sparkles(p: QPainter) -> None:
    p.drawPath(_star(9, 11, 5.2, 2.1, 4))
    p.drawPath(_star(17, 7, 2.6, 1.05, 4))
    p.drawPath(_star(17.5, 16.5, 2.0, 0.8, 4))


def draw_vault(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(4, 5, 16, 14), 2.5, 2.5)
    p.drawEllipse(QPointF(12, 12), 3.2, 3.2)
    p.drawLine(QPointF(12, 12), QPointF(14.4, 10.2))


def draw_sun(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 3.4, 3.4)
    for i in range(8):
        a = i * math.pi / 4
        p.drawLine(
            QPointF(12 + 5.6 * math.cos(a), 12 + 5.6 * math.sin(a)),
            QPointF(12 + 8.2 * math.cos(a), 12 + 8.2 * math.sin(a)),
        )


def draw_moon(p: QPainter) -> None:
    path = QPainterPath()
    path.addEllipse(QRectF(6, 5, 12, 14))
    cut = QPainterPath()
    cut.addEllipse(QRectF(10, 4, 12, 14))
    p.drawPath(path.subtracted(cut))


def draw_key(p: QPainter) -> None:
    p.drawEllipse(QPointF(8, 12), 3.6, 3.6)
    p.drawLine(QPointF(11.6, 12), QPointF(20, 12))
    p.drawLine(QPointF(18, 12), QPointF(18, 15.5))
    p.drawLine(QPointF(15.5, 12), QPointF(15.5, 14.5))


def draw_book(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(6, 5)
    path.lineTo(11, 6.5)
    path.lineTo(11, 19)
    path.lineTo(6, 17.5)
    path.closeSubpath()
    path.moveTo(18, 5)
    path.lineTo(13, 6.5)
    path.lineTo(13, 19)
    path.lineTo(18, 17.5)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(12, 6.5), QPointF(12, 19))


def draw_hash(p: QPainter) -> None:
    p.drawLine(QPointF(9, 5), QPointF(7, 19))
    p.drawLine(QPointF(17, 5), QPointF(15, 19))
    p.drawLine(QPointF(5, 9.5), QPointF(20, 9.5))
    p.drawLine(QPointF(4, 14.5), QPointF(19, 14.5))


def draw_refresh(p: QPainter) -> None:
    path = QPainterPath()
    path.arcMoveTo(5, 5, 14, 14, 40)
    path.arcTo(5, 5, 14, 14, 40, 260)
    p.drawPath(path)
    end_a = math.radians(40 + 260)
    ex = 12 + 7 * math.cos(end_a)
    ey = 12 - 7 * math.sin(end_a)
    tx, ty = -math.sin(end_a), -math.cos(end_a)
    nx, ny = -ty, tx
    p.drawLine(QPointF(ex, ey), QPointF(ex - tx * 4 + nx * 3, ey - ty * 4 + ny * 3))
    p.drawLine(QPointF(ex, ey), QPointF(ex - tx * 4 - nx * 3, ey - ty * 4 - ny * 3))


def draw_copy(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(8, 7, 11, 13), 1.8, 1.8)
    path = QPainterPath()
    path.moveTo(8, 16)
    path.lineTo(5, 16)
    path.lineTo(5, 4)
    path.lineTo(15, 4)
    path.lineTo(15, 7)
    p.drawPath(path)


def draw_save(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(6, 4)
    path.lineTo(16, 4)
    path.lineTo(20, 8)
    path.lineTo(20, 20)
    path.lineTo(4, 20)
    path.lineTo(4, 4)
    path.closeSubpath()
    p.drawPath(path)
    p.drawRect(QRectF(8, 4, 7, 5))
    p.drawRoundedRect(QRectF(7, 13, 10, 7), 1, 1)


def draw_warning(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(12, 3.5)
    path.lineTo(21.5, 20)
    path.lineTo(2.5, 20)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(12, 9), QPointF(12, 14.5))
    p.drawPoint(QPointF(12, 17.4))


def draw_lock(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(6, 11, 12, 9.5), 2, 2)
    path = QPainterPath()
    path.arcMoveTo(8, 5, 8, 8, 0)
    path.arcTo(8, 5, 8, 8, 0, 180)
    p.drawPath(path)


def draw_unlock(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(6, 11, 12, 9.5), 2, 2)
    path = QPainterPath()
    path.arcMoveTo(8, 4, 8, 8, 20)
    path.arcTo(8, 4, 8, 8, 20, 160)
    p.drawPath(path)


def draw_lightning(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(13.5, 3)
    path.lineTo(7, 13)
    path.lineTo(12, 13)
    path.lineTo(10.5, 21)
    path.lineTo(18, 10)
    path.lineTo(13, 10)
    path.closeSubpath()
    p.drawPath(path)


def draw_plus(p: QPainter) -> None:
    p.drawLine(QPointF(12, 5), QPointF(12, 19))
    p.drawLine(QPointF(5, 12), QPointF(19, 12))


def draw_search(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.4, 5.4)
    p.drawLine(QPointF(14.6, 14.6), QPointF(20, 20))


def draw_database(p: QPainter) -> None:
    p.drawEllipse(QRectF(5, 4, 14, 5))
    p.drawLine(QPointF(5, 6.5), QPointF(5, 17.5))
    p.drawLine(QPointF(19, 6.5), QPointF(19, 17.5))
    p.drawArc(QRectF(5, 15, 14, 5), 180 * 16, 180 * 16)
    p.drawArc(QRectF(5, 9.5, 14, 5), 180 * 16, 180 * 16)


def draw_download(p: QPainter) -> None:
    p.drawLine(QPointF(12, 4), QPointF(12, 15))
    p.drawLine(QPointF(8, 11.5), QPointF(12, 16))
    p.drawLine(QPointF(16, 11.5), QPointF(12, 16))
    p.drawLine(QPointF(5, 19), QPointF(19, 19))


def draw_upload(p: QPainter) -> None:
    p.drawLine(QPointF(12, 16), QPointF(12, 5))
    p.drawLine(QPointF(8, 8.5), QPointF(12, 4))
    p.drawLine(QPointF(16, 8.5), QPointF(12, 4))
    p.drawLine(QPointF(5, 19), QPointF(19, 19))


def draw_eye(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(3, 12)
    path.cubicTo(7, 6.5, 17, 6.5, 21, 12)
    path.cubicTo(17, 17.5, 7, 17.5, 3, 12)
    p.drawPath(path)
    p.drawEllipse(QPointF(12, 12), 2.4, 2.4)


def draw_eye_off(p: QPainter) -> None:
    draw_eye(p)
    p.drawLine(QPointF(5, 19), QPointF(19, 5))


def draw_edit(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(13, 5.5)
    path.lineTo(18.5, 11)
    path.lineTo(8.5, 21)
    path.lineTo(3, 21)
    path.lineTo(3, 15.5)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(11.5, 7), QPointF(17, 12.5))


def draw_delete(p: QPainter) -> None:
    p.drawLine(QPointF(5, 7), QPointF(19, 7))
    p.drawLine(QPointF(9, 7), QPointF(10, 4))
    p.drawLine(QPointF(15, 4), QPointF(14, 7))
    path = QPainterPath()
    path.moveTo(7, 7)
    path.lineTo(8, 20)
    path.lineTo(16, 20)
    path.lineTo(17, 7)
    p.drawPath(path)


def draw_info(p: QPainter) -> None:
    p.drawEllipse(QRectF(4, 4, 16, 16))
    p.drawLine(QPointF(12, 11), QPointF(12, 16.5))
    p.drawPoint(QPointF(12, 8.2))


def draw_check(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(5, 12.5)
    path.lineTo(10, 17.5)
    path.lineTo(19.5, 6.5)
    p.drawPath(path)


def draw_close(p: QPainter) -> None:
    p.drawLine(QPointF(6, 6), QPointF(18, 18))
    p.drawLine(QPointF(18, 6), QPointF(6, 18))


ICONS = {
    "shield": draw_shield,
    "sparkles": draw_sparkles,
    "vault": draw_vault,
    "sun": draw_sun,
    "moon": draw_moon,
    "key": draw_key,
    "book": draw_book,
    "hash": draw_hash,
    "refresh": draw_refresh,
    "copy": draw_copy,
    "save": draw_save,
    "warning": draw_warning,
    "lock": draw_lock,
    "unlock": draw_unlock,
    "lightning": draw_lightning,
    "plus": draw_plus,
    "search": draw_search,
    "database": draw_database,
    "download": draw_download,
    "upload": draw_upload,
    "eye": draw_eye,
    "eye-off": draw_eye_off,
    "edit": draw_edit,
    "delete": draw_delete,
    "info": draw_info,
    "check": draw_check,
    "close": draw_close,
}


def paint_icon(
    painter: QPainter,
    name: str,
    rect: QRectF,
    color: QColor,
    width: float = 1.8,
    rotation: float = 0.0,
) -> None:
    fn = ICONS.get(name)
    if not fn:
        return
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.translate(rect.center())
    if rotation:
        painter.rotate(rotation)
    s = min(rect.width(), rect.height()) / SIZE
    painter.scale(s, s)
    painter.translate(-SIZE / 2, -SIZE / 2)
    painter.setPen(_pen(color, width))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    fn(painter)
    painter.restore()


def icon_pixmap(name: str, size: int, color: QColor, dpr: float = 2.0) -> QPixmap:
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    paint_icon(p, name, QRectF(0, 0, px, px), color)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def brand_pixmap(size: int = 36, dpr: float = 2.0) -> QPixmap:
    """App mark: black tile + orange key (bundled PNG, painted fallback)."""
    import sys
    from pathlib import Path

    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[1]
    src = base / "packaging" / "keygen-icon.png"
    px = max(16, int(size * dpr))
    if src.exists():
        img = QPixmap(str(src))
        if not img.isNull():
            scaled = img.scaled(
                px,
                px,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(dpr)
            return scaled
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = QRectF(1, 1, px - 2, px - 2)
    p.setPen(QColor("#242A32"))
    p.setBrush(QColor("#0B0D10"))
    p.drawRoundedRect(r, px * 0.22, px * 0.22)
    glow = QRadialGradient(r.center(), px * 0.42)
    glow.setColorAt(0.0, QColor(255, 90, 31, 70))
    glow.setColorAt(1.0, QColor(255, 90, 31, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(glow)
    p.drawEllipse(r.adjusted(px * 0.12, px * 0.08, -px * 0.12, -px * 0.08))
    paint_icon(
        p,
        "key",
        r.adjusted(px * 0.18, px * 0.18, -px * 0.18, -px * 0.18),
        QColor("#FF5A1F"),
        2.4,
    )
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm
