"""
check_links_chrome.py
Kiem tra chinh xac tung link trong gemini_activation_links.txt bang Chrome that (Profile 102):
- EXPIRED: hien "need a new activation link" / "cần một đường liên kết kích hoạt mới" -> XOA
- USED:    hien "already been used" / "đã được sử dụng"                                -> XOA
- FRESH:   hien nut "Get started" / "Bắt đầu" / "Kích hoạt gói"                        -> GIU LAI (KHONG BAM NUT)
"""

import os
import sys
import time
import json
import socket
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests as req_lib
import websocket

TOOL_DIR       = Path(__file__).parent
LINKS_FILE     = TOOL_DIR / "gemini_activation_links.txt"
FRESH_FILE     = TOOL_DIR / "gemini_links_fresh.txt"
USED_FILE      = TOOL_DIR / "gemini_links_used.txt"

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.isfile(CHROME_EXE):
    CHROME_EXE = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
USER_DATA_LINK = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\UserDataLink")
TARGET_PROFILE = "Profile 102"  # Profile namanhanh76@gmail.com


def ensure_junction():
    if not os.path.exists(USER_DATA_LINK):
        subprocess.run(f'cmd /c mklink /J "{USER_DATA_LINK}" "{USER_DATA}"', shell=True, capture_output=True)


def free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def wait_port(port, timeout=25):
    dl = time.time() + timeout
    while time.time() < dl:
        try:
            s = socket.create_connection(("localhost", port), timeout=0.5)
            s.close()
            return True
        except Exception:
            time.sleep(0.4)
    return False


def kill_chrome_wait():
    for proc in ["chrome.exe", "chrome_elevation_service.exe", "chrome_crashpad_handler.exe"]:
        subprocess.run(["taskkill", "/f", "/im", proc], capture_output=True)
    time.sleep(1.5)

    for attempt in range(6):
        r = subprocess.run(
            ["tasklist", "/fi", "imagename eq chrome.exe", "/fo", "csv"],
            capture_output=True, text=True
        )
        if "chrome.exe" not in r.stdout.lower():
            break
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
        time.sleep(1)

    for base in [USER_DATA, USER_DATA_LINK]:
        if os.path.exists(base):
            for name in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
                p = os.path.join(base, name)
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
    time.sleep(1)


def reset_profile_crash_state(profile):
    prof_dir = os.path.join(USER_DATA, profile)
    pref_path = os.path.join(prof_dir, "Preferences")
    if os.path.isfile(pref_path):
        try:
            with open(pref_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if "profile" in d:
                d["profile"]["exit_type"] = "Normal"
                d["profile"]["exited_cleanly"] = True
            with open(pref_path, "w", encoding="utf-8") as f:
                json.dump(d, f)
        except Exception:
            pass


class CDP:
    def __init__(self, port):
        self.port = port
        self._id = 0
        self.ws = None

    def connect(self, retries=15):
        for attempt in range(retries):
            try:
                r = req_lib.get(f"http://localhost:{self.port}/json/list", timeout=5)
                tabs = r.json()
                page_tabs = [t for t in tabs if t.get("type") == "page"]
                tab = next((t for t in page_tabs if "blank" in t.get("url", "")), None)
                if not tab and page_tabs:
                    tab = page_tabs[0]
                if tab:
                    ws_url = tab["webSocketDebuggerUrl"]
                    self.ws = websocket.create_connection(ws_url, timeout=30)
                    return self
            except Exception:
                time.sleep(1.2)
        raise RuntimeError("Khong the ket noi CDP tab")

    def send(self, method, params=None):
        self._id += 1
        msg = json.dumps({"id": self._id, "method": method, "params": params or {}})
        self.ws.send(msg)
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                raw = self.ws.recv()
                data = json.loads(raw)
                if data.get("id") == self._id:
                    return data.get("result", {})
            except Exception:
                break
        return {}

    def navigate(self, url):
        self.send("Page.enable")
        self.send("Runtime.enable")
        self.send("Page.navigate", {"url": url})

    def eval_js(self, js):
        r = self.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
        })
        return r.get("result", {}).get("value", "")

    def close(self):
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass


