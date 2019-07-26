# Sentinel 2 Dataset Pipeline

This program converts a GeoJSON of objects and converts them into a dataset of images on which you can train a machine learning model. 

## Installation

1. Clone this project,
2. Add execution permission to `setup.sh` by running `sudo chmod u+x setup.sh`
3. Run `setup.sh`, and answer the desired prompts. I recommend that you press enter for every option *except* the last option, where it asks if you would like to run SNAP desktop
4. Change config.cfg. Specifically, under [Snap], change the path variable to the path of the snap file. this is found in `snap/bin/snap`.

## Steps Inside the Pipeline

1. We extract the relevant information from the GeoJSON. It takes the polygons or points and converts them into a bounding box of size `size`. It also extracts the confidence if available and assigns each object an id number.
2. We search the SeDAS API for tiles that covers each bounding box, downloads them and stores them in `downloadpath`.
3. We create 'miss' images that do not include the objects we want. This allows us to have both hits and misses with which we can accurately train an ml model.
4. We subset and convert the Sentinel tiles into tifs of size `size`. Half of the tifs will have an object located in the centre of the image, and half of them will not. The files will be saved as `id_hit/miss/confidence_tilename.tif`.


## Usage

The options to run the pipeline are as follows:
* `-u` or `--username`: Your SeDAS username
* `-p` or `--password`: Your SeDAS password
* `-i` or `--input`: Path of the input GeoJSON. Usually stored in the data folder in the pipeline.
* `-c` or `--confidence`: 
    Some GeoJSON datasets define the confidence they have that the image was correctly identified. In these cases, the value 3 denotes low confidence, 2 is medium confidence and 1 is high confidence. Should your dataset have this value, you can set the minimum confidence level you would like to have in your dataset. (optiona)
* `-d` or `--downloadpath`: The folder location where you want the full Sentinel tile images to be stored. Defaults to the directory before where the pipeline files are located. (Optional)
* `-o` or `--outputpath`: The folder location where you want your finished dataset to be stored. Defaults to the directory before where the pipeline files are located. (Optional)
* `-h` or `--hitdict`: The pipeline stores relevant information in a dictionary pickle file to speed up subsequent dataset creations with the same original GeoJSON. If you want to choose your own dictionary name, you can do so here. Defaults to the name of the `input-file-name.dictionary`. (Optional)
* `-t` or `--threads`: The number of threads you want to use. Defaults to the computer's CPU count. (Optional)
* `-s` or `--size`: The length of one side of a dataset image. Defaults to 256. (Optional)
    
## Issues

Right now, the pipeline does not work on any computer or instance that is outside the Catapult firewall. This means that currently, the pipeline cannot be run on any VM. If you are interested in running the pipeline on another machine, talk to IT.

Furthermore, the current pipeline does not allow the user to change the start and end dates for requesting images. Instead, it searches all images from the last 300 days. However, you can change this manually in `bin/sentinel_tile_download.py`.

