"""
cloud_watchdog.py - Tự động kiểm tra liên tục 5 máy chủ Cloud GitHub,
sửa lỗi nếu có (hủy run treo, kích hoạt lại run chết),
và kéo link mới về thẳng máy tính.
"""

import sys
import time
import base64
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests

BASE_DIR = Path(__file__).resolve().parent
LOCAL_FILE = BASE_DIR / "gemini_activation_links.txt"
LOCAL_FRESH = BASE_DIR / "gemini_links_fresh.txt"
LOCAL_USED = BASE_DIR / "gemini_links_used.txt"

CLOUD_REPOS = [
    {"user": "vananhyyy3-glitch", "token": "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", "repo": "vananhyyy3-glitch/GEMINI"},
    {"user": "bashopee2-droid",   "token": "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", "repo": "bashopee2-droid/GEMINI"},
    {"user": "baoanh200637-arch", "token": "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", "repo": "baoanh200637-arch/GEMINI"},
    {"user": "baoanh2000xx-blip", "token": "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", "repo": "baoanh2000xx-blip/GEMINI"},
    {"user": "anhv98635-lab",     "token": "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", "repo": "anhv98635-lab/GEMINI"},
]


def get_token(url: str) -> str:
    return url.split("?")[0].rstrip("/").split("/")[-1].strip()


def get_used_info() -> tuple[set[str], set[str]]:
    if not LOCAL_USED.exists():
        return set(), set()
    used_lines = [l.strip() for l in LOCAL_USED.read_text(encoding="utf-8").splitlines() if l.strip()]
    used_urls = set(used_lines)
    used_tokens = set(get_token(u) for u in used_lines)
    return used_urls, used_tokens


def get_local_links() -> set[str]:
    if not LOCAL_FILE.exists():
        return set()
    return set(l.strip() for l in LOCAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip())


def append_links(new_links: list[str]) -> int:
    if not new_links:
        return 0
    existing = get_local_links()
    used_urls, used_tokens = get_used_info()

    to_add = []
    seen = set()
    for l in new_links:
        tok = get_token(l)
        if l not in existing and l not in used_urls and tok not in used_tokens and l not in seen:
            to_add.append(l)
            seen.add(l)

    if not to_add:
        return 0

    with LOCAL_FILE.open("a", encoding="utf-8") as f:
        for l in to_add:
            f.write(l + "\n")

    with LOCAL_FRESH.open("a", encoding="utf-8") as f:
        for l in to_add:
            f.write(l + "\n")

    return len(to_add)


import json
import urllib.request
import urllib.error

def gh_api_request(url: str, headers: dict, data: dict = None, method: str = None) -> tuple[int, dict | list | str]:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            status = res.getcode()
            raw_text = res.read().decode("utf-8", errors="replace")
            try:
                return status, json.loads(raw_text)
            except Exception:
                return status, raw_text
    except urllib.error.HTTPError as e:
        raw_text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw_text)
        except Exception:
            return e.code, raw_text
    except Exception as e:
        raise e


def check_and_fix_repo(item: dict) -> None:
    repo = item["repo"]
    token = item["token"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Gemini-Watchdog",
        "Content-Type": "application/json"
    }

    print(f"\n--- [KIỂM TRA] {repo} ---")

    # 1. Kéo link mới từ repo
    try:
        status, data = gh_api_request(f"https://api.github.com/repos/{repo}/contents/gemini_activation_links.txt", headers=headers)
        if status == 200 and isinstance(data, dict):
            content_b64 = data.get("content", "")
            raw = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            links = [l.strip() for l in raw.splitlines() if l.strip() and "serviceactivation.google.com" in l]
            added = append_links(links)
            if added > 0:
                print(f"  [+] ĐÃ KÉO THÀNH CÔNG: +{added} link mới tinh về file!")
            else:
                print(f"  [*] Repo có {len(links)} link (đã được lưu hoặc đã dùng).")
        elif status == 404:
            print("  [*] File gemini_activation_links.txt chưa tồn tại trên repo.")
        else:
            print(f"  [!] HTTP {status} khi kéo link.")
    except Exception as e:
        print(f"  [!] Lỗi kéo link: {e}")

    # 2. Kiểm tra trạng thái runs
    try:
        status, data = gh_api_request(f"https://api.github.com/repos/{repo}/actions/runs?per_page=5", headers=headers)
        if status == 200 and isinstance(data, dict):
            runs = data.get("workflow_runs", [])
            in_progress = [r for r in runs if r.get("status") == "in_progress"]
            pending = [r for r in runs if r.get("status") in ("pending", "queued", "waiting")]
            
            print(f"  [*] Trạng thái: {len(in_progress)} đang chạy | {len(pending)} đang chờ")

            # Nếu không có run nào đang chạy và không có run nào chờ -> Kích hoạt chạy ngay
            if not in_progress and not pending:
                print("  [!] Không có máy chủ nào chạy. Đang tự động kích hoạt...")
                dispatch_url = f"https://api.github.com/repos/{repo}/actions/workflows/gemini_scanner.yml/dispatches"
                d_status, _ = gh_api_request(dispatch_url, headers=headers, data={"ref": "main"}, method="POST")
                if d_status in (204, 201, 200):
                    print("  [OK] Đã kích hoạt workflow thành công!")
                else:
                    print(f"  [!] Thất bại khi kích hoạt: {d_status}")
            
            # Nếu có quá nhiều pending (hơn 2 cái) -> Dọn dẹp các run dư thừa
            if len(pending) > 2:
                print("  [!] Phát hiện hàng chờ bị ứ đọng, đang dọn bớt...")
                for p in pending[2:]:
                    gh_api_request(f"https://api.github.com/repos/{repo}/actions/runs/{p['id']}/cancel", headers=headers, method="POST")
        else:
            print(f"  [!] HTTP {status} khi kiểm tra Actions.")
    except Exception as e:
        print(f"  [!] Lỗi kiểm tra Actions: {e}")


def run_watchdog():
    print("=" * 70)
    print("   GEMINI CLOUD WATCHDOG - TỰ ĐỘNG THEO DÕI VÀ SỬA LỖI CLOUD")
    print("=" * 70)
    for item in CLOUD_REPOS:
        check_and_fix_repo(item)
    print("\n" + "=" * 70)
    print("   HOÀN TẤT VÒNG KIỂM TRA!")
    print("=" * 70)


if __name__ == "__main__":
    run_watchdog()
