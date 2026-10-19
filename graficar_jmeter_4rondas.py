import csv
import os
import matplotlib.pyplot as plt

archivos = {
    "REST": [
        "resultados_rest.jtl",
        "resultados_rest_ronda2.jtl",
        "resultados_rest_ronda3.jtl",
        "resultados_rest_ronda4.jtl",
    ],
    "GraphQL": [
        "resultados_graphql.jtl",
        "resultados_graphql_ronda2.jtl",
        "resultados_graphql_ronda3.jtl",
        "resultados_graphql_ronda4.jtl",
    ],
}

medias = {}

for api, rutas in archivos.items():
    medias[api] = []
    for ruta in rutas:
        with open(ruta, newline="", encoding="utf-8-sig") as archivo:
            filas = list(csv.DictReader(archivo))
        tiempos = [
            float(fila["elapsed"])
            for fila in filas
            if fila.get("elapsed", "").strip()
        ]
        if not tiempos:
            raise ValueError(f"No hay tiempos válidos en {ruta}")
        medias[api].append(sum(tiempos) / len(tiempos))

os.makedirs("graficas_api", exist_ok=True)
salida = os.path.join(
    "graficas_api", "comparacion_latencia_jmeter_4rondas.png"
)

if os.path.exists(salida):
    raise FileExistsError(
        f"La gráfica ya existe y no se sobrescribirá: {salida}"
    )

rondas = [1, 2, 3, 4]
plt.figure(figsize=(9, 5.5))
plt.plot(rondas, medias["REST"], marker="o", linewidth=2,
         label="REST")
plt.plot(rondas, medias["GraphQL"], marker="s", linewidth=2,
         label="GraphQL")
plt.xticks(rondas, ["Ronda 1", "Ronda 2", "Ronda 3", "Ronda 4"])
plt.xlabel("Ronda de prueba")
plt.ylabel("Latencia media (ms)")
plt.title("Comparación de latencia por ronda — Apache JMeter")
plt.grid(True, axis="y", alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(salida, dpi=300, bbox_inches="tight")
plt.close()

print("Gráfica creada:", salida)
for api, valores in medias.items():
    print(
        f"{api}: " +
        ", ".join(f"Ronda {i+1} = {v:.2f} ms"
                  for i, v in enumerate(valores))
    )
