import pandas as pd
import os
from datetime import datetime

# Ruta del archivo de lineas de wicho
archivo_wicho = '/content/drive/MyDrive/Express Analysis/CHIPS RUTA JL CABRERA WICHO.xlsx'

# Directorio que contiene los archivos de detalle
directorio_detalles = '/content/drive/MyDrive/Express Analysis/Detalle'

# Leer todas las hojas del archivo wicho en un diccionario de DataFrames
dataframes_wicho = pd.read_excel(archivo_wicho, sheet_name=None)

# Lista para almacenar los resultados finales
resultados_finales = []

# Iterar sobre cada archivo de detalle en el directorio
for archivo_detalle in os.listdir(directorio_detalles):
    if archivo_detalle.endswith('.xlsx'):
        ruta_archivo_detalle = os.path.join(directorio_detalles, archivo_detalle)

        # Leer el archivo de detalle sin especificar la fila de encabezado
        df_detalle_sin_encabezado = pd.read_excel(ruta_archivo_detalle, header=None)

        # Obtener el periodo del archivo de detalle
        periodo = df_detalle_sin_encabezado.iloc[0, 2]

        # Leer el archivo de detalle con el encabezado en la fila 3
        df_detalle = pd.read_excel(ruta_archivo_detalle, header=2)

        # Eliminar espacios en blanco al inicio y al final de los nombres de las columnas
        df_detalle.columns = df_detalle.columns.str.strip()

        # Verificar el nombre de la columna en el archivo de detalle
        if 'Número celular asignado' in df_detalle.columns:
            columna_numero = 'Número celular asignado'
        elif 'Número de Teléfono' in df_detalle.columns:
            columna_numero = 'Número de Teléfono'
        elif 'Número celular' in df_detalle.columns:
            columna_numero = 'Número celular'
        elif 'Celular' in df_detalle.columns:
            columna_numero = 'Celular'
        else:
            print(f"No se encontró la columna de número de teléfono, Número celular en el archivo {archivo_detalle}. Se omitirá este archivo.")
            continue

        # Crear una lista para almacenar los resultados de este archivo de detalle
        resultados_archivo = []

        # Iterar sobre cada hoja del archivo wicho
        for nombre_hoja, df_wicho in dataframes_wicho.items():
            # Verificar si la columna 'CEL' existe en la hoja actual
            if 'CEL' in df_wicho.columns:
                # Realizar el join entre la hoja actual y el archivo de detalle
                df_join = pd.merge(df_wicho, df_detalle, left_on='CEL', right_on=columna_numero, how='inner')

                # Agregar el resultado a la lista de resultados del archivo
                resultados_archivo.append(df_join)
            else:
                print(f"La hoja '{nombre_hoja}' no tiene la columna 'CEL' y se descartará.")

        # Concatenar los resultados del archivo de detalle actual
        resultado_archivo = pd.concat(resultados_archivo, ignore_index=True)

        # Verificar si se encontraron coincidencias
        if resultado_archivo.empty:
            print(f"No se encontraron coincidencias de pago para Wicho en el periodo: {periodo} (Archivo: {archivo_detalle})")
        else:
            # Eliminar filas duplicadas basadas en la columna 'CEL'
            resultado_archivo = resultado_archivo.drop_duplicates(subset='CEL')

            # Agregar una columna con el nombre del archivo de detalle
            resultado_archivo['Archivo_Detalle'] = archivo_detalle

            # Agregar el resultado a la lista de resultados finales
            resultados_finales.append(resultado_archivo)

# Verificar si se encontraron coincidencias en algún archivo
if resultados_finales:
    # Concatenar todos los resultados finales
    resultado_final = pd.concat(resultados_finales, ignore_index=True)

    # Obtener la fecha actual
    fecha_actual = datetime.now().strftime("%Y%m%d")

    # Crear el nombre del archivo con la fecha
    nombre_archivo = f"/content/drive/MyDrive/Express Analysis/Resultados/{fecha_actual}_analisis_chipExpress_(POR_PAGAR).xlsx"

    # Guardar el resultado en un nuevo archivo de Excel con la fecha en el nombre
    resultado_final.to_excel(nombre_archivo, index=False)

    print(f"Se han encontrado coincidencias. El resultado se ha guardado en '{nombre_archivo}'")
else:
    print("No se encontraron coincidencias de pago para Wicho en ninguno de los archivos de detalle.")