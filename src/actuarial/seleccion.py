"""Reglas comunes de selección preliminar para datos institucionales."""
import numpy as np
import pandas as pd
from .validacion import mascara_capital

C = 'Capital +Bono'
K1 = 'capital_necesario_sm'
K13 = 'capital_necesario_1.3_sm'
K2 = 'capital_necesario_2_sm'


capital_valido = mascara_capital


def clasificar_escenarios(datos):
    """Calcula cada escenario independientemente, sin modificar las entradas."""
    fuentes = {name: datos[name] if name in datos else pd.Series(np.nan,index=datos.index) for name in (C,K1,K13,K2)}
    nums = {name: pd.to_numeric(fuentes[name], errors='coerce') for name in fuentes}
    validos = {name: capital_valido(fuentes[name]) for name in nums}
    c = nums[C]
    salida = pd.DataFrame(index=datos.index)
    for nombre, campo in [('1',K1),('13',K13),('2',K2)]:
        valid = validos[C] & validos[campo]
        salida['evaluables_'+nombre] = valid
        salida['seleccion_'+nombre] = valid & (c < nums[campo])
        salida['brecha_'+nombre] = (c-nums[campo]).where(valid)
    seleccionado = salida['seleccion_2']
    salida['grupo'] = np.select([
        ~salida['evaluables_2'],
        ~seleccionado,
        seleccionado & ~validos[K1],
        seleccionado & validos[K1] & (c < nums[K1]),
    ], ['no evaluable','fuera','seleccionado sin grupo','A'], default='B')
    comparable = validos[K1] & validos[K13] & validos[K2]
    salida['orden_comparable'] = comparable
    salida['orden_inconsistente'] = comparable & ((nums[K1] > nums[K13]) | (nums[K13] > nums[K2]))
    return salida
