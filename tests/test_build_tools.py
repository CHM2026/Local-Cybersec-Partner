"""Tests des outils locaux de construction des artefacts Windows."""

import hashlib

from src.constants import APP_VERSION
from src.updater import parse_checksums
from tools.build_windows import project_version
from tools.write_sha256sums import expand_paths, sha256_file, write_sums


def test_project_version_matches_app_constant():
    assert project_version() == APP_VERSION


def test_sha256_file_and_sums_format(tmp_path):
    first = tmp_path / "CyberSecDashboard-1.0.0-portable.zip"
    second = tmp_path / "CyberSecDashboard-1.0.0-setup.exe"
    first.write_bytes(b"archive")
    second.write_bytes(b"installateur")

    assert sha256_file(first) == hashlib.sha256(b"archive").hexdigest()

    output = write_sums([first, second], tmp_path / "SHA256SUMS.txt")
    parsed = parse_checksums(output.read_text(encoding="utf-8"))
    assert parsed[first.name.lower()] == hashlib.sha256(b"archive").hexdigest()
    assert parsed[second.name.lower()] == hashlib.sha256(b"installateur").hexdigest()


def test_expand_paths_accepts_powershell_literal_wildcards(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.zip").write_bytes(b"a")
    (tmp_path / "b.zip").write_bytes(b"b")

    assert sorted(expand_paths(["*.zip"])) == ["a.zip", "b.zip"]
    assert expand_paths(["introuvable.zip"]) == ["introuvable.zip"]
