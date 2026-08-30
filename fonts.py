"""تحميل خط Cairo العربي تلقائيًا إن لم يكن موجودًا (يُستخدم لرسم البطاقة)"""
import os
import requests

FONT_DIR = "/tmp/fonts"
FONT_PATH = os.path.join(FONT_DIR, "Cairo-Regular.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "Cairo-Bold.ttf")

FONT_URL_REGULAR = "https://github.com/Gue3bara/Cairo/raw/7030db78cca3a7a7d94f9071b3f35dad7447ae71/fonts/ttf/Cairo-Regular.ttf"
FONT_URL_BOLD = "https://github.com/Gue3bara/Cairo/raw/7030db78cca3a7a7d94f9071b3f35dad7447ae71/fonts/ttf/Cairo-Bold.ttf"


def _download_if_missing(url: str, path: str):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)


def ensure_fonts() -> tuple:
    """يضمن وجود الخطوط محليًا، يرجع (مسار العادي, مسار الغامق)"""
    _download_if_missing(FONT_URL_REGULAR, FONT_PATH)
    _download_if_missing(FONT_URL_BOLD, FONT_BOLD_PATH)
    return FONT_PATH, FONT_BOLD_PATH


if __name__ == "__main__":
    regular, bold = ensure_fonts()
    print("الخط العادي:", regular)
    print("الخط الغامق:", bold)
