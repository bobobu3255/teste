# -*- coding: utf-8 -*-
"""Helpers de movimento e profundidade visual.

QSS do Qt nao suporta box-shadow nem animacoes complexas. Este modulo provee
helpers programaticos para os efeitos de:

- Glow cyan em volta de widgets focados/ativos
- Sombra suave para elevacao de cards e modais
- Fade-in animado em widgets recem-instanciados

Uso:
    from app.ui.app_motion import apply_glow, apply_card_shadow, fade_in

    apply_glow(button)            # glow cyan padrao
    apply_glow(button, "success") # glow verde
    apply_card_shadow(card)       # sombra para profundidade
    fade_in(widget)               # entrada suave
"""
from __future__ import annotations

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QWidget


GLOW_COLORS = {
    "primary": QColor(34, 211, 238, 180),   # cyan brilhante
    "primary_soft": QColor(34, 211, 238, 110),
    "success": QColor(16, 185, 129, 170),
    "warning": QColor(245, 158, 11, 180),
    "danger":  QColor(239, 68, 68, 180),
    "muted":   QColor(125, 211, 252, 90),
}


def apply_glow(widget: QWidget, tone: str = "primary", blur: int = 24) -> QGraphicsDropShadowEffect:
    """Aplica glow colorido em volta de um widget."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    effect.setColor(GLOW_COLORS.get(tone, GLOW_COLORS["primary"]))
    widget.setGraphicsEffect(effect)
    return effect


def apply_card_shadow(widget: QWidget, blur: int = 28, offset_y: int = 8) -> QGraphicsDropShadowEffect:
    """Sombra escura sob o widget para sensacao de elevacao."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(QColor(0, 0, 0, 110))
    widget.setGraphicsEffect(effect)
    return effect


def remove_effect(widget: QWidget) -> None:
    """Remove qualquer QGraphicsEffect aplicado."""
    widget.setGraphicsEffect(None)


def fade_in(widget: QWidget, duration_ms: int = 220) -> QPropertyAnimation:
    """Anima o widget de opacidade 0 -> 1."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    animation.start(QPropertyAnimation.DeleteWhenStopped)
    return animation


def hover_glow_filter(widget: QWidget, tone: str = "primary", blur: int = 18):
    """Instala um event filter que adiciona glow no hover e remove ao sair.

    Retorna o objeto event-filter (mantenha referencia para nao ser GC'd).
    """
    from PyQt5.QtCore import QEvent, QObject

    class _HoverGlow(QObject):
        def __init__(self, target: QWidget) -> None:
            super().__init__(target)
            self._target = target
            self._effect: QGraphicsDropShadowEffect | None = None

        def eventFilter(self, obj, event):  # noqa: N802
            if obj is self._target:
                if event.type() == QEvent.Enter:
                    self._effect = apply_glow(self._target, tone, blur)
                elif event.type() == QEvent.Leave:
                    self._target.setGraphicsEffect(None)
                    self._effect = None
            return False

    flt = _HoverGlow(widget)
    widget.installEventFilter(flt)
    widget.setAttribute(Qt.WA_Hover, True)
    return flt


__all__ = [
    "GLOW_COLORS",
    "apply_glow",
    "apply_card_shadow",
    "remove_effect",
    "fade_in",
    "hover_glow_filter",
]
