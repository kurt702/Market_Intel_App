import pandas as pd


def normalize_zip(zip_code):
    """
    Standardize ZIP codes to 5-digit strings.
    """

    try:
        zip_code = str(zip_code).strip()

        if "." in zip_code:
            zip_code = zip_code.split(".")[0]

        if "-" in zip_code:
            zip_code = zip_code.split("-")[0]

        zip_code = zip_code.zfill(5)

        if len(zip_code) != 5:
            return None

        return zip_code

    except Exception:
        return None
def prepare_choropleth_dataframe(heatmap_results,geojson_zip_features=None):
    """
    Converts heatmap intelligence dataframe
    into choropleth-ready structure.

    This engine:
    - normalizes ZIPs
    - validates geometry compatibility
    - prepares choropleth dataframe
    - scores intensity
    """

    if (
        heatmap_results is None
        or not heatmap_results.get("success")
    ):
        return {
            "success": False,
            "error": "Invalid heatmap results."
        }

    map_df = (
        heatmap_results["map_df"]
        .copy()
    )

    if map_df.empty:
        return {
            "success": False,
            "error": "Heatmap dataframe is empty."
        }

    map_df["ZIP"] = (
        map_df["ZIP"]
        .apply(normalize_zip)
    )

    map_df = map_df.dropna(
        subset=["ZIP"]
    )

    if map_df.empty:
        return {
            "success": False,
            "error": "No valid ZIP codes available after normalization."
        }

    # =========================
    # INTENSITY SCORING
    # =========================

    intensity_score_map = {
        "Very High": 4,
        "High": 3,
        "Moderate": 2,
        "Low": 1,
    }

    map_df["Intensity Score"] = (
        map_df["Intensity"]
        .map(intensity_score_map)
        .fillna(1)
    )

    # =========================
    # GEOGRAPHIC FEATURE CHECK
    # =========================

    matched_zips = []

    unmatched_zips = []

    if geojson_zip_features:

        geojson_zips = set()

        for feature in geojson_zip_features:

            try:
                geo_zip = (
                    feature["properties"]
                    .get("ZCTA5CE10")
                )

                geo_zip = normalize_zip(
                    geo_zip
                )

                if geo_zip:
                    geojson_zips.add(
                        geo_zip
                    )

            except Exception:
                pass

        for zip_code in map_df["ZIP"]:

            if zip_code in geojson_zips:
                matched_zips.append(
                    zip_code
                )

            else:
                unmatched_zips.append(
                    zip_code
                )

    # =========================
    # GEOGRAPHIC SUMMARY
    # =========================

    geography_summary = {
        "total_zip_rows": len(map_df),
        "matched_zips": len(matched_zips),
        "unmatched_zips": len(unmatched_zips),
        "match_rate": (
            len(matched_zips)
            / len(map_df)
            * 100
            if len(map_df)
            else 0
        ),
    }

    return {
        "success": True,
        "choropleth_df": map_df,
        "matched_zips": matched_zips,
        "unmatched_zips": unmatched_zips,
        "geography_summary": geography_summary,
    }
def filter_geojson_to_active_zips(
    geojson_data,
    choropleth_df,
):
    """
    Reduces nationwide GeoJSON
    to only active ZIP polygons.

    MASSIVE performance improvement.
    """

    if (
        geojson_data is None
        or "features" not in geojson_data
    ):
        return geojson_data

    active_zips = set(
        choropleth_df["ZIP"]
        .astype(str)
        .tolist()
    )

    filtered_features = []

    for feature in geojson_data["features"]:

        try:
            feature_zip = (
                feature["properties"]
                .get("ZCTA5CE10")
            )

            if feature_zip in active_zips:
                filtered_features.append(
                    feature
                )

        except Exception:
            pass

    filtered_geojson = {
        "type": "FeatureCollection",
        "features": filtered_features,
    }

    return filtered_geojson
def calculate_geographic_viewport(
    choropleth_df,
    geojson_features,
):
    """
    Calculates dynamic map viewport
    from active ZIP polygons.

    Returns:
    - center latitude
    - center longitude
    - approximate zoom scale
    """

    if choropleth_df is None or choropleth_df.empty:
        return {
            "lat": 39.5,
            "lon": -98.35,
            "zoom": 3,
        }

    active_zips = set(
        choropleth_df["ZIP"]
        .astype(str)
        .tolist()
    )

    matched_coordinates = []

    for feature in geojson_features:

        try:
            feature_zip = (
                feature["properties"]
                .get("ZCTA5CE10")
            )

            if feature_zip not in active_zips:
                continue

            geometry = feature.get("geometry")

            if geometry is None:
                continue

            coords = geometry.get("coordinates")

            if not coords:
                continue

            geometry_type = geometry.get("type")

            if geometry_type == "Polygon":

                for polygon in coords:

                    for lon, lat in polygon:
                        matched_coordinates.append(
                            (lat, lon)
                        )

            elif geometry_type == "MultiPolygon":

                for multipolygon in coords:

                    for polygon in multipolygon:

                        for lon, lat in polygon:
                            matched_coordinates.append(
                                (lat, lon)
                            )

        except Exception:
            pass

    if not matched_coordinates:

        return {
            "lat": 39.5,
            "lon": -98.35,
            "zoom": 3,
        }

    lats = [
        c[0]
        for c in matched_coordinates
    ]

    lons = [
        c[1]
        for c in matched_coordinates
    ]

    min_lat = min(lats)
    max_lat = max(lats)

    min_lon = min(lons)
    max_lon = max(lons)

    center_lat = (
        min_lat + max_lat
    ) / 2

    center_lon = (
        min_lon + max_lon
    ) / 2

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon

    max_span = max(
        lat_span,
        lon_span
    )

    # crude zoom approximation
    if max_span < 0.5:
        zoom = 10

    elif max_span < 1:
        zoom = 8

    elif max_span < 2:
        zoom = 7

    elif max_span < 4:
        zoom = 6

    elif max_span < 8:
        zoom = 5

    elif max_span < 15:
        zoom = 4

    else:
        zoom = 3

    return {
        "lat": center_lat,
        "lon": center_lon,
        "zoom": zoom,
    }