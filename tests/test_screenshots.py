"""Tests de l'outil de génération de captures hors écran."""

from pathlib import Path

import pytest

from tools.screenshots import LANGUAGES, normalize_pages, parse_args


def test_language_order_matches_selector():
    assert LANGUAGES == ("fr", "en", "ar")


def test_normalize_pages_defaults_to_dashboard():
    assert normalize_pages("") == ["dashboard"]


def test_normalize_pages_strips_and_deduplicates():
    assert normalize_pages(" dashboard , scanner , dashboard ") == [
        "dashboard", "scanner",
    ]


def test_normalize_pages_rejects_unknown_page():
    with pytest.raises(SystemExit):
        normalize_pages("page-inexistante")


def test_parse_args_supports_native_and_custom_output():
    args = parse_args(["--native", "--pages", "scanner", "--out", "captures"])
    assert args.native is True
    assert args.pages == "scanner"
    assert args.out == Path("captures")
