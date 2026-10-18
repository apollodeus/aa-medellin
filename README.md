# AA Medellín

Directorio de grupos de Alcohólicos Anónimos en Medellín, con mapa y filtros.
Sitio: https://www.aamedellinmap.org (español) · https://www.aamedellinmap.org/en/ (English)

`template.html` es la única plantilla; `scripts/render.py` genera `index.html`, `en/index.html`, `sitemap.xml`, `robots.txt` y `llms.txt`. No edites esos archivos generados a mano.

## Google Maps

Pega tu clave de Google Maps JavaScript API en `site.json` (`"google_maps_key"`). Sin clave, el mapa usa OpenFreeMap. Restringe la clave a `www.aamedellinmap.org/*` y `aamedellinmap.org/*`.

## Cómo se actualiza

`scripts/build.py` genera `data.json` a partir de:

- **aacolombia.org** (API pública de WordPress): grupos con municipio MEDELLÍN.
- **aamedellin.org/meetings**: English-speaking meetings (parsed from the page text).
- **manual.json**: meetings you add by hand.

Una GitHub Action (`.github/workflows/update.yml`) lo corre todos los días a las 04:17 (hora de Colombia) y hace commit de `data.json` si cambió. Si una fuente falla o devuelve pocos resultados, se conserva la versión anterior de esa fuente.

Para forzar una actualización: pestaña **Actions → Update directory → Run workflow**.

## Agregar una reunión a mano

Edita `manual.json` (el primer registro es un ejemplo con `"hidden": true`; déjalo o bórralo). Campos:

```json
{
 "name": "Nombre del grupo",
 "lang": "en",                 // "en" o "es"
 "days": ["L", "Mc"],          // L M Mc J V S D
 "times": ["7:00 pm"],
 "type": "open",               // "open", "closed" o ""
 "format": "in-person",        // "in-person", "hybrid" u "online"
 "place": "Nombre del lugar",
 "address": "Carrera 00 #00-00, Barrio",
 "notes": ["Indicaciones para encontrar la sala"],
 "contact": "Nombre +57 300 000 0000",
 "zoom": "",
 "lat": 6.2096, "lng": -75.5681
}
```

Si dejas `lat`/`lng` en `null`, el build intenta ubicarlo con `venues.json` (lista de lugares conocidos por palabras clave de la dirección). Al hacer push de `manual.json` o `venues.json` el sitio se reconstruye solo.

## Correr localmente

```
python3 scripts/build.py
python3 -m http.server 8000   # abre http://localhost:8000 y http://localhost:8000/en/
```
