# Procédure de publication — v1.0.0

Ce runbook prépare la diffusion de la version **1.0.0** de Local-Cybersec-Partner
(les procédures spécifiques à **v1.1.0** et **v1.1.1** sont résumées aux
sections 7 et 9).
Il ne crée **aucun tag automatiquement** : chaque commande est à exécuter
volontairement, dans l’ordre indiqué.

## 1. État du dépôt au moment de la préparation

| Élément | État constaté |
| --- | --- |
| Branche | `main`, synchronisée avec `origin/main`, arbre de travail propre |
| Dernier commit avant préparation | `9c7d58d` — captures anonymisées |
| CI GitHub Actions | matrice **Ubuntu / macOS / Windows**, Python 3.15, aucun avertissement Node 20 |
| Tests locaux | **34 passed** en mode Qt `offscreen` |
| Internationalisation | 240 clés, triplet FR/EN/AR complet pour chacune |
| Version | `pyproject.toml` = `1.0.0`, `APP_VERSION` aligné sur `1.0.0` |
| Packaging | wheel `py3-none-any` construit et joint par le workflow `Release wheel` |
| Licence | MIT (`LICENSE`) |
| Journal des changements | `CHANGELOG.md` (section `1.0.0`) |
| Tags / Releases GitHub | `v1.0.0` publié et marqué *Latest* |
| Visibilité du dépôt | public |
| Captures | 6 PNG anonymisés (`DEMO-PC`, CPU factice) |

## 2. Version finale retenue

**`v1.0.0`** (SemVer) — première version stable publique.

- `1` : API publique stable (point d’entrée `cybersec-dashboard`, 9 modules).
- `0` : aucune modification incompatible prévue dans cette lignée.
- `0` : première publication.

Le nom de version est centralisé en deux endroits qui doivent rester égaux :

- `pyproject.toml` → `version = "1.0.0"` (utilisé par pip / la Release) ;
- `src/constants.py` → `APP_VERSION = "1.0.0"` (affiché dans l’interface).

Un test de non-régression vérifie cette égalité.

## 3. Checklist avant publication

- [x] Version alignée dans `pyproject.toml` et `src/constants.py`
- [x] Licence MIT ajoutée
- [x] `CHANGELOG.md` à jour
- [x] CI verte sur le dernier commit
- [x] Captures anonymisées et régénérées
- [x] Tests locaux au vert (34)
- [ ] Dernier essai manuel : FR / EN / AR, thèmes sombre et clair, ping, capture
- [ ] `git status -sb` affiche uniquement `## main...origin/main`

## 4. Publication

### 4.1 Se placer à la racine du dépôt

```powershell
# Windows (PowerShell)
cd C:\Users\LITE\Desktop\Programmation\Local-Cybersec-Partner
```

```bash
# macOS / Linux
cd /chemin/vers/Local-Cybersec-Partner
```

### 4.2 Synchroniser et tester

```powershell
# Windows
git status -sb
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pytest -q
```

```bash
# macOS / Linux
git status -sb
git pull --ff-only origin main
./.venv/bin/python -m pytest -q
```

Résultat attendu : `34 passed` et `## main...origin/main`.

### 4.3 Confirmer la CI

Ouvrir <https://github.com/CHM2026/Local-Cybersec-Partner/actions> et vérifier
que le dernier run sur `main` est **success**. Ne pas publier si la CI est rouge.

### 4.4 Construire le paquet (automatique)

Le workflow **`Release wheel`** (`.github/workflows/release.yml`) construit le
wheel et le joint à la Release dès sa publication. Rien à faire manuellement.

Pour vérifier le paquet en local avant de publier :

```powershell
# Windows
.\.venv\Scripts\python.exe -m pip install -r requirements.dev.txt
.\.venv\Scripts\python.exe -m build --wheel
```

```bash
# macOS / Linux
./.venv/bin/python -m pip install -r requirements.dev.txt
./.venv/bin/python -m build --wheel
```

Le dossier `dist/` est ignoré par Git : le wheel n’est jamais commité. Le paquet
est pur Python (`py3-none-any`) : un seul wheel fonctionne sur Windows, macOS et
Linux.

Pour les versions qui publient des exécutables, joindre aussi un fichier
`SHA256SUMS.txt` listant `<empreinte>  <nom de l'artefact>` pour chaque ZIP et
`-setup.exe` : le vérificateur intégré à l'application l'utilise pour refuser un
téléchargement corrompu. En son absence, le téléchargement reste possible mais
est signalé comme non vérifié.

Le workflow **`Build Windows executables`**
(`.github/workflows/build-windows.yml`) construit ces artefacts sur
`windows-latest` (PyInstaller `--onedir` puis Inno Setup 6) et les joint à la
Release dès sa publication. Comme `Release wheel`, il accepte un `tag` en
déclenchement manuel (onglet **Actions → Build Windows executables → Run
workflow**) pour compléter une Release déjà publiée. Le tag doit toujours être
de la forme `v<version pyproject.toml>` : le workflow refuse un décalage.

