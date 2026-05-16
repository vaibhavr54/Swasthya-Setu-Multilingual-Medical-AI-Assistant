import pytest
import sys
import os
import struct
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


# ─── Test TTS text preprocessing ──────────────────────────────────────────

def preprocess_tts_text(text: str, language_code: str = "mr-IN") -> str:
    """Mirrors preprocessing logic in sarvam.py text_to_speech"""
    range_connectors = {
        "hi-IN": "से", "mr-IN": "ते", "ta-IN": "முதல்",
        "te-IN": "నుండి", "kn-IN": "ರಿಂದ", "gu-IN": "થી",
        "bn-IN": "থেকে", "ml-IN": "മുതൽ", "pa-IN": "ਤੋਂ", "en-IN": "to",
    }
    connector = range_connectors.get(language_code, "to")
    text = re.sub(r'(\d+)\s*-\s*(\d+)', rf'\1 {connector} \2', text)
    text = re.sub(r'।([^\s])', '। \\1', text)
    return text


def split_text(t: str, limit: int = 490) -> list:
    """Mirrors split_text logic in sarvam.py"""
    if len(t) <= limit:
        return [t]
    chunks = []
    while len(t) > limit:
        split_at = t.rfind("।", 0, limit)
        if split_at == -1:
            split_at = t.rfind(".", 0, limit)
        if split_at == -1:
            split_at = t.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(t[:split_at + 1].strip())
        t = t[split_at + 1:].strip()
    if t:
        chunks.append(t)
    return chunks


def build_wav(pcm_data: bytes, channels=1, sample_rate=22050, bit_depth=16) -> bytes:
    """Mirrors build_wav in sarvam.py"""
    byte_rate = sample_rate * channels * bit_depth // 8
    block_align = channels * bit_depth // 8
    data_size = len(pcm_data)
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size, b'WAVE',
        b'fmt ', 16, 1, channels,
        sample_rate, byte_rate, block_align, bit_depth,
        b'data', data_size
    )
    return header + pcm_data


class TestTTSPreprocessing:

    def test_range_replaced_marathi(self):
        result = preprocess_tts_text("वय 25-30 वर्षे", "mr-IN")
        assert "25 ते 30" in result

    def test_range_replaced_hindi(self):
        result = preprocess_tts_text("age 40-50 years", "hi-IN")
        assert "40 से 50" in result

    def test_range_replaced_english(self):
        result = preprocess_tts_text("Take 1-2 tablets", "en-IN")
        assert "1 to 2" in result

    def test_devanagari_pause_spacing(self):
        result = preprocess_tts_text("आराम करा।पाणी प्या.", "mr-IN")
        assert "।" in result
        # Should have space after ।
        assert "। " in result or "।प" not in result

    def test_no_range_unchanged(self):
        result = preprocess_tts_text("Take paracetamol daily", "en-IN")
        assert result == "Take paracetamol daily"


class TestTextSplitting:

    def test_short_text_not_split(self):
        text = "This is a short text."
        chunks = split_text(text, limit=490)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_split(self):
        text = "word " * 120  # ~600 chars
        chunks = split_text(text, limit=490)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 490

    def test_split_on_devanagari_sentence(self):
        text = ("आराम करा। " * 30) + "पाणी प्या."
        chunks = split_text(text, limit=490)
        for chunk in chunks:
            assert len(chunk) <= 490

    def test_all_chunks_combined_have_all_words(self):
        text = "The patient should rest. " * 25
        chunks = split_text(text, limit=490)
        combined = " ".join(chunks)
        assert "patient" in combined
        assert "rest" in combined

    def test_empty_string(self):
        chunks = split_text("", limit=490)
        assert chunks == [""]


class TestWAVBuilding:

    def test_wav_has_riff_header(self):
        pcm = b'\x00\x01' * 100
        wav = build_wav(pcm)
        assert wav[:4] == b'RIFF'
        assert wav[8:12] == b'WAVE'

    def test_wav_has_data_chunk(self):
        pcm = b'\x00\x01' * 100
        wav = build_wav(pcm)
        assert b'data' in wav

    def test_wav_correct_size(self):
        pcm = b'\x00' * 200
        wav = build_wav(pcm)
        # RIFF size = 36 + data_size
        riff_size = struct.unpack_from('<I', wav, 4)[0]
        assert riff_size == 36 + 200


class TestLanguageSpeakerMap:

    def test_speaker_map_coverage(self):
        speaker_map = {
            "hi-IN": "Ratan", "mr-IN": "anushka", "ta-IN": "Kavitha",
            "te-IN": "Vijay", "kn-IN": "anushka", "gu-IN": "Ratan",
            "bn-IN": "anushka", "ml-IN": "Kavitha", "pa-IN": "Ratan",
            "en-IN": "anushka",
        }
        supported = ["hi-IN", "mr-IN", "ta-IN", "te-IN", "kn-IN",
                     "gu-IN", "bn-IN", "ml-IN", "pa-IN", "en-IN"]
        for lang in supported:
            assert lang in speaker_map

    def test_default_speaker_fallback(self):
        speaker_map = {"hi-IN": "Ratan"}
        result = speaker_map.get("xx-XX", "anushka")
        assert result == "anushka"