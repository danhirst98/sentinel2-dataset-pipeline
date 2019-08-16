import logging
import pickle
from os import listdir
from os.path import isfile, isdir

from bin.convert import convert
from bin.find_misses import find_misses
from bin.get_polygons import get_polygons
from bin.sentinel_tile_download import download_tiles
from bin.subset import create_subsets


def run_pipeline(input, username, password, name, tilepath, tifpath, outpath, hit_dict_name, threads, size, confidence, dense,
                 clean):
    """
    Runs the dataset pipeline

    :param confidence: Confidence that the polygon represents the object we are trying to classify. 1 is high confidence, 2 medium, 3 low
    :param username: Username for SeDAS account
    :param password: Password for SeDAS account
    :param tilepath: path where downloaded Sentinel tiles should be placed
    :param outpath: path where finished jpgs should be placed
    :param tifpath: path where subsetted tifs should be placed
    :param hit_dict_name: name of the hit dictionary pickle file
    :param threads: Number of threads
    :param size: Size of final image files in pixels
    :param clean: Bypasses dictionary files and does everything from scratch
    :param dense: Uses dense version of find_misses
    :return: none
    """
    # TODO: Add logging
    # 0.5 If hit_dict has already been written, use that instead to save time
    logging.info("STAGE 1: Analysing input file and downloading imagery")
    hitpath = './dicts/' + hit_dict_name
    if not clean and isfile(hitpath) and isdir(tilepath) and listdir(tilepath):
        logging.info("Found a dictionary file. Reading and bypassing tile download...")
        with open(hitpath, 'rb') as f:
            hit_dict = pickle.load(f)
        logging.debug("Hit dictionary reading successful")
    else:
        # 1. Create Polygons of affected areas
        hitlist = get_polygons(confidence, size, input)

        # 2. Download Sentinel Tiles
        hit_dict = download_tiles(hitlist, username, password, tilepath, hitpath, threads=threads)

    # 3. Find locations where there aren't any hits in order to populate dataset with equal numbers of hits and misses
    miss_dict_name = hit_dict_name.split('.')[0] + '_misses.dictionary'
    misspath = './dicts/' + miss_dict_name
    if not clean and isfile(misspath):
        with open(misspath, 'rb') as f:
            miss_dict = pickle.load(f)
    else:
        miss_dict = find_misses(hit_dict, tilepath, size, dense, misspath, threads)

    # 4. Create subsets from full image tiles
    create_subsets(hit_dict, miss_dict, tilepath, tifpath, size, threads)

    convert(size, tifpath, outpath, threads)
