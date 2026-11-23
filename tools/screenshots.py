"""Génère des captures PNG de l'application, avec ou sans fenêtre visible.

Par défaut, le mode Qt ``offscreen`` est utilisé : le script fonctionne partout,
y compris en CI, mais les emoji y sont rendus en monochrome.

Avec ``--native``, la plateforme graphique du système est utilisée afin
d'obtenir les emoji en couleur. Un affichage est alors nécessaire.

Les identifiants de la machine (nom d'hôte, processeur) sont remplacés par
des valeurs factices : les captures peuvent donc être publiées sans exposer
d'informations personnelles. ``--real-data`` désactive cette anonymisation.

Exemples :
    python tools/screenshots.py
    python tools/screenshots.py --native
    python tools/screenshots.py --native --pages dashboard,scanner
    python tools/screenshots.py --native --theme light
"""

import argparse
import os
import platform
import socket
import sys
from contextlib import contextmanager, nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LANGUAGES = ("fr", "en", "ar")
THEMES = ("dark", "light")
DEMO_NODE = "DEMO-PC"
DEMO_PROCESSOR = "Synthetic CPU (demo)"
DEMO_HOSTNAME = "demo.local"
PAGES = (
    "dashboard", "passwords", "strength", "hashing", "files",
    "scanner", "base64", "network", "update", "logs",
)


def parse_args(argv=None):
    description = next(iter((__doc__ or "").splitlines()), "")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--pages", default="dashboard",
        help="Pages à capturer, séparées par des virgules (défaut : dashboard).",
    )
    parser.add_argument(
        "--out", default="docs/screenshots", type=Path,
        help="Dossier de sortie (défaut : docs/screenshots).",
    )
    parser.add_argument(
        "--theme", choices=(*THEMES, "both"), default="both",
        help="Thème à capturer (défaut : both).",
    )
    parser.add_argument(
        "--native", action="store_true",
        help="Utiliser la plateforme graphique système (emoji en couleur).",
    )
    parser.add_argument(
        "--real-data", action="store_true",
        help="Afficher les vrais identifiants machine (déconseillé pour la doc).",
    )
    return parser.parse_args(argv)


@contextmanager
def anonymized_system_info():
    """Remplace temporairement les identifiants machine par des valeurs factices."""
    attributes = (
        (platform, "node", lambda: DEMO_NODE),
        (platform, "processor", lambda: DEMO_PROCESSOR),
        (socket, "gethostname", lambda: DEMO_HOSTNAME),
    )
    originals = [(module, name, getattr(module, name)) for module, name, _ in attributes]
    for module, name, fake in attributes:
        setattr(module, name, fake)
    try:
        yield
    finally:
        for module, name, value in originals:
            setattr(module, name, value)


def configure_platform(native=False):
    """Choisit la plateforme Qt avant tout import PySide6."""
    if native:
        if sys.platform == "win32":
            os.environ["QT_QPA_PLATFORM"] = "windows"
        elif sys.platform == "darwin":
            os.environ["QT_QPA_PLATFORM"] = "cocoa"
        elif os.environ.get("WAYLAND_DISPLAY"):
            os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
        elif os.environ.get("DISPLAY"):
            os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
        else:
            raise SystemExit(
                "Aucun affichage détecté : retirez --native pour le mode offscreen."
            )
    else:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def normalize_pages(raw):
    """Valide et déduplique la liste de pages demandée sur la ligne de commande."""
    pages = []
    for item in raw.split(","):
        page = item.strip()
        if page and page not in pages:
            pages.append(page)
    unknown = [page for page in pages if page not in PAGES]
    if unknown:
        raise SystemExit(f"Page(s) inconnue(s) : {', '.join(unknown)}")
    return pages or ["dashboard"]


def capture_page(app, window, page, lang, theme, out_dir):
    """Reconstruit l'UI dans ``lang``/``theme`` puis enregistre ``page`` en PNG."""
    from src.constants import set_theme
    from src.i18n import I18N

    window.lang_combo.blockSignals(True)
    window.lang_combo.setCurrentIndex(LANGUAGES.index(lang))
    window.lang_combo.blockSignals(False)
    window.theme_combo.blockSignals(True)
    window.theme_combo.setCurrentIndex(THEMES.index(theme))
    window.theme_combo.blockSignals(False)
    I18N.set_language(lang)
    set_theme(theme)
    window._rebuild_ui(page)
    app.processEvents()

    target = out_dir / f"{page}-{lang}-{theme}.png"
    if not window.grab().save(str(target), "PNG"):
        raise RuntimeError(f"Capture impossible : {target}")
    try:
        shown = target.relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(target)
    print(shown)


def main(argv=None):
    args = parse_args(argv)
    pages = normalize_pages(args.pages)
    out_dir = args.out if args.out.is_absolute() else ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    configure_platform(args.native)

    # Imports Qt différés : la plateforme doit être choisie avant ceux-ci.
    from PySide6.QtWidgets import QApplication
    from main import CyberSecApp

    context = nullcontext() if args.real_data else anonymized_system_info()
    with context:
        app = QApplication.instance() or QApplication([])
        window = CyberSecApp()
        window.resize(1280, 820)
        window.show()
        app.processEvents()
        themes = THEMES if args.theme == "both" else (args.theme,)
        try:
            for page in pages:
                for lang in LANGUAGES:
                    for theme in themes:
                        capture_page(app, window, page, lang, theme, out_dir)
        finally:
            window._shutdown()
            window.hide()
            window.deleteLater()
            app.processEvents()


if __name__ == "__main__":
    main()
