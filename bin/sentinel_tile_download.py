import os
import pickle
import threading
import time
from datetime import datetime, timedelta

from sedas_pyapi.bulk_download import SeDASBulkDownload
from sedas_pyapi.sedas_api import SeDASAPI
from tqdm import tqdm


def request(arr, startdate, enddate, cloud_cover, hit_dict, downloader, sedas):
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

    for hit in tqdm(arr):
        result_sar = sedas.search_optical(hit[1].envelope.wkt, startdate, enddate, maxCloudPercent=cloud_cover)
        supplierId = str(result_sar['products'][0]['supplierId'])
        intersection = list(set([el['supplierId'] for el in result_sar['products']]) & set(hit_dict.keys()))
        if intersection:
            hit_dict[intersection[0]].append(hit)
        else:
            print("Found object in a new tile: %s. Beginning download request for this tile." % str(supplierId))
            hit_dict[supplierId] = [hit]
            downloader.add([result_sar['products'][0]])


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

    sedas = SeDASAPI(username, password)
    downloader = SeDASBulkDownload(sedas, tilepath, parallel=threads)

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

    download_threads = []

    for t in range(threads):
        arr = [hitlist[i] for i in range(len(hitlist)) if i % threads == t]
        download_threads.append(threading.Thread(target=request, args=(
            arr, startDate, endDate, cloud_cover, hit_dict, downloader, sedas)))
        download_threads[t].daemon = True
        download_threads[t].start()

    # Checks if any thread is alive and waits until finished
    while any([x.is_alive() for x in download_threads]):
        time.sleep(5)

    # Wait until all downloads are finished
    while not downloader.is_done():
        time.sleep(5)

    # clean up the background threads.
    downloader.shutdown()

    # save the hit dictionary as a pickle file so we can access it in subsequent uses of this program
    with open(hitpath, 'wb') as f:
        pickle.dump(hit_dict, f)

    return hit_dict
