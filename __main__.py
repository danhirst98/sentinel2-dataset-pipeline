import getopt
import os
import sys
from multiprocessing import cpu_count

from bin import pipeline


def main(args):
    os.chdir(sys.path[0])

    unixOptions = "c:u:p:d:o:h:t:s:i:"
    gnuOptions = ["confidence=", "user=", "password=", "downloadpath=", "outputpath=", "hitdict=", "threads=", "size=",
                  "input="]
    try:
        arguments, values = getopt.getopt(args, unixOptions, gnuOptions)
    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))
        sys.exit(2)

    confidence = 3
    username = ""
    password = ""
    tilepath = ""
    tifpath = ""
    input = ""
    hitname = ""
    threads = cpu_count()
    size = 256
    # evaluate given options
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-c", "--confidence"):
            print("Maximum confidence level: %s" % currentValue)
            confidence = currentValue
        elif currentArgument in ("-u", "--username"):
            print("Username: %s" % str(currentValue))
            username = currentValue
        elif currentArgument in ("-p", "--password"):
            password = currentValue
        elif currentArgument in ("-d", "--downloadpath"):
            tilepath = currentValue
            print("Path where all Sentinel tiles will be stored: %s" % tilepath)
        elif currentArgument in ("-o", "--outputpath"):
            tifpath = currentValue
            print("Will store all tif files in the folder: %s" % tifpath)
        elif currentArgument in ("-h", "--hitdict"):
            hitname = currentValue

        elif currentArgument in ("-t", "--threads"):
            threads = int(currentValue)
        elif currentArgument in ("-s", "--size"):
            size = currentValue
        elif currentArgument in ("-i", "--input"):
            input = currentValue
    
    
    # Checks that all mandatory arguments have been given
    empty_args = []
    if not username:
        empty_args.append("username")
    if not password:
        empty_args.append("password")
    if not input:
        empty_args.append("input")

    if empty_args:
        print("ERROR: the following mandatory arguments were not provided:\n%s" % str(empty_args))
        exit(2)
        
    input_name = os.path.splitext(os.path.basename(input))[0]
    if not tilepath: tilepath = "../%s_tiles/" % input_name
    if not tifpath: tifpath = "../%s_tifs/" % input_name
    if not hitname: hitname = "%s.dictionary" % input_name
        

    print("Number of threads: %s" % threads)
    print("Size of all output files: %s" % size)
    print("Name of dictionary containing all mining polygons and the associated sentinel tiles: %s" % hitname)

    pipeline.run_pipeline(confidence, username, password, tilepath, tifpath, hitname, threads, size, input)


if __name__ == '__main__':
    main(sys.argv[1:])
