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

# ================= INTENTS =================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= PARSE TIME =================

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

# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ================= SLASH COMMAND =================

@bot.tree.command(name="setrole", description="ตั้งเวลาให้ Role แบบ ADMINZENO")
@app_commands.describe(
    member="เลือกสมาชิก",
    role="เลือก Role",
    duration="เวลา เช่น 30m / 1h / 7d",
    note="หมายเหตุ"
)
async def setrole(
    interaction: discord.Interaction,
    member: discord.Member,
    role: discord.Role,
    duration: str,
    note: str
):

    # จำกัดเฉพาะ Admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ คำสั่งนี้ใช้ได้เฉพาะ Admin เท่านั้น",
            ephemeral=True
        )
        return

    delta = parse_time(duration)
    if not delta:
        await interaction.response.send_message(
            "❌ ใช้เวลาแบบ 30m / 1h / 7d เท่านั้น",
            ephemeral=True
        )
        return

    end_time = datetime.now(timezone.utc) + delta
    unix_time = int(end_time.timestamp())

    await member.add_roles(role)

    # ================= EMBED =================

    embed = discord.Embed(
        title="📅 Check member time!",
        description=f"📝 รายละเอียด\n\nให้ Role {role.mention} กับ {member.mention}",
        color=MINT_COLOR
    )

    embed.set_thumbnail(url=LOGO_URL)

    embed.add_field(name="👤 สร้างโดย", value="🔔 ADMINZENO", inline=False)
    embed.add_field(name="📌 หมายเหตุ", value=note, inline=False)
    embed.add_field(
        name="⏳ หมดอายุ",
        value=f"<t:{unix_time}:F>",
        inline=False
    )
    embed.add_field(
        name="⌛ นับถอยหลัง",
        value=f"<t:{unix_time}:R>",
        inline=False
    )

    embed.set_footer(text="ADMINZENO SYSTEM")

    await interaction.response.send_message(embed=embed)

    # ================= DM USER =================

    try:
        user_dm = discord.Embed(
            title="🎉 คุณได้รับ Role แล้ว!",
            description=f"คุณได้รับ {role.name}",
            color=MINT_COLOR
        )
        user_dm.set_thumbnail(url=LOGO_URL)
        user_dm.add_field(name="หมดอายุ", value=f"<t:{unix_time}:F>")
        user_dm.add_field(name="นับถอยหลัง", value=f"<t:{unix_time}:R>")
        await member.send(embed=user_dm)
    except:
        pass

    # ================= DM ADMIN (ตอนให้ครั้งแรก) =================

    try:
        admin = await bot.fetch_user(ADMIN_NOTIFY_ID)
        await admin.send(
            f"✅ ให้ Role {role.name} กับ {member.name}\nหมดอายุ: <t:{unix_time}:F>"
        )
    except:
        pass

    # ================= WAIT =================

    await asyncio.sleep(delta.total_seconds())

    await member.remove_roles(role)

    # ================= EXPIRE EMBED =================

    expire_embed = discord.Embed(
        title="⏰ Role หมดเวลาแล้ว",
        description=f"{member.mention} ถูกลบ Role {role.name}",
        color=MINT_COLOR
    )

    expire_embed.set_thumbnail(url=LOGO_URL)

    await interaction.channel.send(embed=expire_embed)

    # DM USER
    try:
        await member.send(f"⏰ Role {role.name} ของคุณหมดเวลาแล้ว")
    except:
        pass

    # DM ADMIN
    try:
        admin = await bot.fetch_user(ADMIN_NOTIFY_ID)
        await admin.send(f"⏰ Role {role.name} ของ {member.name} หมดเวลาแล้ว")
    except:
        pass


# ================= RUN =================

if not TOKEN:
    print("❌ DISCORD_TOKEN not found")
else:
    bot.run(TOKEN)
