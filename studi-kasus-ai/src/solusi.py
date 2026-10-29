"""
Modul logika fuzzy murni untuk simulasi sensor termal kompor pintar.

Berisi fungsi keanggotaan, fuzzifikasi, pembangkit grafik Matplotlib,
dan ekspor CSV. Modul ini TIDAK bergantung pada Flask dan dapat digunakan
secara mandiri maupun diimpor oleh aplikasi_web.py.
"""

import base64
import csv
import io
import os

# ---------------------------------------------------------------------------
# Konstanta domain dan konfigurasi direktori
# ---------------------------------------------------------------------------
SUHU_MINIMUM: float = 60.0
SUHU_MAKSIMUM: float = 110.0
SUHU_TARGET_IDEAL: float = 90.0
DAFTAR_SUHU_BAWAAN: tuple[float, ...] = (72.0, 109.0, 62.0, 94.0)

DIREKTORI_AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIREKTORI_HASIL = os.path.join(DIREKTORI_AKAR, "results")
os.makedirs(DIREKTORI_HASIL, exist_ok=True)

# Konfigurasi Matplotlib agar tidak memerlukan tampilan GUI
os.environ.setdefault(
    "MPLCONFIGDIR", os.path.join(DIREKTORI_HASIL, ".mplconfig")
)

import matplotlib
matplotlib.use("Agg")  # noqa: E402 – harus setelah setdefault MPLCONFIGDIR
import matplotlib.pyplot as plt
import numpy as np


# ===========================================================================
# BAGIAN 1 – FUNGSI KEANGGOTAAN FUZZY
# ===========================================================================

def hitung_derajat_rendah(suhu_input: float) -> float:
    """
    Himpunan fuzzy RENDAH – kurva bahu kiri dengan parameter [60, 60, 75, 90].

    Bernilai 1.0 untuk suhu ≤ 75°C, turun linear hingga 0.0 pada 90°C.
    """
    if suhu_input <= 75:
        return 1.0
    if suhu_input < 90:
        return (90.0 - suhu_input) / (90.0 - 75.0)
    return 0.0


def hitung_derajat_ideal(suhu_input: float) -> float:
    """
    Himpunan fuzzy IDEAL – kurva segitiga dengan parameter [80, 90, 100].

    Naik dari 0.0 pada 80°C ke 1.0 pada 90°C, lalu turun ke 0.0 pada 100°C.
    """
    if suhu_input <= 80 or suhu_input >= 100:
        return 0.0
    if suhu_input <= 90:
        return (suhu_input - 80.0) / (90.0 - 80.0)
    return (100.0 - suhu_input) / (100.0 - 90.0)


def hitung_derajat_tinggi(suhu_input: float) -> float:
    """
    Himpunan fuzzy TINGGI – kurva bahu kanan dengan parameter [90, 100, 110, 110].

    Bernilai 0.0 untuk suhu ≤ 90°C, naik linear hingga 1.0 pada 100°C ke atas.
    """
    if suhu_input <= 90:
        return 0.0
    if suhu_input < 100:
        return (suhu_input - 90.0) / (100.0 - 90.0)
    return 1.0


# ===========================================================================
# BAGIAN 2 – GENERATOR RINCIAN RUMUS (STRING PENJELASAN)
# ===========================================================================

def _rincian_rumus_rendah(suhu_input: float, unicode_aktif: bool = True) -> str:
    """Kembalikan string substitusi rumus untuk himpunan Rendah.

    Parameter
    ----------
    unicode_aktif : bool
        True  → gunakan simbol μ, ≤, ≥, −  (untuk HTML / terminal UTF-8).
        False → gunakan teks ASCII biasa    (untuk terminal Windows cp1252).
    """
    mu = "mu" if not unicode_aktif else "μ"
    lte = "<=" if not unicode_aktif else "≤"
    gte = ">=" if not unicode_aktif else "≥"
    minus = "-" if not unicode_aktif else "−"

    if suhu_input <= 75:
        return f"{mu}_Rendah(T) = 1.0  (karena T {lte} 75)"
    if suhu_input < 90:
        nilai = (90.0 - suhu_input) / 15.0
        return (
            f"{mu}_Rendah(T) = (90 {minus} {suhu_input:g}) / (90 {minus} 75)"
            f" = {90 - suhu_input:g} / 15 = {nilai:.3f}"
        )
    return f"{mu}_Rendah(T) = 0.0  (karena T {gte} 90)"


