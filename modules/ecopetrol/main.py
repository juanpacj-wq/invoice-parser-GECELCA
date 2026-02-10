#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script principal para el procesamiento de facturas de energía (Ecopetrol).
"""

import os
import argparse
import logging
from datetime import datetime
import calendar

# Importar módulos propios con referencia relativa para que funcione como paquete
from . import extractores
from . import procesamiento
from . import exportacion
from . import utils

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("factura_processor_ecopetrol.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def procesar_factura(ruta_pdf, ruta_salida=None, exportar_excel=True, fecha_seleccionada=None):
    """
    Procesa una factura desde el PDF hasta la exportación.
    """
    try:
        # Validar que el archivo exista
        if not os.path.exists(ruta_pdf):
            logger.error(f"El archivo {ruta_pdf} no existe.")
            return None
        
        # Crear directorio de salida si es necesario
        if ruta_salida:
            utils.crear_directorio_si_no_existe(ruta_salida)
        else:
            ruta_salida = os.path.dirname(os.path.abspath(ruta_pdf))
        
        # Obtener nombre base del archivo
        nombre_base = utils.obtener_nombre_archivo_sin_extension(ruta_pdf)
        
        # Paso 1: Convertir PDF a CSV
        logger.info(f"Convirtiendo PDF a CSV: {ruta_pdf}")
        ruta_csv = extractores.convertir_pdf_a_csv(ruta_pdf)
        
        # Paso 2: Extraer datos
        logger.info(f"Extrayendo datos del CSV: {ruta_csv}")
        datos_generales, datos_componentes = extractores.extraer_todos_datos_factura(ruta_csv)
        
        # Paso 3: Procesar datos
        logger.info("Procesando datos extraídos")
        processor = procesamiento.FacturaProcessor(datos_generales, datos_componentes)
        datos_procesados = processor.obtener_datos_procesados()

        # Comparación con Base de Datos (Opcional)
        if fecha_seleccionada:
            try:
                logger.info(f"Consultando base de datos con fecha: {fecha_seleccionada}")
                # Import relativo para DBConnector
                from .db_connector import DBConnector
                connector = DBConnector()
                
                # Calcular último día del mes seleccionado
                fecha_obj = datetime.strptime(fecha_seleccionada, '%Y-%m-%d')
                ultimo_dia = calendar.monthrange(fecha_obj.year, fecha_obj.month)[1]
                fecha_fin = f"{fecha_obj.year}-{fecha_obj.month:02d}-{ultimo_dia:02d}"
                
                # Consultar la BD con el rango de fechas
                comparacion = connector.compare_with_facturas(
                    [datos_procesados], 
                    fecha_inicio=fecha_seleccionada,
                    fecha_fin=fecha_fin
                )
                
                # Añadir resultados de comparación a los datos procesados
                datos_procesados["comparacion_bd"] = comparacion.to_dict() if not comparacion.empty else {}
            except Exception as e:
                logger.warning(f"No se pudo realizar la comparación con BD: {e}")
        
        # Validar los datos
        validacion = datos_procesados["validacion"]
        if not validacion["es_valida"]:
            logger.warning(f"La factura tiene errores de validación: {validacion['errores']}")
        
        # Paso 4: Exportar a Excel
        if exportar_excel:
            ruta_excel = os.path.join(ruta_salida, f"{nombre_base}_analizado.xlsx")
            logger.info(f"Exportando a Excel: {ruta_excel}")
            exportador = exportacion.ExportadorExcel(datos_procesados, ruta_excel)
            ruta_excel_creada = exportador.exportar()
            logger.info(f"Archivo Excel creado: {ruta_excel_creada}")
        
        return datos_procesados
    
    except Exception as e:
        logger.error(f"Error al procesar la factura: {e}", exc_info=True)
        return None


def procesar_directorio(ruta_directorio, ruta_salida=None, fecha_seleccionada=None):
    """
    Procesa todos los archivos PDF en un directorio.
    """
    # Validar que el directorio exista
    if not os.path.exists(ruta_directorio):
        logger.error(f"El directorio {ruta_directorio} no existe.")
        return None
    
    # Crear directorio de salida si es necesario
    if ruta_salida:
        utils.crear_directorio_si_no_existe(ruta_salida)
    else:
        ruta_salida = os.path.join(ruta_directorio, "resultados")
        utils.crear_directorio_si_no_existe(ruta_salida)
    
    # Crear directorio para archivos CSV
    directorio_csv = os.path.join(ruta_salida, "csv")
    utils.crear_directorio_si_no_existe(directorio_csv)
    
    # Obtener lista de archivos PDF
    archivos_pdf = [f for f in os.listdir(ruta_directorio) if f.lower().endswith('.pdf')]
    
    if not archivos_pdf:
        logger.warning(f"No se encontraron archivos PDF en {ruta_directorio}")
        return None
    
    logger.info(f"Se encontraron {len(archivos_pdf)} archivos PDF para procesar")
    
    fecha_inicio = None
    fecha_fin = None
    if fecha_seleccionada:
        fecha_inicio = fecha_seleccionada
        fecha_obj = datetime.strptime(fecha_seleccionada, '%Y-%m-%d')
        ultimo_dia = calendar.monthrange(fecha_obj.year, fecha_obj.month)[1]
        fecha_fin = f"{fecha_obj.year}-{fecha_obj.month:02d}-{ultimo_dia:02d}"
        logger.info(f"Filtrando facturas por fecha: {fecha_inicio} a {fecha_fin}")

    # Usar la función de procesamiento múltiple del módulo exportación
    logger.info("Iniciando procesamiento consolidado de facturas")
    ruta_excel = exportacion.procesar_multiples_facturas(
        ruta_directorio, 
        ruta_salida=ruta_salida, 
        directorio_csv=directorio_csv,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    if ruta_excel:
        logger.info(f"Se ha creado el archivo Excel consolidado: {ruta_excel}")
        return ruta_excel
    else:
        logger.error("No se pudo crear el archivo Excel consolidado")
        return None

if __name__ == "__main__":
    # Este bloque solo se ejecuta si se llama al script directamente, no al importarlo
    parser = argparse.ArgumentParser(description='Procesador de facturas de energía (Ecopetrol)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--archivo', help='Ruta al archivo PDF de la factura')
    group.add_argument('-d', '--directorio', help='Directorio con archivos PDF de facturas')
    parser.add_argument('-o', '--output', help='Directorio donde se guardarán los resultados')
    
    args = parser.parse_args()
    
    if args.archivo:
        procesar_factura(args.archivo, args.output, True)
    elif args.directorio:
        procesar_directorio(args.directorio, args.output)