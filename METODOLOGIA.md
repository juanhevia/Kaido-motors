# Modelo y decisiones de A013

## Fuente y alcance

Caso de Jacinto Velasco y Javier Goikoetxea, Universidad Alfonso X el Sabio.
Fuente: https://github.com/UAX-VCMT-26-27/sim-kaido-motors
Revisión de origen: `3663244f1604ee46b3a8789986fe3ea9030af107`.
Se preservan sin cambios los siete CSV y el enunciado de `docs/`.
Los hashes SHA-256 de los datos están en `resultados/ejecucion.json`.
No se emplean datos reales de 2026: A013 es un año ficticio del caso.

## 1. Demanda observada y demanda subyacente

Se resta `u_automatriculacion` de retail. No se resta `u_venta_especial`: puede ser demanda real y solaparse con otros indicadores.
Se agrupa por segmento y canal. No se unen códigos al detalle de ventas porque los CSV ya están agregados. `codigos.csv` permite verificar la gama y conservar el código literal NA.

La falta de coches no está observada directamente. Se marca un mes cuando el stock final es inferior al 20% de la venta mensual media de los doce meses anteriores. Se compara la venta a clientes con el mercado de ese mes por la cuota neta de los doce meses anteriores. Solo se imputa el exceso positivo, con un máximo del 20% de las ventas observadas. Es una aproximación conservadora de ventas censuradas, no prueba de una rotura. No se usa información posterior al mes para esa imputación. Antes de A009 no hay stock y no se imputan faltas.

Se neutralizan los sucesos dividiendo clientes más imputación entre el factor multiplicativo de sucesos que estima el modelo de mercado. Incluye ayudas, adelantos, caída posterior e IVA. El resultado representa un contrafactual sin esos sucesos y supone que Kaido responde como su mercado por canal. No permite identificar individualmente qué cliente adelantó su compra. El importe denominado `adelanto_estimado` en el CSV es el **efecto neto de todos los sucesos**, puede ser negativo por la caída posterior y no debe interpretarse íntegramente como ventas robadas a A013.

La comparación A011/A012 ajustada se estima retrospectivamente con datos hasta A012. La validación prospectiva se prepara con datos solo hasta A011. El crecimiento ajustado es una estimación sensible al método. Las matriculaciones observadas crecen 8,5%, las ventas sin automatriculaciones 6,0% y el contrafactual estimado 2,7%.

## 2. Modelo mensual por segmento y canal

Se ajustan 21 regresiones ridge de `log(1 + mercado)` con:

- Tendencia temporal y once indicadores de mes.
- Particulares: paro, confianza y coste del crédito.
- Empresas/renting: paro, PIB y actividad.
- Alquiladores: paro y viajeros.
- Días laborables, Semana Santa y cuatro indicadores de sucesos.

Se imponen signos plausibles: paro y crédito no aumentan demanda; confianza, actividad, PIB, viajeros, días laborables, ayudas y adelanto no la reducen; la caída posterior no la aumenta. Son restricciones de modelización, no elasticidades causales demostradas. La regularización y los signos reducen problemas de colinealidad. Los coeficientes completos quedan exportados.

El peso temporal es `exp((t-corte)/60)`. El nivel se ancla al cociente de mercado observado/ajustado de los últimos doce meses, evitando usar diciembre aisladamente. Se elige alpha en {1,10,30} mediante dos cortes internos (A009/A010 y A010/A011). Es una selección **condicional a macro observada** de esos años y no garantiza rendimiento ex ante.

La cuota neta de Kaido se estima con los últimos doce meses activos. Se amortigua al 50% el cambio logarítmico interanual y se limita a +/-20% anual. Con menos de 24 meses activos no se extrapola esa tendencia. La demanda es mercado por cuota neta, con un límite prudente de cuota del 95%.

El producto entra por la cuota: supuesto de lanzamiento en abril, incremento del 8% multiplicado por la fracción de códigos nuevos en central, 16% en optimista y retraso de tres meses para CSUV en pesimista. No hay fecha ni historial de los siete códigos nuevos. Este incremento es un supuesto, no una estimación causal de `renovacion_gama`. El indicador histórico se conserva para extensiones. CSUV usa sus cinco meses activos, con error relativo supuesto del 45% y sin extrapolar tendencia. Su crecimiento anual incluye doce meses frente a cinco de A012.

## 3. Validación sin fuga temporal

El ajuste de mercado y cuota que predice A012 usa datos hasta A011. La gama y los códigos nuevos A013 no se usan en esa validación. Se publican dos pruebas:

