# -*- coding: utf-8 -*-
"""
Tema Visual Premium - Telegram Collector Pro v11.0
Design Moderno: Cyberpunk Neon + Frosted Glass
Paleta: Dark base + Cyan/Teal neon + Rose accents
"""

# ===== TEMA DARK PREMIUM - CYBERPUNK NEON =====
DARK_STYLE_PRO = """
/* === Base === */
QMainWindow, QDialog {
    background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
        stop:0 #0a0e1a, stop:0.4 #111827, stop:1 #0f172a);
    color: #f1f5f9;
}

QWidget {
    background-color: transparent;
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Inter', 'SF Pro Display', -apple-system, sans-serif;
    font-size: 13px;
    font-weight: 400;
}

/* === GroupBox - Frosted Glass Cards === */
QGroupBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(15,23,42,0.9), stop:1 rgba(15,23,42,0.7));
    border: 1px solid rgba(6,182,212,0.15);
    border-radius: 20px;
    margin-top: 28px;
    padding: 24px;
    padding-top: 44px;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 24px;
    top: 12px;
    padding: 4px 16px;
    color: #22d3ee;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    background: rgba(6,182,212,0.08);
    border-radius: 8px;
}

/* === Labels === */
QLabel {
    color: #f1f5f9;
    background-color: transparent;
    font-weight: 400;
    line-height: 1.5;
}

/* === Input Fields - Neon Glow === */
QLineEdit, QSpinBox, QComboBox, QTextEdit, QListWidget {
    background: rgba(15,23,42,0.8);
    border: 1.5px solid rgba(6,182,212,0.2);
    border-radius: 14px;
    padding: 12px 18px;
    color: #f1f5f9;
    selection-background-color: #06b6d4;
    selection-color: #0a0e1a;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border: 1.5px solid #06b6d4;
    background: rgba(6,182,212,0.06);
}

QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
    border: 1.5px solid rgba(6,182,212,0.4);
}

QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
    background: rgba(15,23,42,0.4);
    color: #475569;
    border-color: rgba(71,85,105,0.2);
}

QLineEdit::placeholder {
    color: #64748b;
}

/* === ComboBox === */
QComboBox {
    padding-right: 40px;
}

QComboBox::drop-down {
    border: none;
    width: 36px;
    border-top-right-radius: 14px;
    border-bottom-right-radius: 14px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #06b6d4;
    margin-right: 14px;
}

QComboBox QAbstractItemView {
    background: #111827;
    border: 1.5px solid rgba(6,182,212,0.3);
    border-radius: 14px;
    padding: 8px;
    selection-background-color: rgba(6,182,212,0.25);
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 10px 16px;
    border-radius: 10px;
    color: #f1f5f9;
}

QComboBox QAbstractItemView::item:hover {
    background: rgba(6,182,212,0.15);
}

/* === SpinBox === */
QSpinBox::up-button, QSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 26px;
}

QSpinBox::up-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid #06b6d4;
}

QSpinBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #06b6d4;
}

/* === Buttons - Neon Gradient === */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891b2, stop:1 #06b6d4);
    color: #ffffff;
    border: none;
    border-radius: 14px;
    padding: 12px 24px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.3px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #06b6d4, stop:1 #22d3ee);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0e7490, stop:1 #0891b2);
}

QPushButton:disabled {
    background: rgba(71,85,105,0.3);
    color: #475569;
}

/* === Botoes Secundarios === */
QPushButton[secondary="true"] {
    background: rgba(6,182,212,0.08);
    border: 1.5px solid rgba(6,182,212,0.3);
    color: #22d3ee;
}

QPushButton[secondary="true"]:hover {
    background: rgba(6,182,212,0.15);
    border-color: #06b6d4;
}

/* === Botoes de Acao Especiais === */
QPushButton[action="success"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #059669, stop:1 #10b981);
}

QPushButton[action="success"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #10b981, stop:1 #34d399);
}

QPushButton[action="danger"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #dc2626, stop:1 #ef4444);
}

QPushButton[action="danger"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ef4444, stop:1 #f87171);
}

QPushButton[action="warning"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d97706, stop:1 #f59e0b);
}

QPushButton[action="warning"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f59e0b, stop:1 #fbbf24);
}

/* === Table - Moderna Neon === */
QTableWidget {
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(6,182,212,0.12);
    border-radius: 16px;
    gridline-color: rgba(6,182,212,0.06);
    color: #f1f5f9;
    alternate-background-color: rgba(6,182,212,0.03);
}

QTableWidget::item {
    padding: 12px 16px;
    border-bottom: 1px solid rgba(6,182,212,0.06);
}

QTableWidget::item:selected {
    background: rgba(6,182,212,0.2);
    color: #ffffff;
}

QTableWidget::item:hover {
    background: rgba(6,182,212,0.1);
}

QHeaderView::section {
    background: rgba(6,182,212,0.1);
    color: #22d3ee;
    padding: 14px 16px;
    border: none;
    border-bottom: 2px solid rgba(6,182,212,0.25);
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

/* === ScrollBar - Ultra Minimalista === */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 4px 2px;
}

QScrollBar::handle:vertical {
    background: rgba(6,182,212,0.35);
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(6,182,212,0.6);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 2px 4px;
}

QScrollBar::handle:horizontal {
    background: rgba(6,182,212,0.35);
    border-radius: 4px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(6,182,212,0.6);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* === ProgressBar - Neon Animated === */
QProgressBar {
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(6,182,212,0.15);
    border-radius: 10px;
    text-align: center;
    color: #f1f5f9;
    font-size: 11px;
    font-weight: 600;
    height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891b2, stop:0.5 #06b6d4, stop:1 #22d3ee);
    border-radius: 9px;
}

/* === CheckBox - Neon === */
QCheckBox {
    spacing: 12px;
    color: #f1f5f9;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 7px;
    border: 2px solid rgba(6,182,212,0.3);
    background: rgba(15,23,42,0.6);
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0891b2, stop:1 #06b6d4);
    border-color: #06b6d4;
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
}

QCheckBox::indicator:hover {
    border-color: rgba(6,182,212,0.6);
}

/* === RadioButton === */
QRadioButton {
    spacing: 12px;
    color: #f1f5f9;
}

QRadioButton::indicator {
    width: 22px;
    height: 22px;
    border-radius: 11px;
    border: 2px solid rgba(6,182,212,0.3);
    background: rgba(15,23,42,0.6);
}

QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0891b2, stop:1 #06b6d4);
    border-color: #06b6d4;
}

/* === TabWidget - Neon Tabs === */
QTabWidget::pane {
    background: rgba(15,23,42,0.5);
    border: 1px solid rgba(6,182,212,0.12);
    border-radius: 16px;
    padding: 12px;
    margin-top: -1px;
}

QTabBar::tab {
    background: rgba(15,23,42,0.6);
    color: #64748b;
    padding: 12px 22px;
    margin-right: 3px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid transparent;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: rgba(6,182,212,0.12);
    color: #22d3ee;
    border: 1px solid rgba(6,182,212,0.2);
    border-bottom: 3px solid #06b6d4;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background: rgba(6,182,212,0.08);
    color: #94a3b8;
}

/* === StatusBar === */
QStatusBar {
    background: rgba(10,14,26,0.9);
    color: #64748b;
    border-top: 1px solid rgba(6,182,212,0.1);
    padding: 8px 16px;
    font-size: 12px;
}

/* === Menu === */
QMenuBar {
    background: transparent;
    color: #f1f5f9;
    padding: 8px;
}

QMenuBar::item {
    padding: 8px 16px;
    border-radius: 10px;
}

QMenuBar::item:selected {
    background: rgba(6,182,212,0.15);
}

QMenu {
    background: #111827;
    border: 1px solid rgba(6,182,212,0.2);
    border-radius: 14px;
    padding: 8px;
}

QMenu::item {
    padding: 10px 20px;
    border-radius: 10px;
    color: #f1f5f9;
}

QMenu::item:selected {
    background: rgba(6,182,212,0.2);
    color: #22d3ee;
}

/* === MessageBox === */
QMessageBox {
    background: #111827;
}

QMessageBox QLabel {
    color: #f1f5f9;
    font-size: 14px;
}

QMessageBox QPushButton {
    min-width: 100px;
    padding: 10px 24px;
}

/* === ToolTip === */
QToolTip {
    background: #1e293b;
    color: #f1f5f9;
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 12px;
}

/* === Frame para Cards de Dados === */
QFrame[class="data-card"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(6,182,212,0.1), stop:1 rgba(6,182,212,0.03));
    border: 1px solid rgba(6,182,212,0.15);
    border-radius: 16px;
    padding: 16px;
}

QFrame[class="data-card"]:hover {
    border-color: rgba(6,182,212,0.35);
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(6,182,212,0.15), stop:1 rgba(6,182,212,0.06));
}

/* === Splitter === */
QSplitter::handle {
    background: rgba(6,182,212,0.25);
    width: 2px;
    margin: 4px;
    border-radius: 1px;
}

QSplitter::handle:hover {
    background: #06b6d4;
}

/* === TextEdit === */
QTextEdit {
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(6,182,212,0.12);
    border-radius: 14px;
    padding: 14px;
    color: #f1f5f9;
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.6;
}

/* === ListWidget === */
QListWidget {
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(6,182,212,0.12);
    border-radius: 14px;
    padding: 8px;
    outline: none;
}

QListWidget::item {
    padding: 12px 16px;
    border-radius: 10px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: rgba(6,182,212,0.2);
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background: rgba(6,182,212,0.1);
}
"""

