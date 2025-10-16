import json
import re
import socket

def extract_domains(programs_filename):
    """
    Lit le fichier JSON et extrait tous les domaines syntaxiquement valides.
    Retourne une liste sans doublons.
    """
    domains = set()
    domain_pattern = re.compile(
        r"(?:(?:\*\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})"
    )

    with open(programs_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    for program, sections in data.items():
        for key, values in sections.items():
            if isinstance(values, list):
                for v in values:
                    # Nettoyage du texte brut
                    v = v.strip().split()[0]
                    # Recherche des domaines
                    matches = domain_pattern.findall(v)
                    for m in matches:
                        # Supprime le "http(s)://" et les caractères spéciaux
                        m = m.lower().strip("*/ \t")
                        if m.startswith("http"):
                            continue
                        if "localhost" in m or "node.js" in m:
                            continue
                        # Enlève les wildcards
                        m = m.replace("*.", "")
                        domains.add(m)
    return sorted(domains)


def check_domains(domains_list):
    """
    Vérifie quels domaines sont actifs (résolvent une IP).
    Retourne la liste de ceux qui sont joignables.
    """
    active_domains = []
    for domain in domains_list:
        try:
            socket.gethostbyname(domain)
            active_domains.append(domain)
        except Exception:
            continue
    return active_domains


def clean_domains(programs_filename="programs.json"):
    """
    Combine extraction + vérification et sauvegarde les domaines actifs dans domains.txt.
    """
    print("📤 Extraction des domaines valides...")
    all_domains = extract_domains(programs_filename)
    print(f"→ {len(all_domains)} domaines valides trouvés.")

    print("🌐 Vérification des domaines actifs (résolution DNS)...")
    active = check_domains(all_domains)
    print(f"✅ {len(active)} domaines actifs détectés.")

    with open("domains.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(active))

    print("💾 Fichier 'domains.txt' sauvegardé avec succès !")


if __name__ == "__main__":
    clean_domains("programs.json")
