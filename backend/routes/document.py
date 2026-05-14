from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from services.sarvam import extract_text_from_image, translate_text, text_to_speech
from services.llm import explain_prescription

router = APIRouter()


# ─── Full Document Pipeline ────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    target_language: str = Form(default="en-IN")
):
    try:
        # Step 1: OCR
        file_bytes = await file.read()
        ocr_text = extract_text_from_image(file_bytes, file.filename)

        if not ocr_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from document. Please upload a clearer image.")

        # Step 2: Explain prescription via sarvam-m
        explanation = explain_prescription(ocr_text)

        # Step 3: Translate summary and instructions if not English
        if not target_language.startswith("en"):
            explanation["summary"] = translate_text(explanation["summary"], "en-IN", target_language)
            explanation["instructions"] = [
                translate_text(inst, "en-IN", target_language)
                for inst in explanation["instructions"]
            ]
            for med in explanation["medications"]:
                med["purpose"] = translate_text(med["purpose"], "en-IN", target_language)
                med["side_effects"] = translate_text(med["side_effects"], "en-IN", target_language)

        return {
            "ocr_text": ocr_text,
            "explanation": explanation,
            "target_language": target_language
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Speak Document Summary ────────────────────────────────────────────────

@router.post("/speak-summary")
async def speak_summary(
    text: str = Form(...),
    language_code: str = Form(default="hi-IN"),
    speaker: str = Form(default="auto")
):
    try:
        audio_bytes = text_to_speech(text, language_code, speaker)
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=summary.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))