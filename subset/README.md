S1 ARD Pypeline
================

S1 ARD Pypeline contains tools to run an ARD process on S1 images

Features
--------

* Validate that the environment is able to run the ard process
* Run the ard process

General
-------

The pipeline needs to be given pairs of images to run through the coherence process. These are known as first and last.
The order of these does matter. The First must be the earliest image, the last must be the later image.

When running a batch of images through the pipeline a csv file should be created with two columns, for the first and last product ids. There should be no
header row. Blank lines will be ignored. White space around the product id's will be ignored.

Installing - Basic - Linux
--------------------------

* Get the wheel package or build one ( ``make dist`` in a clone of this repo )
* Copy the wheel package to the target machine
* Make sure python 3.7 is installed (note all apart from Centos, all are un-tested)
    * https://tecadmin.net/install-python-3-7-on-centos/
    * https://linuxize.com/post/how-to-install-python-3-7-on-ubuntu-18-04/
* Install and update Snap
    * https://bitbucket.satapps.org/projects/COL/repos/s1-ard-pipeline/browse/install_snap.sh
    * http://step.esa.int/main/download/
* Run the following commands:

    python3.7 -m venv pipeline
    cd pipeline
    source bin/activate
    pip install --upgrade pip setuptools wheel
    pip install ~/s1_ard_pypeline-0.1.0-py2.py3-none-any.whl
    validate_setup.py # should error saying it can not find snap
    vim config.cfg # edit the snap path and working directory
    validate_setup.py # should now pass

Installing - Basic - Windows
----------------------------

Unfortunately installing and running under windows is a little more complex

* Get the wheel package or build one ( ``make dist`` in a clone of this repo )
* Copy the wheel package to the target machine
* Make sure python 3.7 is installed
    * https://docs.python.org/3/using/windows.html
* Install and update Snap
    * http://step.esa.int/main/download/
    * Once installed, open snap and tell it to update from the help menu.
* Install GDAL
    * Download from http://www.gisinternals.com/release.php make sure you get the core msi installer
* Download the following wheel packages from https://www.lfd.uci.edu/~gohlke/pythonlibs/
    * rasterio
    * shapely
    * GDAL
* Open powershell and run the following commands:

    python -m venv pipeline
    cd pipeline
    .\\scripts\\activate
    pip install [path to rasterio wheel]
    pip install [path to shapely wheel]
    pip install [path to gdal wheel]
    pip install [path to s1_ard_pypeline-0.1.0-py2.py3-none-any.whl]

* Edit the config file to point to the correct working directory and so on.
* In the powershell window run `validate_setup.py` and check that it does not error.

Running - Basic
---------------

To run a single set of data:

    cd pipeline
    source bin/activate
    validate_setup.py
    run_intensity.py -input <path to input> -output <path to output> -product <first product name>
    run_intensity.py -input <path to input> -output <path to output> -product <last product name>
    run_coherence.py -input <path to input> -output <path to output> -first <first product name> -last <last product name>

If you have a large batch of images to run you can create a csv file with the first and last product names on each line.
this can then be run with

    cd pipeline
    source bin/activate
    batch_run.py -input <path to input> -output <path to output> -targets <path to csv file>

Installing - Docker
-------------------

* Get the container package or build one ( ``make dist`` in a clone of this repo ) it will be named ``s1-ard-pypeline.tar`` after the command has finished
* Install docker on the machine if needed. https://docs.docker.com/install/
* Copy the ``s1-ard-pypeline.tar`` file to the server
* run ``sudo docker load -i s1-ard-pypeline.tar``

Running - Docker
----------------

Run the following command:

    sudo docker run -v /data1/pipeline:/working -v ~:/targets s1-ard-pypeline:latest batch_run.py -input iipcom/download -output iipcom/wil_test -targets /targets/batch.csv

The /working mount is where the container will perform the processing. the /targets mount is for finding the
target list, if this is inside the working mount it is not needed. Edit the -targets parameter as needed.

Generating input lists
----------------------

### Getting the list of products

