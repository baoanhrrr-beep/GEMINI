import os, json

user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
local_state_path = os.path.join(user_data, "Local State")

target_email = "namanhanh76@gmail.com"
found = None

if os.path.exists(local_state_path):
    try:
        data = json.load(open(local_state_path, encoding="utf-8"))
        info_cache = data.get("profile", {}).get("info_cache", {})
        for prof, details in info_cache.items():
            user_name = details.get("user_name", "")
            name = details.get("name", "")
            if target_email.lower() in user_name.lower():
                found = prof
                print(f"FOUND_PROFILE: {prof}")
                break
        if not found:
            # Check default or others
            for prof, details in info_cache.items():
                if "Anh Nam" in details.get("name", ""):
                    found = prof
                    print(f"FOUND_PROFILE_BY_NAME: {prof}")
                    break
    except Exception as e:
        print("Error:", e)

if not found:
    print("NOT_FOUND")
