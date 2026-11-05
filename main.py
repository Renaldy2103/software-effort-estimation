import html
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import (
    APP_NAME,
    APP_SUBTITLE,
    EFFORT_UNIT,
    FEATURE_GROUPS,
    FEATURE_HELP,
    FEATURE_LABELS,
    FEATURE_UNITS,
)
from model_service import ValidationError, effort_model
import database

try:
    from config import PERSON_MONTH_HOURS
except ImportError:
    PERSON_MONTH_HOURS = 152

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")
database.init_db()

PAGES = ["Dashboard", "Estimasi Effort", "Riwayat Prediksi", "Informasi Model"]

# ---------------------------------------------------------------- styling
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --blue-700: #1d5fa8;
        --blue-500: #2f80d1;
        --blue-100: #e3f0fc;
        --blue-50: #f0f7fd;
        --line: #d3e5f5;
        --text: #1e2f43;
        --muted: #5b6b7f;
        --white: #ffffff;
    }

    /* ---------- paksa tampilan terang, abaikan tema gelap browser ---------- */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"],
    [data-testid="stBottom"] {
        background: var(--white) !important;
    }
    .stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp span, .stApp small, .stApp [data-testid="stMarkdownContainer"] {
        color: var(--text) !important;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    .stApp td, .stApp th, .stApp input, .stApp select, .stApp textarea, .stApp button {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    /* ikon tetap memakai font ikonnya */
    .material-symbols-rounded, .material-icons, [data-testid="stIconMaterial"],
    [data-testid="stExpanderToggleIcon"], span[translate="no"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }

    #MainMenu, footer, [data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }

    .block-container { max-width: 1180px; padding-top: 2.5rem; padding-bottom: 3rem; }

    /* ---------- header halaman ---------- */
    .app-header {
        background: var(--blue-50); border: 1px solid var(--line); border-left: 4px solid var(--blue-500);
        border-radius: 8px; padding: 1.4rem 1.6rem; margin-bottom: 1.75rem;
    }
    .stApp .app-header h1 { color: var(--blue-700) !important; font-size: 1.7rem; font-weight: 700; margin: 0 0 .3rem 0; padding: 0; }
    .stApp .app-header p { color: var(--muted) !important; font-size: .98rem; margin: 0; max-width: 760px; line-height: 1.55; }

    .stApp .sec-title { color: var(--blue-700) !important; font-size: 1.08rem; font-weight: 600; margin: 0 0 .25rem 0; }
    .stApp .sec-desc { color: var(--muted) !important; font-size: .92rem; margin: 0 0 1rem 0; line-height: 1.5; }

    /* ---------- kartu, expander, input ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] { background: var(--white); }
    [data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 8px !important; background: var(--white); }
    [data-testid="stExpander"] summary { background: var(--blue-50) !important; border-radius: 8px; }
    [data-testid="stExpander"] summary p { color: var(--blue-700) !important; font-weight: 600; }
    [data-testid="stExpanderDetails"] { background: var(--white) !important; }
    [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }

    [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"],
    [data-testid="stNumberInput"] [data-baseweb="input"] {
        background: var(--white) !important; border-color: var(--line) !important; border-radius: 8px !important;
    }
    [data-baseweb="select"] *, [data-baseweb="input"] input, [data-testid="stNumberInput"] input {
        color: var(--text) !important; background: transparent !important;
    }
    [data-baseweb="select"] svg { fill: var(--blue-700) !important; }
    [data-testid="stNumberInput"] button { background: var(--blue-50) !important; color: var(--blue-700) !important; }
    [data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul { background: var(--white) !important; }
    [data-baseweb="popover"] li, [data-baseweb="popover"] li * { color: var(--text) !important; background: var(--white) !important; }
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {
        background: var(--blue-100) !important;
    }
    [data-testid="stTextInput"] input, [data-testid="stCheckbox"] label { color: var(--text) !important; }

    /* ---------- selectbox & number input: semua lapisan dipaksa terang ---------- */
    .stApp [data-testid="stSelectbox"] *:not(svg):not(path),
    .stApp [data-testid="stNumberInput"] *:not(svg):not(path) {
        background-color: var(--white) !important;
        color: var(--text) !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    .stApp [data-testid="stNumberInput"] [data-baseweb="input"] {
        border: 1px solid var(--line) !important;
        border-radius: 8px !important;
    }
    .stApp [data-testid="stNumberInput"] input {
        background-color: var(--white) !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--blue-700);
    }
    .stApp [data-testid="stNumberInput"] input::placeholder,
    .stApp [data-testid="stSelectbox"] input::placeholder {
        color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; opacity: 1 !important;
    }
    .stApp [data-testid="stNumberInput"] button {
        background-color: var(--blue-50) !important;
        color: var(--blue-700) !important;
        border-left: 1px solid var(--line) !important;
    }
    .stApp [data-testid="stNumberInput"] button svg { fill: var(--blue-700) !important; }
    .stApp [data-testid="stSelectbox"] svg { fill: var(--blue-700) !important; }

    /* ---------- metrik ---------- */
    div[data-testid="stMetric"] {
        background: var(--blue-50); border: 1px solid var(--line); border-radius: 8px; padding: .9rem 1.1rem;
    }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * { color: var(--muted) !important; font-size: .85rem; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * { color: var(--blue-700) !important; font-weight: 600; }

    /* ---------- tombol utama ---------- */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        width: 100%; border-radius: 8px; font-weight: 500; border: 1px solid var(--line);
        background: var(--white); color: var(--blue-700) !important;
    }
    .stButton > button p, div[data-testid="stFormSubmitButton"] > button p { color: var(--blue-700) !important; }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        border-color: var(--blue-500); background: var(--blue-50);
    }
    .stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: var(--blue-500) !important; border-color: var(--blue-500) !important;
    }
    .stButton > button[kind="primary"] p, div[data-testid="stFormSubmitButton"] > button[kind="primary"] p,
    .stButton > button[data-testid="stBaseButton-primary"] p { color: var(--white) !important; }
    .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: var(--blue-700) !important; border-color: var(--blue-700) !important;
    }

    /* ---------- tabel HTML (dirender di dalam komponen) ---------- */
    .tbl-note { color: var(--muted); font-size: .85rem; }

    /* ---------- sidebar ---------- */
    section[data-testid="stSidebar"] { background: var(--blue-50) !important; border-right: 1px solid var(--line); }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

    .stApp .brand { padding: .25rem .25rem 1rem .25rem; border-bottom: 1px solid var(--line); margin-bottom: 1rem; }
    .stApp .brand-name { color: var(--blue-700) !important; font-size: 1.05rem; font-weight: 700; line-height: 1.3; }
    .stApp .brand-sub { color: var(--muted) !important; font-size: .8rem; line-height: 1.45; margin-top: .35rem; }
    .stApp .nav-label { color: var(--muted) !important; font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; margin: 0 .25rem .5rem .25rem; }

    section[data-testid="stSidebar"] .stButton { margin-bottom: .3rem; }
    section[data-testid="stSidebar"] .stButton > button {
        justify-content: flex-start; text-align: left; box-shadow: none;
        background: transparent !important; border: 1px solid transparent !important;
        min-height: 2.6rem; padding: .55rem .9rem;
    }
    section[data-testid="stSidebar"] .stButton > button p {
        color: #33475b !important; font-size: .95rem; font-weight: 500; margin: 0; text-align: left; width: 100%;
    }
    section[data-testid="stSidebar"] .stButton > button:hover { background: var(--blue-100) !important; border-color: transparent !important; }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
        background: var(--white) !important; border-color: var(--line) !important;
        box-shadow: inset 3px 0 0 var(--blue-500);
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] p {
        color: var(--blue-700) !important; font-weight: 600;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: var(--white) !important;
    }

    .stApp .side-note {
        margin-top: 1.5rem; padding: .7rem .9rem; background: var(--white); border: 1px solid var(--line);
        border-radius: 8px; color: var(--muted) !important; font-size: .82rem; line-height: 1.5;
    }
    .stApp .side-note b { color: var(--text) !important; font-weight: 600; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- state
for key, default in {"prediction_id": None, "show_result": False, "form_version": 0, "current_page": PAGES[0]}.items():
    st.session_state.setdefault(key, default)


def reset_form():
    st.session_state.form_version += 1  # key baru = semua input kembali kosong
    st.session_state.prediction_id = None
    st.session_state.show_result = False


def close_result():
    st.session_state.show_result = False


# ---------------------------------------------------------------- helpers
def format_effort(value: float) -> str:
    """Format angka gaya Indonesia: 1.234,56"""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def section(title: str, desc: str | None = None):
    st.markdown(f"<p class='sec-title'>{title}</p>", unsafe_allow_html=True)
    if desc:
        st.markdown(f"<p class='sec-desc'>{desc}</p>", unsafe_allow_html=True)


def show_table(df: pd.DataFrame):
    """Tabel HTML di dalam komponen terisolasi, sehingga tidak terpengaruh CSS Streamlit."""
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row) + "</tr>"
        for row in df.itertuples(index=False)
    )
    doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');"
        "body{margin:0;background:transparent;font-family:Inter,'Segoe UI',system-ui,sans-serif;color:#1e2f43;}"
        ".wrap{border:1px solid #d3e5f5;border-radius:8px;overflow:auto;background:#fff;}"
        "table{width:100%;border-collapse:collapse;font-size:14px;}"
        "th{background:#e3f0fc;color:#1d5fa8;font-weight:600;text-align:left;padding:10px 14px;"
        "border-bottom:1px solid #d3e5f5;white-space:nowrap;}"
        "td{padding:9px 14px;border-bottom:1px solid #eef5fb;vertical-align:top;}"
        "tbody tr:nth-child(even) td{background:#f0f7fd;}"
        "tbody tr:last-child td{border-bottom:none;}"
        "</style></head><body><div class='wrap'><table>"
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody>"
        "</table></div></body></html>"
    )
    height = min(520, 60 + len(df) * 42)
    components.html(doc, height=height, scrolling=True)


