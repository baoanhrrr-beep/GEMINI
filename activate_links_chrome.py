"""
activate_links_chrome.py  v7 - Real Profile + CDP
Chrome 127+ uses App-Bound Encryption (v20) for cookies — cannot decrypt externally.
Solution: Kill Chrome → Start with REAL profile directory + --remote-debugging-port
          → Connect CDP → Navigate URL → Chrome decrypts its own cookies normally.

Flow per link:
  1. Kill ALL Chrome
  2. Launch Chrome with REAL user-data-dir and target profile + debug port
  3. Wait until port ready
  4. Connect CDP
  5. Navigate to activation URL  
  6. Detect result, click button
  7. Save screenshot
  8. Kill Chrome, move to next link
"""
import os, sys, time, subprocess, random, json, base64, re
import socket
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests as req_lib
import websocket

CHROME_EXE  = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA   = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
LINKS_FILE  = Path("gemini_activation_links.txt")
FRESH_FILE  = Path("gemini_links_fresh.txt")
USED_FILE   = Path("gemini_links_used.txt")
LOG_FILE    = Path("activate_results.txt")
SS_DIR      = Path("screenshots")
SS_DIR.mkdir(exist_ok=True)

ALL_PROFILES = [
    # 43 Validated Free Google Accounts (Excluded all Pro & Verification-required accounts)
    "Profile 1", "Profile 4", "Profile 6", "Profile 7", "Profile 10",
    "Profile 11", "Profile 12", "Profile 13", "Profile 16", "Profile 18",
    "Profile 21", "Profile 22", "Profile 24", "Profile 25", "Profile 30",
    "Profile 31", "Profile 32", "Profile 34", "Profile 35", "Profile 36",
    "Profile 37", "Profile 38", "Profile 39", "Profile 40", "Profile 41",
    "Profile 42", "Profile 47", "Profile 48", "Profile 50", "Profile 68",
    "Profile 69", "Profile 73", "Profile 74", "Profile 76", "Profile 78",
    "Profile 79", "Profile 81", "Profile 87", "Profile 88", "Profile 89",
    "Profile 90", "Profile 92", "Profile 93"
]


SIGNIN_KW  = [
    "sign in","email or phone","forgot email","choose an account",
    "use another account","create account","sign in with google",
    "enter your email","enter your password"
]
USED_KW    = [
    "subscription has been used","already been used","already redeemed",
    "da duoc su dung","đã được sử dụng","offer is not available",
]
INELIGIBLE_KW = [
    "already have a subscription", "already a google one member",
    "already a member", "current plan", "gói hiện tại", "đã là thành viên",
    "not eligible", "không đủ điều kiện", "ineligible"
]
EXPIRED_KW = [

    "need a new activation link","link is no longer valid",
    "link expired","activation link has expired","request a new link",
    "cần một đường liên kết kích hoạt mới",
]
FRESH_KW   = [
    "gemini advanced","google one","get started","redeem","activate",
    "try now","start your","claim","free trial","ai premium",
]

ACTIVATE_JS = """
(function(){
    var kw=['get started','redeem','activate','subscribe','try now',
            'claim','continue','start free','start trial'];
    var sel='button,[role="button"],a,.VfPpkd-LgbsSe,[jsname]';
    var btns=Array.from(document.querySelectorAll(sel));
    btns.sort(function(a,b){
        var at=(a.innerText||'').trim().length;
        var bt=(b.innerText||'').trim().length;
        return at-bt; // prefer shorter text = more likely to be a CTA button
    });
    for(var i=0;i<btns.length;i++){
        var t=(btns[i].innerText||btns[i].textContent||'').trim().toLowerCase();
        if(!t||t.length>80) continue;
        for(var j=0;j<kw.length;j++){
            if(t.indexOf(kw[j])!==-1){
                btns[i].click();
                return 'clicked:'+t.substring(0,50);
            }
        }
    }
    return 'not_found';
})()
"""

# ── helpers ────────────────────────────────────────────────────────────────────
def read_links(f):
    return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []

def save_links(f, links):
    f.write_text("\n".join(links)+"\n" if links else "", encoding="utf-8")

def append_used(url):
    ex = set(read_links(USED_FILE))
    if url not in ex:
        with USED_FILE.open("a", encoding="utf-8") as fh:
            fh.write(url+"\n")

def log(profile, url, status):
    line = f"[{status}] {profile} | ...{url[-70:]}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line+"\n")

