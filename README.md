# Sistema de Biofeedback

Este proyecto es una aplicación web interactiva para la adquisición, visualización y análisis de datos fisiológicos en sesiones de biofeedback. Utiliza sensores conectados a Arduino (o modo demo con datos simulados) y permite asociar información demográfica y resultados de cuestionarios clínicos (Hamilton).

## Características

* Adquisición de señales ECG, temperatura y BPM en tiempo real.
* Modo demo (simulación) y modo real (Arduino).
* Interfaz web con Flask y SocketIO.
* Registro de sesiones con datos demográficos y cuestionario Hamilton.
* Almacenamiento automático de datos y resúmenes en archivos CSV/JSON.
* Visualización y exportación de resultados para análisis posteriores.

## Estructura principal

* [app.py](vscode-file://vscode-app/c:/Users/egriv/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): Servidor web y lógica de control de sesiones.
* [BioSensorSystem.py](vscode-file://vscode-app/c:/Users/egriv/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): Manejo de sensores, simulación, almacenamiento y análisis de datos.
* Carpeta [sessions](vscode-file://vscode-app/c:/Users/egriv/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): Almacena los datos de cada sesión.
* Carpeta [static](vscode-file://vscode-app/c:/Users/egriv/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html) y [templates](vscode-file://vscode-app/c:/Users/egriv/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html): Archivos para la interfaz web.

## Requisitos

* Python 3.8+
* Flask, Flask-SocketIO, numpy, scipy, pyserial

Instala dependencias con:

`pip install -r requirements.txt`

## Uso

1. Conecta el Arduino (o usa modo demo).
2. Ejecuta el servidor:

   `python app.py`
3. Abre el navegador en [http://localhost:5000](vscode-file://vscode-app/c:/Users/egriv/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
4. Sigue las instrucciones en la interfaz.
