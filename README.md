# SimKuliah Bot" an

> *"Solusi malas berasal dari pemikiran yang malas dibuat ama orang malas"*
> *— orang malas*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-USK_SimKuliah-red?style=flat-square)

</div>

---

## ⚡ Cara Kerja Singkat (serius)

```
Cron server (tiap 15 mnt)  →  Ada kuliah?  →  Bot login SimKuliah
                                                    ↓
HP dapat notif  ←  ntfy.sh  ←  Klik absen ✓  ←  Nunggu dosen buka absen (refresh tiap 45 dtk)
     (walopun masih teler)
```

Bot ini melakukan 3 hal yang seharusnya kalian lakukan sendiri tapi jelas tidak akan:

1. **Login** ke SimKuliah — otomatis, tanpa perlu kalian sentuh apapun
2. **Klik tombol absen** (+ tombol konfirmasi)
3. **Kirim notifikasi** ke HP — supaya kalian setidaknya tahu bahwa hari ini ada kuliah, emang orang malas

---

## 🇮🇩 Panduan Lengkap

> Panduan ini ditulis sedetail mungkin karena pengalaman menunjukkan bahwa pengguna repo ini tidak bisa diberikan instruksi yang ambigu. Ikuti langkah demi langkah. Jangan skip. Kalian sudah cukup banyak skip hal-hal penting dalam hidup.

### Prasyarat

- Akun **SimKuliah** USK yang aktif — semoga masih ingat passwordnya
- **Server/PC Ubuntu dengan IP Indonesia** yang nyala di jam kuliah — VPS lokal, PC rumah, atau server punya kawan
- HP Android/iOS untuk notifikasi

> **Kenapa harus IP Indonesia?** Sejak Agustus 2026 SimKuliah memblokir akses dari luar negeri. GitHub Actions (server Amerika) sudah tidak bisa dipakai — koneksinya langsung timeout. Bukan bot-nya yang malas, kali ini beneran diblokir.

---

### Langkah 1 — Setup Notifikasi di HP

Gratis. Tidak butuh akun. Satu-satunya hal yang diminta adalah kalian install satu aplikasi — sesuatu yang biasanya kalian lakukan tanpa pikir panjang untuk hal-hal yang jauh kurang berguna.

**a. Install app ntfy:**

