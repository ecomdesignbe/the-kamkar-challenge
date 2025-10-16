# Active Targets Finder

## Objectif

Ce projet implémente un petit outil pour détecter quels domaines d'une liste (`domains.txt`) présentent des services actifs pour HTTP, HTTPS et SSH.  
L'idée est d'obtenir des listes propres et vérifiées de cibles actives pour ces services, et d'enregistrer les résultats dans des fichiers texte séparés : `http.txt`, `https.txt` et `ssh.txt`.

Le script est simple, modulaire et conçu pour être intégré dans un workflow (par exemple Ghostools). Il propose une interaction utilisateur pour définir le port à scanner pour chaque service avant d'exécuter les tests.

---

## Fonctions exposées

Le script (version V3) comprend les fonctions principales suivantes :

### `http_check(domain: str, port: int = 80) -> bool`  
Vérifie si un service HTTP répond sur le port indiqué (construit l'URL `http://domain:port` et teste la réponse).

### `https_check(domain: str, port: int = 443) -> bool`  
Vérifie si un service HTTPS répond sur le port indiqué (construit l'URL `https://domain:port` et teste la réponse, `verify=False` pour ignorer les certificats non valides).

### `ssh_check(domain: str, port: int = 22) -> bool`  
Tente une connexion TCP sur le port indiqué (utilise `socket.create_connection`) pour déterminer si le port SSH est ouvert.

### `run_check(check_function, domains, output_file, port)`  
Exécute la fonction de vérification en multithreading (`ThreadPoolExecutor`) sur la liste de domaines et sauvegarde les cibles actives dans `output_file`. Chaque entrée est sauvegardée sous la forme `domain:port`.

### `main()`  
Charge `domains.txt`, demande à l'utilisateur les ports à scanner pour HTTP/HTTPS/SSH (touche Entrée = port par défaut), puis lance les vérifications et écrit les fichiers de sortie (`http.txt`, `https.txt`, `ssh.txt`).

---

## Bonus / fonctionnalités ajoutées

- Interaction utilisateur pour saisir le port à scanner pour chaque service (HTTP, HTTPS, SSH).  
  Si l'utilisateur presse Entrée, le port par défaut est utilisé (80, 443, 22).

- Multithreading pour accélérer les vérifications (configurable via `MAX_THREADS`).

- Timeout configurable (`TIMEOUT`) pour éviter d'attendre indéfiniment des cibles non réactives.

- Résultats sauvegardés en format `domain:port` (utile si on scanne des ports non standard).

---

## Prérequis

- Python 3.8+ (recommandé 3.10+)

- Dépendances : `requests` (installable via `pip install requests`) — le script utilise `requests` pour HTTP/HTTPS et la stdlib `socket` pour SSH.

---

## Exécution

```bash
python3 active_targets_v3.py
```

Le script demandera :

```
Entrez le port HTTP à scanner (par défaut 80) :
Entrez le port HTTPS à scanner (par défaut 443) :
Entrez le port SSH à scanner (par défaut 22) :
```

Appuie sur Entrée pour utiliser le port par défaut ou entre un nombre pour scanner un port personnalisé (ex. `8080`, `8443`, `2222`).

3. À la fin, il y aura trois fichiers créés/modifiés :

- `http.txt`  — domaines actifs pour HTTP (format `domain:port`)  
- `https.txt` — domaines actifs pour HTTPS (format `domain:port`)  
- `ssh.txt`   — domaines avec port SSH ouvert (format `domain:port`)

---

## Exemple de sortie attendue (`http.txt` / `https.txt` / `ssh.txt`)

```
example.com:80
www.mimeridian.com:8080
192.168.1.5:22
```

---

## Sécurité et bonnes pratiques

- Outil pédagogique et d'inventaire passif : **n'exécute de tests actifs que sur des cibles autorisées**.  
- Respecte les règles et les politiques applicables (propriété, programme de bug bounty, contrat, loi).  
- La vérification HTTP/HTTPS envoie des requêtes — ne l'utilise pas pour effectuer des scans intrusifs ou des attaques.  
- Pour des audits plus avancés, privilégie des contrôles autorisés et des environnements de test.

---

