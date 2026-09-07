# Sistema de Biofeedback

Este proyecto es una aplicación web interactiva para la adquisición, visualización y análisis de datos fisiológicos en sesiones de biofeedback. Utiliza sensores conectados a Arduino (o modo demo con datos simulados) y permite asociar información demográfica y resultados de cuestionarios clínicos (Hamilton).

## Características

* Adquisición de señales ECG, temperatura y BPM en tiempo real.
* Modo demo (simulación) y modo real (Arduino).
* Interfaz web con Flask y SocketIO.
* Registro de sesiones con datos demográficos y cuestionario Hamilton.
* Almacenamiento automático de datos y resúmenes en archivos CSV/JSON.
* Identificación de cada medición por fase: Activación o Regulación.
* Separador visible en el CSV cuando la sesión cambia de Activación a Regulación.
* Gráficas de ECG, BPM y temperatura al finalizar la sesión.
* Descarga de un informe PDF con los datos principales, clasificación Hamilton y las gráficas.
* Clasificación Hamilton: 0-5 mínima, 6-14 leve-moderada, 15-23 moderada-alta y 24-28 severa.

## Estructura principal

* [app.py](app.py): Servidor web y lógica de control de sesiones.
* [BioSensorSystem.py](BioSensorSystem.py): Manejo de sensores, simulación, almacenamiento y análisis de datos.
* [sessions](sessions): Almacena los datos de cada sesión.
* [static](static) y [templates](templates): Archivos de la interfaz web.

## Documentación

La documentación del proyecto se encuentra en la carpeta [documentation](documentation):

* [Manual técnico](documentation/BioBreath_manual_tecnico.pdf): arquitectura, instalación, configuración y funcionamiento interno del sistema.
* [Manual de usuario](documentation/BioBreath_manual_usuario.pdf): instrucciones para utilizar la aplicación y completar una sesión.
* [Descripción del programa](documentation/Descripcion_programa.pdf): identificación, finalidad, funcionamiento, entradas, procesamiento y salidas del software.

## Requisitos

* Python 3.8+
* Arduino compatible con comunicación serial a 115200 baudios, si se utiliza el modo Arduino.
* Dependencias indicadas en [requirements.txt](requirements.txt), incluyendo ReportLab para generar PDF.

Con el entorno virtual activo, instala las dependencias con:

```powershell
python -m pip install -r requirements.txt
```

## Uso

1. Activa el entorno virtual en PowerShell:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Instala las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Ejecuta el servidor:

   ```powershell
   python app.py
   ```
4. Abre [http://localhost:5000](http://localhost:5000) y selecciona **Modo Demo** o **Modo Arduino**.
5. Sigue las instrucciones de la interfaz para completar la sesión.

## Archivos generados por sesión

Cada sesión crea una carpeta dentro de `sessions/` con:

* `datos_sensores.csv`: mediciones de ECG, temperatura y BPM. Incluye la fase de cada medición y una línea separadora al pasar de Activación a Regulación.
* `hamilton_pre.json`: datos demográficos y respuestas del cuestionario inicial.
* `resumen_sesion.json`: resumen estadístico y valores baseline.

Al terminar la sesión, el botón **Descargar informe PDF** genera un informe específico de esa sesión con:

* Edad y sexo del participante.
* Baseline de ECG, temperatura y BPM.
* Puntuaciones psíquica, somática y total de Hamilton.
* Clasificación del nivel de ansiedad.
* Gráficas finales de ECG, BPM y temperatura.
