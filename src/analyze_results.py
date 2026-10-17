from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Directorio principal del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT_DIR / "results" / "api_benchmark.csv"
OUTPUT_DIR = ROOT_DIR / "results" / "api_analysis"

def main():
    # Verificar que exista el archivo de resultados
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {CSV_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Leer resultados del benchmark
    df = pd.read_csv(CSV_FILE)

    required_columns = [
        "api",
        "requests",
        "errors",
        "error_rate_pct",
        "mean_latency_ms",
        "median_latency_ms",
        "p95_latency_ms",
        "throughput_success_req_s",
        "total_seconds",
    ]

    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(
            f"Faltan columnas en el CSV: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError("El archivo CSV no contiene resultados.")

    print("\n=== RESULTADOS DEL BENCHMARK ===")
    print(df[required_columns].to_string(index=False))

    # Guardar tabla comparativa
    df[required_columns].to_csv(
        OUTPUT_DIR / "tabla_comparativa.csv",
        index=False,
    )

    # Métricas para graficar
    metrics = [
        (
            "mean_latency_ms",
            "Latencia promedio",
            "Milisegundos (ms)",
            "01_latencia_promedio.png",
        ),
        (
            "p95_latency_ms",
            "Latencia p95",
            "Milisegundos (ms)",
            "02_latencia_p95.png",
        ),
        (
            "throughput_success_req_s",
            "Throughput exitoso",
            "Peticiones por segundo",
            "03_throughput.png",
        ),
        (
            "total_seconds",
            "Duración total del benchmark",
            "Segundos",
            "04_duracion_total.png",
        ),
    ]

    for column, title, ylabel, filename in metrics:
        fig, ax = plt.subplots(figsize=(8, 5))

        bars = ax.bar(df["api"], df[column])

        ax.set_title(title)
        ax.set_xlabel("API")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.bar_label(bars, fmt="%.2f", padding=3)

        fig.tight_layout()
        fig.savefig(
            OUTPUT_DIR / filename,
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)

    # Comparación porcentual descriptiva
    rest = df.loc[df["api"] == "REST"]
    graphql = df.loc[df["api"] == "GraphQL"]

    if len(rest) == 1 and len(graphql) == 1:
        rest = rest.iloc[0]
        graphql = graphql.iloc[0]

        latency_diff = (
            (graphql["mean_latency_ms"] -
             rest["mean_latency_ms"])
            / graphql["mean_latency_ms"]
        ) * 100

        throughput_diff = (
            (rest["throughput_success_req_s"] -
             graphql["throughput_success_req_s"])
            / graphql["throughput_success_req_s"]
        ) * 100

        print("\n=== COMPARACIÓN DESCRIPTIVA ===")
        print(
            f"REST tuvo una latencia promedio "
            f"{latency_diff:.2f}% menor que GraphQL."
        )
        print(
            f"REST obtuvo un throughput "
            f"{throughput_diff:.2f}% mayor que GraphQL."
        )

    print(f"\nAnálisis guardado en: {OUTPUT_DIR}")
    print("Se generaron la tabla y los cuatro gráficos.")

if __name__ == "__main__":
    main()
