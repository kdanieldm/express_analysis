# 📊 Análisis de Comisiones Express

Sistema de análisis y gestión de comisiones para Chips Express con integración Git automática.

## 🚀 Características

- **Análisis Automático**: Procesa archivos Excel de comisiones automáticamente
- **Integración Git**: Cada archivo subido se guarda automáticamente en el repositorio Git
- **Dashboard Interactivo**: Visualizaciones en tiempo real de métricas de comisiones
- **Gestión de Estados**: Control de archivos pagados y pendientes
- **Cálculo de Tasa de Conversión**: Análisis desde archivos Wicho hasta evaluaciones

## 📁 Estructura del Proyecto

```
comisiones-mio/
├── express_analysis/          # Código principal de la aplicación
│   ├── app.py                # Aplicación Streamlit principal
│   ├── main.py               # Script de procesamiento
│   ├── config.json           # Configuración de la aplicación
│   ├── requirements.txt      # Dependencias del módulo
│   └── .streamlit/           # Configuración de Streamlit
├── Detalle/                  # Archivos de detalle (se guardan en Git)
├── Resultados/               # Archivos de resultados generados
├── "Detalle historico"/      # Archivos históricos procesados
├── Temp/                     # Archivos temporales
├── streamlit_app.py          # Punto de entrada para Streamlit Cloud
├── requirements.txt          # Dependencias principales
└── README.md                 # Este archivo
```

## 🛠️ Instalación Local

1. **Clonar el repositorio**:
   ```bash
   git clone <tu-repositorio>
   cd comisiones-mio
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación**:
   ```bash
   streamlit run streamlit_app.py
   ```

## ☁️ Deploy en Streamlit Cloud

### Pasos para el Deploy:

1. **Subir a GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit for Streamlit deploy"
   git push origin main
   ```

2. **Conectar con Streamlit Cloud**:
   - Ve a [share.streamlit.io](https://share.streamlit.io)
   - Conecta tu cuenta de GitHub
   - Selecciona este repositorio
   - Configura el archivo principal como `streamlit_app.py`

### Configuración de Streamlit Cloud:

- **Main file path**: `streamlit_app.py`
- **Python version**: 3.9+
- **Requirements file**: `requirements.txt`

## 📊 Uso de la Aplicación

### 1. Autenticación
- Usuario: `admin`
- Contraseña: `admin123`

### 2. Subir Archivos
- **Archivo Wicho**: Sube el archivo base de datos
- **Archivos de Detalle**: Sube los archivos Excel de comisiones
- **Archivos ZIP**: Soporte para archivos comprimidos

### 3. Procesamiento Automático
- Los archivos se procesan automáticamente
- Se calculan métricas de comisiones
- Se generan reportes en la carpeta `Resultados/`

### 4. Integración Git
- Cada archivo subido se añade automáticamente al repositorio Git
- Los commits se crean con mensajes descriptivos
- El historial se mantiene sincronizado

## 🔧 Configuración

### Variables de Entorno (Opcional):
```bash
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Configuración de Comisiones:
- Comisión por 1ra Evaluación: $25
- Comisión por Otras Evaluaciones: $25
- Días entre evaluaciones: 30
- Máximo de evaluaciones: 4

## 📈 Métricas Disponibles

- **Total de 1ra Evaluación**: Número de líneas en primera evaluación
- **Total de Otras Evaluaciones**: Líneas en evaluaciones posteriores
- **Comisiones Totales**: Cálculo automático de comisiones
- **Tasa de Conversión**: Desde archivo Wicho hasta primera evaluación
- **Funnel de Evaluaciones**: Visualización del proceso completo

## 🗂️ Gestión de Archivos

### Carpetas Principales:
- **Detalle/**: Archivos nuevos por procesar
- **Resultados/**: Archivos generados por el análisis
- **Detalle historico/**: Archivos ya procesados
- **Temp/**: Archivos temporales y datos de sesión

### Tipos de Archivos Soportados:
- `.xlsx`: Archivos Excel principales
- `.zip`: Archivos comprimidos
- `.pkl`: Datos temporales (no se incluyen en Git)

## 🔒 Seguridad

- Autenticación básica implementada
- Validación de tipos de archivo
- Manejo seguro de rutas de archivos
- Exclusión de archivos temporales del Git

## 🐛 Solución de Problemas

### Error: "Git no está disponible"
- En entornos sin Git, los archivos se guardan localmente
- La funcionalidad principal no se ve afectada

### Error: "Archivo no encontrado"
- Verifica que el archivo existe en la ruta especificada
- Asegúrate de que el archivo no esté abierto en Excel

### Error: "Permisos denegados"
- Verifica los permisos de escritura en las carpetas
- En Windows, ejecuta como administrador si es necesario

## 📝 Notas de Desarrollo

- **Versión**: 1.0.0
- **Última actualización**: 2024
- **Compatibilidad**: Python 3.8+, Streamlit 1.32.0+
- **Sistema operativo**: Windows, macOS, Linux

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo

---

**Desarrollado con ❤️ para Chips Express** 