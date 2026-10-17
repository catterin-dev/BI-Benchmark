
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "results" / "ingest_benchmark_randomized.csv"
OUTPUT_DIR = ROOT / "results" / "ingest_audit"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"No se encontro: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_FILE)

    required = {
        "architecture", "run", "elapsed_seconds", "records"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas: {sorted(missing)}")

    # Resumen general y deteccion exploratoria mediante IQR.
    audit_rows = []

    print("\n=== REVISION DE TIEMPOS POR ARQUITECTURA ===")

    for name, group in df.groupby("architecture"):
        times = group["elapsed_seconds"]
        q1 = times.quantile(0.25)
        q3 = times.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        flagged = group[
            (group["elapsed_seconds"] < lower)
            | (group["elapsed_seconds"] > upper)
        ]

        print(f"\nArquitectura: {name}")
        print(f"Media: {times.mean():.6f} s")
        print(f"Mediana: {times.median():.6f} s")
        print(f"Desviacion estandar: {times.std():.6f} s")
        print(f"Q1: {q1:.6f} s | Q3: {q3:.6f} s")
        print(f"Limite inferior IQR: {lower:.6f} s")
        print(f"Limite superior IQR: {upper:.6f} s")
        print(f"Valores marcados por IQR: {len(flagged)}")

        if not flagged.empty:
            print(
                flagged[["run", "elapsed_seconds"]]
                .sort_values("run")
                .to_string(index=False)
            )

        audit_rows.append({
            "architecture": name,
            "n": len(times),
            "mean_s": times.mean(),
            "median_s": times.median(),
            "std_s": times.std(),
            "q1_s": q1,
            "q3_s": q3,
            "iqr_lower_s": lower,
            "iqr_upper_s": upper,
            "iqr_flagged_count": len(flagged),
            "iqr_flagged_runs": ",".join(
                map(str, flagged["run"].tolist())
            ),
        })

    pd.DataFrame(audit_rows).to_csv(
        OUTPUT_DIR / "audit_by_architecture.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8-sig"
    )

    # Comparacion emparejada por numero de bloque.
    pivot = df.pivot(
        index="run",
        columns="architecture",
        values="elapsed_seconds"
    ).sort_index()

    lambda_col = "Lambda_simplificada"
    kappa_col = "Kappa_simplificada"

    if pivot[[lambda_col, kappa_col]].isnull().any().any():
        raise ValueError("Hay bloques sin ambas arquitecturas.")

    pivot["kappa_minus_lambda_s"] = (
        pivot[kappa_col] - pivot[lambda_col]
    )

    print("\n=== BLOQUES CON MAYORES TIEMPOS ===")
    print(
        pivot.sort_values(
            kappa_col, ascending=False
        ).head(5).to_string(float_format=lambda x: f"{x:.6f}")
    )

    # Analisis de sensibilidad: excluir bloques 19 y 20 solo
    # para medir su influencia, no para decidir eliminarlos.
    all_blocks = pivot
    sensitivity_blocks = pivot.drop(index=[19, 20], errors="ignore")

    def report(label, data):
        lam_mean = data[lambda_col].mean()
        kap_mean = data[kappa_col].mean()
        reduction = (kap_mean - lam_mean) / kap_mean * 100

        print(f"\n{label}")
        print(f"Bloques incluidos: {len(data)}")
        print(f"Media Lambda: {lam_mean:.6f} s")
        print(f"Media Kappa: {kap_mean:.6f} s")
        print(f"Reduccion descriptiva: {reduction:.2f}%")
        print(
            "Bloques donde Lambda fue mas rapida: "
            f"{(data['kappa_minus_lambda_s'] > 0).sum()}"
        )

    report("=== ANALISIS CON TODOS LOS BLOQUES ===", all_blocks)
    report(
        "=== SENSIBILIDAD SIN BLOQUES 19 Y 20 (SOLO COMPARACION) ===",
        sensitivity_blocks
    )

    pivot.reset_index().to_csv(
        OUTPUT_DIR / "audit_by_block.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8-sig"
    )

    print(f"\nArchivos guardados en: {OUTPUT_DIR}")
    print("No se han eliminado ni modificado observaciones del benchmark.")


if __name__ == "__main__":
    main()
