import streamlit as st
import pandas as pd
import os
from datetime import datetime
import shutil
from pathlib import Path
import re
import hashlib
import json

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
DATA_DIR = BASE_DIR / "data"  # Directorio para datos persistentes

for directory in [DETALLE_DIR, RESULTADOS_DIR, HISTORICO_DIR, DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Función para guardar datos persistentes
def guardar_datos_persistentes(nombre, datos):
    """Guarda datos localmente."""
    archivo = DATA_DIR / f"{nombre}.pkl"
    pd.to_pickle(datos, archivo)

# Función para cargar datos persistentes
def cargar_datos_persistentes(nombre):
    """Carga datos localmente."""
    archivo = DATA_DIR / f"{nombre}.pkl"
    if archivo.exists():
        return pd.read_pickle(archivo)
    return None

# Función para procesar archivos (versión simplificada)
def procesar_archivos():
    """
    Procesa los archivos de Wicho y detalle para generar el análisis de comisiones.
    """
    # Cargar archivo Wicho persistente
    archivo_wicho = DATA_DIR / "wicho.pkl"
    if not archivo_wicho.exists():
        st.error("❌ No se encontró el archivo de Wicho. Por favor, súbelo primero.")
        return False

    try:
        dataframes_wicho = pd.read_pickle(archivo_wicho)
        st.success("✅ Archivo de Wicho cargado correctamente")
    except Exception as e:
        st.error(f"❌ Error al leer el archivo de Wicho: {str(e)}")
        return False

    # Procesar archivos de detalle
    archivos_detalle = [f for f in os.listdir(DETALLE_DIR) if f.endswith('.xlsx') and not f.startswith('~$')]
    if not archivos_detalle:
        st.warning("⚠️ No hay archivos de detalle para procesar")
        return False

    resultados_finales = []
    for archivo_detalle in archivos_detalle:
        try:
            df_detalle = pd.read_excel(DETALLE_DIR / archivo_detalle, header=2)
            df_detalle.columns = df_detalle.columns.str.strip()
            
            # Procesar cada hoja del archivo wicho
            for nombre_hoja, df_wicho in dataframes_wicho.items():
                if 'CEL' in df_wicho.columns:
                    df_join = pd.merge(
                        df_wicho,
                        df_detalle,
                        left_on='CEL',
                        right_on='Número celular asignado',
                        how='inner'
                    )
                    if not df_join.empty:
                        resultados_finales.append(df_join)
            
            # Mover archivo a histórico
            shutil.move(str(DETALLE_DIR / archivo_detalle), str(HISTORICO_DIR / archivo_detalle))
            
        except Exception as e:
            st.error(f"❌ Error procesando {archivo_detalle}: {str(e)}")
            continue

    if resultados_finales:
        resultado_final = pd.concat(resultados_finales, ignore_index=True)
        fecha_actual = datetime.now().strftime("%Y%m%d")
        nombre_archivo = RESULTADOS_DIR / f"{fecha_actual}_analisis_chipExpress_(POR_PAGAR).xlsx"
        resultado_final.to_excel(nombre_archivo, index=False)
        st.success(f"✅ Análisis completado. Resultados guardados en: {nombre_archivo}")
        return True
    
    st.warning("⚠️ No se encontraron coincidencias")
    return False

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

def mostrar_analisis_pagados():
    st.header("Análisis de Comisiones Pagadas")
    
    df_analisis, df_funnel = analizar_archivos_pagados()
    
    if df_analisis.empty:
        st.warning("No hay archivos pagados para analizar")
        return
    
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
    
    # Análisis de Funnel de Evaluaciones
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
        
        tasas = {
            'Fase': ['1ra → 2da', '2da → 3ra', '3ra → 4ta'],
            'Tasa de Retención': [
                (total_segunda / total_primera * 100) if total_primera > 0 else 0,
                (total_tercera / total_segunda * 100) if total_segunda > 0 else 0,
                (total_cuarta / total_tercera * 100) if total_tercera > 0 else 0
            ]
        }
        df_tasas = pd.DataFrame(tasas)
        st.bar_chart(df_tasas.set_index('Fase'), use_container_width=True)
        st.caption("Porcentaje de líneas que avanzan a la siguiente fase de evaluación")
    
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
            # Extraer fecha del nombre del archivo
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
    
    # Mostrar métricas principales
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
    
    # Mostrar gráfico de estado de comisiones
    st.subheader("Estado de Comisiones por Fecha")
    df_dashboard['fecha'] = pd.to_datetime(df_dashboard['fecha'])
    df_dashboard['mes'] = df_dashboard['fecha'].dt.strftime('%Y-%m')
    
    # Gráfico de barras por mes
    estado_por_mes = df_dashboard.groupby(['mes', 'estado']).size().unstack(fill_value=0)
    # Ordenar por fecha
    estado_por_mes = estado_por_mes.sort_index()
    st.bar_chart(estado_por_mes)
    
    # Tabla de comisiones
    st.subheader("Detalle de Comisiones")
    df_dashboard['fecha'] = df_dashboard['fecha'].dt.strftime('%Y-%m-%d')
    
    # Mostrar tabla con botones de acción
    for _, row in df_dashboard.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(row['fecha'])
        with col2:
            st.write(row['estado'])
        with col3:
            st.write(row['nombre'])
        with col4:
            if st.button(
            "Cambiar a PAGADO" if row['estado'] == 'POR PAGAR' else "Cambiar a POR PAGAR",
            key=f"btn_{row['nombre']}"
            ):
                nuevo_nombre = cambiar_estado_pago(row['nombre'])
            st.success(f"Estado actualizado para {nuevo_nombre}")
            st.rerun()

def mostrar_archivos_carpeta(directorio, titulo):
    st.subheader(titulo)
    try:
        archivos = []
        for archivo in os.listdir(directorio):
            if archivo.endswith('.xlsx') and not archivo.startswith('~$'):
                ruta_completa = directorio / archivo
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
                    with open(directorio / archivo['Nombre'], 'rb') as f:
                        st.download_button(
                            label="📥 Descargar",
                            data=f,
                            file_name=archivo['Nombre'],
                            key=f"download_{archivo['Nombre']}"
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
    
    # Paso 1: Archivo Wicho (solo si no existe)
    archivo_wicho = DATA_DIR / "wicho.pkl"
    if not archivo_wicho.exists():
        st.markdown("### 1️⃣ Subir Archivo Wicho (Solo primera vez)")
        archivo_wicho_upload = st.file_uploader(
            "Sube el archivo CHIPS RUTA JL CABRERA WICHO.xlsx",
            type=['xlsx'],
            help="Este archivo contiene la información base para el análisis"
        )
        if archivo_wicho_upload:
            try:
                dataframes_wicho = pd.read_excel(archivo_wicho_upload, sheet_name=None)
                guardar_datos_persistentes("wicho", dataframes_wicho)
                st.success("✅ Archivo de Wicho guardado correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {str(e)}")
    else:
        st.success("✅ Archivo de Wicho ya está cargado")

    # Paso 2: Archivos de Detalle
    st.markdown("### 2️⃣ Subir Archivos de Detalle")
    archivos_detalle = st.file_uploader(
        "Sube los archivos de detalle",
        type=['xlsx'],
        accept_multiple_files=True,
        help="Puedes subir uno o varios archivos de detalle para procesar"
    )

    # Paso 3: Ejecutar Análisis
    if archivos_detalle:
        if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
            # Guardar archivos de detalle
            for archivo in archivos_detalle:
                with open(DETALLE_DIR / archivo.name, "wb") as f:
                    f.write(archivo.getvalue())
            
            # Ejecutar análisis
            with st.spinner("🔄 Procesando archivos..."):
                procesar_archivos()
                st.rerun()

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