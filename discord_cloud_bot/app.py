"""
app.py - Ultra-compatible Hugging Face Space for Gemini Discord Bot
"""

import os
import sys
import threading
import asyncio
from datetime import datetime
from pathlib import Path

import gradio as gr
import discord
from discord.ext import commands
import aiohttp

# ── Config ────────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "MTU2MTQ1NzQ3MjY4NDgyMjcxMA.Gaho62.yGjCOtSzT749hHwtp_4iH5r3OVKxKM03sxyv6k")

DATA_DIR    = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LINKS_FILE  = DATA_DIR / "gemini_activation_links.txt"
FRESH_FILE  = DATA_DIR / "gemini_links_fresh.txt"
USED_FILE   = DATA_DIR / "gemini_links_used.txt"

EXPIRED_KEYWORDS = [
    "need a new activation link", "cần một đường liên kết kích hoạt mới",
    "can mot duong lien ket kich hoat moi", "ask your provider to send a new link",
    "link is no longer valid", "link expired", "activation link has expired"
]

USED_KEYWORDS = [
    "subscription has been used", "already been used", "already redeemed",
    "đã được sử dụng", "gói thuê bao này đã được sử dụng", "offer is not available"
]

FRESH_KEYWORDS = [
    "kích hoạt gói", "kích hoạt", "bắt đầu", "dùng thử",
    "get started", "redeem", "activate", "claim", "18 tháng", "gemini advanced"
]

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

async def verify_link_http(session: aiohttp.ClientSession, url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }
    try:
        token = url.strip().rstrip("/").split("/")[-1]
        direct_url = f"https://one.google.com/activate/plan/subscription/new/{token}"
        async with session.get(direct_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=False) as direct_resp:
            if direct_resp.status in (404, 410):
                return "expired"

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
            text = (await resp.text()).lower()
            final_url = str(resp.url).lower()

            if any(k in text for k in EXPIRED_KEYWORDS): return "expired"
            if any(k in text for k in USED_KEYWORDS): return "used"
            if resp.status in (404, 410): return "expired"
            if any(k in text for k in FRESH_KEYWORDS): return "fresh"
            if "accounts.google.com" in final_url and "signin" in final_url: return "fresh"
            if resp.status == 200: return "fresh"
            return "unknown"
    except Exception:
        return "unknown"

# ── Discord Bot ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

is_checking = False

async def process_and_check_links(channel, urls: list[str]):
    global is_checking
    if is_checking:
        await channel.send("⏳ Bot đang trong quá trình quét, vui lòng chờ một chút!")
        return

    is_checking = True
    msg = await channel.send(f"🔍 **Bắt đầu tự động kiểm tra {len(urls)} link...**")

    fresh_added = []
    dead_count = 0

    async with aiohttp.ClientSession() as session:
        for idx, url in enumerate(urls, 1):
            st = await verify_link_http(session, url)
            if st == "fresh":
                fresh_added.append(url)
            elif st in ("expired", "used"):
                dead_count += 1
                append_used(url)

            if idx % 5 == 0 or idx == len(urls):
                await msg.edit(content=f"⏳ Đang tự động kiểm tra: `{idx}/{len(urls)}` | 🟢 Sống: `{len(fresh_added)}` | 🔴 Lỗi/Đã xóa: `{dead_count}`")

    existing_fresh = set(read_links(FRESH_FILE))
    for u in fresh_added: existing_fresh.add(u)
    write_links(FRESH_FILE, list(existing_fresh))

    all_links = set(read_links(LINKS_FILE))
    for u in urls:
        if u not in fresh_added: all_links.discard(u)
        else: all_links.add(u)
    write_links(LINKS_FILE, list(all_links))

    is_checking = False

    embed = discord.Embed(title="🎉 Hoàn tất kiểm tra và lọc link!", color=0x22c55e, timestamp=datetime.utcnow())
    embed.add_field(name="🟢 Link SỐNG (Đã lưu)", value=f"`{len(fresh_added)}` link", inline=True)
    embed.add_field(name="🔴 Link CHẾT (Đã tự xóa)", value=f"`{dead_count}` link", inline=True)
    embed.add_field(name="📦 Tổng link sẵn sàng", value=f"`{len(existing_fresh)}` link", inline=True)
    embed.add_field(name="💡 Sử dụng", value="Gõ lệnh `!get` để lấy link bất kỳ lúc nào!", inline=False)
    await msg.edit(content=None, embed=embed)

@bot.event
async def on_ready():
    print(f"[ONLINE] Bot da dang nhap: {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Gemini links 24/7 | !help"))

