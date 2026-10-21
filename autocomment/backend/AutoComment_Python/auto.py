import os
import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from bot import generate_comment

# ── Mapping akun → Chrome CDP port ──
ACCOUNT_PORT_MAP = {
    "akun1": 9222,
    "akun2": 9223,
    "akun3": 9224,
    "akun4": 9225,
    "akun5": 9226,
}
DEFAULT_CDP_PORT = 9222

# ── Setup ──────────────────────────────────────────────────────────────────────
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

BASE_DIR      = Path(__file__).parent
COOKIES_DIR   = BASE_DIR / "cookies"
ACCOUNTS_DIR  = BASE_DIR / "accounts"
ACCOUNTS_FILE = ACCOUNTS_DIR / "accounts.json"
RESULTS_FILE  = BASE_DIR / "results.json"

# ── FIX: buat folder otomatis supaya tidak crash ──
COOKIES_DIR.mkdir(parents=True, exist_ok=True)
ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

# ── FIX: parsing URL lebih aman, split per baris atau koma, tapi URL Facebook 
#          dengan query string bisa mengandung koma, jadi pakai pemisah "|" 
#          kalau multiple URL. Kalau cuma 1 URL, langsung pakai.
POST_URLS_RAW = os.getenv("FB_POST_URLS", "").strip()
if POST_URLS_RAW:
    # Coba split pakai "|" dulu (aman untuk URL dgn koma)
    if "|" in POST_URLS_RAW:
        POST_URLS = [u.strip() for u in POST_URLS_RAW.split("|") if u.strip()]
    else:
        POST_URLS = [POST_URLS_RAW]
else:
    POST_URLS = []


