"""
╔══════════════════════════════════════════════════════════╗
║         CyberSec Dashboard — Outil de Sécurité           ║
║         Édition PySide6                                  ║
╚══════════════════════════════════════════════════════════╝

Lancement : python main.py
"""
lazy import sys, hashlib, string, socket, base64
lazy import os, platform, subprocess, re, secrets, hmac
lazy from html import escape as _esc
lazy from datetime import datetime
lazy from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSlider,
    QProgressBar, QFileDialog, QMessageBox, QStackedWidget, QFrame, QScrollArea,
    QButtonGroup,
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSettings, QUrl
from PySide6.QtGui import QFont, QCursor, QClipboard, QDesktopServices
from PySide6.QtNetwork import QHostInfo, QNetworkInterface, QAbstractSocket

from src.constants import (
    PALETTE, THEMES, APP_NAME, APP_VERSION, COMMON_PORTS,
    current_theme, set_theme,
)
from src.i18n import I18N, LANGUAGES, STRINGS, tr
from src.runtime import (
    app_settings, detect_distribution, distribution_i18n_key,
    executable_dir, setting_flag,
)
from src.updater import (
    RELEASES_PAGE, ReleaseInfo, UpdateError, asset_for_mode, checksum_for_asset,
    download_asset, downloads_dir, extract_portable_archive,
    fetch_latest_release, is_newer, pip_install_command, temp_dir,
)


def _new_hash(algo):
    """Construit un objet hashlib pour un algo donné, y compris en mode FIPS.

    ``usedforsecurity=False`` autorise MD5/SHA-1 pour des contrôles d'intégrité
    non sécuritaires et évite un ValueError sur les systèmes FIPS.
    """
    return hashlib.new(algo.lower().replace("-", ""), usedforsecurity=False)


