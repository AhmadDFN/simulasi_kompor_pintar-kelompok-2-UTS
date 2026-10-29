"""
Pengendali aplikasi web Flask untuk simulasi fuzzifikasi sensor termal
kompor pintar.

Rute yang tersedia
------------------
GET  /            – Halaman utama dengan grafik dan tabel pengujian bawaan.
POST /uji-suhu    – Terima input suhu dari form HTML, evaluasi, dan kembalikan
                   halaman dengan hasil terbaru ditambahkan ke riwayat sesi.
GET  /unduh-csv   – Unduh file hasil-pengujian.csv terbaru.
"""

import os

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

# Impor modul logika fuzzy dari direktori yang sama (src/)
from solusi import (
    DAFTAR_SUHU_BAWAAN,
    DIREKTORI_HASIL,
    SUHU_MAKSIMUM,
    SUHU_MINIMUM,
    evaluasi_suhu_tunggal,
    grafik_ke_base64,
    simpan_csv,
    simpan_grafik,
)

# ---------------------------------------------------------------------------
# Inisialisasi aplikasi Flask
# ---------------------------------------------------------------------------
DIREKTORI_TEMPLAT = os.path.join(os.path.dirname(__file__), "templates")

aplikasi = Flask(__name__, template_folder=DIREKTORI_TEMPLAT)
aplikasi.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "kunci-sesi-kompor-pintar-2025"
)


# ---------------------------------------------------------------------------
# Fungsi pembantu internal
# ---------------------------------------------------------------------------

def _bangun_data_bawaan() -> list[dict]:
    """Evaluasi seluruh suhu bawaan dan kembalikan sebagai daftar dictionary."""
    return [
        {**evaluasi_suhu_tunggal(nilai_suhu), "nomor_uji": nomor}
        for nomor, nilai_suhu in enumerate(DAFTAR_SUHU_BAWAAN, start=1)
    ]


def _persentase(nilai_derajat: float) -> int:
    """Konversi derajat keanggotaan (0.0–1.0) ke persentase bilangan bulat."""
    return round(nilai_derajat * 100)


# ---------------------------------------------------------------------------
# RUTE 1 – Halaman Utama
# ---------------------------------------------------------------------------

@aplikasi.route("/", methods=["GET"])
def halaman_utama():
    """
    Render halaman utama aplikasi.

    Memuat dataset pengujian bawaan, grafik kurva keanggotaan (Base64),
    dan riwayat pengujian manual yang tersimpan di sesi Flask.
    """
    # Bersihkan pesan error/sukses satu kali pakai dari sesi
    pesan_galat = session.pop("pesan_galat", None)
    pesan_sukses = session.pop("pesan_sukses", None)
    hasil_terbaru = session.pop("hasil_terbaru", None)

    # Dataset bawaan
    daftar_hasil_bawaan = _bangun_data_bawaan()

    # Riwayat pengujian manual dari sesi
    riwayat_manual: list[dict] = session.get("riwayat_manual", [])

    # Gabungan semua suhu untuk garis penanda grafik
    semua_suhu_penanda = list(DAFTAR_SUHU_BAWAAN) + [
        entri["suhu_celsius"] for entri in riwayat_manual
    ]

    # Suhu yang paling baru diuji (disorot oranye pada grafik)
    suhu_sorot = hasil_terbaru["suhu_celsius"] if hasil_terbaru else None

    # Grafik dikodekan Base64 (tidak perlu file statis)
    data_grafik_base64 = grafik_ke_base64(
        daftar_suhu_penanda=semua_suhu_penanda,
        suhu_sorot=suhu_sorot,
    )

    # Simpan juga grafik ke file untuk tombol unduh
    simpan_grafik(
        daftar_suhu_penanda=semua_suhu_penanda,
        suhu_sorot=suhu_sorot,
    )

    # Perbarui CSV dengan semua data (bawaan + manual)
    semua_hasil_uji = daftar_hasil_bawaan + [
        {**entri, "nomor_uji": len(daftar_hasil_bawaan) + indeks + 1}
        for indeks, entri in enumerate(riwayat_manual)
    ]
    simpan_csv(semua_hasil_uji)

    return render_template(
        "index.html",
        # Parameter domain
        suhu_minimum=SUHU_MINIMUM,
        suhu_maksimum=SUHU_MAKSIMUM,
        # Dataset tabel
        daftar_hasil_bawaan=daftar_hasil_bawaan,
        riwayat_manual=riwayat_manual,
        jumlah_bawaan=len(daftar_hasil_bawaan),
        # Hasil pengujian terbaru (untuk kartu detail kanan)
        hasil_terbaru=hasil_terbaru,
        # Grafik
        data_grafik_base64=data_grafik_base64,
        # Pesan notifikasi
        pesan_galat=pesan_galat,
        pesan_sukses=pesan_sukses,
        # Fungsi pembantu (dipanggil dari templat)
        persentase=_persentase,
    )


