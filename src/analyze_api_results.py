
from pathlib import Path
import pandas as pd

# Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

ARCHIVOS = {
    "REST": BASE_DIR / "resultados_rest.jtl",
    "GraphQL": BASE_DIR / "resultados_graphql.jtl",
}


def analizar_api(nombre, archivo):
    if not archivo.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {archivo}")

    df = pd.read_csv(archivo)

    columnas = {"timeStamp", "elapsed", "success"}
    faltantes = columnas - set(df.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas en {archivo.name}: {faltantes}"
        )

    df["elapsed"] = pd.to_numeric(df["elapsed"], errors="coerce")
    df["timeStamp"] = pd.to_numeric(df["timeStamp"], errors="coerce")
    df = df.dropna(subset=["elapsed", "timeStamp"])

    if df.empty:
        raise ValueError(f"No hay muestras válidas en {archivo.name}")

    exitosas = df["success"].astype(str).str.lower().eq("true")
    tiempos = df["elapsed"]
    total = len(df)

    inicio = df["timeStamp"].min()
    fin = (df["timeStamp"] + df["elapsed"]).max()
    duracion_segundos = (fin - inicio) / 1000

    rendimiento = (
        total / duracion_segundos if duracion_segundos > 0 else 0
    )

    return {
        "API": nombre,
        "Muestras": total,
        "Exitosas": int(exitosas.sum()),
        "Fallidas": int((~exitosas).sum()),
        "Errores (%)": round((~exitosas).mean() * 100, 2),
        "Promedio (ms)": round(tiempos.mean(), 2),
        "Mediana (ms)": round(tiempos.median(), 2),
        "P95 (ms)": round(tiempos.quantile(0.95), 2),
        "Mínimo (ms)": round(tiempos.min(), 2),
        "Máximo (ms)": round(tiempos.max(), 2),
        "Solicitudes/segundo": round(rendimiento, 2),
    }


def main():
    resultados = [
        analizar_api(nombre, archivo)
        for nombre, archivo in ARCHIVOS.items()
    ]

    comparacion = pd.DataFrame(resultados)

    print("\n=== COMPARACIÓN DE API REST Y GRAPHQL ===\n")
    print(comparacion.to_string(index=False))

    salida = BASE_DIR / "resultados_comparacion_api.csv"
    comparacion.to_csv(salida, index=False, encoding="utf-8-sig")

    print(f"\nArchivo comparativo guardado en:\n{salida}")

    mas_rapida = comparacion.loc[
        comparacion["Mediana (ms)"].idxmin()
    ]
    print(
        f"\nMenor mediana observada: {mas_rapida['API']} "
        f"({mas_rapida['Mediana (ms)']} ms)"
    )
    print(
        "Esta comparación es descriptiva y corresponde a las "
        "ejecuciones realizadas; no garantiza el mismo resultado "
        "bajo otras cargas."
    )


if __name__ == "__main__":
    main()
