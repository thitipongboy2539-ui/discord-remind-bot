import discord
from discord.ext import commands, tasks
import datetime
import json
import os

TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465621460805615820
VIP_ROLE_ID = 1465623773934780516
GOLD_ROLE_ID = 1465623162317180969

DATA_FILE = "premium_data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_ready():
    print(f"✅ ระบบพรีเมียมออนไลน์: {bot.user}")
    check_expiry.start()


@tasks.loop(seconds=60)
async def check_expiry():
    data = load_data()
    now = datetime.datetime.now(datetime.UTC)
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        return

    for user_id in list(data.keys()):
        expiry = datetime.datetime.fromisoformat(data[user_id]["expiry"])

        if now >= expiry:
            member = guild.get_member(int(user_id))
            if member:
                role_id = VIP_ROLE_ID if data[user_id]["package"] == "VIP" else GOLD_ROLE_ID
                role = guild.get_role(role_id)
                if role in member.roles:
                    await member.remove_roles(role)

            del data[user_id]

    save_data(data)


@bot.command()
async def premium(ctx):
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("❌ คุณไม่มีสถานะ VIP / Gold")
        return

    expiry = datetime.datetime.fromisoformat(data[user_id]["expiry"])
    now = datetime.datetime.now(datetime.UTC)
    remaining = expiry - now

    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    await ctx.send(
        f"👑 Package: {data[user_id]['package']}\n"
        f"⏳ หมดอายุ: {expiry}\n"
        f"⌛ คงเหลือ: {days} วัน {hours} ชม {minutes} นาที {seconds} วินาที"
    )


bot.run(TOKEN)
