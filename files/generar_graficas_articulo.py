#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar gráficas del artículo científico:
Sistema de Biorretroalimentación para Manejo de Ansiedad
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# ============================================
# CARGAR DATOS CONSOLIDADOS
# ============================================
print("📊 Cargando datos...")
df = pd.read_csv('/mnt/user-data/uploads/todas_las_sesiones.csv', encoding='utf-8-sig')

print(f"✓ {len(df)} participantes cargados")
print(f"  Edad: {df['edad'].min()}-{df['edad'].max()} años (Media: {df['edad'].mean():.1f})")
print(f"  Sexo: {df['sexo'].value_counts().to_dict()}")
print()

# ============================================
# GRÁFICA 1: CARACTERÍSTICAS DE LA MUESTRA
# ============================================
print("📈 Generando Gráfica 1: Características demográficas...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 1A: Distribución por edad
axes[0].hist(df['edad'], bins=8, color='steelblue', edgecolor='black', alpha=0.7)
axes[0].axvline(df['edad'].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'Media: {df["edad"].mean():.1f} años')
axes[0].set_xlabel('Edad (años)', fontsize=12)
axes[0].set_ylabel('Frecuencia', fontsize=12)
axes[0].set_title('A) Distribución por Edad', fontsize=14, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 1B: Distribución por sexo
sexo_counts = df['sexo'].value_counts()
colors = ['#3498db', '#e74c3c']
explode = (0.05, 0)
axes[1].pie(sexo_counts.values, labels=[f'{s.capitalize()}\n(n={c})' 
            for s, c in zip(sexo_counts.index, sexo_counts.values)],
            autopct='%1.1f%%', startangle=90, colors=colors, explode=explode,
            textprops={'fontsize': 12, 'fontweight': 'bold'})
axes[1].set_title('B) Distribución por Sexo', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/grafica1_caracteristicas_muestra.png', 
            dpi=300, bbox_inches='tight')
print("✓ Guardada: grafica1_caracteristicas_muestra.png\n")

# ============================================
# GRÁFICA 2: NIVELES DE ANSIEDAD (HAMILTON)
# ============================================
print("📈 Generando Gráfica 2: Niveles de ansiedad...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 2A: Distribución de niveles de ansiedad
def clasificar_ansiedad(score):
    if score <= 5:
        return 'Mínima (0-5)'
    elif score <= 14:
        return 'Leve-Moderada (6-14)'
    elif score <= 23:
        return 'Moderada-Alta (15-23)'
    else:
        return 'Severa (24-28)'

df['nivel_ansiedad'] = df['hamilton_total'].apply(clasificar_ansiedad)
nivel_counts = df['nivel_ansiedad'].value_counts().reindex([
    'Mínima (0-5)', 'Leve-Moderada (6-14)', 
    'Moderada-Alta (15-23)', 'Severa (24-28)'
], fill_value=0)

colors_ansiedad = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
bars = axes[0].bar(range(len(nivel_counts)), nivel_counts.values, 
                   color=colors_ansiedad, edgecolor='black', alpha=0.8)
axes[0].set_xticks(range(len(nivel_counts)))
axes[0].set_xticklabels(nivel_counts.index, rotation=15, ha='right')
axes[0].set_ylabel('Número de Participantes', fontsize=12)
axes[0].set_title('A) Distribución de Niveles de Ansiedad', fontsize=14, fontweight='bold')
axes[0].grid(True, alpha=0.3, axis='y')

# Agregar valores encima de las barras
for bar in bars:
    height = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontweight='bold')

# 2B: Ansiedad Psíquica vs Somática
psiquica_mean = df['hamilton_psiquica'].mean()
somatica_mean = df['hamilton_somatica'].mean()
psiquica_std = df['hamilton_psiquica'].std()
somatica_std = df['hamilton_somatica'].std()

x_pos = [0, 1]
means = [psiquica_mean, somatica_mean]
stds = [psiquica_std, somatica_std]
colors_comp = ['#9b59b6', '#3498db']

bars = axes[1].bar(x_pos, means, yerr=stds, capsize=5, 
                   color=colors_comp, edgecolor='black', alpha=0.8)
axes[1].set_xticks(x_pos)
axes[1].set_xticklabels(['Psíquica', 'Somática'], fontsize=12)
axes[1].set_ylabel('Puntuación Promedio ± DE', fontsize=12)
axes[1].set_title('B) Comparación: Ansiedad Psíquica vs Somática', 
                  fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

# Agregar valores
for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
    axes[1].text(bar.get_x() + bar.get_width()/2., mean + std + 0.3,
                f'{mean:.2f}±{std:.2f}',
                ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/grafica2_niveles_ansiedad.png', 
            dpi=300, bbox_inches='tight')
print("✓ Guardada: grafica2_niveles_ansiedad.png\n")

# ============================================
# GRÁFICA 3: VARIABLES FISIOLÓGICAS
# ============================================
print("📈 Generando Gráfica 3: Variables fisiológicas...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 3A: BPM Promedio por participante
axes[0, 0].bar(range(len(df)), df['bpm_promedio'], 
               color='crimson', edgecolor='black', alpha=0.7)
axes[0, 0].axhline(df['bpm_promedio'].mean(), color='blue', linestyle='--', 
                   linewidth=2, label=f'Media: {df["bpm_promedio"].mean():.1f} bpm')
axes[0, 0].set_xlabel('Participante', fontsize=12)
axes[0, 0].set_ylabel('BPM Promedio', fontsize=12)
axes[0, 0].set_title('A) Frecuencia Cardíaca Promedio por Participante', 
                     fontsize=13, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3, axis='y')

# 3B: Reactividad cardíaca (Máx - Mín)
df['bpm_rango'] = df['bpm_maximo'] - df['bpm_minimo']
axes[0, 1].bar(range(len(df)), df['bpm_rango'], 
               color='orange', edgecolor='black', alpha=0.7)
axes[0, 1].axhline(df['bpm_rango'].mean(), color='blue', linestyle='--', 
                   linewidth=2, label=f'Media: {df["bpm_rango"].mean():.1f} bpm')
axes[0, 1].set_xlabel('Participante', fontsize=12)
axes[0, 1].set_ylabel('Rango BPM (Máx - Mín)', fontsize=12)
axes[0, 1].set_title('B) Reactividad Cardíaca', 
                     fontsize=13, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3, axis='y')

# 3C: Temperatura promedio
axes[1, 0].bar(range(len(df)), df['temp_promedio'], 
               color='teal', edgecolor='black', alpha=0.7)
axes[1, 0].axhline(df['temp_promedio'].mean(), color='red', linestyle='--', 
                   linewidth=2, label=f'Media: {df["temp_promedio"].mean():.2f} °C')
axes[1, 0].set_xlabel('Participante', fontsize=12)
axes[1, 0].set_ylabel('Temperatura Promedio (°C)', fontsize=12)
axes[1, 0].set_title('C) Temperatura Corporal Promedio', 
                     fontsize=13, fontweight='bold')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3, axis='y')

# 3D: Cambio de temperatura (Máx - Mín)
df['temp_rango'] = df['temp_maximo'] - df['temp_minimo']
axes[1, 1].bar(range(len(df)), df['temp_rango'], 
               color='green', edgecolor='black', alpha=0.7)
axes[1, 1].axhline(df['temp_rango'].mean(), color='red', linestyle='--', 
                   linewidth=2, label=f'Media: {df["temp_rango"].mean():.2f} °C')
axes[1, 1].set_xlabel('Participante', fontsize=12)
axes[1, 1].set_ylabel('Rango Temp (Máx - Mín) °C', fontsize=12)
axes[1, 1].set_title('D) Reactividad Térmica', 
                     fontsize=13, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/grafica3_variables_fisiologicas.png', 
            dpi=300, bbox_inches='tight')
print("✓ Guardada: grafica3_variables_fisiologicas.png\n")

# ============================================
# GRÁFICA 4: CORRELACIONES
# ============================================
print("📈 Generando Gráfica 4: Correlaciones...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 4A: Hamilton Total vs BPM Promedio
axes[0, 0].scatter(df['hamilton_total'], df['bpm_promedio'], 
                   s=100, alpha=0.6, color='crimson', edgecolors='black')
# Línea de tendencia
z = np.polyfit(df['hamilton_total'], df['bpm_promedio'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['hamilton_total'].min(), df['hamilton_total'].max(), 100)
axes[0, 0].plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
# Correlación
r, p_val = stats.pearsonr(df['hamilton_total'], df['bpm_promedio'])
axes[0, 0].text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.3f}', 
                transform=axes[0, 0].transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5))
axes[0, 0].set_xlabel('Ansiedad Total (Hamilton)', fontsize=12)
axes[0, 0].set_ylabel('BPM Promedio', fontsize=12)
axes[0, 0].set_title('A) Ansiedad vs Frecuencia Cardíaca', 
                     fontsize=13, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# 4B: Hamilton Total vs Temperatura Promedio
axes[0, 1].scatter(df['hamilton_total'], df['temp_promedio'], 
                   s=100, alpha=0.6, color='teal', edgecolors='black')
z = np.polyfit(df['hamilton_total'], df['temp_promedio'], 1)
p = np.poly1d(z)
axes[0, 1].plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
r, p_val = stats.pearsonr(df['hamilton_total'], df['temp_promedio'])
axes[0, 1].text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.3f}', 
                transform=axes[0, 1].transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5))
