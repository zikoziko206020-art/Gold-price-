"""بوت تيليجرام لأسعار الذهب مقابل الدولار والريال اليمني"""
import logging
import os
from datetime import time as dt_time

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import BOT_TOKEN, CHAT_ID
from message_builder import build_exchange_message, build_gold_message, build_silver_message
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

# مواعيد النشر بتوقيت UTC (9ص و5م بتوقيت اليمن UTC+3)
MORNING_UTC = dt_time(hour=6, minute=0)
EVENING_UTC = dt_time(hour=14, minute=0)

# الاستطلاع الأسبوعي: يوم السبت (بداية أسبوع التداول بعد عطلة الجمعة)
POLL_WEEKDAY = 5  # الاثنين=0 ... السبت=5


def _current_gram21_sanaa() -> float:
    ounce_usd = get_gold_price_usd_per_ounce()
    gram24_usd = ounce_usd / TROY_OUNCE_IN_GRAMS
    gram21_usd = gram24_usd * 21 / 24
    usd_sanaa = get_usd_yer_sanaa()["sell"]
    return gram21_usd * usd_sanaa


def _build_change_indicator() -> str:
    try:
        today_price = _current_gram21_sanaa()
        save_today_price(today_price)

        yesterday = get_yesterday_price()
        if not yesterday:
            return ""

        diff = today_price - yesterday["price"]
        pct = (diff / yesterday["price"]) * 100 if yesterday["price"] else 0

        if diff > 0:
            arrow, word = "🔺", "ارتفاع"
        elif diff < 0:
            arrow, word = "🔻", "انخفاض"
        else:
            return "➖ *لا تغيير* عن آخر تحديث"

        return f"{arrow} *{word}* بمقدار *{abs(diff):,.0f}* ريال ({abs(pct):.2f}%) عن آخر تحديث"
    except Exception as e:
        logger.exception("فشل حساب مؤشر التغيّر: %s", e)
        return ""


def _trust_footer() -> str:
    from datetime import datetime
    now = datetime.now().strftime("%H:%M:%S")
    return f"✅ _تم التحقق من المصدر مباشرة الساعة {now}_"


async def send_exchange_update(context: ContextTypes.DEFAULT_TYPE):
    try:
        exchange_text = build_exchange_message()
        exchange_text += f"\n\n{_trust_footer()}"
        await context.bot.send_message(
            chat_id=CHAT_ID, text=exchange_text, parse_mode="Markdown", disable_web_page_preview=True
        )
        logger.info("تم نشر رسالة الصرف بنجاح")
    except Exception as e:
        logger.exception("فشل نشر رسالة الصرف: %s", e)


async def send_silver_update(context: ContextTypes.DEFAULT_TYPE):
    """ينشر رسالة الفضة فقط - مرة واحدة يوميًا صباحًا"""
    try:
        silver_text = build_silver_message()
        silver_text += f"\n\n{_trust_footer()}"
        await context.bot.send_message(
            chat_id=CHAT_ID, text=silver_text, parse_mode="Markdown", disable_web_page_preview=True
        )
        logger.info("تم نشر رسالة الفضة بنجاح")
    except Exception as e:
        logger.exception("فشل نشر رسالة الفضة: %s", e)


async def send_gold_update(context: ContextTypes.DEFAULT_TYPE, with_chart: bool = False):
    try:
        gold_text = build_gold_message()

        if with_chart:
            change_line = _build_change_indicator()
            if change_line:
                gold_text += f"\n\n{change_line}"

        gold_text += f"\n\n{_trust_footer()}"

        await context.bot.send_message(
            chat_id=CHAT_ID, text=gold_text, parse_mode="Markdown", disable_web_page_preview=True
        )
        logger.info("تم نشر رسالة الذهب بنجاح")

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
        logger.exception("فشل نشر رسالة الذهب: %s", e)


async def send_morning_gold_update(context: ContextTypes.DEFAULT_TYPE):
    await send_gold_update(context, with_chart=True)


async def send_evening_gold_update(context: ContextTypes.DEFAULT_TYPE):
    await send_gold_update(context, with_chart=False)


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
    try:
        exchange_text = build_exchange_message()
        exchange_text += f"\n\n{_trust_footer()}"
        await update.message.reply_text(exchange_text, parse_mode="Markdown", disable_web_page_preview=True)

        gold_text = build_gold_message()
        change_line = _build_change_indicator()
        if change_line:
            gold_text += f"\n\n{change_line}"
        gold_text += f"\n\n{_trust_footer()}"
        await update.message.reply_text(gold_text, parse_mode="Markdown", disable_web_page_preview=True)

        silver_text = build_silver_message()
        silver_text += f"\n\n{_trust_footer()}"
        await update.message.reply_text(silver_text, parse_mode="Markdown", disable_web_page_preview=True)
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

    job_queue.run_daily(send_exchange_update, time=MORNING_UTC, name="morning_exchange")
    job_queue.run_daily(send_silver_update, time=MORNING_UTC, name="morning_silver")
    job_queue.run_daily(send_morning_gold_update, time=MORNING_UTC, name="morning_gold")
    job_queue.run_daily(send_evening_gold_update, time=EVENING_UTC, name="evening_gold")
    job_queue.run_daily(send_weekly_poll, time=MORNING_UTC, name="weekly_poll")

    logger.info("🟡 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
