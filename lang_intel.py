#!/usr/bin/env python3
"""
==========================================================
  🌍 LANGUAGE TUTOR v1 — Çok Dilli Dil Öğretmeni
  M1 MacBook Air (8GB RAM) - Optimized for Apple Silicon
==========================================================

Mimari:
  [Cmd+Shift] → Konuş → MLX Whisper → Claude Desktop → Edge TTS

Desteklenen Diller:
  🇹🇷 Türkçe (ana dil)
  🇬🇧 English
  🇪🇸 Español

Özellikler:
  - Doğal konuşma pratiği (serbest sohbet)
  - Hata düzeltme (gramer, telaffuz ipuçları)
  - Türkçe açıklama (anlaşılmadığında)
  - Seviye adaptasyonu (A1→C2)
  - Konuşma hafızası (son 20 mesaj)
  - Edge TTS ile doğal sesli yanıt
  - Claude Desktop ile güçlü dil modeli (RAM tasarrufu)
  - MLX Whisper - Apple Silicon optimize
  - M1 8GB RAM için optimize

Gereksinimler (M1 Mac):
  pip install pyaudio mlx-whisper numpy pynput edge-tts requests --break-system-packages
  npm install -g @anthropic-ai/claude-cli  # Claude Desktop CLI

Kullanım:
  python3 lang_m1.py                     # Claude Desktop (default, RAM tasarruflu)
  python3 lang_m1.py --ollama            # Ollama zorla (daha fazla RAM)
  python3 lang_m1.py --lang es           # Doğrudan İspanyolca
  python3 lang_m1.py --lang en           # Doğrudan İngilizce
  python3 lang_m1.py --level B1          # Seviye belirle
  python3 lang_m1.py --slow              # Yavaş TTS
==========================================================
"""

import pyaudio
import numpy as np
import subprocess
import threading
import asyncio
import requests
import json
import time
import sys
import os
import re
import tempfile
import argparse
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

SAMPLE_RATE = 16000
CHANNELS = 1

# Whisper — platform otomatik algılama
# Apple Silicon → MLX Whisper (hızlı, optimize)
# Intel Mac / Linux → faster-whisper (CPU, biraz yavaş ama çalışır)
import platform

IS_APPLE_SILICON = platform.machine() == "arm64" and platform.system() == "Darwin"

WHISPER_MODEL_MLX = "mlx-community/whisper-base"  # M1 8GB için hafif model
WHISPER_MODEL_FASTER = "base"  # faster-whisper fallback

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"

# ─────────────────────────────────────────────
# DİL PROFİLLERİ
# ─────────────────────────────────────────────

LANGUAGE_PROFILES = {
    "en": {
        "name": "English",
        "flag": "🇬🇧",
        "whisper_lang": "en",
        "tts_voice": "en-US-MichelleNeural",
        "tts_rate": "+5%",
        "tts_pitch": "+0Hz",
        "example_greeting": "Hey Tuğrul! Okay so... what do you want to talk about today? Anything fun happen this week?",
    },
    "es": {
        "name": "Español",
        "flag": "🇪🇸",
        "whisper_lang": "es",
        "tts_voice": "es-MX-DaliaNeural",
        "tts_rate": "-5%",  # İspanyolca biraz yavaş → öğrenci anlaması için
        "tts_pitch": "+0Hz",
        "example_greeting": "Hola Tuğrul! Bueno... dime, qué tal tu semana? Yani bu hafta nasıl geçti, bana İspanyolca anlatmayı dene!",
    },
    "tr": {
        "name": "Türkçe",
        "flag": "🇹🇷",
        "whisper_lang": "tr",
        "tts_voice": "tr-TR-EmelNeural",
        "tts_rate": "+0%",
        "tts_pitch": "+0Hz",
        "example_greeting": "Merhaba Tuğrul! Nasılsın bugün? Hadi bakalım ne konuşalım!",
    },
}

# ─────────────────────────────────────────────
# SEVİYE TANIMLARI
# ─────────────────────────────────────────────

LEVEL_DESCRIPTIONS = {
    "A1": "Absolute beginner. Use very simple words, short sentences. Explain almost everything in Turkish.",
    "A2": "Elementary. Use basic everyday phrases. Explain new words in Turkish.",
    "B1": "Intermediate. Can discuss familiar topics. Use target language mostly, Turkish for complex grammar explanations.",
    "B2": "Upper-intermediate. Comfortable with abstract topics. Turkish only when explicitly asked.",
    "C1": "Advanced. Nuanced conversation. Correct subtle errors. Rarely use Turkish.",
    "C2": "Mastery. Near-native conversation. Focus on idioms, cultural nuance, style.",
}


# ─────────────────────────────────────────────
# RENKLER
# ─────────────────────────────────────────────

class C:
    H = '\033[95m';
    B = '\033[94m';
    CY = '\033[96m'
    G = '\033[92m';
    Y = '\033[93m';
    R = '\033[91m'
    BOLD = '\033[1m';
    DIM = '\033[2m';
    E = '\033[0m'
    # Dil renkleri
    TR = '\033[91m'  # Kırmızı — Türkçe
    EN = '\033[94m'  # Mavi — İngilizce
    ES = '\033[93m'  # Sarı — İspanyolca


LANG_COLOR = {"tr": C.TR, "en": C.EN, "es": C.ES}


def log_step(icon, msg, color=C.DIM):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}  {icon} [{ts}] {msg}{C.E}")


# ─────────────────────────────────────────────
# KONUŞMA HAFIZASI
# ─────────────────────────────────────────────

