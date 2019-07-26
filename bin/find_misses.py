import os
import shapely.geometry as sp
import xml.etree.ElementTree as et
import zipfile
from functools import partial
from glob import glob
from multiprocessing.pool import Pool
from random import random
from tqdm import tqdm
from zipfile import BadZipFile

from bin.square_polygon import square_polygon


def format(string):
    """
    Converts lat lon polygon string in the INSPIRE xml from Sentinel into a readable coordinate list

    :param string: string of latitude and longitude separated by space. In the order 'lon0 lat0 lon1 lat1 lon2...'
    :return: list of tuples for ingestion by the shapely polygon object
    """

    latlon = string.split()

    coordlist = []
    for i in range(int(len(latlon) / 2)):
        lat = float(latlon[i * 2 + 1])
        lon = float(latlon[i * 2])
        coordlist.append((lat, lon))

    return coordlist


def extract_tile_polygon(im_path):
    """
    Finds the latitude and longitude polygon of a Sentinel 2 image

    :param im_path: Path to Sentinel image zip file
    :return: shapely Polygon with the bounds of the tile.
    """
    with zipfile.ZipFile(im_path) as z:
        inspire_path = ''
        for path in z.namelist():
            if 'INSPIRE' in path:
                inspire_path = path
                break

        if not inspire_path:
            raise Exception('Cannot find INSPIRE.xml in Sentinel-2 Zip file %s' % im_path)

        # The INSPIRE file uses namespaces, so we need to pass these to the xml find function
        ns = {'gco': "http://www.isotc211.org/2005/gco", 'gmd': "http://www.isotc211.org/2005/gmd"}

        xml = et.parse(z.open(inspire_path))
        polygon_string = xml.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString',
                                  ns).text

    return sp.Polygon(format(polygon_string))


def rand_polygon(tile, size):
    """
    Finds a random section in a sentinel tile to use as a classification miss in the dataset

    :param tile: shapely polygon of full sentinel tile
    :param size: Number of pixels we want the final image to be
    :return: shapely polygon that is within the boundary of the tile
    """

    (minx, miny, maxx, maxy) = tile.bounds
    lon = minx + random() * (maxx - minx)
    lat = miny + random() * (maxy - miny)
    candidate_polygon = square_polygon(lat, lon, size)
    if tile.contains(candidate_polygon.envelope):
        return candidate_polygon
    else:
        return rand_polygon(tile, size)


def contains_hit_polygon(candidate_polygon, hit_list):
    """
    Checks to see if a candidate miss polygon overlaps with an area that contains a classification hit

    :param candidate_polygon: shapely polygon of a candidate miss image
    :param hit_list: List containing all the hit polygons on this tile
    :return: boolean
    """

    for poly in hit_list:
        if poly[1].envelope.intersects(candidate_polygon.envelope):
            return True
    return False


def overlaps_with_other_misses(candidate_polygon, miss_list):
    """
    Checks if the area of the candidate polygon is already being used as a miss image

    :param candidate_polygon: shapely polygon of a candidate image
    :param miss_list: List containing all the miss polygons on this tile that have already been decided
    :return: boolean
    """

    for miss_poly in miss_list:
        if miss_poly[1].envelope.intersects(candidate_polygon.envelope):
            return True
    return False


def find_one_miss(tile, size, hit_list, miss_list):
    """
    Finds a single polygon that is a candidate for a miss polygon

    :param tile: Sentinel tile polygon
    :param size: size of miss image in pixels
    :param hit_list: list of hit polygons in this tile image
    :param miss_list: list of already identified miss polygons in this tile image
    :return: miss polygon
    """
    candidate_polygon = rand_polygon(tile, size)

    # Checks that candidate polygon will be a unique image in teh dataset
    if not (contains_hit_polygon(candidate_polygon, hit_list) or overlaps_with_other_misses(
            candidate_polygon, miss_list)):
        return candidate_polygon
    else:
        return find_one_miss(tile, size, hit_list, miss_list)


def find_misses_one_tile(num_hits, misses_per_image, size, hit_dict, tiles, idx):
    """
    Finds all miss polygons in one tile

    :param num_hits: Number of total hit polygons
    :param misses_per_image: Number of misses we must identify in each image
    :param size: size of miss image in pixels
    :param hit_dict: dictionary of all hit polygons
    :param tiles: list of all paths to Sentinel tiles
    :param idx: index of the tile we are generating misses for
    :return: key,value for miss_list
    """

    supplierId = os.path.splitext(os.path.basename(tiles[idx]))[0]

    tile_path = tiles[idx]
    try:
        tile = extract_tile_polygon(tile_path)
    except BadZipFile:
        return False
    # Initialise miss_dict lists

    hit_list = hit_dict[supplierId]
    miss_list = []

    for n in range(misses_per_image):
        count = num_hits + idx * misses_per_image + n + 1
        miss = find_one_miss(tile, size, hit_list, miss_list)
        miss_list.append((count, miss, 0))

    return (supplierId, miss_list)


def find_misses(hit_dict, tilepath, size):
    """
    Identifies polygons that will be classification misses for the dataset

    :param hit_dict: the dictionary containing all the classification hits
    :param tilepath: path where all Sentinel tiles are stored
    :param size: size of final images in pixels
    :return: dictionary containing all classification misses
    """

    miss_dict = {}

    # Find the number of polygons in the hit dictionary
    count = 0
    for l in hit_dict.values():
        count += len(l)
    num_hits = int(count)

    # Find number of sentinel tiles in dataset
    images = glob(tilepath + '/*.zip')
    num_images = len(images)

    misses_per_image = int(num_hits / num_images)

    # Creates multiprocess pool to find all the misses
    find_misses_one_tile_partial = partial(find_misses_one_tile, num_hits, misses_per_image, size, hit_dict, images)
    with Pool() as pool:
        for result in tqdm(pool.imap_unordered(find_misses_one_tile_partial, range(len(images))),
                           total=len(images), desc='Finding miss polygons', unit='polygon'):
            if result is not False:
                miss_dict[result[0]] = result[1]

        pool.close()
        pool.join()

    return miss_dict
