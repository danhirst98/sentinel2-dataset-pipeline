import pickle
from os.path import isfile

from bin.find_misses import find_misses
from bin.get_polygons import get_polygons
from bin.sentinel_tile_download import download_tiles
from bin.subsets import create_subsets


def run_pipeline(confidence, username, password, tilepath, tifpath, hit_dict_name, threads, size, input):
    """
    Runs the dataset pipeline

    :param confidence: Confidence that the polygon represents the object we are trying to classify. 1 is high confidence, 2 medium, 3 low
    :param username: Username for SeDAS account
    :param password: Password for SeDAS account
    :param tilepath: path where downloaded Sentinel tiles should be placed
    :param tifpath: path where subsetted tifs should be placed
    :param hit_dict_name: name of the hit dictionary pickle file
    :param threads: Number of threads
    :param size: Size of final image files in pixels
    :return:
    """
    # TODO: Add logging

    # 0.5 If hit_dict has already been written, use that instead to save time
    hitpath = './dicts/' + hit_dict_name
    if isfile(hitpath):
        with open(hitpath, 'rb') as f:
            hit_dict = pickle.load(f)
    else:
        # 1. Create Polygons of affected areas
        hitlist = get_polygons(confidence, size, input)

        # 2. Download Sentinel Tiles
        hit_dict = download_tiles(hitlist, username, password, tilepath, hitpath, threads=threads)

    # 3. Find locations where there aren't any hits in order to populate dataset with equal numbers of hits and misses
    miss_dict = find_misses(hit_dict, tilepath, size)

    # 4. Create subsets from full image tiles
    create_subsets(hit_dict, miss_dict, tilepath, tifpath, size, threads)

    # 5. Convert to jpg
    # convert(tifpath, size)
