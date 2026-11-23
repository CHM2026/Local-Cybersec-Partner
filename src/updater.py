"""Vérification et téléchargement des mises à jour depuis GitHub Releases.

Aucune télémétrie : une seule requête HTTPS vers l'API publique GitHub, et
uniquement quand l'utilisateur clique ou quand le contrôle quotidien est activé.
Le téléchargement n'est jamais automatique : cette module prépare le fichier,
l'interface demande ensuite confirmation avant toute installation.
"""

import hashlib
import json
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

from PySide6.QtCore import QStandardPaths

from src.constants import APP_VERSION
from src.i18n import tr

REPO = "CHM2026/Local-Cybersec-Partner"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
CHECKSUM_FILE = "SHA256SUMS.txt"
USER_AGENT = f"CyberSecDashboard/{APP_VERSION} (+{RELEASES_PAGE})"

API_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 60
CHUNK_SIZE = 64 * 1024
MAX_RELEASE_BYTES = 2 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 600 * 1024 * 1024
MAX_CHECKSUM_BYTES = 1024 * 1024

_VERSION_RE = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]?(alpha|beta|rc|pre|a|b)(\d*))?$",
    re.IGNORECASE,
)
_PRE_STAGES = {"alpha": 0, "a": 0, "beta": 1, "b": 1, "rc": 2, "pre": 2}


class UpdateError(Exception):
    """Erreur présentée telle quelle à l'utilisateur dans l'interface."""


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int = 0


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    title: str
    notes: str
    page_url: str
    published_at: str
    assets: tuple[ReleaseAsset, ...] = ()


def parse_version(text):
    """Convertit ``v1.2.3`` en tuple comparable ; lève ``UpdateError`` sinon."""
    match = _VERSION_RE.match(str(text).strip())
    if match is None:
        raise UpdateError(tr("update.error.version", value=text))
    major, minor, patch, stage, number = match.groups()
    rank = _PRE_STAGES[stage.lower()] if stage else 3
    return (int(major), int(minor), int(patch), rank, int(number or 0))


def is_newer(available, current=APP_VERSION) -> bool:
    """Vrai si ``available`` est strictement supérieur à ``current``."""
    try:
        return parse_version(available) > parse_version(current)
    except UpdateError:
        return False


def _https_url(url):
    if not str(url).startswith("https://"):
        raise UpdateError(tr("update.error.https"))
    return request.Request(str(url), headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    })


def _read_url(url, timeout, max_size):
    """Lit une URL HTTPS en imposant une taille maximale."""
    req = _https_url(url)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = response.read(max_size + 1)
    except error.HTTPError as exc:
        raise UpdateError(tr("update.error.http", code=exc.code)) from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError(tr("update.error.network", error=exc)) from exc
    if len(data) > max_size:
        raise UpdateError(tr("update.error.size"))
    return data


def fetch_latest_release(url=RELEASES_API, timeout=API_TIMEOUT) -> ReleaseInfo:
    """Interroge GitHub et renvoie la dernière Release publique."""
    raw = _read_url(url, timeout, MAX_RELEASE_BYTES)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError(tr("update.error.json")) from exc
    if not isinstance(payload, dict):
        raise UpdateError(tr("update.error.json"))

    tag = str(payload.get("tag_name") or "").strip()
    if not tag:
        raise UpdateError(tr("update.error.json"))
    # Valide le format de version dès la réception : une Release sans tag
    # exploitable ne doit pas afficher de bouton « télécharger ».
    parse_version(tag)

    page_url = str(payload.get("html_url") or RELEASES_PAGE)
    if not page_url.startswith("https://"):
        page_url = RELEASES_PAGE

    assets = []
    for item in payload.get("assets") or []:
        if not isinstance(item, dict):
            continue
        asset_url = str(item.get("browser_download_url") or "")
        if not asset_url.startswith("https://"):
            continue
        assets.append(ReleaseAsset(
            name=str(item.get("name") or Path(asset_url).name),
            url=asset_url,
            size=int(item.get("size") or 0),
        ))

    return ReleaseInfo(
        version=tag.lstrip("vV"),
        tag=tag,
        title=str(payload.get("name") or tag),
        notes=str(payload.get("body") or ""),
        page_url=page_url,
        published_at=str(payload.get("published_at") or "")[:10],
        assets=tuple(assets),
    )


def asset_for_mode(release: ReleaseInfo, mode: str) -> ReleaseAsset | None:
    """Choisit l'artefact attendu selon le mode de distribution."""
    if mode == "portable":
        wanted = lambda name: name.endswith(".zip") and "portable" in name
    elif mode == "installer":
        wanted = lambda name: name.endswith(".exe") and (
            "setup" in name or "installer" in name)
    else:
        return None
    for asset in release.assets:
        if wanted(asset.name.lower()):
            return asset
    return None


