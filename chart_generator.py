"""إنشاء رسم بياني أسبوعي لسعر جرام الذهب عيار 21 بالريال اليمني (صنعاء)
اللون يعكس اتجاه الأسبوع: أخضر = ارتفاع، أحمر = انخفاض، ذهبي = مستقر
"""
import matplotlib
matplotlib.use("Agg")  # للعمل بدون واجهة رسومية (مطلوب على السيرفر)
import matplotlib.pyplot as plt
from price_history import get_last_n_days

CHART_PATH = "/tmp/weekly_chart.png"

COLOR_UP = "#2ECC71"      # أخضر - ارتفاع
COLOR_DOWN = "#E74C3C"    # أحمر - انخفاض
COLOR_FLAT = "#D4AF37"    # ذهبي - مستقر


def _pick_color(prices: list) -> tuple:
    """يحدد اللون بناءً على الفرق بين أول وآخر نقطة، يرجع (لون, رمز اتجاه)"""
    if len(prices) < 2:
        return COLOR_FLAT, "➖"

    diff_pct = ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] else 0

    if diff_pct > 0.3:  # ارتفاع ملموس (أكثر من 0.3%)
        return COLOR_UP, "📈"
    elif diff_pct < -0.3:  # انخفاض ملموس
        return COLOR_DOWN, "📉"
    else:
        return COLOR_FLAT, "➖"


def generate_weekly_chart() -> str:
    """
    ينشئ صورة رسم بياني لآخر 7 أيام بلون يعكس اتجاه الأسبوع
    يرجع مسار الصورة الناتجة، أو None إذا لم تتوفر بيانات كافية
    """
    data = get_last_n_days(7)
    if len(data) < 2:
        return None  # لا فائدة من رسم بنقطة واحدة أو أقل

    dates = [row[0][5:] for row in data]  # نأخذ فقط MM-DD لتقصير التسمية
    prices = [row[1] for row in data]

    color, _ = _pick_color(prices)

    plt.figure(figsize=(8, 4.5), dpi=150)
    plt.plot(dates, prices, marker="o", linewidth=2.5, color=color)
    plt.fill_between(dates, prices, min(prices) * 0.995, alpha=0.15, color=color)

    plt.title("سعر جرام الذهب عيار 21 - صنعاء (آخر 7 أيام)", fontsize=13)
    plt.ylabel("السعر (ريال يمني)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(CHART_PATH)
    plt.close()

    return CHART_PATH


def get_weekly_trend_emoji() -> str:
    """يرجع رمز الاتجاه الأسبوعي فقط (للاستخدام في نص الرسالة دون الحاجة لرسم)"""
    data = get_last_n_days(7)
    prices = [row[1] for row in data]
    _, emoji = _pick_color(prices)
    return emoji


if __name__ == "__main__":
    path = generate_weekly_chart()
    print("مسار الصورة:", path)
    print("اتجاه الأسبوع:", get_weekly_trend_emoji())
