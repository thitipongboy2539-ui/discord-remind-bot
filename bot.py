import discord
from discord import app_commands
from discord.ext import commands, tasks
import sqlite3
import datetime
import os

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1465621460805615820
VIP_ROLE_ID = 1465623773934780516
GOLD_ROLE_ID = 1465623162317180969

LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"
MAIN_COLOR = 0x3EF2C5  # มิ้น

# ==============================
# INTENTS
# ==============================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# DATABASE
# ==============================

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    package TEXT,
    expire_at TEXT,
    role_id INTEGER
)
""")
conn.commit()

# ==============================
# FORMAT DATE (พ.ศ.)
# ==============================

def format_thai_datetime(dt):
    months = [
        "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
        "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"
    ]
    days = ["จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"]

    return f"วัน{days[dt.weekday()]}ที่ {dt.day} {months[dt.month-1]} {dt.year+543} {dt.strftime('%H:%M')}"

# ==============================
# EMBED BUILDER
# ==============================

def build_embed(member, package, expire_time):
    remaining = expire_time - datetime.datetime.utcnow()
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    digital_time = f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"

    embed = discord.Embed(
        title="👑 Premium Membership Activated",
        description=f"📦 แพ็กเกจ: **{package}**",
        color=MAIN_COLOR
    )

    embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
    embed.add_field(name="⏳ วันหมดอายุ", value=format_thai_datetime(expire_time), inline=False)
    embed.add_field(name="🕒 เวลาคงเหลือ (Digital)", value=f"```{digital_time}```", inline=False)

    embed.set_image(url=LOGO_URL)
    embed.set_footer(text="🔔 ADMINZENO • Premium System")

    return embed

# ==============================
# CHECK EXPIRE LOOP
# ==============================

@tasks.loop(minutes=1)
async def check_expired():
    now = datetime.datetime.utcnow()

    cursor.execute("SELECT user_id, package, expire_at, role_id FROM subscriptions")
    rows = cursor.fetchall()

    for user_id, package, expire_at, role_id in rows:
        expire_time = datetime.datetime.fromisoformat(expire_at)

        if now >= expire_time:
            guild = bot.get_guild(GUILD_ID)
            member = guild.get_member(user_id)
            role = guild.get_role(role_id)

            if member and role:
                await member.remove_roles(role)

                try:
                    await member.send(f"⛔ แพ็กเกจ {package} ของคุณหมดอายุแล้ว")
                except:
                    pass

            cursor.execute("DELETE FROM subscriptions WHERE user_id=?", (user_id,))
            conn.commit()

# ==============================
# SLASH COMMAND
# ==============================

@bot.tree.command(name="subscribe", description="สมัคร Premium 30 วัน")
@app_commands.describe(
    member="เลือกสมาชิก",
    package="เลือกแพ็กเกจ"
)
@app_commands.choices(package=[
    app_commands.Choice(name="VIP Member", value="VIP"),
    app_commands.Choice(name="Gold Member", value="GOLD")
])
async def subscribe(interaction: discord.Interaction,
                    member: discord.Member,
                    package: app_commands.Choice[str]):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin เท่านั้น", ephemeral=True)
        return

    expire_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)

    if package.value == "VIP":
        role_id = VIP_ROLE_ID
    else:
        role_id = GOLD_ROLE_ID

    role = interaction.guild.get_role(role_id)
    await member.add_roles(role)

    cursor.execute("DELETE FROM subscriptions WHERE user_id=?", (member.id,))
    cursor.execute(
        "INSERT INTO subscriptions VALUES (?, ?, ?, ?)",
        (member.id, package.value, expire_time.isoformat(), role_id)
    )
    conn.commit()

    embed = build_embed(member, package.value, expire_time)

    await interaction.response.send_message(embed=embed)

    try:
        await member.send(f"🎉 คุณได้รับแพ็กเกจ {package.value} 30 วัน")
    except:
        pass

# ==============================
# READY
# ==============================

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    check_expired.start()
    print(f"✅ Premium System Online: {bot.user}")

bot.run(TOKEN)