axes[0, 1].set_xlabel('Ansiedad Total (Hamilton)', fontsize=12)
axes[0, 1].set_ylabel('Temperatura Promedio (°C)', fontsize=12)
axes[0, 1].set_title('B) Ansiedad vs Temperatura', 
                     fontsize=13, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# 4C: Hamilton Total vs Reactividad BPM
axes[1, 0].scatter(df['hamilton_total'], df['bpm_rango'], 
                   s=100, alpha=0.6, color='orange', edgecolors='black')
z = np.polyfit(df['hamilton_total'], df['bpm_rango'], 1)
p = np.poly1d(z)
axes[1, 0].plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
r, p_val = stats.pearsonr(df['hamilton_total'], df['bpm_rango'])
axes[1, 0].text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.3f}', 
                transform=axes[1, 0].transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5))
axes[1, 0].set_xlabel('Ansiedad Total (Hamilton)', fontsize=12)
axes[1, 0].set_ylabel('Reactividad BPM (Máx - Mín)', fontsize=12)
axes[1, 0].set_title('C) Ansiedad vs Reactividad Cardíaca', 
                     fontsize=13, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# 4D: Hamilton Total vs Desviación BPM
axes[1, 1].scatter(df['hamilton_total'], df['bpm_desviacion'], 
                   s=100, alpha=0.6, color='purple', edgecolors='black')
z = np.polyfit(df['hamilton_total'], df['bpm_desviacion'], 1)
p = np.poly1d(z)
axes[1, 1].plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
r, p_val = stats.pearsonr(df['hamilton_total'], df['bpm_desviacion'])
axes[1, 1].text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.3f}', 
                transform=axes[1, 1].transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5))
