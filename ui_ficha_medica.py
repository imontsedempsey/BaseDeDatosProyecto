import streamlit as st
from datetime import datetime
from datetime import date
from db import fetch_all, fetch_one, execute, expr_paciente_rut, expr_paciente_nombre
from ui_pacientes import listado_pacientes, row_get

# =======================
# Helpers de parsing
# =======================
def as_float(v, default=0.0):
    """Convierte '37.0°C', '37,2', 37 -> 37.0. Si no puede, devuelve default."""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    # Mantener solo dígitos, punto y signo
    num = "".join(ch for ch in s if (ch.isdigit() or ch in ".-"))
    try:
        return float(num) if num not in ("", ".", "-") else default
    except Exception:
        return default

def as_int(v, default=0):
    """Convierte '75 lpm', '075', 75 -> 75. Si no puede, devuelve default."""
    if v is None:
        return default
    if isinstance(v, int):
        return v
    s = str(v).strip()
    digits = "".join(ch for ch in s if ch.isdigit() or ch == "-")
    try:
        return int(digits) if digits not in ("", "-") else default
    except Exception:
        return default

def parse_pa(pa_text, default_pas=120, default_pad=80):
    """'120/80' -> (120,80). Si no puede, defaults."""
    try:
        if pa_text and isinstance(pa_text, str) and "/" in pa_text:
            a, b = pa_text.split("/", 1)
            return as_int(a, default_pas), as_int(b, default_pad)
    except Exception:
        pass
    return default_pas, default_pad


