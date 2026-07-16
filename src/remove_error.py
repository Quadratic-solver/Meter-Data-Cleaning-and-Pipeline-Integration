""" Removes rows from the master CSV file that have unresolved conflicts or malformed serials.
    Some rows have duplicate serial numbers with different FL/LL values.
"""

import pandas as pd
import os

# ==== CONFIG ====
INPUT_PATH = "output/master_serial_fl_ll_clean.csv"
CLEAN_OUTPUT_PATH = "output/master_final_clean.csv"
ERROR_OUTPUT_PATH = "output/unresolved_conflicts_for_review.csv"

# Splits the cleaned master list into good rows and rows that need manual review.
def main():
    print(f"Reading: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH, dtype=str)
    total_before = len(df)
    print(f"Total rows: {total_before}")

    # A serial is considred unresolved if it has more than one distinct (FL, LL) combination in the file.
    # FL and LL are considered together, so if a serial has two rows with the same FL but different LL, it is still considered a conflict.
    # Resolved rows are those that have only one distinct (FL, LL) combination for a given serial.
    combo_counts = df.groupby("meter_serial")[["FL", "LL"]].apply(
        lambda g: g.drop_duplicates().shape[0]
    )
    unresolved_serials = combo_counts[combo_counts > 1].index
    is_unresolved = df["meter_serial"].isin(unresolved_serials)

    # Checks for malformed serials, which are those that contain a comma (e.g. "763953,2SL2019094172EX,2SL2019094172")
    is_malformed = df["meter_serial"].str.contains(",", na=False)

    is_error = is_unresolved | is_malformed

    error_df = df[is_error].copy()
    error_df["error_reason"] = ""
    error_df.loc[is_unresolved[is_error], "error_reason"] += "conflicting_fl_ll;"
    error_df.loc[is_malformed[is_error], "error_reason"] += "malformed_serial;"
    error_df = error_df.sort_values("meter_serial")

    clean_df = df[~is_error]

    os.makedirs("output", exist_ok=True)
    clean_df.to_csv(CLEAN_OUTPUT_PATH, index=False)
    error_df.to_csv(ERROR_OUTPUT_PATH, index=False)

    malformed_count = is_malformed.sum()

    print(f"\nUnresolved conflicting serials: {len(unresolved_serials)}")
    print(f"Malformed serials (multiple values in one cell): {malformed_count}")
    print(f"Rows moved to error file: {len(error_df)}")
    print(f"Rows remaining in clean file: {len(clean_df)}")

    print(f"\nSaved clean file to: {CLEAN_OUTPUT_PATH}")
    print(f"Saved unresolved/error rows to: {ERROR_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
