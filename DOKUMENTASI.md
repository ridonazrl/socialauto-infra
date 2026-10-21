# Dokumentasi Sistem — SocialAuto.tech

## 1. Arsitektur Infrastruktur
- **VPS:** Hostinger (Ubuntu 22.04) | IP: `187.77.119.183`
- **Domain Utama:** `socialauto.tech` (SSL Let's Encrypt Aktif)
- **Subdomain Auto-Comment (ACM):** `https://acm.socialauto.tech`
- **Subdomain Auto-Like (EWS):** `https://ews.socialauto.tech`

## 2. Jaringan & Remote Browser
- Sistem tidak menjalankan Chrome di dalam VPS, melainkan menggunakan **Selenium CDP** untuk mengontrol Chrome di Windows.
- **Tailscale VPN:** Menghubungkan VPS (`100.64.84.81`) ke Windows Host (`100.114.140.47`).
- **Windows Portproxy:** Meneruskan traffic CDP (port 9222-9226) dari Tailscale ke localhost Windows.
- **Start CDP:** Jalankan `start-cdp.ps1` (PowerShell Admin) di Windows.
- **Cek Koneksi:** Jalankan `./check-cdp.sh` di VPS.

## 3. Struktur Container (Docker Compose)
Jalankan perintah dari `/opt/project/spammer`:
- `proxy` (Nginx) : Port 80, 443 (SSL Termination)
- `auto-like-be` : Port 8000 (FastAPI Auto-Comment)
- `autocomment-fe` : Port 5175 (React Auto-Comment)
- `spammer-backend-new` : Port 8081 (FastAPI Auto-Like)
- `spammer-frontend-new` : Port 8082 (React Auto-Like)

*Semua container terhubung ke network `spammer-net`.*

## 4. Fitur Core & Logika Backend
- **AI Fallback:** Gemini (Primary) → Groq/Llama-3 (Fallback) → Template Statis.
- **React Bypass:** Menggunakan `execCommand('insertText')` + `KeyboardEvent` (Bukan `send_keys`) untuk menembus UI React Facebook.
- **Anti-Double Comment:** Menggunakan `Selection API` untuk membersihkan kotak sebelum input.

## 5. Perintah Penting
- **Restart Service:** `docker compose restart <nama-service>`
- **Rebuild Service (Jika ubah Config):** `docker compose up -d --build <nama-service>`
- **Cek Log:** `docker logs -f <nama-container>`
- **Cek SSL:** `sudo certbot certificates`

## 6. Aturan Maintenance
- **Source of Truth:** Selalu edit `docker-compose.yml` dan `nginx-proxy/default.conf` di root folder.
- **Jangan Sentuh:** Folder `backup/`, `data/`, dan file `.env` (kecuali ganti API Key).
- **Update Kode:** Jika ubah *source code* Python/React, cukup restart container. Jika ubah `vite.config.js` atau `Dockerfile`, wajib `docker compose up -d --build`.
