"""
discord_gemini_bot.py
Bot Discord check link Gemini 24/7.

Lenh:
  !get       - Lay 1 link fresh
  !stats     - Xem so luong link con lai
  !check     - Quet ngay toan bo file (xoa link het han)
  !help      - Xem danh sach lenh
"""

import asyncio
import time
import sys
import requests as req_lib
from pathlib import Path
from datetime import datetime

import discord
from discord.ext import commands, tasks

sys.path.insert(0, str(Path(__file__).parent))
from discord_bot_config import DISCORD_TOKEN, ALLOWED_CHANNEL_ID, ALLOWED_USER_ID

# ── Paths ─────────────────────────────────────────────────────────────────────
TOOL_DIR    = Path(__file__).parent
LINKS_FILE  = TOOL_DIR / "gemini_activation_links.txt"
USED_FILE   = TOOL_DIR / "gemini_links_used.txt"
FRESH_FILE  = TOOL_DIR / "gemini_links_fresh.txt"
LOG_FILE    = TOOL_DIR / "discord_bot.log"

# ── HTTP Headers ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EXPIRED_KW = [
    "need a new activation link",
    "cần một đường liên kết kích hoạt mới",
    "ask your provider to send a new link",
    "link is no longer valid",
    "link expired",
    "activation link has expired",
    "liên kết không còn hợp lệ",
    "đường liên kết đã hết hạn",
    "new activation link",
    "request a new link",
    "explore google one",
]
USED_KW = [
    "subscription has been used",
    "already been used",
    "already redeemed",
    "đã được sử dụng",
    "gói thuê bao này đã được sử dụng",
    "offer is not available",
    "ưu đãi không có sẵn",
    "this subscription link has",
    "link has already been used",
]
FRESH_KW = [
    "kích hoạt gói", "kích hoạt", "nhận ưu đãi", "bắt đầu", "dùng thử",
    "get started", "redeem", "activate", "claim", "start free", "try now",
    "gemini advanced", "ai premium", "18 tháng"
]

# ── File helpers ──────────────────────────────────────────────────────────────
def read_links(path: Path) -> list[str]:
    if not path.exists(): return []
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip().startswith("http")]

def write_links(path: Path, links: list[str]):
    path.write_text("\n".join(links) + ("\n" if links else ""), encoding="utf-8")

def append_used(url: str):
    existing = set(read_links(USED_FILE))
    if url not in existing:
        with USED_FILE.open("a", encoding="utf-8") as f:
            f.write(url + "\n")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── Link checker ──────────────────────────────────────────────────────────────
def check_link_status(url: str, timeout: int = 15) -> str:
    """
    Returns: 'fresh' | 'expired' | 'used' | 'unknown'
    Uses direct one.google.com/activate/plan/subscription/new/<token> check:
    - HTTP 404 / 410 -> dead/expired ('You need a new activation link')
    - HTTP 200 / 302 -> live
    """
    try:
        token = url.strip().rstrip("/").split("/")[-1]
        direct_url = f"https://one.google.com/activate/plan/subscription/new/{token}"
        r = req_lib.get(direct_url, headers=HEADERS, timeout=timeout, allow_redirects=False)
        if r.status_code in (404, 410):
            return "expired"
        
        # Follow or inspect content
        r_full = req_lib.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        body = r_full.text.lower()
        for kw in USED_KW:
            if kw.lower() in body: return "used"
        for kw in EXPIRED_KW:
            if kw.lower() in body: return "expired"
        if r_full.status_code in (404, 410): return "expired"
        return "fresh"
    except Exception:
        return "unknown"

# ── Bot state ─────────────────────────────────────────────────────────────────
fresh_pool: list[str] = []   # verified fresh links ready to serve
is_scanning = False

def reload_fresh_pool():
    """Load verified fresh links from fresh file."""
    global fresh_pool
    fresh_pool = read_links(FRESH_FILE)

# ── Permission check ──────────────────────────────────────────────────────────
def is_allowed(ctx) -> bool:
    # DM truc tiep -> luon cho phep
    if ctx.guild is None:
        if ALLOWED_USER_ID and str(ctx.author.id) != ALLOWED_USER_ID:
            return False
        return True
    # Trong server -> check channel va user
    if ALLOWED_CHANNEL_ID and str(ctx.channel.id) != ALLOWED_CHANNEL_ID:
        return False
    if ALLOWED_USER_ID and str(ctx.author.id) != ALLOWED_USER_ID:
        return False
    return True

