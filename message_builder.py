"""بناء نصوص رسائل التحديث: رسالة صرف+فضة منفردة، ورسالة ذهب منفردة"""
from datetime import datetime
from gold_price import get_gold_price_usd_per_ounce, get_local_gold_buy_sell
from silver_price import get_silver_price_per_gram
from exchange_rate import (
    get_usd_yer_sanaa,
    get_usd_yer_aden,
    get_sar_yer_sanaa,
    get_sar_yer_aden,
)
from config import TROY_OUNCE_IN_GRAMS
from price_history import save_today_prices, get_yesterday_prices

DIVIDER = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _row(label: str, value: str, emoji: str = "▫️") -> str:
    return f"{emoji} {label}  ┃  *{value}*"


def _buy_sell_row(label: str, data: dict, emoji: str = "▫️") -> str:
    return f"{emoji} {label}  ┃  شراء: *{_fmt(data['buy'])}*  |  بيع: *{_fmt(data['sell'])}* ريال"


def _change_badge(today_val: float, yesterday_val) -> str:
    """يبني رمزًا صغيرًا أنيقًا للتغيّر (🔺+320 / 🔻-150 / بدون شيء إن لم يوجد سعر أمس)"""
    if yesterday_val is None:
        return ""
    diff = today_val - yesterday_val
    if diff > 0:
        return f"  🔺+{diff:,.0f}"
    elif diff < 0:
        return f"  🔻{diff:,.0f}"
    else:
        return "  ➖"


def _row_with_change(label: str, value: float, today_val: float, yesterday_val, emoji: str = "▫️") -> str:
    badge = _change_badge(today_val, yesterday_val)
    return f"{emoji} {label}  ┃  *{_fmt(value)} ريال*{badge}"


def _now_strings():
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")


def build_exchange_message() -> str:
    """رسالة أسعار الصرف والفضة معًا"""
    usd_sanaa = get_usd_yer_sanaa()
    usd_aden = get_usd_yer_aden()
    sar_sanaa = get_sar_yer_sanaa()
    sar_aden = get_sar_yer_aden()

    gram_silver_usd = get_silver_price_per_gram()
    gram_silver_yer_sanaa = gram_silver_usd * usd_sanaa["sell"]
    gram_silver_yer_aden = gram_silver_usd * usd_aden["sell"]

    now_date, now_time = _now_strings()

    lines = []
    lines.append("💱⚪ *تحديث أسعار الصرف والفضة* ⚪💱")
    lines.append(DIVIDER)
    lines.append(f"📅 التاريخ: *{now_date}*      🕐 الوقت: *{now_time}*")
    lines.append(DIVIDER)
    lines.append("")
    lines.append("💵 *الدولار الأمريكي مقابل الريال اليمني*")
    lines.append(_buy_sell_row("صنعاء", usd_sanaa, "🔹"))
    lines.append(_buy_sell_row("عدن", usd_aden, "🔸"))
    lines.append("")
    lines.append(DIVIDER)
    lines.append("🇸🇦 *الريال السعودي مقابل الريال اليمني*")
    lines.append(_buy_sell_row("صنعاء", sar_sanaa, "🔹"))
    lines.append(_buy_sell_row("عدن", sar_aden, "🔸"))
    lines.append("")
    lines.append(DIVIDER)
    lines.append("⚪ *سعر جرام الفضة*")
    lines.append(_row("بالدولار", f"{gram_silver_usd:,.2f} $"))
    lines.append(_row("صنعاء", f"{_fmt(gram_silver_yer_sanaa)} ريال", "🔹"))
    lines.append(_row("عدن", f"{_fmt(gram_silver_yer_aden)} ريال", "🔸"))
    lines.append("")
    lines.append(DIVIDER)
    lines.append("🔗 قناتنا: t.me/priceGoldyemen")

    return "\n".join(lines)


def build_gold_message() -> str:
    ounce_usd = get_gold_price_usd_per_ounce()
    gram24_usd = ounce_usd / TROY_OUNCE_IN_GRAMS

    usd_sanaa = get_usd_yer_sanaa()["sell"]
    usd_aden = get_usd_yer_aden()["sell"]

    karats_usd = {
        "24": gram24_usd,
        "22": gram24_usd * 22 / 24,
        "21": gram24_usd * 21 / 24,
        "18": gram24_usd * 18 / 24,
    }
    karats_yer_sanaa = {k: v * usd_sanaa for k, v in karats_usd.items()}
    karats_yer_aden = {k: v * usd_aden for k, v in karats_usd.items()}

    # حفظ أسعار اليوم ومقارنتها بالأمس لكل عيار
    yesterday = get_yesterday_prices()
    save_today_prices(karats_yer_sanaa, karats_yer_aden)

    yesterday_sanaa = yesterday["sanaa"] if yesterday else {}
    yesterday_aden = yesterday["aden"] if yesterday else {}

    now_date, now_time = _now_strings()

    lines = []
    lines.append("🟡✨ *تحديث أسعار الذهب* ✨🟡")
    lines.append(DIVIDER)
    lines.append(f"📅 التاريخ: *{now_date}*      🕐 الوقت: *{now_time}*")
    lines.append(DIVIDER)
    lines.append("")
    lines.append("💰 *سعر الأونصة العالمي (XAU/USD)*")
    lines.append(f"┃  *{ounce_usd:,.2f} $*")
    lines.append("")
    lines.append(DIVIDER)
    lines.append("📊 *سعر جرام الذهب بالدولار*")
    for k, v in karats_usd.items():
        lines.append(_row(f"عيار {k}", f"{v:,.2f} $"))
    lines.append("")
    lines.append(DIVIDER)
    lines.append("🇾🇪 *سعر جرام الذهب بالريال اليمني — صنعاء*")
    for k, v in karats_yer_sanaa.items():
        lines.append(_row_with_change(f"عيار {k}", v, v, yesterday_sanaa.get(k), "🔹"))
    lines.append("")
    lines.append("🇾🇪 *سعر جرام الذهب بالريال اليمني — عدن*")
    for k, v in karats_yer_aden.items():
        lines.append(_row_with_change(f"عيار {k}", v, v, yesterday_aden.get(k), "🔸"))

    try:
        local = get_local_gold_buy_sell()
        lines.append("")
        lines.append(DIVIDER)
        lines.append("💎 *أسعار السوق المحلي (عيار 21 والجنيه)*")
        lines.append("")
        lines.append("🇾🇪 *صنعاء*")
        if local["sanaa"]["21"]:
            lines.append(_buy_sell_row("عيار 21", local["sanaa"]["21"], "🔹"))
        if local["sanaa"]["pound"]:
            lines.append(_buy_sell_row("الجنيه", local["sanaa"]["pound"], "🔹"))
        lines.append("")
        lines.append("🇾🇪 *عدن*")
        if local["aden"]["21"]:
            lines.append(_buy_sell_row("عيار 21", local["aden"]["21"], "🔸"))
        if local["aden"]["pound"]:
            lines.append(_buy_sell_row("الجنيه", local["aden"]["pound"], "🔸"))
    except Exception:
        pass

    lines.append("")
    lines.append(DIVIDER)
    lines.append("🔗 قناتنا: t.me/priceGoldyemen")

    return "\n".join(lines)


if __name__ == "__main__":
    print(build_exchange_message())
    print("\n\n" + "=" * 40 + "\n\n")
    print(build_gold_message())
