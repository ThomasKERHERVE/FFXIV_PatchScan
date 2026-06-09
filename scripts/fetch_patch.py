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


def get_latest_patch_url():
    res = requests.get(PATCHNOTE_LOG, headers=HEADERS, timeout=10)
    res.raise_for_status()

    matches = re.findall(
        r'href="(/lodestone/topics/detail/[a-f0-9]+/)"[^>]*class="btn__color"',
        res.text
    )

    if not matches:
        raise ValueError("No patch URL found")

    return BASE_URL + matches[0]


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
    print("Fetching latest patch...")
    patch_url = get_patch_latest_urls()
    if patch_url == null:
        print("No patch URL found.")
        return

    index = load_index()

    title, content = fetch_patch_content(patch_url)
    filename = slugify(title)

    if any(p["file"] == filename for p in index):
        print("Latest patch already processed.")
        return

    print(f"New patch detected: {title}")

    data = analyze_with_gemini(title, content, patch_url)

    save_patch(filename, data)

    patch_date = data.get("patch_date") or datetime.date.today().isoformat()

    index.insert(0, {
        "title": data.get("patch_title") or title,
        "date": patch_date,
        "file": filename
    })

    save_index(index)

    print("Patch added successfully.")


if __name__ == "__main__":
    main()