#!/usr/bin/env python3
"""
build_ordered_mcq_book_fixed.py
- Reads order.txt and processes JSON files in that exact order
- Produces one big Markdown book with YAML header + TOC
- Auto-numbers MCQs across chapters
"""

import json
import os
import glob
import re
from pathlib import Path

# --------------------------
# CONFIG
# --------------------------
INPUT_FOLDER = "mcq_json"            # folder that contains your .json files
ORDER_FILE = "order.txt"             # master order list (one filename per line)
OUTPUT_FILE = "Pediatric_Surgery_MCQ_Book.md"
BOOK_TITLE = "Pediatric Surgery MCQ Book"
AUTHOR = "Dr. Safwan Ahmad Khan"
YEAR = "2025"

# show (cleaned) chapter source line under chapter heading? (True/False)
SHOW_CHAPTER_SOURCE = False

# Answer placement: "immediate", "chapter_end", "book_end"
ANSWER_PLACEMENT = "immediate"

# --------------------------
# YAML metadata header
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
# Helpers
# --------------------------

def read_order_file(order_file):
    """Read the order file and return a list of filenames."""
    with open(order_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def find_file_in_input(candidate_name):
    """
    Given candidate from order.txt (with or without .json),
    return the real path in INPUT_FOLDER (case-insensitive match).
    """
    candidate = candidate_name if candidate_name.lower().endswith(".json") else candidate_name + ".json"
    path = os.path.join(INPUT_FOLDER, candidate)
    if os.path.exists(path):
        return path
    # try case-insensitive exact basename match
    basename_lower = os.path.basename(candidate).lower()
    for p in glob.glob(os.path.join(INPUT_FOLDER, "*.json")):
        if os.path.basename(p).lower() == basename_lower:
            return p
    return None

def clean_source_display(filename):
    """Remove leading numeric prefix like '74_' and trailing .json"""
    name = os.path.basename(filename)
    # strip extension
    if name.lower().endswith(".json"):
        name = name[:-5]
    # remove leading numbers and underscore(s)
    name = re.sub(r"^\d+_+", "", name)
    # Replace underscores with spaces and capitalize
    name = name.replace('_', ' ').replace(' mcqs', '').title()
    return name

def slugify(text):
    """Convert text to a URL-friendly slug."""
    return re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '-')

def load_json_file(file_path):
    """Load JSON file and return data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8-sig') as f: # Handle BOM
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"  WARNING: Skipping malformed JSON in {file_path}")
        return None


# --------------------------
# Build function
# --------------------------

def build_book():
    """Builds the MCQ book from JSON files based on the order specified in ORDER_FILE."""
    os.makedirs(INPUT_FOLDER, exist_ok=True)

    if not os.path.exists(ORDER_FILE):
        raise FileNotFoundError(f"Order file not found: {ORDER_FILE}")

    ordered_filenames = read_order_file(ORDER_FILE)
    print("Processing files in this order:", ordered_filenames)

    all_chapters = []
    toc_entries = []
    mcq_counter = 1
    book_answer_blocks = []

    for listed in ordered_filenames:
        file_path = find_file_in_input(listed)
        if not file_path:
            print(f"WARNING: Listed file not found in {INPUT_FOLDER}: {listed}  (skipping)")
            continue

        data = load_json_file(file_path)
        if data is None:
            continue

        # --- MODIFICATION ---
        # Always derive the disease name from the filename for consistent ordering.
        disease = clean_source_display(file_path)
        # --- END MODIFICATION ---
        
        disease = disease.strip()
        chapter_slug = slugify(disease)

        print(f"Processing: {listed} -> {disease}")

        chapter_content = []
        chapter_answers = []

        chapter_content.append(f"\n\n# {disease}\n")
        if SHOW_CHAPTER_SOURCE:
            display_src = clean_source_display(os.path.basename(file_path))
            chapter_content.append(f"*Chapter source file: `{display_src}`*\n")

        toc_entries.append((disease, chapter_slug))

        mcqs = data.get("mcqs", [])

        for q in mcqs:
            q_text = q.get("question", "").strip()
            if not q_text:
                print(f"  WARNING: Skipping malformed MCQ in {file_path}")
                continue
            
            options = q.get("options", {})
            ans = str(q.get("correct_answer", "")).strip()
            exp = q.get("explanation", "").strip()

            chapter_content.append(f"### MCQ {mcq_counter}: {q_text}\n")
            # Ensure options are sorted, typically A, B, C, D
            for key in sorted(options.keys()):
                chapter_content.append(f"- **{key}.** {options[key]}")

            if ANSWER_PLACEMENT == "immediate":
                chapter_content.append(f"\n**Answer:** **{ans}**  ")
                if exp:
                    chapter_content.append(f"**Explanation:** {exp}\n")
                chapter_content.append("\n---\n")
            else:
                chapter_content.append("\n")
                chapter_answers.append((mcq_counter, ans, exp))
                book_answer_blocks.append((mcq_counter, disease, q_text, ans, exp))
            
            mcq_counter += 1

        if ANSWER_PLACEMENT == "chapter_end" and chapter_answers:
            chapter_content.append("\n**Answer Key (this chapter)**\n")
            for num, ans, exp in chapter_answers:
                chapter_content.append(f"- **MCQ {num}** — **{ans}**: {exp}")
            chapter_content.append("\n---\n")

        all_chapters.append("".join(chapter_content))

    md_lines = []
    md_lines.append(YAML_HEADER)

    toc_lines = ["## Table of Contents\n"]
    for disease, slug in toc_entries:
        toc_lines.append(f"- [{disease}](#{slug})")
    
    md_lines.append("\n".join(toc_lines))
    md_lines.append("\n---\n")

    md_lines.extend(all_chapters)

    if ANSWER_PLACEMENT == "book_end" and book_answer_blocks:
        md_lines.append("\n# Complete Answer Key\n")
        for num, disease, qtext, ans, exp in book_answer_blocks:
            md_lines.append(f"- **MCQ {num}** ({disease}) — **{ans}**: {exp}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n".join(md_lines))

    print(f"Finished. Output written to: {OUTPUT_FILE}")
    print(f"Total MCQs: {mcq_counter - 1}")


if __name__ == "__main__":
    build_book()