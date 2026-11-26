"""
To run:    .venv/bin/python scripts/inspect_dataset.py
"""

import textwrap
import pandas as pd
from huggingface_hub import HfFileSystem

TABLES = [
    "hf://datasets/hao-li/AIDev/pull_request.parquet",
    "hf://datasets/hao-li/AIDev/repository.parquet",
    "hf://datasets/hao-li/AIDev/pr_reviews.parquet",
    "hf://datasets/hao-li/AIDev/pr_review_comments.parquet",
]

def load_table(name):
    df = pd.read_parquet(name)
    return df


def print_table_info(name, df):
    print(f"\n--- {name} ---")
    print(f"rows: {len(df)}")
    print(f"columns ({len(df.columns)}):")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}")
    print("sample rows (3):")
    with pd.option_context("display.max_columns", None, "display.width", 120,
                           "display.max_colwidth", 60):
        print(df.head(3).to_string(index=False))


def main():
    for name in TABLES:
        print(f"\nloading {name} ...")
        df = load_table(name)
        print_table_info(name, df)


if __name__ == "__main__":
    main()
