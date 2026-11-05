from app import app
from model_service import ValidationError, effort_model
import database

client = app.test_client()
for path in ["/", "/estimasi", "/model", "/riwayat"]:
    response = client.get(path)
    if response.status_code != 200:
        raise SystemExit(f"{path} -> {response.status_code}")

html = client.get("/estimasi").get_data(as_text=True)
for name in effort_model.feature_names:
    if f'name="{name}"' not in html:
        raise SystemExit(f"missing field {name}")
if "act_effort" in html:
    raise SystemExit("target leaked into form")

base = {
    "cat2": "datacapture",
    "forg": "g",
    "center": "4",
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
page = client.post("/estimasi", data=base).get_data(as_text=True)
if "tidak termasuk kategori" not in page:
    raise SystemExit("invalid category accepted")

page = client.post("/estimasi", data={**base, "center": "2", "equivphyskloc": "inf"}).get_data(as_text=True)
if "tak hingga" not in page:
    raise SystemExit("infinity accepted")

page = client.post("/estimasi", data={**base, "center": "2", "year": ""}).get_data(as_text=True)
if "wajib diisi" not in page:
    raise SystemExit("empty year accepted")

try:
    effort_model.validate({name: "" for name in effort_model.feature_names})
    raise SystemExit("empty form accepted")
except ValidationError:
    pass

comma_sample = {**base, "center": "2", "equivphyskloc": "177,9"}
value = effort_model.predict(effort_model.validate(comma_sample))
if abs(value - 595.9722943472086) > 1e-9:
    raise SystemExit(f"comma sample mismatch {value}")

history = client.get("/riwayat").get_data(as_text=True)
if "datacapture" not in history:
    raise SystemExit("history missing")

for row in database.list_predictions():
    client.post(f"/riwayat/{row['id']}/hapus")
if database.list_predictions():
    raise SystemExit("history was not deleted")

print("route checks passed")
print(effort_model.alpha, effort_model.l1_ratio, len(effort_model.feature_names))
print(effort_model.training_report["tuning_method"], effort_model.training_report["cv_score"])
