# Pemodelan Sensor Termal Kompor Gas Pintar untuk Pemantauan Suhu Pemanasan dengan permisalan 90°C Menggunakan Logika Fuzzy

Repositori ini dibuat untuk memenuhi tugas proyek mata kuliah **Kecerdasan Buatan** pada topik **Logika Fuzzy dan Fungsi Keanggotaan (Topik 3)**.

---

## 1. Identitas Kelompok

**Nama Kelompok:** _KELOMPOK 2_  
**Kelas:** _5A_

| No. | Nama Anggota  | NIM           |
| --: | ------------- | ------------- |
|   1 | Ahmad Dany FN | _2605101063L_ |
|   2 | Anjar         | _(Isi NIM)_   |
|   3 | Yohan         | _(Isi NIM)_   |

---

## 2. Informasi Studi Kasus

### Judul Studi Kasus

**Pemodelan Sensor Termal Kompor Gas Pintar Rumah Tangga untuk Pemantauan Target Suhu Pemanasan Stabil 90°C Menggunakan Logika Fuzzy dan Fungsi Keanggotaan**

### Latar Belakang dan Deskripsi Masalah

Dalam kegiatan memasak di rumah tangga, beberapa proses pengolahan bahan makanan atau minuman membutuhkan suhu pemanasan yang terjaga di kisaran _sub-boiling_ (**90°C**), misalnya saat merebus kaldu agar tetap jernih, memanaskan susu, atau merebus adonan tertentu agar tidak pecah dan meluap karena mendidih penuh (100°C).

Masalahnya, jika kita menggunakan logika tegas (_crisp_) atau batas saklek pada sensor kompor, pembacaan suhu menjadi kaku. Contohnya, jika batas suhu ideal dipatok tepat 90°C, maka suhu 88°C atau 89°C akan langsung dianggap "belum panas", padahal secara fisik air sudah hampir mencapai target dan panas dari tungku masih terus merambat naik.

Melalui pendekatan **Logika Fuzzy**, pembacaan suhu kompor pada rentang **60°C sampai 110°C** dapat dipetakan secara bertahap ke dalam tiga kategori linguistik: **Rendah**, **Ideal**, dan **Tinggi**. Dengan cara ini, masa transisi suhu (seperti saat suhu berada di 85°C atau 94°C) dapat terukur proporsinya dengan lebih masuk akal.

### Tujuan Penyelesaian

1. Mendefinisikan variabel linguistik dan himpunan fuzzy untuk memodelkan pembacaan suhu pada kompor pintar.
2. Menyusun fungsi keanggotaan menggunakan kurva bahu kiri, segitiga, dan bahu kanan.
3. Melakukan proses fuzzifikasi pada beberapa sampel suhu uji beserta rincian perhitungannya.
4. Menyajikan hasil pemetaan derajat keanggotaan dalam bentuk tabel (`.csv`) dan grafik visualisasi kurva (`.png`).

### Topik dan Metode AI yang Dipilih

- **Topik:** Topik 3 — Logika Fuzzy dan Fungsi Keanggotaan.
- **Metode AI:** Representasi Pengetahuan Fuzzy dan Fuzzifikasi (Pemetaan _Crisp Input_ ke Derajat Keanggotaan).
- **Alasan Pemilihan Metode:** Perubahan suhu air di atas kompor bersifat kontinu dan memiliki area transisi yang samar. Logika fuzzy sangat cocok digunakan karena mampu menilai kondisi suhu secara bertahap (nilai keanggotaan 0 sampai 1), bukan sekadar benar atau salah (0 atau 1).

---

## 3. Deskripsi Metode dan Perancangan Solusi

### Variabel dan Himpunan Fuzzy

Variabel yang dimodelkan adalah **Suhu Kompor (T)** dengan semesta pembicaraan (domain) **60°C hingga 110°C**. Variabel ini dibagi menjadi tiga himpunan fuzzy:

| Himpunan Fuzzy | Bentuk Kurva | Parameter Titik (°C)  | Penjelasan Kondisi                                                                                                 |
| -------------- | ------------ | --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Rendah**     | Bahu Kiri    | `[60, 60, 75, 90]`    | Suhu pemanasan awal (kurang panas). Bernilai penuh (1.0) hingga 75°C, lalu turun bertahap sampai 0 pada 90°C.      |
| **Ideal**      | Segitiga     | `[80, 90, 100]`       | Area target pemanasan. Mulai naik dari 80°C, mencapai puncak (1.0) tepat di 90°C, lalu turun hingga 0 pada 100°C.  |
| **Tinggi**     | Bahu Kanan   | `[90, 100, 110, 110]` | Suhu berlebih (_overheat_) atau rawan mendidih. Mulai naik dari 90°C dan bernilai penuh (1.0) mulai 100°C ke atas. |

