"""Fixtures pytest pour l'interface Qt (mode offscreen, sans fenêtre visible)."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp):
    from main import CyberSecApp

    win = CyberSecApp()
    yield win
    # Nettoyage sans passer par closeEvent() : aucun dialogue de confirmation.
    win._shutdown()
    win.hide()
    win.deleteLater()