def kill_chrome_wait():
    """Kill all Chrome processes (including helpers) and wait until zero remain."""
    # Kill main chrome and helpers
    for proc in ["chrome.exe", "chrome_elevation_service.exe", "chrome_crashpad_handler.exe"]:
        subprocess.run(["taskkill","/f","/im",proc], capture_output=True)
    time.sleep(2)

    # Confirm chrome.exe is gone
    for attempt in range(10):
        subprocess.run(["taskkill","/f","/im","chrome.exe"], capture_output=True)
        time.sleep(1)
        r = subprocess.run(
            ["tasklist","/fi","imagename eq chrome.exe","/fo","csv"],
            capture_output=True, text=True
        )
        if "chrome.exe" not in r.stdout.lower():
            break

    # Remove all lock files
    for name in ["SingletonLock","SingletonCookie","SingletonSocket"]:
        p = os.path.join(USER_DATA, name)
        try:
            if os.path.exists(p): os.remove(p)
        except: pass

    time.sleep(2)

def reset_profile_crash_state(profile):
    """Reset crash state in profile Preferences and clear previous session tabs so Chrome never restores crashed tabs."""
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

    # Delete Sessions/Tabs files to avoid restoring crashed tabs
    sess_dir = os.path.join(prof_dir, "Sessions")
    if os.path.isdir(sess_dir):
        for f in os.listdir(sess_dir):
            try:
                os.remove(os.path.join(sess_dir, f))
            except Exception:
                pass




def free_port():
    with socket.socket() as s:
        s.bind(("",0))
        return s.getsockname()[1]

def wait_port(port, timeout=25):
    dl = time.time()+timeout
    while time.time()<dl:
        try:
            s = socket.create_connection(("localhost",port), timeout=0.5)
            s.close()
            return True
        except:
            time.sleep(0.4)
    return False

def profile_exists(profile):
    p = os.path.join(USER_DATA, profile)
    return os.path.isdir(p)

# ── CDP client ─────────────────────────────────────────────────────────────────
class CDP:
    def __init__(self, port):
        self.port = port
        self._id = 0
        self.ws = None

    def connect(self, retries=10):
        for attempt in range(retries):
            try:
                r = req_lib.get(f"http://localhost:{self.port}/json/list", timeout=5)
                tabs = r.json()
                page_tabs = [t for t in tabs if t.get("type")=="page"]
                # Prefer about:blank or any real web page over crashed data/ tab
                tab = next((t for t in page_tabs if "blank" in t.get("url","")), None)
                if not tab and page_tabs:
                    tab = page_tabs[0]
                if tab:
                    ws_url = tab["webSocketDebuggerUrl"]
                    self.ws = websocket.create_connection(ws_url, timeout=30)
                    return self
            except Exception as e:
                if attempt < retries-1:

                    time.sleep(1.2)
                else:
                    raise RuntimeError(f"CDP connect failed: {e}")
        raise RuntimeError("CDP: no tabs found")

    def send(self, method, params=None):
        self._id += 1
        msg = json.dumps({"id": self._id, "method": method, "params": params or {}})
        self.ws.send(msg)
        deadline = time.time()+20
        while time.time()<deadline:
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
        self.send("Page.navigate", {"url": url})
        time.sleep(8)  # wait for JS render + any redirect

    def get_html(self):
        r = self.send("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True
        })
        return r.get("result",{}).get("value","")

    def eval_js(self, js):
        r = self.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
            "awaitPromise": False
        })
        return r.get("result",{}).get("value","")

    def screenshot(self):
        r = self.send("Page.captureScreenshot", {"format": "png", "quality": 80})
        return r.get("data","")

    def close(self):
        try: self.ws.close()
        except: pass


def classify(html):
    p = html.lower()
    for kw in SIGNIN_KW:
        if kw in p: return "signin"
    for kw in INELIGIBLE_KW:
        if kw in p: return "ineligible"
    for kw in USED_KW:
        if kw in p: return "used"
    for kw in EXPIRED_KW:
        if kw in p: return "expired"
    for kw in FRESH_KW:
        if kw in p: return "fresh"
    return "unknown"


def save_screenshot(data_b64, name):
    if not data_b64: return
    try:
        p = SS_DIR / f"{name}.png"
        p.write_bytes(base64.b64decode(data_b64))
        print(f"    [SS] {p.name}")
    except: pass

