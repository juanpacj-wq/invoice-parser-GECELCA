"""
Módulo para extraer la tabla de componentes de energía de las facturas.
Soporta tanto el formato viejo como el nuevo de las facturas.
"""

import re
from .extractores_patrones import COMPONENTES_ENERGIA


def leer_archivo(file_path):
    """
    Lee el contenido de un archivo con manejo de codificaciones.
    
    Args:
        file_path (str): Ruta al archivo
        
    Returns:
        str: Contenido del archivo
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        # Intentar con otra codificación
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
    return content


def detectar_formato_tabla(content):
    """
    Detecta si la tabla de componentes está en formato nuevo o viejo.
    
    Args:
        content (str): Contenido del archivo CSV
    
    Returns:
        bool: True si es formato nuevo, False si es formato viejo
    """
    # Indicadores del formato nuevo
    indicadores_nuevo = [
        r'Tarifa\s*\$\/kWh',
        r'Ajustes\s+meses\s+anteriores',
        r'"Tarifa\s+\$\/kWh"',
        r'"Ajustes\s+meses"\s+"anteriores\s+\$"',
        r'EnergÃ­a\s+activa'  # Nuevo indicador para el formato con codificación alterada
    ]
    
    # Indicadores del formato viejo
    indicadores_viejo = [
        r'kWh\s+-\s+kVArh',
        r'Mes\s+anteriores\s+\$',
        r'kWh\s+-\s+kVArh,\$\/kWh'
    ]
    
    # Verificar indicadores del formato nuevo
    for indicador in indicadores_nuevo:
        if re.search(indicador, content, re.IGNORECASE):
            return True
    
    # Verificar indicadores del formato viejo
    for indicador in indicadores_viejo:
        if re.search(indicador, content, re.IGNORECASE):
            return False
    
    # Por defecto, asumir formato nuevo
    return True


def limpiar_valor(valor, es_decimal=False):
    """
    Limpia un valor eliminando caracteres innecesarios.
    
    Args:
        valor (str): Valor a limpiar
        es_decimal (bool): Si el valor debe mantener decimales
        
    Returns:
        str: Valor limpio
    """
    if not valor:
        return "0"
    
    # Eliminar comillas y espacios
    if isinstance(valor, str):
        valor = valor.replace('"', '').strip()
        
        # Si está vacío después de limpiar
        if not valor or valor == '-':
            return "0"
        
        # Para valores con .0 al final (formato nuevo)
        if not es_decimal and valor.endswith('.0'):
            valor = valor[:-2]
        
        # Eliminar comas de miles
        valor = valor.replace(',', '')
    
    return valor


def extraer_energia_valores(content):
    """
    Extrae los valores de energía activa y reactiva directamente del contenido.
    
    Args:
        content (str): Contenido del archivo CSV
        
    Returns:
        tuple: (energia_activa, energia_reactiva_total)
    """
    # Buscar valor de energía activa
    energia_activa_patterns = [
        r'Energ[ií]a\s+activa[,\s]+"?([0-9.,]+)"?', 
        r'EnergÃ­a\s+activa[,\s]+"?([0-9.,]+)"?', 
        r'"EnergÃ­a\tactiva,""([0-9.,]+)"""',
        r'EnergÃ­a\tactiva,([0-9.,]+)'
    ]
    
    energia_activa = "0"
    for pattern in energia_activa_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            energia_activa = match.group(1)
            break
    
    # Buscar valor de energía reactiva total
    energia_reactiva_patterns = [
        r'Total\s+energ[ií]a\s+reactiva[,\s]+"?([0-9.,]+)"?',
        r'Total\s+energÃ­a\s+reactiva[,\s]+"?([0-9.,]+)"?',
        r'"Total\tenergÃ­a\treactiva,([0-9.,]+)"',
        r'Total\tenergÃ­a\treactiva,([0-9.,]+)'
    ]
    
    energia_reactiva_total = "0"
    for pattern in energia_reactiva_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            energia_reactiva_total = match.group(1)
            break
    
    return limpiar_valor(energia_activa), limpiar_valor(energia_reactiva_total)