# ===== TEMA CLARO PREMIUM =====
LIGHT_STYLE_PRO = """
/* === Base === */
QMainWindow, QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f8fafc, stop:0.5 #f0fdfa, stop:1 #ecfeff);
    color: #0f172a;
}

QWidget {
    background-color: transparent;
    color: #0f172a;
    font-family: 'Segoe UI', 'Inter', 'SF Pro Display', -apple-system, sans-serif;
    font-size: 13px;
}

/* === GroupBox === */
QGroupBox {
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(6,182,212,0.12);
    border-radius: 20px;
    margin-top: 28px;
    padding: 24px;
    padding-top: 44px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 24px;
    top: 12px;
    padding: 4px 16px;
    color: #0891b2;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    background: rgba(6,182,212,0.06);
    border-radius: 8px;
}

/* === Labels === */
QLabel {
    color: #0f172a;
    background-color: transparent;
}

/* === Input Fields === */
QLineEdit, QSpinBox, QComboBox, QTextEdit, QListWidget {
    background: rgba(255,255,255,0.95);
    border: 1.5px solid rgba(6,182,212,0.15);
    border-radius: 14px;
    padding: 12px 18px;
    color: #0f172a;
    selection-background-color: #06b6d4;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border: 1.5px solid #06b6d4;
    background: rgba(6,182,212,0.03);
}

/* === Buttons === */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891b2, stop:1 #06b6d4);
    color: #ffffff;
    border: none;
    border-radius: 14px;
    padding: 12px 24px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #06b6d4, stop:1 #22d3ee);
}

/* === Table === */
QTableWidget {
    background: rgba(255,255,255,0.95);
    border: 1px solid rgba(6,182,212,0.12);
    border-radius: 16px;
    gridline-color: rgba(6,182,212,0.08);
    color: #0f172a;
}

QTableWidget::item:selected {
    background: rgba(6,182,212,0.2);
}

QHeaderView::section {
    background: rgba(6,182,212,0.08);
    color: #0891b2;
    padding: 14px 16px;
    border: none;
    border-bottom: 2px solid rgba(6,182,212,0.15);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

/* === ProgressBar === */
QProgressBar {
    background: rgba(6,182,212,0.08);
    border: none;
    border-radius: 10px;
    height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891b2, stop:1 #06b6d4);
    border-radius: 9px;
}

/* === CheckBox === */
QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 7px;
    border: 2px solid rgba(6,182,212,0.25);
    background: rgba(255,255,255,0.9);
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0891b2, stop:1 #06b6d4);
    border-color: #06b6d4;
}

/* === TabWidget === */
QTabWidget::pane {
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(6,182,212,0.1);
    border-radius: 16px;
}

QTabBar::tab {
    background: rgba(6,182,212,0.04);
    color: #64748b;
    padding: 12px 22px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: rgba(6,182,212,0.1);
    color: #0891b2;
    border-bottom: 3px solid #06b6d4;
    font-weight: 600;
}

/* === StatusBar === */
QStatusBar {
    background: rgba(255,255,255,0.9);
    color: #64748b;
    border-top: 1px solid rgba(6,182,212,0.1);
}

/* === ScrollBar === */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: rgba(6,182,212,0.35);
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(6,182,212,0.55);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# Alias para compatibilidade
DARK_STYLE = DARK_STYLE_PRO
LIGHT_STYLE = LIGHT_STYLE_PRO


def get_theme(theme_name: str = 'dark') -> str:
    """
    Retorna o tema especificado
    
    Args:
        theme_name: Nome do tema ('dark' ou 'light')
    
    Returns:
        String com o stylesheet do tema
    """
    themes = {
        'dark': DARK_STYLE_PRO,
        'light': LIGHT_STYLE_PRO,
        'dark_pro': DARK_STYLE_PRO,
        'light_pro': LIGHT_STYLE_PRO
    }
    return themes.get(theme_name.lower(), DARK_STYLE_PRO)


# Exportar os temas
__all__ = ['DARK_STYLE_PRO', 'LIGHT_STYLE_PRO', 'DARK_STYLE', 'LIGHT_STYLE', 'get_theme']
