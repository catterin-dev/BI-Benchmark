
import csv
import math
from pathlib import Path
from statistics import mean, median

BASE_DIR = Path(__file__).resolve().parent.parent

ARCHIVOS = {
    "REST": [
        ("resultados_rest.jtl", 1),
        ("resultados_rest_ronda2.jtl", 2),
        ("resultados_rest_ronda3.jtl", 3),
        ("resultados_rest_ronda4.jtl", 4),
    ],
    "GraphQL": [
        ("resultados_graphql.jtl", 1),
        ("resultados_graphql_ronda2.jtl", 2),
        ("resultados_graphql_ronda3.jtl", 3),
        ("resultados_graphql_ronda4.jtl", 4),
    ],
}


def percentile(values, p):
    """Percentil con interpolación lineal."""
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return (
        ordered[lower] * (upper - position)
        + ordered[upper] * (position - lower)
    )


def load_jtl(filename):
    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError(f"El archivo está vacío: {filename}")

    required = {"elapsed", "success", "timeStamp"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError(
            f"{filename} no contiene las columnas necesarias: "
            "elapsed, success y timeStamp."
        )

    for row in rows:
        row["elapsed"] = float(row["elapsed"])
        row["timeStamp"] = float(row["timeStamp"])
        row["success"] = row["success"].strip().lower() == "true"

    return rows


def calculate_metrics(api, round_name, rows):
    times = [row["elapsed"] for row in rows]
    successful = sum(row["success"] for row in rows)
    failed = len(rows) - successful

    # Estimación de duración a partir de las marcas de tiempo JMeter.
    start = min(row["timeStamp"] for row in rows)
    end = max(row["timeStamp"] + row["elapsed"] for row in rows)
    duration_seconds = max((end - start) / 1000, 0.001)

    return {
        "API": api,
        "Ronda": round_name,
        "Muestras": len(rows),
        "Exitosas": successful,
        "Fallidas": failed,
        "Errores_pct": round(failed / len(rows) * 100, 2),
        "Promedio_ms": round(mean(times), 2),
        "Mediana_ms": round(median(times), 2),
        "P95_ms": round(percentile(times, 0.95), 2),
        "Minimo_ms": round(min(times), 2),
        "Maximo_ms": round(max(times), 2),
        "Duracion_seg": round(duration_seconds, 3),
        "Solicitudes_segundo": round(len(rows) / duration_seconds, 2),
    }


def write_csv(filename, rows):
    if not rows:
        return

    path = BASE_DIR / filename
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Archivo generado: {path.name}")


def main():
    round_results = []
    all_rows = {}

    for api, files in ARCHIVOS.items():
        all_api_rows = []

        for filename, round_number in files:
            rows = load_jtl(filename)
            all_api_rows.extend(rows)

            metrics = calculate_metrics(
                api, f"Ronda {round_number}", rows
            )
            round_results.append(metrics)

        all_rows[api] = all_api_rows

        
    
    
    consolidated = []
    for api, rows in all_rows.items():
        result = calculate_metrics(
            api, "Consolidado 4 rondas", rows
        )

        round_metrics = [
            item for item in round_results
            if item["API"] == api
        ]

        total_duration = sum(
            item["Duracion_seg"] for item in round_metrics
        )

        result["Duracion_seg"] = round(total_duration, 3)
        result["Solicitudes_segundo"] = round(
            len(rows) / total_duration, 2
        )

        consolidated.append(result)


    print("\n=== RESULTADOS POR RONDA ===")
    for row in round_results:
        print(
            f'{row["API"]:8} | {row["Ronda"]:8} | '
            f'Muestras: {row["Muestras"]:3} | '
            f'Promedio: {row["Promedio_ms"]:7.2f} ms | '
            f'P95: {row["P95_ms"]:7.2f} ms | '
            f'Errores: {row["Errores_pct"]:5.2f}% | '
            f'Req/s: {row["Solicitudes_segundo"]:6.2f}'
        )

    print("\n=== RESULTADOS CONSOLIDADOS ===")
    for row in consolidated:
        print(
            f'{row["API"]:8} | '
            f'Muestras: {row["Muestras"]:3} | '
            f'Exitosas: {row["Exitosas"]:3} | '
            f'Fallidas: {row["Fallidas"]:3} | '
            f'Promedio: {row["Promedio_ms"]:7.2f} ms | '
            f'Mediana: {row["Mediana_ms"]:7.2f} ms | '
            f'P95: {row["P95_ms"]:7.2f} ms | '
            f'Req/s: {row["Solicitudes_segundo"]:6.2f}'
        )

    write_csv("resultados_api_por_ronda.csv", round_results)
    write_csv("resultados_api_consolidado.csv", consolidated)


if __name__ == "__main__":
    main()
