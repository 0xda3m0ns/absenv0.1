"""
Absen otomatis SimKuliah.

  python absen_runner.py --cek   Cek apakah sekarang ada kuliah (tanpa Chrome).
  python absen_runner.py         Login lalu polling /absensi sampai tombol absen
                                 muncul atau jendela kuliah habis.

Mahasiswa hanya bisa absen setelah dosen membuka absen (jendela ~15 menit),
jadi bot memantau halaman absensi selama jam kuliah, bukan klik sekali.
"""

import json
import os
import sys
import time
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

WIB = ZoneInfo("Asia/Jakarta")
CACHE_FILE = Path("jadwal_cache.json")
PENANDA_DIR = Path(".sudah_absen")

MULAI_PANTAU_SEBELUM = timedelta(minutes=30)
SELESAI_PANTAU_SETELAH = timedelta(minutes=20)
INTERVAL_POLLING = 45  # detik
TEKS_BELUM_BUKA = "Belum masuk waktu absen"


def sekarang() -> datetime:
    # SEKARANG=2026-10-13T16:10 untuk testing
    override = os.getenv("SEKARANG")
    if override:
        return datetime.fromisoformat(override).replace(tzinfo=WIB)
    return datetime.now(WIB)


def load_cache() -> list[dict] | None:
    """Baca jadwal_cache.json dari root repo."""
    if not CACHE_FILE.exists():
        print(" jadwal_cache.json tidak ditemukan.")
        return None
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    jadwal = data.get("jadwal", [])
    for mk in jadwal:
        if mk.get("tanggal"):
            try:
                mk["tanggal"] = date.fromisoformat(mk["tanggal"])
            except Exception:
                mk["tanggal"] = None
    return jadwal


def jendela_kuliah(mk: dict) -> tuple[datetime, datetime] | None:
    """Return (mulai, selesai) kuliah dari tanggal + jam "16.30 - 19.00"."""
    if not mk.get("tanggal") or "-" not in mk.get("jam", ""):
        return None
    try:
        jam_mulai, jam_selesai = [j.strip() for j in mk["jam"].split("-")]
        mulai = datetime.strptime(jam_mulai, "%H.%M").time()
        selesai = datetime.strptime(jam_selesai, "%H.%M").time()
    except ValueError:
        return None
    return (
        datetime.combine(mk["tanggal"], mulai, tzinfo=WIB),
        datetime.combine(mk["tanggal"], selesai, tzinfo=WIB),
    )


def sesi_aktif(jadwal: list[dict], now: datetime) -> list[dict]:
    """Kuliah yang jendela pantaunya (mulai-30m s/d selesai+20m) mencakup sekarang."""
    hasil = []
    for mk in jadwal:
        jendela = jendela_kuliah(mk)
        if not jendela:
            continue
        mulai, selesai = jendela
        if mulai - MULAI_PANTAU_SEBELUM <= now <= selesai + SELESAI_PANTAU_SETELAH:
            hasil.append({**mk, "mulai": mulai, "selesai": selesai})
    return sorted(hasil, key=lambda mk: mk["mulai"])


def cek() -> list[dict]:
    """Tentukan sesi yang perlu dipantau sekarang, tanpa buka browser."""
    now = sekarang()
    print(f" Waktu sekarang: {now.strftime('%A, %d-%m-%Y %H:%M')} WIB")

    jadwal = load_cache()
    if not jadwal:
        return []

    tanggal_terakhir = max((mk["tanggal"] for mk in jadwal if mk.get("tanggal")), default=None)
    if tanggal_terakhir and tanggal_terakhir < now.date():
        print(f" PERINGATAN: jadwal_cache.json basi (jadwal terakhir {tanggal_terakhir}). Jalankan refresh_jadwal.py.")

    aktif = sesi_aktif(jadwal, now)
    if not aktif:
        print(" Tidak ada kuliah dalam jendela pantau sekarang. Skip.")
        return []

    print(f" Kuliah dalam jendela pantau ({len(aktif)} sesi):")
    for mk in aktif:
        print(f"   - {mk['nama_mk']} | {mk['jam']} | {mk['ruang']}")

    kunci = kunci_sesi(aktif)
    if (PENANDA_DIR / kunci).exists():
        print(" Sesi ini sudah diabsen. Skip.")
        return []

    return aktif


def kunci_sesi(aktif: list[dict]) -> str:
    """Nama penanda "sudah absen" untuk sesi ini, mis. absen-20261013-1630."""
    return f"absen-{aktif[0]['mulai'].strftime('%Y%m%d-%H%M')}"