TODO: convert this to a python script rather than a nifi thing.

* Make sure nifi is running on the cems server. (double click the C:\utils\nifi-1.9.0\bin\run-nifi.bat file if the console window is not already open)
* If necessary wait for it to start.
* Open Nifi in a web browser (Can be on your local machine). ( http://172.16.0.13:8080/nifi/ ) 
* Open the Find Files sub flow.
* Open the SentinelSearchQuery processor (its near the top of a big green box)
* In the Properties tab set the date range you are interested in.
* Put the geojson area of interest into the `C:\utils\inputdata` folder.
* Nifi should pick up the new file and process a query. The output file will be generated in `C:\utils\targets.csv`


### Preloading the data into s3

TODO: Convert this to a python script rather than a nifi thing.

* Open nifi (assuming its still running still after getting the list of products)
* Go to the DownloadFiles sub flow.
* Near the top there is a fetchfile processor. Open its settings.
* Set the target filename to be the file generated by the search process.
* Start the generate flow file processor. It should generate a single file
* Stop the generate flow file processor. It will keep generating a new flow file every few hours if you don't.
* Wait. It will take a while to pull down the data and put it into S3. You can go on to pairing up the data while you wait.

### Pairing up the list of products

`pair_porducts.py` is a tool to pair up the images to be fed into the `batch_run.py` tool. It takes a list of products one on each line 
and works out which pairs of images can be processed. 

The pairs will satisfy the following rules:

* In the same relative orbit
* Between 12 and 24 days apart
* Overlap the same geo-spatial region

The results are written to a csv file that can be passed directly to the `batch_run.py` tool. It can also be passed a 
list of names and it will output one result file for each name in the list. This can be used to break the work up between
several machines easily.

    pair_products.py -input [path to product list] -output [somewhere]/pairs.csv -splitlist [path to list of names]

Now you can feed the resulting files into the batch_run.py script and generate the ard data.

What does it do?
----------------

The processing is split into two main sections. There is the coherence and intensity tasks.

The batch_run.py scrip wraps up the steps:

* Fetch products from S3
* Validate that they will work as a coherence input
* Run the coherence process
* Run the intensity process for the first image
* Run the intensity process for the second image
* Upload the results to S3

The Intensity process is comprised of the following steps:

* Unzip the product file (Skipped if it has already been unzipped)
* Run the fist half of the snap processing chain. (orbit corrections and debursting)
* Run the second half of the snap processing chain. (Speckle filtering, terrain correction and output by polarisation)
* Convert to Tiff
* Compress results

The coherence process is comprised of the following steps:

* Unzip the product file (Skipped if it has already been unzipped)
* Run stage 1 of the snap pipeline for each image (splitting products by polarisation and swath)
* Run stage 2 of the snap pipeline for each polarisation and swath. (geo-coding, interferogram, deburst, enhance-spectral-diversity)
* Run stage 3 of the snap pipeline for each polarisation. (Merge the swaths back together)
* Run stage 4 of the snap pipeline for each polarisation. (Topographic phase removal, terrain corrections)
* Convert to Tiff
* Compress results

Both pipelines will clean up after themselves if asked to. (By default they will clean up) This means that they will
delete intermediate files generated when they are no longer needed.

Both the intensity and coherence processes can be run on their own. See the running steps above for instructions.

The validation at the start of the process before the coherence process is run goes through the following checks:

* Both images are from the same satellite
* Both images are at least 12 days and less than 24 days apart.
* Both images are from the same relative orbit
* Both images have ground control points
* Both images have the expected number of bands
* Both images contain some data
* Both images do not contain a single value
* Both images overlap

The validation that can be done on the result images checks that they conform to the following rules:

* The image contains the right number of bands
* The image contains some data
* The image is not one value
* The image is not over the origin of the coordinate system

These checks are not meant to be exhaustive, they are meant to cover the checks that can be done automatically and 
are appropriate for the use case of this system. In some cases it is fine to have an image that covers the origin.
However in our case it probably means something has gone wrong.

Credits
-------

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.


This is the readme for version 0.1.0
