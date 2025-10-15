import argparse

import pandas as pd

parser = argparse.ArgumentParser(
    description="Count the number of rows in a CSV file using pandas."
)

parser.add_argument(
    "--file-name",
    type=str,
    required=True,
    help="File name",
)

args = parser.parse_args()


df = pd.read_csv(args.file_name)
print(f"The CSV file contains {len(df)} rows (excluding header).")


for unique_field in ("title", "url", "text"):
    unique_field_count = df[unique_field].nunique()

    print(f"Number of unique {unique_field}s: {unique_field_count}")