def procesar_componente_generacion(match, es_formato_nuevo, energia_activa=None):
    """
    Procesa específicamente el componente de Generación.
    
    Args:
        match: Objeto match de regex
        es_formato_nuevo (bool): Si es formato nuevo o viejo
        energia_activa (str, optional): Valor de energía activa extraído previamente
        
    Returns:
        dict: Diccionario con los datos del componente
    """
    concepto = {"concepto": "Generación"}
    
    # Usar el valor de energía activa extraído si está disponible
    if energia_activa is not None:
        concepto["kwh_kvarh"] = energia_activa
    elif es_formato_nuevo and len(match.groups()) == 4:
        # Formato nuevo sin kWh
        concepto["kwh_kvarh"] = "N/A"
    elif len(match.groups()) >= 5:
        # Formato viejo con kWh
        concepto["kwh_kvarh"] = limpiar_valor(match.group(1))
    else:
        # Formato ambiguo, intentar detectar
        concepto["kwh_kvarh"] = "N/A"
    
    # Procesar resto de campos
    if es_formato_nuevo and len(match.groups()) == 4:
        concepto["precio_kwh"] = limpiar_valor(match.group(1), es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(match.group(2))
        concepto["mes_anteriores"] = limpiar_valor(match.group(3))
        concepto["total"] = limpiar_valor(match.group(4))
    elif len(match.groups()) >= 5:
        concepto["precio_kwh"] = limpiar_valor(match.group(2), es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(match.group(3))
        concepto["mes_anteriores"] = limpiar_valor(match.group(4))
        concepto["total"] = limpiar_valor(match.group(5))
    else:
        concepto["precio_kwh"] = limpiar_valor(match.group(1), es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(match.group(2))
        concepto["mes_anteriores"] = limpiar_valor(match.group(3))
        concepto["total"] = limpiar_valor(match.group(4) if len(match.groups()) > 3 else "0")
    
    return concepto


def procesar_componente_energia_inductiva(match, es_formato_nuevo, energia_reactiva_total=None):
    """
    Procesa específicamente el componente de Energía inductiva + capacitiva.
    
    Args:
        match: Objeto match de regex
        es_formato_nuevo (bool): Si es formato nuevo o viejo
        energia_reactiva_total (str, optional): Valor de energía reactiva total extraído previamente
        
    Returns:
        dict: Diccionario con los datos del componente
    """
    concepto = {"concepto": "Energía inductiva + capacitiva"}
    
    # Usar el valor de energía reactiva total extraído si está disponible
    if energia_reactiva_total is not None:
        concepto["kwh_kvarh"] = energia_reactiva_total
    elif es_formato_nuevo and len(match.groups()) == 4:
        # Formato nuevo sin kWh
        concepto["kwh_kvarh"] = "N/A"
    elif len(match.groups()) >= 5:
        # Formato viejo con kWh
        concepto["kwh_kvarh"] = limpiar_valor(match.group(1))
    else:
        # Formato ambiguo
        concepto["kwh_kvarh"] = "N/A"
    
    # Procesar resto de campos
    if es_formato_nuevo and len(match.groups()) == 4:
        concepto["precio_kwh"] = limpiar_valor(match.group(1), es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(match.group(2))
        concepto["mes_anteriores"] = limpiar_valor(match.group(3))
        concepto["total"] = limpiar_valor(match.group(4))
    elif len(match.groups()) >= 5:
        concepto["precio_kwh"] = limpiar_valor(match.group(2), es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(match.group(3))
        concepto["mes_anteriores"] = limpiar_valor(match.group(4))
        concepto["total"] = limpiar_valor(match.group(5))
    else:
        concepto["precio_kwh"] = limpiar_valor(match.group(1), es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(match.group(2))
        concepto["mes_anteriores"] = limpiar_valor(match.group(3))
        concepto["total"] = limpiar_valor(match.group(4) if len(match.groups()) > 3 else "0")
    
    return concepto


def procesar_componente_standard(match, nombre_componente):
    """
    Procesa componentes estándar (sin kWh).
    
    Args:
        match: Objeto match de regex
        nombre_componente (str): Nombre del componente
        
    Returns:
        dict: Diccionario con los datos del componente
    """
    concepto = {
        "concepto": nombre_componente,
        "kwh_kvarh": "N/A",
        "precio_kwh": limpiar_valor(match.group(1), es_decimal=True),
        "mes_corriente": limpiar_valor(match.group(2)),
        "mes_anteriores": limpiar_valor(match.group(3)),
        "total": limpiar_valor(match.group(4))
    }
    
    # Manejar valores negativos correctamente
    if concepto["mes_anteriores"].startswith('-'):
        concepto["mes_anteriores"] = "-" + concepto["mes_anteriores"][1:].replace('-', '')
    if concepto["total"].startswith('-'):
        concepto["total"] = "-" + concepto["total"][1:].replace('-', '')
    
    return concepto


def extraer_tabla_componentes(file_path):
    """
    Extrae los datos de la tabla de componentes de energía.
    Soporta tanto el formato viejo como el nuevo de las facturas.
    
    Args:
        file_path (str): Ruta al archivo CSV de la factura
        
    Returns:
        list: Lista de diccionarios con los datos de los componentes
    """
    content = leer_archivo(file_path)
    
    # Detectar formato de la tabla
    es_formato_nuevo = detectar_formato_tabla(content)
    
    # Extraer valores de energía activa y reactiva total directamente del contenido
    energia_activa, energia_reactiva_total = extraer_energia_valores(content)
    
    concepto_data = []
    componentes_encontrados = set()
    
    # Extraer cada componente usando los patrones definidos
    for component in COMPONENTES_ENERGIA:
        nombre = component["name"]
        
        # Si ya encontramos este componente, saltar
        if nombre in componentes_encontrados:
            continue
        
        # Probar cada patrón del componente
        for pattern in component.get("patterns", []):
            match = re.search(pattern, content)
            
            if match:
                concepto = None
                
                # Procesar según el tipo de componente
                if nombre == "Generación":
                    concepto = procesar_componente_generacion(match, es_formato_nuevo, energia_activa)
                elif nombre == "Energía inductiva + capacitiva":
                    concepto = procesar_componente_energia_inductiva(match, es_formato_nuevo, energia_reactiva_total)
                else:
                    concepto = procesar_componente_standard(match, nombre)
                
                if concepto:
                    concepto_data.append(concepto)
                    componentes_encontrados.add(nombre)
                    break  # Salir del loop de patrones si encontramos uno
    
    # Si faltan componentes, intentar extracción línea por línea
    if len(concepto_data) < 8:
        extraer_componentes_linea_por_linea(content, concepto_data, componentes_encontrados, es_formato_nuevo, 
                                           energia_activa, energia_reactiva_total)
    
    return concepto_data


def extraer_componentes_linea_por_linea(content, concepto_data, componentes_encontrados, es_formato_nuevo, 
                                       energia_activa=None, energia_reactiva_total=None):
    """
    Extrae componentes procesando el contenido línea por línea.
    
    Args:
        content (str): Contenido del archivo
        concepto_data (list): Lista de conceptos ya encontrados
        componentes_encontrados (set): Set de nombres de componentes ya encontrados
        es_formato_nuevo (bool): Si es formato nuevo o viejo
        energia_activa (str, optional): Valor de energía activa extraído previamente
        energia_reactiva_total (str, optional): Valor de energía reactiva total extraído previamente
    """
    lines = content.split('\n')
    
    for line in lines:
        # Buscar líneas que empiecen con número y punto (componentes)
        if not re.match(r'^\d+\.', line):
            continue
        
        # Parsear la línea respetando las comillas
        parts = []
        in_quotes = False
        current_part = ""
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part:
            parts.append(current_part.strip())
        
        # Identificar el componente
        component_name = identificar_componente(parts[0] if parts else "")
        
        # Si identificamos el componente y no lo tenemos ya
        if component_name and component_name not in componentes_encontrados:
            concepto = procesar_linea_componente(parts, component_name, es_formato_nuevo, 
                                               energia_activa, energia_reactiva_total)
            if concepto:
                concepto_data.append(concepto)
                componentes_encontrados.add(component_name)


def identificar_componente(texto):
    """
    Identifica el nombre del componente basado en el texto.
    
    Args:
        texto (str): Texto de la primera columna
        
    Returns:
        str: Nombre del componente o None
    """
    componentes_map = {
        '1.': ('Generación', ['Generación', 'Generacion', 'GeneraciÃ³n']),
        '2.': ('Comercialización', ['Comercialización', 'Comercializacion', 'ComercializaciÃ³n']),
        '3.': ('Transmisión', ['Transmisión', 'Transmision', 'TransmisiÃ³n']),
        '4.': ('Distribución', ['Distribución', 'Distribucion', 'DistribuciÃ³n']),
        '5.': ('Pérdidas', ['Perdidas', 'Pérdidas', 'PÃ©rdidas']),
        '6.': ('Restricciones', ['Restricciones', 'RestricciÃ³n']),
        '7.': ('Otros cargos', ['Otros', 'Otro']),
        '8.': ('Energía inductiva + capacitiva', ['inductiva', 'capacitiva', 'EnergÃ­a'])
    }
    
    for prefix, (nombre, keywords) in componentes_map.items():
        if prefix in texto:
            for keyword in keywords:
                if keyword.lower() in texto.lower():
                    return nombre
    
    return None


def procesar_linea_componente(parts, component_name, es_formato_nuevo, 
                            energia_activa=None, energia_reactiva_total=None):
    """
    Procesa una línea de componente parseada.
    
    Args:
        parts (list): Partes de la línea separadas por comas
        component_name (str): Nombre del componente
        es_formato_nuevo (bool): Si es formato nuevo o viejo
        energia_activa (str, optional): Valor de energía activa extraído previamente
        energia_reactiva_total (str, optional): Valor de energía reactiva total extraído previamente
        
    Returns:
        dict: Diccionario con los datos del componente
    """
    if len(parts) < 4:
        return None
    
    concepto = {"concepto": component_name}
    
    # Determinar estructura según el componente y cantidad de partes
    if component_name == "Generación":
        # Usar el valor de energía activa extraído si está disponible
        if energia_activa is not None:
            concepto["kwh_kvarh"] = energia_activa
        elif len(parts) >= 5 and not es_formato_nuevo:
            # Posible formato viejo con kWh
            concepto["kwh_kvarh"] = limpiar_valor(parts[1])
        else:
            concepto["kwh_kvarh"] = "N/A"
    elif component_name == "Energía inductiva + capacitiva":
        # Usar el valor de energía reactiva total extraído si está disponible
        if energia_reactiva_total is not None:
            concepto["kwh_kvarh"] = energia_reactiva_total
        elif len(parts) >= 5 and not es_formato_nuevo:
            concepto["kwh_kvarh"] = limpiar_valor(parts[1])
        else:
            concepto["kwh_kvarh"] = "N/A"
    else:
        concepto["kwh_kvarh"] = "N/A"
    
    # Determinar posiciones de los otros campos basados en si hay kWh o no
    if len(parts) >= 5 and not es_formato_nuevo and component_name in ["Generación", "Energía inductiva + capacitiva"]:
        concepto["precio_kwh"] = limpiar_valor(parts[2], es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(parts[3])
        concepto["mes_anteriores"] = limpiar_valor(parts[4])
        concepto["total"] = limpiar_valor(parts[5] if len(parts) > 5 else "0")
    else:
        # Formato estándar o nuevo
        concepto["precio_kwh"] = limpiar_valor(parts[1], es_decimal=True)
        concepto["mes_corriente"] = limpiar_valor(parts[2])
        concepto["mes_anteriores"] = limpiar_valor(parts[3])
        concepto["total"] = limpiar_valor(parts[4] if len(parts) > 4 else "0")
    
    return concepto