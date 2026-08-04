from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
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



from config.database import db

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

# =========================
# EDITAR ESTUDIANTE
# =========================
@app.route("/admin/estudiante/editar/<id>", methods=["GET", "POST"])
@role_required("admin")
def editar_estudiante(id):

    print("ID RECIBIDO:", id)

    estudiante = db.estudiantes.find_one({
        "_id": id
    })

    print("ESTUDIANTE ENCONTRADO:", estudiante)

    if estudiante is None:

        flash("Estudiante no encontrado", "danger")

        return redirect(
            url_for("listar_estudiantes_admin")
        )

    if request.method == "POST":

        db.estudiantes.update_one(

            {
                "_id": id
            },

            {
                "$set":{

                    "codigo":request.form["codigo"],
                    "nombre":request.form["nombre"],
                    "grado":request.form["grado"],
                    "seccion":request.form["seccion"],
                    "padre":request.form["padre"],
                    "telefono":request.form.get("telefono","")

                }

            }

        )

        flash(
            "Estudiante actualizado correctamente",
            "success"
        )

        return redirect(
            url_for("listar_estudiantes_admin")
        )

    return render_template(

        "admin/editar_estudiante.html",

        estudiante=estudiante

    )
# =========================
# ELIMINAR ESTUDIANTE
# =========================

@app.route("/admin/estudiante/eliminar/<id>")
@role_required("admin")
def eliminar_estudiante(id):

    print("ID RECIBIDO:", id)

    estudiante = db.estudiantes.find_one({
        "_id": id
    })

    print("ESTUDIANTE A ELIMINAR:")
    print(estudiante)

    if estudiante is None:

        flash(
            "Estudiante no encontrado",
            "danger"
        )

        return redirect(
            url_for("listar_estudiantes_admin")
        )

    db.estudiantes.delete_one({
        "_id": id
    })

    flash(
        "Estudiante eliminado correctamente",
        "success"
    )

    return redirect(
        url_for("listar_estudiantes_admin")
    )
@app.route("/admin/estudiantes")
@role_required("admin")
def listar_estudiantes_admin():

    estudiantes = list(
        db.estudiantes.find().sort("nombre", 1)
    )

    print("\n========== ESTUDIANTES ==========")

    for e in estudiantes:
        print("DOCUMENTO COMPLETO:")
        print(e)
        print("TIPO DEL ID:", type(e["_id"]))
        print("--------------------------")

    print("=================================\n")

    return render_template(
        "admin/estudiantes.html",
        estudiantes=estudiantes
    )