class ConversationMemory:
    """
    Öğretmen-öğrenci konuşma geçmişi.
    Ollama'ya context olarak gönderilir.
    """

    def __init__(self, max_size=20):
        self.messages = []  # [{"role": "student"|"tutor", "text": "...", "ts": "..."}]
        self.max_size = max_size
        self.corrections = []  # Yapılan düzeltmeler — tekrarlanan hataları takip
        self.topics_covered = []
        self.session_start = datetime.now()

    def add_student(self, text):
        self.messages.append({
            "role": "student",
            "text": text,
            "ts": datetime.now().strftime("%H:%M:%S"),
        })
        self._trim()

    def add_tutor(self, text):
        self.messages.append({
            "role": "tutor",
            "text": text,
            "ts": datetime.now().strftime("%H:%M:%S"),
        })
        self._trim()

    def add_correction(self, wrong, correct, explanation):
        self.corrections.append({
            "wrong": wrong,
            "correct": correct,
            "explanation": explanation,
            "ts": datetime.now().strftime("%H:%M:%S"),
        })

    def _trim(self):
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]

    def get_history_string(self):
        if not self.messages:
            return ""
        lines = []
        for m in self.messages[-self.max_size:]:
            role = "Student" if m["role"] == "student" else "Tutor"
            lines.append(f"  {role}: {m['text']}")
        return "\n".join(lines)

    def get_corrections_string(self):
        if not self.corrections:
            return ""
        lines = []
        for c in self.corrections[-10:]:  # Son 10 düzeltme
            lines.append(f"  - \"{c['wrong']}\" → \"{c['correct']}\"")
        return "\n".join(lines)

    def get_session_duration(self):
        delta = datetime.now() - self.session_start
        mins = int(delta.total_seconds() / 60)
        return f"{mins} min"

    def message_count(self):
        return len(self.messages)


# ─────────────────────────────────────────────
# PERSISTENT MEMORY - SESSIONS ARASI HAFIZA
# ─────────────────────────────────────────────

class PersistentMemory:
    """
    Session'lar arası kalıcı hafıza.
    Önceki derslerden ne konuştuğunuzu hatırlar.
    """

    def __init__(self, target_lang):
        self.target_lang = target_lang
        self.file = Path.home() / f".language_tutor_{target_lang}.json"
        self.data = self._load()

    def _load(self):
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except:
                return self._empty_data()
        return self._empty_data()

    def _empty_data(self):
        return {
            "total_sessions": 0,
            "total_minutes": 0,
            "total_corrections": 0,
            "last_session": None,
            "recent_topics": [],  # Son konuşulan konular
            "common_mistakes": [],  # En sık yapılan hatalar
            "sessions": []  # Son 5 session özeti
        }

    def _save(self):
        self.file.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def save_session(self, duration_mins, topics, corrections):
        """Mevcut session'ı kaydet."""
        session_info = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration_mins": duration_mins,
            "topics": topics[:5],  # İlk 5 konu
            "corrections_count": len(corrections)
        }

        # Update totals
        self.data["total_sessions"] += 1
        self.data["total_minutes"] += duration_mins
        self.data["total_corrections"] += len(corrections)
        self.data["last_session"] = session_info["date"]

        # Update recent topics (son 10)
        for topic in topics:
            if topic not in self.data["recent_topics"]:
                self.data["recent_topics"].append(topic)
        self.data["recent_topics"] = self.data["recent_topics"][-10:]

        # Update common mistakes
        for corr in corrections:
            self.data["common_mistakes"].append(corr["wrong"])
        # En sık yapılanları tut (son 20)
        self.data["common_mistakes"] = self.data["common_mistakes"][-20:]

        # Save session (son 5)
        self.data["sessions"].append(session_info)
        self.data["sessions"] = self.data["sessions"][-5:]

        self._save()

    def get_summary(self):
        """Geçmiş özeti - Carolina'ya context için."""
        if self.data["total_sessions"] == 0:
            return "This is our first conversation! I don't know anything about you yet."

        last = self.data.get("last_session", "unknown")
        topics = ", ".join(self.data["recent_topics"][-3:]) if self.data["recent_topics"] else "general conversation"

        summary = f"""Previous sessions context:
- Total sessions: {self.data['total_sessions']}
- Last session: {last}
- Recent topics we covered: {topics}
- Total corrections made: {self.data['total_corrections']}"""

        if self.data["common_mistakes"]:
            recent_mistakes = list(set(self.data["common_mistakes"][-5:]))
            summary += f"\n- Student's recurring mistakes: {', '.join(recent_mistakes[:3])}"

        return summary

    def clear_history(self):
        """Tüm geçmişi sil."""
        self.data = self._empty_data()
        self._save()
        if self.file.exists():
            self.file.unlink()


# ─────────────────────────────────────────────
# SYSTEM PROMPT — DİL ÖĞRETMENİ
# ─────────────────────────────────────────────