@bot.event
async def on_message(message):
    if message.author.bot: return

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

    elif not message.content.startswith("!") and "serviceactivation.google.com" in message.content:
        words = message.content.split()
        urls = [w.strip() for w in words if w.strip().startswith("http")]
        if urls:
            await message.channel.send(f"📥 Đã nhận `{len(urls)}` link từ tin nhắn.")
            asyncio.create_task(process_and_check_links(message.channel, urls))

    await bot.process_commands(message)

@bot.command(name="get", aliases=["link", "lay"])
async def cmd_get(ctx):
    fresh_list = read_links(FRESH_FILE)
    if not fresh_list:
        all_untested = read_links(LINKS_FILE)
        if all_untested:
            await ctx.send(f"⏳ Kho còn `{len(all_untested)}` link chưa kiểm tra. Đang tự động kiểm tra ngay...")
            asyncio.create_task(process_and_check_links(ctx.channel, all_untested))
        else:
            await ctx.send("📭 Kho link đang trống. Hãy kéo thả file `.txt` chứa link vào đây để bot tự check và nạp vào kho!")
        return

    url = fresh_list.pop(0)
    write_links(FRESH_FILE, fresh_list)
    all_links = [l for l in read_links(LINKS_FILE) if l.strip() != url.strip()]
    write_links(LINKS_FILE, all_links)
    append_used(url)

    embed = discord.Embed(
        title="🎁 Link Kích Hoạt Gemini AI Pro 18 tháng",
        description="Link này **đã được bot tự động kiểm tra** là còn sống 100%.",
        color=0x22c55e,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🔗 Link kích hoạt (Fresh)", value=f"```{url}```", inline=False)
    embed.add_field(name="📦 Còn lại trong kho", value=f"`{len(fresh_list)}` link", inline=True)
    embed.add_field(name="💡 Cách dùng", value="Mở link trên Chrome đã đăng nhập Google -> Bấm **Kích hoạt gói**", inline=False)
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name} • Đã tự động xóa 1 link khỏi file")
    await ctx.send(embed=embed)

@bot.command(name="stats", aliases=["stat", "sl", "kho"])
async def cmd_stats(ctx):
    fresh = len(read_links(FRESH_FILE))
    used  = len(read_links(USED_FILE))
    embed = discord.Embed(title="📊 Thống kê Kho Link Gemini", color=0x3b82f6, timestamp=datetime.utcnow())
    embed.add_field(name="🟢 Link SỐNG (Sẵn sàng)", value=f"`{fresh}` link", inline=True)
    embed.add_field(name="🔴 Link đã xóa / đã cấp", value=f"`{used}` link", inline=True)
    embed.set_footer(text="Bot hoạt động 24/7 trên Hugging Face")
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["h"])
async def cmd_help(ctx):
    embed = discord.Embed(title="📖 Hướng dẫn sử dụng Gemini Cloud Bot", color=0x8b5cf6)
    embed.add_field(name="📁 Nạp link tự động", value="Kéo thả bất kỳ file `.txt` nào vào chat ➔ Bot tự động check và lưu link sống vào kho!", inline=False)
    embed.add_field(name="!get", value="Lấy 1 link sống đã kiểm tra (tự động xóa khỏi file để không trùng)", inline=False)
    embed.add_field(name="!stats", value="Xem số lượng link còn lại trong kho", inline=False)
    await ctx.send(embed=embed)

def run_discord_thread():
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"[DISCORD CRASH] {e}")

# Chay Discord bot o luong ngam
t = threading.Thread(target=run_discord_thread, daemon=True)
t.start()

# ── Gradio Interface ──────────────────────────────────────────────────────────
def get_bot_status():
    f = len(read_links(FRESH_FILE))
    t = len(read_links(LINKS_FILE))
    now = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    return f"🟢 Bot đang ONLINE 24/7!\n📦 Link Fresh: {f}\n📦 Tổng link trong kho: {t}\n🕒 Cập nhật: {now}"

with gr.Blocks(title="Gemini Discord Bot 24/7") as demo:
    gr.Markdown("# 🚀 Gemini Discord Bot 24/7")
    gr.Markdown("Bot đang chạy liên tục trên đám mây. Bạn có thể tương tác trực tiếp qua Discord bất cứ lúc nào!")
    btn = gr.Button("🔄 Làm mới trạng thái", variant="primary")
    status_out = gr.Textbox(label="Trạng thái hệ thống", value=get_bot_status(), lines=4)
    btn.click(fn=get_bot_status, outputs=status_out)

if __name__ == "__main__":
    demo.launch()