### 4.5 Créer le tag annoté

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git tag -n
git show --stat v1.0.0
```

Un tag annoté est préférable à un tag léger : il porte auteur, date et message.
Vérifier qu’il pointe bien sur le commit contenant la version `1.0.0`.

### 4.6 Pousser le commit puis le tag

```bash
git push origin main
git push origin v1.0.0
```

Alternative équivalente : `git push --follow-tags origin main`.
**Ne jamais utiliser `--force`** sur `main` ni sur le tag.

### 4.7 Créer la Release GitHub

1. Ouvrir <https://github.com/CHM2026/Local-Cybersec-Partner/releases/new?tag=v1.0.0>.
2. Titre : `v1.0.0 — CyberSec Dashboard`.
3. Description : copier la section `[1.0.0]` de `CHANGELOG.md`.
4. Label : **None** (le choix *Pre-release* est réservé aux bêta / RC).
5. Cliquer sur **Publish release**.

Le wheel est ajouté **automatiquement** par le workflow `Release wheel` quelques
secondes après la publication : il n’y a pas d’attachement manuel à faire.

Pour un tag déjà publié avant la mise en place du workflow (cas de `v1.0.0`),
déclencher le workflow à la main :

1. Onglet **Actions** → workflow **Release wheel** → **Run workflow**.
2. Renseigner le champ `tag` avec `v1.0.0`.
3. Le wheel est construit depuis ce tag et joint à la Release existante.

Note : l’utilitaire `gh` n’est pas installé sur la machine de préparation ; la
procédure ci-dessus utilise donc l’interface web. Si `gh` est installé plus
tard, l’équivalent est :

```bash
gh release create v1.0.0 --title "v1.0.0 — CyberSec Dashboard" --notes-file CHANGELOG.md
gh workflow run release.yml -f tag=v1.0.0
```

### 4.8 Vérifications après publication

```bash
git ls-remote --tags origin
git log -1 --decorate
```

Attendu : `refs/tags/v1.0.0` apparaît et le commit `HEAD` est étiqueté `tag: v1.0.0`.
Vérifier aussi :

- la page <https://github.com/CHM2026/Local-Cybersec-Partner/releases/tag/v1.0.0> ;
- le badge de CI du README (il doit rester *passing*) ;
- le badge de release (il doit afficher `v1.0.0`) ;
- le run **Release wheel** au vert et le wheel présent dans **Assets** ;
- le run **Build Windows executables** au vert et, dans **Assets**, le ZIP
  `-portable.zip`, le `-setup.exe` et `SHA256SUMS.txt` ;
- l’installation depuis le tag dans un environnement neuf (optionnel) :

```bash
python -m pip install "git+https://github.com/CHM2026/Local-Cybersec-Partner.git@v1.0.0"
cybersec-dashboard
```

Sur Windows, utiliser `py -3.15` à la place de `python` si nécessaire. Si la
commande `cybersec-dashboard` n’est pas reconnue, `py -3.15 -m main` fonctionne
sans configuration (voir la section « Lancement » du README).

## 5. Annulation (uniquement avant diffusion large)

```bash
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

Puis supprimer la Release depuis l’interface GitHub. Le commit reste sur `main` :
il n’y a pas de code à annuler.

⚠️ Une fois la Release diffusée, **ne déplacez pas le tag**. Pour un correctif,
créez `v1.0.1` : mettez à jour les deux numéros de version, ajoutez une section
dans `CHANGELOG.md`, puis suivez à nouveau la section 4.

## 6. Notes de confidentialité

Les anciennes versions des captures contenaient le nom réel de la machine. Elles
restent présentes dans l’historique Git (décision : ne pas réécrire l’historique).
Le tag `v1.0.0` pointe, lui, sur l’arbre propre avec les six captures anonymisées.

## 7. Publication de v1.1.0

La procédure générale ci-dessus reste valable ; seules les valeurs changent :

1. Vérifier `pyproject.toml` (`version = "1.1.0"`) et `src/constants.py`
   (`APP_VERSION = "1.1.0"`), puis `pytest` (**54 tests**) et la CI sur `main`.
2. Publier le commit, créer le tag annoté `v1.1.0` et le pousser.
3. Créer la Release GitHub `v1.1.0` : titre `v1.1.0 — CyberSec Dashboard`,
   description = section `[1.1.0]` du `CHANGELOG.md`, label **None**.
4. Les workflows **`Release wheel`**, **`Build Windows executables`** et
   **`Publish to PyPI`** se déclenchent automatiquement. Vérifier dans **Assets** :
   `local_cybersec_partner-1.1.0-py3-none-any.whl`,
   `CyberSecDashboard-1.1.0-portable.zip`,
   `CyberSecDashboard-1.1.0-setup.exe` et `SHA256SUMS.txt`.
