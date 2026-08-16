from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from flask import request, url_for
from weasyprint import HTML
from io import BytesIO
from datetime import datetime
from bson import ObjectId
from functools import wraps
from datetime import datetime
import os

from config.database import db


app = Flask(__name__)

app.secret_key = "CIEM_clave_segura_2026"

from routes.docentes import docente_bp
from routes.estudiante import estudiante_bp
from routes.mensajes import mensajes_bp
from routes.ciem_ai import ciem_ai_bp

app.register_blueprint(docente_bp)
app.register_blueprint(estudiante_bp)
app.register_blueprint(mensajes_bp)
app.register_blueprint(ciem_ai_bp)



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
# HOME
# =========================
@app.route("/")
def home():
    return redirect(url_for("login"))



# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        user = db.usuarios.find_one({"usuario": usuario})

        print("Resultado búsqueda:", user)

        if not user:
            flash("Usuario no encontrado", "danger")
            return render_template("login.html")

        if user.get("password") != password:
            flash("Contraseña incorrecta", "danger")
            return render_template("login.html")

        session["usuario"] = user.get("usuario")
        session["rol"] = user.get("rol")
        session["id"] = str(user.get("_id"))

        if user.get("rol") == "admin":
            return redirect(url_for("admin_dashboard"))

        elif user.get("rol") == "docente":
            return redirect(url_for("docente.dashboard_docente"))

        elif user.get("rol") == "estudiante":
            return redirect(url_for("estudiante.dashboard"))

        elif user.get("rol") == "padre":
            return redirect(url_for("estudiante.dashboard"))

        else:
            flash("Rol no válido", "danger")

    return render_template("login.html")
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


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
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
# AGREGAR MATRÍCULA
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


    # ======================================================
    # PROCESAR FORMULARIO
    # ======================================================

    try:

        print("==========================================")
        print("POST DE MATRÍCULA RECIBIDO")
        print("DATOS RECIBIDOS:")
        print(request.form.to_dict())
        print("==========================================")


        # ==================================================
        # NOMBRES Y APELLIDOS
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
        # GENERAR CÓDIGO
        # ==================================================

        iniciales = (

            primer_nombre[:1]
            + segundo_nombre[:1]
            + primer_apellido[:1]
            + segundo_apellido[:1]

        ).upper()

        iniciales = (
            iniciales + "XXXX"
        )[:4]

        codigo = f"CIEM-{iniciales}"

        print(
            "CÓDIGO GENERADO:",
            codigo
        )


        # ==================================================
        # VERIFICAR ESTUDIANTE EXISTENTE
        # ==================================================

        estudiante_existente = db.estudiantes.find_one({
            "_id": codigo
        })


        # ==================================================
        # VERIFICAR MATRÍCULA EXISTENTE
        # ==================================================

        matricula_existente = db.matriculas.find_one({
            "estudiante_id": codigo,
            "anio_lectivo": 2026
        })

        if matricula_existente:

            flash(
                f"El estudiante {codigo} ya tiene "
                f"una matrícula registrada para 2026.",
                "warning"
            )

            print(
                "MATRÍCULA YA EXISTE:",
                codigo
            )

            return redirect(
                url_for("listar_matriculas")
            )


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


        # ==================================================
        # USUARIO DE LA MADRE
        # ==================================================

        madre_usuario = request.form.get(
            "madre_usuario",
            ""
        ).strip()

        print(
            "USUARIO MADRE:",
            madre_usuario
        )


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
        # CREAR ESTUDIANTE
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


                # ==========================================
                # INFORMACIÓN LINGÜÍSTICA
                # ==========================================

                "informacion_linguistica":
                    informacion_linguistica,


                # ==========================================
                # CAPACIDADES
                # ==========================================

                "capacidades":
                    capacidades,

                "observaciones":
                    observaciones,


                # ==========================================
                # PADRE
                # ==========================================

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


                # ==========================================
                # MADRE
                # ==========================================

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
                # TUTOR
                # ==========================================

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


            resultado_estudiante = (
                db.estudiantes.insert_one(
                    estudiante
                )
            )

            print(
                "=========================================="
            )

            print(
                "ESTUDIANTE CREADO:",
                resultado_estudiante.inserted_id
            )

            print(
                "NOMBRE:",
                nombre_completo
            )

            print(
                "MADRE:",
                madre_nombre
            )

            print(
                "USUARIO MADRE:",
                madre_usuario
            )

            print(
                "=========================================="
            )

        else:

            print(
                "ESTUDIANTE YA EXISTÍA:",
                codigo
            )


        # ==================================================
        # CREAR MATRÍCULA
        # ==================================================

        matricula = {

            "estudiante_id":
                codigo,

            "codigo":
                codigo,

            "fecha_matricula":
                fecha_matricula,

            "anio_lectivo":
                2026,

            "grado":
                grado,

            "seccion":
                seccion,


            # ==============================================
            # INFORMACIÓN DEL ESTUDIANTE
            # ==============================================

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


            # ==============================================
            # UBICACIÓN
            # ==============================================

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


            # ==============================================
            # INFORMACIÓN LINGÜÍSTICA
            # ==============================================

            "informacion_linguistica":
                informacion_linguistica,


            # ==============================================
            # CAPACIDADES
            # ==============================================

            "capacidades":
                capacidades,

            "observaciones":
                observaciones,


            # ==============================================
            # PADRE
            # ==============================================

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


            # ==============================================
            # MADRE
            # ==============================================

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


            # ==============================================
            # TUTOR
            # ==============================================

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


            # ==============================================
            # COMPROMISO
            # ==============================================

            "compromiso":
                True,

            "estado":
                "activa"
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
        print("MATRÍCULA GUARDADA CORRECTAMENTE")
        print("CÓDIGO:", codigo)
        print(
            "ID MATRÍCULA:",
            resultado_matricula.inserted_id
        )
        print("==========================================")


        # ==================================================
        # MENSAJE
        # ==================================================

        flash(
            f"¡Matrícula registrada correctamente! "
            f"Código: {codigo}",
            "success"
        )


        # ==================================================
        # REGRESAR AL LISTADO
        # ==================================================

        return redirect(
            url_for("listar_matriculas")
        )


    # ======================================================
    # ERROR
    # ======================================================

    except Exception as e:

        print("==========================================")
        print("ERROR AL GUARDAR MATRÍCULA")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")


        flash(
            f"No se pudo registrar la matrícula: {e}",
            "danger"
        )


        return redirect(
            url_for("agregar_matricula")
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

        print("==========================================")
        print("VER MATRÍCULA")
        print("CÓDIGO:", codigo)
        print("==========================================")


        matricula = db.matriculas.find_one({
            "codigo": codigo
        })


        if not matricula:

            flash(
                "No se encontró la matrícula solicitada.",
                "warning"
            )

            return redirect(
                url_for("listar_matriculas")
            )


        estudiante = db.estudiantes.find_one({
            "_id": codigo
        })


        return render_template(
            "admin/ver_matricula.html",
            matricula=matricula,
            estudiante=estudiante
        )


    except Exception as e:

        print("==========================================")
        print("ERROR AL VER MATRÍCULA")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")


        flash(
            f"No se pudo cargar la matrícula: {e}",
            "danger"
        )


        return redirect(
            url_for("listar_matriculas")
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
        print("EDITAR MATRÍCULA")
        print("CÓDIGO:", codigo)
        print("==========================================")

        # ==================================================
        # BUSCAR ESTUDIANTE
        # ==================================================

        estudiante = db.estudiantes.find_one({
            "_id": codigo
        })

        if not estudiante:

            flash(
                "No se encontró el estudiante.",
                "warning"
            )

            return redirect(
                url_for("listar_matriculas")
            )

        # ==================================================
        # BUSCAR MATRÍCULA
        # ==================================================

        matricula = db.matriculas.find_one({
            "codigo": codigo
        })

        if not matricula:

            flash(
                "No se encontró la matrícula.",
                "warning"
            )

            return redirect(
                url_for("listar_matriculas")
            )

        # ==================================================
        # GUARDAR CAMBIOS
        # ==================================================

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

            fecha_nacimiento = request.form.get(
                "fecha_nacimiento",
                ""
            ).strip()

            lugar_nacimiento = request.form.get(
                "lugar_nacimiento",
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

            telefono = request.form.get(
                "telefono",
                ""
            ).strip()

            celular = request.form.get(
                "celular",
                ""
            ).strip()

            padre_nombre = request.form.get(
                "padre_nombre",
                ""
            ).strip()

            madre_nombre = request.form.get(
                "madre_nombre",
                ""
            ).strip()

            tutor_nombre = request.form.get(
                "tutor_nombre",
                ""
            ).strip()

            tutor_parentesco = request.form.get(
                "tutor_parentesco",
                ""
            ).strip()

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
            # ACTUALIZAR ESTUDIANTE
            # ==================================================

            db.estudiantes.update_one(
                {
                    "_id": codigo
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

                        "direccion":
                            direccion,

                        "barrio":
                            barrio,

                        "telefono":
                            telefono,

                        "celular":
                            celular,

                        "padre":
                            padre_nombre,

                        "madre":
                            madre_nombre,

                        "tutor":
                            tutor_nombre
                    }
                }
            )

            # ==================================================
            # ACTUALIZAR MATRÍCULA
            # ==================================================

            db.matriculas.update_one(
                {
                    "codigo": codigo
                },
                {
                    "$set": {

                        "grado":
                            grado,

                        "seccion":
                            seccion,

                        "fecha_matricula":
                            fecha_matricula,

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

                        "ubicacion.direccion":
                            direccion,

                        "ubicacion.barrio":
                            barrio,

                        "ubicacion.telefono":
                            telefono,

                        "ubicacion.celular":
                            celular,

                        "padre.nombre":
                            padre_nombre,

                        "madre.nombre":
                            madre_nombre,

                        "tutor.nombre":
                            tutor_nombre,

                        "tutor.parentesco":
                            tutor_parentesco
                    }
                }
            )

            print(
                "MATRÍCULA ACTUALIZADA:",
                codigo
            )

            flash(
                f"Los datos de {nombre_completo} "
                f"fueron actualizados correctamente.",
                "success"
            )

            return redirect(
                url_for("listar_matriculas")
            )

        # ==================================================
        # MOSTRAR FORMULARIO DE EDICIÓN
        # ==================================================

        return render_template(
            "admin/editar_matricula.html",
            estudiante=estudiante,
            matricula=matricula
        )

    except Exception as e:

        print("==========================================")
        print("ERROR AL EDITAR MATRÍCULA")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

        flash(
            f"No se pudo editar la matrícula: {e}",
            "danger"
        )

        return redirect(
            url_for("listar_matriculas")
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
        print("DESACTIVAR MATRÍCULA")
        print("ID:", matricula_id)
        print("==========================================")

        # ==================================================
        # VALIDAR OBJECTID
        # ==================================================

        if not ObjectId.is_valid(matricula_id):

            flash(
                "El identificador de la matrícula no es válido.",
                "danger"
            )

            return redirect(
                url_for("listar_matriculas")
            )

        object_id = ObjectId(matricula_id)

        # ==================================================
        # BUSCAR MATRÍCULA
        # ==================================================

        matricula = db.matriculas.find_one({
            "_id": object_id
        })

        if not matricula:

            flash(
                "No se encontró la matrícula.",
                "warning"
            )

            return redirect(
                url_for("listar_matriculas")
            )

        # ==================================================
        # DESACTIVAR
        # ==================================================

        resultado = db.matriculas.update_one(
            {
                "_id": object_id
            },
            {
                "$set": {
                    "estado": "inactiva"
                }
            }
        )

        if resultado.modified_count > 0:

            flash(
                "Matrícula desactivada correctamente.",
                "success"
            )

            print(
                "MATRÍCULA DESACTIVADA:",
                matricula.get("codigo")
            )

        else:

            flash(
                "La matrícula ya estaba inactiva.",
                "info"
            )

        return redirect(
            url_for("listar_matriculas")
        )

    except Exception as e:

        print("==========================================")
        print("ERROR AL DESACTIVAR MATRÍCULA")
        print("TIPO:", type(e).__name__)
        print("ERROR:", repr(e))
        print("==========================================")

        flash(
            f"No se pudo desactivar la matrícula: {e}",
            "danger"
        )

        return redirect(
            url_for("listar_matriculas")
        )
# =========================
# LISTAR-ASIGNATURA
# =========================


@app.route("/asignaturas")
@role_required("admin")
def listar_asignaturas():

    asignaturas = list(
        db.asignaturas.find().sort("nombre",1)
    )


    return render_template(
        "asignaturas/listar.html",
        asignaturas=asignaturas
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


# =========================
# AGREGAR ASIGNATURA
# =========================

@app.route("/asignaturas/agregar", methods=["GET","POST"])
@role_required("admin")
def agregar_asignatura():

    docentes = list(
        db.docentes.find()
    )


    if request.method == "POST":

        db.asignaturas.insert_one({

            "codigo": request.form["codigo"],
            "nombre": request.form["nombre"],
            "nivel": request.form["nivel"],
            "grado": request.form["grado"],
            "docente_id": request.form["docente_id"]

        })


        flash(
            "Asignatura agregada correctamente",
            "success"
        )


        return redirect(
            url_for("listar_asignaturas")
        )


    return render_template(
        "asignaturas/agregar.html",
        docentes=docentes
    )


# =========================
# EDITAR ASIGNATURA
# =========================

@app.route("/asignaturas/editar/<id>", methods=["GET","POST"])
@role_required("admin")
def editar_asignatura(id):


    print("======================")
    print("EDITAR ASIGNATURA")
    print("ID:", id)



    # Buscar asignatura

    if ObjectId.is_valid(id):

        filtro = {
            "_id": ObjectId(id)
        }

    else:

        filtro = {
            "_id": id
        }



    asignatura = db.asignaturas.find_one(filtro)



    if not asignatura:

        flash(
            "Asignatura no encontrada",
            "danger"
        )

        return redirect(
            url_for("listar_asignaturas")
        )




    if request.method == "POST":


        datos = {

            "codigo":
            request.form.get("codigo"),


            "nombre":
            request.form.get("nombre"),


            "nivel":
            request.form.get("nivel"),


            "grado":
            request.form.get("grado"),


            "docente_id":
            request.form.get("docente_id")

        }



        db.asignaturas.update_one(

            filtro,

            {
                "$set":datos
            }

        )



        flash(
            "Asignatura actualizada correctamente",
            "success"
        )


        return redirect(
            url_for("listar_asignaturas")
        )



    docentes = list(
        db.docentes.find().sort("nombre",1)
    )


    return render_template(

        "asignaturas/editar.html",

        asignatura=asignatura,

        docentes=docentes

    )

    # =========================
    # GUARDAR CAMBIOS
    # =========================

    if request.method == "POST":


        print("======================")
        print("DATOS RECIBIDOS")
        print(request.form)
        print("======================")


        datos_actualizados = {

            "codigo": request.form.get("codigo",""),

            "nombre": request.form.get("nombre",""),

            "nivel": request.form.get("nivel",""),

            "grado": request.form.get("grado",""),

            "docente_id": request.form.get("docente_id","")

        }


        db.asignaturas.update_one(

            filtro,

            {
                "$set": datos_actualizados
            }

        )



        flash(
            "Asignatura actualizada correctamente",
            "success"
        )


        return redirect(
            url_for("listar_asignaturas")
        )

# =========================
# ELIMINAR ASIGNATURA
# =========================

@app.route("/asignaturas/eliminar/<id>")
@role_required("admin")
def eliminar_asignatura(id):


    print("======================")
    print("ELIMINAR ASIGNATURA")
    print("ID RECIBIDO:", id)



    if ObjectId.is_valid(id):

        filtro = {
            "_id": ObjectId(id)
        }

    else:

        filtro = {
            "_id": id
        }



    resultado = db.asignaturas.delete_one(filtro)



    if resultado.deleted_count > 0:


        flash(
            "Asignatura eliminada correctamente",
            "success"
        )


    else:


        flash(
            "Asignatura no encontrada",
            "danger"
        )



    return redirect(
        url_for("listar_asignaturas")
    )

# =========================
# NOTAS DE LA ASIGNATURA
# =========================
@app.route("/docente/notas/<id>")
@role_required("docente")
def notas_clase(id):

    asignatura = db.asignaturas.find_one({
        "_id": id
    })

    if not asignatura:
        return "Asignatura no encontrada"


    estudiantes = list(db.estudiantes.find({
        "grado": asignatura["grado"],
        "seccion": asignatura["seccion"]
    }))


    notas = list(db.notas.find({
        "asignatura_id": id
    }))


    return render_template(
        "docente/notas.html",
        asignatura=asignatura,
        estudiantes=estudiantes,
        notas=notas
    )

# =============================
# MATERIALES POR AULA
# =============================
@app.route("/aula/<id>")
@role_required("docente")
def aula_detalle(id):

    materiales = list(db.materiales.find({"asignatura_id": id}))
    tareas = list(db.tareas.find({"asignatura_id": id}))

    return render_template(
        "aula_detalle.html",
        materiales=materiales,
        tareas=tareas,
        asignatura=id
    )


# =============================
# SUBIR MATERIAL
# =============================
@app.route("/material/subir", methods=["POST"])
@role_required("docente")
def subir_material():

    db.materiales.insert_one({
        "titulo": request.form["titulo"],
        "archivo": request.form["archivo"],
        "asignatura_id": request.form["asignatura_id"],
        "docente_id": session["usuario"]
    })

    return redirect(url_for("aulas"))

#=============================
# CREAR TAREA
# =============================
@app.route("/tarea/crear", methods=["POST"])
@role_required("docente")
def crear_tarea():

    db.tareas.insert_one({
        "titulo": request.form["titulo"],
        "descripcion": request.form["descripcion"],
        "asignatura_id": request.form["asignatura_id"],
        "fecha_entrega": request.form["fecha"],
        "puntaje": int(request.form["puntaje"]),
        "docente_id": session["usuario"]
    })

    return redirect(url_for("aulas"))




# =========================
# GUARDAR NOTAS DE LA CLASE
# =========================
@app.route("/docente/notas/guardar", methods=["POST"])
@role_required("docente")
def guardar_nota_clase():

    asignatura_id = request.form["asignatura_id"]

    docente = db.docentes.find_one({
        "usuario": session["usuario"]
    })

    if not docente:
        return redirect(url_for("login"))

    for campo, valor in request.form.items():

        if campo.startswith("nota_"):

            estudiante_id = campo.replace("nota_", "")

            db.notas.update_one(

                {
                    "estudiante_id": estudiante_id,
                    "asignatura_id": asignatura_id
                },

                {
                    "$setOnInsert": {
                        "ep1": 0,
                        "ep2": 0,
                        "ep3": 0,
                        "ep4": 0,
                        "ep5": 0,
                        "ep6": 0,
                        "ep7": 0,
                        "ep8": 0,
                        "ep9": 0,
                        "ep10": 0
                    },

                    "$set": {
                        "ep1": float(valor),
                        "docente": docente["usuario"]
                    }

                },

                upsert=True

            )

    return redirect(
        url_for(
            "notas_clase",
            id=asignatura_id
        )
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
print("\n========= RUTAS REGISTRADAS =========")
print("==========================================")
print("📋 RUTAS REGISTRADAS")
print("==========================================")

for regla in app.url_map.iter_rules():
    print(regla, "=>", regla.endpoint)

print("==========================================")

if __name__ == "__main__":
    app.run(debug=True)

for ruta in app.url_map.iter_rules():
    print(ruta.endpoint, " ---> ", ruta)

print("====================================\n")
if __name__ == "__main__":
    app.run(debug=True, port=5000)