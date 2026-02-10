"""
Módulo para el procesamiento y transformación de datos de facturas.
Este módulo contiene las clases y funciones para procesar, validar y 
transformar los datos extraídos de las facturas.
"""

import re
import os
from datetime import datetime


class FacturaProcessor:
    """
    Clase para procesar y transformar datos de facturas.
    Esta clase realiza la limpieza, validación y transformación de los datos
    extraídos de las facturas.
    """
    
    def __init__(self, datos_generales, datos_componentes):
        """
        Inicializa el procesador de facturas con los datos extraídos.
        
        Args:
            datos_generales (dict): Diccionario con los datos generales de la factura
            datos_componentes (list): Lista de diccionarios con los datos de los componentes
        """
        self.datos_generales = datos_generales
        self.datos_componentes = datos_componentes
        self.fecha_procesamiento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Procesar datos
        self._limpiar_datos_generales()
        self._limpiar_datos_componentes()
    
    def _limpiar_datos_generales(self):
        """
        Limpia y transforma los datos generales de la factura.
        Realiza conversiones de tipo y limpieza de formatos.
        """
        # Lista de campos que no deben ser procesados como valores numéricos
        campos_no_numericos = ["fecha_vencimiento", "periodo_facturacion", "codigo_sic", "numero_factura"]
        
        # Limpiar y convertir valores numéricos
        for key, value in self.datos_generales.items():
            if key in campos_no_numericos:
                # Mantener como string
                continue
            else:
                # Convertir a valor numérico
                self.datos_generales[key] = self._limpiar_valor(value)
    
    def _limpiar_datos_componentes(self):
        """
        Limpia y transforma los datos de los componentes de la factura.
        Realiza conversiones de tipo y limpieza de formatos.
        """
        for componente in self.datos_componentes:
            for key, value in componente.items():
                if key != "concepto" and value != "N/A":
                    componente[key] = self._limpiar_valor(value)
    
    @staticmethod
    def _limpiar_valor(value):
        """
        Limpia un valor numérico y lo convierte al formato apropiado.
        
        Args:
            value: Valor a limpiar y convertir
            
        Returns:
            int, float o str: Valor limpio y convertido
        """
        if value == "No encontrado":
            return 0
        
        # Eliminar comas y comillas
        if isinstance(value, str):
            value = value.replace(',', '').replace('"', '')
            
            # Verificar si es un valor negativo
            es_negativo = value.startswith('-')
            if es_negativo:
                value = value[1:]
        
            # Intentar convertir a float o int
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
                
                # Aplicar signo negativo si era negativo
                if es_negativo:
                    value = -value
            except ValueError:
                # Mantener como string si no se puede convertir
                pass
        
        return value
    
    def calcular_totales(self):
        """
        Calcula totales y subtotales de la factura.
        
        Returns:
            dict: Diccionario con los totales calculados
        """
        totales = {}
        
        # Subtotal de energía (suma de los totales de componentes, excepto energía reactiva)
        subtotal_energia = 0
        for componente in self.datos_componentes:
            if componente["concepto"] != "Energía inductiva + capacitiva":
                # Asegurar que el total sea un número
                total_componente = self._asegurar_numero(componente.get("total", 0))
                subtotal_energia += total_componente
        
        totales["subtotal_energia_calculado"] = subtotal_energia
        
        # Verificar si el subtotal calculado coincide con el reportado
        subtotal_reportado = self._asegurar_numero(self.datos_generales.get("subtotal_base_energia", 0))
        totales["subtotal_energia_reportado"] = subtotal_reportado
        totales["diferencia_subtotal"] = subtotal_energia - subtotal_reportado
        
        # Total neto a pagar
        totales["neto_pagar_reportado"] = self._asegurar_numero(self.datos_generales.get("neto_pagar", 0))
        
        return totales
    
    @staticmethod
    def _asegurar_numero(valor):
        """
        Asegura que un valor sea numérico para operaciones aritméticas.
        
        Args:
            valor: Valor a convertir
            
        Returns:
            int o float: Valor convertido a numérico
        """
        if isinstance(valor, (int, float)):
            return valor
        
        if isinstance(valor, str):
            # Eliminar caracteres no numéricos excepto punto y signo negativo
            valor_limpio = valor.replace(',', '').replace('"', '')
            
            # Verificar si es un valor negativo
            es_negativo = valor_limpio.startswith('-')
            if es_negativo:
                valor_limpio = valor_limpio[1:]
            
            try:
                if '.' in valor_limpio:
                    resultado = float(valor_limpio)
                else:
                    resultado = int(valor_limpio)
                
                # Aplicar signo negativo si era negativo
                if es_negativo:
                    resultado = -resultado
                
                return resultado
            except ValueError:
                # Si no se puede convertir, devolver 0
                return 0
        
        return 0
    
    def obtener_parametros_especificos(self):
        """
        Obtiene los parámetros específicos de la factura (IR, Grupo, DIU INT, etc.)
        
        Returns:
            dict: Diccionario con los parámetros específicos
        """
        parametros = {}
        
        # Lista de parámetros específicos a extraer
        campos_especificos = [
            "ir", "grupo", "diu_int", "dium_int", 
            "fiu_int", "fium_int", "fiug", "diug"
        ]
        
        # Extraer cada parámetro de los datos generales
        for campo in campos_especificos:
            parametros[campo] = self._asegurar_numero(self.datos_generales.get(campo, 0))
        
        return parametros
    
    def validar_factura(self):
        """
        Valida la consistencia de los datos de la factura.
        
        Returns:
            dict: Diccionario con resultados de validación
        """
        validacion = {
            "errores": [],
            "advertencias": [],
            "es_valida": True
        }
        
        # Validar campos requeridos
        campos_requeridos = ["fecha_vencimiento", "periodo_facturacion", "neto_pagar"]
        for campo in campos_requeridos:
            if self.datos_generales.get(campo) in [0, "No encontrado", None, ""]:
                validacion["errores"].append(f"Campo requerido '{campo}' no encontrado")
                validacion["es_valida"] = False
        
        # Validar componentes
        if not self.datos_componentes:
            validacion["errores"].append("No se encontraron componentes de energía")
            validacion["es_valida"] = False
        
        # Validar totales
        totales = self.calcular_totales()
        if abs(totales["diferencia_subtotal"]) > 1:  # Tolerancia de 1 peso por redondeo
            validacion["advertencias"].append(
                f"Diferencia en subtotal de energía: {totales['diferencia_subtotal']} pesos"
            )
        
        # Validar fechas
        if self.datos_generales["fecha_vencimiento"] != "No encontrado":
            try:
                datetime.strptime(self.datos_generales["fecha_vencimiento"], "%Y-%m-%d")
            except ValueError:
                validacion["errores"].append("Formato de fecha de vencimiento inválido")
                validacion["es_valida"] = False
        
        return validacion
    
    def obtener_datos_procesados(self):
        """
        Obtiene todos los datos procesados de la factura.
        
        Returns:
            dict: Datos completos de la factura procesados
        """
        resultado = {
            "datos_generales": self.datos_generales,
            "componentes": self.datos_componentes,
            "totales_calculados": self.calcular_totales(),
            "parametros_especificos": self.obtener_parametros_especificos(),
            "validacion": self.validar_factura(),
            "fecha_procesamiento": self.fecha_procesamiento
        }
        
        return resultado


