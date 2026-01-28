import requests
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

BOT_TOKEN = "8560800023:AAEVqAqEQD_8njulLYwoDLMXKBWWk8v4-oU"
OWNER_ID = 7718459027
TIMEZONE = pytz.timezone("Asia/Amman")

CITIES = {
    "عمان": "Amman",
    "إربد": "Irbid",
    "الزرقاء": "Zarqa",
    "العقبة": "Aqaba",
    "السلط": "Salt",
}

def get_prayer_times(city):
    today = datetime.now(TIMEZONE)
    date_str = today.strftime("%d-%m-%Y")

    url = f"https://api.aladhan.com/v1/timingsByCity/{date_str}"
    params = {
        "city": city,
        "country": "Jordan",
        "method": 2
    }

    r = requests.get(url, params=params).json()
    t = r["data"]["timings"]

    return today, t

def to_12h(time_str):
    return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(city, callback_data=city)]
        for city in CITIES
    ]
    await update.message.reply_text(
        "🕌 اختر المحافظة لعرض أوقات الصلاة:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    city_ar = query.data
    city_en = CITIES[city_ar]

    today, times = get_prayer_times(city_en)

    text = f"""📅 {today.strftime('%A %d-%m-%Y')}

📍 {city_ar}

🕋 الفجر: {to_12h(times['Fajr'])}
🌅 الشروق: {to_12h(times['Sunrise'])}
☀️ الظهر: {to_12h(times['Dhuhr'])}
🌇 العصر: {to_12h(times['Asr'])}
🌆 المغرب: {to_12h(times['Maghrib'])}
🌃 العشاء: {to_12h(times['Isha'])}
"""

    await query.edit_message_text(text)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ البوت شغال الآن")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
