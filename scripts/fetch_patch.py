import os
import re
import json
import datetime
import requests
import time
from google import genai

BASE_URL = "https://na.finalfantasyxiv.com"
PATCHNOTE_LOG = f"{BASE_URL}/lodestone/special/patchnote_log"
DATA_DIR = "public/data"
PATCHES_DIR = f"{DATA_DIR}/patches"
INDEX_FILE = f"{DATA_DIR}/index.json"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FFXIVPatchScan/1.0)"}


def get_patch_urls(limit=50):
    """Get patch URLs from patchnote_log."""
    res = requests.get(PATCHNOTE_LOG, headers=HEADERS, timeout=10)
    res.raise_for_status()

    matches = re.findall(
        r'href="(/lodestone/topics/detail/[a-f0-9]+/)"[^>]*class="btn__color"',
        res.text
    )

    patches = []
    for match in matches[:limit]:
        patch_url = BASE_URL + match
        patches.append(patch_url)

    return patches


def fetch_patch_content(url):
    """Fetch and extract text content from a patch notes page."""
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()

    title_match = re.search(r'<title>(.*?)</title>', res.text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "Patch Notes"

    content = re.sub(r'<[^>]+>', ' ', res.text)
    content = re.sub(r'\s+', ' ', content).strip()

    return title, content[:15000]


def analyze_with_gemini(title, content, patch_url):
    """Send patch content to Gemini and get structured JSON back."""
    prompt = f"""You are a Final Fantasy XIV expert assistant. Here is raw patch notes content.

Extract ONLY the following into strict JSON (no markdown, no extra text):

{{
  "patch_title": "exact patch title",
  "patch_date": "date if found, else null",
  "patch_url": "{patch_url}",
  "jobs_pve": [{{"job": "JobName", "changes": ["change 1", "change 2"]}}],
  "jobs_pvp": [{{"job": "JobName", "changes": ["change 1"]}}],
  "new_content": [
    {{
      "name": "Raid/Dungeon Name",
      "description": "brief description",
      "location": "Zone (X:12.3, Y:45.6)",
      "npc_location": "NPC Name at Location"
    }}
  ],
  "housing": [
    {{
      "name": "Furniture Name",
      "description": "brief description",
      "image_url": null
    }}
  ],
  "glamour": [
    {{
      "name": "Armor/Weapon Name",
      "description": "brief description",
      "image_url": null
    }}
  ]
}}

Rules:
- Empty sections = empty arrays []
- jobs_pve/pvp: only gameplay changes (damage, cooldowns, effects)
- new_content: dungeons, raids, trials, main story quests, major features. Include location and npc_location if mentioned.
- housing: new furniture/housing items
- glamour: new armor/weapons/cosmetic items
- image_url: always null for now
- Reply ONLY with valid JSON

Patch title: {title}
Patch content:
{content}"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",        
        contents=prompt
    )

    raw = response.text
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_index(index):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def save_patch(filename, data):
    os.makedirs(PATCHES_DIR, exist_ok=True)
    with open(f"{PATCHES_DIR}/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return f"{slug}.json"


def main():
    print("Fetching patch URLs...")
    patch_urls = get_patch_urls(limit=50)
    print(f"Found {len(patch_urls)} patches")

    index = load_index()
    existing_files = {p["file"] for p in index}
    new_entries = []

    for patch_url in patch_urls:
        try:
            print(f"\nProcessing: {patch_url}")
            title, content = fetch_patch_content(patch_url)
            print(f"  Title: {title}")

            filename = slugify(title)
            if filename in existing_files:
                print(f"  Skipping (already in index)")
                continue

            print(f"  Analyzing with Gemini...")
            data = analyze_with_gemini(title, content, patch_url)

            save_patch(filename, data)
            print(f"  Saved: {filename}")

            today = datetime.date.today().isoformat()
            patch_date = data.get("patch_date") or today

            new_entries.append({
                "title": data.get("patch_title") or title,
                "date": patch_date,
                "file": filename
            })

            time.sleep(30)  # ← 15s entre chaque appel pour rester sous la limite

        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(60)  # ← attendre plus longtemps en cas d'erreur

    # Trier par date décroissante avant de sauvegarder
    all_entries = index + new_entries
    all_entries.sort(key=lambda x: x["date"], reverse=True)
    save_index(all_entries)
    print("\nIndex updated.")


if __name__ == "__main__":
    main()