def _text_on(color):
    """Choix du texte lisible sur un fond (évite les valeurs figées par thème)."""
    raw = color.lstrip("#")
    if len(raw) != 6:
        return "#ffffff"
    r, g, b = (int(raw[i:i + 2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0f172a" if luminance > 0.62 else "#ffffff"


# ════════════════════════════════════════════════════════════
#  THREADS DE TRAVAIL (remplacent les threads daemon Tkinter)
# ════════════════════════════════════════════════════════════
class PortScanWorker(QThread):
    """Scanne une plage de ports TCP sur un hôte, sans bloquer l'UI."""

    port_found    = Signal(int, str)   # port, service
    progress      = Signal(int, int)   # scannés, total
    finished_scan = Signal(int)        # nombre de ports ouverts
    error         = Signal(str)        # erreur bloquante (ex. hôte invalide)

    def __init__(self, host, port_start, port_end, timeout):
        super().__init__()
        self.host = host
        # Nommés port_start/port_end (et non start/end) pour ne pas écraser
        # la méthode start() héritée de QThread : self.start = start
        # transformerait l'appel self._scan_worker.start() en appel d'un int.
        self.port_start = port_start
        self.port_end = port_end
        self.timeout = timeout
        self._running = True
        self._socket = None

    def stop(self):
        """Demande l'arrêt et ferme le socket en cours pour ne pas attendre le timeout."""
        self._running = False
        sock = self._socket
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

    def run(self):
        # Résolution DNS dans le thread de travail : un hôte invalide remonte
        # une erreur explicite au lieu d'un silencieux « 0 port ouvert ».
        try:
            target = socket.gethostbyname(self.host)
        except Exception as exc:
            self.error.emit(tr("scanner.error", host=self.host, error=exc))
            self.finished_scan.emit(0)
            return

        total = self.port_end - self.port_start + 1
        open_count = 0
        last_pct = -1
        for i, port in enumerate(range(self.port_start, self.port_end + 1)):
            if not self._running:
                break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    self._socket = s
                    s.settimeout(self.timeout)
                    if s.connect_ex((target, port)) == 0:
                        open_count += 1
                        svc = COMMON_PORTS.get(port, tr("common.unknown"))
                        self.port_found.emit(port, svc)
            except Exception:
                pass
            finally:
                self._socket = None
            # Un signal par port inonderait la boucle Qt sur les grandes plages.
            pct = int((i + 1) * 100 / total)
            if pct != last_pct:
                self.progress.emit(i + 1, total)
                last_pct = pct
        self.finished_scan.emit(open_count)


class PingWorker(QThread):
    """Exécute un ping système vers un hôte, sans bloquer l'UI."""

    finished_ping = Signal(bool, str)  # succès, message d'erreur

    def __init__(self, host):
        super().__init__()
        self.host = host

    def run(self):
        windows = platform.system().lower() == "windows"
        param = "-n" if windows else "-c"
        # La sortie du ping n'est pas affichée. On la redirige vers DEVNULL :
        # avec capture_output + text=True, Python la décode dans un thread
        # interne et échoue sous Windows quand elle utilise la page de code
        # OEM (UnicodeDecodeError), même si le ping réussit.
        # Les arguments sont explicites (pas de **kwargs) pour que Pylance
        # puisse choisir la bonne surcharge de subprocess.run().
        command = ["ping", param, "4", self.host]
        try:
            if windows:
                # Évite l'ouverture d'une console fugace quand l'app est lancée
                # via pythonw / un raccourci sans fenêtre.
                r = subprocess.run(
                    command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=12,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            else:
                r = subprocess.run(
                    command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=12,
                )
            self.finished_ping.emit(r.returncode == 0, "")
        except Exception as e:
            self.finished_ping.emit(False, str(e))


class UpdateCheckWorker(QThread):
    """Interroge l'API GitHub en arrière-plan, sans figer l'interface."""

    finished_check = Signal(object, str)  # ReleaseInfo | None, message d'erreur

    def __init__(self, current_version=APP_VERSION):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            release = fetch_latest_release()
            if release is not None and is_newer(release.version, self.current_version):
                self.finished_check.emit(release, "")
            else:
                self.finished_check.emit(None, "")
        except UpdateError as exc:
            self.finished_check.emit(None, str(exc))
        except Exception as exc:  # garde-fou : toujours répondre à l'interface
            self.finished_check.emit(None, str(exc))


class UpdateDownloadWorker(QThread):
    """Télécharge et vérifie un artefact, avec progression et annulation."""

    progress = Signal(int, int)                 # octets reçus, octets attendus
    finished_download = Signal(str, str, str)   # chemin, erreur, état checksum

    def __init__(self, release, mode, destination):
        super().__init__()
        self.release = release
        self.mode = mode
        self.destination = Path(destination)
        self._cancelled = False

    def stop(self):
        self._cancelled = True

    def run(self):
        try:
            asset = asset_for_mode(self.release, self.mode)
            if asset is None:
                raise UpdateError(tr("update.error.asset"))
            digest, _sums_available = checksum_for_asset(self.release, asset.name)
            state = "verified" if digest else "unverified"
            path = download_asset(
                asset, self.destination, expected_sha256=digest,
                progress=lambda done, total: self.progress.emit(done, total),
                cancelled=lambda: self._cancelled,
            )
            self.finished_download.emit(str(path), "", state)
        except Exception as exc:
            self.finished_download.emit("", str(exc), "error")


class FileHashWorker(QThread):
    """Calcule l'empreinte d'un fichier par blocs, sans bloquer l'UI."""

    finished_hash = Signal(str, str, int)  # algo, hexdigest, octets lus
    progress      = Signal(int, int)       # octets lus, taille totale
    error         = Signal(str)

    def __init__(self, path, algo):
        super().__init__()
        self.path = path
        self.algo = algo
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            digest = _new_hash(self.algo)
            total = os.path.getsize(self.path)
            done = 0
            last_pct = -1
            with open(self.path, "rb") as fobj:
                for chunk in iter(lambda: fobj.read(65536), b""):
                    if not self._running:
                        return
                    digest.update(chunk)
                    done += len(chunk)
                    if total:
                        pct = int(done * 100 / total)
                        if pct != last_pct:
                            self.progress.emit(done, total)
                            last_pct = pct
            self.finished_hash.emit(self.algo, digest.hexdigest(), done)
        except Exception as exc:
            self.error.emit(str(exc))


class ClickableFrame(QFrame):
    """QFrame cliquable — utilisé pour les cartes de modules du tableau de bord.

    Peut afficher un petit badge de priorité (ex. « Priorité 1 · Haute ») dans
    le coin supérieur droit de la carte, utilisé par le tableau de bord pour
    présenter les modules suggérés par ordre de priorité.
    """

    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_priority_badge(self, text, color):
        """Ajoute (ou remplace) un badge de priorité positionné en haut à droite."""
        if getattr(self, "_priority_badge", None) is not None:
            self._priority_badge.deleteLater()
        badge = QLabel(text, self)
        badge.setFont(QFont(PALETTE["font_family"], 7, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            background-color:{color}; color:{PALETTE["bg"]};
            border-radius:8px; padding:2px 7px;
        """)
        badge.adjustSize()
        badge.move(self.width() - badge.width() - 8, 8)
        badge.show()
        badge.raise_()
        self._priority_badge = badge  # référence conservée pour éviter le garbage collection
        return badge
# ════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ════════════════════════════════════════════════════════════
class CyberSecApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🛡️  {APP_NAME}")
        self.resize(1150, 740)
        self.setMinimumSize(920, 620)
        self.setStyleSheet(f"background-color:{PALETTE["bg"]};")

        # — État applicatif —
        self.log_entries        = []
        self.current_page       = None
        self._hashes_data       = {}
        self._current_file_hash = ""
        self._scanning          = False
        self._open_ports        = 0
        self._scan_worker       = None   # référence au QThread du scanner
        self._ping_worker       = None   # référence au QThread du ping
        self._file_worker       = None   # référence au QThread du hash de fichier
        self._scan_aborted      = False  # arrêt manuel du scan
        self._scan_error        = ""     # dernière erreur bloquante du scan
        self._clipboard_owned   = False  # vrai si l'app a écrit dans le presse-papiers
        self._last_strength     = None   # résumé du dernier score calculé
        self._closing           = False  # anti-fermetures concurrentes
        self._clock_labels      = []     # horloges affichées sur chaque page
        # — Mises à jour —
        self._update_mode       = detect_distribution()
        self._release: ReleaseInfo | None = None  # dernière Release compatible
        self._update_available  = False
        self._update_status: tuple[str, str] = ("", "")  # (kind, détail) i18n
        self._update_worker: UpdateCheckWorker | None = None
        self._download_worker: UpdateDownloadWorker | None = None

        self._settings = app_settings()
        saved_language = self._settings.value("language", "fr")
        I18N.set_language(saved_language if saved_language in LANGUAGES else "fr")
        saved_theme = self._settings.value("theme", "dark")
        set_theme(saved_theme if saved_theme in THEMES else "dark")
        apply_global_style(QApplication.instance())
        self.setStyleSheet(f"background-color:{PALETTE["bg"]};")

        self.pages = {}
        self._build_ui()
        self._show_page("dashboard")

        # Horloge : remplace le after(1000, ...) récursif de Tkinter par un
        # QTimer, que l'on peut arrêter proprement à la fermeture.
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._refresh_date)
        self._clock_timer.start(1000)
        self._refresh_date()

        self._center_window()

        # Contrôle quotidien silencieux : une seule requête, différée pour ne
        # pas retarder l'affichage de la fenêtre.
        if (setting_flag(self._settings, "update.auto_check", True)
                and self._settings.value("update.last_check", "")
                != datetime.now().strftime("%Y-%m-%d")):
            QTimer.singleShot(1500, self._auto_check_updates)

    # ────────────────────────────────────────────────────────
    # HELPERS UI
    # ────────────────────────────────────────────────────────
    def _label(self, text, size=10, bold=False, color=None, family=None):
        color = PALETTE["text"] if color is None else color
        family = PALETTE["font_family"] if family is None else family
        lbl = QLabel(text)
        f = QFont(family, size)
        f.setBold(bold)
        lbl.setFont(f)
        lbl.setStyleSheet(f"color:{color}; background: transparent;")
        return lbl

    def _btn(self, text, slot, color=None, fg=None):
        color = PALETTE["accent"] if color is None else color
        fg = _text_on(color) if fg is None else fg
        b = QPushButton(text)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        f = QFont(PALETTE["font_family"], 10)
        f.setBold(True)
        b.setFont(f)
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: {fg}; border: none;
                padding: 7px 14px; border-radius: 4px;
            }}
            QPushButton:disabled {{ background-color: {PALETTE["border"]}; color: {PALETTE["dim"]}; }}
        """)
        b.clicked.connect(slot)
        return b

    def _btn2(self, text, slot):
        b = QPushButton(text)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b.setFont(QFont(PALETTE["font_family"], 10))
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE["border"]}; color: {PALETTE["text"]}; border: none;
                padding: 7px 12px; border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {PALETTE["hover"]}; }}
            QPushButton:disabled {{ background-color: {PALETTE["sidebar"]}; color: {PALETTE["dim"]}; }}
        """)
        b.clicked.connect(slot)
        return b

    def _card(self, parent_layout, title=None):
        """Crée une carte stylée et l'ajoute à parent_layout ; renvoie son layout interne."""
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color:{PALETTE["card"]}; border:1px solid {PALETTE["border"]}; border-radius:6px; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        if title:
            layout.addWidget(self._label(title, size=11, bold=True, color=PALETTE["accent2"]))
        parent_layout.addWidget(frame)
        return layout

    def _page_header(self, layout, icon, title, subtitle):
        top = QHBoxLayout()
        top.addWidget(self._label(f"{icon}  {title}", size=17, bold=True, color=PALETTE["accent"]))
        top.addStretch()
        clock = self._label("", size=9, color=PALETTE["dim"])
        self._clock_labels.append(clock)
        top.addWidget(clock)
        layout.addLayout(top)
        sub = self._label(subtitle, size=9, color=PALETTE["dim"])
        sub.setWordWrap(True)
        layout.addWidget(sub)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color:{PALETTE["border"]};")
        layout.addWidget(line)

    def _new_page(self, pid):
        """Crée une page défilable, l'enregistre dans self.pages, renvoie son layout de contenu."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color:{PALETTE["bg"]}; border:none; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background-color:{PALETTE["bg"]};")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(25, 14, 25, 16)
        layout.setSpacing(8)
        scroll.setWidget(inner)
        #if scroll and hasattr(scroll,"viewport"):
        sc = scroll.viewport()
        if isinstance(sc, QWidget):
            sc.setStyleSheet(f"background-color:{PALETTE["bg"]};")
        self.stack.addWidget(scroll)
        self.pages[pid] = scroll
        return layout

    def _clear_layout(self, layout):
        """Supprime récursivement widgets et sous-layouts d'un layout."""
        while layout.count():
            item = layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.deleteLater()
                continue
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)
                child_layout.deleteLater()

    @staticmethod
    def _valid_host(host):
        """Valide une IP ou un nom d'hôte avant de le passer à une commande système.

        Refuse notamment les valeurs commençant par ``-`` qui seraient
        interprétées comme des options par ``ping``.
        """
        return bool(host) and len(host) <= 253 and bool(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?", host))

    def _set_clipboard(self, text):
        """Écrit dans le presse-papiers et mémorise que l'app en est l'auteur."""
        clipboard = QApplication.clipboard()
        if isinstance(clipboard, QClipboard):
            clipboard.setText(text)
        self._clipboard_owned = True

    # ────────────────────────────────────────────────────────
    # INTERFACE PRINCIPALE (sidebar + contenu)
    # ────────────────────────────────────────────────────────
    def _build_ui(self):
        self._clock_labels = []
        central = QWidget()
        central.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if I18N.language == "ar"
            else Qt.LayoutDirection.LeftToRight)
        central.setStyleSheet(f"background-color:{PALETTE["bg"]};")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # — Sidebar —
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(230)
        self.sidebar.setStyleSheet(f"background-color:{PALETTE["sidebar"]};")
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        logo = QWidget()
        logo_l = QVBoxLayout(logo)
        logo_l.setContentsMargins(0, 22, 0, 22)
        logo_l.setSpacing(2)
        icon_lbl = self._label("🛡️", size=28, color=PALETTE["accent"])
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl = self._label("CyberSec", size=15, bold=True, color=PALETTE["accent"])
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl = self._label("Dashboard", size=9, color=PALETTE["dim"])
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_l.addWidget(icon_lbl)
        logo_l.addWidget(name_lbl)
        logo_l.addWidget(sub_lbl)
        sb.addWidget(logo)

        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background-color:{PALETTE["border"]};")
        sb.addWidget(line)

        nav_items = [
            ("dashboard", tr("nav.dashboard")),
            ("passwords", tr("nav.passwords")),
            ("strength",  tr("nav.strength")),
            ("hashing",   tr("nav.hashing")),
            ("files",     tr("nav.files")),
            ("scanner",   tr("nav.scanner")),
            ("base64",    tr("nav.base64")),
            ("network",   tr("nav.network")),
            ("update",    tr("nav.update")),
            ("logs",      tr("nav.logs")),
            ("quit",      tr("nav.quit")),
        ]
        self.nav_buttons = {}
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for pid, label in nav_items:
            btn = QPushButton(label)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFont(QFont(PALETTE["font_family"], 10))

            if pid == "quit":
                # Bouton spécial : ne correspond à aucune page et ne doit donc
                # ni être "checkable", ni rejoindre le groupe exclusif de nav.
                # Un clic déclenche self.close(), qui passe par closeEvent()
                # (confirmation si un scan est en cours, purge des données, etc.).
                btn.setCheckable(False)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color:{PALETTE["sidebar"]}; color:{PALETTE["warning"]}; border:none;
                        text-align:start; padding:10px 20px;
                    }}
                    QPushButton:hover {{ background-color:{PALETTE["card"]}; color:{PALETTE["danger"]}; }}
                """)
                btn.clicked.connect(self.close)
                sb.addWidget(btn)
                continue

            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color:{PALETTE["sidebar"]}; color:{PALETTE["dim"]}; border:none;
                    text-align:left; padding:10px 20px;
                }}
                QPushButton:hover {{ background-color:{PALETTE["card"]}; color:{PALETTE["accent"]}; }}
                QPushButton:checked {{ background-color:{PALETTE["card"]}; color:{PALETTE["accent"]}; }}
            """)
            btn.clicked.connect(lambda checked, p=pid: self._show_page(p))
            sb.addWidget(btn)
            self.nav_group.addButton(btn)
            self.nav_buttons[pid] = btn

        sb.addStretch()

        # — Selecteur de langue —
        lang_row = QHBoxLayout()
        lang_row.setContentsMargins(14, 4, 14, 2)
        lang_row.addWidget(self._label(tr("nav.language"), size=9, color=PALETTE["dim"]))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([LANGUAGES[c] for c in ("fr", "en", "ar")])
        self.lang_combo.setCurrentIndex(("fr", "en", "ar").index(I18N.language))
        self.lang_combo.setStyleSheet(f"""
            QComboBox {{ background-color:{PALETTE["card"]}; color:{PALETTE["accent"]};
                         border:1px solid {PALETTE["border"]}; border-radius:4px;
                         padding:3px 6px; font-size:10px; }}
        """)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.lang_combo)
        sb.addLayout(lang_row)

        # — Sélecteur de thème —
        theme_row = QHBoxLayout()
        theme_row.setContentsMargins(14, 4, 14, 2)
        theme_row.addWidget(self._label(tr("nav.theme"), size=9, color=PALETTE["dim"]))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([tr("theme.dark"), tr("theme.light")])
        self.theme_combo.setCurrentIndex(("dark", "light").index(current_theme()))
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{ background-color:{PALETTE["card"]}; color:{PALETTE["accent"]};
                         border:1px solid {PALETTE["border"]}; border-radius:4px;
                         padding:3px 6px; font-size:10px; }}
        """)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo)
        sb.addLayout(theme_row)

        # — Bouton de capture (PNG de la fenêtre courante) —
        self.capture_btn = QPushButton(tr("nav.capture"))
        self.capture_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.capture_btn.setFont(QFont(PALETTE["font_family"], 10))
        self.capture_btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{PALETTE["sidebar"]}; color:{PALETTE["accent"]};
                border:none; text-align:start; padding:10px 20px;
            }}
            QPushButton:hover {{ background-color:{PALETTE["card"]}; color:{PALETTE["accent2"]}; }}
        """)
        self.capture_btn.clicked.connect(self._capture_screenshot)
        sb.addWidget(self.capture_btn)

        line2 = QFrame(); line2.setFixedHeight(1); line2.setStyleSheet(f"background-color:{PALETTE["border"]};")
        sb.addWidget(line2)
        ver = self._label(f"v{APP_VERSION} (PySide6){tr('app.suffix')}", size=9, color=PALETTE["dim"])
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setContentsMargins(0, 8, 0, 8)
        sb.addWidget(ver)

        main_layout.addWidget(self.sidebar)

        # — Zone contenu —
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color:{PALETTE["bg"]};")
        main_layout.addWidget(self.stack, 1)

        self._build_all_pages()
        if self._update_available:
            nav = self.nav_buttons.get("update")
            if nav is not None:
                nav.setText(f"{tr('nav.update')}  •")

    # ────────────────────────────────────────────────────────
    # NAVIGATION
    # ────────────────────────────────────────────────────────
    def _show_page(self, page_id):
        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)
        if page_id in self.pages:
            self.stack.setCurrentWidget(self.pages[page_id])
        self.current_page = page_id
        if page_id == "logs":
            self._refresh_logs()

    # ────────────────────────────────────────────────────────
    # MULTILINGUE (FR / EN / AR)
    # ────────────────────────────────────────────────────────
    def _on_language_changed(self, index):
        """Appelé par le sélecteur de langue de la sidebar."""
        codes = ("fr", "en", "ar")
        if not (0 <= index < len(codes)):
            return
        code = codes[index]
        if code == I18N.language:
            return
        I18N.set_language(code)
        self._settings.setValue("language", code)
        self._rebuild_ui(self.current_page or "dashboard")

    def _on_theme_changed(self, index):
        """Applique un thème et reconstruit l'interface avec la nouvelle palette."""
        codes = ("dark", "light")
        if not (0 <= index < len(codes)):
            return
        code = codes[index]
        if code == current_theme():
            return
        set_theme(code)
        self._settings.setValue("theme", code)
        apply_global_style(QApplication.instance())
        self.setStyleSheet(f"background-color:{PALETTE["bg"]};")
        self._rebuild_ui(self.current_page or "dashboard")

    def _capture_ui_state(self):
        """Conserve les saisies de l'utilisateur avant une reconstruction."""
        def value(name, getter="text"):
            widget = getattr(self, name, None)
            if widget is None:
                return ""
            try:
                return getattr(widget, getter)()
            except Exception:
                return ""

        return {
            "page": self.current_page or "dashboard",
            "strength": value("str_entry"),
            "hash": value("hash_input", "toPlainText"),
            "b64": value("b64_input", "toPlainText"),
            "b64_out": value("b64_output", "toPlainText"),
            "file_path": value("file_path_edit"),
            "file_algo": value("file_algo", "currentText"),
            "reference": value("expected_hash"),
            "dns": value("dns_entry"),
            "ping": value("ping_entry"),
            "scan": {k: w.text() for k, w in
                     getattr(self, "scan_entries", {}).items()},
        }

    def _restore_ui_state(self, state):
        """Restaure les saisies et recalcule les résultats sans journaliser."""
        for key, text in state.get("scan", {}).items():
            widget = getattr(self, "scan_entries", {}).get(key)
            if widget is not None:
                widget.setText(text)
        for name, key in (("file_path_edit", "file_path"),
                          ("expected_hash", "reference"),
                          ("dns_entry", "dns"),
                          ("ping_entry", "ping")):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.setText(state.get(key, ""))
        if state.get("file_algo"):
            algo = getattr(self, "file_algo", None)
            if algo is not None:
                algo.setCurrentText(state["file_algo"])
        if state.get("b64"):
            self.b64_input.setPlainText(state["b64"])
        if state.get("b64_out"):
            self.b64_output.setPlainText(state["b64_out"])
        if state.get("hash"):
            self.hash_input.setPlainText(state["hash"])
            self._compute_hashes(log=False)
        if state.get("strength"):
            self.str_entry.setText(state["strength"])

    def _rebuild_ui(self, page_id):
        """Reconstruit l'interface dans la nouvelle langue (y compris le RTL)."""
        # Les threads actifs doivent être arrêtés avant la destruction des
        # widgets : leurs signaux cibleraient des objets supprimés.
        self._scanning = False
        self._stop_thread(self._scan_worker, 6000)
        self._stop_thread(self._ping_worker, 15000)
        self._stop_thread(self._file_worker, 6000)
        self._stop_thread(self._update_worker, 5000)
        self._stop_thread(self._download_worker, 5000)
        self._clock_timer.stop()

        state = self._capture_ui_state()
        state["page"] = page_id
        old_central = self.centralWidget()

        self._clock_labels = []
        self.pages = {}
        self.nav_buttons = {}
        self._hashes_data = {}
        self._current_file_hash = ""
        self._build_ui()
        self._restore_ui_state(state)
        self._show_page(state["page"])
        self._refresh_date()
        self._clock_timer.start(1000)
        if old_central is not None:
            old_central.deleteLater()

    # ────────────────────────────────────────────────────────
    # DIVERS
    # ────────────────────────────────────────────────────────
    def _log_action(self, action_key, detail_key="", **kwargs):
        """Stocke des cles de traduction : le journal suit la langue courante."""
        now = datetime.now()
        self.log_entries.insert(0, {
            "time":    now.strftime("%H:%M:%S"),
            "date":    now.strftime("%Y-%m-%d"),
            "action":  action_key,
            "details": detail_key,
            "args":    kwargs,
        })
        if len(self.log_entries) > 300:
            self.log_entries = self.log_entries[:300]

    @staticmethod
    def _log_entry_text(entry):
        """Resout une entree du journal dans la langue active."""
        action = entry.get("action", "")
        details = entry.get("details", "")
        args = entry.get("args", {})
        return (tr(action) if action in STRINGS else action,
                tr(details, **args) if details in STRINGS else details)

    def _capture_screenshot(self):
        """Enregistre la fenêtre courante en PNG, sans dépendance externe."""
        default_name = f"{APP_NAME.lower().replace(' ', '-')}-{I18N.language}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, tr("capture.dialog_title"), default_name, tr("capture.filter"))
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if self.grab().save(path, "PNG"):
            self._log_action("log.capture", "log.capture.done",
                             file=_esc(os.path.basename(path)))
        else:
            QMessageBox.warning(self, tr("capture.dialog_title"), tr("capture.error"))

    def _refresh_date(self):
        now_str = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        for lbl in self._clock_labels:
            lbl.setText(now_str)

    def _center_window(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(geo.center())
        self.move(frame.topLeft())

    # ════════════════════════════════════════════════════════
    #  CONSTRUCTION DE TOUTES LES PAGES
    # ════════════════════════════════════════════════════════
    def _build_all_pages(self):
        self._build_dashboard()
        self._build_passwords()
        self._build_strength()
        self._build_hashing()
        self._build_files()
        self._build_scanner()
        self._build_base64()
        self._build_network()
        self._build_update()
        self._build_logs()

    # ════════════════════════════════════════════════════════
    #  PAGE : TABLEAU DE BORD
    # ════════════════════════════════════════════════════════
    def _build_dashboard(self):
        layout = self._new_page("dashboard")
        self._page_header(layout, "⬡", tr("page.dashboard.title"),
                           tr("page.dashboard.subtitle"))

        c = self._card(layout)
        c.addWidget(self._label(tr("dashboard.welcome"), size=13, bold=True))
        desc = self._label(tr("dashboard.description"),
                           size=9, color=PALETTE["dim"])
        desc.setWordWrap(True)
        c.addWidget(desc)

        sc = self._card(layout, tr("dashboard.system"))
        sys_data = [
            (tr("dashboard.os"), f"{platform.system()} {platform.release()}"),
            (tr("dashboard.architecture"),           platform.machine()),
            (tr("dashboard.processor"),             (platform.processor() or tr("common.na"))[:60]),
            (tr("dashboard.machine"),      platform.node()),
            (tr("dashboard.python"),         platform.python_version()),
        ]
        for lbl, val in sys_data:
            row = QHBoxLayout()
            l1 = self._label(f"  {lbl} :", size=9, color=PALETTE["dim"]); l1.setFixedWidth(220)
            l2 = self._label(val, size=10, color=PALETTE["accent"], family=PALETTE["font_mono"])
            row.addWidget(l1); row.addWidget(l2); row.addStretch()
            sc.addLayout(row)

        layout.addWidget(self._label(tr("dashboard.modules"), size=14, bold=True))

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(8)
        # Chaque module porte un rang de priorité (1 = à traiter en premier) et un
        # badge (texte, couleur) affiché sur la carte via ClickableFrame.set_priority_badge().
        # Rang basé sur l'urgence sécurité : détecter l'exposition réseau et renforcer
        # les mots de passe d'abord ; les utilitaires (Base64, Hachage brut) en dernier.
        modules = [
            ("🔍", tr("dashboard.module.scanner"),  tr("dashboard.module.scanner.desc"),       "scanner",   PALETTE["danger"],  1, tr("priority.badge", num=1, level=tr("priority.high")),   PALETTE["danger"]),
            ("🔑", tr("dashboard.module.passwords"), tr("dashboard.module.passwords.desc"),  "passwords", PALETTE["accent"],  2, tr("priority.badge", num=2, level=tr("priority.high")),   PALETTE["danger"]),
            ("💪", tr("dashboard.module.strength"),      tr("dashboard.module.strength.desc"), "strength",  PALETTE["accent2"], 3, tr("priority.badge", num=3, level=tr("priority.medium")), PALETTE["warning"]),
            ("📄", tr("dashboard.module.files"),      tr("dashboard.module.files.desc"), "files",     PALETTE["warning"], 4, tr("priority.badge", num=4, level=tr("priority.medium")), PALETTE["warning"]),
            ("🔒", tr("dashboard.module.hashing"),        tr("dashboard.module.hashing.desc"),            "hashing",   PALETTE["purple"],  5, tr("priority.badge", num=5, level=tr("priority.low")),   PALETTE["dim"]),
            ("⚙️", tr("dashboard.module.base64"), tr("dashboard.module.base64.desc"),  "base64",    PALETTE["success"], 6, tr("priority.badge", num=6, level=tr("priority.low")),   PALETTE["dim"]),
        ]
        modules_par_priorite = sorted(modules, key=lambda m: m[5])
        for i, (icon, name, desc_txt, pid, color, priority, badge_txt, badge_color) in enumerate(modules_par_priorite):
            card = ClickableFrame()
            card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            card.setFixedSize(220, 110)
            card.setStyleSheet(
                f"QFrame {{ background-color:{PALETTE["card"]}; border:1px solid {PALETTE["border"]}; border-radius:6px; }}")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 12, 14, 12)
            cl.addWidget(self._label(icon, size=20, color=color))
            cl.addWidget(self._label(name, size=11, bold=True))
            d = self._label(desc_txt.replace("\n", " "), size=9, color=PALETTE["dim"])
            d.setWordWrap(True)
            cl.addWidget(d)
            card.set_priority_badge(badge_txt, badge_color)
            card.clicked.connect(lambda checked=False, p=pid: self._show_page(p))
            grid.addWidget(card, i // 3, i % 3)
        layout.addWidget(grid_w)
        layout.addStretch()

    # ════════════════════════════════════════════════════════
    #  PAGE : GÉNÉRATEUR DE MOTS DE PASSE
    # ════════════════════════════════════════════════════════
    def _build_passwords(self):
        layout = self._new_page("passwords")
        self._page_header(layout, "🔑", tr("page.passwords.title"),
                           tr("page.passwords.subtitle"))

        oc = self._card(layout)
        oc.addWidget(self._label(tr("passwords.config"), size=11, bold=True, color=PALETTE["accent2"]))

        lf = QHBoxLayout()
        lf.addWidget(self._label(tr("passwords.length"), size=10))
        lf.addStretch()
        self.pwd_len_lbl = self._label("16", size=12, bold=True, color=PALETTE["accent"])
        lf.addWidget(self.pwd_len_lbl)
        oc.addLayout(lf)

        self.pwd_length_slider = QSlider(Qt.Orientation.Horizontal)
        self.pwd_length_slider.setRange(6, 64)
        self.pwd_length_slider.setValue(16)
        self.pwd_length_slider.valueChanged.connect(lambda v: self.pwd_len_lbl.setText(str(v)))
        self.pwd_length_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background:{PALETTE["sidebar"]}; height:6px; border-radius:3px; }}
            QSlider::handle:horizontal {{ background:{PALETTE["accent"]}; width:14px; margin:-5px 0; border-radius:7px; }}
        """)
        oc.addWidget(self.pwd_length_slider)

        self.use_upper   = QCheckBox(tr("passwords.upper"))
        self.use_lower   = QCheckBox(tr("passwords.lower"))
        self.use_digits  = QCheckBox(tr("passwords.digits"))
        self.use_symbols = QCheckBox(tr("passwords.symbols"))
        self.use_noambig = QCheckBox(tr("passwords.noambig"))
        self.use_upper.setChecked(True)
        self.use_lower.setChecked(True)
        self.use_digits.setChecked(True)
        self.use_symbols.setChecked(True)
        checks = [self.use_upper, self.use_lower, self.use_digits, self.use_symbols, self.use_noambig]
        for cb in checks:
            cb.setStyleSheet(f"QCheckBox {{ color:{PALETTE["text"]}; }}")
        cgrid = QGridLayout()
        for i, cb in enumerate(checks):
            cgrid.addWidget(cb, i // 2, i % 2)
        oc.addLayout(cgrid)

        qf = QHBoxLayout()
        qf.addWidget(self._label(tr("passwords.quantity"), size=10))
        self.pwd_qty = QComboBox()
        self.pwd_qty.addItems(["1", "3", "5", "10"])
        self.pwd_qty.setStyleSheet(
            f"QComboBox {{ background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; padding:4px 8px; border:none; }}")
        qf.addWidget(self.pwd_qty)
        qf.addStretch()
        oc.addLayout(qf)

        bf = QHBoxLayout()
        bf.addWidget(self._btn(tr("passwords.generate"), self._generate_passwords))
        bf.addWidget(self._btn2(tr("common.clear"), lambda: self.pwd_result.clear()))
        bf.addStretch()
        oc.addLayout(bf)

        rc = self._card(layout)
        top = QHBoxLayout()
        top.addWidget(self._label(tr("passwords.generated"), size=11, bold=True, color=PALETTE["accent2"]))
        top.addStretch()
        top.addWidget(self._btn2(tr("common.copy"), self._copy_passwords))
        rc.addLayout(top)
        self.pwd_result = QTextEdit()
        self.pwd_result.setReadOnly(True)
        self.pwd_result.setFixedHeight(140)
        self.pwd_result.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["accent"]}; border:none; padding:8px;")
        f = QFont(PALETTE["font_mono"], 13); f.setBold(True)
        self.pwd_result.setFont(f)
        rc.addWidget(self.pwd_result)

        layout.addStretch()

    def _generate_passwords(self):
        chars = ""
        if self.use_upper.isChecked():   chars += string.ascii_uppercase
        if self.use_lower.isChecked():   chars += string.ascii_lowercase
        if self.use_digits.isChecked():  chars += string.digits
        if self.use_symbols.isChecked(): chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if self.use_noambig.isChecked():
            for c in "0OIl1":
                chars = chars.replace(c, "")
        if not chars:
            QMessageBox.warning(self, tr("common.warning"), tr("passwords.select_charset"))
            return
        length = self.pwd_length_slider.value()
        qty = int(self.pwd_qty.currentText())
        pwds = ["".join(secrets.choice(chars) for _ in range(length)) for _ in range(qty)]
        self.pwd_result.setPlainText("\n".join(pwds))
        self._log_action("log.password_generated", "log.password_generated.detail", count=qty, length=length)

    def _copy_passwords(self):
        content = self.pwd_result.toPlainText().strip()
        if content:
            self._set_clipboard(content)
            QMessageBox.information(self, tr("common.copied"), tr("msg.password_copied"))

    # ════════════════════════════════════════════════════════
    #  PAGE : FORCE DU MOT DE PASSE
    # ════════════════════════════════════════════════════════
    def _build_strength(self):
        layout = self._new_page("strength")
        self._page_header(layout, "💪", tr("page.strength.title"),
                           tr("page.strength.subtitle"))

        ic = self._card(layout)
        ic.addWidget(self._label(tr("strength.input"), size=11, bold=True, color=PALETTE["accent2"]))
        ef = QHBoxLayout()
        self.str_entry = QLineEdit()
        self.str_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.str_entry.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:8px;")
        self.str_entry.setFont(QFont(PALETTE["font_mono"], 14))
        self.str_entry.textChanged.connect(self._analyze_strength)
        self.str_entry.editingFinished.connect(self._log_strength)
        ef.addWidget(self.str_entry)
        self.str_show_cb = QCheckBox("👁")
        self.str_show_cb.setStyleSheet(f"color:{PALETTE["text"]};")
        self.str_show_cb.toggled.connect(
            lambda on: self.str_entry.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        ef.addWidget(self.str_show_cb)
        ic.addLayout(ef)

        self.str_level_lbl = self._label(tr("strength.placeholder"),
                                          size=11, bold=True, color=PALETTE["dim"])
        ic.addWidget(self.str_level_lbl)
        self.str_bar = QProgressBar()
        self.str_bar.setRange(0, 100)
        self.str_bar.setTextVisible(False)
        self.str_bar.setFixedHeight(8)
        self.str_bar.setStyleSheet(f"""
            QProgressBar {{ background-color:{PALETTE["sidebar"]}; border:none; border-radius:4px; }}
            QProgressBar::chunk {{ background-color:{PALETTE["accent"]}; border-radius:4px; }}
        """)
        ic.addWidget(self.str_bar)

        sc = self._card(layout, tr("strength.details"))
        self.stats_grid_w = QWidget()
        self.stats_grid = QGridLayout(self.stats_grid_w)
        sc.addWidget(self.stats_grid_w)

        cc = self._card(layout, tr("strength.criteria"))
        self.crit_w = QWidget()
        self.crit_layout = QVBoxLayout(self.crit_w)
        self.crit_layout.setContentsMargins(0, 0, 0, 0)
        cc.addWidget(self.crit_w)

        layout.addStretch()

    def _analyze_strength(self):
        pwd = self.str_entry.text()
        if not pwd:
            self.str_level_lbl.setText(tr("strength.placeholder_short"))
            self.str_level_lbl.setStyleSheet(f"color:{PALETTE["dim"]};")
            self.str_bar.setValue(0)
            self._clear_layout(self.stats_grid)
            self._clear_layout(self.crit_layout)
            self._last_strength = None
            return

        criteria = {
            tr("strength.length8"):            len(pwd) >= 8,
            tr("strength.length12"):           len(pwd) >= 12,
            tr("strength.length16"):           len(pwd) >= 16,
            tr("strength.upper"): bool(re.search(r"[A-Z]", pwd)),
            tr("strength.lower"): bool(re.search(r"[a-z]", pwd)),
            tr("strength.digits"):   bool(re.search(r"\d", pwd)),
            tr("strength.symbols"):   bool(re.search(r"[^A-Za-z0-9]", pwd)),
            tr("strength.norepeat"): not bool(re.search(r"(.)\1{2,}", pwd)),
        }
        score = sum(v for v in criteria.values()) / len(criteria) * 100

        levels = [
            (25,  tr("strength.veryweak"), PALETTE["danger"]),
            (50,  tr("strength.weak"),      PALETTE["warning"]),
            (70,  tr("strength.medium"),       PALETTE["warning"]),
            (88,  tr("strength.strong"),        PALETTE["success"]),
            (101, tr("strength.verystrong"),   PALETTE["accent"]),
        ]
        txt, color = tr("strength.verystrong"), PALETTE["accent"]
        for thr, t, c in levels:
            if score <= thr:
                txt, color = t, c
                break

        self.str_level_lbl.setText(tr("strength.level", level=txt))
        self.str_level_lbl.setStyleSheet(f"color:{color};")
        self.str_bar.setValue(int(min(score, 100)))

        self._clear_layout(self.stats_grid)
        stats = [
            (tr("strength.stat.length"),        str(len(pwd))),
            (tr("strength.stat.upper"),      str(sum(c.isupper() for c in pwd))),
            (tr("strength.stat.lower"),      str(sum(c.islower() for c in pwd))),
            (tr("strength.stat.digits"),        str(sum(c.isdigit() for c in pwd))),
            (tr("strength.stat.symbols"),        str(sum(not c.isalnum() for c in pwd))),
            (tr("strength.stat.entropy"), f"~{len(pwd) * 4}"),
        ]
        for i, (lbl, val) in enumerate(stats):
            cell = QFrame()
            cell.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; border-radius:4px;")
            cl = QVBoxLayout(cell)
            v = self._label(val, size=16, bold=True, color=PALETTE["accent"])
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = self._label(lbl, size=9, color=PALETTE["dim"])
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(v)
            cl.addWidget(l)
            self.stats_grid.addWidget(cell, i // 3, i % 3)

        self._clear_layout(self.crit_layout)
        for criterion, passed in criteria.items():
            self.crit_layout.addWidget(self._label(
                f"  {'✅' if passed else '❌'}  {criterion}", size=10,
                color=PALETTE["success"] if passed else PALETTE["danger"]))

        self._last_strength = {"score": f"{score:.0f}", "level": txt}

    def _log_strength(self):
        """Journalise une seule fois par saisie, et non à chaque frappe."""
        if self._last_strength and not self._closing:
            self._log_action("log.strength", "log.strength.detail", **self._last_strength)
            self._last_strength = None

    # ════════════════════════════════════════════════════════
    #  PAGE : HACHAGE
    # ════════════════════════════════════════════════════════
    def _build_hashing(self):
        layout = self._new_page("hashing")
        self._page_header(layout, "🔒", tr("page.hashing.title"),
                           tr("page.hashing.subtitle"))

        ic = self._card(layout, tr("hashing.input"))
        self.hash_input = QTextEdit()
        self.hash_input.setFixedHeight(100)
        self.hash_input.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:8px;")
        self.hash_input.setFont(QFont(PALETTE["font_mono"], 11))
        ic.addWidget(self.hash_input)
        bf = QHBoxLayout()
        bf.addWidget(self._btn(tr("hashing.compute"), self._compute_hashes))
        bf.addWidget(self._btn2(tr("common.clear"), self._clear_hashes))
        bf.addStretch()
        ic.addLayout(bf)

        rc = self._card(layout, tr("hashing.results"))
        self.hash_results = {}
        algos  = ["MD5", "SHA-1", "SHA-256", "SHA-384", "SHA-512"]
        colors = [PALETTE["warning"], PALETTE["warning"], PALETTE["accent"], PALETTE["accent2"], PALETTE["purple"]]
        for algo, col in zip(algos, colors):
            f = QFrame()
            f.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; border:1px solid {PALETTE["border"]}; border-radius:4px;")
            fl = QVBoxLayout(f)
            top = QHBoxLayout()
            top.addWidget(self._label(algo, size=10, bold=True, color=col))
            top.addStretch()
            copy_btn = QPushButton("📋")
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.setStyleSheet(f"background:transparent; color:{PALETTE["dim"]}; border:none;")
            copy_btn.clicked.connect(lambda checked=False, a=algo: self._copy_hash(a))
            top.addWidget(copy_btn)
            fl.addLayout(top)
            val_lbl = self._label("—", size=10, color=PALETTE["dim"], family=PALETTE["font_mono"])
            val_lbl.setWordWrap(True)
            fl.addWidget(val_lbl)
            rc.addWidget(f)
            self.hash_results[algo] = val_lbl
        warn = self._label(tr("hashing.warning"),
                            size=9, color=PALETTE["warning"])
        warn.setWordWrap(True)
        rc.addWidget(warn)

        layout.addStretch()

    def _compute_hashes(self, log=True):
        # Aucun strip() : les espaces font partie intégrante des données à hacher.
        text = self.hash_input.toPlainText()
        if not text:
            QMessageBox.warning(self, tr("common.warning"), tr("hashing.enter_text"))
            return
        data = text.encode("utf-8")
        results = {}
        for algo in ("MD5", "SHA-1", "SHA-256", "SHA-384", "SHA-512"):
            digest = _new_hash(algo)
            digest.update(data)
            results[algo] = digest.hexdigest()
        fg_map = {"MD5": PALETTE["warning"], "SHA-1": PALETTE["warning"],
                  "SHA-256": PALETTE["accent"], "SHA-384": PALETTE["accent2"], "SHA-512": PALETTE["purple"]}
        for algo, lbl in self.hash_results.items():
            lbl.setText(results[algo])
            lbl.setStyleSheet(f"color:{fg_map[algo]};")
        self._hashes_data = results
        if log:
            self._log_action("log.hash", "log.hash.detail", length=len(text))

    def _copy_hash(self, algo):
        if algo in self._hashes_data:
            self._set_clipboard(self._hashes_data[algo])
            QMessageBox.information(self, tr("common.copied"), tr("msg.hash_copied", algo=algo))

    def _clear_hashes(self):
        self.hash_input.clear()
        for lbl in self.hash_results.values():
            lbl.setText("—")
            lbl.setStyleSheet(f"color:{PALETTE["dim"]};")
        self._hashes_data = {}

    # ════════════════════════════════════════════════════════
    #  PAGE : INTÉGRITÉ DES FICHIERS
    # ════════════════════════════════════════════════════════
    def _build_files(self):
        layout = self._new_page("files")
        self._page_header(layout, "📄", tr("page.files.title"),
                           tr("page.files.subtitle"))

        fc = self._card(layout, tr("files.select"))
        fr = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:6px;")
        self.file_path_edit.setFont(QFont(PALETTE["font_mono"], 10))
        fr.addWidget(self.file_path_edit)
        fr.addWidget(self._btn(tr("files.browse"), self._browse_file))
        fc.addLayout(fr)

        af = QHBoxLayout()
        af.addWidget(self._label(tr("files.algorithm"), size=10))
        self.file_algo = QComboBox()
        self.file_algo.addItems(["MD5", "SHA-1", "SHA-256", "SHA-512"])
        self.file_algo.setCurrentText("SHA-256")
        self.file_algo.setStyleSheet(
            f"QComboBox {{ background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; padding:4px 8px; border:none; }}")
        af.addWidget(self.file_algo)
        self.file_calc_btn = self._btn(tr("files.calculate"), self._hash_file)
        af.addWidget(self.file_calc_btn)
        self.file_stop_btn = self._btn2(tr("common.stop"), self._stop_file_hash)
        self.file_stop_btn.setEnabled(False)
        af.addWidget(self.file_stop_btn)
        af.addStretch()
        fc.addLayout(af)

        self.file_algo_warn = self._label(
            tr("files.warning"),
            size=9, color=PALETTE["warning"])
        self.file_algo_warn.setWordWrap(True)
        self.file_algo_warn.setVisible(False)
        fc.addWidget(self.file_algo_warn)

        self.file_prog_lbl = self._label("", size=9, color=PALETTE["dim"])
        fc.addWidget(self.file_prog_lbl)
        self.file_bar = QProgressBar()
        self.file_bar.setRange(0, 100)
        self.file_bar.setTextVisible(False)
        self.file_bar.setFixedHeight(6)
        self.file_bar.setStyleSheet(f"""
            QProgressBar {{ background-color:{PALETTE["sidebar"]}; border:none; border-radius:3px; }}
            QProgressBar::chunk {{ background-color:{PALETTE["accent"]}; border-radius:3px; }}
        """)
        fc.addWidget(self.file_bar)

        hc = self._card(layout, tr("files.fingerprint"))
        self.file_hash_lbl = self._label(tr("files.no_file"), size=10, color=PALETTE["dim"], family=PALETTE["font_mono"])
        self.file_hash_lbl.setWordWrap(True)
        hc.addWidget(self.file_hash_lbl)
        hc.addWidget(self._btn2(tr("files.copy_hash"), self._copy_file_hash))

        vc = self._card(layout, tr("files.verify"))
        vc.addWidget(self._label(tr("files.reference_hint"),
                                  size=9, color=PALETTE["dim"]))
        self.expected_hash = QLineEdit()
        self.expected_hash.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:6px;")
        self.expected_hash.setFont(QFont(PALETTE["font_mono"], 10))
        vc.addWidget(self.expected_hash)
        vc.addWidget(self._btn(tr("files.verify_button"), self._verify_hash, color=PALETTE["accent2"]))
        self.verify_lbl = self._label("", size=11, bold=True)
        vc.addWidget(self.verify_lbl)

        # Toute modification de la cible ou de l'algo invalide l'empreinte
        # calculée : évite un faux « INTÉGRITÉ COMPROMISE ».
        self.file_path_edit.textChanged.connect(self._invalidate_file_hash)
        self.file_algo.currentTextChanged.connect(self._on_file_algo_changed)

        layout.addStretch()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("files.file_dialog"))
        if path:
            self.file_path_edit.setText(path)

    def _on_file_algo_changed(self, algo):
        self.file_algo_warn.setVisible(algo in ("MD5", "SHA-1"))
        self._invalidate_file_hash()

    def _invalidate_file_hash(self):
        """Annule l'empreinte calculée dès que le fichier ou l'algo change."""
        had_hash = bool(self._current_file_hash)
        self._current_file_hash = ""
        if hasattr(self, "file_hash_lbl"):
            self.file_hash_lbl.setText(tr("files.no_file"))
            self.file_hash_lbl.setStyleSheet(f"color:{PALETTE["dim"]};")
        if hasattr(self, "verify_lbl"):
            self.verify_lbl.setText("")
        if had_hash and hasattr(self, "file_prog_lbl"):
            self.file_prog_lbl.setText(tr("files.invalidated"))

    def _hash_file(self):
        if self._file_worker is not None and self._file_worker.isRunning():
            return
        path = self.file_path_edit.text()
        if not path or not os.path.isfile(path):
            QMessageBox.critical(self, tr("common.error"), tr("files.not_found"))
            return
        algo = self.file_algo.currentText()
        self._current_file_hash = ""
        self.verify_lbl.setText("")
        self.file_hash_lbl.setText(tr("files.calculating"))
        self.file_hash_lbl.setStyleSheet(f"color:{PALETTE["dim"]};")
        self.file_calc_btn.setEnabled(False)
        self.file_stop_btn.setEnabled(True)
        self.file_bar.setValue(0)
        self.file_prog_lbl.setText("")

        self._file_worker = FileHashWorker(path, algo)
        self._file_worker.finished_hash.connect(self._on_file_hash_done)
        self._file_worker.progress.connect(self._on_file_hash_progress)
        self._file_worker.error.connect(self._on_file_hash_error)
        self._file_worker.start()

    def _on_file_hash_progress(self, done, total):
        self.file_bar.setValue(int(done * 100 / total) if total else 0)
        self.file_prog_lbl.setText(f"{done} / {total} octets")

    def _on_file_hash_done(self, algo, digest, size):
        self._current_file_hash = digest
        self.file_hash_lbl.setText(digest)
        self.file_hash_lbl.setStyleSheet(f"color:{PALETTE["accent"]};")
        self.file_bar.setValue(100)
        self.file_prog_lbl.setText(tr("files.done", size=size))
        self.file_calc_btn.setEnabled(True)
        self.file_stop_btn.setEnabled(False)
        # On ne journalise ni le nom du fichier ni l'empreinte elle-même.
        self._log_action("log.file_hash", "log.file_hash.detail", algo=algo, size=size)

    def _on_file_hash_error(self, message):
        self._current_file_hash = ""
        self.file_hash_lbl.setText(tr("files.calc_error"))
        self.file_prog_lbl.setText("")
        self.file_calc_btn.setEnabled(True)
        self.file_stop_btn.setEnabled(False)
        QMessageBox.critical(self, tr("common.error"), message)

    def _stop_file_hash(self):
        if self._file_worker is not None:
            self._file_worker.stop()
        self.file_stop_btn.setEnabled(False)
        self.file_prog_lbl.setText(tr("files.stopped"))

    def _copy_file_hash(self):
        if self._current_file_hash:
            self._set_clipboard(self._current_file_hash)
            QMessageBox.information(self, tr("common.copied"), tr("msg.file_hash_copied"))

    def _verify_hash(self):
        if not self._current_file_hash:
            QMessageBox.warning(self, tr("common.warning"), tr("files.compute_first"))
            return
        expected = self.expected_hash.text().strip().lower()
        if not expected:
            QMessageBox.warning(self, tr("common.warning"), tr("files.enter_reference"))
            return
        algo = self.file_algo.currentText()
        lengths = {"MD5": 32, "SHA-1": 40, "SHA-256": 64, "SHA-512": 128}
        length = lengths.get(algo)
        if length and len(expected) != length:
            QMessageBox.warning(
                self, tr("common.warning"),
                tr("files.invalid_length", algo=algo, length=length))
            return
        ok = hmac.compare_digest(expected, self._current_file_hash.lower())
        self.verify_lbl.setText(
            tr("files.ok") if ok
            else tr("files.ko"))
        self.verify_lbl.setStyleSheet(f"color:{PALETTE["success"] if ok else PALETTE["danger"]};")
        self._log_action("log.verify", "log.match" if ok else "log.mismatch")

    # ════════════════════════════════════════════════════════
    #  PAGE : SCANNER DE PORTS
    # ════════════════════════════════════════════════════════
    def _build_scanner(self):
        layout = self._new_page("scanner")
        self._page_header(layout, "🔍", tr("page.scanner.title"),
                           tr("page.scanner.subtitle"))

        cc = self._card(layout, tr("scanner.config"))
        rows_data = [
            (tr("scanner.host"),     "host",    "127.0.0.1"),
            (tr("scanner.start_port"), "pstart",  "1"),
            (tr("scanner.end_port"),   "pend",    "1024"),
            (tr("scanner.timeout"),   "timeout", "0.5"),
        ]
        self.scan_entries = {}
        for lbl, key, default in rows_data:
            r = QHBoxLayout()
            l = self._label(lbl, size=10); l.setFixedWidth(120)
            r.addWidget(l)
            e = QLineEdit(default)
            e.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:5px;")
            e.setFont(QFont(PALETTE["font_mono"], 10))
            e.setFixedWidth(160)
            r.addWidget(e)
            r.addStretch()
            self.scan_entries[key] = e
            cc.addLayout(r)

        pf = QHBoxLayout()
        pf.addWidget(self._label(tr("scanner.presets"), size=9, color=PALETTE["dim"]))
        for name, s, e in [(tr("scanner.preset.top"), 1, 1024), (tr("scanner.preset.web"), 80, 443), (tr("scanner.preset.extended"), 1, 10000)]:
            pb = QPushButton(name)
            pb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            pb.setStyleSheet(
                f"QPushButton {{ background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:3px 8px; }}")
            pb.clicked.connect(lambda checked=False, s=s, e=e: self._apply_scan_preset(s, e))
            pf.addWidget(pb)
        pf.addStretch()
        cc.addLayout(pf)

        bf = QHBoxLayout()
        self.scan_btn = self._btn(tr("scanner.launch"), self._start_scan, color=PALETTE["danger"])
        bf.addWidget(self.scan_btn)
        self.stop_btn = self._btn2(tr("common.stop"), self._stop_scan)
        self.stop_btn.setEnabled(False)
        bf.addWidget(self.stop_btn)
        bf.addStretch()
        self.scan_prog_lbl = self._label("", size=9, color=PALETTE["dim"])
        bf.addWidget(self.scan_prog_lbl)
        cc.addLayout(bf)

        self.scan_bar = QProgressBar()
        self.scan_bar.setRange(0, 100)
        self.scan_bar.setTextVisible(False)
        self.scan_bar.setFixedHeight(8)
        self.scan_bar.setStyleSheet(f"""
            QProgressBar {{ background-color:{PALETTE["sidebar"]}; border:none; border-radius:4px; }}
            QProgressBar::chunk {{ background-color:{PALETTE["accent"]}; border-radius:4px; }}
        """)
        cc.addWidget(self.scan_bar)

        rc = self._card(layout, tr("scanner.open_ports"))
        top = QHBoxLayout()
        top.addStretch()
        self.scan_count_lbl = self._label("", size=9, color=PALETTE["dim"])
        top.addWidget(self.scan_count_lbl)
        rc.addLayout(top)
        self.scan_output = QTextEdit()
        self.scan_output.setReadOnly(True)
        self.scan_output.setMinimumHeight(220)
        self.scan_output.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:8px;")
        self.scan_output.setFont(QFont(PALETTE["font_mono"], 10))
        rc.addWidget(self.scan_output)

    def _apply_scan_preset(self, s, e):
        self.scan_entries["pstart"].setText(str(s))
        self.scan_entries["pend"].setText(str(e))

    def _start_scan(self):
        if self._scan_worker is not None and self._scan_worker.isRunning():
            return
        try:
            host    = self.scan_entries["host"].text().strip()
            start   = int(self.scan_entries["pstart"].text())
            end     = int(self.scan_entries["pend"].text())
            timeout = float(self.scan_entries["timeout"].text())
        except ValueError:
            QMessageBox.critical(self, tr("common.error"), tr("scanner.invalid_params"))
            return
        if not self._valid_host(host):
            QMessageBox.critical(self, tr("common.error"), tr("scanner.invalid_host"))
            return
        if end > 65535 or start < 1 or start > end:
            QMessageBox.critical(self, tr("common.error"), tr("scanner.invalid_range"))
            return
        if not (0.05 <= timeout <= 5.0):
            QMessageBox.critical(
                self, tr("common.error"),
                tr("scanner.invalid_timeout"))
            return
        if (end - start) > 10000:
            reply = QMessageBox.question(
                self, tr("common.confirmation"),
                tr("scanner.confirm_large", count=end - start + 1))
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._scanning = True
        self._scan_aborted = False
        self._scan_error = ""
        self._open_ports = 0
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.scan_bar.setValue(0)
        self.scan_output.clear()
        self.scan_output.append(tr(
            "scanner.started",
            host=_esc(host), start=start, end=end, timeout=timeout,
            date=datetime.now().strftime("%d/%m/%Y  %H:%M:%S")) + "\n" + "─" * 56)

        self._scan_worker = PortScanWorker(host, start, end, timeout)
        self._scan_worker.port_found.connect(self._on_port_found)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished_scan.connect(self._scan_done)
        self._scan_worker.error.connect(self._scan_error_occurred)
        self._scan_worker.start()

    def _stop_scan(self):
        self._scan_aborted = True
        self.scan_prog_lbl.setText(tr("scanner.stopping"))
        if self._scan_worker is not None:
            self._scan_worker.stop()
        self.stop_btn.setEnabled(False)

    def _scan_error_occurred(self, message):
        self._scan_error = message
        self._scan_aborted = True
        self.scan_output.append(
            f'<span style="color:{PALETTE["danger"]};">❌  {_esc(message)}</span>')

    def _on_port_found(self, port, svc):
        self.scan_output.append(
            f'<span style="color:{PALETTE["success"]};">'
            f'{tr("scanner.port_open", port=port, svc=_esc(svc))}</span>')

    def _on_scan_progress(self, done, total):
        pct = done / total * 100
        self.scan_bar.setValue(int(pct))
        self.scan_prog_lbl.setText(tr("scanner.progress", done=done, total=total))

    def _scan_done(self, open_count):
        self._scanning = False
        self._open_ports = open_count
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        host = self.scan_entries["host"].text()
        if self._scan_error:
            self.scan_bar.setValue(0)
            self.scan_count_lbl.setText(tr("scanner.impossible"))
        elif self._scan_aborted:
            self.scan_bar.setValue(0)
            self.scan_output.append(
                f'<span style="color:{PALETTE["warning"]};">'
                f'{tr("scanner.aborted", count=open_count)}</span>')
            self.scan_count_lbl.setText(tr("scanner.aborted_count", count=open_count))
            self._log_action("log.scan", "log.scan.aborted", host=host, count=open_count)
        else:
            self.scan_bar.setValue(100)
            self.scan_output.append(
                f'<span style="color:{PALETTE["accent"]};">{"─" * 56}<br>'
                f'{tr("scanner.done", count=open_count)}</span>')
            self.scan_count_lbl.setText(tr("scanner.count", count=open_count))
            self._log_action("log.scan", "log.scan.done", host=host, count=open_count)

    # ════════════════════════════════════════════════════════
    #  PAGE : BASE64
    # ════════════════════════════════════════════════════════
    def _build_base64(self):
        layout = self._new_page("base64")
        self._page_header(layout, "⚙️", tr("page.base64.title"),
                           tr("page.base64.subtitle"))

        ic = self._card(layout, tr("base64.source"))
        self.b64_input = QTextEdit()
        self.b64_input.setFixedHeight(140)
        self.b64_input.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:8px;")
        self.b64_input.setFont(QFont(PALETTE["font_mono"], 11))
        ic.addWidget(self.b64_input)
        bf = QHBoxLayout()
        bf.addWidget(self._btn(tr("base64.encode"), self._b64_encode))
        bf.addWidget(self._btn(tr("base64.decode"), self._b64_decode, color=PALETTE["accent2"]))
        bf.addWidget(self._btn2(tr("base64.swap"), self._b64_swap))
        bf.addWidget(self._btn2(tr("base64.clear"), self._b64_clear))
        bf.addStretch()
        ic.addLayout(bf)

        oc = self._card(layout)
        top = QHBoxLayout()
        top.addWidget(self._label(tr("base64.result"), size=11, bold=True, color=PALETTE["accent2"]))
        top.addStretch()
        top.addWidget(self._btn2(tr("common.copy"), self._b64_copy))
        oc.addLayout(top)
        self.b64_output = QTextEdit()
        self.b64_output.setReadOnly(True)
        self.b64_output.setFixedHeight(140)
        self.b64_output.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["accent"]}; border:none; padding:8px;")
        self.b64_output.setFont(QFont(PALETTE["font_mono"], 11))
        oc.addWidget(self.b64_output)
        self.b64_status = self._label("", size=9)
        oc.addWidget(self.b64_status)

        layout.addStretch()

    def _b64_encode(self):
        # Aucun rstrip() : la charge utile est encodée telle quelle.
        text = self.b64_input.toPlainText()
        if not text:
            return
        result = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        self.b64_output.setPlainText(result)
        self.b64_status.setText(tr("base64.encoded", count=len(result)))
        self.b64_status.setStyleSheet(f"color:{PALETTE["success"]};")
        self._log_action("log.b64_encode", "log.b64_encode.detail", src=len(text), out=len(result))

    def _b64_decode(self):
        # Seuls les sauts de ligne de l'éditeur sont retirés, pas les espaces.
        text = self.b64_input.toPlainText().rstrip("\r\n")
        if not text:
            return
        # On efface d'abord l'ancien résultat pour ne jamais afficher un
        # décodage périmé à côté d'un message d'erreur.
        self.b64_output.clear()
        try:
            raw = base64.b64decode(text.encode("ascii"), validate=True)
        except Exception:
            self.b64_status.setText(tr("base64.invalid"))
            self.b64_status.setStyleSheet(f"color:{PALETTE["danger"]};")
            return
        try:
            result = raw.decode("utf-8")
            self.b64_output.setPlainText(result)
            self.b64_status.setText(tr("base64.decoded", count=len(result)))
        except UnicodeDecodeError:
            self.b64_output.setPlainText(raw.hex(" "))
            self.b64_status.setText(
                tr("base64.binary", count=len(raw)))
        self.b64_status.setStyleSheet(f"color:{PALETTE["success"]};")
        self._log_action("log.b64_decode", "log.ok")

    def _b64_swap(self):
        out = self.b64_output.toPlainText().strip()
        if out:
            self.b64_input.setPlainText(out)
            self.b64_output.clear()
            self.b64_status.setText("")

    def _b64_clear(self):
        self.b64_input.clear()
        self.b64_output.clear()
        self.b64_status.setText("")

    def _b64_copy(self):
        content = self.b64_output.toPlainText().strip()
        if content:
            self._set_clipboard(content)
            QMessageBox.information(self, tr("common.copied"), tr("msg.result_copied"))

    # ════════════════════════════════════════════════════════
    #  PAGE : INFORMATIONS RÉSEAU
    # ════════════════════════════════════════════════════════
    def _build_network(self):
        layout = self._new_page("network")
        self._page_header(layout, "🌐", tr("page.network.title"),
                           tr("page.network.subtitle"))

        top_row = QHBoxLayout()
        top_row.addWidget(self._btn(tr("network.refresh"), self._refresh_network))
        top_row.addStretch()
        layout.addLayout(top_row)

        lc = self._card(layout, tr("network.local"))
        self.net_info_w = QWidget()
        self.net_info_layout = QVBoxLayout(self.net_info_w)
        self.net_info_layout.setContentsMargins(0, 0, 0, 0)
        lc.addWidget(self.net_info_w)

        dc = self._card(layout, tr("network.dns"))
        dr = QHBoxLayout()
        self.dns_entry = QLineEdit("google.com")
        self.dns_entry.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:5px;")
        self.dns_entry.setFont(QFont(PALETTE["font_mono"], 10))
        dr.addWidget(self.dns_entry)
        dr.addWidget(self._btn(tr("network.resolve"), self._dns_resolve, color=PALETTE["accent2"]))
        dc.addLayout(dr)
        self.dns_result = self._label("", size=11, color=PALETTE["accent"], family=PALETTE["font_mono"])
        self.dns_result.setWordWrap(True)
        dc.addWidget(self.dns_result)

        pc = self._card(layout, tr("network.ping"))
        pr = QHBoxLayout()
        self.ping_entry = QLineEdit("8.8.8.8")
        self.ping_entry.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:5px;")
        self.ping_entry.setFont(QFont(PALETTE["font_mono"], 10))
        pr.addWidget(self.ping_entry)
        self.ping_btn = self._btn(tr("network.ping_button"), self._do_ping)
        pr.addWidget(self.ping_btn)
        pc.addLayout(pr)
        self.ping_result = self._label("", size=11, color=PALETTE["accent"], family=PALETTE["font_mono"])
        self.ping_result.setWordWrap(True)
        pc.addWidget(self.ping_result)

        layout.addStretch()
        self._refresh_network()

    def _refresh_network(self):
        self._clear_layout(self.net_info_layout)
        # gethostname() est purement local ; on évite gethostbyname() qui
        # interroge le résolveur systémique sans timeout et gèle l'UI.
        hostname = socket.gethostname()
        local_ip = tr("common.unknown")
        for iface in QNetworkInterface.allInterfaces():
            for entry in iface.addressEntries():
                ip = entry.ip()
                if (ip.protocol() == QAbstractSocket.NetworkLayerProtocol.IPv4Protocol
                        and not ip.toString().startswith("127.")):
                    local_ip = ip.toString()
                    break
            if local_ip != tr("common.unknown"):
                break
        data = [
            (tr("network.hostname"),          hostname),
            (tr("network.local_ip"), local_ip),
            (tr("network.os"),                f"{platform.system()} {platform.release()}"),
            (tr("dashboard.architecture"),      platform.machine()),
            (tr("network.python"),            platform.python_version()),
        ]
        for lbl, val in data:
            row = QFrame()
            row.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; border-radius:3px;")
            rl = QHBoxLayout(row)
            l1 = self._label(f"{lbl} :", size=10, color=PALETTE["dim"]); l1.setFixedWidth(180)
            l2 = self._label(_esc(str(val)), size=10, color=PALETTE["accent"], family=PALETTE["font_mono"])
            rl.addWidget(l1); rl.addWidget(l2); rl.addStretch()
            self.net_info_layout.addWidget(row)

    def _dns_resolve(self):
        domain = self.dns_entry.text().strip()
        if not self._valid_host(domain):
            self.dns_result.setText(tr("dns.invalid"))
            self.dns_result.setStyleSheet(f"color:{PALETTE["danger"]};")
            return
        self.dns_result.setText(tr("dns.resolving", domain=_esc(domain)))
        self.dns_result.setStyleSheet(f"color:{PALETTE["warning"]};")
        # Résolution asynchrone : le thread GUI n'attend pas le résolveur.
        # Les stubs PySide6 déclarent la forme à callback comme une méthode
        # d'instance (et non comme un staticmethod) : on appelle donc
        # lookupHost sur une instance conservée pour prolonger sa durée de vie.
        self._dns_lookup = QHostInfo()
        self._dns_lookup.lookupHost(domain, self._on_dns_done)

    def _on_dns_done(self, info: QHostInfo):
        domain = self.dns_entry.text().strip()
        if info.error() != QHostInfo.HostInfoError.NoError:
            self.dns_result.setText(tr("dns.error", error=_esc(info.errorString())))
            self.dns_result.setStyleSheet(f"color:{PALETTE["danger"]};")
            return
        addresses = [a.toString() for a in info.addresses()
                     if a.protocol() == QAbstractSocket.NetworkLayerProtocol.IPv4Protocol]
        if not addresses:
            self.dns_result.setText(tr("dns.no_ipv4", domain=_esc(domain)))
            self.dns_result.setStyleSheet(f"color:{PALETTE["danger"]};")
            return
        ip = addresses[0]
        self.dns_result.setText(tr("dns.ok", domain=_esc(domain), ip=_esc(ip)))
        self.dns_result.setStyleSheet(f"color:{PALETTE["success"]};")
        self._log_action("log.dns", "log.dns.detail", domain=domain, ip=ip)

    def _do_ping(self):
        if self._ping_worker is not None and self._ping_worker.isRunning():
            return
        host = self.ping_entry.text().strip()
        if not self._valid_host(host):
            self.ping_result.setText(tr("dns.invalid_host"))
            self.ping_result.setStyleSheet(f"color:{PALETTE["danger"]};")
            return
        self.ping_btn.setEnabled(False)
        self.ping_result.setText(tr("ping.running"))
        self.ping_result.setStyleSheet(f"color:{PALETTE["warning"]};")
        self._ping_worker = PingWorker(host)
        self._ping_worker.finished_ping.connect(
            lambda ok, err, h=host: self._on_ping_done(ok, err, h))
        self._ping_worker.start()

    def _on_ping_done(self, ok, err, host):
        self.ping_btn.setEnabled(True)
        if err:
            self.ping_result.setText(tr("dns.error", error=_esc(err)))
            self.ping_result.setStyleSheet(f"color:{PALETTE["danger"]};")
        else:
            state = tr("ping.accessible") if ok else tr("ping.unreachable")
            self.ping_result.setText(tr("ping.result", mark=("✅" if ok else "❌"), host=_esc(host), state=state))
            self.ping_result.setStyleSheet(
                f"color:{PALETTE["success"] if ok else PALETTE["danger"]};")
        self._log_action("log.ping", "log.ping.detail", host=host, state=("OK" if ok else "FAIL"))

    # ════════════════════════════════════════════════════════
    #  PAGE : MISE À JOUR
    # ════════════════════════════════════════════════════════
    def _build_update(self):
        layout = self._new_page("update")
        self._page_header(layout, "🆕", tr("page.update.title"),
                          tr("page.update.subtitle"))

        info = self._card(layout, tr("update.installed"))
        last_check = str(self._settings.value("update.last_check", "") or "") or tr("update.never")
        for label, value in (
            (tr("update.mode"), tr(distribution_i18n_key(self._update_mode))),
            (tr("update.installed"), f"v{APP_VERSION}"),
            (tr("update.last_check"), last_check),
        ):
            row = QHBoxLayout()
            row.addWidget(self._label(f"  {label} :", size=9, color=PALETTE["dim"]))
            row.addWidget(self._label(value, size=10, color=PALETTE["accent"]))
            row.addStretch()
            info.addLayout(row)

        check = self._card(layout, tr("update.check_button"))
        self.update_auto_cb = QCheckBox(tr("update.auto_check"))
        self.update_auto_cb.setChecked(setting_flag(self._settings, "update.auto_check", True))
        self.update_auto_cb.setFont(QFont(PALETTE["font_family"], 10))
        self.update_auto_cb.setStyleSheet(f"color:{PALETTE["text"]}; background:transparent;")
        self.update_auto_cb.stateChanged.connect(self._on_auto_check_changed)
        check.addWidget(self.update_auto_cb)
        self.update_check_btn = self._btn(
            tr("update.check_button"), lambda: self._check_updates(False))
        check.addWidget(self.update_check_btn)
        self.update_status_lbl = self._label("", size=10, color=PALETTE["dim"])
        self.update_status_lbl.setWordWrap(True)
        check.addWidget(self.update_status_lbl)

        avail = self._card(layout, tr("update.available"))
        self.update_version_lbl = self._label(
            tr("update.up_to_date"), size=12, bold=True, color=PALETTE["accent2"])
        avail.addWidget(self.update_version_lbl)
        self.update_notes = QTextEdit()
        self.update_notes.setReadOnly(True)
        self.update_notes.setMinimumHeight(110)
        self.update_notes.setStyleSheet(
            f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:8px;")
        self.update_notes.setFont(QFont(PALETTE["font_mono"], 9))
        avail.addWidget(self.update_notes)

        actions = QHBoxLayout()
        self.update_download_btn = self._btn(
            tr("update.download_button"), self._download_update,
            color=PALETTE["accent2"])
        self.update_download_btn.setEnabled(
            self._release is not None and self._update_mode != "pip")
        actions.addWidget(self.update_download_btn)
        actions.addWidget(self._btn2(tr("update.open_release"), self._open_release_page))
        if self._update_mode == "pip":
            actions.addWidget(self._btn2(tr("update.copy_command"), self._copy_pip_command))
        actions.addStretch()
        avail.addLayout(actions)

        self.update_pip_lbl = self._label(
            "", size=9, color=PALETTE["dim"], family=PALETTE["font_mono"])
        self.update_pip_lbl.setWordWrap(True)
        self.update_pip_lbl.setVisible(self._update_mode == "pip")
        avail.addWidget(self.update_pip_lbl)
        self.update_progress = QProgressBar()
        self.update_progress.setVisible(False)
        avail.addWidget(self.update_progress)

        sec = self._card(layout, tr("update.security"))
        detail = self._label(tr("update.security_detail"), size=9, color=PALETTE["dim"])
        detail.setWordWrap(True)
        sec.addWidget(detail)
        layout.addStretch()

        self._render_update_status()
        if self._release is not None:
            self._display_release(self._release)

    def _set_update_status(self, kind, detail=""):
        self._update_status = (kind, detail)
        self._render_update_status()

    def _render_update_status(self):
        """Redessine le statut dans la langue courante (y compris après RTL)."""
        label = getattr(self, "update_status_lbl", None)
        if label is None:
            return
        kind, detail = self._update_status
        texts = {
            "checking": tr("update.checking"),
            "uptodate": tr("update.up_to_date"),
            "available": tr("update.available_detail", version=detail),
            "error": detail,
            "downloading": tr("update.downloading", percent=detail),
            "downloaded": tr("update.downloaded", file=detail),
        }
        colors = {
            "error": PALETTE["danger"],
            "available": PALETTE["accent2"],
            "checking": PALETTE["warning"],
            "downloading": PALETTE["warning"],
            "downloaded": PALETTE["success"],
        }
        label.setText(texts.get(kind, ""))
        label.setStyleSheet(f"color:{colors.get(kind, PALETTE["dim"])};")

    def _display_release(self, release):
        """Remplit la carte « version disponible » après une vérification."""
        label = getattr(self, "update_version_lbl", None)
        if label is None:
            return
        label.setText(tr("update.available_detail", version=release.version))
        notes = getattr(self, "update_notes", None)
        if notes is not None:
            notes.setPlainText(release.notes.strip() or tr("update.no_notes"))
        btn = getattr(self, "update_download_btn", None)
        if btn is not None:
            btn.setEnabled(self._update_mode != "pip")
        pip_label = getattr(self, "update_pip_lbl", None)
        if pip_label is not None and self._update_mode == "pip":
            pip_label.setText(pip_install_command(release))

    def _auto_check_updates(self):
        if setting_flag(self._settings, "update.auto_check", True):
            self._check_updates(silent=True)

    def _on_auto_check_changed(self, state):
        self._settings.setValue("update.auto_check", int(state) != 0)

    def _check_updates(self, silent=False):
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        if not silent:
            self._set_update_status("checking")
        self.update_check_btn.setEnabled(False)
        self._update_worker = UpdateCheckWorker(APP_VERSION)
        self._update_worker.finished_check.connect(
            lambda release, error, s=silent: self._on_update_checked(release, error, s))
        self._update_worker.start()

    def _on_update_checked(self, release, error, silent=False):
        self.update_check_btn.setEnabled(True)
        self._settings.setValue("update.last_check",
                                datetime.now().strftime("%Y-%m-%d"))
        if error:
            if not silent:
                self._set_update_status("error", error)
                QMessageBox.warning(self, tr("common.warning"), error)
            return
        if release is None:
            if not silent:
                self._set_update_status("uptodate")
            return

        self._release = release
        self._update_available = True
        self._set_update_status("available", release.version)
        self._log_action("log.update.check", "log.update.check.detail",
                         version=release.version)
        self._display_release(release)
        nav = self.nav_buttons.get("update")
        if nav is not None:
            nav.setText(f"{tr('nav.update')}  •")

    def _open_release_page(self):
        release = self._release
        url = release.page_url if release is not None else RELEASES_PAGE
        QDesktopServices.openUrl(QUrl(url))

    def _copy_pip_command(self):
        release = self._release
        if release is None:
            return
        self._set_clipboard(pip_install_command(release))
        QMessageBox.information(self, tr("common.info"), tr("msg.result_copied"))

    def _download_update(self):
        release = self._release
        if release is None:
            return
        if self._download_worker is not None and self._download_worker.isRunning():
            return
        if self._update_mode == "pip":
            self._open_release_page()
            return

        asset = asset_for_mode(release, self._update_mode)
        if asset is None:
            QMessageBox.warning(self, tr("common.warning"), tr("update.error.asset"))
            return
        if self._update_mode == "installer":
            destination = downloads_dir() / asset.name
        else:
            destination = temp_dir() / asset.name

        self._download_worker = UpdateDownloadWorker(
            release, self._update_mode, destination)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished_download.connect(self._on_download_done)
        self.update_progress.setRange(0, 100)
        self.update_progress.setValue(0)
        self.update_progress.setVisible(True)
        self.update_download_btn.setEnabled(False)
        self._set_update_status("downloading", "0")
        self._download_worker.start()

    def _on_download_progress(self, done, total):
        percent = int(done * 100 / total) if total else 0
        self.update_progress.setValue(percent)
        self._set_update_status("downloading", str(percent))

    def _on_download_done(self, path, error, state):
        release = self._release
        self.update_progress.setVisible(False)
        self.update_download_btn.setEnabled(release is not None)
        if error:
            self._set_update_status("error", error)
            QMessageBox.critical(self, tr("common.error"), error)
            return
        if release is None:
            return

        filename = Path(path).name
        checksum_text = (tr("update.verified") if state == "verified"
                         else tr("update.unverified"))
        self._set_update_status("downloaded", filename)
        self._log_action("log.update.download", "log.update.download.detail",
                         file=filename, checksum=checksum_text)

        if self._update_mode == "portable":
            target = executable_dir().parent / f"CyberSecDashboard-v{release.version}"
            folder, exe = extract_portable_archive(path, target)
            shown = str(exe) if exe is not None else str(folder)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(tr("common.info"))
            msg.setText(tr("update.portable_ready", path=shown))
            open_btn = msg.addButton(tr("update.open_folder"),
                                     QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()
            if msg.clickedButton() == open_btn:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
            return

        reply = QMessageBox.question(
            self, tr("common.confirmation"),
            tr("update.installer_confirm", path=path))
        if reply == QMessageBox.StandardButton.Yes:
            try:
                subprocess.Popen([path], shell=False)
            except OSError as exc:
                QMessageBox.critical(self, tr("common.error"), str(exc))

    # ════════════════════════════════════════════════════════
    #  PAGE : JOURNAL D'ACTIVITÉ
    # ════════════════════════════════════════════════════════
    def _build_logs(self):
        layout = self._new_page("logs")
        self._page_header(layout, "📋", tr("page.logs.title"),
                           tr("page.logs.subtitle"))

        bf = QHBoxLayout()
        bf.addWidget(self._btn(tr("logs.export"), self._export_logs))
        bf.addWidget(self._btn2(tr("common.clear"), self._clear_logs))
        bf.addStretch()
        self.log_count_lbl = self._label(tr("logs.entries", count=0), size=9, color=PALETTE["dim"])
        bf.addWidget(self.log_count_lbl)
        layout.addLayout(bf)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(300)
        self.log_text.setStyleSheet(f"background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]}; border:none; padding:10px;")
        self.log_text.setFont(QFont(PALETTE["font_mono"], 10))
        layout.addWidget(self.log_text)

    def _refresh_logs(self):
        self.log_text.clear()
        if not self.log_entries:
            self.log_text.append(f'<span style="color:{PALETTE["text"]};">' + tr("logs.empty") + '</span>')
        else:
            for e in self.log_entries:
                action, details = self._log_entry_text(e)
                line = (f'<span style="color:{PALETTE["dim"]};">[{_esc(e["date"])} {_esc(e["time"])}]</span>  '
                        f'<span style="color:{PALETTE["accent2"]};">{_esc(action)}</span>')
                if details:
                    line += f'  —  <span style="color:{PALETTE["text"]};">{_esc(details)}</span>'
                self.log_text.append(line)
        self.log_count_lbl.setText(tr("logs.entries", count=len(self.log_entries)))

    def _clear_logs(self):
        reply = QMessageBox.question(self, tr("common.confirm"), tr("logs.clear_confirm"))
        if reply == QMessageBox.StandardButton.Yes:
            self.log_entries.clear()
            self._refresh_logs()

    def _export_logs(self):
        if not self.log_entries:
            QMessageBox.information(self, tr("common.info"), tr("logs.no_logs"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("logs.export_dialog"), "", tr("logs.export_filter"))
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tr("logs.export_header", app=APP_NAME))
                for e in self.log_entries:
                    action, details = self._log_entry_text(e)
                    f.write(f"[{e['date']} {e['time']}]  {action}")
                    if details:
                        f.write(f"  —  {details}")
                    f.write("\n")
        except OSError as exc:
            QMessageBox.critical(self, tr("common.error"), tr("logs.export_error", error=exc))
            return
        QMessageBox.information(
            self, tr("logs.exported"),
            tr("logs.export_ok", path=path))

    # ════════════════════════════════════════════════════════
    #  FERMETURE SÉCURISÉE DE LA FENÊTRE
    # ════════════════════════════════════════════════════════
    def closeEvent(self, event):
        """
        Équivalent PyQt du protocole WM_DELETE_WINDOW de Tkinter : appelé à
        chaque tentative de fermeture — croix de la fenêtre, Alt+F4, Cmd+Q,
        ou bouton "Quitter" de la sidebar (qui appelle self.close()).
        Empêche les fermetures concurrentes, demande toujours une confirmation
        stylée, nettoie les ressources actives, puis accepte (ou refuse)
        l'événement.
        """
        if self._closing:
            event.ignore()
            return

        if not self._confirm_quit():
            event.ignore()
            return

        self._closing = True
        try:
            self._shutdown()
        except Exception as e:
            # Le nettoyage ne doit jamais empêcher la fermeture : on
            # journalise l'erreur et on laisse la fenêtre se fermer.
            print(f"[AVERTISSEMENT] Erreur pendant la fermeture : {e}")
        event.accept()

    def _confirm_quit(self):
        """Affiche une confirmation stylée avant de quitter l'application.

        Appelée depuis closeEvent(), donc utilisée aussi bien pour la croix
        de la fenêtre que pour le bouton "Quitter" de la sidebar.
        Renvoie True si l'utilisateur confirme, False sinon.
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tr("common.confirmation"))
        msg.setText(tr("quit.question"))
        if (self._scanning
                or (self._ping_worker is not None and self._ping_worker.isRunning())
                or (self._file_worker is not None and self._file_worker.isRunning())
                or (self._download_worker is not None and self._download_worker.isRunning())):
            msg.setInformativeText(tr("quit.busy"))
        
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Style personnalisé, aligné sur la palette sombre de l'application
        # (plutôt que sur des couleurs génériques) pour rester cohérent avec
        # le reste de l'UI.
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {PALETTE["card"]}; color: {PALETTE["text"]};
                font-size: 14px; font-family: '{PALETTE["font_family"]}';
            }}
            QMessageBox QLabel {{ color: {PALETTE["text"]}; background: transparent; }}
            QPushButton {{
                background-color: {PALETTE["border"]}; color: {PALETTE["text"]};
                padding: 6px 14px; border-radius: 4px; border: none;
            }}
            QPushButton:hover {{ background-color: {PALETTE["danger"]}; color: #ffffff; }}
            QPushButton:pressed {{ background-color: {PALETTE["success"]}; color: #ffffff; }}
        """)
        msg.setFont(QFont(PALETTE["font_family"], 11))

        return msg.exec() == QMessageBox.StandardButton.Yes

    @staticmethod
    def _stop_thread(worker, timeout_ms):
        """Arrête un QThread et attend réellement sa fin avant la fermeture."""
        if worker is None:
            return
        if worker.isRunning():
            stop = getattr(worker, "stop", None)
            if callable(stop):
                stop()
            # Le délai couvre le timeout maximal du scanner (5 s) et celui
            # du ping sous-jacent (12 s).
            worker.wait(timeout_ms)
        if worker.isRunning():
            print("[AVERTISSEMENT] Thread encore actif : arrêt forcé.")
            worker.terminate()
            worker.wait(1000)

    def _shutdown(self):
        """Arrête proprement les threads actifs et purge les données sensibles."""
        self._scanning = False
        self._stop_thread(self._scan_worker, 6000)
        self._stop_thread(self._ping_worker, 15000)
        self._stop_thread(self._file_worker, 6000)
        self._stop_thread(self._update_worker, 5000)
        self._stop_thread(self._download_worker, 5000)

        # Arrêt de l'horloge périodique (QTimer).
        if hasattr(self, "_clock_timer"):
            self._clock_timer.stop()

        self._wipe_sensitive_data()

    @staticmethod
    def _clear_widget(widget):
        """Vide un widget sans déclencher de slot pendant le nettoyage."""
        if widget is None:
            return
        widget.blockSignals(True)
        try:
            widget.clear()
        except Exception:
            pass
        finally:
            widget.blockSignals(False)

    def _wipe_sensitive_data(self):
        """Efface *toutes* les valeurs sensibles gardées en mémoire."""
        for name in ("str_entry", "hash_input", "b64_input", "b64_output",
                     "expected_hash", "file_path_edit", "dns_entry", "ping_entry"):
            self._clear_widget(getattr(self, name, None))
        for name in ("pwd_result", "scan_output", "log_text"):
            self._clear_widget(getattr(self, name, None))
        for label in getattr(self, "hash_results", {}).values():
            label.setText("—")
        for name in ("verify_lbl", "dns_result", "ping_result", "b64_status",
                     "file_hash_lbl", "file_prog_lbl", "scan_count_lbl",
                     "scan_prog_lbl", "file_algo_warn"):
            label = getattr(self, name, None)
            if label is not None:
                label.setText("")
        self.log_entries.clear()
        self._hashes_data = {}
        self._current_file_hash = ""
        self._last_strength = None
        # On n'efface le presse-papiers que si c'est l'application qui l'a écrit.
        if self._clipboard_owned:
            try:
                clipboard = QApplication.clipboard()
                if isinstance(clipboard, QClipboard):
                    clipboard.clear()
            except Exception:
                pass
            self._clipboard_owned = False


# ════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════
# Mémorise le couple (identifiant de l'application, nom du thème) sous deux
# clés. Valeurs hétérogènes (int | str | None) : annotation pour Pylance.
_GLOBAL_STYLE_STATE: dict[str, object] = {"app": None, "theme": None}


def apply_global_style(app):
    """Applique la palette courante aux dialogues et widgets globaux."""
    key = (id(app), current_theme())
    if (_GLOBAL_STYLE_STATE["app"], _GLOBAL_STYLE_STATE["theme"]) == key:
        return
    _GLOBAL_STYLE_STATE["app"], _GLOBAL_STYLE_STATE["theme"] = key
    app.setStyleSheet(f"""
        QWidget {{ color:{PALETTE["text"]}; font-family:'{PALETTE["font_family"]}'; }}
        QToolTip {{ background-color:{PALETTE["card"]}; color:{PALETTE["text"]}; border:1px solid {PALETTE["border"]}; }}
        QMessageBox {{ background-color:{PALETTE["card"]}; color:{PALETTE["text"]}; }}
        QMessageBox QLabel {{ color:{PALETTE["text"]}; background:transparent; }}
        QMessageBox QPushButton {{
            background-color:{PALETTE["border"]}; color:{PALETTE["text"]}; padding:6px 14px; border-radius:4px;
        }}
        QComboBox QAbstractItemView {{
            background-color:{PALETTE["sidebar"]}; color:{PALETTE["text"]};
            selection-background-color:{PALETTE["accent"]}; selection-color:{PALETTE["bg"]};
        }}
    """)


def main():
    # Les indicateurs de mode restent dans sys.argv pour runtime.detect_distribution(),
    # mais ne doivent pas être interprétés comme des options Qt.
    app = QApplication([a for a in sys.argv
                        if a not in ("--portable", "--installer")])
    app.setStyle("Fusion")
    apply_global_style(app)
    window = CyberSecApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
