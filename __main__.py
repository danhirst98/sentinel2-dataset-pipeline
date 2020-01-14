import argparse
import logging
import os
import sys
from multiprocessing import cpu_count

from bin import pipeline


def main():
    # TODO: Verbosity
    os.chdir(sys.path[0])
    parser = argparse.ArgumentParser()

    parser.add_argument("--confidence", default=3,
                        help="Maximum confidence level to accept. Only used in certain datasets")
    parser.add_argument("sedas_username", help="SeDAS Username")
    parser.add_argument("sedas_password", help="SeDAS Password")
    parser.add_argument("input", help="Path for input GeoJSON")
    parser.add_argument("name", help="Identifying name for your dataset")

    parser.add_argument("--tilepath", help="Path for Sentinel 2 tiles to be stored")
    parser.add_argument("--tifpath", help="Path for tif images")
    parser.add_argument("--outpath", help="Path for output jpg images")
    parser.add_argument("--hitdict",
                        help="Name of dictionary storing polygon data (Only pass if Sentinel 2 tiles have already been downloaded")
    parser.add_argument("--threads", default=cpu_count(), help="Number of threads")
    parser.add_argument("--size", default=256, help="Size of one length of the output image")
    parser.add_argument("--dense", action="store_true", help="Use alternative find_misses, adapted for dense datasets")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("--clean", action="store_true", help="Do not look for past dictionaries or skip any steps")
    parser.add_argument("--nomiss", action="store_true", help="Do not generate misses")
    parser.add_argument("--sentinel",default=2,help="Sentinel 1 (1) or Sentinel 2 (2)")
    args = parser.parse_args()

    # Creates variables that haven't been initialised in command line
    if args.tilepath:
        tilepath = args.tilepath
    else:
        tilepath = os.path.join("..", "%s_tiles" % args.name)

    if args.tifpath:
        tifpath = args.tifpath
    else:
        tifpath = os.path.join("..", "%s_tifs" % args.name)
        
    if args.outpath:
        outpath = args.outpath
    else:
        outpath = os.path.join("..", "%s_jpgs" % args.name)

    if args.hitdict:
        hitdict = args.hitdict
    else:
        hitdict = os.path.join("..", "%s.dictionary" % args.name)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    print("Number of threads: %s" % args.threads)
    print("Size of all output files: %s" % args.size)
    print("Name of dictionary containing all mining polygons and the associated sentinel tiles: %s" % hitdict)
    print("Path to Sentinel 2 tiles: %s" % tilepath)
    print("Path to output dataset: %s" % outpath)
    print("Getting images from Sentinel %s" % args.sentinel)

    pipeline.run_pipeline(args.input, args.sedas_username, args.sedas_password, args.name, tilepath, tifpath, outpath, hitdict,
                          int(args.threads), int(args.size), args.confidence, args.dense, args.clean,args.nomiss,args.sentinel)


if __name__ == '__main__':
    main()
