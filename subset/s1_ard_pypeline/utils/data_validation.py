import logging

import rasterio
from shapely.geometry import Polygon


def combine_bounds(existing, newer):
    """
    Create another bounding box that wraps two bounding boxes.

    :param existing: an existing bounding box (can be None)
    :param newer: a new bounding box. Should not be None
    :return: a bounding box that covers both inputs
    """
    if not existing:
        return newer

    return rasterio.coords.BoundingBox(
        min(existing.left, newer.left),
        min(existing.bottom, newer.bottom),
        max(existing.right, newer.right),
        max(existing.top, newer.top),
    )


def check_data(src):
    """
    check the data inside a given image is not a single value and not an empty array.
    :param src: rasterio image
    :return: True if the data pointed to is not a single value.
    """
    for i in range(1, src.count):
        band = src.read(i)
        if band.size() == 0:
            logging.error(f"Band {i} does not contain any data.")
            return False
        elif np.all(band == band[0]):
            logging.error(f"Band {i} only has a single value {band[0]}.")
            return False
    return True


def bounding_box_to_wkt(bbox):
    """
    Create a WKT polygon

    :param bbox:
    :return:
    """
    return f"POLYGON((" \
        f"{bbox.left} {bbox.top}, " \
        f"{bbox.right} {bbox.top}, " \
        f"{bbox.right} {bbox.bottom}, " \
        f"{bbox.left} {bbox.bottom}, " \
        f"{bbox.left} {bbox.top}" \
        f"))"


def bounding_box_to_polygon(bbox):
    return Polygon([
        (bbox.left, bbox.top),
        (bbox.right, bbox.top),
        (bbox.right, bbox.bottom),
        (bbox.left, bbox.bottom),
        (bbox.left, bbox.top),
    ])


def overlap(bbox_a, bbox_b):
    """
    Check if two bounding boxes overlap with each other.

    :param bbox_a: a rasterio.coords.boundingbox
    :param bbox_b: a rasterio.coords.boundingbox
    :return: True if the two bounding boxes overlap
    """

    p1 = bounding_box_to_polygon(bbox_a)
    p2 = bounding_box_to_polygon(bbox_b)
    return p1.intersects(p2)
