import json
import logging
from shapely.geometry import Polygon, Point
from tqdm import tqdm

from bin.square_polygon import square_polygon


def format_coords(coords):
    """
    Converts the coordinates in the geojson into a format that shapely polygon can read

    :param coords: list of lists
    :return: list of tuples
    """
    while len(coords) == 1 or not len(coords[0]) == 2:
        coords = coords[0]

    return [tuple(cd) for cd in coords]


def check_duplicates(point, coordlist):
    """
    Checks if the AoI is within a previously generated polygon

    :param point: shapely point of centre of AoI
    :param coordlist: list of all coordinates
    :return: boolean
    """
    for item in coordlist:
        polygon = item[1]
        if point.within(polygon):
            return True
    return False


def get_polygons(confidence, size, input):
    """
    Makes a list of Polygon objects which we can use to download the appropriate tiles

    :param confidence: Confidence that the object in the dataset has been accurately identified. 3 is low confidence, 2 is medium, and 1 is high confidence
    :return: List of Polygon objects denoting the coordinates of the objects
    """

    logging.info("Beginning reading of AoI polygons")

    coordlist = []

    # Open file with object locations and confidence
    file = open(str(input), "r")
    contents = json.loads(file.read())
    logging.debug("Input GeoJSON file: %s" % contents)
    # Iterate through each object, making a polygon for each one and adding it to coordlist

    count = 0
    for feat in tqdm(contents['features'], desc='Identifying hit polygons', unit='polygon'):

        if 'Confidence' in feat['properties'].keys():
            classification = feat['properties']['Confidence']
        else:
            logging.debug("No confidence variable found")
            classification = 1
        if classification <= confidence:
            coord = feat['geometry']['coordinates']
            logging.debug(feat['geometry']['type'])
            if feat['geometry']['type'] == "MultiPolygon" or feat['geometry']['type'] == 'Polygon':

                polygon_coords = Polygon(format_coords(coord))
                centroid = polygon_coords.centroid
                centre = [centroid.x, centroid.y]

            elif feat['geometry']['type'] == 'Point':
                centre = list(coord)
            else:
                raise TypeError("Unsupported geometry type")
            # TODO: Add functionality for lines

            logging.debug("Centre: %s" % centre)

            point = Point(centre[1], centre[0])

            # If Areas of Interest are too close together, then we skip to avoid duplicate dataset elements
            if check_duplicates(point, coordlist):
                continue

            try:
                polygon_coords = square_polygon(centre[1], centre[0], size)
            except:
                raise SyntaxError("Geojson must use lat/long coordinates")

            coordlist.append((count, polygon_coords, classification))
            count += 1

    return coordlist
