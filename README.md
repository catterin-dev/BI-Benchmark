# BI Benchmark: ingesta Lambda/Kappa y API REST/GraphQL
**Autor:** Catterine Carely Quispe Quispe

Proyecto académico reproducible para comparar prototipos locales de ingesta analítica y API sobre SQLite.

**Alcance:** implementación educativa local; no es un clúster distribuido ni una prueba de Kafka/Spark. Los resultados describen solo este prototipo y el equipo usado.

## Requisitos
Python 3.10+.

## Instalación (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
macOS/Linux: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`.

## 1. Generar datos
```bash
python src/generate_data.py --rows 10000 --output data/events.csv
```

## 2. Benchmark de ingesta
```bash
python src/ingest_benchmark.py --input data/events.csv --runs 5 --output results/ingest_benchmark.csv
```
Lambda simplificada separa batch y speed y reconcilia por `event_id`; Kappa simplificada recorre un flujo por bloques. Se miden segundos y registros/segundo.

## 3. Iniciar las API en dos terminales
```bash
uvicorn src.api_rest:app --host 127.0.0.1 --port 8000
```
```bash
uvicorn src.api_graphql:app --host 127.0.0.1 --port 8001
```
REST: http://127.0.0.1:8000/docs | GraphQL: http://127.0.0.1:8001/graphql

## 4. Benchmark API
Con ambas API activas, en una tercera terminal:
```bash
python src/api_benchmark.py --requests 300 --output results/api_benchmark.csv
```
Registra latencia media/mediana/p95, throughput y errores. Repite 3–5 veces. No compares una API fría con otra caliente.

## Métricas
- Rendimiento de ingesta = registros procesados / segundos.
- Latencia = tiempo entre envío y respuesta HTTP.
- p95 = percentil 95 de latencia.
- Throughput = solicitudes correctas / segundos.
- Tasa de error = errores / solicitudes totales × 100.

## Reproducibilidad
Registra SO, CPU, RAM y versión de Python. Cierra aplicaciones pesadas, usa el mismo CSV y configuración, ejecuta cinco corridas por escenario y reporta mediana y dispersión. Los resultados del informe son campos por completar, no datos inventados.

## Estructura
`src/generate_data.py`, `src/ingest_benchmark.py`, `src/db.py`, `src/api_rest.py`, `src/api_graphql.py`, `src/api_benchmark.py`, `tests/test_db.py`.

## Limitaciones
SQLite y ejecución en un solo proceso no representan Big Data distribuido. El benchmark API es secuencial, no concurrente. Para ampliar el estudio, repetir con Kafka/Spark, PostgreSQL y Locust/k6.
