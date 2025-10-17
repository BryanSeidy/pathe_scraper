# pathe_scraper

Outil local d’automatisation pour extraire les horaires de séances (Pathé, Majestic, etc.), associer les films à une base locale et exporter les résultats en CSV. Conçu pour usage interactif via GUI (Tkinter) ou en mode headless via CLI.

## Fonctionnalités clés

- Navigation et parsing robustes (Selenium) pour sites Pathé et Majestic.
- Scrolling « naturel » pour charger le contenu lazy-loaded.
- Gestion des popups (cookies, annonces) et navigation sur sélecteurs/date-slider.
- Normalisation des durées et heures, extraction de showtimes par film/date.
- Matching exact et fuzzy contre une base Excel locale (movies.xlsx).
- Export CSV et journalisation (logs). Signalement des films inconnus dans `movies_to_add.txt`.
- GUI moderne (thème clair/sombre, progress bar, counts, sauvegarde) et contrôle depuis CLI (`--headless`).

## Prérequis

- Windows, Python 3.10+
- Modules Python : selenium, pandas, openpyxl, pillow
- WebDriver compatible (chromedriver/geckodriver) accessible en PATH ou géré par `driver_manager`.

Exemple d'installation minimale :

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install selenium pandas openpyxl pillow
```

Si un fichier `requirements.txt` existe :

```powershell
pip install -r requirements.txt
```

## Structure principale

- pathe_scraper.py — point d’entrée, orchestration GUI/CLI, gestion de sessions et export.
- scraper.py — navigation et parsing des pages, fonctions utilitaires (durée, horaire, scrolling).
- matcher.py — chargement/création de `movies.xlsx`, normalisation des titres, matching exact + fuzzy.
- gui.py — interface Tkinter (sélection cinéma/date, lancement, sauvegarde).
- driver_manager.py — (module attendu) gestion du cycle de vie du WebDriver.
- csv_writer.py — (module attendu) création/enregistrement des CSV.
- config.py — constantes, sélecteurs CSS, chemins (`OUTPUT_DIR`, `LOG_FILE`, `EXCEL_DB`, `CINEMAS`, ...).

## Usage

Lancer l'interface GUI (par défaut visible) :

```powershell
python pathe_scraper.py
```

Lancer en mode headless (sans interface visible du navigateur) :

```powershell
python pathe_scraper.py --headless
```

Depuis la GUI :

- Sélectionner cinéma et date → Cliquer “Lancer le scraping”.
- Filtrer / revoir les résultats → Sauvegarder (`Save` / `Save As`) pour écrire le CSV.
- À la fermeture, un CSV est généré automatiquement (si résultats).

## Entrées / Sorties

- Base de films : `movies.xlsx` (configurable via `config.EXCEL_DB`). Si absente, elle est créée automatiquement avec en-têtes attendus.
- Fichier d’alerte : `movies_to_add.txt` — liste des films non trouvés dans la DB (à ajouter manuellement).
- CSV de sortie : écrit dans `config.OUTPUT_DIR` par `csv_writer`.
- Logs : `config.LOG_FILE` (dossier `OUTPUT_DIR` créé automatiquement).

## Configuration

Ouvrir `config.py` pour :

- Définir `CINEMAS` (clé, sélecteurs, URLs, site type).
- Définir chemins (`OUTPUT_DIR`, `EXCEL_DB`, `LOG_FILE`) et timeout/IDs (`COOKIE_BTN_ID`, etc.).
- Activer `QUICK_RESCRAPE` si vous souhaitez ignorer navigation initiale pour relancer rapidement.

Ajouter un nouveau cinéma :

1. Ajouter une entrée dans `CINEMAS` avec clés : `label`, `base_url`, `cinema_link_selector`, `movie_card_selector`, `movie_title_selector`, `hour_selector`, etc.
2. Tester via GUI et ajuster sélecteurs si nécessaire.

## Bonnes pratiques / Dépannage

- Assurez-vous que le WebDriver (ex. chromedriver) correspond à la version du navigateur.
- Si les sélecteurs changent (site mis à jour), mettez à jour `config.py`.
- En cas d’erreurs WebDriver / timeouts : augmenter `config.TIMEOUT` ou exécuter en mode visible pour inspection.
- Pour les films non reconnus : ajouter manuellement dans `movies.xlsx` (colonnes `ID`, `Original title`, `Title`, `Duration`), puis relancer le matching.

## Tests et développement

- Points faciles à tester : `parse_duration`, `normalize_time`, logique de matching dans `matcher.py`.
- Suggestions : ajouter tests unitaires (pytest) pour ces utilitaires et mocks pour Selenium.

## Extension et améliorations possibles

- Migration de la DB Excel vers SQLite pour gestion ACID et concurrence.
- API REST locale pour exposer résultats aux systèmes externes.
- Scheduler / cron pour exécutions périodiques et ingestion automatique.

## Licence & Contribution

- Projet privé / interne — préciser licence si partage public.
- Contributions : fork, tests unitaires, mise à jour des sélecteurs et documentation.

---

Pour générer un README adapté à une publication publique (ajout badges, exemples de sortie CSV, captures d’écran GUI), je peux produire une version plus formelle prête à publier.// filepath: c:\Users\Admin\OneDrive\Documents\PROJECT\Python Projects\pathe_scraper\README.md

# pathe_scraper

Outil local d’automatisation pour extraire les horaires de séances (Pathé, Majestic, etc.), associer les films à une base locale et exporter les résultats en CSV. Conçu pour usage interactif via GUI (Tkinter) ou en mode headless via CLI.

## Fonctionnalités clés

- Navigation et parsing robustes (Selenium) pour sites Pathé et Majestic.
- Scrolling « naturel » pour charger le contenu lazy-loaded.
- Gestion des popups (cookies, annonces) et navigation sur sélecteurs/date-slider.
- Normalisation des durées et heures, extraction de showtimes par film/date.
- Matching exact et fuzzy contre une base Excel locale (movies.xlsx).
- Export CSV et journalisation (logs). Signalement des films inconnus dans `movies_to_add.txt`.
- GUI moderne (thème clair/sombre, progress bar, counts, sauvegarde) et contrôle depuis CLI (`--headless`).

## Prérequis

- Windows, Python 3.10+
- Modules Python : selenium, pandas, openpyxl, pillow
- WebDriver compatible (chromedriver/geckodriver) accessible en PATH ou géré par `driver_manager`.

Exemple d'installation minimale :

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install selenium pandas openpyxl pillow
```

