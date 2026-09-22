from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
    jsonify
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from weasyprint import HTML

from io import BytesIO
from datetime import datetime
from bson import ObjectId
from functools import wraps

import os
import re
import random

from config.database import db

# ==========================================================
# GENERAR USUARIOS DE DOCENTES AUTOMÁTICAMENTE
#
# Por cada docente registrado en la colección "docentes" que
# todavía no tenga un usuario de acceso, se crea uno en
# "usuarios" siguiendo el mismo formato que ya usabas:
#
#   _id:        "USR" + los dígitos del código (DOC007 -> USR007)
#   usuario:    el que ya tenga guardado el docente, o su
#               primer nombre en minúscula sin acentos
#   password:   "1234" (por defecto, se puede cambiar luego)
#   rol:        "docente"
#   docente_id: el código del docente (ej. "DOC007")
#   activo:     True
#
# Si el docente ya tiene un usuario (docente_id ya existe en
# "usuarios"), NO se toca ni se sobreescribe.
# ==========================================================

import unicodedata as _unicodedata


def _quitar_acentos(texto):

    if not texto:
        return ""

    texto = _unicodedata.normalize(
        "NFKD",
        texto
    )

    return "".join(
        c for c in texto
        if not _unicodedata.combining(c)
    )


_docentes_nuevos_con_usuario = 0

for _docente in db.docentes.find({}):

    _codigo = str(
        _docente.get("codigo", "")
    ).strip().upper()

    if not _codigo:


        continue


    # ======================================================
    # SI YA TIENE USUARIO, NO SE TOCA
    # ======================================================

    _usuario_existente = db.usuarios.find_one({
        "docente_id": _codigo
    })

    if _usuario_existente:
        continue

    # ======================================================
    # EVITAR COLISIÓN DE NOMBRE DE USUARIO
    #
    # SI YA EXISTE UNA CUENTA (POR EJEMPLO DE ADMIN) CON ESE
    # MISMO "usuario", NO SE CREA UNA SEGUNDA CUENTA DE
    # DOCENTE CON EL MISMO NOMBRE DE LOGIN — CAUSARÍA QUE EL
    # LOGIN ENCUENTRE LA CUENTA EQUIVOCADA.
    # ======================================================

    _usuario_login_check = str(
        _docente.get("usuario", "")
    ).strip().lower()

    if not _usuario_login_check:

        _primer_nombre_check = str(
            _docente.get("nombre", "")
        ).strip().split(" ")[0]

        _usuario_login_check = _quitar_acentos(
            _primer_nombre_check
        ).lower()

    if _usuario_login_check:

        _colision = db.usuarios.find_one({
            "usuario": _usuario_login_check
        })

        if _colision:
            continue


    # ======================================================
    # ID DEL USUARIO A PARTIR DEL CÓDIGO DEL DOCENTE
    # ======================================================

    if _codigo.startswith("DOC"):
        _usr_id = "USR" + _codigo[3:]
    else:
        _usr_id = "USR_" + _codigo


    # ======================================================
    # NOMBRE DE USUARIO
    #
    # SE USA EL QUE YA TENGA GUARDADO EL DOCENTE.
    # SI NO TIENE, SE GENERA DE SU PRIMER NOMBRE.
    # ======================================================

    _usuario_login = str(
        _docente.get("usuario", "")
    ).strip().lower()

    if not _usuario_login:

        _primer_nombre = str(
            _docente.get("nombre", "")
        ).strip().split(" ")[0]

        _usuario_login = _quitar_acentos(
            _primer_nombre
        ).lower()

    if not _usuario_login:
        _usuario_login = _codigo.lower()


    _nuevo_usuario_docente = {
        "_id": _usr_id,
        "usuario": _usuario_login,
        "password": "1234",
        "rol": "docente",
        "docente_id": _codigo,
        "activo": True
    }

    db.usuarios.update_one(
        {"_id": _usr_id},
        {"$set": _nuevo_usuario_docente},
        upsert=True
    )

    _docentes_nuevos_con_usuario += 1


if _docentes_nuevos_con_usuario:

    pass

else:

    pass


# ==========================================================
# USUARIOS ADMINISTRADORES
#
# HOBETH, GUISSELL Y DARLING ENTRAN COMO ADMIN.
#
# SI EL USUARIO YA EXISTE, SOLO SE ASEGURA SU ROL Y QUE
# ESTÉ ACTIVO — NO SE TOCA SU CONTRASEÑA (POR SI YA LA
# CAMBIARON). SI NO EXISTE, SE CREA CON LA CONTRASEÑA
# POR DEFECTO "1234".
# ==========================================================

usuarios_administradores = [
    {
        "_id": "USR_HOBETH",
        "usuario": "hobeth",
        "password": "1234",
        "rol": "admin",
        "activo": True
    },
    {
        "_id": "USR_GUISSELL",
        "usuario": "guissell",
        "password": "1234",
        "rol": "admin",
        "activo": True
    },
    {
        "_id": "USR_DARLING",
        "usuario": "darling",
        "password": "1234",
        "rol": "admin",
        "activo": True
    }
]

for _usuario_admin in usuarios_administradores:

    _existente_admin = db.usuarios.find_one({
        "_id": _usuario_admin["_id"]
    })

    if _existente_admin:

        db.usuarios.update_one(
            {
                "_id": _usuario_admin["_id"]
            },
            {
                "$set": {
                    "usuario": _usuario_admin["usuario"],
                    "rol": "admin",
                    "activo": True
                }
            }
        )

    else:

        db.usuarios.insert_one(
            _usuario_admin
        )


# ==========================================================
# LIMPIEZA: CUENTAS DUPLICADAS DE LOS ADMINISTRADORES
#
# SI HOBETH, GUISSELL O DARLING TAMBIÉN QUEDARON REGISTRADAS
# COMO DOCENTES (CON OTRO _id), ESA CUENTA DUPLICADA SE
# DESACTIVA PARA QUE EL LOGIN SIEMPRE ENCUENTRE LA CUENTA DE
# ADMIN Y NO LA DE DOCENTE. NO SE ELIMINA, SOLO SE INACTIVA.
# ==========================================================

for _usuario_admin in usuarios_administradores:

    db.usuarios.update_many(
        {
            "usuario": _usuario_admin["usuario"],
            "_id": {"$ne": _usuario_admin["_id"]}
        },
        {
            "$set": {
                "activo": False
            }
        }
    )


# ==========================================================
# APLICACIÓN
# ==========================================================

app = Flask(__name__)

app.secret_key = "CIEM_clave_segura_2026"


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form.get(
            "usuario",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # --------------------------------------------------
        # VALIDAR DATOS
        # --------------------------------------------------

        if not usuario or not password:

            flash(
                "Debe ingresar usuario y contraseña.",
                "warning"
            )

            return render_template("login.html")

        # --------------------------------------------------
        # BUSCAR USUARIO
        # --------------------------------------------------

        # --------------------------------------------------
        # SE BUSCA PRIMERO ENTRE CUENTAS ACTIVAS. SI HAY MÁS
        # DE UNA CUENTA CON EL MISMO "usuario" (CASO DUPLICADO
        # DOCENTE/ADMIN), ESTO ASEGURA QUE SE USE LA ACTIVA.
        # --------------------------------------------------

        user = db["usuarios"].find_one({
            "usuario": usuario,
            "activo": {"$ne": False}
        })

        # --------------------------------------------------
        # BUSCAR SIN IMPORTAR MAYÚSCULAS (SOLO ACTIVAS)
        # --------------------------------------------------

        if user is None:

            user = db["usuarios"].find_one({
                "usuario": {
                    "$regex": "^" + re.escape(usuario) + "$",
                    "$options": "i"
                },
                "activo": {"$ne": False}
            })

        # --------------------------------------------------
        # SI NO HAY NINGUNA CUENTA ACTIVA, SE BUSCA CUALQUIERA
        # PARA PODER MOSTRAR EL MENSAJE CORRECTO ("inactivo"
        # EN VEZ DE "no encontrado")
        # --------------------------------------------------

        if user is None:

            user = db["usuarios"].find_one({
                "usuario": {
                    "$regex": "^" + re.escape(usuario) + "$",
                    "$options": "i"
                }
            })

        # --------------------------------------------------
        # USUARIO NO ENCONTRADO
        # --------------------------------------------------

        if user is None:

            flash(
                "Usuario no encontrado.",
                "danger"
            )

            return render_template("login.html")

        # --------------------------------------------------
        # USUARIO INACTIVO
        # --------------------------------------------------

        if user.get("activo") is False:

            flash(
                "El usuario está inactivo.",
                "danger"
            )

            return render_template("login.html")

        # --------------------------------------------------
        # CONTRASEÑA
        # --------------------------------------------------

        password_bd = str(
            user.get(
                "password",
                ""
            )
        ).strip()

        if password_bd != password:

            flash(
                "Contraseña incorrecta.",
                "danger"
            )

            return render_template("login.html")

        # ==================================================
        # LIMPIAR SESIÓN
        # ==================================================

        session.clear()

        # ==================================================
        # DATOS DEL USUARIO
        # ==================================================

        session["usuario"] = user.get(
            "usuario"
        )

        session["rol"] = str(
            user.get(
                "rol",
                ""
            )
        ).strip().lower()

        session["id"] = str(
            user.get(
                "_id",
                ""
            )
        )

        # ==================================================
        # DOCENTE
        # ==================================================

        if session["rol"] == "docente":

            docente_id = user.get(
                "docente_id"
            )

            if not docente_id:

                session.clear()

                flash(
                    "El usuario docente no tiene docente_id asociado.",
                    "danger"
                )

                return render_template(
                    "login.html"
                )

            docente_id = str(
                docente_id
            ).strip().upper()

            # 007 -> DOC007
            if not docente_id.startswith("DOC"):

                docente_id = (
                    "DOC"
                    + docente_id.zfill(3)
                )

            session["docente_id"] = docente_id


            return redirect(
                url_for(
                    "docente.dashboard_docente"
                )
            )

        # ==================================================
        # ADMIN
        # ==================================================

        elif session["rol"] == "admin":

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        # ==================================================
        # SECRETARIA
        # ==================================================

        elif session["rol"] == "secretaria":

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        # ==================================================
        # DIRECTOR
        # ==================================================

        elif session["rol"] == "director":

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        # ==================================================
        # CONTADORA
        # ==================================================

        elif session["rol"] == "contadora":

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        # ==================================================
        # ESTUDIANTE
        # ==================================================

        elif session["rol"] == "estudiante":

            return redirect(
                url_for(
                    "estudiante.dashboard"
                )
            )

        # ==================================================
        # PADRE
        # ==================================================

        elif session["rol"] == "padre":

            return redirect(
                url_for(
                    "estudiante.dashboard"
                )
            )

        # ==================================================
        # ROL NO VÁLIDO
        # ==================================================

        session.clear()

        flash(
            "Rol no válido.",
            "danger"
        )

        return render_template(
            "login.html"
        )

    # ======================================================
    # MOSTRAR LOGIN
    # ======================================================

    return render_template(
        "login.html"
    )


# ==========================================================
# BLUEPRINTS
# ==========================================================

from routes.docentes import docente_bp
from routes.estudiante import estudiante_bp
from routes.mensajes import mensajes_bp
from routes.ciem_ai import ciem_ai_bp


app.register_blueprint(
    docente_bp
)

app.register_blueprint(
    estudiante_bp
)

app.register_blueprint(
    mensajes_bp
)

app.register_blueprint(
    ciem_ai_bp
)
# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():

    return redirect(
        url_for("login")
    )


# ==========================================================
# SERVIDOR
# ==========================================================

if __name__ == "__main__":

    pass

# =========================
# FUNCIONES BASE CIEM
# =========================

def obtener_clase(id):
    return db.clases.find_one({"_id": ObjectId(id)})


def obtener_estudiantes_clase(id_clase):

    clase = db.clases.find_one({"_id": ObjectId(id_clase)})

    grado = clase["grado"]
    seccion = clase["seccion"]

    return list(db.estudiantes.find({
        "grado": grado,
        "seccion": seccion
    }))


def actualizar_notas(estudiante_id, clase_id, n1, n2, n3, promedio):

    db.notas.update_one(
        {
            "estudiante": estudiante_id,
            "clase": clase_id
        },
        {
            "$set": {
                "nota1": n1,
                "nota2": n2,
                "nota3": n3,
                "promedio": promedio
            }
        },
        upsert=True
    )


# =========================
# PROTECCIÓN
# =========================
from functools import wraps
from flask import session, redirect, url_for, render_template

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):


            if "usuario" not in session or "rol" not in session:
                return redirect(url_for("login"))

            if session["rol"] in roles:
                return f(*args, **kwargs)

            return redirect(url_for("login"))

        return wrapper
    return decorator

