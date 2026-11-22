# ════════════════════════════════════════════════════════════
#  PALETTE CYBERSÉCURITÉ (thème sombre) — identique à la version Tkinter
# ════════════════════════════════════════════════════════════

PALETTE = {
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
    "success" : "#3fb950",
    "purple"  : "#bc8cff",
    "font_family" : "Consolas",
    "font_mono"   : "Courier New"
    
}

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
    6379: "Redis", 9200: "Elasticsearch", 5000: "Flask",
    8888: "Jupyter", 2181: "Zookeeper", 9092: "Kafka",
}

APP_NAME = "CyberSec Dashboard"
APP_VERSION = "1.0"