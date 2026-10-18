"""
extension_bridge_server.py
Backend bridge server for Chrome Extension checking Google One Gemini links.
Specifically checks all links in C:\\Users\\k5a3h\\Downloads\\Gemini_Live_Links.
- Serves links one by one to Chrome Extension via /next_link
- Deletes expired/used files from Gemini_Live_Links immediately upon report
- Keeps live files safe in Gemini_Live_Links
- Terminates or reports summary once all links have been tested
"""

import os
import sys
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LIVE_FOLDER = Path(r"C:\Users\k5a3h\Downloads\Gemini_Live_Links")
LINKS_FILE = Path("gemini_activation_links.txt")
USED_FILE  = Path("gemini_links_used.txt")
LOG_FILE   = Path("extension_results.log")

def read_folder_queue():
    if not LIVE_FOLDER.exists():
        return []
    items = []
    for f in sorted(LIVE_FOLDER.glob("*.txt")):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore").strip()
            if content.startswith("http"):
                items.append({"file": f, "url": content, "name": f.name})
        except Exception:
            pass
    return items

def extract_token(u):
    return u.split("?")[0].rstrip("/").split("/")[-1].strip()

def append_used(url):
    ex = set()
    if USED_FILE.exists():
        ex = set(USED_FILE.read_text(encoding="utf-8", errors="ignore").splitlines())
    if url not in ex:
        with USED_FILE.open("a", encoding="utf-8") as fh:
            fh.write(url + "\n")

def remove_from_txt(url):
    if not LINKS_FILE.exists():
        return
    token = extract_token(url)
    lines = LINKS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    remaining = [l for l in lines if extract_token(l) != token and l.strip() != url.strip()]
    LINKS_FILE.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")

def log(msg):
    print(msg)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")

# Global check state
queue = []
checked_count = 0
deleted_count = 0
live_count = 0
unknown_count = 0
current_item = None

class BridgeHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        global queue, current_item
        if self.path == "/next_link":
            if queue:
                current_item = queue.pop(0)
                self._set_headers(200)
                resp = {
                    "url": current_item["url"],
                    "filename": current_item["name"],
                    "remaining": len(queue)
                }
                log(f"\n[NEXT] Testing file: {current_item['name']} | Còn lại trong hàng đợi: {len(queue)}")
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            else:
                current_item = None
                self._set_headers(200)
                log("\n" + "=" * 60)
                log(">>> HOÀN TẤT KIỂM TRA TẤT CẢ CÁC FILE TRONG Gemini_Live_Links!")
                log(f"    - Tổng đã check : {checked_count}")
                log(f"    - Link SỐNG     : {live_count}")
                log(f"    - Link ĐÃ XÓA   : {deleted_count}")
                log(f"    - Nghi vấn      : {unknown_count}")
                log("=" * 60)
                self.wfile.write(json.dumps({"url": None, "remaining": 0}).encode("utf-8"))
        else:
            self._set_headers(404)

    def do_POST(self):
        global checked_count, deleted_count, live_count, unknown_count, current_item
        if self.path == "/report_result":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            url = data.get("url", "")
            status = data.get("status", "")
            details = data.get("details", "")

            checked_count += 1
            fname = current_item["name"] if current_item else "unknown_file"

            token = extract_token(url)
            log(f"[{status.upper()}] File: {fname} | Details: {details}")

            if status in ["expired", "used"]:
                deleted_count += 1
                # Delete corresponding file in Gemini_Live_Links
                deleted_file = False
                if LIVE_FOLDER.exists():
                    for lf in LIVE_FOLDER.glob("*.txt"):
                        try:
                            c = lf.read_text(encoding="utf-8", errors="ignore")
                            if token in c or (current_item and lf.name == current_item["name"]):
                                lf.unlink(missing_ok=True)
                                log(f"  -> [ĐÃ XÓA FILE DIE] {lf.name}")
                                deleted_file = True
                        except Exception as e:
                            log(f"  -> Lỗi khi xóa file {lf.name}: {e}")
                if not deleted_file and current_item and current_item["file"].exists():
                    current_item["file"].unlink(missing_ok=True)
                    log(f"  -> [ĐÃ XÓA FILE DIE] {current_item['name']}")

                remove_from_txt(url)
                append_used(url)

            elif status in ["live", "account_already_pro"]:
                live_count += 1
                log(f"  -> [GIỮ LẠI - LINK SỐNG!] {fname} còn nguyên vẹn trong {LIVE_FOLDER.name}")

            elif status == "not_logged_in":
                unknown_count += 1
                log(f"  -> [CHƯA ĐĂNG NHẬP] Google yêu cầu login trong Profile 102! Link được giữ nguyên.")

            else:
                unknown_count += 1
                log(f"  -> [CHƯA RÕ] Trạng thái {status}. Giữ nguyên {fname}.")

            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        else:
            self._set_headers(404)

    def log_message(self, format, *args):
        pass

def main():
    global queue
    port = 8765
    server = HTTPServer(("127.0.0.1", port), BridgeHandler)
    
    queue = read_folder_queue()
    print("=" * 65)
    print("  GEMINI EXTENSION BRIDGE SERVER")
    print(f"  Thư mục kiểm tra : {LIVE_FOLDER.resolve()}")
    print(f"  Số file cần check: {len(queue)} files")
    for item in queue:
        print(f"    + {item['name']}: {item['url'][:65]}...")
    print("=" * 65)
    print(f"  Bridge server listening on http://127.0.0.1:{port}...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")

if __name__ == "__main__":
    main()
