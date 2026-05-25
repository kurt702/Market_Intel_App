import geopandas as gpd
from pathlib import Path


zip_path = Path("maps/us_zcta_500k.zip")
output_path = Path("maps/zip_boundaries.geojson")

print("Loading ZCTA shapefile...")

gdf = gpd.read_file(zip_path)

print(f"Loaded {len(gdf):,} ZIP polygons")

# Keep only fields needed for Plotly choropleths
keep_cols = [
    "ZCTA5CE20",
    "GEOID20",
    "NAME20",
    "geometry",
]

existing_cols = [
    c for c in keep_cols
    if c in gdf.columns
]

gdf = gdf[existing_cols]

# Standardize property key expected by renderer
if "ZCTA5CE20" in gdf.columns:
    gdf["ZCTA5CE10"] = gdf["ZCTA5CE20"]

elif "GEOID20" in gdf.columns:
    gdf["ZCTA5CE10"] = gdf["GEOID20"]

# Ensure geographic CRS
gdf = gdf.to_crs("EPSG:4326")

print("Converting to GeoJSON...")

gdf.to_file(
    output_path,
    driver="GeoJSON"
)

print(f"Saved: {output_path}")
print(f"Features written: {len(gdf):,}")