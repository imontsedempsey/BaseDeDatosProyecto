import streamlit as st
from db import fetch_all, execute, expr_paciente_rut, expr_paciente_nombre, row_get, expr_medico_esp_aliased
from datetime import date, time

# -------------------------------------------------------------
# UI: Citas
# -------------------------------------------------------------
def ui_citas():
    st.header("Citas")
    tabs = st.tabs(["Crear", "Listar / Gestionar"])

    # Utilidades de listado (compatibles)
    try:
        pacientes = fetch_all(
            f"""
            SELECT id_paciente,
                   {expr_paciente_rut()} AS rut,
                   {expr_paciente_nombre()} AS nombre
            FROM Paciente
            ORDER BY COALESCE(nombre, '')
            """
        )
    except Exception as e:
        st.error(f"Error al obtener pacientes: {e}")
        pacientes = []
        
    pac_map = {f"{row_get(p,'rut','Rut_Paciente','RUT')} – {row_get(p,'nombre','Nombre')}": p["id_paciente"] for p in pacientes}

# Obtener médicos con su especialidad
    try:
        medicos = fetch_all(
            """
            SELECT M.id_medico, M.nombre, M.especialidad  -- Accedemos directamente a la columna especialidad
            FROM Medico M
            ORDER BY M.nombre
            """
        )
    except Exception as e:
        st.error(f"Error al obtener médicos: {e}")
        medicos = []

    med_map = {f"{m['nombre']} – {m['especialidad']}": m["id_medico"] for m in medicos}

    # -------- Crear --------
    with tabs[0]:
        with st.form("form_crear_cita", clear_on_submit=True):
            paciente_key = st.selectbox("Paciente", list(pac_map.keys()) if pac_map else ["(sin pacientes)"])
            medico_key = st.selectbox("Médico", list(med_map.keys()) if med_map else ["(sin médicos)"])
            f = st.date_input("Fecha", value=date.today())
            h = st.time_input("Hora", value=time(9, 0))
            estado = st.selectbox("Estado", ["Agendada", "Realizada", "Cancelada"], index=0)
            submitted = st.form_submit_button("Crear cita", disabled=not (pac_map and med_map))

        if submitted and pac_map and med_map:
            try:
                execute(
                    "INSERT INTO Cita (fecha, hora, estado, id_paciente, id_medico) VALUES (?, ?, ?, ?, ?)",
                    (f.isoformat(), h.strftime("%H:%M:%S"), estado, pac_map[paciente_key], med_map[medico_key]),
                )
                st.success("Cita creada.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear la cita: {e}")


    # -------- Listar / Gestionar --------
    with tabs[1]:
        try:
            rows = fetch_all(
                f"""
                SELECT C.id_cita, C.fecha, C.hora, C.estado, C.id_paciente, C.id_medico, 
                    P.rut AS rut_paciente, 
                    P.nombre AS nombre_paciente, 
                    M.nombre AS nombre_medico,
                    M.especialidad  -- Accedemos directamente a la columna especialidad de Medico
                FROM Cita C
                JOIN Paciente P ON P.id_paciente = C.id_paciente
                JOIN Medico M ON M.id_medico = C.id_medico
                ORDER BY C.fecha DESC, C.hora DESC
                """
            )

        except Exception as e:
            st.error(f"Error al obtener las citas: {e}")
            rows = []

        if not rows:
            st.info("No hay citas registradas.")
        else:
            for r in rows:
                col1, col2, col3, col4, col5 = st.columns([1.2, 1.6, 1.2, 1.2, 1.2])
                with col1:
                    st.markdown(f"**#{r['id_cita']}**")
                    st.caption(f"{r['fecha']} {r['hora']}")
                with col2:
                    st.markdown(f"**{r['nombre_paciente']}**\n\n`{r['rut_paciente']}`")
                with col3:
                    st.markdown(f"**{r['nombre_medico']}**\n\n_{r['especialidad']}_")
                with col4:
                    nuevo_estado = st.selectbox(
                        "Estado",
                        ["Agendada", "Realizada", "Cancelada"],
                        index=["Agendada", "Realizada", "Cancelada"].index(r["estado"]),
                        key=f"estado_{r['id_cita']}",
                    )
                with col5:
                    if st.button("Guardar", key=f"save_{r['id_cita']}"):
                        try:
                            execute("UPDATE Cita SET estado=? WHERE id_cita=?", (nuevo_estado, r["id_cita"]))
                            st.success("Estado actualizado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar el estado: {e}")
                    if st.button("Eliminar", key=f"del_{r['id_cita']}"):
                        try:
                            execute("DELETE FROM Cita WHERE id_cita=?", (r["id_cita"],))
                            st.warning("Cita eliminada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar la cita: {e}")


print(expr_medico_esp_aliased())  # Esto debería imprimir "E.especialidad AS especialidad"
