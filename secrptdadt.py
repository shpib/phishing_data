import requests
import os
from github import Github

# --- الإعدادات ---
# سنقوم بتعريف التوكن كمتغير بيئي (Environment Variable)
# لا تضع التوكن هنا مباشرة!
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN') 
REPO_NAME = 'shpib/phishing_data'
FILE_PATH = 'data1.txt'
OPENPHISH_URL = 'https://openphish.com/feed.txt'

def update_repo():
    if not GITHUB_TOKEN:
        print("خطأ: لم يتم العثور على التوكن! تأكد من ضبط متغير البيئة MY_GITHUB_TOKEN")
        return

    # 1. جلب البيانات من OpenPhish
    try:
        response = requests.get(OPENPHISH_URL)
        new_data = response.text if response.status_code == 200 else None
    except Exception as e:
        print(f"خطأ في الاتصال بالموقع: {e}")
        return

    if not new_data:
        print("لم يتم جلب أي بيانات.")
        return

    # 2. الاتصال بـ GitHub
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # 3. تحديث الملف
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(
            path=contents.path,
            message="Auto-update: Refreshing phishing data from OpenPhish",
            content=new_data,
            sha=contents.sha
        )
        print("تم التحديث بنجاح!")
    except Exception as e:
        print(f"حدث خطأ أثناء الرفع إلى GitHub: {e}")

if __name__ == "__main__":
    update_repo()
