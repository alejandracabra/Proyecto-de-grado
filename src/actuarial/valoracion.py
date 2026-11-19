"""Motor por estados conjuntos aportados por actuaría; sin supuestos predeterminados."""
from dataclasses import dataclass
from datetime import date
from math import isfinite, isclose
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Beneficiario:
    edad: float | None
    sexo: str | None
    derecho_confirmado: bool | None


@dataclass(frozen=True)
class Parametros:
    fecha_valoracion: date | None
    tasa_efectiva_periodica: float | None
    horizonte_periodos: int | None
    fuente_mortalidad: str | None
    reglas_sobrevivencia: str | None
    gastos_por_periodo: Sequence[float] | None
    supuestos_confirmados: bool = False
    edad_titular: float | None = None
    sexo_titular: str | None = None
    mesada_referencia: float | None = None
    mesadas_anuales: int | None = None
    regla_reajuste: str | None = None
    situacion_beneficiarios_confirmada: bool = False
    coherencia_supervivencia_confirmada: bool = False
    tratamiento_cola: str | None = None
    beneficiarios: tuple[Beneficiario, ...] | None = None

    def validar(self):
        if (not self.supuestos_confirmados or not isinstance(self.fecha_valoracion,date)
            or self.tasa_efectiva_periodica is None or not isfinite(self.tasa_efectiva_periodica)
            or self.tasa_efectiva_periodica <= -1 or not isinstance(self.horizonte_periodos,int)
            or isinstance(self.horizonte_periodos,bool) or self.horizonte_periodos <= 0
            or not self.fuente_mortalidad or not self.reglas_sobrevivencia
            or self.gastos_por_periodo is None or self.edad_titular is None
            or not isfinite(self.edad_titular) or not 0 <= self.edad_titular <= 120
            or self.sexo_titular not in ('F','M') or self.mesada_referencia is None
            or not isfinite(self.mesada_referencia) or self.mesada_referencia <= 0
            or not isinstance(self.mesadas_anuales,int) or isinstance(self.mesadas_anuales,bool)
            or self.mesadas_anuales <= 0 or not self.regla_reajuste
            or not self.situacion_beneficiarios_confirmada
            or not self.coherencia_supervivencia_confirmada or not self.tratamiento_cola
            or self.beneficiarios is None):
            raise ValueError('Valoración bloqueada: faltan parámetros o confirmaciones actuariales')
        if len(self.gastos_por_periodo)!=self.horizonte_periodos or any(not isfinite(x) or x<0 for x in self.gastos_por_periodo):
            raise ValueError('Gastos inválidos o incompletos')
        for b in self.beneficiarios:
            if not isinstance(b,Beneficiario) or not isinstance(b.derecho_confirmado,bool):
                raise ValueError('Derechos de beneficiarios no confirmados')
            if b.derecho_confirmado and (b.edad is None or not isfinite(b.edad)
                    or not 0 <= b.edad <= 120 or b.sexo not in ('F','M')):
                raise ValueError('Edad o sexo de beneficiario con derecho inválidos')


@dataclass(frozen=True)
class Estado:
    """Una probabilidad conjunta y pagos ya sujetos a derechos y concurrencia."""
    probabilidad: float
    pago_titular: float
    pago_sobrevivientes: float


def valorar(parametros: Parametros, estados: Sequence[Mapping[str, Estado]]):
    """Calcula VPA por pagos al final de cada periodo, incluidos todos los estados.

    La entrada debe contener distribución conjunta exhaustiva por periodo y pagos
    por estado, tras aplicar calendario, mesadas, reajustes y reglas confirmadas.
    No se supone independencia ni derecho de beneficiarios. Los gastos provistos
    son valores esperados por periodo; las obligaciones excluyen gastos.
    """
    parametros.validar()
    if len(estados)!=parametros.horizonte_periodos: raise ValueError('Horizonte incompleto')
    titular=sobrevivientes=gastos=0.0
    for t, distribucion in enumerate(estados,1):
        if not distribucion: raise ValueError('Faltan estados conjuntos')
        probs=[]
        for estado in distribucion.values():
            if not isinstance(estado,Estado): raise ValueError('Estado inválido')
            p=estado.probabilidad
            if not isfinite(p) or p<0 or p>1: raise ValueError('Probabilidad fuera de [0,1]')
            if any(not isfinite(x) or x<0 for x in (estado.pago_titular,estado.pago_sobrevivientes)):
                raise ValueError('Pago inválido')
            if estado.pago_sobrevivientes and not any(b.derecho_confirmado for b in parametros.beneficiarios):
                raise ValueError('Pago de sobrevivencia sin beneficiario con derecho confirmado')
            probs.append(p)
        if not isclose(sum(probs),1,rel_tol=0,abs_tol=1e-9): raise ValueError('La distribución conjunta no suma uno')
        v=(1+parametros.tasa_efectiva_periodica)**(-t)
        titular += v*sum(s.probabilidad*s.pago_titular for s in distribucion.values())
        sobrevivientes += v*sum(s.probabilidad*s.pago_sobrevivientes for s in distribucion.values())
        gastos += v*parametros.gastos_por_periodo[t-1]
    return {'titular':titular,'sobrevivientes':sobrevivientes,'obligaciones':titular+sobrevivientes,
            'gastos':gastos,'total_con_gastos':titular+sobrevivientes+gastos}
