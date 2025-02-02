import geopandas as gpd

from src.api.kadaaster_api import get_kadaster_data
from src.api.bgt_api import get_bgt_data

from shapely.geometry import box

import warnings
warnings.filterwarnings("ignore")

def calculate_ndvi(rasterio_dataset):
        nir = rasterio_dataset[0].astype(float)
        red = rasterio_dataset[1].astype(float)
        # Calculate NDVI
        ndvi = (nir - red) / (nir + red)
        return ndvi

def get_yard_data(bounds, cutoff=0.05):
    """
    Extract the geometry of each private yard within the given bounds.

    Parameters
    ----------
    bounds : tuple
        The bounding box of the area of interest in the format (minx, miny, maxx, maxy).
    cutoff : float
        The minimum percentage of overlap between the gml and erf zones to consider it a match.
        Default is 0.05.
    
    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing the geometry of each private yard within the given bounds.
        It also includes a column to indicate which erf zone the yard belongs to.

    Notes
    -----
    The function gets Kadaster data and BGT data for the given bounds, filters the Kadaster data
    to the bounds of the erf zones, removes the geometries that touch the bounding box, and assigns 
    the erf zone to each Kadaster geometry based on overlap. It also filters out geomtries
    with an overlap percentage below the cutoff to discard small artifacts.
    """
    bbox_polygon = box(*bounds)
    gml_kadaster = get_kadaster_data(bounds)
    erf_zones = get_bgt_data(bounds)
    assert erf_zones.crs == gml_kadaster.crs
    # filter the gml data to the bounds of the erf zones
    gml_kadaster = gml_kadaster.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
    on_bbox_edge = gml_kadaster.geometry.intersects(bbox_polygon.exterior)
    gml_kadaster = gml_kadaster[~on_bbox_edge]  # Keep only geometries NOT touching the bounding box

    gml_kadaster["geometry_area"] = gml_kadaster.geometry.area
    intersections = gpd.overlay(gml_kadaster, erf_zones, how="intersection")
    intersections["overlap_area"] = intersections.geometry.area
    intersections["overlap_percentage"] = intersections["overlap_area"] / intersections["geometry_area"]

    processed_gml = intersections.sort_values(by="overlap_area", ascending=False) \
                                .drop_duplicates(subset="gml_id").dropna(subset=['id'])
    processed_gml = processed_gml[processed_gml["overlap_percentage"] > cutoff]
    return processed_gml