
import argparse
import csv
import random
import time
from pathlib import Path

from db import reset_db, upsert_events


def read_events(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {
                "event_id": int(row["event_id"]),
                "event_time": row["event_time"],
                "category": row["category"],
                "campus": row["campus"],
                "amount": float(row["amount"]),
            }
            for row in csv.DictReader(f)
        ]


def run_lambda(events, db):
    # Dos rutas simplificadas: lote principal y lote incremental.
    split = max(1, int(len(events) * 0.8))

    upsert_events(events[:split], db)
    upsert_events(events[split:], db)

    # Reconciliación idempotente de los últimos eventos.
    upsert_events(events[-min(100, len(events)):], db)


def run_kappa(events, db):
    # Ruta única simplificada de procesamiento por bloques.
    for start in range(0, len(events), 500):
        upsert_events(events[start:start + 500], db)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/events.csv")
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument(
        "--output",
        default="results/ingest_benchmark_randomized.csv"
    )
    parser.add_argument(
        "--db",
        default="results/benchmark_randomized.sqlite"
    )
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError("--runs debe ser mayor que cero.")

    events = read_events(args.input)

    if not events:
        raise ValueError("El archivo de entrada no contiene registros.")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    architectures = {
        "Lambda_simplificada": run_lambda,
        "Kappa_simplificada": run_kappa,
    }

    # Cada bloque contiene ambas arquitecturas en orden aleatorio.
    rng = random.Random(args.seed)
    schedule = []

    for run_number in range(1, args.runs + 1):
        block = list(architectures.keys())
        rng.shuffle(block)

        for architecture in block:
            schedule.append((run_number, architecture))

    rows = []

    for run_number, name in schedule:
        # Se utiliza la misma base de datos, limpiándola antes
        # de cada ejecución para mantener condiciones comparables.
        reset_db(args.db)

        start = time.perf_counter()
        architectures[name](events, args.db)
        elapsed = time.perf_counter() - start

        row = {
            "architecture": name,
            "run": run_number,
            "records": len(events),
            "elapsed_seconds": round(elapsed, 6),
            "records_per_second": round(len(events) / elapsed, 2),
            "seed": args.seed,
        }

        rows.append(row)
        print(row)

    with output.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nBenchmark aleatorizado guardado en: {output}")
    print(f"Total de ejecuciones: {len(rows)}")
    print(f"Repeticiones por arquitectura: {args.runs}")


if __name__ == "__main__":
    main()
