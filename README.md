# 🏥 Swasthya Setu — स्वास्थ्य सेतु

![CI](https://github.com/vaibhavr54/Swasthya-Setu-Multilingual-Medical-AI-Assistant/actions/workflows/ci.yml/badge.svg)

**Healthcare in your language, for every Indian.**

A multilingual AI-powered health bridge that lets patients speak their symptoms in Hindi, Marathi, Tamil, Telugu, Kannada, Gujarati, Bengali, Malayalam, Punjabi, or English — and receive clear, spoken medical guidance without needing to read or write English.

<p align="center">
  <img src="https://img.shields.io/badge/Sarvam%20AI-Powered-0f6e56?style=for-the-badge&logo=openai&logoColor=white" alt="Sarvam AI Powered">
  <img src="https://img.shields.io/badge/Mistral%20AI-Vision%20%2B%20OCR-185fa5?style=for-the-badge&logo=mistral&logoColor=white" alt="Mistral AI">
  <img src="https://img.shields.io/badge/10%2B%20Languages-Supported-1d9e75?style=for-the-badge&logo=google-translate&logoColor=white" alt="10+ Languages">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Search-FF6F00?style=for-the-badge&logo=chromadb&logoColor=white" alt="ChromaDB">
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#evaluation">Evaluation</a> •
  <a href="#deployment">Deployment</a>
</p>


---

## Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [API Reference](#-api-reference)
  - [Voice Endpoints](#voice-endpoints)
  - [Document Endpoints](#document-endpoints)
  - [FAQ Endpoints](#faq-endpoints)
- [Evaluation Framework](#-evaluation-framework)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Environment Variables](#-environment-variables)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#-disclaimer)
  
---

## Overview

**Swasthya Setu** (स्वास्थ्य सेतु, meaning "Health Bridge") is a production-ready, voice-first healthcare triage and document understanding platform built for India's linguistic diversity. It addresses a critical gap: **over 90% of India's population is not comfortable with English**, yet most digital health tools are English-only.

### The Problem
- 600+ million Indians speak Hindi, Marathi, Tamil, Telugu, Kannada, Gujarati, Bengali, Malayalam, or Punjabi as their primary language
- Medical prescriptions, discharge summaries, and health information are often in English
- Voice-based symptom reporting is inaccessible in regional languages
- Low-literacy populations cannot read or type health queries

### Our Solution
Swasthya Setu provides **three core capabilities** accessible entirely through voice or simple UI interactions:

| Capability | Description | Impact |
|-----------|-------------|--------|
| 🎙️ **Voice Symptom Assistant** | Speak symptoms in any Indian language → get triage guidance, urgency level, and next steps spoken back | Removes language and literacy barriers for symptom reporting |
| 📄 **Medical Document Analyzer** | Upload prescriptions or discharge summaries → get plain-language breakdown of every medicine, dosage, and instruction | Makes medical documents understandable to non-English speakers |
| ❓ **Medical FAQ Search** | Ask health questions in any language → get AI-generated answers from curated medical knowledge | Provides trusted health information in native languages |

---

## Features

### 🎙️ Voice Symptom Assistant
- **Speech-to-Text (STT)**: Sarvam Saaras v3 — supports 10+ Indian languages with auto-detection
- **AI Triage**: Sarvam-m LLM analyzes symptoms and assigns LOW / MEDIUM / HIGH urgency levels
- **Translation**: Sarvam Mayura v1 translates between English and all supported Indian languages
- **Text-to-Speech (TTS)**: Sarvam Bulbul v2 reads responses aloud in the patient's language
- **Follow-up Chat**: Voice or text follow-up questions with conversational memory
- **Safety-first**: Never diagnoses or prescribes — only triages and guides

### 📄 Medical Document Analyzer
- **OCR**: Mistral OCR API for images and PDFs with structured text extraction
- **Fallback OCR**: Tesseract with multi-language support (English + Hindi)
- **Prescription Parsing**: LLM extracts patient info, medications, dosages, instructions, and warnings
- **Plain-language Explanation**: Converts medical jargon into simple, spoken explanations
- **Follow-up Q&A**: Ask questions about specific medications or instructions
- **Multi-language Output**: Results delivered in the patient's chosen language

### ❓ Medical FAQ Search (RAG)
- **Semantic Search**: ChromaDB + Mistral Embeddings for vector-based FAQ retrieval
- **RAG Pipeline**: Retrieves top-3 relevant FAQs and generates contextual answers via LLM
- **Curated Knowledge Base**: 15 medical FAQs covering diabetes, hypertension, fever, cardiac, dengue, medication, gastro, child health, and respiratory topics
- **Voice Query Support**: Speak questions → STT → search → spoken answer
- **Confidence Scoring**: Color-coded similarity badges for transparency

### 🛡️ Production-Ready Features
- **Health Checks**: `/health` endpoint with Docker healthcheck integration
- **Error Handling**: Comprehensive try-catch with meaningful HTTP error codes
- **Input Validation**: Pydantic + FastAPI automatic validation
- **CORS**: Configured for cross-origin frontend access
- **Persistent Storage**: ChromaDB vector store persisted via Docker volumes
- **Evaluation Framework**: Automated quality measurement for STT, translation, and triage accuracy
- **Comprehensive Testing**: Unit tests, integration tests, and schema validation

---

## Architecture

<img width="1402" height="1122" alt="image" src="https://github.com/user-attachments/assets/bf867312-f5f7-407a-82df-5f6f9e3394ae" />


### Data Flow: Voice Triage

<img width="1774" height="887" alt="image" src="https://github.com/user-attachments/assets/d0287d0c-5224-492a-92b5-e528fd32e34c" />


### Data Flow: Document Analysis

<img width="1693" height="929" alt="image" src="https://github.com/user-attachments/assets/4aea72dc-2c23-4fcf-a4a2-756ed80af940" />



---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.128 | High-performance async API framework |
| **ASGI Server** | Uvicorn 0.39 | ASGI server for production |
| **AI/ML APIs** | Sarvam AI (Saaras, Bulbul, Mayura, sarvam-m) | STT, TTS, Translation, LLM |
| **Vision/OCR** | Mistral OCR API | Document text extraction |
| **Embeddings** | Mistral Embeddings API (mistral-embed) | Vector search |
| **Vector DB** | ChromaDB | Semantic FAQ storage and retrieval |
| **Fallback OCR** | Tesseract + pytesseract | Offline OCR fallback |
| **Image Processing** | Pillow | Image preprocessing |
| **Testing** | pytest, pytest-asyncio, httpx | Unit and integration tests |
| **Evaluation** | jiwer, sacrebleu | WER, BLEU, CER metrics |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Structure** | Pure HTML5 | Semantic markup |
| **Styling** | CSS3 (Custom Properties) | Responsive, accessible design |
| **Logic** | Vanilla JavaScript (ES6+) | No build step, zero dependencies |
| **Icons** | Inline SVG | Scalable, theme-aware icons |
| **Audio** | Web Audio API + MediaRecorder | Browser-based voice recording |

### DevOps & Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker + Docker Compose | Production deployment |
| **Health Monitoring** | Docker Healthcheck | Container health verification |
| **Environment** | python-dotenv | Configuration management |
| **CI/CD Ready** | pytest + eval_runner | Automated testing pipeline |

---

## Project Structure

```
swasthya-setu/
├── 📂 backend/
│   ├── 📄 main.py                 # FastAPI app entry point, lifespan, routes
│   ├── 📄 config.py               # Environment variables, API keys, language config
│   ├── 📂 routes/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 voice.py            # Voice triage, STT, TTS, follow-up endpoints
│   │   ├── 📄 document.py         # Document OCR, prescription parsing, follow-up
│   │   └── 📄 faq.py              # Semantic FAQ search, RAG answer generation
│   ├── 📂 services/
│   │   ├── 📄 sarvam.py           # Sarvam AI API wrappers (STT, TTS, Translate, OCR)
│   │   ├── 📄 llm.py              # Sarvam-m LLM prompts (triage, prescription, follow-up)
│   │   └── 📄 faq_store.py        # ChromaDB + Mistral Embeddings FAQ vector store
│   ├── 📂 data/
│   │   ├── 📄 medical_faqs.json   # Curated medical FAQ dataset (15 entries)
│   │   └── 📂 chroma_db/          # Persistent vector store (Docker volume)
│   └── 📂 tests/
│       ├── 📄 test_routes.py      # FastAPI route integration tests with mocks
│       ├── 📄 test_llm.py         # JSON parsing, prompt formatting unit tests
│       └── 📄 test_sarvam.py      # TTS preprocessing, WAV building, text splitting
│
├── 📂 frontend/
│   ├── 📄 index.html              # Landing page with FAQ search
│   ├── 📂 pages/
│   │   ├── 📄 voice.html          # Voice symptom assistant UI
│   │   └── 📄 document.html       # Document analyzer UI
│   ├── 📂 assets/
│   │   ├── 📂 css/
│   │   │   └── 📄 style.css       # Design system, components, responsive layout
│   │   └── 📂 js/
│   │       ├── 📄 main.js         # Shared utilities, FAQ search, TTS helpers
│       ├── 📄 voice.js            # Voice recording, triage display, follow-up chat
│       └── 📄 document.js         # File upload, OCR display, prescription rendering
│
├── 📂 eval/                       # Evaluation Framework
│   ├── 📄 eval_runner.py          # Main evaluation orchestrator
│   ├── 📄 eval_stt.py             # Word Error Rate (WER) / Character Error Rate (CER)
│   ├── 📄 eval_translation.py     # BLEU score + token overlap metrics
│   ├── 📄 eval_triage.py          # Schema validation + severity accuracy
│   ├── 📄 sample_data.py          # Ground-truth datasets for all evaluations
│   └── 📂 reports/                # Generated evaluation reports (JSON)
│
├── 📄 docker-compose.yml          # Docker Compose production config
├── 📄 requirements.txt            # Python dependencies
├── 📄 pytest.ini                # pytest configuration
└── 📄 README.md                   # This file
```

---

## Getting Started

### Prerequisites

- **Python** 3.9+ (backend)
- **Node.js** (optional, for frontend development server)
- **Docker** & **Docker Compose** (for containerized deployment)
- **API Keys** (see [Environment Variables](#-environment-variables))

### Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/vaibhavr54/Swasthya-Setu-Multilingual-Medical-AI-Assistant.git
cd Swasthya-Setu-Multilingual-Medical-AI-Assistant
```

2. **Create a `.env` file** in the project root:
```env
# Required — Sarvam AI APIs (STT, TTS, Translation, LLM)
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_BASE_URL=https://api.sarvam.ai

# Required — Mistral AI (OCR + Embeddings)
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional — Google Vision (alternative OCR)
GOOGLE_VISION_API_KEY=your_google_vision_key_here

# Optional — Tesseract path override (auto-detected if not set)
# TESSERACT_CMD=/usr/bin/tesseract
```

> 🔑 **Get API Keys:**
> - [Sarvam AI](https://www.sarvam.ai/) — for STT, TTS, Translation, and LLM
> - [Mistral AI](https://console.mistral.ai/) — for OCR and Embeddings

### Local Development

1. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR** (for fallback OCR):
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin

# Windows
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

4. **Run the backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **Serve the frontend** (in a new terminal):
```bash
# Option 1: Python simple HTTP server
cd frontend
python -m http.server 3000

# Option 2: VS Code Live Server extension
# Option 3: Any static file server
```

6. **Open the app:**
```
Frontend: http://localhost:3000
API Docs:  http://localhost:8000/docs
Health:    http://localhost:8000/health
```

### Docker Deployment

The fastest way to run in production:

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f swasthya-setu

# Stop
docker-compose down

# Stop and remove persistent data
docker-compose down -v
```

The Docker setup includes:
- **Health checks** every 30 seconds
- **Persistent ChromaDB** via named volume
- **Auto-restart** on failure
- **Environment variable** injection from `.env`

---

## API Reference

### Voice Endpoints

#### `POST /api/voice/transcribe`
Transcribe audio to text using Sarvam Saaras STT.

**Request:**
```http
Content-Type: multipart/form-data

audio: <audio_file.wav>
language_code: "hi-IN"  # or "unknown" for auto-detect
```

**Response:**
```json
{
  "transcript": "मुझे बुखार है और सिर दर्द हो रहा है",
  "detected_language": "hi-IN"
}
```

---

#### `POST /api/voice/triage`
Full voice triage pipeline: STT → Translate → LLM Triage → Translate → Return.

**Request:**
```http
Content-Type: multipart/form-data

audio: <audio_file.wav>
language_code: "unknown"  # auto-detect recommended
```

**Response:**
```json
{
  "transcript": "मुझे बुखार है और सिर दर्द हो रहा है",
  "detected_language": "hi-IN",
  "triage": {
    "triage_level": "MEDIUM",
    "urgency_message": "डॉक्टर से 24 घंटे के भीतर मिलें",
    "possible_conditions": ["वायरल बुखार", "साइनस संक्रमण"],
    "recommended_action": "पर्याप्त पानी पिएं और आराम करें। यदि बुखार 103°F से अधिक हो तो तुरंत डॉक्टर से मिलें।",
    "follow_up_questions": ["क्या आपको खांसी भी है?", "क्या आपको शरीर में दर्द है?"],
    "summary": "आपको मध्यम बुखार और सिर दर्द है..."
  }
}
```

---

#### `POST /api/voice/speak`
Convert text to speech using Sarvam Bulbul TTS.

**Request:**
```http
Content-Type: multipart/form-data

text: "आपको आराम करने की जरूरत है"
language_code: "hi-IN"
speaker: "auto"  # auto-selects by language
```

**Response:** `audio/wav` binary

---

#### `POST /api/voice/followup`
Conversational follow-up about triage results (voice or text input).

**Request:**
```http
Content-Type: multipart/form-data

question_audio: <optional_audio.wav>
question_text: "क्या मैं दवा ले सकता हूं?"
language_code: "hi-IN"
triage_context: '{"triage_level": "MEDIUM", "summary": "..."}'
history: '[{"question": "...", "answer": "..."}]'
```

---

### Document Endpoints

#### `POST /api/document/analyze`
Upload and analyze a medical document (prescription, discharge summary).

**Request:**
```http
Content-Type: multipart/form-data

file: <prescription.jpg or .pdf>
target_language: "hi-IN"
```

**Response:**
```json
{
  "ocr_text": "Paracetamol 500mg BD x 5 days...",
  "explanation": {
    "patient_name": "Ramesh",
    "doctor_name": "Dr. Sharma",
    "date": "2024-01-01",
    "medications": [
      {
        "name": "Paracetamol 500mg",
        "purpose": "बुखार और दर्द कम करने के लिए",
        "dosage": "500mg दिन में दो बार",
        "duration": "5 दिन",
        "side_effects": "सामान्य रूप से सुरक्षित"
      }
    ],
    "instructions": ["भोजन के बाद दवा लें"],
    "summary": "डॉक्टर शर्मा ने रमेश को दो दवाइयां दी हैं..."
  },
  "target_language": "hi-IN"
}
```

---

#### `POST /api/document/followup`
Ask follow-up questions about a prescription (voice or text).

**Request:**
```http
Content-Type: multipart/form-data

question_audio: <optional_audio.wav>
question: "Can I take this with food?"
language_code: "en-IN"
prescription_context: '{"medications": [...], "summary": "..."}'
history: '[]'
```

---

### FAQ Endpoints

#### `POST /api/faq/search`
Semantic FAQ search with RAG answer generation.

**Request:**
```http
Content-Type: multipart/form-data

query: "What are diabetes symptoms?"
language_code: "hi-IN"
n_results: 3
```

**Response:**
```json
{
  "query": "What are diabetes symptoms?",
  "query_en": "What are diabetes symptoms?",
  "answer": "मधुमेह के लक्षण: अत्यधिक प्यास, बार-बार पेशाब आना...",
  "answer_en": "Diabetes symptoms include increased thirst...",
  "language_code": "hi-IN",
  "matched_faqs": [
    {
      "id": "faq_001",
      "question": "What are the symptoms of diabetes?",
      "answer": "Common symptoms of diabetes include...",
      "category": "diabetes",
      "similarity": 0.95
    }
  ],
  "rag_context_used": 3
}
```

---

#### `GET /api/faq/health`
FAQ store health check and count.

**Response:**
```json
{
  "status": "ok",
  "faq_count": 15
}
```

---

## Evaluation Framework

Swasthya Setu includes a comprehensive evaluation framework to measure AI component quality across three dimensions:

### Components Evaluated

| Component | Metric | Threshold | Description |
|-----------|--------|-----------|-------------|
| **STT** | WER (Word Error Rate) | < 30% | Measures transcription accuracy |
| **STT** | CER (Character Error Rate) | < 15% | Character-level accuracy |
| **Translation** | BLEU Score | > 15 | Translation quality vs. reference |
| **Translation** | Token Overlap | > 30% | Semantic similarity fallback |
| **Triage** | Schema Validity | 100% | JSON structure compliance |
| **Triage** | Severity Accuracy | 100% | Correct LOW/MEDIUM/HIGH assignment |

### Running Evaluations

```bash
# Schema-only mode (fast, no API calls, CI-friendly)
cd eval
python eval_runner.py --mode schema

# Full evaluation (makes real API calls, measures actual quality)
python eval_runner.py --mode full --save
```

### Sample Evaluation Output

```
╔══════════════════════════════════════════════════════════╗
║         SWASTHYA SETU — AI EVALUATION FRAMEWORK          ║
║         Measuring STT · Translation · Triage Quality     ║
╚══════════════════════════════════════════════════════════╝

  ✅ STT            3/3 passed  (score: 100%)
  ✅ Translation    4/4 passed  (score: 100%)
  ✅ Triage         6/6 passed  (score: 100%)

  Overall: 13/13 (100%)
  🎉 Evaluation PASSED
```

### Ground Truth Datasets

- **STT Samples**: 3 samples (English, Hindi, Marathi)
- **Translation Samples**: 4 samples (EN→HI, EN→MR, EN→TA)
- **Triage Samples**: 6 clinical scenarios with expected severity levels

---

## Testing

### Test Suite

```bash
# Run all tests
cd backend
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_routes.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| `test_routes.py` | FastAPI endpoint integration tests with mocked external APIs |
| `test_llm.py` | JSON parsing resilience, prompt formatting, message structure |
| `test_sarvam.py` | TTS text preprocessing, WAV audio building, text chunking, speaker mapping |

### Key Test Scenarios

- **JSON Parsing**: Handles markdown fences, think tags, and malformed LLM outputs
- **Schema Validation**: Validates triage and prescription JSON structures
- **API Mocking**: Tests all routes without external API dependencies
- **Error Handling**: Validates proper HTTP status codes for invalid inputs
- **Audio Processing**: WAV header construction, PCM extraction, text splitting

---

## Deployment

### Docker (Recommended)

```bash
# Production deployment
docker-compose up -d

# Scale considerations:
# - ChromaDB is file-based and single-node
# - For high traffic, consider external ChromaDB or Redis
# - Use a reverse proxy (nginx/traefik) for SSL termination
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SARVAM_API_KEY` | ✅ | — | Sarvam AI API key |
| `MISTRAL_API_KEY` | ✅ | — | Mistral AI API key |
| `SARVAM_BASE_URL` | ❌ | `https://api.sarvam.ai` | Sarvam API base URL |
| `GOOGLE_VISION_API_KEY` | ❌ | — | Google Vision OCR (optional) |
| `TESSERACT_CMD` | ❌ | Auto-detected | Tesseract executable path |

### Health Checks

The application exposes a health endpoint:
```bash
curl http://localhost:8000/health
# {"status": "ok", "app": "Swasthya Setu"}
```

Docker healthcheck is configured to restart the container if unhealthy.

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Run** tests (`pytest`)
4. **Run** evaluation (`python eval/eval_runner.py --mode schema`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Add tests for new features
- Update evaluation datasets for new languages
- Maintain the safety-first principle (never diagnose or prescribe)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

**Swasthya Setu is a triage and health information tool only. It does NOT:**
- ❌ Diagnose medical conditions
- ❌ Prescribe medications
- ❌ Replace professional medical advice, diagnosis, or treatment

**Always consult a qualified healthcare provider for medical decisions.**

This tool is designed to:
- ✅ Help patients understand when to seek care
- ✅ Explain prescriptions in plain language
- ✅ Provide general health information from curated sources
- ✅ Reduce language barriers in healthcare access

**In case of emergency, call 108 (India) or your local emergency number immediately.**

---

## Acknowledgments

- **Sarvam AI** for providing world-class Indian language AI APIs
- **Mistral AI** for OCR and embedding capabilities
- The open-source community for FastAPI, ChromaDB, and Tesseract

---

<p align="center">
  <strong>Built with ❤️ for Bharat</strong><br>
  <em>स्वास्थ्य सेतु — Health Bridge</em>
</p>

