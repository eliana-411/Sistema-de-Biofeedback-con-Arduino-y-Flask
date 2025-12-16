import serial
import serial.tools.list_ports
import time
import random
import csv
import os
import json
from datetime import datetime
import numpy as np
from scipy.signal import find_peaks

class BioSensorSystem:
    def __init__(self):
        self.serial_connection = None
        self.connected = False
        self.baseline_ecg = None
        self.baseline_temp = None
        
        #! MODO DEMO - True
        #! MODO ARDUINO - False
        self.DEMO_MODE = True
        
        # Variables para cálculo de BPM
        self.ecg_window = []  # Ventana deslizante de 10 segundos
        self.last_bpm = 70    # BPM inicial por defecto
        self.bpm_history = [] # Historial para suavizar BPM
        
        # Variables de sesión
        self.session_active = False
        self.session_data = []
        self.session_folder = None
        self.demographics = None
        self.hamilton_data = None
        
    def connect(self):
        """Conecta con el Arduino o activa modo demo"""
        if self.DEMO_MODE:
            print("🎭 MODO DEMO activado - Usando datos simulados")
            self.connected = True
            return True
            
        try:
            ports = serial.tools.list_ports.comports()
            arduino_port = None
            
            for port in ports:
                if 'Arduino' in port.description or 'USB' in port.description:
                    arduino_port = port.device
                    break
            
            if arduino_port:
                self.serial_connection = serial.Serial(arduino_port, 115200, timeout=1)
                time.sleep(2)
                self.connected = True
                print(f"✓ Arduino conectado en: {arduino_port}")
                return True
            else:
                print("✗ No se encontró Arduino")
                return False
                
        except Exception as e:
            print(f"✗ Error al conectar: {e}")
            return False
    
    def calculate_bpm(self, ecg_voltage):
        """Calcula BPM a partir de la señal ECG usando detección de picos"""
        
        # Agregar nuevo valor a la ventana
        self.ecg_window.append(ecg_voltage)
        
        # Mantener ventana de 100 muestras (10 segundos a 10Hz)
        if len(self.ecg_window) > 100:
            self.ecg_window.pop(0)
        
        # Necesitamos al menos 5 segundos de datos (50 muestras)
        if len(self.ecg_window) < 50:
            return self.last_bpm
        
        try:
            # Convertir a numpy array
            signal = np.array(self.ecg_window)
            
            # Normalizar señal (z-score)
            signal_mean = np.mean(signal)
            signal_std = np.std(signal)
            
            # ← PROTECCIÓN: Si no hay variación, retornar BPM por defecto
            if signal_std == 0 or signal_std < 0.001:
                return self.last_bpm
            
            normalized_signal = (signal - signal_mean) / signal_std
            
            # Detectar picos R (latidos del corazón)
            peaks, properties = find_peaks(
                normalized_signal, 
                height=0.5,      # Ajustar si no detecta picos
                distance=6,      # Mínimo 0.6 segundos entre latidos
                prominence=0.3   # Qué tan prominente debe ser el pico
            )
            
            # Necesitamos al menos 3 picos para calcular BPM confiable
            if len(peaks) >= 3:
                # Calcular intervalos entre picos (en segundos)
                intervals = np.diff(peaks) * 0.1  # 0.1 segundos por muestra (10Hz)
                
                # ← PROTECCIÓN: Filtrar intervalos válidos
                intervals = intervals[intervals > 0]
                
                if len(intervals) == 0:
                    return self.last_bpm
                
                # Calcular BPM promedio
                avg_interval = np.mean(intervals)
                
                # ← PROTECCIÓN: Evitar división por cero
                if avg_interval == 0 or avg_interval < 0.001:
                    return self.last_bpm
                
                current_bpm = 60 / avg_interval
                
                # Filtrar valores anormales (40-180 BPM)
                if 40 <= current_bpm <= 180:
                    # Suavizar usando promedio móvil
                    self.bpm_history.append(current_bpm)
                    if len(self.bpm_history) > 5:
                        self.bpm_history.pop(0)
                    
                    smoothed_bpm = np.mean(self.bpm_history)
                    self.last_bpm = int(smoothed_bpm)
                    
                    return self.last_bpm
            
            # Si no se detectaron suficientes picos, devolver último BPM válido
            return self.last_bpm
            
        except Exception as e:
            # ← PROTECCIÓN: Si hay cualquier error, retornar BPM seguro
            print(f"⚠️ Error calculando BPM: {e}")
            return self.last_bpm
    
    def read_sensor_data(self):
        """Lee datos de sensores (reales o simulados)"""
        if not self.connected:
            return None
        
        # ← DEFINIR VARIABLES POR DEFECTO AL INICIO
        ecg_raw = 0
        ecg_voltage = 0
        temp = 0
        bpm = self.last_bpm  # ← IMPORTANTE: Inicializar BPM
        
        if self.DEMO_MODE:
            # MODO DEMO: Simular datos realistas
            base_ecg = 1.6
            base_temp = 36.5
            
            # Factor de estrés que aumenta con el tiempo
            stress_factor = min(len(self.ecg_window) / 100, 0.08)  # Hasta 8% de aumento
            
            # ECG: Simular señal con picos (latidos)
            # Crear señal de ECG sintética con latidos
            t = len(self.ecg_window) % 10  # Posición en el ciclo (0-9)
            
            # Simular complejo QRS (pico R cada ~7-8 muestras para 70-80 BPM)
            if t in [2, 3]:  # Pico R
                ecg_spike = random.uniform(0.3, 0.5)
            elif t == 4:  # Onda S
                ecg_spike = random.uniform(-0.1, 0)
            else:
                ecg_spike = random.uniform(-0.05, 0.05)
            
            ecg_raw = int((base_ecg + ecg_spike + stress_factor * 0.2) * 204.8)
            ecg_voltage = ecg_raw / 204.8
            
            # Temperatura: Sube gradualmente con estrés
            temp = base_temp + random.uniform(-0.1, 0.3) + stress_factor * 2
            
            # Calcular BPM del ECG simulado
            bpm = self.calculate_bpm(ecg_voltage)
            
        else:
            # MODO REAL: Leer del Arduino
            try:
                line = self.serial_connection.readline().decode('utf-8').strip()
                # print(f"DEBUG - Línea recibida: '{line}'")

                # ← PROTECCIÓN: Limpiar formato "DATA:XXXX" si existe
                if line.startswith('DATA:'):
                    line = line.replace('DATA:', '')
                # print(f"DEBUG - Después de limpiar: '{line}'")

                # ← PROTECCIÓN: Ignorar líneas vacías o inválidas
                if not line or ',' not in line:
                    return None
                
                values = line.split(',')
                
                # ← PROTECCIÓN: Verificar que tengamos 2 valores
                if len(values) < 4:
                    return None
                
                ecg_raw = int(values[0])
                ecg_voltage = float(values[2])
                temp = float(values[3])
                
                # Calcular BPM del ECG real
                bpm = self.calculate_bpm(ecg_voltage)
                
            except Exception as e:
                print(f"Error leyendo Arduino: {e}")
                return None
        
        # Calcular cambios respecto al baseline
        ecg_change = 0
        temp_change = 0
        
        if self.baseline_ecg is not None:
            ecg_change = ((ecg_voltage - self.baseline_ecg) / self.baseline_ecg) * 100
        
        if self.baseline_temp is not None:
            temp_change = temp - self.baseline_temp
        
        return {
            'timestamp': time.time(),
            'ecg_raw': ecg_raw,
            'ecg_voltage': ecg_voltage,
            'temperature': temp,
            'ecg_change_percent': ecg_change,
            'temp_change_celsius': temp_change,
            'bpm': bpm  # ← Ahora siempre está definido
        }
    
    def set_baseline(self, duration=10):
        """Establece valores baseline durante N segundos"""
        print(f"📊 Calculando baseline durante {duration} segundos...")
        
        ecg_values = []
        temp_values = []
        bpm_values = []
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            data = self.read_sensor_data()
            if data:
                ecg_values.append(data['ecg_voltage'])
                temp_values.append(data['temperature'])
                bpm_values.append(data['bpm'])
            time.sleep(0.1)
        
        self.baseline_ecg = sum(ecg_values) / len(ecg_values)
        self.baseline_temp = sum(temp_values) / len(temp_values)
        baseline_bpm = sum(bpm_values) / len(bpm_values)
        
        print(f"✓ Baseline ECG: {self.baseline_ecg:.4f}V")
        print(f"✓ Baseline Temperatura: {self.baseline_temp:.2f}°C")
        print(f"✓ Baseline BPM: {baseline_bpm:.0f} latidos/min")
        
        return {
            'ecg': self.baseline_ecg,
            'temperature': self.baseline_temp,
            'bpm': baseline_bpm
        }
    
    def start_session(self, demographics, hamilton_data):
        """Inicia una nueva sesión"""
        self.session_active = True
        self.session_data = []
        self.demographics = demographics
        self.hamilton_data = hamilton_data
        
        # Crear carpeta de sesión
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        edad = demographics.get('edad', 'XX')
        sexo = demographics.get('sexo', 'no_especifica')
        
        folder_name = f"{timestamp}_{edad}anos_{sexo}"
        self.session_folder = os.path.join('sessions', folder_name)
        os.makedirs(self.session_folder, exist_ok=True)
        
        # Guardar Hamilton PRE
        hamilton_file = os.path.join(self.session_folder, 'hamilton_pre.json')
        with open(hamilton_file, 'w', encoding='utf-8') as f:
            json.dump({
                'demographics': demographics,
                'responses': hamilton_data['responses'],
                'puntuaciones': {
                    'psiquica': hamilton_data['psychic'],    # ← Corregido
                    'somatica': hamilton_data['somatic'],    # ← Corregido
                    'total': hamilton_data['total']          # ← Corregido
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Sesión iniciada: {self.session_folder}")
        return self.session_folder
    
    

    def add_data_point(self, data):
        """Agrega un punto de datos a la sesión"""
        if self.session_active:
            self.session_data.append(data)
    
    def stop_session(self):
        """Detiene la sesión y guarda archivos"""
        if not self.session_active:
            return None
        
        self.session_active = False
        
        # Guardar CSV de datos de sensores
        csv_file = os.path.join(self.session_folder, 'datos_sensores.csv')
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'ecg_raw', 'ecg_voltage', 'temperature', 
                           'ecg_change_percent', 'temp_change_celsius', 'bpm'])
            
            for point in self.session_data:
                writer.writerow([
                    point['timestamp'],
                    point['ecg_raw'],
                    point['ecg_voltage'],
                    point['temperature'],
                    point['ecg_change_percent'],
                    point['temp_change_celsius'],
                    point['bpm']
                ])
        
        # Calcular resumen
        ecg_values = [p['ecg_voltage'] for p in self.session_data]
        temp_values = [p['temperature'] for p in self.session_data]
        bpm_values = [p['bpm'] for p in self.session_data]
        
        summary = {
            'duracion_segundos': len(self.session_data) * 0.1,
            'puntos_datos': len(self.session_data),
            'ecg': {
                'promedio': sum(ecg_values) / len(ecg_values),
                'minimo': min(ecg_values),
                'maximo': max(ecg_values),
                'desviacion': np.std(ecg_values)
            },
            'temperatura': {
                'promedio': sum(temp_values) / len(temp_values),
                'minimo': min(temp_values),
                'maximo': max(temp_values),
                'desviacion': np.std(temp_values)
            },
            'bpm': {
                'promedio': sum(bpm_values) / len(bpm_values),
                'minimo': min(bpm_values),
                'maximo': max(bpm_values),
                'desviacion': np.std(bpm_values)
            },
            'baseline': {
                'ecg_voltaje': self.baseline_ecg,
                'temperatura_celsius': self.baseline_temp
            }
        }
        
        # Guardar resumen
        summary_file = os.path.join(self.session_folder, 'resumen_sesion.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Agregar a CSV consolidado
        self._agregar_a_csv_consolidado(summary)
        
        print(f"✓ Sesión guardada: {self.session_folder}")
        return summary
    
    def _agregar_a_csv_consolidado(self, summary):
        """Agrega una fila al CSV consolidado con todos los datos de la sesión"""
        csv_consolidado = os.path.join('sessions', 'todas_las_sesiones.csv')
        
        # Verificar si el archivo existe para saber si escribir headers
        file_exists = os.path.exists(csv_consolidado)
        
        with open(csv_consolidado, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # Escribir headers solo si el archivo no existe
            if not file_exists:
                headers = [
                    'fecha_hora', 'carpeta_sesion',
                    'edad', 'sexo',
                    'hamilton_q1', 'hamilton_q2', 'hamilton_q3', 'hamilton_q4',
                    'hamilton_q5', 'hamilton_q6', 'hamilton_q7',
                    'hamilton_psiquica', 'hamilton_somatica', 'hamilton_total',
                    'baseline_ecg_voltaje', 'baseline_temperatura_celsius',
                    'ecg_promedio', 'ecg_minimo', 'ecg_maximo', 'ecg_desviacion',
                    'temp_promedio', 'temp_minimo', 'temp_maximo', 'temp_desviacion',
                    'bpm_promedio', 'bpm_minimo', 'bpm_maximo', 'bpm_desviacion',
                    'duracion_segundos', 'puntos_datos'
                ]
                writer.writerow(headers)
            
            # Extraer datos del hamilton_pre.json
            hamilton_file = os.path.join(self.session_folder, 'hamilton_pre.json')
            with open(hamilton_file, 'r', encoding='utf-8') as hf:
                hamilton_data = json.load(hf)
            
            # Preparar fila de datos
            fila = [
                datetime.now().strftime('%Y%m%d_%H%M%S'),
                os.path.basename(self.session_folder),
                hamilton_data['demographics']['edad'],
                hamilton_data['demographics']['sexo'],
                hamilton_data['responses']['q1'],
                hamilton_data['responses']['q2'],
                hamilton_data['responses']['q3'],
                hamilton_data['responses']['q4'],
                hamilton_data['responses']['q5'],
                hamilton_data['responses']['q6'],
                hamilton_data['responses']['q7'],
                hamilton_data['puntuaciones']['psiquica'],
                hamilton_data['puntuaciones']['somatica'],
                hamilton_data['puntuaciones']['total'],
                summary['baseline']['ecg_voltaje'],
                summary['baseline']['temperatura_celsius'],
                summary['ecg']['promedio'],
                summary['ecg']['minimo'],
                summary['ecg']['maximo'],
                summary['ecg']['desviacion'],
                summary['temperatura']['promedio'],
                summary['temperatura']['minimo'],
                summary['temperatura']['maximo'],
                summary['temperatura']['desviacion'],
                summary['bpm']['promedio'],
                summary['bpm']['minimo'],
                summary['bpm']['maximo'],
                summary['bpm']['desviacion'],
                summary['duracion_segundos'],
                summary['puntos_datos']
            ]
            
            writer.writerow(fila)
        
        print(f"✓ Datos agregados a: {csv_consolidado}")
    
    def disconnect(self):
        """Desconecta del Arduino"""
        if self.serial_connection:
            self.serial_connection.close()
        self.connected = False
        
        # Limpiar ventanas
        self.ecg_window = []
        self.bpm_history = []