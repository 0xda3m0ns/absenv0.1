# SimKuliah Bot" an

> *"Solusi malas berasal dari pemikiran yang malas dibuat ama orang malas"*
> *— orang malas*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium)
![n8n](https://img.shields.io/badge/n8n-workflow-EA4B71?style=flat-square&logo=n8n)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-USK_SimKuliah-red?style=flat-square)

</div>

---

## ⚡ Cara Kerja Singkat (serius)

```
n8n Schedule Trigger  →  SSH jalanin absen_n8n.py  →  Bot login SimKuliah
                                                              ↓
HP dapat notif  ←  ntfy.sh  ←  HTTP Request  ←  Klik absen ✓  ←  Nunggu dosen buka absen
     (walopun masih teler)
```

Bot ini melakukan 3 hal yang seharusnya kalian lakukan sendiri tapi jelas tidak akan:

1. **Login** ke SimKuliah — otomatis, tanpa perlu kalian sentuh apapun
2. **Klik tombol absen** (+ tombol konfirmasi)
3. **Kirim notifikasi** ke HP — supaya kalian setidaknya tahu bahwa hari ini ada kuliah, emang orang malas

Isi repo ini cuma **satu script**: `absen_n8n.py`. n8n yang tahu jam kuliah, bot cuma nunggu.

---

## 🇮🇩 Panduan Lengkap

> Panduan ini ditulis sedetail mungkin karena pengalaman menunjukkan bahwa pengguna repo ini tidak bisa diberikan instruksi yang ambigu. Ikuti langkah demi langkah. Jangan skip. Kalian sudah cukup banyak skip hal-hal penting dalam hidup.

### Prasyarat

- Akun **SimKuliah** USK yang aktif — semoga masih ingat passwordnya
- **Server/PC Ubuntu dengan IP Indonesia** yang nyala di jam kuliah — VPS lokal, PC rumah, atau server punya kawan
- **n8n** yang sudah jalan di server tersebut
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
python3 -m venv .venv
.venv/bin/pip install selenium ddddocr
```

Pastikan **Google Chrome** dan **chromedriver** terpasang (`apt install google-chrome-stable`, atau biarkan Selenium Manager yang urus).

Lalu buat `.env` di folder yang sama:

```bash
NPM=123456789
PASSWORD=passwordkalian
NTFY_TOPIC=budi-absen
```

> Password kalian tersimpan di server itu. Pakai server orang yang kalian percaya — atau minimal password yang tidak dipakai di tempat lain.

---

### Langkah 3 — Workflow n8n

Tiga node, tidak ada YAML, tidak ada token.

**1. Schedule Trigger**

Atur ±10 menit sebelum kuliah, timezone `Asia/Jakarta`. Mau lebih dari satu jadwal? Tambahkan trigger atau pakai Cron node.

**2. SSH** (atau Execute Command kalau n8n satu server dengan bot)

```bash
cd /path/ke/absenv0.1 && .venv/bin/python3 absen_n8n.py --maks-menit 180
```

**3. HTTP Request** (kirim hasil ke ntfy)

Script mencetak satu baris JSON `{"status", "judul", "pesan"}`:

- URL: `https://ntfy.sh/budi-absen-{{ JSON.parse($json.stdout).status }}`
- Method: `POST`
- Header `Title`: `{{ JSON.parse($json.stdout).judul }}`
- Body: `{{ JSON.parse($json.stdout).pesan }}`

Status `bisa` / `info` / `gagal` otomatis jadi topik `-bisa` / `-info` / `-gagal`. Tidak perlu if-else.

Opsi tambahan: `--interval 45` (jeda refresh, detik) dan `--debug` (simpan HTML halaman ke `debug/` untuk bahan perbaikan).

---

### Langkah 4 — Cek Hasilnya

Lihat log node SSH di n8n:

- Di luar jam kuliah / belum dibuka: `Belum dibuka dosen.` tiap ~45 detik sampai tombol absen muncul
- Sesi habis: `Sesi habis, login ulang...` — normal, bot login sendiri

**Notif yang mungkin masuk:**

- 🚨 `ABSEN DIBUKA` → dosen baru buka absen. Bot sedang klik. Kalau kalian di kelas, ini juga alarm buat absen sendiri
- 🟢 `Absen Berhasil` → beres, kalian resmi bisa rebahan dengan hati tenang
- 🟡 `Absen Tidak Dibuka` → sampai batas waktu dosen tidak buka absen
- 🔴 `Absen Butuh Tindakan` / `Absen ERROR` → bot tidak bisa absen. **Absen manual dari HP sekarang**

---

### Cara Kerja Bot (Lebih Detail)

Sejak SimKuliah cuma membuka absen mahasiswa **setelah dosen absen** (dan cuma ~15 menit), bot tidak bisa datang sekali lalu klik. Dia harus nongkrong di halaman absensi sampai tombolnya muncul. Mirip kalian nungguin chat doi, bedanya bot ini dapat balasan.

1. Login SimKuliah (CAPTCHA dicoba ulang sampai 10×)
2. Buka halaman absensi tiap 45 detik sampai tombolnya muncul atau `--maks-menit` habis
3. Tombol muncul → notif `ABSEN DIBUKA` → klik + konfirmasi → notif `Absen Berhasil`
4. Satu sesi = satu absen. Setelah sukses bot langsung berhenti, tidak klik ulang

Bot tidak pernah bolos. Bot tidak pernah lupa. Bot tidak perlu diingatkan dua kali.

---

### Troubleshooting

Karena pasti ada yang tidak berjalan mulus, dan kemungkinan besar itu bukan salah botnya:

| Masalah | Kemungkinan penyebab | Solusi |
|---------|---------------------|--------|
| `Server ini tidak bisa mengakses simkuliah` | Server tidak punya IP Indonesia / diblokir | Cari server lain. Tidak ada jalan pintas. |
| Login gagal terus | NPM atau password salah di `.env` | Cek lagi. Pelan-pelan. Jangan buru-buru. |
| `Absen Tidak Dibuka` padahal dosen buka | Dosen buka absen setelah `--maks-menit` habis | Naikkan `--maks-menit`, atau absen manual. |
| Notif tidak masuk | Nama NTFY_TOPIC tidak cocok | Pastikan nama topik di app **sama persis** dengan yang di `.env` dan URL HTTP Request. Huruf kapital beda = topik beda. |
| `Halaman absensi tidak dikenali` | SimKuliah ganti tampilan | Jalankan dengan `--debug`, cek HTML di `debug/`. |

---

### Penjelasan File

Untuk yang penasaran isi repo ini ngapain aja — apresiasi rasa ingin tahu kalian yang langka:

| File | Fungsi |
|------|--------|
| `absen_n8n.py` | Satu-satunya script — login, tunggu absen dibuka, klik, cetak hasil JSON |
| `.env` | NPM, password, dan `NTFY_TOPIC`. Jangan di-commit (sudah masuk `.gitignore`) |

---

### Tech Stack

| Komponen | Kegunaan |
|----------|----------|
| Python 3.12 | Runtime utama |
| Selenium | Otomatisasi browser — melakukan klik-klik yang seharusnya tanggung jawab kalian |
| Chrome headless | Browser yang bekerja diam-diam di balik layar, tidak seperti kalian |
| ddddocr | Baca CAPTCHA, karena kalian juga sering salah baca |
| n8n | Scheduler yang lebih rajin dari pengguna repo ini |
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
