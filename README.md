# Kaido Motors España: plan A013

Modelo de demanda mensual para siete segmentos y simulación de los escenarios central, optimista y pesimista.

## Archivos necesarios

- `modelo.py`: cálculo de demanda, plan de fabricación y simulación.
- `config.json`: supuestos de los escenarios y política de inventario.
- `requirements.txt`: dos dependencias con las versiones utilizadas.
- `data/`: los siete CSV originales del caso.

En GitHub, `entrega/` contiene los dos PDF finales y el ZIP con este código y los datos.

## Ejecutar

Python 3.12 es la versión utilizada. Desde la carpeta del modelo:

```bash
python -m venv .venv
```

Activar el entorno con `source .venv/bin/activate` en macOS/Linux o `.venv\Scripts\activate` en Windows. Después:

```bash
pip install -r requirements.txt
python modelo.py --n 1000 --seed 20261008
```

El programa crea `resultados/`. Las tablas principales son:

- `demanda_A013_mensual.csv`: demanda por mes, segmento y escenario.
- `plan_fabricacion_A013.csv`: propuesta mensual de fabricación.
- `tabla5.csv`: ventas, stock, costes y contribución por segmento y escenario.

También genera tablas de validación y trazabilidad. No se incluyen resultados precalculados en el ZIP para evitar duplicados.

## Criterios de cálculo

La demanda combina mercado y cuota de Kaido, con estacionalidad, variables económicas y corrección de sucesos. La simulación usa 1.000 réplicas por escenario, stock FIFO y revisión mensual de pedidos; el pedido de enero llega en abril. Los supuestos editables están en `config.json`.

El tránsito inicial es estimado. La validación A012 da un error WAPE del 28,3%; MD y CSUV presentan mayor incertidumbre. El CVP neto es contribución de marca después de los costes modelados, no beneficio contable.

Fuente del enunciado y los datos: https://github.com/UAX-VCMT-26-27/sim-kaido-motors. Uso docente.
