#!/usr/bin/env python3
"""Estilos compartilhados das telas Crunchyroll."""


def cr_lighten_color(hex_color, factor=0.2):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def cr_darken_color(hex_color, factor=0.2):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def cr_group_qss():
    return """
        QGroupBox {
            font-size: 14px;
            font-weight: bold;
            color: #06b6d4;
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """


def cr_subtle_group_qss():
    return """
        QGroupBox {
            font-size: 12px;
            color: #94a3b8;
            border: 1px solid rgba(6,182,212,0.10);
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
        }
    """


def cr_button_qss(color="#059669"):
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            font-size: 13px;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
            border: none;
        }}
        QPushButton:hover {{ background-color: {cr_lighten_color(color)}; }}
        QPushButton:pressed {{ background-color: {cr_darken_color(color)}; }}
        QPushButton:disabled {{ background-color: #1e293b; color: #64748b; }}
    """


def cr_small_button_qss(danger=False):
    hover = "#da3633; color: white" if danger else "rgba(6,182,212,0.15)"
    return f"""
        QPushButton {{
            background-color: #1e293b;
            color: #94a3b8;
            padding: 4px 12px;
            border-radius: 4px;
            border: 1px solid rgba(6,182,212,0.15);
            font-size: 11px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
    """


def cr_header_qss():
    return """
        QLabel {
            font-size: 24px;
            font-weight: bold;
            color: #06b6d4;
            padding: 10px;
        }
    """


def cr_description_qss():
    return "font-size: 12px; color: #94a3b8; padding: 5px;"


def cr_label_qss(color="#94a3b8", size=12, padding=5, bold=False):
    weight = "font-weight: bold; " if bold else ""
    return f"font-size: {size}px; {weight}color: {color}; padding: {padding}px;"


def cr_status_qss(color="#94a3b8", size=14):
    return f"font-size: {size}px; font-weight: bold; color: {color};"


def cr_dependency_status_qss(installed=None):
    if installed is True:
        color = "#10b981"
    elif installed is False:
        color = "#f43f5e"
    else:
        color = "#94a3b8"
    return f"font-size: 13px; color: {color}; padding: 5px;"


def cr_stat_qss(color="#94a3b8"):
    return f"font-size: 14px; font-weight: bold; color: {color}; padding: 10px;"


def cr_tabs_qss(variant="solid"):
    if variant == "compact":
        return """
            QTabWidget::pane { border: 1px solid rgba(6,182,212,0.12); border-radius: 8px; }
            QTabBar::tab { background: #111827; color: #94a3b8; padding: 8px 14px; border-radius: 6px; margin: 2px; }
            QTabBar::tab:selected { background: #083344; color: #67e8f9; }
        """
    if variant == "quiet":
        return """
            QTabWidget::pane {
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 8px;
                background: #0a0e1a;
            }
            QTabBar::tab {
                background: #1e293b;
                color: #94a3b8;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #0a0e1a;
                color: #06b6d4;
            }
        """
    return """
        QTabWidget::pane {
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 8px;
            background: #111827;
        }
        QTabBar::tab {
            background: #1e293b;
            color: #94a3b8;
            padding: 10px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #06b6d4;
            color: white;
        }
        QTabBar::tab:hover:!selected {
            background: rgba(6,182,212,0.15);
        }
    """


def cr_checkbox_qss(size=13, color="#f1f5f9", indicator=18):
    return f"""
        QCheckBox {{
            font-size: {size}px;
            color: {color};
            padding: 5px;
        }}
        QCheckBox::indicator {{
            width: {indicator}px;
            height: {indicator}px;
        }}
        QCheckBox::indicator:unchecked {{
            background-color: #1e293b;
            border: 2px solid rgba(6,182,212,0.15);
            border-radius: 4px;
        }}
        QCheckBox::indicator:checked {{
            background-color: #059669;
            border: 2px solid #059669;
            border-radius: 4px;
        }}
    """


def cr_spinbox_qss():
    return """
        QSpinBox {
            background-color: #1e293b;
            color: #f1f5f9;
            font-size: 14px;
            font-weight: bold;
            padding: 8px 15px;
            border: 2px solid rgba(6,182,212,0.15);
            border-radius: 6px;
            min-width: 80px;
        }
        QSpinBox:hover { border-color: #06b6d4; }
    """


def cr_line_edit_qss(min_width=80):
    return f"""
        QLineEdit {{
            background-color: #1e293b;
            color: #f1f5f9;
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 6px;
            padding: 6px;
            min-width: {min_width}px;
        }}
        QLineEdit:focus {{ border-color: #06b6d4; }}
        QLineEdit:disabled {{ background-color: #111827; color: #6e7681; }}
    """


def cr_text_edit_qss(color="#f1f5f9", border="rgba(6,182,212,0.15)", size=12):
    return f"""
        QTextEdit {{
            background-color: #0a0e1a;
            color: {color};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: {size}px;
            border: 1px solid {border};
            border-radius: 8px;
            padding: 10px;
        }}
    """


def cr_console_qss():
    return """
        QTextEdit {
            background-color: #0a0e1a;
            color: #f1f5f9;
            font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 8px;
            padding: 10px;
            line-height: 1.4;
        }
        QScrollBar:vertical {
            background-color: #0a0e1a;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background-color: rgba(6,182,212,0.15);
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background-color: #484f58; }
    """


def cr_combo_qss():
    return """
        QComboBox {
            background-color: #1e293b;
            color: #f1f5f9;
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 4px;
            padding: 4px 8px;
            min-width: 100px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background-color: #1e293b;
            color: #f1f5f9;
            selection-background-color: #06b6d4;
        }
    """


def cr_info_box_qss():
    return """
        QLabel {
            background: #071827;
            color: #93c5fd;
            border: 1px solid rgba(56,189,248,0.24);
            border-radius: 10px;
            padding: 10px;
        }
    """


def cr_scroll_area_qss():
    return "QScrollArea { border: none; background: transparent; }"


def cr_compact_label_qss(color="#94a3b8", bold=False):
    weight = " font-weight: bold;" if bold else ""
    return f"color: {color}; padding: 4px;{weight}"


def cr_mono_value_qss(color="#22d3ee"):
    return f"color: {color}; font-family: monospace;"
