import requests
import os
from github import Github

# --- الإعدادات ---
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')
REPO_NAME = 'shpib/phishing_data'
FILE_PATH = 'data1.txt'

# قائمة المصادر التي تريد الجلب منها
SOURCES = {
    'OpenPhish': 'https://openphish.com/feed.txt',
    'PhishingArmy': 'https://phishing.army/download/phishing_army_blocklist_extended.txt',
    # أضف هنا أي روابط أخرى تريدها
}

def update_repo():
    if not GITHUB_TOKEN:
        print("خطأ: لم يتم العثور على التوكن!")
        return

    all_data = []

    # 1. جلب البيانات من كافة المصادر
    for name, url in SOURCES.items():
        try:
            print(f"جاري الجلب من {name}...")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                all_data.append(f"# --- {name} Data ---")
                all_data.append(response.text)
            else:
                print(f"فشل الجلب من {name}، كود الخطأ: {response.status_code}")
        except Exception as e:
            print(f"خطأ أثناء الاتصال بـ {name}: {e}")

    if not all_data:
        print("لم يتم جلب أي بيانات من أي مصدر.")
        return

    final_content = "\n".join(all_data)

    # 2. الاتصال بـ GitHub
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # 3. تحديث الملف
    try:
        try:
            contents = repo.get_contents(FILE_PATH)
            repo.update_file(
                path=contents.path,
                message="Auto-update: Refreshing phishing data from multiple sources",
                content=final_content,
                sha=contents.sha
            )
        except:
            # إذا لم يكن الملف موجوداً، سيتم إنشاؤه
            repo.create_file(FILE_PATH, "Initial commit: Add phishing data", final_content)
        
        print("تم التحديث بنجاح من كافة المصادر!")
    except Exception as e:
        print(f"حدث خطأ أثناء الرفع إلى GitHub: {e}")

if __name__ == "__main__":
    update_repo()
