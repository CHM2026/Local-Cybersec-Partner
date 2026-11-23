"""Tests du système de mise à jour et du mode portable (sans réseau)."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

import src.runtime as runtime
import src.updater as updater
from src.runtime import (
    app_settings, detect_distribution, setting_flag, settings_path,
)
from src.updater import (
    ReleaseAsset, ReleaseInfo, UpdateError, asset_for_mode,
    checksum_for_asset, download_asset, extract_portable_archive,
    fetch_latest_release, is_newer, parse_checksums, parse_version,
    pip_install_command,
)


def make_release():
    return ReleaseInfo(
        version="1.0.1", tag="v1.0.1", title="v1.0.1",
        notes="Correctifs divers", page_url="https://github.com/CHM2026/Local-Cybersec-Partner/releases/tag/v1.0.1",
        published_at="2026-12-01", assets=(
            ReleaseAsset("CyberSecDashboard-1.0.1-portable.zip", "https://example.org/portable.zip", 8),
            ReleaseAsset("CyberSecDashboard-1.0.1-setup.exe", "https://example.org/setup.exe", 8),
            ReleaseAsset("SHA256SUMS.txt", "https://example.org/SHA256SUMS.txt", 130),
        ),
    )


# ── Détection du mode de distribution ──────────────────────────────────────
def test_detect_distribution_from_argv(monkeypatch, tmp_path):
    exe = tmp_path / "CyberSecDashboard.exe"
    monkeypatch.setattr(sys, "argv", [str(exe)])
    monkeypatch.setattr(runtime, "is_frozen", lambda: False)
    assert detect_distribution() == "pip"

    monkeypatch.setattr(runtime, "is_frozen", lambda: True)
    assert detect_distribution() == "installer"
    (tmp_path / runtime.PORTABLE_MARKER).write_text("", encoding="utf-8")
    assert detect_distribution() == "portable"

    monkeypatch.setattr(sys, "argv", [str(exe), "--installer"])
    assert detect_distribution() == "installer"
    monkeypatch.setattr(sys, "argv", [str(exe), "--portable"])
    assert detect_distribution() == "portable"


def test_portable_settings_are_written_next_to_executable(monkeypatch, tmp_path):
    exe = tmp_path / "CyberSecDashboard.exe"
    monkeypatch.setattr(sys, "argv", [str(exe)])
    settings = app_settings("portable")
    settings.setValue("language", "ar")
    settings.sync()

    assert settings_path() == tmp_path / "settings.ini"
    assert settings_path().is_file()
    assert "ar" in settings_path().read_text(encoding="utf-8")


def test_setting_flag_normalizes_qsettings_values():
    settings = QSettings("CyberSecPartner", "TestCyberSecUpdates")
    settings.setValue("on/off", "true")
    settings.setValue("off/on", "0")
    assert setting_flag(settings, "on/off", False) is True
    assert setting_flag(settings, "off/on", True) is False
    settings.clear()


# ── Versions et artefacts ──────────────────────────────────────────────────
def test_version_comparison():
    assert parse_version("v1.2.3") == (1, 2, 3, 3, 0)
    assert is_newer("v1.0.1", "1.0.0") is True
    assert is_newer("1.0.0", "v1.0.0") is False
    assert is_newer("0.9.9", "1.0.0") is False
    assert is_newer("1.1.0-rc1", "1.0.9") is True
    with pytest.raises(UpdateError):
        parse_version("pas-une-version")


def test_asset_selection_per_mode():
    release = make_release()
    assert asset_for_mode(release, "portable").name.endswith("portable.zip")
    assert asset_for_mode(release, "installer").name.endswith("setup.exe")
    assert asset_for_mode(release, "pip") is None
    assert "v1.0.1" in pip_install_command(release)


def test_parse_checksums():
    text = ("# empreintes\n"
            f"{'a' * 64}  CyberSecDashboard-1.0.1-portable.zip\n"
            f"{'b' * 64} *CyberSecDashboard-1.0.1-setup.exe\n"
            "ligne invalide\n")
    result = parse_checksums(text)
    assert result["cybersecdashboard-1.0.1-portable.zip"] == "a" * 64
    assert result["cybersecdashboard-1.0.1-setup.exe"] == "b" * 64


def test_fetch_latest_release_parses_github_payload(monkeypatch):
    payload = {
        "tag_name": "v1.0.1", "name": "v1.0.1", "body": "Notes",
        "html_url": "https://github.com/CHM2026/Local-Cybersec-Partner/releases/tag/v1.0.1",
        "published_at": "2026-12-01T10:00:00Z",
        "assets": [
            {"name": "CyberSecDashboard-1.0.1-portable.zip",
             "browser_download_url": "https://example.org/portable.zip", "size": 4},
            {"name": "anti", "browser_download_url": "http://example.org/anti.exe"},
        ],
    }
    monkeypatch.setattr(updater, "_read_url", lambda *a, **k: json.dumps(payload).encode())
    release = fetch_latest_release()
    assert release.version == "1.0.1"
    assert release.notes == "Notes"
    assert len(release.assets) == 1  # HTTP refusé
    assert asset_for_mode(release, "portable") is not None


# ── Téléchargement et intégrité ────────────────────────────────────────────
class FakeResponse:
    def __init__(self, data):
        self.data = data
        self.headers = {"Content-Length": str(len(data))}
        self.position = 0

    def read(self, size=-1):
        chunk = self.data[self.position:self.position + size] if size > 0 else self.data[self.position:]
        self.position += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_download_asset_verifies_sha256(monkeypatch, tmp_path):
    payload = b"contenu"
    digest = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(updater.request, "urlopen", lambda *a, **k: FakeResponse(payload))
    asset = ReleaseAsset("portable.zip", "https://example.org/portable.zip", len(payload))
    seen = []
    target = tmp_path / "portable.zip"

    result = download_asset(asset, target, expected_sha256=digest,
                            progress=lambda done, total: seen.append((done, total)))

    assert result == target
    assert target.read_bytes() == payload
    assert seen[-1] == (len(payload), len(payload))
    assert not (tmp_path / "portable.zip.part").exists()

    with pytest.raises(UpdateError):
        download_asset(asset, tmp_path / "mauvais.zip", expected_sha256="0" * 64)
    assert not (tmp_path / "mauvais.zip").exists()
    assert not (tmp_path / "mauvais.zip.part").exists()


def test_download_asset_can_be_cancelled(monkeypatch, tmp_path):
    monkeypatch.setattr(updater.request, "urlopen",
                        lambda *a, **k: FakeResponse(b"abc"))
    asset = ReleaseAsset("setup.exe", "https://example.org/setup.exe", 3)
    with pytest.raises(UpdateError):
        download_asset(asset, tmp_path / "setup.exe", cancelled=lambda: True)
    assert not (tmp_path / "setup.exe").exists()


def test_checksum_for_asset_reads_sums_file(monkeypatch):
    sums = f"{'c' * 64}  CyberSecDashboard-1.0.1-portable.zip\n".encode()
    monkeypatch.setattr(updater, "_read_url", lambda *a, **k: sums)
    digest, available = checksum_for_asset(make_release(), "CyberSecDashboard-1.0.1-portable.zip")
    assert available is True
    assert digest == "c" * 64


def test_extract_archive_is_safe(tmp_path):
    valid = tmp_path / "valid.zip"
    with zipfile.ZipFile(valid, "w") as bundle:
        bundle.writestr("CyberSecDashboard/CyberSecDashboard.exe", b"MZ")
    folder, exe = extract_portable_archive(valid, tmp_path / "sortie")
    assert exe == folder / "CyberSecDashboard" / "CyberSecDashboard.exe"

    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as bundle:
        bundle.writestr("../hors-cible.txt", b"non")
    with pytest.raises(UpdateError):
        extract_portable_archive(evil, tmp_path / "sortie2")
    assert not (tmp_path / "hors-cible.txt").exists()


# ── Interface ──────────────────────────────────────────────────────────────
def test_update_page_exists_and_lists_current_version(window):
    assert "update" in window.pages
    assert "update" in window.nav_buttons
    labels = [lbl.text() for lbl in window.sidebar.findChildren(type(window._label("")))]
    assert any("v1.0.0" in text for text in labels)
    assert not window.update_download_btn.isEnabled()


def test_update_result_updates_page_and_navigation(window):
    release = make_release()
    window._update_mode = "installer"  #Simulation d'un exécutable installé
    window._on_update_checked(release, "")
    assert window._update_available is True
    assert window.nav_buttons["update"].text().endswith("•")
    assert "1.0.1" in window.update_version_lbl.text()
    assert window.update_download_btn.isEnabled()
    assert "Correctifs divers" in window.update_notes.toPlainText()
    assert any(e["action"] == "log.update.check" for e in window.log_entries)


def test_auto_check_preference_is_persisted(window):
    window.update_auto_cb.setChecked(False)
    assert setting_flag(window._settings, "update.auto_check") is False
    window.update_auto_cb.setChecked(True)
    assert setting_flag(window._settings, "update.auto_check") is True
