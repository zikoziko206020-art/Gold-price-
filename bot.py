"""بوت تيليجرام لأسعار الذهب والفضة مقابل الدولار والريال اليمني"""
import logging
import os
from datetime import time as dt_time

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import BOT_TOKEN, CHAT_ID
from card_generator import generate_daily_card
from gold_price import get_gold_price_usd_per_ounce
from exchange_rate import get_usd_yer_sanaa
from config import TROY_OUNCE_IN_GRAMS
from price_history import save_today_price, get_yesterday_price
from chart_generator import generate_weekly_chart

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MORNING_UTC = dt_time(hour=6, minute=0)
EVENING_UTC = dt_time(hour=14, minute=0)
POLL_WEEKDAY = 5  # السبت


def _current_gram21_sanaa() -> float:
    ounce_usd = get_gold_price_usd_per_ounce()
    gram24_usd = ounce_usd / TROY_OUNCE_IN_GRAMS
    gram21_usd = gram24_usd * 21 / 24
    usd_sanaa = get_usd_yer_sanaa()["sell"]
    return gram21_usd * usd_sanaa


def _build_change_caption() -> str:
    """يبني نص تعليق (caption) بسيط للصورة يشمل مؤشر التغيّر"""
    try:
        today_price = _current_gram21_sanaa()
        save_today_price(today_price)

        yesterday = get_yesterday_price()
        if not yesterday:
            return "📊 تحديث أسعار الذهب والفضة اليوم"

        diff = today_price - yesterday["price"]
        pct = (diff / yesterday["price"]) * 100 if yesterday["price"] else 0

        if diff > 0:
            return f"🔺 ارتفاع عيار 21 بمقدار {abs(diff):,.0f} ريال ({abs(pct):.2f}%)"
        elif diff < 0:
            return f"🔻 انخفاض عيار 21 بمقدار {abs(diff):,.0f} ريال ({abs(pct):.2f}%)"
        else:
            return "➖ لا تغيير في سعر عيار 21 عن آخر تحديث"
    except Exception as e:
        logger.exception("فشل حساب مؤشر التغيّر: %s", e)
        return "📊 تحديث أسعار الذهب والفضة اليوم"


async def send_daily_card(context: ContextTypes.DEFAULT_TYPE, with_chart: bool = False):
    """يرسل البطاقة الشاملة (صرف + ذهب + فضة) كصورة واحدة بدل النصوص المنفصلة"""
    try:
        card_path = generate_daily_card()
        caption = _build_change_caption()

        with open(card_path, "rb") as photo:
            await context.bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption)
        logger.info("تم نشر البطاقة اليومية بنجاح")

        if with_chart:
            chart_path = generate_weekly_chart()
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=photo,
                        caption="📈 الرسم البياني الأسبوعي لسعر جرام الذهب عيار 21 (صنعاء)",
                    )
                logger.info("تم نشر الرسم البياني الأسبوعي بنجاح")
    except Exception as e:
        logger.exception("فشل نشر البطاقة اليومية: %s", e)


async def send_morning_update(context: ContextTypes.DEFAULT_TYPE):
    await send_daily_card(context, with_chart=True)


async def send_evening_update(context: ContextTypes.DEFAULT_TYPE):
    await send_daily_card(context, with_chart=False)


async def send_weekly_poll(context: ContextTypes.DEFAULT_TYPE):
    try:
        import datetime as dt
        if dt.datetime.now().weekday() != POLL_WEEKDAY:
            return

        await context.bot.send_poll(
            chat_id=CHAT_ID,
            question="📊 توقعك لسعر الذهب هذا الأسبوع؟",
            options=["🔺 سيرتفع", "🔻 سينخفض", "➖ سيبقى مستقرًا"],
            is_anonymous=True,
        )
        logger.info("تم نشر استطلاع الرأي الأسبوعي بنجاح")
    except Exception as e:
        logger.exception("فشل نشر استطلاع الرأي: %s", e)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /price - يرسل البطاقة فورًا لمن طلبها"""
    try:
        card_path = generate_daily_card()
        caption = _build_change_caption()
        with open(card_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=caption)
    except Exception as e:
        logger.exception("فشل تنفيذ أمر /price: %s", e)
        await update.message.reply_text("⚠️ حدث خطأ أثناء جلب الأسعار، حاول مرة أخرى بعد قليل.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ أهلاً بك! 👋\n\n"
        "استخدم الأمر /price لمعرفة أسعار الصرف والذهب والفضة الحالية.\n\n"
        "كما أقوم بنشر تحديثات يومية وأسبوعية تلقائيًا في القناة."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))

    job_queue = app.job_queue

    job_queue.run_daily(send_morning_update, time=MORNING_UTC, name="morning_update")
    job_queue.run_daily(send_evening_update, time=EVENING_UTC, name="evening_update")
    job_queue.run_daily(send_weekly_poll, time=MORNING_UTC, name="weekly_poll")

    logger.info("🟡 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
