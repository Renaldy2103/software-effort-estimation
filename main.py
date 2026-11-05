from flask import Flask, flash, redirect, render_template, request, url_for

import database
from config import APP_NAME, APP_SUBTITLE, DEBUG, EFFORT_UNIT, HOST, PORT, SECRET_KEY
from model_service import ValidationError, effort_model

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
database.init_db()


def format_effort(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@app.context_processor
def inject_globals():
    return {
        "app_name": APP_NAME,
        "app_subtitle": APP_SUBTITLE,
        "effort_unit": EFFORT_UNIT,
        "format_effort": format_effort,
    }


@app.route("/")
def dashboard():
    estimator = effort_model.pipeline.named_steps["model"]
    return render_template(
        "dashboard.html",
        alpha=effort_model.alpha,
        l1_ratio=effort_model.l1_ratio,
        feature_count=len(effort_model.feature_names),
        training=effort_model.training_report,
        sklearn_version=effort_model.sklearn_version_trained,
        model_name=type(estimator).__name__,
    )


@app.route("/estimasi", methods=["GET", "POST"])
def estimate():
    submitted = {}
    if request.method == "POST":
        submitted = request.form.to_dict()
        try:
            cleaned = effort_model.validate(submitted)
            effort = effort_model.predict(cleaned)
            rows = effort_model.summarize(cleaned)
            prediction_id = database.save_prediction(cleaned, rows, effort)
            return redirect(url_for("result", prediction_id=prediction_id))
        except ValidationError as error:
            for message in error.messages:
                flash(message, "danger")
        except Exception:
            flash(
                "Estimasi tidak dapat dihitung. Periksa kembali isian karakteristik proyek.",
                "danger",
            )
    return render_template(
        "estimate.html",
        groups=effort_model.form_groups(submitted),
    )


@app.route("/hasil/<int:prediction_id>")
def result(prediction_id: int):
    prediction = database.get_prediction(prediction_id)
    if prediction is None:
        flash("Data hasil prediksi tidak ditemukan.", "warning")
        return redirect(url_for("history"))
    return render_template(
        "result.html",
        prediction=prediction,
        negative=prediction["effort"] < 0,
    )


@app.route("/riwayat")
def history():
    return render_template("history.html", predictions=database.list_predictions())


@app.route("/riwayat/<int:prediction_id>/hapus", methods=["POST"])
def delete_history(prediction_id: int):
    deleted = database.delete_prediction(prediction_id)
    flash(
        "Riwayat prediksi berhasil dihapus." if deleted else "Riwayat tidak ditemukan.",
        "success" if deleted else "warning",
    )
    return redirect(url_for("history"))


@app.route("/riwayat/hapus-semua", methods=["POST"])
def delete_all_history():
    database.delete_all_predictions()
    flash("Seluruh riwayat prediksi berhasil dihapus.", "success")
    return redirect(url_for("history"))


@app.route("/model")
def model_info():
    return render_template(
        "model_info.html",
        alpha=effort_model.alpha,
        l1_ratio=effort_model.l1_ratio,
        feature_count=len(effort_model.feature_names),
        training=effort_model.training_report,
        sklearn_version=effort_model.sklearn_version_trained,
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template(
        "error.html",
        title="Halaman tidak ditemukan",
        message="Halaman yang Anda buka tidak tersedia.",
    ), 404


@app.errorhandler(500)
def server_error(_error):
    return render_template(
        "error.html",
        title="Terjadi kesalahan",
        message="Permintaan tidak dapat diproses. Silakan coba lagi.",
    ), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
