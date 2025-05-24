# Análisis de Chips Express

Aplicación para el análisis y seguimiento de comisiones de líneas Telcel Express.

## Características

- Dashboard de comisiones con métricas principales
- Análisis de evolución de comisiones
- Funnel de evaluaciones
- Gestión de archivos de detalle y resultados
- Configuración personalizable

## Requisitos

- Python 3.8 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd express_analysis
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
streamlit run app.py
```

## Estructura de Directorios

- `Detalle/`: Archivos de detalle nuevos
- `Resultados/`: Archivos de análisis generados
- `Detalle historico/`: Archivos de detalle procesados

## Uso

1. Subir el archivo de Wicho
2. Subir los archivos de detalle
3. Ejecutar el análisis
4. Revisar los resultados en el dashboard

## Configuración

La aplicación permite configurar:
- Valores de comisiones
- Días entre evaluaciones
- Formato de fechas
- Alertas y notificaciones

## Licencia

[Especificar la licencia] 