#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Active Targets Finder - Version 2 interactive
=============================================
Vérifie quels domaines listés dans domains.txt sont actifs pour :
 - HTTP  
 - HTTPS 
 - SSH  

Demande à l'utilisateur quel port scanner pour chaque service.
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
TIMEOUT = 3                  # Délai d’attente (en secondes)
MAX_THREADS = 20             # Nombre maximum de threads


# ----- Fonctions de vérification -----
def http_check(domain: str, port: int = 80) -> bool:
    """Vérifie si le service HTTP est actif sur un port spécifique."""
    url = f"http://{domain}:{port}"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        return r.status_code < 400
    except Exception:
        return False


def https_check(domain: str, port: int = 443) -> bool:
    """Vérifie si le service HTTPS est actif sur un port spécifique."""
    url = f"https://{domain}:{port}"
    try:
        r = requests.get(url, timeout=TIMEOUT, verify=False)
        return r.status_code < 400
    except Exception:
        return False


def ssh_check(domain: str, port: int = 22) -> bool:
    """Vérifie si le port SSH est ouvert sur un port spécifique."""
    try:
        with socket.create_connection((domain, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False


# ----- Fonction utilitaire -----
def run_check(check_function, domains, output_file, port):
    """Exécute la vérification sur une liste de domaines et sauvegarde les résultats."""
    print(f"\n[*] Exécution de {check_function.__name__} sur le port {port}...")
    active = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(check_function, d, port): d for d in domains}
        for future in as_completed(futures):
            domain = futures[future]
            try:
                if future.result():
                    print(f"[+] {domain}:{port} est actif")
                    active.append(f"{domain}:{port}")
            except Exception as e:
                print(f"[-] Erreur lors de la vérification de {domain}:{port} → {e}")

    with open(output_file, "w") as f:
        f.write("\n".join(active))
    print(f"[✓] Résultats enregistrés dans {output_file}")


# ----- Fonction principale -----
def main():
    """Charge les domaines et demande à l'utilisateur les ports à scanner pour chaque service."""
    try:
        with open(INPUT_FILE, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[!] Le fichier {INPUT_FILE} est introuvable.")
        return

    # Demander les ports à l'utilisateur
    try:
        http_port = int(input("Entrez le port HTTP à scanner (par défaut 80) : ") or 80)
        https_port = int(input("Entrez le port HTTPS à scanner (par défaut 443) : ") or 443)
        ssh_port = int(input("Entrez le port SSH à scanner (par défaut 22) : ") or 22)
    except ValueError:
        print("[!] Port invalide, veuillez entrer un nombre.")
        return

    # Lancer les vérifications
    run_check(http_check, domains, HTTP_FILE, http_port)
    run_check(https_check, domains, HTTPS_FILE, https_port)
    run_check(ssh_check, domains, SSH_FILE, ssh_port)


# ----- Point d’entrée -----
if __name__ == "__main__":
    main()
