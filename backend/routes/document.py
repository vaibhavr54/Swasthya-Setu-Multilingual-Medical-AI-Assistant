from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from services.llm import explain_prescription
from services.sarvam import extract_text_from_image, translate_text, text_to_speech, speech_to_text

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
    
@router.post("/followup")
async def document_followup(
    question_audio: UploadFile = File(None),
    question: str = Form(default=""),
    language_code: str = Form(default="en-IN"),
    prescription_context: str = Form(...),
    history: str = Form(default="[]")
):
    import json
    from services.llm import answer_followup

    try:
        # Get question from audio or text
        if question_audio and question_audio.filename:
            audio_bytes = await question_audio.read()
            stt_result = speech_to_text(audio_bytes, language_code)
            question_transcript = stt_result.get("transcript", "")
            detected_lang = stt_result.get("language_code", language_code)
        else:
            question_transcript = question
            detected_lang = language_code

        if not question_transcript.strip():
            raise HTTPException(status_code=400, detail="No question provided.")

        # Translate to English for LLM
        question_en = question_transcript
        if not detected_lang.startswith("en"):
            question_en = translate_text(question_transcript, detected_lang, "en-IN")

        context = json.loads(prescription_context)
        conv_history = json.loads(history)

        answer_en = answer_followup(question_en, context, "prescription", conv_history)

        # Translate answer back
        answer_translated = answer_en
        if not detected_lang.startswith("en"):
            answer_translated = translate_text(answer_en, "en-IN", detected_lang)

        return {
            "question": question_transcript,
            "answer": answer_translated,
            "language_code": detected_lang,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))