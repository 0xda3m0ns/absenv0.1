#!/usr/bin/env bash
# Pasang bot absen di server Ubuntu (IP harus Indonesia, SimKuliah blokir IP luar).
# Jalankan dari folder repo:  bash install.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "== 1. Cek akses ke SimKuliah"
if ! curl -s -o /dev/null -m 20 https://simkuliah.usk.ac.id/; then
    echo "Server ini tidak bisa mengakses simkuliah.usk.ac.id. Bot tidak akan jalan di sini."
    exit 1
fi

echo "== 2. Install Python & Google Chrome"
sudo apt-get update -q
sudo apt-get install -y -q python3 python3-venv wget
if ! command -v google-chrome >/dev/null; then
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt-get install -y -q /tmp/chrome.deb
    rm /tmp/chrome.deb
fi

echo "== 3. Install dependencies Python"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q selenium ddddocr python-dotenv

echo "== 4. Isi .env"
if [ ! -f .env ]; then
    read -rp "NPM: " NPM
    read -rsp "Password SimKuliah: " PASSWORD; echo
    read -rp "NTFY_TOPIC (mis. budi-absen): " NTFY_TOPIC
    printf 'NPM=%s\nPASSWORD=%s\nNTFY_TOPIC=%s\n' "$NPM" "$PASSWORD" "$NTFY_TOPIC" > .env
    chmod 600 .env
else
    echo ".env sudah ada, dilewati."
fi

echo "== 5. Ambil jadwal semester"
mkdir -p logs
.venv/bin/python -u refresh_jadwal.py

echo "== 6. Pasang cron"
# Absen: cek tiap 15 menit; script sendiri yang tahu jam kuliah (WIB), jadi zona waktu server tidak berpengaruh.
# flock: satu bot dalam satu waktu; refresh tidak jalan saat bot sedang menunggu absen.
CRON_ABSEN="*/15 * * * * cd $DIR && flock -n /tmp/absenbot.lock .venv/bin/python -u absen_runner.py >> logs/absen.log 2>&1"
CRON_REFRESH="0 */12 * * * cd $DIR && flock -n /tmp/absenbot.lock .venv/bin/python -u refresh_jadwal.py >> logs/refresh.log 2>&1"
( crontab -l 2>/dev/null | grep -v "$DIR" || true; echo "$CRON_ABSEN"; echo "$CRON_REFRESH" ) | crontab -

echo
echo "Selesai. Bot jalan otomatis tiap 15 menit."
echo "Lihat log:  tail -f $DIR/logs/absen.log"
