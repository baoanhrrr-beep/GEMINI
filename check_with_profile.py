"""
check_with_profile.py (v2 - Clean Process & Lock Handled)
Sử dụng Profile 11 (namanhanh76@gmail.com) để kiểm tra các link trong gemini_activation_links.txt.
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

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.isfile(CHROME_EXE):
    CHROME_EXE = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
USER_DATA_LINK = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\UserDataLink")
TARGET_PROFILE = "Profile 102"

def ensure_junction():
    if not os.path.exists(USER_DATA_LINK):
        subprocess.run(f'cmd /c mklink /J "{USER_DATA_LINK}" "{USER_DATA}"', shell=True, capture_output=True)

LINKS_FILE = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_activation_links.txt")
USED_FILE  = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_links_used.txt")
FRESH_FILE = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_links_fresh.txt")


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
        for name in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            p = os.path.join(base, name)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
    time.sleep(1.5)


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

    def connect(self, retries=12):
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
        raise RuntimeError("Khong ket noi duoc CDP tab")

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
        time.sleep(6.5)

    def eval_js(self, js):
        r = self.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
        })
        return r.get("result", {}).get("value", "")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main():
    if not LINKS_FILE.exists():
        print(f"File {LINKS_FILE} khong ton tai.")
        return

    links = [l.strip() for l in LINKS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not links:
        print("Khong co link nao trong danh sach.")
        return

    print("=" * 70)
    print(f"KIEM TRA VOI PROFILE: {TARGET_PROFILE} (namanhanh76@gmail.com)")
    print(f"So luong link can kiem tra: {len(links)}")
    print("=" * 70)

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

    print(f"Dang khoi dong Chrome voi profile {TARGET_PROFILE} (Port {port})...")
    proc = subprocess.Popen(
        chrome_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )

    if not wait_port(port, timeout=25):
        print("Loi: Chrome khong mo duoc port debugging!")
        return

    try:
        cdp = CDP(port).connect()
    except Exception as e:
        print("Loi CDP connect:", e)
        kill_chrome_wait()
        return

    fresh_links = []
    bad_links = []

    try:
        for idx, url in enumerate(links, 1):
            token_display = url[-45:]
            print(f"\n[{idx:02d}/{len(links)}] Dang test: ...{token_display}")

            cdp.navigate(url)

            current_url = str(cdp.eval_js("window.location.href")).lower()
            page_text   = str(cdp.eval_js("document.body ? document.body.innerText : ''")).lower()

            status = "UNKNOWN"
            is_bad = False

            if any(k in page_text for k in [
                "need a new activation link",
                "ask your provider to send a new link",
                "cần một đường liên kết kích hoạt mới",
                "link is no longer valid",
                "link expired",
                "liên kết hết hạn",
                "đường liên kết đã hết hạn",
            ]):
                status = "EXPIRED (Can link moi)"
                is_bad = True

            elif any(k in page_text for k in [
                "subscription has been used",
                "already been used",
                "already redeemed",
                "đã được sử dụng",
                "offer is not available",
                "ưu đãi không có sẵn",
            ]):
                status = "ALREADY_USED (Da dung)"
                is_bad = True

            elif any(k in page_text for k in [
                "get started", "redeem", "activate", "claim",
                "kích hoạt gói", "kích hoạt", "bắt đầu", "thử ngay",
                "18 tháng", "gemini advanced", "ai premium"
            ]):
                status = "FRESH_READY (Link con dung tot!)"
                is_bad = False

            elif "activate-plan" in current_url or "subscription/new" in current_url:
                if "error" in page_text or "not available" in page_text:
                    status = "BAD_ERROR"
                    is_bad = True
                else:
                    status = "FRESH_PAGE"
                    is_bad = False
            else:
                status = "OTHER_BAD"
                is_bad = True

            if is_bad:
                print(f"   -> [XOA] {status}")
                bad_links.append(url)
            else:
                print(f"   -> [GIU] {status}")
                fresh_links.append(url)

    finally:
        cdp.close()
        kill_chrome_wait()

    print("\n" + "=" * 70)
    print("HOAN TAT KIEM TRA:")
    print(f"  + Link DUNG DUOC (Con song) : {len(fresh_links)}")
    print(f"  + Link RAC / HET HAN (Da xoa): {len(bad_links)}")
    print("=" * 70)

    # Luu bad links
    if bad_links:
        existing_used = set()
        if USED_FILE.exists():
            existing_used = set(USED_FILE.read_text(encoding="utf-8").splitlines())
        with USED_FILE.open("a", encoding="utf-8") as f:
            for u in bad_links:
                if u not in existing_used:
                    f.write(u + "\n")

    # Ghi lai file chinh
    LINKS_FILE.write_text("\n".join(fresh_links) + ("\n" if fresh_links else ""), encoding="utf-8")
    print(f"Da dong bo lai file: {LINKS_FILE.name}")
    if fresh_links:
        FRESH_FILE.write_text("\n".join(fresh_links) + "\n", encoding="utf-8")
        print(f"File fresh link: {FRESH_FILE.name}")


if __name__ == "__main__":
    main()
