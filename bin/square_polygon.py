from functools import partial

import pyproj
from pyproj.datadir import set_data_dir
from shapely.geometry import Point, Polygon
from shapely.ops import transform


def geodesic_point_buffer(lat, lon, metres):
    """
    Converts latitude and longitude to coordinates of a circular polygon of radius metres

    :param lat: decimal latitude (float)
    :param lon: decimal longitude (float)
    :param metres: metres (int)
    :return: list of tuples
    """
    set_data_dir("/opt/anaconda3/envs/IMI/share/proj/proj.db")
    proj_wgs84 = pyproj.Proj(init='epsg:4326')

    # Azimuthal equidistant projection
    aeqd_proj = '+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0'
    project = partial(
        pyproj.transform,
        pyproj.Proj(aeqd_proj.format(lat=lat, lon=lon)),
        proj_wgs84)
    buf = Point(0, 0).buffer(metres)  # distance in metres
    return transform(project, buf).exterior.coords[:]


def square_polygon(lat, lon, size):
    """
    Converts point to square of length size pixels

    :param lat: latitude (float)
    :param lon: longitude (float)
    :param size: size of image in pixels
    :return: shapely polygon
    """
    # Converts size from pixels to radius in metres (assuming 10m pixel resolution of Sentinel images)
    size_metres = int(size) / 2 * 10

    buffered_polygon_coords = geodesic_point_buffer(lat, lon, size_metres)

    polygon = Polygon(buffered_polygon_coords).envelope

    return polygon
