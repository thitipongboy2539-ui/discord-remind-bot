import discord
from discord.ext import commands
import os
import asyncio
import re
from datetime import datetime, timedelta, timezone

# ========================
# CONFIG
# ========================

TOKEN = os.getenv("DISCORD_TOKEN")

ADMIN_NOTIFY_ID = 1392851942480412822

LOGO_URL = "https://cdn.phototourl.com/uploads/2026-02-11-5a3eeb2d-d2bf-4821-9742-bdcf3c4d9540.gif"

MINT_COLOR = 0x98FFCC  # สีมิ้น

# ========================
# INTENTS
# ========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ========================
# แปลงเวลา 1h / 30m / 7d
# ========================

def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return timedelta(seconds=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)

    return None


# ========================
# EVENT READY
# ========================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


# ========================
# คำสั่งให้ Role แบบตั้งเวลา
# ========================

@bot.command()
@commands.has_permissions(administrator=True)
async def setrole(ctx, member: discord.Member, role: discord.Role, time_str: str, *, name: str):

    duration = parse_time(time_str)

    if not duration:
        await ctx.send("❌ ใช้เวลาแบบ 30m / 1h / 7d เท่านั้น")
        return

    end_time = datetime.now(timezone.utc) + duration

    # ให้ Role
    await member.add_roles(role)

    # ========================
    # EMBED แจ้งในเซิร์ฟเวอร์
    # ========================

    embed = discord.Embed(
        title="📅 Check member time!",
        description=f"📝 รายละเอียด\n\nให้ Role {role.mention} กับ {member.mention}",
        color=MINT_COLOR
    )

    embed.set_thumbnail(url=LOGO_URL)

    embed.add_field(name="👤 สร้างโดย", value="🔔 ADMINZENO", inline=False)
    embed.add_field(name="📌 หมายเหตุ", value=name, inline=False)
    embed.add_field(name="⏳ เวลาหมดอายุ", value=end_time.strftime("%d %B %Y %H:%M:%S UTC"), inline=False)
    embed.add_field(name="⌛ นับถอยหลัง", value=f"{time_str}", inline=False)

    embed.set_footer(text="ADMINZENO SYSTEM")

    await ctx.send(embed=embed)

    # ========================
    # DM ผู้ใช้
    # ========================

    try:
        user_dm = discord.Embed(
            title="🎉 คุณได้รับ Role แล้ว!",
            description=f"คุณได้รับ {role.name}",
            color=MINT_COLOR
        )
        user_dm.set_thumbnail(url=LOGO_URL)
        user_dm.add_field(name="⏳ หมดอายุใน", value=time_str)
        await member.send(embed=user_dm)
    except:
        pass

    # ========================
    # DM ADMIN ตอนให้ Role ครั้งแรก
    # ========================

    try:
        admin = await bot.fetch_user(ADMIN_NOTIFY_ID)
        await admin.send(f"✅ ให้ Role {role.name} กับ {member.name} แล้ว ({time_str})")
    except:
        pass

    # ========================
    # รอหมดเวลา
    # ========================

    await asyncio.sleep(duration.total_seconds())

    # ลบ Role
    await member.remove_roles(role)

    # ========================
    # แจ้งหมดเวลาในเซิร์ฟเวอร์
    # ========================

    expire_embed = discord.Embed(
        title="⏰ Role หมดเวลาแล้ว",
        description=f"{member.mention} ถูกลบ Role {role.name}",
        color=MINT_COLOR
    )

    expire_embed.set_thumbnail(url=LOGO_URL)

    await ctx.send(embed=expire_embed)

    # ========================
    # DM ผู้ใช้ตอนหมดเวลา
    # ========================

    try:
        await member.send(f"⏰ Role {role.name} ของคุณหมดเวลาแล้ว")
    except:
        pass

    # ========================
    # DM ADMIN ตอนหมดเวลา
    # ========================

    try:
        admin = await bot.fetch_user(ADMIN_NOTIFY_ID)
        await admin.send(f"⏰ Role {role.name} ของ {member.name} หมดเวลาแล้ว")
    except:
        pass


# ========================
# ERROR ADMIN ONLY
# ========================

@setrole.error
async def setrole_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ คำสั่งนี้ใช้ได้เฉพาะ Admin เท่านั้น")


# ========================
# RUN BOT
# ========================

if not TOKEN:
    print("❌ DISCORD_TOKEN not found")
else:
    bot.run(TOKEN)
