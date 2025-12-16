// ========================================
// CONEXIÓN WEBSOCKET
// ========================================

const socket = io();

// Variables globales
let currentPhase = 'idle';
let baselineData = { ecg: null, temp: null };
let demographicsData = null;
let hamiltonPreData = null;
let currentGame = null;
let sessionStarted = false;

// Gráficas
let ecgChart = null;
let tempChart = null;
let bpmChart = null; 

// Juegos - Variables globales
let gameTimer = 60;
let gameInterval = null;

// Matemáticas
let mathAnswer = 0;
let mathScore = 0;

// Stroop Test
let stroopColors = ['rojo', 'azul', 'verde', 'amarillo'];
let stroopColorNames = {
    'rojo': 'red',
    'azul': 'blue',
    'verde': 'green',
    'amarillo': '#f5c842'
};
let stroopCurrentColor = '';
let stroopScore = 0;

// Memoria
let memorySequence = [];
let memoryUserSequence = [];
let memoryLevel = 1;
let memoryPlaying = false;

// ========================================
// INICIALIZACIÓN
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Sistema cargado');
    checkSystemStatus();
    setupHamiltonForms();
});

// ========================================
// WEBSOCKET EVENTS
// ========================================

socket.on('connect', function() {
    updateConnectionStatus(true);
    console.log('✓ Conectado al servidor');
});

socket.on('disconnect', function() {
    updateConnectionStatus(false);
    console.log('✗ Desconectado del servidor');
});

socket.on('system_initialized', function(data) {
    if (data.success) {
        showNotification(data.message, 'success');
        document.getElementById('initCard').style.display = 'none';
        document.getElementById('demographicsCard').style.display = 'block'; // ← CAMBIO AQUÍ
    } else {
        showNotification(data.message, 'error');
    }
});

socket.on('phase_changed', function(data) {
    currentPhase = data.phase;
    console.log(`Fase cambiada a: ${data.phase}`);
});

socket.on('baseline_complete', function(data) {
    baselineData.ecg = data.baseline_ecg;
    baselineData.temp = data.baseline_temp;
    baselineData.bpm = data.baseline_bpm;  
    
    document.getElementById('baselineProgress').style.display = 'none';
    document.getElementById('baselineResults').style.display = 'block';
    document.getElementById('baselineECG').textContent = data.baseline_ecg.toFixed(4) + ' V';
    document.getElementById('baselineBPM').textContent = data.baseline_bpm.toFixed(0) + ' latidos/min';  
    document.getElementById('baselineTemp').textContent = data.baseline_temp.toFixed(2) + ' °C';
    
    // setTimeout(() => {
    //     document.getElementById('baselineCard').style.display = 'none';
    //     document.getElementById('protocolCard').style.display = 'block';
    // }, 2000);
    
    showNotification('Baseline calculado exitosamente', 'success');
});

socket.on('session_started', function(data) {
    currentPhase = data.phase;
    document.getElementById('stopBtn').style.display = 'block';
    document.getElementById('sensorsMini').style.display = 'flex';
    showNotification(`Sesión iniciada: ${data.phase}`, 'info');
});

socket.on('sensor_data', function(data) {
    updateSensorIndicators(data);
});

socket.on('session_stopped', function(data) {
    console.log('🛑 SESSION STOPPED - Datos recibidos:', data);
    console.log('📊 chart_data:', data.chart_data);
    console.log('📏 Longitud:', data.chart_data ? data.chart_data.length : 'undefined');
    
    document.getElementById('stopBtn').style.display = 'none';
    document.getElementById('protocolCard').style.display = 'none';
    document.getElementById('gameSelection').style.display = 'none';
    document.getElementById('mathGame').style.display = 'none';
    document.getElementById('stroopGame').style.display = 'none';
    document.getElementById('memoryGame').style.display = 'none';
    document.getElementById('breathingGuide').style.display = 'none';
    
    // Ir directo a resultados 
    document.getElementById('analysisCard').style.display = 'block';
    displayFinalResults();

    // Crear gráficas con los datos de la sesión 
    console.log('🎨 Verificando chart_data...');
    console.log('  ¿Existe data.chart_data?', !!data.chart_data);
    console.log('  ¿Es array?', Array.isArray(data.chart_data));
    console.log('  ¿Tiene elementos?', data.chart_data ? data.chart_data.length > 0 : false);
    // Crear gráficas con los datos de la sesión 
    if (data.chart_data && data.chart_data.length > 0) { 
        createCharts(data.chart_data);
    } else {
        console.error('❌ NO SE CREARON GRÁFICAS - Razón:');
        if (!data.chart_data) {
            console.error('   - chart_data es undefined o null');
        } else if (!Array.isArray(data.chart_data)) {
            console.error('   - chart_data no es un array');
        } else if (data.chart_data.length === 0) {
            console.error('   - chart_data está vacío (length = 0)');
        }
    }
    
    showNotification('¡Sesión completada exitosamente! 🎉', 'success');
});

