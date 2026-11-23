"""Génère le fichier ``SHA256SUMS.txt`` joint aux Releases GitHub.

Chaque ligne utilise le format attendu par ``src/updater.py`` ::

    <empreinte hexadécimale>  <nom du fichier>

Usage ::

    py -3.15 tools/write_sha256sums.py dist/*.zip dist/*setup.exe
"""

import argparse
import glob
import hashlib
from pathlib import Path


def sha256_file(path):
    """Calcule l'empreinte SHA-256 d'un fichier par blocs."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expand_paths(paths):
    """Déplie les jokers même quand PowerShell les passe littéralement."""
    expanded = []
    for path in paths:
        expanded.extend(glob.glob(str(path)) or [str(path)])
    return expanded


def write_sums(paths, output):
    """Écrit les empreintes et renvoie le chemin du fichier créé."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{sha256_file(path)}  {Path(path).name}"
             for path in expand_paths(paths)]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", help="Fichiers à vérifier")
    parser.add_argument(
        "--output", default="dist/SHA256SUMS.txt",
        help="Fichier de sortie (défaut : dist/SHA256SUMS.txt).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    result = write_sums(args.files, args.output)
    print(f"[sha256] {result}")
    print(result.read_text(encoding="utf-8"), end="")
