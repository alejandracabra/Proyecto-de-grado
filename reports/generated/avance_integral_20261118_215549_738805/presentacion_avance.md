# Presentación de avance — pensión mutualizada

Universo reportado de 95,011 afiliados en retiro programado, corte 30 de septiembre de 2026; una fila por afiliado y sin duplicados según confirmación institucional. Datos reales agregados. El escenario K(1,3) es provisional y no representa elegibilidad definitiva ni viabilidad de la bolsa.

## 1. Propósito y pregunta

- **Contenido:** Evaluar una posible modalidad independiente de pensión mutualizada, sujeta a viabilidad legal y financiera.
- **Visual recomendado:** Contexto y alcance.
- **Mensaje principal:** La propuesta está en evaluación.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 2. Universo y fuente

- **Contenido:** Universo reportado de 95,011 afiliados en retiro programado, corte 30 de septiembre de 2026; una fila por afiliado y sin duplicados según confirmación institucional. Datos reales agregados. El escenario K(1,3) es provisional y no representa elegibilidad definitiva ni viabilidad de la bolsa.
- **Visual recomendado:** Ficha del universo y corte.
- **Mensaje principal:** Es un universo reportado, no una muestra.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 3. Criterio de selección

- **Contenido:** C < K(1,3) es provisional; A: C < K(1); B: K(1) ≤ C < K(1,3).
- **Visual recomendado:** segmentos.svg.
- **Mensaje principal:** K(1,3) no sustituye a K(2).
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 4. Composición del escenario

- **Contenido:** 84,884 afiliados (89.34%) tienen C inferior a K(1); 1,072 adicionales (1.13%) se encuentran entre K(1) y K(1,3). En conjunto son 85,956 (90.47%). Fuera del escenario hay 9,055 (9.53%); no evaluables: 0. Los cuatro segmentos suman 95,011.
- **Visual recomendado:** segmentos.svg.
- **Mensaje principal:** Conciliación completa y criterio exploratorio.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 5. Edad y riesgo

- **Contenido:** La mediana de edad es 65 años en A y 67 en B; la diferencia es descriptiva y no implica causalidad. En A, la categoría registrada GPM tiene 63,800 afiliados (75.16% del grupo); su definición institucional debe confirmarse.
- **Visual recomendado:** edades.svg y riesgo.svg.
- **Mensaje principal:** Las diferencias son descriptivas.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 6. Capitales y brechas

- **Contenido:** La mediana de C − K(1) en A es -453,527,103.21 y la mediana de C − K(1,3) en B es -16,526,974.47 unidades monetarias de origen. No representan déficit de la bolsa.
- **Visual recomendado:** capital_1.svg, capital_13.svg y brechas.svg.
- **Mensaje principal:** Una comparación de capitales no es déficit de la bolsa.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 7. Calidad y alertas

- **Contenido:** En A, 64,714 registros aparecen como 'No' en Descapitalizado pese a cumplir C < K(1): revisar definiciones, variables base y reglas institucionales antes de interpretar la discrepancia.
- **Visual recomendado:** Tabla de calidad del informe técnico.
- **Mensaje principal:** Validar clasificaciones, moneda y bono.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 8. De K(1,3) a K(2)

- **Contenido:** Calcular K(2) posteriormente con metodología institucional en Python; evaluar C < K(2). No extrapolar K(1).
- **Visual recomendado:** Diagrama de etapas.
- **Mensaje principal:** K(2) requiere metodología actuarial institucional.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 9. Valoración individual y sobrevivientes

- **Contenido:** Valorar 1 SMMLV, mesadas, reajustes, supervivencia del titular y beneficiarios, gastos y descuento durante todo el horizonte vitalicio; contrastar capitales institucionales y datos de beneficiarios.
- **Visual recomendado:** Esquema de flujos y supervivencia.
- **Mensaje principal:** Conservar derechos y valorar toda la vida.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 10. Bolsa y comparación económica

- **Contenido:** Proyectar capital inicial y aportes, rendimientos, prestaciones, gastos y activos; valorar obligaciones remanentes y respaldo, incluso después del horizonte explícito. La no heredabilidad del saldo requiere validación jurídica; conservar derechos de sobrevivientes. Comparar retiro programado, aseguradora y bolsa con prestaciones equivalentes; separar efectos de derechos, rentabilidad, gastos, mutualización y respaldo. La mutualización no implica ahorro automático.
- **Visual recomendado:** Flujo de activos y obligaciones.
- **Mensaje principal:** Comparar derechos equivalentes y recursos de respaldo.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.

## 11. Sensibilidades y próximos pasos

- **Contenido:** Evaluar mortalidad, rentabilidad, descuento, reajuste del SMMLV, gastos y número de mesadas, con parámetros autorizados y escenarios reproducibles. Confirmar variables, clasificaciones, capitales y supuestos con el equipo actuarial.
- **Visual recomendado:** Matriz de decisiones pendientes.
- **Mensaje principal:** No concluir viabilidad ni ahorro antes de modelar.
- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.
