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
    send_file
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

from config.database import db

# ==========================================================
# USUARIOS DOCENTES
# ==========================================================

usuarios_docentes = [
    {
        "_id": "USR007",
        "usuario": "daniela",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC007",
        "activo": True
    },
    {
        "_id": "USR009",
        "usuario": "anielka",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC009",
        "activo": True
    },
    {
        "_id": "USR010",
        "usuario": "erlin",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC010",
        "activo": True
    },
    {
        "_id": "USR011",
        "usuario": "carla",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC011",
        "activo": True
    }
]

for usuario_docente in usuarios_docentes:

    db.usuarios.update_one(
        {"_id": usuario_docente["_id"]},
        {"$set": usuario_docente},
        upsert=True
    )

print("==============================================")
print("USUARIOS DOCENTES VERIFICADOS")
print("==============================================")
print("DANIELA:", db.usuarios.find_one({"usuario": "daniela"}))
print("ERLIN:", db.usuarios.find_one({"usuario": "erlin"}))
print("==============================================")
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

        user = db["usuarios"].find_one({
            "usuario": usuario
        })

        # --------------------------------------------------
        # BUSCAR SIN IMPORTAR MAYÚSCULAS
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

            print("==============================================")
            print("LOGIN DOCENTE")
            print("Usuario:", session["usuario"])
            print("Usuario ID:", session["id"])
            print("Docente ID:", session["docente_id"])
            print("==============================================")

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

    print("==============================================")
    print("🌐 CIEM ACADÉMICO")
    print("🌐 SERVIDOR: http://127.0.0.1:5000")
    print("🔐 LOGIN: http://127.0.0.1:5000/login")
    print("==============================================")

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

            print("SESSION DEBUG:", session)
            print("ROL SESSION:", session.get("rol"))

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
    print("Usuario encontrado:", user)
    print("Contraseña BD:", user.get("password"))
    print("Contraseña ingresada:", password)
    print("¿Coinciden?:", str(user.get("password")).strip() == password)



print("\n========================================")
print("🔎 ASIGNATURAS DE EVERT EN MONGODB")
print("========================================")

evert = db.docentes.find_one({
    "usuario": "evert"
})

if evert:

    evert_id = str(evert["_id"])

    print("DOCENTE:", evert.get("nombre"))
    print("ID:", evert_id)

    asignaturas_evert = list(
        db.asignaturas.find({
            "docente_id": evert_id
        })
    )

    print("TOTAL:", len(asignaturas_evert))

    for a in asignaturas_evert:
        print(
            a.get("_id"),
            "|",
            a.get("nombre"),
            "|",
            a.get("nivel"),
            "|",
            a.get("grado"),
            "| DOCENTE:",
            a.get("docente_id")
        )

