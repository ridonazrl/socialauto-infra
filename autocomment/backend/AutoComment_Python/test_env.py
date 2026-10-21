import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
print(f"Path .env: {env_path}")
print(f"File ada? {env_path.exists()}")

load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"BERHASIL! API key: {api_key[:20]}...")
else:
    print("GAGAL: API key tidak terbaca")
    # Tampilkan semua environment variable yang mengandung 'GEMINI'
    for key, val in os.environ.items():
        if "GEMINI" in key.upper():
            print(f"  {key} = {val[:20]}...")