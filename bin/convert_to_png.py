import glob
import os
import shutil
import sys

from osgeo import gdal


# TODO: turn the whole code into a function
# TODO: Add commenting
# TODO: Allow us to change the output file type (e.g. jpeg, png, or tif)
# TODO: Allow us to change the bands we want to keep (-b 4 -b 3 -b 2)
# TODO: maaaybe also specify a destination path
def conv(tifpath, size):
    """
    Description of function

    :param tifpath: what this parameter does
    :param size:
    :return: what it returns
    """
    return


list = glob.glob('*.tif')

if len(sys.argv) == 2:
    dist = int(sys.argv[1])  # distance in metres
else:
    dist = 'full'

options_list = ['-scale', '-b 4', '-b 3', '-b 2', '-of jpeg', 'ot Byte']

source = os.getcwd()
new_dir = 'test-jpg-' + str(dist)
destination = source + '/' + new_dir

if os.path.isdir(destination) == 0:
    os.mkdir(destination)
else:
    shutil.rmtree(destination)
    os.mkdir(destination)

order = 1
for file in list:

    # load the file
    ds = gdal.Open(file)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()

    if len(sys.argv) == 2:
        # TODO: convert all your GDAL instructions from Python 2 to Python 3 (on Instance)
        # determine boundaries
        minx = gt[0]
        miny = gt[3] + width * gt[4] + height * gt[5]
        maxx = gt[0] + width * gt[1] + height * gt[2]
        maxy = gt[3]

        # estimate the centre
        centre_x = (maxx + minx) / 2
        centre_y = (maxy + miny) / 2

        # determine projected box boudaries
        ulx = centre_x - int(dist / 2)
        lrx = centre_x + int(dist / 2)
        uly = centre_y + int(dist / 2)
        lry = centre_y - int(dist / 2)

        projwinstr = "-projwin %s %s %s %s" % (ulx, uly, lrx, lry)

        # define cut properties
        options_list.append(projwinstr)

    options_string = " ".join(options_list)
    fileinfo = file.split('_')
    filename = destination + '/' + fileinfo[0] + '_' + fileinfo[1] + '_' + str(dist) + '.jpg'
    gdal.Translate(filename, file, options=options_string)
    print("Created %s..." % filename)
    print("Processed %d files \n" % order)
    order = order + 1

# TODO: Add functionality to be able to run from the commandline. Add commandline arguments before passing the convert_to_png function

if __name__ == '__main__':
# TODO: Learn about getopt, and use it to pass arguments to the command
# Commandline arguments etc.
