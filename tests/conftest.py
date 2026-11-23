"""Fixtures pytest pour l'interface Qt (mode offscreen, sans fenêtre visible)."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from src.constants import current_theme, set_theme
from src.i18n import I18N


@pytest.fixture(autouse=True)
def stable_language():
    """Garantit un départ en français pour chaque test, quel que soit l'état QSettings."""
    previous = I18N.language
    I18N.set_language("fr")
    QSettings("CyberSecPartner", "CyberSecDashboard").setValue("language", "fr")
    yield
    I18N.set_language(previous)
    QSettings("CyberSecPartner", "CyberSecDashboard").setValue("language", previous)


@pytest.fixture(autouse=True)
def restore_theme():
    """Évite qu'un test laisse l'application dans un autre thème."""
    previous = current_theme()
    yield
    set_theme(previous)
    QSettings("CyberSecPartner", "CyberSecDashboard").setValue("theme", previous)


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