- **Ex ante**: macro congelada al cierre de A011, actividad y turismo con patrón del último año y calendario A012 conocido. Sin conocer los sucesos futuros. Es la prueba principal.
- **Condicional**: macro y sucesos A012 observados. Aísla el ajuste del modelo, pero no representa una previsión disponible al cierre de A011.

Referencia: repetir cada mes del año anterior sin automatriculaciones. WAPE = suma de errores absolutos / suma de ventas reales. Se exportan también sesgo y errores mensuales. El WAPE agregado ex ante es 28,3% frente a 31,1% de referencia. En MD el 95,2% de error revela una ruptura que el modelo no captó. En CSUV se predice cero porque aún no existe historia a cierre de A011: su WAPE del 100% es una limitación de arranque, no una validación del lanzamiento. No se ha elegido otro modelo después de mirar A012 para mejorar artificialmente esta prueba.

## 4. Escenarios y calibración

Todos los cambios están en `config.json`. El central conserva la última observación económica A012 y los patrones mensuales de actividad y turismo A012. Se usa el calendario suministrado.

Pesimista: paro +2 pp, confianza -5 puntos, crédito +0,5 pp, PIB -1 pp, actividad -3%, viajeros -5 pp, caída posadelanto enero-junio. Multiplicador adicional de demanda 0,97 por combustible. Lanzamiento CSUV en julio y producción CSUV de mayo nula, por tanto llegada de agosto nula. CO2 según `segmentos.csv` y arancel adicional del 5% del coste estimado del vehículo.

Optimista: paro -1 pp, confianza +5 puntos, crédito -0,5 pp, PIB +0,5 pp, actividad +2%, viajeros +5 pp. Caída solo en enero, ayuda desde abril y multiplicador de combustible 1,02. Coste del vehículo -1% por fortaleza del euro, registrado como arancel negativo para conciliar el margen. No se aplica descuento de arancel legal real ni se supone capacidad finita en central u optimista.

Las duraciones y el paro proceden de la Tabla 4. El modelo calibra la respuesta a sucesos con episodios históricos de ayudas y adelantos, incluyendo un mes de adelanto en A011 y dos en A012. Como referencia de magnitud, entre A004 y A005 el paro medio pasa de 21,39% a 24,79% (+3,40 pp), la confianza de 71,11 a 49,82 (-21,29 puntos), el crédito de 8,04% a 8,61% (+0,57 pp), y la variación de viajeros de +3,80% a -2,57% (-6,37 pp). El estrés propuesto es menor en paro/confianza y similar en crédito/turismo. En la recuperación A010-A011 el paro baja de 17,22% a 15,26% (-1,96 pp), por lo que -1 pp en optimista es de menor tamaño. Son comparaciones de magnitud y no episodios causalmente equivalentes a A013. Los CSV no incluyen combustible, divisas o arancel: sus multiplicadores y costes son supuestos explícitos. No se atribuyen probabilidades a los escenarios ni se los interpreta como percentiles.

## 5. Simulación y plazo

Se simulan 1.000 años por escenario, semilla 20261008. El error es lognormal, centrado para conservar la media. El error relativo se estima con RMSE relativo A012 ex ante (límites 10%-60%). Se mantiene la correlación temporal AR(1) estimada con solo 12 errores, limitada a [0,0,65]. La correlación de innovaciones entre segmentos es un supuesto común de 0,35. CSUV tiene 45% de error y rho 0,30. Los intervalos P5-P95 son dispersión condicional simulada, no intervalos que integren toda la incertidumbre de parámetros, gama o escenarios.

El stock inicial son los 2.877 coches reales a cierre de A012. Los tramos de antigüedad se reparten uniformemente entre cohortes de 15/45/75 y 105/135/165 días. El tramo >180 se representa a 195 días. Hay venta FIFO, entradas a principio de mes y venta a mitad de mes. Cada mes dura 30 días, convención coherente con el plazo y los tramos de 90/180.

El tránsito de enero/febrero se estima con la facturación de los últimos seis meses, desestacionalizada con el mercado neutral de A012 y reestacionalizada para enero/febrero. Suma 4.313 coches. No es información de barcos reales. La sensibilidad de +/-25% está incluida.

Al cierre de diciembre A012 se fija marzo con la ecuación 7.4. Al cierre de enero se decide abril, y así sucesivamente. Por eso `plan_fabricacion_A013.csv` etiqueta **mes de pedido/fabricación** y `plan_llegadas_A013.csv` etiqueta **mes de llegada**. La producción de A013 no coincide con ventas ni llegadas de A013. El trimestre final llega a A014, queda registrado como pipeline y no se cuenta como stock de la red. A014-Q1 repite calendario y patrón central A013-Q1 como continuación técnica, sin pretender conocer A014. Esto afecta al plan de octubre-diciembre.