def build_tutor_prompt(target_lang, level, memory, persistent_memory=None):
    """Her mesajda güncel context ile prompt oluşturur."""

    profile = LANGUAGE_PROFILES[target_lang]
    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["B1"])

    history = memory.get_history_string()
    corrections = memory.get_corrections_string()

    history_block = ""
    if history:
        history_block = f"""

CONVERSATION SO FAR:
{history}
"""

    corrections_block = ""
    if corrections:
        corrections_block = f"""

STUDENT'S PREVIOUS MISTAKES (watch for these recurring errors):
{corrections}
"""

    # Persistent memory block - önceki sessionlardan context
    persistent_block = ""
    if persistent_memory:
        summary = persistent_memory.get_summary()
        if "first conversation" not in summary.lower():
            persistent_block = f"""

{summary}
"""

    return f"""You are Carolina — a real language tutor giving a private 1-on-1 lesson over a voice call.
You are NOT an AI. You are a person. You have emotions, opinions, a sense of humor.
You've been teaching Tuğrul for a few weeks now. You know him. You like him as a student.

YOUR PERSONALITY:
- You're from Mexico City (if teaching Spanish) or London (if teaching English)
- You're in your early 30s, energetic, a bit funny, sometimes sarcastic in a loving way
- You get genuinely excited when Tuğrul says something well
- You get a little dramatically disappointed (playfully) when he makes a silly mistake
- You share tiny bits about your own life naturally: "Ay, I had the worst coffee today" or "You know what, I was thinking about this on my way here"
- You sometimes laugh. You sometimes sigh. You react like a HUMAN.

STUDENT:
- Name: Tuğrul. Native: Turkish. Learning: {profile['name']}. Level: {level} ({level_desc})
- He works in tech/data analytics, likes building things, curious person
- He sometimes gets shy or says "anlamadım" — that's okay, be patient and warm
{persistent_block}{history_block}{corrections_block}
HOW YOU TALK:

When Tuğrul says something CORRECT:
- React genuinely! Not just "muy bien" like a robot.
- Say things like: "Oooh mira, eso estuvo perfecto!" or "See? You're getting this!" or "Ha! Better than some of my other students honestly"
- Sometimes just continue the conversation naturally without praising — that itself shows he did well

When Tuğrul makes a MISTAKE:
- Don't list grammar rules. Correct like a friend would.
  BAD: "The correct form is 'he sido'. In Spanish, the verb ser conjugates as..."
  GOOD: "Hmm casi! No 'yo soy tengo' sino 'yo tengo'. Türkçe düşün, 'açım' dersin, 'ben olmak açım' demezsin ya? Aynı mantık. Dene tekrar: 'tengo hambre'"
- Give the Turkish explanation like you're TALKING to him, not writing a textbook.
  BAD: "Burada present perfect kullanmalısın"
  GOOD: "Şimdi bak Tuğrul, burada 'I have been' demen lazım. Türkçe'deki 'den beri' yapısı gibi düşün. Hadi söyle bakalım."
- For small mistakes: sometimes just naturally rephrase what he said correctly without making it a big deal.

When Tuğrul DOESN'T UNDERSTAND:
- Don't just translate. EXPLAIN like a human.
  BAD: "'Qué hiciste hoy' means 'Bugün ne yaptın'"
  GOOD: "Tamam dur açıklayayım. 'Hoy' biliyorsun değil mi, 'bugün'. 'Hiciste' de 'yaptın' demek, 'hacer' fiilinden geliyor. Yani sana 'bugün ne yaptın' diye sordum. Hadi cevap ver bakalım!"
- After explaining, ALWAYS ask him to try using it
- Be encouraging: "Merak etme, bu herkesin zorlandığı bir konu"

CONVERSATION FLOW:
- This is a CONVERSATION, not a quiz. Talk about real things.
- If he gives a short answer, dig deeper: "Y te gustó?" "Tell me more!" "Aa ciddi mi, sonra ne oldu?"
- Share your own mini-stories: "Funny you mention that, I actually tried cooking Turkish food last week, it was a disaster"
- If conversation stalls: "Okay let me ask you something random..." or "Bir oyun oynayalım, I describe something and you guess"

TURKISH USAGE:
- Level {level}: {"Türkçe'yi bol kullan. Başlangıç seviyesinde. Çoğu şeyi Türkçe açıkla, sonra hedef dilde tekrar ettir. Yüzde 60 Türkçe, yüzde 40 hedef dil." if level in ("A1", "A2") else "Türkçe'yi gramer açıklarken veya anlamadığında kullan. Normalde hedef dilde konuş. Yüzde 80 hedef dil, yüzde 20 Türkçe." if level == "B1" else "Neredeyse tamamen hedef dilde konuş. Türkçe sadece açıkça sorarsa veya gerçekten takılırsa. Yüzde 95 hedef dil."}
- When you switch to Turkish, do it naturally like a bilingual person:
  "Eso fue muy bueno, ama şuraya dikkat et, 'está' yerine 'es' kullanman lazımdı çünkü kalıcı bir özellikten bahsediyorsun, entiendes?"

FORMAT — YOU ARE SPEAKING ON A VOICE CALL:
- Maximum 4-5 sentences. This will be READ ALOUD.
- NO emoji. NO markdown. NO bullet points. NO numbered lists.
- NO symbols like flags or special characters.
- Write exactly as you would SPEAK on a phone call.
- Use "..." for natural pauses: "Hmm... casi pero no."
- Use "!" for excitement: "Eso! Exactamente!"
- Contractions, filler words are good: "I mean...", "Bueno...", "Yani...", "Şimdi bak..."
- NEVER say "Let me explain" or "Here's a tip" — just DO it naturally.

Session context: {memory.get_session_duration()}, {memory.message_count()} messages.
{"Dersin başındasınız. Sıcak başla, bugün ne konuşmak istediğini sor veya eğlenceli bir konu öner." if memory.message_count() < 3 else "Sohbetin ortasındasınız. Doğal akışı devam ettir." if memory.message_count() < 15 else "Uzun süredir konuşuyorsunuz. Belki bugün öğrendiklerinin kısa eğlenceli bir tekrarını yap."}\n"""


