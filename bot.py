"""بوت تيليجرام لأسعار الذهب مقابل الدولار والريال اليمني"""
import logging
import os
from datetime import time as dt_time

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import BOT_TOKEN, CHAT_ID
from message_builder import build_exchange_message, build_gold_message
from chart_generator import generate_weekly_chart

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MORNING_UTC = dt_time(hour=6, minute=0)
EVENING_UTC = dt_time(hour=14, minute=0)
POLL_WEEKDAY = 5  # السبت


async def send_exchange_update(context: ContextTypes.DEFAULT_TYPE):
    """رسالة الصرف والفضة معًا - مرة واحدة يوميًا صباحًا"""
    try:
        exchange_text = build_exchange_message()
        await context.bot.send_message(
            chat_id=CHAT_ID, text=exchange_text, parse_mode="Markdown", disable_web_page_preview=True
        )
        logger.info("تم نشر رسالة الصرف والفضة بنجاح")
    except Exception as e:
        logger.exception("فشل نشر رسالة الصرف والفضة: %s", e)


async def send_gold_update(context: ContextTypes.DEFAULT_TYPE):
    """رسالة الذهب مع مؤشر التغيّر لكل عيار - مرتين يوميًا صباحًا ومساءً"""
    try:
        gold_text = build_gold_message()
        await context.bot.send_message(
            chat_id=CHAT_ID, text=gold_text, parse_mode="Markdown", disable_web_page_preview=True
        )
        logger.info("تم نشر رسالة الذهب بنجاح")
    except Exception as e:
        logger.exception("فشل نشر رسالة الذهب: %s", e)


async def send_weekend_chart_and_poll(context: ContextTypes.DEFAULT_TYPE):
    """مساء السبت فقط: الرسم البياني الأسبوعي + استطلاع الرأي معًا"""
    try:
        import datetime as dt
        if dt.datetime.now().weekday() != POLL_WEEKDAY:
            return

        chart_path = generate_weekly_chart()
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=photo,
                    caption="📈 الرسم البياني الأسبوعي لسعر جرام الذهب عيار 21 (صنعاء)",
                )
            logger.info("تم نشر الرسم البياني الأسبوعي بنجاح")

        await context.bot.send_poll(
            chat_id=CHAT_ID,
            question="📊 توقعك لسعر الذهب الأسبوع القادم؟",
            options=["🔺 سيرتفع", "🔻 سينخفض", "➖ سيبقى مستقرًا"],
            is_anonymous=True,
        )
        logger.info("تم نشر استطلاع الرأي الأسبوعي بنجاح")
    except Exception as e:
        logger.exception("فشل نشر الرسم البياني أو الاستطلاع: %s", e)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        exchange_text = build_exchange_message()
        await update.message.reply_text(exchange_text, parse_mode="Markdown", disable_web_page_preview=True)

        gold_text = build_gold_message()
        await update.message.reply_text(gold_text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.exception("فشل تنفيذ أمر /price: %s", e)
        await update.message.reply_text("⚠️ حدث خطأ أثناء جلب الأسعار، حاول مرة أخرى بعد قليل.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ أهلاً بك! 👋\n\n"
        "استخدم الأمر /price لمعرفة أسعار الصرف والفضة والذهب الحالية.\n\n"
        "كما أقوم بنشر تحديثات يومية، ورسمًا بيانيًا واستطلاع رأي أسبوعي مساء كل سبت."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))

    job_queue = app.job_queue

    job_queue.run_daily(send_exchange_update, time=MORNING_UTC, name="morning_exchange")
    job_queue.run_daily(send_gold_update, time=MORNING_UTC, name="morning_gold")
    job_queue.run_daily(send_gold_update, time=EVENING_UTC, name="evening_gold")
    job_queue.run_daily(send_weekend_chart_and_poll, time=EVENING_UTC, name="weekend_chart_poll")

    logger.info("🟡 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
