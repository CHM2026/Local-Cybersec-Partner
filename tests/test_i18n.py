"""Tests du module multilingue (français / anglais / arabe) et du RTL."""

import pytest
from PySide6.QtCore import QCoreApplication, Qt, QSettings
from PySide6.QtWidgets import QApplication

from src.i18n import I18N, LANGUAGES, STRINGS, install_qt_translator, tr


@pytest.fixture(autouse=True)
def restore_language():
    """Évite qu'un test laisse l'application dans une autre langue."""
    previous = I18N.language
    yield
    I18N.set_language(previous)
    QSettings("CyberSecPartner", "CyberSecDashboard").setValue("language", previous)


def test_all_strings_have_three_translations():
    assert len(LANGUAGES) == 3
    assert set(STRINGS) == set(STRINGS)
    for key, values in STRINGS.items():
        assert len(values) == 3, key
        assert all(isinstance(value, str) and value.strip() for value in values), key


def test_missing_key_is_returned_as_is():
    assert tr("cle.inexistante") == "cle.inexistante"


def test_translation_with_parameters():
    I18N.set_language("en")
    assert tr("scanner.count", count=3) == "3 open port(s)"


def test_navigation_is_translated(window):
    I18N.set_language("fr")
    window.lang_combo.setCurrentIndex(0)
    assert window.nav_buttons["dashboard"].text() == "⬡  Tableau de Bord"

    window.lang_combo.setCurrentIndex(1)
    assert window.nav_buttons["dashboard"].text() == "⬡  Dashboard"

    window.lang_combo.setCurrentIndex(2)
    assert window.nav_buttons["dashboard"].text() == "⬡  لوحة التحكم"


def test_rtl_layout_follows_language(window):
    window.lang_combo.setCurrentIndex(1)
    assert window.centralWidget().layoutDirection() == Qt.LayoutDirection.LeftToRight
    window.lang_combo.setCurrentIndex(2)
    assert window.centralWidget().layoutDirection() == Qt.LayoutDirection.RightToLeft
    window.lang_combo.setCurrentIndex(0)
    assert window.centralWidget().layoutDirection() == Qt.LayoutDirection.LeftToRight


def test_language_is_persisted(window):
    window.lang_combo.setCurrentIndex(1)
    settings = QSettings("CyberSecPartner", "CyberSecDashboard")
    assert settings.value("language") == "en"


def test_log_entries_are_retranslated(window):
    window._log_action("log.scan", "log.scan.done", host="8.8.8.8", count=2)
    window.lang_combo.setCurrentIndex(0)
    action, details = window._log_entry_text(window.log_entries[0])
    assert "Scan Ports" in action
    assert "port(s) ouvert(s)" in details

    window.lang_combo.setCurrentIndex(1)
    action, details = window._log_entry_text(window.log_entries[0])
    assert "Port scan" in action
    assert "open port(s)" in details


def test_user_input_survives_language_change(window):
    window.str_entry.setText("Motdepasse123!")
    window.hash_input.setPlainText("secret")
    window.dns_entry.setText("exemple.fr")

    window.lang_combo.setCurrentIndex(1)

    assert window.str_entry.text() == "Motdepasse123!"
    assert window.hash_input.toPlainText() == "secret"
    assert window.dns_entry.text() == "exemple.fr"
    assert len(window._hashes_data) == 5


def test_rebuild_does_not_duplicate_logs(window):
    window._log_action("log.scan", "log.scan.done", host="8.8.8.8", count=2)
    window.lang_combo.setCurrentIndex(1)
    window.lang_combo.setCurrentIndex(2)
    assert len(window.log_entries) == 1


def test_qt_translator_arabic_from_default_path(qapp):
    """Les catalogues Qt sont chargés depuis QLibraryInfo.TranslationsPath."""
    try:
        assert install_qt_translator("ar") is True
        assert QCoreApplication.translate("QDialogButtonBox", "OK") != "OK"
    finally:
        install_qt_translator("fr")


def test_qt_translator_english_removes_previous(qapp):
    install_qt_translator("ar")
    assert install_qt_translator("en") is False
    assert QCoreApplication.translate("QDialogButtonBox", "OK") == "OK"


def test_language_change_installs_qt_translator(window):
    try:
        window.lang_combo.setCurrentIndex(2)  # ar
        assert QCoreApplication.translate("QDialogButtonBox", "OK") != "OK"
    finally:
        window.lang_combo.setCurrentIndex(0)  # fr
