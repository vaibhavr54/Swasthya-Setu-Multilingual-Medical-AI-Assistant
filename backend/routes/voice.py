from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from services.sarvam import speech_to_text, text_to_speech, translate_text, detect_language
from services.llm import analyze_symptoms

router = APIRouter()


# ─── Speech to Text ────────────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language_code: str = Form(default="unknown")
):
    try:
        audio_bytes = await audio.read()
        result = speech_to_text(audio_bytes, language_code)
        transcript = result.get("transcript", "")
        detected_lang = result.get("language_code", "en-IN")
        return {
            "transcript": transcript,
            "detected_language": detected_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Full Voice Triage Pipeline ────────────────────────────────────────────

@router.post("/triage")
async def voice_triage(
    audio: UploadFile = File(...),
    language_code: str = Form(default="unknown")
):
    try:
        # Step 1: Transcribe
        audio_bytes = await audio.read()
        stt_result = speech_to_text(audio_bytes, language_code)
        transcript = stt_result.get("transcript", "")
        detected_lang = stt_result.get("language_code", "en-IN")

        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio. Please speak clearly and try again.")

        # Step 2: Translate to English for LLM if not English
        text_for_llm = transcript
        if not detected_lang.startswith("en"):
            text_for_llm = translate_text(transcript, detected_lang, "en-IN")

        # Step 3: Analyze symptoms via sarvam-m
        triage_result = analyze_symptoms(text_for_llm)

        # Step 4: Translate ALL fields to patient's language
        if not detected_lang.startswith("en"):
            triage_result["summary"] = translate_text(triage_result["summary"], "en-IN", detected_lang)
            triage_result["urgency_message"] = translate_text(triage_result["urgency_message"], "en-IN", detected_lang)
            triage_result["recommended_action"] = translate_text(triage_result["recommended_action"], "en-IN", detected_lang)
            triage_result["possible_conditions"] = [
                translate_text(c, "en-IN", detected_lang)
                for c in triage_result.get("possible_conditions", [])
            ]
            triage_result["follow_up_questions"] = [
                translate_text(q, "en-IN", detected_lang)
                for q in triage_result.get("follow_up_questions", [])
            ]

        return {
            "transcript": transcript,
            "detected_language": detected_lang,
            "triage": triage_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Text to Speech ────────────────────────────────────────────────────────

@router.post("/speak")
async def speak_text(
    text: str = Form(...),
    language_code: str = Form(default="hi-IN"),
    speaker: str = Form(default="auto")
):
    try:
        audio_bytes = text_to_speech(text, language_code, speaker)
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=response.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/followup")
async def voice_followup(
    question_audio: UploadFile = File(None),
    question_text: str = Form(default=""),
    language_code: str = Form(default="en-IN"),
    triage_context: str = Form(...),
    history: str = Form(default="[]")
):
    import json
    from services.llm import answer_followup

    try:
        # Get question — either from audio or text
        if question_audio and question_audio.filename:
            audio_bytes = await question_audio.read()
            stt_result = speech_to_text(audio_bytes, language_code)
            question_en = stt_result.get("transcript", "")
            detected_lang = stt_result.get("language_code", language_code)
        else:
            question_en = question_text
            detected_lang = language_code

        if not question_en.strip():
            raise HTTPException(status_code=400, detail="No question provided.")

        # Translate question to English if needed
        if not detected_lang.startswith("en"):
            question_en = translate_text(question_en, detected_lang, "en-IN")

        # Parse context and history
        context = json.loads(triage_context)
        conv_history = json.loads(history)

        # Get answer in English
        answer_en = answer_followup(question_en, context, "triage", conv_history)

        # Translate answer back to patient's language
        answer_translated = answer_en
        if not detected_lang.startswith("en"):
            answer_translated = translate_text(answer_en, "en-IN", detected_lang)

        return {
            "question": question_text or stt_result.get("transcript", question_en),
            "answer": answer_translated,
            "detected_language": detected_lang,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))