# 🚀 SocialAuto Infrastructure

Sistem otomasi (*Auto-Like* & *Auto-Comment*) untuk platform Facebook. Sistem ini menggunakan arsitektur **Distributed Automation**, di mana *Web App* berjalan di VPS Linux, namun eksekusi *browser* (Chrome) dikendalikan secara *remote* dari sebuah Windows Host via Tailscale.

## 🏗️ Arsitektur Sistem

1. **VPS (Linux - Ubuntu 22.04):** Menjalankan Docker container (FastAPI + React + Nginx).
2. **Windows Host (Remote):** Menjalankan 5 *instance* Google Chrome (via CDP Port 9222-9226) yang sudah login ke akun Facebook.
3. **Tailscale VPN:** Menghubungkan VPS dan Windows Host secara privat.
4. **Nginx Proxy:** Mengatur *routing* domain dan SSL (HTTPS).
   - Auto-Comment (ACM): `https://acm.socialauto.tech`
   - Auto-Like (EWS): `https://ews.socialauto.tech`

## 📂 Struktur Direktori

```text
/opt/project/spammer/
├── docker-compose.yml       # Orkestrasi 5 container (Proxy, BE, FE)
├── .env                     # API Key (JANGAN DI-COMMIT)
├── nginx-proxy/             # Config Nginx untuk reverse proxy & SSL
├── autocomment/             # Source code Auto-Comment (ACM)
│   ├── backend/             # FastAPI + Selenium
│   └── frontend/            # React (Vite)
├── autolike/                # Source code Auto-Like (EWS)
│   ├── backend/             # FastAPI + Playwright
│   └── frontend/            # React (Vite)
└── backup/                  # Arsip file lama & .bak

---

## 🎯 CARA PENGGUNAAN (PENTING UNTUK USER/END-USER)

Web Dashboard ini **TIDAK BISA DIGUNAKAN SEMBARANGAN**. Sistem ini menggunakan arsitektur *Remote Control* (VPS mengendalikan Browser di Windows). 

**Syarat Mutlak Sebelum Menggunakan:**
1. **Windows Host (Worker Node) harus menyala.**
2. **Tailscale di Windows Host harus terhubung (Connected).**
3. **5 Instance Chrome CDP harus berjalan.**
   *(Jalankan script `start-cdp.ps1` di Windows Host via PowerShell Admin).*

**Langkah-Langkah Menggunakan Dashboard (Dari Laptop/HP Mana pun):**
1. Buka URL Dashboard (tidak perlu install Tailscale):
   - Auto-Comment: `https://acm.socialauto.tech`
   - Auto-Like: `https://ews.socialauto.tech`
2. Copy URL postingan Facebook yang ingin di-*comment* / di-*like*.
3. Paste URL tersebut ke kolom "Target Post" di Dashboard.
4. Klik tombol **Jalankan**.
5. Sistem akan mengirim perintah ke Windows Host. Anda bisa melihat prosesnya secara *real-time* di Virtual Terminal Dashboard.
6. **JANGAN TUTUP / MATIKAN Windows Host** selama proses berjalan.

**Troubleshooting Cepat:**
- **Dashboard Offline (FastAPI Offline):** Berarti container Docker di VPS mati. Jalankan `docker compose up -d` di VPS.
- **Bot Gagal Jalan / CDP Error:** Berarti Windows Host mati, Tailscale putus, atau Chrome CDP belum dibuka.
- **Komentar Gagal Masuk:** Bisa jadi akun FB kena *checkpoint* atau AI sedang *down* (sistem akan otomatis *fallback* ke AI cadangan).
