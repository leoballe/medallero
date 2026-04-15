const provinciaOptionsHtml = `
<option value="">Seleccionar provincia</option>
${window.PROVINCIAS_OPTIONS_HTML || ""}
`;

const counters = {
    oro: 1,
    plata: 1,
    bronce: 1
};

function agregarProvincia(tipo) {
    counters[tipo] += 1;

    const container = document.getElementById(`${tipo}-container`);
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.gap = "10px";
    row.style.marginBottom = "10px";

    row.innerHTML = `
        <select name="${tipo}_${counters[tipo]}">
            ${provinciaOptionsHtml}
        </select>
        <button type="button" onclick="eliminarProvincia(this)">−</button>
    `;

    container.appendChild(row);
}

function eliminarProvincia(button) {
    const row = button.parentElement;
    row.remove();
}

function actualizarVisibilidadClase() {
    const adaptadoCheckbox = document.getElementById("adaptado_checkbox");
    const claseContainer = document.getElementById("clase-container");
    const claseSelect = document.getElementById("clase");

    if (!adaptadoCheckbox || !claseContainer || !claseSelect) {
        return;
    }

    if (adaptadoCheckbox.checked) {
        claseContainer.style.display = "flex";
    } else {
        claseContainer.style.display = "none";
        claseSelect.value = "";
    }
}

function esSelectDeProvincia(select) {
    if (!select) return false;

    const id = (select.id || "").toLowerCase();
    const name = (select.name || "").toLowerCase();
    const className = (select.className || "").toLowerCase();

    if (
        id.includes("provincia") ||
        name.includes("provincia") ||
        className.includes("provincia")
    ) {
        return true;
    }

    const optionTexts = Array.from(select.options).map(opt => opt.textContent.trim().toLowerCase());

    const provinciasReferencia = [
        "buenos aires",
        "córdoba",
        "cordoba",
        "santa fe",
        "mendoza",
        "tucumán",
        "tucuman",
        "entre ríos",
        "entre rios",
        "salta",
        "chaco",
        "misiones"
    ];

    const coincidencias = provinciasReferencia.filter(p => optionTexts.includes(p)).length;

    return coincidencias >= 3;
}
function agregarOpcionOtroASelect(select) {
    return;
}

function agregarOpcionOtroAProvincias() {
    return;
}
function inicializarFiltrosDependientes() {
    const eventoSelect = document.getElementById("evento");
    const disciplinaSelect = document.getElementById("disciplina");
    const pruebaSelect = document.getElementById("prueba");

    if (!eventoSelect || !disciplinaSelect || !pruebaSelect) {
        return;
    }

    if (typeof RELACIONES_EVENTO_DISCIPLINA === "undefined") {
        return;
    }

    if (typeof RELACIONES_DISCIPLINA_PRUEBA === "undefined") {
        return;
    }

    const disciplinasOriginales = Array.from(disciplinaSelect.options).map(opt => ({
        value: opt.value,
        text: opt.textContent
    }));

    const pruebasOriginales = Array.from(pruebaSelect.options).map(opt => ({
        value: opt.value,
        text: opt.textContent
    }));

    function reconstruirDisciplinas() {
        const eventoSeleccionado = eventoSelect.value;
        const valorActualDisciplina = disciplinaSelect.value;

        disciplinaSelect.innerHTML = "";

        const optionDefault = document.createElement("option");
        optionDefault.value = "";
        optionDefault.textContent = "Seleccionar";
        disciplinaSelect.appendChild(optionDefault);

        if (!eventoSeleccionado) {
            disciplinasOriginales.forEach(opt => {
                if (opt.value !== "") {
                    const nuevaOpcion = document.createElement("option");
                    nuevaOpcion.value = opt.value;
                    nuevaOpcion.textContent = opt.text;

                    if (opt.value === valorActualDisciplina) {
                        nuevaOpcion.selected = true;
                    }

                    disciplinaSelect.appendChild(nuevaOpcion);
                }
            });

            return;
        }

        const disciplinasPermitidas = RELACIONES_EVENTO_DISCIPLINA
            .filter(r => r.evento === eventoSeleccionado)
            .map(r => r.disciplina);

        disciplinasOriginales.forEach(opt => {
            if (opt.value !== "" && disciplinasPermitidas.includes(opt.value)) {
                const nuevaOpcion = document.createElement("option");
                nuevaOpcion.value = opt.value;
                nuevaOpcion.textContent = opt.text;

                if (opt.value === valorActualDisciplina) {
                    nuevaOpcion.selected = true;
                }

                disciplinaSelect.appendChild(nuevaOpcion);
            }
        });
    }

    function reconstruirPruebas() {
        const disciplinaSeleccionada = disciplinaSelect.value;
        const valorActualPrueba = pruebaSelect.value;

        pruebaSelect.innerHTML = "";

        const optionDefault = document.createElement("option");
        optionDefault.value = "";
        optionDefault.textContent = "Seleccionar";
        pruebaSelect.appendChild(optionDefault);

        if (!disciplinaSeleccionada) {
            pruebasOriginales.forEach(opt => {
                if (opt.value !== "") {
                    const nuevaOpcion = document.createElement("option");
                    nuevaOpcion.value = opt.value;
                    nuevaOpcion.textContent = opt.text;

                    if (opt.value === valorActualPrueba) {
                        nuevaOpcion.selected = true;
                    }

                    pruebaSelect.appendChild(nuevaOpcion);
                }
            });

            return;
        }

        const pruebasPermitidas = RELACIONES_DISCIPLINA_PRUEBA
            .filter(r => r.disciplina === disciplinaSeleccionada)
            .map(r => r.prueba);

        pruebasOriginales.forEach(opt => {
            if (opt.value !== "" && pruebasPermitidas.includes(opt.value)) {
                const nuevaOpcion = document.createElement("option");
                nuevaOpcion.value = opt.value;
                nuevaOpcion.textContent = opt.text;

                if (opt.value === valorActualPrueba) {
                    nuevaOpcion.selected = true;
                }

                pruebaSelect.appendChild(nuevaOpcion);
            }
        });
    }

    eventoSelect.addEventListener("change", function () {
        disciplinaSelect.value = "";
        pruebaSelect.value = "";
        reconstruirDisciplinas();
        reconstruirPruebas();
    });

    disciplinaSelect.addEventListener("change", function () {
        pruebaSelect.value = "";
        reconstruirPruebas();
    });

    reconstruirDisciplinas();
    reconstruirPruebas();
}

document.addEventListener("DOMContentLoaded", function () {
    const adaptadoCheckbox = document.getElementById("adaptado_checkbox");

    actualizarVisibilidadClase();

    if (adaptadoCheckbox) {
        adaptadoCheckbox.addEventListener("change", actualizarVisibilidadClase);
    }

    agregarOpcionOtroAProvincias();

    const observer = new MutationObserver(function () {
        agregarOpcionOtroAProvincias();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    inicializarFiltrosDependientes();

    const formulariosEliminar = document.querySelectorAll('form[action^="/eliminar/"]');

    formulariosEliminar.forEach(form => {
        form.addEventListener("submit", function () {
            sessionStorage.setItem("scrollPosMedallero", String(window.scrollY));
        });
    });

    const scrollGuardado = sessionStorage.getItem("scrollPosMedallero");

    if (scrollGuardado !== null) {
        window.scrollTo(0, parseInt(scrollGuardado, 10));
        sessionStorage.removeItem("scrollPosMedallero");
    }
});