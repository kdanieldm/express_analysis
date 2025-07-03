import streamlit as st
import pandas as pd
import os
from datetime import datetime
import shutil
from pathlib import Path
import re
import hashlib
import json
import plotly.express as px
import subprocess
import pickle

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Chips Express",
    page_icon="📊",
    layout="wide"
)

# Crear directorios necesarios si no existen
BASE_DIR = Path(".")  # Directorio actual
DETALLE_DIR = BASE_DIR / "Detalle"
RESULTADOS_DIR = BASE_DIR / "Resultados"
HISTORICO_DIR = BASE_DIR / "Detalle historico"
TEMP_DIR = BASE_DIR / "Temp"

for directory in [DETALLE_DIR, RESULTADOS_DIR, HISTORICO_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def guardar_en_git(ruta_archivo, mensaje_commit):
    """
    Función que guarda archivos y los añade a Git automáticamente.
    
    Args:
        ruta_archivo (Path): Ruta del archivo a guardar
        mensaje_commit (str): Mensaje para el commit
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Verificar que el archivo existe
        if not ruta_archivo.exists():
            st.error(f"❌ El archivo no existe: {ruta_archivo}")
            return False
        
        # Intentar añadir el archivo a Git
        try:
            # Añadir el archivo al staging area
            result = subprocess.run(
                ['git', 'add', str(ruta_archivo)],
                capture_output=True,
                text=True,
                cwd=BASE_DIR
            )
            
            if result.returncode == 0:
                # Hacer commit del archivo
                commit_result = subprocess.run(
                    ['git', 'commit', '-m', mensaje_commit],
                    capture_output=True,
                    text=True,
                    cwd=BASE_DIR
                )
                
                if commit_result.returncode == 0:
                    st.success(f"✅ Archivo guardado y añadido a Git: {ruta_archivo.name}")
                    return True
                else:
                    st.warning(f"⚠️ Archivo guardado pero no se pudo hacer commit: {commit_result.stderr}")
                    return True
            else:
                st.warning(f"⚠️ Archivo guardado pero no se pudo añadir a Git: {result.stderr}")
                return True
                
        except FileNotFoundError:
            # Git no está disponible, solo guardar localmente
            st.success(f"✅ Archivo guardado localmente: {ruta_archivo.name}")
            return True
            
    except Exception as e:
        st.error(f"❌ Error al guardar archivo: {str(e)}")
        return False

def guardar_datos_persistentes(clave, datos):
    """
    Guarda datos en un archivo pickle para persistencia local.
    
    Args:
        clave (str): Clave para identificar los datos
        datos: Datos a guardar
    """
    try:
        archivo_persistencia = TEMP_DIR / f"{clave}_datos.pkl"
        with open(archivo_persistencia, 'wb') as f:
            pickle.dump(datos, f)
        # No mostrar mensaje de éxito para evitar interferencias
    except Exception as e:
        st.warning(f"⚠️ No se pudieron guardar los datos: {str(e)}")

def cargar_datos_persistentes(clave):
    """
    Carga datos desde un archivo pickle local.
    
    Args:
        clave (str): Clave para identificar los datos
        
    Returns:
        Los datos cargados o None si no existen
    """
    try:
        archivo_persistencia = TEMP_DIR / f"{clave}_datos.pkl"
        if archivo_persistencia.exists():
            with open(archivo_persistencia, 'rb') as f:
                datos = pickle.load(f)
                st.success(f"✅ Datos cargados localmente: {clave}")
                return datos
        else:
            st.info(f"ℹ️ No hay datos guardados para: {clave}")
            return None
    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar los datos: {str(e)}")
        return None

def analizar_archivos_pagados():
    resultados = []
    evaluaciones_detalle = []
    
    for archivo in os.listdir(RESULTADOS_DIR):
        if archivo.endswith('.xlsx') and 'PAGADO' in archivo and not archivo.startswith('~$'):
            try:
                # Leer el archivo
                df = pd.read_excel(RESULTADOS_DIR / archivo)
                
                # Verificar si las columnas necesarias existen
                if 'Fecha Primera Recarga' not in df.columns:
                    st.warning(f"Columna 'Fecha Primera Recarga' no encontrada en {archivo}")
                    continue
                    
                if 'Evaluación' not in df.columns:
                    st.warning(f"Columna 'Evaluación' no encontrada en {archivo}")
                    continue
                
                # Convertir la columna de fecha a datetime
                df['Fecha Primera Recarga'] = pd.to_datetime(df['Fecha Primera Recarga'])
                
                # Contar evaluaciones
                evaluaciones = df['Evaluación'].value_counts()
                
                # Contar evaluaciones con los valores correctos
                primera_eval = evaluaciones.get('1ra evaluación', 0)
                segunda_eval = evaluaciones.get('2da evaluación', 0)
                tercera_eval = evaluaciones.get('3ra evaluación', 0)
                cuarta_eval = evaluaciones.get('4ta evaluación', 0)
                otras_eval = segunda_eval + tercera_eval + cuarta_eval
                
                # Calcular comisiones (cada línea vale $25)
                comision_primera = primera_eval * 25
                comision_otras = otras_eval * 25
                
                # Usar la fecha más reciente del archivo
                fecha_archivo = df['Fecha Primera Recarga'].max()
                
                resultados.append({
                    'fecha': fecha_archivo,
                    'archivo': archivo,
                    'primera_eval': primera_eval,
                    'segunda_eval': segunda_eval,
                    'tercera_eval': tercera_eval,
                    'cuarta_eval': cuarta_eval,
                    'otras_eval': otras_eval,
                    'comision_primera': comision_primera,
                    'comision_otras': comision_otras
                })
                
                # Guardar detalle de evaluaciones para el funnel
                evaluaciones_detalle.append({
                    'fecha': fecha_archivo,
                    'primera': primera_eval,
                    'segunda': segunda_eval,
                    'tercera': tercera_eval,
                    'cuarta': cuarta_eval
                })
                
            except Exception as e:
                st.warning(f"Error al procesar {archivo}: {str(e)}")
                continue
    
    if not resultados:
        return pd.DataFrame(), pd.DataFrame()
    
    return pd.DataFrame(resultados).sort_values('fecha', ascending=False), pd.DataFrame(evaluaciones_detalle).sort_values('fecha', ascending=False)

def calcular_tasa_conversion_wicho():
    """
    Calcula la tasa de conversión desde el archivo Wicho hasta la primera evaluación.
    
    Returns:
        dict: Diccionario con información de conversión
    """
    try:
        # Leer el archivo Wicho
        archivo_wicho = TEMP_DIR / "CHIPS RUTA JL CABRERA WICHO.xlsx"
        if not archivo_wicho.exists():
            return None
            
        dataframes_wicho = pd.read_excel(archivo_wicho, sheet_name=None)
        
        # Contar total de líneas en el archivo Wicho
        total_lineas_wicho = 0
        for nombre_hoja, df_wicho in dataframes_wicho.items():
            if 'CEL' in df_wicho.columns:
                total_lineas_wicho += len(df_wicho)
        
        # Obtener total de líneas en primera evaluación de archivos pagados
        df_analisis, _ = analizar_archivos_pagados()
        if df_analisis.empty:
            return None
            
        total_primera_eval = df_analisis['primera_eval'].sum()
        
        # Calcular tasa de conversión
        tasa_conversion = (total_primera_eval / total_lineas_wicho * 100) if total_lineas_wicho > 0 else 0
        
        return {
            'total_lineas_wicho': total_lineas_wicho,
            'total_primera_eval': total_primera_eval,
            'tasa_conversion': tasa_conversion
        }
        
    except Exception as e:
        return None

def mostrar_analisis_pagados():
    st.header("Análisis de Comisiones Pagadas")
    
    df_analisis, df_funnel = analizar_archivos_pagados()
    
    if df_analisis.empty:
        st.warning("No hay archivos pagados para analizar")
        return
    
    # Calcular tasa de conversión desde Wicho
    conversion_wicho = calcular_tasa_conversion_wicho()
    
    # Métricas principales con estilo mejorado
    st.markdown("### 📊 Métricas Principales")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_primera = df_analisis['primera_eval'].sum()
        st.metric(
            "Total 1ra Evaluación",
            f"{total_primera:,}",
            help="Número total de líneas en primera evaluación"
        )
    
    with col2:
        total_otras = df_analisis['otras_eval'].sum()
        st.metric(
            "Total Otras Evaluaciones",
            f"{total_otras:,}",
            help="Número total de líneas en otras evaluaciones"
        )
    
    with col3:
        total_comision_primera = df_analisis['comision_primera'].sum()
        st.metric(
            "Comisión 1ra Evaluación",
            f"${total_comision_primera:,.2f}",
            help="Comisión total por primera evaluación"
        )
    
    with col4:
        total_comision_otras = df_analisis['comision_otras'].sum()
        st.metric(
            "Comisión Otras Evaluaciones",
            f"${total_comision_otras:,.2f}",
            help="Comisión total por otras evaluaciones"
        )
    
    with col5:
        total_comisiones = total_comision_primera + total_comision_otras
        st.metric(
            "Total Comisiones",
            f"${total_comisiones:,.2f}",
            help="Suma total de todas las comisiones"
        )
    
    # Nueva métrica de conversión desde Wicho
    if conversion_wicho:
        st.markdown("### 🎯 Tasa de Conversión desde Archivo Wicho")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Líneas Wicho",
                f"{conversion_wicho['total_lineas_wicho']:,}",
                help="Total de líneas en el archivo Wicho original"
            )
        
        with col2:
            st.metric(
                "Líneas Convertidas",
                f"{conversion_wicho['total_primera_eval']:,}",
                help="Líneas que llegaron a primera evaluación"
            )
        
        with col3:
            st.metric(
                "Tasa de Conversión",
                f"{conversion_wicho['tasa_conversion']:.1f}%",
                help="Porcentaje de líneas Wicho que llegaron a primera evaluación"
            )
    
    # Gráficos con estilo mejorado
    st.markdown("### 📈 Evolución Temporal")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Evolución de Evaluaciones")
        # Asegurar que las fechas se muestren correctamente
        df_analisis['mes'] = pd.to_datetime(df_analisis['fecha']).dt.strftime('%Y-%m')
        evolucion = df_analisis.groupby('mes')[['primera_eval', 'otras_eval']].sum()
        # Ordenar por fecha
        evolucion = evolucion.sort_index()
        st.line_chart(evolucion, use_container_width=True)
    
    with col2:
        st.markdown("#### Evolución de Comisiones")
        evolucion_comisiones = df_analisis.groupby('mes')[['comision_primera', 'comision_otras']].sum()
        # Ordenar por fecha
        evolucion_comisiones = evolucion_comisiones.sort_index()
        st.line_chart(evolucion_comisiones, use_container_width=True)
    
    # Nueva sección para análisis de evolución de comisiones
    st.markdown("### 💰 Análisis de Evolución de Comisiones")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Diferencia entre Comisiones (1ra vs Otras)")
        df_analisis['diferencia_comisiones'] = df_analisis['comision_otras'] - df_analisis['comision_primera']
        df_analisis['mes'] = pd.to_datetime(df_analisis['fecha']).dt.strftime('%Y-%m')
        evolucion_diferencia = df_analisis.groupby('mes')['diferencia_comisiones'].sum()
        evolucion_diferencia = evolucion_diferencia.sort_index()
        st.line_chart(evolucion_diferencia, use_container_width=True)
        st.caption("Valores positivos indican que las comisiones de otras evaluaciones superan a las de primera evaluación")
    
    with col2:
        st.markdown("#### Ratio de Comisiones (Otras/1ra)")
        df_analisis['ratio_comisiones'] = df_analisis['comision_otras'] / df_analisis['comision_primera'].replace(0, 1)
        evolucion_ratio = df_analisis.groupby('mes')['ratio_comisiones'].mean()
        evolucion_ratio = evolucion_ratio.sort_index()
        st.line_chart(evolucion_ratio, use_container_width=True)
        st.caption("Valores > 1 indican que las comisiones de otras evaluaciones son mayores que las de primera")
    
    # Análisis de Funnel de Evaluaciones Mejorado
    st.markdown("### 🎯 Funnel de Evaluaciones")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Distribución de Evaluaciones por Mes")
        df_funnel['mes'] = pd.to_datetime(df_funnel['fecha']).dt.strftime('%Y-%m')
        funnel_mensual = df_funnel.groupby('mes')[['primera', 'segunda', 'tercera', 'cuarta']].sum()
        funnel_mensual = funnel_mensual.sort_index()
        st.bar_chart(funnel_mensual, use_container_width=True)
    
    with col2:
        st.markdown("#### Tasa de Retención por Fase")
        # Calcular tasas de retención
        total_primera = df_funnel['primera'].sum()
        total_segunda = df_funnel['segunda'].sum()
        total_tercera = df_funnel['tercera'].sum()
        total_cuarta = df_funnel['cuarta'].sum()
        
        # Preparar datos para el gráfico
        fases = []
        lineas_count = []  # Número de líneas para el ancho del funnel
        tasas = []
        lineas = []
        comisiones = []
        
        # Agregar conversión desde Wicho si está disponible
        if conversion_wicho:
            fases.append('Wicho → 1ra')
            lineas_count.append(conversion_wicho['total_lineas_wicho'])  # Ancho basado en líneas Wicho
            tasa_wicho = conversion_wicho['tasa_conversion']
            tasas.append(tasa_wicho)
            lineas.append(f"{conversion_wicho['total_lineas_wicho']:,} → {conversion_wicho['total_primera_eval']:,}")
            comisiones.append(f"$0 → ${total_primera * 25:,}")
        
        # Agregar fases de retención
        fases.extend(['1ra → 2da', '2da → 3ra', '3ra → 4ta'])
        lineas_count.extend([total_primera, total_segunda, total_tercera])  # Ancho basado en líneas de cada fase
        tasas.extend([
            (total_segunda / total_primera * 100) if total_primera > 0 else 0,
            (total_tercera / total_segunda * 100) if total_segunda > 0 else 0,
            (total_cuarta / total_tercera * 100) if total_tercera > 0 else 0
        ])
        lineas.extend([
            f"{total_primera:,} → {total_segunda:,}",
            f"{total_segunda:,} → {total_tercera:,}",
            f"{total_tercera:,} → {total_cuarta:,}"
        ])
        comisiones.extend([
            f"${total_primera * 25:,} → ${total_segunda * 25:,}",
            f"${total_segunda * 25:,} → ${total_tercera * 25:,}",
            f"${total_tercera * 25:,} → ${total_cuarta * 25:,}"
        ])
        
        tasas_data = {
            'Fase': fases,
            'Líneas': lineas_count,  # Usar número de líneas para el ancho
            'Tasa de Retención': tasas,
            'Líneas_Texto': lineas,
            'Comisión': comisiones
        }
        df_tasas = pd.DataFrame(tasas_data)
        
        # Crear el gráfico de funnel
        fig = px.funnel(
            df_tasas,
            x='Líneas',  # Usar número de líneas para el ancho del funnel
            y='Fase',
            title='Funnel de Conversión y Retención',
            orientation='h',
            color='Fase',  # Colores diferentes para cada fase
            color_discrete_map={
                'Wicho → 1ra': '#1f77b4',      # Azul
                '1ra → 2da': '#ff7f0e',        # Naranja
                '2da → 3ra': '#2ca02c',        # Verde
                '3ra → 4ta': '#d62728'         # Rojo
            }
        )
        
        # Configurar el layout
        fig.update_layout(
            xaxis_title='Número de Líneas',
            yaxis_title='Fases',
            showlegend=False,
            height=500,
            margin=dict(t=50, b=50, l=100, r=50),
            xaxis=dict(
                range=[0, max(df_tasas['Líneas']) * 1.1]  # Dar un poco más de espacio
            ),
            yaxis=dict(
                categoryorder='array',
                categoryarray=fases  # Mantener el orden definido
            )
        )
        
        # Agregar anotaciones simplificadas
        for i, row in df_tasas.iterrows():
            # Anotación para líneas (dentro del funnel)
            fig.add_annotation(
                x=row['Líneas'] / 2,  # Centrar en el funnel
                y=row['Fase'],
                text=row['Líneas_Texto'],
                showarrow=False,
                font=dict(size=14, color='white'),
                bgcolor='rgba(0, 0, 0, 0.6)',
                bordercolor='white',
                borderwidth=1,
                borderpad=6
            )
            
            # Anotación para tasa de retención (fuera del funnel)
            fig.add_annotation(
                x=row['Líneas'] + (max(df_tasas['Líneas']) * 0.03),
                y=row['Fase'],
                text=f"{row['Tasa de Retención']:.1f}%",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='black',
                font=dict(size=12, color='black'),
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='black',
                borderwidth=1,
                borderpad=4
            )
        
        # Formatear el funnel
        fig.update_traces(
            textinfo='none',  # No mostrar texto por defecto
            textposition='inside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Funnel de conversión: desde el archivo Wicho hasta la 4ta evaluación")
    
    # Nueva sección: Evolución temporal del funnel
    st.markdown("### 📈 Evolución Temporal del Funnel")
    
    # Crear datos para la evolución temporal
    if not df_analisis.empty:
        # Preparar datos temporales
        df_evolucion = df_analisis.copy()
        df_evolucion['fecha'] = pd.to_datetime(df_evolucion['fecha'])
        df_evolucion['mes'] = df_evolucion['fecha'].dt.strftime('%Y-%m')
        
        # Calcular líneas por mes
        evolucion_tasas = df_evolucion.groupby('mes').agg({
            'primera_eval': 'sum',
            'segunda_eval': 'sum',
            'tercera_eval': 'sum',
            'cuarta_eval': 'sum'
        }).reset_index()
        
        # Ordenar por fecha
        evolucion_tasas = evolucion_tasas.sort_values('mes')
        
        # Crear gráfico de evolución temporal de líneas
        fig_evolucion = px.line(
            evolucion_tasas,
            x='mes',
            y=['primera_eval', 'segunda_eval', 'tercera_eval', 'cuarta_eval'],
            title='Evolución de Líneas por Fase y Mes',
            labels={
                'mes': 'Mes',
                'value': 'Número de Líneas',
                'variable': 'Fase'
            },
            color_discrete_map={
                'primera_eval': '#1f77b4',  # Azul
                'segunda_eval': '#ff7f0e',  # Naranja
                'tercera_eval': '#2ca02c',  # Verde
                'cuarta_eval': '#d62728'    # Rojo
            }
        )
        
        # Configurar el gráfico
        fig_evolucion.update_layout(
            xaxis_title='Mes',
            yaxis_title='Número de Líneas',
            height=400,
            showlegend=True,
            legend_title='Fases'
        )
        
        # Actualizar nombres de las líneas
        fig_evolucion.data[0].name = '1ra Evaluación'
        fig_evolucion.data[1].name = '2da Evaluación'
        fig_evolucion.data[2].name = '3ra Evaluación'
        fig_evolucion.data[3].name = '4ta Evaluación'
        
        st.plotly_chart(fig_evolucion, use_container_width=True)
        
        # Agregar conversión desde Wicho si está disponible
        if conversion_wicho:
            st.markdown("#### 📊 Evolución Wicho → 1ra Evaluación")
            
            # Calcular líneas de Wicho por mes (asumiendo que todas las líneas de primera eval vienen de Wicho)
            evolucion_wicho = df_evolucion.groupby('mes')['primera_eval'].sum().reset_index()
            evolucion_wicho['lineas_wicho'] = evolucion_wicho['primera_eval'] / (conversion_wicho['tasa_conversion'] / 100)
            
            # Crear gráfico de evolución Wicho → 1ra
            fig_wicho = px.line(
                evolucion_wicho,
                x='mes',
                y=['lineas_wicho', 'primera_eval'],
                title='Evolución Wicho → 1ra Evaluación',
                labels={
                    'mes': 'Mes',
                    'value': 'Número de Líneas',
                    'variable': 'Origen'
                },
                color_discrete_map={
                    'lineas_wicho': '#9467bd',  # Púrpura
                    'primera_eval': '#1f77b4'   # Azul
                }
            )
            
            # Configurar el gráfico
            fig_wicho.update_layout(
                xaxis_title='Mes',
                yaxis_title='Número de Líneas',
                height=400,
                showlegend=True,
                legend_title='Origen'
            )
            
            # Actualizar nombres de las líneas
            fig_wicho.data[0].name = 'Líneas Wicho'
            fig_wicho.data[1].name = '1ra Evaluación'
            
            st.plotly_chart(fig_wicho, use_container_width=True)
            
            # Métricas de evolución Wicho
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_wicho = evolucion_wicho['lineas_wicho'].sum()
                st.metric(
                    "Total Líneas Wicho",
                    f"{total_wicho:,.0f}",
                    help="Total de líneas del archivo Wicho en el período"
                )
            
            with col2:
                total_convertidas = evolucion_wicho['primera_eval'].sum()
                st.metric(
                    "Total Convertidas",
                    f"{total_convertidas:,}",
                    help="Total de líneas convertidas a 1ra evaluación"
                )
            
            with col3:
                if len(evolucion_wicho) > 1:
                    crecimiento_wicho = ((evolucion_wicho['lineas_wicho'].iloc[-1] - evolucion_wicho['lineas_wicho'].iloc[0]) / evolucion_wicho['lineas_wicho'].iloc[0] * 100)
                    st.metric(
                        "Crecimiento Wicho",
                        f"{crecimiento_wicho:.1f}%",
                        help="Crecimiento de líneas Wicho desde el primer mes"
                    )
                else:
                    st.metric("Crecimiento Wicho", "N/A")
        
        # Gráfico de evolución de volumen de líneas (mantener el existente)
        st.markdown("#### 📊 Evolución del Volumen de Líneas por Fase")
        
        fig_volumen = px.line(
            evolucion_tasas,
            x='mes',
            y=['primera_eval', 'segunda_eval', 'tercera_eval', 'cuarta_eval'],
            title='Evolución del Volumen de Líneas por Fase',
            labels={
                'mes': 'Mes',
                'value': 'Número de Líneas',
                'variable': 'Fase'
            },
            color_discrete_map={
                'primera_eval': '#1f77b4',  # Azul
                'segunda_eval': '#ff7f0e',  # Naranja
                'tercera_eval': '#2ca02c',  # Verde
                'cuarta_eval': '#d62728'    # Rojo
            }
        )
        
        # Configurar el gráfico
        fig_volumen.update_layout(
            xaxis_title='Mes',
            yaxis_title='Número de Líneas',
            height=400,
            showlegend=True,
            legend_title='Fases'
        )
        
        # Actualizar nombres de las líneas
        fig_volumen.data[0].name = '1ra Evaluación'
        fig_volumen.data[1].name = '2da Evaluación'
        fig_volumen.data[2].name = '3ra Evaluación'
        fig_volumen.data[3].name = '4ta Evaluación'
        
        st.plotly_chart(fig_volumen, use_container_width=True)
        
        # Tabla resumida de evolución
        st.markdown("#### 📋 Resumen de Evolución Temporal")
        
        # Crear tabla resumida
        tabla_evolucion = evolucion_tasas.copy()
        tabla_evolucion['Total_Líneas'] = tabla_evolucion['primera_eval'] + tabla_evolucion['segunda_eval'] + tabla_evolucion['tercera_eval'] + tabla_evolucion['cuarta_eval']
        
        # Agregar datos de Wicho si está disponible
        if conversion_wicho:
            tabla_evolucion['Líneas_Wicho'] = tabla_evolucion['primera_eval'] / (conversion_wicho['tasa_conversion'] / 100)
            columnas_tabla = [
                'mes', 'Líneas_Wicho', 'primera_eval', 'segunda_eval', 'tercera_eval', 'cuarta_eval', 'Total_Líneas'
            ]
            columnas_rename = {
                'mes': 'Mes',
                'Líneas_Wicho': 'Líneas Wicho',
                'primera_eval': '1ra Evaluación',
                'segunda_eval': '2da Evaluación',
                'tercera_eval': '3ra Evaluación',
                'cuarta_eval': '4ta Evaluación',
                'Total_Líneas': 'Total Líneas'
            }
            formato_tabla = {
                'Líneas Wicho': '{:,.0f}',
                '1ra Evaluación': '{:,}',
                '2da Evaluación': '{:,}',
                '3ra Evaluación': '{:,}',
                '4ta Evaluación': '{:,}',
                'Total Líneas': '{:,}'
            }
        else:
            columnas_tabla = [
                'mes', 'primera_eval', 'segunda_eval', 'tercera_eval', 'cuarta_eval', 'Total_Líneas'
            ]
            columnas_rename = {
                'mes': 'Mes',
                'primera_eval': '1ra Evaluación',
                'segunda_eval': '2da Evaluación',
                'tercera_eval': '3ra Evaluación',
                'cuarta_eval': '4ta Evaluación',
                'Total_Líneas': 'Total Líneas'
            }
            formato_tabla = {
                '1ra Evaluación': '{:,}',
                '2da Evaluación': '{:,}',
                '3ra Evaluación': '{:,}',
                '4ta Evaluación': '{:,}',
                'Total Líneas': '{:,}'
            }
        
        st.dataframe(
            tabla_evolucion[columnas_tabla].rename(columns=columnas_rename).style.format(formato_tabla),
            hide_index=True,
            use_container_width=True
        )
    
    # Tabla detallada con estilo mejorado
    st.markdown("### 📋 Detalle por Archivo")
    df_analisis['fecha'] = pd.to_datetime(df_analisis['fecha']).dt.strftime('%Y-%m-%d')
    st.dataframe(
        df_analisis[[
            'fecha', 'archivo', 'primera_eval', 'otras_eval',
            'comision_primera', 'comision_otras'
        ]].rename(columns={
            'primera_eval': '1ra Evaluación',
            'otras_eval': 'Otras Evaluaciones',
            'comision_primera': 'Comisión 1ra',
            'comision_otras': 'Comisión Otras'
        }).style.format({
            '1ra Evaluación': '{:,}',
            'Otras Evaluaciones': '{:,}',
            'Comisión 1ra': '${:,.2f}',
            'Comisión Otras': '${:,.2f}'
        }),
        hide_index=True,
        use_container_width=True
    )

def obtener_estado_archivos():
    archivos = []
    for archivo in os.listdir(RESULTADOS_DIR):
        if archivo.endswith('.xlsx'):
            # Extraer fecha del nombre del archivo - manejar tanto formato antiguo como nuevo
            # Formato antiguo: YYYYMMDD_ (8 dígitos)
            # Formato nuevo: YYYYMMDD_HHMM_ (12 dígitos)
            fecha_match = re.match(r'(\d{8})_', archivo)
            if fecha_match:
                fecha_str = fecha_match.group(1)
                fecha = datetime.strptime(fecha_str, '%Y%m%d')
                estado = "PAGADO" if "PAGADO" in archivo else "POR PAGAR"
                archivos.append({
                    'nombre': archivo,
                    'fecha': fecha,
                    'estado': estado
                })
    return sorted(archivos, key=lambda x: x['fecha'], reverse=True)

def cambiar_estado_pago(nombre_archivo):
    archivo_actual = RESULTADOS_DIR / nombre_archivo
    if "POR_PAGAR" in nombre_archivo:
        nuevo_nombre = nombre_archivo.replace("POR_PAGAR", "PAGADO")
    else:
        nuevo_nombre = nombre_archivo.replace("PAGADO", "POR_PAGAR")
    
    archivo_nuevo = RESULTADOS_DIR / nuevo_nombre
    os.rename(archivo_actual, archivo_nuevo)
    return nuevo_nombre

def analizar_archivo_resultado(nombre_archivo):
    """
    Analiza un archivo de resultado para obtener el desglose de comisiones.
    
    Args:
        nombre_archivo (str): Nombre del archivo a analizar
        
    Returns:
        dict: Diccionario con el desglose de comisiones
    """
    try:
        ruta_archivo = RESULTADOS_DIR / nombre_archivo
        if not ruta_archivo.exists():
            return None
            
        # Leer el archivo
        df = pd.read_excel(ruta_archivo)
        
        # Verificar si las columnas necesarias existen
        if 'Evaluación' not in df.columns:
            return None
            
        if 'Comisión' not in df.columns:
            return None
            
        # Contar evaluaciones con múltiples variaciones de nombres
        evaluaciones = df['Evaluación'].value_counts()
        
        # Buscar evaluaciones con diferentes variaciones de nombres
        primera_eval = 0
        segunda_eval = 0
        tercera_eval = 0
        cuarta_eval = 0
        
        # Filtrar datos por tipo de evaluación y calcular comisiones reales
        primera_mask = df['Evaluación'].str.lower().str.contains('1ra|primera|1a|1°|1º', na=False)
        segunda_mask = df['Evaluación'].str.lower().str.contains('2da|segunda|2a|2°|2º', na=False)
        tercera_mask = df['Evaluación'].str.lower().str.contains('3ra|tercera|3a|3°|3º', na=False)
        cuarta_mask = df['Evaluación'].str.lower().str.contains('4ta|cuarta|4a|4°|4º', na=False)
        
        # Contar líneas por evaluación
        primera_eval = primera_mask.sum()
        segunda_eval = segunda_mask.sum()
        tercera_eval = tercera_mask.sum()
        cuarta_eval = cuarta_mask.sum()
        
        # Calcular comisiones reales basadas en la columna 'Comisión'
        comision_primera = df[primera_mask]['Comisión'].sum() if primera_eval > 0 else 0
        comision_segunda = df[segunda_mask]['Comisión'].sum() if segunda_eval > 0 else 0
        comision_tercera = df[tercera_mask]['Comisión'].sum() if tercera_eval > 0 else 0
        comision_cuarta = df[cuarta_mask]['Comisión'].sum() if cuarta_eval > 0 else 0
        
        # Calcular totales
        otras_eval = segunda_eval + tercera_eval + cuarta_eval
        comision_otras = comision_segunda + comision_tercera + comision_cuarta
        comision_dat = comision_segunda + comision_tercera + comision_cuarta
        total_comision = comision_primera + comision_otras
        
        return {
            'primera_eval': primera_eval,
            'otras_eval': otras_eval,
            'segunda_eval': segunda_eval,
            'tercera_eval': tercera_eval,
            'cuarta_eval': cuarta_eval,
            'comision_primera': comision_primera,
            'comision_otras': comision_otras,
            'comision_dat': comision_dat,
            'comision_segunda': comision_segunda,
            'comision_tercera': comision_tercera,
            'comision_cuarta': comision_cuarta,
            'total_comision': total_comision,
            'total_lineas': len(df)
        }
        
    except Exception as e:
        return None

def mostrar_dashboard():
    st.header("Dashboard de Comisiones")
    
    # Obtener lista de archivos y sus estados
    archivos = obtener_estado_archivos()
    
    if not archivos:
        st.warning("No hay archivos de comisiones para mostrar")
        return
    
    # Crear DataFrame para el dashboard
    df_dashboard = pd.DataFrame(archivos)
    
    # Verificar que el DataFrame tiene las columnas necesarias
    if 'estado' not in df_dashboard.columns:
        st.error("Error: No se pudo crear el DataFrame correctamente")
        return
    
    # Analizar cada archivo para obtener comisiones
    analisis_comisiones = []
    for _, row in df_dashboard.iterrows():
        analisis = analizar_archivo_resultado(row['nombre'])
        if analisis:
            analisis_comisiones.append({
                'nombre': row['nombre'],
                'fecha': row['fecha'],
                'estado': row['estado'],
                **analisis
            })
    
    # Crear DataFrame con análisis de comisiones
    if analisis_comisiones:
        df_comisiones = pd.DataFrame(analisis_comisiones)
        
        # Mostrar métricas principales
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            total_comisiones = len(df_dashboard)
            st.metric("Total Archivos", total_comisiones)
        
        with col2:
            comisiones_pagadas = len(df_dashboard[df_dashboard['estado'] == 'PAGADO'])
            st.metric("Archivos Pagados", comisiones_pagadas)
        
        with col3:
            comisiones_pendientes = len(df_dashboard[df_dashboard['estado'] == 'POR PAGAR'])
            st.metric("Archivos Pendientes", comisiones_pendientes)
        
        with col4:
            total_pagar = df_comisiones['total_comision'].sum()
            st.metric("Total a Pagar", f"${total_pagar:,.2f}")
        
        # Métricas de comisiones
        st.markdown("### 💰 Resumen de Comisiones")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_primera = df_comisiones['comision_primera'].sum()
            st.metric("Total 1ra Evaluación", f"${total_primera:,.2f}")
        
        with col2:
            total_dat = df_comisiones['comision_dat'].sum()
            st.metric("Total Comisión DAT", f"${total_dat:,.2f}")
        
        with col3:
            total_otras = df_comisiones['comision_otras'].sum()
            st.metric("Total Otras Evaluaciones", f"${total_otras:,.2f}")
        
        with col4:
            total_lineas_primera = df_comisiones['primera_eval'].sum()
            st.metric("Líneas 1ra Evaluación", f"{total_lineas_primera:,}")
        
        with col5:
            total_lineas_otras = df_comisiones['otras_eval'].sum()
            st.metric("Líneas Otras Evaluaciones", f"{total_lineas_otras:,}")
        
        # Mostrar gráfico de estado de comisiones
        st.subheader("Estado de Comisiones por Fecha")
        df_dashboard['fecha'] = pd.to_datetime(df_dashboard['fecha'])
        df_dashboard['mes'] = df_dashboard['fecha'].dt.strftime('%Y-%m')
        
        # Gráfico de barras por mes
        estado_por_mes = df_dashboard.groupby(['mes', 'estado']).size().unstack(fill_value=0)
        # Ordenar por fecha
        estado_por_mes = estado_por_mes.sort_index()
        st.bar_chart(estado_por_mes)
        
        # Tabla detallada de comisiones con botones
        st.subheader("📋 Detalle de Comisiones por Archivo")
        
        # Mostrar cada archivo con su información y botón de acción
        for _, row in df_comisiones.iterrows():
            with st.container():
                # Crear un expander para cada archivo
                with st.expander(f"📄 {row['nombre']} - Estado: {row['estado']} - Total: ${row['total_comision']:,.2f}"):
                    # Información del archivo
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**Fecha:** {pd.to_datetime(row['fecha']).strftime('%Y-%m-%d')}")
                        st.write(f"**Estado:** {row['estado']}")
                    
                    with col2:
                        st.write(f"**1ra Evaluación:**")
                        st.write(f"{row['primera_eval']:,} líneas")
                        st.write(f"${row['comision_primera']:,.2f}")
                    
                    with col3:
                        st.write(f"**2da Evaluación:**")
                        st.write(f"{row['segunda_eval']:,} líneas")
                        st.write(f"${row['comision_segunda']:,.2f}")
                    
                    with col4:
                        st.write(f"**3ra Evaluación:**")
                        st.write(f"{row['tercera_eval']:,} líneas")
                        st.write(f"${row['comision_tercera']:,.2f}")
                    
                    with col5:
                        st.write(f"**4ta Evaluación:**")
                        st.write(f"{row['cuarta_eval']:,} líneas")
                        st.write(f"${row['comision_cuarta']:,.2f}")
                    
                    with col6:
                        st.write(f"**Comisión DAT:**")
                        st.write(f"**${row['comision_dat']:,.2f}**")
                        st.write(f"({row['segunda_eval'] + row['tercera_eval'] + row['cuarta_eval']:,} líneas)")
                    
                    with col7:
                        st.write(f"**Total:**")
                        st.write(f"{row['total_lineas']:,} líneas")
                        st.write(f"${row['total_comision']:,.2f}")
                    
                    # Botón de acción
                    st.markdown("---")
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    with col_btn2:
                        if st.button(
                            "Cambiar a PAGADO" if row['estado'] == 'POR PAGAR' else "Cambiar a POR PAGAR",
                            key=f"btn_dashboard_{row['nombre']}",
                            type="primary"
                        ):
                            nuevo_nombre = cambiar_estado_pago(row['nombre'])
                            st.success(f"Estado actualizado para {nuevo_nombre}")
                            st.rerun()
                
                st.markdown("---")
        
        # También mostrar una tabla resumida sin botones para referencia rápida
        st.subheader("📊 Tabla Resumida")
        df_mostrar = df_comisiones.copy()
        df_mostrar['fecha'] = pd.to_datetime(df_mostrar['fecha']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            df_mostrar[[
                'fecha', 'nombre', 'estado', 'primera_eval', 'otras_eval', 
                'comision_primera', 'comision_dat', 'comision_otras', 'total_comision'
            ]].rename(columns={
                'primera_eval': '1ra Evaluación',
                'otras_eval': 'Otras Evaluaciones',
                'comision_primera': 'Comisión 1ra',
                'comision_dat': 'Comisión DAT',
                'comision_otras': 'Comisión Otras',
                'total_comision': 'Total Comisión'
            }).style.format({
                '1ra Evaluación': '{:,}',
                'Otras Evaluaciones': '{:,}',
                'Comisión 1ra': '${:,.2f}',
                'Comisión DAT': '${:,.2f}',
                'Comisión Otras': '${:,.2f}',
                'Total Comisión': '${:,.2f}'
            }),
            hide_index=True,
            use_container_width=True
        )
    else:
        # Mostrar métricas básicas si no hay análisis disponible
        col1, col2, col3 = st.columns(3)
        with col1:
            total_comisiones = len(df_dashboard)
            st.metric("Total Comisiones", total_comisiones)
        
        with col2:
            comisiones_pagadas = len(df_dashboard[df_dashboard['estado'] == 'PAGADO'])
            st.metric("Comisiones Pagadas", comisiones_pagadas)
        
        with col3:
            comisiones_pendientes = len(df_dashboard[df_dashboard['estado'] == 'POR PAGAR'])
            st.metric("Comisiones Pendientes", comisiones_pendientes)
        
        st.warning("⚠️ No se pudo analizar los archivos para obtener el desglose de comisiones")
        
        # Mostrar tabla básica
        st.subheader("Detalle de Comisiones")
        df_dashboard['fecha'] = pd.to_datetime(df_dashboard['fecha']).dt.strftime('%Y-%m-%d')
        
        # Mostrar tabla con botones de acción
        for _, row in df_dashboard.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
                with col1:
                    st.write(f"**{row['fecha']}**")
                with col2:
                    st.write(f"**{row['estado']}**")
                with col3:
                    st.write(f"**{row['nombre']}**")
                with col4:
                    if st.button(
                        "Cambiar a PAGADO" if row['estado'] == 'POR PAGAR' else "Cambiar a POR PAGAR",
                        key=f"btn_basic_{row['nombre']}",
                        type="primary"
                    ):
                        nuevo_nombre = cambiar_estado_pago(row['nombre'])
                        st.success(f"Estado actualizado para {nuevo_nombre}")
                        st.rerun()
                st.markdown("---")

def procesar_archivos():
    """
    Procesa los archivos de Wicho y detalle para generar el análisis de comisiones.
    """
    # Ruta del archivo de wicho
    archivo_wicho = BASE_DIR / "CHIPS RUTA JL CABRERA WICHO.xlsx"
    
    if not archivo_wicho.exists():
        st.error("❌ No se encontró el archivo CHIPS RUTA JL CABRERA WICHO.xlsx")
        return False

    # Leer todas las hojas del archivo wicho
    try:
        st.info("📊 Leyendo archivo de Wicho...")
        dataframes_wicho = pd.read_excel(archivo_wicho, sheet_name=None)
        st.success("✅ Archivo de Wicho leído correctamente")
    except Exception as e:
        st.error(f"❌ Error al leer el archivo de Wicho: {str(e)}")
        return False

    # Lista para almacenar los resultados finales
    resultados_finales = []
    archivos_procesados = []
    total_lineas_procesadas = 0

    # Iterar sobre cada archivo de detalle
    archivos_detalle = [f for f in os.listdir(DETALLE_DIR) if f.endswith('.xlsx') and not f.startswith('~$')]
    
    if not archivos_detalle:
        st.warning("⚠️ No hay archivos de detalle para procesar")
        return False

    st.info(f"📁 Procesando {len(archivos_detalle)} archivos de detalle...")
    
    for archivo_detalle in archivos_detalle:
        ruta_archivo_detalle = DETALLE_DIR / archivo_detalle
        st.write(f"📄 Procesando: {archivo_detalle}")
        
        try:
            # Leer el archivo de detalle sin especificar la fila de encabezado
            df_detalle_sin_encabezado = pd.read_excel(ruta_archivo_detalle, header=None)
            periodo = df_detalle_sin_encabezado.iloc[0, 2]
            st.write(f"📅 Período: {periodo}")

            # Leer el archivo de detalle con el encabezado en la fila 3
            df_detalle = pd.read_excel(ruta_archivo_detalle, header=2)
            df_detalle.columns = df_detalle.columns.str.strip()

            # Verificar el nombre de la columna en el archivo de detalle
            columnas_posibles = ['Número celular asignado', 'Número de Teléfono', 'Número celular', 'Celular']
            columna_numero = next((col for col in columnas_posibles if col in df_detalle.columns), None)

            if not columna_numero:
                st.warning(f"⚠️ No se encontró la columna de número de teléfono en el archivo {archivo_detalle}")
                continue

            # Procesar cada hoja del archivo wicho
            resultados_archivo = []
            for nombre_hoja, df_wicho in dataframes_wicho.items():
                if 'CEL' in df_wicho.columns:
                    # Realizar el join
                    df_join = pd.merge(
                        df_wicho,
                        df_detalle,
                        left_on='CEL',
                        right_on=columna_numero,
                        how='inner'
                    )
                    
                    if not df_join.empty:
                        resultados_archivo.append(df_join)
                        st.write(f"✅ Hoja '{nombre_hoja}': {len(df_join)} líneas encontradas")

            # Concatenar resultados del archivo actual
            if resultados_archivo:
                resultado_archivo = pd.concat(resultados_archivo, ignore_index=True)
                resultado_archivo = resultado_archivo.drop_duplicates(subset='CEL')
                resultado_archivo['Archivo_Detalle'] = archivo_detalle
                resultado_archivo['Periodo'] = periodo
                resultados_finales.append(resultado_archivo)
                archivos_procesados.append(archivo_detalle)
                total_lineas_procesadas += len(resultado_archivo)
                st.success(f"✅ Archivo {archivo_detalle} procesado correctamente")

        except Exception as e:
            st.error(f"❌ Error procesando el archivo {archivo_detalle}: {str(e)}")
            continue

    # Guardar resultados si se encontraron coincidencias
    if resultados_finales:
        resultado_final = pd.concat(resultados_finales, ignore_index=True)
        fecha_hora_actual = datetime.now().strftime("%Y%m%d_%H%M")
        nombre_archivo = RESULTADOS_DIR / f"{fecha_hora_actual}_analisis_chipExpress_(POR_PAGAR).xlsx"
        
        # Guardar el archivo de resultados
        try:
            resultado_final.to_excel(nombre_archivo, index=False)
            st.success(f"✅ Análisis completado. Resultados guardados en: {nombre_archivo}")
            st.info(f"📊 Resumen del análisis:")
            st.write(f"- Total de archivos procesados: {len(archivos_procesados)}")
            st.write(f"- Total de líneas encontradas: {total_lineas_procesadas}")
            st.write(f"- Archivo de resultados: {nombre_archivo}")

            # Mover archivos procesados a la carpeta histórica
            for archivo in archivos_procesados:
                origen = DETALLE_DIR / archivo
                destino = HISTORICO_DIR / archivo
                shutil.move(str(origen), str(destino))
            
            st.success(f"✅ Se movieron {len(archivos_procesados)} archivos a la carpeta histórica")
            return True
            
        except Exception as e:
            st.error(f"❌ Error al guardar el archivo de resultados: {str(e)}")
            return False
    else:
        st.warning("⚠️ No se encontraron coincidencias en ningún archivo")
        return False

def mostrar_archivos_carpeta(directorio, titulo):
    st.subheader(titulo)
    try:
        archivos = []
        for archivo in os.listdir(directorio):
            if archivo.endswith('.xlsx') and not archivo.startswith('~$'):
                ruta_completa = directorio / archivo
                tamaño = os.path.getsize(ruta_completa) / 1024
                fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                
                # Extraer año del nombre del archivo o de la fecha de modificación
                fecha_match = re.match(r'(\d{4})', archivo)
                if fecha_match:
                    año = fecha_match.group(1)
                else:
                    año = fecha_mod.strftime('%Y')
                
                archivos.append({
                    'Nombre': archivo,
                    'Tamaño (KB)': f"{tamaño:.1f}",
                    'Última modificación': fecha_mod.strftime('%Y-%m-%d %H:%M:%S'),
                    'Año': año
                })
        
        if archivos:
            # Convertir a DataFrame
            df = pd.DataFrame(archivos)
            
            # Obtener años únicos y ordenarlos de más reciente a más antiguo
            años = sorted(df['Año'].unique(), reverse=True)
            
            # Crear desplegable para seleccionar año
            año_seleccionado = st.selectbox(
                "Seleccionar Año",
                años,
                key=f"año_{titulo}"
            )
            
            # Filtrar archivos por año seleccionado
            df_filtrado = df[df['Año'] == año_seleccionado]
            
            # Mostrar tabla de archivos
            st.dataframe(
                df_filtrado[['Nombre', 'Tamaño (KB)', 'Última modificación']],
                hide_index=True,
                use_container_width=True
            )
            
            # Agregar botones de descarga
            st.subheader("Descargar Archivos")
            
            # Crear columnas para los archivos
            cols = st.columns(3)  # 3 archivos por fila
            
            for idx, archivo in enumerate(df_filtrado.itertuples()):
                col_idx = idx % 3
                with cols[col_idx]:
                    st.write(archivo.Nombre)
                    with open(directorio / archivo.Nombre, 'rb') as f:
                        st.download_button(
                            label="📥 Descargar",
                            data=f,
                            file_name=archivo.Nombre,
                            key=f"download_{archivo.Nombre}"
                        )
        else:
            st.warning(f"No hay archivos en {titulo}")
    except Exception as e:
        st.error(f"Error al acceder a {titulo}: {str(e)}")

# Función para verificar credenciales
def check_credentials(username, password):
    # En un entorno real, esto debería estar en una base de datos o variables de entorno
    # Por ahora, usaremos un archivo de configuración
    config_file = Path("config.json")
    
    if not config_file.exists():
        # Crear configuración por defecto si no existe
        default_config = {
            "users": {
                "admin": {
                    "password": hashlib.sha256("Lupanar2024".encode()).hexdigest(),
                    "role": "admin"
                }
            }
        }
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)
    
    # Leer configuración
    with open(config_file, "r") as f:
        config = json.load(f)
    
    # Verificar credenciales
    if username in config["users"]:
        stored_password = config["users"][username]["password"]
        if hashlib.sha256(password.encode()).hexdigest() == stored_password:
            return True, config["users"][username]["role"]
    
    return False, None

# Inicializar estado de autenticación
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "archivo_eliminado" not in st.session_state:
    st.session_state.archivo_eliminado = False

# Mostrar login si no está autenticado
if not st.session_state.authenticated:
    st.title("🔐 Login - Análisis de Chips Express")
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            authenticated, role = check_credentials(username, password)
            if authenticated:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = role
                st.success("¡Bienvenido!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    
    st.stop()

# Mostrar información de usuario
st.sidebar.write(f"👤 {st.session_state.username}")

# Menú lateral
st.sidebar.title("📊 Análisis de Chips Express")

# Selección de página
pagina = st.sidebar.radio(
    "Navegación",
    ["📈 Dashboard", "📁 Gestión de Archivos", "🚀 Ejecutar Análisis de Comisiones", "⚙️ Configuración"]
)

# Contenido principal basado en la selección
if pagina == "📈 Dashboard":
    st.title("📈 Dashboard de Comisiones")
    mostrar_analisis_pagados()
    st.markdown("---")
    mostrar_dashboard()

elif pagina == "📁 Gestión de Archivos":
    st.title("📁 Gestión de Archivos")
    
    # Tabs para diferentes tipos de archivos
    tab1, tab2, tab3 = st.tabs(["📊 Resultados", "📚 Detalle Histórico", "📁 Detalle"])
    
    with tab1:
        st.subheader("Archivos en Resultados")
        try:
            archivos = []
            for archivo in os.listdir(RESULTADOS_DIR):
                if archivo.endswith('.xlsx') and not archivo.startswith('~$'):
                    ruta_completa = RESULTADOS_DIR / archivo
                    tamaño = os.path.getsize(ruta_completa) / 1024
                    fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                    archivos.append({
                        'Nombre': archivo,
                        'Tamaño (KB)': f"{tamaño:.1f}",
                        'Última modificación': fecha_mod.strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            if archivos:
                df = pd.DataFrame(archivos)
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Agregar botones de descarga
                st.subheader("Descargar Archivos")
                for archivo in archivos:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(archivo['Nombre'])
                    with col2:
                        with open(RESULTADOS_DIR / archivo['Nombre'], 'rb') as f:
                            st.download_button(
                                label="📥 Descargar",
                                data=f,
                                file_name=archivo['Nombre'],
                                key=f"download_{archivo['Nombre']}"
                            )
            else:
                st.warning("No hay archivos en Resultados")
        except Exception as e:
            st.error(f"Error al acceder a Resultados: {str(e)}")
    
    with tab2:
        mostrar_archivos_carpeta(HISTORICO_DIR, "Archivos en Detalle Histórico")
    
    with tab3:
        mostrar_archivos_carpeta(DETALLE_DIR, "Archivos en Detalle")

elif pagina == "🚀 Ejecutar Análisis de Comisiones":
    st.title("🚀 Ejecutar Análisis de Comisiones")
    
    # Paso 1: Archivo Wicho (siempre permitir subir)
    archivo_wicho = TEMP_DIR / "CHIPS RUTA JL CABRERA WICHO.xlsx"
    
    st.markdown("### 1️⃣ Subir Archivo Wicho")
    
    # Mostrar estado actual del archivo
    if archivo_wicho.exists():
        st.success("✅ Archivo de Wicho actualmente cargado")
        # Mostrar información del archivo actual
        fecha_mod = datetime.fromtimestamp(os.path.getmtime(archivo_wicho))
        tamaño = os.path.getsize(archivo_wicho) / 1024
        st.info(f"📄 Archivo actual: {archivo_wicho.name}")
        st.info(f"📅 Última modificación: {fecha_mod.strftime('%Y-%m-%d %H:%M:%S')}")
        st.info(f"📏 Tamaño: {tamaño:.1f} KB")
        
        # Botón para eliminar archivo actual
        if st.button("🗑️ Eliminar archivo actual", type="secondary"):
            try:
                archivo_wicho.unlink()
                st.success("✅ Archivo eliminado. Puedes subir uno nuevo.")
                # Usar session state para indicar que se eliminó
                st.session_state.archivo_eliminado = True
            except Exception as e:
                st.error(f"❌ Error al eliminar archivo: {str(e)}")
    
    # Uploader para el archivo Wicho
    archivo_wicho_upload = st.file_uploader(
        "Sube el archivo CHIPS RUTA JL CABRERA WICHO.xlsx",
        type=['xlsx'],
        help="Este archivo contiene la información base para el análisis. Si ya existe uno, será reemplazado."
    )
    
    if archivo_wicho_upload:
        try:
            with st.spinner("🔄 Procesando archivo Wicho..."):
                # Guardar archivo Wicho en el directorio temporal
                ruta_wicho = TEMP_DIR / "CHIPS RUTA JL CABRERA WICHO.xlsx"
                with open(ruta_wicho, "wb") as f:
                    f.write(archivo_wicho_upload.getvalue())
                
                # Guardar datos persistentes
                dataframes_wicho = pd.read_excel(archivo_wicho_upload, sheet_name=None)
                guardar_datos_persistentes("wicho", dataframes_wicho)
                
                # Guardar en Git (función simplificada)
                if guardar_en_git(ruta_wicho, "Actualizar archivo Wicho"):
                    st.success("✅ Archivo de Wicho guardado correctamente")
                else:
                    st.error("❌ Error al guardar el archivo Wicho")
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")

    # Paso 2: Archivos de Detalle
    st.markdown("### 2️⃣ Subir Archivos de Detalle")
    
    # Crear tabs para diferentes tipos de archivos
    tab1, tab2 = st.tabs(["📁 Archivos Excel", "📦 Archivos ZIP"])
    
    with tab1:
        archivos_detalle = st.file_uploader(
            "Sube los archivos de detalle en Excel",
            type=['xlsx'],
            accept_multiple_files=True,
            help="Puedes subir uno o varios archivos de detalle para procesar"
        )
    
    with tab2:
        archivos_zip = st.file_uploader(
            "Sube los archivos ZIP",
            type=['zip'],
            accept_multiple_files=True,
            help="Puedes subir uno o varios archivos ZIP. Se extraerán automáticamente los archivos Excel."
        )
        
        if archivos_zip:
            with st.spinner("🔄 Procesando archivos ZIP..."):
                for zip_file in archivos_zip:
                    try:
                        # Crear directorio temporal para extraer
                        temp_extract_dir = TEMP_DIR / "temp_extract"
                        temp_extract_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Guardar ZIP temporalmente
                        temp_zip = temp_extract_dir / zip_file.name
                        with open(temp_zip, "wb") as f:
                            f.write(zip_file.getvalue())
                        
                        # Extraer ZIP
                        import zipfile
                        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                            zip_ref.extractall(temp_extract_dir)
                        
                        # Mover archivos Excel a Detalle
                        for excel_file in temp_extract_dir.glob("**/*.xlsx"):
                            if not excel_file.name.startswith('~$'):  # Ignorar archivos temporales
                                shutil.copy2(excel_file, DETALLE_DIR / excel_file.name)
                                st.success(f"✅ Extraído: {excel_file.name}")
                        
                        # Limpiar archivos temporales
                        shutil.rmtree(temp_extract_dir)
                        temp_zip.unlink()
                        
                    except Exception as e:
                        st.error(f"❌ Error al procesar {zip_file.name}: {str(e)}")
    
    # Paso 3: Ejecutar Análisis
    st.markdown("### 3️⃣ Ejecutar Análisis")
    
    # Mostrar estado de los archivos
    col1, col2 = st.columns(2)
    with col1:
        if archivo_wicho.exists():
            st.success("✅ Archivo Wicho listo")
        else:
            st.warning("⚠️ Falta subir el archivo Wicho")
    
    with col2:
        total_archivos = len(archivos_detalle) + (len(archivos_zip) if archivos_zip else 0)
        if total_archivos > 0:
            st.success(f"✅ {total_archivos} archivos listos para procesar")
        else:
            st.warning("⚠️ Falta subir archivos de detalle")
    
    # Mostrar resumen de archivos a procesar
    if total_archivos > 0:
        st.markdown("#### 📋 Resumen de archivos a procesar")
        if archivos_detalle:
            st.markdown("**Archivos Excel:**")
            for archivo in archivos_detalle:
                st.write(f"- {archivo.name}")
        
        if archivos_zip:
            st.markdown("**Archivos ZIP:**")
            for zip_file in archivos_zip:
                st.write(f"- {zip_file.name}")
    
    # Botón para ejecutar el análisis
    if archivos_detalle or archivos_zip:
        if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
            if not archivo_wicho.exists():
                st.error("❌ Primero debes subir el archivo de Wicho")
            else:
                # Procesar archivos Excel
                for archivo in archivos_detalle:
                    try:
                        # Guardar en directorio temporal
                        ruta_archivo = DETALLE_DIR / archivo.name
                        with open(ruta_archivo, "wb") as f:
                            f.write(archivo.getvalue())
                        
                        # Guardar en Git
                        if guardar_en_git(ruta_archivo, f"Agregar archivo de detalle: {archivo.name}"):
                            st.success(f"✅ Archivo {archivo.name} guardado correctamente en Git")
                        else:
                            st.error(f"❌ Error al guardar {archivo.name} en Git")
                            continue
                    except Exception as e:
                        st.error(f"❌ Error al guardar {archivo.name}: {str(e)}")
                        continue

                # Ejecutar análisis
                with st.spinner("🔄 Procesando archivos..."):
                    if procesar_archivos():
                        st.success("✅ Análisis completado exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al procesar los archivos")

elif pagina == "⚙️ Configuración":
    st.title("⚙️ Configuración")
    
    # Configuración de directorios
    st.markdown("### 📁 Configuración de Directorios")
    st.info("""
    Los directorios actuales son:
    - **Detalle**: Para archivos de detalle nuevos
    - **Resultados**: Para archivos de análisis generados
    - **Detalle histórico**: Para archivos de detalle procesados
    """)
    
    # Configuración de comisiones
    st.markdown("### 💰 Configuración de Comisiones")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Valores de Comisión")
        comision_primera = st.number_input(
            "Comisión por 1ra Evaluación ($)",
            min_value=0.0,
            max_value=1000.0,
            value=25.0,
            step=5.0,
            help="Valor de la comisión para la primera evaluación"
        )
        
        comision_otras = st.number_input(
            "Comisión por Otras Evaluaciones ($)",
            min_value=0.0,
            max_value=1000.0,
            value=25.0,
            step=5.0,
            help="Valor de la comisión para evaluaciones posteriores"
        )
    
    with col2:
        st.markdown("#### Configuración de Evaluaciones")
        dias_entre_evaluaciones = st.number_input(
            "Días entre evaluaciones",
            min_value=1,
            max_value=90,
            value=30,
            step=1,
            help="Número de días que deben pasar entre evaluaciones"
        )
        
        max_evaluaciones = st.number_input(
            "Máximo de evaluaciones",
            min_value=1,
            max_value=10,
            value=4,
            step=1,
            help="Número máximo de evaluaciones por línea"
        )
    
    # Configuración de visualización
    st.markdown("### 📊 Configuración de Visualización")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Formato de Fechas")
        formato_fecha = st.selectbox(
            "Formato de fecha preferido",
            ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
            help="Formato en que se mostrarán las fechas en la aplicación"
        )
        
        zona_horaria = st.selectbox(
            "Zona horaria",
            ["America/Mexico_City", "UTC"],
            help="Zona horaria para las fechas"
        )
    
    with col2:
        st.markdown("#### Configuración de Gráficos")
        mostrar_tooltips = st.checkbox(
            "Mostrar tooltips en gráficos",
            value=True,
            help="Muestra información adicional al pasar el mouse sobre los gráficos"
        )
        
        tema_graficos = st.selectbox(
            "Tema de gráficos",
            ["Claro", "Oscuro", "Sistema"],
            help="Tema visual para los gráficos"
        )
    
    # Configuración de notificaciones
    st.markdown("### 🔔 Configuración de Notificaciones")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Alertas")
        alerta_comisiones = st.checkbox(
            "Alertar cuando las comisiones de otras evaluaciones superen a las de primera",
            value=True,
            help="Muestra una alerta cuando las comisiones de otras evaluaciones sean mayores"
        )
        
        alerta_retencion = st.checkbox(
            "Alertar cuando la tasa de retención sea baja",
            value=True,
            help="Muestra una alerta cuando la tasa de retención entre fases sea menor al 50%"
        )
    
    with col2:
        st.markdown("#### Umbrales de Alerta")
        umbral_retencion = st.slider(
            "Umbral de retención (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Porcentaje mínimo de retención para no mostrar alerta"
        )
        
        umbral_comisiones = st.slider(
            "Umbral de diferencia de comisiones (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            help="Diferencia porcentual mínima para mostrar alerta de comisiones"
        )
    
    # Botón para guardar configuración
    if st.button("💾 Guardar Configuración", type="primary"):
        # Aquí iría la lógica para guardar la configuración
        st.success("Configuración guardada exitosamente")
        
    # Información del sistema
    st.markdown("### ℹ️ Información del Sistema")
    st.info(f"""
    - **Versión de la aplicación**: 1.0.0
    - **Última actualización**: {datetime.now().strftime('%Y-%m-%d')}
    - **Directorio de trabajo**: {BASE_DIR.absolute()}
    - **Espacio disponible**: {shutil.disk_usage(BASE_DIR).free / (1024**3):.2f} GB
    """)

# Agregar espacio en la barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("---")

# Botón de logout al final de la barra lateral
if st.sidebar.button("🚪 Cerrar Sesión", type="primary"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun() 