"""
Definición de patrones Regex para la extracción de datos.
Separación estricta entre patrones de MONTO y patrones de TEXTO/INFO.
"""

import re

# --- CABECERA Y DATOS DEL CLIENTE ---
PATRONES_ENCABEZADO = {
    'numero_factura': re.compile(r'(?:No\.|Número)\s*(?:Factura)?\s*[:.]?\s*(\d+)', re.IGNORECASE),
    'fecha_expedicion': re.compile(r'Fecha\s*expedici[óo]n\s*[:.]?\s*(\d{4}[-/]\d{2}[-/]\d{2})', re.IGNORECASE),
    'fecha_vencimiento': re.compile(r'Fecha\s*vencimiento\s*[:.]?\s*(\d{4}[-/]\d{2}[-/]\d{2})', re.IGNORECASE),
    'periodo_facturacion': re.compile(r'Periodo\s*Facturaci[óo]n\s*[:.]?\s*(\d{4}[-/]\d{2}[-/]\d{2})\s*(?:A|-|hasta)\s*(\d{4}[-/]\d{2}[-/]\d{2})', re.IGNORECASE),
    'cufe': re.compile(r'CUFE\s*[:.]?\s*([a-fA-F0-9]+)', re.IGNORECASE),
    'cliente_nombre': re.compile(r'Señores\s*[:.]?\s*(.+?)(?=\s+(?:Direcci[óo]n|Nit|Email|No\.|Ciudad)|$)', re.IGNORECASE),
    'nit_cliente': re.compile(r'Nit\s*[:.]?\s*([\d-]+)', re.IGNORECASE),
    'contrato': re.compile(r'No\.\s*Contrato\s*[:.]?\s*([A-Z0-9-]+)', re.IGNORECASE),
    'ciudad': re.compile(r'Ciudad\s*[:.]?\s*(.+?)(?=\s+(?:Tel[ée]fono|Email|No\.)|$)', re.IGNORECASE),
    'direccion_cliente': re.compile(r'Direcci[óo]n\s*[:.]?\s*(.+?)(?=\s+(?:Email|No\.|Ciudad|Tel[ée]fono)|$)', re.IGNORECASE),
    'email_cliente': re.compile(r'Email\s*[:.]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
    'telefono_cliente': re.compile(r'Tel[ée]fono\s*[:.]?\s*([\d\s()-]+)(?=\s+Concepto|$)', re.IGNORECASE),
}

# --- MONTOS FINANCIEROS (Se extraen con limpiar_moneda) ---
PATRONES_MONTO = {
    'total_pagar': re.compile(r'TOTAL\s*A\s*PAGAR', re.IGNORECASE),
    'total_facturado': re.compile(r'TOTAL\s*FACTURADO', re.IGNORECASE),
    # Corrección clave: (?:/Prepago)? hace opcional pero consume "/Prepago" si existe
    'anticipo': re.compile(r'Anticipo(?:/Prepago)?', re.IGNORECASE),
    'intereses': re.compile(r'Intereses\s*financieros', re.IGNORECASE),
}

# --- INFORMACIÓN DE PIE DE PÁGINA (Se extraen como TEXTO usando grupos de captura) ---
PATRONES_INFO_PIE = {
    # Valor en letras
    'valor_letras': re.compile(r'SON\s*[:.]?\s*(.+?)(?=\s+Medio|$)', re.IGNORECASE),
    
    # Datos Bancarios
    'medio_pago': re.compile(r'Medio\s*de\s*pago\s*[:.]?\s*(.+?)(?=\s+Entidad|$)', re.IGNORECASE),
    'banco': re.compile(r'Entidad\s*[:.]?\s*(.+?)(?=\s+(?:Cuenta|N[úu]mero)|$)', re.IGNORECASE),
    'tipo_cuenta': re.compile(r'Cuenta\s*[:.]?\s*(.+?)(?=\s+N[úu]mero|$)', re.IGNORECASE),
    'num_cuenta': re.compile(r'N[úu]mero\s*[:.]?\s*(\d+)', re.IGNORECASE),
    'forma_pago': re.compile(r'Forma\s*de\s*pago\s*[:.]?\s*(.+?)(?=\s+Observaciones|$)', re.IGNORECASE),
    
    # Indicadores
    'ipp': re.compile(r'IPP\s*Provisional\s*[:.]?\s*([\d.,]+)', re.IGNORECASE),
    'trm': re.compile(r'TRM\s*.*[:.]?\s*([\d.,]+)', re.IGNORECASE),
    
}

# Configuración para detección de tablas
ENCABEZADOS_TABLA_ITEMS = [
    'Item', 'Concepto', 'Total', 'Descripción', 'Referencia'
]