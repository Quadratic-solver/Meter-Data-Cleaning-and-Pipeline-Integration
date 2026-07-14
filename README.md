# Meter-Data-Cleaning-and-Pipeline-Integration

> Security note: this repository processes internal meter-testing data. The raw files and generated outputs may contain meter serial numbers, test values, and other operational details that should be treated as sensitive/internal information. Do not upload raw data or output files to public repositories without approval.

The project reads messy raw data from CSV files and extracts serial numbers, FL/LL values. It cleans and resolves duplicate extracted records and resolve data conflicts and unresolved rows for manual review. It will update .csv and .xlxs files with the cleaned values.

## Overview

The workflow:

1. Read messy raw CSV files from the data folder.
2. Extract meter serial numbers and FL/LL values.
3. Clean and resolve duplicate data from the extracted records.
4. Resolve conflicts and route unresolved rows for manual review.
5. Update lot files (.csv and .xlsx) with the cleaned values.

The output is written to the output folder, including:

- a cleaned master dataset
- a review file for unresolved conflicts
- updated lot files in the integrated output folder

## Project Structure

```text
data/
  raw/                  # raw source CSV files
  lots/                 # lot test files to update
script/
  0_check_lots.py       # validates lot files before processing
  1_build_database.py   # migrates lot files into a SQLite database
  2_check_database.py   # inspects the database contents
  3_load_result.py      # loads the master clean file and updates the database
  4_lot_excel.py        # exports updated lot files to output/integrated
  extract.py            # extraction helpers
  find.py               # helper utilities
  profile.py            # profiling helpers
  remove_error.py       # separates clean rows from unresolved/error rows
  remove_text.py        # deduplicates and resolves conflicts in the master list
  update_lots.py        # earlier lot-update workflow
output/
  integrated/           # generated updated lot files
  master_final_clean.csv
  master_serial_fl_ll.csv
  master_serial_fl_ll_clean.csv
  unresolved_conflicts_for_review.csv
database/
  lot_data.db           # SQLite database created by the pipeline
```

## Requirements

Install the required Python packages:

```bash
pip install pandas openpyxl
```

## Typical Workflow

Run the scripts in order:

```bash
python script/0_check_lots.py
python script/1_build_database.py
python script/2_check_database.py
python script/3_load_result.py
python script/4_lot_excel.py --all
```

## What the Pipeline Produces

- Cleaned master file: output/master_final_clean.csv
- Review file for unresolved conflicts: output/unresolved_conflicts_for_review.csv
- Updated lot files: output/integrated/

## Notes

- The project is designed to preserve the original lot files and write updated versions to the integrated output folder.
- Some rows may be flagged for manual review when FL/LL values conflict or when serial values appear malformed.
- This repository is intended for reproducible processing and future extension.

## License

This project is for internal use and repository sharing purposes.