# ---------------------------------------------------------------------------
# RUTE 2 – Pengujian Suhu (POST)
# ---------------------------------------------------------------------------

@aplikasi.route("/uji-suhu", methods=["POST"])
def uji_suhu():
    """
    Terima input suhu dari form, validasi, evaluasi, simpan ke sesi.

    Validasi mencakup:
    - Input kosong
    - Input bukan angka
    - Nilai di luar rentang domain sensor (60–110°C)
    """
    masukan_mentah: str = request.form.get("suhu_input", "").strip()

    # Validasi: kosong
    if not masukan_mentah:
        session["pesan_galat"] = "Input suhu tidak boleh kosong."
        return redirect(url_for("halaman_utama"))

    # Validasi: harus angka desimal
    try:
        nilai_suhu = float(masukan_mentah.replace(",", "."))
    except ValueError:
        session["pesan_galat"] = (
            f'"{masukan_mentah}" bukan angka yang valid. '
            "Masukkan nilai numerik seperti 85 atau 87.5."
        )
        return redirect(url_for("halaman_utama"))

    # Validasi dan evaluasi fuzzifikasi
    try:
        data_hasil = evaluasi_suhu_tunggal(nilai_suhu)
    except ValueError as galat:
        session["pesan_galat"] = str(galat)
        return redirect(url_for("halaman_utama"))

    # Tambahkan ke riwayat sesi
    riwayat_manual: list[dict] = session.get("riwayat_manual", [])
    riwayat_manual.append(data_hasil)
    session["riwayat_manual"] = riwayat_manual
    session.modified = True

    # Simpan hasil terbaru untuk ditampilkan di kartu detail
    session["hasil_terbaru"] = data_hasil
    session["pesan_sukses"] = (
        f"Suhu {nilai_suhu:g}°C berhasil diuji — "
        f"status dominan: {data_hasil['status_dominan']}."
    )
    return redirect(url_for("halaman_utama"))


# ---------------------------------------------------------------------------
# RUTE 3 – Reset Riwayat Manual
# ---------------------------------------------------------------------------

@aplikasi.route("/reset-riwayat", methods=["POST"])
def reset_riwayat():
    """Hapus seluruh riwayat pengujian manual dari sesi."""
    session.pop("riwayat_manual", None)
    session.pop("hasil_terbaru", None)
    session["pesan_sukses"] = "Riwayat pengujian manual telah direset."
    return redirect(url_for("halaman_utama"))


# ---------------------------------------------------------------------------
# RUTE 4 – Unduh CSV
# ---------------------------------------------------------------------------

@aplikasi.route("/unduh-csv", methods=["GET"])
def unduh_csv():
    """Kirim file hasil-pengujian.csv terbaru ke browser sebagai unduhan."""
    jalur_csv = os.path.join(DIREKTORI_HASIL, "hasil-pengujian.csv")
    if not os.path.isfile(jalur_csv):
        session["pesan_galat"] = (
            "File CSV belum tersedia. Jalankan pengujian terlebih dahulu."
        )
        return redirect(url_for("halaman_utama"))
    return send_file(
        jalur_csv,
        mimetype="text/csv",
        as_attachment=True,
        download_name="hasil-pengujian.csv",
    )


# ---------------------------------------------------------------------------
# Titik masuk
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Aplikasi Web Kompor Pintar – Fuzzifikasi Suhu")
    print("  Buka browser: http://127.0.0.1:5000")
    print("=" * 60)
    aplikasi.run(debug=True, port=5000)
