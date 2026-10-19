from pathlib import Path
import re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
CARPETA = BASE / "graficas_api"
CARPETA.mkdir(exist_ok=True)

ARCHIVO_RONDAS = BASE / "resultados_api_por_ronda.csv"
ARCHIVO_TOTAL = BASE / "resultados_api_consolidado.csv"

COLORES = {
    "REST": "#8B5CF6",
    "GraphQL": "#F59E0B"
}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "text.color": "#222222",
    "axes.labelcolor": "#333333",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "axes.edgecolor": "#CCCCCC",
    "font.size": 10
})

def guardar(fig, nombre):
    ruta = CARPETA / nombre
    fig.savefig(ruta, dpi=300, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"Grafica guardada: {ruta}")

def columna(df, posibles):
    normalizadas = {
        str(c).strip().lower().replace(" ", "").replace("_", ""): c
        for c in df.columns
    }
    for posible in posibles:
        clave = posible.lower().replace(" ", "").replace("_", "")
        if clave in normalizadas:
            return normalizadas[clave]
    raise ValueError(
        f"No se encontro una columna entre {posibles}. "
        f"Columnas disponibles: {list(df.columns)}"
    )

# ---------------- GRAFICA 03 ----------------
rondas = pd.read_csv(ARCHIVO_RONDAS)
print("Columnas del CSV por ronda:", list(rondas.columns))

col_api = columna(rondas, ["API"])
col_ronda = columna(rondas, ["Ronda"])
col_req = columna(rondas, [
    "Solicitudes_segundo",
    "Solicitudes por segundo",
    "Req_s",
    "Req/s",
    "Throughput"
])

rondas[col_req] = pd.to_numeric(rondas[col_req], errors="coerce")
rondas = rondas.dropna(subset=[col_req]).copy()

def numero_ronda(valor):
    encontrado = re.search(r"(\d+)", str(valor))
    return int(encontrado.group(1)) if encontrado else 999

rondas["_orden"] = rondas[col_ronda].apply(numero_ronda)
rondas = rondas.sort_values("_orden")

fig, ax = plt.subplots(figsize=(10, 6))

for api in ["REST", "GraphQL"]:
    datos = rondas[
        rondas[col_api].astype(str).str.strip().str.lower()
        == api.lower()
    ].sort_values("_orden")

    if not datos.empty:
        ax.plot(
            datos[col_ronda].astype(str),
            datos[col_req],
            marker="o",
            markersize=7,
            linewidth=2.5,
            color=COLORES[api],
            label=api
        )
        for x, y in zip(datos[col_ronda].astype(str), datos[col_req]):
            ax.annotate(
                f"{y:.2f}",
                (x, y),
                textcoords="offset points",
                xytext=(0, 9),
                ha="center",
                fontsize=8
            )

ax.set_title(
    "Rendimiento por ronda: REST vs GraphQL",
    fontsize=14,
    fontweight="bold",
    pad=15
)
ax.set_xlabel("Ronda de prueba")
ax.set_ylabel("Solicitudes por segundo")
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.legend(frameon=False)
fig.tight_layout()
guardar(fig, "03_rendimiento_por_ronda.png")

# ---------------- GRAFICA 04 ----------------
total = pd.read_csv(ARCHIVO_TOTAL)
print("Columnas del CSV consolidado:", list(total.columns))

col_api_t = columna(total, ["API"])
col_error = columna(total, [
    "Errores_pct",
    "Porcentaje_errores",
    "Error_pct",
    "Error_percent"
])

total[col_error] = pd.to_numeric(total[col_error], errors="coerce")
total = total.dropna(subset=[col_error]).copy()
total[col_api_t] = total[col_api_t].astype(str).str.strip()

total = total[
    total[col_api_t].str.lower().isin(["rest", "graphql"])
].copy()

total = total.set_index(
    total[col_api_t].str.lower()
).reindex(["rest", "graphql"]).reset_index(drop=True)

nombres = ["REST", "GraphQL"]
valores = total[col_error].tolist()
colores = [COLORES[n] for n in nombres]

fig, ax = plt.subplots(figsize=(8, 6))
barras = ax.bar(
    nombres,
    valores,
    color=colores,
    width=0.55,
    edgecolor="white"
)

max_error = max(valores) if valores else 0
ax.set_ylim(0, max(1.0, max_error * 1.4 + 0.1))

for barra, valor in zip(barras, valores):
    # La etiqueta queda visible incluso cuando el valor es cero.
    ax.annotate(
        f"{valor:.2f}%",
        xy=(barra.get_x() + barra.get_width() / 2, valor),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color="#333333"
    )

ax.set_title(
    "Porcentaje de errores por API",
    fontsize=14,
    fontweight="bold",
    pad=15
)
ax.set_ylabel("Solicitudes fallidas (%)")
ax.set_xlabel("API evaluada")
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)
fig.tight_layout()
guardar(fig, "04_porcentaje_errores.png")

print("\nProceso terminado. Se regeneraron las graficas 03 y 04.")
