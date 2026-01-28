import json, requests, logging
from datetime import datetime
import pytz

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= الإعدادات =================
BOT_TOKEN = "8560800023:AAEVqAqEQD_8njulLYwoDLMXKBWWk8v4-oU"
OWNER_ID = 7718459027
DATA_FILE = "data.json"
TIMEZONE = pytz.timezone("Asia/Amman")

# ================= لوق =================
logging.basicConfig(level=logging.INFO)

# ================= تحميل البيانات =================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "cities": {
                "عمان": "images/عمان.jpg",
                "إربد": "images/اربد.jpg",
                "الزرقاء": "images/الزرقاء.jpg"
            },
            "users": {}
        }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ================= مواقيت الصلاة =================
def get_prayer_times(city):
    r = requests.get(
        "https://api.aladhan.com/v1/timingsByCity",
        params={
            "city": city,
            "country": "Jordan",
            "method": 2
        }
    ).json()
    return r["data"]["timings"]

def to_12h(time_str):
    return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p")

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in data["users"]:
        data["users"][uid] = {"notify": True}
        save_data()

    buttons = []
    for city in data["cities"]:
        buttons.append([InlineKeyboardButton(city, callback_data=f"city:{city}")])

    toggle = "🔔 إيقاف التنبيه" if data["users"][uid]["notify"] else "🔕 تشغيل التنبيه"
    buttons.append([InlineKeyboardButton(toggle, callback_data="toggle")])

    await update.message.reply_text(
        "🕌 اختر المحافظة:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= الأزرار =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)

    if q.data == "toggle":
        data["users"][uid]["notify"] = not data["users"][uid]["notify"]
        save_data()
        await q.edit_message_text("✅ تم تحديث إعداد التنبيه")
        return

    city = q.data.split(":")[1]
    times = get_prayer_times(city)

    now = datetime.now(TIMEZONE)
    date_text = now.strftime("%A %d / %m / %Y")

    text = (
        f"📅 {date_text}\n"
        f"🕌 مواقيت الصلاة – {city}\n\n"
        f"الفجر: {to_12h(times['Fajr'])}\n"
        f"الشروق: {to_12h(times['Sunrise'])}\n"
        f"الظهر: {to_12h(times['Dhuhr'])}\n"
        f"العصر: {to_12h(times['Asr'])}\n"
        f"المغرب: {to_12h(times['Maghrib'])}\n"
        f"العشاء: {to_12h(times['Isha'])}"
    )

    with open(data["cities"][city], "rb") as img:
        await q.message.reply_photo(photo=img, caption=text)

# ================= تنبيه الأذان =================
async def notify(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE).strftime("%H:%M")
    times = get_prayer_times("Amman")

    prayers = {
        "Fajr": "الفجر",
        "Dhuhr": "الظهر",
        "Asr": "العصر",
        "Maghrib": "المغرب",
        "Isha": "العشاء"
    }

    for k, name in prayers.items():
        if times[k] == now:
            for uid, u in data["users"].items():
                if u["notify"]:
                    try:
                        await context.bot.send_message(int(uid), f"🕌 حان وقت أذان {name}")
                    except:
                        pass

# ================= تشغيل =================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify, "interval", minutes=1)
    scheduler.start()

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
  
