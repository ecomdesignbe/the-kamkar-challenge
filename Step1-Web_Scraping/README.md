# Scraper HackerOne

## Objectif
Ce projet implémente l’étape 1 du challenge : **récupérer la liste des scopes des programmes HackerOne** et sauvegarder le résultat dans un fichier JSON `programs.json`.  
Le script respecte les contraintes du challenge et expose trois fonctions principales :

- `get_programs_list()` : retourne la liste des handles (ex. `audible`, `alibaba_vdp`, ...)
- `get_scope(program_handle)` : extrait pour un programme donné les cibles du scope (domaines, URLs, wildcards)
- `scrape_hackerone()` : orchestre la collecte pour tous les handles et écrit `programs.json`

---

## Prérequis

1. Python 3.8+ (recommandé 3.10+)
2. Virtualenv (optionnel mais recommandé)

Installer Playwright et dépendances :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install playwright
python -m playwright install
```

> `pip install playwright` puis `python -m playwright install`

---

## Exécution

```bash
python3 scrape_hackerone_full.py
```

Ou pour tester un handle précis :

```bash
python3 - <<'PY'
from scrape_hackerone_full import get_scope
print(get_scope("audible"))
PY
```


## Format attendu de `programs.json`

Le fichier doit être un JSON avec la structure suivante :

```json
{
  "audible": {
    "domains": ["tax.audible.com"]
  },
  "alibaba_vdp": {
    "wildcards": ["www.lazada.*sixcountry", "*.youku.com"]
  },
  "centene_vdp": {
    "domains": ["www.mimeridian.com"],
    "wildcards": ["*.ambetterhealth.com"],
    "urls": ["https://www.centenepharmacy.com"]
  }
}
```

Les clés possibles pour chaque programme sont `domains`, `urls`, `wildcards`. Les autres catégories (smart contracts, mobile apps, etc.) sont ignorées.

---

## Détails des fonctions (conforme au challenge)

### `get_programs_list(timeout: int = 30) -> List[str]`
- Rend la page `https://hackerone.com/directory/programs`.
- Effectue un scroll pour charger dynamiquement les vignettes (infinite scroll).
- Extrait les `href` relatifs et normalise en handles (ex. `/audible` → `audible`).
- Retourne une liste triée de handles uniques.

### `get_scope(program_handle: str, timeout: int = 20) -> Dict[str, List[str]]`
- Rend la page du programme `https://hackerone.com/{program_handle}`.
- Tente d’ouvrir l’onglet / section **Scope** (ou `In scope`, `Eligible`).
- Extrait des lignes et les classifie en `domains`, `urls`, `wildcards` via des heuristiques (regex).
- Ne conserve que les cibles marquées/visibles : évite les URLs HackerOne internes.

### `scrape_hackerone(save_path: str = "programs.json", handles: Optional[List[str]] = None)`
- Orchestrateur : si `handles` absent, appelle `get_programs_list()`.
- Pour chaque handle, appelle `get_scope` et agrège le résultat.
- Sauvegarde l’agrégation dans `programs.json`.

---

## Sécurité et respect des règles
- Ce script est destiné à un usage pédagogique / challenge. Respecte les conditions d’utilisation de HackerOne et la législation locale.  
- N’utilise pas les données récoltées pour des actions non autorisées.

---

## Améliorations possibles (bonus)
- Ne conserver que les cibles explicitement marquées *In Scope* et *Eligible*.
- Paralléliser la collecte (ThreadPoolExecutor).
- Supporter d’autres plateformes de bug-bounty (Bugcrowd, Intigriti, ...).
- Intercepter les requêtes réseau pour capturer les réponses JSON.



