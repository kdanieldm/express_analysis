"""
Streamlit App para Análisis de Comisiones Express
Este archivo es el punto de entrada para Streamlit Cloud
"""

import sys
import os

# Añadir el directorio express_analysis al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'express_analysis'))

# Importar la aplicación directamente
import app 