socket.on('hamilton_post_saved', function(data) {
    if (data.success) {
        document.getElementById('hamiltonPostCard').style.display = 'none';
        document.getElementById('analysisCard').style.display = 'block';
        showNotification('Cuestionario guardado', 'success');
    }
});

socket.on('system_reset', function() {
    location.reload();
});

socket.on('error', function(data) {
    showNotification(data.message, 'error');
});

// ========================================
// FUNCIONES DE CONTROL PRINCIPAL
// ========================================

function initializeSystem() {
    socket.emit('initialize_system', {});
    showNotification('Inicializando sistema...', 'info');
}

function startBaseline() {
    const duration = parseInt(document.getElementById('baselineDuration').value);
    
    document.getElementById('baselineProgress').style.display = 'block';
    document.getElementById('baselineResults').style.display = 'none';
    
    const progressBar = document.getElementById('baselineProgressBar');
    const timer = document.getElementById('baselineTimer');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += (100 / duration);
        progressBar.style.width = Math.min(progress, 100) + '%';
        
        const remaining = Math.ceil(duration - (progress * duration / 100));
        timer.textContent = `${remaining} segundos restantes...`;
        
        if (progress >= 100) {
            clearInterval(interval);
        }
    }, 1000);
    
    socket.emit('start_baseline', { duration: duration });
}

function startActivationPhase() {
    document.getElementById('protocolCard').style.display = 'none';
    document.getElementById('gameSelection').style.display = 'block';
}

function startRegulationPhase() {
    stopCurrentGame();
    
    document.getElementById('gameSelection').style.display = 'none';
    document.getElementById('mathGame').style.display = 'none';
    document.getElementById('stroopGame').style.display = 'none';
    document.getElementById('memoryGame').style.display = 'none';
    document.getElementById('protocolCard').style.display = 'none';
    
    document.getElementById('breathingGuide').style.display = 'block';
    startBreathingGuide();
    
    // socket.emit('start_session', { phase: 'regulation' });
    
    // AUTO-STOP después de 60 segundos
    setTimeout(() => {
        stopSession();
        showNotification('Demo completada! ✅', 'success');
    }, 60000);
}

function stopSession() {
    stopCurrentGame();
    socket.emit('stop_session');
}

function resetSystem() {
    socket.emit('reset_system');
}

function stopCurrentGame() {
    if (gameInterval) {
        clearInterval(gameInterval);
        gameInterval = null;
    }
}

// ========================================
// SELECCIÓN DE JUEGO
// ========================================

function selectGame(gameType) {
    currentGame = gameType;
    
    document.getElementById('gameSelection').style.display = 'none';
    if (!sessionStarted) {
        socket.emit('start_session', { phase: 'activation' });
        sessionStarted = true;
    }
    
    switch(gameType) {
        case 'math':
            startMathGame();
            break;
        case 'stroop':
            startStroopGame();
            break;
        case 'memory':
            startMemoryGame();
            break;
    }
}

// ========================================
// JUEGO 1: MATEMÁTICAS
// ========================================

