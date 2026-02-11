import discord
from discord.ext import commands, tasks
import json
import datetime
import os

TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465621460805615820
VIP_ROLE_ID = 1465623773934780516
GOLD_ROLE_ID = 1465623162317180969

ADMIN_CHANNEL_ID = 1471194733836501198
ADMIN_ROLE_ID = 1465623956814827604  # ✅ ใช้ Role ID จริง

DATA_FILE = "premium_data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# Load / Save
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
    print(f"🚀 Enterprise Premium Online: {bot.user}")
    if not check_expiry.is_running():
        check_expiry.start()

# -------------------------
# DM Handler
# -------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):

        content = message.content.lower()

        if content in ["vip", "gold"]:
            pending_users[message.author.id] = content
            await message.channel.send(
                f"📦 เลือกแพ็กเกจ {content.upper()}\n"
                "💸 กรุณาส่งสลิปภายใน 5 นาที"
            )
            return

        if message.attachments:
            if message.author.id not in pending_users:
                await message.channel.send("❌ พิมพ์ vip หรือ gold ก่อน")
                return

            package = pending_users[message.author.id]

            guild = bot.get_guild(GUILD_ID)
            if not guild:
                await message.channel.send("❌ ไม่พบเซิร์ฟเวอร์")
                return

            admin_channel = guild.get_channel(ADMIN_CHANNEL_ID)
            if not admin_channel:
                await message.channel.send("❌ ไม่พบห้องแอดมิน")
                return

            embed = discord.Embed(
                title="💳 สลิปใหม่",
                color=discord.Color.gold()
            )
            embed.add_field(name="User", value=f"{message.author} ({message.author.id})")
            embed.add_field(name="Package", value=package.upper())
            embed.set_image(url=message.attachments[0].url)

            view = ApprovalView(message.author.id, package)

            await admin_channel.send(embed=embed, view=view)
            await message.channel.send("✅ ส่งแล้ว รอแอดมินตรวจสอบ")

    await bot.process_commands(message)

# -------------------------
# Approval View
# -------------------------
class ApprovalView(discord.ui.View):
    def __init__(self, user_id, package):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.package = package

    async def interaction_check(self, interaction: discord.Interaction):
        # 🔒 เฉพาะ Admin Role ID
        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("⛔ เฉพาะแอดมินเท่านั้น", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = bot.get_guild(GUILD_ID)
        if not guild:
            await interaction.response.send_message("❌ Guild ไม่พบ", ephemeral=True)
            return

        member = guild.get_member(self.user_id)
        if not member:
            await interaction.response.send_message("❌ ไม่พบสมาชิก", ephemeral=True)
            return

        role = guild.get_role(VIP_ROLE_ID if self.package == "vip" else GOLD_ROLE_ID)
        if not role:
            await interaction.response.send_message("❌ ไม่พบ Role", ephemeral=True)
            return

        await member.add_roles(role)

        expiry = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

        premium_data[str(self.user_id)] = {
            "package": self.package,
            "expiry": expiry.isoformat(),
            "warned": False
        }

        save_data(premium_data)

        try:
            await member.send(
                f"🎉 ได้รับ {self.package.upper()} แล้ว!\n"
                f"หมดอายุ: {expiry.strftime('%d/%m/%Y %H:%M')}"
            )
        except:
            pass

        await interaction.response.edit_message(content="✅ อนุมัติแล้ว", view=None)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            user = await bot.fetch_user(self.user_id)
            await user.send("❌ การตรวจสอบไม่ผ่าน")
        except:
            pass

        await interaction.response.edit_message(content="❌ ปฏิเสธแล้ว", view=None)

# -------------------------
# Expiry + Warning
# -------------------------
@tasks.loop(minutes=1)
async def check_expiry():

    now = datetime.datetime.now(datetime.UTC)
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        return

    removed = []

    for user_id, data in premium_data.items():

        expiry = datetime.datetime.fromisoformat(data["expiry"])
        member = guild.get_member(int(user_id))

        # 🔔 แจ้งเตือนก่อนหมดอายุ 3 วัน
        if not data.get("warned"):
            if expiry - now <= datetime.timedelta(days=3):
                if member:
                    try:
                        await member.send("⚠️ พรีเมียมของคุณใกล้หมดอายุใน 3 วัน")
                    except:
                        pass
                premium_data[user_id]["warned"] = True
                save_data(premium_data)

        # ⛔ หมดอายุ
        if now >= expiry:

            role = guild.get_role(VIP_ROLE_ID if data["package"] == "vip" else GOLD_ROLE_ID)

            if member and role:
                try:
                    await member.remove_roles(role)
                except:
                    pass

            removed.append(user_id)

    for user_id in removed:
        del premium_data[user_id]

    if removed:
        save_data(premium_data)

bot.run(TOKEN)
