from flask import Flask, render_template, jsonify, request, send_file, abort
from flask_socketio import SocketIO, emit
from BioSensorSystem import BioSensorSystem
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from io import BytesIO
import base64
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Variables globales
bio_system = None
is_streaming = False
current_phase = 'idle'
hamilton_pre = None
demographics_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'phase': current_phase,
        'connected': bio_system is not None
    })

@app.route('/download/session/<session_name>/pdf', methods=['POST'])
def download_session_pdf(session_name):
    """Genera un informe PDF con el resumen y las gráficas de una sesión."""
    safe_session_name = os.path.basename(session_name)

    if safe_session_name != session_name or not safe_session_name:
        abort(404)

    session_directory = os.path.join(app.root_path, 'sessions', safe_session_name)

    if not os.path.isdir(session_directory):
        abort(404)

    data = request.get_json(silent=True) or {}
    demographics = data.get('demographics') or {}
    hamilton = data.get('hamilton') or {}
    baseline = data.get('baseline') or {}
    charts = data.get('charts') or {}
    total = float(hamilton.get('total', 0))

    if total <= 5:
        anxiety_level = 'Ansiedad mínima'
    elif total <= 14:
        anxiety_level = 'Ansiedad leve-moderada'
    elif total <= 23:
        anxiety_level = 'Ansiedad moderada-alta'
    else:
        anxiety_level = 'Ansiedad severa'

    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'], alignment=TA_CENTER,
        textColor=colors.HexColor('#2C3E50'), spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'], alignment=TA_CENTER,
        textColor=colors.HexColor('#7F8C8D'), spaceAfter=18
    )
    heading_style = ParagraphStyle(
        'ReportHeading', parent=styles['Heading2'],
        textColor=colors.HexColor('#4A90E2'), spaceBefore=8, spaceAfter=8
    )

    story = [
        Paragraph('BioBreath', title_style),
        Paragraph('Resumen de sesión de biorretroalimentación', subtitle_style),
        Paragraph('Participante', heading_style),
        _pdf_table([
            ['Edad', f"{demographics.get('edad', 'No disponible')} años"],
            ['Sexo', str(demographics.get('sexo', 'No disponible')).capitalize()]
        ]),
        Spacer(1, 10),
        Paragraph('Resultados del cuestionario Hamilton', heading_style),
        _pdf_table([
            ['Ansiedad psíquica', f"{hamilton.get('psychic', 'No disponible')} / 16"],
            ['Ansiedad somática', f"{hamilton.get('somatic', 'No disponible')} / 12"],
            ['Puntuación total', f"{hamilton.get('total', 'No disponible')} / 28"],
            ['Clasificación', anxiety_level]
        ]),
        Spacer(1, 10),
        Paragraph('Valores baseline', heading_style),
        _pdf_table([
            ['Temperatura', _format_number(baseline.get('temp'), '°C', 2)],
            ['Frecuencia cardíaca', _format_number(baseline.get('bpm'), 'latidos/min', 0)],
            ['ECG', _format_number(baseline.get('ecg'), 'V', 4)]
        ]),
        Spacer(1, 12),
        Paragraph('Evolución temporal de sensores', heading_style)
    ]

    for chart_name, chart_title in [
        ('ecg', 'ECG'), ('bpm', 'Frecuencia cardíaca'), ('temperature', 'Temperatura')
    ]:
        chart_image = _pdf_image_from_data_url(charts.get(chart_name))
        if chart_image:
            story.append(Paragraph(chart_title, styles['Heading3']))
            story.append(chart_image)
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'Este informe resume los datos registrados durante la sesión y no constituye un diagnóstico clínico.',
        styles['Italic']
    ))
    document.build(story)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{safe_session_name}_informe.pdf'
    )