function startMathGame() {
    document.getElementById('mathGame').style.display = 'block';
    
    mathScore = 0;
    gameTimer = 60;
    
    document.getElementById('mathScore').textContent = mathScore;
    document.getElementById('mathTimer').textContent = gameTimer;
    document.getElementById('mathFeedback').textContent = '';
    
    generateMathProblem();
    
    gameInterval = setInterval(() => {
        gameTimer--;
        document.getElementById('mathTimer').textContent = gameTimer;
        
        if (gameTimer <= 0) {
            clearInterval(gameInterval);
            showNotification('¡Tiempo agotado! Pasando a regulación...', 'warning');
            setTimeout(() => startRegulationPhase(), 2000);
        }
    }, 1000);
}

function generateMathProblem() {
    const operations = ['+', '-', '*'];
    const operation = operations[Math.floor(Math.random() * operations.length)];
    
    let num1 = Math.floor(Math.random() * 20) + 1;
    let num2 = Math.floor(Math.random() * 20) + 1;
    
    switch(operation) {
        case '+':
            mathAnswer = num1 + num2;
            break;
        case '-':
            if (num1 < num2) [num1, num2] = [num2, num1];
            mathAnswer = num1 - num2;
            break;
        case '*':
            num1 = Math.floor(Math.random() * 12) + 1;
            num2 = Math.floor(Math.random() * 12) + 1;
            mathAnswer = num1 * num2;
            break;
    }
    
    document.getElementById('mathQuestion').textContent = `${num1} ${operation} ${num2} = ?`;
    document.getElementById('mathAnswer').value = '';
    document.getElementById('mathAnswer').focus();
}

function checkMathAnswer() {
    const userAnswer = parseInt(document.getElementById('mathAnswer').value);
    const feedback = document.getElementById('mathFeedback');
    
    if (userAnswer === mathAnswer) {
        mathScore++;
        document.getElementById('mathScore').textContent = mathScore;
        feedback.textContent = '✓ ¡Correcto!';
        feedback.className = 'feedback-text feedback-correct';
        generateMathProblem();
    } else {
        feedback.textContent = '✗ Incorrecto';
        feedback.className = 'feedback-text feedback-incorrect';
    }
    
    setTimeout(() => {
        feedback.textContent = '';
    }, 1000);
}

// Enter key para matemáticas
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && document.getElementById('mathGame').style.display === 'block') {
        checkMathAnswer();
    }
});

// ========================================
// JUEGO 2: STROOP TEST
// ========================================

function startStroopGame() {
    document.getElementById('stroopGame').style.display = 'block';
    
    stroopScore = 0;
    gameTimer = 60;
    
    document.getElementById('stroopScore').textContent = stroopScore;
    document.getElementById('stroopTimer').textContent = gameTimer;
    document.getElementById('stroopFeedback').textContent = '';
    
    generateStroopProblem();
    
    gameInterval = setInterval(() => {
        gameTimer--;
        document.getElementById('stroopTimer').textContent = gameTimer;
        
        if (gameTimer <= 0) {
            clearInterval(gameInterval);
            showNotification('¡Tiempo agotado! Pasando a regulación...', 'warning');
            setTimeout(() => startRegulationPhase(), 2000);
        }
    }, 1000);
}

function generateStroopProblem() {
    // Palabra que dice (texto)
    const wordText = stroopColors[Math.floor(Math.random() * stroopColors.length)];
    
    // Color en que está escrita (diferente al texto)
    let wordColor;
    do {
        wordColor = stroopColors[Math.floor(Math.random() * stroopColors.length)];
    } while (wordColor === wordText);
    
    stroopCurrentColor = wordColor;
    
    const wordElement = document.getElementById('stroopWord');
    wordElement.textContent = wordText.toUpperCase();
    wordElement.style.color = stroopColorNames[wordColor];
}

function checkStroopAnswer(answer) {
    const feedback = document.getElementById('stroopFeedback');
    
    if (answer === stroopCurrentColor) {
        stroopScore++;
        document.getElementById('stroopScore').textContent = stroopScore;
        feedback.textContent = '✓ ¡Correcto!';
        feedback.className = 'feedback-text feedback-correct';
        generateStroopProblem();
    } else {
        feedback.textContent = '✗ Incorrecto';
        feedback.className = 'feedback-text feedback-incorrect';
    }
    
    setTimeout(() => {
        feedback.textContent = '';
    }, 800);
}

