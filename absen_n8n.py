"""
Absen SimKuliah untuk node "Execute Command" n8n.

    python3 absen_n8n.py [--maks-menit 180] [--interval 45] [--debug]

Dipicu n8n sekitar jam mulai kuliah. Mahasiswa baru bisa absen setelah dosen
membuka absen (~15 menit), jadi script login lalu memuat ulang /absensi sampai
tombol absen muncul atau --maks-menit habis.

Kredensial dari environment (atau file .env di folder yang sama):
    NPM, PASSWORD, NTFY_TOPIC (opsional, untuk alarm "ABSEN DIBUKA" saat itu juga)

Output: log ke stderr, SATU baris JSON ke stdout untuk node berikutnya:
    {"status": "bisa"|"info"|"gagal", "judul": "...", "pesan": "..."}
Exit code selalu 0 supaya alur n8n tetap lanjut ke node notifikasi.

--debug: simpan HTML halaman absensi ke folder debug/ saat tombol muncul,
sesudah konfirmasi, dan saat error/halaman tidak dikenali.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import ddddocr

WIB = ZoneInfo("Asia/Jakarta")
BASE_URL = "https://simkuliah.usk.ac.id"
TEKS_BELUM_BUKA = "Belum masuk waktu absen"


def log(msg: str):
    print(f"[{datetime.now(WIB).strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def selesai(status: str, judul: str, pesan: str):
    """Cetak hasil untuk n8n lalu keluar."""
    print(json.dumps({"status": status, "judul": judul, "pesan": pesan}, ensure_ascii=False))
    sys.exit(0)


def baca_env_file():
    env = Path(__file__).with_name(".env")
    if not env.exists():
        return
    for baris in env.read_text().splitlines():
        if "=" in baris and not baris.lstrip().startswith("#"):
            k, v = baris.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def kirim_alarm(topic: str, judul: str, pesan: str):
    """Notif langsung (tidak menunggu script selesai), untuk alarm absen dibuka."""
    if not topic:
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}-info",
        data=pesan.encode("utf-8"),
        headers={"Title": judul, "Priority": "high", "Tags": "rotating_light"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log(f"Gagal kirim alarm: {e}")


def buat_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    if os.getenv("CHROME_BIN"):
        options.binary_location = os.getenv("CHROME_BIN")
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def di_halaman_login(driver) -> bool:
    return "login" in driver.current_url.lower() or bool(
        driver.find_elements(By.NAME, "captcha_answer")
    )


def login(driver, ocr, npm: str, password: str, max_percobaan: int = 10) -> bool:
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)

    for percobaan in range(1, max_percobaan + 1):
        log(f"Login percobaan ke-{percobaan}...")

        field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        field.clear()
        field.send_keys(npm)

        field = driver.find_element(By.NAME, "password")
        field.clear()
        field.send_keys(password)

        captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha-img")))
        captcha = ocr.classification(captcha_img.screenshot_as_png).strip().replace(" ", "")

        field = driver.find_element(By.NAME, "captcha_answer")
        field.clear()
        field.send_keys(captcha)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
        time.sleep(3)

        if not di_halaman_login(driver):
            log("Login berhasil.")
            return True

        driver.get(BASE_URL)
        time.sleep(1)

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maks-menit", type=int, default=180,
                        help="Berapa lama menunggu dosen buka absen (default 180)")
    parser.add_argument("--interval", type=int, default=45,
                        help="Jeda antar refresh halaman absensi, detik (default 45)")
    parser.add_argument("--debug", action="store_true",
                        help="Simpan HTML halaman ke folder debug/ untuk bahan perbaikan")
    args = parser.parse_args()

    baca_env_file()
    npm = os.getenv("NPM")
    password = os.getenv("PASSWORD")
    topic = os.getenv("NTFY_TOPIC", "")
    if not npm or not password:
        selesai("gagal", "Absen ERROR", "NPM atau PASSWORD belum diset.")

    batas = datetime.now(WIB) + timedelta(minutes=args.maks_menit)
    log(f"Memantau absensi sampai {batas.strftime('%H:%M')} WIB")

    driver = buat_driver()
    ocr = ddddocr.DdddOcr(show_ad=False)

    def ambil_alert() -> str | None:
        """Tutup alert browser kalau ada (mis. 'Harap berikan izin lokasi...')."""
        try:
            alert = driver.switch_to.alert
            teks = alert.text
            alert.accept()
            return teks
        except NoAlertPresentException:
            return None

    def simpan_debug(nama: str):
        if not args.debug:
            return
        try:
            folder = Path(__file__).with_name("debug")
            folder.mkdir(exist_ok=True)
            file = folder / f"{datetime.now(WIB).strftime('%Y%m%d-%H%M%S')}-{nama}.html"
            file.write_text(f"<!-- {driver.current_url} -->\n{driver.page_source}", encoding="utf-8")
            log(f"Debug disimpan: {file.name}")
        except Exception as e:
            log(f"Gagal simpan debug: {e}")

    def cari_tombol_absen():
        # #do_absen_manual = tombol "Simpan" tersembunyi milik modal dosen/asisten, bukan tombol absen
        for btn in driver.find_elements(By.CSS_SELECTOR, ".btn.btn-success:not(#do_absen_manual)"):
            if btn.is_displayed():
                return btn
        return None

    absen_berhasil = 0
    sudah_alarm = False
    sudah_debug_aneh = False

    try:
        if not login(driver, ocr, npm, password):
            selesai("gagal", "Absen ERROR", "Login gagal 10x (CAPTCHA). Absen manual!")

        while datetime.now(WIB) < batas:
            try:
                driver.get(f"{BASE_URL}/index.php/absensi")
                time.sleep(2)

                if di_halaman_login(driver):
                    log("Sesi habis, login ulang...")
                    if not login(driver, ocr, npm, password):
                        selesai("gagal", "Absen ERROR", "Login ulang gagal. Absen manual!")
                    continue

                tombol = cari_tombol_absen()

                if not tombol:
                    if absen_berhasil:
                        break
                    if TEKS_BELUM_BUKA in driver.page_source:
                        log("Belum dibuka dosen.")
                    else:
                        log("Halaman absensi tidak dikenali (tidak ada tombol / pesan 'belum masuk waktu').")
                        if not sudah_debug_aneh:
                            simpan_debug("halaman-aneh")
                            sudah_debug_aneh = True
                    time.sleep(args.interval)
                    continue

                simpan_debug("tombol-muncul")
                if not sudah_alarm:
                    log("Absen DIBUKA!")
                    kirim_alarm(topic, "ABSEN DIBUKA", "Absen dibuka dosen, waktu ~15 menit.")
                    sudah_alarm = True

                driver.execute_script("arguments[0].click();", tombol)
                time.sleep(2)
                teks = ambil_alert()
                simpan_debug("sesudah-klik")
                if teks:
                    selesai("gagal", "Absen Butuh Tindakan", f"Bot tidak bisa absen: {teks} Absen manual dari HP!")

                konfirmasi = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))
                )
                driver.execute_script("arguments[0].click();", konfirmasi)
                time.sleep(3)
                teks = ambil_alert()
                simpan_debug("sesudah-konfirmasi")
                if teks:
                    selesai("gagal", "Absen Butuh Tindakan", f"Bot tidak bisa absen: {teks} Absen manual dari HP!")

                absen_berhasil += 1
                log(f"Absen {absen_berhasil} berhasil.")
                # Langsung muat ulang untuk cek tombol absen berikutnya (mis. teori + praktikum)

            except UnexpectedAlertPresentException as e:
                teks = e.alert_text or ambil_alert() or "alert tidak dikenal"
                selesai("gagal", "Absen Butuh Tindakan", f"Bot tidak bisa absen: {teks} Absen manual dari HP!")

        if absen_berhasil:
            selesai("bisa", "Absen Berhasil", f"{absen_berhasil} absensi berhasil.")
        selesai("info", "Absen Tidak Dibuka",
                f"Sampai {batas.strftime('%H:%M')} dosen tidak membuka absen.")

    except SystemExit:
        raise
    except Exception as e:
        try:
            ambil_alert()
        except Exception:
            pass
        simpan_debug("error")
        selesai("gagal", "Absen ERROR", f"{type(e).__name__}: {str(e)[:200]}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
