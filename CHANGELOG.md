# Changelog

Toutes les modifications notables sont consignées dans ce fichier.
Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et
[Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté
- Badge de **release** et badge de **plateformes** dans les README FR/EN/AR.
- Workflow `release.yml` : le wheel `py3-none-any` est construit puis joint
  automatiquement à la Release dès sa publication (ou à la demande pour un tag
  déjà publié, via *Actions → Release wheel → Run workflow*).
- Tests CI étendus à **macOS et Windows** en plus d’Ubuntu (Python 3.15).

### Modifié
- `requirements.dev.txt` inclut `build` : construction du paquet possible en
  local avec `python -m build --wheel`.
- Runbook `docs/RELEASE.md` mis à jour (attachement automatique du wheel).

## [1.0.0] - 2026-11-23

Première version stable publique de **CyberSec Dashboard** — Python 3.15+, PySide6,
interface FR/EN/AR, thèmes sombre et clair.

[Documentation](https://github.com/CHM2026/Local-Cybersec-Partner#readme)

### Ajouté
- Interface PySide6 avec neuf modules : scanner de ports, générateur et
  évaluateur de mots de passe, hachage de fichiers et de texte, Base64,
  informations réseau et journal d’activité.
- Internationalisation complète **français / anglais / arabe** (240 clés) avec
  bascule automatique en disposition RTL pour l’arabe et préférence mémorisée.
- Deux thèmes sélectionnables et persistés : sombre historique et **clair 2026**.
- Bouton **📸 Capture d’écran** intégré et générateur `tools/screenshots.py`
  (modes `offscreen` / `--native`, langues, thèmes et pages configurables).
- Anonymisation des captures (`DEMO-PC`, CPU factice) ; option `--real-data`
  pour un usage local.
- Documentation traduite (README FR/EN/AR), badges CI et captures d’écran
  intégrées pour les trois langues et les deux thèmes.
- Licence MIT et procédure de publication (`docs/RELEASE.md`).
- CI GitHub Actions : Python 3.15, `actions/checkout@v6`,
  `actions/setup-python@v6`, dépendances Qt système et mode `offscreen`.

### Modifié
- Journal d’activité stocké sous forme de clés i18n : les entrées existantes
  sont retraduites quand la langue change.
- Date du scanner rendue neutre (plus de texte français injecté en EN/AR).
- Style global des dialogues recalculé à chaque changement de thème, avec
  contraste automatique des boutons.

### Corrigé
- Stabilité CI : doublon de `name` supprimé, `libEGL.so.1` installé via `apt`,
  avertissements Node 20 supprimés.
- Rendu des emoji dans les captures (mode `--native`).
- `UnicodeDecodeError` du ping sous Windows (page de code OEM) et console
  fugace au lancement via `pythonw`.
- Textes invisibles dans les `QMessageBox` en thème clair.
- Fuite de langue entre tests et incohérence de version entre `pyproject.toml`
  et l’interface.

### Installation rapide

```bash
pip install "git+https://github.com/CHM2026/Local-Cybersec-Partner.git@v1.0.0"
cybersec-dashboard
```