# ── Discord Bot ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ── Background task: quet links moi 30 phut ──────────────────────────────────
@tasks.loop(minutes=30)
async def background_scan():
    global is_scanning, fresh_pool
    if is_scanning:
        return
    is_scanning = True
    log("[SCAN] Bat dau quet link tu dong...")

    links = read_links(LINKS_FILE)
    if not links:
        log("[SCAN] Khong co link nao de quet")
        is_scanning = False
        return

    fresh, removed = [], []
    for url in links:
        status = await asyncio.get_event_loop().run_in_executor(
            None, check_link_status, url
        )
        if status == "fresh":
            fresh.append(url)
        elif status in ("expired", "used"):
            removed.append(url)
            append_used(url)
        await asyncio.sleep(1)  # tranh spam request

    # Cap nhat files
    kept = [u for u in links if u not in removed]
    write_links(LINKS_FILE, kept)
    write_links(FRESH_FILE, fresh)
    fresh_pool = fresh[:]

    log(f"[SCAN] Xong: {len(fresh)} fresh | {len(removed)} da xoa")
    is_scanning = False

@background_scan.before_loop
async def before_scan():
    await bot.wait_until_ready()
    reload_fresh_pool()   # load pool ngay khi khoi dong

# ── Commands ──────────────────────────────────────────────────────────────────
@bot.command(name="get", aliases=["link", "lay"])
async def cmd_get(ctx):
    """Lay 1 link va xoa link do khoi file ngay lap tuc"""
    if not is_allowed(ctx): return

    reload_fresh_pool()
    all_links = read_links(LINKS_FILE)

    if not fresh_pool and not all_links:
        embed_empty = discord.Embed(
            title="📭 Kho link đang trống",
            description="Hãy gửi file `.txt` chứa danh sách link vào đây để bot lưu vào kho!",
            color=0xef4444
        )
        await ctx.send(embed=embed_empty)
        return

    # Uu tien lay link da verify fresh, neu chua co thi lay link trong kho
    if fresh_pool:
        url = fresh_pool.pop(0)
    else:
        url = all_links[0]

    # XOA NGAY LAP TUC KHOI CA 2 FILE (Khong bao gio xuat hien lai)
    rem_links = [l for l in read_links(LINKS_FILE) if l.strip() != url.strip()]
    rem_fresh = [l for l in read_links(FRESH_FILE) if l.strip() != url.strip()]
    write_links(LINKS_FILE, rem_links)
    write_links(FRESH_FILE, rem_fresh)
    append_used(url)

    embed = discord.Embed(
        title="🎁 Link Kích Hoạt Gemini AI Pro",
        description="Mỗi lần nhả link, bot sẽ **tự động xóa 1 link khỏi file** để không bị trùng.",
        color=0x22c55e,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🔗 Link kích hoạt", value=f"```{url}```", inline=False)
    embed.add_field(name="📦 Còn lại trong kho", value=f"`{len(rem_links)}` link", inline=True)
    embed.add_field(name="🟢 Đã verify fresh", value=f"`{len(rem_fresh)}` link", inline=True)
    embed.add_field(name="💡 Sử dụng", value="Mở link trên Chrome đã đăng nhập Google -> Bấm **Kích hoạt gói**", inline=False)
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name} • Đã xóa 1 link khỏi file")

    await ctx.send(embed=embed)
    log(f"[GET] Da nha link va XOA khoi file cho {ctx.author} | Con lai: {len(rem_links)}")

@bot.command(name="stats", aliases=["stat", "count", "sl"])
async def cmd_stats(ctx):
    """Xem so luong link"""
    if not is_allowed(ctx): return

    total  = len(read_links(LINKS_FILE))
    fresh  = len(read_links(FRESH_FILE))
    used   = len(read_links(USED_FILE))

    embed = discord.Embed(title="📊 Thống kê Link Gemini", color=0x3b82f6, timestamp=datetime.utcnow())
    embed.add_field(name="🟢 Fresh (dùng được)",   value=f"`{fresh}`",  inline=True)
    embed.add_field(name="📦 Tổng trong kho",        value=f"`{total}`",  inline=True)
    embed.add_field(name="🔴 Đã dùng/hết hạn",      value=f"`{used}`",   inline=True)
    embed.add_field(name="🔄 Scan tiếp theo",
                    value=f"`{30 - (int(time.time()) % 1800) // 60}` phút nữa",
                    inline=False)
    await ctx.send(embed=embed)

@bot.command(name="check", aliases=["scan", "quet"])
async def cmd_check(ctx):
    """Quet ngay toan bo link (xoa link het han)"""
    if not is_allowed(ctx): return
    if is_scanning:
        await ctx.send("⏳ Đang có quét đang chạy, chờ xíu...")
        return
    await ctx.send("🔍 Bắt đầu quét toàn bộ links...")
    await do_quick_scan(ctx)

