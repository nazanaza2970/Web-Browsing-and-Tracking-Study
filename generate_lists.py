#!/usr/bin/env python3
"""
generate_lists.py

Splits a pool of websites into non-overlapping lists (one per HIT/participant)
and writes:
  1. lists/NNN.json      - one JSON array of URLs per HIT, for the task page to fetch
  2. batch.csv            - a CSV ready for MTurk's "Upload a CSV file" batch-creation
                            step, with one row per HIT and a list_id column that
                            fills the ${list_id} placeholder in the HIT template.

-----------------------------------------------------------------------------
CONFIGURE THESE VARIABLES
-----------------------------------------------------------------------------
"""

import csv
import json
import math
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# VARIABLES — edit these for your run
# ---------------------------------------------------------------------------

# Path to a plain text file with one website URL per line (the full pool).
SITE_POOL_FILE = "clean_top_1000.txt"

# Number of websites assigned to each participant / HIT.
SITES_PER_PARTICIPANT = 15

# Where to write the per-HIT JSON files (matches the "lists/" folder the
# task page fetches from, e.g. lists/001.json).
OUTPUT_LISTS_DIR = "lists"

# Where to write the MTurk batch-creation CSV.
OUTPUT_BATCH_CSV = "batch.csv"

# If True, shuffle the site pool before splitting (recommended, so list
# composition isn't determined by whatever order the pool file happens
# to be in). Set a fixed SEED for reproducibility.
SHUFFLE_POOL = True
SEED = 42

# If the pool doesn't divide evenly by SITES_PER_PARTICIPANT, decide what
# to do with the remainder:
#   "drop"    - discard the leftover sites (some sites never get assigned)
#   "smaller" - put the leftover sites into one final, smaller list
LEFTOVER_STRATEGY = "smaller"

# Base URL of your published GitHub Pages task page, used only to print
# example HIT links at the end (not required for the CSV itself).
TASK_PAGE_BASE_URL = "https://nazanaza2970.github.io/Web-Browsing-and-Tracking-Study/index.html"

# ---------------------------------------------------------------------------


def load_site_pool(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"Error: site pool file '{path}' not found.")
    with p.open("r", encoding="utf-8") as f:
        sites = [line.strip() for line in f if line.strip()]
    if not sites:
        sys.exit(f"Error: '{path}' contained no non-empty lines.")
    return sites


def split_into_lists(sites, per_list, leftover_strategy):
    n_full_lists = len(sites) // per_list
    remainder = len(sites) % per_list

    chunks = [
        sites[i * per_list:(i + 1) * per_list]
        for i in range(n_full_lists)
    ]

    if remainder:
        leftover = sites[n_full_lists * per_list:]
        if leftover_strategy == "smaller":
            chunks.append(leftover)
        elif leftover_strategy == "drop":
            print(
                f"Note: dropping {remainder} leftover site(s) that didn't "
                f"fill a full list of {per_list}."
            )
        else:
            sys.exit(f"Unknown LEFTOVER_STRATEGY: '{leftover_strategy}'")

    return chunks


def write_json_lists(chunks, output_dir):
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    width = max(3, len(str(len(chunks))))  # zero-pad to at least 3 digits
    list_ids = []
    for idx, chunk in enumerate(chunks, start=1):
        list_id = str(idx).zfill(width)
        file_path = out_dir / f"{list_id}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2)
        list_ids.append(list_id)
    return list_ids


def write_batch_csv(list_ids, output_csv, task_page_base_url):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["list_id"])
        for list_id in list_ids:
            writer.writerow([list_id])
    print(f"\nWrote batch CSV: {output_csv}")
    print("In the MTurk batch-creation step, reference the column as ${list_id}")
    print("in your Survey link field, e.g.:")
    print(f"  {task_page_base_url}?list=${{list_id}}")


def main():
    sites = load_site_pool(SITE_POOL_FILE)
    print(f"Loaded {len(sites)} sites from '{SITE_POOL_FILE}'.")

    if SHUFFLE_POOL:
        random.seed(SEED)
        random.shuffle(sites)
        print(f"Shuffled pool (seed={SEED}).")

    chunks = split_into_lists(sites, SITES_PER_PARTICIPANT, LEFTOVER_STRATEGY)
    n_lists = len(chunks)
    n_assigned = sum(len(c) for c in chunks)

    print(f"Split into {n_lists} list(s) of up to {SITES_PER_PARTICIPANT} sites each.")
    print(f"Total sites assigned: {n_assigned} / {len(sites)}")

    list_ids = write_json_lists(chunks, OUTPUT_LISTS_DIR)
    print(f"Wrote {len(list_ids)} JSON file(s) to '{OUTPUT_LISTS_DIR}/'.")

    write_batch_csv(list_ids, OUTPUT_BATCH_CSV, TASK_PAGE_BASE_URL)

    print("\nDone. Example generated HIT link:")
    if list_ids:
        print(f"  {TASK_PAGE_BASE_URL}?list={list_ids[0]}")


if __name__ == "__main__":
    main()