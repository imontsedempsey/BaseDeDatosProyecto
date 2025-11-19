import streamlit as st                           #streamlit run app.py
from ui_pacientes import ui_pacientes
from ui_medicos import ui_medicos
from ui_citas import ui_citas
from import_export import sidebar_exports_imports
from db import DB_PATH, init_db
from pathlib import Path
import base64, pathlib
from ui_ficha_medica import ui_ficha_medica
# -------------------------------------------------------------
# App principal
# -------------------------------------------------------------
def main():
    st.set_page_config(page_title="SGP – Sistema de Gestión de Pacientes", layout="wide")
    img_path = pathlib.Path("foto.jpg")
    if img_path.exists():
        with open(img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <style>
            /* ===== Fondo general ===== */
            .stApp {{
                background-image: url("data:image/jpg;base64,{data}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}

            /* ===== Variables de color ===== */
            :root {{
                --panel-bg: rgba(10, 10, 10, 0.88);
                --panel-border: rgba(255,255,255,0.08);
                --panel-radius: 12px;
                --panel-shadow: 0 8px 20px rgba(0,0,0,0.6);
                --text-light: #ffffff;
            }}

            /* ===== Contenedor principal ===== */
            .main .block-container {{
                background: transparent !important;
                box-shadow: none !important;
            }}

            /* ===== Sidebar ===== */
            section[data-testid="stSidebar"] {{
                background: var(--panel-bg) !important;
                color: var(--text-light) !important;
                box-shadow: var(--panel-shadow);
                border-right: 1px solid var(--panel-border);
            }}

            section[data-testid="stSidebar"] * {{
                color: var(--text-light) !important;
            }}

            section[data-testid="stSidebar"] .stButton>button,
            section[data-testid="stSidebar"] .stDownloadButton>button,
            section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"],
            section[data-testid="stSidebar"] .stRadio > div {{
                background-color: rgba(20,20,20,0.9) !important;
                border: 1px solid var(--panel-border);
                border-radius: var(--panel-radius);
                color: var(--text-light) !important;
                box-shadow: var(--panel-shadow);
            }}

            /* ===== Header (título) ===== */
            .top-header-card {{
                background: var(--panel-bg);
                border-radius: var(--panel-radius);
                padding: 1.5rem 2rem;
                box-shadow: var(--panel-shadow);
                border: 1px solid var(--panel-border);
                margin-bottom: 1rem;
            }}

            .top-header-card h1 {{
                color: var(--text-light) !important;
                margin: 0;
                text-align: center;
                text-shadow: 0 3px 10px rgba(0,0,0,0.8);
                font-weight: 600;
            }}

            .top-header-separator {{
                border-top: 1px solid rgba(255,255,255,0.5);
                margin-top: 1rem;
            }}

            hr {{ display:none; }}

            /* ===== Formularios / tabs ===== */
            .stTabs [data-baseweb="tab-list"],
            .stTabs [data-baseweb="tab"],
            div[data-testid="stTextInput"] > div > div,
            div[data-testid="stTextArea"] > div > textarea,
            div[data-testid="stDateInput"] > div,
            div[data-testid="stNumberInput"] > div,
            div[data-baseweb="select"] > div,
            div[data-testid="stSelectbox"] > div {{
                background-color: rgba(15,15,15,0.9) !important;
                color: var(--text-light) !important;
                border-radius: var(--panel-radius) !important;
                border: 1px solid var(--panel-border) !important;
                box-shadow: var(--panel-shadow);
            }}

            label, .stMarkdown p, .stMarkdown span, .stMarkdown h2, .stMarkdown h3 {{
                color: var(--text-light) !important;
            }}

            input::placeholder, textarea::placeholder {{
                color: rgba(255,255,255,0.6) !important;
            }}

            /* === Oscurecer fondo debajo de los inputs del formulario === */
            div[data-testid="stForm"] {{
                background: rgba(0, 0, 0, 0.80) !important;  /* ← más oscuro y sólido */
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.6);
                border: 1px solid rgba(255,255,255,0.1);
            }}

            div[data-testid="stForm"] label,
            div[data-testid="stForm"] p,
            div[data-testid="stForm"] span {{
                color: #ffffff !important;
            }}

            /* ===== Recuadro oscuro translúcido para la sección de Citas ===== */
            div[data-testid="stTabs"] {{
                background: rgba(0, 0, 0, 0.78) !important;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}

            div[data-testid="stTabs"] p,
            div[data-testid="stTabs"] span,
            div[data-testid="stTabs"] label {{
                color: #ffffff !important;
            }}

            /* Botones de Guardar / Eliminar en modo dark */
            button[kind="secondary"],
            button[kind="primary"] {{
                background-color: rgba(30,30,30,0.95) !important;
                color: #ffffff !important;
                border-radius: 10px !important;
                border: 1px solid rgba(255,255,255,0.1) !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="top-header-card">
                <h1>Belen Aguirres Clinica Politecnica de Santiago</h1>
                <div class="top-header-separator"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.sidebar.success(f"Base de datos: {DB_PATH}")

    # Inicializa (no borra datos existentes)
    init_db()

    # Barra lateral: exportar/importar CSV con pandas
    sidebar_exports_imports()

    # Navegación
    seccion = st.sidebar.radio("Secciones", ["Pacientes", "Médicos", "Citas", "Ficha Médica"], index=0)

    if seccion == "Pacientes":
        ui_pacientes()
    elif seccion == "Médicos":
        ui_medicos()
    elif seccion == "Ficha Médica":
        ui_ficha_medica()
    else:
        ui_citas()
        


if __name__ == "__main__":
    main()
