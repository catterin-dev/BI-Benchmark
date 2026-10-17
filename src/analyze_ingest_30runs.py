
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "results" / "ingest_benchmark_30runs.csv"
OUTPUT_DIR = ROOT / "results" / "ingest_analysis_30runs"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo: {INPUT_FILE}"
        )

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

    counts = df.groupby("architecture")["run"].count()

    if len(counts) != 2 or not (counts == 30).all():
        raise ValueError(
            "Se esperaban dos arquitecturas con 30 repeticiones cada una."
        )

    if (df["elapsed_seconds"] <= 0).any():
        raise ValueError("Se encontraron tiempos no positivos.")

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
        OUTPUT_DIR / "resumen_estadistico_30runs.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8-sig"
    )

    print("\n=== RESUMEN ESTADISTICO: 30 REPETICIONES ===")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.6f}"))

    # Comparacion de medias.
    means = summary.set_index("architecture")["mean_time_s"]
    lambda_mean = means["Lambda_simplificada"]
    kappa_mean = means["Kappa_simplificada"]

    difference = kappa_mean - lambda_mean
    reduction_pct = difference / kappa_mean * 100

    print("\n=== COMPARACION DE TIEMPOS ===")
    print(f"Media Lambda: {lambda_mean:.6f} segundos")
    print(f"Media Kappa:  {kappa_mean:.6f} segundos")
    print(f"Diferencia Kappa - Lambda: {difference:.6f} segundos")
    print(f"Reduccion descriptiva del tiempo: {reduction_pct:.2f}%")
    print(f"Relacion de tiempos Kappa/Lambda: {kappa_mean/lambda_mean:.2f}x")

    # Bootstrap independiente para intervalo de confianza del 95%.
    # Las dos series se remuestrean por separado.
    rng = np.random.default_rng(2026)

    lam = df.loc[
        df["architecture"] == "Lambda_simplificada",
        "elapsed_seconds"
    ].to_numpy()

    kap = df.loc[
        df["architecture"] == "Kappa_simplificada",
        "elapsed_seconds"
    ].to_numpy()

    iterations = 20000
    boot_reductions = np.empty(iterations)

    for i in range(iterations):
        lam_sample = rng.choice(lam, size=len(lam), replace=True)
        kap_sample = rng.choice(kap, size=len(kap), replace=True)

        lam_avg = lam_sample.mean()
        kap_avg = kap_sample.mean()

        boot_reductions[i] = (
            (kap_avg - lam_avg) / kap_avg * 100
        )

    ci_low, ci_high = np.percentile(boot_reductions, [2.5, 97.5])

    print("\n=== INTERVALO DE CONFIANZA BOOTSTRAP DEL 95% ===")
    print(f"Reduccion del tiempo: {reduction_pct:.2f}%")
    print(f"Limite inferior: {ci_low:.2f}%")
    print(f"Limite superior: {ci_high:.2f}%")

    pd.DataFrame([{
        "lambda_mean_s": lambda_mean,
        "kappa_mean_s": kappa_mean,
        "difference_kappa_minus_lambda_s": difference,
        "descriptive_time_reduction_pct": reduction_pct,
        "time_ratio_kappa_over_lambda": kappa_mean / lambda_mean,
        "bootstrap_ci95_lower_pct": ci_low,
        "bootstrap_ci95_upper_pct": ci_high,
        "bootstrap_iterations": iterations,
        "seed": 2026
    }]).to_csv(
        OUTPUT_DIR / "comparacion_bootstrap_30runs.csv",
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
    plt.xticks(rotation=10)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "01_distribucion_tiempos.png",
        dpi=160
    )
    plt.close()

    # Grafico 2: tiempos por repeticion.
    plt.figure(figsize=(10, 5))
    for name, group in df.groupby("architecture"):
        plt.plot(
            group["run"],
            group["elapsed_seconds"],
            marker="o",
            markersize=3,
            label=name
        )

    plt.title("Tiempo por repeticion: 30 ejecuciones")
    plt.xlabel("Repeticion")
    plt.ylabel("Tiempo (segundos)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "02_tiempo_por_repeticion.png",
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
    print("Se generaron dos CSV y tres graficos.")


if __name__ == "__main__":
    main()
