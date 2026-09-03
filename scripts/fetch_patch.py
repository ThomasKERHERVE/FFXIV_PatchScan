import os
import re
import json
import datetime
import requests
import time
from bs4 import BeautifulSoup

BASE_URL = "https://na.finalfantasyxiv.com"
PATCHNOTE_LOG = f"{BASE_URL}/lodestone/special/patchnote_log"

DATA_DIR = "public/data"
PATCHES_DIR = f"{DATA_DIR}/patches"
INDEX_FILE = f"{DATA_DIR}/index.json"

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FFXIVPatchScan/2.0)"
}


# ======================================================
# Utilities
# ======================================================

def normalize_date(date_str):
    if not date_str:
        return datetime.date.today().isoformat()

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(
                date_str, fmt
            ).date().isoformat()
        except ValueError:
            pass

    return datetime.date.today().isoformat()


def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return f"{slug}.json"


# ======================================================
# Patch discovery
# ======================================================

def get_latest_patch_url(existing_files):
    res = requests.get(PATCHNOTE_LOG, headers=HEADERS, timeout=15)
    res.raise_for_status()

    matches = re.findall(
        r'href="(/lodestone/topics/detail/[a-f0-9]+/)"[^>]*class="btn__color"',
        res.text
    )

    if not matches:
        raise ValueError("No patch URL found")

    print(f"Found {len(matches)} patch links")

    for match in matches:
        patch_url = BASE_URL + match

        try:
            title, _, _ = fetch_patch_content(patch_url)
            filename = slugify(title)

            print(f"Checking: {title}")

            if filename not in existing_files:
                print(f"New patch found: {title}")
                return patch_url

        except Exception as e:
            print(f"Failed to inspect {patch_url}: {e}")

    return None


# ======================================================
# HTML Extraction
# ======================================================

def fetch_patch_content(url):
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()

    html = res.text
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True).split("|")[0].strip() if title_tag else "Patch Notes"

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
# Groq helper
# ======================================================

def get_best_model():
    """Get the first available text generation model."""
    # Priority list — update if needed
    preferred = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3.6-27b",
        "qwen/qwen3.8-27b",
        "groq/compound-mini",
        "groq/compound",
    ]

    response = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
    )
    available = {m["id"] for m in response.json().get("data", [])}

    for model in preferred:
        if model in available:
            print(f"Using model: {model}")
            return model

    raise ValueError("No suitable model available!")

def ask_groq(prompt):
    time.sleep(30)
    model = get_best_model()
    
    for attempt in range(3):
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 4096
            },
            timeout=30
        )
        print(f"Groq status: {response.status_code}")
        print(f"Groq response: {response.text[:500]}")
        
        if response.status_code == 429:
            print(f"Rate limited, waiting 60s...")
            time.sleep(60)
            continue
            
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        clean = raw.replace("```json", "").replace("```", "").strip()

        if not clean:
            print("  Warning: empty response from Groq")
            return {}

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            print("  Warning: truncated JSON, attempting repair...")
            last_bracket = max(clean.rfind("}]"), clean.rfind("}}"))
            if last_bracket > 0:
                clean = clean[:last_bracket + 2]
                try:
                    return json.loads(clean)
                except:
                    pass
            return {}

    return {}
    

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
- date of the patch you analyze
- do not invent information
- return valid JSON only

Title:
{title}

Content:
{content[:5000]}
"""

    data = ask_groq(prompt)

    return {
        "patch_title": data.get("patch_title", title),
        "patch_date": normalize_date(data.get("patch_date")),
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

\n\nContent:\n{content[:8000]}"""

    return ask_groq(prompt).get("jobs_pve", [])


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

\n\nContent:\n{content[:8000]}"""

    return ask_groq(prompt).get("jobs_pvp", [])


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
Valid JSON only.

\n\nContent:\n{content[:8000]}"""

    return ask_groq(prompt).get("new_content", [])

#
#def extract_housing(content, images):
#    prompt = f"""
#Extract ALL housing items.
#
#Available images:
#{json.dumps(images[:300])}
#
#Return:
#
#{{
#  "housing": [
#    {{
#      "name": "",
#      "description": "",
#      "image_url": null
#    }}
#  ]
#}}
#
#Valid JSON only.
#
#\n\nContent:\n{content[:8000]}"""
#
#    return ask_groq(prompt).get("housing", [])
#
#
#def extract_glamour(content, images):
#    prompt = f"""
#Extract ALL glamour items.
#
#Available images:
#{json.dumps(images[:300])}
#
#Return:
#
#{{
#  "glamour": [
#    {{
#      "name": "",
#      "description": "",
#      "image_url": null
#    }}
#  ]
#}}
#
#Valid JSON only.
#
#\n\nContent:\n{content[:8000]}"""
#
#    return ask_groq(prompt).get("glamour", [])


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
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def save_patch(filename, data):
    os.makedirs(PATCHES_DIR, exist_ok=True)
    with open(f"{PATCHES_DIR}/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======================================================
# Main
# ======================================================

def main():
    print("Loading index...")
    index = load_index()
    existing_files = {p["file"] for p in index}

    print("Fetching latest patch...")
    patch_url = get_latest_patch_url(existing_files)

    if not patch_url:
        print("No new patch detected.")
        return

    title, content, images = fetch_patch_content(patch_url)
    filename = slugify(title)

    if any(p["file"] == filename for p in index):
        print("Latest patch already processed.")
        return

    print("Analyzing patch...")

    metadata = extract_patch_metadata(title, content, patch_url)

    data = {
        "patch_title": metadata["patch_title"],
        "patch_date": metadata["patch_date"],
        "patch_url": metadata["patch_url"],
        "jobs_pve": extract_jobs_pve(content),
        "jobs_pvp": extract_jobs_pvp(content),
        "new_content": extract_new_content(content),
#        "housing": extract_housing(content, images),
#        "glamour": extract_glamour(content, images)
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