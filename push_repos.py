import os
import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_FILE = Path(r"c:\Users\k5a3h\Downloads\GEMINI jino Tool\repo_list.txt")

def run_cmd(cmd_list, capture=True):
    res = subprocess.run(cmd_list, capture_output=capture, text=True, encoding="utf-8", errors="replace")
    return res.returncode == 0, res.stdout.strip(), res.stderr.strip()

def main():
    print("=" * 70)
    print("      HE THONG DONG BO DA REPOSITORY GITHUB (MULTI-REPO PUSHER)")
    print("=" * 70)

    if not REPO_FILE.exists():
        print(f"[LOI] Khong tim thay file {REPO_FILE.name}")
        return

    # Doc danh sach repo
    lines = [l.strip() for l in REPO_FILE.read_text(encoding="utf-8").splitlines()]
    repos = [l for l in lines if l and not l.startswith("#")]

    if not repos:
        print("[LOI] Khong tim thay link repo nao trong repo_list.txt!")
        return

    print(f"\n[1/3] Khoi tao ma nguon va dong goi ban cap nhat...")
    run_cmd(["git", "init"])
    run_cmd(["git", "branch", "-M", "main"])
    run_cmd(["git", "add", "."])
    run_cmd(["git", "commit", "-m", "Deploy Jio Gemini Scanner Cloud"])

    print(f"\n[2/3] Bat dau day len {len(repos)} Repositories...")
    print("-" * 70)

    success_count = 0
    fail_count = 0

    for idx, repo_url in enumerate(repos, 1):
        # Format repo url (neu thieu .git thi bo sung)
        clean_url = repo_url.strip()
        if not clean_url.endswith(".git") and "github.com" in clean_url:
            clean_url += ".git"

        print(f"\n[{idx}/{len(repos)}] Dang day len: {clean_url}")
        run_cmd(["git", "remote", "remove", "cloud_target"])
        ok_add, _, _ = run_cmd(["git", "remote", "add", "cloud_target", clean_url])
        
        ok_push, out, err = run_cmd(["git", "push", "-u", "cloud_target", "main", "--force"])

        if ok_push:
            print(f"   => [THANH CONG]")
            success_count += 1
        else:
            print(f"   => [THAT BAI]")
            if err:
                # In ra loi ngan gon
                for line in err.splitlines()[-3:]:
                    print(f"      {line}")
            fail_count += 1

    run_cmd(["git", "remote", "remove", "cloud_target"])

    print("\n" + "=" * 70)
    print("TONG KET:")
    print(f"  + Thanh cong : {success_count}/{len(repos)} repos")
    print(f"  + That bai   : {fail_count}/{len(repos)} repos")
    print("=" * 70)
    print("\nCac buoc tiep theo tren web GitHub:")
    print("1. Mo tung Repo tren GitHub")
    print("2. Vao tab 'Actions'")
    print("3. Chon 'Jio Gemini Scanner Cloud 24/7' -> Bam 'Run workflow'")
    print("Tat ca cac may chu Cloud se chay dong thoi!")

if __name__ == "__main__":
    main()
