import io
import json
import os
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import AutofillRequest, ChatRequest
from api.services.csv_data import _gemini_csv_answer
from api.state import gemini_client, groq_client, genai, Image

router = APIRouter()

@router.post("/chat")
async def chat_text(req: ChatRequest):
    try:
        question = (req.question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is empty")
        answer = _gemini_csv_answer(question)
        return {"answer": answer, "transcription": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/audio")
async def chat_audio(file: UploadFile = File(...)):
    if not groq_client:
        raise HTTPException(status_code=503, detail="Groq API is not configured.")
    
    ext = file.filename.split(".")[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(tmp_path, audio_file.read()),
                model="whisper-large-v3",
                prompt="Tunisian Arabic, Darija tunisien, English, karhba, b9adeh, soum, krahb."
            )
        question_text = transcription.text.strip()
        
        if not question_text:
            return {"answer": "Sorry, I couldn't hear your question.", "transcription": ""}

        answer = _gemini_csv_answer(question_text)

        return {
            "transcription": question_text,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/autofill")
async def autofill_car(req: AutofillRequest):
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is empty")

    try:
        system_prompt = """Tu es un expert automobile tunisien. L'utilisateur décrit une voiture et tu dois extraire les caractéristiques techniques pour une prédiction de prix.
Réponds TOUJOURS en JSON valide avec les champs exacts (met null si tu ne peux pas déterminer). 
{
  "matched": true,
  "message": "<court résumé>",
  "Marque": "<marque>",
  "Energie": "<Essence|Diesel|Electrique|Hybride|GPL>",
  "Boite_vitesse": "<Manuelle|Automatique>",
  "Transmission": "<Traction avant|Propulsion|Intégrale|4x4>",
  "Carrosserie": "<Berline|SUV|Citadine|Compacte|Break|Cabriolet|Coupé|Pick-up|Monospace|Utilitaire>",
  "Puissance_fiscale": <int CV fiscaux>,
  "Puissance_ch": <int chevaux>,
  "Nombre_places": <int>,
  "Nombre_portes": <int>,
  "Cylindree": <int cc>,
  "Kilometrage": null,
  "age_voiture": <int âge en années depuis 2026>,
  "Gouvernorat": null
}"""
        contents = []
        for msg in req.history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(genai.types.Content(role=role, parts=[genai.types.Part(text=msg.get("text", ""))]))
        contents.append(genai.types.Content(role="user", parts=[genai.types.Part(text=req.query.strip())]))

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=contents,
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1, max_output_tokens=1024),
        )

        raw = response.text.strip()
        if raw.startswith("```"): raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"): raw = raw.rsplit("```", 1)[0]
        result = json.loads(raw.strip())
        result.setdefault("matched", True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-car-image")
async def analyze_car_image(file: UploadFile = File(...)):
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini non configuré")
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        system_prompt = """Tu es un expert automobile. Identifie la marque, le modèle et l'année (ou année approximative) de la voiture sur cette image.
Réponds TOUJOURS en JSON valide: {"marque": "<Marque>", "modele": "<Modèle>", "annee": <Année en entier ou null>}"""

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[image, "Identifie cette voiture."],
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1, max_output_tokens=512),
        )
        
        raw = response.text.strip()
        if raw.startswith("```json"): raw = raw[7:]
        elif raw.startswith("```"): raw = raw[3:]
        if raw.endswith("```"): raw = raw[:-3]
        return json.loads(raw.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