# ── main per-link processor ────────────────────────────────────────────────────
def process_one(profile, url, idx):
    cdp = None
    try:
        print(f"    [1] Kill Chrome...")
        kill_chrome_wait()
        reset_profile_crash_state(profile)

        port = free_port()

        args = [
            f"--remote-debugging-port={port}",
            f"--user-data-dir={USER_DATA}",
            f"--profile-directory={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            "--hide-crash-restore-bubble",
            "--remote-allow-origins=*",
            "--window-size=1366,768",
            url,
        ]
        chrome_cmd = [CHROME_EXE] + args
        print(f"    [2] Start Chrome real profile '{profile}' port {port} (direct Popen)...")
        subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        time.sleep(4)  # let Chrome init before polling port

        if not wait_port(port, 45):
            r2 = subprocess.run(["tasklist","/fi","imagename eq chrome.exe","/fo","csv"],
                                capture_output=True, text=True)
            running = "chrome.exe" in r2.stdout.lower()
            print(f"    [ERR] Chrome port {port} not ready (chrome_running={running})")
            return "error"

        print(f"    [3] Connect CDP...")
        time.sleep(1)
        cdp = CDP(port)
        cdp.connect()

        print(f"    [4] Navigate to URL...")
        cdp.navigate(url)
        time.sleep(3)

        html = cdp.get_html()
        status = classify(html)
        print(f"    [5] Page status: {status}")

        ss_data = cdp.screenshot()
        save_screenshot(ss_data, f"link{idx:03d}_before_{status}")

        if status == "signin":
            print(f"    [!] Sign-in page — {profile} session expired")
            return "signin_fail"

        if status == "fresh":
            print(f"    [6] Clicking activate button...")
            click_result = cdp.eval_js(ACTIVATE_JS)
            print(f"    [6] Click: {click_result}")
            time.sleep(6)

            html2 = cdp.get_html()
            status2 = classify(html2)
            ss2 = cdp.screenshot()
            save_screenshot(ss2, f"link{idx:03d}_after_{status2}")
            print(f"    [7] Post-click: {status2}")

            if status2 == "used":
                return "activated"
            if "clicked" in str(click_result).lower() and status2 not in ("signin","unknown"):
                return "fresh_clicked_" + status2
            return "fresh_no_button"

        return status

    except Exception as e:
        print(f"    [ERR] {e}")
        import traceback; traceback.print_exc()
        return "error"
    finally:
        if cdp: cdp.close()
        kill_chrome_wait()


def main():
    print("="*65)
    print("  Gemini Activator v7 - Real Profile CDP (v20 cookie safe)")
    print("="*65)
    kill_chrome_wait()

    # Filter profiles that actually exist
    valid_profiles = [p for p in ALL_PROFILES if profile_exists(p)]
    print(f"[*] Valid profiles on disk: {len(valid_profiles)}/{len(ALL_PROFILES)}")

    all_links = read_links(LINKS_FILE)
    if not all_links:
        print("[!] No links in gemini_activation_links.txt — waiting...")
        return

    print(f"[*] Links to process: {len(all_links)}")
    print()

    profiles = list(valid_profiles)
    random.shuffle(profiles)

    keep = []
    drop = []
    prof_idx = 0

    for idx, url in enumerate(all_links):
        # Rotate through profiles
        profile = profiles[prof_idx % len(profiles)]
        prof_idx += 1

        print(f"\n[{idx+1}/{len(all_links)}] Profile: {profile}")
        print(f"  ...{url[-65:]}")

        status = process_one(profile, url, idx+1)
        print(f"  FINAL: {status}")

        if status == "activated":
            log(profile, url, "ACTIVATED")
            append_used(url)
            drop.append(url)
            print("  *** ACTIVATED! ***")
        elif status in ("used","expired"):
            log(profile, url, status.upper())
            append_used(url)
            drop.append(url)
        elif status == "signin_fail":
            # Rotate to next profile for this link — mark kept
            log(profile, url, "SIGNIN_FAIL_KEPT")
            keep.append(url)
        elif status == "ineligible":
            log(profile, url, "INELIGIBLE_KEPT")
            keep.append(url)

        else:
            log(profile, url, f"{status.upper()}_KEPT")
            keep.append(url)

    # Save remaining links
    save_links(LINKS_FILE, keep)
    save_links(FRESH_FILE, keep)

    activated = len(drop)
    print("\n"+"="*65)
    print(f"  Round done. Activated={activated} | Kept={len(keep)}")
    print("="*65)
    return activated


if __name__ == "__main__":
    while True:
        try:
            activated = main()
            if not activated:
                print("\n[*] No activations this round. Waiting 30s for scanner to add new links...")
                time.sleep(30)
            else:
                print("\n[*] Restarting immediately for next round...")
                time.sleep(5)
        except Exception as e:
            print(f"[OUTER ERR] {e}")
            import traceback; traceback.print_exc()
            time.sleep(10)
