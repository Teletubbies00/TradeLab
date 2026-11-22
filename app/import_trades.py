import csv
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.database import get_connection, initialize_database


REQUIRED_COLUMNS = [
    "symbol", "side", "entry_time", "exit_time",
    "quantity", "entry_price", "exit_price", "net_pnl"
]

ALL_COLUMNS = REQUIRED_COLUMNS + ["notes"]


def validate_row(row, line_number):
    try:
        symbol = (row["symbol"] or "").strip().upper()
        side = (row["side"] or "").strip().upper()

        if not symbol:
            raise ValueError("商品代碼不能為空")

        if side not in ("LONG", "SHORT"):
            raise ValueError("side 必須是 LONG 或 SHORT")

        entry_time = datetime.fromisoformat(row["entry_time"].strip())
        exit_time = datetime.fromisoformat(row["exit_time"].strip())

        if entry_time >= exit_time:
            raise ValueError("出場時間必須晚於進場時間")

        quantity_text = row["quantity"].strip()
        quantity = int(quantity_text)

        if str(quantity) != quantity_text or quantity <= 0:
            raise ValueError("quantity 必須是正整數")

        values = {}

        for column in ("entry_price", "exit_price", "net_pnl"):
            value = Decimal(row[column].strip())

            if not value.is_finite():
                raise ValueError(f"{column} 不能是 NaN 或 Infinity")

            values[column] = value

        if values["entry_price"] <= 0 or values["exit_price"] <= 0:
            raise ValueError("進出場價格必須大於 0")

        return {
            "symbol": symbol,
            "side": side,
            "entry_time": entry_time.isoformat(sep=" "),
            "exit_time": exit_time.isoformat(sep=" "),
            "quantity": quantity,
            "entry_price": float(values["entry_price"]),
            "exit_price": float(values["exit_price"]),
            "net_pnl": float(values["net_pnl"]),
            "notes": (row.get("notes") or "").strip()
        }

    except (ValueError, TypeError, AttributeError, InvalidOperation) as error:
        raise ValueError(f"CSV 第 {line_number} 行：{error}") from error


def trade_fingerprint(trade):
    # 先使用標準化後的欄位辨識完全相同的交易列
    # 不包含 notes，避免只修改備註就重複建立交易
    fields = [
        trade["symbol"],
        trade["side"],
        trade["entry_time"],
        trade["exit_time"],
        str(trade["quantity"]),
        str(trade["entry_price"]),
        str(trade["exit_price"]),
        str(trade["net_pnl"])
    ]

    content = json.dumps(fields, ensure_ascii=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def import_csv(csv_path):
    path = Path(csv_path)

    if not path.is_file():
        raise FileNotFoundError(f"找不到 CSV 檔案：{path}")

    trades = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV 沒有標題列")

        missing = [
            column for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing:
            raise ValueError(f"CSV 缺少必要欄位：{missing}")

        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"CSV 第 {line_number} 行：欄位數量過多")

            trade = validate_row(row, line_number)
            trades.append(trade)

    if not trades:
        raise ValueError("CSV 沒有交易資料")

    initialize_database()

    inserted = 0
    skipped = 0

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS trade_import_keys (
                fingerprint TEXT PRIMARY KEY,
                trade_id INTEGER NOT NULL UNIQUE,
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        """)

        for trade in trades:
            fingerprint = trade_fingerprint(trade)

            existing = connection.execute(
                "SELECT 1 FROM trade_import_keys WHERE fingerprint = ?",
                (fingerprint,)
            ).fetchone()

            if existing:
                skipped += 1
                continue

            cursor = connection.execute("""
                INSERT INTO trades (
                    symbol, side, entry_time, exit_time,
                    quantity, entry_price, exit_price, net_pnl, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(trade[column] for column in ALL_COLUMNS))

            connection.execute("""
                INSERT INTO trade_import_keys (fingerprint, trade_id)
                VALUES (?, ?)
            """, (fingerprint, cursor.lastrowid))

            inserted += 1

    return {
        "total_rows": len(trades),
        "inserted": inserted,
        "skipped_duplicates": skipped
    }


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("使用方式：python -m app.import_trades <CSV路徑>")

        result = import_csv(sys.argv[1])
        print("匯入結果：")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except (ValueError, FileNotFoundError, sqlite3.Error) as error:
        print(f"匯入失敗：{error}")
        sys.exit(1)
