import glob
import pandas as pd
from fastapi import HTTPException

from api.state import gemini_client, genai

def _load_imputed_csvs() -> pd.DataFrame:
    csv_files = sorted(glob.glob("*_imputed.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail="No imputed CSV data files found")
    return pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

def _build_csv_context(df: pd.DataFrame) -> str:
    row_count = len(df)
    columns = df.columns.tolist()
    sample = df.head(5).to_markdown(index=False)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        numeric_summary = df[numeric_cols].describe().round(2).to_string()
    else:
        numeric_summary = "None"

    categorical_cols = [c for c in columns if c not in numeric_cols][:10]
    cat_lines = []
    for col in categorical_cols:
        try:
            vc = df[col].dropna().astype(str).value_counts().head(5)
        except Exception:
            continue
        if not vc.empty:
            pairs = ", ".join([f"{k}: {v}" for k, v in vc.items()])
            cat_lines.append(f"{col}: {pairs}")
    cat_summary = "\n".join(cat_lines) if cat_lines else "None"

    return (
        "CSV context:\n"
        f"Rows: {row_count}\n"
        f"Columns ({len(columns)}): {', '.join(columns)}\n\n"
        "Sample rows:\n"
        f"{sample}\n\n"
        "Numeric summary:\n"
        f"{numeric_summary}\n\n"
        "Top categorical values:\n"
        f"{cat_summary}"
    )

def _gemini_csv_answer(question: str) -> str:
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")

    df = _load_imputed_csvs()
    context = _build_csv_context(df)

    system_prompt = (
        "You are an expert assistant for the Tunisian car market. "
        "Answer using only the provided CSV context. "
        "If the answer cannot be determined, say so. "
        "Reply concisely and in the user's language."
    )

    user_text = f"{context}\n\nQuestion: {question}"

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[genai.types.Content(role="user", parts=[genai.types.Part(text=user_text)])],
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
            max_output_tokens=1024,
        ),
    )

    return response.text.strip() if response and response.text else ""

SYSTEM_PROMPT_CHATBOT = """
You are an expert assistant for the Tunisian car market.
You have been given access to a database of cars (DataFrame).

IMPORTANT DIRECTIVES:
1. ALWAYS answer politely and concisely.
2. If the user's question is in English, reply in English.
3. If the user's question is in Tunisian Darija (Tunisian dialect Arabic, e.g., "b9adeh", "karhba", "chnowa rayek"), you MUST reply in Tunisian Darija (you can use Latin/Franco-Arabic characters or Arabic letters depending on how the user typed/spoke).
4. Use your pandas tools to search for exact information from the database (e.g., average prices, mileage, brand availability).
"""
