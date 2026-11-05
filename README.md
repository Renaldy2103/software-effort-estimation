# Software Effort Estimation

Aplikasi web untuk estimasi effort pengembangan perangkat lunak menggunakan model **Regresi Elastic Net** yang sudah dilatih. Hasil estimasi ditampilkan dalam **person-months**.

Aplikasi ini mendukung penelitian skripsi:

**Estimasi Effort Pengembangan Perangkat Lunak Menggunakan Regresi Elastic Net**

Model tidak dilatih ulang saat pengguna meminta prediksi. Pipeline hasil training dipakai secara utuh, termasuk preprocessing yang sudah tersimpan di dalamnya.

## Teknologi

- Python
- Flask
- Joblib
- Pandas
- NumPy
- Scikit-learn
- SQLite
- HTML5, CSS3, Bootstrap 5, dan JavaScript

Model dilatih dengan scikit-learn **1.6.1**. Lingkungan pengembangan aplikasi ini memakai scikit-learn **1.9.1** pada Python 3.15. Saat file model dibuka, aplikasi menambahkan kelas kompatibilitas `_RemainderColsList` agar pipeline versi 1.6.1 dapat dimuat. Pemeriksaan numerik menunjukkan prediksi aplikasi sama dengan artefak `hasil_prediksi.csv`.

## Struktur folder

```text
elastic_net_web/
├── app.py
├── config.py
├── model_service.py
├── database.py
├── check_consistency.py
├── requirements.txt
├── README.md
├── models/
│   ├── elastic_net_pipeline.pkl
│   └── input_schema.json
├── database/
│   └── predictions.db          # dibuat otomatis saat aplikasi dijalankan
├── NASA93_ElasticNet_Results/  # artefak training asli
├── templates/
└── static/
```

## Model yang dipakai

File yang dimuat aplikasi:

- `models/elastic_net_pipeline.pkl`
- `models/input_schema.json`

Pipeline berisi:

1. `ColumnTransformer`
   - `year` dan `equivphyskloc`: StandardScaler
   - 15 cost driver COCOMO: OrdinalEncoder, lalu StandardScaler
   - `cat2`, `forg`, `center`, dan `mode`: OneHotEncoder
2. `ElasticNet` dengan alpha **1** dan l1_ratio **0.7**

Target `act_effort` tidak menjadi input. Tidak ada transformasi log pada target, sehingga hasil `predict()` langsung ditampilkan sebagai person-months.

Fitur input mengikuti `feature_names_in_` pada pipeline dan `input_schema.json` (21 fitur). Identifier seperti `recordnumber` dan `projectname` tidak digunakan.

## Instalasi

Dari folder project:

```powershell
python -m pip install -r requirements.txt
```

## Menempatkan file model

Salinan yang dipakai aplikasi sudah berada di folder `models/`. Jika file diganti, gunakan pipeline lengkap hasil training beserta `input_schema.json` yang fiturnya sama dengan pipeline. Jangan mengganti pipeline dengan model yang hanya berisi estimator tanpa preprocessing.

Artefak training asli tetap disimpan di `NASA93_ElasticNet_Results/`.

## Menjalankan aplikasi

```powershell
python app.py
```

Debug mode tidak aktif. Untuk mengaktifkannya sementara saat pengembangan:

```powershell
$env:FLASK_DEBUG = "1"
python app.py
```

Buka browser pada [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Penggunaan

1. Buka dasbor untuk melihat metode, satuan, alpha, l1 ratio, dan hasil evaluasi artefak training.
2. Buka halaman **Estimasi**.
3. Isi karakteristik proyek. Seluruh fitur wajib diisi.
4. Tekan **Hitung Estimasi**.
5. Halaman hasil menampilkan estimasi dalam person-months, ringkasan input, serta tombol cetak.
6. Riwayat prediksi tersimpan di SQLite dan dapat dilihat atau dihapus. Riwayat tidak dipakai untuk training.

## Pengujian prediksi

`check_consistency.py` mengirim satu proyek dari data uji:

- kategori `datacapture`, jenis sistem `g`, pusat `2`, tahun `1980`, mode `semidetached`
- cost driver: rely `n`, data `h`, cplx `h`, time `vh`, stor `h`, virt `l`, turn `h`, acap `h`, aexp `n`, pcap `h`, vexp `l`, lexp `h`, modp `h`, tool `n`, sced `l`
- ukuran kode `177.9` KLOC
- effort aktual pada dataset: `1248` person-months, tidak ikut dikirim ke model

Nilai pembanding dari `hasil_prediksi.csv` adalah **595.9722943472086**. Aplikasi menampilkannya sebagai **595,97 Person-Months**.

```powershell
python check_consistency.py
```

Pemeriksaan terpisah terhadap seluruh 19 baris `hasil_prediksi.csv` juga cocok dengan prediksi pipeline pada baris NASA93 yang effort aktualnya sama. Selisih numeriknya 0.

## Catatan

Model regresi dapat menghasilkan estimasi negatif untuk kombinasi fitur tertentu. Aplikasi menampilkan keluaran model apa adanya dan memberi keterangan bila nilainya negatif. Nilai pada halaman hasil adalah estimasi, bukan effort aktual.
