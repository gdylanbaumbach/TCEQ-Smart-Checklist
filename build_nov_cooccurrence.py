"""
NOV Co-occurrence Builder
--------------------------
Reads the TCEQ NOV dataset and builds a co-occurrence JSON file
that powers the get_nov_context() function in the Streamlit app.

OUTPUT: nov_cooccurrence.json

HOW TO RUN:
  1. Install dependency if needed:
       conda install -c conda-forge openpyxl -y
     (pandas and openpyxl should already be in Anaconda)

  2. Place the NOV xlsx in the same folder as this script, OR
     update NOV_FILE below to the full path.

  3. Run:
       python build_nov_cooccurrence.py

  4. Output: nov_cooccurrence.json in the same folder.
     Add this file to your GitHub repo alongside tceq_checklist_v5.py.

JSON STRUCTURE:
  {
    "metadata": { total rows, citations found, regions, biz types },
    "global":    { citation -> { total_novs, co_occurs: [{citation, count, rate}] } },
    "by_region": { region_code -> { citation -> { ... } } },
    "by_biz":    { biz_cluster -> { citation -> { ... } } }
  }

  "rate" = fraction of NOVs containing this citation that also
           contain the co-occurring citation. e.g. rate=0.95 means
           95% of NOVs with citation A also have citation B.
"""

import os
import re
import json
import pandas as pd
from collections import Counter, defaultdict

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
NOV_FILE = "Texas_Commission_on_Environmental_Quality_-_Notices_Of_Violation__NOV__20260324.xlsx"
OUTPUT_FILE = "nov_cooccurrence.json"
MIN_COOCCUR_RATE = 0.10   # only include co-occurrences at 10%+ rate
TOP_N_COOCCUR = 5         # max co-occurring citations per entry
# ─────────────────────────────────────────────────────────────────────────────


def normalize_biz(val) -> str:
    """Cluster raw business type strings into consistent categories."""
    if pd.isna(val):
        return "UNKNOWN"
    v = str(val).upper().strip()
    if any(x in v for x in ["PUBLIC WATER", "WATER SUPPLY", "WATER SYSTEM",
                              "WATER UTILITIES", "TREAT AND SUPPLY"]):
        return "PUBLIC_WATER"
    if any(x in v for x in ["MOBILE HOME", "MHP"]):
        return "MOBILE_HOME_PARK"
    if any(x in v for x in ["CITY", "GOVERNMENT", "MUNICIPALITY"]):
        return "CITY_GOVERNMENT"
    if any(x in v for x in ["RESTAURANT", "FOOD", "CAFE"]):
        return "FOOD_SERVICE"
    if any(x in v for x in ["SCHOOL", "CHURCH", "CAMPGROUND", "RV PARK", "CAMP"]):
        return "INSTITUTIONAL"
    return "OTHER"


def normalize_region(val) -> str:
    """Extract region number and zero-pad, e.g. 'REGION_04'."""
    if pd.isna(val):
        return "UNKNOWN"
    m = re.search(r"REGION\s+(\d+)", str(val).upper())
    return f"REGION_{m.group(1).zfill(2)}" if m else "UNKNOWN"


def extract_290_cites(row) -> list:
    """Extract all unique Chapter 290 citation codes from a NOV row."""
    combined = " ".join([
        str(row.get("Cat. A Violation Citations", "") or ""),
        str(row.get("Cat. B Violation Citations", "") or ""),
        str(row.get("Cat. C Violation Citations", "") or ""),
    ])
    return list(set(re.findall(
        r"290\.\d+(?:\([a-z0-9]+\))*(?:\([a-z0-9]+\))*(?:\([a-z0-9]+\))*",
        combined
    )))


def build_entry(cite, co_counts, total) -> dict:
    """Build a co-occurrence entry for a single citation."""
    top_co = []
    for co_cite, count in co_counts.most_common(TOP_N_COOCCUR):
        rate = round(count / total, 2)
        if rate >= MIN_COOCCUR_RATE:
            top_co.append({"citation": co_cite, "count": count, "rate": rate})
    return {"total_novs": total, "co_occurs": top_co}


