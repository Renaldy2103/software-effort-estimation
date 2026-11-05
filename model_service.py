"""Memuat pipeline Elastic Net hasil training dan menjalankan prediksi.

Pipeline sudah berisi preprocessing. Aplikasi tidak melakukan fitting ulang
dan tidak menerapkan transformasi target karena artefak training memprediksi
act_effort langsung dalam person-months.
"""

import json
import math
import warnings
from pathlib import Path

import joblib
import pandas as pd
import sklearn.compose._column_transformer as column_transformer
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

from config import (
    CATEGORY_LABELS,
    FEATURE_GROUPS,
    FEATURE_HELP,
    FEATURE_LABELS,
    FEATURE_UNITS,
    MODEL_PATH,
    RATING_LABELS,
    RESULTS_DIR,
    SCHEMA_PATH,
)

# scikit-learn 1.6.1 menyimpan remainder column transformer sebagai
# _RemainderColsList. Kelas itu dihapus pada rilis yang lebih baru.
# Shim ini hanya memungkinkan unpickle; tidak mengubah koefisien atau data.
if not hasattr(column_transformer, "_RemainderColsList"):

    class _RemainderColsList(list):
        pass

    column_transformer._RemainderColsList = _RemainderColsList


class ValidationError(Exception):
    def __init__(self, messages):
        self.messages = list(messages)
        super().__init__("; ".join(self.messages))


def _load_schema(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict) or not schema:
        raise RuntimeError("Skema input model kosong atau tidak valid.")
    if "act_effort" in schema:
        raise RuntimeError("Skema input tidak boleh memuat target act_effort.")
    return schema