def pip_install_command(release: ReleaseInfo) -> str:
    """Commande affichée aux utilisateurs du paquet pip."""
    tag = release.tag if release.tag.lower().startswith("v") else f"v{release.tag}"
    return (f'py -3.15 -m pip install --upgrade '
            f'"git+https://github.com/{REPO}.git@{tag}"')


def parse_checksums(text: str) -> dict[str, str]:
    """Analyse un ``SHA256SUMS.txt`` (format ``digest␠␠nom-de-fichier``)."""
    result = {}
    for line in text.splitlines():
        fields = line.strip().split()
        if len(fields) < 2:
            continue
        digest, name = fields[0], fields[1].lstrip("*")
        if re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            result[Path(name).name.lower()] = digest.lower()
    return result


def checksum_for_asset(release: ReleaseInfo, asset_name: str):
    """Renvoie ``(digest, fichier_present)`` pour un artefact donné."""
    sums = next((a for a in release.assets
                 if a.name.lower() == CHECKSUM_FILE.lower()), None)
    if sums is None:
        return None, False
    text = _read_url(sums.url, API_TIMEOUT, MAX_CHECKSUM_BYTES).decode("utf-8", "replace")
    return parse_checksums(text).get(Path(asset_name).name.lower()), True


def download_asset(asset: ReleaseAsset, destination, *,
                   expected_sha256=None, progress=None, cancelled=None,
                   timeout=DOWNLOAD_TIMEOUT):
    """Télécharge ``asset`` avec reprise de hash, puis vérifie l'empreinte.

    Le fichier est d'abord écrit en ``.part`` : un téléchargement interrompu
    ne laisse jamais un exécutable incomplet portant le nom définitif.
    """
    destination = Path(destination)
    if not asset.url.startswith("https://"):
        raise UpdateError(tr("update.error.https"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    digest = hashlib.sha256()
    done = 0
    total = asset.size or 0

    req = request.Request(asset.url, headers={"User-Agent": USER_AGENT})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            header_total = response.headers.get("Content-Length")
            if header_total and header_total.isdigit():
                total = int(header_total)
            with open(partial, "wb") as handle:
                while True:
                    if cancelled is not None and cancelled():
                        raise UpdateError(tr("update.error.cancelled"))
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    done += len(chunk)
                    if done > MAX_DOWNLOAD_BYTES:
                        raise UpdateError(tr("update.error.size"))
                    handle.write(chunk)
                    digest.update(chunk)
                    if progress is not None:
                        progress(done, total)
    except UpdateError:
        partial.unlink(missing_ok=True)
        raise
    except error.HTTPError as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(tr("update.error.http", code=exc.code)) from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(tr("update.error.network", error=exc)) from exc

    if expected_sha256 and digest.hexdigest().lower() != expected_sha256.lower():
        partial.unlink(missing_ok=True)
        raise UpdateError(tr("update.error.checksum"))
    os.replace(partial, destination)
    return destination


def downloads_dir() -> Path:
    """Dossier Téléchargements de l'utilisateur (pour le .exe d'installation)."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    return Path(location) if location else Path.home() / "Downloads"


def temp_dir() -> Path:
    """Dossier temporaire utilisateur pour l'archive portable."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)
    base = Path(location) if location else Path(os.path.join(os.environ.get("TEMP", "/tmp")))
    target = base / "CyberSecDashboard-updates"
    target.mkdir(parents=True, exist_ok=True)
    return target


def extract_portable_archive(archive, target_dir):
    """Extrait une archive zip en toute sécurité et renvoie ``(dossier, exe)``.

    Refuse les chemins absolus, les lettres de lecteur et les ``..`` pour
    éviter une écriture hors du dossier cible (zip slip).
    """
    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                name = member.filename.replace("\\", "/")
                parts = name.split("/")
                if (name.startswith("/") or ".." in parts
                        or re.match(r"^[A-Za-z]:", name)):
                    raise UpdateError(tr("update.error.extract"))
                destination = (target_dir / name).resolve()
                if destination != target_dir and target_dir not in destination.parents:
                    raise UpdateError(tr("update.error.extract"))
            bundle.extractall(target_dir)
    except zipfile.BadZipFile as exc:
        raise UpdateError(tr("update.error.extract")) from exc

    exe = next((p for p in target_dir.rglob("*")
                if p.is_file() and p.name.lower() == "cybersecdashboard.exe"), None)
    return target_dir, exe
