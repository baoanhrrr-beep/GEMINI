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

verify_emails = {
    'nguyenvananhahnsao@gmail.com', 'nguyenthuyduong20671@gmail.com',
    'nguyenvancanhw207@gmail.com', 'duongvanlammmas@gmail.com'
}

# 1. Read Local State to get all profiles
local_state_file = os.path.join(USER_DATA, 'Local State')
with open(local_state_file, 'r', encoding='utf-8') as f:
    ls = json.load(f)

info_cache = ls.get('profile', {}).get('info_cache', {})

pro_list = []
verify_list = []
free_list = []

for prof_key, info in sorted(info_cache.items(), key=lambda x: (len(x[0]), x[0])):
    user_name = info.get('user_name', '').lower()
    name = info.get('name', '')
    
    if any(e in user_name for e in pro_emails):
        pro_list.append((prof_key, user_name, name))
    elif any(e in user_name for e in verify_emails):
        verify_list.append((prof_key, user_name, name))
    else:
        free_list.append((prof_key, user_name, name))

print("=" * 60)
print(f"1. CÁC PROFILE ĐÃ CÓ PRO ({len(pro_list)} profile):")
for p, u, n in pro_list:
    print(f"   - {p:12}: {u} ({n})")

print(f"\n2. CÁC PROFILE CẦN XÁC MINH LẠI ({len(verify_list)} profile):")
for p, u, n in verify_list:
    print(f"   - {p:12}: {u} ({n})")

print(f"\n3. CÁC PROFILE CHƯA CÓ GEMINI PRO ({len(free_list)} profile):")
for p, u, n in free_list:
    print(f"   - {p:12}: {u} ({n})")
print("=" * 60)

# 2. Check which profiles are already running
running_cmd = subprocess.getoutput('wmic process where "name=\'chrome.exe\'" get commandline')
already_running = set()
for p, _, _ in free_list:
    if f"--profile-directory={p}" in running_cmd or f'--profile-directory="{p}"' in running_cmd:
        already_running.add(p)

to_launch = [item for item in free_list if item[0] not in already_running]

print(f"\nĐang mở sẵn: {len(already_running)} profile: {list(already_running)}")
print(f"Cần mở tiếp: {len(to_launch)} profile")

# 3. Launch remaining free profiles
for i, (prof_key, user_name, name) in enumerate(to_launch, start=1):
    print(f"[{i}/{len(to_launch)}] Đang mở {prof_key} ({user_name})...")
    subprocess.Popen([CHROME_EXE, f"--profile-directory={prof_key}"])
    time.sleep(0.5)

print("\nĐã mở toàn bộ profile chưa có Gemini Pro!")
