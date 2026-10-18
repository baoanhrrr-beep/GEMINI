import os, json

user_data = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
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

profiles = ['Default'] + [f'Profile {i}' for i in range(1, 100)]
target_profiles = []

for p in profiles:
    pref = os.path.join(user_data, p, 'Preferences')
    if os.path.isfile(pref):
        try:
            with open(pref, 'r', encoding='utf-8') as f:
                d = json.load(f)
            accs = d.get('account_info', [])
            if accs:
                emails = [a.get('email', '').lower() for a in accs]
                if any(e in pro_emails for e in emails) or any(e in verify_emails for e in emails):
                    continue
                target_profiles.append((p, emails[0]))
        except:
            pass

print(f"Total usable FREE profiles: {len(target_profiles)}")
for p, e in target_profiles:
    print(f'    "{p}",  # {e}')
