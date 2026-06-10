import os
import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from google import genai

BASE_URL = "https://na.finalfantasyxiv.com"
PATCHNOTE_LOG = f"{BASE_URL}/lodestone/special/patchnote_log"

DATA_DIR = "public/data"
PATCHES_DIR = f"{DATA_DIR}/patches"
INDEX_FILE = f"{DATA_DIR}/index.json"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FFXIVPatchScan/2.0)"
}


# ======================================================
# Utilities
# ======================================================

def normalize_date(date_str):
    if not date_str:
        return datetime.today().date().isoformat()

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                date_str,
                fmt
            ).date().isoformat()
        except ValueError:
            pass

    return datetime.today().date().isoformat()


def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return f"{slug}.json"


# ======================================================
# Patch discovery
# ======================================================

def get_latest_patch_url():
    res = requests.get(
        PATCHNOTE_LOG,
        headers=HEADERS,
        timeout=20
    )
    res.raise_for_status()

    matches = re.findall(
        r'href="(/lodestone/topics/detail/[a-f0-9]+/)"[^>]*class="btn__color"',
        res.text
    )

    if not matches:
        raise ValueError("No patch URL found")

    return BASE_URL + matches[0]


# ======================================================
# HTML Extraction
# ======================================================

def fetch_patch_content(url):
    res = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )
    res.raise_for_status()

    html = res.text

    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Patch Notes"

    images = []

    for img in soup.find_all("img"):
        src = img.get("src")

        if not src:
            continue

        if src.startswith("/"):
            src = BASE_URL + src

        images.append(src)

    text = soup.get_text("\n", strip=True)

    return title, text, images


# ======================================================
# Gemini helper
# ======================================================

def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    raw = response.text

    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    return json.loads(raw)


# ======================================================
# Structured extraction
# ======================================================

def extract_patch_metadata(title, content, patch_url):
    prompt = f"""
Extract only:

{{
  "patch_title": "",
  "patch_date": ""
}}

Rules:
- patch_date MUST be YYYY-MM-DD
- do not invent information
- return valid JSON only

Title:
{title}

Content:
{content[:25000]}
"""

    data = ask_gemini(prompt)

    return {
        "patch_title": data.get("patch_title", title),
        "patch_date": normalize_date(
            data.get("patch_date")
        ),
        "patch_url": patch_url
    }


def extract_jobs_pve(content):
    prompt = f"""
Extract ALL PvE job balance changes.

Return:

{{
  "jobs_pve": [
    {{
      "job": "",
      "changes": []
    }}
  ]
}}

Rules:
- include every affected job
- do not summarize excessively
- no PvP changes
- valid JSON only

Content:
{content}
"""

    return ask_gemini(prompt).get("jobs_pve", [])


def extract_jobs_pvp(content):
    prompt = f"""
Extract ALL PvP job balance changes.

Return:

{{
  "jobs_pvp": [
    {{
      "job": "",
      "changes": []
    }}
  ]
}}

Valid JSON only.

Content:
{content}
"""

    return ask_gemini(prompt).get("jobs_pvp", [])


def extract_new_content(content):
    prompt = f"""
Extract all:

- dungeons
- raids
- trials
- quests
- systems
- exploration zones
- major features

Return:

{{
  "new_content": [
    {{
      "name": "",
      "description": "",
      "location": null,
      "npc_location": null
    }}
  ]
}}

Do not invent information.

Content:
{content}
"""

    return ask_gemini(prompt).get("new_content", [])


def extract_housing(content, images):
    prompt = f"""
Extract ALL housing items.

Available images:
{json.dumps(images[:300])}

Return:

{{
  "housing": [
    {{
      "name": "",
      "description": "",
      "image_url": null
    }}
  ]
}}

Content:
{content}
"""

    return ask_gemini(prompt).get("housing", [])


def extract_glamour(content, images):
    prompt = f"""
Extract ALL glamour items.

Available images:
{json.dumps(images[:300])}

Return:

{{
  "glamour": [
    {{
      "name": "",
      "description": "",
      "image_url": null
    }}
  ]
}}

Content:
{content}
"""

    return ask_gemini(prompt).get("glamour", [])


# ======================================================
# Files
# ======================================================

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


def save_index(index):
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            index,
            f,
            ensure_ascii=False,
            indent=2
        )


def save_patch(filename, data):
    os.makedirs(PATCHES_DIR, exist_ok=True)

    with open(
        f"{PATCHES_DIR}/{filename}",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ======================================================
# Main
# ======================================================

def main():
    print("Fetching latest patch...")

    patch_url = get_latest_patch_url()

    index = load_index()

    title, content, images = fetch_patch_content(
        patch_url
    )

    filename = slugify(title)

    if any(p["file"] == filename for p in index):
        print("Latest patch already processed.")
        return

    print("Analyzing patch...")

    metadata = extract_patch_metadata(
        title,
        content,
        patch_url
    )

    data = {
        "patch_title": metadata["patch_title"],
        "patch_date": metadata["patch_date"],
        "patch_url": metadata["patch_url"],
        "jobs_pve": extract_jobs_pve(content),
        "jobs_pvp": extract_jobs_pvp(content),
        "new_content": extract_new_content(content),
        "housing": extract_housing(content, images),
        "glamour": extract_glamour(content, images)
    }

    save_patch(filename, data)

    index.insert(0, {
        "title": data["patch_title"],
        "date": data["patch_date"],
        "file": filename
    })

    save_index(index)

    print("Patch added successfully.")


if __name__ == "__main__":
    main()