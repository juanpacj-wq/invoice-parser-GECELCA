import os
import re
from datetime import datetime
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_directorio_si_no_existe(ruta):
    if not os.path.exists(ruta):
        try:
            os.makedirs(ruta)
        except OSError as e:
            logger.error(f"Error al crear directorio {ruta}: {e}")

def obtener_nombre_archivo_sin_extension(ruta):
    return os.path.splitext(os.path.basename(ruta))[0]

def limpiar_moneda(valor_str):
    """
    Convierte un string de moneda a float, tolerando espacios internos.
    Ej: '$ 8 . 3 6 0 . 5 6 6' -> 8360566.0
    """
    if not valor_str:
        return 0.0
    
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
        
    # 1. Eliminar símbolos de moneda y texto 'COP'
    s = str(valor_str).upper().replace('$', '').replace('COP', '').strip()
    
    if not s:
        return 0.0
    
    try:
        # 2. Truco para OCR/PDFMiner:
        # A veces los números vienen con espacios: "2 9 , 7 6 0 , 0 0 0"
        # Si detectamos que hay digitos separados por espacios, los unimos.
        if re.search(r'\d\s+\d', s):
            s = s.replace(' ', '')
            
        # 3. Limpieza estándar (Asumiendo formato Colombia: 1.000,00 o 1,000.00)
        # La factura muestra "8,360,566,080" (Comas miles) y "280.933" (Punto decimal o miles)
        # Gecelca parece usar coma para miles y punto para decimales en totales grandes,
        # pero a veces punto para miles en tarifas.
        
        # Estrategia segura: Eliminar comas
        s_limpia = s.replace(',', '')
        
        # Si quedan puntos, verificar si son miles o decimales
        # Si hay más de un punto, son miles -> eliminarlos
        if s_limpia.count('.') > 1:
            s_limpia = s_limpia.replace('.', '')
        
        return float(s_limpia)
    except ValueError:
        return 0.0

def limpiar_cantidad(valor_str):
    """
    Limpia strings de cantidad (kWh), tolerando espacios.
    """
    return limpiar_moneda(valor_str)

def parsear_fecha(fecha_str):
    """
    Intenta parsear fechas del formato YYYY-MM-DD.
    """
    if not fecha_str:
        return None
        
    fecha_limpia = fecha_str.split()[0].strip()
    fecha_limpia = re.sub(r'\s+', '', fecha_limpia)
    fecha_limpia = fecha_limpia.replace('–', '-').replace('/', '-')
    
    formatos = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y']
    
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_limpia, fmt).date()
        except ValueError:
            continue
            
    return None