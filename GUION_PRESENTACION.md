# Guion de exposición: diez minutos

10 diapositivas principales y 2 anexos de consulta. Duración total: 600 segundos.

## 1. Kaido Motors España (30 s)

La propuesta inicial es pedir 23.162 coches en A013. La incertidumbre obliga a revisar cada mes. El punto económico crítico es que CO2 y aranceles pueden convertir el crecimiento en pérdidas. Presento primero la demanda, después el plan físico y finalmente sus costes. El resultado financiero es contribución de marca, no beneficio contable.

## 2. El crecimiento observado sobrestima la demanda de fondo (60 s)

Las matriculaciones pasan de 21.362 a 23.175: crecen 8,5%. Sin automatriculaciones, el crecimiento es 6,0%. Al neutralizar los sucesos y añadir 77 ventas censuradas estimadas, queda 2,7%. Esta tercera comparación es un contrafactual del modelo. Las ayudas y la caída posterior también se neutralizan, por lo que no todo el ajuste es adelanto de compras. El nuevo CSUV añade cinco meses de gama en A012.

## 3. El modelo separa mercado y cuota de Kaido (65 s)

Se ajusta mercado mensual para siete segmentos y tres canales. Usamos tendencia, estacionalidad, calendario y dos o tres variables económicas relevantes para cada canal, más sucesos. La demanda de Kaido es mercado por cuota neta. La cuota usa doce meses y una tendencia amortiguada. Los lanzamientos de abril son supuestos porque no hay fechas de producto. Los signos restringidos evitan interpretar correlaciones históricas absurdas como efectos económicos. Todas las variables futuras se publican en el ZIP.

## 4. La prueba A012 mejora la referencia, pero falla en MD (65 s)

El modelo se entrenó hasta A011. La prueba principal no conoce la macro ni los sucesos de A012. WAPE ponderado: 28,3% frente al 31,1% de repetir el año anterior. No mejora todos los segmentos. MD tiene un error del 95,2% y necesita revisión con pedidos reales. En CSUV el modelo preveía cero por falta de historial antes del lanzamiento. El 100% de error no debe ocultarse ni llamarse validación del nuevo producto. Hay una prueba condicional separada usando la macro observada.

## 5. Tres escenarios con un mismo plan inicial (55 s)

El central conserva la situación económica de final de A012. El optimista baja paro y crédito, incluye ayudas y producto más fuerte. El pesimista alarga la caída, añade CO2 y arancel, retrasa el lanzamiento CSUV y elimina su producción de mayo. El combustible no está en los datos: se representa mediante un multiplicador supuesto. No asignamos probabilidades a estas historias. Dentro de cada una se simulan mil años con errores correlacionados.

## 6. 23.162 coches en el plan inicial de fabricación (70 s)

La tabla muestra pedidos a fábrica de cada mes, no llegadas ni matriculaciones. Enero llega en abril. El tránsito estimado de enero y febrero suma 4.313 coches. Marzo se fija a cierre de A012. Hay cero pedidos iniciales en compacto y SUV compacto para absorber existencias. Octubre a diciembre abastecen A014 con una continuación técnica de demanda. El plan inicial es la trayectoria sin ruido: la media de fabricación de las simulaciones cambia con las revisiones.

## 7. Los colchones reflejan el coste de quedarse corto (65 s)

Con tres meses de espera no basta mirar el stock físico de hoy. Se suma el tránsito y se resta la demanda hasta el último mes fijo. El pedido cubre el mes modificable y el colchón. Ajustamos el colchón por correlación temporal del error. B no tiene colchón porque 125 euros de contribución joven no cubren tres meses de stock. Un exceso de 150 SUV medios durante un mes cuesta 9.000 euros, frente a 233.460 de transfer o 857.100 de oportunidad perdida usando el CVP histórico.

## 8. El escenario pesimista deja una contribución negativa (70 s)

La Tabla 5 usa el mismo arranque y una regla común de revisión según demanda. El CVP neto central es 79,88 millones, el optimista 102,81 y el pesimista menos 5,88. El pesimista añade 57,83 millones de CO2 y 13,32 de arancel. No hay transfers rentables en ese escenario. El optimista tiene más ventas perdidas por el desfase de tres meses. Las pérdidas de venta son coste de oportunidad separado, no otro descuento al CVP. El stock medio considera entradas al inicio y venta a mitad de mes.

## 9. MSUV y CSUV concentran la contribución (60 s)

SUV medio y SUV compacto son la prioridad comercial. El compacto tiene exceso inicial y margen menor. El pequeño se limita a demanda confirmada y sin stock especulativo. Con el cargo de CO2 y arancel, B, C, SSUV y S pasan a pérdida. Recomiendo suspender nuevos pedidos deficitarios cuando se confirme ese cambio de costes, siempre respetando el tránsito. Esta medida de crisis es adicional y su mejora no está incluida en los resultados de la Tabla 5. El objetivo es evitar empujar volumen que destruya margen.

## 10. La aprobación requiere revisión mensual (60 s)

Solicito aprobar el plan inicial sujeto a revisión cada mes. Confirmar primero el tránsito real y las fechas de producto, porque son supuestos determinantes. Registrar también demanda no servida para que las roturas no hagan caer la previsión artificialmente. Recalcular cuando el error supere 15% durante dos meses o cuando más del 20% del stock tenga más de 90 días. Vigilar CO2 y arancel para activar el veto comercial. El intervalo central refleja ruido del modelo y no incluye toda la incertidumbre de parámetros. El ZIP contiene datos, código, resultados, pruebas y guía de reproducción.