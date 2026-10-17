
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Rutas del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT_DIR / "results" / "ingest_benchmark.csv"
OUTPUT_DIR = ROOT_DIR / "results" / "ingest_analysis"


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {CSV_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Leer los resultados reales
    df = pd.read_csv(CSV_FILE)

    required = [
        "architecture",
        "run",
        "records",
        "elapsed_seconds",
        "records_per_second",
    ]

    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(
            f"Faltan columnas en el CSV: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError("El archivo no contiene resultados.")

    print("\n=== DATOS DEL BENCHMARK DE INGESTA ===")
    print(df.to_string(index=False))

    # Estadísticas descriptivas por arquitectura
    summary = (
        df.groupby("architecture")
        .agg(
            repetitions=("run", "count"),
            records_per_run=("records", "mean"),
            mean_time_s=("elapsed_seconds", "mean"),
            median_time_s=("elapsed_seconds", "median"),
            std_time_s=("elapsed_seconds", "std"),
            min_time_s=("elapsed_seconds", "min"),
            max_time_s=("elapsed_seconds", "max"),
            mean_records_per_second=("records_per_second", "mean"),
            median_records_per_second=("records_per_second", "median"),
            std_records_per_second=("records_per_second", "std"),
        )
        .reset_index()
    )

    # Coeficiente de variación: desviación estándar / media
    summary["cv_time_pct"] = (
        summary["std_time_s"] / summary["mean_time_s"] * 100
    )

    summary.to_csv(
        OUTPUT_DIR / "resumen_estadistico.csv",
        index=False,
        float_format="%.6f",
    )

    print("\n=== RESUMEN ESTADÍSTICO ===")
    print(summary.round(4).to_string(index=False))

    # Gráfico 1: tiempo de cada repetición
    fig, ax = plt.subplots(figsize=(9, 5))

    for architecture, group in df.groupby("architecture"):
        ax.plot(
            group["run"],
            group["elapsed_seconds"],
            marker="o",
            label=architecture,
        )

    ax.set_title("Tiempo de ejecución por repetición")
    ax.set_xlabel("Repetición")
    ax.set_ylabel("Tiempo (segundos)")
    ax.set_xticks(sorted(df["run"].unique()))
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "01_tiempo_por_repeticion.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Gráfico 2: tiempo promedio
    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        summary["architecture"],
        summary["mean_time_s"],
    )

    ax.set_title("Tiempo promedio de ingesta")
    ax.set_xlabel("Arquitectura")
    ax.set_ylabel("Tiempo promedio (segundos)")
    ax.bar_label(bars, fmt="%.4f", padding=3)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "02_tiempo_promedio.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Gráfico 3: throughput promedio reportado
    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        summary["architecture"],
        summary["mean_records_per_second"],
    )

    ax.set_title("Throughput promedio de ingesta")
    ax.set_xlabel("Arquitectura")
    ax.set_ylabel("Registros por segundo")
    ax.bar_label(bars, fmt="%.0f", padding=3)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "03_throughput_promedio.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Gráfico 4: variabilidad del tiempo
    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        summary["architecture"],
        summary["cv_time_pct"],
    )

    ax.set_title("Variabilidad relativa del tiempo")
    ax.set_xlabel("Arquitectura")
    ax.set_ylabel("Coeficiente de variación (%)")
    ax.bar_label(bars, fmt="%.2f%%", padding=3)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "04_variabilidad_tiempo.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Comparación descriptiva entre ambas implementaciones
    lambda_rows = summary[
        summary["architecture"] == "Lambda_simplificada"
    ]
    kappa_rows = summary[
        summary["architecture"] == "Kappa_simplificada"
    ]

    if len(lambda_rows) == 1 and len(kappa_rows) == 1:
        lambda_mean = lambda_rows.iloc[0]["mean_time_s"]
        kappa_mean = kappa_rows.iloc[0]["mean_time_s"]

        if kappa_mean > 0:
            difference_pct = (
                (kappa_mean - lambda_mean) / kappa_mean
            ) * 100

            print("\n=== COMPARACIÓN DESCRIPTIVA ===")
            print(
                "Diferencia de tiempo promedio a favor de Lambda: "
                f"{difference_pct:.2f}% menos tiempo."
            )

    print(f"\nResultados guardados en: {OUTPUT_DIR}")
    print("Se generaron el resumen estadístico y cuatro gráficos.")


if __name__ == "__main__":
    main()
