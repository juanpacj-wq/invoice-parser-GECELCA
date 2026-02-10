"""
Módulo principal para extracción de datos de facturas en formato PDF y CSV.
Este módulo coordina las funciones de los módulos especializados.
"""

import re

# Importar funciones de los módulos especializados
from .extractores_patrones import (
    PATRONES_CONCEPTO,
    PATRONES_PARAMETROS_ESPECIFICOS
)
from .extractores_pdf import (
    convertir_pdf_a_csv,
    procesar_texto,
    extraer_datos_estructurados,
    analizar_estructura_columnas
)
from .extractores_componentes import (
    extraer_tabla_componentes,
    leer_archivo,
    extraer_energia_valores
)


def extraer_valores_hes(content):
    """
    Extrae los valores HES del contenido, asegurando que solo se extraigan valores numéricos.
    
    Args:
        content (str): Contenido del archivo CSV
        
    Returns:
        dict: Diccionario con los valores HES extraídos (solo números)
    """
    # Inicializar diccionario con valores vacíos para todas las autorizaciones
    results = {
        'hes1': "0", 'hes2': "0", 'hes3': "0", 'hes4': "0", 'hes5': "0",
        'hes6': "0", 'hes7': "0", 'hes8': "0", 'hes9': "0", 'hes10': "0"
    }
    
    # Patrones para cada HES (1-10)
    for i in range(1, 11):
        # Crear varios patrones para cada HES
        patrones = [
            rf'HES{i}:[\t\s]*(\d+)',             # Formato básico: HES1: 12345
            rf'HES{i}[\t\s]*:[\t\s]*(\d+)',      # Variante con espacios
            rf'HES[\t\s,]+{i}[\t\s,]*:[\t\s]*(\d+)'  # Formato con separación: HES, 10, : 12345
        ]
        
        # Intentar los patrones para este HES
        for patron in patrones:
            match = re.search(patron, content)
            if match:
                # Extraer solo el valor numérico
                value = match.group(1).strip()
                # Verificar que sea numérico
                if value.isdigit():
                    results[f'hes{i}'] = value
                    break  # Si encontramos un valor numérico, podemos parar
    
    return results


def extraer_parametros_especificos(content):
    """
    Extrae los parámetros específicos como IR, Grupo, DIU INT, etc.
    
    Args:
        content (str): Contenido del archivo CSV
        
    Returns:
        dict: Diccionario con los parámetros específicos extraídos
    """
    # Inicializar diccionario con valores por defecto (todos numéricos)
    parametros = {
        'ir': "0",
        'grupo': "0",
        'diu_int': "0",
        'dium_int': "0",
        'fiu_int': "0",
        'fium_int': "0",
        'fiug': "0",
        'diug': "0"
    }

    # LÓGICA ESPECIAL PARA IR - Verificar primero si está vacío
    # Buscar el patrón "IR:,Grupo:" que indica que IR está vacío
    if re.search(r'IR:\s*,\s*Grupo:', content):
        # IR está vacío, mantener el valor por defecto "0"
        parametros['ir'] = "0"
    else:
        # IR no está vacío, intentar extraer su valor
        for patron in PATRONES_PARAMETROS_ESPECIFICOS['ir'][1:]:  # Omitir el primer patrón de detección
            match = re.search(patron, content)
            if match:
                value = match.group(1)
                # Limpiar el valor para asegurarse de que sea numérico
                cleaned_value = re.sub(r'[^0-9.]', '', value)
                if cleaned_value:
                    parametros['ir'] = cleaned_value
                    break

    # Patrones combinados para DIU/DIUM y FIU/FIUM
    match_diu = re.search(PATRONES_PARAMETROS_ESPECIFICOS['diu_dium_int'][0], content)
    if match_diu:
        parametros['diu_int'] = match_diu.group(1)
        parametros['dium_int'] = match_diu.group(2)

    match_fiu = re.search(PATRONES_PARAMETROS_ESPECIFICOS['fiu_fium_int'][0], content)
    if match_fiu:
        parametros['fiu_int'] = match_fiu.group(1)
        parametros['fium_int'] = match_fiu.group(2)

    # Patrones individuales para los que no se encontraron en pareja (excepto IR que ya fue procesado)
    for key in ['grupo', 'diu_int', 'dium_int', 'fiu_int', 'fium_int', 'fiug', 'diug']:
        if parametros[key] == "0": # Solo buscar si no se ha encontrado ya
            for patron in PATRONES_PARAMETROS_ESPECIFICOS[key]:
                match = re.search(patron, content)
                if match:
                    # Para patrones combinados como fiug_diug, puede haber más de un grupo
                    if key == 'fiug' and 'DIUG' in patron:
                        parametros['fiug'] = match.group(1)
                        parametros['diug'] = match.group(2)
                        break # Salir del bucle de patrones para esta clave
                    elif key == 'diug' and 'FIUG' in patron:
                        parametros['fiug'] = match.group(1)
                        parametros['diug'] = match.group(2)
                        break # Salir del bucle de patrones para esta clave
                    else:
                        value = match.group(1)
                        # Limpiar el valor para asegurarse de que sea numérico
                        cleaned_value = re.sub(r'[^0-9.]', '', value)
                        if cleaned_value:
                            parametros[key] = cleaned_value
                            break # Salir del bucle de patrones para esta clave
    
    return parametros


