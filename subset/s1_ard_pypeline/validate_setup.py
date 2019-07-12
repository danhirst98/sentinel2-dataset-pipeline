#!python
import logging
import platform
import re
import stat as file_stat
import sys
from os import path, stat

import botocore

"""
This script will check over a system and make sure that it can be used for the ARD pipeline process.

It does not take any parameters.
"""


def executable_exists(_path):
    """
    Verify that a given path points to an executable file.

    :param _path: path that should contain the file.
    :return: True if the file exists, is a regular file and is marked executable
    """
    if path.exists(_path):
        stats = stat(_path)
        # windows doesn't have exec mode bits set ever...
        return file_stat.S_ISREG(stats.st_mode) and \
               (file_stat.S_IEXEC & stats.st_mode or platform.system() == "Windows")
    else:
        return False


def required_module_list():
    # Weird import alert: We need to check that the config file exists before it gets loaded by importing it.
    # So we have to import the config object here rather than at the top of the file.
    from s1_ard_pypeline import _config
    result = []

    for conf in _config.items('Snap_Modules'):
        result.append({
            "name": conf[0],
            "version": conf[1],
        })
    return result


def check_required_files():
    ok = True
    if not path.exists("config.cfg"):
        logging.error("Can not find config.cfg. This is required.")
        ok = False

    if not path.exists("graphs") or not path.isdir("graphs"):
        logging.error("Can not find graphs directory. This is required to hold the processing graphs.")
        ok = False

    return ok


def get_config_value(file, key):
    pattern = re.compile(f"^{key} = (.*)$")
    for line in file:
        value = re.search(pattern, line)
        if value:
            return value.group(1)

    return ""


def check_config_entry(file, key, expected_value):
    """
    Check that the snap config file has the expected value for the provided key.
    :param file: config file to look in
    :param key: config value to look for
    :param expected_value: the value that the key should have.
    :return: empty string if it matches or the string in the config file if not.
    """

    value = get_config_value(file, key)
    if value == expected_value:
        return ""
    return value


def check_snap_executables():
    # Weird import alert: We need to check that the config file exists before it gets loaded by importing it.
    # The snap_utils import the s1_ard_pypeline.config object so we have to late import that too.
    from s1_ard_pypeline.utils import snap_utils
    from s1_ard_pypeline import get_config

    found_snap = True
    ok = True
    if not executable_exists(snap_utils.snap_path()):
        logging.error("Can not find snap at %s Is snap installed?", snap_utils.snap_path())
        found_snap = False
        ok = False

    # check we can find gpt
    if not executable_exists(snap_utils.gpt_path()):
        logging.error("Can not find gpt at %s Is snap installed?", snap_utils.gpt_path())
        found_snap = False
        ok = False

    if found_snap and ok:
        logging.info("Found snap, checking configuration...")
        with open(path.join(snap_utils.config_path(), "snap.auxdata.properties"), 'r') as f:
            expected_url = get_config("Snap_Config", "dem.url")
            dem_url = check_config_entry(
                f,
                "DEM.srtm3GeoTiffDEM_HTTP",
                expected_url
            )
            if dem_url:
                logging.error(
                    f"Expected '{expected_url}' for 'srtm3GeoTiffDEM_HTTP' in snap.auxdata.properties got {dem_url}"
                )
                ok = False

    if found_snap and ok:
        logging.info("Found required executables. Checking versions...")
        # run the snap module list
        modules = snap_utils.fetch_snap_module_list()
        if not snap_utils.match_module_lists(modules, required_module_list()):
            logging.error("Modules do not meet the requirements. Try updating snap.")
            ok = False

    return ok


def check_s3():
    # Weird import alert: We need to check that the config file exists before it gets loaded by importing it.
    # The s3_utils import the s1_ard_pypeline.config object so we have to late import that too.
    from s1_ard_pypeline.utils.s3_utils import S3Utils
    logging.info("checking connection to S3...")
    try:
        connection = S3Utils()
        connection.count()
    except botocore.exceptions.ClientError as e:
        logging.error(f"Could not connect to S3. Check the config.cfg settings. {e}")
        return False
    logging.info("Connected to S3 ok.")
    return True


if __name__ == '__main__':
    logging.info("checking setup...")
    problems = False

    # check that our required files are where we expect them to be.
    if not check_required_files():
        # If we cant find the config file we are not going to be able to find any thing else. So abort here.
        logging.info("Could not find required files.")
        sys.exit(2)

    # check we can find snap
    if not check_snap_executables():
        problems = True

    if not check_s3():
        problems = True

    if problems:
        logging.error("Problems have been found see logging for more details")
        sys.exit(2)

    logging.info("Everything looks as expected.")
