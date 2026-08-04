from flask import Blueprint, render_template, request, redirect, url_for, flash
from config.database import db
from datetime import datetime

from config.database import db
# ===================================
#   PROMEDIO ESTUDIANTE
# ===================================
def calcular_promedio_estudiante(estudiante_id):

    notas = list(db.notas.find({"estudiante_id": estudiante_id}))

    if not notas:
        return None

    total_final = 0
    cantidad = 0

    for n in notas:

        suma_100 = sum(float(n.get(f"ep{i}", 0)) for i in range(1, 11))

        nota_10 = suma_100 / 10  # conversión MINED

        total_final += nota_10
        cantidad += 1

    return total_final / cantidad if cantidad else None
    return round(total_final / cantidad, 2)

# =============================================================
# 3. MOTOR PRINCIPAL POR GRADO (MINED RETENCIÓN + RENDIMIENTO)
# =============================================================
def estadistica_grado(grado):

    estudiantes = list(db.estudiantes.find({"grado": grado}))

    aprobados = 0
    reprobados = 0

    for e in estudiantes:
        promedio = calcular_promedio_estudiante(e["_id"])

        if promedio is None:
            continue

        if promedio >= 6:
            aprobados += 1
        else:
            reprobados += 1

    total = aprobados + reprobados

    return {
        "grado": grado,
        "matricula": len(estudiantes),
        "aprobados": aprobados,
        "reprobados": reprobados,
        "porcentaje_aprobados": round((aprobados/total)*100,2) if total else 0,
        "porcentaje_reprobados": round((reprobados/total)*100,2) if total else 0
    }
# ========================================
#  4. MOTOR COMPLETO POR TODOS LOS GRADOS
# =======================================
def estadistica_general():

    grados = ["Preescolar", "1", "2", "3", "4", "5", "6"]

    resultado = []

    for g in grados:
        resultado.append(estadistica_grado(g))

    return resultado


#========================================
#  5. REPORTE POR ASIGNATURA (MINED)
# =======================================

def estadistica_asignatura():

    asignaturas = list(db.asignaturas.find())

    resultado = []

    for a in asignaturas:

        notas = list(db.notas.find({"asignatura_id": a["_id"]}))

        aprobados = 0
        reprobados = 0

        for n in notas:

            total = sum(float(n.get(f"ep{i}", 0)) for i in range(1, 11))
            promedio = total / 10

            if promedio >= 6:
                aprobados += 1
            else:
                reprobados += 1

        resultado.append({
            "asignatura": a["nombre"],
            "aprobados": aprobados,
            "reprobados": reprobados,
            "total": aprobados + reprobados
        })

    return resultado


#========================================
# 6. REPORTE DE RIESGO (REPROBADOS)
# =======================================
def estudiantes_en_riesgo():

    estudiantes = list(db.estudiantes.find())

    resultado = []

    for e in estudiantes:

        notas = list(db.notas.find({"estudiante_id": e["_id"]}))

        reprobadas = 0

        for n in notas:
            total = sum(float(n.get(f"ep{i}", 0)) for i in range(1, 11))
            promedio = total / 10

            if promedio < 6:
                reprobadas += 1

        if reprobadas > 0:
            resultado.append({
                "nombre": e["nombre"],
                "grado": e["grado"],
                "reprobadas": reprobadas
            })

    return resultado


# =========================
# HELPERS / ESTADÍSTICAS
# =========================

def estadistica_por_grado(grado):

    estudiantes = list(db.estudiantes.find({"grado": grado}))

    total = len(estudiantes)
    aprobados = 0
    reprobados = 0

    for e in estudiantes:

        notas = list(db.notas.find({"estudiante_id": e["_id"]}))

        if not notas:
            continue

        suma_total = 0
        for n in notas:
            suma_total += sum(float(n.get(f"ep{i}", 0)) for i in range(1, 11)) / 10

        promedio = suma_total / len(notas)

        if promedio >= 6:
            aprobados += 1
        else:
            reprobados += 1

    return {
        "grado": grado,
        "matricula": total,
        "aprobados": aprobados,
        "reprobados": reprobados,
        "porcentaje_aprobados": round((aprobados/total)*100,2) if total else 0,
        "porcentaje_reprobados": round((reprobados/total)*100,2) if total else 0
    }
def datos_mined():
    grados = db.estudiantes.distinct("grado")

    resultado = []

    for g in grados:
        estudiantes = list(db.estudiantes.find({"grado": g}))

        aprobados = 0
        reprobados = 0

        for e in estudiantes:
            notas = list(db.notas.find({"estudiante_id": e["_id"]}))

            if not notas:
                continue

            promedio = sum(
                sum(float(n.get(f"ep{i}", 0)) for i in range(1, 11)) / 10
                for n in notas
            ) / len(notas)

            if promedio >= 6:
                aprobados += 1
            else:
                reprobados += 1

        total = aprobados + reprobados

        resultado.append({
            "grado": g,
            "matricula": len(estudiantes),
            "aprobados": aprobados,
            "reprobados": reprobados,
            "porcentaje": round((aprobados / total) * 100, 2) if total else 0
        })

    return resultado

# =========================================
# INFORME MINED RETENCION ESCOLAR
# =========================================

def informe_retencion():

    grados = db.estudiantes.distinct("grado")

    resultado = []


    for grado in grados:

        estudiantes = list(
            db.estudiantes.find({
                "grado": grado
            })
        )


        inicial_as = 0
        inicial_f = 0

        actual_as = 0
        actual_f = 0

        retiros_as = 0
        retiros_f = 0


        for e in estudiantes:

            sexo = e.get("sexo","")


            if sexo == "M":
                inicial_as += 1
            else:
                inicial_f += 1


            if e.get("estado","Activo") == "Activo":

                if sexo == "M":
                    actual_as +=1
                else:
                    actual_f +=1


            else:

                if sexo == "M":
                    retiros_as +=1
                else:
                    retiros_f +=1



        total_inicial = inicial_as + inicial_f

        total_actual = actual_as + actual_f


        resultado.append({

            "grado":grado,

            "inicial_as": inicial_as,
            "inicial_f": inicial_f,

            "retiros_as": retiros_as,
            "retiros_f": retiros_f,

            "actual_as": actual_as,
            "actual_f": actual_f,

            "retencion":
                round(
                    (total_actual / total_inicial)*100,2
                )
                if total_inicial else 0
        })


    return resultado