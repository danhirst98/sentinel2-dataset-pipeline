import argparse
import glob
import os
import threading
import time
from osgeo import gdal
from threading import Thread
from tqdm import tqdm


def convert_to_jpg(tif, side, options_list, destination):
    gdal.PushErrorHandler('CPLQuietErrorHandler')

    # load the file
    ds = gdal.Open(tif)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()

    # determine boundaries
    ulx = gt[0]
    lry = gt[3] + width * gt[4] + height * gt[5]
    lrx = gt[0] + width * gt[1] + height * gt[2]
    uly = gt[3]

    # get relative scale distance per pixel
    x_scale = (lrx - ulx) / width
    y_scale = (uly - lry) / height

    # find the centre
    centre_x = (ulx + lrx) / 2
    centre_y = (uly + lry) / 2

    # determine projected box boundaries
    B_ulx = centre_x - int(side / 2) * x_scale
    B_lrx = centre_x + int(side / 2) * x_scale
    B_uly = centre_y + int(side / 2) * y_scale
    B_lry = centre_y - int(side / 2) * y_scale

    projwinstr = "-projwin %s %s %s %s" % (B_ulx, B_uly, B_lrx, B_lry)

    # define cut properties
    options_list.append(projwinstr)

    options_string = " ".join(options_list)
    fileinfo = os.path.basename(tif).split('_')

    jpgname = destination + '/' + fileinfo[0] + '_' + fileinfo[1] + '_' + str(side) + '.jpg'
    gdal.Translate(jpgname, tif, options=options_string)
    return


def convert_batch(arr, side, options_list, destination, already_done, pbar):
    for el in arr:
        id = int(os.path.basename(el).split('_')[0])
        pbar.update(1)
        if id in already_done:
            continue
        try:
            convert_to_jpg(el, side, options_list, destination)
        except Exception:
            continue

    return


def convert(size, sourcedir, destdir, threads):
    if size <= 256 and size >= 1:

        options_list = ['-scale', '-b 4', '-b 3', '-b 2', '-of jpeg', '-ot Byte']

        list = glob.glob(sourcedir + '/*.tif')

        if not os.path.isdir(destdir):
            os.mkdir(destdir)

        already_done = [int(os.path.basename(x).split('_')[0]) for x in glob.glob(destdir + '/*.jpg')]

        pbar = tqdm(total=len(list), desc="Converting images to jpegs", unit="image")

        conv_thread = []

        for t in range(threads):
            arr = [list[i] for i in range(len(list)) if i % threads == t]
            conv_thread.append(
                threading.Thread(target=convert_batch, args=(arr, size, options_list, destdir, already_done, pbar)))
            conv_thread[t].daemon = True
            conv_thread[t].start()

        while any([x.is_alive() for x in conv_thread]):
            time.sleep(5)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("size", metavar="size", help="Specify side length of crop region in pixels")
    parser.add_argument("sourcedir", metavar="sourcedir", help="Specify source folder")
    parser.add_argument("destdir", metavar="destdir", help="Specify destination folder")
    parser.add_argument("name", metavar="name", help="Specify identifier for your dataset")
    parser.add_argument("--threads", default=int(os.cpu_count(), help="Number of threads"))
    settings = parser.parse_args()

    convert(int(settings.size), settings.sourcedir, settings.destdir, settings.name, int(settings.threads))
