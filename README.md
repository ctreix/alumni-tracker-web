# Alumni Tracking System - Daily Project

Proyek ini adalah implementasi sistem pelacakan jejak alumni melalui sumber publik. Sistem ini dilengkapi dengan algoritma agregasi data dan disambiguasi profil untuk menentukan *confidence score* dari pencocokan identitas kandidat di internet.

## Informasi Rilis
- **Link Github Source Code:** https://github.com/ilhamharun17/alumni-tracker-web.git
- **Link Publish Web:** https://alumni-tracker-web.onrender.com

## Tabel Pengujian Aplikasi (Quality Testing)

Pengujian dilakukan berdasarkan skenario Use Case dan Pseudocode yang telah dirancang pada fase desain (Daily Project 2).

| Aspek Kualitas | Skenario Pengujian | Hasil yang Diharapkan | Status Pengujian | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| **Functionality (Disambiguasi)** | Menjalankan pelacakan untuk alumni "Muhammad Rizky" yang memiliki nama pasaran. | Sistem berhasil membedakan "Muhammad Rizky" UMM (LinkedIn) dengan "Muhammad Rizky" Universitas Brawijaya (Scholar) menggunakan pencocokan afiliasi. | **Pass** | Algoritma *Scoring* berfungsi dengan baik memisahkan data ambigu. |
| **Functionality (Status Update)** | Menekan tombol "Lacak Sekarang" pada *dashboard*. | Status berubah dari "Belum Dilacak" menjadi "Teridentifikasi" atau "Perlu Verifikasi Manual" sesuai perhitungan persentase *confidence*. | **Pass** | Transisi *state* data pada *backend* berjalan lancar. |
| **Usability** | Mengevaluasi kemudahan navigasi *dashboard*. | Admin dapat langsung melihat ringkasan identitas, prodi, dan status tanpa harus membuka halaman/menu baru. | **Pass** | Antarmuka disajikan dalam tabel responsif dengan indikator warna (*badge*) yang informatif. |
| **Reliability** | Memaksa sistem mencari alumni yang tidak ada sama sekali di *mock data* (contoh: "Budi Santoso"). | Sistem tidak *crash*, melainkan menangkap *error* dan mengembalikan status "Tidak Ditemukan". | **Pass** | *Error handling* logika *looping* berjalan sesuai pseudocode (kondisi skor = 0). |

## Cara Menjalankan Secara Lokal
1. Clone repositori ini.
2. Pastikan Python 3 sudah terinstal.
3. Buka terminal/command prompt pada folder proyek.
4. Jalankan perintah instalasi: `pip install -r requirements.txt`
5. Nyalakan server lokal: `python app.py`
6. Akses `http://127.0.0.1:5000/` menggunakan *browser* Anda.