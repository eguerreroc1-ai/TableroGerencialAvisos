# Dashboard gerencial de avisos — Equipo 2

Versión visual ajustada a partir de `Dashboard_ENERGY_V2`.

## Cambios de esta versión
- La página **Inicio** reutiliza el diseño corporativo de referencia: hero azul, ficha corporativa y bloques de paleta de colores.
- La barra lateral recupera el logo ENERGY, la navegación vertical, el fondo azul oscuro y el estilo de filtros del dashboard anterior.
- Se conservan únicamente tres filtros globales: **Año**, **Tipo de aviso** y **Departamento**.
- Se incorporan nuevamente los autores mostrados en la referencia: Mauricio Guerrero y Daniel Rodriguez.
- `theme.py` y la hoja de estilos `assets/style.css` se toman de la versión de referencia para mantener una única paleta institucional.
- Las visualizaciones del nuevo dashboard utilizan los colores semánticos e institucionales definidos en `theme.py`; los indicadores de cumplimiento, atraso y pendientes mantienen colores diferenciados.

## Secciones analíticas
1. Inicio.
2. Resumen gerencial.
3. Cumplimiento y plazos.
4. Pendientes por cumplir.
5. Territorio y tipos.

## Ejecución
```bash
pip install -r requirements.txt
python app.py
```
Abrir `http://127.0.0.1:8050/`.

## Datos y alcance
- Base: `data/avisos.csv`.
- Filtro de alcance: `marca = normal`.
- Los avisos abiertos tienen fecha de corte registrada 06-may-2023; no debe interpretarse como fecha real de cierre.
- Los KPI y gráficos analíticos están en `app.py`; la página de inicio de referencia está en `home.py`; la paleta central está en `theme.py`.


## Ajustes de legibilidad — versión 1.2
- Se aumentó el tamaño de títulos, etiquetas, leyendas, ejes y cifras destacadas de las gráficas.
- Los gráficos de dona del resumen gerencial muestran etiquetas y porcentajes con mayor tamaño.
- El gráfico anual compara categorías excluyentes: avisos cerrados frente a avisos abiertos al corte, con valores visibles sobre las barras.
- Se reemplazó el término "cohorte" por una explicación directa: los avisos recibidos en un mes y los cerrados en ese mes no necesariamente son los mismos avisos.

## Ajuste puntual — versión 1.3
La gráfica «Volumen histórico y pendientes actuales por año de aviso» se rediseñó para seguir el estilo de «Comparación del volumen de avisos cerrados y abiertos por tipo»:
- barras agrupadas por año, con azul para cerrados y rojo para abiertos;
- etiquetas numéricas visibles encima de todas las barras, incluidos los valores cero;
- mayor espacio superior para evitar que las etiquetas queden cortadas;
- leyenda y ejes con la tipografía general del dashboard.

## Versión 1.4 — réplica del estilo de barras agrupadas ENERGY
La gráfica anual ahora reutiliza el patrón técnico de `make_grouped_type_status()` del dashboard ENERGY:
- construcción con `plotly.express.bar`;
- `barmode="group"` y orden fijo de estados Cerrado/Abierto;
- paleta `STATUS_COLORS` del tema original;
- barras con esquinas redondeadas (`cornerradius=7`);
- etiquetas numéricas fuera de las barras y sin recorte;
- leyenda horizontal, márgenes y separación entre barras equivalentes al gráfico de referencia;
- eje Y sin etiquetas numéricas, para conservar el estilo del gráfico original.
Se mantienen todos los años disponibles en la base y se muestran ambas categorías por año, incluso si una de ellas tiene valor cero.

## Versión 1.5 — ajustes de la sección Cumplimiento y plazos
- Se ajustó la gráfica de cumplimiento a tiempo por prioridad para utilizar la escala semántica institucional (rojo, ámbar y verde), con barras redondeadas y etiquetas de porcentaje más legibles.
- Se ajustó la gráfica de proporción de avisos cerrados atrasados por tipo a la escala semántica institucional (verde, ámbar y rojo), con barras horizontales redondeadas y etiquetas porcentuales.
- Se eliminó de esta sección la gráfica «Evolución mensual: avisos recibidos frente a avisos cerrados», que permanece en Resumen gerencial.
- La gráfica «Evolución mensual del cumplimiento de avisos cerrados» ahora ocupa el ancho completo disponible. Se aumentó su altura, grosor de línea y tamaño de marcadores; se mejoraron los ejes, la información emergente y la referencia de meta del 100%.

## Versión 1.6 — paleta y presentación de Pendientes por cumplir
- «Situación de cumplimiento de los pendientes»: se fijaron los colores semánticos de la paleta ENERGY desde `theme.py`: verde para dentro del plazo, rojo para vencido y ámbar para sin clasificación. Se amplió la lectura de las etiquetas.
- «Antigüedad de los avisos abiertos»: se sustituyó el gradiente genérico por colores de la paleta ENERGY ordenados por antigüedad (azules, ámbar, rojo y azul profundo). Se redondearon los bordes superiores de las barras y se mejoraron las etiquetas numéricas.
- «Pendientes por tipo de aviso y situación frente al plazo»: se fijó el mismo mapeo semántico verde/rojo/ámbar y el orden de las situaciones, para mantener consistencia con la gráfica de dona.

