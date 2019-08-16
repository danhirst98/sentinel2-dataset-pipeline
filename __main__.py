import argparse
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
    parser.add_argument("username", help="SeDAS Username")
    parser.add_argument("password", help="SeDAS Password")
    parser.add_argument("input", help="Path for input GeoJSON")

    parser.add_argument("tilepath", help="Path for Sentinel 2 tiles to be stored")
    parser.add_argument("outpath", help="Path for output dataset")
    parser.add_argument("hitdict",
                        help="Name of dictionary storing polygon data (Only pass if Sentinel 2 tiles have already been downloaded")
    parser.add_argument("--threads", default=cpu_count(), help="Number of threads")
    parser.add_argument("--size", default=256, help="Size of one length of the output image")
    parser.add_argument("--dense", action="store_true", help="Use alternative find_misses, adapted for dense datasets")
    parser.add_argument("--verbosity", action="store_true", help="Enable verbose mode")
    parser.add_argument("--clean", action="store_true", help="Do not look for past dictionaries or skip any steps")

    args = parser.parse_args()

    print("Number of threads: %s" % args.threads)
    print("Size of all output files: %s" % args.size)
    print("Name of dictionary containing all mining polygons and the associated sentinel tiles: %s" % args.hitdict)
    print("Path to Sentinel 2 tiles: %s" % args.tilepath)
    print("Path to output dataset: %s" % args.outpath)

    pipeline.run_pipeline(args.confidence, args.username, args.password, args.tilepath, args.outpath, args.hitdict,
                          int(args.threads), int(args.size), args.input, args.dense, args.clean)


if __name__ == '__main__':
    main()