axes[1, 1].set_xlabel('Ansiedad Total (Hamilton)', fontsize=12)
axes[1, 1].set_ylabel('Desviación Estándar BPM', fontsize=12)
axes[1, 1].set_title('D) Ansiedad vs Variabilidad Cardíaca', 
                     fontsize=13, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/grafica4_correlaciones.png', 
            dpi=300, bbox_inches='tight')
print("✓ Guardada: grafica4_correlaciones.png\n")

# ============================================
# GRÁFICA 5: MATRIZ DE CORRELACIÓN (HEATMAP)
# ============================================
print("📈 Generando Gráfica 5: Matriz de correlación...")

variables = ['edad', 'hamilton_psiquica', 'hamilton_somatica', 'hamilton_total',
             'bpm_promedio', 'bpm_rango', 'bpm_desviacion',
             'temp_promedio', 'temp_rango', 'temp_desviacion']

labels = ['Edad', 'Ans. Psíquica', 'Ans. Somática', 'Ans. Total',
          'BPM Prom.', 'BPM Rango', 'BPM DE',
          'Temp. Prom.', 'Temp. Rango', 'Temp. DE']

corr_matrix = df[variables].corr()

fig, ax = plt.subplots(figsize=(12, 10))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            xticklabels=labels, yticklabels=labels, ax=ax)
ax.set_title('Matriz de Correlación - Variables Psicológicas y Fisiológicas', 
             fontsize=15, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('/mnt/user-data/outputs/grafica5_matriz_correlacion.png', 
            dpi=300, bbox_inches='tight')
print("✓ Guardada: grafica5_matriz_correlacion.png\n")

# ============================================
# ESTADÍSTICAS DESCRIPTIVAS
# ============================================
print("=" * 60)
print("📊 ESTADÍSTICAS DESCRIPTIVAS")
print("=" * 60)

print("\n📋 DATOS DEMOGRÁFICOS:")
print(f"  N participantes: {len(df)}")
print(f"  Edad: {df['edad'].mean():.1f} ± {df['edad'].std():.1f} años (rango: {df['edad'].min()}-{df['edad'].max()})")
print(f"  Sexo: Masculino={df[df['sexo']=='masculino'].shape[0]}, Femenino={df[df['sexo']=='femenino'].shape[0]}")

print("\n🧠 ANSIEDAD (HAMILTON):")
print(f"  Total: {df['hamilton_total'].mean():.2f} ± {df['hamilton_total'].std():.2f} (rango: {df['hamilton_total'].min()}-{df['hamilton_total'].max()})")
print(f"  Psíquica: {df['hamilton_psiquica'].mean():.2f} ± {df['hamilton_psiquica'].std():.2f}")
print(f"  Somática: {df['hamilton_somatica'].mean():.2f} ± {df['hamilton_somatica'].std():.2f}")

print("\n❤️  FRECUENCIA CARDÍACA:")
print(f"  BPM Promedio: {df['bpm_promedio'].mean():.2f} ± {df['bpm_desviacion'].mean():.2f} bpm")
print(f"  BPM Mínimo: {df['bpm_minimo'].mean():.1f} bpm")
print(f"  BPM Máximo: {df['bpm_maximo'].mean():.1f} bpm")
print(f"  Reactividad (Rango): {df['bpm_rango'].mean():.1f} ± {df['bpm_rango'].std():.1f} bpm")

print("\n🌡️  TEMPERATURA:")
print(f"  Promedio: {df['temp_promedio'].mean():.2f} ± {df['temp_promedio'].std():.2f} °C")
print(f"  Reactividad (Rango): {df['temp_rango'].mean():.2f} ± {df['temp_rango'].std():.2f} °C")

print("\n📊 CORRELACIONES SIGNIFICATIVAS:")
r_ham_bpm, p_ham_bpm = stats.pearsonr(df['hamilton_total'], df['bpm_promedio'])
print(f"  Hamilton Total vs BPM Promedio: r={r_ham_bpm:.3f}, p={p_ham_bpm:.3f}")

r_ham_temp, p_ham_temp = stats.pearsonr(df['hamilton_total'], df['temp_promedio'])
print(f"  Hamilton Total vs Temp Promedio: r={r_ham_temp:.3f}, p={p_ham_temp:.3f}")

r_ham_bpm_rango, p_ham_bpm_rango = stats.pearsonr(df['hamilton_total'], df['bpm_rango'])
print(f"  Hamilton Total vs BPM Reactividad: r={r_ham_bpm_rango:.3f}, p={p_ham_bpm_rango:.3f}")

print("\n" + "=" * 60)
print("✅ TODAS LAS GRÁFICAS GENERADAS EXITOSAMENTE")
print("=" * 60)
print("\n📁 Archivos guardados en: /mnt/user-data/outputs/")
print("  - grafica1_caracteristicas_muestra.png")
print("  - grafica2_niveles_ansiedad.png")
print("  - grafica3_variables_fisiologicas.png")
print("  - grafica4_correlaciones.png")
print("  - grafica5_matriz_correlacion.png")
