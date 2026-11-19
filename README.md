# Implementación actuarial preliminar

## Actualización del escenario institucional K(2)

El análisis vigente se ejecuta con `python scripts/escenario_2.py`. El script lee localmente `xd.xlsx`, excluye la cédula y genera una carpeta nueva de resultados agregados en `reports/generated/`. El Excel actualizado y los microdatos no deben incorporarse en nuevas confirmaciones. El número sin encabezado de la columna A se usa solo en memoria para contar faltantes y repeticiones; no se exporta ni prueba por sí solo la unicidad de personas.

Las magnitudes monetarias están en pesos colombianos. `sexo1` corresponde al titular; `sexo2` y `sexo3` corresponden a beneficiarios. `capital_necesario_def` es el capital requerido en la cuenta de ahorro individual para financiar la mesada actual, según confirmación del usuario. `Capital +Bono` se usa provisionalmente como capital disponible, pendiente de validar la disponibilidad del bono y el doble conteo.

La selección preliminar utiliza C < K(2); K(1) y K(1,3) sirven como referencias intermedias. La prestación de la modalidad propuesta sería preliminarmente de 1 SMMLV. Los resultados no acreditan viabilidad ni ahorro; la bolsa requiere valoración y proyección actuarial y financiera.

La auditoría de datos reales y los ejemplos sintéticos son procesos separados. La auditoría no constituye una valoración actuarial ni una decisión de elegibilidad.

**Universo reportado confirmado institucionalmente:** 95.011 afiliados, todos pensionados en retiro programado, con corte al 30 de septiembre de 2026. Cada fila corresponde a un afiliado y no existen registros duplicados. Se trata del universo reportado, no de una muestra.

## Ejecución

Con Python 3.10 o posterior: `python -m pip install -e ".[test]"`, `python -m pytest` y `python -m actuarial.reporte`. El reporte presenta exclusivamente un ejemplo sintético. La ingesta proporcionada acepta registros sintéticos en memoria, no archivos corporativos. No utilizarla con información real; antes se requiere un flujo institucional autorizado y revisado. No registrar ni transmitir microdatos. Los conteos sintéticos pequeños son solo de demostración y no constituyen una regla de divulgación para datos reales.

`config.py` documenta variables lógicas; el mapeo institucional está vacío. Nunca mapear identificadores personales, incluida la cédula. El ID técnico se genera de forma secuencial por ejecución. Las coincidencias de variables analíticas no prueban duplicidad de afiliados. La protección de campos por nombre no garantiza anonimización; no usar como filtro de seguridad para bases reales.

Con autorización institucional, `python scripts/metadatos_locales.py RUTA --autorizado` informa únicamente extensión y tamaño; no abre ni inspecciona el contenido. Estos metadatos deben considerarse compartibles solo si la institución lo permite. No identifica columnas ni hojas: cualquier inspección más detallada requiere diseñar y autorizar previamente su salida y sus controles de divulgación.

La selección futura usa C < K(2); A si C < K(1), B si K(1) ≤ C < K(2). Incluir el bono es una decisión explícita. K(2) puede venir de una columna o función autorizada; se deshabilitó la aproximación lineal. La selección definitiva exige confirmación explícita de validación. Esta marca es una salvaguarda operativa, no una prueba de autorización. No se filtran tipos de prestación.

## Pendientes con Protección

Confirmar disponibilidad del saldo y bono sin doble conteo; parámetros del cálculo institucional K(2); beneficiarios, derechos, mesadas y reglas por prestación; tablas de mortalidad, tasas, salarios, gastos, reservas y márgenes; reglas de divulgación y celdas pequeñas; viabilidad jurídica, FGPM y comparación con aseguradora. No se presupone viabilidad legal ni ahorro por mutualización. El sexo del titular, los pesos colombianos y el significado de `capital_necesario_def` fueron confirmados por el usuario.

La siguiente fase debe construir valoración de titular y sobrevivientes, proyección mensual y obligación residual más allá del horizonte; después escenarios estocásticos y comparación de derechos equivalentes. La identidad gráfica utiliza Sura Sans y los colores indicados por el usuario; no se ha comprobado un manual oficial de marca. Sura Sans debe estar instalada localmente para visualizarla; de lo contrario se usa una tipografía alternativa.

## Auditoría local exploratoria del Excel autorizado

La descripción de esta sección corresponde a la auditoría anterior a la incorporación de K(2); para el análisis vigente, véase la actualización al inicio de este documento.

