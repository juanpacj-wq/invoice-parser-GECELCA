"""
Módulo para realizar consultas a la base de datos corporativa.
Contiene funciones para conectarse a la base de datos y ejecutar consultas específicas.
"""

import logging
import pandas as pd
import psycopg2
from .db_connector_utils import format_query_params, log_query_results

# Configurar logger
logger = logging.getLogger(__name__)

def connect_to_database(connection_params):
    """
    Establece conexión con la base de datos.
    
    Args:
        connection_params (dict): Parámetros de conexión a la base de datos
    
    Returns:
        connection: Objeto de conexión a la base de datos o None si falla
    """
    try:
        connection = psycopg2.connect(**connection_params)
        logger.info("Conexión a la base de datos establecida")
        return connection
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None

def get_factura_data_from_db(connection_params, fecha_inicio, fecha_fin, fronteras=None):
    """
    Obtiene los datos de facturas desde la base de datos en un rango de fechas.
    
    Args:
        connection_params (dict): Parámetros de conexión a la base de datos
        fecha_inicio (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_fin (str): Fecha de fin en formato 'YYYY-MM-DD'
        fronteras (list, optional): Lista de fronteras a filtrar
            
    Returns:
        pandas.DataFrame: DataFrame con los datos de las facturas o None si falla
    """
    try:
        # Log de parámetros de consulta para depurar
        logger.info(f"Consultando facturas con fechas: {fecha_inicio} a {fecha_fin}")
        if fronteras:
            logger.info(f"Filtrando por fronteras: {', '.join(fronteras)}")
        
        # Consulta específica por período de facturación con campos adicionales para componentes
        query = _get_main_query()
        
        conn = connect_to_database(connection_params)
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Preparar parámetros
        params = [fecha_inicio, fecha_fin]
        
        # Añadir filtro de fronteras si es necesario
        if fronteras and len(fronteras) > 0:
            placeholder = ','.join(['%s'] * len(fronteras))
            query += f" AND frontera IN ({placeholder})"
            params.extend(fronteras)
        
        # Log de la consulta completa para depuración
        format_query_params(query, params)
        
        # Ejecutar consulta
        cursor.execute(query, params)
        
        # Obtener resultados
        results = cursor.fetchall()
        logger.info(f"Consulta ejecutada. Resultados: {len(results)}")
        
        # Si no hay resultados, intentar con una consulta más flexible
        if not results and fronteras and len(fronteras) > 0:
            results = _try_alternative_query(conn, cursor, fronteras)
        
        # Obtener los nombres de las columnas
        column_names = [desc[0] for desc in cursor.description]
        
        # Crear DataFrame
        df = pd.DataFrame(results, columns=column_names)
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
        # Registrar información sobre los datos encontrados
        log_query_results(df)
        
        return df
            
    except Exception as e:
        logger.error(f"Error al obtener datos de la base de datos: {e}", exc_info=True)
        return None

def _get_main_query():
    """
    Retorna la consulta SQL principal para obtener datos de facturas.
    
    Returns:
        str: Consulta SQL
    """
    return """
    SELECT frontera as frt, factura_dian as factura, v_consumo_energia_ajustado as subtotal_energía_total, v_contribucion + v_consumo_energia_ajustado + v_contribucion_otros_meses as subtotal_energía_contribución_pesos,
    q_activa as energía_activa, q_inductiva_pen as energía_reactiva_inductiva_facturada, q_reactiva_pen as total_energia_reactiva,
    q_capacitiva_pen as energía_reactiva_capacitiva_facturada, v_gm as generación_mes_corriente, 
    v_rm as restricciones_mes_corriente, v_cm as comercialización_mes_corriente, v_dm as distribución_mes_corriente, 
    v_om as otros_cargos_mes_corriente, v_ppond as pérdidas_mes_corriente, v_tpond as transmisión_mes_corriente, 
    v_reactiva_pen as energía_inductiva_capacitiva_facturada_mes_corriente, v_consumo_energia as subtotal_energía_mes_corriente,  
    v_gm_ajuste as generación_ajustes_anteriores, v_rm_ajuste as restricciones_ajustes_anteriores, 
    v_cm_ajuste as comercialización_ajustes_anteriores, v_dm_ajuste as distribución_ajustes_anteriores, 
    v_om_ajuste as otros_cargos_ajustes_anteriores,  v_ppond_ajuste as pérdidas_ajustes_anteriores, 
    v_tpond_ajuste as transmisión_ajustes_anteriores, v_consumo_energia_ajuste as subtotal_energía_ajustes_anteriores, 
    v_reactiva_pen_ajuste as energía_inductiva_capacitiva_facturada_ajustes_anteriores,  v_gm_ajustado as generación_total, v_iap_ajuste + v_iapb as alumbrado_publico_total,
    v_rm_ajustado as restricciones_total, v_cm_ajustado as comercialización_total, v_dm_ajustado as distribución_total, 
    v_om_ajustado as otros_cargos_total, interes_mora+v_aj_cargos_regulados+v_compensacion+total_saldo_cartera+v_trabajos_otc_gec+v_trabajos_otc_oa+v_sobretasa as otros_cobros,v_trabajos_otc_gec+v_trabajos_otc_oa as recobros,  v_ppond_ajustado as pérdidas_total, v_tpond_ajustado as transmisión_total, 
    v_reactiva_pen_ajustado as energía_inductiva_capacitiva_facturada_total, v_contribucion as contribución, 
    v_compensacion as compensaciones, total_saldo_cartera as amortizacion, v_iapb as impuesto_alumbrado_público, 
    v_iap_ajuste as ajuste_iap_otros_meses, v_sgcv as tasa_especial_convivencia_ciudadana, v_asgcv as ajuste_tasa_convivencia_otros_meses, v_sobretasa as sobretasa,
    v_neto_factura as neto_a_pagar, factor_m, v_aj_cargos_regulados as ajustes_cargos_regulados, 
    interes_mora as interés_por_mora, v_neto_factura as total_servicio_energía_impuestos,v_asgcv + v_sgcv as covivencia_ciudadana,v_contribucion_otros_meses,
    
    --interes_mora+v_aj_cargos_regulados+v_compensacion+total_saldo_cartera as otros_cobros

    -- Campos adicionales para componentes detallados
    q_activa as generación_kwh_kvarh, 
    gm_redo as generación_precio_kwh,
    v_gm as generación_mes_corriente_pesos,
    v_gm_ajuste as generación_mes_anteriores_pesos, 
    v_gm_ajustado as generación_total_pesos,
    
    cm_redo as comercialización_precio_kwh, 
    v_cm as comercialización_mes_corriente_pesos,
    v_cm_ajuste as comercialización_mes_anteriores_pesos, 
    v_cm_ajustado as comercialización_total_pesos,
    
    tpond_redo as transmisión_precio_kwh, 
    v_tpond as transmisión_mes_corriente_pesos,
    v_tpond_ajuste as transmisión_mes_anteriores_pesos, 
    v_tpond_ajustado as transmisión_total_pesos,
    
    dm_redo as distribución_precio_kwh, 
    v_dm as distribución_mes_corriente_pesos,
    v_dm_ajuste as distribución_mes_anteriores_pesos, 
    v_dm_ajustado as distribución_total_pesos,
    
    ppond_redo as pérdidas_precio_kwh, 
    v_ppond as pérdidas_mes_corriente_pesos,
    v_ppond_ajuste as pérdidas_mes_anteriores_pesos, 
    v_ppond_ajustado as pérdidas_total_pesos,
    
    rm_redo as restricciones_precio_kwh, 
    v_rm as restricciones_mes_corriente_pesos,
    v_rm_ajuste as restricciones_mes_anteriores_pesos, 
    v_rm_ajustado as restricciones_total_pesos,
    
    om_redo as otros_cargos_precio_kwh, 
    v_om as otros_cargos_mes_corriente_pesos,
    v_om_ajuste as otros_cargos_mes_anteriores_pesos, 
    v_om_ajustado as otros_cargos_total_pesos,
    
    q_inductiva_pen + q_capacitiva_pen as energía_inductiva_capacitiva_kwh_kvarh, 
    v_reactiva_pen as energía_inductiva_capacitiva_mes_corriente_pesos,
    v_reactiva_pen_ajuste as energía_inductiva_capacitiva_mes_anteriores_pesos, 
    v_reactiva_pen_ajustado as energía_inductiva_capacitiva_total_pesos
    
    FROM app_ectc_gecc.reporte_liquidacion_frts 
    WHERE fechafacturacion BETWEEN to_date(%s, 'YYYY-MM-DD') AND to_date(%s, 'YYYY-MM-DD') and factura_dian is not null"""

def _get_alternative_query():
    """
    Retorna una consulta SQL alternativa para buscar por frontera sin restricción de fecha.
    
    Returns:
        str: Consulta SQL alternativa
    """
    return """
    SELECT frontera as frt, factura_dian as factura, v_consumo_energia_ajustado as subtotal_energía_total,  v_contribucion + v_consumo_energia_ajustado + v_contribucion_otros_meses as subtotal_energía_contribución_pesos,
    q_activa as energía_activa, q_inductiva_pen as energía_reactiva_inductiva_facturada, q_reactiva_pen as total_energia_reactiva,
    q_capacitiva_pen as energía_reactiva_capacitiva_facturada, v_gm as generación_mes_corriente, 
    v_rm as restricciones_mes_corriente, v_cm as comercialización_mes_corriente, v_dm as distribución_mes_corriente, 
    v_om as otros_cargos_mes_corriente, v_ppond as pérdidas_mes_corriente, v_tpond as transmisión_mes_corriente, 
    v_reactiva_pen as energía_inductiva_capacitiva_facturada_mes_corriente, v_consumo_energia as subtotal_energía_mes_corriente,  
    v_gm_ajuste as generación_ajustes_anteriores, v_rm_ajuste as restricciones_ajustes_anteriores, 
    v_cm_ajuste as comercialización_ajustes_anteriores, v_dm_ajuste as distribución_ajustes_anteriores, 
    v_om_ajuste as otros_cargos_ajustes_anteriores,  v_ppond_ajuste as pérdidas_ajustes_anteriores, 
    v_tpond_ajuste as transmisión_ajustes_anteriores, v_consumo_energia_ajuste as subtotal_energía_ajustes_anteriores, 
    v_reactiva_pen_ajuste as energía_inductiva_capacitiva_facturada_ajustes_anteriores,  v_gm_ajustado as generación_total, 
    v_rm_ajustado as restricciones_total, v_cm_ajustado as comercialización_total, v_dm_ajustado as distribución_total, 
    v_om_ajustado as otros_cargos_total,  v_ppond_ajustado as pérdidas_total, v_tpond_ajustado as transmisión_total, 
    v_reactiva_pen_ajustado as energía_inductiva_capacitiva_facturada_total,interes_mora+v_aj_cargos_regulados+v_compensacion+total_saldo_cartera+v_trabajos_otc_gec+v_trabajos_otc_oa+v_sobretasa as otros_cobros,v_trabajos_otc_gec+v_trabajos_otc_oa as recobros, v_contribucion as contribución, 
    v_compensacion as compensaciones, total_saldo_cartera as amortizacion, v_iapb as impuesto_alumbrado_público, v_iap_ajuste + v_iapb as alumbrado_publico_total,
    v_iap_ajuste as ajuste_iap_otros_meses, v_sgcv as tasa_especial_convivencia_ciudadana, v_asgcv as ajuste_tasa_convivencia_otros_meses, 
    v_neto_factura as neto_a_pagar, factor_m, v_aj_cargos_regulados as ajustes_cargos_regulados, 
    interes_mora as interés_por_mora,v_asgcv + v_sgcv as covivencia_ciudadana,v_sobretasa as sobretasa,
    fechafacturacion, v_neto_factura as total_servicio_energía_impuestos,v_contribucion_otros_meses ,
    
    -- Campos adicionales para componentes detallados
    q_activa as generación_kwh_kvarh, 
    gm_redo as generación_precio_kwh,
    v_gm as generación_mes_corriente_pesos,
    v_gm_ajuste as generación_mes_anteriores_pesos, 
    v_gm_ajustado as generación_total_pesos,
    
    cm_redo as comercialización_precio_kwh, 
    v_cm as comercialización_mes_corriente_pesos,
    v_cm_ajuste as comercialización_mes_anteriores_pesos, 
    v_cm_ajustado as comercialización_total_pesos,
    
    tpond_redo as transmisión_precio_kwh, 
    v_tpond as transmisión_mes_corriente_pesos,
    v_tpond_ajuste as transmisión_mes_anteriores_pesos, 
    v_tpond_ajustado as transmisión_total_pesos,
    
    dm_redo as distribución_precio_kwh, 
    v_dm as distribución_mes_corriente_pesos,
    v_dm_ajuste as distribución_mes_anteriores_pesos, 
    v_dm_ajustado as distribución_total_pesos,
    
    ppond_redo as pérdidas_precio_kwh, 
    v_ppond as pérdidas_mes_corriente_pesos,
    v_ppond_ajuste as pérdidas_mes_anteriores_pesos, 
    v_ppond_ajustado as pérdidas_total_pesos,
    
    rm_redo as restricciones_precio_kwh, 
    v_rm as restricciones_mes_corriente_pesos,
    v_rm_ajuste as restricciones_mes_anteriores_pesos, 
    v_rm_ajustado as restricciones_total_pesos,
    
    om_redo as otros_cargos_precio_kwh, 
    v_om as otros_cargos_mes_corriente_pesos,
    v_om_ajuste as otros_cargos_mes_anteriores_pesos, 
    v_om_ajustado as otros_cargos_total_pesos,
    
    q_inductiva_pen + q_capacitiva_pen as energía_inductiva_capacitiva_kwh_kvarh, 
    v_reactiva_pen as energía_inductiva_capacitiva_mes_corriente_pesos,
    v_reactiva_pen_ajuste as energía_inductiva_capacitiva_mes_anteriores_pesos, 
    v_reactiva_pen_ajustado as energía_inductiva_capacitiva_total_pesos

    FROM app_ectc_gecc.reporte_liquidacion_frts 
    WHERE frontera IN ({}) and factura_dian is not null 
    ORDER BY fechafacturacion DESC
    """

def _try_alternative_query(conn, cursor, fronteras):
    """
    Intenta ejecutar una consulta alternativa cuando la consulta principal no da resultados.
    
    Args:
        conn: Conexión a la base de datos
        cursor: Cursor de la base de datos
        fronteras (list): Lista de fronteras a consultar
        
    Returns:
        list: Resultados de la consulta o lista vacía si falla
    """
    logger.info("No se encontraron resultados. Intentando búsqueda por frontera...")
    
    # Consulta por frontera sin restricción de fecha
    placeholder = ','.join(['%s'] * len(fronteras))
    frontier_query = _get_alternative_query().format(placeholder)
    
    logger.info(f"Ejecutando consulta alternativa: {frontier_query}")
    logger.info(f"Con parámetros: {fronteras}")
    
    cursor.execute(frontier_query, fronteras)
    results = cursor.fetchall()
    
    if results:
        logger.info(f"Se encontraron {len(results)} registros buscando solo por fronteras")
    
    return results