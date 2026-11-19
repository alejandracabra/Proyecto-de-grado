# Metodología de valoración individual — pendiente de parametrización

La prestación preliminar es 1 SMMLV y el criterio de selección es C < K(2).
Para cada periodo t y estado conjunto s (titular y beneficiarios), sea p_i,s(t)
su probabilidad conjunta, obtenida de tablas y supuestos institucionales, y sean
b_T,i,s(t) y b_S,i,s(t) los pagos en COP, tras aplicar calendario de mesadas,
reajustes, derechos, sustitución y concurrencia. Para cada t, Σ_s p_i,s(t)=1.
No se presume independencia entre vidas ni se asignan mesadas completas a cada beneficiario.

VPA_T,i = Σ_t (1+j)^(-t) Σ_s p_i,s(t) b_T,i,s(t)

VPA_S,i = Σ_t (1+j)^(-t) Σ_s p_i,s(t) b_S,i,s(t)

VPA_obligaciones,i = VPA_T,i + VPA_S,i. Los gastos esperados se descuentan
por separado; el total con gastos suma ese valor. El motor recibe distribuciones
conjuntas exhaustivas y pagos explícitos para cada periodo; supone pagos al final
del periodo y una tasa efectiva periódica constante suministrada. La unidad de
periodo, calendario, mesadas adicionales, reajustes y horizonte deben definirse
antes de construir sus entradas. Las probabilidades deben ser coherentes entre
periodos y con las tablas y reglas aprobadas; el motor valida rango y suma por
periodo, no demuestra por sí mismo esa coherencia actuarial.

Faltan tablas de mortalidad y su fuente, tasa y convención de descuento,
calendario y fecha de valoración confirmados, trayectoria SMMLV y reajustes,
horizonte y cola residual, edades o fechas válidas de beneficiarios, derechos,
porcentajes, reglas de concurrencia y extinción, dependencia entre vidas y gastos.
Sin ellos se bloquea la valoración efectiva. Los campos fn1, fn2 y fn3 se
contabilizan solo como presencia y no se interpretan como fechas de nacimiento.
El motor implementa la agregación matemática, no genera probabilidades de
supervivencia ni decide derechos. Requiere revisión actuarial y jurídica.
