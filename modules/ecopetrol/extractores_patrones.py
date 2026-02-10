"""
Módulo con todos los patrones regex para extracción de datos de facturas.
Este módulo centraliza todos los patrones de expresiones regulares utilizados
para extraer información de las facturas de energía.
"""

# Patrones regex centralizados para extracción de datos generales
PATRONES_CONCEPTO = {
    'subtotal_base_energia': [
        # Nuevos patrones para manejar formato con .0 al final
        r'Subtotal\s+base\s+energÃ­a[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\tbase\tenergÃ­a[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\s+base\s+energía[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\tbase\tenergía[,\s]*"([0-9,]+(?:\.\d+)?)"',
        # Patrones adicionales para capturar el valor completo
        r'Subtotal\s+base\s+energÃ­a[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Subtotal\tbase\tenergÃ­a[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos mantenidos por compatibilidad
        r'Subtotal base energía.*?"([-\d,]+)"',
        r'Subtotal\tbase\tenergía.*?"([-\d,]+)"',
        r'Subtotal base energía.*?(?<!")(\d+)(?!")',
        r'Subtotal\tbase\tenergía.*?(?<!")(\d+)(?!")'
    ],
    'contribucion': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'ContribuciÃ³n[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Contribución[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'ContribuciÃ³n[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Contribución[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos mantenidos por compatibilidad
        r'Contribución.*?"([-\d,]+)"',
        r'Contribución.*?(?<!")(\d+)(?!")'
    ],
    'contribucion_otros_meses': [
        r'ContribuciÃ³n\s+de\s+otros\s+meses[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Contribución\s+de\s+otros\s+meses[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Contribución de otros meses.*?([-\d,]+)',
        r'Contribución\tde\totros\tmeses.*?([-\d,]+)',
        r'Contribución de otros meses.*?(?<!")(\d+)(?!")',
        r'Contribución\tde\totros\tmeses.*?(?<!")(\d+)(?!")'
    ],
    'subtotal_energia_contribucion_kwh': [
        r'\$\/kWh,\$\s*Subtotal\s*energia\s*\+\s*contribución,\s*([-\d.,]+)',
        r'\$\/kWh,\$\s*Subtotal\tenerg[ií]a\t\+\tcontribución,\s*([-\d.,]+)'
    ],
    'subtotal_energia_contribucion_pesos': [
     # NUEVOS PATRONES CORREGIDOS - Capturar el segundo valor después de la coma
        r'Subtotal\s+energia\s*\+\s*contribuciÃ³n[,\s]*[\d.]+[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\tenerg[ií]a\t\+\tcontribuciÃ³n[,\s]*[\d.]+[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\s+energia\s*\+\s*contribución[,\s]*[\d.]+[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\tenergía\t\+\tcontribución[,\s]*[\d.]+[,\s]*"([0-9,]+(?:\.\d+)?)"',
        # Patrón más específico para el formato exacto del ejemplo
        r'Subtotal\s+energia\s*\+\s*contribuciÃ³n,[\d.]+,"([0-9,]+(?:\.\d+)?)"',
        r'Subtotal\tenerg[ií]a\t\+\tcontribuciÃ³n,[\d.]+,"([0-9,]+(?:\.\d+)?)"',
        # Patrones alternativos para capturar el segundo valor
        r'Subtotal\s+energia\s*\+\s*contribuciÃ³n[,\s]*[^,]+[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Subtotal\tenerg[ií]a\t\+\tcontribuciÃ³n[,\s]*[^,]+[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos como respaldo (modificados para evitar capturar el primer valor)
        r'\$\/kWh,\$\s*Subtotal\s*energia\s*\+\s*contribución,\s*[-\d.,]+,\s*"([-\d,]+)"',
        r'\$\/kWh,\$\s*Subtotal\tenerg[ií]a\t\+\tcontribución,\s*[-\d.,]+,\s*"([-\d,]+)"',
        r'\$\/kWh,\$\s*Subtotal\s*energia\s*\+\s*contribución,\s*[-\d.,]+,\s*(?<!")(\d+)(?!")',
        r'\$\/kWh,\$\s*Subtotal\tenerg[ií]a\t\+\tcontribución,\s*[-\d.,]+,\s*(?<!")(\d+)(?!")'
    ],
    'otros_cobros': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Otros\s+cobros[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Otros\tcobros[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Otros\s+cobros[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Otros\tcobros[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Otros cobros.*?"([-\d,]+)"',
        r'Otros\tcobros.*?"([-\d,]+)"',
        r'Otros cobros.*?(?<!")(\d+)(?!")',
        r'Otros\tcobros.*?(?<!")(\d+)(?!")'
    ],
    'sobretasa': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Sobretasa[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Sobretasa[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Sobretasa.*?([-\d,]+)',
        r'Sobretasa.*?(?<!")(\d+)(?!")'
    ],
    'ajustes_cargos_regulados': [
        r'Ajustes\s+cargos\s+regulados[,\s]*"?([-0-9.,]+)"?',
        r'Ajustes\s+cargos\s+regulados[,\s]*"(-[\d,.]+)"',
        r'Ajustes\tcargos\tregulados[,\s]*"(-[\d,.]+)"',
        r'Ajustes\scargos\sregulados,\s*"(-[\d,.]+)"',
        r'Ajustes\tcargos\tregulados,\s*"(-[\d,.]+)"',
        r'Ajustes cargos regulados.*?"([-\d,]+)"',
        r'Ajustes\tcargos\tregulados.*?"([-\d,]+)"',
        r'Ajustes cargos regulados.*?(?<!")(-?\d+)(?!")',
        r'Ajustes\tcargos\tregulados.*?(?<!")(-?\d+)(?!")'
    ],
    'compensaciones': [
        r'Compensaciones[,\s]*"?([-0-9,]+(?:\.\d+)?)"?',
        r'Compensaciones.*?"([-\d,]+)"',
        r'Compensaciones.*?(?<!")(\d+)(?!")'
    ],
    'saldo_cartera': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Saldo\s+cartera[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Saldo\tcartera[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Saldo\s+cartera[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Saldo\tcartera[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Saldo cartera.*?"([-\d,]+)"',
        r'Saldo\tcartera.*?([-\d,]+)',
        r'Saldo cartera.*?(?<!")(\d+)(?!")',
        r'Saldo\tcartera.*?(?<!")(\d+)(?!")'
    ],
    'interes_mora': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'InterÃ©s\s+por\s+Mora[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Interés\s+por\s+Mora[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Interés\tpor\tMora[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'InterÃ©s\s+por\s+Mora[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Interés\s+por\s+Mora[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Interés\tpor\tMora[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Interés por Mora.*?"([-\d,]+)"',
        r'Interés\tpor\tMora.*?"([-\d,]+)"',
        r'Interés por Mora.*?(?<!")(\d+)(?!")',
        r'Interés\tpor\tMora.*?(?<!")(\d+)(?!")'
    ],
    'recobros': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Recobros[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Recobros[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Recobros.*?([-\d,]+)',
        r'Recobros.*?(?<!")(\d+)(?!")'
    ],
    'alumbrado_publico': [
        # Nuevos patrones mejorados para capturar el valor completo con decimales
        r'Alumbrado\s+pÃºblico\s+\(\*\*\)[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Alumbrado\s+público\s+\(\*\*\)[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Alumbrado\s+pÃºblico[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Alumbrado\s+público[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Alumbrado\tpúblico[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Alumbrado\tpÃºblico[,\s]*"([0-9,]+(?:\.\d+)?)"',
        # Patrones con comillas opcionales
        r'Alumbrado\s+pÃºblico\s+\(\*\*\)[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Alumbrado\s+público[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Alumbrado público.*?([-\d,]+)',
        r'Alumbrado\tpúblico.*?"([-\d,]+)"',
        r'Alumbrado público.*?(?<!")(\d+)(?!")',
        r'Alumbrado\tpúblico.*?(?<!")(\d+)(?!")'
    ],
    'impuesto_alumbrado_publico': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Impuesto\s+alumbrado\s+pÃºblico[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Impuesto\s+alumbrado\s+público[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Impuesto\talumbrado\tpúblico[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Impuesto\talumbrado\tpÃºblico[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Impuesto\s+alumbrado\s+pÃºblico[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Impuesto\s+alumbrado\s+público[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Impuesto\talumbrado\tpúblico[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Impuesto\talumbrado\tpÃºblico[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos
        r'Impuesto alumbrado público.*?([-\d,]+)',
        r'Impuesto\talumbrado\tpúblico.*?"([-\d,]+)"',
        r'Impuesto alumbrado público.*?(?<!")(\d+)(?!")',
        r'Impuesto\talumbrado\tpúblico.*?(?<!")(\d+)(?!")'
    ],
    'ajuste_iap_otros_meses': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Ajuste\s+IAP\s+otros\s+meses[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Ajuste\tIAP\totros\tmeses[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Ajuste\s+IAP\s+otros\s+meses[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Ajuste\tIAP\totros\tmeses[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Ajuste IAP otros meses.*?([-\d,]+)',
        r'Ajuste\tIAP\totros\tmeses.*?"([-\d,]+)"',
        r'Ajuste IAP otros meses.*?(?<!")(\d+)(?!")',
        r'Ajuste\tIAP\totros\tmeses.*?(?<!")(\d+)(?!")'
    ],
    'convivencia_ciudadana': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Convivencia\s+ciudadana\s+\(\*\*\*\)[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Convivencia\s+ciudadana[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Convivencia\tciudadana[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Convivencia\s+ciudadana\s+\(\*\*\*\)[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Convivencia\s+ciudadana[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Convivencia\tciudadana[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos
        r'Convivencia ciudadana.*?"([-\d,]+)"',
        r'Convivencia\tciudadana.*?"([-\d,]+)"',
        r'Convivencia ciudadana.*?(?<!")(\d+)(?!")',
        r'Convivencia\tciudadana.*?(?<!")(\d+)(?!")'
    ],
    'tasa_especial_convivencia': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Tasa\s+especial\s+convivencia\s+ciudadana[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Tasa\tespecial\tconvivencia\tciudadana[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Tasa\s+especial\s+convivencia\s+ciudadana[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Tasa\tespecial\tconvivencia\tciudadana[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Tasa especial convivencia ciudadana.*?"([-\d,]+)"',
        r'Tasa\tespecial\tconvivencia\tciudadana.*?"([-\d,]+)"',
        r'Tasa especial convivencia ciudadana.*?(?<!")(\d+)(?!")',
        r'Tasa\tespecial\tconvivencia\tciudadana.*?(?<!")(\d+)(?!")'
    ],
    'ajuste_tasa_convivencia': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Ajuste\s+tasa\s+convivencia\s+otros\s+meses[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Ajuste\ttasa\tconvivencia\totros\tmeses[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Ajuste\s+tasa\s+convivencia\s+otros\s+meses[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Ajuste\ttasa\tconvivencia\totros\tmeses[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Ajuste tasa convivencia otros meses.*?"([-\d,]+)"',
        r'Ajuste\ttasa\tconvivencia\totros\tmeses.*?"([-\d,]+)"',
        r'Ajuste tasa convivencia otros meses.*?(?<!")(\d+)(?!")',
        r'Ajuste\ttasa\tconvivencia\totros\tmeses.*?(?<!")(\d+)(?!")'
    ],
    'total_servicio_energia_impuestos': [
        # Nuevos patrones mejorados
        r'Total\s+servicio\s+energÃ­a\s+\+\s+impuestos[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Total\s+servicio\s+energía\s+\+\s+impuestos[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Total\tservicio\tenergía\t\+\timpuestos[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Total\tservicio\tenergÃ­a\t\+\timpuestos[,\s]*"([0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Total\s+servicio\s+energÃ­a\s+\+\s+impuestos[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Total\s+servicio\s+energía\s+\+\s+impuestos[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos
        r'Total servicio energía \+ impuestos.*?"([-\d,]+)"',
        r'Total\tservicio\tenergía\t\+\timpuestos.*?"([-\d,]+)"',
        r'Total\tservicio\tenergía\t\\\+\timpuestos.*?"([-\d,]+)"',
        r'Total servicio energía \+ impuestos.*?(?<!")(\d+)(?!")',
        r'Total\tservicio\tenergía\t\+\timpuestos.*?(?<!")(\d+)(?!")',
        r'Total\tservicio\tenergía\t\\\+\timpuestos.*?(?<!")(\d+)(?!")'
    ],
    'ajuste_decena': [
        # Nuevos patrones mejorados para capturar valores negativos, decimales y grandes
        r'Ajuste\s+a\s+la\s+decena[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        r'Ajuste\ta\tla\tdecena[,\s]*"([-0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Ajuste\s+a\s+la\s+decena[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        r'Ajuste\ta\tla\tdecena[,\s]*"?(-?[0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos por compatibilidad
        r'Ajuste a la decena.*?([-\d,]+)',
        r'Ajuste\ta\tla\tdecena.*?([-\d,]+)',
        r'Ajuste a la decena.*?(?<!")(\d+)(?!")',
        r'Ajuste\ta\tla\tdecena.*?(?<!")(\d+)(?!")'
    ],
    'neto_pagar': [
        # Nuevos patrones mejorados
        r'Neto\s+a\s+pagar[,\s]*"([0-9,]+(?:\.\d+)?)"',
        r'Neto\ta\tpagar[,\s]*"([0-9,]+(?:\.\d+)?)"',
        # Con comillas opcionales
        r'Neto\s+a\s+pagar[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        # Patrones antiguos
        r'Neto a pagar.*?"([-\d,]+)"',
        r'Neto\ta\tpagar.*?"([-\d,]+)"',
        r'Neto a pagar.*?(?<!")(\d+)(?!")',
        r'Neto\ta\tpagar.*?(?<!")(\d+)(?!")'
    ],
    'energia_reactiva_inductiva': [
        r'Energ[ií]a\s*reactiva\s*inductiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Energ[ií]a\treactiva\tinductiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Energ[ií]a\s*reactiva\s*inductiva[,\s]*(?<!")([0-9.,]+)(?!")',
        r'Energ[ií]a\treactiva\tinductiva[,\s]*(?<!")([0-9.,]+)(?!")'
    ],
    'energia_reactiva_capacitiva': [
        r'Energ[ií]a\s*reactiva\s*capacitiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Energ[ií]a\treactiva\tcapacitiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Energ[ií]a\s*reactiva\s*capacitiva[,\s]*(?<!")([0-9.,]+)(?!")',
        r'Energ[ií]a\treactiva\tcapacitiva[,\s]*(?<!")([0-9.,]+)(?!")'
    ],
    'total_energia_reactiva': [
        r'Total\s*energ[ií]a\s*reactiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Total\tenerg[ií]a\treactiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Total\s*energ[ií]a\s*reactiva[,\s]*(?<!")([0-9.,]+)(?!")',
        r'Total\tenerg[ií]a\treactiva[,\s]*(?<!")([0-9.,]+)(?!")'
    ],
    'energia_activa': [
        r'Energ[ií]a\s*activa[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Energ[ií]a\tactiva[,\s]*"?([0-9,]+(?:\.\d+)?)"?',
        r'Energ[ií]a\s*activa[,\s]*(?<!")([0-9.,]+)(?!")',
        r'Energ[ií]a\tactiva[,\s]*(?<!")([0-9.,]+)(?!")'
    ]
}

# Patrones para componentes de energía - soporta formato viejo y nuevo
COMPONENTES_ENERGIA = [
    {
        "name": "Generación",
        "patterns": [
            # Formato viejo con kWh
            r'1\.\s+Generación,"?([-\d,]*)"?,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?',
            # Formato nuevo sin kWh
            r'1\.\s+Generación,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": True  # Indica que puede tener kWh en formato viejo
    },
    {
        "name": "Comercialización",
        "patterns": [
            r'2\.\s+Comercialización,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": False
    },
    {
        "name": "Transmisión",
        "patterns": [
            r'3\.\s+Transmisión,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": False
    },
    {
        "name": "Distribución",
        "patterns": [
            r'4\.\s+Distribución,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": False
    },
    {
        "name": "Pérdidas",
        "patterns": [
            r'5\.\s+Perdidas\s+\(\*\),([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?',
            r'5\.\s+Pérdidas\s+\(\*\),([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": False
    },
    {
        "name": "Restricciones",
        "patterns": [
            r'6\.\s+Restricciones,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": False
    },
    {
        "name": "Otros cargos",
        "patterns": [
            r'7\.\s+Otros\s+cargos,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": False
    },
    {
        "name": "Energía inductiva + capacitiva",
        "patterns": [
            # Formato viejo con kWh primero
            r'8\.\s+Energía\s+inductiva\s+\+\s+capacitiva\s+facturada,"?([-\d,]*)"?,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?',
            # Formato nuevo sin kWh
            r'8\.\s+Energía\s+inductiva\s+\+\s+capacitiva\s+facturada,([-\d\.]+),"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?,"?([-\d,]+\.?\d*)"?'
        ],
        "has_kwh": True  # Puede tener kWh en formato viejo
    }
]

# Patrones para extraer los parámetros específicos datos OR
PATRONES_PARAMETROS_ESPECIFICOS = {
    'ir': [
        # PATRONES CORREGIDOS PARA IR
        # Patrón específico para cuando IR está vacío seguido de coma y luego Grupo
        r'IR:\s*,\s*Grupo:',  # Este patrón detecta cuando IR está vacío
        # Patrón para cuando IR tiene un valor antes de la coma
        r'IR:\s*(\d+(?:\.\d+)?)\s*,',  # Captura el valor de IR solo si hay un número antes de la coma
        r'IR:\s+(\d+(?:\.\d+)?)\s*(?:,|$)',  # IR con espacio y valor, seguido de coma o fin de línea
        # Patrón para IR sin coma después (al final de línea)
        r'IR:\s*(\d+(?:\.\d+)?)\s*$'
    ],
    'grupo': [
        r'Grupo:\s*(?:,|\s+)(\d+)',
        r'Grupo:,(\d+)',
        r'Grupo:\s*(\d+)'
    ],
    'diu_int': [
        r'DIU\s+INT:\s*([\d\.]+)',
        r'DIU INT:\s*(?:,|\s+)([^,\s]+)',
        r'DIU INT:,([^,]+)'
    ],
    'dium_int': [
        r'DIUM\s+INT:\s*([\d\.]+)',
        r'DIUM INT:\s*(?:,|\s+)([^,\s]+)',
        r'DIUM INT:,([^,]+)'
    ],
    'fiu_int': [
        r'FIU\s+INT:\s*([\d\.]+)',
        r'FIU INT:\s*(?:,|\s+)([^,\s]+)',
        r'FIU INT:,([^,]+)'
    ],
    'fium_int': [
        r'FIUM\s+INT:\s*([\d\.]+)',
        r'FIUM INT:\s*(?:,|\s+)([^,\s]+)',
        r'FIUM INT:,([^,]+)'
    ],
    'fiug': [
        r'FIUG:\s*(?:,|\s+)([\d.]+)',
        r'FIUG:\s*([\d.]+)',
        r'FIUG:\s*([\d.]+),\s*DIUG:\s*([\d.]+)'  # Patrón combinado
    ],
    'diug': [
        r'DIUG:\s*(?:,|\s+)([\d.]+)',
        r'DIUG:\s*([\d.]+)',
        r'FIUG:\s*([\d.]+),\s*DIUG:\s*([\d.]+)'  # Patrón combinado
    ],
    # Nuevos patrones combinados para extraer valores de la misma línea
    'diu_dium_int': [
        r'DIU\s+INT:\s*([\d\.]+),DIUM\s+INT:\s*([\d\.]+)'
    ],
    'fiu_fium_int': [
        r'FIU\s+INT:\s*([\d\.]+),FIUM\s+INT:\s*([\d\.]+)'
    ]
}