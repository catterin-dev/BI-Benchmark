# Informe de resultados: benchmark de ingesta de datos Lambda y Kappa

## 1. Objetivo

Comparar el rendimiento de dos implementaciones simplificadas de las arquitecturas Lambda y Kappa mediante el tiempo de ingesta y el throughput, así como evaluar la consistencia de las diferencias observadas.

## 2. Diseño experimental

Se utilizaron 10.000 registros y se realizaron 30 bloques de ejecución para cada implementación. El orden de ejecución de Lambda y Kappa se aleatorizó dentro de cada bloque. Para cada ejecución se registraron el tiempo transcurrido y los registros procesados por segundo.

La implementación Lambda simplificada dividió los registros en una ruta principal del 80 % y otra incremental, y posteriormente reprocesó hasta los últimos 100 registros mediante una operación idempotente. La implementación Kappa simplificada procesó los registros por una única ruta, organizándolos en bloques de 500.

Ambas implementaciones utilizaron Python y SQLite. El tiempo medido corresponde a la ejecución de la función de procesamiento; no incluye la lectura inicial del archivo CSV ni el reinicio de la base de datos.

## 3. Resultados descriptivos

| Métrica | Lambda simplificada | Kappa simplificada |
|---|---:|---:|
| Repeticiones | 30 | 30 |
| Registros por ejecución | 10.000 | 10.000 |
| Tiempo medio (s) | 0,049349 | 0,158966 |
| Mediana del tiempo (s) | 0,043450 | 0,144713 |
| Desviación estándar (s) | 0,018322 | 0,060704 |
| Tiempo mínimo (s) | 0,033924 | 0,118768 |
| Tiempo máximo (s) | 0,111763 | 0,385195 |
| Throughput medio (registros/s) | 219.001,84 | 67.572,63 |
| Coeficiente de variación | 37,13 % | 38,19 % |

La diferencia entre los tiempos medios fue de 0,109617 segundos. La reducción descriptiva del tiempo de Lambda respecto de Kappa fue del 68,96 %. Esta cifra se calculó a partir de los promedios generales de ambas implementaciones.

## 4. Análisis emparejado e inferencia estadística

En los 30 bloques emparejados, Lambda presentó un menor tiempo de ejecución en todos los casos. La reducción porcentual media calculada por bloque fue del 68,48 %, con un intervalo bootstrap del 95 % de 66,05 % a 70,54 %.

La prueba de signos bilateral obtuvo un valor p aproximado de 1,86 × 10⁻⁹. Al compararlo con un nivel de significación de 0,05, se rechazó la hipótesis nula de igualdad de probabilidades de las direcciones de las diferencias.

Estos resultados muestran una ventaja consistente de Lambda en las condiciones evaluadas. La prueba de signos evalúa la dirección de las diferencias y no debe interpretarse por sí sola como una medida de su magnitud.

## 5. Análisis de sensibilidad

El criterio IQR identificó mediciones inusuales en ambas implementaciones. En Kappa se señalaron los bloques 18, 19 y 20; en Lambda, los bloques 4, 19 y 20.

Se compararon los resultados con todos los bloques y, de forma complementaria, sin los bloques 19 y 20. La reducción descriptiva del tiempo fue del 68,96 % con los 30 bloques y del 68,60 % con los 28 restantes.

La diferencia entre ambas estimaciones fue pequeña. Por ello, la conclusión descriptiva se mantuvo en este análisis de sensibilidad. No se eliminaron las observaciones del conjunto principal, ya que no se ha confirmado que correspondan a errores de medición.

## 6. Validación de equivalencia de datos

En una validación previa con 10.000 registros, ambas implementaciones produjeron bases de datos finales con la misma cantidad de registros. También coincidieron los valores de los campos al comparar los registros individualmente y los resúmenes agregados. Además, se verificó que el reprocesamiento de los últimos 100 eventos en Lambda no modificara el resultado final.

Esta validación respalda la equivalencia de los resultados finales para el conjunto de datos y las operaciones probadas, pero no demuestra equivalencia bajo todas las condiciones de concurrencia, fallos o procesamiento en tiempo real.

## 7. Discusión

En el experimento realizado, Lambda simplificada obtuvo menor tiempo medio de ejecución y mayor throughput que Kappa simplificada. La diferencia se mantuvo al comparar las mediciones por bloques y al realizar el análisis de sensibilidad.

Sin embargo, ambas implementaciones tienen procedimientos operativos diferentes. Lambda utiliza tres llamadas de ingesta, incluida la reconciliación de eventos recientes, mientras que Kappa procesa el conjunto en bloques de 500. Por tanto, las diferencias observadas pueden depender tanto de las operaciones implementadas como de la organización de cada flujo.

La evaluación se efectuó con Python, SQLite, 10.000 registros y un entorno local. Los resultados no deben extrapolarse directamente a sistemas distribuidos, grandes volúmenes de datos, flujos concurrentes ni implementaciones completas de las arquitecturas Lambda y Kappa.

## 8. Limitaciones

1. El conjunto de datos evaluado contiene 10.000 registros.
2. Las implementaciones son prototipos simplificados.
3. Se utilizó SQLite en un entorno local.
4. No se evaluaron concurrencia, tolerancia a fallos, latencia de extremo a extremo ni consumo de memoria y CPU.
5. Se observaron tiempos inusuales cuya causa no se ha confirmado.
6. La aleatorización del orden de ejecución reduce posibles efectos de orden, pero no elimina todas las fuentes de variación del entorno.

## 9. Conclusiones

En las condiciones experimentales utilizadas, Lambda simplificada presentó un menor tiempo medio de ingesta y un mayor throughput que Kappa simplificada. La reducción descriptiva del tiempo fue del 68,96 %, mientras que el análisis emparejado estimó una reducción media por bloque del 68,48 %.

La prueba de signos mostró una diferencia consistente a favor de Lambda en los 30 bloques. Asimismo, el análisis de sensibilidad indicó que la reducción descriptiva se mantuvo al excluir temporalmente los bloques 19 y 20 para fines comparativos.

En consecuencia, los resultados respaldan una ventaja de rendimiento de la implementación Lambda evaluada en este experimento. Para fortalecer las conclusiones se recomienda ampliar el tamaño de los datos, registrar los recursos del sistema, investigar las mediciones inusuales y realizar pruebas adicionales bajo condiciones de carga y concurrencia diferentes.

## 10. Archivos de evidencia

- `results/ingest_benchmark_randomized.csv`: mediciones del experimento aleatorizado.
- `results/ingest_analysis_randomized/resumen_estadistico_randomized.csv`: estadísticas descriptivas.
- `results/ingest_analysis_randomized/comparacion_por_bloque.csv`: diferencias por bloque.
- `results/ingest_analysis_randomized/comparacion_bootstrap_randomized.csv`: estimación bootstrap.
- `results/ingest_audit/audit_by_architecture.csv`: auditoría por arquitectura.
- `results/ingest_audit/audit_by_block.csv`: auditoría por bloque.
- `results/ingest_validation/validation_report.csv`: informe de validación de equivalencia.
