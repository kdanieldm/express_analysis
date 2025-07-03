#!/usr/bin/env python3
"""
Script de configuración para deploy en GitHub y Streamlit Cloud
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e.stderr}")
        return False

def check_git_status():
    """Verifica el estado de Git"""
    print("🔍 Verificando estado de Git...")
    
    # Verificar si es un repositorio Git
    if not Path(".git").exists():
        print("❌ No es un repositorio Git. Inicializando...")
        if not run_command("git init", "Inicializar repositorio Git"):
            return False
    
    # Verificar si hay cambios pendientes
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("📝 Hay cambios pendientes en Git")
        return True
    else:
        print("✅ No hay cambios pendientes")
        return False

def setup_git():
    """Configura Git para el proyecto"""
    print("\n🚀 Configurando Git...")
    
    # Configurar usuario si no está configurado
    result = subprocess.run("git config user.name", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️ Usuario de Git no configurado")
        name = input("Ingresa tu nombre para Git: ")
        run_command(f'git config user.name "{name}"', "Configurar nombre de usuario")
    
    result = subprocess.run("git config user.email", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️ Email de Git no configurado")
        email = input("Ingresa tu email para Git: ")
        run_command(f'git config user.email "{email}"', "Configurar email")
    
    return True

def create_initial_commit():
    """Crea el commit inicial"""
    print("\n📦 Creando commit inicial...")
    
    # Añadir todos los archivos
    if not run_command("git add .", "Añadir archivos al staging"):
        return False
    
    # Crear commit
    commit_message = "Initial commit: Análisis de Comisiones Express con integración Git"
    if not run_command(f'git commit -m "{commit_message}"', "Crear commit inicial"):
        return False
    
    return True

def setup_remote_repository():
    """Configura el repositorio remoto"""
    print("\n🌐 Configurando repositorio remoto...")
    
    # Verificar si ya existe un remoto
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("✅ Repositorio remoto ya configurado")
        return True
    
    # Solicitar URL del repositorio
    print("📋 Para continuar, necesitas crear un repositorio en GitHub:")
    print("1. Ve a https://github.com/new")
    print("2. Crea un nuevo repositorio")
    print("3. NO inicialices con README, .gitignore o licencia")
    print("4. Copia la URL del repositorio")
    
    repo_url = input("\nIngresa la URL del repositorio (ej: https://github.com/usuario/comisiones-mio.git): ")
    
    if repo_url:
        if run_command(f'git remote add origin "{repo_url}"', "Añadir repositorio remoto"):
            if run_command("git branch -M main", "Renombrar rama a main"):
                if run_command("git push -u origin main", "Subir al repositorio remoto"):
                    print("✅ Repositorio configurado exitosamente")
                    return True
    
    print("❌ No se pudo configurar el repositorio remoto")
    return False

def verify_structure():
    """Verifica que la estructura del proyecto sea correcta"""
    print("\n📁 Verificando estructura del proyecto...")
    
    required_files = [
        "streamlit_app.py",
        "requirements.txt",
        "README.md",
        "express_analysis/app.py",
        "express_analysis/requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Archivos faltantes: {', '.join(missing_files)}")
        return False
    
    print("✅ Estructura del proyecto correcta")
    return True

def main():
    """Función principal"""
    print("🚀 Configuración para Deploy en GitHub y Streamlit Cloud")
    print("=" * 60)
    
    # Verificar estructura
    if not verify_structure():
        print("❌ La estructura del proyecto no es correcta")
        sys.exit(1)
    
    # Configurar Git
    if not setup_git():
        print("❌ Error al configurar Git")
        sys.exit(1)
    
    # Verificar estado de Git
    has_changes = check_git_status()
    
    if has_changes:
        # Crear commit inicial
        if not create_initial_commit():
            print("❌ Error al crear commit inicial")
            sys.exit(1)
    
    # Configurar repositorio remoto
    if not setup_remote_repository():
        print("❌ Error al configurar repositorio remoto")
        sys.exit(1)
    
    print("\n🎉 ¡Configuración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Ve a https://share.streamlit.io")
    print("2. Conecta tu cuenta de GitHub")
    print("3. Selecciona este repositorio")
    print("4. Configura el archivo principal como: streamlit_app.py")
    print("5. ¡Tu aplicación estará disponible en Streamlit Cloud!")
    
    print("\n🔗 URLs útiles:")
    print("- Streamlit Cloud: https://share.streamlit.io")
    print("- Documentación Streamlit: https://docs.streamlit.io")
    print("- GitHub: https://github.com")

if __name__ == "__main__":
    main() 