def main():
    os.system("")
    print("=" * 65)
    print("  GEMINI ACCURATE LINK CHECKER (CHROME PROFILE 102)")
    print("  - Khong click nut kich hoat -> Link fresh giu nguyen 100%")
    print("  - Xoa link het han / da dung ngay lap tuc")
    print("=" * 65)

    if not LINKS_FILE.exists():
        print(f"File {LINKS_FILE.name} khong ton tai.")
        input("\n[Enter de thoat]")
        return

    links = [l.strip() for l in LINKS_FILE.read_text(encoding="utf-8").splitlines() if l.strip().startswith("http")]
    if not links:
        print("Khong co link nao trong danh sach.")
        input("\n[Enter de thoat]")
        return

    print(f"\nTong so link can kiem tra: {len(links)}")
    print("Luu y: Trinh duyet Chrome se duoc mo len de kiem tra DOM thuc te.")
    time.sleep(1)

    kill_chrome_wait()
    reset_profile_crash_state(TARGET_PROFILE)
    ensure_junction()

    port = free_port()
    chrome_cmd = [
        CHROME_EXE,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={USER_DATA_LINK}",
        f"--profile-directory={TARGET_PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--remote-allow-origins=*",
        "--window-size=1200,800",
        "about:blank",
    ]

    print(f"\nDang khoi dong Chrome kiem tra (Port {port})...")
    subprocess.Popen(
        chrome_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )

    if not wait_port(port, timeout=25):
        print("Loi: Chrome khong mo duoc port debugging!")
        input("\n[Enter de thoat]")
        return

    try:
        cdp = CDP(port).connect()
    except Exception as e:
        print(f"Loi CDP: {e}")
        kill_chrome_wait()
        input("\n[Enter de thoat]")
        return

    fresh_links = []
    bad_links   = []

    try:
        for idx, url in enumerate(links, 1):
            short = url[-50:]
            print(f"\n[{idx:>2}/{len(links)}] Test: ...{short}")
            cdp.navigate(url)

            # Cho page render
            status = "UNKNOWN"
            is_bad = True
            reason = ""

            for sec in range(1, 10):
                time.sleep(1)
                cur_url = str(cdp.eval_js("window.location.href")).lower()
                page_text = str(cdp.eval_js("document.body ? document.body.innerText : ''")).lower()

                # 1. Kiem tra EXPIRED
                if any(k in page_text for k in [
                    "need a new activation link",
                    "cần một đường liên kết kích hoạt mới",
                    "ask your provider to send a new link",
                    "link is no longer valid",
                    "link expired",
                    "activation link has expired",
                    "liên kết không còn hợp lệ"
                ]):
                    status = "EXPIRED"
                    is_bad = True
                    reason = "You need a new activation link"
                    break

                # 2. Kiem tra ALREADY USED
                if any(k in page_text for k in [
                    "subscription has been used",
                    "already been used",
                    "already redeemed",
                    "đã được sử dụng",
                    "gói thuê bao này đã được sử dụng",
                    "offer is not available",
                    "ưu đãi không có sẵn"
                ]):
                    status = "ALREADY_USED"
                    is_bad = True
                    reason = "Link has already been used"
                    break

                # 3. Kiem tra FRESH READY (co nut kich hoat/get started ma chua bi het han)
                if any(k in page_text for k in [
                    "kích hoạt gói", "kích hoạt", "bắt đầu", "dùng thử",
                    "get started", "redeem", "activate", "claim",
                    "18 tháng", "gemini advanced", "ai premium"
                ]) and not any(k in page_text for k in ["need a new activation link", "already been used"]):
                    status = "FRESH_READY"
                    is_bad = False
                    reason = "Nhin thay nut Kich hoat / Get started"
                    break

                # 4. Redirect sign-in (neu profile bi vang login)
                if "accounts.google.com" in cur_url and ("signin" in cur_url or "identifier" in cur_url):
                    status = "LOGIN_REQUIRED"
                    is_bad = True
                    reason = "Profile bi vang dang nhap Google"
                    break

            if is_bad:
                print(f"   -> \033[91m[XOA - {status}]\033[0m {reason}")
                bad_links.append(url)
            else:
                print(f"   -> \033[92m[GIU - {status}]\033[0m {reason} (KHONG BAM NUT)")
                fresh_links.append(url)

    finally:
        cdp.close()
        kill_chrome_wait()

    # Cap nhat file
    existing_used = set(USED_FILE.read_text(encoding="utf-8").splitlines()) if USED_FILE.exists() else set()
    with USED_FILE.open("a", encoding="utf-8") as uf:
        for b in bad_links:
            if b not in existing_used:
                uf.write(b + "\n")
                existing_used.add(b)

    # Ghi de LINKS_FILE chi giu lai fresh_links
    LINKS_FILE.write_text("\n".join(fresh_links) + ("\n" if fresh_links else ""), encoding="utf-8")
    FRESH_FILE.write_text("\n".join(fresh_links) + ("\n" if fresh_links else ""), encoding="utf-8")

    print("\n" + "=" * 65)
    print("  KET QUA KIEM TRA:")
    print(f"  + Link FRESH (dung tot, con nguyen): \033[92m{len(fresh_links)}\033[0m")
    print(f"  + Link LOI (da xoa):                 \033[91m{len(bad_links)}\033[0m")
    print(f"  + File cap nhat:                     gemini_activation_links.txt")
    print("=" * 65)
    input("\n[Enter de hoan tat]")


if __name__ == "__main__":
    main()
