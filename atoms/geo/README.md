# Bundled region sets for `choropleth_map`

Three sets, no custom GeoJSON (the atom takes ids and numbers only). Names and borders are shown **as the sources ship them, unchanged**.

| File | Set | Source | Resolution |
| --- | --- | --- | --- |
| `world-countries.json` | `world-countries` (176 regions, Antarctica left out) | [Natural Earth](https://www.naturalearthdata.com/) `admin_0_countries`, public domain, via the npm package `world-atlas@2` file `countries-110m.json` | 1:110m, further simplified (Douglas-Peucker 0.06 degrees, vertices on a 0.01 degree grid, rings under 0.01 square degrees dropped) |
| `us-states.json` | `us-states` (50 states and DC; territories left out) | US Census Bureau cartographic boundaries, public domain, via the npm package `us-atlas@3` file `states-10m.json` | 1:10m, simplified (0.05 degrees, same grid) |
| `europe-countries.json` | `europe-countries` | the ids of `world-countries` that lie in Europe (a filter, no geometry) | |

Licence of the packages: `world-atlas` and `us-atlas` are ISC (Mike Bostock); Natural Earth and the Census data are public domain. See `THIRD-PARTY-NOTICES.md`.

Ids: ISO 3166-1 alpha-3 for countries (Kosovo `XKX`, Northern Cyprus `CYN` and Somaliland `SOL` are the user-assigned codes Natural Earth does not number), 2-letter USPS codes for states.

Format: `{set, source, regions: [{id, name, p}]}` where `p` is a list of polygons, a polygon a list of rings, a ring a flat list of integers in hundredths of a degree: the first lon, lat pair absolute, every later pair the difference from the one before (`"enc": "d100"`; the loaders decode to the floats the files held before, `x / 100`).

Regenerate with `scripts/build_choropleth_geo.mjs` (needs the three npm packages in a scratch directory, never in the repo). The Apps Script twins embed the same data through `scripts/emit_choropleth_gas_data.py`.
