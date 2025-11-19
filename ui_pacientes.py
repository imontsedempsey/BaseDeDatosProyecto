import streamlit as st
from db import fetch_all, execute, expr_paciente_rut, expr_paciente_nombre, row_get, paciente_columns, has_column, fetch_one
from datetime import date, time
from Validaciones import validar_rut, validar_correo
import sqlite3
from db import has_column 
# -------------------------------------------------------------
# Límites y default de fecha de nacimiento
# -------------------------------------------------------------
DOB_MIN = date(1920, 1, 1)
DOB_MAX = date.today()
DOB_DEFAULT = date(2000, 1, 1)  # <-- El calendario abrirá en esta fecha

# -------------------------------------------------------------
# Listado de pacientes
# -------------------------------------------------------------
def listado_pacientes():
    """
    Devuelve lista de pacientes en el formato:
    [
        {
            "id_paciente": ...,
            "rut": ...,
            "nombre": "Nombre Apellido" (si hay apellido) o "Nombre" (si no)
        },
        ...
    ]
    """

    # Tenemos que construir el SELECT según qué columnas existan realmente
    cols_select = [
        "id_paciente",
        "rut AS rut" if has_column("Paciente", "rut") else "Rut_Paciente AS rut",
        "nombre AS nombre" if has_column("Paciente", "nombre") else "Nombre AS nombre",
    ]

    # Si existe columna Apellido (o "apellido"), la agregamos
    if has_column("Paciente", "apellido"):
        cols_select.append("apellido AS apellido")
        apellido_colname = "apellido"
    elif has_column("Paciente", "Apellido"):
        cols_select.append("Apellido AS apellido")
        apellido_colname = "Apellido"
    else:
        apellido_colname = None  # no hay columna apellido en la BD

    query = f"""
        SELECT {', '.join(cols_select)}
        FROM Paciente
        ORDER BY nombre
    """

    rows = fetch_all(query, ())

    pacientes_list = []
    for r in rows:
        nombre_base = r["nombre"] or ""
        if apellido_colname and "apellido" in r.keys() and r["apellido"]:
            nombre_full = (nombre_base + " " + r["apellido"]).strip()
        else:
            nombre_full = nombre_base.strip()

        pacientes_list.append({
            "id_paciente": r["id_paciente"],
            "rut": r["rut"],
            "nombre": nombre_full
        })

    return pacientes_list