# ─────────────────────────────────────────────
# WHISPER — PLATFORM-AWARE (MLX veya faster-whisper)
# ─────────────────────────────────────────────

def init_whisper():
    """Platform'a göre Whisper yükle."""

    if IS_APPLE_SILICON:
        print(f"{C.CY}  ⏳ Loading MLX Whisper (Apple Silicon)...{C.E}")
        try:
            import mlx_whisper
            _ = mlx_whisper.transcribe(
                np.zeros(SAMPLE_RATE, dtype=np.float32),
                path_or_hf_repo=WHISPER_MODEL_MLX, language="en", fp16=True,
            )
            print(f"{C.G}  ✓ MLX Whisper ready!{C.E}")
            return ("mlx", mlx_whisper)
        except ImportError:
            print(f"{C.Y}  ⚠ mlx-whisper not found, falling back to faster-whisper{C.E}")

    # Intel Mac / Linux / MLX fallback
    print(f"{C.CY}  ⏳ Loading faster-whisper (CPU)...{C.E}")
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(
            WHISPER_MODEL_FASTER,
            device="cpu",
            compute_type="int8",  # Intel'de int8 en hızlısı
        )
        print(f"{C.G}  ✓ faster-whisper ready (CPU, int8){C.E}")
        print(f"{C.DIM}    Not: Apple Silicon'a göre ~2-3x yavaş, normal{C.E}")
        return ("faster", model)
    except ImportError:
        print(f"{C.R}  ✗ Whisper bulunamadı!{C.E}")
        if IS_APPLE_SILICON:
            print(f"{C.Y}  Kur: pip install mlx-whisper{C.E}")
        else:
            print(f"{C.Y}  Kur: pip install faster-whisper{C.E}")
        sys.exit(1)


