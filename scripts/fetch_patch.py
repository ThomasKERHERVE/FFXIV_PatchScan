import os
import re
import json
import datetime
import requests
from anthropic import Anthropic

BASE_URL = "https://fr.finalfantasyxiv.com"
LODESTONE_NEWS = f"{BASE_URL}/lodestone/news/"
DATA_DIR = "public/data"
PATCHES_DIR = f"{DATA_DIR}/patches"
INDEX_FILE = f"{DATA_DIR}/index.json"

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def get_latest_patch_url():
    """Scrape Lodestone to find the latest patch notes URL."""
    res = requests.get(LODESTONE_NEWS, timeout=10)
    res.raise_for_status()

    matches = re.findall(r'href="(/lodestone/topics/\d+/[^"]+)"', res.text)
    for href in matches:
        if "patch" in href.lower():
            return BASE_URL + href

    raise ValueError("No patch notes URL found on Lodestone.")


def fetch_patch_content(url):
    """Fetch and extract text content from a patch notes page."""
    res = requests.get(url, timeout=10)
    res.raise_for_status()

    title_match = re.search(r'<title>(.*?)</title>', res.text)
    title = title_match.group(1).strip() if title_match else "Patch Notes"

    content = re.sub(r'<[^>]+>', ' ', res.text)
    content = re.sub(r'\s+', ' ', content).strip()

    return title, content[:15000]


def analyze_with_claude(title, content):
    """Send patch content to Claude and get structured JSON back."""
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

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
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
    print("Fetching latest patch URL...")
    patch_url = get_latest_patch_url()
    print(f"Found: {patch_url}")

    print("Fetching patch content...")
    title, content = fetch_patch_content(patch_url)
    print(f"Title: {title}")

    index = load_index()
    filename = slugify(title)
    if any(p["file"] == filename for p in index):
        print("Patch already in index, skipping.")
        return

    print("Analyzing with Claude...")
    data = analyze_with_claude(title, content)

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