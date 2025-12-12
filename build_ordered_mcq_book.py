#!/usr/bin/env python3
"""
build_ordered_mcq_book.py

Usage:
  - Put all your JSON files in the folder defined by INPUT_FOLDER.
  - Create an order.txt file listing filenames (one per line) in the exact order you want chapters.
  - Run: python build_ordered_mcq_book.py
"""

import json
import os
import glob
import re
from pathlib import Path

# --------------------------
# CONFIG - edit as needed
# --------------------------
INPUT_FOLDER = "mcq_json"            # folder that contains your .json files
ORDER_FILE = "order.txt"             # master order list (one filename per line)
OUTPUT_FILE = "Pediatric_Surgery_MCQ_Book.md"
BOOK_TITLE = "Pediatric Surgery MCQ Book"
AUTHOR = "Dr. Safwan Ahmad Khan"
YEAR = "2025"

# Answer placement: one of "immediate", "chapter_end", "book_end"
# - "immediate": question followed by answer+explanation
# - "chapter_end": all questions first, then answers+explanations for that chapter
# - "book_end": all questions in whole book first, then one single Answer Key at end
ANSWER_PLACEMENT = "immediate"

# --------------------------
# YAML metadata header (will be written at top of the file)
# You can add other Pandoc or site-specific fields here
# --------------------------
YAML_HEADER = f"""---
title: "{BOOK_TITLE}"
author: "{AUTHOR}"
date: "{YEAR}"
toc: true
toc-depth: 2
number-sections: false
description: "A comprehensive collection of pediatric surgery MCQs organized by disease."
---
"""

# --------------------------
# Helper functions
# --------------------------
def slugify(text: str) -> str:
    """
    Create a GitHub/GFM-style slug for header linking:
    Lowercase, replace non-alnum with hyphen, collapse hyphens, strip edges.
    """
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)         # remove punctuation
    s = re.sub(r"\s+", "-", s)             # whitespace -> hyphen
    s = re.sub(r"-+", "-", s)              # collapse hyphens
    return s.strip("-")

def read_order_file(path: str):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            lines.append(line)
    return lines

def load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --------------------------
# Main build function
# --------------------------
def build_book():
    os.makedirs(INPUT_FOLDER, exist_ok=True)

    if not os.path.exists(ORDER_FILE):
        raise FileNotFoundError(f"Order file not found: {ORDER_FILE}")

    ordered_filenames = read_order_file(ORDER_FILE)

    # prepare output containers
    md_lines = []
    toc_entries = []
    mcq_counter = 1

    # For answer key modes
    chapter_answer_blocks = {}   # chapter -> list of (num, answer, explanation)
    book_answer_blocks = []      # list of (num, chapter, question, answer, explanation)

    # Add YAML header and Title page
    md_lines.append(YAML_HEADER)
    md_lines.append(f"# {BOOK_TITLE}\n")
    md_lines.append(f"**Author:** {AUTHOR}  \n**Year:** {YEAR}\n")
    md_lines.append("---\n")

    # Iterate in the order provided
    for fname in ordered_filenames:
        # find file in input folder (allow with/without .json)
        candidate = fname if fname.lower().endswith(".json") else fname + ".json"
        file_path = os.path.join(INPUT_FOLDER, candidate)
        if not os.path.exists(file_path):
            # try to find by basename case-insensitively
            matches = [p for p in glob.glob(os.path.join(INPUT_FOLDER, "*.json")) if os.path.basename(p).lower() == candidate.lower()]
            if matches:
                file_path = matches[0]
            else:
                print(f"WARNING: File listed in order.txt not found: {candidate}  (skipping)")
                continue

        data = load_json_file(file_path)
        disease = data.get("disease", Path(file_path).stem)
        mcqs = data.get("mcqs", [])

        chapter_slug = slugify(disease)
        # Chapter heading
        md_lines.append(f"\n\n# {disease}\n")
        md_lines.append(f"*Chapter source file: `{os.path.basename(file_path)}`*\n")
        # Add TOC entry (GFM-style anchor)
        toc_entries.append((disease, chapter_slug))

        # Two modes for question listing:
        # - if ANSWER_PLACEMENT == "chapter_end" then collect Qs first, answers later
        chapter_answers = []

        for q in mcqs:
            q_text = q.get("question", "").strip()
            options = q.get("options", {})
            ans = q.get("correct_answer", "").strip()
            exp = q.get("explanation", "").strip()

            if ANSWER_PLACEMENT == "immediate":
                md_lines.append(f"### MCQ {mcq_counter}: {q_text}\n")
                # options sorted by key order A,B,C...
                for key in sorted(options.keys()):
                    md_lines.append(f"- **{key}.** {options[key]}")
                md_lines.append(f"\n**Answer:** **{ans}**  ")
                md_lines.append(f"**Explanation:** {exp}\n")
                md_lines.append("\n---\n")
            else:
                # Question first
                md_lines.append(f"### MCQ {mcq_counter}: {q_text}\n")
                for key in sorted(options.keys()):
                    md_lines.append(f"- **{key}.** {options[key]}")
                md_lines.append("\n")
                # accumulate answer
                chapter_answers.append((mcq_counter, ans, exp))
                # accumulate for book_end too
                book_answer_blocks.append((mcq_counter, disease, q_text, ans, exp))

            mcq_counter += 1

        # After finishing chapter questions, if chapter_end mode, append answers block
        if ANSWER_PLACEMENT == "chapter_end" and chapter_answers:
            md_lines.append("\n**Answer Key (this chapter)**\n")
            for num, ans, exp in chapter_answers:
                md_lines.append(f"- **MCQ {num}** — **{ans}**: {exp}")
            md_lines.append("\n---\n")

    # Build the Table of Contents (after title but before content ideally)
    # We'll insert it after the initial title block: find first '---' marker index
    # If not found, just prepend
    toc_lines = []
    toc_lines.append("## Table of Contents\n")
    for disease, slug in toc_entries:
        # Markdown anchor link format for headers: # + slug ; using GFM-style link
        anchor = f"#{slug}"
        toc_lines.append(f"- [{disease}]({anchor})")
    toc_lines.append("\n---\n")

    # find insertion point (after first '---' which we created earlier)
    insert_at = 0
    for i, line in enumerate(md_lines):
        if line.strip() == "---":
            insert_at = i + 1
            break
    md_lines[insert_at:insert_at] = toc_lines

    # If book_end, append full Answer Key
    if ANSWER_PLACEMENT == "book_end" and book_answer_blocks:
        md_lines.append("\n# Complete Answer Key\n")
        for num, disease, qtext, ans, exp in book_answer_blocks:
            md_lines.append(f"- **MCQ {num}** ({disease}) — **{ans}**: {exp}")

    # Final write
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n".join(md_lines))

    print(f"Finished. Output written to: {OUTPUT_FILE}")
    print(f"Total MCQs: {mcq_counter - 1}")

# --------------------------
# Run script
# --------------------------
if __name__ == "__main__":
    build_book()
