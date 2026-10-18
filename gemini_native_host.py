"""
gemini_native_host.py
Native Messaging Host cho Chrome Extension.
Nhan lenh tu extension popup -> start/stop bridge server + jio scanner.
"""
import sys
import json
import struct
import subprocess
import os
import signal
from pathlib import Path

TOOL_DIR = Path(__file__).parent
BRIDGE_SCRIPT = TOOL_DIR / "extension_bridge_server.py"
SCANNER_SCRIPT = TOOL_DIR / "jio_gemini_share.py"
PID_FILE = TOOL_DIR / "gemini_pids.txt"

bridge_proc = None
scanner_proc = None

def read_pids():
    if PID_FILE.exists():
        lines = PID_FILE.read_text().strip().splitlines()
        pids = {}
        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                pids[k.strip()] = int(v.strip())
        return pids
    return {}

def save_pids(bridge_pid=None, scanner_pid=None):
    lines = []
    if bridge_pid: lines.append(f"bridge={bridge_pid}")
    if scanner_pid: lines.append(f"scanner={scanner_pid}")
    PID_FILE.write_text("\n".join(lines))

def is_running(pid):
    try:
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
        if handle:
            import ctypes.wintypes
            exit_code = ctypes.wintypes.DWORD()
            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
        return False
    except Exception:
        return False

def get_status():
    pids = read_pids()
    bridge_running = is_running(pids.get("bridge", 0)) if pids.get("bridge") else False
    scanner_running = is_running(pids.get("scanner", 0)) if pids.get("scanner") else False
    return {
        "bridge": bridge_running,
        "scanner": scanner_running,
        "bridge_pid": pids.get("bridge"),
        "scanner_pid": pids.get("scanner"),
    }

def start_tools():
    pids = read_pids()
    # Kill cu neu con chay
    for key in ["bridge", "scanner"]:
        pid = pids.get(key, 0)
        if pid and is_running(pid):
            try:
                subprocess.call(["taskkill", "/f", "/pid", str(pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    python = sys.executable
    # Start bridge server
    bridge = subprocess.Popen(
        [python, str(BRIDGE_SCRIPT)],
        cwd=str(TOOL_DIR),
        stdout=open(TOOL_DIR / "bridge_server.log", "a"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    # Start scanner
    scanner = subprocess.Popen(
        [python, "-u", str(SCANNER_SCRIPT)],
        cwd=str(TOOL_DIR),
        stdout=open(TOOL_DIR / "scanner.log", "a"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    save_pids(bridge.pid, scanner.pid)
    return {"ok": True, "bridge_pid": bridge.pid, "scanner_pid": scanner.pid}

def stop_tools():
    pids = read_pids()
    killed = []
    for key in ["bridge", "scanner"]:
        pid = pids.get(key, 0)
        if pid:
            try:
                subprocess.call(["taskkill", "/f", "/pid", str(pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                killed.append(key)
            except Exception:
                pass
    if PID_FILE.exists():
        PID_FILE.unlink()
    return {"ok": True, "killed": killed}

def send_message(msg):
    data = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()

def read_message():
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len or len(raw_len) < 4:
        return None
    msg_len = struct.unpack("I", raw_len)[0]
    raw_msg = sys.stdin.buffer.read(msg_len)
    return json.loads(raw_msg.decode("utf-8"))

def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        action = msg.get("action", "")
        if action == "start":
            send_message(start_tools())
        elif action == "stop":
            send_message(stop_tools())
        elif action == "status":
            send_message(get_status())
        else:
            send_message({"error": "Unknown action: " + action})

if __name__ == "__main__":
    main()
