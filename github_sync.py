import os
import base64
import requests

# ================== CONFIG ==================
GITHUB_TOKEN = "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"  # <-- paste token here
USERNAME = "zihad-sudo"
REPO = "Miss-Zeba"
BRANCH = "main"

# Upload EVERYTHING from where this script lives
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

API_URL = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

IGNORE = {".git", "__pycache__", ".idea", ".vscode"}
# ============================================

def upload_file(local_path, repo_path):
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"{API_URL}/{repo_path.replace(os.sep, '/')}"

    r = requests.get(url, headers=HEADERS)
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": f"Sync {repo_path}",
        "content": content,
        "branch": BRANCH
    }

    if sha:
        data["sha"] = sha

    res = requests.put(url, headers=HEADERS, json=data)

    if res.status_code in (200, 201):
        print("✔ Uploaded:", repo_path)
    else:
        print("✖ Failed:", repo_path, res.text)


def sync():
    for root, dirs, files in os.walk(LOCAL_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE]

        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, LOCAL_DIR)

            if any(p in IGNORE for p in rel_path.split(os.sep)):
                continue

            upload_file(full_path, rel_path)


if __name__ == "__main__":
    sync()
    print("\n✅ GitHub upload complete")
