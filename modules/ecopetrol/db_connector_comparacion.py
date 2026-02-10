"""
Módulo para realizar comparaciones entre facturas procesadas y datos de la base de datos.
Contiene funciones para comparar datos y calcular diferencias.
"""

import logging
import calendar
from datetime import datetime, date
import pandas as pd
from .db_connector_consultas import connect_to_database, get_factura_data_from_db

# Configurar logger
logger = logging.getLogger(__name__)

def compare_with_facturas(connection_params, facturas_procesadas, fecha_inicio=None, fecha_fin=None):
    """
    Compara las facturas procesadas con los datos de la base de datos.
    
    Args:
        connection_params (dict): Parámetros de conexión a la base de datos
        facturas_procesadas (list): Lista de diccionarios con datos de facturas
        fecha_inicio (str, optional): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_fin (str, optional): Fecha de fin en formato 'YYYY-MM-DD'
            
    Returns:
        pandas.DataFrame: DataFrame con la comparación de facturas
    """
    # Obtener fronteras de las facturas procesadas
    fronteras = []
    periodos_facturacion = []
    
    # Extraer información detallada para depuración
    for factura in facturas_procesadas:
        codigo_sic = factura['datos_generales'].get('codigo_sic', '')
        if codigo_sic and codigo_sic != "No encontrado":
            fronteras.append(codigo_sic)
            
            # Extraer período de facturación
            periodo = factura['datos_generales'].get('periodo_facturacion', 'No encontrado')
            periodos_facturacion.append((codigo_sic, periodo))
    
    if not fronteras:
        logger.warning("No se encontraron códigos de frontera válidos en las facturas procesadas")
        return pd.DataFrame()
    
    logger.info(f"Se encontraron {len(fronteras)} fronteras para comparar: {fronteras}")
    logger.info(f"Períodos de facturación: {periodos_facturacion}")
    
    # Si no se proporcionan fechas, extraerlas de las facturas
    if not fecha_inicio or not fecha_fin:
        fecha_inicio, fecha_fin = extract_date_range_from_facturas(facturas_procesadas)
    
    # Obtener datos de la base de datos
    db_data = get_factura_data_from_db(connection_params, fecha_inicio, fecha_fin, fronteras)
    
    if db_data is None or db_data.empty:
        logger.warning("No se obtuvieron datos de la base de datos para comparar")
        return _create_empty_comparison_dataframe(facturas_procesadas)
    
    # Crear DataFrame para almacenar las comparaciones
    comparaciones = []
    
    # Mapeo de nombres de variables para comparar
    mapeo_variables = _get_variables_mapping()
    
    # Para cada factura procesada, buscar correspondencia en la base de datos
    for factura in facturas_procesadas:
        codigo_sic = factura['datos_generales'].get('codigo_sic', "")
        if codigo_sic == "No encontrado" or not codigo_sic:
            continue
            
        # Buscar la frontera en los datos de la base de datos
        factura_db = db_data[db_data['frt'] == codigo_sic]
        
        if factura_db.empty:
            logger.warning(f"No se encontraron datos en BD para la frontera {codigo_sic}")
            _add_empty_comparison_rows(comparaciones, factura, codigo_sic, mapeo_variables)
            continue
            
        # Si hay múltiples registros para la misma frontera, usar el más reciente
        if len(factura_db) > 1:
            logger.info(f"Se encontraron {len(factura_db)} registros para la frontera {codigo_sic}. Usando el primero.")
            factura_db = factura_db.iloc[[0]]
        
        # Comparar todas las variables generales
        _compare_general_variables(comparaciones, factura, codigo_sic, factura_db, mapeo_variables)
        
        # Comparar componentes de energía
        _compare_energy_components(comparaciones, factura, codigo_sic, factura_db)
    
    # Crear DataFrame con las comparaciones
    return pd.DataFrame(comparaciones)

