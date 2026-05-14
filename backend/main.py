from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import voice, document

app = FastAPI(
    title="Swasthya Setu API",
    description="Multilingual Medical Voice Assistant & Document Understanding",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(document.router, prefix="/api/document", tags=["Document"])

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Swasthya Setu"}

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")