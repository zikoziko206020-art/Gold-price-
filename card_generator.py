"""إنشاء بطاقة صورة شاملة (صرف + ذهب + فضة) بديلة عن الرسائل النصية"""
from PIL import Image, ImageDraw, ImageFont
from arabic_text import prepare_arabic
from fonts import ensure_fonts
from datetime import datetime

from gold_price import get_gold_price_usd_per_ounce
from silver_price import get_silver_price_usd_per_ounce, get_silver_price_per_gram
from exchange_rate import get_usd_yer_sanaa, get_usd_yer_aden, get_sar_yer_sanaa, get_sar_yer_aden
from config import TROY_OUNCE_IN_GRAMS

CARD_WIDTH = 1080

# ألوان التصميم
BG_COLOR = (20, 22, 30)           # خلفية داكنة أنيقة
HEADER_COLOR = (212, 175, 55)     # ذهبي للعناوين
TEXT_COLOR = (235, 235, 235)      # أبيض تقريبًا للنصوص
SUBTEXT_COLOR = (160, 160, 170)   # رمادي للنصوص الثانوية
DIVIDER_COLOR = (55, 58, 68)      # لون خط الفاصل
SANAA_COLOR = (100, 181, 246)     # أزرق لصنعاء
ADEN_COLOR = (255, 183, 77)       # برتقالي لعدن
CARD_PADDING = 50


def _text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _draw_ar(draw, xy, text, font, fill, align_right=True):
    """يرسم نصًا عربيًا محاذى لليمين (لأن العربية RTL) عند نقطة x معينة كحد أيمن"""
    prepared = prepare_arabic(text)
    x, y = xy
    if align_right:
        w = _text_w(draw, prepared, font)
        x = x - w
    draw.text((x, y), prepared, font=font, fill=fill)
    return y


