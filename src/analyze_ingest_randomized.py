
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "results" / "ingest_benchmark_randomized.csv"
OUTPUT_DIR = ROOT / "results" / "ingest_analysis_randomized"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_FILE)

    required = {
        "architecture", "run", "records",
        "elapsed_seconds", "records_per_second"
    }
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Faltan columnas: {sorted(missing)}")

    if df[list(required)].isnull().any().any():
        raise ValueError("Hay valores vacios en las columnas requeridas.")

    expected = {"Lambda_simplificada", "Kappa_simplificada"}
    if set(df["architecture"].unique()) != expected:
        raise ValueError("Las arquitecturas del archivo no son las esperadas.")

    counts = df.groupby("architecture")["run"].count()
    if len(counts) != 2 or not (counts == 30).all():
        raise ValueError("Se esperaban 30 ejecuciones por arquitectura.")

    if (df["elapsed_seconds"] <= 0).any():
        raise ValueError("Hay tiempos de ejecucion no positivos.")

    # Verificar que cada bloque tenga una medicion de cada arquitectura.
    pivot = df.pivot(
        index="run",
        columns="architecture",
        values="elapsed_seconds"
    )

    if pivot.isnull().any().any() or len(pivot) != 30:
        raise ValueError(
            "Cada repeticion debe contener una medicion de Lambda y Kappa."
        )

    # Estadisticas descriptivas por arquitectura.
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

    summary["cv_time_pct"] = (
        summary["std_time_s"] / summary["mean_time_s"] * 100
    )

    summary.to_csv(
        OUTPUT_DIR / "resumen_estadistico_randomized.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8-sig"
    )

    print("\n=== RESUMEN ESTADISTICO: BENCHMARK ALEATORIZADO ===")
    print(summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}"
    ))

    means = summary.set_index("architecture")["mean_time_s"]
    lambda_mean = means["Lambda_simplificada"]
    kappa_mean = means["Kappa_simplificada"]

    difference = kappa_mean - lambda_mean
    reduction_pct = difference / kappa_mean * 100
    ratio = kappa_mean / lambda_mean

    print("\n=== COMPARACION DE TIEMPOS PROMEDIO ===")
    print(f"Media Lambda: {lambda_mean:.6f} segundos")
    print(f"Media Kappa:  {kappa_mean:.6f} segundos")
    print(f"Diferencia Kappa - Lambda: {difference:.6f} segundos")
    print(f"Reduccion descriptiva: {reduction_pct:.2f}%")
    print(f"Relacion de tiempos Kappa/Lambda: {ratio:.2f}x")

    # Comparacion por bloques emparejados: mismo numero de repeticion.
    paired = pivot.copy()
    paired["difference_kappa_minus_lambda_s"] = (
        paired["Kappa_simplificada"] - paired["Lambda_simplificada"]
    )
    paired["reduction_pct"] = (
        paired["difference_kappa_minus_lambda_s"]
        / paired["Kappa_simplificada"] * 100
    )

    print("\n=== COMPARACION POR BLOQUES ===")
    print(
        "Bloques donde Lambda fue mas rapida: "
        f"{(paired['difference_kappa_minus_lambda_s'] > 0).sum()} de 30"
    )
    print(
        "Reduccion media por bloque: "
        f"{paired['reduction_pct'].mean():.2f}%"
    )
    print(
        "Mediana de la reduccion por bloque: "
        f"{paired['reduction_pct'].median():.2f}%"
    )

    paired.reset_index().to_csv(
        OUTPUT_DIR / "comparacion_por_bloque.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8-sig"
    )

    # Bootstrap emparejado del promedio de reduccion por bloque.
    rng = np.random.default_rng(2026)
    values = paired["reduction_pct"].to_numpy()
    iterations = 20000

    boot_means = np.empty(iterations)
    for i in range(iterations):
        sample = rng.choice(values, size=len(values), replace=True)
        boot_means[i] = sample.mean()

    ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])

    print("\n=== BOOTSTRAP EMPAREJADO: INTERVALO DEL 95% ===")
    print(f"Reduccion media por bloque: {values.mean():.2f}%")
    print(f"Limite inferior: {ci_low:.2f}%")
    print(f"Limite superior: {ci_high:.2f}%")

    comparison = pd.DataFrame([{
        "lambda_mean_s": lambda_mean,
        "kappa_mean_s": kappa_mean,
        "difference_kappa_minus_lambda_s": difference,
        "descriptive_reduction_pct": reduction_pct,
        "time_ratio_kappa_over_lambda": ratio,
        "blocks_lambda_faster": int(
            (paired["difference_kappa_minus_lambda_s"] > 0).sum()
        ),
        "mean_paired_reduction_pct": values.mean(),
        "median_paired_reduction_pct": np.median(values),
        "paired_bootstrap_ci95_lower_pct": ci_low,
        "paired_bootstrap_ci95_upper_pct": ci_high,
        "bootstrap_iterations": iterations,
        "seed": 2026
    }])

    comparison.to_csv(
        OUTPUT_DIR / "comparacion_bootstrap_randomized.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8-sig"
    )

    # Grafico 1: distribucion de tiempos.
    plt.figure(figsize=(9, 5))
    df.boxplot(column="elapsed_seconds", by="architecture")
    plt.title("Distribucion del tiempo de ingesta")
    plt.suptitle("")
    plt.xlabel("Arquitectura")
    plt.ylabel("Tiempo (segundos)")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "01_distribucion_tiempos.png",
        dpi=160
    )
    plt.close()

    # Grafico 2: tiempos por bloque.
    plt.figure(figsize=(10, 5))
    for name in ["Lambda_simplificada", "Kappa_simplificada"]:
        plt.plot(
            pivot.index,
            pivot[name],
            marker="o",
            markersize=3,
            label=name
        )
    plt.title("Tiempo por bloque de ejecucion")
    plt.xlabel("Bloque")
    plt.ylabel("Tiempo (segundos)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "02_tiempo_por_bloque.png",
        dpi=160
    )
    plt.close()

    # Grafico 3: throughput promedio.
    throughput = summary.set_index("architecture")[
        "mean_records_per_second"
    ]
    plt.figure(figsize=(8, 5))
    throughput.plot(kind="bar")
    plt.title("Throughput promedio")
    plt.xlabel("Arquitectura")
    plt.ylabel("Registros por segundo")
    plt.xticks(rotation=10)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "03_throughput_promedio.png",
        dpi=160
    )
    plt.close()

    print(f"\nResultados guardados en: {OUTPUT_DIR}")
    print("Se generaron tres CSV y tres graficos.")


if __name__ == "__main__":
    main()
