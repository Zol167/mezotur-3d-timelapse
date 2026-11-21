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

# A magasság mostantól a FALMAGASSÁG (eresz), a ferde tető erre jön rá.
# Épülettípus (OSM building / Overture class) -> falmagasság méterben.
CLASS_HEIGHTS = {
    "shed": 2.2, "carport": 2.2, "hut": 2.3, "garage": 2.4, "garages": 2.4,
    "roof": 3.0, "greenhouse": 2.5, "service": 2.6, "kiosk": 2.8,
    "house": 3.2, "detached": 3.2, "semidetached_house": 3.2, "bungalow": 3.0,
    "terrace": 3.5, "farm": 3.2, "kindergarten": 3.5,
    "apartments": 12.0, "dormitory": 10.0,
    "retail": 4.5, "commercial": 6.0, "supermarket": 6.0, "office": 9.0,
    "school": 8.0, "college": 9.0, "university": 10.0, "public": 8.0,
    "civic": 8.0, "government": 9.0, "hospital": 10.0, "train_station": 6.0,
    "church": 14.0, "chapel": 6.0, "synagogue": 9.0, "religious": 9.0,
    "industrial": 8.0, "warehouse": 8.0, "factory": 9.0, "manufacture": 9.0,
    "barn": 4.5, "farm_auxiliary": 3.5, "stable": 3.5, "cowshed": 3.5,
    "sty": 2.4, "silo": 15.0, "storage_tank": 8.0,
    "transformer_tower": 6.0, "water_tower": 22.0,
}

# Ezek a típusok mindig lapos tetőt kapnak (a templomok helyére később kézi modell jön)
FLAT_ROOF_CLASSES = {
    "apartments", "dormitory", "retail", "commercial", "supermarket", "office",
    "industrial", "warehouse", "factory", "manufacture", "silo", "storage_tank",
    "church", "synagogue", "religious", "water_tower", "transformer_tower",
    "university", "college",
}

# Alapterület (m²) -> (falmagasság, tetőhajlásszög fokban; None = lapos tető)
AREA_CLASSES = [
    (20, 2.3, 25),             # fészer, ól
    (45, 2.6, 30),             # garázs, nyári konyha
    (300, 3.2, 40),            # kertes ház, kádárkocka
    (900, 4.5, 30),            # nagy ház, pajta, üzlet
    (float("inf"), 8.0, 25),   # nagy épület – a széles csarnokok a ROOF_MAX_WIDTH miatt laposak
]

# ---------------------------------------------------------------- tetők
ROOF_OVERHANG = 0.4        # m – eresz kinyúlása
ROOF_MAX_RISE = 6.0        # m – a tető legfeljebb ennyivel magasabb a falnál
ROOF_MAX_WIDTH = 22.0      # m – ennél szélesebb épület lapos tetőt kap
ROOF_MIN_RECT = 0.80       # alaprajz / befoglaló téglalap aránya – ez alatt téglalapokra bontjuk
RECTILINEAR_TOLERANCE_DEG = 12  # ennyi fokkal eltérő falakat még derékszögűnek tekintünk
SNAP_TOLERANCE = 0.8       # m – ennél közelebbi falvonalakat összevonunk a bontásnál
MAX_ROOF_PARTS = 6         # ennél több darabra eső alaprajz lapos tetőt kap
ROOF_MIN_PART_WIDTH = 2.5  # m – ennél keskenyebb szárny lapos tetőt kap
HIP_RATIO = 1.25           # hossz/szélesség ez alatt -> sátortető (kádárkocka), felette nyeregtető
HIP_PITCH_DELTA = 8        # fok – a sátortető ennyivel laposabb a nyeregtetőnél
FLAT_ZONE_HEIGHT = 10.0    # zónás épület e fölött lapos tetős (panel, lakópark)

# Színpaletták (sRGB hex). Blenderben a "Fal" és "Teto" anyag ColorRamp-jében
# később szabadon átírhatók – a szkript a meglévő anyagot nem írja felül.
WALL_PALETTE = ["#EDE6D6", "#F2E3B8", "#E6CFA3", "#EBD5CC", "#D6D3CC", "#F4F1E8", "#E9DDBF"]
ROOF_PALETTE = ["#A0522D", "#8E3B2B", "#B4653F", "#7C4A3B", "#6F6F6E", "#9B4733", "#5E5A57"]
FLAT_ROOF_COLOR = "#7B7A76"

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
    "viz": (0.12, 0.28, 0.42, 1.0),
    "ut": (0.30, 0.30, 0.30, 1.0),
    "foldut": (0.45, 0.36, 0.25, 1.0),
    "vasut": (0.22, 0.18, 0.15, 1.0),
}
