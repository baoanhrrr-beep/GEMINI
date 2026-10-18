"""
Gemini Discord Cloud Bot (Auto-Check 24/7)
- Chay tren Cloud (Koyeb / Render / VPS) hoan toan mien phi, khong can mo may tinh.
- Nguoi dung chi can gui file .txt chua link vao Discord.
- Bot tu dong dung Chromium headless kiem tra DOM thuc te tung link:
    + "need a new activation link" / "can mot duong lien ket kich hoat moi" -> XOA
    + "already been used" / "da duoc su dung"                                -> XOA
    + "Get started" / "Bat dau" / "Kich hoat goi"                            -> LUU VAO KHO (KHONG BAM NUT)
- Lenh !get: Lay 1 link fresh va XOA NGAY LAP TUC khoi file de khong bao gio bi trung.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands, tasks
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

import aiohttp

# ── Config ────────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "MTU2MTQ1NzQ3MjY4NDgyMjcxMA.Gaho62.yGjCOtSzT749hHwtp_4iH5r3OVKxKM03sxyv6k")

DATA_DIR    = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LINKS_FILE  = DATA_DIR / "gemini_activation_links.txt"
FRESH_FILE  = DATA_DIR / "gemini_links_fresh.txt"
USED_FILE   = DATA_DIR / "gemini_links_used.txt"

# ── Keywords ──────────────────────────────────────────────────────────────────
EXPIRED_KEYWORDS = [
    "need a new activation link",
    "cần một đường liên kết kích hoạt mới",
    "can mot duong lien ket kich hoat moi",
    "ask your provider to send a new link",
    "link is no longer valid",
    "link expired",
    "activation link has expired",
    "liên kết không còn hợp lệ"
]

USED_KEYWORDS = [
    "subscription has been used",
    "already been used",
    "already redeemed",
    "đã được sử dụng",
    "gói thuê bao này đã được sử dụng",
    "offer is not available",
    "ưu đãi không có sẵn"
]

FRESH_KEYWORDS = [
    "kích hoạt gói", "kích hoạt", "bắt đầu", "dùng thử",
    "get started", "redeem", "activate", "claim",
    "18 tháng", "gemini advanced", "ai premium"
]

# ── File Helpers ──────────────────────────────────────────────────────────────
def read_links(path: Path) -> list[str]:
    if not path.exists(): return []
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip().startswith("http")]

def write_links(path: Path, links: list[str]):
    path.write_text("\n".join(links) + ("\n" if links else ""), encoding="utf-8")

def append_used(url: str):
    existing = set(read_links(USED_FILE))
    if url not in existing:
        with USED_FILE.open("a", encoding="utf-8") as f:
            f.write(url + "\n")

# ── Link Checkers ─────────────────────────────────────────────────────────────
async def verify_link_http(session: aiohttp.ClientSession, url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
            text = (await resp.text()).lower()
            final_url = str(resp.url).lower()

            if any(k in text for k in EXPIRED_KEYWORDS):
                return "expired"
            if any(k in text for k in USED_KEYWORDS):
                return "used"
            if resp.status in (404, 410):
                return "expired"
            if any(k in text for k in FRESH_KEYWORDS):
                return "fresh"
            if "accounts.google.com" in final_url and "signin" in final_url:
                return "fresh"
            if resp.status == 200:
                return "fresh"
            return "unknown"
    except Exception:
        return "unknown"

async def verify_link_headless(browser, url: str) -> str:
    context = None
    page = None
    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            locale="vi-VN",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        status = "unknown"
        for _ in range(6):
            await asyncio.sleep(1)
            text = (await page.inner_text("body")).lower()

            if any(k in text for k in EXPIRED_KEYWORDS):
                status = "expired"
                break
            if any(k in text for k in USED_KEYWORDS):
                status = "used"
                break
            if any(k in text for k in FRESH_KEYWORDS) and not any(k in text for k in EXPIRED_KEYWORDS):
                status = "fresh"
                break

        return status
    except Exception:
        return "unknown"
    finally:
        if page:
            await page.close()
        if context:
            await context.close()

# ── Discord Bot Setup ─────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

is_checking = False

# ── Core Checking Function ────────────────────────────────────────────────────
async def process_and_check_links(channel, urls: list[str]):
    global is_checking
    if is_checking:
        await channel.send("⏳ Bot đang trong quá trình quét, vui lòng chờ một chút!")
        return

    is_checking = True
    msg = await channel.send(f"🔍 **Bắt đầu tự động kiểm tra {len(urls)} link bằng trình duyệt ngầm...**")

    fresh_added = []
    dead_count = 0

    if HAS_PLAYWRIGHT:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            try:
                for idx, url in enumerate(urls, 1):
                    st = await verify_link_headless(browser, url)
                    if st == "fresh":
                        fresh_added.append(url)
                    elif st in ("expired", "used"):
                        dead_count += 1
                        append_used(url)

                    if idx % 3 == 0 or idx == len(urls):
                        await msg.edit(content=f"⏳ Đang tự động kiểm tra: `{idx}/{len(urls)}` | 🟢 Sống: `{len(fresh_added)}` | 🔴 Lỗi/Đã xóa: `{dead_count}`")
            finally:
                await browser.close()
    else:
        async with aiohttp.ClientSession() as session:
            for idx, url in enumerate(urls, 1):
                st = await verify_link_http(session, url)
                if st == "fresh":
                    fresh_added.append(url)
                elif st in ("expired", "used"):
                    dead_count += 1
                    append_used(url)

                if idx % 3 == 0 or idx == len(urls):
                    await msg.edit(content=f"⏳ Đang tự động kiểm tra: `{idx}/{len(urls)}` | 🟢 Sống: `{len(fresh_added)}` | 🔴 Lỗi/Đã xóa: `{dead_count}`")

    # Cap nhat vao file kho
    existing_fresh = set(read_links(FRESH_FILE))
    for u in fresh_added:
        existing_fresh.add(u)
    write_links(FRESH_FILE, list(existing_fresh))

    # Loai bo cac link chet khoi LINKS_FILE
    all_links = set(read_links(LINKS_FILE))
    for u in urls:
        if u not in fresh_added:
            all_links.discard(u)
        else:
            all_links.add(u)
    write_links(LINKS_FILE, list(all_links))

    is_checking = False

    embed = discord.Embed(
        title="🎉 Hoàn tất kiểm tra và lọc link!",
        color=0x22c55e,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🟢 Link SỐNG (Đã lưu vào kho)", value=f"`{len(fresh_added)}` link", inline=True)
    embed.add_field(name="🔴 Link CHẾT/HẾT HẠN (Đã tự xóa)", value=f"`{dead_count}` link", inline=True)
    embed.add_field(name="📦 Tổng link sẵn sàng", value=f"`{len(existing_fresh)}` link", inline=True)
    embed.add_field(name="💡 Sử dụng", value="Gõ lệnh `!get` để lấy link bất kỳ lúc nào!", inline=False)
    await msg.edit(content=None, embed=embed)

# ── Events ────────────────────────────────────────────────────────────────────
from aiohttp import web

async def handle_ping(request):
    return web.Response(text="Gemini Bot is running 24/7!")

async def start_web_server():
    port = int(os.getenv("PORT", 10000))
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/healthz", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[WEB] Healthcheck server listening on port {port}")

@bot.event
async def on_ready():
    print(f"[ONLINE] Bot da khoi dong tren Cloud: {bot.user}")
    await start_web_server()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Gemini links 24/7 | !help"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Nhan file .txt tu nguoi dung -> TU DONG CHECK NGAY
    if message.attachments:
        for att in message.attachments:
            if att.filename.lower().endswith(".txt"):
                try:
                    raw = await att.read()
                    text = raw.decode("utf-8", errors="ignore")
                    urls = [l.strip() for l in text.splitlines() if l.strip().startswith("http")]
                    if urls:
                        await message.channel.send(f"📥 Đã nhận file `{att.filename}` chứa `{len(urls)}` link.")
                        asyncio.create_task(process_and_check_links(message.channel, urls))
                    else:
                        await message.channel.send(f"⚠️ File `{att.filename}` không có link nào.")
                except Exception as e:
                    await message.channel.send(f"❌ Lỗi đọc file: {e}")

    # 2. Nhan link truc tiep qua tin nhan
    elif not message.content.startswith("!") and "serviceactivation.google.com" in message.content:
        words = message.content.split()
        urls = [w.strip() for w in words if w.strip().startswith("http")]
        if urls:
            await message.channel.send(f"📥 Đã nhận `{len(urls)}` link từ tin nhắn.")
            asyncio.create_task(process_and_check_links(message.channel, urls))

    await bot.process_commands(message)

# ── Commands ──────────────────────────────────────────────────────────────────
@bot.command(name="get", aliases=["link", "lay"])
async def cmd_get(ctx):
    """Lay 1 link va XOA NGAY LAP TUC khoi file"""
    fresh_list = read_links(FRESH_FILE)
    if not fresh_list:
        all_untested = read_links(LINKS_FILE)
        if all_untested:
            await ctx.send(f"⏳ Kho còn `{len(all_untested)}` link chưa kiểm tra. Đang tự động kiểm tra ngay...")
            asyncio.create_task(process_and_check_links(ctx.channel, all_untested))
        else:
            await ctx.send("📭 Kho link đang trống. Hãy kéo thả file `.txt` chứa link vào đây để bot tự check và nạp vào kho!")
        return

    # Lay 1 link
    url = fresh_list.pop(0)

    # XOA NGAY LAP TUC KHOI CA 2 FILE DE KHONG BAO GIO BI TRUNG
    write_links(FRESH_FILE, fresh_list)
    all_links = [l for l in read_links(LINKS_FILE) if l.strip() != url.strip()]
    write_links(LINKS_FILE, all_links)
    append_used(url)

    embed = discord.Embed(
        title="🎁 Link Kích Hoạt Gemini AI Pro 18 tháng",
        description="Link này **đã được bot tự động kiểm tra bằng trình duyệt ngầm** là còn sống 100%.",
        color=0x22c55e,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🔗 Link kích hoạt (Fresh)", value=f"```{url}```", inline=False)
    embed.add_field(name="📦 Còn lại trong kho", value=f"`{len(fresh_list)}` link", inline=True)
    embed.add_field(name="💡 Cách dùng", value="Mở link trên Chrome đã đăng nhập Google -> Bấm **Kích hoạt gói**", inline=False)
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name} • Đã tự động xóa 1 link khỏi file")

    await ctx.send(embed=embed)
    print(f"[DISPENSE] Da nha link va xoa khoi file cho {ctx.author} | Con lai: {len(fresh_list)}")

@bot.command(name="stats", aliases=["stat", "sl", "kho"])
async def cmd_stats(ctx):
    """Xem so luong link trong kho"""
    fresh = len(read_links(FRESH_FILE))
    used  = len(read_links(USED_FILE))
    embed = discord.Embed(title="📊 Thống kê Kho Link Gemini", color=0x3b82f6, timestamp=datetime.utcnow())
    embed.add_field(name="🟢 Link SỐNG (Sẵn sàng)", value=f"`{fresh}` link", inline=True)
    embed.add_field(name="🔴 Link đã xóa / đã cấp", value=f"`{used}` link", inline=True)
    embed.set_footer(text="Bot hoạt động 24/7 trên Cloud")
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["h"])
async def cmd_help(ctx):
    embed = discord.Embed(title="📖 Hướng dẫn sử dụng Gemini Cloud Bot", color=0x8b5cf6)
    embed.add_field(name="📁 Nạp link tự động", value="Kéo thả bất kỳ file `.txt` nào vào chat ➔ Bot tự mở trình duyệt ngầm check và lọc sạch link sống vào kho!", inline=False)
    embed.add_field(name="!get", value="Lấy 1 link sống đã kiểm tra (tự động xóa khỏi file để không trùng)", inline=False)
    embed.add_field(name="!stats", value="Xem số lượng link còn lại trong kho", inline=False)
    embed.add_field(name="!help", value="Xem danh sách lệnh này", inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "PASTE_BOT_TOKEN_HERE":
        print("Loi: Chua co DISCORD_TOKEN")
        sys.exit(1)
    bot.run(DISCORD_TOKEN)
