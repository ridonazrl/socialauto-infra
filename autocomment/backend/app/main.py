import json
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import (
    ACCOUNTS_FILE,
    AUTO_PY,
    COOKIES_DIR,
    CORS_ORIGINS,
    REPO_DIR,
    REPO_ENV_FILE,
    RESULTS_FILE,
)
from app.runner import runner

app = FastAPI(
    title="AutoComment Web Runner API",
    description="Backend API untuk memicu dan memonitor eksekusi auto.py Facebook Comment Bot",
    version="1.0.0",
)

# Enable CORS for Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    post_url: Optional[str] = Field(
        default=None,
        description="URL target postingan Facebook yang ingin dikomentari",
        example="https://www.facebook.com/zuck/posts/10115291244302911",
    )
    headless: bool = Field(
        default=False,
        description="Jalankan browser Chrome dalam mode headless (tanpa GUI)",
    )
    mode: str = Field(
        default="direct",
        description="Mode eksekusi: 'direct' (panggil fungsi run_autocomment) atau 'interactive' (simulasi CLI menu)",
    )


class StopResponse(BaseModel):
    status: str
    message: str


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AutoComment Fullstack Backend",
        "repo_dir": str(REPO_DIR),
        "auto_py_exists": AUTO_PY.exists(),
        "is_running": runner.is_running,
    }


@app.get("/status")
def get_status():
    """Mengembalikan status sistem saat ini dan kesiapan script."""
    has_gemini = False
    if REPO_ENV_FILE.exists():
        with open(REPO_ENV_FILE, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            has_gemini = "GEMINI_API_KEY=" in content and len(content.split("GEMINI_API_KEY=")[1].split("\n")[0].strip()) > 20

    accounts_count = 0
    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts_data = json.load(f)
                if isinstance(accounts_data, list):
                    accounts_count = len(accounts_data)
        except Exception:
            pass

    return {
        "is_running": runner.is_running,
        "repo_dir": str(REPO_DIR),
        "repo_exists": REPO_DIR.exists(),
        "auto_py_exists": AUTO_PY.exists(),
        "accounts_count": accounts_count,
        "has_gemini_api_key": has_gemini,
        "last_result": runner.last_result,
    }


@app.post("/run-autocomment")
async def run_autocomment(req: RunRequest):
    """
    Endpoint utama untuk memicu eksekusi auto.py.
    Menjalankan script via subprocess dan mengembalikan stdout/stderr sebagai JSON response.
    """
    if runner.is_running:
        raise HTTPException(
            status_code=409,
            detail="Script auto.py sedang berjalan. Harap tunggu hingga selesai atau batalkan proses aktif.",
        )

    result = await runner.run(
        post_url=req.post_url,
        headless=req.headless,
        mode=req.mode,
    )
    return result


@app.post("/stop", response_model=StopResponse)
async def stop_autocomment():
    """Hentikan paksa proses auto.py yang sedang berjalan."""
    res = await runner.stop()
    return res


@app.get("/stream-logs")
async def stream_logs():
    """Server-Sent Events (SSE) endpoint untuk streaming live console log."""
    async def event_generator():
        async for line in runner.subscribe_logs():
            yield f"data: {line}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/accounts")
def get_accounts():
    """Mengambil daftar akun yang terdaftar beserta status ketersediaan cookies-nya."""
    if not ACCOUNTS_FILE.exists():
        return {"accounts": []}

    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        if not isinstance(accounts, list):
            return {"accounts": []}

        enriched = []
        for acc in accounts:
            name = acc.get("name", "")
            cookie_file = COOKIES_DIR / f"{name}_cookies.json"
            enriched.append({
                "name": name,
                "email": acc.get("email", ""),
                "has_cookies": cookie_file.exists(),
                "created_at": acc.get("created_at", ""),
            })
        return {"accounts": enriched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membaca accounts.json: {str(e)}")


@app.get("/results")
def get_results(limit: int = Query(default=50, ge=1, le=200)):
    """Mengambil riwayat eksekusi komentar dari results.json."""
    if not RESULTS_FILE.exists():
        return {"results": []}

    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
        if not isinstance(results, list):
            return {"results": []}

        # Urutkan dari yang terbaru
        results_reversed = list(reversed(results))[:limit]
        return {"results": results_reversed, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membaca results.json: {str(e)}")
