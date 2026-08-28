"""إنشاء رسم بياني أسبوعي لسعر جرام الذهب عيار 21 بالريال اليمني (صنعاء)"""
import matplotlib
matplotlib.use("Agg")  # للعمل بدون واجهة رسومية (مطلوب على السيرفر)
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from price_history import get_last_n_days

CHART_PATH = "/tmp/weekly_chart.png"


def generate_weekly_chart() -> str:
    """
    ينشئ صورة رسم بياني لآخر 7 أيام ويحفظها في CHART_PATH
    يرجع مسار الصورة الناتجة، أو None إذا لم تتوفر بيانات كافية
    """
    data = get_last_n_days(7)
    if len(data) < 2:
        return None  # لا فائدة من رسم بنقطة واحدة أو أقل

    dates = [row[0][5:] for row in data]  # نأخذ فقط MM-DD لتقصير التسمية
    prices = [row[1] for row in data]

    plt.figure(figsize=(8, 4.5), dpi=150)
    plt.plot(dates, prices, marker="o", linewidth=2, color="#D4AF37")
    plt.fill_between(dates, prices, min(prices) * 0.995, alpha=0.15, color="#D4AF37")

    plt.title("سعر جرام الذهب عيار 21 - صنعاء (آخر 7 أيام)", fontsize=13)
    plt.ylabel("السعر (ريال يمني)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(CHART_PATH)
    plt.close()

    return CHART_PATH


if __name__ == "__main__":
    path = generate_weekly_chart()
    print("مسار الصورة:", path)
