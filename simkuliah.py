"""Fungsi bersama untuk absen_runner.py dan refresh_jadwal.py."""

import time
import urllib.request

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://simkuliah.usk.ac.id"


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
    # Jangan tunggu semua resource (gambar/CDN) selesai dimuat; cukup DOM siap
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def di_halaman_login(driver: webdriver.Chrome) -> bool:
    return "login" in driver.current_url.lower() or bool(
        driver.find_elements(By.NAME, "captcha_answer")
    )


def login(driver: webdriver.Chrome, ocr, npm: str, password: str, max_percobaan: int = 10) -> bool:
    """Login ke SimKuliah, ulangi kalau CAPTCHA salah. Return True kalau berhasil."""
    print("Membuka SimKuliah...")
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)

    for percobaan in range(1, max_percobaan + 1):
        print(f"Percobaan login ke-{percobaan}...")

        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_field.clear()
        username_field.send_keys(npm)

        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)

        captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha-img")))
        captcha_text = ocr.classification(captcha_img.screenshot_as_png).strip().replace(" ", "")
        print(f"  CAPTCHA terbaca: {captcha_text}")

        captcha_field = driver.find_element(By.NAME, "captcha_answer")
        captcha_field.clear()
        captcha_field.send_keys(captcha_text)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
        time.sleep(3)

        if not di_halaman_login(driver):
            print("Login berhasil!")
            return True

        print("  Login gagal, CAPTCHA salah. Mencoba lagi...")
        driver.get(BASE_URL)
        time.sleep(1)

    print(f"Login gagal setelah {max_percobaan} percobaan.")
    return False


def kirim_notif(topic: str, jenis: str, judul: str, pesan: str, prioritas: str = "default", tags: str = ""):
    """Kirim notif ke ntfy.sh/{topic}-{jenis}. jenis: bisa | info | gagal."""
    if not topic:
        return
    headers = {"Title": judul, "Priority": prioritas}
    if tags:
        headers["Tags"] = tags
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}-{jenis}",
        data=pesan.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Gagal kirim notif: {e}")
