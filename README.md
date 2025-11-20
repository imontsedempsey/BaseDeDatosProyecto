# Sistema de Gestión de Pacientes 
# Integrantes:
- Milovan Caniullan
- Montserrat Muñoz
- Constanza Navarro

Este es un sistema desarrollado en Streamlit para la gestión de pacientes en una clínica u hospital. Permite registrar, gestionar y consultar información de pacientes, médicos, citas, fichas médicas, antecedentes, y más.

## Requisitos

- Python 3.9
- Streamlit
- SQLite

## Funcionalidades

1. **Gestión de Pacientes**
   - Registro, edición y eliminación de pacientes.
   - Consulta de información detallada de pacientes.
   - Gestión de antecedentes médicos (Enfermedades crónicas, cirugías previas, alergias, medicamentos, hábitos, tratamientos previos).

2. **Gestión de Médicos**
   - Registro, edición y eliminación de médicos.
   - Asignación de especialidades y duración de citas.

3. **Citas Médicas**
   - Creación y gestión de citas entre pacientes y médicos.
   - Actualización del estado de las citas.

4. **Ficha Médica**
   - Registro de la atención médica de cada paciente (motivo de consulta, anamnesis, observaciones).
   - Registro de signos vitales (presión arterial, temperatura, frecuencia cardíaca, peso).
   - Gestión de resultados de exámenes solicitados y prescripciones médicas.

5. **Importación/Exportación de Datos**
   - Exportación de datos de pacientes, médicos, citas y fichas médicas en formato CSV.
   - Importación de datos desde archivos CSV.

## Instalación

1. Clona este repositorio:
   
   Abre la terminal y ejecuta el siguiente comando para clonar tu repositorio en tu máquina local:
     git clone https://github.com/imontsedempsey/BaseDeDatosProyecto.git
   Este comando descargará todos los archivos de tu repositorio en una carpeta llamada BaseDeDatosProyecto.


3. Instala los requisitos necesarios:

   Navega a la carpeta de tu proyecto:
     cd BaseDeDatosProyecto
   Luego, instala todas las dependencias listadas en el archivo requirements.txt ejecutando:
     pip install -r requirements.txt
   Esto descargará e instalará las bibliotecas necesarias para ejecutar tu aplicación.


5. Corre la aplicación:
   
   Finalmente, para ejecutar tu aplicación con Streamlit, solo necesitas ejecutar el siguiente comando en la terminal:
     streamlit run app.py
   Esto abrirá la aplicación en tu navegador predeterminado, y podrás empezar a interactuar con ella.
   

## Estructura de Archivos
- app.py: Archivo principal que ejecuta la aplicación Streamlit.
- db.py: Gestión de la base de datos SQLite.
- import_export.py: Funcionalidades de importación y exportación de CSV.
- ui_pacientes.py: Interfaz de usuario para gestionar pacientes.
- ui_medicos.py: Interfaz de usuario para gestionar médicos.
- ui_citas.py: Interfaz de usuario para gestionar citas médicas.
- ui_ficha_medica.py: Interfaz de usuario para gestionar fichas médicas y resultados de exámenes.
- Validaciones.py: Funciones para validar el formato de correos y RUT

## Método de Uso
Una vez que hayas seguido los pasos de Instalación y hayas ejecutado la aplicación en tu navegador, puedes comenzar a interactuar con el sistema de gestión de pacientes a través de las siguientes funcionalidades:

   1. Gestión de Pacientes
      
      Registrar un paciente:
         Dirígete a la sección "Gestión de Pacientes".
         Haz clic en "Agregar Paciente", completa los campos requeridos (nombre, RUT, fecha de nacimiento, etc.), y guarda el registro.

      Editar un paciente:
         Encuentra al paciente en la lista de pacientes registrados.
         Haz clic en "Editar" junto al paciente que deseas modificar, realiza los cambios necesarios y guarda los cambios.

      Eliminar un paciente:
         Selecciona al paciente en la lista y haz clic en "Eliminar" para borrar su registro.

   3. Gestión de Médicos
      
      Registrar un médico:
         En la sección "Gestión de Médicos", haz clic en "Agregar Médico", llena los campos (nombre, especialidad, etc.), y guarda el registro.

      Editar un médico:
         Encuentra al médico que deseas modificar y haz clic en "Editar". Realiza los cambios y guarda.

      Eliminar un médico:
         Selecciona el médico a eliminar y haz clic en "Eliminar".

   3. Citas Médicas

      Crear una cita:
         En la sección "Citas Médicas", haz clic en "Agregar Cita". Selecciona el paciente y el médico, define la fecha y la hora de la cita, y guarda.

      Actualizar estado de la cita:
         En la lista de citas médicas, haz clic en "Actualizar Estado" para cambiar el estado de la cita (pendiente, realizada, cancelada, etc.).

   4. Ficha Médica

      Registrar atención médica:
         En la sección de "Ficha Médica", selecciona al paciente, ingresa el motivo de la consulta, la anamnesis, y las observaciones.

      Registrar signos vitales:
         En el mismo formulario de ficha médica, ingresa los signos vitales como presión arterial, temperatura, etc.

      Gestionar exámenes y prescripciones:
         Dentro de la misma ficha, puedes agregar los resultados de exámenes solicitados y registrar las prescripciones médicas.

   5. Importación y Exportación de Datos

      Exportar datos:
         Para exportar los datos de pacientes, médicos, citas o fichas médicas, dirígete a la sección correspondiente y haz clic en "Exportar". Los datos se descargarán en formato CSV.

      Importar datos:
         Para importar datos desde un archivo CSV, dirígete a la opción de "Importar Datos", selecciona el archivo CSV que deseas cargar, y haz clic en "Cargar".
      
## Notas
Este sistema utiliza SQLite como base de datos, por lo que no requiere configuración adicional. Los datos se almacenan en un archivo de base de datos SQLite llamado base.db.
