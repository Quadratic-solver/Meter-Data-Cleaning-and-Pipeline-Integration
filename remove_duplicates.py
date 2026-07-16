""" Removes duplicate rows from the master CSV file.  
    Some rows have duplicate serial numbers with different FL/LL values.
    This script removes exact duplicates (same serial + FL + LL) and resolves conflicting duplicates 
"""

import pandas as pd
import os

# ==== CONFIG ====
INPUT_PATH = "output/master_serial_fl_ll.csv"
OUTPUT_PATH = "output/master_serial_fl_ll_clean.csv"

def main():
    print(f"Reading: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH, dtype=str)
    total_before = len(df)
    print(f"Total rows before: {total_before}")

    # Step 1: remove EXACT duplicates such as same serial + FL + LL
    exact_dupe_mask = df.duplicated(subset=["meter_serial", "FL", "LL"], keep="first")
    exact_dupe_count = exact_dupe_mask.sum()

    df_deduped = df[~exact_dupe_mask].copy()
    print(f"\nExact duplicates removed (same serial, FL, LL): {exact_dupe_count}")
    print(f"Rows remaining after exact dedup: {len(df_deduped)}")

    # Step 1.5: drops blank FL/LL rows when a value exists for the same serial
    def is_blank(val):
        return pd.isna(val) or str(val).strip() == ""

    blank_mask = df_deduped["FL"].apply(is_blank) & df_deduped["LL"].apply(is_blank)
    serials_with_value = set(df_deduped.loc[~blank_mask, "meter_serial"])

    drop_blank_mask = blank_mask & df_deduped["meter_serial"].isin(serials_with_value)
    blank_dropped_count = drop_blank_mask.sum()

    df_deduped = df_deduped[~drop_blank_mask].copy()
    print(f"\nBlank FL/LL rows dropped (serial already has a real value elsewhere): {blank_dropped_count}")
    print(f"Rows remaining: {len(df_deduped)}")

    df_deduped["date_tested"] = pd.to_datetime(df_deduped["date_tested"], errors="coerce")

    # Step 2: resolves conflicting duplicates (same serial, different FL/LL) using date
    # count how many distinct (FL, LL) combinations each meter_serial has
    combo_counts = df_deduped.groupby("meter_serial")[["FL", "LL"]].apply(
        lambda g: g.drop_duplicates().shape[0]
    )
    conflicting_serials = combo_counts[combo_counts > 1].index
    is_conflict_row = df_deduped["meter_serial"].isin(conflicting_serials)

    conflict_serial_count = len(conflicting_serials)
    print(f"\n=== CONFLICT RESOLUTION (printed here only, NOT saved as a column in the file) ===")
    print(f"Meter serials with conflicting FL/LL values: {conflict_serial_count}")

    non_conflict_df = df_deduped[~is_conflict_row]
    conflict_df = df_deduped[is_conflict_row]

    resolved_rows = []
    unresolved_rows = []
    resolved_serial_count = 0
    unresolved_serial_count = 0
    rows_dropped_as_older = 0

    for serial, group in conflict_df.groupby("meter_serial"):
        if group["date_tested"].notna().any():
            # Checks the row with the latest date_tested and keeps that one, dropping the others
            best_idx = group["date_tested"].idxmax()
            best_row = group.loc[[best_idx]]
            resolved_rows.append(best_row)
            dropped = len(group) - 1
            rows_dropped_as_older += dropped
            resolved_serial_count += 1
            print(f"  RESOLVED {serial}: kept FL={best_row['FL'].values[0]}, LL={best_row['LL'].values[0]} "
                  f"(date={best_row['date_tested'].values[0]}) -- dropped {dropped} older row(s)")
        else:
            # If there is no date information, we cannot resolve which row to keep, so we keep all of them
            unresolved_rows.append(group)
            unresolved_serial_count += 1
            combos = group[["FL", "LL"]].drop_duplicates().values.tolist()
            print(f"  UNRESOLVED {serial}: no date info to compare -- kept all {len(group)} rows -- values: {combos}")

    print(f"\nConflicts resolved using date (kept latest, dropped older): {resolved_serial_count} serials, "
          f"{rows_dropped_as_older} old rows dropped")
    print(f"Conflicts left unresolved (no date to compare, all rows kept): {unresolved_serial_count} serials")

    conflict_parts = resolved_rows + unresolved_rows
    if conflict_parts:
        resolved_conflict_df = pd.concat(conflict_parts, ignore_index=True)
        df_final = pd.concat([non_conflict_df, resolved_conflict_df], ignore_index=True)
    else:
        df_final = non_conflict_df

    # Saves the final cleaned CSV file
    os.makedirs("output", exist_ok=True)
    df_final.to_csv(OUTPUT_PATH, index=False)

    print(f"\nDone! Saved to: {OUTPUT_PATH}")
    print(f"Final row count: {len(df_final)}")
    print(f"(Note: {unresolved_serial_count} serials remain unresolved with multiple rows kept -- see summary above)")

if __name__ == "__main__":
    main()