# =========================
# LOGOUT (ÚNICO)
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# CONFIGURACIÓN: CAMBIAR CONTRASEÑA (ADMIN)
# =========================

@app.route("/admin/configuracion", methods=["GET", "POST"])
@role_required("admin", "director", "secretaria", "contadora")
def configuracion_admin():

    if request.method == "POST":

        password_actual = request.form.get(
            "password_actual", ""
        ).strip()

        password_nueva = request.form.get(
            "password_nueva", ""
        ).strip()

        password_confirmar = request.form.get(
            "password_confirmar", ""
        ).strip()

        usuario_actual = db.usuarios.find_one({
            "usuario": session.get("usuario")
        })

        if not usuario_actual:

            flash(
                "No se encontró tu cuenta.",
                "danger"
            )

            return redirect(url_for("configuracion_admin"))

        password_bd = str(
            usuario_actual.get("password", "")
        ).strip()

        if password_bd != password_actual:

            flash(
                "La contraseña actual no es correcta.",
                "danger"
            )

            return redirect(url_for("configuracion_admin"))

        if len(password_nueva) < 4:

            flash(
                "La nueva contraseña debe tener al menos 4 caracteres.",
                "warning"
            )

            return redirect(url_for("configuracion_admin"))

        if password_nueva != password_confirmar:

            flash(
                "La nueva contraseña y su confirmación no coinciden.",
                "warning"
            )

            return redirect(url_for("configuracion_admin"))

        db.usuarios.update_one(
            {"usuario": session.get("usuario")},
            {"$set": {"password": password_nueva}}
        )

        flash(
            "Contraseña actualizada correctamente.",
            "success"
        )

        return redirect(url_for("configuracion_admin"))

    return render_template(
        "admin/configuracion.html",
        usuario=session.get("usuario")
    )


evert = db.docentes.find_one({
    "usuario": "evert"
})

if evert:

    evert_id = str(evert["_id"])


    asignaturas_evert = list(
        db.asignaturas.find({
            "docente_id": evert_id
        })
    )


    for a in asignaturas_evert:
        pass

# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin", endpoint="admin_dashboard")
@role_required("admin", "director", "secretaria", "contadora")
def admin_dashboard():

    total_estudiantes = db.estudiantes.count_documents({})
    total_docentes = db.docentes.count_documents({})
    total_asignaturas = db.asignaturas.count_documents({})
    total_matriculas = db.matriculas.count_documents({})

    return render_template(
        "admin/admin_dashboard.html",
        total_estudiantes=total_estudiantes,
        total_docentes=total_docentes,
        total_asignaturas=total_asignaturas,
        total_matriculas=total_matriculas
    )
# ==========================================================
# ADMIN - CREAR COMUNICADO
# ==========================================================