### Rumus Fungsi Keanggotaan

1. **Himpunan Rendah (`mu_Rendah`):**
   - Bernilai `1.0` jika `T <= 75`
   - Bernilai `(90 - T) / (90 - 75)` jika `75 < T < 90`
   - Bernilai `0.0` jika `T >= 90`

2. **Himpunan Ideal (`mu_Ideal`):**
   - Bernilai `0.0` jika `T <= 80` atau `T >= 100`
   - Bernilai `(T - 80) / (90 - 80)` jika `80 < T <= 90`
   - Bernilai `(100 - T) / (100 - 90)` jika `90 < T < 100`

3. **Himpunan Tinggi (`mu_Tinggi`):**
   - Bernilai `0.0` jika `T <= 90`
   - Bernilai `(T - 90) / (100 - 90)` jika `90 < T < 100`
   - Bernilai `1.0` jika `T >= 100`

### Gambaran Cara Kerja & Pseudocode

Program bekerja dengan menerima masukan suhu (`T`), menghitung nilai derajat keanggotaan untuk ketiga kurva, menampilkan langkah perhitungannya di layar, lalu menentukan status kondisi suhu berdasarkan nilai derajat tertinggi.

```text
ALGORITMA Fuzzifikasi_Suhu_Kompor
INPUT: suhu_kompor (T) pada rentang 60 - 110
OUTPUT: u_rendah, u_ideal, u_tinggi, status_dominan

1. Hitung u_rendah berdasarkan batas kurva [60, 60, 75, 90]
2. Hitung u_ideal berdasarkan batas kurva [80, 90, 100]
3. Hitung u_tinggi berdasarkan batas kurva [90, 100, 110, 110]
4. Tampilkan rincian rumus dan hasil perhitungan ke layar terminal
5. Bandingkan nilai (u_rendah, u_ideal, u_tinggi) untuk mencari nilai tertinggi sebagai status_dominan
6. Simpan hasil ke tabel CSV dan gambarkan titik pengujian pada grafik fungsi keanggotaan
```

### Contoh Perhitungan Manual (Sampel Suhu = 85°C)

Sebagai verifikasi sebelum masuk ke program, berikut perhitungan manual ketika suhu berada di **85°C**:

- **Himpunan Rendah:** Karena `85` berada di antara `75` dan `90`, maka:
  `mu_Rendah(85) = (90 - 85) / (90 - 75) = 5 / 15 = 0.333`
- **Himpunan Ideal:** Karena `85` berada di antara `80` dan `90`, maka:
  `mu_Ideal(85) = (85 - 80) / (90 - 80) = 5 / 10 = 0.500`
- **Himpunan Tinggi:** Karena `85 <= 90`, maka:
  `mu_Tinggi(85) = 0.000`
- **Interpretasi:** Pada suhu 85°C, kondisi air masih memiliki unsur _Rendah_ sebesar 0.333 (33,3%), namun sudah didominasi oleh kondisi _Ideal_ sebesar 0.500 (50,0%).

### Asumsi dan Batasan

- Nilai suhu yang dimasukkan diasumsikan berasal dari pembacaan sensor dalam satuan derajat Celsius (°C) pada rentang 60°C sampai 110°C.
- Fokus penyelesaian pada Topik 3 ini adalah pemodelan fungsi keanggotaan dan proses fuzzifikasi pada satu variabel suhu, belum mencakup evaluasi aturan (_rule inference_) maupun kontrol katup mekanis secara langsung.
- Kondisi lingkungan sekitar kompor (seperti suhu ruangan dan ukuran panci) diasumsikan konstan.

---

## 4. Kebutuhan Perangkat Lunak

- **Bahasa Pemrograman:** Python 3.x (diuji pada Python 3.12).
- **Library yang Diperlukan:**
  - `numpy` (untuk mengolah titik koordinat kurva).
  - `matplotlib` (untuk membuat grafik visualisasi fungsi keanggotaan).
  - _(Perhitungan logika fuzzy ditulis langsung dari nol tanpa library `scikit-fuzzy` agar proses rumusnya terlihat jelas)._

### Petunjuk Instalasi Dependensi

Buka terminal di direktori proyek, lalu jalankan perintah berikut:

```bash
python -m pip install numpy matplotlib
```

