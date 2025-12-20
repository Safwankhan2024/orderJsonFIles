#!/usr/bin/env python3
"""
proofread_mcqs.py
Proof-read paediatric-surgery MCQ JSON files with OpenAI API
(10 concurrent requests)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import aiohttp
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv   # <── NEW
load_dotenv()


# ------------------------------------------------------------------
# CONFIGURATION – change only these two lines
# ------------------------------------------------------------------
FOLDER = "mcq_json"          # ← change to real folder name
MODEL  = "gpt-5.1"          # ← change model name once
# ------------------------------------------------------------------

REPORT_FILE = "proofread_report.json"
SEMAPHORE_LIMIT = 10            # concurrency level
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    sys.exit("ERROR: set OPENAI_API_KEY environment variable")

print("DEBUG: key starts with", os.getenv("OPENAI_API_KEY", "")[:12])
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# ------------------------------------------------------------------
# Prompt we send to the model
# ------------------------------------------------------------------
SYSTEM_PROMPT = """
You receive a single JSON object representing a paediatric-surgery MCQ.
Perform ONLY a factual / medical accuracy check. Ignore:
- spelling, punctuation, capitalisation, grammar
- formatting or stylistic issues
- wording preferences that do not change meaning

Report ONLY genuine errors such as:
- wrong answer key
- medically incorrect statements
- missing or duplicated options
- contradictory stem and key

Return JSON:
{
  "errors": ["short factual description", …],   // empty if nothing real found
  "fixed": { <only the fields you changed> }     // ABSOLUTELY MINIMAL patch
}
If no factual mistake exists return {"errors": []} with NO "fixed" key.
Do NOT send back the entire question – only the tiny fragment you modified.
"""

# ------------------------------------------------------------------
# Helper: load every .json file in the folder
# ------------------------------------------------------------------
def load_all_mcqs(folder: Path) -> List[Dict[str, Any]]:
    files = list(folder.glob("*.json"))
    if not files:
        print("No JSON files found in folder:", folder.resolve())
    mcqs = []
    for fp in files:
        try:
            with fp.open(encoding="utf-8") as fh:
                data = json.load(fh)
                # Accept either a single question dict or a list of questions
                if isinstance(data, list):
                    for idx, q in enumerate(data):
                        q["_meta_file"] = fp.name
                        q["_meta_idx"]  = idx
                        mcqs.append(q)
                else:
                    data["_meta_file"] = fp.name
                    data["_meta_idx"]  = 0
                    mcqs.append(data)
        except Exception as e:
            print(f"Skipping {fp.name}: {e}")
    return mcqs

# ------------------------------------------------------------------
# Single async call to OpenAI
# ------------------------------------------------------------------
async def ask_openai(question_json: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": json.dumps(question_json, ensure_ascii=False)}
            ],
            temperature=0
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        return {"errors": [f"OpenAI call failed: {e}"]}

# ------------------------------------------------------------------
# Worker with semaphore
# ------------------------------------------------------------------
async def worker(q: Dict[str, Any], sem: asyncio.Semaphore) -> Dict[str, Any]:
    async with sem:
        result = await ask_openai(q)
        # keep metadata so we know where this came from
        result["meta_file"] = q.get("_meta_file")
        result["meta_idx"]  = q.get("_meta_idx")
        result["original"]  = q
        return result

# ------------------------------------------------------------------
# Main async coordinator
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# NEW main – concise report
# ------------------------------------------------------------------
async def main():
    folder_path = Path(FOLDER)
    if not folder_path.is_dir():
        sys.exit(f"Folder '{FOLDER}' does not exist")

    mcqs = load_all_mcqs(folder_path)
    print(f"Loaded {len(mcqs)} MCQ objects … running factual check …")

    sem   = asyncio.Semaphore(SEMAPHORE_LIMIT)
    tasks = [asyncio.create_task(worker(q, sem)) for q in mcqs]
    results = await asyncio.gather(*tasks)

    # build minimal report
    report = []
    for res in results:
        if res.get("errors"):                       # only real mistakes
            report.append({
                "file": res["meta_file"],
                "index": res["meta_idx"],
                "errors": res["errors"],
                "fixed": res.get("fixed", {})      # tiny patch, not full question
            })

    if report:
        with open(REPORT_FILE, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print(f"✅ {len(report)} faulty questions → {REPORT_FILE}")
    else:
        print("✅ No factual errors found – nothing written.")

# ------------------------------------------------------------------
# Entry-point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())