async def do_quick_scan(ctx):
    global is_scanning, fresh_pool
    is_scanning = True
    links = read_links(LINKS_FILE)
    if not links:
        await ctx.send("📭 Không có link nào trong file.")
        is_scanning = False
        return

    msg = await ctx.send(f"⏳ Đang quét `{len(links)}` links...")
    fresh, removed = [], []

    for i, url in enumerate(links):
        status = await asyncio.get_event_loop().run_in_executor(
            None, check_link_status, url
        )
        if status == "fresh":
            fresh.append(url)
        elif status in ("expired", "used"):
            removed.append(url)
            append_used(url)
        if (i + 1) % 5 == 0:
            await msg.edit(content=f"⏳ Đang quét: `{i+1}/{len(links)}` | ✅ Fresh: `{len(fresh)}` | ❌ Xóa: `{len(removed)}`")
        await asyncio.sleep(0.8)

    kept = [u for u in links if u not in removed]
    write_links(LINKS_FILE, kept)
    write_links(FRESH_FILE, fresh)
    fresh_pool = fresh[:]
    is_scanning = False

    embed = discord.Embed(title="✅ Quét xong!", color=0x22c55e, timestamp=datetime.utcnow())
    embed.add_field(name="🟢 Fresh giữ lại", value=f"`{len(fresh)}`",   inline=True)
    embed.add_field(name="🔴 Đã xóa",        value=f"`{len(removed)}`", inline=True)
    embed.add_field(name="📦 Còn trong kho",  value=f"`{len(kept)}`",   inline=True)
    await msg.edit(content=None, embed=embed)
    log(f"[SCAN-CMD] Fresh: {len(fresh)} | Xoa: {len(removed)}")

@bot.command(name="help", aliases=["h"])
async def cmd_help(ctx):
    if not is_allowed(ctx): return
    embed = discord.Embed(title="📖 Gemini Bot - Lệnh", color=0x8b5cf6)
    embed.add_field(name="!get",    value="Lấy 1 link Gemini fresh ngay",             inline=False)
    embed.add_field(name="!stats",  value="Xem số lượng link còn lại",                inline=False)
    embed.add_field(name="!check",  value="Quét toàn bộ file, xóa link hết hạn",     inline=False)
    embed.add_field(name="!help",   value="Xem danh sách lệnh này",                   inline=False)
    embed.set_footer(text="Bot tự động quét link mỗi 30 phút")
    await ctx.send(embed=embed)

# ── Events ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    log(f"[BOT] Da dang nhap: {bot.user} (ID: {bot.user.id})")
    log(f"[BOT] Links hien tai: {len(read_links(LINKS_FILE))}")
    background_scan.start()
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Gemini links | !help")
    )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Kiem tra xem nguoi dung co gui file .txt khong
    if message.attachments:
        for att in message.attachments:
            if att.filename.lower().endswith(".txt"):
                try:
                    raw_bytes = await att.read()
                    content = raw_bytes.decode("utf-8", errors="ignore")
                    extracted = [
                        line.strip() for line in content.splitlines()
                        if line.strip().startswith("http")
                    ]
                    if extracted:
                        existing = set(read_links(LINKS_FILE))
                        new_links = [u for u in extracted if u not in existing]
                        if new_links:
                            with LINKS_FILE.open("a", encoding="utf-8") as f:
                                for u in new_links:
                                    f.write(u + "\n")

                        total_now = len(read_links(LINKS_FILE))
                        embed = discord.Embed(
                            title="📥 Đã nạp file link thành công!",
                            color=0x22c55e,
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="📁 Tên file", value=f"`{att.filename}`", inline=True)
                        embed.add_field(name="➕ Link mới thêm", value=f"`{len(new_links)}` link", inline=True)
                        embed.add_field(name="📦 Tổng kho hiện tại", value=f"`{total_now}` link", inline=True)
                        embed.add_field(
                            name="⚙️ Tự động hóa",
                            value="Bot đã lưu vào kho và sẽ tự động quản lý! Gõ `!get` để lấy link và bot sẽ tự xóa link khỏi file.",
                            inline=False
                        )
                        embed.set_footer(text=f"Gửi bởi {message.author.name}")
                        await message.channel.send(embed=embed)
                        log(f"[UPLOAD] Nhan {len(new_links)} link tu file {att.filename} cua {message.author}")
                    else:
                        await message.channel.send(f"⚠️ File `{att.filename}` không chứa link `http` hợp lệ nào.")
                except Exception as e:
                    await message.channel.send(f"❌ Lỗi khi đọc file `{att.filename}`: {e}")

    # 2. Kiem tra neu gui link truc tiep qua tin nhan (khong phai command)
    elif not message.content.startswith("!") and "serviceactivation.google.com" in message.content:
        words = message.content.split()
        direct_links = [w.strip() for w in words if w.strip().startswith("http")]
        if direct_links:
            existing = set(read_links(LINKS_FILE))
            new_links = [u for u in direct_links if u not in existing]
            if new_links:
                with LINKS_FILE.open("a", encoding="utf-8") as f:
                    for u in new_links:
                        f.write(u + "\n")
                total_now = len(read_links(LINKS_FILE))
                await message.channel.send(
                    f"📥 Đã lưu `{len(new_links)}` link vào kho! Tổng kho hiện tại: `{total_now}` link."
                )

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    log(f"[ERROR] {error}")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if DISCORD_TOKEN == "PASTE_BOT_TOKEN_HERE":
        print("❌ Chua dien token! Mo file discord_bot_config.py va dien DISCORD_TOKEN vao.")
        input("Enter de thoat...")
        sys.exit(1)
    bot.run(DISCORD_TOKEN)
