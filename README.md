# Automated Alumni Profiler

Sistem pelacakan jejak alumni otomatis menggunakan Flask, SQLite, dan Serper.dev API. Sistem mencari profil alumni di **7 platform sosial media** secara paralel dengan algoritma fuzzy scoring untuk menghitung confidence score dan disambiguasi identitas.

## Informasi Rilis
- **Link Github Source Code:** https://github.com/ilhamharun17/alumni-tracker-web.git
- **Link Publish Web:** https://alumni-tracker-web.onrender.com

## Fitur Utama

### 1. Multi-Platform Search Engine
Sistem mencari profil alumni di 7 platform secara otomatis:

| Platform | Scoring Bonus | Data Extract |
|----------|--------------|--------------|
| **LinkedIn** | +15 pts | URL, Posisi, Perusahaan |
| **Instagram** | +8 pts | URL Profile |
| **Facebook** | +5 pts | URL Profile |
| **Twitter/X** | +5 pts | URL Profile |
| **TikTok** | +3 pts | URL Profile |
| **About.me** | +10 pts | URL, Email, Phone |
| **GitHub** | +8 pts | URL, Kategori Developer |

### 2. Scoring Algorithm

**Bobot Penilaian:**
- Nama match >80% fuzzy similarity: **+40 pts**
- UMM/Universitas Muhammadiyah Malang mention: **+30 pts**
- Program Studi/Career keyword match: **+20 pts**
- Platform bonus (LinkedIn +15, Instagram +8, dll.)
- Contact info detected (email/phone): **+5 pts**

**Thresholds:**
- **≥80 pts**: Teridentifikasi Kuat (auto-approve)
- **50-79 pts**: Perlu Verifikasi Manual
- **<50 pts**: Tidak Ditemukan

### 3. Auto-Extract Data
Sistem secara otomatis mengekstrak:
- 📧 Email (regex pattern matching)
- 📱 No. HP (format Indonesia: +62/08xx)
- 💼 Tempat Kerja & Posisi
- 🏷️ Kategori Karir (Manajemen, Teknik, Konsultan, dll.)
- 🔗 Semua URL Sosial Media

### 4. Admin Dashboard
- **Search & Filter**: Cari berdasarkan nama/NIM, filter by status
- **Pagination**: 10 data per halaman
- **Real-time Stats**: Tracking progress, strong matches, verification needed
- **Loading Indicator**: Animasi shimmer saat pelacakan berlangsung

### 5. Review & Verification Panel
- **Evidence Display**: Jejak bukti pencarian dengan snippet dan URL sumber
- **Manual Override**: Admin dapat approve/reject dan edit semua field
- **13 Field Editable**: LinkedIn, Instagram, Facebook, Twitter/X, TikTok, Website, Email, No.HP, Tempat Kerja, Alamat Kerja, Posisi, Kategori, Sosmed Kantor

## Arsitektur Sistem

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Admin User    │────▶│   Flask App      │────▶│   SQLite DB     │
│   (Dashboard)   │     │   (Bootstrap 5)  │     │   (142k+ data)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Serper.dev API  │
                        │  (Google Search) │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Scoring Engine  │
                        │  (thefuzz/       │
                        │   rapidfuzz)     │
                        └──────────────────┘
```

## Tabel Pengujian Aplikasi (Quality Testing)

| Aspek Kualitas | Skenario Pengujian | Hasil yang Diharapkan | Status | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| **Functionality (Disambiguasi)** | Melacak alumni dengan nama pasaran "Muhammad Rizky". | Sistem membedakan alumni UMM dengan alumni universitas lain berdasarkan afiliasi dan prodi. | **Pass** | Fuzzy matching + UMM keyword berfungsi dengan baik. |
| **Functionality (Multi-Platform)** | Menekan "Lacak Profil" pada alumni. | Sistem mencari di 7 platform (LinkedIn, IG, FB, Twitter, TikTok, About.me, GitHub) dan menampilkan indikator loading. | **Pass** | Semua platform dicari secara paralel. |
| **Functionality (Auto-Extract)** | Menemukan profil LinkedIn dengan data lengkap. | Sistem auto-extract: URL LinkedIn, Email, No.HP, Tempat Kerja, Posisi, Kategori. | **Pass** | Regex extraction berjalan dengan baik. |
| **Usability** | Dashboard dengan 142k+ data. | Pagination, search, filter berfungsi cepat. Indikator status dengan warna/badge. | **Pass** | Responsif dan informatif. |
| **Reliability** | Mencari alumni tidak terdaftar. | Sistem tidak crash, return status "Tidak Ditemukan" dengan skor 0. | **Pass** | Error handling berfungsi. |

## Environment Variables

Buat file `.env` dari `.env.example`:

```env
SERPER_API_KEY=your_serper_api_key_here
FLASK_SECRET_KEY=your_random_secret_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### Cara Mendapatkan API Key
- **Serper.dev**: Daftar di https://serper.dev (free tier: 2500 requests)
- **Flask Secret Key**: Generate dengan: `python -c "import secrets; print(secrets.token_hex(32))"`

## Cara Menjalankan Secara Lokal

1. **Clone repositori:**
   ```bash
   git clone https://github.com/ilhamharun17/alumni-tracker-web.git
   cd alumni-tracker-web
   ```

2. **Buat virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env dengan API key Anda
   ```

5. **Jalankan aplikasi:**
   ```bash
   python app.py
   ```

6. **Akses browser:**
   - Dashboard: `http://127.0.0.1:5000/`
   - Login: username `admin`, password `admin123` (default dari .env)

**Catatan:** Saat pertama kali dijalankan, sistem akan auto-import 142,122 data alumni dari `Alumni_2000-2025.csv` ke SQLite database.

## Database Schema

### Tabel Alumni (13 Field Hasil Profiling)
| Field | Tipe | Keterangan |
|-------|------|------------|
| linkedin | String(500) | URL LinkedIn |
| instagram | String(500) | URL Instagram |
| facebook | String(500) | URL Facebook |
| twitter_x | String(500) | URL Twitter/X |
| tiktok | String(500) | URL TikTok |
| website_personal | String(500) | URL Portfolio/GitHub/About.me |
| email | String(255) | Email kontak |
| no_hp | String(50) | No. HP Indonesia format |
| tempat_kerja | String(255) | Nama perusahaan/institusi |
| alamat_kerja | Text | Alamat lengkap tempat kerja |
| posisi | String(255) | Jabatan/posisi |
| kategori | String(100) | Manajemen/Teknik/Konsultan/Akademisi/etc. |
| sosmed_kantor | String(500) | IG/Twitter perusahaan |

## Tech Stack

- **Backend:** Flask 3.0.0, Flask-SQLAlchemy 3.1.1
- **Database:** SQLite
- **Frontend:** Bootstrap 5.3, Bootstrap Icons
- **API:** Serper.dev (Google Search API)
- **Scoring:** thefuzz/rapidfuzz (fuzzy string matching)
- **CSV Processing:** pandas

## License

MIT License - Project for Educational Purposes