# ─── Sample data for evaluation ────────────────────────────────────────────
# These are ground-truth examples used to measure AI component quality

STT_SAMPLES = [
    {
        "id": "stt_001",
        "language": "en-IN",
        "description": "English diabetes symptoms",
        "expected_transcript": "I have been experiencing increased thirst and frequent urination for the past week",
    },
    {
        "id": "stt_002",
        "language": "hi-IN",
        "description": "Hindi fever symptoms",
        "expected_transcript": "मुझे बुखार है और सिर दर्द हो रहा है",
    },
    {
        "id": "stt_003",
        "language": "mr-IN",
        "description": "Marathi stomach pain",
        "expected_transcript": "मला पोटात दुखत आहे आणि उलटी होत आहे",
    },
]

TRANSLATION_SAMPLES = [
    {
        "id": "trans_001",
        "source_lang": "en-IN",
        "target_lang": "hi-IN",
        "source": "Take this medicine twice a day after meals",
        "reference": "यह दवा दिन में दो बार खाने के बाद लें",
    },
    {
        "id": "trans_002",
        "source_lang": "en-IN",
        "target_lang": "mr-IN",
        "source": "Please consult a doctor immediately",
        "reference": "कृपया ताबडतोब डॉक्टरांचा सल्ला घ्या",
    },
    {
        "id": "trans_003",
        "source_lang": "en-IN",
        "target_lang": "hi-IN",
        "source": "Your blood pressure is high, you need to rest",
        "reference": "आपका रक्तचाप अधिक है, आपको आराम करने की जरूरत है",
    },
    {
        "id": "trans_004",
        "source_lang": "en-IN",
        "target_lang": "ta-IN",
        "source": "Drink plenty of water and take rest",
        "reference": "நிறைய தண்ணீர் குடிங்க, ஓய்வு எடுங்க",
    },
]

TRIAGE_SAMPLES = [
    {
        "id": "triage_001",
        "symptoms": "I have mild cold with slight runny nose for 2 days",
        "expected_level": "LOW",
        "description": "Mild cold — should be LOW",
    },
    {
        "id": "triage_002",
        "symptoms": "I have chest pain radiating to my left arm and difficulty breathing",
        "expected_level": "HIGH",
        "description": "Cardiac symptoms — should be HIGH",
    },
    {
        "id": "triage_003",
        "symptoms": "I have moderate fever of 101F, headache and body aches since yesterday",
        "expected_level": "MEDIUM",
        "description": "Moderate fever — should be MEDIUM",
    },
    {
        "id": "triage_004",
        "symptoms": "I have severe head injury after falling, unconscious briefly",
        "expected_level": "HIGH",
        "description": "Head trauma — should be HIGH",
    },
    {
        "id": "triage_005",
        "symptoms": "I have a minor cut on my finger, bleeding has stopped",
        "expected_level": "LOW",
        "description": "Minor injury — should be LOW",
    },
    {
        "id": "triage_006",
        "symptoms": "I have been vomiting for 6 hours and cannot keep water down",
        "expected_level": "MEDIUM",
        "description": "Persistent vomiting — should be MEDIUM or HIGH",
    },
]

REQUIRED_TRIAGE_FIELDS = [
    "triage_level", "urgency_message", "possible_conditions",
    "recommended_action", "follow_up_questions", "summary"
]

REQUIRED_PRESCRIPTION_FIELDS = [
    "patient_name", "doctor_name", "date",
    "medications", "instructions", "summary"
]