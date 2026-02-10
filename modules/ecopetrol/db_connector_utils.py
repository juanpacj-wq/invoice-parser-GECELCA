"""
Módulo de utilidades para la conexión con la base de datos.
Contiene funciones auxiliares para el manejo de consultas y datos.
"""

import logging

# Configurar logger
logger = logging.getLogger(__name__)

def format_query_params(query, params):
    """
    Registra una consulta SQL con sus parámetros para facilitar la depuración.
    
    Args:
        query (str): Consulta SQL
        params (list): Parámetros de la consulta
    """
    # Crear una versión simplificada de la consulta para el log (sin formateo complejo)
    query_simple = query.replace('\n', ' ').strip()
    if len(query_simple) > 200:
        query_simple = query_simple[:200] + "..."
        
    logger.info(f"Ejecutando consulta: {query_simple}")
    
    # Limitar el detalle de los parámetros en caso de listas largas
    if params and len(params) > 5:
        params_str = f"{params[:5]} y {len(params) - 5} más"
    else:
        params_str = str(params)
        
    logger.info(f"Con parámetros: {params_str}")

def log_query_results(df):
    """
    Registra información sobre los resultados de una consulta.
    
    Args:
        df (pandas.DataFrame): DataFrame con los resultados de la consulta
    """
    if df is None:
        logger.warning("DataFrame de resultados es None")
        return
        
    if df.empty:
        logger.warning("No se encontraron datos en la base de datos")
        return
        
    # Registrar información sobre los datos encontrados
    logger.info(f"Se obtuvieron {len(df)} registros de la base de datos")
    
    fronteras_encontradas = df['frt'].unique()
    logger.info(f"Fronteras encontradas en la base de datos: {list(fronteras_encontradas)}")
    
    # Si hay fechafacturacion en las columnas, mostrar rango de fechas
    if 'fechafacturacion' in df.columns:
        min_date = df['fechafacturacion'].min()
        max_date = df['fechafacturacion'].max()
        logger.info(f"Rango de fechas en los resultados: {min_date} a {max_date}")

def ensure_numeric_value(value):
    """
    Asegura que un valor sea numérico para operaciones aritméticas.
    
    Args:
        value: Valor a convertir
        
    Returns:
        float: Valor convertido a número
    """
    if value is None:
        return 0.0
        
    if isinstance(value, (int, float)):
        return float(value)
        
    if isinstance(value, str):
        value = value.replace(',', '').replace('"', '')
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
            
    return 0.0

def calculate_difference(value_1, value_2):
    """
    Calcula la diferencia entre dos valores, con manejo de casos especiales.
    
    Args:
        value_1 (float): Primer valor
        value_2 (float): Segundo valor
        
    Returns:
        tuple: (diferencia, estado)
    """
    value_1 = ensure_numeric_value(value_1)
    value_2 = ensure_numeric_value(value_2)
    
    # Caso donde ambos valores son cero
    if value_1 == 0 and value_2 == 0:
        return 0, 'OK'
        
    # Caso donde el valor de referencia es cero pero el otro no
    if value_2 == 0 and value_1 != 0:
        return 100, 'Alerta'  # 100% de diferencia
        
    # Diferencia absoluta
    diff_abs = abs(value_1 - value_2)
    
    # Para valores pequeños, usar diferencia absoluta
    if abs(value_2) < 1:
        if diff_abs < 0.1:
            return diff_abs, 'OK'
        else:
            return diff_abs, 'Alerta'
    
    # Diferencia porcentual para valores normales
    diff_percent = (diff_abs / abs(value_2)) * 100
    
    if diff_percent < 1:  # Menos del 1% de diferencia
        return diff_percent, 'OK'
    else:
        return diff_percent, 'Alerta'

def extract_component_value(data, component_name, field_name):
    """
    Extrae un valor específico de un componente de la factura.
    
    Args:
        data (dict): Datos de la factura
        component_name (str): Nombre del componente
        field_name (str): Nombre del campo
        
    Returns:
        float: Valor del campo
    """
    if 'componentes' not in data:
        return 0.0
        
    for component in data['componentes']:
        if component.get('concepto') == component_name:
            value = component.get(field_name, 0)
            return ensure_numeric_value(value)
            
    return 0.0

def find_matching_frontera(facturas, codigo_sic):
    """
    Busca una factura que coincida con un código SIC específico.
    
    Args:
        facturas (list): Lista de facturas procesadas
        codigo_sic (str): Código SIC a buscar
        
    Returns:
        dict: Factura coincidente o None si no se encuentra
    """
    for factura in facturas:
        if factura['datos_generales'].get('codigo_sic') == codigo_sic:
            return factura
    return None