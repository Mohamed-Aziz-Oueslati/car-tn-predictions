#!/usr/bin/env python3
"""
Car CSV Imputer using LLM (Groq API with Llama)
Fills in missing values in car data using AI inference.
"""

import pandas as pd
import json
import os
import sys
import time
import requests
from pathlib import Path

# Groq API configuration
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

# API Keys for rotation (add your keys here)
API_KEYS = [
    "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",
    "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",
    "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",
    "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",
]
current_key_index = 0

def get_next_key():
    """Get the next API key in rotation."""
    global current_key_index
    key = API_KEYS[current_key_index % len(API_KEYS)]
    current_key_index += 1
    return key


# Fields that can be imputed based on car knowledge
IMPUTABLE_FIELDS = [
    'Carrosserie',      # Body type: SUV, Berline, Hatchback, Coupe, etc.
    'Puissance_ch',     # Horsepower (can infer from model/engine)
    'Cylindree',        # Engine displacement
    'Nombre_places',    # Number of seats
    'Nombre_portes',    # Number of doors
    'Transmission',     # Traction, Propulsion, Intégrale
]


def call_llm(prompt, max_retries=3):
    """Call the Groq LLM API with retry logic and key rotation."""
    keys_tried = 0
    total_keys = len(API_KEYS)
    
    for attempt in range(max_retries * total_keys):  # Try each key multiple times
        api_key = get_next_key()
        
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 429:
                keys_tried += 1
                if keys_tried >= total_keys:
                    # All keys exhausted, wait before retrying
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
    """Extract JSON from LLM response."""
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
    """Impute missing values for a single row using LLM."""
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
    """Impute missing values in a car CSV file using LLM."""
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Impute missing car data using LLM')
    parser.add_argument('input', nargs='?', default='automobile_tn_data.csv', help='Input CSV file')
    parser.add_argument('-o', '--output', help='Output CSV file')
    parser.add_argument('-l', '--limit', type=int, help='Limit rows to process')
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between API calls')
    parser.add_argument('-k', '--keys', help='Comma-separated API keys (overrides env vars)')
    
    args = parser.parse_args()
    
    # Override keys if provided via CLI
    if args.keys:
        API_KEYS.clear()
        API_KEYS.extend([k.strip() for k in args.keys.split(",") if k.strip()])
    
    if not API_KEYS:
        print("Error: No API keys configured!")
        print("Add your keys to the API_KEYS list in imputer.py or use -k flag")
        sys.exit(1)
    
    impute_csv(args.input, args.output, args.limit, args.delay)