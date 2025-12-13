import os
import json
import time
import re
import logging
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from typing import Dict, Any
import requests

# === Configuration ===
FOLDER = Path(r"E:\kindle\mcq_json")  # update to your folder
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-497a8de3582645e9a52e7a08a49026eb")
MODEL = "deepseek-chat"  # or "deepseek-coder" if you prefer
MAX_CONCURRENT = 10  # Deepseek can handle 10 concurrent requests
RATE_LIMIT_SECONDS = 0.1  # small pause between retries to avoid bursts
MAX_RETRIES = 4
BACKOFF_FACTOR = 1.5
REQUEST_TIMEOUT = 120  # seconds

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("deepseek_parallel")

# === Helpers ===
def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\-_. ]", "_", name)
    name = name.strip().replace(" ", "_")
    return name[:200]

def atomic_write(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(path.parent)) as tmp:
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp_name = tmp.name
    os.replace(tmp_name, str(path))

def build_payload(disease: str, source_filename: str, mcqs: list) -> Dict[str, Any]:
    # Create the system prompt - updated to be clearer
    system_prompt = """You are an expert pediatric surgery reviewer. You will receive a JSON object containing MCQs for one disease.

The MCQs will be provided in this format:
{
  "disease": "Disease Name",
  "source_filename": "filename.json",
  "mcqs": [
    {
      "question": "Question text",
      "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
      "correct_answer": "A/B/C/D",
      "explanation": "Explanation text"
    },
    ... more MCQs
  ]
}

Perform the following tasks and return **only** a single JSON object (no extra text):

1. **Accuracy check**: Verify factual correctness of each question and answer relative to standard pediatric surgery knowledge.
   - For any factual error, provide a concise explanation and, if possible, a corrected fact or reference phrase (no external links).

2. **Spelling and grammar**: Detect spelling mistakes and grammatical issues in questions, options, and explanations.
   - Provide the corrected text for each detected issue.

3. **Quality assessment**: Rate overall quality on a 1–5 scale (5 = excellent).
   - Identify issues such as ambiguous stems, cueing in options, overly long/short options, poor distractors, outdated terminology, or missing clinical context.

4. **Suggestions for improvement**: Provide actionable edits: rewrite ambiguous stems, improve distractors, suggest better explanations, and propose references or topics to verify.
   - If a question should be removed, explain why.

5. **Optional improved version**: For up to 5 representative questions (prioritize those with issues), provide an improved rewritten version.
   - The explanation should be 1–2 sentences.

6. **Confidence**: Provide an overall confidence score (0–1) for the review.

Return the response in the following JSON format:
{
    "disease": "string",
    "source_filename": "string",
    "accuracy_summary": {
        "overall_accuracy": "string (\"high\"|\"moderate\"|\"low\")",
        "factual_errors": [
            {
                "mcq_id": "string or number",
                "issue": "short text",
                "correction": "short text"
            }
        ]
    },
    "spelling_grammar": [
        {
            "mcq_id": "string or number",
            "field": "string (\"question\"|\"option\"|\"explanation\")",
            "original": "string",
            "corrected": "string"
        }
    ],
    "quality": {
        "score": "integer 1-5",
        "issues": ["string"]
    },
    "suggestions": ["string"],
    "improved_examples": [
        {
            "mcq_id": "string or number",
            "question": "string",
            "options": ["string"],
            "correct_option": "index or string",
            "explanation": "string (1-2 sentences)"
        }
    ],
    "confidence": "number 0-1"
}"""

    # Create the user message with explicit structure
    user_message = {
        "disease": disease,
        "source_filename": source_filename,
        "mcqs": mcqs
    }
    
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_message, ensure_ascii=False)}
        ],
        "response_format": {"type": "json_object"}
    }

def validate_response(resp_json: Any) -> bool:
    return isinstance(resp_json, dict)

def extract_json_from_response(response: Dict[str, Any]) -> Any:
    """Extract JSON from DeepSeek response"""
    try:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return None
        
        # Try to parse the content as JSON
        return json.loads(content)
    except json.JSONDecodeError:
        # If it's not valid JSON, return the raw content
        logger.warning("Response content is not valid JSON")
        return content
    except Exception as e:
        logger.error("Error extracting JSON from response: %s", e)
        return None

# === API call with retries ===
def call_deepseek_with_retries(session: requests.Session, payload: Dict[str, Any], fname: str) -> Any:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    attempt = 0
    while attempt <= MAX_RETRIES:
        try:
            resp = session.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            # Raise for HTTP errors (4xx/5xx)
            resp.raise_for_status()
            # Expect JSON response
            return resp.json()
        except requests.exceptions.HTTPError as he:
            status = getattr(he.response, "status_code", None)
            # Retry on server errors (5xx)
            if status and 500 <= status < 600 and attempt < MAX_RETRIES:
                attempt += 1
                sleep = (BACKOFF_FACTOR ** attempt) + RATE_LIMIT_SECONDS
                logger.warning("Server error %s for %s, retry %d/%d after %.1fs", status, fname, attempt, MAX_RETRIES, sleep)
                time.sleep(sleep)
                continue
            # For client errors, do not retry
            logger.error("HTTP error for %s: %s", fname, he)
            # Try to get error details
            try:
                error_detail = he.response.json()
                logger.error("Error details: %s", error_detail)
            except:
                pass
            raise
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < MAX_RETRIES:
                attempt += 1
                sleep = (BACKOFF_FACTOR ** attempt) + RATE_LIMIT_SECONDS
                logger.warning("Network error for %s, retry %d/%d after %.1fs", fname, attempt, MAX_RETRIES, sleep)
                time.sleep(sleep)
                continue
            logger.error("Network failure for %s: %s", fname, e)
            raise
        except ValueError as ve:
            # JSON decode error
            logger.error("Invalid JSON response for %s: %s", fname, ve)
            raise

# === Worker ===
def process_file(path: Path, semaphore: Semaphore) -> Dict[str, Any]:
    fname = path.name
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        logger.error("Skipping %s: failed to read JSON (%s)", fname, e)
        return {"disease": None, "source_filename": fname, "error": f"read_error: {e}"}

    disease = data.get("disease") or path.stem
    mcqs = data.get("mcqs") or []

    payload = build_payload(disease, fname, mcqs)

    # Each thread uses its own Session for connection pooling
    session = requests.Session()

    # Acquire semaphore to ensure we don't exceed concurrency
    with semaphore:
        try:
            api_response = call_deepseek_with_retries(session, payload, fname)
            # Extract the actual JSON content from the API response
            result = extract_json_from_response(api_response)
            
            if result is None:
                logger.warning("Empty response for %s", fname)
                return {"disease": disease, "source_filename": fname, "error": "Empty response from API"}
                
            # If the response is a string (not JSON), convert it to a dict
            if isinstance(result, str):
                result = {"disease": disease, "source_filename": fname, "raw_response": result}
            else:
                # Ensure disease and source_filename are included
                if "disease" not in result:
                    result["disease"] = disease
                if "source_filename" not in result:
                    result["source_filename"] = fname
                    
        except Exception as e:
            logger.exception("API call failed for %s", fname)
            return {"disease": disease, "source_filename": fname, "error": str(e)}

    # Validate and return
    if not validate_response(result):
        logger.warning("Unexpected response type for %s; saving raw response", fname)
        return {"disease": disease, "source_filename": fname, "raw_response": result}

    return result

# === Main ===
def main():
    if not FOLDER.exists() or not FOLDER.is_dir():
        logger.error("Folder does not exist: %s", FOLDER)
        return

    files = sorted([p for p in FOLDER.iterdir() if p.suffix.lower() == ".json"])
    if not files:
        logger.info("No JSON files found in folder: %s", FOLDER)
        return

    semaphore = Semaphore(MAX_CONCURRENT)
    results = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as exe:
        future_to_path = {exe.submit(process_file, p, semaphore): p for p in files}
        for fut in as_completed(future_to_path):
            path = future_to_path[fut]
            fname = path.name
            try:
                result = fut.result()
            except Exception as e:
                logger.exception("Unhandled exception processing %s", fname)
                result = {"disease": None, "source_filename": fname, "error": str(e)}

            # Determine output filename
            disease_name = result.get("disease") or path.stem
            out_name = f"review_{safe_filename(disease_name)}.json"
            out_path = FOLDER / out_name

            # Save result atomically
            try:
                atomic_write(out_path, result)
                logger.info("Saved review for %s -> %s", fname, out_name)
            except Exception as e:
                logger.exception("Failed to write review for %s: %s", fname, e)

    logger.info("All files processed.")

if __name__ == "__main__":
    main()