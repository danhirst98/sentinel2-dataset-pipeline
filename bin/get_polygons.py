import json

from shapely.geometry import Polygon
from tqdm import tqdm

from bin.square_polygon import square_polygon


def format_coords(coords):
    """
    Converts the coordinates in the myanmar json into a format that shapely polygon can read

    :param coords: list of lists
    :return: list of tuples
    """
    while len(coords) == 1 or not len(coords[0]) == 2:
        coords = coords[0]

    return [tuple(cd) for cd in coords]


def get_mine_details(confidence, square, size, features, idx):
    """
    Deprecated, use if we want to add multithreading to this again

    :param confidence:
    :param square:
    :param size:
    :param features:
    :param idx:
    :return:
    """
    feat = features[idx]
    mine_conf = feat['properties']['Confidence']
    if mine_conf <= confidence:
        if feat['geometry']['type'] == "MultiPolygon":
            coord = feat['geometry']['coordinates']
            polygon_coords = Polygon(format_coords(coord))
            if square:
                centre = polygon_coords.centroid
                polygon_coords = square_polygon(centre.y, centre.x, size)
            return idx, polygon_coords, mine_conf

    return False


def get_polygons(confidence, size, input):
    """
    Makes a list of Polygon objects which we can use to download the appropriate tiles

    :param confidence: mine confidence in the myanmar dataset. 3 is low confidence, 2 is medium, and 3 is high confidence
    :return: List of Polygon objects denoting the coordinates of the mines
    """

    coordlist = []

    # Open file with mine locations and confidence
    file = open(str(input), "r")
    contents = json.loads(file.read())

    # Iterate through each mine, making a polygon for each one and adding it to myanmar_coords

    count = 0
    for feat in tqdm(contents['features'], desc='Identifying hit polygons', unit='polygon'):
        if 'Confidence' in feat['properties'].keys():
            mine_conf = feat['properties']['Confidence']
        else:
            mine_conf = 1
        if mine_conf <= confidence:
            coord = feat['geometry']['coordinates']
            if feat['geometry']['type'] == "MultiPolygon":
                polygon_coords = Polygon(format_coords(coord))
                centroid = polygon_coords.centroid
                centre = [centroid.x,centroid.y]
            elif feat['geometry']['type'] == 'Point':
                centre = list(coord)
            polygon_coords = square_polygon(centre[1], centre[0], size)

            coordlist.append((count, polygon_coords, mine_conf))
            count += 1

    return coordlist
