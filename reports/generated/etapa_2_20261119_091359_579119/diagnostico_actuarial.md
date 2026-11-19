# Diagnóstico de preparación actuarial

La selección por capital, la cobertura de campos y la valoración efectiva son
conceptos distintos. Los campos mínimos de titular cuentan edad entre 0 y 120
(filtro técnico provisional), sexo F/M, número entero positivo de mesadas,
mesada y capitales disponibles válidos. El conteo es un control de cobertura,
no garantiza que los datos sean adecuados actuarialmente ni acredita derechos.
La valoración efectiva está bloqueada para todos mientras falten parámetros y
reglas; el cero no indica que ninguno pueda valorarse una vez se suministren.

Las variables sexo2/sexo3, tipo2/tipo3 y estado2/estado3 se describen como
registros disponibles, sin asumir parentesco, edad o derecho a sobrevivencia.
La interpretación y completitud de los campos fn requiere confirmación; no se
calculan edades de beneficiarios. Solicitar a Protección el diccionario y fecha de
corte de beneficiarios, edades/fechas válidas, relaciones, condiciones y derechos,
reglas de sustitución y concurrencia y todos los parámetros de la metodología.
Las tablas cobertura_actuarial.csv y categorias.csv presentan cobertura por
universo, seleccionados, A y B; tablas pequeñas se suprimen preventivamente.

Cada fila corresponde a un afiliado, sin duplicados, según confirmación institucional; se cuentan filas y no se usa la primera columna ni la cédula. COP. Capital +Bono es el capital disponible confirmado. K(1,3) no condiciona selección K(2); el orden entre capitales se controla por separado. Cero es válido; faltantes, no numéricos, negativos y no finitos son no evaluables para cada par correspondiente. Una selección sin K(1) válido permanece seleccionada pero sin grupo A/B. Sexo, tipo y estado registrados no demuestran derechos de sobrevivencia. Las brechas individuales y su suma no son déficit de una bolsa. No se demuestra viabilidad ni ahorro.