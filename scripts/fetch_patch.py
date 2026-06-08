import os
import re
import json
import datetime
import requests
import xml.etree.ElementTree as ET
from google import genai

BASE_URL = "https://na.finalfantasyxiv.com"
RSS_URL = f"{BASE_URL}/lodestone/news/category/1?rss=1"  # Patch Notes category
DATA_DIR = "public/data"
PATCHES_DIR = f"{DATA_DIR}/patches"
INDEX_FILE = f"{DATA_DIR}/index.json"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FFXIVPatchScan/1.0)"}


def get_latest_patch_url():
    res = requests.get(
        "https://fr.finalfantasyxiv.com/lodestone/special/patchnote_log",
        headers=HEADERS,
        timeout=10,
    )
    print("btn__color présent ?", "btn__color" in res.text)
    res.raise_for_status()

    idx = res.text.find("btn__color")
    print(res.text[idx-300:idx+500])

    matches = re.findall(
        r'href="(/lodestone/topics/detail/[a-f0-9]+/)"[^>]*class="btn__color"',
        res.text
    )

    if not matches:
        raise ValueError("No patch URL found")

    patch_url = "https://fr.finalfantasyxiv.com" + matches[1]

    # Récupération de la page du patch
    patch_res = requests.get(patch_url, headers=HEADERS, timeout=10)
    patch_res.raise_for_status()

    # Récupération du titre dans la balise <title>
    title_match = re.search(
        r"<title>(.*?)</title>",
        patch_res.text,
        re.IGNORECASE | re.DOTALL
    )

    rss_title = re.search(
        r'class="btn__color"[^>]*>([^<]+)<',
        res.text
    )
        
    return patch_url, rss_title


def fetch_patch_content(url):
    """Fetch and extract text content from a patch notes page."""
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()

    title_match = re.search(r'<title>(.*?)</title>', res.text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "Patch Notes"

    content = re.sub(r'<[^>]+>', ' ', res.text)
    content = re.sub(r'\s+', ' ', content).strip()

    return title, content[:15000]


def analyze_with_gemini(title, content):
    """Send patch content to Gemini and get structured JSON back."""
    prompt = f"""You are a Final Fantasy XIV expert assistant. Here is raw patch notes content.

Extract ONLY the following into strict JSON (no markdown, no extra text):

{{
  "patch_title": "exact patch title",
  "patch_date": "date if found, else null",
  "jobs_pve": [{{"job": "JobName", "changes": ["change 1", "change 2"]}}],
  "jobs_pvp": [{{"job": "JobName", "changes": ["change 1"]}}],
  "pnj_locations": [{{"npc_name": "NPC Name", "location": "Zone / Coords", "role": "short description"}}],
  "new_content": [{{"name": "Content Name", "description": "short description"}}]
}}

Rules:
- Empty section = empty array []
- jobs_pve/pvp: only gameplay changes (damage, cooldowns, effects), skip minor visual bug fixes
- pnj_locations: NPCs for new main quests, raids, dungeons, important vendors
- new_content: dungeons, raids, trials, main story quests, major features
- Reply ONLY with valid JSON

Patch title: {title}
Patch content:
{content}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
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
    print("Fetching latest patch URL from RSS...")
    patch_url, rss_title = get_latest_patch_url()
    print(f"Found: {patch_url}")

    print("Fetching patch content...")
    title, content = fetch_patch_content(patch_url)
    print(f"Title: {title}")

    index = load_index()
    filename = slugify(title)
    if any(p["file"] == filename for p in index):
        print("Patch already in index, skipping.")
        return

    print("Analyzing with Gemini...")
    data = analyze_with_gemini(title, content)

    today = datetime.date.today().isoformat()
    patch_date = data.get("patch_date") or today

    save_patch(filename, data)
    print(f"Saved patch: {filename}")

    index.insert(0, {
        "title": data.get("patch_title") or title,
        "date": patch_date,
        "file": filename
    })
    save_index(index)
    print("Index updated.")


if __name__ == "__main__":
    main()