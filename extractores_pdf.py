"""
Módulo para conversión de archivos PDF a CSV.
Utiliza ordenamiento manual de líneas de texto (LTTextLine) para reconstruir filas.
"""

import os
import csv
import logging
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LAParams

logger = logging.getLogger(__name__)

def convertir_pdf_a_csv(ruta_pdf, ruta_salida=None):
    """
    Convierte el contenido visual del PDF a un archivo CSV.
    """
    if ruta_salida is None:
        nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
        directorio = os.path.dirname(os.path.abspath(ruta_pdf))
        csv_dir = os.path.join(directorio, "csv")
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
        ruta_salida = os.path.join(csv_dir, f"{nombre_base}.csv")
    
    try:
        datos_paginas = extraer_datos_estructurados(ruta_pdf)
        
        with open(ruta_salida, 'w', encoding='utf-8', newline='') as archivo_csv:
            writer = csv.writer(archivo_csv)
            writer.writerow(["--- TEXTO RECONSTRUIDO (LÍNEAS) ---"])
            
            for num_pag, lineas in datos_paginas.items():
                writer.writerow([f"PÁGINA {num_pag}"])
                for linea in lineas:
                    writer.writerow([linea])
                writer.writerow([])
            
        return ruta_salida
        
    except Exception as e:
        logger.error(f"Error al convertir PDF a CSV: {e}")
        return None

def obtener_lineas_planas(layout_object):
    """
    Función recursiva para extraer todas las LTTextLine de un contenedor.
    """
    lineas = []
    if isinstance(layout_object, LTTextLine):
        lineas.append(layout_object)
    elif isinstance(layout_object, LTTextBox):
        for child in layout_object:
            lineas.extend(obtener_lineas_planas(child))
    elif hasattr(layout_object, '__iter__'):
        for child in layout_object:
            lineas.extend(obtener_lineas_planas(child))
    return lineas

def extraer_datos_estructurados(ruta_pdf):
    """
    Extrae texto agrupando líneas visualmente por su coordenada Y.
    """
    datos_por_pagina = {}
    
    try:
        laparams = LAParams(all_texts=True, boxes_flow=None)
        
        for i, page_layout in enumerate(extract_pages(ruta_pdf, laparams=laparams)):
            num_pag = i + 1
            
            # 1. Obtener todas las líneas
            todas_las_lineas = []
            for element in page_layout:
                todas_las_lineas.extend(obtener_lineas_planas(element))
            
            if not todas_las_lineas:
                datos_por_pagina[num_pag] = []
                continue

            # 2. Ordenar por posición vertical
            todas_las_lineas.sort(key=lambda l: (l.y0 + l.y1) / 2, reverse=True)
            
            # 3. Agrupar líneas (Tolerancia ajustada a 4.0 para evitar basura vertical)
            filas_texto = []
            if todas_las_lineas:
                grupo_actual = [todas_las_lineas[0]]
                y_referencia = (todas_las_lineas[0].y0 + todas_las_lineas[0].y1) / 2
                tolerancia_y = 4.0 # Más estricto
                
                for linea in todas_las_lineas[1:]:
                    y_centro = (linea.y0 + linea.y1) / 2
                    
                    if abs(y_centro - y_referencia) < tolerancia_y:
                        grupo_actual.append(linea)
                    else:
                        # Procesar grupo anterior
                        grupo_actual.sort(key=lambda l: l.x0)
                        texto_fila = " ".join([l.get_text().strip() for l in grupo_actual if l.get_text().strip()])
                        if texto_fila:
                            filas_texto.append(texto_fila)
                        
                        grupo_actual = [linea]
                        y_referencia = y_centro
                
                # Último grupo
                grupo_actual.sort(key=lambda l: l.x0)
                texto_fila = " ".join([l.get_text().strip() for l in grupo_actual if l.get_text().strip()])
                if texto_fila:
                    filas_texto.append(texto_fila)
            
            datos_por_pagina[num_pag] = filas_texto
            
        return datos_por_pagina

    except Exception as e:
        logger.error(f"Error crítico en extracción visual: {e}")
        return {}