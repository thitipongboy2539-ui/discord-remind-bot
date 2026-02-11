import discord
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os

# ========================
# CONFIG
# ========================
DATA_FILE = "reminders.json"
TOKEN = os.getenv("DISCORD_TOKEN")
THAI_TZ = timezone(timedelta(hours=7))

# ========================
# DISCORD SETUP
# ========================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ========================
# FILE HELPERS
# ========================
def load_reminders():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reminders(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================
# REMINDER SCHEDULER
# ========================
async def schedule_reminder(reminder):
    remind_time = datetime.fromisoformat(reminder["time"])

    if remind_time.tzinfo is None:
        remind_time = remind_time.replace(tzinfo=timezone.utc)
    else:
        remind_time = remind_time.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)
    delay = (remind_time - now).total_seconds()

    if delay > 0:
        await asyncio.sleep(delay)

    try:
        user = await client.fetch_user(reminder["user_id"])
        await user.send(
            f"⏰ **แจ้งเตือนถึงเวลาแล้ว!**\n"
            f"📅 {remind_time.astimezone(THAI_TZ).strftime('%Y-%m-%d %H:%M')}\n"
            f"📝 {reminder['message']}"
        )
    except Exception as e:
        print("Send failed:", e)

    # ลบหลังส่ง
    reminders = load_reminders()
    reminders = [r for r in reminders if r["id"] != reminder["id"]]
    save_reminders(reminders)

# ========================
# ON READY
# ========================
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

    reminders = load_reminders()
    for r in reminders:
        client.loop.create_task(schedule_reminder(r))

# ========================
# SLASH COMMAND
# ========================
@tree.command(name="remind", description="ตั้งแจ้งเตือน")
@app_commands.describe(
    date="YYYY-MM-DD",
    time="HH:MM (24h)",
    message="ข้อความเตือน"
)
async def remind(interaction: discord.Interaction, date: str, time: str, message: str):
    try:
        remind_time = datetime.strptime(
            f"{date} {time}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=THAI_TZ).astimezone(timezone.utc)

    except ValueError:
        await interaction.response.send_message(
            "❌ รูปแบบวันที่หรือเวลาไม่ถูกต้อง", ephemeral=True
        )
        return

    reminder = {
        "id": datetime.now().timestamp(),
        "user_id": interaction.user.id,
        "time": remind_time.isoformat(),
        "message": message
    }

    reminders = load_reminders()
    reminders.append(reminder)
    save_reminders(reminders)

    client.loop.create_task(schedule_reminder(reminder))

    # ===== COUNTDOWN =====
    now = datetime.now(timezone.utc)
    seconds_left = int((remind_time - now).total_seconds())

    if seconds_left > 0:
        days = seconds_left // 86400
        hours = (seconds_left % 86400) // 3600
        minutes = (seconds_left % 3600) // 60

        countdown_text = f"{days} วัน {hours} ชั่วโมง {minutes} นาที"
    else:
        countdown_text = "กำลังจะถึงเวลาแล้ว!"

    await interaction.response.send_message(
        f"✅ ตั้งเตือนแล้ว!\n"
        f"📅 {date} ⏰ {time}\n"
        f"📝 {message}\n"
        f"⏳ เหลือเวลาอีก {countdown_text}",
        ephemeral=True
    )

# ========================
# RUN
# ========================
if not TOKEN:
    raise RuntimeError("❌ ไม่พบ DISCORD_TOKEN ใน Environment")

client.run(TOKEN)
