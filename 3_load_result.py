"""
Step 3: Load master_final_clean.csv into the database, then update
FL/LL across all lot data using ONE SQL query.

Bash:
    python 03_load_master_and_update.py
"""

import csv
import os
import re
import sqlite3
import time

MASTER_PATH = "output/master_final_clean.csv"
DB_PATH = "database/lot_data.db"

# Normalizes serial values by removing spaces and making them uppercase.
def normalize_serial(val):
    if val is None:
        return ""
    text = str(val).strip()
    if text.lower() == "nan":
        return ""
    return re.sub(r"\s+", "", text).upper()

# Scans the master_final_clean.csv file and loads it into a 'master' table in the database.
def load_master(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS master (
            meter_serial TEXT,
            meter_serial_normalized TEXT PRIMARY KEY,
            source_file TEXT,
            fl TEXT,
            ll TEXT,
            date_tested TEXT
        )
    """)
    cur.execute("DELETE FROM master")  # safe re-runs, no duplicates

    rows_to_insert = []
    with open(MASTER_PATH, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            serial_norm = normalize_serial(row.get("meter_serial"))
            if not serial_norm:
                continue
            rows_to_insert.append((
                row.get("meter_serial"),
                serial_norm,
                row.get("source_file"),
                row.get("FL"),
                row.get("LL"),
                row.get("date_tested"),
            ))

    cur.executemany(
        """INSERT OR REPLACE INTO master
           (meter_serial, meter_serial_normalized, source_file, fl, ll, date_tested)
           VALUES (?,?,?,?,?,?)""",
        rows_to_insert,
    )
    conn.commit()
    print(f"Loaded {len(rows_to_insert)} rows from {MASTER_PATH} into 'master' table")


def update_testing_details(conn):
    """Update all matching lot rows in the database using the cleaned master data."""
    cur = conn.cursor()

    # counts how many rows in testing_details have a match in 'master' table
    cur.execute("""
        SELECT COUNT(*) FROM testing_details
        WHERE serial_normalized IN (SELECT meter_serial_normalized FROM master)
    """)
    matchable = cur.fetchone()[0]

    cur.execute("""
        UPDATE testing_details
        SET fl = (
                SELECT fl FROM master
                WHERE master.meter_serial_normalized = testing_details.serial_normalized
            ),
            ll = (
                SELECT ll FROM master
                WHERE master.meter_serial_normalized = testing_details.serial_normalized
            )
        WHERE serial_normalized IN (SELECT meter_serial_normalized FROM master)
    """)
    conn.commit()

    return matchable, cur.rowcount


def main():
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH} -- run 01_build_database.py first.")
        return
    if not os.path.exists(MASTER_PATH):
        print(f"Master file not found at {MASTER_PATH}")
        return

    start_time = time.time()

    conn = sqlite3.connect(DB_PATH)

    load_master(conn)

    matchable, rows_updated = update_testing_details(conn)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM testing_details")
    total_rows = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM testing_details
        WHERE serial_normalized NOT IN (SELECT meter_serial_normalized FROM master)
    """)
    no_match = cur.fetchone()[0]

    conn.close()

    elapsed = time.time() - start_time

    print("\n=== SUMMARY ===")
    print(f"Total testing rows in database: {total_rows}")
    print(f"Rows matched to master list: {matchable}")
    print(f"Rows actually updated: {rows_updated}")
    print(f"Rows with no match in master: {no_match}")
    print(f"\nTotal time taken: {elapsed:.2f} seconds")
    print("(compare this to the ~30 minutes the old file-by-file update took)")


if __name__ == "__main__":
    main()