def _pdf_table(rows):
    table = Table(rows, colWidths=[2.25 * inch, 4.35 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def _format_number(value, suffix, decimals):
    if value is None:
        return 'No disponible'
    return f'{float(value):.{decimals}f} {suffix}'


def _pdf_image_from_data_url(data_url):
    if not data_url or ',' not in data_url:
        return None
    try:
        image_bytes = base64.b64decode(data_url.split(',', 1)[1])
        image = Image(BytesIO(image_bytes), width=6.6 * inch, height=2.25 * inch)
        image.hAlign = 'CENTER'
        return image
    except (ValueError, TypeError):
        return None

@socketio.on('connect')
def handle_connect():
    print('✓ Cliente web conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('✗ Cliente web desconectado')

@socketio.on('initialize_system')
def initialize_system(data=None):
    """Inicializar sistema de sensores"""
    global bio_system, current_phase
    
    try:
        data = data or {}
        selected_mode = data.get('mode', 'demo')
        demo_mode = selected_mode != 'arduino'
        bio_system = BioSensorSystem(demo_mode=demo_mode)
        
        if bio_system.connect():
            current_phase = "connected"
            
            if bio_system.DEMO_MODE:
                message = '🎭 Sistema inicializado en MODO DEMO (datos simulados)'
            else:
                message = '🔬 Sistema conectado con sensores Arduino'
            
            emit('system_initialized', {
                'success': True,
                'message': message
            })
        else:
            emit('system_initialized', {
                'success': False,
                'message': 'No se pudo conectar. Verifica que el dispositivo esté conectado por USB.'
            })
    except Exception as e:
        emit('system_initialized', {
            'success': False,
            'message': f'Error: {str(e)}'
        })

@socketio.on('save_hamilton_pre')
def save_hamilton_pre(data):
    """Guardar cuestionario Hamilton PRE"""
    global hamilton_pre, demographics_data
    
    hamilton_pre = data
    demographics_data = data.get('demographics', {})
    
    print(f"✓ Hamilton PRE guardado: Total={data['total']}, Edad={demographics_data.get('edad')}, Sexo={demographics_data.get('sexo')}")
    
    emit('hamilton_pre_saved', {'success': True})

@socketio.on('start_baseline')
def start_baseline(data):
    """Calcular baseline"""
    global bio_system, current_phase
    
    duration = data.get('duration', 10)
    current_phase = 'baseline'
    
    def calculate_baseline():
        try:
            baseline = bio_system.set_baseline(duration=duration)
            
            socketio.emit('baseline_complete', {
                'baseline_ecg': baseline['ecg'],
                'baseline_temp': baseline['temperature'],
                'baseline_bpm': baseline['bpm']
            })
            
            print(f"✓ Baseline calculado: ECG={baseline['ecg']:.4f}V, Temp={baseline['temperature']:.2f}°C, BPM={baseline['bpm']:.0f}")
            
        except Exception as e:
            print(f"✗ Error en baseline: {e}")
            socketio.emit('error', {'message': f'Error en baseline: {str(e)}'})
    
    thread = threading.Thread(target=calculate_baseline)
    thread.daemon = True
    thread.start()

@socketio.on('start_session')  # ← ESTA FUNCIÓN FALTABA COMPLETA
def start_session(data):
    """Iniciar grabación de sesión"""
    global bio_system, is_streaming, current_phase
    
    phase = data.get('phase', 'activation')
    current_phase = phase
    
    # Iniciar sesión con demographics y hamilton_data
    session_folder = bio_system.start_session(
        demographics=demographics_data,
        hamilton_data=hamilton_pre
    )
    
    print(f"✓ Sesión iniciada en: {session_folder}")
    
    # Iniciar streaming
    is_streaming = True  # ← ACTIVAR STREAMING
    
    emit('session_started', {
        'success': True,
        'phase': phase,
        'session_name': session_folder
    })
    
    # Thread para streaming de datos
    def stream_data():
        global is_streaming
        
        print(f"🎬 Streaming iniciado...")  # ← DEBUG
        
        while is_streaming:
            try:
                data = bio_system.read_sensor_data()
                
                if data:
                    data['phase'] = current_phase
                    bio_system.add_data_point(data)  # ← GUARDAR DATOS
                    socketio.emit('sensor_data', data)
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error en streaming: {e}")
                break
        
        print(f"🛑 Streaming detenido. Total de puntos: {len(bio_system.session_data)}")  # ← DEBUG
    
    thread = threading.Thread(target=stream_data)
    thread.daemon = True
    thread.start()

@socketio.on('stop_session')
def stop_session():
    """Detener sesión y guardar datos"""
    global bio_system, is_streaming, current_phase
    
    is_streaming = False
    current_phase = 'analysis'
    
    print(f"🔍 DEBUG - session_data tiene {len(bio_system.session_data)} puntos")  # ← DEBUG
    
    try:
        summary = bio_system.stop_session()

        session_data_for_charts = []

        if bio_system.session_data:
            step = max(1, len(bio_system.session_data) // 120)
            
            for i in range(0, len(bio_system.session_data), step):
                point = bio_system.session_data[i]
                session_data_for_charts.append({
                    'timestamp': point['timestamp'],
                    'ecg_voltage': point['ecg_voltage'],
                    'temperature': point['temperature'],
                    'ecg_change_percent': point.get('ecg_change_percent', 0),
                    'temp_change_celsius': point.get('temp_change_celsius', 0),
                    'bpm': point.get('bpm', 70),
                    'phase': point.get('phase', 'unknown')
                })
        
        print(f"🔍 DEBUG - chart_data tiene {len(session_data_for_charts)} puntos")  # ← DEBUG
        print(f"✓ Sesión detenida. Datos guardados en: {bio_system.session_folder}")
        print(f"  Enviando {len(session_data_for_charts)} puntos al navegador para gráficas")
        
        emit('session_stopped', {
            'success': True,
            'summary': summary,
            'session_name': os.path.basename(bio_system.session_folder),
            'chart_data': session_data_for_charts
        })
        
    except Exception as e:
        print(f"✗ Error al detener sesión: {e}")
        emit('session_stopped', {
            'success': False,
            'error': str(e)
        })

@socketio.on('reset_system')
def reset_system():
    """Reiniciar sistema"""
    global bio_system, is_streaming, current_phase, hamilton_pre, demographics_data
    
    is_streaming = False
    current_phase = 'idle'
    hamilton_pre = None
    demographics_data = None
    
    if bio_system:
        bio_system.serial_connection = None
    
    emit('system_reset')

@socketio.on('phase_change')
def phase_change(data):
    """Cambiar fase del protocolo"""
    global current_phase
    current_phase = data.get('phase', 'idle')
    emit('phase_changed', {'phase': current_phase})

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("=" * 75)
        print("🧠 BioBreath: Sistema de Biorretroalimentación para Reducción de Ansiedad")
        print("=" * 75)
        print("🌐 Abre tu navegador en: http://localhost:5000")
        print("📱 Desde otro dispositivo (misma red): http://TU_IP:5000")
        print("=" * 75)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)