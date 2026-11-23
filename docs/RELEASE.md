# Procédure de publication — v1.0.0

Ce runbook prépare la diffusion de la version **1.0.0** de Local-Cybersec-Partner.
Il ne crée **aucun tag automatiquement** : chaque commande est à exécuter
volontairement, dans l’ordre indiqué.

## 1. État du dépôt au moment de la préparation

| Élément | État constaté |
| --- | --- |
| Branche | `main`, synchronisée avec `origin/main`, arbre de travail propre |
| Dernier commit avant préparation | `9c7d58d` — captures anonymisées |
| CI GitHub Actions | run **#17 = success** sur `9c7d58d`, aucun avertissement Node 20 |
| Tests locaux | **34 passed** en mode Qt `offscreen` |
| Internationalisation | 240 clés, triplet FR/EN/AR complet pour chacune |
| Version | `pyproject.toml` = `1.0.0`, `APP_VERSION` aligné sur `1.0.0` |
| Packaging | wheel `py3-none-any` généré avec succès (`pip wheel . --no-deps`) |
| Licence | MIT (`LICENSE`) |
| Journal des changements | `CHANGELOG.md` (section `1.0.0`) |
| Tags / Releases GitHub | **aucun** ; `v1.0.0` sera le premier |
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

### 4.4 Construire le paquet (vérification optionnelle)

```powershell
# Windows
.\.venv\Scripts\python.exe -m pip wheel . --no-deps -w dist
```

```bash
# macOS / Linux
./.venv/bin/python -m pip wheel . --no-deps -w dist
```

Le dossier `dist/` est ignoré par Git : le wheel ne sera pas commité. Vous
pourrez le joindre à la Release GitHub si vous le souhaitez.

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
4. Cocher **Set as a latest release**.
5. Optionnel : joindre le wheel `dist/local_cybersec_partner-1.0.0-py3-none-any.whl`.
6. Cliquer sur **Publish release**.

Note : l’utilitaire `gh` n’est pas installé sur la machine de préparation ; la
procédure ci-dessus utilise donc l’interface web. Si `gh` est installé plus
tard, l’équivalent est :

```bash
gh release create v1.0.0 --title "v1.0.0 — CyberSec Dashboard" --notes-file CHANGELOG.md dist/*.whl
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
- l’installation depuis le tag dans un environnement neuf (optionnel) :

```bash
python -m pip install "git+https://github.com/CHM2026/Local-Cybersec-Partner.git@v1.0.0"
cybersec-dashboard
```

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
