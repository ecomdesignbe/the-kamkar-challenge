#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_hackerone_full.py
Version commentée en français.

But : récupérer la liste des programmes HackerOne (handles) et, pour chaque programme,
extraire les cibles du scope (domains, urls, wildcards) quand elles sont disponibles.
Le résultat est sauvegardé dans programs.json.

Ce script expose trois fonctions principales requises par l'exercice :
- get_programs_list()
- get_scope(program_handle)
- scrape_hackerone()
"""

# imports standard
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

# Playwright (synchronisé)
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

# URL de la directory et constantes
DIRECTORY_URL = "https://hackerone.com/directory/programs"
BASE = "https://hackerone.com"
OUTPUT = "programs.json"

# Expressions régulières pour détecter domaines / urls
DOMAIN_RE = re.compile(r"(?:\*\.)?(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}")
URL_RE = re.compile(r"https?://[^\s'\"<>]+")

# ---------------------
# Fonctions utilitaires
# ---------------------

def _handle_from_href(href: str) -> Optional[str]:
    """
    Transforme un href (ex. '/audible') en handle 'audible' si c'est un handle valide.
    Ignore les urls non relatives ou les chemins multi-segments (ex: /organizations/...)
    """
    if not href or not href.startswith("/"):
        return None
    # on nettoie les query params / fragments
    part = href.split("?")[0].split("#")[0].lstrip("/")
    # ignorer les chemins composés (par ex. 'organizations/xyz')
    if "/" in part:
        if part.count("/") >= 1:
            return None
    # valide si composé de lettres, chiffres, '-', '_' ou '.'
    if re.match(r"^[A-Za-z0-9_\-\.]+$", part):
        return part.lower()
    return None

def _classify_token(token: str):
    """
    Tentative simple de classification d'une chaîne extraite :
    - 'wildcards' si contient '*'
    - 'urls' si commence par http(s)://
    - 'domains' si ressemble à un nom de domaine
    Retourne (type, valeur) ou (None, None) si non classifiable.
    """
    t = token.strip()
    if not t:
        return None, None
    if "*" in t:
        return "wildcards", t
    if re.match(r"^https?://", t, flags=re.I):
        return "urls", t
    m = DOMAIN_RE.search(t)
    if m:
        return "domains", m.group(0).lower()
    return None, None

# ---------------------
# Fonctions demandées
# ---------------------

def get_programs_list(timeout: int = 30) -> List[str]:
    """
    Retourne la liste des handles (chaînes) présents dans la page /directory/programs.
    Utilise Playwright pour rendre la page et effectue un scroll pour charger le contenu.
    """
    handles = set()
    with sync_playwright() as p:
        # lancement d'un navigateur Chromium headless
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(timeout * 1000)

        # aller sur la page de la directory
        page.goto(DIRECTORY_URL)
        # petit délai pour débuter le rendu/js
        time.sleep(1.0)

        # boucle de scroll pour charger le contenu (infinite scroll)
        prev = 0
        stable = 0
        for i in range(80):
            # recherche de tous les ancres relatives
            anchors = page.query_selector_all("a[href^='/']")
            for a in anchors:
                try:
                    href = a.get_attribute("href") or ""
                except Exception:
                    href = ""
                h = _handle_from_href(href)
                if h:
                    # filtrer des routes internes évidentes (non programmes)
                    if h in {"blog", "press", "privacy", "terms", "jobs", "docs", "help", "directory", "security"}:
                        continue
                    handles.add(h)
            # descendre en bas de la page pour forcer le chargement
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.35)
            # si stable (plus de nouveaux handles) plusieurs fois, sortir
            if len(handles) == prev:
                stable += 1
            else:
                stable = 0
            prev = len(handles)
            if stable >= 4:
                break

        # tentative finale : chercher des éléments marqués data-testid de cartes de programme
        try:
            cards = page.query_selector_all("[data-testid*='program-card'] a[href^='/']")
            for a in cards:
                href = a.get_attribute("href") or ""
                h = _handle_from_href(href)
                if h:
                    handles.add(h)
        except Exception:
            pass

        ctx.close()
        browser.close()

    result = sorted(handles)
    print(f"[+] Found {len(result)} program handles.")
    return result

def get_scope(program_handle: str, timeout: int = 20) -> Dict[str, List[str]]:
    """
    Pour un handle donné, ouvre la page du programme et essaye d'extraire les cibles
    marquées 'In scope' ou 'Eligible'. Retourne un dict pouvant contenir les clés :
    'domains', 'urls', 'wildcards'.

    Remarque : cette extraction est heuristique — HackerOne charge souvent du contenu
    par JS, il peut être nécessaire d'ajuster les sélecteurs si la page change.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    import re, time

    BASE = "https://hackerone.com"
    # structure par défaut
    out = {"domains": [], "urls": [], "wildcards": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(timeout * 1000)

        url = f"{BASE}/{program_handle}"
        try:
            # charger la page — wait_until DOMContentLoaded pour démarrer rapidement
            page.goto(url, wait_until="domcontentloaded")
        except PWTimeout:
            print(f"[!] Timeout loading {url}")
            ctx.close()
            browser.close()
            return {}

        # --- essayer de cliquer/ouvrir l'onglet "Scope" si présent ---
        try:
            # quelques libellés possibles pour l'onglet scope
            page.wait_for_selector("text=Scope", timeout=5000)
            try:
                page.click("text=Scope", timeout=3000)
                page.wait_for_timeout(1000)
            except Exception:
                # si le click échoue, on continue — le texte peut déjà être visible
                pass
        except Exception:
            # pas d'onglet scope détecté rapidement, pas grave on continue
            pass

        # chercher une section qui contient 'In scope' ou 'Eligible'
        selectors = [
            "section:has-text('In scope')",
            "section:has-text('Eligible')",
            "div:has-text('In scope')",
            "div:has-text('Eligible')"
        ]
        content = ""
        for sel in selectors:
            try:
                sec = page.locator(sel)
                if sec.count() > 0:
                    # prendre le texte brut du premier bloc trouvé
                    content = sec.first.inner_text()
                    break
            except Exception:
                pass

        # si rien trouvé, fallback : texte intégral de la page
        if not content:
            content = page.inner_text("body")

        # --- nettoyer / parser le texte ligne par ligne pour extraire targets ---
        lines = [x.strip() for x in content.splitlines() if x.strip()]
        for line in lines:
            # ignorer les longues descriptions, et références internes hackerone
            if len(line) > 150:
                continue
            if re.search(r"\b(hackerone\.com|policy|support)\b", line, re.I):
                continue

            # heuristiques simples pour classer
            if "*" in line:
                if line not in out["wildcards"]:
                    out["wildcards"].append(line)
            elif re.match(r"^https?://", line):
                if line not in out["urls"]:
                    out["urls"].append(line)
            elif re.match(r"^(?:[\w\-]+\.)+[a-z]{2,}$", line):
                if line not in out["domains"]:
                    out["domains"].append(line)

        # supprimer les clés vides pour ne garder que ce qui existe
        out = {k: v for k, v in out.items() if v}

        ctx.close()
        browser.close()

    return out

def scrape_hackerone(save_path: str = OUTPUT, handles: Optional[List[str]] = None):
    """
    Orchestrateur principal :
    - si handles n'est pas fourni, appelle get_programs_list() pour récupérer tous les handles
    - pour chaque handle, appelle get_scope(handle)
    - agrège les résultats et écrit programs.json
    """
    if handles is None:
        handles = get_programs_list()
    print(f"[*] Scraping {len(handles)} programs...")
    aggregated = {}
    for i, h in enumerate(handles, start=1):
        print(f"[{i}/{len(handles)}] {h} ...", end=" ", flush=True)
        scope = get_scope(h)
        if scope:
            aggregated[h] = scope
            print(f"found {', '.join(f'{k}:{len(v)}' for k,v in scope.items())}")
        else:
            # garder une clé vide pour indiquer qu'on a tenté
            aggregated[h] = {}
            print("none")
        # petit délai pour être poli et limiter la charge
        time.sleep(0.25)
    # écrire le JSON final
    Path(save_path).write_text(json.dumps(aggregated, indent=4, ensure_ascii=False))
    print(f"[+] Saved {len(aggregated)} program scopes -> {save_path}")
    return aggregated

# Exécution directe si on lance le script
if __name__ == "__main__":
    scrape_hackerone()