// ========================================
// JUEGO 3: MEMORIA (SIMON SAYS)
// ========================================

function startMemoryGame() {
    document.getElementById('memoryGame').style.display = 'block';
    
    memoryLevel = 1;
    gameTimer = 60;
    memorySequence = [];
    memoryUserSequence = [];
    
    document.getElementById('memoryLevel').textContent = memoryLevel;
    document.getElementById('memoryTimer').textContent = gameTimer;
    document.getElementById('memoryFeedback').textContent = '';
    
    gameInterval = setInterval(() => {
        gameTimer--;
        document.getElementById('memoryTimer').textContent = gameTimer;
        
        if (gameTimer <= 0) {
            clearInterval(gameInterval);
            showNotification('¡Tiempo agotado! Pasando a regulación...', 'warning');
            setTimeout(() => startRegulationPhase(), 2000);
        }
    }, 1000);
    
    generateMemorySequence();
}

function generateMemorySequence() {
    memoryPlaying = true;
    memoryUserSequence = [];
    
    const colors = ['red', 'blue', 'green', 'yellow'];
    const newColor = colors[Math.floor(Math.random() * colors.length)];
    memorySequence.push(newColor);
    
    document.getElementById('memoryStatus').textContent = 'Observa la secuencia...';
    
    // Deshabilitar botones durante reproducción
    disableMemoryButtons(true);
    
    // Reproducir secuencia
    playMemorySequence();
}

function playMemorySequence() {
    let index = 0;
    
    const interval = setInterval(() => {
        if (index < memorySequence.length) {
            flashMemoryButton(memorySequence[index]);
            index++;
        } else {
            clearInterval(interval);
            memoryPlaying = false;
            document.getElementById('memoryStatus').textContent = '¡Tu turno! Repite la secuencia';
            disableMemoryButtons(false);
        }
    }, 800);
}

function flashMemoryButton(color) {
    const button = document.querySelector(`.memory-btn-${color}`);
    button.classList.add('active');
    
    setTimeout(() => {
        button.classList.remove('active');
    }, 400);
}

function memoryClick(color) {
    if (memoryPlaying) return;
    
    flashMemoryButton(color);
    memoryUserSequence.push(color);
    
    const currentIndex = memoryUserSequence.length - 1;
    
    if (memoryUserSequence[currentIndex] !== memorySequence[currentIndex]) {
        // Error
        document.getElementById('memoryFeedback').textContent = '✗ Error! Intenta de nuevo';
        document.getElementById('memoryFeedback').className = 'feedback-text feedback-incorrect';
        
        setTimeout(() => {
            memorySequence = [];
            memoryLevel = Math.max(1, memoryLevel - 1);
            document.getElementById('memoryLevel').textContent = memoryLevel;
            document.getElementById('memoryFeedback').textContent = '';
            generateMemorySequence();
        }, 1500);
        
    } else if (memoryUserSequence.length === memorySequence.length) {
        // Completó la secuencia correctamente
        memoryLevel++;
        document.getElementById('memoryLevel').textContent = memoryLevel;
        document.getElementById('memoryFeedback').textContent = '✓ ¡Excelente!';
        document.getElementById('memoryFeedback').className = 'feedback-text feedback-correct';
        
        setTimeout(() => {
            document.getElementById('memoryFeedback').textContent = '';
            generateMemorySequence();
        }, 1000);
    }
}

function disableMemoryButtons(disabled) {
    const buttons = document.querySelectorAll('.memory-btn');
    buttons.forEach(btn => {
        btn.style.pointerEvents = disabled ? 'none' : 'auto';
        btn.style.opacity = disabled ? '0.6' : '1';
    });
}

// ========================================
// GUÍA DE RESPIRACIÓN
// ========================================

