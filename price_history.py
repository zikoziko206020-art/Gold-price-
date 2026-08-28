"""إدارة قاعدة بيانات سجل الأسعار التاريخي (SQLite على Railway Volume)"""
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "/data/prices.db"


def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            date TEXT PRIMARY KEY,
            gram21_yer_sanaa REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_today_price(gram21_yer_sanaa: float):
    """يحفظ سعر اليوم (يستبدل القيمة إذا كانت موجودة أصلاً لنفس اليوم)"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = _get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO price_history (date, gram21_yer_sanaa) VALUES (?, ?)",
        (today, gram21_yer_sanaa),
    )
    conn.commit()
    conn.close()


def get_yesterday_price():
    """يرجع سعر آخر يوم مسجّل قبل اليوم، أو None إن لم يوجد"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = _get_connection()
    row = conn.execute(
        "SELECT date, gram21_yer_sanaa FROM price_history WHERE date < ? ORDER BY date DESC LIMIT 1",
        (today,),
    ).fetchone()
    conn.close()
    if row:
        return {"date": row[0], "price": row[1]}
    return None


def get_last_n_days(n: int = 7):
    """يرجع قائمة [(date, price), ...] لآخر n يوم، مرتبة من الأقدم للأحدث"""
    cutoff = (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")
    conn = _get_connection()
    rows = conn.execute(
        "SELECT date, gram21_yer_sanaa FROM price_history WHERE date >= ? ORDER BY date ASC",
        (cutoff,),
    ).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    save_today_price(60900)
    print("سعر أمس:", get_yesterday_price())
    print("آخر 7 أيام:", get_last_n_days(7))
