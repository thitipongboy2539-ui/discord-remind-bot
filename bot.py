import discord
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import os
import re

TOKEN = os.getenv("DISCORD_TOKEN")

ADMINZENO_COLOR = 0x3EF2C5
LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"

if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN not found")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =========================
# TIME PARSER
# =========================
def parse_duration(text):
    pattern = re.compile(r"(\d+)([dhm])")
    matches = pattern.findall(text.lower())
    if not matches:
        return None

    delta = timedelta()
    for amount, unit in matches:
        amount = int(amount)
        if unit == "d":
            delta += timedelta(days=amount)
        elif unit == "h":
            delta += timedelta(hours=amount)
        elif unit == "m":
            delta += timedelta(minutes=amount)
    return delta

# =========================
# PROGRESS BAR
# =========================
def make_progress_bar(percent):
    total_blocks = 10
    filled = int(percent * total_blocks)
    empty = total_blocks - filled
    return "▰" * filled + "▱" * empty

# =========================
# COLOR SYSTEM
# =========================
def get_color(percent):
    if percent > 0.5:
        return 0x3EF2C5  # มิ้น
    elif percent > 0.2:
        return 0xFFD93D  # เหลือง
    else:
        return 0xFF4D4D  # แดง

# =========================
# REALTIME ROLE SYSTEM
# =========================
async def role_timer(member, role, duration, interaction):

    start_time = datetime.now(timezone.utc)
    expire_time = start_time + duration

    total_seconds = duration.total_seconds()

    await member.add_roles(role)

    # DM ตอนให้ Role
    try:
        await member.send(f"🎉 คุณได้รับ {role.name} ระยะเวลา {duration}")
        await interaction.user.send(f"✅ คุณให้ {role.name} กับ {member.display_name}")
    except:
        pass

    # ส่ง embed ในห้อง
    message = await interaction.followup.send(embed=build_embed(member, role, start_time, expire_time, total_seconds))

    # ===== LOOP UPDATE =====
    while True:
        now = datetime.now(timezone.utc)
        remaining = (expire_time - now).total_seconds()

        if remaining <= 0:
            break

        percent = remaining / total_seconds

        embed = build_embed(member, role, start_time, expire_time, total_seconds)
        embed.color = get_color(percent)

        try:
            await message.edit(embed=embed)
        except:
            pass

        await asyncio.sleep(60)

    # ===== หมดเวลา =====
    await member.remove_roles(role)

    expired_embed = discord.Embed(
        title="📅 Check member time!",
        description="❌ Role หมดเวลาแล้ว",
        color=0xFF4D4D
    )

    expired_embed.set_thumbnail(url=LOGO_URL)
    expired_embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
    expired_embed.add_field(name="🏷 Role", value=role.mention, inline=False)
    expired_embed.set_footer(text="🔔 ADMINZENO • Expired")

    await message.edit(embed=expired_embed)

    # DM ตอนหมดเวลา
    try:
        await member.send(f"⏳ Role {role.name} ของคุณหมดเวลาแล้ว")
        await interaction.user.send(f"🔔 Role {role.name} ของ {member.display_name} หมดเวลาแล้ว")
    except:
        pass

# =========================
# EMBED BUILDER
# =========================
def build_embed(member, role, start_time, expire_time, total_seconds):

    now = datetime.now(timezone.utc)
    remaining = (expire_time - now).total_seconds()
    percent = max(0, remaining / total_seconds)

    progress = make_progress_bar(percent)
    expire_timestamp = int(expire_time.timestamp())

    thai_year = expire_time.year + 543
    thai_date = expire_time.strftime(f"%Aที่ %d %B {thai_year} %H:%M")

    embed = discord.Embed(
        title="📅 Check member time!",
        description="📌 สมาชิกได้รับยศเรียบร้อยครัช",
        color=get_color(percent)
    )

    embed.set_thumbnail(url=LOGO_URL)

    embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
    embed.add_field(name="🏷 Role", value=role.mention, inline=False)

    embed.add_field(
        name="📝 จำนวนวันสมาชิก",
        value=f"⏳ เหลือเวลา: <t:{expire_timestamp}:R>",
        inline=False
    )

    embed.add_field(
        name="📆 วันหมดอายุ",
        value=f"{thai_date}\n<t:{expire_timestamp}:F>",
        inline=False
    )

    embed.add_field(
        name="📊 Progress",
        value=f"{progress} {int(percent*100)}%",
        inline=False
    )

    embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

    return embed

# =========================
# SLASH COMMAND
# =========================
@tree.command(name="setrole", description="ADMINZENO Premium Role System")
@app_commands.describe(
    member="เลือกสมาชิก",
    role="เลือก Role",
    duration="เช่น 30m / 1h / 7d"
)
async def setrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role, duration: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ สำหรับ Admin เท่านั้น", ephemeral=True)
        return

    delta = parse_duration(duration)
    if not delta:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง", ephemeral=True)
        return

    await interaction.response.defer()

    client.loop.create_task(role_timer(member, role, delta, interaction))

# =========================
# READY
# =========================
@client.event
async def on_ready():
    await tree.sync()
    print(f"🔥 ADMINZENO ONLINE: {client.user}")

client.run(TOKEN)