5. Mettre à jour le badge **Release** dans les trois README (FR/EN/AR) : le badge
   est statique (`img.shields.io/badge/release-vX.Y.Z-blue.svg`) car le badge
   dynamique `github/v/release/...` renvoie un 504 via le proxy d'images de
   GitHub. Mettre aussi à jour le badge `tests-N passed` si le nombre de tests
   change.
6. Ne jamais déplacer `v1.0.0` : les correctifs ultérieurs iront dans `v1.1.1`.

## 8. Publication sur PyPI

Le paquet est distribué sous le nom **`local-cybersec-partner`** (nom libre sur
PyPI au 23/11/2026). Le workflow `.github/workflows/publish-pypi.yml` construit
le wheel **et** le sdist, valide les métadonnées avec `twine check`, puis les
dépose sur PyPI avec un **token API** stocké dans le secret GitHub
`PYPI_API_TOKEN`.

### Configuration unique à faire

1. Créer un compte sur <https://pypi.org/account/register/>, vérifier l'adresse
   e-mail et activer la 2FA.
2. Ouvrir <https://pypi.org/manage/account/token/> et créer un token :
   - **pour la première publication**, portée **« Tous les projets »** — le projet
     n'existe pas encore sur PyPI, un token limité à un projet serait refusé ;
   - après la première publication, le remplacer par un token limité au projet
     `local-cybersec-partner` (moins de privilèges).
3. Copier le token (`pypi-...`) et l'ajouter dans le dépôt GitHub :
   *Settings → Secrets and variables → Actions → New repository secret*,
   nom exact **`PYPI_API_TOKEN`**. L'alias `CHM2026_token` est également accepté
   par le workflow si c'est le nom donné au secret. Le secret est masqué dans
   les logs.

> **Pourquoi pas l'OIDC ?** Le *trusted publisher* a d'abord été essayé mais a
> échoué avec `invalid-publisher` : le nom de dépôt saisi sur PyPI était en
> minuscules (`local-cybersec-partner`) alors que GitHub envoie
> `Local-Cybersec-Partner`, et PyPI compare ce champ **sensiblement à la casse**.
> Pour utiliser l'OIDC plus tard (optionnel), supprimer l'ancienne fiche PyPI,
> la recréer avec exactement `Local-Cybersec-Partner`, puis retirer `password:`
> de l'étape de publication et ajouter `permissions: id-token: write` au job.

### Publier

- **Automatiquement** : publier une Release GitHub. Le workflow vérifie que le tag
  est bien `v<version du pyproject.toml>`, puis publie sur PyPI.
- **Manuellement** : *Actions → Publish to PyPI → Run workflow*, champ `tag` =
  `v1.1.0`. C'est la méthode à utiliser **pour la première publication de v1.1.0**,
  car la Release est déjà publiée (le workflow n'a pas pu se déclencher
  rétroactivement).

Vérification : <https://pypi.org/project/local-cybersec-partner/> puis
`py -3.15 -m pip install local-cybersec-partner` dans un environnement propre.

⚠️ PyPI est immuable : une version publiée ne peut pas être remplacée. Toute
correction après publication doit porter un nouveau numéro (`v1.1.1`, etc.).

Le secret est vérifié par une étape dédiée avant la publication : s'il est
absent, le workflow échoue avec un message explicite plutôt qu'au moment de
l'envoi.

## 9. Publication de v1.1.1

Version de maintenance : traduction des dialogues Qt, finalisation de la
publication PyPI et corrections documentaires. La procédure générale reste
celle des sections 1 à 6 et 8.

1. Vérifier `pyproject.toml` (`version = "1.1.1"`) et `src/constants.py`
   (`APP_VERSION = "1.1.1"`), `installer/CyberSecDashboard.iss`
   (`AppVersion = "1.1.1"`), puis `pytest` (**54 tests**) et la CI sur `main`.
2. Vérifier que le badge Release des trois README est sur `release-v1.1.1` et
   que le `[Non publié]` du `CHANGELOG.md` est vide (tout est passé dans
   `[1.1.1]`).
3. Publier le commit, créer le tag annoté `v1.1.1` et le pousser :
   `git tag -a v1.1.1 -m "v1.1.1 — CyberSec Dashboard" && git push origin v1.1.1`.
4. Créer la Release GitHub `v1.1.1` : titre `v1.1.1 — CyberSec Dashboard`,
   description = section `[1.1.1]` du `CHANGELOG.md`, label **None**.
5. Les workflows **`Release wheel`**, **`Build Windows executables`** et
   **`Publish to PyPI`** se déclenchent automatiquement. Vérifier dans **Assets** :
   `local_cybersec_partner-1.1.1-py3-none-any.whl`,
   `CyberSecDashboard-1.1.1-portable.zip`,
   `CyberSecDashboard-1.1.1-setup.exe` et `SHA256SUMS.txt`, puis la page
   <https://pypi.org/project/local-cybersec-partner/> (version 1.1.1).
6. Ne jamais déplacer `v1.0.0` ni `v1.1.0` : les artefacts des versions
   publiées sont immuables.