def main():
    print("=" * 55)
    print("NOV Co-occurrence Builder")
    print("=" * 55)

    if not os.path.exists(NOV_FILE):
        print(f"ERROR: NOV file not found: {NOV_FILE}")
        return

    print(f"Loading: {NOV_FILE}")
    df = pd.read_excel(NOV_FILE)
    print(f"Total rows: {len(df):,}")

    # Filter to Chapter 290 rows only
    def has_290(cell):
        if pd.isna(cell): return False
        return bool(re.search(r"290\.", str(cell)))

    mask = (
        df["Cat. A Violation Citations"].apply(has_290) |
        df["Cat. B Violation Citations"].apply(has_290) |
        df["Cat. C Violation Citations"].apply(has_290)
    )
    df290 = df[mask].copy()
    print(f"Chapter 290 rows: {len(df290):,}")

    df290["biz_norm"] = df290["Business Type"].apply(normalize_biz)
    df290["region_norm"] = df290["TCEQ Region"].apply(normalize_region)

    # ── Build co-occurrence counters ──────────────────────────────────────────
    global_cooccur = defaultdict(Counter)
    region_cooccur = defaultdict(lambda: defaultdict(Counter))
    biz_cooccur    = defaultdict(lambda: defaultdict(Counter))
    cite_totals         = Counter()
    region_cite_totals  = defaultdict(Counter)
    biz_cite_totals     = defaultdict(Counter)

    print("Building co-occurrence matrix...")
    for _, row in df290.iterrows():
        cites  = extract_290_cites(row)
        region = row["region_norm"]
        biz    = row["biz_norm"]

        for c in cites:
            cite_totals[c] += 1
            region_cite_totals[region][c] += 1
            biz_cite_totals[biz][c] += 1

        for c1 in cites:
            for c2 in cites:
                if c1 != c2:
                    global_cooccur[c1][c2] += 1
                    region_cooccur[region][c1][c2] += 1
                    biz_cooccur[biz][c1][c2] += 1

    # ── Build lookup dicts ────────────────────────────────────────────────────
    global_lookup = {}
    for cite, co_counts in global_cooccur.items():
        entry = build_entry(cite, co_counts, cite_totals[cite])
        if entry["co_occurs"]:
            global_lookup[cite] = entry

    region_lookup = {}
    for region, cite_dict in region_cooccur.items():
        region_lookup[region] = {}
        for cite, co_counts in cite_dict.items():
            entry = build_entry(cite, co_counts, region_cite_totals[region][cite])
            if entry["co_occurs"]:
                region_lookup[region][cite] = entry

    biz_lookup = {}
    for biz, cite_dict in biz_cooccur.items():
        biz_lookup[biz] = {}
        for cite, co_counts in cite_dict.items():
            entry = build_entry(cite, co_counts, biz_cite_totals[biz][cite])
            if entry["co_occurs"]:
                biz_lookup[biz][cite] = entry

    output = {
        "metadata": {
            "total_290_rows":       len(df290),
            "citations_with_data":  len(global_lookup),
            "regions":              sorted(region_lookup.keys()),
            "biz_types":            sorted(biz_lookup.keys()),
        },
        "global":    global_lookup,
        "by_region": region_lookup,
        "by_biz":    biz_lookup,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\nDone.")
    print(f"  Citations with co-occurrence data: {len(global_lookup)}")
    print(f"  Regions covered: {len(region_lookup)}")
    print(f"  Business type clusters: {sorted(biz_lookup.keys())}")
    print(f"  Output: {OUTPUT_FILE} ({size_kb:.1f} KB)")

    # Spot-check
    print("\nSpot-check §290.46(m):")
    print(json.dumps(global_lookup.get("290.46(m)", {}), indent=2))


if __name__ == "__main__":
    main()