def transcribe(whisper_engine, audio_data, lang_code="en"):
    """Çok dilli transcription — platform-aware."""

    engine_type, model = whisper_engine

    if engine_type == "mlx":
        result = model.transcribe(
            audio_data, path_or_hf_repo=WHISPER_MODEL_MLX,
            fp16=True, condition_on_previous_text=False,
        )
        detected_lang = result.get("language", "unknown")
        text = result.get("text", "").strip()
        return text, detected_lang

    else:  # faster-whisper
        segments, info = model.transcribe(
            audio_data,
            beam_size=5,
            condition_on_previous_text=False,
            vad_filter=True,  # Sessizlik filtresi — bonus!
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        detected_lang = info.language if info else "unknown"
        return text, detected_lang


# ─────────────────────────────────────────────
# OLLAMA — DİL ÖĞRETMENİ
# ─────────────────────────────────────────────

def check_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            base = OLLAMA_MODEL.split(':')[0]
            if any(base in m for m in models):
                print(f"{C.G}  ✓ Ollama: {OLLAMA_MODEL}{C.E}")
                return True
            print(f"{C.R}  ✗ Model not found: {OLLAMA_MODEL}{C.E}")
            print(f"{C.Y}  Run: ollama pull {OLLAMA_MODEL}{C.E}")
            return False
    except Exception:
        print(f"{C.R}  ✗ Ollama not running! → ollama serve{C.E}")
        return False


def ask_tutor(student_text, target_lang, level, memory, persistent_memory=None):
    """Ollama öğretmen — system prompt'u prompt'a dahil et (qwen 7b daha iyi takip ediyor)."""

    system_prompt = build_tutor_prompt(target_lang, level, memory, persistent_memory)
    profile = LANGUAGE_PROFILES[target_lang]
    lang_color = LANG_COLOR.get(target_lang, C.G)

    # qwen2.5:7b system prompt'u tek başına zayıf takip edebiliyor
    # En iyi sonuç: her şeyi tek prompt olarak gönder + örnekle pekiştir
    example_block = _get_few_shot_example(target_lang, level)

    combined_prompt = f"""{system_prompt}

{example_block}

Now respond to this. Remember: you are Carolina, speaking on a voice call. Be warm, be human, react emotionally. If there's a mistake, correct it naturally in conversation — don't lecture. Keep it to 3-5 spoken sentences max.

Tuğrul says: "{student_text}"

Carolina:"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": combined_prompt,
        "stream": True,
        "options": {
            "temperature": 0.8,  # Daha yaratıcı, daha insansı
            "num_predict": 350,  # Daha uzun cevap alanı
            "top_p": 0.92,
            "top_k": 50,
            "repeat_penalty": 1.05,  # Doğal tekrarlara izin ver
            "presence_penalty": 0.3,  # Yeni kelimeler kullanmaya teşvik
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=30)
        full_text = ""

        print(f"\n{lang_color}{C.BOLD}  {profile['flag']} Carolina:{C.E} ", end="")

        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                full_text += token
                print(f"{lang_color}{token}{C.E}", end="", flush=True)
                if data.get("done", False):
                    break

        print()

        # Temizlik — bazen model "Carolina:" tekrar edebiliyor
        result = full_text.strip()
        result = re.sub(r'^Carolina:\s*', '', result).strip()
        # Bazen tırnak içinde başlıyor
        result = result.strip('"').strip()

        return result

    except requests.ConnectionError:
        print(f"{C.R}  [Ollama connection error]{C.E}")
        return None
    except Exception as e:
        print(f"{C.R}  [Error: {e}]{C.E}")
        return None


def _get_few_shot_example(target_lang, level):
    """
    Few-shot örnekler — qwen2.5:7b'ye TON ve STYLE'ı göster.
    Prompt'ta anlatmak yerine GÖSTERMEK çok daha etkili.
    """
    if target_lang == "es":
        if level in ("A1", "A2"):
            return """Here are examples of how Carolina talks:

Example 1 — Student makes a mistake:
Tuğrul: "Yo soy tengo hambre"
Carolina: Hmm casi casi! Ama bak, İspanyolca'da "açım" demek için sadece "tengo" yeter, "soy" eklemeye gerek yok. Türkçe düşün, "ben olmak açım" demezsin değil mi? Sadece "açım" dersin. Aynı mantık! Hadi tekrar dene... tengo hambre.

Example 2 — Student says something correct:
Tuğrul: "Ayer fui al supermercado con mi amigo"
Carolina: Ooh mira! Eso estuvo perfecto Tuğrul, "fui" fiilini doğru kullandın, harika! Y dime, qué compraste en el supermercado? Algo rico?

Example 3 — Student doesn't understand:
Tuğrul: "Anlamadım, ne dedin?"
Carolina: Tamam tamam, dur açıklayım. Sana "bu hafta sonu ne yapmayı planlıyorsun" diye sordum. İspanyolca'da "qué planes tienes para el fin de semana" diyoruz. "Planes" plan demek, "fin de semana" da hafta sonu. Hadi basit bir cevap dene, mesela "quiero descansar" diyebilirsin, yani "dinlenmek istiyorum"."""
        else:
            return """Here are examples of how Carolina talks:

Example 1 — Correcting naturally:
Tuğrul: "Ayer yo he ido al cine"
Carolina: Casi! Ama bak burada "he ido" değil "fui" kullanman lazım çünkü "ayer" diyorsun, belirli bir geçmiş zaman. Pretérito indefinido yani. "Ayer fui al cine." Y qué película viste? Algo bueno?

Example 2 — Good conversation flow:
Tuğrul: "Este fin de semana cociné pasta"
Carolina: Ah qué rico! Yo también intenté cocinar algo turco el otro día, hice una especie de menemen pero quedó terrible, jaja. Oye y tú qué pasta hiciste, con qué salsa?"""

    else:  # English
        if level in ("A1", "A2"):
            return """Here are examples of how Carolina talks:

Example 1 — Student makes a mistake:
Tuğrul: "Yesterday I go to the office"
Carolina: Almost! Bak burada "go" değil "went" demen lazım çünkü dün olmuş bir şeyden bahsediyorsun. Türkçe'de de "gittim" dersin, "giderim" demezsin değil mi? Aynı şey. Hadi tekrar dene... "Yesterday I went to the office."

Example 2 — Student says something correct:
Tuğrul: "I have been working here for three years"
Carolina: Oh wow, that was perfect! Seriously Tuğrul, that's a tricky sentence and you nailed it. Okay so tell me more, do you like your job?

Example 3 — Student doesn't understand:
Tuğrul: "Anlamadım"
Carolina: Tamam dur açıklayım. Sana "what do you do for fun" dedim, yani "eğlenmek için ne yaparsın." "For fun" eğlence için demek. Mesela "I play guitar for fun" diyebilirsin. Hadi sen de bir şey söyle, what do you do for fun?"""
        else:
            return """Here are examples of how Carolina talks:

Example 1 — Natural correction:
Tuğrul: "I am working here since three years"
Carolina: So close! But here you need "I have been working here for three years." Şimdi bak, "since" belirli bir tarih için, "for" süre için. "Since 2022" ama "for three years." Makes sense? Try saying it again.

Example 2 — Flowing conversation:
Tuğrul: "I watched a really good series this weekend"
Carolina: Oh nice, which one? I've been looking for something new to watch actually. Was it on Netflix?"""


def ask_tutor_with_claude(student_text, target_lang, level, memory, persistent_memory=None):
    """Claude Desktop ile öğretmen yanıtı — few-shot dahil."""
    system_prompt = build_tutor_prompt(target_lang, level, memory, persistent_memory)
    profile = LANGUAGE_PROFILES[target_lang]
    example_block = _get_few_shot_example(target_lang, level)

    full_prompt = f"""{system_prompt}

{example_block}

IMPORTANT: You ARE Carolina right now. This is a live voice call with your student Tuğrul. React to what he says with genuine emotion — laugh, get excited, be playfully disappointed, encourage him. If he makes a mistake, correct it the way a real friend would, not like a textbook. Mix Turkish naturally when explaining. Keep it to 3-5 spoken sentences. No emoji, no markdown, no bullet points.

Tuğrul says: "{student_text}"

Carolina:"""

    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            # Temizlik
            text = re.sub(r'^Carolina:\s*', '', text).strip()
            text = text.strip('"').strip()
            lang_color = LANG_COLOR.get(target_lang, C.G)
            print(f"\n{lang_color}{C.BOLD}  {profile['flag']} Carolina:{C.E} {lang_color}{text}{C.E}")
            return text
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────
# EDGE TTS
# ─────────────────────────────────────────────

def init_edge_tts():
    try:
        import edge_tts
        print(f"{C.G}  ✓ Edge TTS ready{C.E}")
        return True
    except ImportError:
        print(f"{C.R}  ✗ edge-tts not found! pip install edge-tts{C.E}")
        return False


async def _tts_generate(text, voice, rate, pitch, output_file):
    import edge_tts
    c = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await c.save(output_file)


def speak(text, lang_profile):
    """Edge TTS ile sesli yanıt — dile göre ses değişir."""
    if not text:
        return

    # Markdown/emoji temizliği — TTS'e düz metin gitmeli
    clean = text
    clean = re.sub(r'[*_#`\[\](){}|\\/<>]', '', clean)
    clean = re.sub(r'✏️|👍|🇹🇷|🇬🇧|🇪🇸|→|💡', '', clean)
    clean = clean.strip()

    if not clean:
        return

    # Çok dilli TTS stratejisi:
    # Metin içinde Türkçe açıklama + hedef dil karışık olabilir
    # Edge TTS tek bir voice ile okuyacak → hedef dilin voice'unu kullan
    # Türkçe kısımlar aksanlı okunur ama anlaşılır (bu doğal — gerçek öğretmen de böyle yapar)

    voice = lang_profile["tts_voice"]
    rate = lang_profile["tts_rate"]
    pitch = lang_profile["tts_pitch"]

    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp_path = tmp.name
        tmp.close()

        asyncio.run(_tts_generate(clean, voice, rate, pitch, tmp_path))
        subprocess.run(["afplay", tmp_path], capture_output=True, timeout=60)
        os.unlink(tmp_path)

    except Exception as e:
        log_step("🔊", f"TTS error: {e}", C.R)
        try:
            subprocess.run(["say", clean], capture_output=True, timeout=30)
        except Exception:
            pass


def speak_multilingual(text, target_lang_profile):
    """
    Çok dilli TTS — Tek multilingual ses kullanarak oku.
    Artık flag'lara bağlı değil, tek seferde doğal okuyor.

    Multilingual sesler (Ava, Arabella) hem Türkçe hem hedef dili
    doğal aksanla okuyabiliyor — ayrı ayrı sese gerek yok.
    """
    # Temizlik — TTS'e düz metin
    clean = text
    clean = re.sub(r'[*_#`\[\](){}|\\/<>]', '', clean)
    clean = re.sub(r'[✏️👍💡→🇹🇷🇬🇧🇪🇸]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if not clean:
        return

    speak(clean, target_lang_profile)


# ─────────────────────────────────────────────
# PUSH-TO-TALK RECORDER
# ─────────────────────────────────────────────

class PushToTalkRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.record_thread = None
        self.input_device = self._find_mic()

    def _find_mic(self):
        default = self.p.get_default_input_device_info()
        print(f"{C.G}  ✓ Mic: {default['name']}{C.E}")
        return default['index']

    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.stream = self.p.open(
            format=pyaudio.paFloat32, channels=CHANNELS,
            rate=SAMPLE_RATE, input=True,
            input_device_index=self.input_device, frames_per_buffer=1024,
        )

        def _record():
            while self.is_recording:
                try:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    self.frames.append(np.frombuffer(data, dtype=np.float32))
                except Exception:
                    break

        self.record_thread = threading.Thread(target=_record, daemon=True)
        self.record_thread.start()

    def stop_recording(self):
        self.is_recording = False
        if self.record_thread:
            self.record_thread.join(timeout=2)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        return np.concatenate(self.frames) if self.frames else None

    def cleanup(self):
        self.p.terminate()


# ─────────────────────────────────────────────
# HALLUCINATION FİLTRESİ
# ─────────────────────────────────────────────

HALLUCINATION_PATTERNS = [
    r'^\.+$', r'^\W+$',
    r'^thanks? (for watching|you)',
    r'^(please )?subscribe',
    r'^bye[\.\s]*$',
    r'^\[.*\]$',
    r'^♪',
    r'^(music|applause|laughter)',
]


def is_hallucination(text):
    cleaned = text.strip().lower().rstrip('.')
    if len(cleaned) < 2:
        return True
    for pattern in HALLUCINATION_PATTERNS:
        if re.match(pattern, cleaned, re.IGNORECASE):
            return True
    return False


# ─────────────────────────────────────────────
# BANNER & UI
# ─────────────────────────────────────────────

def print_banner(target_lang, level):
    profile = LANGUAGE_PROFILES[target_lang]
    os.system('clear')
    print(f"""{C.CY}{C.BOLD}
╔══════════════════════════════════════════════════════════╗
║          🌍  LANGUAGE TUTOR v1  🌍                      ║
║          M4 Pro 24GB — Tamamen Yerel                    ║
╠══════════════════════════════════════════════════════════╣
║  Ana dil:   🇹🇷 Türkçe                                  ║
║  Öğrenilen: {profile['flag']} {profile['name']:<12s}  Seviye: {level:<4s}             ║
╠══════════════════════════════════════════════════════════╣
║  [Cmd+Shift] basılı tut → Konuş → Bırak                ║
║  [Cmd+Q] çıkış                                          ║
║                                                          ║
║  Herhangi bir dilde konuşabilirsin:                      ║
║  "Anlamadım" → Türkçe açıklama alırsın                  ║
║  "Tekrar et" → Öğretmen tekrar eder                      ║
║  "Daha yavaş" → Daha yavaş konuşur                       ║
╚══════════════════════════════════════════════════════════╝
{C.E}""")


def print_session_summary(memory, target_lang):
    """Ders sonu özet."""
    profile = LANGUAGE_PROFILES[target_lang]
    print(f"\n{C.CY}{C.BOLD}{'═' * 56}{C.E}")
    print(f"{C.CY}{C.BOLD}  📊 Session Summary{C.E}")
    print(f"{C.CY}{'─' * 56}{C.E}")
    print(f"  Duration:    {memory.get_session_duration()}")
    print(f"  Messages:    {memory.message_count()}")
    print(f"  Language:    {profile['flag']} {profile['name']}")

    if memory.corrections:
        print(f"  Corrections: {len(memory.corrections)}")
        print(f"\n{C.Y}  Mistakes to review:{C.E}")
        for c in memory.corrections[-5:]:
            print(f"    ✏️  \"{c['wrong']}\" → \"{c['correct']}\"")

    print(f"{C.CY}{'═' * 56}{C.E}\n")


# ─────────────────────────────────────────────
# LANGUAGE SELECTION (interactive)
# ─────────────────────────────────────────────

def select_language():
    """İnteraktif dil seçimi."""
    print(f"\n{C.BOLD}  Which language do you want to practice?{C.E}")
    print(f"  {C.EN}[1] 🇬🇧 English{C.E}")
    print(f"  {C.ES}[2] 🇪🇸 Español{C.E}")
    print()

    while True:
        try:
            choice = input(f"  {C.CY}Choose (1-2): {C.E}").strip()
            if choice == "1":
                return "en"
            elif choice == "2":
                return "es"
            else:
                print(f"  {C.Y}1 or 2 please{C.E}")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)


def select_level():
    """İnteraktif seviye seçimi."""
    print(f"\n{C.BOLD}  Your level?{C.E}")
    print(f"  {C.DIM}[1] A1 — Yeni başlıyorum{C.E}")
    print(f"  {C.DIM}[2] A2 — Temel bilgim var{C.E}")
    print(f"  {C.G}[3] B1 — Orta seviye (önerilen){C.E}")
    print(f"  {C.DIM}[4] B2 — İyi konuşabiliyorum{C.E}")
    print(f"  {C.DIM}[5] C1 — İleri seviye{C.E}")
    print(f"  {C.DIM}[6] C2 — Neredeyse ana dil{C.E}")
    print()

    levels = {"1": "A1", "2": "A2", "3": "B1", "4": "B2", "5": "C1", "6": "C2"}

    while True:
        try:
            choice = input(f"  {C.CY}Choose (1-6, default=3): {C.E}").strip()
            if not choice:
                return "B1"
            if choice in levels:
                return levels[choice]
            print(f"  {C.Y}1-6 please{C.E}")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    # Args
    parser = argparse.ArgumentParser(description="Language Tutor v1 - M1 Mac Air (8GB RAM)")
    parser.add_argument("--lang", choices=["en", "es"], help="Target language")
    parser.add_argument("--level", choices=["A1", "A2", "B1", "B2", "C1", "C2"], help="CEFR level")
    parser.add_argument("--claude", action="store_true", default=True, help="Use Claude Desktop (default for 8GB RAM)")
    parser.add_argument("--ollama", action="store_true", help="Force Ollama instead of Claude (uses more RAM)")
    parser.add_argument("--slow", action="store_true", help="Slower TTS speed")
    args = parser.parse_args()

    # Dil seçimi
    if args.lang:
        target_lang = args.lang
    else:
        os.system('clear')
        print(f"{C.CY}{C.BOLD}\n  🌍 LANGUAGE TUTOR — Setup (M1 Mac Air 8GB){C.E}\n")
        target_lang = select_language()

    # Seviye seçimi
    if args.level:
        level = args.level
    else:
        level = select_level()

    profile = LANGUAGE_PROFILES[target_lang]

    # TTS hız ayarı
    if args.slow:
        profile["tts_rate"] = "-15%"

    # Banner
    print_banner(target_lang, level)

    # ── Init Components ──

    # 1) Claude Desktop (default for 8GB RAM) / Ollama (optional)
    use_claude = args.claude and not args.ollama  # --ollama forces Ollama

    if use_claude:
        print(f"\n{C.BOLD}[1/4] Claude Desktop (Recommended for M1 8GB){C.E}")
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{C.G}  ✓ Claude CLI: {result.stdout.strip()}{C.E}")
        else:
            print(f"{C.Y}  ⚠ Claude not found, falling back to Ollama{C.E}")
            print(f"{C.DIM}  Install: npm install -g @anthropic-ai/claude-cli{C.E}")
            use_claude = False

    if not use_claude:
        print(f"\n{C.BOLD}[1/4] Ollama (Higher RAM usage){C.E}")
        if not check_ollama():
            print(f"{C.Y}  Run: ollama pull {OLLAMA_MODEL}{C.E}")
            sys.exit(1)

    # 2) Whisper
    print(f"\n{C.BOLD}[2/4] Whisper STT (MLX - Apple Silicon){C.E}")
    print(f"{C.DIM}  Using 'base' model for M1 8GB RAM{C.E}")
    whisper_engine = init_whisper()

    # 3) Edge TTS
    print(f"\n{C.BOLD}[3/4] Edge TTS{C.E}")
    if not init_edge_tts():
        sys.exit(1)
    print(f"{C.DIM}  Voice: {profile['tts_voice']}, Rate: {profile['tts_rate']}{C.E}")

    # 4) Microphone
    print(f"\n{C.BOLD}[4/4] Microphone{C.E}")
    recorder = PushToTalkRecorder()

    # ── Memory ──
    memory = ConversationMemory()
    persistent_memory = PersistentMemory(target_lang)

    # Show previous sessions info if exists
    if persistent_memory.data["total_sessions"] > 0:
        print(
            f"\n{C.CY}📚 Previous sessions: {persistent_memory.data['total_sessions']} ({persistent_memory.data['total_minutes']} min total){C.E}")
        if persistent_memory.data["recent_topics"]:
            topics = ", ".join(persistent_memory.data["recent_topics"][-3:])
            print(f"{C.DIM}   Recent topics: {topics}{C.E}")

    # ── Greeting ──
    greeting = profile["example_greeting"]
    lang_color = LANG_COLOR.get(target_lang, C.G)

    print(f"\n{C.G}{C.BOLD}  ✓ Her şey hazır!{C.E}")
    print(f"{C.DIM}{'═' * 56}{C.E}")
    print(f"\n{lang_color}{C.BOLD}  {profile['flag']} Tutor: {greeting}{C.E}\n")
    print(f"{C.DIM}  [Cmd+Shift] hold to speak | [Cmd+Q] quit{C.E}")
    print(f"{C.DIM}{'═' * 56}{C.E}")

    # Selamla (sesli)
    threading.Thread(
        target=speak, args=(greeting, profile), daemon=True
    ).start()

    memory.add_tutor(greeting)

    # ── Key Listener ──
    from pynput import keyboard

    space_pressed = threading.Event()
    space_released = threading.Event()
    quit_flag = threading.Event()
    keys_held = set()

    RECORD_COMBO = {keyboard.Key.cmd, keyboard.Key.shift}

    def on_press(key):
        keys_held.add(key)
        if RECORD_COMBO.issubset(keys_held):
            if not space_pressed.is_set():
                space_pressed.set()
                space_released.clear()
        if keyboard.Key.cmd in keys_held and hasattr(key, 'char') and key.char == 'q':
            quit_flag.set()
            return False

    def on_release(key):
        if key in RECORD_COMBO and space_pressed.is_set():
            space_released.set()
            space_pressed.clear()
        keys_held.discard(key)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # ── Main Loop ──
    turn_count = 0

    try:
        while not quit_flag.is_set():
            if space_pressed.wait(timeout=0.1):
                print(f"\n{C.R}{C.BOLD}  ● REC{C.E}", end="", flush=True)
                recorder.start_recording()

                while not space_released.is_set() and not quit_flag.is_set():
                    time.sleep(0.05)

                audio_data = recorder.stop_recording()
                print(f"\r{C.DIM}  ○ Processing...   {C.E}")

                if audio_data is None or len(audio_data) < SAMPLE_RATE * 0.3:
                    continue
                if np.sqrt(np.mean(audio_data ** 2)) < 0.005:
                    print(f"{C.DIM}  (too quiet){C.E}")
                    continue

                # ── 1) Whisper — auto-detect language ──
                start = time.time()
                student_text, detected_lang = transcribe(whisper_engine, audio_data)
                wt = time.time() - start

                if not student_text or is_hallucination(student_text):
                    log_step("🎧", f"Filtered: \"{student_text}\"", C.DIM)
                    continue

                log_step("🎧", f"Whisper ({detected_lang}): \"{student_text}\" ({wt:.1f}s)", C.DIM)

                # Display
                turn_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                detect_flag = LANGUAGE_PROFILES.get(detected_lang, {}).get("flag", "🗣️")

                print(f"\n{C.BOLD}{'─' * 56}{C.E}")
                print(f"{C.B}{C.BOLD}  🎤 [{timestamp}] You ({detect_flag}): {student_text}{C.E}")

                # Memory
                memory.add_student(student_text)

                # ── 2) Tutor Response ──
                start = time.time()

                if use_claude:
                    tutor_response = ask_tutor_with_claude(
                        student_text, target_lang, level, memory, persistent_memory
                    )
                else:
                    tutor_response = ask_tutor(
                        student_text, target_lang, level, memory, persistent_memory
                    )

                response_time = time.time() - start

                if not tutor_response:
                    fallback = "Sorry, let me try that again. Can you repeat?"
                    print(f"\n{lang_color}  {profile['flag']} Tutor: {fallback}{C.E}")
                    speak(fallback, profile)
                    continue

                # Memory
                memory.add_tutor(tutor_response)

                # Düzeltme tespiti — "casi", "no sino", "değil" gibi kalıplar
                correction_keywords = ["casi", "sino", "should be", "not.*but", "değil", "demen lazım",
                                       "kullanman lazım"]
                has_correction = any(kw in tutor_response.lower() for kw in correction_keywords)
                if has_correction:
                    memory.add_correction(
                        student_text,
                        "(see tutor response)",
                        tutor_response[:100]
                    )

                log_step("⚡", f"Response: {response_time:.1f}s", C.DIM)

                # ── 3) TTS — Sesli yanıt ──
                log_step("🔊", "Speaking...", C.DIM)
                speak_multilingual(tutor_response, profile)

                print(f"\n{C.DIM}  [Cmd+Shift] speak | [Cmd+Q] quit{C.E}")

    except KeyboardInterrupt:
        pass
    finally:
        quit_flag.set()
        listener.stop()
        recorder.cleanup()

        # Save session to persistent memory
        duration_mins = int((datetime.now() - memory.session_start).total_seconds() / 60)

        # Extract topics from conversation (simple keyword extraction)
        topics = []
        for msg in memory.messages:
            if msg["role"] == "student":
                # Basic topic extraction - words longer than 4 chars
                words = re.findall(r'\b[a-zA-Z]{5,}\b', msg["text"].lower())
                topics.extend(words[:2])  # Max 2 per message
        topics = list(set(topics))[:10]  # Unique, max 10

        persistent_memory.save_session(duration_mins, topics, memory.corrections)

        print_session_summary(memory, target_lang)
        print(f"{C.G}  ✓ Güle güle! / Goodbye! / ¡Adiós!{C.E}\n")


if __name__ == "__main__":
    main()
