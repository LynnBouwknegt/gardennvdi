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
