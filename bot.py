import discord
from discord import app_commands
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta, timezone

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "reminders.json"
THAI_TZ = timezone(timedelta(hours=7))

# ======================
# CHECK TOKEN (สำคัญมาก)
# ======================
if not TOKEN:
    print("❌ DISCORD_TOKEN not found in Environment")
    sys.exit(0)

# ======================
# DISCORD SETUP
# ======================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ======================
# STORAGE
# ======================
def load_reminders():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reminders(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================
# REMINDER TASK
# ======================
async def schedule_reminder(reminder):
    now = datetime.now(timezone.utc)
    remind_time = datetime.fromisoformat(reminder["time"])
    delay = (remind_time - now).total_seconds()

    if delay > 0:
        await asyncio.sleep(delay)

    user = await client.fetch_user(reminder["user_id"])
    await user.send(f"⏰ แจ้งเตือน:\n{reminder['message']}")

# ======================
# SLASH COMMAND
# ======================
@tree.command(
    name="remind",
    description="ตั้งแจ้งเตือน (วัน/เวลา)"
)
@app_commands.describe(
    date="รูปแบบ YYYY-MM-DD",
    time="รูปแบบ HH:MM (24 ชั่วโมง)",
    message="ข้อความแจ้งเตือน"
)
async def remind(
    interaction: discord.Interaction,
    date: str,
    time: str,
    message: str
):
    try:
        remind_time = datetime.strptime(
            f"{date} {time}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=THAI_TZ).astimezone(timezone.utc)

    except ValueError:
        await interaction.response.send_message(
            "❌ รูปแบบวันหรือเวลาไม่ถูกต้อง",
            ephemeral=True
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

    await interaction.response.send_message(
        f"✅ ตั้งเตือนแล้ว!\n📅 {date}\n⏰ {time}\n📝 {message}",
        ephemeral=True
    )

# ======================
# EVENTS
# ======================
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

    # โหลด reminder ที่ค้างอยู่
    reminders = load_reminders()
    for r in reminders:
        client.loop.create_task(schedule_reminder(r))

# ======================
# RUN BOT
# ======================
client.run(TOKEN)
