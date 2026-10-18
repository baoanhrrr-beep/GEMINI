"""
sync_cloud_links.py
Tự động đồng bộ và gom tất cả link kích hoạt mới từ 5 máy chủ Cloud GitHub
về thẳng file gemini_activation_links.txt trên máy tính của bạn.
Chạy ngầm liên tục 24/24 - Cứ có link mới trên Cloud là tự kéo về máy ngay lập tức!
"""

import time
import base64
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests

LOCAL_FILE = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_activation_links.txt")
LOCAL_FRESH = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_links_fresh.txt")

# 5 Tài khoản Cloud GitHub đã thiết lập
CLOUD_ACCOUNTS = {
    "vananhyyy3-glitch": "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",
    "bashopee2-droid":   "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",
    "baoanh200637-arch": "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",
    "baoanh2000xx-blip": "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",
    "anhv98635-lab":     "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",
}

POLL_INTERVAL_SECONDS = 30  # Kiểm tra các máy chủ Cloud mỗi 30 giây


def get_local_links() -> set[str]:
    if not LOCAL_FILE.exists():
        return set()
    return set(l.strip() for l in LOCAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip())


def append_local_links(new_links: list[str]) -> None:
    if not new_links:
        return
    existing = get_local_links()
    to_add = [l for l in new_links if l not in existing]
    if not to_add:
        return

    with LOCAL_FILE.open("a", encoding="utf-8") as f:
        for l in to_add:
            f.write(l + "\n")

    with LOCAL_FRESH.open("a", encoding="utf-8") as f:
        for l in to_add:
            f.write(l + "\n")

    print(f"\n{'='*70}")
    print(f"[ĐÃ KÉO VỀ MÁY] +{len(to_add)} LINK MỚI TỪ CLOUD!")
    for l in to_add:
        print(f"  -> {l[:85]}...")
    print(f"Tổng số link hiện có trong file: {len(existing) + len(to_add)}")
    print(f"{'='*70}\n")


def fetch_repo_links(username: str, token: str) -> list[str]:
    url = f"https://api.github.com/repos/{username}/GEMINI/contents/gemini_activation_links.txt"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Gemini-Cloud-Sync"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            content_b64 = r.json().get("content", "")
            raw_text = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            return [l.strip() for l in raw_text.splitlines() if l.strip()]
    except Exception:
        pass
    return []


def main():
    print("=" * 70)
    print("   HỆ THỐNG ĐỒNG BỘ LINK CLOUD VỀ MÁY TÍNH (CLOUD LINK SYNC)")
    print("   Theo dõi liên tục 5 máy chủ GitHub Cloud 24/24")
    print(f"   Đích lưu: {LOCAL_FILE.name}")
    print("=" * 70)

    loop = 0
    while True:
        loop += 1
        now_str = time.strftime("%H:%M:%S")
        sys.stdout.write(f"\r[{now_str}] Vòng kiểm tra #{loop} - Đang đồng bộ 5 máy chủ Cloud... ")
        sys.stdout.flush()

        all_cloud_links = []
        for user, tok in CLOUD_ACCOUNTS.items():
            links = fetch_repo_links(user, tok)
            all_cloud_links.extend(links)

        append_local_links(all_cloud_links)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
