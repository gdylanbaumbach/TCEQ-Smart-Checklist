"""
TAC 30 Chapter 290 — Subsection-Level Citation JSON Builder (v2)
-----------------------------------------------------------------
Improved version that slices at the SUBSECTION level (e.g. §290.46(m))
rather than the top-level section (§290.46), giving targeted rule text
for each specific citation code used in the checklist.

OUTPUT: tac30_chapter290.json

HOW TO RUN:
  1. Install dependency if needed:
       conda install -c conda-forge pdfplumber -y
  2. Place all four Chapter 290 PDFs in the same folder as this script
  3. Run:
       python build_tac290_json.py
  4. Output: tac30_chapter290.json in the same folder

LOOKUP STRATEGY IN APP:
  Citation like §290.46(m)(1)(A) is looked up by trying keys in order:
    1. "290.46(m)"   -- subsection level (preferred)
    2. "290.46"      -- full section fallback
  This means even deeply nested citations get the right subsection text.

KEY FORMAT:
  "290.46(m)"  -- subsection entry, e.g. section 290.46 subsection (m)
  "290.46"     -- full section entry (fallback if no subsection match)
"""

import os
import re
import json
import pdfplumber

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
PDF_FILES = [
    "TAC Chapter 290 merged and compressed Subchapter G (optional).pdf",
    "TAC Chapter 290 merged and compressed SUBCHAPTER F.pdf",
    "TAC Chapter 290 merged and compressed SUBCHAPTER D.pdf",
    "Chapter 290 Subchapter H merged.pdf",
]
OUTPUT_FILE = "tac30_chapter290.json"
MAX_CHARS = 0  # 0 = no cap; subsections are naturally short enough
# ─────────────────────────────────────────────────────────────────────────────


def extract_text_from_pdf(path):
    print(f"  Reading: {os.path.basename(path)}")
    full_text = ""
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            if (i + 1) % 50 == 0:
                print(f"    ... {i + 1}/{total} pages")
    print(f"    Done. {total} pages, {len(full_text):,} chars.")
    return full_text


def parse_sections_and_subsections(text):
    """
    Two-pass parse:
      Pass 1: Split into top-level sections by header like §290.102. Title.
      Pass 2: Within each section, split into subsections (a), (b), (c)...

    Returns dict with keys like:
      "290.46"     -> full section text (fallback)
      "290.46(a)"  -> subsection (a) text only
      "290.46(m)"  -> subsection (m) text only
    """
    entries = {}

    # Pass 1: split on section headers
    section_pattern = r'(§290\.\d+\.[^\n]+)\n'
    parts = re.split(section_pattern, text)

    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body   = parts[i + 1] if i + 1 < len(parts) else ""

        num_match = re.match(r'§(290\.\d+)', header)
        if not num_match:
            continue
        section_key = num_match.group(1)

        # Store full section as fallback
        full_text = (header + "\n" + body.strip())
        entries[section_key] = full_text if not MAX_CHARS else full_text[:MAX_CHARS]

        # Pass 2: split body on subsection markers at line start
        sub_pattern = r'\n(\([a-z]\)[ \t])'
        sub_parts = re.split(sub_pattern, body)

        # sub_parts[0] is everything before the first subsection marker
        # In TAC 30, this is typically the (a) subsection text since
        # (a) immediately follows the section header without a blank line
        if sub_parts[0].strip():
            entries[f"{section_key}(a)"] = header + "\n" + sub_parts[0].strip()

        for j in range(1, len(sub_parts), 2):
            sub_marker = sub_parts[j].strip()
            sub_body   = sub_parts[j + 1] if j + 1 < len(sub_parts) else ""

            letter_match = re.match(r'\(([a-z])\)', sub_marker)
            if not letter_match:
                continue
            letter  = letter_match.group(1)
            sub_key = f"{section_key}({letter})"
            sub_text = f"{header}\n{sub_marker} {sub_body.strip()}"
            entries[sub_key] = sub_text if not MAX_CHARS else sub_text[:MAX_CHARS]

    return entries


def main():
    all_entries = {}
    missing = []

    print("=" * 60)
    print("TAC 30 Chapter 290 — Subsection-Level JSON Builder v2")
    print("=" * 60)

    for pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"  WARNING: File not found — {pdf_path}")
            missing.append(pdf_path)
            continue

        raw_text = extract_text_from_pdf(pdf_path)
        entries  = parse_sections_and_subsections(raw_text)

        s_keys  = [k for k in entries if re.match(r'^\d+\.\d+$', k)]
        ss_keys = [k for k in entries if re.match(r'^\d+\.\d+\([a-z]\)$', k)]
        print(f"  Sections: {len(s_keys)}  |  Subsections: {len(ss_keys)}")
        print(f"  Sample subsection keys: {sorted(ss_keys)[:6]}")
        print()
        all_entries.update(entries)

    print("=" * 60)
    s_total  = len([k for k in all_entries if re.match(r'^\d+\.\d+$', k)])
    ss_total = len([k for k in all_entries if re.match(r'^\d+\.\d+\([a-z]\)$', k)])
    print(f"Total sections:    {s_total}")
    print(f"Total subsections: {ss_total}")
    print(f"Total entries:     {len(all_entries)}")

    if missing:
        print(f"\nWARNING: {len(missing)} file(s) not found.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\nOutput: {OUTPUT_FILE} ({size_kb:.1f} KB)")

    # Spot-checks
    for check in ["290.46(m)", "290.109(d)", "290.115(f)", "290.46"]:
        if check in all_entries:
            chars = len(all_entries[check])
            preview = all_entries[check][:200].replace('\n', ' ')
            print(f"\nSpot-check §{check} ({chars:,} chars):")
            print(f"  {preview}...")


if __name__ == "__main__":
    main()
