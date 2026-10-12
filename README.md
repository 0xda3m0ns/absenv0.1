# SimKuliah Bot" an

> *"Solusi malas berasal dari pemikiran yang malas dibuat ama orang malas"*
> *— orang malas*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=flat-square&logo=github-actions)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-USK_SimKuliah-red?style=flat-square)

</div>

---

## ⚡ Cara Kerja Singkat (serius)

```
cron-job.org (tiap 15 mnt)  →  GitHub Actions  →  Ada kuliah? → Bot login SimKuliah
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

Sebelum mulai, pastikan kalian punya:

- Akun **GitHub** (gratis) → [daftar di sini](https://github.com/signup) — anak IT ga punya github?, jadi simpan kode proyek selama ini di lokal?, watafak
- Akun **SimKuliah** USK yang aktif — semoga masih ingat passwordnya
- HP Android/iOS untuk notifikasi

---

### Langkah 1 — Fork Repositori Ini

> Fork = menyalin repo ini ke akun GitHub kalian sendiri. Mirip plagiat, tapi legal dan justru dianjurkan.

1. Klik tombol **Fork** di pojok kanan atas halaman ini
2. Klik **Create fork**
3. Selesai — tiga klik, dan ini mungkin pencapaian teknis terbesar hari ini

---

### Langkah 2 — Isi Data Rahasia (Secrets)

Bot butuh NPM dan password. Jangan ditulis langsung di kode — selain tidak aman, itu juga tingkat kemalasan yang bahkan membuat pembuat repo ini geleng-geleng kepala.

Gunakan **GitHub Secrets**. Ini fitur khusus untuk menyimpan data sensitif, dan ya, kalian perlu belajar cara pakainya. Tidak ada yang bisa menggantikan langkah ini.

**Cara masuk ke halaman Secrets:**
```
Repo → Settings → Secrets and variables → Actions → New repository secret
```

Tambahkan **3 secret** berikut. Satu per satu. Jangan sekaligus, karena memang tidak bisa.

| Nama Secret | Isi dengan | Contoh |
|-------------|-----------|--------|
| `NPM` | NPM kalian | `2108107010001` |
| `PASSWORD` | Password SimKuliah  | `passwordkalian123` |
| `NTFY_TOPIC` | 2 kata identifier unik pilihan kalian | `budi-absen` |

> **Catatan soal `NTFY_TOPIC`:** Ini adalah identifier unik kalian — bebas diisi apa saja, asal tidak sama dengan orang lain. Bot akan otomatis menambahkan `-bisa`, `-info`, dan `-gagal` di belakangnya. Jadi kalau kalian isi `budi-absen`, notif akan dikirim ke `budi-absen-bisa`, `budi-absen-info`, dan `budi-absen-gagal`. Jangan dikosongkan — kalau kosong, kalian tidak akan dapat notifikasi sama sekali, dan bot bisa gagal diam-diam tanpa kalian tahu.

---

### Langkah 3 — Setup Notifikasi di HP

Gratis. Tidak butuh akun. Satu-satunya hal yang diminta adalah kalian install satu aplikasi — sesuatu yang biasanya kalian lakukan tanpa pikir panjang untuk hal-hal yang jauh kurang berguna.

**a. Install app ntfy:**

- Android → [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
- iOS → [App Store](https://apps.apple.com/app/ntfy/id1625396347)

**b. Subscribe ke 3 topik berikut** (ganti `budi-absen` dengan `NTFY_TOPIC` milik kalian):

| Topik | Artinya |
|-------|---------|
| `budi-absen-bisa` | ✅ Absen berhasil — lanjut tidur, kalian aman |
| `budi-absen-info` | ℹ️ Bot jalan tapi tidak ada tombol absen — dosen belum buka, bukan salah kalian |
| `budi-absen-gagal` | 💀 Error — ini saatnya kalian melakukan sesuatu sendiri, untuk sekali ini |

Cara subscribe: buka ntfy → ikon `+` → ketik nama topik → Subscribe. Empat langkah. Kalian pasti bisa.

---

### Langkah 4 — Update Jadwal Kuliah

Bot tidak bisa baca pikiran. Dia butuh file `jadwal_cache.json` untuk tahu kapan harus jalan. Tanpa file ini, bot tidak tahu kalian kuliah — dan jujur, kalian sering lupa juga.

**Ada 2 cara:**

#### Cara A — Generate Otomatis *(untuk yang malas tapi masih punya batas)*

```
Tab Actions → Refresh Jadwal Cache → Run workflow → Run workflow
```

Bot akan login, ambil seluruh jadwal semester, simpan otomatis. Setelah itu workflow-nya jalan sendiri tiap Senin, jadi cukup sekali di awal semester, lalu lupakan. Persis seperti niat olahraga.

#### Cara B — Edit Manual *(untuk kalian yang entah kenapa memilih jalan susah)*

Buka `jadwal_cache.json`, tambahkan entry sesuai format ini:

```json
{
  "pertemuan": 1,
  "kode_mk": "STIK3034",
  "nama_mk": "PATTERN RECOGNITION AND MACHINE LEARNING",
  "dosen": "Prof M. Ammar Fasya, M.T.",
  "tanggal_str": "12-02-2026",
  "tanggal": "2026-02-12",
  "hari": "Kamis",
  "ruang": "A25-203",
  "jam": "08.00 - 09.40"
}
```

> **Penting:** `"tanggal"` harus format `YYYY-MM-DD`. Salah format, bot tidak jalan, absen kosong, itu salah kalian sepenuhnya. `"tanggal_str"` boleh diisi sembarang — label doang, tidak ada yang membaca.

---

### Langkah 5 — Pasang Alarm di cron-job.org

Sejak SimKuliah cuma membuka absen mahasiswa **setelah dosen absen** (dan cuma ~15 menit), bot tidak bisa lagi datang sekali lalu klik. Bot harus **nongkrong di halaman absensi selama jam kuliah** sampai tombolnya muncul. Mirip kalian nungguin chat doi, bedanya bot ini dapat balasan.

Masalahnya, cron bawaan GitHub bisa telat **sampai sejam**. Absen 15 menit + delay sejam = alpa. Jadi yang membangunkan bot adalah **cron-job.org** (gratis, tepat waktu), yang memanggil API GitHub tiap 15 menit. Bot sendiri yang mengecek `jadwal_cache.json`: kalau tidak ada kuliah, dia langsung tidur lagi dalam ~20 detik.

Setup ini **sekali seumur hidup** — tidak perlu diubah tiap semester. Cron bawaan GitHub tetap ada sebagai cadangan.

**5a. Bikin token GitHub**

```
GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token
```

| Field | Isi |
|-------|-----|
| Repository access | *Only select repositories* → pilih repo absen kalian |
| Permissions → Repository → **Actions** | **Read and write** (yang lain biarkan) |
| Expiration | Maksimal 1 tahun. Catat tanggalnya. Iya, catat. |

Token ini cuma bisa menjalankan workflow di repo itu. Password tetap aman di Secrets.

**5b. Bikin cronjob di [cron-job.org](https://cron-job.org)**

Daftar → **Create cronjob**, isi:

| Field | Isi |
|-------|-----|
| URL | `https://api.github.com/repos/<username>/<repo>/actions/workflows/absen.yml/dispatches` |
| Execution schedule | Custom: tiap **15 menit**, jam **7–19**, hari **Senin–Sabtu** |
| Timezone (Settings akun) | `Asia/Jakarta` |
| Advanced → Request method | `POST` |
| Advanced → Headers | `Authorization: Bearer <token>`<br>`Accept: application/vnd.github+json`<br>`X-GitHub-Api-Version: 2022-11-28` |
| Advanced → Request body | `{"ref":"main"}` |
| Notifications | Centang notif kalau gagal — biar tahu saat token kedaluwarsa |

