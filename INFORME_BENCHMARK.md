# Informe de benchmark: arquitecturas de ingesta y API para Business Intelligence

**Autora:** Catterine Carely Quispe Quispe  
**Curso:** Business Intelligence — Maestría en Ingeniería Estadística e Informática  
**Fecha de ejecución:** [completar]  
**Equipo de prueba:** [sistema operativo, CPU, RAM, versión de Python]

## 1. Objetivo y metodología

El objetivo es comparar dos patrones de ingesta analítica (Lambda y Kappa) y dos estilos de API (REST y GraphQL) mediante un prototipo reproducible en Python. Se generan eventos sintéticos con identificador, fecha, categoría, sede y monto, almacenados en SQLite. Para la ingesta, Lambda separa una carga por lote (batch) y una actualización incremental (speed), conciliadas mediante una clave única; Kappa recorre el conjunto con una única ruta de procesamiento por bloques. Se mide tiempo de ejecución y registros procesados por segundo en cinco corridas por arquitectura. Para las API, FastAPI expone REST y Strawberry GraphQL expone la misma agregación desde la misma base de datos. Se envían 300 solicitudes por API después de una petición de calentamiento. Se registran latencia media, mediana, p95, throughput y tasa de error.

## 2. Resultados experimentales

Completar con los CSV generados por el código. **No presentar valores no medidos como resultados reales.**

| Ingesta | Lambda | Kappa |
|---|---:|---:|
| Mediana de tiempo (s) | [dato] | [dato] |
| Mediana de registros/s | [dato] | [dato] |

| API | Latencia mediana (ms) | p95 (ms) | Solicitudes correctas/s | Errores (%) |
|---|---:|---:|---:|---:|
| REST | [dato] | [dato] | [dato] | [dato] |
| GraphQL | [dato] | [dato] | [dato] | [dato] |

Interpretación: la arquitectura con mayor tasa de registros por segundo procesa más eventos por unidad de tiempo bajo esta configuración. En las API, una menor latencia mediana y p95 indica respuestas más rápidas, mientras que mayor throughput indica más solicitudes correctas atendidas por segundo. La elección no debe basarse en una sola métrica: también se consideran complejidad, flexibilidad de consulta, consistencia y consumo de recursos. Si existe alta variación entre corridas, deben repetirse las pruebas y reportar la dispersión.

## 3. Discusión y conclusión

Lambda mantiene rutas separadas para procesamiento por lotes y datos recientes, lo que puede facilitar la combinación de recomputación histórica con baja latencia, pero implica mayor complejidad y reconciliación. Kappa simplifica el diseño al tratar los datos como un flujo reproducible, aunque el reprocesamiento histórico depende de la retención y reproducción de eventos. Baresi et al. (2018) evaluaron Lambda y Kappa con una carga de análisis de redes sociales; su trabajo subraya que el resultado depende del volumen, la configuración y el problema evaluado.

REST ofrece recursos y operaciones HTTP explícitas; GraphQL permite solicitar campos específicos desde un único endpoint. La literatura muestra que el rendimiento relativo depende de las consultas, la carga, el modelo de datos y la implementación; por tanto, no existe un ganador universal. Este experimento solo permite concluir cuál fue más eficiente en el prototipo, el equipo y la consulta definidos.

**Limitaciones:** el prototipo no usa un broker distribuido ni un clúster real; SQLite, ejecución local y carga secuencial limitan la validez externa. La simulación Lambda/Kappa sirve para comprender y comparar patrones, pero no equivale a una implementación industrial con Kafka, Spark o Flink. Como trabajo futuro se propone repetir con PostgreSQL, Kafka y un motor de procesamiento de flujo, y ejecutar pruebas concurrentes con Locust o k6.

## Referencias

Baresi, L., Garriga, M., & De Renzis, A. (2018). *Benchmarking big data architectures for social networks data processing using public cloud platforms*. Future Generation Computer Systems, 89, 98–109. https://doi.org/10.1016/j.future.2018.05.068

Kemer, E., & Samli, R. (2019). *Performance comparison of scalable REST application programming interfaces in different platforms*. Computer Standards & Interfaces, 66, 103355. https://doi.org/10.1016/j.csi.2019.05.001

Lawi, A., Panggabean, B. L. E., & Yoshida, T. (2021). *Evaluating GraphQL and REST API services performance in a massive and intensive accessible information system*. Computers, 10(11), 138. https://doi.org/10.3390/computers10110138

**Nota de verificación:** las páginas editoriales y DOI son consultables. Confirma la indexación específica en Scopus Sources antes de declarar formalmente que cada artículo está indexado. Las dos primeras referencias están en ScienceDirect; la tercera se publica en MDPI, no en ScienceDirect.