# -------------------------------------------------------------
# UI: Pacientes
# -------------------------------------------------------------
def ui_pacientes():
    st.header("Pacientes")
    tabs = st.tabs(["Crear", "Editar", "Eliminar", "Listar", "Antecedentes"])

    # ---- mapeo columnas
    pac_cols = paciente_columns()
    # PARCHE EN CALIENTE: si el mapeo no trae 'prevision' pero la columna existe, la añadimos
    if not pac_cols.get("prevision") and has_column("Paciente", "prevision"):
        pac_cols["prevision"] = "prevision"

    # =======================
    # -------- Crear --------
    # =======================
    with tabs[0]:
        with st.form("form_crear_paciente", clear_on_submit=True):
            rut = st.text_input("RUT", key="create_rut")
            if rut and not validar_rut(rut):
                st.error("El RUT ingresado no es válido.")

            nombre_full = st.text_input("Nombre completo", key="create_nombre")
            fecha_nac = st.date_input(
                "Fecha de nacimiento",
                value=DOB_DEFAULT, min_value=DOB_MIN, max_value=DOB_MAX,
                key="create_fecha"
            )

            col_user, col_domain = st.columns([3,2])
            with col_user:
                correo_user = st.text_input("Correo", key="create_correo", placeholder="nombre.apellido")
            with col_domain:
                st.text_input(" ", value="@gmail.com", disabled=True)

            correo = (correo_user.strip() + "@gmail.com") if correo_user else ""
            if correo and not validar_correo(correo):
                st.error("El correo ingresado no tiene un formato válido.")

            telefono  = st.text_input("Teléfono", key="create_telefono")
            direccion = st.text_input("Dirección", key="create_direccion")

            nacionalidad = st.selectbox(
                "Nacionalidad",
                [
                    "Argentina","Bolivia","Brasil","Chile","Colombia","Costa Rica","Cuba","República Dominicana",
                    "Ecuador","El Salvador","Guatemala","Honduras","Haití","México","Nicaragua","Panamá","Paraguay",
                    "Perú","Puerto Rico","Uruguay","Venezuela","Belice","Guyana","Surinam","Francia",
                    "Canadá","Estados Unidos","Bermudas","Barbados","Islas Caimán","Islas Malvinas",
                    "Reino Unido","España","Francia","Alemania","Italia","Portugal","Países Bajos","Bélgica",
                    "Suiza","Austria","Suecia","Noruega","Dinamarca","Finlandia","Irlanda","Luxemburgo"
                ],
                key="create_nacionalidad"
            )

            sexo          = st.selectbox("Sexo/Género", ["", "Femenino", "Masculino", "Otro"], index=0, key="create_sexo")
            estado_civil  = st.selectbox("Estado civil", ["", "Soltero", "Casado", "Divorciado", "Viudo", "Conviviente"], index=0, key="create_ec")
            tipo_paciente = st.selectbox("Tipo de paciente", ["Ambulatorio", "Urgencias", "Hospitalizado"], index=0, key="create_tp")
            tipo_sangre   = st.selectbox("Tipo de sangre", ["", "O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"], index=0, key="create_ts")
            prevision = st.selectbox("Previsión", ["", "FONASA", "ISAPRE"], index=0, key="create_prevision")
            submitted_create = st.form_submit_button("Crear paciente")

        if submitted_create:
            rut_val = (rut or "").strip()
            nombre_full_val = (nombre_full or "").strip()
            if not rut_val or not nombre_full_val:
                st.error("RUT y Nombre son obligatorios.")
            else:
                nombre_only, apellido_only = (
                    (nombre_full_val.rsplit(" ", 1) + [""])[:2]
                    if pac_cols.get("apellido") else
                    (nombre_full_val, None)
                )

                cols, vals = [], []

                def add(colkey, val):
                    real = pac_cols.get(colkey)
                    if real:
                        cols.append(real); vals.append(val)

                add("rut", rut_val or None)
                add("nombre", nombre_only or None)
                add("fecha_nacimiento", fecha_nac.isoformat() if isinstance(fecha_nac, date) else None)
                add("correo", (correo or "").strip() or None)
                add("telefono", (telefono or "").strip() or None)
                add("direccion", (direccion or "").strip() or None)
                add("nacionalidad", (nacionalidad or "").strip() or None)
                add("sexo", (sexo or "").strip() or None)
                add("estado_civil", (estado_civil or "").strip() or None)
                add("tipo_paciente", (tipo_paciente or "").strip() or None)
                add("tipo_sangre", (tipo_sangre or "").strip() or None)
                add("prevision", (prevision or "").strip() or None)   

                if pac_cols.get("apellido"):
                    cols.append(pac_cols["apellido"]); vals.append((apellido_only or "").strip() or None)

                if not cols:
                    st.error("La tabla Paciente no tiene columnas compatibles para insertar.")
                else:
                    placeholders = ", ".join(["?" for _ in cols])
                    sql_ins = f"INSERT INTO Paciente ({', '.join(cols)}) VALUES ({placeholders})"
                    try:
                        execute(sql_ins, tuple(vals))
                        st.success("Paciente creado correctamente.")
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"Error al crear paciente: {e}")
                    except Exception as e:
                        st.error(f"Ocurrió un error al crear paciente: {e}")

    # =======================
    # -------- Editar -------
    # =======================
    with tabs[1]:
        pacientes = listado_pacientes()
        if not pacientes:
            st.info("No hay pacientes para editar.")
        else:
            opciones = {
                f"#{p['id_paciente']} • {p['rut']} – {p['nombre']}": p["id_paciente"]
                for p in pacientes
            }
            sel_key = st.selectbox("Selecciona un paciente", list(opciones.keys()))
            pid = opciones[sel_key]

            # refrescamos mapeo y re-parcheamos por si acaso
            pac_cols = paciente_columns()
            if not pac_cols.get("prevision") and has_column("Paciente", "prevision"):
                pac_cols["prevision"] = "prevision"

            cols_select = ["id_paciente"]
            for k, realcol in pac_cols.items():
                if realcol:
                    cols_select.append(f"{realcol} AS {k}")

            row_full = fetch_one(
                f"SELECT {', '.join(cols_select)} FROM Paciente WHERE id_paciente=?",
                (pid,)
            )

            rut_original = row_get(row_full, pac_cols.get("rut")) or ""

            with st.form("form_editar_paciente"):
                rut_edit = st.text_input("RUT", value=rut_original)
                nombre_edit = st.text_input(
                    "Nombre completo",
                    value=(
                        row_get(row_full, pac_cols.get("nombre")) if not pac_cols.get("apellido")
                        else (
                            (row_get(row_full, pac_cols.get("nombre")) or "") + " " +
                            (row_get(row_full, pac_cols.get("apellido")) or "")
                        ).strip()
                    )
                )

                fecha_edit_val_raw = row_get(row_full, pac_cols.get("fecha_nacimiento"))
                try:
                    año, mes, dia = map(int, (fecha_edit_val_raw or "2000-01-01").split("-"))
                    fecha_edit_val = date(año, mes, dia)
                except Exception:
                    fecha_edit_val = DOB_DEFAULT

                fecha_edit = st.date_input("Fecha de nacimiento", value=fecha_edit_val, min_value=DOB_MIN, max_value=DOB_MAX)

                correo_actual = row_get(row_full, pac_cols.get("correo")) or ""
                parte_user = correo_actual.replace("@gmail.com", "") if correo_actual.endswith("@gmail.com") else correo_actual

                col_user_e, col_domain_e = st.columns([3, 2])
                with col_user_e:
                    correo_user_edit = st.text_input("Correo", value=parte_user or "")
                with col_domain_e:
                    st.text_input(" ", value="@gmail.com", disabled=True)
                correo_edit = (correo_user_edit.strip() + "@gmail.com") if correo_user_edit else ""

                telefono_edit      = st.text_input("Teléfono", value=row_get(row_full, pac_cols.get("telefono")) or "")
                direccion_edit     = st.text_input("Dirección", value=row_get(row_full, pac_cols.get("direccion")) or "")
                nacionalidad_edit  = st.text_input("Nacionalidad", value=row_get(row_full, pac_cols.get("nacionalidad")) or "")
                sexo_edit          = st.text_input("Sexo/Género", value=row_get(row_full, pac_cols.get("sexo")) or "")
                estado_civil_edit  = st.text_input("Estado civil", value=row_get(row_full, pac_cols.get("estado_civil")) or "")
                tipo_paciente_edit = st.text_input("Tipo de paciente", value=row_get(row_full, pac_cols.get("tipo_paciente")) or "")
                tipo_sangre_edit   = st.text_input("Tipo de sangre", value=row_get(row_full, pac_cols.get("tipo_sangre")) or "")
                prevision_actual = row_get(row_full, pac_cols.get("prevision")) or ""
                opciones_prev = ["", "Fonasa", "Isapre"]
                try:
                    idx_prev = opciones_prev.index(prevision_actual) if prevision_actual in opciones_prev else 0
                except ValueError:
                    idx_prev = 0
                prevision_edit = st.selectbox("Previsión", opciones_prev, index=idx_prev)
                submitted_edit = st.form_submit_button("Guardar cambios")

            def clean_optional(v):
                if v is None:
                    return None
                v2 = v.strip()
                return v2 if v2 != "" else None

            if submitted_edit:
                errores = []
                if not (rut_edit or "").strip() or not (nombre_edit or "").strip():
                    errores.append("RUT y Nombre son obligatorios.")

                if rut_edit is not None and rut_original is not None:
                    cambio_rut = rut_edit.strip() != rut_original.strip()
                else:
                    cambio_rut = True

                if cambio_rut and not validar_rut(rut_edit or ""):
                    errores.append("El RUT ingresado no es válido.")

                if correo_edit and not validar_correo(correo_edit):
                    errores.append("El correo ingresado no tiene un formato válido.")

                if errores:
                    st.error(errores[0])
                else:
                    sets, vals = [], []

                    def add_set(colkey, newval):
                        real = pac_cols.get(colkey)
                        if real:
                            sets.append(f"{real}=?")
                            vals.append(newval)

                    if pac_cols.get("apellido"):
                        partes = (nombre_edit or "").strip().rsplit(" ", 1)
                        nombre_solo = partes[0]
                        apellido_solo = partes[1] if len(partes) > 1 else ""
                        add_set("nombre", nombre_solo)
                        add_set("apellido", apellido_solo)
                    else:
                        add_set("nombre", (nombre_edit or "").strip())

                    add_set("rut", (rut_edit or "").strip())
                    add_set("fecha_nacimiento", fecha_edit.isoformat())
                    add_set("correo", clean_optional(correo_edit))
                    add_set("telefono", clean_optional(telefono_edit))
                    add_set("direccion", clean_optional(direccion_edit))
                    add_set("nacionalidad", clean_optional(nacionalidad_edit))
                    add_set("sexo", clean_optional(sexo_edit))
                    add_set("estado_civil", clean_optional(estado_civil_edit))
                    add_set("tipo_paciente", clean_optional(tipo_paciente_edit))
                    add_set("tipo_sangre", clean_optional(tipo_sangre_edit))
                    add_set("prevision", clean_optional(prevision_edit))  
                    if sets:
                        vals.append(pid)  
                        sql_upd = f"UPDATE Paciente SET {', '.join(sets)} WHERE id_paciente=?"
                        try:
                            execute(sql_upd, tuple(vals))
                            st.success("Paciente actualizado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar paciente: {e}")
                    else:
                        st.error("No hay columnas editables en la tabla Paciente.")

    # =======================
    # ------- Eliminar ------
    # =======================
    with tabs[2]:
        pacientes = listado_pacientes()
        if not pacientes:
            st.info("No hay pacientes.")
        else:
            opciones = {f"#{p['id_paciente']} • {p['rut']} – {p['nombre']}": p for p in pacientes}
            sel_key = st.selectbox("Selecciona un paciente a eliminar", list(opciones.keys()))
            sel = opciones[sel_key]
            if st.button("Eliminar paciente", type="primary"):
                try:
                    execute("DELETE FROM Paciente WHERE id_paciente=?", (sel["id_paciente"],))
                    st.success("Paciente eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocurrió un error al eliminar: {e}")

    # =======================
    # -------- Listar -------
    # =======================
    with tabs[3]:
        rut_expr = expr_paciente_rut() + " AS rut"
        nom_expr = expr_paciente_nombre() + " AS nombre"
        # reusar o refrescar mapeo y parchear por si acaso
        pac_cols = paciente_columns()
        if not pac_cols.get("prevision") and has_column("Paciente", "prevision"):
            pac_cols["prevision"] = "prevision"

        f_expr  = (pac_cols["fecha_nacimiento"] or "NULL") + " AS fecha_nacimiento" if pac_cols["fecha_nacimiento"] else "NULL AS fecha_nacimiento"
        c_expr  = (pac_cols["correo"] or "NULL") + " AS correo" if pac_cols["correo"] else "NULL AS correo"
        t_expr  = (pac_cols["telefono"] or "NULL") + " AS telefono" if pac_cols["telefono"] else "NULL AS telefono"
        d_expr  = (pac_cols["direccion"] or "NULL") + " AS direccion" if pac_cols["direccion"] else "NULL AS direccion"
        nac_expr  = "nacionalidad AS nacionalidad" if has_column("Paciente","nacionalidad") else "NULL AS nacionalidad"
        sexo_expr = "sexo AS sexo"                 if has_column("Paciente","sexo")          else "NULL AS sexo"
        ec_expr   = "estado_civil AS estado_civil" if has_column("Paciente","estado_civil")  else "NULL AS estado_civil"
        tp_expr   = "tipo_paciente AS tipo_paciente" if has_column("Paciente","tipo_paciente") else "NULL AS tipo_paciente"
        ts_expr   = "tipo_sangre AS tipo_sangre"   if has_column("Paciente","tipo_sangre")   else "NULL AS tipo_sangre"
        prev_expr = "prevision AS prevision"       if has_column("Paciente","prevision")     else "NULL AS prevision"

        rows = fetch_all(f"""
            SELECT id_paciente,
                   {rut_expr},
                   {nom_expr},
                   {f_expr},
                   {c_expr},
                   {t_expr},
                   {d_expr},
                   {nac_expr},
                   {sexo_expr},
                   {ec_expr},
                   {tp_expr},
                   {ts_expr},
                   {prev_expr}
            FROM Paciente
            ORDER BY COALESCE(nombre, '')
        """)
        st.dataframe([dict(r) for r in rows], use_container_width=True)
        
    #-------------------------------
    # -------- Antecedentes --------
    #-------------------------------
    with tabs[4]:
        pacientes = fetch_all("""
            SELECT id_paciente, {rut} AS rut, {nom} AS nombre
            FROM Paciente
            ORDER BY COALESCE({nom}, '')
        """.format(rut=expr_paciente_rut(), nom=expr_paciente_nombre()))
        if not pacientes:
            st.info("No hay pacientes para gestionar antecedentes.")
            return
        opciones = {f"#{p['id_paciente']} • {row_get(p,'rut','RUT')} – {row_get(p,'nombre','Nombre')}": p["id_paciente"] for p in pacientes}
        pk = st.selectbox("Paciente", list(opciones.keys()))
        pid = opciones[pk]

        sub = st.tabs([
            "Enfermedades crónicas", "Cirugías previas", "Alergias",
            "Medicamentos actuales", "Hábitos", "Tratamientos previos",
            "Resultado Examen"
        ])

        # --- Enfermedades crónicas ---
        with sub[0]:
            with st.form("f_enfcr", clear_on_submit=True):
                nombre = st.text_input("Enfermedad crónica")
                obs    = st.text_area("Observación", height=70)
                trat   = st.text_area("Tratamiento actual", height=70)
                anio   = st.number_input(
                    "Año diagnóstico",
                    min_value=1900,
                    max_value=date.today().year,
                    value=date.today().year,
                    step=1
                )
                s = st.form_submit_button("Agregar")

            if s and nombre.strip():
                execute(
                    'INSERT INTO EnfermedadCronica (id_paciente, nombre_enfermedad, observacion, '
                    'tratamiento_actual, "Año_diagnostico") VALUES (?,?,?,?,?)',
                    (pid, nombre.strip(), obs.strip() or None, trat.strip() or None, str(anio))
                )
                st.success("Agregado.")
                st.rerun()

            # Obtener enfermedades crónicas para el paciente
            rows = fetch_all(
                'SELECT id_enfermedades_cronicas, nombre_enfermedad, observacion, '
                'tratamiento_actual, "Año_diagnostico" '
                'FROM EnfermedadCronica WHERE id_paciente=? ORDER BY nombre_enfermedad',
                (pid,)
            )
            st.dataframe([dict(r) for r in rows], use_container_width=True)

            # Botones de eliminación
            for r in rows:
                if st.button(f"Eliminar EC #{r['id_enfermedades_cronicas']}",
                            key=f"del_ec_{r['id_enfermedades_cronicas']}"):
                    execute("DELETE FROM EnfermedadCronica WHERE id_enfermedades_cronicas=?",
                            (r["id_enfermedades_cronicas"],))
                    st.warning("Enfermedad crónica eliminada.")
                    st.rerun()


        # --- Cirugías previas ---
        with sub[1]:
            with st.form("f_cir",clear_on_submit=True):
                nombre = st.text_input("Cirugía")
                fecha = st.date_input("Fecha", value=date.today())
                obs = st.text_area("Observación", height=70)
                s = st.form_submit_button("Agregar")
            if s and nombre.strip():
                execute("INSERT INTO CirugiaPrevia (id_paciente, nombre, fecha, observacion) VALUES (?,?,?,?)",
                        (pid, nombre.strip(), fecha.isoformat(), obs.strip() or None))
                st.success("Agregado.")
                st.rerun()
            rows = fetch_all("SELECT id, nombre, fecha, observacion FROM CirugiaPrevia WHERE id_paciente=? ORDER BY fecha DESC", (pid,))
            st.dataframe([dict(r) for r in rows], use_container_width=True)
            for r in rows:
                if st.button(f"Eliminar Cir #{r['id']}", key=f"del_cir_{r['id']}"):
                    execute("DELETE FROM CirugiaPrevia WHERE id=?", (r["id"],))
                    st.rerun()

        # --- Alergias ---
        with sub[2]:
            with st.form("f_ale",clear_on_submit=True):
                alergeno = st.text_input("Alérgeno")
                reaccion = st.text_input("Reacción", placeholder="p.ej. urticaria, anafilaxia")
                gravedad = st.selectbox("Gravedad", ["Grave", "Moderada", "Leve"])
                s = st.form_submit_button("Agregar")
            
            if s and alergeno.strip():
                execute(
                    "INSERT INTO AlergiaPaciente (id_paciente, Sustancia, reaccion, Gravedad) VALUES (?,?,?,?)",
                    (pid, alergeno.strip(), reaccion.strip() or None, gravedad)
                )
                st.success("Alergia agregada.")
                st.rerun()

            # Recuperar alergias del paciente
            rows = fetch_all(
                "SELECT id, Sustancia, reaccion, Gravedad FROM AlergiaPaciente WHERE id_paciente=? ORDER BY Sustancia",
                (pid,)
            )
            st.dataframe([dict(r) for r in rows], use_container_width=True)

            # Mostrar botones de eliminación para cada alergia
            for r in rows:
                if st.button(f"Eliminar Alergia #{r['id']}", key=f"del_al_{r['id']}"):
                    try:
                        execute("DELETE FROM AlergiaPaciente WHERE id=?", (r['id'],))
                        st.warning("Alergia eliminada.")
                        st.rerun()  # Recarga la página para reflejar los cambios
                    except Exception as e:
                        st.error(f"Error al eliminar la alergia: {e}")

        # --- Medicamentos actuales ---
        with sub[3]:
            with st.form("f_med",clear_on_submit=True):
                nombre = st.text_input("Medicamento")
                dosis = st.text_input("Dosis", placeholder="500 mg")
                frec = st.text_input("Frecuencia", placeholder="cada 8 h")
                via = st.text_input("Vía de administración", placeholder="oral, intravenosa, etc.")
                indicaciones = st.text_area("Indicaciones", height=70)
                s = st.form_submit_button("Agregar")
            if s and nombre.strip():
                execute(
                    "INSERT INTO MedicamentoActual (id_paciente, nombre_Medicamento, dosis, frecuencia, Via, Indicaciones) VALUES (?,?,?,?,?,?)",
                    (pid, nombre.strip(), dosis.strip() or None, frec.strip() or None, via.strip() or None, indicaciones.strip() or None)
                )
                st.success("Medicamento agregado.")
                st.rerun()

            # Recuperar medicamentos actuales del paciente
            rows = fetch_all(
                "SELECT id_Medicamento_Acutal, nombre_Medicamento, dosis, frecuencia, Via, Indicaciones FROM MedicamentoActual WHERE id_paciente=? ORDER BY nombre_Medicamento",
                (pid,)
            )
            st.dataframe([dict(r) for r in rows], use_container_width=True)

            # Mostrar botones de eliminación para cada medicamento
            for r in rows:
                if st.button(f"Eliminar Med #{r['id_Medicamento_Acutal']}", key=f"del_med_{r['id_Medicamento_Acutal']}"):
                    try:
                        execute("DELETE FROM MedicamentoActual WHERE id_Medicamento_Acutal=?", (r['id_Medicamento_Acutal'],))
                        st.warning("Medicamento eliminado.")
                        st.rerun()  # Recarga la página para reflejar los cambios
                    except Exception as e:
                        st.error(f"Error al eliminar el medicamento: {e}")

        # --- Hábitos ---
        with sub[4]:
            with st.form("f_hab", clear_on_submit=True):
                tipo = st.text_input("Tipo de hábito", placeholder="Tabaquismo / Alcohol / Actividad física / Dieta")
                desc = st.text_area("Descripción", height=70)
                frecuencia = st.text_input("Frecuencia", placeholder="Diaria, Semanal, etc.")
                s = st.form_submit_button("Agregar")
            if s and tipo.strip():
                execute(
                    "INSERT INTO HabitoPaciente (id_paciente, tipo, descripcion, Frecuencia) VALUES (?,?,?,?)",
                    (pid, tipo.strip(), desc.strip() or None, frecuencia.strip() or None)
                )
                st.success("Hábito agregado.")
                st.rerun()

            # Recuperar hábitos del paciente
            rows = fetch_all(
                "SELECT id_Habitos, tipo, descripcion, Frecuencia FROM HabitoPaciente WHERE id_paciente=? ORDER BY tipo",
                (pid,)
            )
            st.dataframe([dict(r) for r in rows], use_container_width=True)

            # Mostrar botones de eliminación para cada hábito
            for r in rows:
                if st.button(f"Eliminar Hábito #{r['id_Habitos']}", key=f"del_hab_{r['id_Habitos']}"):
                    try:
                        execute("DELETE FROM HabitoPaciente WHERE id_Habitos=?", (r['id_Habitos'],))
                        st.warning("Hábito eliminado.")
                        st.rerun()  # Recarga la página para reflejar los cambios
                    except Exception as e:
                        st.error(f"Error al eliminar el hábito: {e}")

        # --- Tratamientos previos ---
        with sub[5]:
            with st.form("f_trat",clear_on_submit=True):
                nombre = st.text_input("Tratamiento")
                fi = st.date_input("Inicio", value=date.today())
                ff = st.date_input("Fin", value=date.today())
                res = st.text_input("Resultado", placeholder="p.ej. mejoría, sin cambios")
                s = st.form_submit_button("Agregar")
            if s and nombre.strip():
                execute(
                    "INSERT INTO TratamientoPrevio (id_paciente, nombre, fecha_inicio, fecha_fin, resultado) VALUES (?,?,?,?,?)",
                    (pid, nombre.strip(), fi.isoformat(), ff.isoformat(), res.strip() or None)
                )
                st.success("Tratamiento agregado.")
                st.rerun()

            # Recuperar tratamientos previos del paciente
            rows = fetch_all(
                "SELECT id, nombre, fecha_inicio, fecha_fin, resultado FROM TratamientoPrevio WHERE id_paciente=? ORDER BY fecha_inicio DESC",
                (pid,)
            )
            st.dataframe([dict(r) for r in rows], use_container_width=True)

            # Mostrar botones de eliminación para cada tratamiento
            for r in rows:
                if st.button(f"Eliminar Trat #{r['id']}", key=f"del_trat_{r['id']}"):
                    try:
                        execute("DELETE FROM TratamientoPrevio WHERE id=?", (r['id'],))
                        st.warning("Tratamiento eliminado.")
                        st.rerun()  # Recarga la página para reflejar los cambios
                    except Exception as e:
                        st.error(f"Error al eliminar el tratamiento: {e}")


    # --- Resultado Examen ---
    with sub[6]:
        st.subheader("Resultado Examen")

        # Helpers
        def resolve_col(table, candidates):
            for c in candidates:
                if has_column(table, c):
                    return c
            return None

        # 0) Validaciones de esquema mínimas
        if not has_column("ResultadoExamen", "ID_SolicitudExamen"):
            st.error("La tabla 'ResultadoExamen' no tiene la columna 'ID_SolicitudExamen'.")
            st.stop()

        # --- SolicitudExamen ---
        se_table = "SolicitudExamen"
        se_pk        = resolve_col(se_table, ["id", "ID", "ID_SolicitudExamen", "id_solicitud_examen"])
        se_fecha     = resolve_col(se_table, ["fecha_solicitud", "Fecha_solicitud", "Fecha", "fecha"])
        se_tipo      = resolve_col(se_table, ["Tipo_de_examen", "tipo_de_examen", "tipo", "Tipo"])
        se_id_ficha  = resolve_col(se_table, ["ID_ficha_medica", "id_ficha_medica", "id_ficha", "ID_Ficha"])

        if not se_pk or not se_id_ficha:
            st.error(f"No se encontraron columnas en SolicitudExamen. PK:{se_pk} FK ficha:{se_id_ficha}")
            st.stop()

        # --- FichaMedica (para filtrar por paciente actual pid) ---
        fm_table = "FichaMedica"
        fm_id_paciente = resolve_col(fm_table, ["id_paciente", "ID_paciente", "Id_Paciente", "paciente_id"])
        # columna que empareja con se.ID_ficha_medica
        fm_id_ficha = resolve_col(fm_table, [se_id_ficha, "ID_ficha_medica", "id_ficha_medica", "id_ficha", "ID", "id"])

        if not fm_id_paciente or not fm_id_ficha:
            st.error(f"No se pudo identificar columnas en FichaMedica. id_paciente:{fm_id_paciente} id_ficha:{fm_id_ficha}")
            st.stop()

        # 1) Cargar solicitudes del paciente (pid)
        fecha_expr = f"se.{se_fecha}" if se_fecha else "NULL"
        tipo_expr  = f"se.{se_tipo}"  if se_tipo  else "NULL"

        solicitudes_sql = f"""
            SELECT se.{se_pk} AS ID_SolicitudExamen,
                {fecha_expr} AS Fecha_Solicitud,
                {tipo_expr}  AS NombreExamen
            FROM {se_table} se
            JOIN {fm_table} fm ON fm.{fm_id_ficha} = se.{se_id_ficha}
            WHERE fm.{fm_id_paciente} = ?
            ORDER BY COALESCE({fecha_expr}, '')
        """
        solicitudes = fetch_all(solicitudes_sql, (pid,))

        opciones_labels = [
            f'#{r["ID_SolicitudExamen"]} — {(r["NombreExamen"] or "Examen")} — {(r["Fecha_Solicitud"] or "")}'
            for r in solicitudes
        ]
        opciones_ids = [r["ID_SolicitudExamen"] for r in solicitudes]
        hay_opciones = len(opciones_ids) > 0

        # 2) Formulario de alta
        with st.form("f_resultado_examen"):
            label = st.selectbox(
                "Selecciona solicitud de examen",
                opciones_labels,
                index=0 if hay_opciones else None,
                disabled=not hay_opciones,
                placeholder="No hay solicitudes para este paciente"
            )
            resultado = st.text_area("Resultado del examen", height=120)
            fecha_resultado = st.date_input("Fecha de resultado", value=date.today())
            archivo_adjunto = st.text_input("Archivo adjunto (opcional)")
            s = st.form_submit_button("Agregar Resultado", disabled=not hay_opciones)

        # 3) Inserción y listado
        id_solicitud = None
        if hay_opciones and label in opciones_labels:
            id_solicitud = opciones_ids[opciones_labels.index(label)]

        if hay_opciones and s and resultado.strip() and id_solicitud is not None:
            execute(
                """
                INSERT INTO ResultadoExamen (ID_SolicitudExamen, Fecha_Resultado, Archivo_adjunto, Resultado_texto)
                VALUES (?, ?, ?, ?)
                """,
                (id_solicitud, fecha_resultado.isoformat(), (archivo_adjunto or "").strip() or None, resultado.strip())
            )
            st.success("Resultado agregado.")
            st.rerun()

        rows_resultados = []
        if id_solicitud is not None:
            rows_resultados = fetch_all(
                """
                SELECT ID_Resultado_Examen,
                    ID_SolicitudExamen,
                    Resultado_texto,
                    Fecha_Resultado,
                    Archivo_adjunto
                FROM ResultadoExamen
                WHERE ID_SolicitudExamen = ?
                ORDER BY COALESCE(Fecha_Resultado, '')
                """,
                (id_solicitud,)
            )
            st.dataframe([dict(r) for r in rows_resultados], use_container_width=True)

       # --- Eliminación ---
        if rows_resultados:
            st.markdown("### 🗑️ Eliminar resultado(s)")

            # Estado de confirmación (id del resultado que se está confirmando)
            confirm_key = "confirm_del_res"
            if confirm_key not in st.session_state:
                st.session_state[confirm_key] = None

            for r in rows_resultados:
                rid = r["ID_Resultado_Examen"]
                texto = (r["Resultado_texto"] or "").strip() or "(sin texto)"
                fecha = str(r["Fecha_Resultado"] or "—")
                adj   = (r["Archivo_adjunto"] or "—").strip()

                # Tarjeta visual
                with st.container():
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        st.markdown(
                            f"**#{rid}**  {texto}\n\n"
                            f"<small>📅 {fecha} &nbsp;&nbsp; 📎 {adj}</small>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        # ÚNICO botón: abre confirmación para este rid
                        if st.button("Eliminar", key=f"del_open_{rid}"):
                            st.session_state[confirm_key] = rid

                    # Si este es el seleccionado para confirmar, mostramos opciones aquí mismo
                    if st.session_state[confirm_key] == rid:
                        st.warning(f"¿Eliminar definitivamente el resultado #{rid}?")
                        cc1, cc2 = st.columns([1, 1])
                        with cc1:
                            if st.button("✅ Sí, eliminar", key=f"del_yes_{rid}"):
                                try:
                                    execute("DELETE FROM ResultadoExamen WHERE ID_Resultado_Examen=?", (rid,))
                                    st.success(f"Resultado #{rid} eliminado.")
                                    st.session_state[confirm_key] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"No se pudo eliminar: {e}")
                                    st.session_state[confirm_key] = None
                        with cc2:
                            if st.button("❌ Cancelar", key=f"del_no_{rid}"):
                                st.session_state[confirm_key] = None