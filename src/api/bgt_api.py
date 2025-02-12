import time
import os
import zipfile
import requests

import geopandas as gpd
import pandas as pd

def get_bgt_data(bounds):
    # query BGT API for the cartographic data
    url = f'https://api.pdok.nl/lv/bgt/ogc/v1/collections/onbegroeidterreindeel/items?crs=http%3A%2F%2Fwww.opengis.net%2Fdef%2Fcrs%2FEPSG%2F0%2F28992&bbox-crs=http%3A%2F%2Fwww.opengis.net%2Fdef%2Fcrs%2FEPSG%2F0%2F28992&bbox={bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}&f=jsonfg&limit=1000&datetime=2023-01-01T00%3A00%3A00Z'

    response = requests.get(url)
    data = response.json()

    def get_next(data):
        links = data['links']
        link_current, link_next = None, None
        for link in links:
            if link['rel'] == 'next':
                link_next = link['href']
            if link['rel'] == 'self':
                link_current = link['href']

        try:
            link_next = link_next.replace('html', 'jsonfg')
        except AttributeError:
            pass
            
        return link_current, link_next


    current_page, next_page = get_next(data)

    while current_page != next_page:
        if current_page is None or next_page is None:
            break
        
        current_page = next_page
        response = requests.get(current_page)
        data_i = response.json()
        current_page, next_page = get_next(data_i)
        data['features'].extend(data_i['features'])
        data['numberReturned'] += data_i['numberReturned']

    # clean up and load data into geopandas
    for feature in data['features']:
        feature.pop('geometry')
        feature['geometry'] = feature['place']
        feature.pop('place')

    gdf = gpd.GeoDataFrame.from_features(data, crs=data['coordRefSys'])
    gdf = gdf.assign(id=pd.json_normalize(data["features"])["id"])
    erf_zones = gdf[gdf['fysiek_voorkomen'] == 'erf']
    return erf_zones

def get_bgt_download_link(bbox):
    """
    Get link for BGT data download for the given bounding box.

    bbox: tuple (min_x, min_y, max_x, max_y)
    Returns a download link if request is successful.
    """
    minx, miny, maxx, maxy = bbox

    # Build a WKT Polygon from bounding box coordinates.
    polygon_wkt = (
        f"POLYGON(({minx} {miny}, {maxx} {miny}, "
        f"{maxx} {maxy}, {minx} {maxy}, {minx} {miny}))"
    )

    # Prepare the payload.
    payload = {
        "featuretypes": ["onbegroeidterreindeel"],
        "format": "citygml",
        "geofilter": polygon_wkt
    }

    # API endpoint URL.
    url = "https://api.pdok.nl/lv/bgt/download/v1_0/full/custom"

    # Set headers for JSON content.
    headers = {
        "Content-Type": "application/json"
    }

    # Send the request.
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

    # If request was accepted (HTTP 202), poll the download status.
    if response.status_code == 202:
        try:
            download_id = response.json().get('downloadRequestId')
            if not download_id:
                print("Missing 'downloadRequestId' in response.")
                return None

            # Poll for the status.
            status_endpoint = f"{url}/{download_id}/status"
            status = 'PENDING'
            while status in ['PENDING', 'RUNNING']:
                time.sleep(5)
                poll_response = requests.get(status_endpoint, timeout=30)
                poll_response.raise_for_status()
                status_json = poll_response.json()
                status = status_json.get('status', '')

            if status == 'COMPLETED':
                download_link = status_json.get('_links', {}).get('download', {}).get('href')
                if download_link:
                    return f"https://api.pdok.nl{download_link}"
                print("Download link not found.")
                return None
            else:
                print(f"Processing failed or incomplete. Status: {status}")
                return None
        except requests.RequestException as e:
            print(f"Error during status polling: {e}")
            return None
    else:
        # If not 202, print error details.
        try:
            error_details = response.json()
            print(f"Error: {error_details}")
        except ValueError:
            print(f"Error: Unable to parse JSON from response. Status code: {response.status_code}")
        return None

def download_and_unzip_file(download_url: str, output_zip: str = "bgt_data.zip", extract_dir: str = "bgt_data") -> str:
    """
    Downloads a file from the given URL, saves it as output_zip, and unzips it into extract_dir.
    Returns the path to the extracted directory.
    """
    if not download_url:
        print("No download URL provided.")
        return ""

    # Download the file.
    try:
        print(f"Downloading file from: {download_url}")
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(output_zip, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")
        return ""

    # Unzip the file.
    try:
        with zipfile.ZipFile(output_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"Extracted ZIP to {extract_dir}")
        return extract_dir
    except zipfile.BadZipFile:
        print("Error: The downloaded file is not a valid ZIP.")
        return ""
    except Exception as e:
        print(f"Error extracting ZIP: {e}")
        return ""

def find_gml_file(folder: str) -> str:
    """
    Searches the specified folder for a .gml file and returns its path.
    If none or multiple GML files are found, handle accordingly.
    """
    gml_file_path = ""
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".gml"):
                gml_file_path = os.path.join(root, file)
                return gml_file_path
    return gml_file_path