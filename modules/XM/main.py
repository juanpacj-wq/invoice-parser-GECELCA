#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script principal para el procesamiento masivo de facturas de Gecelca/Air-e.
Genera un archivo consolidado (Append) con la información de todos los PDFs procesados.
"""

import os
import argparse
import logging
import time

# Importar módulos del proyecto
from . import extractores_pdf
from . import extractores
from . import procesamiento
from . import exportacion
from . import utils

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("procesador_consolidado.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def procesar_pdf_a_datos(ruta_pdf):
    """
    Ejecuta el pipeline de extracción para un solo PDF y retorna los datos estructurados
    (sin exportar a Excel todavía).
    """
    try:
        nombre_base = utils.obtener_nombre_archivo_sin_extension(ruta_pdf)
        logger.info(f"--- Leyendo: {nombre_base} ---")

        # 1. Reconstrucción Visual (PDF -> CSV interno)
        # extractores_pdf.convertir_pdf_a_csv(ruta_pdf) # Descomentar si se quiere depurar el CSV
        
        # 2. Extracción de Datos Crudos
        datos_crudos = extractores.extraer_datos_factura(ruta_pdf)
        
        # Inyectar nombre de archivo
        if 'datos_generales' not in datos_crudos:
            datos_crudos['datos_generales'] = {}
        datos_crudos['datos_generales']['nombre_archivo'] = f"{nombre_base}.pdf"
        
        # 3. Procesamiento y Estructuración
        processor = procesamiento.FacturaProcessor(datos_crudos)
        datos_finales = processor.obtener_datos_procesados()
        
        return datos_finales

    except Exception as e:
        logger.error(f"Error crítico en {ruta_pdf}: {e}", exc_info=True)
        return None

def procesar_directorio_consolidado(directorio_entrada, directorio_salida=None):
    """
    Procesa todos los PDFs y genera UN SOLO Excel consolidado.
    """
    if not os.path.exists(directorio_entrada):
        logger.error(f"El directorio no existe: {directorio_entrada}")
        return

    if not directorio_salida:
        directorio_salida = os.path.join(directorio_entrada, "Resultados_Consolidados")
    
    utils.crear_directorio_si_no_existe(directorio_salida)

    archivos = [f for f in os.listdir(directorio_entrada) if f.lower().endswith('.pdf')]
    total = len(archivos)
    
    if total == 0:
        logger.warning("No se encontraron archivos PDF.")
        return

    logger.info(f"Iniciando consolidación de {total} archivos...")
    start_time = time.time()
    
    # --- ACUMULADORES (Listas Maestras) ---
    acumulado_conceptos = []
    acumulado_generales = []
    acumulado_comparacion = []
    acumulado_validacion = []
    
    exitosos = 0
    fallidos = 0
    
    for i, archivo in enumerate(archivos, 1):
        ruta_completa = os.path.join(directorio_entrada, archivo)
        print(f"Procesando [{i}/{total}]: {archivo}")
        
        datos = procesar_pdf_a_datos(ruta_completa)
        
        if datos:
            # Append a las listas maestras
            acumulado_conceptos.extend(datos['conceptos'])
            acumulado_generales.extend(datos['generales'])
            acumulado_comparacion.extend(datos['comparacion'])
            
            # Log de validación
            val = datos['validacion']
            log_entry = {
                'Fecha Proceso': time.strftime("%Y-%m-%d %H:%M:%S"),
                'Archivo': archivo,
                'No. Factura': val.get('factura', 'N/A'),
                'Es Válida': "SÍ" if val.get('es_valida') else "NO",
                'Errores': "; ".join(val.get('errores', [])) if val.get('errores') else "Ninguno"
            }
            acumulado_validacion.append(log_entry)
            
            exitosos += 1
        else:
            fallidos += 1
            acumulado_validacion.append({
                'Fecha Proceso': time.strftime("%Y-%m-%d %H:%M:%S"),
                'Archivo': archivo,
                'Es Válida': "ERROR CRÍTICO",
                'Errores': "Fallo en lectura del archivo"
            })

    # --- EXPORTACIÓN FINAL ---
    if exitosos > 0:
        logger.info("Generando Excel Consolidado...")
        
        datos_consolidados = {
            'conceptos': acumulado_conceptos,
            'generales': acumulado_generales,
            'comparacion': acumulado_comparacion,
            'validacion': acumulado_validacion # Pasamos la lista acumulada
        }
        
        nombre_consolidado = f"Consolidado_Gecelca_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
        ruta_excel = os.path.join(directorio_salida, nombre_consolidado)
        
        exportador = exportacion.ExportadorExcel(datos_consolidados, ruta_excel)
        exportador.exportar()
        
        logger.info(f"¡Éxito! Archivo maestro guardado en: {ruta_excel}")
    else:
        logger.error("No se pudo procesar ningún archivo correctamente.")

    elapsed_time = time.time() - start_time
    logger.info(f"Resumen: {exitosos} procesados, {fallidos} fallidos. Tiempo: {elapsed_time:.2f}s")

def procesar_individual(ruta_pdf, directorio_salida=None):
    """
    Procesa un solo archivo (wrapper para mantener compatibilidad con -a).
    """
    if not directorio_salida:
        directorio_salida = os.path.dirname(os.path.abspath(ruta_pdf))
    
    nombre_base = utils.obtener_nombre_archivo_sin_extension(ruta_pdf)
    ruta_excel = os.path.join(directorio_salida, f"{nombre_base}_procesado.xlsx")
    
    datos = procesar_pdf_a_datos(ruta_pdf)
    
    if datos:
        exportador = exportacion.ExportadorExcel(datos, ruta_excel)
        exportador.exportar()
        logger.info(f"Archivo individual generado: {ruta_excel}")
    else:
        logger.error("Fallo al procesar el archivo individual.")

def main():
    parser = argparse.ArgumentParser(description='Procesador Consolidado de Facturas')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--archivo', help='Procesar un solo archivo')
    group.add_argument('-d', '--directorio', help='Procesar directorio completo y consolidar')
    
    parser.add_argument('-o', '--output', help='Directorio de salida (opcional)')
    
    args = parser.parse_args()
    
    if args.archivo:
        procesar_individual(args.archivo, args.output)
    elif args.directorio:
        procesar_directorio_consolidado(args.directorio, args.output)

if __name__ == "__main__":
    main()