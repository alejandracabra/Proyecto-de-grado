"""Diccionario lógico; las columnas de origen requieren aprobación institucional."""

VARIABLES = {
    "capital_cuenta": "Saldo disponible de la cuenta individual.",
    "bono": "Bono pensional computable, si corresponde.",
    "capital_1": "Capital requerido para una prestación de 1 SMMLV.",
    "capital_13": "Capital requerido para una prestación de 1,3 SMMLV.",
    "capital_2": "Capital requerido para una prestación de 2 SMMLV.",
    "capital_actual": "Capital requerido para la mesada actual.",
    "mesada_actual": "Mesada actual, en unidades monetarias documentadas.",
    "mesadas_anuales": "Número de mesadas anuales.",
    "edad_titular": "Edad del titular; definición pendiente de validación.",
    "sexo_titular": "Sexo del titular; no se presupone equivalencia con sexo1.",
    "beneficiarios": "Características y derechos de beneficiarios, si están autorizados.",
    "tipo_prestacion": "Tipo de riesgo o prestación.",
    "fecha_corte": "Fecha de corte de la observación.",
    "unidad_monetaria": "Unidad monetaria y escala.",
}

# Sin equivalencias predeterminadas: completar solo tras validación institucional.
MAPEO_INSTITUCIONAL: dict[str, str] = {}
