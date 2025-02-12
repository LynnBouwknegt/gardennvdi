import geopandas as gpd

from src.api.kadaaster_api import get_kadaster_data
from src.api.bgt_api import get_bgt_data, get_bgt_download_link, download_and_unzip_file, find_gml_file
from rasterio.mask import mask
import pandas as pd
import numpy as np

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

    # get BGT data
    download_link = get_bgt_download_link(bounds)
    extract_path = download_and_unzip_file(download_link, output_zip="bgt_data.zip", extract_dir="bgt_data")
    gml_file = find_gml_file(extract_path)
    erf_zones = gpd.read_file(gml_file)
    erf_zones = erf_zones.rename(columns={'gml_id': 'id'})

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

def process_image(processed_yard_data, aeriel_cir, aeriel_rgb=None):
    """
    Calculate the NDVI and its mean for the aeriel images.
    Make sure that the bounds of the processed_yard_data are the same bounds as of the aeriel images.    

    Parameters
    ----------
    processed_yard_data : geopandas.GeoDataFrame
        The processed yard data with the geometry of the erf zones.
        Obtained from the get_yard_data function.
    aeriel_rgb : rasterio.io.DatasetReader
        The aeriel image in RGB format.
    aeriel_cir : rasterio.io.DatasetReader  
        The aeriel image in CIR format.
    
    Returns
    -------
    df : pandas.DataFrame
        A DataFrame with the yards NDVI and its mean for each erf zone.

    """
        # Create a list to store results
    plot_dict = {}
    transform = aeriel_cir.transform
    resolution_x, resolution_y = transform[0], -transform[4]
    pixel_area = resolution_x * resolution_y

    # Iterate over each erf zone
    for _, row in processed_yard_data.iterrows():
        erf_id = row['id']
        plot_id = row['gml_id']
        zone_geometry = [row['geometry']]
        try:
            mask_image_cir, out_transform_cir = mask(aeriel_cir, zone_geometry, crop=True, filled=False)
            if aeriel_rgb is not None:
                mask_image_rgb, _ = mask(aeriel_rgb, zone_geometry, crop=True, filled=False)
                plot_dict[plot_id] = {
                    'erf_id': erf_id,
                    "clipped_cir": mask_image_cir,
                    "clipped_rgb": mask_image_rgb,
                    "affine_transform": out_transform_cir,
                    "area" : np.ma.count(mask_image_cir[0]) * pixel_area
                }
            # Store results (zone_id and clipped raster)
            else:
                plot_dict[plot_id] = {
                    'erf_id': erf_id,
                    "clipped_cir": mask_image_cir,
                    "affine_transform": out_transform_cir,
                    "area" : np.ma.count(mask_image_cir[0]) * pixel_area
                }
        except ValueError:
            pass

    df = pd.DataFrame(plot_dict).T
    # apply the NDVI to df 
    df['ndvi'] = df.apply(lambda x: calculate_ndvi(x['clipped_cir']), axis=1)

    # Calculate the ndvi mean over unmasked pixels
    df['ndvi_mean'] = df['ndvi'].apply(lambda x: np.ma.mean(x))

    return df