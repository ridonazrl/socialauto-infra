"""
Facebook Auto-Like Bot v19 - Scroll Window 200px
"""
from playwright.sync_api import sync_playwright
import time
import random
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

ACCOUNT_PORT_MAP = {
    "akun1": 9222, "akun2": 9223, "akun3": 9224, "akun4": 9225, "akun5": 9226,
}
DEFAULT_CDP_PORT = 9222
WINDOWS_HOST = "100.114.140.47"

CONFIG = {
    "target_url": "",
    "max_likes": 1,
    "delay_between_accounts": (10, 20),
    "accounts_dir": "./accounts",
}


class AccountManager:
    def __init__(self, accounts_dir: str = "./accounts"):
        self.accounts_dir = Path(accounts_dir)
        self.accounts_dir.mkdir(parents=True, exist_ok=True)
        self.accounts_file = self.accounts_dir / "accounts.json"
        self.load_accounts()

    def load_accounts(self):
        if self.accounts_file.exists():
            try:
                with open(self.accounts_file, "r") as f:
                    self.accounts = json.load(f)
            except:
                self.accounts = []
        else:
            self.accounts = []

    def get_all_accounts(self):
        return self.accounts


class FacebookAutoLike:
    def __init__(self, config: Dict):
        self.config = config
        self.account_manager = AccountManager(config.get("accounts_dir", "./accounts"))
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_account = None

    def log(self, msg: str, level: str = "INFO"):
        t = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌"}
        account_name = f"[{self.current_account.get('name', 'unknown')}] " if self.current_account else ""
        print(f"[{t}] {account_name}{icons.get(level, 'ℹ️')} {msg}", flush=True)

    def wait(self, a: float, b: Optional[float] = None):
        time.sleep(a if b is None else random.uniform(a, b))

    def setup_browser(self, account: Dict):
        account_name = account.get("name")
        port = ACCOUNT_PORT_MAP.get(account_name, DEFAULT_CDP_PORT)
        cdp_url = f"http://{WINDOWS_HOST}:{port}"
        self.log(f"🔌 Connect ke Chrome CDP: {cdp_url}", "INFO")
        try:
            self.browser = self.playwright.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            raise Exception(f"Gagal connect ke Chrome CDP {cdp_url}: {e}")
        if self.browser.contexts:
            self.context = self.browser.contexts[0]
        else:
            self.context = self.browser.new_context()
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        self.log(f"✅ Connected ke Chrome CDP port {port}", "OK")

    def check_login(self) -> bool:
        self.log("Memeriksa login...", "INFO")
        try:
            self.page.goto("https://www.facebook.com/", timeout=30000)
            self.wait(3, 5)
            current_url = self.page.url
            self.log(f"URL: {current_url}", "INFO")
            if "facebook.com/login" in current_url or "/recover" in current_url:
                self.log("❌ Chrome CDP tidak login", "ERR")
                return False
            try:
                if self.page.locator("#email").is_visible(timeout=2000):
                    self.log("❌ Form login muncul", "ERR")
                    return False
            except:
                pass
            self.log("✅ Chrome CDP login OK", "OK")
            return True
        except Exception as e:
            self.log(f"Error check login: {e}", "ERR")
            return False

    def find_like_button_simple(self):
        """Cari tombol Like yang berada di post target/modal target."""
        try:
            # Prioritas 1: dialog yang sedang terbuka.
            dialogs = self.page.locator("[role='dialog']").all()

            self.log(f"Total dialog: {len(dialogs)}", "INFO")

            for di, dialog in enumerate(dialogs):
                try:
                    if not dialog.is_visible():
                        continue

                    text = dialog.inner_text(timeout=2000) or ""
                    self.log(
                        f"Dialog {di}: visible, text={text[:120].replace(chr(10), ' ')}",
                        "INFO"
                    )

                    # Dialog target biasanya punya judul "post" / nama halaman
                    # dan tombol Like di dalam dialog.
                    likes = dialog.locator(
                        "div[role='button'][aria-label='Like'], "
                        "div[role='button'][aria-label='Suka'], "
                        "div[role='button'][aria-label='Sukai']"
                    ).all()

                    self.log(
                        f"Dialog {di}: tombol Like={len(likes)}",
                        "INFO"
                    )

                    for i, el in enumerate(likes):
                        try:
                            if not el.is_visible():
                                continue

                            aria = (el.get_attribute("aria-label") or "").lower()

                            # Jangan klik tombol yang sudah dalam keadaan unlike.
                            if any(x in aria for x in [
                                "unlike",
                                "tidak suka",
                                "berhenti",
                                "batalkan"
                            ]):
                                self.log(
                                    f"Dialog {di} Like {i}: sudah di-like, skip",
                                    "INFO"
                                )
                                continue

                            box = el.bounding_box()
                            if not box:
                                continue

                            self.log(
                                f"✅ TARGET Like ditemukan: dialog={di}, "
                                f"index={i}, pos=({int(box['x'])},{int(box['y'])})",
                                "OK"
                            )

                            return el

                        except Exception as e:
                            self.log(
                                f"Skip dialog Like: {e}",
                                "WARN"
                            )

                except Exception as e:
                    self.log(
                        f"Skip dialog {di}: {e}",
                        "WARN"
                    )

            # Prioritas 2: cari article yang berisi target post.
            articles = self.page.locator("[role='article']").all()
            self.log(f"Fallback: total article={len(articles)}", "INFO")

            target_keywords = [
                "mushoku tensei",
                "episode 14",
                "cour 2",
                "tidak berhenti sampai"
            ]

            for ai, article in enumerate(articles):
                try:
                    if not article.is_visible():
                        continue

                    text = (article.inner_text(timeout=2000) or "").lower()

                    matched = sum(
                        1 for keyword in target_keywords
                        if keyword in text
                    )

                    if matched < 1:
                        continue

                    self.log(
                        f"🎯 Article kandidat target={ai}, "
                        f"keyword_match={matched}, "
                        f"text={text[:150].replace(chr(10), ' ')}",
                        "INFO"
                    )

                    likes = article.locator(
                        "div[role='button'][aria-label='Like'], "
                        "div[role='button'][aria-label='Suka'], "
                        "div[role='button'][aria-label='Sukai']"
                    ).all()

                    for i, el in enumerate(likes):
                        try:
                            if not el.is_visible():
                                continue

                            aria = (el.get_attribute("aria-label") or "").lower()

                            if any(x in aria for x in [
                                "unlike",
                                "tidak suka",
                                "berhenti",
                                "batalkan"
                            ]):
                                continue

                            box = el.bounding_box()
                            if not box:
                                continue

                            self.log(
                                f"✅ TARGET Like ditemukan di article {ai}, "
                                f"index={i}, "
                                f"pos=({int(box['x'])},{int(box['y'])})",
                                "OK"
                            )

                            return el

                        except Exception:
                            continue

                except Exception:
                    continue

        except Exception as e:
            self.log(f"Error find_like: {e}", "WARN")

        return None

    def like_target_post(self) -> bool:
        target_url = self.config["target_url"]

        if not target_url:
            self.log("Target URL belum diisi!", "ERR")
            return False

        self.log(f"Membuka target: {target_url}", "INFO")

        try:
            self.page.goto(target_url, timeout=60000)
            self.wait(5, 8)
        except Exception:
            self.log("Timeout membuka target", "ERR")
            return False

        current_url = self.page.url
        self.log(f"URL target: {current_url}", "INFO")

        if "login" in current_url:
            self.log("Redirect ke login", "WARN")
            return False

        self.wait(3, 5)

        self.log("Mencari tombol Like TARGET...", "INFO")

        like_button = self.find_like_button_simple()

        if not like_button:
            self.log("Target Like belum ketemu, scroll modal...", "INFO")

            try:
                self.page.mouse.wheel(0, 500)
            except Exception:
                self.page.evaluate("window.scrollBy(0, 500)")

            self.wait(2, 3)
            like_button = self.find_like_button_simple()

        if not like_button:
            self.log("❌ Tombol Like TARGET tidak ketemu", "ERR")

            try:
                self.page.screenshot(path="debug_no_target_like.png")
            except Exception:
                pass

            return False

        try:
            # Pastikan elemen masuk viewport.
            like_button.scroll_into_view_if_needed()
            self.wait(1, 2)

            box = like_button.bounding_box()

            if box:
                self.log(
                    f"🎯 Klik TARGET Like di "
                    f"({int(box['x'])},{int(box['y'])})",
                    "INFO"
                )

            # Gunakan click Playwright, bukan JS el.click().
            like_button.click(timeout=10000)

            self.wait(2, 3)

            # Verifikasi tombol berubah menjadi state unlike.
            aria_after = (
                like_button.get_attribute("aria-label") or ""
            ).lower()

            if any(x in aria_after for x in [
                "unlike",
                "tidak suka",
                "berhenti",
                "batalkan"
            ]):
                self.log("✅ Like TARGET berhasil dan terverifikasi!", "OK")
                return True

            # Beberapa UI Facebook tidak langsung mengubah aria-label.
            # Cek kembali tombol Like di container yang sama.
            try:
                parent = like_button.locator("xpath=..")
                parent_text = parent.inner_text(timeout=2000) or ""

                self.log(
                    f"State setelah klik: aria='{aria_after}', "
                    f"parent='{parent_text[:100].replace(chr(10), ' ')}'",
                    "INFO"
                )
            except Exception:
                pass

            self.log(
                "⚠️ Klik sudah dilakukan, tetapi state Like belum "
                "terverifikasi dari aria-label",
                "WARN"
            )

            return True

        except Exception as e:
            self.log(f"❌ Gagal klik Like TARGET: {e}", "ERR")
            return False

    def run_account(self, account: Dict) -> bool:
        self.current_account = account
        try:
            self.log("=" * 50, "INFO")
            self.log(f"Memproses: {account.get('name', 'unknown')}", "INFO")
            self.log(f"{'='*50}", "INFO")
            self.setup_browser(account)
            if not self.check_login():
                self.log("Login gagal", "ERR")
                return False
            return self.like_target_post()
        except Exception as e:
            self.log(f"Error: {e}", "ERR")
            return False
        finally:
            self.log("Selesai akun ini", "INFO")

    def run(self):
        if not self.config["target_url"]:
            self.log("Target URL belum diisi!", "ERR")
            return
        accounts = self.account_manager.get_all_accounts()
        if not accounts:
            self.log("Tidak ada akun!", "ERR")
            return
        self.log(f"Ditemukan {len(accounts)} akun", "INFO")
        try:
            self.playwright = sync_playwright().start()
            results = []
            for i, account in enumerate(accounts, 1):
                self.log(f"\n{'='*50}", "INFO")
                self.log(f"Akun {i}/{len(accounts)}", "INFO")
                self.log(f"{'='*50}", "INFO")
                success = self.run_account(account)
                results.append({
                    "account": account.get("name"),
                    "email": account.get("email", "unknown"),
                    "success": success,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                if i < len(accounts):
                    delay = random.uniform(*self.config["delay_between_accounts"])
                    self.log(f"Jeda {delay:.0f} detik...", "INFO")
                    time.sleep(delay)
            self.log(f"\n{'='*50}", "INFO")
            self.log("RINGKASAN HASIL:", "INFO")
            self.log(f"{'='*50}", "INFO")
            success_count = 0
            for result in results:
                status = "OK" if result["success"] else "FAIL"
                if result["success"]:
                    success_count += 1
                self.log(f"{status} {result['account']} ({result['email']})", "INFO")
            self.log(f"\nTotal berhasil: {success_count}/{len(results)}", "INFO")
            with open("results.json", "w") as f:
                json.dump(results, f, indent=2)
            self.log("Hasil disimpan ke results.json", "OK")
        except Exception as e:
            self.log(f"Fatal error: {e}", "ERR")
        finally:
            if self.playwright:
                self.playwright.stop()
            self.log("Bot selesai!", "OK")


if __name__ == "__main__":
    import sys
    config = CONFIG.copy()
    if len(sys.argv) > 1:
        config["target_url"] = sys.argv[1]
    bot = FacebookAutoLike(config)
    bot.run()