# =========================
# ADMIN - DOCENTES
# =========================
@app.route("/admin/docentes")
@role_required("admin")
def listar_docentes():

    docentes = list(
        db.docentes.find().sort("nombre",1)
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


@app.route("/admin/docentes/editar/<id>", methods=["GET","POST"])
@role_required("admin")
def editar_docente(id):

    print("==========================")
    print("EDITAR DOCENTE")
    print("ID RECIBIDO:", id)


    # Buscar primero como texto
    docente = db.docentes.find_one({
        "_id": id
    })


    # Si no existe buscar como ObjectId
    if docente is None:

        try:
            docente = db.docentes.find_one({
                "_id": ObjectId(id)
            })

        except:
            docente = None



    print("DOCENTE ENCONTRADO:")
    print(docente)



    if docente is None:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("listar_docentes")
        )



    if request.method == "POST":


        filtro = {
            "_id": docente["_id"]
        }



        db.docentes.update_one(

            filtro,

            {
                "$set":{

                    "nombre":
                    request.form["nombre"],


                    "usuario":
                    request.form["usuario"],


                    "telefono":
                    request.form["telefono"],


                    "especialidad":
                    request.form["especialidad"]

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



    return render_template(
        "admin/editar_docente.html",
        docente=docente
    )
# =========================
# ELIMINAR DOCENTE
# =========================

from bson.objectid import ObjectId


@app.route("/admin/docentes/eliminar/<id>")
@role_required("admin")
def eliminar_docente(id):


    print("DOCENTE A ELIMINAR:", id)



    docente = db.docentes.find_one({
        "_id": id
    })


    if docente is None:

        try:

            docente = db.docentes.find_one({
                "_id": ObjectId(id)
            })

        except:

            docente = None



    print("DOCENTE ENCONTRADO:")
    print(docente)



    if docente:


        db.docentes.delete_one({

            "_id": docente["_id"]

        })


        flash(
            "Docente eliminado correctamente",
            "success"
        )


    else:


        flash(
            "Docente no encontrado",
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

# =========================
# AGREGAR ESTUDIANTE
# =========================

@app.route("/admin/estudiante/agregar", methods=["GET","POST"])
@role_required("admin")
def agregar_estudiante():

    if request.method == "POST":

        db.estudiantes.insert_one({

            "_id": request.form["codigo"],
            "codigo": request.form["codigo"],
            "nombre": request.form["nombre"],
            "fecha_nacimiento": request.form["fecha_nacimiento"],
            "grado": request.form["grado"],
            "seccion": request.form["seccion"],
            "padre": request.form["padre"],
            "telefono": request.form["telefono"],
            "usuario": request.form["usuario"],
            "password": request.form["password"],
            "estado": "activo",
            "foto": "usuario.png"

        })

        flash(
            "Estudiante agregado correctamente",
            "success"
        )

        return redirect(
            url_for("listar_estudiantes_admin")
        )


    return render_template(
        "admin/agregar_estudiante.html"
    )
# =========================
# MATRICULA
# =========================

@app.route("/matriculas")
@role_required("admin")
def listar_matriculas():


    matriculas = list(

        db.matriculas.aggregate([


            {
                "$lookup":{

                    "from":"estudiantes",

                    "localField":"estudiante_id",

                    "foreignField":"_id",

                    "as":"estudiante"

                }

            },


            {

                "$unwind":{

                    "path":"$estudiante",

                    "preserveNullAndEmptyArrays":True

                }

            },


            {

                "$sort":{

                    "fecha_matricula":-1

                }

            }


        ])

    )


    return render_template(

        "admin/matriculas.html",

        matriculas=matriculas

    )



    # =====================================
    # BUSCAR ESTUDIANTE DEL PADRE
    # =====================================

    estudiante = db.estudiantes.find_one({

        "padre":{
            "$regex":usuario,
            "$options":"i"
        }

    })


    if not estudiante:

        return "Estudiante no encontrado"



    print(
        "ESTUDIANTE:",
        estudiante.get("nombre")
    )


    # =====================================
    # CARGAR NOTAS DEL ESTUDIANTE
    # MISMAS QUE REGISTRA EL DOCENTE
    # =====================================

    notas = list(

        db.notas.find({

            "estudiante_id":

            estudiante.get("codigo")

        })

    )



    print(
        "TOTAL NOTAS:",
        len(notas)
    )



    # =====================================
    # CALCULAR ACUMULADO Y PROMEDIO
    # =====================================

    for n in notas:


        acumulado = (

            n.get("ep1",0) +
            n.get("ep2",0) +
            n.get("ep3",0) +
            n.get("ep4",0) +
            n.get("ep5",0) +
            n.get("ep6",0) +
            n.get("ep7",0) +
            n.get("ep8",0) +
            n.get("ep9",0) +
            n.get("ep10",0)

        )


        n["acumulado"] = acumulado



        n["promedio"] = round(

            acumulado / 10,

            2

        )



        if n["promedio"] >= 60:

            n["estado"] = "Aprobado"

        else:

            n["estado"] = "Pendiente"





    # =====================================
    # RESUMEN ACADÉMICO
    # =====================================

    promedio_general = 0



    if notas:


        promedio_general = round(

            sum(

                n["promedio"]

                for n in notas

            )

            /

            len(notas),

            2

        )




    resumen = {


        "promedio":

        promedio_general,


        "asistencia":

        0,


        "estado":

        "Aprobado"

        if promedio_general >= 60

        else

        "Pendiente"


    }




    # =====================================
    # DOCENTES
    # =====================================

    docentes = list(

        db.docentes.find()

    )




    return render_template(

        "estudiante_dashboard.html",

        estudiante=estudiante,

        resumen=resumen,

        notas=notas,

        docentes=docentes

    )

# =====================================
# ENVIAR MENSAJE AL DOCENTE
# =====================================

@app.route("/enviar_mensaje_docente", methods=["POST"])
def enviar_mensaje_docente():


    usuario = session.get("usuario")


    estudiante = db.estudiantes.find_one({

        "padre":{

            "$regex": usuario,

            "$options":"i"

        }

    })


    if not estudiante:

        return "Estudiante no encontrado"



    db.mensajes.insert_one({

        "padre": usuario,

        "estudiante": estudiante.get("nombre"),

        "docente": request.form.get("docente_id"),

        "mensaje": request.form.get("mensaje"),

        "fecha": datetime.now(),

        "estado": "Pendiente"

    })


    flash(
        "Mensaje enviado correctamente al docente",
        "success"
    )


    return redirect("/estudiante")

    # =====================================
    # BUSCAR ESTUDIANTE
    # =====================================

    estudiante = db.estudiantes.find_one({

        "padre": {
            "$regex": usuario,
            "$options": "i"
        }

    })



    if not estudiante:

        return "Estudiante no encontrado"



    print("ESTUDIANTE ENCONTRADO:", estudiante["nombre"])




    # =====================================
    # NOTAS DEL ESTUDIANTE
    # =====================================

    notas = list(

        db.notas.find({

            "estudiante_id": estudiante["codigo"]

        })

    )



    for n in notas:


        acumulado = sum([

            n.get("ep1",0),
            n.get("ep2",0),
            n.get("ep3",0),
            n.get("ep4",0),
            n.get("ep5",0),
            n.get("ep6",0),
            n.get("ep7",0),
            n.get("ep8",0),
            n.get("ep9",0),
            n.get("ep10",0)

        ])



        n["acumulado"] = acumulado


        n["promedio"] = round(

            acumulado / 10,

            2

        )



        if n["promedio"] >= 60:

            n["estado"] = "Aprobado"

        else:

            n["estado"] = "Pendiente"







    # =====================================
    # DOCENTES DEL ESTUDIANTE
    # =====================================

    docentes = []



    asignaturas = list(

        db.asignaturas.find({

            "grado": estudiante.get("grado"),

            "seccion": estudiante.get("seccion")

        })

    )



    for asignatura in asignaturas:



        docente = db.docentes.find_one({

            "_id": asignatura.get("docente_id")

        })



        if docente:


            docentes.append({

                "nombre":
                    docente.get("nombre"),


                "telefono":
                    docente.get("telefono"),


                "materia":
                    asignatura.get("nombre")

            })



    print("DOCENTES ENCONTRADOS:")

    print(docentes)







    # =====================================
    # RESUMEN ACADÉMICO
    # =====================================


    promedio_general = 0



    if notas:


        promedio_general = round(

            sum(

                n["promedio"]

                for n in notas

            )

            /

            len(notas)

        ,2)





    resumen = {


        "promedio":

            promedio_general,



        "asistencia":

            0,



        "estado":

            "Aprobado"

            if promedio_general >= 60

            else

            "Pendiente"


    }





    # =====================================
    # CARGAR DASHBOARD
    # =====================================


    return render_template(

        "estudiante_dashboard.html",

        estudiante=estudiante,

        notas=notas,

        docentes=docentes,

        resumen=resumen,

        mensajes=mensajes

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

# ==================================================
# REPORTES ADMINISTRATIVOS CIEM
# ==================================================


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


# =========================
# RUN
# =========================
print("\n========= RUTAS REGISTRADAS =========")

for ruta in app.url_map.iter_rules():
    print(ruta.endpoint, " ---> ", ruta)

print("====================================\n")
if __name__ == "__main__":
    app.run(debug=True, port=5000)