def show_json(data) -> None:
    """JSON ditampilkan sebagai teks terang di komponen terisolasi, tidak terpengaruh tema gelap."""
    text = html.escape(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "body{margin:0;background:transparent;}"
        "pre{margin:0;padding:14px 16px;background:#f0f7fd;color:#1e2f43;border:1px solid #d3e5f5;"
        "border-radius:8px;font-family:'Consolas','Menlo',monospace;font-size:13px;line-height:1.5;"
        "white-space:pre-wrap;word-break:break-word;}"
        "</style></head><body><pre>" + text + "</pre></body></html>"
    )
    height = min(520, 60 + text.count("\n") * 20)
    components.html(doc, height=height, scrolling=True)


@st.cache_resource
def load_model():
    return effort_model


model = load_model()


def render_result(prediction_id: int, closable: bool = False):
    prediction = database.get_prediction(prediction_id)
    if not prediction:
        st.warning("Data prediksi tidak ditemukan.")
        return

    effort = prediction["effort"]
    unit = prediction.get("unit", EFFORT_UNIT)

    with st.container(border=True):
        section("Hasil Estimasi", f"ID prediksi {prediction['id']}, dihitung pada {prediction['created_at']}.")
        if prediction.get("summary"):
            st.write(prediction["summary"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Effort estimasi", f"{format_effort(effort)} {unit}")
        c2.metric("Setara jam kerja", f"{format_effort(effort * PERSON_MONTH_HOURS)} jam")
        c3.metric("Status", "Valid" if effort >= 0 else "Perlu ditinjau")

        if effort < 0:
            st.warning("Model menghasilkan effort negatif. Periksa kembali nilai input, terutama ukuran proyek.")

        st.markdown("**Rincian input**")
        rows = pd.DataFrame(prediction["rows"])
        rows = rows.rename(columns={"label": "Fitur", "display": "Nilai", "group": "Kelompok"})
        show_table(rows[[c for c in ["Kelompok", "Fitur", "Nilai"] if c in rows.columns]])

        with st.expander("Data input mentah"):
            show_json(prediction["input"])

        if closable:
            st.button("Tutup hasil", on_click=close_result, key="close_result")


# ---------------------------------------------------------------- sidebar
def go_to(name: str):
    st.session_state.current_page = name


with st.sidebar:
    st.markdown(
        f"<div class='brand'><div class='brand-name'>{APP_NAME}</div>"
        f"<div class='brand-sub'>{APP_SUBTITLE}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='nav-label'>Menu</div>", unsafe_allow_html=True)
    for name in PAGES:
        active = st.session_state.current_page == name
        st.button(
            name,
            key=f"nav_{name}",
            type="primary" if active else "secondary",
            on_click=go_to,
            args=(name,),
        )
    st.markdown(
        f"<div class='side-note'><b>Satuan effort</b><br>{EFFORT_UNIT}</div>",
        unsafe_allow_html=True,
    )

page = st.session_state.current_page

# ---------------------------------------------------------------- header
st.markdown(
    f"<div class='app-header'><h1>{APP_NAME}</h1><p>{APP_SUBTITLE}</p></div>",
    unsafe_allow_html=True,
)

# ================================================================ Dashboard
if page == "Dashboard":
    with st.container(border=True):
        section(
            "Ringkasan Model",
            "Model Elastic Net Regression untuk mengestimasi effort pengembangan perangkat lunak "
            "berdasarkan karakteristik proyek pada dataset NASA93.",
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Alpha", f"{model.alpha:.4f}")
        c2.metric("L1 ratio", f"{model.l1_ratio:.4f}")
        c3.metric("Jumlah fitur", len(model.feature_names))

    training = model.training_report
    with st.container(border=True):
        section("Hasil Pelatihan")
        if training.get("tuning_method"):
            c1, c2 = st.columns(2)
            c1.metric("Metode tuning", training["tuning_method"])
            if training.get("cv_metric_name") and training.get("cv_score") is not None:
                c2.metric(f"Skor CV ({training['cv_metric_name']})", training["cv_score"])
        if training.get("test_metrics"):
            st.markdown("**Metrik evaluasi pada data uji**")
            show_table(
                pd.DataFrame(training["test_metrics"]).rename(columns={"name": "Metrik", "value": "Nilai"})
            )
        if not training.get("tuning_method") and not training.get("test_metrics"):
            st.info("Laporan pelatihan tidak tersedia.")

    estimator = model.pipeline.named_steps["model"]
    with st.container(border=True):
        section("Informasi Teknis")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Model:** {type(estimator).__name__}")
            st.markdown(f"**Versi scikit-learn:** {model.sklearn_version_trained}")
        with c2:
            st.markdown("**Data latih:** 93 proyek (NASA93)")
            st.markdown("**Target:** act_effort (person-months)")

# ================================================================ Estimasi
elif page == "Estimasi Effort":
    ver = st.session_state.form_version

    with st.form("estimation_form"):
        section("Karakteristik Proyek", "Lengkapi isian berikut, lalu pilih Hitung estimasi.")
        values = {}

        for group in FEATURE_GROUPS:
            with st.expander(group["title"], expanded=True):
                st.caption(group["description"])
                cols = st.columns(2)

                for i, field_key in enumerate(group["fields"]):
                    spec = model.schema[field_key]
                    label = FEATURE_LABELS.get(field_key, field_key)
                    unit = FEATURE_UNITS.get(field_key)
                    display_label = f"{label} ({unit})" if unit else label
                    help_text = FEATURE_HELP.get(field_key, "")
                    widget_key = f"in_{ver}_{field_key}"

                    with cols[i % 2]:
                        if spec["type"] == "category":
                            values[field_key] = st.selectbox(
                                display_label,
                                options=spec["options"],
                                format_func=lambda opt, k=field_key: model.option_label(k, str(opt)),
                                help=help_text,
                                key=widget_key,
                            )
                        else:
                            raw = st.number_input(
                                display_label,
                                value=None,
                                step=0.1,
                                min_value=0.0001 if field_key == "equivphyskloc" else None,
                                placeholder="Isi nilai",
                                help=help_text,
                                key=widget_key,
                            )
                            values[field_key] = "" if raw is None else str(raw)

        b1, b2, b3 = st.columns(3)
        submit = b1.form_submit_button("Hitung estimasi", type="primary")
        preview = b2.form_submit_button("Pratinjau input")
        b3.form_submit_button("Kosongkan form", on_click=reset_form)

    if submit:
        try:
            with st.spinner("Menghitung estimasi..."):
                cleaned = model.validate(values)
                effort = model.predict(cleaned)
                rows = model.summarize(cleaned)
                st.session_state.prediction_id = database.save_prediction(cleaned, rows, effort)
            st.session_state.show_result = True
        except ValidationError as error:
            st.session_state.show_result = False
            for message in error.messages:
                st.error(message)
        except Exception as exc:
            st.session_state.show_result = False
            st.error("Estimasi tidak dapat dihitung. Periksa kembali isian karakteristik proyek.")
            with st.expander("Detail teknis"):
                st.code(repr(exc))

    if preview:
        filled = [{"Fitur": FEATURE_LABELS.get(k, k), "Nilai": v} for k, v in values.items() if v != ""]
        with st.container(border=True):
            section("Pratinjau Input")
            if filled:
                show_table(pd.DataFrame(filled))
            else:
                st.info("Belum ada isian yang terisi.")

    if st.session_state.show_result and st.session_state.prediction_id is not None:
        render_result(st.session_state.prediction_id, closable=True)

# ================================================================ Riwayat
elif page == "Riwayat Prediksi":
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    predictions = database.list_predictions()

    if not predictions:
        st.info("Belum ada riwayat prediksi. Buat estimasi pertama melalui menu Estimasi Effort.")
    else:
        df = pd.DataFrame(predictions)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at", ascending=False)
        valid = df[df["effort"] >= 0]

        with st.container(border=True):
            section("Ringkasan Riwayat")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total prediksi", len(df))
            c2.metric("Rata-rata effort", f"{format_effort(valid['effort'].mean() if len(valid) else 0)} {EFFORT_UNIT}")
            c3.metric("Effort tertinggi", f"{format_effort(valid['effort'].max() if len(valid) else 0)} {EFFORT_UNIT}")

        with st.container(border=True):
            section("Daftar Prediksi")
            table = pd.DataFrame(
                {
                    "ID": df["id"],
                    "Waktu": df["created_at"].dt.strftime("%d-%m-%Y %H:%M"),
                    "Ringkasan": df["summary"],
                    "Effort": df["effort"].apply(lambda x: f"{format_effort(x)} {EFFORT_UNIT}"),
                }
            )
            show_table(table)

        labels = {
            int(r.id): f"ID {int(r.id)}  ({r.created_at:%d-%m-%Y %H:%M})" for r in df.itertuples()
        }
        ids = list(labels)

        with st.container(border=True):
            section("Lihat Detail")
            selected = st.selectbox("Pilih prediksi", ids, format_func=labels.get, key="detail_id")
        render_result(selected)

        with st.container(border=True):
            section("Hapus Riwayat", "Penghapusan bersifat permanen.")
            c1, c2 = st.columns(2)
            with c1:
                target = st.selectbox("Prediksi yang dihapus", ids, format_func=labels.get, key="delete_id")
                if st.button("Hapus prediksi terpilih"):
                    if database.delete_prediction(int(target)):
                        if st.session_state.prediction_id == target:
                            st.session_state.prediction_id = None
                            st.session_state.show_result = False
                        st.session_state.flash = f"Prediksi ID {target} dihapus."
                        st.rerun()
                    else:
                        st.warning("Data tidak ditemukan.")
            with c2:
                confirm = st.checkbox("Saya yakin ingin menghapus seluruh riwayat", key="confirm_all")
                if st.button("Hapus semua riwayat", disabled=not confirm):
                    count = database.delete_all_predictions()
                    st.session_state.prediction_id = None
                    st.session_state.show_result = False
                    st.session_state.flash = f"{count} data riwayat dihapus."
                    st.rerun()

# ================================================================ Informasi Model
elif page == "Informasi Model":
    with st.container(border=True):
        section(
            "Elastic Net Regression",
            "Elastic Net menggabungkan regularisasi L1 (Lasso) dan L2 (Ridge) untuk menangani "
            "multikolinearitas sekaligus melakukan seleksi fitur.",
        )
        st.latex(
            r"\min_{w}\ \frac{1}{2n}\lVert y - Xw \rVert_2^2 "
            r"+ \alpha\rho \lVert w \rVert_1 "
            r"+ \frac{\alpha(1-\rho)}{2}\lVert w \rVert_2^2"
        )
        st.caption("Keterangan: alpha adalah kekuatan regularisasi, rho adalah L1 ratio.")

    with st.container(border=True):
        section("Fitur yang Digunakan")
        show_table(
            pd.DataFrame(
                [
                    {"Kode": name, "Label": FEATURE_LABELS.get(name, name), "Tipe": model.schema[name]["type"]}
                    for name in model.feature_names
                ]
            )
        )

    with st.container(border=True):
        section("Pengelompokan Fitur")
        for group in FEATURE_GROUPS:
            with st.expander(group["title"]):
                st.caption(group["description"])
                for field in group["fields"]:
                    st.markdown(f"- {FEATURE_LABELS.get(field, field)} (`{field}`)")

    with st.expander("Skema input (JSON)"):
        show_json(model.schema)

st.divider()
st.caption(f"{APP_NAME}. {APP_SUBTITLE}")