function startBreathingGuide() {
    const phases = [
        { text: 'Inhala profundamente...', duration: 4000, scale: 1.5 },
        { text: 'Mantén el aire...', duration: 7000, scale: 1.5 },
        { text: 'Exhala lentamente...', duration: 8000, scale: 1.0 }
    ];
    
    let index = 0;
    
    function updateText() {
        const breathingText = document.getElementById('breathingText');
        const breathingCircle = document.getElementById('breathingCircle');
        
        breathingText.textContent = phases[index].text;
        
        // Animar el círculo
        breathingCircle.style.transition = `transform ${phases[index].duration}ms ease-in-out`;
        breathingCircle.style.transform = `scale(${phases[index].scale})`;
        
        setTimeout(() => {
            index = (index + 1) % phases.length;
            if (document.getElementById('breathingGuide').style.display === 'block') {
                updateText();
            }
        }, phases[index].duration);
    }
    
    updateText();
}

// ========================================
// INDICADORES DE SENSORES
// ========================================

function updateSensorIndicators(data) {
    const ecgValue = data.ecg_voltage;
    const ecgChange = data.ecg_change_percent || 0;
    
    document.getElementById('ecgValue').textContent = ecgValue.toFixed(3) + 'V';
    
    const ecgBattery = document.getElementById('ecgBattery');
    const ecgPercent = Math.min(Math.abs(ecgChange) * 5, 100);
    ecgBattery.style.width = ecgPercent + '%';
    
    if (ecgPercent < 30) {
        ecgBattery.style.background = '#7ED321';
    } else if (ecgPercent < 70) {
        ecgBattery.style.background = '#F5A623';
    } else {
        ecgBattery.style.background = '#D0021B';
    }
    
    const tempValue = data.temperature;
    const tempChange = data.temp_change_celsius || 0;
    
    document.getElementById('tempValue').textContent = tempValue.toFixed(1) + '°C';
    
    const tempBattery = document.getElementById('tempBattery');
    const tempPercent = Math.min(Math.abs(tempChange) * 20, 100);
    tempBattery.style.width = tempPercent + '%';
    
    if (tempPercent < 30) {
        tempBattery.style.background = '#7ED321';
    } else if (tempPercent < 70) {
        tempBattery.style.background = '#F5A623';
    } else {
        tempBattery.style.background = '#D0021B';
    }
}

// ========================================
// FORMULARIOS HAMILTON
// ========================================

function setupHamiltonForms() {
    // Formulario de datos demográficos
    const demographicsForm = document.getElementById('demographicsForm');
    if (demographicsForm) {
        demographicsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const age = document.getElementById('participantAge').value;
            const sex = document.querySelector('input[name="sex"]:checked');
            
            if (!sex) {
                showNotification('Por favor selecciona tu sexo', 'error');
                return;
            }
            
            demographicsData = {
                edad: parseInt(age),
                sexo: sex.value
            };
            
            // Pasar a Hamilton PRE
            document.getElementById('demographicsCard').style.display = 'none';
            document.getElementById('hamiltonPreCard').style.display = 'block';
        });
    }
    
    // Hamilton PRE (7 preguntas)
    const formPre = document.getElementById('hamiltonPreForm');
    if (formPre) {
        formPre.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const responses = {};
            for (let i = 1; i <= 7; i++) { // ← CAMBIO: ahora son 7 preguntas
                const value = document.querySelector(`input[name="q${i}"]:checked`);
                if (!value) {
                    showNotification(`Por favor responde la pregunta ${i}`, 'error');
                    return;
                }
                responses[`q${i}`] = parseInt(value.value);
            }
            
            // Calcular puntuaciones según nueva agrupación
            const psychic = responses.q1 + responses.q3 + responses.q4 + responses.q7; // Ítems 1, 3, 4, 7
            const somatic = responses.q2 + responses.q5 + responses.q6; // Ítems 2, 5, 6
            const total = psychic + somatic;
            
            const hamiltonData = {
                responses: responses,
                psychic: psychic,
                somatic: somatic,
                total: total,
                demographics: demographicsData // ← INCLUIR DATOS DEMOGRÁFICOS
            };
            hamiltonPreData = hamiltonData;
            socket.emit('save_hamilton_pre', hamiltonData);
            
            
            // Pasar a baseline
            document.getElementById('hamiltonPreCard').style.display = 'none';
            document.getElementById('baselineCard').style.display = 'block';
        });
    }
}

