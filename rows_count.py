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


def count_rows_with_pandas(file_path):
    df = pd.read_csv(file_path)
    return len(df)


count = count_rows_with_pandas(args.file_name)
print(f"The CSV file contains {count} rows (excluding header).")
