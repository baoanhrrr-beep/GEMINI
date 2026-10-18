"""
check_links.py
Quet va loc file gemini_activation_links.txt:
  - EXPIRED: co chu "need a new activation link" / "can mot duong lien ket kich hoat moi" -> XOA
  - USED:    co chu "already been used" / "da duoc su dung"                                -> XOA
  - FRESH:   hien nut "Get started" / "Bat dau" / "Kich hoat"                            -> GIU LAI
"""

import sys
import time
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
TOOL_DIR       = Path(__file__).parent
LINKS_FILE     = TOOL_DIR / "gemini_activation_links.txt"
LINKS_USED     = TOOL_DIR / "gemini_links_used.txt"
LINKS_FRESH    = TOOL_DIR / "gemini_links_fresh.txt"
TIMEOUT        = 18   # seconds per request
DELAY_BETWEEN  = 0.8  # seconds between checks (tranh bi block)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EXPIRED_KEYWORDS = [
    "need a new activation link",
    "cần một đường liên kết kích hoạt mới",
    "can mot duong lien ket kich hoat moi",
    "new activation link",
    "request a new link",
    "link is no longer valid",
    "link expired",
    "activation link has expired",
    "liên kết không còn hợp lệ",
]

USED_KEYWORDS = [
    "already been used",
    "this subscription link has",
    "link has already been used",
    "gói thuê bao này đã được sử dụng",
    "đã được sử dụng",
    "subscription has been used",
]

# ── Colors (ANSI) ─────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"

def colored(text, color): return f"{color}{text}{C.RESET}"

# ── Core checker ──────────────────────────────────────────────────────────────
def check_link(url: str) -> str:
    """
    Returns: 'fresh' | 'expired' | 'used' | 'unknown'
    Logic:
      Buoc 1 (khong follow redirect): xem redirect dau tien den dau
        -> accounts.google.com/signin  = fresh  (link can dang nhap, van hop le)
        -> one.google.com / serviceactivation = co the het han, follow de check body
      Buoc 2 (follow het redirect): check body + URL cuoi
    """
    try:
        # Buoc 1: check redirect dau tien
        r1 = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False)
        loc = r1.headers.get("Location", "")

        if r1.status_code in (301, 302, 303, 307, 308) and loc:
            # Link chuyen thang ve trang dang nhap -> con song
            if "accounts.google.com" in loc and ("signin" in loc or "/v3/" in loc or "servicelogin" in loc.lower()):
                return "fresh"

            # Link chuyen ve trang one.google.com hoac serviceactivation -> check body
            if "one.google.com" in loc or "serviceactivation.google.com" in loc:
                try:
                    r2 = requests.get(loc, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
                    body = r2.text.lower()
                    for kw in EXPIRED_KEYWORDS:
                        if kw.lower() in body:
                            return "expired"
                    for kw in USED_KEYWORDS:
                        if kw.lower() in body:
                            return "used"
                    if r2.status_code == 200:
                        return "fresh"
                except Exception:
                    pass
                return "unknown"

        # Buoc 2: follow tat ca redirect, check body + URL cuoi
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        final_url = r.url.lower()
        body      = r.text.lower()

        for kw in USED_KEYWORDS:
            if kw.lower() in body:
                return "used"
        for kw in EXPIRED_KEYWORDS:
            if kw.lower() in body:
                return "expired"
        if r.status_code in (404, 410):
            return "expired"
        if "accounts.google.com" in final_url and "signin" in final_url:
            return "fresh"
        if r.status_code == 200 and "one.google.com" in final_url:
            return "fresh"
        return "unknown"

    except requests.Timeout:
        return "unknown"
    except Exception:
        return "unknown"

# ── File helpers ──────────────────────────────────────────────────────────────
def read_links(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip().startswith("http")]

def write_links(path: Path, links: list[str]):
    path.write_text("\n".join(links) + ("\n" if links else ""), encoding="utf-8")

def append_unique(path: Path, url: str):
    existing = set(read_links(path)) if path.exists() else set()
    if url not in existing:
        with path.open("a", encoding="utf-8") as f:
            f.write(url + "\n")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Enable ANSI on Windows
    import os
    os.system("")

    print(colored("=" * 62, C.BOLD))
    print(colored("  GEMINI LINK CHECKER", C.BOLD + C.CYAN))
    print(colored("=" * 62, C.BOLD))

    links = read_links(LINKS_FILE)
    if not links:
        print(colored(f"\n  Khong co link nao trong {LINKS_FILE.name}", C.YELLOW))
        input("\n  [Enter de thoat]")
        return

    total = len(links)
    print(f"\n  File  : {colored(str(LINKS_FILE), C.CYAN)}")
    print(f"  Tong  : {colored(str(total), C.BOLD)} links")
    print(colored("\n  Bam Enter de bat dau quet...", C.DIM))
    input()

    fresh_links   = []
    expired_links = []
    used_links    = []
    unknown_links = []

    for i, url in enumerate(links, 1):
        short = url[-65:] if len(url) > 65 else url
        print(f"  [{i:>3}/{total}] {colored(short, C.DIM)} ", end="", flush=True)

        status = check_link(url)

        if status == "fresh":
            fresh_links.append(url)
            print(colored("✓ FRESH", C.GREEN))
        elif status == "expired":
            expired_links.append(url)
            print(colored("✗ EXPIRED (het han)", C.RED))
            append_unique(LINKS_USED, url)
        elif status == "used":
            used_links.append(url)
            print(colored("✗ USED (da dung)", C.RED))
            append_unique(LINKS_USED, url)
        else:
            unknown_links.append(url)
            print(colored("? UNKNOWN", C.YELLOW))

        if i < total:
            time.sleep(DELAY_BETWEEN)

    # ── Luu ket qua ──────────────────────────────────────────
    # Ghi de file chinh chi giu fresh + unknown
    kept = fresh_links + unknown_links
    write_links(LINKS_FILE, kept)
    write_links(LINKS_FRESH, fresh_links)

    # ── Summary ───────────────────────────────────────────────
    print()
    print(colored("=" * 62, C.BOLD))
    print(colored("  KET QUA", C.BOLD))
    print(colored("=" * 62, C.BOLD))
    print(f"  {colored(str(len(fresh_links)),   C.GREEN)}  link FRESH   (con dung duoc)  -> GIU LAI")
    print(f"  {colored(str(len(expired_links)), C.RED)}  link EXPIRED (het han)         -> DA XOA")
    print(f"  {colored(str(len(used_links)),    C.RED)}  link USED    (da dung roi)     -> DA XOA")
    print(f"  {colored(str(len(unknown_links)), C.YELLOW)}  link UNKNOWN (ko xac dinh)    -> GIU LAI")
    print(colored("=" * 62, C.BOLD))
    print(f"\n  File da cap nhat: {colored(str(LINKS_FILE.name), C.CYAN)}")
    print(f"  Con lai         : {colored(str(len(kept)), C.BOLD)} links\n")
    input("  [Enter de thoat]")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
