#!/usr/bin/env python3

import pandas as pd
import json
import os
import sys
import time
import requests
from pathlib import Path

API_URL = "https://api.groq.com/openai/v1/chat/completions"
model = "llama-3.3-70b-versatile"

API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
]
current_key_index = 0

def get_next_key():
    global current_key_index
    key = API_KEYS[current_key_index % len(API_KEYS)]
    current_key_index += 1
    return key


IMPUTABLE_FIELDS = [
    'Carrosserie',
    'Puissance_ch',
    'Cylindree',
    'Nombre_places',
    'Nombre_portes',
    'Transmission',
]


def call_llm(prompt, max_retries=3):
    keys_tried = 0
    total_keys = len(API_KEYS)
    
    for attempt in range(max_retries * total_keys):
        api_key = get_next_key()
        
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 429:
                keys_tried += 1
                if keys_tried >= total_keys:
                    wait_time = 2 ** (attempt // total_keys)
                    print(f"\nAll {total_keys} keys rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    keys_tried = 0
                else:
                    print(f"\nKey rate limited, rotating to next key...")
                continue
            
            if response.ok:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"\nAPI error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"\nTimeout on attempt {attempt + 1}")
        except Exception as e:
            print(f"\nError: {e}")
        
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


def impute_row(row, missing_cols, all_columns):
    available = {col: str(val) for col, val in row.items() if pd.notna(val) and str(val).strip()}
    missing_imputable = [col for col in missing_cols if col in IMPUTABLE_FIELDS]
    
    if not missing_imputable:
        return {}
    
    car_info = f"{available.get('Marque', '')} {available.get('Modele', '')}"
    title = available.get('Title', '')
    
    prompt = f"""You are an automotive expert. Fill in the missing car specifications.

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
    print(f"Using {len(API_KEYS)} API key(s) for rotation")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
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
    csv_files = []
    for f in sorted(script_dir.glob("*.csv")):
        if "_imputed" not in f.stem:
            csv_files.append(f)
    return csv_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Impute missing car data using LLM')
    parser.add_argument('-l', '--limit', type=int, help='Limit rows to process')
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between API calls')
    parser.add_argument('-k', '--keys', help='Comma-separated API keys (overrides env vars)')

    args = parser.parse_args()

    if args.keys:
        API_KEYS.clear()
        API_KEYS.extend([k.strip() for k in args.keys.split(",") if k.strip()])

    if not API_KEYS:
        print("Error: No API keys configured!")
        print("Add your keys to the API_KEYS list in imputer.py or use -k flag")
        sys.exit(1)

    csv_files = find_csv_files()

    if not csv_files:
        print("No CSV files found in the script directory.")
        sys.exit(0)

    print(f"Found {len(csv_files)} CSV file(s) to impute:")
    for f in csv_files:
        print(f"  - {f.name}")
    print("=" * 50)

    for csv_file in csv_files:
        output_file = csv_file.parent / f"{csv_file.stem}_imputed{csv_file.suffix}"
        print(f"\nProcessing: {csv_file.name} -> {output_file.name}")
        impute_csv(str(csv_file), str(output_file), args.limit, args.delay)