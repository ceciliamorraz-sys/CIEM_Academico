from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from config.database import db
from utils.decorators import role_required

estudiante_bp = Blueprint(
    "estudiante",
    __name__,
    url_prefix="/estudiante"
)


@estudiante_bp.route("/")
@role_required("estudiante","padre")
def dashboard():

    estudiante = db.estudiantes.find_one({
        "_id": session.get("id")
    })


    return render_template(
        "estudiante/estudiante_dashboard.html",
        estudiante=estudiante,
        resumen={
            "promedio":0,
            "asistencia":0
        }
    )
# =====================================
# NOTAS DEL ESTUDIANTE
# =====================================

@estudiante_bp.route("/notas")
@role_required("estudiante")
def notas():

    estudiante_id = session.get("id")


    estudiante = db.estudiantes.find_one({
        "_id": estudiante_id
    })


    if not estudiante:
        flash("Estudiante no encontrado", "danger")
        return redirect(
            url_for("estudiante.dashboard")
        )


    notas = list(
        db.notas.find({
            "estudiante_id": estudiante_id
        })
    )


    return render_template(
        "estudiante/notas.html",
        estudiante=estudiante,
        notas=notas
    )