Klik **Test run**. Kalau responsnya `204`, berhasil — cek tab Actions, harusnya ada run baru. Kalau `401`/`403`, tokennya salah atau izinnya kurang. Kalau `404`, URL-nya typo.

---

### Langkah 6 — Test Pertama Kali

Sebelum menyerahkan tanggung jawab akademik kepada sekumpulan cron job, tes dulu. Ini satu-satunya langkah yang benar-benar membutuhkan perhatian — tolong hadir secara penuh, setidaknya untuk ini.

1. Pastikan jadwal sudah di-refresh (Langkah 4)
2. Buka tab **Actions** → **Absensi Otomatis** → **Run workflow**
3. Di luar jam kuliah, run harus selesai cepat dengan log `Tidak ada kuliah dalam jendela pantau sekarang. Skip.` Itu normal.
4. Tes sebenarnya: saat kuliah berikutnya. Log akan menampilkan `Belum dibuka dosen.` tiap ~45 detik sampai tombol muncul.

**Notif yang mungkin masuk:**

- 🚨 `ABSEN DIBUKA` → dosen baru buka absen. Bot sedang klik. Kalau kalian di kelas, ini juga alarm buat absen sendiri
- 🟢 `Absen Berhasil` → beres, kalian resmi bisa rebahan dengan hati tenang
- 🟡 `Absen Tidak Dibuka` → sampai kuliah selesai dosen tidak buka absen
- 🟡 `Halaman Absen Aneh` → halaman absensi berubah tampilan, cek manual
- 🔴 `Absen Butuh Tindakan` / `Absen ERROR` → bot tidak bisa absen. **Absen manual dari HP sekarang**

---

### Cara Kerja Bot (Lebih Detail)

Setiap kali dibangunkan (tiap 15 menit):

1. Cek `jadwal_cache.json` — ada kuliah yang mulai ≤30 menit lagi atau sedang berjalan?
2. Tidak ada → berhenti dalam ~20 detik, tanpa buka browser
3. Sudah absen untuk sesi ini (penanda di cache Actions) → berhenti
4. Ada → login SimKuliah (CAPTCHA dicoba ulang sampai 10×) → buka halaman absensi tiap 45 detik
5. Tombol muncul → notif `ABSEN DIBUKA` → klik + konfirmasi → notif `Absen Berhasil`
6. Kuliah selesai + 20 menit, tombol tidak pernah muncul → notif `Absen Tidak Dibuka`

Hanya satu bot yang jalan dalam satu waktu; trigger yang datang saat bot sedang menunggu akan antri, lalu langsung berhenti karena sesi itu sudah diabsen.

Bot tidak pernah bolos. Bot tidak pernah lupa. Bot tidak perlu diingatkan dua kali.

---

### Refresh Jadwal

```
Tab Actions → Refresh Jadwal Cache → Run workflow
```

Workflow ini juga jalan otomatis **tiap Senin pagi**, supaya kuliah pengganti dan perubahan ruang/jam ikut terbaca. Commit hanya dibuat kalau jadwal benar-benar berubah. Satu hal dalam hidup kalian yang benar-benar berjalan sendiri — manfaatkan sebaik mungkin.

Kalau cache basi (semua jadwal sudah lewat), log absen akan menampilkan warning kuning.

---

### Troubleshooting

Karena pasti ada yang tidak berjalan mulus, dan kemungkinan besar itu bukan salah botnya:

| Masalah | Kemungkinan penyebab | Solusi |
|---------|---------------------|--------|
| Login gagal terus | NPM atau password salah di Secrets | Cek lagi. Pelan-pelan. Jangan buru-buru. |
| `Absen Tidak Dibuka` padahal dosen buka | Dosen buka absen di luar jendela pantau (30 menit sebelum s/d 20 menit setelah kuliah) | Absen manual. Lalu laporkan, mungkin jendelanya perlu dilebarkan. |
| Bot tidak jalan sama sekali | Token cron-job.org kedaluwarsa / salah | Lihat riwayat eksekusi di cron-job.org. `401` = bikin token baru. |
| Notif tidak masuk | Nama NTFY_TOPIC tidak cocok | Pastikan nama topik di app **sama persis** dengan yang di Secrets. Huruf kapital beda = topik beda. |
| Selalu `Tidak ada kuliah` | `jadwal_cache.json` basi | Jalankan workflow Refresh Jadwal Cache. Tidak ada shortcut. |
| Refresh gagal di step commit | Izin workflow | Settings → Actions → General → Workflow permissions → **Read and write** |

---

### Penjelasan File

Untuk yang penasaran isi repo ini ngapain aja — apresiasi rasa ingin tahu kalian yang langka:

| File | Fungsi |
|------|--------|
| `absen_runner.py` | Script utama — cek jadwal, lalu nongkrong di halaman absensi sampai tombolnya muncul |
| `refresh_jadwal.py` | Scrape jadwal semester dari SimKuliah |
| `simkuliah.py` | Login (+ retry CAPTCHA), browser, dan notif — dipakai kedua script di atas |
| `jadwal_cache.json` | Database jadwal. Satu-satunya entitas di sini yang tahu jadwal kuliah kalian lebih baik dari kalian |
| `.github/workflows/absen.yml` | Workflow absen — dibangunkan cron-job.org |
| `.github/workflows/refresh.yml` | Workflow refresh jadwal tiap Senin |

---

### Jalankan Lokal *(khusus yang mau repot)*

Kalau mau coba di komputer sendiri, silakan. Ini justru membuktikan bahwa kalian tidak sesantai yang kalian kira.

```bash
# Clone repo
git clone https://github.com/NapoleonPro/absenv0.1.git
cd absenv0.1

# Install dependencies
pip install selenium ddddocr python-dotenv

# Buat file .env
echo "NPM=npm_kalian" > .env
echo "PASSWORD=password_kalian" >> .env
echo "NTFY_TOPIC=topic_kalian" >> .env

# Refresh jadwal dulu
python refresh_jadwal.py

# Baru jalankan absen
python absen_runner.py
```

> Butuh Google Chrome terinstall. Kalau belum ada, install dulu — ya, kalian harus melakukan satu hal lagi.

---

### Tech Stack

| Komponen | Kegunaan |
|----------|----------|
| Python 3.12 | Runtime utama |
| Selenium | Otomatisasi browser — melakukan klik-klik yang seharusnya tanggung jawab kalian |
| Chrome headless | Browser yang bekerja diam-diam di balik layar, tidak seperti kalian |
| python-dotenv | Baca `.env` saat development lokal |
| GitHub Actions | Scheduler gratis yang lebih rajin dari pengguna repo ini |
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