`python scripts/inspeccionar_estructura.py xd.xlsx --autorizado` inspecciona nombres de la primera fila; no muestra registros. Para el archivo de corte confirmado, ejecutar `python scripts/auditoria_local.py xd.xlsx --autorizado --confirmar-unidad --confirmar-sin-duplicados --confirmar-retiro-programado`. Se genera un HTML agregado nuevo en `reports/generated/`, ignorado por Git, sin alterar el Excel. Requiere una hoja XLSX en `sheet1.xml` y encabezados en la primera fila. El script usa una lista explícita de campos, excluye `cc` y demás campos no listados y no imprime filas. Comprueba que existan 95.011 filas y que cada una tenga al menos un campo analizado; también exige las tres confirmaciones institucionales. Estos controles no demuestran unicidad de afiliados ni modalidad, ni validan por sí solos la fecha. Para una carga futura se requiere una nueva confirmación institucional y actualizar el corte y el tamaño esperado de manera explícita; no reutilizar las confirmaciones de este corte. No se usa la cédula para verificar duplicados. La ausencia se refiere exclusivamente a los campos examinados. Tipos XML y conteos de valores numéricos no equivalen a una validación semántica. Fórmulas sin valor almacenado se consideran ausentes. Las categorías pequeñas se suprimen de forma conservadora, pero el umbral predeterminado de 10 no representa una política institucional aprobada; no compartir el informe sin revisión institucional.

El archivo examinado tiene una hoja `Sheet1`. Se observan, entre otros, `Riesgo`, `Riesgo 3`, `mesada`, `nmesadas`, `capital`, `Capital +Bono`, `Edad`, `sexo1`, campos de beneficiarios, `capital_necesario_sm`, `capital_necesario_1.3_sm`, `capital_necesario_def`, `Descapitalización`, `Desfinanciación` y `Expectativa de vida`. Son nombres observados, no definiciones verificadas. El cálculo exploratorio usa `Capital +Bono` como hipótesis para comparar pares completos; no confirma que el bono sea computable ni que esté libre de doble conteo. Los cuartiles de K(1,3)/K(1) no prueban proporcionalidad ni permiten extrapolar K(2). No se calcula población elegible ni grupo B. El reporte no incluye gráficos ni una validación exhaustiva de beneficiarios. La desfinanciación se refiere a insuficiencia frente a la mesada actual; la descapitalización, frente a 1 SMMLV: verificar las definiciones institucionales de las columnas antes de interpretarlas.

## Repositorio y confidencialidad

Por autorización expresa, los resultados generados existentes en `reports/generated/` se incorporaron al repositorio. Aunque el directorio está incluido en `.gitignore`, ese archivo no protege resultados ya rastreados; futuras modificaciones a estos archivos pueden aparecer en Git.

## Escenario provisional de selección con K(1,3)

## Avance integral

`python scripts/preparar_avance.py` vuelve a procesar localmente la base autorizada y crea una carpeta nueva con informes, presentación, guion y agregados. Se contrastan los recuentos con la última ejecución anterior disponible. Las barras de brechas de ejecuciones previas usaban magnitudes absolutas y no mostraban correctamente el signo: se conservan como antecedente y deben sustituirse por las gráficas nuevas con eje cero. El proceso no convierte moneda ni agrega por segunda vez el bono; la homogeneidad de unidades, el significado de los campos y la disponibilidad del bono requieren validación institucional. La discrepancia entre la bandera institucional de descapitalización y la comparación C < K(1) requiere investigación.

Con las confirmaciones aplicables al corte, ejecutar `python scripts/escenario_13.py xd.xlsx --autorizado --confirmar-corte`. Cada ejecución genera una carpeta ignorada con informes HTML ejecutivo y técnico, tablas agregadas CSV y gráficos SVG, sin exportar registros. La lista de campos excluye la cédula; el sexo del titular no se presenta hasta validar su variable. El umbral de supresión predeterminado es 10, pendiente de aprobación institucional; los informes deben revisarse antes de compartirlos.

Se clasifica A si C < K(1), B si K(1) ≤ C < K(1,3), fuera si C ≥ K(1,3), y no evaluable si falta algún valor, no es numérico, es no finito, negativo o K(1,3) < K(1). C se aproxima mediante `Capital +Bono`, sujeto a validar bono, unidades y doble conteo. Las brechas son C − K por afiliado, no una valoración de la bolsa. Los percentiles se calculan por interpolación lineal. La codificación de riesgo, beneficiarios y desfinanciación/descapitalización requiere validación. K(1,3) es un umbral provisional, no el criterio definitivo: K(2) se desarrollará con metodología actuarial institucional y los resultados pueden cambiar. No se calcula ni extrapola K(2).

`.gitignore` no retira `xd.xlsx` del índice ni de la historia. Antes de cualquier publicación o acceso al archivo, verificar con el responsable institucional si contiene información autorizada. Si requiere retiro, coordinar revocación de accesos y, con autorización explícita, evaluar eliminación del seguimiento y limpieza del historial (por ejemplo, `git filter-repo`), copias y clones, y el procedimiento de GitHub para datos sensibles. Reescribir historia es destructivo y no se ha realizado. No se ha hecho push.