def _rincian_rumus_ideal(suhu_input: float, unicode_aktif: bool = True) -> str:
    """Kembalikan string substitusi rumus untuk himpunan Ideal."""
    mu = "mu" if not unicode_aktif else "μ"
    lte = "<=" if not unicode_aktif else "≤"
    gte = ">=" if not unicode_aktif else "≥"
    minus = "-" if not unicode_aktif else "−"

    if suhu_input <= 80 or suhu_input >= 100:
        return f"{mu}_Ideal(T) = 0.0  (karena T {lte} 80 atau T {gte} 100)"
    if suhu_input <= 90:
        nilai = (suhu_input - 80.0) / 10.0
        return (
            f"{mu}_Ideal(T) = ({suhu_input:g} {minus} 80) / (90 {minus} 80)"
            f" = {suhu_input - 80:g} / 10 = {nilai:.3f}"
        )
    nilai = (100.0 - suhu_input) / 10.0
    return (
        f"{mu}_Ideal(T) = (100 {minus} {suhu_input:g}) / (100 {minus} 90)"
        f" = {100 - suhu_input:g} / 10 = {nilai:.3f}"
    )


def _rincian_rumus_tinggi(suhu_input: float, unicode_aktif: bool = True) -> str:
    """Kembalikan string substitusi rumus untuk himpunan Tinggi."""
    mu = "mu" if not unicode_aktif else "μ"
    lte = "<=" if not unicode_aktif else "≤"
    gte = ">=" if not unicode_aktif else "≥"
    minus = "-" if not unicode_aktif else "−"

    if suhu_input <= 90:
        return f"{mu}_Tinggi(T) = 0.0  (karena T {lte} 90)"
    if suhu_input < 100:
        nilai = (suhu_input - 90.0) / 10.0
        return (
            f"{mu}_Tinggi(T) = ({suhu_input:g} {minus} 90) / (100 {minus} 90)"
            f" = {suhu_input - 90:g} / 10 = {nilai:.3f}"
        )
    return f"{mu}_Tinggi(T) = 1.0  (karena T {gte} 100)"


# ===========================================================================
# BAGIAN 3 – EVALUASI TERPUSAT (satu sumber kebenaran, prinsip DRY)
# ===========================================================================

def evaluasi_suhu_tunggal(suhu_input: float) -> dict:
    """
    Fungsi terpusat yang mengevaluasi satu nilai suhu input.

    Menghitung derajat keanggotaan ketiga himpunan fuzzy, menentukan status
    dominan, membangun rincian rumus, dan memberikan rekomendasi tindakan.

    Parameter
    ----------
    suhu_input : float
        Nilai suhu dalam derajat Celsius; harus berada di [60, 110].

    Kembalikan
    ----------
    dict dengan kunci:
        - ``suhu_celsius``   : float – nilai suhu input
        - ``derajat_rendah`` : float – derajat keanggotaan himpunan Rendah
        - ``derajat_ideal``  : float – derajat keanggotaan himpunan Ideal
        - ``derajat_tinggi`` : float – derajat keanggotaan himpunan Tinggi
        - ``rumus_rendah``   : str   – rincian substitusi rumus Rendah
        - ``rumus_ideal``    : str   – rincian substitusi rumus Ideal
        - ``rumus_tinggi``   : str   – rincian substitusi rumus Tinggi
        - ``status_dominan`` : str   – label himpunan pemenang
        - ``rekomendasi``    : str   – saran tindakan untuk kompor
        - ``kelas_status``   : str   – kelas Bootstrap untuk badge warna

    Pengecualian
    ------------
    ValueError
        Bila suhu_input berada di luar rentang domain sensor.
    """
    if not (SUHU_MINIMUM <= suhu_input <= SUHU_MAKSIMUM):
        raise ValueError(
            f"Suhu {suhu_input:g}°C berada di luar domain sensor "
            f"({SUHU_MINIMUM:g}°C – {SUHU_MAKSIMUM:g}°C)."
        )

    # -- Hitung ketiga derajat keanggotaan --
    derajat_rendah = hitung_derajat_rendah(suhu_input)
    derajat_ideal = hitung_derajat_ideal(suhu_input)
    derajat_tinggi = hitung_derajat_tinggi(suhu_input)

    # -- Tentukan status dominan --
    peta_derajat = {
        "Rendah": derajat_rendah,
        "Ideal": derajat_ideal,
        "Tinggi": derajat_tinggi,
    }
    nilai_tertinggi = max(peta_derajat.values())
    nama_dominan = [
        nama for nama, derajat in peta_derajat.items()
        if derajat == nilai_tertinggi
    ]

    if len(nama_dominan) > 1:
        status_dominan = "Imbang: " + " & ".join(nama_dominan)
        kelas_status = "secondary"
    else:
        status_dominan = nama_dominan[0]
        kelas_status = {
            "Rendah": "info",
            "Ideal": "success",
            "Tinggi": "danger",
        }.get(status_dominan, "secondary")

    # -- Tentukan rekomendasi tindakan --
    if "Tinggi" in nama_dominan:
        rekomendasi = (
            "Kurangi pemanasan segera — suhu mendekati titik didih dan "
            "berisiko meluapkan cairan."
        )
    elif "Rendah" in nama_dominan:
        rekomendasi = (
            "Lanjutkan pemanasan secara bertahap menuju target 90°C."
        )
    elif "Ideal" in nama_dominan:
        rekomendasi = (
            "Pertahankan intensitas pemanasan — suhu stabil di sekitar "
            "target 90°C."
        )
    else:
        rekomendasi = (
            "Sesuaikan pemanasan secara bertahap sambil terus memantau suhu."
        )

    return {
        "suhu_celsius": suhu_input,
        "derajat_rendah": derajat_rendah,
        "derajat_ideal": derajat_ideal,
        "derajat_tinggi": derajat_tinggi,
        "rumus_rendah": _rincian_rumus_rendah(suhu_input, unicode_aktif=True),
        "rumus_ideal": _rincian_rumus_ideal(suhu_input, unicode_aktif=True),
        "rumus_tinggi": _rincian_rumus_tinggi(suhu_input, unicode_aktif=True),
        "status_dominan": status_dominan,
        "rekomendasi": rekomendasi,
        "kelas_status": kelas_status,
    }


