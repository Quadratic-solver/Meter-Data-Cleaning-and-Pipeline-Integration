"""
Checklot_data.db after a migration run.

Bash:
    python 02_check_database.py
"""

import sqlite3
import os

DB_PATH = "database/lot_data.db"


def main():
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH} -- it was never created.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Checks which tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables found: {tables}\n")

    if "lot_metadata" not in tables or "testing_details" not in tables:
        print("Expected tables are missing -- migration may not have run at all.")
        conn.close()
        return

    # 2. Check how many files were migrated (rows in lot_metadata)
    cur.execute("SELECT COUNT(*) FROM lot_metadata")
    file_count = cur.fetchone()[0]
    print(f"Files migrated (rows in lot_metadata): {file_count} / 65 expected")

    # 3. Check which files are present?
    cur.execute("SELECT lot_file FROM lot_metadata ORDER BY lot_file")
    migrated_files = [row[0] for row in cur.fetchall()]
    print("\nFiles present in database:")
    for f in migrated_files:
        print(f"  - {f}")

    # 4. Compare against what's actually in data/lots/ to find any gaps
    import glob
    expected_files = sorted(
        os.path.basename(p) for p in
        glob.glob("data/lots/*.csv") + glob.glob("data/lots/*.xlsx") + glob.glob("data/lots/*.xls")
    )
    missing = [f for f in expected_files if f not in migrated_files]
    if missing:
        print(f"\nMISSING from database ({len(missing)} files) -- migration likely crashed before reaching these:")
        for f in missing:
            print(f"  - {f}")
    else:
        print("\nAll files in data/lots/ are present in the database. Nothing missing.")

    # 5. Count total rows in testing_details and distinct lot files with rows
    cur.execute("SELECT COUNT(*) FROM testing_details")
    total_rows = cur.fetchone()[0]
    print(f"\nTotal testing rows across all files: {total_rows}")

    cur.execute("SELECT COUNT(DISTINCT lot_file) FROM testing_details")
    distinct_files_with_rows = cur.fetchone()[0]
    print(f"Distinct files with row data: {distinct_files_with_rows}")

    print("\nSample of 5 rows from testing_details:")
    cur.execute("SELECT lot_file, row_index, serial, serial_normalized, fl, ll FROM testing_details LIMIT 5")
    for row in cur.fetchall():
        print(f"  {row}")

    print("\nSample of 3 rows from lot_metadata:")
    cur.execute("SELECT lot_file, brand, type, wire, header_row_idx, data_start_idx FROM lot_metadata LIMIT 3")
    for row in cur.fetchall():
        print(f"  {row}")

    conn.close()


if __name__ == "__main__":
    main()
