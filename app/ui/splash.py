# -*- coding: utf-8 -*-
"""Splash screen do Telegram Collector Pro.

Tela de carregamento minimalista exibida durante o bootstrap do app.
Renderiza o logo hexagonal cyberpunk, titulo e barra de progresso animada.

Uso:
    from PyQt5.QtWidgets import QApplication
    from app.ui.splash import LaunchSplash

    app = QApplication([])
    splash = LaunchSplash()
    splash.show()
    app.processEvents()

    # ... bootstrap pesado ...
    splash.set_message("Carregando features...", 60)

    # quando a janela principal estiver pronta:
    splash.finish_after(window)
"""
from __future__ import annotations

from PyQt5.QtCore import (
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QEasingCurve,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSplashScreen,
    QVBoxLayout,
    QWidget,
)

from app.ui.components import FONT_MONO, FONT_UI, PALETTE


def _draw_logo_hex(size: int = 120) -> QPixmap:
    """Renderiza o logo hexagonal TC programaticamente."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)

    cx = cy = size / 2
    outer_r = size * 0.42
    inner_r = size * 0.30

    def hexagon(radius: float) -> QPolygonF:
        from math import cos, pi, sin
        points = []
        for i in range(6):
            angle = pi / 2 + i * pi / 3  # apontando para cima
            points.append(QPointF(cx + radius * cos(angle), cy - radius * sin(angle)))
        return QPolygonF(points)

    # outer hex com gradiente cyan
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(34, 211, 238))
    grad.setColorAt(1, QColor(6, 182, 212))
    pen = QPen(QBrush(grad), 3.5)
    pen.setJoinStyle(Qt.MiterJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawPolygon(hexagon(outer_r))

    # inner hex preenchido
    painter.setPen(QPen(QColor(34, 211, 238, 140), 1.2))
    painter.setBrush(QColor(10, 14, 26))
    painter.drawPolygon(hexagon(inner_r))

    # corner dots
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(34, 211, 238))
    for angle_idx in range(6):
        from math import cos, pi, sin
        angle = pi / 2 + angle_idx * pi / 3
        x = cx + outer_r * cos(angle)
        y = cy - outer_r * sin(angle)
        painter.drawEllipse(QPointF(x, y), 3.2, 3.2)

    # TC monogram
    painter.setPen(QColor(34, 211, 238))
    font = QFont("Segoe UI", int(size * 0.22))
    font.setBold(True)
    painter.setFont(font)
    rect = QRectF(0, 0, size, size)
    painter.drawText(rect, Qt.AlignCenter, "TC")

    painter.end()
    return pm


def _build_canvas(width: int = 480, height: int = 280) -> QPixmap:
    """Canvas escuro cyberpunk para o splash."""
    pm = QPixmap(width, height)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)

    # background gradient
    grad = QLinearGradient(0, 0, width, height)
    grad.setColorAt(0, QColor(10, 14, 26))
    grad.setColorAt(1, QColor(17, 24, 39))
    painter.fillRect(0, 0, width, height, grad)

    # subtle grid pattern
    painter.setPen(QPen(QColor(6, 182, 212, 18), 1))
    step = 28
    for x in range(0, width, step):
        painter.drawLine(x, 0, x, height)
    for y in range(0, height, step):
        painter.drawLine(0, y, width, y)

    # accent corner brackets
    painter.setPen(QPen(QColor(34, 211, 238, 200), 2))
    bracket = 18
    margin = 14
    # top-left
    painter.drawLine(margin, margin, margin + bracket, margin)
    painter.drawLine(margin, margin, margin, margin + bracket)
    # top-right
    painter.drawLine(width - margin - bracket, margin, width - margin, margin)
    painter.drawLine(width - margin, margin, width - margin, margin + bracket)
    # bottom-left
    painter.drawLine(margin, height - margin, margin + bracket, height - margin)
    painter.drawLine(margin, height - margin - bracket, margin, height - margin)
    # bottom-right
    painter.drawLine(width - margin - bracket, height - margin, width - margin, height - margin)
    painter.drawLine(width - margin, height - margin - bracket, width - margin, height - margin)

    # top accent line
    accent = QLinearGradient(0, 0, width, 0)
    accent.setColorAt(0, QColor(6, 182, 212, 0))
    accent.setColorAt(0.5, QColor(34, 211, 238, 220))
    accent.setColorAt(1, QColor(6, 182, 212, 0))
    painter.fillRect(0, 0, width, 2, accent)
    painter.fillRect(0, height - 2, width, 2, accent)

    painter.end()
    return pm


class LaunchSplash(QSplashScreen):
    """Splash screen com logo, titulo e mensagem de carregamento."""

    def __init__(self, app_name: str = "Telegram Collector Pro", version: str = "v12.0") -> None:
        canvas = _build_canvas(480, 280)
        super().__init__(canvas, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._app_name = app_name
        self._version = version
        self._build_overlay()

    # ----------------------------------------------------------------
    def _build_overlay(self) -> None:
        overlay = QWidget(self)
        overlay.setStyleSheet("background: transparent;")
        overlay.setGeometry(0, 0, self.width(), self.height())

        root = QVBoxLayout(overlay)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(10)

        # eyebrow
        eyebrow = QLabel("\u25CE  CYBERPUNK \u00B7 EDITION")
        eyebrow.setStyleSheet(
            f"color:{PALETTE.primary_light}; font-family:{FONT_MONO};"
            f"font-size:10px; font-weight:700; letter-spacing:3px; background:transparent;"
        )
        root.addWidget(eyebrow)

        # logo + title row
        head = QHBoxLayout()
        head.setSpacing(14)

        logo = QLabel()
        logo_pm = _draw_logo_hex(72)
        logo.setPixmap(logo_pm)
        logo.setFixedSize(QSize(72, 72))
        # glow on logo
        glow = QGraphicsDropShadowEffect(logo)
        glow.setBlurRadius(28)
        glow.setOffset(0, 0)
        glow.setColor(QColor(34, 211, 238, 170))
        logo.setGraphicsEffect(glow)
        head.addWidget(logo)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel(self._app_name.upper())
        title.setStyleSheet(
            f"color:#f1f5f9; font-family:{FONT_UI}; font-size:22px; font-weight:800;"
            f"background:transparent; letter-spacing:-0.5px;"
        )
        sub = QLabel(f"Suite desktop  \u00B7  {self._version}")
        sub.setStyleSheet(
            f"color:{PALETTE.muted}; font-family:{FONT_UI}; font-size:12px; background:transparent;"
        )
        text_col.addWidget(title)
        text_col.addWidget(sub)
        text_col.addStretch(1)
        head.addLayout(text_col, 1)
        root.addLayout(head)

        root.addStretch(1)

        # message
        self._message = QLabel("Inicializando...")
        self._message.setStyleSheet(
            f"color:{PALETTE.primary_light}; font-family:{FONT_MONO}; font-size:11px;"
            f"font-weight:600; background:transparent; letter-spacing:0.5px;"
        )
        root.addWidget(self._message)

        # progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(
            f"""
            QProgressBar {{
                background: rgba(15,23,42,0.8);
                border: 1px solid {PALETTE.border};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PALETTE.primary},
                    stop:1 {PALETTE.primary_light}
                );
                border-radius: 2px;
            }}
            """
        )
        root.addWidget(self._progress)

        # smooth progress animation
        self._anim = QPropertyAnimation(self._progress, b"value", self)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    # ----------------------------------------------------------------
    def set_message(self, message: str, progress: int | None = None) -> None:
        """Atualiza a mensagem e (opcionalmente) a barra de progresso."""
        self._message.setText(message)
        if progress is not None:
            self._anim.stop()
            self._anim.setStartValue(self._progress.value())
            self._anim.setEndValue(max(0, min(progress, 100)))
            self._anim.start()
        self.repaint()

    def finish_after(self, window, delay_ms: int = 200) -> None:
        """Fecha o splash apos um pequeno delay e exibe a janela principal."""
        QTimer.singleShot(delay_ms, lambda: self.finish(window))


__all__ = ["LaunchSplash"]
