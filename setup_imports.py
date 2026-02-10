import os
import re

# Lista de módulos comunes en tus proyectos que necesitan corrección
MODULES_TO_FIX = [
    'extractores', 'procesamiento', 'exportacion', 'utils', 
    'extractores_pdf', 'extractores_patrones', 'extractores_componentes',
    'db_connector', 'db_connector_utils', 'db_connector_consultas', 
    'db_connector_comparacion', 'exportacion_excel', 
    'exportacion_excel_multiple', 'exportacion_batch'
]

def fix_imports_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for mod in MODULES_TO_FIX:
        # Caso 1: import modulo -> from . import modulo
        # Evitamos cambiar imports que ya son relativos o que son de librerías externas
        pattern_import = fr'^\s*import\s+{mod}(\s|$)'
        content = re.sub(pattern_import, f'from . import {mod}\\1', content, flags=re.MULTILINE)
        
        # Caso 2: from modulo import ... -> from .modulo import ...
        pattern_from = fr'^\s*from\s+{mod}\s+import'
        content = re.sub(pattern_from, f'from .{mod} import', content, flags=re.MULTILINE)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Corregido: {os.path.basename(file_path)}")
    else:
        print(f"➖ Sin cambios: {os.path.basename(file_path)}")

def process_directory(directory):
    # Asegurar que exista __init__.py para que sea un paquete
    init_path = os.path.join(directory, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write(f"# Paquete {os.path.basename(directory)}")
        print(f"✨ Creado __init__.py en {os.path.basename(directory)}")

    # Recorrer archivos .py
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != 'setup_imports.py':
                fix_imports_in_file(os.path.join(root, file))

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(base_dir, 'modules')
    
    # Asegurar __init__.py en la carpeta modules
    if not os.path.exists(modules_dir):
        os.makedirs(modules_dir)
    if not os.path.exists(os.path.join(modules_dir, '__init__.py')):
        with open(os.path.join(modules_dir, '__init__.py'), 'w') as f: pass

    print("--- INICIANDO CORRECCIÓN DE IMPORTS ---")
    if os.path.exists(os.path.join(modules_dir, 'ecopetrol')):
        print("Procesando Ecopetrol...")
        process_directory(os.path.join(modules_dir, 'ecopetrol'))
    
    if os.path.exists(os.path.join(modules_dir, 'XM')):
        print("\nProcesando XM...")
        process_directory(os.path.join(modules_dir, 'XM'))
        
    print("\n--- ¡LISTO! PROYECTOS UNIFICADOS ---")