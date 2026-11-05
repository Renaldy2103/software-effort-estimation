"""Membandingkan prediksi aplikasi dengan artefak hasil training.

Sampel adalah baris data uji pertama pada hasil_prediksi.csv.
Fitur proyeknya diambil dari nasa93.arff dan sudah dicocokkan dengan
predicted effort 595.9722943472086.
"""

from app import app, format_effort
from model_service import effort_model

SAMPLE = {
    "cat2": "datacapture",
    "forg": "g",
    "center": "2",
    "year": "1980",
    "mode": "semidetached",
    "rely": "n",
    "data": "h",
    "cplx": "h",
    "time": "vh",
    "stor": "h",
    "virt": "l",
    "turn": "h",
    "acap": "h",
    "aexp": "n",
    "pcap": "h",
    "vexp": "l",
    "lexp": "h",
    "modp": "h",
    "tool": "n",
    "sced": "l",
    "equivphyskloc": "177.9",
}
EXPECTED = 595.9722943472086


def main():
    cleaned = effort_model.validate(SAMPLE)
    direct = effort_model.predict(cleaned)
    if abs(direct - EXPECTED) > 1e-9:
        raise SystemExit(f"Prediksi langsung berbeda: {direct} != {EXPECTED}")

    client = app.test_client()
    response = client.post("/estimasi", data=SAMPLE, follow_redirects=True)
    page = response.get_data(as_text=True)
    shown = format_effort(EXPECTED)
    if response.status_code != 200 or shown not in page:
        raise SystemExit(f"Halaman hasil tidak menampilkan {shown}. Status {response.status_code}")

    invalid = client.post("/estimasi", data={**SAMPLE, "equivphyskloc": "nan"})
    if "angka yang valid" not in invalid.get_data(as_text=True).lower() and "tidak boleh" not in invalid.get_data(as_text=True).lower():
        raise SystemExit("Validasi NaN tidak menolak input.")

    print(f"Konsisten: {direct}")
    print(f"Tampilan: {shown} Person-Months")


if __name__ == "__main__":
    main()