def _load_pipeline(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File model tidak ditemukan: {path}")
    pipeline = joblib.load(path)
    if not hasattr(pipeline, "predict") or not hasattr(pipeline, "named_steps"):
        raise RuntimeError("Artefak model bukan pipeline yang dapat melakukan prediksi.")
    if "preprocessing" not in pipeline.named_steps or "model" not in pipeline.named_steps:
        raise RuntimeError("Pipeline tidak memuat langkah preprocessing dan model.")
    return pipeline


def _read_csv_rows(path: Path) -> list[dict]:
    import csv

    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_training_report(results_dir: Path = RESULTS_DIR) -> dict:
    """Membaca konfigurasi yang benar-benar tertulis pada artefak training."""
    report = {
        "tuning_method": None,
        "cv_metric_name": None,
        "cv_score": None,
        "test_metrics": [],
    }
    grid_path = results_dir / "hasil_gridsearch.csv"
    if grid_path.exists():
        report["tuning_method"] = "Grid Search"
        rows = _read_csv_rows(grid_path)
        metric_name = "MAE CV" if rows and "MAE CV" in rows[0] else None
        if metric_name:
            scored = []
            for row in rows:
                try:
                    scored.append((float(row[metric_name]), row[metric_name]))
                except (TypeError, ValueError):
                    continue
            if scored:
                report["cv_metric_name"] = metric_name
                report["cv_score"] = f"{min(scored)[0]:.4f}"

    evaluation_path = results_dir / "hasil_evaluasi.csv"
    if evaluation_path.exists():
        metrics = []
        for row in _read_csv_rows(evaluation_path):
            name = (row.get("Metrik") or "").strip()
            value = (row.get("Nilai") or "").strip()
            if not name or name in {"Alpha Terbaik", "L1 Ratio Terbaik"}:
                continue
            metrics.append({"name": name, "value": value})
        report["test_metrics"] = metrics
    return report


class EffortModel:
    def __init__(self, model_path: Path = MODEL_PATH, schema_path: Path = SCHEMA_PATH):
        self.pipeline = _load_pipeline(model_path)
        self.schema = _load_schema(schema_path)
        self.feature_names = [str(name) for name in self.pipeline.feature_names_in_]
        missing = [name for name in self.feature_names if name not in self.schema]
        extra = [name for name in self.schema if name not in self.feature_names]
        if missing or extra:
            raise RuntimeError(
                "Skema input tidak sesuai dengan fitur pipeline. "
                f"Tidak ada di skema: {missing or '-'}; tidak ada di model: {extra or '-'}."
            )
        grouped = [field for group in FEATURE_GROUPS for field in group["fields"]]
        if set(grouped) != set(self.feature_names):
            raise RuntimeError("Pengelompokan form tidak sesuai dengan fitur model.")

        estimator = self.pipeline.named_steps["model"]
        self.alpha = float(estimator.alpha)
        self.l1_ratio = float(estimator.l1_ratio)
        self.training_report = load_training_report()
        self.sklearn_version_trained = "1.6.1"

    def form_groups(self, submitted: dict | None = None) -> list[dict]:
        submitted = submitted or {}
        groups = []
        for group in FEATURE_GROUPS:
            fields = []
            for key in group["fields"]:
                spec = self.schema[key]
                raw_value = submitted.get(key, "")
                field = {
                    "key": key,
                    "label": FEATURE_LABELS.get(key, key),
                    "help": FEATURE_HELP.get(key, ""),
                    "unit": FEATURE_UNITS.get(key),
                    "type": spec["type"],
                    "value": "" if raw_value is None else str(raw_value),
                }
                if spec["type"] == "category":
                    field["options"] = [
                        {"value": option, "label": self.option_label(key, option)}
                        for option in spec["options"]
                    ]
                fields.append(field)
            groups.append(
                {
                    "id": group["id"],
                    "title": group["title"],
                    "description": group["description"],
                    "fields": fields,
                }
            )
        return groups

    def option_label(self, feature: str, value: str) -> str:
        if feature in CATEGORY_LABELS and value in CATEGORY_LABELS[feature]:
            return CATEGORY_LABELS[feature][value]
        if value in RATING_LABELS:
            return RATING_LABELS[value]
        return value

    def validate(self, form: dict) -> dict:
        messages = []
        cleaned = {}
        for name in self.feature_names:
            spec = self.schema[name]
            label = FEATURE_LABELS.get(name, name)
            raw = form.get(name, "")
            if raw is None:
                raw = ""
            raw = str(raw).strip()
            if raw == "":
                messages.append(f"{label} wajib diisi.")
                continue
            if spec["type"] == "number":
                numeric_text = raw.replace(" ", "")
                if "," in numeric_text and "." not in numeric_text:
                    numeric_text = numeric_text.replace(",", ".")
                try:
                    value = float(numeric_text)
                except (TypeError, ValueError):
                    messages.append(f"{label} harus berupa angka yang valid.")
                    continue
                if not math.isfinite(value):
                    messages.append(f"{label} tidak boleh kosong, NaN, atau tak hingga.")
                    continue
                if name == "equivphyskloc" and value <= 0:
                    messages.append("Ukuran kode harus lebih besar dari 0 KLOC.")
                    continue
                cleaned[name] = value
            elif spec["type"] == "category":
                allowed = [str(option) for option in spec["options"]]
                if raw not in allowed:
                    messages.append(f"{label} tidak termasuk kategori yang dikenali model.")
                    continue
                cleaned[name] = raw
            else:
                messages.append(f"Tipe fitur {label} tidak dikenali.")
        if messages:
            raise ValidationError(messages)
        return cleaned

    def predict(self, cleaned: dict) -> float:
        frame = pd.DataFrame([{name: cleaned[name] for name in self.feature_names}])
        for name in self.feature_names:
            if self.schema[name]["type"] == "category":
                frame[name] = frame[name].astype(str)
            else:
                frame[name] = frame[name].astype(float)
        frame = frame.loc[:, self.feature_names]
        try:
            prediction = self.pipeline.predict(frame)
        except Exception as exc:
            raise RuntimeError("Model tidak dapat menyelesaikan prediksi.") from exc
        value = float(prediction[0])
        if not math.isfinite(value):
            raise RuntimeError("Model menghasilkan nilai prediksi yang tidak valid.")
        return value

    def summarize(self, cleaned: dict) -> list[dict]:
        rows = []
        for name in self.feature_names:
            value = cleaned[name]
            if self.schema[name]["type"] == "category":
                display = self.option_label(name, str(value))
            elif name == "equivphyskloc":
                display = f"{_format_number(value)} KLOC"
            elif name == "year":
                display = str(int(value)) if float(value).is_integer() else _format_number(value)
            else:
                display = _format_number(value)
            rows.append(
                {
                    "key": name,
                    "label": FEATURE_LABELS.get(name, name),
                    "display": display,
                    "group": next(
                        group["title"]
                        for group in FEATURE_GROUPS
                        if name in group["fields"]
                    ),
                }
            )
        return rows


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value:.4g}"


effort_model = EffortModel()
