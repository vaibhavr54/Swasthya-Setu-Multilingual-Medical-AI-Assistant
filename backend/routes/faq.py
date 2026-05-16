from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from fastapi.responses import Response
from services.faq_store import semantic_search, get_faq_count
from services.llm import chat_completion
from services.sarvam import translate_text, text_to_speech, speech_to_text

router = APIRouter()


@router.get("/health")
def faq_health():
    return {"status": "ok", "faq_count": get_faq_count()}


@router.post("/search")
async def faq_search(
    query: str = Form(...),
    language_code: str = Form(default="en-IN"),
    n_results: int = Form(default=3)
):
    """
    Semantic FAQ search + RAG answer generation.
    1. Translate query to English if needed
    2. Semantic search in ChromaDB
    3. Generate contextual answer via sarvam-m
    4. Translate answer back to user's language
    """
    try:
        # Step 1: Translate query to English for semantic search
        query_en = query
        if not language_code.startswith("en"):
            query_en = translate_text(query, language_code, "en-IN")

        # Step 2: Semantic search
        matched_faqs = semantic_search(query_en, n_results=n_results)

        if not matched_faqs:
            raise HTTPException(status_code=404, detail="No relevant FAQs found")

        # Step 3: Build context from top matches
        context = "\n\n".join([
            f"Q: {faq['question']}\nA: {faq['answer']}"
            for faq in matched_faqs
        ])

        # Step 4: Generate RAG answer via sarvam-m
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful medical information assistant for Indian patients.
Using the following medical FAQ context, answer the patient's question clearly and simply.
Keep your answer under 4 sentences. Be warm, clear, and easy to understand.
If the context doesn't fully answer the question, say so and suggest consulting a doctor.

Context:
{context}"""
            },
            {
                "role": "user",
                "content": f"Patient question: {query_en}"
            }
        ]

        answer_en = chat_completion(messages, reasoning="low")

        # Strip think tags
        if "<think>" in answer_en and "</think>" in answer_en:
            answer_en = answer_en.split("</think>")[-1].strip()

        # Step 5: Translate answer to patient's language
        answer_translated = answer_en
        if not language_code.startswith("en"):
            answer_translated = translate_text(answer_en, "en-IN", language_code)

        return {
            "query": query,
            "query_en": query_en,
            "answer": answer_translated,
            "answer_en": answer_en,
            "language_code": language_code,
            "matched_faqs": matched_faqs,
            "rag_context_used": len(matched_faqs)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-voice")
async def faq_search_voice(
    audio: UploadFile = File(...),
    language_code: str = Form(default="unknown")
):
    """Voice query for FAQ — STT → semantic search → RAG → TTS response."""
    try:
        # STT
        audio_bytes = await audio.read()
        stt_result = speech_to_text(audio_bytes, language_code)
        transcript = stt_result.get("transcript", "")
        detected_lang = stt_result.get("language_code", "en-IN")

        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        # Translate to English
        query_en = transcript
        if not detected_lang.startswith("en"):
            query_en = translate_text(transcript, detected_lang, "en-IN")

        # Semantic search
        matched_faqs = semantic_search(query_en, n_results=3)
        if not matched_faqs:
            raise HTTPException(status_code=404, detail="No relevant FAQs found")

        # RAG answer
        context = "\n\n".join([
            f"Q: {faq['question']}\nA: {faq['answer']}"
            for faq in matched_faqs
        ])
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful medical information assistant.
Answer the patient's question simply using this context. Max 3 sentences.

Context:
{context}"""
            },
            {"role": "user", "content": query_en}
        ]
        answer_en = chat_completion(messages, reasoning="low")
        if "<think>" in answer_en and "</think>" in answer_en:
            answer_en = answer_en.split("</think>")[-1].strip()

        answer_translated = answer_en
        if not detected_lang.startswith("en"):
            answer_translated = translate_text(answer_en, "en-IN", detected_lang)

        # TTS
        audio_bytes_out = text_to_speech(answer_translated, detected_lang)

        return Response(
            content=audio_bytes_out,
            media_type="audio/wav",
            headers={
                "X-Transcript": transcript,
                "X-Answer": answer_translated[:200],
                "X-Language": detected_lang
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))