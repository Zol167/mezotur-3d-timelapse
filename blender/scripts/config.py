"""Közös beállítások: útvonalak, magasságok, szélességek, színek."""
from pathlib import Path

# A repó gyökere (blender/scripts/config.py -> két szinttel feljebb)
ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "export"
MAIN_BLEND = ROOT / "blender" / "mezotur.blend"   # a fő munkafájl
GENERATED_COLLECTION = "Generalt"                   # csak ezt írja felül a szkript

# A QGIS-ből exportált GeoJSON-ok (EOV, EPSG:23700)
FILES = {
    "terulet": EXPORT_DIR / "vizsgalati_terulet.geojson",
    "epuletek": EXPORT_DIR / "overture_epuletek.geojson",
    "kezi_epuletek": EXPORT_DIR / "kezi_epuletek.geojson",     # opcionális, kézzel rajzolt
    "magassag_zonak": EXPORT_DIR / "magassag_zonak.geojson",   # opcionális, kézi felülírás
    "vizfeluletek": EXPORT_DIR / "osm_vizfeluletek.geojson",
    "vizfolyasok": EXPORT_DIR / "osm_vizfolyasok.geojson",
    "utak": EXPORT_DIR / "osm_utak.geojson",
    "vasut": EXPORT_DIR / "osm_vasut.geojson",
}

# ---------------------------------------------------------------- épületek
MIN_AREA = 4.0            # m² – ennél kisebb poligonokat kihagyjuk
FLOOR_HEIGHT = 3.2        # m / emelet
HEIGHT_VARIATION = 0.12   # ±12% véletlen (de futásonként azonos) eltérés

# Épülettípus (OSM building / Overture class) -> magasság méterben.
# None = alapterület alapján becsüljük.
CLASS_HEIGHTS = {
    "shed": 2.4, "carport": 2.4, "hut": 2.5, "garage": 2.6, "garages": 2.6,
    "roof": 3.0, "greenhouse": 3.0, "service": 3.0, "kiosk": 3.0,
    "house": 4.5, "detached": 4.5, "semidetached_house": 4.5, "bungalow": 4.0,
    "terrace": 5.0, "farm": 4.5, "kindergarten": 4.5,
    "apartments": 12.0, "dormitory": 10.0,
    "retail": 5.0, "commercial": 6.5, "supermarket": 6.0, "office": 9.0,
    "school": 8.0, "college": 9.0, "university": 10.0, "public": 8.0,
    "civic": 8.0, "government": 9.0, "hospital": 10.0, "train_station": 7.0,
    "church": 14.0, "chapel": 7.0, "synagogue": 10.0, "religious": 10.0,
    "industrial": 8.0, "warehouse": 8.0, "factory": 9.0, "manufacture": 9.0,
    "barn": 6.0, "farm_auxiliary": 5.0, "stable": 5.0, "cowshed": 5.0,
    "sty": 3.0, "silo": 15.0, "storage_tank": 8.0,
    "transformer_tower": 6.0, "water_tower": 22.0,
}

# Alapterület (m²) -> magasság, ha a típus ismeretlen ("yes" vagy üres)
AREA_HEIGHTS = [      # (alapterület felső határa, magasság)
    (20, 2.5),        # fészer, ól
    (45, 3.2),        # garázs, nyári konyha
    (300, 4.5),       # családi ház
    (900, 6.5),       # nagyobb ház, üzlet, kisüzem
    (float("inf"), 8.0),  # csarnok, gyár
]

# ---------------------------------------------------------------- vonalas elemek
# Út szélessége (m) highway típus szerint. Ami nincs itt, azt kihagyjuk.
ROAD_WIDTHS = {
    "motorway": 12.0, "trunk": 10.0, "primary": 9.0, "secondary": 8.0,
    "tertiary": 7.0, "motorway_link": 6.0, "trunk_link": 6.0,
    "primary_link": 6.0, "secondary_link": 6.0, "tertiary_link": 6.0,
    "residential": 5.5, "unclassified": 5.0, "living_street": 5.0,
    "pedestrian": 4.0, "service": 3.5, "track": 3.0,
}
UNPAVED_SURFACES = {
    "unpaved", "dirt", "ground", "earth", "gravel", "fine_gravel",
    "compacted", "grass", "sand", "mud",
}
RAIL_WIDTHS = {"rail": 3.0, "narrow_gauge": 2.0}     # csak a működő vonalak
WATERWAY_WIDTHS = {"river": 15.0, "canal": 8.0, "stream": 3.0, "drain": 2.0, "ditch": 1.5}

# ---------------------------------------------------------------- rétegmagasságok
# Elég nagy különbségek, hogy messziről se villódzzanak egymáson.
Z_GROUND = 0.0
Z_WATERWAY = 0.15
Z_WATER = 0.20
Z_ROAD_DIRT = 0.30
Z_ROAD = 0.40
Z_RAIL = 0.50

# ---------------------------------------------------------------- színek (RGBA, lineáris)
COLORS = {
    "talaj": (0.32, 0.36, 0.22, 1.0),
    "epulet": (0.85, 0.82, 0.76, 1.0),
    "viz": (0.12, 0.28, 0.42, 1.0),
    "ut": (0.30, 0.30, 0.30, 1.0),
    "foldut": (0.45, 0.36, 0.25, 1.0),
    "vasut": (0.22, 0.18, 0.15, 1.0),
}
