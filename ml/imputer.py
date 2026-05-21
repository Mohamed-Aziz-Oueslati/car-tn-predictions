#!/usr/bin/env python3

import pandas as pd
import json
import os
import re
import time
import unicodedata
from pathlib import Path
import httpx
from groq import Groq

model = "llama-3.3-70b-versatile"

API_KEY = os.getenv("GROQ_API_KEY", "").strip()
HTTP_CLIENT = httpx.Client()


def prompt_for_api_key(reason):
    while True:
        value = input(f"{reason}\nEnter a new Groq API key (Ctrl+C to abort): ").strip()
        if value:
            return value


IMPUTABLE_FIELDS = [
    'Carrosserie',
    'Puissance_ch',
    'Cylindree',
    'Nombre_places',
    'Nombre_portes',
    'Transmission',
]

GOVERNORATE_STOPWORDS = {
    "dt",
    "tnd",
    "dinar",
    "prix",
    "negociable",
    "nego",
}


def call_llm(prompt, max_retries=3):
    global API_KEY

    if not API_KEY:
        API_KEY = prompt_for_api_key("No Groq API key configured.")

    client = Groq(api_key=API_KEY, http_client=HTTP_CLIENT)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            status_code = getattr(e, "status_code", None)
            if status_code == 429:
                API_KEY = prompt_for_api_key("Groq rate limit hit for current key.")
                client = Groq(api_key=API_KEY, http_client=HTTP_CLIENT)
                continue

            print(f"\nAPI error: {e}")
        
        time.sleep(0.5)
    
    return None


def parse_json_response(text):
    if not text:
        return {}
    
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if part.strip().startswith("json"):
                text = part.replace("json", "", 1).strip()
                break
            elif part.strip().startswith("{"):
                text = part.strip()
                break
    
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    
    return {}


def normalize_text(value):
    value = str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower().strip()


def normalize_governorat_text(value):
    value = normalize_text(value)
    value = re.sub(r"[^a-z\s]", " ", value)
    return " ".join(value.split())


def title_case_words(words):
    return " ".join(word.capitalize() for word in words)


def clean_governorat_name(value):
    normalized = normalize_governorat_text(value)
    if not normalized:
        return None

    words = normalized.split()
    if len(words) > 2:
        return None

    if any(word in GOVERNORATE_STOPWORDS for word in words):
        return None

    return title_case_words(words)


def llm_extract_governorat(text):
    prompt = (
        "Extract the Tunisian governorate name from the input. "
        "Return only JSON: {\"Gouvernorat\": \"NAME\"} or {\"Gouvernorat\": null}.\n"
        f"Input: {text}"
    )

    response = call_llm(prompt)
    values = parse_json_response(response)
    value = values.get("Gouvernorat")
    if not value or value == "null":
        return None

    return clean_governorat_name(value)


def clean_governorat_column(df, llm_delay=0.2):
    if "Gouvernorat" not in df.columns:
        return 0

    raw_values = df["Gouvernorat"].dropna().unique()
    value_map = {}

    for raw_value in raw_values:
        text = str(raw_value).strip()
        if not text:
            continue

        extracted = llm_extract_governorat(text)
        if extracted:
            value_map[raw_value] = extracted

        if llm_delay > 0:
            time.sleep(llm_delay)

    cleaned_count = 0
    for idx, value in df["Gouvernorat"].items():
        if pd.isna(value):
            continue

        text = str(value).strip()
        if not text:
            continue

        extracted = value_map.get(value)
        if extracted and extracted != text:
            df.at[idx, "Gouvernorat"] = extracted
            cleaned_count += 1

    return cleaned_count