def generate_daily_card() -> str:
    """
    يبني بطاقة شاملة (صرف + ذهب + فضة) ويحفظها كصورة PNG
    يرجع مسار الصورة الناتجة
    """
    regular_path, bold_path = ensure_fonts()

    font_title = ImageFont.truetype(bold_path, 42)
    font_section = ImageFont.truetype(bold_path, 32)
    font_label = ImageFont.truetype(regular_path, 26)
    font_value = ImageFont.truetype(bold_path, 26)
    font_small = ImageFont.truetype(regular_path, 20)

    # جلب كل البيانات مسبقًا
    usd_sanaa = get_usd_yer_sanaa()
    usd_aden = get_usd_yer_aden()
    sar_sanaa = get_sar_yer_sanaa()
    sar_aden = get_sar_yer_aden()

    ounce_gold = get_gold_price_usd_per_ounce()
    gram24 = ounce_gold / TROY_OUNCE_IN_GRAMS
    karats_usd = {
        "24": gram24,
        "22": gram24 * 22 / 24,
        "21": gram24 * 21 / 24,
        "18": gram24 * 18 / 24,
    }
    karats_yer_sanaa = {k: v * usd_sanaa["sell"] for k, v in karats_usd.items()}
    karats_yer_aden = {k: v * usd_aden["sell"] for k, v in karats_usd.items()}

    ounce_silver = get_silver_price_usd_per_ounce()
    gram_silver_usd = get_silver_price_per_gram()
    gram_silver_yer_sanaa = gram_silver_usd * usd_sanaa["sell"]
    gram_silver_yer_aden = gram_silver_usd * usd_aden["sell"]

    # تقدير ارتفاع الصورة مسبقًا (تقريبي، سنبنيها بارتفاع كبير كافٍ ثم نقصها)
    est_height = 2600
    img = Image.new("RGB", (CARD_WIDTH, est_height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    right_edge = CARD_WIDTH - CARD_PADDING
    left_edge = CARD_PADDING
    y = CARD_PADDING

    # ===== العنوان =====
    _draw_ar(draw, (right_edge, y), "أسعار الذهب والفضة اليوم", font_title, HEADER_COLOR)
    y += 55
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    _draw_ar(draw, (right_edge, y), f"{date_str}  -  {time_str}", font_small, SUBTEXT_COLOR)
    y += 50
    draw.line([(left_edge, y), (right_edge, y)], fill=DIVIDER_COLOR, width=2)
    y += 35

    # ===== قسم الصرف =====
    _draw_ar(draw, (right_edge, y), "💵 سعر الصرف", font_section, HEADER_COLOR)
    y += 50

    def draw_currency_row(label, data, color):
        nonlocal y
        _draw_ar(draw, (right_edge, y), label, font_label, color)
        val_text = f"شراء {data['buy']:,.0f}  |  بيع {data['sell']:,.0f}"
        val_prepared = prepare_arabic(val_text)
        draw.text((left_edge, y), val_prepared, font=font_value, fill=TEXT_COLOR)
        y += 42

    _draw_ar(draw, (right_edge, y), "الدولار الأمريكي", font_label, SUBTEXT_COLOR)
    y += 38
    draw_currency_row("صنعاء", usd_sanaa, SANAA_COLOR)
    draw_currency_row("عدن", usd_aden, ADEN_COLOR)
    y += 15

    _draw_ar(draw, (right_edge, y), "الريال السعودي", font_label, SUBTEXT_COLOR)
    y += 38
    draw_currency_row("صنعاء", sar_sanaa, SANAA_COLOR)
    draw_currency_row("عدن", sar_aden, ADEN_COLOR)
    y += 25

    draw.line([(left_edge, y), (right_edge, y)], fill=DIVIDER_COLOR, width=2)
    y += 35

    # ===== قسم الذهب =====
    _draw_ar(draw, (right_edge, y), "🟡 أسعار الذهب", font_section, HEADER_COLOR)
    y += 50

    _draw_ar(draw, (right_edge, y), f"الأونصة العالمية: {ounce_gold:,.2f} $", font_label, TEXT_COLOR)
    y += 45

    def draw_karat_table(title, karats_dict, unit, color):
        nonlocal y
        _draw_ar(draw, (right_edge, y), title, font_label, color)
        y += 38
        for k, v in karats_dict.items():
            row_text = f"عيار {k}"
            _draw_ar(draw, (right_edge - 20, y), row_text, font_small, SUBTEXT_COLOR)
            val_text = f"{v:,.2f} {unit}" if unit == "$" else f"{v:,.0f} {unit}"
            val_prepared = prepare_arabic(val_text)
            draw.text((left_edge, y), val_prepared, font=font_value, fill=TEXT_COLOR)
            y += 34
        y += 10

    draw_karat_table("بالدولار", karats_usd, "$", SUBTEXT_COLOR)
    draw_karat_table("بالريال - صنعاء", karats_yer_sanaa, "ريال", SANAA_COLOR)
    draw_karat_table("بالريال - عدن", karats_yer_aden, "ريال", ADEN_COLOR)

    draw.line([(left_edge, y), (right_edge, y)], fill=DIVIDER_COLOR, width=2)
    y += 35

    # ===== قسم الفضة =====
    _draw_ar(draw, (right_edge, y), "⚪ أسعار الفضة", font_section, HEADER_COLOR)
    y += 50

    _draw_ar(draw, (right_edge, y), f"الأونصة العالمية: {ounce_silver:,.2f} $", font_label, TEXT_COLOR)
    y += 42
    _draw_ar(draw, (right_edge, y), f"الجرام بالدولار: {gram_silver_usd:,.2f} $", font_label, TEXT_COLOR)
    y += 42

    _draw_ar(draw, (right_edge, y), "الجرام بالريال", font_label, SUBTEXT_COLOR)
    y += 38
    _draw_ar(draw, (right_edge - 20, y), "صنعاء", font_small, SANAA_COLOR)
    val_prepared = prepare_arabic(f"{gram_silver_yer_sanaa:,.0f} ريال")
    draw.text((left_edge, y), val_prepared, font=font_value, fill=TEXT_COLOR)
    y += 34
    _draw_ar(draw, (right_edge - 20, y), "عدن", font_small, ADEN_COLOR)
    val_prepared = prepare_arabic(f"{gram_silver_yer_aden:,.0f} ريال")
    draw.text((left_edge, y), val_prepared, font=font_value, fill=TEXT_COLOR)
    y += 50

    draw.line([(left_edge, y), (right_edge, y)], fill=DIVIDER_COLOR, width=2)
    y += 30

    # ===== التذييل =====
    _draw_ar(draw, (right_edge, y), "قناتنا: t.me/priceGoldyemen", font_small, SUBTEXT_COLOR)
    y += 40

    # قص الصورة للارتفاع الفعلي المستخدم
    final_img = img.crop((0, 0, CARD_WIDTH, y + CARD_PADDING))

    output_path = "/tmp/daily_card.png"
    final_img.save(output_path)
    return output_path


if __name__ == "__main__":
    path = generate_daily_card()
    print("تم إنشاء البطاقة في:", path)