// ========================================
// UTILIDADES
// ========================================

function updateConnectionStatus(connected) {
    const dot = document.querySelector('.status-indicator .dot');
    const text = document.getElementById('statusText');
    
    if (connected) {
        dot.classList.remove('disconnected');
        dot.classList.add('connected');
        text.textContent = 'Conectado';
    } else {
        dot.classList.remove('connected');
        dot.classList.add('disconnected');
        text.textContent = 'Desconectado';
    }
}

function showNotification(message, type) {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#7ED321' : type === 'error' ? '#D0021B' : type === 'warning' ? '#F5A623' : '#4A90E2'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function checkSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            console.log('Estado del sistema:', data);
        })
        .catch(error => {
            console.error('Error verificando estado:', error);
        });
}

// ========================================
// MOSTRAR RESULTADOS FINALES
// ========================================

// ========================================
// MOSTRAR RESULTADOS FINALES
// ========================================

function displayFinalResults() {
    console.log('Mostrando resultados...');
    console.log('Demographics:', demographicsData);
    console.log('Hamilton PRE:', hamiltonPreData);
    console.log('Baseline:', baselineData);
    
    // Mostrar Hamilton en la tabla
    document.getElementById('hamiltonPsychicDisplay').textContent = hamiltonPreData.psychic;
    document.getElementById('hamiltonSomaticDisplay').textContent = hamiltonPreData.somatic;
    document.getElementById('hamiltonTotalDisplay').textContent = hamiltonPreData.total;
    
    // Determinar nivel de ansiedad
    let anxietyLevel = '';
    let anxietyColor = '';
    
    if (hamiltonPreData.total <= 7) {
        anxietyLevel = '✅ Ansiedad Mínima';
        anxietyColor = '#7ED321';
    } else if (hamiltonPreData.total <= 14) {
        anxietyLevel = '⚠️ Ansiedad Leve-Moderada';
        anxietyColor = '#F5A623';
    } else if (hamiltonPreData.total <= 21) {
        anxietyLevel = '⚠️ Ansiedad Moderada-Alta';
        anxietyColor = '#FF6B6B';
    } else {
        anxietyLevel = '🔴 Ansiedad Severa';
        anxietyColor = '#D0021B';
    }
    
    const anxietyDisplay = document.getElementById('anxietyLevelDisplay');
    anxietyDisplay.textContent = anxietyLevel;
    anxietyDisplay.style.background = anxietyColor + '20';
    anxietyDisplay.style.borderLeft = `5px solid ${anxietyColor}`;
    anxietyDisplay.style.color = anxietyColor;
    
    // Mostrar indicadores fisiológicos
    const resultsSection = document.getElementById('physiologicalResults');
    resultsSection.innerHTML = `
        <div style="margin-bottom: 15px;">
            <p><strong>👤 Participante:</strong></p>
            <p style="margin-left: 15px;">• Edad: ${demographicsData.edad} años</p>
            <p style="margin-left: 15px;">• Sexo: ${demographicsData.sexo}</p>
        </div>
        
        <div style="margin-top: 20px;">
            <p><strong>🩺 Valores Baseline:</strong></p>
            <p style="margin-left: 15px;">• ECG: <strong style="color: var(--primary);">${baselineData.ecg ? baselineData.ecg.toFixed(4) + ' V' : 'No disponible'}</strong></p>
            <p style="margin-left: 15px;">• Temperatura: <strong style="color: var(--primary);">${baselineData.temp ? baselineData.temp.toFixed(2) + ' °C' : 'No disponible'}</strong></p>
        </div>
        
        <p style="margin-top: 20px; padding: 12px; background: #ECF0F1; border-radius: 8px; font-size: 0.9em; color: #7F8C8D;">
            📁 Datos completos guardados en el archivo de sesión
        </p>
    `;
}

// ========================================
// GRÁFICAS
// ========================================

function createCharts(chartData) {
    console.log('Creando gráficas con', chartData.length, 'puntos de datos');
    
    // Destruir gráficas anteriores si existen
    if (ecgChart) {
        ecgChart.destroy();
        ecgChart = null;
    }
    if (tempChart) {
        tempChart.destroy();
        tempChart = null;
    }
    if (bpmChart) {
        bpmChart.destroy();
        bpmChart = null;
    }
    
    if (!chartData || chartData.length === 0) {
        console.error('No hay datos para graficar');
        return;
    }
    
    // Calcular valores baseline (primer punto)
    const baselineECG = chartData[0].ecg_voltage;
    const baselineTemp = chartData[0].temperature;
    const baselineBPM = chartData[0].bpm;
    
    console.log('Baselines:', { ecg: baselineECG, temp: baselineTemp, bpm: baselineBPM });
    
    // Calcular punto medio (separador activación/regulación)
    const activationEndIndex = Math.floor(chartData.length / 2);
    
    // Plugin personalizado para línea separadora
    const separatorLinePlugin = {
        id: 'separatorLine',
        afterDraw: (chart) => {
            const ctx = chart.ctx;
            const xAxis = chart.scales.x;
            const yAxis = chart.scales.y;
            
            const xPos = xAxis.getPixelForValue(activationEndIndex);
            
            // Línea vertical roja punteada
            ctx.save();
            ctx.strokeStyle = '#FF4444';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(xPos, yAxis.top);
            ctx.lineTo(xPos, yAxis.bottom);
            ctx.stroke();
            ctx.restore();
            
            // Etiquetas de fases
            ctx.save();
            ctx.font = 'bold 12px Arial';
            ctx.fillStyle = '#FF8C00';
            ctx.fillText('⚡ ACTIVACIÓN', xPos - 100, yAxis.top + 20);
            ctx.fillStyle = '#00CED1';
            ctx.fillText('🧘 REGULACIÓN', xPos + 10, yAxis.top + 20);
            ctx.restore();
        }
    };
    
    // ===== GRÁFICA 1: ECG (VOLTAJE) =====
    const ctxECG = document.getElementById('ecgChart').getContext('2d');
    ecgChart = new Chart(ctxECG, {
        type: 'line',
        data: {
            labels: chartData.map((_, i) => (i * 0.1).toFixed(1)),
            datasets: [
                // Datos reales ECG
                {
                    label: 'ECG (Voltaje)',
                    data: chartData.map(d => d.ecg_voltage),
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    borderWidth: 3,
                    pointRadius: 0,
                    tension: 0.2,
                    order: 1
                },
                // Línea baseline
                {
                    label: 'Baseline',
                    data: Array(chartData.length).fill(baselineECG),
                    borderColor: '#4CAF50',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    order: 0
                },
                // Zona Normal (verde)
                {
                    label: 'Zona Normal',
                    data: Array(chartData.length).fill(baselineECG + 0.05),
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    borderWidth: 0,
                    fill: '+1',
                    pointRadius: 0,
                    order: 2
                },
                {
                    label: '',
                    data: Array(chartData.length).fill(baselineECG - 0.05),
                    backgroundColor: 'transparent',
                    borderWidth: 0,
                    pointRadius: 0,
                    order: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: '📊 Señal ECG (Voltaje)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: { 
                    display: true, 
                    position: 'top',
                    labels: {
                        filter: (item) => item.text !== ''
                    }
                },
                tooltip: {
                    mode: 'index',
                    callbacks: {
                        title: (items) => `Tiempo: ${items[0].label}s`
                    }
                }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Tiempo (segundos)' },
                    ticks: { maxTicksLimit: 10 }
                },
                y: { 
                    title: { display: true, text: 'Voltaje (V)' },
                    min: baselineECG - 0.15,
                    max: baselineECG + 0.15
                }
            }
        },
        plugins: [separatorLinePlugin]
    });
    
    // ===== GRÁFICA 2: BPM =====
    const ctxBPM = document.getElementById('bpmChart').getContext('2d');
    bpmChart = new Chart(ctxBPM, {
        type: 'line',
        data: {
            labels: chartData.map((_, i) => (i * 0.1).toFixed(1)),
            datasets: [
                // Datos reales BPM
                {
                    label: 'Frecuencia Cardíaca (BPM)',
                    data: chartData.map(d => d.bpm),
                    borderColor: '#E91E63',
                    backgroundColor: 'rgba(233, 30, 99, 0.1)',
                    borderWidth: 3,
                    pointRadius: 0,
                    tension: 0.3,
                    order: 1
                },
                // Línea baseline
                {
                    label: 'Baseline',
                    data: Array(chartData.length).fill(baselineBPM),
                    borderColor: '#4CAF50',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    order: 0
                },
                // Zona Normal (60-80)
                {
                    label: 'Zona Normal (60-80)',
                    data: Array(chartData.length).fill(80),
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    borderWidth: 0,
                    fill: '+1',
                    pointRadius: 0,
                    order: 2
                },
                {
                    label: '',
                    data: Array(chartData.length).fill(60),
                    backgroundColor: 'transparent',
                    borderWidth: 0,
                    pointRadius: 0,
                    order: 3
                },
                // Zona Moderada (80-100)
                {
                    label: 'Zona Moderada (80-100)',
                    data: Array(chartData.length).fill(100),
                    backgroundColor: 'rgba(255, 193, 7, 0.15)',
                    borderWidth: 0,
                    fill: '-1',
                    pointRadius: 0,
                    order: 4
                },
                // Zona Alta (100+)
                {
                    label: 'Zona Alta (100+)',
                    data: Array(chartData.length).fill(120),
                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                    borderWidth: 0,
                    fill: '-1',
                    pointRadius: 0,
                    order: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: '❤️ Frecuencia Cardíaca (BPM)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: { 
                    display: true, 
                    position: 'top',
                    labels: {
                        filter: (item) => item.text !== ''
                    }
                },
                tooltip: {
                    mode: 'index',
                    callbacks: {
                        title: (items) => `Tiempo: ${items[0].label}s`
                    }
                }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Tiempo (segundos)' },
                    ticks: { maxTicksLimit: 10 }
                },
                y: { 
                    title: { display: true, text: 'Latidos por Minuto' },
                    min: 50,
                    max: 120,
                    ticks: { stepSize: 10 }
                }
            }
        },
        plugins: [separatorLinePlugin]
    });
    
    // ===== GRÁFICA 3: TEMPERATURA =====
    const ctxTemp = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(ctxTemp, {
        type: 'line',
        data: {
            labels: chartData.map((_, i) => (i * 0.1).toFixed(1)),
            datasets: [
                // Datos reales Temperatura
                {
                    label: 'Temperatura (°C)',
                    data: chartData.map(d => d.temperature),
                    borderColor: '#FF5722',
                    backgroundColor: 'rgba(255, 87, 34, 0.1)',
                    borderWidth: 3,
                    pointRadius: 0,
                    tension: 0.2,
                    order: 1
                },
                // Línea baseline
                {
                    label: 'Baseline',
                    data: Array(chartData.length).fill(baselineTemp),
                    borderColor: '#4CAF50',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    order: 0
                },
                // Zona Normal
                {
                    label: 'Zona Normal',
                    data: Array(chartData.length).fill(baselineTemp + 0.3),
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    borderWidth: 0,
                    fill: '+1',
                    pointRadius: 0,
                    order: 2
                },
                {
                    label: '',
                    data: Array(chartData.length).fill(baselineTemp - 0.3),
                    backgroundColor: 'transparent',
                    borderWidth: 0,
                    pointRadius: 0,
                    order: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: '🌡️ Temperatura Corporal',
                    font: { size: 16, weight: 'bold' }
                },
                legend: { 
                    display: true, 
                    position: 'top',
                    labels: {
                        filter: (item) => item.text !== ''
                    }
                },
                tooltip: {
                    mode: 'index',
                    callbacks: {
                        title: (items) => `Tiempo: ${items[0].label}s`
                    }
                }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Tiempo (segundos)' },
                    ticks: { maxTicksLimit: 10 }
                },
                y: { 
                    title: { display: true, text: 'Temperatura (°C)' },
                    min: baselineTemp - 1,
                    max: baselineTemp + 1.5
                }
            }
        },
        plugins: [separatorLinePlugin]
    });
    
    console.log('✓ Gráficas creadas exitosamente');
}

// Animaciones CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);