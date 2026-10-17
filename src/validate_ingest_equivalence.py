
import csv
from pathlib import Path

from ingest_benchmark import read_events, run_lambda, run_kappa
from db import reset_db, upsert_events, summary, connect


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data" / "events.csv"
OUTPUT_DIR = ROOT / "results" / "ingest_validation"

LAMBDA_DB = OUTPUT_DIR / "lambda_validation.sqlite"
KAPPA_DB = OUTPUT_DIR / "kappa_validation.sqlite"


def read_database(db_path):
    conn = connect(str(db_path))
    try:
        rows = conn.execute("""
            SELECT event_id, event_time, category, campus, amount
            FROM events
            ORDER BY event_id
        """).fetchall()
        return rows
    finally:
        conn.close()


def compare_summaries(lambda_summary, kappa_summary):
    differences = []

    if lambda_summary["total_events"] != kappa_summary["total_events"]:
        differences.append("El total de eventos no coincide")

    if lambda_summary["total_amount"] != kappa_summary["total_amount"]:
        differences.append("El importe total no coincide")

    if lambda_summary["by_category"] != kappa_summary["by_category"]:
        differences.append("El resumen por categoria no coincide")

    return differences


def save_report(checks):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUT_DIR / "validation_report.csv"

    with report_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "details"]
        )
        writer.writeheader()
        writer.writerows(checks)

    return report_file


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n=== VALIDACION DE EQUIVALENCIA ===")

    events = read_events(str(INPUT_FILE))

    if not events:
        raise ValueError("El archivo de entrada no contiene eventos.")

    print(f"Eventos de entrada: {len(events)}")

    # Cada arquitectura utiliza una base de datos independiente.
    reset_db(str(LAMBDA_DB))
    reset_db(str(KAPPA_DB))

    run_lambda(events, str(LAMBDA_DB))
    run_kappa(events, str(KAPPA_DB))

    lambda_rows = read_database(LAMBDA_DB)
    kappa_rows = read_database(KAPPA_DB)

    checks = []

    # 1. Cantidad de registros.
    count_ok = (
        len(lambda_rows) == len(events)
        and len(kappa_rows) == len(events)
    )

    checks.append({
        "check": "Cantidad de registros",
        "status": "APROBADO" if count_ok else "NO APROBADO",
        "details": (
            f"Entrada={len(events)}; "
            f"Lambda={len(lambda_rows)}; Kappa={len(kappa_rows)}"
        )
    })

    # 2. Comparación de cada registro y cada campo.
    equivalent = lambda_rows == kappa_rows

    checks.append({
        "check": "Equivalencia registro por registro",
        "status": "APROBADO" if equivalent else "NO APROBADO",
        "details": (
            "Todos los registros y campos coinciden."
            if equivalent
            else "Existen registros o campos diferentes."
        )
    })

    # 3. Comparación de los resúmenes.
    lambda_summary = summary(str(LAMBDA_DB))
    kappa_summary = summary(str(KAPPA_DB))

    summary_differences = compare_summaries(
        lambda_summary, kappa_summary
    )

    checks.append({
        "check": "Equivalencia de resumenes",
        "status": (
            "APROBADO" if not summary_differences
            else "NO APROBADO"
        ),
        "details": (
            "Totales y categorias coinciden."
            if not summary_differences
            else "; ".join(summary_differences)
        )
    })

    # 4. Idempotencia: reprocesar los ultimos 100 eventos.
    before_reprocessing = read_database(LAMBDA_DB)

    upsert_events(
        events[-min(100, len(events)):],
        str(LAMBDA_DB)
    )

    after_reprocessing = read_database(LAMBDA_DB)

    idempotent = before_reprocessing == after_reprocessing

    checks.append({
        "check": "Idempotencia de Lambda",
        "status": "APROBADO" if idempotent else "NO APROBADO",
        "details": (
            "Reprocesar los ultimos eventos no cambio la base de datos."
            if idempotent
            else "El reprocesamiento modifico los datos finales."
        )
    })

    # 5. Comparar resultados de negocio.
    print("\nResumen Lambda:")
    print(lambda_summary)

    print("\nResumen Kappa:")
    print(kappa_summary)

    print("\n=== RESULTADOS DE VALIDACION ===")

    for check in checks:
        print(
            f'{check["status"]}: {check["check"]} - '
            f'{check["details"]}'
        )

    report_file = save_report(checks)

    all_passed = all(
        check["status"] == "APROBADO" for check in checks
    )

    print("\nRESULTADO GENERAL:", 
          "APROBADO" if all_passed else "REVISAR DIFERENCIAS")

    print("Informe guardado en:", report_file)
    print("Base Lambda:", LAMBDA_DB)
    print("Base Kappa:", KAPPA_DB)


if __name__ == "__main__":
    main()