# =======================
# UI principal
# =======================
def ui_ficha_medica():
    st.header("📋 Ficha Médica / Historial Clínico")

    sub = st.tabs(["➕ Nueva ficha médica", "📚 Historial del paciente", "🧪 Solicitar Examen", "💊 Prescripción"])

    # -----------------------------------------------------------------------------------
    # TAB 0: NUEVA FICHA MÉDICA
    # -----------------------------------------------------------------------------------
    with sub[0]:
        st.subheader("Registrar nueva atención")

        pacientes = listado_pacientes()
        if not pacientes:
            st.info("No hay pacientes registrados.")
        else:
            # Selector de paciente
            opciones = {
                f"#{p['id_paciente']} • {row_get(p,'rut','Rut_Paciente','RUT')} – {row_get(p,'nombre','Nombre')}": p["id_paciente"]
                for p in pacientes
            }
            sel_nueva_key = st.selectbox(
                "Paciente",
                list(opciones.keys()),
                key="ficha_new_paciente_select"
            )
            paciente_id_sel = opciones[sel_nueva_key]

            # Fecha/hora automática (como texto para SQLite)
            ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.write("Fecha y hora de la atención (automática):")
            st.code(ahora_str)

            # ---------- Formulario ----------
            with st.form("form_nueva_ficha", clear_on_submit=True):
                motivo_consulta_in = st.text_input("Motivo de consulta (obligatorio)", max_chars=200)
                anamnesis_in = st.text_area("Anamnesis / Relato del paciente")
                observaciones_in = st.text_area("Observaciones / Examen físico / Indicaciones")

                st.markdown("**Signos vitales**")
                c1, c2, c3, c4 = st.columns(4)
                pas = c1.number_input("PAS (mmHg)", min_value=0, max_value=300, value=120, step=1)
                pad = c2.number_input("PAD (mmHg)", min_value=0, max_value=200, value=80, step=1)
                temp = c3.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, value=36.8, step=0.1, format="%.1f")
                fc   = c4.number_input("Frecuencia cardiaca (lpm)", min_value=0, max_value=230, value=75, step=1)

                peso = st.number_input("Peso (kg)", min_value=0.0, max_value=500.0, value=70.0, step=0.1, format="%.1f")

                submitted_new = st.form_submit_button("Guardar ficha médica")

            # ---------- Guardado ----------
            if submitted_new:
                if not motivo_consulta_in.strip():
                    st.error("El motivo de consulta es obligatorio.")
                else:
                    try:
                        # 1) Insertar ficha
                        execute(
                            """
                            INSERT INTO FichaMedica
                            (id_paciente, fecha_hora, motivo_consulta, Anamnesis, observaciones)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                paciente_id_sel,
                                ahora_str,
                                motivo_consulta_in.strip(),
                                (anamnesis_in.strip() if anamnesis_in else None),
                                (observaciones_in.strip() if observaciones_in else None),
                            )
                        )

                        # 2) Buscar ID recién creado (evita problemas de conexiones)
                        row = fetch_one(
                            """
                            SELECT ID_Ficha
                            FROM FichaMedica
                            WHERE id_paciente = ?
                              AND fecha_hora = ?
                              AND motivo_consulta = ?
                            ORDER BY ID_Ficha DESC
                            LIMIT 1
                            """,
                            (paciente_id_sel, ahora_str, motivo_consulta_in.strip())
                        )
                        if not row:
                            st.error("No se pudo obtener el ID de la ficha médica recién creada.")
                        else:
                            ficha_id = row["ID_Ficha"]

                            # 3) Signos vitales (esquema actual: TEXT)
                            pa_txt = f"{int(pas)}/{int(pad)}"
                            execute(
                                """
                                INSERT INTO SignosVitales
                                (ID_Ficha_Medica, presion_arterial, Temperatura, Frecuencia_cardiaca, peso)
                                VALUES (?,?,?,?,?)
                                """,
                                (ficha_id, pa_txt, f"{temp}", f"{fc}", f"{peso}")
                            )

                            st.success("Ficha médica y signos vitales registrados.")
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    # -----------------------------------------------------------------------------------
    # TAB 1: HISTORIAL (listar, editar, eliminar)
    # -----------------------------------------------------------------------------------
    with sub[1]:
        st.subheader("Historial clínico del paciente")

        pacientes2 = listado_pacientes()
        if not pacientes2:
            st.info("No hay pacientes registrados.")
        else:
            opciones2 = {
                f"#{p['id_paciente']} • {row_get(p,'rut','Rut_Paciente','RUT')} – {row_get(p,'nombre','Nombre')}": p["id_paciente"]
                for p in pacientes2
            }
            sel_hist_key = st.selectbox(
                "Selecciona un paciente para ver historial",
                list(opciones2.keys()),
                key="ficha_hist_paciente_select"
            )
            paciente_hist_id = opciones2[sel_hist_key]

            # Fichas del paciente
            fichas = fetch_all(
                """
                SELECT ID_Ficha,
                       fecha_hora,
                       motivo_consulta,
                       Anamnesis,
                       observaciones
                FROM FichaMedica
                WHERE id_paciente = ?
                ORDER BY datetime(fecha_hora) DESC
                """,
                (paciente_hist_id,)
            )

            if not fichas:
                st.info("Este paciente no tiene fichas médicas aún.")
            else:
                for f in fichas:
                    ficha_id = f["ID_Ficha"]

                    st.markdown("---")
                    st.markdown(
                        f"**Atención:** {f['fecha_hora']}  \n"
                        f"**Motivo:** {f['motivo_consulta']}"
                    )

                    anam = f["Anamnesis"] if "Anamnesis" in f.keys() else None
                    obs  = f["observaciones"] if "observaciones" in f.keys() else None
                    if anam:
                        st.markdown(f"**Anamnesis:** {anam}")
                    if obs:
                        st.markdown(f"**Observaciones:** {obs}")

                    # Signos vitales asociados
                    sv = fetch_all(
                        """
                        SELECT ID_Signos_vitales, presion_arterial, Temperatura, Frecuencia_cardiaca, peso
                        FROM SignosVitales  /* <-- CORRECCIÓN: Usando el nombre de tabla deseado */
                        WHERE ID_Ficha_Medica = ?
                        """,
                        (ficha_id,)
                    )
                    sv_row = sv[0] if sv else None

                    if sv_row:
                        # Mostrar con formateo robusto (por si hay unidades en texto)
                        t_show  = as_float(sv_row['Temperatura'], None)
                        fc_show = as_int(sv_row['Frecuencia_cardiaca'], None)
                        w_show  = as_float(sv_row['peso'], None)
                        st.markdown(
                            f"**Signos vitales:** "
                            f"PA {sv_row['presion_arterial']} mmHg • "
                            f"{('T ' + f'{t_show:.1f} °C • ') if t_show is not None else ''}"
                            f"{('FC ' + str(fc_show) + ' lpm • ') if fc_show is not None else ''}"
                            f"{('Peso ' + f'{w_show:.1f} kg') if w_show is not None else ''}"
                        )
                    else:
                        st.caption("Sin signos vitales registrados para esta ficha.")

                    # ---- Control único de eliminación ----
                    if st.button("🗑️ Eliminar Ficha completa", key=f"del_ficha_{ficha_id}"):
                        execute("DELETE FROM SignosVitales WHERE ID_Ficha_Medica = ?", (ficha_id,))
                        execute("DELETE FROM FichaMedica WHERE ID_Ficha = ?", (ficha_id,))
                        st.success(f"Ficha {ficha_id} y signos vitales eliminados.")
                        st.rerun()

                    # ---- Editor en línea (ficha + SV) ----
                    with st.expander(f"✏️ Editar ficha #{ficha_id}"):
                        with st.form(f"form_edit_ficha_{ficha_id}", clear_on_submit=True):
                            motivo_edit = st.text_input(
                                "Motivo de consulta",
                                value=f['motivo_consulta'] if 'motivo_consulta' in f.keys() else ""
                            )
                            anam_edit = st.text_area("Anamnesis", value=anam or "")
                            obs_edit  = st.text_area("Observaciones", value=obs or "")

                            st.markdown("**Signos vitales**")
                            pas0, pad0 = parse_pa(sv_row['presion_arterial']) if sv_row else (120, 80)
                            temp0 = as_float(sv_row['Temperatura'], 36.8) if sv_row else 36.8
                            fc0   = as_int(sv_row['Frecuencia_cardiaca'], 75) if sv_row else 75
                            peso0 = as_float(sv_row['peso'], 70.0) if sv_row else 70.0

                            col1, col2, col3, col4, col5 = st.columns(5)
                            pas_edit  = col1.number_input("PAS (mmHg)", min_value=0, max_value=300, value=pas0, step=1, key=f"pas_{ficha_id}")
                            pad_edit  = col2.number_input("PAD (mmHg)", min_value=0, max_value=200, value=pad0, step=1, key=f"pad_{ficha_id}")
                            temp_edit = col3.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, value=temp0, step=0.1, format="%.1f", key=f"temp_{ficha_id}")
                            fc_edit   = col4.number_input("FC (lpm)", min_value=0, max_value=230, value=fc0, step=1, key=f"fc_{ficha_id}")
                            peso_edit = col5.number_input("Peso (kg)", min_value=0.0, max_value=500.0, value=peso0, step=0.1, format="%.1f", key=f"peso_{ficha_id}")

                            submitted_edit = st.form_submit_button("💾 Guardar cambios")

                        if submitted_edit:
                            try:
                                # Actualizar Ficha
                                execute(
                                    """
                                    UPDATE FichaMedica
                                    SET motivo_consulta = ?, Anamnesis = ?, observaciones = ?
                                    WHERE ID_Ficha = ?
                                    """,
                                    (
                                        (motivo_edit.strip() or None),
                                        (anam_edit.strip() or None),
                                        (obs_edit.strip() or None),
                                        ficha_id
                                    )
                                )

                                # Upsert de Signos Vitales (esquema actual con TEXT)
                                pa_txt = f"{int(pas_edit)}/{int(pad_edit)}"
                                if sv_row:
                                    execute(
                                        """
                                        UPDATE SignosVitales
                                        SET presion_arterial = ?, Temperatura = ?, Frecuencia_cardiaca = ?, peso = ?
                                        WHERE ID_Ficha_Medica = ?
                                        """,
                                        (pa_txt, f"{temp_edit}", f"{fc_edit}", f"{peso_edit}", ficha_id)
                                    )
                                else:
                                    execute(
                                        """
                                        INSERT INTO SignosVitales
                                        (ID_Ficha_Medica, presion_arterial, Temperatura, Frecuencia_cardiaca, peso)
                                        VALUES (?,?,?,?,?)
                                        """,
                                        (ficha_id, pa_txt, f"{temp_edit}", f"{fc_edit}", f"{peso_edit}")
                                    )

                                st.success("Cambios guardados.")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error al actualizar: {e}")


    # -----------------------------------------------------------------------------------
    # TAB 2: Solicitar Examen (Sección añadida para los exámenes)
    # -----------------------------------------------------------------------------------
    with sub[2]:  # Solicitar Examen
        st.subheader("Solicitar Examen")

        # Formulario para ingresar la solicitud de examen
        with st.form("f_solicitud_examen"):
            tipo_examen = st.selectbox("Tipo de examen", [
            "Examen de sangre", 
            "Radiografía", 
            "Ultrasonido", 
            "Electrocardiograma", 
            "Prueba de función pulmonar", 
            "Prueba de esfuerzo", 
            "Otros"
        ])
            fecha_solicitud = st.date_input("Fecha de solicitud", value=date.today())
            
            # Se selecciona la Ficha Médica asociada (ID de la ficha médica)
            ficha_medica_id = st.number_input("ID Ficha Médica", min_value=1, step=1)

            estado = st.selectbox("Estado", ["Pendiente", "Realizada", "Cancelada"], index=0)
            observaciones = st.text_area("Observaciones", height=70)

            # Botón para enviar el formulario
            s = st.form_submit_button("Solicitar Examen")

        # Si el formulario es enviado correctamente
        if s and tipo_examen.strip():
            try:
                # Insertar la solicitud de examen en la base de datos
                execute(
                    """
                    INSERT INTO SolicitudExamen (ID_ficha_medica, Tipo_de_examen, fecha_solicitud, Observaciones, Estado)
                    VALUES (?,?,?,?,?)
                    """,
                    (ficha_medica_id, tipo_examen.strip(), fecha_solicitud.isoformat(), observaciones.strip(), estado)
                )
                st.success("Examen solicitado.")
                st.rerun()  # Recargar la página para reflejar los cambios
            except Exception as e:
                st.error(f"Error al solicitar examen: {e}")

        # Recuperar todas las solicitudes de examen asociadas a la Ficha Médica seleccionada
        rows = fetch_all(
            """
            SELECT id, Tipo_de_examen, fecha_solicitud, Estado 
            FROM SolicitudExamen 
            WHERE ID_ficha_medica = ? 
            ORDER BY fecha_solicitud DESC
            """,
            (ficha_medica_id,)  # ID de la ficha médica
        )

        # Mostrar los exámenes solicitados en una tabla
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True)
        else:
            st.info("No hay exámenes solicitados aún.")

        # Mostrar botones de eliminación para cada solicitud de examen
        for r in rows:
            if st.button(f"Eliminar Solicitud #{r['id']}", key=f"del_solicitud_{r['id']}"):
                try:
                    # Eliminar la solicitud de examen seleccionada
                    execute("DELETE FROM SolicitudExamen WHERE id=?", (r['id'],))
                    st.warning("Solicitud de examen eliminada.")
                    st.rerun()  # Recargar la página para reflejar los cambios
                except Exception as e:
                    st.error(f"Error al eliminar la solicitud: {e}")

# -----------------------------------------------------------------------------------
    # TAB 3: Prescripcion
    # -----------------------------------------------------------------------------------
    
    with sub[3]:
        st.subheader("Nueva prescripción")

        # Inicializamos rx_rows para evitar UnboundLocalError cuando no hay ficha/prescripción
        rx_rows = []

        # 1) Elegir paciente
        pacientes = fetch_all(f"""
            SELECT id_paciente,
                {expr_paciente_rut()}   AS rut,
                {expr_paciente_nombre()} AS nombre
            FROM Paciente
            ORDER BY COALESCE(nombre,'')
        """)
        if not pacientes:
            st.info("No hay pacientes.")
        else:
            opciones_p = {
                f"#{p['id_paciente']} • {p['rut']} – {p['nombre']}": p["id_paciente"]
                for p in pacientes
            }
            sel_p_key = st.selectbox(
                "Selecciona un paciente",
                list(opciones_p.keys()),
                key="rx_paciente_select"
            )
            paciente_rx_id = opciones_p[sel_p_key]

            # 2) Elegir ficha médica del paciente
            fichas_rx = fetch_all(
                """
                SELECT ID_Ficha, fecha_hora, motivo_consulta
                FROM FichaMedica
                WHERE ID_paciente = ?
                ORDER BY datetime(fecha_hora) DESC
                """,
                (paciente_rx_id,)
            )

            if not fichas_rx:
                st.info("Este paciente no tiene fichas médicas aún.")
            else:
                opciones_f = {
                    f"Ficha #{f['ID_Ficha']} • {f['fecha_hora']} – {f['motivo_consulta'] or ''}": f["ID_Ficha"]
                    for f in fichas_rx
                }
                sel_f_key = st.selectbox(
                    "Selecciona la ficha sobre la que se hará la prescripción",
                    list(opciones_f.keys()),
                    key="rx_ficha_select"
                )
                fid = opciones_f[sel_f_key]

                st.markdown("---")
                st.subheader("Registrar nueva prescripción")

                with st.form("form_prescripcion", clear_on_submit=True):
                    medicamento = st.text_input("Medicamento", max_chars=200)
                    dosis = st.text_input("Dosis", placeholder="Ej: 500 mg")
                    frecuencia = st.text_input("Frecuencia", placeholder="Ej: cada 8 horas")
                    duracion = st.text_input("Duración", placeholder="Ej: 7 días")

                    via = st.selectbox(
                        "Vía de administración",
                        ["Oral", "Intravenosa", "Intramuscular", "Subcutánea", "Tópica", "Otra"],
                        index=0
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        fecha_em = st.date_input("Fecha de emisión")
                    with col2:
                        estado = st.selectbox("Estado", ["Pendiente", "Dispensada", "Cancelada"], index=0)

                    observ = st.text_area("Observaciones", placeholder="Instrucciones adicionales…", height=80)

                    ok = st.form_submit_button("Guardar prescripción")

                if ok:
                    try:
                        execute(
                            """
                            INSERT INTO Prescripcion
                                (ID_Ficha_Medica, Medicamento, Dosis, Frecuencia, Duracion,
                                 Via_administracion, Fecha_emision, Observaciones, Estado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                fid,
                                (medicamento or "").strip() or None,
                                (dosis or "").strip() or None,
                                (frecuencia or "").strip() or None,
                                (duracion or "").strip() or None,
                                (via or "").strip() or None,
                                fecha_em.isoformat() if fecha_em else None,
                                (observ or "").strip() or None,
                                (estado or "").strip() or None,
                            )
                        )
                        st.success("Prescripción guardada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

                # -------- Listado de prescripciones de esta ficha --------
                st.markdown("---")
                st.subheader("Prescripciones de esta ficha")

                rx_rows = fetch_all(
                    """
                    SELECT ID_Prescripcion, Medicamento, Dosis, Frecuencia, Duracion,
                           Via_administracion, Fecha_emision, Observaciones, Estado
                    FROM Prescripcion
                    WHERE ID_Ficha_Medica=?
                    ORDER BY ID_Prescripcion DESC
                    """,
                    (fid,)
                )

                if rx_rows:
                    st.dataframe([dict(r) for r in rx_rows], use_container_width=True)
                else:
                    st.info("Sin prescripciones registradas para esta ficha.")

        # --- ELIMINAR PRESCRIPCIÓN ---
        st.markdown("### 🗑️ Eliminar Prescripción")

        # Verificamos si hay registros (y si rx_rows existe)
        if rx_rows:
            # Creamos un selector con formato legible
            opciones_rx = {
                f"#{r['ID_Prescripcion']} • {r['Medicamento']} ({r['Dosis'] or ''}) – {r['Estado'] or ''}": r["ID_Prescripcion"]
                for r in rx_rows
            }

            sel_rx = st.selectbox(
                "Selecciona una prescripción para eliminar",
                list(opciones_rx.keys()),
                key="sel_rx_del"
            )
            id_del = opciones_rx[sel_rx]

            if st.button("Eliminar Prescripción", type="primary"):
                try:
                    execute("DELETE FROM Prescripcion WHERE ID_Prescripcion=?", (id_del,))
                    st.success("✅ Prescripción eliminada correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar prescripción: {e}")
        else:
            st.info("No hay prescripciones registradas para eliminar.")