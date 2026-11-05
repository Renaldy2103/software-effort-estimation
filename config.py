import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.environ.get("SECRET_KEY", "software-effort-estimation-dev")
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLASK_PORT", "5000"))

MODEL_PATH = BASE_DIR / "models" / "elastic_net_pipeline.pkl"
SCHEMA_PATH = BASE_DIR / "models" / "input_schema.json"
RESULTS_DIR = BASE_DIR / "NASA93_ElasticNet_Results"
DATABASE_PATH = BASE_DIR / "database" / "predictions.db"

APP_NAME = "Software Effort Estimation"
APP_SUBTITLE = (
    "Estimasi Effort Pengembangan Perangkat Lunak Menggunakan Regresi Elastic Net"
)
EFFORT_UNIT = "Person-Months"

# Dokumentasi NASA93: satu person-month = 152 jam,
# mencakup jam pengembangan dan manajemen.
PERSON_MONTH_HOURS = 152

# Urutan dan pengelompokan mengikuti fitur yang benar-benar ada di input_schema.json.
# Kunci yang tidak ada di skema tidak akan ditampilkan.
FEATURE_GROUPS = [
    {
        "id": "umum",
        "title": "Karakteristik Umum Proyek",
        "description": "Konteks aplikasi, organisasi, tahun, dan mode pengembangan.",
        "fields": ["cat2", "forg", "center", "year", "mode"],
    },
    {
        "id": "ukuran",
        "title": "Ukuran Perangkat Lunak",
        "description": "Ukuran kode yang dipakai model, dalam ribuan baris kode.",
        "fields": ["equivphyskloc"],
    },
    {
        "id": "produk",
        "title": "Atribut Produk",
        "description": "Cost driver COCOMO yang menggambarkan produk perangkat lunak.",
        "fields": ["rely", "data", "cplx"],
    },
    {
        "id": "platform",
        "title": "Atribut Platform",
        "description": "Batasan waktu, penyimpanan, dan lingkungan eksekusi.",
        "fields": ["time", "stor", "virt", "turn"],
    },
    {
        "id": "personel",
        "title": "Atribut Personel",
        "description": "Kapabilitas dan pengalaman tim pengembang.",
        "fields": ["acap", "aexp", "pcap", "vexp", "lexp"],
    },
    {
        "id": "proyek",
        "title": "Atribut Proyek",
        "description": "Praktik, alat bantu, dan tekanan jadwal pengembangan.",
        "fields": ["modp", "tool", "sced"],
    },
]

FEATURE_LABELS = {
    "cat2": "Kategori aplikasi",
    "forg": "Jenis sistem",
    "center": "Kode pusat pengembangan",
    "year": "Tahun pengembangan",
    "mode": "Mode pengembangan",
    "equivphyskloc": "Ukuran kode",
    "rely": "Keandalan perangkat lunak",
    "data": "Ukuran basis data",
    "cplx": "Kompleksitas produk",
    "time": "Batasan waktu eksekusi",
    "stor": "Batasan penyimpanan utama",
    "virt": "Volatilitas mesin virtual",
    "turn": "Waktu turnaround komputer",
    "acap": "Kapabilitas analis",
    "aexp": "Pengalaman aplikasi",
    "pcap": "Kapabilitas programmer",
    "vexp": "Pengalaman mesin virtual",
    "lexp": "Pengalaman bahasa pemrograman",
    "modp": "Praktik pemrograman modern",
    "tool": "Penggunaan alat bantu perangkat lunak",
    "sced": "Jadwal pengembangan",
}

FEATURE_HELP = {
    "cat2": "Kategori aplikasi pada dataset NASA93.",
    "forg": "f = flight (sistem penerbangan), g = ground (sistem darat).",
    "center": "Kode pusat NASA yang dikenali model. Kode 4 tidak ada pada kategori hasil training.",
    "year": "Tahun proyek. Pada dataset penelitian, tahun berkisar 1971–1987.",
    "mode": "Mode pengembangan COCOMO: organic, semi-detached, atau embedded.",
    "equivphyskloc": "equivphyskloc, dalam KLOC (thousands of lines of code). Pada dataset, nilai berkisar 0,9–980.",
    "rely": "Required software reliability.",
    "data": "Database size.",
    "cplx": "Product complexity.",
    "time": "Time constraint.",
    "stor": "Main storage constraint.",
    "virt": "Virtual machine volatility.",
    "turn": "Computer turnaround time.",
    "acap": "Analyst capability.",
    "aexp": "Applications experience.",
    "pcap": "Programmer capability.",
    "vexp": "Virtual machine experience.",
    "lexp": "Programming language experience.",
    "modp": "Use of modern programming practices.",
    "tool": "Use of software tools.",
    "sced": "Required development schedule.",
}

FEATURE_UNITS = {
    "year": "tahun",
    "equivphyskloc": "KLOC",
}

RATING_LABELS = {
    "vl": "Sangat rendah (vl)",
    "l": "Rendah (l)",
    "n": "Nominal (n)",
    "h": "Tinggi (h)",
    "vh": "Sangat tinggi (vh)",
    "xh": "Ekstra tinggi (xh)",
}

CATEGORY_LABELS = {
    "cat2": {
        "Avionics": "Avionics",
        "application_ground": "Aplikasi darat (application ground)",
        "avionicsmonitoring": "Pemantauan avionik",
        "batchdataprocessing": "Pemrosesan data batch",
        "communications": "Komunikasi",
        "datacapture": "Akuisisi data",
        "launchprocessing": "Pemrosesan peluncuran",
        "missionplanning": "Perencanaan misi",
        "monitor_control": "Pemantauan dan kendali",
        "operatingsystem": "Sistem operasi",
        "realdataprocessing": "Pemrosesan data real-time",
        "science": "Sains",
        "simulation": "Simulasi",
        "utility": "Utilitas",
    },
    "forg": {
        "f": "Flight — sistem penerbangan (f)",
        "g": "Ground — sistem darat (g)",
    },
    "center": {
        "1": "Pusat 1",
        "2": "Pusat 2",
        "3": "Pusat 3",
        "5": "Pusat 5",
        "6": "Pusat 6",
    },
    "mode": {
        "organic": "Organic",
        "semidetached": "Semi-detached",
        "embedded": "Embedded",
    },
}
