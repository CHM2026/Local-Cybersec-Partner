"""Construit l'exécutable Windows portable (PyInstaller ``--onedir`` + ZIP).

Usage local ::

    py -3.15 tools/build_windows.py

Le dossier ``build/win`` contient le travail PyInstaller, ``dist/`` reçoit
l'archive ``CyberSecDashboard-<version>-portable.zip`` prête à être publiée.
Le marqueur ``portable.txt`` est déposé à côté de l'exécutable : l'application
écrira alors ses préférences dans ``settings.ini`` au lieu du registre.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIRNAME = "CyberSecDashboard"
PORTABLE_MARKER = "portable.txt"


def project_version():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--version",
        default=project_version(),
        help="Version utilisée dans le nom de l'archive (défaut : pyproject.toml).",
    )
    parser.add_argument(
        "--keep-work",
        action="store_true",
        help="Conserve le dossier de travail PyInstaller pour diagnostic.",
    )
    return parser.parse_args(argv)


def build(version, keep_work=False):
    """Lance PyInstaller puis crée l'archive ZIP ; renvoie son chemin."""
    sys.path.insert(0, str(ROOT))
    from src.constants import APP_VERSION  # import local : évite PySide6 au démarrage du script

    if version != APP_VERSION:
        raise SystemExit(
            f"Version {version!r} différente de APP_VERSION {APP_VERSION!r} : "
            "alignez pyproject.toml et src/constants.py."
        )

    work = ROOT / "build" / "win"
    shutil.rmtree(work, ignore_errors=True)
    dist = work / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", APP_DIRNAME,
        "--distpath", str(dist),
        "--workpath", str(work / "work"),
        "--specpath", str(work),
        "--add-data", f"{ROOT / 'LICENSE'}{os.pathsep}.",
        str(ROOT / "main.py"),
    ]
    print("[build] PyInstaller --onedir…", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)

    app_dir = dist / APP_DIRNAME
    exe = app_dir / f"{APP_DIRNAME}.exe"
    if not exe.is_file():
        raise SystemExit(f"Exécutable attendu introuvable : {exe}")
    (app_dir / PORTABLE_MARKER).write_text(
        "CyberSec Dashboard — mode portable.\n"
        "Les préférences sont enregistrées dans settings.ini à côté de cet exécutable.\n",
        encoding="utf-8",
    )
    (app_dir / "settings.ini").unlink(missing_ok=True)

    archive = ROOT / "dist" / f"{APP_DIRNAME}-{version}-portable.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    print(f"[build] Compression de {archive.name}…", flush=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as bundle:
        for path in sorted(app_dir.rglob("*")):
            if path.is_file():
                bundle.write(path, Path(APP_DIRNAME) / path.relative_to(app_dir))

    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)
    print(f"[build] Terminé : {archive}", flush=True)
    return archive


if __name__ == "__main__":
    args = parse_args()
    build(args.version, args.keep_work)
