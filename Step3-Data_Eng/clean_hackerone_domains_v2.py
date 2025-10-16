import json
import re
import socket
import concurrent.futures
from urllib.parse import urlparse

# === Helper Functions === #

def normalize_domain(text):
    """
    Corrige automatiquement les erreurs de syntaxe courantes :
    - Supprime http(s)://, chemins, ports, etc.
    - Corrige les espaces, tabs et punycode.
    - Enlève les caractères non valides.
    """
    if not text:
        return None
    text = text.strip().lower()

    # Retire http(s)://, chemins et paramètres
    if text.startswith("http"):
        parsed = urlparse(text)
        text = parsed.netloc or parsed.path

    # Enlève wildcards et caractères parasites
    text = text.strip("*/ \t\n\r")
    text = text.replace("\\", "").replace(":", "").replace("–", "-")

    # Supprime les éventuels caractères non alphabétiques à la fin
    text = re.sub(r"[^a-z0-9\.\-]", "", text)

    # Retire les sous-chaînes suspectes (android/com/node.js)
    if any(skip in text for skip in ["node.js", "com.", "android", "ios"]):
        return None

    # Valide que c’est un vrai domaine
    if re.fullmatch(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}", text):
        return text
    return None


def expand_wildcard(domain):
    """
    Essaie de dériver des sous-domaines communs à partir d’un wildcard (*.domain.tld)
    """
    if not domain.startswith("*."):
        return [domain]
    root = domain.replace("*.", "")
    common_subs = [
        "www", "api", "app", "dev", "staging", "test", "portal", "login",
        "dashboard", "beta", "mail", "cdn"
    ]
    return [f"{sub}.{root}" for sub in common_subs] + [root]


# === Core Functions === #

def extract_domains(programs_filename):
    """
    Extrait, nettoie et corrige les domaines depuis un fichier HackerOne JSON.
    Retourne une liste unique et syntaxiquement valide.
    """
    domain_pattern = re.compile(r"(?:(?:\*\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})")
    domains = set()

    with open(programs_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    for program, sections in data.items():
        for key, values in sections.items():
            if not isinstance(values, list):
                continue
            for entry in values:
                entry = str(entry)
                matches = domain_pattern.findall(entry)
                for match in matches:
                    norm = normalize_domain(match)
                    if not norm:
                        continue
                    # Expansion des wildcards (très utile pour pentest)
                    expanded = expand_wildcard(norm)
                    for d in expanded:
                        domains.add(d)
    return sorted(domains)


def check_domains(domains_list, max_threads=100):
    """
    Vérifie les domaines actifs via résolution DNS multithreadée.
    Retourne la liste des domaines résolvables.
    """
    active = []

    def resolve(domain):
        try:
            socket.gethostbyname(domain)
            return domain
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        results = list(executor.map(resolve, domains_list))

    for r in results:
        if r:
            active.append(r)
    return active


def clean_domains(programs_filename="programs.json"):
    """
    Combine extraction + correction + vérification DNS + sauvegarde.
    """
    print("📤 Extraction et correction des domaines...")
    all_domains = extract_domains(programs_filename)
    print(f"→ {len(all_domains)} domaines uniques (corrigés).")

    print("🌐 Vérification DNS en parallèle (threads)...")
    active = check_domains(all_domains)
    print(f"✅ {len(active)} domaines actifs détectés.")

    with open("domains.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(set(active))))

    print("💾 Fichier 'domains.txt' créé avec succès.")


# === CLI Entrypoint === #
if __name__ == "__main__":
    clean_domains("programs.json")
