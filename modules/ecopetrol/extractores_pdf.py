"""
Módulo para conversión de archivos PDF a CSV.
Contiene las funciones necesarias para extraer y estructurar datos de PDFs.
"""

import os
import re
import csv
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser


def convertir_pdf_a_csv(ruta_pdf, ruta_salida=None):
    """
    Convierte un archivo PDF a formato CSV, preservando la estructura de columnas.
    
    Args:
        ruta_pdf (str): Ruta al archivo PDF
        ruta_salida (str, optional): Ruta donde se guardará el archivo CSV.
                                     Si es None, se usará el nombre del PDF con .csv.
    
    Returns:
        str: Ruta del archivo CSV creado
    """
    if ruta_salida is None:
        nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
        directorio = os.path.dirname(os.path.abspath(ruta_pdf))
        ruta_salida = os.path.join(directorio, f"{nombre_base}.csv")
    
    # Extraer datos organizados por filas y columnas
    datos_estructurados = extraer_datos_estructurados(ruta_pdf)
    
    # Guardar en archivo CSV
    with open(ruta_salida, 'w', encoding='utf-8', newline='') as archivo_csv:
        writer = csv.writer(archivo_csv)
        
        # Escribir datos
        for pagina, filas in datos_estructurados.items():
            # Escribir encabezado de página
            writer.writerow([f"PÁGINA {pagina}"])
            writer.writerow([])  # Línea vacía para separar
            
            # Escribir filas de datos
            for fila in filas:
                writer.writerow(fila)
            
            # Separador entre páginas
            writer.writerow([])
            writer.writerow([])
    
    return ruta_salida


def procesar_texto(texto):
    """
    Procesa el texto para separar números y valores que podrían estar juntos.
    
    Args:
        texto (str): Texto a procesar
        
    Returns:
        list: Lista de elementos separados
    """
    # Patrones para buscar en el texto
    patrones = [
        # Patrón para separar números con comas seguidos de otros números
        r'(\d[\d,.]+)\s+(\d[\d,.]+)',
        # separa texto de números
        r'([a-zA-Z]+[a-zA-Z\s]+)(\d[\d,.]+)'
    ]
    
    elementos = [texto]
    
    # Aplicar cada patrón
    for patron in patrones:
        nuevos_elementos = []
        for elem in elementos:
            # Verificar si el patrón coincide
            coincidencia = re.search(patron, elem)
            if coincidencia:
                # Separar el elemento según el patrón
                partes = re.split(patron, elem)
                # Filtrar elementos vacíos y agregar a la lista
                nuevos_elementos.extend([p.strip() for p in partes if p and p.strip()])
            else:
                nuevos_elementos.append(elem)
        elementos = nuevos_elementos
    
    # Eliminar duplicados y elementos vacíos
    return [e for e in elementos if e and e.strip()]


def extraer_datos_estructurados(ruta_pdf):
    """
    Extrae datos del PDF y los organiza en una estructura adecuada para CSV
    
    Args:
        ruta_pdf (str): Ruta al archivo PDF
    
    Returns:
        dict: Diccionario con páginas como claves y listas de filas como valores
    """
    datos_por_pagina = {}
    
    with open(ruta_pdf, 'rb') as f:
        parser = PDFParser(f)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        
        device = PDFPageAggregator(rsrcmgr, laparams=LAParams(
            line_margin=0.5,
            word_margin=0.1,
            boxes_flow=-1.0,  
            detect_vertical=True
        ))
        
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        
        page_num = 0
        for page in PDFPage.create_pages(doc):
            page_num += 1
            
            interpreter.process_page(page)
            layout = device.get_result()
            
            # Organizar elementos por posición Y para preservar filas
            elementos_por_y = {}
            
            for element in layout:
                if hasattr(element, 'get_text'):
                    # Redondear para agrupar líneas cercanas (en grupos de 10 unidades)
                    y = int(element.y0 / 10) * 10
                    if y not in elementos_por_y:
                        elementos_por_y[y] = []
                    elementos_por_y[y].append(element)
            
            filas_pagina = []
            
            # Ordenar por y descendente (de arriba hacia abajo)
            for y in sorted(elementos_por_y.keys(), reverse=True):
                # Ordenar elementos de izquierda a derecha en cada fila
                elementos = sorted(elementos_por_y[y], key=lambda e: e.x0)
                
                # Lista para almacenar todos los elementos procesados de la fila
                elementos_procesados = []
                
                for element in elementos:
                    texto = element.get_text().strip()
                    if texto:
                        # Procesar el texto para separar posibles números juntos
                        sub_elementos = procesar_texto(texto)
                        elementos_procesados.extend(sub_elementos)
                
                # Añadir fila si no está vacía
                if elementos_procesados:
                    filas_pagina.append(elementos_procesados)
            
            datos_por_pagina[page_num] = filas_pagina
    
    return datos_por_pagina


def analizar_estructura_columnas(datos_por_pagina):
    """
    Analiza la estructura de las columnas para intentar normalizar el número de columnas.
    Útil para determinar un encabezado si es necesario.
    
    Args:
        datos_por_pagina (dict): Datos estructurados por página
        
    Returns:
        int: Número máximo de columnas encontrado
    """
    max_columnas = 0
    
    for pagina, filas in datos_por_pagina.items():
        for fila in filas:
            max_columnas = max(max_columnas, len(fila))
    
    return max_columnas