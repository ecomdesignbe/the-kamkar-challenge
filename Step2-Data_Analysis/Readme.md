# Clean HackerOne Domains

## 🎯 Objectif
Ce projet implémente l’étape 2 du challenge : **nettoyer et valider les domaines extraits des programmes HackerOne** à partir du fichier `programs.json`.  
L’objectif est d’obtenir une liste propre, normalisée et vérifiée de domaines actifs, enregistrée dans un fichier texte `domains.txt`.

Le script respecte les contraintes du challenge et expose trois fonctions principales :

- **`extract_domains(programs_filename)`** : extrait tous les domaines syntaxiquement valides à partir du JSON.  
- **`check_domains(domains_list)`** : vérifie quels domaines sont actifs (résolvent une IP).  
- **`clean_domains(programs_filename="programs.json")`** : orchestre l’ensemble : extraction → vérification → sauvegarde.

---

## 🧩 Bonus implémentés
Le script inclut également les améliorations bonus :

- **Auto-correction des domaines** : `normalize_domain()` supprime les erreurs courantes (schemes HTTP/HTTPS, ports, caractères invalides, punycode, etc.).  
- **Expansion des wildcards** : `expand_wildcard()` génère des sous-domaines usuels (`www`, `api`, `dev`, `login`, etc.).  
- **Multithreading DNS** : `check_domains()` utilise un `ThreadPoolExecutor` pour accélérer la vérification des domaines actifs.

---

## ⚙️ Prérequis
- **Python 3.8+** (recommandé 3.10+)  
- Aucune dépendance externe : tout repose sur la bibliothèque standard (`json`, `re`, `socket`, `concurrent.futures`, `urllib.parse`)

---

## 🚀 Exécution
### 1️⃣ Extraction + vérification complète
```bash
python3 clean_hackerone_domains.py
python3 clean_hackerone_domains_v2.py (incl. bonus)
```
---

## 📁 Fichier de sortie attendu
Le fichier `domains.txt` contient la liste finale des domaines **actifs**, un par ligne, sans doublons.  
Exemple :

```
tax.audible.com
www.mimeridian.com
api.tmall.com
www.taobao.com
www.centenepharmacy.com
```

---

## 🔐 Sécurité et bonnes pratiques
- Projet purement pédagogique : respecte les règles de HackerOne et la législation.  
- Ne pas utiliser les domaines collectés pour des tests non autorisés.  
- La vérification DNS est passive et sans impact sur les cibles.

