# ════════════════════════════════════════════════════════════
#  PALETTES CYBERSÉCURITÉ — sombre (historique) et clair 2026
# ════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "bg"      : "#0d1117",
        "sidebar" : "#161b22",
        "card"    : "#21262d",
        "accent"  : "#00ff88",
        "accent2" : "#00d4ff",
        "danger"  : "#ff4444",
        "warning" : "#ffaa00",
        "text"    : "#e6edf3",
        "dim"     : "#8b949e",
        "border"  : "#30363d",
        "hover"   : "#444c56",
        "success" : "#3fb950",
        "purple"  : "#bc8cff",
        "font_family" : "Consolas",
        "font_mono"   : "Courier New",
    },
    "light": {
        "bg"      : "#f6f8fb",
        "sidebar" : "#ffffff",
        "card"    : "#ffffff",
        "accent"  : "#2563eb",
        "accent2" : "#0891b2",
        "danger"  : "#dc2626",
        "warning" : "#d97706",
        "text"    : "#0f172a",
        "dim"     : "#64748b",
        "border"  : "#e2e8f0",
        "hover"   : "#e8eef7",
        "success" : "#059669",
        "purple"  : "#7c3aed",
        "font_family" : "Segoe UI",
        "font_mono"   : "Cascadia Mono",
    },
}

_CURRENT_THEME = "dark"

# Objet partagé : main.py importe ce dictionnaire, donc une mutation sur place
# suffit à habiller toute l'application sans reconstruire les modules.
PALETTE = dict(THEMES["dark"])


def current_theme():
    """Renvoie le nom du thème actif."""
    return _CURRENT_THEME


def set_theme(name):
    """Applique un thème en place et renvoie son nom réellement activé."""
    global _CURRENT_THEME
    key = name if name in THEMES else "dark"
    PALETTE.clear()
    PALETTE.update(THEMES[key])
    _CURRENT_THEME = key
    return key


COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
    6379: "Redis", 9200: "Elasticsearch", 5000: "Flask",
    8888: "Jupyter", 2181: "Zookeeper", 9092: "Kafka",
}

APP_NAME = "CyberSec Dashboard"
APP_VERSION = "1.1.0"
