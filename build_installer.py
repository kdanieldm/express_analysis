import os
import shutil
from pathlib import Path
import subprocess

def create_installer():
    # Directorios necesarios
    BASE_DIR = Path(".")
    DETALLE_DIR = BASE_DIR / "Detalle"
    RESULTADOS_DIR = BASE_DIR / "Resultados"
    HISTORICO_DIR = BASE_DIR / "Detalle historico"
    TEMP_DIR = BASE_DIR / "Temp"
    DIST_DIR = BASE_DIR / "dist"

    # Crear directorios necesarios si no existen
    for directory in [DETALLE_DIR, RESULTADOS_DIR, HISTORICO_DIR, TEMP_DIR, DIST_DIR]:
        directory.mkdir(exist_ok=True)

    # Ejecutar PyInstaller directamente
    print("Creando ejecutable...")
    subprocess.run([
        "python", "-m", "PyInstaller",
        "--name=ComisionesExpress",
        "--onefile",
        "--add-data=Detalle;Detalle",
        "--add-data=Resultados;Resultados",
        "--add-data=Detalle historico;Detalle historico",
        "--add-data=Temp;Temp",
        "express_analysis/app.py"
    ], check=True)

    # Crear directorio para el instalador
    installer_dir = DIST_DIR / "ComisionesExpress_Installer"
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    installer_dir.mkdir(exist_ok=True)

    # Copiar archivos necesarios al directorio del instalador
    print("Copiando archivos...")
    shutil.copy(DIST_DIR / "ComisionesExpress.exe", installer_dir)
    
    # Crear archivo batch para ejecutar la aplicación
    batch_content = """@echo off
echo Iniciando Comisiones Express...
start ComisionesExpress.exe
"""
    
    with open(installer_dir / "Iniciar_ComisionesExpress.bat", "w") as f:
        f.write(batch_content)

    # Crear archivo README
    readme_content = """Comisiones Express - Instalación

1. Ejecute el archivo 'Iniciar_ComisionesExpress.bat' para iniciar la aplicación.
2. La primera vez que ejecute la aplicación, deberá iniciar sesión con las credenciales por defecto:
   - Usuario: admin
   - Contraseña: Lupanar2024

Notas:
- No elimine ninguno de los archivos o carpetas incluidas en este directorio.
- Los archivos de detalle deben colocarse en la carpeta 'Detalle'.
- Los resultados se guardarán en la carpeta 'Resultados'.
- Los archivos procesados se moverán automáticamente a 'Detalle historico'.
"""
    
    with open(installer_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # Crear archivo ZIP del instalador
    print("Creando archivo ZIP...")
    shutil.make_archive(
        str(DIST_DIR / "ComisionesExpress_Installer"),
        'zip',
        installer_dir
    )

    print("Instalador creado exitosamente en la carpeta 'dist'")

if __name__ == "__main__":
    create_installer() 