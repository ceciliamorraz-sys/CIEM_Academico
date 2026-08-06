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
    mensajes = []
    conversaciones = []

    rol = session.get("rol")
    usuario = session.get("usuario")


    if rol == "estudiante":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario
        })

        if estudiante:
            notas = list(
                db.notas.find({
                    "estudiante_id": estudiante.get("id")
                })
            )


    elif rol == "padre":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario
        })

        if estudiante:
            notas = list(
                db.notas.find({
                    "estudiante_id": estudiante.get("id")
                })
            )


        mensajes = list(
            db.mensajes.find({
                "padre": usuario
            }).sort("fecha", -1)
        )


        conversaciones = list(
            db.conversaciones.find({
                "padre": usuario
            }).sort("fecha", -1)
        )


    docentes = list(
        db.docentes.find()
    )


    return render_template(
        "estudiante/estudiante_dashboard.html",
        estudiante=estudiante,
        notas=notas,
        docentes=docentes,
        mensajes=mensajes,
        conversaciones=conversaciones
    )