# Spammer Project — Quick Reference

Auto-Like & Auto-Comment bot. Semua containerized.

## Start Cepat

Windows (Admin):
    C:\start-cdp.ps1

Linux:
    /opt/project/spammer/start-all.sh

## URL

| App | URL |
|---|---|
| Auto-Like FE | http://10.10.100.10:8082/ |
| Auto-Comment FE | http://10.10.100.10:5175/ |

## Stop

Linux:
    /opt/project/spammer/stop-all.sh

Windows (Admin):
    C:\stop-cdp.ps1

## Log

    docker logs --tail 0 -f auto-like-be
    docker logs --tail 0 -f spammer-backend-new
    docker logs --tail 0 -f autocomment-fe
    docker logs --tail 0 -f spammer-frontend-new

## Container

| Container | Service | Port |
|---|---|---|
| spammer-backend-new | autolike-be | 8081 |
| spammer-frontend-new | autolike-fe | 8082 |
| auto-like-be | autocomment-be | 8000 |
| autocomment-fe | autocomment-fe | 5175 |

## Detail

Lihat DOKUMENTASI.md
