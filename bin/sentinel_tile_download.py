import logging
import os
import pickle
import threading
import time
from datetime import datetime, timedelta

from google.cloud import storage
from sedas_pyapi.sedas_api import SeDASAPI
from tqdm import tqdm


def download_one_tile(supplierId, tilepath, bucket):
    """
    Downloads an image from GCloud bucket into tilepath

    :param supplierId: supplier ID for Sentinel Tile
    :param tilepath: path to Sentinel tiles
    :param bucket: GCloud bucket object containing all Sentinel imagery
    :return:
    """

    # Finds the right folder in the GCloud bucket from the supplier ID
    identifiers = supplierId.split('_')[5]
    dir1 = identifiers[1:3]
    dir2 = identifiers[3]
    dir3 = identifiers[4:6]

    # Makes supplierId directory
    dirname = os.path.join(tilepath, supplierId)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # Downloads folder to your machine using google cloud client
    prefix = "tiles/%s/%s/%s/%s.SAFE" % (str(dir1), str(dir2), str(dir3), str(supplierId))
    blobs = bucket.list_blobs(prefix=prefix)  # Get list of files
    for blob in blobs:
        if (not blob.name.endswith("/")):
            name = os.path.join(dirname, os.path.basename(blob.name))
            blob.download_to_filename(name)

    return


def request_tile(arr, startdate, enddate, cloud_cover, hit_dict, tilepath, bucket, sedas, pbar):
    """
    Requests to download image from SeDAS server

    :param arr: array of hits to download, in the same format as hitlist
    :param startdate: earliest date the Sentinel image can be taken
    :param enddate: lstest date the Sentinel image can be taken
    :param cloud_cover: maximum percentage of cloud cover in the image
    :param hit_dict: dictionary of all hits, with supplierIds as keys
    :param downloader: the SeDAS downloader object
    :param sedas: SeDAS search object
    :return: none
    """
    for hit in arr:
        result = sedas.search_optical(hit[1].envelope.wkt, startdate, enddate, maxCloudPercent=cloud_cover)
        supplierId = str(result['products'][0]['supplierId'])
        intersection = list(set([el['supplierId'] for el in result['products']]) & set(hit_dict.keys()))
        if intersection:
            hit_dict[intersection[0]].append(hit)
        else:
            hit_dict[supplierId] = [hit]
            download_one_tile(result['products'][0]['supplierId'], tilepath, bucket)
        pbar.update(1)


def download_tiles(hitlist, username, password, tilepath, hitpath, cloud_cover=5, threads=1):
    """
    Downloads all Sentinel tiles that include hit polygons

    :param hitlist: List of tuples, with format (count,polygon_coordinates, classification)
    :param username: SeDAS username
    :param password: SeDAS password
    :param tilepath: path where Sentinel tiles will be downloaded
    :param hitpath: path where the hit dictionary will be stored
    :param cloud_cover: Maximum percentage of cloud cover
    :param threads: Number of threads we will use to download the files
    :return: hit dictionary
    """

    # TODO: Add date change functionality
    # Sets the date range. Configured to search for images in the past 300 days
    td = timedelta(days=300)
    endDate = datetime.now()
    startDate = endDate - td
    logging.basicConfig()
    logging.getLogger("sedas_api").setLevel(logging.ERROR)

    sedas = SeDASAPI(username, password)

    # Converts startdate & enddate to strings for input
    startDate = datetime.strftime(startDate, "%Y-%m-%dT%H:%M:%SZ")
    endDate = datetime.strftime(endDate, "%Y-%m-%dT%H:%M:%SZ")

    if not os.path.isdir(tilepath):
        os.mkdir(tilepath)

    # Identifies already downloaded images so we don't need to redownload them
    hit_dict = {}
    alreadydownloaded = [os.path.splitext(x)[0] for x in os.listdir(tilepath)]
    for file in alreadydownloaded:
        hit_dict[file] = []
    print("Already downloaded %s images: %s" % (len(hit_dict.keys()), str(hit_dict.keys())))

    # Connects to the gcloud bucket containing all historical sentinel-2 imagery
    bucket_name = "gcp-public-data-sentinel-2"
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    # Progress bar
    pbar = tqdm(total=len(hitlist), desc='Analysing polygons and downloading Sentinel tiles', unit='polygon')

    download_threads = []
    for t in range(threads):
        arr = [hitlist[i] for i in range(len(hitlist)) if i % threads == t]
        download_threads.append(threading.Thread(target=request_tile, args=(
            arr, startDate, endDate, cloud_cover, hit_dict, tilepath, bucket, sedas, pbar)))
        download_threads[t].daemon = True
        download_threads[t].start()

    # Checks if any thread is alive and waits until finished
    while any([x.is_alive() for x in download_threads]):
        time.sleep(5)

    pbar.close()
    # save the hit dictionary as a pickle file so we can access it in subsequent uses of this program
    with open(hitpath, 'wb') as f:
        pickle.dump(hit_dict, f)

    return hit_dict
