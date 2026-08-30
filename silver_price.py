"""جلب سعر الفضة العالمي من gold-api.com (نفس المصدر المستخدم للذهب، مجاني بدون مفتاح)"""
import requests
from config import TROY_OUNCE_IN_GRAMS

SILVER_API_URL = "https://api.gold-api.com/price/XAG"


def get_silver_price_usd_per_ounce() -> float:
    resp = requests.get(SILVER_API_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return float(data["price"])


def get_silver_price_per_gram() -> float:
    """الفضة عادة تُباع بعيار واحد (999 أو قريب منه)، فلا حاجة لأعيرة متعددة كالذهب"""
    price_per_ounce = get_silver_price_usd_per_ounce()
    return price_per_ounce / TROY_OUNCE_IN_GRAMS


if __name__ == "__main__":
    ounce = get_silver_price_usd_per_ounce()
    gram = get_silver_price_per_gram()
    print(f"سعر أونصة الفضة: {ounce:.2f} USD")
    print(f"سعر جرام الفضة: {gram:.2f} USD")