---

## 5. Cara Menjalankan Program

1. Pastikan terminal berada di direktori utama proyek (`studi-kasus-ai/`).
2. Jalankan program dengan perintah:

```bash
python src/solusi.py
```

3. Program akan otomatis menjalankan **4 skenario pengujian suhu** (72°C, 85°C, 90°C, dan 94°C).
4. Setelah itu, program akan bertanya apakah Anda ingin menguji suhu tambahan secara manual. Ketik `y` untuk memasukkan angka suhu (60–110°C), atau ketik `t` untuk melewati:

```text
Ingin memasukkan suhu secara manual? (y/t): y
Masukkan suhu (60–110°C): 96
```

5. Setelah selesai, file `results/hasil-pengujian.csv`, `results/visualisasi.png`, serta tiga gambar transkrip terminal di `screenshots/` akan otomatis dibuat atau diperbarui.

---

## 6. Hasil dan Pengujian

### Contoh Keluaran Program

Berikut adalah contoh keluaran terminal untuk pengujian suhu **85°C**:

```text
mu_Rendah(T) = (90 - 85) / (90 - 75) = 0.333
mu_Ideal(T) = (85 - 80) / (90 - 80) = 0.500
mu_Tinggi(T) = 0.0, karena T <= 90
Hasil fuzzifikasi: mu_Rendah=0.333, mu_Ideal=0.500, mu_Tinggi=0.000
Status dominan: Ideal (target stabil)
```

### Ringkasan Skenario Pengujian

| No. | Suhu Uji | μ Rendah | μ Ideal | μ Tinggi | Status Dominan        | Analisis Kondisi Kompor                                                                  |
| --: | -------: | -------: | ------: | -------: | --------------------- | ---------------------------------------------------------------------------------------- |
|   1 | **72°C** |    1.000 |   0.000 |    0.000 | Rendah (kurang panas) | Air masih jauh dari target 90°C, masuk kategori rendah sepenuhnya.                       |
|   2 | **85°C** |    0.333 |   0.500 |    0.000 | Ideal (target stabil) | Suhu berada di masa transisi mendekati 90°C, mulai didominasi status Ideal.              |
|   3 | **90°C** |    0.000 |   1.000 |    0.000 | Ideal (target stabil) | Suhu berada tepat di titik target pemanasan yang diinginkan.                             |
|   4 | **94°C** |    0.000 |   0.600 |    0.400 | Ideal (target stabil) | Suhu mulai melewati 90°C; masih dominan Ideal (60%) namun mulai masuk area Tinggi (40%). |

### Tautan Berkas Hasil dan Screenshot

- **Tabel Hasil Pengujian (CSV):** [`results/hasil-pengujian.csv`](results/hasil-pengujian.csv)
- **Visualisasi Grafik Kurva:** [`results/visualisasi.png`](results/visualisasi.png)
- **Screenshot Eksekusi Terminal:**
  - [`screenshots/eksekusi-1.png`](screenshots/eksekusi-1.png)
  - [`screenshots/eksekusi-2.png`](screenshots/eksekusi-2.png)
  - [`screenshots/eksekusi-3.png`](screenshots/eksekusi-3.png)

---

## 7. Kesimpulan

### Ringkasan Hasil Penyelesaian

Berdasarkan hasil pengujian, model fungsi keanggotaan yang dibuat berhasil memetakan nilai suhu kompor ke dalam derajat keanggotaan fuzzy dengan akurat dan sesuai dengan perhitungan manual. Pendekatan ini membuktikan bahwa satu nilai suhu (misalnya 85°C dan 94°C) dapat memiliki keanggotaan pada lebih dari satu himpunan sekaligus, sehingga memberikan gambaran transisi suhu yang lebih informatif dibandingkan batas angka biasa.

### Keterbatasan Solusi

- Pemodelan saat ini hanya menggunakan satu variabel input (suhu kompor) dan berfokus pada tahap fuzzifikasi serta penentuan status dominan.
- Nilai batas titik kurva ditentukan berdasarkan simulasi rentang pemanasan, belum melalui kalibrasi sensor secara fisik.

### Saran Pengembangan

Pada pengembangan berikutnya, model ini dapat dilanjutkan menjadi **Fuzzy Inference System (FIS)** penuh dengan menambahkan variabel kedua seperti **laju perubahan suhu**, serta menambahkan aturan _IF-THEN_ dan proses defuzzifikasi untuk mengatur bukaan katup gas secara otomatis.
# komporpintar-kelompok2