print("========================================\n")
# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin", endpoint="admin_dashboard")
@role_required("admin")
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
@role_required("admin")
def crear_comunicado():

    try:

        print("==========================================")
        print("📢 CREANDO COMUNICADO")
        print("==========================================")

        print("DATOS RECIBIDOS:")
        print(request.form.to_dict())

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
        print("==========================================")
        print("🔎 VERIFICANDO COMUNICADOS")
        print("==========================================")

        print(
            "TOTAL COMUNICADOS:",
            db.comunicaciones.count_documents({})
        )

        ultimo = db.comunicaciones.find_one(
            {"_id": resultado.inserted_id}
        )

        print("ÚLTIMO COMUNICADO:")
        print(ultimo)

        print("==========================================")
        # ==================================================
        # VERIFICAR COMUNICADO GUARDADO
        # ==================================================

        print("==========================================")
        print("🔎 VERIFICANDO COLECCIÓN comunicaciones")
        print("==========================================")

        total_comunicados = db.comunicaciones.count_documents({})

        print(
            "TOTAL COMUNICADOS EN MONGODB:",
            total_comunicados
        )

        for comunicado_db in db.comunicaciones.find():
            print("COMUNICADO ENCONTRADO:")
            print(comunicado_db)

        print("==========================================")
        print("==========================================")
        print("✅ COMUNICADO GUARDADO")
        print("ID:", resultado.inserted_id)
        print("TÍTULO:", titulo)
        print("DESTINATARIO:", destinatario)
        print("GRADO:", grado)
        print("==========================================")

        flash(
            "Comunicado publicado correctamente.",
            "success"
        )

        return redirect(
            url_for("admin_comunicados")
        )

    except Exception as e:

        print("==========================================")
        print("❌ ERROR AL CREAR COMUNICADO")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

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
@role_required("admin")
def admin_comunicados():

    try:

        print("==========================================")
        print("📢 ADMIN - COMUNICADOS")
        print("==========================================")

        comunicados = list(
            db.comunicaciones.find().sort(
                "fecha_creacion",
                -1
            )
        )

        print(
            "TOTAL COMUNICADOS:",
            len(comunicados)
        )

        return render_template(
            "admin/comunicados.html",
            comunicados=comunicados
        )

    except Exception as e:

        print("==========================================")
        print("❌ ERROR AL CARGAR COMUNICADOS")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

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
@role_required("admin")
def listar_estudiantes_admin():

    try:

        estudiantes = list(
            db.estudiantes.find().sort(
                "nombre",
                1
            )
        )
        print("==========================================")
        print("CÓDIGOS QUE REALMENTE EXISTEN")
        print("==========================================")

        for e in estudiantes[:10]:

            print("NOMBRE:", e.get("nombre"))
            print("_id:", e.get("_id"))
            print("codigo:", e.get("codigo"))
            print("------------------------------------------")
        print("\n")
        print("==================================================")
        print("PRUEBA LISTAR ESTUDIANTES ADMIN")
        print("==================================================")

        for e in estudiantes:

            print("------------------------------------------")

            print("NOMBRE:", repr(e.get("nombre")))

            print("_id:", repr(e.get("_id")))

            print("codigo:", repr(e.get("codigo")))

            print("grado:", repr(e.get("grado")))

            print("seccion:", repr(e.get("seccion")))

            print("TIPO _id:", type(e.get("_id")).__name__)

            print("TIPO codigo:", type(e.get("codigo")).__name__)

            print("------------------------------------------")

        print("==================================================")
        print("TOTAL:", len(estudiantes))
        print("==================================================")
        print("\n")

        return render_template(
            "admin/estudiantes.html",
            estudiantes=estudiantes
        )

    except Exception as e:

        print("==================================================")
        print("ERROR LISTANDO ESTUDIANTES")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==================================================")

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
@role_required("admin")
def editar_estudiante(id):

    print("==========================================")
    print("✏️ EDITAR ESTUDIANTE")
    print("ID RECIBIDO:", id)
    print("==========================================")

    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = db.estudiantes.find_one({
        "_id": id
    })

    print("ESTUDIANTE ENCONTRADO:")
    print(estudiante)

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
@role_required("admin")
def eliminar_comunicado(id):

    try:

        print("==========================================")
        print("🗑️ ELIMINANDO COMUNICADO")
        print("ID:", id)
        print("==========================================")

        resultado = db.comunicaciones.delete_one({
            "_id": ObjectId(id)
        })

        if resultado.deleted_count == 1:

            print("✅ COMUNICADO ELIMINADO")

            flash(
                "Comunicado eliminado correctamente.",
                "success"
            )

        else:

            print("⚠️ COMUNICADO NO ENCONTRADO")

            flash(
                "El comunicado no fue encontrado.",
                "warning"
            )

        return redirect(
            url_for("admin_comunicados")
        )

    except Exception as e:

        print("==========================================")
        print("❌ ERROR AL ELIMINAR COMUNICADO")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

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
@role_required("admin")
def historial_comunicados():

    try:

        print("==========================================")
        print("📋 HISTORIAL DE COMUNICADOS")
        print("==========================================")

        comunicados = list(
            db.comunicaciones.find().sort(
                "fecha_creacion",
                -1
            )
        )

        print(
            "TOTAL HISTORIAL:",
            len(comunicados)
        )

        return render_template(
            "admin/historial_comunicados.html",
            comunicados=comunicados
        )

    except Exception as e:

        print("==========================================")
        print("❌ ERROR AL CARGAR HISTORIAL")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

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
@role_required("admin")
def comunicado_whatsapp(id):

    try:

        print("==========================================")
        print("📱 PREPARANDO WHATSAPP")
        print("ID COMUNICADO:", id)
        print("==========================================")

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

        print("COMUNICADO ENCONTRADO:")
        print(comunicado)

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

        print(
            "ESTUDIANTES ENCONTRADOS:",
            len(estudiantes)
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

        print("==========================================")
        print(
            "📱 CONTACTOS CON TELÉFONO:",
            len(contactos)
        )
        print("==========================================")

        # ==================================================
        # MOSTRAR PÁGINA
        # ==================================================

        return render_template(
            "admin/comunicado_whatsapp.html",
            comunicado=comunicado,
            contactos=contactos
        )

    except Exception as e:

        print("==========================================")
        print("❌ ERROR WHATSAPP")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

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
@role_required("admin")
def eliminar_estudiante(id):

    print("==========================================")
    print("🗑️ ELIMINAR ESTUDIANTE")
    print("ID RECIBIDO:", id)
    print("==========================================")

    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = db.estudiantes.find_one({
        "_id": id
    })

    print("ESTUDIANTE ENCONTRADO:")
    print(estudiante)

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

    print(
        "ESTUDIANTES ELIMINADOS:",
        resultado.deleted_count
    )

    # ======================================================
    # ELIMINAR MATRÍCULA RELACIONADA
    # ======================================================

    resultado_matricula = db.matriculas.delete_many({
        "estudiante_id": id
    })

    print(
        "MATRÍCULAS ELIMINADAS:",
        resultado_matricula.deleted_count
    )

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
@role_required("admin")
def listar_docentes():

    docentes = list(
        db.docentes.find().sort(
            "nombre",
            1
        )
    )

    print("\n========== DOCENTES ==========")

    for d in docentes:

        print("DOCUMENTO:")
        print(d)

        print("ID:", d["_id"])
        print("TIPO:", type(d["_id"]))

        print("----------------------")

    print("==============================\n")

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
@role_required("admin")
def editar_docente(id):

    print("==========================")
    print("EDITAR DOCENTE")
    print("ID RECIBIDO:", id)

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

    print("DOCENTE ENCONTRADO:")
    print(docente)

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
@role_required("admin")
def eliminar_docente(id):

    print("==========================")
    print("ELIMINAR DOCENTE")
    print("ID RECIBIDO:", id)
    print("==========================")

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

        print(
            "DOCENTE ELIMINADO:",
            docente["_id"]
        )

        return redirect(
            url_for("listar_docentes")
        )

    except Exception as e:

        print("==========================")
        print("ERROR AL ELIMINAR DOCENTE")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================")

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
@role_required("admin")
def agregar_docente():

    if request.method == "POST":

        docente = {

            "codigo": request.form["codigo"],
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
@role_required("admin")
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

        print("==========================================")
        print("LISTADO DE MATRÍCULAS")
        print("TOTAL MATRÍCULAS:", len(matriculas))
        print("==========================================")

        return render_template(
            "admin/matriculas.html",
            matriculas=matriculas
        )

    except Exception as e:

        print("==========================================")
        print("ERROR AL LISTAR MATRÍCULAS")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

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

            print("==========================================")
            print("ESTUDIANTE ENCONTRADO POR CÓDIGO")
            print(
                "CÓDIGO:",
                estudiante.get("_id")
            )
            print(
                "NOMBRE:",
                estudiante.get(
                    "nombre",
                    ""
                )
            )
            print("==========================================")


            return estudiante


        print("==========================================")
        print(
            "EL CÓDIGO INDICADO NO EXISTE:",
            codigo_existente
        )
        print("==========================================")


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

        print(
            "NO HAY DATOS SUFICIENTES PARA BUSCAR "
            "ESTUDIANTE."
        )

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

        print("==========================================")
        print(
            "NO SE ENCONTRÓ ESTUDIANTE POR NOMBRE"
        )
        print("==========================================")


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


            print("==========================================")
            print(
                "ESTUDIANTE EXISTENTE IDENTIFICADO"
            )
            print(
                "CÓDIGO:",
                estudiante.get("_id")
            )
            print(
                "NOMBRE:",
                estudiante.get(
                    "nombre",
                    ""
                )
            )
            print(
                "FECHA:",
                estudiante.get(
                    "fecha_nacimiento",
                    ""
                )
            )
            print("==========================================")


            return estudiante


        # ==================================================
        # VARIAS COINCIDENCIAS
        # ==================================================

        if len(coincidencias) > 1:

            print("==========================================")
            print(
                "ADVERTENCIA: EXISTEN VARIOS "
                "ESTUDIANTES CON LOS MISMOS DATOS."
            )
            print(
                "NO SE REUTILIZARÁ NINGÚN CÓDIGO."
            )


            for estudiante in coincidencias:

                print(
                    "CANDIDATO:",
                    estudiante.get("_id"),
                    estudiante.get(
                        "nombre",
                        ""
                    )
                )


            print("==========================================")


            return None


        # ==================================================
        # NOMBRE ENCONTRADO PERO FECHA NO COINCIDE
        # ==================================================

        print("==========================================")
        print(
            "EL NOMBRE COINCIDE, PERO LA FECHA "
            "DE NACIMIENTO NO COINCIDE."
        )
        print(
            "SE CONSIDERARÁ COMO ESTUDIANTE NUEVO."
        )
        print("==========================================")


        return None


    # ======================================================
    # SIN FECHA
    #
    # NO REUTILIZAMOS AUTOMÁTICAMENTE EL CÓDIGO.
    # ======================================================

    print("==========================================")
    print(
        "SE ENCONTRARON CANDIDATOS POR NOMBRE,"
    )
    print(
        "PERO NO HAY FECHA DE NACIMIENTO."
    )
    print(
        "NO SE REUTILIZARÁ AUTOMÁTICAMENTE "
        "NINGÚN CÓDIGO."
    )
    print("==========================================")


    return None


# ==========================================================
# AGREGAR / RENOVAR MATRÍCULA
# ==========================================================

@app.route(
    "/admin/matricula/agregar",
    methods=["GET", "POST"]
)
@role_required("admin")
def agregar_matricula():

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    if request.method == "GET":

        return render_template(
            "admin/agregar_matricula.html"
        )


    try:

        print("==========================================")
        print("NUEVA MATRÍCULA / RENOVACIÓN")
        print("DATOS RECIBIDOS:")
        print(request.form.to_dict())
        print("==========================================")


        # ==================================================
        # CÓDIGO DEL ESTUDIANTE SELECCIONADO
        # ==================================================

        codigo_existente = request.form.get(
            "codigo_estudiante",
            ""
        ).strip()


        print("==========================================")
        print(
            "CÓDIGO RECIBIDO DESDE EL FORMULARIO:"
        )
        print(
            repr(codigo_existente)
        )
        print("==========================================")


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

                print("==========================================")
                print(
                    "CÓDIGO SELECCIONADO NO EXISTE:",
                    codigo_existente
                )
                print("==========================================")


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


            print("==========================================")
            print(
                "ESTUDIANTE SELECCIONADO "
                "DESDE EL FORMULARIO"
            )
            print(
                "CÓDIGO CONSERVADO:",
                codigo
            )
            print(
                "NOMBRE:",
                estudiante_existente.get(
                    "nombre",
                    ""
                )
            )
            print("==========================================")


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


                print("==========================================")
                print(
                    "ESTUDIANTE EXISTENTE "
                    "IDENTIFICADO"
                )
                print(
                    "CÓDIGO CONSERVADO:",
                    codigo
                )
                print("==========================================")


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


                print("==========================================")
                print(
                    "ESTUDIANTE NUEVO"
                )
                print(
                    "CÓDIGO GENERADO:",
                    codigo
                )
                print("==========================================")


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


            print("==========================================")
            print(
                "MATRÍCULA DUPLICADA EVITADA"
            )
            print(
                "CÓDIGO:",
                codigo
            )
            print(
                "AÑO:",
                anio_lectivo
            )
            print("==========================================")


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


            print("==========================================")
            print(
                "ESTUDIANTE NUEVO CREADO:"
            )
            print(
                "CÓDIGO:",
                codigo
            )
            print("==========================================")


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


            print("==========================================")
            print(
                "ESTUDIANTE EXISTENTE ACTUALIZADO"
            )
            print(
                "CÓDIGO CONSERVADO:",
                codigo
            )
            print("==========================================")


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


        print("==========================================")
        print(
            "MATRÍCULA GUARDADA"
        )
        print(
            "CÓDIGO:",
            codigo
        )
        print(
            "AÑO:",
            anio_lectivo
        )
        print(
            "GRADO:",
            grado
        )
        print(
            "SECCIÓN:",
            seccion
        )
        print(
            "TIPO:",
            matricula[
                "tipo_matricula"
            ]
        )
        print(
            "ID:",
            resultado_matricula.inserted_id
        )
        print("==========================================")


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


        return redirect(
            url_for(
                "listar_matriculas"
            )
        )


    except Exception as e:

        print("==========================================")
        print(
            "ERROR AL GUARDAR MATRÍCULA"
        )
        print(
            "TIPO:",
            type(e).__name__
        )
        print(
            "ERROR:",
            repr(e)
        )
        print("==========================================")


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
@role_required("admin")
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

        print(
            "ERROR AL VER MATRÍCULA:",
            repr(e)
        )


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
@role_required("admin")
def editar_matricula(codigo):

    try:

        print("==========================================")
        print(
            "EDITAR MATRÍCULA"
        )
        print(
            "CÓDIGO:",
            codigo
        )
        print("==========================================")


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

            anio_lectivo = request.form.get(

                "anio_lectivo",

                matricula.get(
                    "anio_lectivo",
                    2026
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


            print("==========================================")
            print(
                "MATRÍCULA ACTUALIZADA"
            )
            print(
                "CÓDIGO:",
                codigo
            )
            print(
                "NUEVO GRADO:",
                grado
            )
            print(
                "NUEVA SECCIÓN:",
                seccion
            )
            print(
                "AÑO:",
                anio_lectivo
            )
            print("==========================================")


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

        print("==========================================")
        print(
            "ERROR AL EDITAR MATRÍCULA"
        )
        print(
            "TIPO:",
            type(e).__name__
        )
        print(
            "ERROR:",
            repr(e)
        )
        print("==========================================")


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
@role_required("admin")
def desactivar_matricula(matricula_id):

    try:

        print("==========================================")
        print(
            "DESACTIVAR MATRÍCULA"
        )
        print(
            "ID:",
            matricula_id
        )
        print("==========================================")


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


            print(
                "MATRÍCULA DESACTIVADA:",
                matricula.get(
                    "codigo"
                )
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

        print("==========================================")
        print(
            "ERROR AL DESACTIVAR MATRÍCULA"
        )
        print(
            "TIPO:",
            type(e).__name__
        )
        print(
            "ERROR:",
            repr(e)
        )
        print("==========================================")


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
@role_required("admin")
def listar_asignaturas():

    asignaturas = list(
        db.asignaturas.find().sort("nombre", 1)
    )

    return render_template(
        "asignaturas/listar.html",
        asignaturas=asignaturas
    )


# =========================================================
# ASIGNAR CLASE A DOCENTE
# COLECCIÓN OFICIAL: db.clase
# =========================================================

@app.route("/asignar-clase", methods=["GET", "POST"])
@role_required("admin")
def asignar_clase():

    print("========================================")
    print("👨‍🏫 ASIGNAR CLASE")
    print("📂 COLECCIÓN OFICIAL: db.clase")
    print("========================================")

    # =====================================================
    # 1. OBTENER ASIGNATURAS
    # =====================================================

    asignaturas = list(
        db.asignaturas.find({
            "activo": {
                "$ne": False
            }
        }).sort(
            "nombre",
            1
        )
    )

    # =====================================================
    # 2. OBTENER DOCENTES
    # =====================================================

    docentes = list(
        db.docentes.find({
            "activo": {
                "$ne": False
            }
        }).sort(
            "nombre",
            1
        )
    )

    # =====================================================
    # 3. PROCESAR FORMULARIO
    # =====================================================

    if request.method == "POST":

        print("")
        print("========================================")
        print("📥 DATOS RECIBIDOS DEL FORMULARIO")
        print("========================================")

        asignatura_id = str(
            request.form.get(
                "asignatura_id",
                ""
            )
        ).strip()

        docente_codigo = str(
            request.form.get(
                "docente_id",
                ""
            )
        ).strip()

        nivel = str(
            request.form.get(
                "nivel",
                ""
            )
        ).strip()

        grado = str(
            request.form.get(
                "grado",
                ""
            )
        ).strip()

        seccion = str(
            request.form.get(
                "seccion",
                ""
            )
        ).strip().upper()

        activo_form = str(
            request.form.get(
                "activo",
                "True"
            )
        ).strip()

        print("📚 ASIGNATURA ID:", asignatura_id)
        print("👨‍🏫 DOCENTE:", docente_codigo)
        print("🎓 NIVEL:", nivel)
        print("🎓 GRADO:", grado)
        print("🏫 SECCIÓN:", seccion)
        print("📌 ACTIVO:", activo_form)

        print("========================================")

        # =================================================
        # 4. VALIDACIONES
        # =================================================

        if not asignatura_id:

            flash(
                "Debe seleccionar una asignatura.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        if not docente_codigo:

            flash(
                "Debe seleccionar un docente.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        if not nivel:

            flash(
                "Debe seleccionar el nivel.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        if not grado:

            flash(
                "Debe seleccionar el grado.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        if not seccion:

            flash(
                "Debe seleccionar la sección.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        # =================================================
        # 5. BUSCAR ASIGNATURA
        # =================================================

        print("")
        print("========================================")
        print("🔎 BUSCANDO ASIGNATURA")
        print("========================================")

        asignatura = None

        # -------------------------------------------------
        # 5.1 Buscar por _id como texto
        # -------------------------------------------------

        asignatura = db.asignaturas.find_one({
            "_id": asignatura_id
        })

        # -------------------------------------------------
        # 5.2 Buscar por ObjectId
        # -------------------------------------------------

        if not asignatura:

            try:

                from bson import ObjectId

                if ObjectId.is_valid(
                    asignatura_id
                ):

                    asignatura = db.asignaturas.find_one({
                        "_id": ObjectId(
                            asignatura_id
                        )
                    })

            except Exception as e:

                print(
                    "⚠️ ERROR BUSCANDO ASIGNATURA POR OBJECTID:",
                    e
                )

        # -------------------------------------------------
        # 5.3 Buscar por código
        # -------------------------------------------------

        if not asignatura:

            asignatura = db.asignaturas.find_one({
                "codigo": asignatura_id
            })

        # -------------------------------------------------
        # 5.4 Buscar por código en mayúsculas
        # -------------------------------------------------

        if not asignatura:

            asignatura = db.asignaturas.find_one({
                "codigo": asignatura_id.upper()
            })

        # =================================================
        # 6. VALIDAR ASIGNATURA
        # =================================================

        if not asignatura:

            print("")
            print("❌ ASIGNATURA NO ENCONTRADA")
            print(
                "VALOR RECIBIDO:",
                asignatura_id
            )
            print("========================================")

            flash(
                "La asignatura seleccionada no existe.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        print("✅ ASIGNATURA ENCONTRADA")
        print(
            "🆔 ID:",
            asignatura.get("_id")
        )
        print(
            "🔤 CÓDIGO:",
            asignatura.get("codigo", "")
        )
        print(
            "📖 NOMBRE:",
            asignatura.get("nombre", "")
        )

        # =================================================
        # 7. BUSCAR DOCENTE
        # =================================================

        print("")
        print("========================================")
        print("🔎 BUSCANDO DOCENTE")
        print("========================================")

        docente = None

        # -------------------------------------------------
        # 7.1 Buscar por código
        # -------------------------------------------------

        docente = db.docentes.find_one({
            "codigo": docente_codigo
        })

        # -------------------------------------------------
        # 7.2 Buscar por ObjectId
        # -------------------------------------------------

        if not docente:

            try:

                from bson import ObjectId

                if ObjectId.is_valid(
                    docente_codigo
                ):

                    docente = db.docentes.find_one({
                        "_id": ObjectId(
                            docente_codigo
                        )
                    })

            except Exception as e:

                print(
                    "⚠️ ERROR BUSCANDO DOCENTE POR OBJECTID:",
                    e
                )

        # -------------------------------------------------
        # 7.3 Buscar por _id como texto
        # -------------------------------------------------

        if not docente:

            docente = db.docentes.find_one({
                "_id": docente_codigo
            })

        # -------------------------------------------------
        # 7.4 Buscar por usuario
        # -------------------------------------------------

        if not docente:

            docente = db.docentes.find_one({
                "usuario": docente_codigo
            })

        # =================================================
        # 8. VALIDAR DOCENTE
        # =================================================

        if not docente:

            print("")
            print(
                "❌ DOCENTE NO ENCONTRADO:",
                docente_codigo
            )
            print("========================================")

            flash(
                "El docente seleccionado no existe.",
                "danger"
            )

            return redirect(
                url_for("asignar_clase")
            )

        print("✅ DOCENTE ENCONTRADO")
        print(
            "🆔 ID:",
            docente.get("_id")
        )
        print(
            "🔢 CÓDIGO:",
            docente.get("codigo", "")
        )
        print(
            "👨‍🏫 NOMBRE:",
            docente.get("nombre", "")
        )
        print(
            "👤 USUARIO:",
            docente.get("usuario", "")
        )

        # =================================================
        # 9. NORMALIZAR ID DEL DOCENTE
        # =================================================

        codigo_real = str(
            docente.get(
                "codigo",
                ""
            )
        ).strip().upper()

        if codigo_real.startswith("DOC"):

            docente_id = codigo_real

        else:

            docente_id = (
                "DOC" +
                codigo_real
            )

        print(
            "🆔 DOCENTE ID NORMALIZADO:",
            docente_id
        )

        # =================================================
        # 10. DATOS DE LA ASIGNATURA
        # =================================================

        codigo_asignatura = str(
            asignatura.get(
                "codigo",
                ""
            )
        ).strip().upper()

        nombre_asignatura = str(
            asignatura.get(
                "nombre",
                ""
            )
        ).strip()

        asignatura_id_real = str(
            asignatura.get(
                "_id"
            )
        )

        # =================================================
        # 11. ESTADO
        # =================================================

        activo = (
            activo_form.lower()
            in [
                "true",
                "1",
                "on",
                "si",
                "sí"
            ]
        )

        # =================================================
        # 12. VERIFICAR CLASE DUPLICADA
        #
        # COLECCIÓN ÚNICA:
        # db.clase
        # =================================================

        print("")
        print("========================================")
        print("🔎 VERIFICANDO CLASE DUPLICADA")
        print("========================================")

        clase_existente = db.clase.find_one({

            "asignatura_id":
                asignatura_id_real,

            "docente_id":
                docente_id,

            "nivel":
                nivel,

            "grado":
                grado,

            "seccion":
                seccion,

            "activo":
                True

        })

        if clase_existente:

            print("⚠️ CLASE DUPLICADA")
            print(
                "ID EXISTENTE:",
                clase_existente.get("_id")
            )

            print(
                "ASIGNATURA:",
                clase_existente.get(
                    "asignatura_codigo",
                    ""
                )
            )

            print(
                "DOCENTE:",
                clase_existente.get(
                    "docente_id",
                    ""
                )
            )

            print(
                "GRADO:",
                clase_existente.get(
                    "grado",
                    ""
                )
            )

            print(
                "SECCIÓN:",
                clase_existente.get(
                    "seccion",
                    ""
                )
            )

            print("========================================")

            flash(
                "Esta clase ya está asignada a este docente para ese grado y sección.",
                "warning"
            )

            return redirect(
                url_for("asignar_clase")
            )

        # =================================================
        # 13. CREAR DOCUMENTO DE CLASE
        # =================================================

        nueva_clase = {

            # ---------------------------------------------
            # IDENTIFICACIÓN
            # ---------------------------------------------

            "asignatura_id":
                asignatura_id_real,

            "asignatura_codigo":
                codigo_asignatura,

            "asignatura_nombre":
                nombre_asignatura,

            # ---------------------------------------------
            # UBICACIÓN ACADÉMICA
            # ---------------------------------------------

            "nivel":
                nivel,

            "grado":
                grado,

            "seccion":
                seccion,

            # ---------------------------------------------
            # DOCENTE
            # ---------------------------------------------

            "docente_id":
                docente_id,

            "docente_codigo":
                codigo_real,

            "docente_nombre":
                docente.get(
                    "nombre",
                    ""
                ),

            "tipo_docente":
                docente.get(
                    "tipo_docente",
                    "docente"
                ),

            # ---------------------------------------------
            # ESTADO
            # ---------------------------------------------

            "activo":
                activo

        }

        # =================================================
        # 14. MOSTRAR DOCUMENTO
        # =================================================

        print("")
        print("========================================")
        print("💾 DOCUMENTO QUE SE GUARDARÁ EN db.clase")
        print("========================================")

        for campo, valor in nueva_clase.items():

            print(
                f"{campo}: {valor}"
            )

        print("========================================")

        # =================================================
        # 15. GUARDAR EN db.clase
        # =================================================

        resultado = db.clase.insert_one(
            nueva_clase
        )

        # =================================================
        # 16. CONFIRMACIÓN
        # =================================================

        print("")
        print("========================================")
        print("✅ CLASE GUARDADA CORRECTAMENTE")
        print("========================================")

        print(
            "🆔 ID GENERADO:",
            resultado.inserted_id
        )

        print(
            "📂 COLECCIÓN:",
            "clase"
        )

        print(
            "🔤 CÓDIGO:",
            codigo_asignatura
        )

        print(
            "📖 ASIGNATURA:",
            nombre_asignatura
        )

        print(
            "👨‍🏫 DOCENTE:",
            docente_id
        )

        print(
            "👤 DOCENTE:",
            docente.get(
                "nombre",
                ""
            )
        )

        print(
            "🎓 NIVEL:",
            nivel
        )

        print(
            "🎓 GRADO:",
            grado
        )

        print(
            "🏫 SECCIÓN:",
            seccion
        )

        print(
            "📌 ACTIVO:",
            activo
        )

        print("========================================")

        flash(
            "La clase fue asignada correctamente.",
            "success"
        )

        return redirect(
            url_for("asignar_clase")
        )

    # =====================================================
    # 17. MOSTRAR FORMULARIO
    # =====================================================

    print("")
    print("========================================")
    print("📋 MOSTRANDO FORMULARIO DE ASIGNACIÓN")
    print("========================================")
    print(
        "📚 ASIGNATURAS:",
        len(asignaturas)
    )
    print(
        "👨‍🏫 DOCENTES:",
        len(docentes)
    )
    print("========================================")

    return render_template(

        "asignaturas/asignar_clase.html",

        asignaturas=asignaturas,

        docentes=docentes

    )
# =========================
# ASIGNAR ESTUDIANTE
# =========================
@app.route("/asignar_estudiantes", methods=["POST"])
@role_required("admin")
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
# AGREGAR ASIGNATURA
# ==========================================================

@app.route("/asignaturas/agregar", methods=["GET", "POST"])
@role_required("admin")
def agregar_asignatura():

    # ======================================================
    # OBTENER DOCENTES
    # ======================================================

    docentes = list(
        db.docentes.find({}).sort("nombre", 1)
    )

    # ======================================================
    # GUARDAR ASIGNATURA
    # ======================================================

    if request.method == "POST":

        codigo = request.form.get(
            "codigo",
            ""
        ).strip().upper()

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        nivel = request.form.get(
            "nivel",
            ""
        ).strip()

        grado = request.form.get(
            "grado",
            ""
        ).strip()

        docente_id = request.form.get(
            "docente_id",
            ""
        ).strip()

        print("")
        print("========================================================")
        print("🔥 GUARDANDO NUEVA ASIGNATURA")
        print("========================================================")
        print("CÓDIGO:", codigo)
        print("NOMBRE:", nombre)
        print("NIVEL:", nivel)
        print("GRADO:", grado)
        print("DOCENTE RECIBIDO:", docente_id)
        print("========================================================")

        # ==================================================
        # VALIDAR CAMPOS
        # ==================================================

        if not codigo:

            flash(
                "Debe ingresar el código de la asignatura.",
                "warning"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        if not nombre:

            flash(
                "Debe ingresar el nombre de la asignatura.",
                "warning"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        if not nivel:

            flash(
                "Debe seleccionar el nivel.",
                "warning"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        if not grado:

            flash(
                "Debe ingresar el grado.",
                "warning"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        if not docente_id:

            flash(
                "Debe seleccionar el docente responsable.",
                "warning"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        # ==================================================
        # BUSCAR DOCENTE
        # ==================================================

        docente = None

        # Primero intentamos encontrarlo por código
        docente = db.docentes.find_one({
            "codigo": docente_id
        })

        # Si no existe, intentamos por _id
        if not docente:

            docente = db.docentes.find_one({
                "_id": docente_id
            })

        if not docente:

            flash(
                "El docente seleccionado no existe.",
                "danger"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        # ==================================================
        # NORMALIZAR ID DEL DOCENTE
        # ==================================================

        codigo_docente = str(
            docente.get("codigo", "")
        ).strip().upper()

        if not codigo_docente:

            flash(
                "El docente seleccionado no tiene código.",
                "danger"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        # Siempre trabajaremos con DOCxxx
        if codigo_docente.startswith("DOC"):

            docente_id_final = codigo_docente

        else:

            docente_id_final = (
                "DOC" + codigo_docente
            )

        # ==================================================
        # VERIFICAR DUPLICADO
        # ==================================================

        asignatura_existente = db.asignaturas.find_one({
            "codigo": codigo,
            "nivel": nivel,
            "grado": grado,
            "docente_id": docente_id_final,
            "activo": True
        })

        if asignatura_existente:

            flash(
                "Esta asignatura ya está asignada a "
                "ese docente, nivel y grado.",
                "warning"
            )

            return redirect(
                url_for("agregar_asignatura")
            )

        # ==================================================
        # CREAR ASIGNATURA
        # ==================================================

        nueva_asignatura = {

            "codigo": codigo,

            "nombre": nombre,

            "nivel": nivel,

            "grado": grado,

            "docente_id": docente_id_final,

            "docente_nombre": docente.get(
                "nombre",
                ""
            ),

            "activo": True
        }

        # ==================================================
        # MOSTRAR DOCUMENTO
        # ==================================================

        print("")
        print("========================================================")
        print("💾 DOCUMENTO QUE SE VA A GUARDAR")
        print("========================================================")
        print(nueva_asignatura)
        print("========================================================")

        # ==================================================
        # GUARDAR EN MONGODB
        # ==================================================

        resultado = db.asignaturas.insert_one(
            nueva_asignatura
        )

        # ==================================================
        # CONFIRMAR
        # ==================================================

        if resultado.inserted_id:

            print("")
            print("========================================================")
            print("✅ ASIGNATURA GUARDADA CORRECTAMENTE")
            print("========================================================")
            print("ID:", resultado.inserted_id)
            print("CÓDIGO:", codigo)
            print("NOMBRE:", nombre)
            print("NIVEL:", nivel)
            print("GRADO:", grado)
            print("DOCENTE:", docente_id_final)
            print("DOCENTE NOMBRE:", docente.get("nombre", ""))
            print("========================================================")

            flash(
                f"La asignatura {nombre} fue agregada "
                f"y asignada correctamente al docente.",
                "success"
            )

        else:

            flash(
                "No fue posible guardar la asignatura.",
                "danger"
            )

        return redirect(
            url_for("listar_asignaturas")
        )

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    return render_template(
        "asignaturas/agregar.html",
        docentes=docentes
    )

# ==========================================================
# EDITAR ASIGNATURA
# ==========================================================

@app.route(
    "/asignaturas/editar/<id>",
    methods=["GET", "POST"]
)
@role_required("admin")
def editar_asignatura(id):

    print("")
    print("========================================================")
    print("✏️ EDITAR ASIGNATURA")
    print("========================================================")
    print("ID RECIBIDO:", id)
    print("========================================================")

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
    # BUSCAR ASIGNATURA
    # ======================================================

    asignatura = db.asignaturas.find_one(
        filtro
    )

    if not asignatura:

        flash(
            "Asignatura no encontrada.",
            "danger"
        )

        return redirect(
            url_for("listar_asignaturas")
        )

    # ======================================================
    # OBTENER DOCENTES
    # ======================================================

    docentes = list(
        db.docentes.find({}).sort(
            "nombre",
            1
        )
    )

    # ======================================================
    # GUARDAR CAMBIOS
    # ======================================================

    if request.method == "POST":

        codigo = request.form.get(
            "codigo",
            ""
        ).strip().upper()

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        nivel = request.form.get(
            "nivel",
            ""
        ).strip()

        grado = request.form.get(
            "grado",
            ""
        ).strip()

        docente_id = request.form.get(
            "docente_id",
            ""
        ).strip().upper()

        print("")
        print("========================================================")
        print("💾 ACTUALIZANDO ASIGNATURA")
        print("========================================================")
        print("CÓDIGO:", codigo)
        print("NOMBRE:", nombre)
        print("NIVEL:", nivel)
        print("GRADO:", grado)
        print("DOCENTE RECIBIDO:", docente_id)
        print("========================================================")

        # ==================================================
        # VALIDAR
        # ==================================================

        if (
            not codigo
            or not nombre
            or not nivel
            or not grado
            or not docente_id
        ):

            flash(
                "Debe completar todos los campos.",
                "warning"
            )

            return redirect(
                url_for(
                    "editar_asignatura",
                    id=id
                )
            )

        # ==================================================
        # NORMALIZAR DOCENTE
        # ==================================================

        if docente_id.startswith("DOC"):

            codigo_docente_busqueda = docente_id[3:]

        else:

            codigo_docente_busqueda = docente_id

            docente_id = (
                "DOC" + docente_id
            )

        # ==================================================
        # BUSCAR DOCENTE POR CÓDIGO
        # ==================================================

        docente = db.docentes.find_one({
            "codigo": codigo_docente_busqueda
        })

        # ==================================================
        # SI NO SE ENCUENTRA, BUSCAR POR DOCxxx
        # ==================================================

        if not docente:

            docente = db.docentes.find_one({
                "codigo": docente_id
            })

        # ==================================================
        # SI NO EXISTE
        # ==================================================

        if not docente:

            flash(
                "El docente seleccionado no existe.",
                "danger"
            )

            return redirect(
                url_for(
                    "editar_asignatura",
                    id=id
                )
            )

        # ==================================================
        # OBTENER CÓDIGO DEFINITIVO
        # ==================================================

        codigo_real = str(
            docente.get(
                "codigo",
                ""
            )
        ).strip().upper()

        if codigo_real.startswith("DOC"):

            docente_id_final = codigo_real

        else:

            docente_id_final = (
                "DOC" + codigo_real
            )

        # ==================================================
        # ACTUALIZAR
        # ==================================================

        db.asignaturas.update_one(

            filtro,

            {
                "$set": {

                    "codigo": codigo,

                    "nombre": nombre,

                    "nivel": nivel,

                    "grado": grado,

                    "docente_id":
                        docente_id_final,

                    "docente_nombre":
                        docente.get(
                            "nombre",
                            ""
                        ),

                    "activo": True
                }
            }
        )

        print("")
        print("========================================================")
        print("✅ ASIGNATURA ACTUALIZADA")
        print("========================================================")
        print("CÓDIGO:", codigo)
        print("NOMBRE:", nombre)
        print("NIVEL:", nivel)
        print("GRADO:", grado)
        print("DOCENTE:", docente_id_final)
        print("DOCENTE NOMBRE:", docente.get("nombre", ""))
        print("========================================================")

        flash(
            "Asignatura actualizada correctamente.",
            "success"
        )

        return redirect(
            url_for("listar_asignaturas")
        )

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    return render_template(

        "asignaturas/editar.html",

        asignatura=asignatura,

        docentes=docentes
    )

# ==========================================================
# ELIMINAR ASIGNATURA
# ==========================================================

@app.route(
    "/asignaturas/eliminar/<id>"
)
@role_required("admin")
def eliminar_asignatura(id):

    print("==============================")
    print("ELIMINAR ASIGNATURA")
    print("ID:", id)
    print("==============================")

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
@role_required("admin")
def reportes_admin():

    return render_template(
        "admin/reportes.html"
    )



# =========================
# REPORTE DE ESTUDIANTES
# =========================

@app.route("/admin/reporte/estudiantes")
@role_required("admin")
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




# =========================
# REPORTE DE DOCENTES
# =========================

@app.route("/admin/reporte/docentes")
@role_required("admin")
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




# =========================
# REPORTE DE MATRÍCULAS
# =========================

@app.route("/admin/reporte/matriculas")
@role_required("admin")
def reporte_matriculas():


    matriculas = list(
        db.matriculas.find().sort(
            "fecha_matricula",
            -1
        )
    )


    return render_template(
        "admin/reporte_matriculas.html",
        matriculas=matriculas
    )

# =========================
# REPORTE ACADÉMICO
# =========================

@app.route("/admin/reporte/academico")
@role_required("admin")
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
# ==========================================================
# REPORTE DE ESTUDIANTES POR GRADO
# ==========================================================

@app.route(
    "/admin/reportes/estudiantes-por-grado",
    methods=["GET"]
)
@role_required("admin")
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

        print(
            "=========================================="
        )

        print(
            "ERROR EN REPORTE DE ESTUDIANTES POR GRADO"
        )

        print(
            "TIPO:",
            type(e).__name__
        )

        print(
            "ERROR:",
            repr(e)
        )

        print(
            "=========================================="
        )

        flash(
            f"No se pudo generar el reporte: {e}",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin/reporte_academico.html",

        total_estudiantes=total_estudiantes,

        total_docentes=total_docentes,

        total_asignaturas=total_asignaturas,

        total_matriculas=total_matriculas,

        grados=grados

    )

# =========================
# VERIFICAR RUTAS
# =========================

print("\n========= RUTAS REGISTRADAS =========")

for ruta in app.url_map.iter_rules():
    print(ruta.endpoint, " ---> ", ruta)

print("====================================")


# ==========================================================
# MOSTRAR RUTAS DE COMUNICADOS
# ==========================================================

print("==========================================")
print("📋 RUTAS DE COMUNICADOS")
print("==========================================")

for regla in app.url_map.iter_rules():

    if "comunicado" in str(regla).lower():

        print(
            regla,
            "=>",
            regla.endpoint,
            regla.methods
        )

print("==========================================")


# =========================
# RUN
# =========================
if __name__ == "__main__":

    print("================================================")
    print("🚀 CIEM ACADÉMICO")
    print("================================================")
    print("📄 ARCHIVO:", os.path.abspath(__file__))
    print("🗄️ BASE DE DATOS:", db.name)
    print("")

    print("📌 RUTAS REGISTRADAS:")

    for ruta in app.url_map.iter_rules():
        print(
            ruta.rule,
            "->",
            ruta.endpoint,
            "|",
            ",".join(sorted(ruta.methods))
        )

    print("================================================")
    print("🌐 SERVIDOR: http://127.0.0.1:5000")
    print("🔐 LOGIN: http://127.0.0.1:5000/login")
    print("================================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )