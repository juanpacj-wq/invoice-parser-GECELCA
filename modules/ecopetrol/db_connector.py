"""
Módulo principal para la conexión con la base de datos corporativa.
Este módulo reexporta las clases y funciones de los módulos especializados.
"""

# Importar clases y funciones de los módulos especializados
from .db_connector_consultas import (
    connect_to_database, 
    get_factura_data_from_db
)
from .db_connector_comparacion import (
    compare_with_facturas,
    extract_date_range_from_facturas
)
from .db_connector_utils import (
    format_query_params,
    log_query_results
)

class DBConnector:
    """
    Clase para gestionar la conexión a la base de datos corporativa
    y realizar consultas para la comparación de facturas.
    """
    
    def __init__(self):
        """Inicializa el conector a la base de datos."""
        self.connection_params = {
            'host': '172.16.2.52',
            'database': 'liquidacionxm',
            'user': 'gecc_read',
            'password': 'OSiiErZ229F#',
            'port': '5432'
        }
    
    def connect(self):
        """
        Establece conexión con la base de datos.
        
        Returns:
            connection: Objeto de conexión a la base de datos o None si falla
        """
        return connect_to_database(self.connection_params)

    def get_factura_data_from_db(self, fecha_inicio, fecha_fin, fronteras=None):
        """
        Obtiene los datos de facturas desde la base de datos en un rango de fechas.
        
        Args:
            fecha_inicio (str): Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_fin (str): Fecha de fin en formato 'YYYY-MM-DD'
            fronteras (list, optional): Lista de fronteras a filtrar
                
        Returns:
            pandas.DataFrame: DataFrame con los datos de las facturas o None si falla
        """
        return get_factura_data_from_db(self.connection_params, fecha_inicio, fecha_fin, fronteras)
    
    def compare_with_facturas(self, facturas_procesadas, fecha_inicio=None, fecha_fin=None):
        """
        Compara las facturas procesadas con los datos de la base de datos.
        
        Args:
            facturas_procesadas (list): Lista de diccionarios con datos de facturas
            fecha_inicio (str, optional): Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_fin (str, optional): Fecha de fin en formato 'YYYY-MM-DD'
                
        Returns:
            pandas.DataFrame: DataFrame con la comparación de facturas
        """
        return compare_with_facturas(self.connection_params, facturas_procesadas, fecha_inicio, fecha_fin)
    
    def extract_date_range_from_facturas(self, facturas_procesadas):
        """
        Extrae el rango de fechas de las facturas procesadas,
        asegurando que use el período de facturación y el último día del mes.
        
        Args:
            facturas_procesadas (list): Lista de diccionarios con datos de facturas
            
        Returns:
            tuple: (fecha_inicio, fecha_fin) en formato 'YYYY-MM-DD'
        """
        return extract_date_range_from_facturas(facturas_procesadas)

# Re-exportar las funciones y clases para mantener compatibilidad
__all__ = [
    'DBConnector',
    'connect_to_database',
    'get_factura_data_from_db',
    'compare_with_facturas',
    'extract_date_range_from_facturas',
    'format_query_params',
    'log_query_results'
]