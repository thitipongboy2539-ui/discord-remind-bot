import discord
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import os
import json
import re

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_ID = 1392851942480412822

COLOR_MINT = 0x3EF2C5
LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"
DATA_FILE = "roles.json"

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found")

# ================= DISCORD =================
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ================= STORAGE =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ================= TIME PARSER =================
def parse_duration(text):
    pattern = re.findall(r"(\d+)([dhm])", text.lower())
    if not pattern:
        return None

    delta = timedelta()
    for value, unit in pattern:
        value = int(value)
        if unit == "d":
            delta += timedelta(days=value)
        elif unit == "h":
            delta += timedelta(hours=value)
        elif unit == "m":
            delta += timedelta(minutes=value)

    return delta

# ================= FORMAT THAI DATE =================
def thai_datetime(dt):
    thai_months = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
        "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
        "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    thai_days = [
        "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี",
        "ศุกร์", "เสาร์", "อาทิตย์"
    ]

    dt_local = dt.astimezone(timezone(timedelta(hours=7)))
    year_be = dt_local.year + 543

    return f"วัน{thai_days[dt_local.weekday()]}ที่ {dt_local.day} {thai_months[dt_local.month]} {year_be} {dt_local.strftime('%H:%M')}"

# ================= EXPIRE TASK =================
async def expire_role(data):
    expire_time = datetime.fromisoformat(data["expire"])
    now = datetime.now(timezone.utc)

    delay = (expire_time - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)

    guild = client.get_guild(data["guild_id"])
    if not guild:
        return

    member = guild.get_member(data["member_id"])
    role = guild.get_role(data["role_id"])

    if member and role:
        await member.remove_roles(role)

        embed = discord.Embed(
            title="📅 Check member time!",
            description="📌 หมายเหตุ\nRole หมดเวลาแล้ว",
            color=0xFF4D4D
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
        embed.add_field(name="🏷 Role", value=role.mention, inline=False)
        embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

        # DM ผู้รับ
        try:
            await member.send(embed=embed)
        except:
            pass

        # DM คุณ
        admin = await client.fetch_user(ADMIN_ID)
        try:
            await admin.send(embed=embed)
        except:
            pass

        # แจ้งในห้องเดิม
        channel = guild.get_channel(data["channel_id"])
        if channel:
            await channel.send(embed=embed)

    # ลบจากฐานข้อมูล
    records = load_data()
    records = [r for r in records if r["id"] != data["id"]]
    save_data(records)

# ================= READY =================
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

    records = load_data()
    for r in records:
        client.loop.create_task(expire_role(r))

# ================= SLASH COMMAND =================
@tree.command(name="setrole", description="ตั้ง Role ชั่วคราว (Admin เท่านั้น)")
@app_commands.describe(
    member="เลือกสมาชิก",
    role="เลือก Role",
    duration="เช่น 30m / 1h / 7d / 2h30m"
)
async def setrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role, duration: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ สำหรับ Admin เท่านั้น", ephemeral=True)
        return

    delta = parse_duration(duration)
    if not delta:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง", ephemeral=True)
        return

    expire_time = datetime.now(timezone.utc) + delta
    expire_timestamp = int(expire_time.timestamp())

    await member.add_roles(role)

    embed = discord.Embed(
        title="📅 Check member time!",
        description="📌 หมายเหตุ\nRole ได้รับยศเรียบร้อยครัช",
        color=COLOR_MINT
    )

    embed.set_thumbnail(url=LOGO_URL)
    embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
    embed.add_field(name="🏷 Role", value=role.mention, inline=False)
    embed.add_field(name="📝 จำนวนวันสมาชิก", value=f"ระยะเวลา: {duration}", inline=False)
    embed.add_field(
        name="⏳ วันหมดอายุ",
        value=f"{thai_datetime(expire_time)}\nระยะเวลาคงเหลือ: <t:{expire_timestamp}:R>",
        inline=False
    )
    embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

    # แจ้งในห้องที่ใช้คำสั่ง
    await interaction.response.send_message(embed=embed)

    # DM ผู้รับ
    try:
        await member.send(embed=embed)
    except:
        pass

    # DM คุณ
    admin = await client.fetch_user(ADMIN_ID)
    try:
        await admin.send(embed=embed)
    except:
        pass

    # บันทึกข้อมูล
    record = {
        "id": datetime.now().timestamp(),
        "guild_id": interaction.guild.id,
        "channel_id": interaction.channel.id,
        "member_id": member.id,
        "role_id": role.id,
        "expire": expire_time.isoformat()
    }

    data = load_data()
    data.append(record)
    save_data(data)

    client.loop.create_task(expire_role(record))

# ================= RUN =================
client.run(TOKEN)
