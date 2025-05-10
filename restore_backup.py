#!/usr/bin/env python
import os
import json
import shutil
import subprocess
import sys
from pathlib import Path
from django.core.management import call_command
from django.conf import settings

"""
Script para restaurar una copia de seguridad del sistema CRM
Este script:
1. Restaura la base de datos desde el archivo JSON
2. Copia los archivos multimedia a sus ubicaciones correctas
"""

def restore_database():
    """Restaura la base de datos desde el archivo JSON"""
    print("Restaurando la base de datos...")
    
    # Ruta al archivo de volcado de la base de datos
    db_dump_path = 'media/db_backups/tmp/db_dump.json'
    
    # Verificar que el archivo existe
    if not os.path.exists(db_dump_path):
        print(f"Error: No se encontró el archivo {db_dump_path}")
        return False
    
    try:
        # Usar loaddata para cargar los datos en la base de datos
        print("Ejecutando loaddata para restaurar la base de datos...")
        call_command('loaddata', db_dump_path, verbosity=1)
        print("✓ Base de datos restaurada correctamente")
        return True
    except Exception as e:
        print(f"Error al restaurar la base de datos: {e}")
        return False

def restore_media_files():
    """Copia los archivos multimedia a sus ubicaciones correctas"""
    print("Restaurando archivos multimedia...")
    
    # Directorio origen de los archivos multimedia
    source_dir = Path('media/db_backups/tmp/media')
    
    # Directorio destino para los archivos multimedia
    dest_dir = Path('media')
    
    # Verificar que el directorio origen existe
    if not source_dir.exists():
        print(f"Error: No se encontró el directorio {source_dir}")
        return False
    
    try:
        # Copiar cada subdirectorio recursivamente
        for subdir in source_dir.iterdir():
            if subdir.is_dir():
                # Crear la carpeta destino si no existe
                target_dir = dest_dir / subdir.name
                target_dir.mkdir(exist_ok=True)
                
                # Copiar todos los archivos
                for file_path in subdir.glob('**/*'):
                    if file_path.is_file():
                        # Determinar la ruta relativa
                        rel_path = file_path.relative_to(source_dir)
                        target_path = dest_dir / rel_path
                        
                        # Crear directorios padres si es necesario
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copiar el archivo
                        shutil.copy2(file_path, target_path)
                        print(f"  Copiado: {rel_path}")
        
        print("✓ Archivos multimedia restaurados correctamente")
        return True
    except Exception as e:
        print(f"Error al restaurar los archivos multimedia: {e}")
        return False

if __name__ == "__main__":
    print("=== Proceso de restauración de copia de seguridad ===")
    
    # Configurar Django para poder usar call_command
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
    import django
    django.setup()
    
    # Restaurar la base de datos
    db_success = restore_database()
    
    # Restaurar los archivos multimedia
    media_success = restore_media_files()
    
    if db_success and media_success:
        print("\n✓ Restauración completada exitosamente")
    else:
        print("\n✗ La restauración no se completó correctamente")
        if not db_success:
            print("  - Hubo un problema al restaurar la base de datos")
        if not media_success:
            print("  - Hubo un problema al restaurar los archivos multimedia")