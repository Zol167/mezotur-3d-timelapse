#!/usr/bin/env bash
# QGIS-rétegek exportálása GeoJSON-ba (EOV) a Blender számára.
# Futtatás a repó gyökeréből vagy bárhonnan: ./tools/export_geojson.sh
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/export

export_layer() {  # $1 = forrás .gpkg, $2 = kimenet neve, $3 = rétegnév a fájlon belül (opcionális)
  local src="$1" out="$2" layer="${3:-}"
  if [[ ! -f "$src" ]]; then
    echo "– $out: nincs $src, kihagyva"; return
  fi
  if [[ -n "$layer" ]] && ! ogrinfo -q -so "$src" "$layer" >/dev/null 2>&1; then
    echo "– $out: nincs '$layer' réteg a $src fájlban, kihagyva"; return
  fi
  rm -f "data/export/$out.geojson"
  if ogr2ogr -f GeoJSON -t_srs EPSG:23700 -lco COORDINATE_PRECISION=2 \
       "data/export/$out.geojson" "$src" $layer 2>/dev/null; then
    echo "✓ $out"
  else
    echo "✗ $out: hiba az exportnál"
  fi
}

# Letöltött adatok – fájlonként egy réteg
for name in overture_epuletek osm_utak osm_vizfolyasok osm_vizfeluletek \
            osm_teruletek osm_vasut osm_vasut_unused; do
  export_layer "qgis/$name.gpkg" "$name"
done

# Kézzel rajzolt rétegek a mezotur.gpkg-ből
for layer in vizsgalati_terulet magassag_zonak kezi_epuletek beepites_foltok; do
  export_layer qgis/mezotur.gpkg "$layer" "$layer"
done
