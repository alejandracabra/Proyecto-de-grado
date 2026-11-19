# Pensión mutualizada: selección y preparación actuarial

El flujo institucional usa exclusivamente el archivo local `xd.xlsx`, sin modificarlo ni exportar microdatos. El universo confirmado por la institución es de 95.011 afiliados en retiro programado, con corte al 30 de septiembre de 2026; una fila por afiliado y sin duplicados. La conciliación utiliza el número de filas y esa confirmación, sin consultar la primera columna ni las cédulas. Las magnitudes monetarias están en pesos colombianos.

## Ejecución

Con Python y las dependencias ya disponibles:

```text
python scripts/escenario_2.py
python -m pytest -q tests
```

La primera orden lee el Excel autorizado en la raíz y crea una nueva carpeta local `reports/generated/etapa_2_FECHA_HORA`. Incluye informes ejecutivo y técnico, diagnóstico de preparación, metodología matemática, diccionario, tablas agregadas y gráficos. El resultado es preliminar y las reglas de supresión de celdas pequeñas son provisionales, pendientes de revisión institucional. Los resultados históricos se conservan como antecedentes; no se actualizan ni son la metodología vigente. Los fixtures artificiales solo se usan en pruebas.

`src/actuarial/ingesta_institucional.py` contiene la lista blanca de variables y descarta las demás durante el análisis. `src/actuarial/seleccion.py` centraliza la selección; `src/actuarial/diagnostico.py` genera controles de cobertura. La primera columna y `cc` no forman parte de la lista blanca.

## Selección y preparación

El capital disponible es `Capital +Bono`. La selección principal es C < K(2), independientemente de K(1) y K(1,3). Se compara cada escenario solo con sus propios campos válidos. Para los seleccionados con K(1) válido, A es C < K(1) y B es K(1) ≤ C < K(2); sin K(1) válido se conserva la selección K(2) y no se asigna A/B. K(1,3) es referencia intermedia. El orden entre capitales se controla por separado. Los datos negativos, no finitos y faltantes no se imputan; el cero se admite en la comparación.

`sexo1` corresponde al titular y `sexo2` y `sexo3` a beneficiarios registrados; no demuestran derecho de sobrevivencia. `capital_necesario_def` es el capital requerido para la mesada actual. La existencia de información básica no demuestra que el afiliado pueda valorarse efectivamente.

## Valoración individual

`src/actuarial/valoracion.py` implementa una suma descontada por estados conjuntos explícitos, con obligaciones de titular y sobrevivientes separadas y gastos aparte. No genera tablas de mortalidad ni asigna derechos. Requiere parámetros, reglas de sobrevivencia, calendario y probabilidades conjuntas suministrados y confirmados; sin ellos bloquea el cálculo. El motor valida rangos y que cada distribución sume uno, pero no verifica la coherencia actuarial entre periodos. La prestación preliminar propuesta es de 1 SMMLV y puede requerir prestaciones de sobrevivientes. El horizonte, cola residual, edades y derechos de beneficiarios, tasa, reajustes, gastos y reglas faltantes deben definirse con Protección.

Las brechas C − K son diferencias individuales, no un déficit actuarial de la bolsa. El proyecto no ha demostrado viabilidad ni ahorro. La simulación colectiva y la proyección financiera siguen pendientes.

## Confidencialidad y antecedentes

El Excel `xd.xlsx` está rastreado en Git y ya existe en GitHub; contiene una columna `cc` y puede contener otros datos identificables. `.gitignore` no elimina archivos previamente rastreados ni sus versiones históricas. Revisar los accesos y el tratamiento de información con el responsable institucional; no se ha modificado el historial ni la visibilidad del repositorio. No hacer commit, push ni merge como parte de esta ejecución.

Los scripts e informes históricos del escenario 1,3 conservan supuestos anteriores y no integran el flujo vigente. La supresión de menos de 10 observaciones es una medida provisional, no una política aprobada ni una garantía de anonimización.
