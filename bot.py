import discord
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import re

# ========================
# CONFIG
# ========================
TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "reminders.json"

# 🎨 ADMINZENO THEME
ADMINZENO_COLOR = 0x3EF2C5  # สีมิ้น
LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"

if not TOKEN:
    raise RuntimeError("❌ ไม่พบ DISCORD_TOKEN")

# ========================
# DISCORD SETUP
# ========================
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ========================
# STORAGE
# ========================
def load_reminders():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reminders(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================
# PARSE TIME (1h 30m 7d)
# ========================
def parse_duration(duration_str):
    pattern = re.compile(r"(\d+)([dhm])")
    matches = pattern.findall(duration_str.lower())

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

# ========================
# REMINDER TASK
# ========================
async def schedule_reminder(reminder):
    remind_time = datetime.fromisoformat(reminder["time"])
    now = datetime.now(timezone.utc)

    delay = (remind_time - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)

    guild = client.get_guild(reminder["guild_id"])
    if not guild:
        return

    member = guild.get_member(reminder["target_user_id"])
    role = guild.get_role(reminder["role_id"])

    if member and role:
        try:
            await member.remove_roles(role)
        except Exception as e:
            print("Remove role error:", e)

        # 🔴 Embed ตอนหมดเวลา
        embed = discord.Embed(
            title="📅 Check member time!",
            description="📌 หมายเหตุ\nRole หมดเวลาแล้ว",
            color=0xFF4D4D
        )

        embed.set_thumbnail(url=LOGO_URL)

        embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
        embed.add_field(name="🏷 Role", value=role.mention, inline=False)
        embed.add_field(name="📝 รายละเอียด", value="ระบบได้ลบ Role อัตโนมัติ", inline=False)

        embed.set_footer(text="🔔 ADMINZENO • Premium Role System")

        try:
            await member.send(embed=embed)
        except:
            pass

    reminders = load_reminders()
    reminders = [r for r in reminders if r["id"] != reminder["id"]]
    save_reminders(reminders)

# ========================
# READY
# ========================
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

    reminders = load_reminders()
    for r in reminders:
        client.loop.create_task(schedule_reminder(r))

# ========================
# SLASH COMMAND
# ========================
@tree.command(name="temprole", description="ให้ Role ชั่วคราว (Admin เท่านั้น)")
@app_commands.describe(
    duration="เช่น 30m / 1h / 7d / 2h30m",
    target_user="เลือกสมาชิก",
    role="เลือก Role"
)
async def temprole(
    interaction: discord.Interaction,
    duration: str,
    target_user: discord.Member,
    role: discord.Role
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ คำสั่งนี้สำหรับ Admin เท่านั้น",
            ephemeral=True
        )
        return

    delta = parse_duration(duration)

    if not delta:
        await interaction.response.send_message(
            "❌ รูปแบบเวลาไม่ถูกต้อง (ตัวอย่าง: 30m, 1h, 7d, 2h30m)",
            ephemeral=True
        )
        return

    now = datetime.now(timezone.utc)
    remind_time = now + delta
    expire_timestamp = int(remind_time.timestamp())

    try:
        await target_user.add_roles(role)
    except:
        await interaction.response.send_message(
            "❌ เพิ่ม Role ไม่สำเร็จ (เช็ค Permission)",
            ephemeral=True
        )
        return

    reminder = {
        "id": datetime.now().timestamp(),
        "guild_id": interaction.guild.id,
        "target_user_id": target_user.id,
        "role_id": role.id,
        "time": remind_time.isoformat()
    }

    reminders = load_reminders()
    reminders.append(reminder)
    save_reminders(reminders)

    client.loop.create_task(schedule_reminder(reminder))

    # 🟢 Embed ตอนตั้งสำเร็จ
    embed = discord.Embed(
        title="📅 Check member time!",
        description="📌 สมาชิก\nRole ได้รับยศเรียบร้อยครัช",
        color=ADMINZENO_COLOR
    )

    embed.set_thumbnail(url=LOGO_URL)

    embed.add_field(name="👤 สมาชิก", value=target_user.mention, inline=False)
    embed.add_field(name="🏷 Role", value=role.mention, inline=False)
    embed.add_field(name="📝 จำนวนวันสมาชิก", value=f"ระยะเวลา: {duration}", inline=False)

    embed.add_field(
        name="⏳ วันหมดอายุ",
        value=f"<t:{expire_timestamp}:F>\n(เหลือเวลา <t:{expire_timestamp}:R>)",
        inline=False
    )

    embed.set_footer(text="🔔 ADMINZENO • ยินดีต้อนรับ")

    await interaction.response.send_message(embed=embed)

# ========================
# RUN
# ========================
client.run(TOKEN)
