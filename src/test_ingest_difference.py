
from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "results" / "ingest_benchmark_randomized.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    pivot = df.pivot(
        index="run",
        columns="architecture",
        values="elapsed_seconds"
    ).sort_index()

    if pivot.isnull().any().any() or len(pivot) != 30:
        raise ValueError("Se requieren 30 bloques completos.")

    # Diferencia positiva: Kappa tardó más que Lambda.
    differences = (
        pivot["Kappa_simplificada"]
        - pivot["Lambda_simplificada"]
    )

    n = len(differences)
    lambda_faster = int((differences > 0).sum())
    ties = int((differences == 0).sum())
    kappa_faster = int((differences < 0).sum())

    # Prueba exacta de signos, bilateral.
    # Bajo H0, cada signo tiene probabilidad 0.5.
    non_ties = n - ties
    k = min(lambda_faster, kappa_faster)

    if non_ties == 0:
        p_value = 1.0
    else:
        tail = sum(
            math.comb(non_ties, i)
            for i in range(k + 1)
        ) / (2 ** non_ties)

        p_value = min(1.0, 2 * tail)

    print("\n=== PRUEBA DE SIGNOS EMPAREJADA ===")
    print(f"Bloques analizados: {n}")
    print(f"Lambda mas rapida: {lambda_faster}")
    print(f"Kappa mas rapida: {kappa_faster}")
    print(f"Empates: {ties}")
    print(f"Mediana de la diferencia Kappa - Lambda: "
          f"{differences.median():.6f} segundos")
    print(f"Valor p bilateral: {p_value:.10g}")

    print("\n=== INTERPRETACION ===")
    if p_value < 0.05:
        print(
            "Se rechaza la hipotesis nula de igualdad de probabilidades "
            "de que cada arquitectura sea mas rapida, al nivel 0.05."
        )
    else:
        print(
            "No se rechaza la hipotesis nula al nivel 0.05."
        )

    print(
        "\nNota: la prueba de signos evalua la consistencia de la "
        "direccion de las diferencias; no mide por si sola el tamano "
        "de la ventaja ni corrige efectos del entorno."
    )


if __name__ == "__main__":
    main()
