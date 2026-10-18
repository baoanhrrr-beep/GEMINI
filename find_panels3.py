"""
Firebase Panel Finder v3 - Tim panel theo pattern so
Nhieu panel co ten kieu: name-XXXXX-default-rtdb.firebaseio.com
"""
import requests
import concurrent.futures
from pathlib import Path
from datetime import datetime

FOUND_FILE = "new_panels_found_v3.txt"
TIMEOUT = 6

# Pattern: ten + so (nhieu panel Jio dung ten nay)
BASE_NAMES = [
    "jio", "gem", "otp", "sms", "panel", "bot", "master",
    "rupesh", "santosh", "rahul", "rohit", "ravi", "amit",
    "rajesh", "suresh", "ramesh", "vikash", "deepak", "sanjay",
    "rohan", "sachin", "ankit", "vishal", "mohit", "lucky",
    "rinku", "bunty", "raju", "raja", "chandan", "madan",
    "sharma", "verma", "singh", "yadav", "kumar", "gupta",
    "patil", "reddy", "india", "delhi", "bihar", "up",
    "free", "new", "main", "tool", "hack", "vip", "pro",
]

# Tao danh sach: name-NUMBER
# Pham vi so: 1 den 99 + mot so so phong phu 100-9999
import itertools

def gen_urls():
    urls = set()
    for name in BASE_NAMES:
        # Ten + so 1-99
        for n in range(1, 100):
            urls.add(f"https://{name}-{n}-default-rtdb.firebaseio.com")
        # Ten + so 100-999 (bo qua de khong qua lon)
        for n in [100, 111, 123, 200, 222, 333, 404, 500, 555, 666, 777, 888, 999]:
            urls.add(f"https://{name}-{n}-default-rtdb.firebaseio.com")
        # Ten + chu cai phien ban
        for suffix in ["a", "b", "c", "x", "v1", "v2", "v3", "v4", "vip", "pro"]:
            urls.add(f"https://{name}-{suffix}-default-rtdb.firebaseio.com")
    return list(urls)

def check(url):
    try:
        r = requests.get(f"{url}/clients.json", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and len(data) > 0:
                online = sum(1 for v in data.values() if isinstance(v, dict) and v.get("status") is True)
                return url, True, online
        return url, False, r.status_code
    except Exception:
        return url, False, -1

def main():
    urls = gen_urls()
    print(f"Checking {len(urls)} URLs...")
    print(f"Start: {datetime.now().strftime('%H:%M:%S')}\n")

    found = []
    checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = {ex.submit(check, u): u for u in urls}
        for fut in concurrent.futures.as_completed(futures):
            url, ok, info = fut.result()
            checked += 1
            if ok:
                print(f"[FOUND] {url} -> {info} devices")
                found.append(url)
                with open(FOUND_FILE, "a", encoding="utf-8") as f:
                    f.write(url + "\n")
            elif checked % 200 == 0:
                print(f"  {checked}/{len(urls)}...")

    print(f"\n{'='*55}")
    print(f"DONE - {len(found)} panels found / {len(urls)} checked")
    for u in found:
        print(f"  {u}")

if __name__ == "__main__":
    main()
