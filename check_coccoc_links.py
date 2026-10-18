"""
check_coccoc_links.py
Tự động điều khiển trình duyệt Cốc Cốc đang mở để kiểm tra toàn bộ link trong gemini_activation_links.txt.
"""

import os
import sys
import time
import ctypes
import pyperclip
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import uiautomation as auto
import mss
from PIL import Image
import numpy as np
import easyocr

LINKS_FILE = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_activation_links.txt")
USED_FILE  = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_links_used.txt")
DOWNLOADS_DIR = Path(r"c:\Users\k5a3h\Downloads")
FRESH_DOWNLOAD_FILE = DOWNLOADS_DIR / "gemini_fresh_links.txt"
FRESH_LOCAL_FILE    = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\gemini_links_fresh.txt")

user32 = ctypes.windll.user32
h_default = user32.OpenDesktopW("default", 0, False, 0x01FF)

def ensure_desktop():
    if h_default:
        user32.SetThreadDesktop(h_default)

def find_coccoc_window():
    ensure_desktop()
    found = []
    def enum_proc(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            t = buff.value.lower()
            if "cốc cốc" in t or "coccoc" in t:
                found.append((hwnd, buff.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumDesktopWindows(h_default, WNDENUMPROC(enum_proc), 0)
    return found[0] if found else (None, None)

def ensure_window_active(hwnd):
    ensure_desktop()
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9) # SW_RESTORE
        time.sleep(0.3)
    user32.ShowWindow(hwnd, 3) # SW_SHOWMAXIMIZED
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)

def append_to_file(path: Path, url: str):
    ex = set()
    if path.exists():
        ex = set(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    if url not in ex:
        with path.open("a", encoding="utf-8") as f:
            f.write(url.strip() + "\n")

def capture_crop(hwnd):
    ensure_window_active(hwnd)
    with mss.MSS() as sct:
        sct.shot(output="current_check.png")
    img = Image.open("current_check.png")
    # Vùng trung tâm màn hình 1920x1080 (X: 450 -> 1470, Y: 220 -> 820)
    return img.crop((450, 220, 1470, 820))

def main():
    if not LINKS_FILE.exists():
        print(f"[ERR] Không tìm thấy file {LINKS_FILE}")
        return

    links = [l.strip() for l in LINKS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
    if not links:
        print("[INFO] Không có link nào trong file gemini_activation_links.txt")
        return

    print("=" * 70)
    print("  GEMINI ACTIVATION LINKS CHECKER - VIA CỐC CỐC")
    print(f"  Tổng số link cần kiểm tra: {len(links)}")
    print("=" * 70)

    hwnd, title = find_coccoc_window()
    if not hwnd:
        print("[ERR] Không tìm thấy cửa sổ Cốc Cốc đang mở!")
        return
    print(f"[INFO] Đã kết nối cửa sổ Cốc Cốc: HWND={hwnd} | '{title}'")

    print("[INFO] Đang khởi tạo mô hình nhận diện EasyOCR...")
    reader = easyocr.Reader(["vi", "en"], gpu=False)
    print("[INFO] EasyOCR đã sẵn sàng!\n")

    ensure_window_active(hwnd)

    fresh_links = []
    expired_links = []
    used_links = []
    unknown_links = []

    for idx, url in enumerate(links, 1):
        token_short = url.split("?")[0].rstrip("/").split("/")[-1]
        token_short = token_short[-35:] if len(token_short) > 35 else token_short
        print(f"\n[{idx:02d}/{len(links)}] Đang kiểm tra: ...{token_short}")

        ensure_window_active(hwnd)

        # Điều hướng link bằng Ctrl+L -> Ctrl+V -> Enter
        pyperclip.copy(url)
        time.sleep(0.15)
        auto.SendKeys("{Ctrl}l")
        time.sleep(0.25)
        auto.SendKeys("{Ctrl}v")
        time.sleep(0.25)
        auto.SendKeys("{Enter}")

        # Chờ trang tải (5.5s)
        time.sleep(5.5)

        # Chụp vùng trung tâm
        try:
            crop = capture_crop(hwnd)
            crop_np = np.array(crop)
            texts = reader.readtext(crop_np, detail=0)
            combined_text = " ".join(texts).lower()
        except Exception as e:
            print(f"  [Lỗi chụp/OCR]: {e}")
            texts = []
            combined_text = ""

        # Nếu còn trống do mạng load chậm, chờ thêm 2.5s và chụp lại
        if not combined_text.strip():
            time.sleep(2.5)
            try:
                crop = capture_crop(hwnd)
                crop_np = np.array(crop)
                texts = reader.readtext(crop_np, detail=0)
                combined_text = " ".join(texts).lower()
            except Exception:
                pass

        status = "UNKNOWN"
        reason = ""

        # 1. EXPIRED
        if any(k in combined_text for k in [
            "cần một đường liên kết", "liên kết kích hoạt mới",
            "đường liên kết kích hoạt mới", "khám phá google one",
            "new activation link", "link is no longer valid",
            "link expired", "đã hết hạn", "hết hạn"
        ]):
            status = "EXPIRED"
            reason = "Link hết hạn (Cần liên kết kích hoạt mới)"
            expired_links.append(url)
            append_to_file(USED_FILE, url)

        # 2. ALREADY USED
        elif any(k in combined_text for k in [
            "đã được sử dụng", "gói thuê bao này đã được sử dụng",
            "already been used", "already redeemed", "không có sẵn",
            "offer is not available", "ưu đãi không có sẵn"
        ]):
            status = "ALREADY_USED"
            reason = "Link đã được sử dụng"
            used_links.append(url)
            append_to_file(USED_FILE, url)

        # 3. FRESH (CÒN DÙNG ĐƯỢC)
        elif any(k in combined_text for k in [
            "bắt đầu", "kích hoạt", "kích hoạt gói", "get started",
            "18 tháng", "gemini advanced", "dùng thử", "tiếp tục",
            "đổi ưu đãi", "redeem", "claim", "ai premium"
        ]):
            status = "FRESH"
            reason = "Link SỐNG - Còn nguyên giá trị kích hoạt!"
            fresh_links.append(url)
            append_to_file(FRESH_DOWNLOAD_FILE, url)
            append_to_file(FRESH_LOCAL_FILE, url)

        # 4. Yêu cầu login
        elif any(k in combined_text for k in ["đăng nhập", "sign in", "chọn tài khoản", "choose an account"]):
            status = "NOT_LOGGED_IN"
            reason = "Cốc Cốc chưa đăng nhập tài khoản Google"
            unknown_links.append(url)

        else:
            status = "UNKNOWN"
            reason = f"Chưa rõ: '{combined_text[:50]}...'"
            unknown_links.append(url)

        print(f"  -> [{status}] {reason}")
        if texts:
            print(f"     Nội dung trang: {texts[:4]}")

        # Tự động cập nhật file gốc sau mỗi link để an toàn
        bad_set = set(expired_links + used_links)
        cur_remaining = [u for u in links if u not in bad_set]
        LINKS_FILE.write_text("\n".join(cur_remaining) + ("\n" if cur_remaining else ""), encoding="utf-8")

    # Tổng kết
    print("\n" + "=" * 70)
    print("  KẾT QUẢ KIỂM TRA TOÀN BỘ LINK")
    print("=" * 70)
    print(f"  - Tổng số link đã check : {len(links)}")
    print(f"  - Link SỐNG (FRESH)      : {len(fresh_links)}")
    print(f"  - Link HẾT HẠN (EXPIRED) : {len(expired_links)}")
    print(f"  - Link ĐÃ DÙNG (USED)    : {len(used_links)}")
    print(f"  - Link nghi vấn/chưa rõ  : {len(unknown_links)}")
    print("=" * 70)
    bad_count = len(expired_links) + len(used_links)
    print(f"  -> Đã xóa {bad_count} link lỗi khỏi file gốc: {LINKS_FILE.name}")
    print(f"  -> File gốc hiện còn lại : {len(cur_remaining)} link")
    if fresh_links:
        print(f"  -> Đã lưu các link SỐNG vào Downloads:")
        print(f"     {FRESH_DOWNLOAD_FILE.resolve()}")
        print("\n  DANH SÁCH LINK SỐNG (DÙNG ĐƯỢC):")
        for i, u in enumerate(fresh_links, 1):
            print(f"    [{i}] {u}")
    else:
        print("  -> Không có link nào còn dùng được (tất cả đều đã hết hạn hoặc đã sử dụng).")

if __name__ == "__main__":
    main()
