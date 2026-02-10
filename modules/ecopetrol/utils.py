"""
Módulo de utilidades auxiliares para el procesamiento de facturas.
Contiene funciones comunes utilizadas por otros módulos.
"""

import os
import re
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("factura_processor.log"),
        logging.StreamHandler()
    ]
    
)

logger = logging.getLogger(__name__)


def crear_directorio_si_no_existe(directorio):
    """
    Crea un directorio si no existe.
    
    Args:
        directorio (str): Ruta del directorio a crear
        
    Returns:
        bool: True si el directorio existe o fue creado, False en caso de error
    """
    if not os.path.exists(directorio):
        try:
            os.makedirs(directorio)
            logger.info(f"Directorio creado: {directorio}")
            return True
        except Exception as e:
            logger.error(f"Error al crear directorio {directorio}: {e}")
            return False
    return True


def obtener_nombre_archivo_sin_extension(ruta_archivo):
    """
    Obtiene el nombre de un archivo sin su extensión.
    
    Args:
        ruta_archivo (str): Ruta completa del archivo
        
    Returns:
        str: Nombre del archivo sin extensión
    """
    return os.path.splitext(os.path.basename(ruta_archivo))[0]


def validar_estructura_csv(ruta_csv):
    """
    Valida que un archivo CSV tenga la estructura esperada para una factura.
    
    Args:
        ruta_csv (str): Ruta del archivo CSV
        
    Returns:
        bool: True si la estructura es válida, False en caso contrario
    """
    try:
        with open(ruta_csv, 'r', encoding='utf-8') as file:
            contenido = file.read()
    except UnicodeDecodeError:
        try:
            with open(ruta_csv, 'r', encoding='latin-1') as file:
                contenido = file.read()
        except Exception as e:
            logger.error(f"Error al leer archivo {ruta_csv}: {e}")
            return False
    
    # Patrones que deben estar presentes en una factura válida
    patrones_obligatorios = [
        r'Fecha\s+vencimiento',
        r'Período\s+Facturación',
        r'Subtotal\s+(?:base\s+)?energía'
    ]
    
    for patron in patrones_obligatorios:
        if not re.search(patron, contenido):
            logger.warning(f"Patrón no encontrado en {ruta_csv}: {patron}")
            return False
    
    return True


def normalizar_fecha(fecha_str):
    """
    Normaliza una fecha a formato ISO (YYYY-MM-DD).
    
    Args:
        fecha_str (str): Fecha en varios formatos posibles
        
    Returns:
        str: Fecha en formato ISO o la cadena original si no se puede normalizar
    """
    # Patrones de fecha comunes
    patrones = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY o MM/DD/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})'   # DD-MM-YYYY o MM-DD-YYYY
    ]
    
    for patron in patrones:
        match = re.search(patron, fecha_str)
        if match:
            # Determinar el formato
            if '/' in fecha_str and len(match.group(3)) == 4:
                # Asumir DD/MM/YYYY
                dia, mes, anio = match.group(1), match.group(2), match.group(3)
                try:
                    # Validar que la fecha sea correcta
                    fecha = datetime(int(anio), int(mes), int(dia))
                    return fecha.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            elif '-' in fecha_str and len(match.group(1)) == 4:
                # Ya está en formato YYYY-MM-DD
                return fecha_str
    
    # Si no se pudo normalizar, devolver la cadena original
    return fecha_str


def convertir_a_numero(valor):
    """
    Convierte un valor a número (entero o flotante) si es posible.
    
    Args:
        valor: Valor a convertir (puede ser string, número, etc.)
        
    Returns:
        int, float o el valor original: Valor convertido o el original si no se puede convertir
    """
    if valor is None:
        return 0
    
    if isinstance(valor, (int, float)):
        return valor
    
    if isinstance(valor, str):
        # Limpiar el valor (quitar comas, espacios, etc.)
        valor_limpio = valor.replace(',', '').replace(' ', '').replace('"', '')
        
        # Determinar si es negativo
        es_negativo = valor_limpio.startswith('-')
        if es_negativo:
            valor_limpio = valor_limpio[1:]
        
        try:
            # Intentar convertir a entero o flotante
            if '.' in valor_limpio:
                resultado = float(valor_limpio)
            else:
                resultado = int(valor_limpio)
            
            # Aplicar signo negativo si corresponde
            if es_negativo:
                resultado = -resultado
                
            return resultado
        except ValueError:
            pass
    
    # Si no se pudo convertir, devolver el valor original
    return valor


def formatear_valor_monetario(valor, incluir_signo=True):
    """
    Formatea un valor como valor monetario.
    
    Args:
        valor: Valor a formatear
        incluir_signo (bool): Si se debe incluir el signo de pesos
        
    Returns:
        str: Valor formateado como moneda
    """
    # Convertir a número si es posible
    valor_numerico = convertir_a_numero(valor)
    
    # Si no es un número, devolver el valor original
    if not isinstance(valor_numerico, (int, float)):
        return str(valor)
    
    # Formatear con separador de miles y 2 decimales
    valor_formateado = f"{valor_numerico:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
    
    # Agregar signo de pesos si se solicita
    if incluir_signo:
        return f"${valor_formateado}"
    
    return valor_formateado