import os
import sqlite3
from datetime import date, time
import contextlib
import pathlib
from typing import Any, Dict, List, Optional


# -------------------------------------------------------------
# Configuración y utilidades de base de datos
# -------------------------------------------------------------
DB_PATH = "base.db"
base_dir = os.path.dirname(DB_PATH) or "."
pathlib.Path(base_dir).mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    """Obtiene una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Configuración de rendimiento y concurrencia para Streamlit
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def execute(query: str, params: tuple = ()) -> int:
    """Ejecuta una consulta SQL de escritura (INSERT, UPDATE, DELETE)."""
    with contextlib.closing(get_conn()) as conn, conn:  # autocommit
        cur = conn.execute(query, params)
        return cur.lastrowid if cur.lastrowid is not None else 0


def fetch_all(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    """Ejecuta una consulta SQL de lectura y devuelve todos los resultados."""
    with contextlib.closing(get_conn()) as conn:
        return conn.execute(query, params).fetchall()


def fetch_one(query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    """Ejecuta una consulta SQL de lectura y devuelve el primer resultado."""
    with contextlib.closing(get_conn()) as conn:
        return conn.execute(query, params).fetchone()


def row_get(row: sqlite3.Row, *keys, default: Optional[str] = None):
    """Obtiene el valor de una fila según las claves proporcionadas."""
    for k in keys:
        if k is None:
            continue
        try:
            if k in row.keys():
                return row[k]
        except Exception:
            pass
    return default


# -------------------------------------------------------------
# Detección de esquema para compatibilidad hacia atrás
# -------------------------------------------------------------
def has_column(table: str, col: str) -> bool:
    """Verifica si una columna existe en una tabla."""
    rows = fetch_all(f"PRAGMA table_info('{table}')")
    return any(r[1].lower() == col.lower() for r in rows)  # r[1] es nombre de columna


def ensure_column(table: str, column: str, coltype: str, extra: str = ""):
    """Agrega una columna si no existe (migración segura)."""
    if not has_column(table, column):
        execute(f'ALTER TABLE {table} ADD COLUMN {column} {coltype} {extra}'.strip())


def init_db() -> None:
    """Crea tablas si no existen y aplica migraciones (no borra datos)."""
    # Tabla Paciente (esquema base)
    execute(
        """
        CREATE TABLE IF NOT EXISTS Paciente (
            id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT UNIQUE,
            nombre TEXT NOT NULL,
            fecha_nacimiento DATE,
            correo TEXT,
            telefono TEXT,
            direccion TEXT,
            alergias TEXT,
            enfermedades_previas TEXT,
            nacionalidad TEXT,
            sexo TEXT,
            estado_civil TEXT,
            tipo_paciente TEXT CHECK(tipo_paciente IN ('Ambulatorio', 'Urgencias', 'Hospitalizado')),
            tipo_sangre TEXT
            prevision TEXT CHECK(prevision IN ('Fonasa', 'Isapre'))
        );
        """
    )
    
        # Enfermedad crónica
    execute(
        """
        CREATE TABLE IF NOT EXISTS EnfermedadCronica (
            id_enfermedades_cronicas INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            nombre_enfermedad TEXT NOT NULL,
            observacion TEXT,
            tratamiento_actual TEXT,
            Año_diagnostico TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )

    # Cirugías previas
    execute(
        """
        CREATE TABLE IF NOT EXISTS CirugiaPrevia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            fecha TEXT,
            observacion TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )

    # Alergias declaradas por el paciente
    execute(
        """
        CREATE TABLE IF NOT EXISTS AlergiaPaciente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            Sustancia TEXT NOT NULL,
            reaccion TEXT,
            Gravedad TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )

    # Medicamentos actuales
    execute(
        """
        CREATE TABLE IF NOT EXISTS MedicamentoActual (
            id_Medicamento_Acutal INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            nombre_Medicamento TEXT NOT NULL,
            dosis TEXT,
            frecuencia TEXT,
            Via TEXT,
            Indicaciones TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )

    # Hábitos
    execute(
        """
        CREATE TABLE IF NOT EXISTS HabitoPaciente (
            id_Habitos INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            Frecuencia TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )

    # Tratamientos previos
    execute(
        """
        CREATE TABLE IF NOT EXISTS TratamientoPrevio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            resultado TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )

    # Solicitudes de examen
    execute(
        """
        CREATE TABLE IF NOT EXISTS SolicitudExamen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ficha_medica INTEGER NOT NULL,
            Tipo_de_examen TEXT NOT NULL,
            fecha_solicitud TEXT,
            Observaciones TEXT,
            Estado TEXT,
            FOREIGN KEY (ID_ficha_medica) REFERENCES FichaMedica(ID_Ficha) ON DELETE CASCADE
        );
        """
    )

    # Resultados de examen
    execute(
        """
        CREATE TABLE IF NOT EXISTS ResultadoExamen (
            ID_Resultado_Examen INTEGER NOT NULL,
            Fecha_Resultado TEXT,
            Archivo_adjunto TEXT,
            Resultado_texto TEXT,
            FOREIGN KEY (ID_Resultado_Examen) REFERENCES SolicitudExamen(id) ON DELETE CASCADE
        );
        """
    )

    # Tabla Medico (esquema base)
    execute(
        """
        CREATE TABLE IF NOT EXISTS Medico (
            id_medico INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            Apellidos TEXT,
            Duracion_de_cita TEXT,
            Telefono TEXT,
            Rut TEXT,
            Estado TEXT,
            Correo_Electronico TEXT,
            especialidad TEXT NOT NULL
        );
        """
    )
    
    # Tabla SignosVitales
    execute(
        """
        CREATE TABLE IF NOT EXISTS SignosVitales (
            ID_Signos_vitales INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Ficha_Medica INTEGER NOT NULL,
            presion_arterial TEXT,
            Temperatura REAL,
            Frecuencia_cardiaca INTEGER,
            peso REAL,
            FOREIGN KEY (ID_Ficha_Medica) REFERENCES FichaMedica(ID_Ficha)
        );
        """
    )

    # Tabla Cita
    execute(
        """
        CREATE TABLE IF NOT EXISTS Cita (
            id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            estado TEXT CHECK(estado IN ('Agendada','Realizada','Cancelada')) NOT NULL DEFAULT 'Agendada',
            id_paciente INTEGER NOT NULL,
            id_medico INTEGER NOT NULL,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE,
            FOREIGN KEY (id_medico) REFERENCES Medico(id_medico) ON DELETE CASCADE
        );
        """
    )
    
    # Tabla FichaMedica (historial clínico por visita)
    execute(
        """
        CREATE TABLE IF NOT EXISTS FichaMedica (
            ID_Ficha INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            motivo_consulta TEXT NOT NULL,
            Anamnesis TEXT,
            observaciones TEXT,
            FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
        );
        """
    )
    
    # Tabla Prescripcion (una o más por Ficha)
    execute(
        """
        CREATE TABLE IF NOT EXISTS Prescripcion (
            ID_Prescripcion   INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Ficha_Medica   INTEGER NOT NULL,
            Medicamento       TEXT,
            Dosis             TEXT,
            Frecuencia        TEXT,
            Duracion          TEXT,
            Via_administracion TEXT,
            Fecha_emision     TEXT,   -- ISO 'YYYY-MM-DD'
            Observaciones     TEXT,
            Estado            TEXT,   -- Pendiente / Dispensada / Cancelada, etc.
            FOREIGN KEY (ID_Ficha_Medica) REFERENCES FichaMedica(ID_Ficha)
        );
        """
    )
    
    #--- Migraciones por si la tabla ya existía con menos columnas---
    #--- Asegurar columna id_paciente---
    try:
        execute("ALTER TABLE FichaMedica ADD COLUMN id_paciente INTEGER;")
    except Exception:
        pass  # ya existe

    # Asegurar columna fecha_hora
    try:
        execute("ALTER TABLE FichaMedica ADD COLUMN fecha_hora TEXT;")
    except Exception:
        pass

    # Asegurar columna motivo_consulta
    try:
        execute("ALTER TABLE FichaMedica ADD COLUMN motivo_consulta TEXT;")
    except Exception:
        pass

    # Asegurar columna Anamnesis
    try:
        execute("ALTER TABLE FichaMedica ADD COLUMN Anamnesis TEXT;")
    except Exception:
        pass

    # Asegurar columna observaciones
    try:
        execute("ALTER TABLE FichaMedica ADD COLUMN observaciones TEXT;")
    except Exception:
        pass

    # --- Migraciones: nuevas columnas en Paciente ---
    ensure_column("Paciente", "nacionalidad", "TEXT")
    ensure_column("Paciente", "sexo", "TEXT")  # Femenino/Masculino/Otro o texto libre
    ensure_column("Paciente", "estado_civil", "TEXT")  # Soltero/Casado/...
    ensure_column("Paciente", "tipo_paciente", "TEXT", "CHECK(tipo_paciente IN ('Ambulatorio','Urgencias','Hospitalizado'))")
    ensure_column("Paciente", "tipo_sangre", "TEXT")  # O-, O+, etc.
    ensure_column("Paciente", "prevision", "TEXT", "CHECK(prevision IN ('Fonasa','Isapre'))")

    # Índices útiles
    execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_paciente_rut ON Paciente(rut);")
    execute("CREATE INDEX IF NOT EXISTS idx_cita_paciente ON Cita(id_paciente);")
    execute("CREATE INDEX IF NOT EXISTS idx_cita_medico ON Cita(id_medico);")
    execute("CREATE INDEX IF NOT EXISTS idx_cita_fecha_hora ON Cita(fecha, hora);")
    execute("CREATE INDEX IF NOT EXISTS idx_ficha_paciente_fecha ON FichaMedica(id_paciente, fecha_hora);")

# Mapeo dinámico de columnas para Paciente y Medico
def paciente_columns() -> Dict[str, Optional[str]]: 
    mapping = {
        "rut": "rut" if has_column("Paciente", "rut") else ("Rut_Paciente" if has_column("Paciente", "Rut_Paciente") else None),
        "nombre": "nombre" if has_column("Paciente", "nombre") else ("Nombre" if has_column("Paciente", "Nombre") else None),
        "apellido": "Apellido" if has_column("Paciente", "Apellido") else None,
        "fecha_nacimiento": "fecha_nacimiento" if has_column("Paciente", "fecha_nacimiento") else ("Fecha_Nacimiento" if has_column("Paciente", "Fecha_Nacimiento") else None),
        "correo": "correo" if has_column("Paciente", "correo") else ("Correo" if has_column("Paciente", "Correo") else None),
        "telefono": "telefono" if has_column("Paciente", "telefono") else ("Telefono" if has_column("Paciente", "Telefono") else None),
        "direccion": "direccion" if has_column("Paciente", "direccion") else ("Dirección" if has_column("Paciente", "Dirección") else None),
        "alergias": "alergias" if has_column("Paciente", "alergias") else None,
        "enfermedades_previas": "enfermedades_previas" if has_column("Paciente", "enfermedades_previas") else None,
        "nacionalidad": "nacionalidad" if has_column("Paciente", "nacionalidad") else None,
        "sexo": "sexo" if has_column("Paciente", "sexo") else None,
        "estado_civil": "estado_civil" if has_column("Paciente", "estado_civil") else None,
        "tipo_paciente": "tipo_paciente" if has_column("Paciente", "tipo_paciente") else None,
        "tipo_sangre": "tipo_sangre" if has_column("Paciente", "tipo_sangre") else None,
        "prevision": "prevision" if has_column("Paciente", "prevision") else None,
    }
    return mapping


def medico_columns() -> Dict[str, str]:
    return {
        "nombre": "nombre" if has_column("Medico", "nombre") else "nombre",  # Nombre del médico
        "apellidos": "Apellidos" if has_column("Medico", "Apellidos") else "Apellidos",  # Apellidos del médico
        "duracion_de_cita": "Duracion_de_cita" if has_column("Medico", "Duracion_de_cita") else "Duracion_de_cita",  # Duración de cita
        "telefono": "Telefono" if has_column("Medico", "Telefono") else "Telefono",  # Teléfono
        "rut": "Rut" if has_column("Medico", "Rut") else "Rut",  # RUT del médico
        "estado": "Estado" if has_column("Medico", "Estado") else "Estado",  # Estado del médico
        "correo_electronico": "Correo_Electronico" if has_column("Medico", "Correo_Electronico") else "Correo_Electronico",  # Correo electrónico
        "especialidad": "especialidad" if has_column("Medico", "especialidad") else "especialidad",  # Especialidad
    }


# Helpers de expresiones SQL seguras según columnas existentes
def expr_paciente_rut() -> str:
    pac = paciente_columns()
    if pac["rut"]:
        return f"{pac['rut']}"
    return "NULL"


def expr_paciente_nombre() -> str:
    pac = paciente_columns()
    if pac["nombre"] and not pac["apellido"]:
        return f"{pac['nombre']}"
    if pac["nombre"] and pac["apellido"]:
        return "TRIM(" + pac["nombre"] + " || ' ' || COALESCE(" + pac["apellido"] + ",''))"
    return "''"


def expr_medico_nombre() -> str:
    med = medico_columns()
    return med["nombre"]


def expr_medico_esp() -> str:
    return "M.especialidad AS especialidad"  

# -------- Versiones aliased para evitar ambigüedad en JOINs (P.*, M.*) -----
def expr_paciente_rut_aliased(alias: str = "P") -> str:
    pac = paciente_columns()
    if pac["rut"]:
        return f"{alias}.{pac['rut']}"
    return "NULL"

def expr_paciente_nombre_aliased(alias: str = "P") -> str:
    pac = paciente_columns()
    if pac["nombre"] and not pac["apellido"]:
        return f"{alias}.{pac['nombre']}"
    if pac["nombre"] and pac["apellido"]:
        return f"TRIM({alias}.{pac['nombre']} || ' ' || COALESCE({alias}.{pac['apellido']},''))"
    return "''"   # <- esta línea evita el error SQL inválido

def expr_medico_nombre_aliased(alias: str = "M") -> str:
    med = medico_columns()
    return f"{alias}.{med['nombre']}"

def expr_medico_esp_aliased() -> str:
    return "M.especialidad AS especialidad"  
