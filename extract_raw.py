"""Extracts the raw data from the CSV files in the raw folder and writes them to a single master CSV file."""

import pandas as pd
import glob
import os

# ==== CONFIG ====
RAW_FOLDER = "data/raw"
OUTPUT_PATH = "output/master_serial_fl_ll.csv"

# Find the column that contains the serial number, FL, and LL values, and optionally a date column.
# Case sensitive, but ignores spaces and underscores. Returns the column names as they appear in the file.
def find_column(columns, keyword, exclude_keywords=None):
    exclude_keywords = exclude_keywords or []
    for col in columns:
        col_lower = str(col).lower().strip()
        if keyword.lower() in col_lower:
            if any(ex.lower() in col_lower for ex in exclude_keywords):
                continue
            return col
    return None

# Finds the latest date column in the file, prioritizing "date tested", then "timestamp", then "date".
def find_date_column(columns):
    for keyword in ["date tested", "timestamp", "date"]:
        col = find_column(columns, keyword)
        if col:
            return col
    return None

def process_file(file_path):
    file_name = os.path.basename(file_path)
    df = pd.read_csv(file_path, dtype=str, low_memory=False)
    columns = df.columns.tolist()

    serial_col = find_column(columns, "serial")
    fl_col = find_column(columns, "fl", exclude_keywords=["sfl"]) or find_column(columns, "fl")
    ll_col = find_column(columns, "ll", exclude_keywords=["sll"]) or find_column(columns, "ll")
    date_col = find_date_column(columns)

    # Some are using SFL/SLL instead of FL/LL, so check for those too
    sfl_col = find_column(columns, "sfl")
    sll_col = find_column(columns, "sll")

    if sfl_col:
        fl_col = sfl_col
    if sll_col:
        ll_col = sll_col

    if not serial_col or not fl_col or not ll_col:
        print(f"  SKIPPED: {file_name} -- missing columns "
              f"(serial={serial_col}, fl={fl_col}, ll={ll_col})")
        return None

    out = pd.DataFrame({
        "source_file": file_name,
        "meter_serial": df[serial_col],
        "FL": df[fl_col],
        "LL": df[ll_col],
    })

    # Subtract 100 from SFL/SLL values to convert them to FL/LL, if present. This is a known quirk of the data.
    if sfl_col:
        out["FL"] = pd.to_numeric(out["FL"], errors="coerce") - 100
    if sll_col:
        out["LL"] = pd.to_numeric(out["LL"], errors="coerce") - 100

    # parse date column -- handles "10/18/2022 13:56:24", "10/18/2022", and blanks all at once
    if date_col:
        out["date_tested"] = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        # some entries are garbage typos (e.g. "1-09-23" read as year 1) -- outside a
        # sane range, pandas can't even store them, so treat them as blank too
        out.loc[
            (out["date_tested"] < "2000-01-01") | (out["date_tested"] > "2030-12-31"),
            "date_tested"
        ] = pd.NaT
    else:
        out["date_tested"] = pd.NaT

    date_missing_count = out["date_tested"].isna().sum()
    print(f"  OK: {file_name} -- serial='{serial_col}', fl='{fl_col}', ll='{ll_col}', "
          f"date='{date_col}' -- {len(out)} rows ({date_missing_count} blank/unparsed dates)")
    return out

def main():
    csv_files = glob.glob(os.path.join(RAW_FOLDER, "*.csv"))
    print(f"Found {len(csv_files)} files\n")

    all_data = []
    for file_path in csv_files:
        try:
            result = process_file(file_path)
            if result is not None:
                all_data.append(result)
        except Exception as e:
            print(f"  FAILED: {os.path.basename(file_path)} -- {e}")

    if not all_data:
        print("\nNo data extracted. Check file formats.")
        return

    master = pd.concat(all_data, ignore_index=True)

    os.makedirs("output", exist_ok=True)
    master.to_csv(OUTPUT_PATH, index=False)

    print(f"\nDone! {len(master)} total rows written to: {OUTPUT_PATH}")
    print(f"(Duplicates were kept, as requested)")

if __name__ == "__main__":
    main()