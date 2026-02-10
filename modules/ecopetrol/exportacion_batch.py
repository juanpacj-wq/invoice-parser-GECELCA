"""
Módulo para el procesamiento por lotes de facturas.
Permite procesar múltiples facturas y exportarlas a un archivo Excel consolidado.
"""

import os
import logging
from datetime import datetime

# Configurar logger
logger = logging.getLogger(__name__)

def procesar_multiples_facturas(directorio_entrada, ruta_salida=None, directorio_csv=None, fecha_inicio=None, fecha_fin=None):
    """
    Procesa múltiples facturas en un directorio y las exporta a un solo archivo Excel.
    
    Args:
        directorio_entrada (str): Directorio con los archivos PDF de facturas
        ruta_salida (str, optional): Ruta donde se guardará el archivo Excel.
                                     Si es None, se usará 'facturas_analizadas.xlsx'.
        directorio_csv (str, optional): Directorio donde se guardarán los archivos CSV.
                                        Si es None, se usará 'csv' dentro del directorio de salida.
        fecha_inicio (str, optional): Fecha de inicio para filtrar las facturas en BD (YYYY-MM-DD)
        fecha_fin (str, optional): Fecha de fin para filtrar las facturas en BD (YYYY-MM-DD)
    
    Returns:
        str: Ruta del archivo Excel creado
    """
from . import extractores
from . import procesamiento
from .db_connector import DBConnector
    import pandas as pd
from .exportacion_excel_multiple import ExportadorExcelMultiple
    
    # Definir ruta de salida
    if ruta_salida is None:
        ruta_salida = os.path.join(os.path.dirname(directorio_entrada), "resultados")
    
    # Crear directorio de salida si no existe
    if not os.path.exists(ruta_salida):
        os.makedirs(ruta_salida)
    
    # Definir directorio para archivos CSV
    if directorio_csv is None:
        directorio_csv = os.path.join(ruta_salida, "csv")
    
    # Crear directorio para archivos CSV si no existe
    if not os.path.exists(directorio_csv):
        os.makedirs(directorio_csv)
    
    # Ruta del archivo Excel consolidado
    ruta_excel = os.path.join(ruta_salida, "facturas_analizadas.xlsx")
    
    # Obtener lista de archivos PDF
    archivos_pdf = [f for f in os.listdir(directorio_entrada) if f.lower().endswith('.pdf')]
    
    if not archivos_pdf:
        logger.warning(f"No se encontraron archivos PDF en el directorio {directorio_entrada}")
        return None
    
    # Crear exportador de Excel consolidado
    exportador = ExportadorExcelMultiple(ruta_excel)
    
    # Lista para guardar datos procesados para la comparación
    facturas_procesadas = []
    
    # Procesar cada factura
    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(directorio_entrada, archivo)
        
        # Validar archivo
        if not procesamiento.validar_ruta_archivo(ruta_pdf):
            logger.warning(f"Omitiendo archivo: {archivo}")
            continue
        
        # Extraer nombre base
        nombre_base = os.path.splitext(archivo)[0]
        
        # Convertir PDF a CSV (guardándolo en el directorio de CSV)
        ruta_csv = os.path.join(directorio_csv, f"{nombre_base}.csv")
        extractores.convertir_pdf_a_csv(ruta_pdf, ruta_csv)
        
        # Extraer datos del CSV
        datos_generales, datos_componentes = extractores.extraer_todos_datos_factura(ruta_csv)
        
        # Procesar datos
        processor = procesamiento.FacturaProcessor(datos_generales, datos_componentes)
        datos_procesados = processor.obtener_datos_procesados()
        
        # Agregar a Excel consolidado incluyendo el nombre del archivo
        factura_id = exportador.agregar_factura(datos_procesados, archivo)
        
        # Guardar el ID en los datos procesados para la comparación
        datos_procesados['id'] = factura_id
        facturas_procesadas.append(datos_procesados)
    
    if facturas_procesadas:
        # Imprimir información de diagnóstico
        for factura in facturas_procesadas:
            logger.info(f"Procesada factura con código SIC: {factura['datos_generales'].get('codigo_sic')}")
            logger.info(f"Período de facturación: {factura['datos_generales'].get('periodo_facturacion')}")
    
        # Realizar comparación con la base de datos
        try:
            # Usar el conector de base de datos
            db_connector = DBConnector()
            
            # Comparar con la base de datos usando fechas proporcionadas o extraídas de las facturas
            comparaciones_df = db_connector.compare_with_facturas(
                facturas_procesadas,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            # Agregar hoja de comparación si hay datos
            if not comparaciones_df.empty:
                exportador.agregar_hoja_comparacion(comparaciones_df)
                logger.info(f"Se agregó hoja de comparación con {len(comparaciones_df)} registros")
            else:
                logger.warning("No se encontraron datos para comparación con la base de datos")
        
        except Exception as e:
            logger.error(f"Error al comparar con la base de datos: {e}", exc_info=True)
    
    # Finalizar y guardar Excel
    ruta_final = exportador.finalizar()
    logger.info(f"Archivo Excel consolidado creado: {ruta_final}")
    
    return ruta_final