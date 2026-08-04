// ======================================================
// CIEM ACADEMICO 2026
// MODULO DE NOTAS
// Calculo de cortes sobre 10 puntos
// ======================================================


document.addEventListener("DOMContentLoaded", () => {


    const filas = document.querySelectorAll("tbody tr");

    const promedioGeneral =
        document.getElementById("promedioGeneral");

    const aprobados =
        document.getElementById("aprobados");

    const riesgo =
        document.getElementById("riesgo");



    // ======================================================
    // ACTUALIZAR CALCULOS
    // ======================================================


    function calcularNotas() {


        let sumaCortes = 0;

        let cantidadEstudiantes = 0;

        let totalAprobados = 0;

        let totalRiesgo = 0;



        filas.forEach(fila => {



            const inputs =
                fila.querySelectorAll(".nota");



            let acumulado = 0;

            let actividades = 0;



            inputs.forEach(input => {



                let valor =
                    parseFloat(input.value);



                if (!isNaN(valor)) {


                    acumulado += valor;

                    actividades++;



                    // ------------------------------
                    // COLOR DE NOTA
                    // ------------------------------


                    if (valor >= 8) {

                        input.style.background =
                            "#d1fae5";

                        input.style.border =
                            "2px solid #16a34a";

                    } else if (valor >= 6) {

                        input.style.background =
                            "#fef3c7";

                        input.style.border =
                            "2px solid #f59e0b";

                    } else if (valor > 0) {

                        input.style.background =
                            "#fee2e2";

                        input.style.border =
                            "2px solid #dc2626";

                    }


                }



            });




            const campoAcumulado =
                fila.querySelector(".acumulado");



            const campoCorte =
                fila.querySelector(".promedio");



            const campoEstado =
                fila.querySelector(".estado");




            if (actividades > 0) {



                // ------------------------------
                // TOTAL SOBRE 100
                // ------------------------------

                campoAcumulado.innerHTML =
                    acumulado + " / 100";




                // ------------------------------
                // CONVERSION A CORTE SOBRE 10
                // ------------------------------

                let corte =
                    (acumulado / 10).toFixed(2);



                campoCorte.innerHTML =
                    corte;



                sumaCortes +=
                    parseFloat(corte);



                cantidadEstudiantes++;




                // ------------------------------
                // ESTADO
                // ------------------------------


                if (corte >= 6) {


                    campoEstado.innerHTML =
                        "Aprobado";


                    campoEstado.style.background =
                        "#d1fae5";


                    campoEstado.style.color =
                        "#166534";



                    totalAprobados++;


                } else {


                    campoEstado.innerHTML =
                        "Reforzamiento";


                    campoEstado.style.background =
                        "#fee2e2";


                    campoEstado.style.color =
                        "#991b1b";



                    totalRiesgo++;


                }



            } else {


                campoAcumulado.innerHTML =
                    "0 / 100";


                campoCorte.innerHTML =
                    "0.0";


                campoEstado.innerHTML =
                    "Pendiente";


                campoEstado.style.background =
                    "#eeeeee";


                campoEstado.style.color =
                    "#555";


            }




        });





        // ======================================================
        // TARJETAS SUPERIORES
        // ======================================================


        if (cantidadEstudiantes > 0) {


            promedioGeneral.innerHTML =
                (
                    sumaCortes /
                    cantidadEstudiantes
                ).toFixed(2);



        } else {


            promedioGeneral.innerHTML =
                "0.0";


        }



        aprobados.innerHTML =
            totalAprobados;



        riesgo.innerHTML =
            totalRiesgo;



    }





    // ======================================================
    // ESCUCHAR CAMBIOS EN EP
    // ======================================================


    document.querySelectorAll(".nota")
        .forEach(input => {


            input.addEventListener(
                "input",
                calcularNotas
            );


        });





    // ======================================================
    // BUSCADOR DE ESTUDIANTES
    // ======================================================


    const buscador =
        document.getElementById("buscar");



    if (buscador) {


        buscador.addEventListener(
            "keyup",
            () => {


                let texto =
                    buscador.value.toLowerCase();



                filas.forEach(fila => {


                    let nombre =
                        fila.querySelector(".nombre")
                        .innerText
                        .toLowerCase();




                    if (nombre.includes(texto)) {


                        fila.style.display = "";


                    } else {


                        fila.style.display = "none";


                    }



                });



            });



    }





    // Ejecutar al cargar

    calcularNotas();



});