"""Tests de l'outil de génération de captures hors écran."""

import platform
import socket
from pathlib import Path

import pytest

from tools.screenshots import (
    DEMO_HOSTNAME, DEMO_NODE, DEMO_PROCESSOR, LANGUAGES,
    anonymized_system_info, normalize_pages, parse_args,
)


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
    assert args.theme == "both"


def test_parse_args_theme_choice():
    args = parse_args(["--theme", "light"])
    assert args.theme == "light"


def test_parse_args_real_data_opt_out():
    assert parse_args([]).real_data is False
    assert parse_args(["--real-data"]).real_data is True


def test_anonymized_system_info_hides_and_restores_identifiers():
    original = (platform.node(), platform.processor(), socket.gethostname())

    with anonymized_system_info():
        assert platform.node() == DEMO_NODE
        assert platform.processor() == DEMO_PROCESSOR
        assert socket.gethostname() == DEMO_HOSTNAME

    assert (platform.node(), platform.processor(), socket.gethostname()) == original
