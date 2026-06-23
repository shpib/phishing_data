import requests
import os
import sqlite3
import hashlib
import gzip
import shutil
import json
from github import Github
from datetime import datetime

# =====================
# الإعدادات
# =====================
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')
REPO_NAME = 'shpib/phishing_data'

DB_FILE = 'phishing.db'
COMPRESSED_FILE = 'phishing.db.gz'
HASH_FILE = 'sha256.txt'
VERSION_FILE = 'version.json'

SOURCES = {
    'OpenPhish': 'https://openphish.com/feed.txt',
    'PhishingArmy': 'https://phishing.army/download/phishing_army_blocklist_extended.txt',
}

# =====================
# تحديث قاعدة البيانات
# =====================
def update_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            url TEXT PRIMARY KEY,
            source TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS change_log (
            url TEXT,
            action TEXT,
            timestamp TEXT
        )
    ''')

    for name, url in SOURCES.items():
        try:
            print(f"جاري الجلب من {name}...")
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                urls = response.text.splitlines()

                for u in urls:
                    u = u.strip()
                    if u:
                        cursor.execute(
                            "INSERT OR IGNORE INTO urls (url, source) VALUES (?, ?)",
                            (u, name)
                        )

                        cursor.execute(
                            "INSERT INTO change_log VALUES (?, ?, datetime('now'))",
                            (u, "add")
                        )

        except Exception as e:
            print(f"خطأ في {name}: {e}")

    conn.commit()
    conn.close()
    print("تم تحديث قاعدة البيانات")


# =====================
# SHA256
# =====================
def generate_sha256():
    sha256 = hashlib.sha256()

    with open(DB_FILE, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    hash_value = sha256.hexdigest()

    with open(HASH_FILE, "w") as f:
        f.write(hash_value)

    print("SHA256:", hash_value)
    return hash_value


# =====================
# ضغط قاعدة البيانات
# =====================
def compress_db():
    with open(DB_FILE, 'rb') as f_in:
        with gzip.open(COMPRESSED_FILE, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    print("تم ضغط قاعدة البيانات")


# =====================
# إنشاء Delta Update
# =====================
def generate_delta():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT url FROM change_log WHERE action='add'")
    added = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT url FROM change_log WHERE action='remove'")
    removed = [row[0] for row in cursor.fetchall()]

    conn.close()

    version = datetime.utcnow().strftime("%Y.%m.%d.%H%M")

    delta = {
        "version": version,
        "added": added,
        "removed": removed
    }

    file_name = f"delta_{version}.json"

    with open(file_name, "w") as f:
        json.dump(delta, f, indent=4)

    print("تم إنشاء Delta:", file_name)
    return file_name


# =====================
# version.json
# =====================
def update_version(delta_file, sha):
    data = {
        "version": datetime.utcnow().strftime("%Y.%m.%d.%H%M"),
        "full_db": COMPRESSED_FILE,
        "latest_delta": delta_file,
        "sha256": sha
    }

    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("تم إنشاء version.json")


# =====================
# رفع إلى GitHub
# =====================
def upload_to_github():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    files = [
        DB_FILE,
        COMPRESSED_FILE,
        HASH_FILE,
        VERSION_FILE
    ]

    # إضافة ملفات delta تلقائياً
    for f in os.listdir():
        if f.startswith("delta_") and f.endswith(".json"):
            files.append(f)

    for file_name in files:
        try:
            with open(file_name, 'rb') as f:
                content = f.read()

            try:
                contents = repo.get_contents(file_name)
                repo.update_file(contents.path, "update", content, contents.sha)
            except:
                repo.create_file(file_name, "create", content)

        except Exception as e:
            print(f"خطأ رفع {file_name}: {e}")

    print("تم رفع كل الملفات")


# =====================
# التشغيل الرئيسي
# =====================
if __name__ == "__main__":
    update_db()
    sha = generate_sha256()
    compress_db()
    delta_file = generate_delta()
    update_version(delta_file, sha)
    upload_to_github()