def extract_date_range_from_facturas(facturas_procesadas):
    """
    Extrae el rango de fechas de las facturas procesadas,
    asegurando que use el período de facturación y el último día del mes.
    
    Args:
        facturas_procesadas (list): Lista de diccionarios con datos de facturas
        
    Returns:
        tuple: (fecha_inicio, fecha_fin) en formato 'YYYY-MM-DD'
    """
    # Buscar períodos de facturación
    periodos_facturacion = []
    
    for factura in facturas_procesadas:
        datos_generales = factura.get('datos_generales', {})
        
        # Extraer período de facturación
        periodo_facturacion = datos_generales.get('periodo_facturacion')
        if periodo_facturacion and periodo_facturacion != "No encontrado":
            logger.info(f"Encontrado período de facturación: {periodo_facturacion}")
            # El período puede tener formato "YYYY-MM-DD a YYYY-MM-DD" o solo "YYYY-MM-DD"
            if ' a ' in periodo_facturacion:
                inicio, fin = periodo_facturacion.split(' a ')
                periodos_facturacion.append((inicio, fin))
            else:
                # Si solo hay una fecha, asumir que es el inicio del período
                periodos_facturacion.append((periodo_facturacion, ""))
    
    if not periodos_facturacion:
        logger.warning("No se encontraron períodos de facturación. Usando fechas predeterminadas.")
        # Usar el mes actual como predeterminado
        hoy = date.today()
        primer_dia = date(hoy.year, hoy.month, 1)
        ultimo_dia = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
        return primer_dia.strftime('%Y-%m-%d'), ultimo_dia.strftime('%Y-%m-%d')
    
    # Procesar los períodos encontrados
    fechas_inicio = []
    fechas_fin = []
    
    for inicio, fin in periodos_facturacion:
        try:
            # Convertir fecha de inicio
            fecha_inicio = datetime.strptime(inicio, '%Y-%m-%d').date()
            fechas_inicio.append(fecha_inicio)
            
            # Procesar fecha de fin
            if fin:
                fecha_fin = datetime.strptime(fin, '%Y-%m-%d').date()
            else:
                # Si no hay fecha fin, calcular el último día del mes de la fecha de inicio
                ultimo_dia = calendar.monthrange(fecha_inicio.year, fecha_inicio.month)[1]
                fecha_fin = date(fecha_inicio.year, fecha_inicio.month, ultimo_dia)
            
            fechas_fin.append(fecha_fin)
            
            logger.info(f"Período procesado: {fecha_inicio} a {fecha_fin}")
        except ValueError as e:
            logger.error(f"Error al procesar fecha: {e}")
            continue
    
    if not fechas_inicio or not fechas_fin:
        logger.warning("No se pudieron procesar las fechas. Usando fechas predeterminadas.")
        # Usar el mes actual como predeterminado
        hoy = date.today()
        primer_dia = date(hoy.year, hoy.month, 1)
        ultimo_dia = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
        return primer_dia.strftime('%Y-%m-%d'), ultimo_dia.strftime('%Y-%m-%d')
    
    # Obtener el rango completo (la fecha más temprana de inicio y la más tardía de fin)
    fecha_inicio_min = min(fechas_inicio)
    fecha_fin_max = max(fechas_fin)
    
    # Asegurar que la fecha de inicio sea el primer día del mes
    fecha_inicio_ajustada = date(fecha_inicio_min.year, fecha_inicio_min.month, 1)
    
    # Asegurar que la fecha de fin sea el último día del mes
    ultimo_dia = calendar.monthrange(fecha_fin_max.year, fecha_fin_max.month)[1]
    fecha_fin_ajustada = date(fecha_fin_max.year, fecha_fin_max.month, ultimo_dia)
    
    logger.info(f"Rango de fechas final: {fecha_inicio_ajustada} a {fecha_fin_ajustada}")
    
    return fecha_inicio_ajustada.strftime('%Y-%m-%d'), fecha_fin_ajustada.strftime('%Y-%m-%d')

def _get_variables_mapping():
    """
    Retorna el mapeo de nombres de variables entre la factura y la base de datos.
    
    Returns:
        dict: Diccionario con el mapeo de variables
    """
    return {
        'periodo_facturacion': 'período facturación',
        'factor_m': 'factor_m',
        'codigo_sic': 'frt',
        'subtotal_base_energia': 'subtotal_energía_total',
        'contribucion': 'contribución',
        'contribucion_otros_meses': 'v_contribucion_otros_meses',
        'subtotal_energia_contribucion_pesos': 'subtotal_energía_contribución_pesos',
        'otros_cobros': 'otros_cobros',
        'sobretasa': 'sobretasa',
        'ajustes_cargos_regulados': 'ajustes_cargos_regulados',
        'compensaciones': 'compensaciones',
        'saldo_cartera': 'amortizacion',
        'interes_mora': 'interés_por_mora',
        'recobros':'recobros',
        'alumbrado_publico': 'alumbrado_publico_total',
        'impuesto_alumbrado_publico': 'impuesto_alumbrado_público',
        'ajuste_iap_otros_meses': 'ajuste_iap_otros_meses',
        'convivencia_ciudadana': 'covivencia_ciudadana',
        'tasa_especial_convivencia': 'tasa_especial_convivencia_ciudadana',
        'ajuste_tasa_convivencia': 'ajuste_tasa_convivencia_otros_meses',
        'total_servicio_energia_impuestos': 'total_servicio_energía_impuestos',
        'ajuste_decena': 'ajuste_decena',
        'neto_pagar': 'neto_a_pagar',
        'energia_reactiva_inductiva': 'energía_reactiva_inductiva_facturada',
        'energia_reactiva_capacitiva': 'energía_reactiva_capacitiva_facturada',
        'total_energia_reactiva': 'total_energia_reactiva'
    }

def _create_empty_comparison_dataframe(facturas_procesadas):
    """
    Crea un DataFrame de comparación con datos de la factura y valores nulos para DB.
    
    Args:
        facturas_procesadas (list): Lista de diccionarios con datos de facturas
        
    Returns:
        pandas.DataFrame: DataFrame con comparaciones vacías
    """
    comparaciones = []
    
    # Lista de campos a comparar
    campos_a_comparar = [
        'periodo_facturacion', 'factor_m', 'codigo_sic', 'subtotal_base_energia', 
        'contribucion', 'contribucion_otros_meses',
        'subtotal_energia_contribucion_pesos', 'otros_cobros', 'sobretasa', 
        'ajustes_cargos_regulados', 'compensaciones', 'saldo_cartera', 
        'interes_mora','recobros', 'alumbrado_publico', 'impuesto_alumbrado_publico', 
        'ajuste_iap_otros_meses', 'convivencia_ciudadana', 'tasa_especial_convivencia', 
        'ajuste_tasa_convivencia', 'total_servicio_energia_impuestos', 
        'ajuste_decena', 'neto_pagar', 'energia_reactiva_inductiva', 
        'energia_reactiva_capacitiva', 'total_energia_reactiva'
    ]
    
    for factura in facturas_procesadas:
        codigo_sic = factura['datos_generales'].get('codigo_sic', "")
        if codigo_sic == "No encontrado" or not codigo_sic:
            continue
            
        # Agregar datos generales con valor nulo para DB
        for campo in campos_a_comparar:
            var_factura = factura['datos_generales'].get(campo.lower(), 0)
            comparaciones.append({
                'ID_Factura': factura.get('id', ''),
                'Frontera': codigo_sic,
                'Concepto': campo,
                'Valor_Factura': var_factura,
                'Valor_Datalake': None,
                'Diferencia': None,
                'Estado': 'No encontrado en DB'
            })
        
        # Agregar componentes con valor nulo para DB
        for componente in factura['componentes']:
            concepto = componente.get('concepto', '')
            valor_factura = componente.get('total', 0)
            comparaciones.append({
                'ID_Factura': factura.get('id', ''),
                'Frontera': codigo_sic,
                'Concepto': concepto,
                'Valor_Factura': valor_factura,
                'Valor_Datalake': None,
                'Diferencia': None,
                'Estado': 'No encontrado en DB'
            })
            
            # Agregar campos detallados de componentes
            for campo in ['kwh_kvarh', 'precio_kwh', 'mes_corriente', 'mes_anteriores']:
                concepto_detallado = f"{concepto}_{campo}"
                valor_factura = componente.get(campo, 0)
                if valor_factura == "N/A":
                    valor_factura = 0
                comparaciones.append({
                    'ID_Factura': factura.get('id', ''),
                    'Frontera': codigo_sic,
                    'Concepto': concepto_detallado,
                    'Valor_Factura': valor_factura,
                    'Valor_Datalake': None,
                    'Diferencia': None,
                    'Estado': 'No encontrado en DB'
                })
    
    return pd.DataFrame(comparaciones)

def _add_empty_comparison_rows(comparaciones, factura, codigo_sic, mapeo_variables):
    """
    Agrega filas de comparación con valores nulos para la base de datos.
    
    Args:
        comparaciones (list): Lista de diccionarios con comparaciones
        factura (dict): Datos de la factura
        codigo_sic (str): Código SIC de la factura
        mapeo_variables (dict): Mapeo de nombres de variables
    """
    # Agregar datos generales con valor nulo para DB
    for var_factura in mapeo_variables.keys():
        valor_factura = factura['datos_generales'].get(var_factura, 0)
        comparaciones.append({
            'ID_Factura': factura.get('id', ''),
            'Frontera': codigo_sic,
            'Concepto': var_factura,
            'Valor_Factura': valor_factura,
            'Valor_Datalake': None,
            'Diferencia': None,
            'Estado': 'No encontrado en DB'
        })
    
    # Agregar componentes con valor nulo para DB
    for componente in factura['componentes']:
        concepto = componente.get('concepto', '')
        valor_factura = componente.get('total', 0)
        comparaciones.append({
            'ID_Factura': factura.get('id', ''),
            'Frontera': codigo_sic,
            'Concepto': concepto,
            'Valor_Factura': valor_factura,
            'Valor_Datalake': None,
            'Diferencia': None,
            'Estado': 'No encontrado en DB'
        })
        
        # Agregar campos detallados de componentes
        for campo in ['kwh_kvarh', 'precio_kwh', 'mes_corriente', 'mes_anteriores']:
            concepto_detallado = f"{concepto}_{campo}"
            valor_factura = componente.get(campo, 0)
            if valor_factura == "N/A":
                valor_factura = 0
            comparaciones.append({
                'ID_Factura': factura.get('id', ''),
                'Frontera': codigo_sic,
                'Concepto': concepto_detallado,
                'Valor_Factura': valor_factura,
                'Valor_Datalake': None,
                'Diferencia': None,
                'Estado': 'No encontrado en DB'
            })