def impute_row(row, missing_cols, all_columns):
    available = {col: str(val) for col, val in row.items() if pd.notna(val) and str(val).strip()}
    missing_imputable = [col for col in missing_cols if col in IMPUTABLE_FIELDS]
    
    if not missing_imputable:
        return {}
    
    car_info = f"{available.get('Marque', '')} {available.get('Modele', '')}"
    title = available.get('Title', '')
    
    prompt = f"""You are an automotive expert focused on the Tunisian car market. Fill in the missing car specifications with values typical for Tunisia listings.

Car: {car_info}
Title: {title}

Available information:
- Brand: {available.get('Marque', 'unknown')}
- Model: {available.get('Modele', 'unknown')}
- Fuel: {available.get('Energie', 'unknown')}
- Power (fiscal): {available.get('Puissance_fiscale', 'unknown')}
- Engine (cc): {available.get('Cylindree', 'unknown')}

Missing fields to fill: {', '.join(missing_imputable)}

Field definitions:
- Carrosserie: Body type in French (SUV, Berline, Compacte, Citadine, Coupé, Cabriolet, Break, Monospace, Pick-up, Utilitaire)
- Puissance_ch: Engine horsepower (numeric value only)
- Cylindree: Engine displacement in cc (numeric value only)
- Nombre_places: Number of seats (typically 2, 4, 5, 7, 8, 9)
- Nombre_portes: Number of doors (typically 2, 3, 4, 5)
- Transmission: Drive type (Traction = FWD, Propulsion = RWD, Intégrale = AWD)

Market guidance:
- Prioritize common Tunisia trims, engines, and body styles for this brand/model.
- If unsure, return null for that field rather than guessing.

Return ONLY a valid JSON object with the missing fields. Use null if truly unknown.
Example: {{"Carrosserie": "SUV", "Puissance_ch": 150}}"""

    response = call_llm(prompt)
    values = parse_json_response(response)
    
    cleaned = {}
    for col, val in values.items():
        if col not in missing_imputable or val is None or val == "null":
            continue
        
        if col in ['Puissance_ch', 'Cylindree']:
            try:
                cleaned[col] = float(str(val).replace(',', '.'))
            except:
                pass
        elif col in ['Nombre_places', 'Nombre_portes']:
            try:
                cleaned[col] = int(float(str(val)))
            except:
                pass
        else:
            cleaned[col] = str(val)
    
    return cleaned


def impute_csv(input_file, output_file=None, limit=None, delay=0.5):
    print(f"Loading {input_file}...")
    print("Using interactive API key prompts on rate limits")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    cleaned_governorat = clean_governorat_column(df)
    if cleaned_governorat:
        print(f"Cleaned {cleaned_governorat} Gouvernorat value(s)")
    
    missing_mask = df[IMPUTABLE_FIELDS].isna().any(axis=1)
    rows_to_process = df[missing_mask].index.tolist()
    
    if limit:
        rows_to_process = rows_to_process[:limit]
    
    print(f"Found {len(rows_to_process)} rows with missing imputable fields")
    print("-" * 50)
    
    imputed_count = 0
    total_fields_filled = 0
    
    for idx, row_idx in enumerate(rows_to_process):
        row = df.loc[row_idx]
        missing_cols = [col for col in IMPUTABLE_FIELDS if pd.isna(row[col])]
        
        if not missing_cols:
            continue
        
        car_name = f"{row.get('Marque', '')} {row.get('Modele', '')}"
        print(f"[{idx+1}/{len(rows_to_process)}] {car_name} - missing: {', '.join(missing_cols)}", end="")
        
        imputed_values = impute_row(row.to_dict(), missing_cols, df.columns.tolist())
        
        if imputed_values:
            for col, val in imputed_values.items():
                df.at[row_idx, col] = val
            total_fields_filled += len(imputed_values)
            imputed_count += 1
            print(f" -> filled {len(imputed_values)} fields")
        else:
            print(" -> no values imputed")
        
        if delay > 0:
            time.sleep(delay)
    
    print("-" * 50)
    print(f"Imputed {total_fields_filled} fields across {imputed_count} rows")
    
    if not output_file:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_imputed{input_path.suffix}"
    
    df.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")
    
    return df


def find_csv_files():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    csv_files = []
    for f in sorted(project_root.glob("*.csv")):
        if "_imputed" not in f.stem:
            csv_files.append(f)
    return csv_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Impute missing car data using LLM')
    parser.add_argument('-l', '--limit', type=int, help='Limit rows to process')
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between API calls')
    parser.add_argument('-k', '--key', help='Groq API key (overrides GROQ_API_KEY)')

    args = parser.parse_args()

    if args.key:
        API_KEY = args.key.strip()

    csv_files = find_csv_files()

    if not csv_files:
        print("No CSV files found in the script directory.")
        raise SystemExit(0)

    print(f"Found {len(csv_files)} CSV file(s) to impute:")
    for f in csv_files:
        print(f"  - {f.name}")
    print("=" * 50)

    for csv_file in csv_files:
        output_file = csv_file.parent / f"{csv_file.stem}_imputed{csv_file.suffix}"
        print(f"\nProcessing: {csv_file.name} -> {output_file.name}")
        impute_csv(str(csv_file), str(output_file), args.limit, args.delay)
