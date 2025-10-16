#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Active Targets Finder
=====================
Vérifie quels domaines listés dans domains.txt sont actifs pour :
 - HTTP  (port 80)
 - HTTPS (port 443)
 - SSH   (port 22)

Résultats : http.txt, https.txt, ssh.txt
"""

import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----- Configuration -----
INPUT_FILE = "domains.txt"   # Fichier contenant la liste des domaines à tester
HTTP_FILE = "http.txt"       # Fichier de sortie pour les domaines HTTP actifs
HTTPS_FILE = "https.txt"     # Fichier de sortie pour les domaines HTTPS actifs
SSH_FILE = "ssh.txt"         # Fichier de sortie pour les domaines SSH actifs
TIMEOUT = 3                  # Délai d’attente (en secondes) avant de considérer une cible comme inactive
MAX_THREADS = 20             # Nombre maximum de threads pour exécuter les vérifications en parallèle


# ----- Fonctions de vérification -----
def http_check(domain: str) -> bool:
    """Vérifie si le service HTTP (port 80) du domaine est actif."""
    url = f"http://{domain}"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        return r.status_code < 400  # Considère le domaine actif si le code HTTP est inférieur à 400
    except Exception:
        return False  # Retourne False si la requête échoue ou dépasse le délai


def https_check(domain: str) -> bool:
    """Vérifie si le service HTTPS (port 443) du domaine est actif."""
    url = f"https://{domain}"
    try:
        r = requests.get(url, timeout=TIMEOUT, verify=False)  # verify=False ignore les certificats SSL invalides
        return r.status_code < 400
    except Exception:
        return False


def ssh_check(domain: str) -> bool:
    """Vérifie si le port SSH (22) du domaine est ouvert."""
    try:
        with socket.create_connection((domain, 22), timeout=TIMEOUT):
            return True  # Connexion réussie → port ouvert
    except Exception:
        return False  # Erreur ou délai dépassé → port fermé/inaccessible


# ----- Fonction utilitaire -----
def run_check(check_function, domains, output_file):
    """
    Exécute une vérification donnée (HTTP, HTTPS ou SSH)
    sur une liste de domaines en multithreading, puis
    enregistre les domaines actifs dans un fichier.
    """
    print(f"\n[*] Exécution de {check_function.__name__}...")
    active = []  # Liste des domaines actifs détectés

    # Utilisation d’un pool de threads pour accélérer les vérifications
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Soumet chaque vérification en tâche parallèle
        futures = {executor.submit(check_function, d): d for d in domains}
        for future in as_completed(futures):  # Parcourt les résultats au fur et à mesure
            domain = futures[future]
            try:
                if future.result():  # Si la vérification retourne True
                    print(f"[+] {domain} est actif")
                    active.append(domain)
            except Exception as e:
                print(f"[-] Erreur lors de la vérification de {domain}: {e}")

    # Écrit les domaines actifs dans le fichier de sortie
    with open(output_file, "w") as f:
        f.write("\n".join(active))
    print(f"[✓] Résultats enregistrés dans {output_file}")


# ----- Fonction principale -----
def main():
    """Charge les domaines depuis le fichier d’entrée et lance les tests."""
    try:
        # Lecture de la liste des domaines (un par ligne)
        with open(INPUT_FILE, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[!] Le fichier {INPUT_FILE} est introuvable.")
        return

    # Exécution des trois vérifications successives
    run_check(http_check, domains, HTTP_FILE)
    run_check(https_check, domains, HTTPS_FILE)
    run_check(ssh_check, domains, SSH_FILE)


# ----- Point d’entrée -----
if __name__ == "__main__":
    main()