- Android → [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
- iOS → [App Store](https://apps.apple.com/app/ntfy/id1625396347)

**b. Pilih `NTFY_TOPIC`** — 2 kata unik bebas, misalnya `budi-absen`. Jangan sama dengan orang lain. Bot akan kirim ke 3 topik:

| Topik | Artinya |
|-------|---------|
| `budi-absen-bisa` | ✅ Absen berhasil — lanjut tidur, kalian aman |
| `budi-absen-info` | 🚨 Absen dibuka dosen / ℹ️ dosen tidak buka absen sampai kuliah selesai |
| `budi-absen-gagal` | 💀 Error — ini saatnya kalian absen sendiri dari HP, untuk sekali ini |

Cara subscribe: buka ntfy → ikon `+` → ketik nama topik → Subscribe. Ulangi 3 kali. Kalian pasti bisa.

---

### Langkah 2 — Pasang di Server

Masuk ke server, lalu:

```bash
git clone https://github.com/Napoleonnnnn/absenv0.1.git
cd absenv0.1
bash install.sh
```

Script ini akan:

1. Cek apakah server bisa mengakses SimKuliah (kalau tidak, berhenti — cari server lain)
2. Install Python, Google Chrome, dan library yang dibutuhkan
3. Tanya NPM, password, dan `NTFY_TOPIC`, lalu simpan ke `.env` (hanya bisa dibaca user kalian)
4. Ambil jadwal semester ke `jadwal_cache.json`
5. Pasang cron: bot dicek tiap 15 menit, jadwal di-refresh tiap 12 jam

Sudah. Itu saja. Tidak ada token, tidak ada Secrets, tidak ada YAML.

> Password kalian tersimpan di server itu. Pakai server orang yang kalian percaya — atau minimal password yang tidak dipakai di tempat lain.

---

#### Alternatif — Pakai n8n *(kalau server kalian sudah punya n8n)*

Tidak perlu cron, tidak perlu `jadwal_cache.json`. n8n yang tahu jam kuliah, bot cukup nunggu.

1. Di server: siapkan venv + `pip install selenium ddddocr`, taruh `absen_n8n.py` dan `.env` (`NPM`, `PASSWORD`) di satu folder
2. Di n8n, buat workflow: **Schedule Trigger** (±10 menit sebelum kuliah, timezone `Asia/Jakarta`) → **SSH** → **HTTP Request**
3. Command node SSH:
   ```bash
   NTFY_TOPIC=budi-absen .venv/bin/python3 absen_n8n.py --maks-menit 180
   ```
4. Script mencetak satu baris JSON `{"status", "judul", "pesan"}`. Node HTTP Request:
   - URL: `https://ntfy.sh/budi-absen-{{ JSON.parse($json.stdout).status }}`
   - Header `Title`: `{{ JSON.parse($json.stdout).judul }}`
   - Body: `{{ JSON.parse($json.stdout).pesan }}`

Opsi tambahan: `--interval 45` (jeda refresh, detik) dan `--debug` (simpan HTML halaman ke `debug/` untuk bahan perbaikan).

---

### Langkah 3 — Cek Hasilnya

```bash
tail -f logs/absen.log
```

- Di luar jam kuliah: tiap 15 menit muncul `Tidak ada kuliah dalam jendela pantau sekarang. Skip.` Itu normal.
- Saat kuliah: muncul `Belum dibuka dosen.` tiap ~45 detik sampai tombol absen muncul.

**Notif yang mungkin masuk:**

- 🚨 `ABSEN DIBUKA` → dosen baru buka absen. Bot sedang klik. Kalau kalian di kelas, ini juga alarm buat absen sendiri
- 🟢 `Absen Berhasil` → beres, kalian resmi bisa rebahan dengan hati tenang
- 🟡 `Absen Tidak Dibuka` → sampai kuliah selesai dosen tidak buka absen
- 🟡 `Halaman Absen Aneh` → halaman absensi berubah tampilan, cek manual
- 🔴 `Absen Butuh Tindakan` / `Absen ERROR` → bot tidak bisa absen. **Absen manual dari HP sekarang**

---

### Cara Kerja Bot (Lebih Detail)

Sejak SimKuliah cuma membuka absen mahasiswa **setelah dosen absen** (dan cuma ~15 menit), bot tidak bisa lagi datang sekali lalu klik. Dia harus nongkrong di halaman absensi sampai tombolnya muncul. Mirip kalian nungguin chat doi, bedanya bot ini dapat balasan.

Setiap 15 menit:

1. Cek `jadwal_cache.json` — ada kuliah yang mulai ≤30 menit lagi atau sedang berjalan?
2. Tidak ada, atau sesi ini sudah diabsen → berhenti dalam sekejap, tanpa buka browser
3. Ada → login SimKuliah (CAPTCHA dicoba ulang sampai 10×) → buka halaman absensi tiap 45 detik
4. Tombol muncul → notif `ABSEN DIBUKA` → klik + konfirmasi → notif `Absen Berhasil`
5. Kuliah selesai + 20 menit, tombol tidak pernah muncul → notif `Absen Tidak Dibuka`

Hanya satu bot yang jalan dalam satu waktu (`flock`). Jadwal di-refresh otomatis, jadi kuliah pengganti dan pindah ruang ikut terbaca.

Bot tidak pernah bolos. Bot tidak pernah lupa. Bot tidak perlu diingatkan dua kali.

---

### Perintah Berguna

```bash
.venv/bin/python absen_runner.py --cek      # ada kuliah sekarang? (tanpa login)
.venv/bin/python refresh_jadwal.py          # refresh jadwal manual
git pull                                    # update bot ke versi terbaru
crontab -l                                  # lihat jadwal cron
```

---

### Troubleshooting

Karena pasti ada yang tidak berjalan mulus, dan kemungkinan besar itu bukan salah botnya:

| Masalah | Kemungkinan penyebab | Solusi |
|---------|---------------------|--------|
| `install.sh` berhenti di langkah 1 | Server tidak punya IP Indonesia / diblokir | Cari server lain. Tidak ada jalan pintas. |
| Login gagal terus | NPM atau password salah di `.env` | Cek lagi. Pelan-pelan. Jangan buru-buru. |
| `Absen Tidak Dibuka` padahal dosen buka | Dosen buka absen di luar jendela pantau (30 menit sebelum s/d 20 menit setelah kuliah) | Absen manual. Lalu laporkan, mungkin jendelanya perlu dilebarkan. |
| Notif tidak masuk | Nama NTFY_TOPIC tidak cocok | Pastikan nama topik di app **sama persis** dengan yang di `.env`. Huruf kapital beda = topik beda. |
| Selalu `Tidak ada kuliah` | Jadwal basi | Cek `logs/refresh.log`, atau jalankan `refresh_jadwal.py` manual. |

---

### Penjelasan File

Untuk yang penasaran isi repo ini ngapain aja — apresiasi rasa ingin tahu kalian yang langka:

| File | Fungsi |
|------|--------|
| `absen_runner.py` | Script utama — cek jadwal, lalu nongkrong di halaman absensi sampai tombolnya muncul |
| `refresh_jadwal.py` | Scrape jadwal semester dari SimKuliah ke `jadwal_cache.json` |
| `simkuliah.py` | Login (+ retry CAPTCHA), browser, dan notif — dipakai kedua script di atas |
| `install.sh` | Pasang semuanya di server dalam sekali jalan (versi cron) |
| `absen_n8n.py` | Versi mandiri untuk n8n — login, tunggu absen dibuka, cetak hasil JSON |
| `jadwal_cache.json` | Dibuat di server, tidak di-commit. Satu-satunya entitas yang tahu jadwal kuliah kalian lebih baik dari kalian |

---

### Tech Stack

| Komponen | Kegunaan |
|----------|----------|
| Python 3.12 | Runtime utama |
| Selenium | Otomatisasi browser — melakukan klik-klik yang seharusnya tanggung jawab kalian |
| Chrome headless | Browser yang bekerja diam-diam di balik layar, tidak seperti kalian |
| python-dotenv | Baca `.env` di server |
| cron + flock | Scheduler di server yang lebih rajin dari pengguna repo ini |
| ntfy.sh | Satu-satunya yang masih mau memberi kabar ke HP kalian |

---

### ⚠️ Disclaimer

Bot ini dibuat untuk keperluan pribadi. Developer tidak bertanggung jawab atas segala konsekuensi akademik — termasuk tapi tidak terbatas pada: absen tetap kosong karena ada bug yang tidak dilaporkan, dosen yang tiba-tiba kenal muka kalian di lorong padahal kalian "selalu hadir", atau IPK yang tetap tidak naik meski kehadiran sudah 100%.

- SimKuliah bisa update tampilannya kapan saja — kalau bot tiba-tiba tidak jalan, itu bukan hantu, cek dulu perubahannya
- **Selalu verifikasi manual** bahwa absensi kalian tercatat. Bot sudah kerja keras, giliran kalian cek sebentar
- Bot tidak 100% sempurna — tapi setidaknya dia selalu mencoba. Beda dengan kalian.

<div align="center">

Made with too much coffee and too little sleep by [NapoleonPro](https://github.com/Napoleonnnnn)

Kalau membantu, kasih ⭐ plis . bantu untuk portfolio, hehe. moga masuk surga, aamiin.

</div>