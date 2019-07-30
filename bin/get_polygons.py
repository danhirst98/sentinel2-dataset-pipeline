import json
from shapely.geometry import Polygon,Point
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

def check_duplicates(point,coordlist):
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

    coordlist = []

    # Open file with object locations and confidence
    file = open(str(input), "r")
    contents = json.loads(file.read())

    # Iterate through each object, making a polygon for each one and adding it to coordlist

    count = 0
    for feat in tqdm(contents['features'], desc='Identifying hit polygons', unit='polygon'):
        if 'Confidence' in feat['properties'].keys():
            classification = feat['properties']['Confidence']
        else:
            classification = 1
        if classification <= confidence:
            coord = feat['geometry']['coordinates']
            if feat['geometry']['type'] == "MultiPolygon":
                polygon_coords = Polygon(format_coords(coord))
                centroid = polygon_coords.centroid
                centre = [centroid.x, centroid.y]
            elif feat['geometry']['type'] == 'Point':
                centre = list(coord)

            point = Point(centre[1],centre[0])
            if check_duplicates(point,coordlist): continue

            polygon_coords = square_polygon(centre[1], centre[0], size)

            coordlist.append((count, polygon_coords, classification))
            count += 1

    return coordlist