## Versión 1.7 — Territorio y tipologías
- El mapa amplía su altura y utiliza límites departamentales de Colombia como capa base; añade marcadores para las capitales departamentales y para los municipios con coordenadas en la base del proyecto.
- Los puntos municipales se dimensionan según el volumen de avisos y se colorean según el porcentaje pendiente (verde, ámbar y rojo).
- La capa GeoJSON departamental MGN 2025 se obtiene desde el repositorio público `ytolosa/mapas-colombia`, que declara derivar sus divisiones político-administrativas del Marco Geoestadístico Nacional del DANE. Se descarga al solicitar el mapa y queda en caché durante la ejecución. Si no hay conexión, el mapa conserva los puntos y capitales sobre la vista geográfica de Plotly, pero no dibuja los límites departamentales.
- La gráfica de departamentos usa rojo para pendientes y ámbar para cierres atrasados, con bordes redondeados.
- Se eliminó de esta sección «Pendientes por tipo de aviso y situación», porque la comparación por tipo ya está disponible en «Pendientes por cumplir».
- La tabla «Municipios con mayor acumulación pendiente» ahora ocupa todo el ancho disponible, con columnas distribuidas y tipografía ampliada.

Fuente cartográfica de referencia: https://github.com/ytolosa/mapas-colombia (archivos GeoJSON derivados de MGN 2025 del DANE).

## Versión 1.8 — ampliación del mapa territorial
- Se ocultó la leyenda de capas («Municipios analizados» y «Capitales departamentales») para recuperar espacio visual. Las dos capas siguen activas: los municipios continúan representados por círculos y las capitales por estrellas con sus etiquetas; sus datos se consultan al pasar el cursor.
- Se amplió la altura del mapa a 620 px y se extendió el dominio geográfico para aprovechar mejor el marco de la tarjeta.
- Se ajustó el encuadre y la escala de la proyección; se reservó únicamente el espacio lateral necesario para la escala de porcentaje pendiente.

## Versión 1.9 — mapa topográfico y altura compacta
- Se sustituyó el mapa Plotly por un mapa interactivo Leaflet/Folium embebido en la tarjeta existente; no se amplía el marco exterior.
- La vista inicial utiliza Esri World Topographic Map, que incluye relieve sombreado, rasgos fisiográficos, hidrografía, carreteras y caminos. Se incorpora OpenStreetMap como mapa base alternativo para revisar calles y caminos.
- Se conservan los límites departamentales, círculos de municipios analizados (tamaño por volumen y color por porcentaje pendiente) y estrellas de capitales departamentales.
- Se redujo la altura de la gráfica de departamentos y se fijó una altura uniforme de 460 px para las dos tarjetas de la fila; el mapa ocupa 370 px dentro de su tarjeta.
- Las capas base requieren conexión a internet. La cartografía de relieve y carreteras es contextual y no certifica transitabilidad, cierres, estado de la vía ni tiempos reales de acceso. Para análisis logístico de detalle se requiere contrastar con información vial oficial y actualizada de INVIAS/autoridades territoriales.

## Versión 1.9.1 — corrección de carga de la sección Territorio
- Se retiró el atributo `loading` del componente `html.Iframe`, para evitar que una versión de Dash que no lo soporte provoque un error de callback al construir la página.
- Se conserva el mapa Folium/Leaflet, sus capas topográficas, las vías, los municipios analizados, las capitales y la altura compacta de las tarjetas.
- Se validó la sintaxis de todos los archivos Python.

## Versión 1.10 — jerarquía visual del mapa y ranking territorial
- Capitales departamentales: se sustituyeron los iconos de estrella por un punto azul pequeño acompañado del nombre de la capital.
- Municipios analizados: se amplió la escala no lineal de los círculos según el número de avisos distintos por municipio. La escala utiliza 4 px para un aviso y puede alcanzar 18 px para los mayores volúmenes, manteniendo el color asociado al porcentaje pendiente.
- Texto de apoyo del mapa: se retiró la referencia a las estrellas.
- Departamentos con mayor concentración: se excluyeron etiquetas vacías, «Sin dato» y equivalentes; se ordenaron los departamentos por volumen combinado de pendientes y cierres atrasados, de mayor a menor.

## Versión 1.11 — tabla compacta y autores
- Se redujeron tamaño de fuente, interlineado y padding vertical de encabezados y filas de la tabla «Municipios con mayor acumulación pendiente». Se conservan las 15 filas y las cinco columnas; no se elimina información.
- Se añadieron a la barra lateral los autores Juan Bojacá (iniciales JB) y Andres Nova (iniciales AN), conservando los autores existentes.
