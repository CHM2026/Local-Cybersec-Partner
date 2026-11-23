# CyberSec Dashboard

[![Python app](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)
[![Python 3.15+](https://img.shields.io/badge/python-3.15%2B-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/Qt-PySide6%20%E2%89%A5%206.12-green.svg)](https://pypi.org/project/PySide6/)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)

> Langues : **Français** · [English](README.en.md) · [العربية](README.ar.md)

Tableau de bord local regroupant plusieurs utilitaires de cybersécurité, réalisé avec **PySide6**.

## Aperçu

Sombre (thème historique) :

![Tableau de bord en français — sombre](docs/screenshots/dashboard-fr-dark.png)

Clair 2026 :

![Tableau de bord en français — clair 2026](docs/screenshots/dashboard-fr-light.png)

> ⚠️ **Prérequis : Python 3.15 ou supérieur.** Le code utilise la syntaxe `lazy import` (PEP 810) et les f-strings imbriquées (PEP 701). Sur Python ≤ 3.14, le lancement échoue avec un `SyntaxError`.

## Installation

Python 3.15 ou supérieur est requis. Selon votre système :

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Sur Windows, si `python` pointe vers une version antérieure, utilisez `py -3.15` à la place.

Pour le développement (tests inclus), remplacez `requirements.txt` par `requirements.dev.txt` dans la commande d’installation.

## Lancement

```powershell
# Windows
.\.venv\Scripts\python.exe main.py
```

```bash
# macOS / Linux
./.venv/bin/python main.py
```

Si le projet a été installé avec `pip install -e .` :

```bash
cybersec-dashboard
```

## Modules

| Module | Description |
|---|---|
| ⬡ Tableau de bord | Informations système et accès priorisé aux modules |
| 🔑 Mots de Passe | Génération CSPRNG via `secrets` (longueur, jeu de caractères, quantité) |
| 💪 Force du MDP | Analyse des critères, score, entropie indicative |
| 🔒 Hachage | MD5, SHA-1, SHA-256, SHA-384, SHA-512 d'un texte |
| 📄 Intégrité Fichier | Empreinte de fichier (hors thread GUI) et comparaison avec un hash de référence |
| 🔍 Scanner Ports | Scan TCP Connect d'une plage de ports (hôte résolu et timeout validés) |
| ⚙️ Base64 | Encodage/décodage strict, avec affichage hexadécimal des données binaires |
| 🌐 Réseau | Informations locales, résolution DNS asynchrone, ping |
| 📋 Journal | Historique des actions, effacement et export texte |

## Multilingue (FR / EN / AR)

Le sélecteur **🌐 Langue** en bas de la sidebar permet de basculer entre **Français**, **English** et **العربية**. Le choix est mémorisé (`QSettings`) et restauré au prochain lancement.

- **Interface complète** : titres, libellés, boutons, messages, infobulles et saisies du journal sont traduits.
- **Journal rétroactif** : les entrées sont stockées sous forme de clés avec leurs paramètres ; elles sont retraduites à l'affichage lors d'un changement de langue, y compris dans l'export texte.
- **RTL automatique** : sélectionner l'arabe inverse la disposition de l'interface (`RightToLeft`) et les alignements (`text-align: start`).
- **Préservation de l'état** : les saisies en cours sont conservées et les résultats recalculés sans créer de nouvelle entrée de journal.

Pour ajouter ou corriger une traduction, éditez `src/i18n.py` : chaque clé du dictionnaire `STRINGS` contient le triplet `(français, english, العربية)`.

## Thèmes

Deux palettes sont disponibles via le sélecteur **🎨 Thème** de la barre latérale :

- **Sombre** : le thème cyber historique (fond `#0d1117`, accents vert/cyan).
- **Clair 2026** : palette moderne sur fond clair `#f6f8fb`, accents bleu/cyan et typographie `Segoe UI`.

Le choix est mémorisé (`QSettings`) et restauré au lancement. Le bouton **📸 Capture d'écran** enregistre le rendu courant en PNG.

## Sécurité et périmètre

- Aucun mot de passe, fichier ou hash n'est envoyé à un service tiers : tout est traité localement.
- Le scan de ports, la résolution DNS et le ping contactent **uniquement la cible que vous saisissez**.
- N'utilisez le scanner que sur des hôtes que vous possédez ou que vous êtes expressément autorisé à tester.
- MD5 et SHA-1 sont conservés à des fins de compatibilité ; **SHA-256 est recommandé** pour toute vérification d'intégrité.
- Le journal exporté est un fichier texte non chiffré : ne le stockez pas dans un emplacement partagé.
- À la fermeture, l'application arrête ses threads et efface les données sensibles (champs, empreintes, journal, presse-papiers si l'application en était l'auteure).

## Tests

```powershell
# Windows
.\.venv\Scripts\python.exe -m pytest
```

```bash
# macOS / Linux
./.venv/bin/python -m pytest
```

Les tests s'exécutent en mode Qt `offscreen` : aucune fenêtre n'est ouverte.

## Captures d'écran

- **Depuis l’application** : cliquez sur **📸 Capture d'écran** dans la barre latérale, puis choisissez le fichier PNG de destination.
- **Depuis le terminal** (idéal pour la documentation et la CI) :

```bash
python tools/screenshots.py
python tools/screenshots.py --native --theme light
python tools/screenshots.py --pages dashboard,scanner --out docs/screenshots
```

Le script génère `docs/screenshots/<page>-<langue>.png` pour le français, l’anglais et l’arabe. Par défaut, il tourne en mode `offscreen` (aucune fenêtre, idéal en CI), mais les emoji y sont rendus en monochrome.

Pour obtenir des captures avec les **emoji en couleur**, ajoutez `--native` (un affichage est nécessaire) :

```bash
python tools/screenshots.py --native
```

Les images présentées ci-dessus ont été générées avec `--native`. Sur Windows, utilisez `.\.venv\Scripts\python.exe tools\screenshots.py --native` si nécessaire.

## Structure

```
main.py              Application (fenêtre, pages, threads de travail)
src/constants.py     Palette, table des ports, nom et version de l'app
src/i18n.py          Dictionnaires FR/EN/AR, moteur de traduction, sélecteur RTL
tests/               Tests automatisés
tools/screenshots.py Générateur de captures FR/EN/AR (hors écran)
requirements.txt     Dépendance d'exécution
requirements.dev.txt Dépendances de développement
pyproject.toml       Métadonnées, script d'entrée, configuration pytest
```
