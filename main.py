import os
import logging
import importlib

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def obtener_modulo(project_type):
    """Carga dinámicamente el módulo main del proyecto seleccionado"""
    if project_type == "Ecopetrol":
        return importlib.import_module("modules.ecopetrol.main")
    elif project_type == "Gecelca/XM":
        return importlib.import_module("modules.XM.main")
    else:
        raise ValueError(f"Proyecto desconocido: {project_type}")

def procesar_factura(ruta_pdf, directorio_salida=None, project_type="Ecopetrol"):
    try:
        modulo = obtener_modulo(project_type)
        logger.info(f"--- Iniciando proceso individual para {project_type} ---")
        
        if project_type == "Ecopetrol":
            # Ecopetrol usa procesar_factura(ruta, salida, exportar_excel)
            return modulo.procesar_factura(ruta_pdf, directorio_salida, True)
        elif project_type == "Gecelca/XM":
            # Gecelca usa procesar_individual(ruta, salida)
            if hasattr(modulo, 'procesar_individual'):
                return modulo.procesar_individual(ruta_pdf, directorio_salida)
            else:
                return modulo.procesar_factura(ruta_pdf, directorio_salida)
                
    except Exception as e:
        logger.error(f"Error crítico en {project_type}: {e}", exc_info=True)
        return False

def procesar_directorio(directorio_entrada, directorio_salida=None, project_type="Ecopetrol"):
    try:
        modulo = obtener_modulo(project_type)
        logger.info(f"--- Iniciando proceso masivo para {project_type} ---")
        
        if project_type == "Ecopetrol":
            # Ecopetrol usa procesar_directorio(entrada, salida)
            return modulo.procesar_directorio(directorio_entrada, directorio_salida)
        elif project_type == "Gecelca/XM":
            # Gecelca usa procesar_directorio_consolidado(entrada, salida)
            if hasattr(modulo, 'procesar_directorio_consolidado'):
                return modulo.procesar_directorio_consolidado(directorio_entrada, directorio_salida)
            else:
                # Fallback por si el nombre es diferente
                return modulo.procesar_directorio(directorio_entrada, directorio_salida)

    except Exception as e:
        logger.error(f"Error crítico en directorio {project_type}: {e}", exc_info=True)
        return False