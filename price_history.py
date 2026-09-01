"""إدارة قاعدة بيانات سجل الأسعار التاريخي (SQLite على Railway Volume)
يحفظ كل الأعيرة الأربعة (24، 22، 21، 18) لكل من صنعاء وعدن يوميًا
"""
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "/data/prices.db"

KARATS = ["24", "22", "21", "18"]

EXPECTED_COLUMNS = {"date"}
for k in KARATS:
    EXPECTED_COLUMNS.add(f"gram{k}_sanaa")
    EXPECTED_COLUMNS.add(f"gram{k}_aden")


def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # تحقق إن كان الجدول موجودًا بهيكل قديم مختلف، وإن كان كذلك احذفه لإعادة إنشائه بالهيكل الصحيح
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='price_history'"
    ).fetchone()

    if existing:
        current_columns = {row[1] for row in conn.execute("PRAGMA table_info(price_history)")}
        if current_columns != EXPECTED_COLUMNS:
            conn.execute("DROP TABLE price_history")
            conn.commit()

    columns = ", ".join([f"gram{k}_sanaa REAL, gram{k}_aden REAL" for k in KARATS])
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS price_history (
            date TEXT PRIMARY KEY,
            {columns}
        )
    """)
    conn.commit()
    return conn


def save_today_prices(karats_yer_sanaa: dict, karats_yer_aden: dict):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = _get_connection()

    columns = ["date"]
    values = [today]
    for k in KARATS:
        columns.append(f"gram{k}_sanaa")
        columns.append(f"gram{k}_aden")
        values.append(karats_yer_sanaa.get(k))
        values.append(karats_yer_aden.get(k))

    placeholders = ", ".join(["?"] * len(values))
    columns_str = ", ".join(columns)
    conn.execute(
        f"INSERT OR REPLACE INTO price_history ({columns_str}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    conn.close()


def get_yesterday_prices():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM price_history WHERE date < ? ORDER BY date DESC LIMIT 1",
        (today,),
    ).fetchone()
    columns = [desc[0] for desc in conn.execute("SELECT * FROM price_history LIMIT 0").description]
    conn.close()

    if not row:
        return None

    row_dict = dict(zip(columns, row))
    sanaa = {k: row_dict.get(f"gram{k}_sanaa") for k in KARATS}
    aden = {k: row_dict.get(f"gram{k}_aden") for k in KARATS}
    return {"date": row_dict["date"], "sanaa": sanaa, "aden": aden}


def get_last_n_days(n: int = 7):
    cutoff = (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")
    conn = _get_connection()
    rows = conn.execute(
        "SELECT date, gram21_sanaa FROM price_history WHERE date >= ? ORDER BY date ASC",
        (cutoff,),
    ).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    sample_sanaa = {"24": 69554, "22": 63758, "21": 60860, "18": 52166}
    sample_aden = {"24": 203332, "22": 186388, "21": 177916, "18": 152499}
    save_today_prices(sample_sanaa, sample_aden)
    print("أمس:", get_yesterday_prices())
    print("آخر 7 أيام:", get_last_n_days(7))
