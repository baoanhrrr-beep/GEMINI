import os
import sys
import json
import subprocess
import time

sys.stdout.reconfigure(encoding='utf-8')

USER_DATA = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.isfile(CHROME_EXE):
    CHROME_EXE = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not os.path.isfile(CHROME_EXE):
    CHROME_EXE = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")

pro_emails = {
    'miorakia@gmail.com', 'daip33886@gmail.com', 'hoanglinhdan0402209@gmail.com',
    'daip23859@gmail.com', 'vananhyyy3@gmail.com', 'lamkhoa826@gmail.com',
    'yyuuiiiyyuu334@gmail.com', 'k5.a3.haonx@gmail.com', 'khanhtunglam598@gmail.com',
    'baoanh2000xx@gmail.com'
}

local_state_file = os.path.join(USER_DATA, 'Local State')
with open(local_state_file, 'r', encoding='utf-8') as f:
    ls = json.load(f)

info_cache = ls.get('profile', {}).get('info_cache', {})
free_profiles = []

for prof_key, info in info_cache.items():
    user_name = info.get('user_name', '').lower()
    name = info.get('name', '')
    if not any(e in user_name for e in pro_emails):
        free_profiles.append((prof_key, user_name, name))

free_profiles = sorted(free_profiles, key=lambda x: (len(x[0]), x[0]))

print(f"Bắt đầu mở {len(free_profiles)} profile Chrome chưa có Gemini Pro lên màn hình...")

for i, (p, email, name) in enumerate(free_profiles, start=1):
    print(f"[{i:02d}/{len(free_profiles)}] Mở {p} | {email} ({name})")
    # Launch with cmd /c start so that Windows shell spawns the actual visible GUI window
    subprocess.Popen(f'start "" "{CHROME_EXE}" --profile-directory="{p}"', shell=True)
    time.sleep(0.4)

print("\nHoàn tất mở tất cả các profile lên màn hình!")
