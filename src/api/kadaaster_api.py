import time
import zipfile
from pathlib import Path
import requests
import geopandas as gpd

# Define the URL and headers (if any)
url_base = "https://api.pdok.nl"
url_custom_download = url_base + "/kadaster/kadastralekaart/download/v5_0/full/custom"

# Function to convert bbox to WKT POLYGON
def bbox_to_polygon_wkt(bbox):
    min_x, min_y, max_x, max_y = bbox
    coords = [
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
        (min_x, min_y)
    ]
    coords_str = ", ".join(f"{x} {y}" for x, y in coords)
    return f"POLYGON(({coords_str}))"

# Download the file and save it locally
def download_file(url, output_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print(f"Downloaded file saved to {output_path}")

# Extract the GML file from the ZIP
def extract_gml_from_zip(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"Extracted files to {extract_dir}")
    gml_files = [f for f in Path(extract_dir).glob("**/*.gml")]
    if not gml_files:
        raise Exception("No GML file found in the ZIP archive.")
    return gml_files

# Receive download link from kadaster API
def kadaaster_link(bbox, features=["perceel"]):

    # Request body
    body = {       
         "featuretypes": features,
        "format": "gml",
        "geofilter": f"{bbox_to_polygon_wkt(bbox)}"
    }

    # Make the POST request
    try:
        # Send initial request to start processing
        response = requests.post(url_custom_download, json=body)
        response.raise_for_status()

        # Obtain the download request ID
        data = response.json()
        download_key = data['downloadRequestId']
        status_url = f"{url_custom_download}/{download_key}/status"

        # Polling the status endpoint
        while True:
            status_response = requests.get(status_url)
            status_response.raise_for_status()
            status_data = status_response.json()

            # Check the status
            status = status_data.get("status")
            if status == "COMPLETED":
                # Processing completed, retrieve the download link
                zip_file = status_data['_links']['download']['href']
                print(f"Download ready: {zip_file}")
                return url_base + zip_file
            elif status == "FAILED":
                print("Processing failed.")
                return None
            else:
                print(f"Status: {status}. Download progress: {status_data.get('progress')}%. Waiting...")
                time.sleep(10)  # Wait for 5 seconds before checking again

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def clean_kadaster_data(input_file):
    with open(input_file, "r") as file:
        lines = file.readlines()  # Read all lines into memory

    # Filter out lines starting with <oz:plaatscoordinaten> and overwrite the file
    with open(input_file, "w") as file:
        for line in lines:
            if not line.strip().startswith("<oz:plaatscoordinaten>"):
                file.write(line)
    
def get_kadaster_data(bbox, features=['perceel']):
    # Download the file
    download_link = kadaaster_link(bbox, features=features)
    if download_link:
        zip_path = Path("kadaaster_data.zip")
        download_file(download_link, zip_path)

        # Extract the GML file
        extract_dir = Path("kadaaster_data")
        gml_files = extract_gml_from_zip(zip_path, extract_dir)
        clean_kadaster_data(gml_files[0])
        gml = gpd.read_file(gml_files[0])
        return gml
    else:
        return None
