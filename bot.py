import discord
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import os
import re
import json

TOKEN = os.getenv("DISCORD_TOKEN")

ADMIN_ID = 1392851942480412822
LOG_CHANNEL_ID = 123456789012345678
LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"
MINT = 0x3EF2C5

DATA_FILE = "temprole.json"

if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN not found")

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# ================= STORAGE =================

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ================= TIME PARSER =================

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


# ================= THAI DATE =================

def thai_datetime(dt):
    thai_months = [
        "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
        "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"
    ]
    thai_days = [
        "จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"
    ]

    day_name = thai_days[dt.weekday()]
    day = dt.day
    month = thai_months[dt.month - 1]
    year = dt.year + 543
    time_str = dt.strftime("%H:%M")

    return f"วัน{day_name}ที่ {day} {month} {year} เวลา {time_str}"


# ================= SCHEDULER =================

async def schedule_expire(data):
    expire_time = datetime.fromisoformat(data["expire"])
    delay = (expire_time - datetime.now(timezone.utc)).total_seconds()

    if delay > 0:
        await asyncio.sleep(delay)

    guild = client.get_guild(data["guild"])
    if not guild:
        return

    member = guild.get_member(data["member"])
    role = guild.get_role(data["role"])
    channel = guild.get_channel(LOG_CHANNEL_ID)

    if member and role:
        await member.remove_roles(role)

        embed = discord.Embed(
            title="📅 Check member time!",
            color=MINT
        )
        embed.set_thumbnail(url=LOGO_URL)

        embed.add_field(name="📌 หมายเหตุ", value="Role หมดเวลาแล้ว", inline=False)
        embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
        embed.add_field(name="🏷 Role", value=role.mention, inline=False)
        embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

        if channel:
            await channel.send(embed=embed)

        try:
            await member.send(embed=embed)
        except:
            pass

        try:
            admin = await client.fetch_user(ADMIN_ID)
            await admin.send(embed=embed)
        except:
            pass

    saved = load_data()
    saved = [x for x in saved if x["id"] != data["id"]]
    save_data(saved)


# ================= READY =================

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

    for item in load_data():
        client.loop.create_task(schedule_expire(item))


# ================= SLASH COMMAND =================

@tree.command(name="setrole", description="กำหนด Role แบบจำกัดเวลา (Admin)")
@app_commands.describe(
    member="เลือกสมาชิก",
    role="เลือก Role",
    duration="เช่น 30m / 1h / 7d",
    note="หมายเหตุ"
)
async def setrole(
    interaction: discord.Interaction,
    member: discord.Member,
    role: discord.Role,
    duration: str,
    note: str
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin เท่านั้น", ephemeral=True)
        return

    delta = parse_duration(duration)
    if not delta:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง", ephemeral=True)
        return

    now = datetime.now(timezone.utc)
    expire = now + delta

    await member.add_roles(role)

    expire_ts = int(expire.timestamp())
    thai_date_text = thai_datetime(expire.astimezone())

    embed = discord.Embed(
        title="📅 Check member time!",
        color=MINT
    )

    embed.set_thumbnail(url=LOGO_URL)

    embed.add_field(name="📌 หมายเหตุ", value=note, inline=False)
    embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
    embed.add_field(name="🏷 Role", value=role.mention, inline=False)
    embed.add_field(name="📝 ระยะเวลา", value=duration, inline=False)
    embed.add_field(
        name="⏳ วันหมดอายุ",
        value=f"{thai_date_text}\nระยะเวลาคงเหลือ: <t:{expire_ts}:R>",
        inline=False
    )

    embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

    channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

    try:
        await member.send(embed=embed)
    except:
        pass

    try:
        admin = await client.fetch_user(ADMIN_ID)
        await admin.send(embed=embed)
    except:
        pass

    save = load_data()
    data = {
        "id": datetime.now().timestamp(),
        "guild": interaction.guild.id,
        "member": member.id,
        "role": role.id,
        "expire": expire.isoformat()
    }
    save.append(data)
    save_data(save)

    client.loop.create_task(schedule_expire(data))

    await interaction.response.send_message("✅ ตั้ง Role สำเร็จ", ephemeral=True)


client.run(TOKEN)