def extraer_datos_factura(file_path):
    """
    Extrae los datos generales de la factura desde un archivo CSV.
    
    Args:
        file_path (str): Ruta al archivo CSV de la factura
        
    Returns:
        dict: Diccionario con los datos extraídos de la factura
    """
    content = leer_archivo(file_path)
    
    # Extraer información principal
    fecha_vencimiento_match = re.search(r'Fecha\s+vencimiento:\s+(\d{4}-\d{2}-\d{2})', content)
    fecha_vencimiento = fecha_vencimiento_match.group(1) if fecha_vencimiento_match else "No encontrado"
    
    periodo_facturacion_match = re.search(r'Período\s+Facturación:\s+(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})', content)
    if periodo_facturacion_match:
        periodo_facturacion = f"{periodo_facturacion_match.group(1)} a {periodo_facturacion_match.group(2)}"
    else:
        # Try alternative format
        alt_match = re.search(r'Período\s+Facturación:\s+(\d{4}-\d{2}-\d{2})', content)
        periodo_facturacion = alt_match.group(1) if alt_match else "No encontrado"
    
    factor_m_match = re.search(r'Factor\s+M:\s+(\d+)', content)
    factor_m = factor_m_match.group(1) if factor_m_match else "No encontrado"
    
    # Extraer código SIC
    codigo_sic_match = re.search(r'Código\s+SIC:.*?([A-Za-z]+)[,\s]*(\d+)', content)
    if codigo_sic_match:
        # Concatenar el prefijo de letras y los números
        prefijo = codigo_sic_match.group(1)
        numeros = codigo_sic_match.group(2)
        codigo_sic = f"{prefijo}{numeros}"
    else:
        codigo_sic = "No encontrado"
    
    # Extraer número de factura
    numero_factura_patrones = [
        r'FACTURA\s+ELECTR[ÓO]NICA\s+DE\s+VENTA\s+SERVICIO\s+P[ÚU]BLICO:.*?No\.\s+([A-Za-z0-9]+)',
        r'FACTURA\s+ELECTR[ÓO]NICA\s+DE\s+VENTA\s+SERVICIO\s+P[ÚU]BLICO:,No\.\s+([A-Za-z0-9]+)',
        r'No\.\s+([A-Za-z0-9]+)'
    ]
    
    numero_factura = "No encontrado"
    for patron in numero_factura_patrones:
        match = re.search(patron, content, re.IGNORECASE)
        if match:
            numero_factura = match.group(1)
            break
    
    # Initialize results dictionary with the main variables
    results = {
        "fecha_vencimiento": fecha_vencimiento,
        "periodo_facturacion": periodo_facturacion,
        "factor_m": factor_m,
        "codigo_sic": codigo_sic,
        "numero_factura": numero_factura,
    }
    
    # Extract all the financial variables
    for var_name, patterns in PATRONES_CONCEPTO.items():
        # Skip subtotal_energia_contribucion_pesos since it will be calculated later
        if var_name == "subtotal_energia_contribucion_pesos":
            continue
        
        value = "No encontrado"
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                # Clean the captured value
                captured_value = match.group(1)
                # Remove commas at the beginning of the value
                if captured_value.startswith(','):
                    captured_value = captured_value[1:]
                value = captured_value
                break
        results[var_name] = value
    
    # Intentar extraer subtotal_energia_contribucion_pesos directamente usando patrones
    for pattern in PATRONES_CONCEPTO['subtotal_energia_contribucion_pesos']:
        match = re.search(pattern, content)
        if match:
            # Clean the captured value
            captured_value = match.group(1)
            # Remove commas at the beginning of the value
            if captured_value.startswith(','):
                captured_value = captured_value[1:]
            results["subtotal_energia_contribucion_pesos"] = captured_value
            break
    
    # Si no se encontró, calcular subtotal_energia_contribucion_pesos como la suma de subtotal_base_energia y contribucion
    if "subtotal_energia_contribucion_pesos" not in results or results["subtotal_energia_contribucion_pesos"] == "No encontrado":
        try:
            # Convertir valores a números, eliminando las comas
            subtotal_base = int(results["subtotal_base_energia"].replace(',', '').replace('"', '')) if results["subtotal_base_energia"] != "No encontrado" else 0
            contribucion = int(results["contribucion"].replace(',', '').replace('"', '')) if results["contribucion"] != "No encontrado" else 0
            
            # Calcular la suma
            subtotal_energia_contribucion_pesos = subtotal_base + contribucion
            
            # Formatear el resultado con comas para miles
            results["subtotal_energia_contribucion_pesos"] = f"{subtotal_energia_contribucion_pesos:,}"
        except (ValueError, KeyError):
            # En caso de error, establecer un valor por defecto
            results["subtotal_energia_contribucion_pesos"] = "No encontrado"
    
    # Extraer valores HES (autorizaciones)
    hes_values = extraer_valores_hes(content)
    results.update(hes_values)
    
    # Extraer parámetros específicos (IR, Grupo, DIU INT, etc.)
    parametros_especificos = extraer_parametros_especificos(content)
    results.update(parametros_especificos)
    
    # Extraer directamente los valores de energía activa y reactiva
    energia_activa, energia_reactiva_total = extraer_energia_valores(content)
    
    # Asegurarse de que los valores de energía reactiva inductiva y capacitiva sumen el total
    # Si tenemos total_energia_reactiva pero no tenemos uno de los componentes
    if results["total_energia_reactiva"] != "No encontrado" and energia_reactiva_total != "0":
        # Actualizar el total con el valor extraído directamente
        results["total_energia_reactiva"] = energia_reactiva_total
        
        # Si tenemos energía reactiva inductiva pero no capacitiva
        if results["energia_reactiva_inductiva"] != "No encontrado" and results["energia_reactiva_capacitiva"] == "No encontrado":
            # Calcular la capacitiva como la diferencia
            try:
                total = float(energia_reactiva_total)
                inductiva = float(results["energia_reactiva_inductiva"].replace(',', '').replace('"', ''))
                capacitiva = total - inductiva
                results["energia_reactiva_capacitiva"] = str(max(0, capacitiva))
            except (ValueError, TypeError):
                pass
        
        # Si tenemos energía reactiva capacitiva pero no inductiva
        elif results["energia_reactiva_capacitiva"] != "No encontrado" and results["energia_reactiva_inductiva"] == "No encontrado":
            # Calcular la inductiva como la diferencia
            try:
                total = float(energia_reactiva_total)
                capacitiva = float(results["energia_reactiva_capacitiva"].replace(',', '').replace('"', ''))
                inductiva = total - capacitiva
                results["energia_reactiva_inductiva"] = str(max(0, inductiva))
            except (ValueError, TypeError):
                pass
    
    # Actualizar también el valor de energía activa
    if results.get("energia_activa", "No encontrado") == "No encontrado" and energia_activa != "0":
        results["energia_activa"] = energia_activa
    
    return results


def extraer_todos_datos_factura(file_path):
    """
    Extrae todos los datos de la factura, combinando datos generales y tabla de componentes.
    
    Args:
        file_path (str): Ruta al archivo CSV de la factura
        
    Returns:
        tuple: Tupla con (datos_generales, datos_componentes)
    """
    datos_generales = extraer_datos_factura(file_path)
    datos_componentes = extraer_tabla_componentes(file_path)
    
    return datos_generales, datos_componentes


# Re-exportar las funciones que antes estaban en este archivo
# para mantener compatibilidad con el resto del código
__all__ = [
    'convertir_pdf_a_csv',
    'procesar_texto',
    'extraer_datos_estructurados',
    'analizar_estructura_columnas',
    'leer_archivo',
    'extraer_valores_hes',
    'extraer_parametros_especificos',
    'extraer_datos_factura',
    'extraer_tabla_componentes',
    'extraer_todos_datos_factura',
    'extraer_energia_valores'
]