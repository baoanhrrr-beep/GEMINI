import os, sys, time, json, socket, subprocess
from pathlib import Path
import requests as req_lib
import websocket

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.isfile(CHROME_EXE):
    CHROME_EXE = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
USER_DATA_LINK = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\UserDataLink")
TARGET_PROFILE = "Profile 102"

FOLDER = Path(r"C:\Users\k5a3h\Downloads\Gemini_Live_Links")
USED_FILE = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_links_used.txt")

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

    for base in [USER_DATA, USER_DATA_LINK]:
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

    def eval_page(self):
        r = self.send("Runtime.evaluate", {
            "expression": "JSON.stringify({url: location.href, text: document.body ? document.body.innerText : ''})",
            "returnByValue": True,
        })
        try:
            val = r.get("result", {}).get("value", "{}")
            return json.loads(val)
        except Exception:
            return {"url": "", "text": ""}

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

def main():
    files = sorted([f for f in FOLDER.glob("*.txt")], key=lambda x: x.name)
    if not files:
        print("Khong tim thay file txt nao trong", FOLDER)
        return

    items = []
    for f in files:
        u = f.read_text(encoding="utf-8", errors="ignore").strip()
        if u.startswith("http"):
            items.append((f, u))

    print("=" * 70)
    print(f"KIEM TRA CHINH XAC {len(items)} FILE TRONG {FOLDER}")
    print(f"PROFILE: {TARGET_PROFILE} (namanhanh76@gmail.com)")
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

    print(f"Khoi dong Chrome port {port}...")
    subprocess.Popen(
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

    alive_files = []
    dead_files = []

    try:
        for idx, (filepath, url) in enumerate(items, 1):
            token_display = url[-45:]
            print(f"\n[{idx:02d}/{len(items)}] {filepath.name} ...{token_display}")
            cdp.navigate(url)

            # Polling DOM render len den 12 giay
            status = "UNKNOWN"
            is_bad = True
            matched_text = ""

            for sec in range(1, 13):
                time.sleep(1)
                page = cdp.eval_page()
                cur_url = page.get("url", "").lower()
                text = page.get("text", "").lower()

                # 1. Kiem tra EXPIRED (uu tien so 1)
                if any(k in text for k in [
                    "need a new activation link",
                    "ask your provider to send a new link",
                    "cần một đường liên kết kích hoạt mới",
                    "link is no longer valid",
                    "link expired",
                    "liên kết hết hạn",
                    "đường liên kết đã hết hạn",
                    "explore google one",
                ]):
                    status = "EXPIRED (Can link moi)"
                    is_bad = True
                    matched_text = "You need a new activation link"
                    break

                # 2. Kiem tra ALREADY_USED
                if any(k in text for k in [
                    "subscription has been used",
                    "already been used",
                    "already redeemed",
                    "đã được sử dụng",
                    "offer is not available",
                    "ưu đãi không có sẵn",
                ]):
                    status = "ALREADY_USED"
                    is_bad = True
                    matched_text = "Already used"
                    break

                # 3. Kiem tra FRESH_READY (Phai co nut kich hoat that)
                if any(k in text for k in [
                    "kích hoạt gói", "kích hoạt", "nhận ưu đãi", "bắt đầu", "dùng thử",
                    "get started", "redeem", "activate", "claim", "start free", "try now",
                    "gemini advanced", "ai premium", "18 tháng"
                ]) and not any(k in text for k in ["need a new activation link", "explore google one"]):
                    status = "FRESH_READY"
                    is_bad = False
                    matched_text = "Found activate CTA button"
                    break

                # 4. Kiem tra Dang nhap
                if "accounts.google.com" in cur_url and ("signin" in cur_url or "identifier" in cur_url):
                    status = "NOT_LOGGED_IN"
                    is_bad = True
                    matched_text = "Redirected to Google Sign-in"
                    # Doi them vai giay xem co tu login khong

            if is_bad:
                print(f"   -> [XOA FILE] {status} | {matched_text}")
                dead_files.append((filepath, url, status))
            else:
                print(f"   -> [GIU FILE] {status} | {matched_text}")
                alive_files.append((filepath, url, status))

    finally:
        cdp.close()
        kill_chrome_wait()

    print("\n" + "=" * 70)
    print("HOAN TAT KIEM TRA:")
    print(f"  + Link SONG  : {len(alive_files)}")
    print(f"  + Link LOI   : {len(dead_files)}")
    print("=" * 70)

    # Xoa ngay file loi va luu used
    if dead_files:
        existing_used = set()
        if USED_FILE.exists():
            existing_used = set(USED_FILE.read_text(encoding="utf-8").splitlines())
        with USED_FILE.open("a", encoding="utf-8") as uf:
            for fp, u, st in dead_files:
                try:
                    fp.unlink(missing_ok=True)
                    print(f"  Da xoa: {fp.name} ({st})")
                except Exception as e:
                    print(f"  Loi xoa {fp.name}: {e}")
                if u not in existing_used:
                    uf.write(u + "\n")
                    existing_used.add(u)

if __name__ == "__main__":
    main()
