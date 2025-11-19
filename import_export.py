import io
import csv
import contextlib

import pandas as pd
import streamlit as st

from db import get_conn


# Helper para leer un SELECT como DataFrame
def df(query: str, params: tuple = ()):
    with contextlib.closing(get_conn()) as conn:
        return pd.read_sql_query(query, conn, params=params)


def sidebar_exports_imports():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📤 Exportar CSV")

    # =========================================================================
    # EXPORTAR PACIENTES
    # =========================================================================
    try:
        pacientes_df = df(
            """
            SELECT
                id_paciente,
                rut,
                nombre,
                fecha_nacimiento,
                correo,
                telefono,
                direccion,
                nacionalidad,
                sexo,
                estado_civil,
                tipo_paciente,
                tipo_sangre,
                prevision
            FROM Paciente
            ORDER BY nombre
            """
        )
        st.sidebar.download_button(
            "Descargar Pacientes.csv",
            data=pacientes_df.to_csv(index=False).encode("utf-8"),
            file_name="Pacientes_export.csv",
            mime="text/csv",
        )
    except Exception as ex:
        st.sidebar.caption(f"Pacientes (export): {ex}")

    # =========================================================================
    # EXPORTAR MÉDICOS
    # =========================================================================
    try:
        medicos_df = df(
            """
            SELECT
                id_medico,
                nombre,
                apellidos,
                duracion_de_cita,
                telefono,
                rut,
                estado,
                correo_electronico,
                especialidad
            FROM Medico
            ORDER BY nombre
            """
        )
        st.sidebar.download_button(
            "Descargar Medicos.csv",
            data=medicos_df.to_csv(index=False).encode("utf-8"),
            file_name="Medicos_export.csv",
            mime="text/csv",
        )
    except Exception as ex:
        st.sidebar.caption(f"Médicos (export): {ex}")

    # =========================================================================
    # EXPORTAR CITAS
    # =========================================================================
    try:
        citas_df = df(
            """
            SELECT
                C.id_cita,
                C.fecha,
                C.hora,
                C.estado,
                C.id_paciente,
                C.id_medico,
                P.rut     AS rut_paciente,
                P.nombre  AS nombre_paciente,
                M.nombre  AS nombre_medico,
                M.especialidad AS especialidad_medico
            FROM Cita C
            JOIN Paciente P ON P.id_paciente = C.id_paciente
            JOIN Medico   M ON M.id_medico   = C.id_medico
            ORDER BY C.fecha DESC, C.hora DESC
            """
        )
        st.sidebar.download_button(
            "Descargar Citas.csv",
            data=citas_df.to_csv(index=False).encode("utf-8"),
            file_name="Citas_export.csv",
            mime="text/csv",
        )
    except Exception as ex:
        st.sidebar.caption(f"Citas (export): {ex}")

    # =========================================================================
    # EXPORTAR FICHA MÉDICA
    # =========================================================================
    try:
        ficha_df = df(
            """
            SELECT
                F.ID_Ficha,
                F.fecha_hora,
                F.motivo_consulta,
                F.Anamnesis,
                F.observaciones,
                SV.presion_arterial    AS presion_arterial,
                SV.Temperatura         AS temperatura,
                SV.Frecuencia_cardiaca AS frecuencia_cardiaca,
                SV.peso                AS peso,
                F.id_paciente,
                P.rut    AS rut_paciente,
                P.nombre AS nombre_paciente
            FROM FichaMedica F
            JOIN Paciente P
              ON P.id_paciente = F.id_paciente
            LEFT JOIN SignosVitales SV
              ON SV.ID_Ficha_Medica = F.ID_Ficha
            ORDER BY datetime(F.fecha_hora) DESC
            """
        )
        st.sidebar.download_button(
            "Descargar FichaMedica.csv",
            data=ficha_df.to_csv(index=False).encode("utf-8"),
            file_name="FichaMedica_export.csv",
            mime="text/csv",
        )
    except Exception as ex:
        st.sidebar.caption(f"Ficha Médica (export): {ex}")

    # =====================================================================
    #  IMPORTAR CSV
    # =====================================================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Importar CSV")

    # =====================================================================
    #  IMPORTAR PACIENTES 
    # =====================================================================
    with st.sidebar.expander("Importar Pacientes.csv"):
        up = st.file_uploader("Selecciona CSV de Pacientes", type=["csv"], key="up_pac")
        if up is not None:
            try:
                # Leemos el archivo UNA sola vez
                raw = up.read()
                if not raw:
                    st.error("El archivo CSV está vacío.")
                    return

                # Decodificamos texto (Excel en Windows suele ir bien con latin1)
                txt = raw.decode("latin1", errors="ignore")

                # 1) Intento normal con coma (sep=",")
                data = pd.read_csv(io.StringIO(txt), sep=",")

                # 2) Caso “encabezado raro”: solo 1 columna y dentro hay ';'
                if len(data.columns) == 1 and ";" in data.columns[0]:
                    st.warning("Encabezado de CSV inválido detectado. Aplicando corrección...")

                    # Limpiamos: sacamos comillas al inicio/fin de cada línea
                    lines = txt.splitlines()
                    clean = "\n".join(
                        l.strip().strip('"')
                        for l in lines
                        if l.strip()
                    )

                    # Releemos ahora sí como CSV separado por ';'
                    data = pd.read_csv(io.StringIO(clean), sep=";", engine="python")

                # ================================
                # 1) Leemos columnas REALES de la tabla Paciente
                # ================================
                with contextlib.closing(get_conn()) as conn:
                    cur = conn.execute("PRAGMA table_info(Paciente)")
                    db_cols = [row[1] for row in cur.fetchall()]

                # ================================
                # 2) Columnas posibles que pueden venir desde el CSV
                # ================================
                csv_cols_posibles = [
                    "id_paciente",
                    "rut",
                    "nombre",
                    "apellido",            # si en algún momento lo usas separado
                    "fecha_nacimiento",
                    "correo",
                    "telefono",
                    "direccion",
                    "alergias",
                    "enfermedades_previas",
                    "nacionalidad",
                    "sexo",
                    "estado_civil",
                    "tipo_paciente",
                    "tipo_sangre",
                    "prevision",
                ]

                # Aviso si el CSV trae columnas que NO existen en la BD
                extras = [c for c in csv_cols_posibles if c in data.columns and c not in db_cols]
                if extras:
                    st.info(
                        "Estas columnas están en el CSV pero no en la tabla Paciente; se ignorarán: "
                        + ", ".join(extras)
                    )

                # ================================
                # 3) Nos quedamos solo con columnas que:
                #    (a) estén en el CSV y
                #    (b) EXISTAN en la tabla Paciente
                # ================================
                present = [c for c in csv_cols_posibles if c in data.columns and c in db_cols]

                if not present:
                    st.error(
                        "No se detectaron columnas compatibles en el CSV de Pacientes. "
                        "Revisa que los encabezados sean rut, nombre, fecha_nacimiento, etc."
                    )
                    return

                # Nunca insertamos id_paciente (AUTOINCREMENT)
                if "id_paciente" in present:
                    present.remove("id_paciente")

                # ================================
                # 4) Normalizaciones de datos (solo si la columna existe)
                # ================================
                if "fecha_nacimiento" in present:
                    data["fecha_nacimiento"] = (
                        pd.to_datetime(
                            data["fecha_nacimiento"],
                            errors="coerce",
                            dayfirst=True,
                        )
                        .dt.strftime("%Y-%m-%d")
                    )

                if "telefono" in present:
                    data["telefono"] = (
                        data["telefono"]
                        .astype(str)
                        .str.strip()
                        .replace({"nan": None, "None": None})
                    )

                if "prevision" in present:
                    data["prevision"] = (
                        data["prevision"]
                        .astype(str)
                        .str.upper()
                        .str.strip()
                        .replace(
                            {
                                "FONAS": "FONASA",
                                "FONASA ": "FONASA",
                                "ISAPRES": "ISAPRE",
                                "IS APRE": "ISAPRE",
                                "": None,
                                "NONE": None,
                                "NAN": None,
                                "NULL": None,
                            }
                        )
                    )
                    data["prevision"] = data["prevision"].where(
                        data["prevision"].isin(["FONASA", "ISAPRE"]), None
                    )

                # ================================
                # 5) Limpieza de RUT y filtro contra BD
                # ================================
                if "rut" in present:
                    # Filtrar vacíos
                    before = len(data)
                    data = data[data["rut"].astype(str).str.strip().ne("")]
                    dropped = before - len(data)
                    if dropped > 0:
                        st.warning(f"Se omitieron {dropped} filas con RUT vacío.")

                    # Evitar duplicados dentro del propio CSV
                    data = data.drop_duplicates(subset=["rut"], keep="last")

                    # Filtrar RUT que ya están en la base
                    with contextlib.closing(get_conn()) as conn:
                        existing = conn.execute(
                            "SELECT rut FROM Paciente WHERE rut IS NOT NULL"
                        ).fetchall()
                    existing_ruts = {row[0] for row in existing}

                    before_db = len(data)
                    data = data[~data["rut"].isin(existing_ruts)]
                    skipped = before_db - len(data)
                    if skipped > 0:
                        st.info(
                            f"Se omitieron {skipped} filas porque el RUT ya existe en Paciente."
                        )

                # ================================
                # 6) Insertar SOLO columnas que existen en la tabla
                # ================================
                if len(data) == 0:
                    st.warning(
                        "No quedaron filas nuevas para importar "
                        "(todos los RUT ya existían o los datos estaban vacíos)."
                    )
                    return

                with contextlib.closing(get_conn()) as conn:
                    data[present].to_sql(
                        "Paciente",
                        conn,
                        if_exists="append",
                        index=False,
                    )

                st.success(f"Se importaron {len(data[present])} filas nuevas a Paciente.")
                st.rerun()

            except Exception as e:
                st.error(f"Error importando Pacientes: {e}")

    # =====================================================================
    #  IMPORTAR MÉDICOS 
    # =====================================================================
    with st.sidebar.expander("Importar Medicos.csv"):
        up_m = st.file_uploader(
            "Selecciona CSV de Médicos", type=["csv"], key="up_med"
        )
        if up_m is not None:
            try:
                raw = up_m.read()
                if not raw:
                    st.error("El archivo CSV de Médicos está vacío.")
                    return

                txt = raw.decode("latin1", errors="ignore")
                lines = txt.splitlines()
                if not lines:
                    st.error("El archivo CSV no tiene contenido.")
                    return

                # Cabecera original (nombres de columnas tal como los exporta tu sistema)
                header = lines[0]

                filas_limpias = []
                for l in lines[1:]:
                    if not l.strip():
                        continue
                    s = l.strip()
                    # Caso feo: toda la fila entre comillas y separada por ';'
                    if ";" in s and s.startswith('"') and s.endswith('"'):
                        inner = s.strip('"')
                        partes = inner.split(";")
                        filas_limpias.append(",".join(partes))
                    else:
                        # Línea ya normal con comas
                        filas_limpias.append(s)

                clean_txt = "\n".join([header] + filas_limpias)

                # Leemos el CSV ya normalizado
                data = pd.read_csv(io.StringIO(clean_txt), sep=",")

                # Ver columnas reales de la tabla Medico
                with contextlib.closing(get_conn()) as conn:
                    cur = conn.execute("PRAGMA table_info(Medico)")
                    db_cols = [row[1] for row in cur.fetchall()]

                # Columnas posibles según tu esquema/export
                posibles = [
                    "id_medico",
                    "nombre",
                    "Apellidos",
                    "Duracion_de_cita",
                    "Telefono",
                    "Rut",
                    "Estado",
                    "Correo_Electronico",
                    "especialidad",
                ]

                # Solo columnas que existen en CSV y en la tabla
                present = [c for c in posibles if c in data.columns and c in db_cols]
                if not present:
                    st.error(
                        "No se detectaron columnas compatibles en el CSV de Médicos. "
                        "Ejemplo: nombre, Apellidos, Rut, especialidad..."
                    )
                    return

                # Nunca insertamos id_medico (AUTOINCREMENT)
                if "id_medico" in present:
                    present.remove("id_medico")

                # Nos quedamos con las columnas relevantes
                data_sub = data[present].copy()

                # Limpiar filas completamente vacías
                data_sub = data_sub.dropna(how="all")

                # Regla mínima: sin nombre o sin Rut, no tiene sentido crear médico
                if "nombre" in data_sub.columns:
                    data_sub = data_sub[data_sub["nombre"].astype(str).str.strip().ne("")]
                if "Rut" in data_sub.columns:
                    data_sub = data_sub[data_sub["Rut"].astype(str).str.strip().ne("")]

                if data_sub.empty:
                    st.warning("Después de limpiar, no quedaron filas válidas para importar.")
                    return

                # Evitar duplicados por Rut dentro del propio archivo
                if "Rut" in data_sub.columns:
                    data_sub = data_sub.drop_duplicates(subset=["Rut"], keep="last")

                    # --- NUEVO: filtrar RUT que ya existen en la BD ---
                    with contextlib.closing(get_conn()) as conn:
                        existing = conn.execute(
                            "SELECT Rut FROM Medico WHERE Rut IS NOT NULL"
                        ).fetchall()
                    existing_ruts = {row[0] for row in existing}

                    before_db = len(data_sub)
                    data_sub = data_sub[~data_sub["Rut"].isin(existing_ruts)]
                    skipped = before_db - len(data_sub)
                    if skipped > 0:
                        st.info(
                            f"Se omitieron {skipped} filas porque el Rut ya existe en Medico."
                        )

                if data_sub.empty:
                    st.warning(
                        "No quedaron filas nuevas para importar "
                        "(todos los Rut ya existían o los datos estaban vacíos)."
                    )
                    return

                # Insertar en la tabla Medico
                with contextlib.closing(get_conn()) as conn:
                    data_sub.to_sql("Medico", conn, if_exists="append", index=False)

                st.success(f"Se importaron {len(data_sub)} médicos nuevos.")
                st.rerun()

            except Exception as e:
                st.error(f"Error importando Médicos: {e}")

    # =====================================================================
    #  IMPORTAR CITAS 
    # =====================================================================
    with st.sidebar.expander("Importar Citas.csv"):
        up_c = st.file_uploader(
            "Selecciona CSV de Citas", type=["csv"], key="up_cit"
        )
        if up_c is not None:
            try:
                raw = up_c.read()
                if not raw:
                    st.error("El archivo CSV de Citas está vacío.")
                    return

                txt = raw.decode("latin1", errors="ignore")
                lines = txt.splitlines()
                if not lines:
                    st.error("El archivo CSV no tiene contenido.")
                    return

                # Detectamos formato de las filas de datos
                line1 = lines[1] if len(lines) > 1 else ""
                usa_punto_coma = line1.count(";") > 0 and line1.count(";") >= line1.count(",")

                if usa_punto_coma:
                    # CASO 1: filas como "101;2025-11-20;10:00:00;..."
                    header = lines[0]
                    header_cols = header.split(",")  # nombres originales

                    data_lines = [
                        l.strip().strip('"')
                        for l in lines[1:]
                        if l.strip()
                    ]

                    clean_txt = ";".join(header_cols) + "\n" + "\n".join(data_lines)
                    data = pd.read_csv(io.StringIO(clean_txt), sep=";", engine="python")
                else:
                    # CASO 2: CSV ya limpio con comas normales
                    data = pd.read_csv(io.StringIO(txt), sep=",")

                # Columnas posibles según tu export
                posibles = [
                    "id_cita",
                    "fecha",
                    "hora",
                    "estado",
                    "id_paciente",
                    "id_medico",
                    "rut_paciente",
                    "nombre_paciente",
                    "nombre_medico",
                    "especialidad_medico",
                ]

                # Columnas reales de la tabla Cita
                with contextlib.closing(get_conn()) as conn:
                    cur = conn.execute("PRAGMA table_info(Cita)")
                    db_cols = [row[1] for row in cur.fetchall()]

                present = [c for c in posibles if c in data.columns and c in db_cols]
                if not present:
                    st.error(
                        "No se detectaron columnas compatibles en el CSV de Citas. "
                        "Se esperaban al menos: fecha, hora, id_paciente, id_medico."
                    )
                    return

                # Nunca insertamos id_cita (AUTOINCREMENT)
                if "id_cita" in present:
                    present.remove("id_cita")

                data_sub = data[present].copy()
                data_sub = data_sub.dropna(how="all")

                # Campos críticos
                obligatorias = [c for c in ["fecha", "hora", "id_paciente", "id_medico"] if c in data_sub.columns]
                for col in obligatorias:
                    data_sub = data_sub[data_sub[col].astype(str).str.strip().ne("")]

                if data_sub.empty:
                    st.warning("Después de limpiar, no quedaron filas válidas para importar.")
                    return

                # Normalizar fecha y hora
                if "fecha" in data_sub.columns:
                    data_sub["fecha"] = (
                        pd.to_datetime(data_sub["fecha"], errors="coerce", dayfirst=True)
                        .dt.date.astype(str)
                    )
                if "hora" in data_sub.columns:
                    data_sub["hora"] = (
                        pd.to_datetime(data_sub["hora"], errors="coerce")
                        .dt.time.astype(str)
                    )

                if "fecha" in data_sub.columns:
                    data_sub = data_sub[data_sub["fecha"].astype(str).str.strip().ne("NaT")]
                if "hora" in data_sub.columns:
                    data_sub = data_sub[data_sub["hora"].astype(str).str.strip().ne("NaT")]

                if data_sub.empty:
                    st.warning("No quedaron filas válidas después de normalizar fecha y hora.")
                    return

                # Evitar duplicados dentro del propio archivo
                subset_dup = [c for c in ["fecha", "hora", "id_paciente", "id_medico"] if c in data_sub.columns]
                if subset_dup:
                    data_sub = data_sub.drop_duplicates(subset=subset_dup, keep="last")

                # Evitar duplicados contra la BD
                if all(c in data_sub.columns for c in ["fecha", "hora", "id_paciente", "id_medico"]):
                    with contextlib.closing(get_conn()) as conn:
                        existing = conn.execute(
                            "SELECT fecha, hora, id_paciente, id_medico FROM Cita"
                        ).fetchall()
                    existing_keys = {
                        f"{f}|{h}|{pid}|{mid}"
                        for (f, h, pid, mid) in existing
                    }

                    def make_key(row):
                        return f"{row['fecha']}|{row['hora']}|{row['id_paciente']}|{row['id_medico']}"

                    before_db = len(data_sub)
                    data_sub = data_sub[~data_sub.apply(make_key, axis=1).isin(existing_keys)]
                    skipped = before_db - len(data_sub)
                    if skipped > 0:
                        st.info(f"Se omitieron {skipped} citas porque ya existían en la BD.")

                if data_sub.empty:
                    st.warning(
                        "No quedaron citas nuevas para importar "
                        "(todas ya existían o los datos estaban vacíos)."
                    )
                    return

                with contextlib.closing(get_conn()) as conn:
                    data_sub.to_sql("Cita", conn, if_exists="append", index=False)

                st.success(f"Se importaron {len(data_sub)} citas nuevas.")
                st.rerun()

            except Exception as e:
                st.error(f"Error importando Citas: {e}")


   # =====================================================================
    #  IMPORTAR FICHA MÉDICA 
    # =====================================================================
    with st.sidebar.expander("Importar FichaMedica.csv"):
        up_f = st.file_uploader(
            "Selecciona CSV de Ficha Médica", type=["csv"], key="up_ficha"
        )
        if up_f is not None:
            try:
                raw = up_f.read()
                if not raw:
                    st.error("El archivo CSV de Ficha Médica está vacío.")
                    return

                txt = raw.decode("latin1", errors="ignore")
                lines = txt.splitlines()
                if not lines:
                    st.error("El archivo CSV no tiene contenido.")
                    return

                # Detectar si las filas vienen con ';' (CSV “roto”) o con comas normales
                line1 = lines[1] if len(lines) > 1 else ""
                usa_punto_coma = line1.count(";") > 0 and line1.count(";") >= line1.count(",")

                if usa_punto_coma:
                    # CASO 1: filas tipo "1;2025-11-20 10:00;Dolor..."
                    header = lines[0]
                    header_cols = header.split(",")  # nombres originales del export

                    data_lines = [
                        l.strip().strip('"')
                        for l in lines[1:]
                        if l.strip()
                    ]

                    clean_txt = ";".join(header_cols) + "\n" + "\n".join(data_lines)
                    data = pd.read_csv(io.StringIO(clean_txt), sep=";", engine="python")
                else:
                    # CASO 2: CSV ya limpio con comas
                    data = pd.read_csv(io.StringIO(txt), sep=",")

                # --- Consultar esquema real de FichaMedica ---
                with contextlib.closing(get_conn()) as conn:
                    cur = conn.execute("PRAGMA table_info(FichaMedica)")
                    db_cols = [row[1] for row in cur.fetchall()]

                # Determinar qué columna usar para anamnesis en la BD
                anam_col_db = None
                if "Anamnesis" in db_cols:
                    anam_col_db = "Anamnesis"
                elif "Anamesis" in db_cols:
                    anam_col_db = "Anamesis"

                # Mapeo de nombres del CSV -> nombres de la tabla
                rename_map = {
                    "ID_Ficha": "ID_Ficha",
                    "id_ficha": "ID_Ficha",
                    "ID_paciente": "ID_paciente",
                    "id_paciente": "ID_paciente",
                    "paciente_id": "ID_paciente",
                    "fecha_hora": "fecha_hora",
                    "FechaHora": "fecha_hora",
                    "fecha": "fecha_hora",
                    "motivo_consulta": "motivo_consulta",
                    "Motivo_consulta": "motivo_consulta",
                    "motivo": "motivo_consulta",
                    "Anamnesis": anam_col_db or "Anamnesis",
                    "anamnesis": anam_col_db or "Anamnesis",
                    "Anamesis": anam_col_db or "Anamnesis",
                    "observaciones": "observaciones",
                    "Observaciones": "observaciones",
                    # columnas de signos vitales (se usan para otra tabla)
                    "presion_arterial": "presion_arterial",
                    "Presion_arterial": "presion_arterial",
                    "Temperatura": "Temperatura",
                    "temperatura": "Temperatura",
                    "Frecuencia_cardiaca": "Frecuencia_cardiaca",
                    "frecuencia_cardiaca": "Frecuencia_cardiaca",
                    "peso": "peso",
                    # joins que podríamos ignorar
                    "rut_paciente": "rut_paciente",
                    "nombre_paciente": "nombre_paciente",
                }

                cols_presentes = {
                    c: rename_map[c]
                    for c in data.columns
                    if c in rename_map and rename_map[c] is not None
                }
                data = data.rename(columns=cols_presentes)

                # Columnas posibles ligadas a FichaMedica
                posibles_ficha = [
                    "ID_Ficha",
                    "ID_paciente",
                    "fecha_hora",
                    "motivo_consulta",
                    "observaciones",
                ]
                if anam_col_db:
                    posibles_ficha.append(anam_col_db)

                # Columnas de signos vitales si vienen en el CSV
                posibles_sv = [
                    "presion_arterial",
                    "Temperatura",
                    "Frecuencia_cardiaca",
                    "peso",
                ]

                # Solo columnas de FichaMedica que están en CSV y en la tabla
                present_ficha = [c for c in posibles_ficha if c in data.columns and c in db_cols]

                if not present_ficha:
                    st.error(
                        "No se detectaron columnas compatibles en el CSV de Ficha Médica. "
                        "Se esperaban al menos ID_paciente, fecha_hora, motivo_consulta, anamnesis, observaciones."
                    )
                    return

                # Nunca insertamos ID_Ficha (AUTOINCREMENT)
                if "ID_Ficha" in present_ficha:
                    present_ficha.remove("ID_Ficha")

                # Campos obligatorios
                requeridas_base = ["ID_paciente", "fecha_hora", "motivo_consulta", "observaciones"]
                if anam_col_db:
                    requeridas_base.append(anam_col_db)

                requeridas = [c for c in requeridas_base if c in present_ficha]

                # Validar que las requeridas existan en CSV
                faltantes = [c for c in requeridas if c not in data.columns]
                if faltantes:
                    st.error(
                        f"Faltan columnas obligatorias en el CSV de Ficha Médica: {faltantes}"
                    )
                    return

                # Sub-DF de fichas, conservando también las columnas de signos vitales si están
                columnas_usar = present_ficha + [c for c in posibles_sv if c in data.columns]
                data_sub = data[columnas_usar].copy()

                # Normalizar fecha_hora
                if "fecha_hora" in data_sub.columns:
                    data_sub["fecha_hora"] = pd.to_datetime(
                        data_sub["fecha_hora"], errors="coerce"
                    ).dt.strftime("%Y-%m-%d %H:%M:%S")

                # Limpiar filas completamente vacías
                data_sub = data_sub.dropna(how="all")

                # Validar que las columnas requeridas no estén vacías
                for col in requeridas:
                    data_sub = data_sub[data_sub[col].astype(str).str.strip().ne("")]

                if data_sub.empty:
                    st.warning("Después de limpiar, no quedaron filas válidas para importar Ficha Médica.")
                    return

                # Evitar duplicados por (ID_paciente, fecha_hora) contra la BD
                if "ID_paciente" in data_sub.columns and "fecha_hora" in data_sub.columns:
                    with contextlib.closing(get_conn()) as conn:
                        existing = conn.execute(
                            "SELECT ID_paciente, fecha_hora FROM FichaMedica"
                        ).fetchall()
                    existing_keys = {f"{pid}|{fh}" for (pid, fh) in existing}

                    def make_key(row):
                        return f"{row['ID_paciente']}|{row['fecha_hora']}"

                    before_db = len(data_sub)
                    data_sub = data_sub[~data_sub.apply(make_key, axis=1).isin(existing_keys)]
                    skipped = before_db - len(data_sub)
                    if skipped > 0:
                        st.info(
                            f"Se omitieron {skipped} fichas porque ya existían en la BD "
                            "(misma combinación ID_paciente + fecha_hora)."
                        )

                if data_sub.empty:
                    st.warning(
                        "No quedaron fichas nuevas para importar "
                        "(todas ya existían o los datos estaban vacíos)."
                    )
                    return

                # ========== INSERT MANUAL: FichaMedica + SignosVitales ==========
                inserted_fichas = 0
                inserted_sv = 0

                with contextlib.closing(get_conn()) as conn:
                    cur = conn.cursor()

                    for _, row in data_sub.iterrows():
                        # Campos de ficha
                        id_pac = row["ID_paciente"]
                        fh = row["fecha_hora"]
                        mot = row["motivo_consulta"]
                        obs = row.get("observaciones", None)
                        anam_val = None
                        if anam_col_db and anam_col_db in row:
                            anam_val = row[anam_col_db]

                        cur.execute(
                            f"""
                            INSERT INTO FichaMedica
                                (ID_paciente, fecha_hora, motivo_consulta, {anam_col_db if anam_col_db else 'Anamnesis'}, observaciones)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                id_pac,
                                fh,
                                mot,
                                anam_val,
                                obs,
                            ),
                        )
                        ficha_id = cur.lastrowid
                        inserted_fichas += 1

                        # Campos de signos vitales (si existen en el CSV)
                        pres = row.get("presion_arterial", None) if "presion_arterial" in row else None
                        temp = row.get("Temperatura", None) if "Temperatura" in row else None
                        fc = row.get("Frecuencia_cardiaca", None) if "Frecuencia_cardiaca" in row else None
                        peso_val = row.get("peso", None) if "peso" in row else None

                        # Si viene al menos un dato de signos vitales, insertamos en SignosVitales
                        if not (
                            (pd.isna(pres) if 'presion_arterial' in row else True)
                            and (pd.isna(temp) if 'Temperatura' in row else True)
                            and (pd.isna(fc) if 'Frecuencia_cardiaca' in row else True)
                            and (pd.isna(peso_val) if 'peso' in row else True)
                        ):
                            cur.execute(
                                """
                                INSERT INTO SignosVitales
                                    (ID_Ficha_Medica, presion_arterial, Temperatura, Frecuencia_cardiaca, peso)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    ficha_id,
                                    pres,
                                    temp,
                                    fc,
                                    peso_val,
                                ),
                            )
                            inserted_sv += 1

                    conn.commit()

                st.success(
                    f"Se importaron {inserted_fichas} fichas nuevas a FichaMedica. "
                    f"Se registraron signos vitales para {inserted_sv} fichas."
                )
                st.rerun()

            except Exception as e:
                st.error(f"Error importando Ficha Médica: {e}")