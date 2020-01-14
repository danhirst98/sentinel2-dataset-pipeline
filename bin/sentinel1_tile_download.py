from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import datetime, timedelta


def sentinel1_tile_download(file,username,password,tilepath):
    api = SentinelAPI(username, password, 'https://scihub.copernicus.eu/dhus')

    td = timedelta(days=60)
    endDate = datetime.now()
    startDate = endDate - td

    footprint = geojson_to_wkt(read_geojson(file))
    print(footprint)
    #products = api.query(footprint,
    #                     date=(startDate, endDate),platformname='Sentinel-1')
    products = api.query(footprint,
                         producttype='SLC',
                         orbitdirection='ASCENDING')
    # download all results from the search
    api.download_all(products,directorypath=tilepath)
    return