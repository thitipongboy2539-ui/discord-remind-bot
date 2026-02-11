import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import datetime

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1465621460805615820

VIP_ROLE_ID = 1465623773934780516
GOLD_ROLE_ID = 1465623162317180969

ADMIN_ID = 1392851942480412822

DATA_FILE = "premium.json"

PROMPTPAY_NUMBER = "0643270431"
BANK_INFO = "กสิกร : ฐิติพงษ์ สมบูรณ์"

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATABASE
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# UTIL
# =========================

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def add_30_days():
    return now() + datetime.timedelta(days=30)

def format_expire(dt):
    thai_year = dt.year + 543
    return dt.strftime(f"%d/%m/{thai_year} %H:%M")

# =========================
# BUY COMMAND
# =========================

@bot.tree.command(name="buy", description="ซื้อแพ็กเกจ VIP / Gold")
async def buy(interaction: discord.Interaction):

    embed = discord.Embed(
        title="💎 Premium Package",
        description="เลือกแพ็กเกจแล้วโอนเงิน จากนั้นส่งสลิปใน DM พร้อมพิมพ์ /submit",
        color=0x3EF2C5
    )

    embed.add_field(name="👑 VIP Member", value="200 บาท / 30 วัน", inline=False)
    embed.add_field(name="🥇 Gold Member", value="100 บาท / 30 วัน", inline=False)
    embed.add_field(name="💳 PromptPay", value=PROMPTPAY_NUMBER, inline=False)
    embed.add_field(name="🏦 ธนาคาร", value=BANK_INFO, inline=False)

    await interaction.response.send_message(embed=embed)

# =========================
# SUBMIT SLIP
# =========================

@bot.tree.command(name="submit", description="ส่งสลิปชำระเงิน")
@app_commands.describe(package="VIP หรือ Gold")
async def submit(interaction: discord.Interaction, package: str):

    if interaction.guild:
        await interaction.response.send_message("❌ กรุณาใช้คำสั่งนี้ใน DM", ephemeral=True)
        return

    if package.lower() not in ["vip", "gold"]:
        await interaction.response.send_message("❌ ระบุ VIP หรือ Gold", ephemeral=True)
        return

    admin = await bot.fetch_user(ADMIN_ID)

    embed = discord.Embed(
        title="📩 มีการส่งสลิปใหม่",
        description=f"ผู้ใช้: {interaction.user.mention}\nแพ็กเกจ: {package.upper()}",
        color=0xFFD93D
    )

    await admin.send(embed=embed)

    await interaction.response.send_message("✅ ส่งคำขอแล้ว รอ Admin ตรวจสอบ")

# =========================
# APPROVE
# =========================

@bot.tree.command(name="approve", description="อนุมัติแพ็กเกจ (Admin)")
@app_commands.describe(member="เลือกสมาชิก", package="VIP หรือ Gold")
async def approve(interaction: discord.Interaction, member: discord.Member, package: str):

    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Admin เท่านั้น", ephemeral=True)
        return

    package = package.lower()

    if package == "vip":
        role_id = VIP_ROLE_ID
    elif package == "gold":
        role_id = GOLD_ROLE_ID
    else:
        await interaction.response.send_message("❌ ระบุ VIP หรือ Gold", ephemeral=True)
        return

    role = interaction.guild.get_role(role_id)

    expire_date = add_30_days()

    await member.add_roles(role)

    data = load_data()
    data.append({
        "user_id": member.id,
        "role_id": role_id,
        "expire": expire_date.isoformat()
    })
    save_data(data)

    embed = discord.Embed(
        title="✅ อนุมัติสำเร็จ",
        description=f"{member.mention} ได้รับ {role.mention}\nหมดอายุ: {format_expire(expire_date)}",
        color=0x3EF2C5
    )

    await interaction.response.send_message(embed=embed)

    await member.send(f"🎉 คุณได้รับ {role.name} หมดอายุ {format_expire(expire_date)}")

# =========================
# AUTO CHECK EXPIRY
# =========================

@tasks.loop(minutes=1)
async def check_expire():

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    data = load_data()
    new_data = []

    for entry in data:
        expire_time = datetime.datetime.fromisoformat(entry["expire"])

        if now() >= expire_time:

            member = guild.get_member(entry["user_id"])
            role = guild.get_role(entry["role_id"])

            if member and role:
                await member.remove_roles(role)
                try:
                    await member.send(f"⛔ {role.name} ของคุณหมดอายุแล้ว")
                except:
                    pass

        else:
            new_data.append(entry)

    save_data(new_data)

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    await bot.tree.sync()
    check_expire.start()
    print(f"✅ ระบบพรีเมียมออนไลน์: {bot.user}")

# =========================
# RUN
# =========================

bot.run(TOKEN)
