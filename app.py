import os
import uuid
from datetime import datetime

from flask import (
    Flask, render_template, request, send_file,
    url_for, flash, redirect
)
from werkzeug.utils import secure_filename

from evaluacion_reba import analizar_postura
from generador_informe import generar_pdf


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "informes")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "reba-ergonomia-cambiar-en-produccion"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

RESULTADOS = {}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analizar", methods=["POST"])
def analizar():
    nombre = request.form.get("nombre", "").strip()
    edad = request.form.get("edad", "").strip()
    cargo = request.form.get("cargo", "").strip()
    area = request.form.get("area", "").strip()

    carga = request.form.get("carga", "ligera")
    acoplamiento = request.form.get("acoplamiento", "regular")
    actividad = request.form.get("actividad", "estatica")

    imagen = request.files.get("imagen")

    if not nombre or not cargo or not imagen or imagen.filename == "":
        flash(
            "Completa el nombre, el cargo y selecciona una fotografía.",
            "error"
        )
        return redirect(url_for("index"))

    if not allowed_file(imagen.filename):
        flash(
            "Formato no permitido. Utiliza JPG, JPEG, PNG o WEBP.",
            "error"
        )
        return redirect(url_for("index"))

    ext = secure_filename(imagen.filename).rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    image_path = os.path.join(UPLOAD_FOLDER, filename)
    imagen.save(image_path)

    try:
        resultado = analizar_postura(
            image_path,
            carga=carga,
            acoplamiento=acoplamiento,
            actividad=actividad
        )

    except Exception as exc:
        if os.path.exists(image_path):
            os.remove(image_path)

        flash(
            f"No fue posible procesar la fotografía: {exc}",
            "error"
        )
        return redirect(url_for("index"))

    resultado_id = uuid.uuid4().hex

    resultado.update({
        "id": resultado_id,
        "nombre": nombre,
        "edad": edad or "No indicada",
        "cargo": cargo,
        "area": area or "No indicada",
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "imagen": url_for(
            "static",
            filename=f"uploads/{filename}"
        ),
        "imagen_archivo": image_path,
        "imagen_analizada_url": url_for(
            "static",
            filename=(
                f"uploads/"
                f"{os.path.basename(resultado['imagen_analizada'])}"
            )
        )
    })

    RESULTADOS[resultado_id] = resultado

    return render_template("resultados.html", r=resultado)


@app.route("/informe/<resultado_id>")
def informe(resultado_id):
    resultado = RESULTADOS.get(resultado_id)

    if not resultado:
        flash(
            "La sesión de evaluación expiró. Realiza nuevamente el análisis.",
            "error"
        )
        return redirect(url_for("index"))

    pdf_path = os.path.join(
        REPORT_FOLDER,
        f"Informe_REBA_{resultado_id[:8]}.pdf"
    )

    generar_pdf(resultado, pdf_path)

    nombre_archivo = secure_filename(resultado["nombre"])

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"Informe_REBA_{nombre_archivo}.pdf"
    )


@app.errorhandler(413)
def demasiado_grande(_):
    flash(
        "La fotografía supera el límite de 12 MB.",
        "error"
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )