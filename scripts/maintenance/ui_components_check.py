#!/usr/bin/env python3
"""Verifica se o kit visual compartilhado cria widgets sem erro."""
from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def configure_path() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    for path in (ROOT / "venv" / "Lib" / "site-packages", ROOT):
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)


def main() -> int:
    configure_path()
    from PyQt5.QtWidgets import QApplication
    from app.ui.components import make_button, make_card, make_combo, make_label, make_line_edit, make_section, make_text_area

    app = QApplication.instance() or QApplication([])
    created = [
        make_button("Primario"),
        make_button("Perigo", role="danger"),
        make_label("Titulo", "title"),
        make_line_edit("placeholder"),
        make_text_area("texto"),
        make_combo(["A", "B"]),
        make_card()[0],
        make_section("Secao", "Descricao curta")[0],
    ]
    for widget in created:
        widget.deleteLater()
    app.processEvents()
    print("[ui] Componentes visuais OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
