from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from BioSensorSystem import BioSensorSystem
import threading
import time

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
        bio_system = BioSensorSystem()
        
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
                    'bpm': point.get('bpm', 70)
                })
        
        print(f"🔍 DEBUG - chart_data tiene {len(session_data_for_charts)} puntos")  # ← DEBUG
        print(f"✓ Sesión detenida. Datos guardados en: {bio_system.session_folder}")
        print(f"  Enviando {len(session_data_for_charts)} puntos al navegador para gráficas")
        
        emit('session_stopped', {
            'success': True,
            'summary': summary,
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
    print("=" * 60)
    print("🧠 Sistema de Biorretroalimentación - Servidor Web")
    print("=" * 60)
    print("🌐 Abre tu navegador en: http://localhost:5000")
    print("📱 Desde otro dispositivo (misma red): http://TU_IP:5000")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)