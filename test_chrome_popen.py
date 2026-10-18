"""Quick test: start Chrome with real profile from Python subprocess.Popen and check debug port"""
import subprocess, time, socket, os, requests

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA  = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
PORT = 9811

# Kill first
print("Killing Chrome...")
for proc in ["chrome.exe","chrome_elevation_service.exe","chrome_crashpad_handler.exe"]:
    subprocess.run(["taskkill","/f","/im",proc], capture_output=True)
time.sleep(4)

# Remove lock files
for name in ["SingletonLock","SingletonCookie","SingletonSocket"]:
    p = os.path.join(USER_DATA, name)
    try:
        if os.path.exists(p): os.remove(p); print(f"  Removed {name}")
    except: pass
time.sleep(2)

# Check Chrome is gone
r = subprocess.run(["tasklist","/fi","imagename eq chrome.exe","/fo","csv"],
                   capture_output=True, text=True)
print("Chrome processes before start:", "NONE" if "chrome.exe" not in r.stdout.lower() else "STILL RUNNING")

# Start Chrome via Python subprocess.Popen (same as our script)
print(f"\nStarting Chrome with --remote-debugging-port={PORT}...")
cmd = [
    CHROME_EXE,
    f"--remote-debugging-port={PORT}",
    f"--user-data-dir={USER_DATA}",
    "--profile-directory=Profile 11",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-session-crashed-bubble",
    "--remote-allow-origins=*",
    "--window-size=1366,768",
    "about:blank",
]
proc = subprocess.Popen(
    cmd,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
)
print(f"Popen returned PID: {proc.pid}")

# Poll every second for 30s
for i in range(30):
    time.sleep(1)
    # Check if process still alive
    alive = proc.poll() is None
    # Try TCP port
    port_open = False
    try:
        s = socket.create_connection(("localhost", PORT), timeout=0.5)
        s.close()
        port_open = True
    except:
        pass
    print(f"  t={i+1}s: chrome_alive={alive}, port_open={port_open}")
    if port_open:
        print("\nPort OPEN! Testing CDP...")
        try:
            resp = requests.get(f"http://localhost:{PORT}/json/list", timeout=5)
            print(f"CDP HTTP {resp.status_code}")
            for tab in resp.json()[:3]:
                print(f"  Tab: {tab.get('type')} | {tab.get('url')}")
        except Exception as e:
            print(f"CDP ERR: {e}")
        break
    if not alive:
        print(f"  Chrome EXITED with code: {proc.returncode}")
        break

print("\nDone. Killing Chrome.")
subprocess.run(["taskkill","/f","/im","chrome.exe"], capture_output=True)
