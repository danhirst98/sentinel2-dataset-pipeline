# -*- coding: utf-8 -*-

"""Top-level package for Project Extruder."""
import configparser
import logging
import logstash
from os import environ

__author__ = """Wil Selwood"""
__email__ = 'wil.selwood@sa.catapult.org.uk'
__version__ = '0.1.0'

# init the config here so it is available in many places.
_config = configparser.ConfigParser()
_config.read("config.cfg")


def get_config(section, key):
    """
    Get a configuration value from the environment if it is available if not fall back to the config file.

    environment version of the values from the config file are the {section}_{key} upper cased.

    :param section:
    :param key:
    :return:
    """
    env_result = environ.get(f"{section}_{key}".upper())
    if env_result:
        return env_result

    return _config.get(section, key)


# also configure the console logging just in case
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter('%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)s -- %(message)s')
)

# configure the root logger.
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

logger.addHandler(console)

# turn down some of the more chatty 3rd party loggers.
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('s3transfer').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('boto3').setLevel(logging.INFO)

logging.getLogger('rasterio').setLevel(logging.INFO)
