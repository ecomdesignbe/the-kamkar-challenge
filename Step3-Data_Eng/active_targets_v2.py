#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Active Targets Finder - Version 2
=================================
Vérifie quels domaines listés dans domains.txt sont actifs pour :
 - HTTP  (port par défaut 80)
 - HTTPS (port par défaut 443)
 - SSH   (port par défaut 22)

Bonus : chaque vérification peut utiliser un port spécifique en paramètre.
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
def http_check(domain: str, port: int = 80) -> bool:
    """
    Vérifie si le service HTTP est actif sur un port spécifique.
    
    :param domain: nom de domaine ou IP
    :param port: port HTTP à tester (par défaut 80)
    :return: True si actif, False sinon
    """
    url = f"http://{domain}:{port}"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        return r.status_code < 400  # Considère le domaine actif si le code HTTP < 400
    except Exception:
        return False


def https_check(domain: str, port: int = 443) -> bool:
    """
    Vérifie si le service HTTPS est actif sur un port spécifique.
    
    :param domain: nom de domaine ou IP
    :param port: port HTTPS à tester (par défaut 443)
    :return: True si actif, False sinon
    """
    url = f"https://{domain}:{port}"
    try:
        r = requests.get(url, timeout=TIMEOUT, verify=False)  # Ignorer les certificats SSL invalides
        return r.status_code < 400
    except Exception:
        return False


def ssh_check(domain: str, port: int = 22) -> bool:
    """
    Vérifie si le port SSH (TCP) est actif sur un port spécifique.
    
    :param domain: nom de domaine ou IP
    :param port: port SSH à tester (par défaut 22)
    :return: True si ouvert, False sinon
    """
    try:
        with socket.create_connection((domain, port), timeout=TIMEOUT):
            return True  # Connexion réussie → port ouvert
    except Exception:
        return False  # Erreur ou délai dépassé → port fermé/inaccessible


# ----- Fonction utilitaire -----
def run_check(check_function, domains, output_file, port):
    """
    Exécute une vérification donnée (HTTP, HTTPS ou SSH) sur une liste de domaines
    en multithreading et enregistre les domaines actifs dans un fichier.
    
    :param check_function: fonction de vérification (http_check, https_check, ssh_check)
    :param domains: liste des domaines à tester
    :param output_file: fichier où sauvegarder les résultats
    :param port: port à utiliser pour la vérification
    """
    print(f"\n[*] Exécution de {check_function.__name__} sur le port {port}...")
    active = []

    # Utilisation d’un pool de threads pour accélérer les vérifications
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

    # Écriture des résultats dans le fichier de sortie
    with open(output_file, "w") as f:
        f.write("\n".join(active))
    print(f"[✓] Résultats enregistrés dans {output_file}")


# ----- Fonction principale -----
def main():
    """Charge les domaines depuis le fichier d'entrée et lance les tests sur les ports définis."""
    try:
        # Lecture de la liste des domaines (un par ligne)
        with open(INPUT_FILE, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[!] Le fichier {INPUT_FILE} est introuvable.")
        return

    # Exemples d’utilisation : modification facile des ports ici
    run_check(http_check, domains, HTTP_FILE, port=80)
    run_check(https_check, domains, HTTPS_FILE, port=443)
    run_check(ssh_check, domains, SSH_FILE, port=22)


# ----- Point d’entrée -----
if __name__ == "__main__":
    main()
