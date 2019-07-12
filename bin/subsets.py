import os
import threading
import time

from subset.s1_ard_pypeline.ard.ard import gpt


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


def rungpt(supplierIds, full_dict, tilepath, tifpath, size):
    """
    Runs SNAP gpt command to resample and subset the a Sentinel tile

    :param supplierIds: list of supplierIds of Sentinel tiles
    :param full_dict: dictionary containing the polygons that will be subsetted in each tile
    :param tilepath: directory path to the Sentinel tiles
    :param tifpath: directory path to where tif files will be stored
    """

    # Stores all subsets that fails
    errorlist = []

    if not os.path.isdir(tifpath):
        os.mkdir(tifpath)

    # Identifies already subsetted images so we can skip them
    tif_folder = os.listdir(tifpath)
    tiffiles = [file for file in tif_folder if file.endswith(".tif")]
    image_nums = [file.split("_")[0] for file in tiffiles]

    for supplierId in supplierIds:
        for count, polygon, confidence in full_dict[supplierId]:
            if str(count) in image_nums:
                print('Already downloaded. Continuing...')
                continue

            try:

                print('Subsetting polygon %s' % count)

                # Runs a SNAP graph to resample to 10m resolution, subset to the geography, and to finally subset to a pixel of square length size
                gpt(
                    r'./subset/graphs/resample_and_subset.xml',
                    {'count': str(count).zfill(5), 'confidence': confidence, 'polygon': polygon.envelope.wkt,
                     'supplierId': supplierId,
                     'tilepath': tilepath, 'tifpath': tifpath, 'size': size})

            # If a process fails, it'll store the index of the subset where the failure occurred.
            except Exception:
                print('Error with Polygon %s - category %s' % (count, confidence))
                errorlist.append(count)
                continue
    print(errorlist)


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

    full_dict = merge_dicts(hit_dict, miss_dict)

    # SNAP cannot handle very many threads, so we should limit to 5
    if threads > 5:
        threads = 5

    subset_threads = []
    for t in range(threads):
        # Evenly divides up the number of tiles each thread handles
        arr = []
        for i in range(len(full_dict.keys())):
            if i % threads == t:
                arr.append(list(full_dict.keys())[i])

        # Starts threading for subset
        subset_threads.append(threading.Thread(target=rungpt, args=(arr, full_dict, tile_path, tif_path, size)))
        subset_threads[t].daemon = True
        subset_threads[t].start()

    # Waits until all threads are finished
    while any([x.is_alive() for x in subset_threads]):
        time.sleep(5)

    return
