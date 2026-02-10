"""
Módulo principal de extracción.
Analiza las líneas de texto reconstruidas visualmente para extraer datos y tablas.
"""

import re
import logging
from .extractores_pdf import extraer_datos_estructurados
from .extractores_patrones import PATRONES_ENCABEZADO, PATRONES_MONTO, PATRONES_INFO_PIE, ENCABEZADOS_TABLA_ITEMS
from .utils import limpiar_moneda, limpiar_cantidad

logger = logging.getLogger(__name__)

def es_linea_totales(linea):
    """
    Detecta si la línea es un pie de tabla o resumen financiero.
    """
    linea_norm = re.sub(r'\s+', ' ', linea.lower()).strip()
    claves = [
        'total facturado', 'total a pagar', 'subtotal', 'son:', 'paguese', 
        'anticipo', 'intereses', 'saldo', 'total pagar', 'valor a pagar'
    ]
    return any(k in linea_norm for k in claves)

def es_numero_valido(token):
    """Verifica si un string parece un número."""
    if not re.search(r'\d', token):
        return False
    limpio = token.replace('$', '').replace(',', '').replace('.', '').replace(' ', '')
    return limpio.isdigit()

def parsear_linea_item(linea):
    """
    Intenta interpretar una línea de texto como un ítem de factura.
    """
    if es_linea_totales(linea):
        return None

    palabras = linea.split()
    if len(palabras) < 2:
        return None

    try:
        # --- PASO 1: ENCONTRAR INICIO ---
        idx_inicio_real = -1
        for i in range(min(len(palabras), 6)):
            token = palabras[i]
            if token.isdigit() and len(token) <= 3:
                idx_inicio_real = i
                break
        
        if idx_inicio_real == -1:
            idx_inicio_real = 0
            while idx_inicio_real < len(palabras) - 2:
                tok = palabras[idx_inicio_real]
                if len(tok) == 1 and not tok.isdigit() and tok.lower() not in ['a', 'y']:
                    idx_inicio_real += 1
                else:
                    break
        
        palabras_validas = palabras[idx_inicio_real:]
        if len(palabras_validas) < 2:
            return None

        item = {
            'item': '', 'referencia': '', 'concepto': '',
            'unidad': '', 'cantidad': 0, 'tarifa': 0, 'total': 0
        }

        # --- PASO 2: DESARMAR DESDE EL FINAL ---
        idx_cursor = len(palabras_validas) - 1
        encontrado_total = False
        
        for i in range(3):
            if idx_cursor < 0: break
            token = palabras_validas[idx_cursor]
            val = limpiar_moneda(token)
            if val > 0 and es_numero_valido(token):
                item['total'] = val
                encontrado_total = True
                idx_cursor -= 1 
                break
            idx_cursor -= 1
            
        if not encontrado_total: return None 

        if idx_cursor >= 0:
            token = palabras_validas[idx_cursor]
            if es_numero_valido(token):
                item['tarifa'] = limpiar_moneda(token)
                idx_cursor -= 1

        if idx_cursor >= 0:
            token = palabras_validas[idx_cursor]
            if es_numero_valido(token):
                item['cantidad'] = limpiar_cantidad(token)
                idx_cursor -= 1

        if idx_cursor >= 0:
            token = palabras_validas[idx_cursor]
            if len(token) <= 6 and not es_numero_valido(token):
                item['unidad'] = token
                idx_cursor -= 1

        # --- PASO 3: ANALIZAR EL INICIO ---
        idx_inicio = 0
        if idx_inicio <= idx_cursor:
            token = palabras_validas[idx_inicio]
            if token.isdigit() and len(token) <= 3:
                item['item'] = token
                idx_inicio += 1
        
        if idx_inicio <= idx_cursor:
            token = palabras_validas[idx_inicio]
            if len(token) <= 5 and (token.isupper() or any(c.isdigit() for c in token)):
                item['referencia'] = token
                idx_inicio += 1

        # --- PASO 4: CONCEPTO ---
        if idx_inicio <= idx_cursor:
            concepto_parts = palabras_validas[idx_inicio : idx_cursor + 1]
            item['concepto'] = " ".join(concepto_parts).strip()
        
        item['concepto'] = item['concepto'].strip(" .-,")
        
        if es_linea_totales(item['concepto']): return None
        if not item['concepto'] or len(item['concepto']) < 2: return None
            
        return item

    except Exception:
        return None

def extraer_datos_factura(ruta_pdf):
    """
    Proceso principal de extracción.
    """
    datos_paginas = extraer_datos_estructurados(ruta_pdf)
    todas_lineas = []
    for p in sorted(datos_paginas.keys()):
        todas_lineas.extend(datos_paginas[p])
    
    datos = {'datos_generales': {}, 'items': []}
    
    # --- CONFIGURACIÓN DE LÓGICA DE CLIENTE ---
    # Campos que son ESPECÍFICOS del cliente y se repiten para el emisor.
    KEYS_CLIENTE = [
        'nit_cliente', 'direccion_cliente', 'ciudad', 
        'telefono_cliente', 'email_cliente', 'cliente_nombre'
    ]
    
    # Palabras clave que indican que hemos llegado a la sección del cliente
    MARCADORES_CLIENTE = ['señores', 'datos del cliente', 'cliente:', 'adquirente']
    
    seccion_cliente_activa = False

    # --- RECORRIDO DE LÍNEAS PARA DATOS GENERALES ---
    for linea in todas_lineas:
        linea_lower = linea.lower()
        
        # 1. DETECTAR SI ENTRAMOS A LA SECCIÓN DEL CLIENTE
        # Si la línea contiene "Señores" o "Datos del cliente", activamos la bandera.
        if not seccion_cliente_activa:
            if any(m in linea_lower for m in MARCADORES_CLIENTE):
                seccion_cliente_activa = True
        
        # 2. HEADER (Patrones de Cabecera)
        for key, patron in PATRONES_ENCABEZADO.items():
            # SI el campo es del cliente y NO estamos en la sección cliente -> SALTAR (Ignora NIT emisor)
            if key in KEYS_CLIENTE and not seccion_cliente_activa:
                continue
                
            # Si ya tenemos el dato, no lo sobrescribimos (opcional, pero seguro si confiamos en la sección)
            if key not in datos['datos_generales']:
                match = patron.search(linea)
                if match:
                    if len(match.groups()) > 1:
                        val = f"{match.group(1)} al {match.group(2)}"
                    else:
                        val = match.group(1)
                    datos['datos_generales'][key] = val.strip()
        
        # 3. MONTOS FINANCIEROS
        for key, patron in PATRONES_MONTO.items():
            if key not in datos['datos_generales']:
                match = patron.search(linea)
                if match:
                    resto = linea[match.end():]
                    monto = limpiar_moneda(resto)
                    datos['datos_generales'][key] = monto

        # 4. INFO PIE DE PÁGINA
        for key, patron in PATRONES_INFO_PIE.items():
            if key not in datos['datos_generales']:
                match = patron.search(linea)
                if match:
                    val = match.group(1).strip()
                    datos['datos_generales'][key] = val

    # --- EXTRACCIÓN DE TABLA DE ÍTEMS ---
    en_tabla = False
    for linea in todas_lineas:
        if not en_tabla:
            coincidencias = sum(1 for h in ENCABEZADOS_TABLA_ITEMS if h.lower() in linea.lower())
            if coincidencias >= 2:
                en_tabla = True
                continue
        
        if en_tabla:
            if es_linea_totales(linea):
                en_tabla = False
                continue 
            
            item = parsear_linea_item(linea)
            if item:
                datos['items'].append(item)

    return datos