Los tres escenarios comparten la misma previsión inicial, stock, tránsito y llegada de marzo. Cada cierre actualiza una razón demanda observada/previsión, con ganancia 0,35, y cambia solo la llegada de t+3. Se supone que la red registra también las solicitudes no servidas. La política nunca observa el nombre del escenario futuro. Solo la parada impuesta cambia la disponibilidad física. La fabricación media simulada puede diferir del plan inicial sin error.

Stock de seguridad = z * sigma * sqrt(3 + 4*rho + 2*rho^2). Se deriva de tres meses de errores correlacionados. B no tiene colchón especulativo por su baja contribución; C usa z=1,28, los demás 1,65. Es una política propuesta y sometida a sensibilidad +/-25%, no una optimización global. No hay restricciones de capacidad, mínimos de lote ni límites de puerto proporcionados.

## 6. Costes, transfers y decisión comercial

Stock de marca: 2 euros por coche y día hasta 180 días desde factura. Se cobran 15 días a unidades vendidas a mitad de mes y 30 días a las restantes, respetando el tope. Los intereses de la red se calculan aparte con los importes diarios de los CSV y no se restan del margen de la marca.

VM según edad de venta. Falta VM CSUV >180: se imputa VM 91-180 más la mediana de las diferencias entre tramos de los otros segmentos. Se respeta el VM por edad observado de B aunque no sea creciente. No se resta adicionalmente el VM tarifa ni el margen concesionario, ya incorporados en el beneficio bruto de la marca.

Transfers: disponibilidad instantánea supuesta, máximo del 10% de demanda mensual; cada uno cuesta 20% del beneficio bruto y VM del tramo joven. Solo se usa si la contribución después de CO2/arancel sigue positiva. Los restantes pedidos se pierden sin arrastre al siguiente mes. Unidades transferidas forman parte de ventas, nunca de fabricación propia. Los costes de oportunidad de ventas perdidas se muestran aparte y se acotan a cero en segmentos deficitarios.

CVP neto = ventas * beneficio bruto - VM - stock - transfer - CO2 - arancel. El coste implícito del coche es PFF - margen completo concesionario - beneficio bruto. Se informa por separado y no se resta dos veces. El resultado es contribución, no beneficio contable: no incluye costes fijos, impuestos de sociedades ni flujo de caja de inventarios.

La Tabla 5 evalúa una política que revisa por demanda. **No activa un veto adicional de producción por pérdidas.** En pesimista, la recomendación comercial es suspender nuevos pedidos de B, C, SSUV y S si se confirman CO2/arancel, manteniendo los compromisos a tres meses. Ese veto es una recomendación adicional sin cuantificar en la tabla, no una mejora que ya esté contada. MSUV y CSUV concentran la contribución y son la prioridad, mientras MD exige seguimiento por su baja precisión.

Un error de 150 MSUV de más durante un mes cuesta 9.000 euros de stock, antes de VM adicional. Si faltan 150, el transfer supone 233.460 euros y la pérdida a CVP real histórico 857.100 euros, según sección 7.5. El límite de transfers puede impedir recuperar todas las ventas. Un coche B joven solo deja 125 euros antes de stock; tres meses de stock (180 euros) superan ese margen. Esta asimetría justifica colchones distintos y ningún empuje indiscriminado del segmento B.

## 7. Auditoría y límites

`python -m unittest -v` verifica el balance físico, plazo de tres meses, FIFO/tope de coste, transfer y ausencia de doble descuento de pérdidas, consistencia de datos y suma de Tabla 5. Las réplicas usan la misma semilla en los escenarios para reducir ruido en comparaciones. Los cinco ensayos de sensibilidad conservan la misma semilla.

El histórico no cuadra exactamente: los mayores residuos stock - stock anterior - wholesale + retail son +51 y -50 coches en SSUV, A009-junio/julio, y el saldo acumulado de todos los residuos es -2. Se conserva el original y se registra en `auditoria_stock.csv`, sin forzar ajustes. La simulación sí satisface el balance físico por réplica y segmento con tolerancia 1e-6.

Los intervalos son amplios y el modelo requiere revisión mensual. Se proponen alertas si el error supera el 15% dos meses seguidos o si el stock >90 días supera el 20%. Estos umbrales de gestión son propuestos, no estimados. La suma de simulaciones no constituye garantía de servicio. Para operar el plan se debe sustituir tránsito estimado por manifiestos de barcos y confirmar los calendarios de lanzamiento, costes normativos y transfers.
