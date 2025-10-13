#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_hackerone_full.py
Version corrigée : collecte les handles depuis /directory/programs et extrait proprement
les targets marqués "In scope" / "Eligible". Expose les trois fonctions demandées.
"""

import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

DIRECTORY_URL = "https://hackerone.com/directory/programs"
BASE = "https://hackerone.com"
OUTPUT = "programs.json"

DOMAIN_RE = re.compile(r"(?:\*\.)?(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}")
URL_RE = re.compile(r"https?://[^\s'\"<>]+")

# ---------------------
# Utility helpers
# ---------------------
def _handle_from_href(href: str) -> Optional[str]:
    if not href or not href.startswith("/"):
        return None
    # only top-level handles (no /organizations/ etc)
    part = href.split("?")[0].split("#")[0].lstrip("/")
    if "/" in part:
        # keep only single-segment handles
        if part.count("/") >= 1:
            return None
    # valid handle: letters, digits, dash, underscore
    if re.match(r"^[A-Za-z0-9_\-\.]+$", part):
        return part.lower()
    return None

def _classify_token(token: str):
    t = token.strip()
    if not t:
        return None, None
    if "*" in t:
        return "wildcards", t
    if re.match(r"^https?://", t, flags=re.I):
        return "urls", t
    # domain-like?
    m = DOMAIN_RE.search(t)
    if m:
        return "domains", m.group(0).lower()
    return None, None

# ---------------------
# Required functions
# ---------------------

def get_programs_list(timeout: int = 30) -> List[str]:
    """
    Retourne la liste des handles (chaînes) présents dans la directory HackerOne.
    Utilise Playwright et scroll infini.
    """
    handles = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(timeout * 1000)

        page.goto(DIRECTORY_URL)
        # attendre un sélecteur raisonnable qui contient des cartes de programmes
        # essayer plusieurs sélecteurs possibles
        possible_card_selectors = [
            "a[data-testid^='program-card']",            # si présent
            "a[href^='/'][role='link']",
            ".program-card a[href^='/']",
            "a[href^='/'][data-testid]"
        ]
        time.sleep(1.0)
        # scroll loop
        prev = 0
        stable = 0
        for i in range(80):
            # collect anchors
            anchors = page.query_selector_all("a[href^='/']")
            for a in anchors:
                try:
                    href = a.get_attribute("href") or ""
                except Exception:
                    href = ""
                h = _handle_from_href(href)
                if h:
                    # filter out obvious non-programs
                    if h in {"blog", "press", "privacy", "terms", "jobs", "docs", "help", "directory", "security"}:
                        continue
                    handles.add(h)
            # scroll
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.35)
            if len(handles) == prev:
                stable += 1
            else:
                stable = 0
            prev = len(handles)
            if stable >= 4:
                break

        # final pass: try more specific program card anchors
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
    Scrape la page d'un programme HackerOne et récupère les cibles marquées 'In scope' ou 'Eligible'.
    Retourne un dictionnaire avec 'domains', 'urls', 'wildcards' si disponibles.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    import re, time

    BASE = "https://hackerone.com"
    out = {"domains": [], "urls": [], "wildcards": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(timeout * 1000)

        url = f"{BASE}/{program_handle}"
        try:
            page.goto(url, wait_until="domcontentloaded")
        except PWTimeout:
            print(f"[!] Timeout loading {url}")
            ctx.close()
            browser.close()
            return {}

        # --- attendre l'onglet "Scope" s’il existe ---
        try:
            page.wait_for_selector("text=Scope", timeout=5000)
            try:
                page.click("text=Scope", timeout=3000)
                page.wait_for_timeout(1000)
            except Exception:
                pass
        except Exception:
            pass

        # attendre que des targets apparaissent
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
                    content = sec.first.inner_text()
                    break
            except Exception:
                pass

        # fallback : tout le texte de la page
        if not content:
            content = page.inner_text("body")

        # --- extraire les domaines/urls/wildcards ---
        lines = [x.strip() for x in content.splitlines() if x.strip()]
        for line in lines:
            if len(line) > 150:
                continue
            if re.search(r"\b(hackerone\.com|policy|support)\b", line, re.I):
                continue

            if "*" in line:
                if line not in out["wildcards"]:
                    out["wildcards"].append(line)
            elif re.match(r"^https?://", line):
                if line not in out["urls"]:
                    out["urls"].append(line)
            elif re.match(r"^(?:[\w\-]+\.)+[a-z]{2,}$", line):
                if line not in out["domains"]:
                    out["domains"].append(line)

        # retirer les listes vides
        out = {k: v for k, v in out.items() if v}

        ctx.close()
        browser.close()

    return out


def scrape_hackerone(save_path: str = OUTPUT, handles: Optional[List[str]] = None):
    """
    Orchestrateur principal.
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
            aggregated[h] = {}
            print("none")
        time.sleep(0.25)
    Path(save_path).write_text(json.dumps(aggregated, indent=4, ensure_ascii=False))
    print(f"[+] Saved {len(aggregated)} program scopes -> {save_path}")
    return aggregated

# If run as script
if __name__ == "__main__":
    scrape_hackerone()
