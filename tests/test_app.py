"""Tests de non-régression sur les corrections prioritaires."""

import hashlib

from PySide6.QtWidgets import QMessageBox

from main import CyberSecApp, FileHashWorker, PortScanWorker
from src.constants import APP_VERSION


def test_version_label_uses_pyside6(window):
    labels = [lbl.text() for lbl in window.sidebar.findChildren(type(window._label("")))]
    assert any(f"v{APP_VERSION}" in t and "PySide6" in t for t in labels)


def test_hash_keeps_surrounding_spaces(window):
    window.hash_input.setPlainText("  secret  ")
    window._compute_hashes()
    assert window._hashes_data["SHA-256"] == hashlib.sha256(b"  secret  ").hexdigest()


def test_base64_encode_preserves_payload(window):
    window.b64_input.setPlainText("abc\n")
    window._b64_encode()
    assert window.b64_output.toPlainText() == "YWJjCg=="


def test_base64_rejects_invalid_and_clears_stale_result(window):
    window.b64_input.setPlainText("abc")
    window._b64_decode()
    window.b64_input.setPlainText("@@@aGVsbG8=")
    window._b64_decode()
    assert "invalides" in window.b64_status.text()
    assert window.b64_output.toPlainText() == ""


def test_base64_binary_is_displayed_as_hex(window):
    window.b64_input.setPlainText("/w==")
    window._b64_decode()
    assert "ff" in window.b64_output.toPlainText().lower()


def test_host_validation(window):
    assert window._valid_host("8.8.8.8")
    assert window._valid_host("exemple.fr")
    assert not window._valid_host("-n")
    assert not window._valid_host("")
    assert not window._valid_host("host name")


def test_timeout_out_of_range_is_rejected(window, monkeypatch):
    messages = []
    monkeypatch.setattr(QMessageBox, "critical",
                        lambda *args, **kwargs: messages.append(args[-1]))
    window.scan_entries["timeout"].setText("0")
    window._start_scan()
    assert any("Timeout invalide" in m for m in messages)


def test_invalid_scan_host_reports_error():
    errors, results = [], []
    worker = PortScanWorker("host-inexistant.invalid", 1, 3, 0.05)
    worker.error.connect(errors.append)
    worker.finished_scan.connect(results.append)
    worker.run()
    assert errors and results == [0]


def test_file_hash_worker(tmp_path):
    target = tmp_path / "sample.bin"
    target.write_bytes(b"contenu de test")
    results, errors = [], []
    worker = FileHashWorker(str(target), "SHA-256")
    worker.finished_hash.connect(lambda a, d, s: results.append((a, d, s)))
    worker.error.connect(errors.append)
    worker.run()
    assert not errors
    assert results[0][1] == hashlib.sha256(b"contenu de test").hexdigest()


def test_digest_invalidated_when_algorithm_changes(window, tmp_path):
    target = tmp_path / "sample.bin"
    target.write_bytes(b"abc")
    window.file_path_edit.setText(str(target))
    window._on_file_hash_done("SHA-256", "a" * 64, 3)
    assert window._current_file_hash
    window.file_algo.setCurrentText("SHA-1")
    assert window._current_file_hash == ""
    assert not window.file_algo_warn.isHidden()


def test_strength_logged_once(window):
    before = len(window.log_entries)
    for ch in "motdepasse":
        window.str_entry.setText(ch)
    assert len(window.log_entries) == before
    window._log_strength()
    assert len(window.log_entries) == before + 1


def test_sensitive_data_is_wiped(window):
    window.str_entry.setText("secretmdp")
    window.hash_input.setPlainText("texte secret")
    window.b64_input.setPlainText("Y29uZmlkZW50aWVs")
    window.expected_hash.setText("hashref")
    window.scan_output.setPlainText("donnees privees")
    window._log_action("Test", "details")
    window._set_clipboard("valeur de l'application")
    window._wipe_sensitive_data()

    assert window.str_entry.text() == ""
    assert window.hash_input.toPlainText() == ""
    assert window.b64_input.toPlainText() == ""
    assert window.expected_hash.text() == ""
    assert window.scan_output.toPlainText() == ""
    assert not window.log_entries
    assert not window._hashes_data
    assert not window._current_file_hash
    assert not window._clipboard_owned
