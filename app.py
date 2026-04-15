from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from utils.db import get_connection, init_db
import pandas as pd
import io
import csv

app = Flask(__name__)
app.secret_key = "clave-simple"


@app.route("/")
def index():
    conn = get_connection()

    filtro_evento = request.args.get("evento", "").strip()
    filtro_disciplina = request.args.get("disciplina", "").strip()
    filtro_genero = request.args.get("genero", "").strip()
    filtro_categoria = request.args.get("categoria", "").strip()
    filtro_provincia = request.args.get("provincia", "").strip()
    filtro_medalla = request.args.get("medalla", "").strip()
    busqueda = request.args.get("q", "").strip()

    query_registros = """
        SELECT id, evento, disciplina, prueba, genero, categoria, adaptado, clase, provincia, medalla
        FROM medals
        WHERE 1 = 1
    """
    params_registros = []

    if filtro_evento:
        query_registros += " AND evento = ?"
        params_registros.append(filtro_evento)

    if filtro_disciplina:
        query_registros += " AND disciplina = ?"
        params_registros.append(filtro_disciplina)

    if filtro_genero:
        query_registros += " AND genero = ?"
        params_registros.append(filtro_genero)

    if filtro_categoria:
        query_registros += " AND categoria = ?"
        params_registros.append(filtro_categoria)

    if filtro_provincia:
        query_registros += " AND provincia = ?"
        params_registros.append(filtro_provincia)

    if filtro_medalla:
        query_registros += " AND medalla = ?"
        params_registros.append(filtro_medalla)

    if busqueda:
        query_registros += """
            AND (
                evento LIKE ?
                OR disciplina LIKE ?
                OR prueba LIKE ?
                OR genero LIKE ?
                OR categoria LIKE ?
                OR provincia LIKE ?
            )
        """
        like = f"%{busqueda}%"
        params_registros.extend([like, like, like, like, like, like])

    query_registros += " ORDER BY id DESC"

    registros = conn.execute(query_registros, params_registros).fetchall()

    query_medallero = """
        SELECT
            provincia,
            SUM(CASE WHEN medalla = 'oro' THEN 1 ELSE 0 END) AS oros,
            SUM(CASE WHEN medalla = 'plata' THEN 1 ELSE 0 END) AS platas,
            SUM(CASE WHEN medalla = 'bronce' THEN 1 ELSE 0 END) AS bronces,
            COUNT(*) AS total
        FROM medals
        WHERE 1 = 1
    """
    params_medallero = []

    if filtro_evento:
        query_medallero += " AND evento = ?"
        params_medallero.append(filtro_evento)

    if filtro_disciplina:
        query_medallero += " AND disciplina = ?"
        params_medallero.append(filtro_disciplina)

    if filtro_genero:
        query_medallero += " AND genero = ?"
        params_medallero.append(filtro_genero)

    if filtro_categoria:
        query_medallero += " AND categoria = ?"
        params_medallero.append(filtro_categoria)

    if filtro_provincia:
        query_medallero += " AND provincia = ?"
        params_medallero.append(filtro_provincia)

    if filtro_medalla:
        query_medallero += " AND medalla = ?"
        params_medallero.append(filtro_medalla)

    if busqueda:
        query_medallero += """
            AND (
                evento LIKE ?
                OR disciplina LIKE ?
                OR prueba LIKE ?
                OR genero LIKE ?
                OR categoria LIKE ?
                OR provincia LIKE ?
            )
        """
        like = f"%{busqueda}%"
        params_medallero.extend([like, like, like, like, like, like])

    query_medallero += """
        GROUP BY provincia
        ORDER BY
            oros DESC,
            platas DESC,
            bronces DESC,
            provincia ASC
    """

    medallero = conn.execute(query_medallero, params_medallero).fetchall()

    eventos = conn.execute("""
        SELECT name
        FROM catalog_events
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    disciplinas = conn.execute("""
        SELECT name
        FROM catalog_disciplines
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    generos = conn.execute("""
        SELECT name
        FROM catalog_genders
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    categorias = conn.execute("""
        SELECT name
        FROM catalog_categories
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    pruebas = conn.execute("""
        SELECT name
        FROM catalog_tests
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    clases = conn.execute("""
        SELECT name
        FROM catalog_classes
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    provincias = conn.execute("""
        SELECT name
        FROM catalog_provinces
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    relaciones_evento_disciplina_rows = conn.execute("""
        SELECT evento, disciplina
        FROM catalog_event_disciplines
        ORDER BY evento, disciplina
    """).fetchall()

    relaciones_evento_disciplina = [
        {
            "evento": row["evento"],
            "disciplina": row["disciplina"]
        }
        for row in relaciones_evento_disciplina_rows
    ]

    relaciones_disciplina_prueba_rows = conn.execute("""
        SELECT disciplina, prueba
        FROM catalog_discipline_tests
        ORDER BY disciplina, prueba
    """).fetchall()

    relaciones_disciplina_prueba = [
        {
            "disciplina": row["disciplina"],
            "prueba": row["prueba"]
        }
        for row in relaciones_disciplina_prueba_rows
    ]

    conn.close()

    filtros = {
        "evento": filtro_evento,
        "disciplina": filtro_disciplina,
        "genero": filtro_genero,
        "categoria": filtro_categoria,
        "provincia": filtro_provincia,
        "medalla": filtro_medalla,
        "q": busqueda
    }

    return render_template(
        "index.html",
        registros=registros,
        eventos=eventos,
        disciplinas=disciplinas,
        generos=generos,
        pruebas=pruebas,
        clases=clases,
        categorias=categorias,
        provincias=provincias,
        medallero=medallero,
        filtros=filtros,
        relaciones_evento_disciplina=relaciones_evento_disciplina,
        relaciones_disciplina_prueba=relaciones_disciplina_prueba
    )

@app.route("/medallero")
def ver_medallero():
    conn = get_connection()

    filtro_evento = request.args.get("evento", "").strip()
    filtro_disciplina = request.args.get("disciplina", "").strip()
    filtro_genero = request.args.get("genero", "").strip()
    filtro_categoria = request.args.get("categoria", "").strip()
    filtro_provincia = request.args.get("provincia", "").strip()
    filtro_medalla = request.args.get("medalla", "").strip()
    busqueda = request.args.get("q", "").strip()

    query_medallero = """
        SELECT
            provincia,
            SUM(CASE WHEN medalla = 'oro' THEN 1 ELSE 0 END) AS oros,
            SUM(CASE WHEN medalla = 'plata' THEN 1 ELSE 0 END) AS platas,
            SUM(CASE WHEN medalla = 'bronce' THEN 1 ELSE 0 END) AS bronces,
            COUNT(*) AS total
        FROM medals
        WHERE 1 = 1
    """
    params_medallero = []

    if filtro_evento:
        query_medallero += " AND evento = ?"
        params_medallero.append(filtro_evento)

    if filtro_disciplina:
        query_medallero += " AND disciplina = ?"
        params_medallero.append(filtro_disciplina)

    if filtro_genero:
        query_medallero += " AND genero = ?"
        params_medallero.append(filtro_genero)

    if filtro_categoria:
        query_medallero += " AND categoria = ?"
        params_medallero.append(filtro_categoria)

    if filtro_provincia:
        query_medallero += " AND provincia = ?"
        params_medallero.append(filtro_provincia)

    if filtro_medalla:
        query_medallero += " AND medalla = ?"
        params_medallero.append(filtro_medalla)

    if busqueda:
        query_medallero += """
            AND (
                evento LIKE ?
                OR disciplina LIKE ?
                OR prueba LIKE ?
                OR genero LIKE ?
                OR categoria LIKE ?
                OR provincia LIKE ?
            )
        """
        like = f"%{busqueda}%"
        params_medallero.extend([like, like, like, like, like, like])

    query_medallero += """
        GROUP BY provincia
        ORDER BY
            oros DESC,
            platas DESC,
            bronces DESC,
            provincia ASC
    """

    medallero = conn.execute(query_medallero, params_medallero).fetchall()

    eventos = conn.execute("""
        SELECT name
        FROM catalog_events
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    disciplinas = conn.execute("""
        SELECT name
        FROM catalog_disciplines
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    generos = conn.execute("""
        SELECT name
        FROM catalog_genders
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    categorias = conn.execute("""
        SELECT name
        FROM catalog_categories
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    provincias = conn.execute("""
        SELECT name
        FROM catalog_provinces
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    relaciones_evento_disciplina = conn.execute("""
        SELECT id, evento, disciplina
        FROM catalog_event_disciplines
        ORDER BY evento, disciplina
    """).fetchall()

    relaciones_disciplina_prueba = conn.execute("""
        SELECT id, disciplina, prueba
        FROM catalog_discipline_tests
        ORDER BY disciplina, prueba
    """).fetchall()

    relaciones_evento_disciplina = [dict(row) for row in relaciones_evento_disciplina]
    relaciones_disciplina_prueba = [dict(row) for row in relaciones_disciplina_prueba]

    conn.close()

    filtros = {
        "evento": filtro_evento,
        "disciplina": filtro_disciplina,
        "genero": filtro_genero,
        "categoria": filtro_categoria,
        "provincia": filtro_provincia,
        "medalla": filtro_medalla,
        "q": busqueda
    }

    return render_template(
        "medallero.html",
        medallero=medallero,
        eventos=eventos,
        disciplinas=disciplinas,
        generos=generos,
        categorias=categorias,
        provincias=provincias,
        filtros=filtros,
        relaciones_evento_disciplina=relaciones_evento_disciplina,
        relaciones_disciplina_prueba=relaciones_disciplina_prueba
    )
@app.route("/verificar_duplicado_medalla", methods=["POST"])
def verificar_duplicado_medalla():
    evento = request.form.get("evento", "").strip()
    disciplina = request.form.get("disciplina", "").strip()
    prueba = request.form.get("prueba", "").strip()
    genero = request.form.get("genero", "").strip()
    categoria = request.form.get("categoria", "").strip()
    adaptado = "Sí" if request.form.get("adaptado") == "Sí" else "No"
    clase = request.form.get("clase", "").strip()

    medallas_a_verificar = []

    for key in request.form.keys():
        value = request.form.get(key, "").strip()

        if not value:
            continue

        if key.startswith("oro_"):
            medallas_a_verificar.append((value, "oro"))
        elif key.startswith("plata_"):
            medallas_a_verificar.append((value, "plata"))
        elif key.startswith("bronce_"):
            medallas_a_verificar.append((value, "bronce"))

    conn = get_connection()

    duplicadas = []

    for provincia, medalla in medallas_a_verificar:
        existente = conn.execute("""
            SELECT id
            FROM medals
            WHERE evento = ?
              AND disciplina = ?
              AND prueba = ?
              AND genero = ?
              AND categoria = ?
              AND adaptado = ?
              AND clase = ?
              AND provincia = ?
              AND medalla = ?
            LIMIT 1
        """, (
            evento,
            disciplina,
            prueba,
            genero,
            categoria,
            adaptado,
            clase,
            provincia,
            medalla
        )).fetchone()

        if existente:
            duplicadas.append({
                "id": existente["id"],
                "provincia": provincia,
                "medalla": medalla
            })

    conn.close()

    return jsonify({
        "hay_duplicadas": len(duplicadas) > 0,
        "duplicadas": duplicadas
    })
@app.route("/guardar", methods=["POST"])
def guardar():
    evento = request.form.get("evento", "").strip()
    disciplina = request.form.get("disciplina", "").strip()
    prueba = request.form.get("prueba", "").strip()
    genero = request.form.get("genero", "").strip()
    categoria = request.form.get("categoria", "").strip()
    adaptado = "Sí" if request.form.get("adaptado") == "Sí" else "No"
    clase = request.form.get("clase", "").strip()

    if not evento:
        flash("El campo Evento es obligatorio.")
        return redirect(url_for("index"))

    if not disciplina:
        flash("El campo Disciplina es obligatorio.")
        return redirect(url_for("index"))

    if not genero:
        flash("El campo Género es obligatorio.")
        return redirect(url_for("index"))

    if not categoria:
        flash("El campo Categoria es obligatorio.")
        return redirect(url_for("index"))
    if adaptado == "Sí" and not clase:
        flash("Si está marcado 'Es adaptado', el campo Clase es obligatorio.")
        return redirect(url_for("index"))

    medallas_a_guardar = []

    for key in request.form.keys():
        value = request.form.get(key, "").strip()

        if not value:
            continue

        if key.startswith("oro_"):
            medallas_a_guardar.append((value, "oro"))
        elif key.startswith("plata_"):
            medallas_a_guardar.append((value, "plata"))
        elif key.startswith("bronce_"):
            medallas_a_guardar.append((value, "bronce"))

    if not medallas_a_guardar:
        flash("Tenés que cargar al menos una provincia en ORO, PLATA o BRONCE.")
        return redirect(url_for("index"))

    confirmar_duplicado = request.form.get("confirmar_duplicado", "").strip() == "1"

    conn = get_connection()

    duplicadas = []
    ids_duplicadas = []

    for provincia, medalla in medallas_a_guardar:
        existente = conn.execute("""
            SELECT id
            FROM medals
            WHERE evento = ?
              AND disciplina = ?
              AND prueba = ?
              AND genero = ?
              AND categoria = ?
              AND adaptado = ?
              AND clase = ?
              AND provincia = ?
              AND medalla = ?
            LIMIT 1
        """, (
            evento,
            disciplina,
            prueba,
            genero,
            categoria,
            adaptado,
            clase,
            provincia,
            medalla
        )).fetchone()

        if existente:
            duplicadas.append((provincia, medalla))
            ids_duplicadas.append(str(existente["id"]))

    if duplicadas and not confirmar_duplicado:
        conn.close()
        flash("Esa medalla ya fue cargada. Confirmá la carga para continuar.")
        return redirect(url_for("index"))

    for provincia, medalla in medallas_a_guardar:
        conn.execute("""
            INSERT INTO medals (
                evento,
                disciplina,
                prueba,
                genero,
                categoria,
                adaptado,
                clase,
                provincia,
                medalla
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evento,
            disciplina,
            prueba,
            genero,
            categoria,
            adaptado,
            clase,
            provincia,
            medalla
        ))

    conn.commit()
    conn.close()

    flash(f"Se guardaron {len(medallas_a_guardar)} medalla(s) correctamente.")
    return redirect(url_for("index", resaltar_duplicadas=",".join(ids_duplicadas)))


@app.route("/editar/<int:registro_id>")
def editar(registro_id):
    conn = get_connection()

    registro = conn.execute("""
        SELECT id, evento, disciplina, prueba, genero, categoria, adaptado, clase, provincia, medalla
        FROM medals
        WHERE id = ?
    """, (registro_id,)).fetchone()

    if not registro:
        conn.close()
        flash("No se encontró el registro a editar.")
        return redirect(url_for("index"))

    eventos = conn.execute("""
        SELECT name
        FROM catalog_events
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    disciplinas = conn.execute("""
        SELECT name
        FROM catalog_disciplines
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    generos = conn.execute("""
        SELECT name
        FROM catalog_genders
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    categorias = conn.execute("""
        SELECT name
        FROM catalog_categories
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    pruebas = conn.execute("""
        SELECT name
        FROM catalog_tests
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    clases = conn.execute("""
        SELECT name
        FROM catalog_classes
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    provincias = conn.execute("""
        SELECT name
        FROM catalog_provinces
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    relaciones_evento_disciplina_rows = conn.execute("""
        SELECT evento, disciplina
        FROM catalog_event_disciplines
        ORDER BY evento, disciplina
    """).fetchall()

    relaciones_evento_disciplina = [
        {
            "evento": row["evento"],
            "disciplina": row["disciplina"]
        }
        for row in relaciones_evento_disciplina_rows
    ]

    relaciones_disciplina_prueba_rows = conn.execute("""
        SELECT disciplina, prueba
        FROM catalog_discipline_tests
        ORDER BY disciplina, prueba
    """).fetchall()

    relaciones_disciplina_prueba = [
        {
            "disciplina": row["disciplina"],
            "prueba": row["prueba"]
        }
        for row in relaciones_disciplina_prueba_rows
    ]

    conn.close()

    return render_template(
        "edit.html",
        registro=registro,
        eventos=eventos,
        disciplinas=disciplinas,
        generos=generos,
        pruebas=pruebas,
        clases=clases,
        categorias=categorias,
        provincias=provincias,
        relaciones_evento_disciplina=relaciones_evento_disciplina,
        relaciones_disciplina_prueba=relaciones_disciplina_prueba
    )


@app.route("/actualizar/<int:registro_id>", methods=["POST"])
def actualizar(registro_id):
    evento = request.form.get("evento", "").strip()
    disciplina = request.form.get("disciplina", "").strip()
    prueba = request.form.get("prueba", "").strip()
    genero = request.form.get("genero", "").strip()
    categoria = request.form.get("categoria", "").strip()
    adaptado = "Sí" if request.form.get("adaptado") == "Sí" else "No"
    clase = request.form.get("clase", "").strip()
    provincia = request.form.get("provincia", "").strip()
    medalla = request.form.get("medalla", "").strip()

    if not evento:
        flash("El campo Evento es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    if not disciplina:
        flash("El campo Disciplina es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    if not genero:
        flash("El campo Género es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    if not categoria:
        flash("El campo Categoria es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    if adaptado == "Sí" and not clase:
        flash("Si está marcado 'Es adaptado', el campo Clase es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    if not provincia:
        flash("El campo Provincia es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    if medalla not in ["oro", "plata", "bronce"]:
        flash("El campo Medalla es obligatorio.")
        return redirect(url_for("editar", registro_id=registro_id))

    conn = get_connection()

    existe = conn.execute("""
        SELECT id
        FROM medals
        WHERE id = ?
    """, (registro_id,)).fetchone()

    if not existe:
        conn.close()
        flash("No se encontró el registro a actualizar.")
        return redirect(url_for("index"))

    conn.execute("""
        UPDATE medals
        SET evento = ?,
            disciplina = ?,
            prueba = ?,
            genero = ?,
            categoria = ?,
            adaptado = ?,
            clase = ?,
            provincia = ?,
            medalla = ?
        WHERE id = ?
    """, (
        evento,
        disciplina,
        prueba,
        genero,
        categoria,
        adaptado,
        clase,
        provincia,
        medalla,
        registro_id
    ))

    conn.commit()
    conn.close()

    flash("Registro actualizado correctamente.")
    return redirect(url_for("index"))

@app.route("/eliminar_seleccionados", methods=["POST"])
def eliminar_seleccionados():
    ids = request.form.getlist("ids")

    if not ids:
        flash("No seleccionaste ningún registro para eliminar.")
        return redirect(url_for("index"))

    ids_validos = []
    for item in ids:
        try:
            ids_validos.append(int(item))
        except:
            continue

    if not ids_validos:
        flash("No hay registros válidos para eliminar.")
        return redirect(url_for("index"))

    conn = get_connection()

    placeholders = ",".join(["?"] * len(ids_validos))

    conn.execute(f"""
        DELETE FROM medals
        WHERE id IN ({placeholders})
    """, ids_validos)

    conn.commit()
    conn.close()

    flash(f"Se eliminaron {len(ids_validos)} registro(s) correctamente.")
    return redirect(url_for("index"))
@app.route("/eliminar/<int:registro_id>", methods=["POST"])
def eliminar(registro_id):
    conn = get_connection()

    existe = conn.execute("""
        SELECT id
        FROM medals
        WHERE id = ?
    """, (registro_id,)).fetchone()

    if not existe:
        conn.close()
        flash("No se encontró el registro a eliminar.")
        return redirect(url_for("index"))

    conn.execute("""
        DELETE FROM medals
        WHERE id = ?
    """, (registro_id,))

    conn.commit()
    conn.close()

    flash("Registro eliminado correctamente.")
    return redirect(url_for("index"))


@app.route("/exportar_excel")
def exportar_excel():
    conn = get_connection()

    filtro_evento = request.args.get("evento", "").strip()
    filtro_disciplina = request.args.get("disciplina", "").strip()
    filtro_genero = request.args.get("genero", "").strip()
    filtro_categoria = request.args.get("categoria", "").strip()
    filtro_provincia = request.args.get("provincia", "").strip()
    filtro_medalla = request.args.get("medalla", "").strip()
    busqueda = request.args.get("q", "").strip()

    query_registros = """
        SELECT
            evento,
            disciplina,
            prueba,
            genero,
            categoria,
            adaptado,
            clase,
            provincia,
            medalla
        FROM medals
        WHERE 1 = 1
    """
    params_registros = []

    if filtro_evento:
        query_registros += " AND evento = ?"
        params_registros.append(filtro_evento)

    if filtro_disciplina:
        query_registros += " AND disciplina = ?"
        params_registros.append(filtro_disciplina)

    if filtro_genero:
        query_registros += " AND genero = ?"
        params_registros.append(filtro_genero)

    if filtro_categoria:
        query_registros += " AND categoria = ?"
        params_registros.append(filtro_categoria)

    if filtro_provincia:
        query_registros += " AND provincia = ?"
        params_registros.append(filtro_provincia)

    if filtro_medalla:
        query_registros += " AND medalla = ?"
        params_registros.append(filtro_medalla)

    if busqueda:
        query_registros += """
            AND (
                evento LIKE ?
                OR disciplina LIKE ?
                OR prueba LIKE ?
                OR genero LIKE ?
                OR categoria LIKE ?
                OR provincia LIKE ?
            )
        """
        like = f"%{busqueda}%"
        params_registros.extend([like, like, like, like, like, like])

    query_registros += " ORDER BY id DESC"

    registros = conn.execute(query_registros, params_registros).fetchall()

    query_medallero = """
        SELECT
            provincia,
            SUM(CASE WHEN medalla = 'oro' THEN 1 ELSE 0 END) AS oros,
            SUM(CASE WHEN medalla = 'plata' THEN 1 ELSE 0 END) AS platas,
            SUM(CASE WHEN medalla = 'bronce' THEN 1 ELSE 0 END) AS bronces,
            COUNT(*) AS total
        FROM medals
        WHERE 1 = 1
    """
    params_medallero = []

    if filtro_evento:
        query_medallero += " AND evento = ?"
        params_medallero.append(filtro_evento)

    if filtro_disciplina:
        query_medallero += " AND disciplina = ?"
        params_medallero.append(filtro_disciplina)

    if filtro_genero:
        query_medallero += " AND genero = ?"
        params_medallero.append(filtro_genero)

    if filtro_categoria:
        query_medallero += " AND categoria = ?"
        params_medallero.append(filtro_categoria)

    if filtro_provincia:
        query_medallero += " AND provincia = ?"
        params_medallero.append(filtro_provincia)

    if filtro_medalla:
        query_medallero += " AND medalla = ?"
        params_medallero.append(filtro_medalla)

    if busqueda:
        query_medallero += """
            AND (
                evento LIKE ?
                OR disciplina LIKE ?
                OR prueba LIKE ?
                OR genero LIKE ?
                OR categoria LIKE ?
                OR provincia LIKE ?
            )
        """
        like = f"%{busqueda}%"
        params_medallero.extend([like, like, like, like, like, like])

    query_medallero += """
        GROUP BY provincia
        ORDER BY
            oros DESC,
            platas DESC,
            bronces DESC,
            provincia ASC
    """

    medallero = conn.execute(query_medallero, params_medallero).fetchall()

    conn.close()

    data = []
    for registro in registros:
        data.append({
            "Evento": registro["evento"],
            "Disciplina": registro["disciplina"],
            "Prueba": registro["prueba"],
            "Género": registro["genero"],
            "Categoría": registro["categoria"],
            "Adaptado": registro["adaptado"],
            "Clase": registro["clase"],
            "Provincia": registro["provincia"],
            "Medalla": registro["medalla"]
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Medallero")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="medallero.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/catalogos")
def catalogos():
    conn = get_connection()

    eventos = conn.execute("""
        SELECT id, name, active
        FROM catalog_events
        ORDER BY name
    """).fetchall()

    disciplinas = conn.execute("""
        SELECT id, name, active
        FROM catalog_disciplines
        ORDER BY name
    """).fetchall()

    generos = conn.execute("""
        SELECT id, name, active
        FROM catalog_genders
        ORDER BY name
    """).fetchall()

    pruebas = conn.execute("""
        SELECT id, name, active
        FROM catalog_tests
        ORDER BY name
    """).fetchall()

    categorias = conn.execute("""
        SELECT id, name, active
        FROM catalog_categories
        ORDER BY name
    """).fetchall()

    clases = conn.execute("""
        SELECT id, name, active
        FROM catalog_classes
        ORDER BY name
    """).fetchall()

    provincias = conn.execute("""
        SELECT id, name, active
        FROM catalog_provinces
        ORDER BY name
    """).fetchall()

    relaciones_evento_disciplina = conn.execute("""
        SELECT id, evento, disciplina
        FROM catalog_event_disciplines
        ORDER BY evento, disciplina
    """).fetchall()

    eventos_activos = conn.execute("""
        SELECT name
        FROM catalog_events
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    disciplinas_activas = conn.execute("""
        SELECT name
        FROM catalog_disciplines
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    pruebas_activas = conn.execute("""
        SELECT name
        FROM catalog_tests
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    generos_activos = conn.execute("""
        SELECT name
        FROM catalog_genders
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    relaciones_disciplina_prueba = conn.execute("""
        SELECT id, disciplina, prueba
        FROM catalog_discipline_tests
        ORDER BY disciplina, prueba
    """).fetchall()

    relaciones_disciplina_prueba_genero = conn.execute("""
        SELECT id, disciplina, prueba, genero
        FROM catalog_discipline_test_genders
        ORDER BY disciplina, prueba, genero
    """).fetchall()

    conn.close()

    return render_template(
        "catalogos.html",
        eventos=eventos,
        disciplinas=disciplinas,
        generos=generos,
        pruebas=pruebas,
        categorias=categorias,
        clases=clases,
        provincias=provincias,
        relaciones_evento_disciplina=relaciones_evento_disciplina,
        eventos_activos=eventos_activos,
        disciplinas_activas=disciplinas_activas,
        pruebas_activas=pruebas_activas,
        generos_activos=generos_activos,
        relaciones_disciplina_prueba=relaciones_disciplina_prueba,
        relaciones_disciplina_prueba_genero=relaciones_disciplina_prueba_genero
    )


@app.route("/catalogos/agregar", methods=["POST"])
def agregar_catalogo():
    tipo_catalogo = request.form.get("tipo_catalogo", "").strip()
    nombre_nuevo = request.form.get("nombre_nuevo", "").strip()

    if not tipo_catalogo:
        flash("Tenés que seleccionar un catálogo.")
        return redirect(url_for("catalogos"))

    if not nombre_nuevo:
        flash("Tenés que escribir un nombre.")
        return redirect(url_for("catalogos"))

    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    tabla = tablas[tipo_catalogo]

    conn = get_connection()

    existente = conn.execute(
        f"SELECT id FROM {tabla} WHERE lower(name) = lower(?)",
        (nombre_nuevo,)
    ).fetchone()

    if existente:
        conn.close()
        flash("Ese valor ya existe en el catálogo seleccionado.")
        return redirect(url_for("catalogos"))

    conn.execute(
        f"INSERT INTO {tabla} (name, active) VALUES (?, 1)",
        (nombre_nuevo,)
    )
    conn.commit()
    conn.close()

    flash("Nuevo valor agregado correctamente.")
    return redirect(url_for("catalogos"))
@app.route("/catalogos/importar_csv", methods=["POST"])
def importar_catalogo_csv():
    tipo_catalogo = request.form.get("tipo_catalogo_csv", "").strip()
    archivo = request.files.get("archivo_csv")

    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    if not tipo_catalogo:
        flash("Tenés que seleccionar un catálogo para importar.")
        return redirect(url_for("catalogos"))

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    if not archivo or archivo.filename.strip() == "":
        flash("Tenés que seleccionar un archivo CSV.")
        return redirect(url_for("catalogos"))

    if not archivo.filename.lower().endswith(".csv"):
        flash("El archivo tiene que ser un CSV.")
        return redirect(url_for("catalogos"))

    tabla = tablas[tipo_catalogo]

    # ---- LECTURA ROBUSTA DEL CSV ----
    try:
        data = archivo.stream.read()

        contenido = None

        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                contenido = data.decode(encoding)
                break
            except:
                continue

        if contenido is None:
            flash("No se pudo leer el CSV.")
            return redirect(url_for("catalogos"))

    except:
        flash("Error al leer el archivo.")
        return redirect(url_for("catalogos"))

    # ---- PROCESAMIENTO ----
    lector = csv.reader(io.StringIO(contenido))

    valores = []

    for fila in lector:
        if not fila:
            continue

        valor = fila[0].strip()

        if not valor:
            continue

        valores.append(valor)

    if not valores:
        flash("El CSV está vacío o mal formado.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    insertados = 0
    duplicados = 0

    for valor in valores:
        existente = conn.execute(
            f"SELECT id FROM {tabla} WHERE lower(name) = lower(?)",
            (valor,)
        ).fetchone()

        if existente:
            duplicados += 1
            continue

        conn.execute(
            f"INSERT INTO {tabla} (name, active) VALUES (?, 1)",
            (valor,)
        )
        insertados += 1

    conn.commit()
    conn.close()

    flash(f"Importación: {insertados} nuevos, {duplicados} duplicados.")
    return redirect(url_for("catalogos"))
@app.route("/catalogos/toggle/<tipo_catalogo>/<int:item_id>", methods=["POST"])
def toggle_catalogo(tipo_catalogo, item_id):
    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    campos_medals = {
        "eventos": "evento",
        "disciplinas": "disciplina",
        "generos": "genero",
        "pruebas": "prueba",
        "categorias": "categoria",
        "clases": "clase",
        "provincias": "provincia"
    }

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    tabla = tablas[tipo_catalogo]
    campo_medals = campos_medals[tipo_catalogo]

    conn = get_connection()

    item = conn.execute(
        f"SELECT id, name, active FROM {tabla} WHERE id = ?",
        (item_id,)
    ).fetchone()

    if not item:
        conn.close()
        flash("No se encontró el elemento seleccionado.")
        return redirect(url_for("catalogos"))

    nuevo_estado = 0 if item["active"] == 1 else 1

    if item["active"] == 1:
        uso = conn.execute(
            f"SELECT id FROM medals WHERE {campo_medals} = ? LIMIT 1",
            (item["name"],)
        ).fetchone()

        if uso:
            conn.close()
            flash("No se puede desactivar porque está siendo utilizado en registros.")
            return redirect(url_for("catalogos"))

    conn.execute(
        f"UPDATE {tabla} SET active = ? WHERE id = ?",
        (nuevo_estado, item_id)
    )

    conn.commit()
    conn.close()

    if nuevo_estado == 1:
        flash("Elemento activado correctamente.")
    else:
        flash("Elemento desactivado correctamente.")

    return redirect(url_for("catalogos"))


@app.route("/catalogos/eliminar/<tipo_catalogo>/<int:item_id>", methods=["POST"])
def eliminar_catalogo(tipo_catalogo, item_id):
    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    campos_medals = {
        "eventos": "evento",
        "disciplinas": "disciplina",
        "generos": "genero",
        "pruebas": "prueba",
        "categorias": "categoria",
        "clases": "clase",
        "provincias": "provincia"
    }

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    tabla = tablas[tipo_catalogo]
    campo = campos_medals[tipo_catalogo]

    conn = get_connection()

    item = conn.execute(
        f"SELECT name FROM {tabla} WHERE id = ?",
        (item_id,)
    ).fetchone()

    if not item:
        conn.close()
        flash("Elemento no encontrado.")
        return redirect(url_for("catalogos"))

    nombre = item["name"]

    uso = conn.execute(
        f"SELECT id FROM medals WHERE {campo} = ? LIMIT 1",
        (nombre,)
    ).fetchone()

    if uso:
        conn.close()
        flash("No se puede eliminar porque está en uso.")
        return redirect(url_for("catalogos"))

    if tipo_catalogo == "eventos":
        conn.execute(
            "DELETE FROM catalog_event_disciplines WHERE evento = ?",
            (nombre,)
        )
    elif tipo_catalogo == "disciplinas":
        conn.execute(
            "DELETE FROM catalog_event_disciplines WHERE disciplina = ?",
            (nombre,)
        )
        conn.execute(
            "DELETE FROM catalog_discipline_tests WHERE disciplina = ?",
            (nombre,)
        )
    elif tipo_catalogo == "pruebas":
        conn.execute(
            "DELETE FROM catalog_discipline_tests WHERE prueba = ?",
            (nombre,)
        )

    conn.execute(
        f"DELETE FROM {tabla} WHERE id = ?",
        (item_id,)
    )

    conn.commit()
    conn.close()

    flash("Elemento eliminado correctamente.")
    return redirect(url_for("catalogos"))


@app.route("/catalogos/editar/<tipo_catalogo>/<int:item_id>")
def editar_catalogo(tipo_catalogo, item_id):
    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    titulos = {
        "eventos": "Eventos",
        "disciplinas": "Disciplinas",
        "generos": "Géneros",
        "pruebas": "Pruebas",
        "categorias": "Categorías",
        "clases": "Clases",
        "provincias": "Provincias"
    }

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    tabla = tablas[tipo_catalogo]

    conn = get_connection()

    item = conn.execute(
        f"SELECT id, name, active FROM {tabla} WHERE id = ?",
        (item_id,)
    ).fetchone()

    conn.close()

    if not item:
        flash("No se encontró el elemento seleccionado.")
        return redirect(url_for("catalogos"))

    return render_template(
        "editar_catalogo.html",
        item=item,
        tipo_catalogo=tipo_catalogo,
        titulo_catalogo=titulos[tipo_catalogo]
    )


@app.route("/catalogos/actualizar/<tipo_catalogo>/<int:item_id>", methods=["POST"])
def actualizar_catalogo(tipo_catalogo, item_id):
    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    nombre_nuevo = request.form.get("name", "").strip()

    if not nombre_nuevo:
        flash("El nombre no puede estar vacío.")
        return redirect(url_for("editar_catalogo", tipo_catalogo=tipo_catalogo, item_id=item_id))

    tabla = tablas[tipo_catalogo]

    conn = get_connection()

    item_actual = conn.execute(
        f"SELECT id, name FROM {tabla} WHERE id = ?",
        (item_id,)
    ).fetchone()

    if not item_actual:
        conn.close()
        flash("No se encontró el elemento seleccionado.")
        return redirect(url_for("catalogos"))

    duplicado = conn.execute(
        f"SELECT id FROM {tabla} WHERE lower(name) = lower(?) AND id <> ?",
        (nombre_nuevo, item_id)
    ).fetchone()

    if duplicado:
        conn.close()
        flash("Ya existe otro elemento con ese nombre en este catálogo.")
        return redirect(url_for("editar_catalogo", tipo_catalogo=tipo_catalogo, item_id=item_id))

    nombre_viejo = item_actual["name"]

    conn.execute(
        f"UPDATE {tabla} SET name = ? WHERE id = ?",
        (nombre_nuevo, item_id)
    )

    campos_medals = {
        "eventos": "evento",
        "disciplinas": "disciplina",
        "generos": "genero",
        "pruebas": "prueba",
        "categorias": "categoria",
        "clases": "clase",
        "provincias": "provincia"
    }

    campo_medals = campos_medals[tipo_catalogo]

    conn.execute(
        f"UPDATE medals SET {campo_medals} = ? WHERE {campo_medals} = ?",
        (nombre_nuevo, nombre_viejo)
    )

    if tipo_catalogo == "eventos":
        conn.execute(
            """
            UPDATE catalog_event_disciplines
            SET evento = ?
            WHERE evento = ?
            """,
            (nombre_nuevo, nombre_viejo)
        )
    elif tipo_catalogo == "disciplinas":
        conn.execute(
            """
            UPDATE catalog_event_disciplines
            SET disciplina = ?
            WHERE disciplina = ?
            """,
            (nombre_nuevo, nombre_viejo)
        )

        conn.execute(
            """
            UPDATE catalog_discipline_tests
            SET disciplina = ?
            WHERE disciplina = ?
            """,
            (nombre_nuevo, nombre_viejo)
        )
    elif tipo_catalogo == "pruebas":
        conn.execute(
            """
            UPDATE catalog_discipline_tests
            SET prueba = ?
            WHERE prueba = ?
            """,
            (nombre_nuevo, nombre_viejo)
        )

    conn.commit()
    conn.close()

    flash("Elemento actualizado correctamente.")
    return redirect(url_for("catalogos"))

@app.route("/catalogos/relacion/evento-disciplina/importar_csv", methods=["POST"])
def importar_relacion_evento_disciplina_csv():
    archivo = request.files.get("archivo_csv_relacion_evento_disciplina")

    if not archivo or archivo.filename.strip() == "":
        flash("Tenés que seleccionar un archivo CSV de relaciones Evento → Disciplina.")
        return redirect(url_for("catalogos"))

    if not archivo.filename.lower().endswith(".csv"):
        flash("El archivo tiene que ser un CSV.")
        return redirect(url_for("catalogos"))

    try:
        data = archivo.stream.read()

        contenido = None

        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                contenido = data.decode(encoding)
                break
            except:
                continue

        if contenido is None:
            flash("No se pudo leer el CSV de relaciones Evento → Disciplina.")
            return redirect(url_for("catalogos"))

    except:
        flash("Error al leer el archivo CSV de relaciones Evento → Disciplina.")
        return redirect(url_for("catalogos"))

    muestra_csv = contenido[:2048]

    try:
        dialecto = csv.Sniffer().sniff(muestra_csv, delimiters=",;")
        delimitador = dialecto.delimiter
    except:
        delimitador = ";"

    lector = csv.DictReader(io.StringIO(contenido), delimiter=delimitador)

    if not lector.fieldnames:
        flash("El CSV está vacío o mal formado.")
        return redirect(url_for("catalogos"))

    encabezados = [h.strip().lower() for h in lector.fieldnames if h]

    if "evento" not in encabezados or "disciplina" not in encabezados:
        flash("El CSV debe tener exactamente las columnas 'evento' y 'disciplina'.")
        return redirect(url_for("catalogos"))

    filas = []
    filas_vacias = 0

    for fila in lector:
        if not fila:
            continue

        fila_normalizada = {}
        for clave, valor in fila.items():
            clave_limpia = clave.strip().lower() if clave else ""
            valor_limpio = valor.strip() if valor else ""
            fila_normalizada[clave_limpia] = valor_limpio

        evento = fila_normalizada.get("evento", "").strip()
        disciplina = fila_normalizada.get("disciplina", "").strip()

        if not evento and not disciplina:
            filas_vacias += 1
            continue

        if not evento or not disciplina:
            filas.append({
                "evento": evento,
                "disciplina": disciplina,
                "valida": False,
                "motivo": "incompleta"
            })
            continue

        filas.append({
            "evento": evento,
            "disciplina": disciplina,
            "valida": True
        })

    if not filas:
        flash("El CSV no contiene relaciones válidas para procesar.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    insertadas = 0
    duplicadas = 0
    inexistentes = 0
    incompletas = 0

    for fila in filas:
        if not fila.get("valida"):
            incompletas += 1
            continue

        evento = fila["evento"]
        disciplina = fila["disciplina"]

        existe_evento = conn.execute("""
            SELECT id
            FROM catalog_events
            WHERE lower(name) = lower(?)
        """, (evento,)).fetchone()

        existe_disciplina = conn.execute("""
            SELECT id
            FROM catalog_disciplines
            WHERE lower(name) = lower(?)
        """, (disciplina,)).fetchone()

        if not existe_evento or not existe_disciplina:
            inexistentes += 1
            continue

        nombre_evento_real = existe_evento["id"]
        nombre_disciplina_real = existe_disciplina["id"]

        evento_real = conn.execute("""
            SELECT name
            FROM catalog_events
            WHERE id = ?
        """, (nombre_evento_real,)).fetchone()["name"]

        disciplina_real = conn.execute("""
            SELECT name
            FROM catalog_disciplines
            WHERE id = ?
        """, (nombre_disciplina_real,)).fetchone()["name"]

        existe_relacion = conn.execute("""
            SELECT id
            FROM catalog_event_disciplines
            WHERE lower(evento) = lower(?) AND lower(disciplina) = lower(?)
        """, (evento_real, disciplina_real)).fetchone()

        if existe_relacion:
            duplicadas += 1
            continue

        conn.execute("""
            INSERT INTO catalog_event_disciplines (evento, disciplina)
            VALUES (?, ?)
        """, (evento_real, disciplina_real))

        insertadas += 1

    conn.commit()
    conn.close()

    flash(
        f"Importación Evento → Disciplina: {insertadas} nuevas, "
        f"{duplicadas} duplicadas, "
        f"{inexistentes} con catálogos inexistentes, "
        f"{incompletas} incompletas."
    )
    return redirect(url_for("catalogos"))

@app.route("/catalogos/relacion/evento-disciplina/agregar", methods=["POST"])
def agregar_relacion_evento_disciplina():
    evento = request.form.get("evento", "").strip()
    disciplina = request.form.get("disciplina", "").strip()

    if not evento or not disciplina:
        flash("Tenés que seleccionar evento y disciplina.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    existe = conn.execute("""
        SELECT id
        FROM catalog_event_disciplines
        WHERE evento = ? AND disciplina = ?
    """, (evento, disciplina)).fetchone()

    if existe:
        conn.close()
        flash("Esa relación ya existe.")
        return redirect(url_for("catalogos"))

    conn.execute("""
        INSERT INTO catalog_event_disciplines (evento, disciplina)
        VALUES (?, ?)
    """, (evento, disciplina))

    conn.commit()
    conn.close()

    flash("Relación agregada correctamente.")
    return redirect(url_for("catalogos"))


@app.route("/catalogos/relacion/evento-disciplina/eliminar/<int:id>", methods=["POST"])
def eliminar_relacion_evento_disciplina(id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM catalog_event_disciplines
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Relación eliminada.")
    return redirect(url_for("catalogos"))

@app.route("/catalogos/relacion/disciplina-prueba-genero/agregar", methods=["POST"])
def agregar_relacion_disciplina_prueba_genero():
    disciplina = request.form.get("disciplina", "").strip()
    prueba = request.form.get("prueba", "").strip()
    genero = request.form.get("genero", "").strip()

    if not disciplina or not prueba or not genero:
        flash("Tenés que completar disciplina, prueba y género para agregar la relación.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    existe_disciplina = conn.execute("""
        SELECT id, name
        FROM catalog_disciplines
        WHERE lower(name) = lower(?)
    """, (disciplina,)).fetchone()

    existe_prueba = conn.execute("""
        SELECT id, name
        FROM catalog_tests
        WHERE lower(name) = lower(?)
    """, (prueba,)).fetchone()

    existe_genero = conn.execute("""
        SELECT id, name
        FROM catalog_genders
        WHERE lower(name) = lower(?)
    """, (genero,)).fetchone()

    if not existe_disciplina or not existe_prueba or not existe_genero:
        conn.close()
        flash("La disciplina, la prueba o el género no existen en los catálogos.")
        return redirect(url_for("catalogos"))

    disciplina_real = existe_disciplina["name"]
    prueba_real = existe_prueba["name"]
    genero_real = existe_genero["name"]

    existe_relacion = conn.execute("""
        SELECT id
        FROM catalog_discipline_test_genders
        WHERE lower(disciplina) = lower(?)
          AND lower(prueba) = lower(?)
          AND lower(genero) = lower(?)
    """, (disciplina_real, prueba_real, genero_real)).fetchone()

    if existe_relacion:
        conn.close()
        flash("Esa relación Disciplina → Prueba → Género ya existe.")
        return redirect(url_for("catalogos"))

    conn.execute("""
        INSERT INTO catalog_discipline_test_genders (disciplina, prueba, genero)
        VALUES (?, ?, ?)
    """, (disciplina_real, prueba_real, genero_real))

    conn.commit()
    conn.close()

    flash("Relación Disciplina → Prueba → Género agregada correctamente.")
    return redirect(url_for("catalogos"))

@app.route("/catalogos/relacion/disciplina-prueba-genero/eliminar/<int:item_id>", methods=["POST"])
def eliminar_relacion_disciplina_prueba_genero(item_id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM catalog_discipline_test_genders
        WHERE id = ?
    """, (item_id,))

    conn.commit()
    conn.close()

    flash("Relación Disciplina → Prueba → Género eliminada correctamente.")
    return redirect(url_for("catalogos"))

@app.route("/catalogos/relacion/disciplina-prueba/importar_csv", methods=["POST"])
def importar_relacion_disciplina_prueba_csv():
    archivo = request.files.get("archivo_csv_relacion_disciplina_prueba")

    if not archivo or archivo.filename.strip() == "":
        flash("Tenés que seleccionar un archivo CSV de relaciones Disciplina → Prueba.")
        return redirect(url_for("catalogos"))

    if not archivo.filename.lower().endswith(".csv"):
        flash("El archivo tiene que ser un CSV.")
        return redirect(url_for("catalogos"))

    try:
        data = archivo.stream.read()

        contenido = None

        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                contenido = data.decode(encoding)
                break
            except:
                continue

        if contenido is None:
            flash("No se pudo leer el CSV de relaciones Disciplina → Prueba.")
            return redirect(url_for("catalogos"))

    except:
        flash("Error al leer el archivo CSV de relaciones Disciplina → Prueba.")
        return redirect(url_for("catalogos"))

    muestra_csv = contenido[:2048]

    try:
        dialecto = csv.Sniffer().sniff(muestra_csv, delimiters=",;")
        delimitador = dialecto.delimiter
    except:
        delimitador = ";"

    lector = csv.DictReader(io.StringIO(contenido), delimiter=delimitador)

    if not lector.fieldnames:
        flash("El CSV está vacío o mal formado.")
        return redirect(url_for("catalogos"))

    encabezados = [h.strip().lower() for h in lector.fieldnames if h]

    if "disciplina" not in encabezados or "prueba" not in encabezados:
        flash("El CSV debe tener exactamente las columnas 'disciplina' y 'prueba'.")
        return redirect(url_for("catalogos"))

    filas = []

    for fila in lector:
        if not fila:
            continue

        fila_normalizada = {}
        for clave, valor in fila.items():
            clave_limpia = clave.strip().lower() if clave else ""
            valor_limpio = valor.strip() if valor else ""
            fila_normalizada[clave_limpia] = valor_limpio

        disciplina = fila_normalizada.get("disciplina", "").strip()
        prueba = fila_normalizada.get("prueba", "").strip()

        if not disciplina and not prueba:
            continue

        if not disciplina or not prueba:
            filas.append({
                "disciplina": disciplina,
                "prueba": prueba,
                "valida": False
            })
            continue

        filas.append({
            "disciplina": disciplina,
            "prueba": prueba,
            "valida": True
        })

    if not filas:
        flash("El CSV no contiene relaciones válidas para procesar.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    insertadas = 0
    duplicadas = 0
    inexistentes = 0
    incompletas = 0

    for fila in filas:
        if not fila.get("valida"):
            incompletas += 1
            continue

        disciplina = fila["disciplina"]
        prueba = fila["prueba"]

        existe_disciplina = conn.execute("""
            SELECT id, name
            FROM catalog_disciplines
            WHERE lower(name) = lower(?)
        """, (disciplina,)).fetchone()

        existe_prueba = conn.execute("""
            SELECT id, name
            FROM catalog_tests
            WHERE lower(name) = lower(?)
        """, (prueba,)).fetchone()

        if not existe_disciplina or not existe_prueba:
            inexistentes += 1
            continue

        disciplina_real = existe_disciplina["name"]
        prueba_real = existe_prueba["name"]

        existe_relacion = conn.execute("""
            SELECT id
            FROM catalog_discipline_tests
            WHERE lower(disciplina) = lower(?) AND lower(prueba) = lower(?)
        """, (disciplina_real, prueba_real)).fetchone()

        if existe_relacion:
            duplicadas += 1
            continue

        conn.execute("""
            INSERT INTO catalog_discipline_tests (disciplina, prueba)
            VALUES (?, ?)
        """, (disciplina_real, prueba_real))

        insertadas += 1

    conn.commit()
    conn.close()

    flash(
        f"Importación Disciplina → Prueba: {insertadas} nuevas, "
        f"{duplicadas} duplicadas, "
        f"{inexistentes} con catálogos inexistentes, "
        f"{incompletas} incompletas."
    )
    return redirect(url_for("catalogos"))

@app.route("/catalogos/relacion/disciplina-prueba/agregar", methods=["POST"])
def agregar_relacion_disciplina_prueba():
    disciplina = request.form.get("disciplina", "").strip()
    prueba = request.form.get("prueba", "").strip()

    if not disciplina or not prueba:
        flash("Tenés que seleccionar disciplina y prueba.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    existe = conn.execute("""
        SELECT id
        FROM catalog_discipline_tests
        WHERE disciplina = ? AND prueba = ?
    """, (disciplina, prueba)).fetchone()

    if existe:
        conn.close()
        flash("Esa relación ya existe.")
        return redirect(url_for("catalogos"))

    conn.execute("""
        INSERT INTO catalog_discipline_tests (disciplina, prueba)
        VALUES (?, ?)
    """, (disciplina, prueba))

    conn.commit()
    conn.close()

    flash("Relación agregada correctamente.")
    return redirect(url_for("catalogos"))


@app.route("/catalogos/relacion/disciplina-prueba/eliminar/<int:id>", methods=["POST"])
def eliminar_relacion_disciplina_prueba(id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM catalog_discipline_tests
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Relación eliminada.")
    return redirect(url_for("catalogos"))
@app.route("/catalogos/eliminar_seleccionados/<tipo_catalogo>", methods=["POST"])
def eliminar_catalogo_seleccionados(tipo_catalogo):
    tablas = {
        "eventos": "catalog_events",
        "disciplinas": "catalog_disciplines",
        "generos": "catalog_genders",
        "pruebas": "catalog_tests",
        "categorias": "catalog_categories",
        "clases": "catalog_classes",
        "provincias": "catalog_provinces"
    }

    campos_medals = {
        "eventos": "evento",
        "disciplinas": "disciplina",
        "generos": "genero",
        "pruebas": "prueba",
        "categorias": "categoria",
        "clases": "clase",
        "provincias": "provincia"
    }

    if tipo_catalogo not in tablas:
        flash("Catálogo inválido.")
        return redirect(url_for("catalogos"))

    ids = request.form.getlist("ids")

    if not ids:
        flash("No seleccionaste ningún elemento.")
        return redirect(url_for("catalogos"))

    tabla = tablas[tipo_catalogo]
    campo = campos_medals[tipo_catalogo]

    conn = get_connection()

    eliminados = 0
    omitidos = 0

    for item_id in ids:
        item = conn.execute(
            f"SELECT name FROM {tabla} WHERE id = ?",
            (item_id,)
        ).fetchone()

        if not item:
            continue

        nombre = item["name"]

        uso = conn.execute(
            f"SELECT id FROM medals WHERE {campo} = ? LIMIT 1",
            (nombre,)
        ).fetchone()

        if uso:
            omitidos += 1
            continue

        if tipo_catalogo == "eventos":
            conn.execute(
                "DELETE FROM catalog_event_disciplines WHERE evento = ?",
                (nombre,)
            )
        elif tipo_catalogo == "disciplinas":
            conn.execute(
                "DELETE FROM catalog_event_disciplines WHERE disciplina = ?",
                (nombre,)
            )
            conn.execute(
                "DELETE FROM catalog_discipline_tests WHERE disciplina = ?",
                (nombre,)
            )
        elif tipo_catalogo == "pruebas":
            conn.execute(
                "DELETE FROM catalog_discipline_tests WHERE prueba = ?",
                (nombre,)
            )

        conn.execute(
            f"DELETE FROM {tabla} WHERE id = ?",
            (item_id,)
        )

        eliminados += 1

    conn.commit()
    conn.close()

    if eliminados > 0 and omitidos > 0:
        flash(f"Se eliminaron {eliminados} elemento(s). {omitidos} no se pudieron eliminar porque están en uso.")
    elif eliminados > 0:
        flash(f"Se eliminaron {eliminados} elemento(s).")
    else:
        flash("No se pudo eliminar ningún elemento porque todos están en uso.")

    return redirect(url_for("catalogos"))


@app.route("/catalogos/relacion/evento-disciplina/eliminar_seleccionadas", methods=["POST"])
def eliminar_relaciones_evento_disciplina_seleccionadas():
    ids = request.form.getlist("ids")

    if not ids:
        flash("No seleccionaste ninguna relación.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    for relacion_id in ids:
        conn.execute("""
            DELETE FROM catalog_event_disciplines
            WHERE id = ?
        """, (relacion_id,))

    conn.commit()
    conn.close()

    flash(f"Se eliminaron {len(ids)} relación(es) Evento → Disciplina.")
    return redirect(url_for("catalogos"))


@app.route("/catalogos/relacion/disciplina-prueba/eliminar_seleccionadas", methods=["POST"])
def eliminar_relaciones_disciplina_prueba_seleccionadas():
    ids = request.form.getlist("ids")

    if not ids:
        flash("No seleccionaste ninguna relación.")
        return redirect(url_for("catalogos"))

    conn = get_connection()

    for relacion_id in ids:
        conn.execute("""
            DELETE FROM catalog_discipline_tests
            WHERE id = ?
        """, (relacion_id,))

    conn.commit()
    conn.close()

    flash(f"Se eliminaron {len(ids)} relación(es) Disciplina → Prueba.")
    return redirect(url_for("catalogos"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)