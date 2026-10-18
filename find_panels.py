"""
Firebase Panel Finder - tìm panel mới có dữ liệu Jio SMS
Thử các tên Firebase phổ biến từ cộng đồng tool Ấn Độ
"""
import requests
import concurrent.futures
from datetime import datetime

# Danh sách tên Firebase phổ biến — kết hợp tên + số
NAMES = [
    # Tên phổ biến trong cộng đồng tool Jio
    "jiopanel", "jiogem", "jiomaster", "jiomain", "jiobot",
    "gemmaster", "gempanel", "gembot", "gemactivate",
    "masterbot", "masterpanel", "mainpanel", "mainbot",
    "otpmaster", "otppanel", "otpbot", "otpreader",
    "smspanel", "smsbot", "smsmaster", "smsreader",
    "activator", "activation", "activepanel",
    "indiabot", "indiapanel", "indiamaster",
    "jioactivation", "jiootp", "jiolink",
    "panel1", "panel2", "panel3", "panel4", "panel5",
    "mypanel", "mybot", "mymaster",
    "freegem", "freegoogle", "gemfree",
    "googleai", "googleone", "googlegem",
    "recharge1", "recharge2", "rechargepanel",
    "rupesh", "santosh", "rajesh", "suresh", "ramesh",
    "vikash", "vikram", "rahul", "rohit", "ravi",
    "priya", "pooja", "neha", "anita", "sunita",
    "delhi", "mumbai", "kolkata", "chennai", "bangalore",
    "india1", "india2", "india3",
    "tool1", "tool2", "tool3", "toolpanel",
    "hack1", "hack2", "hackpanel",
    "free1", "free2", "freepanel",
    "newpanel", "newbot", "newmaster",
    "testpanel", "testbot", "test1", "test2",
    "autobot", "automaster", "autopanel",
    "kingpanel", "kingbot", "kingmaster",
    "bossbot", "bosspanel", "bossmaster",
    "superbot", "superpanel", "supermaster",
    "jio1", "jio2", "jio3", "jio4", "jio5",
    "jio10", "jio11", "jio12", "jio13",
    "gem1", "gem2", "gem3", "gem4", "gem5",
    "otp1", "otp2", "otp3", "otp4", "otp5",
    "sms1", "sms2", "sms3", "sms4", "sms5",
]

# Thêm suffix số
SUFFIXES = ["", "-1", "-2", "-3", "-v2", "-v3", "-new", "-main", "-master", "-bot"]

TIMEOUT = 8
FOUND_FILE = "new_panels_found.txt"

def check_panel(url: str) -> tuple[str, bool, int]:
    try:
        r = requests.get(f"{url}/clients.json", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and len(data) > 0:
                # Kiểm tra có device online không
                online = sum(1 for v in data.values() if isinstance(v, dict) and v.get("status") is True)
                return url, True, online
        return url, False, r.status_code
    except Exception:
        return url, False, -1

def main():
    # Tạo danh sách URL cần thử
    urls = []
    for name in NAMES:
        for suffix in SUFFIXES:
            full = f"{name}{suffix}"
            # Firebase tên project phải lowercase, chỉ chứa chữ và số và dấu gạch
            urls.append(f"https://{full}-default-rtdb.firebaseio.com")

    print(f"Checking {len(urls)} potential Firebase panels...")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}\n")

    found = []
    checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(check_panel, url): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            url, success, info = future.result()
            checked += 1
            if success:
                online_count = info
                print(f"[FOUND] {url} -> {online_count} devices online")
                found.append(f"{url}  # {online_count} devices online")
                # Lưu ngay vào file
                with open(FOUND_FILE, "a") as f:
                    f.write(f"{url}\n")
            elif checked % 50 == 0:
                print(f"  Checked {checked}/{len(urls)}...")

    print(f"\n{'='*60}")
    print(f"DONE — Found {len(found)} live panels out of {len(urls)} checked")
    print(f"Saved to: {FOUND_FILE}")
    for f in found:
        print(f"  {f}")

if __name__ == "__main__":
    main()
