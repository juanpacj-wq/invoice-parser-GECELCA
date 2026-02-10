"""
Módulo de procesamiento y lógica de negocio.
Estructura los datos en tres niveles: 
1. Conceptos (Detalle Vertical)
2. Generales (Resumen Horizontal)
3. Comparación (Lista Maestra Vertical para conciliación con llaves)
"""

import logging
from utils import limpiar_moneda

logger = logging.getLogger(__name__)

class FacturaProcessor:
    def __init__(self, datos_extraidos):
        """
        Inicializa el procesador con los datos crudos extraídos.
        """
        self.datos_generales = datos_extraidos.get('datos_generales', {})
        self.items = datos_extraidos.get('items', [])
        self.errores = []

    def validar_datos(self):
        """
        Validaciones de integridad de los datos.
        """
        # 1. Validar campos mínimos
        if 'numero_factura' not in self.datos_generales:
            self.errores.append("No se encontró el Número de Factura")

        # 2. Validar coherencia matemática
        if self.items:
            suma_items = sum(item.get('total', 0) for item in self.items)
            total_leido = limpiar_moneda(self.datos_generales.get('total_facturado', 0))
            if total_leido == 0:
                total_leido = limpiar_moneda(self.datos_generales.get('total_pagar', 0))
            
            if total_leido > 0:
                diferencia = abs(suma_items - total_leido)
                if diferencia > 100: 
                    self.errores.append(f"Diferencia matemática: Suma Items ({suma_items:,.2f}) != Total Leído ({total_leido:,.2f})")

    def obtener_datos_procesados(self):
        """
        Genera las estructuras de datos para el Excel.
        """
        self.validar_datos()
        dg = self.datos_generales
        
        # Variables clave
        num_factura = dg.get('numero_factura', '')
        contrato = dg.get('contrato', '')
        
        # --- 1. DATASET VERTICAL (CONCEPTOS) ---
        filas_conceptos = []
        if self.items:
            for item in self.items:
                fila = {
                    'No. Factura': num_factura,
                    'No. Contrato': contrato,
                    'Item ID': item.get('item', ''),
                    'Referencia': item.get('referencia', ''),
                    'Concepto': item.get('concepto', 'DESCONOCIDO'),
                    'Unidad': item.get('unidad', ''),
                    'Cantidad': item.get('cantidad', 0),
                    'Tarifa': item.get('tarifa', 0),
                    'Valor Total Item': item.get('total', 0)
                }
                filas_conceptos.append(fila)
        else:
            filas_conceptos.append({
                'No. Factura': num_factura, 'No. Contrato': contrato,
                'Item ID': '-', 'Referencia': '-', 'Concepto': 'SIN DETALLE DETECTADO',
                'Unidad': '-', 'Cantidad': 0, 'Tarifa': 0, 'Valor Total Item': 0
            })

        # --- 2. DATASET HORIZONTAL (VARIABLES GENERALES) ---
        fila_general = {
            'Nombre Archivo': dg.get('nombre_archivo', ''),
            'No. Factura': num_factura,
            'CUFE': dg.get('cufe', ''),
            'No. Contrato': contrato,
            'Fecha Expedición': dg.get('fecha_expedicion', ''),
            'Fecha Vencimiento': dg.get('fecha_vencimiento', ''),
            'Periodo Facturación': dg.get('periodo_facturacion', ''),
            'Cliente': dg.get('cliente_nombre', ''),
            'NIT Cliente': dg.get('nit_cliente', ''),
            'Dirección': dg.get('direccion_cliente', ''),
            'Ciudad': dg.get('ciudad', ''),
            'Email': dg.get('email_cliente', ''),
            'Teléfono': dg.get('telefono_cliente', ''),
            'Total Facturado (Subtotal)': limpiar_moneda(dg.get('total_facturado', 0)),
            'Intereses': limpiar_moneda(dg.get('intereses', 0)),
            'Anticipo/Prepago': limpiar_moneda(dg.get('anticipo', 0)),
            'Total a Pagar': limpiar_moneda(dg.get('total_pagar', 0)),
            'Valor en Letras': dg.get('valor_letras', ''),
            'Medio de Pago': dg.get('medio_pago', ''),
            'Banco': dg.get('banco', ''),
            'Tipo Cuenta': dg.get('tipo_cuenta', ''),
            'No. Cuenta': dg.get('num_cuenta', ''),
            'Forma de Pago': dg.get('forma_pago', ''),
            'IPP': dg.get('ipp', ''),
            'TRM': dg.get('trm', ''),
            'Observaciones': dg.get('observaciones', ''),
            'Items Detectados': len(self.items),
            'Estado Validación': "OK" if not self.errores else "REVISAR",
            'Errores': "; ".join(self.errores) if self.errores else ""
        }

        # --- 3. DATASET COMPARACIÓN (LISTA MAESTRA VERTICAL) ---
        # Ahora incluye No. Factura y No. Contrato en cada fila para poder consolidar múltiples PDFs
        filas_comparacion = []
        
        # A. Agregar Variables Generales
        campos_a_comparar = [
            'CUFE', 'Fecha Expedición', 'Fecha Vencimiento',
            'Periodo Facturación', 'Cliente', 'NIT Cliente', 'Total Facturado (Subtotal)',
            'Total a Pagar', 'Anticipo/Prepago', 'Banco', 'No. Cuenta'
        ]
        
        for key in campos_a_comparar:
            filas_comparacion.append({
                'No. Factura': num_factura, # <--- LLAVE AGREGADA
                'No. Contrato': contrato,   # <--- LLAVE AGREGADA
                'Tipo': 'General',
                'Variable': key,
                'Valor PDF': fila_general.get(key, ''),
                'Valor Data Lake': '' 
            })
            
        # B. Agregar Conceptos (Items)
        if self.items:
            for idx, item in enumerate(self.items, 1):
                prefijo = f"Item {idx}"
                
                # Concepto
                filas_comparacion.append({
                    'No. Factura': num_factura, # <--- LLAVE AGREGADA
                    'No. Contrato': contrato,   # <--- LLAVE AGREGADA
                    'Tipo': 'Detalle',
                    'Variable': f"{prefijo} - Concepto",
                    'Valor PDF': item.get('concepto', ''),
                    'Valor Data Lake': ''
                })
                # Cantidad
                filas_comparacion.append({
                    'No. Factura': num_factura,
                    'No. Contrato': contrato,
                    'Tipo': 'Detalle',
                    'Variable': f"{prefijo} - Cantidad",
                    'Valor PDF': item.get('cantidad', 0),
                    'Valor Data Lake': ''
                })
                # Tarifa
                filas_comparacion.append({
                    'No. Factura': num_factura,
                    'No. Contrato': contrato,
                    'Tipo': 'Detalle',
                    'Variable': f"{prefijo} - Tarifa",
                    'Valor PDF': item.get('tarifa', 0),
                    'Valor Data Lake': ''
                })
                # Total
                filas_comparacion.append({
                    'No. Factura': num_factura,
                    'No. Contrato': contrato,
                    'Tipo': 'Detalle',
                    'Variable': f"{prefijo} - Total",
                    'Valor PDF': item.get('total', 0),
                    'Valor Data Lake': ''
                })

        return {
            'conceptos': filas_conceptos,
            'generales': [fila_general],
            'comparacion': filas_comparacion,
            'validacion': {
                'es_valida': len(self.errores) == 0,
                'errores': self.errores,
                'factura': num_factura # Para el log
            }
        }