# ===========================================================================
# BAGIAN 4 – EKSPOR CSV
# ===========================================================================

def simpan_csv(daftar_hasil_uji: list[dict]) -> str:
    """
    Tulis seluruh skenario pengujian ke file CSV dengan presisi 4 desimal.

    Parameter
    ----------
    daftar_hasil_uji : list[dict]
        Setiap elemen adalah dictionary hasil ``evaluasi_suhu_tunggal``,
        ditambah kunci opsional ``nomor_uji``.

    Kembalikan
    ----------
    str – Jalur absolut file CSV yang telah disimpan.
    """
    os.makedirs(DIREKTORI_HASIL, exist_ok=True)
    jalur_csv = os.path.join(DIREKTORI_HASIL, "hasil-pengujian.csv")

    nama_kolom = [
        "Nomor_Uji",
        "Suhu_Celsius",
        "Derajat_Rendah",
        "Derajat_Ideal",
        "Derajat_Tinggi",
        "Status_Dominan",
        "Rekomendasi",
    ]

    with open(jalur_csv, "w", newline="", encoding="utf-8") as berkas_csv:
        penulis = csv.DictWriter(berkas_csv, fieldnames=nama_kolom)
        penulis.writeheader()
        for indeks, data in enumerate(daftar_hasil_uji, start=1):
            penulis.writerow({
                "Nomor_Uji": data.get("nomor_uji", indeks),
                "Suhu_Celsius": data["suhu_celsius"],
                "Derajat_Rendah": round(data["derajat_rendah"], 4),
                "Derajat_Ideal": round(data["derajat_ideal"], 4),
                "Derajat_Tinggi": round(data["derajat_tinggi"], 4),
                "Status_Dominan": data["status_dominan"],
                "Rekomendasi": data["rekomendasi"],
            })

    return jalur_csv


# ===========================================================================
# BAGIAN 5 – PEMBANGKIT GRAFIK MATPLOTLIB
# ===========================================================================

