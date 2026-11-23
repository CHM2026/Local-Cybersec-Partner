"""Mode de distribution et réglages de CyberSec Dashboard.

Trois modes sont possibles :

``pip``
    Installation classique (wheel ou dépôt). Les préférences vont dans le
    registre Windows / équivalent macOS-Linux via ``QSettings``.
``installer``
    Exécutable PyInstaller installé par Inno Setup : mêmes réglages que ``pip``.
``portable``
    Archive PyInstaller accompagnée d'un fichier ``portable.txt`` (ou lancée
    avec ``--portable``) : les préférences sont écrites dans ``settings.ini``
    à côté de l'exécutable, sans toucher au registre.

Ce module est la seule source de vérité pour ces décisions : ``main.py`` et
les tests n'ont plus à manipuler directement ``QSettings("CyberSecPartner", …)``.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QSettings

ORGANIZATION = "CyberSecPartner"
APPLICATION = "CyberSecDashboard"
PORTABLE_MARKER = "portable.txt"
SETTINGS_FILENAME = "settings.ini"


def is_frozen() -> bool:
    """Vrai quand le code tourne dans un exécutable PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def executable_dir() -> Path:
    """Dossier de l'exécutable (ou du script source) en cours."""
    argv0 = sys.argv[0] if sys.argv else ""
    return Path(argv0).resolve().parent


def detect_distribution(argv=None) -> str:
    """Renvoie ``portable``, ``installer`` ou ``pip``.

    ``--portable`` et ``--installer`` servent de surcharge explicite, utile
    pour les tests et pour dépanner sans renommer le fichier marqueur.
    """
    args = list(sys.argv if argv is None else argv)
    if "--portable" in args:
        return "portable"
    if "--installer" in args:
        return "installer"
    if not is_frozen():
        return "pip"
    return "portable" if (executable_dir() / PORTABLE_MARKER).is_file() else "installer"


def settings_path() -> Path:
    """Emplacement de ``settings.ini`` en mode portable."""
    return executable_dir() / SETTINGS_FILENAME


def app_settings(mode=None) -> QSettings:
    """Renvoie le ``QSettings`` adapté au mode de distribution courant."""
    if (mode or detect_distribution()) == "portable":
        return QSettings(str(settings_path()), QSettings.Format.IniFormat)
    return QSettings(ORGANIZATION, APPLICATION)


def setting_flag(settings, key, default=True) -> bool:
    """Lit un booléen ``QSettings`` quelle que soit sa représentation.

    Selon les plateformes, une valeur enregistrée comme booléen peut revenir
    sous forme de chaîne (« true », « 1 »…) ; on normalise ici.
    """
    value = settings.value(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def distribution_i18n_key(mode=None) -> str:
    """Clé i18n correspondant au mode courant (pour l'écran « Mise à jour »)."""
    return {
        "portable": "update.mode.portable",
        "installer": "update.mode.installer",
        "pip": "update.mode.pip",
    }.get(mode or detect_distribution(), "update.mode.pip")