Si un fichier `requirements.txt` existe :

```powershell
pip install -r requirements.txt
```

## Structure principale

- pathe_scraper.py — point d’entrée, orchestration GUI/CLI, gestion de sessions et export.
- scraper.py — navigation et parsing des pages, fonctions utilitaires (durée, horaire, scrolling).
- matcher.py — chargement/création de `movies.xlsx`, normalisation des titres, matching exact + fuzzy.
- gui.py — interface Tkinter (sélection cinéma/date, lancement, sauvegarde).
- driver_manager.py — (module attendu) gestion du cycle de vie du WebDriver.
- csv_writer.py — (module attendu) création/enregistrement des CSV.
- config.py — constantes, sélecteurs CSS, chemins (`OUTPUT_DIR`, `LOG_FILE`, `EXCEL_DB`, `CINEMAS`, ...).

## Usage

Lancer l'interface GUI (par défaut visible) :

```powershell
python pathe_scraper.py
```

Lancer en mode headless (sans interface visible du navigateur) :

```powershell
python pathe_scraper.py --headless
```

Depuis la GUI :

- Sélectionner cinéma et date → Cliquer “Lancer le scraping”.
- Filtrer / revoir les résultats → Sauvegarder (`Save` / `Save As`) pour écrire le CSV.
- À la fermeture, un CSV est généré automatiquement (si résultats).

## Entrées / Sorties

- Base de films : `movies.xlsx` (configurable via `config.EXCEL_DB`). Si absente, elle est créée automatiquement avec en-têtes attendus.
- Fichier d’alerte : `movies_to_add.txt` — liste des films non trouvés dans la DB (à ajouter manuellement).
- CSV de sortie : écrit dans `config.OUTPUT_DIR` par `csv_writer`.
- Logs : `config.LOG_FILE` (dossier `OUTPUT_DIR` créé automatiquement).

## Configuration

Ouvrir `config.py` pour :

- Définir `CINEMAS` (clé, sélecteurs, URLs, site type).
- Définir chemins (`OUTPUT_DIR`, `EXCEL_DB`, `LOG_FILE`) et timeout/IDs (`COOKIE_BTN_ID`, etc.).
- Activer `QUICK_RESCRAPE` si vous souhaitez ignorer navigation initiale pour relancer rapidement.

Ajouter un nouveau cinéma :

1. Ajouter une entrée dans `CINEMAS` avec clés : `label`, `base_url`, `cinema_link_selector`, `movie_card_selector`, `movie_title_selector`, `hour_selector`, etc.
2. Tester via GUI et ajuster sélecteurs si nécessaire.

## Bonnes pratiques / Dépannage

- Assurez-vous que le WebDriver (ex. chromedriver) correspond à la version du navigateur.
- Si les sélecteurs changent (site mis à jour), mettez à jour `config.py`.
- En cas d’erreurs WebDriver / timeouts : augmenter `config.TIMEOUT` ou exécuter en mode visible pour inspection.
- Pour les films non reconnus : ajouter manuellement dans `movies.xlsx` (colonnes `ID`, `Original title`, `Title`, `Duration`), puis relancer le matching.

## Tests et développement

- Points faciles à tester : `parse_duration`, `normalize_time`, logique de matching dans `matcher.py`.
- Suggestions : ajouter tests unitaires (pytest) pour ces utilitaires et mocks pour Selenium.

## Extension et améliorations possibles

- Migration de la DB Excel vers SQLite pour gestion ACID et concurrence.
- API REST locale pour exposer résultats aux systèmes externes.
- Scheduler / cron pour exécutions périodiques et ingestion automatique.

## Licence & Contribution

- Projet privé / interne — préciser licence si partage public.
- Contributions : fork, tests unitaires, mise à jour des sélecteurs et documentation.

---