def _compare_general_variables(comparaciones, factura, codigo_sic, factura_db, mapeo_variables):
    """
    Compara las variables generales de la factura con los datos de la base de datos.
    
    Args:
        comparaciones (list): Lista de diccionarios con comparaciones
        factura (dict): Datos de la factura
        codigo_sic (str): Código SIC de la factura
        factura_db (pandas.DataFrame): Datos de la base de datos
        mapeo_variables (dict): Mapeo de nombres de variables
    """
    for var_factura, var_db in mapeo_variables.items():
        valor_factura = factura['datos_generales'].get(var_factura, 0)
        
        # Convertir a float para evitar problemas de tipo
        if not isinstance(valor_factura, (int, float)):
            try:
                valor_factura = float(valor_factura)
            except (ValueError, TypeError):
                valor_factura = 0
        
        valor_db = factura_db[var_db.lower()].values[0] if var_db.lower() in factura_db.columns else 0
        
        # Asegurar que el valor de la BD sea numérico
        if not isinstance(valor_db, (int, float)):
            try:
                valor_db = float(valor_db)
            except (ValueError, TypeError):
                valor_db = 0
        
        # Caso especial para las variables específicas de energía reactiva
        if var_factura in ['energia_reactiva_inductiva', 'energia_reactiva_capacitiva', 'total_energia_reactiva']:
            # Calcular diferencia como una simple resta
            diferencia = abs(valor_factura - valor_db)
            
            # Verificar si la diferencia es mayor que 0.5
            if diferencia > 0.5:
                estado = 'Alerta'
            else:
                estado = 'OK'
        else:
            # Cálculo original de diferencia para el resto de variables
            if valor_db == 0:
                if valor_factura == 0:
                    # Ambos valores son 0, por lo que no hay diferencia
                    diferencia = 0
                    estado = 'OK'
                else:
                    # valor_db es 0 pero valor_factura no, diferencia es 100% o más
                    diferencia = 100  # O podrías usar float('inf') para representar infinito
                    estado = 'Alerta'
            else:
                # Cálculo normal de la diferencia porcentual
                diferencia = abs(valor_factura - valor_db) / abs(valor_db) * 100
                
                # Verificar si la diferencia porcentual es mayor o igual al 1%
                if diferencia >= 1:
                    estado = 'Alerta'
                else:
                    estado = 'OK'
        
        # Agregar a la lista de comparaciones
        comparaciones.append({
            'ID_Factura': factura.get('id', ''),
            'Frontera': codigo_sic,
            'Concepto': var_factura,
            'Valor_Factura': valor_factura,
            'Valor_Datalake': valor_db,
            'Diferencia': diferencia,
            'Estado': estado
        })

def _compare_energy_components(comparaciones, factura, codigo_sic, factura_db):
    """
    Compara los componentes de energía de la factura con los datos de la base de datos.
    
    Args:
        comparaciones (list): Lista de diccionarios con comparaciones
        factura (dict): Datos de la factura
        codigo_sic (str): Código SIC de la factura
        factura_db (pandas.DataFrame): Datos de la base de datos
    """
    # Mapeo detallado para componentes y sus campos
    componentes_map = _get_components_mapping()
    
    for componente in factura['componentes']:
        concepto = componente.get('concepto', '')
        if concepto in componentes_map:
            var_db_total = componentes_map[concepto]['total']
            valor_factura = componente.get('total', 0)
            
            # Convertir a float para evitar problemas de tipo
            if not isinstance(valor_factura, (int, float)):
                try:
                    valor_factura = float(valor_factura)
                except (ValueError, TypeError):
                    valor_factura = 0
            
            valor_db = factura_db[var_db_total.lower()].values[0] if var_db_total.lower() in factura_db.columns else 0
            
            # Asegurar que el valor de la BD sea numérico
            if not isinstance(valor_db, (int, float)):
                try:
                    valor_db = float(valor_db)
                except (ValueError, TypeError):
                    valor_db = 0
            
            # Calcular diferencia
            diferencia = float(valor_factura) - float(valor_db)
            
            # Definir estado basado en la diferencia
            if abs(diferencia) <= 1:  # Tolerancia de 1 para redondeos
                estado = 'OK'
            else:
                estado = 'Alerta'
            
            # Agregar a la lista de comparaciones
            comparaciones.append({
                'ID_Factura': factura.get('id', ''),
                'Frontera': codigo_sic,
                'Concepto': concepto,
                'Valor_Factura': valor_factura,
                'Valor_Datalake': valor_db,
                'Diferencia': diferencia,
                'Estado': estado
            })
            
            # Comparar campos detallados del componente
            for campo, var_db_campo in componentes_map[concepto].items():
                if campo != 'total' and var_db_campo is not None:
                    concepto_detallado = f"{concepto}_{campo}"
                    valor_factura = componente.get(campo, 0)
                    
                    # Manejar valores N/A
                    if valor_factura == "N/A":
                        valor_factura = 0
                        
                    # Convertir a float para evitar problemas de tipo
                    if not isinstance(valor_factura, (int, float)):
                        try:
                            valor_factura = float(valor_factura)
                        except (ValueError, TypeError):
                            valor_factura = 0
                    
                    valor_db = factura_db[var_db_campo.lower()].values[0] if var_db_campo.lower() in factura_db.columns else 0
                    
                    # Asegurar que el valor de la BD sea numérico
                    if not isinstance(valor_db, (int, float)):
                        try:
                            valor_db = float(valor_db)
                        except (ValueError, TypeError):
                            valor_db = 0
                    
                    # Calcular diferencia
                    diferencia = float(valor_factura) - float(valor_db)
                    
                    # Definir estado basado en la diferencia
                    if abs(diferencia) <= 1:  # Tolerancia de 1 para redondeos
                        estado = 'OK'
                    else:
                        estado = 'Alerta'
                    
                    # Agregar a la lista de comparaciones
                    comparaciones.append({
                        'ID_Factura': factura.get('id', ''),
                        'Frontera': codigo_sic,
                        'Concepto': concepto_detallado,
                        'Valor_Factura': valor_factura,
                        'Valor_Datalake': valor_db,
                        'Diferencia': diferencia,
                        'Estado': estado
                    })

