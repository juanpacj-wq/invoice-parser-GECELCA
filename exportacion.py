"""
Módulo para la exportación de datos a Excel.
Genera un archivo con múltiples hojas: Detalle, Resumen y Comparación.
"""

import pandas as pd
import logging
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

class ExportadorExcel:
    def __init__(self, datos_procesados, ruta_salida):
        """
        Inicializa el exportador.
        Args:
            datos_procesados (dict): Diccionario con listas 'conceptos', 'generales', 'comparacion' y 'validacion'.
            ruta_salida (str): Ruta completa donde se guardará el archivo .xlsx.
        """
        self.datos = datos_procesados
        self.ruta_salida = ruta_salida

    def ajustar_ancho_columnas(self, writer):
        """
        Ajusta automáticamente el ancho de las columnas en todas las hojas.
        """
        workbook = writer.book
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                
                for cell in column:
                    try:
                        if cell.value:
                            val_len = len(str(cell.value))
                            max_length = max(max_length, val_len)
                    except:
                        pass
                
                adjusted_width = min(max(max_length + 2, 10), 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    def exportar(self):
        """
        Ejecuta la exportación a Excel.
        """
        try:
            # 1. Preparar DataFrames
            df_conceptos = pd.DataFrame(self.datos.get('conceptos', []))
            df_generales = pd.DataFrame(self.datos.get('generales', []))
            df_comparacion = pd.DataFrame(self.datos.get('comparacion', []))
            
            # Validación puede ser una lista (si es consolidado) o dict (si es individual)
            validacion_data = self.datos.get('validacion', [])
            if isinstance(validacion_data, dict):
                # Caso individual 
                errores = validacion_data.get('errores', [])
                df_validacion = pd.DataFrame({
                    'Fecha Proceso': [pd.Timestamp.now()],
                    'No. Factura': [validacion_data.get('factura', 'N/A')],
                    'Es Válida': ["SÍ" if validacion_data.get('es_valida') else "NO"],
                    'Errores': ["; ".join(errores)] if errores else ["Ninguno"]
                })
            else:
                # Caso masivo (lista de logs)
                df_validacion = pd.DataFrame(validacion_data)

            # 2. Orden Columnas - HOJA CONCEPTOS
            cols_conceptos_orden = [
                'No. Factura', 'No. Contrato', 'Item ID', 'Referencia', 
                'Concepto', 'Unidad', 'Cantidad', 'Tarifa', 'Valor Total Item'
            ]
            
            if not df_conceptos.empty:
                cols_existentes = [c for c in cols_conceptos_orden if c in df_conceptos.columns]
                otras = [c for c in df_conceptos.columns if c not in cols_existentes]
                df_conceptos = df_conceptos[cols_existentes + otras]

            # 3. Orden Columnas - HOJA GENERALES
            cols_generales_orden = [
                'Nombre Archivo', 'No. Factura', 'CUFE', 'No. Contrato',
                'Fecha Expedición', 'Fecha Vencimiento', 'Periodo Facturación',
                'Cliente', 'NIT Cliente', 'Dirección', 'Ciudad', 'Email', 'Teléfono',
                'Total Facturado (Subtotal)', 'Intereses', 'Anticipo/Prepago', 'Total a Pagar', 
                'Valor en Letras', 'Medio de Pago', 'Banco', 'Tipo Cuenta', 'No. Cuenta', 
                'Forma de Pago', 'IPP', 'TRM', 'Observaciones', 
                'Items Detectados', 'Estado Validación', 'Errores'
            ]
            
            if not df_generales.empty:
                cols_existentes = [c for c in cols_generales_orden if c in df_generales.columns]
                otras = [c for c in df_generales.columns if c not in cols_existentes]
                df_generales = df_generales[cols_existentes + otras]

            # 4. Orden Columnas - HOJA COMPARACIÓN
            cols_comparacion_orden = [
                'No. Factura',     
                'No. Contrato',   
                'Tipo', 
                'Variable', 
                'Valor PDF', 
                'Valor Data Lake'
            ]
            if not df_comparacion.empty:
                # Asegurar orden y columnas existentes
                cols_existentes = [c for c in cols_comparacion_orden if c in df_comparacion.columns]
                df_comparacion = df_comparacion[cols_existentes]

            # 5. Escribir a Excel
            with pd.ExcelWriter(self.ruta_salida, engine='openpyxl') as writer:
                df_conceptos.to_excel(writer, sheet_name='Conceptos_Vertical', index=False)
                df_generales.to_excel(writer, sheet_name='Variables_Generales', index=False)
                df_comparacion.to_excel(writer, sheet_name='Comparacion', index=False)
                df_validacion.to_excel(writer, sheet_name='Log_Proceso', index=False)
                
                self.ajustar_ancho_columnas(writer)
                
            return self.ruta_salida
            
        except Exception as e:
            logger.error(f"Error al exportar a Excel: {e}")
            raise