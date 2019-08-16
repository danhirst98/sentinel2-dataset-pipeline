import csv
import glob
import os
import threading
import time

import gdal
from tqdm import tqdm


def merge_dicts(hit_dict, miss_dict):
    """
    Combines the dictionary with all the hit polygons and the dictionary with all the miss polygons

    :param hit_dict: dictionary of classification hit polygons along with their id and classification
    :param miss_dict: dictionary of classification miss polygons along with their id and classification
    :return: full dictionary of all polygons
    """

    full_dict = hit_dict
    for supplierId in miss_dict.keys():
        if supplierId in full_dict:
            full_dict[supplierId] += miss_dict[supplierId]
        else:
            full_dict[supplierId] = miss_dict[supplierId]

    return full_dict


def one_subset(supplierId, filename, polygon, tilepath, tifpath, size):
    """
    Creates one subsetted image from the large sentinel tile

    :param supplierId: supplierId (also the name) of the Sentinel 2 tile (str)
    :param filename: Filename of output image (str)
    :param polygon: Shapely polygon of desired subset
    :param tilepath: Path to Sentinel tiles
    :param tifpath: Path to output images
    :param size: Length of one side of the output image in pixels
    :return: none
    """

    # gdalwarp inputs polygons as a csv file. This code creates that csv file so that we can run gdalwarp
    csvData = [["", "WKT"], [str(1), polygon.wkt]]
    csvname = '/tmp/%s.csv' % filename[:-4]
    with open(csvname, 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(csvData)
    csvFile.close()

    # TODO: Change this in verbose mode
    gdal.PushErrorHandler('CPLQuietErrorHandler')

    # Finds all the image bands as jp2 files and sorts them alphabetically to retain correct order
    dir = os.path.join(tilepath, supplierId)
    fulllist = sorted(glob.glob(dir + '/*.jp2'))

    # Builds VRT dataset to speed up conversion
    vrtname = '/tmp/%s.vrt' % filename[:-4]
    buildvrt_options = gdal.BuildVRTOptions(separate=True, xRes=10, yRes=10)
    vrt_dataset = gdal.BuildVRT(destName=vrtname, srcDSOrSrcDSTab=fulllist, options=buildvrt_options)

    try:
        # Subsets image using gdalwarp
        warp_output = os.path.join(tifpath, filename + ".tif")
        warp_options = gdal.WarpOptions(cropToCutline=True, cutlineDSName=csvname, dstSRS="EPSG:4326", width=size,
                                        height=size)
        gdal.Warp(warp_output, vrt_dataset, options=warp_options)
    except SystemError:
        print('Failed.')
        return

    # removes the temporary csv file
    os.remove(csvname)
    return


def subset_wrapper(supplierIds, full_dict, tilepath, tifpath, size, pbar):
    """
    Iterates through given Sentinel Tiles, subsetting all the images within its bounds

    :param supplierIds: list of supplier IDs of Sentinel Tiles
    :param full_dict: merged dictionary of both the hit polygons and miss polygons
    :param tilepath: Path to Sentinel tiles
    :param tifpath: Path to output images
    :param size: size: size of each tif in pixels
    :param pbar: tqdm progress bar
    :return: none
    """

    # Identifies already subsetted images so we can skip them
    tif_folder = os.listdir(tifpath)
    tiffiles = [file for file in tif_folder if file.endswith(".tif")]
    image_nums = [file.split("_")[0] for file in tiffiles]

    # Iterates through each tile and performs subset for each polygon within that tile
    for supplierId in supplierIds:
        for count, polygon, confidence in full_dict[supplierId]:
            if str(count) in image_nums:
                print('Already downloaded. Continuing...')
                continue
            filename = "%.5d_%s_%s" % (count, confidence, supplierId)
            one_subset(supplierId, filename, polygon, tilepath, tifpath, size)
            pbar.update(1)

    return


def create_subsets(hit_dict, miss_dict, tile_path, tif_path, size, threads=1):
    """
    Converts full Sentinel tiles into tifs of hits and misses of the right size

    :param hit_dict: dictionary containing all the polygons of hits
    :param miss_dict: dictionary containing all the polygons of misses
    :param tile_path:  path where all Sentinel tiles are stored
    :param tif_path: path where all the tifs will be stored
    :param size: size of each tif in pixels
    :param threads: Number of threads
    """

    # Creates one dictionary continaining both hit  polygons and miss polygons
    full_dict = merge_dicts(hit_dict, miss_dict)
    if not os.path.isdir(tif_path):
        os.mkdir(tif_path)
    full_dict_len = sum([len(full_dict[x]) for x in full_dict.keys()])

    # Creates progress bar to monitor progress
    pbar = tqdm(total=full_dict_len)

    subset_threads = []
    for t in range(threads):
        # Evenly divides up the number of tiles each thread handles
        arr = []
        for i in range(len(full_dict.keys())):
            if i % threads == t:
                arr.append(list(full_dict.keys())[i])

        # Starts threading for subset
        subset_threads.append(
            threading.Thread(target=subset_wrapper, args=(arr, full_dict, tile_path, tif_path, size, pbar)))
        subset_threads[t].daemon = True
        subset_threads[t].start()

    # Waits until all threads are finished
    while any([x.is_alive() for x in subset_threads]):
        time.sleep(5)

    pbar.close()
    return
