"""Bot comment generator dengan multi-provider fallback.

Primary: Google Gemini (gemini-3.8-flash)
Fallback 1: Groq (llama-3.3-70b-versatile)
Fallback 2: Template statis (last resort)
"""

import os
import time
import random
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# === KONFIGURASI ===
GEMINI_MODEL = "gemini-3.8-flash"
GROQ_MODEL = "openai/gpt-oss-120b"
MAX_RETRIES = 3

# Prompt yang sama untuk semua provider
PROMPT_TEMPLATE = (
    "Baca postingan media sosial berikut dan buatkan komentar yang:\n"
    "1. Relevan dengan isi dan konteks postingan\n"
    "2. Bersifat positif, ramah, dan membangun\n"
    "3. Menggunakan bahasa yang natural, santai, dan mengalir\n"
    "4. Cukup 1 kalimat saja, singkat dan padat\n"
    "5. Kalimat harus utuh dan bermakna, bukan sekadar pujian pendek\n"
    "6. Boleh menambahkan kesan atau opini singkat\n"
    "7. Jangan gunakan emoji berlebihan (maksimal 1 emoji)\n"
    "8. Hanya balas dengan teks komentarnya saja, tanpa penjelasan tambahan\n"
    "9. Jangan gunakan tanda kutip di awal/akhir komentar\n\n"
    "Postingan: {post_text}\n\n"
    "Komentar:"
)

# === TEMPLATE STATIS (LAST RESORT) ===
STATIC_TEMPLATES = [
    "Keren banget, semoga makin sukses terus ya! 👍",
    "Mantap, terus konsisten bikin konten sebagus ini! 🔥",
    "Bagus banget sharingnya, semoga bermanfaat buat banyak orang! 🙌",
    "Setuju banget, semangat terus ya! 💪",
    "Inspiratif sekali, terima kasih sudah berbagi! ✨",
    "Kontennya relate banget, sukses terus! 🚀",
    "Nice postingan, ditunggu konten selanjutnya! 👏",
    "Terima kasih sharingnya, sangat menginspirasi! 🌟",
]


def _is_retryable_error(err_str: str) -> bool:
    """Cek apakah error termasuk retryable (server sibuk / rate limit)."""
    err_str = err_str.lower()
    keywords = [
        "503", "unavailable", "high demand", "service unavailable",
        "429", "rate limit", "too many requests",
        "500", "502", "504", "timeout", "timed out",
    ]
    return any(k in err_str for k in keywords)


def _generate_via_gemini(post_text: str) -> str:
    """Generate komentar via Google Gemini dengan retry agresif (maks 1x)."""
    try:
        from google import genai
    except ImportError:
        raise Exception("SDK google-genai tidak terinstall")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY belum diisi di .env")

    client = genai.Client(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(post_text=post_text)

    max_attempts = 2  # Attempt 1 + 1 retry

    for attempt in range(1, max_attempts + 1):
        try:
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt,
            )
            comment = (interaction.output_text or "").strip()
            if not comment:
                raise Exception("Respons Gemini kosong")
            print(f"💬 Komentar (gemini): {comment}")
            return comment
            
        except Exception as e:
            err_str = str(e)
            is_503 = _is_retryable_error(err_str)
            
            if is_503 and attempt < max_attempts:
                print(f"⚠️ Gemini 503, retry dalam 5s... (attempt {attempt}/{max_attempts})")
                time.sleep(5)
                continue
            else:
                raise Exception(f"Gemini gagal: {err_str}") from e

def _generate_via_groq(post_text: str) -> str:
    """Generate komentar via Groq (fallback AI)."""
    try:
        from groq import Groq
    except ImportError:
        raise Exception("SDK groq tidak terinstall — tambah 'groq' ke requirements.txt")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY belum diisi di .env")

    client = Groq(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(post_text=post_text)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200,
            )
            comment = (response.choices[0].message.content or "").strip()
            # Strip quote kalau ada
            comment = comment.strip('"').strip("'").strip()
            if not comment:
                raise Exception("Respons Groq kosong")
            print(f"💬 Komentar (groq): {comment}")
            return comment
        except Exception as e:
            last_error = e
            err_str = str(e)

            if _is_retryable_error(err_str) and attempt < MAX_RETRIES - 1:
                wait = 10 * (attempt + 1)  # 10s, 20s
                print(f"⚠️ Groq error (retryable), retry dalam {wait}s... "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            break

    raise Exception(f"Groq gagal setelah {MAX_RETRIES} attempt: {last_error}")


def _generate_via_template() -> str:
    """Generate komentar dari template statis (last resort)."""
    comment = random.choice(STATIC_TEMPLATES)
    print(f"⚠️ Komentar via TEMPLATE STATIS (last resort): {comment}")
    return comment


def generate_comment(post_text: str, max_retries: int = 3) -> str:
    """Generate komentar dengan multi-provider fallback.

    Alur:
        1. Gemini (retry 3x)
        2. Groq (retry 3x) — kalau Gemini gagal
        3. Template statis — kalau semua AI gagal

    Args:
        post_text: Teks postingan
        max_retries: (unused, disimpan buat backward-compat)

    Returns:
        String komentar
    """
    # === [1] COBA GEMINI ===
    try:
        print("🔵 [Primary] Coba Gemini...")
        return _generate_via_gemini(post_text)
    except Exception as e:
        print(f"❌ Gemini gagal: {e}")

    # === [2] COBA GROQ ===
    try:
        print("🟡 [Fallback 1] Coba Groq...")
        return _generate_via_groq(post_text)
    except Exception as e:
        print(f"❌ Groq gagal: {e}")

    # === [3] TEMPLATE STATIS ===
    print("🔴 [Fallback 2] Semua AI gagal, pake template statis...")
    return _generate_via_template()


if __name__ == "__main__":
    test = generate_comment("Hari ini cuacanya cerah sekali, matahari bersinar terang.")
    print(f"\nHasil: {test}")
