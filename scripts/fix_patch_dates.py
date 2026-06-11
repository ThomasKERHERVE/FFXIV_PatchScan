import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

PATCHES_DIR = "public/data/patches"
INDEX_FILE = "public/data/index.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_date_from_patch(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.raise_for_status()
    except Exception as e:
        print(f"Erreur lors du chargement de l'URL {url}: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # --- MÉTHODE 1 : Les balises Meta (Le plus fiable sur Lodestone) ---
    # Lodestone inclut souvent des meta de partage ou de publication cachées dans le <head>
    meta_date = soup.find("meta", property="article:published_time") or soup.find("meta", name="pubdate")
    if meta_date and meta_date.get("content"):
        try:
            # Souvent au format ISO "2022-04-11T07:00:00Z" -> on prend les 10 premiers caractères
            raw_meta = meta_date["content"]
            return raw_meta[:10]
        except Exception:
            pass

    # --- MÉTHODE 2 : Le timestamp caché (ldst-time) ---
    time_tag = soup.select_one(".news__date") or soup.select_one("time")
    
    if time_tag:
        ldst_time = time_tag.get("ldst-time")
        if ldst_time:
            try:
                timestamp = int(ldst_time)
                dt = datetime.fromtimestamp(timestamp)
                return dt.date().isoformat()
            except ValueError:
                pass

        # Si on n'a que du texte
        raw_date = time_tag.get_text(strip=True)
        
        # Si le texte est un tiret, on essaie de chercher n'importe quel texte textuel de date dans le header de l'article
        if raw_date == "-":
            # On cherche un fallback (ex: les structures d'anciennes pages)
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                # Parfois la date est au début de la description : "Posted on 04/11/2022..."
                raw_date = og_desc["content"]

        # Si on a un format classique américain "MM/DD/YYYY HH:MM AM/PM"
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)", raw_date, re.IGNORECASE)
        if match:
            try:
                dt = datetime.strptime(match.group(1), "%m/%d/%Y %I:%M %p")
                return dt.date().isoformat()
            except ValueError:
                pass

        # Si le format est écrit textuellement (ex: "Apr. 11, 2022" ou "August 23, 2022")
        # On extrait quelque chose qui ressemble à : un mois, un jour, une année
        match_text = re.search(r"([A-Za-z\.]+\s+\d{1,2},\s+\d{4})", raw_date)
        if match_text:
            try:
                # Nettoyage rapide du point pour les abréviations (ex: "Jan." -> "Jan")
                clean_date = match_text.group(1).replace(".", "")
                # On gère les deux formats possibles (abrégé "Apr" ou complet "April")
                fmt = "%b %d, %Y" if len(clean_date.split()[0]) <= 4 else "%B %d, %Y"
                dt = datetime.strptime(clean_date, fmt)
                return dt.date().isoformat()
            except ValueError:
                pass

    print(f"Impossible de trouver une date valide pour l'URL {url}")
    return None
    
def rebuild_index():
    print("\nRegénération de index.json...")
    files = [f for f in os.listdir(PATCHES_DIR) if f.endswith(".json")]
    new_index = []

    for file in files:
        path = os.path.join(PATCHES_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        new_index.append({
            "title": data.get("patch_title"),
            "date": data.get("patch_date"),
            "file": file
        })
    
    # Optionnel : Trier l'index par date décroissante (les plus récents en premier)
    new_index.sort(key=lambda x: x["date"] or "", reverse=True)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(new_index, f, ensure_ascii=False, indent=2)
    print("index.json mis à jour avec succès !")


def main():
    files = [
        f for f in os.listdir(PATCHES_DIR)
        if f.endswith(".json")
    ]

    print(f"Found {len(files)} patch files")

    updated = 0

    for file in files:
        path = os.path.join(PATCHES_DIR, file)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        patch_url = data.get("patch_url")

        if not patch_url:
            print(f"Skipping {file} (no patch_url)")
            continue

        try:
            real_date = extract_date_from_patch(patch_url)

            if not real_date:
                print(f"No date found for {file}")
                continue

            old_date = data.get("patch_date")

            if old_date != real_date:
                data["patch_date"] = real_date

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        data,
                        f,
                        ensure_ascii=False,
                        indent=2
                    )

                updated += 1

                print(
                    f"Updated {file}: "
                    f"{old_date} -> {real_date}"
                )

        except Exception as e:
            print(f"Error on {file}: {e}")

    print(f"\nDone. Updated {updated} files.")
    rebuild_index()


if __name__ == "__main__":
    main()