def main():
    from dotenv import load_dotenv
    load_dotenv()

    npm = os.getenv("NPM")
    password = os.getenv("PASSWORD")
    ntfy_topic = os.getenv("NTFY_TOPIC", "")

    if not npm or not password:
        print(" NPM atau PASSWORD tidak ditemukan di environment.")
        sys.exit(1)

    aktif = cek()
    if not aktif:
        sys.exit(0)

    batas = max(mk["selesai"] for mk in aktif) + SELESAI_PANTAU_SETELAH
    nama_mk = ", ".join(sorted({mk["nama_mk"] for mk in aktif}))
    print(f" Memantau absensi sampai {batas.strftime('%H:%M')} WIB")

    from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import ddddocr

    from simkuliah import BASE_URL, buat_driver, di_halaman_login, kirim_notif, login

    def ambil_alert() -> str | None:
        """Tutup alert browser kalau ada (mis. 'Harap berikan izin lokasi...')."""
        try:
            alert = driver.switch_to.alert
            teks = alert.text
            alert.accept()
            return teks
        except NoAlertPresentException:
            return None

    def cari_tombol_absen():
        # #do_absen_manual = tombol "Simpan" tersembunyi milik modal dosen/asisten, bukan tombol absen
        for btn in driver.find_elements(By.CSS_SELECTOR, ".btn.btn-success:not(#do_absen_manual)"):
            if btn.is_displayed():
                return btn
        return None

    driver = buat_driver()
    ocr = ddddocr.DdddOcr(show_ad=False)

    absen_berhasil = 0
    sudah_alarm = False
    sudah_lapor_aneh = False

    try:
        if not login(driver, ocr, npm, password):
            kirim_notif(ntfy_topic, "gagal", "Absen ERROR",
                        f"Login gagal (CAPTCHA) untuk {nama_mk}. Absen manual!", "high")
            sys.exit(1)

        while sekarang() < batas:
            try:
                driver.get(f"{BASE_URL}/index.php/absensi")
                time.sleep(2)

                if di_halaman_login(driver):
                    print(" Sesi habis, login ulang...")
                    if not login(driver, ocr, npm, password):
                        kirim_notif(ntfy_topic, "gagal", "Absen ERROR",
                                    f"Login ulang gagal untuk {nama_mk}. Absen manual!", "high")
                        sys.exit(1)
                    continue

                tombol = cari_tombol_absen()

                if not tombol:
                    if absen_berhasil:
                        break
                    if TEKS_BELUM_BUKA in driver.page_source:
                        print(f" [{sekarang().strftime('%H:%M:%S')}] Belum dibuka dosen.")
                    elif not sudah_lapor_aneh:
                        print(" Halaman absensi tidak dikenali (tidak ada tombol maupun pesan 'belum masuk waktu').")
                        kirim_notif(ntfy_topic, "info", "Halaman Absen Aneh",
                                    "Tidak ada tombol absen maupun pesan 'Belum masuk waktu absen'. Cek manual.")
                        sudah_lapor_aneh = True
                    time.sleep(INTERVAL_POLLING)
                    continue

                if not sudah_alarm:
                    print(" Absen DIBUKA!")
                    kirim_notif(ntfy_topic, "info", "ABSEN DIBUKA",
                                f"{nama_mk}: absen dibuka, waktu ~15 menit.", "high", "rotating_light")
                    sudah_alarm = True

                driver.execute_script("arguments[0].click();", tombol)
                time.sleep(2)

                teks_alert = ambil_alert()
                if teks_alert:
                    print(f" Alert setelah klik: {teks_alert}")
                    kirim_notif(ntfy_topic, "gagal", "Absen Butuh Tindakan",
                                f"Bot tidak bisa absen: {teks_alert} Absen manual dari HP!", "high")
                    sys.exit(1)

                konfirmasi = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))
                )
                driver.execute_script("arguments[0].click();", konfirmasi)
                time.sleep(3)

                teks_alert = ambil_alert()
                if teks_alert:
                    print(f" Alert setelah konfirmasi: {teks_alert}")
                    kirim_notif(ntfy_topic, "gagal", "Absen Butuh Tindakan",
                                f"Bot tidak bisa absen: {teks_alert} Absen manual dari HP!", "high")
                    sys.exit(1)

                absen_berhasil += 1
                print(f" Absen {absen_berhasil} berhasil!")
                # Langsung muat ulang untuk cek tombol absen berikutnya (mis. teori + praktikum)

            except UnexpectedAlertPresentException as e:
                teks = e.alert_text or ambil_alert() or "alert tidak dikenal"
                print(f" Alert: {teks}")
                kirim_notif(ntfy_topic, "gagal", "Absen Butuh Tindakan",
                            f"Bot tidak bisa absen: {teks} Absen manual dari HP!", "high")
                sys.exit(1)

        if absen_berhasil:
            pesan = f"{absen_berhasil} absensi berhasil ({nama_mk})."
            print(f"\n {pesan}")
            kirim_notif(ntfy_topic, "bisa", "Absen Berhasil", pesan)
            PENANDA_DIR.mkdir(exist_ok=True)
            (PENANDA_DIR / kunci_sesi(aktif)).write_text(sekarang().isoformat())
        else:
            print(" Jendela kuliah habis, absen tidak pernah dibuka.")
            kirim_notif(ntfy_topic, "info", "Absen Tidak Dibuka",
                        f"{nama_mk}: sampai {batas.strftime('%H:%M')} dosen tidak membuka absen.")

    except SystemExit:
        raise
    except Exception as e:
        print(f" Error: {type(e).__name__}: {e}")
        kirim_notif(ntfy_topic, "gagal", "Absen ERROR", f"{nama_mk}: {type(e).__name__}: {str(e)[:200]}", "high")
        sys.exit(1)

    finally:
        driver.quit()


if __name__ == "__main__":
    if "--cek" in sys.argv:
        cek()
    else:
        main()
