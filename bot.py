import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import datetime
import asyncio
import os

TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465621460805615820
VIP_ROLE_ID = 1465623773934780516
GOLD_ROLE_ID = 1465623162317180969

ADMIN_CHANNEL_ID = 1465621460805615820  # 🔥 ใส่ Channel ID ห้องแอดมินตรงนี้

DATA_FILE = "premium_data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# Load / Save Data
# -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

premium_data = load_data()

pending_users = {}

# -------------------------
# Ready
# -------------------------
@bot.event
async def on_ready():
    print(f"🚀 Premium System Online: {bot.user}")
    check_expiry.start()

# -------------------------
# DM Handler
# -------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # เฉพาะ DM เท่านั้น
    if isinstance(message.channel, discord.DMChannel):

        content = message.content.lower()

        if content in ["vip", "gold"]:
            pending_users[message.author.id] = {
                "package": content,
                "time": datetime.datetime.now(datetime.UTC)
            }

            await message.channel.send(
                f"📦 แพ็กเกจ {content.upper()} เลือกแล้ว\n"
                "💸 กรุณาโอนเงินแล้วส่งสลิปภายใน 5 นาที"
            )
            return

        # ถ้ามีไฟล์แนบ = ถือว่าส่งสลิป
        if message.attachments:
            if message.author.id not in pending_users:
                await message.channel.send("❌ กรุณาพิมพ์ vip หรือ gold ก่อน")
                return

            package = pending_users[message.author.id]["package"]

            guild = bot.get_guild(GUILD_ID)
            admin_channel = guild.get_channel(ADMIN_CHANNEL_ID)

            embed = discord.Embed(
                title="💳 มีสลิปใหม่",
                color=discord.Color.gold()
            )
            embed.add_field(name="ผู้ใช้", value=f"{message.author} ({message.author.id})")
            embed.add_field(name="แพ็กเกจ", value=package.upper())
            embed.set_image(url=message.attachments[0].url)

            view = ApprovalView(message.author.id, package)

            await admin_channel.send(embed=embed, view=view)
            await message.channel.send("✅ ส่งสลิปแล้ว รอแอดมินตรวจสอบ")

    await bot.process_commands(message)

# -------------------------
# Approval Buttons
# -------------------------
class ApprovalView(discord.ui.View):
    def __init__(self, user_id, package):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.package = package

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(self.user_id)

        if self.package == "vip":
            role = guild.get_role(VIP_ROLE_ID)
        else:
            role = guild.get_role(GOLD_ROLE_ID)

        await member.add_roles(role)

        expiry = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

        premium_data[str(self.user_id)] = {
            "package": self.package,
            "expiry": expiry.isoformat()
        }

        save_data(premium_data)

        await member.send(
            f"🎉 ได้รับ {self.package.upper()} แล้ว!\n"
            f"หมดอายุ: {expiry.strftime('%d/%m/%Y %H:%M')}"
        )

        await interaction.response.edit_message(content="✅ อนุมัติแล้ว", view=None)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = await bot.fetch_user(self.user_id)
        await user.send("❌ การตรวจสอบไม่ผ่าน กรุณาติดต่อแอดมิน")

        await interaction.response.edit_message(content="❌ ปฏิเสธแล้ว", view=None)

# -------------------------
# Expiry Check Loop
# -------------------------
@tasks.loop(minutes=1)
async def check_expiry():

    now = datetime.datetime.now(datetime.UTC)
    guild = bot.get_guild(GUILD_ID)

    removed = []

    for user_id, data in premium_data.items():

        expiry = datetime.datetime.fromisoformat(data["expiry"])

        if now >= expiry:

            member = guild.get_member(int(user_id))

            if data["package"] == "vip":
                role = guild.get_role(VIP_ROLE_ID)
            else:
                role = guild.get_role(GOLD_ROLE_ID)

            if member and role:
                await member.remove_roles(role)

            removed.append(user_id)

    for user_id in removed:
        del premium_data[user_id]

    save_data(premium_data)

bot.run(TOKEN)
