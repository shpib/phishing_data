import requests
import os
import sqlite3
from github import Github

# --- الإعدادات ---
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')
REPO_NAME = 'shpib/phishing_data'
DB_FILE = 'phishing.db'  # اسم ملف قاعدة البيانات

SOURCES = {
    'OpenPhish': 'https://openphish.com/feed.txt',
    'PhishingArmy': 'https://phishing.army/download/phishing_army_blocklist_extended.txt',
}

def update_db():
    # 1. إعداد قاعدة البيانات
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS urls 
                      (url TEXT PRIMARY KEY, source TEXT)''')
    
    # 2. جلب البيانات وإضافتها
    for name, url in SOURCES.items():
        try:
            print(f"جاري الجلب من {name}...")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                urls = response.text.splitlines()
                for u in urls:
                    if u.strip():
                        cursor.execute("INSERT OR IGNORE INTO urls (url, source) VALUES (?, ?)", (u.strip(), name))
        except Exception as e:
            print(f"خطأ في {name}: {e}")
    
    conn.commit()
    conn.close()
    print("تم تحديث قاعدة البيانات بنجاح!")

def upload_to_github():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # رفع ملف قاعدة البيانات إلى GitHub
    with open(DB_FILE, 'rb') as file:
        content = file.read()
        
    try:
        contents = repo.get_contents(DB_FILE)
        repo.update_file(contents.path, "Update SQLite DB", content, contents.sha)
    except:
        repo.create_file(DB_FILE, "Create SQLite DB", content)

if __name__ == "__main__":
    update_db()
    upload_to_github()
