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
@role_required("estudiante", "padre")
def dashboard():

    estudiante = None
    notas = []
    docentes = []
    conversaciones = []
    mensajes = []

    if session.get("rol") == "estudiante":

        estudiante = db.estudiantes.find_one({
            "_id": session.get("id")
        })

        if estudiante:
            notas = list(db.notas.find({
                "estudiante_id": session.get("id")
            }))

    elif session.get("rol") == "padre":

        mensajes = list(
            db.mensajes.find({
                "padre": session.get("usuario")
            }).sort("fecha", -1)
        )

    docentes = list(db.docentes.find())

    return render_template(
        "estudiante/estudiante_dashboard.html",
        estudiante=estudiante,
        notas=notas,
        docentes=docentes,
        conversaciones=conversaciones,
        mensajes=mensajes,
        resumen={
            "promedio": 0,
            "asistencia": 0,
            "estado": "Activo"
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