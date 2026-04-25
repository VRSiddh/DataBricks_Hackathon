"""
Merge Elchemist (4670 schemes) + Bilingual Razvi (451 schemes) datasets
into a single unified gov_schemes_full.csv for Nyaya-Sahayak.

Usage:
  1. Download Elchemist dataset from Kaggle → extract into data/elchemist/
     Expected file: data/elchemist/schemes.csv
  2. Download Bilingual dataset from Kaggle → extract into data/bilingual/
     Expected file: data/bilingual/*.csv (or JSON files)
  3. Run: python data/prepare_schemes.py
  4. Output: data/gov_schemes_full.csv (unified, deduplicated)
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_FILE = HERE / "gov_schemes_full.csv"

# ─── Column mapping for unified format ──────────────────────────────────────

UNIFIED_FIELDS = [
    "scheme_id",
    "scheme_name",
    "short_title",
    "ministry",           # department/ministry
    "category",           # primary category
    "sub_category",
    "level",              # Central / State / UT
    "state_ut",           # specific state or "All"
    "target_beneficiaries",
    "eligibility_criteria",
    "eligibility_gender",
    "eligibility_min_age",
    "eligibility_max_age",
    "eligibility_income_limit",
    "eligibility_caste",
    "benefits",
    "application_process",
    "documents_required",
    "description_en",
    "description_hi",
    "source_url",
]


def safe_str(v):
    if v is None:
        return ""
    return str(v).strip()


def extract_gender_from_eligibility(text: str) -> str:
    """Try to infer gender requirement from eligibility text."""
    lower = text.lower()
    if any(kw in lower for kw in ["only women", "only for women", "female only", "women only", "girl child",
                                   "pregnant women", "lactating mother", "widow"]):
        return "Female"
    if any(kw in lower for kw in ["only men", "male only", "only for men"]):
        return "Male"
    return "All"


def extract_age_from_eligibility(text: str):
    """Try to extract min/max age from eligibility text."""
    min_age, max_age = 0, 99
    # Patterns: "age between 18 and 40", "age 18-40", "minimum age 18", "above 18 years"
    between = re.search(r'age\s*(?:between|from|of)\s*(\d+)\s*(?:to|and|-)\s*(\d+)', text, re.IGNORECASE)
    if between:
        min_age = int(between.group(1))
        max_age = int(between.group(2))
        return min_age, max_age

    above = re.search(r'(?:above|minimum|at least|more than)\s*(\d+)\s*years', text, re.IGNORECASE)
    if above:
        min_age = int(above.group(1))

    below = re.search(r'(?:below|under|up to|less than|maximum)\s*(\d+)\s*years', text, re.IGNORECASE)
    if below:
        max_age = int(below.group(1))

    return min_age, max_age


def extract_income_from_eligibility(text: str) -> float:
    """Try to extract income limit from eligibility text."""
    # Patterns: "income below Rs 2.5 lakh", "annual income up to 2,50,000"
    lakh_match = re.search(r'(?:income|earning).*?(?:below|under|up to|less than|not exceeding).*?(?:Rs\.?|₹)\s*([\d.]+)\s*lakh', text, re.IGNORECASE)
    if lakh_match:
        val = lakh_match.group(1).strip()
        if val:
            try:
                return float(val) * 100000
            except ValueError:
                pass

    rupee_match = re.search(r'(?:income|earning).*?(?:below|under|up to|less than).*?(?:Rs\.?|₹)\s*([\d,]+)', text, re.IGNORECASE)
    if rupee_match:
        val = rupee_match.group(1).replace(",", "").strip()
        if val:
            try:
                return float(val)
            except ValueError:
                pass

    return 0


def extract_caste_from_eligibility(text: str) -> str:
    """Try to extract caste/category from eligibility text."""
    lower = text.lower()
    cats = []
    if "sc" in lower or "scheduled caste" in lower:
        cats.append("SC")
    if "st" in lower or "scheduled tribe" in lower:
        cats.append("ST")
    if "obc" in lower or "other backward" in lower:
        cats.append("OBC")
    if "bpl" in lower or "below poverty" in lower:
        cats.append("BPL")
    if "ews" in lower or "economically weaker" in lower:
        cats.append("EWS")
    if "general" in lower and not cats:
        cats.append("General")
    return "/".join(cats) if cats else "All"


# ─── Loaders ────────────────────────────────────────────────────────────────


def load_elchemist() -> list[dict]:
    """Load the Elchemist dataset (schemes.csv with 4670 rows)."""
    schemes = []
    candidates = [
        HERE / "elchemist" / "schemes.csv",
        HERE / "elchemist" / "myscheme_india_govt_welfare_schemes.csv",
    ]
    # Also find any CSV in the elchemist folder
    elc_dir = HERE / "elchemist"
    if elc_dir.is_dir():
        for f in elc_dir.glob("*.csv"):
            if f not in candidates:
                candidates.append(f)

    csv_file = None
    for c in candidates:
        if c.is_file():
            csv_file = c
            break

    if csv_file is None:
        print("[WARN] Elchemist dataset not found. Expected CSV in data/elchemist/")
        print("       Download from: https://www.kaggle.com/datasets/elchemist/myscheme-india-govt-welfare-schemes")
        return []

    print(f"[INFO] Loading Elchemist data from: {csv_file}")

    with open(csv_file, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        print(f"[INFO] Elchemist columns: {cols}")

        for i, row in enumerate(reader):
            elig_text = safe_str(row.get("eligibility_criteria") or row.get("eligibility") or "")
            desc = safe_str(row.get("detailed_description") or row.get("brief_description") or row.get("description") or "")

            min_age, max_age = extract_age_from_eligibility(elig_text)
            gender = extract_gender_from_eligibility(elig_text)
            income = extract_income_from_eligibility(elig_text)
            caste = extract_caste_from_eligibility(elig_text)

            scheme = {
                "scheme_id": i + 1,
                "scheme_name": safe_str(row.get("scheme_name") or row.get("name") or ""),
                "short_title": safe_str(row.get("short_title") or ""),
                "ministry": safe_str(row.get("department") or row.get("ministry") or ""),
                "category": safe_str(row.get("categories") or row.get("category") or ""),
                "sub_category": safe_str(row.get("sub_categories") or row.get("sub_category") or ""),
                "level": safe_str(row.get("level") or ""),
                "state_ut": safe_str(row.get("state_ut") or row.get("state") or row.get("state_name") or "All"),
                "target_beneficiaries": safe_str(row.get("target_beneficiaries") or ""),
                "eligibility_criteria": elig_text,
                "eligibility_gender": gender,
                "eligibility_min_age": min_age,
                "eligibility_max_age": max_age,
                "eligibility_income_limit": income,
                "eligibility_caste": caste,
                "benefits": safe_str(row.get("benefits") or ""),
                "application_process": safe_str(row.get("application_process") or ""),
                "documents_required": safe_str(row.get("documents_required") or ""),
                "description_en": desc,
                "description_hi": "",  # Will be merged from bilingual dataset
                "source_url": safe_str(row.get("source_url") or row.get("url") or ""),
            }
            if scheme["scheme_name"]:
                schemes.append(scheme)

    print(f"[INFO] Loaded {len(schemes)} schemes from Elchemist dataset")
    return schemes


def load_bilingual() -> dict[str, dict]:
    """Load the bilingual dataset and return a dict keyed by normalized scheme name."""
    bilingual = {}
    bi_dir = HERE / "bilingual"

    if not bi_dir.is_dir():
        print("[WARN] Bilingual dataset directory not found: data/bilingual/")
        return {}

    # Try CSV files first
    csv_files = list(bi_dir.glob("*.csv"))
    json_files = list(bi_dir.glob("*.json")) + list(bi_dir.glob("**/*.json"))

    for csv_file in csv_files:
        print(f"[INFO] Loading bilingual CSV: {csv_file.name}")
        try:
            with open(csv_file, encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                cols = reader.fieldnames or []
                print(f"[INFO] Bilingual columns: {cols}")

                # Detect QA format (Zaker Razvi dataset)
                is_qa_format = "answer" in cols and "question" in cols

                for row in reader:
                    name = safe_str(row.get("scheme_name") or row.get("name") or "")
                    if not name:
                        continue
                    key = name.lower().strip()

                    if is_qa_format:
                        # QA format: answer = Hindi, answer_english = English
                        hindi_answer = safe_str(row.get("answer") or "")
                        hindi_question = safe_str(row.get("question") or "")
                        # Combine Q+A for a richer Hindi description
                        hindi_text = f"{hindi_question}\n{hindi_answer}" if hindi_question else hindi_answer
                        bilingual.setdefault(key, {"description_hi": ""})
                        existing_hi = bilingual[key].get("description_hi", "")
                        # Append multiple QA pairs for the same scheme
                        if existing_hi:
                            bilingual[key]["description_hi"] = existing_hi + "\n\n" + hindi_text
                        else:
                            bilingual[key]["description_hi"] = hindi_text
                    else:
                        # Direct description format
                        bilingual[key] = {
                            "description_hi": safe_str(
                                row.get("summary_hi") or row.get("description_hi") or
                                row.get("hindi_description") or row.get("hindi_summary") or
                                row.get("answer") or ""
                            ),
                            "eligibility_hi": safe_str(
                                row.get("eligibility_hi") or row.get("hindi_eligibility") or ""
                            ),
                            "benefits_hi": safe_str(
                                row.get("benefits_hi") or row.get("hindi_benefits") or ""
                            ),
                        }
        except Exception as e:
            print(f"[WARN] Failed to load CSV {csv_file}: {e}")

    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        name = safe_str(item.get("scheme_name") or item.get("name") or "")
                        if not name:
                            continue
                        key = name.lower().strip()
                        bilingual.setdefault(key, {})
                        bilingual[key]["description_hi"] = safe_str(
                            item.get("summary_hi") or item.get("description_hi") or
                            item.get("hindi_description") or bilingual[key].get("description_hi", "")
                        )
                elif isinstance(data, dict):
                    for k, v in data.items():
                        bilingual.setdefault(k.lower(), {})
                        if isinstance(v, dict):
                            bilingual[k.lower()]["description_hi"] = safe_str(v.get("hindi", ""))
        except Exception as e:
            print(f"[WARN] Failed to load JSON {json_file}: {e}")

    print(f"[INFO] Loaded bilingual data for {len(bilingual)} schemes")
    return bilingual


def load_existing_35() -> list[dict]:
    """Load our existing hand-crafted 35 schemes as fallback."""
    csv_file = HERE / "gov_schemes.csv"
    if not csv_file.is_file():
        return []

    schemes = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scheme = {field: safe_str(row.get(field, "")) for field in UNIFIED_FIELDS}
            scheme["scheme_id"] = int(row.get("scheme_id", 0) or 0)
            scheme["eligibility_min_age"] = int(row.get("eligibility_min_age", 0) or 0)
            scheme["eligibility_max_age"] = int(row.get("eligibility_max_age", 99) or 99)
            scheme["eligibility_income_limit"] = float(row.get("eligibility_income_limit", 0) or 0)
            schemes.append(scheme)
    print(f"[INFO] Loaded {len(schemes)} existing hand-crafted schemes")
    return schemes


# ─── Merge & Deduplicate ────────────────────────────────────────────────────


def normalize_name(name: str) -> str:
    """Normalize scheme name for deduplication."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def merge_datasets():
    """Merge all sources into a single unified dataset."""
    elchemist = load_elchemist()
    bilingual = load_bilingual()
    existing = load_existing_35()

    # Start with Elchemist as primary
    if elchemist:
        merged = elchemist
    else:
        # Fallback to existing if Elchemist not available
        merged = existing
        print("[WARN] Using existing 35-scheme dataset as primary (Elchemist not found)")

    # Merge bilingual Hindi descriptions
    hindi_merged = 0
    for scheme in merged:
        name_key = scheme["scheme_name"].lower().strip()
        if name_key in bilingual:
            bi = bilingual[name_key]
            if bi.get("description_hi") and not scheme.get("description_hi"):
                scheme["description_hi"] = bi["description_hi"]
                hindi_merged += 1

    # Also try fuzzy matching on normalized names
    bi_normalized = {normalize_name(k): v for k, v in bilingual.items()}
    for scheme in merged:
        if scheme.get("description_hi"):
            continue
        norm_key = normalize_name(scheme["scheme_name"])
        if norm_key in bi_normalized:
            bi = bi_normalized[norm_key]
            if bi.get("description_hi"):
                scheme["description_hi"] = bi["description_hi"]
                hindi_merged += 1

    print(f"[INFO] Merged Hindi descriptions for {hindi_merged} schemes")

    # Add existing hand-crafted schemes that aren't in the main dataset
    existing_names = {normalize_name(s["scheme_name"]) for s in merged}
    added_from_existing = 0
    for s in existing:
        norm = normalize_name(s["scheme_name"])
        if norm not in existing_names:
            s["scheme_id"] = len(merged) + 1
            merged.append(s)
            existing_names.add(norm)
            added_from_existing += 1

    if added_from_existing:
        print(f"[INFO] Added {added_from_existing} unique schemes from hand-crafted dataset")

    # Re-number IDs
    for i, s in enumerate(merged):
        s["scheme_id"] = i + 1

    # Deduplicate by normalized name
    seen = set()
    deduped = []
    for s in merged:
        key = normalize_name(s["scheme_name"])
        if key and key not in seen:
            seen.add(key)
            deduped.append(s)

    print(f"\n{'='*60}")
    print(f"TOTAL UNIQUE SCHEMES: {len(deduped)}")
    print(f"{'='*60}\n")

    return deduped


def write_output(schemes: list[dict]):
    """Write merged dataset to CSV."""
    with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=UNIFIED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for s in schemes:
            writer.writerow(s)
    print(f"[OK] Written {len(schemes)} schemes -> {OUT_FILE}")
    size_mb = OUT_FILE.stat().st_size / (1024 * 1024)
    print(f"     File size: {size_mb:.2f} MB")


if __name__ == "__main__":
    schemes = merge_datasets()
    if schemes:
        write_output(schemes)
    else:
        print("[ERROR] No schemes loaded. Please download the datasets first.")
        print("  1. https://www.kaggle.com/datasets/elchemist/myscheme-india-govt-welfare-schemes → data/elchemist/")
        print("  2. https://www.kaggle.com/datasets/zakerrazvi/indian-government-schemes-dataset-english-and-hindi → data/bilingual/")
        sys.exit(1)