def _get_components_mapping():
    """
    Retorna el mapeo de componentes de energía y sus campos con la base de datos.
    
    Returns:
        dict: Diccionario con el mapeo de componentes
    """
    return {
        'Generación': {
            'total': 'generación_total_pesos',
            'kwh_kvarh': 'generación_kwh_kvarh',
            'precio_kwh': 'generación_precio_kwh',
            'mes_corriente': 'generación_mes_corriente_pesos',
            'mes_anteriores': 'generación_mes_anteriores_pesos'
        },
        'Transmisión': {
            'total': 'transmisión_total_pesos',
            'kwh_kvarh': None,  # No aplica
            'precio_kwh': 'transmisión_precio_kwh',
            'mes_corriente': 'transmisión_mes_corriente_pesos',
            'mes_anteriores': 'transmisión_mes_anteriores_pesos'
        },
        'Distribución': {
            'total': 'distribución_total_pesos',
            'kwh_kvarh': None,  # No aplica
            'precio_kwh': 'distribución_precio_kwh',
            'mes_corriente': 'distribución_mes_corriente_pesos',
            'mes_anteriores': 'distribución_mes_anteriores_pesos'
        },
        'Pérdidas': {
            'total': 'pérdidas_total_pesos',
            'kwh_kvarh': None,  # No aplica
            'precio_kwh': 'pérdidas_precio_kwh',
            'mes_corriente': 'pérdidas_mes_corriente_pesos',
            'mes_anteriores': 'pérdidas_mes_anteriores_pesos'
        },
        'Comercialización': {
            'total': 'comercialización_total_pesos',
            'kwh_kvarh': None,  # No aplica
            'precio_kwh': 'comercialización_precio_kwh',
            'mes_corriente': 'comercialización_mes_corriente_pesos',
            'mes_anteriores': 'comercialización_mes_anteriores_pesos'
        },
        'Restricciones': {
            'total': 'restricciones_total_pesos',
            'kwh_kvarh': None,  # No aplica
            'precio_kwh': 'restricciones_precio_kwh',
            'mes_corriente': 'restricciones_mes_corriente_pesos',
            'mes_anteriores': 'restricciones_mes_anteriores_pesos'
        },
        'Otros cargos': {
            'total': 'otros_cargos_total_pesos',
            'kwh_kvarh': None,  # No aplica
            'precio_kwh': 'otros_cargos_precio_kwh',
            'mes_corriente': 'otros_cargos_mes_corriente_pesos',
            'mes_anteriores': 'otros_cargos_mes_anteriores_pesos'
        },
        'Energía inductiva + capacitiva': {
            'total': 'energía_inductiva_capacitiva_total_pesos',
            'kwh_kvarh': 'energía_inductiva_capacitiva_kwh_kvarh',
            'precio_kwh': 'distribución_precio_kwh',  
            'mes_corriente': 'energía_inductiva_capacitiva_mes_corriente_pesos',
            'mes_anteriores': 'energía_inductiva_capacitiva_mes_anteriores_pesos'
        }
    }