# ── Helpers ────────────────────────────────────────────────────────────────────
def load_accounts() -> list[dict]:
    # ── FIX: handle file tidak ada / kosong tanpa crash ──
    if not ACCOUNTS_FILE.exists():
        log.error(f"❌ File akun tidak ditemukan: {ACCOUNTS_FILE}")
        log.error("   Buat file accounts/accounts.json dulu dengan format:")
        log.error('   [{"name": "akun1", "email": "a@b.com", "password": "xxx"}]')
        return []
    try:
        with open(ACCOUNTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            log.error("❌ Format accounts.json harus list/array JSON")
            return []
        return data
    except json.JSONDecodeError as e:
        log.error(f"❌ accounts.json bukan JSON valid: {e}")
        return []


def load_results() -> list[dict]:
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_results(results: list[dict]) -> None:
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def build_driver(headless: bool = False, port: int = DEFAULT_CDP_PORT) -> webdriver.Chrome:
    """
    Connect Selenium ke Chrome yang berjalan di Windows host
    via Chrome DevTools Protocol (CDP) pada port tertentu.
    """
    cdp_address = f"100.114.140.47:{port}"

    opts = Options()
    opts.add_experimental_option("debuggerAddress", cdp_address)

    service = Service("/usr/local/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=opts)

    log.info(f"✅ Connected ke Chrome CDP: {cdp_address}")
    return driver

def inject_cookies(driver: webdriver.Chrome, account_name: str) -> bool:
    """
    Skip inject cookies — Chrome CDP sudah login manual.
    Fungsi ini tetap ada biar kompatibel dengan kode lama.
    """
    log.info(f"ℹ️  Skip inject cookies, pakai session Chrome CDP untuk {account_name}")
    return True

def get_post_text(driver: webdriver.Chrome, post_url: str) -> str:
    """Ambil teks dari postingan Facebook."""
    driver.get(post_url)
    time.sleep(4)

    # Coba pakai JavaScript untuk ambil teks dari elemen post utama.
    # Strategi: cari article pertama di halaman (itu adalah post yang dituju),
    # lalu ambil semua teks di dalamnya yang bukan komentar/reaksi.
    try:
        text = driver.execute_script("""
            // Cari article pertama = post utama
            const articles = document.querySelectorAll('div[role="article"]');
            if (!articles.length) return null;

            const article = articles[0];

            // Cari elemen teks postingan — prioritaskan data-ad-preview atau data-testid
            const msgSelectors = [
                '[data-ad-preview="message"]',
                '[data-ad-comet-preview="message"]',
                '[data-testid="post_message"]',
            ];
            for (const sel of msgSelectors) {
                const el = article.querySelector(sel);
                if (el && el.innerText.trim().length > 5) {
                    return el.innerText.trim();
                }
            }

            // Fallback: ambil semua div[dir="auto"] langsung di dalam article,
            // tapi HANYA yang berada di kedalaman dangkal (bukan komentar di bawah)
            const dirAutos = article.querySelectorAll(':scope > div div[dir="auto"]');
            for (const el of dirAutos) {
                const t = el.innerText.trim();
                // Ambil yang cukup panjang dan bukan nama/label pendek
                if (t.length > 20) return t;
            }

            return null;
        """)

        if text and len(text.strip()) > 5:
            log.info(f"📄 Teks post ({len(text)} char): {text[:100]}...")
            return text.strip()
    except Exception as e:
        log.debug(f"JS extract gagal: {e}")

    # Fallback: judul halaman
    title = driver.title.replace(" | Facebook", "").strip()
    if title and len(title) > 5:
        log.warning(f"⚠️  Pakai title sebagai fallback: {title}")
        return title

    log.warning("⚠️  Tidak bisa baca teks post, pakai placeholder")
    return "Postingan Facebook"


import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException,
    StaleElementReferenceException
)
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ReadTimeout

def submit_comment(driver, comment_text: str) -> bool:
    wait = WebDriverWait(driver, 12)

    def safe_js(script, *args):
        try:
            return driver.execute_script(script, *args)
        except (ReadTimeoutError, ReadTimeout, WebDriverException) as e:
            if "timed out" in str(e).lower() or "read timed out" in str(e).lower():
                log.warning(f"[CDP TIMEOUT] {e}")
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            raise

    try:
        safe_js("window.scrollBy(0, 550);")
        time.sleep(1.8)

        comment_box_selectors = [
            "div[aria-label='Write a comment…']",
            "div[aria-label='Write a comment...']",
            "div[aria-label='Write a comment']",
            "div[aria-label='Tulis komentar…']",
            "div[aria-label='Tulis komentar...']",
            "div[aria-label='Tulis komentar']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true'][aria-label*='comment' i]",
            "div[contenteditable='true'][aria-label*='komentar' i]",
        ]

        comment_box = None
        for sel in comment_box_selectors:
            try:
                comment_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except TimeoutException:
                continue

        if not comment_box:
            log.warning("Kotak komentar tidak ditemukan")
            return False

        try:
            comment_box.click()
        except Exception:
            safe_js("arguments[0].focus(); arguments[0].click();", comment_box)
        time.sleep(0.9)

        safe_js("""
            const el = arguments[0];
            const text = arguments[1];

            el.focus();
            el.click();

            // Kosongkan dulu isi kotak komentar
            const selection = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(el);
            selection.removeAllRanges();
            selection.addRange(range);
            document.execCommand('delete', false, null);

            // Masukkan teks HANYA sekali
            document.execCommand('insertText', false, text);

            // Trigger event tanpa membawa data lagi (supaya tidak double)
            el.dispatchEvent(new Event('input',  { bubbles: true, cancelable: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """, comment_box, comment_text)

        time.sleep(1.3)

        current = (comment_box.text or "").strip()
        if len(current) < 2:
            log.warning("Teks gagal masuk ke kotak komentar")
            return False

        submitted = False

        # 1. KeyboardEvent Enter
        try:
            safe_js("""
                const el = arguments[0];
                el.focus();
                ['keydown', 'keypress', 'keyup'].forEach(type => {
                    const e = new KeyboardEvent(type, {
                        key: 'Enter', code: 'Enter',
                        keyCode: 13, which: 13,
                        bubbles: true, cancelable: true
                    });
                    el.dispatchEvent(e);
                });
            """, comment_box)
            time.sleep(2.8)
            if len((comment_box.text or "").strip()) < 2:
                submitted = True
        except Exception as e:
            log.warning(f"KeyboardEvent gagal: {e}")

        # 2. Keys.RETURN
        if not submitted:
            try:
                comment_box.send_keys(Keys.RETURN)
                time.sleep(2.5)
                if len((comment_box.text or "").strip()) < 2:
                    submitted = True
            except Exception:
                pass

        # 3. Cari & Klik Tombol Post
        if not submitted:
            log.warning("Enter gagal, cari tombol Post/Kirim...")
            post_xpaths = [
                ".//div[@aria-label='Post' and @role='button']",
                ".//div[@aria-label='Posting' and @role='button']",
                ".//div[@aria-label='Kirim' and @role='button']",
                ".//div[@role='button' and normalize-space(.)='Post']",
                ".//div[@role='button' and normalize-space(.)='Kirim']",
                ".//div[@role='button' and normalize-space(.)='Posting']",
                ".//div[@role='button']//span[normalize-space(.)='Post']/ancestor::div[@role='button'][1]",
                ".//div[@role='button']//span[normalize-space(.)='Kirim']/ancestor::div[@role='button'][1]",
            ]

            try:
                parent = comment_box.find_element(By.XPATH, "./ancestor::div[contains(@class,'x1n2onr6') or contains(@role,'article') or contains(@class,'x1y1aw1k')][1]")
            except Exception:
                parent = comment_box

            for xp in post_xpaths:
                try:
                    btn = parent.find_element(By.XPATH, xp)
                    if btn.is_displayed():
                        safe_js("arguments[0].scrollIntoView({block:'center'});", btn)
                        time.sleep(0.4)
                        try:
                            btn.click()
                        except Exception:
                            safe_js("arguments[0].click();", btn)
                        time.sleep(2.5)
                        submitted = True
                        break
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            if not submitted:
                clicked = safe_js("""
                    const labels = ['post', 'kirim', 'posting', 'send'];
                    const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
                    for (const btn of buttons) {
                        const txt = (btn.getAttribute('aria-label') || btn.innerText || '').toLowerCase().trim();
                        if (labels.some(l => txt === l || txt.startsWith(l))) {
                            btn.scrollIntoView({block: 'center'});
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                """)
                if clicked:
                    submitted = True
                    time.sleep(2.5)

        # Verifikasi Final
        time.sleep(2.5)
        short = comment_text[:35].lower()
        found = safe_js("""
            const text = arguments[0];
            const nodes = document.querySelectorAll('div[role="article"], div[dir="auto"], span[dir="auto"]');
            for (const n of nodes) {
                if (n.innerText && n.innerText.toLowerCase().includes(text)) return true;
            }
            return false;
        """, short)

        if found:
            log.info(f"✅ VERIFIED: Komentar muncul di list komentar")
            return True
        else:
            log.warning(f"⚠️ Komentar TIDAK terverifikasi (mungkin belum render)")
            return False

    except (ReadTimeoutError, ReadTimeout, TimeoutException, WebDriverException) as e:
        err = str(e).lower()
        if "timed out" in err or "read timed out" in err:
            log.warning(f"[TIMEOUT HANDLED] Akun ini dilewati: {e}")
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
            return False
        log.error(f"Error lain: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return False

def run_autocomment(post_urls: list[str], headless: bool = False) -> None:
    if not post_urls:
        log.error("❌ Tidak ada URL post yang diisi. Set FB_POST_URLS di .env atau edit auto.py")
        return

    accounts = load_accounts()
    if not accounts:
        log.error("❌ Tidak ada akun yang bisa diproses. Berhenti.")
        return

    results = load_results()

    log.info(f"🚀 Mulai proses: {len(accounts)} akun × {len(post_urls)} post")

    for idx, account in enumerate(accounts, 1):
        name  = account.get("name", "unknown")
        email = account.get("email", "")
        log.info(f"\n{'='*50}")
        log.info(f"👤 Akun {idx}/{len(accounts)}: {name} ({email})")
        log.info(f"{'='*50}")

        driver = None  # ── FIX: init dulu supaya aman di finally ──
        try:
            # Ambil port dari mapping akun
            cdp_port = ACCOUNT_PORT_MAP.get(name, DEFAULT_CDP_PORT)
            log.info(f"🔌 Menggunakan Chrome CDP port {cdp_port} untuk {name}")
            driver = build_driver(headless=False, port=cdp_port)

            # Inject cookies
            if not inject_cookies(driver, name):
                log.error(f"❌ Gagal load cookies untuk {name}, skip akun ini")
                results.append({
                    "account": name,
                    "email": email,
                    "success": False,
                    "error": "Cookies tidak ditemukan/invalid",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                save_results(results)
                continue

            # Chrome CDP sudah login — cek status via feed
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            current_url = driver.current_url.lower()

            if "facebook.com/login" in current_url or "/recover" in current_url:
                log.error(f"❌ Chrome CDP tidak login untuk {name}")
                results.append({
                    "account": name,
                    "email": email,
                    "success": False,
                    "error": "Chrome CDP tidak login",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                save_results(results)
                continue

            try:
                driver.find_element(By.CSS_SELECTOR, "input#email[name='email']")
                log.error(f"❌ Form login muncul untuk {name}")
                results.append({
                    "account": name, "email": email, "success": False,
                    "error": "Form login muncul",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                save_results(results)
                continue
            except NoSuchElementException:
                pass

            log.info(f"✅ Chrome CDP login OK untuk {name}")

            # Proses setiap post URL
            for url in post_urls:
                log.info(f"\n🔗 Post: {url}")
                try:
                    post_text = get_post_text(driver, url)
                    comment   = generate_comment(post_text)

                    success = submit_comment(driver, comment)

                    results.append({
                        "account":   name,
                        "email":     email,
                        "post_url":  url,
                        "comment":   comment,
                        "success":   success,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    save_results(results)

                    if success:
                        log.info(f"✅ Selesai komentar di: {url}")
                    else:
                        log.warning(f"⚠️  Gagal submit komentar di: {url}")

                except Exception as e:
                    log.error(f"❌ Error di {url}: {e}")
                    results.append({
                        "account":   name,
                        "email":     email,
                        "post_url":  url,
                        "success":   False,
                        "error":     str(e),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    save_results(results)

                # Jeda antar post
                if len(post_urls) > 1:
                    delay = random.uniform(5, 12)
                    log.info(f"⏳ Jeda {delay:.1f} detik...")
                    time.sleep(delay)

        except Exception as e:
            log.error(f"❌ Error tak terduga untuk akun {name}: {e}")
        finally:
            # ── FIX: cek driver None dulu ──
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                log.info(f"🔒 Browser {name} ditutup")

        # Jeda antar akun
        if idx < len(accounts):
            delay = random.uniform(8, 15)
            log.info(f"⏳ Jeda {delay:.1f} detik sebelum akun berikutnya...")
            time.sleep(delay)

    log.info(f"\n{'='*50}")
    log.info("🏁 Semua akun selesai diproses")
    log.info(f"📄 Hasil tersimpan di: {RESULTS_FILE}")


def prompt_input(label: str, required: bool = True, secret: bool = False) -> str:
    """Input helper dengan validasi tidak boleh kosong."""
    import getpass
    while True:
        try:
            value = (getpass.getpass(f"  {label} : ") if secret
                     else input(f"  {label} : ").strip())
        except (EOFError, KeyboardInterrupt):
            return ""
        if value:
            return value
        if not required:
            return ""
        print("  ⚠️  Tidak boleh kosong, coba lagi.\n")


# ── State sesi (disimpan selama program berjalan) ──────────────────────────────
_state = {
    "post_url": "",       # URL post yang akan dikomentari
    "accounts": [],       # list akun: [{name, email, password, cookies_path}]
}


def menu_set_url() -> None:
    """Opsi 1 — Set URL post Facebook."""
    print("\n📌 Set URL Post Facebook")
    print(f"  URL sekarang: {_state['post_url'] or '(belum diisi)'}\n")
    while True:
        url = prompt_input("Masukkan URL post")
        if "facebook.com" in url:
            _state["post_url"] = url
            print(f"\n  ✅ URL disimpan: {url}\n")
            break
        print("  ❌ Bukan URL Facebook yang valid, coba lagi.\n")


def save_accounts(accounts: list[dict]) -> None:
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)


def menu_add_account() -> None:
    """Opsi 2 — Manajemen akun: tambah baru, pilih, atau import cookies."""
    while True:
        all_accounts = load_accounts()

        print("\n" + "="*55)
        print("  👤  Manajemen Akun")
        print("="*55)
        print(f"  Akun tersimpan: {len(all_accounts)}\n")
        for i, acc in enumerate(all_accounts, 1):
            cookies_path = COOKIES_DIR / f"{acc['name']}_cookies.json"
            cookie_status = "🍪✅" if cookies_path.exists() else "🍪❌"
            selected = " [DIPILIH]" if any(
                a["email"] == acc["email"] for a in _state["accounts"]
            ) else ""
            print(f"  [{i}] {acc['name']} ({acc['email']}) {cookie_status}{selected}")
        print("-"*55)
        print("  [A] Tambah akun baru")
        print("  [C] Import cookies untuk akun")
        print("  [H] Hapus akun")
        print("  [0] Kembali ke menu utama")
        print("="*55)

        pilihan = input("\n  Pilih : ").strip().upper()

        if pilihan == "0":
            break

        elif pilihan == "A":
            # ── Tambah akun baru ──────────────────────────────
            print("\n  ➕ Tambah Akun Baru\n")
            nama  = prompt_input("Nama akun (contoh: akun2)")
            email = prompt_input("Email Facebook")
            password = prompt_input("Password")

            # Cek duplikat
            if any(a["email"] == email for a in all_accounts):
                print(f"\n  ⚠️  Akun dengan email '{email}' sudah ada.\n")
                continue

            all_accounts.append({
                "name":       nama,
                "email":      email,
                "password":   password,
                "created_at": datetime.now().isoformat(),
            })
            save_accounts(all_accounts)
            print(f"\n  ✅ Akun '{nama}' ({email}) berhasil disimpan ke accounts.json\n")

        elif pilihan == "C":
            # ── Import cookies ────────────────────────────────
            if not all_accounts:
                print("\n  ❌ Belum ada akun. Tambah akun dulu (pilih A).\n")
                continue

            print("\n  🍪 Import Cookies\n")
            for i, acc in enumerate(all_accounts, 1):
                print(f"  [{i}] {acc['name']} ({acc['email']})")
            print()

            pilih_akun = input("  Pilih akun : ").strip()
            if not pilih_akun.isdigit() or not (1 <= int(pilih_akun) <= len(all_accounts)):
                print("\n  ❌ Pilihan tidak valid.\n")
                continue

            acc          = all_accounts[int(pilih_akun) - 1]
            cookies_path = COOKIES_DIR / f"{acc['name']}_cookies.json"

            print(f"\n  Akun: {acc['name']} ({acc['email']})")
            print(f"  Cookies akan disimpan ke: {cookies_path.name}\n")
            print("  Pilih cara import:")
            print("  [1] Path file cookies (dari browser extension export)")
            print("  [2] Paste isi JSON cookies langsung\n")

            cara = input("  Pilih : ").strip()

            if cara == "1":
                while True:
                    raw = prompt_input("Path file cookies").strip('"').strip("'")
                    src = Path(raw)
                    if not src.is_absolute():
                        src = BASE_DIR / src
                    if src.exists():
                        # Validasi isinya JSON valid
                        try:
                            with open(src, encoding="utf-8") as f:
                                data = json.load(f)
                            # Salin ke folder cookies dengan nama yang benar
                            with open(cookies_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2)
                            print(f"\n  ✅ Cookies berhasil diimport ke {cookies_path.name}\n")
                            break
                        except json.JSONDecodeError:
                            print("  ❌ File bukan JSON yang valid, coba lagi.\n")
                    else:
                        print(f"  ❌ File tidak ditemukan: {src}, coba lagi.\n")

            elif cara == "2":
                print("\n  Paste isi JSON cookies di bawah ini.")
                print("  Setelah selesai paste, ketik baris baru lalu ketik 'DONE' dan tekan Enter:\n")
                lines = []
                while True:
                    try:
                        line = input()
                    except EOFError:
                        break
                    if line.strip().upper() == "DONE":
                        break
                    lines.append(line)

                raw_json = "\n".join(lines)
                try:
                    data = json.loads(raw_json)
                    with open(cookies_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"\n  ✅ Cookies berhasil disimpan ke {cookies_path.name}\n")
                except json.JSONDecodeError as e:
                    print(f"\n  ❌ JSON tidak valid: {e}\n")
            else:
                print("\n  ⚠️  Pilihan tidak valid.\n")

        elif pilihan == "H":
            # ── Hapus akun ────────────────────────────────────
            if not all_accounts:
                print("\n  ❌ Belum ada akun.\n")
                continue

            print()
            for i, acc in enumerate(all_accounts, 1):
                print(f"  [{i}] {acc['name']} ({acc['email']})")
            print()

            pilih_hapus = input("  Pilih akun yang dihapus : ").strip()
            if not pilih_hapus.isdigit() or not (1 <= int(pilih_hapus) <= len(all_accounts)):
                print("\n  ❌ Pilihan tidak valid.\n")
                continue

            idx_hapus = int(pilih_hapus) - 1
            acc_hapus = all_accounts.pop(idx_hapus)
            save_accounts(all_accounts)

            # Hapus cookies-nya juga kalau ada
            cookies_path = COOKIES_DIR / f"{acc_hapus['name']}_cookies.json"
            if cookies_path.exists():
                cookies_path.unlink()
                print(f"\n  ✅ Akun '{acc_hapus['name']}' dan cookies-nya berhasil dihapus.\n")
            else:
                print(f"\n  ✅ Akun '{acc_hapus['name']}' berhasil dihapus.\n")

        else:
            print("\n  ⚠️  Pilihan tidak valid.\n")


def menu_run_bot() -> None:
    """Opsi 3 — Jalankan bot."""
    print()

    # Validasi URL
    if not _state["post_url"]:
        print("  ❌ URL post belum diisi (pilih opsi 1)\n")
        return

    # Langsung pakai semua akun dari accounts.json
    all_accounts = load_accounts()
    if not all_accounts:
        print("  ❌ Belum ada akun. Tambah akun dulu (pilih opsi 2)\n")
        return

    # Bangun daftar akun beserta cookies-nya
    accounts_to_run = []
    for acc in all_accounts:
        cookies_path = COOKIES_DIR / f"{acc['name']}_cookies.json"
        if not cookies_path.exists():
            print(f"  ⚠️  Skip {acc['name']}: cookies belum diimport")
            continue
        accounts_to_run.append({
            "name":         acc["name"],
            "email":        acc["email"],
            "password":     acc.get("password", ""),
            "cookies_path": cookies_path,
        })

    if not accounts_to_run:
        print("  ❌ Tidak ada akun yang punya cookies. Import cookies dulu (opsi 2 → C)\n")
        return

    # Ringkasan
    print("="*55)
    print(f"  🔗 Post    : {_state['post_url']}")
    print(f"  👤 Akun    : {len(accounts_to_run)} akun")
    for acc in accounts_to_run:
        print(f"             - {acc['name']} ({acc['email']})")
    print("="*55)

    confirm = input("\n  Mulai komentar? (y/n) : ").strip().lower()
    if confirm != "y":
        print("\n⛔ Dibatalkan.\n")
        return

    url     = _state["post_url"]
    results = load_results()

    for idx, account in enumerate(accounts_to_run, 1):
        name         = account["name"]
        email        = account["email"]
        cookies_path = account["cookies_path"]

        print()
        log.info(f"{'='*50}")
        log.info(f"👤 Akun {idx}/{len(accounts_to_run)}: {name} ({email})")
        log.info(f"{'='*50}")

        driver = None
        try:
            # Ambil port dari mapping akun
            cdp_port = ACCOUNT_PORT_MAP.get(name, DEFAULT_CDP_PORT)
            log.info(f"🔌 Menggunakan Chrome CDP port {cdp_port} untuk {name}")
            driver = build_driver(headless=False, port=cdp_port)

            # Inject cookies
            # Skip inject cookies — Chrome CDP sudah login manual
            log.info(f"ℹ️  Skip inject cookies, pakai session Chrome CDP")

            # Cek login via Chrome CDP
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            if "facebook.com/login" in driver.current_url.lower():
                log.error(f"❌ Chrome CDP tidak login untuk {name}")
                results.append({
                    "account": name, "email": email, "post_url": url,
                    "success": False, "error": "Chrome CDP tidak login",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                save_results(results)
                continue

            try:
                driver.find_element(By.CSS_SELECTOR, "input#email[name='email']")
                log.error(f"❌ Form login muncul untuk {name}")
                results.append({
                    "account": name, "email": email, "post_url": url,
                    "success": False, "error": "Form login muncul",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                save_results(results)
                continue
            except NoSuchElementException:
                pass

            log.info(f"✅ Chrome CDP login OK untuk {name}")

            post_text = get_post_text(driver, url)
            comment   = generate_comment(post_text)
            success   = submit_comment(driver, comment)

            results.append({
                "account":   name,
                "email":     email,
                "post_url":  url,
                "comment":   comment,
                "success":   success,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_results(results)

            if success:
                log.info(f"✅ Komentar berhasil dikirim: {comment}")
            else:
                log.warning(f"⚠️  Komentar gagal dikirim")

        except Exception as e:
            log.error(f"❌ Error: {e}")
            results.append({
                "account": name, "email": email, "post_url": url,
                "success": False, "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_results(results)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            log.info(f"🔒 Browser {name} ditutup")

        if idx < len(accounts_to_run):
            delay = random.uniform(8, 15)
            log.info(f"⏳ Jeda {delay:.1f} detik sebelum akun berikutnya...")
            time.sleep(delay)

    log.info(f"\n🏁 Selesai! Hasil tersimpan di: {RESULTS_FILE}")


def show_menu() -> None:
    """Tampilkan menu utama."""
    all_accounts = load_accounts()
    akun_count   = len(all_accounts)
    akun_status  = f"{akun_count} akun" if akun_count else "(belum ada)"
    url_status   = _state["post_url"] or "(belum diisi)"

    print("\n" + "="*55)
    print("  🤖  Facebook AutoComment — powered by Gemini AI")
    print("="*55)
    print(f"  🔗 Post URL : {url_status}")
    print(f"  👤 Akun     : {akun_status}")
    print("-"*55)
    print("  [1] Set URL post")
    print("  [2] Kelola akun")
    print("  [3] Jalankan bot")
    print("  [0] Keluar")
    print("="*55)


if __name__ == "__main__":
    try:
        while True:
            show_menu()
            pilihan = input("\n  Pilih menu : ").strip()

            if pilihan == "1":
                menu_set_url()
            elif pilihan == "2":
                menu_add_account()
            elif pilihan == "3":
                menu_run_bot()
            elif pilihan == "0":
                print("\n👋 Sampai jumpa!\n")
                break
            else:
                print("\n  ⚠️  Pilihan tidak valid, coba lagi.\n")

    except KeyboardInterrupt:
        print("\n\n⛔ Dihentikan oleh user (Ctrl+C)\n")
    except Exception as e:
        log.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()