def _gambar_grafik_ke_axes(
    sumbu: plt.Axes,
    daftar_suhu_penanda: tuple | list = (),
    suhu_sorot: float | None = None,
) -> None:
    """
    Gambarkan ketiga kurva fungsi keanggotaan ke objek Axes yang diberikan.

    Parameter
    ----------
    sumbu : plt.Axes
        Objek sumbu Matplotlib yang akan digambar.
    daftar_suhu_penanda : tuple | list
        Daftar suhu yang akan ditandai dengan garis vertikal abu-abu.
    suhu_sorot : float | None
        Suhu yang sedang diuji saat ini; ditandai dengan garis vertikal oranye.
    """
    domain_suhu = np.linspace(SUHU_MINIMUM, SUHU_MAKSIMUM, 501)

    konfigurasi_kurva = (
        ("Rendah", hitung_derajat_rendah, "#3b82f6"),   # biru
        ("Ideal",  hitung_derajat_ideal,  "#22c55e"),   # hijau
        ("Tinggi", hitung_derajat_tinggi, "#ef4444"),   # merah
    )

    for nama_himpunan, fungsi_keanggotaan, warna_kurva in konfigurasi_kurva:
        nilai_derajat = np.array(
            [fungsi_keanggotaan(t) for t in domain_suhu]
        )
        sumbu.plot(
            domain_suhu,
            nilai_derajat,
            color=warna_kurva,
            linewidth=2.5,
            label=nama_himpunan,
        )
        # Titik penanda suhu bawaan
        if daftar_suhu_penanda:
            sumbu.scatter(
                daftar_suhu_penanda,
                [fungsi_keanggotaan(t) for t in daftar_suhu_penanda],
                color=warna_kurva,
                edgecolors="white",
                linewidths=0.8,
                s=60,
                zorder=4,
            )

    # -- Garis vertikal untuk suhu penanda bawaan --
    for indeks, nilai_suhu in enumerate(daftar_suhu_penanda):
        sumbu.axvline(
            nilai_suhu,
            color="gray",
            linestyle="--",
            linewidth=0.9,
            alpha=0.6,
            label="Suhu pengujian" if indeks == 0 else None,
        )
        sumbu.annotate(
            f"{nilai_suhu:g}°C",
            xy=(nilai_suhu, 1.0),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color="#4b5563",
        )

    # -- Garis vertikal oranye untuk suhu yang sedang disorot --
    if suhu_sorot is not None:
        sumbu.axvline(
            suhu_sorot,
            color="#f97316",
            linestyle="-",
            linewidth=2.0,
            alpha=0.85,
            label=f"Suhu diuji: {suhu_sorot:g}°C",
            zorder=5,
        )
        sumbu.annotate(
            f"▲ {suhu_sorot:g}°C",
            xy=(suhu_sorot, 1.08),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="#f97316",
        )

    sumbu.set_title(
        "Fungsi Keanggotaan Suhu Kompor Pintar",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    sumbu.set_xlabel("Suhu Kompor (°C)", fontsize=11)
    sumbu.set_ylabel("Derajat Keanggotaan (μ)", fontsize=11)
    sumbu.set_xlim(SUHU_MINIMUM, SUHU_MAKSIMUM)
    sumbu.set_ylim(-0.04, 1.16)
    sumbu.set_xticks(np.arange(SUHU_MINIMUM, SUHU_MAKSIMUM + 1, 5))
    sumbu.grid(True, linestyle=":", alpha=0.5)
    sumbu.legend(fontsize=10)


def simpan_grafik(
    daftar_suhu_penanda: tuple | list = DAFTAR_SUHU_BAWAAN,
    suhu_sorot: float | None = None,
) -> str:
    """
    Render grafik kurva keanggotaan ke file PNG di direktori hasil.

    Parameter
    ----------
    daftar_suhu_penanda : tuple | list
        Suhu yang ditandai titik & garis vertikal abu-abu.
    suhu_sorot : float | None
        Suhu saat ini yang akan disorot dengan garis oranye.

    Kembalikan
    ----------
    str – Jalur absolut file PNG yang telah disimpan.
    """
    os.makedirs(DIREKTORI_HASIL, exist_ok=True)
    gambar, sumbu = plt.subplots(figsize=(10, 6))
    _gambar_grafik_ke_axes(sumbu, daftar_suhu_penanda, suhu_sorot)
    gambar.tight_layout()

    jalur_grafik = os.path.join(DIREKTORI_HASIL, "visualisasi.png")
    gambar.savefig(jalur_grafik, dpi=150, bbox_inches="tight")
    plt.close(gambar)
    return jalur_grafik


def grafik_ke_base64(
    daftar_suhu_penanda: tuple | list = DAFTAR_SUHU_BAWAAN,
    suhu_sorot: float | None = None,
) -> str:
    """
    Render grafik kurva keanggotaan langsung ke string Base64 PNG.

    Digunakan oleh aplikasi_web.py agar gambar dapat disematkan langsung
    di dalam respons HTML tanpa menyimpan file sementara.

    Kembalikan
    ----------
    str – String data URI siap pakai untuk atribut ``src`` pada tag ``<img>``.
    """
    gambar, sumbu = plt.subplots(figsize=(10, 6))
    _gambar_grafik_ke_axes(sumbu, daftar_suhu_penanda, suhu_sorot)
    gambar.tight_layout()

    penyangga = io.BytesIO()
    gambar.savefig(penyangga, format="png", dpi=150, bbox_inches="tight")
    plt.close(gambar)
    penyangga.seek(0)

    data_base64 = base64.b64encode(penyangga.read()).decode("utf-8")
    return f"data:image/png;base64,{data_base64}"


# ===========================================================================
# BAGIAN 6 – ANTARMUKA CLI (dijalankan langsung via `python src/solusi.py`)
# ===========================================================================

def _tampilkan_hasil_terminal(nomor: int, data: dict) -> None:
    """Cetak hasil evaluasi satu skenario ke terminal dengan format rapi."""
    print("\n" + "=" * 68)
    print(f"UJI {nomor} -- SUHU KOMPOR {data['suhu_celsius']:g} derajat C")
    print("=" * 68)
    print("Perhitungan derajat keanggotaan:")
    print(f"  {_rincian_rumus_rendah(data['suhu_celsius'], unicode_aktif=False)}")
    print(f"  {_rincian_rumus_ideal(data['suhu_celsius'], unicode_aktif=False)}")
    print(f"  {_rincian_rumus_tinggi(data['suhu_celsius'], unicode_aktif=False)}")
    print(
        f"Hasil fuzzifikasi: "
        f"mu_Rendah={data['derajat_rendah']:.3f}, "
        f"mu_Ideal={data['derajat_ideal']:.3f}, "
        f"mu_Tinggi={data['derajat_tinggi']:.3f}"
    )
    print(f"Status dominan  : {data['status_dominan']}")
    print(f"Rekomendasi     : {data['rekomendasi']}")
    print("-" * 68)


def _minta_input_manual(nomor_berikutnya: int) -> dict | None:
    """
    Tawarkan pengujian suhu tambahan melalui terminal.

    Mendukung loop berulang agar pengguna dapat menguji beberapa suhu
    tanpa membatasi hanya satu kali input.
    """
    try:
        jawaban = input(
            "\nIngin menguji suhu tambahan? (y/t): "
        ).strip().lower()
    except EOFError:
        print("\nMode non-interaktif – pengujian manual dilewati.")
        return None

    if jawaban not in ("y", "ya"):
        return None

    while True:
        try:
            masukan_suhu = input(
                f"Masukkan suhu ({SUHU_MINIMUM:g}–{SUHU_MAKSIMUM:g}°C): "
            ).strip()
            nilai_suhu = float(masukan_suhu)
        except ValueError:
            print("  ✗ Input tidak valid – harap masukkan angka desimal.")
            continue
        except EOFError:
            print("\n  Input suhu dilewati.")
            return None

        try:
            data_hasil = evaluasi_suhu_tunggal(nilai_suhu)
            data_hasil["nomor_uji"] = nomor_berikutnya
            return data_hasil
        except ValueError as galat:
            print(f"  ✗ {galat}")


def utama() -> None:
    """Titik masuk utama untuk mode CLI."""
    daftar_hasil_uji: list[dict] = []

    for nomor, nilai_suhu in enumerate(DAFTAR_SUHU_BAWAAN, start=1):
        data = evaluasi_suhu_tunggal(nilai_suhu)
        data["nomor_uji"] = nomor
        _tampilkan_hasil_terminal(nomor, data)
        daftar_hasil_uji.append(data)

    # Pengujian manual berulang
    nomor_berikutnya = len(daftar_hasil_uji) + 1
    while True:
        data_manual = _minta_input_manual(nomor_berikutnya)
        if data_manual is None:
            break
        _tampilkan_hasil_terminal(nomor_berikutnya, data_manual)
        daftar_hasil_uji.append(data_manual)
        nomor_berikutnya += 1

    # Simpan keluaran
    jalur_csv = simpan_csv(daftar_hasil_uji)
    semua_suhu = [d["suhu_celsius"] for d in daftar_hasil_uji]
    jalur_grafik = simpan_grafik(daftar_suhu_penanda=semua_suhu)

    print(f"\nCSV berhasil disimpan   : {jalur_csv}")
    print(f"Grafik berhasil disimpan: {jalur_grafik}")


if __name__ == "__main__":
    utama()
