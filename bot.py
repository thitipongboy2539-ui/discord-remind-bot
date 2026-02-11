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
# FILE STORAGE
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

    message_text = (
        f"⏰ **แจ้งเตือน: {reminder['name']}**\n"
        f"📅 {remind_time.astimezone(THAI_TZ).strftime('%Y-%m-%d %H:%M')}\n"
        f"📝 {reminder['message']}"
    )

    # ส่ง DM ให้เจ้าของ
    try:
        owner = await client.fetch_user(reminder["user_id"])
        await owner.send(message_text)
    except Exception as e:
        print("Owner DM failed:", e)

    # ส่ง DM ให้ user ที่ถูกเลือก (ถ้ามี)
    if reminder.get("notify_user_id"):
        try:
            notify_user = await client.fetch_user(reminder["notify_user_id"])
            await notify_user.send(message_text)
        except Exception as e:
            print("Notify user DM failed:", e)

    # ลบ reminder หลังส่ง
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
    name="ชื่อกิจกรรม",
    message="รายละเอียด",
    notify_user="เลือกคนที่ต้องการให้แจ้งเตือนเพิ่ม (ไม่บังคับ)"
)
async def remind(
    interaction: discord.Interaction,
    date: str,
    time: str,
    name: str,
    message: str,
    notify_user: discord.User = None
):
    try:
        remind_time = datetime.strptime(
            f"{date} {time}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=THAI_TZ).astimezone(timezone.utc)

    except ValueError:
        await interaction.response.send_message(
            "❌ รูปแบบวันที่หรือเวลาไม่ถูกต้อง",
            ephemeral=True
        )
        return

    reminder = {
        "id": datetime.now().timestamp(),
        "user_id": interaction.user.id,
        "time": remind_time.isoformat(),
        "name": name,
        "message": message,
        "notify_user_id": notify_user.id if notify_user else None
    }

    reminders = load_reminders()
    reminders.append(reminder)
    save_reminders(reminders)

    client.loop.create_task(schedule_reminder(reminder))

    await interaction.response.send_message(
        f"✅ แจ้งเตือนวันหมดอายุ!\n"
        f"📌 {name}\n"
        f"📅 {date} ⏰ {time}\n"
        f"👤 แจ้งเตือนเพิ่ม: {notify_user.mention if notify_user else 'ไม่มี'}",
        ephemeral=True
    )

# ========================
# RUN
# ========================
if not TOKEN:
    raise RuntimeError("❌ ไม่พบ DISCORD_TOKEN ใน Environment")

client.run(TOKEN)
