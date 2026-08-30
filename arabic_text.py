"""تحضير النص العربي ليُرسم بشكل صحيح (متصل ومن اليمين لليسار) في Pillow"""
import arabic_reshaper
from bidi.algorithm import get_display


def prepare_arabic(text: str) -> str:
    """
    يحوّل نصًا عربيًا (أو مختلطًا مع أرقام/إنجليزي) إلى صيغة جاهزة للرسم
    بشكل صحيح بصريًا داخل مكتبة Pillow
    """
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)
