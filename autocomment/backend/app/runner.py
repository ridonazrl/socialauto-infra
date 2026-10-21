import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
import logging

from app.config import AUTO_PY, REPO_DIR, PYTHON_BIN, DEFAULT_TIMEOUT_SECONDS

logger = logging.getLogger("autocomment_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class ScriptRunner:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._process: Optional[asyncio.subprocess.Process] = None
        self._is_running: bool = False
        self._current_logs: List[str] = []
        self._subscribers: List[asyncio.Queue] = []
        self._start_time: Optional[float] = None
        self._last_result: Optional[Dict] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def last_result(self) -> Optional[Dict]:
        return self._last_result

    def _broadcast_log(self, line: str):
        """Append to log buffer and broadcast to any SSE queue."""
        self._current_logs.append(line)
        for q in list(self._subscribers):
            try:
                q.put_nowait(line)
            except Exception:
                pass

    async def subscribe_logs(self) -> AsyncGenerator[str, None]:
        """Subscribe to real-time logs stream."""
        q = asyncio.Queue()
        # First send any logs collected so far in this run
        for line in self._current_logs:
            await q.put(line)
        self._subscribers.append(q)
        try:
            while True:
                line = await q.get()
                if line == "__STREAM_END__":
                    break
                yield line
        finally:
            if q in self._subscribers:
                self._subscribers.remove(q)

    async def stop(self) -> Dict:
        """Terminate the running process if active."""
        if not self._is_running or not self._process:
            return {"status": "error", "message": "Tidak ada proses yang sedang berjalan"}

        try:
            self._process.terminate()
            self._broadcast_log("\n[RUNNER] ⚠️ Sinyal TERMINATE dikirim ke proses...")
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                self._broadcast_log("[RUNNER] ⛔ Proses dihentikan paksa (SIGKILL).")
            return {"status": "success", "message": "Proses berhasil dihentikan"}
        except Exception as e:
            return {"status": "error", "message": f"Gagal menghentikan proses: {str(e)}"}

    async def run(
        self,
        post_url: Optional[str] = None,
        headless: bool = False,
        mode: str = "direct",
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> Dict:
        """
        Executes auto.py inside the target repository.
        
        mode:
          - "direct": invokes run_autocomment([url], headless=headless) from auto.py
          - "interactive": runs `python auto.py` feeding simulated stdin for menu choices
        """
        if self._lock.locked():
            return {
                "status": "error",
                "message": "Script auto.py sedang berjalan. Harap tunggu hingga selesai atau hentikan proses sebelumnya.",
                "returncode": -1,
                "stdout": "",
                "stderr": "Conflict: Another run is currently in progress",
                "execution_time_seconds": 0.0,
            }

        async with self._lock:
            if not REPO_DIR.exists():
                return {
                    "status": "error",
                    "message": f"Direktori repository tidak ditemukan di {REPO_DIR}",
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Repository directory not found at {REPO_DIR}",
                    "execution_time_seconds": 0.0,
                }

            if not AUTO_PY.exists():
                return {
                    "status": "error",
                    "message": f"File auto.py tidak ditemukan di {AUTO_PY}",
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"File not found: {AUTO_PY}",
                    "execution_time_seconds": 0.0,
                }

            self._is_running = True
            self._current_logs = []
            self._start_time = time.time()
            start_iso = datetime.now().isoformat()

            # Ensure clean environment
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            if post_url:
                env["FB_POST_URLS"] = post_url

            stdin_data = None
            cmd = []

            if mode == "interactive":
                # Run `python -u auto.py` with menu input simulation:
                # 1 = set url, then url, 3 = run bot, y = confirm, 0 = exit
                cmd = [PYTHON_BIN, "-u", str(AUTO_PY)]
                if post_url:
                    stdin_data = f"1\n{post_url}\n3\ny\n0\n"
                else:
                    stdin_data = "3\ny\n0\n"
            else:
                # Direct mode: call run_autocomment function from auto.py cleanly
                script_code = (
                    "import sys, os\n"
                    "from auto import run_autocomment\n"
                    f"url = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else os.getenv('FB_POST_URLS', '')\n"
                    f"headless_val = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else False\n"
                    "urls = [url] if url else []\n"
                    "print(f'[RUNNER] Menjalankan auto.py dengan URL: {urls}, Headless: {headless_val}')\n"
                    "run_autocomment(urls, headless=headless_val)\n"
                )
                cmd = [
                    PYTHON_BIN,
                    "-u",
                    "-c",
                    script_code,
                    post_url or "",
                    str(headless),
                ]

            self._broadcast_log(f"[RUNNER] 🚀 Memulai auto.py pada {start_iso}")
            self._broadcast_log(f"[RUNNER] 📂 Working Directory: {REPO_DIR}")
            self._broadcast_log(f"[RUNNER] ⚙️  Mode: {mode}, Headless: {headless}")
            if post_url:
                self._broadcast_log(f"[RUNNER] 🔗 Target URL: {post_url}")
            self._broadcast_log("-" * 60)

            stdout_chunks: List[str] = []
            stderr_chunks: List[str] = []

            try:
                self._process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE if stdin_data else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(REPO_DIR),
                    env=env,
                )

                async def read_stream(stream, is_stderr: bool):
                    while True:
                        line_bytes = await stream.readline()
                        if not line_bytes:
                            break
                        line = line_bytes.decode(errors="replace")
                        if is_stderr:
                            stderr_chunks.append(line)
                            prefix = "[STDERR] "
                        else:
                            stdout_chunks.append(line)
                            prefix = ""
                        self._broadcast_log(prefix + line.rstrip("\r\n"))

                # Write stdin if applicable
                if stdin_data and self._process.stdin:
                    try:
                        self._process.stdin.write(stdin_data.encode())
                        await self._process.stdin.drain()
                        self._process.stdin.close()
                    except Exception as e:
                        logger.warning(f"Error writing to stdin: {e}")

                # Read stdout and stderr concurrently
                await asyncio.wait_for(
                    asyncio.gather(
                        read_stream(self._process.stdout, False),
                        read_stream(self._process.stderr, True),
                        self._process.wait(),
                    ),
                    timeout=timeout,
                )

                returncode = self._process.returncode

            except asyncio.TimeoutError:
                self._broadcast_log(f"\n[RUNNER] ❌ Timeout: Eksekusi melebihi batas {timeout} detik.")
                if self._process:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                returncode = -1
                stderr_chunks.append(f"TimeoutError: Process exceeded {timeout} seconds\n")

            except Exception as e:
                self._broadcast_log(f"\n[RUNNER] ❌ Error internal subprocess: {str(e)}")
                returncode = -1
                stderr_chunks.append(str(e))

            finally:
                duration = round(time.time() - self._start_time, 2)
                self._is_running = False
                self._process = None

                full_stdout = "".join(stdout_chunks)
                full_stderr = "".join(stderr_chunks)

                status = "success" if returncode == 0 else "error"
                self._broadcast_log("-" * 60)
                self._broadcast_log(
                    f"[RUNNER] 🏁 Eksekusi selesai dengan status '{status}' (Exit Code: {returncode}) dalam {duration} detik."
                )

                # Send stream end to any SSE subscribers
                for q in list(self._subscribers):
                    try:
                        q.put_nowait("__STREAM_END__")
                    except Exception:
                        pass

                result = {
                    "status": status,
                    "message": (
                        "Eksekusi auto.py selesai dengan sukses."
                        if returncode == 0
                        else f"Eksekusi auto.py gagal dengan kode keluar {returncode}."
                    ),
                    "returncode": returncode,
                    "stdout": full_stdout,
                    "stderr": full_stderr,
                    "full_logs": "\n".join(self._current_logs),
                    "execution_time_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "post_url": post_url or "",
                    "headless": headless,
                    "mode": mode,
                }
                self._last_result = result
                return result


# Singleton instance
runner = ScriptRunner()
