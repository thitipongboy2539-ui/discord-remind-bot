import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import re
import os

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_ID = 1392851942480412822
LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# TIME PARSER
# ==============================
def parse_time(time_str):
    match = re.match(r"(\d+)([mhd])", time_str.lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400

# ==============================
# FORMAT DATE (พ.ศ.)
# ==============================
def format_thai_datetime(dt):
    thai_months = [
        "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
        "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"
    ]
    thai_days = [
        "จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"
    ]

    year = dt.year + 543
    return f"วัน{thai_days[dt.weekday()]}ที่ {dt.day} {thai_months[dt.month-1]} {year} {dt.strftime('%H:%M')}"

# ==============================
# DIGITAL TIMER STYLE
# ==============================
def format_digital(seconds):
    seconds = int(seconds)

    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"

# ==============================
# COLOR SYSTEM
# ==============================
def get_color(remaining, total):
    if remaining <= total * 0.1:
        return 0xFF4D4D  # แดง
    elif remaining <= total * 0.5:
        return 0xFFD93D  # เหลือง
    else:
        return 0x3EF2C5  # มิ้น

# ==============================
# PROGRESS BAR
# ==============================
def progress_bar(percent):
    total_blocks = 12
    filled = int(total_blocks * percent)
    empty = total_blocks - filled
    return "🟩" * filled + "⬜" * empty

# ==============================
# BUILD EMBED
# ==============================
def build_embed(member, role, expire_time, remaining, total, note):
    percent = remaining / total
    bar = progress_bar(percent)

    embed = discord.Embed(
        title="📅 Check member time!",
        description="Welcome to Zeno Community Mod\nRole ได้รับยศเรียบร้อยครัช",
        color=get_color(remaining, total)
    )

    embed.add_field(name="👤 สมาชิก", value=member.mention, inline=False)
    embed.add_field(name="🏷 Role", value=role.mention, inline=False)
    embed.add_field(name="📝 หมายเหตุ", value=note, inline=False)
    embed.add_field(name="⏳ วันหมดอายุ", value=format_thai_datetime(expire_time), inline=False)

    embed.add_field(
        name="🕹 เวลานับถอยหลัง (Digital)",
        value=f"`{format_digital(remaining)}`",
        inline=False
    )

    embed.add_field(name="📊 Progress", value=bar, inline=False)

    embed.set_image(url=LOGO_URL)
    embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

    return embed

# ==============================
# TIMER LOOP
# ==============================
async def role_timer(message, member, role, expire_time, total_seconds, admin_user, note):
    while True:
        now = datetime.datetime.now()
        remaining = (expire_time - now).total_seconds()

        if remaining <= 0:
            try:
                await member.remove_roles(role)

                expired_embed = discord.Embed(
                    title="⛔ Role หมดเวลาแล้ว",
                    description=f"{member.mention} ถูกลบ {role.mention} แล้ว",
                    color=0xFF0000
                )
                expired_embed.set_footer(text="🔔 ADMINZENO • หมดเวลาแล้ว")

                await message.edit(embed=expired_embed)

                await member.send(f"⛔ Role {role.name} ของคุณหมดเวลาแล้ว")
                await admin_user.send(f"⛔ {member.name} หมดเวลา Role {role.name}")

            except:
                pass
            break

        embed = build_embed(member, role, expire_time, remaining, total_seconds, note)
        await message.edit(embed=embed)

        await asyncio.sleep(5)  # อัปเดตทุก 5 วิ

# ==============================
# SLASH COMMAND
# ==============================
@bot.tree.command(name="setrole", description="ตั้ง Role พร้อมจับเวลา")
@app_commands.describe(
    member="เลือกสมาชิก",
    role="เลือก Role",
    duration="เช่น 30m / 1h / 7d",
    note="หมายเหตุ"
)
async def setrole(interaction: discord.Interaction,
                  member: discord.Member,
                  role: discord.Role,
                  duration: str,
                  note: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ สำหรับ Admin เท่านั้น", ephemeral=True)
        return

    seconds = parse_time(duration)
    if not seconds:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง (30m / 1h / 7d)", ephemeral=True)
        return

    expire_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)

    await member.add_roles(role)

    embed = build_embed(member, role, expire_time, seconds, seconds, note)

    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()

    admin_user = await bot.fetch_user(ADMIN_ID)

    try:
        await member.send(f"🎉 คุณได้รับ Role {role.name} ระยะเวลา {duration}")
        await admin_user.send(f"✅ ให้ Role {role.name} กับ {member.name} สำเร็จ")
    except:
        pass

    bot.loop.create_task(
        role_timer(message, member, role, expire_time, seconds, admin_user, note)
    )

# ==============================
# READY
# ==============================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

bot.run(TOKEN)
