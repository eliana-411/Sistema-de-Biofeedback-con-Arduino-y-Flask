#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRÁFICA 6: ANÁLISIS DE EFECTIVIDAD DE LA RESPIRACIÓN
Comparación Fase de Activación vs Fase de Regulación
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import glob

# Configuración
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("Set2")

print("=" * 70)
print("📊 ANÁLISIS DE EFECTIVIDAD: ACTIVACIÓN vs REGULACIÓN")
print("=" * 70)
print()

# ============================================
# PROCESAR DATOS INDIVIDUALES
# ============================================

# Como los archivos cargados tienen el mismo nombre, vamos a simular
# el procesamiento con uno de ellos como ejemplo

print("📂 Cargando datos de sensores individuales...")
df_sensores = pd.read_csv('/mnt/user-data/uploads/datos_sensores.csv')

print(f"✓ {len(df_sensores)} puntos de datos cargados")
print(f"  Duración: {len(df_sensores) * 0.1:.1f} segundos")
print()

# Dividir en fases (aproximadamente 60s = 600 puntos cada una)
total_puntos = len(df_sensores)
punto_medio = total_puntos // 2

fase_activacion = df_sensores.iloc[:punto_medio].copy()
fase_regulacion = df_sensores.iloc[punto_medio:].copy()

print(f"📊 División de fases:")
print(f"  Activación: {len(fase_activacion)} puntos ({len(fase_activacion)*0.1:.1f}s)")
print(f"  Regulación: {len(fase_regulacion)} puntos ({len(fase_regulacion)*0.1:.1f}s)")
print()

# Calcular estadísticas por fase
stats_activacion = {
    'bpm_mean': fase_activacion['bpm'].mean(),
    'bpm_std': fase_activacion['bpm'].std(),
    'bpm_max': fase_activacion['bpm'].max(),
    'temp_mean': fase_activacion['temperature'].mean(),
    'temp_std': fase_activacion['temperature'].std(),
}

stats_regulacion = {
    'bpm_mean': fase_regulacion['bpm'].mean(),
    'bpm_std': fase_regulacion['bpm'].std(),
    'bpm_max': fase_regulacion['bpm'].max(),
    'temp_mean': fase_regulacion['temperature'].mean(),
    'temp_std': fase_regulacion['temperature'].std(),
}

# Calcular cambios
delta_bpm = stats_activacion['bpm_mean'] - stats_regulacion['bpm_mean']
delta_bpm_pct = (delta_bpm / stats_activacion['bpm_mean']) * 100
delta_temp = stats_activacion['temp_mean'] - stats_regulacion['temp_mean']

print("📈 RESULTADOS DEL ANÁLISIS:")
print()
print("❤️  FRECUENCIA CARDÍACA (BPM):")
print(f"  Activación:  {stats_activacion['bpm_mean']:.2f} ± {stats_activacion['bpm_std']:.2f} bpm")
print(f"  Regulación:  {stats_regulacion['bpm_mean']:.2f} ± {stats_regulacion['bpm_std']:.2f} bpm")
print(f"  Reducción:   {delta_bpm:.2f} bpm ({delta_bpm_pct:.1f}%)")
print()
print("🌡️  TEMPERATURA (°C):")
print(f"  Activación:  {stats_activacion['temp_mean']:.2f} ± {stats_activacion['temp_std']:.2f} °C")
print(f"  Regulación:  {stats_regulacion['temp_mean']:.2f} ± {stats_regulacion['temp_std']:.2f} °C")
print(f"  Reducción:   {delta_temp:.2f} °C")
print()

# ============================================
# GRÁFICA 6: COMPARACIÓN POR FASES
# ============================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 6A: BPM Promedio por Fase
x_pos = [0, 1]
bpm_means = [stats_activacion['bpm_mean'], stats_regulacion['bpm_mean']]
bpm_stds = [stats_activacion['bpm_std'], stats_regulacion['bpm_std']]
colors = ['#e74c3c', '#2ecc71']

bars = axes[0, 0].bar(x_pos, bpm_means, yerr=bpm_stds, capsize=10,
                      color=colors, edgecolor='black', alpha=0.8, linewidth=2)
axes[0, 0].set_xticks(x_pos)
axes[0, 0].set_xticklabels(['⚡ Activación\n(Estrés)', '🧘 Regulación\n(Respiración)'], 
                            fontsize=12, fontweight='bold')