@app.route(
    "/admin/comunicados/crear",
    methods=["POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def crear_comunicado():

    try:


        # ==================================================
        # DATOS DEL FORMULARIO
        # ==================================================

        titulo = request.form.get(
            "titulo",
            ""
        ).strip()

        destinatario = request.form.get(
            "destinatario",
            ""
        ).strip()

        grado = request.form.get(
            "grado",
            ""
        ).strip()

        fecha = request.form.get(
            "fecha",
            ""
        ).strip()

        hora = request.form.get(
            "hora",
            ""
        ).strip()

        mensaje = request.form.get(
            "mensaje",
            ""
        ).strip()

        # ==================================================
        # VALIDACIONES
        # ==================================================

        if not titulo:
            flash(
                "Debe ingresar el título.",
                "warning"
            )
            return redirect(
                url_for("admin_comunicados")
            )

        if not destinatario:
            flash(
                "Debe seleccionar los destinatarios.",
                "warning"
            )
            return redirect(
                url_for("admin_comunicados")
            )

        if destinatario == "grado" and not grado:
            flash(
                "Debe seleccionar el grado.",
                "warning"
            )
            return redirect(
                url_for("admin_comunicados")
            )

        if not fecha:
            flash(
                "Debe seleccionar la fecha.",
                "warning"
            )
            return redirect(
                url_for("admin_comunicados")
            )

        if not hora:
            flash(
                "Debe seleccionar la hora.",
                "warning"
            )
            return redirect(
                url_for("admin_comunicados")
            )

        if not mensaje:
            flash(
                "Debe escribir el mensaje.",
                "warning"
            )
            return redirect(
                url_for("admin_comunicados")
            )

        # ==================================================
        # CREAR COMUNICADO
        # ==================================================

        comunicacion = {

            "titulo": titulo,
            "mensaje": mensaje,
            "destinatario": destinatario,
            "grado": grado,
            "fecha": fecha,
            "hora": hora,
            "estado": "publicado",
            "fecha_creacion": datetime.now()

        }

        # ==================================================
        # GUARDAR EN MONGODB
        # ==================================================

        resultado = db.comunicaciones.insert_one(
            comunicacion
        )


        ultimo = db.comunicaciones.find_one(
            {"_id": resultado.inserted_id}
        )


        # ==================================================
        # VERIFICAR COMUNICADO GUARDADO
        # ==================================================


        total_comunicados = db.comunicaciones.count_documents({})


        for comunicado_db in db.comunicaciones.find():
            pass


        flash(
            "Comunicado publicado correctamente.",
            "success"
        )

        return redirect(
            url_for("admin_comunicados")
        )

    except Exception as e:


        flash(
            f"Error al publicar el comunicado: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_comunicados")
        )


# ==========================================================
# ADMIN - LISTAR COMUNICADOS
# ==========================================================

@app.route("/admin/comunicados")
@role_required("admin", "director", "secretaria", "contadora")
def admin_comunicados():

    try:


        comunicados = list(
            db.comunicaciones.find().sort(
                "fecha_creacion",
                -1
            )
        )


        return render_template(
            "admin/comunicados.html",
            comunicados=comunicados
        )

    except Exception as e:


        flash(
            f"No se pudieron cargar los comunicados: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )
# ==========================================================
# ADMIN - LISTAR ESTUDIANTES
# ==========================================================

@app.route("/admin/estudiantes")
@role_required("admin", "director", "secretaria", "contadora")
def listar_estudiantes_admin():

    try:

        estudiantes = list(
            db.estudiantes.find().sort(
                "nombre",
                1
            )
        )

        for e in estudiantes[:10]:

            pass

        for e in estudiantes:

            pass


        return render_template(
            "admin/estudiantes.html",
            estudiantes=estudiantes
        )

    except Exception as e:


        flash(
            f"No se pudieron cargar los estudiantes: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )
# ==========================================================
# ADMIN - EDITAR ESTUDIANTE
# ==========================================================

@app.route(
    "/admin/estudiantes/editar/<id>",
    methods=["GET", "POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def editar_estudiante(id):


    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = db.estudiantes.find_one({
        "_id": id
    })


    # ======================================================
    # VALIDAR EXISTENCIA
    # ======================================================

    if estudiante is None:

        flash(
            "Estudiante no encontrado.",
            "danger"
        )

        return redirect(
            url_for("listar_estudiantes_admin")
        )

    # ======================================================
    # PROCESAR POST
    # ======================================================

    if request.method == "POST":

        primer_nombre = request.form.get(
            "primer_nombre",
            ""
        ).strip()

        segundo_nombre = request.form.get(
            "segundo_nombre",
            ""
        ).strip()

        primer_apellido = request.form.get(
            "primer_apellido",
            ""
        ).strip()

        segundo_apellido = request.form.get(
            "segundo_apellido",
            ""
        ).strip()

        grado = request.form.get(
            "grado",
            ""
        ).strip()

        seccion = request.form.get(
            "seccion",
            ""
        ).strip()

        edad = request.form.get(
            "edad",
            ""
        ).strip()

        genero = request.form.get(
            "genero",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        celular = request.form.get(
            "celular",
            ""
        ).strip()

        direccion = request.form.get(
            "direccion",
            ""
        ).strip()

        barrio = request.form.get(
            "barrio",
            ""
        ).strip()

        padre = request.form.get(
            "padre",
            ""
        ).strip()

        madre = request.form.get(
            "madre",
            ""
        ).strip()

        tutor = request.form.get(
            "tutor",
            ""
        ).strip()

        # ==================================================
        # NOMBRE COMPLETO
        # ==================================================

        nombre_completo = " ".join(
            parte
            for parte in [
                primer_nombre,
                segundo_nombre,
                primer_apellido,
                segundo_apellido
            ]
            if parte
        )

        # ==================================================
        # ACTUALIZAR MONGODB
        # ==================================================

        db.estudiantes.update_one(
            {
                "_id": id
            },
            {
                "$set": {
                    "nombre": nombre_completo,
                    "primer_nombre": primer_nombre,
                    "segundo_nombre": segundo_nombre,
                    "primer_apellido": primer_apellido,
                    "segundo_apellido": segundo_apellido,
                    "grado": grado,
                    "seccion": seccion,
                    "edad": edad,
                    "genero": genero,
                    "telefono": telefono,
                    "celular": celular,
                    "direccion": direccion,
                    "barrio": barrio,
                    "padre": padre,
                    "madre": madre,
                    "tutor": tutor
                }
            }
        )

        flash(
            "Estudiante actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("listar_estudiantes_admin")
        )

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    return render_template(
        "admin/editar_estudiante.html",
        estudiante=estudiante
    )


# ==========================================================
# ADMIN - ELIMINAR COMUNICADO
# ==========================================================

@app.route(
    "/admin/comunicados/eliminar/<id>",
    methods=["POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def eliminar_comunicado(id):

    try:


        resultado = db.comunicaciones.delete_one({
            "_id": ObjectId(id)
        })

        if resultado.deleted_count == 1:


            flash(
                "Comunicado eliminado correctamente.",
                "success"
            )

        else:


            flash(
                "El comunicado no fue encontrado.",
                "warning"
            )

        return redirect(
            url_for("admin_comunicados")
        )

    except Exception as e:


        flash(
            f"No se pudo eliminar el comunicado: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_comunicados")
        )
# ==========================================================
# ADMIN - HISTORIAL DE COMUNICADOS
# ==========================================================

@app.route("/admin/comunicados/historial")
@role_required("admin", "director", "secretaria", "contadora")
def historial_comunicados():

    try:


        comunicados = list(
            db.comunicaciones.find().sort(
                "fecha_creacion",
                -1
            )
        )


        return render_template(
            "admin/historial_comunicados.html",
            comunicados=comunicados
        )

    except Exception as e:


        flash(
            f"No se pudo cargar el historial: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_comunicados")
        )
# ==========================================================
# ADMIN - PREPARAR ENVÍO POR WHATSAPP
# ==========================================================

@app.route("/admin/comunicados/<id>/whatsapp")
@role_required("admin", "director", "secretaria", "contadora")
def comunicado_whatsapp(id):

    try:


        # ==================================================
        # BUSCAR COMUNICADO
        # ==================================================

        comunicado = db.comunicaciones.find_one({
            "_id": ObjectId(id)
        })

        if not comunicado:

            flash(
                "El comunicado no existe.",
                "danger"
            )

            return redirect(
                url_for("admin_comunicados")
            )


        # ==================================================
        # BUSCAR ESTUDIANTES
        # ==================================================

        if comunicado.get("destinatario") == "grado":

            estudiantes = list(
                db.estudiantes.find({
                    "grado": comunicado.get("grado")
                }).sort(
                    "nombre",
                    1
                )
            )

        else:

            estudiantes = list(
                db.estudiantes.find().sort(
                    "nombre",
                    1
                )
            )


        # ==================================================
        # CREAR CONTACTOS
        # ==================================================

        contactos = []

        for estudiante in estudiantes:

            nombre_estudiante = estudiante.get(
                "nombre",
                ""
            )

            # ----------------------------------------------
            # PADRE
            # ----------------------------------------------

            padre = estudiante.get(
                "padre",
                ""
            )

            telefono_padre = estudiante.get(
                "telefono",
                ""
            )

            if padre and telefono_padre:

                contactos.append({

                    "nombre": padre,

                    "tipo": "Padre",

                    "estudiante":
                        nombre_estudiante,

                    "telefono":
                        telefono_padre

                })

            # ----------------------------------------------
            # MADRE
            # ----------------------------------------------

            madre = estudiante.get(
                "madre",
                ""
            )

            telefono_madre = estudiante.get(
                "celular",
                ""
            )

            if madre and telefono_madre:

                contactos.append({

                    "nombre": madre,

                    "tipo": "Madre",

                    "estudiante":
                        nombre_estudiante,

                    "telefono":
                        telefono_madre

                })

            # ----------------------------------------------
            # TUTOR
            # ----------------------------------------------

            tutor = estudiante.get(
                "tutor",
                ""
            )

            if tutor:

                telefono_tutor = estudiante.get(
                    "telefono",
                    ""
                )

                if telefono_tutor:

                    contactos.append({

                        "nombre": tutor,

                        "tipo": "Tutor",

                        "estudiante":
                            nombre_estudiante,

                        "telefono":
                            telefono_tutor

                    })


        # ==================================================
        # MOSTRAR PÁGINA
        # ==================================================

        return render_template(
            "admin/comunicado_whatsapp.html",
            comunicado=comunicado,
            contactos=contactos
        )

    except Exception as e:


        flash(
            f"No se pudo preparar WhatsApp: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_comunicados")
        )
    
# ==========================================================
# ADMIN - ELIMINAR ESTUDIANTE
# ==========================================================

@app.route(
    "/admin/estudiantes/eliminar/<id>",
    methods=["GET"]
)
@role_required("admin", "director", "secretaria", "contadora")
def eliminar_estudiante(id):


    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = db.estudiantes.find_one({
        "_id": id
    })


    # ======================================================
    # VALIDAR EXISTENCIA
    # ======================================================

    if estudiante is None:

        flash(
            "Estudiante no encontrado.",
            "danger"
        )

        return redirect(
            url_for("listar_estudiantes_admin")
        )

    # ======================================================
    # ELIMINAR ESTUDIANTE
    # ======================================================

    resultado = db.estudiantes.delete_one({
        "_id": id
    })


    # ======================================================
    # ELIMINAR MATRÍCULA RELACIONADA
    # ======================================================

    resultado_matricula = db.matriculas.delete_many({
        "estudiante_id": id
    })


    # ======================================================
    # MENSAJE
    # ======================================================

    flash(
        "Estudiante eliminado correctamente.",
        "success"
    )

    # ======================================================
    # REGRESAR AL LISTADO
    # ======================================================

    return redirect(
        url_for("listar_estudiantes_admin")
    )
    # ==================================================
    # ACTUALIZAR EN MONGODB
    # ==================================================

    db.estudiantes.update_one(

        {
            "_id": id
        },

        {
            "$set": {

                "nombre":
                    nombre_completo,

                "primer_nombre":
                    primer_nombre,

                "segundo_nombre":
                    segundo_nombre,

                "primer_apellido":
                    primer_apellido,

                "segundo_apellido":
                    segundo_apellido,

                "grado":
                    grado,

                "seccion":
                    seccion,

                "edad":
                    edad,

                "genero":
                    genero,

                "telefono":
                    telefono,

                "celular":
                    celular,

                "direccion":
                    direccion,

                "barrio":
                    barrio,

                "padre":
                    padre,

                "madre":
                    madre,

                "tutor":
                    tutor
            }
        }
    )

    flash(
        "Estudiante actualizado correctamente.",
        "success"
    )

    return redirect(
        url_for("listar_estudiantes_admin")
    )


# ======================================================
# MOSTRAR FORMULARIO
# ======================================================

    return render_template(
        "admin/editar_estudiante.html",
        estudiante=estudiante
    )

       


# =========================
# ADMIN - DOCENTES
# =========================

@app.route("/admin/docentes")
@role_required("admin", "director", "secretaria", "contadora")
def listar_docentes():

    docentes = list(
        db.docentes.find().sort(
            "nombre",
            1
        )
    )


    for d in docentes:

        pass


    return render_template(
        "admin/docente.html",
        docentes=docentes
    )
# =========================
# EDITAR DOCENTE
# =========================

from bson.objectid import ObjectId

@app.route(
    "/admin/docentes/editar/<id>",
    methods=["GET", "POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def editar_docente(id):


    # ==================================================
    # BUSCAR DOCENTE
    # ==================================================

    docente = db.docentes.find_one({
        "_id": id
    })

    # ==================================================
    # SI NO EXISTE, PROBAR ObjectId
    # ==================================================

    if docente is None:

        try:

            docente = db.docentes.find_one({
                "_id": ObjectId(id)
            })

        except Exception:

            docente = None


    # ==================================================
    # DOCENTE NO ENCONTRADO
    # ==================================================

    if docente is None:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("listar_docentes")
        )

    # ==================================================
    # GUARDAR CAMBIOS
    # ==================================================

    if request.method == "POST":

        filtro = {
            "_id": docente["_id"]
        }

        db.docentes.update_one(

            filtro,

            {
                "$set": {

                    "nombre":
                        request.form.get(
                            "nombre",
                            ""
                        ).strip(),

                    "usuario":
                        request.form.get(
                            "usuario",
                            ""
                        ).strip(),

                    "telefono":
                        request.form.get(
                            "telefono",
                            ""
                        ).strip(),

                    "especialidad":
                        request.form.get(
                            "especialidad",
                            ""
                        ).strip()

                }
            }

        )

        flash(
            "Docente actualizado correctamente",
            "success"
        )

        return redirect(
            url_for("listar_docentes")
        )

    # ==================================================
    # MOSTRAR FORMULARIO
    # ==================================================

    return render_template(
        "admin/editar_docente.html",
        docente=docente
    )

# =========================
# ELIMINAR DOCENTE
# =========================

@app.route("/admin/docentes/eliminar/<id>")
@role_required("admin", "director", "secretaria", "contadora")
def eliminar_docente(id):


    try:

        # Buscar primero como texto
        docente = db.docentes.find_one({
            "_id": id
        })

        # Si no existe, probar como ObjectId
        if docente is None:

            try:

                docente = db.docentes.find_one({
                    "_id": ObjectId(id)
                })

            except Exception:

                docente = None

        # ==============================================
        # NO ENCONTRADO
        # ==============================================

        if docente is None:

            flash(
                "Docente no encontrado.",
                "warning"
            )

            return redirect(
                url_for("listar_docentes")
            )

        # ==============================================
        # ELIMINAR
        # ==============================================

        db.docentes.delete_one({
            "_id": docente["_id"]
        })

        flash(
            "Docente eliminado correctamente.",
            "success"
        )


        return redirect(
            url_for("listar_docentes")
        )

    except Exception as e:


        flash(
            f"No se pudo eliminar el docente: {e}",
            "danger"
        )

        return redirect(
            url_for("listar_docentes")
        )
# =========================
# AGREGAR DOCENTE
# =========================

@app.route("/admin/docente/agregar", methods=["GET","POST"])
@role_required("admin", "director", "secretaria", "contadora")
def agregar_docente():

    if request.method == "POST":

        codigo = request.form["codigo"].strip()

        # ==================================================
        # EVITAR CÓDIGO DUPLICADO
        # ==================================================
        # "_id" se fija igual al código (ej. "DOC012") para
        # que el docente quede identificado de forma
        # consistente en todas las colecciones que guardan
        # docente_id (conversaciones, notas, asignaciones).
        # Sin esto, Mongo generaría un ObjectId aleatorio
        # como _id, distinto al resto de docentes.

        if db.docentes.find_one({"_id": codigo}):

            flash(
                f"Ya existe un docente con el código {codigo}.",
                "danger"
            )

            return redirect(
                url_for("agregar_docente")
            )

        docente = {

            "_id": codigo,
            "codigo": codigo,
            "nombre": request.form["nombre"],
            "usuario": request.form["usuario"],
            "telefono": request.form["telefono"],
            "nivel": request.form["nivel"],
            "tipo_docente": request.form["tipo_docente"],
            "cargo": request.form["cargo"],
            "especialidad": request.form["especialidad"],
            "activo": True

        }


        db.docentes.insert_one(docente)


        flash(
            "Docente agregado correctamente",
            "success"
        )


        return redirect(
            url_for("listar_docentes")
        )


    return render_template(
        "admin/agregar_docente.html"
    )

# ==========================================================
# LISTAR MATRÍCULAS
# ==========================================================

@app.route("/matriculas")
@role_required("admin", "director", "secretaria", "contadora")
def listar_matriculas():

    try:

        matriculas = list(
            db.matriculas.aggregate([

                {
                    "$lookup": {
                        "from": "estudiantes",
                        "localField": "estudiante_id",
                        "foreignField": "_id",
                        "as": "estudiante"
                    }
                },

                {
                    "$unwind": {
                        "path": "$estudiante",
                        "preserveNullAndEmptyArrays": True
                    }
                },

                {
                    "$sort": {
                        "fecha_matricula": -1
                    }
                }

            ])
        )


        return render_template(
            "admin/matriculas.html",
            matriculas=matriculas
        )

    except Exception as e:


        flash(
            f"No se pudieron cargar las matrículas: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

# ==========================================================
# NORMALIZAR TEXTO
# ==========================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    return " ".join(
        str(texto).strip().upper().split()
    )


# ==========================================================
# GENERAR CÓDIGO DE ESTUDIANTE
# ==========================================================

def generar_codigo_estudiante(
    primer_nombre,
    segundo_nombre,
    primer_apellido,
    segundo_apellido
):

    primer_nombre = normalizar_texto(
        primer_nombre
    )

    segundo_nombre = normalizar_texto(
        segundo_nombre
    )

    primer_apellido = normalizar_texto(
        primer_apellido
    )

    segundo_apellido = normalizar_texto(
        segundo_apellido
    )


    # ======================================================
    # GENERAR INICIALES
    # ======================================================

    iniciales = (

        (primer_nombre or "")[:1]

        + (segundo_nombre or "")[:1]

        + (primer_apellido or "")[:1]

        + (segundo_apellido or "")[:1]

    ).upper()


    # ======================================================
    # COMPLETAR HASTA 4 CARACTERES
    # ======================================================

    iniciales = (
        iniciales + "XXXX"
    )[:4]


    codigo_base = f"CIEM-{iniciales}"

    codigo = codigo_base

    contador = 2


    # ======================================================
    # COMPROBAR QUE EL CÓDIGO NO EXISTA
    #
    # IMPORTANTE:
    # El código se comprueba contra estudiantes.
    # ======================================================

    while db.estudiantes.find_one({
        "_id": codigo
    }):

        codigo = (
            f"{codigo_base}{contador}"
        )

        contador += 1


    return codigo


# ==========================================================
# BUSCAR ESTUDIANTE EXISTENTE
# ==========================================================

def buscar_estudiante_existente(
    codigo_existente="",
    primer_nombre="",
    segundo_nombre="",
    primer_apellido="",
    segundo_apellido="",
    fecha_nacimiento=""
):

    # ======================================================
    # NORMALIZAR DATOS
    # ======================================================

    codigo_existente = normalizar_texto(
        codigo_existente
    )

    primer_nombre = normalizar_texto(
        primer_nombre
    )

    segundo_nombre = normalizar_texto(
        segundo_nombre
    )

    primer_apellido = normalizar_texto(
        primer_apellido
    )

    segundo_apellido = normalizar_texto(
        segundo_apellido
    )

    fecha_nacimiento = (
        fecha_nacimiento or ""
    ).strip()


    # ======================================================
    # 1. SI VIENE CÓDIGO DESDE EL FORMULARIO
    #
    # ESTA ES LA OPCIÓN MÁS SEGURA.
    #
    # SI EL USUARIO SELECCIONÓ UN ESTUDIANTE,
    # NO VOLVEMOS A BUSCAR POR NOMBRE.
    # ======================================================

    if codigo_existente:

        estudiante = db.estudiantes.find_one({
            "_id": codigo_existente
        })


        if estudiante:


            return estudiante


        return None


    # ======================================================
    # 2. SIN CÓDIGO
    #
    # BUSCAR POR LOS CAMPOS INDIVIDUALES.
    #
    # NO BUSCAMOS CAMPOS VACÍOS COMO SI FUERAN DATOS.
    # ======================================================

    consulta = {}


    if primer_nombre:

        consulta["primer_nombre"] = {
            "$regex": "^" + re.escape(
                primer_nombre
            ) + "$",
            "$options": "i"
        }


    if segundo_nombre:

        consulta["segundo_nombre"] = {
            "$regex": "^" + re.escape(
                segundo_nombre
            ) + "$",
            "$options": "i"
        }


    if primer_apellido:

        consulta["primer_apellido"] = {
            "$regex": "^" + re.escape(
                primer_apellido
            ) + "$",
            "$options": "i"
        }


    if segundo_apellido:

        consulta["segundo_apellido"] = {
            "$regex": "^" + re.escape(
                segundo_apellido
            ) + "$",
            "$options": "i"
        }


    # ======================================================
    # SI NO HAY NINGÚN DATO PARA BUSCAR
    # ======================================================

    if not consulta:


        return None


    # ======================================================
    # BUSCAR CANDIDATOS
    # ======================================================

    candidatos = list(
        db.estudiantes.find(
            consulta
        )
    )


    # ======================================================
    # NO HAY CANDIDATOS
    # ======================================================

    if not candidatos:


        return None


    # ======================================================
    # SI HAY FECHA DE NACIMIENTO
    # DEBE COINCIDIR EXACTAMENTE
    # ======================================================

    if fecha_nacimiento:

        coincidencias = []


        for estudiante in candidatos:

            fecha_bd = str(
                estudiante.get(
                    "fecha_nacimiento",
                    ""
                )
            ).strip()


            if fecha_bd == fecha_nacimiento:

                coincidencias.append(
                    estudiante
                )


        # ==================================================
        # UNA SOLA COINCIDENCIA
        # ==================================================

        if len(coincidencias) == 1:

            estudiante = coincidencias[0]


            return estudiante


        # ==================================================
        # VARIAS COINCIDENCIAS
        # ==================================================

        if len(coincidencias) > 1:


            for estudiante in coincidencias:

                pass


            return None


        # ==================================================
        # NOMBRE ENCONTRADO PERO FECHA NO COINCIDE
        # ==================================================


        return None


    # ======================================================
    # SIN FECHA
    #
    # NO REUTILIZAMOS AUTOMÁTICAMENTE EL CÓDIGO.
    # ======================================================


    return None


# ==========================================================
# API: BUSCAR ESTUDIANTES (PARA RE-MATRÍCULA)
#
# Devuelve una lista corta de coincidencias por código o
# nombre, para que la secretaria pueda seleccionar un
# estudiante ya existente y autocompletar el formulario.
# ==========================================================

@app.route(
    "/admin/api/estudiantes/buscar"
)
@role_required("admin", "director", "secretaria", "contadora")
def api_buscar_estudiantes():

    termino = request.args.get(
        "q",
        ""
    ).strip()

    if len(termino) < 2:

        return jsonify([])


    termino_regex = re.escape(
        termino
    )

    resultados = list(
        db.estudiantes.find(
            {
                "$or": [

                    {
                        "_id": {
                            "$regex": termino_regex,
                            "$options": "i"
                        }
                    },

                    {
                        "nombre": {
                            "$regex": termino_regex,
                            "$options": "i"
                        }
                    }

                ]
            },

            {
                "_id": 1,
                "nombre": 1,
                "grado": 1,
                "seccion": 1
            }

        ).limit(10)
    )


    return jsonify([
        {
            "codigo": e.get("_id", ""),
            "nombre": e.get("nombre", ""),
            "grado": e.get("grado", ""),
            "seccion": e.get("seccion", "")
        }
        for e in resultados
    ])


# ==========================================================
# API: OBTENER UN ESTUDIANTE COMPLETO
#
# Devuelve todos los datos guardados de un estudiante para
# precargar el formulario de matrícula al renovarla.
# ==========================================================

@app.route(
    "/admin/api/estudiante/<codigo>"
)
@role_required("admin", "director", "secretaria", "contadora")
def api_obtener_estudiante(codigo):

    estudiante = db.estudiantes.find_one({
        "_id": codigo
    })

    if not estudiante:

        return jsonify({
            "error": "No encontrado"
        }), 404


    fecha_nacimiento = str(
        estudiante.get(
            "fecha_nacimiento",
            ""
        )
    )

    dia = mes = anio = ""

    if fecha_nacimiento and len(
        fecha_nacimiento.split("-")
    ) == 3:

        anio, mes, dia = (
            fecha_nacimiento.split("-")
        )


    informacion_linguistica = estudiante.get(
        "informacion_linguistica",
        {}
    )

    padre = estudiante.get("padre", {})
    madre = estudiante.get("madre", {})
    tutor = estudiante.get("tutor", {})


    return jsonify({

        "codigo": estudiante.get("_id", ""),

        "primer_nombre": estudiante.get("primer_nombre", ""),
        "segundo_nombre": estudiante.get("segundo_nombre", ""),
        "primer_apellido": estudiante.get("primer_apellido", ""),
        "segundo_apellido": estudiante.get("segundo_apellido", ""),

        "dia_nacimiento": dia,
        "mes_nacimiento": mes,
        "anio_nacimiento": anio,

        "edad": estudiante.get("edad", ""),
        "genero": estudiante.get("genero", ""),
        "lugar_nacimiento": estudiante.get("lugar_nacimiento", ""),
        "talla": estudiante.get("talla", ""),
        "peso": estudiante.get("peso", ""),
        "tipo_sangre": estudiante.get("tipo_sangre", ""),

        "direccion": estudiante.get("direccion", ""),
        "barrio": estudiante.get("barrio", ""),
        "telefono": estudiante.get("telefono", ""),
        "celular": estudiante.get("celular", ""),

        "lengua_materna": informacion_linguistica.get("lengua_materna", ""),
        "idioma": informacion_linguistica.get("idioma", ""),
        "curso_ingles": informacion_linguistica.get("curso_ingles", ""),
        "grupo_etnico": informacion_linguistica.get("grupo_etnico", ""),

        "capacidades": estudiante.get("capacidades", []),
        "observaciones": estudiante.get("observaciones", ""),

        "padre_nombre": padre.get("nombre", ""),
        "padre_cedula": padre.get("cedula", ""),
        "padre_telefono": padre.get("telefono", ""),
        "padre_celular": padre.get("celular", ""),
        "padre_ocupacion": padre.get("ocupacion", ""),

        "madre_nombre": madre.get("nombre", ""),
        "madre_cedula": madre.get("cedula", ""),
        "madre_telefono": madre.get("telefono", ""),
        "madre_celular": madre.get("celular", ""),
        "madre_ocupacion": madre.get("ocupacion", ""),

        "tutor_nombre": tutor.get("nombre", ""),
        "tutor_parentesco": tutor.get("parentesco", ""),
        "tutor_cedula": tutor.get("cedula", ""),
        "tutor_celular": tutor.get("celular", ""),
        "tutor_ocupacion": tutor.get("ocupacion", ""),

        "grado_anterior": estudiante.get("grado", ""),
        "seccion_anterior": estudiante.get("seccion", "")

    })


# ==========================================================
# API: HISTORIAL DE MATRÍCULA DE UN ESTUDIANTE
# ==========================================================

@app.route(
    "/admin/api/estudiante/<codigo>/historial"
)
@role_required("admin", "director", "secretaria", "contadora")
def api_historial_matricula(codigo):

    estudiante = db.estudiantes.find_one({
        "_id": codigo
    })

    if not estudiante:

        return jsonify({
            "error": "No encontrado"
        }), 404


    matriculas = list(
        db.matriculas.find({
            "estudiante_id": codigo
        }).sort("anio_lectivo", 1)
    )


    historial = []

    for m in matriculas:

        fecha_matricula = m.get(
            "fecha_matricula",
            ""
        )

        historial.append({

            "anio_lectivo":
                m.get("anio_lectivo", ""),

            "grado":
                m.get("grado", ""),

            "seccion":
                m.get("seccion", ""),

            "fecha_matricula":
                str(fecha_matricula),

            "tipo_matricula":
                m.get("tipo_matricula", ""),

            "estado":
                m.get("estado", "")

        })


    return jsonify({

        "codigo": estudiante.get("_id", ""),

        "nombre": estudiante.get("nombre", ""),

        "historial": historial

    })


# ==========================================================
# ADMIN - PANTALLA DE HISTORIAL DE MATRÍCULA
# ==========================================================

@app.route(
    "/admin/estudiantes/historial"
)
@role_required("admin", "director", "secretaria", "contadora")
def historial_matricula_admin():

    return render_template(
        "admin/historial_matricula.html"
    )


# ==========================================================
# AGREGAR / RENOVAR MATRÍCULA
# ==========================================================

@app.route(
    "/admin/matricula/agregar",
    methods=["GET", "POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def agregar_matricula():

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    if request.method == "GET":

        return render_template(
            "admin/agregar_matricula.html"
        )


    try:


        # ==================================================
        # CÓDIGO DEL ESTUDIANTE SELECCIONADO
        # ==================================================

        codigo_existente = request.form.get(
            "codigo_estudiante",
            ""
        ).strip()


        # ==================================================
        # NOMBRES
        # ==================================================

        primer_apellido = request.form.get(
            "primer_apellido",
            ""
        ).strip()

        segundo_apellido = request.form.get(
            "segundo_apellido",
            ""
        ).strip()

        primer_nombre = request.form.get(
            "primer_nombre",
            ""
        ).strip()

        segundo_nombre = request.form.get(
            "segundo_nombre",
            ""
        ).strip()


        # ==================================================
        # VALIDACIONES
        # ==================================================

        if not primer_nombre:

            flash(
                "Debe ingresar el primer nombre.",
                "warning"
            )

            return redirect(
                url_for("agregar_matricula")
            )


        if not primer_apellido:

            flash(
                "Debe ingresar el primer apellido.",
                "warning"
            )

            return redirect(
                url_for("agregar_matricula")
            )


        # ==================================================
        # FECHA DE NACIMIENTO
        # ==================================================

        dia = request.form.get(
            "dia_nacimiento",
            ""
        ).strip()

        mes = request.form.get(
            "mes_nacimiento",
            ""
        ).strip()

        anio = request.form.get(
            "anio_nacimiento",
            ""
        ).strip()


        if dia and mes and anio:

            fecha_nacimiento = (
                f"{anio}-"
                f"{mes.zfill(2)}-"
                f"{dia.zfill(2)}"
            )

        else:

            fecha_nacimiento = ""


        # ==================================================
        # BUSCAR / IDENTIFICAR ESTUDIANTE
        #
        # SI VIENE CODIGO_ESTUDIANTE:
        #
        #   NO BUSCAMOS POR NOMBRE.
        #
        #   USAMOS DIRECTAMENTE ESE CÓDIGO.
        #
        # ==================================================

        estudiante_existente = None


        if codigo_existente:

            estudiante_existente = (
                db.estudiantes.find_one({
                    "_id": codigo_existente
                })
            )


            if not estudiante_existente:

                flash(
                    "El estudiante seleccionado "
                    "no existe en la base de datos.",
                    "danger"
                )


                return redirect(
                    url_for(
                        "agregar_matricula"
                    )
                )


            # ==============================================
            # CONSERVAR CÓDIGO EXISTENTE
            # ==============================================

            codigo = (
                estudiante_existente["_id"]
            )


        else:

            # ==============================================
            # NO HAY SELECCIÓN
            #
            # INTENTAR IDENTIFICAR POR DATOS
            # ==============================================

            estudiante_existente = (
                buscar_estudiante_existente(

                    codigo_existente="",

                    primer_nombre=
                        primer_nombre,

                    segundo_nombre=
                        segundo_nombre,

                    primer_apellido=
                        primer_apellido,

                    segundo_apellido=
                        segundo_apellido,

                    fecha_nacimiento=
                        fecha_nacimiento

                )
            )


            # ==============================================
            # ESTUDIANTE EXISTENTE
            # ==============================================

            if estudiante_existente:

                codigo = (
                    estudiante_existente["_id"]
                )


            # ==============================================
            # ESTUDIANTE NUEVO
            # ==============================================

            else:

                codigo = generar_codigo_estudiante(

                    primer_nombre,

                    segundo_nombre,

                    primer_apellido,

                    segundo_apellido

                )


        # ==================================================
        # DATOS GENERALES
        # ==================================================

        grado = request.form.get(
            "grado",
            ""
        ).strip()

        seccion = request.form.get(
            "seccion",
            ""
        ).strip()

        edad = request.form.get(
            "edad",
            ""
        ).strip()

        genero = request.form.get(
            "genero",
            ""
        ).strip()

        lugar_nacimiento = request.form.get(
            "lugar_nacimiento",
            ""
        ).strip()


        # ==================================================
        # AÑO LECTIVO
        # ==================================================

        anio_lectivo = request.form.get(
            "anio_lectivo",
            "2026"
        ).strip()


        try:

            anio_lectivo = int(
                anio_lectivo
            )

        except ValueError:

            anio_lectivo = 2026


        # ==================================================
        # VERIFICAR MATRÍCULA DEL MISMO AÑO
        # ==================================================

        matricula_existente = (
            db.matriculas.find_one({

                "estudiante_id":
                    codigo,

                "anio_lectivo":
                    anio_lectivo

            })
        )


        if matricula_existente:

            flash(
                f"El estudiante {codigo} ya tiene "
                f"una matrícula registrada para "
                f"{anio_lectivo}.",
                "warning"
            )


            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        # ==================================================
        # DATOS FÍSICOS
        # ==================================================

        talla = request.form.get(
            "talla",
            ""
        ).strip()

        peso = request.form.get(
            "peso",
            ""
        ).strip()

        tipo_sangre = request.form.get(
            "tipo_sangre",
            ""
        ).strip()


        # ==================================================
        # UBICACIÓN
        # ==================================================

        direccion = request.form.get(
            "direccion",
            ""
        ).strip()

        barrio = request.form.get(
            "barrio",
            ""
        ).strip()


        # ==================================================
        # CONTACTO
        # ==================================================

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        celular = request.form.get(
            "celular",
            ""
        ).strip()


        # ==================================================
        # INFORMACIÓN LINGÜÍSTICA
        # ==================================================

        lengua_materna = request.form.get(
            "lengua_materna",
            ""
        ).strip()

        idioma = request.form.get(
            "idioma",
            ""
        ).strip()

        curso_ingles = request.form.get(
            "curso_ingles",
            ""
        ).strip()

        grupo_etnico = request.form.get(
            "grupo_etnico",
            ""
        ).strip()


        informacion_linguistica = {

            "lengua_materna":
                lengua_materna,

            "idioma":
                idioma,

            "curso_ingles":
                curso_ingles,

            "grupo_etnico":
                grupo_etnico

        }


        # ==================================================
        # CAPACIDADES
        # ==================================================

        capacidades = request.form.getlist(
            "capacidades"
        )


        # ==================================================
        # OBSERVACIONES
        # ==================================================

        observaciones = request.form.get(
            "observaciones",
            ""
        ).strip()


        # ==================================================
        # PADRE
        # ==================================================

        padre_nombre = request.form.get(
            "padre_nombre",
            ""
        ).strip()

        padre_cedula = request.form.get(
            "padre_cedula",
            ""
        ).strip()

        padre_telefono = request.form.get(
            "padre_telefono",
            ""
        ).strip()

        padre_celular = request.form.get(
            "padre_celular",
            ""
        ).strip()

        padre_ocupacion = request.form.get(
            "padre_ocupacion",
            ""
        ).strip()


        # ==================================================
        # MADRE
        # ==================================================

        madre_nombre = request.form.get(
            "madre_nombre",
            ""
        ).strip()

        madre_cedula = request.form.get(
            "madre_cedula",
            ""
        ).strip()

        madre_telefono = request.form.get(
            "madre_telefono",
            ""
        ).strip()

        madre_celular = request.form.get(
            "madre_celular",
            ""
        ).strip()

        madre_ocupacion = request.form.get(
            "madre_ocupacion",
            ""
        ).strip()

        madre_usuario = request.form.get(
            "madre_usuario",
            ""
        ).strip()


        # ==================================================
        # TUTOR
        # ==================================================

        tutor_nombre = request.form.get(
            "tutor_nombre",
            ""
        ).strip()

        tutor_parentesco = request.form.get(
            "tutor_parentesco",
            ""
        ).strip()

        tutor_cedula = request.form.get(
            "tutor_cedula",
            ""
        ).strip()

        tutor_celular = request.form.get(
            "tutor_celular",
            ""
        ).strip()

        tutor_ocupacion = request.form.get(
            "tutor_ocupacion",
            ""
        ).strip()


        # ==================================================
        # FECHA DE MATRÍCULA
        # ==================================================

        fecha_matricula = request.form.get(
            "fecha_matricula",
            ""
        ).strip()


        # ==================================================
        # NOMBRE COMPLETO
        # ==================================================

        nombre_completo = " ".join(

            parte

            for parte in [

                primer_nombre,

                segundo_nombre,

                primer_apellido,

                segundo_apellido

            ]

            if parte

        )


        # ==================================================
        # CREAR ESTUDIANTE SI ES NUEVO
        # ==================================================

        if not estudiante_existente:

            estudiante = {

                "_id":
                    codigo,

                "codigo":
                    codigo,

                "nombre":
                    nombre_completo,

                "primer_nombre":
                    primer_nombre,

                "segundo_nombre":
                    segundo_nombre,

                "primer_apellido":
                    primer_apellido,

                "segundo_apellido":
                    segundo_apellido,

                "fecha_nacimiento":
                    fecha_nacimiento,

                "grado":
                    grado,

                "seccion":
                    seccion,

                "edad":
                    edad,

                "genero":
                    genero,

                "lugar_nacimiento":
                    lugar_nacimiento,

                "talla":
                    talla,

                "peso":
                    peso,

                "tipo_sangre":
                    tipo_sangre,

                "direccion":
                    direccion,

                "barrio":
                    barrio,

                "telefono":
                    telefono,

                "celular":
                    celular,

                "informacion_linguistica":
                    informacion_linguistica,

                "capacidades":
                    capacidades,

                "observaciones":
                    observaciones,

                "padre": {

                    "nombre":
                        padre_nombre,

                    "cedula":
                        padre_cedula,

                    "telefono":
                        padre_telefono,

                    "celular":
                        padre_celular,

                    "ocupacion":
                        padre_ocupacion

                },

                "madre": {

                    "nombre":
                        madre_nombre,

                    "cedula":
                        madre_cedula,

                    "telefono":
                        madre_telefono,

                    "celular":
                        madre_celular,

                    "ocupacion":
                        madre_ocupacion,

                    "usuario":
                        madre_usuario

                },

                # ==========================================
                # madre_usuario también en la raíz del
                # documento. obtener_estudiante_sesion() (en
                # estudiante.py) y guardar_comunicacion() (en
                # docentes.py) buscan este campo plano, no el
                # anidado madre.usuario, así que sin esta línea
                # el login de la madre nunca encontraba al hijo.
                # ==========================================

                "madre_usuario":
                    madre_usuario,

                "tutor": {

                    "nombre":
                        tutor_nombre,

                    "parentesco":
                        tutor_parentesco,

                    "cedula":
                        tutor_cedula,

                    "celular":
                        tutor_celular,

                    "ocupacion":
                        tutor_ocupacion

                },

                "estado":
                    "activo",

                "foto":
                    "usuario.png",

                "fecha_creacion":
                    datetime.now()

            }


            db.estudiantes.insert_one(
                estudiante
            )


        # ==================================================
        # ACTUALIZAR ESTUDIANTE EXISTENTE
        #
        # AQUÍ NO CAMBIAMOS _id NI codigo.
        # ==================================================

        else:

            db.estudiantes.update_one(

                {
                    "_id":
                        codigo
                },

                {
                    "$set": {

                        "nombre":
                            nombre_completo,

                        "primer_nombre":
                            primer_nombre,

                        "segundo_nombre":
                            segundo_nombre,

                        "primer_apellido":
                            primer_apellido,

                        "segundo_apellido":
                            segundo_apellido,

                        "fecha_nacimiento":
                            fecha_nacimiento,

                        "grado":
                            grado,

                        "seccion":
                            seccion,

                        "edad":
                            edad,

                        "genero":
                            genero,

                        "lugar_nacimiento":
                            lugar_nacimiento,

                        "talla":
                            talla,

                        "peso":
                            peso,

                        "tipo_sangre":
                            tipo_sangre,

                        "direccion":
                            direccion,

                        "barrio":
                            barrio,

                        "telefono":
                            telefono,

                        "celular":
                            celular,

                        "informacion_linguistica":
                            informacion_linguistica,

                        "capacidades":
                            capacidades,

                        "observaciones":
                            observaciones,

                        "padre": {

                            "nombre":
                                padre_nombre,

                            "cedula":
                                padre_cedula,

                            "telefono":
                                padre_telefono,

                            "celular":
                                padre_celular,

                            "ocupacion":
                                padre_ocupacion

                        },

                        "madre": {

                            "nombre":
                                madre_nombre,

                            "cedula":
                                madre_cedula,

                            "telefono":
                                madre_telefono,

                            "celular":
                                madre_celular,

                            "ocupacion":
                                madre_ocupacion,

                            "usuario":
                                madre_usuario

                        },

                        "madre_usuario":
                            madre_usuario,

                        "tutor": {

                            "nombre":
                                tutor_nombre,

                            "parentesco":
                                tutor_parentesco,

                            "cedula":
                                tutor_cedula,

                            "celular":
                                tutor_celular,

                            "ocupacion":
                                tutor_ocupacion

                        },

                        "estado":
                            "activo"

                    }

                }

            )


        # ==================================================
        # CREAR NUEVA MATRÍCULA
        # ==================================================

        matricula = {

            "estudiante_id":
                codigo,

            "codigo":
                codigo,

            "fecha_matricula":
                fecha_matricula,

            "anio_lectivo":
                anio_lectivo,

            "grado":
                grado,

            "seccion":
                seccion,

            "estudiante": {

                "primer_apellido":
                    primer_apellido,

                "segundo_apellido":
                    segundo_apellido,

                "primer_nombre":
                    primer_nombre,

                "segundo_nombre":
                    segundo_nombre,

                "nombre_completo":
                    nombre_completo,

                "fecha_nacimiento":
                    fecha_nacimiento,

                "edad":
                    edad,

                "genero":
                    genero,

                "lugar_nacimiento":
                    lugar_nacimiento,

                "talla":
                    talla,

                "peso":
                    peso,

                "tipo_sangre":
                    tipo_sangre

            },

            "ubicacion": {

                "direccion":
                    direccion,

                "barrio":
                    barrio,

                "telefono":
                    telefono,

                "celular":
                    celular

            },

            "informacion_linguistica":
                informacion_linguistica,

            "capacidades":
                capacidades,

            "observaciones":
                observaciones,

            "padre": {

                "nombre":
                    padre_nombre,

                "cedula":
                    padre_cedula,

                "telefono":
                    padre_telefono,

                "celular":
                    padre_celular,

                "ocupacion":
                    padre_ocupacion

            },

            "madre": {

                "nombre":
                    madre_nombre,

                "cedula":
                    madre_cedula,

                "telefono":
                    madre_telefono,

                "celular":
                    madre_celular,

                "ocupacion":
                    madre_ocupacion,

                "usuario":
                    madre_usuario

            },

            "tutor": {

                "nombre":
                    tutor_nombre,

                "parentesco":
                    tutor_parentesco,

                "cedula":
                    tutor_cedula,

                "celular":
                    tutor_celular,

                "ocupacion":
                    tutor_ocupacion

            },

            "compromiso":
                True,

            "estado":
                "activa",

            "tipo_matricula":
                (
                    "renovacion"
                    if estudiante_existente
                    else "nuevo_ingreso"
                ),

            "fecha_creacion":
                datetime.now()

        }


        # ==================================================
        # GUARDAR MATRÍCULA
        # ==================================================

        resultado_matricula = (
            db.matriculas.insert_one(
                matricula
            )
        )


        # ==================================================
        # CUENTA DE ACCESO DE LA MADRE/TUTORA
        #
        # Antes esto no existía: se guardaba el nombre de
        # usuario deseado (madre_usuario) dentro del estudiante,
        # pero nunca se creaba la cuenta correspondiente en
        # db.usuarios, así que nadie podía iniciar sesión.
        #
        # Si el usuario ya existe (por ejemplo, dos hermanos
        # con la misma madre) no se crea una cuenta duplicada,
        # se reutiliza la que ya tiene.
        # ==================================================

        password_generada_madre = None

        if madre_usuario:

            cuenta_madre = db.usuarios.find_one({
                "usuario": madre_usuario
            })

            if not cuenta_madre:

                password_generada_madre = str(
                    random.randint(100000, 999999)
                )

                db.usuarios.insert_one({
                    "usuario": madre_usuario,
                    "password": password_generada_madre,
                    "rol": "padre",
                    "activo": True,
                    "estudiante_codigo": codigo,
                    "fecha_creacion": datetime.now()
                })


        # ==================================================
        # MENSAJE FINAL
        # ==================================================

        if estudiante_existente:

            flash(
                f"Renovación realizada correctamente. "
                f"{nombre_completo} conserva el código "
                f"{codigo} y queda matriculado en "
                f"{grado}, sección {seccion}.",
                "success"
            )

        else:

            flash(
                f"¡Matrícula registrada correctamente! "
                f"Código: {codigo}",
                "success"
            )

        if password_generada_madre:

            flash(
                f"Se creó la cuenta de acceso para la madre/tutora "
                f"(usuario: {madre_usuario}, contraseña: "
                f"{password_generada_madre}). Compártela con ella "
                f"para que pueda ingresar al portal.",
                "info"
            )


        return redirect(
            url_for(
                "listar_matriculas"
            )
        )


    except Exception as e:


        flash(
            f"No se pudo registrar la matrícula: {e}",
            "danger"
        )


        return redirect(
            url_for(
                "agregar_matricula"
            )
        )


# ==========================================================
# VER MATRÍCULA
# ==========================================================

@app.route(
    "/admin/matricula/ver/<codigo>"
)
@role_required("admin", "director", "secretaria", "contadora")
def ver_matricula(codigo):

    try:

        # ==================================================
        # BUSCAR MATRÍCULA MÁS RECIENTE
        # ==================================================

        matricula = db.matriculas.find_one(

            {
                "codigo":
                    codigo
            },

            sort=[
                (
                    "anio_lectivo",
                    -1
                )
            ]

        )


        if not matricula:

            flash(
                "No se encontró la matrícula solicitada.",
                "warning"
            )

            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        # ==================================================
        # BUSCAR ESTUDIANTE
        # ==================================================

        estudiante = db.estudiantes.find_one({

            "_id":
                codigo

        })


        # ==================================================
        # HISTORIAL ACADÉMICO
        # ==================================================

        historial = list(

            db.matriculas.find({

                "estudiante_id":
                    codigo

            }).sort(

                "anio_lectivo",
                -1

            )

        )


        return render_template(

            "admin/ver_matricula.html",

            matricula=
                matricula,

            estudiante=
                estudiante,

            historial=
                historial

        )


    except Exception as e:


        flash(
            f"No se pudo cargar la matrícula: {e}",
            "danger"
        )


        return redirect(
            url_for(
                "listar_matriculas"
            )
        )


# ==========================================================
# EDITAR MATRÍCULA
# ==========================================================

@app.route(
    "/admin/matricula/editar/<codigo>",
    methods=["GET", "POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def editar_matricula(codigo):

    try:


        # ==================================================
        # BUSCAR ESTUDIANTE
        # ==================================================

        estudiante = db.estudiantes.find_one({

            "_id":
                codigo

        })


        if not estudiante:

            flash(
                "No se encontró el estudiante.",
                "warning"
            )

            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        # ==================================================
        # BUSCAR MATRÍCULA MÁS RECIENTE
        # ==================================================

        matricula = db.matriculas.find_one(

            {
                "estudiante_id":
                    codigo
            },

            sort=[
                (
                    "anio_lectivo",
                    -1
                )
            ]

        )


        if not matricula:

            flash(
                "No se encontró la matrícula.",
                "warning"
            )

            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        # ==================================================
        # GUARDAR CAMBIOS
        # ==================================================

        if request.method == "POST":

            # ==================================================
            # NOMBRES
            # ==================================================

            primer_nombre = request.form.get(
                "primer_nombre",
                ""
            ).strip()

            segundo_nombre = request.form.get(
                "segundo_nombre",
                ""
            ).strip()

            primer_apellido = request.form.get(
                "primer_apellido",
                ""
            ).strip()

            segundo_apellido = request.form.get(
                "segundo_apellido",
                ""
            ).strip()


            # ==================================================
            # DATOS PERSONALES
            # ==================================================

            fecha_nacimiento = request.form.get(
                "fecha_nacimiento",
                ""
            ).strip()

            edad = request.form.get(
                "edad",
                ""
            ).strip()

            genero = request.form.get(
                "genero",
                ""
            ).strip()

            lugar_nacimiento = request.form.get(
                "lugar_nacimiento",
                ""
            ).strip()


            # ==================================================
            # GRADO / SECCIÓN
            # ==================================================

            grado = request.form.get(
                "grado",
                ""
            ).strip()

            seccion = request.form.get(
                "seccion",
                ""
            ).strip()


            # ==================================================
            # FECHA MATRÍCULA
            # ==================================================

            fecha_matricula = request.form.get(
                "fecha_matricula",
                ""
            ).strip()


            # ==================================================
            # AÑO LECTIVO
            # ==================================================

            anio_lectivo = str(
                request.form.get(

                    "anio_lectivo",

                    matricula.get(
                        "anio_lectivo",
                        2026
                    )

                )
            ).strip()


            try:

                anio_lectivo = int(
                    anio_lectivo
                )

            except ValueError:

                anio_lectivo = matricula.get(
                    "anio_lectivo",
                    2026
                )


            # ==================================================
            # EVITAR CHOCAR CON OTRA MATRÍCULA DEL MISMO AÑO
            # ==================================================
            # Si el año lectivo cambió, verificar que el
            # estudiante no tenga ya otra matrícula (distinta
            # a la que se está editando) para ese año.

            if anio_lectivo != matricula.get("anio_lectivo"):

                choque = db.matriculas.find_one({

                    "estudiante_id":
                        codigo,

                    "anio_lectivo":
                        anio_lectivo,

                    "_id": {
                        "$ne": matricula["_id"]
                    }

                })

                if choque:

                    flash(
                        f"El estudiante {codigo} ya tiene "
                        f"otra matrícula registrada para "
                        f"{anio_lectivo}. No se puede "
                        f"cambiar el año lectivo a uno "
                        f"que ya está en uso.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "editar_matricula",
                            codigo=codigo
                        )
                    )


            # ==================================================
            # ESTADO
            # ==================================================

            estado = request.form.get(
                "estado",
                "activa"
            ).strip()


            # ==================================================
            # DATOS FÍSICOS
            # ==================================================

            talla = request.form.get(
                "talla",
                ""
            ).strip()

            peso = request.form.get(
                "peso",
                ""
            ).strip()

            tipo_sangre = request.form.get(
                "tipo_sangre",
                ""
            ).strip()


            # ==================================================
            # UBICACIÓN
            # ==================================================

            direccion = request.form.get(
                "direccion",
                ""
            ).strip()

            barrio = request.form.get(
                "barrio",
                ""
            ).strip()


            # ==================================================
            # CONTACTO
            # ==================================================

            telefono = request.form.get(
                "telefono",
                ""
            ).strip()

            celular = request.form.get(
                "celular",
                ""
            ).strip()


            # ==================================================
            # INFORMACIÓN LINGÜÍSTICA
            # ==================================================

            lengua_materna = request.form.get(
                "lengua_materna",
                ""
            ).strip()

            idioma = request.form.get(
                "idioma",
                ""
            ).strip()

            curso_ingles = request.form.get(
                "curso_ingles",
                ""
            ).strip()

            grupo_etnico = request.form.get(
                "grupo_etnico",
                ""
            ).strip()


            # ==================================================
            # CAPACIDADES
            # ==================================================

            capacidades = request.form.getlist(
                "capacidades"
            )


            if not capacidades:

                capacidades_texto = request.form.get(
                    "capacidades_texto",
                    ""
                ).strip()


                capacidades = [

                    item.strip()

                    for item in
                    capacidades_texto.split(",")

                    if item.strip()

                ]


            # ==================================================
            # OBSERVACIONES
            # ==================================================

            observaciones = request.form.get(
                "observaciones",
                ""
            ).strip()


            # ==================================================
            # PADRE
            # ==================================================

            padre_nombre = request.form.get(
                "padre_nombre",
                ""
            ).strip()

            padre_cedula = request.form.get(
                "padre_cedula",
                ""
            ).strip()

            padre_telefono = request.form.get(
                "padre_telefono",
                ""
            ).strip()

            padre_celular = request.form.get(
                "padre_celular",
                ""
            ).strip()

            padre_ocupacion = request.form.get(
                "padre_ocupacion",
                ""
            ).strip()


            # ==================================================
            # MADRE
            # ==================================================

            madre_nombre = request.form.get(
                "madre_nombre",
                ""
            ).strip()

            madre_cedula = request.form.get(
                "madre_cedula",
                ""
            ).strip()

            madre_telefono = request.form.get(
                "madre_telefono",
                ""
            ).strip()

            madre_celular = request.form.get(
                "madre_celular",
                ""
            ).strip()

            madre_ocupacion = request.form.get(
                "madre_ocupacion",
                ""
            ).strip()


            # ==================================================
            # TUTOR
            # ==================================================

            tutor_nombre = request.form.get(
                "tutor_nombre",
                ""
            ).strip()

            tutor_parentesco = request.form.get(
                "tutor_parentesco",
                ""
            ).strip()

            tutor_cedula = request.form.get(
                "tutor_cedula",
                ""
            ).strip()

            tutor_celular = request.form.get(
                "tutor_celular",
                ""
            ).strip()

            tutor_ocupacion = request.form.get(
                "tutor_ocupacion",
                ""
            ).strip()


            # ==================================================
            # NOMBRE COMPLETO
            # ==================================================

            nombre_completo = " ".join(

                parte

                for parte in [

                    primer_nombre,

                    segundo_nombre,

                    primer_apellido,

                    segundo_apellido

                ]

                if parte

            )


            # ==================================================
            # ACTUALIZAR ESTUDIANTE
            #
            # IMPORTANTE:
            # NUNCA MODIFICAMOS _id NI codigo.
            # ==================================================

            db.estudiantes.update_one(

                {
                    "_id":
                        codigo
                },

                {
                    "$set": {

                        "nombre":
                            nombre_completo,

                        "primer_nombre":
                            primer_nombre,

                        "segundo_nombre":
                            segundo_nombre,

                        "primer_apellido":
                            primer_apellido,

                        "segundo_apellido":
                            segundo_apellido,

                        "fecha_nacimiento":
                            fecha_nacimiento,

                        "edad":
                            edad,

                        "genero":
                            genero,

                        "lugar_nacimiento":
                            lugar_nacimiento,

                        "grado":
                            grado,

                        "seccion":
                            seccion,

                        "talla":
                            talla,

                        "peso":
                            peso,

                        "tipo_sangre":
                            tipo_sangre,

                        "direccion":
                            direccion,

                        "barrio":
                            barrio,

                        "telefono":
                            telefono,

                        "celular":
                            celular,

                        "informacion_linguistica": {

                            "lengua_materna":
                                lengua_materna,

                            "idioma":
                                idioma,

                            "curso_ingles":
                                curso_ingles,

                            "grupo_etnico":
                                grupo_etnico

                        },

                        "capacidades":
                            capacidades,

                        "observaciones":
                            observaciones,

                        "padre": {

                            "nombre":
                                padre_nombre,

                            "cedula":
                                padre_cedula,

                            "telefono":
                                padre_telefono,

                            "celular":
                                padre_celular,

                            "ocupacion":
                                padre_ocupacion

                        },

                        "madre": {

                            "nombre":
                                madre_nombre,

                            "cedula":
                                madre_cedula,

                            "telefono":
                                madre_telefono,

                            "celular":
                                madre_celular,

                            "ocupacion":
                                madre_ocupacion

                        },

                        "tutor": {

                            "nombre":
                                tutor_nombre,

                            "parentesco":
                                tutor_parentesco,

                            "cedula":
                                tutor_cedula,

                            "celular":
                                tutor_celular,

                            "ocupacion":
                                tutor_ocupacion

                        }

                    }

                }

            )


            # ==================================================
            # ACTUALIZAR MATRÍCULA
            # ==================================================

            db.matriculas.update_one(

                {
                    "_id":
                        matricula["_id"]
                },

                {
                    "$set": {

                        "grado":
                            grado,

                        "seccion":
                            seccion,

                        "fecha_matricula":
                            fecha_matricula,

                        "anio_lectivo":
                            anio_lectivo,

                        "estado":
                            estado,

                        "estudiante.nombre":
                            nombre_completo,

                        "estudiante.primer_nombre":
                            primer_nombre,

                        "estudiante.segundo_nombre":
                            segundo_nombre,

                        "estudiante.primer_apellido":
                            primer_apellido,

                        "estudiante.segundo_apellido":
                            segundo_apellido,

                        "estudiante.fecha_nacimiento":
                            fecha_nacimiento,

                        "estudiante.edad":
                            edad,

                        "estudiante.genero":
                            genero,

                        "estudiante.lugar_nacimiento":
                            lugar_nacimiento,

                        "estudiante.talla":
                            talla,

                        "estudiante.peso":
                            peso,

                        "estudiante.tipo_sangre":
                            tipo_sangre,

                        "ubicacion.direccion":
                            direccion,

                        "ubicacion.barrio":
                            barrio,

                        "ubicacion.telefono":
                            telefono,

                        "ubicacion.celular":
                            celular,

                        "informacion_linguistica": {

                            "lengua_materna":
                                lengua_materna,

                            "idioma":
                                idioma,

                            "curso_ingles":
                                curso_ingles,

                            "grupo_etnico":
                                grupo_etnico

                        },

                        "capacidades":
                            capacidades,

                        "observaciones":
                            observaciones,

                        "padre.nombre":
                            padre_nombre,

                        "padre.cedula":
                            padre_cedula,

                        "padre.telefono":
                            padre_telefono,

                        "padre.celular":
                            padre_celular,

                        "padre.ocupacion":
                            padre_ocupacion,

                        "madre.nombre":
                            madre_nombre,

                        "madre.cedula":
                            madre_cedula,

                        "madre.telefono":
                            madre_telefono,

                        "madre.celular":
                            madre_celular,

                        "madre.ocupacion":
                            madre_ocupacion,

                        "tutor.nombre":
                            tutor_nombre,

                        "tutor.parentesco":
                            tutor_parentesco,

                        "tutor.cedula":
                            tutor_cedula,

                        "tutor.celular":
                            tutor_celular,

                        "tutor.ocupacion":
                            tutor_ocupacion

                    }

                }

            )


            flash(
                f"Los datos de {nombre_completo} "
                f"fueron actualizados correctamente.",
                "success"
            )


            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        # ==================================================
        # MOSTRAR FORMULARIO
        # ==================================================

        return render_template(

            "admin/editar_matricula.html",

            estudiante=
                estudiante,

            matricula=
                matricula

        )


    except Exception as e:


        flash(
            f"No se pudo editar la matrícula: {e}",
            "danger"
        )


        return redirect(
            url_for(
                "listar_matriculas"
            )
        )


# ==========================================================
# DESACTIVAR MATRÍCULA
# ==========================================================

@app.route(
    "/admin/matricula/desactivar/<matricula_id>",
    methods=["POST"]
)
@role_required("admin", "director", "secretaria", "contadora")
def desactivar_matricula(matricula_id):

    try:


        # ==================================================
        # VALIDAR OBJECTID
        # ==================================================

        if not ObjectId.is_valid(
            matricula_id
        ):

            flash(
                "El identificador de la matrícula "
                "no es válido.",
                "danger"
            )

            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        object_id = ObjectId(
            matricula_id
        )


        # ==================================================
        # BUSCAR MATRÍCULA
        # ==================================================

        matricula = db.matriculas.find_one({

            "_id":
                object_id

        })


        if not matricula:

            flash(
                "No se encontró la matrícula.",
                "warning"
            )

            return redirect(
                url_for(
                    "listar_matriculas"
                )
            )


        # ==================================================
        # DESACTIVAR
        # ==================================================

        resultado = db.matriculas.update_one(

            {
                "_id":
                    object_id
            },

            {
                "$set": {

                    "estado":
                        "inactiva",

                    "fecha_desactivacion":
                        datetime.now()

                }

            }

        )


        # ==================================================
        # RESULTADO
        # ==================================================

        if resultado.modified_count > 0:

            flash(
                "Matrícula desactivada correctamente.",
                "success"
            )


        else:

            flash(
                "La matrícula ya estaba inactiva.",
                "info"
            )


        return redirect(
            url_for(
                "listar_matriculas"
            )
        )


    except Exception as e:


        flash(
            f"No se pudo desactivar la matrícula: {e}",
            "danger"
        )


        return redirect(
            url_for(
                "listar_matriculas"
            )
        )

# =========================
# LISTAR-ASIGNATURA
# =========================

@app.route("/asignaturas")
@role_required("admin", "director", "secretaria", "contadora")
def listar_asignaturas():

    asignaturas = list(
        db.asignaturas.find().sort("nombre", 1)
    )

    return render_template(
        "asignaturas/listar.html",
        asignaturas=asignaturas
    )


# =========================
# ASIGNAR ESTUDIANTE
# =========================
@app.route("/asignar_estudiantes", methods=["POST"])
@role_required("admin", "director", "secretaria", "contadora")
def asignar_estudiantes():

    db.matriculas.insert_one({
        "estudiante_id": request.form["estudiante_id"],
        "asignatura_id": request.form["asignatura_id"],
        "docente_id": request.form["docente_id"]
    })

    return redirect(url_for("listar_asignaturas"))


# =========================
#  EDITAR NOTA
# =========================

@app.route("/editar_nota/<id>", methods=["GET", "POST"])
@role_required("docente")
def editar_nota(id):

    nota = db.notas.find_one({"_id": ObjectId(id)})

    if request.method == "POST":

        db.notas.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "ep1": float(request.form["ep1"]),
                "ep2": float(request.form["ep2"]),
                "ep3": float(request.form["ep3"]),
                "ep4": float(request.form["ep4"]),
                "ep5": float(request.form["ep5"]),
                "ep6": float(request.form["ep6"]),
                "ep7": float(request.form["ep7"]),
                "ep8": float(request.form["ep8"]),
                "ep9": float(request.form["ep9"]),
                "ep10": float(request.form["ep10"]),
            }}
        )

        return redirect(url_for("docente_dashboard"))

# ==========================================================
# AGREGAR ASIGNATURA (CATÁLOGO — SIN DOCENTE/GRADO)
# ==========================================================
# A partir de esta versión, "asignaturas" es solo el catálogo
# de materias (ej. "Lengua y Literatura", "Educación Física").
# Quién la imparte, en qué grado y sección se define en
# "Asignar Clase" (ver asignar_clase()), no aquí.
# ==========================================================

@app.route("/asignaturas/agregar", methods=["GET", "POST"])
@role_required("admin", "director", "secretaria", "contadora")
def agregar_asignatura():

    if request.method == "POST":

        codigo = request.form.get("codigo", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()


        if not codigo or not nombre:

            flash(
                "Debe completar código y nombre de la asignatura.",
                "warning"
            )

            return redirect(url_for("agregar_asignatura"))

        existente = db.asignaturas.find_one({
            "codigo": codigo
        })

        if existente:

            flash(
                "Ya existe una asignatura con ese código en el catálogo.",
                "warning"
            )

            return redirect(url_for("agregar_asignatura"))

        resultado = db.asignaturas.insert_one({
            "codigo": codigo,
            "nombre": nombre,
            "activo": True
        })

        if resultado.inserted_id:

            flash(
                "Asignatura agregada al catálogo. Ahora puede asignarla a un "
                "docente en 'Asignar Clase'.",
                "success"
            )

        else:

            flash(
                "No fue posible guardar la asignatura.",
                "danger"
            )

        return redirect(url_for("listar_asignaturas"))

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    return render_template("asignaturas/agregar.html")


# ==========================================================
# ASIGNAR CLASE (ADMIN → DOCENTE)
# ==========================================================
# Aquí se conecta: catálogo de asignaturas + docentes +
# grados/secciones reales (tomados de los estudiantes ya
# matriculados) → escribe en "asignaciones_clase", que es la
# colección que sí lee el dashboard del docente.
#
# Soporta dos escenarios:
#   - Un docente da la MISMA materia en VARIOS grados/secciones
#     a la vez (ej. Educación Física, Informática, Ed. Cristiana):
#     el admin marca todas las casillas que correspondan en un
#     solo envío.
#   - Una materia se da por DISTINTO docente en cada grado
#     (ej. Lengua y Literatura): el admin repite este proceso
#     una vez por cada grado/sección, eligiendo el docente
#     correspondiente cada vez.
#
# Si una casilla (nivel+grado+sección+asignatura) ya tenía un
# docente activo asignado, se desactiva esa asignación anterior
# y se crea una nueva con el docente elegido (reasignación).
# ==========================================================

@app.route("/asignar_clase", methods=["GET", "POST"])
@role_required("admin", "director", "secretaria", "contadora")
def asignar_clase():

    # ======================================================
    # GRADOS Y SECCIONES REALES (según estudiantes matriculados)
    # ======================================================

    pipeline_grados = [
        {
            "$match": {
                "grado": {"$nin": [None, ""]},
                "seccion": {"$nin": [None, ""]}
            }
        },
        {
            "$group": {
                "_id": "$grado",
                "secciones": {"$addToSet": "$seccion"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    grados_raw = list(db.estudiantes.aggregate(pipeline_grados))

    grados_secciones = []

    for g in grados_raw:

        grados_secciones.append({
            "grado": g["_id"],
            "secciones": sorted(g["secciones"])
        })

    # ======================================================
    # DOCENTES Y ASIGNATURAS DISPONIBLES
    # ======================================================

    docentes = list(
        db.docentes.find({}).sort("nombre", 1)
    )

    asignaturas = list(
        db.asignaturas.find({"activo": {"$ne": False}}).sort("nombre", 1)
    )

    # ======================================================
    # ASIGNACIONES ACTIVAS (PARA ADVERTIR REASIGNACIONES
    # EN EL FORMULARIO ANTES DE GUARDAR)
    # ======================================================

    asignaciones_existentes = {}

    for a in db.asignaciones_clase.find({"activo": True}):

        clave = "|".join([
            str(a.get("asignatura_codigo", "")),
            str(a.get("nivel", "")),
            str(a.get("grado", "")),
            str(a.get("seccion", ""))
        ])

        asignaciones_existentes[clave] = {
            "docente_id": a.get("docente_id", ""),
            "docente_nombre": a.get("docente_nombre") or a.get("docente_id", "")
        }

    NIVELES = ["Preescolar", "Primaria"]

    if request.method == "POST":

        asignatura_id = request.form.get("asignatura_id", "").strip()
        docente_codigo = request.form.get("docente_id", "").strip().upper()
        nivel = request.form.get("nivel", "").strip()
        celdas = request.form.getlist("celdas")


        if not asignatura_id or not docente_codigo or not nivel or not celdas:

            flash(
                "Debe elegir asignatura, nivel, docente y al menos un "
                "grado/sección.",
                "warning"
            )

            return redirect(url_for("asignar_clase"))

        # ==================================================
        # BUSCAR ASIGNATURA (CATÁLOGO)
        # ==================================================

        filtro_asig = (
            {"_id": ObjectId(asignatura_id)}
            if ObjectId.is_valid(asignatura_id)
            else {"_id": asignatura_id}
        )

        asignatura = db.asignaturas.find_one(filtro_asig)

        if not asignatura:

            flash("La asignatura seleccionada no existe.", "danger")
            return redirect(url_for("asignar_clase"))

        # ==================================================
        # BUSCAR DOCENTE POR CÓDIGO
        # ==================================================

        docente = db.docentes.find_one({"codigo": docente_codigo})

        if not docente:

            flash("El docente seleccionado no existe.", "danger")
            return redirect(url_for("asignar_clase"))

        nuevas = 0
        reasignadas = 0
        sin_cambios = 0

        for celda in celdas:

            if "||" not in celda:
                continue

            grado, seccion = celda.split("||", 1)

            filtro_slot = {
                "asignatura_codigo": asignatura["codigo"],
                "nivel": nivel,
                "grado": grado,
                "seccion": seccion,
                "activo": True
            }

            existente = db.asignaciones_clase.find_one(filtro_slot)

            if existente:

                if existente.get("docente_id") == docente["codigo"]:

                    sin_cambios += 1
                    continue

                # ----------------------------------------------
                # REASIGNACIÓN: desactivar la anterior
                # ----------------------------------------------

                db.asignaciones_clase.update_one(
                    {"_id": existente["_id"]},
                    {
                        "$set": {
                            "activo": False,
                            "fecha_desactivacion": datetime.now()
                        }
                    }
                )

                reasignadas += 1

            else:

                nuevas += 1

            db.asignaciones_clase.insert_one({
                "asignatura_id": asignatura["_id"],
                "asignatura_codigo": asignatura["codigo"],
                "asignatura_nombre": asignatura["nombre"],
                "nivel": nivel,
                "grado": grado,
                "seccion": seccion,
                "docente_id": docente["codigo"],
                "docente_nombre": docente.get("nombre", ""),
                "activo": True,
                "fecha_asignacion": datetime.now()
            })

        flash(
            f"Listo: {nuevas} clase(s) nueva(s), {reasignadas} "
            f"reasignada(s), {sin_cambios} sin cambios.",
            "success"
        )

        return redirect(url_for("asignar_clase"))

    return render_template(
        "admin/asignar_clase.html",
        docentes=docentes,
        asignaturas=asignaturas,
        grados_secciones=grados_secciones,
        niveles=NIVELES,
        asignaciones_existentes=asignaciones_existentes
    )


# ==========================================================
# GESTIONAR ASIGNACIONES (VER / DESACTIVAR)
# ==========================================================

@app.route("/admin/asignaciones")
@role_required("admin", "director", "secretaria", "contadora")
def gestionar_asignaciones():

    # ==================================================
    # SE USA $lookup PARA TRAER EL NOMBRE ACTUAL DEL
    # DOCENTE DESDE LA COLECCIÓN "docentes", EN VEZ DE
    # CONFIAR EN EL "docente_nombre" QUE SE GUARDÓ AL
    # MOMENTO DE ASIGNAR (ESE DATO PUEDE QUEDAR VACÍO O
    # DESACTUALIZADO SI EL DOCENTE NO TENÍA NOMBRE EN
    # ESE MOMENTO, O SI SU NOMBRE CAMBIÓ DESPUÉS).
    #
    # CADENA DE RESPALDO PARA EL NOMBRE A MOSTRAR:
    #   1) nombre actual del docente (colección docentes)
    #   2) docente_nombre guardado en la asignación
    #   3) docente_id (código)
    #   4) "Sin asignar"
    # ==================================================

    asignaciones = list(
        db.asignaciones_clase.aggregate([

            {"$match": {"activo": True}},

            {
                "$lookup": {
                    "from": "docentes",
                    "localField": "docente_id",
                    "foreignField": "codigo",
                    "as": "docente_info"
                }
            },

            {
                "$addFields": {
                    "docente_nombre_mostrar": {
                        "$let": {
                            "vars": {
                                "nombre_actual": {
                                    "$arrayElemAt": [
                                        "$docente_info.nombre",
                                        0
                                    ]
                                }
                            },
                            "in": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$ne": ["$$nombre_actual", None]},
                                            {"$ne": ["$$nombre_actual", ""]}
                                        ]
                                    },
                                    "$$nombre_actual",
                                    {
                                        "$cond": [
                                            {
                                                "$and": [
                                                    {"$ne": ["$docente_nombre", None]},
                                                    {"$ne": ["$docente_nombre", ""]}
                                                ]
                                            },
                                            "$docente_nombre",
                                            {
                                                "$ifNull": [
                                                    "$docente_id",
                                                    "Sin asignar"
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            },

            {
                "$sort": {
                    "nivel": 1,
                    "grado": 1,
                    "seccion": 1,
                    "asignatura_nombre": 1
                }
            }
        ])
    )

    return render_template(
        "admin/gestionar_asignaciones.html",
        asignaciones=asignaciones
    )


@app.route("/admin/asignaciones/desactivar/<id>")
@role_required("admin", "director", "secretaria", "contadora")
def desactivar_asignacion(id):

    filtro = (
        {"_id": ObjectId(id)}
        if ObjectId.is_valid(id)
        else {"_id": id}
    )

    db.asignaciones_clase.update_one(
        filtro,
        {
            "$set": {
                "activo": False,
                "fecha_desactivacion": datetime.now()
            }
        }
    )

    flash("Asignación desactivada.", "success")

    return redirect(url_for("gestionar_asignaciones"))


@app.route("/admin/asignaciones/eliminar/<id>", methods=["POST"])
@role_required("admin", "director", "secretaria", "contadora")
def eliminar_asignacion(id):

    filtro = (
        {"_id": ObjectId(id)}
        if ObjectId.is_valid(id)
        else {"_id": id}
    )

    resultado = db.asignaciones_clase.delete_one(filtro)

    if resultado.deleted_count == 1:
        flash("Asignación eliminada correctamente.", "success")
    else:
        flash("No se encontró la asignación a eliminar.", "danger")

    return redirect(url_for("gestionar_asignaciones"))


# ==========================================================
# EDITAR ASIGNATURA (CATÁLOGO — SIN DOCENTE/GRADO)
# ==========================================================

@app.route("/asignaturas/editar/<id>", methods=["GET", "POST"])
@role_required("admin", "director", "secretaria", "contadora")
def editar_asignatura(id):

    filtro = (
        {"_id": ObjectId(id)}
        if ObjectId.is_valid(id)
        else {"_id": id}
    )

    asignatura = db.asignaturas.find_one(filtro)

    if not asignatura:

        flash("Asignatura no encontrada.", "danger")
        return redirect(url_for("listar_asignaturas"))

    if request.method == "POST":

        codigo = request.form.get("codigo", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()

        if not codigo or not nombre:

            flash("Debe completar código y nombre.", "warning")
            return redirect(url_for("editar_asignatura", id=id))

        db.asignaturas.update_one(
            filtro,
            {
                "$set": {
                    "codigo": codigo,
                    "nombre": nombre
                }
            }
        )

        flash("Asignatura actualizada.", "success")
        return redirect(url_for("listar_asignaturas"))

    return render_template(
        "asignaturas/editar.html",
        asignatura=asignatura
    )


# ==========================================================
# ELIMINAR ASIGNATURA
# ==========================================================

@app.route(
    "/asignaturas/eliminar/<id>"
)
@role_required("admin", "director", "secretaria", "contadora")
def eliminar_asignatura(id):


    # ======================================================
    # CONSTRUIR FILTRO
    # ======================================================

    if ObjectId.is_valid(id):

        filtro = {
            "_id": ObjectId(id)
        }

    else:

        filtro = {
            "_id": id
        }

    # ======================================================
    # ELIMINAR
    # ======================================================

    resultado = db.asignaturas.delete_one(
        filtro
    )

    if resultado.deleted_count > 0:

        flash(
            "Asignatura eliminada correctamente.",
            "success"
        )

    else:

        flash(
            "Asignatura no encontrada.",
            "danger"
        )

    return redirect(
        url_for("listar_asignaturas")
    )

   
# =========================
# PANEL DE REPORTES
# =========================

@app.route("/admin/reportes")
@role_required("admin", "director", "secretaria", "contadora")
def reportes_admin():

    return render_template(
        "admin/reportes.html"
    )


# =========================
# REPORTE DE ESTUDIANTES
# =========================

@app.route("/admin/reporte/estudiantes")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_estudiantes():


    estudiantes = list(
        db.estudiantes.find().sort(
            "nombre",
            1
        )
    )


    return render_template(
        "admin/reporte_estudiantes.html",
        estudiantes=estudiantes
    )


@app.route("/admin/reporte/estudiantes/pdf")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_estudiantes_pdf():

    estudiantes = list(
        db.estudiantes.find().sort(
            "nombre",
            1
        )
    )

    html_render = render_template(
        "admin/reporte_estudiantes_pdf.html",
        estudiantes=estudiantes,
        fecha_generado=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    pdf_bytes = HTML(
        string=html_render,
        base_url=request.url_root
    ).write_pdf()

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="reporte_estudiantes.pdf"
    )


# =========================
# REPORTE DE DOCENTES
# =========================

@app.route("/admin/reporte/docentes")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_docentes():


    docentes = list(
        db.docentes.find().sort(
            "nombre",
            1
        )
    )


    return render_template(
        "admin/reporte_docentes.html",
        docentes=docentes
    )


@app.route("/admin/reporte/docentes/pdf")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_docentes_pdf():

    docentes = list(
        db.docentes.find().sort(
            "nombre",
            1
        )
    )

    html_render = render_template(
        "admin/reporte_docentes_pdf.html",
        docentes=docentes,
        fecha_generado=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    pdf_bytes = HTML(
        string=html_render,
        base_url=request.url_root
    ).write_pdf()

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="reporte_docentes.pdf"
    )


# =========================
# REPORTE DE MATRÍCULAS
# =========================

@app.route("/admin/reporte/matriculas")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_matriculas():


    matriculas = list(
        db.matriculas.aggregate([

            {
                "$lookup": {
                    "from": "estudiantes",
                    "localField": "estudiante_id",
                    "foreignField": "_id",
                    "as": "estudiante"
                }
            },

            {
                "$unwind": {
                    "path": "$estudiante",
                    "preserveNullAndEmptyArrays": True
                }
            },

            {
                "$sort": {
                    "fecha_matricula": -1
                }
            }

        ])
    )


    return render_template(
        "admin/reporte_matriculas.html",
        matriculas=matriculas
    )


@app.route("/admin/reporte/matriculas/pdf")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_matriculas_pdf():

    matriculas = list(
        db.matriculas.aggregate([

            {
                "$lookup": {
                    "from": "estudiantes",
                    "localField": "estudiante_id",
                    "foreignField": "_id",
                    "as": "estudiante"
                }
            },

            {
                "$unwind": {
                    "path": "$estudiante",
                    "preserveNullAndEmptyArrays": True
                }
            },

            {
                "$sort": {
                    "fecha_matricula": -1
                }
            }

        ])
    )

    html_render = render_template(
        "admin/reporte_matriculas_pdf.html",
        matriculas=matriculas,
        fecha_generado=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    pdf_bytes = HTML(
        string=html_render,
        base_url=request.url_root
    ).write_pdf()

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="reporte_matriculas.pdf"
    )

# =========================
# REPORTE ACADÉMICO
# =========================

@app.route("/admin/reporte/academico")
@role_required("admin", "director", "secretaria", "contadora")
def reporte_academico():


    total_estudiantes = db.estudiantes.count_documents({})

    total_docentes = db.docentes.count_documents({})

    total_asignaturas = db.asignaturas.count_documents({})

    total_matriculas = db.matriculas.count_documents({})


    # estudiantes por grado

    grados = list(
        db.estudiantes.aggregate([
            {
                "$group":{
                    "_id":"$grado",
                    "cantidad":{
                        "$sum":1
                    }
                }
            }
        ])
    )

    return render_template(
        "admin/reporte_academico.html",

        total_estudiantes=total_estudiantes,

        total_docentes=total_docentes,

        total_asignaturas=total_asignaturas,

        total_matriculas=total_matriculas,

        grados=grados

    )

# ==========================================================
# REPORTE DE ESTUDIANTES POR GRADO
# ==========================================================

@app.route(
    "/admin/reportes/estudiantes-por-grado",
    methods=["GET"]
)
@role_required("admin", "director", "secretaria", "contadora")
def reporte_estudiantes_por_grado():

    try:

        # ==================================================
        # GRADO SELECCIONADO
        # ==================================================

        grado_seleccionado = request.args.get(
            "grado",
            ""
        ).strip()

        # ==================================================
        # OBTENER GRADOS DISPONIBLES
        # DIRECTAMENTE DESDE ESTUDIANTES
        # ==================================================

        grados = db.estudiantes.distinct(
            "grado"
        )

        grados = [
            str(grado).strip()
            for grado in grados
            if grado
        ]

        grados = sorted(
            list(set(grados)),
            key=lambda x: x.lower()
        )

        # ==================================================
        # ESTUDIANTES
        # ==================================================

        estudiantes = []

        if grado_seleccionado:

            estudiantes = list(
                db.estudiantes.find(
                    {
                        "grado": grado_seleccionado
                    }
                )
            )

            # ==================================================
            # ORDENAR POR APELLIDOS Y NOMBRES
            # ==================================================

            estudiantes.sort(
                key=lambda estudiante: (
                    str(
                        estudiante.get(
                            "primer_apellido",
                            ""
                        )
                    ).upper(),

                    str(
                        estudiante.get(
                            "segundo_apellido",
                            ""
                        )
                    ).upper(),

                    str(
                        estudiante.get(
                            "primer_nombre",
                            ""
                        )
                    ).upper()
                )
            )

        # ==================================================
        # TOTAL
        # ==================================================

        total_estudiantes = len(
            estudiantes
        )

        # ==================================================
        # RENDERIZAR
        # ==================================================

        return render_template(
            "admin/reporte_estudiantes_grado.html",

            grados=grados,

            grado_seleccionado=
                grado_seleccionado,

            estudiantes=
                estudiantes,

            total_estudiantes=
                total_estudiantes
        )

    except Exception as e:


        flash(
            f"No se pudo generar el reporte: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

# =========================
# VERIFICAR RUTAS
# =========================


for ruta in app.url_map.iter_rules():
    pass


# ==========================================================
# MOSTRAR RUTAS DE COMUNICADOS
# ==========================================================


for regla in app.url_map.iter_rules():

    if "comunicado" in str(regla).lower():

        pass


# =========================
# RUN
# =========================
if __name__ == "__main__":


    for ruta in app.url_map.iter_rules():
        pass


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )