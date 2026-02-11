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
# BOT
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

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def format_time(dt):
    thai_year = dt.year + 543
    return dt.strftime(f"%d/%m/{thai_year} %H:%M")

# =========================
# BUY
# =========================

@bot.tree.command(name="buy", description="ซื้อ VIP หรือ Gold")
async def buy(interaction: discord.Interaction):

    embed = discord.Embed(
        title="💎 Premium Package",
        color=0x3EF2C5
    )

    embed.add_field(name="👑 VIP Member", value="200 บาท / 30 วัน", inline=False)
    embed.add_field(name="🥇 Gold Member", value="100 บาท / 30 วัน", inline=False)
    embed.add_field(name="💳 PromptPay", value=PROMPTPAY_NUMBER, inline=False)
    embed.add_field(name="🏦 ธนาคาร", value=BANK_INFO, inline=False)

    await interaction.response.send_message(embed=embed)

# =========================
# STATUS
# =========================

@bot.tree.command(name="status", description="เช็คสถานะสมาชิก")
async def status(interaction: discord.Interaction):

    data = load_data()
    user_data = next((x for x in data if x["user_id"] == interaction.user.id), None)

    if not user_data:
        await interaction.response.send_message("❌ คุณยังไม่มีแพ็กเกจ", ephemeral=True)
        return

    expire = datetime.datetime.fromisoformat(user_data["expire"])
    remaining = expire - now()

    embed = discord.Embed(
        title="📊 สถานะสมาชิก",
        color=0x3EF2C5
    )

    embed.add_field(name="Role ID", value=user_data["role_id"])
    embed.add_field(name="หมดอายุ", value=format_time(expire))
    embed.add_field(name="เหลือเวลา", value=str(remaining).split(".")[0])

    await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# APPROVE
# =========================

@bot.tree.command(name="approve", description="อนุมัติ (Admin)")
@app_commands.describe(member="สมาชิก", package="VIP หรือ Gold")
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
        await interaction.response.send_message("❌ VIP หรือ Gold เท่านั้น", ephemeral=True)
        return

    guild = bot.get_guild(GUILD_ID)
    role = guild.get_role(role_id)

    data = load_data()
    existing = next((x for x in data if x["user_id"] == member.id), None)

    if existing:
        old_expire = datetime.datetime.fromisoformat(existing["expire"])
        if old_expire > now():
            new_expire = old_expire + datetime.timedelta(days=30)
        else:
            new_expire = now() + datetime.timedelta(days=30)
        existing["expire"] = new_expire.isoformat()
    else:
        new_expire = now() + datetime.timedelta(days=30)
        data.append({
            "user_id": member.id,
            "role_id": role_id,
            "expire": new_expire.isoformat()
        })

    save_data(data)

    await member.add_roles(role)

    embed = discord.Embed(
        title="✅ อนุมัติสำเร็จ",
        description=f"{member.mention} ได้รับ {role.mention}\nหมดอายุ: {format_time(new_expire)}",
        color=0x3EF2C5
    )

    await interaction.response.send_message(embed=embed)
    await member.send(f"🎉 คุณได้รับ {role.name} ถึง {format_time(new_expire)}")

# =========================
# AUTO EXPIRE + 1 DAY WARNING
# =========================

@tasks.loop(minutes=1)
async def check_expire():

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    data = load_data()
    new_data = []

    for entry in data:
        expire = datetime.datetime.fromisoformat(entry["expire"])
        member = guild.get_member(entry["user_id"])
        role = guild.get_role(entry["role_id"])

        if not member:
            continue

        remaining = expire - now()

        # แจ้งเตือนก่อนหมด 1 วัน
        if datetime.timedelta(hours=23) < remaining < datetime.timedelta(hours=24):
            try:
                await member.send("⚠️ แพ็กเกจของคุณจะหมดภายใน 24 ชั่วโมง")
            except:
                pass

        if now() >= expire:
            if role:
                await member.remove_roles(role)
            try:
                await member.send("⛔ แพ็กเกจของคุณหมดอายุแล้ว")
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
    print(f"🚀 Premium Business System Online: {bot.user}")

# =========================
# RUN
# =========================

bot.run(TOKEN)