axes[0, 0].set_ylabel('BPM Promedio ± DE', fontsize=12)
axes[0, 0].set_title('A) Frecuencia Cardíaca por Fase', fontsize=14, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3, axis='y')

# Agregar valores y diferencia
for i, (bar, mean, std) in enumerate(zip(bars, bpm_means, bpm_stds)):
    axes[0, 0].text(bar.get_x() + bar.get_width()/2., mean + std + 1,
                    f'{mean:.1f}±{std:.1f}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)

# Línea de comparación
axes[0, 0].plot([0, 1], [stats_activacion['bpm_mean'], stats_regulacion['bpm_mean']], 
                'k--', alpha=0.5, linewidth=1.5)
axes[0, 0].text(0.5, (stats_activacion['bpm_mean'] + stats_regulacion['bpm_mean'])/2 + 2,
                f'↓ {delta_bpm:.1f} bpm\n({delta_bpm_pct:.1f}%)',
                ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

# 6B: Temperatura por Fase
temp_means = [stats_activacion['temp_mean'], stats_regulacion['temp_mean']]
temp_stds = [stats_activacion['temp_std'], stats_regulacion['temp_std']]

bars = axes[0, 1].bar(x_pos, temp_means, yerr=temp_stds, capsize=10,
                      color=colors, edgecolor='black', alpha=0.8, linewidth=2)
axes[0, 1].set_xticks(x_pos)
axes[0, 1].set_xticklabels(['⚡ Activación\n(Estrés)', '🧘 Regulación\n(Respiración)'], 
                            fontsize=12, fontweight='bold')
axes[0, 1].set_ylabel('Temperatura Promedio ± DE (°C)', fontsize=12)
axes[0, 1].set_title('B) Temperatura Corporal por Fase', fontsize=14, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3, axis='y')

for i, (bar, mean, std) in enumerate(zip(bars, temp_means, temp_stds)):
    axes[0, 1].text(bar.get_x() + bar.get_width()/2., mean + std + 0.02,
                    f'{mean:.2f}±{std:.2f}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)

axes[0, 1].plot([0, 1], [stats_activacion['temp_mean'], stats_regulacion['temp_mean']], 
                'k--', alpha=0.5, linewidth=1.5)
axes[0, 1].text(0.5, (stats_activacion['temp_mean'] + stats_regulacion['temp_mean'])/2 + 0.03,
                f'↓ {delta_temp:.2f} °C',
                ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

# 6C: Evolución temporal BPM (Ejemplo de un participante)
tiempo = np.arange(len(df_sensores)) * 0.1 / 60  # Convertir a minutos
axes[1, 0].plot(tiempo, df_sensores['bpm'], color='crimson', linewidth=1.5, alpha=0.8)
axes[1, 0].axvline(len(fase_activacion) * 0.1 / 60, color='red', linestyle='--', 
                    linewidth=2, label='Fin Activación / Inicio Regulación')
axes[1, 0].axhline(stats_activacion['bpm_mean'], color='orange', linestyle=':', 
                    linewidth=2, alpha=0.7, label=f'Media Activación: {stats_activacion["bpm_mean"]:.1f}')
axes[1, 0].axhline(stats_regulacion['bpm_mean'], color='green', linestyle=':', 
                    linewidth=2, alpha=0.7, label=f'Media Regulación: {stats_regulacion["bpm_mean"]:.1f}')
axes[1, 0].fill_between(tiempo[:len(fase_activacion)], 
                         df_sensores['bpm'].iloc[:len(fase_activacion)].min() - 5,
                         df_sensores['bpm'].iloc[:len(fase_activacion)].max() + 5,
                         alpha=0.1, color='red', label='Fase Activación')
axes[1, 0].fill_between(tiempo[len(fase_activacion):], 
                         df_sensores['bpm'].iloc[len(fase_activacion):].min() - 5,
                         df_sensores['bpm'].iloc[len(fase_activacion):].max() + 5,
                         alpha=0.1, color='green', label='Fase Regulación')
axes[1, 0].set_xlabel('Tiempo (minutos)', fontsize=12)
axes[1, 0].set_ylabel('BPM', fontsize=12)
axes[1, 0].set_title('C) Evolución Temporal - Frecuencia Cardíaca', fontsize=14, fontweight='bold')
axes[1, 0].legend(loc='best', fontsize=9)
axes[1, 0].grid(True, alpha=0.3)

# 6D: Evolución temporal Temperatura
axes[1, 1].plot(tiempo, df_sensores['temperature'], color='teal', linewidth=1.5, alpha=0.8)
axes[1, 1].axvline(len(fase_activacion) * 0.1 / 60, color='red', linestyle='--', 
                    linewidth=2, label='Fin Activación / Inicio Regulación')
axes[1, 1].axhline(stats_activacion['temp_mean'], color='orange', linestyle=':', 
                    linewidth=2, alpha=0.7, label=f'Media Activación: {stats_activacion["temp_mean"]:.2f}')
axes[1, 1].axhline(stats_regulacion['temp_mean'], color='green', linestyle=':', 
                    linewidth=2, alpha=0.7, label=f'Media Regulación: {stats_regulacion["temp_mean"]:.2f}')
axes[1, 1].fill_between(tiempo[:len(fase_activacion)], 
                         df_sensores['temperature'].min() - 0.2,
                         df_sensores['temperature'].max() + 0.2,
                         alpha=0.1, color='red', label='Fase Activación')
axes[1, 1].fill_between(tiempo[len(fase_activacion):], 
                         df_sensores['temperature'].min() - 0.2,
                         df_sensores['temperature'].max() + 0.2,
                         alpha=0.1, color='green', label='Fase Regulación')
axes[1, 1].set_xlabel('Tiempo (minutos)', fontsize=12)
axes[1, 1].set_ylabel('Temperatura (°C)', fontsize=12)
axes[1, 1].set_title('D) Evolución Temporal - Temperatura', fontsize=14, fontweight='bold')
axes[1, 1].legend(loc='best', fontsize=9)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/grafica6_efectividad_respiracion.png', 
            dpi=300, bbox_inches='tight')

print("=" * 70)
print("✅ GRÁFICA DE EFECTIVIDAD GENERADA")
print("=" * 70)
print("📁 Archivo guardado: grafica6_efectividad_respiracion.png")
print()

# ============================================
# TEST ESTADÍSTICO
# ============================================

print("📊 ANÁLISIS ESTADÍSTICO:")
print()

# Test t pareado (mismo participante, dos fases)
# Igualar tamaños cortando al mínimo
min_len = min(len(fase_activacion), len(fase_regulacion))
act_bpm = fase_activacion['bpm'].values[:min_len]
reg_bpm = fase_regulacion['bpm'].values[:min_len]
act_temp = fase_activacion['temperature'].values[:min_len]
reg_temp = fase_regulacion['temperature'].values[:min_len]

t_stat_bpm, p_val_bpm = stats.ttest_rel(act_bpm, reg_bpm)
print(f"❤️  BPM - Test t pareado (n={min_len}):")
print(f"   t = {t_stat_bpm:.3f}, p = {p_val_bpm:.4f}")
if p_val_bpm < 0.05:
    print(f"   ✓ Diferencia SIGNIFICATIVA (p < 0.05)")
else:
    print(f"   • Diferencia no significativa (p ≥ 0.05)")
print()

t_stat_temp, p_val_temp = stats.ttest_rel(act_temp, reg_temp)
print(f"🌡️  Temperatura - Test t pareado (n={min_len}):")
print(f"   t = {t_stat_temp:.3f}, p = {p_val_temp:.4f}")
if p_val_temp < 0.05:
    print(f"   ✓ Diferencia SIGNIFICATIVA (p < 0.05)")
else:
    print(f"   • Diferencia no significativa (p ≥ 0.05)")
print()

print("=" * 70)
print("✨ INTERPRETACIÓN:")
print("=" * 70)
if delta_bpm > 0:
    print(f"✅ La técnica de respiración 4-7-8 REDUJO el BPM en {delta_bpm:.2f} bpm")
    print(f"   (Reducción del {delta_bpm_pct:.1f}% respecto a la fase de activación)")
else:
    print(f"⚠️  El BPM NO se redujo con la técnica de respiración")

if delta_temp > 0:
    print(f"✅ La temperatura se REDUJO en {delta_temp:.2f} °C durante la regulación")
else:
    print(f"⚠️  La temperatura NO se redujo con la técnica de respiración")

print()
print("💡 NOTA: Este análisis muestra datos de UN participante como ejemplo.")
print("   Para el artículo, debes repetir este análisis para TODOS los participantes")
print("   y calcular promedios grupales con barras de error.")
print("=" * 70)
