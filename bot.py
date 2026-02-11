import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import re
from datetime import datetime, timedelta, timezone

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

ADMIN_NOTIFY_ID = 1392851942480412822

LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"
MINT_COLOR = 0x98FFCC

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= TIME PARSER =================
def parse_duration(time_str):
    match = re.match(r"(\d+)([smhd])$", time_str.lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

# ================= THAI DATE =================
def thai_datetime(dt):
    thai_months = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
        "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
        "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    thai_days = [
        "วันจันทร์", "วันอังคาร", "วันพุธ",
        "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"
    ]

    day_name = thai_days[dt.weekday()]
    month_name = thai_months[dt.month]
    year_be = dt.year + 543

    return f"{day_name}ที่ {dt.day} {month_name} {year_be} {dt.strftime('%H:%M')}"

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ================= SLASH COMMAND =================
@bot.tree.command(name="setrole", description="🔔 ADMINZENO ตั้งเวลา Role")
@app_commands.describe(
    member="เลือกสมาชิก",
    role="เลือก Role",
    duration="เช่น 30m / 1h / 7d"
)
async def setrole(interaction: discord.Interaction,
                  member: discord.Member,
                  role: discord.Role,
                  duration: str):

    # จำกัดเฉพาะ Admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ ใช้ได้เฉพาะ Admin เท่านั้น",
            ephemeral=True
        )
        return

    delta = parse_duration(duration)
    if not delta:
        await interaction.response.send_message(
            "❌ รูปแบบเวลาใช้ 1h / 30m / 7d",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "✅ ระบบกำลังดำเนินการ (แจ้งเตือนผ่าน DM เท่านั้น)",
        ephemeral=True
    )

    end_time = datetime.now(timezone.utc) + delta
    unix_time = int(end_time.timestamp())
    thai_time = thai_datetime(end_time.astimezone())

    # เพิ่ม Role
    await member.add_roles(role)

    # ================= EMBED =================
    embed = discord.Embed(
        title="📅 Check member time!",
        color=MINT_COLOR
    )

    embed.add_field(
        name="📌 สมาชิก",
        value="Role ได้รับยศเรียบร้อยครัช",
        inline=False
    )

    embed.add_field(
        name="👤 สมาชิก",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="🏷 Role",
        value=role.mention,
        inline=False
    )

    embed.add_field(
        name="📝 จำนวนวันสมาชิก",
        value=f"ระยะเวลา: {duration}",
        inline=False
    )

    embed.add_field(
        name="⏳ วันหมดอายุ",
        value=f"{thai_time}\n(<t:{unix_time}:R>)",
        inline=False
    )

    embed.set_image(url=LOGO_URL)
    embed.set_footer(text="🔔 ADMINZENO • Welcome To community")

    # ================= DM ตอนให้ Role =================
    try:
        await member.send(embed=embed)
    except:
        pass

    try:
        admin_user = await bot.fetch_user(ADMIN_NOTIFY_ID)
        await admin_user.send(embed=embed)
    except:
        pass

    # ================= รอหมดเวลา =================
    await asyncio.sleep(delta.total_seconds())

    # ลบ Role
    await member.remove_roles(role)

    expire_embed = discord.Embed(
        title="⏰ Role หมดอายุแล้ว",
        color=MINT_COLOR
    )

    expire_embed.add_field(
        name="👤 สมาชิก",
        value=member.mention,
        inline=False
    )

    expire_embed.add_field(
        name="🏷 Role ที่ถูกลบ",
        value=role.mention,
        inline=False
    )

    expire_embed.set_footer(text="🔔 ADMINZENO SYSTEM")
    expire_embed.set_image(url=LOGO_URL)

    # ================= DM ตอนหมดเวลา =================
    try:
        await member.send(embed=expire_embed)
    except:
        pass

    try:
        admin_user = await bot.fetch_user(ADMIN_NOTIFY_ID)
        await admin_user.send(embed=expire_embed)
    except:
        pass


# ================= RUN =================
if not TOKEN:
    print("❌ ไม่พบ DISCORD_TOKEN")
else:
    bot.run(TOKEN)
