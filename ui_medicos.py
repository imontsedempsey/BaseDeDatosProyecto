import streamlit as st
from db import fetch_all, execute, medico_columns, fetch_one

# --- Crear Médico ---
def ui_medicos():
    st.header("Médicos")
    tabs = st.tabs(["Crear", "Editar", "Eliminar", "Listar"])

    med_cols = medico_columns()

    # -------- Crear --------
    with tabs[0]:
        with st.form("form_crear_medico", clear_on_submit=True):
            nombre = st.text_input("Nombre del médico")
            apellidos = st.text_input("Apellidos del médico")
            duracion_de_cita = st.text_input("Duración de cita")
            telefono = st.text_input("Teléfono")
            rut = st.text_input("RUT del médico")
            estado = st.selectbox("Estado", ["Activo", "Inactivo"])
            col_u, col_d = st.columns([3, 2])
            with col_u:
                correo_user_med = st.text_input("Correo electrónico", placeholder="dr.perez")
            with col_d:
                st.text_input(" ", value="@gmail.com", disabled=True)

            correo_electronico = (correo_user_med.strip() + "@gmail.com") if correo_user_med else ""


            # Lista de especialidades directamente en Medico
            especialidades = [
                'Cirugía General', 'Cirugía Ortopédica', 'Cirugía Cardiaca', 
                'Cirugía Plástica y Estética', 'Cirugía Neurocirúrgica', 
                'Cirugía Ginecológica', 'Cirugía Urológica', 'Cirugía Oncológica', 
                'Cirugía Oftalmológica', 'Cirugía Otorrinolaringológica', 
                'Cirugía Torácica', 'Cirugía Maxilofacial'
            ]
            especialidad = st.selectbox("Especialidad", especialidades)

            submitted = st.form_submit_button("Crear médico")

        if submitted:
            if not nombre.strip() or not apellidos.strip() or not rut.strip() or not correo_electronico.strip():
                st.error("El nombre, apellidos, RUT y correo electrónico son obligatorios.")
            else:
                # Insertar el médico con su especialidad
                try:
                    execute(
                        """
                        INSERT INTO Medico (nombre, Apellidos, Duracion_de_cita, Telefono, Rut, Estado, Correo_Electronico, especialidad) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (nombre.strip(), apellidos.strip(), duracion_de_cita.strip(), telefono.strip(), rut.strip(), estado, correo_electronico.strip(), especialidad)
                    )
                    st.success("Médico creado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear el médico: {e}")

    # --- Helper para obtener lista de médicos con todos los campos necesarios ---
    def listado_medicos():
        return fetch_all(
            """
            SELECT
                M.id_medico,
                M.nombre,
                M.Apellidos,
                M.Duracion_de_cita,
                M.Telefono,
                M.Rut,
                M.Estado,
                M.Correo_Electronico,
                M.especialidad
            FROM Medico M
            ORDER BY M.nombre
            """
        )

    # -------- Editar --------
    with tabs[1]:
        medicos = listado_medicos()  # Usamos la función de listado actualizada
        if not medicos:
            st.info("No hay médicos registrados.")
        else:
            opciones = {f"{m['nombre']} – {m['especialidad']}": m for m in medicos}
            sel_key = st.selectbox("Selecciona un médico", list(opciones.keys()))
            sel = opciones[sel_key]
            
            with st.form("form_editar_medico"):
                nombre = st.text_input("Nombre", value=sel["nombre"])
                apellidos = st.text_input("Apellidos", value=sel["Apellidos"])
                duracion_de_cita = st.text_input("Duración de cita", value=sel["Duracion_de_cita"])
                telefono = st.text_input("Teléfono", value=sel["Telefono"])
                rut = st.text_input("RUT", value=sel["Rut"])
                estado = st.selectbox("Estado", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(sel["Estado"]))
                correo_actual = sel["Correo_Electronico"] or ""
                parte_user = correo_actual.replace("@gmail.com", "") if correo_actual.endswith("@gmail.com") else correo_actual

                col_u_e, col_d_e = st.columns([3, 2])
                with col_u_e:
                    correo_user_edit = st.text_input("Correo electrónico", value=parte_user)
                with col_d_e:
                    st.text_input(" ", value="@gmail.com", disabled=True)

                correo_electronico = (correo_user_edit.strip() + "@gmail.com") if correo_user_edit else ""


                # Lista de especialidades directamente en Medico
                especialidades = [
                    'Cirugía General', 'Cirugía Ortopédica', 'Cirugía Cardiaca', 
                    'Cirugía Plástica y Estética', 'Cirugía Neurocirúrgica', 
                    'Cirugía Ginecológica', 'Cirugía Urológica', 'Cirugía Oncológica', 
                    'Cirugía Oftalmológica', 'Cirugía Otorrinolaringológica', 
                    'Cirugía Torácica', 'Cirugía Maxilofacial'
                ]
                especialidad = st.selectbox("Especialidad", especialidades, index=especialidades.index(sel['especialidad']) if sel['especialidad'] else 0)

                submitted = st.form_submit_button("Guardar cambios")

            if submitted:
                if not nombre.strip() or not apellidos.strip() or not rut.strip() or not correo_electronico.strip():
                    st.error("El nombre, apellidos, RUT y correo electrónico son obligatorios.")
                else:
                    # Actualizar el médico con la nueva especialidad
                    try:
                        execute(
                            """
                            UPDATE Medico 
                            SET nombre=?, Apellidos=?, Duracion_de_cita=?, Telefono=?, Rut=?, Estado=?, Correo_Electronico=?, especialidad=? 
                            WHERE id_medico=?
                            """,
                            (nombre.strip(), apellidos.strip(), duracion_de_cita.strip(), telefono.strip(), rut.strip(), estado, correo_electronico.strip(), especialidad, sel["id_medico"])
                        )
                        st.success("Médico actualizado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar el médico: {e}")


    # -------- Eliminar --------
    with tabs[2]:
        medicos = listado_medicos()
        if not medicos:
            st.info("No hay médicos registrados.")
        else:
            opciones = {f"{m['nombre']} – {m['especialidad']}": m for m in medicos}
            sel_key = st.selectbox("Selecciona un médico a eliminar", list(opciones.keys()))
            sel = opciones[sel_key]
            
            if st.button("Eliminar médico", type="primary"):
                try:
                    execute("DELETE FROM Medico WHERE id_medico=?", (sel["id_medico"],))
                    st.success("Médico eliminado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar el médico: {e}")

    # -------- Listar --------
    with tabs[3]:
        rows = fetch_all(
            """
            SELECT id_medico, nombre, Apellidos, Duracion_de_cita, Telefono, Rut, Estado, Correo_Electronico, especialidad
            FROM Medico
            ORDER BY nombre
            """
        )

        if not rows:
            st.info("No hay médicos registrados.")
        else:
            st.dataframe([dict(r) for r in rows], use_container_width=True)