def validar_ruta_archivo(file_path):
    """
    Valida que la ruta del archivo exista y sea accesible.
    
    Args:
        file_path (str): Ruta del archivo a validar
        
    Returns:
        bool: True si la ruta es válida, False en caso contrario
    """
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe.")
        return False
    
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} no es un archivo.")
        return False
    
    # Para archivos CSV o de texto, verificar si se pueden leer
    if file_path.lower().endswith(('.csv', '.txt')):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Intentar leer el archivo
                file.read(1)
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    # Intentar leer con otra codificación
                    file.read(1)
            except Exception as e:
                print(f"Error al acceder al archivo {file_path}: {e}")
                return False
        except Exception as e:
            print(f"Error al acceder al archivo {file_path}: {e}")
            return False
    
    # Para archivos PDF, solo verificar si se pueden abrir en modo binario
    elif file_path.lower().endswith('.pdf'):
        try:
            with open(file_path, 'rb') as file:
                # Intentar leer el archivo en modo binario
                file.read(1)
        except Exception as e:
            print(f"Error al acceder al archivo PDF {file_path}: {e}")
            return False
    
    return True


def normalizar_valor_monetario(valor):
    """
    Normaliza un valor monetario para presentación en reportes.
    
    Args:
        valor: Valor monetario a normalizar
        
    Returns:
        str: Valor monetario normalizado con formato de moneda
    """
    try:
        # Asegurar que el valor sea numérico
        if isinstance(valor, str):
            valor = valor.replace(',', '').replace('"', '')
            valor = float(valor) if '.' in valor else int(valor)
        
        # Formatear con separador de miles y 2 decimales
        return f"${valor:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')
    except (ValueError, TypeError):
        return str(valor)